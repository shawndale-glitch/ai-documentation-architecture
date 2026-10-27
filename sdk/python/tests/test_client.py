import pytest

import waypoint
from waypoint import Waypoint

OPEN = "3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa"
CLOSED = "7a1e5c3b-2d4f-4e6a-8b9c-0d1e2f3a4b5c"


def test_missing_key_is_a_configuration_error(monkeypatch):
    monkeypatch.delenv("WAYPOINT_API_KEY", raising=False)
    with pytest.raises(waypoint.ConfigurationError, match="WAYPOINT_API_KEY"):
        Waypoint()


def test_bad_base_url_is_a_configuration_error():
    with pytest.raises(waypoint.ConfigurationError, match="http"):
        Waypoint(api_key="wp_test_x", base_url="localhost:8080")


def test_get_returns_rental_and_etag(api):
    rental = Waypoint().rentals.get(OPEN)
    assert rental.agreement_number == "BCN-2026-004417"
    assert rental.etag == '"rev-4"'
    assert rental.lines[0].unit_id == "EXC-0412"


def test_update_stores_new_revision(api):
    client = Waypoint()
    rental = client.rentals.get(OPEN)
    updated = client.rentals.update(OPEN, if_match=rental.etag, end_date="2026-10-14", customer_approval_ref="A")
    assert (updated.end_date, updated.revision, updated.etag) == ("2026-10-14", 5, '"rev-5"')


def test_stale_etag_raises_precondition_failed(api):
    client = Waypoint()
    with pytest.raises(waypoint.PreconditionFailedError) as e:
        client.rentals.update(OPEN, if_match='"rev-1"', end_date="2026-10-10")
    assert e.value.status == 412 and e.value.code == "revision_mismatch"


def test_price_increase_needs_approval(api):
    client = Waypoint()
    rental = client.rentals.get(OPEN)
    with pytest.raises(waypoint.UnprocessableEntityError) as e:
        client.rentals.update(OPEN, if_match=rental.etag, end_date="2026-10-30")
    assert e.value.code == "customer_approval_required"


def test_closed_agreement_raises_conflict(api):
    client = Waypoint()
    rental = client.rentals.get(CLOSED)
    with pytest.raises(waypoint.ConflictError):
        client.rentals.update(CLOSED, if_match=rental.etag, end_date="2026-09-08", customer_approval_ref="A")


def test_unknown_id_raises_not_found(api):
    with pytest.raises(waypoint.NotFoundError):
        Waypoint().rentals.get("00000000-0000-0000-0000-000000000000")


def test_wrong_key_raises_authentication_error(api):
    with pytest.raises(waypoint.AuthenticationError):
        Waypoint(api_key="live_123").status()


def test_errors_carry_the_correlation_id(api):
    with pytest.raises(waypoint.NotFoundError) as e:
        Waypoint().rentals.get("00000000-0000-0000-0000-000000000000")
    assert e.value.correlation_id


def test_server_errors_are_retried_with_the_same_idempotency_key(api):
    client = Waypoint()
    rental = client.rentals.get(OPEN)
    api.state.fail_next = 2  # first two attempts get 503
    updated = client.rentals.update(OPEN, if_match=rental.etag, end_date="2026-10-14",
                                    customer_approval_ref="A", idempotency_key="k-1")
    assert updated.revision == 5


def test_replayed_idempotency_key_returns_first_result(api):
    client = Waypoint()
    rental = client.rentals.get(OPEN)
    first = client.rentals.update(OPEN, if_match=rental.etag, end_date="2026-10-14",
                                  customer_approval_ref="A", idempotency_key="k-2")
    again = client.rentals.update(OPEN, if_match=rental.etag, end_date="2026-10-14",
                                  customer_approval_ref="A", idempotency_key="k-2")
    assert again.revision == first.revision == 5  # applied once, not twice


def test_retries_give_up_and_raise_server_error(api):
    api.state.fail_next = 3
    with pytest.raises(waypoint.ServerError):
        Waypoint(max_retries=2).rentals.get(OPEN)
