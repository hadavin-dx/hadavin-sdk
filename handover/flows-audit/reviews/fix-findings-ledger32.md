# fix-findings-ledger32 (flows-audit fixer, round 32, non-security path, beyond the round cap)
Input: reviews/findings-ledger-reader-r32.md (items a to z, 28 Majors). Edited ONLY FINDINGS.md (ten rows plus one new bullet) and LEDGER-ROWS.md (the same ten fix cells). No row marked FIXED-VERIFIED. No commit, no push. Cited rules: R-numbers of the BRIEF-PREAMBLE apply (honesty, no secrets, wording clear for non-technical readers, fix-dont-defer).

## What was NOT done or NOT checked (said first)
- Nothing was run against a real Postgres, n8n, HubSpot or the real take folder. Every new or changed command block was tested only with stand-in functions or stub files in a scratch folder. The new password block of F-011 (item m) was tested only with a stand-in psql (the password is not in its arguments); it is marked UNTESTED against a real server in the row.
- The inputs only the studio lead can give stay "LEAD FILLS" with a due time: the role the node Claim uses (F-002), the test-log path for F-007 (Tue 17 Nov 07:44Z, 13:14 IST), the HubSpot menu path and the probe's minutes (F-018, by Wed 05:45Z and Tue 07:00Z), PGCONN_SELECT_ONLY (Wed 05:45Z), $EXPORT command (Q31 item 140), the grep runner (Q31 item 26, default nobody). I invented no value.
- Whether F003-4 still prints PASS after the F-007 and F-031 edits to the run sheet is UNVERIFIED (the row says so and tells the lead to type it once more).
- The check counts for tools/ were run once at the end; check_secrets file count changed from 2964 to 2966 between runs (extra files in the tree, not mine to explain; PASS both times).

