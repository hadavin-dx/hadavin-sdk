"""Pure anchor check of the mutant list: no mutant and no script is run, the list is only imported.

Every mutant's ``old`` text must occur exactly once in its source file; a stale anchor makes the script exit 2
before the first mutant.
"""

from pathlib import Path

import pytest

from tests import endpoint_mutants as em

ROOT = Path(__file__).resolve().parents[1]

# G33d: its anchor (`now - last_warned`, endpoints_mutants line ~1255) is stale since a rename in worker.py
# (`at - last_warned`); fixing that line is pending the owner. strict: the day it is fixed this xpasses and fails.
PENDING = {"G33d"}


def _case(m):
    marks = []
    if m.name.split()[0] in PENDING:
        marks.append(
            pytest.mark.xfail(
                strict=True, reason="G33d anchor line 1255 pending the owner: now -> at"
            )
        )
    return pytest.param(m, id=m.name.split()[0], marks=marks)


@pytest.mark.parametrize("m", [_case(m) for m in em.M])
def test_every_mutant_anchor_occurs_exactly_once(m):
    text = (ROOT / m.file).read_text(encoding="utf-8")
    assert text.count(m.old) == 1, (m.name, m.file, text.count(m.old))


def test_mutant_ids_are_unique():
    ids = [m.name.split()[0] for m in em.M]
    assert len(ids) == len(set(ids))
