# P4b1 round 3, correctness review (ticket revision 3)

Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

Reviewer type: egm:egm-codebase-details. Read-only.

Ids: R3-COR-1 to R3-COR-17.

TICKET REVIEW round 3, CORRECTNESS, handover/tickets/P4b1.md (revision 3)

Verdict: 0 Blockers, 1 Major, 11 Minors, 5 Nits. By the order 20 item 6 rule (no Blocker and at most 2 Majors) an extra round 4 is allowed.
The files at src and tests were read-only. Every src cite below was checked against that copy. Whether it equals `ce70eb5` is UNVERIFIED, because this directory is not a git repository. No cite failed on account of main differing.

## Findings

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | 268, 280 (R4d-1), 324 (W16), 427 | The ticket says a `ProviderError` includes `CallTimeout`, and that R4d-1 and W16 book `count x attempts x W` for a `CallTimeout` stub. In code, `CallTimeout` is `class CallTimeout(Exception)` at `k1b/loop.py:77`. It is raised by k1b's own timer at `k1b/loop.py:109`, not by a kind. It is not a `ProviderError` (`llm/protocol.py:10`). `NetworkLLM` has no such class. P4a lists it as a separate class beside `ProviderExhausted` (`P4a.md:47,88,139`). Under the ticket's own rule "any other exception settles at the reserved amount", R4d-1 expecting 6W for a `CallTimeout` stub cannot pass. A network timeout reaches the wrapper as `ProviderExhausted`, which is covered. | Delete `CallTimeout` from the `ProviderError` list at line 268 and from the R4d-1 stub list. Name the real classes: `UsageMissing`, `UnpricedUsage`, `ProviderExhausted`, plain `ProviderError`. Add a row stating what a bare `CallTimeout` (plain `Exception`) books, which is the reserved amount. |
| R3-COR-2 | Minor | 163 (T2.14) | "1,001 holds of 1 micro-dollar, each settled at MAX_USD" does not reach the premise if hold and settle alternate. MAX_COUNTER_USD is 10**15 (`P4d.md:153`, `:279`) and MAX_USD is 10**12. Each hold leaves the counter at exactly 10**12 (1 micro reserved, plus excess 10**12 minus 1 micro). After 1,000 rounds the counter is exactly 10**15, and the 1001st reserve is refused by the ceiling. The counter never goes above it. | Say that all 1,001 reserves are opened first (ExitStack) and settled afterwards. The sum is then 1.001e15. |
| R3-COR-3 | Minor | 147, 154 (T1.30, T2.6) | The pinned UTC date is not given. P4d refuses a new reservation whose day is more than 1 day from the database UTC date (`P4d.md:154` item 5). Postgres uses the DB clock, which a test cannot inject. A fixed past date would give `store_rejected`. | State that the pin uses the real current UTC date (23:59:59) and the next day (00:00:00), both within the bound. Note that the row is time-of-day sensitive around midnight. |
| R3-COR-4 | Minor | 48, 98, 102, 254, 258, 304 and similar | The ids "A5, A6, A8, A12, A13, A15" are round-1 finding ids. They collide with `amendments.md` A1-A14. Line 3 lists A8 and A13 as amendments that apply here. A reader who looks up "Live-call gate (A5)" finds KERNEL-1. A6 is the llm-kind claims, A12 is the package table, A13 is P4d/P2a/P1/P3a decisions, and A15 does not exist. | Prefix them as "round 1 ADV-A5" and so on, or cite the real source. |
| R3-COR-5 | Minor | 49 vs 166, 231 | Line 49 says no other number is written in `meter.py`, `money.py` or `llm/metered.py`, scanned by T4.4. T4.4 and M52 scan only `meter.py` and `money.py`. `llm/metered.py` has no scan row and no mutant. | Extend T4.4 and M52 to `llm/metered.py`, or reword line 49. |
| R3-COR-6 | Minor | 261, 301 (B19) | `price x MICRO_PER_USD` is computed in the default 28-digit context, then tested for a whole number. A `model_construct` route price with more than 28 significant digits can round its fractional part away and pass as whole. B19 tests only a short 7-decimal value. P4d's `check_usd` reads the scale from `as_tuple()` with no context rounding for this reason (`P4d.md:72`). | Reuse `check_usd(price, max_decimals=MICRO_DECIMALS)` for the price, or test `as_tuple().exponent`. Add a B19 sub-row with a 30-digit price. |
| R3-COR-7 | Minor | 93, 122, 218 (M39) | `ceil_cost` refuses a zero denominator and a negative numerator. A negative denominator is not refused, and `-(-n // -d)` gives a wrong sign. T1.5 and M39 do not cover it. | Refuse denominators of 0 or below with `ValueError`. Add the case to T1.5 and M39. |
| R3-COR-8 | Minor | 104, 105; 197-233 | Two stated behaviours have no row and no mutant. (a) The log line at exit when `age_s()` passes `max_hold_s` (line 105). (b) The pass-through of the store's "clock set back more than a day" refusal (line 104). Several rows have no mutant: T1.24, T2.14, T2.15, B14, B16, B17. B14 is the row meant to prove the wrapper never reads `Reply.cost_usd` (R2-COR-7). | Add T1 rows for (a) and (b). Add a mutant "wrapper uses `reply.cost_usd`" killed by B14. Say that the other rows are pins. |
| R3-COR-9 | Minor | 149, 156, 161 | T2.1, T2.8 and T2.11 write `Limits.charge("a", 0.60)` and "0.40" as numbers. Floats are refused (`config.py:41-43`; `check_usd` needs `type(x) is Decimal`, `P4d.md:72`). A literal float in a test fails on the new code. | Write `Decimal("0.60")` and `Decimal("0.40")`. |
| R3-COR-10 | Minor | 419 and 3 | Line 419 says "P4c revision 3 is NOT written yet", and line 3 says "reads P4c revision 2". `handover/tickets/P4c.md:1` is "REVISION 3" and already carries `scope.refusal`, `estimate_exceeded`, `limits_unavailable`, `WALLS`, `REASON_BY_WHICH` and `on_settle_failed` (lines 8-18, 34, 54, 62, 75). The couplings were not re-checked against it. | Re-read P4c revision 3 and update lines 3, 419 and 425. |
| R3-COR-11 | Minor | 51, 88, 396 | Names a "P2a-1b" package. Order 7 item 3 merged 1a and 1b into one PR, and P4d already says "P2a-1 (the merged 1a and 1b)". Line 418 says `Limits.stop` is no longer used. | Rename to "P2a-1" and check whether the dependency is still needed. |
| R3-COR-12 | Minor | 168 (T5.1) | "Granted holds EQUALS floor(cap / amount)" holds only if floor(cap/amount) is at most 48 (8 x 6 attempts). Otherwise the answer is 48. No numbers are given. | Give made-up numbers (for example a cap for 20 holds), or write min(48, floor(...)). |
| R3-COR-13 | Nit | 12 | "`Limits` is built once at `app.py:171`". `cli.py:209` also builds `Limits(store, audit, reg)`. The claim that the loop is the only caller of `blocked`/`charge` holds: `agent_loop.py:240,670,744` for `blocked` and `:314,440` for `charge`. | Say "built at `app.py:171` and `cli.py:209`". |
| R3-COR-14 | Nit | 50, 71, 165 | Cite drift. `test_budget.py` forms are lines 151-159 (decorator 151-153, test 154-159). Line 71 says 151-160 and P7 says 148-159, where 148 is the previous test's last line. `tests/test_s5_runtime.py:109-128` covers the body of a test that spans 107-130. `P4a.md:164` does not say `pytest.importorskip` is forbidden. That rule is this ticket's own, and `P4a.md:165` itself uses `importorskip`. | Correct the cites. Mark the importorskip ban as this ticket's rule. |
| R3-COR-15 | Nit | 111 | "uses the existing `store` and `store_pair` fixtures". `tests/contracts/conftest.py` has `store` only (line 30). `store_pair` is P4d-a1's (line 114 says so). | Write "the `store` fixture and P4d-a1's `store_pair`". |
| R3-COR-16 | Nit | 143 (T1.26) | "equals 2 x max_hold_s + 5 for max_hold_s above 297 and is 600 below". At 297, 2x297+5 is 599, so the value is 600. | Write "at or below 297". |
| R3-COR-17 | Nit | 413 (PL22) | `P4b2.md:95` calls the field "PENDING LEAD 16 with P4b1", but this ticket numbers it PL21. | Note the cross-numbering in PL21. |

