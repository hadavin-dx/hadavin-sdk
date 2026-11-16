# P4d round 5 disposition (ticket revision 7)

Ticket: `handover/tickets/P4d.md` revision 7 (271 lines). Locations are line numbers in that file as written. Decisions follow `P4d-round5-resolve.md`. No code was run against the ticket's claims; each cite kept was re-read in `src/` (core ce70eb5) or in the named ticket. Not a git repository, so there is no head SHA.

| id | status | where in the ticket | note |
|---|---|---|---|
| ADV-F1 | applied | 172 (B4 vii-a, vii-b, vii-c), 196 (b15), 5, 32, 25 | holder is `FOR NO KEY UPDATE`; `pg_stat_activity` wait plus NOWAIT probes; mirror row for the inverted order; B4(v) kept as backup; FK key-share added to the lock-order paragraph; probe cited. The exact `wait_event` is UNVERIFIED. |
| ADV-F2 | applied (merged with COR-C2) | 72 (row d, d2), 73 (i12) | |
| ADV-F3 | applied | 72 (ceiling rows), 73 (i8-day, i8-month, i8-run), 169 (B1), 208-213 (b26a-c) | memory's month is a sum of days; month row plants a different day |
| ADV-F4 | applied, narrowed (Postgres only) | 175 (B7 rows c1, c2), 197 (b16), 204 (b22) | no new memory rows |
| ADV-F5 | applied | 101 (T1, T2, T3), 117-122 (w8a-f), 199-200 (b18a, b18b) | wall-clock bounds are loose upper bounds |
| ADV-F6 | applied (merged with COR-C10) | 137 (precedence 6), 169 (X1-X4), 208-213 (b26d-f) | Postgres: cap-only UPDATEs, then a Python check of the returned totals (smaller diff) |
| ADV-F7 | applied, narrowed (one named bound, no price table) | 67, 72 (price rows, guard rows), 73 (i13, i14), 263 (item 17) | bound 10**6 is my number, UNVERIFIED against any price list |
| ADV-F8 | applied as a cap (merged with COR-C9) | 140, 171, 216 (b28b), 262 (item 16), 21, 65 | tagged [PL16]; a "no" is undoable by tag |
| ADV-F9 | applied, narrowed (P4d unchanged, relayed) | 242 (Tell the authors, P4c) | no line of `agent_loop.py` touched |
| ADV-F10 | applied (relay; merged with COR-C7) | 238-245 (Tell the authors) | `expired_at`, 6 versus 8 decimals, P4b1 caps |
| COR-C1 | applied, with my own arithmetic | 72 (a1-a8), 77-84 (i10a-h) | the resolve's example (1235 x 0.0751) does not give a 9th decimal of 1; I used 1231, 1234, 1236, 1239 at price 0.001 and checked each by hand with Decimal |
| COR-C2 | applied | 72, 73 | row (d) is a value fail-before; (d2) is a pin with mutant i12 |
| COR-C3 | applied as a cut | 5, 13, 26, 271 (v1.1 row) | k1b grep result replaces UNVERIFIED |
| COR-C4 | applied | 33 | plain SELECT right either way; locking read would hold the lock against `stop`; role grant text is `P2a.md:50-51` (the resolve said `:8`) |
| COR-C5 | applied | 8, 13 | "ALL FIVE"; P2a-1; migrate order P3a, P4d-b, P2a-1, P4b2-b; cite by item name (P2a list is at `:10`, not `:9`) |
| COR-C6 | applied | 13, 239 | `fake.py` order P4d-a2-i, P4a-1, P4a-2 |
| COR-C7 | applied (merged into ADV-F10) | 238-245 | |
| COR-C8 | applied | 141, 163, 140, 190 (b9), 171, 215 | [PL10] tags added |
| COR-C9 | applied (merged into ADV-F8) | as ADV-F8 | |
| COR-C10 | applied (merged into ADV-F6) | as ADV-F6 | |
| COR-C11 | applied (output price 0 in every row) | 72 | |
| COR-C12 | applied | 35 and 104 (`:294`, def `:293`), 155 (`:31`), 125-126 (w11 before w12), 226 (two more `pg_driver(` callers), 25 (`pyproject.toml:54`; `:52` is the `test` group) | |

Counts: 22 finding ids. Applied 22 (3 narrowed: ADV-F4, ADV-F7, ADV-F9; 1 as a cut: COR-C3). Contested 0. Declined 0.

Where I disagree with the resolve's text (the finding is still applied): the C1 example arithmetic; its cite `P2a.md:8` (actually `:50-51`) and `P2a.md:9` (actually `:10`).
New PENDING LEAD: item 16 ([PL16], settle excess cap) and item 17 ([PL17], route price bound), at lines 262 and 263.
