# F-install review 4: ORDER 017 (B) items 1 and 5 (read-only audit)

Tree: /tmp/core-b-wt/Y, branch local/code-Y. Nothing changed, committed or pushed. Line numbers are of that tree.
Paths are under src/hadavin_sdk/ unless they start with tests/.

State of the gate API: `ModelGate.bind(agent_id, run_id, *, mapping=None, ...)` (guard/model_gate.py:190-202). The
mapping is OPTIONAL, defaults to None, and None means "no enforce step" (model_gate.py:303, 316). There is no
`NO_MAP` constant anywhere (grep over src and tests: no hit). So item 1's API change is not done yet; nothing forces
a call site to say it passes no map.

## (1) Every bind site and whether it passes the run's live mapping

| # | Site | file:line | Passes run map? | Verdict for ORDER 017 |
|---|------|-----------|-----------------|------------------------|
| 1 | Run loop chat | runtime/agent_loop.py:363 (`_bound_llm`), used at 543 | YES: `mapping=rmap`, the live `runmap.RunMap` (rmap created 475; same object grows through the run) | OK. Built fresh each step, by reference. |
| 2 | Judge, document screen | agent_loop.py:367-371 (`_bound_detector`), called by `_screen` 374-378, at 495 | NO. `bind_detector(self.detector, self._gate, run.agent_id, run.run_id)` has no mapping parameter; guard/injection.py:195-196 and 214-223 and guard/judge.py:71-74 (`wrap(self.llm).bind(agent_id, run_id)`) cannot carry one | MUST CHANGE. judge.py:73 docstring says "No run map is passed" on purpose. |
| 3 | Judge, tool-result screen | agent_loop.py:632 -> `_screen` -> same path as #2 | NO | MUST CHANGE (same code path as #2). |
| 4 | Judge, shadow-card diagnosis | agent_loop.py:719-721 `render_shadow(..., detector=self._bound_detector(run))`; approvals/cards.py:66-81 calls `injection_check(detector, diagnosis, "shadow_card")` | NO | MUST CHANGE. Highest risk of the three: `diagnosis` is `reply.text` (agent_loop.py:~551, passed through `_submit` 703 unredacted by the runtime) and goes to the judge as a document. |
| 5 | judge's own redaction | guard/judge.py:84 `runmap.redact_text(text, {})`: a fresh empty map, so only pattern detection; a value the run knows but no pattern matches (tenant name, short host) is not replaced | n/a | This is the leak path behind #2-#4. Item 1 needs the gate's enforce step to cover it. |
| 6 | eval command line | evals.py:67 `llm.bind(f"eval:{agent_id}", new_id("eval"))`; also the judge qualification at evals.py:143 uses that same bound client | NO (correct) | Pass `mapping=NO_MAP` here. Comment at 65-66 already says "No run map". |
| 7 | replay command line, agent | k1b/loop.py:130 `gate.bind(agent_id, case_run_id)` (called from k1b/replay.py run_case) | NO (correct, per comment replay.py:~147-150: bundles masked before) | Pass `NO_MAP`. |
| 8 | replay command line, detector | k1b/loop.py:131 `bind_detector(detector, wrap, agent_id, case_run_id)`; `wrap` defined at k1b/replay.py:151-156 | NO (correct) | Pass `NO_MAP` through the detector bind. |
| 9 | cli `gate` | cli.py:171-176 calls `evals.gate` (bind is inside evals.py:67) | NO (correct) | covered by #6 |
| 10 | Gate construction (not a bind) | agent_loop.py:344-358 `_gate`; evals.py:62-65; replay.py:151-156 | n/a | no change |

No other `.bind(` on a gate exists in src (grep of `\.bind(` and `bind_detector`). `tests/test_model_gate_install.py::test_every_chat_call_in_src_outside_llm_and_the_gate_is_on_a_bound_client` (1165) pins the set of files that call `.chat(`; it does not pin which map each passes.

Net for item 1: of the three run-side sites (run loop, judge, shadow card) only the run loop passes the map. The
judge (document screen, tool screen) and the shadow-card judge bind with no map. The detector bind signature
(`Detector.bind(wrap, agent_id, run_id)` in guard/injection.py:195, 214 and guard/judge.py:71) has nowhere to put a
mapping; AnyOf.bind (injection.py:195-196) forwards the same three arguments. A mapping keyword (required, NO_MAP
for the command lines) has to be added through bind_detector, AnyOf.bind and JudgeDetector.bind, and
`_bound_detector(run)` must take the run's `rmap` (it is available in `handle` at 475 and in `_submit` as `mapping`,
agent_loop.py:~697, but `_shadow(run, plan, decision, diagnosis, cited)` at 713 does not receive it: the signature
and its caller at ~832 need `rmap` added).

## (2) How refusals are caught in agent_loop.py

