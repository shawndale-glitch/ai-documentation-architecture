import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "sdk" / "mock"))

import server as mock  # noqa: E402


@pytest.fixture
def api(monkeypatch):
    """A fresh mock API, with the SDK's environment variables pointing at it."""
    with mock.running() as srv:
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        monkeypatch.setenv("WAYPOINT_API_KEY", "wp_test_pytest_key")
        monkeypatch.setenv("WAYPOINT_BASE_URL", url)
        yield srv
