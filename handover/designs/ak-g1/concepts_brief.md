# AK-G1: chat turn flow and conversation store transaction rules

* **Author:** Claude (git `user.name`), for the lead, order 36 item 82 (PENDING LEAD 11 option (b))
* **Date:** 2026-11-06, written about 06:00 UTC (11:30 IST)

## Read this first: what this brief is not

- The EGM brainstorm skill has two parts: questions to the user, then a "Goldfish" review (fresh reviewer agents with no memory of this work). **Neither part ran.** The brief asked for AUTO mode (no questions), and this session has no tool that starts a subagent, so no fresh reviewer read this brief. The "Analysis" section below is a stress test I wrote myself, in the same context. It is not a Goldfish review. The Goldfish review is the next EGM step (`egm:egm-review`) on the design document.
- Nothing new is decided here. Every decision comes from the frozen ticket `tickets/AK-G1.md` revision 3, its build notes BN-1 to BN-28, and the lead's answers to PENDING LEAD 11-16 (all six take the recommended option). Where they disagree, the lead's answers win, then the build notes, then the ticket body.
- I read the ticket's flow table, interfaces, build notes and lead answers in full, the round 3 resolve (honest note, facts, positions, couplings), order 36, and these code files: `runtime/runs.py:8-42`, `runtime/tick.py:98-135`, `:184-218`, `:245-268`, `store/memory.py:83-90`, `store/postgres.py:279-280`, `runtime/agent_loop.py:560-567`, `store/migrate.py:24-40`. I did not read P4c, P5c or AK1 ticket text, and I ran nothing.

## Overview

