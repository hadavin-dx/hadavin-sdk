"""Mutants of A10 (audit/chain.py): flip the classifier, drop the LIMIT, drop the quarantine, drop the backoff cap.
Each is applied to src in place, tests/test_mutants_audit_drain_a10.py must FAIL, the file is restored byte for byte.
Run from the repo root (refuses a dirty chain.py):  uv run --all-extras --group test python tests/audit_drain_a10_mutants.py
Exit 1 if a mutant survives."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/hadavin_sdk/audit/chain.py"
MUTANTS = {
    "M1 flip classifier": (
        "return state.startswith(defaults.AUDIT_PERMANENT_SQLSTATES)",
        "return not state.startswith(defaults.AUDIT_PERMANENT_SQLSTATES)",
    ),
    "M2 drop LIMIT": (
        '(defaults.AUDIT_QUARANTINE_PREFIX + "%", want, seen)',
        '(defaults.AUDIT_QUARANTINE_PREFIX + "%", 10**9, seen)',
    ),
    "M3 drop quarantine": ("r.marked += self._quarantine(event, row_id)", "pass"),
    "M4 drop backoff cap": (
        "self._sleep(min(delay, defaults.AUDIT_FLUSH_BACKOFF_MAX_S))",
        "self._sleep(delay)",
    ),
}


def main() -> int:
    original = SRC.read_text(encoding="utf-8")
    bad = 0
    try:
        for name, (old, new) in MUTANTS.items():
            if original.count(old) != 1:
                print(f"{name}: pattern not found exactly once")
                bad += 1
                continue
            SRC.write_text(original.replace(old, new), encoding="utf-8")
            run = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-x",
                    "-p",
                    "no:cacheprovider",
                    "tests/test_mutants_audit_drain_a10.py",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            killed = run.returncode == 1
            print(f"{name}: {'KILLED' if killed else 'SURVIVED'}")
            bad += not killed
    finally:
        SRC.write_text(original, encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
