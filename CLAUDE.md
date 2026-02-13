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

**Not yet implemented:** Hotel/car rental scrapers, Playwright (JS-rendered scraping), Sentry monitoring, Prometheus/Grafana.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI 0.115+, Celery 5.4 + Redis |
| Scraping | httpx 0.28 + BeautifulSoup4 + lxml (static pages) |
| Frontend | Next.js 16 (App Router), TypeScript 5, React 19, Tailwind CSS 4, TanStack Query 5, Zustand 5, Recharts 3 |
| Database | PostgreSQL 16 (asyncpg), SQLAlchemy 2.0+ (async), Redis 5.2+ (cache/queue) |
| Auth | python-jose (JWT HS256), passlib + bcrypt |
| Validation | Pydantic 2.10 + pydantic-settings (backend), Zod 4 (frontend) |
| Testing | pytest + pytest-asyncio + factory-boy + respx (backend), Vitest 4 + React Testing Library 16 (frontend) |
| CI/CD | GitHub Actions (test, lint, build, Docker push, integration tests, security scanning) |

## Project Structure

```
Travel-Price/
├── backend/
│   ├── app/
│   │   ├── api/v1/               # FastAPI route handlers
│   │   │   ├── __init__.py       # APIRouter prefix=/api/v1, includes all sub-routers
│   │   │   ├── auth.py           # Register, login, refresh, profile
│   │   │   ├── trips.py          # Trip CRUD
│   │   │   ├── watches.py        # PriceWatch CRUD + alerts-per-watch
│   │   │   ├── alerts.py         # Alert history
│   │   │   └── prices.py         # Manual scrape trigger, price history, trip watches
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic-settings configuration (Settings class)
│   │   │   ├── database.py       # SQLAlchemy async engine + session
│   │   │   └── security.py       # JWT token creation, password hashing
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── trip.py           # TripType enum (flight, hotel, car_rental)
│   │   │   ├── price_watch.py
│   │   │   ├── price_snapshot.py # Immutable scraped price records
│   │   │   └── alert.py          # AlertType, AlertChannel, AlertStatus enums
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
│   │   │   ├── base.py           # BaseNotifier ABC, NotificationPayload
│   │   │   └── email.py          # LogEmailNotifier (logs instead of sending SMTP)
│   │   └── main.py               # FastAPI app factory, CORS, rate limiting, /health endpoint
│   ├── migrations/               # Alembic migrations
│   │   ├── env.py                # Reads DB URL from app settings, imports all models
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 0001_initial_schema.py  # All 5 tables: users, trips, price_watches, price_snapshots, alerts
│   │       └── 0002_create_price_watches_table.py  # Adds last_alerted_at column to price_watches
│   ├── Dockerfile                # Python 3.11-slim, non-root user (appuser)
│   ├── entrypoint.sh             # Runs alembic upgrade head then exec $@
│   ├── tests/                    # 18 test files (~3300 lines)
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
│   ├── next.config.ts            # Security headers (X-Frame-Options, HSTS, etc.)
│   ├── vitest.config.ts
│   ├── Dockerfile                # Node 22-alpine, non-root user (node)
│   ├── eslint.config.mjs
│   └── postcss.config.mjs
├── .github/
│   └── workflows/
│       ├── ci.yml                # CI pipeline (test, lint, build, Docker push, integration tests)
│       ├── codeql.yml            # CodeQL security scanning (Actions + Python + JS/TS)
│       ├── dependency-review.yml # Dependency vulnerability scanning on PRs
│       └── docker-scan.yml       # Trivy Docker image vulnerability scanning
├── .env.example                  # Environment variable template
├── .gitignore
├── docker-compose.yml            # Full-stack orchestration (6 services)
├── docker-compose.override.yml   # Dev overrides (hot-reload, volume mounts)
├── CLAUDE.md
└── README.md
```

## Data Model Core Entities

