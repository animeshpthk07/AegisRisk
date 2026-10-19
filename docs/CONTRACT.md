# Initial integration contract

API prefix `/api/v1`; backend localhost:8000, frontend localhost:3000. Frontend server proxies fixed API paths through Next.js route handlers; no browser CORS needed. PostgreSQL deployment target; explicit SQLite fallback for local verification only. All demo data fictional, INR, one-year PD horizon.

- GET `/api/v1/health`: `{status:"ok", service:"aegisrisk-api", version:"0.1.0", external_ai:false}` liveness; no DB claim.
- GET `/api/v1/ready`: `{status:"ok", database:"connected"}` or safe 503.
- GET `/api/v1/portfolio`: `{dataset_id,dataset_version,currency:"INR",horizon:"one_year",synthetic:true,facilities:[{id,borrower,industry,geography,rating,pd,lgd,ead,expected_loss}],summary:{facility_count,total_ead,total_expected_loss,weighted_pd,weighted_lgd,borrower_hhi},segments:[{industry,ead,expected_loss,share}],warnings:string[]}`.
- GET `/api/v1/facilities?q=&industry=&offset=0&limit=25`: `{items,total,offset,limit}`.
- POST `/api/v1/stress`: JSON `{pd_multiplier:1.5,lgd_multiplier:1.1,ead_multiplier:1,industry:null}` returns `{baseline_el,stressed_el,delta_el,delta_pct,assumptions:string[]}`; reject nonfinite/out-of-range, cap stressed PD/LGD to1.
- GET `/api/v1/explanation`: `{mode:"deterministic",text,disclaimer}` derived from current portfolio.

All displayed portfolio values must come from the backend. No fake model metrics, no claim of full product readiness. Module placeholders should not look completed.

## Synthetic CSV / XLSX preview (not a persisted import)

POST `/api/v1/import-preview` with a raw UTF-8 CSV body (`Content-Type: text/csv`) or a values-only XLSX body (`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`), and `X-AegisRisk-Synthetic: true`. No database access or external AI calls. The acknowledgement is a user assertion, not proof that data is synthetic; never upload customer information.

Required headers (any order, exact spelling, no extra/duplicate columns):

`id,borrower,industry,geography,rating,pd,lgd,ead,currency,horizon`

Example fictional record:

`SYN-CSV-001,Fictional Orchard,Energy,West,B,0.1,0.5,1000.00,INR,one_year`

Limits: 256 KiB encoded file; 1,000 nonblank data records; UTF-8 BOM accepted. CSV quoting is supported. Fully empty lines are ignored; empty records are rejected. Text is trimmed, printable and nonempty; formula-like prefixes (= + - @) are rejected. Field lengths match the facility model. IDs use ASCII letters/digits/hyphens/underscores, start with a letter or digit, and must be unique within the file (case-insensitive). Borrower HHI groups exact trimmed borrower labels; use a consistent name for one borrower.

PD/LGD are decimal fractions from 0 to 1, at most 10 decimal places, not percentages. EAD is INR from 0 to 1,000,000,000,000 with at most 2 decimal places. Signs, exponents, thousands separators, NaN and infinity are rejected. Currency must be INR and horizon one_year on every row. No automatic conversions or rounding of inputs.

Valid response (200): `{valid:true,persisted:false,digest,storage_digest,source_format,synthetic_acknowledged:true,currency,horizon,row_count,valid_rows,invalid_rows:0,issue_count:0,issues:[],issues_truncated:false,summary,warnings}`. Summary uses the existing Decimal risk calculations with JSON numbers for presentation. Example EL is INR 50. Zero total EAD returns null weighted ratios and HHI.

Invalid row response (422): same envelope with `valid:false,summary:null` and `issues:[{row,column,code,message}]`. Row means CSV record number, including the header as record 1. At most 100 issues are returned; issue_count records the total. No partial-file summary is calculated. Raw uploaded values are not echoed. Structural/encoding/header errors use `{detail}` (422); missing acknowledgement 400; wrong content type 415; byte/row limits 413.

This previews the uploaded file in isolation. It does not check IDs against existing database facilities, merge, save, replace, or affect the active portfolio. Authentication and production upload abuse controls remain future work. Persisting a reviewed CSV or XLSX uses the separate opt-in endpoint below. Do not expose an unauthenticated demo as a customer-data service.

