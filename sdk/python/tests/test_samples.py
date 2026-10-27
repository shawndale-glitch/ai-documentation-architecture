"""Run every sample against a fresh mock, and compare with the docs.

A sample's output shown in a topic (under an `<!-- output-of: ... -->`
comment) must be exactly what the sample prints, so readers can trust that
what they see on the page is what they'll get.
"""
import os
import re
import subprocess
import sys

import pytest

from conftest import REPO

SAMPLES = sorted((REPO / "sdk" / "samples" / "python").glob("*.py"))
DOCS = sorted((REPO / "examples").glob("*.md"))
OUTPUT_OF = re.compile(r"<!--\s*output-of:\s*(\S+?)\s*-->\s*\n```\w*\n(.*?)\n```", re.S)


def documented_outputs():
    for doc in DOCS:
        for ref, text in OUTPUT_OF.findall(doc.read_text(encoding="utf-8")):
            yield pytest.param((doc.parent / ref).resolve(), text, id=f"{doc.name}:{ref.rsplit('/', 1)[-1]}")


def run(sample):
    return subprocess.run([sys.executable, str(sample)], capture_output=True, text=True,
                          env=dict(os.environ), timeout=30)


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda p: p.name)
def test_sample_runs(api, sample):
    result = run(sample)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("sample,expected", list(documented_outputs()))
def test_documented_output_matches(api, sample, expected):
    result = run(sample)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected.strip()


def test_every_sample_is_shown_in_the_docs():
    shown = "\n".join(d.read_text(encoding="utf-8") for d in DOCS)
    unused = [s.name for s in SAMPLES if f"/{s.name}#" not in shown]
    assert not unused, f"samples no topic uses: {unused}"


def test_setup_check_passes(api):
    result = subprocess.run([sys.executable, "-m", "waypoint.check"], capture_output=True, text=True,
                            env=dict(os.environ), timeout=30)
    assert result.returncode == 0, result.stdout
    assert "Connected to Waypoint API 1.8.0" in result.stdout
    assert "wp_test_pytest_key" not in result.stdout  # never prints the whole key
