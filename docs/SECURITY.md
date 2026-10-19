# Security notes — educational prototype, not a compliance claim

## Scope and boundaries

Only fictional data. Native demo services bind to loopback; Compose publishes ports only on 127.0.0.1. No personal banking documents, API credentials or third-party AI requests. No affiliation with any bank or regulator.

| Threat | Current mitigation | Remaining work |
| --- | --- | --- |
| Secret disclosure | Ignored .env files, no external API key, generic storage errors | Automated secret scanning and operational secret management |
| Query injection | SQLAlchemy expressions, parameter binding, literal search escaping | Expanded fuzzing and independent review |
| Invalid scenario | Finite 0–10 multipliers, unknown-field rejection, bounded JSON proxy body | Traffic rate limits and service-level resource controls |
| Browser abuse | Fixed proxy paths, no redirects, timeouts, no wildcard CORS, guarded report identity | CSP/headers review and deployment threat model |
| Unauthorized persisted writes | Saving disabled by default; explicit synthetic/review assertions and raw-byte preview digest | Authentication, authorization, tenant isolation and CSRF/origin protection before any shared saving |
| Upload resource exhaustion | 256 KiB input, 1,000 rows, bounded streaming, XLSX expanded-size/member/ratio limits | Concurrency limits, parser isolation and independent adversarial testing |
| Active workbook content | Values-only XLSX, archive validation, defused XML, formula/macro/link/hidden-content rejection | These checks are not proof of general spreadsheet safety |
| Stored-file corruption | Immutable snapshot IDs, normalized-storage SHA-256 verified on read, revalidation | Authenticated provenance, storage lifecycle and backup policies |
| Storage growth | Saving remains local-only and opt-in; duplicate stored bytes reuse snapshots | Aggregate quotas, retention and deletion interface |
| Misleading analytics | Fictional labels, fixed horizon/currency, decimal evidence and explicit limitations | Independent math/model validation; no regulatory claims |
| Dependency risk | Frontend lockfile, pinned XLSX libraries, CI dependency audits | Fully locked Python environment and continuous maintenance |

Synthetic/review checkboxes are user assertions, not authentication or proof that data is fictional. CSV snapshots retain uploaded bytes. XLSX snapshots retain normalized CSV values; the original workbook is not stored. An upload can still contain confidential text: never submit it to this demo.

SHA-256 fingerprints detect content changes; they do not prove authorship or authenticity. Reports are not signed audit records. Scenarios and reports do not mutate stored portfolios. Switching datasets or editing assumptions invalidates pending work to reduce stale-output errors.

The prototype is not approved for internet exposure. Keep SYNTHETIC_IMPORTS_ENABLED disabled on shared/public instances. Production hosting requires a separate reviewed security boundary; passing CI, a dependency audit or browser tests does not establish compliance or validated credit-decision capability.
