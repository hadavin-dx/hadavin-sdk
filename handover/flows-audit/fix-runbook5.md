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
event 269 4 h 29 min sum terms 3 + 5 + 5 + 3 + 10 + 25 + 3 + 20 + 15 + 25 + 30 + 15 + 20 + 15 + 30 + 30 + 15
repeat 146 2 h 26 min steps 3,4,4b,5,9,10,11,12,13
start 1 04:00 UTC (09:30 IST)
start 2 04:03 UTC (09:33 IST)
start 3 04:08 UTC (09:38 IST)
start 4 04:13 UTC (09:43 IST)
start 4a 04:16 UTC (09:46 IST)
start 4b 04:26 UTC (09:56 IST)
start 5 04:51 UTC (10:21 IST)
start 6 04:54 UTC (10:24 IST)
start 7 05:14 UTC (10:44 IST)
start 8 05:29 UTC (10:59 IST)
start 9 05:54 UTC (11:24 IST)
start 10 06:24 UTC (11:54 IST)
start 11 06:39 UTC (12:09 IST)
start 12 06:59 UTC (12:29 IST)
start 13 07:14 UTC (12:44 IST)
start 14 07:44 UTC (13:14 IST)
start 15 08:14 UTC (13:44 IST)
event end if step 1 at 04:00 08:29 UTC (13:59 IST) ; to end 08:00 step 1 must start 03:31 UTC (09:01 IST)
no-start 60 429 06:51 UTC (12:21 IST) | with repeat 575 04:25 UTC (09:55 IST) | old formula (event+resmoke only) 329 08:31 UTC (14:01 IST) | old with repeat 475 06:05 UTC (11:35 IST)
no-start 90 459 06:21 UTC (11:51 IST) | with repeat 605 03:55 UTC (09:25 IST) | old formula (event+resmoke only) 359 08:01 UTC (13:31 IST) | old with repeat 505 05:35 UTC (11:05 IST)
from 08:00 end: resmoke60 09:00 UTC (14:30 IST) spare 300 ; 09:30 slot spare 270
repeat from 08:00 end 10:26 UTC (15:56 IST) resmoke60 11:26 UTC (16:56 IST) spare 154 | 90 11:56 UTC (17:26 IST) spare 124
from 04:00 start: resmoke end 09:29 UTC (14:59 IST) spare 271 after extras 171 ; 09:30 slot after extras 170 ; repeat still fits by 24
W-Tue start 01:30 UTC (07:00 IST) W-Wed window 20 h 16 min
--- Wed
positive control 07:30 UTC (13:00 IST) -> 07:40 UTC (13:10 IST)
rehearsal 1 07:40 UTC (13:10 IST) -> 08:25 UTC (13:55 IST)
step 22 08:25 UTC (13:55 IST) -> 08:40 UTC (14:10 IST)
rehearsal 2 08:40 UTC (14:10 IST) -> 09:25 UTC (14:55 IST)
block end 09:25 UTC (14:55 IST) gate end 09:50 UTC (15:20 IST) GO end 09:55 UTC (15:25 IST) spare to 10:00 5
with apply: block end 09:35 UTC (15:05 IST) GO end 10:05 UTC (15:35 IST)
watch 11:00 UTC (16:30 IST) -> 11:20 UTC (16:50 IST) edit -> 13:20 UTC (18:50 IST) spare 100
latest take start (60+20+120+10=210) 11:30 UTC (17:00 IST)
retake 25+60+20+120=225, +10=235 11:05 UTC (16:35 IST)
step18 regenerate from 07:00 + REP 09:26 UTC (14:56 IST)
chain 355 5 h 55 min
A end 12:55 UTC (18:25 IST) margin 5 h 34 min latest event end 12:34 UTC (18:04 IST)
A repeat 15:21 UTC (20:51 IST) margin 3 h 08 min latest event end with repeat 10:08 UTC (15:38 IST)
B event end 11:29 UTC (16:59 IST) take end 17:24 UTC (22:54 IST) margin 1 h 05 min
B repeat take end 19:50 UTC (01:20 IST) after stop
B latest start with repeat 05:39 UTC (11:09 IST) no repeat 08:05 UTC (13:35 IST) | minutes 770 12 h 50 min 624 10 h 24 min
```

## Test of the two FINAL greps (made-up lines, not a real take_check run)
Commands per sample file F: grep -c '^FINAL: take_check exit status 0\. ' F and grep -c '^FINAL: .*RESULT: 0 FAIL' F
```
== final-good.txt
exit-status-0 count: 1
RESULT 0 FAIL count: 1
== final-bad.txt
exit-status-0 count: 0
RESULT 0 FAIL count: 0
```
Good sample gives 1 and 1; a sample with status 4 and 1 FAIL gives 0 and 0. Limit: the samples copy the format of take_check.sh line 304; the real script was not run.

## Finishing commands (run from handover/flows-audit)
| Command | Exit code |
|---|---|
| python3 -I tools/check_secrets.py (PASS 0 hits in 1782 files) | 0 |
| python3 tools/check_refs.py (PASS 5146 references) | 0 |
| ruff check . (All checks passed) | 0 |
| ruff format --check RUNBOOK.md (1 file already formatted) | 0 |

## Not checked
- No step was run; take_check.sh was read, not executed.
- The real RESULT line text of the checker was not seen in a live run (grep 2 relies on the format `RESULT: 0 FAIL`).
- OWNER-STEPS-q16-rows.md and ORDERS.md were read only; their wording is for the lead (section 9).
- All minute figures are audit estimates.
