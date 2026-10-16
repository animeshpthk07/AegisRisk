# Initial integration contract

API prefix `/api/v1`; backend localhost:8000, frontend localhost:3000. Frontend server proxies fixed API paths through Next.js route handlers; no browser CORS needed. PostgreSQL deployment target; explicit SQLite fallback for local verification only. All demo data fictional, INR, one-year PD horizon.

- GET `/api/v1/health`: `{status:"ok", service:"aegisrisk-api", version:"0.1.0", external_ai:false}` liveness; no DB claim.
- GET `/api/v1/ready`: `{status:"ok", database:"connected"}` or safe 503.
- GET `/api/v1/portfolio`: `{dataset_id,dataset_version,currency:"INR",horizon:"one_year",synthetic:true,facilities:[{id,borrower,industry,geography,rating,pd,lgd,ead,expected_loss}],summary:{facility_count,total_ead,total_expected_loss,weighted_pd,weighted_lgd,borrower_hhi},segments:[{industry,ead,expected_loss,share}],warnings:string[]}`.
- GET `/api/v1/facilities?q=&industry=&offset=0&limit=25`: `{items,total,offset,limit}`.
- POST `/api/v1/stress`: JSON `{pd_multiplier:1.5,lgd_multiplier:1.1,ead_multiplier:1,industry:null}` returns `{baseline_el,stressed_el,delta_el,delta_pct,assumptions:string[]}`; reject nonfinite/out-of-range, cap stressed PD/LGD to1.
- GET `/api/v1/explanation`: `{mode:"deterministic",text,disclaimer}` derived from current portfolio.

All displayed portfolio values must come from the backend. No fake model metrics, no claim of full product readiness. Module placeholders should not look completed.

## Synthetic CSV preview (not a persisted import)

POST `/api/v1/import-preview` with a raw UTF-8 CSV body, `Content-Type: text/csv`, and `X-AegisRisk-Synthetic: true`. No database access or external AI calls. The acknowledgement is a user assertion, not proof that data is synthetic; never upload customer information.

Required headers (any order, exact spelling, no extra/duplicate columns):

`id,borrower,industry,geography,rating,pd,lgd,ead,currency,horizon`

Example fictional record:

`SYN-CSV-001,Fictional Orchard,Energy,West,B,0.1,0.5,1000.00,INR,one_year`

Limits: 256 KiB encoded file; 1,000 nonblank data records; UTF-8 BOM accepted. CSV quoting is supported. Fully empty lines are ignored; empty records are rejected. Text is trimmed, printable and nonempty; formula-like prefixes (= + - @) are rejected. Field lengths match the facility model. IDs use ASCII letters/digits/hyphens/underscores, start with a letter or digit, and must be unique within the file (case-insensitive). Borrower HHI groups exact trimmed borrower labels; use a consistent name for one borrower.

PD/LGD are decimal fractions from 0 to 1, at most 10 decimal places, not percentages. EAD is INR from 0 to 1,000,000,000,000 with at most 2 decimal places. Signs, exponents, thousands separators, NaN and infinity are rejected. Currency must be INR and horizon one_year on every row. No automatic conversions or rounding of inputs.

Valid response (200): `{valid:true,persisted:false,digest,synthetic_acknowledged:true,currency,horizon,row_count,valid_rows,invalid_rows:0,issue_count:0,issues:[],issues_truncated:false,summary,warnings}`. Summary uses the existing Decimal risk calculations with JSON numbers for presentation. Example EL is INR 50. Zero total EAD returns null weighted ratios and HHI.

Invalid row response (422): same envelope with `valid:false,summary:null` and `issues:[{row,column,code,message}]`. Row means CSV record number, including the header as record 1. At most 100 issues are returned; issue_count records the total. No partial-file summary is calculated. Raw uploaded values are not echoed. Structural/encoding/header errors use `{detail}` (422); missing acknowledgement 400; wrong content type 415; byte/row limits 413.

This previews the uploaded file in isolation. It does not check IDs against existing database facilities, merge, save, replace, or affect the active portfolio. XLSX, authentication and production upload abuse controls remain future work. Persisting a reviewed CSV uses the separate opt-in endpoint below. Do not expose an unauthenticated demo as a customer-data service.

## Reviewed synthetic snapshots (disabled by default)

The API process must explicitly opt in with `SYNTHETIC_IMPORTS_ENABLED=true`. This is a local single-user demonstration feature, not permission to expose uploads publicly. There is no authentication, tenant separation, aggregate storage quota or retention/deletion interface. All saved content must be fictional.

- GET `/api/v1/saved-portfolios?offset=0&limit=50`: `{enabled,items:[{id,name,digest,row_count,created_at}],total,offset,limit}`. Offset is nonnegative; limit is 1–100. Disabled instances return an empty disabled catalog. Raw CSV text is not returned by this listing.
- POST `/api/v1/saved-portfolios?name=...`: raw CSV with `Content-Type: text/csv`, `X-AegisRisk-Synthetic: true`, `X-AegisRisk-Reviewed: true`, and `X-AegisRisk-Preview-Digest` equal to the preview's lowercase SHA-256 digest of the original file bytes. Names are trimmed, printable, nonempty, at most 80 characters and cannot begin with formula-like prefixes.
- The server revalidates the entire CSV, then compares the digest. A valid new snapshot returns 201: `{persisted:true,created:true,portfolio:{id,name,digest,row_count,created_at}}`. Identical file bytes return 200 with `created:false` and the original metadata/name. No merge, overwrite or partial save occurs.
- Errors: disabled saving 403; missing review/synthetic acknowledgement 400; wrong content type 415; byte/row limits 413; invalid name/CSV 422; stale preview digest 409; storage failure 503 with a generic message. Validation failures never create a partial snapshot.
- GET portfolio, facilities and explanation, plus POST stress, accept `dataset_id=<UUID>`. Omit it to use the seeded demo. A malformed UUID is 422, an unknown ID 404, disabled saved access 403, and a corrupt snapshot 503. None silently fall back to the demo. A selected portfolio reports its ID and `saved-v1:<UUID>` version; the demo reports a null ID.

The browser proxies only fixed resource paths. Preview/save requests are byte-bounded and require the acknowledgement headers; the backend remains authoritative. Saving leaves the current selection unchanged. Opening a saved portfolio is explicit. Dataset switches clear the previous note/scenario and invalidate in-flight responses; reload returns to the demo while preserving saved records. The UI prints rounded currency for presentation; backend Decimal calculations remain the source of truth.
