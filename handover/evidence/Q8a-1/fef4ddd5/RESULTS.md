# EVIDENCE RUNNER results: Q8a-1 batch 14, head fef4ddd5d085f6b0444e4af420ef9d2db2b850ad (tag Q8a1-b14, SECURITY path)
Recorded 2026-11-12 08:3x-08:5x UTC (14:0x-14:2x IST). Run, not judged. Raw logs: /home/user/build/evidence-raw/Q8a1-b14-fef4ddd5/ (outside the repo). Worktree clean at start and end (git status empty, also after the mutant run).

## Failed or not run, first
- Nothing in items 1-6 failed. Exceptions to the plain command as given:
  - `uv sync --locked --no-build` fails here (`hadavin-sdk` editable has no binary distribution); I ran `uv sync --locked --all-extras --group test` (rc 0). Same lockfile.
  - bandit is not in the synced venv; run as `uv run --no-sync --with bandit bandit ...` (rc 0).
  - Builder's two failures were NOT reproduced: test_k5_round5 r1_hold_run_ids passed on this head; demo_askdata dblink-connect passed on my Postgres (my server listens on 127.0.0.1 with its own socket dir). The `unshare -m` re-run was therefore not needed and not done.
  - The builder's fail-before number "3 failed / 516 passed" is not what I got for the four named files (see item 4); it matches a run that also includes tests/test_stage_names.py (1 failed there, see item 4).
  - Not run: CI steps outside the brief (perf step, Python 3.12 job). The flaky timing test was not asked for and was not run.

## Table
| Item | Command (all via env -u of the cloud variables, own venv, own Postgres 16.15 on 127.0.0.1:56731) | Exit | Result |
|---|---|---|---|
| head | git rev-parse HEAD; git status --short | 0 | fef4ddd5d085f6b0444e4af420ef9d2db2b850ad; 0 changed files |
| 1 full pytest | heavy.sh ... pytest -p no:cacheprovider -q -m "not live and not perf" -rfEs (started 08:34:24Z, 282.61 s) | 0 | `11381 passed, 1 skipped, 28 deselected in 282.61s`; the skip: tests/contracts/test_llm.py:95 Stubber refuses a malformed Converse shape |
| 2 stage mutants | heavy.sh ... python tests/stage_mutants.py (08:39:18Z-08:49:33Z) | 0 | `281 of 281 good; problems: []` = 263 KILLED + 18 CRASH (CRASH lines are the M16g..M18k ones, counted good by the runner). Z65-Z99: 35 of 35 KILLED, Z89 KILLED on this run. Z28, Z47, Z55 KILLED. Per-mutant lines: mutants-Z28-47-55-65-99.txt |
| 3 ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| 3 ruff format | ruff format --check src tests demos tools | 0 | 329 files already formatted |
| 3 bandit | bandit -ll -r src; and bandit -q -r src demos tools -ll | 0 / 0 | src: High 0, Medium 0, Low 6 (below the -ll level); both runs only print tester warnings (one `nosec encountered (B102) ... tools.py:410` with no failed test) |
| 3 scan_repo | python tools/scan_repo.py | 0 | no output beyond a uv warning |
| 3 gitleaks | gitleaks git --redact --no-banner --exit-code 1 --config .gitleaks.toml --log-opts="origin/main..HEAD" . | 0 | no leaks found (~890 KB scanned) |
| list | git diff --name-only origin/main...HEAD (origin/main = 2a8c2aac) | 0 | 94 files: diff-names.txt |

## Item 4: fail-before (detached worktree of 918c03455704777add06ac250271a701c706fde5, src from that commit via PYTHONPATH; only the four test files copied in)
| Files | Result on 918c0345 | Same files on fef4ddd5 |
|---|---|---|
| tests/test_q8a1_b14_fixes.py | 22 failed, 88 passed | (both files together) 155 passed |
| tests/test_guard_reasons.py (with _text_guard.py, _guard_allowances.py) | 2 failed, 43 passed: test_the_claim_of_each_reason_holds_in_the_code[BUNDLE] and [HOST] | |
| extra, not asked: tests/test_stage_names.py (head version copied in) | 1 failed, 473 passed: test_no_config_derived_name_is_put_in_a_message_outside_the_one_filter | |
- The 24 failing test ids on old code (22 + 2) are in failbefore-ids.txt (lines starting FAILED); the extra file's one failure is named above.
- Every new test that PASSES on old code: 131 ids (88 in the b14 file, 43 in test_guard_reasons.py), listed in new-tests-passing-on-old-code.txt. No judgment given.

## Item 5: probes with made-up values (verbatim output: probe5.out; script: probe5.py, values built from parts)
- Route.model_id: `anthropic.claude-sonnet-5-5-v1:0` ACCEPTED (len 32); `us.anthropic.claude-haiku-5-5-v1:0` ACCEPTED (len 34). Both are bare Bedrock-shaped ids; I recorded them as they came out. A value with a space: REFUSED. 129 characters: REFUSED. 128 characters of one letter: REFUSED (value_error, because it contains a 32-character run). 32-character alphanumeric run alone and inside `x-<run>-y`: REFUSED. 31-character run: ACCEPTED. Empty string: REFUSED, and the error text does contain the (empty) value. Value with a newline: REFUSED. None of the non-empty refused values appear in the error text.
- Tick, plain RuntimeError with a marker text: `tick._message(RuntimeError(m))` = `(details withheld)`; same for ValueError; the package's own ConfigError shows its text. `tick._each([1], boom, "probe step")` logs `WARNING hadavin_sdk.tick probe step: RuntimeError` (class name only, marker not in the log) and then re-raises the RuntimeError to the caller, whose own text is the marker.
- DSN with sslmode: odd mode with iam_auth -> ConfigError `... not <not shown>` (odd text not echoed); `require` and `disable` shown as the mode word; verify-full without a CA bundle -> the sslrootcert message; odd mode without iam_auth is returned as is (passed on to libpq); a URI-style DSN with an odd mode and iam_auth -> `not <not shown>`.

## Item 6: guard sites (guardcount.py / guardcount.out; run over src/ with the widened guard)
- src modules 109; 8 exempt prefixes; 101 modules scanned; 590 sites seen.
- Allowance rows: GUARD_ALLOWED 118 + NEW_ALLOWED 445 = 563 rows; all 563 rows used; 590 sites matched to a row (several sites share a row).
- FOUND (not allowed): 0. STALE: 0.
- UNCHECKED set (reasons with no check by code): CARD (22 rows), REDACTED (4), STOREID (39), URL (8) = 73 of the 445 NEW_ALLOWED rows. NEW_ALLOWED rows by reason are in guardcount.out.

## Cleanup
Own Postgres stopped and its folder removed; my worktrees removed. Nothing pushed, nothing committed, no source or test of the head edited.
