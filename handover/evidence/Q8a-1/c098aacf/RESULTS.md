# EVIDENCE RUNNER results: Q8a-1 batch 15, head c098aacf (origin/wip/cloud-q8a1-b15), previous head fef4ddd5

Run 2026-11-12 by the evidence runner. I recorded; I did not judge, fix, commit or push. Raw logs: /home/user/build/evidence-raw/Q8a1-b15-c098aacf/ (outside the repo).
Head checked: `git rev-parse HEAD` = c098aacf30faf836569b616c50ea87233547a942, tree clean (own detached worktree).

## What failed, differed or was not run (first)
1. Install command in the common brief failed: `uv sync --locked --no-build ...` exits 2 ("hadavin-sdk editable can't be installed because it is marked as --no-build"). I ran `uv sync --locked --all-extras --group test` (without `--no-build`), exit 0. Python 3.13.18 in the venv.
2. Fail-before: 22 failed, 769 passed. The builder's figure is 21 failed / 694 passed. The difference: I also ran tests/test_migration_numbers_guards.py (it fails on old code, because the copied-in mutant file names text the old source lacks): 1 extra failure, 75 extra passes. Without that file the failing set is the builder's 21.
3. 25 new tests pass on old code (list below). 14 of them are the R15a-R15n planted-fault rows of tests/test_stage_names.py: they pass on old src because they exercise tests/_text_guard.py (test code that I copied in), not src. The builder's note said the 13 b15 tests all fail: confirmed (13 of 13 in tests/test_q8a1_b15_fixes.py fail).
4. AuditEvent.event_id probe: the refusal text of a hostile id DOES contain the id for ids that match no pattern problem of length or control characters (pydantic prints input_value). Verbatim: see probe 5 below. (Recorded, not judged.)
5. Not run: the flaky timing test (item 9 of the common brief) and the perf tests; this brief did not name a perf item. The dblink-connect test passed in my run (it failed for the builder).
6. Not pushed or committed: the common brief says the lead pushes; no push recipe exists in it.

## Table
| # | item | command (clean env, own Postgres 16.15 on a port of my choice, heavy.sh) | exit | last line |
|---|---|---|---|---|
| 1 | full pytest | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` | 0 | 11423 passed, 1 skipped, 28 deselected in 306.06s (the skip: tests/contracts/test_llm.py:95 Stubber) |
| 2 | stage mutants | `python tests/stage_mutants.py` | 0 | 325 of 325 good; problems: [] |
| 2b | migration-number mutants (the runner named in CI-ready docstring; not a CI step) | `python tests/migration_numbers_mutants.py` | 0 | 36 of 36 good; problems: [] |
| 3a | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 3b | ruff format | `ruff format --check src tests demos tools` | 0 | 331 files already formatted |
| 3c | bandit | `bandit -q -r src demos tools -ll` (uv --with bandit) | 0 | only warnings: nosec B102 at src/hadavin_sdk/tools.py:417 has no failed test; "bytes is not a test name" |
| 3d | repo scan | `python tools/scan_repo.py` | 0 | (no findings output) |
| 3e | gitleaks | `gitleaks git --redact --log-opts origin/main..HEAD` | 0 | no leaks found |
| 4 | fail-before | old src (fef4ddd5), the 11 changed or new test files of the delta copied in, 8 test files run | 1 (expected) | 22 failed, 769 passed |
| 5 | probes | my own scripts: probe-guard.log, probe-runtime.log | 0 | see below |
| 6 | guard over src | tests.test_stage_names._guard_violations() | 0 | modules 109, found 0, stale 0, ALL_ALLOWED rows 547 (NEW_ALLOWED 432, GUARD_ALLOWED 115), reasons 52, UNCHECKED = [CARD, REDACTED] |

## Item 2 detail
Z12 (a failing audit folder raises inside the except block again): KILLED. Z100 to Z143: 44 of 44 KILLED (per-mutant status in stage-mutants-Z-status.txt). The run is the full run on the final head, after the builder's Z12 fix (the builder had not repeated it). Total BAD rows: 0.

## Item 4 detail (fail-before)
Setup: detached worktree of fef4ddd5 (src from fef4ddd5, PYTHONPATH pointed at its src, verified the import path), copied from c098aacf: tests/_guard_allowances.py, _text_guard.py, migration_numbers_mutants.py, stage_mutants.py, test_changelog_claims.py, test_guard_reasons.py, test_k5_round7.py, test_q8a1_b13_fixes.py, test_q8a1_b14_fixes.py, test_q8a1_b15_fixes.py, test_stage_names.py. CHANGELOG.md stayed the old one. Tests run: test_q8a1_b15_fixes, test_changelog_claims, test_guard_reasons, test_k5_round7, test_q8a1_b13_fixes, test_q8a1_b14_fixes, test_stage_names, test_migration_numbers_guards.
- Failed ids (22): failbefore-failed-ids.txt (13 of 13 b15 tests, changelog names-test, 5 reason checks FILENAME/FRAMES/KEPTID/NUM/STOREID, the b14 describe test, the guard scan over src, test_every_mutant_still_applies_to_the_source).
- New test ids (head minus base collection of these 8 files): 43; failing on old: 18; passing on old: 25 (new-tests-passing-on-old-code.txt): changelog path test; reason checks CLOSED, OWNERROR, URL; 14 planted-fault rows R15a-R15n; 7 clean-form rows "R15 ...".

## Item 5 and 6 (verbatim outputs are in probe-guard.log and probe-runtime.log)
- Guard, my own planted modules: error object built outside raise (raised later) found 1; same returned found 1; out-parameter list joined into an error found 1 (site `out.append(name)`), control with written text found 0; raise inside except without from found 1 ([context]); with `from None` found 0; with `from exc` found 1 ([cause]); parameter in f-string found 1; written text found 0.
- Route.model_id: a 32-character run refused, a `model@sha256:<64 hex>` pin refused, both with "a model id has no run of 32 or more letters and digits ... write the model's short name or version, not an immutable hash pin" and the value not in the text; a normal id, a 31-character run and two 20-character pieces cut by `-` accepted.
- NotFound(caller id): str = 'no row has this id', repr = NotFound('no row has this id'), .key keeps the id; MemoryStore().get_run(id) the same.
- AuditEvent.event_id: refused: '../x', '..\\x', '/etc/x', 'a/b', '.hidden', 'a b', '', 129 chars, NUL, 'a.json', trailing newline; accepted: 'evt-ok_1' and new_id("evt"). Text for '../x' (verbatim): "String should match pattern '^[A-Za-z0-9][A-Za-z0-9_:-]{0,127}$' [type=string_pattern_mismatch, input_value='../x', input_type=str]" (the refused id is inside the text).
- check-config: good config exit 0, stdout "the configuration is accepted", 0 connect attempts (socket.connect patched), 61 files before and after with the same mtimes and sizes. Refused configs (key-shaped model id, duplicate key, unknown key, bad YAML): exit 1 each, stderr "refused: ..." naming field and rule, my marker value not in stdout or stderr.

## Hygiene
Own Postgres stopped and its folder removed; my worktrees removed (see end of this file for the check). Slots: waited in the heavy.sh queue for the fail-before run (about 20 minutes); full pytest 5 min 6 s of run time.

Cleanup check: Postgres stopped and folder removed; worktrees wt, wt-mut, wt-old, wt-basecollect removed; venv removed. No processes of mine left.
