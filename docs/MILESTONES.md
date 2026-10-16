# Execution tracker

Started 2026-10-13. Updated 2026-10-16. Public GitHub publication approved by the owner. No external AI enabled.

## Current activity — live development

The frontend-to-backend-to-database flow was verified locally. The foundation source is now published at https://github.com/animeshpthk07/AegisRisk. Current work uses VS Code for the Web and GitHub in the visible browser, as requested. The local preview is not a public deployment.

### What is saved

- Separate Git repository at `work/AegisRisk`; Finance Workbench is untouched.
- Next.js 16.4 / React 19.3 / TypeScript / Tailwind / Recharts frontend.
- FastAPI / SQLAlchemy / Alembic backend, explicit seed of 40 fictional INR facilities.
- Decimal EL calculation, EAD weights, borrower HHI, industry breakdown, search and scenario sensitivity.
- Bounded synthetic CSV preview with row-level validation and independent risk totals; no database writes.
- Deterministic narrative. No external AI provider or API credentials.
- PostgreSQL Compose and CI definitions. GitHub CI passed the PostgreSQL migration/read smoke; the full Compose stack remains unverified.

### How it works

Browser → fixed Next.js API proxy → FastAPI validation → SQLAlchemy database reads → Decimal calculations → dashboard.

CSV preview: browser → bounded Next.js proxy → in-memory FastAPI CSV validation → Decimal calculations → independent preview (no database writes).

### Historical foundation checks (before CSV preview)

