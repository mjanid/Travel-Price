# CLAUDE.md — Travel Price Scraper Platform

## Project Overview

A platform that monitors and scrapes pricing data from travel websites (flights, hotels, car rentals). Users set target price thresholds for planned trips and receive real-time alerts when prices drop below their targets.

## Current Implementation Status

All 8 MVP features have been implemented:

| # | Feature | Status |
|---|---------|--------|
| 1 | User Authentication (JWT) | Done |
| 2 | Trip CRUD with pagination | Done |
| 3 | Price Watch Management | Done |
| 4 | Flight Scraper (BaseScraper + Google Flights) | Done |
| 5 | Scheduled Scraping & Price Storage (Celery Beat) | Done |
| 6 | Price Alert Notifications (threshold + email) | Done |
| 7 | Frontend: Auth & Trip Management | Done |
| 8 | Frontend: Price Watch, Dashboard & Alert History | Done |

**Not yet implemented:** Hotel/car rental scrapers, Playwright (JS-rendered scraping), full CI/CD pipeline, Sentry monitoring, Prometheus/Grafana.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI 0.115+, Celery 5.4 + Redis |
| Scraping | httpx 0.28 + BeautifulSoup4 (static pages) |
| Frontend | Next.js 16 (App Router), TypeScript 5, React 19, Tailwind CSS 4, TanStack Query 5, Zustand 5, Recharts 3 |
| Database | PostgreSQL 16 (asyncpg), Redis (cache/queue) |
| Auth | python-jose (JWT), passlib + bcrypt |
| Validation | Pydantic 2.10 (backend), Zod 4 (frontend) |
| Testing | pytest + pytest-asyncio + factory-boy + respx (backend), Vitest + React Testing Library (frontend) |

## Project Structure

