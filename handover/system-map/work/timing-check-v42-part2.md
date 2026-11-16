Status: DRAFT, unverified

# Timing check H2, part 2: take-day runbook v4.2, lines 321-628, against the 49-minute worst-case window

Written 2026-11-16 (UTC). Static read only. Nothing was run, no sub-agent, no spend. Times in UTC and IST (IST = UTC + 5:30). All wording marked PROPOSAL is a suggestion for the lead, not a decision.

File read: `handover/system-map/inputs/lead-reviews/LEAD-RUNBOOK-TAKE-DAY-v4.2.md` lines 202-227 (section 3), 258-270 (G1 to G11, for G7), 314-321 (T-01), and 321-628 (my range). Also read `work/timing-check-a.md` (the v5 owner-sheet findings).

## What I could not check (read first)

1. What the 49 minutes are made of. v4.2 contains no "49" in a timing sense (my search for "49" found only table-of-changes rows, not a duration). The only source is the lead's order at `ORDERS.md` line 183 ("latest start about 17:40Z for window end 18:29Z"). I assume 49 minutes means: the slowest case of the take program's spending run, from its start to its last spend or last deletion. If it also includes the owner's watch, the clean-up, or a restart, the findings in rows R-30 to R-34 change.
2. Where the take program (`scripts/run_real_check_n8n.py`) takes its window figure. Not in this checkout. The runbook range does not state the number (v5 says 14 minutes; v4.2 says only "window too close", line 450). So I cannot show that the program's own refusal rule uses 49.
3. None of the step durations (T-02 to T-11, W-01 to W-05) were measured. They are the lead's estimates (line 407: "Estimates are the lead's own").
4. Whether the Wednesday blocks (60 / 30 / 120 / 25 / 60 minutes) hold in real use. The runbook says the rehearsal measures them; it has not run.
5. Whether n8n starts inside the 12 x 10 s readiness loop on this laptop, and what the real stop time is.
6. Lines outside 321-628 (section 4 spend, sections 6 to 8) were not read except G1 to G11 and T-01.

## Window arithmetic (shown)

