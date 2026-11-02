# AegisRisk project presentation

Prepared 2 November 2026. Career copy below is a draft for the owner's review. It has not been posted to LinkedIn. Use the repository and exact verification links; do not imply a hosted app or a completed production system.

## Thirty-second introduction

I built AegisRisk to make credit-risk calculations easier to inspect. It takes fictional CSV or Excel facility data through validation, expected-loss calculations, sensitivity scenarios and downloadable evidence. I used Python/FastAPI, Next.js/TypeScript and PostgreSQL, with automated browser and container checks. A separate synthetic Model Lab demonstrates a training and evaluation pipeline. My focus is the connection between financial assumptions, reliable software and an explanation a reviewer can check.

## Five-minute demonstration

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:40 | Built-in fictional portfolio | Supplied PD/LGD assumptions, INR and a one-year horizon; no claim of real-world credit accuracy |
| 0:40–1:30 | CSV/Excel validation, then an invalid PD | Preview cannot silently change the active dataset; errors must be actionable |
| 1:30–2:20 | One-row fixture: PD 0.1, LGD 0.5, EAD 1,000 | EL is INR 50; doubling PD produces INR 100 in this bounded sensitivity example |
| 2:20–3:10 | Scenario JSON and PDF | Reconcile dataset identity, assumptions and decimal evidence; explain stale-result guards |
| 3:10–4:00 | Synthetic Model Lab | Separate training, calibration and test splits; fictional performance is not bank validation |
| 4:00–5:00 | Actions results, architecture and limitations | Show what passed, what is still open, and how another developer can reproduce it |

Use [DEMO_GUIDE.md](DEMO_GUIDE.md) for exact steps and [DEVELOPMENT.md](DEVELOPMENT.md) for setup. The one-row scenario requires that fixture to be explicitly selected; never attribute those totals to the 40-record seed. Optional workspace controls require a separate disposable token-mode configuration. Do not show credentials or real customer data.

## Evidence a reviewer can inspect

- [Repository](https://github.com/animeshpthk07/AegisRisk), [architecture](ARCHITECTURE.md) and [API/import/report contract](CONTRACT.md).
- Merged source `c30f0266ce4dc719d6cad3c0e391ac25b5f2c7d3` passed [application verification](https://github.com/animeshpthk07/AegisRisk/actions/runs/41443684705) and [demo-image verification](https://github.com/animeshpthk07/AegisRisk/actions/runs/41443684766). Consult [release readiness](RELEASE_READINESS.md) for later verified changes; source presence alone is not proof of a pass.
- [Model design and evaluation limits](MODEL_LAB.md), [workspace access](AUTHENTICATION.md) and [security limits](SECURITY.md).
- The [published educational pre-release](https://github.com/animeshpthk07/AegisRisk/releases/tag/v0.1.0-preview.1) pins an earlier source. It does not automatically include later main-branch features. CI artifacts expire after seven days; source and reproduction instructions remain available.

## CV project entry — owner-review draft

**AegisRisk — Open-source educational credit-risk workbench**  
Python, FastAPI, SQLAlchemy, PostgreSQL, TypeScript, Next.js, Playwright

- Built a fictional-data workflow connecting bounded CSV/XLSX validation, reviewed immutable snapshots, Decimal expected-loss calculations and baseline/scenario evidence exports in JSON, HTML and PDF.
- Implemented optional token roles and workspace-scoped data access, request/response guards and a per-response browser script policy; checked application flows across Chromium, Firefox and WebKit and exercised PostgreSQL restart persistence in CI.
- Developed an isolated synthetic logistic-regression lab with separate training, calibration and test splits, baseline comparisons and disclosed limitations; kept model estimates separate from portfolio assumptions.

Use these bullets only if you can explain and demonstrate the implementation. They do not assert employment, client delivery, financial savings, real-world predictive accuracy or independent validation. The project demonstrates credit-risk and software skills; it is not evidence of investment-banking deal execution or professional FP&A experience.

## LinkedIn project description — owner-review draft

AegisRisk is my open-source educational credit-risk workbench, built with Python/FastAPI, Next.js/TypeScript and PostgreSQL. It connects fictional CSV/Excel inputs to inspectable expected-loss calculations, bounded scenarios and JSON/HTML/PDF evidence. The repository includes automated browser/container checks, optional workspace access controls and a separate synthetic Model Lab. It is a research project using fictional data; production operations, real-world model validation and hosting remain unfinished.

Project URL: https://github.com/animeshpthk07/AegisRisk

## LinkedIn post — owner-review draft; do not publish automatically

A risk dashboard is only useful if someone can check where its numbers came from.

That's the problem I've been exploring with AegisRisk, my open-source credit-risk workbench.

Start with fictional CSV or Excel facilities. Validate the inputs. Calculate expected loss. Change the assumptions. Download evidence that shows the dataset, calculation and limits behind the result.

One example: PD 10% × LGD 50% × INR 1,000 exposure = INR 50 expected loss. Double the PD assumption and the scenario becomes INR 100. Simple arithmetic; keeping the right inputs, results and reports together is the harder software problem.

I built it with Python/FastAPI, Next.js/TypeScript and PostgreSQL. The repository includes browser tests, workspace access controls and a separate synthetic model experiment. It is educational, uses fictional data and is not a production banking system.

If you work in credit risk, financial analytics or fintech, what evidence would you want to inspect before trusting a scenario report? I'd value specific feedback on the workflow.

I'm also interested in internship opportunities where finance and software meet. Happy to connect with people building in this area.

https://github.com/animeshpthk07/AegisRisk

#CreditRisk #FinancialAnalytics #FinTech

## Questions to prepare for

1. Why use Decimal for evidence calculations while chart values may be floating point?
2. What changes when the active dataset or scenario assumptions change during an in-flight request?
3. How do workspace scope, roles and browser cleanup differ from enterprise identity and server-side revocation?
4. Why do disjoint synthetic splits still fail to establish real-world model validity?
5. Which risks remain before shared persistence: quotas, retention, backup/restore, deletion, monitoring and independent review?

Answer using the code, contract and known limits. Do not invent results, promise hiring outcomes or guarantee reach. The owner must review the exact final public copy before publication.
