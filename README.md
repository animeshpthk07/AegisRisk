# AegisRisk

Banking risk intelligence and explainable credit analytics. Educational portfolio project; synthetic data only. Not a credit approval system and not affiliated with a bank or regulator.

**Mathematics calculates. Models estimate. AI explains. Humans decide.**

Implementation is in progress. See [milestones](docs/MILESTONES.md) for verified status. External AI is disabled by decision; no API key is needed. The foundation source is published on [GitHub](https://github.com/animeshpthk07/AegisRisk) under the MIT license. A public hosted application is not yet verified.

## Current foundation scope

- Next.js / React / TypeScript dashboard with accessible tables, Recharts, dark/light themes and error states.
- FastAPI versioned API, SQLAlchemy facilities, Alembic migrations and explicit fictional seed.
- Facility/portfolio expected loss, EAD-weighted metrics, borrower HHI, industry exposures and bounded scenario sensitivity.
- Deterministic narrative derived from backend totals, not an LLM.
- PostgreSQL Docker Compose configuration, local SQLite verification fallback, tests and CI definition.
- Bounded synthetic CSV preview: file validation, row-level issues and independently calculated totals, without saving or replacing the active portfolio.
- Opt-in reviewed CSV snapshots: immutable saved portfolios, duplicate-file reuse, dataset selection and dataset-scoped calculations. Saving is disabled by default.

**Not yet the complete product:** no trained ML model, XLSX imports, PDF reports, authentication or verified public deployment. No real-world banking validation or regulatory compliance claims.

Read [development guide](docs/DEVELOPMENT.md), [architecture](docs/ARCHITECTURE.md), [security notes](docs/SECURITY.md), and [API contract](docs/CONTRACT.md). Verification results are recorded in the milestone tracker, not inferred from the existence of source files.

## Verified foundation checkpoint

[GitHub verification run #1](https://github.com/animeshpthk07/AegisRisk/actions/runs/38502931162) passed on 14 October 2026: backend tests/lint, PostgreSQL migration/read smoke, frontend typecheck/tests/build, and dependency-audit steps. See the milestone tracker for scope and limitations.

## Local demo preview

![AegisRisk foundation dashboard using fictional portfolio data](docs/foundation-preview.jpg)

This image is from the earlier locally verified foundation demo, not a hosted production release.

## Synthetic CSV preview checkpoint

[GitHub verification run #5](https://github.com/animeshpthk07/AegisRisk/actions/runs/38730979855) passed on 15 October 2026 for commit `f0c0caf`: backend and frontend checks completed successfully.

In the dashboard, open **CSV preview**, choose **Use fictional example**, confirm synthetic-only data, then select **Validate and preview**. The two-row example should report INR 3,000 EAD and INR 66 one-year expected loss. A download link provides the example CSV. Invalid files show record/field errors and no partial totals.

The preview supports UTF-8 CSV up to 256 KiB / 1,000 rows. It is independent of the database portfolio, uses no external AI, and never saves uploaded data. See the [validation contract](docs/CONTRACT.md). [Full-stack verification run #8](https://github.com/animeshpthk07/AegisRisk/actions/runs/38855476887) passed on 16 October 2026 for commit `5e8ce09`: backend, frontend and Chromium browser jobs succeeded. The browser checks exercise the production Next.js app, real API and isolated fictional database, including desktop/mobile examples, uploads, rejection paths and retry recovery. Synthetic-only screenshots, traces and results are retained as a seven-day CI artifact. See the [reproduction guide](docs/DEVELOPMENT.md#full-stack-browser-verification).

That historical run verifies the CSV-preview slice only, not the later snapshot feature, full accessibility, other browser engines, production security or a public deployment.

## Reviewed saved portfolios

The snapshot workflow is implemented in commit `09e0156`; its [verification run #11](https://github.com/animeshpthk07/AegisRisk/actions/runs/38981748695) must be checked for the latest result.

On a local, single-user instance, explicitly set `SYNTHETIC_IMPORTS_ENABLED=true` on the API process after applying migrations. Keep it disabled on shared or public instances: this feature has no authentication, tenant isolation, retention policy or total storage quota.

1. Validate a fictional CSV and inspect its totals.
2. Enter a name, confirm that you reviewed the totals, then choose **Save reviewed portfolio**.
3. Choose **Open saved portfolio**. The portfolio, facilities, explanation and stress calculations use that snapshot together.
4. Use **Active portfolio** to return to the built-in demo or another saved file. Reload returns the selection to the demo, but saved files remain available in the catalog.

Previewing does not save. Saving does not switch datasets or overwrite the demo. Exact duplicate file bytes reuse the original snapshot and name. The server revalidates every save and checks the preview digest; errors never silently fall back to the demo. Only synthetic data is supported.
