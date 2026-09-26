# FlowOps

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=28&duration=3000&pause=900&color=2563EB&center=true&vCenter=true&width=800&lines=FlowOps+-+Approval+Workspace;FastAPI+%2B+React+%2B+PostgreSQL;Secure+Role-Based+Approval+Workflows;From+Request+to+Approval+-+All+in+One+Place" alt="FlowOps animated heading" />
</p>

<p align="center">
  <strong>A secure approval workspace for everyday company requests.</strong>
</p>

<p align="center">
  Equipment • Software • Cloud Budgets • Access • Expenses • Leave • Vendor Payments • Training
</p>

<p align="center">
  <a href="https://flowops-274o.onrender.com">
    <img src="https://img.shields.io/badge/LIVE%20DEMO-Open%20FlowOps-22c55e?style=for-the-badge&logo=render&logoColor=white" alt="Live Demo" />
  </a>
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-2563eb?style=for-the-badge&logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Database-PostgreSQL-4169e1?style=for-the-badge&logo=postgresql&logoColor=white" />
</p>

---

## 🚀 Live Demo

FlowOps is currently deployed on Render.

### 👉 [Open FlowOps Live](https://flowops-274o.onrender.com)

> The Render free service may need a short cold start when it has been inactive.

---

## ✨ About FlowOps

FlowOps is an approval management workspace built for everyday company requests such as equipment purchases, software access, cloud budgets, expenses, leave, vendor payments, training, and other internal approval workflows.

The project contains a working **React / TypeScript frontend**, **Python FastAPI API**, **PostgreSQL configuration**, **SQLAlchemy models**, **Alembic migrations**, **Redis rate limiting**, **Celery background jobs**, private attachments, and Docker Compose.

The preview environment uses sample data. The normal frontend build communicates with the real API and database.

---

## ⚡ Start Here

### Windows without Docker

After installing **Python 3.12+** and **Node.js 22+**, double-click:

```powershell
START_WINDOWS.bat
```

This starts a real API using a local SQLite database for quick development.

PostgreSQL is the intended deployment database.

---

### PostgreSQL + Docker — Recommended

Install Docker Desktop and Python, then open a terminal in the project folder:

```powershell
python scripts/setup.py
docker compose up --build -d
docker compose run --rm backend python -m app.manage seed
```

Open:

```text
http://localhost:8080
```

The setup script generates a unique demo password and stores it as:

```text
DEMO_PASSWORD
```

inside the local `.env` file.

All sample accounts use the generated password.

No real password or JWT signing secret is included in the project archive.

> ⚠️ Do not seed sample accounts in production.

---

## 👥 Demo Accounts

| Role | Sign-in Email |
| --- | --- |
| Employee | arjun@flowops.local |
| Employee — Same Team | sara@flowops.local |
| Manager | raish@flowops.local |
| IT | neha@flowops.local |
| Finance | priya@flowops.local |
| HR | rohan@flowops.local |
| Director | ananya@flowops.local |
| Administrator | admin@flowops.local |
| Employee — Different Team | vikram@flowops.local |
| Manager — Different Team | meera@flowops.local |

To stop the Docker stack:

```powershell
docker compose down
```

Database data and uploaded documents remain stored in Docker volumes.

Do **not** add `-v` unless you intentionally want to delete those volumes.

---

## 🔄 First End-to-End Workflow

1. Sign in as **Arjun**.
2. Choose **New Request**.
3. Create an equipment request worth **₹75,000**.
4. The workflow displays:

```text
Manager → IT → Finance
```

5. Submit the request.
6. Sign out and sign in as **Raish**.
7. Open **Approvals** and approve the request.
8. Sign in as **Neha** and approve the IT step.
9. Sign in as **Priya** and approve the Finance step.
10. Sign back in as **Arjun**.

The request should now show:

```text
Approved
```

with every approval decision visible in its timeline.

### Authorization Test

Sign in as **Sara**.

Arjun's request should not be visible or retrievable through the API.

