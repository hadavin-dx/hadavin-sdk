# P4c round 1 disposition (revision author, 2026-11-06)

- Ticket: `tickets/P4c.md` revision 2 (280 lines), written from revision 1 (236 lines, commit `63549c7`) by applying `reviews/P4c-round1-resolve.md`. Findings read only to check the resolve was applied faithfully: `reviews/P4c-round1-adversarial.md` (A1-A17) and `reviews/P4c-round1-correctness.md` (C1-C16).
- Result: 33 finding ids. 31 applied (7 of them feature cuts as listed in the resolve's Positions: A3, A4/C4, A5/C3a, A6/C2, C5, C11, C14), 2 declined as the resolve says (A13, A14). Unaddressed: 0.
- Honest limits first. I ran nothing: no Postgres, no pytest, no import of the code; only reads and greps. Every SQL claim, every P4b1 name and every line number into `src/` stays UNVERIFIED in the ticket. I did not re-read the full text of the two review files row by row; I used them to check each resolve row names the right defect. I did not verify the reviewers' "found sound" lists.

## One row per finding id

| id | decision | where in revision 2 |
|---|---|---|
| A1, C1 | applied | Rule 6 (two entry paths, `_wall_stop`), interface of `agent_loop.py` (b), T2 rows (a)-(d), T5, mutant m21 |
| A2 | applied | P4c-2 "Where the model call is held" (judge hold before `injection_check`), T2j, T3j, T4j, T7j, mutants m22, m23, PENDING LEAD 15 |
| A3 | applied (cut) | estimate-exceeded row, `guard/estimate_exceeded` audit row, R4 text and m19 removed; T6 rewritten; R4 now defers to P4b1 `on_overshoot`; PENDING LEAD 14 |
| A4, C4 | applied (cut) | no `attempts`/`max_attempts`; period-bounded `claim_wall_alert(..., today=, retry_after_s=)` and `list_unsent_wall_alerts(..., today=)`; tick step raises only on current-period rows; W10; mutant w13 replaces w4, w9; PENDING LEAD 13 |
| A5, C3(a) | applied (cut) | `alert_to: str \| None`; no `MAX_ALERT_RECIPIENTS`; v1.1 row and PENDING LEAD 11 |
| C3(b), A15 | applied | "at least once, normally once" in the problem text, both templates, T5, T10; T10 crash-between-send-and-mark row (m13) |
| A6, C2 | applied (cut) | `raise_wall` with no `alert_to`: no claim, no row; `LogAlertSink` gone; T5 dev row; mutant m25 |
| A7, C10 | applied | the two golden templates copied from the resolve (daily, monthly, IST suffix only for UTC); T12 golden rows; `run_budget` card unchanged |
| A8 | applied (as narrowed) | `defaults.py` constant with comment, no worker thread; T10 A8 row (300 > Slack default read with `inspect.signature`); mutant m26 |
| A9 | applied | W2 A9 row (Python clock patched one day ahead); kills w3 |
| A10 | applied | T5 A10 row (advancing clock across midnight); kills m4 |
| A11, C15 | applied | T8 scan by attribute names `chat` and `apply_guardrail`; Bedrock row; demo pipeline row; v1.1 row for the vendor charge |
| A12 | applied | hot-file list for `runtime/agent_loop.py`: P2a-1, P4c-2, P5c; "P2a-1a/1b" renamed "P2a-1" everywhere; PENDING LEAD 5 |
| A13 | declined (Nit) | not built; one CHANGELOG sentence is listed under the `registry.py` bullet |
| A14 | declined (Nit) | not built; stated in the `deferred.py` bullet |
| A16 | applied | `retry_unsent` drop rule (log, one `dropped` audit row, not counted, no raise); T10 A16 row; mutant m24 |
| A17 | applied | Rollback item (1) marked UNVERIFIED, pinned by P4b1-a parity row (`P4b1.md:85`) |
| C5 | applied (cut) | no `AlertSink`, `alert_sink`, `reaches_person`, old T13, m15; six `pilot_cfg` files listed and in the P4c-2 pytest command; PENDING LEAD 12 |
| C6 | applied | `DRIVERS` row in `tests/test_k5_round9.py`, fuzz-map note, no `MODEL_CALLERS` row |
| C7 | applied | fail-before base is the pre-P4c head, not `ce70eb5`; W7(d) in its own module `test_store_wall_alert_missing.py`; "new feature" labels |
| C8 | applied | R1-R6 rewritten against `P4b1.md` revision 1 (`Limits.caps`, `Limits.hold`, `OverBudget`, `MeterUnavailable`, `Hold.day`); own `Caps` deleted; `WALLS` table with consistency test; P4b1 name defect relayed; PENDING LEAD 4 replaced by 15 |
| C9 | applied | `App.wall_alerter` field; tick step reads it; T13 through `run_tick(app)` |
| C11 | applied (cut) | no `alerts.WallAlert` dataclass; `render(agent_id, wall, period, limit_usd, zone)`; only `models.WallAlert` keeps the name |
| C12 | applied | triggers force `claimed_at` and `sent_at`; DDL one column per line ending `\n);`; memory store uses injected wall-time clock; W9; mutant w12 |
| C13 | applied | audit fields named (`object_ref`, `result` sent/failed/dropped, `error_code` class name), no recipient count |
| C14 | applied (cut) | StopGate section and PENDING LEAD 2 removed (item 2 marked WITHDRAWN); pointer to P2a v1.1 row; stop-switch bullet restated against P2a revision 10 (marked UNVERIFIED for the SQL) |
| C16 | applied | `Money` cited at `config.py:40-47`; `tick.STEPS` at `tick.py:249-270`; stale `worst_case_usd` cite deleted |

## Where I deviated from, or went beyond, the resolve (flagged)

1. **Run id for the tick path.** The resolve says fall back to `tick:wall_alerts`. `limits.py:35` already uses `"-"` for rows that belong to no run, so the ticket uses `"-"` (marked UNVERIFIED on the build base).
2. **Pruning owner.** The resolve's Couplings line says pruning of past-period rows stays with P4b2's maintenance identity. P4b2's round-1 resolve (line 40) says pruning is not P4b2's and the separate identity is cut. The ticket therefore says: no pruning in v1, no DELETE grant, a v1.1 row with a trigger, and states the difference in Couplings. This is a conflict between two resolves; the lead should confirm.
3. **P4a revision.** The resolve says revision 11; the file on disk is revision 12. The ticket cites 12.
4. **Anchors.** `_limits_stop` is cited at `agent_loop.py:238-250` (the resolve and revision 1 said 240-251); re-read on `ce70eb5`.
5. **Judge settlement for several judges (my refinement, extra m27).** The resolve says settle at the verdict cost when it has one and at the reserved amount otherwise. With two or more judges in an `AnyOf` list the summed verdict cost hides which judge failed, so the ticket settles at the reserved amount unless there is exactly one judge, a positive cost and no `guard_unavailable` code. This over-counts in those cases on purpose (upper bound, P4d PL23). Mutant m27 and test rows in T7j cover it; v1.1 row for exact per-judge booking.
6. **Mutants m25-m27 are mine** (not in the resolve): m25 (claim taken with no `alert_to`) follows from A6; m26 follows from A8; m27 follows from item 5.
7. **"One audit row" for a dropped row (A16).** Without a status column a dropped row cannot be deduplicated across passes. The ticket says one `dropped` audit row per pass, not once ever. A later column could fix that; not added (cut surface).
8. **Tick step also fails only for current-period rows** (follows A4); the ticket says so in the interface and in T10/T13.
9. **Added a wiring note:** the tick step and `App.wall_alerter` are new on the hot-file lists (PENDING LEAD 5).

## Recount (commands run: `wc -l`, `grep -c` on the ticket)

- Lines: 280 (revision 1: 236).
- Mutants: P4c-1 = 11 (w1, w2, w3, w5-w8, w10-w13); P4c-2 = 25 (m1-m14, m16-m18, m20-m27). Deleted from revision 1: w4, w9, m15, m19. Total 36. Revision 1 had 11 + 20 less the deletions plus new ones; the table rows were counted by grep (`^| w` = 11, `^| m` = 25).
- Test rows: P4c-1 W1-W10 (10 rows, W7 has parts a-d, W6 has i-iii). P4c-2 T1-T13 (13 rows) plus the judge rows T2j, T3j, T4j, T7j. Revision 1 had W1-W9 and T1-T13; W10 is new, old T13 (`reaches_person`) deleted and the tick/App row became the new T13.
- Template fields: each sub-ticket has all 17 fields in template order. The umbrella has the package line, path class and depends-on.
- PENDING LEAD: 16 items, of which item 2 is WITHDRAWN and item 4 is REPLACED by 15; new items 11-16 (6).
- Store Protocol: 38 (P4d) + 3 = 41, UNVERIFIED until re-counted on the merged head.
- Forbidden content scan of the ticket (model ids, home or studio paths, address-like text, key-like strings): no hits. "Bedrock" and "Slack" appear only as names of existing modules and channel backends in this repository.
- Other tickets touched: none. Note: `git status` shows `tickets/P5b1.md` modified by another agent in the same worktree; my commit is path-limited and does not include it.
