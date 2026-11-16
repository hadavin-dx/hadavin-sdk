# fix-ownersteps6 (round 3, FIXER; failures first)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os6/OWNER-STEPS-q16-rows.md
Edited only OWNER-STEPS-q16-rows.md (plus this log). Nothing run except the secret check at the end.

## Not done / uncertain
- Owner times for items 3 and 4 (V17, V18) and V1 (which conversation "the chat" is) are still lead values; the sheet tells the owner to reply "missing: <item>". I added a fallback "answer in the conversation the message came in" for where to reply: my proposal, not a lead rule.
- "Up to 3 paid calls, one each for the lead's HubSpot test, rehearsal and take" is my mapping of line 63 (Row 4, rehearsal, take) and Q21; the lead should confirm. Rehearsal normally runs on the stand-in (default), so a paid call there is not certain.
- The 07:00Z take-prep message time, the 08:00Z "missing: take-prep message" fallback, and "re-check done expected Tue after about 08:00Z" are my derivations from Q30 and the schedule; 08:00Z fallback is my proposal.
- Silence rule uses no invented clock time (planned times only); my proposal.
- Decision 12 wording fix: the sheet now follows Q17-5 and Q30-1 over decision 12; I added that the lead corrects decision 12 at re-pin (my reading; Q28 item 5 lists only items 1 and 7). Lead must confirm.
- Caption "intake mailbox": the sheet elsewhere says "intake" is being replaced by the mailbox words; I kept the lead's Q28 word in the caption and flagged it for re-read at re-pin.
- Not verified: T19-T21 definitions come from FINDINGS.md line 21 (read, not run); n8n_drive.py existence stays UNVERIFIED (Q30-3).

## Reviewer findings checked against files
- B1 right (line 70 plans up to 3 live calls; old owner text said nothing planned). Fixed: owner part states the standing yes, up to 3 calls, ceiling in the take-prep message, asked only above it.
- M1 right. Owner part rewritten with in-place definitions (take, practice run, Row 4 as "the lead's HubSpot test", rehearsal, GO or slip, take-prep message, ceiling, chat, settings file, clean-up, re-check); no Q-numbers, decision numbers, V-numbers, S9 labels, repository rule or file-name dependence (FACTS-ALREADY-DONE.md is named only as where the yes is recorded).
- M2 right. "Take prep" defined for the lead as the broad period and "take-prep message" as the single message at order step 9; item 6 now has a clock time (about 07:00Z Wed).
- M3 right. Owner part now has the Wed schedule, F-002 07:30Z cut, GO or slip 09:30-10:00Z, slip moves the take by up to a day and the post time follows the lead's message.
- M4 right (V1 still open). Fallback added; message 2 waits on message 1 stated with a "cannot" reply.
- M5 right. Reply words for items 3 and 4, reply format listed in the lead messages, item 5 list now includes private addresses and the LinkedIn account or page.
- M6 right. "mailbox address" replaced by "address of a mail account you log in to"; the only address typed is the made-up contact address.
- M7 right. "which conversation" -> "which delete message it is".
- M8 right. Silence rule rewritten: three actions wait for a message; missing message -> reply "missing: ...".
- M9 right (position 8 = short re-smoke, Tue). L6 fixed.
- M10 right. T13 note now says why "lead ID" and "sent" appear and what "lead" means in the caption.
- M11 right. T19 to T21 defined in the lead's words (FINDINGS.md line 21) and F-002 explained to the owner in plain words.
- M12 right. Owner part says there is no Step A, B or C for the owner; the owner-facing label "Step D" is kept only as "the lead calls this Step D".
- Citations Major 1 right: step 13 had the positive control after the rehearsal; moved into step 12 before the rehearsal (no renumbering). Major 2 right: DECISIONS line 13 says "right after the loopback re-smoke passes"; quote corrected. Major 3 right: T13 caption now the Q28 caption (Q28 is ORDERS line 166, item 1). L6 and V16 cites (Q22 follow-up item 4 = ORDERS line 138; Q24 item 3 = line 141) fixed.
- Q30 applied: practice run about 06:00Z, F-002 test at its end about 07:00Z, Row 4 after it, rehearsal about 07:30Z, F-031 and F-007 text fixes applied and re-read by Wed 06:00Z (schedule, still Blocker until applied), n8n_drive.py "lead provides at re-pin, existence UNVERIFIED" (R6, V7, T6). Wrong lead stamps (13:00Z to 15:00Z, 13:05Z) removed everywhere in the sheet; only dated schedule values remain (Tue 14:00Z GO/NO-GO and so on).

## Commands
python3 -I tools/check_secrets.py (from handover/flows-audit): see the report below.
PASS 0 hits in 1727 files
