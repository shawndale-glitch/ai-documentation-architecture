"""Check that code in the docs is the code CI runs.

    python tooling/check_snippets.py <corpus-dir> [--fix]

A code block is bound to a region of a tested sample file by a comment on the
line before it:

    <!-- snippet: ../sdk/samples/python/get_rental.py#get_rental -->
    ```python
    ...
    ```

The region is the lines between `# [START get_rental]` and `# [END get_rental]`
in that file. Paths are relative to the Markdown file.

Checks (each failure names the file, the line, and the rule):
  bound     every ```python block in the corpus has a snippet comment, so no
            untested code reaches readers
  region    the sample file exists and contains the region exactly once
  drift     the block is identical to the region (after removing the region's
            common indentation)
  output    each `<!-- output-of: <sample> -->` comment names a sample that
            exists and is followed by a code block; sdk/python/tests compares
            that block with the sample's real output

With --fix, rewrites drifted blocks from their sample files. Run it, review the
diff, and commit: the sample is the source of truth, the page is generated.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

MARKER = re.compile(r"^<!--\s*(snippet|output-of):\s*(\S+?)\s*-->\s*$")
FENCE_OPEN = re.compile(r"^(```|~~~)(\w*)\s*$")
BOUND_LANGUAGES = {"python"}


@dataclass
class Block:
    start: int        # index of the opening fence line
    end: int          # index of the closing fence line
    lang: str
    text: str


def find_blocks(lines: list[str]) -> list[Block]:
    blocks, i = [], 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i].strip())
        if m and lines[i] == lines[i].lstrip():  # top-level fences only; indented ones belong to lists
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == m.group(1):
                    blocks.append(Block(i, j, m.group(2), "\n".join(lines[i + 1:j])))
                    i = j
                    break
        i += 1
    return blocks


def region(sample: Path, name: str) -> tuple[str | None, str | None]:
    """Return (text, error). Text is dedented with blank edges removed."""
    if not sample.is_file():
        return None, f"region: sample file '{sample}' not found"
    lines = sample.read_text(encoding="utf-8").splitlines()
    starts = [i for i, l in enumerate(lines) if l.strip() == f"# [START {name}]"]
    ends = [i for i, l in enumerate(lines) if l.strip() == f"# [END {name}]"]
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        return None, f"region: '{name}' must appear once as # [START {name}] ... # [END {name}] in {sample.name}"
    return textwrap.dedent("\n".join(lines[starts[0] + 1:ends[0]])).strip("\n"), None


def check_file(path: Path, fix: bool) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks = find_blocks(lines)
    by_start = {b.start: b for b in blocks}
    errors, bound, replacements = [], set(), []

    for i, line in enumerate(lines):
        m = MARKER.match(line.strip())
        if not m:
            continue
        kind, ref = m.groups()
        block = by_start.get(i + 1)
        if not block:
            errors.append(f"line {i + 1}: {kind}: the comment must be directly followed by a code block")
            continue
        bound.add(block.start)
        if kind == "output-of":
            if not (path.parent / ref).is_file():
                errors.append(f"line {i + 1}: output: sample file '{ref}' not found")
            continue
        file_ref, _, name = ref.partition("#")
        if not name:
            errors.append(f"line {i + 1}: region: '{ref}' needs a #region name")
            continue
        expected, err = region(path.parent / file_ref, name)
        if err:
            errors.append(f"line {i + 1}: {err}")
        elif block.text != expected:
            if fix:
                replacements.append((block, expected))
            else:
                diff = difflib.unified_diff(expected.splitlines(), block.text.splitlines(),
                                            f"{file_ref}#{name}", "page", lineterm="", n=1)
                shown = "\n".join("           " + d for d in list(diff)[2:12])
                errors.append(f"line {block.start + 2}: drift: block differs from {file_ref}#{name}"
                              f" (run with --fix)\n{shown}")

    for b in blocks:
        if b.lang in BOUND_LANGUAGES and b.start not in bound:
            errors.append(f"line {b.start + 1}: bound: ```{b.lang} block has no snippet comment, so CI never runs it")

    if replacements:
        for block, text in sorted(replacements, key=lambda r: r[0].start, reverse=True):
            lines[block.start + 1:block.end] = text.splitlines()
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus", type=Path, help="folder containing Markdown files")
    ap.add_argument("--fix", action="store_true", help="rewrite drifted blocks from their sample files")
    args = ap.parse_args()

    corpus = args.corpus.resolve()
    files = sorted(corpus.rglob("*.md"))
    failed = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        if "<!-- snippet:" not in text and "<!-- output-of:" not in text and "```python" not in text:
            continue
        errors = check_file(path, args.fix)
        failed += bool(errors)
        print(f"{'FAIL' if errors else 'ok  '} {path.relative_to(corpus.parent).as_posix()}")
        for e in errors:
            print(f"       - {e}")
    print(f"\n{failed} file(s) failing")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
