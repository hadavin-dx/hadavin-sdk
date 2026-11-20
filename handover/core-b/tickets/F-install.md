# TICKET F-install: install the model gate in every consumer, delete the old charge sites, delete extract.py (owner core-b SPINE)
Written 2026-11-20 05:33 UTC from the lead's draft (inputs/draft-ticket-F-install.md, kept word for word below the line). Path class: money. Migration: none. Depends on: F-store built; core-c's gate module for commit 5. Ticket review: one EGM round together with F-store and core-c's gate ticket. NO source code before GO BUILD F.

## core-b's corrections to the draft's "Assumed" paragraph (now decided, see interfaces/README.md version 2)
- meter.reserve(agent_id, worst_usd, *, run_id=None) -> str (the reservation id), meter.settle(reservation_id, actual_usd) -> Decimal (the overshoot). Every place below that writes reserve(agent_id, run_id, worst) or settle(res, actual) means this order.
- Refusal type from the meter: limits.SpendRefused with reason kill_switch, daily_budget, monthly_budget, limits_unavailable or bad_amount. The agent loop maps a refusal to NEEDS_PERSON with the code limits.<reason>.
- Per-run cost: done by the store inside settle_spend (ticket F-store, decision 2), not by a second call from Limits.settle. Section 6 "Per-run cost" below is replaced by this.
- Budget (section 7) takes the Meter shape exactly: reserve(agent_id, worst_usd, *, run_id=None) -> str, settle(reservation_id, actual_usd) -> Decimal, plus forfeit().
- Still open with core-c (their module): the gate's module path, its constructor keywords (the draft assumes ModelGate(llm, *, meter, audit, mask_check) plus the recommended routes=), its refusal exception for a mask failure, and whether already-masked text passes the check-only mask function unchanged (the draft's main risk, open question 5).
- CHECKED by core-b: agent_loop.py:323-326, 470-486 and the Detector having no agent or run are as the draft says. NOT opened by core-b: the test files and counts in section 4, evals.py, k1b/replay.py, guard/injection.py, producers.py (the lane map LANE-MAP.md agrees on the charge sites and on extract.py having no caller).
- RUNG TABLE: component "install lines and charge-site removal" | need: one gate, no double charge | rungs 1 to 4: not applicable (it is wiring of our own module inside our own consumers) | rung 5: about 110 lines added, 100 removed | verdict KEEP-CODE. ONE-PLACE-PER-JOB: after this ticket the meter is the only place that books a model call. CODE-LAST: extract.py (no caller) is deleted, not kept.

---
# TICKET F-install: install the model gate in every consumer, delete the old charge sites, delete extract.py

Owner: SPINE. Read from snapshot `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main` (HEAD 51c9fc4fb). Nothing was run. S = `src/hadavin_sdk`, T = `tests`.

Assumed, not mine to define: `ModelGate(llm, *, meter, audit, mask_check)`, `bind(agent_id, run_id) -> LLM`, `meter.reserve(agent_id, run_id, worst_case_usd) -> reservation`, `meter.settle(reservation, actual_usd)`. The gate module path, its exception names, the mask_check signature and the Store reserve/settle method names are all UNVERIFIED (no F-store or TEXT ticket exists in `tickets/` yet).

## 1. Purpose
Today five lines charge money after a model call, and one judge call (the shadow card) is never charged. After this ticket every `chat` goes through one bound gate client: reserve, mask check, call, settle, audit row. The old charge lines are gone, so nothing is charged twice.

## 2. NEEDED-CHECK (why each part is needed)
- **No payer on the call:** `LLM.chat` carries no agent or run (S/llm/protocol.py:18-28), and `Detector.check(text, source)` has none either (S/guard/injection.py:19-20, 69-70, 85-88).
- **Charge after the fact:** S/runtime/agent_loop.py:325 and 485, S/k1b/loop.py:170, 179, 206. One reply can overshoot (loop.py:41; T/test_s5_runtime.py:107-111).
- **Unmetered call:** the shadow card judge at agent_loop.py:650-652 into S/approvals/cards.py:76-79 drops the verdict cost.
- **Evals has no cap at all:** S/evals.py:73 and the second judge client at evals.py:109; the client is built at S/cli.py:150 and the `gate` parser has no `--max-usd` (cli.py:90-92).
- **k1b Budget:** no reserve, no lock, and a thread at loop.py:104 (Budget at loop.py:40-52).
- **Wrapping at app.py:209 or once in `Runtime.__init__` is wrong:**
  - tests replace `rt.llm` after construction (T/test_k5_tools.py:608);
  - tests patch `rt.llm.chat` (T/test_p1a_fixes.py:35, T/test_p5_llm.py:57 and 169, T/test_p5p6_followups.py:97);
  - tests read `rt.llm.calls` (T/test_s5_runtime.py:64, 98, 119; T/test_peel_run_id.py, 11 places);
  - one test pins `isinstance(app.runtime.llm, FakeLLM)` (T/test_k3_pilot.py:666);
  - tests replace `rt.detector` (T/test_p6_detectors.py:179, 257, 357; T/test_p5p6_followups.py:96).
  - So `self.llm` stays the raw client and the gate is built per run from the current `self.llm`.