You can also test **Ask for details**. The approver can request additional information, and the requester can provide it before continuing the same approval workflow.

---

## ✅ What Works

- Secure login and logout
- 15-minute JWT access cookies
- Rotating seven-day refresh sessions
- Immediate session revocation
- Argon2id password hashing
- One-time password reset tokens
- Seven user roles
- Manager assignments
- Object-level access control
- No self-approval
- Request creation
- Approval
- Rejection
- Request information
- Comments
- Request cancellation
- Request resubmission
- Workflow management
- Amount-based workflow routing
- Workflow overlap validation
- Ordered approval steps
- Workflow snapshots for existing requests
- Optimistic concurrency checks
- PostgreSQL row locking
- Audit events
- Notifications
- Account creation
- Role management
- User deactivation
- Session revocation after access changes
- Search
- Status filters
- Category filters
- Request details
- Analytics
- CSV export
- Responsive navigation
- Secure private uploads
- File extension validation
- MIME validation
- File signature checks
- DOCX validation
- Authorized downloads
- Optional ClamAV malware scanning
- WebSocket notifications
- Polling fallback
- Redis login rate limiting
- Celery background jobs
- Password-reset email jobs
- Daily pending-request reminders
- 48-hour escalation notifications
- TOTP verification
- Administrator MFA enrollment
- Nginx security headers
- Restricted CORS
- SameSite cookies
- Origin validation

---

## 🛡️ Security Architecture

FlowOps implements multiple security layers rather than depending on a single protection mechanism.

```text
User
  ↓
React Frontend
  ↓
Nginx / HTTPS
  ↓
FastAPI
  ↓
Authentication + Authorization
  ↓
Business Rules
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

Additional services:

```text
FastAPI
 ├── Redis
 │    └── Rate Limiting
 │
 ├── Celery
 │    ├── Email Jobs
 │    ├── Reminders
 │    └── Escalations
 │
 └── Private File Storage
      └── Malware Scanning
```

---

## 🧰 Tech Stack

### Frontend

![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)

- React
- TypeScript
- Tailwind CSS
- Radix / shadcn UI
- Lucide Icons
- Recharts
- Browser Fetch API

### Backend

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square)

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- JWT Authentication
- Argon2id
- TOTP MFA

### Database & Infrastructure

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Render](https://img.shields.io/badge/Render-000000?style=flat-square&logo=render&logoColor=white)

- PostgreSQL
- Redis
- Celery
- Docker
- Docker Compose
- Nginx
- Render

---

## 💻 Manual Windows Setup

Use three terminals if you want to run each component separately.

### One-Time Setup

From the project root:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
python scripts/setup.py
Copy-Item .env backend/.env
```

Edit:

```text
backend/.env
```

Change:

```dotenv
FRONTEND_ORIGIN=http://localhost:5173
```

For quick local development, omit `DATABASE_URL` to use SQLite.

For PostgreSQL:

```dotenv
DATABASE_URL=postgresql+psycopg://flowops:YOUR_URL_ENCODED_PASSWORD@localhost:5432/flowops
```

Create the `flowops` database and a dedicated PostgreSQL account first.

URL-encode special characters inside database passwords.

**pgAdmin 4 is optional** and is mainly useful for visually inspecting and managing PostgreSQL.

---

## 🐍 Backend