| Item | Calculation | Result |
|---|---|---|
| Latest start, 49-minute worst case | 18:29Z minus 49 min | 17:40Z = 23:10 IST (17:40 + 5:30 = 23:10, checked) |
| Window end in IST | 18:29Z + 5:30 | 23:59 IST (checked) |
| Mon 23 Nov 12:00Z slipped-take limit (line 222, 482, 526) versus latest start | 17:40 minus 12:00 | 5 h 40 min = 340 min of extra room that the 12:00Z limit gives away |
| Margin of a take that starts at the 12:00Z limit | 18:29 minus (12:00 + 49 min = 12:49) | 5 h 40 min |
| Re-pin event, Tue (line 325, 407) | 3 + 5 + 2 + 15 + 10 + 15 + 3 + 40 + 65 + 45 + 20 | 223 min (checked: 3, 8, 10, 25, 35, 50, 53, 93, 158, 203, 223) |
| Start for Tue 08:00Z | 08:00 minus 223 min (3 h 43 min) | 04:17Z = 09:47 IST (checked) |
| Start for Mon 23 Nov 07:00Z | 07:00 minus 223 min | 03:17Z = 08:47 IST (checked) |
| Repeat of T-06 to T-10, line 348, 454, 524 | 15 + 3 + 40 + 65 + 45 | 168 min (checked: 18, 58, 123, 168). Note: T-07 (3 min) runs in parallel with T-08 (line 355, 361), so on the critical path it is 165 min; 168 is a safe upper bound. T-11 (20 min) is also parallel (line 402), so the whole event on the critical path is 223 - 3 - 20 = 200 min if both overlaps hold. The runbook keeps 223 as the one-after-another sum (line 209). |
| Latest start of a 168-minute repeat to finish by Mon 07:00Z | 07:00 minus 168 min (2 h 48 min) | 04:12Z = 09:42 IST. Line 524 states only the 223-minute start (03:17Z); it does not state the 168-minute start. |
| G7 chain (line 265) | re-smoke 1 h + practice 1 h + Row 4 0.5 h + rehearsal 2 h + take 1 h = 5.5 h = 330 min; from 07:00Z | ends 12:30Z = 18:00 IST. The chain leaves out the start-state gate (25 min, W-04, line 478) and the lead's watch (20 min). With the gate: take starts 11:55Z, ends 12:55Z; with the watch: 13:15Z. Margin to 18:29Z from 13:15Z: 5 h 14 min. |
| Take slot versus worst case | W-05 slot 10:00 to 11:00Z = 60 min (line 484) versus 49 min | 11 min of slack inside the slot, if 49 is the take program's run only |
| Same-day retake (line 226, 508, 528) | gate 25 + take 60 + edit 120 + watch 20 = 225 min; 15:00Z minus 225 min (3 h 45 min) | 11:15Z = 16:45 IST (checked) |
| First take ends, watch ends | 10:00 + 60 = 11:00Z; + 20 = 11:20Z | 11:20Z is 5 min after 11:15Z, so the same-day retake for a 15:00Z post fails by 5 min (matches line 226) |
| Same, with a 49-minute take | 10:00 + 49 = 10:49Z; + 20 = 11:09Z | 11:09Z is 6 min before 11:15Z, so a same-day retake would then fit (only if the gate for the retake starts at once) |
| Owner edit after hand-over | 11:20Z + 120 min | 13:20Z; post 15:00Z leaves 100 min (checked) |
| Scene 4 stop, worst case (line 473) | 45 s + 5 s + 3 s | 53 s (checked) |
| Scene 4 limit, `<LIMIT_S>` (line 473) | 180 s = 3 min (matches G6 rule 2 "3 minutes") | OK as a number |
| Scene 4 total worst case from the lines given | stop 53 s + readiness loop up to 12 x 10 s = 120 s + lease 45 s + check 30 s | 248 s = 4 min 8 s, which is more than 180 s. Caveat: the lease may already be running during the stop, so the real figure can be lower. Not measured; the rehearsal measures it (line 473). |
| Last possible start of a retake if the first take ran Mon 23 Nov | first start t; second start = t + 49 (run) + 20 (watch) + 25 (gate) = t + 94 min must be <= 17:40Z | t <= 16:06Z (= 21:36 IST). With a 60-minute slot: t + 105 <= 17:40Z, t <= 15:55Z (= 21:25 IST). |

## Rows: every sentence in lines 321-628 that states or implies a time

Column "Conflict" = does it conflict with the 49-minute worst-case window (latest start 17:40Z, window end 18:29Z). YES / NO / GAP (no time given where one is needed) / UNCLEAR. Proposals are labelled PROPOSAL.

### Part A. Re-pin event, Tue 17 Nov (lines 321-420)

