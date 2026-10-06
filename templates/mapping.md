---
id: mapping.<source-system>.<building-block>
type: mapping
title: <Legacy building block> to <target object>
summary: <One sentence: what this legacy building block holds and what it becomes in the target system.>
domain: migration
audience: [data-migration, developer]
status: draft
owner: Migration documentation
source:
  - system: workbook
    title: <Workbook title>
    ref: <file>.xlsx, sheet "<sheet>"
    version: "<version or date>"
    retrieved: <YYYY-MM-DD>
related:
  - decision.mapping.log
---
# <Legacy building block> to <target object>

> [!WARNING]
> **DRAFT.** Not yet validated. Remove this notice when an SME has reviewed the page.

<One sentence: what this legacy building block holds and what it becomes in the target system.>

## Summary

| | Legacy | Target |
|---|---|---|
| Object | <building block> | <object> |
| Module / API | <legacy module or table> | <API or configuration area> |
| Business-object scope | | |
| System of record after migration | | |

| | |
|---|---|
| Source workbook | `<file name>.xlsx`, sheet `<sheet>`, version `<version or date>` |
| Page status | Not started / In progress / In review / Validated |
| SME | <role> |

## Relationship

<Cardinality and ownership. For example: one legacy group maps to one target block and many bookings; the target system owns the block after migration.>

## Field mapping

Rows are generated from the source workbook. Don't edit them by hand.

| Legacy field | Target field | Rule | Identifier type | Required in target | Status | Notes |
|---|---|---|---|---|---|---|
| `<field>` | `<field or API path>` | Direct / T1 / L1 / Default `<value>` / — | — or Internal ID / External reference / Locator | Yes / No | Mapped / Transform / Gap / Not migrated / TBC | |

Every **Gap** row links a `G-nnn` entry and every **Not migrated** row links a `D-nnn` entry in the decision and gap log.

## Transformation rules

### T1: <rule name>

<What the rule does, in one or two sentences.>

| Legacy value | Target value |
|---|---|
| | |

## Code lookups

### L1: <legacy code set> to <target code set>

| Legacy code | Meaning | Target code | Notes |
|---|---|---|---|
| | | | |

## Identifiers

<Every legacy identifier on this building block and what happens to it. A legacy ID carried into the target is an external reference with the legacy source system; say exactly where it's stored.>

| Legacy identifier | Type in legacy system | Stored in target as | Location |
|---|---|---|---|
| | Internal ID / Locator | External reference / Not stored | |

## Gaps and decisions

- <G-nnn: short title>
- <D-nnn: short title>

## Related topics

- <decision and gap log>
