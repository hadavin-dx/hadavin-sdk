# AK-G1 round 3 resolve (egm:egm-resolve, AUTO mode; LAST round)

## Honest note (read first: what I did NOT check)
- **I ran no test, lint, mutant, ruff or Postgres.** The only things I executed were one `python3 -I` arithmetic and string check (the ADV-12 surrogate premise and the totals in BN-28). That is scratch output, not evidence. I did not edit the ticket, did not commit or push, and did not touch `DECISIONS.md`, `questions-for-lead.md`, `owner-visible-limits.md` or `HEARTBEAT.md`. This file replaces the skill's default name `goldfish_review_report.md`. I skipped the skill's interactive gate because the brief says AUTO.
- **I did not write revision 3, so I have no author memory of it.** I read the full ticket (575 lines), both round 3 reports, the round 2 resolve (head and decisions), the AK-G2 round 3 resolve (for its layout), LEAD-ORDERS orders 1-34, `amendments.md`, `TICKET-TEMPLATE.md`, and the code cited in Facts F1-F10.
- **I did not check git.** "Commit 42368a3" comes from the brief. I did not confirm that `<repo>/src` equals `ce70eb5`.
- **Not checked (UNVERIFIED):**
  - Exact P4c-2 class names beyond `P4c.md:8-11`, `:53-54` and `:176-192`: whether `MeterUnavailable` subclasses `MeterError`, and the rule-6 table in full (`P4c.md:79-93`, which I read only in part). BN-2 points to that table and does not copy it.
  - P5c's `MaskedLLM` API beyond `P5c.md:268-276` and `:335-342`.
  - AK1 build notes BN-1 to BN-17.
  - Whether PostgreSQL 16 and 17 allow the purge role's row lock (open since revision 2).
  - Whether `tool_calls` written on the manifest path hold masked text only (open since revision 1).
  - Whether `registry.py` has one place that sees both the agents and `principals` (BN-23 says what to look for, and the builder names the place).
  - AK-G15 and AK-G22 have no tickets.
- **Judgements a reader may dispute:**
  - **BN-6** hands a conversation to a person for good after EVERY lost exchange, not only after a stop in `HANDOFF_STOPS` (which is what the brief named). Positions gives the reason.
  - **BN-1** labels every earlier message whose answer was a fixed text. That also hides, for example, a message that passed the injection screen before a provider outage. I chose it because it is the fail-closed side and needs no new column.

## Status, target, gate
- **Status:** resolved (AUTO; categorised). The ticket is NOT edited. The fixes are build notes BN-1 to BN-28 below, and they win over the ticket text.
- **Target:** `handover/tickets/AK-G1.md` revision 3 DRAFT, commit `42368a3`, full file, all sub-PRs.
- **Findings:** 35 ids. I took every severity from the report tables and changed none.
  - `reviews/AK-G1-round3-adversarial.md` R3-ADV-1..19: 0 Blocker, 7 Major (ADV-1 to ADV-7), 10 Minor, 2 Nit.
  - `reviews/AK-G1-round3-correctness.md` R3-COR-1..16: 0 Blocker, 3 Major (COR-1 to COR-3), 8 Minor, 5 Nit.
- **Gate (order 20 item 6):** round 3 is the last round under the cap of 3. A money, redaction or security ticket gets one more round only if its last round had no Blocker and at most 2 Majors. Round 3 has **10 Majors**, all distinct, so **there is no round 4.**
  - The ticket freezes at revision 3 with this file attached. The banner below goes under its revision line.
  - The build-start review (order 19 A, order 20 item 3) reads the ticket and this file together. The RESULT review of built code keeps no round cap.
- **Build start is BLOCKED** on PENDING LEAD 11 (the EGM draft; ADV-7). This is the one item the builder may NOT decide on the recommendation.
  - For every other NEEDS LEAD item (12 to 16), the builder applies the recommended option meanwhile, because each one is the fail-closed side.
  - None of them asks the owner for money, a live call or a key.

## Facts I checked myself (on disk at `<repo>`)
- **F1 (COR-1 TRUE).** `tests/test_p7_tick.py:80-89` asserts the exact list `["sweep","reconcile","stuck","checkpoint","purge_evidence","reprobe_sources"]`. An appended step fails it.
- **F2 (COR-2 TRUE).** `tests/contracts/kinds/store_postgres.py:22-24`: with no `HADAVIN_TEST_PG_DSN` set, it calls `pytest.skip(...)`. The module docstring (`:1-2`) says the skip is on purpose ("so the laptop needs no Docker"). CI sets the variable (`.github/workflows/ci.yml:86`, `:93`). So "fails, not skips" is false on today's code.
- **F3 (COR-3 TRUE).** `_SplitStore` (`store_postgres.py:59-73`) sends only `purge_tool_calls` and `purge_redaction_maps` to the purge store. Every other name goes through `__getattr__` to the runtime-role store.
- **F4 (ADV-2 TRUE).**
  - `P4c.md:8-11`: one `MeteredLLM` around `deps.llm`. Overshoot ends the run `NEEDS_PERSON estimate_exceeded` "with a card". An exit-settle failure ends it `NEEDS_PERSON limits_unavailable` "with a card".
  - `P4c.md:54`: today the main call catches ONLY `ProviderError`, and any other exception from `chat` leaves `handle`.
  - `P4c.md:178`: P4c-2 adds a separate `except MeterError` clause.
  - `P4c.md:179`: `_screen` reads `scope.refusal` and the per-run signal, because `injection_check` swallows exceptions (`P4c.md:53`).
  - So the AK-G1 flow has no row for any of these, and "with a card" clashes with T25.
