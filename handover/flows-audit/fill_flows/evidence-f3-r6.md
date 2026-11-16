# evidence-f3-r6 (EVIDENCE RUNNER, 2026-11-16 ~10:20-10:35 UTC; raw output, no judgement)

Tree under test: HEAD d31ee5a25 (fill_flows.py 1039 lines, test_fill_flows.py 1972 lines). The folder was clean in git at the start (`git status --short handover/flows-audit/fill_flows` empty). Other dirty paths in the repo belong to other work (handover/flows-audit/patches/*, lanes7/); not touched.

## 1. What failed or did not match the claims (first)
- Old-code proof: claim "11 of 128 new tests fail on old code" HOLDS only with the shim (11 fail, list in section 4). Without the shim, old code fails 104 of 128 (the old tool does not know `--allow-placeholders`).
- Round-6 code was already committed by the automatic board commits before this run (commit 90fbdec54 and later contain it). The last commit WITHOUT the round-6 code is bf1acc701 (893 lines, no SIGTERM, no `--allow-placeholders`); that is the "old code" used.
- Mutation, seed 20261116 list, new code: 19 killed, 1 survived (m5, a comment text; same as the claim 19 of 20).
- Mutation, my fresh 20 (seed 20261117) on the new paths: **5 SURVIVED, 15 killed** (section 5). Survivors: n6 (clean-up unlink order), n7 and n16 (`_sigint_blocked` replaced by a no-op context), n15 (`except _Stopped` in main replaced by another exception), n18 (`ph_left > 1` instead of `ph_left`, i.e. one left-over placeholder name no longer refused in strict mode).
- Observed behaviour, not a test failure: after a SIGKILL mid-fill the left-over folder holds only `.fill_flows-output` and `NOT-READY-DO-NOT-IMPORT.txt` (no .json yet); `check` on it prints "refused: no .json files in the folder (nothing was checked)" rc 1 (it refuses, but does not name the not-ready note). `delete` removes it, rc 0.
- Not done: Python 3.9 / 3.10 (not installed; only 3.11, 3.12, 3.13 present), macOS, real n8n. SIGTERM/SIGHUP were sent through a wrapper that pauses after the 3rd file write (patches only `_write_new` with a sleep, then calls the real `main`); the tool CLI itself has no pause.
- Unexplained failure hunt: no failure in 10 full runs (section 7).

## 2. Gates (raw)
unittest, `python3 -I -m unittest` in the folder (128 tests each): python3.11 OK 12.8s; python3.12 OK 13.3s; python3.13 OK 12.9s.
`uv run --all-extras --group test pytest -q handover/flows-audit/fill_flows`: `128 passed in 13.41s`.
`ruff check` on the folder: `All checks passed!` rc 0. `ruff format --check`: `22 files already formatted` rc 0.
`bandit -ll -r`: `No issues identified.`, lines of code 2571, High 0, Medium 0, Low 6 (not shown at -ll), rc 0.
grep noqa/nosec/type: ignore: fill_flows.py 1 (line 1033 `noqa: BLE001`); test_fill_flows.py 5 lines (78 S603, 794 S311, 1637 S603, 1638 S607, 1939 S603); nosec 0; `type: ignore` 0. Matches the claim 1 + 5.

## 3. (note) old code source
`git show bf1acc701:handover/flows-audit/fill_flows/fill_flows.py` (893 lines). Tests need `FF_DEMO_DIR=/home/user/hadavin-sdk/handover/demo` when run from a copy outside the repo.

## 4. New test file against old code
No shim: Ran 128, FAILED (failures=68, errors=36) = 104 not passing.
With shim (old file + `main()` drops `--allow-placeholders` from argv): Ran 128, FAILED (failures=11). Failing tests:
- test_a_kill_that_cannot_be_caught_leaves_a_copy_that_check_refuses
- test_check_compares_the_folder_with_its_manifest
- test_delete_no_manifest_keeps_a_file_the_manifest_does_not_list
- test_delete_stopped_half_way_leaves_a_marked_folder
- test_delete_takes_the_note_and_the_marker_last
- test_escaped_spellings_of_the_env_name_are_refused
- test_fill_refuses_by_default_when_a_placeholder_value_is_missing
- test_fill_then_import_stops_when_placeholders_are_left
- test_terminate_and_hangup_signals_clean_up_the_copy
- test_the_not_ready_note_goes_in_first_and_out_last
- test_values_file_must_be_yours
Same 11 as in fix-f3-r6.md.

## 5. Mutants (scratch copies, python3.13 -I -m unittest, FF_DEMO_DIR set; 4 at a time)
### 5a. The 20 mutants of evidence-f3-r5.md (seed 20261116), mapped to the new line numbers by text and occurrence
| m | line | change | result |
|---|---|---|---|
| m1 | 893 | `dfd = -1` -> `dfd = -0` | killed |
| m2 | 81 | `ascii(str(x))[1:-1]` -> `[0:-1]` | killed |
| m3 | 677 | "Linux or macOS disk" -> "Linux and macOS disk" | killed |
| m4 | 788 | `ph.get(name, 0) + 1` -> `+ 2` | killed |
| m5 | 196 | comment "in case" -> "not in case" | SURVIVED (comment only) |
| m6 | 249 | message "at its start or end" -> "start and end" | killed |
| m7 | 660 | `dfd = -1` -> `dfd = -0` | killed |
| m8 | 298 | `"not filled)"` -> `" filled)"` | killed |
| m9 | 116 | `split(b"\0", 1)` -> `split(b"\0", 0)` | killed |
| m10 | 920 | manifest "is not owned by you" -> "is  owned by you" | killed |
| m11 | 964 | file "not owned by you" -> " owned by you" | killed |
| m12 | 393 | "sits in a" -> "sits not in a" | killed |
| m13 | 496 | `return True` -> `return False` | killed |
| m14 | 623 | `shape(new) != before` -> `==` | killed |
| m15 | 244 | `endswith("_MS") and not DIGITS` -> `and DIGITS` | killed |
| m16 | 518 | `0o600` -> `0o644` | killed |
| m17 | 349 | `slash = True` -> `slash = False` | killed |
| m18 | 755 | `bad += 1` -> `bad += 0` (NOT-READY note line in check area) | killed |
| m19 | 344 | `elif ch in "'\"\`":` -> `not in` | killed |
| m20 | 552 | `st is not None and` -> `st is None and` | killed |
Lines equal those in fix-f3-r6.md. 19 killed, 1 survived (m5).

### 5b. Fresh 20, seed 20261117 (random.sample of a pool of 35 single-line mutants aimed at the new code; pool in scratchpad/mut/run.py)
| n | line | change | result |
|---|---|---|---|
| n1 | 149 | signal handler `raise _Stopped(signum)` -> `return` | killed |
| n2 | 153 | handled signals `("SIGTERM","SIGHUP")` -> `("SIGTERM",)` | killed |
| n3 | 274 | ESCAPE regex `\x` alternative -> `\q` | killed |
| n4 | 389 | `"$env" in _unescaped(s)` -> `in s` (\u refusal) | killed |
| n5 | 685 | `if not ph_left:` -> `if ph_left:` (note removed last) | killed |
| n6 | 691 | clean-up `reversed(created)` -> `created` | **SURVIVED** |
| n7 | 667 | `with _sigint_blocked()` (mkdir step) -> `nullcontext()` | **SURVIVED** |
| n8 | 728 | check: no manifest `return 0` -> `return 1` | killed |
| n9 | 740 | manifest compare: `present - set(files)` -> `present & set(files)` | killed |
| n10 | 745 | `n != NOT_READY_NAME` -> `==` | killed |
| n11 | 750 | `sha256 == h` -> `!= h` | killed |
| n12 | 949 | delete folder owner check `!= me` -> `== me` | killed |
| n13 | 974 | delete order (note and marker last) swapped | killed |
| n14 | 921 | `if no_manifest:` -> `if not no_manifest:` | killed |
| n15 | 1024 | `except _Stopped:` -> `except ZeroDivisionError:` | **SURVIVED** |
| n16 | 975 | delete `with _sigint_blocked()` -> `nullcontext()` | **SURVIVED** |
| n17 | 687 | `os.unlink(NOT_READY_NAME, ...)` -> `pass` | killed |
| n18 | 639 | `if ph_left and` -> `if ph_left > 1 and` | **SURVIVED** |
| n19 | 714 | `return EXIT_INCOMPLETE` -> `return EXIT_OK` | killed |
| n20 | 793 | `not tokens_only and ...NOT_READY` -> `tokens_only and ...` | killed |
Totals: 15 killed, 5 survived. Not judged here whether any is equivalent.

## 6. End to end, made-up canary values, copy of demo/n8n-flows-real-v5 under /tmp (outside the repo), file hash of the tool copy equals the repo file (15eead94cb65dd45...)
Run twice with the same script: as root (uid 0) and as nobody (`runuser -u nobody`, uid 65534). Python 3.13.18. Transcripts: scratchpad/e2e-root.txt and e2e-nobody.txt; return codes and folder states were identical for both users.
| step | result (both users) |
|---|---|
| A fill strict, 6 flow keys, no placeholder values | rc 1, "refused: 23 placeholder name(s) would be left ... nothing written"; work dir unchanged (no out, no manifest) |
| B fill --allow-placeholders | rc 3, 4 files + `.fill_flows-output` + `NOT-READY-DO-NOT-IMPORT.txt`, manifest `out.manifest.json` next to it |
| C check on B copy | rc 1, "24 problem(s)" (23 placeholder uses + the note) |
| D delete | rc 0, folder and manifest gone |
| E fill strict, all 12 values | rc 0, "no placeholders left" |
| F check | rc 0, "4 files, 0 problem(s)" |
| G delete | rc 0, folder and manifest gone |
| H SIGTERM during fill (paused after 3rd file; folder held marker/note) | rc 1, "stopped by a signal; the run's own clean-up was done"; folder and manifest both gone |
| H SIGHUP, same | rc 1, same message; folder and manifest gone |
| H SIGKILL, same | rc -9; left-over folder (`.fill_flows-output`, note) and manifest stay; `check` rc 1 "no .json files in the folder"; `delete` rc 0 "deleted 0 files, the folder and the manifest"; work dir clean afterwards |
Canary scan of everything the script printed (stdout and stderr of every step, 12 values, plus the stem "canary-"): 0 hits for both users. Files the tool wrote were not scanned for canaries (they legitimately hold filled values). Repo `git status` for the fill_flows folder: clean before this file was added; no repo path was used as an output place. Temporary /tmp/e2e-* dirs removed.
"Run as nobody" needed no change; as root the tool did not refuse anything either (no ownership problem seen).

## 7. Unexplained-failure hunt: 5 full runs, twice
`python3 -I -m unittest` (3.13): run1..5 each rc 0, Ran 128, OK (13.3s, 13.8s, 13.6s, 14.4s, 13.8s).
`uv run ... pytest -q`: runs 1..5 each rc 0, `128 passed` (13.7s, 13.6s, 13.3s, 13.2s, 13.3s).
No failure seen in 10 runs; load on the machine was low (one run at a time; the mutation runs were not running at the same time). The earlier one-off failure ("unrecognized arguments: --allow-placeholders" at non-matching line numbers) did not recur.
Raw outputs: scratchpad/rep1..5.txt, prep1..5.txt.