- **User** — id (UUID), email (unique, indexed), hashed_password, full_name, is_active (default true), created_at, updated_at
- **Trip** — id (UUID), user_id (FK→users, CASCADE), origin/destination (String(3), IATA codes), departure_date, return_date (nullable), travelers (default 1), trip_type (String(20), default "flight"), notes (nullable), created_at, updated_at
- **PriceWatch** — id (UUID), user_id (FK→users, CASCADE), trip_id (FK→trips, CASCADE), provider (default "google_flights"), target_price (cents), currency (default "USD"), is_active (default true), alert_cooldown_hours (default 6), created_at, updated_at
- **PriceSnapshot** — id (UUID), trip_id (FK→trips, CASCADE), user_id (FK→users, CASCADE), provider (indexed), price (cents), currency (default "USD"), cabin_class (nullable), airline (nullable), outbound_departure/arrival (nullable), return_departure/arrival (nullable), stops (nullable), raw_data (Text, nullable), scraped_at, created_at
- **Alert** — id (UUID), price_watch_id (FK→price_watches, CASCADE), user_id (FK→users, CASCADE), price_snapshot_id (FK→price_snapshots, CASCADE), alert_type (default "price_drop"), channel (default "email"), status, target_price (cents), triggered_price (cents), message (nullable), sent_at (nullable), created_at

### Enums

- **TripType**: `flight`, `hotel`, `car_rental`
- **AlertType**: `price_drop`
- **AlertChannel**: `email`
- **AlertStatus**: `pending`, `sent`, `failed`

All models use UUID primary keys (uuid4). Cascade deletes on all foreign keys. Migration `0001` creates all 5 tables; migration `0002` adds `last_alerted_at` column to `price_watches` (DB-only, not yet mapped in ORM).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (returns `{"status": "healthy"}`) |
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | JWT login (access + refresh tokens) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Current user profile |
| PATCH | `/api/v1/auth/me` | Update profile |
| POST | `/api/v1/trips/` | Create trip |
| GET | `/api/v1/trips/` | List trips (paginated: `page`, `per_page` max 100) |
| GET | `/api/v1/trips/{trip_id}` | Get trip |
| PATCH | `/api/v1/trips/{trip_id}` | Update trip |
| DELETE | `/api/v1/trips/{trip_id}` | Delete trip (204) |
| POST | `/api/v1/trips/{trip_id}/scrape` | Trigger manual scrape |
| GET | `/api/v1/trips/{trip_id}/prices` | Price history (paginated, filterable by `provider`) |
| GET | `/api/v1/trips/{trip_id}/watches` | List watches for trip (paginated) |
| POST | `/api/v1/watches/` | Create price watch |
| GET | `/api/v1/watches/` | List watches (paginated) |
| GET | `/api/v1/watches/{watch_id}` | Get watch |
| PATCH | `/api/v1/watches/{watch_id}` | Update watch |
| DELETE | `/api/v1/watches/{watch_id}` | Delete watch (204) |
| GET | `/api/v1/watches/{watch_id}/alerts` | Alerts for a watch (paginated) |
| GET | `/api/v1/alerts/` | List user alerts (paginated) |
| GET | `/api/v1/alerts/{alert_id}` | Get alert detail |

All `/api/v1/` endpoints require JWT Bearer token except `register`, `login`, and `refresh`. Rate limited at 60 req/min via slowapi. CORS configured for origins in `CORS_ORIGINS` env var (default: `http://localhost:3000`). Allowed methods: GET, POST, PATCH, DELETE, OPTIONS.

## Environment Variables

