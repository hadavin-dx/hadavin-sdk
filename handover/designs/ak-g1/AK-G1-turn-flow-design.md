# AK-G1 design: the chat turn flow (`handle_turn`) and the conversation store transaction rules

*   **Author:** Claude (git `user.name`), for the lead, order 36 item 82 (PENDING LEAD 11 option (b))
*   **Status:** Draft (not yet reviewed; the next step is `egm:egm-review` with fresh reviewers)
*   **Date:** 2026-11-06, written about 06:00-06:40 UTC (11:30-12:10 IST; IST = UTC+5:30)
*   **Predecessor:** `designs/ak-g1/concepts_brief.md`
*   **Authority order:** lead answers to PENDING LEAD 11-16 (end of `tickets/AK-G1.md`) > build notes BN-1 to BN-28 (same file, copied from `reviews/AK-G1-round3-resolve.md`) > the frozen ticket body (revision 3). This design changes no decision. Where the ticket body is stale, this design follows the build notes and says so ("Ticket text this design does not follow"). Where the sources leave a gap or disagree, it is an **open point** with a recommendation; the ticket is not edited.

--------------------------------------------------------------------------------

## Read this first: limits of this document

- **No code was run.** I read files only. No test, lint, mutant or database was run.
- **No fresh reviewer has read this.** The brainstorm's Goldfish review did not run (this session has no tool that starts a subagent). This document still needs `egm:egm-review`.
- **Interactive gates skipped.** Both EGM skills ask the author to approve each section. The brief asked for AUTO mode, so I wrote all sections in one pass and chose nothing the ticket and the lead's answers had not already fixed.
- **Read in code by me (2026-11-06, about 05:50-06:00 UTC / 11:20-11:30 IST):** `runtime/runs.py:8-42` (allowed run state moves; `STOPPED` from any non-final state), `runtime/tick.py:98-135` (stuck-run time and the `stuck` step), `:184-218` (`purge_evidence`, the hold hook re-raises), `:245-268` (`STEPS`; `stuck` runs before any appended step), `store/memory.py:83-90` and `store/postgres.py:279-280` (`touch` moves `updated_at` and checks no state), `runtime/agent_loop.py:560-567` (`_deliver` never raises), `store/migrate.py:24-40` (`Grant` has no column-limited runtime field today). The `runtime/` folder has no `conversation.py` yet; migrations `0001` to `0005` exist.
- **Not read by me, taken from the ticket and its resolve (UNVERIFIED here):** every other line cite in this document; the P4c-2, P4b1-b, P5c-2, P5c-3 and AK1 names (`MeterError`, the rule-6 codes, `scope.refusal`, `MaskedLLM.of`, `llm.run`, `SessionClosed`, `tenant_key`); whether the manifest tool path stores only masked text in `tool_calls`; whether the purge role can lock rows on PostgreSQL 16 and 17.

## Words used

Plain meanings, one meaning each. They are the ticket's words.

- **person**: the human who writes to the agent. **user id**: the made-up, opaque id of that person (for example `user-1`; never an e-mail address).
- **conversation** (or chat): one chat between one person and one agent, an ordered list of **turns**. A turn is one message, the person's (role `user`, odd numbers) or the agent's (role `assistant`, even numbers). An **exchange** is the person's turn plus the agent's answer turn.
- **fixed reply**: a reply whose words come from configuration, not from the model (the `handoff` and `paused` texts, and the lost-answer filler `[no answer was given]`).
- **hand-off**: the agent stops answering in this conversation for good, and one item goes into the "needs a person" queue (AK-G15).
- **mask / placeholder / label**: before text goes to the model, a protected value such as an e-mail address is replaced by a placeholder such as `<EMAIL_1>`. A **label** is the text `[hidden email]` shown in place of a placeholder. The **conversation map** is the saved list "placeholder -> original value" for one conversation (identifier kinds only).
- **lease**: the claim one exchange holds on a conversation while it is being answered, so two messages of one conversation are never answered at the same time. It is **live** while its run is not final and the run's last heartbeat (`store.touch`) is newer than the agent's **quiet limit** (the stuck-run time of `tick.py:100-109`). Otherwise it is **dead**.
- **version**: a counter on the conversation row. Every write to the row adds 1. A writer passes the number it read, and the store refuses the write (`stale`) when the row changed since.
- **takeover**: the store step that ends a lost exchange (an exchange whose lease died): it writes the filler answer, clears the lease and hands the conversation off.
- **sweep**: a tick step that finds conversations with a dead lease, for a person who never writes again.
- **stop reason**: a closed code that says why an exchange stopped before a normal reply. A stop in the fixed set `HANDOFF_STOPS` hands the chat off. Every other stop is a **passing fault**: the chat stays open and the person gets the fixed `paused` reply.

--------------------------------------------------------------------------------

## Overview

AK-G1 adds a chat to the core's agent runtime. A host app (a web widget, a messaging app, or AK-G2's signed webhook) calls one method, `Runtime.handle_turn`, once for each message a person sends. The method checks and masks the message, stores it, asks the model for an answer with the last few turns as history, masks the answer again, sends it to the person through a hook, and stores it. When the agent should not or cannot answer, the chat goes to a person.

This document writes out two things the ticket keeps in one dense table and many notes: (1) the order of the steps of one exchange, and (2) what each store method writes, in which transaction, and what it refuses. It folds in the 28 build notes and the lead's six answers, so the builder reads one consistent text.

## The Problem

Three review rounds found most of their serious defects in the ordering of this flow, not in its parts:

- round 2: who may write the conversation map, and whether the hand-off item is opened before or after the chat is marked handed off;
- round 3: a lost exchange that was answered again by the model (R3-ADV-6), earlier messages that never passed the screen but were shown to the model again (R3-ADV-1), and exceptions after the claim that left the method (R3-ADV-2).

Build note BN-6 then changed the ordering again. A table plus 28 notes is easy to misread. The risk is concrete: a wrong order either loses a message (the person was told something the record does not show, or nobody is told at all), or answers a chat that was promised to a person. Both break rule R368 (no lost or double-applied messages).

## Goals

1.  One numbered step list for an exchange, F1 to F13 and E1 to E6, with every build note applied, where each step names its store call, its run state change, its delivery and the result it returns when it ends the call.
2.  One numbered rule list for each store transaction: `claim_turn`, `finish_turn`, `record_user_turn`, the private takeover helper, `lost_exchanges`, `forget_user` and `purge_conversations`.
3.  These invariants, stated so a test can check each one:
    - **I-1.** Every call returns exactly one result, or raises in F1 (a host programming error). No `Exception` leaves `handle_turn` after F1.
    - **I-2.** Every run that is created makes exactly one state change after `WORKING`, and gets at most one delivery attempt.
    - **I-3.** A conversation has at most one live lease.
    - **I-4.** Once the takeover or the hand-off commits: a "needs a person" item exists for the exchange if and only if the conversation is `handed_off` (BN-6). Open point OP-1 names the one path that can still break this.
    - **I-5.** A placeholder never stands for two values in one conversation. Every placeholder in stored text has its value in the saved map, or has been turned into a label.
    - **I-6.** No turn text, exception text or user id reaches a log line, an audit event or the hand-off item.
    - **I-7.** After a hand-off, the agent never calls the model for that conversation again.
