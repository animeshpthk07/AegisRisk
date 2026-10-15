"""Real Chromium -> Next.js proxy -> FastAPI checks on fictional data only."""

import re
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright

BASE_URL = "http://127.0.0.1:3000"
ARTIFACTS = Path("test-results")
HEADER = "id,borrower,industry,geography,rating,pd,lgd,ead,currency,horizon\n"
VALID = (
    HEADER
    + "SYN-E2E-001,Fictional Birch,Energy,West,B,0.1,0.5,1000,INR,one_year\n"
).encode()
CONSENT = re.compile("I confirm this file contains only fictional data")


@pytest.fixture(scope="session")
def running_app():
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{BASE_URL}/api/ready", timeout=2)
            if response.status_code == 200:
                ARTIFACTS.mkdir(exist_ok=True)
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    pytest.fail("The web/API/database did not become ready within 60 seconds")


@pytest.fixture(scope="session")
def browser(running_app):
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch()
        yield instance
        instance.close()


@pytest.fixture(autouse=True)
def portfolio_is_unchanged(running_app):
    before = httpx.get(f"{BASE_URL}/api/portfolio", timeout=10)
    before.raise_for_status()
    summary = before.json()["summary"]
    assert summary["facility_count"] == 40
    yield
    after = httpx.get(f"{BASE_URL}/api/portfolio", timeout=10)
    after.raise_for_status()
    assert after.json()["summary"] == summary


@pytest.fixture
def page(browser, request):
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    tab = context.new_page()
    errors = []
    tab.on("pageerror", lambda error: errors.append(str(error)))
    tab.set_default_timeout(15000)
    tab.goto(f"{BASE_URL}/#import-preview")
    heading = tab.get_by_role("heading", name="Check a fictional portfolio CSV.")
    expect(heading).to_be_visible()
    try:
        yield tab
    finally:
        name = re.sub(r"[^A-Za-z0-9_-]", "_", request.node.name)
        try:
            tab.screenshot(path=str(ARTIFACTS / f"{name}.png"), full_page=True)
            context.tracing.stop(path=str(ARTIFACTS / f"{name}.zip"))
        finally:
            context.close()
    assert not errors, f"Uncaught browser errors: {errors}"


def submit(page):
    with page.expect_response(
        lambda response: response.url == f"{BASE_URL}/api/import-preview"
        and response.request.method == "POST"
    ) as pending:
        page.get_by_role("button", name="Validate and preview").click()
    return pending.value


def choose_file(page, name, content):
    page.get_by_label("Synthetic portfolio CSV", exact=True).set_input_files(
        {"name": name, "mimeType": "text/csv", "buffer": content}
    )


@pytest.mark.parametrize("width", [1440, 390])
def test_example_requires_consent_and_has_exact_totals(page, width):
    page.set_viewport_size({"width": width, "height": 1000})
    submit_button = page.get_by_role("button", name="Validate and preview")
    expect(submit_button).to_be_disabled()
    page.get_by_role("button", name="Use fictional example").click()
    expect(submit_button).to_be_disabled()
    page.get_by_role("checkbox", name=CONSENT).check()
    response = submit(page)
    assert response.status == 200
    result = response.json()
    assert result["persisted"] is False
    assert result["summary"]["facility_count"] == 2
    assert result["summary"]["total_ead"] == 3000
    assert result["summary"]["total_expected_loss"] == 66
    panel = page.locator("#import-preview")
    expect(panel.get_by_text(re.compile("Validation passed"))).to_be_visible()
    ead = panel.locator("article").filter(has_text="Preview EAD")
    loss = panel.locator("article").filter(has_text="Preview one-year EL")
    expect(ead.get_by_role("heading")).to_contain_text("3,000.00")
    expect(loss.get_by_role("heading")).to_contain_text("66.00")
    page.get_by_role("checkbox", name=CONSENT).uncheck()
    expect(submit_button).to_be_disabled()
    expect(panel.get_by_text("Preview EAD", exact=True)).to_have_count(0)


def test_uploaded_utf8_csv_and_example_download(page):
    with page.expect_download() as pending:
        page.get_by_role("link", name="Download example CSV").click()
    download = pending.value
    assert download.suggested_filename == "aegisrisk-synthetic-example.csv"
    assert Path(download.path()).read_text().startswith(HEADER)
    choose_file(page, "fictional.csv", b"\xef\xbb\xbf" + VALID)
    page.get_by_role("checkbox", name=CONSENT).check()
    response = submit(page)
    assert response.status == 200
    assert response.json()["summary"]["total_expected_loss"] == 50
    expect(page.get_by_text(re.compile("Validation passed"))).to_be_visible()


def test_invalid_probability_has_issues_and_no_partial_totals(page):
    invalid = VALID.replace(b",0.1,0.5,", b",2,0.5,")
    choose_file(page, "invalid.csv", invalid)
    page.get_by_role("checkbox", name=CONSENT).check()
    response = submit(page)
    assert response.status == 422
    result = response.json()
    assert result["valid"] is False
    assert result["summary"] is None
    assert result["persisted"] is False
    assert any(issue["column"] == "pd" for issue in result["issues"])
    panel = page.locator("#import-preview")
    expect(panel.get_by_text(re.compile("Validation failed"))).to_be_visible()
    expect(panel.get_by_role("table")).to_be_visible()
    expect(panel.get_by_text("Preview EAD", exact=True)).to_have_count(0)


@pytest.mark.parametrize(
    ("name", "content", "message"),
    [
        ("fictional.xlsx", VALID, "Choose a .csv file"),
        ("empty.csv", b"", "non-empty CSV"),
        ("oversized.csv", b"x" * 262145, "non-empty CSV"),
    ],
)
def test_file_picker_rejects_unsupported_or_unbounded_files(
    page, name, content, message
):
    choose_file(page, name, content)
    expect(page.get_by_role("alert")).to_contain_text(message)
    button = page.get_by_role("button", name="Validate and preview")
    expect(button).to_be_disabled()


@pytest.mark.parametrize(
    ("headers", "body", "status"),
    [
        ({"Content-Type": "text/csv"}, VALID, 400),
        ({"Content-Type": "application/json",
          "X-AegisRisk-Synthetic": "true"}, VALID, 415),
        ({"Content-Type": "text/csv",
          "X-AegisRisk-Synthetic": "true"}, b"x" * 262145, 413),
    ],
)
def test_proxy_enforces_acknowledgement_type_and_size(headers, body, status):
    response = httpx.post(
        f"{BASE_URL}/api/import-preview", headers=headers, content=body,
        timeout=10,
    )
    assert response.status_code == status


def test_backend_error_is_visible_and_retry_recovers(page):
    # Deliberate fault injection only; other tests use the real API unchanged.
    page.route(
        "**/api/import-preview",
        lambda route: route.fulfill(
            status=503, content_type="application/json",
            body='{"detail":"Simulated preview outage"}',
        ),
    )
    page.get_by_role("button", name="Use fictional example").click()
    page.get_by_role("checkbox", name=CONSENT).check()
    page.get_by_role("button", name="Validate and preview").click()
    expect(page.get_by_role("alert")).to_contain_text("Simulated preview outage")
    page.unroute("**/api/import-preview")
    response = submit(page)
    assert response.status == 200
    expect(page.get_by_text(re.compile("Validation passed"))).to_be_visible()
