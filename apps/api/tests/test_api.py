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
