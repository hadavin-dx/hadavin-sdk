# AK-G1 design: the chat turn flow (`handle_turn`) and the conversation store transaction rules

*   **Author:** Claude (git `user.name`), for the lead, order 36 item 82 (PENDING LEAD 11 option (b))
*   **Status:** Draft, revision 2: the review (`reviews/AK-G1-design-review.md`, 31 findings, no Blocker) is resolved in `reviews/AK-G1-design-resolve.md`. Three points wait for the lead ("Open for the lead" below). Next step: the build-start review (order 19 A) reads this design with the ticket.
*   **Date:** 2026-11-06, written about 06:00-06:40 UTC (11:30-12:10 IST; IST = UTC+5:30); revision 2 about 06:50-07:40 UTC (12:20-13:10 IST)
*   **Predecessor:** `designs/ak-g1/concepts_brief.md`
*   **Authority order:** lead answers to PENDING LEAD 11-16 (end of `tickets/AK-G1.md`) > build notes BN-1 to BN-28 (same file, copied from `reviews/AK-G1-round3-resolve.md`) > the frozen ticket body (revision 3). This design changes no lead answer and no build note. Where the ticket body is stale, this design follows the build notes and says so ("Ticket text this design does not follow"). Revision 2 also changes some ticket BODY text to fix defects the design review found; each change is listed in "Ticket text changed by the design review" with its finding id, and the lead may overrule any of them. The ticket file itself is not edited.

--------------------------------------------------------------------------------

## Read this first: limits of this document

- **No project code was run.** No test, lint or mutant was run. One exception in revision 2: a throwaway PostgreSQL 16 server (made-up tables, deleted afterwards) was used to check two facts about the purge role's locks (see `forget_user`). PostgreSQL 17 was not checked.
- **Reviewed once.** Two fresh reviewers (adversarial and correctness) read revision 1; their 31 findings are resolved in `reviews/AK-G1-design-resolve.md`. No fresh reviewer has read revision 2. The brainstorm's own Goldfish review never ran.
- **Read in code for revision 2 (2026-11-06, about 06:50-07:10 UTC / 12:20-12:40 IST):** `runtime/runs.py:10-42` (`RECEIVED` and `WORKING` may move to `NEEDS_PERSON`; `NEEDS_PERSON` is final; `advance` is a compare-and-set on the state), `store/memory.py:61-90` and `store/postgres.py:257-280` (`transition` raises `StaleState` when the state moved; `touch` checks nothing), `runtime/tick.py:111-143` (the `stuck` step writes reason `interrupted` for `RECEIVED` and `WORKING`; at `:130` a run is stuck only when `updated_at` is strictly older than `now` minus its stuck time), `runtime/agent_loop.py:256-267` (`_restored_digest` takes a dict), `:310-316` (`_screen` charges the limits and the run cost itself), `:318-320` (`_to` reads the state, then calls `advance`), `guard/judge.py:62-96` and `app.py:163-166` (the `llm_judge` screen calls the model object it is built with), `store/migrate.py:45-48` (the purge role may read only `run_id`, `state`, `updated_at` of `runs`).
- **Interactive gates skipped.** Both EGM skills ask the author to approve each section. The brief asked for AUTO mode, so I wrote all sections in one pass and chose nothing the ticket and the lead's answers had not already fixed.
- **Read in code by me (2026-11-06, about 05:50-06:00 UTC / 11:20-11:30 IST):** `runtime/runs.py:8-42` (allowed run state moves; `STOPPED` from any non-final state), `runtime/tick.py:98-135` (stuck-run time and the `stuck` step), `:184-218` (`purge_evidence`, the hold hook re-raises), `:245-268` (`STEPS`; `stuck` runs before any appended step), `store/memory.py:83-90` and `store/postgres.py:279-280` (`touch` moves `updated_at` and checks no state), `runtime/agent_loop.py:560-567` (`_deliver` never raises), `store/migrate.py:24-40` (`Grant` has no column-limited runtime field today). The `runtime/` folder has no `conversation.py` yet; migrations `0001` to `0005` exist.
- **Not read by me, taken from the ticket and its resolve (UNVERIFIED here):** every other line cite in this document; the P4c-2, P4b1-b, P5c-2, P5c-3 and AK1 names (`MeterError`, the rule-6 codes, `scope.refusal`, `MaskedLLM.of`, `llm.run`, `SessionClosed`, `tenant_key`); whether the manifest tool path stores only masked text in `tool_calls`; whether the purge role can lock rows on PostgreSQL 16 and 17.

## Words used

Plain meanings, one meaning each. They are the ticket's words.

- **person**: the human who writes to the agent. **user id**: the made-up, opaque id of that person (for example `user-1`; never an e-mail address).
- **conversation** (or chat): one chat between one person and one agent, an ordered list of **turns**. A turn is one message, the person's (role `user`) or the agent's (role `assistant`). Until a hand-off, turns alternate, so user turns have odd numbers and answers even numbers. After a hand-off, the person's later messages follow one another with no answer between them, so the numbers no longer tell the role. Code always reads the role from the turn's `role` column, never from its number. An **exchange** is the person's turn plus the agent's answer turn.
- **fixed reply**: a reply whose words come from configuration, not from the model (the `handoff` and `paused` texts, and the lost-answer filler `[no answer was given]`).
- **hand-off**: the agent stops answering in this conversation for good, and one item goes into the "needs a person" queue (AK-G15).
- **mask / placeholder / label**: before text goes to the model, a protected value such as an e-mail address is replaced by a placeholder such as `<EMAIL_1>`. A **label** is the text `[hidden email]` shown in place of a placeholder. The **conversation map** is the saved list "placeholder -> original value" for one conversation (identifier kinds only).
- **lease**: the claim one exchange holds on a conversation while it is being answered, so two messages of one conversation are never answered at the same time. It is **live** while its run is not final and the run's last heartbeat (`store.touch`) is not older than the agent's **quiet limit** (the stuck-run time of `tick.py:100-109`). Otherwise it is **dead**.
- **lease token**: the value of `version` that an exchange's claim wrote. The exchange carries it, and `finish_turn` commits only when the stored `version` still equals it.
- **fence**: the store step that ends a lost exchange's claim on the conversation BEFORE anyone opens the "needs a person" item for it. In one transaction it adds 1 to `version`, so the old lease token no longer matches, and it moves the lost run to the final state `NEEDS_PERSON` with reason `interrupted`, so the lease can never come back to life (a final run never leaves its state). OP-1 explains both parts.
- **run check**: one read of the run's own row (`store.get_run`) that `handle_turn` makes before each model call and before each hook call. When the run is already final (fenced, or moved by the tick), the exchange takes the **lease-lost path**: no more model calls, no more deliveries, no store write except the logged attempt at E6.
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

1.  One numbered step list for an exchange, F1 to F13 and E1 to E7 (E7, the money card, is new in revision 2), with every build note that touches the flow applied, where each step names its store call, its run state change, its delivery and the result it returns when it ends the call.
2.  One numbered rule list for each store transaction: `claim_turn`, `finish_turn`, `record_user_turn`, the private fence and takeover helpers, `lost_exchanges`, `forget_user` and `purge_conversations`.
3.  These invariants, stated so a test can check each one:
    - **I-1.** Every call returns exactly one result, or raises in F1 (a host programming error). No `Exception` leaves `handle_turn` after F1: before the claim commits, any `Exception` gives `retry` (crash rule, point 1); after it, the crash rule applies.
    - **I-2.** Every run that is created makes exactly one state change after `WORKING`, and gets at most one delivery attempt.
    - **I-3.** A conversation has at most one live lease.
    - **I-4.** Once the takeover or the hand-off commits: a "needs a person" item exists for the exchange if and only if the conversation is `handed_off` (BN-6). Revision 2 closes the path revision 1 left open (a quiet run that wakes after its item was opened): the fence makes the run final before the item, and `finish_turn` refuses a final run.
    - **I-5.** A placeholder never stands for two values in one conversation. Every placeholder in stored text has its value in the saved map, or has been turned into a label.
    - **I-6.** No turn text, exception text or user id reaches a log line, an audit event or the hand-off item.
    - **I-7.** After a hand-off or a fence commits, no new exchange starts in that conversation, and no exchange commits anything to it except through the takeover. Said plainly: a run that was fenced while it was still working may finish ONE model call or ONE delivery that had already started before its last run check; it starts no further one. (Revision 1 said "the agent never calls the model again"; that was not true, because `touch` checks no state.)
    - **I-8.** `finish_turn` commits only while the conversation names this run as busy AND this run is not final.
4.  The list of every file each sub-PR touches, and why.

## Non-Goals

- Wiring AK-G22 (the gate for text sent to a person) and AK-G15 (the "needs a person" queue) into `app.build` (row V12). Until then, the blanket pilot/prod refusal (T19 b) keeps every chat out of pilot and prod.
- The chat window and the transport.
- Actions from a chat (V11), summaries (V1), putting hidden values back into replies (V3), giving a chat back to the agent (V2), closing a chat (V13), voice and attachments (V6), streaming (V7).
- Read tools in a chat. They come in AK-G1-c, only after the owner picks PENDING LEAD 5 (a). This document describes the (b) shape that AK-G1-b builds, and marks the AK-G1-c parts.
- Any change to the frozen ticket text.

