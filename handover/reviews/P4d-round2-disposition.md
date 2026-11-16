# P4d ticket, round 2: disposition of all 34 findings

Applied to `handover/tickets/P4d.md` (revision 4), 2026-11-05 (UTC). Source: `handover/reviews/P4d-round2-resolve-report.md`; findings in `P4d-round2-adversarial.md` (A1-A17) and `P4d-round2-correctness.md` (C1-C17). Each claim was re-checked in code on ce70eb5 or by running Python in the project venv before editing. Nothing was run against Postgres (none available). Sub-tickets: a1 (harness), a2 (validators, write wrapper), b (money), c (guard); "Rules" = "Rules stated once"; "Facts" = "Verified facts".

Counts: FIXED 34, REJECTED 0, ESCALATED 0 findings (the positions that stay PENDING LEAD are listed at the end; they are choices inside fixed findings).

| Finding | Sev | Status | Section | One line |
|---|---|---|---|---|
| A1 | BLOCKER | FIXED | Rules "ONE total lock order"; b "Money SQL rules" 1; B4(v); mutant b15 | One total order stated once for all methods plus `add_spend`/`add_cost`: reservation, ensure-counter-rows, run, day, month; reserve rewritten to it; deadlock stress with `run_id`; `which` reported in the same order; mutant inverts the order. |
| A2 | MAJOR | FIXED | a2 `check_usd`; edge table; mutant a5 | Verified by running: `normalize()` of a 31-decimal value has exponent 0. Scale is read from `as_tuple()` with hand-stripped zeros and a local `Context(prec=100)`; rows with 29, 40 and 1000 digits; mutant "default-context normalize". |
| A3 | MAJOR | FIXED | Rules "Retry and timeout"; a2 A2b; b B4; mutant a9, b18 | `SET LOCAL lock_timeout` from new setting `lock_timeout_ms`; `55P03` becomes `StoreBusy`; `is_connectivity_error` false for 55P03 and 57014 (both are `OperationalError` subclasses, run); never-released admin lock test. |
| A4 | MAJOR | FIXED | b "Money SQL rules" 1; B4; mutant b17 | Kill switch read with `FOR KEY SHARE`; a test that `set_kill_switch` completes while a reserve is blocked. |
| A5 | MAJOR | FIXED | b Interface (`expired`, `list_open_reservations`, `SpendOutcome`, `MIN_SWEEP_AGE_S`) | Terminal status `expired` in CHECK, trigger and model; one downward correction by a late settle; release from expired; listing by run/agent; sweep floor 30 s; `applied` flag; rollback loop. |
| A6 | MAJOR | FIXED | a1 `require_backend` and session-end check | Check runs only when a store test was selected, counts only skips whose reason starts `require_backend:`, pairs rows per backend with a named Postgres-only list; no memory skip; `pytest -m perf` stays silent. |
| A7 | MAJOR | FIXED | Header "Order inside P4d"; each sub-ticket "Depends on" | Strict order a1, a2, b, c; "parallel" claim removed; shared files named. |
| A8 | MAJOR | FIXED | a1 `pg_driver` (`connect_runtime`); a2 Security; b Security; mutant b14 | Runtime-role connection helper; every negative test first asserts `current_user`, `rolsuper = false`, membership, then exact SQLSTATE; trigger RAISE (P0001, message) asserted apart from CHECK (23514); mutant "GRANT DELETE given". |
| A9 | MAJOR | FIXED | Header; a1 vs a2 split; Rules "Retry" | P4d-a split into a1 (harness) and a2 (validators, wrapper, fixes; counts as money PR); retry only on 40001 and 40P01, never 40003, never for keyless add-style writes. |
| A10 | MINOR | FIXED | a2 `check_int`; edge table | `check_int(type(x) is int, bounds)` for `limit` (1-1000) and `older_than_s` (30-10**7); rows `True`, 0, -1, 10**30. |
| A11 | MINOR | FIXED | a2 `check_text`; hostile values | `check_text` runs over `model_dump()` of every model, every str field and key; NUL in `reason_code` row. |
| A12 | MINOR | FIXED | b DDL | Grammar CHECKs on `agent_id` and `run_id`, `day` bounds, `REFERENCES runs`. |
| A13 | MINOR | FIXED | b Security (honest limit) | Runtime can UPDATE `spend`, `spend_month`, `runs` (`migrate.py:53-54`): counters are the trust boundary; caps are caller-supplied (P4b1); triggers protect the ledger only. |
| A14 | MINOR | FIXED | b DDL (BEFORE INSERT trigger) | Insert trigger forces an open row; owner/superuser/replica-role stated outside the model. |
| A15 | MINOR | FIXED | c Interface and tests; mutant c5 | Guard flags string constants "psycopg", alias imports, `pg_driver(` calls; states it is a lint, not a boundary. |
| A16 | MINOR | FIXED | a1 recording proxy, property test | Proxy counts only calls inside test bodies; seeded `random.Random` model-based test against a reference ledger (no new dependency; hypothesis not used); closed-port test accepts one outcome only. |
| A17 | MINOR | FIXED | b B7, B4 process rows | Injected clock (memory) and owner-only fixture INSERT of an old `created_at` (Postgres) instead of sleep; SIGKILL test releases the admin lock and polls `pg_stat_activity` with a timeout. |
| C1 | MAJOR | FIXED | same as A1 | Same lock-order fix; ensure-rows step kept before the run lock with the reason written; `which` order stated. |
| C2 | MAJOR | FIXED | same as A6 | Session-end check scoped to `require_backend:` skips and to runs that selected a store test (`test_llm.py:95` skip and `-m perf` at `ci.yml:94` verified). |
| C3 | MAJOR | FIXED | same as A7 | Sequence and per-sub-ticket Depends-on; shared files named. |
| C4 | MAJOR | FIXED | a1 `pg_driver` created in a1; a2/b use only it | a, b tests never import psycopg; c only converts the old files and adds the guard. |
| C5 | MAJOR | FIXED | "Fail-before wording"; a1/a2 FAIL-BEFORE; b "FAIL-BEFORE honesty" | Every B row labelled "new feature; killed by mutants"; B8(d) named as the real assertion fail-before; tests written against the ce70eb5 API; CI-without-DSN test catches `Skipped`/`Failed`. |
| C6 | MINOR | FIXED | Rules "Retry" | Exact SQLSTATE 40001 and 40P01 only; `StatementCompletionUnknown` is 40003 (run). |
| C7 | MINOR | FIXED | same as A11 | `check_text` over every string field. |
| C8 | MINOR | FIXED | all Evidence commands | `uv run --group scan bandit -q -r src demos -ll` (`pyproject.toml:52,54`). |
| C9 | MINOR | FIXED | Facts | `test_p7_store.py` has 1 importorskip of psycopg (`:11`; `:106` is boto3), grep confirmed. |
| C10 | MINOR | FIXED | Facts; a1 Security | Reworded: no password-bearing DSN; literals exist in `ci.yml:86, 93` and about ten tests. |
| C11 | MINOR | FIXED | a2 "Regression pins" | Round trips, duplicate rows, A3 atomicity, A2 races on existing methods, Postgres list order, `build()` mapping and grants listed as pins. |
| C12 | MINOR | FIXED | b Interface | Four writes (reserve, settle, release, sweep) wrapped; two reads (get, list) not wrapped; Store grows 32 to 38. |
| C13 | MINOR | FIXED | a2 A4 (one test per caller) | Tests for `audit/chain.py:531-541`, `cli.py:368`, `runtime/tick.py:342,362` pin the outcome for a `40P01` fake; imprecise chain message noted, `is_transient_error` helper left PENDING LEAD. |
| C14 | MINOR | FIXED | b B8(c) | Mechanism named: `test_k2_migrations.py:387-394` (monkeypatch `_migration_files` to drop the newest file, stub `check_grants`) with its limit; catalog check covers ALTER-only migrations only (`:357-371`). |
| C15 | MINOR | FIXED | b settle interface | Validation runs first on every settle/release call, including on closed reservations. |
| C16 | MINOR | FIXED | structure; c header | Template order inside each sub-ticket; own Depends-on, Reviewers, Done; A13 wording already corrected by A14(2) (P4d-c is the guard). |
| C17 | MINOR | FIXED | b "Kill switch" line | Only `reserve_spend` reads the kill switch; settle, release, sweep and reads ignore it; coupling with P2a's kill-switch storage stated. |

## Still PENDING LEAD (positions are written in the ticket)
1. Amendment to F7: exempt the 8 named `tests/demo_askdata/` files, dated expiring entry (`review_by` 2026-12-31 proposed).
2. Which identity may run the sweep (P4b2 fourth role; recommended).
3. Run counter `runs.cost_usd`; callers stop pairing `limits.charge` with `store.add_cost` for reserved calls; all spend through reserve (P4b1/P4c wiring).
4. Defaults and shapes: `lock_timeout_ms` 5000, `MIN_SWEEP_AGE_S` 30, `StoreBusy` as a `StoreUnavailable` subclass, an `is_transient_error` helper, `pg_driver` with five names, review tier of a1 and c, deployed agent ids vs the id grammar, code default `store` is `memory` (`table.py:586`), billing-record tags and post-booking totals in the return value.

UNVERIFIED: all Postgres behaviour (nothing run); PR #48 signatures; the `PENDING` mechanism shape; the mutation runner; P2a's final kill-switch storage; whether `check_grants`/`_scan` accept the inline `REFERENCES` and `CHECK` text.
