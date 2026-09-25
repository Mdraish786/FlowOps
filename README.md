# FlowOps

An approval workspace built for everyday company requests: equipment, software, cloud budgets, access, expenses, leave, vendor payments, and training.

The project contains a working React / TypeScript frontend, a Python FastAPI API, PostgreSQL configuration, SQLAlchemy models, Alembic migrations, Redis rate limiting, Celery background jobs, private attachments, and Docker Compose. The preview uses sample data; the normal frontend build uses the actual API and database.

## Start here

**Windows without Docker:** double-click `START_WINDOWS.bat` after installing Python 3.12+ and Node.js 22+. This starts a real API with a local SQLite database for easy first use. PostgreSQL is the intended deployment database; use Docker below to run that stack.

**PostgreSQL + Docker (recommended):** install Docker Desktop and Python, open a terminal in this folder, then run:

```powershell
python scripts/setup.py
docker compose up --build -d
docker compose run --rm backend python -m app.manage seed
```

Open **http://localhost:8080**.

The setup script prints a unique demo password and saves it as `DEMO_PASSWORD` in your local `.env`. All sample accounts use that password. No actual password or JWT signing secret is shipped in the archive. Do not seed sample accounts in production.

| Role | Sign-in email |
| --- | --- |
| Employee | arjun@flowops.local |
| Employee, same team | sara@flowops.local |
| Manager | raish@flowops.local |
| IT | neha@flowops.local |
| Finance | priya@flowops.local |
| HR | rohan@flowops.local |
| Director | ananya@flowops.local |
| Administrator | admin@flowops.local |
| Employee, different team | vikram@flowops.local |
| Manager, different team | meera@flowops.local |

To stop the stack, run `docker compose down`. Database and uploaded documents stay in named Docker volumes. Do not add `-v` unless you intentionally want to erase those volumes.

## First end-to-end check

1. Sign in as Arjun, choose **New request**, and request equipment costing **₹75,000**.
2. The route shows **Manager → IT → Finance**. Submit the request.
3. Sign out and sign in as Raish. Open **Approvals**, select the request, and approve it.
4. Sign in as Neha, then Priya, and approve their respective steps.
5. Sign in as Arjun. The request now shows **Approved**, with each decision in the timeline.
6. Sign in as Sara. Arjun’s request should not be visible or retrievable through the API.
7. Try **Ask for details** with a comment. The requester can submit the requested information and resume the same approval step.

Sample activity and sample requests are fictional, dated September 2026. Requests you submit use the real current time.

## What works

- Login and logout; 15-minute JWT access cookies; rotating seven-day refresh sessions with immediate revocation.
- Argon2id password hashing; reset tokens that expire after 30 minutes and work once.
- Seven roles, manager assignments, object-level access rules, and no self-approval.
- Create, view, comment, cancel, approve, reject, request information, and resubmit.
- Workflow editing by admins with amount ranges, overlap checks, ordered steps, and snapshots for existing requests.
- Optimistic concurrency checks and PostgreSQL row locking for decisions; request change, audit event, and notification commit together.
- Account creation, role changes, and deactivation. Access changes revoke existing sessions.
- Search, status/category filters, request details, analytics, CSV export, and responsive navigation.
- Private uploads: 5 MB limit, extension/MIME/signature checks, DOCX checks, generated filenames, authorized download.
- Optional ClamAV scanning, required in production mode.
- Scoped audit activity and database notifications; a WebSocket endpoint with 30-second frontend polling fallback.
- Redis login rate limiting; in-memory limiting only for single-process local development.
- Celery email outbox, password reset email jobs, daily reminders for requests older than 24 hours, and 48-hour escalation notices.
- TOTP verification and local administrator enrollment, required for sensitive roles in production mode.
- Nginx security headers, same-origin routing, restricted CORS, SameSite cookies, and Origin validation for cookie mutations.

## Manual Windows setup

Use three terminals if you prefer to inspect each part.