- **extract.py has no caller in src:** the only `.chat(` users outside `llm/` are evals.py:73, extract.py:47, judge.py:72, k1b/loop.py:94, agent_loop.py:470, bedrock_guardrail.py:101 and the demo pipeline.py:155.

## 3. Per-site table

| Site | Client built at | Wrap / bind goes at | Payer (agent, run) | Meter | Audit sink | Who masks |
|---|---|---|---|---|---|---|
| Run loop, agent_loop.py:470 | S/app.py:209 (raw; unchanged) or the test's own | `Runtime.handle`, just before the loop at agent_loop.py:465: `llm = self._gate(self.llm).bind(agent_id, run.run_id)`; line 470 uses `llm` | run's agent, run id | `self.limits` (new `Limits.reserve/settle` over the Store) | `self.audit` (chain), `write_outcome` | caller: agent_loop.py:412, 534 and tools `prepare_output`; gate only checks |
| Judge inside the run, judge.py:72 | app.py:212 (`deps.llm`, raw) | `Runtime._screen`, agent_loop.py:323, binds the detector per call (section 5) | same run | same | same | judge.py:71 (own fresh map); gate checks |
| Shadow-card judge, cards.py:79 | same judge object | `Runtime._shadow`, agent_loop.py:651: pass the bound detector; cards.py unchanged | run's agent, run id (new: charged) | same | same | judge.py:71; gate checks |
| Evals gate, evals.py:73 | cli.py:150 or the test's double | `evals.gate`, first statement after the `k` check (evals.py:37): wrap and bind, rebinding the local `llm` | `eval:<agent_id>`, `new_id("eval")` per gate call | in-process `Budget(max_usd)` (no store on this path, cli.py:146-164) | none exists: one line per call to stderr (open question 4) | evals.py:63; gate checks |
| Evals second judge client, evals.py:109 | built from the same local `llm` | no extra line: it receives the already bound client | same eval payer | same Budget | same | judge.py:71 |
| k1b replay loop, loop.py:94 | cli.py:221 or the test's double | `_replay`, right after replay.py:136: wrap and bind, rebinding `llm` | replay agent id, `run_id` of replay.py:135 | the Budget of replay.py:136 | `audit.sink` (`K1bAudit.sink`, S/k1b/audit_sink.py:28), `write_outcome` | replay.py:156-159 `redact_bundle`; with the acknowledge flag `mask_check` is off (replay.py:119-123), the one documented unmasked path |
| k1b judge, loop.py:205 | cli.py:222 from the raw client | same place in `_replay`: bind the detector once with the same wrap | same | same Budget | same | judge.py:71 |
| Bedrock guardrail, S/guard/bedrock_guardrail.py:101 | its own `make` via app.py:212 / cli.py:222 (line UNVERIFIED) | none: not on the LLM Protocol | nobody (not metered; stated in the guarantee text) | none | none | itself, bedrock_guardrail.py:98-100 |

The helper on Runtime (the only place a gate is constructed for runs):
```python
def _gate(self, llm):
    if isinstance(llm, ModelGate):
        return llm
    return ModelGate(llm, meter=self.limits, audit=self.audit, mask_check=MASK_CHECK)
```
app.py needs no change. A reserve or mask refusal from the gate must end the run, not strand it in WORKING: add one `except` next to agent_loop.py:477. A budget refusal maps to `_abstain(NEEDS_PERSON, "limits.<daily_budget|monthly_budget>")`; a mask refusal maps to `self._redaction_failed(run, cited)`. The refusal type must not be a `ProviderError`. In the judge paths a refusal is already caught by `injection_check` and becomes a flag (injection.py:87-101), which is fail closed.

