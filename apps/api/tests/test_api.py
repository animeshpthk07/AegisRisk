import csv
import io
from decimal import Decimal
from hashlib import sha256
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from aegisrisk.database import Base, get_session
from aegisrisk.main import app
from aegisrisk.models import Facility, SavedPortfolio


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            Facility(
                id="A",
                borrower="Fictional A",
                industry="Energy",
                geography="West",
                rating="B",
                pd=Decimal(".1"),
                lgd=Decimal(".5"),
                ead=Decimal(1000),
            )
        )
        session.commit()

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def test_health_and_ready(client):
    assert client.get("/api/v1/health").json()["external_ai"] is False
    assert client.get("/api/v1/ready").json()["database"] == "connected"


def test_portfolio(client):
    response = client.get("/api/v1/portfolio")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.json()["summary"]["total_expected_loss"] == 50
    assert response.json()["synthetic"] is True


def test_pagination_search(client):
    assert client.get("/api/v1/facilities?q=Fictional&limit=1").json()["total"] == 1
    assert client.get("/api/v1/facilities?q=%25").json()["total"] == 0
    assert client.get("/api/v1/facilities?offset=1").json()["items"] == []
    assert client.get("/api/v1/facilities?limit=1000").status_code == 422
    assert client.get("/api/v1/facilities?offset=-1").status_code == 422


def test_stress(client):
    result = client.post(
        "/api/v1/stress", json={"pd_multiplier": 2, "lgd_multiplier": 1, "ead_multiplier": 1}
    ).json()
    assert result["baseline_el"] == 50
    assert result["stressed_el"] == 100
    assert result["delta_pct"] == 1


def test_stress_probability_cap(client):
    result = client.post(
        "/api/v1/stress", json={"pd_multiplier": 10, "lgd_multiplier": 10, "ead_multiplier": 1}
    ).json()
    assert result["stressed_el"] == 1000


@pytest.mark.parametrize(
    "payload",
    [
        {"pd_multiplier": -1},
        {"pd_multiplier": "NaN"},
        {"pd_multiplier": 11},
        {"unknown": 1},
        {"industry": "Not real"},
    ],
)
def test_invalid_stress(client, payload):
    assert client.post("/api/v1/stress", json=payload).status_code == 422


def test_grounded_explanation(client):
    result = client.get("/api/v1/explanation").json()
    assert result["mode"] == "deterministic"
    assert "50.00" in result["text"]
    assert "1,000.00" in result["text"]


PREVIEW_HEADERS = {"content-type": "text/csv", "x-aegisrisk-synthetic": "true"}
CSV_COLUMNS = ["id", "borrower", "industry", "geography", "rating", "pd", "lgd", "ead",
               "currency", "horizon"]
CSV_ROW = ["SYN-CSV-001", "Fictional Orchard", "Energy", "West", "B", "0.1", "0.5",
           "1000.00", "INR", "one_year"]


def csv_body(rows=None, columns=None):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(CSV_COLUMNS if columns is None else columns)
    writer.writerows([CSV_ROW] if rows is None else rows)
    return output.getvalue().encode("utf-8")


def preview(client, body, headers=None):
    return client.post("/api/v1/import-preview", content=body,
                       headers=PREVIEW_HEADERS if headers is None else headers)


def test_preview_is_accurate_and_read_only(client):
    before = client.get("/api/v1/portfolio").json()
    result = preview(client, csv_body()).json()
    assert result["valid"] is True
    assert result["persisted"] is False
    assert result["summary"]["total_expected_loss"] == 50
    assert result["summary"]["total_ead"] == 1000
    assert result["summary"]["borrower_hhi"] == 1
    assert result["row_count"] == result["valid_rows"] == 1
    assert result["issues"] == []
    assert client.get("/api/v1/portfolio").json() == before


def test_preview_utf8_bom_reordered_headers_and_quoted_text(client):
    row = CSV_ROW.copy()
    row[1] = "Fictional Orchard, Ltd"
    result = preview(client, b"\xef\xbb\xbf" + csv_body([row[::-1]], CSV_COLUMNS[::-1]))
    assert result.status_code == 200
    assert result.json()["summary"]["total_expected_loss"] == 50


