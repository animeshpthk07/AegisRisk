"""Real Chromium -> Next.js proxy -> FastAPI checks on fictional data only."""

import json
import re
import time
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

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
        name = re.sub(r"[^A-Za-z0-9_-]", "_", request.node.name)[:120]
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
    ids=["wrong-extension", "empty", "oversized"],
)
def test_file_picker_rejects_unsupported_or_unbounded_files(
    page, name, content, message
):
    choose_file(page, name, content)
    alert = page.locator("#import-preview").get_by_role("alert")
    expect(alert).to_contain_text(message)
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
    ids=["missing-consent", "wrong-content-type", "too-large"],
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
    alert = page.locator("#import-preview").get_by_role("alert")
    expect(alert).to_contain_text("Simulated preview outage")
    page.unroute("**/api/import-preview")
    response = submit(page)
    assert response.status == 200
    expect(page.get_by_text(re.compile("Validation passed"))).to_be_visible()


REVIEW = re.compile("I reviewed these totals")


def fictional_csv():
    return VALID.replace(b"SYN-E2E-001", ("SYN-" + uuid4().hex[:24]).encode())


def save_snapshot(body, name="Fictional browser portfolio"):
    response = httpx.post(
        f"{BASE_URL}/api/saved-portfolios", params={"name": name},
        headers={"Content-Type": "text/csv", "X-AegisRisk-Synthetic": "true",
                 "X-AegisRisk-Reviewed": "true",
                 "X-AegisRisk-Preview-Digest": sha256(body).hexdigest()},
        content=body, timeout=10,
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["portfolio"]


def test_reviewed_snapshot_round_trip_and_reload(page):
    body = fictional_csv()
    choose_file(page, "reviewed.csv", body)
    page.get_by_role("checkbox", name=CONSENT).check()
    assert submit(page).status == 200
    save = page.get_by_role("button", name="Save reviewed portfolio", exact=True)
    expect(save).to_be_disabled()
    page.get_by_label("Saved portfolio name", exact=True).fill("Fictional E2E snapshot")
    page.get_by_role("checkbox", name=REVIEW).check()
    with page.expect_response(
        lambda response: "/api/saved-portfolios?" in response.url
        and response.request.method == "POST"
    ) as pending:
        save.click()
    assert pending.value.status == 201
    snapshot = pending.value.json()["portfolio"]
    selector = page.get_by_label("Active portfolio", exact=True)
    expect(selector).to_have_value("")
    page.get_by_role("button", name="Open saved portfolio", exact=True).click()
    expect(selector).to_have_value(snapshot["id"])
    metrics = page.get_by_role("region", name="Portfolio metrics")
    expect(metrics).to_contain_text("1 fictional facilities")
    expect(metrics).to_contain_text("1,000")
    expect(metrics).to_contain_text("₹50")
    expect(page.locator("section.insight")).to_contain_text("50.00")
    page.get_by_label("PD multiplier", exact=True).fill("2")
    page.get_by_label("LGD multiplier", exact=True).fill("1")
    page.get_by_role("button", name="Calculate scenario →", exact=True).click()
    expect(page.locator(".scenario-result")).to_contain_text("₹100")
    # Byte-identical retries reuse the immutable snapshot, never duplicate it.
    assert save_snapshot(body, "A different label")["id"] == snapshot["id"]
    page.reload()
    expect(selector).to_have_value("")
    expect(
        selector.locator("option").filter(has_text="Fictional E2E snapshot")
    ).to_have_count(1)
    selector.select_option(snapshot["id"])
    expect(metrics).to_contain_text("1 fictional facilities")
    expect(page.locator(".scenario-result")).to_have_count(0)
    selector.select_option("")
    expect(metrics).to_contain_text("40 fictional facilities")


def test_review_is_invalidated_by_name_and_file_changes(page):
    choose_file(page, "first.csv", fictional_csv())
    page.get_by_role("checkbox", name=CONSENT).check()
    assert submit(page).status == 200
    review = page.get_by_role("checkbox", name=REVIEW)
    review.check()
    page.get_by_label("Saved portfolio name", exact=True).fill("Changed fictional name")
    expect(review).not_to_be_checked()
    expect(
        page.get_by_role("button", name="Save reviewed portfolio", exact=True)
    ).to_be_disabled()
    review.check()
    choose_file(page, "second.csv", fictional_csv())
    expect(page.get_by_role("checkbox", name=CONSENT)).not_to_be_checked()
    expect(review).to_have_count(0)
    expect(
        page.get_by_role("button", name="Save reviewed portfolio", exact=True)
    ).to_have_count(0)


def test_disabled_saving_keeps_preview_available(page):
    page.route(
        "**/api/saved-portfolios?*",
        lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({"enabled": False, "items": [], "total": 0,
                             "offset": 0, "limit": 100}),
        ),
    )
    page.reload()
    page.get_by_role("button", name="Use fictional example").click()
    page.get_by_role("checkbox", name=CONSENT).check()
    assert submit(page).status == 200
    expect(
        page.get_by_role("button", name="Save reviewed portfolio", exact=True)
    ).to_have_count(0)
    expect(page.locator("#import-preview")).to_contain_text("Saving is disabled")