```
Travel-Price/
├── backend/
│   ├── app/
│   │   ├── api/v1/               # FastAPI route handlers
│   │   │   ├── auth.py           # Register, login, refresh, profile
│   │   │   ├── trips.py          # Trip CRUD
│   │   │   ├── watches.py        # PriceWatch CRUD + alerts-per-watch
│   │   │   ├── alerts.py         # Alert history
│   │   │   └── prices.py         # Manual scrape trigger, price history
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic-settings configuration
│   │   │   ├── database.py       # SQLAlchemy async engine + session
│   │   │   └── security.py       # JWT token creation, password hashing
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── trip.py           # TripType enum (flight, hotel, car_rental)
│   │   │   ├── price_watch.py
│   │   │   ├── price_snapshot.py # Immutable scraped price records
│   │   │   └── alert.py
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   │   ├── auth.py
│   │   │   ├── trip.py
│   │   │   ├── price_watch.py
│   │   │   ├── price_snapshot.py
│   │   │   ├── alert.py
│   │   │   └── common.py         # ApiResponse, PaginatedApiResponse
│   │   ├── services/             # Business logic layer
│   │   │   ├── auth_service.py
│   │   │   ├── trip_service.py
│   │   │   ├── price_watch_service.py
│   │   │   ├── scraper_service.py
│   │   │   ├── scheduled_scrape_service.py
│   │   │   └── alert_service.py
│   │   ├── scrapers/
│   │   │   ├── base.py           # BaseScraper (retry, rate-limit, proxy rotation)
│   │   │   ├── types.py          # ScrapeQuery, PriceResult, ScrapeError
│   │   │   ├── registry.py       # Provider name → scraper class mapping
│   │   │   └── flights/
│   │   │       └── google_flights.py
│   │   ├── workers/
│   │   │   ├── celery_app.py     # Celery config + Beat schedule
│   │   │   ├── tasks.py          # scrape_all_active_trips, scrape_single_trip
│   │   │   └── db.py             # Worker database session helper
│   │   ├── notifications/
│   │   │   ├── base.py           # NotificationPayload
│   │   │   └── email.py          # Email dispatcher
│   │   └── main.py               # FastAPI app factory, router registration
│   ├── migrations/               # Alembic migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial_schema.py  # All 5 tables: users, trips, price_watches, price_snapshots, alerts
│   ├── Dockerfile                # Backend container image
│   ├── entrypoint.sh             # Runs migrations then starts server
│   ├── tests/                    # 18 test files (~3200 lines)
│   │   ├── conftest.py           # Async fixtures, in-memory SQLite setup
│   │   ├── factories.py          # Factory Boy model factories
│   │   ├── test_auth_service.py
│   │   ├── test_auth_routes.py
│   │   ├── test_trip_service.py
│   │   ├── test_trip_routes.py
│   │   ├── test_watch_routes.py
│   │   ├── test_price_watch_service.py
│   │   ├── test_prices_routes.py
│   │   ├── test_scraper_base.py
│   │   ├── test_flight_scraper.py
│   │   ├── test_scraper_service.py
│   │   ├── test_scheduled_scrape_service.py
│   │   ├── test_worker_tasks.py
│   │   ├── test_alert_service.py
│   │   ├── test_alert_routes.py
│   │   ├── test_celery_config.py
│   │   └── test_notification.py
│   ├── pyproject.toml
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx        # Root layout
│   │   │   ├── page.tsx          # Home (redirects)
│   │   │   ├── globals.css
│   │   │   ├── providers.tsx     # TanStack Query + Zustand providers
│   │   │   ├── (auth)/           # Unauthenticated routes
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   └── (protected)/      # Auth-guarded routes
│   │   │       ├── layout.tsx    # Auth guard wrapper
│   │   │       ├── dashboard/page.tsx
│   │   │       ├── trips/page.tsx, new/page.tsx, [id]/page.tsx, [id]/edit/page.tsx
│   │   │       ├── watches/page.tsx, [id]/page.tsx
│   │   │       └── settings/page.tsx
│   │   ├── components/
│   │   │   ├── ui/               # Button, Input, Card, Badge
│   │   │   ├── auth/             # LoginForm, RegisterForm
│   │   │   ├── trips/            # TripForm, TripCard, TripList
│   │   │   ├── watches/          # WatchForm, WatchCard, WatchList
│   │   │   ├── alerts/           # AlertList
│   │   │   ├── charts/           # PriceChart (Recharts)
│   │   │   └── layout/           # Header
│   │   ├── hooks/                # useAuth, useTrips, useWatches, usePrices, useAlerts
│   │   ├── lib/
│   │   │   ├── api.ts            # Centralized fetch client with token refresh
│   │   │   ├── types.ts          # TypeScript interfaces
│   │   │   ├── validators.ts     # Zod schemas
│   │   │   ├── utils.ts
│   │   │   └── __tests__/        # Validator + util tests
│   │   └── stores/
│   │       └── auth-store.ts     # Zustand auth state
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── vitest.config.ts
│   ├── Dockerfile                # Frontend container image
│   ├── eslint.config.mjs
│   └── postcss.config.mjs
├── .github/
│   └── workflows/
│       └── codeql.yml            # CodeQL security scanning (Python + JS/TS)
├── .env.example                  # Environment variable template
├── .gitignore
├── docker-compose.yml            # Full-stack dev orchestration
├── CLAUDE.md
├── PLAN-FEATURE-4.md
└── README.md
```

## Data Model Core Entities

- **User** — id (UUID), email, hashed_password, full_name, is_active, timestamps
- **Trip** — id (UUID), user_id (FK), origin/destination (IATA codes), dates, travelers, trip_type (enum: flight/hotel/car_rental), notes, timestamps
- **PriceWatch** — id (UUID), user_id (FK), trip_id (FK), provider, target_price (cents), currency, is_active, alert_cooldown_hours, timestamps
- **PriceSnapshot** — id (UUID), trip_id (FK), user_id (FK), provider, price (cents), currency, cabin_class, airline, flight times, stops, raw_data (JSON), scraped_at, created_at
- **Alert** — id (UUID), price_watch_id (FK), user_id (FK), price_snapshot_id (FK), alert_type, channel, status, target_price, triggered_price, message, sent_at, created_at