## 4. Tests that build `Runtime(` directly
- **Count:** 8 constructions in 7 test files (literal grep; the review's "17 files, 33 hits" was not reproduced). They are T/k5_support.py:205, T/test_k3_pilot.py:98, T/test_k5_fixes1.py:73, T/test_k5_postgres.py:52, T/test_k5_round5.py:246, T/test_k5_tools.py:1132 and 1263, T/test_s5_runtime.py:29.
- **Reach:** 21 test files reuse these helpers (`build_runtime`, `test_s5_runtime.build`, the k3 helper).
- **They keep working with zero edits to the constructions** because the signature is unchanged and no gate is built in `__init__`. test_k5_fixes1.py:73 passes `None` for llm and limits and expects a ValueError; that still holds.
- **They stay metered** because `handle` wraps whatever `self.llm` holds at call time, and `_screen` / `_shadow` bind whatever `self.detector` holds.
- **Tests whose expectations change:**
  - T/test_s5_runtime.py:107-111: the reserve is refused before the call, so the result is `(NEEDS_PERSON, "limits.daily_budget")` with `rt.llm.calls == []`, no longer DENIED at the gate.
  - T/test_s5_runtime.py:109, 116: `rt.limits.charge` setup becomes `rt.store.add_spend("test-agent", now().date(), ...)`.
  - T/test_k1b_replay.py:279-286: worst case is about 0.0154 against a 0.01 cap, so 0 calls and usd "0".
  - T/test_k1b_replay.py:321-333: a detector's self-reported cost is no longer charged; rewrite with a `JudgeDetector` on the scripted client.
  - T/test_k1b_replay.py:289-293: UNVERIFIED, depends on prompt size against a 0.02 cap.
- **Must stay green unchanged:** T/test_p6_detectors.py:176-187 (judge cost in run cost and in day spend), T/test_k5_tools.py:723-731 (run cap), T/test_p5p6_followups.py:94-102 (an actual of 1,000,000 settles in full, then `limits.*`), T/test_k1b_replay.py:502-528.

## 5. Judge carrier
Smallest change: the Detector Protocol stays as it is, so no test double changes. Add one free function in S/guard/injection.py and one method on each of two classes:
```python
def bind(detector, wrap, agent_id, run_id):
    fn = getattr(detector, "bind", None)
    return fn(wrap, agent_id, run_id) if fn else detector
# AnyOf.bind: AnyOf([bind(d, wrap, agent_id, run_id) for d in self.detectors])
# JudgeDetector.bind: JudgeDetector(wrap(self.llm).bind(agent_id, run_id), self.route, self.threshold)
```
Callers that change (all of them):
- agent_loop.py:323 (`_screen`).
- agent_loop.py:651 (`_shadow`).
- k1b: one bind in `_replay` after replay.py:136; the bound detector is then passed at replay.py:168.
- evals.py:109 needs no bind (its client is already bound).
- Unchanged: cards.py:79, `judge.make` (judge.py:39-40), `judge.qualify` (judge.py:100-109), and the 10 tests that call `JudgeDetector(double, ...).check` directly.

Stated limit: a `JudgeDetector.check` called outside these carriers runs on its raw client. That covers unit tests and a `detector=` object injected into `build()`, which then also serves as summary detector (app.py:210). The injection is refused in pilot and prod unless `allow_test_doubles` (app.py:115-127). `Verdict.cost_usd` stays as information only; nobody charges it. Fix the docstrings at judge.py:6-7 and S/models.py:310-312.

## 6. Deleted lines and what keeps run cost working
- **agent_loop.py:324-326:** delete all three; `_screen` becomes the single bound `injection_check` call.
- **agent_loop.py:485-486:** delete both.
- **k1b/loop.py:**
  - 169-170: replace with `budget.forfeit()`.
  - 179: delete.
  - 206: delete.
  - `Budget.charge` (47-48): delete.
  - `route_prices` parameter (130) and its argument at replay.py:166: delete.
  - `worst_case_usd` (115-122): moves to where the gate computes it (open question 1).
- **`Limits.charge` (S/limits.py:17-18):** delete, so `grep "\.charge(" src` returns nothing.
- **Per-run cost:** `Limits.settle(reservation, actual)` settles in the Store and then calls `store.add_cost(reservation.run_id, actual)`. Recommended: the Store's settle does both in one transaction on Postgres (UNVERIFIED, F-store's call). This covers all three run sites, including the shadow judge.
- **Run cap:** agent_loop.py:256-257 is unchanged; it reads `get_run(...).cost_usd` before each step (466, 505).
- **Kill switch and budget pre-checks:** `_limits_stop` is unchanged.

