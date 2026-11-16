# HUNKS: every hunk of core-fix-v2.patch against the frozen tree (tree hash 49d3c85938fe5323a3378a49195d3b8da434b3ca)

Source: /home/user/build/rr6/out/CF2/core-fix-v2.patch (sha256 df03b49f8609bf6433d73db5dec4beda9d42d58b67f4c7e08d1d99e510211264), 51 files, 123 hunks (a new file counts as one hunk).
Method: `git apply --reject` on a copy of the frozen tree (repo2 untouched), then every rejected hunk and every file that does not exist in the frozen tree read by hand against the frozen text. The rejected hunks are kept in `work/rej/` (one file per source file).
Classes: (a) applied cleanly; (b) rejected because the frozen series changed the same lines: frozen wording and behaviour kept, only what our fix adds was re-added; (c) depends on code that exists only in the real-run patches: ported in a smaller form, or dropped and moved to the "on top" list (DEPENDS.md).
Counts (corrected): the apply log gave 87 hunks applied cleanly (class a) and 36 rejected or missing. Of those 36: 16 were rejected in files that exist in the frozen tree and are listed in the (b) table; the rest are the 14 rejected hunks of run_live_check.py / run_real_check.py (class c, ported, see the (c) block) and 6 hunks of 3 files that do not exist in the frozen tree (class c, dropped). I did not re-derive an exact per-class number beyond this; the per-file rows below are the record.

## (b) rejected, resolved by hand (frozen text kept)
| file | hunk | class | decision | why |
|---|---|---|---|---|
| README.md | 1 (reset-script exit codes) | b | re-added to the frozen bullet list: `* 4:` now also says "or a `DESK_` setting is wrong (the same one line the desk prints ...)" | the frozen README turned the sentence into a bullet list; same fact, frozen layout |
| demo_only/fake_model_server.py | 1 (imports) | b | `import argparse` removed, `open_output/open_regular` and `RefusingParser` imports added next to the frozen `tools.pathconfine` import | frozen already has the path check block, so the import lines differ |
| demo_only/fake_model_server.py | 3 (main) | b | KEPT the frozen `confine`/`confine_existing` block (it already refuses a pipe named for --call-log/--control-file, with its own line on stderr); then our block opens --call-log with `open_output` and reads the key with `open_regular` | frozen path check goes first; our check is the second layer and the only one that covers a key file that is a pipe |
| load_tools/catcher.py, check_invariants.py, load_driver.py | 1 each (one import line) | b | `from tools.refusing_args import RefusingParser` added after the frozen import fallback block | the frozen import block has longer comments |
| scripts/n8n_api.py | 1 (import) | b | `load_json_file, open_regular` import added after the frozen `lead_desk.envnum` line | context only |
| scripts/n8n_api.py | 4 (`import` command) | b | KEPT the frozen `PathRefused` handler and its long rule text; `json.loads(...read_text())` replaced by `load_json_file(...)`; the fixed text "cannot read a workflow from the FILE given" (no typed path) is used in the generic handler only | frozen added a separate `except PathRefused`; the typed path is still never printed in the generic handler |
| scripts/reset_check.py | 1 (docstring) | b | exit 2 added to the frozen docstring; "on a refusal (3 or 4)" changed to "(2, 3 or 4)" | frozen docstring has an extra sentence |
| scripts/start_all.ps1 | 1 | b | `Get-DeskSetting` function and the guarded `New-Item` re-added over the frozen line (the frozen line 10 has the extra `-not [string]::IsNullOrEmpty` test, kept) | context only |
| src/lead_desk/constants.py | 1 (`LIVE_EFFORTS`) | b | tuple added after `LIVE_API_VERSION` | the frozen comment line above differs ("the provider's address") |
| src/lead_desk/crm_hubspot.py | 1 | b | the local `SECRET_FILE_MAX_BYTES = 4096` removed (the constant now comes from constants.py, as the applied hunk imports it) | frozen comment lines differ |
| src/lead_desk/desk.py | 1 (`book_problem`) | b | the two checks (folder part is a file; existing path is not a regular file) added; KEPT frozen docstring wording ("private in-memory database") and appended our two sentences | frozen docstring wording differs |
| src/lead_desk/live_claude.py | 1 (`_read_key`) | b | bounded read through `open_regular`, refusal when the file is larger than `SECRET_FILE_MAX_BYTES` | context only |
| tools/scrub_n8n_export.py | 1 (imports) | b | KEPT the frozen comment about "another project's `tools`" (a frozen test pins that sentence) and replaced the try/except import by the `src` + repository path insert (needed to import `lead_desk.regfile`; the frozen test that starts the script without PYTHONPATH still passes) | frozen text pinned by `test_the_foreign_tools_limit_is_stated_where_the_import_is` |
| tools/scrub_n8n_export.py | 2 (`main`) | b | refusals go to STANDARD ERROR like the frozen `refused: ...` lines of this function (v2 printed to standard output) | frozen behaviour kept |

(The (b) table covers 16 rejected hunks of 13 files; the ported hunks of the two big scripts are in the (c) block.)

