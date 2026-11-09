# PR89 review-fix builder report (ORDER 194 B), saved by the cloud session 09:45Z
Head 6706e67 on core/mutation-runner-keywords (on top of 59f62a3). NOT marked READY.

CHECKED BY ME (builder output, unverified by an independent run):
- ruff check and ruff format --check clean (322 files); 147 affected tests passed.
- One full pytest via heavy.sh, `env -u HADAVIN_TEST_PG_DSN`: 10104 passed, 455 skipped, exit=0.
- Fail-on-old-code proof: 13 failed, 32 passed (2 pass on old code by design).
- Nine fixes: JUNIT MISSING error row under forbid_skips; always-on FIXTURE ERROR row (fixture_errors()); judge returns ERROR for rc 1 with empty test id; [REDACTED] masking of pass_env values and URL passwords; conftest path "not a file of the tree" ValueError before any temp folder; _plugin_module needs ASCII and refuses keywords; **extra dicts and two type: ignore removed; docstring and CHANGELOG. New hashes: tools fd46eee7…0283, mutation.py c29245e2…8aa5.
NOT RUN: Postgres, py3.12, mutation scripts, EGM steps, GitHub checks, Linux mutants (ORDER 196).
OPEN: always-on FIXTURE ERROR changes default behaviour (demos copying the runner must re-copy both files and re-pin). One timing test flaked under load (passed alone and on rerun).