## Open Points (found while drafting; decided in the resolve, revision 2)

Revision 1 left six open points with recommendations. The resolve (`reviews/AK-G1-design-resolve.md`) decided each one. The decisions are written into the steps and rules below. Nothing here changes a lead answer or a build note.

- **OP-1. A dead lease can come back to life after its item was opened.** *Decided: replaced by the two-part fence (DES-ADV-1, DES-COR-4; lead order 38 item 85, "a monotonic lease token checked on every write").* Revision 1's fix (take over without the liveness check) was not enough: `finish_turn` checked only `busy_run_id`, so a slow run could still commit `open` between the item and the takeover. The fence has two parts, and both run in ONE store transaction, under the conversation row lock, at the moment a caller learns of a lost exchange (`claim_turn` returning `lost`, or `lost_exchanges` listing it):
    1. **Lease token (the conversation side).** The token is the conversation's existing `version` counter. It only ever goes up, and every write to the conversation row already adds 1 to it. The claim hands this exchange its token (the version after the claim). The fence adds 1 to it. `finish_turn` and the takeover each commit only when the token they carry equals the stored one. So once the fence commits, the old exchange can never write to the conversation again, whatever its heartbeat does. No new column and no new right are needed: `version` is already in PL16's column list.
    2. **Final run state (the run side).** In the same transaction the fence moves the lost run from `RECEIVED` or `WORKING` to `NEEDS_PERSON` with reason `interrupted`, by compare-and-set. `runtime/runs.py:11-12` allows both moves, and `tick.py:111-113` writes the same reason for a stuck run. A run that is already final is left as it is. This part keeps the lease dead for good: a final run never leaves its state, so a later `touch` cannot make the lease live again. Without it, a woken run would look live to the sweep, and a conversation whose item failed to open would not be found again. It also drives the run check, which stops the woken run from starting another model call or delivery.

  The cost, said plainly: a run that is really still working, but has been quiet longer than its quiet limit (16 minutes with the real model settings), is treated as lost. It gets `LeaseLost` at E4, the history shows `[no answer was given]`, and the chat goes to a person. The person may already have seen that slow reply, or may still receive it if the delivery had started before the fence. See "Owner-visible limits".
- **OP-2. The takeover for a resent lost message.** *Decided: the recommendation stands* (both reviewers: sound). For a duplicate message id, the takeover writes the filler, clears the lease, sets `handed_off`, adds 1 to `version`, appends nothing, and returns `duplicate` with `lost` set. `handle_turn` returns `with_person`, `delivered=False`. For a new message id it returns `recorded` (BN-6). This matches the ticket's row A5.
- **OP-3. The result when the tick moved the run after `finish_turn` committed.** *Decided: the recommendation stands, extended by DES-ADV-2.* When E4 committed, the outcome follows the conversation (`replied`, `paused` or `with_person`, by the mapping rule), and `interrupted` stays on the run record only. When E4 did not commit, the outcome is `with_person`. When `finish_turn` raised something other than `LeaseLost`, one read of the answer slot decides which case holds (E4).
- **OP-4. Where the money card goes.** *Decided: after E6, as step E7 (DES-ADV-5).* Revision 1 put it between E2 and E4, inside the window where a crash or a hanging hook turns a passing fault into a permanent hand-off.
- **OP-5. Where the report paths are recorded.** *Decided:* the files stay in `handover/designs/ak-g1/` and `handover/reviews/`, as the ticket's PL11 line says. Order 36's `egm/hadavin-sdk/ak-g1/` is a folder in the lead's own notes, which this repository does not hold. The lead records the paths there.
- **OP-6. A takeover from `claim_turn` with a version that moved.** *Decided: the recommendation stands, adjusted for the fence.* A `lost` result now adds 1 to `version` (the fence) and returns the new value. F7's second call passes that value as both `expect_version` and the takeover token. If another writer committed in between (for example the sweep's own takeover), the second call sees `ConversationNotOpen` (go to F5 after one re-read) or `stale` (back to F3 once, then `retry`).

## Open for the lead (NEEDS LEAD; the builder applies the "meanwhile" text until the lead answers)

- **NEEDS LEAD 1 (redaction): new map entries after a hand-off** (DES-ADV-4). F5 saves `_keep(rmap)` for every later message of a handed-off chat, so original values (personal data) keep piling up in `conversations.mapping` with no limit. Nothing in v1 reads those originals: there is no put-back (V3) and the hand-off item holds no text. Options: (a) save new values only while the stored map stays within `max_map_entries`; beyond that, new values are stored as labels; (b) never save new values after a hand-off: every new value in a later message is stored as `[hidden <kind>]`, and the person who takes over sees the label, not the value; (c) keep the ticket's INFORM I13 as written (no limit). **Recommendation: (b)**, the least personal data at rest, because nobody reads it in v1. **Meanwhile:** (a), which only ever stores less than the ticket does.
- **NEEDS LEAD 2 (erasure and retention, R98): a handed-off chat can be purged while its item is still open** (DES-ADV-8). `purge_conversations` deletes by `updated_at` age (default 30 days). A chat that waits longer than that for a person loses its turns. Options: (a) keep the purge as it is and add an owner-visible sentence; the store cannot see AK-G15's queue; (b) skip conversations whose item is still open, which needs a read hook into AK-G15 and keeps data past the contract's retention; (c) require the queue's service time to be shorter than `conversations_days`, written in the client contract. **Recommendation: (a) plus (c).** **Meanwhile:** (a).
- **NEEDS LEAD 3 (erasure, PL15 wording): does the age-out purge also delete chat runs' tool calls?** (DES-COR-9). PL15 says "forget_user and the conversation purge delete chat runs' maps and tool calls even when the hold names them". BN-11 and the ticket's D5 say the age-out purge deletes maps only, and tool calls keep their own `tool_calls_days`. The lead's answer wins over the build note, but its wording can be read either way. Options: (a) read PL15 literally: `purge_conversations` also deletes those runs' tool calls; (b) maps only, as BN-11 says. **Recommendation: (a)** (it deletes more, so it can only help R98). In the (b) shape a chat run writes no tool call, so this matters only from AK-G1-c. **Meanwhile:** (b), which is the built text, and AK-G1-c may not merge until the lead answers.
- **NEEDS LEAD 4 (erasure, R98): a fenced run's late map write.** The lease token guards every write to the two conversation tables. A run's own writes to `runs` and `redaction_maps` (`touch`, `_save_map`) are existing core methods that do not carry the token. A fenced run that is in the middle of F8 can still save its run map after `forget_user` has run. That map then ages out under `redaction_maps_days`, the ticket's accepted limit 2(vi). Options: (a) a run check right before `_save_map` (applied in F8 below; no new surface; it narrows the window but does not close it); (b) a token-checked map write for chat runs, which changes the `Store` protocol of an existing method. **Recommendation: (a).** **Meanwhile:** (a).

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
| Interface 2: `claim_turn(...)` and `record_user_turn(...)` signatures without `text_digest` | BN-9: both take `text_digest` |
| Interface 3: `"conversations": Grant("table", "SELECT, INSERT, UPDATE", ...)` | BN-15 and PL16: `SELECT, INSERT` plus column-limited UPDATE |

Two build notes are not repeated in this design because they do not touch the flow or the store rules: BN-18's ADV-19 line (a "checked and not used" list entry) and BN-24 (clocks in tests, which the builder applies to the test rows). Both still apply.

## Ticket text changed by the design review (revision 2; the lead may overrule any row)

These rows change frozen ticket BODY text, not a lead answer or a build note. Each fixes a defect a reviewer found; the resolve file gives the evidence.

| Ticket text | Changed to | Finding |
|---|---|---|
| F6 row and F6 note: `lost` "nothing written"; Interface 2: `lost_exchanges` "With an empty `take_over` it writes nothing" | A `lost` result fences: one transaction adds 1 to `version` and moves the lost run to `NEEDS_PERSON interrupted`. `LostExchange` gains `version` and `fenced` | DES-ADV-1, DES-COR-4, order 38 item 85 |
| Interface 2: `finish_turn` checks the lease by `busy_run_id` only | `finish_turn` also takes `lease_token` and refuses when `version` differs or the busy run is final | DES-ADV-1 |
| Interface 2: `lost_exchanges(..., take_over: frozenset[str])` | `take_over: Mapping[str, int]` (run id to the version the fence returned), plus `limit` (oldest first, default 100) | DES-ADV-1, DES-ADV-7 |
| Interface 2: `forget_user(tenant, user_id)` | `forget_user(tenant, user_id, *, now, quiet_s: float)`, one conditional DELETE | DES-COR-1, DES-COR-12 |
| Interface 3: user turns may have `run_id` NULL | the claim writes the run id on the user turn | DES-ADV-3 |
| Takeover helper: "do not touch the lost run's row" | unchanged in the helper; the fence before it makes the run final | DES-ADV-1 |


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
*   **Host contract** (DES-ADV-11): when a result is `with_person` with `delivered=False`, `handle_turn` sent the person nothing in this call. The host shows its own fixed notice (for example "a person will reply here"). It must not call the model or wait for a reply from the agent.

### CUJ 3: a provider outage

