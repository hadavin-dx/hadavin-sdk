# Open checks before filming (the take = the one filmed run of the demo) (rewritten Mon 16 Nov 2026 by the system-map session)

Order: loopback re-smoke (F3), then row 0, then row 1, then rows 2 and 4 together. Film only after rows 0, 1, 2 and 4 pass. Rows 3, 5, 6, 7 and 8 do not block filming. Key: studio lead, core-hardening session and system-map session are Claude sessions; owner is a human. Answers to F1 to F8 are due by Tue 17 Nov 12:00 UTC / 17:30 IST (proposal); the row times themselves are set by F6. Proposed pass rules (unconfirmed): loopback re-smoke passes when every service answers only on the laptop's own address; row 0 passes when the filled flows import without error. Flow order (UNVERIFIED; the studio lead confirms): Claim, CrmUpsert, Mail, MarkDone. Whether the mail goes before or after the contact write is NOT RECORDED.

## What the demo does
The demo takes a made-up sales lead, writes it once into a small database, creates or updates one contact in HubSpot (a sales-contact tool) and sends one mail. The steps run in n8n (a tool that runs such steps). The film must show that the same lead sent twice gives one mail and one contact write. The flow files hold placeholders for settings; a script (fill_flows.py, not built) would fill them from the laptop's environment.

## Source and scope
Source: an unverified zoom-out read of REPORT.md, flowcheck/REPORT.md, flowset/REPORT.md and inputs/DECISIONS-2026-11-16.md. Items settled by decisions 1 to 12 of that file are removed: patched copy chosen (lead answer 10:20Z), source tree and licence copies (decision 11), S9-1 and S9-4 deferred and no closed-gate claim (decision 5), scenes 5 to 11 cut (decision 1), HubSpot write scope moot because the take never deletes (decision 2), proof screen is a rehearsal capture (decision 9). T19 has not run. Nothing below is verified.

## Terms
- take = one filmed run of the lead-intake demo on made-up data; scenes 1 to 4 = the four parts of the run sheet that the take shows (the run sheet is on branch origin/demo/handover and is not in this checkout).
- studio lead = the Claude session doing the technical steps; owner = the human at the laptop; studio head = the human who runs the studio (not named); core-hardening session = the other Claude session that patches the program.
- T19 = the test that sends one lead twice and counts mails and contact writes.
- Claim, MarkDone, CrmUpsert = steps in the flows (Claim inserts the lead id once; MarkDone is the last step; CrmUpsert creates or updates the contact). flowcheck = the flow-file checker. `$env` = settings read from the laptop's environment.
- BL-wp6-G1 (a backlog id; its page is not in this checkout) = the open item "the fill script is not built".
- decision 12 (second-hand, UNVERIFIED; inputs/DECISIONS-2026-11-16.md) = the studio lead runs the first laptop rehearsal after the loopback re-smoke, target tonight or tomorrow morning IST.
- loopback re-smoke = the studio lead's short self-check on its own side before the rehearsal; what it checks and what counts as passing are not recorded in any file (the pass rule on line 3 is a proposal).
- rehearsal = a test run on the laptop without a real account (decision 12; target tonight or tomorrow morning IST). How it differs from rows 1 and 2 is NOT RECORDED; this page treats rows 1 and 2 as steps inside it.
- stand-ins, refusal, 60 s = words used in the run-sheet sentences; the run sheet is not in this checkout, so their meaning is NOT RECORDED here.
- row N = row N of the table below.