@pytest.mark.parametrize("field,value", [
    ("pd", "NaN"), ("pd", "Infinity"), ("pd", "1e-3"), ("pd", "1a2"),
    ("pd", "-0.1"), ("pd", "1.01"), ("lgd", "101"), ("pd", "0.12345678901"),
    ("ead", "1000.001"), ("ead", "1000000000001"), ("ead", "1,000"), ("ead", ""),
    ("currency", "USD"), ("horizon", "lifetime"), ("id", "bad/id"),
    ("borrower", "=SUM(A1)"), ("borrower", "@formula"), ("borrower", ""),
    ("borrower", "a" * 101), ("borrower", "two\nlines"), ("rating", "a" * 9),
])
def test_preview_rejects_invalid_rows_without_partial_summary(client, field, value):
    row = CSV_ROW.copy()
    row[0] = "SYN-CSV-002"
    row[CSV_COLUMNS.index(field)] = value
    result = preview(client, csv_body([CSV_ROW, row]))
    assert result.status_code == 422
    data = result.json()
    assert data["valid"] is False
    assert data["summary"] is None
    assert data["invalid_rows"] == 1
    assert any(issue["column"] == field and issue["row"] == 3 for issue in data["issues"])
    assert data["persisted"] is False


def test_preview_duplicate_ids_case_insensitive(client):
    row = CSV_ROW.copy()
    row[0] = " syn-csv-001 "
    data = preview(client, csv_body([CSV_ROW, row])).json()
    assert data["summary"] is None
    assert data["issues"][0]["code"] == "duplicate"


def test_preview_zero_exposure_and_boundary_probabilities(client):
    row = CSV_ROW.copy()
    row[5:8] = ["0", "1", "0"]
    data = preview(client, csv_body([row])).json()
    assert data["valid"] is True
    assert data["summary"]["total_expected_loss"] == 0
    assert data["summary"]["weighted_pd"] is None
    assert data["summary"]["borrower_hhi"] is None


@pytest.mark.parametrize("body", [
    b"", b"\xff", b"id,borrower\nA,B", csv_body([]),
    csv_body(columns=CSV_COLUMNS[:-1] + ["currency"]),
    csv_body() + b'"unterminated', csv_body([CSV_ROW[:-1]]),
    csv_body([CSV_ROW + ["extra"]]),
])
def test_preview_rejects_malformed_files(client, body):
    assert preview(client, body).status_code == 422


def test_preview_requires_acknowledgement_and_content_type(client):
    assert preview(client, csv_body(), {"content-type": "text/csv"}).status_code == 400
    assert preview(client, csv_body(), {"x-aegisrisk-synthetic": "true"}).status_code == 415


def test_preview_size_and_row_limits(client):
    assert preview(client, b"x" * 262_145).status_code == 413
    rows = []
    for index in range(1001):
        row = CSV_ROW.copy()
        row[0] = f"SYN-{index}"
        rows.append(row)
    assert preview(client, csv_body(rows[:1000])).status_code == 200
    assert preview(client, csv_body(rows)).status_code == 413


def test_preview_bounds_error_output(client):
    data = preview(client, csv_body([CSV_ROW] * 102)).json()
    assert data["issue_count"] == 101
    assert len(data["issues"]) == 100
    assert data["issues_truncated"] is True
    assert data["summary"] is None


@pytest.fixture
def saved_client(client, monkeypatch):
    monkeypatch.setenv("SYNTHETIC_IMPORTS_ENABLED", "true")
    return client


def save_csv(client, body=None, **header_overrides):
    body = csv_body() if body is None else body
    headers = PREVIEW_HEADERS | {
        "x-aegisrisk-reviewed": "true",
        "x-aegisrisk-preview-digest": sha256(body).hexdigest(),
    } | header_overrides
    return client.post("/api/v1/saved-portfolios?name=Fictional%20test", content=body,
                       headers=headers)


def test_saving_is_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv("SYNTHETIC_IMPORTS_ENABLED", raising=False)
    assert client.get("/api/v1/saved-portfolios").json()["enabled"] is False
    assert save_csv(client).status_code == 403
    assert preview(client, csv_body()).status_code == 200