- **F5 (ADV-4: contradiction TRUE; the reviewer's open question is answered in frozen text).**
  - `P5c.md:274` and `:335`: `Runtime.__init__` requires `isinstance(llm, MaskedLLM) and isinstance(llm.inner, MeteredLLM)`. P5c-3 REPLACES P4c-2's check. P4c's `self.llm.scope(...)` becomes `self.llm.inner.scope(...)`.
  - `P5c.md:270`: `MaskedLLM` has no `__getattr__`, and tests read `rt.llm.inner.calls` (`:355`).
  - `P5c.md:276`: a `chat` outside `run(...)` raises `SessionClosed`.
  - The AK-G1 ticket still says "Test builders wrap it in `MeteredLLM`" (Interface 11 and the Tests header).
- **F6 (ADV-3 TRUE, by the ticket's own text).** In the (b) build, F10 offers only `ask_for_person`. F11 then ends step 1 in every branch: text goes to F13, `ask_for_person` is a stop, and anything else is `unknown_action`. The loop end (`max_steps`) cannot be reached.
- **F7 (ADV-6 TRUE).** D9 and E5: when `open_handoff` raises, E4 is skipped, the run ends `NEEDS_PERSON handoff_unavailable` (final), and the lease is dead. The next message then goes F6 `lost`, then F7 opens `interrupted`, then F6 with `take_over` gives `claimed`, and the model answers it. D6's "never answers again" is false for that path.
- **F8 (ADV-11, COR-16).** `tick.purge_evidence` (`tick.py:184-216`) runs the two 400-day ceilings first. It then calls `hooks.hold_run_ids()` and **re-raises** if the hook raises, so nothing after that point runs. Held runs keep their maps and tool calls until the ceilings.
- **F9 (ADV-15).** `store/migrate.py:24-37` `Grant` has `runtime: str` (table-level privileges), `portal`, `purge` and `purge_cols`. Column grants exist only as `GRANT SELECT (cols)` for the purge role (`:182-186`). A column-limited UPDATE for the runtime role cannot be written today without a new `Grant` field.
- **F10 (small facts).**
  - `tests/conftest.py:68-70` `qualify` overwrites `qualified.jsonl` with one record (COR-11 TRUE).
  - `models.py:190-199` `AuditEvent` requires `run_id`, `domain`, `operation`, `principal` and `source` (COR-14).
  - `k1b/redaction.py` exists (ADV-19).
  - `tickets/AK-G2.md:197-198` is the `lease_s` rule and `:288-289` are C2 and C2b. `tickets/P5c.md:101-103` holds the mask and placeholder words (COR-5 TRUE).
  - `python3 -I`: `"a\ud800b".encode("utf-8")` raises `UnicodeEncodeError` (ADV-12 TRUE).

## Banner for the ticket (placed under the revision line, word for word)
> **BUILD NOTES WIN.** Review round 3 (`reviews/AK-G1-round3-adversarial.md`, `reviews/AK-G1-round3-correctness.md`) had 10 Majors, so there is no round 4 (order 20 item 6). This ticket is FROZEN at revision 3. The builder applies build notes BN-1 to BN-28 in `reviews/AK-G1-round3-resolve.md`; where a build note and the text below disagree, the build note wins. **Build start is BLOCKED until the lead answers PENDING LEAD 11 (EGM draft); the sentence "No PENDING LEAD item blocks the build start" is withdrawn.** The build-start review (order 19 A) reads this ticket together with those notes. The "Changes since" and CHANGELOG sections are history, not instructions. Three sub-PRs: AK-G1-a, AK-G1-b, and AK-G1-c (person-bound read tools, built only if the owner chooses PENDING LEAD 5 (a)). Totals after the notes: 62 test rows (-a 21, -b 39, -c 2); 111 mutant ids (A 38, B 73); the (b) stage runs 107, and 110 after AK-G1-c (M-B70 retired). Store methods: 9. Tables: 2.

## Decisions (one decision per finding id; duplicates merged)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major) | PROPOSE FIX (history label from the existing `fixed` field; no new column; PENDING LEAD 12, NEEDS LEAD) | TRUE. When building history, any user turn whose answer turn is `fixed=True` is shown to the model as a fixed label, never as its text. New T9 assertions on what the model receives, and mutant M-B71. **BN-1.** |
| R3-ADV-2 (Major) | PROPOSE FIX (PENDING LEAD 13, NEEDS LEAD, money) | TRUE (F4). After the claim: `MeterError` and P4c-2's signals become passing-fault stops with P4c-2's codes. `RedactionError`/`InputTooLarge` in F13 becomes `redaction_error`. Every other `Exception` takes the crash rule (`internal_error`). The two money signals post P4c-2's fixed money card, with no `_abstain`. New row T40, wider T12 and T36, mutants M-B72 to M-B75. **BN-2.** |
| R3-ADV-3 (Major) | PROPOSE FIX | TRUE (F6). T9's `max_steps` case and M-B53 move to AK-G1-c. The (b) stage runs 107 mutants (BN-28), and every count line follows BN-28. **BN-3.** |
| R3-ADV-4 (Major) | PROPOSE FIX (with a CONTESTED part) | The contradiction inside AK-G1 is TRUE. The question "does Runtime unwrap, and what if `run` is missing" is answered in frozen text (`P5c.md:270`, `:274`, `:276`, `:335`; F5). So: one stack `MaskedLLM(MeteredLLM(raw))` in tests and production, no fallback, and Interface 11 and 12 are fixed. **BN-4.** |
| R3-ADV-5 (Major) | PROPOSE FIX (vehicle: AK-G1-c; PENDING LEAD 17, INFORM) | TRUE. The (a) work becomes its own sub-PR, AK-G1-c, with its own branch, tag, evidence files and uncapped result review. It is built only after AK-G1-b merges AND the owner picks PENDING LEAD 5 (a). Holding AK-G1-b back is rejected. **BN-5.** |
| R3-ADV-6 (Major) | PROPOSE FIX (wider than asked: every takeover hands off; PENDING LEAD 14, NEEDS LEAD) | TRUE (F7). The takeover in `claim_turn` and in `lost_exchanges` writes `state="handed_off"`. A message arriving at a takeover is recorded (as in F5) and not answered. PENDING LEAD 2(vii) is withdrawn. New mutant M-A35. **BN-6.** |
| R3-ADV-7 (Major) | PROPOSE FIX (header) + NEEDS LEAD (PENDING LEAD 11; BLOCKS build start) | TRUE. The header sentence is withdrawn. Build start of AK-G1-a and AK-G1-b waits for the lead's answer on the user's standing EGM rule. **BN-7.** |
| R3-ADV-8 (Minor) | PROPOSE FIX | TRUE. Cite `P4c.md:8`. `handle_turn` opens `self.llm.inner.scope(agent, run_id=run)` and never books cost itself. **BN-8.** |
| R3-ADV-9 (Minor) | PROPOSE FIX | TRUE. Each user turn stores `text_digest` (a keyed digest of the stored masked text). A reused `message_id` with a different digest gives `refused message_id_reused`. Mutant M-A36. **BN-9.** |
| R3-ADV-10 (Minor) | PROPOSE FIX | TRUE. In A3 the second claim passes the CURRENT version. A7 is dropped from M-A4's killers. **BN-10.** |
| R3-ADV-11 + R3-COR-16 (Minor, Nit) | PROPOSE FIX (PENDING LEAD 15, NEEDS LEAD: owner rule R98 versus the evidence hold) | TRUE (F8). Erasure and conversation retention win over the hold for the run maps and tool calls of chat runs. The conversation purge runs BEFORE the hold hook. New row A22, mutant M-A37. **BN-11.** |
| R3-ADV-12 (Minor) | PROPOSE FIX | TRUE (F10). F2 refuses text that is not valid Unicode scalar values with `refused message_unreadable` (audited). T15 extended, mutant M-B79. **BN-12.** |
| R3-ADV-13 (Minor) | PROPOSE FIX (rollback text); DECLINE the separate `ConversationStore` protocol | Partly TRUE. The revert is safe for custom stores (the old protocol comes back). The drop of the tables gets a pre-drop count file. A second protocol would add surface for a refusal that A16 already makes loud. **BN-13.** |
| R3-ADV-14 + R3-COR-2 + R3-COR-10 (Minor, Major, Minor) | PROPOSE FIX (surface cut: the "fail, not skip" claim and its evidence file are DELETED) | TRUE (F2). The skip is the helper's intent, and changing a shared helper is outside this package. Instead, the Postgres evidence runs with `HADAVIN_TEST_PG_DSN` set and must show 0 skipped among the conversation contract rows. The A-mutant run sets the variable. Commands are "to be filled at build" with fixed rules. **BN-14.** |
| R3-ADV-15 (Minor) | PROPOSE FIX (partial index, INFORM) + NEEDS LEAD (column UPDATE grant, PENDING LEAD 16, least privilege) | TRUE (F9). Add a partial index on `busy_run_id IS NOT NULL`. Recommended: a new `Grant` field for column-limited runtime UPDATE, with a negative test. Mutant M-A38. **BN-15.** |
| R3-ADV-16 (Minor) | PROPOSE FIX (surface cut) | TRUE. Values that first appear in the model's reply are never saved. `finish_turn` gets the map as it was before F13, and the stored answer labels the rest. T5 extended, mutant M-B78. **BN-16.** |
| R3-ADV-17 (Minor) | PROPOSE FIX | TRUE. A T37 variant with a hook that hangs past the quiet limit, plus mutants M-B76 (`idempotency_key` not the run id) and M-B77 (`touch` before a hook removed). The timeout stays a contract, said plainly. **BN-17.** |
| R3-ADV-18, R3-ADV-19, R3-COR-12, R3-COR-13, R3-COR-14, R3-COR-15 (Nits) | PROPOSE FIX (one line each) | TRUE. **BN-18.** |
| R3-COR-1 (Major) | PROPOSE FIX | TRUE (F1). `tests/test_p7_tick.py` goes into AK-G1-b CHANGE, and its list assertion gains `sweep_conversations` at the end. **BN-19.** |
| R3-COR-3 (Major) | PROPOSE FIX | TRUE (F3). `_SplitStore` routes `purge_conversations` and `forget_user` to the purge store. `store_postgres.py` is already in -a CHANGE. **BN-20.** |
| R3-COR-4 (Minor) | PROPOSE FIX | TRUE. Both tables gain `schema_version INTEGER NOT NULL DEFAULT 1`. **BN-21.** |
| R3-COR-5 (Minor) | PROPOSE FIX | TRUE (F10). Four cites fixed. **BN-22.** |
| R3-COR-6 (Minor) | PROPOSE FIX | TRUE. The conversation load rules run where both the agents and `principals` are known, not in `_load_tools`. **BN-23.** |
| R3-COR-7 (Minor) | PROPOSE FIX | TRUE. Fake clock rule stated. **BN-24.** |
| R3-COR-8 (Minor) | PROPOSE FIX (surface cut: no run read) | TRUE. A duplicate whose answer slot is filled is mapped from the conversation and the stored answer turn, never from the run. **BN-25.** |
| R3-COR-9 (Minor) | PROPOSE FIX | TRUE. `handle` maps by reason string and never re-reads limits. **BN-26.** |
| R3-COR-11 (Minor) | PROPOSE FIX | TRUE (F10). One qualified agent per registry. A test that needs two writes both records itself. **BN-27.** |

No finding is CONTESTED as a whole. The one contested part (ADV-4's open question) is answered by frozen P5c text that the ticket should have cited. No ESCALATE. One partial DECLINE: ADV-13's second protocol.

## Build notes (round 3), to be copied into the ticket as the section "Build notes (round 3)"

**BN-1. Earlier messages that were not answered by the model are shown as a label (R3-ADV-1; PENDING LEAD 12).**
- **Rule (F10, history):** `list_turns(..., before_turn_no=n, last=history_turns)` returns whole pairs, because `history_turns` is even and turns alternate. For each pair whose assistant turn has `fixed=True`, the user turn is given to the model as `defaults.CONVERSATION_UNPROCESSED_TEXT = "[an earlier message was not processed]"`, never as its stored text. The fixed assistant turn is shown as it is.
- **Why `fixed` is enough:** an answer is fixed exactly when the model's reply did not reach the person. That covers a paused fault (`guard_unavailable`, `evidence_unavailable` at F8, `provider_error`, limits, kill switch), a hand-off reply, and the lost-answer filler. So every turn whose screen failed, was skipped or never finished is covered, with no new column and no UPDATE on `conversation_turns`, which stays append-only.
- **Cost, said plainly:** the model also loses an earlier message that DID pass the screen before, for example, a provider outage. The person must repeat it.
- **Tests:** T9's passing-fault cases gain a second exchange. For `guard_unavailable`, `evidence_unavailable` and `provider_error`, a canary in the first message is absent from `ScriptedLLM.calls` of the second exchange (read through the harness's own reference to the `ScriptedLLM`, BN-4), and the label is present. T2's lost-exchange case asserts the label before the filler.
- **Mutant M-B71** (`runtime/agent_loop.py`): the label rule removed (killed by T9).

**BN-2. Exceptions after the claim, and money signals in a chat (R3-ADV-2; PENDING LEAD 13).**
- **F11, the model call:** next to `except ProviderError`, a separate `except MeterError` (as `P4c.md:178` adds to `handle`). The exception becomes the stop code that P4c-2's rule-6 table gives it (`P4c.md:79-93`): `kill_switch` (run `STOPPED`), `run_budget`, `limits.daily_budget`, `limits.monthly_budget`, or `limits_unavailable` when the meter could not be reached. No card, and no `_wall_stop` or `_abstain` call. The chat is paused, and E6 makes the one transition.
- **After every model call and after `_screen` (F9):** read P4c-2's per-run signal and `scope.refusal` (`P4c.md:179`) exactly as `handle` does. Overshoot gives stop `estimate_exceeded`. A settle failure gives stop `limits_unavailable`. A screen refusal gives the rule-6 code. All are passing faults (D6's list gains `estimate_exceeded` and `limits_unavailable`).
- **Money card (PENDING LEAD 13 (a), applied meanwhile):** for `estimate_exceeded` and `limits_unavailable` only, `_end_exchange` also posts P4c-2's FIXED card text (ids and the code, no turn text) through `hooks.post_card`, wrapped like `_deliver`, without `_abstain`. T25 becomes: "spies on `hooks.post_card` and `hooks.request_approval` are never called, except one P4c-2 money card per `estimate_exceeded` or `limits_unavailable` exchange".
- **F13:** `RedactionError` and `InputTooLarge` from `redact_text` give stop `redaction_error` (a passing fault).
- **Crash rule (replaces the "Store failures, one rule" paragraph):**
  - Any other `Exception` raised after the claim commits and before E6 is treated as a crash: one ERROR log line (ids and the class name), one wrapped `_to(run, NEEDS_PERSON, reason)`, result `with_person`, no delivery and no further store call.
  - The reason is `store_unavailable` for a store error class and `internal_error` for anything else. `LeaseLost` keeps its own row (E4).
  - A `BaseException` that is not an `Exception` (for example `KeyboardInterrupt`) is not caught. Then the lease dies and the sweep recovers the slot (BN-6).
  - The sentence "No exception leaves `handle_turn` after F1" becomes "No `Exception` leaves `handle_turn` after F1".
- **Tests:** new **T40** (money in a chat), with a fake meter:
  - `OverBudget` for the day gives `paused`, run `NEEDS_PERSON limits.daily_budget`, zero cards.
  - The overshoot signal gives `paused`, run `NEEDS_PERSON estimate_exceeded`, exactly one card whose text is P4c-2's fixed text and holds no canary.
  - The kill switch through the meter gives run `STOPPED kill_switch`.
  - T12's script list and T36's fault list gain `MeterError`, the overshoot signal, `RedactionError` in F13 and a plain `RuntimeError` from `llm.chat`. T36 asserts `with_person internal_error` for the last one.
- **Mutants:**
  - M-B72: `MeterError` not caught in F11 (T40).
  - M-B73: F13 redaction error not caught (T36).
  - M-B74: catch-all removed (T36).
  - M-B75: the overshoot signal not read (T40).
- Names follow P4c-2 and P4b1 as built. If a name differs on the build base, the builder follows the built name and says so in `AK-G1-b-notes.txt`.

**BN-3. `max_steps` is reachable only with read tools (R3-ADV-3).**
- T9's "`max_steps` reached" case and M-B53 move to AK-G1-c (BN-5), where a tool step can lead to another step.
- In the (b) stage, T9 covers the other stops. The loop stays a bounded `for` loop, so the code is still there.
- Every count line (ticket lines 281, 386, 395 and the revision 3 counts paragraph) is replaced by BN-28.

**BN-4. One wrapper stack, in tests and in production (R3-ADV-4).**
- **Stack:** `MaskedLLM(MeteredLLM(raw))` everywhere, built with P5c's `MaskedLLM.of` over P4b1-b's `MeteredLLM`. `Runtime.__init__` uses P5c-3's check, `isinstance(llm, MaskedLLM) and isinstance(llm.inner, MeteredLLM)` (`P5c.md:274`, `:335`). That check looks through `MaskedLLM.inner`, and P5c-3 replaces P4c-2's check.
- **No fallback:** `handle_turn` always calls `llm.run(...)`. A model object without it cannot reach `Runtime`, and a call outside `run(...)` raises `SessionClosed` (`P5c.md:276`). The meter scope is `self.llm.inner.scope(agent_id, run_id=run.run_id)` (`P5c.md:335`).
- **Interface 11:** "Test builders wrap it in `MeteredLLM`" becomes "test builders wrap it exactly as production does, `MaskedLLM.of(MeteredLLM(ScriptedLLM(...), limits, routes), redactor, audit)`, with one helper in `tests/conversation_support.py`".
- **Interface 12 and the Tests header:** the harness keeps its own reference to the `ScriptedLLM` and reads `calls` from it (`MaskedLLM` has no `__getattr__`, `P5c.md:270`).

**BN-5. AK-G1-c: the vehicle for person-bound read tools (R3-ADV-5; PENDING LEAD 17).**
- **AK-G1-c** is a third sub-PR in this ticket. Branch `core/AK-G1-c` from current `origin/main`; tag `pre-AK-G1-c` by the lead; evidence files `AK-G1-c-tests.txt`, `-suite.txt`, `-lint.txt`, `-mutants.txt`, `-notes.txt`. Its own RESULT review: security path, no round cap.
- **Depends on:** AK-G1-b merged AND the owner's answer PENDING LEAD 5 (a). It touches `tools.py` (K5 hot file), and its merge slot follows order 20 item 5.
- **Content:** the "Build start" list at the top of the ticket, plus BN-3's `max_steps` case and M-B53.
- **Counts:** rows T26 and T27 (plus the (a) parts of T4, T9, T11, T12 and T30). Mutants M-B12, M-B27, M-B28 and M-B53 are added, and M-B70 is retired.
- If the owner picks PENDING LEAD 5 (b) for good, AK-G1-c is never built and V14 gets the trigger "the owner picks (a) later".
- AK-G1-b merges in the (b) shape without waiting for the owner. Holding it back was rejected, because it would block the whole chat on an owner answer that only read tools need.

**BN-6. Every takeover hands the conversation to a person (R3-ADV-6; PENDING LEAD 14).**
- **Store (AK-G1-a):** the private takeover helper, used by `claim_turn` with `take_over` and by `lost_exchanges` with `take_over`:
  - writes the lost-answer filler (`fixed=True`, `delivered=False`), clears the lease, and sets `state="handed_off"`;
  - adds 1 to `version`;
  - in `claim_turn`, then appends this message's masked user turn as `record_user_turn` does (no answer slot, no run row, no lease) and returns `ClaimResult(kind="recorded", ...)`. `recorded` may now come from `claim_turn` too.
- **Flow:** F7's second F6 call ends in `recorded`, so the result is `with_person`, `delivered=False`, no model call. T31's sentences "the new message is answered" become "the new message is recorded, outcome `with_person`, zero model calls". T18, T34 and T35 each also assert `state == "handed_off"` after the takeover.
- **What this closes:** D6's "final" is now true on every path, including a queue outage and a crash between E2 and E4. One invariant, stated in D9: a "needs a person" item for an exchange exists if and only if the conversation is `handed_off` once the takeover commits. PENDING LEAD 2(vii) is WITHDRAWN, and the sweep paragraph's "the conversation stays `open`" is deleted.
- **Tests and mutant:** A4, A5 and A18 assert the state. **M-A35** (`store/memory.py`): the takeover leaves `state="open"` (killed by A4, A18, T31).

**BN-7. The EGM draft blocks build start (R3-ADV-7; PENDING LEAD 11).**
- The header's "No PENDING LEAD item blocks the build start" is withdrawn. Replacement: "Build start of AK-G1-a and AK-G1-b is BLOCKED until the lead answers PENDING LEAD 11. Every other PENDING LEAD item is applied on its recommendation."
- PENDING LEAD 4 is superseded by 11. Round 3 has happened, so 4's "before round 3" can no longer be met.

**BN-8. Meter scope and cost booking (R3-ADV-8).**
- F8: "P4c-2's meter scope opens around the rest (UNVERIFIED name)" becomes "`with self.llm.inner.scope(agent_id, run_id=run.run_id):` (`P4c.md:8`, `P5c.md:335`)".
- `handle_turn` never calls `limits.charge` or `store.add_cost` itself. The wrapper books every call, the run's and the screen's. F9's "`add_cost` when charged" becomes "booked by the wrapper".
- T21 asserts the booking by run id through the fake meter.

**BN-9. A reused message id with other text is refused (R3-ADV-9).**
- `Turn` and `conversation_turns` gain `text_digest TEXT` (user turns only) = `_keyed_digest(stored_user)`.
- `claim_turn` and `record_user_turn` take `text_digest`. A duplicate `message_id` whose digest differs gives `ClaimResult(kind="reused")` and writes nothing. `handle_turn` returns `refused message_id_reused`, audited as in F2.
- A5 and T14 gain the case. **M-A36** (`store/memory.py`): the digest comparison removed (killed by A5).

**BN-10. A3 and M-A4 (R3-ADV-10).** A3's second claim passes the version returned by a fresh `get_conversation`, so only the lease can refuse it. M-A4's killers become "A3, T13" (A7 is dropped).

**BN-11. Erasure and retention against the evidence hold (R3-ADV-11, R3-COR-16; PENDING LEAD 15).**
- `forget_user` and `purge_conversations` delete the run maps (and, for `forget_user`, the tool calls) of the chat runs named in the deleted turns, whatever `hooks.hold_run_ids` says.
- `runs` rows and labels stay; they hold no text and no user id.
- In `tick.purge_evidence`, the `purge_conversations` call runs right after the two ceilings and BEFORE the hold hook (F8), so a raising hook cannot block conversation retention.
- **New row A22:** a chat run named by `hold_run_ids` still loses its run map to `forget_user` and to the conversation purge, and with a hold hook that raises, `purge_conversations` has still run and the step still fails.
- **M-A37** (`runtime/tick.py`): the conversation purge moved after the hold hook (killed by A22).

**BN-12. Text that cannot be encoded is refused (R3-ADV-12).**
- F2 first checks that `text` holds only Unicode scalar values (no lone surrogate: `text.encode("utf-8")` succeeds). If it fails: `refused message_unreadable`, audited as in F2, nothing masked or stored. This happens before the size check, which then measures the valid encoding.
- T15 gains `"a\ud800b"`. **M-B79**: the check removed (killed by T15).

**BN-13. Rollback (R3-ADV-13).**
- **Reverting AK-G1-a:** restores the old `Store` protocol, so custom stores load again. It is refused while AK-G1-b is merged (b depends on a). The lead reverts in the order c, b, a.
- **Dropping the two tables:** non-revertible, and the lead decides. Before a drop, the lead saves the row counts of both tables (`SELECT count(*)`) to `handover/evidence/AK-G1/pre-drop-<sha>.txt`.
- A16 is the loud-failure test for the protocol growth.
- DECLINED: a separate `ConversationStore` protocol. It adds surface, and A16 and the CHANGELOG line already make the refusal loud.

**BN-14. Postgres evidence: run, never "fail-not-skip" (R3-ADV-14, R3-COR-2, R3-COR-10).**
- **Cut:** the sentence "Postgres rows FAIL, not skip, with no database address", the evidence file `AK-G1-a-postgres-absent.txt`, and its Done item. The shared helper keeps its intended skip (F2).
- **Instead:** `AK-G1-a-postgres.txt` is produced with `HADAVIN_TEST_PG_DSN` set (the variable named at `store_postgres.py:22`), once against PostgreSQL 16 and once against 17, with `pytest -rs`. The file must show **0 skipped** among the conversation contract rows. A skip there fails Done.
- The A-mutant run (`AK-G1-a-mutants.txt`) has the same variable set, because M-A3, M-A9, M-A13, M-A14, M-A21, M-A22, M-A25 and M-A38 are killed only by Postgres rows.
- **Commands to be filled at build, by these fixed rules:**
  - Each throwaway server gets its own uniquely named data folder under the scratchpad, is started from the installed binaries, holds made-up data only, and is deleted by the agent that created it (order 22 item 20, order 27 item 46).
  - The exact `initdb`/`pg_ctl` lines and the DSN go into the first lines of the evidence file.
  - The mutation command comes from P1m's merged docs and goes into the first line of each mutants file.
- **Done:** "the Postgres-absent run fails as expected" becomes "the Postgres runs on 16 and 17 show 0 skipped conversation rows".

**BN-15. Runtime rights on `conversations` and the lease index (R3-ADV-15; PENDING LEAD 16).**
- **Partial index (INFORM):** `CREATE INDEX ... ON conversations (busy_run_id) WHERE busy_run_id IS NOT NULL`, for `lost_exchanges`.
- **Column-limited UPDATE (PENDING LEAD 16 (a), applied meanwhile):**
  - `Grant` gains `runtime_update_cols: tuple[str, ...] = ()`. When the tuple is set, `migrate` grants `UPDATE (cols)` instead of table UPDATE, and `effective_problems` checks it.
  - The `conversations` row becomes `Grant("table", "SELECT, INSERT", runtime_update_cols=("state", "next_turn", "version", "mapping", "busy_run_id", "busy_since", "updated_at"), purge=..., purge_cols=...)`.
  - A10 gains: as the runtime role, `UPDATE conversations SET tenant = ...` (and `user_id`, `readers`, `agent_id`) is refused.
  - **M-A38** (`store/migrate.py`): whole-table UPDATE restored (killed by A10).
  - `store/migrate.py` is a hot file (P2a). This PR adds the field, and no other row changes.

**BN-16. Values the model invents are never saved (R3-ADV-16).**
- Before F13, take `kept = _keep(rmap)` (the map after the user message and any tool step). F13 masks the reply with `rmap` as now. Then `stored = label_unsaved(r)` is computed against `kept`, and `finish_turn` gets `mapping=kept`.
- So a value that first appears in the model's reply becomes `[hidden <kind>]` in the stored answer and never enters the saved map. The map grows only from the person's messages (bounded by F4) and tool results (bounded by `max_map_entries` per run).
- T5 gains: the made-up address the model invented is absent from `conversations.mapping`. **M-B78**: `finish_turn` gets `_keep(rmap)` after F13 (killed by T5).

**BN-17. Hooks that hang (R3-ADV-17).**
- Said plainly: `CONVERSATION_HOOK_TIMEOUT_S` is a contract on AK-G22 and AK-G15, and `Runtime` does not enforce it.
- What protects a hang: the `touch` before each hook, then the tick's `stuck` step, then E6's wrapped transition.
- T37 gains a variant: `deliver_reply` blocks while the test ages the run past its quiet limit and runs the tick. The call then returns `with_person interrupted`, there is no second transition, and exactly one item exists after the sweep.
- Mutants:
  - **M-B76**: `HandoffRequest.idempotency_key` set to a fresh id instead of the run id (killed by T34: two items).
  - **M-B77**: the `store.touch` before E5 removed (killed by a T34 spy on the store's call order: `touch` then `open_handoff`).

**BN-18. One-line fixes (R3-ADV-18, R3-ADV-19, R3-COR-12, R3-COR-13, R3-COR-14, R3-COR-15).**
- **ADV-18:**
  - F1 raises `Unqualified` only when the agent is not in `self.agents`. A qualified agent without `conversation` gets `ValueError("agent is not conversational")`.
  - `FixedReplies` fields default to `defaults.CONVERSATION_HANDOFF_TEXT` and `defaults.CONVERSATION_PAUSED_TEXT`.
  - Interface 5 states that `max_message_bytes` may only be lowered (`le` equals the default).
- **ADV-19:** the "Checked and NOT used" list gains `k1b/redaction.py` (case-replay redaction, not run-time masking).
- **COR-12:** "keyed digests only" gains "(dev without `restored_key`: a plain hash of MASKED text, `agent_loop.py:263-267`)".
- **COR-13:** the producers row needs `redact_untrusted` and `redact_text` called directly in the body of `handle_turn`, not in a helper, because `_called_names` reads only the function body. M-B4 and M-B33 also cover the reply mask.
- **COR-14:** a refusal `AuditEvent` has `principal = f"chat:{agent_id}"`, `source = "runtime"`, `domain = "conversation"`, `operation = "refused"`, and `run_id` = the pre-made id (precedent: `Limits._event`, `limits.py:34`).
- **COR-15:** D2's cite `runs.py:31` becomes `runs.py:30-32`.

**BN-19. The tick step list test (R3-COR-1).**
- AK-G1-b CHANGE gains `tests/test_p7_tick.py`. Its assertion at `:81-88` gains `"sweep_conversations"` as the LAST element. That makes the existing test the pin of the appended step.
- The sentence "Existing tests that may break: none expected" becomes "one existing test changes on purpose: `tests/test_p7_tick.py:80-89` (the step list)". The Files field lists it.

**BN-20. Purge routing in the Postgres contract helper (R3-COR-3).**
- `_SplitStore` (`tests/contracts/kinds/store_postgres.py:59-73`) gains `purge_conversations` and `forget_user`, both sent to `self._purge`, as `app.build` sends them through `purge_store` (`app.py:151-160`). That file is already in AK-G1-a's CHANGE list.
- A8, A9, A20, A21 and A22 on Postgres then run with the purge role's rights only.
- `lost_exchanges` stays on the runtime role (Interface 2).

**BN-21. `schema_version` columns (R3-COR-4).** Both tables gain `schema_version INTEGER NOT NULL DEFAULT 1`, as `runs` has (`0001_core.sql:7`), so the generic `_row`/`_select` helpers can be used. The builder may still write hand-written SQL. Either way, A1 reads a record back through the model.

**BN-22. Stale cites (R3-COR-5).**
- `AK-G2.md:78` and `:196` become `:197-198` (the `lease_s` rule). `:286-287` becomes `:288-289` (C2, C2b).
- The "mask / placeholder" words cite `P5c.md:101-103` instead of `:64`.

**BN-23. Where the load rules run (R3-COR-6).**
- The conversation rules are checked for EVERY agent with `conversation`, whether or not it has a `tools/<agent>.yaml`:
  - `scope_allowed` empty;
  - in the (b) shape, `tools_allowed` empty;
  - `ask_for_person` reserved;
  - no `principals.yaml` id starting with `chat:`.
- They run in one new function `_conversation_problems(agents, principals)`, called at the point of registry load where both are known (`registry.py:218` loads principals; `_cross_check` at `:338` does not receive them today). `_load_tools` (`:275-276`) is not that point.
- T10 and T32 name `registry.py` as the file. M-B24, M-B25 and M-B70 patch that function.

**BN-24. Clocks in tests (R3-COR-7).** The Tests header's "Every time is the fake clock" becomes: "Times handed to `claim_turn`, `finish_turn` and the tick start at `models.now()` and only move forward. A test that ages a run sets `runs.updated_at` directly (`tests/test_p7_tick.py:225-243`), because `touch` writes the wall clock (`store/memory.py:90`, `store/postgres.py:280`)."

**BN-25. Duplicate outcome from the stored conversation (R3-COR-8).**
- When a duplicate's answer slot holds a turn, the outcome is mapped from the conversation and that turn, never from the run:
  - `state == "handed_off"` gives `with_person`;
  - `open` with `fixed=False` gives `replied`;
  - `open` with `fixed=True` gives `paused`.
- After BN-6, a filler slot implies `handed_off`, so it gives `with_person`. This holds even while the first run is still `WORKING` between E4 and E6.
- T14 gains that window, with a crash-injection point after E4 and a resend before E6.

**BN-26. `handle`'s reason mapping (R3-COR-9).** Interface 6 becomes: "`handle` maps the returned reason STRING to the old transition, `kill_switch` to `_to(STOPPED, kill_switch)`, `limits.<x>` to `_to(NEEDS_PERSON, limits.<x>)`, `run_budget` to `_abstain(NEEDS_PERSON, run_budget)`, without calling `_limits_stop` or reading limits again. The `run_budget` guard note is written once, by `_limit_reason`." These names cannot clash with tool-step reasons. M-B40 stays.

**BN-27. Qualification in tests (R3-COR-11).** `qualify` writes ONE record (`tests/conftest.py:68-70`). Every AK-G1 test builds a registry with ONE qualified agent: F0's base side, its branch side and T38 each have their own registry. A test that needs two agents in one `Runtime` writes both green records itself in one `qualified.jsonl`. No AK-G1 test needs it today.

**BN-28. Table delta and totals (one place for the builder).**
- **Test rows: 62.**
  - AK-G1-a 21: A1-A10, A12-A22, with new A22.
  - AK-G1-b 39: F0, T1-T25, T28-T40, with new T40.
  - AK-G1-c 2: T26, T27.
  - Extended rows (no new id): T2, T5, T9, T12, T14, T15, T18, T21, T25, T31, T34, T35, T36, T37, A3, A4, A5, A10, A18.
- **Mutant ids: 111.**
  - A 38: M-A1 to M-A38, with new M-A35 to M-A38.
  - B 73: the revision 3 set plus M-B71 to M-B79.
  - The (b) stage runs **107**: all except M-B12, M-B27, M-B28 and M-B53, which come with AK-G1-c.
  - After AK-G1-c: **110** (those four added, M-B70 retired).
  - If PENDING LEAD 5 (b) is final: 107.
- **Store methods: 9** (unchanged; `claim_turn` and `record_user_turn` gain `text_digest`).
- **New result kinds:** `reused` (store); `recorded` from `claim_turn` too.
- **New reasons:** `message_unreadable`, `message_id_reused` (refusals); `estimate_exceeded`, `limits_unavailable`, `internal_error`.
- **New defaults:** `CONVERSATION_UNPROCESSED_TEXT`, `CONVERSATION_HANDOFF_TEXT`, `CONVERSATION_PAUSED_TEXT`.
- **New column:** `text_digest`. **New field:** `Grant.runtime_update_cols`. **New index:** 1.
- **Cut:** the Postgres-absent evidence file and its Done item; the 2(vii) residual; the run read for duplicate mapping.
- **Evidence files gain:** `AK-G1-c-*.txt` (BN-5) and `pre-drop-<sha>.txt` (BN-13, lead-run, only at a drop). They lose `AK-G1-a-postgres-absent.txt`.

## Positions
- **BN-6 goes wider than "hand off for `HANDOFF_STOPS`".**
  - The narrow rule would need the takeover to read the lost run. That run's reason is `handoff_unavailable`, not the original stop, because E6's precedence puts it first. So the original stop is not even on the record.
  - The narrow rule also leaves the crash window between E2 and E4 open: there the run is `WORKING`, and nobody knows a hand-off was due.
  - Every takeover already opens an `interrupted` item, so a person is already pulled in. Making the conversation `handed_off` at the same commit gives one invariant (item if and only if handed off) and needs no run read.
  - Cost: a crash or a store fault in an ordinary reply ends that chat for good, and a person continues it.
- **BN-1 uses the existing `fixed` field** instead of a `screened` flag. A flag would need either an UPDATE on the append-only turns table (a new runtime right) or a second write path. The label is fail-closed and adds no right.
- **BN-14 and BN-16 are surface cuts.** BN-14 deletes a claim that was false on today's code instead of changing a shared test helper. BN-16 deletes a growth path instead of adding a second cap.
- **BN-5 picks a third sub-PR over holding AK-G1-b back.** The owner's answer on read tools must not block a chat that offers none.
- **ADV-4 is fixed by citing P5c, not by new design.** The frozen P5c text already settles the Runtime check and the absence of a fallback.
- **No CONTEST.** Every Major was checked against code or frozen ticket text (F1-F7), and each holds.

## Couplings
- **P4c-2 / P4b1-b:** BN-2 relies on `MeterError`, the rule-6 codes, the per-run signal and `scope.refusal` (`P4c.md:79-93`, `:178-179`), and on P4c-2's fixed card text for `estimate_exceeded` and `limits_unavailable`. If P4c-2's helper that posts the card also ends the run, AK-G1-b adds a card-only helper next to it, in the same file. The P4c-2 builder is told so through this coupling, and no P4c text changes.
- **P5c-3:** BN-4 uses its `Runtime` check, `MaskedLLM.of`, `inner` and `run(...)`. AK-G1-b builds after P5c-3 (already in the split table).
- **P2a (hot file `store/migrate.py`):** BN-15 adds the `Grant.runtime_update_cols` field. P2a's rows are untouched. CI runs the grant check on PostgreSQL 16 and 17 (order 20 item 1, order 21 item 15).
- **AK-G15:** it receives one `interrupted` item per lost exchange, and the conversation is then `handed_off` (BN-6). It must still dedupe on `idempotency_key`. Order 34 item 72 also moves `compare_ids`, `IdComparison` and `list_inbound` to AK-G15/V7. No AK-G1 name changes for that, but AK-G15 now carries both packages' reconciliation work.
- **AK-G2:** when AK-G2's signed webhook carries chat, order 34 item 70 applies to its sources: one agent id or principal id is never shared across tenants. AK-G1 itself adds no tenant-per-agent rule (one deployment per client, order 27 item 56). The cites follow BN-22.
- **`runtime/tick.py`:** BN-11 moves the conversation purge before the hold hook. BN-19 pins the step list.
- **`owner-visible-limits.md`:** PENDING LEAD 2(vii) is withdrawn and replaced by BN-6's sentence. BN-1's cost sentence is added. The lead edits the file.

## PENDING LEAD (continuing the ticket's numbering after 9)
Routing rule: an item that touches an owner-only choice, money, redaction, least privilege, an owner rule or the standing EGM rule is NEEDS LEAD. For every NEEDS LEAD item except 11, the builder applies the recommended option meanwhile, because it is the fail-closed side.

10. **NEW, INFORM. Freeze with build notes, no round 4.** There are 10 Majors, so order 20 item 6 rules out a round 4. The banner goes under the revision line.
11. **NEW, NEEDS LEAD (the user's standing EGM rule: brainstorm, draft, review, resolve, then build; only the user or the lead can waive it). Supersedes PENDING LEAD 4. BLOCKS BUILD START.**
    - (a) The lead waives brainstorm and draft for AK-G1. The three ticket rounds, these build notes and the build-start review count as the plan check.
    - (b) **Recommended:** before build start, run `egm:egm-brainstorm` (short, from GAPS G1 and this ticket), then `egm:egm-draft` on the `handle_turn` flow and the store transaction rules with BN-1 to BN-28 folded in. The build-start review (order 19 A) then reads the draft together with the ticket. It is not a fourth ticket round: the ticket stays frozen.
    - Evidence for (b): rounds 2 and 3 found Blockers and Majors in exactly that ordering (round 2: map writes and the hand-off order; round 3: ADV-1, ADV-2 and ADV-6), and BN-6 changes the ordering again.
    - Cost: one draft step. Confidence 75 percent.
12. **NEW, NEEDS LEAD (redaction and security). Unprocessed earlier messages in history (BN-1).**
    - (a) **Recommended:** the label rule on `fixed` answers. No new column and no new right.
    - (b) A `screened` flag on turns. It needs UPDATE on turns or a second write path.
    - Confidence 80 percent.
13. **NEW, NEEDS LEAD (money). Meter errors and money signals in a chat (BN-2).**
    - (a) **Recommended:** the codes become passing faults. `estimate_exceeded` and `limits_unavailable` post P4c-2's fixed money card, with no turn text, and the chat pauses.
    - (b) No card, only the run record. This breaks the "fail loudly, tell a person" money rule.
    - (c) Put both into `HANDOFF_STOPS`. That ends each affected chat for good for a fault in the model route or the meter, not in the conversation.
    - Confidence 75 percent.
14. **NEW, NEEDS LEAD (owner-visible; R368 and D6). Every lost exchange hands the conversation to a person (BN-6).**
    - (a) **Recommended:** every takeover writes `handed_off`. PENDING LEAD 2(vii) is withdrawn. New owner-visible sentence: "after a crash, a store fault or a queue outage during an answer, that chat continues with a person, not with the agent".
    - (b) Only lost runs whose reason is `handoff_unavailable` hand off. This leaves the crash window open.
    - Confidence 75 percent.
15. **NEW, NEEDS LEAD (owner rules R98 delete-by-user and the evidence hold). Erasure against the hold (BN-11).**
    - (a) **Recommended:** `forget_user` and the conversation purge delete chat runs' maps and tool calls even when the hold names those runs. `runs` rows and labels stay. The conversation purge runs before the hold hook.
    - (b) The hold wins until its 400-day ceiling, and the erasure report says what was kept.
    - Confidence 70 percent.
16. **NEW, NEEDS LEAD (least privilege). Column-limited UPDATE for the runtime role on `conversations` (BN-15).**
    - (a) **Recommended:** the new `Grant.runtime_update_cols` field, with a negative test and a mutant.
    - (b) Keep table UPDATE and rely on the store code. That is narrower than "exact actions and resources".
    - Confidence 80 percent.
17. **NEW, INFORM (merge order). AK-G1-c is the vehicle for read tools (BN-5).** It is built only after AK-G1-b merges and the owner picks PENDING LEAD 5 (a). It takes a `tools.py` slot under order 20 item 5. Confidence 85 percent.
18. **NEW, INFORM. One wrapper stack follows P5c (BN-4).** `MaskedLLM(MeteredLLM(raw))` in tests and production, P5c-3's check, no fallback. Confidence 90 percent.

These eight new NEEDS LEAD and INFORM lines (11 to 16 NEEDS LEAD) should also go under "NEEDS LEAD" in `handover/questions-for-lead.md` (order 19 item 2). This resolve's brief forbids writing that file, so the session copies them.

## Counts
- **Finding ids: 35** (ADV 19, COR 16).
  - Majors: 10 (ADV-1 to ADV-7, COR-1 to COR-3), all distinct. Minors: 18 (ADV-8 to ADV-17, COR-4 to COR-11). Nits: 7 (ADV-18, ADV-19, COR-12 to COR-16).
  - No Blocker. No severity changed.
- **Decision rows: 27.** Merged: ADV-11 + COR-16; ADV-14 + COR-2 + COR-10; the six Nits ADV-18, ADV-19 and COR-12 to COR-15 in one row.
- **Categories by row:**
  - PROPOSE FIX 27, of which:
    - 4 hold surface cuts (BN-14, BN-16, BN-25, and the 2(vii) residual inside BN-6);
    - 1 holds a CONTESTED part (ADV-4's open question, answered by `P5c.md`);
    - 1 holds a DECLINED part (ADV-13's separate protocol).
  - CONTEST 0 whole rows. ESCALATE 0. DECLINE 0 whole rows.
- **Build notes: 28** (BN-1 to BN-28; BN-28 holds the totals).
- **Totals after the notes:**
  - 62 test rows (-a 21, -b 39, -c 2).
  - 111 mutant ids (A 38, B 73). The (b) stage runs 107, and 110 after AK-G1-c.
  - 9 store methods, 2 tables, 3 sub-PRs (-c conditional).
- **PENDING LEAD:** 9 new (10 to 18). 6 are NEEDS LEAD (11 to 16; 11 blocks build start) and 3 are INFORM (10, 17, 18). None asks the owner for money, a live call or a key.
- **Probes run:** 1 `python3 -I` arithmetic and string check, not evidence. Tests, lints and mutants run: 0.
- **Fixes applied to the ticket in this step:** 0, because they are build notes. Remaining unaddressed findings: 0.
