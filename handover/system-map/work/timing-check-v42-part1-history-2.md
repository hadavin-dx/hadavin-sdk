Status: DRAFT. Unverified: (a) what the 49 minutes contain; (b) whether the 17:40Z latest start is right; (c) every minute figure in the runbook (they are estimates, not measurements); (d) runbook lines 321 to end (another checker's range). Checked only: the arithmetic on this page, by hand. Nothing was run.

# Timing check H1, part 1: take-day runbook v4.2, lines 1 to 320, against the 49-minute worst-case window

## In three lines

1. 49 min = the lead session's order (ORDERS.md line 183); what it contains is unconfirmed. Latest start 17:40Z / 23:10 IST (window end 18:29Z minus 49 min).
2. Finding for the lead session: the runbook plans the take at "about 60 min" but the window assumes 49 min. If the 49 is the take, the plan is 11 min longer than the window. The lead session must say which number is right and what the 49 contains.
3. Every PROPOSAL below that uses 49 or 17:40Z is conditional on that answer. Nothing in the runbook has been changed.

## Words used on this page

Definitions use `work/GLOSSARY.md` wording where it has one; other entries say where they come from.
- **take**: one recorded (filmed) run of the lead-intake demo on made-up data (GLOSSARY.md). **take program**: the script that runs it, `scripts/run_real_check_n8n.py` (named in part 2; not in this checkout).
- **lead session**: the Claude session that gives orders to the system-map session through ORDERS.md (GLOSSARY.md). This page says "the lead" in many rows; read each as "lead session". **studio lead**: the Claude session that does the technical steps and is the only one that messages the owner. **owner**: the human at the laptop who gives the written yes.
- **gate** (start-state gate): a check of about 25 minutes, planned before the take, on Wed 18 Nov, that the demo is in the right state; the decision is by 10:00Z. Source: runbook lines 93 and 217. What it checks in detail: not covered by this page.
- **re-pin**: pointing the demo at a new fixed version of the core code (a version id called a sha). The runbook's whole re-pin event is estimated at 223 minutes (line 86). **re-smoke**: a repeat quick test run after the re-pin. The runbook says it has no time limit (line 88). The meaning of "smoke" is my reading, UNVERIFIED.
- **Row 4**: the runbook's 30-minute Wednesday step (07:00Z to 07:30Z) in which the owner posts one test lead and checks the results. My reading from part 2 (runbook W-02); UNVERIFIED here.
- **G7**: runbook rule G7 (line 266): the chain of steps after the re-pin must end before 18:29Z.
- **H1**: the label of this check (timing checker 1, runbook lines 1-320). **v4.2** / **v5**: version 4.2 of the take-day runbook (the file checked here) and version 5 of the owner sheet (`inputs/OWNER-STEPS-realrun-v5-core-hardening.md`); `work/timing-check-a.md` is the earlier check of v5.
- **EGM**: the studio's review process. **bible**, **R-numbers**: the studio's rule book and its rule numbers. Neither is in this checkout, so I looked up no R-number.
- **Z** = UTC. **IST** = UTC + 5 h 30 min.

Written 2026-11-16 (UTC) by timing checker H1. Read-only check; nothing was run. No sub-agents, no spend. Source: `handover/system-map/inputs/lead-reviews/LEAD-RUNBOOK-TAKE-DAY-v4.2.md` lines 1-320 (all read), plus `work/timing-check-a.md` (the v5 findings, read).

## What I could not check (read first)

1. I do not know what the 49 minutes are made of. The only source is the lead session's order (`ORDERS.md:183`: "latest start about 17:40Z for window end 18:29Z"). Neither v4.2 (lines 1-320) nor timing-check-a defines it. So I cannot say whether the 49 minutes cover the take itself, the start-state gate, or the whole run program. Every "conflict" below is conditional on that. The planned-take point (60 min against 49 min) is also stated as finding 2 at the top.
2. v4.2 lines 321 to end (T-08 on, T-12, W-01 to W-05, section 10 and 12) are another checker's range; not read by me.
3. I did not check any figure against a measurement. The runbook itself says every minute figure is the lead's estimate (line 76), not a measurement.
4. The 14-minute rule and the 18:15Z latest start in timing-check-a are about the owner sheet v5, not v4.2. v4.2 lines 1-320 contain no "14 minutes" and no latest-start time at all (grep of my range; the only 18:29 hits are lines 107, 223, 236, 272 context). So the v5 finding does not carry over word for word.

## Arithmetic (all visible)

| Item | Calculation | Result |
|---|---|---|
| Window end | 18:29Z + 5:30 | 23:59 IST (correct, lines 107, 223) |
| Latest start | 18:29Z - 49 min | 17:40Z = 23:10 IST (17:40 + 5:30 = 23:10, correct) |
| Re-pin sum (line 209) | 08:00 - 223 min = 08:00 - 3 h 43 min | 04:17Z = 09:47 IST (correct) |
| Wed 06:00Z | + 5:30 | 11:30 IST (correct) |
| Practice (line 213) | 06:00 + 60 min | 07:00Z (correct); Row 4 07:00 + 30 = 07:30 (correct); rehearsal 07:30 + 2 h = 09:30 (correct) |
| Gate (line 217) | 09:30 + about 25 min | about 09:55Z, "decision by 10:00" (correct); IST 15:00 to 15:30 (correct) |
| Take (line 218) | 10:00 + about 1 h | 11:00Z = 16:30 IST (correct) |
| Watch (line 219) | 11:00 + 20 min | 11:20Z = 16:50 IST (correct) |
| Retake (line 226) | 25 + 60 + 120 + 20 | 225 min (correct); 15:00Z - 225 min = 11:15Z (correct) |
| Post (line 220) | 15:00Z + 5:30 | 20:30 IST (correct) |
| Slipped take cut-off (line 222) | Mon 23 Nov 12:00Z + 5:30 | 17:30 IST (correct) |
| NO-GO path re-pin (line 221) | 07:00Z + 5:30 | 12:30 IST (correct) |
| G7 chain (line 266) | 1 h (re-smoke) + 1 h (practice) + 0.5 h (Row 4) + 2 h (rehearsal) + 1 h (take) = 5.5 h; from 07:00Z = 12:30Z end; the 25-minute gate is not in the sum, so 12:55Z | before 17:40Z by 4 h 45 min (17:40 - 12:55) |
| STOP-N8N worst case (line 156) | 45 s + 5 s + 3 s | 53 s (correct) |
| Take (about 1 h) versus window | 60 min vs 49 min | the planned take (60) is 11 min LONGER than the worst-case window (49), if the 49 is the take |

Last row: if the 49 minutes is the take's own worst case (UNVERIFIED), a planned take of "about 1 h" (lines 94, 218, 266) does not fit the same figure. The two are not the same quantity (planned estimate versus worst case) but the runbook never says which one the window uses.

## Findings, by line

Conflict column: YES = conflicts with the 49-minute window / latest start 17:40Z; GAP = no time where one is needed; STALE = contradicts another v4.2 sentence; NO = compatible.

| # | Line | Quoted text | Conflict? | Why | PROPOSAL (not applied) |
|---|---|---|---|---|---|
| 1 | 107 | "Money stop Mon 23 Nov 18:29Z." | GAP | States only the end of the window. No latest start next to it. | PROPOSAL: "Money stop Mon 23 Nov 18:29Z (23:59 IST). If the lead session confirms the 49 minutes: the latest start of any run is 17:40Z (23:10 IST), because the slowest case would take 49 minutes (source: ORDERS.md line 183, unverified)." |
| 2 | 223 | "Credits / money stop \| Mon 23 Nov 18:29 \| 23:59 \| Q26-1" | GAP | Same: no row for the latest start. | PROPOSAL (only if the lead session confirms the 49): add a row above it: "Latest start of any run (slowest case 49 min, from ORDERS.md line 183, unverified) \| Mon 23 Nov 17:40 \| 23:10 \| 18:29 - 49 min". |
| 3 | 236 | "Window end for any spend: Mon 23 Nov 18:29Z (23:59 IST)." | GAP | A run started after 17:40Z can still be spending when 18:29Z passes. The sentence says nothing about starting. | PROPOSAL: "Window end for any spend: Mon 23 Nov 18:29Z (23:59 IST). If the lead session confirms the 49 minutes: no run starts after 17:40Z (23:10 IST), so that its slowest case ends before this time." |
| 4 | 94 and 218 | "THE TAKE ... about 1 h" / "Take (about 1 h) \| about 10:00 to 11:00" | YES (conditional) | 60 min planned > 49 min worst case if the window is the take. On Wed 18 Nov this does not matter (11:00Z is 7 h 29 min before 18:29Z, 18:29 - 11:00). On a slipped take (Mon 23 Nov) it matters: start at 17:40Z + 60 min = 18:40Z, 11 min past the end. | PROPOSAL: "Take: about 1 h planned. The lead session's order says 49 minutes for the slowest case; what it contains is UNVERIFIED." The lead session decides which number is right. |
| 5 | 222 | "NO-GO path: a slipped take is allowed until \| Mon 23 Nov 12:00 \| 17:30" | NO, but inconsistent in kind | 12:00Z is earlier than the latest start 17:40Z, by 5 h 40 min (17:40 - 12:00). It is not wrong; it is a stricter, older cut-off. Two cut-offs now exist and the file does not say which wins. | PROPOSAL: "A slipped take may start until Mon 23 Nov 12:00Z (17:30 IST); the hard latest start is 17:40Z (23:10 IST) for any run." Lead confirms whether 12:00 stays. |
| 6 | 265 (G6) | "the take slips one day at the same times, allowed until Mon 23 Nov 12:00Z" | NO | Same cut-off as row 5. | Same note as row 5. |
| 7 | 266 (G7) | "re-smoke 1 h, practice 1 h, Row 4 0.5 h, rehearsal 2 h, take 1 h) must end before 18:29Z with margin" | STALE and GAP | (a) "re-smoke 1 h" contradicts line 88, 211 and V3/V9 ("no 1-hour limit"); the v4.2 change list did not cover line 266. (b) The sum omits the 25-minute gate. (c) "with margin" has no number. Arithmetic: 5.5 h without the gate, 5 h 55 min with it; from 07:00Z that is 12:55Z; margin to 17:40Z = 4 h 45 min, margin to 18:29Z = 5 h 34 min. Fits, but only if the re-smoke really takes 1 h. | PROPOSAL: "(re-smoke: estimate stated in the owner's ask, no limit; practice 1 h, Row 4 0.5 h, rehearsal 2 h, start-state gate about 25 min, take 1 h) must end before 18:29Z, and the take must start no later than 17:40Z (23:10 IST) if the lead session confirms the 49 minutes. With a 1 h re-smoke the chain from 07:00Z ends about 12:55Z, a margin of 4 h 45 min to the latest start." |
| 8 | 88 | "no 1-hour limit ... v4.1 estimate was about 1 h, done about 09:30Z (15:00 IST), no longer a limit" | YES only if unbounded re-smoke runs on take day | Unbounded re-smoke on Mon 23 Nov could eat the window. On Tue 17 Nov no conflict (window is 6 days later). | PROPOSAL: add "A re-smoke on Mon 23 Nov must still finish early enough that the take can start by 17:40Z (23:10 IST)." |
| 9 | 211 | "ends: the lead states it in the ask" (re-smoke, no limit) | Same as row 8 | same | same PROPOSAL; also: the ask must state the clock time and whether it still leaves 17:40Z. |
| 10 | 86 | "no later than 04:17 ... done by 08:00Z (13:30 IST); 223 min sequential estimate" | NO | Tue 17 Nov, 6 days before the window. Arithmetic correct. | No change. |
| 11 | 209 | "NO-GO path: re-pin done by Mon 23 Nov 07:00" (line 221) | NO | 07:00Z is 10 h 40 min before 17:40Z. | No change. |
| 12 | 90 | "60 min, to about 07:00Z" | NO | Wed 18 Nov. Correct. | No change. |
| 13 | 91, 92, 93 | Row 4 30 min; rehearsal about 2 h to 09:30Z; gate about 25 min, decision by 10:00Z | NO | All Wed 18 Nov; arithmetic correct. | No change. |
| 14 | 95 | "watch about 20 min; hand-over about 11:20Z" | NO | Not in the 49-minute window (after the take). | No change. |
| 15 | 96, 220, 224 | post Wed 18 Nov 15:00Z (20:30 IST); latest Wed 25 Nov 15:00Z | NO | After the window. | No change. |
| 16 | 226 | "a same-day retake for the 15:00Z post is NOT possible unless the watch finishes by 11:15Z" | NO for the Wed take | Arithmetic correct. Note: a retake is a second 49-minute worst case; the sentence says nothing about the 17:40Z latest start. | PROPOSAL: append "A retake on Mon 23 Nov must also start by 17:40Z (23:10 IST). A first run must start by 16:51Z for a retake to start by 17:40Z." Check: 17:40 - 49 min = 16:51Z; this ignores the watch (20 min) and the gate (25 min) that the runbook puts between two runs, so the real first-run deadline is earlier (the last-start rows of its arithmetic table give 16:06Z). Both depend on the 49. |
| 17 | 156 | "up to 45 s + 5 s + 3 s (53 s worst case)" | NO | 53 s is tiny against 49 min; sum correct. But if the take needs several stops (W-03 step 4, after take), 53 s each, add to the total; I cannot count the stops outside my range. | No change; lead counts stops in the 49-minute build-up. |
| 18 | 126 | "retried every 0.1 s for up to 3 s" | NO | Part of the 53 s. | No change. |
| 19 | 127 (5) | "SIGTERM, then up to 45 s ... SIGKILL ... up to 5 s, then the 3 s final probe ... the lead re-measures at W-03 step 4" | NO | Consistent with row 17. | No change. |
| 20 | 76 | "Every minute figure is the lead's own estimate ... never a measurement. Where a number is not in a source it says 'lead sets at re-pin'." | NO | Honest label. But the 49 must be added to the list of lead-set figures. | PROPOSAL: add "The 49-minute worst case and the 17:40Z latest start are the lead session's order of 2026-11-16 (ORDERS.md line 183), not a measurement." |
| 21 | 109 | "`<WAIT_S>`, `<TRIES>`, `<LIMIT_S>` ... the time box and tripwire threshold of 8A" | GAP | These are all times the 49 minutes depends on, listed as not yet set. | PROPOSAL: add "the 49-minute worst-case figure and the 17:40Z latest start" to the NOT DONE list until confirmed. |
| 22 | 193 | "`<WAIT_S>`, `<TRIES>` ... scene 4 limit (default 180 s)" | NO (small) | 180 s = 3 min, inside any budget. | No change. |
| 23 | 210 | "Tue script block ... time box: lead sets at re-pin (no figure in any source)" | NO | Tuesday. | No change; still an open number. |
| 24 | 213 | "practice run (1 h) with F-002 test T19 to T21 at its end" | NO | Wed 18 Nov. | No change. |
| 25 | 215 | "F-002 deadline \| Wed 07:30" and G4 (line 263) | NO | Correct in IST (13:00). | No change. |
| 26 | 217 | "about 25 min, then the decision" | NO | Wed. | No change. |
| 27 | 242 to 250 (section 4) | Max posts per phase, "Total ... 11 with form (a), 12 with form (b)" | NO for time | These are counts, not times. Sum check: 1 + 1 + 3 + 4 + 2 = 11 (form a); with form b the take row is 3 not 2 so 1 + 1 + 3 + 4 + 3 = 12 (correct). But the sum leaves out T21's one lead (rows: T19 1, T21 1, Row 4 3, rehearsal 4, take 2 = 11); T20 is 0 and the positive control is 0. | No change for timing. |
| 28 | 250 | "13 (A twice, B ten times at once, C once)" | NO | 2 + 10 + 1 = 13 (correct). | No change. |
| 29 | 262 (G3) and 261 (G2) | "deadline Tue 14:00Z; outside the 223-minute clock" | NO | Tue. | No change. |
| 30 | 280 (PSG step 2) etc. | No time. | NO | | |

Rows 27 to 30 are listed so no time statement in the range is silently skipped. Items without a time (sections 1, 2 conventions, variable table lines 166-200, HS-1 to HS-16 lines 291-307) hold no duration or deadline; the only time-like words are "Tue", "Wed" and "before the 14:00Z GO" which refer to days far from Mon 23 Nov.

## Other time words in range, checked

- Line 39-38 (CHANGES): "Round 33 pending" and "re-pin" are not times.
- Line 76: "Times: UTC first, then IST (IST = UTC + 5 h 30 min)": correct.
- Line 161 (not a timing sentence): "run once alone" is advice, no time.
- Line 163 PORT-FREE: no time.
- Line 236: "T20 rule: stop at the FIRST response that is not 422" no time.
- Line 289-311 (hard stops): no time except HS-12 (no time).

## Sentences that must change (summary for the lead)

Must change (conflict with the 49-minute window, or contradict a v4.2 sentence):
1. Line 266 (G7): "re-smoke 1 h" is stale against "no 1-hour limit"; gate omitted from the sum; "margin" has no number. (row 7)
2. Lines 94 and 218: take "about 1 h" is 11 minutes longer than 49 minutes; either the take row or the 49 must say what it contains. (row 4)
3. Lines 107, 223, 236: state 18:29Z but never the latest start 17:40Z (23:10 IST); add it. (rows 1 to 3)
4. Lines 88 and 211: unbounded re-smoke; add that on Mon 23 Nov it must leave room for 17:40Z. (rows 8, 9)
5. Line 222 / 265: two cut-offs (12:00Z slipped take, 17:40Z latest start); say which governs. (rows 5, 6)
6. Line 226: retake arithmetic has no latest start. (row 16)
7. Lines 76 and 109: label the 49 and 17:40Z as lead's order, add to the NOT DONE list. (rows 20, 21)

Fine as written: lines 86, 90-96 (all Wed times, arithmetic checked), 156 (53 s), 209, 213-221, 224-225, 242-250.

## Open questions for the lead (needed before the PROPOSALs are final)

1. What do the 49 minutes contain: the take run program only, or the gate (about 25 min) plus take plus the stop, or the whole run on Mon 23 Nov including a possible failed-run clean-up?
2. Does the 12:00Z cut-off for a slipped take (lines 222, 265) stay, now that the hard latest start is 17:40Z?
3. Is "about 1 h" for the take a planning figure and 49 min the measured worst case, or the reverse? If 49 is the true worst case, the 1 h figure on lines 94, 218, 266, 225-226 (retake arithmetic uses 60) would shrink to 49 and the retake total 225 would become 25 + 49 + 120 + 20 = 214 min (gate must start by 11:26Z for a 15:00Z post, 15:00 - 214 min = 11:26Z). That is a PROPOSAL only; I did not change anything.

## Files

Written: `/home/user/hadavin-sdk/handover/system-map/work/timing-check-v42-part1.md`. No other file changed. No process started. R-numbers: none looked up (no bible in this checkout); EGM skipped: read-and-list step, as the brief says.
