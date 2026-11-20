# Security wording v3: what the tests show and what is still open

DRAFT, version 3 (the last review round), written by core-c's drafter on 2026-11-20.
It replaces SECURITY-README-v2.md. The lead decides where each part goes: part 2 into SECURITY.md, part 3 into README.md.
Parts 1 to 3 are meant to be shippable. Part 4 is the technical appendix; its last section (4.7) is INTERNAL and does not ship.
This draft changes no other file.

---

## 0. Plain glossary (read this first)

As of 2026-11-20 07:50 UTC.

### How to read the marks (one list)
Evidence words (how we know):
- **TESTED**: a named test ran and passed in a recorded batch of tests.
- **MEASURED**: a recorded run measured the number given.
- **UNVERIFIED**: the only basis is someone reading the code. Nothing was run to show it.
- **NOT RUN**: the check was not run at all. Nothing is claimed about its result.

Status words (one per known gap):
- **FIXED**: changed, and a test fails without the change. The change is on the shared branch, and a batch holding that test passed. It is not on the product's main line. No independent reviewer has re-checked it.
- **FIXED ON BRANCH**: changed, and the builder showed a test fails without the change. The change sits on the shared branch only as a work-in-progress commit. Its test batch has NOT RUN. No independent reviewer has re-checked it.
- **PINNED**: not fixed, on purpose. A named test fails if the behaviour changes. This includes a "strict expected failure": a test that records the gap and fails once the gap closes, so someone must update it.
- **STATED**: accepted and described, with no test. Nobody is asked to act.
- **WAITING**: another team must act, and a written request or a lead's written order exists.
- **OPEN**: nobody has fixed or decided it yet. The line names who must act.

Every example value in this file is made up. None is a real secret.

### People and teams
- **The owner**: the person who owns Hadavin, pays for the work and has the final say.
- **The lead**: the coordinating session (software, not a person) on the owner's laptop. It writes the orders and decides open questions. The owner can overrule it.
- **core-b**: the build team that owns the model connectors, the store, the agent loop and the approval-message code. It must install the gate.
- **core-c**: the build team that built the gate, the secret finder changes and text folding. It wrote this file.
- **Builder**: a core-c worker that writes code and runs the tests. **Reviewer**: an independent checker. Reviewers only read; core-c's builders ran the tests.
- **Operator**: the person who installs and runs the kit for a client.
- Note: core-c wrote this file and must act on 10 of the open gaps. Independent reviewers read version 2. Nobody outside core-c has checked these statuses against the code.

### Product words
- **The kit**: this software package (the Hadavin SDK) that client projects are built on.
- **Stages**: there are only three: demo (shows the product with made-up data), pilot (a first, limited use with a real client), prod (normal live use).
- **Model**: the outside AI service that reads text and answers. A **model call** is one request to it.
- **Guardrail call**: a separate request to the cloud vendor's safety service. It is not a model call.
- **Route**: which AI service and which model a call goes to.
- **Model connector**: core-b's code that talks to one AI service and reports the cost of each call.
- **Run** (noun): one job of one agent, from start to finish. The **agent loop** is core-b's code that drives a run step by step. (The mark NOT RUN and the verb "ran" are about tests only.)
- **Tool**: an action an agent may use, such as a search. A **tool result** is the text a tool returns. Each tool call gets a **call number**.
- **Test and replay command lines**: two tools for staff. One runs saved test cases; the other re-plays a stored run for checking.
- **Planted text**: text an attacker put into a document or tool result so that the agent reads it.
- **Sensitive value**: a secret (password, key, token) or an identifying value (e-mail address, host name, account number).
- **Known value**: a sensitive value already in the run map.
- **Mask**: replace a sensitive value with a placeholder. **Placeholder**: a stand-in such as `<SECRET_1>`. The model sees only the stand-in.
- **Run map**: one table per run, kept in memory, that records which real value each placeholder stands for.
- **Secret finder**: core-c's code that searches text for sensitive values by their shape and masks them. There is one secret finder. It runs where text enters a run (tool results, documents, approval messages). Only it adds to the run map.
- **Kind**: the type the secret finder gives each value it finds. Secret kinds: passwords, keys, tokens. Identifier kinds: e-mail, host name, IP address and the like.
- **Withheld**: the secret finder hides a whole line it cannot mask in place, and shows a fixed note.
- **Text folding**: turning look-alike letters (full-width letters, Cyrillic letters that look Latin), invisible characters and accents into one plain spelling before searching.
- **Unicode**: the world standard list of characters. Each Python version carries one edition of it.
- **base64**: a common way of writing any data as letters and digits.
- **The gate**: one wrapper meant to sit in front of every model call. It masks known values, reserves money, makes the call, settles and writes an audit row. It searches for no new values.
- **Installed**: placed at every point in the code that calls a model. The gate is NOT installed yet.
- **Held back**: a known value at a placeholder's edge (it starts with `>` or ends with `<`). The gate masks it last, so the placeholder text stays whole.
- **Framing marker**: the fixed line the agent loop puts around each tool result, so the model sees where tool output starts. It holds fixed words, the call number and the tool's name.
- **Planted-instruction check**: core-b's check that looks for planted orders such as "ignore previous instructions". **Guard failure**: its report that it could not finish.
- **Grounding check**: core-b's check that a name an agent proposes to act on appears in a tool result it cites.
- **Slack**: the chat service where approval messages are posted.

### Money words
- **The store**: the database that records spending, reservations, the stop switch and the audit record. (The place secrets are kept is called the **secrets vault**.)
- **Cap**: the most money one agent may spend in a day and in a month.
- **Worst case**: the most a model call could cost. core-b's code must compute it.
- **Reserve**: before a call, count its worst case against the cap. **Settle**: after the call, replace the worst case with the real cost. **Booked**: the amount counted against the cap at any moment.
- **Price table**: the list of prices per AI service used to work out the worst case.
- **Stop switch**: a flag in the store. While it is on, the store refuses every new reservation. A **stop record** says who turned it on.
- **Database login**: a named account the software uses to reach the store (runtime, purge, reset). Each has its own rights.

### Record and code words
- **Audit row**: one line in the permanent record of what happened. It holds short codes, not message text.
- **Refusal word**: the exact short word the gate or store prints when it refuses. The words are listed in the appendix (4.1).
- **The shared branch**: core-c's pushed line of changes, from which the lead takes code. **The product's main line**: what clients get. Nothing of this work is on the main line.
- **Work-in-progress commit**: changes saved to the shared branch before their tests ran.
- **Working copy**: changes on core-c's disk, not yet saved to any branch.
- **Test**: a small program that checks one behaviour and fails when it changes. **Batch**: one recorded run of many tests.
- **Deliberate code break**: a planted fault used to prove a test can fail.
- **Known gap**: a weakness we know about, or a gap fixed in this work. Each has a number K1 to K63, used in parts 2 and 4. Part 1 uses no numbers.

---

## 1. Owner summary

As of 2026-11-20 07:50 UTC.

1. **Short answer: the gate is written and tested alone. It is not connected, so no agent in use goes through it. Do not promise a client any gate protection yet.**
2. core-b must write the worst-case formula, add the "refused before any answer" mark and install the gate. core-b also has four other open requests: empty cost fields, retried calls, tool-error text and approval-message id fields. core-c must finish and test its leak fixes.
3. This summary names 13 of 63 known gaps. They are ordered by what they put at risk: first secrets reaching the AI service, then money, then stopped work.
4. NOT RUN on this work's code: the full test suite; Python 3.12; database version 17; any live call to an AI service; any end-to-end stop; 238 of the 240 deliberate code breaks for text folding.
5. **Your action (the owner):** read the seven decisions in 1a. Tell the lead by 2026-11-23 12:00 UTC which defaults you overrule.
6. If the owner has not answered by then, the lead applies the default in the last column of 1a. core-c proposed this date; the lead confirms or changes it.
7. Today an agent in use is protected only by the secret finder as it is on the product's main line, without this work's changes.
8. Installing the gate and passing a fresh review will not be enough. The gaps below stay until each one is closed.

