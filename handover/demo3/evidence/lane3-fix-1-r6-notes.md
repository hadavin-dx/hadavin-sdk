# lane3-fix-1 round 6 (builder B1f): notes
Written 2026-11-13 (UTC; IST = UTC + 5:30; checkpoints in raw/progress-B1f.txt). Worktree /home/user/work/b1f-base = public main f3c39cf8 + lane3-fix-1-r5.patch + round-6 changes, files staged (`git add -A`), nothing committed or pushed. Patch: evidence/lane3-fix-1-r6.patch (full diff from f3c39cf8, so it REPLACES r5). Documentation, comments and tests only: no behaviour change (the only `src/` and `demo_only/` edits are docstring and comment words).

## Failures and unproven first
* FULL SUITE: see "Full suite" at the end. If that section says not finished, it was not.
* The lane3-fix-2 patches do NOT apply on top of r6 (see "git apply --check"): they change the same "Exit code 1" sub-bullet in docs/limits.md, the same exit-codes line in contract.md and a line in docs/why-this-code.md. My new wording is true on the stack where fix-2 turns a data folder that cannot be made into exit code 4 (see M1), but the fix-2 patch text itself has to be re-cut on top of r6 by whoever owns fix-2 (take its extra clause "it says so first, because a bad key file is reported only once they are reachable" into my sentence). I did not re-cut it (not in my brief).
* The Windows lines (PowerShell) are still "not tried"; n8n is not installed here; the new `Get-Process -Id` wording is an idea, not run.
* "n8n may offer a free licence key for registered community users" is the reviewer's wording (m1) and is marked "not checked on the screen" in the text; I did not check it.
* Not run by design: ruff, ruff format, mypy, bandit, gitleaks (CI only). I wrote for them (no unused import: checked by a small `ast` script, 0 found; no `noqa`, no `type: ignore`; no added Python line over 120; one pre-existing `schema.sql` comment line that was over 120 is now 119), but the new test code is NOT checked for ruff format or mypy types. The 4 gitleaks-dependent hygiene tests skip here.
* The new traceback test (`test_the_causes_of_a_traceback_named_in_limits_end_in_exit_code_1`) skips its first case where the desk's code is installed as a package (then a missing PYTHONPATH is not a fault); here the package is not installed, so all three cases ran.
* My slips: (1) the first draft of the exit-code 1 sentence repeated the reviewer's suggestion "A bad DESK_* value is refused with exit code 4, not a traceback". I tried it: on f3c39cf8 a `DESK_DB_PATH` inside a file ends in a traceback (exit 1), so that sentence is false on the base. I replaced it (see M1). (2) My first sweep for "request number" in contract.md missed 2 lines (18 and 249); the new test found them.

## Facts I checked myself (command or file; outputs in raw/ where kept)
| claim | how verified |
|---|---|
| A traceback with exit 1 when PYTHONPATH is not set | real run: `python -m lead_desk.server` with no PYTHONPATH from a folder without the code: "No module named 'lead_desk'", exit 1 |
| A traceback with exit 1 when `demo_only/` is missing | real run: copy of `src` with no `demo_only`, demo servers running: `RuntimeError: ... the folder demo_only is missing`, exit 1 (loader.py:95; same code on the fix-2 stack, its loader diff does not touch it) |
| A traceback with exit 1 when a fixed value is edited | real run: `MAX_CONNECTIONS: Final = 2` in a copy: `ValueError: MAX_CONNECTIONS must be a whole number from 8 to 4096, got 2`, exit 1 |
| On f3c39cf8 a `DESK_DB_PATH` inside a file (and one that is a folder) is NOT exit 4 | real run: `NotADirectoryError`, exit 1 (path inside a file); folder: the desk got as far as the demo servers check first. This is why the reviewer's "a bad DESK_* value gives exit 4, not a traceback" is false on the base; fix-2 makes it exit 4 |
| `server.py` main catches only the named refusals | read server.py 1125-1190 (FakesUnreachable, SettingRefused, DeskSettingRefused, lock errors); `mkdir` at line 1140 unguarded on the base; fix-2-r3 patch guards it (exit 4) |
| STATUS holds words for a request with no HTTP answer | demo_only/burst.py `_post_once`: `"refused"` or `type(e.reason).__name__` or `type(e).__name__`; `main` prints every key of the Counter |
| contract.md "Host and Origin gate" names n8n in Docker, `DESK_BIND` and `DESK_ALLOWED_HOSTS` | read contract.md 102-110 (line 110); the new test reads it |
| The desk hints and the "could not store" message are texts shown on portal screens | read desk.py 203-211, portal_api.py 653-656, schema.sql 132 |

