Status: DRAFT. Unverified: (a) what the 49 minutes contain and whether the 17:40Z latest start is right (source: ORDERS.md line 183, unverified); (b) every step duration in the runbook (lead session estimates, not measurements); (c) the take program's own refusal rule; (d) runbook lines outside 321-628 except those named below. Checked only: the arithmetic on this page, by hand. Nothing was run.

# Timing check H2, part 2: take-day runbook v4.2, lines 321-628, against the 49-minute worst-case window

Written 2026-11-16 (UTC). Static read only. Nothing was run, no sub-agent, no spend. Times in UTC (Z) and IST (IST = UTC + 5:30). All wording marked PROPOSAL is a suggestion for the lead session, not a decision.

## In plain words

This page checks every time statement in lines 321 to 628 of the take-day runbook, version 4.2 (the written plan for the day of the filmed demo run). It asks one question: does each statement fit a worst-case run of 49 minutes that must end before the money stop at 18:29Z?

**49 minutes: source ORDERS.md line 183, unverified.** The lead session ordered a check against "latest start about 17:40Z for window end 18:29Z". Nobody has written down what the 49 minutes contain. Rows that depend on the 49 (they stay proposals until the lead session answers): R-30, R-31, R-34, R-35, R-36, R-39, R-42, R-46, R-48, R-49, R-53, R-56, R-60, the "G7 and the stop time" section, and these arithmetic rows: latest start, 12:00Z margin, take slot against worst case, take with 49 minutes, same-day retake with 49 minutes, last possible retake start, late Monday take. Rows that do not depend on it: the rest (they use only runbook figures).

## Words and codes used on this page

Definitions use `work/GLOSSARY.md` wording where it has one.
- **lead session**: the Claude session that gives orders to the system-map session through ORDERS.md. The rows below say "the lead"; read each as "lead session". **studio lead**: the Claude session that does the technical steps and is the only one that messages the owner. **owner**: the human at the laptop who gives the written yes.
- **take**: one recorded (filmed) run of the lead-intake demo on made-up data. **take program**: the script that runs it, `scripts/run_real_check_n8n.py` (named by the runbook; not in this checkout).
- **re-pin**: pointing the demo at a new fixed version of the core code (a version id called a sha). The runbook's re-pin event is one set of steps T-02 to T-12 on Tue 17 Nov. **re-smoke**: a repeat quick test run after the re-pin (my reading; UNVERIFIED).
- **gate** (start-state gate): a check of about 25 minutes before the take, W-04. **Row 4**: the 30-minute Wednesday step W-02 (my reading: the owner posts one test lead and checks the results; UNVERIFIED). **G7**: runbook rule G7 (line 265).
- **Row labels.** R-01 to R-62 are this page's own row numbers, so a row can be cited. The codes T-nn, W-nn, G-n, U-nn and O-n are the runbook's own labels, used here only to point to lines: T-nn = the Tuesday re-pin steps, W-nn = the Wednesday steps (rehearsal, gate, take), G-n = go/no-go rules, O-n = owner steps. What U-nn stands for is not given in the part I read: UNVERIFIED (U-16, U-19, U-20 appear in the rows). "H2" is the label of this check. Also used by the runbook and left as written because their meaning is not in my range: PSG, F-002, T19, DEACT, STOP-N8N, scene 4, WAIT_S, LIMIT_S.
- **EGM**, **bible**, **R-numbers** in the studio's sense: not used on this page.

## What I could not check (read first)