*   **Given**: as CUJ 1, and the model provider fails.
*   **When**: `llm.chat` raises `ProviderError`.
*   **Then**: the fixed `paused` reply is delivered; the chat stays `open`; no item is opened; run `NEEDS_PERSON provider_error`; result `paused`. On the next exchange, the earlier user message is shown to the model as `[an earlier message was not processed]` (BN-1).

### CUJ 4: a crash in the middle of an answer

*   **Given**: an exchange whose process died after delivery and before `finish_turn`.
*   **When**: the person writes again after the quiet limit, or the person never writes again and the tick runs.
*   **Then**: the next claim (F6 `lost`, F7) or the sweep first fences the lost exchange (adds 1 to `version`; the run becomes `NEEDS_PERSON interrupted` if it was not final yet), then opens one `interrupted` item for the lost run, then the takeover writes the filler `[no answer was given]` (`delivered=False`), clears the lease and sets `handed_off`. The new message, if any, is stored with no model call; result `with_person`. One item exists, whichever came first.

### CUJ 5: an answer that is slower than the quiet limit

*   **Given**: as CUJ 1, but the model call (or a hook) blocks for longer than the agent's quiet limit (960 s with the real model settings).
*   **When**: the person writes again, or the tick runs the sweep.
*   **Then**: the fence ends the slow exchange's claim. When the slow process wakes, its next run check sees a final run and stops: no further model call, no delivery that had not already started. If its delivery had already started, the person may still get that reply. Its `finish_turn` gets `LeaseLost` and writes nothing. The history shows `[no answer was given]`, one `interrupted` item exists, and the chat is `handed_off`. Result of the slow call: `with_person`, reason `interrupted` (the reason the fence wrote on the run).

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
 |  _end_exchange: E1 -> E2 deliver -> E3 -> E5 open_handoff -> E4 finish -> E6 -> E7 card   |
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
            |        (fence, then item, then takeover)
