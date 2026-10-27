"""HTTP-only checks for an isolated, fictional Docker Compose test stack."""

import argparse
import json
import os
import time
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:3000/api"
STATE = Path("test-results/container-state.json")
BODY = (
    "id,borrower,industry,geography,rating,pd,lgd,ead,currency,horizon\n"
    "SYN-CONTAINER-001,Fictional Container Birch,Energy,West,B,"
    "0.1,0.5,1000,INR,one_year\n"
).encode()
HEADERS = {
    "Origin": "http://127.0.0.1:3000",
    "Content-Type": "text/csv",
    "X-AegisRisk-Synthetic": "true",
    "X-AegisRisk-Reviewed": "true",
    "X-AegisRisk-Preview-Digest": sha256(BODY).hexdigest(),
}


def wait_ready(client):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            if client.get("/ready").status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    raise RuntimeError("Container stack did not become ready within 90 seconds")


def get_json(client, resource, **kwargs):
    response = client.get(resource, **kwargs)
    response.raise_for_status()
    return response.json()


def save(client):
    return client.post(
        "/saved-portfolios", params={"name": "Fictional container recovery"},
        headers=HEADERS, content=BODY,
    )


def stable(value):
    # Generated timestamps may change; every other evidence field must match.
    if isinstance(value, dict):
        return {key: stable(item) for key, item in value.items()
                if key != "generated_at"}
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def evidence(client, dataset_id):
    query = {"dataset_id": dataset_id}
    demo = get_json(client, "/report")
    report = get_json(client, "/report", params=query)
    scenario = client.post(
        "/scenario-report", params=query,
        json={"pd_multiplier": 2, "lgd_multiplier": 1, "ead_multiplier": 1},
    )
    scenario.raise_for_status()
    scenario_data = scenario.json()
    assert scenario_data["dataset_id"] == dataset_id
    assert scenario_data["scenario"]["stressed_el"] == 100
    calculation = scenario_data["scenario"]["calculation"]
    assert Decimal(calculation["stressed_el_decimal"]) == 100
    assert demo["summary"]["facility_count"] == 40
    assert report["dataset_id"] == dataset_id
    assert report["summary"]["facility_count"] == 1
    assert report["summary"]["total_expected_loss"] == 50
    assert Decimal(report["calculation"]["total_expected_loss_decimal"]) == 50
    catalog = get_json(client, "/saved-portfolios")
    assert catalog["enabled"] is True
    assert any(item["id"] == dataset_id for item in catalog["items"])
    return stable({
        "demo": demo, "saved": report, "scenario": scenario_data,
        "catalog": catalog,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["defaults", "capture", "verify"])
    mode = parser.parse_args().mode
    if os.environ.get("AEGISRISK_CONTAINER_TEST") != "fictional-only":
        raise RuntimeError("Use only the isolated fictional container-test setup")
    with httpx.Client(base_url=BASE_URL + "/", timeout=10) as client:
        wait_ready(client)
        if mode == "defaults":
            catalog = get_json(client, "/saved-portfolios")
            assert catalog["enabled"] is False
            assert catalog["items"] == []
            blocked = save(client)
            assert blocked.status_code in (403, 503), blocked.text
            preview = client.post(
                "/import-preview", headers=HEADERS, content=BODY,
            )
            preview.raise_for_status()
            assert preview.json()["persisted"] is False
            assert preview.json()["summary"]["total_expected_loss"] == 50
            assert get_json(client, "/portfolio")["summary"]["facility_count"] == 40
            print("Default containers: saving blocked; preview and demo healthy")
        elif mode == "capture":
            created = save(client)
            assert created.status_code == 201, created.text
            dataset_id = created.json()["portfolio"]["id"]
            state = {"dataset_id": dataset_id, "evidence": evidence(client, dataset_id)}
            STATE.parent.mkdir(exist_ok=True)
            STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
            print("Captured fictional portfolio, reports and catalog before restart")
        else:
            state = json.loads(STATE.read_text(encoding="utf-8"))
            assert evidence(client, state["dataset_id"]) == state["evidence"]
            retry = save(client)
            assert retry.status_code == 200, retry.text
            assert retry.json()["portfolio"]["id"] == state["dataset_id"]
            assert evidence(client, state["dataset_id"]) == state["evidence"]
            print("Restart/reseed recovery: all evidence unchanged; retry deduplicated")


if __name__ == "__main__":
    main()