0. File read: `handover/system-map/inputs/lead-reviews/LEAD-RUNBOOK-TAKE-DAY-v4.2.md` lines 202-227 (section 3), 258-270 (G1 to G11, for G7), 314-321 (T-01), and 321-628 (my range). Also read `work/timing-check-a.md` (the v5 owner-sheet findings).
1. What the 49 minutes are made of. v4.2 contains no "49" in a timing sense (my search for "49" found only table-of-changes rows, not a duration). The only source is the lead session's order at `ORDERS.md` line 183 ("latest start about 17:40Z for window end 18:29Z"). I assume 49 minutes means: the slowest case of the take program's spending run, from its start to its last spend or last deletion. If it also includes the owner's watch, the clean-up, or a restart, the findings in rows R-30 to R-34 change.
2. Where the take program takes its window figure. Not in this checkout. The runbook range does not state the number (v5, the owner sheet version 5, says 14 minutes; v4.2 says only "window too close", line 450). So I cannot show that the program's own refusal rule uses 49.
3. None of the step durations (T-02 to T-11, W-01 to W-05) were measured. They are the lead session's estimates (line 407: "Estimates are the lead's own").
4. Whether the Wednesday blocks (60 / 30 / 120 / 25 / 60 minutes) hold in real use. The runbook says the rehearsal measures them; it has not run.
5. Whether n8n (the tool that runs the demo steps) starts inside the 12 x 10 s readiness loop on this laptop, and what the real stop time is.
6. Lines outside 321-628 (section 4 spend, sections 6 to 8) were not read except G1 to G11 and T-01.

## Window arithmetic (shown, one calculation per row)

| Item | Calculation | Result | Note | Depends on 49 |
|---|---|---|---|---|
| Latest start, 49-minute worst case | 18:29Z - 49 min | 17:40Z = 23:10 IST | depends on the 49 | yes |
| Window end in IST | 18:29Z + 5:30 | 23:59 IST | | no |
| Slipped-take limit (lines 222, 482, 526) against latest start | 17:40 - 12:00 | 5 h 40 min | the 12:00Z limit is stricter than the hard latest start by this much; depends on the 49 | yes |
| Margin of a take that starts at 12:00Z | 18:29 - (12:00 + 49 min = 12:49) | 5 h 40 min | depends on the 49 | yes |
| Re-pin event, Tue (lines 325, 407): sum | 3 + 5 + 2 + 15 + 10 + 15 + 3 + 40 + 65 + 45 + 20 | 223 min | running totals 3, 8, 10, 25, 35, 50, 53, 93, 158, 203, 223 all checked | no |
| Start for Tue 08:00Z | 08:00 - 223 min (3 h 43 min) | 04:17Z = 09:47 IST | | no |
| Start for Mon 23 Nov 07:00Z | 07:00 - 223 min | 03:17Z = 08:47 IST | | no |
| Repeat of T-06 to T-10 (lines 348, 454, 524), one after another | 15 + 3 + 40 + 65 + 45 | 168 min | running totals 18, 58, 123, 168 checked | no |
| Same repeat, T-07 beside T-08 | 168 - 3 | 165 min | T-07 (3 min) runs in parallel with T-08 (lines 355, 361) | no |
| Whole re-pin event, T-07 and T-11 in parallel | 223 - 3 - 20 | 200 min | only if both overlaps hold; the runbook keeps 223 (line 209) | no |
| Latest start of a 168-minute repeat, done by Mon 07:00Z | 07:00 - 168 min (2 h 48 min) | 04:12Z = 09:42 IST | line 524 states only the 223-minute start (03:17Z), not this one | no |
| G7 chain (line 265) | re-smoke 60 + practice 60 + Row 4 30 + rehearsal 120 + take 60 = 330 min; 07:00Z + 330 min | ends 12:30Z = 18:00 IST | leaves out the gate and the watch | no |
| G7 chain with the gate | 12:30Z + 25 min | ends 12:55Z (take starts 11:55Z) | gate is W-04, line 478 | no |
| G7 chain with gate and watch | 12:55Z + 20 min | 13:15Z | | no |
| Margin from the G7 chain to the window end | 18:29 - 13:15 | 5 h 14 min | | no |
| Take slot against worst case | W-05 slot 60 min (line 484) - 49 min | 11 min | depends on the 49 | yes |
| Same-day retake total (lines 226, 508, 528) | gate 25 + take 60 + edit 120 + watch 20 | 225 min | | no |
| Latest gate start for a 15:00Z post | 15:00Z - 225 min (3 h 45 min) | 11:15Z = 16:45 IST | | no |
| First take ends | 10:00 + 60 | 11:00Z | | no |
| First watch ends | 11:00 + 20 | 11:20Z | 5 min after 11:15Z, so a same-day retake fails by 5 min (matches line 226) | no |
| Take of 49 minutes, watch end | 10:00 + 49 + 20 | 11:09Z | 6 min before 11:15Z, so a retake would fit if its gate starts at once; depends on the 49 | yes |
| Owner edit after hand-over | 11:20Z + 120 min | 13:20Z | post at 15:00Z leaves 100 min | no |
| Scene 4 stop, worst case (line 473) | 45 s + 5 s + 3 s | 53 s | | no |
| Scene 4 limit `<LIMIT_S>` (line 473) | 180 s | 3 min | matches G6 rule 2 "3 minutes" | no |
| Scene 4 total worst case from the lines given | 53 s stop + 120 s readiness loop (12 x 10 s) + 45 s lease + 30 s check | 248 s = 4 min 8 s | more than 180 s; the lease may already run during the stop, so the real figure can be lower; not measured, the rehearsal measures it (line 473) | no |
| Retake after a Monday take, gap between starts | 49 (run) + 20 (watch) + 25 (gate) | 94 min | depends on the 49 | yes |
| Last start of a first take so the retake starts by 17:40Z | 17:40Z - 94 min | 16:06Z = 21:36 IST | depends on the 49 | yes |
| Same, with a 60-minute slot | 17:40Z - (60 + 20 + 25 = 105 min) | 15:55Z = 21:25 IST | | yes |
| Same-day retake total with a 49-minute take | 25 + 49 + 120 + 20 | 214 min | depends on the 49 | yes |
| Latest gate start for a 15:00Z post, 49-minute take | 15:00Z - 214 min (3 h 34 min) | 11:26Z | depends on the 49 | yes |
| Late Monday take, watch end | 17:40Z + 49 min + 20 min | 18:49Z = 00:19 IST on Tue 24 Nov | depends on the 49 | yes |
| Late Monday take, edit end | 18:49Z + 120 min | 20:49Z (02:19 IST Tue) | | no |
| Late Monday take, time left before the Wed 25 Nov 15:00Z post | Wed 25 Nov 15:00Z - Mon 23 Nov 20:49Z | 42 h 11 min | | no |

