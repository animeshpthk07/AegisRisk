# Security notes — educational prototype, not a compliance claim

## Scope and boundaries

Only fictional data. Native demo services bind to loopback; Compose publishes ports only on 127.0.0.1. No personal banking documents, API credentials or third-party AI requests. No affiliation with any bank or regulator.

| Threat | Current mitigation | Remaining work |
| --- | --- | --- |
| Secret disclosure | Ignored .env files, no external API key, generic storage errors | Automated secret scanning and operational secret management |
| Query injection | SQLAlchemy expressions, parameter binding, literal search escaping | Expanded fuzzing and independent review |
| Invalid scenario | Finite 0–10 multipliers, unknown-field rejection, bounded JSON proxy body | Traffic rate limits and service-level resource controls |
| Browser abuse | Fixed proxy paths, no redirects, timeouts, no wildcard CORS, guarded report identity, deny framing/objects and unused device capabilities, no referrer | Full script/style CSP, cross-browser review and deployment threat model |
| Unauthorized persisted writes | Saving disabled by default; explicit synthetic/review assertions, raw-byte preview digest and same-origin check on web save requests | Authentication, authorization, tenant isolation and reviewed CSRF/session controls before any shared saving |
| Upload resource exhaustion | 256 KiB input, 1,000 rows, bounded streaming, XLSX expanded-size/member/ratio limits | Concurrency limits, parser isolation and independent adversarial testing |
| Active workbook content | Values-only XLSX, archive validation, defused XML, formula/macro/link/hidden-content rejection | These checks are not proof of general spreadsheet safety |
| Stored-file corruption | Immutable snapshot IDs, normalized-storage SHA-256 verified on read, revalidation | Authenticated provenance, storage lifecycle and backup policies |
| Storage growth | Saving remains local-only and opt-in; duplicate stored bytes reuse snapshots | Aggregate quotas, retention and deletion interface |
| Misleading analytics | Fictional labels, fixed horizon/currency, decimal evidence and explicit limitations | Independent math/model validation; no regulatory claims |
| Dependency risk | Frontend lockfile, pinned XLSX libraries, CI dependency audits | Fully locked Python environment and continuous maintenance |

Synthetic/review checkboxes are user assertions, not authentication or proof that data is fictional. CSV snapshots retain uploaded bytes. XLSX snapshots retain normalized CSV values; the original workbook is not stored. An upload can still contain confidential text: never submit it to this demo.

SHA-256 fingerprints detect content changes; they do not prove authorship or authenticity. Reports are not signed audit records. Scenarios and reports do not mutate stored portfolios. Switching datasets or editing assumptions invalidates pending work to reduce stale-output errors.

The prototype is not approved for internet exposure. Keep SYNTHETIC_IMPORTS_ENABLED disabled on shared/public instances. Production hosting requires a separate reviewed security boundary; passing CI, a dependency audit or browser tests does not establish compliance or validated credit-decision capability.

## Browser response policy

The Next.js web server applies these headers across dashboard, API and error paths:

- `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`.
- `Referrer-Policy: no-referrer` so navigation and fetch requests do not disclose the page URL through the Referer header. This does not anonymize network traffic or remove URLs from server logs.
- `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()` because the workbench does not need these capabilities. This changes policy for this application, not browser-wide permissions.
- `Content-Security-Policy: base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'`. This restricts document embedding, objects, base URLs and form destinations. It deliberately does not claim complete script/style injection protection; nonce/hash policy and deployment-specific resource rules remain unfinished.

Integration tests request real success, rejected-method and missing-page responses; Chromium checks its effective device policy and omission of the Referer header. The existing full application/download suite checks compatibility in native and Compose environments. See the [milestone tracker](MILESTONES.md) for actual outcomes. These headers are emitted by Next.js; they are not a claim that a directly exposed FastAPI server or hosting proxy has the same policy. No HSTS or public TLS configuration is claimed for the loopback demo.

Configuration follows the official [Next.js headers](https://nextjs.org/docs/app/api-reference/config/next-config-js/headers) and [CSP guidance](https://nextjs.org/docs/app/guides/content-security-policy). Full nonce-based CSP changes rendering requirements and needs separate testing; the baseline policy does not authorize shared saving or internet exposure.

## Web snapshot origin boundary

The web proxy rejects POST `/api/saved-portfolios` unless `Origin` exactly matches the request URL origin (scheme, host and port). Missing or opaque (`null`) origins are rejected. When `Sec-Fetch-Site` is supplied it must be `same-origin`; same-site siblings and cross-site requests are rejected. Validation runs before reading the upload or calling the backend, returns a non-cacheable 403 and does not fall back to `Referer` or forwarding headers. The normal browser save flow and explicit same-origin test clients retain the existing consent, digest, size and backend checks.

This is browser-origin defense in depth, not authentication. Non-browser callers can forge these headers; a compromised same-origin page is not stopped by it. The backend remains private/loopback and saving remains disabled by default. Reverse-proxy origin handling must be revalidated for any future deployment; do not trust arbitrary forwarded host values or weaken the check to make a deployment work. Shared persistence still requires authenticated sessions, authorization, tenant isolation and a reviewed CSRF strategy.

Eleven rejection cases exercise missing/opaque/foreign/malformed origins, wrong ports, fetch metadata and forged fallback headers, checking that the saved catalog does not change. Existing successful save/reload and duplicate-reuse workflows verify allowed requests. Results belong to the exact GitHub verification run, not to the presence of these tests.

## PDF and model boundaries

PDF exports use the same bounded synthetic evidence as JSON, load the dataset once, and make no database writes or external asset/provider requests. Output is limited to 1,000 facilities and 4 MiB. Portfolio labels are literal escaped text; non-ASCII labels use Unicode escapes. Browser byte-count/header/SHA-256 checks detect malformed or changed transfers but cannot authenticate the server or turn a report into a signed audit record. Server CPU/concurrency budgets, broader parser testing and production traffic controls remain required.

The synthetic Model Lab uses a fixed in-process training recipe with bounded inputs and a cached model. It does not load an uploaded pickle, replace portfolio assumptions or establish real-world credit accuracy. Input validation and synthetic-consent checkboxes do not replace authorization, operational limits or independent validation.
