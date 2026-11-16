# fix-findings-ledger26 (fixer, round 27): five Majors of reviews/findings-ledger-reader-r26.md

EGM skipped: wording and check-command edits to two audit files (no product code); the lead runs the review of the result. Not committed. Nothing was run in n8n; scratch tests used copies of made-up files.

## What failed or is uncertain (first)
- Reviewer words were checked against the text before editing. M1: the rubric already had a one-line narrow-route clause; the real gap was that it did not say how F-001 and F-037 are rated. M2, M3, M4, M5 were confirmed as written.
- THE F-001 / F-037 RATINGS ARE NOT ONE RULE (kept, listed for the lead): by the narrow-route clause F-001 would be a Blocker by rubric (its own evidence cell says so) or Major if the psql stop is accepted as the guard; it is Nit only because the studio lead dropped the patch (Q17-3, Q16). F-037 is Blocker by the clause. I kept both ratings and changed no count.
- Not run: the typed commands on the real tree (REPO, FLOWS, FILLED, EXPORT are LEAD FILLS). $NEW is unnamed, so which extra files the real $FLOWS folder holds is UNVERIFIED (the --include makes this harmless).
- Not read: the other 38 rows were not re-read cell by cell; the compare script covers severity, status, summary and fix cell only.

## Changes
- M1: FINDINGS severity rubric: new NARROW-ROUTE CLAUSE (definition, how F-037 and F-001 are rated, the inconsistency, no count change); pointer in HOW THE RATINGS point 1; F-001 fix cell (both files) ends with a RATING NOTE.
- M2: F-042 and F-043: fail-closed PASS LINE (variables, one command with `test -n`, `test -f`, FOLDER-OK, `grep exit $?`, positive control count 2) placed in the fix cell (both files); the old one-line `cd "$REPO" && grep` text in the evidence cells replaced by a pointer.
- M3: F-029 and F-037 (both files): every `grep -rlF` carries `--include='mf-*.json'`; the control sentences say the lists hold only the four take flow files.
- M4: FINDINGS top: "WHAT THIS IS" (5 lines) and "COMPANION FILES" (one line each) before the READ-FIRST list; READ-FIRST title no longer says "ten" (it has 12 bullets); the four-clause line (GO test / Row 4) split into two bullets, same content.
- M5: FINDINGS point 5 gets (7) THE WEDNESDAY SET: Q31 items 25 (Tue 06:00Z (11:30 IST)), 50 and 82 (Wed 05:45Z (11:15 IST)), plus item 54 (not in the review's list; Row 4 does not run without it); point 6 and the item-25 pointer adjusted.
- Minors: BM cites: ClaimStuck BM:98-99, AlertClaim BM:104-105 (the node starts one line before the SELECT the text describes, so both lines are now cited), CrmIdOk links BM:68-70 (checked against build_mainframe.py: Qualify/LabelOk 68-69, CrmIdOk 70). IST added after the quoted headings 14:15Z (19:45 IST), 10:58Z (16:28 IST), 11:40Z (17:10 IST), 15:00Z (20:30 IST), 14:35Z (20:05 IST), 12:33Z (18:03 IST), 8+2+2+1+1+1 uses in FINDINGS, 3+3+1 in LEDGER-ROWS. LEDGER-ROWS history bullet added.

## Commands and output (from /home/user/hadavin-sdk/handover/flows-audit)
- `python3 .../scratchpad/compare14.py FINDINGS.md LEDGER-ROWS.md` -> `45 45 differences: 0`
- `python3 -I tools/count_findings.py` -> `sev {'Blocker': 5, 'Major': 5, 'Nit': 35}`, all 45 (BEFORE 11, AFTER 34)
- check_refs.py `PASS 5184 references`; check_names.py `PASS 655 rows`; check_secrets.py `PASS 0 hits in 2825 files` (this file adds one more, rerun by the lead); check_counts.py `PASS 52 files / 655 nodes`; `ruff format --check .` -> `951 files already formatted`.
- Scratch tests (folder scratchpad/scratch26, copies of made-up files):
  - F-042/F-043, correct REPO: `FOLDER-OK`, `grep exit 1`; positive control prints `2`.
  - EMPTY REPO: prints nothing (no FOLDER-OK); control prints only `grep: /handover/demo/VIDEO-RUNSHEET.md: No such file or directory` on stderr and no `2`. WRONG REPO: nothing printed.
  - Planted hit ("the audit trail is complete"): `FOLDER-OK`, the hit line, `grep exit 0`.
  - The OLD form with empty REPO: `cd ""` succeeds, stdout empty, error on stderr only = the false pass the reviewer described (confirmed).
  - F-029 control over $FLOWS with --include: PLACEHOLDER lists mf-recovery.json and mf-sub-crm-mail.json; SUB_WORKFLOW_ID lists mf-form, mf-hook, mf-recovery; PG_CREDENTIAL_ID all four; SMTP_CREDENTIAL_ID mf-recovery and mf-sub-crm-mail; each `grep exit 0`. Without --include, PLACEHOLDER also lists V5-NODE-DIFF.txt and V5-README.md (M3 confirmed).
  - F-037 control with --include: lists mf-recovery.json and mf-sub-crm-mail.json. EMPTY variable (F-029 and F-037 forms): `grep exit 2` and `ls` error, so neither reads as a pass.

## Lead decisions and follow-ups (not mine to change)
1. F-001 rating: stay Nit by ruling (Q17-3), or Blocker/Major by the clause? Q31 item 21 asks about F-037 only; a new question is needed. No count changed.
2. TAKE-CHECKLIST.md check 7 (line about "approved by a person") still holds the old one-line form; its owner must use the new F-042/F-043 pass line.
3. Whether item 54 belongs in the Wednesday set (I added it).
4. Q31 item 25's default still breaks the Wednesday chain; the set only names it, it does not change the default.