## Rows: every sentence in lines 321-628 that states or implies a time

Column "Conflict" = does it conflict with the 49-minute worst-case window (latest start 17:40Z, window end 18:29Z). YES / NO / GAP (no time given where one is needed) / UNCLEAR. Proposals are labelled PROPOSAL.

### Part A. Re-pin event, Tue 17 Nov (lines 321-420)

| Row | Line | Quoted text | Conflict | Depends on 49 | Why | PROPOSAL |
|---|---|---|---|---|---|---|
| R-01 | 322 | "T-02 Final head ... (about 5 min)" | NO | no | Tue work, before the window (window is Mon 23 Nov only) | none |
| R-02 | 325 | "Latest start for the sequential event is 04:17Z; a later start means the 08:00Z target is missed" | NO | yes | 04:17Z is checked (above). Unrelated to 17:40Z. | none |
| R-03 | 327 | "T-03 ... (about 2 min)" | NO | no | no window link | none |
| R-04 | 330, 337, 345 | "T-04 ... (about 15 min)", "T-05 ... (about 10 min)", "T-06 ... (about 15 min)" | NO | no | Tue; counted in the 223 sum | none |
| R-05 | 348 | "a new sha and a repeat through T-10 (about 168 min)" | NO for the window; arithmetic OK (168 = 15 + 3 + 40 + 65 + 45) | no | but the sum counts T-07 in series while line 361 says T-07 runs parallel with T-08 | Which figure the runbook should use: 168 min. It is the one-after-another sum that matches the 223-minute total (line 209), and it is a safe upper bound. PROPOSAL: keep "about 168 min" and add "(165 min with T-07 beside T-08)" as a note, not as the planning figure. |
| R-06 | 355 | "T-07 ... (about 3 min; runs in parallel with T-08)" | NO | no | same as R-05 | none |
| R-07 | 360 | "T-08 Own n8n, database and values file (about 40 min)" | NO | no | lead re-adds step 0, stored-active check, guard proof at re-pin (line 407); so 40 is probably low | No change. |
| R-08 | 377 | readiness loop "i -lt 12 ... sleep 10" | NO | no | 12 x 10 s = 120 s worst case; counted nowhere in the 40 min; part of the Wed restart too (R-18) | PROPOSAL: add "(at most 120 s)" after "within 12 tries". |
| R-09 | 383 | "`timeout 15` ... Exit 124" | NO | no | bounded, 15 s | none |
| R-10 | 385 | "T-09 ... (about 65 min, the v3 two-fill estimate; one fill is less)" | NO | no | Tue only; stated as an upper bound | none |
| R-11 | 395 | "T-10 ... (about 45 min)" | NO | no | Tue | none |
| R-12 | 400 | "not needed until Wednesday" | NO | no | Wed 18 Nov, not the window | none |
| R-13 | 402 | "T-11 ... (about 20 min, may run parallel to T-09 and T-10)" | NO | no | parallel, so the sum 223 is an upper bound | none |
| R-14 | 407 | "= 223 min. Estimates are the lead's own" | NO | no | arithmetic checked; stands | none |
| R-15 | 409-411 | "T-12 ... (no 1-hour limit; starts after 08:00Z and ONLY after the owner's yes)" | NO | no | T-12 is on Tuesday, so it is outside the window. It has no time limit by design and is not part of the 223 minutes, so no end time can be computed for it. | PROPOSAL: in the ask, the lead session states an end time for T-12. The latest possible end is the Tue 14:00Z GO, which is 360 minutes after 08:00Z (14:00 - 08:00); this bound is my own and is not in the runbook. |
| R-16 | 423, 427-436 | 8A "needed Tue ... before Tue 14:00Z"; "needed Wed ... about 06:00Z / 07:00Z"; "lead sets at re-pin" | GAP (not a conflict) | no | tripwire thresholds and check time are blank (line 437). Window-neutral. | none from this check |

