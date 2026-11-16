# DRAFT: replacement for OWNER-VIEW "order of messages" (16 Nov 2026, from an independent style read; NOT applied)
Held because: (1) the lead must say whether the film pause stays (QUESTIONS item 8); (2) OWNER-VIEW row 3 still says `end` DELETES, and decision 2 says it deletes nothing; (3) cells marked [studio lead fills] have no source file. Made-up data only. Times: UTC and IST (IST = UTC+5:30).

The run never deletes anything. `end` only stops the run. Leftover made-up contacts are deleted by hand. Do nothing in a row until the message above it has arrived.

| # | Who sends | Exact words | What you do | Can it be undone? |
|---|---|---|---|---|
| 1 | Studio lead | [studio lead fills: exact words]; run date and start time in UTC and IST, at least 3 hours ahead | Nothing until it arrives; then laptop plugged in, sleep Never, lid action Do nothing | yes |
| 2 | Studio lead | "rehearsal passed" and the result file name | No file name: do not send your yes | yes |
| 3 | Studio lead | [studio lead fills]; at most 3 model calls, worst-case price of one call, 3 times that in US dollars, money spent so far, spending backstop, stop time, path of `stage.env` | Open `stage.env`; compare money spent so far and the backstop with the message; a number missing or different: type nothing, tell the studio lead | yes |
| 4 | You | "Yes, run <run name>, up to 3 model calls and up to US$<total> (3 times the worst-case price of one call), stop time Mon 23 Nov 2026 18:29 UTC / 23:59 IST." | Once per paid run, with a run name never used before | yes; no money moves until you type `y` |
| 5 | Studio lead | "start now" | Terminal; type the lines the studio lead sends; both login lines must say "still works" (good here) | yes |
| 6 | You | `y`, then `<6 digits> <run name>` | Type both yourself, only after the figures match your yes | NO: up to 3 paid calls start |
| 7 | Studio lead | "program paused" (draft card only; pause not confirmed) | Type nothing; film the HubSpot contact list; no Ctrl-C, do not close the terminal | yes |
| 8 | You | "film done" | Only after you checked the film file exists and plays | yes |
| 9 | Studio lead | a new message beginning exactly "film done, type end" | Type `end`, Enter. Deletes nothing. Screen says "delete" or "archive": type nothing, tell the studio lead | pause ends; nothing deleted |
| 10 | Studio lead | [studio lead fills]; count of leftover made-up contacts | Delete by hand only contacts whose email is exactly one of the 3 test addresses named; reply "contacts deleted" and the number | NO (HubSpot may keep a recoverable copy: not checked) |
| 11 | Studio lead | "demo mails may be deleted" (failed run only) | Delete demo mails (Inbox, label `demo`), empty Trash; reply "demo mails deleted"; new run name and new yes | NO |
| 12 | You | "accepted" (after watching the edited video twice) | Only if no further run is needed | NO: ends all runs |
| 13 | Studio lead | "last run done" | With your "accepted": clean-up step 1 | NO |
| 14 | Studio lead | "delete these apps: ..." | Delete exactly those HubSpot private apps; screenshot | NO |
| 15 | Studio lead | "run the check" plus command | Run it, `echo $?`; "refused as expected" (0) good; "STILL WORKS" (3) bad: say which login | yes |
| 16 | You | "retire check passed" | Only if both logins printed "refused as expected" | yes |
| 17 | Studio lead | "n8n removal done" | Wait | NO |
| 18 | Studio lead | "secret files may be deleted" | Delete only the names sent, `shred -u --` line compared letter by letter; reply "secret files deleted" | NO |
| 19 | You | "model key revoked" | Revoke it yourself, only after row 16; then restore sleep and lid values, sign out of `demo-take` | NO |
| 20 | Studio lead | [studio lead fills: final post words] | Second person checks the post; send the text to the studio lead first; you post | NO |

Time limits: stop time Mon 23 Nov 18:29 UTC / 23:59 IST (last minute the program allows); latest start 18:14:40 UTC / 23:44:40 IST (v5 rounds to 18:15 / 23:45); notice at least 3 h before the start (last day: before about 15:14 UTC / 20:44 IST); post Wed 25 Nov 15:00 UTC / 20:30 IST (does not move); run date target Wed 18 Nov NOT confirmed; video-watch and clean-up deadlines [studio lead fills], not tied to the stop time.
