"""Custom exceptions for API client operations."""


class ApiClientError(Exception):
    """Base exception for all API client errors."""


class NetworkError(ApiClientError):
    """Network-related errors (timeouts, connection failures) - retryable."""


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
