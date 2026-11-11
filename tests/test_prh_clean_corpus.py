"""PR H, T6: text that holds only ordinary hidden items (tables with tabs, colour codes, joiners, line continuations,
overstrike) comes out as the reader sees it, with no new placeholder and every ignorable character still there.

The inputs are `tests/record_prh_main.py` CORPUS; the number of placeholders main wrote for each is in
`tests/fixtures/prh_main_corpus.json` (recorded from main). Every test whose name starts `test_mf_` must FAIL on main;
the others must pass on main (they guard what main already did)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
from tests import hidden_oracle as oracle
from tests import record_prh_main as rec

MAIN_COUNTS = json.loads(
    (Path(__file__).parent / "fixtures" / "prh_main_corpus.json").read_text(encoding="utf-8")
)
NAMES = sorted(rec.CORPUS)
# items that reach the person only as a space or nothing; the corpus items below hold only these
CONTROL_FREE = {"hindi", "json", "log_lines", "persian_zwnj", "emoji_joiners"}


def _placeholders(text: str) -> int:
    return sum(1 for _ in runmap.PLACEHOLDER.finditer(text))


def test_every_corpus_item_has_a_recorded_count():
    assert sorted(MAIN_COUNTS) == NAMES


@pytest.mark.parametrize("name", NAMES)
def test_no_more_placeholders_than_main(name):
    out = runmap.redact_untrusted(rec.CORPUS[name], {})
    assert _placeholders(out) <= MAIN_COUNTS[name], (name, out)


# main leaves the C1 character and the backspaces of the overstrike in the output: these two must fail on main
MAIN_DIFFERS = {"cp1252_c1", "nroff_overstrike"}


@pytest.mark.parametrize(
    "name", [pytest.param(n, id=("mf_" + n if n in MAIN_DIFFERS else n)) for n in NAMES]
)
def test_output_is_the_spaced_reading(name):
    """With the ignorable characters left in place (they are not removed by the choke point), the output is the
    oracle's spaced reading and nothing else."""
    text = rec.CORPUS[name]
    out = runmap.redact_untrusted(text, {})
    assert out == oracle.readings(text)[1], (name, out)


@pytest.mark.parametrize("name", NAMES)
def test_every_ignorable_character_is_still_present(name):
    text = rec.CORPUS[name]
    ign = oracle.derive_ignorable()
    kept = [c for c in text if ord(c) in ign]
    out = runmap.redact_untrusted(text, {})
    for c in set(kept):
        assert out.count(c) == text.count(c), (name, hex(ord(c)))


@pytest.mark.parametrize("name", NAMES)
def test_tool_path_gives_the_same_text(name):
    text = rec.CORPUS[name]
    assert tools.prepare_output(text, {}, 4000, []) == runmap.redact_untrusted(text, {})


def test_a_tab_table_keeps_its_tabs():
    out = runmap.redact_untrusted(rec.CORPUS["kubectl_tab_table"], {})
    assert out == rec.CORPUS["kubectl_tab_table"]


def test_coloured_output_loses_only_the_colour_codes():
    out = runmap.redact_untrusted(rec.CORPUS["coloured_test_output"], {})
    assert out == "PASSED tests/test_a.py::test_one\nFAILED tests/test_a.py::test_two\n"