## Reviewed synthetic snapshots (disabled by default)

The API process must explicitly opt in with `SYNTHETIC_IMPORTS_ENABLED=true`. This is a local single-user demonstration feature, not permission to expose uploads publicly. There is no authentication, tenant separation, aggregate storage quota or retention/deletion interface. All saved content must be fictional.

- GET `/api/v1/saved-portfolios?offset=0&limit=50`: `{enabled,items:[{id,name,digest,row_count,created_at}],total,offset,limit}`. Offset is nonnegative; limit is 1–100. Disabled instances return an empty disabled catalog. Raw CSV text is not returned by this listing.
- POST `/api/v1/saved-portfolios?name=...`: raw CSV or XLSX with the matching content type above, `X-AegisRisk-Synthetic: true`, `X-AegisRisk-Reviewed: true`, and `X-AegisRisk-Preview-Digest` equal to the preview's lowercase SHA-256 digest of the original file bytes. Names are trimmed, printable, nonempty, at most 80 characters and cannot begin with formula-like prefixes.
- The server revalidates the entire file, then compares its original-byte digest. A valid new snapshot returns 201: `{persisted:true,created:true,portfolio:{id,name,digest,row_count,created_at}}`. Identical stored bytes return 200 with `created:false` and the original metadata/name. No merge, overwrite or partial save occurs.
- Errors: disabled saving 403; missing review/synthetic acknowledgement 400; wrong content type 415; byte/row limits 413; invalid name/CSV/XLSX 422; stale preview digest 409; storage failure 503 with a generic message. Validation failures never create a partial snapshot.
- GET portfolio, facilities and explanation, plus POST stress, accept `dataset_id=<UUID>`. Omit it to use the seeded demo. A malformed UUID is 422, an unknown ID 404, disabled saved access 403, and a corrupt snapshot 503. None silently fall back to the demo. A selected portfolio reports its ID and `saved-v1:<UUID>` version; the demo reports a null ID.

The browser proxies only fixed resource paths. Preview/save requests are byte-bounded and require the acknowledgement headers; the backend remains authoritative. Saving leaves the current selection unchanged. Opening a saved portfolio is explicit. Dataset switches clear the previous note/scenario and invalidate in-flight responses; reload returns to the demo while preserving saved records. The UI prints rounded currency for presentation; backend Decimal calculations remain the source of truth.


## Baseline evidence report (JSON)

GET `/api/v1/report` accepts the same optional `dataset_id=<UUID>` and loader guards as portfolio. The UI uses `/api/report`. It reads the selected dataset once and does not write to storage, call an AI provider, or include the current browser stress scenario.

Schema `aegisrisk.baseline-report.v1` includes UTC `generated_at`, `report_kind: baseline_only`, `scenario_included: false`, all portfolio fields, the deterministic explanation and disclaimers, plus:

- `source.input_rows`: identity/categorical fields and PD, LGD, EAD as normalized plain decimal strings. Rows are sorted by case-sensitive unique ID.
- `source.canonical_sha256`: SHA-256 of those input rows serialized with sorted JSON keys, compact separators, ASCII escapes and UTF-8 encoding. Equivalent numeric spellings and row order yield the same fingerprint. This is NOT the original CSV-byte digest, a signature, or independent proof of authenticity.
- `calculation`: formula, probability units, Decimal precision/rounding, decimal-computed total EAD/EL and facility EL strings, and explicit limitations. Calculations reuse the application's Decimal arithmetic (normally 28 significant digits, ROUND_HALF_EVEN); multiply PD then LGD then EAD. Arithmetic may round to that precision. JSON summary numbers are display values, not lossless decimal encodings.

For unchanged inputs, only generation time should vary. The report is a baseline educational snapshot, not IFRS 9 ECL, capital estimation, an audit opinion, or a lending decision. Currency remains INR and horizon one year. Empty/zero-EAD datasets retain null ratios. Responses use no-store/nosniff headers. The filename uses only a fixed prefix and the dataset UUID or demo token.

The browser validates report schema/dataset identity before offering a download. A dataset switch aborts and invalidates pending exports, including A → B → A changes; failures never reuse a previously downloaded report. Catalog refresh preserves the active ID even when it is outside the visible catalog page. Formatted PDF/CSV reports and scenario exports are not implemented by this endpoint.


## Scenario comparison report (JSON)

