# walk-B (lane B)
(Saved by the session: the builder's Write of this file was refused by the harness, so this is the builder's returned report extracted VERBATIM by script from its transcript, not edited. Verdicts are the builder's proposals; not yet spot-checked by a reviewer. Audited sha b4cce5b.)

## walk-B (agent loop walk, runtime/agent_loop.py, plan.py, tick.py, runs.py, evidence.py). Not saved to disk; the lead should save it as parts/walk-B.md.

**Trigger.** A host calls `Runtime.handle(agent_id, principal_id, document_bytes, trigger_kind, trigger_ref, mapping)` (agent_loop.py:325). The agent must be in `agents`, which were each qualified at start (agent_loop.py:195-196, 339-340). Tick (a separate CLI process) runs reconcile, stuck, purge and the other steps (tick.py:335).

**Branches in `handle` (agent_loop.py:339-540).**
- create run, audit `run received`, state WORKING (:348-350).
- document larger than `max_document_bytes`: NEEDS_PERSON `document_too_large` (:354-356).
- limits (kill switch, daily or monthly budget, run cap) checked before anything paid: STOPPED or NEEDS_PERSON (:359-360, 239-250).
- save redaction map, redact the document, save the map again (:362-381); too many map entries: `document_too_complex` (:382-386).
- injection screen on the redacted document: NEEDS_PERSON with the reason code (:387-390).
- loop up to `max_steps` (:420). Each step: limits, heartbeat `store.touch`, `llm.chat`.
- `ProviderError` or `ProviderExhausted`: NEEDS_PERSON (:432-439).
- `max_tokens` or `refusal`: NEEDS_PERSON (:442-449).
- no tool call: NO_ACTION (:450-451).
- first tool call only (:452): an action contract goes to `_submit` (:453-454); an allowed read tool is run (:455-538); anything else is NEEDS_PERSON `unknown_action` (:539).
- tool branch: limits again; caps on calls (`max_tool_calls_per_run`), bytes and errors; redact and save the map; store the call record; screen the output; feed the result back inside `<<TOOL RESULT ...>>` markers (:530-537).
- `_submit` (:632-722): validate (cited, grounded) -> `build_plan` -> save plan -> PLAN_READY -> `limits.blocked` -> `authorize` (an exception denies, rule `gateway.error`) -> `write_intent gate/decide` (unavailable: NEEDS_PERSON `audit_unavailable`) -> save gate decision -> level.
- `limits.*` rule: DENIED, no card.
- shadow level: post a card, then NO_ACTION.
- deny: DENIED.
- suggest without needs_approval: DENIED (:709-712).
- needs_approval: WAITING_FOR_APPROVAL, then `request_approval`.
- allow with no level (dev only, levels None): `execute` directly.
- `execute` (:760-869): hooks present -> `_recheck` (gate re-run at execution time) -> intent -> restored inputs, `input.unresolved` check -> compare the HMAC of the restored view with the one bound at gate time (`restored_unbound`, `restored_changed`) -> EXECUTING -> `hooks.execute` (an exception becomes outcome `unknown`) -> audit result -> VERIFYING -> verify -> SUCCEEDED, or rollback -> ROLLED_BACK, else NEEDS_PERSON.

**Error paths.** Every failure ends in a state with a reason code. NEEDS_PERSON is final (runs.py:21-30). `_abstain` also posts an abstain card (:569-597); a failed card post is audited and never raised. Store failures while saving the map or a tool call give `evidence_unavailable`. Redaction failures give `redaction_error`.

**Retries and timeouts.** The runtime has no retry loop of its own. Provider retries live in the llm kinds (`max_attempts` 3, `call_timeout_s` 60, table.py:37-40). Loop bounds: `max_steps` and the evidence caps. Tick marks a run stuck after `max_steps * call_timeout_s * max_attempts + 60` s (tick.py:100-110). The store connect timeout is 10 s (postgres.py:146). No statement timeout was found.

**Kill, restart, duplicate, out-of-order, empty and huge input.**
- Process killed mid-run: the run stays WORKING, PLAN_READY, EXECUTING and so on until tick moves it to NEEDS_PERSON (`interrupted`, `outcome_unknown`, `verify_interrupted`, tick.py:111-175). EXECUTING is never re-executed.
- Crash between WAITING_FOR_APPROVAL and saving the request: tick finds `approval_missing` (tick.py:152-175).
- Duplicate approval click: `record_decision` compare-and-set loses with `StaleState`, so no second callback.
- Racing callback and tick reconcile: only one wins at `_to(EXECUTING)`, but the loser still writes an audit intent (B-03).
- Duplicate event: two runs (B-04).
- Out-of-order state moves: `runs.check` refuses with `IllegalTransition`, and tick treats it as "moved by another worker".
- Empty document: the model is called; there is no empty check (UNVERIFIED).
- Huge document or tool output: caps in config, then `document_too_large` or `tool_error` (:354, 481).
- Only the first tool call of a reply is used (B-21).

**Written where.**
- Store: runs, plans, gate_decisions, approval_requests, approval_decisions, spend, spend_month, kill_switch, tick_state, tool_calls, redaction_maps.
- Audit sink: audit events (hashes and codes).
- Files: qualified.jsonl (read only).
- Loggers: `hadavin_sdk.runtime`, `hadavin_sdk.tick`.

**What a person sees.** A card (shadow, abstain or approval) through the channel hook; a final run state with `reason_code`; the tick exit code (0, 1, 2 or 4) and `tick_state.last_error`. In pilot and prod, deferred.py:83,87 allows only shadow levels, so the approval and execute path is demo-only today (the README states "suggest ... before K6 and K8"; UNVERIFIED whether any text claims otherwise).

**What is logged.** Warnings use reason codes and class names only (agent_loop.py:114,237). Tick messages are redacted and cut to 500 chars (tick.py:287-293). The audit gets hashes, with the HMAC of restored inputs when the key is set (app.py:84-85 requires it in pilot and prod).

**Identity.**
- Runtime role in Postgres, with the approval and kill-switch write waiver (B-06).
- The executor and its secrets are injected as hooks; runtime never imports them (agent_loop.py:3-4).
- The purge step uses a separate role (tick.py:196; app.py:86-89 requires it in pilot and prod on Postgres).

**Approval points.** `authorize` decides allow, needs_approval or deny. needs_approval waits for the approvals subsystem (lane A). `execute` re-runs the gate and checks that the restored inputs equal what the approval was bound to (:730-751, 798-830).

**Loop stop conditions.** `max_steps`, run cost cap, daily and monthly budgets, kill switch, tool caps, injection flag, provider error and step-end states. K1b's separate loop stops on `max_steps`, `max_tool_calls`, a case timeout and a USD cap, but ignores the kill switch (B-07).

**Needs a runtime, so UNVERIFIED:** real Postgres lock behaviour, the executor's heartbeat timing, host process layout, scheduler behaviour, and whether duplicate events arrive.
