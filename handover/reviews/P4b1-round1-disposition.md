# P4b1 round 1: disposition of the findings (ticket revision 2)

Ticket revised: `handover/tickets/P4b1.md` (revision 2, 374 lines; revision 1 was 255 lines, commit `15d01fa`). Author: Sonnet 5.5 revision agent, 2026-11-06 (UTC). Input: `reviews/P4b1-round1-resolve.md` (30 decision rows for 41 finding ids, plus 7 relay rows). I read the round 1 adversarial (A1-A16) and correctness (C1-C25) files only to check that the resolve was applied faithfully. Nothing was run; the only checks were `grep` and file reads (listed below). Verdict APPLIED = the ticket text now says it.

## Counts
- Finding ids 41 (A1-A16, C1-C25) in 30 resolve rows: APPLIED 28 rows covering 39 ids; CONTESTED, no change 2 rows (C21, C24); not applied 0 otherwise. A16 is applied with one sub-point kept as the resolve contested (gate 3 wording).
- Relay rows: 8 labels (R1, R2, R3, R4a, R4b, R4c, R4d, R4e); the resolve calls them 7 (see note 1). All APPLIED.
- Mutants in revision 2: P4b1-a 50 live (M1-M53 minus the three CUT ids M14, M17, M25; 29 old minus 3 plus 24 new M30-M53); P4b1-b 23 live (W1-W24 minus the CUT id W2; W10 replaced). Total 73 live mutants. Counted by script over the two tables (53 and 24 table rows).
- Test rows in revision 2: P4b1-a 74 (T1 30, T2 13, T3 14 parity rows, T4 4, T5 5, T6 8); P4b1-b 23 (relay rows R4a, R4b-1, R4b-2, R4c, R4d-1, R4d-2 = 6, plus B1-B17). Total 97. T7 (settings) is gone. Counted by script over the numbered rows.
- PENDING LEAD: 17 numbers, 16 live (4 replaced by 11). New 11-17 as the resolve gave. 3 amended by 15; 7 moved to the P4b1-c stub.
- Cut: `Config.meter` and `MeterSettings`, the `zone` argument, `cap_zone`, `Asia/Kolkata` row, T7, M25; the global stop on overshoot (`Limits.stop` wiring, PL4, M14); the `halt` field, grammar, row, M17; `tests/contracts/kinds/meter.py`; P4b1-c; W2 and all tier, monotone-price, highest-input-class and price-date text; P4b1's own `PROMPT_BYTES_PER_TOKEN`; the overshoot fallback and its crash-window test; "Needs from P4d item 1".

Note 1 (counting): the resolve says "7 relay rows (R1, R2, R3, R4a to R4e)". That is eight labels (R1, R2, R3, R4a, R4b, R4c, R4d, R4e); the resolve's own count of 7 is a slip and I applied all eight.

## Verification I did (read-only)
- `limits.py` lines 16-30: day taken as `now().date()` (UTC), reasons `daily_budget` and `monthly_budget` (C1, A4, C7 confirmed). `registry.py` `max_run_usd: Money | None` (C2). `app.py:171` `Limits(store, audit, reg)`. `llm/common.py:59` `estimate_tokens`. `llm/fake.py` has no `max_attempts`. No `zoneinfo` under `src/`. `tests/contracts/conftest.py` has per-capability `_kinds(...)` fixtures only (C9).
- P4a.md lines 86, 160-162, 194, 199 (`request_bound` strict, `REQUESTS_PER_CHAT`, forwarding, item 15 settle in `finally`, constants owned by P4a-2) and the lead merge-time checklist item 0 (i)-(v): all five items are now in the P4b1 text and found by grep (`request_bound` 11 hits, "a missing count never books 0" 1 hit, `REQUESTS_PER_CHAT = 2` with `max_attempts = 3`, "100,000" 4 hits, `finally`/round_cost_up row).
- P4d.md lines 37, 153-160 (error classes, `reserve_spend` and `settle_spend` shapes, `CounterDamaged`, the settle books the full actual, PL23 mention).
- Hygiene grep on the ticket for model ids, studio paths, home paths and owner names: no hits.

## Decisions applied

