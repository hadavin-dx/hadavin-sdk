STATUS: DRAFT. Do not use this page. Follow OWNER-VIEW until the lead session approves.

# DRAFT: replacement for OWNER-VIEW "order of messages" (16 Nov 2026, from an independent style read; NOT applied)
Held because: (1) the lead must say whether the film pause stays (QUESTIONS item 8); (2) CONFLICT: the older OWNER-VIEW text (row 3) says `end` deletes, this page says the program never deletes anything; the question (M17) is open, see decisions/M17-end-never-deletes.md; (3) cells marked "NOT SET: needs studio lead" have no source file. Made-up data only. Times: UTC and IST (IST = UTC+5:30).

Terms (one line each; meanings come from OWNER-RUN-DAY-CARD.md and the decisions of 16 Nov, so some are NOT SET):
- run = one recorded run of the demo on made-up data (the program calls it a "take"); run name = the one word you invent for it and never reuse.
- rehearsal = a test run before the filmed run, with no real account; film pause = the moment the program stops and waits for you to type `end` while the contact list is filmed (unconfirmed, see below).
- stage.env = a settings file in the run folder; you open it to compare numbers. demo-take = the Chrome profile used only for the run. v5 = version 5 of the owner's step list. A13 = the question on decision-list-for-lead.md whether a 4-hour rerun margin is kept.
- retire check, n8n removal and clean-up step 1: NOT SET: needs studio lead (a one-line plain meaning of each, to be taken from OWNER-CLEANUP-CARD.md).
- The 6 digits in row 6 are the number the program prints in its second prompt. Where that number comes from beyond that: NOT SET: needs studio lead (the source of the 6 digits).

Pause rows (7, 8, 9) apply only if the studio lead confirms the film pause. Skip them if there is no pause. If the pause stays, the order is: row 7 first (studio lead: "program paused"), then row 8 (you: "film done"), then row 9 (studio lead: "film done, type end"), then row 10. Do nothing on a row marked TBD until its text is filled in. Rows 12 to 19 (clean-up) are read with the OWNER-CLEANUP-CARD.md steps; their one-line meaning: row 12 = you say "accepted"; row 13 = the studio lead says "last run done" and clean-up starts; row 15 = the studio lead sends the command for the retire check; row 16 = you confirm the two old logins now print "refused as expected" (the retire check passed); row 17 = the studio lead says n8n was removed; row 19 = you revoke the model key.
This page is a draft that replaces the older "order of messages" text in OWNER-VIEW only after the lead agrees; until then follow OWNER-VIEW.

CONFLICT (open): the older OWNER-VIEW text says `end` deletes; this page says the program never deletes anything. M17 question open, see decisions/M17-end-never-deletes.md.

According to this draft, the run never deletes anything. `end` only stops the run. Leftover made-up contacts are deleted by hand. Do nothing in a row until the message above it has arrived.

