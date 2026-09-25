# Security and deployment

## Trust boundaries

The browser never decides who may access a request. FastAPI authenticates the cookie/bearer token, checks the live account and session, loads the object, verifies ownership/assigned role, and performs the transition inside a database transaction. Admin access allows configuration and audit access, not automatic bypass of an approval step.

Requests snapshot the workflow and assigned manager when submitted. Reconfiguration does not silently alter an in-flight route. A version field catches outdated actions; PostgreSQL uses row locking as well. Comments and notifications commit with decisions. Audit rows are append-only through the application, but a database administrator can still change them: use database access restrictions or an external immutable log destination for stronger tamper resistance.

## Authentication

Passwords are Argon2id hashes. Access JWTs live for 15 minutes and are kept in HttpOnly, SameSite=Strict cookies. Refresh tokens are random, only their hash is stored, and rotation detects reuse. Every API access also checks session revocation. Login rate limiting uses Redis in production. Origin validation protects cookie mutations; the browser and API should use the same origin through Nginx. Credentialed CORS allows only the configured origin. HTTPS adds Secure cookies.

TOTP secrets are encrypted using a separate Fernet key. Sensitive roles require TOTP when `REQUIRE_MFA=true`. Enrollment is intentionally a local administrator operation rather than an unprotected public setup endpoint:

```sh
python -m app.manage enroll-mfa --email admin@yourcompany.com
```

Enter the account owner's current authenticator code to verify enrollment. Store the enrollment key and encryption key securely. There is no self-service recovery-code UI in this release; recovery requires a verified administrator-controlled process.

## Production configuration

- Create a fresh database. Run `alembic upgrade head`, then `python -m app.manage create-admin`. Do not seed demo accounts.
- Put the frontend/API behind HTTPS. Set `FRONTEND_ORIGIN=https://your-domain`.
- Generate separate strong values for `JWT_SECRET`, database password, and `MFA_ENCRYPTION_KEY`. Never commit `.env` or share it in a ZIP.
- Set `ENVIRONMENT=production`, `REQUIRE_MFA=true`, and `REQUIRE_MALWARE_SCAN=true`. Startup refuses an incomplete production configuration.
- Start a healthy ClamAV service; Compose provides it under `--profile secure`. Uploads fail closed if the scanner is unavailable.
- Enroll authenticators for Admin, IT, Finance, and Director accounts. Confirm all other users have the correct manager and department.
- Configure a verified SMTP sender, Redis, and Celery worker/beat. Run one beat scheduler. Review mail delivery and reminder behavior before inviting users.
- Keep PostgreSQL, Redis, the worker, and the raw API on internal networks. Compose binds the frontend to loopback by default; an HTTPS proxy can expose it deliberately. There are no public database or Redis ports.
- Limit direct database access. The application role should not be a superuser. Migrations can use a separate owner role in production.
- Back up PostgreSQL and the private upload volume. Encrypt backups, define retention, and restore a backup into an isolated environment before launch.
- Monitor HTTP errors, slow queries, failed login audit records, worker failures, scanner health, disk usage, and database connection limits. Wire your preferred telemetry/error platform before production use.
- Run dependency scans, independent authorization review, abuse testing, and an actual PostgreSQL concurrency test. A passing local suite is not a security certification.

## Files

Files are limited to 5 MB and ten files per request. Their extension, declared MIME, and leading signature are checked; DOCX packages are inspected for expected entries, total expanded size, and macros. Files get random server names outside the public directory. Downloads require object authorization and force attachment/octet-stream behavior. A production malware scanner adds another layer, not a guarantee of harmless content.

## Operational limits

- This release is a single-company workspace; multi-tenant isolation is not implemented.
- Roles and request categories are fixed code enums. Admins can assign roles and configure approval routes. A fully customizable permissions/department/category editor is future work.
- Request bodies are validated; Nginx enforces request size. Run behind the supplied proxy when exposed.
- Rate limiting without Redis is for local, single-process development only.
- Directory and request listings are suitable for a small workspace. Server-side pagination and reporting queries should be added for large installations.
- The UI has a 30-second polling fallback; the WebSocket server polls committed notifications every three seconds. It is not a distributed push broker.
- Session refresh is coordinated per tab. Multiple browser tabs can still contend on a one-use refresh token and require signing in again; use a cross-tab refresh coordinator before a large deployment.
- Email outbox delivery is at least once. A crash between SMTP delivery and marking a row sent can cause a duplicate.
- Reminder and escalation jobs create notifications; escalation does not bypass the required human approvals.
- No automated AWS/DB/VPN provisioning occurs after approval. Approval authorizes a separate operational action.
- No AI routing, OpenTelemetry exporter, SSO, recovery-code UI, or disaster recovery automation is claimed as implemented.

## References

- FastAPI security: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- SQLAlchemy version counters: https://docs.sqlalchemy.org/en/20/orm/versioning.html
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