```bash
# Application
APP_NAME="Travel Price Scraper"     # Display name
DEBUG=false                          # Enable debug mode (allows insecure default SECRET_KEY)

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/travel_price

# Redis
REDIS_URL=redis://redis:6379/0               # Cache/general
CELERY_BROKER_URL=redis://redis:6379/1        # Task queue
CELERY_RESULT_BACKEND=redis://redis:6379/2    # Task results

# Auth / JWT
SECRET_KEY=change-me-to-a-random-string       # REQUIRED in production (app errors if default used with DEBUG=false)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000            # Comma-separated origins

# Scraping
SCRAPE_INTERVAL_MINUTES=60                    # Celery Beat schedule interval

# Alerts / Notifications
ALERT_COOLDOWN_HOURS=6                        # Min hours between alerts per watch
SMTP_HOST=                                    # Email config (currently logs only, SMTP not wired)
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=alerts@travelprice.local

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000      # Backend URL for API calls
```

## Build & Run Commands

### Docker (recommended)

```bash
cp .env.example .env                    # Create env file (edit SECRET_KEY for production)
docker compose up --build               # Start all services
docker compose down                     # Stop all services
docker compose down -v                  # Stop and remove volumes (including DB data)
```

Services: `postgres` (:5432), `redis` (:6379), `backend` (:8000), `celery-worker`, `celery-beat`, `frontend` (:3000). The backend entrypoint runs `alembic upgrade head` automatically before starting.

A `docker-compose.override.yml` is included for development: it enables hot-reload (`--reload`), mounts source directories as volumes for live editing, and uses a named volume for `node_modules`. This file is auto-loaded by Docker Compose alongside `docker-compose.yml`.

### Backend (manual)

```bash
cd backend && pip install -e ".[dev]"   # Install with dev dependencies
uvicorn app.main:app --reload           # Dev server on :8000
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
npm run dev          # Dev server on :3000
npm run build        # Production build
npm run test         # Run Vitest tests
npm run test:watch   # Watch mode
npm run lint         # ESLint (core-web-vitals + TypeScript)
```

## Architecture Patterns

### Backend: Service Layer Pattern

Routes → Services → Models → DB. Business logic lives in services, never in route handlers.

```
api/v1/trips.py  →  services/trip_service.py  →  models/trip.py  →  PostgreSQL
```

- `async/await` for all I/O (DB, HTTP, scraping)
- Dependency injection via FastAPI `Depends()`
- Environment variables via `pydantic-settings` (never hardcode secrets)
- All services take `AsyncSession` as constructor argument
- Response envelope: `ApiResponse[T]` wraps `{ data, meta, errors }`; `PaginatedApiResponse[T]` adds pagination meta

### Scraping Architecture

- Every scraper inherits `BaseScraper` and implements `async scrape(query: ScrapeQuery) -> list[PriceResult]`
- Public entry point is `execute()` which wraps `scrape()` with rate limiting + retry
- Scrapers are stateless and idempotent
- Rate limiting per-provider via Redis (optional, skipped if Redis unavailable)
- Proxy rotation (round-robin) and User-Agent rotation (5-agent pool) built into base class
- Failed scrapes retry with exponential backoff (max 3 retries, base delay 1s)
- HTTP timeout: 30s per request
- All scraped data stored as immutable timestamped PriceSnapshot records
- Currently only `google_flights` provider is registered

### Alert System

- Celery Beat schedules `scrape_all_active_trips` at `SCRAPE_INTERVAL_MINUTES` (default: 60 min)
- Workers fan out: `scrape_all_active_trips` → individual `scrape_single_trip` tasks
- New price < target → create Alert → send notification
- Notifications currently use `LogEmailNotifier` (logs to stdout; real SMTP not wired)
- Cooldown: max 1 alert per PriceWatch per `alert_cooldown_hours` (default: 6)

### Frontend Architecture

- Next.js App Router with route groups: `(auth)` for public, `(protected)` for authenticated
- Auth guard in `(protected)/layout.tsx` redirects unauthenticated users
- Centralized API client (`lib/api.ts`) with automatic JWT token refresh
- TanStack Query for server state, Zustand for client state (auth store)
- Zod validation on API responses
- Path alias: `@/*` → `./src/*`

## CI/CD Pipeline

