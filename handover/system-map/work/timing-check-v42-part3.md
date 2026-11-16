Status: DRAFT. Read-only check; nothing was run, nothing changed except this page. Unverified: every minute figure in the runbook is the lead's estimate, not a measurement; the lead's answers are taken as given and were not checked against the take program (it is not in this checkout); I did not open lines of v4.2 outside the ones named in the brief except where a grep for time words pointed to them.

# Timing check, part 3: take-day runbook v4.2 against the lead's answers 6, 7, 8, 9, 10, 14, 15, 16, 17

Written 2026-11-16 (UTC). Times in UTC (Z) and IST (IST = UTC + 5 h 30 min). "Lead" means the studio lead (the Claude session on the owner's laptop). Verdicts: HOLDS = still true after the answers; CHANGE = the line must be reworded; OPEN = the answers do not settle it.

## What the answers fix (the new rules, one line each)

- 49 minutes = the take program's own run only. The program computes it: 2630 s + 6 x lease, lease 45 s = 2630 + 270 = 2900 s = 48 min 20 s, rounded up to 49 min (answers 6, 14). It is not a stored setting. It covers posts, table and mail waits, final reads and the margin (answer 15 b, c, e, f, g). It does not cover the owner's typed answers before the window check (15 a) and has no term for a film pause (15 d).
- Hard latest start 17:40Z (23:10 IST): the program refuses a start that leaves less than 49 min before the stop time 18:29Z (23:59 IST). 18:29 minus 49 min = 17:40 (answer 7).
- Planning target: start by 12:00Z (17:30 IST) so a failed run still has the afternoon. Both times are written (answer 16).
- Pause while filming: at most 10 minutes, with an alarm (answer 8; whether the program enforces it is not yet answered).
- No same-day rerun after a failed run; the next try is a new day inside the credit window, chosen by the owner (answers 6, 9).
- Clean-up: next morning (answer 17).
- Notice: at least 3 hours before the start time the notice names (answer 10).
- Obsolete: the 14-minute figure, and 18:15 and 18:14:40. A search of v4.2 found none of them (they sit in the owner sheet v5, see timing-check-a.md). Nothing to delete in v4.2.

## Table

| v4.2 line | quote | verdict | new wording | answer |
|---|---|---|---|---|
| 86, 209, 325 | "start no later than 04:17; done by 08:00" (re-pin, 223 min) | HOLDS | none. Tuesday work, unrelated to the 49 minutes. 08:00Z - 223 min = 04:17Z (09:47 IST). | not touched |
| 88, 211, 409 | "no 1-hour limit ... the ask states estimated clock times" (loopback re-smoke) | CHANGE (one sentence added) | add: "On Mon 23 Nov a re-smoke must end early enough that the take program can still start before 12:00Z (planning) and never after 17:40Z (23:10 IST), and the 3-hour notice must already be sent." | 7, 10, 16 |
| 94, 218, 484 | "THE TAKE ... about 1 h" (10:00 to 11:00Z, 15:30 to 16:30 IST) | CHANGE | "Take slot about 1 h (planning). The program's own run is at most 49 min. Add before it: the owner's three typed answers (`y`, the challenge, `end`; not counted in the 49). Add after it: a film pause of at most 10 min (not counted in the 49). Worst case from the answers: 49 + 10 = 59 min plus the typing time, so the slot can run past 11:00Z; the lead measures the typing time at rehearsal." | 6, 8, 15 a, d |
| 107, 223, 236 | "Money stop Mon 23 Nov 18:29Z" / "Window end for any spend: 18:29Z (23:59 IST)" | CHANGE | add a row/sentence: "Hard latest start of the take program: Mon 23 Nov 17:40Z (23:10 IST) = 18:29Z minus 49 min. The program refuses a later start." Keep 18:29Z (23:59 IST) as the stop. | 7, 16 |
| 450 | "refusal (... window too close ...) 2" | CHANGE | "window too close = less than 49 minutes (2630 s + 6 x lease 45 s, rounded up) left before the stop time; computed by the program, not a setting; latest start 17:40Z (23:10 IST)". | 7, 14 |
| 497 (ROUND 28 PENDING) | "the time window is re-checked after the `y` prompt ... Until then the window is checked only before the prompts, so a slow answer can run past it" | CHANGE | keep the sentence; add: "The owner's typing time is not inside the 49 minutes. Until the re-check lands, the lead plans the three answers to finish well before 17:40Z; after it, a late answer is refused." | 15 a |
| no line (gap) | film pause not mentioned anywhere in v4.2 (search for "pause": 0 hits) | CHANGE (new line in W-05) | "A pause while filming lasts at most 10 min; the lead sets an alarm at the start of the pause. The 49 minutes have no term for a pause, so a take started at 17:40Z with a 10-min pause could end at 18:39Z, past the 18:29Z stop. Until the program is shown to stop spending itself, the hard latest start with a pause planned is 17:30Z (23:00 IST) = 18:29 - 49 - 10." The last two sentences are my arithmetic, not an answer. | 8, 15 d |
| 487 (W-05 take command) | "its notice states 3 people, maximum model calls, contacts and mails" | CHANGE | add: "The notice goes to the owner at least 3 hours before the start time it names. For a Wed take at 10:00Z (15:30 IST) the notice is due by 07:00Z (12:30 IST); for a start at 12:00Z, by 09:00Z (14:30 IST); for the hard latest start 17:40Z, by 14:40Z (20:10 IST)." Section 3 gets one row for it. | 10 |
| 213, 214, 216 | practice 1 h; Row 4 30 min; rehearsal about 2 h | HOLDS | none for the times. Whether a repeat of a rehearsal or practice step on the same day counts as "same-day rerun" is not answered (see the lead-fact list). | 9 (scope) |
| 217, 478 | gate "about 25 min" in a 09:30 to 10:00Z slot | HOLDS | none. Not touched by the answers. (Earlier finding in part 2, R-29: 25 min and the 30-minute slot are read two ways; still open, not an answer-number item.) | none |
| 156, 127 | "up to 45 s + 5 s + 3 s (53 s worst case)" | HOLDS | none. 45 + 5 + 3 = 53 s. | none |
| 193, 473 | "scene 4 limit (default 180 s)" / "`<LIMIT_S>` = 180 s" | HOLDS | none; "limit 180 stays, rehearsal measures". Part 2 computed a possible 248 s from the runbook lines; the rehearsal decides; over 180 s scene 4 is cut (G6 rule 2). | 18 (other answer) |
| 489 | counts proof: mailbox count "after `<WAIT_S>` and once more after the stated wait" | HOLDS | none. Mail waits are inside the 49 (answer 15 c). Two waits of at least 170 s each is about 5 min 40 s of the 49. | 15 c |
| 493, 494 | Ctrl-C "inert for up to 120 s ... a further signal after 120 s" | HOLDS | none. The 120 s clean-up bound is the margin inside the 49 (answer 15 e). | 15 e |
| 226 | "a same-day retake for the 15:00Z post is NOT possible unless the watch finishes by 11:15Z" (225 = 25 + 60 + 120 + 20) | CHANGE | replace the paragraph: "There is no same-day retake after a failed run. A retake is a new day inside the credit window, chosen by the owner; the post then moves to the next suitable day, never later than Wed 25 Nov 15:00Z (20:30 IST). The 225-minute arithmetic is no longer used." | 6, 9 |
| 251 | "Each retake | repeat of the take row, new keys, new tag" | CHANGE (small) | "Each retake (on a new day, never the same day)". | 9 |
| 270 (G11) | "Any extra mail: stop, retake with new keys and a new address" | CHANGE | add "on a new day". | 9 |
| 491 (W-05 Failure) | "stop, retake with new keys and a new address (back to W-04)" | CHANGE | "stop; no retake today; next try on a new day from W-04 with new keys, new address and a new tag; the owner chooses the day." | 9 |
| 508 (section 10 step 3) | "If a retake is needed: the same day for a 15:00Z post only if this watch finished by 11:15Z" | CHANGE | "A retake is never the same day. A retake needs a new `<TAKE_TAG>`, new keys, a new made-up address, the model key and passwords still valid and the ceiling re-checked." | 9 |
| 528 (section 11) | "Retake needed | gate 25 + take 60 + edit 120 + watch 20 = 225 min; a 15:00Z post needs the gate to start by 11:15Z" | CHANGE | "Retake needed: new day, chosen by the owner; no same-day retake." | 9 |
| 222, 265 (G6), 482, 526 | "a slipped take is allowed until Mon 23 Nov 12:00Z (17:30 IST)" | CHANGE | "Planning target: a slipped take starts by Mon 23 Nov 12:00Z (17:30 IST). Hard latest start: 17:40Z (23:10 IST), the program refuses a later start. 12:00Z is the earlier of the two and applies to the start of the program, not to its end." The reason the answer gives ("a failed run still has the afternoon") conflicts with answer 9, see lead-fact list. | 16, 7 |
| 221, 266 (G7), 524 | NO-GO path: re-pin by Mon 23 Nov 07:00Z; chain "re-smoke 1 h, practice 1 h, Row 4 0.5 h, rehearsal 2 h, take 1 h ... must end before 18:29Z with margin" | CHANGE | "re-smoke: as long as the owner agreed in the ask" (the 1 h is superseded); add the 25-min gate; replace "must end before 18:29Z with margin" with "the take program must start by 12:00Z (planning), never after 17:40Z (23:10 IST)". With a 1 h re-smoke the chain from 07:00Z puts the take program start at 11:55Z (07:00 + 60 + 60 + 30 + 120 + 25 minutes), 5 min inside the 12:00Z target, so there is almost no room for a longer re-smoke (arithmetic mine). Also add "notice due 3 h before the start". | 7, 10, 16 |
| 524 | "take later, before Mon 23 Nov 18:29Z" | CHANGE | "take later; the program must start before 17:40Z (23:10 IST), planning target 12:00Z (17:30 IST)". The 168 min and 223 min arithmetic stands (re-pin start by 03:17Z). | 7, 16 |
| 224, 517, 96 | "post at the latest Wed 25 Nov 15:00Z (20:30 IST)"; "post Wed 18 Nov 15:00Z" | HOLDS | none for the dates. Check with the new worst case on Wed 18: take 10:00Z + typing + 49 + 10 min pause, then watch 20 min, hand-over, edit 120 min; even with 15 min of typing the hand-over is about 11:35Z and the edit ends about 13:35Z, 85 min before 15:00Z (my arithmetic). | none |
| 502 (title), 510, 514, 595, 596 | "AFTER THE TAKE (same day)"; owner clean-up and revoking "the same day" (O6, O7 "same day") | CHANGE | "Watch and copy out the same day (steps 1 to 3). The owner's clean-up (step 5: delete the made-up contacts by the filtered list, compare figures, revoke the model key, app passwords and HubSpot private apps) is done the next morning; the lead sends the message in time and gives the clock time in UTC and IST." Section 10 title: remove "(same day)". The rule "nothing is revoked before step 3 passes" is unchanged. | 17 |
| 593 (O4) | "about Wed 11:20Z / 16:50 IST or later (time U-19)" | CHANGE | "next morning; time set by the lead (U-19), stated in UTC and IST". | 17 |
| 515, 516 (steps 6, 7) | lead teardown (delete n8n credentials, stop n8n, remove the database container) and the retire check, "after step 5" | OPEN | They already come after step 5, so they move to the next morning with it. Whether the lead may tear down the same evening is not answered. | 17 |
| 506 (step 1) | "Copy out first" (result.json, logs, counts, recording sha-256) | HOLDS | none; it stays on the day of the take, before anything is changed. | 17 (consistent) |
| 454, 525, 265 (G6), 526 | "NO-GO that day; try again the next day at the same times"; "slip one day at the same times" | HOLDS | none; this is the same rule as "no same-day rerun". | 9 |
| 252, 4 (spend rows) | "each retake adds the take row" | HOLDS | none; a retake on a new day still adds the row. | 9 |

## Lines needing a lead fact that is not in the answers

1. What "steps A to D happen before the start" means (answer 6). In v4.2 "Step D" is the owner's clean-up after the take (lines 500, 510), and Step A is removed (line 514). Which steps are meant, and are they the take program's own?
2. Is the 10-minute pause inside or outside the program's stop time, and does the program end itself or does a person type `end` (answer 8 sent this to core-hardening)? Without it the hard latest start with a planned pause is 17:30Z (23:00 IST), not 17:40Z.
3. Answer 16 gives "so a failed run still has the afternoon" as the reason for 12:00Z, but answer 9 says a failed run is not repeated the same day. What is the afternoon for? (Mon 23 Nov is the last day of the window, so a failed run that day has no later day.)
4. Does "no same-day rerun" (A13) also bar a repeat of Rehearsal 2, a practice step or a retake caused only by a recording defect (a private address on screen, line 509)? The answers speak of a failed run only.
5. Which notice has the 3-hour rule: the program's printed notice (line 487), the lead's ask to the owner, or both; who sends it, and does each take-program start need its own notice?
6. How long the owner's three typed answers take (outside the 49), and whether the lead may tear down the same evening (lines 515, 516).
7. Retake day: after a failed Wed 18 Nov take, is the next try Thu 19 Nov at the same times, as lines 454 and 525 say, or whatever day the owner picks (answer 9)?

## Not checked

The take program itself (not in this checkout); lines of v4.2 beyond the ranges in the brief except where a search for time words pointed to them; the owner sheet v5 and RUNBOOK-SPEED-3; any measurement. No sub-agent, no spend. EGM skipped: read-and-list timing check, as the brief says. R-numbers: none looked up (no bible in this checkout).