| # | Who sends | Exact words | What you do | Can it be undone? |
|---|---|---|---|---|
| 1 | Studio lead | TBD (owner of this cell: studio lead, due before the first rehearsal; time NOT SET); run date and start time in UTC and IST, at least 3 hours ahead | Nothing until it arrives; then laptop plugged in, sleep Never, lid action Do nothing | yes |
| 2 | Studio lead | "rehearsal passed" and the result file name | No file name: do not send your yes | yes |
| 3 | Studio lead | TBD (owner of this cell: studio lead, due before the first rehearsal); at most 3 model calls, worst-case price of one call, 3 times that in US dollars, money spent so far, spending backstop, stop time, path of `stage.env` | Open `stage.env`; compare money spent so far and the backstop with the message; a number missing or different: type nothing, tell the studio lead | yes |
| 4 | You | "Yes, run <run name>, up to 3 model calls and up to US$<total> (3 times the worst-case price of one call), stop time Mon 23 Nov 2026 18:29 UTC / 23:59 IST." | Once per paid run, with a run name never used before | yes; no money moves until you type `y` |
| 5 | Studio lead | "start now" | Terminal; type the lines the studio lead sends; both login lines must say "still works" (good here) | yes |
| 6 | You | `y`, then `<6 digits> <run name>` | Type both yourself, only after the figures match your yes | NO: up to 3 paid calls start; no refund; only the program's own limits stop them |
| 7 | Studio lead | "program paused" (draft card only; pause not confirmed). Skip if no pause. Comes first of the pause rows. | Type nothing; film the HubSpot contact list; no Ctrl-C, do not close the terminal | yes |
| 8 | You | "film done" (Skip if no pause. Comes second of the pause rows.) | Only after you checked the film file exists and plays | yes |
| 9 | Studio lead | (proposed) a new message beginning exactly "film done, type end". Skip if no pause. Comes third of the pause rows. | Type `end`, Enter. Deletes nothing (this page's reading; CONFLICT with the older OWNER-VIEW, see above). Screen says "delete" or "archive": type nothing, tell the studio lead | pause ends; nothing deleted |
| 10 | Studio lead | NOT SET: needs studio lead (the exact words of this message); count of leftover made-up contacts | The studio lead sends the list (lead key and contact id of each leftover made-up contact; the 3 test addresses are named to check each match); the owner deletes exactly those contacts by hand, then replies "contacts deleted" and the number | NO (HubSpot may keep a recoverable copy: not checked) |
| 11 | Studio lead | "demo mails may be deleted" (failed run only) | Delete demo mails (Inbox, label `demo`), empty Trash; reply "demo mails deleted"; new run name and new yes | NO |
| 12 | You | "accepted" (after watching the edited video twice) | Only if no further run is needed | NO: ends all runs |
| 13 | Studio lead | "last run done" | With your "accepted": clean-up step 1 | NO |
| 14 | Studio lead | "delete these apps: ..." | Delete exactly those HubSpot private apps; screenshot | NO |
| 15 | Studio lead | "run the check" plus command | Run it, `echo $?`; "refused as expected" (0) good; "STILL WORKS" (3) bad: say which login | yes |
| 16 | You | "retire check passed" | Only if both logins printed "refused as expected" | yes |
| 17 | Studio lead | "n8n removal done" | Wait | NO |
| 18 | Studio lead | "secret files may be deleted" | Delete only the names sent, `shred -u --` line compared letter by letter; reply "secret files deleted" | NO |
| 19 | You | "model key revoked" | Revoke it yourself, only after row 16; then restore sleep and lid values, sign out of `demo-take` | NO |
| 20 | Studio lead | NOT SET: needs studio lead (the final post words) | Second person checks the post; send the text to the studio lead first; you post | NO |


## Current rules (Mon 16 Nov 2026; draft; older paragraphs are in owner-timeline-draft-history.md, owner-timeline-draft-history-2.md and owner-timeline-draft-history-3.md)
- Stop time: Mon 23 Nov 18:29 UTC / 23:59 IST (the lead's order; this file's older text printed the same stop time).
- Post: Wed 25 Nov 15:00 UTC / 20:30 IST.
- Cells marked "NOT SET: needs studio lead" have no time or text yet; nothing here sets them.
- Words: "you" = the owner (the human at the laptop). A13 = the lead's decision list item on the 4-hour rerun margin (work/decision-list-for-lead.md).


## Proposals (unverified)
Nothing in this section is decided. Each item is a proposal or an unchecked figure; the lead decides.
- Row 9 words: "film done, type end" (a NEW message from the studio lead). The studio lead has not confirmed these words; until then the row is a proposal. It replaces the OWNER-VIEW "order of messages" (older text is in owner-timeline-draft-history.md).
- Row 7: if "program paused" has not arrived 10 minutes after you typed `y`, type nothing, press no Ctrl-C and tell the studio lead. The 10-minute limit is my proposal; no file sets it.
- Latest start (PROPOSAL, from work/critical-path-r2.md): about Mon 23 Nov 17:40 UTC / 23:10 IST, for the lead's worst case of 49 minutes (17:40 + 0:49 = 18:29). What fills the 49 minutes is NOT STATED in any file; if the real worst case is longer, the start moves earlier by the same amount. This REPLACES the older figure 18:14:40 UTC / 23:44:40 IST, which left a window of only 14 min 20 s and is out of date (34 min 40 s too late against the lead's 49 minutes). The older rule "never round it" now applies to the 17:40 figure: do not round it later. v5's 18:15 / 23:45 is also out of date. UNVERIFIED: nobody has checked the 49 minutes.
- Studio lead notice (at least 3 hours before the start), all times PROPOSAL, base case = work/critical-path-r2.md section 2 (decision A13 = no, no rerun): the notice must be sent by Mon 23 Nov 14:40 UTC / 20:10 IST. If decision A13 = yes (4-hour rerun margin; the same 4 hours as before applied to 17:40): the last start of the first run is 13:40 UTC / 19:10 IST and the notice must come by 10:40 UTC / 16:10 IST; a second run may then start no later than 17:40 UTC / 23:10 IST and must end by 18:29 UTC / 23:59 IST. A13 is undecided. The base case (A13 = no) is my PROPOSAL; the lead decides.
- Two readings of "3 hours notice" (the anchors differ): (1) 3 hours before the START of the run (this file's older rows, and r2 base): notice by 14:40 UTC / 20:10 IST (A13 = no) or 10:40 UTC / 16:10 IST (A13 = yes). (2) 3 hours before the owner's SETUP (laptop plugged in, sleep Never, lid action Do nothing), where setup is assumed 30 minutes before the start (r1's guess, no source): notice by 14:10 UTC / 19:40 IST (A13 = no) or 10:10 UTC / 15:40 IST (A13 = yes). The two differ by 30 minutes; reading (2) is the stricter one. PROPOSAL: use reading (1) as the base case; if the lead prefers the stricter reading, send 30 minutes earlier. The owner notice in row 1 is the same message in both readings. The older draft figures 15:14:40 / 11:14:40 UTC are out of date.
- Time source: the times in this section come from work/critical-path-r2.md (DRAFT, unverified; no durations were measured). Row 4 (owner yes) and its cell "stop time" keep Mon 23 Nov 18:29 UTC / 23:59 IST; a start time in a row 1 notice, when filled, would be the PROPOSAL 17:40 UTC / 23:10 IST unless the lead changes it.
