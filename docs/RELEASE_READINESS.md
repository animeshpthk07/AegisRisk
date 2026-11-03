# Release readiness

Updated 2026-11-03. This document defines the evidence needed for a release; it does not declare all five project phases complete.

## Current deliverable

AegisRisk is a public MIT educational workbench using fictional INR credit facilities. It includes bounded CSV/XLSX review, opt-in immutable snapshots, Decimal risk calculations, scenario sensitivity, JSON/HTML/PDF evidence exports and an isolated synthetic Model Lab. External AI is disabled. The published educational preview remains pinned to `6611ec20fc941888419ac501c482d7d3054459d5`. The later verified development checkpoints below record workspace access, browser script policy and demo-test reliability work.

On 2026-10-26 the owner chose to keep the project on GitHub for now. Hosting is intentionally deferred; no service was created, paid plan accepted or hosted URL verified. The subsequent [three-engine application run #69](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371000876) passed all six jobs for `deeb228109af43552b728e3be63140424744d377`. A public repository and passing CI do not establish an authenticated hosted service. Optional workspace tokens are verified in the checkpoint below; production identity and operational controls remain unfinished.

## Combined main integration — verified 2026-11-03

[PR #3](https://github.com/animeshpthk07/AegisRisk/pull/3) and [PR #4](https://github.com/animeshpthk07/AegisRisk/pull/4) are merged. Combined main commit `f17650ec74aee37b5c20bdeebcf346c481ab2488` passed all six jobs in [application run #160](https://github.com/animeshpthk07/AegisRisk/actions/runs/41537535832): backend, frontend, Chromium, Firefox, WebKit and PostgreSQL lifecycle. The preceding PR #3 merge `de105e9605f8fc4d9d0d4101d4ee0a63cb701082` passed [demo image verification](https://github.com/animeshpthk07/AegisRisk/actions/runs/41537328044). PR #4 changes documentation only; the demo was not rerun for its merge. The earlier main application run was superseded and cancelled, not relabelled successful.

Architecture and demonstration guidance now describe optional workspace access accurately. [PROJECT_PRESENTATION.md](PROJECT_PRESENTATION.md) contains a walkthrough, CV bullets and draft LinkedIn copy. These are saved reviewer materials; the LinkedIn post is not published or approved. Production identity, storage operations, independent validation and the remaining accessibility checks are still open. Hosting remains deferred by owner decision.

## Main-branch integration — verified 2026-11-02

PR #2 merged as `c30f0266ce4dc719d6cad3c0e391ac25b5f2c7d3`. That exact main commit passed [application verification](https://github.com/animeshpthk07/AegisRisk/actions/runs/41443684705) and [demo image verification](https://github.com/animeshpthk07/AegisRisk/actions/runs/41443684766). Its final pre-merge source `c86ad833c9a2d5e4b8154d8207d781c5be383959` passed application run #139 and demo run #50. These checks do not establish production approval.

## Automatic inactivity lock — verified 2026-11-03

[PR #3](https://github.com/animeshpthk07/AegisRisk/pull/3), source `8a232dbbe19526962bcfe08c1e9c091af1f9a444`, passed [application verification](https://github.com/animeshpthk07/AegisRisk/actions/runs/41492180418) and [demo image verification](https://github.com/animeshpthk07/AegisRisk/actions/runs/41492180561). Results were reviewed on 2026-11-03. Backend recorded 190 passing tests with one dependency warning; frontend recorded 19 passing tests. Chromium recorded 111 workflow cases and 18 access cases; Firefox and WebKit each recorded 110 workflow cases, one existing Chromium-only inspection skip and 18 access cases. Builds, typecheck, audits and PostgreSQL lifecycle checks passed. Demo verification recorded 41 reused browser cases plus four runtime cases. Repeated engines and environments are not additional distinct tests.

Token-mode tabs lock after 15 minutes of inactivity with a one-minute warning and keyboard-operable extension. Expiry clears credentials and loaded state and aborts pending requests. Wall-clock and monotonic checks run at timer, resume, activity and request boundaries. Anonymous local mode remains unchanged.

Seven added cases cover warning/extension/re-unlock at 1440 and 320 pixels, synthetic input, focus/visibility/request resume boundaries and rejection of a late response. Initial checks stopped at a long assertion and then exposed an incorrect standalone-text selector and an initial-load race in the test driver. The correction selects the actual facility row and waits for the loaded dashboard before advancing time; assertions and application restrictions were retained. Earlier failures remain visible.

This verifies browser cleanup, not server-side token revocation, enterprise identity, physical-device sleep or screen-reader behavior. Hosting remains deferred. These results do not declare all five project phases complete or change the source pinned by the published educational preview.

## Browser script policy — verified 2026-11-02

Source `fb920c2945beb4ed92ef34f7d60cb5a34a5751bb` passed [application run #132](https://github.com/animeshpthk07/AegisRisk/actions/runs/41317265512) and [bounded demo image run #46](https://github.com/animeshpthk07/AegisRisk/actions/runs/41317265488) on 2026-11-01; their completed results were reviewed in the browser on 2026-11-02. All 14 push/pull-request checks passed before the documentation follow-up.

- All six application jobs passed: backend, frontend, Chromium, Firefox, WebKit and PostgreSQL lifecycle. Backend recorded **190 passing tests**, one dependency deprecation warning and no known vulnerabilities in that dated audit. Chromium recorded **111 workflow cases plus 11 access cases**. The other engines passed their configured suites; the existing Chromium-only permissions inspection remains explicitly skipped outside Chromium.
- The bounded demo passed **41 reused browser cases plus four runtime cases**, startup restrictions, restart and fresh-container recovery. Repeated cases across engines, environments and events are not additional distinct coverage.
- Per-response random nonces, request-time rendering, caller-header overwrite, script/event-handler restrictions and resource rules are implemented. Nine policy cases check real response headers and browser enforcement. Parser-executed script probes retain the actual server CSP; debugger evaluation is not used as proof that scripts are blocked. The unchanged application workflows check compatibility.
- Four Chromium overview captures at 1440/320 pixels in dark/light themes were reviewed from run #132. The captured controls and text remain readable without overlapping panels. This is a dated overview review, not every screen, screen-reader, zoom or physical-device certification.
- The November 1 audit found seven advisories in the PDF inspection development dependency `pypdf==6.21.2`. Pinning `6.21.4` resolved the audit findings; the 190 backend tests and PDF fixture generation passed. Production PDF generation still uses ReportLab. No claim is made about vulnerabilities discovered after this audit.

Earlier runs exposed an API cache-header mismatch and test-driver problems: in-page polling used string compilation, debugger-injected scripts did not reliably exercise page policy, and a test button was covered by the application sidebar. The API retains its exact `no-store` contract; driver-side polling and parser-executed probes fix the tests without removing restrictions or assertions. Failed and superseded runs remain in history.

Style attributes remain allowed for chart positioning. Correctly nonced scripts and their dependencies remain trusted. Production identity, idle locking, quotas, retention/backup/deletion operations and independent security/model review remain incomplete. See [SECURITY.md](SECURITY.md). Hosting remains deferred and no real credentials were issued. This checkpoint does not replace the source pinned by v0.1.0-preview.1 or declare all five phases complete.

## Optional workspace access — verified 2026-10-30

[Application run #112](https://github.com/animeshpthk07/AegisRisk/actions/runs/40989999826) passed all six jobs for `45afa677368cd77a0c8e71aba702457e55b5f43d`: backend, frontend, Chromium, Firefox, WebKit and PostgreSQL lifecycle. Backend recorded 190 passing tests with one dependency deprecation warning. Chromium recorded 102 existing workflow cases plus 11 access cases; WebKit recorded 101 existing cases plus the documented Chromium-only inspection skip, and all 11 access cases. The same access suite passed in Firefox. Repeated engines/environments are not additional distinct cases.

Optional administrator-issued bearer tokens now gate protected APIs and the browser workbench. Server-side roles restrict saves; catalog, counts, deduplication, calculations and saved-data exports are workspace-scoped. Migration 0003 preserves legacy local snapshots and blocks unsafe downgrade. The browser keeps tokens in memory and clears workspace state on refresh, lock or rejected access. No real credentials were issued. [AUTHENTICATION.md](AUTHENTICATION.md) documents configuration and limits.

Two Chromium unlock captures at 1440 and 320 pixels were inspected through the run log: text, input focus, help and controls fit without page clipping or overlap. This is a review of those captures, not every authenticated screen or accessibility certification. The access tests use disposable credentials and omit traces. Synthetic artifacts have seven-day retention.

Run #106 failed three new access tests because a global alert locator also matched the Next.js route announcer. Commit `9eac24d` scopes those assertions to the access screen; the assertions and application restrictions were retained. Subsequent run #112 passed. Earlier failures and superseded/cancelled runs remain visible.

This is a development checkpoint, not a replacement for the source pinned by v0.1.0-preview.1 or completion of all five phases. The default local mode remains anonymous; optional tokens do not provide enterprise identity, MFA, idle locking, complete CSP, quotas or storage operations. Hosting remains deferred by owner decision.

## Published educational preview — 2026-10-27

[v0.1.0-preview.1](https://github.com/animeshpthk07/AegisRisk/releases/tag/v0.1.0-preview.1) is a GitHub **Pre-release**, pinned to `6611ec20fc941888419ac501c482d7d3054459d5`. [Application run #70](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371011488) passed all six jobs, and [demo image run #5](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371011459) passed for that same source. Source archives and pinned reproduction links are available on the release page. Subsequent commits on main do not change this released source.

This is a release of the verified fictional-data slice, not completion of all five phases. Hosting remains deferred, external AI disabled and LinkedIn launch unperformed. The shared-user security, accessibility and real-world validation limits below remain open. Documentation-only run #72 initially timed out downloading Firefox system dependencies before application tests started; its focused retry passed on 2026-10-27. The original cancelled attempt remains visible.

## Snapshot origin and demo-check reliability — 2026-10-27

Commit `0e3d6f5de982fe78927f0be6a791d440e24f9674` passed [application verification #85](https://github.com/animeshpthk07/AegisRisk/actions/runs/40519911411) and [demo image verification #12](https://github.com/animeshpthk07/AegisRisk/actions/runs/40519911435). This is a later development checkpoint; it does not silently replace the source pinned by v0.1.0-preview.1.

Snapshot saves through the web proxy require a matching Origin and, when supplied, same-origin fetch metadata. Eleven negative cases assert a 403 and an unchanged saved catalog for missing, opaque, foreign or malformed origins, conflicting fetch metadata and forged fallback headers. Existing browser save/reload/report workflows and the isolated PostgreSQL restart/reseed/duplicate-reuse checks cover allowed requests. This is browser-origin defense, not caller authentication or approval for shared persistence.

The initial comparison used NextURL, whose loopback normalization rejected valid local requests. Commit `9920a34` retains the actual HTTP Host authority; the lifecycle test client now explicitly supplies its Origin. Historical failures remain visible. Demo run #8 also exposed an unrelated test burst: Nginx correctly rate-limited rapid automated page loads. The normal UI suite now waits one second between cases only in the bounded-demo job. The production quota, dedicated burst test, recovery assertions and application assertions were not relaxed.

## Acceptance evidence

| Area | Evidence required | Current status |
| --- | --- | --- |
| Reproducible source | Frozen dependencies, lint, tests, production build and dependency audits pass for the exact release commit | Published preview commit 6611ec2 passed all six application jobs in run #70 and demo image run #5; verify again for any future application release |
| Calculations and reports | Exact totals, dataset identity, scope/caps, errors, stale responses and real downloads tested | Implemented cases pass; see [CONTRACT.md](CONTRACT.md) |
| PDF layout | Rendered fixture pages reviewed for readable text, pagination and tables | All 13 pages reviewed for run #34 on 2026-10-24; review again after layout changes |
| Database lifecycle | Default save restriction, migrations, repeat seed, restart persistence and duplicate reuse checked | Isolated Compose/PostgreSQL checks pass |
| Browser usability | Keyboard operation, visible focus, labels, zoom/reflow and supported browser engines verified | Keyboard-only search/scenario/download at 1440/320px, both-theme reflow and reduced-motion checks pass; four overview captures reviewed. The same workflows also pass in Firefox and WebKit; screen-reader, browser zoom and physical-device validation remain pending |
| Shared-user security | Identity/session handling, authorization/tenant separation, CSRF strategy, full CSP and resource limits reviewed and tested | Token/workspace slice verified in run #112, nonce/resource policy in run #132 and inactivity cleanup in run #160; style-attribute exception, production identity, quotas, storage lifecycle and independent security review remain open |
| Operations | Documented quotas, retention, backups/restore where storage is enabled, monitoring and rollback | Demo limits, ephemeral storage and rollback documented in [DEPLOYMENT.md](DEPLOYMENT.md); actual hosted operations deferred, persistent shared-user operations incomplete |
| Hosted demo | Approved hosting account/cost, HTTPS URL and deployed-commit smoke evidence | Deferred by owner; image verified in CI, no hosted application claimed |
| Release and career materials | Accurate release notes, current screenshots, walkthrough and approved final public copy | Walkthrough and educational pre-release published; presentation/CV/LinkedIn drafts saved in PROJECT_PRESENTATION.md; full product release and approved LinkedIn launch remain pending |

Run #50 recorded 141 backend tests (one dependency deprecation warning), 19 frontend tests and 90 Chromium cases in each of two environments. Native browser tests passed in 104.15s and Compose/PostgreSQL browser tests in 105.66s. The two browser runs exercise the same cases and must not be counted as 180 distinct cases. Both dependency audits reported no known vulnerabilities at this checkpoint; these are dated checks. CI artifacts expire after seven days; preserve only synthetic release evidence needed for reproducibility.

## Usability checkpoint — 2026-10-26

The seven additional cases are saved in commit `86d72e1`; run #49 passed before the evidence-output change. Run #50 verifies the same application plus bounded UI-preview output (`aa739a9`). Keyboard checks use actual Tab/Enter/Space/arrow input through skip navigation, theme switching with visible focus, search, table scrolling, scenario calculation and a downloaded JSON report. Reflow checks retain internal table scrolling while rejecting document-wide horizontal overflow at 320 and 1440 CSS pixels in both themes. The reduced-motion preference disables animated document scrolling.

Four viewport captures from run #50 were inspected through its browser log: `ui-review-{1440,320}-{dark,light}.png`. The reviewed overview has readable text and controls with no overlap or page-wide clipping. This review covers those captured viewports, not every screen, screen-reader behaviour, browser zoom or all browser engines. The [browser evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40250142556/artifacts/12620203929) and [container evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40250142556/artifacts/12620034892) expire after seven days. CI captures do not establish a hosted deployment.

## Browser compatibility checkpoint — 2026-10-26

[Application run #69](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371000876), commit `deeb228109af43552b728e3be63140424744d377`, passed backend, frontend, PostgreSQL lifecycle and the full browser workflow on Chromium, Firefox and WebKit. The fixtures now select an explicitly allowed engine through `AEGISRISK_BROWSER`; each matrix job has an isolated runner and evidence artifact. Referrer behavior is asserted separately on every engine. The Chromium permissions-policy inspection is preserved and explicitly skipped on Firefox/WebKit because its inspection API is Chromium-specific; response-header checks still run in every job.

This verifies the covered preview, snapshot, report, model, keyboard, reflow, reduced-motion and error/recovery workflows in Playwright's Linux browser builds. It is not branded Safari, physical iOS, browser zoom, screen-reader or complete accessibility certification. The four visually inspected overview captures above remain the dated Chromium review; automated captures in other engines are not relabelled as a new manual visual review.

[Demo image run #5](https://github.com/animeshpthk07/AegisRisk/actions/runs/40371011459), commit `6611ec20fc941888419ac501c482d7d3054459d5`, also passed: 32 selected browser cases and four demo runtime cases, with startup restrictions, restart and fresh-container recovery. The selected cases are reused coverage, not 32 new distinct tests. The intervening change retains the separate referrer test in the demo selection; it does not change application behavior. Hosting remains deferred.

## Verified demo image — 2026-10-26

[Demo image run #3](https://github.com/animeshpthk07/AegisRisk/actions/runs/40322565275) built the non-root image and passed 31 reused browser cases plus four demo runtime cases. Tests exercised real JSON/HTML/PDF downloads, disabled saving, oversized-request rejection, shared request quotas, recovery, restart and a fresh-container seed under a 512 MB memory limit. The 31 cases are a subset of the existing 90, not additional distinct coverage. The candidate also passed all four jobs in application run #61. These results verify a CI container, not a hosting provider.

The first two image runs failed readiness because Nginx tried to create an unwritable FastCGI temporary directory. Commit `9b5715a` moved all remaining Nginx temporary paths under `/tmp`; the next run passed without relaxing restrictions or removing assertions. [Synthetic image evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40322565275/artifacts/12649986138) has seven-day retention.

## Public demonstration configuration

A first public demonstration should use only the fictional built-in portfolio and in-memory previews. It must keep snapshot saving disabled until the shared-user controls above exist.

1. Set `SYNTHETIC_IMPORTS_ENABLED=false` and verify that save and saved-dataset routes reject access. Do not copy the CI save override or disposable database credentials into a deployment.
2. Expose only the intended HTTPS web entry point. Keep the database and backend private where the provider supports it; document the actual network boundaries. Do not remove loopback restrictions merely to obtain a URL.
3. Configure request/body/time/concurrency limits and confirm response policies through the hosted web proxy. Reports must remain uncached. Use synthetic-only logs and do not log uploaded contents.
4. Record environment variable names, secret destinations, owner, spending limit, monitoring and rollback. Never commit secret values.
5. Smoke-test readiness, the 40-record seed, CSV/XLSX previews, a scoped scenario and JSON/HTML/PDF downloads at the actual URL. Verify save rejection, an error and recovery. Do not run destructive CI cleanup against a deployed database.
6. Capture the deployed commit, verification time, observed results and current screenshots. CI screenshots are test evidence, not proof of a live deployment.

A read-only public demonstration does not complete the authenticated workbench. Enabling shared persistence additionally requires identity, authorization, tenant separation, CSRF protections, quotas and a storage lifecycle.

## Remaining work order

1. Close concrete usability and security defects with focused regression checks.
2. Keep the verified demo image, provider configuration and cost/access proposal in GitHub; hosting remains deferred by owner decision.
3. Resume deployment only if the owner explicitly reopens it; then confirm current provider terms and any required account, spending or access approval, deploy and test the real URL.
4. Keep the published educational preview and its limitations accurate; create future releases only when their stated acceptance criteria pass.
5. Keep the saved project presentation current. Show the exact LinkedIn copy to the owner before publishing, as requested.

A Render Free proposal with a $0 budget is documented, but it is not activated. Provider/account, domain and operations ownership must be confirmed only if deployment is reopened. No hosting purchase or new security-sensitive access is authorized by this document. Synthetic model performance must remain labelled synthetic; it cannot be presented as bank validation or real-world hiring/credit-decision readiness.

## Release record template

- Version and full source commit:
- Successful verification run for that commit:
- Test totals and dated dependency audits:
- PDF visual review fixture/commit/date:
- Supported browsers and remaining accessibility issues:
- Security boundaries and unresolved issues:
- Provider, account owner, approved cost and environment configuration:
- Actual hosted URL, deployed commit and smoke-test results:
- Monitoring, backup/retention policy where applicable, and rollback procedure:
- Release notes, screenshots and presentation approval:

Leave unverified entries incomplete. Preserve failed workflow history and explain corrections rather than relabelling failed runs as successful.
