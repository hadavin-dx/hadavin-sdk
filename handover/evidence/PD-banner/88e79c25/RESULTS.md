# Evidence: PD part 6 (mode banner and demo-only folder guard), batch 6, head 88e79c25986bcd94bcee15d33b26379e5b6439a5 (EVIDENCE RUNNER, no judgement)

Head checked out in a clean detached worktree (`git rev-parse HEAD` equals the sha, `git status` clean before and after the mutant tables). Previous head 3d7967cb. Raw logs: `/home/user/build/evidence-raw/pdbanner6-88e79c25/` (outside the repo). Own Postgres 16 on 127.0.0.1:55436, test database created as UTF8; stopped at the end. Not committed, not pushed.

## Not run / deviations (first)
- Two false starts, both stopped by me and rerun from scratch; only the rerun is recorded: (1) I passed the word `q8a1` as a command, `heavy.sh: q8a1: not found` (exit 127). The word is now given as `env tag=q8a1 ...`, so heavy.sh's name match gives priority 1 (the Q8a1 class, not the PD-banner class 2). (2) `uv sync --locked` without extras left out boto3 and psycopg, so collection failed (exit 2); I reran `uv sync --locked --all-extras --group test`. A stage_mutants run had started in that window; I killed it (my own processes only) and `git status` of the worktree was clean afterwards.
- Slot wait: none. The full run started the second after the launch (00:30:01 UTC = 06:00 IST), the stage table at 00:35:34 and the banner table at 00:36:24 UTC, ending 00:39:07 UTC. Other jobs held slots at the time (a policy plant run, a bind-mutants run); none blocked mine.
- Lint, bandit, scan_repo, gitleaks and the handover check (item 4) were run directly, not through heavy.sh (each takes seconds); they ran in a second worktree at the same sha so the mutant runs never saw them.
- Probes ran in that second worktree (same sha) for the same reason; fail-before in a third worktree at 3d7967cb. All three worktrees are removed.
- Probe 6b "unreadable file" as root reads the file (exit 1 only because it names the folder). The real unreadable cases ran as user `nobody` with the throwaway trees owned by `nobody` (as root-owned trees git refuses them: "git ls-files failed", exit 1; recorded in probe_6b_6f_2.txt).
- Not run: the page script with a real browser (only node with the fake page of tests/mode_banner_probe.js); no probe of a file vanishing from a real race (I removed it inside a patched `Path.open` and `Path.stat`); `.webp .ttf .otf .svg` with wrong first bytes are NOT a hit at this head (see 6f) - recorded as found.
- Skipped tests in the full run: 1 (expected 1). Reason: `tests/contracts/test_llm.py:95` "Stubber refuses a malformed Converse shape before the kind sees it".

