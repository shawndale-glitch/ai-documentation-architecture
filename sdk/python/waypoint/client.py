"""The Waypoint API client.

    from waypoint import Waypoint

    client = Waypoint()                     # reads WAYPOINT_API_KEY and WAYPOINT_BASE_URL
    rental = client.rentals.get(rental_id)
    rental = client.rentals.update(rental_id, if_match=rental.etag, end_date="2026-10-14", ...)

Standard library only, so the quickstart has one install step and no
dependency conflicts.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from . import errors

DEFAULT_BASE_URL = "https://api.waypoint.example"
USER_AGENT = "waypoint-python/0.1.0"

# Status codes worth retrying. Safe for PATCH because every update carries an
# Idempotency-Key: a retry with the same key returns the first result.
RETRYABLE = {429, 500, 502, 503, 504}


@dataclass
class RentalLine:
    line_id: str
    unit_id: str


@dataclass
class Rental:
    """One revision of a rental agreement, as returned by the API."""

    id: str                     # rentalId: internal ID, use it in every call
    agreement_number: str       # locator: human-facing, never a key
    status: str
    start_date: str
    end_date: str
    revision: int
    etag: str                   # pass back as if_match when you update
    lines: list[RentalLine] = field(default_factory=list)
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, body: dict, etag: str) -> "Rental":
        return cls(
            id=body["rentalId"],
            agreement_number=body["agreementNumber"],
            status=body["status"],
            start_date=body["startDate"],
            end_date=body["endDate"],
            revision=body["revision"],
            etag=etag,
            lines=[RentalLine(l["lineId"], l["unitId"]) for l in body.get("lines", [])],
            raw=body,
        )


class Rentals:
    def __init__(self, client: "Waypoint"):
        self._client = client

    def get(self, rental_id: str) -> Rental:
        """GET /rentals/{rentalId}: the current revision."""
        body, headers = self._client._request("GET", f"/rentals/{rental_id}")
        return Rental.from_api(body, headers.get("ETag", ""))

    def update(
        self,
        rental_id: str,
        *,
        if_match: str,
        end_date: Optional[str] = None,
        lines: Optional[list[RentalLine]] = None,
        customer_approval_ref: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Rental:
        """PATCH /rentals/{rentalId}: store a new revision.

        `if_match` is the `etag` of the revision you read. If someone changed
        the agreement since, this raises PreconditionFailedError.
        """
        patch: dict[str, Any] = {}
        if end_date is not None:
            patch["endDate"] = end_date
        if lines is not None:
            patch["lines"] = [{"lineId": l.line_id, "unitId": l.unit_id} for l in lines]
        if customer_approval_ref is not None:
            patch["customerApprovalRef"] = customer_approval_ref
        body, headers = self._client._request(
            "PATCH",
            f"/rentals/{rental_id}",
            body=patch,
            headers={
                "If-Match": if_match,
                "Idempotency-Key": idempotency_key or str(uuid.uuid4()),
                "Content-Type": "application/merge-patch+json",
            },
            correlation_id=correlation_id,
        )
        return Rental.from_api(body, headers.get("ETag", ""))


class Waypoint:
    """Client for the Waypoint Rentals API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        *,
        max_retries: int = 2,
        timeout: float = 10.0,
    ):
        self.api_key = api_key or os.environ.get("WAYPOINT_API_KEY", "")
        if not self.api_key:
            raise errors.ConfigurationError(
                "No API key. Set WAYPOINT_API_KEY or pass api_key= to Waypoint()."
            )
        self.base_url = (base_url or os.environ.get("WAYPOINT_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        if not self.base_url.startswith(("http://", "https://")):
            raise errors.ConfigurationError(f"Base URL must start with http:// or https://, got {self.base_url!r}")
        self.max_retries = max_retries
        self.timeout = timeout
        self.rentals = Rentals(self)

    def status(self) -> dict:
        """GET /status: confirms the key works and returns the API version."""
        body, _ = self._request("GET", "/status")
        return body

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
        correlation_id: Optional[str] = None,
    ) -> tuple[dict, dict]:
        correlation_id = correlation_id or str(uuid.uuid4())
        all_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "X-Correlation-ID": correlation_id,
            **(headers or {}),
        }
        data = json.dumps(body).encode() if body is not None else None

        # The same headers, including Idempotency-Key, go out on every attempt.
        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(self.base_url + path, data=data, headers=all_headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read() or b"{}"), dict(resp.headers)
            except urllib.error.HTTPError as e:
                if e.code in RETRYABLE and attempt < self.max_retries:
                    time.sleep(0.2 * 2 ** attempt)
                    continue
                try:
                    err_body = json.loads(e.read() or b"{}")
                except ValueError:
                    err_body = {}
                raise errors.from_response(e.code, err_body, correlation_id) from None
            except urllib.error.URLError as e:
                if attempt < self.max_retries:
                    time.sleep(0.2 * 2 ** attempt)
                    continue
                raise errors.APIConnectionError(f"Couldn't reach {self.base_url}: {e.reason}") from None
        raise AssertionError("unreachable")
