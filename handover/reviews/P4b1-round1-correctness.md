# P4b1 ticket, round 1, CORRECTNESS review
- Reviewer: egm:egm-codebase-details (fresh, read-only, Sonnet 5.5). Ticket tickets/P4b1.md rev 1 (15d01fa). Nothing run.
- Result: BLOCKER 0, MAJOR 12 (C1-C12), MINOR 9, NIT 4 (C13-C25). Stop rule NOT met.
- Saved by the lead 2026-11-05, CONDENSED to one short line per finding (evidence dropped; the full text was delivered to the lead in chat). The author re-checks every claim in the code. Ledger BL-core-p4b1-r1-cor-*.

| id | sev | problem / fix |
|---|---|---|
| C1 | MAJOR | `OverBudget((which+"_budget",))` gives `day_budget`/`month_budget`, but `limits.py:27,29` print `daily_budget`/`monthly_budget` (T2 expects `("daily_budget",)`, P4c `WALLS`). Fix: explicit table day->daily_budget, month->monthly_budget, run->run_budget + mutant. |
| C2 | MAJOR | `run_id` iff run cap not None conflicts with P4d-b (allows `run_id` with `run_cap=None`) and P4c-2 R6 (loop passes `run_id` on every reserve); `max_run_usd` optional in dev (`registry.py:53`, `deferred.py:62-63`). Fix: allow `run_id` with `run=None`; tell P4c. (Same as adversarial A2.) |
| C3 | MAJOR | Written against P4d rev 4 ("all four" PRs; rev 5 has five); Needs 2-7 already adopted; only Need 1 (settle above reserved) open and rev 5 keeps it as ValueError. Rebase on rev 5, cite lines. |
| C4 | MAJOR | `OverBudget` carries only names; P4c needs `which`, cap, current, requested and the UTC day (a refusal returns no `Hold`); P4c mutant m4 unkillable. Make them unconditional. |
| C5 | MAJOR | Overshoot turns the GLOBAL kill switch on (PENDING LEAD 4); P4c rule 6/T6 expect per-run `NEEDS_PERSON run_budget`, audit `guard/estimate_exceeded`, no stop. Reconcile and tell the lead which. |
| C6 | MAJOR | Overshoot fallback: no rule that excess is booked only on `applied=True` (retry/second process loses or double-books); stored row says reserved so replay cannot give `charged=actual`. Prefer the lead accepting P4d Need 1. (Same root as adversarial A1.) |
| C7 | MAJOR | `Config.meter` (`cap_zone`, `max_hold_s`) has no path into `Limits.hold` (`app.py:171` builds `Limits(store,audit,reg)`; `app.py` not in Files, a hot file); non-UTC zone splits the "ONE counter" (`limits.py:18,24` use UTC). One day function; T2 `Asia/Kolkata` row across 18:30 UTC. |
| C8 | MAJOR | T5 settles inside the run so grants can exceed `floor(cap/amount)`; -b 8-thread row same flaw (P4d B4(i) holds open until a second barrier). |
| C9 | MAJOR | T6 registers `@kind("meter", name)` but conftest only builds fixtures per capability via `_kinds("store")` (lines 29-70); nothing consumes `KINDS["meter"]`; conftest is a hot file. Local fixture or add the edit with hot-file order. |
| C10 | MAJOR | Fail-before copies only the T2 file to ce70eb5, but it imports `hadavin_sdk.money`/`meter` (collection ImportError, not AssertionError). Lazy imports or a separate file. |
| C11 | MAJOR | Step 0 table: gate 1 still fails A for `Decimal` though A1(3)/A9 B1 say that is no longer a reason; owner notice says Intake settles the same reservation twice "right" while the table says D raises. Rewrite in plain words. |
| C12 | MAJOR | -c "holds a `Limits`-style handle": `Limits` needs `Registry` and `AuditSink` the demo lacks; `worst_case_usd` (`pipeline.py:23,145`), `remaining()`, `snapshot()`, `check()`, `charge()` have no disposition. (-c is to be removed/BLOCKED per adversarial A9.) |
| C13 | MINOR | -b fail-before shim fails because nothing exists; label "new feature; killed by mutants". |
| C14 | MINOR | `Hold.record(..., halt=)`: no callback/stop call/test; define or remove. |
| C15 | MINOR | T4(b) import allow-list omits `hadavin_sdk.money` (and stdlib `zoneinfo`, `contextlib`, `logging`). |
| C16 | MINOR | M10 claims a T5 row that is absent; M18 claims a T2 kill-switch row that is absent; missing mutants (release on OverBudget/store_busy, `Limits.caps`, `Settled.applied`, `record(halt)`, `charge(BusinessMoney)`, `prompt_bytes`). |
| C17 | MINOR | Only `reserve` error mapping specified; add one table for settle/release; `NotFound` on reserve for an unknown run is named `unknown_reservation` (misleading). |
| C18 | MINOR | Does not say how "1 byte/token" relates to `llm/common.estimate_tokens` (3 chars/token, `:59`), `k1b/loop.py:115 worst_case_usd`, demo `worst_case_usd` (`tests/demo_askdata/test_meter.py:32` pins it). |
| C19 | MINOR | `zoneinfo` not used in core; `tzdata` Windows-only in `uv.lock`; use `datetime.UTC` for default or pin. |
| C20 | MINOR | memo-2 gap 6 overstated (`Hold.age_s()` logs one line; sweep uses DB clock). |
| C21 | MINOR | PR #48 numstat claims UNVERIFIED by the reviewer; builder re-measures. |
| C22 | NIT | T2 "1.20 or less, in fact at most 0.80": 1.20 exceeds the 1.00 cap. |
| C23 | NIT | P4d rev 5 line 11 lists P4b1 among editors of `store/protocol.py`/`postgres.py`; P4b1 says none; record the deviation. |
| C24 | NIT | "Existing core code reused" lacks what was checked and rejected. |
| C25 | NIT | Literals (`2` in `orphan_age_s`, `{1,40}`, 3, 16) vs "no other number in `meter.py`". |

Verified by the reviewer: demo defect arithmetic (0.2 vs 1.1), race arithmetic, no psycopg/sqlite3 on import paths (plausible), Intake file sizes and line cites, MANIFEST ids, parity arithmetic, 17 template fields, memo-2 gap rows.
Model used: Sonnet 5.5 (set by the lead).
