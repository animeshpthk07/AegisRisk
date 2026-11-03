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
        for content in ('[' * 1500 + ']' * 1500, '{}', '[]', '{', '{"synthetic":true,"synthetic":true}',
                        '{"debt_to_assets":NaN}', b"\xff"):
            result = client.post("/api/v1/model-predict", content=content, headers=headers)
            assert result.status_code == 422
        oversized = client.post("/api/v1/model-predict", content=" " * 4097, headers=headers)
        assert oversized.status_code == 413
        assert client.get("/api/v1/model-card").json() == card.json()
    assert lab.get_model() is model


def test_threshold_counts_match_independent_confusion_matrix(model):
    from sklearn.metrics import confusion_matrix

    x, y = lab.generate_data()
    test = lab.split_indices(y)["test"]
    probabilities = model.calibrated.predict_proba(x[test])[:, 1]
    analysis = model.card["threshold_analysis"]
    assert analysis["rule"] == "probability >= threshold"
    assert analysis["model"] == "calibrated_logistic"
    assert analysis["positive_label"] == 1
    assert analysis["default_threshold"] == 0.5
    rows = analysis["rows"]
    assert [r["threshold"] for r in rows] == [0, 0.1, 0.2, 0.3, 0.5, 0.7, 1]
    for row in rows:
        predicted = probabilities >= row["threshold"]
        tn, fp, fn, tp = confusion_matrix(y[test], predicted, labels=[0, 1]).ravel()
        assert [row[k] for k in (
            "true_negative", "false_positive", "false_negative", "true_positive"
        )] == [tn, fp, fn, tp]
        assert tn + fp + fn + tp == 600
        assert row["flagged"] == int(predicted.sum())
        assert row["flagged_rate"] == pytest.approx(predicted.mean())
        assert row["recall"] == pytest.approx(tp / (tp + fn))
        assert row["false_positive_rate"] == pytest.approx(fp / (fp + tn))
        if tp + fp:
            assert row["precision"] == pytest.approx(tp / (tp + fp))
        else:
            assert row["precision"] is None
    assert [r["flagged"] for r in rows] == sorted(
        [r["flagged"] for r in rows], reverse=True
    )


def test_threshold_boundary_ties_and_hand_calculated_errors():
    rows = lab.threshold_sensitivity([0, 1, 1, 0], [0.1, 0.2, 0.5, 0.8])
    middle = next(r for r in rows if r["threshold"] == 0.5)
    assert middle == {
        "threshold": 0.5, "true_positive": 1, "false_positive": 1,
        "false_negative": 1, "true_negative": 1, "flagged": 2,
        "flagged_rate": 0.5, "precision": 0.5, "recall": 0.5,
        "false_positive_rate": 0.5,
    }
    assert rows[0]["flagged"] == 4
    assert rows[-1]["flagged"] == 0
    assert rows[-1]["precision"] is None
    # A prediction exactly equal to either endpoint is classified positive.
    endpoints = lab.threshold_sensitivity([0, 1], [0.0, 1.0])
    assert endpoints[0]["flagged"] == 2
    assert endpoints[-1]["true_positive"] == 1


def test_threshold_undefined_rates_are_null_and_json_safe():
    no_events = lab.threshold_sensitivity([0, 0], [0.1, 0.9])
    only_events = lab.threshold_sensitivity([1, 1], [0.1, 0.9])
    assert all(r["recall"] is None for r in no_events)
    assert all(r["false_positive_rate"] is None for r in only_events)
    import json

    json.dumps(no_events + only_events, allow_nan=False)


@pytest.mark.parametrize(("labels", "probabilities"), [
    ([], []), ([0], [0.1, 0.2]), ([2], [0.1]),
    ([0], [float("nan")]), ([1], [float("inf")]),
    ([0], [-0.01]), ([1], [1.01]), ([[0]], [[0.1]]),
])
def test_threshold_analysis_rejects_invalid_evaluation_arrays(labels, probabilities):
    with pytest.raises(ValueError):
        lab.threshold_sensitivity(labels, probabilities)

