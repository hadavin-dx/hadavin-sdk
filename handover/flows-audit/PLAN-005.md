# PLAN-005: independent cross-review of system-map (ORDER 005)
Written 2026-11-16 07:52 UTC / 13:22 IST. Static review only: no runtime, made-up data, edit only handover/flows-audit/.

## Target (read-only copies, from `git archive origin/cloud/system-map`)
- Outputs: /tmp/sm/handover/system-map/{MASTER-MAP.md, SWEEP.md, ONE-PLACE-TABLE.md, REPORT.md, DECISION-one-store.md}
- Whole tree for checking cited file:line: /tmp/smfull (handover/demo, handover/demo3, src, demos, .github)
- Not visible to anyone here: take repo `duplicate-proof-lead-desk`, n8n runtime, HubSpot, SMTP -> UNVERIFIABLE, never guessed.

## What I judge (ORDER 005 focus)
1. One-place table: is the single owner right for STORE, LOG, FILTER, COUNTER, RETRY, NOTICE, OTHER; are the extras truly duplicates; any NEEDED called DUPLICATE or the reverse; anything proposed for deletion/archive that has a caller.
2. The 4 open lead decisions the target lists (dollar-cap place, second alert channel + watcher, what the take proof counter reads, count outside n8n / three roles vs fourth identity).
3. The three Blocker bands in the fix plan (before-video decisions; before-video only if chosen; after-video): is each Blocker real, in the right band.
4. Spot-check every Blocker (raw 20 / dedup 16) and at least half of the Majors against real file:line: CONFIRMED / WRONG / UNVERIFIABLE.
5. What the target MISSED.

## Lanes (agents; all sonnet, fresh, one scope each)
| id | type | scope |
|---|---|---|
| EV5 | general-purpose, "EVIDENCE RUNNER" | script: every citation in Blocker rows and a seeded sample of Major rows of SWEEP.md; caller grep for the 5 ARCHIVE proposals; row/key counts of ONE-PLACE-TABLE. Raw output only, no judging. |
| R5-code | egm:egm-codebase-details | every Blocker finding vs source (read the cited file:line, judge claim) + half the Majors |
| R5-design | egm:egm-design | ONE-PLACE-TABLE owners, DUPLICATE/NEEDED calls, 4 open decisions, three bands |
| R5-zoom | egm:egm-zoom-out | what was MISSED; cut/archive proposals; does the table answer "one place per job" |
Plan review (egm-review-loop, 1 round, small): design_critic + implementation_readiness on this file.

## Order
plan review -> EV5 and R5-* in parallel (R5 also read EV5 output when it lands) -> egm-resolve -> write REVIEW.md, CORRECTIONS.md, LEDGER-ROWS.md -> round 2 only if a Blocker/Major remains in my own outputs (max 2) -> drift check -> FINAL block, push, stop.

## Outputs (reviews-of-system-map/)
REVIEW.md (verdict first, failures first), CORRECTIONS.md (exact fixes to target), LEDGER-ROWS.md (id | source | severity | area | summary | status | fixing artifact | verified-by | date).

## Stop rule
Every Blocker has a verdict with a real file:line read by a reviewer; every claim in REVIEW.md cites it; anything not checked is listed as not checked.
