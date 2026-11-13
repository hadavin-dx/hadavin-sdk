# Lane 3 fix 1: documentation patch for the cold-reader findings (builder B1)

Base: public main f3c39cf89ec989f032ea48a23cfd824b88da9c68. Python 3.12.3 (final-venv), private ports 23801/23802, private TMPDIR, one core. Time: 2026-11-13 12:42Z (18:12 IST) to about 12:55Z (18:25 IST). Prose and one new test file only; no product code changed.

## Patch
File: `evidence/lane3-fix-1.patch` (against f3c39cf8). SHA256: 67597283f3459496bdb148bf870b3eddd618be4f5ef67144c06ee7c68f8ccf27
Files changed: README.md (3 hunks), docs/limits.md (2 hunks), docs/n8n-recipe.md (4 hunks, one file), tests/test_docs_claims_lane3.py (new, 9 tests).
`git apply --check` on a fresh f3c39cf8 worktree: OK. On f3c39cf8 plus `claims-stack-on-f3c39cf8.patch` applied first: OK, both applied together with no conflict.
Hunk overlap with the claims stack: the stack touches README.md at lines 11, 85-91, 101-112, 117, 127 and docs/limits.md at lines 68 and 138. This patch touches README.md at lines 44-50, 57-66, 74-80 and docs/limits.md at lines 88-94 and 117-123. Nearest neighbours are README 85 (stack) versus 80 (this patch). No overlapping hunk, no conflict. The stack also touches docs/settings.md and docs/tests.md; this patch does not. The new tests pass on the stacked tree (9 passed).