## Verified (command or read, then result)
- Test rows: -a is 77 (T1 30, T2 16 with T2.11a/b, T3 14, T4 4, T5 5, T6 8). -b is 28 (R4 rows 7, B1-B21 21). Total 105. OK.
- Live mutants: M1-M55 minus the CUT M14, M17, M25 is 52. W1-W30 minus the CUT W2 is 29. Total 81. Every mutant has a named killer row that exists. Rows with no mutant are listed in R3-COR-8.
- Constants: -a 8 and -b 5, matching the list at line 49. Error codes: 7, matching the list at line 31. PENDING LEAD: 22. Template fields: all present for -a and -b.
- No constant named in the ticket exists in `src/` yet (grep count 0). That is expected, because they are proposed.
- Line cites against `src/` that matched:
  - `limits.py:8` (the `now` import), `:17-30`, `:18,24` (`now().date()`), `:26` (`>=`), `:27,29` (reason strings)
  - `app.py:171`; `agent_loop.py:240`, `:245`, `:314-315`, `:440-441`
  - `registry.py:53`; `config.py:47`, `:55-59`
  - `models.py:23` (`new_id` gives `prefix-<32 hex>`), `:289-297`. `Reply` is `extra="forbid"` via `Shape` (`models.py:50-51`) and has no unknown-attempts field now.
  - `llm/common.py:59` (3 chars per token), `:86-92` (docstring at `:90`, decode at `:92`), `:193`, `:208-220`
  - `llm/fake.py:29`, `:39`; `llm/protocol.py:19`
  - The four kinds subclass `NetworkLLM` at `anthropic.py:91`, `bedrock.py:113`, `gemini.py:40`, `openai_compat.py:74`. The only `def chat` in `llm/` is `common.py:208`, `fake.py:29` and `protocol.py:19`.
  - `backends/table.py:37` (socket timeout), `:40` (`max_attempts` default 3, `ge=1`, `le=10`), `:593` (`DEV_ONLY`)
  - `store/protocol.py:25`, `:45`, `:151`; `store/protocol.py:33` (`OSError` counts as unreachable)
  - `guard/injection.py:85`, `:89`
  - `demos/ask-your-data/askdata/meter.py:221` (`settle`)
  - `tests/test_lockin_guard.py:69`; `ci.yml:40` (postgres:17.10); `ci.yml:79,81,119` (ruff and bandit); `pyproject.toml` markers `live` and `perf`
  - `tests/contracts/kinds/store_postgres.py:18` (`pg_schema(migrated=True, runtime=False)`); nothing in `src/` uses `zoneinfo`; `FakeLLM` has no `max_attempts`
