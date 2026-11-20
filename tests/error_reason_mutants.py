"""The mutant of `tools.error_reason` (lone surrogate in an exception message), run by ``tools/mutation_runner.py``. Not collected
by pytest. The named test must fail first with the crash class below. Run from the repo root:

    python tests/error_reason_mutants.py
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_error_reason_surrogate.py"
PIN = "tests/test_error_reason_surrogate::"
KILLER = "test_lone_surrogate_message_with_a_handed_out_secret_does_not_raise"

M = [
    Mutant(
        "ER1-no-sanitise",
        "src/hadavin_sdk/tools.py",
        "    message = _sanitise(str(exc))\n    long_enough",
        "    message = str(exc)\n    long_enough",
        "surrogates not allowed",
        allow_crash=True,
        crash_type="UnicodeEncodeError",
        test_file=TEST,
        only_test=KILLER,
        pinned=PIN + KILLER,
    ),
]

if __name__ == "__main__":
    results = run_mutants(
        ROOT,
        M,
        [TEST],
        extra_dirs=("tests", "tools"),
        only=sys.argv[1:],
        on_result=lambda r: print(r, flush=True),
    )
    sys.exit(0 if all(good for *_, good in results) else 1)
