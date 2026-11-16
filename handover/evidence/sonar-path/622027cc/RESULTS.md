# Evidence for SONAR-PATH batch 5, round 5 (head 622027cc0aff5168c61deb79d1334334af3289b2)

EVIDENCE RUNNER output. Records only; no verdict. Raw files are under `raw/`. Nothing was committed or pushed.
Merge-base of the branch with origin/main is 81a5aadb (origin/main itself is now 51c9fc4f). Python 3.13.18 and 3.12 venvs, PYTHONPATH set to the worktree `src`;
`hadavin_sdk.__file__` printed as `/home/user/build/E-head/src/hadavin_sdk/__init__.py` (raw/00-head.txt, raw/t313/pyfile.txt, raw/t312/pyfile.txt).

## Failures first
1. FAIL, tests/test_pathguard_tripwire.py (1 failed, 79 passed, same on 3.13 and 3.12):
   `test_no_file_operation_in_the_package_works_on_an_unchecked_path_unless_listed_with_a_reason` ->
   `src/hadavin_sdk/registry.py | _load_tools | .is_file: listed (1) but no hit is left`. The exception fixture line 62
   (`tests/fixtures/pathguard_exceptions.txt`) lists an `.is_file` that the code no longer has as an unchecked call
   (registry.py:252-255 now joins through `pathguard.join` first). Raw: raw/t313/test_pathguard_tripwire.log. Clean worktree, no local edits.
2. The 3 audit-drop tests the brief names do NOT fail on abb3e90a (see section 5).
3. The mutant table has 175 rows, not 172 (section 6).
4. Pin/control header counts disagree with the measured items in 3 files (section 7).
5. `_os` raises `PathRefused ... from None`: `__cause__` is None and `__suppress_context__` is True, but `__context__` still holds the OSError whose `.filename` is the path (section 8).

## 1-3. Head, lint, suppressions
- HEAD 622027cc confirmed in worktree /home/user/build/E-head (raw/00-head.txt). Note: the session checkout at /home/user/hadavin-sdk is on core/cloud-handover, not this branch; origin/wip/cloud-sonar-path2 = 622027cc.
- ruff 0.17.1 `check src tests`: pass; `format --check src tests`: 299 files formatted; with CI scope (`src tests demos tools`): pass, 334 files. bandit -ll (src, and src demos tools): exit 0, no issue; only warnings "nosec encountered (B102) tools.py:394" and "(B608) demos/ask-your-data/db/lumen.py:723" (not added lines). raw/01-ruff.txt, raw/01b-ci-scope.txt.
- Suppression grep on added lines of the merge-base diff (noqa, type: ignore, fmt: skip, pragma: no cover, NOSONAR, nosec): 0 hits. pyproject.toml is not in the diff, so no new per-file-ignores. raw/02-suppress.txt.

## 4. Focused tests (each file run on its own, no -x)
- Selection: all test_pathguard*.py, test_changelog_claims, test_k1b_cli, test_k1b_replay, plus every file whose text imports a changed module (grep) = 72 files (raw/03-testfile-list.txt), plus 3 more found by symbol grep (test_k5_producers, test_k5_round11, test_s2_audit; raw/03b-extra-list.txt), plus 4 repo guard tests run on 3.13 only (test_no_hardcoded_values, test_no_reference_material, test_scan_repo, test_migration_numbers_guards: 15+3+31+76 passed).
- py3.13: 72 files, 1 failed (item 1 above), 30 skipped (all Postgres/DB tests). py3.12: same, 1 failed, same 30 skipped. Per-file lines: raw/t313/summary.txt, raw/t312/summary.txt (a few files print a dots line instead of a summary; rc=0). Extra 3 files: all pass on both (raw/t313x, raw/t312x).
- NOT run: 18 files of 103 in tests/ (raw/04-not-run.txt), e.g. test_mutation_runner*.py, test_k5_perf.py, test_http_metadata.py, test_g4_parity.py; 14 of these were not selected because the grep found no link to a changed module. The selection is a grep, so a file that reaches a changed module only indirectly can be missing. The full suite was not run (cloud limit). Python 3.12 did not run the 4 guard tests.

