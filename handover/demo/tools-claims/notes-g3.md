# notes-g3: numbers cross-check of six docs against the code

Tree: /tmp/v5work. Files in scope: docs/settings.md, docs/tests.md, docs/n8n-recipe.md, docs/hubspot-probe.md, docs/real-services.md, docs/why-this-code.md. No pytest, ruff or network was used. The studio folder (bible, handoff, memory) does not exist in this container, so no R-numbers were looked up.

## Result table (MISMATCH first)

| doc:line | claim | where checked | verdict |
|---|---|---|---|
| docs/tests.md:34 | a missing scan folder makes Semgrep exit 2, which the job "retries three times" | .github/workflows/semgrep.yml (loop "for attempt in 1 2 3", comment "3 tries", pause only between tries) | MISMATCH, fixed: the job tries three times in all (two retries) |
| docs/tests.md:42 | exit 2: the job "retries up to three times, 20 seconds apart" | same loop; RETRY_PAUSE_SECONDS 20; tests/test_nosemgrep_form.py:294 | MISMATCH (unit: tries vs retries), fixed: "tries up to three times in all, 20 seconds apart" |
| docs/n8n-recipe.md:77 | n8n "repeats" a refused request "3 times", so the desk counts it 3 times | n8n/desk-form.json:104 (maxTries 3 = total tries), same sentence says the desk counts 3 | MISMATCH (repeat 3 times would be 4 calls), fixed: "sends such a refused request 3 times in all" |
| docs/tests.md:82 | the totals do not match a full run of "this commit (2516 tests" | docs/tests.md:79 gives 2516 for commit 2ce1f98 only; versions.md says collection on the tree that holds the docs listed 3883 tests in 92 files (tests/ here has 92 test files, 1679 test functions before parametrising) | MISMATCH, fixed: the 2516 now names commit 2ce1f98 |
| docs/hubspot-probe.md:14 | reads up to 10 owners, prints the count and the last 4 characters of each id | scripts/hubspot_probe.py:189 (limit=10), :99-100 (_mask keeps last 4), :194 | OK |
| docs/hubspot-probe.md:31 | first 100 characters of the error message | scripts/hubspot_probe.py:169 ([:100]) | OK |
| docs/hubspot-probe.md:4,11,22-25,33 | budget 8, 7 planned calls, 1 call kept for the permanent delete | scripts/hubspot_probe.py:45-49, :111, :303 | OK |
| docs/n8n-recipe.md:44 | n8n timeout well above the desk's default send timeout of 5 seconds | n8n/desk-form.json:100 (15000 ms); config.py send_timeout_seconds 5.0 | OK |
| docs/n8n-recipe.md:54 | Retry On Fail, 3 tries, 1 second apart | n8n/desk-form.json:103-105 and desk-webhook.json (same) | OK |
| docs/n8n-recipe.md:54,78 | "within about 2 seconds" (all three tries used up) | two waits of 1000 ms (desk-form.json:105); the measured time is the author's | CANNOT-TELL (author's timing; the arithmetic agrees) |
| docs/n8n-recipe.md:54,77 | 3 tries each for a 400 or 413; the desk counts each rejected call 3 times | desk-form.json maxTries 3; server.py:853-900 (400 bad_body, 413 too_large) | OK |
| docs/n8n-recipe.md:26,81 | 403 forbidden_host | server.py:740-761 (HTTP_FORBIDDEN) | OK |
| docs/n8n-recipe.md:46,51,53,76 | desk answers 201 new, 200 duplicate, 202 review; 400 and 413 on bad body and too large | desk.py:1281-1295; server.py:853-900 | OK |
| docs/n8n-recipe.md:27 | port 5679 (n8n_api default and proof workflow URL) | scripts/n8n_api.py:3,89; n8n/proof.json:149 | OK |
| docs/n8n-recipe.md:70 | ten requests at once, 1 new and 9 duplicates | n8n/proof.json:135 (length 10), :157 (batchSize 10) | OK |
| docs/settings.md:7,28,16,46 | exit code 4 for a refused setting, :memory:, refused leadflow file | server.py:1112-1177 (EXIT_DESK_SETTING_REFUSED = 4), desk.py:320 | OK |
| docs/settings.md:15 | approver id at most 32; name 1 to 64; label at most 64; file at most 16384 bytes | constants.py APPROVER_ID_MAX, APPROVER_NAME_MAX, APPROVERS_FILE_MAX_BYTES; config.py:_check_approvers | OK |
| docs/settings.md:24 | host name parts of 1 to 63 characters | config.py:60-61 (_LABEL: 1 + up to 61 + 1) | OK |
| docs/settings.md:16 | demo start scripts set reminder@example.test | scripts/start_all.sh:17, start_all.ps1:9 | OK |
| docs/settings.md:28,36,41,70,102 | the desk cuts every call at 9 seconds; ceiling 600 | constants.py MODEL_CALL_BUDGET_SECONDS 9.0, CALL_DEADLINE_MAX_SECONDS 9.0, SEND_TIMEOUT_SECONDS_MAX 600.0; config.py LiveSettings check | OK |
| docs/settings.md:9,18,21-23 | defaults 8765, 8766, 5.0, 65536, 120, ./data/desk.sqlite3, 127.0.0.1, demo, recorded, http, fake, off | config.py:Config fields | OK |
| docs/settings.md:32-35,38-42 | accepted ranges for ports, size cap, stall, caps, 429 retries (0 to 5), nudge (1 to 2678400), REAL_PERSONS (at most 1000) | config.py:from_env and __post_init__; smtp_outbox.py:92,107; smtp_provider.py:96,109,138; crm_hubspot.py:154,157,190; constants.py CAP_COUNT_MAX, REAL_PERSONS_MAX | OK |
| docs/settings.md:50-58 | leadflow bounds: file 16384, rota 1 to 20, steps 3 to 12, name 64, label 32, crm values 1 to 64, nudge 1 to 2678400 (31 days) | config.py:312-352 (_STEPS_MIN = 3); constants.py LEADFLOW_*; 31 x 86400 = 2678400 | OK |
| docs/settings.md:70,74-76 | SMTP defaults: host 127.0.0.1, port 2525, from, id domain example.test, timeout 5.0; SMTPP: port 587 or 465, domain example.invalid, timeout 5.0 | smtp_outbox.py:68-79; smtp_provider.py:87-88,135 | OK |
| docs/settings.md:75,82 | key and password files at most 4096 bytes; key at least 8 characters | smtp_provider.py:72; crm_hubspot.py:97,255-268; constants.py LIVE_KEY_MIN_CHARS 8 | OK |
| docs/settings.md:84 | HubSpot timeout 4.5, 429 retries 2 | crm_hubspot.py:91-92 | OK |
| docs/settings.md:96-102 | live key file has no size limit; prices 0.000001 to 1,000,000; caps up to 1,000,000; version 2026-10-21; effort low; timeout 8; tokens 64 | live_claude.py:_read_key (read_text, no limit); constants.py LIVE_PRICE_MIN/MAX, LIVE_LEDGER_USD_MAX, LIVE_API_VERSION, LIVE_DEFAULT_* | OK |
| docs/settings.md:104 | the 5 automatic tries of one follow-up email | gate.py:50 SEND_MAX_ATTEMPTS 5 | OK |
| docs/settings.md:107 | MAX_CONNECTIONS 256, MAX_HANDLER_THREADS 1024, header and body deadlines 10 s, Retry-After 1 s | constants.py MAX_CONNECTIONS, MAX_HANDLER_THREADS, HEADER_READ_DEADLINE_SECONDS, BODY_READ_DEADLINE_SECONDS, BUSY_RETRY_AFTER_SECONDS | OK |
| docs/settings.md:111,112 | live key shorter than 8 refused; ledger file larger than 8,000,000 bytes refused | live_claude.py:428; constants.py LIVE_LEDGER_FILE_MAX_BYTES | OK |
| docs/settings.md:116-120 | run_real_check: exit 0/1/2/3, readback at least 5 and at most 10000, REAL_PERSONS 12/8/1000, drain 150, mail wait 90, settle 10, limit 86,400, port 993, DESK_SEND_TIMEOUT_SECONDS=8 | scripts/run_real_check.py:96 (EXIT_REFUSED, EXIT_STOPPED, EXIT_FAILED = 2, 1, 3), :102-123, :612, :636, :854-875 | OK |
| docs/settings.md:121 | n8n_api: default port 5679, key at most 4096 characters, port 1 to 65535, exit 1 or 2 | scripts/n8n_api.py:66,81,89,93,108,175-222 | OK |
| docs/settings.md:126 | DPLD_REQUIRE_DEMO=1 stops the run with exit code 2; both workflows set it to 1 | tests/conftest.py:27-29; lint.yml:100; sonar.yml:50 | OK |
| docs/tests.md:34 | semgrep job: time limit at most 20 minutes, exactly five steps | semgrep.yml:26 and the five steps; tests/test_nosemgrep_form.py:200,333 | OK |
| docs/tests.md:36 | run 43403502735: 64 files, 79 rules, 77 rules, 47 files | only the same text in semgrep.yml comment (a dated run read by the lead) | CANNOT-TELL (4 numbers) |
| docs/tests.md:42 | 20 seconds apart | semgrep.yml (RETRY_PAUSE_SECONDS 20) | OK |
| docs/tests.md:42 | 47 files on 61ded9e | the author's own run | CANNOT-TELL |
| docs/tests.md:78-80 | 958 s, 16 min 33 s (993 s), 82.7 s, 83.0 s, 80.6 s; counts 2349/116, 2460/2/3, 2462/3, 2513/3, 114/113, 92/135 | dated run results; only the sums were checked: 2349+116 = 2465, 2460+2+3 = 2465, 2462+3 = 2465, 2513+3 = 2516, 2465+51 = 2516, 49+1+1 = 51, 114+113 = 92+135 = 227, 114-92 = 22 = 1+2+19, 22+28+60+3 = 113, 16x60+33 = 993, 2329+135 = 2464 | CANNOT-TELL (7 timing rows); the sums are consistent |
| docs/tests.md:80 | skip lines 110, 175, 488, 113, 27, 171, 204, 257 | tests/test_mode_safety.py:110,175; test_portal_lead_pages.py:113,488; test_portal_browser.py:27; test_portal_wording_and_masking.py:171,204,257 | OK |
| docs/tests.md:80,52 | eight browser test files; three in test_portal_wording_and_masking.py | the 8 files named exist; three importorskip lines there | OK |
| docs/tests.md:78 | four gitleaks skips in tests/test_hygiene.py | test_hygiene_scan_public, the carriage-return test, the lock-file test and the relative-path test all skip without gitleaks | OK |
| docs/tests.md:92 | line 31 of the 34 lines of exceptions.txt; pattern 9 is the 40-or-more run | exceptions.txt (34 lines; line 31 is the sonar.projectKey line); patterns.txt:9 | OK |
| docs/tests.md:40 | n8n holds 3 JSON files | n8n/desk-form.json, desk-webhook.json, proof.json | OK |
| docs/tests.md:48,54 | uv 0.11.32 (coverage lock), 0.13.8 (Semgrep lock); Playwright 1.63.0 plus greenlet, pyee, typing-extensions with the same typing-extensions version as the dev lock | requirements-coverage.in:4, requirements-semgrep.in:4,6; requirements-browser.txt; typing-extensions 4.16.0 in every lock | OK |
| docs/tests.md:96-113 | ten crash points (A, A2, B, L, C0, C1, D1, D1b, D2, D3) plus N1; D2 killed 3 times | src/lead_desk crash_point calls (11 names); tests/test_http.py:292-336 (keyed, blind, SMTP blind) | OK |
| docs/tests.md:124,127 | ten at once: 1 new and 9 duplicates; newest 50 | proof.json batch 10; constants.py DUPLICATES_MAX 50 | OK |
| docs/tests.md:129 | eye button shows a value for 30 seconds at most | src/lead_desk/portal/portal.js:227 (REVEAL_MS 30000) | OK |
| docs/tests.md:79 | the file tests/test_except_clause_hierarchy.py lists 52 tests; 10 hygiene tests passed with gitleaks 8.30.1 | needs pytest collection or a run (not allowed here); lint.yml names gitleaks 8.30.1 | CANNOT-TELL (not run) |
| docs/real-services.md:9 | about 12 invented people | scripts/run_real_check.py:102 (DEFAULT_PERSONS 12) | OK |
| docs/why-this-code.md:13,21,24 | four n8n patterns; seven checks; about 200 lines | docs/n8n-recipe.md section 2 (a to d); load_tools/check_invariants.py:1,645; tools/scrub_n8n_export.py is 205 lines | OK |
| docs/hubspot-probe.md:4,66-73 | 403 MISSING_SCOPES, 400 on .test, 204 on permanent delete, "6 or 7 of the 8 calls" | the author's runs against a real account | CANNOT-TELL (kept as labelled history) |

