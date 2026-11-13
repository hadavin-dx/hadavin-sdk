# notes-v8-D (builder, text only; tree /tmp/v8work; no pytest, lint, network or commit)

Studio folder not in this container: no R-numbers cited. Not run: any test or lint (forbidden); not re-read after edits except backtick parity (all even), no 40+ character run, no URL or path added.

## Facts first (type c and d rows, out-d9 DIFFERS, out-d8)

| row id | file:line | problem | verdict | edit (old -> new) |
|---|---|---|---|---|
| d7 tests:30 "no result claimed" | tests.md:30 | contradicts Semgrep result at :36 | TRUE-PROBLEM | "No result of any of these" -> "No result of the CodeRabbit, SonarQube Cloud or CodeQL checks ...; the one Semgrep run that was read is reported below" |
| d7 tests:30 ".env / no secrets" | tests.md:30 | SONAR_TOKEN, key files | TRUE-PROBLEM | -> "The demo needs no secrets and no .env file; the real-service scripts read their secrets from files you name" |
| d7 tests:30 "whole test suite" | tests.md:30 vs :111 | lint.yml installs only requirements-dev (browser tests skip) | TRUE-PROBLEM | -> "the test suite (without the browser tests, which skip there)" |
| d7 tests:34 "no usage data sent" | tests.md:34 | same paragraph says not measured | TRUE-PROBLEM | -> "usage reporting is switched off, see the network paragraph below" |
| d7 tests:46 owner approves | tests.md:46 | not enforced | TRUE-PROBLEM | "approves" -> "is meant to approve; nothing enforces this" |
| d7 tests:48 "harmless" | tests.md:48 | no evidence | TRUE-PROBLEM | -> "the author expects this to be harmless" |
| d7 tests:52 "a few" vs 22 skips | tests.md:52 | vague | TRUE-PROBLEM | -> "the tests ... that use the browser helper" |
| d7 tests:74 Windows lock | tests.md:74 vs versions.md:75 | dev-win was installed, browser lock was not | TRUE-PROBLEM | -> "Windows browser lock file" |
| d7 tests:79 vs versions:9 collect command | tests.md:79 | `-q` prints per-file lines, no total (versions.md says so) | TRUE-PROBLEM | tests.md now says without `-q` the last line gives the total; `-q` gives no total |
| d7 tests:78 vs versions:9 skips 3 vs 2 | both | two runs, not reconciled | NOT-A-PROBLEM as a contradiction (different runs), made plain | versions.md:9 now says they are different runs or set-ups, skip count per commit unknown |
| d7 tests:79 vs versions:9 2516 vs 3883 | both | 1,367 tests unexplained | TRUE-PROBLEM (words) | versions.md:9: "older counts (2465, 2516) are from older commits; growth to 3883 not itemised" |
| d7 tests:111 vs 30,36 CI | tests.md:111 | "no CI run seen" vs Semgrep CI run | TRUE-PROBLEM | -> "no CI run of these tests has been seen (the only CI run reported here is the Semgrep one)" |
| d7 tests:129 "below" | tests.md:129 | section is above | TRUE-PROBLEM | "below" -> "above" |
| d7 tests:131 n8n "below" | tests.md:131 | in docs/n8n-recipe.md | TRUE-PROBLEM | pointer added |
| d7 tests:127 receipt vs request number | tests.md:127 | two meanings? | NOT-A-PROBLEM (README: receipt = desk's first note; request number = sender's label) | added "Receipt" term to Terms for developers |
| d7 why:3-6 order | why-this-code.md | two different orders | TRUE-PROBLEM | line 3-4 now gives the same order as 5-6; "order tried" -> "order the author aimed for" |
| d7 why:13 crash test file | why-this-code.md:13 vs tests.md:123 | test_crash_points.py checks hook names (flag-file helper child, ALL_HOOK_POINTS called by desk.py, second crash in start-up); each-point crash tests are in test_flow.py (test_crash_resume_each_point, parametrized) | TRUE-PROBLEM | row now names both files correctly |
| d7 why:13 "No n8n-only result" | why-this-code.md:13 | misleading | TRUE-PROBLEM | -> "n8n alone was not shown to fail or to work" |
| d7 why:19 "repeated" | why-this-code.md:19 | real-services.md says never run | TRUE-PROBLEM | -> "can be run against real services later (never run so far)" |
| d7 why:20 "could replace" | why-this-code.md:20 | untried | TRUE-PROBLEM | "might replace" |
| d7 why:28 "ships one real CRM kind and one AI kind" | why-this-code.md:28 vs versions:26 | both only run on stand-ins | TRUE-PROBLEM | -> "ships adapters for one CRM service ... tests run these against stand-ins only; the one real-service try was the probe" |
| d7 why:28 vs n8n:8 licence | LICENSE read: you may not change the software | adopter steps need permission | TRUE-PROBLEM | sentence added saying changing it needs the licence holder's written permission |
| d7 n8n:10 vs 21 licence key | n8n-recipe.md:10 | "no n8n licence key" vs free community licence | TRUE-PROBLEM | -> real items allowed are the owner account and the free community licence |
| d7 n8n:13 "only" | n8n-recipe.md:13 | proof needs more | TRUE-PROBLEM | "only" removed, pointer to section 3 |
| d7 n8n:36 | n8n-recipe.md:36 | reason rested on unchecked expectation | TRUE-PROBLEM | -> "was not tried here, so it is not used" |
| d7 n8n:44 timeout | n8n-recipe.md:44 | value not given | TRUE-PROBLEM | n8n/desk-form.json says 15000 ms: now "15 seconds"; sentence split |
| d7 n8n:54 "Never Error" | n8n-recipe.md:54 | untried | TRUE-PROBLEM | "(not tried)" |
| d7 n8n:67-68 vs 46,52 "answered with an error" | n8n-recipe.md:67-68 | which error? | UNRESOLVED | the sentence rests on the author's run and no log is shipped; code cannot tell. Left unchanged. Needs the author. |
| d7 n8n:76 vs 77 | n8n-recipe.md:76 | 400 is also an answer | TRUE-PROBLEM | "whenever the desk answered with a success status" (also at :46) |
| d7 n8n:78 "raise tries" | n8n-recipe.md:78 | untried advice | NOT-CHANGED | kept; low risk, listed here |
| d7 real:5/7 duplicate; real:9 vs probe .test | real-services.md | may vs was | TRUE-PROBLEM | merged lines 5 and 7 first sentence; `.test` now "HubSpot refused a .test address in the probe" |
| d7 real:11 vs probe:48 scopes | real-services.md:11 | code: crm_hubspot.py top comment says /crm/v3/owners is not used by the desk | NOT-A-PROBLEM for the desk, words fixed | real-services.md says the desk does not use the owners list, only the probe; probe doc says the same |
| d7 real:16 Gmail/Workspace | real-services.md:16 | both Google | TRUE-PROBLEM | example removed |
| d7 real:16 "only counts" vs masked tables | real-services.md:16 | | TRUE-PROBLEM | -> "counts, a pass/fail table and a per-lead table (failure tables mask e-mail addresses)" |
| d7 probe:4 "6 or 7" | hubspot_probe.py:181-215 | 6 when owner list gives no owner (owner write skipped), else 7 | TRUE-PROBLEM (unexplained) | explained from code |
| d7 probe:23-25 arithmetic | hubspot_probe.py:45-47,111 | normal calls limited to 7 attempts, cleanup to 8; normal path = 6 steps + delete = 7 | TRUE-PROBLEM | rewritten; spare call pays for a retry OR the archive fallback |
| d7 probe:33 "agreed to 7" vs 8 cap | hubspot_probe.py:15 (flag must equal planned count 7) | | TRUE-PROBLEM | "7 planned calls; hard cap is 8" |
| d7 probe:3 desk combined call | crm_hubspot.py | probe does not test combined call (already said at :31) | TRUE-PROBLEM (placement) | moved into the first sentence |
| d7 probe:66-68 real domain | | example.com is reserved | TRUE-PROBLEM | reworded; verified facts (OPEN accepted, delete 204) moved up from the UNVERIFIED paragraph |
| d7 probe:71-72 hearsay harmless | | | TRUE-PROBLEM | "the author thinks this does not matter" |
| d7 versions:9 limits | versions.md:9 | "no test failed" limit | TRUE-PROBLEM | restated with the limit in the same sentence; cell split into short sentences |
| d7 versions:10 SQLite machine | versions.md:10 vs :75 | | TRUE-PROBLEM | "machine not recorded; the Linux container had 3.46.1" |
| out-d9 f3c39cf8 3683/200 not in docs | tests.md, versions.md | | TRUE-PROBLEM (doc has no such number) | added to both, marked "reported by a separate run; no log is shipped" |
| out-d9 tests:79 "10 tests" vs 24 | tests.md:79 | different commit and file set | NOT-A-PROBLEM (different commit); added the later numbers (24, 44, 4) with the same marking |
| out-d9 tests:80 60 vs 113 | tests.md:80; code: tests/test_portal_lead_pages.py helper (browser helper) is imported by layout, long_values, phone_layout, drawer_long_name | evidence run counts ten files, doc eight | TRUE-PROBLEM | words now say the 166 / 113 figure comes from the extra files using that helper |
| out-d9 tests:80 line numbers | tests.md:80, 22 | doc said 110, 27, 113, 171, 204, 257, 175, 488 "read on this commit"; the files here have the skip at 115, 32, 179, 211, 264 | TRUE-PROBLEM (stale numbers) | all line numbers removed |
| out-d9 README timing / 3.13 | README.md:130 | not my file | n/a (group A); the same facts added to tests.md | |
| out-d8 rows 1 and 8 | contract.md, docs/limits.md only | not in my files | n/a | |