def test_switch_clears_pending_stress_and_ignores_old_result(page):
    snapshot = save_snapshot(fictional_csv(), "Fictional race test")
    page.reload()
    selector = page.get_by_label("Active portfolio", exact=True)
    expect(
        selector.locator("option").filter(has_text="Fictional race test")
    ).to_have_count(1)
    expect(
        page.get_by_role("region", name="Portfolio metrics")
    ).to_contain_text("40 fictional facilities")
    pending = []
    page.route("**/api/stress", lambda route: pending.append(route))
    page.get_by_role("button", name="Calculate scenario →", exact=True).click()
    expect(page.get_by_role("button", name="Calculating…", exact=True)).to_be_disabled()
    selector.select_option(snapshot["id"])
    expect(
        page.get_by_role("region", name="Portfolio metrics")
    ).to_contain_text("1 fictional facilities")
    assert len(pending) == 1
    pending[0].fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"baseline_el": 999999, "stressed_el": 999999,
                         "delta_el": 0, "delta_pct": 0, "assumptions": []}),
    )
    page.get_by_role("button", name="Calculate scenario →", exact=True).click()
    expect(page.locator(".scenario-result")).to_contain_text("₹83")
    expect(page.locator(".scenario-result")).not_to_contain_text("9,99,999")


def download_report(page):
    with page.expect_download() as pending:
        page.get_by_role("button", name="Download baseline report (JSON)", exact=True).click()
    download = pending.value
    return download, json.loads(Path(download.path()).read_text(encoding="utf-8"))


def test_download_report_matches_demo_and_selected_snapshot(page):
    metrics = page.get_by_role("region", name="Portfolio metrics")
    expect(metrics).to_contain_text("40 fictional facilities")
    download, report = download_report(page)
    assert download.suggested_filename == "aegisrisk-baseline-demo.json"
    assert report["dataset_id"] is None
    assert report["summary"]["facility_count"] == 40
    assert report["scenario_included"] is False
    body = fictional_csv()
    snapshot = save_snapshot(body, "Fictional report test")
    page.get_by_role("button", name="Refresh saved portfolios", exact=True).click()
    selector = page.get_by_label("Active portfolio", exact=True)
    expect(selector.locator("option").filter(has_text="Fictional report test")).to_have_count(1)
    selector.select_option(snapshot["id"])
    expect(metrics).to_contain_text("1 fictional facilities")
    download, report = download_report(page)
    assert download.suggested_filename == "aegisrisk-baseline-" + snapshot["id"] + ".json"
    assert report["dataset_id"] == snapshot["id"]
    assert report["summary"]["total_expected_loss"] == 50
    assert report["source"]["input_rows"][0]["ead"] == "1000"
    assert report["report_kind"] == "baseline_only"
    assert report["explanation"]["mode"] == "deterministic"


