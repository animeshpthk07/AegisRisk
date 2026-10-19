"""Bounded synthetic CSV/XLSX preview. No portfolio storage access."""

import csv
import io
import re
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .risk import summarize
from .xlsx import XLSX_TYPE, xlsx_to_csv

router = APIRouter()
MAX_BYTES = 262_144
MAX_ROWS = 1_000
MAX_ISSUES = 100
COLUMNS = ("id", "borrower", "industry", "geography", "rating", "pd", "lgd", "ead",
           "currency", "horizon")
TEXT_LIMITS = {"id": 32, "borrower": 100, "industry": 50, "geography": 50, "rating": 8}
NUMBER = re.compile(r"[0-9]+(?:[.][0-9]+)?", re.ASCII)
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}", re.ASCII)


@dataclass(frozen=True)
class PreviewFacility:
    id: str
    borrower: str
    industry: str
    geography: str
    rating: str
    pd: Decimal
    lgd: Decimal
    ead: Decimal


def parse_csv(raw: bytes):
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "CSV exceeds the 256 KiB limit")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(422, "Use UTF-8 CSV encoding") from None
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    issues = []
    issue_count = 0
    invalid_rows = 0
    row_count = 0
    rows = []
    seen_ids = set()

    def issue(row, column, code, message):
        nonlocal issue_count
        issue_count += 1
        if len(issues) < MAX_ISSUES:
            issues.append({"row": row, "column": column, "code": code, "message": message})

    try:
        header = next(reader, None)
        if header is None or len(header) != len(COLUMNS) or set(header) != set(COLUMNS):
            raise HTTPException(422, "Headers must match the documented CSV schema exactly")
        for record, values in enumerate(reader, start=2):
            if not values:
                continue
            row_count += 1
            if row_count > MAX_ROWS:
                raise HTTPException(413, "CSV exceeds the 1,000-row limit")
            before = issue_count
            if len(values) != len(COLUMNS):
                issue(record, None, "column_count", "Each record must have exactly 10 fields")
                invalid_rows += 1
                continue
            data = {key: value.strip() for key, value in zip(header, values, strict=True)}
            for key, limit in TEXT_LIMITS.items():
                value = data[key]
                if (not value or len(value) > limit or not value.isprintable()
                        or value.startswith(("=", "+", "-", "@"))):
                    issue(record, key, "text", f"Use 1-{limit} printable, non-formula characters")
            if not IDENTIFIER.fullmatch(data["id"]):
                issue(record, "id", "identifier", "Use letters, digits, hyphens or underscores")
            normalized_id = data["id"].casefold()
            if normalized_id in seen_ids:
                issue(record, "id", "duplicate", "Facility ID is duplicated within this file")
            seen_ids.add(normalized_id)
            if data["currency"] != "INR":
                issue(record, "currency", "currency", "Only INR is supported; no FX conversion")
            if data["horizon"] != "one_year":
                issue(record, "horizon", "horizon", "Use one_year for the PD horizon")
            numbers = {}
            for key in ("pd", "lgd", "ead"):
                value = data[key]
                scale = 2 if key == "ead" else 10
                maximum = Decimal(1_000_000_000_000) if key == "ead" else Decimal(1)
                if (len(value) > 30 or not NUMBER.fullmatch(value)
                        or len(value.partition(".")[2]) > scale):
                    issue(record, key, "number", f"Use a non-negative decimal with <= {scale} places")
                    continue
                number = Decimal(value)
                if number > maximum:
                    issue(record, key, "range", f"Value must be between 0 and {maximum}")
                else:
                    numbers[key] = number
            if issue_count == before:
                rows.append(PreviewFacility(**{key: data[key] for key in TEXT_LIMITS}, **numbers))
            else:
                invalid_rows += 1
    except csv.Error:
        raise HTTPException(422, "Malformed CSV: check quoting and field sizes") from None
    if row_count == 0:
        raise HTTPException(422, "CSV must contain at least one facility")
    valid = issue_count == 0
    return {
        "valid": valid,
        "digest": sha256(raw).hexdigest(),
        "persisted": False,
        "synthetic_acknowledged": True,
        "currency": "INR",
        "horizon": "one_year",
        "row_count": row_count,
        "valid_rows": len(rows),
        "invalid_rows": invalid_rows,
        "issue_count": issue_count,
        "issues": issues,
        "issues_truncated": issue_count > MAX_ISSUES,
        "summary": summarize(rows) if valid else None,
        "warnings": [
            "Preview only: nothing is saved and the active portfolio is unchanged.",
            "Synthetic data only. PD/LGD are user-supplied illustrative assumptions.",
            "No trained model, IFRS 9 ECL, regulatory capital or credit decision is produced.",
            "Duplicate checks cover this file only, not the stored portfolio.",
        ],
    }, rows


def preview_csv(raw: bytes):
    result, _ = parse_csv(raw)
    return result


def parse_import(raw: bytes, content_type: str):
    """Keep review identity separate from normalized storage identity."""
    media_type = content_type.split(";")[0].strip().lower()
    if media_type not in ("text/csv", XLSX_TYPE):
        raise HTTPException(415, "Use UTF-8 CSV or values-only XLSX")
    stored = xlsx_to_csv(raw, MAX_BYTES, MAX_ROWS) if media_type == XLSX_TYPE else raw
    result, rows = parse_csv(stored)
    result["storage_digest"] = result["digest"]
    result["digest"] = sha256(raw).hexdigest()
    result["source_format"] = "xlsx" if media_type == XLSX_TYPE else "csv"
    if media_type == XLSX_TYPE:
        result["warnings"].append(
            "XLSX is normalized to CSV values for storage; workbook formatting is not retained."
        )
    return result, rows, stored


async def read_csv_body(request: Request):
    if request.headers.get("x-aegisrisk-synthetic") != "true":
        raise HTTPException(400, "Confirm synthetic data only before previewing")
    if request.headers.get("content-type", "").split(";")[0].strip().lower() not in (
        "text/csv", XLSX_TYPE,
    ):
        raise HTTPException(415, "Use UTF-8 CSV or values-only XLSX")
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, "CSV exceeds the 256 KiB limit")
        raw.extend(chunk)
    return bytes(raw)


@router.post("/api/v1/import-preview")
async def import_preview(request: Request):
    result, _, _ = parse_import(
        await read_csv_body(request), request.headers.get("content-type", ""),
    )
    return JSONResponse(status_code=200 if result["valid"] else 422, content=result)
