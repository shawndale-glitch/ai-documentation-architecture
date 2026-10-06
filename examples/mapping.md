---
id: mapping.legacy.customer
type: mapping
title: Legacy customer record to customer account
summary: >-
  How each field of a Classic customer record is carried into a Waypoint
  customer account: direct copy, transformation, code lookup, gap, or left behind.
domain: migration
audience: [data-migration, developer, support]
status: draft
owner: Migration documentation
canonical: true
source:
  - system: workbook
    title: Customer migration mapping
    ref: customer-mapping.xlsx, sheet "Accounts"
    version: "v4, 2026-09-12"
    retrieved: 2026-09-15
last_reviewed: 2026-09-15
related:
  - decision.mapping.log
  - glossary.identifiers
tags: [classic, customer]
---
# Legacy customer record to customer account

> [!WARNING]
> **DRAFT.** Field rows are generated from the workbook. Items marked **TBC** need confirmation from the migration team.

A Classic **customer record** holds a business customer's identity, contacts, and credit terms. In Waypoint it becomes a **customer account**, with contacts as child records.

## Summary

| | Classic | Waypoint |
|---|---|---|
| Object | Customer record | Customer account |
| Module / API | `CUST` table | Customers API, `POST /accounts` |
| Business-object scope | One record per billing customer | One account per billing customer; contacts as children |
| System of record after migration | — | Waypoint |

| | |
|---|---|
| Source workbook | `customer-mapping.xlsx`, sheet `Accounts`, version `v4, 2026-09-12` |
| Page status | In progress |
| SME | Migration lead, customer data |

## Relationship

One Classic customer record maps to one Waypoint customer account. Classic stores up to three contacts as columns on the record; Waypoint stores each as a separate contact under the account. Waypoint owns the account after migration; Classic becomes read-only.

## Field mapping

The rows in this table are generated from the workbook and aren't edited by hand. See [D-001](decision-log.md#d-001-source-of-truth-for-field-level-mappings).

| Classic field | Waypoint field | Rule | Identifier type | Required in Waypoint | Status | Notes |
|---|---|---|---|---|---|---|
| `CUST_NO` | `externalRefs[]` (`sourceSystem: classic`) | Direct | External reference | No | Mapped | See [Identifiers](#identifiers) and [D-002](decision-log.md#d-002-legacy-identifiers-become-external-references) |
| `CUST_NAME` | `legalName` | [T1](#t1-trim-and-normalize-legal-name) | — | Yes | Transform | |
| `VAT_ID` | `taxId` | Direct | — | Yes | Mapped | |
| `CUST_CLASS` | `segment` | [L1](#l1-customer-class-to-segment) | — | Yes | Transform | |
| `CONTACT1_*` … `CONTACT3_*` | `contacts[]` | [T2](#t2-contact-columns-to-contact-records) | — | No | Transform | |
| `CREDIT_LIMIT` | `credit.limit` | Direct | — | No | Mapped | Currency taken from `CUR` |
| `HOLD_REASON` | — | — | — | — | Gap | [G-001](decision-log.md#g-001-free-text-credit-hold-reason) |
| `FAX_NO` | — | — | — | — | Not migrated | [D-003](decision-log.md#d-003-fax-numbers-are-not-migrated) |
| `REGION_CD` | `region` | TBC | — | Yes | TBC | Target code set not yet agreed |

## Transformation rules

### T1: Trim and normalize legal name

Trim whitespace, collapse repeated spaces, and keep the original casing. Classic stored some names in upper case; they're migrated as is, not title-cased, because legal names can't be safely re-cased.

| Classic value | Waypoint value |
|---|---|
| `"  ACME  PLANT HIRE LTD "` | `"ACME PLANT HIRE LTD"` |

### T2: Contact columns to contact records

Each non-empty `CONTACTn_NAME` becomes one contact. Contact 1 is flagged `primary: true`.

## Code lookups

### L1: Customer class to segment

| Classic code | Meaning | Waypoint segment | Notes |
|---|---|---|---|
| `A` | Key account | `enterprise` | |
| `B` | Regular trade | `trade` | |
| `C` | Cash customer | `retail` | |
| `X` | Blocked | — | Not migrated; blocked accounts are reviewed manually. TBC: confirm with credit control |

## Identifiers

| Classic identifier | Type in Classic | Stored in Waypoint as | Location |
|---|---|---|---|
| `CUST_NO` | Internal ID | External reference | `externalRefs[]` with `sourceSystem: classic` |
| `ACCOUNT_CODE` | Locator | Not stored | Replaced by the Waypoint account number |

## Gaps and decisions

- [D-001](decision-log.md#d-001-source-of-truth-for-field-level-mappings): Source of truth for field-level mappings
- [D-002](decision-log.md#d-002-legacy-identifiers-become-external-references): Legacy identifiers become external references
- [D-003](decision-log.md#d-003-fax-numbers-are-not-migrated): Fax numbers are not migrated
- [G-001](decision-log.md#g-001-free-text-credit-hold-reason): Free-text credit hold reason

## Related topics

- [Mapping decision and gap log](decision-log.md)
- [Identifier glossary](glossary.md)
