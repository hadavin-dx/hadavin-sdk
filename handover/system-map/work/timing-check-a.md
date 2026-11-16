Status: DRAFT, unverified

# Timing check A: take-day timing sentences against the 49-minute worst-case window

Written 2026-11-16 (UTC) by timing checker A. Read-only check; nothing was run. No sub-agents, no spend.

## What I could not check (read first)

1. The take-day runbook v4.2 is not in this checkout. The nearest text is OWNER-STEPS-realrun-v5-core-hardening.md, which calls itself "version 5" (line 1, line 3). I cannot say whether v4.2 and v5 word the timing sentences the same way. Every finding below is about v5.
2. The source of the "49-minute worst-case window" is not in the three files. I searched `handover/` for "49 min", "49-minute", "17:40" and "worst-case window". The only hit is the lead's own order at `handover/system-map/ORDERS.md:183`. I do not know what the 49 minutes are made of (which steps, which worst case). I did not invent a breakdown.
3. The run program (`scripts/run_real_check_n8n.py`) and the settings file `stage.env` are not in this checkout. I cannot check where the "about 14 minutes" figure comes from, or whether it is a fixed number or computed.
4. The two speed files (RUNBOOK-SPEED-3.md, RUNBOOK-INPUTS.md) are about proving test speed on a cloud container and the laptop. They are not the take-day runbook. They have no take-day timing sentences. I list their time statements only so the lead can see which would clash with the 49-minute window if they were ever run in it.
5. Click paths and durations on the owner's laptop were not checked.

## The arithmetic (visible)

| Item | Calculation | Result |
|---|---|---|
| Window end | given | 18:29Z = 23:59 IST (18:29 + 5:30 = 23:59, checked) |
| Latest start for a 49-minute worst case | 18:29 minus 49 min | 17:40Z = 23:10 IST |
| Latest start in v5 today | 18:29 minus 14 min (line 17, line 201) | 18:15Z = 23:45 IST (checked) |
| Gap between the two | 18:15 minus 17:40 | 35 minutes |
| Check of the weekday | 16 Nov 2026 is Monday (line 3), plus 7 days | 23 Nov 2026 is Monday (matches line 17 and line 46) |
| Post time | Wed 25 Nov 15:00Z + 5:30 | 20:30 IST (matches line 164) |

Durations the v5 sheet STATES for the take day: only two. (a) "about 14 minutes" the program needs before the stop time (lines 17, 201). (b) "under 2 seconds" typed answers are refused (line 116). Sum of stated step durations: 14 minutes. That cannot be reconciled with 49 minutes, and the file gives no way to split 49 into steps.

Durations MISSING in v5 (so no total can be built from it): step A to D (no length), checks of both logins, the 13 sends, the model calls, the n8n stop and restart while person C is sent (line 120), the film pause (step F, ends only when a person types `end`, no limit), the program's final counts, and the time a failed run needs to clean up and start again (step G).

Consequence: if the worst-case run takes 49 minutes from start to the last deletion, the program's start check (14 minutes) lets the owner start at 18:14Z and run to 19:03Z, 34 minutes past the stop time. The 14 must become 49 (or the real worst case), or the window must be redefined. I cannot tell which from these files.

## Part 1. OWNER-STEPS-realrun-v5-core-hardening.md (213 lines)

Conflict column: YES = conflicts with a 49-minute worst case ending 18:29Z; GAP = no time stated where one is needed; NO = compatible; OPEN = the file itself says open.