### Part B. Wednesday 18 Nov (lines 439-500)

| Row | Line | Quoted text | Conflict | Depends on 49 | Why | PROPOSAL |
|---|---|---|---|---|---|---|
| R-17 | 443 | "W-00 ... (about 06:00Z) ... inside the practice hour" | NO (Wed) | no | W-00 shares the 60 minutes of W-01 with T19 to T21 and the restart; 120 s readiness + at least WAIT_S for the positive control (defaults 150 + 20 = 170 s, line 566) are not added anywhere | PROPOSAL: lead adds, at rehearsal, "W-00 + W-01 together: restart up to 2 min, positive control wait about 3 min (170 s)", so the 60 minutes can be checked. |
| R-18 | 448 | "W-01 ... (06:00 to 07:00Z, 11:30 to 12:30 IST, 60 min)" | NO | no | IST checked (06:00 + 5:30 = 11:30) | none |
| R-19 | 451 | "inside the test's own fixed 10 s bound" | NO | no | belongs to T19 only (text says so) | none |
| R-20 | 452 | "at most 12 tries, 5 s apart" | NO | no | 60 s worst case | none |
| R-21 | 454 | "new sha, T-06 to T-10 again (about 168 min): NO-GO that day (G5)" | NO | no | same 168 figure; the line also says NO-GO that day, so Wed is lost | PROPOSAL: add "the next try is Thu at the same times"; line 525 already says so. |
| R-22 | 454 | "F-002 open at 07:30Z: NO-GO that day (G4)" | NO | no | W-02 ends at 07:30Z; W-01 ends 07:00Z; consistent | none |
| R-23 | 457 | "W-02 Row 4 ... (07:00 to 07:30Z, 12:30 to 13:00 IST, 30 min)" | NO | no | IST checked; 30 min contains: PSG, 1 post, mailbox wait about 170 s, four checks. Not measured | none |
| R-24 | 465 | "up to 3 sends" | NO | no | retry count; each retry uses more time inside the 30 min; no time per retry given | PROPOSAL: "a failed first try takes about N minutes (measured at Row 4); if less than N minutes remain before 07:30Z, the rehearsal does not start" (N lead sets). |
| R-25 | 469 | "W-03 Rehearsal (07:30 to 09:30Z, 13:00 to 15:00 IST, about 2 h)" | NO | no | IST checked | none |
| R-26 | 473 | "'about 75 s' is not valid after r31: the stop waits up to 45 s, then up to 5 s after SIGKILL, then the 3 s probe (53 s worst case ...)" | NO for the window; arithmetic OK (53 s) | no | but the 53 s is stop only; start (readiness up to 120 s) is extra, giving up to 248 s against `<LIMIT_S>` 180 s (table above) | PROPOSAL: add after "53 s worst case": "the restart's readiness wait adds up to 120 s (12 tries of 10 s); the total of stop, start and takeover is measured here, not assumed; if the total is over 180 s, scene 4 is cut (G6 rule 2)". |
| R-27 | 473-474 | "`<LIMIT_S>` = 180 s unless the rehearsal shows otherwise" | NO | yes | OK, but it is also the figure behind the 49-minute worst case if scene 4 is in the take | PROPOSAL: lead writes the measured scene-4 worst case into `<TAKE_NOTES>` so the 49 minutes can be rebuilt (see Open question). |
| R-28 | 475 | "Rehearsal 2 ... new start-state gate" | NO | no | adds a gate (about 25 min?) inside the 2 h; no time given | PROPOSAL: "the new gate takes about the same as W-04 (about 25 min)" if the lead agrees. |
| R-29 | 478 | "W-04 ... (09:30 to 10:00Z, 15:00 to 15:30 IST; gate about 25 min)" | UNCLEAR | no | slot is 30 min; the gate alone is 25 min; the sign-off and the GO check are extra, but line 217 (section 3) says the gate, sign-off and GO check together are "about 25 min". Two readings of the same 25 minutes. Retake arithmetic (225 min) uses 25 for the gate. | PROPOSAL: "W-04 takes 30 min (09:30 to 10:00Z): gate checks about N min, sign-off and GO check about M min, N + M = 30 (lead sets)". Use one reading everywhere (section 3 line 217, 478, 528). |
| R-30 | 482 | "the take slips (until Mon 23 Nov 12:00Z)" | NO | yes | If the 49 is right, the hard latest start is 17:40Z. The 12:00Z limit is a planning limit 5 h 40 min earlier, so it is stricter and does not conflict with the window. The sentence does not say that it limits the start; read as a start limit it agrees with G7 (the take starts 11:55Z, see the arithmetic table). Wording only. | PROPOSAL: "the take slips one day at the same times, as long as the take program can start before Mon 23 Nov 12:00Z (the lead session's planning limit; if the lead session confirms the 49 minutes, the hard limit is a start before 17:40Z = 23:10 IST). The owner decides whether to move the planning limit." |
| R-31 | 484 | "W-05 THE TAKE (about 10:00 to 11:00Z, 15:30 to 16:30 IST, about 1 h)" | NO (60 > 49, slot is larger than the worst case) | yes | if 49 is the run only, there are 11 min spare | PROPOSAL: "about 1 h slot (the slowest run takes 49 minutes)". |
| R-32 | 488 | "CUT scene 4 if no takeover shows within `<LIMIT_S>`" | NO | no | bounded by LIMIT_S | none |
| R-33 | 489 | "the intake mailbox count after `<WAIT_S>` and once more after the stated wait" | GAP | yes | two waits, each at least `MAIL_WAIT_SECONDS` 150 s + `MAIL_SETTLE_SECONDS` 20 s = 170 s (U-16, line 566): at least 340 s = 5 min 40 s inside the take. No time stated in W-05. | PROPOSAL: "the counts proof takes at least two waits of `<WAIT_S>` (defaults 170 s each, about 6 min together); this is inside the 49 minutes". |
| R-34 | 493-494 | "Ctrl-C ... inert for up to 120 s ... A further signal after 120 s ends a hung clean-up" | YES in the worst case, unless counted | yes | 120 s is a possible extra at the end of the take; it must be inside the 49 minutes. 120 s = 2 min. | PROPOSAL: "(up to 120 s; counted in the 49-minute worst case)". Needs the lead to confirm the 49 contains it. |
| R-35 | 497 | "Until then the window is checked only before the prompts, so a slow answer can run past it." (ROUND 28 PENDING) | YES | yes | A slow answer (the owner typing `y`, the challenge and `end`) can push a take that starts at 17:40Z past 18:29Z. The check before the prompts would pass at 17:40Z and the run would then end after 18:29Z. | PROPOSAL: keep the sentence, and add: "Until r28 lands the latest start is earlier than 17:40Z by the time the owner needs to answer (the lead states the figure; PROPOSED margin 10 minutes, so 17:30Z = 23:00 IST; not measured)." |
| R-36 | 450 | "refusal (... window too close ...) 2" | GAP | yes | no figure; the program's refusal threshold is not in this file | PROPOSAL: add "(the program refuses a start that leaves less than 49 minutes before the stop time; the lead reads the settings value at re-pin and writes it in `<TAKE_NOTES>`)". Only if the program really uses 49; see "could not check" 2. |
| R-37 | 500 | "DEACT immediately after the counts proof" | NO | no | no time | none |