## 7. k1b Budget
Move the class to S/limits.py (evals needs it too); loop.py imports it so `loop.Budget` still resolves. It needs:
- **`reserve(agent_id, run_id, worst)`**: under a lock; refuses when settled + held + worst > limit.
- **`settle(res, actual)`**: under the lock; no-op for an unknown or already closed reservation; otherwise drop the hold and add the actual amount (which may exceed the hold).
- **`forfeit()`**: turn every open hold into spend at its worst case and close it, so the late settle of the abandoned thread changes nothing.
- **`spent`**: settled plus held. **`exhausted`**: as today.
- **`run_case`**: one new `except` for the gate's budget refusal, giving `("capped", "usd_cap", halt "capped")`.
- **Meaning of run.json `usd` (replay.py:152, 227, 252):** settled actual cost of that run's model and judge calls, plus the worst case of a forfeited call. It can no longer pass the cap by more than (actual minus reserved) of one call, and it no longer includes a non-model detector's self-reported cost.

## 8. extract.py deletion
- **Delete:** S/extract.py (64 lines); T/fixtures/schemas.py (only importer is test_s4_llm_guard.py:18).
- **T/test_s4_llm_guard.py:** line 8 (import), line 18, tests at 48-59, the `"extract.txt"` parameter at 67, and the unused `DeadLetter` import at 17. Fix the docstring at line 1.
- **T/test_k5_round9.py:** `_extract` at 91-109 and the DRIVERS row at 195.
- **T/fixtures/record.py:31-36:** rows `extract.txt` and `bad.txt` (bad.txt is used only at test_s4:55).
- **Fixture files:** T/fixtures/inputs/extract.txt, plus inputs/bad.txt and their recorded answer files under T/fixtures/recorded/ (UNVERIFIED: not listed; check whether they are committed or generated).
- **S/guard/producers.py:** line 36 (PRODUCERS row) and line 58 (MODEL_CALLERS).
- No doc, README or mutation-manifest reference was found.

## 9. Producers rows for the gate module
- If the module sits under `llm/` it is skipped by the scan (T/test_k5_producers.py:86) and needs no row.
- Otherwise add its path to MODEL_CALLERS and an OUTSIDE_THE_CHOKE_POINT entry: "forwards only what its caller produced and refuses unmasked content; produces no text".
- Do not add a PRODUCERS row: test_k5_round9.py:203-216 would demand a driver that outputs a placeholder, and a refusing gate cannot do that.
- Nothing checks that a MODEL_CALLERS path exists, so SPINE can land the two rows before TEXT's module.
- evals.py, judge.py, k1b/loop.py and agent_loop.py keep their rows (they still call `.chat(`).

## 10. INVARIANTS
1. No `chat` reaches a provider client without an open reservation for a named (agent, run). In src, outside `llm/` and the gate module, `.chat(` is only ever called on a bound client.
2. No double charge: one settle per reservation; `Limits.charge`, `Budget.charge` and the five lines are gone; `Verdict.cost_usd` is charged by nobody.
3. A failed reserve or mask check means zero provider contact, and the run ends NEEDS_PERSON (`limits.*` or `redaction_error`) or the judge flags. The mask check never creates or changes a map.
4. Injected doubles are wrapped: whatever object is in `rt.llm` / `rt.detector` at call time, or passed to `evals.gate` / `replay`.
5. An abandoned k1b call counts at worst case from the moment of the timeout, and a late reply never lowers it. In the Runtime a crash leaves the hold for the expired-reservation sweep (F-store).
6. A successful call writes one audit row through `write_outcome`; an audit failure never fails or repeats the call.
7. Settle never refuses; an actual above the hold is charged in full.
8. The inner client's exceptions pass through unchanged (agent_loop.py:477-484 and loop.py:173-178 keep working).
9. `store.get_run(run).cost_usd` equals the sum of that run's settles; day spend moves by the same amounts.
10. `Runtime(...)`, `evals.gate(reg, llm, agent)` and `replay(...)` keep their current signatures; `rt.llm` is the raw client.

## 11. Test cases (new file T/test_model_gate_install.py, written by a different agent than the builder)
- **Normal:**
  - N1: one run, FakeLLM: spend, run cost, one `llm chat ok` row.
  - N2: judge in the run: two settles, both in run cost.
  - N3: shadow card with a judge: charged to the run's agent.
  - N4: evals with `max_usd`: the cap stops it.
  - N5: replay: usd equals the sum of settles.
