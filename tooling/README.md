# Tooling

The architecture only holds if the rules are cheap to follow and impossible to skip. Tooling does both: it removes the mechanical work from authors and turns the content rules into checks that run on every change.

| Tool | Job | In this repository |
|---|---|---|
| [Corpus validator and retrieval export](#corpus-validator-and-retrieval-export) | Enforce the metadata and content rules; produce chunks and a graph | Included, runnable |
| [Snippet drift check](#snippet-drift-check) | Keep every code block identical to a tested sample | Included, runnable |
| [AI review skill](#ai-review-skill) | Review SDK and API docs as an editor would, after the mechanical checks | [Included](../.claude/skills/review-sdk-docs/SKILL.md) |
| [Strict site build](#strict-site-build-and-publishing) | Fail on broken links or pages missing from navigation; publish | Described |
| [Media capture toolkit](#media-capture-toolkit) | Regenerate visuals from design boards and live UIs | Described |
| [Workbook import](#workbook-import) | Generate mapping tables from their system of record | Described |
| [AI import agent](#ai-import-agent) | Draft structured topics from source material, under guardrails | [Included](../agents/documentation-import.agent.md) |
| [Presentation as code](#presentation-as-code) | Build stakeholder decks from a reviewed, structured brief | Described |

## Corpus validator and retrieval export

[`validate_corpus.py`](validate_corpus.py) treats every Markdown file with frontmatter as a topic.

```bash
pip install -r tooling/requirements.txt
python tooling/validate_corpus.py examples                 # validate only
python tooling/validate_corpus.py examples --export build  # validate, then export
```

It runs two kinds of checks:

- **Per-topic** checks against [`schemas/topic.schema.json`](../schemas/topic.schema.json): required fields, controlled vocabularies, conditional requirements (a validated topic needs `validated_by`; a deprecated one needs `superseded_by`; API and event topics need an `interface`).
- **Cross-corpus** checks the schema can't express: unique IDs, ID prefix matches type, every relation resolves, H1 matches title, required sections per type, status rules (`TBC` and DRAFT notices), visual assets exist, relative links resolve.

The full rule list, and the reason for each rule, is in [validation](../validation/README.md).

Output on success:

```text
ok   examples/api.md                      api.rental.update [in-review]
ok   examples/concept.md                  concept.rental.agreement [validated]
...
8 topics, 0 failing
Exported 37 chunks and 23 edges to build
```

Output when something's wrong names the file and the rule:

```text
FAIL examples/procedure.md                procedure.rental.modify [validated]
       - relations: related -> 'event.rental.deleted' does not resolve to any topic
       - status: validated topics can't contain TBC (body lines [10])
```

The export writes `chunks.jsonl` and `graph.json`, described in the [retrieval model](../architecture/retrieval-model.md).

## Snippet drift check

[`check_snippets.py`](check_snippets.py) keeps code on the page and code in CI the same code. A block is bound to a region of a sample file by the comment before it:

````markdown
<!-- snippet: ../sdk/samples/python/get_rental.py#get_rental -->
```python
...
```
````

```bash
python tooling/check_snippets.py examples         # check
python tooling/check_snippets.py examples --fix   # copy drifted regions into the pages
```

It fails when a `python` block has no snippet comment (`bound`), when the sample or region is missing (`region`), or when the block differs from the region (`drift`). The [SDK tests](../sdk/python/tests/test_samples.py) then run every sample against the [mock API](../sdk/mock/server.py) and compare its output with the block under each `<!-- output-of: -->` comment. See [`sdk/`](../sdk/README.md) for the whole loop.

## AI review skill

[`review-sdk-docs`](../.claude/skills/review-sdk-docs/SKILL.md) is a Claude Code skill that engineers run on a docs change before a writer reviews it. It runs the validator, the drift check, and the tests first, then reviews what tooling can't: API claims with no source, identifiers used as the wrong type, error paths missing from the samples or the errors table, unsafe retries, secrets in code. Every finding cites `path:line` and its evidence; anything it can't support becomes an open question. It never changes `status` or removes `TBC`.

## Strict site build and publishing

The private implementation publishes the corpus as a MkDocs Material site:

- Every pull request runs `mkdocs build --strict`. A broken link, a missing anchor, or a page not listed in navigation **fails the check**, so the PR can't merge.
- Every merge to `main` rebuilds the site and deploys it to GitHub Pages through GitHub Actions. No one publishes by hand.
- Light and dark themes, full-text search, "edit this page" links back to the source file, copyable code blocks, and Mermaid rendering.

The same workflow pattern runs the validator in this repository: see [`.github/workflows/validate.yml`](../.github/workflows/validate.yml).

## Media capture toolkit

Diagrams drawn on collaborative design boards are where a lot of architecture knowledge first appears. Copying them into documentation by hand means they go stale the day after. The toolkit makes capture a command.

Built with **Playwright** (browser automation) and **Node.js**, with a single PowerShell entry point and matching VS Code tasks so non-developers can run it from a menu.

| Command | What it does |
|---|---|
| `setup` | Install Playwright and Chromium |
| `login` | Open a browser so the **user signs in themselves**; save the session (never credentials) to a git-ignored folder |
| `list` | Show the boards registered in a JSON config |
| `board --board <id>` | Capture one registered board as an image |
| `boards` | Capture every registered board |
| `page --url <u> --name <n> [--full \| --selector <css>]` | Screenshot any page, or a single element |
| `pdf <url> <name>` | Save a page as PDF |
| `codegen [url]` | Record clicks into a new automation script |
| `new-poc <name>` | Scaffold a proof-of-concept folder and its media folder from a template |
| `manifest` | Rebuild the machine-readable media index and its human-readable twin |
| `archive [days]` | Move captures older than N days out of the working set |

Design decisions worth calling out:

- **Stable "latest" paths.** Every capture is saved twice: a timestamped file for history, and `<id>_latest.png`. Documentation references the latest path, so a topic's `visual.asset` never goes stale and never needs editing when the diagram changes.
- **A registry, not ad hoc URLs.** Boards are declared once in a config file (`id`, `url`, optional section `nodeId`, `owner`, `notes`), so captures are repeatable and reviewable.
- **Deterministic capture.** The script waits for the canvas, zooms to fit, hides the editor chrome, and captures at a fixed viewport and scale, so two captures of an unchanged board are comparable.
- **A media manifest.** `manifest.json` (for machines) and `INDEX.md` (for people) list every asset, its category, size, and age, regenerated before each commit.
- **Retention.** Only the newest N timestamped captures per board are kept; older media is archived after a set number of days.
- **No secrets in the repository.** The user authenticates interactively; only the browser session state is stored, in a git-ignored folder.

Design boards render to a canvas, so captures are raster images of the canvas, not vector exports. Where vector output matters, the design tool's own export or API is the better source; the toolkit is for keeping visual context current, cheaply.

## Workbook import

Some facts have a structured system of record outside the docs, such as field-level mappings maintained in spreadsheets by a migration team. Per [D-001](../examples/decision-log.md#d-001-source-of-truth-for-field-level-mappings), those rows are **generated, not typed**:

1. Read the workbook with `openpyxl`, using a versioned column layout.
2. Emit the field mapping table for each mapping topic between generated-content markers.
3. Leave narrative, transformation rules, gaps, and decisions untouched; people write those.
4. Record the workbook file, sheet, and version in the topic's `source` metadata.

In the private implementation this is designed and its dependency is in place; the generator is written once the source workbooks have a stable layout. Building a parser against a layout that's still changing would just move the drift somewhere else.

## AI import agent

A reusable agent definition that turns source material (documents, wikis, spreadsheets, trackers, work boards) into draft topics, with fidelity and provenance guardrails written into its configuration. See [AI-assisted workflow](../architecture/ai-workflow.md) and the [agent definition](../agents/documentation-import.agent.md).

## Presentation as code

Stakeholder decks about the documentation system are built the same way the documentation is: from a structured, reviewable source.

1. Raw material (workshop notes, architecture docs, meeting transcripts) is turned into a **slide-by-slide brief**: title, one-sentence message, content points, and visual per slide, plus an explicit list of open gaps with owners. Missing figures are marked as pending, never invented.
2. The brief is reviewed and approved as text.
3. A Python build script (`python-pptx`) generates the deck from the approved brief using a fixed set of slide archetypes (cover, key message, comparison table, timeline, annotated screenshot), and screenshots are captured by the media toolkit.
4. Each build is rendered to PDF and checked page by page before it's shared.

The same principle as the docs: separate **what we're saying** (reviewed content) from **how it's laid out** (generated), so changing one doesn't break the other.
