# AegisRisk reviewer walkthrough

A reproducible tour of the verified educational slice, not a production launch. Use only fictional data on a local, single-user instance. The public repository is source code; no public hosted application is currently verified.

## Before the demo

Follow [DEVELOPMENT.md](DEVELOPMENT.md) to start the application and apply migrations/seed. Confirm the API is ready before opening the dashboard. Never present an old screenshot as evidence that the current app is running.

Saving is intentionally disabled by default. The preview, demo portfolio and reports can be shown without enabling it. Demonstrate saving only on a local, isolated instance configured as described in the development guide; it has no authentication or tenant isolation. Never enable it on a shared/public deployment merely to complete this walkthrough.

## 1. Explain the problem and boundary

“I built an educational workbench that makes credit-risk calculations inspectable. It connects validated fictional facility inputs to portfolio summaries, bounded sensitivity scenarios and downloadable evidence. Portfolio calculations use supplied PD/LGD assumptions and deterministic explanations. A separate synthetic Model Lab demonstrates training and evaluation; it does not replace those assumptions or use an external LLM.”

The implemented calculation is expected loss: **EL = PD × LGD × EAD**. PD and LGD are fractions; EAD is an INR amount over the supported one-year horizon. This is not a lending decision, a prediction of realized loss, a regulatory capital measure or a claim of bank-grade validation.

## 2. Show the built-in portfolio

Select the built-in demo. The fictional seed has 40 facilities, INR 115,000,000 EAD and INR 2,769,125 expected loss. Search for `SYN-001` to inspect one record. Explain that concentration and weighted portfolio measures summarize the selected inputs; they do not establish the quality of those assumptions.

Show the industry breakdown and the deterministic explanation. Identify which displayed totals support the explanation. Do not call the narrative an AI model output.

## 3. Validate an independent preview

Open **CSV / Excel preview**, choose **Use fictional example**, acknowledge synthetic-only data, and select **Validate and preview**. Expect two records, INR 3,000 EAD and INR 66 expected loss. The active portfolio must remain unchanged: preview is not persistence or dataset selection.

For an arithmetic example that can be checked by hand, save the following fictional text as a UTF-8 CSV and preview it instead:

```csv
id,borrower,industry,geography,rating,pd,lgd,ead,currency,horizon
SYN-CONTAINER-001,Fictional Container Birch,Energy,West,B,0.1,0.5,1000,INR,one_year
```

Expected result: one facility, INR 1,000 EAD and INR 50 expected loss, because `0.1 × 0.5 × 1000 = 50`. This is the same fictional input used in the container-lifecycle verification.