## Findings table
| # | Finding | Reproduced? how | Patched? | Test (tests/test_docs_claims_lane3.py) | BASE | Patched |
|---|---|---|---|---|---|---|
| 1 | limits.md exit code 1 "the sender cannot be reached" | Yes: `python -m lead_desk.server` with no demo servers: prints "cannot reach the demo servers (are they running? ...)", exit 1 | Yes | test_exit_code_1_uses_the_words_the_desk_prints (runs the desk, takes the printed words) | FAIL: `AssertionError: limits.md must quote the words the desk prints for exit code 1` | pass |
| 2 | "should each be 1" true only on a fresh desk | Yes: fresh desk burst of 100 gave `201=1 200=99`, new 1; after the README demo (same email) the same burst gave `200=100`, new stays 1 and no 201 | Yes (also the `201=1` expectation, same cause) | test_burst_counts_are_stated_for_a_fresh_desk_only | FAIL (first assertion: no "fresh desk" before "should each be 1") | pass |
| 3 | recipe says ports come from settings.md, files hardcode 8765/8766/5679 | Yes: grep of n8n/*.json: 8765 (leads), 8766 (/fake/crm, /fake/outbox), 5679 (proof's call to desk-form) | Yes: new sentence says files do not read the settings, name the three ports, and that editing is licence-restricted; the "(host and port from settings.md)" phrase replaced | test_the_workflow_files_carry_the_default_ports (premise, derived from Config defaults and n8n_api default) and test_the_recipe_says_the_ports_are_written_into_the_workflow_files | premise test passes on BASE (correct, it checks the fact); second FAIL (`"do not read those settings" in flat`) | both pass |
| 4a | recipe example returns "new" only after a reset | Yes: after the README demo, the form example (sub-0001, Ada@example.com) answered `duplicate`, receipt 4. The example email equals demo_only/canned_leads.json lead 1 | Yes | test_the_recipe_example_lead_is_the_readme_demo_lead_so_it_says_to_reset_first (derives the premise from the canned lead) | FAIL | pass |
| 4b | recipe does not say how to make the API key, nor name N8N_API_KEY_FILE | Yes (recipe text has only "see the top of that script"); setting name exists in scripts/n8n_api.py | Yes: names the setting, says run from repository folder, says create key in n8n's own settings (menu names NOT compared, n8n not installed here) | test_the_recipe_names_the_key_file_setting_and_says_how_to_delete_a_workflow | FAIL | pass |
| 4c | recipe does not say how to delete a workflow | Yes: only section 3 says it; the helper has no delete command | Yes: one clause at the same place (delete it in the n8n screen, not tried) | same test | FAIL | pass |
| 5a | `curl` not listed in "You need" | Yes: README Linux block uses curl 3 times; "You need" line lacks it | Yes: added `curl` for Linux with a one-line explanation | test_readme_lists_curl_because_the_linux_lines_use_it_and_shows_a_port_check | FAIL | pass |
| 5b | no way to check ports 8765/8766 are free | Yes. I ran `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:23801/` on a port nothing used: prints `000`, exit 7; on the live desk it prints 404 | Yes for Linux. Windows: not tried, the README now says so | same test | FAIL | pass |
| 5c | webhook door answers HTTP 200 for a duplicate | Yes: `feed.py --source webhook` printed `200 {... "verdict": "duplicate"}` (the form door's new answer is 201) | Yes | test_readme_says_the_duplicate_door_answers_200_and_why_receipt_ids_skip | FAIL | pass |
| 5d | receipt_id jumps 1 to 3 | Yes, twice. Cause found: `src/lead_desk/schema.sql` has `receipt_id INTEGER PRIMARY KEY AUTOINCREMENT`, and the "insert, on conflict update" in desk.py uses up a number for each repeated request. Check: ids 1,2,(repeat of 1),4,(repeat),(repeat),7 | Yes: README says numbers only go up, can skip, and a gap is not a lost request. The behaviour is by design; no product code change | same test (also asserts the AUTOINCREMENT premise in schema.sql) | FAIL | pass |
| 5e | "numbers all 0" ignores reaper_running and last_reaper_pass_at | Yes: `/counts` on a fresh desk has `reaper_running: true` and `last_reaper_pass_at` non-zero | Yes (Linux line and the Windows line) | test_readme_counts_check_names_the_counts_that_are_zero | FAIL | pass |
| 5f | `/` and `/health` return 404, README implies otherwise | Both do return 404 (checked). The README does NOT imply otherwise: line 88 already says "answers 404 for / and /health on purpose" | DROPPED (not a defect in the README) | none | n/a | n/a |

## RUNG TABLE
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| limits.md exit 1 sentence | name the real message | fix the sentence (rung 7 not needed, prose) | reproduced, test | the message text lives in our server code | KEEP (fixed) |
| limits.md burst sentence | say it needs a fresh desk | fix the sentence | two runs above | nothing | KEEP (fixed) |
| n8n-recipe ports sentence | say ports are written in files | fix the sentence | grep of n8n/*.json | nothing | KEEP (fixed) |
| n8n-recipe reset sentence | say reset first | fix the sentence | duplicate answer seen | nothing | KEEP (fixed) |
| n8n-recipe key/delete clause | name setting, key, delete | fix the sentence | script has no delete command | nothing | KEEP (fixed) |
| README curl + port check | list the tool, give a check | fix the sentence | curl run on free and used port | nothing | KEEP (fixed) |
| README duplicate 200 + receipt skip | state both | fix the sentence | runs above, schema.sql | nothing | KEEP (fixed) |
| README "numbers all 0" (two lines) | name the counts | fix the sentence | `/counts` output | nothing | KEEP (fixed) |
| README 404 claim | nothing wrong | delete = not needed | line 88 already says it | nothing | CUT (no change) |

## Evidence (commands run)
* New tests on BASE (new file copied into a clean f3c39cf8 worktree, TMPDIR private, `--basetemp` inside it): `8 failed, 1 passed in 0.20s`; the one that passes is the premise test of finding 3 (it checks the port fact, which is true on BASE). First failure line: `AssertionError: limits.md must quote the words the desk prints for exit code 1`.
* New tests on the patched tree: `9 passed in 0.27s`. On the patched tree plus the claims stack: `9 passed in 0.27s`.
* `ruff check`, `ruff format --check` and `bandit -ll` on the new test file: clean (after one format fix).
* Hygiene and doc-related existing tests: see the section "Existing tests" below.

## Not patched, and why
* `src/lead_desk/server.py` line 1112 (docstring) and `src/lead_desk/constants.py` line 256 (comment) also say "the sender cannot be reached". That is product code (a docstring and a comment, not output): the brief says prose and tests only, so I did NOT change them. Next step for the owner: one-word edit in both places in a code patch if they want the code to match the docs.
* Cold-reader item F2 (workflow files hold `"active": true` while the recipe says the flag is ignored) and the n8n jargon lists (cold reader section 4) were not in the assigned finding list; not patched here. The wording items are a wider rewrite and need their own EGM pass.
* Windows: no way to check ports given (not tried; the README says so). n8n was not installed, so nothing about n8n's screen was verified; the "settings page" for the API key is stated with "menu names were not compared".
* The README lines about HTML/portal content were not seen in a browser by either reader or me.

## Existing tests (patched tree, before the final format fix of the new test file, which changed no assertion)
Command: `pytest <17 test files that mention limits.md, n8n-recipe, README or .md> tests/test_hygiene.py -p no:xdist --basetemp=$TMPDIR/bt2` with a private TMPDIR. Result: `1412 passed, 71 skipped in 380.72s`, exit 0. The 71 skips are the repository's own skips (browser, scanner tools not installed here, etc.); I did not list them. The 9 new tests were re-run after the format fix: `9 passed`.
Not run: the full suite (about 20 minutes on this shared machine).
