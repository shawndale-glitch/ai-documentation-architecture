"""Recover from a 412 when someone changed the agreement first.

Shown in examples/sdk-quickstart-python.md. To make the conflict happen on
every run, the script reads the agreement, then changes it "as someone else"
before calling extend_rental with the stale copy.
"""
import os

from waypoint import Waypoint

RENTAL_ID = os.environ.get("WAYPOINT_RENTAL_ID", "3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa")
client = Waypoint()

# [START handle_conflict]
from waypoint import PreconditionFailedError


def extend_rental(client, rental, end_date, approval_ref, attempts=3):
    """Apply the change to the latest revision, re-reading after each 412."""
    for _ in range(attempts):
        try:
            return client.rentals.update(
                rental.id,
                if_match=rental.etag,
                end_date=end_date,
                customer_approval_ref=approval_ref,
            )
        except PreconditionFailedError:
            rental = client.rentals.get(rental.id)  # changed since you read it
            print("Agreement changed; retrying on", rental.etag)
    raise RuntimeError(f"{rental.id} kept changing; giving up after {attempts} attempts")
# [END handle_conflict]


stale = client.rentals.get(RENTAL_ID)
client.rentals.update(RENTAL_ID, if_match=stale.etag, end_date=stale.end_date)  # someone else's edit

updated = extend_rental(client, stale, "2026-10-21", "CALL-2026-10-06-119")
print("Now ends", updated.end_date, "at", updated.etag)
