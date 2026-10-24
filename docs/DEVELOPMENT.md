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

Migration/seed runs before API readiness; the web waits for API readiness. Persistent PostgreSQL volume is retained on ordinary shutdown. Do not delete volumes unless you intend to lose that local data. The container path passed the isolated GitHub browser/restart lifecycle in run #22 (see MILESTONES.md). A hosted deployment still requires its own configuration and verification.

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


## Inspect a scenario comparison report

Choose a portfolio, set the multipliers/scope in **Stress laboratory**, and calculate. Inspect the printed calculated assumptions, then download the scenario JSON. Confirm the outer and nested baseline dataset IDs/versions agree. Compare `scenario.inputs` with the printed assumptions and `scenario` totals with the displayed result. The baseline source fingerprint and input rows are nested under `baseline.source`.

For a saved fictional one-row CSV with PD 0.1, LGD 0.5 and EAD INR 1,000, choose PD ×2, LGD ×1 and EAD ×1. Baseline EL must be INR 50, stressed EL INR 100, delta INR 50 and fractional delta 1 (100%). The decimal evidence must reconcile to these values. Use all multipliers ×1 to reproduce baseline loss; zero baseline loss has a null percentage change.

Change an assumption before recalculating: the old result and its download button must disappear. A report request already in progress must not download after an assumption or portfolio change. Recalculate and retry to download the current result. Reports are read-only, synthetic-only sensitivities; they are not forecasts and do not save scenario history.

The same API/browser commands above cover scenario exports. Added checks include desktop/mobile demo and saved downloads, exact parity with the calculation endpoint, invalid inputs, scope/caps, single-load construction, dataset loader guards, zero/empty cases, proxy limits, failed/mismatched report retry, all four controls changing during calculation/export, and A → B/A → B → A portfolio switches. Delayed/error responses are explicit test fault injections; ordinary downloads use the production frontend, proxy and actual API.


## Verify values-only XLSX imports

The API install includes pinned openpyxl and defusedxml; no spreadsheet service or credentials are needed. Create a clean workbook with exactly the ten headers from CONTRACT.md in A1:J1, followed by fictional values only. Numeric PD 0.1, LGD 0.5 and EAD 1000 must produce INR 50 one-year EL. Save as XLSX, not XLS or XLSM.

The same test commands above generate real workbooks in memory. API checks cover numeric cells, formula/boolean/date/error cells, hidden content, multiple sheets, merges, hyperlinks, filters, archive/XML limits, invalid probabilities and duplicate IDs. Save checks require the raw workbook review digest, verify the normalized storage digest, and demonstrate metadata-only workbook changes require fresh review but reuse equivalent stored values. Desktop/mobile Chromium tests upload through the real proxy, review/save/reload, and parse baseline/scenario downloads. Formula/corrupt-file rejection and CSV retry are exercised separately.

No original workbook is retained on save. To reproduce normalized storage, read cells with formula expressions preserved for rejection (data_only=False), only after enforcing the strict archive contract, write CSV with LF line endings and hash those bytes. Do not treat cached formula values as validated numbers. The API is authoritative; browser accept filters are convenience only.


## Container lifecycle verification

The separate **PostgreSQL container lifecycle** CI job builds the repository's actual API and standalone web Dockerfiles and starts the Compose stack on an isolated GitHub runner. It first uses only the default compose.yaml and confirms that saving is blocked while synthetic preview and the 40-facility demo work. It then adds tests/containers/compose.yaml, which enables saving only for the disposable test environment, and runs the same complete Chromium suite against PostgreSQL.

After the browser suite, check_lifecycle.py saves one additional fictional portfolio and records the demo, saved baseline, scenario and catalog evidence. CI restarts PostgreSQL, re-runs migrations and the idempotent seed, restarts API/web, and compares every recorded field except report generation timestamps. A duplicate save must return the original UUID without changing the catalog. Both the baseline INR 50 and stressed INR 100 are asserted independently.

