# C4b v5 naive reader (egm comprehension), condensed copy, 2026-11-16
READINESS: MAJOR (not blocker). Reader read only OWNER-STEPS-realrun-v5.md (213 lines, not truncated). Line numbers are v5.
## Fix before the owner sees it
1 Open items that decide owner actions sit in a file the owner cannot see: who films/edits (l.94), who types the n8n stop/restart during the run (l.120), whether a trial run happens (l.26), run name format "likely, not confirmed" (l.13; the yes example l.76 needs the name), HubSpot key can delete contacts (l.130, owner has no check). Resolve or give the owner a check.
2 The studio lead is a Claude session with no access to the owner's screen (l.9) yet l.120 and l.158 give it laptop actions (stop/start n8n, remove folder and container). State plainly who types each.
3 Wrong cross-reference l.154 "removed in step 6": step 6 (l.159) only deletes secret files; I.4 vs I.5 disagree on who removes the settings file and the run folder.
4 Words box "Delete = gone for good" (l.31) vs same line admitting HubSpot may keep a recoverable copy (not checked).
5 Two "settings files" (the `--take` file l.14 vs `stage.env` l.72); "spending backstop" (l.52,72) undefined next to "no dollar ceiling".
6 Missing: where to save the new n8n password (l.90); expected duration of the run and the start time to plan (l.120); no sign of "finished" and no stuck guidance.
7 Undefined: proof screen, crash-safe/crash test (l.170), independent login (l.171), executions saving (l.158), "run program" (l.119), Hook door (l.21, no owner action), lead/test person/contact, label vs folder demo, "settings" (laptop/file/n8n).
8 Step F mistype: add that contacts are then gone, the spend is spent and a new run needs a new yes; box lacks "closed input on first prompt ends pause at once" (l.127).
9 l.151: how to crop screenshots (name a tool); App passwords needs 2-Step Verification; Gmail "select all" in Inbox caution; HubSpot filter for run-name contacts in F (path only in G).
10 Move or shrink "What is not proven yet" (l.203-213) out of the owner sheet.
## Smaller
l.3 "studio lead's instructions win over this sheet" weakens the sheet; l.5 done items have no check the owner can do (HubSpot delete right, label demo exists); order of B,C,D vs A and how many days ahead; fast-typing refusal (l.116) exit code unlisted; login failure exit code unlisted (l.109); l.191 vs l.200 lock-per-name unclear; I.1 revoke has no confirmed list; l.99/207 "company address" undefined; "archive" printed by the program vs sheet saying delete (hazard if screen text differs); l.164 final words not yet available and who checks them is open; I.2 key-question hard to answer (no mapping file name to private app); `retire` and "real company mailbox" l.63 has no checkable action.
IST/UTC arithmetic and weekdays checked right (18:29 UTC = 23:59 IST; 25 Nov 15:00 UTC = 20:30 IST).
