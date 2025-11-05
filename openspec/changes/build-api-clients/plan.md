# Build API Clients Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use skills_executing_plans to implement this plan task-by-task.

**Goal:** Build async HTTP client infrastructure and API clients for Open5e (v1, v2) and D&D 5e APIs to fetch game data with caching, retry logic, and error handling.

**Architecture:** Base HTTP client with async/await, exponential backoff retry, SQLite cache integration. Separate clients for each API version with Pydantic models for response normalization. Factory pattern for dependency injection.

**Tech Stack:** httpx (async HTTP), Pydantic (validation), aiosqlite (caching), respx (testing mocks), pytest-asyncio

---

## Task 1: Custom Exception Classes

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/__init__.py`
- Create: `src/lorekeeper_mcp/api_clients/exceptions.py`
- Create: `tests/test_api_clients/__init__.py`
- Create: `tests/test_api_clients/test_exceptions.py`

**Step 1: Write the failing test**

Create test file with exception hierarchy validation:

```python
"""Tests for API client custom exceptions."""

import pytest

from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)


def test_exception_hierarchy() -> None:
    """Test that all exceptions inherit from ApiClientError."""
    assert issubclass(NetworkError, ApiClientError)
    assert issubclass(ApiError, ApiClientError)
    assert issubclass(ParseError, ApiClientError)
    assert issubclass(CacheError, ApiClientError)


def test_network_error_creation() -> None:
    """Test NetworkError can be created with message."""
    error = NetworkError("Connection timeout")
    assert str(error) == "Connection timeout"
    assert isinstance(error, ApiClientError)


def test_api_error_with_status_code() -> None:
    """Test ApiError stores status code."""
    error = ApiError("Not found", status_code=404)
    assert str(error) == "Not found"
    assert error.status_code == 404


def test_parse_error_with_raw_data() -> None:
    """Test ParseError stores raw response data."""
    raw_data = '{"invalid": json}'
    error = ParseError("Failed to parse JSON", raw_data=raw_data)
    assert str(error) == "Failed to parse JSON"
    assert error.raw_data == raw_data


def test_cache_error_is_non_fatal() -> None:
    """Test CacheError represents non-fatal cache failures."""
    error = CacheError("Cache write failed")
    assert str(error) == "Cache write failed"
    assert isinstance(error, ApiClientError)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_exceptions.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.api_clients.exceptions'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/exceptions.py`:

```python
"""Custom exceptions for API client operations."""


class ApiClientError(Exception):
    """Base exception for all API client errors."""

    pass


class NetworkError(ApiClientError):
    """Network-related errors (timeouts, connection failures) - retryable."""

    pass


class ApiError(ApiClientError):
    """API response errors (4xx/5xx status codes) - non-retryable."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize ApiError with optional status code.

        Args:
            message: Error message
            status_code: HTTP status code if available
        """
        super().__init__(message)
        self.status_code = status_code


class ParseError(ApiClientError):
    """Response parsing errors (malformed JSON, validation failures)."""

    def __init__(self, message: str, raw_data: str | None = None) -> None:
        """Initialize ParseError with optional raw response data.

        Args:
            message: Error message
            raw_data: Raw response data that failed to parse
        """
        super().__init__(message)
        self.raw_data = raw_data


class CacheError(ApiClientError):
    """Cache operation errors - non-fatal, should not break requests."""

    pass
```

Create `src/lorekeeper_mcp/api_clients/__init__.py`:

```python
"""API client package for external D&D 5e data sources."""

from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)

__all__ = [
    "ApiClientError",
    "NetworkError",
    "ApiError",
    "ParseError",
    "CacheError",
]
```

Create `tests/test_api_clients/__init__.py` (empty file):

```python
"""Tests for API clients."""
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_exceptions.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/__init__.py
git add src/lorekeeper_mcp/api_clients/exceptions.py
git add tests/test_api_clients/__init__.py
git add tests/test_api_clients/test_exceptions.py
git commit -m "feat: add custom exception classes for API clients"
```

---