| # | file:line | Quoted text | Conflict? | Proposed new wording |
|---|---|---|---|---|
| 1 | v5:17 | "Planned: 2026-11-23 18:29 UTC = 23:59 IST (Mon 23 Nov 2026). The program refuses a start that is too close to it (it needs about 14 minutes), so the latest start is before about 18:15 UTC = 23:45 IST; the studio lead gives you the exact latest start time." | YES. 18:15Z is 25 min after 17:40Z. | "Planned: 2026-11-23 18:29 UTC = 23:59 IST (Mon 23 Nov 2026). The whole run, in its slowest case, takes up to 49 minutes. The program refuses a start that leaves less than 49 minutes before this time, so the latest start is 17:40 UTC = 23:10 IST. The studio lead gives you the exact latest start time." (Only after the lead confirms what the 49 minutes contain; see the open question below.) |
| 2 | v5:201 | "the program refuses to start unless it can finish about 14 minutes before the stop time. With stop time 18:29 UTC, the latest start is before about 18:15 UTC (23:45 IST). The studio lead gives the exact time." | YES (same number as row 1). Also: "finish about 14 minutes before the stop time" says the opposite of line 17 (line 17: needs 14 minutes up to the stop time; line 201: finish 14 minutes BEFORE it). | "The program refuses to start unless the slowest case of the run (49 minutes) fits before the stop time. With stop time 18:29 UTC, the latest start is 17:40 UTC (23:10 IST). The studio lead gives the exact time." Fix the 14-before versus 14-until wording at the same time (one meaning). |
| 3 | v5:191 | "2: the program refused to start or to go on (... the stop time too close)." | NO. Wording stays valid. | No change. |
| 4 | v5:46 | "Fixed times: stop time 18:29 UTC = 23:59 IST on Mon 23 Nov 2026. The stop time limits only the start and the spending of the run." | Partly. The sentence says the stop time limits "only the start and the spending". With a 49-minute worst case, the film pause (step F) and the clean-up of a failed run also sit inside the window; the sentence does not say whether they do. | "Fixed times: stop time 18:29 UTC = 23:59 IST on Mon 23 Nov 2026. By this time the run must have finished spending and must have deleted its contacts (steps E and F). Watching the video (H) and clean-up (I) come later and have their own deadlines." Lead must confirm which steps are inside the 49 minutes. |
| 5 | v5:46 | "Watching (H) and clean-up (I) have their own deadlines, which the studio lead gives you (open)" | OPEN / GAP. No deadline written. | Replace "(open)" with the two real deadlines in UTC and IST once the lead sets them. |
| 6 | v5:46 | "The post is planned for Wed 25 Nov 2026, 15:00 UTC = 20:30 IST." | NO. Arithmetic checked. | No change. |
| 7 | v5:52 | "A spending backstop and the stop time sit in a settings file" | NO (no number), but the settings file must hold the 49-minute rule, not 14. | After "stop time", add: "and the 49-minute start rule". |
| 8 | v5:72-73 | Step A message lists "the spending backstop and the stop time as they stand in the settings file `stage.env`" and "the planned stop time 2026-11-23 18:29 UTC = 23:59 IST" | GAP. The yes message does not state the latest start. | Add a bullet: "the latest start time, 17:40 UTC = 23:10 IST, and the slowest-case length of the run, 49 minutes". The yes line in row 9 must repeat it. |
| 9 | v5:76 | Example yes: "...stop time 2026-11-23 23:59 IST." | GAP. No start time in the yes. | "Yes, run <run name>, up to 3 model calls and up to US$<total>, start no later than 2026-11-23 23:10 IST (17:40 UTC), stop time 2026-11-23 23:59 IST (18:29 UTC)." |
| 10 | v5:39 and 38-45 (Order of the day) | Steps A to F listed with no times. | GAP. With a latest start at 17:40Z, steps A to D (yes, laptop settings, mailbox check, profile, filming check) must be finished before it. No sentence says how long they take or when they must be done. | Add one line under "Order of the day": "Steps A to D must be finished by 17:25 UTC = 22:55 IST (15 minutes before the latest start of 17:40 UTC = 23:10 IST). Step E starts at the time the studio lead names, never later than 17:40 UTC." The 15 minutes is a PROPOSED margin, not a measured one; the lead must set it. |
| 11 | v5:87-90 (step C) | "Run day, before the studio lead says go" | GAP. No duration for the mailbox check, the browser profile or the n8n sign-in (line 90 may be long: new owner login and three connections typed again). | Add a stated length per sub-step after the owner times one rehearsal, or write "allow 20 minutes (PROPOSED, not measured)" until measured. |
| 12 | v5:108-113 (step E) | Four screens in order, no times. | GAP. Time from typing the command to the notice, and from the notice to the sends, is not stated. | State the measured length from rehearsal ("the notice appears within about N minutes"). I could not measure this; the rehearsal has not been run (line 205). |
| 13 | v5:116 | "An answer typed in under 2 seconds is refused." | NO. | No change. |
| 14 | v5:120 | "The studio lead's session stops and restarts n8n while person C is sent." | GAP. Length of the stop and restart is not stated (it belongs in the 49 minutes). | Add "this takes about N seconds (measured in the rehearsal)". |
| 15 | v5:127 (step F) | "Type `end` ... only when that person tells you the contact list is filmed" | YES in worst case. The film pause has no time limit and sits between the sends and the deletion. If the owner is slow, the pause eats the window and deletion may fall after 18:29Z. | Add: "The film pause is at most N minutes. If filming is not done N minutes after the pause starts, tell the studio lead; the contacts must be deleted before 18:29 UTC = 23:59 IST." N is the lead's choice. |
| 16 | v5:134-140 (step G) | "Give a NEW written yes with numbers ... pick a NEW run name." and "If the studio lead later says a new run is no longer possible before the stop time, no new run happens." | YES. A second run needs another full worst case (49 minutes) plus clean-up of the first. Window start 17:40 plus 49 = 18:29: the first run alone fills the window, so a rerun cannot fit. The sheet does not say that. | Add: "A second run fits only if the first run failed and was cleaned up early enough that a new start still comes before 17:40 UTC = 23:10 IST. With a latest start of 17:40 UTC, a rerun on the same day is possible only if the first start was before about 16:30 UTC (PROPOSED: first run's failure point plus clean-up must be known)." Better: "There is no rerun margin on the take day. A failed run means a new day." Lead decides; the file today says "before the stop time" which is too loose. |
| 17 | v5:62 (rule 6) | "On run days: laptop on mains power, sleep Never..." | NO (no time). | No change. |
| 18 | v5:145 (step H) | "The studio lead tells you the deadline." | OPEN. | Fill in UTC and IST when set. |
| 19 | v5:150-159 (step I) | "Starts when the studio lead says the last run is done." deadline "from the studio lead" | OPEN. Not tied to the window. | Fill in UTC and IST when set. |
| 20 | v5:154 | "Run it BEFORE the secret files are deleted" | NO (order, not time). | No change. |
| 21 | v5:206-213 ("What is not proven yet") | Lists that the rehearsal has not run. | GAP. No line says the 49-minute worst case is not measured. | Add: "The 49-minute worst case is a planning figure. It has not been measured; the rehearsal measures it." (Only if true; the lead confirms.) |