## Readability edits (8 worst plus the small ones)

1. tests.md:30 split sentences, Action and SHA explained; 2. tests.md:42 exit codes in order (3 before "any other"); 3. tests.md:19 SonarQube explained; 4. tests.md:26 D2, blind explained; 5. tests.md:46 gitleaks aside marked as aside; 6. why-this-code.md:28 six steps as a numbered list; 7. n8n-recipe.md:70 "owner" -> reader, old rule explained, "line result" -> field; 8. hubspot-probe.md call arithmetic; 9. versions.md:9 cell split; 10. real-services.md:16 split, "load", "hard", header and SPF explained; plus: intro defines the desk and n8n, D1b defined in the table, "put" -> "write request", "session storage" explained, "open" in /counts, "book" -> desk's own records, CRLF defined, EXPECT_MORE removed, "REST" explained, GDPR explained, "upsert" explained, symbolic link and process substitution explained, ruff rule groups, MPL-2.0 in words, B101, stray space in versions.md.

## Facts added (out-d9 "findings no doc mentions", my files)

Added to tests.md after the 2329 bullet (marked as reported by a separate run, no log shipped): 3683 passed / 200 skipped split 166+30+4 on f3c39cf8; about 20 minutes; Linux Python 3.13 one run 3684 passed 199 skipped; one run per commit so no flake rate; the four on-purpose skips (the Windows-only, 3.13-only, load-measurement and root-user ones are in test files: checked, test_path_confinement.py:284, test_n8n_api_url.py:510, test_stall_eviction.py:526, test_server_hardening.py:224); basetemp inside TMPDIR (56 tests); do not run git pull/stash/checkout while a run writes its output file.

