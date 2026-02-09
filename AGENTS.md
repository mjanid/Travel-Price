# AGENTS.md

## Purpose
This file documents repository-specific guidance for contributors and automated agents.
Its scope is the entire repository unless overridden by a nested `AGENTS.md`.

## Repository layout
- `backend/`: FastAPI service, scrapers, notifications, and Celery workers/beat.
- `frontend/`: Next.js app (React 19 + Tailwind + React Query + Zustand).
- `docker-compose.yml`: Local orchestration for Postgres, Redis, backend, Celery, and frontend.

## Local setup (Docker-first)
- Start the full stack:
  - `docker-compose up --build`
- Service endpoints:
  - Backend: `http://localhost:8000`
  - Frontend: `http://localhost:3000`
- Environment:
  - The compose file loads `.env` for backend and Celery services.
  - The frontend uses `NEXT_PUBLIC_API_URL` to reach the backend.

## Backend workflow
- Run locally (outside Docker):
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Key locations:
  - Settings: `backend/app/core/config.py`
  - Database: `backend/app/core/database.py` and `backend/app/models/`
  - API routes: `backend/app/api/`
  - Celery: `backend/app/workers/`
  - Migrations: `backend/migrations/`
- Tests:
  - `pytest`

## Frontend workflow
- Install deps: `npm install`
- Dev server: `npm run dev`
- Build: `npm run build`
- Lint: `npm run lint`
- Tests: `npm test`

## Conventions & tips
- Prefer updating documentation in this file when workflows change.
- Ensure Postgres and Redis are running before starting backend or Celery.
- Celery workers depend on Redis and the backend codebase.
