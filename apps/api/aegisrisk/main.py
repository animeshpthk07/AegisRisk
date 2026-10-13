import logging
from collections import defaultdict
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import get_session
from .models import Facility
from .risk import expected_loss, summarize

app = FastAPI(title="AegisRisk", version="0.1.0", description="Synthetic educational demo only")
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


@app.get("/api/v1/portfolio")
def portfolio(session: SessionDep):
    rows = list(session.scalars(select(Facility).order_by(Facility.id)))
    summary = summarize(rows)
    groups = defaultdict(lambda: {"ead": 0.0, "expected_loss": 0.0})
    for row in rows:
        groups[row.industry]["ead"] += float(row.ead)
        groups[row.industry]["expected_loss"] += float(expected_loss(row.pd, row.lgd, row.ead))
    return {
        "dataset_version": "demo-v1",
        "currency": "INR",
        "horizon": "one_year",
        "synthetic": True,
        "facilities": [serialize(row) for row in rows],
        "summary": summary,
        "segments": [
            {
                "industry": key,
                **value,
                "share": value["ead"] / summary["total_ead"] if summary["total_ead"] else 0,
            }
            for key, value in sorted(groups.items())
        ],
        "warnings": [
            "Fictional data. PD and LGD are illustrative inputs, not trained model estimates.",
            "Single snapshot: no historical trend or real-world validation.",
        ]
        + (["No facilities loaded."] if not rows else []),
    }


@app.get("/api/v1/facilities")
def facilities(
    session: SessionDep,
    q: str = Query("", max_length=100),
    industry: str | None = Query(None, max_length=50),
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
):
    query = select(Facility).order_by(Facility.id)
    if q:
        query = query.where(Facility.borrower.contains(q, autoescape=True))
    if industry:
        query = query.where(Facility.industry == industry)
    rows = list(session.scalars(query))
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


@app.post("/api/v1/stress")
def stress(config: StressInput, session: SessionDep):
    rows = list(session.scalars(select(Facility)))
    if config.industry and config.industry not in {r.industry for r in rows}:
        return JSONResponse(status_code=422, content={"detail": "Unknown industry"})
    baseline = sum((expected_loss(r.pd, r.lgd, r.ead) for r in rows), Decimal(0))
    stressed = Decimal(0)
    for row in rows:
        if config.industry is None or row.industry == config.industry:
            stressed += expected_loss(
                min(Decimal(1), row.pd * Decimal(str(config.pd_multiplier))),
                min(Decimal(1), row.lgd * Decimal(str(config.lgd_multiplier))),
                row.ead * Decimal(str(config.ead_multiplier)),
            )
        else:
            stressed += expected_loss(row.pd, row.lgd, row.ead)
    return {
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


@app.get("/api/v1/explanation")
def explanation(session: SessionDep):
    stats = summarize(list(session.scalars(select(Facility))))
    return {
        "mode": "deterministic",
        "text": f"This fictional portfolio contains {stats['facility_count']} facilities with INR {stats['total_ead']:,.2f} exposure at default. Summing PD × LGD × EAD for each facility gives one-year expected loss of INR {stats['total_expected_loss']:,.2f}.",
        "disclaimer": "Rule-based explanation, not an LLM output, credit recommendation, IFRS 9 calculation, or regulatory capital estimate.",
    }
