from __future__ import annotations


class MatiaError(Exception):
    """Base class for all errors raised by the Matia client."""


class MatiaAPIError(MatiaError):
    """Raised when the Matia API returns a non-2xx response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: str | None = None,
        response_body: object = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.response_body = response_body

    def __str__(self) -> str:
        suffix = f" (code={self.code})" if self.code else ""
        return f"[{self.status_code}] {self.message}{suffix}"


class MatiaBadRequestError(MatiaAPIError):
    """Raised for HTTP 400 responses."""


class MatiaNotFoundError(MatiaAPIError):
    """Raised for HTTP 404 responses."""
