# P3a-2 batch 8 (round 18) builder notes

Branch `core/p3a2-b8` from `aac26d60`. Code head `6a25ae5d` (two commits: `405a199a` the fix, `6a25ae5d` a test-only rename, see Gates). This notes file and the raw evidence live outside the branch under `handover/evidence/P3a-2/b8/` of the handover checkout. Path: security, no round cap. O8 (`q-p3a2-o8-schema-owner`) stays OFF and OWNER-ONLY: nothing built.

## What was fixed (class, standard, choke point)

Class: an error built INSIDE an `except` block keeps the handled error on `__context__`; `raise ... from None` only sets `__suppress_context__` (hides it from the printed traceback). A log handler that walks `__context__` or `__cause__` records the SDK's or driver's own words (account name, role, host, user). Standard: Python language reference, "The raise statement" (implicit exception chaining; `from None`). Choke points: the four places that turn such an error into a refusal now hold only the class NAME in a variable, leave the `except` block and raise from outside it.

| Group | Fix | Files |
|---|---|---|
| 1 | refusal raised outside the `except` block in `auth_aws.rds_iam` (client step and token step), `migrate._connected_before_commit` (sign-in refusal AND refused-connection refusal), and the sibling `postgres.build` (`StoreUnavailable`, same class, same choke-point idea); `__context__` and `__cause__` both empty | `store/auth_aws.py`, `store/migrate.py`, `store/postgres.py` |
| 2 | both sign-in steps convert any `Exception` (class name only); `KeyboardInterrupt` and `SystemExit` pass | `store/auth_aws.py` |
| 3 | the DSN guard no longer wraps `int()` in a `try`; it checks host, user and port by an allow list (`_plain_port`: digits 0-9 only, 1 to 65535; one host only). Added cases: `port=abc`, port list, 0, 65536, sign, underscore, digits of another script, two hosts | `store/postgres.py` |
| 4 | message names the part ("no host", "no user", "more than one host", "a port that is not one number from 1 to 65535"), ends with a full stop, no Python error name; the close of a half-made connection ignores any `Exception` | `store/postgres.py` |
| 5 | the "no connection is tried" stub is now in the DSN-guard test, the migrate-level tests and the build-path test; CHANGELOG sentence on the runtime build path | tests, `CHANGELOG.md` |
| 6 | this file and `handover/evidence/P3a-2/b8/` | see below |

## Tests, fail-before (measured on a clean detached worktree of aac26d60 with only the changed test files copied in; `PYTHONPATH` on that worktree's src, `fb-import.txt` prints its path)

Denominator: 47 test ids = the 44 ids that are new against `aac26d60` (`ids-new-b8.txt`) + the 3 existing ids whose body I tightened (`ids-failbefore-b8.txt`). Raw: `fail-before-b8-on-aac26d60.txt`. Result: **38 failed, 9 passed** (pytest exit 1; shell exit 123 comes from `xargs`).

The 9 that PASS on aac26d60, one written reason each:
1. `test_a_close_that_fails_with_any_error_does_not_hide_the_first_error[OperationalError]`: control; the old `suppress(psycopg.Error)` already covered the driver's own error; the OSError, BrokenPipeError and RuntimeError cases fail on old.
2. to 4. `test_an_iam_address_with_a_host_a_user_and_a_plain_port_asks_for_the_sign_in[default-port|port-1|port-65535]`: control for the allow list (good addresses worked before); they pin the ends of the range. Killed by V140 only for the range ends of the bad cases; these three guard against over-refusal.
5. to 8. `test_an_interrupt_during_the_sign_in_is_not_turned_into_a_refusal[KeyboardInterrupt|SystemExit x client|token]`: control; old code caught two library types only, so an interrupt always passed. Killed by V138 and V139 (catch widened to `BaseException`).
9. `test_the_ast_scan_finds_a_raise_inside_a_handler_and_ignores_a_bare_raise`: new path; checks the helper that lives in the test file, so the old src cannot change it.

Mutants (all in `tests/migrate_mutants.py`, not `tests/stage_mutants.py`, see Deviations): new V130 to V148 (19), re-pointed V116, V117, V122, V125 (their old text was replaced by the fix); each killed for its named reason by the runner's allow list (a failed `assert`, `AssertionError`, `Failed:` or `ConfigError`, never a crash). First run of the 23: `mut-new.log`, 23 of 23 killed. Final run: four batches, see Gates.

## Group 6: evidence of batch 7, re-measured