def test_save_roundtrip_is_independent_and_idempotent(saved_client):
    client = saved_client
    before = client.get("/api/v1/portfolio").json()
    row = CSV_ROW.copy()
    row[5:8] = ["0.2", "0.5", "3210.99"]
    body = b"\xef\xbb\xbf" + csv_body([row])
    reviewed = preview(client, body).json()
    assert reviewed["digest"] == sha256(body).hexdigest()
    response = save_csv(client, body)
    assert response.status_code == 201
    saved = response.json()["portfolio"]
    assert "csv_text" not in saved
    assert saved["digest"] == reviewed["digest"]
    params = {"dataset_id": saved["id"]}
    selected = client.get("/api/v1/portfolio", params=params).json()
    assert selected["summary"] == reviewed["summary"]
    assert selected["facilities"][0]["id"] == CSV_ROW[0]
    assert selected["facilities"][0]["ead"] == 3210.99
    assert selected["dataset_id"] == saved["id"]
    exposures = client.get("/api/v1/facilities", params=params | {"q": "orchard"}).json()
    assert exposures["total"] == 1
    stress = client.post("/api/v1/stress", params=params,
                         json={"pd_multiplier": 2, "lgd_multiplier": 1}).json()
    assert stress["baseline_el"] == 321.099
    assert stress["stressed_el"] == 642.198
    assert "321.10" in client.get("/api/v1/explanation", params=params).json()["text"]
    retry = save_csv(client, body)
    assert retry.status_code == 200
    assert retry.json()["created"] is False
    assert retry.json()["portfolio"] == saved
    assert client.get("/api/v1/saved-portfolios").json()["total"] == 1
    assert client.get("/api/v1/portfolio").json() == before


@pytest.mark.parametrize("header,value,status", [
    ("x-aegisrisk-reviewed", "false", 400),
    ("x-aegisrisk-synthetic", "false", 400),
    ("x-aegisrisk-preview-digest", "0" * 64, 409),
    ("content-type", "application/json", 415),
])
def test_save_guards_write_nothing(saved_client, header, value, status):
    assert save_csv(saved_client, **{header: value}).status_code == status
    assert saved_client.get("/api/v1/saved-portfolios").json()["total"] == 0


def test_invalid_or_changed_csv_cannot_be_saved(saved_client):
    invalid = CSV_ROW.copy()
    invalid[0] = "SYN-BAD"
    invalid[5] = "2"
    result = save_csv(saved_client, csv_body([CSV_ROW, invalid]))
    assert result.status_code == 422
    assert result.json()["persisted"] is False
    assert save_csv(saved_client, b"x" * 262_145).status_code == 413
    assert save_csv(saved_client, b"not,csv").status_code == 422
    assert saved_client.get("/api/v1/saved-portfolios").json()["total"] == 0


@pytest.mark.parametrize("name", ["", " " * 3, "=formula", "x" * 81, "two\nlines"])
def test_save_rejects_invalid_names(saved_client, name):
    result = saved_client.post("/api/v1/saved-portfolios", params={"name": name},
                               content=csv_body(), headers=PREVIEW_HEADERS)
    assert result.status_code == 422
    assert saved_client.get("/api/v1/saved-portfolios").json()["total"] == 0


def test_saved_list_pagination_and_unknown_ids(saved_client):
    save_csv(saved_client)
    assert saved_client.get("/api/v1/saved-portfolios?offset=1").json()["items"] == []
    assert saved_client.get("/api/v1/saved-portfolios?limit=101").status_code == 422
    for resource in ("portfolio", "facilities", "explanation"):
        assert saved_client.get(f"/api/v1/{resource}?dataset_id={uuid4()}").status_code == 404
        assert saved_client.get(f"/api/v1/{resource}?dataset_id=invalid").status_code == 422
    assert saved_client.post(f"/api/v1/stress?dataset_id={uuid4()}", json={}).status_code == 404


def test_storage_error_leaves_no_partial_snapshot(saved_client, monkeypatch):
    def broken_commit(self):
        raise SQLAlchemyError("private storage details must not be returned")
    monkeypatch.setattr(Session, "commit", broken_commit)
    response = save_csv(saved_client)
    assert response.status_code == 503
    assert response.json() == {"detail": "Data service unavailable"}
    assert saved_client.get("/api/v1/saved-portfolios").json()["total"] == 0


def test_corrupt_snapshot_fails_closed(saved_client):
    saved = save_csv(saved_client).json()["portfolio"]
    sessions = app.dependency_overrides[get_session]()
    session = next(sessions)
    try:
        snapshot = session.get(SavedPortfolio, saved["id"])
        snapshot.csv_text = snapshot.csv_text.replace("1000.00", "2000.00")
        session.commit()
    finally:
        sessions.close()
    response = saved_client.get("/api/v1/portfolio", params={"dataset_id": saved["id"]})
    assert response.status_code == 503
    assert response.json() == {"detail": "Saved portfolio integrity check failed"}