## (c) real-run dependent
The frozen `scripts/run_live_check.py` (225 lines) and `scripts/run_real_check.py` (1117 lines) are the version from before the real-run patches (no `scripts/precheck.py`, no `scripts/terminal_guard.py`, no `--assume-yes` on the live script, no refusing parser in the live script). Our hunks there were written on top of the real-run version (1448 lines).
| file | hunk | class | decision | why |
|---|---|---|---|---|
| scripts/run_live_check.py | 1,2,3,4 (imports, `RefusingParser`/`refusal` moved out) | c, ported smaller | the frozen script gets `RefusingParser`, `refusal` from `tools/refusing_args.py`, `sys.path.insert(0, REPO)`; typed text no longer echoed: `ArgumentTypeError` texts fixed ("is not a number", "needs ID=IN_PRICE,OUT_PRICE"), the `ap.error(...)` for leads/runs is now one `refused:` line | the class (argparse echoes a typed key) holds on the frozen script too |
| scripts/run_live_check.py | 5,6 (`_price_date_problem`, `option_problem`) | c, ported smaller | ported WITHOUT the `--leads/--runs` range, `--base-url` required and `--assume-yes` checks (those flags/rules exist only in the real-run version): price date shape/real day/floor/future, empty values, effort word, same model twice | needs `LIVE_EFFORTS` (constants hunk, ported) |
| scripts/run_live_check.py | 7 (call of `option_problem` in main) | c, ported smaller | called right after the leads/runs check, before anything is read or asked | |
| scripts/run_live_check.py | 8 (ledger refusal line without the class name) | a | applied cleanly | |
| scripts/run_real_check.py | 1 (`from precheck import ... folder_cannot_be_made`) | c, ported smaller | frozen has no precheck: `folder_cannot_be_made` defined in the script itself (same body) | |
| scripts/run_real_check.py | 2,3 (imports regfile, refusing_args, `DRY_PORT_COUNT`) | b/c | added | |
| scripts/run_real_check.py | 4 (`load_env` read) | c, ported | `read_regular_text`; `FileRefused` turned into the same fixed ValueError text | |
| scripts/run_real_check.py | 5 (`read_counter_files`) | a | applied cleanly | |
| scripts/run_real_check.py | 6,7,8 (`RefusingParser`, `--dry-smtp-script` default None) | a | applied cleanly | |
| scripts/run_real_check.py | 9 (`option_problem`: dry port base range, dry smtp script) | c, ported | added; called at the start of `_run` (frozen has no separate start step) | the frozen `--assume-yes` line ("refused: --assume-yes is only for ...") is kept as it is |
| scripts/run_real_check.py | 10 (`DryFakes(... or "ok")`) | b | applied by hand | |
| scripts/run_real_check.py | 11 (`SettingProblem` for a run folder that cannot be made) | c, ported smaller | frozen has no `SettingProblem`: one `refused: DESK_DB_PATH: the run folder cannot be made here ...` line and exit 2 before the start question | |
| scripts/run_real_check.py | 12 (`mkdir` guard after the question) | a | applied cleanly | |
| scripts/precheck.py (2 hunks) | all | c, DROPPED (file missing) | moved to the on-top list | file is created by the real-run patch |
| tests/test_core_key_readers.py (2 hunks) | all | c, DROPPED (file missing) | moved to the on-top list | file is created by the real-run patch |
| tests/test_survivor_r20_config_read.py (2 hunks) | all | c, DROPPED (file missing) | moved to the on-top list | file is created by the real-run patch |

## (a) applied cleanly (87 hunks in 33 files)
demo_only/burst.py (3), demo_only/fake_smtp_tls.py (1), demo_only/fakes_server.py (3), demo_only/fake_model_server.py (1 of 3), load_tools/* (the other 9 hunks), scripts/crash_desk.py (1), scripts/feed.py (4), scripts/hubspot_probe.py (4), scripts/n8n_api.py (2 of 4), scripts/reset.ps1 (1), scripts/reset.sh (1), scripts/reset_check.py (2 of 3), scripts/start_all.ps1 (1 of 2), scripts/start_all.sh (2), src/lead_desk/config.py (4), constants.py (1 of 2), crm_hubspot.py (2 of 3), desk.py (2 of 3), envnum.py (2), hooks.py (2), live_claude.py (4 of 5), lockfile.py (2), run_stats.py (1), server.py (1), smtp_provider.py (5), trace.py (3), tools/pathconfine.py (4), tools/scrub_n8n_export.py (0 of 2), tests/test_lead_step_route.py (1), test_n8n_api_url.py (2), test_reset_scripts.py (1), test_sonar_p2_feed_optional.py (2).
New files created by the patch (one hunk each, applied): scripts/desk_setting.py, scripts/refusals.py, src/lead_desk/regfile.py, tools/refusing_args.py and the seven new test files (see TESTS below).

## TESTS (decision per new test file)
| file | decision |
|---|---|
| tests/test_cli_refusals.py | KEPT, adapted (see below) |
| tests/test_file_reader_refusals.py | KEPT as it is |
| tests/test_script_refusals_feed.py | KEPT as it is |
| tests/test_special_files_and_plain_text.py | KEPT, adapted: the three key-reader helpers are written inline (the helper file `test_core_key_readers.py` does not exist in the frozen tree) |
| tests/test_special_output_files.py | KEPT, adapted: for `--call-log` on a pipe the frozen path check answers first, with its own line (`refused: --call-log: is not a regular file ...`); the test accepts that line for `--call-log` and our line for `--key-file` |
| tests/test_wrapper_setting_refusals.py | KEPT as it is |
| tests/test_book_folder_refusals.py | KEPT as it is |
test_cli_refusals.py changes forced by the frozen differences: `--assume-yes` removed from the live-script cases (the frozen live script has no such flag); the control test "a good date ... reaches the no-terminal refusal" DROPPED (the frozen live script has no terminal guard: it would reach `input()` and fail with EOFError; that belongs to the real-run patch); the test of `precheck` helpers with `None` DROPPED (no precheck); `precheck.folder_cannot_be_made` replaced by `rrc.folder_cannot_be_made`; the `stdin_is_terminal` stand-in removed (frozen run_real_check has none); the ledger test answers the start question with a stand-in `input`. The original v2 text is kept in `work/test_cli_refusals.v2.py`.
