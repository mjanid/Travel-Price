# Feature 4: Flight Scraper — Implementation Plan

## Prerequisites

**Feature 3 (Price Watch Management) has NOT been implemented yet.** Per the roadmap, features should be built sequentially. However, feature 4's core deliverables (BaseScraper + flight provider) can be built independently. The PriceSnapshot model is needed to store scraper results and should be created as part of this feature.

## Scope

- `BaseScraper` abstract class with retry logic, rate limiting, and proxy rotation
- Scraper type definitions (`ScrapeQuery`, `PriceResult`)
- First flight provider scraper implementation
- `PriceSnapshot` model for storing scraped results
- Scraper service to orchestrate scraping and storage
- Tests using VCR.py for recorded HTTP responses

## Implementation Steps

### Step 1: Add Dependencies to `pyproject.toml`

**File:** `backend/pyproject.toml`

Add to `dependencies`:
```
"httpx>=0.28.0",           # Move from dev to main — used by scrapers
"beautifulsoup4>=4.12.0",  # HTML parsing
"lxml>=5.0.0",             # Fast HTML parser backend
```

Add to `[project.optional-dependencies] dev`:
```
"vcrpy>=6.0.0",            # Record/replay HTTP for scraper tests
"pytest-recording>=0.13.0", # VCR pytest plugin
"respx>=0.21.0",           # Mock httpx requests (simpler alternative to VCR)
```

> **Note:** Playwright and Celery are deferred to Feature 5 (Scheduled Scraping). Feature 4 focuses on the scraper abstraction and a single httpx-based provider.

### Step 2: Create `PriceSnapshot` Model

**File:** `backend/app/models/price_snapshot.py` (NEW)

```python
class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: UUID (PK, default uuid4)
    trip_id: UUID (FK -> trips.id, CASCADE, indexed)
    user_id: UUID (FK -> users.id, CASCADE, indexed)
    provider: str (e.g. "google_flights", "skyscanner")
    price: int (cents — per CLAUDE.md convention)
    currency: str (3-char ISO 4217, default "USD")
    cabin_class: str | None (economy, business, first)
    airline: str | None
    outbound_departure: datetime | None
    outbound_arrival: datetime | None
    return_departure: datetime | None
    return_arrival: datetime | None
    stops: int | None
    raw_data: JSON | None (full provider response for debugging)
    scraped_at: datetime (UTC)
    created_at: datetime (UTC)
```

**Also update:** `backend/app/models/__init__.py` to export `PriceSnapshot`.

### Step 3: Create Scraper Type Definitions

**File:** `backend/app/scrapers/types.py` (NEW)

```python
@dataclass
class ScrapeQuery:
    origin: str              # IATA code
    destination: str         # IATA code
    departure_date: date
    return_date: date | None
    travelers: int = 1
    cabin_class: str = "economy"
    trip_id: UUID | None = None
    user_id: UUID | None = None

@dataclass
class PriceResult:
    provider: str
    price: int               # cents
    currency: str            # ISO 4217
    cabin_class: str | None
    airline: str | None
    outbound_departure: datetime | None
    outbound_arrival: datetime | None
    return_departure: datetime | None
    return_arrival: datetime | None
    stops: int | None
    raw_data: dict | None
    scraped_at: datetime     # UTC

class ScrapeError(Exception):
    """Raised when a scrape operation fails after all retries."""
    def __init__(self, provider: str, message: str, retries: int = 0): ...
```

### Step 4: Create `BaseScraper` Abstract Class

**File:** `backend/app/scrapers/base.py` (NEW)

