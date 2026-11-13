# lane3-fix-1 round 5 (builder B1e): notes
Written 2026-11-13 (UTC; IST = UTC + 5:30; checkpoints in raw/progress-B1e.txt). Worktree /home/user/work/b1e-base = public main f3c39cf8 + lane3-fix-1-r4.patch + round-5 changes, files staged (`git add -A`), nothing committed anywhere. Patch: evidence/lane3-fix-1-r5.patch (full diff from f3c39cf8, so it REPLACES r4). Prose and tests only; product code untouched (item 16, the server.py docstring, is not in this patch: another builder).

## Gaps first (not tried / not verified / failed)
* FULL SUITE: see "Full suite" at the end (result written after the run finished; if that section says not finished, it was not).
* n8n is not installed here. The two new `curl` lines for the example inputs were NOT run as written; the text says so. Nothing of the n8n steps A to F was run except the key-file reading (now tested for 10 cases).
* Windows: no Windows computer. Every PowerShell line stays marked "not tried"; the README now says "Windows: no tested check".
* The two 404 codes were read on Linux only (stated in the README sentence).
* The in-test GET on the demo server uses the tests' own in-process server of the same class (`demo_only` fakes), not the command-line program; the command-line program was checked separately by hand (raw/b1e-404-root.txt: 404 and 404).
* Not run by design: ruff, ruff format, mypy, bandit, gitleaks (CI only). So the new test code is NOT checked for ruff style or mypy types; I wrote it for mypy (typed helpers `_search`, `_start_real_desk`, `cast`) but did not run mypy. The 4 gitleaks-dependent hygiene tests skip here.
* First hygiene run FAILED (my slip): two `http://` literals in the new tests (`tests/test_docs_claims_lane3.py:759` and `:779`). Fixed (address built from `HOST`; pattern without the scheme); hygiene is green after (see "Proof runs").
* A reviewer ask I did not follow literally: item 3 names limits.md:122, portal.md:5 and tests.md:129 as "keep quoted". limits.md:122 was not a quoted label, so it now reads `request ids (the portal's "Request number")`; portal.md:5 and tests.md:129 (P10) describe the portal screen and still say "request numbers" (not changed; the test allows that word only there).

## Facts I checked myself (command or file)
| claim | how verified |
|---|---|
| The desk and the demo server answer 404 for `/` | real run 13:58Z: `curl` on desk root and demo-server root: 404 and 404, counts 200; both processes stopped (raw/b1e-404-root.txt); again in the new real-desk test |
| `RETRIES` counts every 503 or refused answer, the last too | demo_only/burst.py: `post_with_retries` calls `on_retryable(res)` before the stop checks; `fire` counts `busy503`/`refused` there; pinned by premise asserts |
| `sent=` counts 200/201/202 answers | burst.py `main`: `ok_count = sum(... k in (HTTP_OK, HTTP_CREATED, HTTP_ACCEPTED))`; the MISMATCH line uses the same number |
| feed.py gives both doors `canned-1` | scripts/feed.py `build_envelope`: `source_ref` = `canned-{index}`; the real-desk test now posts form, form, webhook all with `canned-1`: rows `[(1, 2), (3, 1)]`, webhook receipt 3 |
| Key file rules | scripts/n8n_api.py `_read_key` (strip first, then ASCII/printable/no whitespace/4096): 10 cases run against the real module by the new parametrised test (plain, line break at end, spaces and CRLF around, space inside, second line, control char, non-ASCII, byte-order mark first, empty, 4097 characters) |
| proof.json ignores `N8N_URL` | n8n/proof.json holds the 5679 address and no `N8N_URL`; desk-form.json and desk-webhook.json do not name 5679 (test) |
| curl lines carry exactly the example inputs | the test parses each `-d '{...}'` and compares with the `form:` and `webhook:` example lines, and checks the webhook paths exist in the two workflow files |
| Form example = first canned lead | test compares name, email, phone, company, message with demo_only/canned_leads.json[0] |