4.  The list of every file each sub-PR touches, and why.

## Non-Goals

- Wiring AK-G22 (the gate for text sent to a person) and AK-G15 (the "needs a person" queue) into `app.build` (row V12). Until then, the blanket pilot/prod refusal (T19 b) keeps every chat out of pilot and prod.
- The chat window and the transport.
- Actions from a chat (V11), summaries (V1), putting hidden values back into replies (V3), giving a chat back to the agent (V2), closing a chat (V13), voice and attachments (V6), streaming (V7).
- Read tools in a chat. They come in AK-G1-c, only after the owner picks PENDING LEAD 5 (a). This document describes the (b) shape that AK-G1-b builds, and marks the AK-G1-c parts.
- Any change to the frozen ticket text.

## Open Points (gaps and contradictions found while drafting; the lead decides each)

Each point has a recommendation. Until the lead answers, the builder should not guess; OP-1 to OP-3 change store or result behaviour and belong to the build-start review.

- **OP-1. A dead lease can come back to life after its item was opened.** *Gap.* A lease is dead when the run is quiet past the quiet limit, even while the run is not yet final. `touch` moves `updated_at` without checking state (`store/memory.py:83-90`, `store/postgres.py:279-280`, read in code). So: (1) the sweep or F7 sees a quiet run, (2) opens the `interrupted` item, (3) the slow process wakes and calls `touch`, which makes the lease live again, (4) the takeover call with `take_over` reaches the "live lease" check first (ticket check order, F6 note) and returns `busy` (or `lost_exchanges` skips it), (5) the slow process reaches E4 and `finish_turn` commits `open`. Now an item exists while the chat stays open, which breaks I-4. The tick's `stuck` step runs before the appended `sweep_conversations` step in the same tick (`tick.py:249-266`), which narrows the window for the sweep but not for F7. **Recommendation:** in the takeover helper (both callers), when `take_over` equals the conversation's current `busy_run_id`, take over WITHOUT re-checking that the lease is dead: the item for that run is already open, so the takeover must follow. The late process then gets `LeaseLost` at E4 and returns `with_person`. Add a test where the run is touched between the item and the takeover.
- **OP-2. The takeover for a resent lost message.** *Gap.* BN-6 says the takeover inside `claim_turn` "then appends this message's masked user turn". When the call is the person's (or the host's) resend of the lost message, the message id is already stored, and the table's unique rule on `(tenant, conversation_id, message_id)` refuses a second row. The ticket's older text returns `duplicate` with `lost` set for that case; BN-6 does not say which wins. **Recommendation:** for a duplicate message id, the takeover writes the filler, clears the lease, sets `handed_off`, adds 1 to `version`, appends nothing, and returns `duplicate` with `lost` set; `handle_turn` returns `with_person`, `delivered=False`. For a new message id it returns `recorded` as BN-6 says.
- **OP-3. The result when the tick moved the run after `finish_turn` committed.** *Contradiction inside the ticket.* E6 says that when its one transition finds the run already moved by the tick, the call returns `with_person`, reason `interrupted`. The outcome mapping paragraph says the outcome follows what this exchange wrote to the conversation. If `finish_turn` already wrote `open` with a normal reply, the two disagree: the host would be told "with a person" while the chat is open and the agent will answer the next message. BN-17 only covers the case where `finish_turn` did not commit. **Recommendation:** when E4 committed, the outcome follows the conversation (`replied`, `paused` or `with_person`, by the mapping rule), and `interrupted` stays on the run record only; when E4 did not commit, keep `with_person interrupted`. T37's variant stays as written (E4 does not commit there).
- **OP-4. Where the money card goes inside `_end_exchange`.** *Gap.* BN-2 says `_end_exchange` "also posts" P4c-2's fixed money card for `estimate_exceeded` and `limits_unavailable`, but not when. **Recommendation:** right after E2 (delivery) and before E3, with a `store.touch` before it, wrapped like `_deliver`, so the card hook gets a fresh quiet stretch as the other hooks do. A card failure is logged (ids and class name) and does not change the outcome.
- **OP-5. Where the report paths are recorded.** *Contradiction between two lead texts.* Order 36 item 82 says "Record the report paths in egm/hadavin-sdk/ak-g1/". The ticket's "Lead answers" says "Report paths: `handover/designs/ak-g1/`". This document and the brief are in `handover/designs/ak-g1/`, as the brief for this task said. **Recommendation:** keep the files here, and the lead records the paths in the studio folder if that is what order 36 meant.
- **OP-6. A takeover from `claim_turn` with a version that moved.** *Small gap.* F7's second F6 call passes the `expect_version` read before the first call. A `lost` result writes nothing, so the version normally still matches. If another writer committed in between (for example the sweep's own takeover), the second call sees `ConversationNotOpen` or `stale`. **Recommendation:** state it in the step list (done in F7 below): `ConversationNotOpen` goes to the F5 path after one re-read, `stale` goes back to F3 once, then `retry`.

## Ticket text this design does not follow (stale, superseded by build notes)

| Ticket text | Replaced by |
|---|---|
| Interface 2: "`recorded` comes only from `record_user_turn`" | BN-6: `claim_turn` with a takeover also returns `recorded` |
| Interface 2: the `ClaimResult` kinds | BN-9 adds `reused` |
| F6 note and sweep paragraph: after an `interrupted` item "the conversation stays `open`"; PENDING LEAD 2(vii) | BN-6 and PL14: every takeover writes `handed_off` |
| "Store failures, one rule"; "No exception leaves `handle_turn` after F1" | BN-2 crash rule; "No `Exception` leaves..." |
| F8: "meter scope opens around the rest (UNVERIFIED name)"; F9: "`add_cost` when charged" | BN-8: `with self.llm.inner.scope(agent_id, run_id=run.run_id)`; the wrapper books every call |
| Interface 11: "Test builders wrap it in `MeteredLLM`" | BN-4: tests wrap exactly as production, `MaskedLLM.of(MeteredLLM(ScriptedLLM(...)))` |
| F1: `Unqualified` for an agent without `conversation` | BN-18: `Unqualified` only for an agent not in `self.agents`; otherwise `ValueError("agent is not conversational")` |
| F13 and E4: `mapping=_keep(rmap)` after the reply | BN-16: `kept` is taken before F13 |
| Duplicate mapping from the first run's reason | BN-25: from the conversation and the stored answer turn |
| "Existing tests that may break: none expected" | BN-19: `tests/test_p7_tick.py:80-89` changes on purpose |
| "Postgres rows FAIL, not skip" | BN-14: Postgres runs on 16 and 17 with 0 skipped |
| T9's `max_steps` case in the (b) stage | BN-3: moves to AK-G1-c |

--------------------------------------------------------------------------------

## Critical User Journeys (CUJs)

All values are made up (`tenant-a`, `user-1`, `person-1@example.invalid`).

### CUJ 1: a normal reply