### Part C. After the take (lines 502-518)

| Row | Line | Quoted text | Conflict | Depends on 49 | Why | PROPOSAL |
|---|---|---|---|---|---|---|
| R-38 | 504 | "A retake after revocation is impossible" | NO | no | order rule | none |
| R-39 | 508 | "the same day for a 15:00Z post only if this watch finished by 11:15Z (section 3)" | NO; arithmetic OK (225 min) | yes | but with the W-05 slot (take ends 11:00Z, watch to 11:20Z) the condition fails by 5 min, so the sentence is true but effectively never met; with a 49-minute take it can be met (watch ends 11:09Z) | PROPOSAL: "the take ends at 11:00Z at the latest, the watch ends at 11:20Z, 5 min after 11:15Z; a same-day retake works only if the take ended by 10:55Z." (10:55 + 20 = 11:15, checked) |
| R-40 | 508 | "the model key and passwords still valid and the ceiling re-checked" | NO | no | no time | none |
| R-41 | 509 | "about 11:20Z" hand-over | NO | no | 11:00 + 20 = 11:20, IST 16:50 (checked) | none |
| R-42 | 510, 514 | "ONE owner clean-up, only after the lead writes 'no retake, clean-up starts'" ... "the owner does S9-2 and S9-3 'the same day'" | YES if the take is on Mon 23 Nov late | yes | A take starting 17:40Z ends 18:29Z = 23:59 IST; the watch takes until 18:49Z = 00:19 IST (Tue 24 Nov in IST). "The same day" is then impossible in IST, and the owner's clean-up and revocation fall after midnight. For the Wed 18 Nov take the problem does not arise (11:20Z). | PROPOSAL: "If the take runs after about 16:00Z on Mon 23 Nov (21:30 IST), the clean-up and revocation are done the next morning; the lead states the time in UTC and IST in the clean-up message (U-19). The model key must stay valid until then (the program's spend stop at 18:29Z, not the key, stops spending)." Owner decision. |
| R-43 | 515 | "STOP-N8N ... docker rm" | NO | no | no time | none |
| R-44 | 517 | "edits the video (about 120 min) and posts on LinkedIn Wed 18 Nov 15:00Z (20:30 IST), or at the latest Wed 25 Nov 15:00Z (20:30 IST)" | NO | no | 15:00 + 5:30 = 20:30 IST, checked. For a late Monday take the arithmetic table gives 42 h 11 min before the Wed 25 Nov post, so it fits. | none |
| R-45 | 506-507 | step 1 "Copy out first", step 2 | NO | no | no time | none |

