# Ticket F (TEXT part): the model gate wrapper body

Written by core-c (session role TEXT), 2026-11-20. Status: DRAFT for one EGM plan-review round. No source code is written until the lead writes "GO BUILD F".
Step type (RIGHT-SIZE): new shipping code on a guarantee-class path (money cap and masked model input).
Source of every requirement: inputs/plan-v4-final.md B1 row F and B2; inputs/plan-v3.md A3 (lines 28-37); inputs/review-plan-3-codebase.md B1, M1, M4, N4, N7. Code lines were read on origin/main 51c9fc4.

- Package id and name: F, "model gate" (TEXT writes the wrapper module; SPINE = core-b installs it, deletes the old charge sites and builds reserve/settle).
- Path class: money and redaction. Extended review: the lead decides; ORDER 004 item 3 allows ONE ticket round in this session.
- Depends on (merged first): step G's check-only mask function (same session); SPINE's reserve/settle interface (interface ticket (ii), not published yet).

## Problem in plain words
Today five places call a model, and each one does its own masking and its own charging after the call. A place that forgets either step sends unmasked text or spends without a cap, and nothing stops a call before the money is spent (limits.py:17-30 only adds spend after the reply; agent_loop.py:485; k1b/loop.py:170, 179, 206). The plan wants ONE wrapper around the model client. Before any provider contact it (1) checks that every document and message is already masked, (2) reserves the worst-case cost against the cap; after the call it (3) settles the real cost and (4) writes an audit row. If the check or the reservation fails, no call is made.

## NEEDED-CHECK (bible R454) and ONE-PLACE-PER-JOB
| question | what I read | finding |
|---|---|---|
| Does a no-code tool do it? | plan-v2.md:15 ("n8n model nodes document no cap", n8n.md 8.6, as cited by the plan; not re-checked by me: UNVERIFIED) | no |
| Does a module already in src/hadavin_sdk do it? | llm/protocol.py:19-28 (LLM Protocol, `chat` only); llm/retry.py (retries only, 108 lines, names read, body not read); limits.py:17-30 (charge after the fact, `blocked` is a read); k1b/loop.py:40-52 (`Budget`: in-memory, no reserve, no lock); guard/egress.py (host allowlist only, 30 lines) | no wrapper exists; pieces to REUSE exist |
| Is it a thin add-on on something else? | plan-v3 A3 | yes by design: it holds no money logic and no redaction logic of its own |
Verdict: NEEDED. One place per job: masking logic stays in guard/runmap.py; money logic stays in SPINE's meter; audit stays in the audit sink; the wrapper only orders the four steps.

## RUNG TABLE (CODE-LAST v1, scale of 2026-11-06)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| gate wrapper module | refuse a model call before provider contact when masking or the cap fails | 1 n8n: no cap on model nodes (plan-v2.md:15, UNVERIFIED by me); 2 core modules: none wraps the client (files above, read 2026-11-20); 3 and 4: LiteLLM-style proxies ruled out by the plan ("LiteLLM never a dependency", plan-v2.md:15) | as cited | exact cap before spend, mask failure means no call, one audit row per call | KEEP-CODE (guarantee class), about 120 lines |

## Target module
NEW file `src/hadavin_sdk/guard/model_gate.py`. Name chosen so it cannot be confused with approvals/gate.py (outbound message gate) or `evals.gate` (eval gate). DECISIONS.md row asks the lead to confirm the name.

## Interface (signatures)
```python
class Meter(Protocol):            # NEEDED FROM SPINE (interface (ii)); names are provisional until SPINE publishes
    def reserve(self, agent_id: str, run_id: str, usd: Decimal) -> str: ...   # returns a reservation id; raises CapExceeded / Stopped before any spend
    def settle(self, reservation_id: str, usd: Decimal) -> None: ...          # idempotent per reservation id

class ModelGate:
    def __init__(self, llm: LLM, *, meter: Meter, audit: AuditSink, worst_case: Callable[..., Decimal]) -> None
    def bind(self, agent_id: str, run_id: str, *, mapping: dict[str, str]) -> LLM   # returns a BoundGate; see open question 1

class BoundGate:                   # satisfies llm.protocol.LLM
    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None) -> Reply

class GateRefused(RuntimeError): ...        # base; never carries message text or a secret
class UnmaskedInput(GateRefused): ...       # the mask check found unmasked content, or the check itself failed
```
`ModelGate` itself has NO `chat`: an unbound gate cannot call a model, so a caller that forgets `bind` fails with AttributeError in its first test and not silently unmetered. (Open question 3.)

