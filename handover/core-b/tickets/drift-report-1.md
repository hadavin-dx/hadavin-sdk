# Drift report 1: core-b tickets A, B, C, F and interfaces vs src/hadavin_sdk (branch cloud/core-b, HEAD d0b2c4d90, read 2026-11-20)

Notes: there is no D ticket file (only D-config-review-1.md, excluded by the rule), so D has no section. F-install says its install is built on wip/cloud-core-b/F-install; this checkout is cloud/core-b, so "missing" below means missing on this branch. Paths are relative to src/hadavin_sdk.

## A-audit-drain.md

- Section A5 is marked "OPEN, fix round 3" but both parts are built: `_is_outage` (audit/chain.py:76-90) with the SQLSTATE rule (OSError, StoreUnavailable, InterfaceError, OperationalError with no SQLSTATE or 08/57P), used at audit/chain.py:271 and :323; and the once-per-run retry of `_unwritable` (audit/chain.py:299-301). The doc state is stale.
- Invariant 2 in the main text ("stops at the first failure", tickets A line 12 and Files line 13) differs from the code, which stops only on an outage and moves a non-outage refusal to `_unwritable` (audit/chain.py:269-280). A2 already overrides this, so only the unreconciled body text differs.
- Code in the touched modules that no doc mentions: `_flush_lock` (audit/chain.py:193, only implied by "safe for two threads"); the warning line `audit pending flush: written=%d not_writable=%d ...` (audit/chain.py:283-289) and `audit outbox: drained=%d unreadable=%d not_writable=%d not_deleted=%d (kept)` (audit/chain.py:342-348); `audit_drain` logs `drained=%s` at INFO (runtime/tick.py:260), which the doc does state, but the two chain.py warnings are not stated.

## B-stop-state.md

- [owner: step B, other lane] No drift detected between the ticket (incl. RESOLUTION S1-S12 and ADDENDUM) and the code in store/migrations/0006_stop_state.sql, store/migrate.py (Grant.reset :31, GRANTS :46-68 stop rows, reset block, `_CAN_CLEAR`/`who_else_can_clear`, `_FORBIDDEN_ROLES`), store/postgres.py:220-222 and :467-540, limits.py:204-217, cli.py:193-225 and :392-395 and :441-486, backends/table.py:124, app.py:188, runtime/agent_loop.py:254/721/791. who_else_can_clear is stated as being rewritten under lead ORDER 015, so it may drift again.

## C-price-constraint.md

- No drift detected (defaults.py:134; config.py:9, :84-98 `Route._price`, :478-491 `prices_as_of` and `_plain_date`, :537 `_price_refusals` call, :563-585 `_today` and `_price_refusals`; k1b/replay.py:85-90 kept as stated).

## F-install.md

- The model gate is not in the tree: guard/model_gate.py does not exist [owner: core-c lane], `runmap.enforce_map` does not exist in guard/runmap.py [owner: core-c lane], and there is no ModelGate, BoundGate, GateRefused, UnmaskedInput or NO_MAP anywhere in src. guard/producers.py:59 and :67 already list "guard/model_gate.py" (rows for a module that is absent).
- `Runtime._gate` / `bind` is not built: runtime/agent_loop.py:473 still calls `self.llm.chat(` directly (no gate, no reserve, no settle). No `.reserve(`, `.settle(` or `.forfeit(` call exists anywhere in src outside the Meter classes themselves.
- The old charge sites the ticket deletes are still there: runtime/agent_loop.py:327-329 (`_screen`: `limits.charge` + `store.add_cost`), :488-489 (reply charge), k1b/loop.py:156, :165, :192 (`budget.charge`); `Limits.charge` (limits.py:121) and `Budget.charge` (limits.py:67) still exist (ticket: both deleted).
- V5 says the loop's own "llm chat failed" note is removed; it is still written at runtime/agent_loop.py:486.
- No SpendRefused / GateRefused handling in the run loop (W1/V6): no `_refused` helper and no import of either in runtime/agent_loop.py. guard/injection.py:85 `injection_check` does not re-raise SpendRefused (V7), and there is no `bind` on `injection`, `JudgeDetector` (guard/judge.py:62) or `AnyOf` (guard/injection.py:61) (Z7, Z11). `_screen` (runtime/agent_loop.py:324) and `_shadow` (:648) have no `mapping` parameter.
- Y2 not built: `Reply.cost_usd` is `Decimal = Decimal(0)`, not `Decimal | None` (models.py:299); `reply()` still estimates missing usage with `estimate_tokens` at 3 chars per token and always sets a Decimal (llm/common.py:60-65, :251-280). Verdict docstring still says "charged by the caller" (models.py:310-312) and guard/judge.py:6-7 still says "the caller charges it".
- Y3/Z1 not built: no `Reply.attempts` (models.py:294-302); `with_retry` has no `record` parameter (llm/retry.py:165-175); `NetworkLLM._retry` passes none (llm/common.py:331-342); `Answer` has no `attempts` or `prior_known` (llm/common.py:283-290); openai_compat's second round sums tokens only, no ANDing of `prior_known` (llm/openai_compat.py:120-142).
- V3 not built: `evals.gate(registry, llm, agent_id, *, k=1)` has no `max_usd` (evals.py:35); evals.py:80 adds `reply.cost_usd` with no None check; the CLI `gate` parser has no `--max-usd` and builds no Budget (cli.py:96-98, :156-163). No stage rule (ConfigError in pilot/prod without a cap).
- W2/V4 only half built: `Budget.reserve/settle/forfeit(run_id)` with "usd_cap" exist (limits.py:71-111) but `run_case` never calls `forfeit` and still takes `route_prices` (k1b/loop.py:116, :155-156); k1b/loop.py:101-110 keeps its own `worst_case_usd` (3 chars per token via `estimate_tokens`, one attempt, no documents or tools) beside the shared llm/common.py:74 (ticket: "moves to llm/common.py").
- V9 not built: `_replay` does not refuse `acknowledge_masked` in pilot or prod (k1b/replay.py:119-123; no `is_live` or stage import in that file); replay builds `loop.Budget(max_usd)` at :136 and wraps no gate.
- Matches (no drift): `worst_case_usd`/`worst_case_for` (llm/common.py:74-161: six positional args, route name, unknown name priced at the largest, SpendRefused("bad_amount") on failure, requests = max_attempts x2 with schema), `defaults.WORST_CASE_OVERHEAD_BYTES = 4096` (defaults.py:155), extract.py deleted with its producers rows, Budget moved to limits.py and imported by k1b/loop.py:27.

