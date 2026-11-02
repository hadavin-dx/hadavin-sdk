"""Fixes for review 4 of PR #42: the truncation marker stays inside the redactor's cap, every timing test carries the perf
marker, the CHANGELOG merge order names the four PRs, and a replacement between two secrets forces a fresh decoded view."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod

ROOT = Path(__file__).resolve().parents[1]
CAP = defaults.MAX_REDACT_CHARS

# --- Minor 1: the [truncated] marker is part of what the redactor reads ------------------------------------------------------------------


def test_a_large_output_cut_at_the_window_is_not_refused_for_its_marker():
    """Whitespace on the very last byte of the cut used to keep every character and add the marker: cap + 12."""
    text = "x" * (CAP - 1) + " yy"
    out = tools_mod.prepare_output(text, {}, 200_000)
    assert out  # no InputTooLarge


def test_a_spaced_300k_output_with_a_200k_cap_is_not_refused():
    out = tools_mod.prepare_output("word " * 60_000, {}, 200_000)
    assert out.startswith("word word")


@pytest.mark.parametrize("n", [CAP - 12 - 1, CAP - 12, CAP - 11, CAP])
def test_lengths_around_the_window_are_all_accepted(n):
    assert tools_mod.prepare_output("x" * (n - 1) + " ", {}, 200_000)


def test_the_window_plus_the_marker_is_never_over_the_cap():
    assert len(tools_mod._cut("x" * (3 * CAP), CAP - len(tools_mod.TRUNCATED))) <= CAP


# --- Minor 2: structural checks on the tests and the checklist -------------------------------------------------------------------------


def test_every_test_in_the_perf_file_carries_the_perf_marker():
    tree = ast.parse((ROOT / "tests" / "test_k5_perf.py").read_text(encoding="utf-8"))
    tests = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert len(tests) >= 4, "the scan would check nothing"
    unmarked = [
        n.name for n in tests if not any("mark.perf" in ast.unparse(d) for d in n.decorator_list)
    ]
    assert not unmarked, unmarked


def test_the_changelog_merge_order_names_the_four_prs():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if (
        "K5-core, merge conditions" not in text
    ):  # the block is deleted in the rename commit, by design
        return
    line = next(ln for ln in text.splitlines() if ln.strip().startswith("1. **Order:"))
    # the ORDER itself, not just the mentions (a later sentence of the line also says "#49 keeps ..."): the bold
    # heading names the three merges in sequence, and #48 is said to go in first as well
    order = re.match(r"\d+\. \*\*Order: (.*?)\*\*", line.strip())
    assert order, line
    assert re.findall(r"#\d+", order.group(1)) == ["#49", "#42", "#41"], order.group(1)
    assert "**#48 goes in first as well" in line, line


# --- Nit 1: a replacement between two secrets must not leave a stale decoded view -----------------------------------------------------------


def test_a_replacement_between_two_secrets_forces_a_fresh_decoded_view():
    absent = (
        "Mn7Bv+" + "ef56=Hj-none"
    )  # never in the text: its forms make the first decoded view, before any replacement
    s1 = "Zx9Qw+" + "ab12=Pq-one"  # fakes, built from parts
    s2 = "Rt5Yu+" + "cd34=Lm-two"
    hidden2 = "".join(f"%{b:02X}" for b in s2.encode())
    out = tools_mod.prepare_output(f"a {s1} b {hidden2} c", {}, 16_384, [absent, s1, s2])
    assert s1 not in out and s2 not in out