| Row | Line | Quoted text | Conflict | Why | PROPOSAL |
|---|---|---|---|---|---|
| R-01 | 322 | "T-02 Final head ... (about 5 min)" | NO | Tue work, before the window (window is Mon 23 Nov only) | none |
| R-02 | 325 | "Latest start for the sequential event is 04:17Z; a later start means the 08:00Z target is missed" | NO | 04:17Z is checked (above). Unrelated to 17:40Z. | none |
| R-03 | 327 | "T-03 ... (about 2 min)" | NO | no window link | none |
| R-04 | 330, 337, 345 | "T-04 ... (about 15 min)", "T-05 ... (about 10 min)", "T-06 ... (about 15 min)" | NO | Tue; counted in the 223 sum | none |
| R-05 | 348 | "a new sha and a repeat through T-10 (about 168 min)" | NO for the window; arithmetic OK (168 = 15 + 3 + 40 + 65 + 45) | but the sum counts T-07 in series while line 361 says T-07 runs parallel with T-08 | PROPOSAL: "about 168 min one after another (about 165 min with T-07 beside T-08)". |
| R-06 | 355 | "T-07 ... (about 3 min; runs in parallel with T-08)" | NO | same as R-05 | none |
| R-07 | 360 | "T-08 Own n8n, database and values file (about 40 min)" | NO | lead re-adds step 0, stored-active check, guard proof at re-pin (line 407); so 40 is probably low | PROPOSAL: leave the figure, add "lead re-adds at re-pin" is already written; no change |
| R-08 | 377 | readiness loop "i -lt 12 ... sleep 10" | NO | 12 x 10 s = 120 s worst case; counted nowhere in the 40 min; part of the Wed restart too (R-18) | PROPOSAL: add "(at most 120 s)" after "within 12 tries". |
| R-09 | 383 | "`timeout 15` ... Exit 124" | NO | bounded, 15 s | none |
| R-10 | 385 | "T-09 ... (about 65 min, the v3 two-fill estimate; one fill is less)" | NO | Tue only; stated as an upper bound | none |
| R-11 | 395 | "T-10 ... (about 45 min)" | NO | Tue | none |
| R-12 | 400 | "not needed until Wednesday" | NO | Wed 18 Nov, not the window | none |
| R-13 | 402 | "T-11 ... (about 20 min, may run parallel to T-09 and T-10)" | NO | parallel, so the sum 223 is an upper bound | none |
| R-14 | 407 | "= 223 min. Estimates are the lead's own" | NO | arithmetic checked; stands | none |
| R-15 | 409-411 | "T-12 ... (no 1-hour limit; starts after 08:00Z and ONLY after the owner's yes)" | NO | Tue; no end time by design. Not in the window. Note it is not inside the 223 min and has no end, so 06:00Z Wed to 14:00Z Tue chain has no computed margin | PROPOSAL: in the ask, the lead states an end time; also state "must end before the Tue 14:00Z GO (6 h after 08:00Z at most)". 14:00 minus 08:00 = 360 min; this bound is not in the file. |
| R-16 | 423, 427-436 | 8A "needed Tue ... before Tue 14:00Z"; "needed Wed ... about 06:00Z / 07:00Z"; "lead sets at re-pin" | GAP (not a conflict) | tripwire thresholds and check time are blank (line 437). Window-neutral. | none from this check |

### Part B. Wednesday 18 Nov (lines 439-500)

