# Feature 5: Scheduled Scraping & Price Storage — Implementation Plan

## Prerequisites

**Feature 3 (Price Watch Management) has NOT been built.** The roadmap requires it before Feature 5, because the scheduler needs PriceWatch records to know _what_ to scrape and _what thresholds_ to check. This plan includes Feature 3 as Part A, with the Celery scheduling as Part B.

### Current State (84 tests passing)

| Feature | Status |
|---------|--------|
| Feature 1: User Auth | Done |
| Feature 2: Trip CRUD | Done |
| Feature 3: Price Watch CRUD | **Not started** |
| Feature 4: Flight Scraper | Done (BaseScraper + GoogleFlightsScraper + PriceSnapshot + manual scrape endpoint) |

### What Already Exists That Feature 5 Builds On

- `BaseScraper` with retry/rate-limit/proxy (`scrapers/base.py`)
- `GoogleFlightsScraper` (`scrapers/flights/google_flights.py`)
- `get_scraper()` registry (`scrapers/registry.py`)
- `ScrapeQuery`, `PriceResult`, `ScrapeError` types (`scrapers/types.py`)
- `ScraperService.scrape_trip()` — orchestrates scrape + stores PriceSnapshots (`services/scraper_service.py`)
- `PriceSnapshot` model — immutable price records in cents (`models/price_snapshot.py`)
- Manual scrape endpoint: `POST /api/v1/trips/{trip_id}/scrape`
- Price history endpoint: `GET /api/v1/trips/{trip_id}/prices`
- Config has `redis_url` already (`core/config.py`)
- `app/workers/__init__.py` exists (empty)

---

## Part A: Feature 3 — Price Watch Management

### Step A1: Create PriceWatch Model

**File:** `backend/app/models/price_watch.py` (NEW)

```python
class PriceWatch(Base):
    __tablename__ = "price_watches"

    id: UUID (PK, default uuid4)
    user_id: UUID (FK -> users.id, CASCADE, indexed)
    trip_id: UUID (FK -> trips.id, CASCADE, indexed)
    provider: str (String(50), default "google_flights")
    target_price: int (cents — the threshold for alerts)
    currency: str (String(3), default "USD")
    cabin_class: str (String(20), default "economy")
    is_active: bool (default True, indexed)
    check_interval_minutes: int (default 360 = 6 hours)
    last_checked_at: datetime | None (UTC, when last scraped)
    alert_cooldown_hours: int (default 6)
    last_alerted_at: datetime | None (UTC, when last alert sent)
    created_at: datetime (UTC)
    updated_at: datetime (UTC)
```

**Key fields for Feature 5:**
- `is_active` — scheduler only processes active watches
- `check_interval_minutes` — how often to scrape (per watch)
- `last_checked_at` — scheduler uses this to determine if a check is due

**Update:** `backend/app/models/__init__.py` to export `PriceWatch`.

### Step A2: Create PriceWatch Schemas

**File:** `backend/app/schemas/price_watch.py` (NEW)

```python
class PriceWatchCreateRequest(BaseModel):
    trip_id: UUID
    provider: str = "google_flights"  # validated against SCRAPER_REGISTRY
    target_price: int  # cents, ge=1
    currency: str = "USD"  # 3 chars
    cabin_class: str = "economy"
    check_interval_minutes: int = 360  # ge=30, le=1440
    alert_cooldown_hours: int = 6  # ge=1, le=72

class PriceWatchUpdateRequest(BaseModel):  # all optional
    target_price: int | None
    provider: str | None
    cabin_class: str | None
    is_active: bool | None
    check_interval_minutes: int | None
    alert_cooldown_hours: int | None

class PriceWatchResponse(BaseModel):
    id: UUID
    user_id: UUID
    trip_id: UUID
    provider: str
    target_price: int
    currency: str
    cabin_class: str
    is_active: bool
    check_interval_minutes: int
    last_checked_at: datetime | None
    alert_cooldown_hours: int
    last_alerted_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

### Step A3: Create PriceWatch Service

**File:** `backend/app/services/price_watch_service.py` (NEW)

```python
class PriceWatchService:
    def __init__(self, db: AsyncSession): ...

    async def create(user_id, payload) -> PriceWatchResponse
        # Validate trip exists and belongs to user
        # Validate provider exists in SCRAPER_REGISTRY
        # Create PriceWatch record

    async def get_by_id(user_id, watch_id) -> PriceWatchResponse

    async def list(user_id, page, per_page, is_active=None) -> (list, total)
        # Optional filter by is_active

    async def update(user_id, watch_id, payload) -> PriceWatchResponse
        # Partial update, validate provider if changed

    async def delete(user_id, watch_id) -> None

    async def get_due_watches() -> list[PriceWatch]
        # Used by Celery Beat: get all active watches where
        # last_checked_at IS NULL OR
        # last_checked_at + check_interval_minutes < now()
        # No user_id filter — this is a system-level query

    async def mark_checked(watch_id) -> None
        # Update last_checked_at = now()