### Workflows

| Workflow | Trigger | Jobs |
|----------|---------|------|
| **CI** (`ci.yml`) | Push/PR to `main`, `develop` | Backend tests + coverage (Codecov), frontend lint + test + build, Docker image build/push (GHCR), integration tests (PR only) |
| **CodeQL** (`codeql.yml`) | Push/PR to `main`, daily 2:00 UTC | Static analysis for Actions, JavaScript/TypeScript, Python |
| **Dependency Review** (`dependency-review.yml`) | PR to `main` | Scans dependency changes for known vulnerabilities, comments summary in PR |
| **Docker Scan** (`docker-scan.yml`) | Dockerfile changes, weekly (Monday 10:00 UTC) | Trivy scans backend + frontend images for CRITICAL/HIGH vulnerabilities, uploads to GitHub Security |

### CI Job Flow

```
backend-test ──→ backend-docker ──┐
                                  ├──→ integration-test (PRs only)
frontend-test ──→ frontend-docker ─┘
```

Docker images are pushed to `ghcr.io` on push to `main`/`develop` (not on PRs).

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

- JWT: short-lived access tokens (30 min) + refresh tokens (7 days), HS256
- Passwords hashed with bcrypt (via passlib)
- Rate limiting on all API endpoints via slowapi (60 req/min)
- SECRET_KEY enforced: app refuses to start in non-debug mode with the default key
- Scraper credentials and proxy configs in environment variables only
- Input sanitization on all user-provided search parameters
- CORS configured for specified origins only
- Ownership enforcement: users can only access their own trips/watches/alerts
- Frontend security headers via `next.config.ts`: X-Frame-Options (DENY), X-Content-Type-Options (nosniff), X-XSS-Protection, Referrer-Policy (strict-origin-when-cross-origin), HSTS (1 year, includeSubDomains)
- Docker images run as non-root users (`appuser` for backend, `node` for frontend)
- CI security scanning: CodeQL (Actions + Python + JS/TS), dependency review on PRs, Trivy Docker image scanning (weekly + on Dockerfile changes)

## UI/UX Quick Reference

- **Design:** Clean, minimal, white/light-gray background, card-based layouts
- **Colors:** Blue `#2563EB` (primary), Green `#16A34A` (price drops), Red `#DC2626` (price increases)
- **Typography:** Inter or system font, hierarchy via font weight
- **Cards:** 8px rounded corners, subtle shadow, 16-24px padding
- **Mobile:** Fully responsive, stacking cards, hamburger nav

### Frontend Routes

`/login` - `/register` - `/dashboard` - `/trips` - `/trips/new` - `/trips/[id]` - `/trips/[id]/edit` - `/watches` - `/watches/[id]` - `/settings`

## Known Gaps & Next Steps

1. **Additional scrapers** — Only Google Flights (httpx-based). Hotel and car rental scrapers not implemented.
2. **Playwright** — Not integrated. Needed for JS-rendered travel sites.
3. **Real email delivery** — Notifications currently log only (`LogEmailNotifier`). SMTP sending not wired.
4. **ORM/migration mismatch** — Migration `0002` adds `last_alerted_at` to `price_watches` table, but the `PriceWatch` ORM model does not map this column.
5. **Monitoring** — Sentry, Prometheus, Grafana not configured.
6. **E2E tests** — No Playwright E2E tests for frontend.
7. **Frontend test coverage** — Only lib utilities tested; component/hook tests not yet written.

## Agent Workflow Guidelines

- Consult this file at the start of every session to understand project state
- Check the "Known Gaps & Next Steps" section for available work
- Run and pass all tests before committing: `cd backend && pytest` and `cd frontend && npm test`
- Follow the service layer pattern: routes → services → models
- Keep sessions focused — one feature or fix per session
- Commit after each completed feature: `feat: implement <description>`
- When in doubt about UI/UX decisions, ask the user rather than assuming
