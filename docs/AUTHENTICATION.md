# Workspace access (development feature)

AegisRisk supports an opt-in, administrator-issued bearer-token mode for isolated fictional-data workspaces. It is not bank authentication, public signup, password login, OIDC, MFA or a production approval. The public demo remains in local mode with saving disabled. No hosted service or real user credential is created by these source changes.

## Modes and trust boundaries

- AEGISRISK_ACCESS_MODE=local is the default for local single-user research and the read-only fictional demo. It uses the reserved local workspace. Anyone reaching that instance has the same local access; do not enable shared public persistence in this mode.
- AEGISRISK_ACCESS_MODE=token requires a valid bearer token for every data, preview, save, model and report route. Health is public. Readiness validates configuration and the database without requiring a token.
- Unknown modes and invalid or missing token configuration fail closed with a generic 503. Expired, revoked, missing or malformed credentials return a generic 401. Configuration and credentials are not returned in errors.
- Identity and workspace come only from the server's token-hash registry. Caller-supplied workspace/user headers and query values do not establish identity.

## Administrator configuration

Configure these variables on the **API process**, not as NEXT_PUBLIC variables and not in source control:

| Variable | Meaning |
| --- | --- |
| AEGISRISK_ACCESS_MODE | Exact value token to opt in |
| AEGISRISK_ACCESS_USERS | JSON array of 1–64 validated user records; maximum 32 KiB |
| SYNTHETIC_IMPORTS_ENABLED | Exact true separately enables reviewed snapshot saving |
| DATABASE_URL | Database for this private research instance |

Each record has exactly subject, workspace, role, token_sha256 and expires_at. Subject and workspace are canonical UUID strings. Subjects and token hashes are unique; several subjects may share one workspace. Role is viewer or analyst. Expiry is a positive integer Unix timestamp; a token is invalid at or after that instant.

Use a cryptographically random 32-byte token encoded as 43 URL-safe Base64 characters (for example, Python's secrets.token_urlsafe(32)). The registry stores only its lowercase SHA-256 hex digest. This hashing scheme relies on high-entropy random tokens and must never be used for user-chosen passwords. Distribute credentials through an approved private channel. Never paste them into GitHub, screenshots, URLs, CI variables for public demos, or analytics.

The administrator owns issuance, secure distribution, expiry and revocation. Removing a record revokes that token after configuration is applied to **every API process**. Process environment changes require restart; there is no online administration or self-service recovery UI. Do not reuse tokens between people or environments. Keep API clocks accurate and choose short access lifetimes suitable for the research session.

The web process requires only its existing fixed API_BASE_URL; it learns the access mode from GET /api/access. It must not receive the registry. Run migrations before starting the API. Require HTTPS for any remote use, restrict API/database network reachability, and keep the existing body, request-time and snapshot-origin controls. This document does not authorize exposing or deploying a service.

## Permissions and data ownership

Both roles may inspect the shared fictional seed, preview fictional CSV/XLSX, calculate scenarios, use the synthetic Model Lab, and read/export snapshots in their workspace. Only analysts may save reviewed snapshots when saving is enabled. The API enforces this independently of the hidden browser save controls.

Snapshot reads, catalog counts/pagination, exports and duplicate reuse are scoped to the verified workspace. Unknown and foreign snapshot IDs return the same 404. Identical bytes in different workspaces create different snapshots; identical bytes within one workspace reuse the existing snapshot. Input validation, immutable data and report integrity rules are unchanged.

Migration 0003 moves every pre-existing snapshot into the reserved local workspace and replaces global digest uniqueness with (workspace_id, digest). It does not assign historical data to a private user. Downgrade refuses to proceed while private-workspace snapshots exist, preventing an accidental merge into the unauthenticated catalog. Back up and verify a restore on an isolated database before migrating any valuable environment; no user database was migrated by this GitHub-only work.

## Browser behavior

The access screen checks the API before mounting the dashboard. Token-mode users enter their administrator-issued token into a masked field. The field is cleared after submission. Tokens are kept only in module memory for the current tab: no localStorage, sessionStorage, cookies or URL parameters. Refresh requires re-entry.

All dashboard, upload, model and report requests use the same restricted same-origin request helper. Credentials are forwarded explicitly to the fixed backend, without cookies or caller identity headers; redirects are rejected. Responses are non-cacheable. The UI is not an authorization boundary: every API request is verified separately.

Locking clears the token, cancels pending requests, unmounts the dashboard and clears its loaded state. A 401 also locks the workbench. Locking is local cleanup, **not server-side revocation**; a copied token remains valid until expiry or administrator revocation. Downloaded reports remain wherever the user saved them. Closing/navigating away clears tab memory, but this does not promise forensic erasure. A token expires on the next server request; there is no inactivity timer or immediate remote screen-clearing guarantee.

## Verification and limits

API tests cover all data-route authentication, malformed/duplicate credentials, expiry/revocation, invalid configuration, forged identity, role restrictions, workspace catalogs/deduplication, eight foreign report/calculation paths, legacy isolation and migration rollback refusal. Separate full-stack tests start a fresh token-mode API/database/web process and exercise real browser/proxy/API workflows on Chromium, Firefox and WebKit. Runtime test tokens are disposable; access tests deliberately omit request tracing so tokens do not enter trace artifacts.

See [RELEASE_READINESS.md](RELEASE_READINESS.md) for the actual verified commit and run. Source or test presence alone is not proof of a passing run.

Remaining production controls include independent security review, an appropriate identity provider/MFA and credential lifecycle, comprehensive CSP/XSS defenses, authorization audit trails, per-workspace quotas, encrypted storage/backup policy, restore exercises, retention/deletion workflows and operational monitoring. Memory-only tokens reduce persistence but do not protect against same-origin script compromise or a compromised client. Use fictional data only.
