"""A local stand-in for the Waypoint Rentals API, for the quickstart and CI.

    python sdk/mock/server.py            # serves http://localhost:8080
    python sdk/mock/server.py --port 9000

It implements the behavior documented in examples/api.md: If-Match revision
checks (412), Idempotency-Key replay, closed agreements (409), and the
customer-approval rule on price increases (422). State lives in memory and
resets on every start. Any key that starts with `wp_test_` is accepted.

Standard library only, so any language's samples can run against it.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator, Optional

API_VERSION = "1.8.0"
RENTAL_PATH = re.compile(r"^/rentals/([0-9a-f-]{36})$")
UNAVAILABLE_UNITS = {"EXC-0999"}  # booked for every date, to show a 422

SEED = {
    "3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa": {
        "rentalId": "3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa",
        "agreementNumber": "BCN-2026-004417",
        "status": "open",
        "startDate": "2026-10-01",
        "endDate": "2026-10-10",
        "revision": 4,
        "lines": [{"lineId": "9d2b7c41-5e8f-4a3b-b6d0-1c4e2f8a7b95", "unitId": "EXC-0412"}],
        "externalRefs": [{"value": "C-88213", "sourceSystem": "classic"}],
    },
    "7a1e5c3b-2d4f-4e6a-8b9c-0d1e2f3a4b5c": {
        "rentalId": "7a1e5c3b-2d4f-4e6a-8b9c-0d1e2f3a4b5c",
        "agreementNumber": "BCN-2026-003980",
        "status": "closed",
        "startDate": "2026-09-01",
        "endDate": "2026-09-05",
        "revision": 7,
        "lines": [{"lineId": "1b2c3d4e-5f60-4718-9a0b-c1d2e3f4a5b6", "unitId": "EXC-0233"}],
        "externalRefs": [],
    },
}


class State:
    def __init__(self):
        self.rentals = copy.deepcopy(SEED)
        self.idempotency: dict[str, tuple[int, dict, dict]] = {}
        self.fail_next = 0  # tests set this to make the next N requests return 503
        self.lock = threading.Lock()


def error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


class Handler(BaseHTTPRequestHandler):
    server_version = "WaypointMock/" + API_VERSION
    state: State  # set on the class by make_server

    def log_message(self, fmt, *args):  # keep test output quiet
        if getattr(self.server, "verbose", False):
            super().log_message(fmt, *args)

    def send(self, status: int, body: dict, headers: Optional[dict] = None) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        if self.headers.get("X-Correlation-ID"):
            self.send_header("X-Correlation-ID", self.headers["X-Correlation-ID"])
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def authorized(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer wp_test_"):
            return True
        self.send(401, error("invalid_api_key", "Use a key that starts with wp_test_ against the mock server."))
        return False

    def injected_failure(self) -> bool:
        with self.state.lock:
            if self.state.fail_next > 0:
                self.state.fail_next -= 1
                self.send(503, error("unavailable", "Injected failure for testing retries."))
                return True
        return False

    def do_GET(self):
        if self.injected_failure() or not self.authorized():
            return
        if self.path == "/status":
            return self.send(200, {"apiVersion": API_VERSION, "environment": "mock"})
        m = RENTAL_PATH.match(self.path)
        rental = self.state.rentals.get(m.group(1)) if m else None
        if not rental:
            return self.send(404, error("not_found", "No rental agreement with that rentalId."))
        self.send(200, rental, {"ETag": f'"rev-{rental["revision"]}"'})

    def do_PATCH(self):
        if self.injected_failure() or not self.authorized():
            return
        m = RENTAL_PATH.match(self.path)
        key = self.headers.get("Idempotency-Key", "")
        length = int(self.headers.get("Content-Length") or 0)
        patch = json.loads(self.rfile.read(length) or b"{}")

        with self.state.lock:
            if key and key in self.state.idempotency:
                return self.send(*self.state.idempotency[key])
            result = self.apply(m.group(1) if m else "", patch)
            if key and result[0] < 500:
                self.state.idempotency[key] = result
        self.send(*result)

    def apply(self, rental_id: str, patch: dict) -> tuple[int, dict, dict]:
        rental = self.state.rentals.get(rental_id)
        if not rental:
            return 404, error("not_found", "No rental agreement with that rentalId."), {}
        if rental["status"] in ("closed", "cancelled"):
            return 409, error("agreement_not_open", f"The agreement is {rental['status']}. Use an invoice adjustment."), {}
        current = f'"rev-{rental["revision"]}"'
        if self.headers.get("If-Match") != current:
            return 412, error("revision_mismatch", f"The agreement is now at {current}. Read it again and reapply."), {}
        for line in patch.get("lines", []):
            if line.get("unitId") in UNAVAILABLE_UNITS:
                return 422, error("unit_unavailable", f"Unit {line['unitId']} isn't available for these dates."), {}
        if patch.get("endDate", "") > rental["endDate"] and not patch.get("customerApprovalRef"):
            return 422, error("customer_approval_required", "Extending the agreement raises the price; send customerApprovalRef."), {}

        if "endDate" in patch:
            rental["endDate"] = patch["endDate"]
        if "lines" in patch:
            by_id = {l["lineId"]: l for l in rental["lines"]}
            for line in patch["lines"]:
                by_id.setdefault(line["lineId"], {"lineId": line["lineId"]})["unitId"] = line["unitId"]
            rental["lines"] = list(by_id.values())
        rental["revision"] += 1
        return 200, copy.deepcopy(rental), {"ETag": f'"rev-{rental["revision"]}"'}


def make_server(port: int = 8080, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    state = State()
    handler = type("BoundHandler", (Handler,), {"state": state})
    server = ThreadingHTTPServer((host, port), handler)
    server.state = state  # type: ignore[attr-defined]
    return server


@contextlib.contextmanager
def running(port: int = 0) -> Iterator[ThreadingHTTPServer]:
    """Run a fresh mock in a background thread; port 0 picks a free port."""
    server = make_server(port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    server = make_server(args.port)
    server.verbose = True  # type: ignore[attr-defined]
    print(f"Waypoint mock API {API_VERSION} on http://localhost:{args.port}  (Ctrl+C to stop)")
    print("Use any API key that starts with wp_test_, for example wp_test_quickstart")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