```python
class BaseScraper(ABC):
    """Abstract base class for all scrapers.

    Features:
    - Abstract scrape() method for subclasses
    - Exponential backoff retry (max 3 retries, configurable)
    - Per-provider rate limiting via Redis (optional, graceful if Redis unavailable)
    - Proxy rotation support (list of proxy URLs from config)
    - Shared httpx.AsyncClient management
    """

    provider_name: str  # e.g. "google_flights"
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    rate_limit_requests: int = 10
    rate_limit_window: int = 60  # seconds

    def __init__(self, redis_client=None, proxies: list[str] | None = None): ...

    @abstractmethod
    async def scrape(self, query: ScrapeQuery) -> list[PriceResult]:
        """Execute a scrape for the given query. Subclasses implement this."""

    async def execute(self, query: ScrapeQuery) -> list[PriceResult]:
        """Public entry point: rate-limit check → retry loop → scrape()."""

    async def _retry_with_backoff(self, query: ScrapeQuery) -> list[PriceResult]:
        """Call self.scrape() with exponential backoff on failure."""

    async def _check_rate_limit(self) -> None:
        """Check Redis-based rate limit. Raise if exceeded."""

    def _get_proxy(self) -> str | None:
        """Return next proxy URL via round-robin rotation."""

    def _get_headers(self) -> dict[str, str]:
        """Return default HTTP headers (User-Agent rotation, etc.)."""
```

**Key design decisions:**
- `execute()` is the public API; `scrape()` is the protected method subclasses override
- Redis is optional — scraper works without it (just skips rate limiting)
- Proxy list comes from constructor, not hardcoded
- Uses `httpx.AsyncClient` for all HTTP requests (async/await per CLAUDE.md)

### Step 5: Implement First Flight Provider

**File:** `backend/app/scrapers/flights/__init__.py` (NEW, empty)
**File:** `backend/app/scrapers/flights/google_flights.py` (NEW)

```python
class GoogleFlightsScraper(BaseScraper):
    """Scraper for Google Flights using httpx + BeautifulSoup.

    Note: Google Flights doesn't have a public API, so this scraper
    works by parsing the publicly accessible flight search results.
    In production, this would likely need Playwright for JS rendering.
    For the MVP, we implement the httpx-based structure and use it
    with mock/recorded responses in tests.
    """

    provider_name = "google_flights"

    async def scrape(self, query: ScrapeQuery) -> list[PriceResult]:
        """Build search URL, fetch page, parse flight results."""
        # 1. Build search URL from query params
        # 2. Make HTTP request via self._get_client()
        # 3. Parse HTML with BeautifulSoup
        # 4. Extract flight data into PriceResult list
        # 5. Return results
```

**Alternative provider consideration:** If Google Flights proves too difficult to parse without JS rendering, implement a simpler provider first (e.g., a mock provider that returns structured test data, or an API-based provider like Amadeus if credentials are available).

### Step 6: Create Scraper Registry

**File:** `backend/app/scrapers/registry.py` (NEW)

```python
# Simple registry mapping provider names to scraper classes
SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    "google_flights": GoogleFlightsScraper,
}

def get_scraper(provider: str, **kwargs) -> BaseScraper:
    """Factory function to instantiate a scraper by provider name."""
```

### Step 7: Create Pydantic Schemas

**File:** `backend/app/schemas/price_snapshot.py` (NEW)

```python
class PriceSnapshotResponse(BaseModel):
    id: UUID
    trip_id: UUID
    provider: str
    price: int
    currency: str
    cabin_class: str | None
    airline: str | None
    outbound_departure: datetime | None
    outbound_arrival: datetime | None
    return_departure: datetime | None
    return_arrival: datetime | None
    stops: int | None
    scraped_at: datetime
    created_at: datetime

class ScrapeRequest(BaseModel):
    """Manual scrape trigger request."""
    provider: str = "google_flights"
    cabin_class: str = "economy"
```

### Step 8: Create Scraper Service

**File:** `backend/app/services/scraper_service.py` (NEW)

```python
class ScraperService:
    """Orchestrates scraping and stores results as PriceSnapshots."""

    def __init__(self, db: AsyncSession): ...

    async def scrape_trip(
        self, trip_id: UUID, user_id: UUID, provider: str = "google_flights"
    ) -> list[PriceSnapshotResponse]:
        """Scrape prices for a trip and store results.

        1. Load trip from DB (validate ownership)
        2. Build ScrapeQuery from trip data
        3. Get scraper from registry
        4. Execute scrape
        5. Store each PriceResult as a PriceSnapshot
        6. Return stored snapshots
        """

    async def get_price_history(
        self, trip_id: UUID, user_id: UUID, page: int, per_page: int
    ) -> tuple[list[PriceSnapshotResponse], int]:
        """Get paginated price history for a trip."""
```