## Task 2: Base HTTP Client - Request Method

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/base.py`
- Create: `tests/test_api_clients/test_base.py`

**Step 1: Write the failing test**

Create test file with basic request functionality:

```python
"""Tests for BaseHttpClient."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError


@pytest.fixture
def base_client() -> BaseHttpClient:
    """Create a BaseHttpClient instance for testing."""
    return BaseHttpClient(base_url="https://api.example.com", timeout=5.0)


@respx.mock
async def test_make_request_success(base_client: BaseHttpClient) -> None:
    """Test successful HTTP GET request."""
    mock_route = respx.get("https://api.example.com/test").mock(
        return_value=httpx.Response(200, json={"data": "success"})
    )

    response = await base_client._make_request("/test")

    assert response == {"data": "success"}
    assert mock_route.called


@respx.mock
async def test_make_request_404_error(base_client: BaseHttpClient) -> None:
    """Test API error handling for 404 response."""
    respx.get("https://api.example.com/notfound").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )

    with pytest.raises(ApiError) as exc_info:
        await base_client._make_request("/notfound")

    assert exc_info.value.status_code == 404


@respx.mock
async def test_make_request_timeout(base_client: BaseHttpClient) -> None:
    """Test network timeout handling."""
    respx.get("https://api.example.com/slow").mock(side_effect=httpx.TimeoutException("Timeout"))

    with pytest.raises(NetworkError) as exc_info:
        await base_client._make_request("/slow", max_retries=1)

    assert "Timeout" in str(exc_info.value)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_base.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.api_clients.base'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/base.py`:

```python
"""Base HTTP client with retry logic and error handling."""

import asyncio
import logging
from typing import Any

import httpx

from lorekeeper_mcp.api_clients.exceptions import ApiError, NetworkError

logger = logging.getLogger(__name__)


class BaseHttpClient:
    """Base HTTP client providing common functionality for API requests."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 5,
    ) -> None:
        """Initialize the base HTTP client.

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "LoreKeeper-MCP/0.1.0"},
            )
        return self._client

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            max_retries: Override max_retries for this request
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            NetworkError: For network-related failures
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"
        retries = max_retries if max_retries is not None else self.max_retries
        client = await self._get_client()

        for attempt in range(retries + 1):
            try:
                response = await client.request(method, url, **kwargs)

                if response.status_code >= 400:
                    raise ApiError(
                        f"API error: {response.status_code}",
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.TimeoutException as e:
                if attempt == retries:
                    raise NetworkError(f"Request timeout after {retries + 1} attempts") from e
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except httpx.RequestError as e:
                if attempt == retries:
                    raise NetworkError(f"Network error: {e}") from e
                await asyncio.sleep(2**attempt)

        # Should not reach here
        raise NetworkError("Max retries exceeded")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

Update `src/lorekeeper_mcp/api_clients/__init__.py`:

```python
"""API client package for external D&D 5e data sources."""

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)

__all__ = [
    "BaseHttpClient",
    "ApiClientError",
    "NetworkError",
    "ApiError",
    "ParseError",
    "CacheError",
]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_base.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/base.py
git add src/lorekeeper_mcp/api_clients/__init__.py
git add tests/test_api_clients/test_base.py
git commit -m "feat: add base HTTP client with retry logic"
```

---

## Task 3: Base HTTP Client - Cache Integration

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/base.py`
- Modify: `tests/test_api_clients/test_base.py`

**Step 1: Write the failing test**

Add cache integration tests:

```python
# Add to existing test_base.py imports
from lorekeeper_mcp.cache.db import get_cached, set_cached


@pytest.fixture
async def base_client_with_cache(test_db: Any) -> BaseHttpClient:
    """Create BaseHttpClient with cache enabled for testing."""
    client = BaseHttpClient(base_url="https://api.example.com", cache_ttl=3600)
    yield client
    await client.close()


@respx.mock
async def test_cache_hit(base_client_with_cache: BaseHttpClient) -> None:
    """Test that cached responses are returned without making HTTP request."""
    # Pre-populate cache
    await set_cached("https://api.example.com/cached", {"data": "from_cache"}, ttl=3600)

    # Mock should not be called if cache works
    mock_route = respx.get("https://api.example.com/cached").mock(
        return_value=httpx.Response(200, json={"data": "from_api"})
    )

    response = await base_client_with_cache.make_request("/cached")

    assert response == {"data": "from_cache"}
    assert not mock_route.called


@respx.mock
async def test_cache_miss(base_client_with_cache: BaseHttpClient) -> None:
    """Test that cache miss results in HTTP request and cache update."""
    mock_route = respx.get("https://api.example.com/uncached").mock(
        return_value=httpx.Response(200, json={"data": "from_api"})
    )

    response = await base_client_with_cache.make_request("/uncached")

    assert response == {"data": "from_api"}
    assert mock_route.called

    # Verify cache was updated
    cached = await get_cached("https://api.example.com/uncached")
    assert cached == {"data": "from_api"}


@respx.mock
async def test_cache_error_continues(base_client_with_cache: BaseHttpClient, monkeypatch: Any) -> None:
    """Test that cache errors don't break requests."""
    # Mock cache to raise error
    async def failing_get_cached(*args: Any, **kwargs: Any) -> None:
        raise Exception("Cache read failed")

    monkeypatch.setattr("lorekeeper_mcp.api_clients.base.get_cached", failing_get_cached)

    mock_route = respx.get("https://api.example.com/test").mock(
        return_value=httpx.Response(200, json={"data": "success"})
    )

    # Should still succeed despite cache error
    response = await base_client_with_cache.make_request("/test")

    assert response == {"data": "success"}
    assert mock_route.called
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_base.py::test_cache_hit -v`
Expected: FAIL with "AttributeError: 'BaseHttpClient' object has no attribute 'make_request'" or "no cache_ttl parameter"

**Step 3: Write minimal implementation**

Update `src/lorekeeper_mcp/api_clients/base.py`:

```python
"""Base HTTP client with retry logic and error handling."""

