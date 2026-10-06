# Metadata model

Every topic starts with YAML frontmatter. The frontmatter is the machine-readable half of the topic: it tells the gate what rules apply, tells the site how to file the page, and tells a retriever what a chunk is about, who it's for, and how far to trust it.

The contract is enforced by [`schemas/topic.schema.json`](../schemas/topic.schema.json) plus the cross-file rules in the [validator](../tooling/validate_corpus.py).

## A complete example

```yaml
---
id: procedure.rental.modify
type: procedure
title: Change the dates or items on a rental agreement
summary: >-
  Extend, shorten, or change the equipment on an open rental agreement
  from the branch console, and what the customer is charged.
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
```

## Fields

| Field | Required | Type | Purpose |
|---|---|---|---|
| `id` | Yes | string | Stable identity. See [ID grammar](#id-grammar). |
| `type` | Yes | enum | Topic type from the [content model](content-model.md#topic-types). Must match the ID prefix. |
| `title` | Yes | string | Must match the H1. Sentence case. |
| `summary` | Yes | string, ≤ 300 chars | One or two sentences. Used as the page lede, the search snippet, and the retrieval abstract. |
| `domain` | Yes | enum | Business capability the topic belongs to. |
| `audience` | Yes | enum[] | Who the topic is written for. Used for filtering at query time. |
| `status` | Yes | enum | `draft`, `in-review`, `validated`, `deprecated`. See [provenance](provenance.md#status-lifecycle). |
| `owner` | Yes | string | The role accountable for keeping the topic accurate. A role, not a person, so it survives staff changes. |
| `canonical` | No (default `true`) | boolean | `true` if this topic is the authoritative home for its facts. `false` for derived topics, such as training that restates a procedure. |
| `source` | Yes | object[] | Where the facts came from: `system`, `title`, `ref`, `version`, `retrieved`. At least one entry. |
| `validated_by` | When `status: validated` | object | `role` and `date` of the subject-matter sign-off. |
| `last_reviewed` | No | date | When the content was last checked against its sources. |
| `related` | No | ID[] | Topics a reader or agent should consider next. Every ID must resolve. |
| `supersedes` | No | ID[] | Topics this one replaces. |
| `superseded_by` | When `status: deprecated` | ID | The topic that replaces this one. |
| `visual` | No | object | A visual and what it means. See [Visuals](#visuals). |
| `interface` | For `api` and `event` | object | The machine contract: HTTP method and path, or event name and version. |
| `tags` | No | string[] | Free keywords. Not used for filtering; controlled fields are. |

## ID grammar

```text
<type>.<domain-or-area>.<slug>[.<slug>...]

procedure.rental.modify
api.rental.update
event.rental.updated
mapping.legacy.customer
glossary.identifiers
```

Rules:

- Lowercase letters, digits, and hyphens; dot-separated segments.
- The first segment is the topic type, and must equal `type`.
- IDs are **never reused and never renamed**. If a topic's meaning changes enough to need a new ID, create the new topic, set `supersedes` on it, and deprecate the old one with `superseded_by`.
- Links between topics in metadata always use IDs, never file paths.

Why dotted IDs rather than paths or UUIDs: a path changes when someone reorganizes folders, which breaks every reference and every embedding keyed on it. A UUID is stable but meaningless to the reviewer reading the diff. A dotted ID is stable **and** tells a human, a search filter, and an LLM what the topic is before it's opened.

## Controlled vocabularies

Filtering only works if values are predictable. These fields accept a fixed list, defined once in the schema:

| Field | Values |
|---|---|
| `type` | `concept`, `procedure`, `reference`, `api`, `event`, `training`, `mapping`, `decision`, `glossary` |
| `domain` | `rental`, `customer`, `fleet`, `billing`, `platform`, `migration`, `documentation` |
| `audience` | `branch-staff`, `trainer`, `support`, `developer`, `integrator`, `data-migration`, `writer` |
| `status` | `draft`, `in-review`, `validated`, `deprecated` |
| `visual.type` | `diagram`, `screenshot`, `animation`, `video` |

Adding a value is a schema change, reviewed like code. That friction is intentional: a vocabulary that anyone can extend in a single topic stops being a vocabulary.

## Visuals

A visual is metadata, not decoration.

```yaml
visual:
  type: diagram
  asset: assets/modify-rental-flow.svg
  describes: procedure.rental.modify
  alt: "Five-step flow for changing the dates or items on an open rental agreement"
```

| Field | Meaning |
|---|---|
| `type` | What kind of visual it is. Retrieval can prefer a diagram for "how does it flow" questions and a screenshot for "where do I click" questions. |
| `asset` | Path relative to the topic. The gate checks it exists. |
| `describes` | The ID of the topic the visual explains. This is what lets a visual be retrieved for a question about the procedure, even though the visual lives on a training topic. |
| `alt` | A text equivalent. Required: it's the accessible description for people and the only part of the visual a text-only model can read. |

Captured visuals (board exports, UI screenshots) come from the [media capture toolkit](../tooling/README.md#media-capture-toolkit), which writes to stable `_latest` paths so `asset` references never go stale.

## Interface contracts

`api` and `event` topics carry their contract in metadata so they can be matched to specs and to each other:

```yaml
interface:
  kind: http
  method: PATCH
  path: /rentals/{rentalId}
  operation_id: updateRental
```

```yaml
interface:
  kind: event
  name: rental.agreement.updated
  version: 2
  producer: Waypoint rental service
```

When OpenAPI or AsyncAPI specs exist, `operation_id` and `name` are the join keys between the hand-written topic (business meaning, identifier semantics) and the generated reference (exact fields). The hand-written topic never repeats the field list; it links to it.
