---
id: glossary.identifiers
type: glossary
title: Identifier glossary
summary: >-
  The four identifier types every topic must use (internal ID, external
  reference, locator, correlation ID), with the rules that keep integrations safe.
domain: platform
audience: [developer, integrator, data-migration, support, writer]
status: validated
owner: Platform documentation
canonical: true
source:
  - system: architecture-guideline
    title: Waypoint integration guidelines, identifiers chapter
    ref: ARCH-INT-003
    version: "1.2"
    retrieved: 2026-07-30
validated_by:
  role: Integration architect
  date: 2026-08-04
last_reviewed: 2026-08-04
related:
  - concept.rental.agreement
  - api.rental.update
  - mapping.legacy.customer
---
# Identifier glossary

Integrations break when two different kinds of identifier get treated as the same thing. Use these four terms, and only these, whenever you document an identifier.

## Definitions

| Type | Definition | Issued by | Stable? | Unique within | Use it to |
|---|---|---|---|---|---|
| **Internal ID** | The primary key a system assigns to its own record. | The owning system | Yes, for the life of the record | That system | Address the record in that system's APIs |
| **External reference** | Another system's identifier, stored on this record to link the two. | The *other* system; stored here | As stable as the other system's ID | The pair (value + source system) | Find the counterpart record in the other system |
| **Locator** | A human-facing lookup value, such as an agreement number. | Usually the owning system | Not guaranteed; may be reissued | Often per branch or per region | Let customers and staff find a record |
| **Correlation ID** | A value attached to a request or event to trace one business operation across systems. | The originator of the operation | Per operation, not per record | The operation | Trace, debug, and deduplicate |

## Rules

- An external reference is meaningless without its **source system**. Always store and document both.
- A locator is **not** a key. Don't join or upsert on it.
- A correlation ID identifies an **operation**, not a business object. Don't store it as a record's identity.
- Always state the **business-object scope**: an agreement ID is not a customer ID, and a line ID is unique only within its agreement.
- An identifier carried over from a legacy system is an **external reference** with that source system, whatever it was in the legacy system. Document exactly where it's stored.

## Related topics

- [What a rental agreement is](concept.md)
- [Update a rental agreement (API)](api.md)
- [Legacy customer record to customer account](mapping.md)
