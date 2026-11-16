# P4b1 round 3, adversarial review (ticket revision 3)

Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

Reviewer type: egm:egm-design. Read-only.

TICKET REVIEW round 3 (adversarial), handover/tickets/P4b1.md revision 3 (read in full, 459 lines plus a blank).

Verdict: 0 Blockers, 2 Majors, 7 Minors, 3 Nits. By the order 20 item 6 rule (no Blocker and at most 2 Majors), a round 4 is allowed. The 2 Majors are small edits. If R3-ADV-1 and R3-ADV-2 are applied as build notes, a round 4 may not be needed.
Nothing was run. No Postgres was available. P4a, P4b2, P4c and P4d facts are from ticket text only (UNVERIFIED in code). The core copy at src is assumed equal to ce70eb5 (UNVERIFIED).

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-ADV-1 | Major | 111, 148, 154, 156, 292 (T2, B10); 240 (fail-before) | The `store` fixture is defined only in `tests/contracts/conftest.py:29-31`. pytest does not expose it to `tests/test_meter_limits.py` or `tests/test_meter_llm.py`, which are not under `tests/contracts/`. Line 111 says the contract fixtures are used, but line 111 places T2 outside `tests/contracts/`. The T2 file would fail to collect ("fixture 'store' not found"). The ticket also says `conftest.py` is untouched, and `tests/conftest.py` has no `store`. A tests/conftest.py move would be a hot-file edit that no ticket assigns. | Put T2 in `tests/contracts/test_meter_limits.py` (the fixtures are then visible, and `ce70eb5` has `store` so the fail-before copy still collects). Or have T2 build `MemoryStore` plus `Limits` itself and run Postgres only through `pg_schema`. State the choice. Do the same for B10 and any `test_meter_llm.py` row that needs a store. |
| R3-ADV-2 | Major | 102 ("the books can only be too high"); 268 | False when the planned amount is above the reservation. The wrapper's failure booking is `count x attempts x W`, which is above `count x W` (the reservation) when attempts > 1. A measured overshoot also plans above the reservation. If the exit settle then fails (`StoreBusy` after 2 retries, or `CounterDamaged`), the row stays open at the reservation. The counters are under-booked by up to `count x (attempts-1) x W` (up to 9W with the fallback of 10 attempts) until an operator repairs it. Order 14(3) says "never below the bound". Settling at the reservation instead would close the row and make the later repair settle a replay that returns the first result, so that is not a fix. | Reword line 102 to say the books are too high only when planned <= reserved. For planned > reserved they are too LOW by planned minus reserved until the repair. Add this to the -a rules: `on_settle_failed` and the log must carry `planned` (they already do), and P4c-2's audit row must carry it. Add a test row that, for planned > reserved, asserts `SettleFailure.planned` is the larger figure and the store still holds the reservation. Tell the lead plainly (PENDING LEAD 15). |
| R3-ADV-3 | Minor | 261, 301 (B19) | The "second line of defence" in `worst_case_micro` checks only that the micro price is a whole number. `config.py:40-47` `Money` has no sign or finiteness check (read in code). `Infinity == Infinity.to_integral_value()` is True, so `int()` then raises `OverflowError`, which is not the stated `ValueError`. A negative price is a whole number and passes. With one negative price and one large price, W is under-sized. `sNaN` raises `InvalidOperation`. B19 tests only a 7-decimal price. | Route both prices through `check_usd(x, max_decimals=MICRO_DECIMALS)` before multiplying (finite, not signed, at most 6 decimals). Add B19 rows for `Infinity`, `-1` and `NaN`, built with `model_construct`. Add a mutant for each. |
| R3-ADV-4 | Minor | 103, 99, 95 | `on_overshoot` for a standalone `Meter.settle(id, amount)` is unspecified. Only a `Hold` carries `measured`. The operator repair settle (line 102) and the T5.3 crash-recovery settle (`Meter.settle(id, None)`) run with no scope and no `measured` flag. P4c-2 reads the run from the open scope, so a callback there would find no run. | State: `Meter.settle` and `Meter.release` never call `on_overshoot`. They still write the WARNING `overshoot` and `superseded` lines. Only the exit of `Meter.hold` signals. Add a T1.20 row and a mutant. |
| R3-ADV-5 | Minor | 268, 408 (PL17) | Any non-`ProviderError` exception after `inner.chat` started (a `KeyboardInterrupt` during a retry, an adapter `KeyError`, or `ValueError` from `round_cost_up`) books only `count x W`. Earlier attempts in the same chat may already have been billed. This is below the whole-call maximum that orders 14(3) and 19 D accepted. PL17 acknowledges the difference, but the ticket still builds the lower figure. | Book `max(reserved, count x attempts x W)` for any exception that escapes the body after the call was sent. Or get the lead's explicit yes in PL17 before the build. The fake-only note on line 48 does not justify a lower bound on a money path. |
| R3-ADV-6 | Minor | 240 (evidence 4) | The fail-before command is `uv run ... pytest <dir>/tests/test_meter_limits.py -k check_then_spend` with no working directory. From the main tree, `uv run` imports the editable NEW `hadavin_sdk`, so `Limits.hold` exists and the shim takes the new path. The row would pass, not fail. | Write `cd <dir> && uv run ...`. Add a step that prints `hadavin_sdk.__file__` into the saved evidence and checks it lies under `<dir>`. |
| R3-ADV-7 | Minor | 241 (evidence 5) | `PYTHONPATH=... python -I` cannot work, because `-I` ignores `PYTHON*` variables. The Intake modules would not import. | Use `python -s -c` with `sys.path.insert` in the script, or run `pytest` with `-p no:cacheprovider` and `PYTHONPATH` (no `-I`). |
| R3-ADV-8 | Minor | 49, 52 (M52), 166 (T4.4) | Line 49 says "No other number is written in `meter.py`, `money.py` or `llm/metered.py`", but T4.4 and M52 scan only the first two. `metered.py` has the 3 and 16 bytes, the 100,000, and the 1,000,000. | Extend T4.4 and M52 to `llm/metered.py`, or reword line 49. Also fix the `-b` constant check: a literal in `metered.py` currently survives. |
| R3-ADV-9 | Minor | 49, 267 (`METER_ABSURD_TOKENS = 10**9`) | P4a-1 already defines `MAX_USAGE_TOKENS_PER_CLASS = 1_000_000_000` (`P4a.md:525`) and refuses the same usage before a `Reply` exists. A second constant with the same value can drift and gives the same garbage rule two sources. | Import P4a's constant. Drop `METER_ABSURD_TOKENS` (the constants count then becomes 4). Or state why a second bound is needed. |
| R3-ADV-10 | Minor | 263, 279 (R4c), 407 (PL16) | The tier bound is on the BYTE bound, because `PROMPT_BYTES_PER_TOKEN = 1` (`P4a.md:525`). A prompt over 100 KB is refused. Documents count 3x, so a document over about 33 KB of raw bytes is refused, whatever the real token count. This is stated nowhere as a consequence. | Add one plain sentence to the -b CHANGELOG ("prompts over 100,000 bytes, or documents over about 33,000 bytes, are refused, whatever their real token count"). |
| R3-ADV-11 | Nit | 88, 253 | -a "Depends on" P4a-2 although -a "imports none of P4a's names". This delays -a for no reason. The order 20 chain places P4a last. | Say -a needs only P4d and P2a-1. P4a-2 is a -b dependency. |
| R3-ADV-12 | Nit | 88 | Says "P2a-1b". Order 7(3) merged P2a 1a and 1b into one PR (P2a-1). The ticket also states `Limits.stop` is no longer used, so this is only a hot-file ordering. | Write "P2a-1". |
| R3-ADV-13 | Nit | 140, 212 (T1.23, M33) | "`StoreBusy` three times" gives `store_busy` after 3 attempts (1 + 2 retries). M33's "retries more than the constant" is killed only if the test asserts exactly 3 `settle_spend` calls. It does not say so. M47 (no lock on first `Limits.hold`) is killed by T2.10 only if the build is slowed. A fast build can pass by luck. | T1.23: assert exactly 3 calls. T2.10: put a barrier or `sleep` inside the `Meter` constructor stub so two threads overlap. |

