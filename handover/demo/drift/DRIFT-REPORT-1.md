# Drift report 1: README.md, docs/*.md, contract.md against the code

Target: /tmp/work/ro-clone, branch initial-code, head 43110e7 (read only; nothing edited, committed or pushed there).
Run through the Skill tool: `Skill(skill="egm:egm-drift-report", args="/tmp/work/ro-clone ...")` returned "Launching skill: egm:egm-drift-report" and loaded the instructions. No reviewer agents were dispatched (no Agent tool in this run); the file-by-file comparison below was done by the runner following the skill's steps (sequential, per document). EGM reviewer judgement of this report is still for the lead.
Studio rules used: R-numbers not looked up (no studio folder here; the brief said to ignore pointers to it). No model call, no spend, made-up data only.

STATUS: FINAL on the doc-vs-code pass. Test-suite run: see section 2 (updated at the end).

## 1. Differences found (failures first)

Classes: DOC WRONG = the code is right, fix the text. CODE WRONG = the text states the intended rule and the code breaks it. BOTH FINE = text and code differ in wording only.

Count: DOC WRONG 3, CODE WRONG 0, BOTH FINE 1 (listed in section 3), UNVERIFIED 4 (section 4).

### D1. DOC WRONG: portal.md says the masked search also finds request numbers
- Doc: docs/portal.md:5 says that while values are masked the search matches "only the company, the lead number and request numbers without an "@"".
- Code: src/lead_desk/portal_api.py:311-314 (and the same in the count query 325-328): with `by_email = 0` (masking on) only `l.company` and `l.lead_id` are matched; `r.source_ref` (the request number) is matched only when `by_email = 1`. The page sends by_email=0 while masked (src/lead_desk/portal/pages/leads.js:321-326, placeholder "Company or lead number" at line 289).
- Other documents already agree with the code: contract.md:122 ("the search never looks at request numbers or names while masked"), docs/tests.md:64 P10 ("a request number is not searched while masked"), docs/limits.md (matches only the company and the lead number).
- Evidence: `grep -n "by_email" src/lead_desk/portal_api.py` and the SQL lines above (quoted). Fix: docs-fixes.patch hunk 2.

### D2. DOC WRONG: contract.md start-up step (4) gives the wrong limit for an AI adapter's `timeout_seconds`
- Doc: contract.md:143 says the desk refuses an AI adapter whose `timeout_seconds` is "not a number above 0 or not below the stuck grace minus its margin".
- Code: src/lead_desk/desk.py:332-341 refuses it only when it is not a positive number or is above `MODEL_CALL_BUDGET_SECONDS` (src/lead_desk/constants.py:80, 9.0). The same contract.md at lines 40-41 ("9 accepted, 9.1 refused"), docs/limits.md ("above 9 s") and docs/settings.md already say 9 s. The grace-minus-margin wording would put the limit at 15 s, which the code does not do.
- Evidence: desk.py line 338 `if declared > MODEL_CALL_BUDGET_SECONDS:` quoted. Fix: docs-fixes.patch hunk 1.

### D3. DOC WRONG: docs/tests.md "Browser tests" list is missing a file
- Doc: docs/tests.md:27 lists the files that need Playwright: test_portal_browser.py, test_portal_lead_pages.py, three tests in test_portal_wording_and_masking.py, a few in test_mode_safety.py, test_portal_layout.py, test_portal_look.py.
- Code: tests/test_stage_confirm_browser.py (all of its tests drive a real browser through `_browse` imported from tests/test_mode_safety.py:108, which does `pytest.importorskip("playwright.sync_api")` at tests/test_mode_safety.py:109; its docstring says "skipped when playwright or its browser is missing"). It is not named in tests.md, README.md or any other document, so a reader who skips browser tests is not told this file also needs Playwright (and the masking-promise sentence "P10 rests on them" is incomplete for the stage-confirm question).
- Evidence: `grep -rn stage_confirm docs README.md contract.md` returns nothing; `grep -n importorskip tests/test_mode_safety.py`. Fix: docs-fixes.patch hunk 3.

## 2. Test counts and run (README/versions.md/limits.md claims)

Claim (docs/limits.md:67, versions.md): full suite 2026-11-12, Windows Python 3.13: 2449 passed, 15 skipped; Linux Python 3.12: 2462 passed, 2 skipped (2464 tests either way).
Observed here: `python -m pytest --collect-only -q` on a scratch copy (/tmp/work/drift-copy, Python 3.13.18, Linux, lock file requirements-dev.txt installed with --require-hashes) collects 2465 tests, one more than the claimed 2464. The same text says edits after those runs changed "one test file", which would explain one added test, so this is recorded as BOTH FINE (section 3, B1), not as drift.
FULL RUN RESULT: see the line "FULL RUN" at the end of this file (filled in when the run ended).

## 3. BOTH FINE (differences that are only wording or timing)
- B1. Test count 2465 collected against 2464 claimed (section 2). The doc states the claim is for the runs of 2026-11-12 and names later test-file edits. Not a defect.