## Table: finding | fixed how | pinned by (test in tests/test_docs_claims_lane3.py)
| # | fixed how | pinned by |
|---|---|---|
| M1 | limits.md "Exit code 1": a traceback "means a program fault or a problem with this computer that the desk does not check for". Causes TRIED on 2026-11-13: PYTHONPATH not set, `demo_only/` missing, an edited fixed value in constants.py. "A `DESK_*` value that no check listed under exit code 4 covers is not promised to be refused with code 4 and may also end in a traceback. A `DESK_*` value that a check listed under exit code 4 rejects gives code 4 ...". The "data folder cannot be created" cause is NOT listed on purpose (see below). Sibling fixed: contract.md "Exit codes" line said "the sender cannot be reached ... (a constant that is out of range)": now the demo servers and a pointer to limits.md | test_exit_code_1_uses_the_words_the_desk_prints (regexes for the three causes, the DESK_* sentence, absence of "never caused by" and of "the data folder cannot be created", contract line); NEW test_the_causes_of_a_traceback_named_in_limits_end_in_exit_code_1 runs the three causes for real |
| M1 true on both stacks | On f3c39cf8 an uncreatable data folder is a traceback (exit 1); with fix-2 it is exit 4 (its patch, step 4 "folder cannot be made"). So that cause is left out of the list. Every listed cause is a traceback on both. The `DESK_*` sentence says "not promised", which is true on the base and on the stack. Two variants were therefore NOT needed | same tests; the stack was checked by reading the fix-2-r3 patch (loader and server hunks), not by running the stack |
| M2 | n8n-recipe "n8n in Docker": "Not tried here. On the default Docker network (called bridge) ... do not reach the desk ... not reachable from a container by the computer's own address. Whether Docker's host networking, or Docker's own host name for the computer, makes it work was not tried." Keeps the licence sentence and `DESK_ALLOWED_HOSTS` sentence; adds `DESK_BIND` and a pointer to contract.md "Host and Origin gate" (which describes a Docker caller setting both) | test_the_recipe_tells_one_true_story_about_docker (new regexes; "at all" and "even with edited files" must be absent; premise: contract.md gate section names n8n in Docker, DESK_BIND, DESK_ALLOWED_HOSTS) |
| m1 | licence key: "n8n may also offer a licence key (for paid plans, or a free one for registered community users; this was not checked on the screen). The runs used the free community licence; whether the workflows work without a key was not checked. Use no key from a paid plan."; "Before you start" now says "Use no key from a paid plan (Step A)" | test_the_recipe_import_steps_match_the_script |
| m2 | "no real e-mail address in the workflows or their test data (the n8n owner account needs your own e-mail address: Step A)" | same test |
| m3 | unused `import os` removed | grep + `ast` unused-import script: 0 |
| m4 | no `http://` and no port literal left in the test file: addresses come from `lead_desk.urls.desk_origin`, `DESK_SCHEME`; ports from `Config()` (8765, 8766 defaults) and from the default address in scripts/n8n_api.py (the n8n port) | `grep` of the file: 0 literal `http://`, 0 of the three port numbers; hygiene tests run in the full suite |
| m5 | renamed to `test_premise_the_desk_and_the_demo_server_answer_404_for_the_root_address`, docstring says it reads no document; the README sentence is pinned by test_readme_port_check_explains_000_and_404. Fails-before for it was only ever possible against the program, so it passes on r5 by design (stated) | rename |
| m6 | `_key_file_result` saves and restores `sys.path` and unloads the modules the script's folder brought in (the script and its helper), instead of `monkeypatch.syspath_prepend` (which put the path back only at the end of the test) | NEW test_reading_a_key_file_leaves_the_search_path_and_loaded_modules_as_they_were (fails with the r5 helper: proven) |
| m7 | README Windows idea: "shows the process id that holds the port, and `Get-Process -Id <that id>` names that process"; still "not tried" | test_readme_port_check_explains_000_and_404 |
| m8 | README step 3 remedy: "run `bash scripts/reset.sh` here (it also deletes the desk's records and logs), in the project folder ..." | same test (+ premise: the README's own reset line says DELETES) |
| m9 | limits burst step 3: "a request that got no HTTP answer at all is counted under a word instead of a number: `refused` ... or the name of the Python error type the script received ..., so a `STATUS` line can hold words as well as numbers" | test_the_burst_steps_explain_each_term_and_both_systems (+ premise on burst.py) |
| m10 | "request number" -> "request id" in prose of contract.md (7 prose lines: 18, 115, 215, 217, 249, 253, 263; line 122 keeps the screen's label in quotes), schema.sql comments (2), docstrings in desk.py, portal_api.py, demo_only/portal_demo.py. They STAY, on purpose, only in text the desk shows on portal screens: the review hints of item types R and O and the repeated-fault hint (desk.py 203-211), the form's "could not store" messages (portal_api.py 653-656), the reason `same request number, different payload` (schema.sql 132; contract.md 263) and the portal's own label "Request number". A new sentence at the top of contract.md says this | NEW test_the_desks_own_word_in_contract_and_comments_is_request_id (premise: the shown texts exist in code; every remaining "request number" line in schema.sql, desk.py, portal_api.py is inside a string) |
Docs, README, limits and recipe were already swept in r5 (test_prose_says_request_id_...).

## Fails before: tests that FAIL on f3c39cf8 + lane3-fix-1-r5.patch (new test file copied over; raw/b1f-fails-before.log)
6 failed, 27 passed: test_exit_code_1_uses_the_words_the_desk_prints, test_the_desks_own_word_in_contract_and_comments_is_request_id, test_the_burst_steps_explain_each_term_and_both_systems, test_the_recipe_tells_one_true_story_about_docker, test_the_recipe_import_steps_match_the_script, test_readme_port_check_explains_000_and_404.
Also fails on the old code: test_reading_a_key_file_leaves_the_search_path_and_loaded_modules_as_they_were (run with the r5 helper appended to the r5 test file: 1 failed; the helper lives in the test file, so it cannot "fail on old docs").
Pass on r5 by design (they check the program, not the new text): test_the_causes_of_a_traceback_named_in_limits_end_in_exit_code_1 (the program ends with exit 1 on all three causes), the renamed premise 404 test.

## Rung table (tool ladder)
| component | rung | why lower rungs were rejected |
|---|---|---|
| Corrected sentences in README, limits, n8n recipe, contract.md; docstring and comment words; pinning tests | documentation and tests only, no product code | rung 1 (reuse): every document and test is corrected in place (improve before replace); `desk_origin`, `DESK_SCHEME` and `Config()` are reused for the addresses and ports in the tests; rungs 2 to 6 (client tool, no-code, MCP, retrieval, model features) do not apply to correcting text; rung 7 (custom code) is not used: no behaviour changes |

## Proof runs (commands and exit codes; python /home/user/work/final-venv/bin/python; TMPDIR and --basetemp under /home/user/work/priv/b1f-tmp; -p no:cacheprovider)
| command | exit | result |
|---|---|---|
| `pytest tests/test_docs_claims_lane3.py -q` on the final tree (before the last comment-only edit of schema.sql and the contract exit-codes line) | 0 | 33 passed |
| same file on /home/user/work/b1f-old = f3c39cf8 + r5, new file copied (raw/b1f-fails-before.log) | 1 | 6 failed, 27 passed |
| `awk 'length>120'` on the test file; added `.py`/`.sql` lines over 120 in the patch | | 0; 0 |
| added lines with `noqa` or `type: ignore` | | 0 |

## git apply --check / apply (fresh worktrees /home/user/work/b1f-chk1..5, patches from evidence/)
| tree | patch | exit |
|---|---|---|
| fresh f3c39cf8 | lane3-fix-1-r6.patch (check) | 0 |
| f3c39cf8 + claims-stack-on-f3c39cf8.patch | lane3-fix-1-r6.patch (check) | 0 |
| claims-stack, then lane3-fix-3-r5, then lane3-fix-5-r4 (each check 0, apply 0) | lane3-fix-1-r6.patch (check) | 0 |
| same with lane3-fix-5-r3 instead of r4 (each check 0, apply 0) | lane3-fix-1-r6.patch (check and apply) | 0, 0 |
| other order: claims-stack, then fix-1-r6, then fix-3-r5, then fix-5-r4 | all four, each check then apply | 0, 0, 0, 0 |
| claims + fix-3-r5 + fix-5-r3 + fix-1-r6 | lane3-fix-2-r3-on-fix-1-r5.patch (check) | 1 (contract.md, docs/limits.md, docs/why-this-code.md hunks) |
| same | lane3-fix-2-r3-for-stack.patch (check) | 1 (contract.md, docs/limits.md) |
| f3c39cf8 + fix-1-r5 (for comparison) | lane3-fix-2-r3-on-fix-1-r5.patch (check) | 0 |
The newest fix-3 patch is lane3-fix-3-r5.patch and the newest fix-5 patch is lane3-fix-5-r4.patch (the brief named r3; both were tried).

## sha256
lane3-fix-1-r6.patch: 96c6697547a33686b140b53b041f25fcbf5966efe6e288dc8ecc412df4b3ac06 (computed before the full suite and again after it: identical; `git diff --cached` of /home/user/work/b1f-base gave the same hash; raw/b1f-patch-sha-before.txt and raw/b1f-patch-sha-after.txt)

## Full suite
Command: `/home/user/work/priv/b1f-full.sh` (detached; `pytest -q -rs -p no:cacheprovider -o faulthandler_timeout=120` in /home/user/work/b1f-base, serial, TMPDIR and --basetemp outside every git worktree, no cloud settings set by me; the shell had AWS_* and ANTHROPIC_BASE_URL variables of the session, which the tests did not need). Result: EXIT_CODE=0, 3716 passed, 200 skipped in 1203 s (WALL_SECONDS=1204), log raw/b1f-full.log. 0 FAILED, 0 ERROR lines. The 200 skips are the same count as in the r5 run (3713 passed, 200 skipped; +3 = the three new tests); I did not read every skip reason (they are by design here: no playwright, no gitleaks, Windows-only tests, measurement runs that need an environment variable). The tree did not change during the run.