Classes: `GateRefused` (model_gate.py:155, code "gate_refused"), `UnmaskedInput(GateRefused)` (164, "mask_refused"),
`_GateError(GateRefused)` local (agent_loop.py:71-76, "gate_error"), `SpendRefused` (limits.py:18, `.reason`).
No single "gate exception type with a code" from core-c exists yet beyond GateRefused.code.

Catch sites (all `except (SpendRefused, GateRefused) as exc: return self._refused(run, exc, cited)`):
- document screen: agent_loop.py:495-497
- chat: 543-545 (comment "no call was made")
- tool-result screen: 632-634
- shadow card (judge on diagnosis): 723-728 (inside `_shadow`)
- `injection_check` (guard/injection.py:225-238) re-raises SpendRefused and GateRefused and turns any other detector error into a guard_unavailable flag.
- `_bound_llm` and `_bound_detector` wrap any build error into `_GateError` (366-371), so a gate that cannot be built is a refusal, not a crash.

`_refused` (agent_loop.py:380-390):
- SpendRefused -> `_SPEND_STOP` table (78-83): kill_switch -> STOPPED "kill_switch"; daily_budget -> NEEDS_PERSON "limits.daily_budget"; monthly_budget -> NEEDS_PERSON "limits.monthly_budget"; any other reason (limits_unavailable, bad_amount, usd_cap, unknown) -> NEEDS_PERSON "limits_unavailable". So a budget refusal ends NEEDS_PERSON with a limits reason: MEETS ORDER 017 item 5 (kill switch is STOPPED, same as `_limits_stop`).
- UnmaskedInput -> `_redaction_failed` (392-394; reason "redaction_error", audit guard/redaction/failed, plus abstain card): MEETS the item for the one subclass that exists.
- any other GateRefused (including `_GateError`) -> `_to(NEEDS_PERSON, exc.code)` (390), NOT the redaction-failed path. ORDER 017 item 5 says "gate refusal -> the redaction-failed path". This differs for every GateRefused that is not UnmaskedInput (code "gate_refused", "gate_error", any future code). It posts no abstain card either (`_to`, not `_abstain`), so a miss cannot be labelled on that path. Decide with core-c's request 3 whether a coded gate exception maps to redaction_error or keeps its code; today the code and the order disagree.

Can any path leave a run WORKING?
- Covered (never WORKING after the catch): the four sites above, plus provider errors at 546-551 (ProviderError/ProviderExhausted -> NEEDS_PERSON provider_error/provider_exhausted). Tested by `tests/test_model_gate_install.py::test_a_meter_refusal_ends_the_run_by_the_mapping_at_every_site` (749, 7 reasons x 4 sites), `test_a_bound_gate_as_the_judge_client_ends_the_run_gate_error` (765), `test_a_gate_refusal_other_than_the_map_ends_the_run_with_its_code` (789), `test_h2_a_map_that_cannot_be_enforced_ends_the_run_redaction_error` (653), `test_h6_...never_working` (695).
- NOT covered, run stays WORKING and escapes `handle` as an exception:
  a. The chat try (535-551) catches only SpendRefused, GateRefused, ProviderError. Any other Exception from `self.llm.chat` (client bug, timeout type that is not a ProviderError, reply parse failure, model_gate rule (c) `CODE_CALL_FAILED` re-raise at model_gate.py:263-265) and any BaseException (266-268) propagates out of `handle`; the run is left WORKING until tick's STUCK rule moves it to "interrupted" after `stuck_after_s` (tick.py:100-117). No test asserts this ends in a state.
  b. `_refused` itself calls `_to` (agent_loop.py:~320-325), which does `store.get_run` and `advance`; if the store raises there (down, StaleState) the exception escapes and the run stays WORKING. Same for `_redaction_failed` -> `_abstain` -> `_to`.
  c. `_shadow` (713-728): the `except Exception` at 729 makes any non-refusal error an undelivered card, fine; but `_to(run, NO_ACTION, ...)` at the end can raise as in b.
  d. `_screen` -> `_bound_detector` raising something that is not wrapped: wrapped into `_GateError`, OK. A detector whose `check` raises is a flag, OK.
  e. The gate is rebuilt per call (`_gate(self.llm)` each `_bound_llm`), so a `TypeError` for a BoundGate in `rt.llm` becomes `_GateError` on the first call, OK (test e3 at 377).
  f. With item 3 of ORDER 017 (a "cost unknown" flag, gate does not settle) there is no new raise; but item 2 (`Reply.cost_usd` None): agent_loop does not read `reply.cost_usd` (the gate settles), judge.py:96/107 already handles None; evals.py:109 raises ConfigError on None (command line, fine).

## (3) Missing tests (concrete)

