"""Exceptions raised by the Waypoint SDK.

Every HTTP error from the API becomes a subclass of `APIError`, so callers can
catch the specific case they can handle and let the rest propagate. The
mapping follows the Errors section of api.rental.update.
"""
from __future__ import annotations

from typing import Optional


class WaypointError(Exception):
    """Base class for every error the SDK raises."""


class ConfigurationError(WaypointError):
    """The client is missing an API key or has an invalid base URL."""


class APIConnectionError(WaypointError):
    """The API could not be reached, even after retries."""


class APIError(WaypointError):
    """The API answered with an error status."""

    def __init__(self, status: int, code: str, message: str, correlation_id: Optional[str] = None):
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code
        self.message = message
        self.correlation_id = correlation_id


class AuthenticationError(APIError):
    """401: the API key is missing, malformed, or revoked."""


class NotFoundError(APIError):
    """404: no record with that internal ID."""


class ConflictError(APIError):
    """409: the agreement is closed or cancelled and can't be changed."""


class PreconditionFailedError(APIError):
    """412: `If-Match` doesn't match the current revision. Read again and reapply."""


class UnprocessableEntityError(APIError):
    """422: the change is valid HTTP but breaks a business rule."""


class ServerError(APIError):
    """5xx: the API failed. The SDK retries these before raising."""


BY_STATUS = {
    401: AuthenticationError,
    404: NotFoundError,
    409: ConflictError,
    412: PreconditionFailedError,
    422: UnprocessableEntityError,
}


def from_response(status: int, body: dict, correlation_id: Optional[str]) -> APIError:
    err = body.get("error", {}) if isinstance(body, dict) else {}
    cls = BY_STATUS.get(status, ServerError if status >= 500 else APIError)
    return cls(status, err.get("code", "unknown"), err.get("message", ""), correlation_id)
