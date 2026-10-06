---
id: api.rental.update
type: api
title: Update a rental agreement (API)
summary: >-
  PATCH /rentals/{rentalId} changes the dates or lines of an open rental
  agreement, creates a new revision, and emits rental.agreement.updated.
domain: rental
audience: [developer, integrator]
status: in-review
owner: Rental platform documentation
canonical: true
source:
  - system: openapi
    title: Waypoint Rentals API
    ref: rentals-api.yaml, operation updateRental
    version: "1.8.0"
    retrieved: 2026-09-02
  - system: sme-review
    title: Review with rental service tech lead
    retrieved: 2026-09-04
last_reviewed: 2026-09-04
interface:
  kind: http
  method: PATCH
  path: /rentals/{rentalId}
  operation_id: updateRental
related:
  - concept.rental.agreement
  - procedure.rental.modify
  - event.rental.updated
  - glossary.identifiers
tags: [rentals-api]
---
# Update a rental agreement (API)

`PATCH /rentals/{rentalId}` changes the dates or lines of an open rental agreement. It's the call the branch console makes in [Change the dates or items on a rental agreement](procedure.md). This page explains the business meaning, the identifiers, and the side effects; the exact field list is in the generated OpenAPI reference for operation `updateRental`.

## Request

```http
PATCH /rentals/3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa
If-Match: "rev-4"
Idempotency-Key: 6a1f0c2e-1d34-4f8b-a0b9-7f3e2c9d5a10
X-Correlation-ID: 0b7e4a52-91c3-4d6e-8f20-5c1a9e7d3b44
Content-Type: application/merge-patch+json

{
  "endDate": "2026-10-14",
  "lines": [
    { "lineId": "9d2b7c41-5e8f-4a3b-b6d0-1c4e2f8a7b95", "unitId": "EXC-0457" }
  ],
  "customerApprovalRef": "CALL-2026-10-06-118"
}
```

| Element | Meaning |
|---|---|
| `rentalId` (path) | The agreement's internal ID in Waypoint. Never the agreement number. |
| `If-Match` | The revision you read. The call fails with `412` if someone changed the agreement since. |
| `Idempotency-Key` | Lets you retry safely. The same key within 24 hours returns the first result. |
| `X-Correlation-ID` | Traces this business operation across services and into the emitted event. |
| `customerApprovalRef` | Required when the change increases the price. |

## Response

`200 OK` with the full agreement at its new revision, and an `ETag` header carrying the new revision (`"rev-5"`).

## Identifiers

| Identifier | Owning system | Type | Scope | Notes |
|---|---|---|---|---|
| `rentalId` | Waypoint | Internal ID | Rental agreement | Use it to address the agreement in every API call. |
| `agreementNumber` (response) | Waypoint | Locator | Rental agreement | Human-facing. Don't join or upsert on it. |
| `lineId` | Waypoint | Internal ID | Agreement line, within one agreement | Unique only within its agreement. |
| `unitId` | Waypoint fleet service | Internal ID | Fleet unit | Owned by the fleet service, referenced here. |
| `externalRefs[]` (response) | Other systems | External reference | Rental agreement | Each entry is a value plus its `sourceSystem`, for example the legacy Classic contract number. |
| `X-Correlation-ID` | The caller | Correlation ID | One operation | Not stored as the agreement's identity. |

## Side effects

- A new revision is stored; the previous revision stays readable at `GET /rentals/{rentalId}/revisions/{n}`.
- A [`rental.agreement.updated`](event.md) event is emitted with the same correlation ID.
- If the price changes, billing creates a pending charge or refund from that event, not from this call.

## Errors

| Status | When | What to do |
|---|---|---|
| `409 Conflict` | The agreement is closed or cancelled | Use an invoice adjustment instead |
| `412 Precondition Failed` | `If-Match` doesn't match the current revision | Read the agreement again and reapply the change |
| `422 Unprocessable Entity` | Unit not available for the new dates, or `customerApprovalRef` missing on a price increase | Show the reason to the user |

## Related topics

- [What a rental agreement is](concept.md)
- [Change the dates or items on a rental agreement](procedure.md)
- [Rental agreement updated (event)](event.md)
- [Identifier glossary](glossary.md)