```

`handle_turn` sits beside the existing `handle`. Both use the read-tool block of `handle`, moved into `_tool_step` (D1); a chat run in the (b) shape never calls it. A chat run never calls `_abstain`, `_shadow` or `_submit`, so it posts no approval card. The one card it can post is P4c-2's fixed money card (BN-2, PL13).

### Fixed sets

- **`HANDOFF_STOPS`** (a constant in `runtime/agent_loop.py`, not config, D6): `asked_for_person`, `injection_suspected`, `unknown_action`, `reply_not_delivered`, `conversation_too_long`.
- **Passing faults** (every other stop): `provider_error`, `provider_exhausted`, `limits.<x>` (for example `limits.daily_budget`), `run_budget`, `kill_switch`, `max_steps` (AK-G1-c only, BN-3), `llm_max_tokens`, `llm_refusal`, `empty_reply`, `reply_too_long`, `tool_error`, `evidence_unavailable`, `document_too_complex`, `redaction_error`, `guard_unavailable`, `estimate_exceeded`, `limits_unavailable` (BN-2).
- **Refusal reasons** (F1-F5, nothing accepted beyond one audit event): `message_unreadable`, `message_too_large`, `empty_message`, `unknown_conversation`, `redaction_error`, `message_too_complex`, `message_id_reused`.
- **Reasons only on the run record**: `replied`, `lease_lost`, `handoff_unavailable`, `store_unavailable`, `internal_error`, `interrupted` (written by the tick's `stuck` step or by the fence).

**Order of execution in `_end_exchange`** (DES-ADV-15): E1, E2, E3, E5, E4, E6, E7. The ids E4 and E5 are kept from older rounds, so E5 runs before E4.

### The exchange, step by step (F1 to F13)

Names used below: `rmap` is this exchange's map, `RunMap(conversation.mapping)`, grown by masking (and by tool results in AK-G1-c). `_keep(m)` is `runmap.storable(m, self._kinds)`, the only way the flow calls `storable`, so a client's narrower `stored_kinds` applies everywhere. `label_unsaved(t, kept)` turns every exact placeholder in `t` whose key is not in `kept` into `[hidden <kind>]`. `render(t)` rewrites every placeholder-shaped text, look-alikes included, into a label. Steps F1 to F5 create no run, call no model and deliver nothing.

1.  **F1. Inputs.** The agent must be in `self.agents`; if not, raise `Unqualified`. If the agent has no `conversation` setting, raise `ValueError("agent is not conversational")` (BN-18). `type(text) is str`. `conversation_id` fully matches `conv-[0-9a-f]{32}`; `message_id` and `user_id` fully match their patterns. A bad input raises `ValueError` naming the field only, never its value. Then make the run id: `run_id = new_id("run")`. Every refusal event of this call carries it; it becomes the run's id only if the claim commits.
2.  **F2. Readable, size, not empty.** In this order: (a) `text` must encode as UTF-8 (no lone surrogate), else `refused message_unreadable` (BN-12); (b) its UTF-8 length must be at most `max_message_bytes`, else `refused message_too_large`; (c) `text.strip()` must not be empty, else `refused empty_message`. Each refusal first writes one `conversation/refused` audit event with `write_intent` (which raises on failure), with principal `chat:<agent_id>`, source `runtime`, domain `conversation`, operation `refused`, and the pre-made run id (BN-18 COR-14). If that write raises `AuditUnavailable`, return `retry`. Nothing is masked or stored.
3.  **F3. Read and owner check.** `get_conversation(tenant, conversation_id, reader=user_id)`. Then require `conversation.user_id == user_id` and `conversation.agent_id == agent_id`. A missing row, another tenant, a reader not allowed, a caller who is not the owner, or another agent's chat all give one answer: `refused unknown_conversation`, audited as in F2. A store exception gives `retry`.
4.  **F4. Mask and map size.** `masked = redact_untrusted(text, rmap)` (through P5c's session once P5c-2 merged), called directly in the body of `handle_turn` (BN-18 COR-13). `stored_user = label_unsaved(masked, _keep(rmap))`. `added = len(rmap) - len(conversation.mapping)`. A redaction failure gives `refused redaction_error`; `InputTooLarge` or `added > max_map_entries` gives `refused message_too_complex`; both audited as in F2. If the STORED map is already at or over `max_map_entries`, do not refuse: set stop `conversation_too_long` and continue (it hands off once at E1, after the claim, with no screen and no model call). Compute `text_digest = _keyed_digest(stored_user)` (BN-9).
5.  **F5. Handed-off chat.** If `state == "handed_off"`: first apply the map limit (NEEDS LEAD 1, meanwhile option (a)). If `len(conversation.mapping) + added > max_map_entries`, every new value becomes a label: `stored_user = label_unsaved(masked, conversation.mapping)`, the digest is computed again from it, and the map passed on is `conversation.mapping` unchanged. Then `record_user_turn(..., expect_version=conversation.version, text=stored_user, text_digest, mapping=<_keep(rmap), or the unchanged map>)`. `recorded` returns `with_person`, `delivered=False`, no model call. `duplicate` returns `with_person`, nothing written. `reused` returns `refused message_id_reused`, audited as in F2. The first `stale` goes back to F3 once; the second gives `retry`. `ConversationNotOpen` (the row was deleted by erasure meanwhile, DES-ADV-13) goes back to F3 once, which then gives `refused unknown_conversation`. A store exception gives `retry`.
6.  **F6. Claim.** `claim_turn(..., run=Run(run_id=<pre-made>, agent_id, principal_id="chat:<agent_id>", trigger_kind="user", trigger_ref="<conversation_id>:<n>"), message_id, expect_version, text=stored_user, text_digest, mapping=_keep(rmap), now=models.now(), quiet_s=self._quiet[agent_id], take_over=None)`. Results:
    - `claimed`: the run row (`RECEIVED`), the user turn (carrying this run's id, DES-ADV-3) and the lease committed together. Continue with `turn_no = n` (answer slot `n + 1`) and `token = <the version the claim wrote>` (the lease token).
    - `busy`: `retry`.
    - `stale`: the first time back to F3; the second time `retry`.
    - `lost` (a dead lease): the store has fenced it in this call (`version` + 1; the run moved to `NEEDS_PERSON interrupted` unless it was already final) and wrote nothing else. Go to F7.
    - `duplicate` with its answer slot filled: map from the stored conversation and that turn (BN-25): `handed_off` gives `with_person`; `open` with `fixed=False` gives `replied`; `open` with `fixed=True` gives `paused`; `delivered=False` in all three (this call delivered nothing).
    - `duplicate` with an empty slot and a live lease: `retry`. With an empty slot and a dead lease the store returns `lost` instead (F7).
    - `reused`: `refused message_id_reused`, audited as in F2 (BN-9).
    - `ConversationNotOpen`: re-read once (F3) and take the F5 path, or `refused unknown_conversation` when the row is gone.
    - A store exception: the claim and the run row commit together or not at all, but the caller cannot always tell which (a lost commit acknowledgement, DES-ADV-2's class). So make ONE read, `get_conversation`: if `busy_run_id` equals this call's run id, the claim committed; continue as `claimed`, with the token read from that row. Otherwise, or if the read fails, `retry`.
7.  **F7. Lost exchange.** There is no run for this call yet. If `lost.fenced` is true (this call's fence moved the lost run), first write one `run/state` outcome event for that run, as the tick's `stuck` step does (`tick.py:133-143`), but with principal `chat:<agent_id>` and source `runtime`. Use `_note`, which never raises. Then call `open_handoff(HandoffRequest(tenant, conversation_id, run_id=lost.run_id, reason="interrupted", idempotency_key=lost.run_id))`, wrapped. If it raises: one ERROR log line (ids and class name only) and `retry`; nothing was written. If it returns: call F6 again with `take_over=lost.run_id` and `expect_version=lost.version` (the version the fence wrote; it is also the takeover token). The store writes the takeover (filler, lease cleared, `handed_off`) and then records this message without a lease, and returns `recorded` (BN-6), which gives `with_person`, `delivered=False`, no model call, `run_id=None` (this call created no run, DES-COR-15) and `turn_no` = the number of the stored user turn. For a resend of the lost message, see OP-2. A second `lost` naming another run gives `retry`; `stale` goes back to F3 once; `ConversationNotOpen` goes to F5 after one re-read (OP-6).
8.  **F8. Run start.** Audit `run/received` with `inputs_hash = _keyed_digest(masked)`. `_to(run, WORKING)`; if it raises `IllegalTransition` or `StaleState`, the run was fenced or moved by the tick: take the lease-lost path. Enter `with self.llm.inner.scope(agent_id, run_id=run.run_id)` (the meter scope, BN-8) and `with self.llm.run(run.run_id, principal, seed=rmap)` (the mask session; always, there is no fallback, BN-4). If F4 set `conversation_too_long`: go to E1 now, before the map save, so no later stop can replace that reason (DES-COR-13). Run check (NEEDS LEAD 4, meanwhile (a)); then `_save_map(run, rmap)` (the run's own copy in `redaction_maps`). If `_save_map` fails: stop `evidence_unavailable`, go to E1. Any other exception: the crash rule.
9.  **F9. Screen the message.** `_screen(run, masked, "user")`. Its cost is booked ONCE (BN-8, DES-COR-2). Today `_screen` books it itself (`agent_loop.py:310-316`: `limits.charge` and `store.add_cost`), and the `llm_judge` screen calls the model object it was built with (`guard/judge.py:68-78`, built at `app.py:165`). If that object is the metered wrapper on the build base, the wrapper also books the call, so the cost would be booked twice. Rule: in a chat run the screen's cost is booked by exactly one of the two. BN-8 says `handle_turn` never books cost itself, so when the judge's call goes through the metered wrapper, `handle_turn` uses the screen without `_screen`'s own booking (a flag or a second private helper; `handle` keeps today's behaviour). The builder records which case holds on the build base in `AK-G1-b-notes.txt`. T21 gains the case "a model-backed screen's cost is booked exactly once". Then read P4c-2's per-run signal and `scope.refusal` as `handle` does (BN-2). A flag gives stop `injection_suspected` (hand-off) or `guard_unavailable` (passing fault); a meter refusal gives its rule-6 code. Go to E1 on any stop.
10. **F10. Model step**, a bounded loop `for _step in range(agent.max_steps)`: `_limit_reason(run)`; a value (`kill_switch`, `limits.<x>`, `run_budget`) is the stop, go to E1. `store.touch(run.run_id)`, then the run check: a final run takes the lease-lost path, with no model call (DES-COR-4). On the first step only, build `messages` from `list_turns(..., before_turn_no=n, last=history_turns)`, oldest first; for each pair whose assistant turn has `fixed=True`, give the user turn as `[an earlier message was not processed]` (BN-1, PL12); then append the new masked user turn once. `system` = agent prompt + `_CHAT_RULE`. `tools` = `ask_for_person` only (AK-G1-c adds the agent's `subject_scoped` tools). Call `self.llm.chat(messages, system, route, tools, documents=[])`.
11. **F11. Model answer.** `ProviderError` gives stop `provider_error` or `provider_exhausted`. A separate `except MeterError` gives P4c-2's rule-6 code: `kill_switch`, `run_budget`, `limits.daily_budget`, `limits.monthly_budget` or `limits_unavailable`, with no card and no `_abstain` (BN-2). After the call, read the per-run signal: overshoot gives `estimate_exceeded`, a settle failure gives `limits_unavailable`. `stop_reason` `max_tokens` or `refusal` gives `llm_max_tokens` or `llm_refusal`. No tool call goes to F13. First tool call `ask_for_person` gives `asked_for_person`. Any other tool call gives `unknown_action` (in the (b) shape; AK-G1-c sends an allowed tool to F12). The end of the loop gives `max_steps` (reachable only with read tools, BN-3). Every stop goes to E1.
12. **F12. Tool step (AK-G1-c only).** `reason = self._tool_step(..., subject=Subject(tenant, conversation.user_id))`. A reason is the stop, go to E1; `None` goes back to F10.
13. **F13. Reply.** First take `kept = _keep(rmap)` (BN-16). Then `r = redact_text(reply.text, rmap)`, called directly in the body of `handle_turn`. `RedactionError` or `InputTooLarge` gives stop `redaction_error` (BN-2). Empty after stripping gives `empty_reply`; longer than `max_reply_chars` gives `reply_too_long` (never cut before masking). Otherwise `rendered = render(r)` and `stored = label_unsaved(r, kept)`. So a value that first appears in the model's reply is a label in the stored answer and never enters the saved map. Go to E1 with no stop.

### Ending the exchange (`_end_exchange`, E1 to E7)

Every path from F8 on ends here exactly once, or in the crash rule. The ticket keeps the ids E4 and E5 from older rounds; E5 runs BEFORE E4. The order of execution is E1, E2, E3, E5, E4, E6, E7.

**The lease-lost path** (new in revision 2). A run check that finds the run final (fenced, or moved by the tick), a `_to(run, WORKING)` at F8 that finds the run already moved, and a `LeaseLost` at E4 all set the flag `lease_lost`. From a run check or F8, the exchange skips whatever remains of E1 to E5 and E4: no further delivery, no item, no conversation write. In every case it goes to E6. When the run is already final, E6's transition fails and writes one log line; otherwise (for example `finish_turn` found the row deleted by erasure) E6 writes `NEEDS_PERSON lease_lost`. The result is `with_person` with the reason that is now on the run record: `interrupted` when the tick or a fence moved the run (as BN-17's T37 variant expects), `lease_lost` when E6 wrote it; `delivered` says whether E2 had already delivered. The fencer (F7 or the sweep) opens the `interrupted` item and takes over.

1.  **E1. Choose the text.** No stop: `rendered`, `fixed=False`. A stop in `HANDOFF_STOPS`: `replies.handoff`, `fixed=True`. Any other stop, the kill switch included: `replies.paused`, `fixed=True`. (Under the kill switch the fixed `paused` text is still delivered on purpose: it holds no model text and tells the person why nobody answers.)
2.  **E2. Deliver once.** `store.touch(run.run_id)`, then the run check (a final run takes the lease-lost path and nothing is delivered), then `d = hooks.deliver_reply(ReplyEnvelope(tenant, conversation_id, user_id, turn_no=n+1, text, idempotency_key=tenant_key(tenant, conversation_id, str(n+1))))`, wrapped like `_deliver` (never raises; a raise is `d.ok = False`). The hook must return within `CONVERSATION_HOOK_TIMEOUT_S` (30 s), a contract on AK-G22 that `Runtime` does not enforce (BN-17). Audit `conversation/reply` with `_note` (an outcome write that never raises): object ref `tenant_key(tenant, conversation_id, str(n+1))`, keyed digest of the text sent, result `delivered` or `undelivered`, error code `d.reason`.
3.  **E3. Hand off?** `handed_off = (stop in HANDOFF_STOPS) or not d.ok`.
4.  **E5 (before E4). Open the item.** If `handed_off`: `store.touch(run.run_id)`, then the run check (a final run takes the lease-lost path: the fencer opens the item under the same idempotency key), then `hooks.open_handoff(HandoffRequest(tenant, conversation_id, run.run_id, reason=<stop, or "reply_not_delivered">, idempotency_key=run.run_id))`, wrapped. A raise sets the flag `handoff_unavailable` and writes one ERROR log line (ids and class name).
5.  **E4. The one commit.** Unless `handoff_unavailable`: `finish_turn(tenant, conversation_id, run_id, lease_token=token, turn_no=n+1, text=<stored or fixed text>, fixed, delivered=d.ok, state="handed_off" if handed_off else "open", mapping=kept, now=models.now())`. `LeaseLost` sets the flag `lease_lost` (nothing was written). Any other exception (DES-ADV-2): the commit may have happened without its acknowledgement reaching the caller, so make ONE read of the answer slot (`list_turns` for `turn_no=n+1`). If the slot holds a turn with this run's id, E4 committed: go on to E6 as if it had returned. If the slot is empty, or the read fails: the crash rule. With `handoff_unavailable`, E4 is skipped, so `handed_off` is never written without an item. The run ends final at E6, its lease is then dead, and the next claim or the sweep fences, opens the item and takes over (which writes `handed_off`, BN-6).
6.  **E6. The one run transition.** The reason, by fixed precedence: `lease_lost` > `handoff_unavailable` > `reply_not_delivered` (when `not d.ok`) > the stop > `replied`. The state: `STOPPED` for `kill_switch`; `NO_ACTION` for `replied`; else `NEEDS_PERSON`. One `_to(run, state, reason)`, wrapped: if the run was already moved by the tick or the fence (`IllegalTransition` or `StaleState`), write one log line with the ids and make no second transition. **The result follows what this exchange wrote to the conversation** (OP-3, decided): `finish_turn` wrote `handed_off` gives `with_person`; `open` with no stop gives `replied`; `open` with a stop gives `paused`; nothing written gives `with_person`, with the reason on the run record (`interrupted` when the tick or a fence had moved the run). So when E4 committed and the tick moved the run before E6, the result still follows the conversation, and `interrupted` stays on the run record only. Each result carries `reason`, `run_id`, `turn_no=n` and `delivered=d.ok`, and no text.
7.  **E7. Money card** (only for stop `estimate_exceeded` or `limits_unavailable`; DES-ADV-5, replaces revision 1's E2b). After E6, so the card hook is outside the window in which a crash or a hang turns a passing fault into a hand-off, and the run record already holds the money code. `hooks.post_card` with P4c-2's fixed card text (ids and the code, no turn text), wrapped like `_deliver`, without `_abstain`. A failure writes one ERROR log line (ids and class name) and does not change the result. At most one card per exchange, because E7 runs once. Said plainly: (1) a process that dies between E6 and E7 posts no card; the run record (`NEEDS_PERSON estimate_exceeded` or `limits_unavailable`) and P4c-2's own meter records still show it; (2) the bound on cards is one per message the person sends, until the daily limit stops the run before the model call, and that stop (`limits.daily_budget`) posts no card (BN-2).

### The crash rule (BN-2; replaces the ticket's "Store failures, one rule")

1.  Before the claim commits (F2 to F7), a store exception gives `retry`: nothing was accepted. Any other `Exception` in those steps also gives `retry`, after one ERROR log line with the ids and the class name only (DES-COR-3, DES-ADV-9). The exceptions with their own row stay as written: `AuditUnavailable` at a refusal (F2), the uncertain claim commit (F6), a raise from `open_handoff` in F7.
2.  After the claim commits and before E6, any other `Exception` (not `LeaseLost`, which has its own path at E4) is a crash: one ERROR log line (ids and the class name only), one wrapped `_to(run, NEEDS_PERSON, reason)` with reason `store_unavailable` for a store error class and `internal_error` for anything else, result `with_person`, no delivery, and no store call other than that one transition (DES-ADV-10).
3.  A `BaseException` that is not an `Exception` (for example `KeyboardInterrupt`) is not caught. The lease dies (quiet limit) and the sweep recovers the slot.
4.  After a crash the run is final, so the lease is dead. The next claim or the sweep fences (the run is already final, so only `version` moves), opens the `interrupted` item and takes over (`handed_off`). PL14's owner-visible sentence: "after a crash, a store fault or a queue outage during an answer, that chat continues with a person, not with the agent".
5.  **Reach of one fault, said plainly** (DES-ADV-10): a short outage of the database or of the audit store hands off EVERY chat whose answer was in progress at that moment, not only one. They all go to the "needs a person" queue once the store is back.

### Store transaction rules

All methods take `tenant` and filter by it in every statement on the two tables (Postgres: `WHERE tenant = %s AND ...`). Every read also takes `reader` and returns nothing when the reader is not allowed, exactly as for a missing row. Busy, stale, duplicate, reused and lost are results, not errors, so a fence or a takeover and its result commit in one transaction. Errors (`ConversationConflict`, `ConversationNotOpen`, `LeaseLost`) derive from `ConversationError(RuntimeError)`; their text gives the class name and ids only. **A missing conversation row** (deleted by `forget_user` or the purge between a read and a write; DES-ADV-13): `claim_turn` and `record_user_turn` raise `ConversationNotOpen`, and `finish_turn` and the takeover raise `LeaseLost`.

**The lease rule** (one rule, the tick's): the lease of a conversation is live when `busy_run_id` is set, that run is not final, and its `runs.updated_at >= now - quiet_s`; it is dead when `updated_at < now - quiet_s`, which is the same strict comparison as the tick's `stuck` step (`tick.py:130`; DES-COR-11). `quiet_s = quiet_limit_s(agent.max_steps, llm settings)`, the formula of `tick.py:100-109` moved into `runtime/runs.py` (960 s for `max_steps` 5 with the real backend defaults; 360 s with the fake model kind). That one function is the only place the number is computed: the tick calls it on every tick, and `Runtime` calls it once at start into `self._quiet` from the same `app.config` (DES-ADV-12). The store reads the busy run's row in the same transaction. `busy_since` is kept for the record only. **Clocks:** `touch` writes the clock of the app machine that runs the exchange, and `now` comes from the machine that claims or sweeps. All machines of one deployment must agree within 60 s, which is the fixed margin inside the formula. Larger clock drift can make a healthy lease look dead.

**The lease token** (order 38 item 85): the token is `conversations.version`. `version` only ever goes up, and every write to the conversation row adds 1. The version a claim writes is that exchange's token. While a lease is held, only three writers can change `version`: the fence, the takeover, and the exchange's own `finish_turn` (every other writer gets `busy` or `ConversationNotOpen`). So "the stored version equals my token" means "nobody has fenced or taken over my exchange". This needs no new column and no new right: `version` is in PL16's column list.

**`claim_turn`** (one transaction; Postgres locks the conversation row first, then reads the busy run's row):

1.  If the row is missing, or `state != "open"`: raise `ConversationNotOpen`.
2.  If `message_id` is already stored: if its `text_digest` differs, return `reused` and write nothing (BN-9). If the answer slot of that message holds a turn, return `duplicate` with `first_run_id`. If the slot is empty and the lease is live, return `duplicate` (the caller returns `retry`). If the slot is empty and the lease is dead: without `take_over`, run the fence and return `lost`. With `take_over` naming the busy run and `expect_version` equal to the stored version, take over (helper below) and return per OP-2.
3.  With `take_over` naming the busy run and `expect_version` equal to the stored version: go to step 5 whatever the heartbeat says (the fence already made the run final; this is a second safety net, not a liveness skip). Otherwise, if the lease is live: return `busy`, write nothing.
4.  If `version != expect_version`: return `stale`, write nothing.
5.  If the lease is dead: without a matching `take_over`, run the fence and return `lost` with `LostExchange(tenant, conversation_id, run_id, turn_no, version=<the new version>, fenced=<true when this call moved the run>)`. With a matching `take_over`: run the takeover helper, then append this message's masked user turn (with `text_digest`, no answer slot, no lease, no run row, `run_id` empty because no run exists), `next_turn += 1`, set `mapping`, `version += 1`, and return `recorded` (BN-6).
6.  Otherwise (no lease): append the user turn at `next_turn` (with `text_digest` and `run_id = run.run_id`, DES-ADV-3), `next_turn += 2` (the answer slot is reserved), `busy_run_id = run.run_id`, `busy_since = now`, `mapping = <given>`, `version += 1`, `updated_at = now`, AND insert the run row (`RECEIVED`, as `create_run` writes it). Return `claimed` with the new `version` (the lease token).

**The fence** (private; called by `claim_turn` and `lost_exchanges`, inside their transaction, under the conversation row lock, only after the same transaction has seen that `busy_run_id` names the run and the lease is dead):

1.  `version += 1`, `updated_at = now`. Nothing else on the conversation row; no turn is written.
2.  On the busy run's row: one compare-and-set from `RECEIVED` or `WORKING` to `NEEDS_PERSON` with reason `interrupted` and `updated_at = now` (allowed by `runtime/runs.py:11-12`; the same reason the tick writes, `tick.py:111-113`). If the run is already final, nothing changes on it. A chat run is never in any other state.
3.  Return the new `version` and whether step 2 moved the run (`fenced`). The caller writes the `run/state` audit event when `fenced` is true (F7, the sweep), because the store writes no audit.

Why the fence and `finish_turn` cannot both win: both lock the conversation row first. If the fence commits first, `finish_turn` sees another `version` and a final run and raises `LeaseLost`. If `finish_turn` commits first, `busy_run_id` is cleared, so the fence never runs and no item is opened. The tick's `stuck` step moves runs without the conversation lock; that is safe: if it moves the run before `finish_turn`, `finish_turn` raises `LeaseLost` (the BN-17 T37 variant), and if after, the conversation is already `open` with no lease and no item (OP-3).

**The takeover helper** (private; called by `claim_turn` and `lost_exchanges`, inside their transaction):

0.  Precondition: `busy_run_id` names the given run and the stored `version` equals the given token (the value the fence returned). Otherwise write nothing: `claim_turn` returns per steps 3 to 5, and `lost_exchanges` skips that conversation.
1.  Write the lost exchange's answer slot as the filler: text `defaults.CONVERSATION_LOST_REPLY_TEXT` (`[no answer was given]`), `fixed=True`, `delivered=False`, `run_id` of the lost run. Turns keep alternating.
2.  Clear `busy_run_id` and `busy_since`.
3.  Set `state = "handed_off"` (BN-6).
4.  `version += 1`, `updated_at = now`.
5.  Do not touch `mapping`. Do not touch the lost run's row: the fence before the item already made it final.

**`finish_turn(tenant, conversation_id, run_id, *, lease_token, turn_no, text, fixed, delivered, state, mapping, now)`** (one transaction; Postgres locks the conversation row first, then reads the run's row):

1.  If the row is missing, `busy_run_id != run_id`, `version != lease_token`, or the run is final: raise `LeaseLost`, write nothing.
2.  Append the answer turn at `turn_no` (`fixed`, `delivered`, `run_id`).
3.  Clear `busy_run_id` and `busy_since`; set `state`, `mapping` (the `kept` map) and `updated_at`; `version += 1`.

**`record_user_turn`** (one transaction; for a `handed_off` conversation only, else `ConversationNotOpen`; a missing row is `ConversationNotOpen` too):

1.  A stored `message_id`: `reused` if the digest differs, else `duplicate`. Nothing written.
2.  `version != expect_version`: `stale`. Nothing written.
3.  Append the masked user turn (with `text_digest`, no `run_id`), `next_turn += 1`, set `mapping` (F5 applies the map limit before the call, NEEDS LEAD 1), `version += 1`, return `recorded`. No lease.

**`lost_exchanges(now, quiet_s, *, take_over: Mapping[str, int] = {}, limit: int = 100)`** (runtime identity):

1.  Read the conversations, in every tenant, whose `busy_run_id` is set and whose lease is dead, oldest `busy_since` first, at most `limit`, looking up `quiet_s` by the conversation's `agent_id`; skip a conversation whose agent is not in `quiet_s`. This SELECT is one of the two statements not filtered by tenant (the other is in `purge_conversations`); each write is filtered.
2.  With an empty `take_over`: for each listed conversation, one transaction: lock the row, check again that `busy_run_id` is the same and the lease is still dead, run the fence, and return it with its new `version` and `fenced`. A conversation that changed since the read is left out.
3.  For each listed conversation whose busy run id is a key of `take_over`: one transaction per conversation, the takeover helper with that token. Those are not returned.
4.  It uses the partial index on `conversations (busy_run_id) WHERE busy_run_id IS NOT NULL` (BN-15).

Note: after the fence the run is final, so its lease stays dead. If the item fails to open, the next tick's `lost_exchanges` finds the same conversation again (the fence then moves only `version`).

**The sweep** (`Runtime.sweep_conversations(now) -> int`, called by the tick step `sweep_conversations`, appended last to `STEPS`; the name `sweep` is taken):

1.  Build `quiet = {agent_id: quiet_s}` for the conversational agents; with none, do nothing.
2.  `found = store.lost_exchanges(now, quiet, limit=defaults.CONVERSATION_SWEEP_MAX)` (100; DES-ADV-7: a cap per tick, so one tick cannot take unbounded time).
3.  For each: when `fenced`, the `run/state` audit event (as in F7); then the wrapped `open_handoff(HandoffRequest(..., run_id=lost.run_id, reason="interrupted", idempotency_key=lost.run_id))`. A raise leaves that conversation for the next tick, with one ERROR log line (ids, class name).
4.  One call `store.lost_exchanges(now, quiet, take_over={run_id: version for each item that opened})`.
5.  Return the number of items opened. If any `open_handoff` raised, the step then raises after step 4, so the tick marks it FAILED and `tick_state.last_error` shows it, the same pattern `purge_evidence` uses for its hook (`tick.py:204-211`). This is the loud signal for a queue outage (DES-ADV-7). Revision 1's sentence "`stuck` runs first, so quiet runs are already final" is deleted: `list_runs` takes at most 100 runs per state (`store/memory.py:92`), and a failed step does not stop later steps (DES-COR-11). The fence does not depend on it.

**`forget_user(tenant, user_id, *, now, quiet_s: float) -> ForgetReport`** (purge identity, through `app.purge_store`; in pilot/prod `ConfigError` when `app.purge_store is app.store`):

1.  `quiet_s` is one number: the largest quiet limit over the conversational agents, filled by the entry point `runtime/conversation.forget_user(app, ...)` from `quiet_limit_s` (DES-COR-1). One number is needed because the purge role cannot read `conversations.agent_id` (Interface 3's purge columns), and the largest is the safe side: it never deletes during a live lease, and at worst it waits a little longer.
2.  One transaction. First ONE conditional DELETE on `conversations` for that tenant and user, keeping only the rows whose lease is provably dead: `busy_run_id` is empty, OR its run row exists and is final or has `updated_at < now - quiet_s`. Then count that person's conversations that remain. If any remain, roll back and return `kind="busy"`: nothing is deleted, and the caller tries again.
    - Why this form (DES-COR-12; checked on a throwaway PostgreSQL 16 server, 2026-11-06): (a) a role with only `SELECT` and `DELETE` gets "permission denied" for `SELECT ... FOR UPDATE` and for `FOR SHARE`, while the conditional DELETE runs; (b) the condition must be written as "the busy run is provably dead". Written as "no live run exists", the DELETE removed a conversation whose claim committed while the DELETE waited on its row lock, because the new run row was not visible to the waiting statement. Written as "provably dead", that row was kept. PostgreSQL 17 is not checked; the contract rows on 16 and 17 settle it (BN-14).
3.  Otherwise, in the same transaction: delete those conversations' turns and, by the run ids named in those turns (user turns and answer turns, DES-ADV-3), the `redaction_maps` rows and the `tool_calls`, whatever `hooks.hold_run_ids` says (BN-11, PL15). `runs` rows and the audit chain stay (no text, no user id). Return `kind="done"` with counts per table.

**`purge_conversations(before) -> int`** (purge identity):

1.  In one transaction: delete conversations with `updated_at < before`, their turns, and the `redaction_maps` rows of the run ids named in those turns, through the same private helper as `forget_user`, whatever the hold says. It does not delete `tool_calls`; they keep their own `tool_calls_days` (BN-11, D5). Whether PL15 means that it should is NEEDS LEAD 3. A conversation with a lease held is not special here: after 30 days the sweep has long since taken it over.
2.  `tick.purge_evidence` calls it right after the two 400-day ceilings and BEFORE the hold hook, so a raising hook cannot block conversation retention (BN-11). The step still fails when the hook raises.

**Rights** (BN-15, PL16): `conversations` gets `SELECT, INSERT` plus `UPDATE` on the columns `state, next_turn, version, mapping, busy_run_id, busy_since, updated_at` only, through the new `Grant.runtime_update_cols`; the purge role gets `DELETE` and may read `conversation_id, tenant, user_id, busy_run_id, updated_at`. `conversation_turns` gets `SELECT, INSERT` (append only); the purge role gets `DELETE` and may read `tenant, conversation_id, run_id`. The runtime role can never change `tenant`, `user_id`, `readers` or `agent_id` (negative test A10). The lease token and the fence add no column and no right: the token is `version`, and the fence's run write uses the runtime role's existing `UPDATE` on `runs` (`store/migrate.py:47`). The purge role takes no row lock; its DELETE locks the rows it deletes itself. Whether the runtime role's `SELECT ... FOR UPDATE` in `claim_turn` and `finish_turn` works with column-level UPDATE only is UNVERIFIED (the throwaway server gave the role table-level UPDATE); the Postgres contract rows on 16 and 17 settle it.

### State diagram (text)

Conversation, as stored:

```text
                 start_conversation
                        |
                        v
  +------------------ OPEN, no lease <------------------------------+
  |                     |                                           |
  |        claim_turn   |  (claimed: user turn + run row + lease;   |
  |                     |   version = the lease token)              |
  |                     v                                           |
  |               OPEN, lease held by run R                         |
  |      +--------------+-----------------------+                   |
  |      | finish_turn  | finish_turn           | R final, or quiet |
  |      | state=open   | state=handed_off      | past quiet_s      |
  |      | (reply or    | (hand-off stop or     |  => lease DEAD    |
  |      |  paused)     |  reply not delivered) |        |          |
  |      |              |                       |  FENCE (version+1,|
  |      |              |                       |  R -> final)      |
  |      |              |                       |        |          |
  |      |              |                       |  item for R opened|
  |      v              v                       v  (F7 or sweep)    |
  +-- (back to OPEN,   HANDED_OFF <------- takeover (filler turn,   |
       no lease)        ^   |               lease cleared)          |
                        |   |                                       |
     record_user_turn   +---+                                       |
     (stored, no model, no reply)                                   |