```

### Step A4: Create PriceWatch Routes

**File:** `backend/app/api/v1/watches.py` (NEW)

```python
router = APIRouter(prefix="/watches", tags=["watches"])

POST   /               -> Create watch (201)
GET    /               -> List watches (paginated, ?is_active filter)
GET    /{watch_id}     -> Get single watch
PATCH  /{watch_id}     -> Update watch
DELETE /{watch_id}     -> Delete watch (204)
```

**Update:** `backend/app/api/v1/__init__.py` to include watches router.

### Step A5: Write Part A Tests

**Files:**
- `backend/tests/test_price_watch_service.py` — Unit tests for PriceWatchService CRUD + `get_due_watches()`
- `backend/tests/test_price_watch_routes.py` — Integration tests for all 5 endpoints

**Test coverage targets:**
- CRUD operations (create, get, list, update, delete)
- Ownership enforcement (can't see/modify other user's watches)
- Provider validation (unknown provider → 422)
- Trip validation (trip must exist and belong to user)
- `is_active` filter on list
- `get_due_watches()` returns correct watches based on timing

---

## Part B: Feature 5 — Celery Beat Scheduled Scraping

### Step B1: Add Celery Dependencies

**File:** `backend/pyproject.toml` — add to `dependencies`:

```
"celery[redis]>=5.4.0",
```

### Step B2: Add Celery Configuration

**File:** `backend/app/core/config.py` — add new settings:

```python
# Celery settings
celery_broker_url: str = "redis://localhost:6379/1"
celery_result_backend: str = "redis://localhost:6379/2"
scrape_batch_size: int = 50  # max watches to process per beat tick
```

Use separate Redis databases (1 for broker, 2 for results) to avoid conflicts with the app cache on db 0.

### Step B3: Create Celery App Instance

**File:** `backend/app/workers/celery_app.py` (NEW)

```python
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "travel_price_scraper",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,          # re-deliver if worker crashes
    worker_prefetch_multiplier=1, # one task at a time per worker
)
```

### Step B4: Create Database Session for Workers

**File:** `backend/app/workers/db.py` (NEW)

Celery tasks run outside FastAPI, so they need their own sync-compatible DB session strategy. Since our services are async, we need an async event loop inside the Celery task.

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings

settings = get_settings()
_engine = create_async_engine(settings.database_url)
_session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

async def get_worker_session() -> AsyncSession:
    """Yield a session for use in Celery tasks."""
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Step B5: Create Celery Tasks

**File:** `backend/app/workers/tasks.py` (NEW)

```python
import asyncio
from app.workers.celery_app import celery_app

@celery_app.task(name="scrape_due_watches", bind=True, max_retries=0)
def scrape_due_watches(self):
    """Periodic task: find all due PriceWatches and scrape each one.

    Flow:
    1. Query PriceWatchService.get_due_watches() for active watches
       where last_checked_at + check_interval < now
    2. For each watch:
       a. Call ScraperService.scrape_trip(watch.trip_id, watch.user_id, watch.provider)
       b. Update watch.last_checked_at = now
       c. Log result (success/failure + snapshot count)
    3. Return summary dict {total, succeeded, failed}
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_scrape_due_watches_async())
    finally:
        loop.close()


async def _scrape_due_watches_async():
    """Async implementation of the scrape task."""
    async with get_worker_session() as db:
        watch_service = PriceWatchService(db)
        scraper_service = ScraperService(db)

        due_watches = await watch_service.get_due_watches()
        results = {"total": len(due_watches), "succeeded": 0, "failed": 0}

        for watch in due_watches:
            try:
                await scraper_service.scrape_trip(
                    trip_id=watch.trip_id,
                    user_id=watch.user_id,
                    provider=watch.provider,
                    cabin_class=watch.cabin_class,
                )
                await watch_service.mark_checked(watch.id)
                results["succeeded"] += 1
            except Exception as exc:
                logger.error("Failed to scrape watch %s: %s", watch.id, exc)
                results["failed"] += 1

        return results


@celery_app.task(name="scrape_single_watch", bind=True, max_retries=2)
def scrape_single_watch(self, watch_id: str):
    """On-demand task to scrape a single watch (triggered via API or other task)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_scrape_single_watch_async(watch_id))
    finally:
        loop.close()
```

### Step B6: Configure Beat Schedule

**File:** `backend/app/workers/beat_schedule.py` (NEW)

```python
from celery.schedules import crontab
from app.workers.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "scrape-due-watches-every-5-min": {
        "task": "scrape_due_watches",
        "schedule": 300.0,  # every 5 minutes, check for due watches
        "options": {"queue": "scraping"},
    },
}
```

**Design decision:** Beat runs every 5 minutes but only scrapes watches that are actually due (based on `check_interval_minutes`). This avoids per-watch Beat entries and scales to any number of watches.

### Step B7: Update Workers `__init__.py`

**File:** `backend/app/workers/__init__.py` (EDIT)

```python
from app.workers.celery_app import celery_app
# Import beat_schedule to register it with the app
import app.workers.beat_schedule  # noqa: F401

