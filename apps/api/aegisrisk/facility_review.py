"""Inspect one fictional facility and its borrower within one authorized snapshot."""

from decimal import Decimal
from hashlib import sha256
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .database import get_session
from .model_lab import ModelInput, predict
from .risk import expected_loss, summarize
from .snapshots import load_rows

router = APIRouter(prefix="/api/v1")
PROFILE_VERSION = "demo-financial-ratios-v1"
SEED_BORROWERS = {f"SYN-{i:03}": f"Fictional Borrower {i:03}" for i in range(1, 41)}


def demo_profile(row, dataset_id):
    if dataset_id is not None or SEED_BORROWERS.get(row.id) != row.borrower:
        return None
    # Four independent, bounded fictional ratios keyed to a stable demo identity.
    # Neither the supplied facility PD nor its rating enters the generation rule.
    digest = sha256(f"{PROFILE_VERSION}/{row.id}".encode("ascii")).digest()
    return ModelInput(
        synthetic=True,
        debt_to_assets=round(0.15 + digest[0] / 255 * 0.75, 3),
        interest_coverage=round(0.5 + digest[1] / 255 * 7.5, 3),
        current_ratio=round(0.5 + digest[2] / 255 * 2.5, 3),
        revenue_growth=round(-0.2 + digest[3] / 255 * 0.5, 3),
    )


def review_facility(rows, facility_id, dataset_id):
    row = next((item for item in rows if item.id == facility_id), None)
    if row is None:
        raise HTTPException(404, "Facility unavailable in the selected portfolio")
    borrower = summarize([item for item in rows if item.borrower == row.borrower])
    portfolio = summarize(rows)
    baseline = expected_loss(row.pd, row.lgd, row.ead)
    stressed_pd = min(Decimal(1), 2 * row.pd)
    stressed = expected_loss(stressed_pd, row.lgd, row.ead)
    profile = demo_profile(row, dataset_id)
    return {
        "dataset_id": str(dataset_id) if dataset_id else None,
        "dataset_version": f"saved-v1:{dataset_id}" if dataset_id else "demo-v1",
        "synthetic": True, "currency": "INR", "horizon": "one_year",
        "facility": {
            "id": row.id, "borrower": row.borrower, "industry": row.industry,
            "geography": row.geography, "rating": row.rating, "pd": float(row.pd),
            "lgd": float(row.lgd), "ead": float(row.ead), "expected_loss": float(baseline),
        },
        "borrower": borrower, "portfolio": portfolio,
        "sensitivity": {"pd_multiplier": 2, "stressed_pd": float(stressed_pd),
                        "stressed_el": float(stressed), "delta_el": float(stressed - baseline)},
        "profile_version": PROFILE_VERSION if profile else None,
        "model": predict(profile) if profile else None,
        "profile_note": (
            "Four synthetic, versioned ratios belong to this built-in demonstration case. "
            "The model estimate is separate from the supplied PD used for expected loss."
            if profile else "No linked financial ratios are available for this facility."
        ),
    }


@router.get("/facility-review")
def facility_review(session: Annotated[Session, Depends(get_session)],
                    facility_id: Annotated[str, Query(min_length=1, max_length=128)],
                    dataset_id: UUID | None = None):
    return review_facility(load_rows(session, dataset_id), facility_id, dataset_id)