```

`finish_turn` after the fence raises `LeaseLost` (token and run state both differ). There is no way back from `HANDED_OFF` in v1 (V2), and no `closed` state (V13).

Run of one exchange (existing states; no new state):

```text
  (claim_turn) -> RECEIVED -> WORKING --E6--> NO_ACTION replied
                     |           |----E6--> NEEDS_PERSON <stop | lease_lost | handoff_unavailable | reply_not_delivered>
                     |           |----E6--> STOPPED kill_switch
                     |--crash----+--crash-> NEEDS_PERSON store_unavailable | internal_error
                     |           |
                     +-----------+--tick stuck, or fence--> NEEDS_PERSON interrupted
                                                            (then the run check, F8's _to or E4 gives the
                                                             lease-lost path, and E6 makes no second move)
```

A crash can also happen in `RECEIVED` (for example the `run/received` audit write at F8 raises before `_to(run, WORKING)`); `RECEIVED -> NEEDS_PERSON` is allowed (`runtime/runs.py:11`).

### Non-functional requirements

- **Security and privacy.** The model sees masked text only. Stored turns are masked, with unsaved placeholders labelled. Logs and audit hold ids, counts, keyed digests and closed codes only (without `restored_key` in dev, a plain hash of masked text). The hand-off item holds ids and a closed reason, no text, no user id. Tenant filter in every statement except the two named full scans. Column-limited runtime UPDATE; the lease token and the fence add no column and no right. The run's principal is `chat:<agent_id>`, and a registered principal starting with `chat:` is a load problem, so no staff right attaches to a chat. Every outbound path is listed in the ticket ("Every outbound text path"); until AK-G22 merges, replies go through neither gate, which is why pilot and prod refuse a conversational agent.
- **Money.** Every model call, the screen's included, runs inside the meter scope and is booked exactly once (F9). Meter faults pause the chat; `estimate_exceeded` and `limits_unavailable` also post the fixed money card, after the run's final state is written (E7).
- **Timing.** The lease margin depends on `call_timeout_s` being a per-socket-operation timeout, not a wall clock (`backends/table.py:37-39`, ticket cite), so it is a large margin, not a hard guarantee. A run that overruns it is fenced: it commits nothing, and its run checks stop further model calls and deliveries (CUJ 5). Machine clocks must agree within 60 s (lease rule).
- **Message ids and digests** (DES-ADV-14, DES-COR-10). `text_digest` is the keyed digest of the STORED (masked and labelled) text. A genuine resend of an old message can be refused `message_id_reused` after a change to `stored_kinds` in the client config, or after `restored_key` is replaced, because the same words then give another digest. This is intended: a false refusal is the safe side (the host sends it again under a new message id), and digesting the unmasked text would keep a digest of personal data. Test T14 gains the case "same text, `stored_kinds` narrowed between the two calls: `refused message_id_reused`".
- **Rollout and rollback** (BN-13). Revert in the order c, b, a. Reverting AK-G1-a restores the old `Store` protocol. Dropping the two tables cannot be undone; the lead decides, after saving both row counts to `handover/evidence/AK-G1/pre-drop-<sha>.txt`.
- **Owner-visible limits** (the lead edits `owner-visible-limits.md`; the exact proposed sentences are in `reviews/AK-G1-design-resolve.md`): BN-1's cost (an earlier message that was not processed must be repeated); PL14's sentence; PL15's sentence ("erasure takes priority over the evidence hold for chat content; this has not been reviewed by counsel"); a crash after delivery and before `finish_turn` leaves history saying "[no answer was given]" for an answer the person saw (PENDING LEAD 2(iv)); one false positive of the injection screen hands a chat off for good. New in revision 2: an answer slower than the quiet limit is treated as lost, and the person may still see it (CUJ 5); one database or audit outage hands off every chat that was being answered at that moment (crash rule 5); a money card can be missing if the process dies right after the run ends (E7); and, if the lead keeps NEEDS LEAD 2 (a), a chat that waits longer than the retention period for a person is deleted.

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

### Alternative N: a separate `lease_token` column for the lease token

*   **Pros**: the token's meaning is not shared with the compare-and-set counter.
*   **Cons**: a new column the runtime role must UPDATE, which widens PL16's fixed column list (a least-privilege change for the lead); and `version` already has exactly the needed property (it only goes up, and every write to the row adds 1).
*   **Reason for Rejection**: Rejected in the resolve (order 38 item 85 asks for a token, not for a column). If the lead wants a separate column anyway, that is a NEEDS LEAD item because it widens a grant.

### Alternative O: fence by the run's final state only (no token)

*   **Pros**: no change to `finish_turn`'s arguments.
*   **Cons**: `finish_turn` would rely on a read of another table for its only guard, and a write to the conversation would not carry proof that nobody fenced it. The lead asked for a token checked on every write (order 38 item 85).
*   **Reason for Rejection**: Rejected in the resolve. The final-state move stays as the run-side half of the fence (OP-1), because the token alone does not keep the lease dead.

### Alternative P: the money card before E4 (revision 1's OP-4)

*   **Pros**: the card goes out before the commit, so a process death after the commit cannot lose it.
*   **Cons**: the card hook then runs while the lease is held; a crash or a hang there turns a passing fault into a permanent hand-off (DES-ADV-5).
*   **Reason for Rejection**: Rejected in the resolve: E7, after E6.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

No code here. Paths are relative to `<repo>` (`src/hadavin_sdk/...` unless a path starts with `tests/` or `handover/`). "Hot file" means other packages edit it too; merge slots follow order 20 item 5.

### Target Files to Create/Modify

#### AK-G1-a (the store)

1.  **`src/hadavin_sdk/store/migrations/<next>_conversations.sql`** (Create; today the next free number would be `0006`, fixed at merge, A3). The two tables of Interface 3, plus `schema_version INTEGER NOT NULL DEFAULT 1` on both (BN-21), `text_digest TEXT` on `conversation_turns` (BN-9), indexes `(tenant, user_id)` and `(updated_at)`, and the partial index on `busy_run_id` (BN-15). No foreign-key cascade. Why: the store needs the rows; the columns serve the transaction rules above.
2.  **`src/hadavin_sdk/models.py`** (Modify, hot). `Conversation`, `Turn` (with `text_digest`), `USER_ID_PATTERN`; `__repr__` without text, map or reader names. Why: typed records for both stores.
3.  **`src/hadavin_sdk/store/protocol.py`** (Modify, hot). The 9 methods; `ClaimResult` with kinds `claimed`, `recorded`, `busy`, `stale`, `duplicate`, `lost`, `reused`; `LostExchange` (with `version` and `fenced`, revision 2); `ConversationError` and its three subclasses; `text_digest` on `claim_turn` and `record_user_turn`; `lease_token` on `finish_turn`; `take_over` as a map and `limit` on `lost_exchanges`; `now` and `quiet_s` on `forget_user` (see "Ticket text changed by the design review"). Still 9 methods. Why: one contract for memory and Postgres; `missing_methods` then refuses an incomplete custom store at start.
4.  **`src/hadavin_sdk/store/memory.py`** (Modify, hot). All 9 methods under the existing lock, the fence and the takeover helper, the lease rule reading the run in the same lock. Why: the built alternative and the test store.
5.  **`src/hadavin_sdk/store/postgres.py`** (Modify, hot). The same, with the row lock order (conversation, then run) in `claim_turn`, `finish_turn`, the fence and the takeover, tenant filters, the shared delete helper for `forget_user` and `purge_conversations`, and `forget_user`'s single conditional DELETE in the "provably dead" form. Why: the neutral default.
6.  **`src/hadavin_sdk/store/migrate.py`** (Modify, hot, P2a). `Grant.runtime_update_cols` (when set, `UPDATE (cols)` instead of table UPDATE; `effective_problems` checks it) and the two `GRANTS` rows. Why: PL16.
7.  **`src/hadavin_sdk/config.py`** (Modify, hot). `Retention.conversations_days` (default 30, ceiling 400). Why: R98 retention.
8.  **`src/hadavin_sdk/runtime/tick.py`** (Modify, hot). In `purge_evidence`, call `purge_conversations(now - conversations_days)` on the purge store right after the two ceilings and before the hold hook; count it in the log line. Why: BN-11, PL15.
9.  **`src/hadavin_sdk/runtime/conversation.py`** (Create). `start_conversation`, the `forget_user` entry point (picks the purge store; `ConfigError` in pilot/prod when it is the runtime store; passes `now` and the largest quiet limit), `ForgetReport`, `TurnResult`, `ReplyEnvelope`, `HandoffRequest`. Why: records shared by -a and -b; the entry point picks the deleting identity.
10. **`src/hadavin_sdk/defaults.py`** (Modify, hot; own block `# --- conversations (AK-G1-a) ---`). `CONVERSATIONS_DAYS`, `CONVERSATION_LOST_REPLY_TEXT`. Why: no hardcoding.
11. **`tests/test_conversation_store.py`** (Create). Rows A1-A10, A12-A22 including A22 (BN-11), the extended A3 (BN-10), A4, A5 (digest, BN-9), A10 (column refusal, BN-15), A18. Revision 2 adds cases to existing rows, with no new row id: A3 (`finish_turn` with an old token, and with a final run, raises `LeaseLost` and writes nothing; a missing row raises `LeaseLost`); A4 and A18 (a `lost` result fences: `version` + 1, run `NEEDS_PERSON interrupted`, `fenced` true, and false for a run that was already final; a `touch` after the fence leaves the lease dead; `finish_turn` between the fence and the takeover raises `LeaseLost`; a takeover with an old token writes nothing); A5 (OP-2); A20 (`forget_user` against a claim that commits while the DELETE waits gives `busy`; on Postgres with two connections); A22 (crash after the claim, then `forget_user`, removes the run map found through the user turn's run id). Why: the transaction rules above, as tests.
12. **`tests/contracts/test_store.py`** and **`tests/contracts/kinds/store_postgres.py`** (Modify). Contract rows; `_SplitStore` sends `purge_conversations` and `forget_user` to the purge store (BN-20). Why: Postgres rows run with the purge role's rights only.
13. **`CHANGELOG.md`** (Modify, append only). "The `Store` protocol gains 9 methods; `missing_methods` refuses a custom store without them at start."
14. **Evidence** (`handover/evidence/AK-G1/`): `AK-G1-a-postgres.txt` on PostgreSQL 16 and 17 with `HADAVIN_TEST_PG_DSN` set and 0 skipped conversation rows (BN-14); `AK-G1-a-mutants.txt` with the variable set. Why: Done for -a.

#### AK-G1-b (the turn loop; the (b) shape, no read tools)

15. **`src/hadavin_sdk/runtime/agent_loop.py`** (Modify, hot: P4c, P5c). `handle_turn` (F1-F13, with `redact_untrusted` and `redact_text` called directly in its body); `_end_exchange` (E1-E7; the money card is E7); `sweep_conversations`; `HANDOFF_STOPS`; `_CHAT_RULE`; `_limit_reason`; `_tool_step` (the moved block, for `handle`; no `subject` parameter yet); `_keyed_digest(text: str) -> str`: HMAC-SHA256 under `hooks.restored_key` over the UTF-8 bytes of the text, or plain SHA-256 without a key (dev). Today's `_restored_digest(view)` (`agent_loop.py:256-267`) takes a dict; it becomes `_keyed_digest` of the same canonical JSON text, so its existing callers get the same bytes and their tests stay unchanged (DES-COR-10); `_keep`; the label and render helpers; two `Hooks` fields; `__init__` checks (both hooks set for a conversational agent; `self._quiet`; P5c-3's wrapper check); the run check and the lease-lost path; the screen booked once (F9). `handle` maps reason strings back to its old transitions (BN-26). Why: the flow lives here; one loop.
16. **`src/hadavin_sdk/runtime/runs.py`** (Modify, hot). `quiet_limit_s(max_steps, llm)`. Why: one formula for the tick and the lease.
17. **`src/hadavin_sdk/runtime/tick.py`** (Modify, hot). `stuck_after_s` calls `quiet_limit_s`; append the step `sweep_conversations` last. Why: one formula; the sweep.
18. **`tests/test_p7_tick.py`** (Modify, on purpose). The step-list assertion at `:80-89` gains `"sweep_conversations"` as the last element (BN-19). Why: pins the appended step.
19. **`src/hadavin_sdk/registry.py`** (Modify, hot). `ConversationSettings` (even `history_turns`; `max_message_bytes` may only be lowered), `FixedReplies` (defaults from `defaults.py`), `AgentRecord.conversation`, and one new function `_conversation_problems(agents, principals)` called where both are known (BN-23): `scope_allowed` empty, `tools_allowed` empty, `ask_for_person` reserved, no principal id starting `chat:`. Why: load-time refusals.
20. **`src/hadavin_sdk/deferred.py`** (Modify, hot). Pilot/prod refusal of any conversational agent (T19 b). Why: no person-facing path before the wiring ticket.
21. **`src/hadavin_sdk/llm/fake.py`** (Modify, hot). `ScriptedLLM` (dev-only fake kind; records messages, system and tools; `ScriptExhausted`). Why: multi-turn tests with no live model.
22. **`src/hadavin_sdk/guard/producers.py`** (Modify, hot, after P5c-3). One row: "conversation message and reply", `runtime/agent_loop.py`, `handle_turn`, `{redact_untrusted, redact_text}`. Why: the producer check sees both masks.
23. **`src/hadavin_sdk/defaults.py`** (Modify; own block `# --- conversations (AK-G1-b) ---`). `CONVERSATION_HISTORY_TURNS`, `_MAX_MESSAGE_BYTES`, `_MAX_REPLY_CHARS`, `_RETRY_AFTER_S`, `_HIDDEN_TEXT`, `_HOOK_TIMEOUT_S`, `_UNPROCESSED_TEXT`, `_HANDOFF_TEXT`, `_PAUSED_TEXT`, `_SWEEP_MAX` (100, revision 2).
24. **`tests/conversation_support.py`** (Create). `RecordingRecipient`, `RecordingHandoff` (dedupes on the key), the one-agent qualified fixture (BN-27), crash-injection points (between E2 and E5, between E5 and E4, after E4, before E6, between E6 and E7), a point that blocks a model call or a hook until the test has run the sweep (CUJ 5), a store wrapper that commits and then raises (DES-ADV-2), a raising store wrapper, the wrapper-stack helper `MaskedLLM.of(MeteredLLM(ScriptedLLM(...)))` keeping its own reference to the `ScriptedLLM` (BN-4), `run_script`. Why: one harness.
25. **`tests/test_conversation_turns.py`** (Create). F0, T1-T25, T28-T40 with the extended rows of BN-28 (T9 label cases, T15 surrogate, T36 crash rule, T37 hanging hook, T40 money in a chat). Revision 2 adds cases to existing rows, with no new row id: T34 and T37 (CUJ 5: the slow run is fenced, makes no further model call or delivery after its run check, gets `with_person lease_lost`, one item); T36 (an `Exception` before the claim gives `retry`; `finish_turn` commits and then raises: the answer-slot read finds the turn and the result follows the conversation; a claim that commits and then raises continues as `claimed`); T40 (the card comes after the run's final transition, at most one per exchange); T21 (the screen's cost booked once); T14 (a `stored_kinds` change makes a resend `message_id_reused`); T18 (`with_person`, `delivered=False`, `run_id=None` for F5 and F7). Whether the new behaviour also gets new mutant ids is for the build-start review: new ids would change BN-28's counts, which this design does not change. Why: the step list above, as tests.
26. **`CHANGELOG.md`** (Modify, append only).
27. **Evidence**: `AK-G1-b-*.txt`, 107 mutants in the (b) stage (BN-28). `AK-G1-b-notes.txt` records any P4c-2 or P4b1 name that differs on the build base (BN-2).