Secrets that can reach the AI service (worst first):
9. A secret in a shape the secret finder does not know goes out as written, after install too.
10. Short base64 text is not masked. Measured: 41 of 41 such test lines leaked.
11. Host names without a "host" label are not masked. Measured: 28 of 44 test lines leaked. Decision 3 covers both.
12. The gate never masks the system prompt (the standing instructions) or the tool descriptions.
13. A secret first seen in a tool's error message is not masked in later text (UNVERIFIED). Waiting on core-b.
14. The guardrail call goes around the gate. It is neither masked nor counted against the cap.

Money (worst first):
15. When a call is retried, only the last attempt's cost is counted (UNVERIFIED). Earlier billed attempts are lost, so spending is understated.
16. A reply whose cost field was left empty is booked as free. The gate part is tested; that connectors leave it empty is UNVERIFIED.
17. Nobody has written the worst-case formula yet. Until core-b writes it, the cap has nothing real to reserve.
18. A failed call stays booked for the rest of the day and month. With cap 3.00 and worst case 1.00, three failures stop an agent (worked out, not run).

Stopped work and set-up:
19. Planted text can make a run's later tool-using calls refuse, if it plants a secret equal to a tool's name. Decision 1 covers it.
20. A pilot or prod install on Python 3.12 succeeds, and then the program refuses to start.

Shown by tests (each in core-c's or core-b's tests, on the code alone):
21. In the gate's tests, known values are replaced before a call, in message text and documents only. Not when a tool states "no map"; only the test and replay command lines may.
22. In the gate's tests, a model call needs a reservation, and a refused reservation means no call. This does not cover a call already in flight, the test and replay command lines, or the guardrail call.
23. In two test runs on database version 16, 50 simultaneous requests against a cap of 3.00 reserved 3.00 and refused 47. Booked money can still pass the cap (line 18 and part 2.2).
24. In the gate's tests, its code holds no message or error text, and no audit row in those tests held a secret.

### 1a. The seven decisions (the lead takes them; the owner can overrule by 2026-11-23 12:00 UTC)

| # | Question | What each answer means | Default if no answer, and why |
|---|---|---|---|
| 1 | The gate refuses a model call when planted text makes a known value equal part of a framing marker. core-c has built a narrower rule. Accept it? | Narrower rule (built, not yet batch-tested): refuse only when a known secret of 4 or more characters equals a tool's name or a call number. Wider rule (the lead's earlier order): also refuse when any known value equals a fixed marker word. | The narrower rule. The marker's fixed words are now kept exact either way, so the wider rule adds no secrecy; it only stops more runs. The lead confirms after core-c's batch passes. |
| 2 | Should each audit row also say whether anything was replaced, and which route was used? | Without it, nobody can tell from the record whether masking happened. The row now says only whether a map was used, empty or absent. | Add a "replaced: yes or no" field and the route. No text. core-c builds it. |
| 3 | Build the planned host-name and base64 change, or keep both as known gaps for now? | Keeping them means such values reach the AI service. Two plan reviewers found 6 distinct blocking problems in the plan; core-c is rewriting it. | Keep both as known gaps until a fresh plan review is clean, then core-c builds. Meanwhile the lead drafts a short client note on both gaps and the owner sends it. |
| 4 | Accept that the grounding check now counts a name as present in more cases in Korean, Japanese and Indian scripts? | This happens when an invisible character splits the name. Accepting lets more proposed names pass the check, with no tests for those scripts. | Go back to the older rule for those scripts (it lets fewer names pass) until tests exist. core-c makes the change. |
| 5 | Tighten five wide database rights, or accept them in writing? | Runtime login: can rewrite a reserved amount, and can sign a stop record with any name. Purge login: can delete an open reservation. Reset login: can change any stop-switch row, and can add any audit row. Accepting leaves the cap and the stop record resting on code alone. | Tighten them: narrower rights or one fixed database function per action. The lead decides; core-b changes its database rights. |
| 6 | Should the gate refuse a call whose run map is empty, as the lead ordered, or accept it and mark the audit row, as core-c asks? | Refusing stops each run whose first document held no value the secret finder found. Accepting lets it go on. Either way the gate masks nothing in that call, and a secret the finder missed goes out in both cases. | Refuse, as the lead ordered: it is the stricter choice and already written. core-c's request favours letting runs continue over strictness. |
| 7 | Accept core-c's changes to two of core-b's files, or have core-b redo them? | The files: the Slack approval-message file, and the list of code that calls a model (it now names the gate). Two teams editing one file can collide. | Accept both as core-c's changes, and the lead tells core-b at once. Either change can be undone with one commit. |

---

## 2. For SECURITY.md: "What the tests show and what is still open"

As of 2026-11-20 07:50 UTC.

> **These items describe what tests showed on the gate, the secret finder and the store, each run on its own. UNVERIFIED means a reviewer's reading. "Work in progress" means saved to the shared branch, but its test batch has not run. The shared branch is not the product's main line. None of this describes an agent in use going through the gate.**

Words used here (if this part ships alone): the gate is the wrapper in front of each model call; the run map is the table of placeholders for one run; booked means counted against the money cap; core-b is the team that must install the gate. The full glossary is part 0.

