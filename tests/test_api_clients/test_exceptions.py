"""Tests for API client custom exceptions."""

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