The job uses the explicit Compose project aegisrisk-container-ci and a public, test-only database password. Its final cleanup removes only that disposable runner project's containers and volume. It does not touch a developer's local volume or any deployed database. Do not copy the CI override or password into a public/shared deployment. The default Compose configuration remains unchanged.

Container status, logs, screenshots, traces, report downloads, JUnit results and the synthetic before-restart evidence are retained as container-check-evidence for seven days. Inspect the actual run before calling the container path verified. A passing runner check is not hosted-deployment, disaster-recovery, load, authentication or production-security certification.

## Print a self-contained evidence report

Download baseline or scenario **printable HTML**, open the saved file in a browser, then use Print and choose a physical printer or Save as PDF. The file contains local styles and escaped evidence, with no scripts or remote assets. This is a browser-print workflow, not a server-generated PDF service. Scenario reports still require a current calculation and matching assumptions. Desktop/mobile and print-style checks run in Chromium; confirm your own browser/printer's pagination before sharing.


## CI runtime maintenance

The workflow targets Ubuntu 24.04 explicitly for all four jobs, retaining Node.js 24 and Python 3.12. The GitHub-maintained checkout, setup-node, setup-python and upload-artifact actions use their documented v7 interfaces. Checkout does not persist a token into the working tree, setup-node automatic package-manager caching is explicitly disabled, and workflow permissions remain contents: read. No test, audit, artifact retention or failure check was removed.

Upgrade guidance: [checkout](https://github.com/actions/checkout), [setup-node](https://github.com/actions/setup-node), [setup-python](https://github.com/actions/setup-python), [upload-artifact](https://github.com/actions/upload-artifact). Re-check these official notes and run all jobs when changing major action or runner versions.

## Verify server-generated PDF reports

The PDF buttons are separate from the printable HTML workflow above. **Download baseline report (PDF)** exports the active baseline; after calculating current assumptions, **Download scenario report (PDF)** exports the comparison. Check dataset identity, exact decimal appendix values, INR/fraction/count labels, separate baseline/scenario limitations, repeated table headings and numbered page footers. Compare the evidence with the corresponding JSON report. Non-ASCII names appear as explicit Unicode escapes in the portable PDF; JSON retains original text.

The same backend and full-stack test commands above cover PDF parsing, output bounds, all 1,000 facility identifiers, literal labels, loader/input guards and read-only behavior. Browser checks cover real desktop/mobile demo and saved downloads, byte count/header/digest validation, retry and stale-response cancellation. Native and Compose runs execute the same browser cases.

For visual evidence, the backend CI job sets `AEGISRISK_PDF_EVIDENCE_DIR=test-results/pdf` while running tests. It retains the baseline, scenario and literal-label PDF fixtures, renders every page with Poppler at 90 dpi, and uploads `pdf-review-evidence` for seven days. The **Render synthetic PDF evidence for browser-only review** step also emits each rendered PNG as an `AEGISRISK_PDF_PREVIEW` line in the job log, so pages can be inspected through the browser without reading local files.

Review every generated page after a renderer/layout change. Text extraction can verify values and identifiers but cannot prove that tables are readable or unclipped. Record the exact commit/run, pages inspected and remaining limits in [MILESTONES.md](MILESTONES.md). The 24 October checkpoint reviewed 13 fixture pages; do not present that as universal layout, tagged-PDF accessibility or regulatory certification.

## Verify browser response protections

The full-stack suite checks response headers on the dashboard, readiness API, PDF export, rejected method and missing page. Chromium also inspects its effective device-permission policy and checks a real fetch omits the Referer header. No device is accessed and no permission prompt is requested. Existing import, scenario, model and download cases run under the same policy.

The configured CSP restricts framing, objects, base URLs and form destinations. It is not a complete script/style policy. See [SECURITY.md](SECURITY.md#browser-response-policy) for exact headers and the remaining deployment requirements. A passing native/Compose run does not verify a hosting provider or reverse proxy preserves those headers.