__all__ = ["celery_app"]
```

### Step B8: Adapt ScraperService for Worker Use

**File:** `backend/app/services/scraper_service.py` (EDIT)

The current `scrape_trip()` raises `HTTPException` on errors, which is FastAPI-specific. For Celery tasks, we need a version that raises plain exceptions. Two options:

**Option A (preferred):** Extract the core logic into a method that doesn't raise HTTPException, and have the route handler catch and translate:

```python
async def scrape_trip_core(self, trip_id, user_id, provider, cabin_class):
    """Core scrape logic. Raises ValueError/ScrapeError (no HTTPException)."""
    ...

async def scrape_trip(self, trip_id, user_id, provider, cabin_class):
    """API-facing wrapper that translates errors to HTTPException."""
    try:
        return await self.scrape_trip_core(...)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except ScrapeError as exc:
        raise HTTPException(502, str(exc))
```

This keeps the service reusable across both FastAPI routes and Celery tasks.

### Step B9: Add API Endpoint for Task Status (Optional)

**File:** `backend/app/api/v1/watches.py` (EDIT — add to existing)

```python
POST /watches/{watch_id}/scrape  -> Trigger immediate scrape for a watch
    # Dispatches scrape_single_watch.delay(watch_id)
    # Returns 202 Accepted with task_id
```

### Step B10: Write Part B Tests

**Files:**
- `backend/tests/test_celery_tasks.py` — Test scrape tasks with mocked services
- `backend/tests/test_scraper_service_core.py` — Test the new `scrape_trip_core()` method

**Testing approach:**
- Mock Celery task execution (don't require a running Redis/Celery)
- Mock `get_due_watches()` to return controlled test data
- Verify `mark_checked()` is called on success
- Verify failed scrapes are logged but don't stop the batch
- Test the `scrape_trip_core()` method raises plain exceptions

### Step B11: Run All Tests

Run `pytest` from `backend/` and verify all tests pass with zero regressions.

---

## File Summary

### Part A (Feature 3 — Price Watch CRUD)

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/price_watch.py` | NEW | PriceWatch ORM model |
| `backend/app/models/__init__.py` | EDIT | Export PriceWatch |
| `backend/app/schemas/price_watch.py` | NEW | Create/Update/Response schemas |
| `backend/app/services/price_watch_service.py` | NEW | CRUD + get_due_watches() + mark_checked() |
| `backend/app/api/v1/watches.py` | NEW | 5 CRUD endpoints |
| `backend/app/api/v1/__init__.py` | EDIT | Register watches router |
| `backend/tests/test_price_watch_service.py` | NEW | Service unit tests |
| `backend/tests/test_price_watch_routes.py` | NEW | Route integration tests |

### Part B (Feature 5 — Celery Beat Scheduling)

| File | Action | Description |
|------|--------|-------------|
| `backend/pyproject.toml` | EDIT | Add celery[redis] |
| `backend/app/core/config.py` | EDIT | Add celery_broker_url, celery_result_backend, scrape_batch_size |
| `backend/app/workers/__init__.py` | EDIT | Export celery_app, import beat_schedule |
| `backend/app/workers/celery_app.py` | NEW | Celery app instance + config |
| `backend/app/workers/db.py` | NEW | Async DB session factory for workers |
| `backend/app/workers/tasks.py` | NEW | scrape_due_watches + scrape_single_watch tasks |
| `backend/app/workers/beat_schedule.py` | NEW | Beat schedule config (every 5 min) |
| `backend/app/services/scraper_service.py` | EDIT | Extract scrape_trip_core() for reuse |
| `backend/app/api/v1/watches.py` | EDIT | Add POST /{id}/scrape trigger endpoint |
| `backend/tests/test_celery_tasks.py` | NEW | Task tests with mocked services |
| `backend/tests/test_scraper_service_core.py` | NEW | Core method tests |

---

## Architectural Decisions

1. **Feature 3 included as prerequisite.** Without PriceWatch, the scheduler has nothing to schedule. Part A is compact (~8 files) and follows the exact same patterns as Trip CRUD.

2. **Beat polls every 5 min, watches define their own interval.** Instead of creating a separate Beat entry per watch, a single periodic task queries for "due" watches. This scales cleanly — adding a watch doesn't reconfigure Beat.

3. **Async inside Celery tasks via `asyncio.new_event_loop()`.** Celery workers are sync by default. We create a fresh event loop per task to run our async services. This is simpler than using Celery's experimental async support.

4. **Separate Redis databases.** Broker on db/1, results on db/2, app cache on db/0. Prevents key collisions and makes it easy to flush one without affecting others.

5. **`scrape_trip_core()` extracted for reuse.** The current method raises `HTTPException` which is FastAPI-specific. Extracting core logic lets Celery tasks and routes share the same service.

6. **`task_acks_late=True`** ensures tasks are re-delivered if a worker crashes mid-scrape, preventing silent data loss.

7. **No alert logic in Feature 5.** Feature 5 stores snapshots on schedule. Feature 6 adds threshold comparison + notification dispatch. Clean separation of concerns.

## Estimated New Files: 13 | Edited Files: 6 | Total Parts: A (8 files) + B (11 files)