## CODE-LOOKS-WRONG

None. Observation, not a code bug: tests/test_crash_points.py `_CHILD` crash test kills a small helper process, not the desk (the docs already say so).

## NOT-ADDED

- out-d9 B.7 (path object with `__fspath__` returning int/None raises TypeError), B.8 (hard links bypass folder limit), B.10 (LEAD_DESK_PATH_ROOTS=/), B.9 (foreign `tools` on PYTHONPATH): belong to docs/settings.md or README (not my files); lead should place them.
- B.12 (wall-time spread 67 s vs 37 s): unexplained, no doc effect.
- "the author / project lead / project owner / repository owner / licence holder" unified: not done, I do not know which person each stands for; licence holder is now defined (LICENSE top) in why-this-code.md and n8n-recipe.md only. Needs the owner.
- tests.md:36 run id and commit 15b8b15e: cannot be opened by a reader; left, no replacement fact known.
- tests.md:92 and :129 (P10) long paragraphs not split (time cap); n8n-recipe.md:67-68 "which error" unresolved (see above); remaining (e) rows (tests.md:34, 78-80, 90; hubspot-probe:41-43; versions.md:37, 40, 57, 61, 69-71) not touched.

true problems 41 (fixed 40, 1 unresolved), not-a-problem 5, readability edits 10 main plus about 20 small
