---
id: event.rental.updated
type: event
title: Rental agreement updated (event)
summary: >-
  rental.agreement.updated is emitted after every new revision of a rental
  agreement; billing and the fleet planner consume it to reprice and replan.
domain: rental
audience: [developer, integrator]
status: draft
owner: Rental platform documentation
canonical: true
source:
  - system: asyncapi
    title: Waypoint rental events
    ref: rental-events.yaml, channel rental.agreement.updated
    version: "0.9.0"
    retrieved: 2026-09-05
last_reviewed: 2026-09-05
interface:
  kind: event
  name: rental.agreement.updated
  version: 2
  producer: Waypoint rental service
related:
  - api.rental.update
  - concept.rental.agreement
  - glossary.identifiers
tags: [events]
---
# Rental agreement updated (event)

> [!WARNING]
> **DRAFT.** Structure and identifiers are in place. Items marked **TBC** need confirmation from the rental service team before this page moves to review.

`rental.agreement.updated` (version 2) is emitted after every new revision of a rental agreement. Billing uses it to create charges and refunds; the fleet planner uses it to free or reserve units.

## Trigger

A new revision is stored, by [Update a rental agreement](api.md) or by an internal process such as an automatic extension. One revision produces exactly one event.

## Payload

```json
{
  "eventId": "e3c9a1f4-7b2d-4c8e-9f10-6a5d4b3c2e1f",
  "eventType": "rental.agreement.updated",
  "eventVersion": 2,
  "occurredAt": "2026-10-06T10:42:17Z",
  "correlationId": "0b7e4a52-91c3-4d6e-8f20-5c1a9e7d3b44",
  "rentalId": "3f6c1d9e-8a42-4b1f-9a0e-2d7c51b0e8aa",
  "revision": 5,
  "changes": ["endDate", "lines"],
  "priceDelta": { "amount": "184.00", "currency": "EUR" }
}
```

The event carries **what changed**, not the full agreement. Consumers that need the full state call `GET /rentals/{rentalId}` with the revision.

## Identifiers

| Identifier | Owning system | Type | Scope | Notes |
|---|---|---|---|---|
| `eventId` | Waypoint rental service | Internal ID | This event | Use it to deduplicate. |
| `rentalId` | Waypoint | Internal ID | Rental agreement | The key consumers join on. |
| `revision` | Waypoint | Internal ID (sequence) | Revision within one agreement | Increases by one per change. |
| `correlationId` | The original caller | Correlation ID | One business operation | Same value as the `X-Correlation-ID` of the request that caused it. |

## Consumers

| Consumer | Uses it to | Status |
|---|---|---|
| Billing service | Create a pending charge or refund from `priceDelta` | Confirmed |
| Fleet planner | Release or reserve units for the changed dates | Confirmed |
| Customer notifications | Send the updated confirmation | TBC: consumes this event or is called directly |

## Ordering and idempotency

- Events for the same `rentalId` are delivered in `revision` order. Partition key: `rentalId`.
- Delivery is at least once. Consumers deduplicate on `eventId`.
- Retention on the topic is TBC.

## Related topics

- [Update a rental agreement (API)](api.md)
- [What a rental agreement is](concept.md)
- [Identifier glossary](glossary.md)
