# fix-ownersteps5 (round 2 of 2, FIXER; failures first; nothing run except the two commands at the end)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os5/OWNER-STEPS-q16-rows.md

## Failures and not done
- python3 -I tools/check_secrets.py exits with FAIL, 18 hits, all "token-like (length 64)" in flow-check/raw/take-check-*.txt (line 5 of each). None are in OWNER-STEPS-q16-rows.md (grep for OWNER-STEPS in the output: 0). These are other files, outside my edit scope; looks like hash lines, NOT verified. The lead must look.
- ruff format --check: not run (no Python changed; the brief said on nothing else).
- RUNBOOK times: the lead NOTE says update RUNBOOK too; I may edit only the sheet. Lead step.
- Values the sheet cannot know are V rows V1, V2, V17-V21 (chat place, HubSpot facts, settings file, key, recording place, post text, private-address list). Owner replies "missing: <item>".
- Not verified: T19/T20 meaning, flock guard facts (taken from Q28/Q29 text only).

## Reviewer findings checked against files
- B1 right: chat defined but V1 open. Fixed: each message must say where/when; "missing: where to reply".
- B2 right (V2 open). Fixed: general rule + Step D "missing: <item>".
- B3 right on all points. Fixed: challenge/window/when via lead; "end" explained as finish only (marked for lead verify at R6, not verified); false "only things you type" replaced with a full list.
- B4, B5 right. Fixed with V17-V20 and "missing" rule. NO-GO post date: Q26 item 1 "post by Wed 25 Nov" is the last day; sheet now says so (it was not an error in fact, only unclear).
- M6 right: owner list marked GO-path; NO-GO moves times; "cannot/can" reply added (my proposal, not a lead rule).
- M7 right, M11 right: count rewritten (five items plus one question, item 6 token scopes, asked once at take prep after the practice run, before Row 4). Step A removed per lead Q28-3 (supersedes "if kept").
- M8 right: clean-up, S9-2, S9-3 explained. Clean-up meaning is my reading (lead stops n8n and stand-ins, writes "clean-up starts"); NOT in a lead answer; lead must confirm.
- M9, M10 right: search-box/delete-screen mismatch -> "stop"; capital-letter difference -> "stop"; "recently deleted" counted as deleted only if the message names it.
- M12 right: line 68 said lead states a new ceiling; replaced with owner explicit yes with numbers for any new spend.
- M13 partly: owner cannot verify the re-check; sheet now says so honestly and gives a "matching re-check time" reply.
- M14 fixed: "take program" -> "demo script"; "take branch/tree" defined; "check" alone = fill program command; re-check, step check, comparison separated. Remaining uses of "take" for the recorded run are defined.
- Citations M1 right (ORDERS 159-160): re-smoke about 1 h, done about 09:30Z Tue, re-pin about 08:00Z, GO/NO-GO 14:00Z; sheet line 92 updated, footer cites it. M2 right (Q26 line 147, Q27 items 6, 9): practice run (Wed) and short re-smoke (Tue) are two runs; definition, order steps 8-9, schedule, R9 fixed. M3 right: P4a is at line 136 (verified: 136 is P4a); fixed.
- Lead orders applied: flock guard round 23 (already stated, kept); Q28 items 2-4 (private addresses to owner, T16; Step A removed; owner list), Q29 items 1-3 (T15 positive control, mailbox recount in T2 and step 13, NO-GO if T19/T20 fail).
- Q28 item 5 (lead corrects DECISIONS items 1 and 7, VIDEO-RUNSHEET N-9..N-11 at re-pin): not in the sheet's lead steps; lead step, I did not add it.

## Commands
python3 -I tools/check_secrets.py -> FAIL, 18 hits (above), none in the sheet.