- Intake inputs, all matched: `budget.py` 753 lines and `model.py` 315 lines; `test_budget.py` 775 lines and 49 test functions. `budget.py:289`, `:545`, `:604`, `:663` and `model.py:197,210,285` match. Parity cites P1 `:56`, P2 `:66`, P3 `:79`, P4 `:118`, P5 `:128`, P6 `:136`, P8 `:162`, P9 `:173`, P10 `:181`, P11 `:199`, P14 `:579` match. The 14 garbage forms are exactly 14. MANIFEST ids 1265 and 1266 match `budget.py` and `model.py` in `MANIFEST.csv`.
- Cites into other tickets that matched:
  - `P4d.md:71-76` (MAX_USD 10**12, 6-decimal route price, PL17)
  - `P4d.md:153-156` (StaleState only from `reserve_spend`, settle replay returns the first result)
  - `P4d.md:9,39` (counter above the ceiling only after a settle)
  - `P4a.md:134`, `:189`, `:192`, `:196`
  - `P4b2.md:95`, `:133`, `:165`, `:184`, `:187`, `:212`, `:321`
- `amendments.md:17` (F1) and `:30` (A11) match. Order references (7, 14, 19 D, 20 items 4-6) match.
- Hand arithmetic, all correct:
  - W example: 4000 x 3e6 + 1024 x 15e6 = 2.736e10, divided by 1e6, gives 27,360 (also in `P4a.md`).
  - P14: 6,620 and 26,480.
  - P8: 333,334 over 1e6 gives 1; (3,7) at 1e6/5e6 gives 38.
  - P2: 10 + 400,010 + 400,010 fits under 1e6; three 400,010 do not.
  - P10: 20 reserved, 2,000 actual, overshoot 1,980.
  - T2.8: floor(1.00/0.40) x 0.40 = 0.80; the old path gives 3.20.
  - 0.075 x 10**6 = 75,000; 0.0000001 x 10**6 is not whole.
  - Failure excess: count x (attempts-1) x W = 2W for count 1 and 3 attempts, 4W for count 2. R4d-3 counts 0-7 for attempts 8.
  - B15: 10**10 x 10**9 = 10**19, above 10**18.
  - Release table: 9 rows, matching T1.13 and M43.
- No real-looking secret found. The DSN is built from parts.

## Not checked
- UNVERIFIED: PR #48 figures (`origin/core-hardening-1`, 8986cb5, numstat) and `ce70eb5` itself. There is no git here, so I could not confirm equality with this `src/`.
- UNVERIFIED: the P4d method names and behaviour (`check_usd` home, `StoreBusy`, `SpendCapExceeded`, etc.), the P4a names (`request_bound`, `REQUESTS_PER_CHAT`, `UsageMissing`, `UnpricedUsage`, constants), and P4b2's `Reply.unknown_attempts`. They are ticket-only and not in `src/`.
- Whether `boto3` is absent from the T4.1 import graph (only psycopg and sqlite3 were measured by the author).
- The round-2 resolve counts in line 3 (30 ids / 26 rows / 2 contested). I was told not to read `handover/reviews/`. CHANGELOG line 457 also says COR-12 was contested in part, which may make 3 contested rows.
- "Lead's relay errata for P4b1" (order 20 item 6) and the P4c revision 3 body. I checked names only.
- Nothing was run (no tests, no Postgres). The memo-2 "89 passed" claim and the 3.20 measurement were not re-run.
