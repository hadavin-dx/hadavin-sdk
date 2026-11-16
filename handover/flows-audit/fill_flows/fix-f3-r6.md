# fix-f3-r6 (BUILDER log, 2026-11-16 UTC; nothing committed)

## What did not go as expected / not checked (first)
- One full-suite run in the middle of the work showed a failure at line numbers that did not match the file and "unrecognized arguments: --allow-placeholders"; the next identical run was green. I could not reproduce it and did not find the cause (a file being changed under me by someone else is possible; not verified). Treat as unexplained.
- Review r3 findings 1-7 were "from reading, unproven". I built a fix and a test for each, and ran the tests against the OLD code (below). The behaviour of n8n on a JS escape such as the u0024 form was NOT tested (no n8n here); refusing is the safe side.
- Not run: Python 3.9/3.10/3.12 (only 3.13 here), macOS, real n8n, NFS/WSL. m9 (macOS F_GETPATH branch) is now tested with a fake fcntl module, but the real macOS call is still untested: next step is one run of the suite on a Mac.
- Mutants were re-run only on the 20 old mutants; the NEW code paths (manifest compare in check, signal handling, escape refusal) have no mutation run yet. Next step: a 20-mutant sample on those lines.
- m5 still survives: it is a comment text change (equivalent, no behaviour).
- Added no suppression. Existing noqa: 1 in fill_flows.py, 5 in the test file (unchanged count; my first draft added 2, I removed them by routing through run_cli).
- `--force-hash` + `--no-manifest`: if the manifest cannot be read it is ignored (a cut-short manifest is the reason for the flag), so the subset rule applies only when the manifest still reads.

## Evidence-r5 weaknesses: what I did
| mutant | fix | now |
|---|---|---|
| m18 NOT-READY `bad += 1` | test: clean json + note only, rc 1, "1 problem(s)" | killed |
| m1 `dfd = -0` | test spies os.close on a delete refused before the folder opens; no fd 0..2 is closed | killed |
| m3 "or macOS" | test makes fchmod loosen the folder, asserts the full phrase | killed |
| m10/m11 "not owned by you" | tests with an other-owner lstat for manifest and for a file | killed |
| m12 "sits in a" | assertion added to the jsCode refusal test | killed |
| m9 F_GETPATH split | fake fcntl module + readlink failure; asserts the cut at the first NUL and the fallback | killed |
| m5 comment | equivalent | survives |

## Review r3 fixes (code in fill_flows.py, tests in test_fill_flows.py, README updated)
1. Signals: SIGTERM/SIGHUP now raise an internal stop (clean-up path as for Ctrl-C); clean-up shielded from SIGINT/SIGTERM/SIGHUP; the not-ready note is written first (after manifest and folder) and removed last for a complete copy; manifest always lists it. Tests: child process sends itself SIGTERM/SIGHUP (copy removed, rc 1); SIGKILL (leftover has the note, `check` rc 1, `delete` still works); order test.
2. `check` compares with the manifest when it sits next to the folder: missing / extra (any file kind) / changed file is a problem. Test with 4 damages.
3. `fill` refuses by default when placeholder names would stay (rc 1, nothing written); `--allow-placeholders` gives the old rc 3 copy. The test helper adds the flag unless a test sets `strict`.
4. `delete --no-manifest`: when a valid manifest exists the folder must hold nothing beyond it (also with --force-hash); the message no longer says "only the files this tool writes".
5. Values file must be owned by the current user.
6. `delete` unlinks the note then the marker last, whole removal shielded. Tests: order, and a stop half way leaves a marked folder that a re-run deletes.
7. Any `\uXXXX`, `\u{X}`, `\xXX` spelling that decodes to `$env` is refused in fill and counted in check; README notes the manifest-travel caveat.

## Tests against OLD code (old fill_flows.py plus a shim that ignores the new flag; new test file)
FAIL: test_a_kill_that_cannot_be_caught_leaves_a_copy_that_check_refuses
FAIL: test_check_compares_the_folder_with_its_manifest
FAIL: test_delete_no_manifest_keeps_a_file_the_manifest_does_not_list
FAIL: test_delete_stopped_half_way_leaves_a_marked_folder
FAIL: test_delete_takes_the_note_and_the_marker_last
FAIL: test_escaped_spellings_of_the_env_name_are_refused
FAIL: test_fill_refuses_by_default_when_a_placeholder_value_is_missing
FAIL: test_terminate_and_hangup_signals_clean_up_the_copy
FAIL: test_the_not_ready_note_goes_in_first_and_out_last
FAIL: test_values_file_must_be_yours
FAIL: test_fill_then_import_stops_when_placeholders_are_left
FAILED (failures=11)

Ran 128, FAILED (failures=11): the 10 new r3 tests and the changed placeholder test fail on old code. The 6 round-6 mutant-killer tests pass on old code by design (they test existing behaviour).

## Gates on the final tree (raw)
## unittest -I
----------------------------------------------------------------------
Ran 128 tests in 12.935s

OK
## pytest
........................................................                 [100%]
128 passed in 13.34s
## ruff check
All checks passed!
## ruff format --check
21 files already formatted
## bandit -ll -r
rc=0
	No issues identified.
	Total lines of code: 2571
## noqa count (fill_flows.py / test)
handover/flows-audit/fill_flows/fill_flows.py:1
handover/flows-audit/fill_flows/test_fill_flows.py:5

## 20 mutants re-run (seed 20261116 list, new code, scratch copies)
m1: killed (FAILED (failures=8)) line 893
m2: killed (FAILED (failures=2)) line 81
m3: killed (FAILED (failures=1)) line 677
m4: killed (FAILED (failures=2)) line 788
m5: SURVIVED (OK) line 196
m6: killed (FAILED (failures=1)) line 249
m7: killed (FAILED (failures=2)) line 660
m8: killed (FAILED (failures=1)) line 298
m9: killed (FAILED (failures=1)) line 116
m10: killed (FAILED (failures=1)) line 920
m11: killed (FAILED (failures=1)) line 964
m12: killed (FAILED (failures=1)) line 393
m13: killed (FAILED (failures=4)) line 496
m14: killed (FAILED (failures=43, errors=21)) line 623
m15: killed (FAILED (failures=60, errors=21)) line 244
m16: killed (FAILED (failures=35, errors=21)) line 518
m17: killed (FAILED (failures=1)) line 349
m18: killed (FAILED (failures=1)) line 755
m19: killed (FAILED (failures=44, errors=22)) line 344
m20: killed (FAILED (failures=3)) line 552
