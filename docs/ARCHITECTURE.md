# AegisRisk architecture

```mermaid
flowchart LR
    U[Analyst browser] --> W[Next.js / React dashboard]
    W --> P[Fixed allowlisted API proxy]
    P --> A[FastAPI / Pydantic]
    A --> V[CSV validator / bounded values-only XLSX decoder]
    V --> R[Decimal risk calculations]
    V --> S[Explicit review and local-only save gate]
    S --> D[(Immutable normalized snapshots)]
    A --> D
    A --> F[(Seeded fictional facilities)]
    D --> R
    F --> R
    R --> E[Deterministic narrative]
    R --> J[Baseline / scenario JSON evidence]
    J --> H[Escaped standalone printable HTML]
    J --> PDF[Bounded server-generated PDF]
    PDF --> Q[Browser identity, length and SHA-256 checks]
    Q --> U
    A --> L[Isolated synthetic Model Lab]
    G[Seeded fictional generator and disjoint data splits] --> L
    L --> C[Model card and fictional single-profile estimates]
    M[Alembic migrations + explicit synthetic seed] --> F
```

PostgreSQL is the deployment target. SQLite is an explicit local/test fallback, not a parity claim. CI checks PostgreSQL migration/read smoke and Chromium against a production Next.js build, real API and isolated fictional database. The real Compose images, all Chromium cases and database/application restart persistence passed the container job in [run #34](https://github.com/animeshpthk07/AegisRisk/actions/runs/40078175863). This is an isolated CI environment, not a verified public deployment.

## Decisions and boundaries

- Separate frontend/backend, versioned API, fixed proxy paths. No user-controlled upstream URL; bounded request streams and timeouts.
- Preview is read-only. CSV/XLSX share validation and calculations. XLSX archives/XML are checked before openpyxl, then only normalized values are retained if explicitly saved.
- Save is disabled by default. Enabling it is only for a local single-user synthetic demo; no accounts, tenant isolation, global storage quota or retention/deletion controls yet. Never upload customer information.
- Save revalidates raw bytes against the reviewed fingerprint. Stored content has its own integrity digest and immutable UUID. Equal stored bytes reuse a snapshot. Neither digest is an authenticity signature.
- Dataset selection is explicit. Invalid, unknown, disabled or corrupt saved data fails closed instead of falling back to the demo. Reload resets selection, not saved data.
- Seed/migrations are explicit; the seed never overwrites a nonempty portfolio. Scenario and report requests do not persist changes.
- Decimal expected-loss calculations supply all totals and deterministic explanations. JSON/chart numbers are presentation values; reports also carry decimal-string evidence and stated precision.
- Assumption edits/dataset switches invalidate pending calculations and downloads. Export checks bind scenario evidence to the visible calculation and selected dataset. PDF requests render the same single-load evidence, capped at 1,000 facilities and 4 MiB. The browser checks the PDF header, byte count and SHA-256, then rechecks stale request versions after asynchronous hashing. The digest is not an authenticity signature.
- ReportLab PDFs use escaped literal labels, built-in fonts and no external assets. A4 tables repeat headings and include page numbers; exact decimal evidence remains distinct from rounded headline values. Non-ASCII labels use explicit Unicode escapes, while JSON preserves original text. These PDFs are not tagged accessible or digitally signed.
- Portfolio PD/LGD remain assigned illustrative inputs, not model predictions. The separate synthetic Model Lab trains logistic regression on 1,800 fictional rows, calibrates on 600 different rows and reports metrics on 600 held-out rows. It never writes portfolio data or replaces report PDs. See [MODEL_LAB.md](MODEL_LAB.md).
- Model training/scaling excludes calibration and test rows; calibration excludes test rows. The in-process model is cached behind a lock and recreated from a fixed recipe after restart; no uploaded model or pickle is loaded. Runtime numerical-library versions are disclosed.
- Model inputs require explicit synthetic consent, strict bounded numeric values, no extra fields/query parameters and a 4 KiB JSON request limit. Input/consent changes cancel pending estimates and clear prior results.
- No external AI or API key. Portfolio calculations use one currency (INR) and a one-year horizon. Model estimates are fictional event probabilities, not validated borrower PDs or lending decisions.
- pnpm lockfile pins frontend resolution. XLSX parser packages are exactly pinned; remaining Python dependencies are bounded and audited in CI, not yet fully locked.
- Next.js follows the requested stack. No Sites registration or publication.

## Remaining product work

The synthetic model/calibration slice and JSON, printable HTML and server-generated PDF reports are implemented and covered by the verified checkpoints. Real-world model validation, authentication and production security, verified hosting and final career presentation remain unfinished. Read [milestones](MILESTONES.md) for exact verified commits: source presence is not test evidence.

The risk engine loads bounded fictional datasets in memory. Larger real portfolios would require database-side aggregation, pagination, tenancy, access controls and independent domain validation. Readiness checks schema presence, not an expected facility count; an empty portfolio is valid and disclosed.
