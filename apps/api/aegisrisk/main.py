import json
import logging
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, getcontext
from hashlib import sha256
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import get_session
from .imports import router as import_router
from .models import Facility, SavedPortfolio
from .risk import expected_loss, summarize
from .snapshots import load_rows
from .snapshots import router as snapshot_router

app = FastAPI(title="AegisRisk", version="0.1.0", description="Synthetic educational demo only")
app.include_router(import_router)
app.include_router(snapshot_router)
SessionDep = Annotated[Session, Depends(get_session)]


@app.middleware("http")
async def safe_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    logging.getLogger("aegisrisk").error("Database operation failed: %s", type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "Data service unavailable"})


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "aegisrisk-api", "version": "0.1.0", "external_ai": False}


@app.get("/api/v1/ready")
def ready(session: SessionDep):
    session.execute(text("SELECT 1"))
    session.execute(select(Facility.id).limit(1))
    session.execute(select(SavedPortfolio.id).limit(1))
    return {"status": "ok", "database": "connected"}


def serialize(row):
    return {
        key: getattr(row, key) for key in ["id", "borrower", "industry", "geography", "rating"]
    } | {
        "pd": float(row.pd),
        "lgd": float(row.lgd),
        "ead": float(row.ead),
        "expected_loss": float(expected_loss(row.pd, row.lgd, row.ead)),
    }


def portfolio_payload(rows, dataset_id):
    summary = summarize(rows)
    total_ead = sum((row.ead for row in rows), Decimal(0))
    groups = defaultdict(lambda: {"ead": Decimal(0), "expected_loss": Decimal(0)})
    for row in rows:
        groups[row.industry]["ead"] += row.ead
        groups[row.industry]["expected_loss"] += expected_loss(row.pd, row.lgd, row.ead)
    return {
        "dataset_version": f"saved-v1:{dataset_id}" if dataset_id else "demo-v1",
        "dataset_id": str(dataset_id) if dataset_id else None,
        "currency": "INR",
        "horizon": "one_year",
        "synthetic": True,
        "facilities": [serialize(row) for row in rows],
        "summary": summary,
        "segments": [
            {
                "industry": key,
                "ead": float(value["ead"]),
                "expected_loss": float(value["expected_loss"]),
                "share": float(value["ead"] / total_ead) if total_ead else 0,
            }
            for key, value in sorted(groups.items())
        ],
        "warnings": [
            "Fictional data. PD and LGD are illustrative inputs, not trained model estimates.",
            "Single snapshot: no historical trend or real-world validation.",
        ]
        + (["No facilities loaded."] if not rows else []),
    }


@app.get("/api/v1/portfolio")
def portfolio(session: SessionDep, dataset_id: UUID | None = None):
    return portfolio_payload(load_rows(session, dataset_id), dataset_id)


@app.get("/api/v1/facilities")
def facilities(
    session: SessionDep,
    q: str = Query("", max_length=100),
    industry: str | None = Query(None, max_length=50),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    dataset_id: UUID | None = None,
):
    rows = load_rows(session, dataset_id)
    if q:
        rows = [row for row in rows if q.casefold() in row.borrower.casefold()]
    if industry:
        rows = [row for row in rows if row.industry == industry]
    return {
        "items": [serialize(row) for row in rows[offset : offset + limit]],
        "total": len(rows),
        "offset": offset,
        "limit": limit,
    }


class StressInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    pd_multiplier: float = Field(1.5, ge=0, le=10)
    lgd_multiplier: float = Field(1.1, ge=0, le=10)
    ead_multiplier: float = Field(1, ge=0, le=10)
    industry: str | None = Field(None, max_length=50)


def stress_payload(rows, config, *, include_evidence=False):
    rows = sorted(rows, key=lambda row: row.id)
    if config.industry is not None and config.industry not in {r.industry for r in rows}:
        raise HTTPException(status_code=422, detail="Unknown industry")
    baseline = Decimal(0)
    stressed = Decimal(0)
    evidence = []
    factors = {key: Decimal(str(value)) for key, value in config.model_dump().items()
               if key != "industry"}
    for row in rows:
        affected = config.industry is None or row.industry == config.industry
        pd = row.pd * factors["pd_multiplier"] if affected else row.pd
        lgd = row.lgd * factors["lgd_multiplier"] if affected else row.lgd
        ead = row.ead * factors["ead_multiplier"] if affected else row.ead
        base_el = expected_loss(row.pd, row.lgd, row.ead)
        scenario_el = expected_loss(min(Decimal(1), pd), min(Decimal(1), lgd), ead)
        baseline += base_el
        stressed += scenario_el
        if include_evidence:
            evidence.append({
                "id": row.id, "affected": affected,
                "pd_capped": pd > 1, "lgd_capped": lgd > 1,
                "stressed_pd": format(min(Decimal(1), pd), "f"),
                "stressed_lgd": format(min(Decimal(1), lgd), "f"),
                "stressed_ead": format(ead, "f"),
                "baseline_el": format(base_el, "f"),
                "stressed_el": format(scenario_el, "f"),
                "delta_el": format(scenario_el - base_el, "f"),
            })
    result = {
        "baseline_el": float(baseline),
        "stressed_el": float(stressed),
        "delta_el": float(stressed - baseline),
        "delta_pct": float((stressed - baseline) / baseline) if baseline else None,
        "assumptions": [
            "Illustrative sensitivity, not a validated macroeconomic model.",
            "Multipliers apply to selected industry or entire portfolio; PD/LGD capped at 1.",
            "One-year horizon; INR; unchanged recovery timing and dependence assumptions.",
        ],
    }
    if include_evidence:
        result["inputs"] = config.model_dump()
        result["calculation"] = {
            "decimal_precision": getcontext().prec,
            "decimal_rounding": getcontext().rounding,
            "baseline_el_decimal": format(baseline, "f"),
            "stressed_el_decimal": format(stressed, "f"),
            "delta_el_decimal": format(stressed - baseline, "f"),
            "delta_pct_decimal": format((stressed - baseline) / baseline, "f")
            if baseline else None,
            "delta_pct_unit": "fraction; multiply by 100 for percent",
            "affected_facility_count": sum(item["affected"] for item in evidence),
            "facilities": evidence,
            "notes": [
                "User-selected multipliers are assumptions, not forecasts or probabilities.",
                "PD/LGD are capped at 1 after multiplication. Unselected rows are unchanged.",
                "Delta percentage is undefined when baseline expected loss is zero.",
                "Decimal evidence uses the stated context; JSON numbers are display values.",
                "Synthetic sensitivity only; no IFRS 9, capital, audit or lending conclusion.",
            ],
        }
    return result