- **Edge:**
  - E1: `rt.llm = other` after construction is still metered.
  - E2: `rt.detector` replaced, likewise.
  - E3: a client that is already a ModelGate is not double wrapped.
  - E4: actual above reserved.
  - E5: reserve refused with 0.001 left: no call.
  - E6: hung call: forfeit, then the late settle is a no-op (release the thread and re-read `spent`).
  - E7: evals in pilot without `max_usd` is refused.
  - E8: 20 threads on one Budget never pass the limit.
- **Hostile:**
  - H1: a double whose `chat` raises still gets a settle and leaves no hold.
  - H2: a document with an unmasked secret handed straight to the bound client is refused; the double saw 0 calls.
  - H3: an audit sink that raises: the call still returns.
  - H4: a judge steered off schema is still charged once.
  - H5: a double returning negative or NaN cost (expected result decided with TEXT; UNVERIFIED).
  - H6: reserve raises StoreUnavailable: the run ends NEEDS_PERSON, never WORKING.
- **Mutants:**
  - M1: the bind line in `handle` removed.
  - M2: `_screen` uses the raw detector.
  - M3: `_shadow` passes `self.detector`.
  - M4: line 485 restored (double charge).
  - M5: `add_cost` dropped from settle.
  - M6: `forfeit` empty.
  - M7: `spent` ignores holds.
  - M8: Budget lock removed.
  - M9: `evals.gate` wrap removed.
  - M10: replay detector not bound.
  - M11: the refusal `except` removed (run stranded).
  - M12: `settle` not idempotent.

## 12. Commit order (the tree imports and the suite collects after each)
1. extract deletion (section 8).
2. producers rows for the gate module (section 9).
3. Budget moved and extended; `Limits.reserve/settle` added (needs F-store's Store methods); old `charge` kept.
4. TEXT's gate module arrives.
5. One install commit: Runtime, injection/judge bind, evals, cli `--max-usd`, k1b loop and replay, deletion of the five lines and both `charge` methods, test edits of section 4.
6. Docs: the "capped spend" sentence of plan B3, CHANGELOG.

## 13. Out
- The gate body.
- Store reserve/settle and migration 0007.
- The sweep tick step.
- T1 (the test with 50 separate connections).
- The price validator (step C).
- The check-only mask function body.
- Metering the Bedrock guardrail.
- The demo's own meter (demos/ask-your-data).
- The kill switch on CLI paths.
- A Detector Protocol change.
- Any change to app.py or cards.py.

## 14. Open questions (recommended answer first)
1. **Where the worst case comes from.** The assumed constructor has no prices, and test doubles have no `.routes`. Recommended: add a `routes=` keyword (`registry.config.routes` is at hand at all three sites) and move `worst_case_usd` to S/llm/common.py, counting documents and tools and multiplying by `max_attempts` for network kinds. Otherwise the cap is not honest under retries (loop.py:167).
2. **Settle amount on failure.** Recommended: 0 on a plain `ProviderError` (as today, agent_loop.py:477-484), worst case on `ProviderExhausted` and any other exception.
3. **Refusal types.** Recommended: the gate module exports one exception with a code, and the meter's refusal carries `daily_budget` or `monthly_budget`.
4. **Evals audit line.** Recommended: stderr, not stdout. Five test files capture `gate` output (test_cuj, test_k1a_pass_k, test_review_pr3_round2, test_client_profile, test_k1b_cli); which of them compare it exactly is UNVERIFIED.
5. **mask_check in F.** The check-only function is step G. Recommended: TEXT ships it with the gate module in F. Whether already redacted text passes it unchanged is UNVERIFIED and is the main risk to the existing suite.
6. **Audit row fields.** `AuditEvent` needs `principal` and `source` (S/models.py:193-217), and the gate knows only agent and run. Recommended: domain `llm`, operation `chat`, principal the agent id, source `gate`.
7. **Acknowledge flag outside demo.** Plan B2 says demo only; today nothing enforces it. Recommended: `_replay` refuses it when the environment is pilot or prod (2 lines).
8. **Does `Limits.blocked` count holds?** Recommended: yes; decided in F-store.
9. **Import of the gate into runtime/agent_loop.py.** Whether a layering test forbids it is UNVERIFIED.

## 15. Size
About 110 lines added and 100 removed in src (64 of the removals are extract.py). Tests: about 260 added, 60 removed or edited. Docs: about 10.