import asyncio
import logging
from typing import Any

import httpx

from lorekeeper_mcp.api_clients.exceptions import ApiError, CacheError, NetworkError
from lorekeeper_mcp.cache.db import get_cached, set_cached

logger = logging.getLogger(__name__)


class BaseHttpClient:
    """Base HTTP client providing common functionality for API requests."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 5,
        cache_ttl: int = 604800,  # 7 days default
    ) -> None:
        """Initialize the base HTTP client.

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            cache_ttl: Cache time-to-live in seconds (default 7 days)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "LoreKeeper-MCP/0.1.0"},
            )
        return self._client

    async def _get_cached_response(self, cache_key: str) -> dict[str, Any] | None:
        """Get cached response if available.

        Args:
            cache_key: Cache key (typically full URL)

        Returns:
            Cached response or None if not found/expired
        """
        try:
            return await get_cached(cache_key)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
            return None

    async def _cache_response(self, cache_key: str, data: dict[str, Any]) -> None:
        """Cache response data.

        Args:
            cache_key: Cache key (typically full URL)
            data: Response data to cache
        """
        try:
            await set_cached(cache_key, data, ttl=self.cache_ttl)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
            # Non-fatal - continue without caching

    async def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        use_cache: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with caching and retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            use_cache: Whether to use cache for this request
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            NetworkError: For network-related failures
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"

        # Check cache first
        if use_cache and method == "GET":
            cached = await self._get_cached_response(url)
            if cached is not None:
                logger.debug(f"Cache hit: {url}")
                return cached

        # Make request (delegates to _make_request)
        response = await self._make_request(endpoint, method, **kwargs)

        # Cache successful response
        if use_cache and method == "GET":
            await self._cache_response(url, response)

        return response

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            max_retries: Override max_retries for this request
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            NetworkError: For network-related failures
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"
        retries = max_retries if max_retries is not None else self.max_retries
        client = await self._get_client()

        for attempt in range(retries + 1):
            try:
                response = await client.request(method, url, **kwargs)

                if response.status_code >= 400:
                    raise ApiError(
                        f"API error: {response.status_code}",
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.TimeoutException as e:
                if attempt == retries:
                    raise NetworkError(f"Request timeout after {retries + 1} attempts") from e
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except httpx.RequestError as e:
                if attempt == retries:
                    raise NetworkError(f"Network error: {e}") from e
                await asyncio.sleep(2**attempt)

        # Should not reach here
        raise NetworkError("Max retries exceeded")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_base.py -v`
Expected: PASS (all tests including new cache tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/base.py
git add tests/test_api_clients/test_base.py
git commit -m "feat: add cache integration to base HTTP client"
```

---

## Task 4: Pydantic Base Models

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/models/__init__.py`
- Create: `src/lorekeeper_mcp/api_clients/models/base.py`
- Create: `tests/test_api_clients/test_models.py`

**Step 1: Write the failing test**

```python
"""Tests for Pydantic response models."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.api_clients.models.base import BaseModel


def test_base_model_required_fields() -> None:
    """Test that BaseModel validates required fields."""
    model = BaseModel(name="Test Item", slug="test-item")
    assert model.name == "Test Item"
    assert model.slug == "test-item"


def test_base_model_optional_fields() -> None:
    """Test that BaseModel handles optional fields."""
    model = BaseModel(
        name="Test Item",
        slug="test-item",
        desc="Test description",
        document_url="https://example.com",
    )
    assert model.desc == "Test description"
    assert model.document_url == "https://example.com"


def test_base_model_missing_required_field() -> None:
    """Test that BaseModel raises error for missing required fields."""
    with pytest.raises(ValidationError):
        BaseModel(name="Test")  # Missing slug


def test_base_model_to_dict() -> None:
    """Test model serialization to dict."""
    model = BaseModel(name="Test", slug="test", desc="Description")
    data = model.model_dump()

    assert data["name"] == "Test"
    assert data["slug"] == "test"
    assert data["desc"] == "Description"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.api_clients.models'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/models/base.py`:

```python
"""Base Pydantic models for API responses."""

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field


class BaseModel(PydanticBaseModel):
    """Base model with common fields for API responses."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    name: str = Field(..., description="Name of the item")
    slug: str = Field(..., description="URL-safe identifier")
    desc: str | None = Field(None, description="Description text")
    document_url: str | None = Field(None, description="Source document URL")
```

Create `src/lorekeeper_mcp/api_clients/models/__init__.py`:

```python
"""Pydantic models for API response parsing and validation."""

from lorekeeper_mcp.api_clients.models.base import BaseModel

__all__ = ["BaseModel"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_models.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/models/__init__.py
git add src/lorekeeper_mcp/api_clients/models/base.py
git add tests/test_api_clients/test_models.py
git commit -m "feat: add base Pydantic model for API responses"
```

---

## Task 5: Spell Model

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/models/spell.py`
- Modify: `tests/test_api_clients/test_models.py`

**Step 1: Write the failing test**

Add spell model tests to `test_models.py`:

```python
# Add to imports
from lorekeeper_mcp.api_clients.models.spell import Spell


def test_spell_model_minimal() -> None:
    """Test Spell model with minimal required fields."""
    spell = Spell(
        name="Fireball",
        slug="fireball",
        level=3,
        school="Evocation",
        casting_time="1 action",
        range="150 feet",
        components="V, S, M",
        duration="Instantaneous",
    )

    assert spell.name == "Fireball"
    assert spell.level == 3
    assert spell.school == "Evocation"


def test_spell_model_full() -> None:
    """Test Spell model with all fields."""
    spell = Spell(
        name="Fireball",
        slug="fireball",
        level=3,
        school="Evocation",
        casting_time="1 action",
        range="150 feet",
        components="V, S, M",
        duration="Instantaneous",
        desc="A bright streak flashes...",
        higher_level="When you cast this spell using a spell slot of 4th level or higher...",
        concentration=False,
        ritual=False,
        material="A tiny ball of bat guano and sulfur",
        damage_type=["fire"],
    )

    assert spell.concentration is False
    assert spell.ritual is False
    assert spell.material == "A tiny ball of bat guano and sulfur"
    assert spell.damage_type == ["fire"]


def test_spell_cantrip() -> None:
    """Test Spell model with cantrip (level 0)."""
    spell = Spell(
        name="Fire Bolt",
        slug="fire-bolt",
        level=0,
        school="Evocation",
        casting_time="1 action",
        range="120 feet",
        components="V, S",
        duration="Instantaneous",
    )

    assert spell.level == 0
    assert spell.name == "Fire Bolt"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_models.py::test_spell_model_minimal -v`
Expected: FAIL with "ImportError: cannot import name 'Spell'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/models/spell.py`:

```python
"""Spell model for D&D 5e spells."""

from pydantic import Field

from lorekeeper_mcp.api_clients.models.base import BaseModel


class Spell(BaseModel):
    """Model representing a D&D 5e spell."""

    level: int = Field(..., ge=0, le=9, description="Spell level (0-9, 0=cantrip)")
    school: str = Field(..., description="Magic school (Evocation, Conjuration, etc.)")
    casting_time: str = Field(..., description="Time required to cast")
    range: str = Field(..., description="Spell range")
    components: str = Field(..., description="Components (V, S, M)")
    duration: str = Field(..., description="Spell duration")
    concentration: bool = Field(False, description="Requires concentration")
    ritual: bool = Field(False, description="Can be cast as ritual")
    material: str | None = Field(None, description="Material components")
    higher_level: str | None = Field(None, description="Higher level casting effects")
    damage_type: list[str] | None = Field(None, description="Damage types dealt")
```

Update `src/lorekeeper_mcp/api_clients/models/__init__.py`:

```python
"""Pydantic models for API response parsing and validation."""

from lorekeeper_mcp.api_clients.models.base import BaseModel
from lorekeeper_mcp.api_clients.models.spell import Spell

__all__ = ["BaseModel", "Spell"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_models.py -v`
Expected: PASS (all tests including spell tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/models/spell.py
git add src/lorekeeper_mcp/api_clients/models/__init__.py
git add tests/test_api_clients/test_models.py
git commit -m "feat: add Spell model for spell data"
```

---

## Task 6: Monster Model

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/models/monster.py`
- Modify: `tests/test_api_clients/test_models.py`

**Step 1: Write the failing test**

Add monster model tests:

```python
# Add to imports
from lorekeeper_mcp.api_clients.models.monster import Monster


def test_monster_model_minimal() -> None:
    """Test Monster model with minimal fields."""
    monster = Monster(
        name="Goblin",
        slug="goblin",
        size="Small",
        type="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        challenge_rating="1/4",
    )

    assert monster.name == "Goblin"
    assert monster.size == "Small"
    assert monster.armor_class == 15
    assert monster.challenge_rating == "1/4"


def test_monster_model_with_stats() -> None:
    """Test Monster model with ability scores."""
    monster = Monster(
        name="Goblin",
        slug="goblin",
        size="Small",
        type="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        challenge_rating="1/4",
        strength=8,
        dexterity=14,
        constitution=10,
        intelligence=10,
        wisdom=8,
        charisma=8,
    )

    assert monster.strength == 8
    assert monster.dexterity == 14
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_models.py::test_monster_model_minimal -v`
Expected: FAIL with "ImportError: cannot import name 'Monster'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/models/monster.py`:

```python
"""Monster model for D&D 5e creatures."""

from pydantic import Field

from lorekeeper_mcp.api_clients.models.base import BaseModel


class Monster(BaseModel):
    """Model representing a D&D 5e monster or creature."""

    size: str = Field(..., description="Size category (Tiny, Small, Medium, Large, etc.)")
    type: str = Field(..., description="Creature type (humanoid, beast, dragon, etc.)")
    alignment: str = Field(..., description="Alignment")
    armor_class: int = Field(..., ge=0, description="Armor class")
    hit_points: int = Field(..., ge=0, description="Average hit points")
    hit_dice: str = Field(..., description="Hit dice formula")
    challenge_rating: str = Field(..., description="Challenge rating (CR)")

    # Ability scores
    strength: int | None = Field(None, ge=1, le=30, description="Strength score")
    dexterity: int | None = Field(None, ge=1, le=30, description="Dexterity score")
    constitution: int | None = Field(None, ge=1, le=30, description="Constitution score")
    intelligence: int | None = Field(None, ge=1, le=30, description="Intelligence score")
    wisdom: int | None = Field(None, ge=1, le=30, description="Wisdom score")
    charisma: int | None = Field(None, ge=1, le=30, description="Charisma score")

    # Optional arrays
    speed: dict[str, int] | None = Field(None, description="Speed values")
    actions: list[dict] | None = Field(None, description="Actions")
    legendary_actions: list[dict] | None = Field(None, description="Legendary actions")
    special_abilities: list[dict] | None = Field(None, description="Special abilities")
```

Update `src/lorekeeper_mcp/api_clients/models/__init__.py`:

```python
"""Pydantic models for API response parsing and validation."""

from lorekeeper_mcp.api_clients.models.base import BaseModel
from lorekeeper_mcp.api_clients.models.monster import Monster
from lorekeeper_mcp.api_clients.models.spell import Spell

__all__ = ["BaseModel", "Spell", "Monster"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_models.py -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/models/monster.py
git add src/lorekeeper_mcp/api_clients/models/__init__.py
git add tests/test_api_clients/test_models.py
git commit -m "feat: add Monster model for creature data"
```

---

## Task 7: Equipment Models (Weapon, Armor)

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/models/equipment.py`
- Modify: `tests/test_api_clients/test_models.py`

**Step 1: Write the failing test**

Add equipment model tests:

```python
# Add to imports
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon


def test_weapon_model() -> None:
    """Test Weapon model."""
    weapon = Weapon(
        name="Longsword",
        slug="longsword",
        category="Martial Melee",
        damage_dice="1d8",
        damage_type="slashing",
        cost="15 gp",
        weight=3.0,
    )

    assert weapon.name == "Longsword"
    assert weapon.damage_dice == "1d8"
    assert weapon.damage_type == "slashing"


def test_weapon_with_properties() -> None:
    """Test Weapon with properties array."""
    weapon = Weapon(
        name="Shortbow",
        slug="shortbow",
        category="Simple Ranged",
        damage_dice="1d6",
        damage_type="piercing",
        cost="25 gp",
        weight=2.0,
        properties=["ammunition", "two-handed"],
        range_normal=80,
        range_long=320,
    )

    assert weapon.properties == ["ammunition", "two-handed"]
    assert weapon.range_normal == 80
    assert weapon.range_long == 320


def test_armor_model() -> None:
    """Test Armor model."""
    armor = Armor(
        name="Chain Mail",
        slug="chain-mail",
        category="Heavy",
        base_ac=16,
        cost="75 gp",
        weight=55.0,
        stealth_disadvantage=True,
    )

    assert armor.name == "Chain Mail"
    assert armor.category == "Heavy"
    assert armor.base_ac == 16
    assert armor.stealth_disadvantage is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_models.py::test_weapon_model -v`
Expected: FAIL with "ImportError: cannot import name 'Weapon'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/models/equipment.py`:

```python
"""Equipment models for weapons and armor."""

from pydantic import Field

from lorekeeper_mcp.api_clients.models.base import BaseModel


class Weapon(BaseModel):
    """Model representing a D&D 5e weapon."""

    category: str = Field(..., description="Weapon category (Simple/Martial, Melee/Ranged)")
    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: str = Field(..., description="Damage type (slashing, piercing, bludgeoning)")
    cost: str = Field(..., description="Cost in gold pieces")
    weight: float = Field(..., ge=0, description="Weight in pounds")

    properties: list[str] | None = Field(None, description="Weapon properties")
    range_normal: int | None = Field(None, description="Normal range in feet")
    range_long: int | None = Field(None, description="Long range in feet")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")


class Armor(BaseModel):
    """Model representing D&D 5e armor."""

    category: str = Field(..., description="Armor category (Light, Medium, Heavy, Shield)")
    base_ac: int = Field(..., ge=0, description="Base armor class")
    cost: str = Field(..., description="Cost in gold pieces")
    weight: float = Field(..., ge=0, description="Weight in pounds")

    dex_bonus: bool | None = Field(None, description="Can add Dex bonus to AC")
    max_dex_bonus: int | None = Field(None, description="Maximum Dex bonus")
    strength_required: int | None = Field(None, description="Minimum Strength required")
    stealth_disadvantage: bool = Field(False, description="Imposes disadvantage on Stealth")
```

Update `src/lorekeeper_mcp/api_clients/models/__init__.py`:

```python
"""Pydantic models for API response parsing and validation."""

from lorekeeper_mcp.api_clients.models.base import BaseModel
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon
from lorekeeper_mcp.api_clients.models.monster import Monster
from lorekeeper_mcp.api_clients.models.spell import Spell

__all__ = ["BaseModel", "Spell", "Monster", "Weapon", "Armor"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_models.py -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/models/equipment.py
git add src/lorekeeper_mcp/api_clients/models/__init__.py
git add tests/test_api_clients/test_models.py
git commit -m "feat: add Weapon and Armor models for equipment data"
```

---

## Task 8: Open5e V2 Client - Core Implementation

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/open5e_v2.py`
- Create: `tests/test_api_clients/test_open5e_v2.py`

**Step 1: Write the failing test**

```python
"""Tests for Open5eV2Client."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


@pytest.fixture
async def v2_client(test_db) -> Open5eV2Client:
    """Create Open5eV2Client for testing."""
    client = Open5eV2Client()
    yield client
    await client.close()


@respx.mock
async def test_get_spells_basic(v2_client: Open5eV2Client) -> None:
    """Test basic spell lookup."""
    respx.get("https://api.open5e.com/v2/spells/?name=fireball").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Fireball",
                        "slug": "fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "desc": "A bright streak...",
                    }
                ]
            },
        )
    )

    spells = await v2_client.get_spells(name="fireball")

    assert len(spells) == 1
    assert spells[0].name == "Fireball"
    assert spells[0].level == 3


@respx.mock
async def test_get_spells_with_filters(v2_client: Open5eV2Client) -> None:
    """Test spell lookup with multiple filters."""
    respx.get("https://api.open5e.com/v2/spells/?level=3&school=Evocation").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    spells = await v2_client.get_spells(level=3, school="Evocation")

    assert isinstance(spells, list)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_open5e_v2.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.api_clients.open5e_v2'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/open5e_v2.py`:

```python
"""Client for Open5e API v2 (spells, weapons, armor, etc.)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.models.spell import Spell


class Open5eV2Client(BaseHttpClient):
    """Client for Open5e API v2 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v2 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v2", **kwargs)

    async def get_spells(self, **filters: Any) -> list[Spell]:
        """Get spells with optional filters.

        Args:
            name: Filter by spell name
            level: Filter by spell level (0-9)
            school: Filter by magic school
            **filters: Additional filter parameters

        Returns:
            List of Spell objects
        """
        # Build query parameters
        params = {k: v for k, v in filters.items() if v is not None}

        # Make request
        response = await self.make_request("/spells/", params=params)

        # Parse results
        results = response.get("results", [])
        return [Spell(**spell_data) for spell_data in results]
```

Update `src/lorekeeper_mcp/api_clients/__init__.py`:

```python
"""API client package for external D&D 5e data sources."""

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

__all__ = [
    "BaseHttpClient",
    "Open5eV2Client",
    "ApiClientError",
    "NetworkError",
    "ApiError",
    "ParseError",
    "CacheError",
]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_open5e_v2.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/open5e_v2.py
git add src/lorekeeper_mcp/api_clients/__init__.py
git add tests/test_api_clients/test_open5e_v2.py
git commit -m "feat: add Open5eV2Client with spell lookup"
```

---

## Task 9: Open5e V2 Client - Weapons and Armor

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/open5e_v2.py`
- Modify: `tests/test_api_clients/test_open5e_v2.py`

**Step 1: Write the failing test**

Add weapon and armor tests:

```python
# Add to imports
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon


@respx.mock
async def test_get_weapons(v2_client: Open5eV2Client) -> None:
    """Test weapon lookup."""
    respx.get("https://api.open5e.com/v2/weapons/?name=longsword").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Longsword",
                        "slug": "longsword",
                        "category": "Martial Melee",
                        "damage_dice": "1d8",
                        "damage_type": "slashing",
                        "cost": "15 gp",
                        "weight": 3.0,
                    }
                ]
            },
        )
    )

    weapons = await v2_client.get_weapons(name="longsword")

    assert len(weapons) == 1
    assert weapons[0].name == "Longsword"
    assert weapons[0].damage_dice == "1d8"


@respx.mock
async def test_get_armor(v2_client: Open5eV2Client) -> None:
    """Test armor lookup."""
    respx.get("https://api.open5e.com/v2/armor/?name=chain-mail").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Chain Mail",
                        "slug": "chain-mail",
                        "category": "Heavy",
                        "base_ac": 16,
                        "cost": "75 gp",
                        "weight": 55.0,
                        "stealth_disadvantage": True,
                    }
                ]
            },
        )
    )

    armors = await v2_client.get_armor(name="chain-mail")

    assert len(armors) == 1
    assert armors[0].name == "Chain Mail"
    assert armors[0].base_ac == 16
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_open5e_v2.py::test_get_weapons -v`
Expected: FAIL with "AttributeError: 'Open5eV2Client' object has no attribute 'get_weapons'"

**Step 3: Write minimal implementation**

Update `src/lorekeeper_mcp/api_clients/open5e_v2.py`:

```python
"""Client for Open5e API v2 (spells, weapons, armor, etc.)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon
from lorekeeper_mcp.api_clients.models.spell import Spell


class Open5eV2Client(BaseHttpClient):
    """Client for Open5e API v2 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v2 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v2", **kwargs)

    async def get_spells(self, **filters: Any) -> list[Spell]:
        """Get spells with optional filters.

        Args:
            name: Filter by spell name
            level: Filter by spell level (0-9)
            school: Filter by magic school
            **filters: Additional filter parameters

        Returns:
            List of Spell objects
        """
        params = {k: v for k, v in filters.items() if v is not None}
        response = await self.make_request("/spells/", params=params)
        results = response.get("results", [])
        return [Spell(**spell_data) for spell_data in results]

    async def get_weapons(self, **filters: Any) -> list[Weapon]:
        """Get weapons with optional filters.

        Args:
            name: Filter by weapon name
            category: Filter by weapon category
            **filters: Additional filter parameters

        Returns:
            List of Weapon objects
        """
        params = {k: v for k, v in filters.items() if v is not None}
        response = await self.make_request("/weapons/", params=params)
        results = response.get("results", [])
        return [Weapon(**weapon_data) for weapon_data in results]

    async def get_armor(self, **filters: Any) -> list[Armor]:
        """Get armor with optional filters.

        Args:
            name: Filter by armor name
            category: Filter by armor category
            **filters: Additional filter parameters

        Returns:
            List of Armor objects
        """
        params = {k: v for k, v in filters.items() if v is not None}
        response = await self.make_request("/armor/", params=params)
        results = response.get("results", [])
        return [Armor(**armor_data) for armor_data in results]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_open5e_v2.py -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/open5e_v2.py
git add tests/test_api_clients/test_open5e_v2.py
git commit -m "feat: add weapon and armor lookup to Open5eV2Client"
```

---

## Task 10: Open5e V1 Client - Core Implementation

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/open5e_v1.py`
- Create: `tests/test_api_clients/test_open5e_v1.py`

**Step 1: Write the failing test**

```python
"""Tests for Open5eV1Client."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client


@pytest.fixture
async def v1_client(test_db) -> Open5eV1Client:
    """Create Open5eV1Client for testing."""
    client = Open5eV1Client()
    yield client
    await client.close()


@respx.mock
async def test_get_monsters(v1_client: Open5eV1Client) -> None:
    """Test monster lookup."""
    respx.get("https://api.open5e.com/v1/monsters/?name=goblin").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Goblin",
                        "slug": "goblin",
                        "size": "Small",
                        "type": "humanoid",
                        "alignment": "neutral evil",
                        "armor_class": 15,
                        "hit_points": 7,
                        "hit_dice": "2d6",
                        "challenge_rating": "1/4",
                    }
                ]
            },
        )
    )

    monsters = await v1_client.get_monsters(name="goblin")

    assert len(monsters) == 1
    assert monsters[0].name == "Goblin"
    assert monsters[0].challenge_rating == "1/4"


