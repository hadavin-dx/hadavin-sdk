# Fail-before: tests/test_strict_flags.py run against the base source of the pull request (0dabf1f)

Command: COLUMNS=300 PYTHONPATH=<base>/src python -m pytest tests/test_strict_flags.py -q -rA --tb=no (test file copied onto the base worktree; no Postgres, no cloud setting)

Result line: `49 failed in 2.73s` (0 passed). Raw list: failbefore-strict-flags-raw.txt.

Counts by outcome:
- FAILED: hadavin_sdk.errors.ConfigError: 1
- FAILED: Failed: 47
- FAILED: AssertionError: 1

Meaning: on the old source every one of the 49 rows fails (a loose value such as "yes", 1, "true" or "on" is accepted by a boolean field, or the structural row lists the loose fields). On the changed source they pass (see the full-suite log).
