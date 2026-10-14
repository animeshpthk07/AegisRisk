# Initial integration contract

API prefix `/api/v1`; backend localhost:8000, frontend localhost:3000. Frontend server proxies fixed API paths through Next.js route handlers; no browser CORS needed. PostgreSQL deployment target; explicit SQLite fallback for local verification only. All demo data fictional, INR, one-year PD horizon.

- GET `/api/v1/health`: `{status:"ok", service:"aegisrisk-api", version:"0.1.0", external_ai:false}` liveness; no DB claim.
- GET `/api/v1/ready`: `{status:"ok", database:"connected"}` or safe 503.
- GET `/api/v1/portfolio`: `{dataset_version,currency:"INR",horizon:"one_year",synthetic:true,facilities:[{id,borrower,industry,geography,rating,pd,lgd,ead,expected_loss}],summary:{facility_count,total_ead,total_expected_loss,weighted_pd,weighted_lgd,borrower_hhi},segments:[{industry,ead,expected_loss,share}],warnings:string[]}`.
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

Valid response (200): `{valid:true,persisted:false,synthetic_acknowledged:true,currency,horizon,row_count,valid_rows,invalid_rows:0,issue_count:0,issues:[],issues_truncated:false,summary,warnings}`. Summary uses the existing Decimal risk calculations with JSON numbers for presentation. Example EL is INR 50. Zero total EAD returns null weighted ratios and HHI.

Invalid row response (422): same envelope with `valid:false,summary:null` and `issues:[{row,column,code,message}]`. Row means CSV record number, including the header as record 1. At most 100 issues are returned; issue_count records the total. No partial-file summary is calculated. Raw uploaded values are not echoed. Structural/encoding/header errors use `{detail}` (422); missing acknowledgement 400; wrong content type 415; byte/row limits 413.

This previews the uploaded file in isolation. It does not check IDs against existing database facilities, merge, save, replace, or affect the active portfolio. XLSX, persisted imports, authentication and production upload abuse controls remain future work. Do not expose an unauthenticated demo as a customer-data service.