@pytest.mark.parametrize("failure", ["outage", "identity-mismatch"])
def test_report_failure_downloads_nothing_and_retry_recovers(page, failure):
    expect(page.get_by_role("region", name="Portfolio metrics")).to_be_visible()
    valid = httpx.get(f"{BASE_URL}/api/report", timeout=10).json()
    invalid = dict(valid, dataset_id=str(uuid4()))
    downloads = []
    page.on("download", lambda download: downloads.append(download))
    page.route(
        "**/api/report",
        lambda route: route.fulfill(
            status=503 if failure == "outage" else 200,
            content_type="application/json", body=json.dumps(invalid),
        ),
    )
    page.get_by_role("button", name="Download baseline report (JSON)", exact=True).click()
    panel = page.get_by_role("region", name="Baseline report", exact=True)
    expect(panel.get_by_role("alert")).to_be_visible()
    assert downloads == []
    page.unroute("**/api/report")
    _, report = download_report(page)
    assert report["dataset_id"] is None
    expect(panel.get_by_role("alert")).to_have_count(0)
    assert len(downloads) == 1


@pytest.mark.parametrize("switch_back", [False, True], ids=["a-to-b", "a-to-b-to-a"])
def test_switch_ignores_pending_report_download(page, switch_back):
    name = "Fictional stale report " + uuid4().hex[:8]
    snapshot = save_snapshot(fictional_csv(), name)
    stale = httpx.get(f"{BASE_URL}/api/report", timeout=10).json()
    page.reload()
    selector = page.get_by_label("Active portfolio", exact=True)
    expect(selector.locator("option").filter(has_text=name)).to_have_count(1)
    expect(page.get_by_role("region", name="Portfolio metrics")).to_contain_text(
        "40 fictional facilities"
    )
    pending = []
    downloads = []
    page.on("download", lambda download: downloads.append(download))
    page.route("**/api/report", lambda route: pending.append(route))
    page.get_by_role("button", name="Download baseline report (JSON)", exact=True).click()
    expect(page.get_by_role("button", name="Preparing report…", exact=True)).to_be_disabled()
    selector.select_option(snapshot["id"])
    expect(page.get_by_role("region", name="Portfolio metrics")).to_contain_text(
        "1 fictional facilities"
    )
    if switch_back:
        selector.select_option("")
        expect(page.get_by_role("region", name="Portfolio metrics")).to_contain_text(
            "40 fictional facilities"
        )
    assert len(pending) == 1
    pending[0].fulfill(status=200, content_type="application/json", body=json.dumps(stale))
    page.unroute("**/api/report")
    _, current = download_report(page)
    assert current["dataset_id"] == (None if switch_back else snapshot["id"])
    assert len(downloads) == 1


def test_catalog_refresh_does_not_disguise_active_dataset(page):
    snapshot = save_snapshot(fictional_csv(), "Fictional outside page")
    page.reload()
    selector = page.get_by_label("Active portfolio", exact=True)
    expect(selector.locator("option").filter(has_text="Fictional outside page")).to_have_count(1)
    selector.select_option(snapshot["id"])
    metrics = page.get_by_role("region", name="Portfolio metrics")
    expect(metrics).to_contain_text("1 fictional facilities")
    # Simulate a catalog page which does not contain the active immutable snapshot.
    page.route(
        "**/api/saved-portfolios?*",
        lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({"enabled": True, "items": [], "total": 0,
                             "offset": 0, "limit": 100}),
        ),
    )
    page.get_by_role("button", name="Refresh saved portfolios", exact=True).click()
    expect(selector).to_have_value(snapshot["id"])
    expect(selector.locator("option:checked")).to_contain_text("outside current list")
    expect(metrics).to_contain_text("1 fictional facilities")
    _, report = download_report(page)
    assert report["dataset_id"] == snapshot["id"]
    selector.select_option("")
    expect(metrics).to_contain_text("40 fictional facilities")