## 4. Not verified (cannot be checked from this clone, stated honestly)
- U1. Every figure tagged "tried once by the author, logs not shipped" (150 simultaneous connections on the Windows computer, refused connections from about 300, the Windows/Python 3.13 run of 2449 passed/15 skipped, the Linux real-kill-under-load run, the n8n runs on 2026-11-09, versions.md n8n 2.46.6 / Node 24.22.2) and the HubSpot probe results in docs/hubspot-probe.md (one free account, scopes, `MISSING_SCOPES`). No logs exist in the repository.
- U2. Windows-only text: PowerShell commands in README.md, `scripts/start_all.ps1` output, the two-minute port wait, `SO_EXCLUSIVEADDRUSE`, the 2-second refused connect (contract.md). Linux only here.
- U3. Browser behaviour described in docs/portal.md, docs/limits.md and contract.md (30-second eye button, session storage, "34s ago" tooltips, layout at 1300 px, light/dark look): the Playwright tests were not run (Playwright is not installed here). Only the strings were matched in src/lead_desk/portal (banners, button labels, page names, REVEAL_MS = 30000, the `ago` format, sessionStorage use all exist).
- U4. n8n behaviour in docs/n8n-recipe.md (n8n not available). Only the shipped workflow files were compared: 3 nodes each, paths desk-form / desk-webhook / proof-run, retry on fail 3 tries 1000 ms, timeout 15000 ms, desk URL on 8765, proof workflow posts through port 5679, source_ref from submission_id / message_id: all match.

## 5. What was compared and found to match (so a re-run knows what was covered)
Not drift, listed only as coverage:
- Settings (docs/settings.md, contract.md "Config environment names", README): every `DESK_*`, `REAL_*`, `DPLD_*`, `LEAD_DESK_LOAD_*`, `GITLEAKS_BIN`, `N8N_*` name in the three scope sets exists in code or scripts (script `/tmp/work/tok.py`, token-existence check over all backticked identifiers, files, constants, routes and test names; only non-code placeholders such as `GET /ui/<file>`, n8n's own `N8N_PORT` and the historical `MISSING_SCOPES` answer were unmatched). All Config defaults match docs/settings.md: db_path ./data/desk.sqlite3, bind 127.0.0.1, port 8765, fakes 127.0.0.1:8766, send timeout 5.0, size cap 65536, stall 120, qualifier recorded, outbox http, crm fake, later_mode off; also SMTP 2525, SMTPP 587/465, IMAP 993, HubSpot timeout 4.5 and 429 retries 2 (max 5), live defaults (version 2026-10-21, effort low, timeout 8, tokens 64), REAL_PERSONS 12, drain 150, mail wait 90, settle 10.
- Limits in docs/limits.md and contract.md against constants.py/gate.py/config.py: 9 s call budget and 15 s margin (9+15=24 below the 25 s smallest grace), 30 s stuck grace, 5 tries (`SEND_MAX_ATTEMPTS`) with waits 1, 2, 4, 8 s, worker caps 4/8/8/4, 256 connections, 1024 threads, 4 x 1024 + 96 = 4192 files, 10 s header and body deadlines, 5 s reply write, 2 s eviction idle, 1 s Retry-After, 32 in-flight requests with a 5 s wait, 8 drive places, 8 portal requests, listen queue 1024, 10 s write deadline, 15 s request deadline, reaper pass 10 s and interval 1 s (10 + 27 + 18 = 55 s), copy-to-CRM waits 10/60/180/420 s and 5 tries, 3 failed decisions then `review`, limits on the lead flow file (16384 bytes, 1-20 owners, 3-12 steps, 32/64-character labels/names, nudge up to 2678400 s), 50 duplicates/later messages shown, field limits, exit codes 1-5 and the reset script's exit codes 2, 3, 4 (reset_check), 5, 6, 8,000,000-byte ledger and 8-character key minimums.
- Live behaviour, README "Try it" run on the scratch copy (`bash scripts/start_all.sh keyed`): /counts answered HTTP/1 200 with all 0; feed form 1 gave 201 verdict new; again gave 201 replayed true; webhook 1 gave 200 duplicate; /counts received 2, new 1, duplicate 1; `/fake/outbox` count 1; `/` and `/health` answered 404; `/ui` answered 308 to `/ui/`; the 100-request burst from limits.md gave STATUS 201=1 200=99, one email; `scripts/reset.sh` exited 0. HTTP reply shapes in contract.md checked live: GET /leads/{id} (lead, followup, owner, step, reminder), GET /review, /api/ui/summary, /api/ui/leads keys, bad_step, bad_expected, 405, 501 for TRACE, 404.
- Ten crash points (A, A2, B, L, C0, C1, D1, D1b, D2, D3) plus N1 match `hooks.ALL_HOOK_POINTS`; the test names quoted in all docs (every `test_*` token and glob) exist in tests/; workflows, dependabot, coderabbit, sonarcloud and gitleaks files exist; lint.yml steps match the list in docs/tests.md; schema triggers, indexes, view, columns, CHECK, user_version 1 match contract.md.

## 6. Hardcoding / "dev" stage check
Not part of this lane. No occurrence of "dev" as a stage name was looked for beyond what the documents contain.

FULL RUN: NOT COMPLETED. The runner stopped my pytest process at about 33-40% (all dots, no failure seen up to then; the machine was shared with other pytest runs, so it was slow) to meet the handback. No pass/fail count is claimed. Only the collection count (2465) is evidenced.
