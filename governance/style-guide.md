# Style guide

Short rules for writing topics in this corpus. When in doubt, favor precision over brevity. Most of these rules exist because they make content easier to retrieve and harder to misread, for people and for models alike.

## Voice and tone

- US English, second person ("you"), present tense, active voice.
- Lead with what the reader needs to do or know. Background goes after.
- One idea per paragraph. One action per numbered step.
- State intent in procedures: when to use it, and the nearest wrong use.

## Topic types

| Type | Answers | Template |
|---|---|---|
| Concept | What is it? How does it work? | [`templates/concept.md`](../templates/concept.md) |
| Procedure | How do I do X? | [`templates/task.md`](../templates/task.md) |
| Reference | What are the exact values? | [`templates/reference.md`](../templates/reference.md) |
| Mapping | Where does this legacy data go in the new system? | [`templates/mapping.md`](../templates/mapping.md) |
| API, event, training, glossary, decision | See the [content model](../architecture/content-model.md#topic-types) | See [examples](../examples/) |

Don't mix types on one page. Link between them instead.

## Identifiers and relationships

Integration documentation lives or dies on identifier precision. Always:

- Name the **owning system** of every identifier.
- Say whether it's an **internal ID**, an **external reference**, a **locator**, or a **correlation ID**. See the [identifier glossary](../examples/glossary.md).
- State the **business-object scope** (agreement, customer, fleet unit, line).
- State the **relationship** when an identifier links two objects (one-to-one, one-to-many, and which side owns it).

Never write "the ID" without saying which one.

## Status markers

| Marker | Meaning | Rule |
|---|---|---|
| `status: draft` + a visible **DRAFT** notice at the top | Structure in place; content not yet validated | Required together; the gate checks both |
| `TBC` in a sentence or table cell | One specific fact still needs confirmation | Not allowed in `in-review` or `validated` topics |
| `status: validated` + `validated_by` | A named role confirmed the content against its sources | Remove the DRAFT notice and every `TBC` in the same pull request |

The DRAFT notice uses the renderer's syntax: `!!! warning "DRAFT"` on a MkDocs site, `> [!WARNING]` on GitHub. The validator accepts both.

## Formatting

- Headings: sentence case. One H1 per topic, identical to the frontmatter `title`.
- H2 sections are retrieval chunk boundaries. Use the section names the topic type requires; don't rename them.
- Code, field names, headers, and literal values: `backticks`.
- UI labels: **bold**.
- Tables for comparisons and field lists, not prose.
- Diagrams: Mermaid in fenced code blocks, or SVG, so they stay diffable. Every visual needs alt text that states what it shows.

## File names and IDs

- Files: lowercase, hyphen-separated, named for the topic, not the ticket.
- IDs: `<type>.<domain>.<slug>`. Never reuse or rename an ID. See the [metadata model](../architecture/metadata-model.md#id-grammar).

## Workflow

1. Branch from `main`: `docs/<short-topic>`.
2. Start new topics from a template.
3. Run the validator locally and fix every failure.
4. Open a pull request. Say what changed and **who validated the content**.
5. Merge after review. Publishing and retrieval export run automatically.

Commit messages use a short, imperative summary line:

```text
docs(rental): add agreement change procedure
docs(migration): map legacy customer record
build: pin jsonschema 4.23
```