## INVARIANTS (each gets a test; I = invariant)
- I1 Order: mask check, then reserve, then provider call, then settle, then audit outcome. No other order exists in the code.
- I2 Mask failure means no call: if the check-only function reports unmasked content in any document or message, or raises any error (too large, too deep, any redactor error), `chat` raises `UnmaskedInput`; the provider client is not called; nothing is reserved.
- I3 The check never changes the caller's map: the map after `chat` is equal to the map before, for pass and for refuse. The gate never builds a new map (plan-v3 A3: "it never creates a new map").
- I4 What is checked: every `documents` item and every message `content` (string, or each text / tool-result leaf of a content list). NOT checked: `system` and `tools` (operator text, plan-v4-final B2 "Mask step").
- I5 Reserve failure means no call: if `meter.reserve` raises, the provider is not called and the error propagates unchanged.
- I6 One reservation per `chat` call, made for `worst_case(...)`; it covers the client's internal retries (plan-v3 A3).
- I7 Settle exactly once per reservation: with `reply.cost_usd` on success; with the reserved worst case when the call raises or is abandoned (plan-v3 A3 "settles at worst case when a call is abandoned"; for provider errors see open question 2).
- I8 Audit: a successful call writes one row with the non-raising `write_outcome` (audit/protocol.py:23); a refused call (I2, I5) writes one row with result "refused" and an error code, never the text. An audit failure never turns a paid call into an exception.
- I9 No secret and no message text in any exception, log line or audit row written by this module (class names and codes only).
- I10 `bind` is explicit and per call site; no ContextVar and no module-level state (k1b/loop.py:104 runs the call in a new thread). Two bound gates from one `ModelGate` share only the client, the meter and the audit sink.
- I11 The wrapper returns the provider's `Reply` object unchanged.

## Files
- Create: `src/hadavin_sdk/guard/model_gate.py` (the module above); `tests/test_model_gate.py` (written by a different agent than the builder, plan-v2 phase 1).
- Modify (TEXT): none besides step G's files.
- Modify (SPINE, not this ticket, listed so nothing is forgotten): `guard/producers.py` MODEL_CALLERS gains `guard/model_gate.py` with a PRODUCERS row or an OUTSIDE entry in the same change as the install (tests/test_k5_producers.py:78-107, review M4); app.py, runtime/agent_loop.py, k1b/replay.py, evals.py installs; charge sites deleted.
- Delete: none by TEXT (extract.py is deleted by SPINE).

## Existing core code reused (checked 2026-11-20)
- `llm.protocol.LLM` (protocol.py:19-28): the wrapper's `chat` has the identical signature.
- `k1b.loop.worst_case_usd(route, system, messages)` (loop.py:115-122): passed in as `worst_case` by the installer; the gate does not import k1b and does not read prices.
- `audit.protocol.AuditSink.write_outcome` (protocol.py:23): non-raising by contract.
- `guard.runmap` check-only function from step G (see G ticket); `runmap.RedactionError` family (runmap.py:38-42, 98).
- NOT reused: `Limits.charge` (after-the-fact; SPINE replaces it), `runmap.redact_text` (it always rewrites the map, runmap.py:524-525).

## Interfaces
- Offered to SPINE: `ModelGate(llm, meter=, audit=, worst_case=)`, `.bind(agent_id, run_id, mapping=)`, `GateRefused`, `UnmaskedInput`.
- Needed from SPINE: the `Meter` methods and their error types (exact names, whether `reserve` also checks the stop state, whether `settle` with a larger amount than reserved is allowed); which `AuditEvent` domain and operation names to use (models.AuditEvent fields as used in limits.py:34-41).
- Needed from the lead: answers to the open questions.
- Migration need: none in this ticket (0007 reservations belongs to SPINE).

