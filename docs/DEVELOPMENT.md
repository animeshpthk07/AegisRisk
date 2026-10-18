# Local development

Requirements: Node.js 24, pnpm 11.25.0, Python 3.12. Docker with Compose is optional for the PostgreSQL path.

## Native local demo (SQLite verification fallback)

From repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e './apps/api[dev]'
pnpm install --frozen-lockfile
```

In a backend terminal:

```powershell
cd apps/api
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m aegisrisk.seed
..\..\.venv\Scripts\python.exe -m uvicorn aegisrisk.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, repository root:

```powershell
pnpm dev
```

Open http://127.0.0.1:3000. FastAPI schema docs: http://127.0.0.1:8000/docs. Readiness: http://127.0.0.1:8000/api/v1/ready.

Unix uses `.venv/bin/python`. `DATABASE_URL` overrides the SQLite default. For native frontend the backend URL defaults to loopback; set `API_BASE_URL` in the frontend server environment if needed. No dotenv loader is installed in the backend; export its variables explicitly. `.env.example` is for Compose substitution, not automatic Python configuration.

## PostgreSQL through Docker Compose

Copy `.env.example` to an ignored `.env` locally and replace its demonstration password (URL-encode special characters in database URLs). Then:

```text
docker compose up --build
```

Migration/seed runs before API readiness; the web waits for API readiness. Persistent PostgreSQL volume is retained on ordinary shutdown. Do not delete volumes unless you intend to lose that local data. These container instructions must be tested before claiming deployment readiness.

## Checks

```text
python -m pytest apps/api/tests -q
python -m ruff check apps/api
python -m pip_audit --skip-editable
pnpm typecheck
pnpm test
pnpm build
pnpm audit --prod
```

Use the virtual environment's Python. GitHub Actions is configured in the public repository. Check the latest run and job logs before relying on it; a YAML file is not evidence of successful CI.

## Full-stack browser verification

The GitHub Actions **Full-stack browser checks** job builds the production Next.js app, migrates and seeds an isolated SQLite database with 40 fictional facilities, starts the real FastAPI and web servers on loopback, and runs `tests/browser/test_csv_preview.py` in Chromium. This is separate from the PostgreSQL migration smoke and backend unit tests.

Covered flows: consent gating, built-in example at desktop/mobile viewport widths, CSV download, UTF-8 BOM upload, exact EAD/EL results, invalid probability without partial totals, unsupported/empty/oversized file rejection, proxy acknowledgement/content-type/size enforcement, and recovery after an intentionally simulated 503 response. Portfolio summary totals are compared before and after each test. The outage, disabled-capability and delayed-response tests deliberately inject responses. Ordinary preview and snapshot round-trip requests use the actual proxy/API. Snapshot checks cover reviewed saving, duplicate-byte reuse, reopen after reload, confirmation invalidation and switching away from an in-flight scenario. Report checks download and parse actual JSON for the demo and a saved snapshot; simulated failures verify no download on outage or mismatched identity. Delayed responses cover A → B and A → B → A selection changes. Catalog refresh tests preserve a selected snapshot outside the current listing page.

To reproduce against a fresh, fictional-only local database, install the test dependency in the existing virtual environment:

```text
python -m pip install playwright==1.64.0
python -m playwright install chromium
```

For this isolated test run, set `SYNTHETIC_IMPORTS_ENABLED=true` on the API process, then start the migrated/seeded API as above. Build the web application with `pnpm build`, then start it with `pnpm --dir apps/web exec next start --hostname 127.0.0.1 --port 3000`. With both services running, from the repository root:

```text
python -m ruff check --select E,F,I tests/browser
python -m pytest tests/browser -q --junitxml=test-results/browser.xml
```

The tests expect the untouched 40-record fictional seed. Do not point them at customer data or a production service. The CI job installs Linux browser dependencies with `python -m playwright install --with-deps chromium`. Screenshots, traces, JUnit results and server logs are kept in ignored `test-results/`; the CI artifact `browser-check-evidence` expires after seven days. Traces contain request data, so retain synthetic inputs only. Check the actual run result before calling the checkpoint verified.

This does not certify full accessibility, Firefox/WebKit compatibility, load capacity, production upload security, multi-user storage or hosted deployment.

## Learn the foundation

1. Liveness asks whether the API responds; readiness asks whether the database and expected schema are accessible.
2. A migration versions database structure. The seed creates fictional example rows and refuses to overwrite existing data.
3. For PD 2%, LGD 45%, EAD INR 1,000,000, illustrative one-year EL is INR 9,000.
4. Portfolio EL sums facility losses. Multiplying separately averaged PD and LGD is not generally equivalent.
5. HHI aggregates by borrower before squaring exposure shares; multiple facilities must not disguise borrower concentration.
6. A stress multiplier demonstrates sensitivity. It is not evidence that a macroeconomic shock causes the chosen probability change.

## Opt-in synthetic saved portfolios

Apply `alembic upgrade head` before starting the API; migration `0002` adds a separate snapshot table without replacing seeded facilities. The default is read-only preview. For a local, single-user fictional-data session only, enable saving in the backend terminal before starting the API:

```powershell
$env:SYNTHETIC_IMPORTS_ENABLED = 'true'
```

On Unix, use `export SYNTHETIC_IMPORTS_ENABLED=true`. The frontend discovers the capability from the API; no frontend secret or external AI service is needed. Disabling this flag prevents saving and access to saved portfolios but does not delete their stored data. The built-in demo and preview remain available.

Use the UI to preview, review, save and explicitly open a snapshot. Reload resets the active selection to the demo; use the saved catalog to reopen. Byte-identical retries reuse the original record and name. A save that times out is not necessarily absent: retry the same file to resolve the outcome without duplicates.

Do not enable this flag on public/shared deployments. Authentication, authorization, tenant isolation, aggregate storage quotas and retention/deletion controls are not implemented. The per-file 256 KiB and 1,000-row limits are not a total storage budget. This milestone is not a production ingestion service.


## Inspect a baseline report

In the dashboard, choose **Active portfolio**, then **Download baseline report (JSON)**. Open the downloaded JSON in a text editor. Verify `dataset_id` and `dataset_version`, the synthetic/INR/one-year labels, summary totals, source input rows and decimal computation evidence. A saved snapshot uses its UUID; the built-in demo uses a null ID and `demo-v1`.

The report deliberately excludes the currently configured or calculated stress scenario. It does not persist reports or transmit them to an AI provider. The source fingerprint is a reproducibility aid, not a signature or audit certification. Decimal precision and rounding are recorded alongside the calculations. See [CONTRACT.md](CONTRACT.md#baseline-evidence-report-json).

The baseline report test set runs through the same commands above. API tests also cover one-load construction, repeatability excluding generation time, canonical row ordering/numeric spelling, zero exposure, an empty demo, unknown IDs, disabled saved access and corrupt snapshots.