### 2.0 State of the work
- The gate is built and tested alone. core-b has not installed it at any point that calls a model. WAITING on core-b.
- Three tests are marked "expected to fail" until core-b installs the gate. Once it does, they fail on purpose, so someone removes the mark.
- The list of code that calls a model now names the gate. core-c made this four-line change in a core-b file (decision 7).
- core-b must not install the gate before the model connectors can say "refused before any answer" (the lead's order).
- Merged into the shared branch: the approval-message fixes, the glued e-mail fix, the secret finder's look-alike search and its second search round.
- Before that merge, core-c's builder ran 12,392 tests in 135 test files on that code. All passed except two: one was repaired and passed when re-run alone; the other was closed later.
- The merge result itself was not re-tested. It also carries the gate's work in progress below.
- Saved as work in progress, test batch NOT RUN: the gate's fixes for its second independent review (forged marker, tool line, audit marks, interrupts, part of the time limit).
- In core-c's working copy, not yet saved: the secret finder's capped repeat (for K39 and K40). Its batch has NOT RUN.

### 2.1 Masking before a model call (the gate)

Shown by tests:
- In the gate's tests, it replaces each known value with its placeholder before a call. This covers message text and documents only. K8 lists what it skips.
- The gate searches for no new values. The secret finder does that (K1).
- If replacing fails, the gate makes no call and reserves no money. Causes: text too long, not text, out of time, or still changing after 4 rounds. The refusal carries a refusal word and no text.
- If no known value is present, the text goes out byte for byte as it came in.
- In tests, the gate does not change the caller's messages, documents or run map.
- The code that calls the gate must name a run map or state "no map". Leaving it out is an error. Only the test and replay command lines may state "no map" (K9).
- Deliberate code breaks: core-c's builder ran 66 on the gate, before its round-2 fixes. The tests caught all 66.
- Later edits left 24 of those 66 matching no code. The builder then updated them. It reports that tests caught all 81 code breaks on the edited code. No second run has confirmed that.
- core-c's drafter checked on 2026-11-20 that all 81 now match the code. That check ran none of them.

Known gaps and fixed findings:
- **K1. Not protected:** a secret the secret finder never found.
  - Example: a raw `hunter2zz` that no shape matched goes out as written.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody; the secret finder is the control.
- **K2. Not masked, even when known:** values under 3 characters; all-digit values under 6; common words (`admin`, `test`); an identifier that a letter or digit touches.
  - Example: the known identifier `abc123` (an account number, not a secret) stays readable inside `xabc1234`, because a letter touches it.
  - Rule: a secret of 4 or more characters is masked wherever its exact text appears, except as K3 to K7 describe. A 3-character secret and every identifier follow the rules above.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K3. Not masked:** a copy spelled differently from the run map (percent codes, web character codes, look-alike letters, hidden characters, colour codes).
  - Example: known `qrs789`, text `qrs&#55;89` (a web code for the digit 7) goes out as written.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody; text folding in the secret finder is the control (K47).
- **K4. Not masked:** the same value in other capital or small letters.
  - Example: known `db01.acme.example`, text `DB01.ACME.EXAMPLE`.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K5. Not masked whole:** two known values that overlap. Masking the first takes part of the second, so the second's rest stays.
  - Example: known `abcd` and `cdef`; text `abcdef` becomes `<SECRET_1>ef`.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K6. Not protected:** a clean key and a clean value that look sensitive only when joined.
  - Example: `"user_id": "abc123"`, where neither part is in the run map.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K7. Not masked:** a known value that itself looks like a placeholder or sits in angle brackets.
  - Example: a known value `ab<X_1>cd` goes out as written.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K8. Not masked:** the system prompt, tool descriptions, the role label (who speaks), extra message fields, the requested answer format and the route.
  - Example: an operator puts a customer's name in the system prompt; it goes out unmasked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody on the gate. core-b is asked for a start-up check that system prompts come only from the approved list.
- **K9. Not masked:** anything, when a caller states "no map".
  - Example: a replay of an old run sends its text as stored.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K10. Fixed in work in progress:** the audit row said "map in use" when the map was empty or a test replacement was plugged in. The row now says which.
  - Example: a run with an empty map now writes "map empty", not the same row as one with 50 values.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (batch). Who acts: core-c (batch, then fresh review).
- **K11. Fixed in work in progress:** a known secret inside a forged tool-result marker went out unmasked. Now the gate keeps only the marker's fixed words and masks the rest.
  - Example: a document holds a fake marker line whose call number contains the known `S3cr3tPw`; before this fix, `S3cr3tPw` went out.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (batch); the builder reproduced the leak first. Who acts: core-c.
- **K12. Reported, not reproduced:** a secret at a held-back value's edge may leak its tail.
  - Example: known `S3cr3t` and `>abcdef`; a reviewer read that `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`. The builder ran it and got `<SECRET_1><SECRET_2>` (no leak).
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: core-c (a fresh reviewer re-checks; a safety net that refuses the call is in work in progress).
- **K13. Not limited:** the total time the gate spends on one model call. One budget per call now counts time and size, but the matching step inside it has no clock.
  - Example: before the change, 100 messages could each take the full 6-second allowance. Measured after: 100 messages against 2,000 map entries took 0.018 s.
  - Status: OPEN. Evidence: UNVERIFIED (the remaining gap). Who acts: core-c.
- **K14. Not protected:** a run's later tool-using calls. A planted secret that equals a tool's name or a call number makes each of them refuse.
  - Example: a tool result contains `password=search_web`, where `search_web` is a tool's name; later calls in that run refuse.
  - Status: OPEN. Evidence: TESTED (the earlier, wider rule); NOT RUN (the narrower rule). Who acts: the lead (decision 1).
- **K15. Fixed in work in progress:** planted text could rewrite part of a tool's name in the line where the model asked for that tool.
  - Example: a document planted `password=logs`; the model then saw two names for one tool call.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (batch). Who acts: core-c.
- **K16. Fixed in work in progress:** an interrupt (someone stopping the program by hand) while the gate reserved money left no audit row. Now a row is written.
  - Example: the reservation still stays booked after the interrupt; that is the safe side, on purpose.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (batch). Who acts: core-c.
- **K17. Not safe:** two threads writing one run map at once can give one placeholder number to two values.
  - Example: two tools finish together and both values become `<SECRET_3>`.
  - Status: STATED. Evidence: none. Who acts: nobody. Condition for core-b's install: one writer per run map.
- **K18. Not handled:** a gate refusal or a refused reservation leaves the run's status "working" instead of "stopped".
  - Example: the planted-instruction check reports a refused reservation as a guard failure.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: core-b (install request).
- **K19. Not through the gate:** the guardrail call. It is neither masked by the gate nor counted against the cap.
  - Example: a run's guardrail calls cost money that the cap never sees.
  - Status: STATED. Evidence: none (plan decision). Who acts: nobody.

### 2.2 Spending cap

Shown by tests:
- In the gate's tests, it makes no model call without a reservation. Order: mask, reserve, call, settle, write the audit row.
- On core-b's store code, database version 16, Python 3.13: 50 connections asked at once, cap 3.00 for the day and month, worst case 1.00. 3.00 was reserved and 47 refused. The test ran twice.
- Further cases in the same test file: five other cap and worst-case pairs, two agents, and a month cap reached over two days.
- These tests do not cover the database rights in K26 or a call costing more than its worst case (K24).
- In the gate's tests, when a reply arrives with a usable cost, the gate settles that real cost.

Known gaps:
- **K20. Not released:** the worst case of a failed call. The connectors cannot yet say "refused before any answer".
  - Example: cap 3.00, worst case 1.00. Three failed calls book 3.00. It stays booked for the rest of the day (day cap) and month (month cap).
  - Status: WAITING. Evidence: TESTED (a failed call is not settled); UNVERIFIED (the example, worked out). Who acts: core-b (request written).
- **K21. Booked as free:** a reply whose cost field was left empty. The connectors' reply form fills an empty cost with 0, and the gate settles 0 as 0.
  - Example: a connector forgets to fill in the cost; a 0.80 call is booked as 0.00.
  - Status: WAITING. Evidence: TESTED (the gate side); UNVERIFIED (that a connector leaves it empty). Who acts: core-b (request written).
- **K22. Not settled:** a reply whose cost the gate cannot read (negative, not a number, or absent). The worst case stays booked, the safe side.
  - Example: a reply reports its cost as "not a number"; the full 1.00 stays booked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K23. Not counted:** earlier attempts of a call that succeeded after retries. Only the last attempt is settled.
  - Example: attempt 1 times out but was billed 0.40; attempt 2 costs 0.30; only 0.30 is booked.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: core-b (the lead's written order).
- **K24. The cap can be passed once:** a call that costs more than its worst case is booked in full, on purpose.
  - Example: three calls each reserve 1.00 (cap 3.00). One settles at 2.50. Booked: 1.00 + 1.00 + 2.50 = 4.50. Later calls are refused.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody (by design). A sound worst-case formula (K25) keeps it rare.
- **K25. Not written:** the worst-case formula. No function in the code fits the gate today.
  - Example: a formula that ignores documents would make K24 the normal case.
  - Status: WAITING. Evidence: NOT RUN (nothing to test). Who acts: core-b (the lead's written order).
- **K26. Not enforced by the database:** the runtime login can rewrite a reserved amount; the purge login can delete an open reservation.
  - Example: faulty code could lower its own reservation.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the lead (decision 5), then core-b.
- **K27. Not refused:** an out-of-date price table.
  - Example: a vendor raises prices; the worst case is computed at the old price.
  - Status: STATED. Evidence: none (plan). Who acts: nobody.
- **K28. Not capped across processes:** the test and replay command lines keep their cap in memory, per process.
  - Example: two replay processes each spend up to the cap.
  - Status: STATED. Evidence: none (plan). Who acts: nobody.

### 2.3 Stop switch

Shown by tests:
- In the gate's tests, a refused reservation, including the stop switch's refusal, means no model call.
- That the store refuses every reservation while the switch is on is core-b's code. No test of core-b's reservation code for this is named here (UNVERIFIED).
- No end-to-end stop of a live run was tested (NOT RUN).

Known gaps:
- **K29. Not narrowed by the database:** the runtime login can sign a stop record with any name; the reset login can change any stop-switch row.
  - Example: a stop record says "by: operator" when the runtime wrote it. Any change the reset login makes reads as "on", the safe side.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the lead (decision 5), then core-b.
- **K30. Not stopped:** a call already in flight, and the test and replay command lines (they do not read the switch).
  - Example: a 30-second call started before the stop still completes.
  - Status: STATED. Evidence: none (plan). Who acts: nobody.

### 2.4 Audit record

Shown by tests:
- The gate tries to write one audit row per call: run, type of action, who asked, result, and a code from a fixed list.
- In tests, the gate's code holds no logging and no error text, and no audit row in those tests held a secret.
- In tests, if writing the row or settling fails after the reply came back, the gate still returns the reply.

Known gaps:
- **K31. Not recorded:** whether anything was replaced, and the route.
  - Example: an investigator cannot tell from the row whether a secret was swapped.
  - Status: OPEN. Evidence: none (a design question). Who acts: the lead (decision 2).
- **K32. Not narrowed:** the reset login can add any audit row, not only a reset record.
  - Example: faulty reset code could write a row that looks like a model call.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the lead (decision 5), then core-b.
- **K33. Not in the record:** the test and replay command lines print their audit lines to the screen only.
  - Example: a replay leaves no row in the store.
  - Status: STATED. Evidence: none (plan). Who acts: nobody.

### 2.5 The secret finder (what enters the run map)

Shown by tests (on the shared branch, in the batch before the merge):
- It finds the kinds it knows: addresses, keys, tokens, e-mail, passwords in web addresses and command lines, and supplier payment details (a bank account beside its bank code).
- One call masks a bank account beside its bank code. It also masks the part after a known secret inside a longer token, within K40.
- A line it cannot mask in place is withheld.

Known gaps and fixed findings:
- **K34. Not found:** a secret in a shape the secret finder does not know.
  - Example: an unlabelled 40-character code in plain prose.
  - Status: STATED. Evidence: none. Who acts: nobody.
- **K35. Not masked:** a bare number with no label.
  - Example: `ref 55556666 paid`. Measured on the main line: 24 of 43 such test lines not masked.
  - Status: STATED (by decision). Evidence: MEASURED. Who acts: nobody.
- **K36. Not masked:** host names with no "host" word in front; a private name with a public ending is masked only in part.
  - Example: `db01.acme.example` stays; `db01.corp.example` becomes `<HOSTNAME_1>.example`. Measured on the main line, which lacks the planned change: 28 of 44 test lines leaked.
  - Status: OPEN. Evidence: MEASURED. Who acts: the lead (decision 3), then core-c.
- **K37. Not masked:** base64 text under 40 characters.
  - Example: a short password written in base64. Measured on the main line: 41 of 41 such lines leaked.
  - Status: OPEN. Evidence: MEASURED. Who acts: the lead (decision 3), then core-c.
- **K38. Not masked:** an IP address, phone number, international bank account number or unique id with a letter or `_x` glued behind it.
  - Example: `10.20.30.40_x` goes out unmasked. Measured on the merged integration code.
  - Status: OPEN. Evidence: MEASURED. Who acts: core-c (writes the next work item).
- **K39. Not masked:** a value that only a third search round would find. The secret finder now does at most two rounds.
  - Example: planted text glues a bank code to a secret, then puts the account after that code elsewhere. The attacker must know the bank code.
  - Status: OPEN. Evidence: TESTED (strict expected failure). Who acts: core-c (a capped repeat is being built; past its cap it refuses the text).
- **K40. Not masked:** the last part, up to 7 characters, of a longer token in its other copies. This happens when the token was found only after a shorter known secret inside it was masked.
  - Example: `password=ab9x`, then `Bearer ab9xqrstu`; another copy of `ab9xqrstu` shows `<SECRET_1>qrstu`.
  - Status: OPEN. Evidence: TESTED (strict expected failure). Who acts: core-c (the same capped repeat).
- **K41. Not limited:** how long one call of the secret finder takes. Its time allowance is checked between rounds only.
  - Example: 100,000 characters with one secret took 0.206 s before the second round and 0.484 s after (measured). One text may pass through it up to 7 times per call.
  - Status: OPEN. Evidence: MEASURED. Who acts: core-c.
- **K42. Not masked later:** a secret first seen in a tool's error message. It never enters the run map.
  - Example: a tool fails with "bad password hunter2zz"; later results show `hunter2zz`.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: core-b (request written).
- **K43. Not masked:** a secret spelled exactly like an escaped placeholder (`‹SECRET_1›`, with angle quotes).
  - Example: `password=‹SECRET_1›` stays as written, on purpose.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K44. Fixed:** a secret wrapped in look-alike angle quotes was left readable.
  - Example: `password=‹hunter2zz_1›` is now masked.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K45. Fixed for the one place found:** the secret finder, run again on its own output, turned real placeholders into new secrets. The place was the tool-error path.
  - Example: a tool error quoting `<SECRET_1>` no longer adds a new map entry.
  - Status: FIXED. Evidence: TESTED (that place); UNVERIFIED (that no other place does this). Who acts: nobody.
- **K46. Not masked whole:** a secret holding a space, `;`, `,` or `&`. It is masked only up to that character.
  - Example: `password="my secret phrase"` shows `secret phrase`.
  - Status: STATED (in today's SECURITY.md). Evidence: none. Who acts: nobody.

### 2.6 Text folding (look-alike and hidden characters)

Shown by tests (on the shared branch, in the batch before the merge):
- Before the secret finder searches, it folds the text: look-alike letters, invisible characters and accents become one plain spelling.
- Condition: the program runs on Python 3.13 (part 3).

Known gaps and fixed findings:
- **K47. Fixed:** the secret finder's own look-alike search was missing from the shared branch. It is there now.
  - Example: `password=x` written with a Cyrillic "а" is now found.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K48. Not decoded by folding:** escape codes; look-alikes added after Unicode edition 15.1; hidden marks outside two character blocks.
  - Example: the escape code `abc1` is not read as `abc1`.
  - Status: STATED. Evidence: none. Who acts: nobody.
- **K49. Not flagged:** the Chinese character for zero (Unicode name IDEOGRAPHIC NUMBER ZERO, 〇) inside a Latin word.
  - Example: `pay` + 〇 + `al` is not called mixed script. It is the only such character in the folding table (measured).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K50. Not measured:** how often folding finds a known name inside an innocent longer word.
  - Example: known `Mary` found in `summary`; innocent text may be masked or withheld.
  - Status: OPEN. Evidence: UNVERIFIED (core-c's measurement is running, no result yet). Who acts: core-c.
- **K51. Not limited:** the time text folding takes. The planted-instruction check folds up to 2,097,152 characters with no clock.
  - Example: a very large planted text slows that check.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: core-c.
- **K52. Refused, not read:** a very long text in Chinese or Japanese only. It is reported as a guard failure.
  - Example: 300,000 characters of Chinese (measured). Russian prose of that size is read.
  - Status: STATED. Evidence: MEASURED. Who acts: nobody.
- **K53. Chosen by the lead:** dashes and curly quotes are ordinary punctuation; three slash look-alikes make the line withheld.
  - Example: a value right after an em dash (—) is masked in place. A line holding DIVISION SLASH (∕), BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT (╱) or BIG SOLIDUS (⧸) plus a look-alike value is withheld.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K54. Finds more than before:** an invisible character between a Latin letter and its accent. Accepted by the lead.
  - Example: `e` + hidden mark + accent now matches `é`.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K55. Not decided:** the same wider matching in Korean, Japanese and Indian scripts, for the grounding check.
  - Example: a Korean name split by a hidden mark now counts as present.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the lead (decision 4).
- **K56. Fixed:** a secret stored as `Müller` but shown with a separate accent mark was not masked in tool output.
  - Example: `Mu` + combining accent + `ller` is masked again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K57. Fixed:** look-alike padding before a 32,768-character boundary could hide a planted order from the planted-instruction check.
  - Example: "ignore previous instructions" split across that boundary is found again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K58. Fixed:** on the wrong Python, the secrets vault connection was built before the start-up refusal. The refusal now comes first.
  - Example: a pilot build on the wrong Python stops before it reaches any secret.
  - Status: FIXED. Evidence: TESTED (on Python 3.13 with the version faked). Who acts: nobody.

### 2.7 Approval messages

Shown by tests (on the shared branch):
- On each free-text path found so far that writes an approval message, the secret finder runs first. Web addresses are made unclickable last (a dot written as `[.]`).
- 26 path test functions exist. The batch before the merge ran 135 test files with no failure among them; that these were in it is UNVERIFIED, as its file list is not recorded.
- A message is re-read until it stops changing, at most 3 times. If it never settles, a fixed note is shown instead.
- Id fields are not masked (K59).

Known gaps and fixed findings:
- **K59. Not masked:** the "requested by" line and other id fields. Slack reads them as formatting.
  - Example: a requester id `slack:U1|<!channel>` notifies everyone in the channel.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: core-b (request written).
- **K60. Not proven:** that no clickable link remains. The test for it uses the same patterns as the code it tests.
  - Example: a link the patterns miss, such as `see/evil.com`, would slip past both (UNVERIFIED).
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: core-c (adds a link check with its own patterns).
- **K61. Fixed:** an e-mail address with a digit or `_` glued behind it was shown whole.
  - Example: `anna.m@example.org9` is now masked.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K62. Not checked:** old summaries stored in the admin console before these fixes.
  - Example: a summary stored before the fixes could still show an e-mail address; nobody has looked.
  - Status: OPEN. Evidence: NOT RUN. Who acts: core-c.

Measured slowdown of approval-message cleaning on the merged code: a 174-character message went from 1.26 ms to 3.60 ms. A 71,179-character message went from 367 ms to 655 ms (median, on a shared busy machine).

### 2.8 Set-up

- **K63. Late failure:** the project file allows installing on Python 3.12. A pilot or prod install there succeeds and fails only at start.
  - Example: an operator installs on 3.12; the program then refuses to start (part 3).
  - Status: OPEN. Evidence: NOT RUN (no install on 3.12 was tried). Who acts: core-b.

### 2.9 What was not run (NOT RUN)
- The full test suite. Python 3.12 on this work's code (only an older branch ran there once). Database version 17 (the automatic test service uses 17.10).
- Any live call to an AI service. Any end-to-end stop of a live run. The gate installed at any call point.
- The planned host-name and base64 change (never built). 238 of the 240 deliberate code breaks for text folding.
- The test batch on the merge result, on the gate's work in progress, and on the secret finder's capped repeat.

---

## 3. For README.md: "Python version"

As of 2026-11-20 07:50 UTC.

**Operators (the people who install and run the kit for a client) must run pilot and prod on Python 3.13.**

Why: text folding uses the Unicode character data built into Python. Unicode is the world standard list of characters, and each Python version carries one edition. The folding tables are built for edition 15.1.0, which Python 3.13 carries. Python 3.12 carries 15.0.0.

On the shared branch, a pilot or prod program on Python 3.12 refuses to start and prints the error UnidataMismatch. A test shows this order on Python 3.13 with the version faked. The Python 3.12 case was NOT RUN. The project file still allows the install on 3.12, so the failure shows only at start (OPEN, core-b).

The refusal comes before the program connects to the secrets vault or any other outside service.

Demo stage: the program starts on 3.12. Each name that text folding produces carries the Unicode edition, so names made on 3.12 and on 3.13 are meant not to match. Do not mix results from the two. This was NOT RUN on 3.12.

Moving to a later Python (for example 3.14): core-c must first rebuild the character tables. Changing the version number alone is not enough.

---

## 4. Technical appendix

As of 2026-11-20 07:50 UTC. Internal references (codes, test names, files, orders, commits) appear only here.

### 4.1 Key to codes used in the sources
| code | meaning |
|---|---|
| cloud/core-c | the shared branch; head at the time of writing: 9c719c7 (pushed) |
| d95a727 | the merge of the integration (P1d-a card fixes, P2d-1 fold scan, G7, glued-rest fixes) into cloud/core-c, 07:28 UTC. Its second parent cfda4d0 is the pick branch wip-pick; its first parent 1c884b2 is a gate snapshot "work in progress, NOT verified" |
| wip-pick | the worktree branch /tmp/core-c-pick, cut from bd4446c, where the pick batch ran (evidence/PICK-int-onto-core-c.md) |
| fb08bde, 89af120, 1c884b2 | work-in-progress commits on cloud/core-c ("NOT verified") that carry gate round 2, ORDER 017 and the gate review-round-2 fixes |
| aa7c5fa | core-c's 4-line edit of guard/producers.py (core-b's file): the registry test passes (DECISIONS 07:40) |
| working copy | uncommitted edits in /home/user/hadavin-sdk: guard/redact.py, guard/runmap.py, defaults.py, tests (G7 fix round 2, gate fixes) |
| origin/main | the product's main line; d95a727 is not on it (checked with git merge-base) |
| F, G, B, T1 | work packages: F the gate; G the text work; B database rights; T1 the 50-connection cap test |
| G0 | the check-only mask function (later deleted by lead decision) |
| G1 / G2 / G3 | text folding / approval-message text (old branch P1d-a) / the look-alike search ported into the secret finder (old branch P2d-1) |
| G4 | the planned base64 and host-name change (old ticket P1c), not built; G5, G6 docstring wording; G7 the extra search round after the sweep |
| dz, cb / dz2, cb2 | first / second independent result review of the gate: design reviewer (dz), code reviewer (cb) |
| dz-1 to dz-8, cb-M1 to cb-M4 | result review of G7 |
| B1, B2, M3 to M10 | result review of text folding |
| M1 to M7, N1 to N8 | result review of the approval-message text |
| g4r | plan review of G4 (tickets/G4-review-1.md: 8 Blockers, 6 distinct, 12 Majors) |
| E1 to E7 | entries in ESCALATIONS.md (E7: database rights) |
| ORDER nnn | orders from the lead in ORDERS.md; MJ-A to MJ-D = Majors of the lead's review round 3 (ORDER 020) |
| T:: / E:: | tests/test_model_gate.py / tests/test_runmap_enforce_map.py |
| sweep | the step that masks every copy of values already in the run map |
| NO_MAP | the named constant for "no map" |
| strict xfail | strict expected failure |
| refusal words | gate: `mask_refused`, `framing_refused`, `worst_case_failed`, `worst_case_invalid`, `reserve_refused`, `reservation_invalid` (type `GateRefused`); store: `kill_switch` (stop switch), `daily_budget`, `monthly_budget`, `limits_unavailable`, `bad_amount`, `usd_cap` |
| audit decision field | `map_enforced`, `map_enforced_empty`, `enforce_custom`, `map_failed`, `no_map`; codes `call_interrupted`, `reserve_interrupted`, `held_value_left` |
| framing marker | `<<TOOL RESULT call_id=ID tool=NAME>>` ... `<<END TOOL RESULT>>`; assistant line `tool NAME {json}` |
| UnidataMismatch | the start-up refusal of `textnorm.require_pinned_unidata` (README part 3) |

### 4.2 Table of known gaps
| gap | status | evidence level | evidence | who acts |
|---|---|---|---|---|
| K1 secret not found passes | PINNED | TESTED | T::test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job | nobody |
| K2 short, digits, common words, touching | PINNED | TESTED | E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept; E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept | nobody |
| K3 other spellings | PINNED | TESTED | T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate; E::test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced; E::test_stated_limit_a_copy_split_by_nul_characters_is_not_found; T::test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced | nobody |
| K4 letter case | PINNED | TESTED | T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced | nobody |
| K5 overlap tail | PINNED | TESTED | E::test_stated_limit_partial_overlap_leaves_a_tail; T::test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent | nobody |
| K6 joined key and value | PINNED | TESTED | T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched | nobody |
| K7 placeholder-shaped values | PINNED | TESTED | E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced; E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder; E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass | nobody |
| K8 fields not masked | PINNED | TESTED | T::test_t20_system_and_tools_are_not_touched; T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched; install check asked in requests/3-bind-mapping-required.md section 6 (ORDER 020 MJ-D) | nobody (core-b asked for the install check) |
| K9 no map | PINNED | TESTED | T::test_no_map_means_no_enforce_step_at_all; NO_MAP placement checked by tests/test_gate_install_callers.py (plain test) | nobody |
| K10 audit says map in use | FIXED ON BRANCH | NOT RUN | dz2-M5; T::test_r2_m5_the_audit_decision_says_what_was_really_enforced; mutants G22a-c (builder: 81 of 81); WIP commits | core-c |
| K11 forged marker | FIXED ON BRANCH | NOT RUN | dz2-B1, ORDER 020 MJ-A; reproduced by the builder; T::test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client[id,name,both]; old pin renamed to T::test_o17_6_a_value_that_only_lies_inside_a_framing_word_leaves_the_fixed_words_alone; mutants B1a, B1b | core-c |
| K12 edge value tail | OPEN | UNVERIFIED | dz2-M2 (reading); NOT REPRODUCED by the builder (evidence/F-G0-1.md "Review round 2 fixes (final)"); safety net `held_value_left`, T::test_r2_m2_a_held_back_edge_value_does_not_leak_the_tail_of_a_secret, T::test_r2_m2_safety_net_a_held_back_secret_value_left_raw_refuses_the_call; mutant G24 | core-c |
| K13 per-call time and size | OPEN | UNVERIFIED | dz2-M3 PARTLY FIXED: one EnforceBudget per call, cap 256 held-back values; T::test_r2_m3_one_budget_per_chat_call_and_a_cap_on_held_back_values; missing: a deadline inside `_Redactor.sweep`; measured 0.018 s for 100 texts / 2,000 entries | core-c |
| K14 planted secret stops tool calls | OPEN | TESTED (old rule) / NOT RUN (new rule) | T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker; new rule: T::test_r2_m4_an_identifier_kind_value_equal_to_a_tool_name_does_not_stop_the_run, T::test_r2_m1_a_value_the_sweep_never_replaces_does_not_stop_a_run_with_a_tool_of_that_name; mutants O6-O8 | lead |
| K15 tool line rewritten | FIXED ON BRANCH | NOT RUN | cb2-M2; T::test_r2_m2_the_assistant_line_and_the_token_name_the_tool_alike_when_a_value_sits_inside_it; T::test_r2_m2_the_fixed_word_of_the_assistant_line_is_kept_exact; mutants O9, O10 | core-c |
| K16 interrupt leaves no row | FIXED ON BRANCH | NOT RUN | dz2-M7; T::test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on; T::test_pin_no_settle_on_keyboard_interrupt (reservation stays booked); mutants G23a-d | core-c |
| K17 two writers | STATED | none | a race; ticket F stated limits | nobody |
| K18 run left "working" | WAITING | UNVERIFIED | F-result-review-2.md call-site list; ticket F "For core-b (install)": agent_loop.py:477; requests/3-bind-mapping-required.md section 3 | core-b |
| K19 guardrail call outside gate | STATED | none | plan-v3 call-site table; plan-v4-final B3; tests/test_gate_install_callers.py BYPASS table | nobody |
| K20 failed call stays booked | WAITING | TESTED / UNVERIFIED (example) | T::test_pin_an_unmarked_provider_error_is_not_settled; T1 expiry case (counters stay after expiry); requests/2-refused-before-response.md | core-b |
| K21 empty cost booked as free | WAITING | TESTED / UNVERIFIED | T::test_m5_a_zero_cost_reply_is_settled_at_zero; models.py:299 `cost_usd: Decimal = Decimal(0)` (read by core-c in this tree, 2026-11-20); requests/3-bind-mapping-required.md section 4 | core-b |
| K22 unreadable cost not settled | PINNED | TESTED | T::test_pin_a_reply_with_no_usable_cost_is_not_settled; T::test_o17_2_a_reply_whose_cost_is_absent_or_not_a_usable_number_is_cost_unknown_and_not_settled | nobody |
| K23 retries settle last attempt | WAITING | UNVERIFIED | llm/retry.py lines 92-107 (reading, E6 item 3); ORDER 017 item 3 | core-b |
| K24 overshoot booked in full | PINNED | TESTED | tests/contracts/test_t1_reserve_cap.py::test_a_settle_above_the_reserve_books_the_actual_amount_past_the_cap (core-b 576f292, PostgreSQL 16.15); T::test_a_settle_above_the_reservation_is_passed_through | nobody |
| K25 worst-case formula | WAITING | NOT RUN | ORDER 016c item 13; ticket F "For core-b (install)" item 3 | core-b |
| K26 reservation rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md findings 1, 2 (migrate.py:56, read); E7 items 1-2 | lead, then core-b |
| K27 stale price table | STATED | none | plan-v4-final B3 | nobody |
| K28 in-memory cap on command lines | STATED | none | plan-v4-final B3; interface README 2.1; refusal `usd_cap` (ORDER 014) | nobody |
| K29 stop-switch rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md findings 3, 4 (migrate.py:61-62, read); E7 items 3-4 | lead, then core-b |
| K30 in-flight call, command lines ignore stop | STATED | none | plan-v4-final B3 | nobody |
| K31 audit lacks replaced flag and route | OPEN | none | F-result-review-1.md nits; the decision field (4.1) covers map use only | lead |
| K32 reset login audit rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md finding 5 (migrate.py:65, read); E7 item 5 | lead, then core-b |
| K33 command lines audit to screen | STATED | none | plan-v4-final B2 | nobody |
| K34 unknown shape | STATED | none | README "Limits and trust" | nobody |
| K35 bare number | STATED | MEASURED | evidence/P1c-probe.md (24 of 43, main code) | nobody |
| K36 host names | OPEN | MEASURED | evidence/P1c-probe.md (28 of 44 leaked, main code); tickets/G4-review-1.md | lead, then core-c |
| K37 short base64 | OPEN | MEASURED | evidence/P1c-probe.md (under 40 characters: 41 of 41; all base64 rows: 52 of 142; main code) | lead, then core-c |
| K38 glued IPv4, phone, IBAN, UUID, host label | OPEN | MEASURED | evidence/INT-g2-g3.md follow-up (c); now in d95a727 | core-c |
| K39 third round | OPEN | TESTED (strict xfail) | tests/test_redact_idempotent_property.py::test_one_pass_is_a_fixed_point_and_leaves_no_raw_copy[constructed:0]; ORDER 020 MJ-B; fix in the working copy (G7 fix round 2: `_SETTLE_ROUNDS` = 4, RedactionError("NotSettled"); tests/test_redact_settle_loop.py, 20 of 28 failed before; batch NOT RUN) | core-c |
| K40 tail up to 7 | OPEN | TESTED (strict xfail) | tests/test_redact_idempotent_property.py::test_limit_the_tail_of_a_compound_value_found_late_is_not_swept_from_its_other_copies; G7 review dz-2; same working-copy fix | core-c |
| K41 finder time | OPEN | MEASURED | evidence/G7-1.md perf, try 1; G7 review dz-3 | core-c |
| K42 tool error not in map | WAITING | UNVERIFIED | G7 review dz-6 (reading); requests/4-error-reason-run-map.md | core-b |
| K43 escaped-placeholder spelling | PINNED | TESTED | tests/test_redact_own_output.py::test_only_the_exact_escaped_shape_is_left_alone; tests/test_redact_own_output_hardening.py::test_legitimate_own_output_is_left_alone | nobody |
| K44 wrapped secret | FIXED | TESTED | tests/test_redact_own_output_hardening.py::test_a_secret_wrapped_in_lookalike_brackets_is_masked (10 failed before; ab6ff2f; kept in the pick) | nobody |
| K45 finder on its own output | FIXED | TESTED / UNVERIFIED (other places) | tests/test_redact_own_output.py::test_the_tool_error_path_adds_no_map_entry_and_keeps_the_escaped_text (8 failed before); caller table in tickets/G7-context-after-sweep.md (reading) | nobody |
| K46 separators in a secret | STATED | none | SECURITY.md "Stated limits of redaction" | nobody |
| K47 look-alike search in the finder | FIXED | TESTED | tests/test_redact_g3_port.py; pick batch; merged in d95a727 | nobody |
| K48 escapes, newer characters, hidden marks | STATED | none | G1 review (documented limits confirmed by reading) | nobody |
| K49 Chinese zero (U+3007) | PINNED | TESTED | tests/test_textnorm_mixed_script_micro.py::test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed; evidence/TW-order020.md (1 of 852 table entries) | nobody |
| K50 over-matching | OPEN | UNVERIFIED | G1 review M5 (reading); evidence runner `evrun` measuring (no evidence file yet) | core-c |
| K51 folding has no clock | OPEN | UNVERIFIED | G1 review M4 (reading) | core-c |
| K52 long Chinese or Japanese text | STATED | MEASURED | evidence/G1-fold.md "G1 fix round 1", M6 | nobody |
| K53 dashes, quotes, slashes (U+2215, U+2571, U+29F8) | PINNED | TESTED | tests/test_redact_g3_port.py::test_typography_an_em_dash_is_ordinary_the_value_beside_it_is_masked_in_the_line, ::test_typography_a_curly_quote_is_ordinary_the_value_inside_the_quotes_is_masked_in_the_line, ::test_typography_the_division_slash_u2215_withholds_a_line_with_a_lookalike_value, ::test_typography_the_box_drawing_diagonal_u2571_withholds_a_line_with_a_lookalike_value, ::test_typography_the_big_solidus_u29f8_withholds_a_line_with_a_lookalike_value; ORDER 014 item 9 | nobody |
| K54 Latin accent matching | PINNED | TESTED | tests/test_evidence_decomposed.py::test_known_difference_from_main_an_invisible_character_between_a_letter_and_its_accent_now_joins_them; ORDER 010 item 3 | nobody |
| K55 other scripts (grounding, runtime/evidence.py) | OPEN | UNVERIFIED | G1 review M7 (reading) | lead |
| K56 undo recombines | FIXED | TESTED | tests/test_undo_composes.py (9 of 10 failed before) | nobody |
| K57 boundary split | FIXED | TESTED | tests/test_injection_chunk_boundary.py (6 failed before) | nobody |
| K58 start-up order | FIXED | TESTED | tests/test_app_unicode_check_order.py::test_a_wrong_unicode_version_refuses_a_pilot_build_before_any_backend_is_made | nobody |
| K59 requested-by line | WAITING | UNVERIFIED | G2 review M3 (reading); requests/5-card-ids-redact-defang.md | core-b |
| K60 link check shares patterns | OPEN | UNVERIFIED | G2 review M6 (reading) | core-c |
| K61 glued e-mail | FIXED | TESTED | tests/test_text_parts_together.py::test_glued_email_regression_digit_or_underscore_behind_the_address; tests/test_p1d_a_paths.py::test_glued_addresses_are_masked_whole_in_one_pass; merged in d95a727 | nobody |
| K62 admin console | OPEN | NOT RUN | G2 review "not checked" | core-c |
| K63 install on 3.12 succeeds | OPEN | NOT RUN | pyproject.toml line 8 `requires-python = ">=3.12"` (lines 6-7: floor kept on purpose); SEC-wording-review-2 Major (Part 3) | core-b |

State items (not gaps):
- Gate not installed: tests/test_gate_install_callers.py holds 3 strict expected failures until core-b installs (evidence/TW-order020.md); tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered passes since aa7c5fa (25 passed, DECISIONS 07:40).
- The 50-connection test: tests/contracts/test_t1_reserve_cap.py::test_fifty_connections_against_a_cap_of_three_grant_exactly_three, plus 16 more cases (evidence/T1-reserve-cap.md), 49 passed twice on PostgreSQL 16.15, Python 3.13.18.
- Pick batch: 12,392 passed, 2 failed, 108 skipped, 7 xfailed in 135 files (-n 2, not perf); perf 64 passed; gate mutants 66 of 66; bandit clean. NOT RUN there: Python 3.12, PostgreSQL 17, the full suite, the full batch after the re-pin, textnorm mutants, p1d_a mutants.
- Mutants: tests/test_gate_mutants_picked_up.py found 24 stale search texts (evidence/TW-order020.md). On 2026-11-20 core-c's drafter counted 81 mutants in tests/gate_mutants.py, each search text exactly once in its file, in both HEAD and the working copy (a read-only count; no mutant run). The gate fix builder reports "81 of 81 good; problems: []".
- Gate tests behind part 2.2 to 2.4: T::test_pin_no_client_call_without_a_reservation; T::test_t1_pass_path_order_is_enforce_reserve_call_settle_audit; T::test_t12_a_spend_refusal_passes_unchanged_and_no_call_is_made[kill_switch]; T::test_pin_every_outcome_writes_exactly_one_audit_row; T::test_i9_the_module_has_no_logger_no_exception_text_and_no_module_state; T::test_t18_no_secret_in_any_audit_row_exception_or_log_record; T::test_t17_a_raising_audit_sink_never_loses_the_reply_or_the_settle; T::test_m2_settle_raising_after_a_paid_call_returns_the_reply_and_the_row_says_ok. These last ran in the gate builder's batch "1 failed, 2307 passed, 2 xfailed" (before the review-round-2 fixes).

### 4.3 Counts by status (63 gaps)
| status | count | gaps |
|---|---|---|
| PINNED | 15 | K1-K9, K22, K24, K43, K49, K53, K54 |
| STATED | 11 | K17, K19, K27, K28, K30, K33, K34, K35, K46, K48, K52 |
| WAITING (all on core-b) | 7 | K18, K20, K21, K23, K25, K42, K59 |
| OPEN, core-c acts | 10 | K12, K13, K38, K39, K40, K41, K50, K51, K60, K62 |
| OPEN, the lead or core-b acts | 9 | K14, K26, K29, K31, K32, K36, K37, K55 (lead); K63 (core-b) |
| FIXED | 7 | K44, K45, K47, K56, K57, K58, K61 |
| FIXED ON BRANCH | 4 | K10, K11, K15, K16 |
| total | 63 | 15 + 11 + 7 + 10 + 9 + 7 + 4 = 63 |

By evidence level: UNVERIFIED as the only basis: 13 (K12, K13, K18, K23, K26, K29, K32, K42, K50, K51, K55, K59, K60). An UNVERIFIED part beside a test: 3 (K20 example, K21 connectors, K45 other places). NOT RUN: 7 (K10, K11, K15, K16, K25, K62, K63). K14 is TESTED for the old rule and NOT RUN for the new one.

Changes from v2 (62 gaps): K63 added. K10, K11, K15, K16 OPEN to FIXED ON BRANCH. K47, K61 FIXED ON BRANCH to FIXED. K14 now "lead or core-b" group as before; K63 joins it.

Gaps named in part 1 (13 of 63): K34 (line 9), K37 and K36 (10, 11), K8 (12), K42 (13), K19 (14), K23 (15), K21 (16), K25 (17), K20 (18), K14 (19), K63 (20), K59 (line 2, "approval-message id fields"). Order rule: secrets reaching the AI service first, then money, then stopped work; within a group, wider exposure first.

### 4.4 Where two sources disagreed
1. Short-value exemptions: we used the later gate ticket (they do not apply to a secret of 4 or more characters), because it was checked against the sweep's code.
2. Settling after a plain connector error (settle 0, or not at all): we used ORDER 011 (not at all), because it replaced the earlier order.
3. A bind without a map (silent skip, or an error): we used ORDER 017 (an error; NO_MAP must be named), because it is newer.
4. The judge (no map, or the run's map): we used ORDER 017 item 1 (the run's map), because it is newest.
5. The tool-error double pass ("harmless", or a gap): we used the G7 review (a gap, K42), because the ticket's author withdrew "harmless".
6. "Two search rounds" (per text, or per call) and the tail size (5 or 7): we used the G7 review (per call, up to 7 calls per text; tail up to 7), because it traced the code.
7. Escaped look-alikes (any kind exempt, or only SECRET): we used the G7 fix evidence (only `‹SECRET_n›` with ASCII digits), because it is newer and tested.
8. The forged-marker leak (fixed, or leaking): v2 used the second gate review (leaking). We now use evidence/F-G0-1.md "Review round 2 fixes (final)" (reproduced, then fixed in work in progress), because it is newer. Batch NOT RUN.
9. The glued-digit e-mail (not fixed, or fixed): we used the integration evidence; it is now merged (d95a727), so FIXED.
10. G2 evidence (two failures, or fixed): we used its fix round (fixed, 7,879 passed), because it comes later in the same file.
11. The spacing-mark test (still red, or decided): we used the integration batch and the G text ticket (lead chose option a), because both are newer.
12. The G1 blockers (being fixed, or fixed): we used the G1 fix round (fixed, tests failed before). No independent re-review exists.
13. Whether folding is wired into the secret finder: v2 said only on an unpushed branch. Since d95a727 it is on cloud/core-c (K47 FIXED). Not on main.
14. A failed call's booking ("about an hour", or longer): we used core-b's interface README and T1's expiry case: expiry closes the row but the amount stays booked. Day and month both keep it (worked out).
15. Dash, quote and slash choice: we used ORDER 014 item 9 (accepted).
16. The third-round chain: we used ORDER 020 MJ-B (a capped repeat that refuses), because it is newer.
17. The overshoot example: the test holds three reservations of 1.00; one settles at 2.50: 1.00 + 1.00 + 2.50 = 4.50.
18. Base64 counts (41 of 41, or 52 of 142): both true: rows under 40 characters, and all rows, on the main code.
19. The 3.12 test job: the lead's 3.12 run of old branch P1a had one real failure; the G text ticket reads it as a test slip repaired in the folded code. That repair is UNVERIFIED on a real 3.12.
20. The deliberate code breaks (66 of 66, 24 stale, or 81 of 81): all true at different times. 66 of 66 ran in the pick worktree (gate code before the review-round-2 fixes). 24 went stale in the working copy. The gate builder reports 81 of 81 on its edited code; core-c's drafter counted all 81 search texts present.
21. The planted-word refusal scope: ORDER 017 item 6 (refuse on any marker word, tool name or call id) versus the builder's narrower rule (secret kind, 4+ characters, tool name or call id only). We describe the narrower rule, as it is the code in the WIP commits; the lead decides (decision 1).
22. The month cap (round-2 reviewer: not shown to be covered) versus evidence/T1-reserve-cap.md (cap 3.00 for the day and the month; a month cap reached over two days): we used T1, because it lists the case.
23. "If writing the row or settling fails, the reply is still returned" (round-2 reviewer: no test named) versus the gate tests t17 and m2 (4.2 state items): we used the tests.
24. K12 (dz2-M2 reading: the tail leaks) versus the builder's run (`<SECRET_1><SECRET_2>`, no leak): we keep it OPEN and UNVERIFIED until a fresh review.
25. K32 (v2: runtime and reset logins) versus E7 item 5 and B-grants-rework finding 5 (the reset login; the runtime's audit right is its normal duty): we used E7.
26. The producers registry test (v2: red on purpose) versus DECISIONS 07:40 (closed by aa7c5fa): we used DECISIONS, because it is newer.
27. "Verified" merge (d95a727 message) versus the PICK evidence: the batch ran on wip-pick before the merge and before the re-pin; the merge's first parent is unverified gate work. We say "tested before the merge; the merge result was not re-tested".
28. Decision 3's "three questions" (v2) has no source in the G4 ticket: dropped. The "blocking problems" come from tickets/G4-review-1.md (8 Blockers, 6 distinct).

### 4.5 Requests to core-b (files in handover/core-c/requests)
1. 1-producers.patch: register the gate as a model caller (applied by core-c as aa7c5fa; decision 7).
2. 2-refused-before-response.md: the "refused before any answer" mark (K20).
3. 3-bind-mapping-required.md: required map, `GateRefused`, empty cost, catch sites, install checks (K8, K18, K21).
4. 4-error-reason-run-map.md: tool-error text with the run map (K42).
5. 5-card-ids-redact-defang.md: id fields on approval messages (K59).
Lead's orders to core-b without a request file: sum the cost of all attempts (ORDER 017 item 3, K23); the worst-case formula (ORDER 016c item 13, K25); an operator release for expired reservations (ORDER 017 item 4); the install test with core-b (ORDER 020 MJ-C). K63 has no request yet: core-c writes one if the lead agrees.

### 4.6 What is still moving at the time of writing
- Gate fix round for review round 2 (`gfix2`): code in WIP commits; batch NOT RUN; fresh review not started. K10, K11, K15, K16 depend on it; K12 and K13 stay OPEN.
- G7 fix round 2 (`g7f2`, ORDER 020 MJ-B): capped repeat in guard/redact.py, uncommitted in the working copy; progress note only (evidence/G7-1.md); budget timing, defaults.py comments, duplicate TEXTNORM_PINNED_PYTHON and the full batch still to do. K39, K40, K41 depend on it.
- G4 plan version 2 (`g4v2`): being drafted; decision 3.
- Fold false-hit measurement (`evrun`): running; no evidence file yet (K50).
- Lead verdicts pending: DECISIONS 07:35 (empty map contest, decision 6) and 07:40 (producers edit, decision 7); decision 1 (framing rule).

### 4.7 INTERNAL: change log of review round 2 (does not ship)

Findings from tickets/SEC-wording-review-2.md, in its order. Round 1 items (tickets/SEC-wording-review-1.md) were re-checked and are not regressed: verdict first, glossary first, one status per gap, three-line gaps, codes in the appendix, made-up values note, no self-certifying line.

| finding | resolved where / CONTESTED why |
|---|---|
| B1 absolutes vs gaps (money) | Part 1 line 23 and 2.2 reworded to what the T1 test shows; K24 and K26 named beside it. CONTESTED in part: the month cap IS covered by a T1 case (4.4 item 22). |
| B2 banner vs body | Heading "What the tests show and what is still open"; "What holds" renamed "Shown by tests" everywhere; banner as proposed, adapted: "on the unpushed branch" replaced by "work in progress", because the code is now on the shared branch (d95a727 and WIP commits). One secret finder defined (part 0; Part 1 line 7). |
| B3 unqualified protection claims | 2.1-2.4 and Part 1 lines 21-24 reworded with the K9, K19, K28, K30, K16 exceptions. CONTESTED in part: "reply still returned" is not UNVERIFIED: tests t17 and m2 exist (4.2 state items; 4.4 item 23). |
| B4 summary does not stand alone | Proposed first lines used (adapted counts); NOT RUN at line 4; owner action and dated default (2026-11-23 12:00 UTC, proposed by core-c, confirmed by the lead) at lines 5-6; line 8 says install is not enough; K19, K23, K25, K21/K23/K42/K59, 3.12 trap added; no gap listed twice; criterion stated (line 3; 4.3). Count is 13 of 63, not 9 of 62, because the added items and K63 raise it. |
| M K2 example and rule | Example labelled "known identifier"; rule as proposed; K3 example changed to `qrs789`. |
| M decision 5 gaps and count | Five rights, K26 (two), K29 (two), K32 (one), described without K-numbers in 1a. |
| M decision 4 wording | "lets more / fewer names pass"; grounding check defined. |
| M decision 6 reasoning | Rewritten: no absolute; names the missed-secret case; default is the lead's order, the stricter one; core-c's request "favours continuing over strictness". |
| M decision 3 source and actor | Source: 6 distinct blocking problems (4.4 item 28); actors: core-c rewrites, lead drafts the client note, owner sends it. |
| M decision 1 wording | Rewritten for the narrower rule now built; "keep stopping" and "any document" removed; "honest names such as web" dropped, because tests r2_m1 and r2_m4 now cover it (batch NOT RUN). |
| M decisions passive; undefined cell words | Actors named in every default; evidence check, sibling file, Slack, marker line, call number, route defined in part 0 or replaced. |
| M status words vs glossary | FIXED and FIXED ON BRANCH redefined (main line, no re-review, batch). CONTESTED in part: the proposed "not in the shared branch" no longer fits the facts; FIXED ON BRANCH now means "WIP commit on the shared branch, batch NOT RUN". Separate evidence column added; WAITING allows "request or order"; STATED and PINNED gaps name no actor (K8, K17, K24, K27 reworded); K62 OPEN + NOT RUN; strict expected failures defined under PINNED, and K39/K40 kept OPEN as defects with that evidence; K53 now on the shared branch, so plain PINNED. |
| M Part 3 | The proposed paragraph used word for word; Unicode, secrets vault explained; "test job", "required check", "folded check name" removed; install trap is K63 (OPEN, core-b). CONTESTED in part: the error name UnidataMismatch stays in Part 3, because the reviewer's own text uses it and an operator must recognise it on screen. |
| M NOT RUN loose | One list (Part 1 line 4; 2.9) in the proposed wording; 238 of 240 marked NOT RUN. |
| M "caught all 66" stale | Proposed sentence used, then updated: 81 of 81 reported by the builder; drafter's count of matching search texts (2.1; 4.4 item 20). |
| M cost fields | K21 (empty: booked free) and K22 (unreadable: worst case stays) each named once; "may" removed; K20 now says day and month. |
| M wrong reference (within K36) | Now "within K40"; K35-K37 say "main line". |
| M codes outside appendix | Refusal words, marker syntax, call_id, CI, IBAN, Ctrl-C, NaN, Slack, base64, Unicode removed or explained; K-numbers out of Part 1; Part 5 dropped (this table is internal); Part 2 has a "words used here" box. K-numbers stay in Part 2, explained in part 0. |
| M words with several meanings | Part 0 fixes one meaning each: run, check (named checks), known gap (no "limit"), store vs secrets vault, run map, kind vs type of action, caller (place), stop switch vs stop record, branch words, reserve/booked, secret finder (one), guardrail call, operator, planted, known value, withheld vs held back, route, role label, answer format, price table, approved prompt list, replay, who asked. |
| M headings and garbled sentences | K13, K41 "Not limited: ..."; K24 "The cap can be passed once"; K38 "goes out unmasked"; K39 attacker via "planted text"; K12 explained with held back; 2.7 "each path found so far", batch caveat, K59; "Measured slowdown"; "As of" in each part. |
| M summary overall | One finder (line 7); 2.5 condition stated; self-grading flagged (part 0 note); "Reviewers only read"; lead = software. |
| Nits | v3, DRAFT; "red" replaced; time stated; one list of marks; Unicode names in words (K49, K53); operators defined; later Python names core-c; K60 marked UNVERIFIED with core-c's action; K16 "may" removed. |

Contested in all: 4 findings in part (B1 month cap, B3 "no test named", status definition "not in the shared branch", Part 3 error name). Each with its reason above.
