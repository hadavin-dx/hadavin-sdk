# EVIDENCE RUNNER results, PD banner round 13, head 63996217d8c2e0f5c21218ac0ce7ca58e20081d4
Records only; no judging. Raw logs: raw/ (this folder). Worktree of exactly 63996217 on both venvs; PYTHONPATH=<worktree>/src; hadavin_sdk.__file__ printed = worktree src each time.
Python 3.13.18 = $PY (/home/user/build/wt/q8c1-b17fix/.venv); Python 3.12.3 = /home/user/build/sonarpath-venv312. Both have pytest; neither has hypothesis (not needed by the files run). bandit = /root/.local/bin/bandit 1.9.4; ruff 0.17.1.

## FAILURES / SURPRISES (first)
1. `ruff check src tests demos tools` (the CI command, ci.yml:80) FAILS: 1 error, S603 `subprocess` call, tools/fixed_run.py:30:12 (`return subprocess.run([exe, *argv[1:]], check=check, **kwargs)`). No noqa on it. `ruff format --check` passes (331 files). raw/ruff-check2.log
2. Mutant rows: 20 of 22 named rows good. BAD: R13B2 "a bare word bypass is shown with any value" SURVIVED (no killer ran, no first line). Also R13A5 and R13A8 are killed by the very same first failing line (test_a_bug_in_banner_or_unconfirmed_is_not_turned_into_a_ban...); the runner exits 1 for it. raw/named.log
3. Fail-before: test_mode_banner.py and test_demo_only_guard.py do not even import on dd827d79 or c7eb5c79 with new tests + old src/tools (ModuleNotFoundError: tools.fixed_run). The pass lists below come from a SECOND run where only tools/fixed_run.py (new file) was copied in as well; that is not "old src" strictly.
4. Brief says "five READ_ERRORS sites": I found SIX `except READ_ERRORS` handlers (mode_banner.py:564,742,775; app.py:273,301,320) plus the post_card handler (app.py:479). All six injected.
5. Brief says "the 20 COMPUTED_EXPECT rows": the table has 24 entries (B1,B2,B2b,B21,B22,B24,B38,B39,B40,B41,B59,B60,G30,G38,G51-G57,G81,G82,J3).
6. tools/demo_only_guard.py does not exist on origin/main (new file; main has no fixed_run.py either), so "main's version of the masker" cannot be run. I compared with the core redactor of main (hadavin_sdk.guard.redact, unchanged by this branch) instead.
7. pyproject.toml diff vs origin/main (not vs c7eb5c79 only) removes `pytest-xdist==3.8.0` from the test group; origin/main is at 51c9fc4f "run the unit suite on 3 pytest-xdist workers (#99)". Not judged, recorded.

