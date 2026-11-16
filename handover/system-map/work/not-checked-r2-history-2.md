# Not checked: open items before the filmed demo run, the take (rewritten Mon 16 Nov 2026 by the system-map session)

## What the demo does
The demo takes a made-up sales lead, writes it once into a small database, creates or updates one contact in HubSpot (a sales-contact tool) and sends one mail. The steps run in n8n (a tool that runs such steps). The film must show that the same lead sent twice gives one mail and one contact write. The flow files hold placeholders for settings; a script (fill_flows.py, not built) would fill them from the laptop's environment.

## Source and scope
Source: an unverified zoom-out read of REPORT.md, flowcheck/REPORT.md, flowset/REPORT.md and inputs/DECISIONS-2026-11-16.md. Items settled by decisions 1 to 12 of that file are removed: patched copy chosen (lead answer 10:20Z), source tree and licence copies (decision 11), S9-1 and S9-4 deferred and no closed-gate claim (decision 5), scenes 5 to 11 cut (decision 1), HubSpot write scope moot because the take never deletes (decision 2), proof screen is a rehearsal capture (decision 9). T19 has not run. Nothing below is verified.

## Terms
- take = one filmed run of the lead-intake demo on made-up data; scenes 1 to 4 = the four parts of the run sheet that the take shows (the run sheet is on branch origin/demo/handover and is not in this checkout).
- studio lead = the Claude session doing the technical steps; owner = the human at the laptop; studio head = the human who runs the studio (not named); core-hardening session = the other Claude session that patches the program.
- T19 = the test that sends one lead twice and counts mails and contact writes.
- Claim, MarkDone, CrmUpsert = steps in the flows (Claim inserts the lead id once; MarkDone is the last step; CrmUpsert creates or updates the contact). flowcheck = the flow-file checker. `$env` = settings read from the laptop's environment.
- BL-wp6-G1 = the open item "the fill script is not built".
- loopback re-smoke = the studio lead's short self-check on its own side before the rehearsal; what it checks and what counts as passing are not recorded in any file (decision 12).
- rehearsal = a test run on the laptop without a real account (decision 12; target tonight or tomorrow morning IST). How it differs from rows 1 and 2 is NOT RECORDED; this page treats rows 1 and 2 as steps inside it.
- stand-ins, refusal, 60 s = words used in the run-sheet sentences; the run sheet is not in this checkout, so their meaning is NOT RECORDED here.
- row N = row N of the table below.

## Open items
| # | open item | person | due |
|---|---|---|---|
| 0 | Build fill_flows.py (BL-wp6-G1), the script that reads the laptop's settings and writes a copy of the flow files with the `$env` values filled in (the list of values is NOT RECORDED; done when the studio lead names a test: NOT SET; asked of the studio lead with the other facts by Tue 17 Nov 12:00 UTC / 17:30 IST). | not chosen yet | before row 1 |
| 1 | Import the filled copy on the laptop, send one made-up lead, reach MarkDone. | studio lead | after the loopback re-smoke passes |
| 2 | Run T19: send one lead twice. | studio lead | same time as row 1 |
| 3 | Re-check the regenerated flow folder with flowcheck on the final folder and write its git sha (where it is written: NOT SET). | core-hardening session | after the folder is on a fetchable branch |
| 4 | n8n's saved runs (its executions list) hold lead id, e-mail and name. Is that list kept off camera or cleaned? | studio lead | same time as row 1 |
| 5 | List the mail sender and the 3 recipients; confirm all are the owner's own inboxes. No program check enforces this (S9-1 deferred). | owner | before the owner sends the written yes |
| 6 | Mark every scene 1 to 4 sentence in the run sheet that mentions stand-ins, refusal, 60 s or counts. | studio lead | before the film |
| 7 | flowcheck blind spots (writes without "crm" in the address, `$node[...]`, disabled steps). | core-hardening session | after the rehearsal |
| 8 | Duplicate behaviour of CrmUpsert on the owner's own free HubSpot trial. | studio lead | same time as row 2 |

## Goal and gating
Goal: settle the open checks before the take. Must pass before filming: rows 0, 1, 2 and 4. Tracked only, not gating: rows 3, 5, 6 and 8 (row 5 should be done before the written yes); row 7 comes after the rehearsal. Row 1 cannot run before row 0 exists. If row 0 has no owner by Tue 17 Nov 12:00 UTC / 17:30 IST (proposed by the system-map session), the studio lead asks the owner to choose.

## Pass rules
- Row 1: one lead reached MarkDone (yes/no).
- Row 2: pass = one mail and one contact write in total, counts recorded.
- Row 4: the n8n executions list and the database tables hold no real-looking data on camera; record what was seen.
- Rows 3, 5, 7 and 8: no pass rule is recorded in any file I read (NOT SET); the studio lead is asked to write one for each by Tue 17 Nov 12:00 UTC / 17:30 IST (proposal). Row 5 "3 recipients": the names of the three recipient inboxes are NOT RECORDED here (and must not be written on this page).
- Row 6: every scene 1 to 4 sentence that mentions stand-ins, refusal, 60 s or counts is marked.

## Times
No file sets an exact time for any row; they are NOT SET. Decision 12 gives only the target (tonight or tomorrow morning IST) for rows 1, 2 and 4. The studio lead proposes exact UTC and IST times by Tue 17 Nov 12:00 UTC / 17:30 IST (my proposal).
