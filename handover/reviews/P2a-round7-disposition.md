# P2a round 7: disposition of every finding (ticket revision 9)

Date: 2026-11-05 evening UTC (2026-11-06 early morning IST; IST = UTC+5:30). Author: Sonnet sub-agent applying `reviews/P2a-round7-resolve.md` (text only; no code, no suite run, no commit). Ticket: `tickets/P2a.md`, revision 9. "Field N" = the numbered field of the ticket (1 to 17). Evidence cited, not re-run: `evidence/P2a-round7-probes.md` (probes P1, P2, P3). Every ticket claim about the database that is not one of those three probes is marked UNVERIFIED in the ticket's UNVERIFIED list.

Status words: applied (as the resolve says); applied-narrowed (the resolve itself narrowed it); applied-deviation (applied with a difference from the resolve text, recorded below); declined (the resolve says DECLINE, nothing changed in the ticket for that finding); contested (I disagree with the resolve and changed nothing: none).

| Id | Status | Ticket location |
|---|---|---|
| ADV-R7-1 (reset names a set by version and count) | applied | Field 7 `Limits.reset`, store protocol, CLI flags `--expect-version`/`--expect-open`; field 11 reset function and rationale; S31 cases b2, b3, k; S32; mut-R18 to R20, ST19 to ST22, L43 to L46 |
| ADV-R7-2 (cap on open stop requests) | applied | Field 11 "The cap on open stop requests" and livelock runbook step; S29 cases 8 to 11; `limits.max_open_stop_requests`; mut-F13 to F16, K6; v1.1 row "Row limit" withdrawn; PENDING LEAD 32 |
| ADV-R7-3 + COR-R7-2 (dry run waits for the lock; probe P1) | applied (by a cut) | Field 11 "Probe" (catalog only; outcomes OK, FAILED, INCONCLUSIVE; one retry at start-up); S38 catalog-at-once check; mut-P22 to P24; v1.1 row "Dry-run proof"; mut-P7, P12 removed |
| ADV-R7-4 (false "no lock" claim; probe P2) | applied-deviation | Field 11 "What the stop can and cannot wait on"; field 7 `limits.migrate_lock_timeout_ms`; S30 lock table; S33 case 2; mut-G45, K7. Deviation: `lock_timeout` set once with `set_config(..., true)` as the first `migrate` statement, not `SET LOCAL` before each statement |
| ADV-R7-5 (P4d names) | applied | Field 3 couplings; field 9 item (q) (P4d Kill-switch read bullet, rows b17 and w8a, v1.1 short-connection row); UNVERIFIED list (names to confirm before P4d revision 9 merges) |
| ADV-R7-6 (cuts 1, 3, 5; keep 2; pending 4) | applied (cuts 1, 3, 5); kept (2); pending lead (4) | Cut 1: field 7 tables, field 11 guard trigger (literal group, `migrate` requires `reset_role`), mut-G5/G24/G25 removed, mut-G46, G47; cut 3: `typed_by` removed from `kill_switch_resets`, mut-R13 removed; cut 5: breakglass login, `reset_breakglass`, `session_identity`, group `SELECT` on label table removed, mut-L7, P21 removed; kept (2): ON-then-OFF pre-step and `kill_switch."on"` as second ON source (field 11 DBA recipe); (4) reconciliation kept pending PENDING LEAD 33. Seven v1.1 rows added (cuts 1, 3, 5, dry run, group-member label check, conditional reconciliation) |
| ADV-R7-7 (one pytest id per mutant; G7 killer) | applied | Field 13 (every mutant row ends `=> <pytest id>`; planned names, UNVERIFIED); G7 killer is the duplicate primary key; [catalog] rows G12, G39, F9, R8 counted apart |
| ADV-R7-8 (typed name for request-only stop) | declined | No ticket change for this finding. Reason as in the resolve: the link to who stopped is `cleared_by` on each cleared request (one query); no new column. The ticket's DBA recipe note says so |
| ADV-R7-9 (cluster-wide connection exhaustion) | applied-narrowed | Field 11 runbook sentence; S34 covers the per-role limit only; UNVERIFIED list names `superuser_reserved_connections` |
| COR-R7-1 (`KillSwitch` vs table columns test) | applied | Field 7 `StopState(KillSwitch)` with `open_requests`; `KillSwitch` gains `version` only (`tests/test_p2_postgres.py:61-64`) |
| COR-R7-3 (sequence grant shape) | applied-deviation | Field 7 `Grant("sequence", "")`; field 9 item (n) (fix to `test_k2_migrations.py:219-227`). Deviation: the resolve's alternative (`USAGE` granted to nobody) does not exist in this code (`_apply_grants` would grant it to the runtime) and omitting the entry is refused by `check_grants`; only the empty entry works |
| COR-R7-4 (`tick_state` use) | applied | Field 11 "Probe": step `stop_guard_probe` uses existing `tick_state` columns, no new column; the framework sets `last_ok_at` and `last_error` |
| COR-R7-5 (PENDING LEAD 26, 27 decided) | applied | Open points 26 and 27 marked DECIDED by order 8(2); header cites it |
| COR-R7-6 (casts, probe P3) | applied | Field 7 store protocol (`%s::bigint`, `%s::int`); range checks raise `ValueError` before any audit row; S42; mut-ST20, ST21, L46 |
| COR-R7-7 (brace escape) | applied | Field 11 function text uses `{{ }}`; test of final text against a literal (field 12 tests) |
| COR-R7-8 (PENDING LEAD 31 lists all ten) | applied | Open point 31 restated, ten deviations numbered; count printed in the change list |

