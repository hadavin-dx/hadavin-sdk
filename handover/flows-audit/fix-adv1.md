# fix-adv1 (fixer, 2026-11-16): items from reviews/adversarial-takeday-r1.md and reviews/crossread-demo-r1.md

## Failures, unfixed items and what I did not check (first)
- Nothing ran. Only text was edited; both reviews are unverified reviewer words, checked here only against the text of CLAIMS-TABLE.md and RUNSHEET-WORDING.md.
- Reviewer item 4 says "decision 4 rows"; neither file has a decision 4 about recovery claims. I reconciled with the file's own decision 1 (no recovery time anywhere) and marked N-5a as NOT a recovery claim (mechanism only) instead of cutting it.
- Still open, lead-owned (exact missing input): Q-A (who types the machine actions), Q-B (who draws or starts the stopwatch overlay), Q21 (yes or no to an optional clean-up of the take own database), Q22 (yes or no, and who runs the mf_leads select), Q-H (re-pin date and hour). Q21 and Q22 are my proposals, written as proposals, not as decisions.
- Not touched (outside the two editable files, or not in the asked list): adversarial items 3, 5, 8, 9, 11 and crossread items 2, 4, 5, 7. The two review files and other files were not edited.
- Item 3 of crossread (CT or RW still say the script archives contacts or saved runs are deleted): I searched both files; the remaining mentions are already marked older, HELD, STALE or the old desk harness, so nothing needed changing.
- No rows were added, so counts are unchanged (327 claims, 87 to-do rows). Q21 and Q22 were added as bullets, not rows.

## Changes
RUNSHEET-WORDING.md
- Item 2: step 10, the A-016f row note and the closing card line 1 now say the proof of processed once is: exactly 1 mail in the intake mailbox + the mf_leads row (attempts, mail_sent) + the POST 2 reply under 10 s; one CRM row proves nothing about n8n (CRM keyed on e-mail only). Paste cells untouched.
- Item 4: step 8 and the N-5a row: N-5a only after a rehearsal showed the takeover; it is NOT a recovery claim; if the stop misses the window or no takeover shows within 2 minutes, scene 4 is cut (with N-5a and N-5b); Q-A and Q-B stay open.
- Item 6: step 6 and the P4a row: P4a fails means the take is postponed, failed rows are never filmed; A-008a stays conditional on P4a.
- Item 1: Q22 bullet in section 4 (and step 6 points to it).
- Crossread 6: line 13 now says the K1 figure is relayed, raw not seen, measured on stand-in film-v4 flows; the statement that nothing is measured at 45 s on real-v5 stays.
- Q21 bullet (optional clean-up of the take own database, written nowhere in the video); open-items-without-owner bullet (adversarial item 10) naming the missing lead input.
CLAIMS-TABLE.md
- Start here item 2: scene 2 (Q22 dependency), scene 3 (proof), scene 4 (N-5a, cut rule, Q-A, Q-B).
- Checks: P4a fail rule; Q22 and Q21 bullets after P4c.
- D1: K1 wording "relayed, raw not seen, measured on stand-in film-v4 flows".
- Row 8 note: A-016f proof. 

## Verification (commands run)
- python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md: RESULT: PASS
- python3 claims-count.py CLAIMS-TABLE.md: total 327, to-do rows 87, offenders 0, ids 327 unique.
- Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-adv1/