@app.post("/api/v1/stress")
def stress(config: StressInput, session: SessionDep, dataset_id: UUID | None = None):
    return stress_payload(load_rows(session, dataset_id), config)


def explanation_payload(stats):
    return {
        "mode": "deterministic",
        "text": f"This fictional portfolio contains {stats['facility_count']} facilities with INR {stats['total_ead']:,.2f} exposure at default. Summing PD × LGD × EAD for each facility gives one-year expected loss of INR {stats['total_expected_loss']:,.2f}.",
        "disclaimer": "Rule-based explanation, not an LLM output, credit recommendation, IFRS 9 calculation, or regulatory capital estimate.",
    }


@app.get("/api/v1/explanation")
def explanation(session: SessionDep, dataset_id: UUID | None = None):
    return explanation_payload(summarize(load_rows(session, dataset_id)))


def baseline_report_payload(rows, dataset_id):
    """Read-only baseline evidence; rows are loaded once by the caller."""
    rows = sorted(rows, key=lambda row: row.id)
    baseline = portfolio_payload(rows, dataset_id)
    inputs = [
        {key: getattr(row, key) for key in
         ("id", "borrower", "industry", "geography", "rating")}
        | {key: format(getattr(row, key).normalize(), "f") for key in ("pd", "lgd", "ead")}
        for row in rows
    ]
    canonical = json.dumps(inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return {
        "schema_version": "aegisrisk.baseline-report.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "report_kind": "baseline_only",
        "scenario_included": False,
        **baseline,
        "explanation": explanation_payload(baseline["summary"]),
        "source": {
            "canonical_sha256": sha256(canonical.encode("utf-8")).hexdigest(),
            "canonicalization": (
                "Input rows sorted by case-sensitive id; normalized plain decimal strings; "
                "JSON sorted keys, compact separators, ensure_ascii=true, UTF-8. "
                "This is not the original CSV digest or a digital signature."
            ),
            "input_rows": inputs,
        },
        "calculation": {
            "formula": "EL = sum(PD * LGD * EAD)",
            "probability_unit": "fraction_0_to_1",
            "decimal_precision": getcontext().prec,
            "decimal_rounding": getcontext().rounding,
            "total_ead_decimal": format(sum((r.ead for r in rows), Decimal(0)), "f"),
            "total_expected_loss_decimal": format(
                sum((expected_loss(r.pd, r.lgd, r.ead) for r in rows), Decimal(0)), "f"
            ),
            "facility_expected_loss_decimal": [
                {"id": r.id, "expected_loss": format(expected_loss(r.pd, r.lgd, r.ead), "f")}
                for r in rows
            ],
            "notes": [
                "Summary numbers are JSON display values; decimal evidence is provided separately.",
                "Weighted PD/LGD use EAD. Borrower HHI sums squared borrower exposure shares.",
                "No stress scenario, trained model, investment advice or lending decision is included.",
                "Not IFRS 9 ECL, regulatory capital, an audit opinion or production validation.",
            ],
        },
    }


@app.get("/api/v1/report")
def report(session: SessionDep, dataset_id: UUID | None = None):
    return baseline_report_payload(load_rows(session, dataset_id), dataset_id)


@app.post("/api/v1/scenario-report")
def scenario_report(config: StressInput, session: SessionDep, dataset_id: UUID | None = None):
    """Compare one loaded snapshot under explicit assumptions; no writes."""
    rows = sorted(load_rows(session, dataset_id), key=lambda row: row.id)
    scenario = stress_payload(rows, config, include_evidence=True)
    baseline = baseline_report_payload(rows, dataset_id)
    return {
        "schema_version": "aegisrisk.scenario-report.v1",
        "generated_at": baseline["generated_at"],
        "report_kind": "baseline_and_scenario",
        "scenario_included": True,
        **{key: baseline[key] for key in
           ("dataset_id", "dataset_version", "synthetic", "currency", "horizon")},
        "baseline": baseline,
        "scenario": scenario,
    }