## Per item
- a F-002 fixed: `unset BEFORE21` at the start of step (0) and in BOTH FAIL branches (digit-test branch and guard branch); step (2) now also tests digits only. Stub test: psql error text leaves BEFORE21 unset; a stale value is cleared on a guard failure.
- b F-002 fixed: the spliced paragraph now starts a new sentence "THE FOUR TEST BLOCKS: on the patched, filled, imported and activated copy, ...".
- c F-002 fixed in the file text, needs LEAD FILLS: $FLOWS_ROLE defined as the role behind credential n8n-publish-pg; the lead writes in the test log by Wed 18 Nov 05:45Z (11:15 IST) which credential and role the node Claim uses and checks it equals $FLOWS_ROLE; otherwise T21 must not be typed.
- d F-002 fixed: "the take" (and take folder, database, mailbox) defined in WORDS USED.
- e F-002 fixed: item (3) now says the wait value is a copy of the Tuesday decision (Q31 item 25, Tue 06:00Z), not a Wednesday decision.
- cross-row F-002 fixed: RATING BASIS says F-003 and F-037 are rated by the rubric, not by ORDER 007.
- f F-003 fixed: new text "ANCHORS TESTED ONLY ON A SCRATCHPAD COPY", F003-3 named as the proof the apply happened, saved F003-1 output as proof of a clean apply; the status cell now requires the F003-1 PASS output saved BEFORE the apply.
- g F-003 fixed: new bullet "GO ROW 6, WHICH ROWS COUNT" directly under the WEDNESDAY CLOCK in FINDINGS.md (F-002, F-007, F-031 out; F-003 decides, item 89 due Tue 06:45Z (12:15 IST), default counts; F-037, F-008, F-029 count; F-011 and F-041 count with GO row 7; F-018 counts unless item 31 flags it out). F-003 points to it.
- h F-007 fixed: "two things", (c) dropped; one sentence says nothing else is LEAD FILLS.
- i F-007 fixed, needs LEAD FILLS: check-log path needed by Tue 17 Nov 07:44Z (13:14 IST) (the step 14 time).
- j F-007 fixed: one ORDER OF EDITS AT RUNBOOK STEP 14 list (F-007 table, F-031 sentence, F007-1, F007-2, F031-1, then F003-4 again).
- k F-011 fixed: the downgrade (b) command now prints `F011-B PASS` or `F011-B FAIL`; status cell updated. Tested with stub files (hit, no hit, empty REPO).
- l F-011 fixed: both mentions now say `F041-R7 NEEDS-READ`.
- m F-011 fixed, marked UNTESTED against Postgres: `\password` through -c replaced by a no-echo prompt into a variable and ALTER ROLE through psql's \getenv from standard input (no pipe, no password in arguments; tested with a stand-in psql; psql 16.15 here, 15 or later needed).
- n F-018 fixed: F018-7 now also counts toEmail lines holding an address-shaped literal (must be 1), lines left holding REPLACE_ME (must be 0) and two controls; wording says it does not prove the address is the desk's real one or that mail arrives. Stub tests: real-looking address PASS; intake address, empty, REPLACE_ME, plain text, unfilled $env expression all FAIL.
- o F-018 fixed: the lead key is made at the send (07:00Z, 12:30 IST); the lead types it right after the send; item 141 (b) asks only who types it.
- p F-018 needs LEAD FILLS (written in the row): the probe's minutes and place, by Tue 17 Nov 07:00Z (12:30 IST).
- q F-018 fixed: item 54 described one way everywhere: (a) take command Wed 05:45Z, (b) HubSpot search method Tue 04:00Z; reader and key are item 141 (b); the menu path has no Q31 item (LEAD FILLS).
- r F-018 fixed by enforcing the claim: new SENT18 (typed `date +%s` right after the send); F018-10B refuses a non-number and prints FAIL unless the seconds since the send are at least WAIT_S. Stub tests: 100 s PASS, 1 s FAIL, bad SENT18 or WAIT_S refused.
- s F-031 fixed: N1 and N2 are Q31 items 138 and 139 (already in QUESTIONS.md); PGCONN_SELECT_ONLY needed by Wed 18 Nov 05:45Z (11:15 IST).
- t F-031 fixed: status cell (still starting with OPEN) says first that the Blocker can close only as "closed as disclosed, flaw remains".
- u F-037 fixed: one runner statement: NOBODY unless Q31 item 26 is answered (audit recommends the studio lead). F-008 and F-029 already said nobody.
- v F-037 and F-029 fixed: N3 is Q31 item 140 (three places in F-029, two in F-037, plus the words list); the $EXPORT half runs only after import and export back; item 140's default is stated.
- w F-008 fixed: K8 keys-present count added for the three flows and for mf-recovery.json (2 or more each, else FAIL) so a changed spacing is told from a switched-off setting; fill_flows' json.dumps(indent=2) read in the source (not run on real files, UNVERIFIED there); "inside the re-pin" wording; take_check.sh reads the unfilled patched folder and the block reads $FILLED; item 141 (a) named. Stub tests: correct spacing PASS; changed spacing FAIL with keys-present 2; switched-off setting FAIL.
- x F-041 fixed: the garbled DETAIL paragraph is replaced by "TWO WAYS TO CLOSE THIS ROW" (wording route, downgrade route), parenthesis closed.
- y F-041 fixed: who owns the paste (the studio lead alone, from TAKE-CHECKLIST.md at the re-pin commit) and which text is compared (the file in git); the comparison itself is the lead's look and is stated as UNVERIFIED by command.
- z F-041 fixed: STEP 4 refuses an OWNER_SHEET value starting with `<`. Stub tests: file named with `<` FAIL, real file PASS, empty REFUSED.

## Commands run in handover/flows-audit (last lines, saved in the scratchpad file final-outputs.txt)
- python3 /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/compare14.py FINDINGS.md LEDGER-ROWS.md: `45 45 differences: 0`
- python3 -I tools/count_findings.py: 45 rows, `sev {'Blocker': 5, 'Major': 5, 'Nit': 35}`
- check_refs: `PASS 5190 references`; check_names: `PASS 655 rows`; check_secrets: `PASS 0 hits in 2966 files`; check_counts: `PASS 52 files / 655 nodes`
- ruff format --check .: `1091 files already formatted`
- Own cell check: FINDINGS rows have 10 cells and LEDGER rows 9; for the ten rows the FINDINGS fix cell equals the LEDGER fix cell byte for byte; every FINDINGS status cell starts with OPEN.

Files changed: /home/user/hadavin-sdk/handover/flows-audit/FINDINGS.md, /home/user/hadavin-sdk/handover/flows-audit/LEDGER-ROWS.md, and these two report files. Backups of the originals: scratchpad w32/FINDINGS.before and w32/LEDGER.before.
