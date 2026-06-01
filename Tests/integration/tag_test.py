"""
apfel Integration Tests - `apfel tag` subcommand (content-tagging model, #170)

Exercises the release binary end-to-end:
- plain + JSON output formats
- JSON structure (object with a non-empty "tags" array of strings)
- empty / whitespace stdin handling and exit codes
- --permissive path
- a broad parametrized sweep of varied real-world inputs

Model-dependent: requires Apple Intelligence. Skipped (loudly, per the suite's
convention) only if the model is unavailable on this host.

Run: python3 -m pytest Tests/integration/tag_test.py -v
"""

import functools
import json
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
BINARY = ROOT / ".build" / "release" / "apfel"
TIMEOUT = 60


def run_tag(text, extra_args=None, timeout=TIMEOUT):
    """Pipe `text` into `apfel tag [extra_args]`; return CompletedProcess."""
    args = [str(BINARY), "tag"] + (extra_args or [])
    return subprocess.run(
        args, input=text, text=True, capture_output=True, timeout=timeout
    )


@functools.lru_cache(maxsize=1)
def model_available():
    r = subprocess.run([str(BINARY), "--model-info"], capture_output=True, text=True, timeout=20)
    return r.returncode == 0 and "available:  yes" in r.stdout.lower()


pytestmark = pytest.mark.skipif(
    not BINARY.exists() or not model_available(),
    reason="apfel release binary or Apple Intelligence not available",
)


# A broad set of clearly-benign, distinct inputs. --permissive is used in the
# sweep so an occasional guardrail false-positive does not make the suite flaky.
SWEEP_INPUTS = [
    "The headphones sound amazing and the battery lasts all day.",
    "Mix flour, eggs, and sugar, then bake at 180C for 25 minutes.",
    "Kubernetes pods keep crashing with OOMKilled under sustained load.",
    "Our Q3 revenue grew twelve percent driven by enterprise subscriptions.",
    "A hiking trip through the Alps with stunning views and great weather.",
    "The central bank raised interest rates by half a percent today.",
    "She practiced the violin for two hours before the evening concert.",
    "Install the dependencies, run the migrations, then start the dev server.",
    "The soup needs more salt and a squeeze of fresh lemon juice.",
    "Quarterly sales report shows strong growth in the European market.",
]


# ---------------------------------------------------------------------------
# Plain output
# ---------------------------------------------------------------------------

def test_tag_plain_returns_tags():
    p = run_tag("The new espresso machine pulls a great shot every morning.", ["--permissive"])
    assert p.returncode == 0, f"stderr={p.stderr!r}"
    out = p.stdout.strip()
    assert out, "expected non-empty tag output"
    # plain output is whitespace-separated short tags on (essentially) one logical line
    tags = out.split()
    assert len(tags) >= 1


def test_tag_plain_is_not_json():
    p = run_tag("A documentary about deep-sea creatures and bioluminescence.", ["--permissive"])
    assert p.returncode == 0
    assert not p.stdout.strip().startswith("{"), "plain output must not be JSON"


# ---------------------------------------------------------------------------
# JSON output (-o json and --output json)
# ---------------------------------------------------------------------------

def test_tag_json_structure():
    p = run_tag("Kubernetes pods keep crashing under sustained load.", ["-o", "json", "--permissive"])
    assert p.returncode == 0, f"stderr={p.stderr!r}"
    payload = json.loads(p.stdout)
    assert isinstance(payload, dict) and "tags" in payload
    assert isinstance(payload["tags"], list) and len(payload["tags"]) >= 1
    assert all(isinstance(t, str) and t for t in payload["tags"]), "all tags must be non-empty strings"


def test_tag_output_long_flag_equivalent():
    p = run_tag("Our Q3 revenue grew driven by enterprise subscriptions.", ["--output", "json", "--permissive"])
    assert p.returncode == 0, f"stderr={p.stderr!r}"
    payload = json.loads(p.stdout)
    assert "tags" in payload and isinstance(payload["tags"], list)


def test_tag_json_no_duplicate_tags():
    p = run_tag("A hiking trip through the Alps with stunning mountain views.", ["-o", "json", "--permissive"])
    assert p.returncode == 0
    tags = json.loads(p.stdout)["tags"]
    assert len(tags) == len(set(t.lower() for t in tags)), f"tags should be de-duplicated: {tags}"


# ---------------------------------------------------------------------------
# Input handling / exit codes
# ---------------------------------------------------------------------------

def test_tag_empty_stdin_exits_2():
    p = run_tag("")
    assert p.returncode == 2, f"expected rc=2 for empty stdin, got {p.returncode}"
    assert "no input" in p.stderr.lower()


def test_tag_whitespace_only_stdin_exits_2():
    p = run_tag("   \n\t  \n")
    assert p.returncode == 2, f"whitespace-only stdin should be treated as no input, got rc={p.returncode}"


def test_tag_long_input_handled():
    big = "The annual engineering conference covered databases, networking, and security. " * 40
    p = run_tag(big, ["-o", "json", "--permissive"])
    assert p.returncode == 0, f"stderr={p.stderr!r}"
    assert "tags" in json.loads(p.stdout)


# ---------------------------------------------------------------------------
# --permissive
# ---------------------------------------------------------------------------

def test_tag_permissive_succeeds():
    p = run_tag("This local-first CLI tool is fast and private.", ["--permissive"])
    assert p.returncode == 0, f"stderr={p.stderr!r}"
    assert p.stdout.strip()


# ---------------------------------------------------------------------------
# Massive sweep across varied inputs (plain + json)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", SWEEP_INPUTS)
def test_tag_sweep_plain(text):
    p = run_tag(text, ["--permissive"])
    assert p.returncode == 0, f"input={text!r} stderr={p.stderr!r}"
    assert p.stdout.strip(), f"no tags for input={text!r}"


@pytest.mark.parametrize("text", SWEEP_INPUTS)
def test_tag_sweep_json(text):
    p = run_tag(text, ["-o", "json", "--permissive"])
    assert p.returncode == 0, f"input={text!r} stderr={p.stderr!r}"
    payload = json.loads(p.stdout)
    assert isinstance(payload.get("tags"), list) and len(payload["tags"]) >= 1, f"no tags for input={text!r}"
    assert all(isinstance(t, str) and t.strip() for t in payload["tags"])
