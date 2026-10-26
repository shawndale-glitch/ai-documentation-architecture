import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_snippets  # noqa: E402

SAMPLE = '''import os

# [START hello]
def hello():
    print("hello")
# [END hello]
'''


def write(tmp_path, page):
    (tmp_path / "hello.py").write_text(SAMPLE)
    doc = tmp_path / "page.md"
    doc.write_text(page)
    return doc


def page(code):
    return f"# Page\n\n<!-- snippet: hello.py#hello -->\n```python\n{code}\n```\n"


def test_matching_block_passes(tmp_path):
    doc = write(tmp_path, page('def hello():\n    print("hello")'))
    assert check_snippets.check_file(doc, fix=False) == []


def test_drifted_block_fails_and_fix_rewrites_it(tmp_path):
    doc = write(tmp_path, page('def hello():\n    print("hi")'))
    errors = check_snippets.check_file(doc, fix=False)
    assert len(errors) == 1 and "drift" in errors[0]
    assert check_snippets.check_file(doc, fix=True) == []
    assert 'print("hello")' in doc.read_text()
    assert check_snippets.check_file(doc, fix=False) == []


def test_unbound_python_block_fails(tmp_path):
    doc = write(tmp_path, "# Page\n\n```python\nprint(1)\n```\n")
    errors = check_snippets.check_file(doc, fix=False)
    assert len(errors) == 1 and "bound" in errors[0]


def test_other_languages_need_no_snippet(tmp_path):
    doc = write(tmp_path, "# Page\n\n```bash\npip install x\n```\n")
    assert check_snippets.check_file(doc, fix=False) == []


def test_missing_region_fails(tmp_path):
    doc = write(tmp_path, "# Page\n\n<!-- snippet: hello.py#nope -->\n```python\nx\n```\n")
    errors = check_snippets.check_file(doc, fix=False)
    assert len(errors) == 1 and "region" in errors[0]


def test_marker_without_block_fails(tmp_path):
    doc = write(tmp_path, "# Page\n\n<!-- snippet: hello.py#hello -->\n\nText.\n")
    errors = check_snippets.check_file(doc, fix=False)
    assert len(errors) == 1 and "directly followed" in errors[0]