- Backend: **25 tests passed**, one dependency deprecation warning (Starlette's httpx test-client integration).
- Backend lint: **passed**, after fixing import/format issues.
- Frontend type checking: **passed**.
- Frontend formatting unit tests: **3 passed**.
- Next.js production build: **passed**.
- Live frontend → API → database readiness: **passed**.
- Browser verified: 40 facilities, INR 115,000,000 EAD, INR 2,769,125 expected loss.
- Browser search: `SYN-001` returns exactly one facility.
- Browser stress: PD ×1.5, LGD ×1.1, EAD ×1 returns a 65% EL increase (display-rounded INR 4,569,056).
- Browser preview visibly confirmed at narrow pane width. Full accessibility/E2E coverage and broader security verification remain outstanding; CI dependency-audit steps passed.
- Full Docker Compose runtime: not tested locally; PostgreSQL service migration/read smoke passed in GitHub CI.
- Public hosted deployment: not verified. GitHub Actions: backend and frontend jobs passed for commit `423ea5b`.

### Independent GitHub verification — 2026-10-14

[Run #1](https://github.com/animeshpthk07/AegisRisk/actions/runs/38502931162) completed successfully for commit `423ea5bd6f99b9b5c1588827f51fb79d84f5e904`.

- Backend job passed: install, lint, pytest, PostgreSQL migration/read smoke and pip-audit.
- Frontend job passed: frozen-lockfile install, typecheck, unit tests, production build and production dependency audit.
- GitHub displayed Node 20 action-runtime deprecation warnings and an upcoming runner-image migration notice. These are maintenance items, not a claim of a failed build.
- Job/step outcomes were verified in the GitHub UI. Expanded log bodies failed to load in the browser, so test counts above remain the earlier local results.
- A successful dependency audit is not a penetration test, regulatory validation or proof of production safety.

### CSV preview verification — 2026-10-15

[Run #5](https://github.com/animeshpthk07/AegisRisk/actions/runs/38730979855) passed for commit `f0c0caf0d4ad47453c7ecbd2a197a70a992b084a`: backend and frontend jobs both succeeded. This covers the CSV API tests and the frontend typecheck/tests/production build, not a fresh interactive browser test of the new panel.

- Preview accepts explicitly acknowledged synthetic UTF-8 CSV, at most 256 KiB / 1,000 rows. Invalid records produce field-level issues and no partial totals. It never saves uploaded data or replaces the active portfolio.
- The dashboard provides a fictional example, a downloadable CSV, validation feedback and independent totals. Expected example: 2 records, INR 3,000 EAD and INR 66 one-year EL.
- The failure email corresponds to [run #3](https://github.com/animeshpthk07/AegisRisk/actions/runs/38559344804): Ruff FURB157 rejected a verbose Decimal constructor at imports.py:89. Commit `f247e0f` corrected it; [run #4](https://github.com/animeshpthk07/AegisRisk/actions/runs/38559598226) and run #5 passed. The historical failed run remains in the audit trail.
- At this checkpoint, interactive browser behavior was still unverified; the 2026-10-16 full-stack checkpoint below supersedes that limitation for the tested CSV-preview flows. Full application coverage and public deployment remain incomplete.

### Full-stack CSV browser verification — 2026-10-16

[Run #8](https://github.com/animeshpthk07/AegisRisk/actions/runs/38855476887) passed for commit `5e8ce09e82e8452d037ebc8d069c999ee8a497c4`. GitHub showed backend (37s), frontend (25s) and Full-stack browser checks (1m 8s) all successful.

- Chromium exercised the production Next.js server, fixed proxy, real FastAPI and isolated SQLite database with the 40-record fictional seed. The existing backend job separately checks PostgreSQL migration/read readiness.
- Covered consent gating, desktop/mobile example previews, CSV download, UTF-8 BOM upload, exact EAD/EL, invalid PD with no partial totals, unsupported/empty/oversized files, proxy guards and recovery from one explicitly simulated 503. Portfolio summary totals are checked before and after each case.
- [Run #7](https://github.com/animeshpthk07/AegisRisk/actions/runs/38782651556) exposed test-harness defects: global alert locators also matched the Next.js route announcer, and an oversized fixture payload became an oversized evidence filename. Explicit test IDs, bounded filenames and panel-scoped locators resolved them without weakening assertions or changing application behavior. The historical failure remains visible.
- Screenshots, traces, JUnit results and server logs are available in the synthetic-only `browser-check-evidence` artifact for seven days. Follow [DEVELOPMENT.md](DEVELOPMENT.md#full-stack-browser-verification) to reproduce.
- Job success was verified in GitHub. The successful test step's expanded log did not load reliably, so no new exact test-count claim is made here. Existing action-runtime and runner-image notices remain maintenance items.
- This is limited full-stack CSV-preview coverage, not complete E2E/accessibility/security certification, persisted imports, Firefox/WebKit coverage or hosted deployment.
- Next: persisted synthetic imports with explicit review, atomic database transactions, duplicate handling and regression tests. Preview success is not import persistence.

### What you can inspect

`apps/web/app/page.tsx` contains the dashboard. `apps/api/aegisrisk/main.py` exposes API endpoints. `risk.py` contains the formulas. `docs/ARCHITECTURE.md` explains the system, `docs/DEVELOPMENT.md` shows how to run it, and `docs/SECURITY.md` records limits.

This is a foundation slice, not the completed AegisRisk product. ML, persisted CSV/XLSX imports, reports, full security verification and career materials remain incomplete.

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 Foundation | Foundation checkpoint verified | Public source, setup docs, frontend/backend builds and GitHub CI; full product scope remains below |
| M1 Data layer | Partial | SQLAlchemy facilities, Alembic migration and 40 synthetic records; validated CSV preview implemented, persisted CSV/XLSX imports pending |
| M2 Risk mathematics | Partial | Decimal EL, weighted metrics and HHI implemented and tested; full scope pending |
| M3 ML | Not started | No model performance claims |
| M4 Stress | Partial | Bounded PD/LGD/EAD sensitivity verified; broader scenarios pending |
| M5 API | Partial | Versioned foundation endpoints plus bounded CSV preview and validation tests; full scope pending |
| M6 Full frontend | Partial | Portfolio dashboard, scenario controls and CSV preview panel; CSV flows verified in CI Chromium, full workbench pending |
| M7 Explanations | Not complete | Deterministic only; external AI deferred |
| M8 Reports | Not started | |
| M9 Security | In progress | Local-only, synthetic-only, no API credentials |
| M10 Full verification | Partial | Backend/frontend/CSV Chromium CI passed; broader E2E, accessibility, Compose and security verification pending |
| M11 Deployment | Not complete | Public source published; no hosted application verified or paid service purchased |
| M12 Release | Not started | |
| Career presentation and learning | Not started | Begin after credible verified application |

## Visible workflow requested by user

1. **Code:** visible browser editor at https://vscode.dev/github/animeshpthk07/AegisRisk (`apps/web`, `apps/api`). Browser-only work is the current instruction.
2. **Run:** local frontend http://127.0.0.1:3000, backend http://127.0.0.1:8000/docs.
3. **Verify:** tests, browser interactions, and recorded results here. Never label checks passed just because files exist.
4. **GitHub:** public MIT repository created with approval; backend and dashboard committed. Review commits and Actions through the visible browser.
5. **Release:** deployment only after required verification and user approval; no hosting account or expense created.
6. **LinkedIn:** case study/project/launch drafts after verification; show exact content before publishing.

Earlier local runtime checks are historical results, not a claim that those processes are still running. No paid services or external AI credentials have been configured.
