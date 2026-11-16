# v12 NOTES FOR THE LEAD (failures and unverified items first)

## 1. What is not done or not good enough
1. `OWNER-STEPS-realrun-v12.md` is 129 lines (target 150: met) but 26.3 KB (target 25 KB: MISSED by about 1.3 KB). I moved what I could to the appendix; more cutting would drop content the reviews asked for.
2. Nothing was run. Every command in the three files is UNVERIFIED, including `python3 -I` (SN3: not fixed; the rehearsal must use the printed form).
3. Hedges are only partly removed (TM19), "row N" references are still many (TM20, about 30 left in the sheet), and E.0 on the card is still 10 ticks (TM12).
4. The 20 stranger majors were mapped to TM1-TM20 by me from the condensed list. The mapping may differ from the full report; a reviewer should check by text, not by number.
5. I did not edit `inputs/AGENT-SCOPE-DO-AND-DONT.md` or `inputs/DECISIONS-2026-11-16.md` (not mine to edit). F01, F05, F13, F17, F18 stay open until you apply the patch text in section 4.
6. The shot list (appendix 14) is PROPOSED, not verified by a rehearsal.

## 2. "Lead verifies at re-pin" (the sheet says so; nobody has checked)
- Go item 5: the take program has no delete call. I did not give item 5; you give it only after your final-head check.
- The backstop counter is the program's cumulative ledger and does not reset between trial and real run.
- Whether the program re-reads the settings file after start (sheet says: do not edit settings after start).
- `n8n_start.sh` and `n8n_kill.py` lines, and that the program prints no cue lines except for y, challenge and end.
- Clean start: names of the admin role, the take database and the fresh container (one Postgres server, two databases). I wrote none; you fill them (row 2 of the run card).
- Exit code for case C "unknown" (the sheet states none).
- The claim "a lead sent twice with the same id is processed once", the lease and three-try wording, and "index not seen" for the take database.
- HubSpot key scopes: the take key is read-only, the probe key is separate; ask the owner once at take prep.
- Retake count: lead computes (row 10).
- Window end 2026-11-23 18:29 UTC = 23:59 IST; take target Wed 18 Nov (not fixed); cancel the run key the same day; post by Wed 25 Nov 15:00 UTC = 20:30 IST.

## 3. New question for you (not on the list)
What do `DESK_*` and `MF_*` hold in the local flow copy? I.6 erases them, but I could not say what they contain; state it in writing before I.6.

## 4. Lead decisions the owner may veto (labelled as such in the files)
20-minute margin before the latest start; erase and cancel "same day" (not 60 minutes); run-name rule; accepted exposure of the shared Linux user; the trial run as a lead addition; the 5-minute limit at "Type y to start".

## 5. Patch text for the inputs (file, old line, new line)
- AGENT-SCOPE line 5: old "n8n test account and its own Postgres table" -> new "n8n test account and its own database on the one Postgres server (one server, two databases: n8n's own and the take's)".
- AGENT-SCOPE line 9: add "the execution clean-up wording is owned by sheet step I.5; do not restate it here".
- AGENT-SCOPE line 13: add "the key file lives in the secret folder named on run card row 12, mode 600, made by the owner, never under /mnt".
- AGENT-SCOPE line 20: old "at the end ARCHIVE the take's own HubSpot contacts, which the code does as a DELETE call (...)" -> new "list leftover contacts; no delete call exists in the take program (read-only HubSpot identity, archive_contacts 'no'); the owner deletes by hand from your list".
- DECISIONS line 2: add the claim plus the Q21.2 honest sentence, marked "lead verifies at re-pin".
- DECISIONS line 9: add "the step 0 probe runs once, with the owner's written yes and a separate probe key".
- Also: add a scope row for your own acts (F17): clean start, n8n stop/start, contact list, re-pin checks.

## 6. 180/189
The sheet uses neither figure; appendix 17 "Figures" explains why. Decide which is right before any figure goes in a message.

## 7. PENDING markers
All PENDING Q19.n, Q20.n, Q21.n markers are removed (0 left in the sheet and card). Where an answer left something unverified, the text says UNVERIFIED or "lead verifies at re-pin".
