# notes-r1fix2 (tree /tmp/v8work, nothing committed or pushed)
Method: every edit applied by one script with an exact-match check (each old text found exactly once). Targeted tests run (not the full suite):
tests/test_hygiene.py, test_nosemgrep_form.py, test_portal_wording_and_masking.py, test_gitleaks_exceptions.py, test_portal_mode.py::test_one_way_to_say_an_email_was_sent,
test_scrub_n8n_export.py, test_hubspot_probe.py, test_portal_layout.py (doc tests): 169 passed 31 skipped, and 61 passed. Skips = no gitleaks/node/browser here. Run with a plain venv (pytest, pyyaml), not `uv run --group test` (the project has no `test` group; uv made a .venv in the tree, I removed it).
Lines: file:line are in the NEW text (approx).

| # | file | old -> new (short) | proof |
|---|---|---|---|
| 7 | README Words "Request id" | "this is a repeat" -> "this is a replay (see Replayed below)" | README Replayed bullet: same request number = replayed |
| 7 | README Optional features | "then a repeat is only listed" -> "then it is only listed" | contract.md step 3: D item = verdict duplicate |
| 7 | settings.md later_mode row | "a repeat (a second request from a lead the desk already knows)" -> "a duplicate (... under a new request number with an email address the desk already knows)"; "per repeat" -> "per duplicate" | contract.md "D<n> a receipt with verdict duplicate and non-empty differing_fields" |
| 7 | portal.md:7 | "Repeat (...)" -> "Repeat (the verdict `duplicate`: ...)" | src/lead_desk/portal/portal.js:58 maps duplicate to 'Repeat' |
| 9 | limits.md short item 3 and "At most 4 AI calls" bullet | "nothing is lost and nothing is sent" -> waiting follow-ups stay in the records, shown `stalled`, tested only for a full AI cap; "nothing is sent or lost" -> "in the stalled list" | contract.md (4) "stalled list", test_full_model_cap_shows_the_row |
| 10 | limits.md short item 5 | "on a keyed mail system that is harmless" -> "on the demo keyed mail system the repeated send is ignored (a real mail system may send it twice)" | README:10 and limits "What is not claimed" first bullet |
| 11 | limits.md masking bullet | removed "so nobody can probe whether a name exists..." -> "this hides values on the page only, see the next bullet" | next bullet states by_email search works |
| 12 | SECURITY.md:5 | "not meant to go ... until a person has done the checks" -> "must not go into it, whether or not a real CRM is connected; the named check is only the minimum before connecting a real CRM, first test with one made-up contact" | README WARNING "Required before you point this at a real CRM" |
| 13 | tests.md (checks paragraph, Status of the scan, node paragraph) | one-Semgrep-run / "only CI run reported in this file" removed; now "No run result is stored in this repository" in all places; semgrep.yml status lines removed so no pointer remains | grep: no "one Semgrep run", "only CI run" left |
| 14 | limits.md (was 64-69) | replaced the whole "Test runs" bullet (2449/2462 passed, 558d37f, collection-count sentence) by one bullet: no run result stored; versions.md gives only the number of test files (92); no count of collected tests stored | `ls tests/test_*.py` = 92; versions.md row |
| 15 | README "You have the demo working" | test bookkeeping removed, now "no page at `/` or `/health`; it answers 404 for an address it does not know"; moved to tests.md before "The promises P1 to P10" | tests/test_http.py `/nope` 404; test_server_hardening.py odd request with path `/` 404 |
| 16 | README reset script | one bullet per exit code 2..6; RESET_STOP_WAIT_SECONDS in its own sentence | text unchanged otherwise |
| 17 | README WARNING | split into 3 bullets (what is written/what may react; Required before a real CRM; No sign-in). Test phrases kept each within one line | test_lead_status_write_warning_is_in_the_docs passed |
| 18 | limits.md "Time budget" | now opens with: stuck after 30 s ("stuck grace"), AI call 9 s + save 15 s = 24 s below smallest grace 25 s | contract.md lines on grace, MODEL_GRACE_MARGIN_SECONDS |
| 19 | tests.md CRLF paragraph | rewritten to lead with the action (cure 2 one-liner, cure 1 conditions); all git/gitleaks measurements and "line 31 of 34" removed (also the "What the two secret checks reported" paragraph, same kind of measurement) | tests/test_hygiene.py CRLF_HINT and test_every_cure_in_the_message_works |
| 20 (not on my list, done) | README:9 | "same lead twice and through two doors" -> one lead, same request again, same person other door: new, replayed, duplicate | README Try it steps |
| 21 | README | start-step comment "demo servers" -> "demo server" (one fakes_server program); "(the stand-ins)" -> "(the demo server and the file of pre-written answers)" | README:53 |
| 22 | README Crash point | added: crash point names are not review-item ids | contract.md D<n>/N<n> items |
| 23 | README Reaper | "in all" -> "in a row; a person's Retry starts the count again"; "decides receipts" explained "(writes a verdict for them)" | limits.md "A person's Retry starts the count again at try 1" |
| 24 | README:22 | "step replied" -> "stage the same file names as `reminder_until` (`replied`)" | demo_only/leadflow.json |
| 25 | README Try it / Tests | "(tried: Windows with Python 3.13 and Linux with Python 3.12; see versions.md)"; "not supported for running the tests" | versions.md, README tests paragraph |
| 26 | README About n8n | "no result of those n8n-only patterns is stated here (shipped workflows: docs/n8n-recipe.md)" | n8n-recipe.md states results |
| 27 | contract.md accepted-limit bullet | subject added; DESK_SEND_TIMEOUT_SECONDS above 9 accepted, no effect | settings.md send-timeout row |
| 28 | settings.md DESK_STALL_SECONDS | removed "(early, not wrong: a decision is written once)"; "decides" explained "(writes a verdict for it)"; did NOT add "even one still being handled" or "for tests" (not proven) | - |
| 29 | limits.md:3 | heading name corrected to "What is claimed, and what is not" | README heading |
| 30 | limits.md; desk.py 2 docstring lines + 1 comment; gate.py 1 docstring | "private memory book" -> "private in-memory database" (comments only) | text only |
| 31 | tests.md "Four tests are skipped" | replaced by list of causes (OS, Python 3.13, LEAD_DESK_LOAD_N, root, node, gitleaks, Playwright); no fixed count stored; the 2/3/4 counts are gone with the deleted run results | grep skipif/skip in tests/ shows many more than four skip causes (symlink tests, fcntl, geteuid) so "four" was false |
| 32 | SECURITY.md:3-4 | added the two demo routes with what they do | docs/portal.md:31 |
| 34 | contract.md heading and bullets (4) and the give-back bullet | heading -> "Reply rows that are easy to miss (checklist)" + one explanatory sentence; two long bullets split into sub-bullets | text only |
| order | tests.md ~74, 78, 80, 92 (+90) | Measured-on-Linux paragraph, "Counts from earlier full runs", "2329 passed", gitleaks/git measurements deleted; "Nothing else was needed in the author's runs below..." (pointer) -> "The lock holds only Playwright and its three packages; neither lock file holds Pillow" | requirements-browser.txt has 4 packages; grep Pillow in locks: none |
| order | limits.md 65-66 | deleted (see 14) | - |
| order | semgrep.yml | run id, head sha, quoted "Scanning 64 files"/"Ran 77 rules", exit-3 --strict claim, 17 s install claim, "from the author's own runs" exit-code parenthetical (incl. unproven code 7) deleted; exit codes now stated as what the step handles | step script lines 0/1/2/other |
| order | tests.md nosemgrep paragraph | removed "(checked by the author ... no log is shipped)" | test_nosemgrep_form.py refuses those spellings |
| order | tests/test_gitleaks_exceptions.py docstring | pointed at the deleted measurement; now says the two sets assert it | docstring only |
| extra | limits.md ~153 | "no test asserts that no other field is in the body" was FALSE: tests/test_lead_crm_copy.py:157-162 asserts the PATCH body equals exactly the two properties. Sentence corrected | test read |
| coord a | hubspot-probe.md:3, :18 | "then deletes" -> "then tries to delete (WARNING naming the contact if refused)"; "Always deletes it" -> "Tries to delete it ... If both are refused the `delete` line shows FAIL and a WARNING names the contact" | scripts/hubspot_probe.py _delete / finally block; no other "always deletes" sentence found (grep) |
| coord b | README:31 | demo servers play CRM and mail only; AI step = file `replies.json` read by RecordedQualifier | demo_only/fakes.py:112, loader.py:100 |
| coord c | settings.md:3 | added ", or an IPv4 loopback address written in the `::ffff:` form" | config.py is_loopback_host ipv4_mapped |
| coord confirm | semgrep.yml:55, tests.md:30, tests.md:111, limits.md:68 | all fixed as above | greps |

## Skipped, and why
- Findings 1-6, 33: PR body (lead's).
- Finding 8: NOT added. Not provable that author, project owner, project lead, repository owner and licence holder are one person: LICENSE names the licence holder (README:161 "all rights reserved by the author" ties author = licence holder), but "repository owner" (semgrep.yml:3, tests.md:38/46/48, requirements-semgrep.in:12) is not defined in the tree. "project owner" and "project lead" sentences are deleted with the run results (the semgrep.yml one even set the project lead apart from the comment's author). Lead: decide whether author = repository owner, then one line in README "Words used here" is enough.
## Left alone, lead to decide
- Other dated results with no log in the tree, not on the lead's list: limits.md load figures (150/300 connections, "from the author's own run"), n8n-recipe.md results (run 2026-11-09), versions.md licence/SQLite/Python readings (2026-11-12), tests.md Chromium build numbers read 2026-11-12, codeql.yml/lint.yml/sonar.yml comments, tests/test_hygiene.py comment "Measured (gitleaks 8.30.1...)". They are labelled "no log is shipped".
- semgrep.yml lines 2,3,19,37,49,50,54-56 are over 120 characters (already so before; only my new lines were kept short).
- Existing hedge "may" remains in untouched sentences.