## Table: item | fixed how | verified how (test name = in tests/test_docs_claims_lane3.py)
| # | fixed how | verified how |
|---|---|---|
| 1 | n8n-recipe: two `curl -i -X POST ... -d '<example>' http://127.0.0.1:5679/webhook/desk-form` and `.../desk-webhook` lines, form first, with "the first canned lead", expected verdicts, "not run as written here", "Windows: no tested line" | test_the_recipe_curl_lines_send_the_two_example_inputs (fails on r4) |
| 2 | Import steps are now `**Step A.**` to `**Step F.**`; "Before you start" moved ABOVE them; no "Step <digit>" anywhere in the recipe; pointers say Step A, C, D | test_the_recipe_import_steps_match_the_script (fails on r4): letters A-F in order, section above the steps, `(?i)\bstep [0-9]` absent, `## 1.` still there |
| 3 | "request id" in prose in README/limits/n8n-recipe/tests/why-this-code; "Request number" only as the portal's quoted label (limits 118 and 122, README 34, recipe 46) | test_prose_says_request_id_and_keeps_request_number_only_as_the_portals_label (fails on r4); premise: portal.js really holds both labels |
| 4 | limits burst step 3: exact RETRIES wording, "HTTP status code", `sent` explained | test_the_burst_steps_explain_each_term_and_both_systems (fails on r4) + premise asserts on burst.py |
| 5 | README: the port check is now step 3, AFTER the clone step; 404 sentence says "read on 2026-11-13 from a real desk and a real demo server on Linux; not on Windows"; "If nothing uses the two ports, both checks print `000`"; "Windows: no tested check"; reset remedy says project folder and a terminal with `.venv` | test_readme_port_check_explains_000_and_404 (fails on r4, order check clone < check < terminal step) + test_the_readme_404_claim_for_the_root_address_holds_on_a_real_desk_and_a_real_demo_server (real GET; a premise test, passes on r4 by design because it checks the program) |
| 6 | The new `noqa` is gone: the exit-code test uses `start_proc` / `proc.wait` / `stop_proc`; the 5 `type: ignore` are gone (typed `_search`, typed `_start_real_desk(env: Env, ...) -> tuple[str, str]`, `cast`) | grep: 0 added lines with noqa or type: ignore in the patch, 0 in the whole file; test_exit_code_1_uses_the_words_the_desk_prints (runs the real desk, exit 1; fails on r4 because of the new sub-bullets) |
| 7 | Step C: the script first strips spaces and line breaks at both ends; refusal list exact (empty, over 4096, space or second line inside, control character, not printable ASCII, byte-order mark first); non-text file gets another message | test_the_key_file_rules_in_the_recipe_are_what_the_script_does (10 cases, real module) + test_the_key_file_sentence_says_what_the_script_does (fails on r4) |
| 8 | README: "attempts" explained ("the `attempts` column of that row in the desk's records, from 1 to 2") | test_the_receipt_explanation_is_true_and_the_word_is_defined (fails on r4) |
| 9 | "the repeat is not counted again" replaces "the replayed id ..." (Windows counts line) | same test: sentence present, "replayed id" absent |
| 10 | README: feed.py gives both doors the request id `canned-1`; webhook line is the same id on the other door = a duplicate, not a repeat | same test + premise on feed.py + real-desk test now posts `canned-1` on both doors |
| 11 | limits exit codes: "Exit codes of the desk:" with sub-bullets "Exit code 1" to "Exit code 5"; "cannot reach the demo servers" kept | test_exit_code_1_uses_the_words_the_desk_prints checks each sub-bullet (fails on r4) |
| 12 | limits burst step 1: common sentence, then a `Linux:` line and a `Windows (not tried for this burst):` line | burst-steps test (regex on both lines) |
| 13 | Step C says a line break at the end is fine | key-file sentence test |
| 14 | Step D: another n8n port works only for desk-form and desk-webhook; the proof workflow has the 5679 address written in | test_the_recipe_says_the_proof_workflow_ignores_n8n_url (fails on r4) |
| 15 | real-desk 404 test (see item 5) | see item 5; also raw/b1e-404-root.txt |
| 16 | NOT MINE (server.py docstring, product code; another builder) | not touched |
| 17 | kept: "run on a Linux computer with 100 sends, most recently on 2026-11-13; logs not shipped" (the r4 run, raw/b1d-burst-100.txt); the test runs n=10 | existing regex pin in the burst-steps test |
| 18 | I read the whole test file after the edits (870 added lines) | by reading; 0 noqa, 0 type: ignore, 0 lines over 120 |
| 19 | declined by resolve | not done |
Extra, same class (found while fixing item 3): docs/why-this-code.md "a log line per request number" -> "request id"; docs/tests.md rows P1 and P5 now say "request id" (P10 keeps the portal's words).

## Fails before (tests that FAIL on f3c39cf8 + lane3-fix-1-r4.patch, only the new test file copied; raw/b1e-fails-before.log)
`pytest tests/test_docs_claims_lane3.py` on that tree: 9 failed, 21 passed. FAIL: test_exit_code_1_uses_the_words_the_desk_prints, test_the_receipt_explanation_is_true_and_the_word_is_defined, test_prose_says_request_id_and_keeps_request_number_only_as_the_portals_label, test_the_burst_steps_explain_each_term_and_both_systems, test_the_recipe_import_steps_match_the_script, test_the_key_file_sentence_says_what_the_script_does, test_the_recipe_says_the_proof_workflow_ignores_n8n_url, test_the_recipe_curl_lines_send_the_two_example_inputs, test_readme_port_check_explains_000_and_404.
The 21 that pass on the old text are tests of the program or of unchanged text (fresh-desk counts, the second feed and receipt, burst numbers on a real desk, ports, Docker, reset, activate names, the 10 key-file cases, the real 404 test). They pass because they check real behaviour that was already right; they are the evidence behind the new sentences, not tests of the new sentences.

## Rung table (tool ladder)
| component | rung | why lower rungs were rejected |
|---|---|---|
| README, limits, recipe wording and the test file | documentation and tests only, no product code | rung 1 (reuse): the existing documents and tests are improved in place (improve before replace), nothing new is written where an old sentence could be corrected; rungs 2 to 6 (client tool, no-code, MCP, retrieval, model features) do not apply to correcting text and pinning it with tests; rung 7 (custom code) is not used: no product code changes |

## Proof runs (commands and exit codes)
| command (run in /home/user/work/b1e-base unless noted; TMPDIR=/home/user/work/priv/b1e-tmp, --basetemp inside it; python /home/user/work/final-venv/bin/python) | exit | result |
|---|---|---|
| `git add -A; pytest tests/test_docs_claims_lane3.py -p no:cacheprovider --basetemp ... -q` (first full pass of the new file) | 0 | 30 passed |
| `pytest tests/test_hygiene.py tests/test_portal_wording_and_masking.py tests/test_clock_steps.py tests/test_vendor_hosts.py ...` (raw/b1e-hygiene-first-run-failed.log) | 1 | 1 failed (test_hygiene_scan_public: the two `http://` literals above), 69 passed, 6 skipped. Fixed |
| `pytest tests/test_docs_claims_lane3.py tests/test_hygiene.py ...` after the fix (raw/b1e-new-tests-and-hygiene.log) | 0 | 50 passed, 4 skipped (the 4 are the gitleaks tests) |
| same two files in /home/user/work/b1e-chk = f3c39cf8 + claims-stack + fix-1-r5 + fix-3-r5 + fix-5-r3 (raw/b1e-stack-tests.log) | 0 | 50 passed, 4 skipped |
| on /home/user/work/b1e-old (f3c39cf8 + r4, new test file copied) `pytest tests/test_docs_claims_lane3.py -rf` (raw/b1e-fails-before.log) | 1 | 9 failed, 21 passed (list above) |
| `awk 'length>120' tests/test_docs_claims_lane3.py` | | 0 lines; added .py lines over 120 in the patch: 0 |
| `grep` of added lines of the patch for `noqa` and `type: ignore` | | 0 (whole new test file: 0) |
The other test files that mention the three documents were run in the first hygiene batch (portal wording and masking, clock steps, vendor hosts: green) and by the full suite below.

## git apply --check (patch order given in the brief; fresh worktrees, outputs in this table)
| tree | patch | exit |
|---|---|---|
| fresh f3c39cf8 | lane3-fix-1-r5.patch | 0 |
| f3c39cf8 + claims-stack-on-f3c39cf8.patch | lane3-fix-1-r5.patch | 0 |
| + lane3-fix-3-r5.patch | lane3-fix-1-r5.patch | 0 |
| + lane3-fix-5-r3.patch (check 0, apply 0) | lane3-fix-1-r5.patch | 0 |
| other order: claims-stack, then fix-1-r5, then fix-3-r5, then fix-5-r3 (each `--check` then apply) | all four | 0, 0, 0, 0 |

## sha256
lane3-fix-1-r5.patch: f7e9c78b629b8983d3305f70edc85ac60c119cd17a32d4e88cde57ad85f12857 (1160 lines; computed after the last change; the full suite ran on the same tree)

## Full suite
Command: `/home/user/work/priv/b1e-full.sh` (detached; `pytest -q -rs -p no:cacheprovider -o faulthandler_timeout=120` in /home/user/work/b1e-base, TMPDIR and --basetemp outside the git folder, no cloud settings). Result: EXIT_CODE=0, 3713 passed, 200 skipped in 1224 s (about 20 min 24 s), log raw/b1e-full-suite.log. The 200 skips are by design on this computer (no playwright, gitleaks and ruff-style tools not installed, Windows-only tests, measurement runs that need an environment variable); I did not read every skip reason. The tree did not change during the run (patch sha256 identical before and after).
