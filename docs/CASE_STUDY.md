# AegisRisk case study

## The analyst's question

If one industry comes under stress, which facilities explain the change in expected loss? A portfolio total alone cannot answer that question. A reviewer needs the original assumptions, each facility's contribution and a way to reconcile the amounts. AegisRisk demonstrates that workflow on fictional INR credit facilities over a one-year horizon.

## Follow a loss from portfolio to facility

Consider this worked example from the automated scenario checks. The amounts are deliberately small so a reader can repeat the calculation by hand.

| Industry | Baseline expected loss | After an Energy shock | Change |
| --- | ---: | ---: | ---: |
| Energy | ₹50 | ₹165 | +₹115 |
| Services | ₹20 | ₹20 | ₹0 |
| Portfolio | ₹70 | ₹185 | +₹115 |

The scenario multiplies Energy PD by 2.5, LGD by 1.2 and EAD by 1.1. In this example the probability and severity stay within their bounds, so ₹50 × 2.5 × 1.2 × 1.1 = ₹165. Services keeps its original assumptions. The portfolio rises by about 164.3%. This example illustrates arithmetic under a chosen shock. It provides no estimate of the probability of a recession.

In the workbench, the industry table explains where the change originated. The facility ranking identifies which exposures drove it. Exposure share and expected-loss share answer different questions. A smaller sector can contribute a large share of expected loss when its PD or LGD is high. [Portfolio analytics](PORTFOLIO_ANALYTICS.md)

## Read a borrower review

Choose a facility in the explorer. Compare the facility, all facilities belonging to that borrower, and the active portfolio. Search, geography and rating narrow the picker. The two benchmarks still describe their entire groups in the selected snapshot.

A second test fixture groups two facilities under one fictional borrower. The first has EAD ₹100, PD 80% and LGD 50%, giving expected loss of ₹40. The second has EAD ₹200, PD 10% and LGD 50%, giving ₹10. Borrower expected loss is ₹50. Exposure-weighted PD is (100 × 0.8 + 200 × 0.1) / 300 = 33.33%. Doubling only the first facility's PD caps it at 100%, taking its expected loss to ₹50. This sensitivity holds LGD and EAD fixed. [Borrower review and API fixtures](../apps/api/tests/test_api.py)

## What the model contributes

The model lab generates 3,000 fictional financial profiles. It fits a scaled logistic regression on 1,800, calibrates on a separate 600 and evaluates on the final 600. The model card compares a training-event-rate baseline with raw and calibrated estimates. ROC-AUC measures ranking, average precision summarizes precision across recall levels, and Brier score measures probability error. A seven-threshold table makes missed simulated events and false alarms visible. The exact scores and split fingerprints come from the running model card. [Model methodology](MODEL_LAB.md)

Each of the 40 built-in facilities has four reproducible example ratios derived from its versioned fictional identifier. The model displays an illustrative probability beside the portfolio's supplied PD. Its feature contributions explain the raw logistic score. Expected loss uses the supplied PD throughout. An imported row can share a demo name and identifier and still has no linked ratios or model score. This preserves the origin of every input. [Facility review calculation](../apps/api/aegisrisk/facility_review.py)

## How to inspect the evidence

1. Open the dashboard using the [demo guide](DEMO_GUIDE.md). Check the active dataset, currency and horizon.
2. Review concentration and open a facility. Explain why a borrower's exposure-weighted PD differs from an unweighted average.
3. Run the sector shock, reconcile the industry changes with the total and inspect the largest facility changes. Download the scenario JSON to inspect the underlying calculation.
4. In Model Lab, change the display threshold and observe the confusion matrix. The portfolio expected loss continues to use its original assumptions.

The Next.js interface requests results through a same-origin proxy. FastAPI validates the request, reads the selected dataset and computes the results. PostgreSQL stores saved snapshots. Numerical tests use small independently calculable examples, and browser tests exercise the same controls a reviewer uses. [Architecture](ARCHITECTURE.md) · [Verification record](RELEASE_READINESS.md)

## Lessons and limits

A result is easier to defend when a reviewer can reproduce one row and add the segments back to the total. Score provenance matters as much as a score's precision. Portfolio PD, model PD and stressed PD each answer a different question, so the interface labels them separately. The examples use synthetic data and fixed assumptions. A real deployment for credit decisions would need representative outcomes, temporal and independent model validation, governance and operational review.
