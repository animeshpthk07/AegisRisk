"""Isolated synthetic research model; never supplies portfolio PDs or credit decisions."""

import json
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import version
from threading import Lock

import numpy as np
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError, field_validator
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/api/v1")
FEATURES = ("debt_to_assets", "interest_coverage", "current_ratio", "revenue_growth")
BOUNDS = ((0, 1.5), (0, 10), (0, 4), (-0.5, 0.5))
MODEL_ID = "synthetic-logistic-v1"
SEED = 20261021
WARNING = (
    "Fictional generator only: not validated on real borrowers, not a bank PD model, "
    "not a credit recommendation. Portfolio PDs and reports are unchanged."
)


class ModelInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    synthetic: StrictBool
    debt_to_assets: float = Field(ge=0, le=1.5)
    interest_coverage: float = Field(ge=0, le=10)
    current_ratio: float = Field(ge=0, le=4)
    revenue_growth: float = Field(ge=-0.5, le=0.5)

    @field_validator("synthetic")
    @classmethod
    def fictional_only(cls, value):
        if value is not True:
            raise ValueError("Confirm fictional inputs only")
        return value


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def generate_data():
    rng = np.random.default_rng(SEED)
    x = np.round(rng.uniform([b[0] for b in BOUNDS], [b[1] for b in BOUNDS], (3000, 4)), 8)
    debt, coverage, current, growth = x.T
    score = -2 + 3.5 * debt - 0.25 * coverage - 0.9 * current - 2 * growth
    score += 1.5 * debt * (1 - current / 4)
    probability = 1 / (1 + np.exp(-score))
    y = rng.binomial(1, probability)
    return x, y


def split_indices(y):
    train, remaining = train_test_split(
        np.arange(len(y)), test_size=0.4, stratify=y, random_state=SEED + 1
    )
    calibration, test = train_test_split(
        remaining, test_size=0.5, stratify=y[remaining], random_state=SEED + 2
    )
    return {"train": train, "calibration": calibration, "test": test}


def metrics(y, probabilities):
    return {
        "roc_auc": float(roc_auc_score(y, probabilities)),
        "average_precision": float(average_precision_score(y, probabilities)),
        "brier_score": float(brier_score_loss(y, probabilities)),
        "log_loss": float(log_loss(y, probabilities, labels=[0, 1])),
    }


def reliability_bins(y, probabilities):
    indices = np.minimum((probabilities * 10).astype(int), 9)
    return [
        {"lower": i / 10, "upper": (i + 1) / 10, "count": int((indices == i).sum()),
         "mean_prediction": float(probabilities[indices == i].mean())
         if (indices == i).any() else None,
         "observed_rate": float(y[indices == i].mean()) if (indices == i).any() else None}
        for i in range(10)
    ]


@dataclass
class ModelBundle:
    base: object
    calibrated: object
    card: dict


def train_model():
    x, y = generate_data()
    splits = split_indices(y)
    train, calibration, test = (splits[name] for name in ("train", "calibration", "test"))
    base = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000, tol=1e-8))
    base.fit(x[train], y[train])
    calibrated = CalibratedClassifierCV(FrozenEstimator(base), method="sigmoid")
    calibrated.fit(x[calibration], y[calibration])
    probabilities = {
        "training_prior": np.full(len(test), y[train].mean()),
        "raw_logistic": base.predict_proba(x[test])[:, 1],
        "calibrated_logistic": calibrated.predict_proba(x[test])[:, 1],
    }
    card = {
        "schema_version": "aegisrisk.model-card.v1", "model_id": MODEL_ID,
        "synthetic": True, "portfolio_integration": False, "warning": WARNING,
        "generator": {"version": "fictional-ratios-v1", "seed": SEED, "rows": len(y),
                      "label": "Bernoulli event from a disclosed artificial logistic function",
                      "logit": "-2+3.5*d-0.25*i-0.9*c-2*g+1.5*d*(1-c/4)",
                      "sampling": "Independent uniform ratios, rounded to 8 decimal places"},
        "features": [{"name": name, "min": low, "max": high}
                     for name, (low, high) in zip(FEATURES, BOUNDS, strict=True)],
        "dataset_sha256": fingerprint({"x": x.tolist(), "y": y.tolist()}),
        "splits": {
            name: {"rows": len(ids), "events": int(y[ids].sum()),
                   "event_rate": float(y[ids].mean()), "ids_sha256": fingerprint(ids.tolist())}
            for name, ids in splits.items()
        },
        "split_seeds": [SEED + 1, SEED + 2],
        "training": "Train-only StandardScaler + L2 logistic regression, C=1, max_iter=1000",
        "calibration": "Frozen trained pipeline; sigmoid fitted on calibration rows only",
        "evaluation": "Untouched 600-row synthetic test split; no model selection on test",
        "metrics": {name: metrics(y[test], p) for name, p in probabilities.items()},
        "calibration_bins": reliability_bins(y[test], probabilities["calibrated_logistic"]),
        "versions": {name: version(name) for name in ("scikit-learn", "numpy", "scipy")},
        "limitations": [
            "Self-generated labels only demonstrate the pipeline, not real-world accuracy.",
            "No temporal, external, fairness, stability or independent banking validation.",
            "Calibration is measured, not assumed to improve the raw model.",
            "Contributions explain raw log-odds, not calibrated probability or causality.",
            "No personal data, protected attributes, uploaded records or external AI used.",
        ],
    }
    return ModelBundle(base, calibrated, card)


_bundle = None
_lock = Lock()


def get_model():
    global _bundle
    with _lock:
        if _bundle is None:
            _bundle = train_model()
        return _bundle


def predict(inputs):
    bundle = get_model()
    values = {name: getattr(inputs, name) for name in FEATURES}
    row = np.array([[values[name] for name in FEATURES]])
    scaler = bundle.base.named_steps["standardscaler"]
    classifier = bundle.base.named_steps["logisticregression"]
    contributions = scaler.transform(row)[0] * classifier.coef_[0]
    return {
        "model_id": MODEL_ID, "synthetic": True, "portfolio_integration": False,
        "inputs": values, "raw_probability": float(bundle.base.predict_proba(row)[0, 1]),
        "calibrated_probability": float(bundle.calibrated.predict_proba(row)[0, 1]),
        "raw_log_odds": float(bundle.base.decision_function(row)[0]),
        "intercept": float(classifier.intercept_[0]),
        "contributions": [{"feature": name, "log_odds": float(value)}
                          for name, value in zip(FEATURES, contributions, strict=True)],
        "warning": WARNING,
    }


def no_query(request):
    if request.query_params:
        raise HTTPException(422, "Model Lab does not accept dataset IDs or query parameters")


@router.get("/model-card")
def model_card(request: Request):
    no_query(request)
    return deepcopy(get_model().card)


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


@router.post("/model-predict")
async def model_predict(request: Request):
    no_query(request)
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        raise HTTPException(415, "Send application/json")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 4096:
            raise HTTPException(413, "Model input exceeds 4096 bytes")
        body.extend(chunk)
    try:
        data = json.loads(body, object_pairs_hook=strict_object)
        inputs = ModelInput.model_validate(data)
    except (ValueError, ValidationError, RecursionError):
        raise HTTPException(422, "Confirm fictional inputs and use finite numeric ratios in range")
    return await run_in_threadpool(predict, inputs)
