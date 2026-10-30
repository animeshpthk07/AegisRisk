"""Real browser/proxy/API isolation using disposable tokens and a fresh database."""

import json
import os
import re
import secrets
import signal
import socket
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "test-results"
BODY = ("id,borrower,industry,geography,rating,pd,lgd,ead,currency,horizon\n"
        "SYN-PRIVATE-1,Fictional Private Birch,Energy,West,B,0.1,0.5,"
        "1000,INR,one_year\n").encode()


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def private_app(tmp_path_factory):
    folder = tmp_path_factory.mktemp("workspace-access")
    ARTIFACTS.mkdir(exist_ok=True)
    tokens = [secrets.token_urlsafe(32) for _ in range(3)]
    workspace = str(uuid4())
    records = [{"subject": str(uuid4()),
                "workspace": str(uuid4()) if i == 1 else workspace,
                "role": "viewer" if i == 2 else "analyst",
                "token_sha256": sha256(token.encode()).hexdigest(),
                "expires_at": int(time.time()) + 3600}
               for i, token in enumerate(tokens)]
    api_port, web_port = free_port(), free_port()
    while web_port == api_port:
        web_port = free_port()
    base = f"http://127.0.0.1:{web_port}"
    env = os.environ | {
        "DATABASE_URL": f"sqlite:///{folder / 'private.db'}",
        "AEGISRISK_ACCESS_MODE": "token",
        "AEGISRISK_ACCESS_USERS": json.dumps(records),
        "SYNTHETIC_IMPORTS_ENABLED": "true",
        "API_BASE_URL": f"http://127.0.0.1:{api_port}",
        "NEXT_TELEMETRY_DISABLED": "1",
    }
    subprocess.run(["alembic", "upgrade", "head"],
                   cwd=ROOT / "apps/api", env=env, check=True)
    subprocess.run([sys.executable, "-m", "aegisrisk.seed"], env=env, check=True)
    processes = []
    logs = []
    try:
        for name, args in (
            ("access-api", [sys.executable, "-m", "uvicorn", "aegisrisk.main:app",
                            "--host", "127.0.0.1", "--port", str(api_port)]),
            ("access-web", ["pnpm", "--dir", str(ROOT / "apps/web"), "exec", "next",
                            "start", "--hostname", "127.0.0.1",
                            "--port", str(web_port)]),
        ):
            log = (ARTIFACTS / f"{name}.log").open("w")
            logs.append(log)
            processes.append(subprocess.Popen(args, cwd=ROOT, env=env, stdout=log,
                             stderr=subprocess.STDOUT, start_new_session=True))
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                if httpx.get(base + "/api/ready", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
        else:
            pytest.fail("Isolated token-mode application did not become ready")
        headers = {"Authorization": "Bearer " + tokens[0], "Origin": base,
                   "Content-Type": "text/csv", "X-AegisRisk-Synthetic": "true",
                   "X-AegisRisk-Reviewed": "true",
                   "X-AegisRisk-Preview-Digest": sha256(BODY).hexdigest()}
        saved = httpx.post(
            base + "/api/saved-portfolios?name=Fictional%20access%20seed",
                           headers=headers, content=BODY, timeout=15)
        assert saved.status_code == 201
        yield {"url": base, "tokens": tokens, "records": records,
               "saved_id": saved.json()["portfolio"]["id"]}
    finally:
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        for log in logs:
            log.close()


@pytest.fixture(scope="session")
def private_browser(private_app):
    with sync_playwright() as playwright:
        engine = os.environ.get("AEGISRISK_BROWSER", "chromium")
        instance = getattr(playwright, engine).launch()
        yield instance
        instance.close()


@pytest.fixture
def page(private_app, private_browser, request):
    context = private_browser.new_context(viewport={"width": 1440, "height": 1000})
    tab = context.new_page()
    tab.set_default_timeout(15000)
    errors = []
    tab.on("pageerror", lambda error: errors.append(str(error)))
    tab.goto(private_app["url"])
    expect(tab.get_by_role("heading", name="Unlock your workspace")).to_be_visible()
    try:
        yield tab
    finally:
        # No tracing: request traces would contain even these disposable credentials.
        name = re.sub(r"[^A-Za-z0-9_-]", "_", request.node.name)
        tab.screenshot(path=str(ARTIFACTS / f"access-{name}.png"), full_page=True)
        context.close()
    assert not errors


def unlock(page, app, index=0):
    page.get_by_label("Access token", exact=True).fill(app["tokens"][index])
    page.get_by_role("button", name="Unlock workspace", exact=True).click()
    expect(page.get_by_label("Workspace access", exact=True)).to_be_visible()
    expect(page.get_by_label("Active portfolio", exact=True)).to_be_enabled()


@pytest.mark.parametrize("width", [1440, 320])
def test_keyboard_unlock_reload_and_memory_only_token(page, private_app, width):
    page.set_viewport_size({"width": width, "height": 1000})
    expect(page.get_by_label("Active portfolio", exact=True)).to_have_count(0)
    field = page.get_by_label("Access token", exact=True)
    field.fill("x" * 43)
    field.press("Enter")
    expect(page.locator(".access-screen").get_by_role("alert")).to_contain_text(
        "invalid, expired or revoked"
    )
    expect(field).to_have_value("")
    field.fill(private_app["tokens"][0])
    field.press("Tab")
    expect(page.get_by_role(
        "button", name="Unlock workspace", exact=True
    )).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_label("Workspace access")).to_contain_text("Analyst workspace")
    storage = page.evaluate(
        "JSON.stringify([Object.entries(localStorage),"
        "Object.entries(sessionStorage), document.cookie])"
    )
    assert all(token not in storage and token not in page.url
               for token in private_app["tokens"])
    page.get_by_role("button", name="Lock workbench").click()
    expect(field).to_be_focused()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    unlock(page, private_app)
    page.reload()
    expect(page.get_by_role("heading", name="Unlock your workspace")).to_be_visible()
    expect(page.get_by_label("Active portfolio", exact=True)).to_have_count(0)