### Step 9: Create API Routes

**File:** `backend/app/api/v1/prices.py` (NEW)

```python
# POST /api/v1/trips/{trip_id}/scrape  — Trigger manual scrape
# GET  /api/v1/trips/{trip_id}/prices  — Get price history (paginated)
```

**Update:** `backend/app/main.py` to include the new router.

### Step 10: Write Tests

**Files:**
- `backend/tests/test_scraper_base.py` — Test BaseScraper retry logic, rate limiting, proxy rotation
- `backend/tests/test_flight_scraper.py` — Test GoogleFlightsScraper with mocked HTTP responses (respx)
- `backend/tests/test_scraper_service.py` — Test ScraperService integration (scrape + store)
- `backend/tests/test_prices_routes.py` — Test API endpoints

**Testing approach:**
- Use `respx` to mock httpx requests (simpler than VCR for initial implementation)
- Test retry behavior by simulating failures
- Test rate limiting with mock Redis
- Test the full flow: API request → scraper execution → DB storage → response

### Step 11: Run All Tests

Run `pytest` from `backend/` and verify:
- All new tests pass
- All existing tests (auth, trips) still pass
- No regressions

## File Summary

| File | Action | Description |
|------|--------|-------------|
| `backend/pyproject.toml` | EDIT | Add httpx, beautifulsoup4, lxml, respx |
| `backend/app/models/price_snapshot.py` | NEW | PriceSnapshot ORM model |
| `backend/app/models/__init__.py` | EDIT | Export PriceSnapshot |
| `backend/app/scrapers/types.py` | NEW | ScrapeQuery, PriceResult, ScrapeError |
| `backend/app/scrapers/base.py` | NEW | BaseScraper abstract class |
| `backend/app/scrapers/flights/__init__.py` | NEW | Package init |
| `backend/app/scrapers/flights/google_flights.py` | NEW | First flight provider |
| `backend/app/scrapers/registry.py` | NEW | Scraper factory/registry |
| `backend/app/schemas/price_snapshot.py` | NEW | Response/request schemas |
| `backend/app/services/scraper_service.py` | NEW | Scraping orchestration + storage |
| `backend/app/api/v1/prices.py` | NEW | Price/scrape API routes |
| `backend/app/main.py` | EDIT | Register new router |
| `backend/tests/test_scraper_base.py` | NEW | BaseScraper unit tests |
| `backend/tests/test_flight_scraper.py` | NEW | Flight scraper tests |
| `backend/tests/test_scraper_service.py` | NEW | Service integration tests |
| `backend/tests/test_prices_routes.py` | NEW | API endpoint tests |

## Architectural Decisions

1. **httpx over Playwright for MVP**: The first provider uses httpx + BeautifulSoup. Playwright support can be added to BaseScraper later (Feature 5) for JS-rendered sites.

2. **Celery deferred to Feature 5**: Feature 4 provides a manual scrape endpoint (`POST /trips/{id}/scrape`). Automated scheduling via Celery Beat is Feature 5's scope.

3. **Redis optional**: Scrapers work without Redis (rate limiting is skipped). This keeps the development loop simple — no need to run Redis locally just to test scrapers.

4. **Monetary values in cents**: Per CLAUDE.md convention, all prices are stored as integers (cents) to avoid floating-point issues.

5. **Provider as string, not enum**: Using string identifiers for providers allows adding new scrapers without model migrations.

6. **Feature 3 dependency**: PriceWatch (feature 3) is not needed for feature 4. The scraper stores PriceSnapshots directly linked to trips. PriceWatch will later use scrapers via Celery tasks.

## Estimated New Files: 12 | Edited Files: 4
