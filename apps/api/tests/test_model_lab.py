import math

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sklearn.metrics import brier_score_loss, roc_auc_score

import aegisrisk.model_lab as lab
from aegisrisk.main import app

INPUT = {"synthetic": True, "debt_to_assets": 0.6, "interest_coverage": 3.0,
         "current_ratio": 1.5, "revenue_growth": 0.05}


@pytest.fixture(scope="module")
def model():
    return lab.get_model()


def test_splits_are_disjoint_complete_and_stratified(model):
    x, y = lab.generate_data()
    splits = lab.split_indices(y)
    assert x.shape == (3000, 4)
    assert [len(ids) for ids in splits.values()] == [1800, 600, 600]
    assert len(set(np.concatenate(list(splits.values())))) == 3000
    for name, ids in splits.items():
        assert 0 < y[ids].sum() < len(ids)
        assert abs(y[ids].mean() - y.mean()) < 0.005
        assert model.card["splits"][name]["ids_sha256"] == lab.fingerprint(ids.tolist())
    scaler = model.base.named_steps["standardscaler"]
    assert scaler.n_samples_seen_ == 1800
    np.testing.assert_allclose(scaler.mean_, x[splits["train"]].mean(axis=0))


def test_evaluation_recomputes_against_train_prior(model):
    x, y = lab.generate_data()
    splits = lab.split_indices(y)
    target = y[splits["test"]]
    probabilities = model.calibrated.predict_proba(x[splits["test"]])[:, 1]
    actual = model.card["metrics"]["calibrated_logistic"]
    assert actual["roc_auc"] == pytest.approx(roc_auc_score(target, probabilities))
    assert actual["brier_score"] == pytest.approx(brier_score_loss(target, probabilities))
    baseline = np.full(len(target), y[splits["train"]].mean())
    prior = model.card["metrics"]["training_prior"]
    assert prior["roc_auc"] == 0.5
    assert prior["brier_score"] == pytest.approx(brier_score_loss(target, baseline))
    assert sum(item["count"] for item in model.card["calibration_bins"]) == 600
    # A minimum synthetic learning signal; no claim that calibration beats raw.
    assert actual["roc_auc"] > 0.65
    assert actual["brier_score"] < prior["brier_score"]


def test_training_is_reproducible_and_test_labels_cannot_change_model(model, monkeypatch):
    repeated = lab.train_model()
    assert repeated.card == model.card
    x, y = lab.generate_data()
    splits = lab.split_indices(y)
    changed = y.copy()
    changed[splits["test"]] = 1 - changed[splits["test"]]
    monkeypatch.setattr(lab, "generate_data", lambda: (x, changed))
    monkeypatch.setattr(lab, "split_indices", lambda _: splits)
    perturbed = lab.train_model()
    np.testing.assert_array_equal(
        model.calibrated.predict_proba(x), perturbed.calibrated.predict_proba(x)
    )
    assert perturbed.card["metrics"] != model.card["metrics"]


def test_calibration_only_receives_calibration_rows(monkeypatch):
    x, y = lab.generate_data()
    ids = lab.split_indices(y)["calibration"]
    original = lab.CalibratedClassifierCV.fit
    observed = []

    def record(self, features, labels, *args, **kwargs):
        observed.append(len(labels))
        np.testing.assert_array_equal(features, x[ids])
        np.testing.assert_array_equal(labels, y[ids])
        return original(self, features, labels, *args, **kwargs)

    monkeypatch.setattr(lab.CalibratedClassifierCV, "fit", record)
    lab.train_model()
    assert observed == [600]


def test_prediction_contributions_reconstruct_raw_score(model):
    result = lab.predict(lab.ModelInput.model_validate(INPUT))
    score = result["intercept"] + sum(item["log_odds"] for item in result["contributions"])
    assert score == pytest.approx(result["raw_log_odds"])
    assert 1 / (1 + math.exp(-score)) == pytest.approx(result["raw_probability"])
    assert 0 < result["calibrated_probability"] < 1
    assert result["portfolio_integration"] is False
    assert result["inputs"] == {key: INPUT[key] for key in lab.FEATURES}


@pytest.mark.parametrize("changes", [
    {"synthetic": False}, {"synthetic": "true"}, {"synthetic": 1},
    {"debt_to_assets": -0.01}, {"debt_to_assets": 1.51},
    {"interest_coverage": 11}, {"current_ratio": 4.1}, {"revenue_growth": -0.51},
    {"debt_to_assets": "NaN"}, {"debt_to_assets": "0.6"},
    {"debt_to_assets": True}, {"borrower": "Do not accept personal data"},
])
def test_api_rejects_invalid_inputs(changes):
    with TestClient(app) as client:
        response = client.post("/api/v1/model-predict", json=INPUT | changes)
        assert response.status_code == 422
        assert "finite numeric ratios" in response.json()["detail"]


def test_api_boundaries_and_read_only_model_card(model):
    with TestClient(app) as client:
        card = client.get("/api/v1/model-card")
        assert card.status_code == 200
        assert card.headers["cache-control"] == "no-store"
        assert card.json()["synthetic"] is True
        assert client.post("/api/v1/model-predict", json=INPUT).status_code == 200
        assert client.get("/api/v1/model-card?dataset_id=anything").status_code == 422
        assert client.post("/api/v1/model-predict?x=1", json=INPUT).status_code == 422
        assert client.post("/api/v1/model-predict", content="{}").status_code == 415
        headers = {"Content-Type": "application/json"}
        for content in ('{}', '[]', '{', '{"synthetic":true,"synthetic":true}',
                        '{"debt_to_assets":NaN}', b"\xff"):
            result = client.post("/api/v1/model-predict", content=content, headers=headers)
            assert result.status_code == 422
        oversized = client.post("/api/v1/model-predict", content=" " * 4097, headers=headers)
        assert oversized.status_code == 413
        assert client.get("/api/v1/model-card").json() == card.json()
    assert lab.get_model() is model