## Results
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 Full suite | `heavy.sh env tag=q8a1 uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (HADAVIN_REQUIRE_NODE=1, own PG) | 0 | `10723 passed, 1 skipped, 28 deselected in 330.56s (0:05:30)` |
| 2 Stage mutants | `heavy.sh env tag=q8a1 python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` (37 lines `ok  KILLED`) |
| 3 Banner mutants | `heavy.sh env tag=q8a1 python tests/banner_mutants.py` | 0 | `200 of 200 good; problems: []` (191 `ok  KILLED`, 9 `ok  CRASH`: B5 B7 B13 B34 B43 B44 B52 B54 B62; full table in `banner_mutants.log`) |
| 4a ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 4b ruff format | `ruff format --check src tests demos tools` | 0 | `326 files already formatted` |
| 4c bandit | `bandit -q -r src demos tools -ll` | 0 | only `nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389` |
| 4d scan_repo | `python tools/scan_repo.py` | 0 | no output |
| 4e gitleaks | `gitleaks git --redact --no-banner --config .gitleaks.toml --log-opts refs/remotes/origin/main..HEAD` | 0 | `no leaks found` |
| 4f handover files | `check-no-handover-files.sh wip/cloud-pd-banner 88e79c25...` | 0 | no output |
| 5 Fail-before | 6 changed test files of 3d7967cb..HEAD (`banner_mutants.py`, `mode_banner_probe.js`, `test_banner_mutant_table.py`, `test_demo_only_guard.py`, `test_demo_only_guard_ci.py`, `test_mode_banner.py`) copied into a detached worktree of 3d7967cb, `PYTHONPATH=<old>/src` (import path checked: old src); pytest of the 4 test files | 1 | `23 failed, 172 passed in 10.21s` |

## Fail-before detail (item 5)
- Test functions with a new or changed `def` line in the delta: 27 (`added_tests.txt`); 1 old test function was removed or renamed (`test_the_copy_does_not_take_untracked_secret_files_but_keeps_tracked_ones`).
- 19 of the 27 FAIL on old code. 8 of the 27 PASS on old code: `test_a_failing_tone_attribute_alone_leaves_the_old_text_and_the_old_mode_together`, `test_a_planted_generic_expectation_or_a_row_that_changes_nothing_is_reported`, `test_a_tag_or_text_that_is_not_plain_text_is_not_painted_as_given`, `test_a_tracked_file_in_a_folder_that_cannot_be_entered_is_a_hit_not_a_skip`, `test_no_row_changes_nothing`, `test_no_row_has_a_generic_or_shortened_expectation`, `test_the_banner_is_never_more_lenient_than_the_tool_client_on_40_urls_and_20_hosts`, `test_the_type_of_a_system_base_url_is_text_and_another_type_reads_as_real`.
- 4 further tests (not in the added list; older, edited) also fail on old code: `test_a_text_file_renamed_to_a_binary_ending_is_read_and_a_real_binary_is_searched_as_bytes`, `test_ci_runs_the_copy_run_the_banner_mutants_and_checks_node_is_there` (the old tree has the old ci.yml), `test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once`, `test_the_settings_file_checks_the_size_cap_the_copy_exclusions_and_the_child_environment`. 23 failed ids are in `failbefore.log` (`failed_funcs.txt` lists the function names).

## Probe 6a: banner_for / banner_from_config, 45 made-up inputs (`probe_6a.txt`)
Exit 0; `VIOLATIONS 0 of 45`: no input gave a banner that says "made-up" while a real service is listed or declared. Every case printed an answer (OK or a named TypeError/ValueError); none crashed with another error type. Cases include: unknown mode (`dev`, empty, None), tool_specs not a mapping, host entries odd (`localhost\n`, padded, full-width, URL form, int, bare string), control characters in names (NUL, ESC, newline), empty lists, 10000-name lists (real and stand-in), unicode, full-width names, URL vs bare host, egress with empty string, 10000 outside hosts.

## Probe 6b: guard on made-up trees (`probe_6b_6f.txt`, `probe_6b_6f_2.txt`, `probe_6b_6f_3.txt`)
Matched text printed raw: none in any run (grep for the sentinels in every output: `no`).
| Tree | Exit | First line |
|---|---|---|
| clean | 0 | none |
| folder inside a product root | 1 | `src/demo_only: folder-inside-product-root` |
| product file names the folder | 1 | `names-demo-only-folder` |
| fake id in a string | 1 | `fake-record-id` |
| symlink | 1 | `symlink-in-product-root` (+ `copy-run-not-wired`) |
| BOM file | 1 | `names-demo-only-folder` |
| UTF-16 file | 1 | `names-demo-only-folder (as UTF-16 or UTF-32 text)` |
| UTF-32 file named .png | 1 | `ending-does-not-match-content`, `names-demo-only-folder (inside a binary file)` |
| compiled .pyc | 1 | `binary-in-product-root` |
| 9 MB file | 1 | `file-too-large` |
| pipe (fifo) | 1 | `unreadable-file (the entry cannot be inspected)` |
| unreadable file as root | 1 | reads it, `names-demo-only-folder` |
| unreadable file as nobody | 1 | `unreadable-file (it cannot be read)` |
| CRLF file | 1 | `src/g.py:2: names-demo-only-folder` |
| missing root | 1 | `product-root-missing` |
| full-width name | 1 | `names-demo-only-folder` |
| control character (ESC) in a path | 1 | printed as `src/a\x1bbdemo_only.txt: path-names-demo-only-folder` |
Extra (6f): folder 000 as nobody: exit 1 `unreadable-file (the entry cannot be inspected)`; top-level product root 000 as nobody: exit 1, same, for both files; tracked file deleted before the scan: exit 0; file removed between the size check and the open, and removed at the size check: exit 1 `unreadable-file (it cannot be read)`; GIT_DIR and GIT_WORK_TREE set to another checkout: exit 1 and the hit comes from the tree asked for (`src/bad.py:1`); untracked bad file is scanned (exit 1).

## Probe 6c: `--without-folder` (`probe_6c.txt`)
- c1 (folder present; 4 tests that need the folder gone, the package imported from the copy, no `SECRETENV_VAR`, no `HADAVIN_TEST_PG_DSN` although both were set in the caller): exit 0, `4 passed`.
- c2 same with GIT_DIR and GIT_WORK_TREE set to the head checkout: exit 0, `4 passed` (copy of the tree asked for).
- c3 two untracked files plus an untracked test: notice `3 file(s) are not added to git and are not in the copy`, names printed, exit 0.
- c4 a test that needs the folder: exit 1 (`FileNotFoundError`), `1 failed, 4 passed`.
- c5 `--without-folder-if-present` with no folder: exit 0. c8 `--require` with the folder missing: exit 2.
- c6 `--require` with `--without-folder`, and with `--without-folder-if-present`: argparse error, exit 2 (both). c7 pytest args without a copy flag (with and without `--require`): argparse error, exit 2 (both).
- c9 empty `product_packages`: exit 1 with the message. c10 a tracked symlink to a path outside the copy: copy run exit 0, `4 passed` (recorded as found; the plain scan lists a symlink in a product root as a hit).

## Probe 6f: picture and font files, marker, exempt files (`probe_6b_6f.txt`)
Wrong first bytes (text `NOTMAGIC ...`) in a product root: `.png .gif .jpg .woff .woff2 .ico` exit 1 `ending-does-not-match-content`; `.webp .ttf .otf .svg` exit 0 (no hit; these four endings have no first-bytes rule in `ENDING_MARKS` at this head, and the file is read as text). Genuine tiny files (`.png .gif .jpg .webp .woff .woff2 .ttf .otf .ico` and a small `.svg`): all exit 0.
Marker: non-empty file exit 1 `copy-run-marker-not-empty`; symlink exit 1 `...not-a-regular-file (a link ...)`; folder exit 1 (`a folder`) plus `path-names-demo-only-folder`; fifo exit 1 (`a unreadable cannot be the marker`); empty regular file exit 0.
Exempt file: symlink exit 1 `symlink-exempt-file`; regular exit 0; missing exit 1 `stale-exempt-entry`; 9 MB exit 1 `file-too-large`.

## Probe 6g: banner extras (`probe_6g.txt`)
- A tool module with no manifest host (spec without hosts, or no spec at all): tone real, real = `component tool-modules`. Module with a spec naming only localhost: tone demo, says made-up, real empty. Two modules, one without a host: tone real.
- `egress_hosts` as bare text or bytes: TypeError "is a str/bytes, not a list of hosts". A generator of an outside host: tone real; a generator of localhost: tone demo.
- Tool and agent names with control characters and an outside host: tone real, real = `component tool-hosts` (names not printed).
- `tool_specs` a generator: TypeError. Spec `hosts` a generator: TypeError naming the tool. `tool_modules` a generator: answered tone real, `component tool-modules` (no error).
- `NOTHING_CONNECTED` pinned, 3 pairs: (`anchor`, `none`) = no outside copy of the audit checkpoints is written; (`detector`, `regex`) = the built-in pattern detector, runs inside the process; (`signer`, `none`) = no signing service.

## Probe 6d: page script under node, 21 cases (`probe_6d.txt`)
`threw=""` and `htmlWrites=0` in all 21 (no markup written). Cases 01-11 (null, undefined, array, empty object, missing fields, script tags in text and name, made-up text with a real list, unknown tone, unknown mode, 601-character text): painted the UNCONFIRMED banner text. Failing tone/mode/append/all-writes, throwing getter/proxy/list, broken document, null element: no markup, 0 or 2 text lines (see file). Good banner control: painted `DEMO` and the made-up sentence as text.

## Probe 6e: duplicate search text (`probe_6e.txt`)
`rows: 200`, clean table on the real tree `[]`; copy unplanted `[]`. Plant 1 (search text of B1, B31, G90 duplicated in their files): `non_unique_rows` returned all three, `search text found 2 times`. Plant 2 (text not present): `search text found 0 times`. Plant 3 (label used twice): `label used twice`. Worktree clean afterwards.

## Cleanup
Postgres stopped (`server stopped`); three worktrees removed; no process of mine left (checked with `ps`); no planted mutation left (`git status` clean after the mutant tables).
