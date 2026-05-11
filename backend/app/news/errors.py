"""Errors raised during news refresh (HTTP mapping in routes)."""


class NewsRefreshError(Exception):
    """Raised when refresh cannot complete; maps to an HTTP error response."""

    def __init__(self, message: str, status_code: int, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