| Row | Line | Quoted text | Conflict | Why | PROPOSAL |
|---|---|---|---|---|---|
| R-17 | 443 | "W-00 ... (about 06:00Z) ... inside the practice hour" | NO (Wed) | W-00 shares the 60 minutes of W-01 with T19 to T21 and the restart; 120 s readiness + at least WAIT_S for the positive control (defaults 150 + 20 = 170 s, line 566) are not added anywhere | PROPOSAL: lead adds, at rehearsal, "W-00 + W-01 together: restart up to 2 min, positive control wait about 3 min (170 s)", so the 60 minutes can be checked. |
| R-18 | 448 | "W-01 ... (06:00 to 07:00Z, 11:30 to 12:30 IST, 60 min)" | NO | IST checked (06:00 + 5:30 = 11:30) | none |
| R-19 | 451 | "inside the test's own fixed 10 s bound" | NO | belongs to T19 only (text says so) | none |
| R-20 | 452 | "at most 12 tries, 5 s apart" | NO | 60 s worst case | none |
| R-21 | 454 | "new sha, T-06 to T-10 again (about 168 min): NO-GO that day (G5)" | NO | same 168 figure; the line also says NO-GO that day, so Wed is lost | PROPOSAL: add "the next try is Thu at the same times"; line 525 already says so. |
| R-22 | 454 | "F-002 open at 07:30Z: NO-GO that day (G4)" | NO | W-02 ends at 07:30Z; W-01 ends 07:00Z; consistent | none |
| R-23 | 457 | "W-02 Row 4 ... (07:00 to 07:30Z, 12:30 to 13:00 IST, 30 min)" | NO | IST checked; 30 min contains: PSG, 1 post, mailbox wait about 170 s, four checks. Not measured | none |
| R-24 | 465 | "up to 3 sends" | NO | retry count; each retry uses more time inside the 30 min; no time per retry given | PROPOSAL: "a failed first try takes about N minutes (measured at Row 4); if less than N minutes remain before 07:30Z, the rehearsal does not start" (N lead sets). |
| R-25 | 469 | "W-03 Rehearsal (07:30 to 09:30Z, 13:00 to 15:00 IST, about 2 h)" | NO | IST checked | none |
| R-26 | 473 | "'about 75 s' is not valid after r31: the stop waits up to 45 s, then up to 5 s after SIGKILL, then the 3 s probe (53 s worst case ...)" | NO for the window; arithmetic OK (53 s) | but the 53 s is stop only; start (readiness up to 120 s) is extra, giving up to 248 s against `<LIMIT_S>` 180 s (table above) | PROPOSAL: add after "53 s worst case": "the restart's readiness wait adds up to 120 s (12 tries of 10 s); the total of stop, start and takeover is measured here, not assumed; if the total is over 180 s, scene 4 is cut (G6 rule 2)". |
| R-27 | 473-474 | "`<LIMIT_S>` = 180 s unless the rehearsal shows otherwise" | NO | OK, but it is also the figure behind the 49-minute worst case if scene 4 is in the take | PROPOSAL: lead writes the measured scene-4 worst case into `<TAKE_NOTES>` so the 49 minutes can be rebuilt (see Open question). |
| R-28 | 475 | "Rehearsal 2 ... new start-state gate" | NO | adds a gate (about 25 min?) inside the 2 h; no time given | PROPOSAL: "the new gate takes about the same as W-04 (about 25 min)" if the lead agrees. |
| R-29 | 478 | "W-04 ... (09:30 to 10:00Z, 15:00 to 15:30 IST; gate about 25 min)" | UNCLEAR | slot is 30 min; the gate alone is 25 min; the sign-off and the GO check are extra, but line 217 (section 3) says the gate, sign-off and GO check together are "about 25 min". Two readings of the same 25 minutes. Retake arithmetic (225 min) uses 25 for the gate. | PROPOSAL: "W-04 takes 30 min (09:30 to 10:00Z): gate checks about N min, sign-off and GO check about M min, N + M = 30 (lead sets)". Use one reading everywhere (section 3 line 217, 478, 528). |
| R-30 | 482 | "the take slips (until Mon 23 Nov 12:00Z)" | YES (loosely) | The hard window allows a start until 17:40Z. 12:00Z is a planning limit and is 5 h 40 min earlier. Not an error, but the sentence reads as a hard limit and gives away the window's room. It also does not match G7: the G7 chain ends 12:30Z (above), after 12:00Z. | PROPOSAL: "the take slips one day at the same times, as long as the take program can start before Mon 23 Nov 12:00Z (the lead's planning limit; the hard limit is a start before 17:40Z = 23:10 IST, because the slowest run takes 49 minutes). The owner decides whether to move the planning limit." The owner decides. |
| R-31 | 484 | "W-05 THE TAKE (about 10:00 to 11:00Z, 15:30 to 16:30 IST, about 1 h)" | NO (60 > 49, slot is larger than the worst case) | if 49 is the run only, there are 11 min spare | PROPOSAL: "about 1 h slot (the slowest run takes 49 minutes)". |
| R-32 | 488 | "CUT scene 4 if no takeover shows within `<LIMIT_S>`" | NO | bounded by LIMIT_S | none |
| R-33 | 489 | "the intake mailbox count after `<WAIT_S>` and once more after the stated wait" | GAP | two waits, each at least `MAIL_WAIT_SECONDS` 150 s + `MAIL_SETTLE_SECONDS` 20 s = 170 s (U-16, line 566): at least 340 s = 5 min 40 s inside the take. No time stated in W-05. | PROPOSAL: "the counts proof takes at least two waits of `<WAIT_S>` (defaults 170 s each, about 6 min together); this is inside the 49 minutes". |
| R-34 | 493-494 | "Ctrl-C ... inert for up to 120 s ... A further signal after 120 s ends a hung clean-up" | YES in the worst case, unless counted | 120 s is a possible extra at the end of the take; it must be inside the 49 minutes. 120 s = 2 min. | PROPOSAL: "(up to 120 s; counted in the 49-minute worst case)". Needs the lead to confirm the 49 contains it. |
| R-35 | 497 | "Until then the window is checked only before the prompts, so a slow answer can run past it." (ROUND 28 PENDING) | YES | A slow answer (the owner typing `y`, the challenge and `end`) can push a take that starts at 17:40Z past 18:29Z. The check before the prompts would pass at 17:40Z and the run would then end after 18:29Z. | PROPOSAL: keep the sentence, and add: "Until r28 lands the latest start is earlier than 17:40Z by the time the owner needs to answer (the lead states the figure; PROPOSED margin 10 minutes, so 17:30Z = 23:00 IST; not measured)." |
| R-36 | 450 | "refusal (... window too close ...) 2" | GAP | no figure; the program's refusal threshold is not in this file | PROPOSAL: add "(the program refuses a start that leaves less than 49 minutes before the stop time; the lead reads the settings value at re-pin and writes it in `<TAKE_NOTES>`)". Only if the program really uses 49; see "could not check" 2. |
| R-37 | 500 | "DEACT immediately after the counts proof" | NO | no time | none |