## Security and least privilege
The gate holds no credential and opens no connection. It adds no identity. Personal data and secrets: it reads message text only to check it and never stores or logs it (I9).

## Tests (new file tests/test_model_gate.py; fake client, fake meter, list audit sink; no network, no live model)
Unit: T1 pass path order (I1) recorded by a shared call log. T2 reply returned unchanged (I11). T3 settle amount equals reply.cost_usd.
FAIL-BEFORE: T4 an unmasked secret in a document reaches the fake client when the same call is made WITHOUT the gate, and does not with it (catches today's "caller forgot to mask").
Hostile inputs (each must end in UnmaskedInput, zero client calls, zero reservations, map unchanged):
T5 secret in `documents` bytes; T6 secret in a nested tool-result block of a content list; T7 secret spelled with full-width letters, a zero-width space, a `A` escape, percent-encoding (the views redact_text scans, runmap.py:464-480); T8 input over `defaults.MAX_REDACT_CHARS`; T9 bytes that are not UTF-8; T10 a placeholder look-alike that is not in the caller's map (open question 4); T11 content that is not str/list/dict (an int, None): refused, not skipped.
Money: T12 reserve raises: zero client calls (I5). T13 client raises ProviderError and ProviderExhausted: settle called once with the worst case (I7). T14 client raises BaseException subclass (KeyboardInterrupt): settle still called once. T15 the same bound gate used from 8 threads: every reservation settled exactly once.
Audit: T16 `write_outcome` returning None (parked) does not raise. T17 an audit sink that raises: the reply is still returned and the settle happened. T18 no audit row, exception text or log record contains the secret from T5 (search of all captured strings).
Structure: T19 `ModelGate` has no `chat`; T20 `system` and `tools` containing a secret-looking string do not cause a refusal (I4, documented limit).
Contract test for the `Meter` interface: written by SPINE's side against their implementation; this ticket's tests use a fake that passes the same contract file once SPINE publishes it.

## Mutation plan
| mutant | killed by |
|---|---|
| skip the mask check | T4, T5 |
| check after reserve | T5 (zero reservations) |
| mutate the caller's map in the check | T5-T10 (map unchanged) |
| call the provider when reserve raises | T12 |
| settle with 0 on error | T13 |
| settle twice / never on success | T3, T15 |
| drop the audit row | T1, T16 |
| include text in the exception | T18 |

## Evidence commands
`uv run --all-extras --group test ruff check src/hadavin_sdk/guard/model_gate.py tests/test_model_gate.py`; `uv run --all-extras --group test ruff format --check` on the same two files; `uv run --all-extras --group test pytest tests/test_model_gate.py tests/test_k5_producers.py -q`; `bandit -ll src/hadavin_sdk/guard/model_gate.py`. Raw output to handover/core-c/evidence/F-1.md. ONE full pytest at the end of the session's steps (ORDER 004 item 6). The 50-connection test T1 of the plan and PostgreSQL runs are SPINE's and the lead's.

## What stays out
Reserve/settle storage, the cap arithmetic, the stop state, the expired-reservation sweep, the installs in Runtime / replay / evals, the deletion of the five charge sites and of extract.py, the judge's payer binding (all SPINE). The Bedrock guardrail call stays outside the gate (plan-v3 A3). The k1b acknowledge flag (replay.py:119-123) stays the one documented unmasked path, demo stage only (plan-v4-final B2): how the gate lets it through is open question 5.

## Done and rollback
Done = I1 to I11 each have a passing test, every mutant above is killed, ruff and bandit clean, lead verdict. Rollback: the module is new and unused until SPINE installs it; removing the file and its test restores main.

## OPEN QUESTIONS (each with my recommended answer; none blocks the review round)
1. How does the gate get "the caller's run map"? The LLM Protocol `chat` has no map argument (protocol.py:20-28) and the plan names `bind(agent_id, run_id)` only. Options: (a) keyword `mapping=` on `bind`; (b) a `mapping=` keyword on `chat` (breaks the Protocol for doubles); (c) check with an empty copy. RECOMMEND (a): the run map lives as long as the run, so one bind per run fits; the judge binds with its own map (judge.py:71). Gives up: the literal two-argument `bind` of the plan.
2. Settle amount when the provider raises ProviderError (refused) or ProviderExhausted (retries used up). The plan covers only "abandoned". RECOMMEND worst case for every exception: the cap can only be under-used, never broken. Gives up: some budget is held although a refused request cost nothing. A simpler option for the owner: settle 0 on ProviderError.
3. Should an unbound `ModelGate` have a `chat` that raises a clear error, instead of having none? RECOMMEND none (fails at the first test). SPINE may prefer the clear error because `Runtime.__init__` "wraps or requires the gate type".
4. Is a placeholder-shaped token that is not in the caller's map "unmasked"? RECOMMEND refuse: it is either a forged placeholder or text masked with another map, and put-back would fail on it.
5. The k1b acknowledge path: does SPINE bypass the gate there, or does the gate take `check_mask=False` at construction, allowed only in stage demo? RECOMMEND a constructor flag that the installer sets only from that one code path, with a test that stage pilot and prod refuse it.

## NOT CHECKED
The input heads #66, #75, #79 core/P4b1 and core/T1-T2-tests (they may already contain a reserve/settle shape); llm/retry.py and llm/common.py bodies; how tool-result blocks are shaped in each provider adapter (T6 needs it); whether `write_outcome` is truly non-raising in every sink implementation; baselines (the lead runs them).

---
## AMENDMENT 1 (2026-11-20, after review round 1, ORDER 006, INTERFACE (ii) and ORDER 007). This section WINS over everything above where they differ.
Lead decisions written in: ORDER 006 items 3, 4, 8; ORDER 007 (decision on escalation E2); inputs/draft-ticket-F-store-with-INTERFACE-ii.md lines 113-135.

1. THE MASK STEP IS ENFORCEMENT, NOT A CHECK (ORDER 007). The gate does not re-scan with patterns and never refuses because a pattern matched. With a mapping, for every original value already in the caller's run map it replaces any raw occurrence in each outgoing document and message with that value's EXISTING placeholder, and sends those copies. It adds no map entry, invents no placeholder, never writes the map, never changes the caller's lists or dicts. Nothing raw from the map present: what is sent is byte-identical.
2. Guarantee sentence (verbatim from ORDER 007): "values the run has identified as sensitive are replaced by their placeholders in everything sent to a model; detection of new values is done by the producers' pattern redactor".
3. "Mask failure means no call" = if the enforce step raises (bad map, text too large, budget, content that is not a str), there is no reservation and no provider call; the caller gets `UnmaskedInput` (code mask_refused).
4. `bind(agent_id, run_id, *, mapping=None, principal=None, source="gate")`. mapping None (eval and replay command-line paths, the judge with its own map): NO enforce step.
5. STATED LIMIT (ORDER 007 item 2): a key and a value that are each clean but match a pattern once composed into one JSON string (example shape: `"user_id": "abc123"`, built by agent_loop.py:574-577 from leaves masked one by one at runmap.py:588-598) are not touched by the gate: it is not a value the run has identified. Pinned by a test; the lead keeps it as a ledger row.
6. Meter = INTERFACE (ii): `reserve(agent_id, worst_usd, *, run_id=None) -> str`, `settle(reservation_id, actual_usd) -> Decimal` (overshoot). Any exception from reserve means no call; its `reason` attribute is the audit error code. Settle: actual cost on success; 0 on a plain ProviderError (provider refused before doing work); the reserved worst case on ProviderExhausted and every other Exception; NO settle on KeyboardInterrupt / SystemExit or an abandoned thread (the worst case stays booked, the store sweep closes it). If settle raises after a reply, the reply is returned.
7. Constructor `ModelGate(llm, *, meter, audit, worst_case, mask_check=...)`; `worst_case(route, system, messages, tools, documents, output_schema) -> Decimal` supplied by the installer, computed on the enforced copies. Audit rows: domain llm, operation chat, source gate; `audit` may be None.
8. Order: enforce, reserve, call, settle, audit.
9. Invariants I2, I3, I4 above are replaced by: I2' enforce failure means no call; I3' the map and the caller's objects are never written; I4' enforced = every message content (str only) and every document; system and tools untouched. New: I12 a value added to the map after an earlier message is replaced in that earlier message on the next call; I13 existing placeholders are untouched; I14 idempotent (enforcing twice equals once); I15 zero refusals and byte-identical output for real producer output with nothing raw from the map.
10. Tests T5 to T11 are reworked accordingly (a raw secret NOT in the map passes through: detection is the producers' job). Mutant script tests/gate_mutants.py in the format of tests/stage_mutants.py (ORDER 008): no call without a reservation; enforce failure means no call; known originals replaced.
11. `runmap.is_masked` (ticket G part G0) is still delivered as plan row G's check-only function, but the gate does not call it.
12. Still for SPINE: requests/1-producers.patch; per-site handling of `GateRefused` and of `SpendRefused`; deletion of agent_loop.py:483, 491 with the charge sites.

## AS BUILT (2026-11-20 05:55 UTC, commit "code F:" 45156c1; evidence/F-G0-1.md). Differences from Amendment 1, each for the lead's verdict
1. Constructor keyword is `enforce=runmap.enforce_map` (a function (text, mapping) -> str), NOT `mask_check=`. SPINE's draft install line `mask_check=MASK_CHECK` must change to `enforce=` or be dropped (the default is right).
2. `runmap.enforce_map` reuses the redactor's own sweep (`redact._Redactor.sweep`, a private class imported into runmap.py): longest value first, never inside a placeholder token, every copy of a secret, identifiers only as standalone words (`xabc1234` is not touched when `abc1234` is known).
3. STATED LIMIT: a known value written in a look-alike or hidden-character spelling is NOT replaced by the gate (returning a decoded view could turn a look-alike into a real placeholder). Pinned by a test. The fold scan (G3) covers this at the producers.
4. `ModelGate(llm)` raises TypeError when `llm` is already a ModelGate or a BoundGate.
5. Audit error codes: mask_refused, reserve_refused (or the meter's `reason` when it is a short lower-case code), provider_error, provider_exhausted, call_failed, call_interrupted, settle_failed. A row has run id, domain llm, operation chat, principal, source, result, error code: no route and no agent id.
6. Unchanged messages and documents are sent as the caller's same objects in new lists; a changed document is re-encoded as UTF-8 (bad bytes become U+FFFD).
7. With a map (even an empty one) a text over the redactor's size cap is refused; with mapping=None only the types are looked at.
8. Size: 269 lines (target was 120 to 180).
Verified: 140 tests pass in the three new files, 2 strict expected failures (E3); mutant script tests/gate_mutants.py "12 of 12 good"; ruff clean; bandit no findings; the 23 existing test files that use runmap: 6336 passed, 1 failed (tests/test_k5_producers.py, expected until requests/1-producers.patch is applied).
NOT checked: the full suite; Python 3.12; the cost of the enforce step per call; the real Limits / SpendRefused (not built yet); type check.

## REVIEW ROUND 1 CHANGES (2026-11-20, ORDER 011, inputs/lead-review-code-F-gate-1.md; evidence/F-G0-1.md section "Review round 1 fixes"). This section WINS over Amendment 1 item 6 and AS BUILT items 2 and 5.
1. THE ONE SETTLE RULE (replaces Amendment 1 item 6 and ORDER 006 item 8): (a) a reply came back with a usable cost: settle it; (b) the adapter marked the error `refused_before_response` (requests/2-refused-before-response.md; no adapter sets it yet, so today this never fires): settle 0; (c) everything else (unmarked ProviderError, ProviderExhausted, timeout, any other Exception, KeyboardInterrupt / SystemExit, abandoned thread, a reply whose cost is missing, negative, NaN, infinite or not a Decimal): NO settle, the worst case stays booked and the store sweep closes it.
2. A reply with no usable cost is RETURNED to the caller (the call happened); row `ok` / `cost_unknown`.
3. Audit rows: the reservation id is in `object_ref` (None for a row written before a reservation exists). A paid call whose settle raised is `ok` / `settle_failed`. Codes now: mask_refused, reserve_refused or one of the five published SpendRefused reasons (kill_switch, daily_budget, monthly_budget, limits_unavailable, bad_amount; an allowlist, any other `.reason` is not copied), provider_refused (settled 0), provider_error, provider_exhausted, call_failed, call_interrupted, cost_unknown (none of these five settled), settle_failed.
4. `runmap.enforce_map` = the redactor's sweep with a private cache copy, PLUS one step: a known value that is a piece of a placeholder token of the map (`SECRET`, `UUID_1`) is swept afterwards, alone, so it cannot be replaced inside a placeholder written in the same pass (seen before the fix: `<<SECRET_1>_2>`).
5. `runmap.redact_text` no longer empties the live map before writing it (`mapping.clear()` dropped: the new content is always the old content plus new entries; tests `test_m4_*` in tests/test_runmap_enforce_map.py).
6. The "no logger, no exception text, no chain, no message text" guard (I9) walks the syntax tree of the whole module; tests/gate_mutants.py G7a to G7e prove it fails.

## STATED LIMITS (lead review round 1)
The guarantee sentence ("values the run has identified as sensitive are replaced by their placeholders in everything sent to a model; detection of new values is done by the producers' pattern redactor") holds with these limits. Each was checked against the sweep's rule in guard/redact.py (`_sweep` lines 1204-1219, `_replace_standalone` 1225-1243, `_Redactor.sweep` 1011-1050) and is pinned by the test named (T = tests/test_model_gate.py, E = tests/test_runmap_enforce_map.py). The same list is in the module docstring of guard/model_gate.py.
1. SHORT VALUES. A known value under 3 characters is never replaced, whatever its kind. Pin: E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept.
2. SHORT DIGIT STRINGS AND COMMON WORDS. A known value that is all digits and under 6 characters, or a common word (`redact._COMMON`: prod, test, dev, web, db ...; any letter case), is never replaced. CORRECTION to the review's wording: this exemption does NOT apply to a secret kind of 4 characters or more (SECRET, APIKEY, JWT ...): those are replaced in every copy, digits and common words included. It applies to identifier kinds and to a 3-character secret. Pin: same test as 1.
3. IDENTIFIERS TOUCHING A LETTER OR DIGIT. A value that is not a secret kind of 4 or more is replaced only where no ASCII letter or digit touches it on either side (`abc123` inside `xabc1234` stays; `abc123_`, `-abc123-` and a non-ASCII letter beside it are replaced). Pin: E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept.
4. ENCODED OR LOOK-ALIKE SPELLINGS. Only the spelling held in the map is replaced: a percent-, entity- or backslash-encoded copy, a full-width or other look-alike spelling, and a copy split by a zero-width character pass as written. Pins: T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate, E::test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced.
5. PARTIAL OVERLAPS. Two known values that overlap in the text without one containing the other (`abcd` and `cdef` in `abcdef`): the longer is replaced (for equal length, the earlier in the map) and the tail of the other stays readable (`<SECRET_1>ef`). When both are identifiers, neither is replaced in the overlap (limit 3). Pins: E::test_stated_limit_partial_overlap_leaves_a_tail, T::test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent.
6. COMPOSED KEY AND VALUE. A clean key and a clean value that only match a pattern once composed (`"user_id": "abc123"`) are not touched: the gate runs no pattern, and a value in no map passes as written. Pin: T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched (and T::test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job).
7. Not limits of the sweep but of the gate's scope, unchanged: `mapping=None` means no enforce step; `system` and `tools` are not touched (T::test_no_map_means_no_enforce_step_at_all, T::test_t20_system_and_tools_are_not_touched). A changed document is re-encoded as UTF-8 (bad bytes become U+FFFD); an unchanged one is the caller's own bytes object (T::test_b1_an_unchanged_document_with_bad_bytes_is_the_callers_own_object_beside_a_changed_one).
