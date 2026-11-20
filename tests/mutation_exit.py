"""Exit-code helpers of ``tests/endpoint_mutants.py`` (kept apart so they can be tested without running the mutant list)."""

import sys
import traceback
from collections.abc import Callable, Iterable, Sequence


def check_test_files(mutants: Iterable, tests: Sequence[str]) -> list[str]:
    """A mutant whose killer file is not in ``tests`` makes the runner raise ``ValueError`` before any mutant runs.
    Returns one message per such mutant, naming the mutant and the file."""
    return [
        f"ERROR mutant {m.name!r}: killer test file {m.test_file!r} is missing from TESTS"
        for m in mutants
        if m.test_file and m.test_file not in tests
    ]


def exit_guard(main: Callable[[], object]) -> int:
    """Run ``main``; return its exit code, and never 0 after an exception (traceback to stderr, 1; Ctrl-C gives 130).
    ``SystemExit`` keeps its own code (``sys.exit(None)`` is 0)."""
    try:
        main()
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        print(code, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    except BaseException:
        traceback.print_exc()
        return 1
    return 0
