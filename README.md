# ResumeAI

AI-powered resume analysis and job matching SaaS. Upload a resume, review AI-extracted
data, receive a transparent scored analysis, match against job descriptions, edit with
professional templates, and export a polished PDF.

Built as a production-grade portfolio project: phased development, tested, documented,
and deployable without a cloud account.

Python 3.12 | FastAPI | Next.js 14 | PostgreSQL 16 | Docker Compose

## Core Features

- Secure authentication with email verification and backend-managed sessions (Phase 3 - delivered)
- Account management: profile updates and authenticated password changes (Phase 4 - delivered)
- PDF/DOCX resume upload with validation, text extraction, and user review (Phase 5)
- Explainable resume scoring plus LLM-generated improvement suggestions (Phase 6)
- Job description matching with skill-gap and keyword-coverage reports (Phase 7)
- Resume editor with four templates, accent colors, and PDF export (Phase 8)
- Analysis and match history scoped to the authenticated user (Phase 9)

All AI runs on the backend behind a provider abstraction (Gemini free tier default,
mock provider in every test). Deterministic scoring is computed separately from LLM
text and every report stores its scoring_version. Honest disclaimers throughout:
scores are estimates, never ATS verdicts.

## Tech Stack

| Layer    | Technology                                                      |
| -------- | --------------------------------------------------------------- |
| Frontend | Next.js 14 (App Router), TypeScript strict, Tailwind, Radix UI   |
| Backend  | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x               |
| Database | PostgreSQL 16 (migrations via Alembic)                          |
| AI       | Provider abstraction: Gemini free tier default, mock in tests   |
| Infra    | Docker Compose, GitHub Actions CI (Phase 11)                    |
| Deploy   | Vercel (frontend) + container platform (backend) + Neon (DB)    |

## Project Structure

```text
resumeai/
|-- backend/           # FastAPI application (app/, tests/, alembic/, Dockerfile)
|-- frontend/          # Next.js application (src/, Dockerfile)
`-- docker-compose.yml # Local orchestration: db + backend + frontend
## Quickstart (Docker)
Prerequisite: Docker Desktop. Node.js is only needed for frontend tooling outside Docker.

git clone https://github.com/Abhisherk01/ResumeAI.git
cd ResumeAI
cp backend/.env.example backend/.env
docker compose up --build

| Service   | URL                              |
| --------- | -------------------------------- |
| Frontend  | http://localhost:3000            |
| API docs  | http://localhost:8000/docs       |
| Health    | http://localhost:8000/health     |
| Readiness | http://localhost:8000/ready      |


Useful Commands

docker compose exec backend pytest -v           # backend tests
docker compose exec backend ruff check .        # backend lint
docker compose exec backend ruff format .       # backend format
docker compose exec frontend npm test           # frontend component tests
docker compose exec frontend npx tsc --noEmit   # frontend type check
docker compose exec frontend npm run lint       # frontend lint
docker compose exec frontend npm run format     # frontend format

Never run npm run build while the frontend dev container is running - both write to
the same .next directory. Use this sequence:

bash
docker compose stop frontend
docker compose run --rm frontend npm run build
Remove-Item -Recurse -Force frontend\.next   # PowerShell; rm -rf frontend/.next elsewhere
docker compose start frontend

Authentication and Account Management (Phases 3-4)
Server-side sessions. The cookie holds a random 256-bit token; only its SHA-256
hash is stored (no JWTs). Sessions expire after 7 days and can be revoked individually
or all at once.
CSRF double-submit. The JS-readable csrf_token cookie must be echoed in the
X-CSRF-Token header on every mutating request; its hash is bound to the session row.
Passwords. Argon2id (OWASP-aligned defaults), 8-128 characters, no composition
rules (NIST 800-63B). Weak/legacy hashes are transparently upgraded on login.
Email tokens. Verification (24 h) and reset (30 min) tokens are single-use, hashed
at rest, atomically consumed, and superseded when reissued. A password reset revokes
every session.
Account changes (Phase 4). Display-name updates via PATCH /auth/me. An
authenticated password change (POST /auth/me/password) requires the current password
and revokes every OTHER session while keeping the one performing the change (a wrong
current password returns 400 invalid_current_password, shown inline by the UI).
Email address changes are deferred: they require verifying the NEW address first.
Anti-enumeration. Registration and reset responses are identical whether or not an
email has an account; all login failures share one generic error, and the unknown-email
path burns equivalent CPU time.
Rate limiting (sliding window, per IP):
Endpoint group
Limit
Window
login    5    15 min
register    5    60 min
password reset    3    60 min
token endpoints (verify/reset confirm)    10    15 min

Retry-After is exposed via CORS so the UI shows a precise countdown.
Security headers. nosniff, frame-deny, strict referrer policy, API-profile CSP,
no-store, permissions policy; HSTS in production only.
Email in development
No SMTP needed: the dev transport prints full emails - including verification and reset
links - to the backend log. Grab the newest link, confirm the EMAIL to= address, and
open it in a browser:

bash
docker compose logs backend --tail 50

A real SMTP provider lands in Phase 12 behind the same EmailSender interface.

Manual E2E Checklist (auth and account)
Run against http://localhost:3000 after any auth-adjacent change:

Logged out: /dashboard redirects to /login; landing page renders normally.
Register: "Check your inbox" state; exactly one email in the backend log.
Newest verification link: "Email verified." Superseded links: "invalid or has
expired" with no retry button.
Login: lands on /dashboard; sidebar shows name and email; theme switcher works.
Wrong password: "Email or password is incorrect." (identical for unknown emails).
Unverified login: "Please verify your email address before signing in."
Reset loop: forgot-password -> link from logs -> new password -> "Password updated";
old session dead; new password logs in.
Rate limiting: 6 rapid failed logins; the 6th shows "Try again in about 15 minutes."
Profile (Phase 4): change display name in /settings; sidebar updates instantly
(no refresh) and persists across a reload.
Password change (Phase 4): with two sessions open, change the password in one; the
other session is kicked to /login on its next request, the changing session stays
alive, and a wrong current password shows inline on the field.
Development Status
Phase
Scope
Status
0    Requirements & architecture    Complete
1    Project initialization    Complete
2    Design system & landing page    Complete
3    Authentication & user management    Complete
4    Dashboard & settings    Complete
5    Resume upload & document processing    Complete
6    AI analysis    Complete
7    Job matching    Complete
8    Editor, templates & PDF export    Planned
9    History & reports    Planned
10    Integration, security & performance    Planned
11    Docker & CI    Planned
12    Deployment (Vercel + Render/Railway + Neon)    Planned
13    Portfolio documentation    Planned

Security Notes
Local Postgres credentials in docker-compose.yml are for development only. Production
secrets will be platform-managed (Phase 12). .env files are git-ignored and must
never be committed.



