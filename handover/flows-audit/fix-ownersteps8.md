# fix-ownersteps8 (fixer; edited only OWNER-STEPS-q16-rows.md, owner part)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os8/OWNER-STEPS-q16-rows.md. Not committed.

## Failures and gaps first
- `ruff format --check .` FAILS: 1 file would be reformatted, inputs/plan-wp6-resmoke-v5.md (a python block inside a .md file, line 193). Not my file and not in my allowed edit list; unchanged. Lead to decide (needs a fix by someone allowed to edit it).
- I did not run anything real; all texts are planned wording, unverified. I did not re-read lines 80 on beyond the glossary (only to search for a file saying the key is demo-only: none found).
- Reviewer's 8 Majors were checked against the file; all 8 were true.
- Inconsistency in the brief: it suggested silence "by 10:00Z on Tue 17 Nov after GO/NO-GO"; the decision itself is at 14:00Z Tue, so I used 16:00Z Tue (21:30 IST) as the silence limit.

## Fixes (each marked "planned by the audit, lead to confirm" where the lead decides)
1. Re-check done never arrives: owner writes "missing: re-check done" at 10:00Z (15:30 IST) Tue 17 Nov; still nothing at 14:00Z (19:30 IST) = NO-GO for Wed 18.
2. GO/NO-GO: lead to tell by 15:00Z (20:30 IST) Tue 17; no message by 16:00Z (21:30 IST) = NO-GO.
3. Key (item 4): owner must confirm with the lead that the key is used only by this demo and that revoking loses no prepaid credits, before revoking (no file says either).
4. "challenge" now defined in the glossary at first use (demo program entry); owner types y only after the lead's message says in one sentence what y confirms, else replies "missing: what y confirms" and types nothing.
5. First lead message location: unknown, so fallback is the conversation where the owner normally writes to the lead; flagged as lead question.
6. "private address" = private e-mail address on a real mailbox; web and street addresses not meant.
7. Silence chain: no reply to delete message 1 = message 2 not sent, both contacts stay; clean-up and item 4 not held up.
8. Retake: now a fifth kind of run; may need a 4th paid call = new yes with numbers; silence = no retake; delays post, clean-up, key revocation. Also added to "The ceiling" and the post-time line.

## Evidence
`ruff format --check .` (from handover/flows-audit): "1 file would be reformatted, 464 files already formatted" (the file named above; not OWNER-STEPS-q16-rows.md).
`python3 -I tools/check_secrets.py`: "PASS 0 hits in 1746 files".
Diff vs backup: 14 changed or added lines.

## QUESTIONS FOR LEAD
1. Which chat (app and name) carries your first message to the owner, and where does the owner write "missing: re-check done" / "missing: re-check time" if nothing has arrived? The sheet says "the conversation where you normally write to the lead" for now.
2. Confirm: no "re-check done" by 14:00Z (19:30 IST) Tue 17 Nov = NO-GO for Wed 18?
3. Confirm: you tell the owner GO or NO-GO by 15:00Z (20:30 IST) Tue 17, and silence by 16:00Z (21:30 IST) = NO-GO?
4. Is the model key used only by this demo (no other project or use)? Which file says so?
5. Does revoking the model key lose any prepaid credits (or are credits tied to the account, not the key)?
6. What exactly does typing y confirm in the demo program, and in which window / where it runs (owner's own computer or remote)?
7. Retake: is a retake a fourth paid call? Confirm: silence on a retake yes-with-numbers = no retake, and post, clean-up and key revocation wait.
8. Confirm: no reply to delete message 1 means delete message 2 is not sent; what deadline do you put in each delete message?
9. Fix inputs/plan-wp6-resmoke-v5.md line 193 formatting (ruff format fails on it) or exclude it; who may edit it?

## Round 19 (fixer; static; nothing run except the four checks)
Source: reviews/ownersteps-r19-findings.md (Major 1-7, Nit 1-5). All twelve were checked against the file first and all were true. Only the owner part (line 9 up to "## For the lead") was edited; the lead part is byte-identical to bak-os19.md (cmp rc 0, lead part now starts at line 225, was 178).
Fixes: Major 1 "under way" split into two cases (retake under way / no word by 12:30). Major 2 item 2 now says type only after "take starting now"; the typing message gives order and expected times; if "take starting now" has not come by 10:10 UTC (15:40 IST) type nothing and write nothing special (no new "missing" reply, so counts unchanged). Major 3 GO check wording made plain; the short Tuesday test run is named and excluded from "A run"; "trial pass" renamed "counted pass" (trial now only means the HubSpot trial account). Major 4 rule 6 split into 6a-6j with the six causes as a list, "later of" spelled out, silent cancellations (causes 1, 3, 4) stated. Major 5 rule 7 paragraph: a GO between 14:00 and 16:00 UTC counts only if "re-check done" came before 14:00. Major 6 "window" = program window, time = "editing time"; "chase" replaced by "missing: replies"; "planned" heading now says planned by the audit, lead to confirm; retake defined once; flows named at first use in the first paragraph; "AI model" entry added and "model credits/key/provider/calls" now say "AI model". Major 7 items 2, 4, 5 split into lettered short steps; item 4 now says ask the two facts as soon as the clean-up message arrives, and who writes to whom at 17:30.
Nits: 1 safety test lists its three parts (same id twice, id missing refused, database down); 2 a move = a later day the lead names (planned: normally the next day it can be done, never after Mon 23 Nov); 3 post rule (a) now 12:00 UTC (17:30 IST), not 13:00, so 3 hours of editing time hold; 4 delete message field says every delete message states its deadline (planned 1 hour); 5 crop/blur/cover/not needed defined in Words for you.
Counts kept true (unchanged): 13 table rows, 21 "missing" rows / 22 reply forms, 7 items, 8 rules, 6 causes, 3 kinds, 6 delete-message fields.
Checks (from handover/flows-audit): check_secrets rc 0, check_refs rc 0 (5166 references), ruff check rc 0, ruff format --check rc 0.

## QUESTIONS FOR LEAD (round 19)
1. Confirm the new default: if "take starting now" has not come by 10:10 UTC (15:40 IST) the owner types nothing and writes nothing.
2. Confirm: a GO message between 14:00 and 16:00 UTC Tue counts only if "re-check done" came before 14:00.
3. Confirm: recording-ready cut-off 12:00 UTC (17:30 IST) for the Wed 18 Nov post (was 13:00 in rule 8, 12:00 elsewhere); later arrival moves the post.
4. Confirm the GO conditions as worded (short Tuesday test run; independent review; no serious open problem), and that "not needed" (leave an address readable) is an allowed owner choice.
5. Confirm the 17:30 UTC lead message and the "30 minutes after your message" rule in item 4.
