# fix-runbook5.md: round 5 fixes to RUNBOOK.md (fixer log)

Scope: static edits only. Only RUNBOOK.md and this log were written. Nothing ran in n8n, Postgres or HubSpot. Data is made up. No commit. Backup of the round 4 file: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rb5/RUNBOOK.md.
Source of the findings: reviews/round-12z-findings.md, section "RUNBOOK.md readiness round 5" (reviewer words were unverified; each item below was checked against the named file).

## Failures and uncertain items first
- Not run: no step was executed; every timing is an estimate by this audit, not a measurement.
- Arithmetic slip found and fixed by me during this round: an earlier draft of the section 8 chain counted the 10 min positive control twice (it is already inside the 115 min rehearsal block), giving 365 min. The correct sum is 355 min. The runbook and the script output below use 355. The log of the round 4 figure (350) is mentioned in the text.
- Honest note kept in the runbook: the lead's plan "re-pin done about 08:00 UTC" (13:30 IST) is about 29 min optimistic against this audit's sums if step 1 starts at 04:00 UTC (event 269 min, ends 08:29 UTC).
- Facts no file holds are LEAD FILLS rows with a recommended default marked "planned by the audit, lead to confirm": I40 to I46 (new), plus I9, I24, I34, I36, I38 reworded. Open for the lead: services and switch per step (I43), apply when N is exceeded (I44), paid-call count (I41), retake yes in advance (I42), whose clock (I46), new K3/K3B wording (I34).
- The reviewer's no-start limits (07:36 and 07:06) differ from mine (06:51 and 06:21) because the reviewer left out step 4b (25 min) and step 17 (10 min); I kept mine.
- The readiness address of step 7 (/healthz/readiness, 200) comes from inputs/plan-wp6-resmoke-v5.md lines 148-149 and is marked UNVERIFIED.

## Verdicts per finding (all confirmed; none wrong)
| Finding | Verdict | Evidence | Fix in RUNBOOK.md |
|---|---|---|---|
| B1 FINAL grep can never match | CONFIRMED | flow-check/take_check.sh line 304 prints `FINAL: take_check exit status $RC. Flow files sha256 (four files, combined): $FLOWSHA. ${RESULTLINE...}` | step 5 and step 13 use two greps, each must count 1; tested below on made-up lines |
| B2 no step replaces pin line 2 | CONFIRMED | take_check.sh reviewer_ok (rejects "session", "lead to confirm", PLACEHOLDER, stand-in names, bad or future dates); `--write-warn-pin` writes a PLACEHOLDER line and exits 4 | new step 4b (pin 1) and step 13 (d): sed on line 2 by a person, the three/four shas, failures 3 and 4 |
| M1 which services each step talks to | CONFIRMED, partly unanswerable | DECISIONS item 1 (real-v5 only), ORDERS line 144 item 10 | new subsection "Which services each step talks to"; the rest is I43 |
| M2 apply of N, lease, recovery; no time | CONFIRMED | no file gives the apply method | step 22 rewritten (15 min, 25 with apply), recording test moved in; I44 |
| M3 re-read of F-031, F-007, F-028 | CONFIRMED | FINDINGS.md F-028 | step 14 re-read commands, count >= 2 plus no-digit check; I34 for K3/K3B wording |
| M4 to M9 | CONFIRMED | see failure 15 of RUNBOOK.md for the per-item text | steps 6, 7, 9, 11, 18, 19, 21, 24, 26 to 30 changed as listed in failure 15 and 16 |
| Minor: stale INFO sentence | CONFIRMED | take_check.sh says "This script never deletes them"; grep shows only the two run_all scripts name it | removed from step 5 and section 9 |
| Failure 13 incomplete | CONFIRMED | ORDERS lines 135 and 144 contradict on whose clock | failure 13 (j) to (p) added; I46 |
| Nits (line cites, labels) | FIXED where in RUNBOOK.md | check_refs passes | section 7 rows labelled RC1 to RC15; section 10 column renamed "Needed by (first use)" |

## Changes in this last batch (sections 8, 9, 10)
- Section 8: N4 regenerate text now 146 min with the steps named; latest-day arithmetic rewritten with chain 355 min (A end 12:55 UTC, margin 5 h 34; with a repeat 15:21, margin 3 h 08; B take end 17:24, margin 1 h 05; latest start 05:39 with repeat or 08:05 without); T4 trigger now also covers a missing S9-2 reply or scope answer.
- Section 9: INFO bullet replaced; new bullet on OWNER-STEPS alignments (retake timing against I42, paid-call count I41, S9-2 order, scope question, recording-ready message after step 29).
- Section 10: column "Needed by (first use)"; Tuesday times shifted to the step clock; rows I2, I9, I10, I24, I26, I27, I31, I34, I36, I38 updated; rows I40 to I46 added.

## Command for the figures (run from the scratchpad folder)
`python3 -I /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/rb5/calc.py`
Output:
```
