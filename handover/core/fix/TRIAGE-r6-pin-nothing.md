# TRIAGE of the 24 tests that PASS on the old frozen code (EV6 list)

Author: TRI (read-only analyst). Date: 2026-11-13 UTC.
Trees: r6 = /home/user/build/rr6/tree-TRI (copy of tree-EV6); old = /home/user/build/rr6/tree-TRI-old (clone of repo2 branch frozen2, with the r6 `tests/` folder copied over it, because the old branch has no copy of the new tests; the old tree's src, demo_only, scripts, tools and load_tools are untouched frozen2).
Runner: /home/user/build/rr6/out/TRI/run.sh (the recipe of the brief).

## What was NOT checked (read first)
- Windows or macOS behaviour (pipes opened in append mode, `os.replace` over a node): Linux only.
- I did not run the full suite; only the 24 ids, the 9 helper files, and the guard file with mutants.
- test_path_confinement and test_real_check_dry on the OLD tree: see section 4 for what finished (some tests wait on a pipe on old code; each run is capped at 450 s by run.sh).
- I did not read every one of the 969 changed tests; only the 24, and the diffs of the 9 helper files.

## 1. Reproduction
Old code + r6 tests, the 24 ids: `24 passed, 8 warnings in 6.41s`. r6 tree: `24 passed, 8 warnings in 6.46s`. (EV6 finding reproduced.)

## 2. Result in one line
None of the 24 is a PIN that is simply too weak. 16 are CONTROLs (the old code already did the right thing, or the test guards good input or a de-flake), 8 are GUARD-OF-GUARD (they test code that lives inside the test file). Two of the 8 guard tests do have real weak spots, fixed in `tri-tests.patch`.

## 3. Table

| id | asserts | class | why it passes on old | proposed fix | proof |
|---|---|---|---|---|---|
| test_crm_hubspot.py::test_read_back_list_search_lag_and_archive | search index lag of the fake: row not visible at 0.05 s, visible later, archive works. Diff vs frozen2: lag 0.6 s to 2.0 s, wait 5 s to 15 s | CONTROL (de-flake of a timing test; no behaviour fix) | the test never touched the changed code; only its time numbers changed | none (not a pin by design) | old and r6 both pass (section 1) |
| test_file_call_guard.py::test_at_least_forty_round_six_shapes_are_planted_and_all_are_found | the guard (a function defined in the same test file) finds each of >= 40 planted code shapes in a temp folder | GUARD-OF-GUARD | file does not exist in frozen2; the guard logic and the planted source are both inside the test file, so no old `src` can change the result | none for the logic; it is pinned by mutation (M3, M5, M7, M9 fail it) | mutation table below |
| ...::test_the_guard_finds_each_planted_shape_on_its_own | same for the base set of shapes | GUARD-OF-GUARD | same | none; pinned by M1, M3, M5, M7 | mutation table |
| ...::test_the_guard_leaves_alone_what_is_not_a_file_call | no false alarm on str.replace, dict.copy, os.path.join, json.loads, asyncio.run | GUARD-OF-GUARD | same | none; pinned by M6 | mutation table |
| ...::test_an_import_of_a_denied_module_needs_a_reason_per_file | each denied module import is found, accepted when listed with a reason, refused when the reason is blank | GUARD-OF-GUARD | same | none; pinned by M3 | mutation table |
| ...::test_a_listed_reason_that_matches_nothing_is_a_failure | a stale table entry is reported | GUARD-OF-GUARD | same | none; pinned by M2 | mutation table |
| ...::test_a_planted_call_in_every_guarded_folder_is_found | a call planted in each of the guarded folders is found | GUARD-OF-GUARD, WEAK SPOT: it loops over `GUARDED_FOLDERS` itself, so deleting a folder from that tuple removes its own check | same | add `assert GUARDED_FOLDERS == (the five folders written out)` (patch) | M10: before the fix only the sweep test failed; after the fix this test fails too |
| ...::test_a_tls_loader_is_refused_outside_the_two_demo_fakes | a TLS certificate loader outside the two demo fakes is refused | GUARD-OF-GUARD | same | none; pinned by M4 | mutation table |
| ...::test_the_listed_exceptions_are_each_used_once_and_have_a_reason | only `all(reason.strip())` over the two tables merged with `{**a, **b}` | GUARD-OF-GUARD, WEAK SPOT: the name says "used once" but nothing checks it; a repeated dict key silently keeps the last reason; the merge could hide one table's gap behind the other | same | replace body (patch): per table, non-empty reason and name, file exists, and the table text is read with `ast` and a repeated key fails | M11 (duplicate key): old test 9 passed, new test fails. On the OLD src tree the new test also fails (table names `src/lead_desk/regfile.py`, which old does not have), r6 tree passes |
| test_live_claude.py::test_a_bad_key_file_is_refused_before_the_ledger_and_the_call[UTF-16] | key file in UTF-16 is refused with a fixed text (no path, no content), no ledger line, no network call | CONTROL | old `_read_key` does `read_text(encoding="utf-8")`; UTF-16 raises UnicodeError, which old turns into `LiveTransport("the key file cannot be read") from None`. Same refusal as new | none | old and r6 pass; the 7 other shapes of the same test (two lines, space, tab, control character, ...) are the pins: `6 failed, 52 passed` on old for the file (section 4) |
| ...[empty] | empty key file refused | CONTROL | old: `strip()` gives "" and `len < LIVE_KEY_MIN_CHARS` gives `LiveTransport("the key file holds no key")`, before the ledger | none | same |
| test_portal_demo.py::test_burst_keeps_every_answer[cut_body-201] | a desk reply cut in the middle of a 201 body is still one answer with status 201 | CONTROL | the patch changed only the word for a failed request with no status (hang_up: "RemoteDisconnected" to "error"); a cut body still has its HTTP status, old code returned it too | none; the sibling parameter `hang_up-error` is the pin (it fails on old) | diff of the test: only the `hang_up` parameter changed |
| ...[cut_error_body-409] | same with a 409 | CONTROL | same | none | same |
| test_special_files_and_plain_text.py::test_bind_still_accepts_every_plain_spelling | `DESK_BIND` accepts 127.0.0.1, localhost, [::1], ... | CONTROL (good input still works, by name) | the new refusal of control characters leaves these alone; old accepted them | none | passes on both by design |
| ...::test_hubspot_base_url_plain_text_still_works | a plain https base URL is accepted | CONTROL | same | none | same |
| ...::test_a_number_with_a_trailing_line_end_stays_accepted_on_purpose | `DESK_PORT=12\n` accepted; `1\n2` and a full-width `12` refused | CONTROL | the "stays accepted" half is by design; the two refusals were already done by old `env_number` | none | passes on both |
| test_special_output_files.py::test_a_writer_refuses_a_pipe_a_link_to_a_pipe_and_a_folder_at_once[ledger-append-pipe] | `SpendLedger._append` on a pipe: answers within 5 s with the fixed `LiveCapReached` text, path not in text | CONTROL | Python's `open(path, "a+b")` seeks to the end when it opens; on a pipe that raises ESPIPE (an OSError) at once, and old `_append` already turns any OSError into the same fixed text. No wait on old, same message | none (no behavioural difference exists to pin); wiring is pinned by the sweep test (old `open(` is a hit) | probe run: old and r6 give the identical answer for all three kinds |
| ...[ledger-append-link-to-pipe] | same, link to pipe | CONTROL | same | none | same |
| ...[ledger-append-folder] | same, folder | CONTROL | `IsADirectoryError` is an OSError, same text | none | same |
| ...[ledger-lock-pipe] | `_FileLock` on a pipe: fixed text "lock file cannot be opened" | CONTROL | `open(..., "a+b")` raises at open (same reason as above), old catches OSError at the same line | none | same |
| ...[ledger-lock-link-to-pipe] | same | CONTROL | same | none | same |
| ...[ledger-lock-folder] | same | CONTROL | same | none | same |
| ...[stats-folder] | `write_stats` with a folder under the temporary name returns, creates nothing | CONTROL | old `write_text` raises `IsADirectoryError`; `except OSError: pass` already caught it. The pins are `stats-pipe` and `stats-link-to-pipe` (they fail on old: the child waits on the pipe) | none | probe: old `stats pipe` = child timed out (test would fail), `stats folder` = same answer as r6 |
| ...[trace-folder] | `Tracer.event` with a folder as the trace file: returns, `write_failures == 1` | CONTROL | old `open(path, "a")` raises `IsADirectoryError`, caught by the broad `except Exception` that counts a failure. `trace-pipe` and `trace-link-to-pipe` are the pins (old waits) | none | probe: same pattern |

### Mutation proof for the GUARD-OF-GUARD rows
Script: /home/user/build/rr6/out/TRI/mut_guard.py (copies tree-EV6's guard test, applies one change to the guard's own tables or logic in the tree-TRI copy, runs the file, restores). Each mutant is one made-up defect in the guard. All results are real runs:

| mutant | guard test(s) that failed |
|---|---|
| M1 `os.listdir` removed from HIT_QUALIFIED | test_the_guard_finds_each_planted_shape_on_its_own |
| M2 stale-entry check removed | test_a_listed_reason_that_matches_nothing_is_a_failure |
| M3 denied-import check removed | planted_shape, forty_shapes, denied_module (3 failed) |
| M4 TLS loader check removed | test_a_tls_loader_is_refused_outside_the_two_demo_fakes |
| M5 `__import__` removed from BARE_NAMES | planted_shape, forty_shapes |
| M6 `asyncio.run` made a hit (false alarm) | leaves_alone, and the sweep of the real code |
| M7 `getattr` removed from REACH_FUNCTIONS | sweep, planted_shape, forty_shapes |
| M8 one empty reason in ALLOWED_CALLS | sweep, exceptions_have_a_reason |
| M9 first 5 entries of PLANTED_R6 removed (list falls below 40) | forty_shapes |
| M10 folder `tools` removed from GUARDED_FOLDERS | sweep only (original). With the patch: sweep and planted_call_in_every_guarded_folder |
| M11 a repeated key in ALLOWED_CALLS | NONE (original: `9 passed`). With the patch: test_the_listed_exceptions_are_each_used_once_and_have_a_reason fails (`1 failed, 8 passed`) |

## 4. The 9 helper-changed files (see FINAL REPORT section of this file below for run lines)

Each file run on OLD (frozen2 src + r6 tests) and on r6, same recipe (run.sh). Logs: /home/user/build/rr6/out/TRI/h-<tree>-<file>.log.

| file | what the helper change is | old | r6 | does the helper hide a pin-nothing test? |
|---|---|---|---|---|
| test_except_clause_hierarchy | expected handler table entry for `Catcher.handle` split in two clauses | 1 failed, 51 passed (the Catcher.handle entry) | 52 passed | No: the table entry itself fails on old |
| test_live_claude | new table BAD_KEY_FILES (feeds the new test) | 6 failed, 52 passed | not run in full (the 24 ids pass) | No for the table; but 5 of its 9 shapes pass on old (UTF-16, empty, and ALSO "only a newline", "too short", "not UTF-8", which EV6 did not list): all five are refused by old code too (strip, length check, UnicodeError). CONTROL. Pins: two lines, space, tab, control character, BOM test |
| test_n8n_api_url | new import `EXIT_UNREACHABLE` | collection ERROR (ImportError) so the whole file fails on old | not run in full by me | Cannot hide anything: old cannot even import it. I did not check whether the unchanged tests of the file would pin behaviour on their own |
| test_path_confinement | `_KNOWN_SITES` renames `def main(` to `def _main(` (8 sites) | 10 failed, 368 passed (8 `_main` sites, 2 read_book tests) | 378 passed, 1 skipped | No: the renamed header makes the 8 site tests fail on old |
| test_real_check_dry | adds `import os` (new tests only) | 8 failed, 71 passed (239.88 s; the pipe test waits on old) | 79 passed (292 s) | No |
| test_reset_scripts | stub `python` for start_all.sh now answers `scripts/desk_setting.py ...` instead of `-c` | 25 failed, 34 passed (unchanged start_all tests fail on old too, because the stub no longer speaks old's interface) | 59 passed | Not hiding: unchanged tests fail on old. Not checked: whether the stub could make a start_all test pass for the wrong reason on r6 |
| test_scrub_n8n_export | child script times with `process_time` not `perf_counter` | 254 passed | 254 passed | It is a de-flake of a timing test (CPU time of the child). It cannot fail on old by design (CONTROL). Not checked: that the time limit still fails a slow pattern; the pin for the regex is in other tests |
| test_smtp_outbox | fixture asserts the catcher prints only the port (no host) | 54 passed, 13 errors (the 13 tests that use the fixture) | 67 passed | No: the fixture assertion is the pin |
| test_sonar_p2_feed_optional | fake reply `read(size)` accepts a size | 1 failed, 2 passed | 3 passed | No: the fake got more lenient, but the changed test body still fails on old |

## 5. Other things found
1. /dev/null in this sandbox is now a regular file. I caused it: my first probe called `write_stats` with the path /dev/null, and `write_stats` ends with `os.replace(tmp, path)`, which replaced the device node. Not repaired (an attempt was refused and the lead ordered me not to). The owner must decide.
2. `write_stats` (both old and r6) replaces any file kind at the TARGET name with a regular file (a pipe or a device node is removed from its place, no hang). The r6 tests only put the special file at the `.tmp` name. Verified on a tmp-made FIFO: after the call it is a regular file. Not a hang, so left alone; a decision for the lead.
3. An untracked stray file named `a<newline>b` (12 bytes, content `{ "x": 1 }`) sits in the root of tree-EV6 (created 20:49). A test wrote to a relative path with the repo as the working folder. I did not trace which test.
4. Two guard tests were weak (patch).
