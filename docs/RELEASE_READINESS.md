# Release readiness

Updated 2026-10-26. This document defines the evidence needed for a release; it does not declare all five project phases complete.

## Current deliverable

AegisRisk is a public MIT educational workbench using fictional INR credit facilities. It includes bounded CSV/XLSX review, opt-in immutable snapshots, Decimal risk calculations, scenario sensitivity, JSON/HTML/PDF evidence exports and an isolated synthetic Model Lab. External AI is disabled. The latest verified application checkpoint is [run #50](https://github.com/animeshpthk07/AegisRisk/actions/runs/40250142556), commit `aa739a956e07504919cd33560933da834ca47f5e`.

A public repository and passing CI do not establish an authenticated hosted service. Shared-user authentication, operational controls and an actual deployed URL remain unfinished.

## Acceptance evidence

| Area | Evidence required | Current status |
| --- | --- | --- |
| Reproducible source | Frozen dependencies, lint, tests, production build and dependency audits pass for the exact release commit | Run #50 passed; rerun for the release candidate |
| Calculations and reports | Exact totals, dataset identity, scope/caps, errors, stale responses and real downloads tested | Implemented cases pass; see [CONTRACT.md](CONTRACT.md) |
| PDF layout | Rendered fixture pages reviewed for readable text, pagination and tables | All 13 pages reviewed for run #34 on 2026-10-24; review again after layout changes |
| Database lifecycle | Default save restriction, migrations, repeat seed, restart persistence and duplicate reuse checked | Isolated Compose/PostgreSQL checks pass |
| Browser usability | Keyboard operation, visible focus, labels, zoom/reflow and supported browser engines verified | Keyboard-only search/scenario/download at 1440/320px, both-theme reflow and reduced-motion checks pass; four overview captures reviewed. Screen-reader, zoom and Firefox/WebKit validation remain pending |
| Shared-user security | Identity/session handling, authorization/tenant separation, CSRF strategy, full CSP and resource limits reviewed and tested | Not complete; basic browser policy is verified, not a complete security review |
| Operations | Documented quotas, retention, backups/restore where storage is enabled, monitoring and rollback | Not complete |
| Hosted demo | Approved hosting account/cost, HTTPS URL and deployed-commit smoke evidence | No hosted application verified |
| Release and career materials | Accurate release notes, current screenshots, walkthrough and approved final public copy | Walkthrough exists; final release and LinkedIn launch pending |

Run #50 recorded 141 backend tests (one dependency deprecation warning), 19 frontend tests and 90 Chromium cases in each of two environments. Native browser tests passed in 104.15s and Compose/PostgreSQL browser tests in 105.66s. The two browser runs exercise the same cases and must not be counted as 180 distinct cases. Both dependency audits reported no known vulnerabilities at this checkpoint; these are dated checks. CI artifacts expire after seven days; preserve only synthetic release evidence needed for reproducibility.

## Usability checkpoint — 2026-10-26

The seven additional cases are saved in commit `86d72e1`; run #49 passed before the evidence-output change. Run #50 verifies the same application plus bounded UI-preview output (`aa739a9`). Keyboard checks use actual Tab/Enter/Space/arrow input through skip navigation, theme switching with visible focus, search, table scrolling, scenario calculation and a downloaded JSON report. Reflow checks retain internal table scrolling while rejecting document-wide horizontal overflow at 320 and 1440 CSS pixels in both themes. The reduced-motion preference disables animated document scrolling.

Four viewport captures from run #50 were inspected through its browser log: `ui-review-{1440,320}-{dark,light}.png`. The reviewed overview has readable text and controls with no overlap or page-wide clipping. This review covers those captured viewports, not every screen, screen-reader behaviour, browser zoom or all browser engines. The [browser evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40250142556/artifacts/12620203929) and [container evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40250142556/artifacts/12620034892) expire after seven days. CI captures do not establish a hosted deployment.

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
2. Prepare the selected provider's deployment configuration and an exact cost/access proposal.
3. Obtain any required account, spending or security-access approval for that concrete proposal; then deploy and test the real URL.
4. Record release evidence and remaining limitations; create a versioned release only when its stated acceptance criteria pass.
5. Prepare the final project presentation. Show the exact LinkedIn copy to the owner before publishing, as requested.

Provider/account, spending limit, domain and operations owner are deployment decisions still to be resolved. No hosting purchase or new security-sensitive access is authorized by this document. Synthetic model performance must remain labelled synthetic; it cannot be presented as bank validation or real-world hiring/credit-decision readiness.

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
