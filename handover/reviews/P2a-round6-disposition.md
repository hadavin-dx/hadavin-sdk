# P2a round 6: disposition of every finding (ticket revision 8)

Date: 2026-11-05 evening UTC (about 2026-11-06 00:xx IST). Author: Sonnet sub-agent applying `reviews/P2a-round6-resolve.md`. Ticket: `tickets/P2a.md`, revision 8. "Field N" = the numbered field of the ticket (1 to 17); "change list" = its last section. No SQL, suite or code was run (brief rules). Where the resolve gave only an id and I summarise it, the summary is my reading; the resolve file is the source.

Status words: applied (as the resolve says); applied-narrowed (the resolve itself narrowed it); applied-deviation (applied, with a difference from the resolve text that is recorded below and in PENDING LEAD 31).

| Id | Status | Ticket location |
|---|---|---|
| ADV-R6-1 (a compromised runtime can hold the stop's row lock; timeouts are USERSET) | applied | Field 7 (tables, view, functions), field 11 (why no lock; fallback sentence), S29-S34 in field 12, mutants G41-G44, F1-F12, R1-R17 |
| ADV-R6-2 (probe reads what the runtime cannot) | applied-narrowed | Field 11 "Probe"; breakglass check moves to `limits check` (field 7 CLI); mut-P21 |
| ADV-R6-3 (trigger regex branch; rollback) | applied | Field 11 guard trigger text (branch removed); field 17 recipe (3 steps); S37 |
| ADV-R6-4 = COR-C6-6 (merged: `key_id` validation, masking never raises) | applied-deviation (no separate start-up label check) | Field 7 "Limits" and "Masking"; field 12 property test; mut-L32, L33, L34 |
| ADV-R6-5 (cut-over order, half-migrated state, DBA stop) | applied | Field 11 "Cut-over order", "DBA emergency recipe"; field 7 exit 9; S38; mut-G37, G38, ST9, L41 |
| ADV-R6-6 (mutant plan not re-derived) | applied | Field 13 (159 with arithmetic and equivalents list); fields 14 and 16 say 159 |
| ADV-R6-7 (runtime can use up all connections) | applied-deviation (credential field name) | Field 11 identities and role defaults; field 7 CLI stop; S34; mut-G34, G19, L39, L24 |
| ADV-R6-8 (no model SQL for the new design) | applied | Field 12 S29-S40 with "must show"; field 14 item 5 |
| ADV-R6-9 (timeout settings as control) | applied-narrowed | Field 7 Config, field 11 "Role-level defaults" and probe (`rolconnlimit`, `stop_guard_probe_ok_ts`); no `pg_db_role_setting` check |
| ADV-R6-10 (EXECUTE per function, per-action table) | applied | Field 11 identities table; mut-F4 to F7, R10 to R12 |
| ADV-R6-11 (custom error codes) | applied-deviation (HD002 meaning) | Field 7 "Custom SQLSTATE codes"; store mapping; mut-ST4 to ST9 |
| ADV-R6-12 (stop must confirm `on`) | applied | Field 7 `Limits.stop` (`StopNotConfirmed`); mut-L31, ST11 |
| ADV-R6-13 (pooler hides the person) | applied-narrowed | Field 11 secret-store paragraph (one runbook sentence; no probe) |
| ADV-R6-14 (stale relays to other tickets) | applied | Field 3 couplings, by item name; new coupling P4d-b `reserve_spend` |
| ADV-R6-15 ("verified" vs "read"; PR50 counts) | applied | Heads; field 5; field 10; UNVERIFIED list |
| COR-C6-1 (`pilot_cfg` and secret fakes need the label key and stop ref) | applied | Field 9 UPDATE (m), (p) |
| COR-C6-2 (full list of existing tests to update) | applied | Field 9 UPDATE (a) to (p) |
| COR-C6-3 (`test_k5_fixes2._folder` and `check_grants`) | applied | Field 9 UPDATE (o); field 3 P4d coupling |
| COR-C6-4 (hard-coded migration list at `test_p2_postgres.py:290`) | applied | Field 9 UPDATE (i) |
| COR-C6-5 (non-superuser migrator fixture) | applied | Field 9 "Fixtures"; S35 |
| COR-C6-7 (narrow return row, not `SETOF kill_switch`) | applied | Field 7 functions text; field 11 function SQL |
| COR-C6-8 (`cli.kill_switch` signature) | applied | Field 7 CLI |
| COR-C6-9 (wrong cites) | applied | Fields 7, 9, 10; change list "Corrections of my own" |
| COR-C6-10 (wrong reason for `_secret_name` suffix) | applied | Field 7 "Label key wiring"; field 11 credentials |
| COR-C6-11 (`ALTER ROLE ... IN DATABASE`) | applied | Field 11 "Role-level defaults"; mut-G35 |
| COR-C6-12 (reconciliation false alarm) | applied-narrowed | Field 11 probe (`reconcile_grace_s` 120); field 7 Config; mut-P18; test (h) |
| COR-C6-13 (stop never refused for key problems) | applied | Field 7 "Limits" (nokey label); mut-L35, L36, K4 |
| COR-C6-14 (memory store label rule) | applied | Field 7 store; field 12 contract row; mut-ST15 |
| COR-C6-15 (`lock_timeout` on the read helper) | applied-deviation (recorded as moot: reads never wait) | v1.1 table last row; change list |
| COR-C6-16 (S9 heading vs body; `set_config(false)`) | applied | Field 11 evidence note; S39 |
| COR-C6-17 (core half of "no `SwitchChanged`") | applied | Field 5 last bullet (core half VERIFIED by search) |
| COR-C6-18 (17 numbered fields) | applied | Ticket headings 1 to 17 |
| COR-C6-19 (eight removed rows inside the 82) | applied | Field 13 last paragraphs (confirmed by reading commit `60fedf6`) |

Counts. Ids 34 (ADV 15, COR 19); merged pair 1 (ADV-R6-4 = COR-C6-6); table rows 33. Applied 25, applied-narrowed 4 (ADV-R6-2, R6-9, R6-13, COR-C6-12), applied-deviation 4 (ADV-R6-4/COR-C6-6, ADV-R6-7, ADV-R6-11, COR-C6-15) = 33. Of the resolve's own counts, "4 narrowed and 1 recorded deviation (COR-C6-15)" match the table; the other three deviation tags are MY deviations, listed next. Contested 0. Declined 0. Escalated 0. New PENDING LEAD items from the resolve: 28, 29, 30; mine: 31.

## My deviations from the resolve text (the lead should look at each)

1. `store.stop_credential_ref`, not `store.stop_secret_name`: the `_secret_name` suffix makes `platform_secrets.secret_names` collect it, so the runtime would read the stopper credential.
2. `BIGSERIAL` for the request table id, not `generated always as identity`: `migrate._UNREAD` refuses `AS IDENTITY` (`migrate.py:87-90`). The sequence gets a `GRANTS` entry with no rights.
3. New view `kill_switch_state`; runtime and stop roles read only the view and hold no table right (resolve: "nothing on the table").
4. The reset function does not repeat the group and label checks; the trigger makes them (a copy would make every single-removal mutant equivalent). The reset group's column UPDATE grants are dropped.
5. HD002 means "guard set up wrongly (group unset or role missing)", not "grant lost" (a lost grant is PostgreSQL 42501 and cannot carry a custom code).
6. `KillSwitch` and the function row carry an extra `open_requests` column beyond the resolve's narrow row (needed for the count token).
7. No separate start-up check of a label built from `key_id`: validation plus the property test already cover it; a separate check would be dead code.
8. New CLI exit codes 8 (stop done, audit not written), 9 (not migrated), 10 (`limits check` problems).
9. Runtime `CONNECTION LIMIT` default 20 is my number, UNVERIFIED against the real pool.
10. Rollback recipe gains a step the resolve did not state: fold open stop requests into `kill_switch."on"`, else an old release reads OFF while stops are open (fail open).

## Still UNVERIFIED (nothing was run)

All database claims for the new design (S29-S40 planned); PostgreSQL 17.10 behaviour; that a role with only view `SELECT` is denied every lock mode; that an in-progress INSERT stays invisible to the reset's UPDATE; that `migrate()`'s Python steps share the one transaction; the correctness reviewer's claim about `P4b1.md` near line 190; the PR50 counts; exact names of P4d's helpers until P4d merges.
