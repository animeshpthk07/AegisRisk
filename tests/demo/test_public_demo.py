"""Checks for the disposable public-demo image; never a live deployment."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright
from pypdf import PdfReader

URL = "http://127.0.0.1:3000"
ARTIFACTS = Path("test-results/demo")


@pytest.fixture(scope="session", autouse=True)
def ready():
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            if httpx.get(URL + "/healthz", timeout=3).status_code == 200:
                ARTIFACTS.mkdir(parents=True, exist_ok=True)
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    pytest.fail("Public demo did not become ready within 120 seconds")


@pytest.mark.parametrize("kind", ["baseline", "scenario"])
def test_real_browser_downloads_all_report_formats(kind):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            page.goto(URL)
            expect(page.get_by_role("region", name="Portfolio metrics"))\
                .to_contain_text("40 fictional facilities")
            if kind == "scenario":
                page.get_by_label("PD multiplier", exact=True).fill("2")
                page.get_by_label("LGD multiplier", exact=True).fill("1")
                page.get_by_label("EAD multiplier", exact=True).fill("1")
                page.get_by_role(
                    "button", name="Calculate scenario →", exact=True
                ).click()
                expect(page.locator(".scenario-result")).to_be_visible()
            for fmt in ("JSON", "HTML", "PDF"):
                # HTML is labelled printable in the product.
                label = (f"Download {kind} report ({fmt})" if fmt != "HTML"
                         else f"Download {kind} report (printable HTML)")
                with page.expect_download() as pending:
                    page.get_by_role("button", name=label, exact=True).click()
                download = pending.value
                content = Path(download.path()).read_bytes()
                assert download.suggested_filename.endswith("." + fmt.lower())
                if fmt == "JSON":
                    report = json.loads(content)
                    assert report["dataset_id"] is None
                    assert report["scenario_included"] is (kind == "scenario")
                    summary = (report["baseline"]["summary"]
                               if kind == "scenario" else report["summary"])
                    assert summary["facility_count"] == 40
                    assert summary["total_expected_loss"] == 2769125
                    if kind == "scenario":
                        assert report["scenario"]["inputs"]["pd_multiplier"] == 2
                elif fmt == "PDF":
                    assert content.startswith(b"%PDF-")
                    reader = PdfReader(BytesIO(content), strict=True)
                    text = "\n".join(p.extract_text() for p in reader.pages)
                    assert "NOT A CREDIT DECISION" in text
                    assert "demo-v1" in text
                else:
                    assert b"demo-v1" in content
                    assert b"<html" in content.lower()
                download.save_as(str(ARTIFACTS / download.suggested_filename))
            assert not errors, errors
        finally:
            page.screenshot(path=str(ARTIFACTS / f"{kind}.png"), full_page=True)
            context.tracing.stop(path=str(ARTIFACTS / f"{kind}.zip"))
            context.close()
            browser.close()


def test_transport_rejects_oversize_and_then_recovers():
    response = httpx.post(URL + "/api/import-preview", content=b"x" * 600000)
    assert response.status_code == 413
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "transport limit" in response.json()["detail"]
    assert httpx.get(URL + "/healthz").status_code == 200


def test_shared_rate_budget_rejects_bursts_and_recovers():
    # Synthetic local CI traffic only; not a load test against a hosted service.
    with httpx.Client(base_url=URL, timeout=10) as client:
        def request(index):
            # A spoofed forwarding header must not create a new quota bucket.
            return client.get(
                "/api/portfolio",
                headers={"X-Forwarded-For": f"192.0.2.{index}"},
            )
        with ThreadPoolExecutor(max_workers=16) as pool:
            responses = list(pool.map(request, range(100)))
        limited = [r for r in responses if r.status_code == 429]
        assert limited, {r.status_code for r in responses}
        assert all(r.headers.get("retry-after") == "5" for r in limited)
        time.sleep(6)
        recovered = client.get("/api/portfolio")
        assert recovered.status_code == 200
        assert recovered.json()["summary"]["facility_count"] == 40