Open question for the lead (needed before rows 1, 2, 10, 16 can be finalised): what are the 49 minutes made of, and does the window include steps A to D, the film pause (F) and the failed-run clean-up (G)? I could not find it.

## Part 2. RUNBOOK-SPEED-3.md (108 lines): test-speed proof windows

These are test windows on the cloud container and laptop, not the take day. They conflict only if run in the same 17:40Z to 18:29Z period or on the owner's laptop that day.

| # | file:line | Quoted text | Check | Conflict with 49-minute window? | Proposed wording |
|---|---|---|---|---|---|
| 22 | SPEED-3:75 | "Per window add 20 minutes slack ... a full demo item = 2 x 15 + 3 x 7 = about 51 min + 20 slack = about 71 min." | Arithmetic: 2 x 15 = 30; 3 x 7 = 21; 30 + 21 = 51; 51 + 20 = 71. Correct. | YES if scheduled inside the take window: 71 minutes > 49. | Add: "Do not run this window on the take day or on the take laptop between 17:00 UTC and 18:29 UTC on Mon 23 Nov 2026." |
| 23 | SPEED-3:75 | "sdk-Linux ... 2 x 14 + 3 x 8 + broken 8 + posix 1 = about 61 min + 20 = about 81 min." | 28 + 24 + 8 + 1 = 61; 61 + 20 = 81. Correct. (Note: the laptop serial median is 804.5 s = 13.4 min, so "14" is rounded up.) | YES, 81 > 49. | Same as row 22. |
| 24 | SPEED-3:75 | "Run demo and sdk in SEPARATE windows, never at the same time" | Total if one after the other: 71 + 81 = 152 min. | YES if both on the take day. | State the 152-minute total and keep both off the take day. |
| 25 | SPEED-3:72 | "wait 2 minutes, retry once; if still not quiet, stop the window" | Rerun margin inside a window is 2 minutes. | NO (small). | No change. |
| 26 | SPEED-3:46, 49-50 (3b) | Windows runs use `heavy_slot` on the laptop, "max 4 slots, use 2 per run" | Laptop load. The take run is on the same owner laptop (v5:62, 108). | GAP: nothing says the laptop must be free of speed runs on the take day. The rule at line 11 item 3 (CPU outside tests < 15 percent) would discard such a run, but the take run would be slowed. | Add to the take-day sheet or this file: "No speed run, mutation run or heavy job on the owner's laptop from 17:00 UTC until the clean-up is done on the take day." |
| 27 | SPEED-3:9 | "439.7 / 804.5 = 0.55" | 439.7 / 804.5 = 0.5465, rounds to 0.55. Correct. | NO. | No change. |
| 28 | SPEED-3:42 | "lane-6 measured 886-953 s on this container" (via line 75) | 886 s = 14.8 min; 953 s = 15.9 min. "about 15" fine. | NO. | No change. |
| 29 | SPEED-3:82, 91 | "win serial 1206 s, par 423-439 s (0.35 x)" and "867.0 s vs 296.6 s" | 423/1206 = 0.351, 439/1206 = 0.364 (so "0.35 x" is the low end; the high end is 0.36); 296.6/867.0 = 0.342. | NO. Minor precision only. | "0.35 to 0.36 x". |
| 30 | SPEED-3:3, 20 | "Written 2026-11-12 (UTC)" | Date only. | NO. | No change. |