AK-G1 lets a person (for example a shop's customer) chat with an agent. Each message the person sends becomes one **exchange**: the message is masked (personal values such as e-mail addresses are replaced by placeholders like `<EMAIL_1>`), stored, answered by the model, the answer is masked again and shown with labels such as `[hidden email]`, delivered through a hook, and stored. When the agent cannot help, the chat is **handed off**: one item goes into the "needs a person" queue and the agent never answers that chat again.

The hard part, and the reason for this EGM step, is the **order of steps and the store transactions**. Review rounds 2 and 3 found their Blockers and Majors in exactly that ordering (map writes, the order of delivery, hand-off and the final write, and what happens after a crash). The design document must write that ordering out step by step, with every build note folded in, so the builder has one consistent text.

## Analysis (my own stress test; not a Goldfish review)

- **One commit point is the core idea.** The claim (`claim_turn`) takes a short claim on the chat (the **lease**) and creates the run row in one transaction. The answer is delivered while the lease is held. For a hand-off, the queue item is opened next. Then one `finish_turn` writes the answer, the state and the map. A crash anywhere before `finish_turn` leaves the lease in place. Once the lease is dead, the next message or the tick's sweep opens an `interrupted` item and hands the chat to a person (BN-6, lead answer PL14). This is simple to state. Its weak points are at the edges, listed next.
- **Weak point 1: a lease can come back to life.** A lease is dead when its run is final OR the run has been quiet longer than the stuck-run time. `touch` (the heartbeat) moves `updated_at` without checking the run's state (`store/memory.py:83-90`). So a slow process that was judged quiet, but that the tick has not yet moved to a final state, can touch again and make its lease live. If the item for it was already opened, the ticket's check order (live lease before dead lease) returns `busy` for the takeover. Then an item exists while the chat stays `open`, which breaks the invariant of BN-6. The design carries this as an open point with a recommendation.
- **Weak point 2: the resend of a lost message.** BN-6 says the takeover in `claim_turn` also appends "this message's" user turn. When the message is a resend of the lost one (same message id), a second append would break the unique message-id rule. BN-6 does not cover that case. Open point.
- **Weak point 3: the outcome after a late tick.** When the tick has already moved the run, row E6 returns `with_person interrupted`. If `finish_turn` had already committed `open` with a normal reply, the host is told "with a person" while the chat stays open and the agent keeps answering. The mapping paragraph says the outcome follows what the exchange wrote to the conversation, so the two texts disagree. Open point.
- **Cost of the fail-closed choices, said plainly.** BN-6 hands a chat to a person after every lost exchange, including a plain crash during an ordinary reply. BN-1 hides from the model every earlier message whose answer was a fixed text, including messages that passed the screen before a provider outage. The lead accepted both (PL12, PL14).
- **Lock-in check.** No new outside dependency. The store is the existing `store` kind (Postgres default, memory alternative). The reply and the hand-off go through two hook contracts that AK-G22 and AK-G15 implement later.
- **Surface check (YAGNI).** No new run state, no new identity, no new run-table column. The additions are each tied to a found defect: `version`, `text_digest`, `lost_exchanges`, the sweep step, `Grant.runtime_update_cols`, one index.

## Goals vs. Non-Goals

* **In-Scope Goals:** the order of steps of `Runtime.handle_turn` (F1 to F13, then E1 to E6); the transaction rules of `claim_turn`, `finish_turn`, `record_user_turn`, the takeover helper and `lost_exchanges`; the lease rule; the sweep; the crash rule; the outcome mapping; the store rights (column-limited UPDATE); erasure and retention order against the evidence hold; the files each sub-PR touches.
* **Out-of-Scope Non-Goals:** the wiring of AK-G22 (recipient gate) and AK-G15 (queue) (V12); the chat window and transport; actions from a chat (V11); summaries (V1); put-back of hidden values into replies (V3); giving a chat back to the agent (V2); read tools in a chat (AK-G1-c, only after the owner picks PENDING LEAD 5 (a)); any change to the frozen ticket text.

## Alternatives Weighed

- **A second agent loop for chats.** Rejected by the ticket author (D1): it duplicates every guard. `handle_turn` sits beside `handle` and shares the moved `_tool_step`.
- **Calling `handle` with the history packed as a document.** Rejected (D1): `handle` drops the reply text (`agent_loop.py:450-451`).
- **A new run state `REPLIED`.** Rejected (D2): it needs a migration of the `runs.state` check for no safety gain.
- **Writing `handed_off` before opening the queue item.** Rejected in revision 3 (D9, R2-ADV-2): a crash between the two left a person told "a person will take over" with no item.
- **A separate lease time setting (`lease_s`).** Cut in revision 3 (R2-ADV-5): one lease rule, the tick's stuck rule, on the existing heartbeat.
- **A compare on `next_turn` instead of `version`.** Replaced in revision 3 (R2-ADV-1): `finish_turn` changes the map but not `next_turn`.
- **Hand off only for stops in `HANDOFF_STOPS` after a lost exchange.** Rejected by the round 3 resolve (BN-6 position), lead answer PL14 (a): the original stop is not on the record, and the crash window stays open.
- **A `screened` flag on stored turns.** Rejected, lead answer PL12 (a): it needs UPDATE on the append-only turns table or a second write path.
- **Meter faults as hand-offs, or with no card.** Rejected, lead answer PL13 (a): a hand-off ends the chat for a fault outside the chat; no card breaks "fail loudly, tell a person".
- **The evidence hold wins over erasure.** Rejected, lead answer PL15 (a) (R98 delete-by-user).
- **Table-wide UPDATE for the runtime role.** Rejected, lead answer PL16 (a) (least privilege).
- **A separate `ConversationStore` protocol.** Declined in BN-13: more surface; the loud refusal of an incomplete store (A16) is enough.
- **Holding AK-G1-b until the owner answers about read tools.** Rejected in BN-5: it would block every chat on a question only read tools need.

## Key Decisions & Staging for Next Steps

1. The draft writes F1-F13 and E1-E6 as numbered steps with BN-1, BN-2, BN-6, BN-8, BN-9, BN-12, BN-16, BN-17, BN-18 and BN-25 applied, and the store rules with BN-6, BN-9, BN-11, BN-15, BN-20 and BN-21 applied.
2. The order of the (b) build stays: no read tools in a chat; F12 only in AK-G1-c.
3. The three weak points above go into the draft's "Open points" with a recommendation each. The ticket is not edited.
4. Next EGM steps (not in this task): `egm:egm-review` on the design document with fresh reviewers, then `egm:egm-resolve`, then the build-start review (order 19 A) reads the design together with the ticket.
