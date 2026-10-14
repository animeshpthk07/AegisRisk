# Security notes — foundation, not a compliance claim

## Scope and boundaries

Only fictional data. Local loopback binding for native preview; Compose publishes ports only on 127.0.0.1. No personal banking documents, tokens or third-party AI requests. No affiliation with Deutsche Bank or any other institution.

| Threat | Current mitigation | Remaining work |
| --- | --- | --- |
| Secret disclosure | Ignored .env files, no API key, generic DB errors | Automated secret scanning before publication |
| Query injection | SQLAlchemy expressions, parameter binding, literal search escaping | Expand fuzz tests with future import/query features |
| Unbounded or invalid scenario | Finite values, 0–10 multipliers, Pydantic unknown-field rejection | Request-body limit at server/proxy and traffic rate limits before public hosting |
| Browser abuse | Fixed proxy paths, no redirects, timeout, no wildcard CORS | CSP and production headers audit |
| Unauthorized write | No persisted web write endpoints; explicit local seed | Authorization if account/import persistence is later exposed |
| Misleading analytics | Synthetic labels, horizon/currency, no real-world validation claims | Independent math/model review |
| Dependency risk | Isolated project environment, lockfile, audit commands and CI | Record scan results and remediate findings |

The prototype is not approved for internet exposure. Do not upload real bank or customer data. Do not claim regulatory compliance or validated credit approval capability.
