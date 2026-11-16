Status: DRAFT, unverified

# Runbook v4.3 patch, part 3: timing sentences (49-minute worst case)

Written 2026-11-16 (UTC) by builder C. Static work: I read files only; nothing was run, no spend, no sub-agents.

## Read first: what this patch is not

1. The v4.2 file is not in this checkout. Every "target" below is a line of `handover/system-map/inputs/OWNER-STEPS-realrun-v5-core-hardening.md` (called "v5" here), which calls itself version 5. I cannot say whether v4.2 words these sentences the same way. The lead must map each row to the v4.2 file before applying it.
2. The 49 minutes are an order from `handover/system-map/ORDERS.md:183`, not a measured value. I do not know what they contain (see OPEN QUESTION). Every new number below that depends on 49 is therefore a PROPOSAL until the lead answers.
3. The "old text" for the v5 rows was read by me from the v5 file today. The old text for rows P7 to P10 (other files) is quoted from `timing-check-a.md`; I did not re-read those files.
4. Source for every row: `handover/system-map/work/timing-check-a.md` ("TCA" below), with its row number.

Arithmetic used (checked): 18:29 UTC minus 49 minutes = 17:40 UTC; 17:40 UTC + 5:30 = 23:10 IST; 18:29 UTC + 5:30 = 23:59 IST. 17:40 UTC minus 15 minutes = 17:25 UTC = 22:55 IST.

## Patch rows (all of TCA's "YES" / MUST CHANGE rows)

Format: id | target (file and line) | old text | new text | source

### P1 | v5 line 17 (Stop time bullet)

Old text:
> The program refuses a start that is too close to it (it needs about 14 minutes), so the latest start is before about 18:15 UTC = 23:45 IST; the studio lead gives you the exact latest start time.

New text (PROPOSAL, depends on the open question):
> The whole run, in its slowest case, takes up to 49 minutes. The program refuses a start that leaves less than 49 minutes before this time, so the latest start is 17:40 UTC = 23:10 IST; the studio lead gives you the exact latest start time.

Source: TCA row 1.

### P2 | v5 line 201 (Start deadline bullet)

Old text:
> - **Start deadline:** the program refuses to start unless it can finish about 14 minutes before the stop time. With stop time 18:29 UTC, the latest start is before about 18:15 UTC (23:45 IST). The studio lead gives the exact time.

New text (PROPOSAL):
> - **Start deadline:** the program refuses to start unless the slowest case of the run (49 minutes) fits before the stop time. With stop time 18:29 UTC, the latest start is 17:40 UTC (23:10 IST). The studio lead gives the exact time.