## Counts for the final line

All 49 rows of g3.tsv were read in their full sentence. Of those: 35 agree with the code (OK), 14 cannot be compared (CANNOT-TELL: rows for tests.md:36 x4, tests.md:42 "47 files", tests.md:78-80 x7, n8n-recipe.md:54 and :78 "2 seconds" x2). None of the 49 rows has a wrong value or unit. The 4 MISMATCH rows above came from the extra checks (b) to (d) and a read of the surrounding sentences (retry wording, one commit label), not from a row of the tsv.

Not checked (needs a run, a network or a real account): all dated run results and timings; the Semgrep and gitleaks numbers; how many tests pytest collects; whether n8n really waits 1 second between tries (the file says 1000 ms).

## Edits made (old -> new)

1. docs/tests.md:34: "which the job retries three times and then fails with a message" -> "which the job tries up to three times in all before it fails with a message".
2. docs/tests.md:42: "the job retries up to three times, 20 seconds apart, then fails" -> "the job tries up to three times in all, 20 seconds apart, then fails".
3. docs/n8n-recipe.md:77: "n8n repeats such a refused request 3 times" -> "n8n sends such a refused request 3 times in all".
4. docs/tests.md:82: "do not match a full run of this commit (2516 tests" -> "do not match a full run of commit 2ce1f98 (2516 tests".

No backslash-escaped quotes, URLs, host names or long unbroken runs were added.

## CODE-LOOKS-WRONG

None found. One inconsistency between files that I did not touch: versions.md says collection on the tree that holds the docs lists 3883 tests, while docs/tests.md:79 gives 2516 for commit 2ce1f98 and says 52 tests for the except-clause file; the doc states these as different commits, so I only changed the label in docs/tests.md:82. Whoever runs `python -m pytest --collect-only -q` should confirm the current total.