Smaller items (not in the table)
- Line 244 vs line 238: line 238 requires `HADAVIN_REQUIRE_PG=1` and treats a skip as a FAILED run, but line 244 says no real Postgres is available in the cloud unless the lead supplies one. Say who starts the throwaway Postgres 17 (CI image `ci.yml:40`) and whether the cloud may.
- Line 100 and 134 (T1.17): the case where a release wins over a settle books 0 for a call that WAS sent. This is under-booking by design (the `superseded` WARNING is the only signal). Within -a/-b it cannot occur, because the wrapper never releases a sent call. P4b2 must not call `release` for a sent call. Add one line in the -a "Caller rule".
- Line 258: `NetworkLLM` stores `dict(deps.routes)`, a copy. The "same mapping object" requirement therefore applies only to the wrapper. B9's "by identity of each `Route`" is correct. Reword so nobody reads it as the wrapper sharing the inner's dict.

Verified (read in code or by arithmetic)
- limits.py:8 binds `now` at import. Lines 17-30 are as described. `charge` returns a tuple.
- agent_loop.py:240, 314-315, 440-441 are the check and charge sites.
- models.py:19-24 (`now` is UTC-aware, `new_id`), Reply at 289-297.
- config.py:47 (Money is a plain Decimal with no sign or scale check), 55-59 (Route).
- registry.py:35-36 and 53.
- table.py:37-40: the `max_attempts` default is 3 with `ge=1, le=10`.
- common.py:59-62 (3 characters per token) and 86-92 (documents decoded with replacement).
- NetworkLLM defines `max_attempts` and `chat` at common.py:206-208. No kind overrides `chat`.
- store/protocol.py:25 (`StaleState`), 45 (`NotFound`, a `KeyError` subclass), 151 (`missing_methods`).
- guard/injection.py:85 and 89.
- fake.py:39 and 54.
- test_s5_runtime.py:109-128 kills M29.
- ci.yml:40 is Postgres 17.10.
- `pg_schema(runtime=...)` exists at store_postgres.py:18.
- tests/contracts/conftest.py has no `meter` fixture. `store_pair` is P4d's.
- Arithmetic: W for 4,000 bytes at prices 3 and 15 with `max_tokens` 1,024 is 27,360. P14 gives 6,620 and 26,480. P2, P8 and P1 hold.
- Counts add up: T1 30, T2 16, T3 14, T4 4, T5 5, T6 8 gives 77. -b has 7 R4 rows plus B1-B21 gives 28, total 105. M1-M55 minus 3 gives 52. W1-W30 minus 1 gives 29. Constants 8 and 5. Seven error codes.
- The release table is internally consistent with T1.12, T1.13, T5.4 and mutant M43.
- T1.30 and T2.6 kill the `astimezone()` variant of M16, because `now()` returns an aware UTC datetime.
- All 17 template fields are present in both -a and -b. The -b "Done" says "as -a", which is fine. The -b contract-suite item is not applicable.
- No real-looking secret in the file. The DSN is built from parts.
- Couplings: P4c.md:34, 106 and 171 name P4b1-a and -b as dependencies and match the names here.
- Amendments A9 B1 (exponent -6, no migration), A11 (no `store/*` edit) and F6/A4 hot files (deviation stated) are respected.
- Orders 14(3) and 19 D are satisfied for `ProviderError` (`count x attempts x W`).

Not checked
- Everything from P4a, P4b2, P4c and P4d is ticket text only: `check_usd` location (`store/protocol.py` per `P4d.md:293`), `MAX_USD`, `request_bound`, `UsageMissing`, `Reply.unknown_attempts`, and whether P4a's `Price` refuses negative values.
- Whether `Reply` accepts the extra field.
- Postgres behaviour: the release after `StoreBusy`, the replay of a released id by `reserve_spend`, and the run, day, month cap order.
- Whether Python 3.12 exists in the cloud.
- The Intake `test_budget.py` conftest needs.
- The "lead's relay errata for P4b1" mentioned in order 20 item 6 (not in the files I read).
- The meaning of "PL7(a)-(d)" and the contents of `reviews/` and `evidence/` (not read, per instruction).
