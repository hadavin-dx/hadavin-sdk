# F-install hostile review 1 (branch local/code-FI4, HEAD e686b1d88)
Read-only review. Files: src/hadavin_sdk/runtime/agent_loop.py, src/hadavin_sdk/guard/model_gate.py, tests/test_agent_loop_never_working.py, tests/test_model_gate_install.py, tickets/F-install.md. Two probes were run against the worktree with fakes (a temp test file, removed afterwards; no source, test, commit or push change; no live model call). Line numbers are agent_loop.py unless named.

Verdict: the gate itself (model_gate.py) is sound on the settle rule and on text leaks. The new loop code has two confirmed holes where a run still ends WORKING or the end is misreported, one inconsistency on the kill switch, and several lower items.

## Findings

### 1. HIGH (confirmed by reading; same pattern as probe 1) - audit fault in the new model_error branch leaves the run WORKING
Lines 573-576: `self._note(run, "llm", "chat", result="failed", error_code="model_error")` is called bare, BEFORE `_abstain`. `Runtime._note` (268) does not suppress; the gate's own `_note` does (model_gate.py:334). If the audit sink raises, the exception escapes `handle` from inside the except block and `_abstain`/`_end` never run.
Scenario: the audit store is down or the sink raises on that row while the provider raises ValueError (or any non-ProviderError). Result: the ticket's goal "a run never stays WORKING on a client fault" fails exactly when two faults coincide; the hold stays booked (correct), the run stays WORKING until tick. Probe 1 confirmed `OSError` escapes `handle`.
Fix direction: write the row with the same suppress used for cards (`_note_card` style), or drop the row (the gate already wrote `call_failed`) and end first.

### 2. MEDIUM (confirmed by probe 2) - `_end` retry is not idempotent: a committed end is reported as RunEndFailed
`_end` (396-409) retries `_to`, which is transition + audit `_note` (386-390). If the transition commits and the audit write (or a lost store reply) raises, attempt 2 reads state NEEDS_PERSON, `check()` (runs.py:31) raises IllegalTransition ("is final"), so both attempts fail and `RunEndFailed` is raised even though the run IS ended. Probe 2: first `run/state` audit write raises once, result `RunEndFailed ... NEEDS_PERSON (model_error)`.
Scenario: one audit hiccup while ending. Consequences: the caller is told the run could not be ended (it may retry or alarm), the abstain card is never posted, and the `run/state` audit row is missing. Not WORKING, so not the worst case, but the "retried once" claim is false for the audit half.
Fix direction: on retry, re-read the run; if it is already in `new` with the same reason, only write the missing note (suppressed) and carry on; or separate transition (retried) from note (suppressed).

### 3. MEDIUM - `_limits_stop` still uses a single `_to` with no retry (278-292), including the kill switch
Lines 282, 284, 286 call `_to`, not `_end`. The fix covers `_abstain` and `_refused` only. A single store fault while writing STOPPED/kill_switch, NEEDS_PERSON/limits.*, or limits_unavailable raises raw out of `handle` with the run WORKING. `_limits_stop` runs at every step and after every tool, so it is the most frequent ending path and the one that matters most (kill switch).
Same family, unchanged and unguarded: `self._to(run, S.WORKING)` (469; transition commits, audit note raises -> handle raises with run WORKING), `self.store.touch` (527), `self.store.get_run(...)` in the cap check (287), `_shadow`'s final `_to` (~line 800) and any `_to` in `_submit`. If the ticket's claim is "never WORKING", these contradict it; if it is scoped to client faults, say so in the ticket.

