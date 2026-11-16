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