## Counts (rows and ids separately)

- Rows in the table above: 16. Ids covered: 17 (ADV-R7-1 to ADV-R7-9 = 9, COR-R7-1 to COR-R7-8 = 8; the ids ADV-R7-3 and COR-R7-2 share one row, so 17 ids - 1 = 16 rows). Check: ADV rows 9 (the shared row counted once) + COR rows 7 (COR-R7-1, 3, 4, 5, 6, 7, 8) = 16.
- By status: applied 11 (ADV-R7-1, 2, 5, 7; COR-R7-1, 4, 5, 6, 7, 8; and ADV-R7-3 with COR-R7-2 by a cut, which I count as applied); applied-deviation 2 (ADV-R7-4, COR-R7-3); applied-narrowed 1 (ADV-R7-9); applied with cuts and a kept item 1 (ADV-R7-6); declined 1 (ADV-R7-8); contested 0. 11 + 2 + 1 + 1 + 1 = 16.
- Mutants: 159 - 8 removed + 23 new = 174 (G 44, F 16, R 19, ST 22, P 21, L 45, K 7; 44 + 16 + 19 + 22 + 21 + 45 + 7 = 174). [catalog] rows 4, behaviour killers 170. If PENDING LEAD 33 is accepted (P10, P11, P18 go): 171 and 167.
- `migrate(` call sites that need `reset_role`: 26 (1 + 5 + 11 + 2 + 2 + 2 + 1 + 1 + 1 = 26, by grep; per-file split in field 9 item (r)). `Limits(` sites: 9 (7 test + 2 src).
- Equivalent rows by reading: 6 (5 earlier + 1 new).
- SQL steps: S29 to S42 = 14.
- New PENDING LEAD items: 32 (cap and lock timeout defaults), 33 (the cuts, and a recommendation to also cut reconciliation).

## My deviations from the resolve text (also in the ticket change list)

1. `Grant("sequence", "")` only (COR-R7-3), reason above.
2. The resolve says the CLI and tests already pass `reset_role`. They do not: 26 `migrate(` sites, none passes it; the CLI has no `--reset-role` flag. So `reset_role` becomes required together with a list of sites to change (field 9 item (r), mut-G47).
3. No new `tick_state` column (COR-R7-4).
4. `lock_timeout` once per `migrate` transaction via `set_config(..., true)` (ADV-R7-4).
5. Version and count both required on every reset; out-of-range raises `ValueError` before any audit row.
6. Mutant total recounted by me (174), since the resolve left the recount to me.

## Disagreements and things I corrected in revision 8 (disclosed)

- Findings I disagree with: none strongly. I carry one doubt: ADV-R7-8 is declined by the resolve and I applied that; a reader who wants the typed name for a request-only stop has no record of it in the database (the audit row still has it).
- Rev 8 errors fixed: the count token did not identify stops seen across resets; "no lock another caller can wait on" was false (P2); "privilege check before the lock" for the dry run was false (P1); "harmless" and the rejection of a row cap were wrong; "bible files absent" was wrong (`handover/bible/RULES.md` exists; I found rule heads by grep only and did not read it in full); PENDING LEAD 31 listed six of the ten deviations.

## Not verified by me

All database behaviour except probes P1 to P3. Every pytest id in field 13 is a planned name. The 26-site and 9-site call counts were found by grep in this session and not re-run after the last edit. No tests, no linter, no suite were run (brief rule). Core code at `ce70eb5` was only read.