All models use UUID primary keys. Cascade deletes are configured on foreign keys. Initial Alembic migration (`001_initial`) covers all 5 tables.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | JWT login (access + refresh tokens) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Current user profile |
| PATCH | `/api/v1/auth/me` | Update profile |
| POST | `/api/v1/trips/` | Create trip |
| GET | `/api/v1/trips/` | List trips (paginated) |
| GET | `/api/v1/trips/{trip_id}` | Get trip |
| PATCH | `/api/v1/trips/{trip_id}` | Update trip |
| DELETE | `/api/v1/trips/{trip_id}` | Delete trip |
| POST | `/api/v1/trips/{trip_id}/scrape` | Trigger manual scrape |
| GET | `/api/v1/trips/{trip_id}/prices` | Price history (paginated, filterable by provider) |
| GET | `/api/v1/trips/{trip_id}/watches` | List watches for trip |
| POST | `/api/v1/watches/` | Create price watch |
| GET | `/api/v1/watches/` | List watches (paginated) |
| GET | `/api/v1/watches/{watch_id}` | Get watch |
| PATCH | `/api/v1/watches/{watch_id}` | Update watch |
| DELETE | `/api/v1/watches/{watch_id}` | Delete watch |
| GET | `/api/v1/watches/{watch_id}/alerts` | Alerts for a watch |
| GET | `/api/v1/alerts/` | List user alerts (paginated) |
| GET | `/api/v1/alerts/{alert_id}` | Get alert detail |

All endpoints require JWT Bearer token (except register/login). Rate limited at 60 req/min. CORS configured for frontend domain.

## Build & Run Commands

### Docker (recommended)

```bash
cp .env.example .env                    # Create env file (edit as needed)
docker compose up --build               # Start all services
docker compose down                     # Stop all services
docker compose down -v                  # Stop and remove volumes
```

Services: `postgres` (:5432), `redis` (:6379), `backend` (:8000), `celery-worker`, `celery-beat`, `frontend` (:3000). The backend entrypoint runs `alembic upgrade head` automatically before starting.

### Backend (manual)

```bash
cd backend && pip install -e ".[dev]"   # Install with dev dependencies
uvicorn app.main:app --reload           # Dev server
pytest                                   # Run tests
pytest --cov=app                        # Tests with coverage

# Celery (requires Redis running)
celery -A app.workers.celery_app worker --loglevel=info   # Worker
celery -A app.workers.celery_app beat --loglevel=info     # Scheduler

# Alembic
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m ""   # Generate new migration
```

### Frontend (manual)

```bash
cd frontend && npm install
npm run dev          # Dev server
npm run build        # Production build
npm run test         # Run Vitest tests
npm run test:watch   # Watch mode
npm run lint         # ESLint
```

## Architecture Patterns

### Backend: Service Layer Pattern

Routes -> Services -> Models -> DB. Business logic lives in services, never in route handlers.

```
api/v1/trips.py  ->  services/trip_service.py  ->  models/trip.py  ->  PostgreSQL
```

- `async/await` for all I/O (DB, HTTP, scraping)
- Dependency injection via FastAPI `Depends()`
- Environment variables via `pydantic-settings` (never hardcode secrets)
- All services take `AsyncSession` as constructor argument

### Scraping Architecture

- Every scraper inherits `BaseScraper` and implements `async scrape(query: ScrapeQuery) -> list[PriceResult]`
- Public entry point is `execute()` which wraps `scrape()` with rate limiting + retry
- Scrapers are stateless and idempotent
- Rate limiting per-provider via Redis (optional, skipped if Redis unavailable)
- Proxy rotation and User-Agent rotation built into base class
- Failed scrapes retry with exponential backoff (max 3 retries)
- All scraped data stored as immutable timestamped PriceSnapshot records
- Currently only `google_flights` provider is implemented

### Alert System

- Celery Beat schedules periodic scrape jobs per active PriceWatch
- Workers fan out: `scrape_all_active_trips` -> individual `scrape_single_trip` tasks
- New price < target -> create Alert -> send email notification
- Cooldown: max 1 alert per PriceWatch per 6 hours (configurable via `alert_cooldown_hours`)

