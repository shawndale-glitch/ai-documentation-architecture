---
id: decision.mapping.log
type: decision
title: Mapping decision and gap log
summary: >-
  A numbered, permanent record of every mapping decision (D-nnn) and gap
  (G-nnn) in the Classic to Waypoint migration, so pages link instead of repeat.
domain: migration
audience: [data-migration, developer, support, writer]
status: draft
owner: Migration documentation
canonical: true
source:
  - system: meeting-notes
    title: Migration design reviews
    ref: Weekly migration design review, 2026-09
    retrieved: 2026-09-19
last_reviewed: 2026-09-19
related:
  - mapping.legacy.customer
---
# Mapping decision and gap log

> [!WARNING]
> **DRAFT.** Entries marked **Proposed** are not yet agreed.

A numbered record of mapping decisions and gaps. Mapping pages link here (for example `[D-002](decision-log.md#d-002-legacy-identifiers-become-external-references)`) instead of repeating the reasoning, so each decision is explained once and stays findable.

**Rules.** Take the next free number: `D-nnn` for a decision, `G-nnn` for a gap. Never reuse or renumber an entry. When a gap is resolved, don't delete it: set its status to **Resolved** and link the decision that resolved it.

## Decisions

### D-001: Source of truth for field-level mappings

| | |
|---|---|
| Status | Agreed |
| Date | 2026-09-10 |
| Decided by | Migration lead; documentation lead |
| Affects | All mapping pages |

**Context.** The mapping workbooks and the documentation both describe field-level mappings. If both are edited by hand, they drift apart.

**Decision.** The workbooks stay authoritative for field-level rows. Field mapping tables in the documentation are generated from the workbooks by a script and aren't edited by hand. Narrative, transformation rules, gaps, and decisions are written by hand around the generated tables.

**Consequences.** A mapping row is changed in the workbook first, then the tables are regenerated. The script depends on the workbooks keeping a stable column layout, so the layout is now versioned.

### D-002: Legacy identifiers become external references

| | |
|---|---|
| Status | Agreed |
| Date | 2026-09-12 |
| Decided by | Integration architect |
| Affects | [Legacy customer record to customer account](mapping.md) |

**Context.** Support staff still search by Classic customer numbers during the transition.

**Decision.** Every Classic internal ID that's kept is stored as an external reference with `sourceSystem: classic`. It's never reused as a Waypoint ID or account number.

**Consequences.** Lookups by Classic number go through the external-reference search. See the [identifier glossary](glossary.md).

### D-003: Fax numbers are not migrated

| | |
|---|---|
| Status | Proposed |
| Date | 2026-09-19 |
| Decided by | Migration lead (proposed) |
| Affects | [Legacy customer record to customer account](mapping.md) |

**Context.** 4% of Classic customer records have a fax number; none were used for correspondence in the last two years.

**Decision.** Fax numbers are left behind. The Classic archive keeps them.

**Consequences.** No Waypoint field is needed. Support is told where to look in the archive.

## Gaps

### G-001: Free-text credit hold reason

| | |
|---|---|
| Status | Open |
| Date | 2026-09-15 |
| Raised by | Migration analyst |
| Affects | [Legacy customer record to customer account](mapping.md) |

**Impact.** Classic stores why an account is on credit hold as free text. Waypoint has a coded hold reason only, so the explanation would be lost.

**Options.** Map common phrases to codes and keep the original text as a note; add a free-text field; or leave it in the Classic archive.

## Related topics

- [Legacy customer record to customer account](mapping.md)