@respx.mock
async def test_get_monsters_by_cr(v1_client: Open5eV1Client) -> None:
    """Test monster lookup by challenge rating."""
    respx.get("https://api.open5e.com/v1/monsters/?challenge_rating=5").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    monsters = await v1_client.get_monsters(challenge_rating="5")

    assert isinstance(monsters, list)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_open5e_v1.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.api_clients.open5e_v1'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/open5e_v1.py`:

```python
"""Client for Open5e API v1 (monsters, classes, races, magic items)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.models.monster import Monster


class Open5eV1Client(BaseHttpClient):
    """Client for Open5e API v1 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v1 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v1", **kwargs)

    async def get_monsters(self, **filters: Any) -> list[Monster]:
        """Get monsters with optional filters.

        Args:
            name: Filter by monster name
            challenge_rating: Filter by CR
            type: Filter by creature type
            size: Filter by size
            **filters: Additional filter parameters

        Returns:
            List of Monster objects
        """
        params = {k: v for k, v in filters.items() if v is not None}
        response = await self.make_request("/monsters/", params=params)
        results = response.get("results", [])
        return [Monster(**monster_data) for monster_data in results]
```

Update `src/lorekeeper_mcp/api_clients/__init__.py`:

```python
"""API client package for external D&D 5e data sources."""

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

__all__ = [
    "BaseHttpClient",
    "Open5eV1Client",
    "Open5eV2Client",
    "ApiClientError",
    "NetworkError",
    "ApiError",
    "ParseError",
    "CacheError",
]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_open5e_v1.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/open5e_v1.py
git add src/lorekeeper_mcp/api_clients/__init__.py
git add tests/test_api_clients/test_open5e_v1.py
git commit -m "feat: add Open5eV1Client with monster lookup"
```