### Part D. Quick routing, section 11 (lines 520-530)

| Row | Line | Quoted text | Conflict | Depends on 49 | Why | PROPOSAL |
|---|---|---|---|---|---|---|
| R-46 | 524 | "take later, before Mon 23 Nov 18:29Z; re-pin done by Mon 23 Nov 07:00Z (G7). One repeat of T-06 to T-10 takes about 168 min (15 + 3 + 40 + 65 + 45); the re-pin event of 223 min must start by Mon 23 Nov 03:17Z to be done by 07:00Z." | YES | yes | "before 18:29Z" is the end of the window. With a 49-minute worst case the take PROGRAM must START before 17:40Z (23:10 IST), not "be taken before 18:29Z". Arithmetic: 168 and 223 and 03:17Z are correct. The sentence omits the start time of a 168-minute repeat (04:12Z, above). | PROPOSAL: "take later; the take program must start before Mon 23 Nov 17:40Z (23:10 IST) so its slowest run (49 minutes) ends before 18:29Z (23:59 IST); the lead's planning limit for a take is 12:00Z. Re-pin done by Mon 23 Nov 07:00Z (G7). One repeat of T-06 to T-10 takes about 168 min (15 + 3 + 40 + 65 + 45) and must start by 04:12Z (09:42 IST); the whole re-pin event of 223 min must start by 03:17Z (08:47 IST)." |
| R-47 | 525 | "Wed 07:30Z F-002 open ... try again the next day at the same times" | NO | no | no window link until the slip count runs out on Mon 23 | none |
| R-48 | 526 | "Take counts not green: slip one day at the same times, until Mon 23 Nov 12:00Z" | NO | no | same as R-30 (wording only) | PROPOSAL: same wording as R-30. |
| R-49 | 528 | "gate 25 + take 60 + edit 120 + watch 20 = 225 min; a 15:00Z post needs the gate to start by 11:15Z" | NO; arithmetic OK | yes | with a 49-minute take, 214 min (25 + 49 + 120 + 20 = 214) and gate start by 11:26Z (15:00 minus 3 h 34 min; checked). The 60 is a slot, 49 is the worst case; the text does not say which. | PROPOSAL: "(take slot 60; if the real take is 49 minutes, 214 min and gate start by 11:26Z)". |
| R-50 | 527 | "scene 4 cut; take goes ahead (G6 rule 2)" | NO | no | same 3 min | none |
| R-51 | 529-530 | "Second start not refused ... Stored-active flow ... DEACT at once" | NO | no | no time | none |