## F-provider-mark.md

- The "fix round 1 ... QUEUED" paragraph (M1, M2, N3, N6) is already built on this branch: retry.py docstring says rule 2 is INERT (llm/retry.py:56-58), `OpenAICompatLLM.refused_statuses = {401, 403, 404}` (llm/openai_compat.py:78) fed through `NetworkLLM.refused_statuses` (llm/common.py:351) and `with_retry(refused_statuses=...)` (llm/retry.py:174), a truncated cause chain counts as not never-sent (llm/retry.py:108-134), and llm/protocol.py:15-17 carries the N6 wording. The "QUEUED" status is stale.
- Code that the doc does not mention in the touched modules: `transient()` treats a TLS certificate or protocol error (not an EOF/zero-return drop) as non-retryable (llm/retry.py:138-139); `retry_after()` honours a numeric Retry-After up to 8 s (llm/retry.py:148-156).

## F-store.md

- Reserve step 2: `Limits.reserve` also turns an unhashable agent id into KeyError (limits.py:147-148); not stated in R6.
- R6 says the amount check is "one helper" in store/protocol.py; the code has seven: `check_reservation_id` (store/protocol.py:72), `check_store_id` (:87), `check_spend_day` (:104), `check_spend_amount` (:111), `check_spend_cap` (:127), `check_purge_bound` (:147), `check_expiry_age` (:155). `check_spend_day` (a spend day must be exactly a `date`, ValueError otherwise, used at store/postgres.py:628 and store/memory.py:323) is in no ticket or interface text.
- R6 and Q10 do not state the 12-decimal and exponent window of an amount or a cap; code enforces it (store/protocol.py:111-142). (README 2.3 does state it.)
- Undocumented code in the touched modules: `Budget.charge` and `Budget.exhausted` (limits.py:63-69), not part of the Meter contract; `STORE_LOCK_TIMEOUT_MS = 10000` set on the connection (store/postgres.py:195, defaults.py:161), only in README point 14, not in this ticket; the memory store builds the row before touching the counter (store/memory.py:336-347).
- Open "sweep tick step" draft text says `expire_spend_reservations(defaults.RESERVATION_EXPIRE_S)`; code uses `reservation_expire_s` = max(3600, ceil(longest stuck_after_s)) (runtime/tick.py:263-276). This is the Q3 resolution, so it matches the resolution, not the draft body.

## interfaces/README.md

- Section 2 says the gate takes a Meter and calls `meter.reserve` / `meter.settle`, with two implementers "(Limits ... and k1b Budget ... for the eval and replay command lines)". No gate exists in the tree [owner: core-c lane], nothing in src calls `reserve` or `settle`, and the eval command line has no meter at all (evals.py:35, :80); only replay constructs a Budget (k1b/replay.py:136) and it still uses `Budget.charge` (k1b/loop.py:156, :165, :192).
- The "ProviderError.refused_before_response" paragraph (also in ii-meter.md point 7 area) lists HTTP 400, 401, 403, 404, 413, 422 for every kind; for openai_compat only 401, 403, 404 count (llm/openai_compat.py:78).
- Version 2.3 header and section 1 invariants 1 to 13 otherwise match store/protocol.py:51-160, store/postgres.py:612-743, store/memory.py:309-405 and limits.py:136-191. Not in this doc but in code: `check_spend_day` (store/protocol.py:104) rejects a datetime or str day with ValueError.

## interfaces/ii-meter.md

- Header says "The in-memory Budget meter arrives with step F-install"; `Budget` already exists in limits.py:41-111 on this branch (reserve, settle, forfeit, "usd_cap" = the sixth reason).
- Point 8 ("nothing calls Limits.charge for a gated call") and point 1 (gate calls reserve) describe the installed state; on this branch `Limits.charge` still exists (limits.py:121) and is called by the run loop (runtime/agent_loop.py:328, :488), and no gated call exists.
- Point 2 lists the amounts that raise SpendRefused("bad_amount") but not the more-than-12-decimals and exponent-window refusals (store/protocol.py:111-124, same check used at limits.py:142); point 4 says settle "with a bad amount raises ValueError" but a malformed reservation id also raises ValueError first (store/protocol.py:72-85).
- Provider-errors paragraph: status list is the generic six; openai_compat narrows to 401, 403, 404 (llm/openai_compat.py:78).
- Point 7 is matched by llm/common.py:74-161 (bytes, schema twice, overhead 4096, max_attempts, doubled with a schema, SpendRefused("bad_amount") on failure). Point 10 matched by runtime/tick.py:263-276. Point 14 matched by store/postgres.py:195.
- Reason-list in the SpendRefused docstring (limits.py:19-21) names six reasons, as the doc says; the interface file ii_meter.py (not in scope) still names five.
