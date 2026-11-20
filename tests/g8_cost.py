"""Ticket G8 cost check (section 10 of the ticket): times the seven hostile texts of tests/test_redact_glued_rest.py through
`redact()` and `runmap.redact_text` on the tree it runs in. Not collected by pytest. Run from the repo root of each tree:

    python -m tests.g8_cost run OUT.json        # CPU seconds (`time.thread_time`), best of 3, 65,536 and 262,144 characters
    python -m tests.g8_cost compare BASE.json BUILD.json

`compare` prints both tables side by side and exits 1 when a row breaks the acceptance rule: on the build, for every text and
call, the 262,144-character time is under 3.0 s, at most 6.0 times the 65,536-character time, and at most 1.5 times the
base's time plus 0.05 s.
"""

from __future__ import annotations

import json
import sys
import time

from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact
from tests.test_redact_glued_rest import HOSTILE

CALLS = {
    "redact": lambda t: redact(t),
    "redact_text": lambda t: runmap.redact_text(t, runmap.RunMap()),
}
SIZES = (65_536, 262_144)


def best(call: str, name: str, n: int) -> float:
    text = (HOSTILE[name] * (n // len(HOSTILE[name]) + 1))[:n]
    out = []
    for _ in range(3):
        t0 = time.thread_time()
        CALLS[call](text)
        out.append(time.thread_time() - t0)
    return min(out)


def run(path: str) -> None:
    res = {
        f"{name}|{call}": [best(call, name, n) for n in SIZES]
        for name in sorted(HOSTILE)
        for call in sorted(CALLS)
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    for key, (small, large) in res.items():
        print(f"{key:32} {small:7.3f} {large:7.3f}  x{large / max(small, 1e-3):.2f}")


def compare(base_path: str, build_path: str) -> int:
    with open(base_path, encoding="utf-8") as fh:
        base = json.load(fh)
    with open(build_path, encoding="utf-8") as fh:
        build = json.load(fh)
    bad = 0
    print(
        f"{'text|call':32} {'base 64K':>8} {'base 256K':>9} {'G8 64K':>8} {'G8 256K':>8} {'ratio':>6} {'G8/base':>7}"
    )
    for key in sorted(build):
        (b_small, b_large), (g_small, g_large) = base[key], build[key]
        ratio = g_large / max(g_small, 1e-3)
        ok = g_large < 3.0 and ratio <= 6.0 and g_large <= 1.5 * b_large + 0.05
        bad += not ok
        print(
            f"{key:32} {b_small:8.3f} {b_large:9.3f} {g_small:8.3f} {g_large:8.3f} {ratio:6.2f} "
            f"{g_large / max(b_large, 1e-3):7.2f} {'ok' if ok else 'FAIL'}"
        )
    print(f"{bad} rows break the rule")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(sys.argv[2])
    elif sys.argv[1:2] == ["compare"]:
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    else:
        sys.exit("usage: python -m tests.g8_cost run OUT.json | compare BASE.json BUILD.json")