def test_save_lock_switch_workspace_and_foreign_export(page, private_app):
    unlock(page, private_app)
    page.get_by_role("button", name="Use fictional example").click()
    page.get_by_role(
        "checkbox", name=re.compile("I confirm this file contains only fictional")
    ).check()
    page.get_by_role("button", name="Validate and preview").click()
    expect(page.get_by_text(re.compile("Validation passed"))).to_be_visible()
    name = "Private browser snapshot"
    page.get_by_label("Saved portfolio name", exact=True).fill(name)
    page.get_by_role("checkbox", name=re.compile("I reviewed these totals")).check()
    with page.expect_response(
        lambda r: "/api/saved-portfolios?" in r.url and r.request.method == "POST"
    ) as saved:
        page.get_by_role("button", name="Save reviewed portfolio", exact=True).click()
    assert saved.value.status == 201
    saved_id = saved.value.json()["portfolio"]["id"]
    page.get_by_role("button", name="Open saved portfolio", exact=True).click()
    expect(page.get_by_label("Active portfolio", exact=True)).to_have_value(saved_id)
    page.get_by_role("button", name="Lock workbench").click()
    expect(page.get_by_text(name, exact=True)).to_have_count(0)
    unlock(page, private_app, 1)
    expect(page.get_by_label("Active portfolio", exact=True)).to_have_value("")
    expect(page.get_by_role("option", name=re.compile(name))).to_have_count(0)
    expect(page.get_by_text(re.compile("Validation passed"))).to_have_count(0)
    response = httpx.get(
        private_app["url"] + "/api/report", params={"dataset_id": saved_id},
        headers={"Authorization": "Bearer " + private_app["tokens"][1]},
                         timeout=10)
    assert response.status_code == 404


def test_viewer_can_preview_but_never_save(page, private_app):
    unlock(page, private_app, 2)
    expect(page.get_by_label("Workspace access")).to_contain_text("Read-only workspace")
    selector = page.get_by_label("Active portfolio", exact=True)
    selector.select_option(private_app["saved_id"])
    expect(selector).to_have_value(private_app["saved_id"])
    page.get_by_role("button", name="Use fictional example").click()
    page.get_by_role(
        "checkbox", name=re.compile("I confirm this file contains only fictional")
    ).check()
    page.get_by_role("button", name="Validate and preview").click()
    expect(page.get_by_text(re.compile("Validation passed"))).to_be_visible()
    expect(page.get_by_role(
        "button", name="Save reviewed portfolio", exact=True
    )).to_have_count(0)
    response = httpx.get(
        private_app["url"] + "/api/report",
        params={"dataset_id": private_app["saved_id"]},
        headers={"Authorization": "Bearer " + private_app["tokens"][2]},
                         timeout=10)
    assert response.status_code == 200


def test_rejected_access_clears_workspace_and_pending_ui(page, private_app):
    unlock(page, private_app)
    page.route("**/api/stress*", lambda route: route.fulfill(
        status=401, content_type="application/json",
        body='{"detail":"Valid access token required"}'))
    page.get_by_role("button", name="Calculate scenario →", exact=True).click()
    expect(page.get_by_role("heading", name="Unlock your workspace")).to_be_visible()
    expect(page.get_by_label("Active portfolio", exact=True)).to_have_count(0)
    expect(page.get_by_label("Access token", exact=True)).to_have_value("")


def test_access_outage_fails_closed_and_retry_recovers(page, private_app):
    page.route("**/api/access", lambda route: route.fulfill(
        status=503, content_type="application/json", body='{"detail":"Unavailable"}'))
    page.reload()
    expect(page.locator(".access-screen").get_by_role("alert")).to_contain_text(
        "Access service unavailable"
    )
    expect(page.get_by_label("Active portfolio", exact=True)).to_have_count(0)
    page.unroute("**/api/access")
    page.get_by_role("button", name="Retry connection").click()
    unlock(page, private_app)


@pytest.mark.parametrize(
    "authorization", [None, "Basic abc", "Bearer short", "Bearer " + "x" * 43]
)
def test_proxy_rejects_missing_or_invalid_identity(private_app, authorization):
    headers = {} if authorization is None else {"Authorization": authorization}
    response = httpx.get(private_app["url"] + "/api/portfolio",
                         headers=headers, timeout=10)
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


def test_proxy_ignores_claimed_workspace_and_user_headers(private_app):
    headers = {"Authorization": "Bearer " + private_app["tokens"][0],
               "X-Workspace-Id": private_app["records"][1]["workspace"],
               "X-User-Id": private_app["records"][1]["subject"]}
    response = httpx.get(private_app["url"] + "/api/access",
                         headers=headers, timeout=10)
    assert response.status_code == 200
    assert response.json()["workspace"] == private_app["records"][0]["workspace"]
    assert response.json()["subject"] == private_app["records"][0]["subject"]