POST `/api/v1/scenario-report` (browser proxy: `/api/scenario-report`) accepts the same JSON inputs, finite 0–10 multiplier limits, scope validation and optional dataset UUID as POST stress. Defaults are PD ×1.5, LGD ×1.1 and EAD ×1 across the whole portfolio. Unknown fields and invalid scopes are rejected. The proxy caps this JSON request at 4 KiB and does not allow GET for this resource.

Schema `aegisrisk.scenario-report.v1` has `report_kind: baseline_and_scenario`, `scenario_included: true`, UTC generation time, dataset ID/version, synthetic flag, currency and horizon. It contains:

- `baseline`: the complete baseline report envelope above, clearly labeled baseline-only. Its dataset identity and timestamp match the outer report.
- `scenario`: the same baseline/stressed EL, absolute delta, fractional delta percentage and limitations produced by POST stress. Both endpoints use one shared calculation helper.
- `scenario.inputs`: the validated multipliers and selected industry (null means whole portfolio). These are user assumptions, not forecasts or trained estimates.
- `scenario.calculation`: precision/rounding context, decimal-string baseline/stressed/delta totals, nullable fractional delta, affected-facility count and sorted per-facility evidence. Each facility records whether it was affected, PD/LGD cap flags, stressed PD/LGD/EAD, baseline/stressed EL and delta EL. Unselected rows remain unchanged; stressed PD/LGD never exceed 1.

The selected portfolio is loaded once for both sections. No scenario is persisted and no external AI runs. Saved-dataset disabled/unknown/corrupt guards remain enforced. Zero baseline EL gives null percentage change, not infinity. Empty portfolios give empty evidence and zero absolute totals. Decimal arithmetic uses the stated context, so evidence is reproducible but not a claim of unlimited precision.

The browser binds export to the last successful calculation and its submitted assumptions. Every assumption edit invalidates the displayed result and cancels calculation/export requests, even if a control later returns to its previous value. Portfolio switches do the same. Before downloading, the browser checks outer/nested dataset identity, report schema, echoed input values and all four result numbers against that calculation. Mismatches and failed requests produce no download and allow retry. The filename is `aegisrisk-scenario-<UUID or demo>.json`.

This is an educational sensitivity comparison, not a macroeconomic forecast, IFRS 9 result, regulatory-capital estimate, audit opinion or lending recommendation. Formatted reports, scenario persistence and production deployment remain outside this feature.


## Values-only XLSX safety and storage

XLSX uses the same ten columns, row validator and Decimal calculations as CSV. It must contain exactly one visible worksheet with its header in row 1 and all populated cells inside A1:J1001. Only text and finite numeric values are supported. Numbers are converted to plain decimals, never rounded to satisfy validation. Boolean, date, error and formula cells are rejected; formulas are never calculated and cached formula values are never trusted.

Rejected content includes hidden rows/columns/sheets, merged cells, defined names, filters, hyperlinks, external relationships, macros and embedded binary objects. XLS and XLSM are unsupported. These strict limits intentionally reject many ordinary workbooks: prepare a clean values-only sheet, not a complex model.

The compressed upload is capped at 256 KiB. Before openpyxl reads it, every ZIP member is checked: at most 64 entries, 4 MiB total expanded bytes, 2 MiB per member and 100:1 maximum compression ratio. Only stored/deflated XML/relationship entries are allowed. Duplicate names, unsafe paths and encrypted entries are rejected. XML is parsed with DTDs, entities and external references forbidden. Physical cell coordinates are bounded independently of worksheet dimensions. Malformed archives return 422; size/coordinate limits return 413. This is defense in depth for a local fictional-data demo, not a production security certification.

Preview adds `source_format: csv | xlsx` and two SHA-256 fingerprints:

- `digest` binds review to the exact uploaded bytes. The save header must match this original-byte digest; workbook metadata edits require fresh review.
- `storage_digest` identifies the stored bytes. CSV bytes are preserved; XLSX is normalized to UTF-8 CSV values with LF record endings. Workbook formatting and the original archive are not retained.

Saved metadata's `digest` is the storage digest and is checked again when loading a snapshot. Workbooks with identical normalized values reuse the existing snapshot/name even if workbook metadata differs. This is byte-normalized deduplication, not arbitrary semantic equivalence: different row order or numeric spelling may still create distinct snapshots. The baseline report's canonical-input fingerprint is a third, separate digest with the semantics documented above.
