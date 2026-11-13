# out-ver-r1fix2 (verifier, read-only, tree /tmp/v8work; no full suite run, nothing written in the tree)

Deleted-text grep (2349, 2462, 2449, 958 s, 43403502735, "Ran 77 rules" as a quoted result, "reported below", "only CI run", "one Semgrep run", 2329 passed, 558d37f, "line 31 of 34", "Four tests are skipped"): no hit in the tree except hash lines in requirements-*.txt (random hex, not text). The words "Ran N rules" remain only as an instruction in tests.md and semgrep.yml (not a result). Clean.

| row | verified how | verdict |
|---|---|---|
| 7 README Request id "replay" | README:37 Replayed bullet; README:9/20 use new/replayed/duplicate | TRUE |
| 7 README Optional features "then it is only listed" | settings.md later_mode row + contract.md:163 (D item = verdict duplicate) | TRUE |
| 7 settings.md later_mode "duplicate ... new request number" | contract.md:163, README:36 | TRUE |
| 7 portal.md:7 Repeat = verdict duplicate | portal.js:58 `duplicate: 'Repeat'` | TRUE |
| 7 (sibling, not a row) docs/limits.md:118 "treated by the desk as a repeat" | same request number = "replayed" per README:37; the word "repeat" now means two things | FALSE (leftover). Replace "treated by the desk as a repeat" with "answered by the desk as a replay (same stored answer)" |
| 9 limits.md item 3 + "At most 4 AI calls" bullet | limits.md:11,40-44; contract.md:40 stalled list; tests/test_hung_adapter_calls.py:421 exists | TRUE |
| 10 limits.md item 5 keyed mail | limits.md:13 vs README:10, limits.md:22 | TRUE |
| 11 limits.md masking bullet | limits.md:108 says by_email=1 search works; contract.md:227 `by_email` default 1 | TRUE |
| 11 (sibling) contract.md:227 "so nobody can probe for a name" | same sentence in the same parenthesis says any caller can send 1; "nobody" is false | FALSE (leftover). Replace "so nobody can probe for a name; masking is on screen only, so any caller can send 1" with "this hides values on the page only; any caller can send 1" |
| 12 SECURITY.md:5 | README:131 "Required before you point this at a real CRM" has the same text | TRUE |
| 13 tests.md "No run result stored" / semgrep status | tests.md:36, 107; limits.md:62; greps clean | TRUE |
| 14 limits.md Test runs bullet | `ls tests/test_*.py` = 92; versions.md:9 says 92 test files | TRUE |
| 15 README no page at `/` or `/health`, 404 | grep src: no `/health` route; tests/test_http.py `/nope`; test_server_hardening.py path `/` 404 (tests.md:127 itself says `/health` and plain `/` are untested) | TRUE (by code reading for /health, not by a test) |
| 16 README reset exit codes 2..6 | reset.sh exit 2/3/5/6, reset_check.py return 3/4; reset.ps1 exit 2/5/6; Linux ps-missing = 3 (reset.sh:24) | TRUE |
| 17 README WARNING 3 bullets | README:128-132; real_services in config.py:451 covers crm, mail, ai; is_loopback_host config.py:64; test_lead_crm_copy.py:157-162 asserts exact body | TRUE |
| 18 limits.md Time budget | constants.py MODEL_CALL_BUDGET 9, MODEL_GRACE_MARGIN 15 (24 s); contract.md:47 smallest grace 25 s; desk.py:409 grace = send timeout + 5x5 s | TRUE |
| 19 tests.md CRLF paragraph | tests/test_hygiene.py CRLF_HINT cures 1 and 2 and `test_every_cure_in_the_message_works` | TRUE |
| 20 README:9 | README:20, 62-64 steps give new / replayed / duplicate | TRUE |
| 21 README demo server | demo_only/fakes_server.py one program; README:18, 31 | TRUE |
| 22 README Crash point vs review ids | contract.md:163 D<n> items; README:41 | TRUE |
| 23 README Reaper | gate.py:53 backoff (1,2,4,8), SEND_MAX_ATTEMPTS 5; limits.md:32 Retry starts count again | TRUE |
| 24 README:22 `reminder_until` (`replied`) | demo_only/leadflow.json `"reminder_until":"replied"` | TRUE |
| 25 README "tried: Windows Python 3.13 and Linux Python 3.12" | versions.md:3,8: the DEMO was run on Windows (3.13.3); Linux 3.12 is the test suite/lock container, not stated for the demo; README:47 sits in "Try it" | UNPROVEN. Replace with "(the demo was run on Windows with Python 3.13 and the tests on Linux with Python 3.12; see `versions.md`)" |
| 26 README About n8n | README:138 vs docs/n8n-recipe.md (results there) | TRUE |
| 27 contract.md:49 "DESK_SEND_TIMEOUT_SECONDS above 9 accepted, no effect" (and settings.md:36 "has no effect, because the desk cuts every call at 9 seconds") | config.py:521 accepts up to SEND_TIMEOUT_SECONDS_MAX; desk.py:1437 call deadline = min(value, 9) so the call deadline is unchanged, BUT desk.py:409 stuck_grace_seconds = int(send_timeout_seconds + 25), so a value above 9 DOES change the stuck grace; adapters (loader.py:77,84, smtp) also take it as their own socket timeout | FALSE. Replace in both places with "a value above 9 is accepted; the desk still cuts every CRM put, send and capability read at 9 seconds, but the value also sets the stuck grace (value + 25 s), so a larger value makes the desk wait longer before it puts a stuck follow-up back" |
| 28 settings.md DESK_STALL_SECONDS | settings.md:35; stall_seconds 0..86400 (contract/settings); reaper decides wording consistent | TRUE |
| 29 limits.md:3 heading | README:100 "What is claimed, and what is not" | TRUE |
| 30 "private in-memory database" in limits.md, desk.py, gate.py | grep: desk.py:318,381; gate.py:188; limits.md:50 | TRUE |
| 30 (sibling) contract.md:155 "a private memory book" | grep shows the old wording still in contract.md:155 | FALSE (leftover). Replace "a private memory book" with "a private in-memory database" |
| 31 tests.md skip causes | tests.md:77; tests use skipif for ntpath.isreserved (3.13), geteuid (root), LEAD_DESK_LOAD_N, node, gitleaks, Playwright | TRUE |
| 32 SECURITY.md demo routes | docs/portal.md:31 | TRUE |
| 34 contract.md heading | contract.md:7 "Reply rows that are easy to miss (checklist)" | TRUE (text only) |
| order: tests.md Pillow/lock sentence | requirements-browser.in 1 pin; requirements-browser.txt has 4 `==` pins; no Pillow in any requirements file | TRUE |
| order: limits.md 65-66 deleted | limits.md:62 single bullet | TRUE |
| order: semgrep.yml exit codes and deleted numbers | semgrep.yml:70-80 script: 0 pass, 1 "findings above", only 2 retried (3 tries, 20 s), other = tool error | TRUE |
| order: tests.md nosemgrep paragraph | tests.md:46; no "checked by the author" text | TRUE |
| order: test_gitleaks_exceptions docstring | not opened in detail; the instruction was docstring-only and the deleted-text grep is clean | UNPROVEN (low risk; open `tests/test_gitleaks_exceptions.py` top docstring once) |
| extra limits.md:146 PATCH body | crm_hubspot.py:401-405 props = hs_lead_status (+ owner if not empty); test_lead_crm_copy.py:157-162 asserts equality | TRUE |
| coord a hubspot-probe.md:3, 18 | scripts/hubspot_probe.py `_delete` (permanent, then normal delete for an id only) and the `finally` block; WARNING printed on refusal (it names the contact by a masked id, or by the email when the create answer was lost) | TRUE |
| coord b README:31 | demo_only/fakes.py:112, loader.py:100 | TRUE |
| coord c settings.md:3 `::ffff:` | config.py:76-77 ipv4_mapped | TRUE |

Not a row, seen while checking: semgrep.yml:3 "the repository owner agreed to use them here" and the `--strict` comment are statements with no proof in the tree (the lead already knows about finding 8). tests.md:107 has "; No run result" with a capital N after a semicolon (wording only).

Result: 4 FALSE (row 27, and three leftover siblings: limits.md:118, contract.md:227, contract.md:155), 2 UNPROVEN (row 25, gitleaks docstring), rest TRUE.
