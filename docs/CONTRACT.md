# Initial integration contract

API prefix `/api/v1`; backend localhost:8000, frontend localhost:3000. Frontend server proxies fixed API paths through Next.js route handlers; no browser CORS needed. PostgreSQL deployment target; explicit SQLite fallback for local verification only. All demo data fictional, INR, one-year PD horizon.

- GET `/api/v1/health`: `{status:"ok", service:"aegisrisk-api", version:"0.1.0", external_ai:false}` liveness; no DB claim.
- GET `/api/v1/ready`: `{status:"ok", database:"connected"}` or safe 503.
- GET `/api/v1/portfolio`: `{dataset_version,currency:"INR",horizon:"one_year",synthetic:true,facilities:[{id,borrower,industry,geography,rating,pd,lgd,ead,expected_loss}],summary:{facility_count,total_ead,total_expected_loss,weighted_pd,weighted_lgd,borrower_hhi},segments:[{industry,ead,expected_loss,share}],warnings:string[]}`.
- GET `/api/v1/facilities?q=&industry=&offset=0&limit=25`: `{items,total,offset,limit}`.
- POST `/api/v1/stress`: JSON `{pd_multiplier:1.5,lgd_multiplier:1.1,ead_multiplier:1,industry:null}` returns `{baseline_el,stressed_el,delta_el,delta_pct,assumptions:string[]}`; reject nonfinite/out-of-range, cap stressed PD/LGD to1.
- GET `/api/v1/explanation`: `{mode:"deterministic",text,disclaimer}` derived from current portfolio.

All displayed portfolio values must come from the backend. No fake model metrics, no claim of full product readiness. Module placeholders should not look completed.