### 4. MEDIUM - non-client faults from the gate are labelled `model_error`
`BoundGate.chat` re-raises whatever `worst_case` or `meter.reserve` raised (model_gate.py:241-245), and only `SpendRefused` is caught by the loop (545). Any other Exception there (the meter's store down raising StoreUnavailable, a ValueError from worst_case, a TypeError from a custom meter) now lands in the new `except Exception` (573) and ends `NEEDS_PERSON model_error`, with an `llm/chat failed model_error` row, although no model was contacted and nothing is a client fault. The ticket maps limits trouble to `limits.<reason>` / `limits_unavailable`. Scenario: Postgres meter outage -> run says model_error, the operator looks at the provider. Also double audit rows: gate writes `reserve_refused`/`call_failed`, loop writes `model_error` for the same call (one failure, two llm/chat rows; counts of failed model calls are inflated).
Fix direction: have the gate wrap non-Spend reserve faults in a GateRefused subclass (code `reserve_unavailable`), or map exceptions from reserve to limits_unavailable.

### 5. MEDIUM-LOW - exception chain can carry model/prompt text (module promises none)
`RunEndFailed` is raised from `_end` while the outer `except Exception:` (573) or `except ProviderError` (566) handler is still active, so `__context__` is the client exception (its text may hold the prompt or a document value, as the tests' SECRET does). `from failure` sets `__cause__` to the store's exception (whose text may hold SQL values). The message is clean, but a worker that logs `exc_info`, `repr(exc.__context__)` or walks the chain, or Sentry-style capture, will emit both. model_gate.py's docstring forbids exception chains in what it raises; the loop's new error does not follow it. The test (102) only checks `str(info.value)`.
Fix direction: `raise RunEndFailed(...) from None` and clear context (`exc.__context__ = None` via a raise outside any except, e.g. return a sentinel from the handler and raise after it), keep the store fault only as a class name in the message.
Related, pre-existing: `injection_check` logs `safe_head(str(exc), 300)` for a judge client fault (injection.py:243); the judge's model fault text can contain the screened text. The text is already redacted, so Low.

### 6. LOW - BaseException (cancel, KeyboardInterrupt, asyncio.CancelledError, SystemExit)
- During `llm.chat`: the gate notes `call_interrupted` and re-raises with the worst case still booked (model_gate.py:266-268). Correct per rule (c). The loop catches only Exception (573), so the run stays WORKING, deliberately left to tick's stuck-run rule (heartbeat `touch` at 527). Document that; there is no test of it (no test uses KeyboardInterrupt in either new test file; the gate tests may, check before claiming coverage).
- During `meter.settle` (`_settle`, model_gate.py:282-286): `except Exception` does not catch it, so no `settle_failed`/`ok` row and the paid reply is lost; the reservation is either settled or kept at worst case, never doubled. Bookkeeping loss is only the audit row.
- During `meter.reserve` (240): if the store committed the hold and the interrupt lands before the id is returned, an orphan hold exists with no id, no row, no way to settle; only the sweep (3600 s) closes it. Unfixable in the gate; mention it in the ticket's stated limits.
- `_end` catches `Exception` only, so an interrupt between the two attempts leaves the run WORKING (fine, same tick rule).

### 7. LOW - billed answer after a client fault
The gate's rule (c) keeps the worst case booked and the run's `cost_usd` is not increased (the store adds cost in settle). So a run that ended `model_error` after a billed-but-unparseable reply shows cost 0 and holds worst case until the sweep; `max_run_usd` (287) never sees that spend. No double settle, no settle of an unknown cost, which is the rule; but the per-run cap is blind to it. Retrying run/agent loops could chain several such holds up to the daily budget before the sweep. Accept and state, or forfeit-at-worst-case into the run cost.

### 8. LOW - double settle
None found in the gate: one `_settle` per call, rule (b) and (a) are exclusive, a raising settle is never retried (model_gate.py:278-286). No other `.settle(`/`.reserve(` site exists in src outside the gate and limits.py/k1b. The new `_end` retry does not touch the meter. The reply path after a settle failure still returns the reply (correct).

### 9. LOW - text and secret leaks
Checked: reason codes are fixed strings (`model_error`, `provider_error`, `provider_exhausted`, gate codes); audit rows carry codes and ids only (model_gate.py:334-345; agent_loop 575); the abstain card label is `_REASON_TEXT.get(reason, reason)` = the code. `model_error` is not in GUARD_STOP_REASONS or `_REASON_TEXT`, so the card reads literally "model_error": acceptable but unfriendly. Only chain leaks, item 5. `exc.code` for a GateRefused subclass is a class attribute; fine.

### 10. LOW - test gaps
- No test for item 1 (audit raising in the model_error branch), item 2 (commit then note fail), item 3 (`_limits_stop` single fault), item 4, or any BaseException.
- `test_a_client_failure_writes_no_raw_text_to_the_audit_trail` checks `repr(events)` only; not the card, not `__context__`/`__cause__`.
- `_fail_transition` raises before the store commits, so it cannot model commit-then-fail, which is why item 2 passed review.
- The old test change (test_model_gate_install.py:617-625) keeps the hold-kept assertion: good.
- `test_two_store_faults_in_a_redaction_failure_ending...` relies on `reserve_spend` down to reach a refusal path: good but does not assert the run state (store says WORKING there; assert it, to document the residual).

## Summary table
| # | Sev | Where | One line |
|---|-----|-------|----------|
| 1 | High | 573-576 | bare `_note` before `_abstain`: audit fault leaves WORKING (probe confirmed) |
| 2 | Med | 396-409, 386-390 | retry not idempotent: commit-then-note-fail becomes RunEndFailed (probe confirmed) |
| 3 | Med | 278-292, 469, 527 | `_limits_stop` (kill switch) and other `_to` sites have no retry; still WORKING on one fault |
| 4 | Med | 573 vs model_gate.py:241 | non-Spend reserve/worst_case faults mislabelled model_error; double rows |
| 5 | Med-Low | 409, 566-576 | RunEndFailed carries client and store exceptions in context/cause |
| 6 | Low | model_gate.py:240,282; 573 | BaseException: worst case kept, run WORKING by design; settle interrupt loses the row |
| 7 | Low | model_gate.py:263 | billed-after-fault spend is held, not in run cost |
| 8 | Low | - | no double settle found |
| 9 | Low | 575 | no raw text in codes/rows/cards; card reads "model_error" |
| 10 | Low | tests | gaps listed above |