Also fixes a wording clash: line 17 says the program "needs" about 14 minutes up to the stop time; line 201 says it must "finish" 14 minutes BEFORE the stop time. The new text uses one meaning (the run's slowest case must end by the stop time). The program's own number (the "14") lives in code or in `stage.env`, neither of which is in this checkout, so the matching change in the program or settings file is a separate item for the lead (cannot be done from here).

Source: TCA row 2, and TCA "arithmetic" section (with a 14-minute rule an owner could start at 18:14 UTC and run until 19:03 UTC, 34 minutes past the stop time).

### P3 | v5 line 127 (Step F, film pause)

Old text (the sentence to extend; the rest of the line stays):
> Type `end` and Enter yourself only when that person tells you the contact list is filmed (if you film, when you have filmed it).

New text (PROPOSAL; N is the lead's choice, not measured):
> Type `end` and Enter yourself only when that person tells you the contact list is filmed (if you film, when you have filmed it). The film pause lasts at most N minutes. If filming is not finished N minutes after the pause starts, tell the studio lead at once. This run's contacts must be deleted before 18:29 UTC = 23:59 IST.

Reason: today the pause has no limit and sits between the sends and the deletion, so a slow film can push deletion past the stop time.

Source: TCA row 15.

### P4 | v5 lines 134-140 (Step G, failed run)

Old text (line 140):
> If the studio lead later says a new run is no longer possible before the stop time, no new run happens.

New text, option 1 (PROPOSAL, stricter; TCA's own preferred wording):
> There is no spare time for a second run on the take day: one run in its slowest case fills the whole window (17:40 UTC plus 49 minutes is 18:29 UTC). A failed run therefore means a new run day.

New text, option 2 (PROPOSAL, weaker):
> A second run is possible only if the first run failed and was cleaned up early enough that the new start still comes before 17:40 UTC = 23:10 IST. The studio lead decides this and says so by message; otherwise no new run happens.

The lead picks one. Option 1 only holds if the 49 minutes are a full run from start to last deletion; option 2 is needed if they are not.

Also check line 139 ("Give a NEW written yes with numbers ... pick a NEW run name"): it stays, but the new yes must carry the latest start time (see P11).

Source: TCA row 16.

### P5 (other target) | `RUNBOOK-SPEED-3.md` line 75 (test-speed windows)

Old text (quoted from TCA, not re-read): "Per window add 20 minutes slack ... a full demo item = 2 x 15 + 3 x 7 = about 51 min + 20 slack = about 71 min." and "sdk-Linux ... 2 x 14 + 3 x 8 + broken 8 + posix 1 = about 61 min + 20 = about 81 min." and "Run demo and sdk in SEPARATE windows, never at the same time".

New text (PROPOSAL), add after line 75:
> Do not run these windows on the take day, or on the take laptop, between 17:00 UTC and 18:29 UTC on Mon 23 Nov 2026. The two windows together take 71 + 81 = 152 minutes; each alone is longer than the 49-minute take window.

TCA checked the arithmetic (51, 71, 61, 81 correct).

Source: TCA rows 22, 23, 24 (and row 26 for the laptop rule, which is a GAP row; included here because it is the same sentence).

### P6 (other target) | `RUNBOOK-INPUTS.md` lines 27-32 (serial run lengths)

Old text (quoted from TCA, not re-read): serial runs of 886 s, 1026 s, 894.6 s, 953 s, and "about 15 minutes without Playwright and about 17 minutes with it".

New text (PROPOSAL), add after line 32:
> A full serial run takes 15 to 17 minutes. Do not start one inside the take window.

Source: TCA row 32.

## Rows that depend on the patch rows (TCA "GAP", not "YES"; included because P1 to P4 are incomplete without them; PROPOSALS)

### P7 | v5 line 76 (example yes) and lines 72-73 (step A list)

Old text, line 76: `"Yes, run <run name>, up to 3 model calls and up to US$<the total in the message>, stop time 2026-11-23 23:59 IST."`
New text: `"Yes, run <run name>, up to 3 model calls and up to US$<the total in the message>, start no later than 2026-11-23 23:10 IST (17:40 UTC), stop time 2026-11-23 23:59 IST (18:29 UTC)."`
Old text, line 73: `- the planned stop time 2026-11-23 18:29 UTC = 23:59 IST;`
New text: add after it: `- the latest start time, 17:40 UTC = 23:10 IST, and the slowest-case length of the run, 49 minutes;`
Source: TCA rows 8, 9.

### P8 | v5 lines 38-45 (Order of the day)

Old text: the seven numbered steps A to J with no times.
New text: add one line after line 45: `Steps A to D must be finished by 17:25 UTC = 22:55 IST (15 minutes before the latest start of 17:40 UTC = 23:10 IST). Step E starts at the time the studio lead names, never later than 17:40 UTC.`
PROPOSAL. The 17:25 UTC deadline and its 15-minute margin are a proposed margin, not a measured one; the lead sets it.
Source: TCA row 10.

### P9 | v5 line 46 (Fixed times)

Old text: `The stop time limits only the start and the spending of the run. Watching (H) and clean-up (I) have their own deadlines, which the studio lead gives you (open); they are not tied to the stop time.`
New text (PROPOSAL, only after the lead confirms which steps sit inside the 49 minutes): `By the stop time the run must have finished spending and must have deleted its contacts (steps E and F). Watching (H) and clean-up (I) come later and have their own deadlines, which the studio lead gives you in UTC and IST.`
Source: TCA rows 4, 5 (and 18, 19 for the H and I deadlines, which are still empty: lines 145 and 150-152 say only "the studio lead gives you the deadline").

### P10 | v5 lines 206-213 ("What is not proven yet")

Add as a new bullet: `The 49-minute worst case is a planning figure. It has not been measured; the rehearsal measures it.` Only if true; the lead confirms.
Source: TCA row 21.

### P11 | v5 line 52 (settings file sentence)

Old text: `A spending backstop and the stop time sit in a settings file that a person checks`
New text: `A spending backstop, the stop time and the 49-minute start rule sit in a settings file that a person checks`
Only valid if the program really takes the rule from the settings file; I cannot see the program or `stage.env`, so this is UNVERIFIED.
Source: TCA row 7.

### P12 | durations missing (v5 lines 87-90, 108-113, 120)

TCA rows 11, 12, 14: no length is written for step C (mailbox, browser profile, n8n sign-in), step E (command to notice, notice to sends) or the n8n stop and restart. Do not invent numbers. Until the rehearsal measures them, the only wording I can propose is: add "allow 20 minutes (PROPOSED, not measured)" at the end of step C, and "(length to be measured in the rehearsal)" at lines 108 and 120. The rehearsal has not run (v5 line 205 region).

## Rows left unchanged (TCA "NO")

v5 line 116 (2 seconds), line 164 (post time 20:30 IST), line 191 (exit code 2 wording), SPEED-3 line 9, line 72. No change.

## OPEN QUESTION for the lead (blocks P1, P2, P3, P4, P8, P9)

What exactly do the 49 minutes contain? The only mention in `handover/` is `ORDERS.md` line 183 ("the 49-minute worst-case window (latest start about 17:40Z for window end 18:29Z)"). It does not say:

1. Which steps: does the 49 minutes start at typing the command (step E) or at step A? Does it include steps A to D (so their deadline would be earlier than 17:25 UTC)?
2. Does it include the film pause (F), and at what length? (P3's N depends on this.)
3. Does it include a failed run's clean-up (G) and a second run? (Decides P4 option 1 or 2.)
4. Does it include the n8n stop and restart while person C is sent (line 120)?
5. Is 49 minutes a measured worst case or a planning figure? (Decides P10.)
6. Where does the program's current "about 14 minutes" come from, and where is it changed (program source or `stage.env`)? Neither is in this checkout.

Also not checked: the run program, `stage.env`, any click path on the owner's laptop, and whether v4.2 and v5 word these lines the same way.
