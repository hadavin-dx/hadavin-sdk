# EVIDENCE RUNNER results: Q8a-1 batch 16, head 20581c80 (round 17)

Head confirmed: `git rev-parse HEAD` in my detached worktree = 20581c809a247e2d5f4f72b626c6af045e81872f (= origin/wip/cloud-q8a1-b16), tree clean. Previous head c098aacf. I recorded results only and fixed nothing. Raw logs: /home/user/build/evidence-raw/Q8a1-b16-20581c80/ (outside the repo).

## What failed or was not run (first)
- Mutant Z150 is "BAD WRONG_REASON": the planted fault was caught, but by test `test_the_guard_finds_each_planted_fault_alone[R15c an attribute set to the text of an error]` with first failing line `AssertionError: ('R15c an attribute set to the text of an error', [])`. The runner prints 362 of 363 good; stage_mutants.py exit code 1. Same as the builder's own claim.
- Python 3.12, semgrep, zizmor, trivy, pip-audit: not run (impossible now, per the brief). Python here is 3.13.
- The known timing test (`test_the_timing_harness_flags_a_quadratic_stand_in`) was not touched or run alone: ticket item 7 says do not touch it. It passed inside the full run (not a separate 3+3 run).
- No perf run (the ticket names no perf item). No CI-only step beyond those in the table was run (the `perf` job, the semgrep/zizmor/trivy steps).
- `uv sync --locked --no-build` fails here ("hadavin-sdk marked --no-build but has no binary distribution"); I used `uv sync --locked --all-extras --group test` instead (exit 0).
- Slip of mine: to test the nobody wrapper I ran `stage_mutants.py M1` (matched 138 mutants) once without heavy.sh; log shown only in my transcript, result 138 of 138 good. It did not touch the head (runner works on a temp copy).
- Mutant runners ran as user nobody (uid 65534) in a second detached worktree of 20581c80 (wt-mut), one at a time, via heavy.sh, because the full pytest was using the first worktree.

## Table
| Item | Command (short) | Exit | Last line / result |
|---|---|---|---|
| 1 diff names | `git diff --name-only origin/main...HEAD` | 0 | 105 files (list in raw dir `item1-diff-names.txt`; origin/main = 2a8c2aac) |
| 2a ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b ruff format | `ruff format --check src tests demos tools` | 0 | 332 files already formatted |
| 3 bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | no issues printed; only 3 warning lines (nosec B102 at tools.py:417 with no failed test; "bytes is not a test name") |
| 4a scan_repo | `python tools/scan_repo.py` | 0 | no findings printed |
| 4b gitleaks | `gitleaks git ... origin/main..HEAD` | 0 | 40 commits scanned, no leaks found |
| 5 full pytest | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh, own Postgres 16.15 (PGHOST/PGPORT/PGUSER in server and test env) | 0 | 11480 passed, 1 skipped, 28 deselected in 301.63s. Skip by name: `tests/contracts/test_llm.py:95` "Stubber refuses a malformed Converse shape before the kind sees it". No dblink failure this time. |
| 6a stage mutants | `python tests/stage_mutants.py` as nobody via heavy.sh | 1 | 362 of 363 good; problems: Z150 (above). 344 KILLED, 18 CRASH (all marked ok), 1 BAD. Non-ok rows: `stage_mutants-non-ok.txt` |
| 6b runner mutants | `python tests/mutation_runner_mutants.py` as nobody via heavy.sh | 0 | 62 of 62 good; problems: [] |
| 6c migration-number mutants (file changed in the delta; not named by ci.yml) | `python tests/migration_numbers_mutants.py` as nobody via heavy.sh | 0 | 36 of 36 good; problems: [] |
| 7 fail-before | detached worktree of c098aacf (src unchanged, PYTHONPATH=its src; import path printed as wt-old/src), the 8 changed test files of DELTA-FILES.txt copied in; pytest on test_changelog_claims, test_guard_reasons, test_q8a1_b15_fixes, test_q8a1_b16_fixes, test_stage_names | 1 | 27 failed, 591 passed. Failed list: `failbefore-failed.txt` (20 of the 27 are in test_q8a1_b16_fixes.py). Passed on old code: `failbefore-passed-on-old-all.txt` (591 ids); the 5 of test_q8a1_b16_fixes.py: `failbefore-b16-passed-on-old.txt` |
| 8 CHANGELOG claim test | `pytest tests/test_changelog_claims.py` alone | 0 | 3 passed |
| 9 hostile probes | own script `probe.py.txt`, 39 rows, `probes.log.txt`, `probe2.log.txt` | 0 | see next section |

## Hostile probes (my own inputs, made-up markers built from parts, recorded without judgment)
- check-config with a configured model_id of shapes plain, `../M`, `M/..\x`, `M:stream`, `M M`, `M` plus a right-to-left mark: exit 0 for the two valid shapes, exit 2 otherwise; marker in stdout or stderr: none in all 6 rows. The `M/..\x` shape gives "refused: not valid YAML (line 5, column 38)".
- check-config with a made-up library error text raised inside the YAML reader: exit 0, accepted, marker not in output (this planted error happened at a call that check-config did not reach as a failure; recorded as is). With a made-up OSError text on reading config.yaml: exit 2, output `refused: config.yaml: cannot be read (PermissionError)`, marker not in output.
- AuditEvent(event_id=...), 15 shapes (plain, `../M`, `..\M`, `/etc/M`, `M:ads`, `M x`, upper-case, `con`, `nul`, `com1`, newline, NUL, 129 characters, `.M`, `M.json`): all refused with the fixed sentence. In `str(exc)`, `repr(exc)` and `exc.args` the marker is absent. In `exc.errors()` and `exc.json()` the marker IS present (the input value is carried by pydantic's default); `exc.errors(include_input=False)` has no marker (`probe2.log.txt`). The "LEAK" word in `probes.log.txt` for the AuditEvent rows refers to this errors()/json() channel (11 rows).
- `shown_id`: returns `?` for the marker, `evt-<marker>`, a trailing newline, `../M`, an int; returns the id unchanged for `evt-` or `run-` plus 32 hex digits; a str subclass with an overridden `__str__` returns the real id text.
- LocalDirSink.write_intent with an AuditEvent built by model_construct (no validation), 5 event_id shapes: all raise `ValueError('event_id is not a plain file name')`; no file with the marker made; no file in the parent folder. With mkdir raising a made-up OSError text: `AuditUnavailable: intent evt-<32 hex>: OSError`, marker not in output.

## Not checked
Whether the 5 passing tests of test_q8a1_b16_fixes.py on old code are expected (a list only; I make no judgment). The builder's pass-on-old-code table was not compared line by line. The 3 + 3 timing-test runs. A re-run of the full pytest was not needed (the first run has a summary line).

## Cleanup
My Postgres on port 56391 was stopped and its folder deleted. No background processes of mine remain. Worktrees left in place for the lead: /home/user/build/EV-Q8a1-b16-20581c80/{wt,wt-mut,wt-old} (`git worktree remove` when done; wt-mut and its venv are owned by nobody). Nothing committed or pushed.