## 1 Focused tests (one pytest per file, -x, rc=0 each, both versions)
| file | 3.13 | 3.12 |
| tests/test_mode_banner.py | 188 passed | 188 passed |
| tests/test_demo_only_guard.py | 152 passed | 152 passed |
| tests/test_banner_mutant_table.py | 21 passed | 21 passed |
| tests/test_changelog_numbers.py | 7 passed | 7 passed |
| tests/test_stage_names.py | 97 passed | 97 passed |
| tests/test_demo_only_guard_ci.py | 8 passed | 8 passed |
| tests/test_repo_rules.py | 40 passed | 40 passed |
| tests/test_scan_repo.py | 31 passed | 31 passed |
(grep for fixed_run|scan_repo|demo_only_guard|READ_ERRORS|_DELIVERY_ERRORS also names tests/banner_mutants.py, tests/fixed_run.py: not test files.) Builder's 3.12 per-file summary /tmp/claude-0/b13-p312.sum (read only): 52 files, ends DONE, no failed/error line, 1 skipped (test_k5_postgres).
NOT RUN: 126 test files (80 top-level tests/test_*.py + 46 in tests/*/); list in raw/test-files-not-run.txt. No full suite (cloud limit).

## 2 Mutant rows (tests/banner_mutants.py, 3.13, name substring)
Named rows `R13A R13B B62 R9A4 R9D4 R9D8 R9D14 R11C1 R12` matched 22 rows: 21 good (B62 and R9A4 are CRASH-type rows, good; the rest KILLED), 1 BAD (R13B2 SURVIVED). Rows R13A1-9, R13B1,B3,B4, R9D4, R9D8, R9D14, R11C1, R12B1, R12C1, R12C2 killed. Final line: `20 of 22 good; problems: ['R13B2 ...', 'shared:R13A5+R13A8']` (rc=1).
Sample: random.seed(13), random.sample of the 311 other rows (of 333), 60 rows run in 3 chunks (raw/sample.json, s0.log, s10.log, s30.log): 60 of 60 KILLED/good, no shared first lines, no BAD.
Leftover mutation: the runner works in a temp copy; `git status --short` in the worktree and in /home/user/hadavin-sdk after the runs showed no modified tracked file (only untracked __pycache__).

## 3 COMPUTED_EXPECT rows (24, run through run_mutants, expect text tested with `in` against the first failing line)
All 24 KILLED, expect in first failing line = True for every one (raw/computed.log). Weak-looking: G51-G55 expect `Error: .gz` etc. matches inside `AssertionError: .gz` (the first line is only `AssertionError: .gz`).

## 4 Fail-before (new tests/* from 63996217 copied over old trees; old src and tools)
| tree | file | result |
| dd827d79 | test_mode_banner | collection ERROR tools.fixed_run missing (0 tests run) |
| dd827d79 | test_demo_only_guard | collection ERROR tools.fixed_run missing |
| dd827d79 | test_banner_mutant_table | 3 failed, 18 passed |
| c7eb5c79 | test_mode_banner | collection ERROR |
| c7eb5c79 | test_demo_only_guard | collection ERROR |
| c7eb5c79 | test_banner_mutant_table | 2 failed, 19 passed |
Second run with tools/fixed_run.py also copied in: dd827d79: mode_banner 44 failed/144 passed, guard 12 failed/140 passed; c7eb5c79: mode_banner 6 failed/182 passed, guard 3 failed/149 passed.
Failing on dd827d79 (table): every_row_of_the_table_has_its_own_label..., the_changelog_states_the_row_count_of_the_table, test_pin_every_equivalent_mutation... ; on c7eb5c79 the first two.
Tests that PASS on the old trees and are not named test_pin_* (what the reviewers need): full id lists in raw/pass-<sha>-<file>.txt. Counts: dd827d79 mode_banner 110, guard 123, table 8; c7eb5c79 mode_banner 141, guard 132, table 8. (Test-file count of failures named test_pin_* in the shim run: 7 on dd827d79, 0 on c7eb5c79, so almost all failures are non-pin tests.) Counts are parametrized ids as pytest -rA prints them.

## 5 Static checks
Suppressions on added lines of `git diff origin/main 63996217 -- . ':!handover'` (11541 added lines): 0 matches for noqa|type: *ignore|fmt: *skip|pragma: *no cover|NOSONAR|nosec.
pyproject.toml per-file-ignores: only `"tests/**" = ["S101"]`; ruff extend-select B DTZ I S TID UP.
ruff check: see failure 1 (without demos: 1 error too). ruff format --check: all formatted.
`bandit -ll -r src tools` rc=0: "No issues identified", Low 12, Medium 0, High 0, skipped via nosec 3 (pre-existing: nosec warnings at src/hadavin_sdk/tools.py:389).

## 6 Masker (tools/demo_only_guard.py `_hide_secrets` at 63996217 vs main's core redactor hadavin_sdk.guard.redact; main has no guard masker)
bypass=true -> guard `bypass=true`, core `bypass=true` (same)
bypass=true x -> guard `bypass=<hidden> x`, core `bypass=true x` (guard hides more)
bypass=abc123 -> guard `bypass=<hidden>`, core `bypass=<SECRET_1>`
bypass_key=abc -> guard `bypass_key=<hidden>`, core `bypass_key=abc` (guard hides more)
authorization=Bearer abcdefgh -> guard `authorization=<hidden>`, core `authorization=Bearer <SECRET_1>`
authorization=Bearer abcdefghij -> guard `authorization=<hidden>`, core `authorization=Bearer <SECRET_1>`
Bearer abcdefghijk (11) -> both shown unchanged (same)
Bearer abc123defg -> guard `Bearer <hidden>`, core shown (guard hides more)
Basic abcdefg (7) -> both shown (same)
Basic abc1234 -> guard `Basic <hidden>`, core shown (guard hides more)
"Bearer"+12 letters joined (`Bearerqwertyuiopas`) -> both shown; with a space (`Bearer qwertyuiopas`) -> guard `Bearer <hidden>`, core `Bearer <BEARER_1>`; `Bearer qwertyuiop` (10) both shown.
Where the guard shows MORE than the core: none in this table. (`bypass=true` shown by both.)

## 7 Surprise exception (a ZeroDivisionError subclass, not in READ_ERRORS nor _DELIVERY_ERRORS), monkeypatched in, no file changed (raw/inject.py)
PROPAGATED (not swallowed) at: mode_banner.py:564, :742, :775; app.py:273 (_seal), :301 (_known_overrides), :320 (App.mode_banner); post_card app.py:479. Controls: OSError at post_card returns Delivery(ok=False, reason='OSError'); ValueError at :742 returns the unconfirmed banner.

## 8 Cleanup
Worktrees ER-pdbanner13, ER13-old-dd827d79, ER13-old-c7eb5c79 removed. No process of mine left. Nothing committed. Builder's scratch /tmp/wt-c7 and its run untouched.
