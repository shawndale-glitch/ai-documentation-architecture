"""Check that the SDK can reach the API with your key.

    python -m waypoint.check

Prints where the key and base URL come from (never the full key), then sends
one authenticated request. Exit code 0 means you're ready for the quickstart.
"""
from __future__ import annotations

import os
import sys

from . import errors
from .client import DEFAULT_BASE_URL, Waypoint


def main() -> int:
    key = os.environ.get("WAYPOINT_API_KEY", "")
    base = os.environ.get("WAYPOINT_BASE_URL", "")

    if not key:
        print("FAIL WAYPOINT_API_KEY is not set in this terminal.")
        return 1
    shown = key[:12] if len(key) > 16 else key[:4]  # enough to tell keys apart, never the secret
    print(f"ok   API key   {shown}... (from WAYPOINT_API_KEY)")
    if key.startswith("wp_test_"):
        print("     test key: requests can't change live data")
    print(f"ok   Base URL  {base or DEFAULT_BASE_URL} ({'from WAYPOINT_BASE_URL' if base else 'default'})")

    try:
        status = Waypoint().status()
    except errors.AuthenticationError as e:
        print(f"FAIL The API rejected the key: {e.message}")
        return 1
    except errors.WaypointError as e:
        print(f"FAIL {e}")
        return 1
    print(f"ok   Connected to Waypoint API {status.get('apiVersion')} ({status.get('environment')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