| id(s) | verdict | where in revision 2 | note |
|---|---|---|---|
| A1, C6 | APPLIED | -a "Overshoot"; T2.12, T6.8, P10; M13, M51 | one `settle_spend`; fallback, crash-window test and "Needs from P4d item 1" deleted; R2 stale `ValueError` sentence gone with it |
| A2, C2 | APPLIED | -a `reserve`; T1.14, T2.7, B8; M30 | only P4d's rule kept (`run_cap` None when `run_id` None) |
| A3, C8 | APPLIED | T5.1/T5.2, B10; M24 | holds open until a second barrier; exact count; separate `<=` row for cost below worst case |
| A4, C7 | APPLIED (cut) | Rules stated once (UTC day), PL12, T1.30, T2.6; M16 reworded | no zone, no `Config.meter`, no T7, no M25; v1.1 row written in the rules block; `max_hold_s` is a `Meter` keyword |
| A5 | APPLIED | Rules stated once ("Live-call gate"), -b, PL5 | no release rule in -b; retry-storm drain stated as dev/fake-only |
| A6 | APPLIED | -a "Exit-settle failure", `SettleFailure`; T1.22-T1.24; M33-M35; PL15 | `METER_SETTLE_RETRIES = 2`; repair path by resending `Meter.settle(id, planned)` |
| A7, C5 | APPLIED (cut) | -a "Overshoot", PL11, Security notes; M14 CUT, T2.12 | meter only signals; no `Limits.stop` anywhere in the ticket |
| A8 | APPLIED | -b interface (`scope`, `ContextVar`), B7; W20, W21; PL14 | no scope raises `MeterError` before any call; threads open their own scope; -a owns `Caps`, `Limits.caps`, `REASON_BY_WHICH` |
| A9, C12 | APPLIED (cut) | P4b1-c stub (5 bullets), problem line wording, memo-2 table | open questions copied including C12's `worst_case_usd`, `remaining`, `snapshot`, `check`, `charge` and the `Registry`/`AuditSink` need; rev 1 had no -c rows in the memo-2 table, so only a pointer row was added |
| A10, C3 | APPLIED | header, Depends-on, "Answered by P4a revision 12 ... and P4d revision 10" table | five P4d PRs; section shrunk to a table of final names |
| A11 | APPLIED | -a `reserve` (`except BaseException`), late-commit window sentence; T1.12, T5.4; M36 | |
| A12, C13 | APPLIED | -b "FAIL-BEFORE honesty", B17 | shim row is a regression pin |
| A13, C16 | APPLIED | T1.2, T1.5-T1.7, T1.13, T1.19, T1.20, T2.9, T2.11, B11; M37-M46 | W10 replaced; M10 has T5.5; M18 points at T1.25/T2.5; record-twice rule pinned as "last call wins" (my pick, as the resolve allowed) |
| A14, C19, C25 | APPLIED | Rules stated once (constants), T4.4; M52 | 16, 3, 10**9, 2, 5, 2 are now `METER_FRAMING_BYTES`, `METER_DOC_BYTES_FACTOR`, `METER_ABSURD_TOKENS`, `METER_ORPHAN_FACTOR`, `METER_ORPHAN_MARGIN_S`, `METER_SETTLE_RETRIES`; `clock=None` resolved at call time; `from_usd` calls `check_usd`; `halt` and `zoneinfo`/`tzdata` gone with their cuts |
| A15 | APPLIED | -b interface (`routes` is the same mapping), B9; W22 | |
| A16 | APPLIED, sub-point contested | `Limits.hold` lock (T2.10, M47); `stop` masking gone with A7; `Limits.caps` rounds down to 8 decimals (T2.9, M44); Step 0 "Expected outcome" and owner notice TEMPLATE | gate 3 stays as written and now cites `studio-notes/amendments.md:17` (F1) as its source, as the resolve decided |
| C1 | APPLIED | `REASON_BY_WHICH`; T1.11; M31 | |
| C4 | APPLIED | `OverBudget(reasons, *, which, cap, current, requested, day)`; T1.10; M32 | |
| C9 | APPLIED (cut) | Files list; T6 | no `kinds/meter.py`; uses existing `store` and `store_pair`; `conftest.py` untouched |
| C10 | APPLIED | Fail-before wording rule; T2.8; evidence step 4 | `importlib` inside the shim; `pytest.importorskip` forbidden |
| C11 | APPLIED | Step 0 table gate 1 and 3 cells; owner notice template | gate 1 for A is "UNVERIFIED: builder checks that A's Decimals have a fixed exponent (A1(3))"; "keeps money as decimals" removed |
| C14 | APPLIED (cut) | `Hold.record` has no `halt`; M17 CUT | |
| C15 | APPLIED | T4.2 exact allow-list | |
| C17 | APPLIED | "One error table" in Rules stated once; T1.9; M48-M50 | seven closed codes; `counter_damaged` new |
| C18 | APPLIED | last bullet of Rules stated once | one paragraph |
| C20 | APPLIED | memo-2 row 6 | wording as the resolve gave |
| C21 | CONTESTED, no change | Step 0 keeps "builder re-measures"; measurements section notes the resolve's re-run | resolve re-ran the numstat at head `8986cb5`; all figures match; I did not re-run it |
| C22 | APPLIED | T2.8 | "at most 0.80"; "1.20 or less" deleted |
| C23 | APPLIED | first bullet of Rules stated once | one sentence citing amendment A11 |
| C24 | CONTESTED, no change | "Existing core code reused" keeps its "Checked and NOT relevant" list | already present in rev 1 |
| R1 | APPLIED | -a orphan-age bullet; PL8 | "once, in either direction" at both places (rev 1 `:71` and `:243`) |
| R2 | APPLIED | closed by the A1 rewrite | |
| R3 | APPLIED | "Caller rule" bullet; T1.23, T5.3, B16 | T5 crash row uses `Meter.settle(id, None)`; -b never releases before P4b2 |
| R4a | APPLIED | -b "Reservation = request_bound(inner) x W", row R4a; W11, W12 | N/2 sentence in the interface and the CHANGELOG line |
| R4b | APPLIED | rows R4b-1 ("a missing count never books 0"), R4b-2 (settle in `finally`); W13, W14 | |
| R4c | APPLIED | tier bound, row R4c, `METER_MAX_PROMPT_TOKENS`; W15; PL16 | UNVERIFIED number, marked |
| R4d | APPLIED | "Failure booking (PL60)", unknown attempts (PL51), PL59 sentence; rows R4d-1, R4d-2; W16-W19, M53; PL17 | see note 3 |
| R4e | APPLIED | -b interface, "Answered by P4a revision 12" table, Depends-on lines | tier/monotone/highest-class/W2/price-date text deleted; own `PROMPT_BYTES_PER_TOKEN` deleted and imported; "both P4a pull requests"; -a Depends-on names P4a-2 |

