ResumeAI
AI-powered resume analysis and job matching SaaS. Upload a resume, reviewAI-extracted data, receive a transparent scored analysis, match against jobdescriptions, edit with professional templates, and export a polished PDF.

Built as a production-grade portfolio project — phased development, tested,documented, and deployable without a cloud account.

PythonFastAPINext.jsPostgreSQLDocker

Planned Core Features
Secure authentication with email verification and backend-managed sessions
PDF/DOCX resume upload with validation, text extraction, and user review
Explainable resume scoring plus LLM-generated improvement suggestions
Job description matching with skill-gap and keyword-coverage reports
Resume editor with four templates, accent colors, and PDF export
Analysis and match history scoped to the authenticated user


Tech Stack
Layer	Technology
Frontend	Next.js 14 (App Router), TypeScript (strict), Tailwind CSS, shadcn/ui
Backend	Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x
Database	PostgreSQL 16 (migrations via Alembic)
AI	LLM provider abstraction (Gemini free tier default, mock in tests)
Infra	Docker Compose, GitHub Actions (CI added in Phase 11)
Deploy	Vercel (frontend) + container platform (backend) + Neon (DB)


Project Structure
resumeai/├── backend/           # FastAPI application (app/, tests/, Dockerfile)├── frontend/          # Next.js application (src/, Dockerfile)└── docker-compose.yml # Local orchestration: db + backend + frontend


Quickstart (Docker)
Prerequisites: Docker Desktop.Node.js 20+ is only needed for frontend tooling outside Docker.

git clone <your-repo-url>cd resumeaicp backend/.env.example backend/.envdocker compose up --build

Service	        URL
Frontend	http://localhost:3000
API docs	http://localhost:8000/docs
Health	    http://localhost:8000/health
Readiness	http://localhost:8000/ready


Useful Commands
docker compose exec backend pytest -v        # backend testsdocker compose exec backend ruff check .     # backend lintdocker compose exec backend ruff format .    # backend formatdocker compose exec frontend npm run lint    # frontend lintcd frontend && npm run format                # frontend format
Never run npm run build while the dev server container is running — bothwrite to the same .next directory. Stop the container first.


Development Status
Phase	Scope	                                Status
0       Requirements & architecture	            ✅ Complete
1	    Project initialization	                ✅ Complete
2	    Design system & landing page	        🚧 In progress
3–13	Auth → AI → Matching → Editor → Deploy	⬜ Planned


Security Notes
Local Postgres credentials in docker-compose.yml are for development only.All production secrets will be platform-managed (Phase 12). .env files aregit-ignored and must never be committed.