### Part E. Other time statements in lines 532-628

| Row | Line | Quoted text | Conflict | Depends on 49 | Why | PROPOSAL |
|---|---|---|---|---|---|---|
| R-52 | 541 | "The cloud RUNBOOK.md uses a 3.5 to 4.5 h re-smoke ... made it about 1 hour; SUPERSEDED" | NO | no | stale figures, already listed as superseded | none |
| R-53 | 542 | "Several time stamps in ORDERS blocks (13:00Z to 15:00Z) are wrong" | NO | yes | fine; the 49-minute and 17:40Z figures come from ORDERS.md line 183 and should be checked by the lead against the same correction | PROPOSAL: lead confirms 17:40Z after reading Q30. |
| R-54 | 566 | "`MAIL_WAIT_SECONDS=150.0`, `MAIL_SETTLE_SECONDS=20.0`, `WAIT_STEP_SECONDS=60.0`" | NO | no | inputs to R-33 | none |
| R-55 | 570 | "U-20 CLOSED: Mon 23 Nov 07:00Z reading is 're-pin done by 07:00Z'" | NO | no | consistent with R-46 | none |
| R-56 | 583 | "Also not checked by this document: ..." | GAP | yes | does not say the 49-minute figure is a planning figure | PROPOSAL: add "the 49-minute worst case of the take run and its parts (not measured; rehearsal measures it)". |
| R-57 | 593 | O4: "about Wed 11:20Z / 16:50 IST or later (time U-19)" | NO | no | 11:20 + 5:30 = 16:50 (checked) | none |
| R-58 | 592 | O3: "the take, about Wed 10:00Z / 15:30 IST" | NO | no | checked | none |
| R-59 | 594 | O5: "after the watch, about Wed 11:20Z" | NO | no | same | none |
| R-60 | 595-596 | O6 "same day", O7 "same day, time set by the lead (U-19)" | YES (late Mon take only) | no | same as R-42 | PROPOSAL: same as R-42. |
| R-61 | 597 | O8: "Wed 18 Nov 15:00Z / 20:30 IST (latest Wed 25 Nov 15:00Z / 20:30 IST)" | NO | no | checked | none |
| R-62 | 601-628 (section 15) | map rows | NO | no | no time statements beyond those above (m7, "before W-01") | none |

