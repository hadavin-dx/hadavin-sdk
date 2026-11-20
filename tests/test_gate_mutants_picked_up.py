"""Makes ``tests/gate_mutants.py`` (not a pytest file) part of the batch (review-code-F-gate-3 m-6, ORDER 020).

Always: a cheap check (the list imports, every search text is in its file exactly once, the count is >= MIN_MUTANTS (the real count), every mutant names its
killer and an `expect` fragment). The full mutant run is slow: it is behind HADAVIN_RUN_MUTANTS=1 (the repo has no marker for slow
evidence tests: CI deselects only `live` and `perf`; the mutants of the stages run in their own CI step).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

from tests import gate_mutants

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIN_MUTANTS = 105


def test_the_gate_mutant_list_imports_and_is_not_shrunk():
    assert len(gate_mutants.M) >= MIN_MUTANTS, (
        f"only {len(gate_mutants.M)} gate mutants (was {MIN_MUTANTS}): do not delete mutants"
    )
    names = [m.name for m in gate_mutants.M]
    assert len(set(names)) == len(names), "duplicate mutant names"


def test_every_mutant_search_text_is_in_its_file_exactly_once():
    bad = []
    for m in gate_mutants.M:
        found = (gate_mutants.ROOT / m.file).read_text(encoding="utf-8").count(m.old)
        if found != 1:
            bad.append((m.name, m.file, found))
    assert not bad, f"search text not found exactly once (name, file, count): {bad}"


def test_every_mutant_has_an_expect_fragment_and_a_pinned_killer():
    runner_min = 4  # tools.mutation_runner: expect is >= 4 characters
    bad = [m.name for m in gate_mutants.M if len(m.expect.strip()) < runner_min or not m.expect]
    assert not bad, f"mutants without an `expect` fragment: {bad}"
    no_killer = [
        m.name for m in gate_mutants.M if not m.only_test or not m.pinned or not m.test_file
    ]
    assert not no_killer, f"mutants without a named killer test: {no_killer}"
    for m in gate_mutants.M:
        assert (ROOT / m.test_file).is_file(), f"{m.name}: killer file {m.test_file} is missing"
        assert m.only_test in (ROOT / m.test_file).read_text(encoding="utf-8"), (
            f"{m.name}: killer {m.only_test} is not in {m.test_file}"
        )


@pytest.mark.skipif(
    os.environ.get("HADAVIN_RUN_MUTANTS") != "1",
    reason="the full gate mutant run is slow: set HADAVIN_RUN_MUTANTS=1 to run it (python tests/gate_mutants.py)",
)
def test_the_full_gate_mutant_run_kills_every_mutant():
    done = subprocess.run(
        [sys.executable, "tests/gate_mutants.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=3 * 3600,
        check=False,
    )
    lines = [ln for ln in done.stdout.splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    n = len(gate_mutants.M)
    assert last == f"{n} of {n} good; problems: []", (
        f"last line {last!r}; stderr tail {done.stderr[-500:]!r}; BAD rows: {[ln for ln in lines if ln.startswith('BAD')]}"
    )
    assert done.returncode == 0
