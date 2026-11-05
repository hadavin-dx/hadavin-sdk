# P4d round 3 resolve report (egm:egm-resolve, Opus 5.5)

Status: resolved (categorised; ticket NOT edited here; the author rewrites revision 5)
Target: `handover/tickets/P4d.md` rev 4 (b215b50). Inputs: `P4d-round3-adversarial.md` (A1-A19), `P4d-round3-correctness.md` (C1-C21).
Gate: the skill's "wait for the user" step is skipped: standing rule is auto mode, lead answers by recommended answer. Nothing was contested or escalated to the owner.
Facts checked by me: PostgreSQL requires UPDATE privilege on at least one column for any `FOR UPDATE/NO KEY UPDATE/SHARE/KEY SHARE` lock (SELECT docs, "Locking Clause"): A1 and C13 are real. psycopg `ForeignKeyViolation` is an `IntegrityError` (C5): real.

| id(s) | category | decision for revision 5 |
|---|---|---|
| A1 + C13 | PROPOSE FIX (blocker) | Plain `SELECT "on" FROM kill_switch WHERE id=1` in the same transaction; one private helper shared by `get_kill_switch` and `reserve_spend`; state the window (a reserve that read "off" may commit after a stop commits, at most one transaction); drop the FOR KEY SHARE claims and mutant b17; contract row: reserve as a role with SELECT only on kill_switch. |
| A2 | PROPOSE FIX | Session-end checks (1)(2) active only when `HADAVIN_REQUIRE_PG` or `CI` is set; say how `-k memory`, `--lf`, xdist behave; unit-test it. |
| A3 + C5 | PROPOSE FIX | Pre-check the run (SELECT ... on `runs`, raise `NotFound`) before the INSERT; also map 23503 to `NotFound` as a backstop; one precedence table (validation, replay, kill switch, run, caps) for both stores; memory matches; B row. |
| A4 | PROPOSE FIX | Per-call total budget (`statement_timeout` + deadline), default `lock_timeout` about 1 s, backoff with jitter, plain statement of the in-process lock wait; B4 stop-test from a second handle only; no change to the one-connection design in this ticket. |
| A5 | PROPOSE FIX | Keyword-only caps, no defaults (`None` explicit); `TypeError` test; mutant. |
| A6 | PROPOSE FIX | New reservation requires `abs(day - UTC database date) <= 1`, replay keeps stored day; test incl. midnight. |
| A7 | PROPOSE FIX | Distinct `CounterDamaged` error (meter alerts) plus a documented audited maintenance close path; drift-detection read; invariant note (`add_spend` mixed in, ties to C15). |
| A8 | PROPOSE FIX | Split a2 into a2-i (validators, `add_spend`/`add_cost` refusal, money edge table) and a2-ii (write wrapper, retry, StoreBusy, non-money fixes). Five sub-PRs total; header says so (ties to C8). |
| A9 | PROPOSE FIX | `pg_driver` exposes neutral operations (`execute`, `ident`, `sqlstate`, `is_unique_violation`), call sites converted; else delete the "replaceable" claim. Choose the neutral operations. |
| A10 + C16 | PROPOSE FIX | Add P2a to hot-file lists; order P2a-1a after P4d-b with the shared helper from A1 as the only coupling; fix `table.py` attribution; answer P3a line 99 requests (layer 2 run logged in b's Done; `lock_timeout` decision for `migrate()`). |
| A11 | PROPOSE FIX | Old methods `max_decimals=8`; memory counter arithmetic in `Context(prec=100)` or integers; counter ceiling; add `0E-1000`, `0E+5`, 28-digit boundary rows. |
| A12 | PROPOSE FIX | Assert granted count equals `floor(cap/amount)` and sum equals booked total; kill-after-commit row; `spawn`; worker reports `pg_backend_pid()`; admin connection for `pg_stat_activity`. |
| A13 | PROPOSE FIX (PENDING LEAD for the choice) | Recommend: optional keyword-only `meta` (bounded JSON column) and cap/total on `SpendCapExceeded` now, same migration. Mark PENDING LEAD; revision 5 writes it with the recommendation. |
| A14 + C6 | PROPOSE FIX | `StoreBusy` a separate class, not a `ConfigError`/`StoreUnavailable`; `is_connectivity_error` returns False for it; state base classes of `SpendCapExceeded`, `KillSwitchOn`, `ReservationConflict`; caller-test row. |
| A15 | PROPOSE FIX | Sweep needs no separate role; maintenance identity reserved for P4b2 pruning. |
| A16 + C3 + C4 | PROPOSE FIX | Insert trigger sets `created_at`; open-to-expired sets `settled_usd = reserved_usd` AND `closed_at`; release of expired sets `settled_usd = NULL` and `closed_at`; do not overwrite `closed_at` on expired-to-settled (keep `expired_at` or document); tests. |
| A17 + C7 | PROPOSE FIX | Substring/prefix matching stated; allow-list entries listed per file with reasons (guard file, `demo_askdata/test_imports.py`, `test_p7_tick.py`, `test_cuj.py`); expiry owner named. |
| A18 | PROPOSE FIX | Tie-break ordering, B7 counters row, B3 replay row, `set_config('lock_timeout', %s, true)`, independent integer-based month model, month/year boundary rows. |
| A19 | PROPOSE FIX (note) | Record retention need for P4b2/P3b/P7. |
| C1 | PROPOSE FIX | Add `test_k5_fixes2.py:260-309` to b's change list (include new migration in `_folder` or stub `check_grants`). |
| C2 | PROPOSE FIX | Add plan round-trip rows in a1. |
| C8 | PROPOSE FIX | PENDING LEAD item for the split (now five); P2a depends on all P4d sub-PRs. |
| C9-C12, C14, C15 | PROPOSE FIX | Text fixes as in the report (six new methods; ten fields; mandatory `check_day`/`check_id`; missing kill-switch row Postgres-only; precedence row; invariant includes `add_spend`). |
| C17-C21 | PROPOSE FIX | Template order; relabel regression pins; name symbol for fail-before; rollback command; correct cites. |

Counts: 40 findings (A1-A19, C1-C21); PROPOSE FIX 40 (some merged), CONTEST 0, ESCALATE 0, DECLINE 0. PENDING LEAD: A13 choice, sub-ticket split. Severity unchanged.
Model: Opus 5.5 (egm:egm-resolve).
