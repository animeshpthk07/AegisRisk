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

**Not yet the complete product:** no trained ML model, CSV/XLSX imports, PDF reports or verified public deployment. No real-world banking validation or regulatory compliance claims.

Read [development guide](docs/DEVELOPMENT.md), [architecture](docs/ARCHITECTURE.md), [security notes](docs/SECURITY.md), and [API contract](docs/CONTRACT.md). Verification results are recorded in the milestone tracker, not inferred from the existence of source files.
