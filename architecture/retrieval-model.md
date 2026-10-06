# Retrieval model

How the corpus is prepared for search engines, RAG pipelines, and AI agents. The goal: when a model answers from this documentation, it retrieves the **right** passage, knows **how much to trust it**, and can **cite** the canonical source.

## What goes wrong without a retrieval model

| Failure | Cause | Fix in this architecture |
|---|---|---|
| The answer mixes two products' behavior | Chunks carry no domain or audience | Every chunk inherits `domain` and `audience` and can be filtered on them |
| The answer quotes a superseded process | Old and new topics look equally authoritative | `status`, `canonical`, and `superseded_by` travel with every chunk |
| The answer is right but uncitable | Chunks have no stable address | Every chunk has an ID of the form `<topic-id>#<section-anchor>` |
| Half a procedure is retrieved | Fixed-size chunking cut it in two | Chunks follow H2 boundaries the content model defines |
| "The ID" is ambiguous | Identifier types aren't stated | Identifier semantics are required content (see [content model](content-model.md#identifier-semantics-are-part-of-the-content-model)) |
| A diagram is invisible to the model | The image has only a filename | `visual.alt` and `visual.describes` put its meaning in text, attached to the topic it explains |

## Chunking

Chunks follow the **structure authors already wrote**, not a token count.

1. The text between the H1 and the first H2 becomes the `overview` chunk (the summary and any status notice).
2. Each H2 section becomes one chunk, including its H3 subsections.
3. `Related topics` sections are **not** chunked: they're navigation, and their meaning is already in the `related` metadata.
4. Each chunk's text is prefixed with its heading path (`Change the dates or items on a rental agreement › Steps`), so a chunk read in isolation still says what it's about.

This works because the content model fixes which sections each topic type has. A procedure's `Steps` section is always one chunk, never split, never merged with `Before you begin`.

If a section grows beyond the embedding model's context budget, that's treated as a **content** defect (the section is doing too much) rather than solved by blind splitting.

## Metadata inheritance

Each chunk carries the topic's metadata, so filters and ranking can act on it without a second lookup:

```json
{
  "chunk_id": "procedure.rental.modify#steps",
  "topic_id": "procedure.rental.modify",
  "type": "procedure",
  "title": "Change the dates or items on a rental agreement",
  "section": "Steps",
  "heading_path": ["Change the dates or items on a rental agreement", "Steps"],
  "domain": "rental",
  "audience": ["branch-staff", "support"],
  "status": "validated",
  "canonical": true,
  "last_reviewed": "2026-08-25",
  "source": [{"system": "product-spec", "title": "Rental changes, functional specification", "ref": "SPEC-RENT-014", "version": "2.3"}],
  "related": ["concept.rental.agreement", "api.rental.update", "event.rental.updated"],
  "citation": {"path": "examples/procedure.md", "anchor": "steps"},
  "text": "Change the dates or items on a rental agreement › Steps\n\n1. Open the agreement..."
}
```

That record is produced by the validator's export step: see [`tooling/validate_corpus.py`](../tooling/validate_corpus.py).

## Ranking and filtering signals

The metadata is designed to be used at query time, not just stored.

| Signal | Use |
|---|---|
| `audience` | Pre-filter. A branch-staff assistant never sees developer-only chunks unless asked. |
| `domain` | Pre-filter or boost when the question names a capability. |
| `status` | Exclude `deprecated`. Down-rank `draft`, and label it in the answer ("this is draft guidance"). |
| `canonical` | Prefer canonical chunks when a derived topic (training, overview) says the same thing. |
| `type` | Route by intent: "how do I" → `procedure`; "what is" → `concept`; "what does field X mean" → `reference` or `api`. |
| `last_reviewed` | Tie-breaker, and a freshness warning when old. |

## The relationship graph

`related`, `supersedes`, and `visual.describes` are exported as a typed graph:

```json
{
  "nodes": [{"id": "procedure.rental.modify", "type": "procedure", "status": "validated", "path": "examples/procedure.md"}],
  "edges": [
    {"from": "procedure.rental.modify", "to": "api.rental.update", "kind": "related"},
    {"from": "training.rental.modify", "to": "procedure.rental.modify", "kind": "describes"}
  ]
}
```

An agent uses it for **query expansion**: after retrieving the best chunk, it pulls in one hop of related topics. That's how a question that starts in end-user language ("extend a rental") reaches the API and event documentation a developer needs, without the user knowing those words.

## Citations and provenance

Every answer built from the corpus can cite:

1. the **chunk ID**, which resolves to a file and an anchor on the published site
2. the topic's **status** and **validation** (who signed it off and when)
3. the topic's **sources**, which point back to the system of record

So the chain is: *answer → chunk → topic → source*. An answer that can't follow that chain shouldn't be presented as authoritative. See [provenance](provenance.md).

## Human and machine views of the same content

| Concern | Human view (site) | Machine view (export) |
|---|---|---|
| What is this? | Title and lede paragraph | `title`, `summary`, `type` |
| Who is it for? | Navigation section | `audience` |
| Can I trust it? | `DRAFT` banner, `TBC` markers | `status`, `validated_by`, `canonical` |
| What next? | Related topics list | `related` edges |
| Where did it come from? | Source table on the page | `source[]` |
| What does the picture show? | The picture | `visual.alt`, `visual.describes` |

There's one source file. Both views are generated from it, so they can't disagree.