```powershell
cd backend

.venv/Scripts/python.exe -m alembic upgrade head

.venv/Scripts/python.exe -m app.manage seed

.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Development API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## ⚛️ Frontend

From the project root:

```powershell
npm install
npm run dev:frontend
```

Open:

```text
http://localhost:5173
```

The frontend automatically proxies `/api` requests to the FastAPI backend.

No manual API URL editing is required.

---

## 📧 Redis & Email

Email is optional for local development.

The primary approval workflow works without SMTP.

For email notifications:

```dotenv
SMTP_HOST=your.smtp.server
SMTP_PORT=587
SMTP_USERNAME=your_account
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_verified_sender@example.com
SMTP_STARTTLS=true
```

Restart the backend, Celery worker, and Celery beat after changing environment settings.

Without SMTP:

- Approval workflows continue working
- In-app notifications continue working
- Email messages are not sent

---

## 📂 Project Structure

| Path | Purpose |
| --- | --- |
| `app/page.tsx` | Main React application and workflows |
| `app/globals.css` | Product styles and responsive layouts |
| `frontend/` | Standalone Vite entry point and API proxy |
| `lib/flowops/data.ts` | Types and sample workspace adapter |
| `components/ui/` | Accessible shared UI components |
| `backend/app/main.py` | FastAPI routes |
| `backend/app/models.py` | SQLAlchemy database models |
| `backend/app/security.py` | Passwords, JWT, MFA and rate limiting |
| `backend/app/services.py` | Authorization and approval transactions |
| `backend/app/tasks.py` | Celery email, reminder and escalation tasks |
| `backend/app/manage.py` | Seed, admin creation and authenticator enrollment |
| `backend/alembic/` | Database migrations |
| `backend/tests/` | API, authorization and workflow tests |
| `docker/` | Docker and Nginx configuration |
| `docs/` | Security, API and verification documentation |

---

## 🌐 Production Deployment

### Current deployment

🚀 **Live:** [https://flowops-274o.onrender.com](https://flowops-274o.onrender.com)

FlowOps contains a single-service Render deployment configuration.

See:

```text
RENDER_DEPLOY.md
render.yaml
docs/SECURITY_AND_DEPLOYMENT.md
```

The Render deployment:

```text
React Frontend
      ↓
FastAPI
      ↓
PostgreSQL
```

The frontend is built during deployment and served by FastAPI from the same HTTPS origin.

Alembic migrations run automatically.

The demo workspace can also be seeded on first launch.

---

## 🔐 Production Security Requirements

This is a working development project, not an independently audited enterprise security product.

No application can honestly be described as **100% hack-proof**.

A real production deployment should include:

- HTTPS
- Strong production secrets
- MFA
- SMTP configuration
- Malware scanning
- Database backups
- Backup restoration testing
- Application monitoring
- Security logging
- Dependency scanning
- Regular security updates
- PostgreSQL kept private
- Redis kept private

AI-assisted routing may be added in the future.

**AI does not make approval decisions.**

---

## 🧪 Verification

Frontend:

```powershell
npm run check
npm run build:frontend
```

Backend:

```powershell
cd backend
.venv/Scripts/python.exe -m pytest -q
```

The test suite uses a disposable SQLite database and does not interact with normal application data.

PostgreSQL locking behavior, Docker services, SMTP delivery, Redis, and ClamAV should additionally be verified in the target deployment environment.

See:

```text
docs/VERIFICATION.md
```

for detailed verification information.

---

## 🎯 Core Approval Flow

```text
┌──────────────┐
│   Employee   │
│   Request    │
└──────┬───────┘
       ↓
┌──────────────┐
│   Manager    │
│   Approval   │
└──────┬───────┘
       ↓
┌──────────────┐
│ Department   │
│   Approval   │
└──────┬───────┘
       ↓
┌──────────────┐
│   Finance    │
│   Approval   │
└──────┬───────┘
       ↓
   ✅ Approved
```

---

## 🚀 FlowOps

<p align="center">
  <strong>Request. Review. Approve. Track.</strong>
</p>

<p align="center">
  <a href="https://flowops-274o.onrender.com">
    <img src="https://img.shields.io/badge/Try%20FlowOps-Live%20Demo-22c55e?style=for-the-badge&logo=render&logoColor=white" />
  </a>
</p>

<p align="center">
  Built with React, TypeScript, FastAPI, PostgreSQL, Redis and Celery.
</p>

---

Photo: **NEW DATA SERVICES / Unsplash**

Full attribution and license information is available in:

```text
docs/ASSETS.md
```