### One-time setup (project root)

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
python scripts/setup.py
Copy-Item .env backend/.env
```

Edit `backend/.env`: change `FRONTEND_ORIGIN` to `http://localhost:5173`. For a quick first run, omit `DATABASE_URL` to use SQLite. For your local PostgreSQL server, add:

```dotenv
DATABASE_URL=postgresql+psycopg://flowops:YOUR_URL_ENCODED_PASSWORD@localhost:5432/flowops
```

Create the `flowops` database and a dedicated account in PostgreSQL first. URL-encode special characters in passwords. pgAdmin is optional and only used to inspect/manage the database.

### Backend terminal

```powershell
cd backend
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m app.manage seed
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend terminal (project root)

```powershell
npm install
npm run dev:frontend
```

Open **http://localhost:5173**. This frontend proxies `/api` to the backend, so no manual API URL editing is required. Development API documentation is available at **http://127.0.0.1:8000/docs**.

### Redis and email (optional during local development)

The core approval flow works without email. To send real messages, configure SMTP and run Redis, Celery worker, and Celery beat. The Docker stack already contains Redis, worker, and beat.

```dotenv
SMTP_HOST=your.smtp.server
SMTP_PORT=587
SMTP_USERNAME=your_account
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_verified_sender@example.com
SMTP_STARTTLS=true
```

Restart backend, worker, and beat after changing `.env`. An email provider and credentials are not included. Without SMTP, no emails are sent; in-app updates still work. Email delivery is at least once, so a crash after sending can result in a duplicate email.

## Project map

| Path | Purpose |
| --- | --- |
| `app/page.tsx` | Main React application and workflows |
| `app/globals.css` | Product styles and responsive layouts |
| `frontend/` | Standalone Vite entry point and API proxy |
| `lib/flowops/data.ts` | Types and sample workspace adapter |
| `components/ui/` | Accessible shared interface primitives |
| `backend/app/main.py` | API routes |
| `backend/app/models.py` | Database models |
| `backend/app/security.py` | Passwords, sessions, JWT, MFA, rate limiting |
| `backend/app/services.py` | Authorization and approval transactions |
| `backend/app/tasks.py` | Celery outbox, reminders, escalation |
| `backend/app/manage.py` | Seed, admin creation, authenticator enrollment |
| `backend/alembic/` | Versioned schema migrations |
| `backend/tests/` | API, workflow, and authorization tests |
| `docker/` | Backend/frontend containers and Nginx |
| `docs/` | Security notes, scope, API guide, verification results |

The frontend uses React, TypeScript, Tailwind, accessible Radix/shadcn primitives, Lucide icons, Recharts, and browser fetch. React Router, Axios, and TanStack Query from the proposed stack are not needed for this implementation: views share one workspace, and the API adapter handles requests directly. Core backend stack is FastAPI + SQLAlchemy + PostgreSQL.

## Production deployment

Read `docs/SECURITY_AND_DEPLOYMENT.md`. This is a working development project, not an independently audited enterprise product. No system can be honestly called 100% hack-proof.

A real deployment needs HTTPS, production secrets, SMTP, MFA enrollment, a malware scanner, backups with tested restoration, monitoring, and dependency/security review. PostgreSQL and Redis must remain private. AI-assisted routing is a future feature; no AI makes approval decisions.

## Checks

```powershell
npm run check
npm run build:frontend
cd backend
.venv/Scripts/python.exe -m pytest -q
```

The test suite sets up a disposable SQLite database and never uses your application data. PostgreSQL-specific lock behavior, Docker services, mail delivery, and ClamAV must also be verified in your deployment environment. See `docs/VERIFICATION.md` for what was actually run during delivery.

Photo: NEW DATA SERVICES / Unsplash. Full attribution and license details: `docs/ASSETS.md`.

## Render demo deployment

A single-service Render deployment is included in this package. See `RENDER_DEPLOY.md` and `render.yaml`. The Render image builds the React frontend, serves it from FastAPI on the same HTTPS origin, runs Alembic migrations automatically, and can seed the demo workspace on first launch.