### Part C. After the take (lines 502-518)

| Row | Line | Quoted text | Conflict | Why | PROPOSAL |
|---|---|---|---|---|---|
| R-38 | 504 | "A retake after revocation is impossible" | NO | order rule | none |
| R-39 | 508 | "the same day for a 15:00Z post only if this watch finished by 11:15Z (section 3)" | NO; arithmetic OK (225 min) | but with the W-05 slot (take ends 11:00Z, watch to 11:20Z) the condition fails by 5 min, so the sentence is true but effectively never met; with a 49-minute take it can be met (watch ends 11:09Z) | PROPOSAL: "the take ends at 11:00Z at the latest, the watch ends at 11:20Z, 5 min after 11:15Z; a same-day retake works only if the take ended by 10:55Z." (10:55 + 20 = 11:15, checked) |
| R-40 | 508 | "the model key and passwords still valid and the ceiling re-checked" | NO | no time | none |
| R-41 | 509 | "about 11:20Z" hand-over | NO | 11:00 + 20 = 11:20, IST 16:50 (checked) | none |
| R-42 | 510, 514 | "ONE owner clean-up, only after the lead writes 'no retake, clean-up starts'" ... "the owner does S9-2 and S9-3 'the same day'" | YES if the take is on Mon 23 Nov late | A take starting 17:40Z ends 18:29Z = 23:59 IST; the watch takes until 18:49Z = 00:19 IST (Tue 24 Nov in IST). "The same day" is then impossible in IST, and the owner's clean-up and revocation fall after midnight. For the Wed 18 Nov take the problem does not arise (11:20Z). | PROPOSAL: "If the take runs after about 16:00Z on Mon 23 Nov (21:30 IST), the clean-up and revocation are done the next morning; the lead states the time in UTC and IST in the clean-up message (U-19). The model key must stay valid until then (the program's spend stop at 18:29Z, not the key, stops spending)." Owner decision. |
| R-43 | 515 | "STOP-N8N ... docker rm" | NO | no time | none |
| R-44 | 517 | "edits the video (about 120 min) and posts on LinkedIn Wed 18 Nov 15:00Z (20:30 IST), or at the latest Wed 25 Nov 15:00Z (20:30 IST)" | NO | arithmetic checked (15:00 + 5:30 = 20:30). Take on Mon 23 Nov 17:40 to 18:29Z + watch 20 = 18:49Z; edit 120 = 20:49Z (02:19 IST Tue); post Wed 25 15:00Z leaves 42 h 11 min. Fits. | none |
| R-45 | 506-507 | step 1 "Copy out first", step 2 | NO | no time | none |

