# Validation

The validation gate is where the architecture stops being a set of good intentions. Every rule below runs on every pull request; a failure blocks the merge.

Each rule exists to protect a specific consumer: the human reader, the search index, or the AI system answering from the corpus.

## Rules

| Rule | Check | Protects against |
|---|---|---|
| `schema` | Frontmatter matches [`topic.schema.json`](../schemas/topic.schema.json): required fields, types, controlled vocabularies | Metadata that filters and rankers can't rely on |
| `schema` (conditional) | `validated` needs `validated_by`; `deprecated` needs `superseded_by`; `api` and `event` need `interface` | Trust signals without evidence; dead ends for retired content |
| `id-type` | The ID prefix equals `type` | IDs that lie about what they identify |
| `id-unique` | No two topics share an ID | Ambiguous citations; one chunk overwriting another in an index |
| `relations` | Every `related`, `supersedes`, `superseded_by`, and `visual.describes` resolves to a real topic, and not to itself | A relationship graph with dangling edges; agents following links to nothing |
| `title` | The H1 equals the frontmatter `title` | Search results and chunks that name a different thing than the page |
| `sections` | The H2 sections required by the topic type exist | Unpredictable structure; chunks that don't line up with intent |
| `status` | `draft` shows a DRAFT notice; `in-review` and `validated` contain no `TBC`; `validated` has no DRAFT notice | Unconfirmed facts presented as confirmed |
| `visual` | `visual.asset` exists | Visual metadata that points at nothing |
| `links` | Relative Markdown links and images resolve | Broken navigation for readers |

In the private implementation, the strict site build adds: every page is in navigation, every in-site anchor exists, and no absolute internal links.

## Running it

```bash
python tooling/validate_corpus.py examples
```

Exit code `0` means every topic passed; `1` means at least one failed, with the file and rule named for each failure. CI uses the exit code; see [`.github/workflows/validate.yml`](../.github/workflows/validate.yml).

## What validation doesn't do

Validation proves the corpus is **well-formed**, not that it's **true**. A topic can pass every rule and still be wrong. That's why:

- `validated` requires a named role and date (`validated_by`), set by a person in a reviewed pull request
- the AI import agent must report "build passed" and "content approved" as separate things
- `TBC` exists: the honest state of a fact is sometimes "not yet confirmed", and the gate makes sure that state can't be hidden

## Extending the rules

Rules worth adding as the corpus grows:

| Candidate rule | Why |
|---|---|
| Reciprocal relations warning | `A related B` without `B related A` is often an oversight |
| Staleness | Warn when `last_reviewed` is older than a threshold for the topic's type |
| Source drift | Warn when a source's `version` is older than the latest known version of that source |
| Generated-region integrity | Fail when generated mapping tables were edited by hand |
| Section length budget | Warn when a section is too large to be one good retrieval chunk |
| Terminology | Flag banned or ambiguous terms ("the ID") using a project vocabulary |
