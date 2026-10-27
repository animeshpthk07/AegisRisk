# Execution tracker

Started 2026-10-13. Updated 2026-10-27. Public GitHub publication approved by the owner. No external AI enabled.

## Current activity — live development

The frontend-to-backend-to-database flow was verified locally. The foundation source is now published at https://github.com/animeshpthk07/AegisRisk. Current work uses VS Code for the Web and GitHub in the visible browser, as requested. The local preview is not a public deployment.

### What is saved

- Separate Git repository at `work/AegisRisk`; Finance Workbench is untouched.
- Next.js 16.4.1 / React 19.3 / TypeScript / Tailwind / Recharts frontend.
- FastAPI / SQLAlchemy / Alembic backend, explicit seed of 40 fictional INR facilities.
- Decimal EL calculation, EAD weights, borrower HHI, industry breakdown, search and scenario sensitivity.
- Bounded synthetic CSV / values-only XLSX preview with row-level validation and independent risk totals; preview performs no database writes.
- Opt-in reviewed CSV / XLSX snapshots with immutable storage, dataset selection and duplicate-file reuse; saving remains disabled by default.
- Baseline and scenario-comparison JSON, printable HTML and server-generated PDF evidence reports with dataset identity, Decimal computation evidence and canonical input fingerprints.
- Deterministic narrative. No external AI provider or API credentials.
- PostgreSQL Compose and CI definitions. GitHub CI passed the PostgreSQL migration/read smoke and full Compose browser/restart lifecycle (latest verified application run #71).

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

### CI runtime maintenance — verified 2026-10-21

[Run #23](https://github.com/animeshpthk07/AegisRisk/actions/runs/39491329995) passed for commit `c8d6f66720b3640be8d15b47499fac82add8a02d`: backend 55s, frontend 31s, full-stack Chromium 1m 51s and PostgreSQL container lifecycle 3m 3s; total 3m 34s.

All four jobs now use Ubuntu 24.04. Official checkout/setup-node/setup-python/upload-artifact actions use v7; checkout does not persist credentials and automatic package-manager caching is disabled. Node 24, Python 3.12, read-only repository permissions, dependency audits, test assertions and seven-day evidence retention remain in place. No application security control was relaxed. This is CI maintenance, not deployment or completion of the remaining product milestones.

### Synthetic Model Lab — implementation 2026-10-22

Added an isolated 3,000-row fictional training recipe, train-only scaling, logistic regression and separate sigmoid calibration/test splits. The model card reports actual held-out metrics against a training-prior baseline, hashes, seeds, versions, calibration bins and limitations. A consent-gated dashboard demonstrates single-profile predictions and raw log-odds contributions without changing portfolio PDs or reports.

Backend and browser regressions cover leakage, reproducibility, bounded inputs, explanation arithmetic, desktop/mobile flows, failures/retry and stale request cancellation. The successful 2026-10-23 checkpoint below records verification of this slice. See [MODEL_LAB.md](MODEL_LAB.md). No real-world performance, production security or hosted release is claimed.

### Synthetic Model Lab and security patch — verified 2026-10-23

[Run #27](https://github.com/animeshpthk07/AegisRisk/actions/runs/39834579698) passed all four jobs for commit `b9ddf98ebe9c115aaf1625f681595032a7d6ea0f`: backend 1m 3s, frontend 36s, full-stack Chromium 3m 2s and PostgreSQL container lifecycle 3m 10s; total 3m 35s.

- Backend: **130 passed**, one warning; lint, PostgreSQL migration/read smoke and pip-audit passed.
- Frontend: **19 passed**, typecheck and Next.js 16.4.1 production build passed; frozen-lockfile installation accepted the updated resolution and integrity checks, and the production audit found no known vulnerabilities.
- All full-stack Chromium checks passed. Against the real Compose images and PostgreSQL, **61 passed in 64.26s**. Restart/reseed recovery preserved the recorded evidence and duplicate saves reused the existing snapshot.
- New Model Lab coverage includes disjoint data splits, train-only scaling, calibration isolation, repeated results, held-out metrics, explanation arithmetic, strict consent/input validation, malformed and deeply nested JSON rejection, desktop/mobile flows, retry recovery and stale-result cancellation across every input. The model remains isolated from portfolio PDs and reports.
- Run #25 failed six input-label browser cases in both test environments. Commit `923619d` supplied explicit accessible names without removing assertions; run #26 passed backend/browser/container checks but its frontend dependency audit flagged three newly listed Next.js advisories.
- Next.js was patched from 16.4.0 to 16.4.1, including its environment and eight platform compiler packages. The ten package integrity values were checked against the official npm registry; already-pinned Sharp 0.35.5 meets the patched requirement. [Official release/advisories](https://github.com/vercel/next.js/releases/tag/v16.4.1). Audits and frozen-lockfile enforcement were not bypassed. Historical failed runs remain visible.
- Synthetic-only screenshots, traces, logs and results are retained for seven days in the [browser evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/39834579698/artifacts/12450776383) and [container evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/39834579698/artifacts/12449359244).

This verifies the implemented synthetic research workflow and its tested integrations, not real-world predictive performance, fairness, regulatory suitability, penetration testing or hosted deployment. A clean dependency audit is a point-in-time check, not a security guarantee.

### Server-generated PDF evidence — verified 2026-10-24

[Run #34](https://github.com/animeshpthk07/AegisRisk/actions/runs/40078175863) passed all four jobs for commit `cb756b67c6e46807b3078307d79afbff81eda46f`: backend 1m 22s, frontend 27s, full-stack Chromium 3m 2s and PostgreSQL container lifecycle 3m 39s; total 3m 43s. The job logs were read through the visible browser.

- Backend: **141 passed**, one warning; lint, PostgreSQL migration/read smoke and dependency audit passed.
- Frontend: **19 passed**, frozen-lockfile installation, typecheck, Next.js 16.4.1 production build and production dependency audit passed. Both dependency audits reported no known vulnerabilities at this checkpoint.
- Full-stack browser checks: **77 passed in 100.99s** with the native test servers; **77 passed in 82.18s** against real Compose images and PostgreSQL. Container restart, repeat migration/seed and duplicate reuse checks also passed.
- ReportLab renders baseline/scenario PDF envelopes from a single load of the same report evidence. Bounds are 1,000 facilities and 4 MiB. Export performs no database write, provider call or external asset fetch. The browser validates identity, assumptions, calculated totals, byte count, PDF header and SHA-256, then rechecks request versions after asynchronous hashing.
- Regression coverage includes real desktop/mobile demo and saved-snapshot downloads; failed or malformed responses with retry; stale responses and assumption changes; API input/loader guards; a 1,000-row document with all identifiers retained; and literal markup/Unicode-escape handling. PDF extraction checks do not substitute for visual review.
- **Visual review completed in the browser:** all 13 Poppler-rendered fixture pages were inspected (baseline 4, literal labels 2, scenario 7). Text, tables, repeated headings and numbered footers were readable without clipping/overlap. The scenario summary labels INR amounts, fractional change and affected-facility count separately. Baseline evidence limitations and scenario limitations have distinct headings. This is fixture-specific review, not proof for every possible input or print device.
- Interpretation fixes are in `f8df7fd`; regression assertions in `3eb68ed`; the PDF contract in `cb756b6`. Runs #32, #33 and #34 all passed. Historical failed runs remain visible; this entry does not relabel them successful.
- Seven-day artifacts: [PDFs and rendered pages](https://github.com/animeshpthk07/AegisRisk/actions/runs/40078175863/artifacts/12554310733), [browser evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40078175863/artifacts/12553868637), and [container evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40078175863/artifacts/12554276792).

Portable PDF labels use explicit Unicode escapes for non-ASCII characters; JSON retains original text. These are not tagged accessible or digitally signed PDFs. A digest is an integrity check, not trusted provenance. This checkpoint does not establish authentication, public-hosted operation, independent model validation, production security or completion of all five project phases. See [the PDF contract](CONTRACT.md#server-generated-pdf-evidence).

### Browser security policy — verified 2026-10-25

[Run #43](https://github.com/animeshpthk07/AegisRisk/actions/runs/40174744456) passed all four jobs for commit `2bc6949a7d29fe47d468b1457f93e3651fdfdf79`: backend 1m 17s, frontend 28s, full-stack Chromium 3m and PostgreSQL container lifecycle 4m 15s; total 4m 20s. The job logs were read through the visible browser.

- Backend: **141 passed**, one warning; lint, PostgreSQL migration/read smoke and dependency audit passed. Frontend: **19 passed**, typecheck and production build passed. Both audits reported no known vulnerabilities at this checkpoint.
- Chromium: **83 passed in 100.72s** with native test servers and **83 passed in 90.40s** against Compose/PostgreSQL. These are the same cases in two environments, not 166 distinct cases. Restart/reseed recovery preserved all recorded evidence and duplicate retries reused the snapshot.
- The web layer now denies camera, microphone, geolocation and payment capabilities, suppresses referrers and the framework identification header, and restricts embedding, objects, base URLs and form destinations. Six additional browser cases verify policy headers on normal/error/API/PDF responses, browser capability enforcement and a real request with no referrer.
- Run #40 exposed an incorrect new test expectation: a disallowed proxy method/resource pair returns the established 404 contract, not 405. The test expectation was corrected in `2bc6949`; application behavior and assertions were retained. Historical failed runs remain visible.
- Seven-day evidence: [browser](https://github.com/animeshpthk07/AegisRisk/actions/runs/40174744456/artifacts/12590964462), [containers](https://github.com/animeshpthk07/AegisRisk/actions/runs/40174744456/artifacts/12591468323), [PDF fixtures](https://github.com/animeshpthk07/AegisRisk/actions/runs/40174744456/artifacts/12591238862). The 13-page visual PDF review remains the dated run #34 review above; these header-only changes do not claim a new layout review.

This is a bounded browser-security improvement, not authentication, a complete script/style CSP, penetration testing or a public deployment. See [SECURITY.md](SECURITY.md) for the remaining boundaries.

### Usability and public-demo image checkpoint — 2026-10-26

[Run #50](https://github.com/animeshpthk07/AegisRisk/actions/runs/40250142556), commit `aa739a956e07504919cd33560933da834ca47f5e`, passed all four application jobs with 141 backend tests, 19 frontend tests and 90 Chromium cases in each native/SQLite and Compose/PostgreSQL environment. The seven additional cases were saved in `86d72e1`: keyboard workflows at 1440/320 pixels, both-theme reflow at both widths, and reduced-motion scrolling. Four overview screenshots were visually reviewed; this is not full screen-reader/zoom/browser-engine certification.

The separate [Public demo image run #3](https://github.com/animeshpthk07/AegisRisk/actions/runs/40322565275), commit `9b5715a0626f6e4a94e52fdabf7904dc117627ec`, passed with **31 reused browser cases in 26.60s** and **four demo runtime cases in 10.88s**. The same commit passed [full application run #61](https://github.com/animeshpthk07/AegisRisk/actions/runs/40322565203): backend, frontend, full-stack Chromium and PostgreSQL lifecycle. The 31 image browser cases are a subset of the existing 90, not 31 additional distinct cases.

- The real non-root image was built, then exercised with a 512 MB memory limit, one CPU, 128 PIDs, all capabilities dropped and no privilege escalation. This is a test configuration, not a provider performance guarantee.
- Startup rejects enabled persistence and a privileged public port. Actual saved-portfolio requests remain disabled while fictional CSV/XLSX previews work.
- Baseline/scenario JSON, printable HTML and PDF were downloaded through the real browser. Transport-size rejection, shared rate limits (including spoofed forwarding headers), recovery, restart and fresh-container seed recovery all passed.
- Initial demo runs #1 and #2 failed readiness: Nginx attempted to create `/var/lib/nginx/fastcgi` as a non-root user. Diagnostic run #2 showed the permission error. Commit `9b5715a` moved all remaining Nginx temporary paths into the writable temporary directory; run #3 then passed. No checks or security restrictions were removed.
- Synthetic [demo evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40322565275/artifacts/12649986138) expires after seven days. See [deployment settings, cost boundaries and rollout checks](DEPLOYMENT.md).
- The owner chose to keep AegisRisk on GitHub for now on 2026-10-26. Hosting is intentionally deferred; the proposed Render Free service has not been created. No hosted URL or hosted smoke result is claimed. The deployment package remains available for a future explicit decision. No API credentials or paid services were configured.

### Three-engine browser verification — confirmed 2026-10-27

[Application run #70](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371011488), commit `6611ec20fc941888419ac501c482d7d3054459d5`, passed all six jobs: backend, frontend, Chromium, Firefox, WebKit and PostgreSQL container lifecycle. [Run #71](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371380326) also passed after the reproduction-guide update. The matrix runs the existing real application workflows in separate runners with engine-specific artifacts. Chromium passed 91 cases; Firefox passed 90 with one explicit skip for the Chromium-only permissions-policy inspection. WebKit passed the same 90 cases with that explicit skip in the preceding [run #69](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371000876). Header and referrer checks remain enabled on every engine. These repeat the same workflows, not hundreds of distinct cases.

[Demo image run #5](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371011459) passed for `6611ec2`: 32 selected browser cases, four runtime cases, startup restrictions and restart/fresh-container recovery. Hosting remains deferred by owner decision. Linux Playwright WebKit is not branded Safari or a physical iOS test; screen-reader, browser zoom and physical-device verification remain incomplete.

The first attempt of documentation-only run #72 reached the 15-minute job limit while downloading Firefox system dependencies from the Ubuntu mirror. The Firefox application tests had not started; the other jobs passed. The cancelled attempt remains in the history and is not relabelled successful. The focused Firefox retry passed on 2026-10-27, and run #72 now reports Success. The original timed-out attempt remains part of the run history.

### GitHub educational preview — 2026-10-27

Published [v0.1.0-preview.1](https://github.com/animeshpthk07/AegisRisk/releases/tag/v0.1.0-preview.1) as a GitHub **Pre-release**, pinned to `6611ec20fc941888419ac501c482d7d3054459d5`. That exact source passed application run #70 and demo image run #5. The release provides source archives, reproducible setup links, scope and known limitations. Later documentation-only commits on main are not silently substituted for this pinned version.

This packages the verified fictional-data educational slice; it does not complete all five phases or the authenticated workbench. Hosting remains deferred, external AI disabled and LinkedIn publication unperformed. The release notes retain the outstanding identity/authorization, full CSP, operational, accessibility and real-world-validation limits.

### What you can inspect

`apps/web/app/page.tsx` contains the dashboard. `apps/api/aegisrisk/main.py` exposes API endpoints. `risk.py` contains the formulas. `docs/ARCHITECTURE.md` explains the system, `docs/DEVELOPMENT.md` shows how to run it, and `docs/SECURITY.md` records limits.

This is a growing verified slice, not the completed AegisRisk product. Reviewed CSV persistence is verified. Values-only XLSX review/save/reports are verified by run #20. Printable HTML reports are verified by run #21. The synthetic Model Lab and Next.js security patch are verified by run #27, and server-generated PDFs by run #34. Broader ML validation, full security verification, hosted deployment and public career materials remain incomplete.

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 Foundation | Foundation checkpoint verified | Public source, setup docs, frontend/backend builds and GitHub CI; full product scope remains below |
| M1 Data layer | Partial | SQLAlchemy facilities, Alembic migration and 40 synthetic records; validated CSV preview and reviewed immutable CSV persistence implemented; values-only XLSX verified |
| M2 Risk mathematics | Partial | Decimal EL, weighted metrics and HHI implemented and tested; full scope pending |
| M3 ML | Synthetic research slice verified (run #27) | Isolated logistic regression, held-out calibration/test data, baseline metrics and raw-score contributions; no real-world validation |
| M4 Stress | Partial | Bounded PD/LGD/EAD sensitivity, industry scope and guarded scenario-comparison export verified; broader scenarios pending |
| M5 API | Partial | Versioned portfolio, preview, reviewed snapshots, baseline/scenario reports and isolated model-card/prediction endpoints; full scope pending |
| M6 Full frontend | Partial | Dashboard, scenario controls, CSV / XLSX review/save/select and baseline/scenario JSON, printable HTML and PDF downloads; full workbench pending |
| M7 Explanations | Not complete | Deterministic only; external AI deferred |
| M8 Reports | Educational evidence-export slice verified (run #34) | Baseline/scenario JSON, printable HTML and server-generated PDF; exact evidence, identity/digest/stale-result guards and 13-page visual fixture review; accessible tagged/multilingual/signed reports remain outside this implementation |
| M9 Security | In progress; browser policy verified (run #43) | Synthetic-only defaults, no API credentials, bounded proxy and browser policy checks; authentication, full CSP and operational controls remain incomplete |
| M10 Full verification | Partial | Backend/frontend and real workflows pass in Chromium, Firefox and WebKit; Compose browser/restart lifecycle passes; screen-reader, zoom, physical-device and broader security verification remain pending |
| M11 Deployment | Image package verified; hosting deferred by owner | Public demo image run #3 passes; Render Free proposal and cost/rollback guide saved; no actual hosted URL verified |
| M12 Release | Educational preview published; full product incomplete | v0.1.0-preview.1 pins the source verified by application #70 and demo #5; hosting deferred and broader acceptance gaps remain |
| Career presentation and learning | Partial | Reproducible reviewer walkthrough and technical discussion guide added; public career materials and LinkedIn launch remain pending |

## Visible workflow requested by user

1. **Code:** visible browser editor at https://vscode.dev/github/animeshpthk07/AegisRisk (`apps/web`, `apps/api`). Browser-only work is the current instruction.
2. **Run:** local frontend http://127.0.0.1:3000, backend http://127.0.0.1:8000/docs.
3. **Verify:** tests, browser interactions, and recorded results here. Never label checks passed just because files exist.
4. **GitHub:** public MIT repository created with approval; backend and dashboard committed. Review commits and Actions through the visible browser.
5. **Release:** deployment only after required verification and user approval; no hosting account or expense created.
6. **LinkedIn:** case study/project/launch drafts after verification; show exact content before publishing.

Earlier local runtime checks are historical results, not a claim that those processes are still running. No paid services or external AI credentials have been configured.
