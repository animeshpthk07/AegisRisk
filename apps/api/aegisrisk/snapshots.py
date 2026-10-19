"""Opt-in, single-user synthetic snapshots. Not a public upload service."""

import os
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_session
from .imports import parse_csv, parse_import, read_csv_body
from .models import Facility, SavedPortfolio

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


def imports_enabled():
    return os.getenv("SYNTHETIC_IMPORTS_ENABLED", "false").lower() == "true"


def require_enabled():
    if not imports_enabled():
        raise HTTPException(403, "Saved imports are disabled on this instance")


def metadata(snapshot):
    return {key: getattr(snapshot, key) for key in
            ("id", "name", "digest", "row_count", "created_at")}


def load_rows(session: Session, dataset_id: UUID | None = None):
    if dataset_id is None:
        return list(session.scalars(select(Facility).order_by(Facility.id)))
    require_enabled()
    snapshot = session.get(SavedPortfolio, str(dataset_id))
    if snapshot is None:
        raise HTTPException(404, "Saved portfolio not found")
    try:
        result, rows = parse_csv(snapshot.csv_text.encode("utf-8"))
    except HTTPException:
        raise HTTPException(503, "Saved portfolio integrity check failed") from None
    if (not result["valid"] or result["digest"] != snapshot.digest
            or len(rows) != snapshot.row_count):
        raise HTTPException(503, "Saved portfolio integrity check failed")
    return sorted(rows, key=lambda row: row.id)


@router.get("/api/v1/saved-portfolios")
def list_snapshots(
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    if not imports_enabled():
        return {"enabled": False, "items": [], "total": 0, "offset": offset, "limit": limit}
    rows = session.scalars(select(SavedPortfolio).order_by(
        SavedPortfolio.created_at.desc(), SavedPortfolio.id
    ).offset(offset).limit(limit))
    total = session.scalar(select(func.count()).select_from(SavedPortfolio))
    return {"enabled": True, "items": [metadata(row) for row in rows],
            "total": total, "offset": offset, "limit": limit}


@router.post("/api/v1/saved-portfolios")
async def save_snapshot(
    request: Request,
    session: SessionDep,
    name: str = Query(..., min_length=1, max_length=80),
):
    require_enabled()
    name = name.strip()
    if not name or not name.isprintable() or name.startswith(("=", "+", "-", "@")):
        raise HTTPException(422, "Use a printable, non-formula portfolio name")
    if request.headers.get("x-aegisrisk-reviewed") != "true":
        raise HTTPException(400, "Review the valid preview and explicitly confirm saving")
    raw = await read_csv_body(request)
    result, _, stored = parse_import(raw, request.headers.get("content-type", ""))
    if not result["valid"]:
        return JSONResponse(status_code=422, content=result)
    if request.headers.get("x-aegisrisk-preview-digest") != result["digest"]:
        raise HTTPException(409, "File changed since preview; validate and review it again")
    existing = session.scalar(select(SavedPortfolio).where(
        SavedPortfolio.digest == result["storage_digest"]
    ))
    if existing is not None:
        return {"persisted": True, "created": False, "portfolio": metadata(existing)}
    snapshot = SavedPortfolio(
        id=str(uuid4()), name=name, digest=result["storage_digest"],
        csv_text=stored.decode("utf-8"), row_count=result["row_count"],
        created_at=datetime.now(UTC).isoformat(),
    )
    session.add(snapshot)
    try:
        session.commit()
    except IntegrityError:
        # A concurrent retry of identical bytes must resolve to the same saved snapshot.
        session.rollback()
        existing = session.scalar(select(SavedPortfolio).where(
            SavedPortfolio.digest == result["storage_digest"]
        ))
        if existing is None:
            raise
        return {"persisted": True, "created": False, "portfolio": metadata(existing)}
    return JSONResponse(status_code=201, content={
        "persisted": True, "created": True, "portfolio": metadata(snapshot),
    })
