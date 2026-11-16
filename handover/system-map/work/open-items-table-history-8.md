# Open items that block the take (live page; Mon 16 Nov 2026)

## What this page is
The demo (called lead-intake; the program is the demo's own script that sends the leads): a made-up sales lead goes into n8n (a tool that runs steps), is stored once, creates one contact in HubSpot (a sales-contact tool) and sends one mail; the take (one filmed run) shows that the same lead sent twice gives one mail and one contact write. The flow files carry placeholders for settings; the script that copies the laptop's settings (addresses, logins) into the n8n flow files (file name fill_flows.py) fills them in. UNVERIFIED whether that script exists: this page and work/critical-path-r1.md say "not built"; the plan (plan lines 4 and 223) says it read a file fill_flows.py in the glue folder (conflict 4 in work/critical-path-r2.md). I searched this checkout and found no file of that name, but the glue folder may not be in it, so neither statement is checked; the studio lead must look at the real disk. Below, the questions that must be answered first.
Seven rows (1a, 1b, 2, 3, 4, 4b, 5). What each blocks:
- Rows 1b, 2, 3, 4 and 4b block the first rehearsal; row 5 blocks scheduling it. Row 1a blocks the first rehearsal unless row 1b is answered no. While 1b is unanswered, 1a blocks. All seven must be answered before the take.
- A row is answered when its answer, quoting who answered and when, is written in the "Answer" column (the listed answerer gives the answer; the studio lead and the system-map session are two different Claude sessions; the studio lead or the system-map session writes the answer into this table; no reply file is named).
- Former items 3-19 and 22-25 (old numbering) are post-take or settled by the decisions of 16 Nov (which decision settles which row is in work/open-items-table-history-2.md); they are not tracked here. The "old #" column is the item number in an earlier version of this table (that version is work/open-items-table-history-2.md).
- Every date below is a proposal by the system-map session (the Claude session that wrote this page); the studio lead accepts or changes each one.

## Words
- take = one filmed run of the lead-intake demo on made-up data.
- studio lead = the Claude session doing the technical steps.
- studio head = the human who runs the studio; not named. If nobody has named the studio head by Mon 16 Nov 18:00 UTC / 23:30 IST, the studio lead messages the owner (the person at the laptop) and asks: "Who will build fill_flows.py?" The owner replies with one name by Tue 17 Nov 01:30 UTC / 07:00 IST; the name is entered in row 1a by Tue 17 Nov 03:30 UTC / 09:00 IST. If no name comes, the take cannot start.
- owner = the human at the laptop. Whether the owner is also the studio head is NOT SETTLED.
- run (a) = the loopback re-smoke (same thing, two names): the studio lead's short self-check on its own side, where every service answers only on the lab machine's own address (decision 12). The first rehearsal = the first laptop test run (decision 12), a lead step.
- decisions 2, 3 and 12 = items 2, 3 and 12 of handover/system-map/inputs/DECISIONS-2026-11-16.md: decision 2 = the take never deletes anything (leftover contacts are deleted by hand afterwards); decision 3 = the plan to give each part its own login (the four logins) is parked; decision 12 = the studio lead runs the first laptop rehearsal after the loopback re-smoke, target tonight or tomorrow morning IST.
- receiver Gmail account = the throwaway Gmail account that only receives the demo mails; "the delete" in rows 4 and 4b = the owner emptying that account's Trash by hand.
- Order: run (a), then the first rehearsal, then the take. Decision 12 said the rehearsal would run tonight or tomorrow morning IST. This page proposes Tue 17 Nov 12:30 UTC / 18:00 IST instead, after every row is due. The studio lead must accept or change that. The "old #" 21 appears twice because rows 4 and 4b come from the same old item.
- HubSpot check message = one line the owner runs in HubSpot, then pastes the result back; leftover-contact list = the list of made-up contacts still in HubSpot after the program stops (the program lists them by lead key and contact id).
- Rows 4 and 4b both come from old item 21; row 4 cannot be answered until row 4b's sentence is written.
- "before the first rehearsal" in an Answer-by cell means: due before that event; the clock time is the proposal.
- decision-list item A4 = item A4 of handover/system-map/work/decision-list-for-lead.md: "does run (a) start today".

## Schedule (the one place with all dates; every time is a PROPOSAL; from work/critical-path-r2.md, which is DRAFT and unverified; UTC / IST)
| date and time | what | source |
|---|---|---|
| Mon 16 Nov 13:00 / 18:30 | row 5 (A4) was due; PASSED, answer UNKNOWN | row 5 |
| Mon 16 Nov 18:00 / 23:30 | if the studio head is unnamed: the studio lead asks the owner "Who will build fill_flows.py?" | Words |
| Tue 17 Nov 01:30 / 07:00 | the owner answers with one name (row 1a fallback) | Words, row 1a |
| Tue 17 Nov 03:30 / 09:00 | rows 1a, 1b, 3 and 5 due; the name is entered in row 1a (if the owner answered by 01:30 UTC; otherwise the answer is needed before this time and the row stays NOT SET) | rows 1a, 1b, 3, 5 |
| Tue 17 Nov 09:00 / 14:30 | row 4b due | row 4b |
| Tue 17 Nov 12:00 / 17:30 | rows 2 and 4 due | rows 2, 4 |
| Tue 17 Nov 12:30 / 18:00 | earliest start of the first rehearsal (laptop test run) | Words, order of events |
| Mon 23 Nov 03:40 / 09:10 | latest start of build and import of the flow copy, base case (A13 = no, no 4-hour spare); a plan-length chain of 14 hours ends at the take start | r2 section 2, step 4 |
| Mon 23 Nov 14:40 / 20:10 | latest time for the owner notice, base case (3 hours before the start; the stricter reading, 3 hours before the owner's setup, is 14:10 / 19:40) | r2 sections 2 and 5 |
| Mon 23 Nov 17:40 / 23:10 | latest start of the take (49-minute worst case) | r2 section 1 |
| Mon 23 Nov 18:29 / 23:59 | stop time | r2 section 1 |
| Wed 25 Nov 15:00 / 20:30 | post | r2 section 1 |
A13 = decide whether to keep a 4-hour spare for one rerun; the answer is unknown. If A13 = yes: take start 13:40 / 19:10, notice 10:40 / 16:10, build and import Sun 22 Nov 23:40 / Mon 23 Nov 05:10 (r2 section 2). What fills the 49 minutes, the owner setup time and the review and rehearsal times are NOT STATED in any file or rest on an earlier draft's guess; the margin of about 6 days is not usable until rows 1a, 1b and 5 are answered.

## Open items
| # | old # | Question (yes/no unless it says one name or one sentence) | Where (path from the repo root, or relative as written) | Answerer (role) | Answer by (UTC / IST) | Answer |
|---|---|---|---|---|---|---|
| 1a | 1 | Who builds the script that copies the laptop's settings (addresses, logins) into the n8n flow files (whether it exists is UNVERIFIED, see the intro)? One name, not yes/no. If row 1b is yes and nobody is named, the take cannot start. | handover/system-map/README.md line 3; handover/system-map/TAKE-BLOCKERS.md row 1 | Answerer: the studio head. Fallback only if the studio head is unnamed by Mon 16 Nov 18:00 UTC / 23:30 IST: the owner, who then answers by Tue 17 Nov 01:30 UTC / 07:00 IST (see Words) | Tue 17 Nov 03:30 UTC / 09:00 IST (the owner's name must be entered before this time, so the answer is needed before it) | NOT SET |
| 1b | new | Does the first rehearsal need fill_flows.py? yes/no (unknown today; if still unknown at the due time, treat it as yes) | handover/system-map/TAKE-BLOCKERS.md row 1 | studio lead | Tue 17 Nov 03:30 UTC / 09:00 IST | NOT SET |
| 2 | 2 | Does the studio lead send the owner the HubSpot check message (one line the owner runs in HubSpot, then pastes back the result)? yes/no. (The four logins are parked by decision 3; deleting leftovers is moot because of decision 2.) | handover/system-map/OWNER-VIEW.md line 27; handover/system-map/TAKE-BLOCKERS.md row 5 | studio lead | Tue 17 Nov 12:00 UTC / 17:30 IST | NOT SET |
| 3 | 20 | Will the studio lead name the demo HubSpot account (no account number) in the message that sends the leftover-contact list, so the owner can check it before deleting the leftover contacts by hand (decision 2)? yes/no | handover/system-map/work/end-delete-cases.md step 18 | studio lead | Tue 17 Nov 03:30 UTC / 09:00 IST (proposed; due before the first rehearsal) | NOT SET |
| 4 | 21 | Does the owner empty the receiver Gmail account's Trash by hand before the take (the take date is NOT SET; the answer is needed before the first rehearsal)? yes/no. Row 4b first, then this question. Why it gates (a rehearsal uses the card): emptying Trash cannot be undone, and the run-day card (OWNER-RUN-DAY-CARD.md, the owner's checklist for filming day) is unsafe while the sentence in row 4b is empty. | handover/system-map/OWNER-RUN-DAY-CARD.md line 31 | owner | Tue 17 Nov 12:00 UTC / 17:30 IST | NOT SET |
| 4b | 21 | Studio lead: one sentence that says how the receiver Gmail account looks (name shown, label or inbox state, without its address) before the Trash is emptied, so the owner can be sure it is the right account | handover/system-map/OWNER-RUN-DAY-CARD.md line 31 | studio lead | Tue 17 Nov 09:00 UTC / 14:30 IST (earlier than row 4, which needs it) | NOT SET |
| 5 | 26 | Does run (a) start today (decision-list item A4)? yes/no. The original due time passed (Mon 16 Nov 13:00 UTC / 18:30 IST); the new due time is Tue 17 Nov 03:30 UTC / 09:00 IST. Its status is UNKNOWN (no answer found in any file). It blocks scheduling the first rehearsal, which in turn must happen before the take. If it stays unanswered, run (a) has no start. The studio lead acts now: write the answer in this table. | handover/system-map/work/decision-list-for-lead.md | studio lead | Tue 17 Nov 03:30 UTC / 09:00 IST (new; the original due time passed) | NOT SET |
