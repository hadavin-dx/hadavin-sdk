"""Judge one mutation-test run by the REASON for the kill, not only the exit code.

A mutant that makes some unrelated test fail is not evidence the intended test works. ``judge`` labels a
run from pytest's exit code and ``"<failing test id> | <first assertion line>"``: SURVIVED, NO TESTS RAN,
KILLED-WRONG-REASON (an expected fragment is missing), KILLED-OTHER-TEST (not the test pinned in a reviewed
baseline), KILLED-CRASH (the assertion line is an exception, or an executor's internal-error denial was the
RESULT) or KILLED. Stdlib only."""

from __future__ import annotations

import re

CRASH = re.compile(
    r"\|\s*E\s+(\w+\.)*(KeyError|StopIteration|IndexError|TypeError|AttributeError|ValueError"
    r"|ZeroDivisionError|UnboundLocalError|SyntaxError|ImportError|NameError)"
)
INTERNAL = re.compile(r"assert \(*['\"](?:denied:)?internal_error['\"] ==")


def judge(rc: int, why: str, expect: str | None = None, pinned: str | None = None) -> str:
    if rc != 1:
        return {0: "SURVIVED", 5: "NO TESTS RAN"}.get(rc, f"rc={rc}")
    if expect and expect not in why:
        return "KILLED-WRONG-REASON"
    test_id, _, first = why.partition(" | ")
    if pinned is not None and pinned != test_id:
        return "KILLED-OTHER-TEST"
    return "KILLED-CRASH" if CRASH.search("| " + first) or INTERNAL.search(first) else "KILLED"