## Part 3. RUNBOOK-INPUTS.md (38 lines): facts measured in the demo cloud container

| # | file:line | Quoted text | Check | Conflict with 49-minute window? | Proposed wording |
|---|---|---|---|---|---|
| 31 | INPUTS:2 | "Status: DRAFT (updated below ...) at 2026-11-12 19:05Z." | Internal inconsistency: line 37 holds a sample taken "2026-11-12T19:45:30Z", 40 minutes after the stated update time. | NO (not a window issue). Wrong time stamp. | "updated at 2026-11-12 19:45Z or later" (or move the stamp to match the last sample). |
| 32 | INPUTS:27-31 | Serial runs 886 s, 1026 s, 894.6 s, 225 s, 953 s | 886/60 = 14.8 min; 1026/60 = 17.1 min; 894.6/60 = 14.9 min; 225/60 = 3.75 min; 953/60 = 15.9 min. | YES if a full run is attempted in a 49-minute window together with other work: one serial run alone is 15 to 17 minutes (about a third of 49). | Add: "A full serial run takes 15 to 17 minutes; do not start one inside the take window." |
| 33 | INPUTS:32 | "about 15 minutes without Playwright and about 17 minutes with it ... a lead estimate of 16 minutes holds." | 14.8 and 17.1 agree. | NO. | No change. |
| 34 | INPUTS:32 | "one hung run killed after more than 10 minutes near test 840" | Unexplained hang; unbounded risk on a shared machine. | Only if run in the window. | No change; it belongs with row 26. |
| 35 | INPUTS:17, 36-38 | Load averages and "NOT an idle sample" | No window figure. | NO. | No change. The idle sample is still missing, so a "quiet container" claim is unproven. |

## Summary for the lead

1. Sentences that MUST change (conflict with a 49-minute worst case): v5:17, v5:201 (14 minutes and 18:15Z become 49 minutes and 17:40Z / 23:10 IST; also fix the 14-before versus 14-until contradiction), v5:127 (film pause has no time limit), v5:134-140 (rerun margin: none fits inside the window), plus the speed-file windows at SPEED-3:75 if they could fall on the take day.
2. Sentences that SHOULD be added (gaps): latest start in the written yes (v5:72-76), a deadline for steps A to D (v5:38-45), step durations from the rehearsal (v5:87-90, 108-113, 120), deadlines for H and I (v5:46, 145, 150), and a line that no heavy job runs on the take laptop (SPEED-3 row 26).
3. Sentences that are fine: v5:116, 164, 191, SPEED-3:9, 72.
4. Not found, needed from the lead: what the 49 minutes contain, and the run program's own source for the "14 minutes" figure. Without them the new numbers in rows 1, 2, 10, 15 and 16 are proposals.
5. The speed files do not change the take-day window unless someone schedules them in it; the main risk is the shared owner laptop.