*   **Given**: an open conversation of `user-1` in `tenant-a`, no live lease, a qualified conversational agent, both hooks set.
*   **When**: the host calls `handle_turn` with a new message id and the text "my address is person-1@example.invalid, where is my order?".
*   **Then**: the model sees `<EMAIL_1>`, never the address; the person receives the model's reply with any placeholder shown as `[hidden email]`; two turns are stored (masked user turn, answer turn with `delivered=True`); the run ends `NO_ACTION replied`; the result is `replied` with no text in it.

### CUJ 2: the person asks for a person

*   **Given**: as CUJ 1.
*   **When**: the model calls `ask_for_person`.
*   **Then**: the fixed `handoff` reply is delivered; one item is opened with `idempotency_key = run_id`; then `finish_turn` writes `handed_off`; the run ends `NEEDS_PERSON asked_for_person`; result `with_person`. A later message is stored masked, with no model call and no reply.

### CUJ 3: a provider outage

*   **Given**: as CUJ 1, and the model provider fails.
*   **When**: `llm.chat` raises `ProviderError`.
*   **Then**: the fixed `paused` reply is delivered; the chat stays `open`; no item is opened; run `NEEDS_PERSON provider_error`; result `paused`. On the next exchange, the earlier user message is shown to the model as `[an earlier message was not processed]` (BN-1).

### CUJ 4: a crash in the middle of an answer

*   **Given**: an exchange whose process died after delivery and before `finish_turn`.
*   **When**: the person writes again after the quiet limit, or the person never writes again and the tick runs.
*   **Then**: the next claim (F6 `lost`, F7) or the sweep opens one `interrupted` item for the lost run, then the takeover writes the filler `[no answer was given]` (`delivered=False`), clears the lease and sets `handed_off`. The new message, if any, is stored with no model call; result `with_person`. One item exists, whichever came first.

--------------------------------------------------------------------------------

## Technical Plan (Architecture)

### Components

```text
 host app / AK-G2 webhook
        |  handle_turn(agent_id, tenant, conversation_id, user_id, message_id, text)
        v
 +------------------------------ Runtime (runtime/agent_loop.py) ------------------------------+
 |  F1-F5 checks, mask, read          F6 claim (store)        F8-F13 model loop                |
 |  (no run, no model)  ------------> run row + lease  -----> MaskedLLM(MeteredLLM(raw))      |
 |                                                              |                              |
 |  _end_exchange: E1 text -> E2 deliver_reply -> E3 -> E5 open_handoff -> E4 finish_turn -> E6|
 +----------|----------------------------|------------------------|--------------------------+
            v                            v                        v
   Store (memory / Postgres)      Hooks.deliver_reply      Hooks.open_handoff
   conversations,                 (AK-G22 later;           (AK-G15 later;
   conversation_turns, runs,      RecordingRecipient       RecordingHandoff
   redaction_maps, tool_calls     in tests)                in tests)
            ^
            |  tick: stuck (moves quiet runs to NEEDS_PERSON interrupted)
            |        ... purge_evidence (conversation purge runs before the hold hook)
            |        sweep_conversations (appended last): Runtime.sweep_conversations(now)
```

`handle_turn` sits beside the existing `handle`. Both use the read-tool block of `handle`, moved into `_tool_step` (D1); a chat run in the (b) shape never calls it. A chat run never calls `_abstain`, `_shadow` or `_submit`, so it posts no approval card. The one card it can post is P4c-2's fixed money card (BN-2, PL13).

### Fixed sets

- **`HANDOFF_STOPS`** (a constant in `runtime/agent_loop.py`, not config, D6): `asked_for_person`, `injection_suspected`, `unknown_action`, `reply_not_delivered`, `conversation_too_long`.
- **Passing faults** (every other stop): `provider_error`, `provider_exhausted`, `limits.<x>` (for example `limits.daily_budget`), `run_budget`, `kill_switch`, `max_steps` (AK-G1-c only, BN-3), `llm_max_tokens`, `llm_refusal`, `empty_reply`, `reply_too_long`, `tool_error`, `evidence_unavailable`, `document_too_complex`, `redaction_error`, `guard_unavailable`, `estimate_exceeded`, `limits_unavailable` (BN-2).
- **Refusal reasons** (F1-F5, nothing accepted beyond one audit event): `message_unreadable`, `message_too_large`, `empty_message`, `unknown_conversation`, `redaction_error`, `message_too_complex`, `message_id_reused`.
- **Reasons only on the run record**: `replied`, `lease_lost`, `handoff_unavailable`, `store_unavailable`, `internal_error`, `interrupted`.

### The exchange, step by step (F1 to F13)

Names used below: `rmap` is this exchange's map, `RunMap(conversation.mapping)`, grown by masking (and by tool results in AK-G1-c). `_keep(m)` is `runmap.storable(m, self._kinds)`, the only way the flow calls `storable`, so a client's narrower `stored_kinds` applies everywhere. `label_unsaved(t, kept)` turns every exact placeholder in `t` whose key is not in `kept` into `[hidden <kind>]`. `render(t)` rewrites every placeholder-shaped text, look-alikes included, into a label. Steps F1 to F5 create no run, call no model and deliver nothing.

