# P4d build-start resolve (order 20, one round)
Status: resolved (AUTO mode, interactive gate skipped as ordered; model output, not user authority)
Target: `handover/tickets/P4d.md` rev 10 (FROZEN), full file. Fixes are a new end section "Build notes (build-start review, order 20)" (K1-K4 corrections, N1-N13 instructions); no body line changed or renumbered.
Gate: AUTO; one round, no second review (order 20(3)).
Facts checked by me (read/grep on the worktree `src/`, `tests/`, `handover/`): `migrate.py:308-332` one `db.transaction()` around advisory lock, all files, ledger, grants (confirms A:ADV-5/C:COR-1); `memory.py:29` `__init__(self)` no args, `:31` plain Lock, `:57-59` `get_run` takes it, `:196-204` `add_spend` adds before any check; `postgres.py:197` plain Lock, `:201-202` `_exec` is the only `.execute(` in `PostgresStore` (the other is `conn.execute` in `connect`, `:148`), `_insert`/`_select`/`_update_run` use `_exec`, `:276-277` `add_cost` one autocommit UPDATE, no RETURNING; `tests/test_p2_postgres.py:51` regex `^\s+"?(\w+)"?\s+[A-Z]` (an `AND NEW...` line is a phantom column); ticket line 153 `amount_usd` > 0 (so `positive` is needed, not deleted); line 251 P4d-c depends on P4d-b and P3a; LEAD-ORDERS 19(D) accepts PL22 and PL23; order 20(2) text "P4d (a1 to c, then a2-i)"; `P4b1.md:17` meter rounds up to whole micro-dollars itself. T4 margins worked with python3 -I.
Honest note (what I did NOT check): I ran nothing against Postgres or the project venv; every PG behaviour in the notes (savepoint nesting in N4, lock waits in N6, `INSERT ... ON CONFLICT DO NOTHING` not waiting on a held counter row in B4b(b)) is documented/reasoned, UNVERIFIED. I did not read the whole 86k-token ticket: only the lines the findings cite plus headings, PENDING LEAD and v1.1 tails, so a note may collide with a body line I did not read (the "note wins" rule covers it, but a conflict could hide). I did not open P3a.md, P2a.md, P4a.md, P6b1.md, test_lockin_guard.py or the evidence dir. The two reports reuse ids (the adv file has rows named COR-1..8); I prefixed A:/C: by file. N8's seed/step numbers and N9's cut are my choices, not a reviewer's. I did not update the PENDING LEAD list or "Tell the authors" in the body (frozen); the relays are in N10/N11 and below.

| id | category | decision |
|---|---|---|
| A:ADV-1 | PROPOSE FIX | N10 rows r1 (larger second settle ignored, applied=False) and r2 (release of expired pinned); K2 item 23 answered; mismatch handling to P4b1 = PL 25. Release-of-expired kept: crash recovery of a never-sent call needs it, and cutting it changes the 16-pair trigger matrix C verified. |
| A:ADV-2 | PROPOSE FIX | N11: B6 7/8-decimal rows; relay P4b1 to round up to micro-dollars (it already says so, P4b1.md:17). Store stays at 6 decimals. |
| A:ADV-3 | PROPOSE FIX (cut) | N9: keep memory plain Lock, no nesting, delete b29 (b 43->42), keep B4b(c). |
| A:ADV-4 | PROPOSE FIX | N8: 200 seeds x 30 steps; sweep ops on memory only; 180 s CI budget with stated fallback. |
| A:ADV-5 | PROPOSE FIX | K1 correction (dup of C:COR-1). |
| A:ADV-6 | PROPOSE FIX | N1 ticket order, b/c after P3a; K3; order 20(2) wording = PL 24. |
| A:COR-1 | PROPOSE FIX | N2. |
| A:COR-2 | PROPOSE FIX | N3 (dup of C:COR-2). |
| A:COR-3 | PROPOSE FIX | N4 (dup of C:COR-4). |
| A:COR-4 | PROPOSE FIX | N12. |
| A:COR-5 | PROPOSE FIX | N7. |
| A:COR-6 | PROPOSE FIX | K4 label correction. |
| A:COR-7 | PROPOSE FIX | N13: define `positive` (refuses zero; used by reserve_spend). Reviewer's "delete" option rejected: line 153 needs it. |
| A:COR-8 | DECLINE | Nit; order 20(5) rebase-on-main makes hot-file UNVERIFIED notes moot. |
| C:COR-1 | PROPOSE FIX | K1. |
| C:COR-2 | PROPOSE FIX | N3. |
| C:COR-3 | PROPOSE FIX | N6: budget 5000, releases at 2500/6000 (margins >= 1 s). Monotonic-clock seam not chosen: it would test the seam, not real waits. |
| C:COR-4 | PROPOSE FIX | N4. |
| C:COR-5 | PROPOSE FIX | N5. |
| C:COR-6 | PROPOSE FIX | N1. |
| C:COR-7 | PROPOSE FIX | K3. |
| C:ADV-1b | DECLINE | Reviewer's own "no change": the +-1 day bound is for app/DB clock skew; caller is our meter (caller-trust boundary already stated). Not escalated; lead may add a v1.1 row if wanted. |

Couplings: K1 also touches line 246 (still true: SET LOCAL comes after the advisory lock) and evidence (c) (assert the timeout lasts to end of the migrate transaction). N3+N6 together kill w14 (scan + T4) and b18c. N9 removes b29 and voids lines 25/179 and the RLock part of B4b(c) wording; Postgres RLock (a2-ii) untouched. N2 moves the memory fake clock to b, matching line 160. N4 precedes a2-ii, so a2-ii must keep the inner transaction as a savepoint. N10/N11 are relays to P4b1 (owner P4b1).

PENDING LEAD (continuing the ticket's numbering):
24. Order 20(2) says "P4d (a1 to c, then a2-i)"; the ticket chain is a1, a2-i, a2-ii, b, c and a2-i is a money PR that b needs. Recommendation: read it as the ticket order (N1); a1, a2-i, a2-ii start now, b and c after P3a merges. Reversible.
25. Settle returning `applied=False` with `settled_usd` different from the meter's actual (two actuals for one call = a meter bug). Recommendation (owner P4b1): halt the agent and tell a person, and if the meter's actual is LARGER book the difference with `add_spend` before halting (never under-book, order 14(3)). Reversible.

Counts: 22 finding ids (14 in adv file, 8 in cor file); PROPOSE FIX 20 (of which 1 cut: N9; 4 are corrections K1-K4, with 3 duplicate pairs merged), CONTEST 0, ESCALATE 0, DECLINE 2; build notes K 4 + N 13; PENDING LEAD new 2 (24, 25); ticket body lines changed 0 (316 -> 338 lines, append only); mutants b 43 -> 42.
