# Examples

A small, valid corpus that shows the content model, metadata model, and provenance rules working together.

The examples describe **Waypoint**, the platform of **Fieldline Rentals**, a fictional equipment-rental company, and its migration away from a fictional legacy system called **Classic**. None of it is real client material. The domain was chosen because it has the same documentation problems as any integration-heavy business: several systems, several kinds of identifier, end users and developers looking at the same operation from different sides, and a legacy migration that needs every decision recorded.

## The topic cluster

| Topic | Type | Status | Shows |
|---|---|---|---|
| [What a rental agreement is](concept.md) | `concept` | validated | Object model and identifier semantics |
| [Change the dates or items on a rental agreement](procedure.md) | `procedure` | validated | One action per step; intent and consequence stated |
| [Learn to change a rental agreement](training.md) | `training` | validated | Derived content (`canonical: false`); a visual bound to the procedure it explains |
| [Update a rental agreement (API)](api.md) | `api` | in-review | Business meaning of an endpoint; identifiers; side effects |
| [Rental agreement updated (event)](event.md) | `event` | draft | Event contract; `TBC` used precisely |
| [Identifier glossary](glossary.md) | `glossary` | validated | The four identifier types every topic must use |
| [Legacy customer record to customer account](mapping.md) | `mapping` | draft | Field mapping, transformation rules, code lookups, gaps |
| [Mapping decision and gap log](decision-log.md) | `decision` | draft | Numbered, permanent decision and gap records |

Validate them and export the retrieval artifacts:

```bash
python tooling/validate_corpus.py examples --export build
```

## Rendering note

Status notices here use GitHub alert syntax (`> [!WARNING]`) so they render on GitHub. The production site uses MkDocs admonitions (`!!! warning "DRAFT"`). The validator accepts either.