1.  **F1. Inputs.** The agent must be in `self.agents`; if not, raise `Unqualified`. If the agent has no `conversation` setting, raise `ValueError("agent is not conversational")` (BN-18). `type(text) is str`. `conversation_id` fully matches `conv-[0-9a-f]{32}`; `message_id` and `user_id` fully match their patterns. A bad input raises `ValueError` naming the field only, never its value. Then make the run id: `run_id = new_id("run")`. Every refusal event of this call carries it; it becomes the run's id only if the claim commits.
2.  **F2. Readable, size, not empty.** In this order: (a) `text` must encode as UTF-8 (no lone surrogate), else `refused message_unreadable` (BN-12); (b) its UTF-8 length must be at most `max_message_bytes`, else `refused message_too_large`; (c) `text.strip()` must not be empty, else `refused empty_message`. Each refusal first writes one `conversation/refused` audit event with `write_intent` (which raises on failure), with principal `chat:<agent_id>`, source `runtime`, domain `conversation`, operation `refused`, and the pre-made run id (BN-18 COR-14). If that write raises `AuditUnavailable`, return `retry`. Nothing is masked or stored.
3.  **F3. Read and owner check.** `get_conversation(tenant, conversation_id, reader=user_id)`. Then require `conversation.user_id == user_id` and `conversation.agent_id == agent_id`. A missing row, another tenant, a reader not allowed, a caller who is not the owner, or another agent's chat all give one answer: `refused unknown_conversation`, audited as in F2. A store exception gives `retry`.
4.  **F4. Mask and map size.** `masked = redact_untrusted(text, rmap)` (through P5c's session once P5c-2 merged), called directly in the body of `handle_turn` (BN-18 COR-13). `stored_user = label_unsaved(masked, _keep(rmap))`. `added = len(rmap) - len(conversation.mapping)`. A redaction failure gives `refused redaction_error`; `InputTooLarge` or `added > max_map_entries` gives `refused message_too_complex`; both audited as in F2. If the STORED map is already at or over `max_map_entries`, do not refuse: set stop `conversation_too_long` and continue (it hands off once at E1, after the claim, with no screen and no model call). Compute `text_digest = _keyed_digest(stored_user)` (BN-9).
5.  **F5. Handed-off chat.** If `state == "handed_off"`: `record_user_turn(..., expect_version=conversation.version, text=stored_user, text_digest, mapping=_keep(rmap))`. `recorded` returns `with_person`, `delivered=False`, no model call. `duplicate` returns `with_person`, nothing written. `reused` returns `refused message_id_reused`, audited as in F2. The first `stale` goes back to F3 once; the second gives `retry`. A store exception gives `retry`.
6.  **F6. Claim.** `claim_turn(..., run=Run(run_id=<pre-made>, agent_id, principal_id="chat:<agent_id>", trigger_kind="user", trigger_ref="<conversation_id>:<n>"), message_id, expect_version, text=stored_user, text_digest, mapping=_keep(rmap), now=models.now(), quiet_s=self._quiet[agent_id], take_over=None)`. Results:
    - `claimed`: the run row (`RECEIVED`), the user turn and the lease committed together. Continue with `turn_no = n` (answer slot `n + 1`).
    - `busy`: `retry`.
    - `stale`: the first time back to F3; the second time `retry`.
    - `lost` (a dead lease; nothing written): go to F7.
    - `duplicate` with its answer slot filled: map from the stored conversation and that turn (BN-25): `handed_off` gives `with_person`; `open` with `fixed=False` gives `replied`; `open` with `fixed=True` gives `paused`; `delivered=False` in all three (this call delivered nothing).
    - `duplicate` with an empty slot and a live lease: `retry`. With an empty slot and a dead lease the store returns `lost` instead (F7).
    - `reused`: `refused message_id_reused`, audited as in F2 (BN-9).
    - `ConversationNotOpen`: re-read once and take the F5 path.
    - A store exception: `retry` (the claim and the run row commit together or not at all).
7.  **F7. Lost exchange.** There is no run for this call yet. Call `open_handoff(HandoffRequest(tenant, conversation_id, run_id=lost.run_id, reason="interrupted", idempotency_key=lost.run_id))`, wrapped. If it raises: one ERROR log line (ids and class name only) and `retry`; nothing was written. If it returns: call F6 again with `take_over=lost.run_id`. The store writes the takeover (filler, lease cleared, `handed_off`) and then records this message without a lease, and returns `recorded` (BN-6), which gives `with_person`, `delivered=False`, no model call. For a resend of the lost message, see OP-2. A second `lost` naming another run gives `retry`; `stale` goes back to F3 once; `ConversationNotOpen` goes to F5 after one re-read (OP-6).
8.  **F8. Run start.** Audit `run/received` with `inputs_hash = _keyed_digest(masked)`. `_to(run, WORKING)`. Enter `with self.llm.inner.scope(agent_id, run_id=run.run_id)` (the meter scope, BN-8) and `with self.llm.run(run.run_id, principal, seed=rmap)` (the mask session; always, there is no fallback, BN-4). `_save_map(run, rmap)` (the run's own copy in `redaction_maps`). If `_save_map` fails: stop `evidence_unavailable`, go to E1. If F4 set `conversation_too_long`: go to E1. Any other exception: the crash rule.
9.  **F9. Screen the message.** `_screen(run, masked, "user")`. Its cost is booked by the wrapper (BN-8). Then read P4c-2's per-run signal and `scope.refusal` as `handle` does (BN-2). A flag gives stop `injection_suspected` (hand-off) or `guard_unavailable` (passing fault); a meter refusal gives its rule-6 code. Go to E1 on any stop.
10. **F10. Model step**, a bounded loop `for _step in range(agent.max_steps)`: `_limit_reason(run)`; a value (`kill_switch`, `limits.<x>`, `run_budget`) is the stop, go to E1. `store.touch(run.run_id)`. On the first step only, build `messages` from `list_turns(..., before_turn_no=n, last=history_turns)`, oldest first; for each pair whose assistant turn has `fixed=True`, give the user turn as `[an earlier message was not processed]` (BN-1, PL12); then append the new masked user turn once. `system` = agent prompt + `_CHAT_RULE`. `tools` = `ask_for_person` only (AK-G1-c adds the agent's `subject_scoped` tools). Call `self.llm.chat(messages, system, route, tools, documents=[])`.
11. **F11. Model answer.** `ProviderError` gives stop `provider_error` or `provider_exhausted`. A separate `except MeterError` gives P4c-2's rule-6 code: `kill_switch`, `run_budget`, `limits.daily_budget`, `limits.monthly_budget` or `limits_unavailable`, with no card and no `_abstain` (BN-2). After the call, read the per-run signal: overshoot gives `estimate_exceeded`, a settle failure gives `limits_unavailable`. `stop_reason` `max_tokens` or `refusal` gives `llm_max_tokens` or `llm_refusal`. No tool call goes to F13. First tool call `ask_for_person` gives `asked_for_person`. Any other tool call gives `unknown_action` (in the (b) shape; AK-G1-c sends an allowed tool to F12). The end of the loop gives `max_steps` (reachable only with read tools, BN-3). Every stop goes to E1.
12. **F12. Tool step (AK-G1-c only).** `reason = self._tool_step(..., subject=Subject(tenant, conversation.user_id))`. A reason is the stop, go to E1; `None` goes back to F10.
13. **F13. Reply.** First take `kept = _keep(rmap)` (BN-16). Then `r = redact_text(reply.text, rmap)`, called directly in the body of `handle_turn`. `RedactionError` or `InputTooLarge` gives stop `redaction_error` (BN-2). Empty after stripping gives `empty_reply`; longer than `max_reply_chars` gives `reply_too_long` (never cut before masking). Otherwise `rendered = render(r)` and `stored = label_unsaved(r, kept)`. So a value that first appears in the model's reply is a label in the stored answer and never enters the saved map. Go to E1 with no stop.

### Ending the exchange (`_end_exchange`, E1 to E6)

Every path from F8 on ends here exactly once, or in the crash rule. The ticket keeps the ids E4 and E5 from older rounds; E5 runs BEFORE E4.

1.  **E1. Choose the text.** No stop: `rendered`, `fixed=False`. A stop in `HANDOFF_STOPS`: `replies.handoff`, `fixed=True`. Any other stop, the kill switch included: `replies.paused`, `fixed=True`. (Under the kill switch the fixed `paused` text is still delivered on purpose: it holds no model text and tells the person why nobody answers.)
2.  **E2. Deliver once.** `store.touch(run.run_id)`, then `d = hooks.deliver_reply(ReplyEnvelope(tenant, conversation_id, user_id, turn_no=n+1, text, idempotency_key=tenant_key(tenant, conversation_id, str(n+1))))`, wrapped like `_deliver` (never raises; a raise is `d.ok = False`). The hook must return within `CONVERSATION_HOOK_TIMEOUT_S` (30 s), a contract on AK-G22 that `Runtime` does not enforce (BN-17). Audit `conversation/reply` with `_note` (an outcome write that never raises): object ref `tenant_key(tenant, conversation_id, str(n+1))`, keyed digest of the text sent, result `delivered` or `undelivered`, error code `d.reason`.
3.  **E2b. Money card** (only for stop `estimate_exceeded` or `limits_unavailable`; position per OP-4): `store.touch`, then `hooks.post_card` with P4c-2's fixed card text (ids and the code, no turn text), wrapped like `_deliver`, without `_abstain`.
4.  **E3. Hand off?** `handed_off = (stop in HANDOFF_STOPS) or not d.ok`.
5.  **E5 (before E4). Open the item.** If `handed_off`: `store.touch(run.run_id)`, then `hooks.open_handoff(HandoffRequest(tenant, conversation_id, run.run_id, reason=<stop, or "reply_not_delivered">, idempotency_key=run.run_id))`, wrapped. A raise sets the flag `handoff_unavailable` and writes one ERROR log line (ids and class name).
6.  **E4. The one commit.** Unless `handoff_unavailable`: `finish_turn(tenant, conversation_id, run_id, turn_no=n+1, text=<stored or fixed text>, fixed, delivered=d.ok, state="handed_off" if handed_off else "open", mapping=kept, now=models.now())`. `LeaseLost` sets the flag `lease_lost` (nothing was written). Any other exception: the crash rule. With `handoff_unavailable`, E4 is skipped, so `handed_off` is never written without an item. The run ends final at E6, its lease is then dead, and the next claim or the sweep opens the item and takes over (which writes `handed_off`, BN-6).
7.  **E6. The one run transition.** The reason, by fixed precedence: `lease_lost` > `handoff_unavailable` > `reply_not_delivered` (when `not d.ok`) > the stop > `replied`. The state: `STOPPED` for `kill_switch`; `NO_ACTION` for `replied`; else `NEEDS_PERSON`. One `_to(run, state, reason)`, wrapped: if the tick already moved the run (`IllegalTransition` or `StaleState`), write one log line with the ids and make no second transition; the result is then `with_person interrupted` (see OP-3 for the case where E4 committed). The result follows what this exchange wrote to the conversation: `finish_turn` wrote `handed_off` gives `with_person`; `open` with no stop gives `replied`; `open` with a stop gives `paused`; nothing written gives `with_person`. Each result carries `reason`, `run_id`, `turn_no=n` and `delivered=d.ok`, and no text.

### The crash rule (BN-2; replaces the ticket's "Store failures, one rule")

1.  Before the claim commits, a store exception gives `retry`: nothing was accepted.
2.  After the claim commits and before E6, any other `Exception` (not `LeaseLost`, which has its own path at E4) is a crash: one ERROR log line (ids and the class name only), one wrapped `_to(run, NEEDS_PERSON, reason)` with reason `store_unavailable` for a store error class and `internal_error` for anything else, result `with_person`, no delivery and no further store call.
3.  A `BaseException` that is not an `Exception` (for example `KeyboardInterrupt`) is not caught. The lease dies (quiet limit) and the sweep recovers the slot.
4.  After a crash the run is final, so the lease is dead. The next claim or the sweep opens the `interrupted` item and takes over (`handed_off`). PL14's owner-visible sentence: "after a crash, a store fault or a queue outage during an answer, that chat continues with a person, not with the agent".

### Store transaction rules

All methods take `tenant` and filter by it in every statement on the two tables (Postgres: `WHERE tenant = %s AND ...`). Every read also takes `reader` and returns nothing when the reader is not allowed, exactly as for a missing row. Busy, stale, duplicate, reused and lost are results, not errors, so a takeover and its result commit in one transaction. Errors (`ConversationConflict`, `ConversationNotOpen`, `LeaseLost`) derive from `ConversationError(RuntimeError)`; their text gives the class name and ids only.

**The lease rule** (one rule, the tick's): the lease of a conversation is live when `busy_run_id` is set, that run is not final, and its `runs.updated_at` is newer than `now - quiet_s`, where `quiet_s = quiet_limit_s(agent.max_steps, llm settings)`, the formula of `tick.py:100-109` moved into `runtime/runs.py` (960 s for `max_steps` 5 with the real backend defaults; 360 s with the fake model kind). Otherwise it is dead. The store reads the busy run's row in the same transaction. `busy_since` is kept for the record only.

**`claim_turn`** (one transaction; Postgres locks the conversation row first, then reads the busy run's row):

1.  If `state != "open"`: raise `ConversationNotOpen`.
2.  If `message_id` is already stored: if its `text_digest` differs, return `reused` and write nothing (BN-9). If the answer slot of that message holds a turn, return `duplicate` with `first_run_id`. If the slot is empty and the lease is live, return `duplicate` (the caller returns `retry`). If the slot is empty and the lease is dead: without `take_over`, return `lost`; with `take_over` naming the busy run, take over (helper below) and return per OP-2.
3.  If the lease is live: return `busy`, write nothing. (OP-1 recommends that a `take_over` naming the current busy run skip this check.)
4.  If `version != expect_version`: return `stale`, write nothing.
5.  If the lease is dead: without `take_over`, or with a `take_over` that does not name the busy run, return `lost` with `LostExchange(tenant, conversation_id, run_id, turn_no)` and write nothing. With `take_over` naming the busy run: run the takeover helper, then append this message's masked user turn (with `text_digest`, no answer slot, no lease, no run row), `next_turn += 1`, set `mapping`, `version += 1`, and return `recorded` (BN-6).
6.  Otherwise (no lease): append the user turn at `next_turn` (with `text_digest`), `next_turn += 2` (the answer slot is reserved), `busy_run_id = run.run_id`, `busy_since = now`, `mapping = <given>`, `version += 1`, `updated_at = now`, AND insert the run row (`RECEIVED`, as `create_run` writes it). Return `claimed`.

**The takeover helper** (private; called by `claim_turn` and `lost_exchanges`, inside their transaction):

1.  Write the lost exchange's answer slot as the filler: text `defaults.CONVERSATION_LOST_REPLY_TEXT` (`[no answer was given]`), `fixed=True`, `delivered=False`, `run_id` of the lost run. Turns keep alternating.
2.  Clear `busy_run_id` and `busy_since`.
3.  Set `state = "handed_off"` (BN-6).
4.  `version += 1`, `updated_at = now`.
5.  Do not touch `mapping` and do not touch the lost run's row (the tick's `stuck` step moves it to `NEEDS_PERSON interrupted` if it is not final yet).

**`finish_turn`** (one transaction):

1.  If `busy_run_id != run_id`: raise `LeaseLost`, write nothing.
2.  Append the answer turn at `turn_no` (`fixed`, `delivered`).
3.  Clear `busy_run_id` and `busy_since`; set `state`, `mapping` (the `kept` map) and `updated_at`; `version += 1`.

**`record_user_turn`** (one transaction; for a `handed_off` conversation only, else `ConversationNotOpen`):

1.  A stored `message_id`: `reused` if the digest differs, else `duplicate`. Nothing written.
2.  `version != expect_version`: `stale`. Nothing written.
3.  Append the masked user turn (with `text_digest`), `next_turn += 1`, set `mapping`, `version += 1`, return `recorded`. No lease.

**`lost_exchanges(now, quiet_s, take_over=frozenset())`** (runtime identity):

1.  Read every conversation, in every tenant, whose `busy_run_id` is set and whose lease is dead, looking up `quiet_s` by the conversation's `agent_id`; skip a conversation whose agent is not in `quiet_s`. This SELECT is one of the two statements not filtered by tenant (the other is in `purge_conversations`); each write is filtered.
2.  With an empty `take_over`: return the list; write nothing.
3.  For each listed conversation whose busy run id is in `take_over`: one transaction per conversation, the takeover helper. Those are not returned. (OP-1 applies: the recommendation is that the write checks only that `busy_run_id` still equals the named run.)
4.  It uses the partial index on `conversations (busy_run_id) WHERE busy_run_id IS NOT NULL` (BN-15).

**The sweep** (`Runtime.sweep_conversations(now) -> int`, called by the tick step `sweep_conversations`, appended last to `STEPS`; the name `sweep` is taken):

1.  Build `quiet = {agent_id: quiet_s}` for the conversational agents; with none, do nothing.
2.  `found = store.lost_exchanges(now, quiet)`.
3.  For each: the wrapped `open_handoff(HandoffRequest(..., run_id=lost.run_id, reason="interrupted", idempotency_key=lost.run_id))`. A raise leaves that conversation for the next tick, with one ERROR log line (ids, class name).
4.  One call `store.lost_exchanges(now, quiet, take_over=<run ids whose item opened>)`.
5.  Return the number of items opened. In one tick, `stuck` runs first, so quiet runs are already final when the sweep reads them.

**`forget_user(tenant, user_id) -> ForgetReport`** (purge identity, through `app.purge_store`; in pilot/prod `ConfigError` when `app.purge_store is app.store`):

1.  Lock that person's conversations in the tenant (or use one conditional delete; the form must need no new right on PostgreSQL 16 and 17, UNVERIFIED).
2.  If any has a live lease: return `kind="busy"`, write nothing; the caller tries again.
3.  Otherwise, in one transaction: delete the turns, the conversations (with their maps), and, by the run ids named in those turns, the `redaction_maps` rows and the `tool_calls`, whatever `hooks.hold_run_ids` says (BN-11, PL15). `runs` rows and the audit chain stay (no text, no user id). Return `kind="done"` with counts per table.

**`purge_conversations(before) -> int`** (purge identity):

1.  In one transaction: delete conversations with `updated_at < before`, their turns, and the `redaction_maps` rows of the run ids named in those turns, through the same private helper as `forget_user`, whatever the hold says.
2.  `tick.purge_evidence` calls it right after the two 400-day ceilings and BEFORE the hold hook, so a raising hook cannot block conversation retention (BN-11). The step still fails when the hook raises.

**Rights** (BN-15, PL16): `conversations` gets `SELECT, INSERT` plus `UPDATE` on the columns `state, next_turn, version, mapping, busy_run_id, busy_since, updated_at` only, through the new `Grant.runtime_update_cols`; the purge role gets `DELETE` and may read `conversation_id, tenant, user_id, busy_run_id, updated_at`. `conversation_turns` gets `SELECT, INSERT` (append only); the purge role gets `DELETE` and may read `tenant, conversation_id, run_id`. The runtime role can never change `tenant`, `user_id`, `readers` or `agent_id` (negative test A10). Whether PostgreSQL's row lock (`SELECT ... FOR UPDATE`) in `claim_turn` works with column-level UPDATE only is UNVERIFIED here; the Postgres contract rows on 16 and 17 settle it.

### State diagram (text)

Conversation, as stored:

```text
                 start_conversation
                        |
                        v
  +------------------ OPEN, no lease <------------------------------+
  |                     |                                           |
  |        claim_turn   |  (claimed: user turn + run row + lease)   |
  |                     v                                           |
  |               OPEN, lease held by run R                         |
  |      +--------------+-----------------------+                   |
  |      | finish_turn  | finish_turn           | R final, or quiet |
  |      | state=open   | state=handed_off      | past quiet_s      |
  |      | (reply or    | (hand-off stop or     |  => lease DEAD    |
  |      |  paused)     |  reply not delivered) |                   |
  |      v              v                       v                   |
  +-- (back to OPEN,   HANDED_OFF <------- takeover (filler turn,   |
       no lease)        ^   |               lease cleared), only    |
                        |   |               after the item for R    |
     record_user_turn   +---+               was opened (F7 or sweep)|
     (stored, no model, no reply)                                   |
```

There is no way back from `HANDED_OFF` in v1 (V2), and no `closed` state (V13).

Run of one exchange (existing states; no new state):

```text
  (claim_turn) -> RECEIVED -> WORKING --E6--> NO_ACTION replied
                     |           |----E6--> NEEDS_PERSON <stop | lease_lost | handoff_unavailable | reply_not_delivered>
                     |           |----E6--> STOPPED kill_switch
                     |           |--crash-> NEEDS_PERSON store_unavailable | internal_error
                     +-----------+--tick stuck--> NEEDS_PERSON interrupted   (then E6 makes no second move)
```

### Non-functional requirements

- **Security and privacy.** The model sees masked text only. Stored turns are masked, with unsaved placeholders labelled. Logs and audit hold ids, counts, keyed digests and closed codes only (without `restored_key` in dev, a plain hash of masked text). The hand-off item holds ids and a closed reason, no text, no user id. Tenant filter in every statement except the two named full scans. Column-limited runtime UPDATE. The run's principal is `chat:<agent_id>`, and a registered principal starting with `chat:` is a load problem, so no staff right attaches to a chat. Every outbound path is listed in the ticket ("Every outbound text path"); until AK-G22 merges, replies go through neither gate, which is why pilot and prod refuse a conversational agent.
- **Money.** Every model call, the screen's included, runs inside the meter scope and is booked by the wrapper. Meter faults pause the chat; `estimate_exceeded` and `limits_unavailable` also post the fixed money card.
- **Timing.** The lease margin depends on `call_timeout_s` being a per-socket-operation timeout, not a wall clock (`backends/table.py:37-39`, ticket cite), so it is a large margin, not a hard guarantee. E6's wrapped transition covers the rare overrun; OP-1 covers a run that wakes after its item was opened.
- **Rollout and rollback** (BN-13). Revert in the order c, b, a. Reverting AK-G1-a restores the old `Store` protocol. Dropping the two tables cannot be undone; the lead decides, after saving both row counts to `handover/evidence/AK-G1/pre-drop-<sha>.txt`.
- **Owner-visible limits** (the lead edits `owner-visible-limits.md`): BN-1's cost (an earlier message that was not processed must be repeated); PL14's sentence; PL15's sentence ("erasure takes priority over the evidence hold for chat content; this has not been reviewed by counsel"); a crash after delivery and before `finish_turn` leaves history saying "[no answer was given]" for an answer the person saw (PENDING LEAD 2(iv)); one false positive of the injection screen hands a chat off for good.

--------------------------------------------------------------------------------

## Alternatives Considered

### Alternative A: a second agent loop for chats

*   **Pros**: no edit to the hot file's `handle`.
*   **Cons**: duplicates every guard (masking, meter, screen, tool limits), so a fix in one loop can miss the other.
*   **Reason for Rejection**: Rejected by author (ticket D1): one loop, with the read-tool block moved into `_tool_step` and `handle`'s behaviour pinned by its existing tests (T20).

### Alternative B: call `handle` with the history packed as a document

*   **Pros**: no new method.
*   **Cons**: `handle` drops a plain text reply (`agent_loop.py:450-451`, ticket cite) and posts cards a chat must not post.
*   **Reason for Rejection**: Rejected by author (D1).

### Alternative C: a new run state `REPLIED`

*   **Pros**: a clearer run record.
*   **Cons**: a migration of the `runs.state` check for no safety gain.
*   **Reason for Rejection**: Rejected by author (D2): `NO_ACTION replied` carries the same meaning.

### Alternative D: write `handed_off` first, then open the item

*   **Pros**: one store write fewer on the hand-off path.
*   **Cons**: a crash between the two leaves a person told "a person will take over" with no item (R2-ADV-2).
*   **Reason for Rejection**: Rejected by author (D9): deliver, then open the item, then the one commit.

### Alternative E: a separate lease time (`lease_s`)

*   **Pros**: the lease can be tuned apart from the stuck rule.
*   **Cons**: two clocks; a lease shorter than the stuck time lets a healthy exchange lose its lease, a longer one blocks the chat after a crash.
*   **Reason for Rejection**: Rejected by author (R2-ADV-5): the lease is the tick's stuck rule on the existing heartbeat.

### Alternative F: compare `next_turn` instead of a `version` counter

*   **Pros**: no new column.
*   **Cons**: `finish_turn` changes the map without changing `next_turn`, so a stale writer could overwrite a bigger map (R2-ADV-1).
*   **Reason for Rejection**: Rejected by author: every write adds 1 to `version`.

### Alternative G: hand off after a lost exchange only for stops in `HANDOFF_STOPS`

*   **Pros**: a plain crash during an ordinary reply would not end the chat for good.
*   **Cons**: the original stop is not on the record (E6's precedence records `handoff_unavailable`), and the crash window between E2 and E4 stays open, where nobody knows a hand-off was due.
*   **Reason for Rejection**: Rejected by the round 3 resolve (BN-6) and the lead (PL14 (a)): one invariant, item if and only if handed off.

### Alternative H: a `screened` flag on stored turns instead of the label rule

*   **Pros**: the model keeps earlier messages that did pass the screen.
*   **Cons**: needs UPDATE on the append-only turns table (a new runtime right) or a second write path.
*   **Reason for Rejection**: Rejected by the lead (PL12 (a)).

### Alternative I: meter faults as hand-offs, or with no card

*   **Pros**: (hand-off) a person is always pulled in; (no card) less surface.
*   **Cons**: a hand-off ends the chat for a fault in the route or the meter, not in the chat; no card breaks "fail loudly, tell a person".
*   **Reason for Rejection**: Rejected by the lead (PL13 (a)).

### Alternative J: the evidence hold wins over erasure

*   **Pros**: keeps evidence for labelled runs.
*   **Cons**: delete-by-user (R98) would wait up to 400 days.
*   **Reason for Rejection**: Rejected by the lead (PL15 (a)); the owner-visible line says it has not been reviewed by counsel.

### Alternative K: table-wide UPDATE for the runtime role

*   **Pros**: no new `Grant` field.
*   **Cons**: the runtime role could rewrite `tenant`, `user_id`, `readers` or `agent_id`; wider than "exact actions and resources".
*   **Reason for Rejection**: Rejected by the lead (PL16 (a)).

### Alternative L: a separate `ConversationStore` protocol

*   **Pros**: custom stores without chats keep loading.
*   **Cons**: more surface; the loud refusal of an incomplete store (A16) and the CHANGELOG line already cover it.
*   **Reason for Rejection**: Declined in BN-13.

### Alternative M: hold AK-G1-b until the owner answers about read tools

*   **Pros**: one merge with the full shape.
*   **Cons**: blocks every chat on a question only read tools need.
*   **Reason for Rejection**: Rejected in BN-5: AK-G1-c carries read tools.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

No code here. Paths are relative to `<repo>` (`src/hadavin_sdk/...` unless a path starts with `tests/` or `handover/`). "Hot file" means other packages edit it too; merge slots follow order 20 item 5.

### Target Files to Create/Modify

#### AK-G1-a (the store)

1.  **`src/hadavin_sdk/store/migrations/<next>_conversations.sql`** (Create; today the next free number would be `0006`, fixed at merge, A3). The two tables of Interface 3, plus `schema_version INTEGER NOT NULL DEFAULT 1` on both (BN-21), `text_digest TEXT` on `conversation_turns` (BN-9), indexes `(tenant, user_id)` and `(updated_at)`, and the partial index on `busy_run_id` (BN-15). No foreign-key cascade. Why: the store needs the rows; the columns serve the transaction rules above.
2.  **`src/hadavin_sdk/models.py`** (Modify, hot). `Conversation`, `Turn` (with `text_digest`), `USER_ID_PATTERN`; `__repr__` without text, map or reader names. Why: typed records for both stores.
3.  **`src/hadavin_sdk/store/protocol.py`** (Modify, hot). The 9 methods; `ClaimResult` with kinds `claimed`, `recorded`, `busy`, `stale`, `duplicate`, `lost`, `reused`; `LostExchange`; `ConversationError` and its three subclasses; `text_digest` on `claim_turn` and `record_user_turn`. Why: one contract for memory and Postgres; `missing_methods` then refuses an incomplete custom store at start.
4.  **`src/hadavin_sdk/store/memory.py`** (Modify, hot). All 9 methods under the existing lock, the takeover helper, the lease rule reading the run in the same lock. Why: the built alternative and the test store.
5.  **`src/hadavin_sdk/store/postgres.py`** (Modify, hot). The same, with the row lock order (conversation, then run), tenant filters, the shared delete helper for `forget_user` and `purge_conversations`. Why: the neutral default.
6.  **`src/hadavin_sdk/store/migrate.py`** (Modify, hot, P2a). `Grant.runtime_update_cols` (when set, `UPDATE (cols)` instead of table UPDATE; `effective_problems` checks it) and the two `GRANTS` rows. Why: PL16.
7.  **`src/hadavin_sdk/config.py`** (Modify, hot). `Retention.conversations_days` (default 30, ceiling 400). Why: R98 retention.
8.  **`src/hadavin_sdk/runtime/tick.py`** (Modify, hot). In `purge_evidence`, call `purge_conversations(now - conversations_days)` on the purge store right after the two ceilings and before the hold hook; count it in the log line. Why: BN-11, PL15.
9.  **`src/hadavin_sdk/runtime/conversation.py`** (Create). `start_conversation`, the `forget_user` entry point (picks the purge store; `ConfigError` in pilot/prod when it is the runtime store), `ForgetReport`, `TurnResult`, `ReplyEnvelope`, `HandoffRequest`. Why: records shared by -a and -b; the entry point picks the deleting identity.
10. **`src/hadavin_sdk/defaults.py`** (Modify, hot; own block `# --- conversations (AK-G1-a) ---`). `CONVERSATIONS_DAYS`, `CONVERSATION_LOST_REPLY_TEXT`. Why: no hardcoding.
11. **`tests/test_conversation_store.py`** (Create). Rows A1-A10, A12-A22 including A22 (BN-11), the extended A3 (BN-10), A4, A5 (digest, BN-9), A10 (column refusal, BN-15), A18; and the OP-1/OP-2 cases if the lead accepts them. Why: the transaction rules above, as tests.
12. **`tests/contracts/test_store.py`** and **`tests/contracts/kinds/store_postgres.py`** (Modify). Contract rows; `_SplitStore` sends `purge_conversations` and `forget_user` to the purge store (BN-20). Why: Postgres rows run with the purge role's rights only.
13. **`CHANGELOG.md`** (Modify, append only). "The `Store` protocol gains 9 methods; `missing_methods` refuses a custom store without them at start."
14. **Evidence** (`handover/evidence/AK-G1/`): `AK-G1-a-postgres.txt` on PostgreSQL 16 and 17 with `HADAVIN_TEST_PG_DSN` set and 0 skipped conversation rows (BN-14); `AK-G1-a-mutants.txt` with the variable set. Why: Done for -a.

#### AK-G1-b (the turn loop; the (b) shape, no read tools)

15. **`src/hadavin_sdk/runtime/agent_loop.py`** (Modify, hot: P4c, P5c). `handle_turn` (F1-F13, with `redact_untrusted` and `redact_text` called directly in its body); `_end_exchange` (E1-E6, the money card); `sweep_conversations`; `HANDOFF_STOPS`; `_CHAT_RULE`; `_limit_reason`; `_tool_step` (the moved block, for `handle`; no `subject` parameter yet); `_keyed_digest` (renamed `_restored_digest`); `_keep`; the label and render helpers; two `Hooks` fields; `__init__` checks (both hooks set for a conversational agent; `self._quiet`; P5c-3's wrapper check). `handle` maps reason strings back to its old transitions (BN-26). Why: the flow lives here; one loop.
16. **`src/hadavin_sdk/runtime/runs.py`** (Modify, hot). `quiet_limit_s(max_steps, llm)`. Why: one formula for the tick and the lease.
17. **`src/hadavin_sdk/runtime/tick.py`** (Modify, hot). `stuck_after_s` calls `quiet_limit_s`; append the step `sweep_conversations` last. Why: one formula; the sweep.
18. **`tests/test_p7_tick.py`** (Modify, on purpose). The step-list assertion at `:80-89` gains `"sweep_conversations"` as the last element (BN-19). Why: pins the appended step.
19. **`src/hadavin_sdk/registry.py`** (Modify, hot). `ConversationSettings` (even `history_turns`; `max_message_bytes` may only be lowered), `FixedReplies` (defaults from `defaults.py`), `AgentRecord.conversation`, and one new function `_conversation_problems(agents, principals)` called where both are known (BN-23): `scope_allowed` empty, `tools_allowed` empty, `ask_for_person` reserved, no principal id starting `chat:`. Why: load-time refusals.
20. **`src/hadavin_sdk/deferred.py`** (Modify, hot). Pilot/prod refusal of any conversational agent (T19 b). Why: no person-facing path before the wiring ticket.
21. **`src/hadavin_sdk/llm/fake.py`** (Modify, hot). `ScriptedLLM` (dev-only fake kind; records messages, system and tools; `ScriptExhausted`). Why: multi-turn tests with no live model.
22. **`src/hadavin_sdk/guard/producers.py`** (Modify, hot, after P5c-3). One row: "conversation message and reply", `runtime/agent_loop.py`, `handle_turn`, `{redact_untrusted, redact_text}`. Why: the producer check sees both masks.
23. **`src/hadavin_sdk/defaults.py`** (Modify; own block `# --- conversations (AK-G1-b) ---`). `CONVERSATION_HISTORY_TURNS`, `_MAX_MESSAGE_BYTES`, `_MAX_REPLY_CHARS`, `_RETRY_AFTER_S`, `_HIDDEN_TEXT`, `_HOOK_TIMEOUT_S`, `_UNPROCESSED_TEXT`, `_HANDOFF_TEXT`, `_PAUSED_TEXT`.
24. **`tests/conversation_support.py`** (Create). `RecordingRecipient`, `RecordingHandoff` (dedupes on the key), the one-agent qualified fixture (BN-27), crash-injection points (between E2 and E5, between E5 and E4, after E4, before E6), a raising store wrapper, the wrapper-stack helper `MaskedLLM.of(MeteredLLM(ScriptedLLM(...)))` keeping its own reference to the `ScriptedLLM` (BN-4), `run_script`. Why: one harness.
25. **`tests/test_conversation_turns.py`** (Create). F0, T1-T25, T28-T40 with the extended rows of BN-28 (T9 label cases, T15 surrogate, T36 crash rule, T37 hanging hook, T40 money in a chat), and the OP-3/OP-4 cases if accepted. Why: the step list above, as tests.
26. **`CHANGELOG.md`** (Modify, append only).
27. **Evidence**: `AK-G1-b-*.txt`, 107 mutants in the (b) stage (BN-28). `AK-G1-b-notes.txt` records any P4c-2 or P4b1 name that differs on the build base (BN-2).

#### AK-G1-c (only after AK-G1-b merges and the owner picks PENDING LEAD 5 (a))

28. **`src/hadavin_sdk/tools.py`** (Modify, hot, K5 owner). `Subject`, `ToolContext.subject`, `ToolBox.invoke(..., subject=...)`, `ToolSpec.subject_scoped`. Why: read tools bound to the chatting person.
29. **`src/hadavin_sdk/runtime/agent_loop.py`** and **`src/hadavin_sdk/registry.py`** (Modify). `_tool_step`'s `subject` parameter and its plain-callable refusal; F12; the `subject_scoped` load rules replacing "`tools_allowed` empty". Tests T26, T27, the `max_steps` case and mutants M-B12, M-B27, M-B28, M-B53; M-B70 retired. Evidence `AK-G1-c-*.txt`.

#### Not touched by the builder

- `handover/owner-visible-limits.md`, `handover/questions-for-lead.md`, `tickets/AK-G1.md`: the lead edits them.

### Verification Plan

*   **Unit and contract tests**: `uv run --all-extras --group test pytest` on the final head; the 19 existing `.handle(` test files pass unchanged (T20).
*   **Postgres**: contract rows on PostgreSQL 16 and 17, 0 skipped (BN-14).
*   **Static checks**: `ruff check`, `ruff format --check`, `bandit -ll`, the repo guard tests.
*   **Mutation**: 38 A-mutants; 107 B-mutants in the (b) stage, 110 after AK-G1-c (command from P1m's merged docs, UNVERIFIED here).
*   **Design-level checks** (for the reviewers): each invariant I-1 to I-7 has at least one test row; each open point the lead accepts has a test.

--------------------------------------------------------------------------------

### Reconciliation with the concepts brief (draft skill step 6.1)

- **Contradictions:** none. The brief fixed no question differently from this draft.
- **Additions that change behaviour:** OP-1, OP-2, OP-3 and OP-4 are recommendations, not decisions; the brief listed OP-1 to OP-3 as weak points and named no fix. OP-5 and OP-6 are new in the draft. None changes a dependency.

### Additional Resources

*   `tickets/AK-G1.md` (revision 3 FROZEN, build notes, lead answers)
*   `reviews/AK-G1-round3-resolve.md`
*   `LEAD-ORDERS.md` orders 20-36 (order 36 item 82 read in full; the others only by their headings)
*   `designs/ak-g1/concepts_brief.md`

*Drafted with EGM*