### Frontend Architecture

- Next.js App Router with route groups: `(auth)` for public, `(protected)` for authenticated
- Auth guard in `(protected)/layout.tsx` redirects unauthenticated users
- Centralized API client (`lib/api.ts`) with automatic JWT token refresh
- TanStack Query for server state, Zustand for client state (auth store)
- Zod validation on API responses

## Coding Conventions

### Python (Backend)

- Type hints on all function signatures
- Pydantic models for all request/response validation
- `snake_case` for functions/variables, `PascalCase` for classes
- Google-style docstrings for all public functions and classes
- `async/await` for all I/O-bound operations
- Monetary values stored as integers (cents)
- All times in UTC

### TypeScript (Frontend)

- Strict TypeScript — no `any` types
- Functional components with hooks only (no class components)
- Co-locate component files: `ComponentName/index.tsx`, `types.ts`, `hooks.ts`
- API calls through centralized client (`lib/api.ts`)
- Zod for runtime validation of API responses

### General

- All times in UTC; convert to local only in frontend display layer
- Monetary values stored as integers (cents) to avoid floating point issues
- API response envelope: `{ data, meta, errors }`
- Git commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`

## Testing Strategy

| Area | Tools | Notes |
|------|-------|-------|
| Backend services | pytest, pytest-asyncio, factory-boy | In-memory SQLite via aiosqlite for isolation |
| Backend routes | pytest, httpx (TestClient) | Full request/response cycle testing |
| Scrapers | respx (httpx mocking) | Mock HTTP responses, test retry/rate-limiting |
| Celery workers | pytest with mocked tasks | Unit test task logic without Redis |
| Frontend | Vitest, React Testing Library, jsdom | Validator and utility tests |

Run backend tests: `cd backend && pytest`
Run frontend tests: `cd frontend && npm test`

## Security

- JWT: short-lived access tokens + refresh tokens
- Passwords hashed with bcrypt
- Rate limiting on all API endpoints via slowapi (60 req/min)
- Scraper credentials and proxy configs in environment variables only
- Input sanitization on all user-provided search parameters
- CORS configured for frontend domain only
- Ownership enforcement: users can only access their own trips/watches/alerts

## UI/UX Quick Reference

- **Design:** Clean, minimal, white/light-gray background, card-based layouts
- **Colors:** Blue `#2563EB` (primary), Green `#16A34A` (price drops), Red `#DC2626` (price increases)
- **Typography:** Inter or system font, hierarchy via font weight
- **Cards:** 8px rounded corners, subtle shadow, 16-24px padding
- **Mobile:** Fully responsive, stacking cards, hamburger nav

### Frontend Routes

`/login` - `/register` - `/dashboard` - `/trips` - `/trips/new` - `/trips/[id]` - `/trips/[id]/edit` - `/watches` - `/watches/[id]` - `/settings`

## Known Gaps & Next Steps

1. **CI/CD** — CodeQL security scanning added. Full CI pipeline (lint, test, build, deploy) not yet implemented.
2. **Additional scrapers** — Only Google Flights (httpx-based). Hotel and car rental scrapers not implemented.
3. **Playwright** — Not integrated. Needed for JS-rendered travel sites.
4. **Monitoring** — Sentry, Prometheus, Grafana not configured.
5. **E2E tests** — No Playwright E2E tests for frontend.
6. **Frontend test coverage** — Only lib utilities tested; component/hook tests not yet written.

## Agent Workflow Guidelines

- Consult this file at the start of every session to understand project state
- Check the "Known Gaps & Next Steps" section for available work
- Run and pass all tests before committing: `cd backend && pytest` and `cd frontend && npm test`
- Follow the service layer pattern: routes -> services -> models
- Keep sessions focused — one feature or fix per session
- Commit after each completed feature: `feat: implement <description>`
- When in doubt about UI/UX decisions, ask the user rather than assuming
