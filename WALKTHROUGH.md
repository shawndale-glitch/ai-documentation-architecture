# Interview walkthrough

A 15-minute live demonstration, designed to run entirely from this repository. The production POC is private and contains client content, so I don't screen-share it; everything below shows the same patterns working on a fictional corpus.

## 1. The problem (2 min)

Open the [README](README.md#why-this-matters).

- Documentation is usually written for one consumer: a person reading a page.
- RAG systems and agents are a second consumer with different needs: predictable structure, explicit relationships, identifiable authority, and machine-readable trust signals.
- The architecture makes those needs first-class, and enforces them with tooling.

## 2. One topic, two representations (3 min)

Open [`examples/procedure.md`](examples/procedure.md) in raw view, then rendered.

- **Frontmatter**: type, stable ID, domain, audience, status, owner, sources, validation, relations.
- **Body**: the sections the procedure type requires; intent and "not for" stated up front; one action per step.
- Same file, two readers: the person sees a clean procedure; the machine sees typed, filterable, citable metadata.

## 3. The knowledge model (3 min)

Open [`examples/training.md`](examples/training.md), then the [content model diagram](architecture/content-model.md#how-types-relate).

- The visual isn't a filename: `visual.describes` binds it to the procedure it explains, with alt text a text-only model can read.
- `canonical: false`: training restates the procedure, so a retriever prefers the procedure.
- Follow the edges: procedure → API → event. That's how an agent answers "what happens downstream when staff extend a rental?"

## 4. The gate (3 min)

Run it live:

```bash
python tooling/validate_corpus.py examples --export build
```

Then break something on purpose (add `TBC` to a validated topic, or point `related` at an ID that doesn't exist) and run it again. The gate names the file and the rule.

Then open `build/chunks.jsonl`: one chunk per section, each carrying the topic's metadata and a citation anchor.

## 5. Provenance and decisions (2 min)

Open [`examples/mapping.md`](examples/mapping.md) and the [decision log](examples/decision-log.md).

- Field rows are generated from their system of record; people write the rules, gaps, and decisions.
- Numbered decisions (`D-nnn`) and gaps (`G-nnn`) are never renumbered, so "why wasn't this migrated?" has a permanent answer with a name and a date.

## 6. AI in the workflow (2 min)

Open the [agent definition](agents/documentation-import.agent.md) and the [AI-assisted workflow](architecture/ai-workflow.md).

- Guardrails are configuration: no invented facts, `TBC` instead of guessing, contradictions reported not resolved, provenance always recorded, no publishing without a person.
- The model does the mechanical work; a person decides what becomes canonical.

## 7. Developer docs as tested code (3 min, for developer-docs roles)

Open the [Python SDK quickstart](examples/sdk-quickstart-python.md), then one [sample file](sdk/samples/python/handle_conflict.py).

- Every code block is a region of a sample file. CI runs every sample against the [mock API](sdk/mock/server.py) on the oldest and newest supported Python, and fails if the page's code or shown output differs from what really runs.
- Break it live: change one line in a sample, run `python tooling/check_snippets.py examples`, show the drift failure, then `--fix`.
- The [review skill](.claude/skills/review-sdk-docs/SKILL.md) is the AI editor: it runs those checks, then reviews what tooling can't (claims without a source, identifier misuse, missing error paths) and cites a line for every finding. A person still approves.

## Questions I expect

| Question | Short answer |
|---|---|
| Why not just embed the existing docs? | You can, and you'll retrieve contradictory, stale, uncitable passages. The architecture fixes the corpus so retrieval has something reliable to work with. |
| Doesn't frontmatter slow authors down? | Templates pre-fill it and the AI agent drafts it. The gate catches what's missing. Most fields are set once per topic. |
| How does this scale to thousands of topics? | IDs, controlled vocabularies, and the graph are what make it scale: they let you filter, route, and audit without reading everything. |
| What's implemented versus designed? | See [what is implemented where](architecture/overview.md#what-is-implemented-where). |