For XLSX, use a clean values-only workbook with one visible sheet and the same ten-column header. Formulas, dates, hidden content, macros and links are unsupported. See the precise [import contract](CONTRACT.md#values-only-xlsx-safety-and-storage); do not upload real customer information.

## 4. Demonstrate reviewed persistence, if locally enabled

Inspect the one-row preview, enter a descriptive name, confirm the totals were reviewed, and choose **Save reviewed portfolio**. Saving does not automatically switch the active dataset. Choose **Open saved portfolio** and verify the selected dataset now has one facility and INR 50 expected loss.

Repeat the identical save: it must reuse the existing snapshot rather than create another copy. CSV identity is based on original bytes; XLSX storage identity is based on normalized CSV values. Changing an uploaded file requires a new validated preview. Reloading returns selection to the built-in demo, but the saved snapshot should still be in the catalog.

If saving is disabled, explain the intended boundary and skip this step. Do not imply that a preview was saved.

## 5. Stress, inspect and export

For the selected one-row saved portfolio, use PD ×2, LGD ×1, EAD ×1 and all industries, then choose **Calculate scenario →**.

| Quantity | Expected value |
| --- | --- |
| Baseline EL | INR 50 |
| Stressed PD | 0.2 |
| Stressed EL | INR 100 |
| EL difference | INR 50 |
| Relative EL increase | 100% |

These are sensitivity assumptions, not an economic forecast. Download both baseline and scenario JSON reports. Confirm the dataset identity, supplied assumptions and decimal evidence agree with the calculation. The baseline report excludes the scenario; the scenario report includes its baseline comparison. A source fingerprint identifies canonical input content, not an authenticated signature.

Download a printable HTML report, open it offline and inspect its methodology, evidence table and limitations. It has no scripts or external assets. Browser Print remains available for that HTML document.

Then choose **Download baseline report (PDF)** and **Download scenario report (PDF)** to demonstrate the separate server-generated exports. Compare the selected dataset and decimal evidence with JSON. In the scenario PDF, identify baseline EL, stressed EL, INR difference, fractional relative change and affected-facility count; read the separate baseline and scenario limitations. Inspect all pages, repeated table headings and numbered footers. The browser validates identity, byte length and SHA-256 before releasing the download. These PDFs are not digitally signed or tagged accessible; non-ASCII labels use explicit Unicode escapes, and JSON retains the original text.

Changing a scenario control or portfolio clears the old result; recalculate before exporting again. If saving is disabled, demonstrate exports on the built-in portfolio and reconcile with its JSON evidence; the one-row values in the table apply only to that explicitly saved fixture.

## 6. Show a failure, not just the happy path

- Change the CSV PD from `0.1` to `1.5`. Preview must reject the out-of-range value, identify an issue and show no partial totals. The active portfolio should not change. Restore `0.1` and validate again.
- Calculate a scenario, then change an assumption before downloading. The previous result must clear and must not be offered as a current comparison.
- If a request genuinely fails, show the visible error and retry. Do not claim a failure was tested merely because a button exists; intentional outage and stale-response cases are exercised by the browser test suite.

## 7. Show independent verification

[Run #34](https://github.com/animeshpthk07/AegisRisk/actions/runs/40078175863) passed backend, frontend, full-stack Chromium and PostgreSQL container-lifecycle jobs for commit `cb756b6` on 24 October 2026. It recorded 141 backend tests, 19 frontend tests and 77 browser cases passing in each environment. The container job also checked default saving was blocked and verified unchanged evidence after database/application restart and repeat migration/seed. The same browser suite runs in two environments; do not describe that as twice as many distinct cases. All 13 rendered baseline, scenario and literal-label PDF fixture pages were visually reviewed in the browser.

Open the actual Actions run and relevant logs rather than relying on a badge alone. Synthetic screenshots, traces and reports have seven-day retention and may have expired. The source and test definitions remain available for reproduction. Restart persistence is not a backup or disaster-recovery test, and a dependency audit is not a penetration test.

## 8. Inspect the synthetic Model Lab

Open **Synthetic Model Lab** and **Load model evidence**. Inspect the 1,800/600/600 row splits, baseline/raw/calibrated metrics and calibration bins. Explain why an artificial generator is not an external banking benchmark. Confirm the example ratios are fictional, then **Estimate fictional event**. The intercept and feature contributions reconstruct raw log-odds, not the calibrated probability. Change any ratio or withdraw consent: the old estimate must clear, while the active portfolio remains unchanged.

## Technical discussion map

- **Why Decimal?** To make EL arithmetic and report evidence inspectable without binary floating-point drift. Presentation can round; supplied exact decimal evidence remains available.
- **Why a fixed proxy?** The browser calls the same-origin Next.js routes, which forward to the configured API rather than an arbitrary caller-supplied destination.
- **Why immutable snapshots?** Reports can refer to a stable reviewed input set. Preview and save are separate, and every save revalidates the supplied data and review fingerprint.
- **Why stale-response guards?** A late calculation or export must not be presented as belonging to a different dataset or newer assumptions, including an A → B → A switch.
- **What does the model learn?** The isolated Model Lab learns an explicitly artificial relationship between four fictional ratios and simulated labels. It uses separate train/calibration/test data and compares held-out metrics with a constant training-prior baseline. This is pipeline evidence, not real-world credit accuracy. See [MODEL_LAB.md](MODEL_LAB.md) and the latest verified run in the tracker.
- **What remains before a real deployment?** Authentication, tenant isolation, retention/storage controls, broader security/accessibility verification and an approved hosting design. Real financial documents are not supported by the synthetic-only boundary.

## Honest completion statement

“The verified slice includes synthetic CSV/XLSX validation, reviewed local snapshots, deterministic risk calculations, guarded sensitivity analysis, evidence exports and automated full-stack/container checks. An isolated synthetic training/evaluation demonstration is implemented separately; its current verification status is in the tracker. Baseline and scenario reports are available as JSON, printable HTML and server-generated PDF, with fixture-based visual review. Real-world model validation, production security and hosted release remain incomplete.”

Use [MILESTONES.md](MILESTONES.md) as the detailed record. Do not claim regulatory approval, affiliation with a bank, real-world model accuracy, production readiness or a deployed product.
