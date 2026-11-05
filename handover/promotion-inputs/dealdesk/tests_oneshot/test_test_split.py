"""One-shot checks of the held-out split (data/test.jsonl): TUNED, NOT SEALED. Not part of the default run (pyproject testpaths = tests).

    uv run --group test pytest tests_oneshot --confirm-one-shot

The first run writes eval/test_split_run.json; a second run is refused unless --allow-rerun is given (and the rerun is then recorded). The seed and the
generator are public in this repo and the builder could read the file, so no number from it may be called held-out or blind. A second-author blind set
(see eval-contract.md) is the prerequisite for ANY rated claim."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "demo_only" / "data")]
import caserun

DATA = ROOT / "demo_only" / "data"


def _rows(name):
    return [json.loads(x) for x in (DATA / name).read_text(encoding="utf-8").splitlines()]


def test_file_matches_its_own_manifest():
    man = json.loads((DATA / "test_manifest.json").read_text(encoding="utf-8"))["sha256"]
    assert hashlib.sha256((DATA / "test.jsonl").read_bytes()).hexdigest() == man["demo_only/data/test.jsonl"]


def test_implementation_agrees_with_the_test_split_labels():
    assert caserun.run_rows(_rows("test.jsonl")) == []


def test_test_split_is_a_redraw_not_a_copy_of_dev_and_has_the_same_shape():
    dev, test = _rows("dev_cases.jsonl"), _rows("test.jsonl")
    key = lambda r: json.dumps(r.get("input") or r["params"], sort_keys=True)
    dec = {key(r) for r in dev if r["kind"] == "decide"} & {key(r) for r in test if r["kind"] == "decide"}
    assert not dec  # random deals, terms and pools must not repeat
    tr = {key(r) for r in dev if r["kind"] == "trace"} & {key(r) for r in test if r["kind"] == "trace"}
    assert len(tr) <= 3  # the quoted-history template has only nine figures, so a couple of chance repeats are expected
    for kind in ("decide", "accept", "trace", "scenario"):
        assert sum(r["kind"] == kind for r in dev) == sum(r["kind"] == kind for r in test)
    assert {r["scenario"] for r in test if r["kind"] == "scenario"} == {r["scenario"] for r in dev if r["kind"] == "scenario"}
