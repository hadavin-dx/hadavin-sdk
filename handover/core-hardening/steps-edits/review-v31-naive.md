# Owner sheet v31 stranger review, round 4 (egm-comprehension, condensed copy), 2026-11-16
Read: SA, SB, CA, AA, FP, then review-v30-naive.md; CARD-B only grepped; APPENDIX-B unread. Verdict: 1 blocker, 8 majors, 13 minors. All UTC/IST pairs and the price arithmetic (0.27 per call, 0.81) check out.
## BLOCKER
- B1 SA/SB line 54 (5.1a), the very first action, cannot be executed: "today plus 7 days as a first guess" = Mon 23 Nov, which check 2 (line 42) forbids; "before any message from the lead" contradicts "the run day you and the lead have agreed" (no step agrees the day); "read the older key's last-used time" stated twice; "take B" vs the sheet's own word "used"; paragraph about 330 words; owner cannot tell A from B if the key was used in the last 7 days (run days only through Sun 22).
## MAJOR
- M1 The 7-day rule is not explained; A and B look the same in effect (B cancels at 7.11 hours later). 6.7 says a key used after the first reading is not cancelled but 7.11 cancels anyway: A silently turns into B, reason unstated.
- M2 6.6 waits for "restarted" until the latest start (11:30 sample) while 7.3, W5 and the card forbid pressing Enter from 5 minutes before it; nothing says what happens 11:25-11:30; "latest start" is really latest start plus 5 minutes.
- M3 The cancel helper has no step: only CA blank 16, the yes pattern, AA parts 1 and 10; no helper row in the sample numbers message though the yes needs "cancel helper <name or none>"; no step says when to ask; how the helper differs from the backup person unclear; helper with a model-account role conflicts with R1 (work alone); a cancel-only role is not explained.
- M4 "Date you decided to use the existing balance" (R4 sample row) is never asked for in 5.1b; also phone/mail for "other channel" and "backup person" collide with the no-real-address rule.
- M5 Last-resort timing: 10 + 10 minutes after "cancel failed" plus 2-minute retry can land about 18:41 UTC = 00:11 IST, after the 18:29 UTC deadline; the yes does not say it accepts this.
- M6 6.1 Recall step asks the owner to have the lead "show that your Windows has no Recall"; the lead cannot see the screen.
- M7 The yes sentence has two sources (the message's exact sentence vs the AA part 8 pattern); items such as cancel helper and last-resort step may be the owner's to supply.
- M8 Section 7 heading promises "what to do if the key is cancelled during the run" but has no such text (v30 m6 still open).
## MINOR
1 "cancel-by time" two meanings (alarm 3 vs Mon 23 18:19 UTC = 23:49 IST); Sunday latest time not said. 2 card L2 "revoked" for keys. 3 "film cue" two meanings (AA part 1 vs FP item 2 "film pause now"). 4 words with several meanings: key, run, card, yes, go, take, exit, challenge, delete, message. 5 internal codes in owner text: R1, R4-R10, W1-W9, L1-L5, Key-list check, R6 shape check, re-pin, STOP RULE, UNVERIFIED. 6 bare pointers "(appendix N)". 7 wrong pointer: AA part 1 "STOP RULE in sheet section 2" (it is at the end of section 1, SA line 15). 8 FREEZE defined differently on sheet and appendix. 9 WSL, Ubuntu, date -u, grep, cut not glossed at first use. 10 7.10 and 8.1 "send the counts / two times" with no set format. 11 "no earlier run used the run name" (5.1b) owner cannot know. 12 Alarm 4 "cancel by the older-key time" has no buffer. 13 reading load: 7.11 (about 330 words) and CA line 13 (about 500 words) single paragraphs.
## v30 findings
Fixed: M-A2, M-A3 in 7.3/W5/card (but see M2), M-A4, m1, m3, m4, m8-m11. Not fixed: M-A1 (reworded, now B1), m6, M9 reading load. Partly: m2, m5, m7.
## Route A vs B
SA/SB 5.1a consistent with each other but unclear why B exists; SB R4, 6.7, 7.1 consistent; SB does not say A needs the 7-day rule. B card and appendix not compared.
## Not checked
CARD-B, APPENDIX-B, a mechanical A/B diff, the real numbers message, word counts, vendor pages and buttons, click paths, build/check scripts, whether the helper role exists.