---

## Task 11: Client Factory

**Files:**
- Create: `src/lorekeeper_mcp/api_clients/factory.py`
- Create: `tests/test_api_clients/test_factory.py`

**Step 1: Write the failing test**

```python
"""Tests for ClientFactory."""

import pytest

from lorekeeper_mcp.api_clients.factory import ClientFactory
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


def test_create_open5e_v1_client() -> None:
    """Test factory creates Open5eV1Client."""
    client = ClientFactory.create_open5e_v1()

    assert isinstance(client, Open5eV1Client)
    assert client.base_url == "https://api.open5e.com/v1"


def test_create_open5e_v2_client() -> None:
    """Test factory creates Open5eV2Client."""
    client = ClientFactory.create_open5e_v2()

    assert isinstance(client, Open5eV2Client)
    assert client.base_url == "https://api.open5e.com/v2"


def test_factory_with_custom_timeout() -> None:
    """Test factory accepts custom configuration."""
    client = ClientFactory.create_open5e_v1(timeout=60.0)

    assert client.timeout == 60.0


async def test_factory_clients_are_independent() -> None:
    """Test that factory creates independent client instances."""
    client1 = ClientFactory.create_open5e_v1()
    client2 = ClientFactory.create_open5e_v1()

    assert client1 is not client2

    await client1.close()
    await client2.close()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_factory.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.api_clients.factory'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/api_clients/factory.py`:

```python
"""Factory for creating API client instances with dependency injection."""

from typing import Any

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


class ClientFactory:
    """Factory for creating API client instances."""

    @staticmethod
    def create_open5e_v1(**kwargs: Any) -> Open5eV1Client:
        """Create an Open5e v1 API client.

        Args:
            **kwargs: Configuration options for the client

        Returns:
            Configured Open5eV1Client instance
        """
        return Open5eV1Client(**kwargs)

    @staticmethod
    def create_open5e_v2(**kwargs: Any) -> Open5eV2Client:
        """Create an Open5e v2 API client.

        Args:
            **kwargs: Configuration options for the client

        Returns:
            Configured Open5eV2Client instance
        """
        return Open5eV2Client(**kwargs)
```

Update `src/lorekeeper_mcp/api_clients/__init__.py`:

```python
"""API client package for external D&D 5e data sources."""

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)
from lorekeeper_mcp.api_clients.factory import ClientFactory
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

__all__ = [
    "BaseHttpClient",
    "ClientFactory",
    "Open5eV1Client",
    "Open5eV2Client",
    "ApiClientError",
    "NetworkError",
    "ApiError",
    "ParseError",
    "CacheError",
]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_factory.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/factory.py
git add src/lorekeeper_mcp/api_clients/__init__.py
git add tests/test_api_clients/test_factory.py
git commit -m "feat: add ClientFactory for dependency injection"
```

