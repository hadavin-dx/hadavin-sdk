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