## G7 and the stop time (asked for, shown)

- Stop time near line 223: "Credits / money stop | Mon 23 Nov 18:29 | 23:59". 18:29 + 5:30 = 23:59 (checked). The row says when the money stops. It does not say when the last take program start is. PROPOSAL (section 3, one new row, outside my range): "Latest start of the take program | Mon 23 Nov 17:40 | 23:10 | 18:29 minus the slowest run of 49 minutes (lead's order, ORDERS.md line 183)".
- G7 (line 265): "re-pin done by Mon 23 Nov 07:00Z (12:30 IST); the chain after it (re-smoke 1 h, practice 1 h, Row 4 0.5 h, rehearsal 2 h, take 1 h) must end before 18:29Z with margin." Arithmetic: 5.5 h = 330 min from 07:00Z ends 12:30Z; adding the gate (25) and watch (20) ends 13:15Z; margin to 18:29Z is 5 h 14 min. Conflict with the 49-minute window: NO for the chain (it ends far before 17:40Z). Two defects: (1) "re-smoke 1 h" is the superseded figure (v4.1 NOTE 14:35Z; the re-smoke has no limit since 2026-11-16, line 211, 411); (2) the chain's end, 12:30Z, is after the 12:00Z slipped-take limit of line 222 and 526, so on this path the take could not be the one allowed "until 12:00Z" unless the limit means "start". PROPOSAL: "...the chain after it (re-smoke: as long as the owner agreed, practice 1 h, Row 4 0.5 h, rehearsal 2 h, gate 25 min, take 1 h) must have its take PROGRAM start before 17:40Z (23:10 IST) with margin." If the re-smoke is 1 h, the take program would start at 11:55Z.

## Which timing sentences must change (short list)

Must change (conflict YES): R-46 (line 524), R-35 (line 497, after r28 only), R-34 (lines 493-494, only if the 49 minutes include the extra 120 s), R-42 and R-60 (lines 510, 514, 595-596: "same day" for a late Monday take), plus G7 (line 265) and the section 3 stop-time row (line 223), both outside my range.

Should change (gap, unclear or wording only): R-30 (line 482) and R-48 (line 526) (wording: say the 12:00Z limit limits the start), R-26 (line 473, scene 4 worst case 248 s against 180 s), R-29 (line 478, one 25-minute figure read two ways), R-33 (line 489, two mailbox waits not counted), R-36 (line 450, no number), R-49 (line 528, 60 versus 49), R-39 (line 508, 5-minute miss), R-56 (line 583).

No change needed: everything in Part A except small tidy proposals R-05, R-08; R-18 to R-25, R-31 to R-32, R-38, R-41, R-43 to R-45, R-47, R-50 to R-55, R-57 to R-59, R-61, R-62.

## Open question for the lead (needed before the PROPOSAL wording is final)

What are the 49 minutes made of? In particular: do they include the owner's typing of `y`, the challenge and `end`; the scene 4 stop and restart (up to 248 s by the lines of this runbook); the two mailbox waits (at least 340 s); the film pause; the 120 s Ctrl-C wait; the post-take counts; and the program's own clean-up? And is the program's refusal rule set to 49 in `stage.env`? Without this, R-34, R-35, R-36 and the "49" in R-31 and R-49 stay proposals.
