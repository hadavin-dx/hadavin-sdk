Status: DRAFT, unverified

# Runbook v4.3 patch, timing rows against v4.2 (49-minute window check)

Written 2026-11-16 (UTC) by builder PATCH-H. Static work: files read, nothing run, no spend, no sub-agents. v4.2 and every other file are unchanged; only this file was written. Times in UTC (Z) first, then IST (IST = UTC + 5 h 30 min).

## Read first: what this page is and is not

1. **Every 49-minute figure below is a PROPOSAL.** The only source for 49 minutes and the latest start 17:40Z is the lead's order at `handover/system-map/ORDERS.md` line 183 ("latest start about 17:40Z for window end 18:29Z"). It is not a measurement. I do not know what the 49 minutes contain. Nothing here decides that.
2. Source pages: `work/timing-check-v42-part1.md` (v4.2 lines 1-320, called "C1" with its row number) and `work/timing-check-v42-part2.md` (v4.2 lines 321-628, called "C2" with its R-number). Target file: `inputs/lead-reviews/LEAD-RUNBOOK-TAKE-DAY-v4.2.md` (called "v4.2"). Line numbers below are the real v4.2 line numbers; I opened each line.
3. Old text is copied from v4.2 and was checked by script against the line (result in the last section). Where a v4.2 line is very long I quote only the part that changes; that part occurs once in the line.
4. Arithmetic used (each step shown): 18:29Z - 49 min = 17:40Z; 17:40Z + 5:30 = 23:10 IST; 18:29Z + 5:30 = 23:59 IST; 17:40Z - 12:00Z = 5 h 40 min.
5. Two things in the check pages were wrong or unclear and are handled here:
   - C2 cites the G7 row at line 265. It is line 266 (line 265 is G6). C1 has it right. Rows below use 266.
   - C1 row 16 and C2 row "Last possible start of a retake" give different latest first starts for a retake (16:51Z and 16:06Z). They count different things. See H-3b. I did not choose silently.
6. Section A rows can be applied once the lead accepts them (the 49-based ones stay marked PROPOSAL until the lead answers H-1). Section B rows are HELD: a question is open and I wrote no answer.

## Section A. Patch rows

Format per row: id, v4.2 line, Old text, New text, source.

### PH-01 | v4.2 line 107 (GO / NO-GO rules)

Old (line 107) >> Money stop Mon 23 Nov 18:29Z.