#### AK-G1-c (only after AK-G1-b merges and the owner picks PENDING LEAD 5 (a))

28. **`src/hadavin_sdk/tools.py`** (Modify, hot, K5 owner). `Subject`, `ToolContext.subject`, `ToolBox.invoke(..., subject=...)`, `ToolSpec.subject_scoped`. Why: read tools bound to the chatting person.
29. **`src/hadavin_sdk/runtime/agent_loop.py`** and **`src/hadavin_sdk/registry.py`** (Modify). `_tool_step`'s `subject` parameter and its plain-callable refusal; F12; the `subject_scoped` load rules replacing "`tools_allowed` empty". Tests T26, T27, the `max_steps` case and mutants M-B12, M-B27, M-B28, M-B53; M-B70 retired. Evidence `AK-G1-c-*.txt`.

#### Not touched by the builder

- `handover/owner-visible-limits.md`, `handover/questions-for-lead.md`, `tickets/AK-G1.md`: the lead edits them.

### Dependencies and build order (DES-COR-8; from the ticket's sub-PR table)

| Sub-PR | Needs merged first | Names this design uses from it (not in this checkout) |
|---|---|---|
| AK-G1-a | P4d-a1 (contract harness and store fixes); AK1-a | `TENANT_PATTERN`, `READER_PATTERN`, `tenant_key` (AK1); `store_pair` (P4d-a1, UNVERIFIED name) |
| AK-G1-b | AK-G1-a; P4c-2; P4b1-b; P5c-2; P5c-3; AK1 | `MeterError`, the per-run money signal, `scope.refusal`, the money card text (P4c-2); `MeteredLLM` (P4b1-b); `MaskedLLM.of`, `llm.run`, `SessionClosed` (P5c-2); `guard/producers.py` (P5c-3) |
| AK-G1-c | AK-G1-b; the owner's PENDING LEAD 5 (a) | `tools.py` changes (K5 owner) |

