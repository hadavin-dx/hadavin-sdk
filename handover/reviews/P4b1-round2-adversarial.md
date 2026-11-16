# P4b1 round 2, adversarial review (ticket rev 2, 374 lines) - agent a212246bf98d8f4ba
Status: REPORTED (saved by the lead session from the reviewer's hand-back, model output, not user authority)
Reviewer: a212246bf98d8f4ba (read-only)
Verdict: no Blocker; 4 Majors (R2-ADV-1..4), 10 Minors, 4 Nits

R2 adversarial review of handover/tickets/P4b1.md (rev 2). Main-checkout cites were read in the main checkout; P4d line numbers are from handover/tickets/P4d.md as it is now.

## Majors

| id | sev | ticket line | problem | fix |
|---|---|---|---|---|
| R2-ADV-1 | Major | 24, 138 (T4.4), 118 (T1.26), 68, 94 | T4.4 says that apart from 0, 1 and -1 no number may appear in `meter.py` or `money.py`. But the ticket needs `to_usd()` at exponent -6, `check_usd(x, max_decimals=6)`, `MAX_USD x 10**6`, and the 1..3600 check on `max_hold_s`. None of these has a constant. The constants list holds only `MICRO_PER_USD`, not a decimals count or 3600. The builder must either fail T4.4 or invent constants, which is a decision left to guess. M52 is also unkillable as written for any literal the builder derives (for example `len(str(MICRO_PER_USD)) - 1`). | Add to the -a block: `USD_DECIMALS = 6`, `METER_MAX_HOLD_MIN_S = 1`, `METER_MAX_HOLD_MAX_S = 3600`. Say that `MICRO_PER_USD` is used for the bound. Or say that T4.4 exempts the exponent. |
| R2-ADV-2 | Major | 234 (call flow), 248 (R4d-2), 289 (W19) | The unknown-attempts count is read from "the attribute P4b2-a's `with_retry` exposes". That attribute sits on the inner model, which is one object shared by every thread and scope (A8). Two concurrent chats overwrite or reset it. One call then books another call's timeouts, or loses its own, so spend is under-booked on the safe-direction-violating side. R4d-2 uses a single-threaded stub, so W19 is killed while the race is not. The name is also provisional. | Require a per-call channel: either a ContextVar set inside the retry wrapper, or the count carried on the `Reply` or the exception. Add an 8-thread row where each call has a different timeout count, and assert that each books its own count. List it as a coupling P4b2 must meet. |
| R2-ADV-3 | Major | 232, 371 | The byte bound is called a "worst case", but it is wrong for non-text documents. Images are billed by pixel area, not bytes, so a tiny highly-compressed PNG can cost far more than 3 x its bytes. PDF pages are billed per page as text plus image. The ticket marks this UNVERIFIED and leaves it to the builder. Overshoot is booked in full at settle, so the books stay right. But the reservation and the cap are not a bound, and 8 concurrent calls can all overshoot. A "state it in the evidence" step is not a fix. | Until a per-type bound exists, `MeteredLLM.chat` should refuse (`ValueError`, before any reserve) any `documents` entry that is not decoded text. Add a row for it. Otherwise add a hostile-document test with a pixel-count bound. |
| R2-ADV-4 | Major | 232, 235, 241 (PL59), 301 table row "Usage classes" | `Reply.usage` has input and output only. If the adapter fills `input` from a vendor's `input_tokens`, then cache-write and cache-read tokens are in neither the reservation nor the settle. The result is a systematic under-count, not just an overshoot, once prompt caching is on. Bible R216/R335 and the cost rules want caching. The ticket only says "cache write not covered" for the reservation. | Either add a row asserting that the P4a usage type cannot carry cache classes, or make the wrapper refuse a request carrying a cache marker until P4a/P4b2 adds cache classes. Say which one P4a does (UNVERIFIED). |

## Minors and Nits

- R2-ADV-5 Minor (money), 235/247: `max_attempts` has no upper bound; a huge value makes `count x attempts x W` exceed `MAX_USD`, `SpendMicro` raises `ValueError` in the error path and replaces the `ProviderError`. Fix: cap attempts (`METER_MAX_ATTEMPTS`), define the over-`MAX_USD` behaviour, add a row.
- R2-ADV-6 Minor, 21/72/105/143: after `StoreBusy` on reserve no release is attempted, but each `reserve` makes a new id so a retry cannot replay; a committed first attempt is an orphan and the month counter stays inflated. Fix: state P4d's `StoreBusy`-after-commit behaviour; retry with the same id inside `reserve`, or make a release-on-sweep rule a PENDING P4b2 item.
- R2-ADV-7 Minor, 131/258/140: barrier placement in T2.8 and B10 is ambiguous (inside the hold body the refused threads never arrive and the test deadlocks). Fix: barrier before the reserve plus an Event/counter that refused threads also trip; in B10 release the 3 `chat` calls when 8 reserves are answered.
- R2-ADV-8 Minor, 118/167: `clock().astimezone().date()` equals UTC in a UTC container, so that M16 variant survives. Fix: T1.30 sets `TZ` to a non-zero-offset zone (`time.tzset()`) and checks 23:59:59 and 00:00:00 UTC.
- R2-ADV-9 Minor, 21/157/201/101: the `conflict` row for `StaleState` on settle/release is unreachable on real stores (P4d `settle_spend` returns the stored first result); M50 is killable only on a fake. Fix: mark the row defensive and fake-only, or drop it and M50.
- R2-ADV-10 Minor, 74/109: `release` then `settle(real cost)` silently returns the `released` first result with `applied=False`; the paid cost is lost with no signal. Fix: code-only log line and counter, or a `Settled.superseded` field; add a row.
- R2-ADV-11 Minor, 33/81: no test for a `SpendMicro` that overflows `MAX_COUNTER_USD`; behaviour of `Limits.blocked`/`charge` above the ceiling is unstated. Fix: one row showing a counter above the ceiling still blocks and does not raise.
- R2-ADV-12 Minor, 74/77: a route with both prices 0 gives W = 0 and `reserve` raises; an answered call with cost 0 makes `record(SpendMicro(0))` raise `ValueError` and replace the reply. Fix: refuse zero prices at construction or let `record` take a 1-micro minimum; add a row.
- R2-ADV-13 Minor, 22/23: the live-call gate and "never release a sent call" are process rules only; nothing stops a paid kind using `MeteredLLM` before P4c-2 and P4b2-a merge. Fix: name the gate owner (P6a or P4a PL51), add a test or CHANGELOG note and a lead-checklist item.
- R2-ADV-14 Minor, 123 (T2.7): a hold with a `run_id` that has no `runs` row (`unknown_run`) is untested. Fix: add a row, refuse and write nothing.
- R2-ADV-15 Nit, 265/266: B17 is labelled "regression pin (NOT fail-before)" but fails on the old code, so it is a fail-before. Fix: relabel.
- R2-ADV-16 Nit, 138 (T4.1): the assertion lists `boto3` but only `psycopg` and `sqlite3` were measured. Fix: measure `boto3` once.
- R2-ADV-17 Nit, 102 (T1.10): types of `OverBudget.cap/current/requested` unstated. Fix: state the type.
- R2-ADV-18 Nit, 4 vs 1: line 1 says "no round cap", line 4 says 3 rounds (order 20 item 6). Fix: line 1 -> "capped by order 20 item 6".

## Verified
- `limits.py` cites at 18, 24, 26, 27, 29 are correct and `Limits` has no `hold`/`caps` yet; `models.now()` returns `datetime.now(UTC)`; `missing_methods` at `store/protocol.py:151`; `StaleState`, `NotFound`, `new_id` exist.
- Arithmetic for P1, P2, P8, P14 (6,620 and 26,480; 333,334 gives 1; (3,7) gives 38), `orphan_age_s` (599 at 297, 601 at 298), T2.8 (0.80), 723/2,093 sums, M-count 50, W-count 23.
- All 17 template fields present in -a and -b; the only lack is a true fail-before for -b (see ADV-15).
- P4d settle semantics match the ticket; order 20 item 6 allows a 3-round cap with one extra for a money package with at most 2 Majors.

## Not checked (UNVERIFIED)
- Anything in P4a, P4b2 or P4c beyond the ticket's quotes (`request_bound`, `UsageMissing`, `unknown_attempts` name); `defaults.MAX_USD`; `check_usd` semantics; P4d `StoreBusy` never raised post-commit.
- Cites `llm/common.py:59/:92`, `registry.py:53`, `agent_loop.py:240/440`, `tests/test_s5_runtime.py:109-128`, `backends/table.py:37/593`; intake source files, the PR #48 branch and numstat figures; PROMPT_BYTES_PER_TOKEN being 1; Postgres behaviour; nothing was run.
