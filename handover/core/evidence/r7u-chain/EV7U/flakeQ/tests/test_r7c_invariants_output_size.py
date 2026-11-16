"""Round 7C, O-3: the size of what `check_invariants` prints does not grow with the log. A log of 100,000 short rows
printed 168 lines where 161 were expected. The 7 extra lines are the line `first 10 of N: ...` that the table prints
under EACH failing check (7 checks, 7 lines): they were left out of the expected number. The exact counts are pinned."""

from __future__ import annotations

import json
from pathlib import Path

from test_load_tools import T0, make_world, run_world

from load_tools import check_invariants as ci

TABLE_LINES_ALL_HOLD = 2 + 7 * 2 + 1  # two header lines, two lines per check, the closing line
JSON_LINES_ALL_HOLD_AND_EMPTY = 68  # seven checks, no values, no offenders, indent 2 (see the test below)


def _synthetic(offenders: int, ok: bool) -> dict[str, object]:
    return {
        "ok": ok,
        "checks": [ci._result(n, ok, "d", [f"o{i:06d}" for i in range(offenders)], {}) for n in range(1, 8)],
    }


def _dump(result: dict[str, object]) -> list[str]:
    return json.dumps(result, indent=2, sort_keys=True).split("\n")


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# one table line per offender.
def test_each_failing_check_adds_exactly_one_line_to_the_table() -> None:
    assert len(ci.render_table(_synthetic(0, True)).split("\n")) == TABLE_LINES_ALL_HOLD
    for failing_offenders in (1, ci.FIRST_N, ci.FIRST_N + 1, 100_000):
        lines = ci.render_table(_synthetic(failing_offenders, False)).split("\n")
        assert len(lines) == TABLE_LINES_ALL_HOLD + 7, failing_offenders  # one `first N of M` line per check
        assert sum(1 for line in lines if line.lstrip().startswith("first ")) == 7


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# one table line per offender.
def test_the_printed_size_is_the_same_for_a_hundred_thousand_offenders_as_for_eleven() -> None:
    small, big = _synthetic(ci.FIRST_N + 1, False), _synthetic(100_000, False)
    assert len(_dump(small)) == len(_dump(big)) == 145
    assert len(_dump(_synthetic(0, True))) == JSON_LINES_ALL_HOLD_AND_EMPTY


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# one table line per offender.
def test_a_real_run_over_a_hundred_thousand_short_rows_prints_a_fixed_number_of_lines(tmp_path: Path) -> None:
    w = make_world()
    clean = run_world(tmp_path, make_world())
    w["reqs"] += [
        {"request_id": f"x{i}", "door": "form", "intended_ts": T0, "final_status": 503}
        for i in range(100_000 - len(w["reqs"]))
    ]
    result = run_world(tmp_path, w)
    assert result["checks"][0]["offender_count"] > 99_000 and len(result["checks"][0]["offenders"]) == ci.FIRST_N
    clean_table = len(ci.render_table(clean).split("\n"))
    table = ci.render_table(result).split("\n")
    failing = sum(1 for c in result["checks"] if c["offender_count"])
    assert len(table) == clean_table + failing  # one `first N of M` line for each failing check, nothing else
    assert (len(table), len(json.dumps(result, indent=2, sort_keys=True).split("\n"))) == (18, 150)  # measured