New (PROPOSAL) >> Money stop Mon 23 Nov 18:29Z (23:59 IST). Latest start of any run that spends: 17:40Z (23:10 IST), because the slowest case is 49 minutes (the lead's order of 2026-11-16, not a measurement).

Source: C1 row 1.

### PH-02 | v4.2 line 223 (section 3 table, new row above the money stop row)

Old (line 223) >> | Credits / money stop | Mon 23 Nov 18:29 | 23:59 | Q26-1 |

New (PROPOSAL): keep the old row as it is and insert this row directly above it:

> | Latest start of any run that spends (PROPOSAL, slowest case 49 min) | Mon 23 Nov 17:40 | 23:10 | 18:29 minus 49 min; lead's order, ORDERS.md line 183, not a measurement |

Source: C1 row 2; C2 "G7 and the stop time".

### PH-03 | v4.2 line 236 (spend method)

Old (line 236) >> Window end for any spend: Mon 23 Nov 18:29Z (23:59 IST).

New (PROPOSAL) >> Window end for any spend: Mon 23 Nov 18:29Z (23:59 IST). No run that spends starts after 17:40Z (23:10 IST), so that its slowest case (49 minutes) ends before this time.

Source: C1 row 3.

### PH-04 | v4.2 line 76 (header, how figures are labelled)

Old (line 76) >> Every minute figure is the lead's own estimate from the Q26/Q27/Q30 answers or this file's step estimates, never a measurement.

New (PROPOSAL) >> Every minute figure is the lead's own estimate from the Q26/Q27/Q30 answers or this file's step estimates, never a measurement. The 49-minute slowest case and the 17:40Z latest start come from the lead's order of 2026-11-16 (ORDERS.md line 183) and are not measured either.

Source: C1 row 20.

### PH-05 | v4.2 line 109 (NOT DONE AT FREEZE list)

Old (line 109) >> the time box and tripwire threshold of 8A;

New (PROPOSAL) >> the time box and tripwire threshold of 8A; what the 49-minute slowest case contains and the latest start taken from it (H-1);

Source: C1 row 21.

### PH-06 | v4.2 line 88 (section 2 table row 3, re-smoke has no limit)

Old (line 88) >> the ask states estimated clock times in UTC and IST and the cost;

New (PROPOSAL) >> the ask states estimated clock times in UTC and IST and the cost; on Mon 23 Nov the ask also states that the take program can still start by 17:40Z (23:10 IST);

Source: C1 row 8.

### PH-07 | v4.2 line 211 (section 3 table, re-smoke row)

Old (line 211) >> starts after 08:00 and after his yes; end: the lead states it in the ask

New (PROPOSAL) >> starts after 08:00 and after his yes; end: the lead states it in the ask (on Mon 23 Nov the ask also states the clock time and that the take program can still start by 17:40Z, 23:10 IST)

Source: C1 row 9.

### PH-08 | v4.2 line 266 (G7)

Why: "re-smoke 1 h" contradicts lines 88, 211 and 411 (no 1-hour limit); the 25-minute start-state gate is missing from the chain; "with margin" has no number.

Old (line 266) >> the chain after it (re-smoke 1 h, practice 1 h, Row 4 0.5 h, rehearsal 2 h, take 1 h) must end before 18:29Z with margin.

New (PROPOSAL for the 17:40Z part) >> the chain after it (re-smoke: no limit, its end is stated in the lead's ask; practice 1 h, Row 4 0.5 h, rehearsal 2 h, start-state gate about 25 min, take about 1 h) must end before 18:29Z, and the take program must start by 17:40Z (23:10 IST). Example with a 1 h re-smoke: from 07:00Z (12:30 IST) the take starts at 07:00 + 1 h + 1 h + 0.5 h + 2 h + 25 min = 11:55Z (17:25 IST), 5 h 45 min before 17:40Z, and ends about 12:55Z (18:25 IST).

Arithmetic check: 07:00 + 1:00 = 08:00; + 1:00 = 09:00; + 0:30 = 09:30; + 2:00 = 11:30; + 0:25 = 11:55; + 1:00 = 12:55. 17:40 - 11:55 = 5 h 45 min.

Source: C1 row 7; C2 "G7 and the stop time". Note: whether the 12:00Z slipped-take cut-off means "start" or "end" is H-2.

### PH-09 | v4.2 line 524 (section 11, Tue NO-GO routing)

Old (line 524) >> take later, before Mon 23 Nov 18:29Z;

New (PROPOSAL) >> take later: the take program must start by Mon 23 Nov 17:40Z (23:10 IST) so that its slowest run (49 minutes) ends before 18:29Z (23:59 IST);

Second change in the same line:

Old (line 524) >> the re-pin event of 223 min must start by Mon 23 Nov 03:17Z to be done by 07:00Z.

New >> a repeat of T-06 to T-10 (168 min) must start by Mon 23 Nov 04:12Z (09:42 IST) to be done by 07:00Z; the whole re-pin event of 223 min must start by 03:17Z (08:47 IST) to be done by 07:00Z.

Arithmetic check: 07:00 - 2 h 48 min = 04:12; 04:12 + 5:30 = 09:42. 07:00 - 3 h 43 min = 03:17; 03:17 + 5:30 = 08:47.

Source: C2 R-46. The 12:00Z cut-off wording is not touched here (H-2).

### PH-10 | v4.2 line 348 (T-06, 168 minutes)

Old (line 348) >> that is a new sha and a repeat through T-10 (about 168 min).

New >> that is a new sha and a repeat through T-10 (about 168 min one after another; about 165 min if T-07 runs beside T-08, as lines 355 and 361 allow).

Arithmetic check: 15 + 3 + 40 + 65 + 45 = 168; without the 3 min of T-07 = 165.

Source: C2 R-05. Window-neutral (Tuesday); a tidy-up only.

### PH-11 | v4.2 line 377 (T-08 readiness loop)

Old (line 377) >> Expect `ready` within 12 tries;

New >> Expect `ready` within 12 tries (at most 120 s: 12 x 10 s);

Source: C2 R-08.

### PH-12 | v4.2 line 443 (W-00 shares the practice hour)

Old (line 443) >> (about 06:00Z, inside the practice hour)

New >> (about 06:00Z, inside the practice hour; the restart's readiness wait of up to 120 s and the positive-control wait count against these 60 minutes; with the take program's defaults of 150 s + 20 s the wait is 170 s)

Source: C2 R-17. The 170 s is from v4.2 line 566 (take program defaults); not measured.

### PH-13 | v4.2 line 473 (scene 4 rehearsal, total time)

Old (line 473) >> `<LIMIT_S>` = 180 s unless the rehearsal shows otherwise.

New >> `<LIMIT_S>` = 180 s unless the rehearsal shows otherwise. The restart's readiness wait adds up to 120 s (12 tries of 10 s) to the 53 s stop, so the stop, the start and the takeover are measured together, not assumed. By the lines of this file the worst case adds to 53 + 120 + 45 + 30 = 248 s (4 min 8 s), more than 180 s, unless the 45 s lease already runs during the stop (not measured). If the measured total is over 180 s, scene 4 is cut (G6 rule 2).

Source: C2 R-26, R-27 and its "Scene 4 total worst case" row. The lead writes the measured scene 4 figure into `<TAKE_NOTES>` so the 49 minutes can be rebuilt (H-1).

### PH-14 | v4.2 line 489 (counts proof, two mailbox waits)

Old (line 489) >> the intake mailbox count after `<WAIT_S>` and once more after the stated wait: exactly 1 mail.

New >> the intake mailbox count after `<WAIT_S>` and once more after the stated wait: exactly 1 mail (two waits; with the take program's defaults of 150 s + 20 s each, at least 340 s = 5 min 40 s together; whether they sit inside the 49 minutes is H-1).

Arithmetic check: 150 + 20 = 170; 2 x 170 = 340 s = 5 min 40 s.

Source: C2 R-33.

### PH-15 | v4.2 line 497 (ROUND 28 PENDING, slow answer)

Old (line 497) >> Until then the window is checked only before the prompts, so a slow answer can run past it.

New (PROPOSAL for the 17:40Z part) >> Until then the window is checked only before the prompts, so a slow answer can run past it: a take started right at 17:40Z (23:10 IST) ends after 18:29Z (23:59 IST) by as long as the owner needs to answer. Until r28 lands the lead sets an earlier latest start (the size of the margin is H-4).

Source: C2 R-35. The margin figure is not written (H-4).

### PH-16 | v4.2 line 508 (same-day retake condition)

Old (line 508) >> the same day for a 15:00Z post only if this watch finished by 11:15Z (section 3)

New >> the same day for a 15:00Z post only if this watch finished by 11:15Z (section 3); with the take ending at 11:00Z and a 20 min watch the watch ends at 11:20Z, 5 min too late, so a same-day retake works only if the take ended by 10:55Z

Arithmetic check: 15:00 - 225 min = 11:15; 11:15 - 20 min = 10:55; 10:00 + 60 min = 11:00; 11:00 + 20 min = 11:20.

Source: C2 R-39. This uses the planned 1 h take. If the real take is 49 minutes, see H-3.

### PH-17 | v4.2 line 583 (not checked by this document)

Old (line 583) >> whether n8n's public API has a credentials list route.

New (PROPOSAL) >> whether n8n's public API has a credentials list route; the 49-minute slowest case of the take and what it contains (not measured; the rehearsal measures it).

Source: C2 R-56.

## Section B. HELD rows (a question is open; no answer written)

Each row names the v4.2 lines it would change and the question. When the lead answers, the row becomes a Section A row.

### H-1 | What do the 49 minutes contain?

Lines that depend on the answer: 94 and 218 (take about 1 h), 484, 107, 223, 236 (the 17:40Z figure itself), 450, 493-494, 524, 528.

Question: does the 49 minutes mean the take program's own run only (typed `y`, confirmation line, the run, scene 4 stop and restart, the two mailbox waits, post-take counts, its own clean-up), or also the start-state gate (about 25 min), the lead's watch (20 min), the extra Ctrl-C wait of up to 120 s (lines 493-494), or a failed-run clean-up?

Known pieces from v4.2 that may or may not be inside (all lead estimates, none measured): scene 4 up to 248 s by the lines of this file (PH-13); two mailbox waits at least 340 s (PH-14); Ctrl-C wait up to 120 s; stop of n8n 53 s.

Held sub-rows:
- **H-1a, lines 493-494.** Old (line 493) >> Ctrl-C in the closing phase looks inert for up to 120 s: press it ONCE and wait.
  Candidate new text (only if the lead confirms the 49 contains it): add "(counted in the 49-minute slowest case)". Source: C2 R-34.
- **H-1b, line 450.** Old (line 450) >> window too close
  Candidate: add what the program's refusal rule uses. Held because the program's refusal setting is not in this checkout; C2 says v5 states 14 minutes, v4.2 states no figure. If the program refuses a start with less than 14 minutes left, a start at 18:15Z passes the program's check but not the 49-minute rule; one of the two numbers must change. Source: C2 R-36; C1 "could not check" 4.

### H-2 | 12:00Z slipped-take cut-off versus 17:40Z latest start

Lines: 107 (G6 text in the rules sentence), 222, 265 (G6), 482, 526.

Old texts (for the lead's decision, none changed):
- Old (line 222) >> | NO-GO path: a slipped take is allowed until | Mon 23 Nov 12:00 | 17:30 | Q27-7 |
- Old (line 482) >> Counts proof not green: the take slips (until Mon 23 Nov 12:00Z).
- Old (line 526) >> | Take counts not green | slip one day at the same times, until Mon 23 Nov 12:00Z |

Question 1: does the 12:00Z cut-off stay now that the hard latest start is 17:40Z? The gap is 5 h 40 min (17:40 - 12:00) of room the cut-off gives away. Question 2: does 12:00Z mean the latest start of the take, or the end? (G7 example in PH-08 starts the take at 11:55Z and ends at 12:55Z, so under "end" a 1 h re-smoke path would already miss the cut-off.) Question 3: if both stay, which wins? C1 offers "A slipped take may start until Mon 23 Nov 12:00Z (17:30 IST); the hard latest start is 17:40Z (23:10 IST) for any run." C2 offers a longer sentence with "the owner decides whether to move the planning limit." Both are wording only; the owner or lead decides the figure.

Source: C1 rows 5 and 6; C2 R-30, R-48.

### H-3 | Planned take of 60 minutes versus a 49-minute slowest case

Lines: 94, 218, 484, 226, 266 (PH-08 uses "about 1 h"), 508 (PH-16), 528.

Old texts (none changed):
- Old (line 218) >> | Take (about 1 h) | about 10:00 to 11:00 | 15:30 to 16:30 | Q26-1 |
- Old (line 484) >> ### W-05 THE TAKE (about 10:00 to 11:00Z, 15:30 to 16:30 IST, about 1 h)
- Old (line 226) >> Retake arithmetic: start-state gate 25 + take 60 + edit 120 + lead's watch 20 = 225 min.
- Old (line 528) >> | Retake needed | gate 25 + take 60 + edit 120 + watch 20 = 225 min; a 15:00Z post needs the gate to start by 11:15Z |

Question: is "about 1 h" a planned slot and 49 minutes the slowest run inside it (then there are 11 spare minutes: 60 - 49), or is 49 the true figure and 60 should shrink? This cannot be answered without H-1.

If the answer is "60 is the slot, 49 the run": C2 offers "about 1 h slot (the slowest run takes 49 minutes)" for lines 218 and 484. Retake arithmetic would stay 225 min.

If the answer is "49 replaces 60": retake = 25 + 49 + 120 + 20 = 214 min; gate must start by 15:00 - 3 h 34 min = 11:26Z (16:56 IST); the first take would end 10:49Z, the watch 11:09Z, which is before 11:15Z, so a same-day retake would then fit (C2). Both are PROPOSAL arithmetic; I changed nothing.

**H-3b, latest first start of a retake on Mon 23 Nov (line 226, a possible added sentence).** C1 says the first run must start by 16:51Z (17:40 - 49 min). C2 says 16:06Z (second start = first start + 49 run + 20 watch + 25 gate = first start + 94 min, must be at most 17:40Z). I recomputed: 17:40 - 94 min = 16:06Z (21:36 IST). C1's figure counts only the run, not the watch and gate; C2's counts all three. With the 60 min slot: 17:40 - 105 min = 15:55Z (21:25 IST). Held because it depends on H-1 (what the 49 contains) and on whether a retake needs the 20 min watch and the 25 min gate. Source: C1 row 16; C2 retake row.

Source for H-3: C1 row 4 and open question 3; C2 R-31, R-49.

### H-4 | Margin before the round 28 change lands (line 497, PH-15)

C2 R-35 proposed a 10-minute margin (latest start 17:30Z = 23:00 IST) and itself says it is "not measured". No source gives the owner's answer time, so I wrote no figure in PH-15. Question: how many minutes does the owner need to type `y`, the challenge and `end`, and does the lead want a fixed earlier latest start until r28 lands?

### H-5 | The 25-minute gate versus the 30-minute slot (lines 217, 478, 475)

Old texts (none changed):
- Old (line 217) >> | Start-state gate, sign-off and GO check (about 25 min, then the decision) | 09:30 to 10:00 | 15:00 to 15:30 | Q27-7 |
- Old (line 478) >> ### W-04 Start-state gate, sign-off and GO check (09:30 to 10:00Z, 15:00 to 15:30 IST; gate about 25 min)

Question: line 217 reads "about 25 min" for gate plus sign-off plus GO check together; line 478 reads "gate about 25 min" (gate alone) inside a 30-minute slot. The retake sums use 25 for the gate. Which reading holds, and what is the split (gate N min, sign-off and GO check M min, N + M = 30)? Also whether the new start-state gate in rehearsal 2 (line 475) takes the same 25 minutes. Not 49-related, but it changes the sums that 49 is compared with. Source: C2 R-28, R-29.

### H-6 | Owner decision: clean-up "the same day" after a late Monday take (lines 510, 514, 595, 596)

Old texts (none changed):
- Old (line 595) >> | O6 | S9-2: compare the figures in the settings file by himself | same day, after the lead's "clean-up starts" |
- Old (line 596) >> same day, time set by the lead (U-19) |

Problem: a take that starts at 17:40Z ends at 18:29Z (23:59 IST); the lead's watch runs to 18:49Z (00:19 IST, which is already Tue 24 Nov in IST). "The same day" then cannot hold in IST. For the Wed 18 Nov take the watch ends 11:20Z (16:50 IST) and there is no problem.

Question for the owner: if the take runs late on Mon 23 Nov (C2 suggests after about 16:00Z = 21:30 IST), is the clean-up and key revocation done the next morning, and may the model key stay valid until then (the program's spend stop at 18:29Z, not the key, stops spending)? Only the owner can decide this. Source: C2 R-42, R-60.

### H-7 | How long a failed Row 4 try takes (line 465)

Old (line 465) >> the next try uses a new key and address (sends counted against the up-to-3 ceiling;

C2 R-24 proposes "if less than N minutes remain before 07:30Z, the rehearsal does not start". N is not in any source; the lead sets it from Row 4. Held until measured. Wed 18 Nov, not the 49-minute window.

## Not turned into rows (listed so nothing is silently dropped)

- C1 rows 10 to 15, 17 to 19, 22 to 30 and C2 rows R-01 to R-04, R-06, R-07, R-09 to R-14, R-18 to R-23, R-25, R-32, R-37, R-38, R-40, R-41, R-43 to R-45, R-47, R-50 to R-55, R-57 to R-59, R-61, R-62: both pages say "no change". I did not re-check each of them; I relied on the check pages.
- C2 R-15 (T-12 has no end time, so no computed margin before Tue 14:00Z GO; bound would be 14:00 - 08:00 = 6 h) and C2 R-16 (8A thresholds blank): not 49-related. Not written as rows; the lead's ask already states an end time (v4.2 line 411).
- C2 R-33's "inside the 49 minutes" claim is not written as fact (PH-14 and H-1).

## What I did not check (read first)

1. I do not know what the 49 minutes contain (H-1). Nothing in the files I read says.
2. I did not run anything, so no figure here is measured. Step durations are the lead's estimates (v4.2 line 76 and 407).
3. I read only these v4.2 lines in full: 76, 88, 94, 107, 109, 211, 217, 218, 222, 223, 226, 236, 263 to 267, 270, 348, 355, 361, 377, 402, 407, 409 to 412, 443, 450, 454, 465, 473 to 475, 478, 482, 484, 489, 493, 494, 497, 508, 510, 514, 524, 526, 528, 566, 583, 595, 596. All other claims about lines come from the two check pages, which are themselves marked DRAFT, unverified.
4. I did not re-read or re-compute the rows both check pages call "no change" (see list above).
5. The program `scripts/run_real_check_n8n.py` and its refusal setting are not in this checkout; I cannot say what window figure it really uses (H-1b).
6. No bible (`RULES.md`) is in this checkout, so I cited no R-numbers. EGM skipped for this step: it turns two reviewed check pages into a patch list of text proposals, nothing built; the lead's EGM review of the patch comes before it is applied.
7. The v4.2 file may have been edited after the check pages were written; I did not compare file dates.
