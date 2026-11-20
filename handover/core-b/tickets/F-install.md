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

## UPDATE 2026-11-20 06:08 UTC (binding; wins over everything below where they differ). Sources: lead ORDER 010 items 4 and 6, lead note 05:31Z, core-c's pushed module (origin/cloud/core-c bfc13e4, marked by core-c "work in progress, not verified"), interfaces/ii-meter.md.
U1. The gate as core-c built it: src/hadavin_sdk/guard/model_gate.py, `ModelGate(llm, *, meter, audit, worst_case, enforce=runmap.enforce_map)` and `gate.bind(agent_id, run_id, *, mapping=None, principal=None, source=...) -> BoundGate` (an LLM). There is NO mask_check and NO routes keyword. A client that is already a gate raises TypeError, so `_gate` below keeps its isinstance test. Refusals: `GateRefused` (code only) and its subclass `UnmaskedInput`; a meter refusal passes through as limits.SpendRefused with `.reason`.
U2. Masking (lead decision on core-c escalation E2): the gate does NOT refuse on a pattern hit and runs no pattern. It replaces values the run's map already holds by their existing placeholders in every message and document it sends. So SPINE re-masks nothing in the producers. The run loop passes the run's LIVE map by reference: `self._gate(self.llm).bind(agent_id, run.run_id, mapping=<the run map object the loop already holds>)`. The judge binds with mapping=None (it keeps its own map). Eval and replay command lines bind with mapping=None, except replay passes its bundle map if it has one object for it (decided at build after reading replay.py; if not, None and stated).
U3. worst_case: SPINE supplies the callable at each install site: a closure over the registry's routes calling the shared helper worst_case_usd(route, system, messages, *, tools, documents, requests) -> Decimal in src/hadavin_sdk/llm/common.py (moved and extended from k1b/loop.py:115-122: counts documents and tool schemas, multiplies by the client's max_attempts; one token per byte at most; rounded up). The exact argument list the gate passes to worst_case is read from model_gate.py at build time and the closure adapts to it.
U4. Settle rule is the gate's (core-c): cost known: settle that cost; error marked "refused before any response": settle 0; everything else: no settle, the worst case stays booked and the tick step expire_reservations closes it. For k1b Budget (in memory, no sweep) the abandoned hold is closed by Budget.forfeit() exactly as section 7 says.
U5. Meter facts now built (commit 8db9c29): limits.SpendRefused(reason), limits.Meter, Limits.reserve(agent_id, worst_usd, *, run_id=None) -> str, Limits.settle(reservation_id, actual_usd) -> Decimal; an unknown reservation id raises NotFound from BOTH meters (Budget too; section 7's "no-op for an unknown reservation" is replaced). The store adds the settled cost to the run's cost; nothing in the install calls store.add_cost for a gated call. Limits.charge is deleted in the install change.
U6. Budget moves to src/hadavin_sdk/limits.py with reserve(agent_id, worst_usd, *, run_id=None) -> str, settle(reservation_id, actual_usd) -> Decimal, forfeit(), a lock, `spent` = settled plus held; k1b/loop.py imports it so loop.Budget still resolves.
U7. Run ends on a refusal: SpendRefused -> _abstain(NEEDS_PERSON, "limits.<reason>"); UnmaskedInput -> self._redaction_failed(run, cited); any other GateRefused -> NEEDS_PERSON with its code. None of these is a ProviderError.
U8. Producers rows for guard/model_gate.py are already landed (commit a1c1013). extract.py deletion (section 8) and commit order (section 12) stand; commit 2 is done.
U9. NOT decided here, read at build: the audit row fields the gate writes (core-c: domain llm, operation chat, source gate) against any audit-shape pin in tests; whether a layering test forbids runtime/agent_loop.py importing guard/model_gate.py.
U10. Tests for this ticket: new file tests/test_model_gate_install.py (section 11) and tests/contracts/test_meter.py (the ten points of interfaces/ii-meter.md against Limits and Budget), both by a different agent than the builder; mutant script tests/gate_install_mutants.py in the runner format (M1 to M12 of section 11).
NO source code for this ticket before the lead writes GO BUILD F-install (the lead said: when core-c's module is pushed and verified).

## RESOLUTION of review round 3 (the last; binding; wins over everything below where they differ). Report: tickets/F-install-review-3.md. State: Y1, Y2, Y3, Y5, Y6 are BUILT on branch wip/cloud-core-b/F-install (commits d8d76ff and the merge 28abb73 of cloud/core-b into it); the line "NO source code before GO BUILD" at the top is void (GO BUILD F-install was given in ORDER 014).
Z1 (Y3 mechanism as built). with_retry(..., record: list[bool] | None) appends one entry per retried failed attempt: True when that attempt was never sent (connection refused, name lookup failed; cost 0), False for everything else, INCLUDING a 429 (a throttled request is not known to be unbilled: stricter than the mark, which counts a 429 as unbilled for the final error). NetworkLLM._retry passes a record and puts attempts = len(record) + 1 and prior_known = all(record) on the Answer; the four adapters already pass **vars(got) to reply(), so no adapter edit was needed. reply() sets cost None when prior_known is False. Reply.attempts (audit only, no consumer yet; core-c may read it).
Z2 (Y2 as built). A Decimal cost is set only when BOTH token counts are not None; a partial usage is unknown. Tokens fields still hold estimates for display only (estimate_tokens never prices a call). openai_compat's second request round: attempts are summed, prior_known is ANDed, and if either request lacked usage the tokens become (None, None) so the cost is None (this closes the under-count).
Z3 (readers). evals.py: a None cost raises ConfigError naming the golden case. guard/judge.py: Verdict.cost_usd is the reply cost, and Decimal(0) when the reply cost is None (so the existing tests that compare it with the reply cost stay valid). Test doubles that built a Reply without a cost now pass cost_usd=Decimal(0) explicitly (the builder's list: tests/test_model_gate.py, test_k5_round5.py, k5_support.py, test_k5_round9.py, test_k5_tools.py, test_p5_llm.py, test_k3_pilot.py, test_p6_detectors.py, demo_askdata/test_llm_io.py).
Z4 (the demo). demos/ask-your-data/askdata/pipeline.py reads reply.cost_usd (adds it, settles it, formats it): with a None cost it would raise TypeError. The demo runs on the fake model (always a Decimal) and made-up data; the follow-up (treat None as the worst case in the demo meter) is NOT built; stated here and for the lead.
Z5 (Y4, the release command): ON HOLD. It contradicts the recorded invariant 4 (a booking never goes down after expiry), can drop real spend, widens the reset role on three money tables and edits files the lead's builder owns. Nothing is built. The decisions needed and my recommendation are in ESCALATIONS.md E6.
Z6 (file list for Y2 and Y3, in addition to V11): models.py, llm/common.py, llm/retry.py, llm/openai_compat.py, evals.py, guard/judge.py, interfaces/ii-meter.md (point 11); tests: the nine doubles above plus tests/warden_port/test_providers.py (the no-usage estimate test now expects cost None). The "ten points" text of ii-meter.md and interfaces/README.md become "eleven points".
Z7 (Y1 map path). The run loop binds per step with mapping=<the run's RunMap object>; the judge and the shadow-card judge are bound inside _screen and _shadow, which receive the map as a new keyword `mapping` passed from handle (the local `rmap`); the JudgeDetector.bind and AnyOf.bind carriers take `mapping` as a parameter. NO_MAP is not available until core-c publishes it (its request 3); until then None.
Z8 (CHANGELOG behaviour list, in addition to V5). A call whose provider reports no usage, and a call that succeeded after a retry that may have been billed (timeout, reset, 5xx, a throttled attempt), now leaves its worst case booked until the expiry step; the run's cost does not include it, so the run cap does not see it. A local model server that omits usage (for example Ollama) behaves this way on every call. A zero price is allowed only for the fake kind in demo, which always reports usage. Until the release command exists the only remedy is waiting for the day and month to end.
Z9 (header). See the state line at the top of this section.
Z10 (nits). Line 103 of models.py is Run.cost_usd and stays a Decimal (store arithmetic); the Reply field is the one at about line 299 (V10: by text). The retry.py mark on ProviderExhausted needs core-c's gate to honour it (requests/to-core-c-1 and to-core-c-2); Y3's per-attempt rule deliberately does NOT treat a 429 as cost 0.

## RESOLUTION of lead order 017(B) (2026-11-20 06:45 UTC; binding; wins over everything below where they differ). NOT yet reviewed by a fresh reviewer; Y4 is a money path and needs a plan review round before it is built.
Y1 (bind mapping required). core-c makes the `mapping` keyword of bind REQUIRED and names "no map" NO_MAP (its request 3, not yet published). The run loop, the judge and the shadow-card judge always pass the run's map object; only the eval and replay command lines pass NO_MAP. Test (test writer): with a scripted client that records what it receives, a value known to the run map never reaches the client raw through the run loop, the judge and the shadow-card judge. Build waits for core-c's module; until then the built code already passes mapping=<the run map> at all three sites and NO_MAP is None.
Y2 (Reply.cost_usd). models.py: `Reply.cost_usd: Decimal | None = None`; None means "the true cost of this call is not known". The gate then returns the reply and does NOT settle (the worst case stays booked). Every producer sets a Decimal only when it measured a usage; an adapter that reports no usage sets None (llm/common.py `reply()` stops estimating tokens at 3 characters per token: that estimate is no upper bound). Places that read cost_usd and must handle None (grep result at 06:44): evals.py:80 (`cost += reply.cost_usd`: treat None as unknown and stop the eval with a clear refusal, never add), guard/judge.py:86 and 96 (Verdict.cost_usd stays a Decimal for information: pass 0 and say so in its docstring), models.py:103 (the Reply sibling at that line) and models.py:310 (Verdict), llm/fake.py:54 and every test double that built a Reply without a cost (builder lists them in its report; the double keeps working by setting the cost it means). Doubles that relied on the default of 0 and are asserted free get cost_usd=Decimal(0) explicitly.
Y3 (retries never under-book). The reply of a call that needed retries: cost_usd is the sum of the known costs of ALL attempts when every earlier attempt was marked refused before any response (refused_before_response, cost 0) or returned a usage; if ANY earlier attempt may have been billed with an unknown cost (timeout, reset, 5xx, an answer without usage) the reply carries cost_usd None. With_retry keeps a small record per call (the list of attempt outcomes) and common.reply() reads it; field name: `Reply.cost_usd` only (None is the flag); an audit-only integer `Reply.attempts` (default 1) records how many requests the call took. Named in interfaces/ii-meter.md as point 11.
Y4 (release command; MONEY PATH: plan review before build). Operator command `hadavin-sdk limits release-expired --day YYYY-MM-DD --by WHO` under the RESET identity (same refusals as limits reset: pilot and prod need backends.store.reset_credential_ref, exit 2 before any connection; the audit intent is written BEFORE it acts, exit 3 when the audit is down). Effect: for every reservation with status expired and day = the named day it lowers the day counter and that day's month counter by the reserved amount, in one transaction per row, marks the row settled with settled_usd = 0 (so the table still reconciles: counters equal the sum of settled_usd of closed rows plus reserved of open rows), prints the count and the total, writes one audit outcome limits.release_expired with those two numbers. Store method (new, one place): Store.release_expired_spend(day: date, *, limit: int = 1000) -> tuple[int, Decimal]. A counter that would go below zero raises CounterDamaged-style RuntimeError and rolls that row back (nothing is lowered below what the rows prove). Rights: this WIDENS the reset role: GRANTS gains reset rights "SELECT, UPDATE" on spend_reservations, spend and spend_month (migrate.py GRANTS rows; no new migration file); LEAD to confirm, because the reset login can then lower the money counters, which is the point of the command and its stated cost. The CLI function is `_limits_release_expired` in its own function; the lead's builder may touch cli.py for step B: keep the diff apart. Nothing is built until a review round on this section has run.
Y5 (one gate exception type). Pre-call failures arrive as GateRefused with a stable `.code` (core-c); SpendRefused passes unchanged. W1's mapping already covers both; nothing new except that the test writer pins it.
Y6 (order). The refused-before-response mark is on cloud/core-b (commits "code F: providers mark ..." x2 and its tests) and therefore lands BEFORE the install: satisfied. core-c must (a) stop excluding ProviderExhausted by type and (b) add "usd_cap" to its reason list and (c) change its test that says no adapter error carries the mark: requests/to-core-c-1-exhausted-mark.md and requests/to-core-c-2.md.

## RESOLUTION of review round 2 (binding; wins over round 1's resolution and everything below). Report: tickets/F-install-review-2.md. Sent to the running builder at 06:31 UTC.
W1 (where refusals are caught). One helper Runtime._refused(run, exc, cited) -> Run holds the V6 mapping; an unknown reason (also usd_cap) ends NEEDS_PERSON "limits_unavailable". It is called from an except (SpendRefused, GateRefused) at every site a refusal can surface: the document screen before the loop, the bind plus chat call in the loop, the tool-result screen, and inside _shadow before its existing except Exception (a refusal there ends the run by the mapping with no card, never "shadow_undelivered"). The detector is bound per _screen and per _shadow call, inside those trys. NO blanket except Exception around the chat: a non-provider fault of the client propagates as today (the hold is closed by the expiry step).
W2 (Budget per case; replaces V2's "closes the budget" and "case scope"). run_case binds the gate PER CASE with a case run id (the replay run id plus the case index). Budget.forfeit(run_id: str) turns every open hold of that run id into spend at its worst case and closes that run id: a later reserve with it raises SpendRefused("usd_cap"); other cases are not affected. run_case calls it unconditionally in its finally. A settle of a forfeited hold can only raise the booked amount. reserve with run_id None is allowed (evals).
W3 (requests). requests = max_attempts x 2 when an output schema is passed, else max_attempts; max_attempts is the client's attribute if it is an int of at least 1, else 1.
W4 (formula details). None counts 0 bytes; JSON text is json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str) with default separators, UTF-8 with surrogatepass; an empty routes mapping is a ValueError when the closure is built; if sizing fails the closure raises SpendRefused("bad_amount") (no call, W1 ends the run), never a guess.
W5 (imports). guard/injection.py imports SpendRefused and GateRefused inside the function, not at module top (limits -> registry -> guard.judge -> guard.injection would be a cycle).
W6 (replay and evals). In run_case ONE try covers the chat and the detector call on a tool result: usd_cap ends the case ("capped", "usd_cap", halt capped); any other SpendRefused reason or a GateRefused ends it ("error", reason or code, halt aborted); run_case still never raises for these. evals.gate lets both propagate; the command prints "gate stopped: <reason or code>" and exits 2. A max_usd that is not a finite Decimal above zero is a ConfigError. An already-gated client: a ModelGate is used as it is; a BoundGate is a ConfigError.
W7 (small). SpendRefused docstring names six reasons, Meter names Limits and Budget; point 1's "unknown agent is a KeyError" does not apply to Budget (it has no registry); tests/test_k1b_replay.py:289-293 stays; the eval row's "one line per call to stderr" is dropped; invariant 3 reads "a failed reserve or a map that cannot be enforced means zero provider contact"; the mutants of section 11 are M1 to M4 and M6 to M12, named by text, not by line.

## RESOLUTION of review round 1 (binding; wins over the UPDATE and everything below where they differ). Report: tickets/F-install-review-1.md. Decisions marked LEAD wait for the lead's OK in DECISIONS.md / ESCALATIONS.md E3.
V1 (worst case). The gate calls worst_case(route, system, messages, tools, documents, output_schema) with six positional arguments and route as a NAME. SPINE supplies one closure per install site, built by a new function in src/hadavin_sdk/llm/common.py: `worst_case_for(routes: Mapping[str, Route], llm: object) -> Callable[[str, str, list, list | None, list | None, dict | None], Decimal]`. It uses the helper `worst_case_usd(route: Route, system, messages, *, tools, documents, output_schema, requests) -> Decimal`: input bytes = UTF-8 length of system + of the JSON text of messages (sorted keys, ensure_ascii False) + of the JSON text of tools + the byte length of every document + TWO times the JSON text of output_schema (adapters send it as a forced tool and as a hint in the system prompt) + defaults.WORST_CASE_OVERHEAD_BYTES (new constant, 4096, for adapter framing); input tokens = input bytes (at most one token per byte); cost = (input tokens x input price + route.max_tokens x output price) / 1000000 x requests, rounded UP to 12 decimal places; requests = getattr(llm, "max_attempts", 1). LEAD: a route NAME the registry does not hold (only test doubles: the config check refuses an unknown detector route at load) is priced as the LARGEST worst case over all configured routes, never refused; the closure never raises (any error inside it also falls back to that bound). Worked number for the fixture route (3.00 in, 15.00 out, max_tokens 1024): output part 1024 x 15 / 1000000 = 0.01536; a 1000-byte prompt adds (1000 + 4096) x 3 / 1000000 = 0.015288; one request: 0.030648.
V2 (Budget, the in-memory meter; moved to limits.py). reserve(agent_id, worst_usd, *, run_id=None) -> str: same amount check as Limits (bad amount: SpendRefused("bad_amount")); under a lock; refused with SpendRefused("usd_cap") when settled + held + worst > limit, or when the budget was closed by forfeit(). LEAD: "usd_cap" is a SIXTH published reason (interfaces/ii-meter.md is updated when the lead agrees; core-c's gate audits an unknown reason as reserve_refused, so nothing breaks before that). settle(reservation_id, actual_usd) -> Decimal: unknown id NotFound; first settle of an open hold replaces the hold by the actual amount (may exceed it) and returns the overshoot; a settle of a hold that forfeit() closed can only RAISE the booked amount (same rule as the store after expiry) and returns the overshoot; a repeat returns the first result. forfeit(): turns every open hold into spend at its worst case and CLOSES the budget for new reserves made by an abandoned thread of that case (run_case opens a fresh "case scope" per case: implementation detail, one counter). spent = settled + held, an exact Decimal sum, formatted as today. The contract points of ii-meter.md that apply to Budget: 1 to 7; not 8 (no run), 9 (no stop state), 10 (no tick).
V3 (evals and replay wiring). evals.gate(reg, llm, agent, *, k=<as today>, max_usd: Decimal | None = None): the existing positional signature is unchanged. LEAD: with max_usd None in demo the cap is the agent's daily budget from the registry (a cap always exists); in pilot and prod (stages.is_live) a missing max_usd is a ConfigError raised by evals.gate (exit 2). CLI: `gate --max-usd DECIMAL` (optional flag, parsed as Decimal, refused if not finite and above zero). A cap hit raises SpendRefused out of evals.gate; cli prints "gate stopped: usd cap reached" to stderr and exits 2. LEAD: the gate is built with audit=None on BOTH command-line paths (eval and replay): the eval path has no sink, and the replay sink is pinned to hold only replay events written with write_intent (tests/test_k1b_replay.py:114-121, k1b/audit_sink.py:1). Stated limit: model calls of the eval and replay commands are metered but not audited one by one; run.json and the command's own summary carry the cost. This departs from the lead draft's k1b row (audit.sink).
V4 (holds on failure, Budget). run_case calls budget.forfeit() in a finally for every exit that leaves a hold open (timeout, exhausted retries, any provider error, a reply with unusable cost), not only on CallTimeout. run.json usd = settled real costs + the worst case of every forfeited hold.
V5 (holds on failure, runtime; stated behaviour changes for CHANGELOG). A provider error that is not marked "refused before any response" keeps the worst case booked on the day and month counters until the expiry step closes it (at least 3600 seconds); today such an error costs nothing. A bad key or throttling can therefore use up a small daily budget without real spend; the mark from ORDER 013 (code F: providers mark ...) removes the certain cases. The run's cost moves only on settle, so day spend and run cost can differ for failed calls, and a reply whose cost is unusable does not count toward the run cap. Invariant 9 reads: for calls that settled, the run's cost and the day spend move by the same amounts. The loop's own "llm chat failed" note is REMOVED (the gate writes that row); tests that count it are adapted.
V6 (how a run ends on a refusal; one place, the chat site and the two bind sites are inside one try). SpendRefused is mapped exactly like the loop's existing limits stop: kill_switch -> STOPPED "kill_switch" through _to (no card); daily_budget and monthly_budget -> the same state and code _limits_stop gives today for that reason; limits_unavailable and bad_amount -> NEEDS_PERSON "limits_unavailable" through _to (no card). UnmaskedInput -> self._redaction_failed(run, cited). Any other GateRefused -> NEEDS_PERSON with its code through _to. Any other exception from bind, worst_case or the gate before provider contact -> NEEDS_PERSON "gate_error" through _to. None is a ProviderError; the existing except ProviderError block stays for provider failures.
V7 (wrap and judge). `_gate(llm)`: a ModelGate is used as it is; a BoundGate in rt.llm is a programming error and ends the run "gate_error" (V6); anything else is wrapped: ModelGate(llm, meter=self.limits, audit=self.audit, worst_case=worst_case_for(self.registry.config.routes, llm)). The run loop binds with mapping=<the RunMap object created at the start of handle>, principal and source left to the gate's defaults. guard/injection.py: injection_check RE-RAISES limits.SpendRefused and model_gate.GateRefused instead of turning them into an injection flag (a refusal to spend is not a verdict about the text); every caller then follows V6 (run), V4 (replay: case ends "capped") or V3 (evals: cap stop). The shadow-card judge is bound inside the same try.
V8 (tests of section 11, rewritten). H1: a chat that raises an unmarked error leaves the hold booked and no settle is made; with the refused-before-response mark the hold is settled at 0. H2: a document holding a value that IS in the run map reaches the client with the placeholder; a value in no map passes as written (stated limit). H5: a reply with a negative or NaN cost is returned, nothing is settled, the gate's audit code is cost_unknown. E6: a late settle after forfeit raises the booked amount only when the actual is above the worst case. M5 is dropped (the store adds run cost; F-store's mutant 20 covers it). M12 names both meters. New cases: an unknown route name is priced at the largest bound; a meter refusal inside the judge ends the run as V6 says and prints no injection warning on the card.
V9 (closed questions). Replay binds with mapping=None (the bundle map is dropped inside redact_bundle, replay.py:156-159). The acknowledge flag is refused by _replay when the environment is pilot or prod (2 lines, IN). The layering question is settled at build by running tests/test_lockin_guard.py and tests/test_k5_producers.py; if one forbids the import, the builder stops and reports.
V10 (line numbers). Identify every place by its text, not by number. Current numbers in agent_loop.py: _screen and its charge 324-330 (charge lines 327-329); loop 468; _limits_stop calls 469, 508; chat call 473; except ProviderError 480-487; charge and add_cost 488-489; shadow render 652-655; run cap 259-260. limits.py: Limits.charge 45-46. cli.py: gate parser 96-98, gate client 158-163, k1b clients 262-263. app.py: 218, 219, 221. My earlier line "CHECKED by core-b: 323-326, 470-486" was wrong by three lines after steps A to F-store landed: my slip.
V11 (files). Create: tests/test_model_gate_install.py, tests/contracts/test_meter.py, tests/gate_install_mutants.py (all by the test writer). Modify: src/hadavin_sdk/runtime/agent_loop.py, guard/injection.py, guard/judge.py (bind, docstring), evals.py, cli.py (flag, usage text), k1b/loop.py, k1b/replay.py, limits.py (Budget moved in and extended; Limits.charge deleted), llm/common.py (worst_case_usd, worst_case_for), defaults.py (WORST_CASE_OVERHEAD_BYTES), models.py (Verdict docstring), guard/producers.py (extract rows removed), CHANGELOG.md, README.md and SECURITY.md (the capped-spend and masked-input sentences of plan B3 with their limits), tests/test_s5_runtime.py (107-116: the test is renamed and asserts NEEDS_PERSON... as V6 maps it, no model call), tests/test_k1b_replay.py (279-286, 321-333, usd strings at 97 and 467 if the rounding changes them), tests/test_s4_llm_guard.py, tests/test_k5_round9.py, tests/fixtures/record.py. Delete: src/hadavin_sdk/extract.py, tests/fixtures/schemas.py, tests/fixtures/inputs/extract.txt and bad.txt, and the three recorded answer files for them (regenerate tests/fixtures/recorded/ by running tests.fixtures.record after removing the two ANSWERS rows). Store.add_cost stays in the Protocol (custom stores, tests) although src no longer calls it.
V12 (dependencies). Needs from core-c, all on its branch today and marked by it "work in progress": src/hadavin_sdk/guard/model_gate.py and runmap.enforce_map in guard/runmap.py. The lead names the core-c commit in GO BUILD F-install; the builder reads the gate's real signatures from that commit and stops if they differ from U1 and V1. Naming: the meter class keeps the name Budget in limits.py; registry.Budget (the agent's budget numbers) is a different class and limits.py refers to it only through the registry.

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