## 5. Fail-before (real old trees: copy of abb3e90a, and origin/main src + head pathguard.py, both with the head tests and tools overlaid)
(c) abb3e90a (raw/fb-c/): test_changelog_claims 23 failed; batch4 8 failed; batch5 12 failed, 15 passed; tripwire 2 failed; test_pathguard, batch3, callers, sites, k1b_replay, p3b_neutral_audit, s2_audit all pass.
Failing lines of batch5 on abb3e90a: long-name params 256/257/300/1000; `test_pin_the_error_of_the_operating_system_is_never_chained_or_quoted`; `test_pin_every_short_mix_of_long_names_dots_links_and_loops_...`; `test_every_mutant_row_old_text_occurs_exactly_once_in_its_file`; `test_pin_an_error_while_asking_if_a_path_is_a_file_is_a_refusal`; `test_a_tool_module_part_longer_than_a_file_name_...`; `test_a_key_file_name_too_long_...`; `test_a_key_path_with_an_unknown_home_...`; `test_a_tools_file_for_an_agent_id_longer_than_a_file_name_...` (raw/fb-c/test_pathguard_batch5.log).
(a) origin/main src + head pathguard.py (raw/fb-a/): changelog collection error; test_pathguard 15 failed; batch3 44; batch4 26; batch5 17; callers 2; sites 19; tripwire 2; test_k1b_cli 1 failed; k1b_replay, p3b, s2_audit pass.
AUDIT-DROP TESTS ON abb3e90a: `test_an_outcome_with_a_bad_event_id_is_dropped_and_counted`, `test_an_outcome_refused_for_another_reason_takes_the_outbox_path_not_the_drop`, `test_a_loop_in_the_objects_folder_takes_the_outbox_path_too` and the control `test_control_reconcile_replays_a_file_when_the_outbox_folder_itself_is_a_link` ALL PASS on abb3e90a (raw/05-c-auditdrop.txt; the tree's local_dir.py still has the old `except pathguard.PathRefused` drop at line 120/132). The docstring of the "another_reason" test says it fails-before on abb3e90a; measured here it does not (on Linux the objects-folder-is-a-file case raises an OSError, which already took the outbox path). Also on abb3e90a, k1b_replay and k1b_cli tests pass (no fail-before for those changes), and the head tests edited in this delta for test_k1b_replay do not fail there.

## 6. Mutant table tests/pathguard_mutants.py (scratch copy /home/user/build/E-work/mut-tree, runner `tools.mutation_runner`, py3.13)
- Rows in `M`: 175 (175 unique names), not 172. All 175 ran (raw/mut/all-rows.txt, chunks raw/mut/chunks/): 153 KILLED, 22 CRASH (the 22 rows with allow_crash), 0 BAD, 0 survived.
- Run in chunks of 10 rows; three chunks (70:80, 80:90, 150:160) ended silently with exit 0 and no summary on the first try (cause not found; other agents' mutation runs share this machine's /tmp) and passed on retry. Earlier attempts (two runs in parallel, then slices of 44) also ended early; their logs are in raw/mut/earlier-attempts/ and are not used for the count.
- `test_every_mutant_row_old_text_occurs_exactly_once_in_its_file` passes at head (batch5 file: 27 items, 27 passed on py3.13/3.12 except none failed; raw/t313/test_pathguard_batch5.log).
- EQUIVALENT (5 entries), baseline vs mutated (raw/06b-equivalent.txt, raw/eq/): baseline 1 failed (the tripwire entry of item 1), 825 passed, over 826 items of pathguard, k1b, s2_audit, p3b, k5_round11 and changelog tests. For each of the 5 hand-written unguarded replacements the only difference is `test_every_equivalent_mutant_still_names_text_that_exists_...` (expected: the text is gone). No behaviour test changed result. Restored tree equals baseline. My replacements: bundle -> `path.joinpath(*rel.split("/"))`; replay -> `out / f"run{run_index}"`; local_dir -> `self.outbox / f"{event.event_id}.json"`; atomic -> `flags |= 0`; `0` for O_BINARY.

## 7. Pin/control labels (raw/07-labels.txt)
Rule in file headers: control passes on (a) and (b); pin passes on (a) and fails on (b); every other name fails on (a). I measured (a) and (c) (abb3e90a). (b) = origin/main with an empty stand-in module: not reproducible; my empty module gives collection errors in 6 files (raw/fb-b/), so (b) is NOT checked.
- Header counts equal the measured item counts by name in test_pathguard.py (3/31/15), batch3 (12/42/44), batch4 (6/0/26), callers (3/0/2), sites (3/11/19).
- MISMATCH batch5: header 1 control, 9 pin, 12 other (22) vs measured 27 items: by name 1 / 6 / 20. Three "other"-named items PASS on (a): long-name params [250], [254], [255] (rule says other fails on (a)).
- MISMATCH tripwire: header 19 control, 0 pin, 2 other (21) vs 80 items: 78 control-named, 2 other.
- MISMATCH changelog_claims: header 23/11/30 (64) vs 65 items (control 22 pass+1 fail, pin 5 pass+6 fail on (c)); on (a) the file does not collect.
- On (c) abb3e90a a control-named test fails: batch4 `test_control_every_converted_call_site_has_a_mutant_row_or_an_equivalent_entry`; changelog `test_control_every_bullet_of_the_entry_is_named_by_a_claim_test`. Pin-named tests failing on (c) include 3 in batch5 and 5 param items + 1 more in changelog (listed in raw/07-labels.txt).
- test_k1b_cli and test_k1b_replay have no label header.

## 8. Error-leak probe (raw/08-probe-py3.13.txt, raw/08-probe-py3.12.txt; script /home/user/build/E-work/probe8.py)
- Names 255 B: accepted; 256, 300 B: R5 "too long"; NUL: R4; colon: R3; CON/nul/COM1/con.txt/LPT¹: R7; "CON  ", trailing dot/space/dots: R6; "..": R1. In every refusal the message is `probe: <fixed text>`, no path or name text (leak_in_msg False). For these name rules, no exception chain (cause None, context None).
- OS-level refusals (symlink loop strict, operator_dir on loop, operator_file/operator_dir on a missing path): R10 "cannot be resolved", message has no path; `__cause__` None, `__suppress_context__` True, BUT `__context__` is the original OSError/FileNotFoundError and its `.filename` holds the path (context_holds_path True). A traceback does not print it; code that reads `__context__` or `exc.__context__.filename` sees it. Not chained for display only.
- Base with a 300-byte component and non-strict join: returned a result, no refusal on this file system. `join(tmp,"loop","x")` non-strict through a symlink loop: returned a result. Path text over 4096 B: R5. NUL in base or path: R4. Symlink escape: R8. kind mismatch: R11.

## 9. pathguard.py size and call sites (raw/09-callsites.txt)
- src/hadavin_sdk/pathguard.py: 220 lines (limit 220: at the limit, zero room).
- The builder-report table was not supplied to me, so no table comparison was done. Files with a pathguard import: cli, config, hashing, registry, tools, actions/{secrets_file,secrets_vault}, audit/{local_dir,signer}, guard/judge, k1b/{atomic,bundle,causelist,replay,score}, llm/fake. Of the 8 files named in the brief: score (7 calls), hashing (3), secrets_file (3), signer (5), judge (1), secrets_vault (1), registry (1) call `pathguard.join/inside/operator_*`; tools.py imports pathguard but only reads the constant `pathguard.MAX_COMPONENT_BYTES` (line 51), no join. registry.py `golden_path`/`_prompt_path`/`confined` still use `config.confined` (entries listed as "checked | confined" in the exceptions fixture).

## Not done / uncertain
- No SonarCloud result was checked; nothing here shows a SonarCloud finding is cleared.
- Full suite, mutation of src outside the table, load/perf tests, and 18 test files (list above) were not run. Postgres tests skipped (no database).
- (b) label measurement not reproducible; the 26 control-labelled pin entries in the brief were not re-applied.
- Cause of the silent early exits of the mutant runner is unknown.
- Stale temp folders /tmp/mutants_* and /tmp/mutant_ini_* exist; some were made at 00:17-00:22, some at 05:5x by other sessions; I did not delete any because I cannot tell which are mine.
