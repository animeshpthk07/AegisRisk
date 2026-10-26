# Fictional public-demo deployment

Prepared and image-verified 2026-10-26. The owner chose to keep AegisRisk on GitHub for now. Hosting is intentionally deferred; no service was created. This is a reproducible package and retained proposal, not evidence of a live service. See [release readiness](RELEASE_READINESS.md) for the unfinished authenticated workbench.

## Proposed hosting and cost boundary

If the owner explicitly resumes deployment, the retained proposal is one **Render Free web service**, named `aegisrisk-demo`, in Frankfurt, from this public GitHub repository. The [Blueprint](../render.yaml) selects Docker, the Free compute plan, a managed HTTPS endpoint, `/healthz` readiness and manual deployments. No database service, persistent disk, GPU, external AI, custom domain or paid upgrade is requested.

Official [pricing](https://render.com/pricing) lists the Free web service at $0/month with 512 MB RAM. The [Free limits](https://render.com/docs/free), checked on the date above, include idle shutdown after 15 minutes, cold starts, ephemeral files and 750 shared instance hours per workspace per month. Hobby usage currently includes 5 GB outbound bandwidth and 500 standard build minutes per month. Recheck the account's actual included usage before applying.

**Free compute is not an unconditional zero-bill guarantee.** A workspace with a payment method can incur bandwidth/build overages. Proposed spending authorization is **$0**, with no payment method added, no paid plan and no overages accepted. The provider documents suspension/build blocking when a payment method is absent and included allowances are exhausted. If account verification requires a card, or an existing billing setup can incur overages, stop for an explicit owner decision. Do not treat a pipeline spend limit as a universal bandwidth cap.

The account owner must approve the actual Render account, the public fictional-data endpoint and any sign-up terms or GitHub access request before deployment. Prefer the public repository URL where supported; do not grant access to unrelated repositories. The application itself needs no API key, database password or other runtime secret. Source publication here does not create a hosting account or service.

## Package and network boundaries

- [Dockerfile](../deploy/demo/Dockerfile): frozen frontend build plus the existing backend, non-root UID 1000 and a health check. Build context is the repository root.
- [Startup](../deploy/demo/start.sh): migrations and the deterministic 40-facility seed, fixed ephemeral SQLite, disabled saving, loopback application listeners and coordinated shutdown. Startup rejects an attempt to enable imports. Environment variables cannot redirect this image to an external database.
- [Proxy](../deploy/demo/nginx.conf): only the configured public port listens externally. Next.js is bound to 127.0.0.1:3000 and FastAPI to 127.0.0.1:8000 inside the same container. Render terminates HTTPS before the container's HTTP port. The database is a local file and has no network listener.
- [Image verification](../.github/workflows/demo.yml): builds and starts the real image with 512 MB memory, one CPU, 128 PIDs, dropped capabilities and no privilege escalation. This validates those test constraints; it does not promise identical provider CPU capacity or high-traffic performance.

The original PostgreSQL Compose configuration remains for isolated development. Do not expose its loopback-only database/API ports or copy its CI override into hosting.

## Limits, logging and persistence

The transport accepts at most 512 KiB per request; application CSV/XLSX limits remain 256 KiB and 1,000 records. Request bodies within the transport limit are buffered in memory. API requests share a 10 requests/second budget with a 40-request burst and at most eight concurrent requests. This is a single-instance aggregate limit, not a per-user allowance. Client-supplied forwarding headers do not allocate new buckets. It cannot replace provider DDoS protection, identity controls or a distributed quota service.

Header/body read timeouts are 15 seconds. Proxy connect timeout is five seconds, and proxy read/send and client send timeouts are 30 seconds. Limits return bounded errors; busy responses include a retry hint. Reports preserve the application's no-store policy. The public health check goes through Next.js to the backend/database.

Nginx access logging and Uvicorn access logging are disabled. Application/startup errors still reach provider logs; only fictional inputs are permitted. Do not add uploaded contents, request bodies, credentials or borrower documents to logs. Review provider log retention and account access before launch. CI's synthetic evidence expires after seven days.

There is no uploaded-portfolio persistence and no user account/session store in this demo. The built-in SQLite seed is disposable and recreated after loss of the container filesystem; no database backup is required for this fictional-only configuration. Reports downloaded by a visitor remain in that visitor's browser/downloads. Real financial documents are outside this deployment's scope.

## Verification gate

Before applying the proposal, require a successful **Public demo image verification** run and the normal **AegisRisk verification** checks for the candidate application source. The image checks include:

1. Rejection of persistent-import configuration and privileged public ports.
2. Actual disabled-save responses plus valid fictional previews and the 40-record seed.
3. CSV/XLSX validation, Model Lab, keyboard workflows, reflow, reduced motion and response policy tests against the container's public proxy.
4. Real browser downloads of baseline/scenario JSON, printable HTML and PDF reports.
5. Oversized requests, shared burst limiting and successful recovery.
6. Restart and fresh-container reseeding while saving stays disabled.

These checks run only against a disposable local CI container. Never point the burst test, destructive container cleanup or reseed test at a hosted service. A green image check is not deployed-URL evidence.

## Apply and observe after owner approval

1. Confirm the owner/account, $0 billing conditions, Free compute, region and public scope in the actual hosting UI. Accept account terms only with the owner's required approval.
2. Review the [Blueprint fields](https://render.com/docs/blueprint-spec) or enter the equivalent web-service settings. Use `deploy/demo/Dockerfile` with repository-root context, port 10000 and health path `/healthz`. Keep auto-deploy off so future commits do not silently change the published demo.
3. Deploy the exact verified commit manually. Record the full SHA, service identity, HTTPS URL and deployment time. Do not infer the live SHA from the current main branch.
4. At the real URL, check readiness, 40 facilities and INR 2,769,125 baseline expected loss; preview the fictional CSV and a values-only XLSX; calculate a scoped scenario; download JSON/HTML/PDF; verify disabled saving and a harmless invalid-file error followed by successful retry.
5. Inspect desktop/mobile layouts in both themes. Record actual hosted screenshots separately from CI captures. Do not run the burst test against the provider.
6. Review service memory/CPU, readiness failures, restart history and included usage. Investigate repeated 429/503 errors; do not silently raise limits or move to paid resources. Cold starts are expected on the free plan and must be disclosed beside the demo link.

## Operations and rollback

The repository owner remains responsible for the hosting account and usage review; a different operations owner must be explicitly recorded. Provider health checks supervise the process. No external uptime monitor, keep-alive traffic, subscription or notification destination is configured by this package.

For a faulty deployment, use Render's available rollback to a previously verified build, or manually redeploy its recorded commit if the old build is no longer retained. Free-service rollback retention is limited; verify availability in the dashboard. Re-run the harmless live smoke checks and record the actual recovered SHA. If safe operation or $0 billing cannot be maintained, suspend the demo. The dataset is recreated from source, so recovery does not require preserving user uploads.

## Release record — GitHub only

- Owner decision, 2026-10-26: keep the project on GitHub for now; hosting deferred.
- Verified candidate: `9b5715a0626f6e4a94e52fdabf7904dc117627ec`.
- [Public demo image run #3](https://github.com/animeshpthk07/AegisRisk/actions/runs/40322565275): passed; 31 reused browser cases and four demo runtime cases, plus startup guards, restart and fresh-container checks.
- [Application run #61](https://github.com/animeshpthk07/AegisRisk/actions/runs/40322565203): all four jobs passed for the same candidate.
- [Synthetic demo evidence](https://github.com/animeshpthk07/AegisRisk/actions/runs/40322565275/artifacts/12649986138): seven-day retention.
- Initial image failures: non-root Nginx could not create `/var/lib/nginx/fastcgi`; all remaining temporary paths were moved under `/tmp`, after which run #3 passed.
- Account, billed-plan/payment-method review, hosted URL, live smoke, screenshots and hosted operations: deferred; not performed or claimed.

Recheck provider terms, billing and the candidate checks if the owner reopens deployment. Do not create a hosting account or service from this retained proposal alone.

This public fictional demo does not complete authentication, authorization/tenant separation, shared persistence, CSRF strategy, a full script/style CSP, screen-reader testing or real-world model validation. Keep those gaps visible rather than relabelling this package as the complete five-phase product.
