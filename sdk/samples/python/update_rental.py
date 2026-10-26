"""Extend a rental agreement. Shown in examples/sdk-quickstart-python.md."""
import os

from waypoint import Waypoint

RENTAL_ID = os.environ.get("WAYPOINT_RENTAL_ID", "3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa")
client = Waypoint()

# [START update_rental]
rental = client.rentals.get(RENTAL_ID)

updated = client.rentals.update(
    RENTAL_ID,
    if_match=rental.etag,                        # the revision you read
    end_date="2026-10-14",
    customer_approval_ref="CALL-2026-10-06-118",  # required: a later end date raises the price
)
print("Now ends", updated.end_date, "at", updated.etag)
# [END update_rental]