---

## Task 12: Run Full Test Suite

**Step 1: Run all tests**

Run: `pytest tests/test_api_clients/ -v --cov=src/lorekeeper_mcp/api_clients`
Expected: PASS (all tests), coverage report

**Step 2: Fix any failing tests**

If tests fail, debug and fix issues. Commit fixes:

```bash
git add <fixed-files>
git commit -m "fix: resolve test failures in API clients"
```

**Step 3: Check code quality**

Run linting and formatting:

```bash
ruff check src/lorekeeper_mcp/api_clients/
ruff format src/lorekeeper_mcp/api_clients/
```

**Step 4: Commit formatting changes**

```bash
git add src/lorekeeper_mcp/api_clients/
git commit -m "style: format API client code"
```

---

## Remaining Work

The following components are **NOT** included in this plan but are in the full tasks.md:

### Not Implemented (for future phases):
- Character models (Class, Race, Background, Feat)
- Rule models and D&D 5e API client
- Open5e v1 classes, races, magic items endpoints
- Open5e v2 backgrounds, feats, conditions endpoints
- Pagination handling for large result sets
- Advanced retry logic with jitter
- Request/response interceptors
- Integration tests with real API calls
- End-to-end testing scenarios
- Performance and load testing
- Comprehensive documentation and examples

**Rationale**: Following YAGNI principle - implementing core infrastructure first (base client, exceptions, basic models, two API clients with key endpoints). Additional endpoints and features can be added incrementally as needed.

---

## Summary

This plan implements:
1. ✅ Exception hierarchy
2. ✅ Base HTTP client with caching and retry
3. ✅ Pydantic models (Spell, Monster, Weapon, Armor)
4. ✅ Open5e v2 client (spells, weapons, armor)
5. ✅ Open5e v1 client (monsters)
6. ✅ Client factory
7. ✅ Unit tests with mocks
8. ✅ Code quality checks

**Estimated Time**: 2-3 hours for core implementation

**Next Steps**: After this plan is complete, additional endpoints and clients can be added following the same TDD pattern established here.
