"""Catch the business-rule errors from an update. Shown in examples/sdk-quickstart-python.md."""
import os

from waypoint import Waypoint

RENTAL_ID = os.environ.get("WAYPOINT_RENTAL_ID", "3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa")
CLOSED_RENTAL_ID = "7a1e5c3b-2d4f-4e6a-8b9c-0d1e2f3a4b5c"
client = Waypoint()

# [START handle_errors]
from waypoint import ConflictError, UnprocessableEntityError


def try_extend(rental_id, end_date, approval_ref=None):
    rental = client.rentals.get(rental_id)
    try:
        client.rentals.update(
            rental_id, if_match=rental.etag, end_date=end_date, customer_approval_ref=approval_ref
        )
        print(rental.agreement_number, "extended to", end_date)
    except ConflictError as e:
        print(rental.agreement_number, "can't change:", e.code)  # closed or cancelled
    except UnprocessableEntityError as e:
        print(rental.agreement_number, "rejected:", e.code)  # show e.message to the user


try_extend(RENTAL_ID, "2026-10-30")                  # no approval reference
try_extend(CLOSED_RENTAL_ID, "2026-09-08", "CALL-1")  # agreement already closed
# [END handle_errors]
