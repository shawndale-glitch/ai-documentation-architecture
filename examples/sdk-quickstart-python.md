---
id: quickstart.rental.python-sdk
type: quickstart
title: Change a rental agreement with the Python SDK
summary: >-
  Install the Waypoint Python SDK, check your setup, read a rental agreement,
  extend it, and recover from the two errors every integration meets: a stale
  revision (412) and a business-rule rejection (422).
domain: rental
audience: [developer, integrator]
status: in-review
owner: Developer experience documentation
canonical: true
source:
  - system: sdk-source
    title: waypoint-python SDK
    ref: sdk/python/waypoint
    version: "0.1.0"
    retrieved: 2026-10-26
  - system: openapi
    title: Waypoint Rentals API
    ref: rentals-api.yaml, operations getStatus, getRental, updateRental
    version: "1.8.0"
    retrieved: 2026-09-02
last_reviewed: 2026-10-26
related:
  - api.rental.update
  - event.rental.updated
  - concept.rental.agreement
  - glossary.identifiers
tags: [rentals-api, python-sdk]
---
# Change a rental agreement with the Python SDK

In about ten minutes you install the SDK, read a rental agreement, extend it by four days, and handle the errors your integration will see in production.

**Intent.** Use this to make your first working calls from Python. **Not for:** the full field list or every status code, which are in [Update a rental agreement (API)](api.md).

Every code block on this page is a region of a file in [`sdk/samples/python/`](../sdk/samples/python/). CI runs those files against the mock API on every change, and fails if a block here no longer matches its file.

## Before you begin

- Python 3.9 or later: `python3 --version`.
- A Waypoint **test** API key. Test keys start with `wp_test_`.
- No account? Run the mock API from this repository instead. It behaves like the real API for everything on this page and accepts any `wp_test_` key:

  ```bash
  python sdk/mock/server.py
  ```

  Leave it running in its own terminal. It listens on `http://localhost:8080` and resets its data every time it starts.

## Install the SDK

From the repository root, in a new terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install ./sdk/python
```

Then give the SDK your key and, for the mock, its address:

```bash
export WAYPOINT_API_KEY=wp_test_quickstart
export WAYPOINT_BASE_URL=http://localhost:8080   # leave unset to use the real API
```

The SDK reads both variables when you create a client. You can also pass them to `Waypoint(api_key=..., base_url=...)`, but don't commit a key to source control.

## Check your setup

```bash
python -m waypoint.check
```

```text
ok   API key   wp_test_quic... (from WAYPOINT_API_KEY)
     test key: requests can't change live data
ok   Base URL  http://localhost:8080 (from WAYPOINT_BASE_URL)
ok   Connected to Waypoint API 1.8.0 (mock)
```

The check shows where each setting came from and only the start of the key, then makes one authenticated call to `GET /status`. If a line says `FAIL`, fix that line before going on: a wrong key or URL is the most common reason a first call fails.

## Make your first call

Read an agreement by its `rentalId`. In the samples, `RENTAL_ID` is `3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa`, an open agreement the mock creates on start:

<!-- snippet: ../sdk/samples/python/get_rental.py#get_rental -->
```python
from waypoint import Waypoint

client = Waypoint()  # reads WAYPOINT_API_KEY and WAYPOINT_BASE_URL

rental = client.rentals.get(RENTAL_ID)
print(rental.agreement_number, rental.status, "ends", rental.end_date, "at", rental.etag)
```

<!-- output-of: ../sdk/samples/python/get_rental.py -->
```text
BCN-2026-004417 open ends 2026-10-10 at "rev-4"
```

Three values matter for the next step:

| Value | What it is | Use it to |
|---|---|---|
| `rental.id` | The `rentalId`, Waypoint's internal ID for the agreement | Address the agreement in every call |
| `rental.agreement_number` | A locator for people, such as `BCN-2026-004417` | Show to staff and customers. Never use it as a key |
| `rental.etag` | The revision you just read, `"rev-4"` | Pass back as `if_match` when you change the agreement |

See the [identifier glossary](glossary.md) for why the internal ID and the locator are never interchangeable.

## Change the agreement

Extend the agreement to 14 October. A later end date raises the price, so the API requires the reference of the customer's approval:

<!-- snippet: ../sdk/samples/python/update_rental.py#update_rental -->
```python
rental = client.rentals.get(RENTAL_ID)

updated = client.rentals.update(
    RENTAL_ID,
    if_match=rental.etag,                        # the revision you read
    end_date="2026-10-14",
    customer_approval_ref="CALL-2026-10-06-118",  # required: a later end date raises the price
)
print("Now ends", updated.end_date, "at", updated.etag)
```

<!-- output-of: ../sdk/samples/python/update_rental.py -->
```text
Now ends 2026-10-14 at "rev-5"
```

The update stores a new revision and emits a [`rental.agreement.updated`](event.md) event, which billing uses to create the extra charge. You don't call billing yourself.

Each call sends an `Idempotency-Key`, so the SDK can safely retry a request that failed on the network or with a `5xx`: the API returns the first result instead of applying the change twice. Revision numbers in your output are higher if you ran the samples more than once; restart the mock to reset them.

## Handle a conflict

If someone changes the agreement between your read and your update, the API rejects the update with `412 Precondition Failed` instead of overwriting their change. The SDK raises `PreconditionFailedError`. Read the agreement again and reapply your change to the new revision:

<!-- snippet: ../sdk/samples/python/handle_conflict.py#handle_conflict -->
```python
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
```

<!-- output-of: ../sdk/samples/python/handle_conflict.py -->
```text
Agreement changed; retrying on "rev-5"
Now ends 2026-10-21 at "rev-6"
```

Reapply your **change**, not the whole agreement you read. If the other change makes yours unnecessary or invalid, stop and show the user what changed.

## Handle errors

Business-rule errors aren't retried: retrying the same request gets the same answer. Catch the ones your code can explain to a user:

<!-- snippet: ../sdk/samples/python/handle_errors.py#handle_errors -->
```python
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
```

<!-- output-of: ../sdk/samples/python/handle_errors.py -->
```text
BCN-2026-004417 rejected: customer_approval_required
BCN-2026-003980 can't change: agreement_not_open
```

| Exception | Status | When | What to do |
|---|---|---|---|
| `AuthenticationError` | `401` | The key is missing, malformed, or revoked | Run `python -m waypoint.check` |
| `NotFoundError` | `404` | No agreement with that `rentalId` | Check you used the internal ID, not the agreement number |
| `ConflictError` | `409` | The agreement is closed or cancelled | Use an invoice adjustment instead |
| `PreconditionFailedError` | `412` | The agreement changed since you read it | Read again and reapply, as in [Handle a conflict](#handle-a-conflict) |
| `UnprocessableEntityError` | `422` | A unit isn't available, or `customer_approval_ref` is missing on a price increase | Show `e.message` to the user |
| `ServerError`, `APIConnectionError` | `5xx`, network | The API failed or couldn't be reached, after the SDK's retries | Log `e.correlation_id` and try again later |

Every `APIError` carries `status`, `code`, `message` and `correlation_id`. Quote the correlation ID when you contact support: it traces the request across Waypoint's services.

## Related topics

- [Update a rental agreement (API)](api.md)
- [Rental agreement updated (event)](event.md)
- [What a rental agreement is](concept.md)
- [Identifier glossary](glossary.md)
