# Security Status and Production Backlog

## Implemented Controls

| Control | Current implementation | Status |
|---|---|---|
| Password handling | Passlib bcrypt hashing; passwords are not returned by the user store. | Implemented. |
| Authentication | HS256 JWT access token with subject, phone, role, issue/expiry, and access type claims. | Implemented for MVP. |
| Authorization | Backend admin dependency and Flutter `/admin` route guard. | Implemented; extension-worker role has no distinct workflow yet. |
| Mobile token storage | `flutter_secure_storage`; token and language only, no password persistence. | Implemented. |
| Authenticated APIs | Profile, dashboard, scan, pest, market, and admin surfaces use auth as designed. | Implemented; weather endpoints are not all authenticated. |
| Rate limits | In-memory general, login, and pesticide advisory limits. | Implemented for a single process only. |
| Upload validation | Safe basename, extension/MIME allow-lists, 5 MB limit, UUID filenames, traversal defense. | Implemented; no magic-byte content inspection. |
| Input validation | Pydantic request models and bounded advisory/query validation. | Implemented. |
| Audit logging | Thread-locked JSONL events for auth, scans, and pesticide access. | Implemented; no rotation or cross-process safety. |
| Source/status transparency | Mock/live/historical/unavailable states and pesticide citation fields are exposed. | Implemented. |
| Safe unavailable behavior | Missing model/source conditions return unavailable/error behavior rather than invented output. | Implemented. |

## Known Security and Operations Gaps

- Default JWT secret is development-safe only; production must reject weak/default secrets.
- Access tokens have no refresh, revocation, or key-rotation mechanism.
- Rate-limit buckets are in process, trust forwarded IP values, are not distributed, and reset on restart.
- JSON user storage is non-transactional, non-atomic, non-multi-process safe, and unsuitable for production.
- Audit logging lacks rotation, retention, tamper protection, and multi-process coordination; failed login details can contain attempted phone identifiers.
- Upload validation relies on extension and client MIME claim rather than content inspection.
- Flutter HTTPS assertion behavior requires release validation; no certificate pinning is implemented.
- The configured ML model path is absent, so the scan route cannot be treated as production-ready.
- No production data retention, consent, privacy, observability, backup, or incident-response process exists yet.

## Production Backlog

| Priority | Item | Acceptance condition |
|---|---|---|
| P0 | Deploy HTTPS endpoint and release signing | Release build uses trusted HTTPS API endpoint and signed APK is installed/tested on device. |
| P0 | Replace default JWT secret handling | Secrets come from production secret manager; startup fails on insecure defaults. |
| P1 | PostgreSQL migration | User/profile/scan data is transactional, migrated, backed up, and tested with concurrent requests. |
| P1 | Refresh tokens and key rotation | Rotation, expiry, revocation/logout semantics, and recovery flow are tested. |
| P1 | Persistent distributed rate limits | Proxy-aware limits persist across restarts and workers. |
| P1 | Monitoring and audit hardening | Structured, rotated, protected logs; metrics, alerts, and retention policy exist. |
| P1 | Privacy policy and consent | User-visible policy, consent record, deletion/retention procedures, and owner are defined. |
| P1 | Security assessment | Auth, API, upload, mobile, dependency, and infrastructure testing is completed. |
| P1 | Backup and recovery | Restore drill proves RPO/RTO and integrity for database, logs, models, and data. |
| P2 | Upload content verification | Magic-byte/image decoding validation and malware-scanning policy are implemented. |
| P2 | Field model validation | Model calibration and real-field-image validation determine safe production claims. |

No security gap was fixed in this freeze. The report is a handoff baseline, not a production-security attestation.
