# Synthetic Model Lab

## Scope and non-goals

AegisRisk now contains an isolated, trained logistic-regression research demonstration.
It does **not** replace the supplied PDs in the demo, uploaded portfolios, stress scenarios
or reports. It is not validated for lending, pricing, capital, IFRS 9 or real borrowers.
No names, protected attributes, uploaded documents, external AI or personal data are used.

## Reproduce and inspect

Start the normal API and web stack, open **Synthetic Model Lab**, and select
**Load model evidence**. The first request builds the fixed small model once per API
process; subsequent requests reuse it. A restart retrains from the same fixed recipe.
No serialized executable model is loaded and no user-controlled training job exists.

The model card is available at GET /api/v1/model-card (or /api/model-card via the web).
It includes the actual held-out scores, split counts and event rates, dataset/split
SHA-256 fingerprints, generator and split seeds, and installed numerical-library versions.
Floating-point details may differ across platforms or library versions: record the card
with a result, and do not assume byte-identical model weights on different runtimes.

To inspect from the API development environment:

    python -c "import json; from aegisrisk.model_lab import get_model; print(json.dumps(get_model().card, indent=2))"
    pytest apps/api/tests/test_model_lab.py -q

Run the pytest command from the repository root with the API package installed.

## Dataset and split discipline

- 3,000 independent fictional ratio profiles, seed 20261021; each feature is uniform
  over its bounded range and rounded to eight decimals.
- Inputs: debt/assets d in [0,1.5], interest coverage i in [0,10], current ratio c
  in [0,4], revenue growth g in [-0.5,0.5]. Ratios are unitless, not percentages.
- Simulated event label: Bernoulli(sigmoid(z)), with
  z = -2 + 3.5d - 0.25i - 0.9c - 2g + 1.5d(1-c/4).
- The generating probability is never a model feature. This artificial relationship
  deliberately supplies a learning signal; reproducing it is not external validation.
- Stratified disjoint 60/20/20 train/calibration/test partitions, split seeds
  20261022 and 20261023. There are 1,800 / 600 / 600 rows respectively.
- StandardScaler is fitted on training rows only. Logistic regression uses C=1,
  L2 regularization, max_iter=1000 and tolerance 1e-8. No test-driven model selection.
- FrozenEstimator keeps the fitted pipeline unchanged while a sigmoid calibrator
  is fitted on the separate calibration split. Test rows are used only for evaluation.

## Evaluation and explanation

The untouched synthetic test split compares a constant **training-prior baseline**,
raw logistic predictions and calibrated predictions using ROC-AUC, average precision,
Brier score and log loss. Higher AUC/AP and lower Brier/log loss are better. Ten fixed-width
calibration bins include counts and observed rates; empty bins are explicitly null.
Calibration is not guaranteed to improve the raw model. Scores are calculated at runtime,
not copied from a benchmark or represented as real-world detection accuracy.

Single-profile results return raw and calibrated probabilities, the submitted ratios,
raw log-odds, intercept, and standardized feature contributions. The contributions plus
intercept reconstruct the **raw logistic score**. They are not SHAP, causal explanations,
or contributions to the calibrated probability. No approve/reject recommendation exists.

## Confusion matrix and threshold sensitivity

The model card adds `threshold_analysis` for **calibrated logistic predictions on the
same untouched 600-row synthetic test split**. The fixed descriptive grid is
0%, 10%, 20%, 30%, 50%, 70% and 100%. It is not selected by optimizing test results.
The initial 50% display is an illustration, not a recommended operating threshold.
A simulated event (label 1) is predicted when probability **>=** the threshold;
this includes exact ties at zero and one.

The browser displays an actual-by-predicted confusion matrix and all seven rows:

- TP: events detected; FN: events missed; FP: false alarms; TN: non-events unflagged.
- Flagged count = TP + FP; flagged rate = (TP + FP) / test rows.
- Precision = TP / (TP + FP); recall = TP / (TP + FN).
- False-positive rate = FP / (FP + TN).
- Undefined rates use JSON null and display N/A, never a fabricated zero.

Changing the native, keyboard-accessible selector only changes the displayed matrix.
It never retrains the model or changes portfolio PDs, reports or lending decisions.
Lowering a threshold generally flags more profiles, reducing missed events while
increasing false alarms. Choosing a real operating policy would require separate
validation, explicit costs, governance and relevant expert review.

For a hand-checkable example, labels [0,1,1,0] and probabilities [0.1,0.2,0.5,0.8]
at 50% give TP=1, FP=1, FN=1, TN=1; precision, recall and false-positive rate are 50%.
These are illustrative numbers, not the trained model's measured results.

Tests independently compare all runtime counts with scikit-learn's confusion matrix,
check exact threshold ties, single-class/undefined cases and invalid evaluation arrays.
Browser checks compare displayed cells with actual API evidence at 1440px and 320px,
exercise keyboard selection/reset, and reject missing or inconsistent evidence.
The UI validates totals, event counts, rates, fixed thresholds and monotonic counts
before displaying the model card. See the relevant GitHub verification run for
execution status; the presence of tests alone is not a passing result.

## Boundaries and checks

POST /api/v1/model-predict accepts only four finite bounded numeric ratios and an explicit
boolean synthetic=true acknowledgment. It rejects extra fields, string numbers, duplicate
JSON keys, malformed JSON, unsupported content types, and bodies larger than 4 KiB.
Both endpoints reject query parameters, including dataset IDs. Nothing is persisted.
Consent does not make real data safe: this prototype must still receive fictional inputs only.

The browser clears/cancels predictions on every field or consent change, including A-to-B-to-A
edits. It verifies the returned model identity and echoed inputs before showing a result.
Regression checks cover disjoint splits, train-only scaling, calibration-only fit, independent
metric recomputation, reproducibility, test-label perturbation, contribution arithmetic,
input limits, desktop/mobile use, outages/retry and pending-result cancellation.

Remaining model work: independent real-world data governance and validation, temporal testing,
uncertainty intervals, monitoring, fairness assessment, and banking expert review. These are
not implied by successful synthetic tests. Public hosting is deferred by owner choice.
Optional access controls are described in [Authentication](AUTHENTICATION.md);
this module does not establish production banking readiness.
