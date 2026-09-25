# FlowOps deployment on Render

This package is prepared to run the React frontend and FastAPI backend from one Render Web Service, with Render PostgreSQL.

## 1. Push this folder to GitHub
Create a new GitHub repository and upload the contents of the `FlowOps` folder (not the outer ZIP folder).

## 2. Create the Render Blueprint
1. Sign in to Render.
2. Choose **New > Blueprint**.
3. Connect the GitHub repository.
4. Render reads `render.yaml` and creates:
   - one Web Service: `flowops`
   - one PostgreSQL database: `flowops-db`

## 3. Enter DEMO_PASSWORD
Render will ask for `DEMO_PASSWORD` because it is marked `sync: false`.
Use a password of at least 12 characters. Example format: `FlowOpsDemo-2026!` (choose your own password).

On the first deployment, the database is migrated and demo accounts are seeded. On later restarts/deployments, seeding is skipped when users already exist.

## 4. Open the service
After deployment succeeds, open the Render service URL. The frontend and API use the same HTTPS origin, so login cookies work without cross-site cookie configuration.

Health check: `/api/health`

## Demo login
Use any email from `backend/app/seed.json` with the `DEMO_PASSWORD` you entered in Render.

## Important deployment notes
- `ENVIRONMENT=staging` enables Secure HTTPS cookies but does not force Redis, MFA, or ClamAV. This is suitable for a college/demo deployment, not an audited enterprise production rollout.
- Uploaded attachments are stored in `/tmp/flowops-uploads` in this demo configuration and can disappear when the Render instance is replaced/restarted. For persistent file storage, use an object-storage service or a persistent disk on a plan that supports it.
- Password-reset emails require SMTP configuration. The core approval workflow works without SMTP.
- For a true production deployment, use `ENVIRONMENT=production` and configure Redis, MFA, malware scanning, backups, monitoring, persistent file storage, and production SMTP as described in `docs/SECURITY_AND_DEPLOYMENT.md`.

## If deployment fails
Check Render Logs first. Common causes:
- `DEMO_PASSWORD` is shorter than 12 characters.
- The PostgreSQL database is still provisioning; redeploy once it is available.
- A build dependency failed to download; use **Manual Deploy > Clear build cache & deploy**.