## Things I added or chose that the resolve did not spell out (please check)
1. `Hold.record(actual, *, measured=True)`: a new keyword, needed so the PL60 failure booking and the PL51 add-on can be recorded without calling `on_overshoot` (the resolve says that booking "does NOT call on_overshoot, which is only for measured replies"). It is one small piece of surface the resolve implies but does not name. Mutants M53 and W17 cover it.
2. `on_overshoot` is called only when `applied` is true (a replay does not signal twice). The resolve did not say this; it follows from idempotent settle.
3. R4b says a stub whose `chat()` raises `ValueError` "settles at the reserved amount", while R4d says "any exception from `inner.chat`" books request count x attempts x W. These conflict for a plain `ValueError`. I followed P4a item 15 (a non-`ProviderError` settles at the reserved amount) and applied the R4d booking to `ProviderError` only (`UsageMissing`, `ProviderExhausted`, `CallTimeout`). Written into PL17 for the lead to confirm.
4. `Limits.on_overshoot` and `Limits.on_settle_failed` as two plain attributes read at call time, so no `Limits` constructor or `app.py` change is needed (the resolve says callbacks exist but not how `Limits` carries them). Rows T2.13, mutant M46.
5. `SettleFailure(reservation_id, planned, code)` fields follow the resolve; the Hold attribute is named `settle_failure` (rev 1 had `settle_error: str`).
6. `max_hold_s` is validated 1..3600 in the `Meter` constructor (it was the `MeterSettings` validation); row T1.26, mutant M15.
7. `unknown_attempts` is a provisional name for the count P4b2-a exposes (marked PENDING P4b2).
8. `record` twice / `record` then `release`: the last call wins (the resolve told the author to pick one and pin it).
9. Test rows were numbered (T1.1 and so on) so mutants point at rows; this made the file longer (255 to 374 lines), not wider in scope. The resolve predicted about 20 fewer lines for the -c cut; the added rows, mutants and error table outweigh that.
10. The resolve's "Expected revision 2 effects" said "about 14 rows/mutants added"; the real figure is 24 new -a mutants plus 14 new -b mutants, because A13, C17 and A6 each produced several.

## Not applied, and why
- Nothing from the 39 fixes was left out. C21 and C24 are contests with no change, as the resolve decided.
- Not done by me, and not part of this task: edits to P4c, P4b2, P4a or P4d (the couplings are written in "Not checked and not run" for their authors); any run of tests or Postgres; any push (commit is local only).
- Still UNVERIFIED in the ticket, marked as such: all P4a/P4d names (read from frozen tickets, not code), the 100,000-token bound, `limits.py` `now` binding for the shared-day test, which kinds expose `routes`, whether Python 3.12 exists in the cloud container.
