---
id: procedure.rental.modify
type: procedure
title: Change the dates or items on a rental agreement
summary: >-
  Extend, shorten, or change the equipment on an open rental agreement from the
  branch console, and see what the customer is charged before you confirm.
domain: rental
audience: [branch-staff, support]
status: validated
owner: Rental operations documentation
canonical: true
source:
  - system: product-spec
    title: Rental changes, functional specification
    ref: SPEC-RENT-014
    version: "2.3"
    retrieved: 2026-08-18
  - system: sme-review
    title: Walkthrough with branch operations lead
    retrieved: 2026-08-22
validated_by:
  role: Branch operations lead
  date: 2026-08-25
last_reviewed: 2026-08-25
related:
  - concept.rental.agreement
  - api.rental.update
  - event.rental.updated
tags: [extension, pricing]
---
# Change the dates or items on a rental agreement

Extend, shorten, or change the equipment on an open rental agreement from the branch console. You see the price difference before you confirm, so you can quote it to the customer.

**Intent.** Use this when a customer asks to keep equipment longer, return it early, or swap a unit. **Not for:** correcting a closed agreement. That's an invoice adjustment.

## Before you begin

- The agreement is **open** or **on hire**. See [agreement states](concept.md#how-it-works).
- You have the **Branch agent** role.
- You have the agreement number (for example `FL-2026-004211`) or the customer's account.

## Steps

1. In the branch console, select **Rentals**, then search for the agreement number.
2. Open the agreement and select **Change agreement**.
3. Change the **End date**, or select **Swap unit** on the line you want to change.
4. Review the **Price difference** panel. It shows the new total and the amount to charge or refund.
5. Select **Confirm change**. If the price goes up, the console asks for the customer's approval reference first.

## Result

The agreement shows a new revision number and the updated dates, items, and total. The customer receives an updated confirmation by email.

Behind the scenes, Waypoint calls [Update a rental agreement](api.md) and emits a [`rental.agreement.updated`](event.md) event, which billing and the fleet planner consume.

## Related topics

- [What a rental agreement is](concept.md)
- [Update a rental agreement (API)](api.md)
- [Rental agreement updated (event)](event.md)
- [Learn to change a rental agreement](training.md)
