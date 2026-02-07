# CLAUDE.md — Travel Price Scraper Platform

## Project Overview

A platform that monitors and scrapes pricing data from travel websites (flights, hotels, car rentals). Users set target price thresholds for planned trips and receive real-time alerts when prices drop below their targets.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI (async), Celery + Redis (task queue) |
| Scraping | Playwright (JS-rendered), httpx + BeautifulSoup (static) |
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS, TanStack Query, Zustand, Recharts |
| Database | PostgreSQL 16 + TimescaleDB (time-series), Redis (cache/queue) |
| Infrastructure | Docker + Docker Compose, GitHub Actions CI/CD |
| Monitoring | Sentry (errors), Prometheus + Grafana (metrics) |

## Project Structure

```
travel-price-scraper/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # FastAPI route handlers (auth, alerts, prices, trips)
│   │   ├── core/             # Config, security, settings
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic layer
│   │   ├── scrapers/         # Scraper modules (base.py + flights/, hotels/, car_rentals/)
│   │   ├── workers/          # Celery tasks and job scheduling
│   │   └── notifications/    # Email, push, webhook alert dispatchers
│   ├── migrations/           # Alembic DB migrations
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router pages
│   │   ├── components/       # Reusable UI components
│   │   ├── lib/              # API client, utilities, types
│   │   └── hooks/            # Custom React hooks
│   ├── public/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Data Model Core Entities

- **User** — authentication, preferences
- **Trip** — planned trip (origin/destination IATA codes, dates, travelers)
- **PriceWatch** — monitoring rule (trip + provider + target price + alert config)
- **PriceSnapshot** — immutable scraped price record (provider, price, currency, timestamp)
- **Alert** — sent notification log (type, channel, status, sent_at)

## Build & Run Commands

### Backend

```bash
# Install dependencies
cd backend && pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload

# Run tests
pytest

# Run Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Run Celery Beat scheduler
celery -A app.workers.celery_app beat --loglevel=info

# Run Alembic migrations
alembic upgrade head
```

### Frontend

```bash
cd frontend && npm install

# Dev server
npm run dev

# Build
npm run build

# Tests
npm run test

# Lint
npm run lint
```

### Docker

```bash
docker-compose up        # Start all services
docker-compose up -d     # Detached mode
```

## Architecture Patterns

### Backend: Service Layer Pattern

Routes → Services → Repositories → DB. Never put business logic in route handlers.

```
api/v1/trips.py  →  services/trip_service.py  →  models/trip.py  →  PostgreSQL
```

- Use `async/await` for all I/O (DB, HTTP, scraping)
- Dependency injection via FastAPI `Depends()`
- Environment variables via `pydantic-settings` (never hardcode secrets)

### Scraping Architecture

- Every scraper inherits `BaseScraper` and implements `async scrape(query: ScrapeQuery) -> list[PriceResult]`
- Scrapers are stateless and idempotent
- Rate limiting per-provider via Redis
- Proxy rotation built into base class
- Failed scrapes retry with exponential backoff (max 3 retries)
- All scraped data stored as immutable timestamped snapshots

### Alert System

- Celery Beat schedules periodic scrape jobs per active PriceWatch
- New price < target → create Alert → send notification
- Cooldown: max 1 alert per PriceWatch per 6 hours (configurable)

## Coding Conventions

### Python (Backend)

- Type hints on all function signatures
- Pydantic models for all validation
- `snake_case` for functions/variables, `PascalCase` for classes
- Google-style docstrings for all public functions and classes
- `async/await` for all I/O-bound operations

### TypeScript (Frontend)

- Strict TypeScript — no `any` types
- Functional components with hooks only (no class components)
- Co-locate component files: `ComponentName/index.tsx`, `types.ts`, `hooks.ts`
- API calls through centralized client (`lib/api.ts`)
- `zod` for runtime validation of API responses

### General

- All times in UTC; convert to local only in frontend display
- Monetary values stored as integers (cents) to avoid floating point issues
- API response envelope: `{ data, meta, errors }`
- Git commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`

## Testing Strategy

| Area | Tools | Notes |
|------|-------|-------|
| Backend | pytest, pytest-asyncio, factory_boy | 80%+ coverage on services and scrapers |
| Scrapers | VCR.py | Record/replay to avoid live requests in CI |
| Frontend | Vitest, React Testing Library | Component and hook tests |
| E2E | Playwright | Critical user flows |

## MVP Feature Roadmap (Build Order)

Build sequentially. Each feature must pass tests before starting the next.

1. **User Authentication** — JWT auth with register/login/refresh endpoints
2. **Trip CRUD** — Create, read, update, delete trips with pagination
3. **Price Watch Management** — CRUD for price watches linked to trips
4. **Flight Scraper** — BaseScraper + first provider implementation
5. **Scheduled Scraping & Price Storage** — Celery Beat + PriceSnapshot storage
6. **Price Alert Notifications** — Threshold comparison + email alerts
7. **Frontend: Auth & Trip Management** — Login, register, dashboard, trip forms
8. **Frontend: Price Watch & Dashboard** — Price charts, watch cards, alert history

## UI/UX Quick Reference

- **Design:** Clean, minimal, white/light-gray background, card-based layouts
- **Colors:** Blue `#2563EB` (primary), Green `#16A34A` (price drops), Red `#DC2626` (price increases)
- **Typography:** Inter or system font, hierarchy via font weight
- **Cards:** 8px rounded corners, subtle shadow, 16–24px padding
- **Mobile:** Fully responsive, stacking cards, hamburger nav

### Routes

`/login` · `/register` · `/dashboard` · `/trips` · `/trips/new` · `/trips/[id]` · `/watches/[id]` · `/settings`

## Security

- JWT: short-lived access tokens + refresh tokens
- Rate limit all public API endpoints (per-user and per-IP)
- Scraper credentials and proxy configs in environment variables only
- Input sanitization on all user-provided search parameters
- CORS configured for frontend domain only

## Agent Workflow Guidelines

- Build one feature per session following the roadmap order
- Run and pass all tests before moving to the next feature
- Reference this file at the start of every new session
- Keep sessions focused — start a new session if context grows too large
- Do not skip ahead in the roadmap — each feature builds on the previous
- Commit after each completed feature: `feat: implement trip CRUD with tests`
- When in doubt about UI/UX decisions, ask the user rather than assuming
