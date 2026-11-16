# Change log: OWNER-STEPS-q16-rows.md, apply lead answer Q27 (ORDERS.md line 155 onward, 14:15Z, 10 items)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os4/OWNER-STEPS-q16-rows.md
Text only. Nothing was run, no file other than the sheet and this log was edited, no git commit.

## Failures and uncertainty first
- Nothing verified. Every Q27 value is the lead's word, copied; the sheet is still UNVERIFIED and "Re-check done" is still NOT YET.
- Item 8 ("decision 4"): the sheet contained no "decision 4" or "decisions 1 and 4" (searched "decision 4", "and 4"). It already says "decision 1" (line 37). Nothing to drop; the wrong wording lives in ORDERS.md Q25-8 and QUESTIONS.md Q27 item 8, which I may not edit.
- Times I derived, not given by Q27 (marked UNVERIFIED in the sheet): Wed 18 Nov practice run about 06:00-07:00Z, Row 4 07:00-07:30Z, rehearsal 07:30-09:30Z, Step D message 1 about 07:30Z, Step D message 2 after about 11:00Z. They come from Q27 item 6 durations (1 h, 0.5 h, 2 h, 1 h) counted back from the 09:30Z / 10:00Z times and the F-002 check at 07:30Z. Owner list items 4 (settings-file comparison) and 5 (key revocation) have a day (take day) but NO clock time: Q27 says "the same day" only; written as "lead sets".
- The meaning of "the challenge" (owner types y, the challenge and end) is not explained in the files I read; the sheet says the lead explains it in the chat.
- The Q26 guard-change risk: Q26 named a 2-3 h risk for the guard design change; Q27 item 4 says the decision is made but gives no new figure; I kept it as an open risk until rounds 23 and 24 are merged.
- Q27 does not answer V1, V2, V8, V9, V10, V11, V16, the mailbox-emptying method (V4), the command lines of the scripts, the place of n8n_drive.py, or the place of the ledger of paid model calls (not the blocker ledger). They stay OPEN in the table.

## Open questions for QUESTIONS.md (lead)
1. Step A: removed by Q25-7; Q27-10 says "if kept"; lead confirms it stays removed. (Sheet lists it as owner item 3 with exactly that sentence.)
2. Practice run vs short re-smoke: Q27 items 6 and 9 read as two runs (short re-smoke Tue, practice run 1 h Wed morning with T19-T21), while Q26 and Q17 treated them as one; also Q26 put the practice run on Tuesday. Confirm at box R9.
3. Owner list items 4 and 5: clock times (S9-2 settings-file comparison, S9-3 key revocation).
4. What "the challenge" is, in words the owner can follow.
5. Is the 2-3 h risk of the guard change (Q26) still counted now that rounds 23 and 24 are in progress?
6. Where is the ledger of paid model calls (separate from egm/BLOCKER-LEDGER.md)? And the command lines of the scripts.

## Changes (Q27 item -> sheet)
1. Scripts: V7, T6, R6 and the definitions: n8n_start.sh, n8n_kill.py, run_real_check_n8n.py on local take branches (merge head take/nlite-merge-m1 706b34d, rounds 23/24 in progress), lead copies at re-pin and writes the sha then; n8n_api.py and the post-twice script marked UNKNOWN, "lead provides or writes at re-pin (a short curl script), sha then".
2. Credentials: L3 fixed (the lead confirms the credentials exist, does not create them; no new ask to the owner); V3, R5, order step 5, owner block; HubSpot token scopes: lead asks once at take prep (order step 9); address setting names and mailbox words: AT RE-PIN (V4, R2, L3).
3. V5, schedule, T8: lead records via Playwright; owner edits and posts on LinkedIn, Wed 18 Nov 15:00Z (20:30 IST).
4. V14, risk paragraph, r22 text: flock lock-file guard decided yes 2026-11-16 about 13:05Z, round 23 replaces r22's scanner; order step 1 now includes rounds 23/24.
5. V6: egm/BLOCKER-LEDGER.md with the ledger_check command (forward slashes); lead decides, owner sees the table.
6. V13 and NO-GO path: re-pin by Mon 23 Nov 07:00Z (12:30 IST), with the 1 h + 0.5 h + 2 h + 1 h reason. Removed the old "V13 is the real latest re-pin" sentence.
7. V12, order step 13: GO decision rule between 09:30Z and 10:00Z; slip to next day at same times, allowed until Mon 23 Nov 12:00Z; scene 4 cut if no takeover inside 3 minutes.
8. One number: already "decision 1" everywhere (see failures).
9. GO / NO-GO paragraph rewritten: T19-T21 not part of Tuesday; F-011 and F-041 fixed or downgraded with evidence before Tue 14:00Z else automatic NO-GO; F-002 lifted at Wed practice run, NO-GO if open Wed 07:30Z. R9 and the Tue/Wed run reading updated.
10. Owner block: new owner list of six items, each marked "owner", with times (Step D, y/challenge/end on camera at about 10:00Z, Step A conflict sentence, S9-2, S9-3, edit and post); the "owner does only Step D" statements fixed in the owner block, definitions (Step D, Step A), take-day list intro, L3; V15 closed.
Other: "the log" now points to this file; header marker line defines AT RE-PIN and UNKNOWN; table "Values only the lead can supply" now has a Status column; footer line "Twelfth rewrite" added.

## V-items still open
V1, V2 (not in Q27), V4 emptying method, V7 command lines, V8, V9, V10, V11, V16 (gap items; lead values), plus clock times of owner items 4 and 5.
