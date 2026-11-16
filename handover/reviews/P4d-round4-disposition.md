# P4d round 4 disposition (ticket revision 6)

Ticket: `handover/tickets/P4d.md` revision 6. Inputs: `P4d-round4-resolve.md`, `P4d-round4-adversarial.md` (A1-A16), `P4d-round4-correctness.md` (C1-C14), LEAD-ORDERS order 7, `handover/evidence/model-probe.md`. Author: Sonnet 5.5 (set by the lead). Nothing was run against Postgres by me; the lead's PG 16.15 run is used where named. Duplicates: A1 = C2, A4 = C1, A2 = C3.
Decisions: applied / contested / declined. "where" names the ticket section.

| id | decision | where in the ticket |
|---|---|---|
| A1 + C2 | applied | a2-i Interface ("Cost producers": `round_cost_up`, ROUND_UP at 8 decimals in `llm/common.py:166-169`, `llm/fake.py:50-53`, `k1b/loop.py:119-122`), a2-i Files, Tests (producer rows a-d, expected `0.00009263`), mutants i10; header hot-file order (P4d-a2-i before P4a); Verified facts (producer cites); PENDING LEAD 13. Note: `k1b/loop.py` feeds `budget.charge`, no store call found there (UNVERIFIED path to the store); rounded anyway so the three agree. |
| A2 + C3 | applied | Rules stated once (retry: `on_retry` hook); a2-ii Tests (A2 zero-retry plus `pg_stat_database.deadlocks`), mutant w12; b B4(v) zero retries, B4(vii) deterministic lock-order row (`NOWAIT` on day and month rows while an admin holds the run row), mutant b15 kill column names both. The `deadlocks` statistic lag is UNVERIFIED, so the hook is the primary assertion. |
| A3 | applied | b Interface (sweep: `MemoryStore(*, clock=None, _checkpoint=None)`, aware UTC wall clock, default `models.now`, no monotonic clock); precedence (5); b Tests B7; a1 (`utc_today(store)`, fake clock in fixtures). |
| A4 + C1 | applied (cut) | a2-i: 28-digit row, `Context(prec=100)` and mutant i7 removed; ceiling kept; ce70eb5-only fail-before evidence kept, not a permanent test; Verified facts (28-digit note); v1.1 row. |
| A5 | applied | PENDING LEAD 12 (`expired` is not terminal, with the reason). |
| A6 | applied | b precedence (3), SQL rule 1 (`SELECT agent_id FROM runs`), B1 other-agent row, mutant b25. |
| A7 | applied | b `reserve_spend` interface (ceiling before booking), SQL rule 1 (ceiling condition), B1 ceiling rows both directions, precedence (6), mutant b26; a2-i ceiling text. |
| A8 | applied | Rules stated once (retry: `str(ms)`, confirmed 42883 on int in the PG 16.15 run), Verified facts, mutant w8. |
| A9 + C12 | applied, narrowed; separate-connection idea contested as out of scope | Rules stated once (every wrapped write is a transaction with timeouts first; `statement_timeout` from the remaining budget; back-off outside the lock); a2-ii A2b (blockers on `add_spend`, `record_decision`, `transition`, `set_kill_switch`; retried call within budget; sleep not under the lock); v1.1 row for the separate short connection (trigger: stop delayed past `call_budget_ms`). Evidence for C12: the connection is autocommit (`postgres.py:146`), only `:359` and `:419` open a transaction. |
| A10 | applied | b Security negative tests (trigger matrix: 16 pairs, 40 column cases, 4 field rules); mutant b14 one per forbidden edge. |
| A11 | applied | b B3 (`CounterDamaged` Postgres-only on `POSTGRES_ONLY_BY_DESIGN`; memory seeded-dict row kills b11), b12 deterministic through `_checkpoint`; ensure-rows position claim dropped (Rules stated once). |
| A12 | applied | a1 session-end check (fails under the fail rule when xdist is seen; unit test; real xdist UNVERIFIED). |
| A13 | applied | a2-i `check_cap` = `check_usd(max_decimals=8)`; edge rows (7-decimal accepted, 9-decimal refused), mutant i11; b B1 cap rows; PENDING LEAD 14 (P4b1 rounds down). |
| A14 | applied | b SQL rule 1 wording ("takes the row lock only when it matches", `current` best effort). |
| A15 | applied | b precedence (4) (content check before status), B2 rows, mutant b27. |
| A16 | declined | v1.1 row (trigger: more than 1000 open rows; P4b2 owns reconcile); no Protocol change. |
| C4 | applied | a2-ii wrapper unit test with `drv.make_error("23503")` (new `pg_driver` operation) and mutant w10 re-pointed; b B1 backstop row (pre-check patched out), mutant b24 re-pointed. Checked: no `REFERENCES` in migrations 0001-0005 (the reviewer's count; the table DDL I read has none). |
| C5 | applied | c Interface (expected caller list by file, exact-set test), c Tests, mutant c3; a1 Files (new `test_pg_driver.py`). |
| C6 | applied | cite `postgres.py:444-451` (checked: `get_kill_switch` is at those lines) at both places. |
| C7 | applied | b Done: `P3a.md` line 100, PENDING LEAD item 6, cited by item (checked: line 100 is item 6; line 99 is not). |
| C8 | applied | a1 Interface (pair: Postgres-only `a._db is not b._db`, memory `a is b`), a2-ii A2 test, mutant a1-4. |
| C9 | applied | a2-i Tests (39 inputs, counted; 29/40/1000-decimal rows; `limit`/`older_than_s` rows live in b B6); `add_spend` calls `check_day` (stated, i9). |
| C10 | applied | Rules stated once (fail-before: assertion or unexpected exception; driver error caught and typed); a2-ii FAIL-BEFORE. |
| C11 | applied | b `meta`: UTF-8 bytes of `json.dumps(meta, ensure_ascii=False, separators=(", ", ": "))`, same check in both stores; boundary row. JSONB text length versus this rule is UNVERIFIED. |
| C13 | applied | a2-ii caller analysis (checked: `add_tool_call` is inside `except Exception` at `agent_loop.py:497-501`; `save_plan` at `:667` is not guarded), NUL tool-output row; PENDING LEAD 15 for the `save_plan` gap. |
| C14 | applied | header (money queue wording as `P4c.md` line 11); Rules stated once (a1/b evidence is the `evidence-p4d.md` row of plan-v3 line 179). |

Lead-ordered additions (not findings): PENDING LEAD 10 (settle above reserved, marked `[PL10]` at 9 places; DDL CHECK relaxed, SQL rule 2, B3 rows, mutant b28), 11 (maintenance identity), 12, 13, 14, 15; v1.1 table (3 rows).

Contested: none of the 30 findings is wrong. Disagreements and open points are in the author's final message: (1) P4a-2's "`cost_usd` never rounds" conflicts with A1/C2 (item 13); (2) the rounding at `k1b/loop.py` may not reach the store.
Counts: 30 finding ids in 26 rows (A1+C2, A2+C3, A4+C1 and A9+C12 are merged): 25 rows applied (A9 narrowed), 1 declined (A16), 0 contested.
