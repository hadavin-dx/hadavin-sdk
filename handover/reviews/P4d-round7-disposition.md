# P4d round 7 disposition (author answer to `P4d-round7-resolve.md`; ticket `handover/tickets/P4d.md` REVISION 9)

Written 2026-11-05 at about 19:49 UTC (2026-11-06 01:19 IST). Author: a Sonnet sub-agent; nothing in this file or in the ticket was run against Postgres. Text only.

## Read this first: failures, gaps and what is unverified

1. NOT RUN, ordered by the resolve before round 8: (a) release with a counter lowered below the reserved amount and with a deleted `spend_month` row; (b) the T4 two-holder timing, once as a test write (a2-ii) and once over `reserve_spend` (B4b); (c) `SET LOCAL lock_timeout` as the first statement of a migration file run by `migrate()` and a foreign-key creation waiting behind a held `runs` row; (d) the project-venv probe file `handover/evidence/P4d-venv-probe.md`. Every claim that needs them is marked UNVERIFIED in the ticket. The timings in T4 and B4b (450 ms and 900 ms release points, 500 ms budget) are my design, not measurements.
2. What I did run in this revision (plain `python3`, standard `decimal` module only, output not saved because the resolve forbids extra files): `Decimal("-0").quantize(1E-8, ROUND_UP)` prints `-0E-8` and `is_signed()` is true; a 29-significant-digit value `1.` + 27 zeros + `1` quantizes up to `1.00000001`, `+x` and `normalize()` change it (`1.000...` with 27 zeros, `1`); the 6-decimal round trip `x == x.quantize(1E-6)` accepts `0.0750000`, `999999.999999`, `1000000` and refuses `0.0000001`; digit counts (`10**9 x 10**12` has 22 digits, `10**24` has 25); and the kill sets of every rounding mode on the real rows a1-a8 (rows built from the ticket: `1231, 1234, 1236, 1239, 1235, 1230` tokens at the prices named there, `1` token at `1E-30`, price `0`). Result: DOWN dies on a1-a5 and a7; HALF_UP on a1, a2, a7; HALF_EVEN and HALF_DOWN on a1, a2, a5, a7; `ROUND_05UP` on a1-a5 and NOT on a7 (a7's last kept digit is 0, so it rounds away from zero and agrees with round-up); `ROUND_CEILING` never (equal to round-up for positives); `ROUND_FLOOR` as DOWN; 7 decimals dies on a1-a7; 9 decimals on a1-a5 and a7. These are the numbers in the ticket's table.
3. Not read by me as code this revision beyond what I list in the ticket: the whole of `agent_loop.py`, the existing tests that build a `Reply` or `Verdict` (which ones break: UNVERIFIED), the `pg_stat_activity` wait values, PG 17 behaviour.
4. Cross-ticket reads: P2a revision 9 (on disk, line 25 and the stop-view and short-connection items), P4a revision 6 (on disk; "Notes for P4d"), P3a revision 8 (on disk; P3a revision 9 is being written in parallel, so its final names may differ), P4b1, P4c, P6b1 line numbers as the resolve gave them. I cite by item name.

## Counts

- Rows of the resolve table: 18. Finding ids: 20 (ADV-R7-1 to 13 = 13; COR-C7-1 to 7 = 7). Two rows cover two ids each (ADV-R7-6 with COR-C7-4; ADV-R7-7 with COR-C7-6), so 18 rows = 20 ids - 2 merged.
- Status: applied 20, contested 0, declined 0. Of the applied: 18 rows as proposed; ADV-R7-9 and ADV-R7-13 applied in their narrowed form as the resolve says.
- New PENDING LEAD items: 3 (19, 20, 21). Item 18 is marked answered yes by LEAD-ORDERS order 8(2).
- Mutants after this revision (counted from the ticket tables by a script): a2-ii table 19 rows (w1-w7 = 7, w8a-f = 6, w9-w13 = 5, new w14 = 1); b table 43 rows (new: b11c, b11d, b18c, b28c, b29, b30 = 6 new, so 37 before); rounding table 10 rows (i10a-j, new i10i `ROUND_05UP` and i10j context); a2-i plan also new i15a, i15b (validators). The contract file runs 26 test functions x 2 backends = 52 cases (counted: `grep -c "^def test_" tests/contracts/test_store.py` = 26; two registered backends `memory` and `postgres`). Protocol methods 32 now, 38 after (6 new, counted in the ticket; `grep -c "    def "` in `protocol.py` printed 32).

## One row per finding id

| id | status | where in the ticket (section / bullet) | what was written |
|---|---|---|---|
| ADV-R7-1 | applied | "Rules stated once", bullet "No counter below zero"; P4d-b Interface (`CounterDamaged`, `release_spend`); P4d-b "Money SQL rules" 3 and 5; B3 "RELEASE GUARD" rows r1-r4; mutants b11c, b11d | Release gets the settle guard in the SQL `WHERE`; zero rows = `CounterDamaged`, full rollback, reservation as it was; memory checks before any change; PL21 (no table CHECK) and a v1.1 row; round-6 miss admitted |
| ADV-R7-2 | applied | "Verified facts" PG-rule bullet; "Rules stated once" bullet "Kill-switch read"; "Retry and timeout" (short connection); a2-ii A2b; "Tell the authors" P2a entry; v1.1 first row | View-only `SELECT`; stop is P2a's function plus short connection; two reasons for no locking clause; the SELECT-only-role test is the design pin (b17); v1.1 row withdrawn; A2b `set_kill_switch` rows moved to P2a (not kept for memory: memory has no row lock); derived-state read left to P2a-1 because the view does not exist at P4d merge |
| ADV-R7-3 | applied | P4d-c Interface (allow-list), Depends-on, Mutation plan c6, Evidence; P4d-b B8 bullet; P4d-a1 Files; "Tell the authors" P3a entry | P3a's three files on the allow-list (the numbers file only if it needs it: UNVERIFIED, exact-set test arbitrates); B8 and a1 reuse `tests/migration_schemas.py`, no second builder |
| ADV-R7-4 | applied | P4d-a2-i Interface, bullets "Cost producers" and "Files"; tests HELPER and VALIDATOR ROWS (h1, h2, v1-v4); mutants i12, i15a, i15b; Evidence (re-run list); header hot files; PL20 | Helper moves to `models.py`; `field_validator("cost_usd")` on `Reply` and `Verdict`; producers still call it; effects stated; honest limits (`model_copy`, assignment, `model_construct`) stated; NaN rows are regression pins (pydantic already refuses NaN) |
| ADV-R7-5 | applied | "Rules stated once", bullet "Retry and timeout" (THE BOUND); a2-ii wrapper bullet (`_run`); a2-ii A2b row (T4); mutant w14; P4d-b B4b(b), mutant b18c; v1.1 rows for `set_config` re-issue and `transaction_timeout` | `_run` checks a monotonic deadline before each statement; the bound is stated honestly (budget plus one statement's timeout, so at most twice the budget, plus back-offs); the resolve's `3 x (budget + one statement)` is NOT adopted because one budget covers all retries; same-handle wait bounded by the same figure; T4 with two holders and a note that one holder cannot show it |
| ADV-R7-6 | applied (merged with COR-C7-4) | P4d-a2-i Interface, bullet "Route price check" (decimals sentence replaced, arithmetic written out, overlap with P4a); tests "REAL FAIL-BEFORE rows" (7-decimal price); mutant i14 | At most 6 decimals via `x == x.quantize(1E-6)` after the bound check; ONE validator, owner P4d-a; the "not limited" sentence deleted |
| ADV-R7-7 | applied (merged with COR-C7-6) | "Verified facts" memory-lock bullet; P4d-b Money SQL rule 5; B4b(c); mutant b29 | `MemoryStore._lock` becomes `RLock` in P4d-b (moved from a2-ii: no killer there); lone-caller rows per new memory method on a fresh store and a daemon thread; the "no helper takes another lock" claim to be checked by grep (count UNVERIFIED) |
| ADV-R7-8 | applied | P4d-b B4b(a) | The (vii) rows use `lock_timeout_ms=60000` and `call_budget_ms=60000`; SQL-head strings are module constants |
| ADV-R7-9 | applied, narrowed | P4d-b Interface (`settle_spend` EXCESS BOUND), Money SQL rule 2, B3 "EXCESS BOUND" rows, mutant b28c; PL19; v1.1 row | `actual - reserved <= max(reserved, SETTLE_EXCESS_FLOOR_USD)`, constant in `defaults.py` (1 USD, UNVERIFIED); checked in Python after the claim, before any counter UPDATE; no per-agent accounting; PL16 paragraph states "limits one call, not repeated small excesses" |
| ADV-R7-10 | applied | Header "Hot files" bullet (migrate/store files: P4c-1, P4b1 removed; `config.py`: P4b2-b, P6b1; `defaults.py`; `models.py`); "Tell the authors" P4b1, P4b2, P4c, P6b1 entries | Orders re-read against the other tickets; P4b1 `:195` and `:248` named by item; line numbers are the resolve's, I re-read `P4b1.md:195,248,155`, `P4c.md:20,68-69`, `P6b1.md:111`: they match |
| ADV-R7-11 | applied | P4d-b Files, migration bullet (first statement `SET LOCAL lock_timeout = '10s'`, runbook sentence, text test); "Done" bullet; mutant b30; evidence run (c) | Weak reason replaced; P3a's guard allows exactly this `SET` (P3a revision 8, by item name; coupling stated) |
| ADV-R7-12 | applied | P4d-a2-i Evidence commands (the `P4d-venv-probe.md` list); header "READ FIRST" paragraph | Probe ordered with the exact value list; claims worded "run by me, output not kept" |
| ADV-R7-13 | applied, narrowed | P4d-a2-i tests (edge-table values; rounding table "all rows"); P4d-b Security bullet (day before `db_date`) | (a) i10f dies on every row a1-a8; (b) `1.` + zeros + `1` with 28/39/999 zeros (29, 40, 1000 significant digits), `0.000...1` removed; (c) one sentence, no code change |
| COR-C7-1 | applied | P4d-a2-i Route price bullet and "Tell the authors" P4a entry; item 17 | Constant named `MAX_ROUTE_PRICE_USD_PER_MTOK` everywhere; P4a cited by item name ("Money type and exactness", "Named constants", "Notes for P4d") because the resolve's `P4a.md:66`/`:346` moved (P4a is revision 6 on disk) |
| COR-C7-2 | applied | P4d-a2-i mutation plan i5; rounding table i10j; helper row h1 | i5 killed by the 29-digit edge rows on `check_usd` (the scale reader); the resolve's helper row `Decimal("1."+27 zeros+"1")` is real and kills the NEW i10j (context before `quantize`); expected value `1.00000001` |
| COR-C7-3 | applied | P4d-a2-i table below the mutation plan | `ROUND_05UP` named as i10i; `CEILING`/`FLOOR` stated equivalent; killers listed for i10g; the resolve's proposed killer for `05UP` (last digit 0 or 5) is wrong: it agrees with round-up (a7 shows it); killers are a1-a5 |
| COR-C7-4 | applied (merged with ADV-R7-6) | as ADV-R7-6 | as ADV-R7-6 |
| COR-C7-5 | applied | P4d-b Files, migration bullet (LAYOUT sentence) | One column per line, `\n);` last, because `test_p2_postgres._sql_columns` is a regex (`:44-58` read) |
| COR-C7-6 | applied (merged with ADV-R7-7) | as ADV-R7-7 | as ADV-R7-7 |
| COR-C7-7 | applied | P4d-a2-ii, "Evidence commands" line (EXISTING TESTS to re-run before and after) | The five files added, each checked to exist with `ls`; `test_safe_text` and `test_ledger` are under `tests/demo_askdata/`; which of them change: UNVERIFIED |

## Where the resolve and reality differ (recorded, not my errors)

1. NaN on `Reply`/`Verdict`: pydantic already refuses it, so the NaN rows are regression pins, not fail-before.
2. CI runs `postgres:17.10` only (`ci.yml:40`); the resolve says "CI also runs 16". The `transaction_timeout` sentence was changed to match.
3. `ROUND_05UP` is not killed by a row whose last kept digit is 0 or 5 (see COR-C7-3).
4. The resolve's `3 x (budget + one statement)` bound does not hold with one budget across retries; the ticket states "budget plus one statement's timeout, at most twice the budget, plus back-offs".
5. The resolve's "A2b rows kept for memory" is incoherent (memory has no row lock); they move to P2a whole.
6. The derived-state view does not exist at P4d merge time; P2a-1 changes the one statement.
7. `round_cost_up` refuses `-0` through `is_signed()` (the resolve says "not negative"; a minus zero quantizes to `-0E-8`, which the store's sign check would refuse after the paid call).
8. The memory `RLock` and its mutant moved from a2-ii to P4d-b because a2-ii has no row that could kill it.
9. `tests/test_migration_numbers.py` is expected to have no psycopg use, so its allow-list entry is conditional on the exact-set test.
10. P4a revision 6 now says `cost_usd` stays exact with rounding done once at the producers; P4d item 13 was changed to agree (the older P4d text asked P4a-2 to keep an upward rounding).

## Findings I disagree with

None contested. Two disagreements with detail inside applied rows: the `ROUND_05UP` killer (point 3 above, the resolve's suggestion would not kill it) and the bound arithmetic (point 4).

## Gaps found after the last edit

None known after the last edit. The v1.1 table now has 13 data rows (7 from earlier revisions, 6 new; counted: 14 lines starting with a bar and a letter or backtick, one of them the header); new rows: CHECK on counters, `set_config` re-issue, `transaction_timeout`, excess accounting, `validate_assignment`, the `ROUND_05UP` suggestion; the first row (short stop connection) is marked withdrawn.
