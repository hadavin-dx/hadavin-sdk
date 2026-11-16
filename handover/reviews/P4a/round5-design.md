# P4a rev 5 plan review round 5, design (0B/2M/8N). Saved by cloud session.

PLAN REVIEW ROUND 5, P4a.md revision 5 (BN-17/18/19, ticket lines 606-718, revision log line 3) plus the P4b1.md edits (line 397, BN-35 at line 531). Reviewer: egm-design (hostile design critic), money path, no round cap.

VERDICT: 0 Blockers, 2 Majors, 8 Nits. All five round-4 Majors (M1 to M5) are closed in design. The two new Majors are narrow and cheap to fix in the ticket. I would not start a builder until they are fixed. I do not think they need another full round: a one-line check by the resolver is enough.

What I checked: ticket text as on disk at 45359b0 (P4a.md lines 1-12 and 600-718, P4b1.md lines 397 and 531, TICKET-TEMPLATE.md, round4-resolve.md). Code was read, not run, in snapshot 78 and a little of snapshot 79. I read:
- 78 `backends/factory.py` in full.
- Imports of `deferred.py`, `config.py`, `replay_records.py`, `actions/contract.py` and `backends/table.py`.
- `llm/common.py` lines 150-285, `llm/retry.py` `with_retry`, and every `_retry(` caller.
- `cli.py` lines 160-185 and 285-300, `app.py` lines 160-180, and all `make(` call sites in `src`.
- `models.py` `Reply`.
- The migration file lists of 78 and 79, and 79 `meter.py` `Hold.record`.

## Round-4 Majors: did rev 5 close them?

- **M1 (refusal inside `make`): closed in design.**
  - 78 `make` is the one function that every llm and detector build passes through. The `make(` grep gives exactly the sites the ticket names (cli.py 177, 296, 297; app.py 165, 168).
  - Refusal as the first step, before `import_module`, with `None` read as not-demo (fail closed), is sound.
  - SG-T12 and SG-M15/M16 pin it.
  - Import cycle, by reading only: `factory.py` already imports `actions.secrets` and `backends.table`. `deferred.py` imports only `replay_records` (which imports `errors`) and `actions.contract` (which imports `models`). `backends/table.py` imports nothing from the package. `config.py` already imports `deferred`. I found no path from those modules back to `factory`. The fallback ("put the function in `deferred.py`") is also acceptable. See Nit 7 for what I did not run.
  - Residual hole in the guard: Major 1 below.
- **M2 (retry counter, `Reply.unknown_attempts`): closed in design.** With the counter, an answered call with no retry books its real cost. The arithmetic is right: with `max_attempts` 3 and count 2, R = 6W. The cap `0..count x (attempts-1)` and the exact-`int` check are right. There is a new fail-open risk in how the counter is carried: Major 2.
- **M3 (alert and lock-out): closed in design.** The numbers check out: 30 failures at US$0.164160 is US$4.9248, and the 31st needs more room than is left. The month figure is about 304. `on_failure_booked` is added to FB-2, FB-3 and FB-4 with mutant FB-M2h. Residual gaps: Nits 3 and 4.
- **M4 (one `reserved_factor`): closed.** Only `k1b/loop.py` 143-144 and `request_bound` held the rule in 78, and my grep found no third copy. FB-T7c ties the "20" to the `le` bound.
- **M5 (stage value): closed as plain text.** The paragraph "What the stage value rests on", the SG-T3 WARNING and NEEDS LEAD 79 are enough for a plan. This is not a code control, and the ticket says so honestly. It stays an owner/lead decision.

## Findings

