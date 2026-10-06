"""Validate a documentation corpus and export retrieval artifacts.

    python tooling/validate_corpus.py <corpus-dir> [--export <out-dir>]

Every Markdown file with YAML frontmatter under <corpus-dir> is a topic.
Files without frontmatter (such as README.md) are skipped.

Checks (each failure names the file and the rule):
  schema      frontmatter matches schemas/topic.schema.json
  id-type     the ID prefix equals the declared type
  id-unique   no two topics share an ID
  relations   related / supersedes / superseded_by / visual.describes resolve
  title       the H1 equals the frontmatter title
  sections    the H2 sections required by the topic type are present
  status      draft shows a DRAFT notice; in-review and validated contain no TBC;
              validated shows no DRAFT notice
  visual      visual.asset exists
  links       relative Markdown links point to files that exist

With --export, writes:
  chunks.jsonl  one chunk per H2 section, carrying the topic's metadata
  graph.json    topics as nodes, typed relations as edges
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = ROOT / "schemas" / "topic.schema.json"

# The sections each topic type must contain, in the content model's words.
REQUIRED_SECTIONS = {
    "concept": ["How it works", "Key objects and identifiers", "Related topics"],
    "procedure": ["Before you begin", "Steps", "Result", "Related topics"],
    "reference": ["Related topics"],
    "api": ["Request", "Response", "Identifiers", "Side effects", "Errors", "Related topics"],
    "event": ["Trigger", "Payload", "Identifiers", "Consumers", "Ordering and idempotency", "Related topics"],
    "training": ["Learning objective", "Walkthrough", "Check your understanding", "Related topics"],
    "mapping": ["Summary", "Relationship", "Field mapping", "Transformation rules", "Code lookups",
                "Identifiers", "Gaps and decisions", "Related topics"],
    "decision": ["Decisions", "Gaps", "Related topics"],
    "glossary": ["Definitions", "Rules", "Related topics"],
}

# Sections that are navigation, not content: their meaning is already in `related`.
NOT_CHUNKED = {"Related topics"}

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", re.S)
FENCE = re.compile(r"^(```|~~~).*?^\1\s*$", re.S | re.M)
H1 = re.compile(r"^# (.+)$", re.M)
H2 = re.compile(r"^## (.+)$", re.M)
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)")
# MkDocs admonition or GitHub alert carrying the word DRAFT near the top of the page.
DRAFT_NOTICE = re.compile(r'(!!! warning "DRAFT"|> \[!WARNING\]\s*\n> \*\*DRAFT)')
TBC = re.compile(r"\bTBC\b")


@dataclass
class Topic:
    path: Path
    meta: dict
    body: str
    errors: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.meta.get("id", "")


def jsonable(value):
    """YAML turns ISO dates into date objects; the schema and the export want strings."""
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    return value


def slug(heading: str) -> str:
    """GitHub-style heading anchor."""
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def strip_code(text: str) -> str:
    return FENCE.sub("", text)


def load_topics(corpus: Path) -> list[Topic]:
    topics = []
    for path in sorted(corpus.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = FRONTMATTER.match(text)
        if not m:
            continue
        meta = jsonable(yaml.safe_load(m.group(1)) or {})
        topics.append(Topic(path, meta, m.group(2)))
    return topics


def sections(body: str) -> list[tuple[str, str]]:
    """Split a body into (heading, text). Text before the first H2 is 'Overview'."""
    prose = strip_code(body)
    heads = [(m.start(), m.group(1).strip()) for m in H2.finditer(prose)]
    # Re-find the headings in the original body so code blocks stay in the chunk text.
    out, cursor = [], 0
    starts = []
    for _, title in heads:
        idx = body.find(f"## {title}", cursor)
        starts.append((idx, title))
        cursor = idx + 1
    first = starts[0][0] if starts else len(body)
    out.append(("Overview", body[:first]))
    for i, (idx, title) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(body)
        out.append((title, body[idx + len(f"## {title}"):end]))
    return out


def check(topics: list[Topic], schema: dict) -> None:
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    ids: dict[str, Topic] = {}

    for t in topics:
        for err in sorted(validator.iter_errors(t.meta), key=lambda e: list(e.path)):
            where = ".".join(str(p) for p in err.path) or "(root)"
            t.errors.append(f"schema: {where}: {err.message}")

        if t.id and t.meta.get("type") and not t.id.startswith(t.meta["type"] + "."):
            t.errors.append(f"id-type: id '{t.id}' must start with '{t.meta['type']}.'")

        if t.id in ids:
            t.errors.append(f"id-unique: '{t.id}' is also used by {ids[t.id].path}")
        elif t.id:
            ids[t.id] = t

    for t in topics:
        m = t.meta
        prose = strip_code(t.body)

        refs = [("related", r) for r in m.get("related", [])]
        refs += [("supersedes", r) for r in m.get("supersedes", [])]
        if m.get("superseded_by"):
            refs.append(("superseded_by", m["superseded_by"]))
        if isinstance(m.get("visual"), dict) and m["visual"].get("describes"):
            refs.append(("visual.describes", m["visual"]["describes"]))
        for kind, ref in refs:
            if ref not in ids:
                t.errors.append(f"relations: {kind} -> '{ref}' does not resolve to any topic")
            elif ref == t.id:
                t.errors.append(f"relations: {kind} points to itself")

        h1 = H1.search(prose)
        if not h1:
            t.errors.append("title: no H1 heading")
        elif h1.group(1).strip() != m.get("title"):
            t.errors.append(f"title: H1 '{h1.group(1).strip()}' != frontmatter title '{m.get('title')}'")

        present = {h.strip() for h in H2.findall(prose)}
        for name in REQUIRED_SECTIONS.get(m.get("type"), []):
            if name not in present:
                t.errors.append(f"sections: '{m.get('type')}' topics need a '## {name}' section")

        status = m.get("status")
        has_notice = bool(DRAFT_NOTICE.search(t.body))
        tbc_lines, in_fence = [], False
        for i, line in enumerate(t.body.splitlines(), start=1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
            elif not in_fence and TBC.search(line):
                tbc_lines.append(i)
        if status == "draft" and not has_notice:
            t.errors.append("status: draft topics must show a DRAFT notice")
        if status in ("in-review", "validated") and tbc_lines:
            t.errors.append(f"status: {status} topics can't contain TBC (body lines {tbc_lines})")
        if status == "validated" and has_notice:
            t.errors.append("status: validated topics must not show a DRAFT notice")

        visual = m.get("visual")
        if isinstance(visual, dict) and visual.get("asset"):
            if not (t.path.parent / visual["asset"]).exists():
                t.errors.append(f"visual: asset '{visual['asset']}' not found")

        for match in LINK.finditer(prose):
            target = (match.group(1) or match.group(2)).split("#")[0]
            if not target or re.match(r"^[a-z]+:", target):
                continue  # same-page anchor or external URL
            if not (t.path.parent / target).exists():
                t.errors.append(f"links: '{target}' not found")


def export(topics: list[Topic], corpus: Path, out: Path) -> tuple[int, int]:
    out.mkdir(parents=True, exist_ok=True)
    inherited = ("type", "title", "domain", "audience", "status", "canonical", "owner",
                 "last_reviewed", "source", "related")
    chunks = []
    for t in topics:
        rel = t.path.relative_to(corpus.parent).as_posix()
        for heading, text in sections(t.body):
            if heading in NOT_CHUNKED:
                continue
            text = text.strip()
            if heading == "Overview":
                text = H1.sub("", text, count=1).strip()
            if not text:
                continue
            anchor = "" if heading == "Overview" else slug(heading)
            path = [t.meta["title"]] + ([] if heading == "Overview" else [heading])
            chunk = {
                "chunk_id": f"{t.id}#{anchor or 'overview'}",
                "topic_id": t.id,
                "section": heading,
                "heading_path": path,
                **{k: t.meta.get(k, True if k == "canonical" else None) for k in inherited},
                "citation": {"path": rel, "anchor": anchor},
                "text": " › ".join(path) + "\n\n" + text,
            }
            chunks.append(chunk)

    with (out / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    nodes = [{"id": t.id, "type": t.meta["type"], "title": t.meta["title"], "domain": t.meta["domain"],
              "status": t.meta["status"], "canonical": t.meta.get("canonical", True),
              "path": t.path.relative_to(corpus.parent).as_posix()} for t in topics]
    edges = []
    for t in topics:
        edges += [{"from": t.id, "to": r, "kind": "related"} for r in t.meta.get("related", [])]
        edges += [{"from": t.id, "to": r, "kind": "supersedes"} for r in t.meta.get("supersedes", [])]
        if isinstance(t.meta.get("visual"), dict) and t.meta["visual"].get("describes"):
            edges.append({"from": t.id, "to": t.meta["visual"]["describes"], "kind": "describes"})
    (out / "graph.json").write_text(json.dumps({"nodes": nodes, "edges": edges}, indent=2), encoding="utf-8")
    return len(chunks), len(edges)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus", type=Path, help="folder containing topic Markdown files")
    ap.add_argument("--export", type=Path, metavar="DIR", help="write chunks.jsonl and graph.json here")
    args = ap.parse_args()

    corpus = args.corpus.resolve()
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    topics = load_topics(corpus)
    if not topics:
        print(f"No topics with frontmatter found under {corpus}")
        return 1

    check(topics, schema)
    failed = [t for t in topics if t.errors]
    for t in topics:
        mark = "FAIL" if t.errors else "ok  "
        print(f"{mark} {t.path.relative_to(corpus.parent).as_posix():<36} {t.id} [{t.meta.get('status')}]")
        for e in t.errors:
            print(f"       - {e}")

    print(f"\n{len(topics)} topics, {len(failed)} failing")
    if failed:
        return 1

    if args.export:
        n_chunks, n_edges = export(topics, corpus, args.export)
        print(f"Exported {n_chunks} chunks and {n_edges} edges to {args.export}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
