# **ResumeAI**

AI-powered resume analysis and job matching SaaS. Upload a resume, review AI-extracteddata, receive a transparent scored analysis, match against job descriptions, edit withprofessional templates, and export a polished PDF.

Built as a production-grade portfolio project: phased development, tested, documented,and deployable without a cloud account.

Python 3.12 | FastAPI | Next.js 14 | PostgreSQL 16 | Docker Compose

## **Core Features**

- Secure authentication with email verification and backend-managed sessions (Phase 3 - delivered)
- PDF/DOCX resume upload with validation, text extraction, and user review (Phase 5)
- Explainable resume scoring plus LLM-generated improvement suggestions (Phase 6)
- Job description matching with skill-gap and keyword-coverage reports (Phase 7)
- Resume editor with four templates, accent colors, and PDF export (Phase 8)
- Analysis and match history scoped to the authenticated user (Phase 9)

All AI runs on the backend behind a provider abstraction (Gemini free tier default,mock provider in every test). Deterministic scoring is computed separately from LLMtext and every report stores its scoring_version. Honest disclaimers throughout:scores are estimates, never ATS verdicts.

## **Tech Stack**


| **Layer** | **Technology**                                                 |
| --------- | -------------------------------------------------------------- |
| Frontend  | Next.js 14 (App Router), TypeScript strict, Tailwind, Radix UI |
| Backend   | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x              |
| Database  | PostgreSQL 16 (migrations via Alembic)                         |
| AI        | Provider abstraction: Gemini free tier default, mock in tests  |
| Infra     | Docker Compose, GitHub Actions CI (Phase 11)                   |
| Deploy    | Vercel (frontend) + container platform (backend) + Neon (DB)   |


## **Project Structure**

```text
resumeai/|-- backend/           # FastAPI application (app/, tests/, alembic/, Dockerfile)|-- frontend/          # Next.js application (src/, Dockerfile)`-- docker-compose.yml # Local orchestration: db + backend + frontend
```

## **Quickstart (Docker)**

Prerequisite: Docker Desktop. Node.js is only needed for frontend tooling outside Docker.

```bash
git clone https://github.com/Abhisherk01/ResumeAI.gitcd ResumeAIcp backend/.env.example backend/.envdocker compose up --build
```


| **Service** | **URL**                                                              |
| ----------- | -------------------------------------------------------------------- |
| Frontend    | ++**[http://localhost:3000](http://localhost:3000)**++               |
| API docs    | ++**[http://localhost:8000/docs](http://localhost:8000/docs)**++     |
| Health      | ++**[http://localhost:8000/health](http://localhost:8000/health)**++ |
| Readiness   | ++**[http://localhost:8000/ready](http://localhost:8000/ready)**++   |


## **Useful Commands**

```bash
docker compose exec backend pytest -v           # backend testsdocker compose exec backend ruff check .        # backend lintdocker compose exec backend ruff format .       # backend formatdocker compose exec frontend npm test           # frontend component testsdocker compose exec frontend npx tsc --noEmit   # frontend type checkdocker compose exec frontend npm run lint       # frontend lintdocker compose exec frontend npm run format     # frontend format
```

Never run `npm run build` while the frontend dev container is running - both write tothe same `.next` directory. Use this sequence:

```bash
docker compose stop frontenddocker compose run --rm frontend npm run buildRemove-Item -Recurse -Force frontend\.next   # PowerShell; rm -rf frontend/.next elsewheredocker compose start frontend
```

## **Authentication (Phase 3)**

- **Server-side sessions.** The cookie holds a random 256-bit token; only its SHA-256hash is stored (no JWTs). Sessions expire after 7 days and can be revoked individuallyor all at once.
- **CSRF double-submit.** The JS-readable `csrf_token` cookie must be echoed in the`X-CSRF-Token` header on every mutating request; its hash is bound to the session row.
- **Passwords.** Argon2id (OWASP-aligned defaults), 8-128 characters, no compositionrules (NIST 800-63B). Weak/legacy hashes are transparently upgraded on login.
- **Email tokens.** Verification (24 h) and reset (30 min) tokens are single-use, hashedat rest, atomically consumed, and superseded when reissued. A password reset revokesevery session.
- **Anti-enumeration.** Registration and reset responses are identical whether or not anemail has an account; all login failures share one generic error, and the unknown-emailpath burns equivalent CPU time.
- **Rate limiting** (sliding window, per IP):

  | **Endpoint group**                     | **Limit** | **Window** |
  | -------------------------------------- | --------- | ---------- |
  | login                                  | 5         | 15 min     |
  | register                               | 5         | 60 min     |
  | password reset                         | 3         | 60 min     |
  | token endpoints (verify/reset confirm) | 10        | 15 min     |

  `Retry-After` is exposed via CORS so the UI shows a precise countdown.
- **Security headers.** nosniff, frame-deny, strict referrer policy, API-profile CSP,`no-store`, permissions policy; HSTS in production only.

### **Email in development**

No SMTP needed: the dev transport prints full emails - including verification and resetlinks - to the backend log. Grab the newest link, confirm the `EMAIL to=` address, andopen it in a browser:

```bash
docker compose logs backend --tail 50
```

A real SMTP provider lands in Phase 12 behind the same `EmailSender` interface.

## **Manual E2E Checklist (auth)**

Run against ++**[http://localhost:3000](http://localhost:3000)**++ after any auth-adjacent change:

1. Logged out: `/dashboard` redirects to `/login`; landing page renders normally.
2. Register: "Check your inbox" state; exactly one email in the backend log.
3. Newest verification link: "Email verified." Superseded links: "invalid or hasexpired" with no retry button.
4. Login: lands on `/dashboard`; sidebar shows name and email; theme switcher works.
5. Wrong password: "Email or password is incorrect." (identical for unknown emails).
6. Unverified login: "Please verify your email address before signing in."
7. Reset loop: forgot-password -> link from logs -> new password -> "Password updated";old session dead; new password logs in.
8. Rate limiting: 6 rapid failed logins; the 6th shows "Try again in about 15 minutes."

## **Development Status**


| **Phase** | **Scope**                                   | **Status** |
| --------- | ------------------------------------------- | ---------- |
| 0         | Requirements & architecture                 | Complete   |
| 1         | Project initialization                      | Complete   |
| 2         | Design system & landing page                | Complete   |
| 3         | Authentication & user management            | Complete   |
| 4         | Dashboard & settings                        | Planned    |
| 5         | Resume upload & document processing         | Planned    |
| 6         | AI analysis                                 | Planned    |
| 7         | Job matching                                | Planned    |
| 8         | Editor, templates & PDF export              | Planned    |
| 9         | History & reports                           | Planned    |
| 10        | Integration, security & performance         | Planned    |
| 11        | Docker & CI                                 | Planned    |
| 12        | Deployment (Vercel + Render/Railway + Neon) | Planned    |
| 13        | Portfolio documentation                     | Planned    |


## **Security Notes**

Local Postgres credentials in docker-compose.yml are for development only. Productionsecrets will be platform-managed (Phase 12). `.env` files are git-ignored and mustnever be committed.


