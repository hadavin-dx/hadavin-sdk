"""The scan-loop gate (structural, on the syntax tree): see ``tools/scan_gate.py``. The table lists the shapes that bypass a substring or name check; each must be
reported, and the shipped source tree (recursive, no file exempt) must be clean."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scan_gate", ROOT / "tools" / "scan_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

HEAD = "from . import pipeline, extract, model\nfrom .extract import TransportStreak\n"

BAD = {
    "no streak keyword": HEAD
    + "def scan(s, p, m, sup):\n    streak = TransportStreak()\n    pipeline.process(s, p, m, sup)\n    if streak.stop: pass\n",
    "streak given but never read": HEAD
    + "def scan(s, p, m, sup):\n    streak = TransportStreak()\n    pipeline.process(s, p, m, sup, streak=streak)\n",
    "streak None-ish and unread": HEAD + "def scan(s, p, m, sup):\n    pipeline.process(s, p, m, sup, streak=None)\n",
    "comment is not a streak": "from . import pipeline\n# TransportStreak\ndef scan(s, p, m, sup):\n    pipeline.process(s, p, m, sup)\n",
    "renaming import": "from .pipeline import process as go\ndef scan(s, p, m, sup):\n    go(s, p, m, sup)\n",
    "alias assignment": HEAD + "go = pipeline.process\ndef scan(s, p, m, sup):\n    go(s, p, m, sup)\n",
    "getattr constant": HEAD + "def scan(s, p, m, sup):\n    getattr(pipeline, 'process')(s, p, m, sup)\n",
    "getattr folded string": HEAD + "def scan(s, p, m, sup):\n    getattr(pipeline, 'pro' + 'cess')(s, p, m, sup)\n",
    "functools.partial": HEAD
    + "import functools\ndef scan(s, p, m, sup):\n    f = functools.partial(pipeline.process, s)\n    f(p, m, sup)\n",
    "passed as a callback": HEAD + "def scan(s, p, m, sup, run):\n    run(pipeline.process)\n",
    "bare imported name without streak": "from .pipeline import process\ndef scan(s, p, m, sup):\n    process(s, p, m, sup)\n",
    "bare name passed on": "from .pipeline import process\ndef scan(run):\n    run(process)\n",
    "extract_parsed without streak": HEAD + "def one(p, m, s):\n    return extract.extract_parsed(p, m, s)\n",
    "guard built where nothing watches a streak": HEAD + "def start(s):\n    return model.build_guarded(s)\n",
    "guard class built with no stop read": HEAD
    + "def start(s, b, bud):\n    streak = TransportStreak()\n    return model.GuardedModel(b, bud, s)\n",
    "dotted module path": "import intake.pipeline\ndef scan(s, p, m, sup):\n    intake.pipeline.process(s, p, m, sup)\n",
}

GOOD = {
    "loop with a streak": HEAD
    + "def scan(s, ps, m, sup):\n    streak = TransportStreak()\n    for p in ps:\n        pipeline.process(s, p, m, sup, streak=streak)\n        if streak.stop:\n            break\n",
    "wrapper forwarding its own streak": HEAD
    + "def go(s, p, m, sup, *, streak):\n    return pipeline.process(s, p, m, sup, streak=streak)\n",
    "guard with a streak": HEAD
    + "def start(s):\n    streak = TransportStreak()\n    g = model.build_guarded(s)\n    return g, streak.wall\n",
}


@pytest.mark.parametrize("name", sorted(BAD))
def test_bad_shape_is_reported(name):
    assert gate.violations(BAD[name], "scanner"), name


@pytest.mark.parametrize("name", sorted(GOOD))
def test_good_shape_is_clean(name):
    assert gate.violations(GOOD[name], "scanner") == [], name


def test_the_defining_module_may_use_its_own_names():
    assert gate.violations("def process(s):\n    return extract_parsed(s)\n", "pipeline") == []


def test_the_whole_source_tree_is_clean_with_no_file_exempt():
    bad = {}
    for p in sorted((ROOT / "src").rglob("*.py")):
        v = gate.violations(p.read_text(encoding="utf-8"), p.stem)
        if v:
            bad[str(p.relative_to(ROOT))] = v
    assert bad == {}


def test_the_tree_scan_is_not_vacuous():
    """The real callers exist and are the ones the gate reasons about."""
    cli = (ROOT / "src" / "intake" / "cli.py").read_text(encoding="utf-8")
    pipe = (ROOT / "src" / "intake" / "pipeline.py").read_text(encoding="utf-8")
    assert "extract_parsed(" in cli and "build_guarded(" in cli and "extract_parsed(" in pipe
    assert gate.violations(cli.replace(", streak=streak", ""), "cli") != []
    assert gate.violations(pipe.replace(", streak=streak", ""), "pipeline") != []
