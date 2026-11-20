# REC: reconciliation check of the 4 commits `git cherry` still lists

Head: origin/cloud/core-c 64948390a; branch wip/cloud-core-c/rec. Result: all four are SUPERSEDED in content (no port needed); one unrelated red baseline (PU1) re-pinned from a measured value.

## Per commit
| Commit | Verdict | Evidence |
|---|---|---|
| 73d624c12 (G2: defang every dot, glued e-mails one pass) | SUPERSEDED (MIX + tidy-p1d + G8) | gate.py has `_DOMAIN_LAST`, `_DOTTED_TOKEN`, `_NAME_DOT`, `_whole_token`, the `certain` flag of `_outside_code`, `_PLACEHOLDER_DEFANGED`, `_undefang_prose`. Differences are deliberate rewrites: `_DOMAIN_LAST` lookbehind/lookahead narrower (defangs more: HEAD does not refuse a host behind `.[/` or before `-`), `undefang_text` also uses `certain=True`. redact.py has `_sub_glued`, `_NOT_ADDRESS`, `_GLUED_WINDOW`, with the search for the token end bounded (review M1). Its tests are in tests/test_p1d_a_paths.py (HEAD version is larger). TESTED: test_p1d_a_paths + test_p1d_a_rows 139 passed; p1d_a_mutants 50 of 51 killed, A15 survivor = known equivalent. |
| 7de1c4f86 (G3 step 2: fold scan port, runmap views, CPU deadline) | SUPERSEDED (MIX; fold scan since reworked by G1/G4/G9/G12) | redact.py has the fold scan; runmap `_views` has the six views plus canonical/composed of the text without marks; `REDACT_BUDGET_S` is thread CPU time (`time.thread_time`), one deadline passed to both `redact()` calls and `_decoded_masks`; pyproject TID251 exemption row for guard/redact.py present. defaults.py comment is the reworded one. Lines "missing" by text compare are reformatted/removed (U+2044 early return removed as dead code, see redact_mutants docstring N1/N14). TESTED: fold/budget/seams/property tests green, redact_mutants 123 of 123 good. |
| 2be153143 (re-pin textnorm manifest hash, CHANGELOG) | SUPERSEDED | textnorm.py changed afterwards; manifest in HEAD pins 928a4247... which equals the measured sha256 of src/hadavin_sdk/guard/textnorm.py at HEAD (test_textnorm_meta green). The old hash e7a93738... would be wrong. CHANGELOG already carries the `RedactionResult.actions` entry. No textnorm.py change by REC, so no re-pin. |
| 7d6b5fbff (RedactionResult.actions + cb-1-1 test) | SUPERSEDED, NOT missing | `RedactionResult.actions` is in HEAD (redact.py: dataclass field, `_Redactor.actions`, journal rollback `_journal_actions`, count per masked value, per sweep copy, per withheld line). tests/test_redact_g3_port.py in HEAD (235 lines changed vs the commit) holds the sweep test with a TENANT value instead of the UUID spelling. TESTED: test_redact_g3_port green. |

Method: added lines of each commit compared with HEAD file contents, then read the remaining lines; plus guard tests.

## Measured
- ruff check src tests: clean; ruff format --check: clean (366 files). TESTED.
- pytest -n 3 -m "not perf" on tests/test_redact_*, test_runmap_*, test_textnorm*, test_p1d_*, test_s3_gate, test_gate_*, test_k1b_*: 4879 passed, 2 failed, 1 skipped, 56 xfailed (489 s). TESTED.
- The 2 failures: test_row_PU1_card / test_row_PU1_model, a baseline already red before REC (also on d462a4c80, see G13 notes, TIDYP notes). They expected `password=<SECRET_3> x` (TIDYP re-pin: the map then held `ab&amp;`, `ab&amp`, `ab&`). At this head the map holds ONE value (`{'<SECRET_1>': 'ab&amp;'}`) and the entries give `password=<SECRET_2> x`, the original pre-G9 number. REC re-pinned tests/fixtures/p1d_cases.py SECRET_3 -> SECRET_2 from the measured output (LEAD to confirm; the old pin was itself a measured re-pin). After: 139 passed. TESTED.
- tests/redact_mutants.py: 123 of 123 good. TESTED. tests/g8_mutants.py: 43 of 43 good. TESTED. tests/p1d_a_mutants.py: 50 of 51 killed, A15 (known equivalent). TESTED.
- Perf-marked tests, whole suite, CI: NOT RUN.
- No mutant counts, no textnorm manifest, no CHANGELOG changed.
