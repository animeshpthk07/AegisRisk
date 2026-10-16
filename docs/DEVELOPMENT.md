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

Covered flows: consent gating, built-in example at desktop/mobile viewport widths, CSV download, UTF-8 BOM upload, exact EAD/EL results, invalid probability without partial totals, unsupported/empty/oversized file rejection, proxy acknowledgement/content-type/size enforcement, and recovery after an intentionally simulated 503 response. Portfolio summary totals are compared before and after each test. Only the outage test injects a response; the other preview requests use the actual proxy/API.

To reproduce against a fresh, fictional-only local database, install the test dependency in the existing virtual environment:

```text
python -m pip install playwright==1.64.0
python -m playwright install chromium
```

Start the migrated/seeded API as above. Build the web application with `pnpm build`, then start it with `pnpm --dir apps/web exec next start --hostname 127.0.0.1 --port 3000`. With both services running, from the repository root:

```text
python -m pytest tests/browser -q --junitxml=test-results/browser.xml
```

The tests expect the untouched 40-record fictional seed. Do not point them at customer data or a production service. The CI job installs Linux browser dependencies with `python -m playwright install --with-deps chromium`. Screenshots, traces, JUnit results and server logs are kept in ignored `test-results/`; the CI artifact `browser-check-evidence` expires after seven days. Traces contain request data, so retain synthetic inputs only. Check the actual run result before calling the checkpoint verified.

This does not certify full accessibility, Firefox/WebKit compatibility, load capacity, production upload security, persisted imports or hosted deployment.

## Learn the foundation

1. Liveness asks whether the API responds; readiness asks whether the database and expected schema are accessible.
2. A migration versions database structure. The seed creates fictional example rows and refuses to overwrite existing data.
3. For PD 2%, LGD 45%, EAD INR 1,000,000, illustrative one-year EL is INR 9,000.
4. Portfolio EL sums facility losses. Multiplying separately averaged PD and LGD is not generally equivalent.
5. HHI aggregates by borrower before squaring exposure shares; multiple facilities must not disguise borrower concentration.
6. A stress multiplier demonstrates sensitivity. It is not evidence that a macroeconomic shock causes the chosen probability change.
