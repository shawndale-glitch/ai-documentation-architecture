"""Read a rental agreement. Shown in examples/sdk-quickstart-python.md."""
import os

RENTAL_ID = os.environ.get("WAYPOINT_RENTAL_ID", "3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa")

# [START get_rental]
from waypoint import Waypoint

client = Waypoint()  # reads WAYPOINT_API_KEY and WAYPOINT_BASE_URL

rental = client.rentals.get(RENTAL_ID)
print(rental.agreement_number, rental.status, "ends", rental.end_date, "at", rental.etag)
# [END get_rental]