Item 1 (map to the gate):
1. API: `bind` with no `mapping=` keyword raises TypeError; `bind(..., mapping=NO_MAP)` is accepted and means no enforce step; `NO_MAP` is importable from guard/model_gate.py and is not equal to `{}` or None (an empty live map must still enforce, since it can grow). Replace/extend tests/test_model_gate.py::test_no_map_means_no_enforce_step_at_all (584), which today relies on the default None.
2. Run loop: a value known to the run (in rmap, not matched by any pattern, for example a tenant name of 8 letters) placed in a tool result or in the agent's earlier message is NOT in the client's `sent` text on the next chat. Only the existing test e3 (350-375) checks that `mapping` is a `RunMap`; nothing proves the value never leaves raw.
3. Judge, document screen: the judge's model client (a spy) never receives a run-known value raw. Use a detector `JudgeDetector` with a spy model, a map entry added to rmap that no pattern matches, and a document or tool output that still holds it raw (for example inserted after the first map save), assert the spy's `documents` and `messages` hold only the placeholder. Currently impossible to pass: judge binds with no map (judge.py:71-74).
4. Judge, tool-result screen: same assertion with the run-known value in `out.text` (agent_loop.py:632).
5. Judge, shadow card: the diagnosis (`reply.text`) containing a run-known raw value reaches the judge spy only as its placeholder (agent_loop.py:719-721). Include the case where the value was added to the map after the card started (live map by reference).
6. The three binds use the SAME map object as the run (identity, `is`), not a copy; and the judge's bind is made per `_screen` call so a map that grew between screens is seen.
7. AnyOf: `AnyOf([RegexDetector, JudgeDetector]).bind(..., mapping=...)` forwards the mapping to every entry that has `bind`; a detector with no `bind` still passes unchanged (test e2 at 337 covers only the unbound case).
8. Eval and replay: `evals.gate` binds with `NO_MAP` and k1b `run_case` binds both the client and the detector with `NO_MAP` (spy on `bind` kwargs, as test e3 does for the run loop), and nothing else in src passes NO_MAP (a source scan: `NO_MAP` appears only in evals.py, k1b/loop.py, k1b/replay.py and the definition). Also a guard that no call site in runtime/ passes NO_MAP.
9. Shadow card path asserts a map even for `_shadow` called after `_submit` returns (signature change: `_shadow` needs `rmap`); test that `_submit` with `mapping=None` still passes an enforcing (empty, live) map, not NO_MAP.
10. Mutant for tests/gate_install_mutants.py: drop `mapping=` at agent_loop.py:363, at the judge bind, at the shadow bind; each must be caught by tests 2-5.

Item 5 (refusal endings):
11. A non-Spend, non-Gate Exception from `self.llm.chat` (RuntimeError, TimeoutError, a rule (c) `call_failed` case) ends the run in a final state, not WORKING. Today it escapes `handle` (agent_loop.py:535-551); the test would fail and the code needs an `except Exception` ending NEEDS_PERSON with a reason. Same for KeyboardInterrupt/SystemExit semantics (decide: re-raise but first move the run).
12. `_refused` when the store raises in `_to` (store down while ending the run): the test should pin what happens (today the exception escapes and the run stays WORKING; tick's STUCK recovers it). Same for `_redaction_failed`.
13. A GateRefused that is not UnmaskedInput: assert the order's wording (redaction-failed path) or the chosen mapping; today test 789 pins "exc.code" (NEEDS_PERSON "odd_code"), which contradicts item 5 as written. Add the same check for `_GateError` at each site (test 765 covers document, tool, shadow but not chat: a bound gate in `rt.llm` is test e3 at 377, chat only).
14. UnmaskedInput at the other three sites: today `test_h2_a_map_that_cannot_be_enforced...` (653) covers the chat site only. Add document-screen, tool-screen and shadow-card (once those binds carry a map, an enforce step failure there is a refusal): each must end NEEDS_PERSON "redaction_error", no card posted, no call, run not WORKING.
15. Budget refusal at the shadow site leaves no card and no "shadow_undelivered" (covered at 749); add the same for `UnmaskedInput` and `_GateError`.
16. Audit rows for a refusal: one `refused` row with the code (mask_refused / reserve_refused / published reason) and no spend row, at each of the four sites. Test 835/846 cover the gate in isolation only.
17. The single gate exception type with a code (core-c request 3): test that every pre-call failure class (enforce failure, bad worst case, non-str content, over cap, build failure) arrives as that type, and that SpendRefused arrives unchanged (identity of the exception, reason preserved). Not testable until core-c publishes the name.
18. State invariant over all sites: a parametrized run where every injectable failure (reserve refuses, enforce raises, worst_case raises, client raises each of ProviderError, ProviderExhausted, ValueError, KeyboardInterrupt, settle raises, audit sink raises) at each of the four sites ends with `store.get_run(...).state != WORKING`. This is the "never a run left WORKING" test of the order; only the SpendRefused slice exists (749).

Not in the gaps but worth knowing: tests/test_model_gate_install.py:765 and 749 build their own site runners (`run_refused`, lines 713-747), reuse them for tests 13-14 and 18 above.
