"""Per-test fail-before / pass-after proof.

Usage: python mutation/prefix_proof.py <old-tree-demo-dir> --old-python <python of a venv installed from the old tree> [--out FILE]

<old-tree-demo-dir> is the `demos/dealdesk` folder of a checkout of the OLD source (for example `git worktree add --detach X 1479888`). This script copies
the CURRENT `tests/test_review1_behaviour.py` into that old tree, then runs EVERY test of that file one by one, in its own pytest process with a hard
timeout, against the old source and against the current source, and prints one line per test:

    <test id> | old: FAILED/PASSED/TIMEOUT/ERROR | new: PASSED/...

A test that hangs the old code (an unbounded regex holds the GIL) is reported as TIMEOUT, which counts as failing before. The failure CLASS is recorded: only
AssertionError / Failed / TIMEOUT count as a behaviour proof; AttributeError, ImportError, TypeError and the like mean the old source lacks the API, which proves nothing and is flagged. Raw output goes to --out when given.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TEST = "tests/test_review1_behaviour.py"
TIMEOUT_S = 150


def run(tree: Path, node: str | None, py: str, collect: bool = False) -> tuple[str, str]:
    """Returns (status, detail). status is PASSED, FAILED:<class>, TIMEOUT or ERROR; <class> is the exception class of the first failure line
    (AssertionError and Failed are BEHAVIOUR failures; AttributeError, ImportError, TypeError, NameError mean the old source lacks an API: NOT a proof)."""
    args = [py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=short", "--maxfail=1"]
    args += ["--collect-only", TEST] if collect else [node or TEST]
    try:
        r = subprocess.run(args, cwd=tree, capture_output=True, text=True, timeout=TIMEOUT_S, check=False)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", f"no result in {TIMEOUT_S} s"
    out = (r.stdout + r.stderr).strip()
    if collect:
        return ("OK" if r.returncode == 0 else "ERROR"), out
    if " passed" in out and r.returncode == 0:
        return "PASSED", out.splitlines()[-1]
    if r.returncode == 1 and " failed" in out:
        found = []
        for ln in out.splitlines():
            if ln.startswith("E "):
                body = ln[1:].strip()
                found.append((body.split(":")[0].split(" ")[0], body[:100]))
        for (
            cls,
            body,
        ) in found:  # chained exceptions: the first BEHAVIOUR class wins (an assert, a pytest.fail, or the old pattern hanging a child process)
            if cls in BEHAVIOUR_CLASSES:
                return "FAILED:" + (
                    "AssertionError" if cls == "assert" else "Failed" if cls == "subprocess.TimeoutExpired" else cls
                ), body
        if found:
            return f"FAILED:{found[0][0]}", found[0][1]
        return "FAILED:unknown", out.splitlines()[-1][:100]
    return "ERROR", out[-160:]


BEHAVIOUR = ("FAILED:AssertionError", "FAILED:Failed", "TIMEOUT")
BEHAVIOUR_CLASSES = ("AssertionError", "assert", "Failed", "subprocess.TimeoutExpired")


def main(argv: list[str]) -> int:
    old = Path(argv[1]).resolve()
    old_py = (
        argv[argv.index("--old-python") + 1] if "--old-python" in argv else sys.executable
    )  # the interpreter whose venv imports the OLD source
    out_file = Path(argv[argv.index("--out") + 1]) if "--out" in argv else None
    shutil.copy2(HERE / TEST, old / TEST)
    _status, listing = run(HERE, None, sys.executable, collect=True)
    ids = [ln for ln in listing.splitlines() if "::" in ln]
    lines = []
    bad = 0
    for node in ids:
        o, o_msg = run(old, node, old_py)
        n, _ = run(HERE, node, sys.executable)
        flag = "" if o in BEHAVIOUR and n == "PASSED" else "   <-- NOT a behaviour proof"
        bad += bool(flag)
        lines.append(f"{node} | old: {o} ({o_msg[:80]}) | new: {n}{flag}")
        print(lines[-1], flush=True)
    lines.append(
        f"summary: {len(ids)} tests, {bad} not a behaviour proof (the old source must FAIL by assertion or hang, the current source must pass)"
    )
    print(lines[-1])
    if out_file:
        out_file.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