### Part D. Quick routing, section 11 (lines 520-530)

| Row | Line | Quoted text | Conflict | Why | PROPOSAL |
|---|---|---|---|---|---|
| R-46 | 524 | "take later, before Mon 23 Nov 18:29Z; re-pin done by Mon 23 Nov 07:00Z (G7). One repeat of T-06 to T-10 takes about 168 min (15 + 3 + 40 + 65 + 45); the re-pin event of 223 min must start by Mon 23 Nov 03:17Z to be done by 07:00Z." | YES | "before 18:29Z" is the end of the window. With a 49-minute worst case the take PROGRAM must START before 17:40Z (23:10 IST), not "be taken before 18:29Z". Arithmetic: 168 and 223 and 03:17Z are correct. The sentence omits the start time of a 168-minute repeat (04:12Z, above). | PROPOSAL: "take later; the take program must start before Mon 23 Nov 17:40Z (23:10 IST) so its slowest run (49 minutes) ends before 18:29Z (23:59 IST); the lead's planning limit for a take is 12:00Z. Re-pin done by Mon 23 Nov 07:00Z (G7). One repeat of T-06 to T-10 takes about 168 min (15 + 3 + 40 + 65 + 45) and must start by 04:12Z (09:42 IST); the whole re-pin event of 223 min must start by 03:17Z (08:47 IST)." |
| R-47 | 525 | "Wed 07:30Z F-002 open ... try again the next day at the same times" | NO | no window link until the slip count runs out on Mon 23 | none |
| R-48 | 526 | "Take counts not green: slip one day at the same times, until Mon 23 Nov 12:00Z" | YES (loosely) | same as R-30 | PROPOSAL: same wording as R-30. |
| R-49 | 528 | "gate 25 + take 60 + edit 120 + watch 20 = 225 min; a 15:00Z post needs the gate to start by 11:15Z" | NO; arithmetic OK | with a 49-minute take, 214 min (25 + 49 + 120 + 20 = 214) and gate start by 11:26Z (15:00 minus 3 h 34 min; checked). The 60 is a slot, 49 is the worst case; the text does not say which. | PROPOSAL: "(take slot 60; if the real take is 49 minutes, 214 min and gate start by 11:26Z)". |
| R-50 | 527 | "scene 4 cut; take goes ahead (G6 rule 2)" | NO | same 3 min | none |
| R-51 | 529-530 | "Second start not refused ... Stored-active flow ... DEACT at once" | NO | no time | none |

### Part E. Other time statements in lines 532-628

| Row | Line | Quoted text | Conflict | Why | PROPOSAL |
|---|---|---|---|---|---|
| R-52 | 541 | "The cloud RUNBOOK.md uses a 3.5 to 4.5 h re-smoke ... made it about 1 hour; SUPERSEDED" | NO | stale figures, already listed as superseded | none |
| R-53 | 542 | "Several time stamps in ORDERS blocks (13:00Z to 15:00Z) are wrong" | NO | fine; the 49-minute and 17:40Z figures come from ORDERS.md line 183 and should be checked by the lead against the same correction | PROPOSAL: lead confirms 17:40Z after reading Q30. |
| R-54 | 566 | "`MAIL_WAIT_SECONDS=150.0`, `MAIL_SETTLE_SECONDS=20.0`, `WAIT_STEP_SECONDS=60.0`" | NO | inputs to R-33 | none |
| R-55 | 570 | "U-20 CLOSED: Mon 23 Nov 07:00Z reading is 're-pin done by 07:00Z'" | NO | consistent with R-46 | none |
| R-56 | 583 | "Also not checked by this document: ..." | GAP | does not say the 49-minute figure is a planning figure | PROPOSAL: add "the 49-minute worst case of the take run and its parts (not measured; rehearsal measures it)". |
| R-57 | 593 | O4: "about Wed 11:20Z / 16:50 IST or later (time U-19)" | NO | 11:20 + 5:30 = 16:50 (checked) | none |
| R-58 | 592 | O3: "the take, about Wed 10:00Z / 15:30 IST" | NO | checked | none |
| R-59 | 594 | O5: "after the watch, about Wed 11:20Z" | NO | same | none |
| R-60 | 595-596 | O6 "same day", O7 "same day, time set by the lead (U-19)" | YES (late Mon take only) | same as R-42 | PROPOSAL: same as R-42. |
| R-61 | 597 | O8: "Wed 18 Nov 15:00Z / 20:30 IST (latest Wed 25 Nov 15:00Z / 20:30 IST)" | NO | checked | none |
| R-62 | 601-628 (section 15) | map rows | NO | no time statements beyond those above (m7, "before W-01") | none |