**Major 1. The SG-T11 guard does not cover the ways a caller can skip `make`. Ticket lines 666 and 690.**
- Rule (a) bans importing or calling the name `make` from a paid kind module. Rule (b) bans `stage=` with an `ast.Constant`.
- Scenario A: a new product module writes `from hadavin_sdk.llm.anthropic import AnthropicLLM` and builds it with `AnthropicLLM(...)`. Or it calls `importlib.import_module("hadavin_sdk.llm.openai_compat")` and builds the class itself. A rule about `make` does not see either. The classes are public (78 `llm/openai_compat.py` line 82 declares one). A paid kind then exists in pilot with no stage check. This is the same bug class that round 4 M1 named, and the fix must sit at the choke point.
- Scenario B: product code writes `make("llm", s, stage=deferred.DEMO_STAGE)` or `stage=DEMO_STAGE`. That is an attribute or a name, not an `ast.Constant`, so rule (b) passes. It is a hard-coded demo label and bypasses the gate.
- Fix: replace (a) and (b) with allowlists.
  - (a'): no module outside `backends/factory.py`, the kind module itself, and `tests/` may import any name from a paid kind module, or pass its module name as a string to `import_module`, `__import__` or `getattr`.
  - (b'): the `stage=` argument of a factory `make` call must be exactly the expression `cfg.environment`. Allow `<name>.environment` and nothing else. Tests may pass `deferred.DEMO_STAGE`, so the guard scans `src/` only.
  - Add self-test modules for a class import, a string import and `stage=DEMO_STAGE`, with matching mutants.

**Major 2. The retry counter can fail open (book too little) and nothing would catch it. Ticket lines 631 and 638.**
- The ticket carries the per-call count in "for example a `contextvars.ContextVar` set and reset inside `chat`", and the builder picks the form. Anything that retries outside that context (a thread pool, an `asyncio` hop, or a `ContextVar` that is reset early) increments nothing. u then reads 0, and 0 is a "proven" value. FB-9 books `answered` only, which is below the ambiguous-call floor in rule (3) of the lead order.
- Today no llm kind uses threads (grep of `src/hadavin_sdk/llm` for Thread, Executor, asyncio and contextvars found nothing), so this is a trap for the next kind, not a live bug. The tests do not close it: FB-T9b checks two threads that call `chat`, not a kind that retries from a worker.
- Fix: make "no context, no proof" the rule.
  - Count into an explicit per-call object that `chat` creates and passes down to `_retry`, so a lost increment cannot happen silently.
  - Or have `with_retry` also report attempts started, with `chat` setting the field only when started equals counted-retries plus requests answered.
  - Add a mutant FB-M9g: the counter lives in a context the retry cannot see, killed by a test kind that retries from a worker thread. The field then stays `None` and R is booked.

**Nit 3. Lock-out by input, not only by outage. Ticket line 644.**
- The bullet names an outage and a wrong key. A document or prompt that makes the provider answer with an HTTP 4xx (a content-policy refusal, for example) books R each time with real spend 0. A stream of such inputs shuts one agent's day cap in about 30 calls.
- Add this case to the bullet. In P4c-2's duty (LEAD ACTION 74), say the failure-count threshold is per agent per day. NEEDS LEAD 78 can keep "no" for now.

**Nit 4. `on_failure_booked` has no call on two paths that also leave R booked.**
- One is FB-1d (the reserve reply was lost and the release also failed, so R stays open). The other is FB-5 (the settle failed, so R stays open). In both, a person may be the only one who can repair the row.
- `on_settle_failed` covers FB-5, so FB-1d is the one without an alert. Say so explicitly in the FB-2 alert sentence, or add the call to FB-1d.

**Nit 5. `unknown_attempts` is trusted from any inner `Reply`. Ticket lines 631 and 638.**
- Any llm object, a wrapper around a `NetworkLLM` for example, can return a `Reply` with `unknown_attempts=0`. The meter then books the cheap branch.
- The ticket says "recordings and fakes never carry it" because `Reply` forbids extra fields. That reason is gone once the field exists.
- Fix: the wrapper trusts the field only when `isinstance(inner, NetworkLLM)`, or the wrapper sets the field itself from the context in Major 2's fix. Add a mutant for it.

**Nit 6. Stale cross-ticket text.**
- P4b1.md line 531 (BN-35) says "PENDING LEAD 69 (fresh plan review round 4 of P4a BN-17 revision 4...)". That is now round 5 of revision 5.
- The same line says R4d-2 and R4d-3 "run only with a proven count (P4b2-a's field, or a test-local reply subclass until then)". The field is now built by P4a-2.
- P4a.md line 666 says "the four build sites" and then lists five lines in 78.
- FB-M9e/M9f say they are "killed by FB-T9b", but the real-counter sub-row is owned by P4b1-b. State that FB-T9b itself asserts `reply.unknown_attempts` after a real `NetworkLLM.chat` over scripted attempts, so the P4a-2 mutants die inside P4a-2.

**Nit 7. Import cycle and `Reply` serialization were read, not run.**
- Add one builder step: run `python -I -c "import hadavin_sdk.backends.factory"` and the same for `config` and `deferred` in a fresh interpreter, in each import order, and save the output.
- Grep for any dump, hash or fixture of a `Reply` before adding a field. My grep found only `model_copy` uses, and `Reply` is a `Shape` with `extra="forbid"` (78 `models.py` line 346).

**Nit 8. Migration number collision.**
- FB-6 numbers the new migration "one above the highest on P4b1-a's merge base". P4d, P3a or other branches may take the same number before merge.
- Add: the builder re-checks the number at merge time, and `late_files` is the backstop.
- Separately, 78 and 79 each carry their own `0006_spend_reservations.sql`, and main has only 0001-0005. I did not diff the two files. The ticket assumes they are the same.

## What I did not check
- I ran nothing: no tests, no import-cycle check, no mutants, no migration.
- I did not read 79 `cli.py` or `app.py`, so the 79 line cites (150, 221, 222, 162, 165) are unverified.
- I did not read P4b2.md, P4c.md or P4d.md, or the earlier round reports. The lead actions 74 and 77 (copying duties into other tickets) depend on the lead and are not verified.
- I did not verify the claims "Anthropic `max_retries: 0`, Bedrock `total_max_attempts: 1`, Gemini and OpenAI-compatible have no SDK retry". I checked only that all four kinds route through `self._retry` and that nothing in `llm/` uses threads.
- I did not re-derive W = 27,360 or R = 164,160. I only checked the lock-out arithmetic. The round-4 codebase reviewer already re-derived W and R.
- I did not check whether OpenAI-compatible request 2's usage is summed with request 1's in `Reply`. FB-9's "answered" assumes it is.
- I did not read the full 700 lines of the rest of P4a.md (body, answers 1-14).
- The stage value (M5) stays operator-written; that is a decision for the lead and owner (NEEDS LEAD 79), not something I can settle.

Files: /home/user/hadavin-sdk/handover/tickets/P4a.md, /home/user/hadavin-sdk/handover/tickets/P4b1.md, /home/user/build/snap/78-4a0976f/src/hadavin_sdk/backends/factory.py, /home/user/build/snap/78-4a0976f/src/hadavin_sdk/llm/common.py, /home/user/build/snap/78-4a0976f/src/hadavin_sdk/llm/retry.py.