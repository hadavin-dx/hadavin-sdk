# Fix f3 round 9 (tests only; fill_flows.py untouched, sha256 checked equal to the backup)

Backup: scratchpad `bak-f3r9/` (fill_flows.py, test_fill_flows.py, fix-f3-r8.md). Source of the task: the 3 surviving mutants in evidence-f3-r7.md (#9, #12, #17) and the open link-parent case. Made-up data only; nothing ran in n8n.

## Confirmed against the CURRENT r8 code (170 tests) before writing
Each of the three mutants was applied to a COPY in /tmp and run with the r8 test file: all three still SURVIVED (rc 0, Ran 170, OK). So none was already killed by r8.

## New tests (class Round9, 4 tests; suite is now 174)
| mutant | test | what it pins |
|---|---|---|
| #9 `--tokens-only` lists placeholders | test_tokens_only_lists_no_placeholder_and_the_plain_check_does | on the real input flows the plain check lists "placeholder PG_CREDENTIAL_ID x2"; with the flag no ": placeholder " line, the "not checked" line and the token scan stay |
| #12 owner check on `--remove-others` dropped | test_remove_others_refuses_a_stray_file_owned_by_another_user | a stray file is reported as owned by another user (os.lstat faked through unittest.mock, no root tricks): delete refuses, file and folder stay; with the real owner it is taken. Run with and without `--no-manifest` |
| #17 JSON cap 32 to 64 MB | test_the_json_size_cap_is_32_mib_and_a_file_one_byte_over_is_refused | constant == 32 MiB; a sparse file (truncate, no real data) of cap+1 bytes is refused with "larger than 33554432 bytes"; exactly cap is not refused as too large |

## Mutants of the current code, applied to a copy in /tmp (live file never touched), Round9 tests
| mutant | result |
|---|---|
| #9 `if not tokens_only` -> `if True` | KILLED (rc 1, the #9 test) |
| #12 `or ls.st_uid != me` removed in `_stray_files` | KILLED (rc 1, the #12 test) |
| #17 MAX_JSON_BYTES 64 MiB | KILLED (rc 1, the #17 test) |
| extra: MAX_JSON_BYTES 32 MiB minus 1 | KILLED |
| extra: `_read_capped` `len(raw) > cap + 1` | KILLED |
Unmutated copy: Round9 rc 0, OK.

## Link-parent case (`--out` through a symlinked parent folder)
Decision from the current code: r8 already handles it BY DESIGN, not as a bug. `_check_parent_links` refuses only a link made by another user (README section "Folders that are links": "A link in the folders above it is accepted when you or root made it"). A link made by you is accepted, the real target is still checked for /mnt, git and cloud-synced folders, and files are written into the target. So `linkparent/o5` returning rc 0 and writing into the target is the documented behaviour. Test added that DOCUMENTS it: test_an_output_path_through_a_link_made_by_you_is_accepted_and_writes_to_its_target (fill rc 0, files appear in the target, check rc 0, delete rc 0 and target empty, link still there). The other-user case is already pinned by two older tests.
QUESTION FOR THE LEAD (no tool change made): should a parent link made by you stay accepted? Keeping it means a link someone tricked you into creating still sends the copy there, but it is your own link, the target is 0700 with 0600 files, and /tmp on macOS needs it. Refusing every parent link would break macOS /tmp. If you want it stricter, that is a change to fill_flows.py and then this test must change.

## Real bugs found in fill_flows.py
None. No input to list.

## Gates (each rc from the command itself, no pipe; FF_DEMO_DIR set to the demo folder, as in evidence-f3-r7.md 1b; repo pyproject.toml, line length 100)
- python3.11 -I -m unittest discover -s . -p test_fill_flows.py: rc 0, Ran 174, OK
- python3.12: rc 0, Ran 174, OK
- python3.13: rc 0, Ran 174, OK
- ruff check --config <repo pyproject.toml> .: rc 0 (All checks passed!)
- ruff format --check --config <repo pyproject.toml> .: rc 0 (28 files already formatted; the pyproject scope is wider than these two files)
- bandit -ll -r fill_flows.py test_fill_flows.py: rc 0, "No issues identified", Medium 0, High 0
- grep -c noqa/nosec/type: ignore: 0 in both files