## G7 and the stop time (asked for, shown)

- Stop time near line 223: "Credits / money stop | Mon 23 Nov 18:29 | 23:59". 18:29 + 5:30 = 23:59 (checked). The row says when the money stops. It does not say when the last take program start is. PROPOSAL (section 3, one new row, outside my range): "Latest start of the take program | Mon 23 Nov 17:40 | 23:10 | 18:29 minus the slowest run of 49 minutes (lead's order, ORDERS.md line 183)".
- G7 (line 265): "re-pin done by Mon 23 Nov 07:00Z (12:30 IST); the chain after it (re-smoke 1 h, practice 1 h, Row 4 0.5 h, rehearsal 2 h, take 1 h) must end before 18:29Z with margin." Arithmetic: 5.5 h = 330 min from 07:00Z ends 12:30Z; adding the gate (25) and watch (20) ends 13:15Z; margin to 18:29Z is 5 h 14 min. Conflict with the 49-minute window: NO for the chain (it ends far before 17:40Z). Two defects: (1) "re-smoke 1 h" is the superseded figure (v4.1 NOTE 14:35Z; the re-smoke has no limit since 2026-11-16, line 211, 411); (2) the chain's end, 12:30Z, is after the 12:00Z slipped-take limit of line 222 and 526, so on this path the take could not be the one allowed "until 12:00Z" unless the limit means "start". PROPOSAL: "...the chain after it (re-smoke: as long as the owner agreed, practice 1 h, Row 4 0.5 h, rehearsal 2 h, gate 25 min, take 1 h) must have its take PROGRAM start before 17:40Z (23:10 IST) with margin." If the re-smoke is 1 h, the take program would start at 11:55Z.

## Which timing sentences must change (short list)

Must change (conflict YES): R-46 (line 524), R-48 (line 526), R-30 (line 482), R-35 (line 497, after r28 only), R-34 (lines 493-494, only if the 49 minutes include the extra 120 s), R-42 and R-60 (lines 510, 514, 595-596: "same day" for a late Monday take), plus G7 (line 265) and the section 3 stop-time row (line 223), both outside my range.

Should change (gap or unclear): R-26 (line 473, scene 4 worst case 248 s against 180 s), R-29 (line 478, one 25-minute figure read two ways), R-33 (line 489, two mailbox waits not counted), R-36 (line 450, no number), R-49 (line 528, 60 versus 49), R-39 (line 508, 5-minute miss), R-56 (line 583).

No change needed: everything in Part A except small tidy proposals R-05, R-08; R-18 to R-25, R-31 to R-32, R-38, R-41, R-43 to R-45, R-47, R-50 to R-55, R-57 to R-59, R-61, R-62.

## Open question for the lead (needed before the PROPOSAL wording is final)

What are the 49 minutes made of? In particular: do they include the owner's typing of `y`, the challenge and `end`; the scene 4 stop and restart (up to 248 s by the lines of this runbook); the two mailbox waits (at least 340 s); the film pause; the 120 s Ctrl-C wait; the post-take counts; and the program's own clean-up? And is the program's refusal rule set to 49 in `stage.env`? Without this, R-34, R-35, R-36 and the "49" in R-31 and R-49 stay proposals.