Merge order: AK-G1-a, then AK-G1-b, then AK-G1-c. If a name differs on the build base, the builder follows the built name and records it in the notes file (BN-2).

### Verification Plan

*   **Unit and contract tests**: `uv run --all-extras --group test pytest` on the final head; the 19 existing `.handle(` test files pass unchanged (T20), except the one assertion BN-19 changes on purpose in `tests/test_p7_tick.py` (one of the 19).
*   **Postgres**: contract rows on PostgreSQL 16 and 17, 0 skipped (BN-14).
*   **Static checks**: `ruff check`, `ruff format --check`, `bandit -ll`, the repo guard tests.
*   **Mutation**: 38 A-mutants; 107 B-mutants in the (b) stage, 110 after AK-G1-c (command from P1m's merged docs, UNVERIFIED here).
*   **Design-level checks** (for the reviewers): each invariant I-1 to I-8 has at least one test row; each open point the lead accepts has a test.

--------------------------------------------------------------------------------

### Reconciliation with the concepts brief (draft skill step 6.1)

- **Contradictions:** none. The brief fixed no question differently from this draft.
- **Additions that change behaviour:** revision 1 carried OP-1 to OP-6 as recommendations; the resolve decided all six (revision 2). The brief's weak point 1 (a lease that comes back to life) is now closed by the two-part fence of order 38 item 85, which is new against the brief. None changes a dependency.

### Additional Resources

*   `tickets/AK-G1.md` (revision 3 FROZEN, build notes, lead answers)
*   `reviews/AK-G1-round3-resolve.md`
*   `LEAD-ORDERS.md` orders 20-38 (orders 20, 36, 37 and 38 read in full; the others only by their headings)
*   `reviews/AK-G1-design-review.md` and `reviews/AK-G1-design-resolve.md`
*   `designs/ak-g1/concepts_brief.md`

*Drafted with EGM*
