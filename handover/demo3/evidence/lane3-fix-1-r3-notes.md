# lane3-fix-1 round 3 (builder B1c): notes
Worktree /home/user/work/b1c-base (public main f3c39cf8 + lane3-fix-1-r2.patch + round-3 changes), files staged, nothing committed. Patch: evidence/lane3-fix-1-r3.patch, sha256 0c45bbfe4c87a54d180ff086b37de530e367dcb346e173b67516f4e99ce53a52. Prose and tests only; product code untouched.

## Gaps first (not tried / not verified)
* Windows: no Windows computer. Every Windows step (reset.ps1, start_all.ps1, `$env:...`, `Get-NetTCPConnection`, `src;.`) is marked "not tried" in the text.
* n8n: not installed. How to start n8n, the menu names, and steps 4 and 5 of the import (import, activate) were not run by me; the workflow names were copied from the `name` field of n8n/*.json, not from a run.
* A real CRM or mail sender that cannot be reached: I read src/lead_desk/adapters.py (demo adapters: connection refused is "nothing was sent", other errors are "may have been sent") but did not find what exit code or message the desk gives for the REAL adapters at start-up, so limits.md says "not described here".
* Item 13 consolidated asserts only; I did not run ruff/format (owner rule). I kept double quotes and wrapped to 120 by script.
* Doc-related tests (11 files that mention limits.md, n8n-recipe or README.md, including the new file): 774 passed, 31 skipped (playwright missing, Python 3.13-only, gitleaks missing).

## Real outputs seen (desk on private ports 32101/32102, keyed, stopped afterwards)
* Second `feed.py --source form --index 1`: `201 {"receipt_id": 1, "verdict": "new", ..., "replayed": true, "payload_matches": true}`: the repeat shows receipt 1 (resolver was right). I sent the repeat twice by accident in the first run: the webhook lead then got `receipt_id` 4 (each repeat burns one number); with one repeat the test pins 3 (passes on a real child desk).
* /counts on a fresh desk: five counts 0; rejected_envelopes, pending_followups, failed_followups, unknown_followups, sending_followups, decide_integrity_errors, decide_transient_errors 0; hung_workers {model, crm, send, refresh} all 0; reaper_running true at the first call (not false); last_reaper_pass_at a number (1794576186); expected_match and ok null. After the demo: received 2, new 1, duplicate 1; outbox count 1. Desk and demo servers both answer 404 for /.
* Burst, --n 10, same desk: fresh prefix p1 `STATUS 201=1 200=9`, RETRIES busy503=0 refused=0, `RESULT sent=10 expected=10`; same prefix again `201=1 200=9`; different prefix p2 `200=10`. (The desk was not empty: another lead was already on it; the burst email was new, so the first case is the fresh case for that address.)
* burst.py: request numbers f"{prefix}-{i}", i from 1; prints SENT, STATUS, RETRIES (busy503, refused), RESULT or MISMATCH; no lead count.
* n8n names: "Lead Desk: Web Form Intake" (desk-form.json), "Lead Desk: Email Intake" (desk-webhook.json), "Lead Desk: Duplicate Test (10 at once)" (proof.json). They equal the resolver's guess for the first; I took them from the files.
* scripts/reset.sh refuses (exit with a reason, nothing deleted) when the database path is outside ./data: true, matches README text; I stopped my own processes by pid (12188, 12189) and checked none remain.

## Table: item | change | real output | test | fails-before first line
| # | change | real output | test (tests/test_docs_claims_lane3.py) | fails on base (first line) | fails on r2 (first line) |
|---|---|---|---|---|---|
| 1 | true receipt wording, word-list entry receipt_id, paragraph under the Linux block | repeat shows receipt_id 1, webhook lead 3 (one repeat), received 2 | test_the_receipt_explanation_is_true_and_the_word_is_defined; test_the_second_feed_and_the_receipt_number_match_the_real_desk | "the word list defines receipt_id ..."; Linux webhook line "HTTP 200 (not 201)" | "the word list defines receipt_id ..." |
| 2 | reaper_running wait of 10 seconds + data/desk.log; field list moved to 3 bullets under the block | reaper_running true at first call | test_the_fresh_desk_counts_are_what_the_readme_says | "the five counts are named and the other counts are 0 too" | same |
| 3 | Windows counts line: other number fields 0 except last_reaper_pass_at, expected_match, ok; hung_workers explained | four keys | same test | same | same |
| 4 | burst step 1: where to run, Linux and Windows (not tried) | scripts exist (reset.ps1, start_all.ps1) | test_the_burst_steps_explain_each_term_and_both_systems | "burst request numbers run from run1-1 ..." (first assert hit) | same |
| 5 | --ref-prefix, SENT/STATUS/RETRIES/RESULT explained | run1-1 .. run1-n; RETRIES busy503/refused | same + test_the_burst_numbers_in_limits_are_what_a_real_desk_answers | "a fresh desk: 201=1 and 200 for the other n - 1 sends" | "the ten-send numbers 201=1 200=9 / 200=10" |
| 6 | import steps 0-5 in order, n8n start, activate with real names | names from files | test_the_recipe_import_steps_match_the_script; test_the_recipe_activates_each_workflow_by_its_real_name | IndexError (text absent) | "the Linux way, a file outside the folder"; "the activate step names the workflow 'Lead Desk: Web Form Intake'" |
| 7 | one true Docker statement, short ports list | (n8n not run) | test_the_recipe_tells_one_true_story_about_docker; test_the_recipe_names_the_ports_each_workflow_file_needs | IndexError / "the form and webhook files need only the desk port" | IndexError; "'the easiest way' names what to keep" |
| 8 | reset sentence first, full stop, where to run | n/a | test_the_recipe_says_to_reset_and_start_everything_again | IndexError | IndexError |
| 9 | key file outside the folder, same name both systems, lasts one window, N8N_URL | n/a | import-steps test | as 6 | as 6 |
| 10 | curl --max-time 5, "usually", remedy after clone, Windows idea not tried | curl 8.5.0: 000 + exit 7 for refused; exit 28 not reproduced (resolver) | test_readme_port_check_explains_000_and_404 | "curl is listed as needed on Linux" (old text moved) | "the port check has a time limit of 5 seconds" |
| 11 | traceback explained; real CRM/mail "not described here" | adapters.py read | test_exit_code_1_uses_the_words_the_desk_prints | "limits.md quotes the words the desk prints for exit code 1" | "the traceback case is a program fault, not a setting" |
| 12 | "measured once on a Linux computer with 100 sends; logs not shipped"; numbered list | (the figure is the resolver's, not re-measured at n=100) | burst-steps test | as 5 | as 5 |
| 13 | docstring, messages, regex on facts, free_port reuse, split test | n/a | all | n/a | n/a |
| 14 | burst numbers derived from a real desk: fire() n=10 three cases | 201=1 200=9 / same / 200=10 | test_the_burst_numbers_in_limits_are_what_a_real_desk_answers | as 5 | as 5 |
| 15 | exit-code test skips on exit 3, asserts output first | n/a (this container: test ran, exit 1) | test_exit_code_1_... | n/a | n/a |
| 16 | all lines <= 120 | awk length check: 0 lines over 120 | script | n/a | n/a |
| 17 | 3-second wait before the outbox check | n/a | burst-steps test (index order) | as 5 | as 5 |

## Proof runs
* New file on patched tree: 14 passed. On unpatched base f3c39cf8 (new file copied in): 12 failed, 2 passed (the two premise tests). On round-2 patch tree: 11 failed, 3 passed (the real-desk receipt test passes there because that sentence was already in r2). Honest caveat: some "fails before" lines are IndexError because the anchor text I split on is new.
* Staged (git add -A), tests/test_hygiene.py: 20 passed, 4 skipped (all 4: no gitleaks program on PATH).
* Line length: awk over the new test file: 0 lines over 120. Changed documents: no drive path, no absolute path, no http address other than 127.0.0.1 (f-string http://{HOST} lines in the test are covered by the repo's rules, hygiene passed).
* git apply --check of lane3-fix-1-r3.patch: clean on fresh f3c39cf8; clean after claims-stack-on-f3c39cf8; clean after claims stack + lane3-fix-3-r3; clean after those + lane3-fix-5. No conflicts.

## Rung table (one row per changed sentence group; no product code; rung 1 = reuse what exists)
| group | rung | why |
|---|---|---|
| README receipt wording, counts list, port check | 1 (existing README, improved) | wording only |
| limits.md burst steps, exit code 1 | 1 | wording only |
| n8n-recipe steps 0-5, Docker, reset | 1; n8n parts rung 3 (no-code tool) described, not tried | wording only |
| tests/test_docs_claims_lane3.py | 7 (our own checking code) | reads facts from code and a real child desk |
