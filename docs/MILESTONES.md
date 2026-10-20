# Execution tracker

Started 2026-10-13. Updated 2026-10-21. Public GitHub publication approved by the owner. No external AI enabled.

## Current activity — live development

The frontend-to-backend-to-database flow was verified locally. The foundation source is now published at https://github.com/animeshpthk07/AegisRisk. Current work uses VS Code for the Web and GitHub in the visible browser, as requested. The local preview is not a public deployment.

### What is saved

- Separate Git repository at `work/AegisRisk`; Finance Workbench is untouched.
- Next.js 16.4 / React 19.3 / TypeScript / Tailwind / Recharts frontend.
- FastAPI / SQLAlchemy / Alembic backend, explicit seed of 40 fictional INR facilities.
- Decimal EL calculation, EAD weights, borrower HHI, industry breakdown, search and scenario sensitivity.
- Bounded synthetic CSV / values-only XLSX preview with row-level validation and independent risk totals; preview performs no database writes.
- Opt-in reviewed CSV / XLSX snapshots with immutable storage, dataset selection and duplicate-file reuse; saving remains disabled by default.
- Baseline and scenario-comparison JSON evidence reports with dataset identity, Decimal computation evidence and canonical input fingerprints.
- Deterministic narrative. No external AI provider or API credentials.
- PostgreSQL Compose and CI definitions. GitHub CI passed the PostgreSQL migration/read smoke and full Compose browser/restart lifecycle (run #22).

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

### Reviewed snapshot verification — 2026-10-17

[Run #12](https://github.com/animeshpthk07/AegisRisk/actions/runs/38982082684) passed for commit `73cc16b0145e2263c7daf1d87face29bbfed9f83`: backend (35s), frontend (27s), and full-stack browser checks (1m 14s).

- CSV review/save/open/reload, duplicate reuse, dataset-scoped calculations and stale stress-response protection were covered. Saving stays explicitly opt-in and local/single-user only.
- Run #10 stopped at an import-order lint error. Run #11 exposed an overly broad browser assertion. Both were corrected; historical failures remain visible.
- This supersedes the earlier statement that persisted CSV imports were pending. XLSX, authentication and public hosting remain incomplete.

### Baseline report verification — 2026-10-18

[Run #14](https://github.com/animeshpthk07/AegisRisk/actions/runs/39076727875) passed for commit `3d9024268caff9b7dcc359af71c24141e279e624`: backend (36s), frontend (21s) and full-stack Chromium (1m 22s); total run duration 1m 26s.

- Baseline JSON downloads include dataset identity/version, source input fingerprint, decimal computation evidence, shared dashboard totals and deterministic explanations. The report explicitly excludes stress scenarios and regulatory/audit claims.
- API regression tests cover single-load construction, repeatability excluding generation time, canonical row order/numeric spelling, empty/zero exposure, disabled saved access, unknown IDs and corrupt snapshot rejection.
- The Chromium test step reported **21 passed in 22.72s**. Browser regression tests verify actual demo/saved JSON downloads, visible errors with no download, retry recovery, stale response protection across A → B and A → B → A, and an active selection surviving catalog refresh. Existing preview/snapshot coverage still runs.
- Run #13 passed backend/frontend but the browser job stopped at eight E501 line-length errors in new tests. Commit `3d90242` wrapped those lines without removing assertions; run #14 then passed all jobs.
- Evidence is retained for seven days in the [browser-check-evidence artifact](https://github.com/animeshpthk07/AegisRisk/actions/runs/39076727875/artifacts/12117606105). Existing action-runtime warnings and upcoming runner-image notices are maintenance items, not verification failures.
- This is a baseline JSON reporting checkpoint, not completion of formatted reports, ML, XLSX, authentication, production security or deployment.

### Scenario comparison report verification — 2026-10-18

[Run #17](https://github.com/animeshpthk07/AegisRisk/actions/runs/39144933526) passed for commit `33e355d0c3d8b392596e324e07b0bd5c6cfe76dc`: backend (29s), frontend (29s) and full-stack Chromium (1m 50s); total run duration 1m 54s.

- Read-only scenario JSON exports include a complete baseline report, dataset identity/version, submitted multipliers and scope, baseline/stressed/delta losses, fractional percentage change and per-facility decimal evidence with cap/affected flags. Stress and reporting share the calculation path; each report loads the selected dataset once.
- The UI binds downloads to the calculated assumptions and selected portfolio. Editing any of the four controls or switching portfolios clears old results and cancels pending calculations/exports. Outages or identity/input/result mismatches produce a visible error with no download; retry remains available.
- The Chromium step reported **38 passed in 45.80s**. Coverage includes actual desktop/mobile demo and saved-snapshot downloads, exact calculation/report parity, proxy limits, injected failures, all four controls changing during calculation/export, and A → B/A → B → A portfolio changes. Backend tests cover scope, caps, zero/empty cases, loader guards and immutable baselines.
- Run #16 passed backend/frontend but eight browser cases timed out on an exact scope-label lookup. Giving the dropdown the explicit accessible name `Scenario scope` and updating those locators resolved the failure. No cases or assertions were removed.
- Synthetic-only screenshots, traces, JUnit results and server logs are retained for seven days in the [browser-check-evidence artifact](https://github.com/animeshpthk07/AegisRisk/actions/runs/39144933526/artifacts/12143485075). See [DEVELOPMENT.md](DEVELOPMENT.md#inspect-a-scenario-comparison-report) for reproduction.
- This verifies the tested JSON-reporting slice, not formatted reports, saved scenario history, macroeconomic forecasting, ML, XLSX, authentication, production security or public deployment. Action-runtime/runner-image maintenance notices remain.

### Values-only XLSX verification — 2026-10-19

Added bounded ZIP/XML decoding, shared row validation, raw-upload review and normalized-storage fingerprints, local-only reviewed persistence, and CSV/XLSX UI support. New API cases exercise unsafe/corrupt/unsupported workbooks and metadata-only duplicate handling. New Chromium cases cover desktop/mobile save/reload/reports, formula/corrupt-file recovery and proxy limits.

[Run #20](https://github.com/animeshpthk07/AegisRisk/actions/runs/39217858867) passed for commit `0ff7c60625c6c0a35187e4bfdbc4430b0019ce5b`: backend 39s, frontend 28s and full-stack browser checks 1m 58s. Chromium reported **44 passed in 53.42s**. Synthetic-only evidence is retained for seven days in [the run artifact](https://github.com/animeshpthk07/AegisRisk/actions/runs/39217858867/artifacts/12169904166).

Run #19 passed frontend/browser but stopped backend before tests at one I001 import-order rule in xlsx.py. Sorting those imports resolved it; no test assertions or validation checks were removed. No production-security or public-hosting claim is made.

### Printable evidence reports — verified 2026-10-19

Added standalone printable HTML baseline/scenario downloads using the existing API evidence and stale-response guards. The renderer escapes text, embeds no scripts/external assets, prints decimal evidence unchanged, and provides print styles. Unit tests cover malformed evidence and injection text; Chromium tests download/open real reports at desktop/mobile widths and exercise print media. This is not server-generated PDF or a completed security review.

[Run #21](https://github.com/animeshpthk07/AegisRisk/actions/runs/39218815669) passed for commit `19ed7421fd0ef2db247db41f65c87e621bb7607a`: backend 39s, frontend 22s, full-stack Chromium 2m 11s; total 2m 16s. The browser test step reported **48 passed in 61.31s**. Synthetic HTML, screenshots, traces and results are retained for seven days in [the evidence artifact](https://github.com/animeshpthk07/AegisRisk/actions/runs/39218815669/artifacts/12170318239).

Tested documents opened offline, preserved escaped injection-like text, issued no HTTP requests/dialogs, and exposed print styles with repeated table headers at desktop/mobile widths. This does not establish all-browser pagination, full accessibility or production security. Existing action-runtime/runner-image notices remain maintenance items.

### PostgreSQL container lifecycle — verified 2026-10-21

Added an independent CI job that builds the actual API/standalone web images, verifies saving is disabled in the default Compose stack, runs all existing Chromium cases with a test-only save override, then compares saved/demo/report/catalog evidence after PostgreSQL restart and repeat migration/seed. The override is isolated to a disposable CI project; production defaults and loopback bindings remain unchanged. 

[Run #22](https://github.com/animeshpthk07/AegisRisk/actions/runs/39445548042) passed for commit `40358a32e725bf784ec962eaf7385adb94633dee`: backend 44s, frontend 29s, native full-stack Chromium 1m 40s, and PostgreSQL container lifecycle 2m 37s; total 2m 41s. The container browser step reported **48 passed in 45.16s**.

The real API and standalone web images built successfully. Default saving was blocked while preview remained available. The test-only override then enabled fictional snapshots. PostgreSQL/API/web restart, repeat migrations and seed retained the existing portfolio; every recorded report/catalog field except generation timestamps matched, and an identical save reused the original UUID. Synthetic-only evidence is retained for seven days in [container-check-evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/39445548042/artifacts/12275454749).

This verifies the tested container path on an isolated GitHub runner, not hosted deployment, backups/disaster recovery, production security, authentication or bank validation. The run's action-runtime and runner-image notices are maintenance warnings, not failures.

### What you can inspect

`apps/web/app/page.tsx` contains the dashboard. `apps/api/aegisrisk/main.py` exposes API endpoints. `risk.py` contains the formulas. `docs/ARCHITECTURE.md` explains the system, `docs/DEVELOPMENT.md` shows how to run it, and `docs/SECURITY.md` records limits.

This is a growing verified slice, not the completed AegisRisk product. Reviewed CSV persistence is verified. Values-only XLSX review/save/reports are verified by run #20. Printable HTML reports are verified by run #21; ML, server-generated PDF, full security verification and career materials remain incomplete.

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 Foundation | Foundation checkpoint verified | Public source, setup docs, frontend/backend builds and GitHub CI; full product scope remains below |
| M1 Data layer | Partial | SQLAlchemy facilities, Alembic migration and 40 synthetic records; validated CSV preview and reviewed immutable CSV persistence implemented; values-only XLSX verified |
| M2 Risk mathematics | Partial | Decimal EL, weighted metrics and HHI implemented and tested; full scope pending |
| M3 ML | Not started | No model performance claims |
| M4 Stress | Partial | Bounded PD/LGD/EAD sensitivity, industry scope and guarded scenario-comparison export verified; broader scenarios pending |
| M5 API | Partial | Versioned portfolio, preview, reviewed snapshots, baseline and scenario-report endpoints; full scope pending |
| M6 Full frontend | Partial | Dashboard, scenario controls, CSV / XLSX review/save/select and baseline/scenario JSON and printable HTML downloads; full workbench pending |
| M7 Explanations | Not complete | Deterministic only; external AI deferred |
| M8 Reports | Partial | Baseline/scenario JSON and printable HTML evidence exports verified; server-generated PDF pending |
| M9 Security | In progress | Local-only, synthetic-only, no API credentials |
| M10 Full verification | Partial | Backend/frontend/CSV/snapshot/report Chromium CI passed; Compose browser/restart lifecycle also passed; broader E2E, accessibility and security verification pending |
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
