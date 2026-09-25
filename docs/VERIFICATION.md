# Delivery verification

Verified on 24 September 2026.

## Completed

- 16 API/workflow/security tests passed against a disposable SQLite database.
- Repeat tested after updating and installing the pinned backend dependencies in a fresh Python environment.
- `pip check` reported no broken dependencies in that fresh environment.
- TypeScript compile checks passed.
- Standalone release archive source passed npm ci, TypeScript checks, and Vite production build with its own minimal dependencies and package-lock.json.
- Alembic initial migration applied successfully to a new database; demo data seeded successfully.
- Browser checked the dashboard, real packaged office image, request details, manager approval transition, role selection, and employee request submission with correct ownership.
- Dependency vulnerability scan: runtime and test requirements were updated after findings in older Starlette and pytest versions. After also updating pip, the final clean-environment scan reported: No known vulnerabilities found. This is a point-in-time package advisory check, not a guarantee. Setup scripts explicitly upgrade pip before installing.

## Tested API cases

1. Employee list and object-level isolation.
2. Complete Manager → IT → Finance approval, with transactional audit/comment/notification records.
3. Self-approval, wrong manager, and out-of-order approval blocked.
4. Stale/repeated approval returns conflict.
5. Ask for information → resubmit → reject.
6. Owner cancellation and comments.
7. Refresh token rotation and logout revocation.
8. Refresh token reuse revokes the session.
9. Cross-origin mutation and privilege escalation blocked.
10. Upload type validation and authorized download.
11. Workflow overlap rejection and preservation of an existing route snapshot.
12. Invalid amounts and login rate limiting.
13. Expired JWT rejected.
14. Optimistic concurrency rejects a second stale database write.
15. Password reset works once and revokes old sessions.
16. Account deactivation revokes active access.

## Boundaries

PostgreSQL and Docker executables were not available in the build environment, so PostgreSQL container startup, actual PostgreSQL locking under load, and Docker orchestration were not executed here. The migrations and driver configuration target PostgreSQL, and Docker Compose includes the complete local stack. Run the README end-to-end test on that stack before presenting it as a PostgreSQL deployment.

SMTP delivery, Celery with a real broker, ClamAV scanning, TOTP enrollment with a physical authenticator, and a production HTTPS domain require your local/deployment services and were not exercised here. Browser WebMCP was unavailable in the testing browser; the optional tool is feature-detected and does not affect normal UI operation.

The frontend build emits a nonblocking bundle-size advisory. The Python test runner emits a nonblocking httpx/TestClient deprecation warning. Neither prevents the current tests or application build.

These are verification results, not a penetration-test certificate or a guarantee against attacks.
