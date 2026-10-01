ResumeAI
AI-powered resume analysis and job matching SaaS. Upload a resume, reviewAI-extracted data, receive a transparent scored analysis, match against jobdescriptions, edit with professional templates, and export a polished PDF.

Built as a production-grade portfolio project — phased development, tested,documented, and deployable without a cloud account.

Tech Stack
Layer	                Technology
Frontend	        Next.js 14 (App Router), TypeScript (strict), Tailwind CSS, shadcn/ui
Backend	            Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x
Database	        PostgreSQL 16 (migrations via Alembic)
AI	                LLM provider abstraction (Gemini free tier default, mock in tests)
Infra	            Docker Compose, GitHub Actions (CI added in Phase 11)
Deploy	            Vercel (frontend) + container platform (backend) + Neon (DB)

Quickstart (Docker)
Prerequisites: Docker Desktop, Node.js 20+ (for frontend tooling).

git clone <your-repo-url> && cd resumeaicp backend/.env.example backend/.envdocker compose up --build

| Service   | URL                            |
|-----------|--------------------------------|
| Frontend  | http://localhost:3000          |
| API docs  | http://localhost:8000/docs     |
| Health    | http://localhost:8000/health   |
| Readiness | http://localhost:8000/ready    |


Useful Commands

docker compose exec backend pytest -v      # backend tests
docker compose exec backend ruff check .   # backend lint
docker compose exec backend ruff format .  # backend format
cd frontend && npm run lint                # frontend lint
cd frontend && npm run format              # frontend format


Development Status

| Phase | Scope                              | Status |
|-------|------------------------------------|--------|
| 0     | Requirements & architecture        | ✅ Complete |
| 1     | Project initialization             | ✅ Complete |
| 2     | Design system & landing page       | ⬜ Next |
| 3–13  | Auth → AI → Matching → Editor → Deploy | ⬜ Planned |


Security Notes
Local Postgres credentials in docker-compose.yml are for development only.
All production secrets will be platform-managed (Phase 12). .env files are
git-ignored and must never be committed.