# fix-rwct39: fixer report for read r38 (3 Majors, 2 weaker points) and open items of read r22
Files edited: CLAIMS-TABLE.md and RUNSHEET-WORDING.md only. Static work; nothing run except the checkers. Not committed.

## Changes (read r38, each checked against the cited sources first; the reviewer was right on all three Majors)
- M1, A-040, A-041, A-042: UNSUPPORTED -> OVERSTATED. Checked: VIDEO-RUNSHEET.md lines 39, 50, 62 describe a plan or instruction; n8n-table-screen/mf-table-screen.json line 23 does select seven columns (incl. alert_attempts), so "seven" is true for v1 and stale for v2, not false. A-042 keeps its second verdict (not counted). Verdict index lines for rows 13 and 18 updated.
- M2, B-054: UNSUPPORTED -> UNTRACED. Checked: PLAN-4-NLITE-FROM-LEAD.md line 122 is a forward-looking WP4 test list; V5-README.md line 17 "not run" is a status. To-do row 52 and its index line updated; B-054 added to the "14 others added on purpose" list (now 15).
- M3, B-179: first verdict SUPPORTED -> OVERSTATED; the CrmIdOk test is now the second verdict (not counted). RW rows B-179 and B-179b note reworded to say so. B-179 has no to-do row, so it joins the list of rowless OVERSTATED claims (16 -> 17).
- Weak point B-197: UNSUPPORTED -> OVERSTATED (by relay), not UNTRACED: PUB:5 is a file we have and PUB:20/PUB:31 give a different but relayed figure (README table quoted, not seen), the same class as A-019/A-051 (the line 530 precedent). Row 74 and index line updated.
- Weak point B-180: no change. Checked: demo/n8n-tests/test_crmid_regex.py exists; PASS comes only from the README and was not re-run, which is exactly the RELAYED-ONLY definition.

## New totals (python3 claims-count.py)
SUPPORTED 88, RELAYED-ONLY 64, OVERSTATED 89, UNSUPPORTED 10, UNTRACED 79; 88 + 64 + 89 + 10 + 79 = 330. Lane A 21/23/42/3/11 = 100; Part 7 67/41/47/7/68 = 230. Recounted by an independent script: same. Updated in CT (header line 15, bullets on UNTRACED/sum/Count, rowless 233 = 87+63+66+17, traced 251, 82+15 = 97 rows' claims, flagged 96 unchanged, UNTRACED A/B 78) and RW (verdict line 33, count line 483).

## Read r22: already fixed in earlier rounds (checked against current text)
Item 1 (N-5a reworded, n8n/flow/lead glossed, no recovery number), 2 (one speed-up rule in row (u), N-10, N-11b), 3 (A-008a "Scenes 1 to 4" dropped, round 23), 4 (B-195, B-197 carry "reported by another test session; we have not seen its raw files"), 5 (CT lists steps 2c, 3, 4, 6), 6 (stale counts: RW table 55/30/91/9/14 = 199 matches; A-083 wait "A-073a only"), 7 (step 2 states the real order), 8 (B-010 "built to, not observed"), 9 (S9-2, S9-3 and challenge number defined at RW line 93, CT line 14). Lower points: every UTC time now has IST (re-scanned by script; only same-sentence ranges remain); "17:05Z" has IST; B-062 V-11 cross-reference, B-032 note, B-127 (lead decision, not applied), B-077 ("person who receives the alerts") no longer match the stale text.
Still open: none fixable here. Declared Blocker (nobody named for voice rows, screen capture, mailbox emptying) needs the lead naming people (RWQ-10 / Q31 item 100).

## Commands (from handover/flows-audit)
- claims-count.py: offenders 0, ids 330 unique 330.
- check_rw_ct_pairs.py: paste strings in RW 144, found word for word in CT 144, not found 0.
- check_runsheet_paste.py: 96 flagged with no missing row, 78 UNTRACED A/B (65 without row), RESULT: PASS.
- check_refs.py PASS 5184; check_names.py PASS 655 rows; check_secrets.py PASS 0 hits in 2826 files; check_counts.py PASS 52 files / 655 nodes; ruff format --check . 952 files already formatted.

## Not checked
r22 lower points on arithmetic wording ("four hours add up to 4.5 hours" now reads "durations") were read, not recomputed. Source-side issues from r38 (AGENT-SCOPE:7,9 and DECISION-one-store.md:23 say saved runs ON while all 8 flows say none; OWNER-STEPS-realrun-v3.md "count: 13" lists 14) are in files I may not touch. Other files in flows-audit (README, STATUS-BOARD, REPORT) may still quote the old totals 89/64/84/15/78: not searched or edited.

## Decisions for the lead
1. N-5a has no lane row (r22 item 1 asked for one). Adding a claim row would change the total 330 everywhere; I left it, since the string is hedged ("built so that", "By this design") and CT line 70 says it is no recovery claim. Say if you want a row.
2. B-197: I chose OVERSTATED (by relay) over UNTRACED; switching is a one-word change plus counts (O 88, T 80).
3. Source-side fixes for AGENT-SCOPE, DECISION-one-store, OWNER-STEPS-realrun-v3 (above) and any other file quoting the old totals.
