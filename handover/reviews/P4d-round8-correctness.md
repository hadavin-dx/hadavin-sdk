# P4d round 8, correctness review (ticket revision 9)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-codebase-details`, read-only, nothing run, did not open `reviews/`. Last of the 3 rounds P4d may still have under order 16. Every trace UNVERIFIED unless read.

Verdict: NOT CLEAN by the stated rule: 0 Blocker, 1 Major, 6 Nit.

## MAJOR

**M1. Producer row a7 contradicts the ticket's own route-price validator (line 81; mutant table lines 86-95).** Row a7 is "1 token at price `1E-30`", cost `1E-36`, expected `0.00000001`, through both `reply()` and `FakeLLM`; both take a `Route`. The new `Route` validator (line 76) allows at most 6 decimals (`x != x.quantize(1E-6)` refused). `1E-30` has 30 decimals, so the fixture cannot be built (`model_copy(update=...)` is the only way past, and the row does not use it; `FakeLLM` reads `self.routes[route]`, fake.py:49-53). Fix: price `0.000001`, cost `1E-12`, rounds up to `1E-8`; HALF_UP, HALF_EVEN, HALF_DOWN give 0 on it, so i10c, i10d, i10e and i10h keep their kill sets; i10g still dies on a7. (Same defect as the adversarial M1.)

## NIT

- N1: line 17 says P6b1's place relative to P4d is "not stated: UNVERIFIED"; line 273 and the P6b1 relay state it (after P4d-a2-i, before P4b1). Make them agree.
- N2: P4d cites "P4a revision 6 (as on disk)" at lines 33, 75, 76, 265; P4a.md is revision 10+. Reword to "revision 6 or later, cite by item name".
- N3: P4b1.md:71 still says P4d lets one real settle correct an expired row downward once; PL10 makes it either direction; add to the "Tell the authors" P4b1 bullet (line 266).
- N4: P4a.md:154 says `round_cost_up` is imported by `llm/common.py`, `llm/fake.py` and `k1b/loop.py`; P4d says `k1b/loop.py` is untouched; the P4a bullet (5) should point at that line.
- N5: P4d-c mutation plan (line 258) numbered c6, c1..c5 (cosmetic).
- N6: line 21 recount definitions differ (17 and 6 vs 15+15 and 5+5); reviewer's own count of lines containing "psycopg" matches the table totals (k2_migrations 30, audit_chain 10, k5_fixes2 4, k5_round10 9, p2_postgres 9, p7_store 6). Close the "UNVERIFIED which is right" note.

## Verified (by reading or by hand)

Money rows a1-a8 and every i10 kill set (HALF_UP dies on a1, a2, a7; HALF_EVEN/HALF_DOWN on a1, a2, a5, a7; ROUND_DOWN a1-a5, a7; ROUND_05UP a1-a5; i10f every row; i10g 7 decimals a1-a7, 9 decimals a1-a5 and a7); exactness row; digit arithmetic (ceiling 1000 x MAX_USD, below 28 digits); settle-bound and PL16 rows; 12 SpendReservation fields vs 12 DDL columns; 16 status pairs (5 allowed, 11 refused); 40 frozen-column cases; Protocol 32 methods + 6 = 38; 18 write methods; 12 `with self._lock` lines; 26 test functions (52 cases); `is_connectivity_error` 4 callers; 8 and 7 importers. Cites in postgres.py, memory.py, protocol.py, common.py, fake.py, config.py, models.py, agent_loop.py, limits.py, migrate.py, table.py, ci.yml, cli.py, app.py match. Lock order and FK-lock reasoning consistent on paper. Cross-ticket relays by grep: P4a, P3a, P2a, P4c, P6b1.

## Not checked

Everything needing Postgres, the venv or pydantic (the ticket's own "run by me" claims, wait_event values, nested savepoint, `make_interval`, DDL through `_scan`, FK probe behaviour on 17); P2a, P4b2, P4c line cites beyond grep; P6b1 item 2; P3a rev 8; the 16 test files building Reply/Verdict; `_insert`/`_select` internals; FOR KEY SHARE / NO KEY UPDATE / ON CONFLICT DO NOTHING interaction.
