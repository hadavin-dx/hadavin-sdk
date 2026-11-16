Status: resolved (round 1 of max 2). Date 2026-11-16. Findings: item7-review-round1.md. Target: AUDIT-FINDINGS.md. Headless, auto-accept PROPOSE FIX; no CONTEST, no ESCALATE.
| id | sev | category | action |
|---|---|---|---|
| Z1 stale top text | Blocker | PROPOSE FIX | applied: lines 2,5-8,16,17, Q11, 2b marked superseded (AUDIT-FINDINGS.md) |
| Z2 gate mislabelled | Blocker | PROPOSE FIX | applied: gate split into "before an executor", "live not yet scheduled" |
| Z3 live Majors unplaced | Major | PROPOSE FIX | applied: "Next batch" line in section 4 |
| Z4, C1 judge already charged; size | Major | PROPOSE FIX | applied: reserve-before wording, atomic reserve note, largest item |
| Z5 uneven rule | Major | PROPOSE FIX | applied: CI-gate exception in the rule; D3-03, R-09, R-10 to Nit |
| Z6 two ratings | Major | PROPOSE FIX | applied: R-06 merged into A-02; counts now 3/29/118 lanes, 3/37/123 with R/ADD |
| Z7 G5 decided | Major | PROPOSE FIX | applied: dropped (ORDER 009); A-10 delete moved behind the gate |
| Z8 redaction size | Major | PROPOSE FIX | applied: tests first, fix only for failing tests |
| C2 other model calls | Major | PROPOSE FIX | applied: judge.py:72, extract.py:47 named; extract body NOT READ |
| C3 R-07 cite wrong | Major | PROPOSE FIX | applied: known-limit and longest-first claims removed |
| C4 R-09 figures | Nit | PROPOSE FIX | applied |
| C5 R-11 | Nit | PROPOSE FIX | applied |
| C6 2b vs 2a | Nit | PROPOSE FIX | applied |
| C7 ADD-2 in plan | Nit | PROPOSE FIX | applied (plan step 2) |
| C8-C10 item4 cites | Nit | PROPOSE FIX | applied in item4-job-owner-table.md |
| Z9-Z13 nits | Nit | PROPOSE FIX | applied: banners, 9b/9f note, terms, cite-claim wording, NOT-NEEDED-YET note |
Also applied from C: tick.py:323 writes last_ok_at per step (dead-man check reads a named step); gate.py:59 cite for R-06.
Counts: accepted 21, contested 0, escalated 0, declined 0. Remaining: nothing Blocker or Major open from this round. A second round would only be needed for a Blocker or Major; none remains by my own reading, but a fresh reviewer has not confirmed it (the round cap is 2; I have used 1).
Not verified: lane parts I-VII were read by neither reviewer; item3 readers' findings are static.
