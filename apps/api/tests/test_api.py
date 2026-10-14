import csv
import io
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from aegisrisk.database import Base, get_session
from aegisrisk.main import app
from aegisrisk.models import Facility


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