(a) the timing test is `tests/test_migration_numbers_perf.py::test_the_timing_harness_flags_a_quadratic_stand_in` (not in `test_migration_numbers.py` as the brief names it); it carries the `perf` marker, so `-m "not live and not perf"` deselects it. Not touched, NOT RUN: its result at this head is unknown.
(b) and (c) I rebuilt the id lists: ids at `140a1268` 12442, at `aac26d60` 12472, new 32, gone 2 (the three full id lists carry fixture names that look like secrets, so only `ids-new-*` and `ids-removed-*` are kept here). Running the 32 new ids of batch 7 (with the aac26d60 test files) on the 140a1268 source: **7 failed, 25 passed** (`b7-new32-on-140a1268.txt`), equal to the runner's count. The builder's earlier "7 failed, 37 passed" used another set: the 32 new ids plus 12 changed ids picked by a name filter (44 ids). So 7 and 25 over 32 ids is the number to quote; 7 and 37 over 44 ids is the builder's. The 25 are: matrix 5, rules 18, verify_pg 2; every one has a line in `handover/evidence/P3a-2/b7/passes-on-old-code.md` (checked one by one: the matrix 4 test names (5 ids), the three wording-check tests (18 ids), the SQLSTATE test (2 ids)).
(d) the builder's "1 failed" in the full suite of batch 7 was the dblink test on the fixed socket (environment, not code); at this head the full suite result is in Gates.
(e) this file is the notes file batch 7 lacked (for batch 7 itself only the evidence folder exists).

## Deviations and open items (stated first, not hidden)

- The brief says mutants go in `tests/stage_mutants.py`; that file holds only the mutants of the stage rename (own runner, own pinned meta-tests). Report group 1 names `tests/migrate_mutants.py`, which is where the earlier sign-in mutants V122 to V125 live, so the new ones are there. `stage_mutants` is still run as a gate.
- `# noqa: BLE001 - <reason>` on the two `except Exception` lines of `auth_aws.py` (the repo already does this in `cli.py`, `tick.py`, `audit_sink.py`; the reviewer asked for `Exception`). That is a lint suppression with a written reason, not a weakened test.
- NOT done, decision needed from the lead: 11 further `raise ... from e` places in `migrate.py` (steps after the connection exists, e.g. lines 1295, 1619-1667) keep the driver error as `__cause__`. One test pins that on purpose (`tests/test_migration_postgres.py:1256` asserts `__cause__` is `LockNotAvailable`). Whether later-step refusals may keep the driver error is a policy question; this round closed the connection and sign-in path only. The CHANGELOG says so.
- IMPOSSIBLE-NOW (not run): PostgreSQL 17 tests (3 skipped by name), Python 3.12, semgrep, zizmor, trivy, pip-audit.

## Gates (all on the final head 6a25ae5d unless a line says otherwise; raw logs next to this file)

| Gate | Result | Exit | Log |
|---|---|---|---|
| gitleaks (origin/main..HEAD) | no leaks found | 0 | final-gitleaks.log (run on 405a199a; the later commit is one test file, re-checked below) |
| ruff check, ruff format --check (src tests demos tools) | passed, 335 files formatted | 0, 0 | final-ruffcheck.log, final-ruffformat.log (run on 405a199a plus the rename; re-run by hand after it: passed) |
| bandit -ll | no finding (two `nosec` warnings of the tool in `tools.py`, not mine) | 0 | final-bandit.log |
| tools/scan_repo.py | clean | 0 | final-scan.log |
| migrate mutants batch 1 | 148 of 148 killed | 0 | final2-batch1.log (final head) |
| migrate mutants batch 2 | 88 of 88 killed | 0 | final2-batch2.log (final head) |
| migrate mutants batch 3 | 98 of 98 killed | 0 | final-batch3.log |
| migrate mutants batch 4 | 97 of 97 killed | 0 | final-batch4.log |
| migration_numbers_mutants | 40 of 40 good (its rows named CRASH are the expected kill reason of that runner and are marked ok) | 0 | final-numbers.log |
| stage_mutants | 37 of 37 good | 0 | final2-stage.log |
| full pytest, first run | 2 failed, 12479 passed, 4 skipped, 29 deselected in 604 s; both failures in `tests/demo_askdata/test_validate_harm.py` | 1 | final-pytest.log |

Slips and corrections I made (stated plainly):
- The first batch of gates ran on 405a199a and `stage_mutants` refused to start because my new tests used the word "stage" as the name of a parameter; the stage-name guard (`test_the_old_stage_word_is_gone`) reads that as a stage label. I renamed it to "step" (test ids unchanged) in 6a25ae5d. Batches 1 and 2 and the stage mutants were re-run on the final head (the `final2-*` logs). Batches 3 and 4, numbers and the first full suite started after the rename and ran on the final tree.
- Batch 2 of the first pass (`final-batch2.log`) started before the rename, so only `final2-batch2.log` is quoted.
- The first full suite had 2 failures in the harm test file: `[dblink-connect]` is the known environment fault (the server connects back to the fixed socket path `/var/run/postgresql`); `[copy-program]` failed with "could not close pipe to external command: Broken pipe", which did NOT fail in the batch 7 run. I did not find the cause. The file run alone inside `unshare -m` with the own server restarted inside it: **253 passed** (`final-harm-unshare.log`). A second full run (same command, whole suite inside `unshare -m`) was started: see "Full suite, second run" below.
- The auto-mode guard refused a command that would have killed my own queued gate jobs; I did not work around it. Lanes A and B therefore ran to the end.
