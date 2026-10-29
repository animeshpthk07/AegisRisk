"""Boundary and ownership regressions using disposable fictional identities."""

import json
import secrets
import time
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from test_api import client as client  # noqa: PLC0414 - re-export the pytest fixture
from test_api import csv_body, save_csv

from aegisrisk import database
from aegisrisk.access import authenticate, current_principal


@pytest.fixture
def identities(monkeypatch):
    workspace = str(uuid4())
    tokens = [secrets.token_urlsafe(32) for _ in range(3)]
    records = [{
        "subject": str(uuid4()), "workspace": workspace if i != 1 else str(uuid4()),
        "role": "viewer" if i == 2 else "analyst",
        "token_sha256": sha256(token.encode()).hexdigest(),
        "expires_at": int(time.time()) + 3600,
    } for i, token in enumerate(tokens)]
    monkeypatch.setenv("AEGISRISK_ACCESS_MODE", "token")
    monkeypatch.setenv("AEGISRISK_ACCESS_USERS", json.dumps(records))
    monkeypatch.setenv("SYNTHETIC_IMPORTS_ENABLED", "true")
    return records, [{"Authorization": f"Bearer {token}"} for token in tokens]


@pytest.mark.parametrize("method,resource", [
    ("get", "portfolio"), ("get", "facilities"), ("get", "explanation"),
    ("get", "report"), ("get", "report-pdf"), ("get", "saved-portfolios"),
    ("get", "model-card"), ("get", "access"), ("post", "stress"),
    ("post", "scenario-report"), ("post", "scenario-report-pdf"),
    ("post", "import-preview"), ("post", "saved-portfolios"), ("post", "model-predict"),
])
def test_all_data_endpoints_require_identity(client, identities, method, resource):
    response = getattr(client, method)(f"/api/v1/{resource}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Valid access token required"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("value", ["", "Bearer short", "Basic abc", "Bearer " + "x" * 43,
                                   "Bearer " + "x" * 44, "Bearer " + "é" * 43])
def test_invalid_tokens_do_not_expose_data(client, identities, value):
    # Unicode is checked at the authentication function through a raw ASGI header below.
    if "é" in value:
        request = Request({"type": "http", "headers": [(b"authorization", value.encode())]})
        with pytest.raises(HTTPException) as error:
            authenticate(request)
        assert error.value.status_code == 401
    else:
        assert client.get("/api/v1/portfolio", headers={"Authorization": value}).status_code == 401


def test_token_expiration_revocation_and_forged_identity(client, identities, monkeypatch):
    records, headers = identities
    assert client.get("/api/v1/access", headers=headers[0]).json()["workspace"] == records[0]["workspace"]
    forged = headers[0] | {"X-Workspace-Id": records[1]["workspace"], "X-User-Id": records[1]["subject"]}
    assert client.get("/api/v1/access", headers=forged).json()["subject"] == records[0]["subject"]
    records[0]["expires_at"] = 1
    monkeypatch.setenv("AEGISRISK_ACCESS_USERS", json.dumps(records))
    assert client.get("/api/v1/portfolio", headers=headers[0]).status_code == 401
    records.pop(0)
    monkeypatch.setenv("AEGISRISK_ACCESS_USERS", json.dumps(records))
    assert client.get("/api/v1/portfolio", headers=headers[0]).status_code == 401
    assert client.get("/api/v1/portfolio", headers=headers[1]).status_code == 200
    assert client.get("/api/v1/portfolio").status_code == 401
    assert current_principal.get() is None


def test_duplicate_authorization_is_rejected(client, identities):
    _, headers = identities
    response = client.get("/api/v1/portfolio", headers=[
        ("Authorization", headers[0]["Authorization"]),
        ("Authorization", headers[1]["Authorization"]),
    ])
    assert response.status_code == 401


@pytest.mark.parametrize("raw", ["", "{}", "[]", "null", "not json", "[{}]", "x" * 32769])
def test_invalid_configuration_fails_closed(client, monkeypatch, raw):
    monkeypatch.setenv("AEGISRISK_ACCESS_MODE", "token")
    monkeypatch.setenv("AEGISRISK_ACCESS_USERS", raw)
    assert client.get("/api/v1/portfolio").status_code == 503
    assert client.get("/api/v1/ready").status_code == 503
    assert client.get("/api/v1/health").status_code == 200
    assert raw not in client.get("/api/v1/portfolio").text or raw == ""


@pytest.mark.parametrize("key,value", [("workspace", "local"), ("subject", "bad-id"),
    ("role", "admin"), ("token_sha256", "plaintext"), ("expires_at", True),
    ("expires_at", -1), ("extra", "ignored")])
def test_invalid_user_record_disables_access(client, identities, monkeypatch, key, value):
    records, headers = identities
    records[0][key] = value
    monkeypatch.setenv("AEGISRISK_ACCESS_USERS", json.dumps(records))
    assert client.get("/api/v1/portfolio", headers=headers[1]).status_code == 503


def test_unknown_mode_and_missing_config_fail_closed(client, monkeypatch):
    monkeypatch.setenv("AEGISRISK_ACCESS_MODE", "tokne")
    assert client.get("/api/v1/portfolio").status_code == 503
    monkeypatch.setenv("AEGISRISK_ACCESS_MODE", "token")
    monkeypatch.delenv("AEGISRISK_ACCESS_USERS", raising=False)
    assert client.get("/api/v1/portfolio").status_code == 503


def test_workspace_catalog_and_duplicate_bytes_are_independent(client, identities):
    _, headers = identities
    first = save_csv(client, **headers[0])
    second = save_csv(client, **headers[1])
    assert first.status_code == second.status_code == 201
    one, two = first.json()["portfolio"], second.json()["portfolio"]
    assert one["id"] != two["id"]
    for header, own in zip(headers[:2], (one, two), strict=True):
        catalog = client.get("/api/v1/saved-portfolios", headers=header).json()
        assert catalog["items"] == [own] and catalog["total"] == 1
        assert client.get("/api/v1/saved-portfolios?offset=1", headers=header).json()["items"] == []
        retry = save_csv(client, **header)
        assert retry.status_code == 200 and retry.json()["created"] is False
        assert retry.json()["portfolio"] == own


@pytest.mark.parametrize("method,resource", [("get", "portfolio"), ("get", "facilities"),
    ("get", "explanation"), ("get", "report"), ("get", "report-pdf"),
    ("post", "stress"), ("post", "scenario-report"), ("post", "scenario-report-pdf")])
def test_foreign_snapshot_cannot_be_read_or_exported(client, identities, method, resource):
    _, headers = identities
    saved = save_csv(client, **headers[0]).json()["portfolio"]["id"]
    options = {"json": {}} if method == "post" else {}
    own = getattr(client, method)(f"/api/v1/{resource}?dataset_id={saved}", headers=headers[0], **options)
    assert own.status_code == 200
    foreign = getattr(client, method)(f"/api/v1/{resource}?dataset_id={saved}", headers=headers[1], **options)
    unknown = getattr(client, method)(f"/api/v1/{resource}?dataset_id={uuid4()}", headers=headers[1], **options)
    assert foreign.status_code == unknown.status_code == 404
    assert foreign.json() == unknown.json() == {"detail": "Saved portfolio not found"}


def test_viewer_can_review_own_workspace_but_cannot_save(client, identities):
    _, headers = identities
    saved = save_csv(client, **headers[0]).json()["portfolio"]["id"]
    assert client.get(f"/api/v1/report?dataset_id={saved}", headers=headers[2]).status_code == 200
    assert save_csv(client, **headers[2]).status_code == 403
    assert client.get("/api/v1/saved-portfolios", headers=headers[2]).json()["total"] == 1


def test_legacy_local_snapshots_never_become_private_user_data(client, identities, monkeypatch):
    _, headers = identities
    monkeypatch.setenv("AEGISRISK_ACCESS_MODE", "local")
    saved = save_csv(client).json()["portfolio"]["id"]
    monkeypatch.setenv("AEGISRISK_ACCESS_MODE", "token")
    assert client.get("/api/v1/saved-portfolios", headers=headers[0]).json()["total"] == 0
    assert client.get(f"/api/v1/report?dataset_id={saved}", headers=headers[0]).status_code == 404
    monkeypatch.setenv("AEGISRISK_ACCESS_MODE", "local")
    assert client.get(f"/api/v1/report?dataset_id={saved}").status_code == 200


def test_migration_preserves_legacy_data_and_blocks_unsafe_downgrade(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    monkeypatch.setattr(database, "engine", engine)
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(config, "0002")
    row = {"id": str(uuid4()), "name": "Fictional legacy", "digest": sha256(csv_body()).hexdigest(),
           "csv_text": csv_body().decode(), "row_count": 1, "created_at": "2026-01-01T00:00:00+00:00"}
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO saved_portfolios (id,name,digest,csv_text,row_count,created_at) "
                                "VALUES (:id,:name,:digest,:csv_text,:row_count,:created_at)"), row)
    command.upgrade(config, "head")
    with engine.connect() as connection:
        stored = connection.execute(text("SELECT * FROM saved_portfolios")).mappings().one()
        assert stored["workspace_id"] == "local"
        assert all(stored[key] == value for key, value in row.items())
    private = row | {"id": str(uuid4()), "workspace_id": str(uuid4())}
    insert = text("INSERT INTO saved_portfolios (id,name,digest,csv_text,row_count,created_at,workspace_id) "
                  "VALUES (:id,:name,:digest,:csv_text,:row_count,:created_at,:workspace_id)")
    with engine.begin() as connection:
        connection.execute(insert, private)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(insert, private | {"id": str(uuid4())})
    with pytest.raises(RuntimeError, match="Cannot downgrade"):
        command.downgrade(config, "0002")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM saved_portfolios")) == 2
    engine.dispose()