## Open items
| # | open item | person | due |
|---|---|---|---|
| R | Loopback re-smoke (a self-check by the studio lead on its own side). Blocks row 1. Pass rule: NOT SET (F3). | studio lead | before row 1 |
| 0 | Build fill_flows.py (BL-wp6-G1): the script that fills the flow files' settings from the laptop. Done when (proposed, unconfirmed): the filled flow files import into n8n without error. See Facts needed F1. | studio lead (default; no one else named) | before row 1 |
| 1 | Import the filled copy on the laptop, send one made-up lead, reach MarkDone. | studio lead | after the loopback re-smoke passes |
| 2 | Run T19: send one lead twice. | studio lead | same time as row 1 |
| 3 | Re-check the regenerated flow folder with flowcheck on the final folder and write its git sha (where it is written: NOT SET). | core-hardening session | after the folder is on a fetchable branch |
| 4 | n8n's saved runs (its executions list) hold lead id, e-mail and name. Is that list kept off camera or cleaned? | studio lead | same time as row 1 |
| 5 | List the mail sender and the 3 recipients; confirm all are the owner's own inboxes. No program check enforces this (S9-1 deferred). | owner | before the owner sends the written yes |
| 6 | BLOCKED until F4 is answered: mark every scene 1 to 4 sentence in the run sheet that mentions stand-ins, refusal, 60 s or counts. | studio lead | before the film |
| 7 | flowcheck blind spots (writes without "crm" in the address, `$node[...]`, disabled steps). | core-hardening session | after the rehearsal |
| 8 | Duplicate behaviour of CrmUpsert on the owner's own free HubSpot trial. | studio lead | same time as row 2 |

## Facts needed (each gap named once; none is recorded in any file I read)
Asker for all rows: the system-map session. Proposed answer time for every row: Tue 17 Nov 12:00 UTC / 17:30 IST (no one has agreed).
| id | question | who answers | answer and date |
|---|---|---|---|
| F1 | Row 0: which settings does fill_flows.py fill, and which test says it is done? | studio lead | NOT SET |
| F2 | How does the first rehearsal differ from rows 1 and 2? | studio lead |
| F3 | What does the loopback re-smoke check, and what counts as a pass? | studio lead | NOT SET |
| F4 | What do "stand-ins", "refusal" and "60 s" mean in the run sheet (the run sheet is not in this checkout)? | studio lead | NOT SET |
| F5 | One pass rule each for rows 3, 5, 7 and 8. | studio lead | NOT SET |
| F6 | Exact UTC and IST time for each row. | studio lead | NOT SET |
| F7 | What does the owner's "written yes" approve (money numbers, filming, both)? Row 5 must be done before it. | owner | NOT SET |
| F8 | Who gets rows 3 and 7? Proposal: the core-hardening session, as now written. | lead session | NOT SET |

Glosses for the decisions cited above (second-hand, UNVERIFIED; inputs/DECISIONS-2026-11-16.md): 1 = only scenes 1 to 4 are filmed; 2 = the take never deletes; 5 = checks S9-1 (a program check that mail recipients are the owner's own inboxes) and S9-4 are deferred, so the film must not claim a closed gate; 9 = the counts proof is a rehearsal screenshot; 10 = one Postgres server, two databases; 11 = licence files are never overwritten; 12 = the studio lead runs the first laptop rehearsal after the loopback re-smoke. Decisions 3, 4, 6, 7 and 8 are not used on this page.

## Goal and gating
Goal: settle the open checks before the take. Must pass before filming, in this order: row 0, then row 1, then rows 2 and 4 together. Tracked only, not gating: rows 3, 5, 6 and 8 (row 5 must be done before the owner's written yes, see F7); row 7 comes after the rehearsal. Row 1 cannot run before row 0 exists. If row 0 has no owner by Tue 17 Nov 12:00 UTC / 17:30 IST (proposed by the system-map session), the studio lead asks the owner to choose.

## Pass rules
- Row 1: one lead reached MarkDone (yes/no).
- Row 2: pass = one mail and one contact write in total, counts recorded.
- Row 4: the n8n executions list and the database tables hold no real-looking data on camera; record what was seen.
- Rows 3, 5, 7 and 8: no pass rule is recorded in any file I read (NOT SET); the studio lead is asked to write one for each by Tue 17 Nov 12:00 UTC / 17:30 IST (proposal). Row 5 "3 recipients": the names of the three recipient inboxes are NOT RECORDED here (and must not be written on this page).
- Row 6: every scene 1 to 4 sentence that mentions stand-ins, refusal, 60 s or counts is marked.

## Times
No file sets an exact time for any row; they are NOT SET. Decision 12 gives only the target (tonight or tomorrow morning IST) for rows 1, 2 and 4. The studio lead proposes exact UTC and IST times by Tue 17 Nov 12:00 UTC / 17:30 IST (my proposal).
