# Security wording v4: what the tests show and what is still open

DRAFT, version 4, written by core-c's drafter on 2026-11-20. It replaces SECURITY-README-v3.md and answers review round 3 (tickets/SEC-wording-review-3.md).
Who reads what: part 0 and part 1 are for the owner only. Part 2 ships as SECURITY.md. Part 3 ships as README.md (section "Python version"). Part 4 is internal and does not ship.
Strip step before shipping (the lead or whoever copies the text): (1) copy part 2, from its heading to the line before part 3, into SECURITY.md; (2) copy part 3, from its heading to the line before part 4, into README.md; (3) in both copies delete every line whose text, after any list dash and spaces, starts with `[INTERNAL]`; (4) delete nothing else. After step 3, parts 2 and 3 name no project, team code or session: they say "the owner", "the connector and store team" and "the text and masking team".
This draft changes no other file.

---

## 0. Plain glossary (read this first)

As of 2026-11-20 07:52 UTC (repository head 11935aa).

### How to read the marks (one list)

Evidence words (how we know). Every claim carries one of these:

- **TESTED**: a named test ran and passed in a recorded batch of tests (a batch whose result line is in an evidence file).
- **MEASURED**: a recorded run measured the number given.
- **UNVERIFIED**: the only basis is someone reading the code or the text. Nothing was run to show it.
- **NOT REPRODUCED**: a reviewer reported a fault from reading; a builder then ran the reported case and did not see the fault. No fresh reviewer has checked the builder's run.
- **NOT RUN**: the check was not run at all, or no recorded result exists. Nothing is claimed about its result.
- **NONE**: no test, run or reading is named. The gap is written down from a plan, an order or the published SECURITY.md only.

Status words (one per known gap):

- **FIXED**: changed, and a test fails without the change. The change is on the shared branch. A recorded batch that holds that test passed, on the builder's copy of the code before it was saved; the code as saved was not re-tested as a whole. It is not on the product's main line. No independent reviewer has passed it.
- **FIXED ON BRANCH**: changed, and the builder showed a test fails without the change. The change is saved on the shared branch, but no recorded batch covers it. No independent reviewer has passed it.
- **PINNED**: not fixed, on purpose. A named test fails if the behaviour changes. This includes a "strict expected failure": a test that records the gap and fails once the gap closes; the team that closes the gap then removes the mark.
- **STATED**: accepted and written down (in a plan, an order, a ticket, an evidence file or the published SECURITY.md), with no test. The appendix (4.2) names the source and its date. Nobody is asked to act.
- **WAITING**: another team must act, and a written request or a written order exists.
- **OPEN**: nobody has fixed or decided it yet. The line names who must act.

Every example value in this file is made up. None is a real secret.

### People and teams

- **The owner**: the person who owns Hadavin, pays for the work and has the final say.
- **The lead**: the coordinating session (software, not a person) on the owner's laptop. It writes the orders and decides open questions. The owner can overrule it. The lead is named in parts 0, 1 and 4 only.
- **The connector and store team** (internal code: core-b): the build team that owns the model connectors, the store, the agent loop and the approval-message code. It must install the gate.
- **The text and masking team** (internal code: core-c): the build team that built the gate, the secret finder changes and text folding. It wrote this file.
- **Builder**: a worker of the text and masking team that writes code and runs the tests. **Reviewer**: an independent checker. Reviewers only read; the builders ran the tests.
- **Operator**: the person who installs and runs the kit for a client.
- Note: the text and masking team wrote this file. It must act on 15 OPEN gaps, and it must still run a recorded batch for the 4 FIXED ON BRANCH gaps (4.3). Independent reviewers read version 3. Nobody outside the team has checked these statuses against the code.

### Product words

- **The kit**: this software package (the Hadavin SDK) that client projects are built on.
- **Stages**: there are only three: demo (shows the product with made-up data), pilot (a first, limited use with a real client), prod (normal live use).
- **Model**: the outside AI service that reads text and answers. A **model call** is one request to it.
- **Guardrail call**: a separate request to the cloud vendor's safety service. It is not a model call.
- **Route**: which AI service and which model a call goes to.
- **Model connector**: the code that talks to one AI service and reports the cost of each call.
- **Run** (noun): one job of one agent, from start to finish. The **agent loop** is the code that drives a run step by step. (The mark NOT RUN and the verb "ran" are about tests only.)
- **Tool**: an action an agent may use, such as a search. A **tool result** is the text a tool returns. Each tool call gets a **call number**. **Tool list**: the list of tools, with names and descriptions, sent with a model call.
- **Calling code**: the program code that hands a call to the gate. (A "tool" is never the calling code.)
- **Test and replay command lines**: two programs for staff. One runs saved test cases; the other re-plays a stored run for checking.
- **Planted text**: text an attacker put into a document or tool result so that the agent reads it.
- **Sensitive value**: a secret (password, key, token) or an identifier (e-mail address, host name, account number).
- **Known value**: a sensitive value already in the run map.
- **Mask**: replace a sensitive value with its placeholder. **Placeholder**: a fixed text such as `<SECRET_1>` that the model sees in place of the value. (This file uses only these two words for this.)
- **Run map**: one table per run, kept in memory, that records which real value each placeholder stands for. **Restore**: put the real value back in place of a placeholder, for a tool that needs it.
- **Secret finder**: the code that searches text for sensitive values by their shape and masks them. There is one secret finder. It runs where text enters a run (tool results, documents, approval messages). Only it adds to the run map.
- **Search round**: one pass of the secret finder's patterns over the text, followed by one masking of every copy of the known values. **One call of the secret finder** runs up to 5 search rounds.
- **Kind**: the type the secret finder gives each value it finds. Secret kinds: passwords, keys, tokens. Identifier kinds: e-mail, host name, IP address and the like.
- **Withheld**: the secret finder hides a whole line it cannot mask in place, and shows a fixed note.
- **Glued**: written directly against another character, with no space between.
- **Fail closed**: when in doubt, refuse the text or the call rather than let it through.
- **Text folding**: turning look-alike letters (full-width letters, Cyrillic letters that look Latin), invisible characters and accents into one plain spelling before searching.
- **Unicode**: the world standard list of characters. Each Python version carries one edition of it.
- **base64**: a common way of writing any data as letters and digits.
- **The gate**: one wrapper meant to sit in front of every model call. It masks known values, reserves money, makes the call, settles and writes an audit row. It searches for no new values.
- **Installed**: placed at every point in the code that calls a model. The gate is NOT installed yet.
- **Held back**: a known value at a placeholder's edge (it starts with `>` or ends with `<`). The gate masks it last, so the placeholder text stays whole. **Safety net**: the gate's last check, which refuses the call if a held-back secret is still readable.
- **Framing marker**: the fixed line the agent loop puts around each tool result, so the model sees where tool output starts. It holds fixed words, the call number and the tool's name.
- **Planted-instruction check**: the check that looks for planted orders such as "ignore previous instructions". **Guard failure**: its report that it could not finish.
- **Grounding check**: the check that a name an agent proposes to act on appears in a tool result it cites.
- **Judge**: a model call that rates a text (used by the planted-instruction check and the approval code). It is a model call and must go through the gate too.
- **Prompt registry**: the fixed list of system prompts (standing instructions) that ship with the kit.
- **Slack**: the chat service where approval messages are posted.
- **Admin page**: the staff web page that shows stored approval summaries.

### Money words

All amounts are in US dollars (USD).

- **The store**: the database that records spending, reservations, the stop switch and the audit record. (The place secrets are kept is called the **secrets vault**.)
- **Cap**: the most money one agent may spend in a day and in a month.
- **Worst case**: the most a model call could cost. The connector and store team's code must compute it.
- **Reserve**: before a call, count its worst case against the cap. **Settle**: after the call, replace the worst case with the real cost. **Booked**: the amount counted against the cap at any moment.
- **Empty cost field**: a reply whose cost was never filled in. It reads as 0.00 USD. **Unreadable cost**: a cost that is absent, negative or not a number.
- **Price table**: the list of prices per AI service used to work out the worst case.
- **Stop switch**: a flag in the store. While it is on, the store is meant to refuse every new reservation. A **stop record** says who turned it on.
- **Database login**: a named account the software uses to reach the store (runtime, purge, reset). Each has its own rights.

### Record and code words

- **Audit row**: one line in the permanent record of what happened. It holds short codes, not message text.
- **Refusal word**: the exact short word the gate or store prints when it refuses. The words are listed in the appendix (4.1).
- **The shared branch**: the text and masking team's pushed line of changes, from which the lead takes code. **The product's main line**: what clients get. Nothing of this work is on the main line.
- **Work-in-progress commit**: changes saved to the shared branch before their tests ran.
- **Test**: a small program that checks one behaviour and fails when it changes. **Batch**: one recorded run of many tests.
- **Deliberate code break**: a planted fault used to prove a test can fail.
- **Known gap**: a weakness we know about, or a gap fixed in this work. Each has a number K1 to K69, used in parts 2 and 4. K64 to K69 are new in this version. Part 1 uses no numbers.
- **Item**: one numbered line of part 1.

---

## 1. Owner summary

As of 2026-11-20 07:52 UTC.

### What to know first

1. **Short answer: the gate is written and tested on its own. It is not installed, so no agent in use goes through it. Do not promise a client any gate protection yet.**
2. The connector and store team must write the worst-case formula, add the "refused before any answer" mark and install the gate. It also has seven other open items: empty cost fields, retried calls, tool-error text, approval-message id fields, the run's status after a refusal, a start-up check that system prompts come only from the prompt registry, and installs on Python 3.12. The last one has no written request yet.
3. The text and masking team must finish two fix rounds that are running now (one for the gate, one for the secret finder), run their test batches, and get a fresh review.
4. This summary names 24 of 69 known gaps. They are ordered by what they put at risk: first secrets reaching the AI service, then money, then stopped work. Within a group, wider exposure comes first, and a tested or measured gap comes before an UNVERIFIED one.
5. NOT RUN on this work's code: the full test suite; Python 3.12; database version 17; any live call to an AI service; any end-to-end stop; 238 of the 240 deliberate code breaks for text folding; a recorded batch for the gate's second-review fixes; the merge result as a whole; the gate's third fix round and the secret finder's third fix round (both running).
6. **Your action (the owner):** read the seven decisions in 1a. Tell the lead by 2026-11-23 12:00 UTC which defaults you overrule, and whether to send the client note of decision 3.
7. If the owner has not answered by then, the lead applies the default in the last column of 1a. The text and masking team proposed this date. As of 07:52 UTC the lead has not confirmed it in writing.
8. Today an agent in use is protected only by the secret finder as it is on the product's main line, without this work's changes.
9. Installing the gate and passing a fresh review will not be enough. The gaps below stay until each one is closed.

### Secrets that can reach the AI service (worst first)

10. A secret in a shape the secret finder does not know goes out as written, after install too.
11. Short base64 text is not masked. Measured on the main line: 41 of 41 such test lines leaked.
12. Host names without a "host" label are not masked. Measured on the main line: 28 of 44 test lines leaked. Decision 3 covers this item and item 11.
13. The gate never masks the system prompt (the standing instructions) or the tool descriptions.
14. The guardrail call goes around the gate. It is neither masked nor counted against the cap. The lead's frozen plan of 2026-11-20 accepts this. Tell the lead if you want it changed.
15. Also leaking today, each in one narrow shape (so they rank below items 10 to 14): a bare number with no label (measured on the main line: 24 of 43 test lines not masked); a secret that holds a space, `;`, `,` or `&` (masked only up to that character; written in the published SECURITY.md); an IP address, phone number, international bank account number or unique id with a letter or `_x` glued behind it (measured).
16. A secret first seen in a tool's error message is not masked in later text. This is UNVERIFIED: read from the code, not run. It waits on the connector and store team.
17. Reviewers found three more leak paths by reading (UNVERIFIED). Their fixes are running (NOT RUN). The gate's safety net checks only held-back values. A known value inside a tool's name is masked in one place but not in the tool list. The hand-over list for the install misses the judge's call points.

### Money (worst first)

18. When a call is retried, only the last attempt's cost is counted (UNVERIFIED). Earlier billed attempts are lost, so spending is understated.
19. Nobody has written the worst-case formula yet. Until the connector and store team writes it, the cap has nothing real to reserve.
20. Booked money can pass the cap, on purpose: a call that costs more than its worst case is booked in full. Tested: three reservations of 1.00 USD against a cap of 3.00 USD; one settles at 2.50 USD; 4.50 USD is booked.
21. The database does not stop the software's own login from lowering a reservation or deleting an open one (UNVERIFIED). Decision 5 covers it.
22. That a model connector leaves the cost field empty is UNVERIFIED. If one does, the call is booked as free. The gate's side of this is tested.
23. A failed call stays booked for the rest of the day and month. With a cap of 3.00 USD and a worst case of 1.00 USD, three failed calls stop an agent (worked out, not run).

### Stopped work and set-up

24. Planted text can make a run's later tool-using calls refuse, if it plants a secret equal to a tool's name. A reviewer read that this still happens under the narrower rule (UNVERIFIED). Decision 1 covers it.
25. Planted text with more than 256 values at a placeholder's edge makes every later call of that run refuse (UNVERIFIED, read by a reviewer).
26. A pilot or prod install on Python 3.12 succeeds, and then the program refuses to start. This is the design; it was NOT RUN on 3.12.

### Shown by tests (each in the teams' own tests, on the code alone)

27. In the gate's tests, known values are masked before a call, in message text and documents only. They are not masked when the calling code states "no map". Only the test and replay command lines may state "no map".
28. In the gate's tests a refused reservation means no call. That the store refuses while the stop switch is on is UNVERIFIED, and no stop of a live run was tested. This does not cover a call already in flight, the test and replay command lines, or the guardrail call.
29. In two test runs on database version 16, 50 separate database connections, started together, asked for reservations against a cap of 3.00 USD with a worst case of 1.00 USD each. 3.00 USD was reserved and 47 requests were refused. Booked money can still pass the cap (items 20 and 21).
30. In the gate's tests, its code holds no message or error text, and no audit row in those tests held a secret.
31. In the secret finder's tests, a chain of planted values that needs a third search round is now masked (a batch of 9,681 tests passed, 0 failed). A reviewer read a case the repeat may skip (UNVERIFIED). Its fix is NOT RUN.

### 1a. The seven decisions (the lead takes them; the owner can overrule by 2026-11-23 12:00 UTC)

| # | Question | What each answer means | Default if no answer: who does what, by when, and why |
|---|---|---|---|
| 1 | Planted text can make a known value equal part of a framing marker. When should the gate refuse the call? | Narrower rule (saved on the shared branch, its batch NOT RUN): refuse only when a known secret of 4 or more characters equals a tool's name or a call number. Wider rule (the lead's earlier order): also refuse when any known value equals a fixed marker word. A reviewer proposes a third way: never store a tool's name as a secret when the secret finder adds it (UNVERIFIED that this closes it; the connector and store team's code). | The narrower rule. The lead confirms it in DECISIONS.md after the gate's third fix round passes its batch; until then the code holds the narrower rule. Why: under both rules the marker's fixed words are kept exact (read from the code; the batch for this is NOT RUN), so the wider rule's extra refusals do not appear to protect more text, and they stop more runs. Both rules still let a planted secret equal to a tool's name stop a run (item 24). |
| 2 | Should each audit row also say whether anything was masked, and which route was used? | Without it, nobody can tell from the record whether masking happened. The row now says only how the run map was used (a map, an empty map, no map). | Add a "masked: yes or no" field and the route. No text. The text and masking team builds it in the gate's next fix round after the lead's verdict. No date is set. |
| 3 | Build the planned host-name and base64 change, or keep both as known gaps for now? | Keeping them means such values reach the AI service (items 11, 12). Two plan reviewers found 6 distinct blocking problems in the first plan. The text and masking team wrote version 2 of the plan at 07:46 UTC; its plan review has not reported. | Keep both as known gaps until a plan review is clean, then the text and masking team builds. The lead drafts a short client note on both gaps by 2026-11-23 12:00 UTC. The owner decides whether to send it (item 6). |
| 4 | Accept that the grounding check now counts a name as present in more cases in Korean, Japanese and Indian scripts? | This happens when an invisible character splits the name. Accepting lets more proposed names pass the check, with no tests for those scripts. | Go back to the older rule for those scripts (it lets fewer names pass) until tests exist. The text and masking team makes the change in its next text-folding round. No date is set. |
| 5 | Tighten five wide database rights, or accept them in writing? | Runtime login: can rewrite a reserved amount, and can sign a stop record with any name. Purge login: can delete an open reservation. Reset login: can change any stop-switch row, and can add any audit row. Accepting leaves the cap and the stop record resting on code alone. | Tighten them: narrower rights, or one fixed database function per action. The lead writes the order; the connector and store team changes its database rights in its next store change, before any pilot uses the store. |
| 6 | Should the gate refuse a call whose run map is empty, as the lead ordered, or accept it and mark the audit row, as the text and masking team asks? | Refusing stops each run whose first document held no value the secret finder found. Accepting lets it go on. Either way the gate masks nothing in that call, and a secret the finder missed goes out in both cases. A reviewer also read that the gate does not check that the map is the run's own map (UNVERIFIED). | Refuse, as the lead ordered: it is the stricter choice and already written. The text and masking team's request favours letting runs continue over strictness. The lead writes its verdict in DECISIONS.md; no date is set. |
| 7 | Accept the text and masking team's changes to two of the connector and store team's files, or have that team redo them? | The files: the Slack approval-message file, and the list of code that calls a model (it now names the gate). Two teams editing one file can collide. | Accept both. The lead tells the connector and store team in its next order. Either change can be undone with one commit. |

---

## 2. For SECURITY.md: "What the tests show and what is still open"

As of 2026-11-20 07:52 UTC.

> **These items describe what tests showed on the gate, the secret finder and the store, each run on its own. UNVERIFIED means someone read the code and nothing was run. "Work in progress" means saved to the shared branch, but no recorded test batch covers it. The shared branch is not the product's main line. None of this describes an agent in use going through the gate.**

Words used here (this part ships alone):

- The gate: the wrapper meant to sit in front of each model call. The run map: the table of placeholders for one run. A placeholder: the fixed text, such as `<SECRET_1>`, that the model sees in place of a value. Mask: replace a value with its placeholder. Booked: counted against the money cap. The store: the database that records spending. All amounts are in US dollars (USD).
- The secret finder: the code that searches new text for sensitive values and masks them. A search round: one pass of its patterns, then one masking of every copy of the values already known.
- The connector and store team: the team that owns the model connectors, the store and the agent loop; it must install the gate. The text and masking team: the team that built the gate and the secret finder changes. The owner: the person who owns Hadavin and has the final say.
- The shared branch: the text and masking team's pushed changes. The main line: what clients get.
- Kn: the number of a known gap in this list.
- Evidence words: TESTED (a named test passed in a recorded batch), MEASURED (a recorded run measured the number), UNVERIFIED (only read), NOT REPRODUCED (reported from reading; a builder ran the case and did not see the fault), NOT RUN (not run, or no recorded result), NONE (written down from a plan or an order only).
- Status words: FIXED (changed; a recorded batch with its test passed; not on the main line), FIXED ON BRANCH (changed and saved; no recorded batch), PINNED (kept on purpose; a test fails if it changes), STATED (accepted in writing; no test), WAITING (another team must act; a written request or order exists), OPEN (not fixed or decided; the line names who acts).

### 2.0 State of the work

- The gate is built and tested on its own. The connector and store team has not installed it at any point that calls a model. WAITING on the connector and store team.
- Three tests are marked as strict expected failures until the gate is installed. Once the connector and store team installs it, these tests pass, the strict mark turns that pass into a batch failure, and the connector and store team removes the three marks.
- The list of code that calls a model now names the gate. The text and masking team made this two-line change in a file of the connector and store team.
- The connector and store team will not install the gate before the model connectors can say "refused before any answer" (a written order).
- Merged into the shared branch at 07:28 UTC: the approval-message fixes, the glued e-mail fix, the secret finder's look-alike search and its second search round.
- Before that merge, a builder ran a batch of 135 test files on that code: 12,392 passed, 2 failed, 108 skipped, 7 expected failures.
- The first failure was a text folding test whose expected result no longer fitted the joined code. The builder changed the expected result, and the test then passed when run alone.
- The second failure was the test that lists every piece of code that calls a model: the list did not name the gate yet. The two-line change above (at 07:36 UTC) added it, and that test's file then passed (25 passed). The batch was not run again after either change.
- The merge result as a whole was not re-tested (NOT RUN). A later batch of the test files that name the secret finder passed (9,681 passed, 0 failed); the record does not say which saved version it ran on (UNVERIFIED).
- The gate's fixes for its second independent review (forged marker, tool line, audit marks, interrupts, part of the time limit) are saved on the shared branch in commits marked "work in progress, not verified". A commit message reports 302 passed tests and 81 of 81 deliberate code breaks caught. The record holds the 81 of 81 run, but no test batch: the batch is NOT RUN.
- A third review of the gate (two reviewers, reading only) found 9 faults it rates as major and none it rates as blocking. Its fix round is running: NOT RUN.
- The secret finder's capped repeat (K39, K40) is saved on the shared branch. Its batch of the test files that name the secret finder passed: 9,681 passed, 0 failed. A second review of it (two reviewers, reading only) found 1 blocking fault (a code comment that says the opposite of the code) and 11 major ones. Its third fix round is running: NOT RUN.
- One later change, a time limit inside the secret finder's masking step, is saved as work in progress with its own test. No batch covers it (NOT RUN).

### 2.1 Masking before a model call (the gate)

Shown by tests:

- In the gate's tests, it replaces each known value with its placeholder before a call. This covers message text and documents only. K8 lists what it skips.
- The gate searches for no new values. The secret finder does that (K1).
- If masking fails, the gate makes no call and reserves no money. Causes: text too long, content that is not text, out of time, or text still changing after 4 maskings. The refusal carries a refusal word and no text.
- If no known value is present, the text goes out unchanged.
- In tests, the gate does not change the calling code's messages, documents or run map.
- The calling code must name a run map or state "no map". Leaving it out is an error. Only the test and replay command lines may state "no map" (K9).
- Deliberate code breaks: a builder ran 66 on the gate before its second-review fixes. The tests caught all 66.
- Later edits left 24 of those 66 matching no code. The builder then updated those 24 and added 15 new ones, 81 in all. The recorded run reports that tests caught all 81 on the edited code. No second run has confirmed it.

Known gaps and fixed findings:

- **K1. Not protected:** a secret the secret finder never found.
  - Example: a raw `hunter2zz` that no shape matched goes out as written.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody; the secret finder is the control.
- **K2. Not masked, even when known:** any value under 3 characters. Also, for every identifier and for a secret of exactly 3 characters: an all-digit value under 6 characters, a common word (`admin`, `test`), and any copy that a letter or digit touches.
  - Example: the known identifier `abc123` (an account number, not a secret) stays readable inside `xabc1234`, because a letter touches it.
  - Rule: a secret of 4 or more characters is masked wherever its exact text appears, even when it is all digits or a common word, except as K3 to K7 describe.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K3. Not masked by the gate:** a copy spelled differently from the run map (percent codes, web character codes, look-alike letters, hidden characters, the control codes terminals use for colours).
  - Example: known `qrs789`, text `qrs&#55;89` (a web code for the digit 7) goes out as written.
  - Status: PINNED. Evidence: TESTED (the gate does not replace these spellings). Who acts: nobody on the gate. Whether the secret finder's text folding catches each such copy is UNVERIFIED. A reviewer also read that the gate does replace some other spellings of known values written in non-Latin letters (UNVERIFIED); the gate's fix round (NOT RUN) either tests this or writes it down.
- **K4. Not masked:** the same value in other capital or small letters.
  - Example: known `db01.acme.example`, text `DB01.ACME.EXAMPLE`.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K5. Not masked whole:** two known values that overlap. Masking the first takes part of the second, so the rest of the second stays.
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
  - Status: PINNED. Evidence: TESTED. Who acts: nobody on the gate.
  - Related request (WAITING on the connector and store team): a start-up check that system prompts come only from the prompt registry, the fixed list of system prompts that ship with the kit.
- **K9. Not masked:** anything, when the calling code states "no map".
  - Example: a replay of an old run sends its text as stored.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K10. Fixed in work in progress:** the audit row said "map in use" when the map was empty, or when the calling code had supplied its own masking function (allowed for tests). The row now says which.
  - Example: a run with an empty map now writes "map empty", not the same row as one with 50 values.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (no recorded batch). Who acts: the text and masking team (batch, then fresh review).
- **K11. Fixed in work in progress:** a known secret inside a forged tool-result marker went out unmasked. Now the gate keeps only the marker's fixed words and masks the rest.
  - Example: a document holds a fake marker line whose call number contains the known `S3cr3tPw`; before this fix, `S3cr3tPw` went out.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (no recorded batch); the builder reproduced the leak first; a third-round reviewer read the fix as closed (UNVERIFIED). Who acts: the text and masking team (batch).
- **K12. Reported, not reproduced:** a secret at a held-back value's edge may leak its tail.
  - Example: known `S3cr3t` and `>abcdef`. A reviewer read that `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`. A builder ran it and got `<SECRET_1><SECRET_2>` (no leak).
  - Status: OPEN. Evidence: NOT REPRODUCED. Who acts: the text and masking team (a fresh reviewer checks the builder's run; a safety net that refuses the call is saved in work in progress).
- **K13. Not limited:** the total time the gate spends on one model call. One time and size budget per call now exists, but the final masking step inside it has no time limit.
  - Example: before the change there was no limit per call: 100 messages × 6 seconds each = 600 seconds was possible (worked out, not run). After the change, measured: 100 messages against a run map of 2,000 entries took 0.018 seconds.
  - Status: OPEN. Evidence: MEASURED (that one case). That the final masking step has no time limit is UNVERIFIED (read from the code): the secret finder's masking step now accepts a time limit, but the gate does not pass one, and the two use different clocks. A reviewer estimates about 128 million steps for one hostile text of 256 KB (an estimate, UNVERIFIED). Who acts: the text and masking team (fix round running, NOT RUN).
- **K14. Not protected:** a run's later tool-using calls. A planted secret that equals a tool's name or a call number makes each of them refuse.
  - Example: a tool result contains `password=search_web`, where `search_web` is a tool's name; later calls in that run refuse.
  - Status: OPEN. Evidence: TESTED (the earlier, wider rule); NOT RUN (the narrower rule, no recorded batch); a reviewer read that the narrower rule still refuses in this example (UNVERIFIED). Who acts: the owner decides which rule.
  - [INTERNAL] Decision 1 in part 1a.
- **K15. Fixed in work in progress:** planted text could rewrite part of a tool's name in the line where the model asked for that tool.
  - Example: a document planted `password=logs`; the model then saw two names for one tool call.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (no recorded batch). Who acts: the text and masking team. See K66 for the tool list.
- **K16. Fixed in work in progress:** someone stopping the program by hand while the gate worked out the worst case or asked for a reservation left no audit row. Now a row is written.
  - Example: the program is stopped by hand while the gate waits for its reservation. The record now holds a row that says "reservation interrupted". The reservation stays booked, on purpose: this over-counts spending and never under-counts it.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (no recorded batch). A reviewer read two more places where a stop by hand still leaves no row (UNVERIFIED). Who acts: the text and masking team (fix round running, NOT RUN).
- **K17. Not safe:** two threads writing one run map at the same time can give one placeholder number to two values.
  - Example: two tools finish together and both values become `<SECRET_3>`.
  - Status: OPEN. Evidence: NONE. Who acts: the text and masking team adds the condition "one writer per run map" to its install request to the connector and store team.
- **K64. Not protected:** a run's later calls, when planted text holds more than 256 values at a placeholder's edge (such as `password=>aaaa1`). The gate then refuses every later call of that run, because the run map only grows.
  - Example: one planted document with 257 such lines stops the run.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team (fix round running, NOT RUN).
- **K65. Not refused:** a known secret left readable outside the held-back case. The safety net checks held-back values only. The audit row still says the map was used.
  - Example: a known secret `AKIAEXAMPLE123` written as `<AKIAEXAMPLE123_1>` (see K7), or written across a fixed marker word.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team (fix round running, NOT RUN).
- **K66. Not consistent:** a known value inside a tool's name. The gate masks it in the line where the model asked for the tool, but the tool list goes out as written.
  - Example: the run map holds `<TENANT_1>` for `billing`. The model sees `tool get_<TENANT_1>_info` and may call a tool that does not exist. A secret that is only part of a tool's name, such as `logs` in `read_logs`, stays readable in the tool list.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team (fix round running, NOT RUN).
- **K67. Not complete:** the install hand-over list and the install test. They miss the judge's call points, so after install a judge call could still go around the gate.
  - Example: the approval code reaches the judge from three places that the list does not name.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team corrects the list and the test (fix round running, NOT RUN); then the connector and store team installs.
- **K69. Not checked:** that the run map given to the gate is the run's own, current map. A copy taken earlier, or another run's map, still reads "map used" in the audit row. A masking function supplied by the calling code is accepted outside tests too.
  - Example: the calling code passes yesterday's run map; values found today are not masked, and the row says the map was used.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the owner decides, together with the empty-map question; then the text and masking team.
  - [INTERNAL] Tied to decision 6 in part 1a.
- **K18. Not handled:** a gate refusal or a refused reservation leaves the run's status "working" instead of "stopped".
  - Example: after a refused reservation the run still shows "working". The planted-instruction check reports the same refusal as a guard failure.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written install request).
- **K19. Not through the gate:** the guardrail call. It is neither masked by the gate nor counted against the cap.
  - Example: a run's guardrail calls cost money that the cap never sees.
  - Status: STATED (accepted in the written plan, 2026-11-20). Evidence: NONE. Who acts: nobody.

### 2.2 Spending cap

Shown by tests:

- In the gate's tests, it makes no model call without a reservation. Order: mask, reserve, call, settle, write the audit row.
- On the connector and store team's store code, database version 16, Python 3.13: 50 separate database connections, started together by the test, each asked for a reservation. Cap 3.00 USD for the day and the month, worst case 1.00 USD. 3.00 USD was reserved and 47 requests were refused. The test ran twice.
- Further cases in the same test file: five other cap and worst-case pairs, two agents, and a month cap reached over two days.
- These tests do not cover the database rights in K26 or a call costing more than its worst case (K24).
- In the gate's tests, when a reply arrives with a usable cost, the gate settles that real cost.

Known gaps:

- **K20. Not released:** the worst case of a failed call. The model connectors cannot yet say "refused before any answer".
  - Example: cap 3.00 USD, worst case 1.00 USD. Three failed calls book 3.00 USD. It stays booked for the rest of the day (day cap) and month (month cap).
  - Status: WAITING. Evidence: TESTED (a failed call is not settled); UNVERIFIED (the example, worked out). Who acts: the connector and store team (written request).
- **K21. Booked as free:** a reply with an empty cost field. The connectors' reply form fills an empty cost with 0.00 USD, and the gate settles 0.00 USD as 0.00 USD.
  - Example: a connector forgets to fill in the cost; a 0.80 USD call is booked as 0.00 USD.
  - Status: WAITING. Evidence: TESTED (the gate side); UNVERIFIED (that a connector leaves it empty). Who acts: the connector and store team (written request).
- **K22. Not settled:** a reply with an unreadable cost (absent, negative, or not a number). The worst case stays booked. This over-counts spending and never under-counts it.
  - Example: a reply reports its cost as "not a number"; the full 1.00 USD stays booked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K23. Not counted:** earlier attempts of a call that succeeded after retries. Only the last attempt is settled.
  - Example: attempt 1 times out but was billed 0.40 USD; attempt 2 costs 0.30 USD; only 0.30 USD is booked.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written order).
- **K24. The cap can be passed once:** a call that costs more than its worst case is booked in full, on purpose.
  - Example: three calls each reserve 1.00 USD (cap 3.00 USD). One settles at 2.50 USD. Booked: 1.00 + 1.00 + 2.50 = 4.50 USD. Later calls are refused.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody (by design). A sound worst-case formula (K25) keeps it rare.
- **K25. Not written:** the worst-case formula. No function in the code fits the gate today.
  - Example: a formula that ignores documents would make K24 the normal case.
  - Status: WAITING. Evidence: NOT RUN (nothing to test). Who acts: the connector and store team (written order).
- **K26. Not enforced by the database:** the runtime login can rewrite a reserved amount; the purge login can delete an open reservation.
  - Example: faulty code could lower its own reservation.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the owner decides; then the connector and store team changes the rights.
  - [INTERNAL] Decision 5 in part 1a.
- **K27. Not refused:** an out-of-date price table.
  - Example: a vendor raises prices; the worst case is computed at the old price.
  - Status: STATED (accepted in the written plan, 2026-11-20). Evidence: NONE. Who acts: nobody.
- **K28. Not capped across processes:** the test and replay command lines keep their cap in memory, per process.
  - Example: two replay processes each spend up to the cap.
  - Status: STATED (accepted in the written plan, 2026-11-20). Evidence: NONE. Who acts: nobody.

### 2.3 Stop switch

Shown by tests:

- In the gate's tests, a refused reservation, including the stop switch's refusal, means no model call.
- That the store refuses every reservation while the switch is on is in the connector and store team's code. No test of that code for this is named here (UNVERIFIED).
- No end-to-end stop of a live run was tested (NOT RUN).

Known gaps:

- **K29. Not narrowed by the database:** the runtime login can sign a stop record with any name; the reset login can change any stop-switch row.
  - Example: a stop record says "by: operator" when the runtime wrote it. Any change the reset login makes reads as "on", so the store then refuses reservations.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the owner decides; then the connector and store team changes the rights.
  - [INTERNAL] Decision 5 in part 1a.
- **K30. Not stopped:** a call already in flight, and the test and replay command lines (they do not read the switch).
  - Example: a 30-second call started before the stop still completes.
  - Status: STATED (accepted in the written plan, 2026-11-20). Evidence: NONE. Who acts: nobody.

### 2.4 Audit record

Shown by tests:

- The gate tries to write one audit row per call: run, type of action, who asked, result, and a code from a fixed list.
- In tests, the gate's code holds no logging and no error text, and no audit row in those tests held a secret.
- In tests, if writing the row or settling fails after the reply came back, the gate still returns the reply.

Known gaps:

- **K31. Not recorded:** whether anything was masked, and the route.
  - Example: an investigator cannot tell from the row whether a secret was masked.
  - Status: OPEN. Evidence: NONE (a design question). Who acts: the owner decides.
  - [INTERNAL] Decision 2 in part 1a.
- **K32. Not narrowed:** the reset login can add any audit row, not only a reset record.
  - Example: faulty reset code could write a row that looks like a model call.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the owner decides; then the connector and store team changes the rights.
  - [INTERNAL] Decision 5 in part 1a.
- **K33. Not in the record:** the test and replay command lines print their audit lines to the screen only.
  - Example: a replay leaves no row in the store.
  - Status: STATED (accepted in the written plan, 2026-11-20). Evidence: NONE. Who acts: nobody.

### 2.5 The secret finder (what enters the run map)

Shown by tests (on the shared branch; batch of 135 files before the merge, and the later batch of 9,681 tests):

- It finds the kinds it knows: addresses, keys, tokens, e-mail, passwords in web addresses and command lines, and supplier payment details (a bank account beside its bank code).
- One call masks a bank account beside its bank code. It also masks the rest of a longer token that holds a shorter known secret (K40).
- One call runs up to 5 search rounds. Past the 5th round, it refuses the whole text (fail closed).
- A reviewer read that one text can go through up to 7 calls of the secret finder, one for each way of reading it, such as the decoded and the folded text (UNVERIFIED).
- A line it cannot mask in place is withheld.

Known gaps and fixed findings:

- **K34. Not found:** a secret in a shape the secret finder does not know.
  - Example: an unlabelled 40-character code in plain prose.
  - Status: STATED (in the published README, section "Limits and trust"). Evidence: NONE. Who acts: nobody.
- **K35. Not masked:** a bare number with no label.
  - Example: `ref 55556666 paid`. Measured on the main line: 24 of 43 such test lines not masked.
  - Status: STATED (written down as accepted, 2026-11-20). Evidence: MEASURED. Who acts: nobody.
  - [INTERNAL] Source: ticket G4 v2 section 6 calls it "an accepted decision (order 64 item 4)"; this drafter did not find that order in ORDERS.md (UNVERIFIED source).
- **K36. Not masked:** host names with no "host" word in front; a private name with a public ending is masked only in part.
  - Example: `db01.acme.example` stays; `db01.corp.example` becomes `<HOSTNAME_1>.example`. Measured on the main line, which lacks the planned change: 28 of 44 test lines leaked.
  - Status: OPEN. Evidence: MEASURED. Who acts: the owner decides; then the text and masking team builds.
  - [INTERNAL] Decision 3 in part 1a; plan version 2 is in tickets/G4-P1c-redactor-gaps-v2.md, its review running.
- **K37. Not masked:** base64 text under 40 characters.
  - Example: a short password written in base64. Measured on the main line: 41 of 41 such lines leaked.
  - Status: OPEN. Evidence: MEASURED. Who acts: the owner decides; then the text and masking team builds.
  - [INTERNAL] Decision 3 in part 1a.
- **K38. Not masked:** an IP address, phone number, international bank account number or unique id with a letter or `_x` glued behind it.
  - Example: `10.20.30.40_x` goes out unmasked. Measured on the joined branch whose code is now on the shared branch.
  - Status: OPEN. Evidence: MEASURED. Who acts: the text and masking team (writes the next work item).
- **K39. Not proven:** that the repeated search finds every value. Each call now runs up to 5 search rounds.
  - Example: planted text glues a bank code to a secret, then puts the account after that code elsewhere. This needed a third round and is now masked. A reviewer read that a line changed by the patterns, but not by the masking step, is not searched again in later rounds (UNVERIFIED; no leaking text was built). Planted text that needs a 6th round makes the secret finder refuse the whole document (UNVERIFIED).
  - Status: OPEN. Evidence: TESTED (the chain; batch of 9,681 tests, 0 failed); UNVERIFIED (the reviewer's case). Who acts: the text and masking team (fix round running, NOT RUN).
- **K40. Fixed:** the last part, up to 7 characters, of a longer token stayed readable in its other copies, when the token was found only after a shorter known secret inside it.
  - Example: `password=ab9x`, then `Bearer ab9xqrstu`; the line `note ab9xqrstuvw end` used to show `note <SECRET_1>qrstuvw end` and now shows `note <BEARER_1>vw end`.
  - Status: FIXED. Evidence: TESTED (20 of 28 new tests failed before the change; batch of 9,681 tests, 0 failed). Who acts: nobody. See K68.
- **K41. Not limited:** how long one call of the secret finder takes. Its time budget (6 seconds of processor time per call) is checked before each search round, not inside one.
  - Example (measured, processor time): 100,000 characters of bank lines took 0.167 seconds before the repeat and 0.395 seconds with it. A text at the size cap, built to be slow, took 4.00 seconds against the 6-second budget.
  - Status: OPEN. Evidence: MEASURED (those numbers). A reviewer read that one call can take its budget plus one whole search round, and that one step grows with the number of values times the text length, with no time check (UNVERIFIED). Who acts: the text and masking team (fix round running, NOT RUN).
- **K42. Not masked later:** a secret first seen in a tool's error message. It never enters the run map.
  - Example: a tool fails with "bad password hunter2zz"; later results show `hunter2zz`.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written request).
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
  - Status: STATED (in the SECURITY.md on the main line since 2026-11-04). Evidence: NONE. Who acts: nobody.
- **K68. Wrong value restored:** after the secret finder undoes a half-made entry, an old record can survive. A later placeholder with the same number can then be restored to the wrong value. The text stays masked; nothing raw leaks to the model.
  - Example: a token found and then undone leaves a record for `<BEARER_1>`; a new `<BEARER_1>` for another value is later restored as the old one.
  - Status: OPEN. Evidence: UNVERIFIED (two reviewers' reading). Who acts: the text and masking team (fix round running, NOT RUN).

### 2.6 Text folding (look-alike and hidden characters)

Shown by tests (on the shared branch, in the batch before the merge):

- Before the secret finder searches, it folds the text: look-alike letters, invisible characters and accents become one plain spelling.
- Condition: the program runs on Python 3.13 (see README, section "Python version").

Known gaps and fixed findings:

- **K47. Fixed:** the secret finder's own look-alike search was missing from the shared branch. It is there now.
  - Example: `password=x` written with a Cyrillic "а" is now found.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K48. Not decoded by folding:** escape codes; look-alikes added after Unicode edition 15.1; hidden marks outside two character blocks.
  - Example: the escape code `abc1` (`1` is a code for the digit 1) is not read as `abc1`.
  - Status: STATED (in the text work's written limits, 2026-11-20). Evidence: UNVERIFIED (a reviewer's reading confirms the limits). Who acts: nobody.
- **K49. Not flagged:** the Chinese character for zero (Unicode name IDEOGRAPHIC NUMBER ZERO, 〇) inside a Latin word.
  - Example: `pay` + 〇 + `al` is not called mixed script. It is the only such character in the folding table (measured).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K50. Not measured:** how often folding finds a known name inside an innocent longer word.
  - Example: known `Mary` found in `summary`; innocent text may be masked or withheld.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading); the measurement is NOT RUN (no result is recorded). Who acts: the text and masking team.
- **K51. Not limited:** the time text folding takes. The planted-instruction check folds up to 2,097,152 characters with no time limit.
  - Example: a very large planted text slows that check.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the text and masking team.
- **K52. Refused, not read:** a long text in Chinese or Japanese only. It is reported as a guard failure.
  - Example (measured): 300,000 characters of Chinese, and of Japanese, were refused. Russian prose of that size is read. The shortest length that is refused was not measured (NOT RUN).
  - Status: STATED (written down by the text and masking team, 2026-11-20). Evidence: MEASURED. Who acts: nobody.
- **K53. Chosen in a written order:** dashes and curly quotes are ordinary punctuation; three slash look-alikes make the line withheld.
  - Example: a value right after an em dash (—) is masked in place. A line holding DIVISION SLASH (∕), BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT (╱) or BIG SOLIDUS (⧸) plus a look-alike value is withheld.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K54. Finds more than before:** an invisible character between a Latin letter and its accent. Accepted in a written order.
  - Example: `e` + hidden mark + accent now matches `é`.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K55. Not decided:** the same wider matching in Korean, Japanese and Indian scripts, for the grounding check.
  - Example: a Korean name split by a hidden mark now counts as present.
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the owner decides.
  - [INTERNAL] Decision 4 in part 1a.
- **K56. Fixed:** a secret stored as `Müller` but shown with a separate accent mark was not masked in tool output.
  - Example: `Mu` + combining accent + `ller` is masked again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K57. Fixed:** look-alike padding before a 32,768-character boundary could hide a planted order from the planted-instruction check.
  - Example: "ignore previous instructions" split across that boundary is found again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K58. Fixed:** on the wrong Python, the connection to the secrets vault was built before the start-up refusal. The refusal now comes first.
  - Example: a pilot build on the wrong Python stops before it builds the connection to the secrets vault.
  - Status: FIXED. Evidence: TESTED (one test, on Python 3.13 with the version faked; other outside services were not checked). Who acts: nobody.

### 2.7 Approval messages

Shown by tests (on the shared branch):

- On each free-text path found so far that writes an approval message, the secret finder runs first. Web addresses are made unclickable last (a dot written as `[.]`).
- 26 path test functions exist. The batch of 135 files before the merge had 2 failures (see 2.0), neither in these path tests. That these path tests were in that batch is UNVERIFIED: the batch's file list is not recorded.
- A message is re-read until it stops changing, at most 3 times. If it never settles, a fixed note is shown instead.
- Id fields are not masked (K59).

Known gaps and fixed findings:

- **K59. Not masked:** the "requested by" line and other id fields.
  - Example (UNVERIFIED: read from the code, not tried on Slack): a requester id `slack:U1|<!channel>` could make Slack notify everyone in the channel.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written request).
- **K60. Not proven:** that no clickable link remains. The test for it uses the same patterns as the code it tests.
  - Example: a link the patterns miss, such as `see/evil.com`, would slip past both (UNVERIFIED).
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the text and masking team (adds a link check with its own patterns).
- **K61. Fixed:** an e-mail address with a digit or `_` glued behind it was shown whole.
  - Example: `anna.m@example.org9` is now masked.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K62. Not checked:** approval summaries stored before these fixes, as shown on the staff admin page.
  - Example: a summary stored before the fixes could still show an e-mail address; nobody has looked.
  - Status: OPEN. Evidence: NOT RUN. Who acts: the text and masking team.

Measured slowdown of approval-message masking on the joined code (median, on the builder's test machine): a 174-character message went from 1.26 ms to 3.60 ms; a 71,179-character message went from 367 ms to 655 ms.

### 2.8 Set-up

- **K63. Late failure:** the project file allows installing on Python 3.12. A pilot or prod install there succeeds and fails only at start.
  - Example: an operator installs on 3.12; the program then refuses to start (see README, section "Python version").
  - Status: OPEN. Evidence: NOT RUN (no install on 3.12 was tried). Who acts: the connector and store team (no written request yet).

### 2.9 What was not run (NOT RUN)

- The full test suite. Python 3.12 on this work's code (only an older branch ran there once). Database version 17 (the automatic test service uses 17.10).
- Any live call to an AI service. Any end-to-end stop of a live run. The gate installed at any call point.
- The planned host-name and base64 change (never built). 238 of the 240 deliberate code breaks for text folding.
- A recorded test batch on: the merge result as a whole; the gate's fixes for its second review; the time limit inside the secret finder's masking step.
- The gate's third fix round and the secret finder's third fix round (both running; no results here).

---

## 3. For README.md: "Python version"

As of 2026-11-20 07:52 UTC.

[INTERNAL] This section describes the text folding change. As of 2026-11-20 it is on the shared branch only, not on the product's main line. Ship it with the release that contains that change.

**Operators (the people who install and run the kit for a client) must run pilot and prod on Python 3.13.** To see your version, run `python3 --version`.

Why: text folding uses the Unicode character data built into Python. Unicode is the world standard list of characters, and each Python version carries one edition. The folding tables are built for edition 15.1.0, which Python 3.13 carries. Python 3.12 carries 15.0.0.

Pilot and prod on Python 3.12: by design the program refuses to start and prints the error UnidataMismatch. This was NOT RUN on Python 3.12; one test shows the refusal on Python 3.13 with the version faked. The project file still allows installing on 3.12, so the install succeeds and the failure shows only when the program starts.

In that test, the refusal comes before the program builds its connection to the secrets vault. Other outside services were not checked.

Demo stage on Python 3.12 (NOT RUN on 3.12; this is the design): the program starts. Each name that text folding makes carries the Unicode edition, so names made on 3.12 and on 3.13 are designed never to match. Do not mix results from the two versions.

Moving to a later Python (for example 3.14): the text and masking team must first rebuild the character tables. Changing the version number alone is not enough.

---

## 4. Technical appendix (INTERNAL, does not ship)

As of 2026-11-20 07:52 UTC. Internal references (codes, test names, files, orders, commits) appear only here. Team codes: core-b = the connector and store team; core-c = the text and masking team.

### 4.1 Key to codes used in the sources
| code | meaning |
|---|---|
| cloud/core-c | the shared branch; head at the time of writing: 11935aa (07:52 UTC, pushed; equal to origin/cloud/core-c) |
| d95a727 | the merge of the integration (P1d-a card fixes, P2d-1 fold scan, G7, glued-rest fixes) into cloud/core-c, 07:28 UTC. Its second parent cfda4d0 is the pick branch wip-pick; its first parent 1c884b2 is a gate snapshot "work in progress, NOT verified" |
| wip-pick | the worktree branch /tmp/core-c-pick, cut from bd4446c, where the pick batch ran (evidence/PICK-int-onto-core-c.md) |
| fb08bde, 89af120, 1c884b2 | work-in-progress commits on cloud/core-c ("NOT verified"); guard/model_gate.py last changed in fb08bde (git log at HEAD) |
| aa7c5fa | core-c's edit of guard/producers.py (core-b's file), 07:36 UTC: 1 file, 2 lines added (git show --stat); tests/test_k5_producers.py 25 passed (commit message; DECISIONS 07:40) |
| c9478a9 | 07:38 UTC, title "code F: gate round 2 fixes ..."; its message reports "81 of 81 mutants good, 302 passed in the gate and install files". Its files are the G7 fix round 2 code (guard/redact.py, guard/runmap.py 4 lines, defaults.py, tests incl. tests/test_redact_settle_loop.py) and evidence/G7-1.md; model_gate.py is not in it |
| a2b6311 | 07:41 UTC, "code G: work in progress of the running G7 fix round 2 builder, NOT verified": `_Redactor.sweep(out, deadline=None)` and its test |
| working copy | clean at 07:52 UTC (git status: no changes) |
| origin/main | the product's main line; none of d95a727, c9478a9, a2b6311 is on it |
| F, G, B, T1 | work packages: F the gate; G the text work; B database rights; T1 the 50-connection cap test |
| G0 | the check-only mask function (later deleted by lead decision) |
| G1 / G2 / G3 | text folding / approval-message text (old branch P1d-a) / the look-alike search ported into the secret finder (old branch P2d-1) |
| G4 | the planned base64 and host-name change (old ticket P1c), not built; v2 ticket tickets/G4-P1c-redactor-gaps-v2.md (330f4fb, 07:46 UTC), plan review round 2 running; G5, G6 docstring wording; G7 the extra search rounds after the sweep |
| dz, cb / dz2, cb2 / F-r3 | first / second / third independent result review of the gate (design reviewer dz, code reviewer cb); third: tickets/F-result-review-3.md (design 0 B, 4 M, 5 N; codebase 0 B, 5 M, 7 N) |
| dz-1 to dz-8, cb-M1 to cb-M4 / G7-r2 | result review round 1 of G7 / round 2: tickets/G7-result-review-2.md (codebase 1 B, M2-M7 = 6 M (its header says 5), N8-N10; design 0 B, 5 M, 3 N) |
| B1, B2, M3 to M10 | result review of text folding |
| M1 to M7, N1 to N8 | result review of the approval-message text |
| g4r | plan review of G4 (tickets/G4-review-1.md: 8 Blockers, 6 distinct, 12 Majors) |
| E1 to E7 | entries in ESCALATIONS.md (E7: database rights) |
| ORDER nnn | orders from the lead in ORDERS.md; MJ-A to MJ-D = Majors of the lead's review round 3 (ORDER 020) |
| T:: / E:: | tests/test_model_gate.py / tests/test_runmap_enforce_map.py |
| sweep | the step that masks every copy of values already in the run map (the "masking step" of a search round) |
| NO_MAP | the named constant for "no map" |
| strict xfail | strict expected failure |
| refusal words | gate: `mask_refused`, `framing_refused`, `worst_case_failed`, `worst_case_invalid`, `reserve_refused`, `reservation_invalid` (type `GateRefused`); store: `kill_switch` (stop switch), `daily_budget`, `monthly_budget`, `limits_unavailable`, `bad_amount`, `usd_cap` |
| audit decision field | `map_enforced`, `map_enforced_empty`, `enforce_custom`, `map_failed`, `no_map`; codes `call_interrupted`, `reserve_interrupted`, `held_value_left` |
| framing marker | `<<TOOL RESULT call_id=ID tool=NAME>>` ... `<<END TOOL RESULT>>`; assistant line `tool NAME {json}` |
| UnidataMismatch | the start-up refusal of `textnorm.require_pinned_unidata` (README part 3) |
| REDACT_BUDGET_S | 6.0 CPU seconds of the calling thread per `redact_text` call (defaults.py:65) |
| `_SETTLE_ROUNDS` | 4 (redact.py:1751): rounds 2 to 5 after the first pass; RedactionError("NotSettled") past it |

### 4.2 Table of known gaps
| gap | status | evidence level | evidence | who acts |
|---|---|---|---|---|
| K1 secret not found passes | PINNED | TESTED | T::test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job | nobody |
| K2 short, digits, common words, touching | PINNED | TESTED | E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept; E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept; rule read in redact.py `_sweep` 1905-1917 (secret kind and 4+ characters: every copy) | nobody |
| K3 other spellings | PINNED | TESTED / UNVERIFIED (alias) | T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate; E::test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced; E::test_stated_limit_a_copy_split_by_nul_characters_is_not_found; T::test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced; alias spellings: F-r3 codebase M2 (reading) | nobody (gate); F round 4 for the alias point |
| K4 letter case | PINNED | TESTED | T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced | nobody |
| K5 overlap tail | PINNED | TESTED | E::test_stated_limit_partial_overlap_leaves_a_tail; T::test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent | nobody |
| K6 joined key and value | PINNED | TESTED | T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched | nobody |
| K7 placeholder-shaped values | PINNED | TESTED | E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced; E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder; E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass | nobody |
| K8 fields not masked | PINNED | TESTED | T::test_t20_system_and_tools_are_not_touched; T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched. Separate: the prompt-registry install check is asked in requests/3-bind-mapping-required.md section 6 (ORDER 020 MJ-D), WAITING on core-b | nobody (gate); core-b (the request) |
| K9 no map | PINNED | TESTED | T::test_no_map_means_no_enforce_step_at_all; NO_MAP placement checked by tests/test_gate_install_callers.py (plain test) | nobody |
| K10 audit says map in use | FIXED ON BRANCH | NOT RUN | dz2-M5; T::test_r2_m5_the_audit_decision_says_what_was_really_enforced; mutants G22a-c (81 of 81 run recorded in evidence/F-G0-1.md); WIP commits; no pytest result recorded (F-r3 codebase M5) | core-c |
| K11 forged marker | FIXED ON BRANCH | NOT RUN / UNVERIFIED (closed, reading) | dz2-B1, ORDER 020 MJ-A; reproduced by the builder; T::test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client[id,name,both]; old pin renamed to T::test_o17_6_a_value_that_only_lies_inside_a_framing_word_leaves_the_fixed_words_alone; mutants B1a, B1b; F-r3 design "verified closed" (reading) | core-c |
| K12 edge value tail | OPEN | NOT REPRODUCED | dz2-M2 (reading); NOT REPRODUCED by the builder (evidence/F-G0-1.md "Review round 2 fixes (final)"); safety net `held_value_left`, T::test_r2_m2_a_held_back_edge_value_does_not_leak_the_tail_of_a_secret, T::test_r2_m2_safety_net_a_held_back_secret_value_left_raw_refuses_the_call; mutant G24. F-r3 did not name it again (not a check) | core-c |
| K13 per-call time and size | OPEN | MEASURED / UNVERIFIED | dz2-M3 PARTLY FIXED: one EnforceBudget per call, cap 256 held-back values; measured 0.018 s for 100 texts / 2,000 entries (F-G0-1.md); T::test_r2_m3_one_budget_per_chat_call_and_a_cap_on_held_back_values; missing deadline: runmap.py:742 and :746 call `sweep(out)` with no deadline (read at HEAD); clock mismatch G7-r2 codebase M5; F-r3 design M2 (128 million steps, estimate) | core-c (F round 4) |
| K14 planted secret stops tool calls | OPEN | TESTED (old rule) / NOT RUN (new rule) / UNVERIFIED | T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker; new rule: T::test_r2_m4_an_identifier_kind_value_equal_to_a_tool_name_does_not_stop_the_run, T::test_r2_m1_a_value_the_sweep_never_replaces_does_not_stop_a_run_with_a_tool_of_that_name; mutants O6-O8; F-r3 design M1a, codebase N3 (reading) | lead (decision 1) |
| K15 tool line rewritten | FIXED ON BRANCH | NOT RUN | cb2-M2; T::test_r2_m2_the_assistant_line_and_the_token_name_the_tool_alike_when_a_value_sits_inside_it; T::test_r2_m2_the_fixed_word_of_the_assistant_line_is_kept_exact; mutants O9, O10 | core-c |
| K16 interrupt leaves no row | FIXED ON BRANCH | NOT RUN / UNVERIFIED (two more places) | dz2-M7; T::test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on; T::test_pin_no_settle_on_keyboard_interrupt; mutants G23a-d; F-r3 design N4 (`_enforced`; gap between reserve and try) | core-c (F round 4) |
| K17 two writers | OPEN | NONE | a race; ticket F stated limits; no request names "one writer per run map" (requests/3 read) | core-c (adds it to request 3) |
| K18 run left "working" | WAITING | UNVERIFIED | F-result-review-2.md call-site list; ticket F "For core-b (install)": agent_loop.py:477; requests/3-bind-mapping-required.md section 3 | core-b |
| K19 guardrail call outside gate | STATED | NONE | inputs/plan-v4-final.md line 29 ("the Bedrock guardrail detector call is not metered"), frozen 2026-11-20; tests/test_gate_install_callers.py BYPASS table | nobody |
| K20 failed call stays booked | WAITING | TESTED / UNVERIFIED (example) | T::test_pin_an_unmarked_provider_error_is_not_settled; T1 expiry case (counters stay after expiry); requests/2-refused-before-response.md | core-b |
| K21 empty cost booked as free | WAITING | TESTED / UNVERIFIED | T::test_m5_a_zero_cost_reply_is_settled_at_zero; models.py:299 `cost_usd: Decimal = Decimal(0)` (read at HEAD); requests/3-bind-mapping-required.md section 4 | core-b |
| K22 unreadable cost not settled | PINNED | TESTED | T::test_pin_a_reply_with_no_usable_cost_is_not_settled; T::test_o17_2_a_reply_whose_cost_is_absent_or_not_a_usable_number_is_cost_unknown_and_not_settled | nobody |
| K23 retries settle last attempt | WAITING | UNVERIFIED | llm/retry.py lines 92-107 (reading, E6 item 3); ORDER 017 item 3 | core-b |
| K24 overshoot booked in full | PINNED | TESTED | tests/contracts/test_t1_reserve_cap.py::test_a_settle_above_the_reserve_books_the_actual_amount_past_the_cap (core-b 576f292, PostgreSQL 16.15); T::test_a_settle_above_the_reservation_is_passed_through | nobody |
| K25 worst-case formula | WAITING | NOT RUN | ORDER 016c item 13; ticket F "For core-b (install)" item 3 | core-b |
| K26 reservation rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md findings 1, 2 (migrate.py:56, read); E7 items 1-2 | lead (decision 5), then core-b |
| K27 stale price table | STATED | NONE | plan-v4-final line 29, frozen 2026-11-20 | nobody |
| K28 in-memory cap on command lines | STATED | NONE | plan-v4-final line 29; interface README 2.1; refusal `usd_cap` (ORDER 014) | nobody |
| K29 stop-switch rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md findings 3, 4 (migrate.py:61-62, read); E7 items 3-4 | lead (decision 5), then core-b |
| K30 in-flight call, command lines ignore stop | STATED | NONE | plan-v4-final B3, frozen 2026-11-20 | nobody |
| K31 audit lacks masked flag and route | OPEN | NONE | F-result-review-1.md nits; the decision field (4.1) covers map use only | lead (decision 2) |
| K32 reset login audit rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md finding 5 (migrate.py:65, read); E7 item 5 | lead (decision 5), then core-b |
| K33 command lines audit to screen | STATED | NONE | plan-v4-final B2, frozen 2026-11-20 | nobody |
| K34 unknown shape | STATED | NONE | README.md "Limits and trust" (main line) | nobody |
| K35 bare number | STATED | MEASURED | evidence/P1c-probe.md (24 of 43, main code; "accepted property"); tickets/G4-P1c-redactor-gaps-v2.md section 6 ("order 64 item 4": not found in ORDERS.md by this drafter) | nobody |
| K36 host names | OPEN | MEASURED | evidence/P1c-probe.md (28 of 44 leaked, main code); tickets/G4-review-1.md; G4 v2 ticket (review running) | lead (decision 3), then core-c |
| K37 short base64 | OPEN | MEASURED | evidence/P1c-probe.md (under 40 characters: 41 of 41; all base64 rows: 52 of 142; main code) | lead (decision 3), then core-c |
| K38 glued IPv4, phone, IBAN, UUID | OPEN | MEASURED | evidence/INT-g2-g3.md follow-up (c); now in d95a727 | core-c |
| K39 repeat not proven complete | OPEN | TESTED / UNVERIFIED | tests/test_redact_idempotent_property.py::test_one_pass_is_a_fixed_point_and_leaves_no_raw_copy[constructed:0] (strict xfail removed; passes); tests/test_redact_settle_loop.py; evidence/G7-1.md "G7 fix round 2: evidence" batch 9681 passed, 73 skipped, 5 xfailed, 0 failed; G7-r2 design M1, M2, codebase M3 (reading) | core-c (G7 round 3) |
| K40 tail up to 7 | FIXED | TESTED | tests/test_redact_settle_loop.py tail cases (fail-before 20 of 28 on round 1 code); evidence/G7-1.md batch above; c9478a9 | nobody |
| K41 finder time | OPEN | MEASURED / UNVERIFIED | evidence/G7-1.md round 2 timings table (T1 0.167 -> 0.395 s; T4 `curl -u` 4.00 s, budget 6.0); G7-r2 design M4, M5 (reading) | core-c (G7 round 3) |
| K42 tool error not in map | WAITING | UNVERIFIED | G7 review dz-6 (reading); requests/4-error-reason-run-map.md | core-b |
| K43 escaped-placeholder spelling | PINNED | TESTED | tests/test_redact_own_output.py::test_only_the_exact_escaped_shape_is_left_alone; tests/test_redact_own_output_hardening.py::test_legitimate_own_output_is_left_alone | nobody |
| K44 wrapped secret | FIXED | TESTED | tests/test_redact_own_output_hardening.py::test_a_secret_wrapped_in_lookalike_brackets_is_masked (10 failed before; ab6ff2f; kept in the pick) | nobody |
| K45 finder on its own output | FIXED | TESTED / UNVERIFIED (other places) | tests/test_redact_own_output.py::test_the_tool_error_path_adds_no_map_entry_and_keeps_the_escaped_text (8 failed before); caller table in tickets/G7-context-after-sweep.md (reading) | nobody |
| K46 separators in a secret | STATED | NONE | SECURITY.md "Stated limits of redaction" (main line, ce70eb5, 2026-11-04) | nobody |
| K47 look-alike search in the finder | FIXED | TESTED | tests/test_redact_g3_port.py; pick batch; merged in d95a727 | nobody |
| K48 escapes, newer characters, hidden marks | STATED | UNVERIFIED | G1 review (tickets/G1-result-review-1.md line 17: documented limits confirmed by reading) | nobody |
| K49 Chinese zero (U+3007) | PINNED | TESTED | tests/test_textnorm_mixed_script_micro.py::test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed; evidence/TW-order020.md (1 of 852 table entries) | nobody |
| K50 over-matching | OPEN | UNVERIFIED / NOT RUN | G1 review M5 (reading); evidence runner `evrun` (STATUS-BOARD: running; no evidence file) | core-c |
| K51 folding has no time limit | OPEN | UNVERIFIED | G1 review M4 (reading) | core-c |
| K52 long Chinese or Japanese text | STATED | MEASURED | evidence/G1-fold.md "G1 fix round 1", M6 (300,000 characters; threshold not measured) | nobody |
| K53 dashes, quotes, slashes (U+2215, U+2571, U+29F8) | PINNED | TESTED | tests/test_redact_g3_port.py::test_typography_an_em_dash_is_ordinary_the_value_beside_it_is_masked_in_the_line, ::test_typography_a_curly_quote_is_ordinary_the_value_inside_the_quotes_is_masked_in_the_line, ::test_typography_the_division_slash_u2215_withholds_a_line_with_a_lookalike_value, ::test_typography_the_box_drawing_diagonal_u2571_withholds_a_line_with_a_lookalike_value, ::test_typography_the_big_solidus_u29f8_withholds_a_line_with_a_lookalike_value; ORDER 014 item 9 | nobody |
| K54 Latin accent matching | PINNED | TESTED | tests/test_evidence_decomposed.py::test_known_difference_from_main_an_invisible_character_between_a_letter_and_its_accent_now_joins_them; ORDER 010 item 3 | nobody |
| K55 other scripts (grounding, runtime/evidence.py) | OPEN | UNVERIFIED | G1 review M7 (reading) | lead (decision 4) |
| K56 undo recombines | FIXED | TESTED | tests/test_undo_composes.py (9 of 10 failed before) | nobody |
| K57 boundary split | FIXED | TESTED | tests/test_injection_chunk_boundary.py (6 failed before) | nobody |
| K58 start-up order | FIXED | TESTED | tests/test_app_unicode_check_order.py::test_a_wrong_unicode_version_refuses_a_pilot_build_before_any_backend_is_made (3.13, version stubbed; `make("secrets", ...)` recorded) | nobody |
| K59 requested-by line | WAITING | UNVERIFIED | G2 review M3 (reading); requests/5-card-ids-redact-defang.md | core-b |
| K60 link check shares patterns | OPEN | UNVERIFIED | G2 review M6 (reading) | core-c |
| K61 glued e-mail | FIXED | TESTED | tests/test_text_parts_together.py::test_glued_email_regression_digit_or_underscore_behind_the_address; tests/test_p1d_a_paths.py::test_glued_addresses_are_masked_whole_in_one_pass; merged in d95a727 | nobody |
| K62 admin page | OPEN | NOT RUN | G2 review "not checked" (the admin console) | core-c |
| K63 install on 3.12 succeeds | OPEN | NOT RUN | pyproject.toml line 8 `requires-python = ">=3.12"` (read at HEAD); SEC-wording-review-2 Major (Part 3); no request file | core-b (core-c writes the request if the lead agrees) |
| K64 planted edge values over 256 | OPEN | UNVERIFIED | F-r3 design M1(b) (reading; `snapshot` InputTooLarge, every chat `mask_refused`); step budget 102,400 (same finding) | core-c (F round 4) |
| K65 safety net held values only | OPEN | UNVERIFIED | F-r3 design M3 (reading); runmap.py:827-833 `held_value_left` checks `snap.secret_held` only (read at HEAD) | core-c (F round 4) |
| K66 tool name slot vs tool list | OPEN | UNVERIFIED | F-r3 codebase M1 (reading) | core-c (F round 4) |
| K67 install list misses judge sites | OPEN | UNVERIFIED | F-r3 codebase M3, M4 (reading: app.py:217, judge.py:40, 65-72, approvals/cards.py:79, approvals/requests.py:37, :105, k1b/loop.py:205) | core-c (F round 4: request 3, ticket F, install test), then core-b |
| K68 rolled-back spelled entry | OPEN | UNVERIFIED | G7-r2 codebase M4, design M3 (reading; redact.py 1520-1532, 1613-1614) | core-c (G7 round 3) |
| K69 map not checked as the run's own | OPEN | UNVERIFIED | F-r3 design M4 (reading); overlaps ORDER 020 m-2 (contested, DECISIONS 07:35) | lead (with decision 6), then core-c |

State items (not gaps):
- Gate not installed: tests/test_gate_install_callers.py holds 3 strict expected failures until core-b installs (evidence/TW-order020.md; the file's own comment at line 210: "remove the marker when the install lands"); tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered passes since aa7c5fa (25 passed, commit message; DECISIONS 07:40).
- The 50-connection test: tests/contracts/test_t1_reserve_cap.py::test_fifty_connections_against_a_cap_of_three_grant_exactly_three, plus 16 more cases (evidence/T1-reserve-cap.md), 49 passed twice on PostgreSQL 16.15, Python 3.13.18.
- Pick batch: 12,392 passed, 2 failed, 108 skipped, 7 xfailed in 135 files (-n 2, not perf). Failures: tests/test_redact_fold_budget.py::test_dm_2_257_decomposed_names_refuse_the_text_and_256_do_not (re-pinned in cfda4d0, then "1 passed, 22 deselected" alone) and tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered (closed by aa7c5fa). Perf 64 passed; gate mutants 66 of 66; bandit clean. NOT RUN there: Python 3.12, PostgreSQL 17, the full suite, the full batch after the re-pin, textnorm mutants, p1d_a mutants.
- G7 fix round 2 batch (evidence/G7-1.md): `pytest -n 2 -m "not perf"` over the redact/runmap/grep-redact files: 9681 passed, 73 skipped, 5 xfailed, 0 failed (251 s); perf 4 passed; ruff and bandit clean. The commit it ran on is not recorded; a2b6311 came after it.
- Mutants: tests/test_gate_mutants_picked_up.py found 24 stale search texts (evidence/TW-order020.md). evidence/F-G0-1.md "Review round 2 fixes (final)" records "81 of 81 good; problems: []". This drafter counted 81 `mutant(` calls in tests/gate_mutants.py at HEAD (read-only AST count, no mutant run). That each search text still matches the code at HEAD was NOT checked by this drafter (v3's drafter checked an earlier tree). tests/test_gate_mutants_picked_up.py still has MIN_MUTANTS = 66 (F-r3 codebase N6).
- Gate tests behind part 2.2 to 2.4: T::test_pin_no_client_call_without_a_reservation; T::test_t1_pass_path_order_is_enforce_reserve_call_settle_audit; T::test_t12_a_spend_refusal_passes_unchanged_and_no_call_is_made[kill_switch]; T::test_pin_every_outcome_writes_exactly_one_audit_row; T::test_i9_the_module_has_no_logger_no_exception_text_and_no_module_state; T::test_t18_no_secret_in_any_audit_row_exception_or_log_record; T::test_t17_a_raising_audit_sink_never_loses_the_reply_or_the_settle; T::test_m2_settle_raising_after_a_paid_call_returns_the_reply_and_the_row_says_ok. These last ran in the gate builder's batch "1 failed, 2307 passed, 2 xfailed" (before the review-round-2 fixes).

### 4.3 Counts by status (69 gaps)
| status | count | gaps |
|---|---|---|
| PINNED | 15 | K1-K9, K22, K24, K43, K49, K53, K54 |
| STATED | 10 | K19, K27, K28, K30, K33, K34, K35, K46, K48, K52 |
| WAITING (all on core-b) | 7 | K18, K20, K21, K23, K25, K42, K59 |
| OPEN, core-c acts | 15 | K12, K13, K17, K38, K39, K41, K50, K51, K60, K62, K64, K65, K66, K67, K68 |
| OPEN, the lead or core-b acts | 10 | K14, K26, K29, K31, K32, K36, K37, K55, K69 (lead); K63 (core-b) |
| FIXED | 8 | K40, K44, K45, K47, K56, K57, K58, K61 |
| FIXED ON BRANCH | 4 | K10, K11, K15, K16 |
| total | 69 | 15 + 10 + 7 + 15 + 10 + 8 + 4 = 69 |

By evidence level (each gap counted once; 58 single + 11 mixed = 69):
- TESTED only: 21 (K1, K2, K4-K9, K22, K24, K40, K43, K44, K47, K49, K53, K54, K56, K57, K58, K61).
- MEASURED only: 5 (K35, K36, K37, K38, K52).
- UNVERIFIED only: 17 (K18, K23, K26, K29, K32, K42, K48, K51, K55, K59, K60, K64, K65, K66, K67, K68, K69).
- NOT REPRODUCED: 1 (K12).
- NOT RUN only: 5 (K10, K15, K25, K62, K63).
- NONE: 9 (K17, K19, K27, K28, K30, K31, K33, K34, K46).
- Mixed: 11 (K3 TESTED+UNVERIFIED; K11 NOT RUN+UNVERIFIED; K13 MEASURED+UNVERIFIED; K14 TESTED+NOT RUN+UNVERIFIED; K16 NOT RUN+UNVERIFIED; K20 TESTED+UNVERIFIED; K21 TESTED+UNVERIFIED; K39 TESTED+UNVERIFIED; K41 MEASURED+UNVERIFIED; K45 TESTED+UNVERIFIED; K50 UNVERIFIED+NOT RUN).

Changes from v3 (63 gaps): K64 to K69 added (from F-result-review-3 and G7-result-review-2). K17 STATED to OPEN (core-c). K40 OPEN to FIXED. K12 evidence UNVERIFIED to NOT REPRODUCED; K13 UNVERIFIED to MEASURED + UNVERIFIED; K50 UNVERIFIED to UNVERIFIED + NOT RUN; K48 none to UNVERIFIED (its source is a reading); "none" rows renamed NONE. K39 reworded (the third-round chain is masked; completeness not proven). Totals: STATED 11 to 10; OPEN core-c 10 to 15; OPEN lead/core-b 9 to 10; FIXED 7 to 8.

Gaps named in part 1 (24 of 69): item 2: K25, K20, K21, K23, K42, K59, K18, K8 (request), K63; item 10 K34; item 11 K37; item 12 K36; item 13 K8; item 14 K19; item 15 K35, K46, K38; item 16 K42; item 17 K65, K66, K67; item 18 K23; item 19 K25; item 20 K24; item 21 K26; item 22 K21; item 23 K20; item 24 K14; item 25 K64; item 26 K63; item 31 K39. Distinct: K8, K14, K18, K19, K20, K21, K23, K24, K25, K26, K34, K35, K36, K37, K38, K39, K42, K46, K59, K63, K64, K65, K66, K67 = 24. Order rule: secrets first, then money, then stopped work; within a group, wider exposure first, and tested or measured before UNVERIFIED (item 16 and 17 follow item 15 for that reason).

### 4.4 Where two sources disagreed
1. Short-value exemptions: we used the later gate ticket (they do not apply to a secret of 4 or more characters), because it was checked against the sweep's code; this drafter read the same rule in redact.py `_sweep` at HEAD.
2. Settling after a plain connector error (settle 0, or not at all): we used ORDER 011 (not at all), because it replaced the earlier order.
3. A bind without a map (silent skip, or an error): we used ORDER 017 (an error; NO_MAP must be named), because it is newer.
4. The judge (no map, or the run's map): we used ORDER 017 item 1 (the run's map), because it is newest.
5. The tool-error double pass ("harmless", or a gap): we used the G7 review (a gap, K42), because the ticket's author withdrew "harmless".
6. Search rounds per call and calls per text: v3 used the G7 review ("two rounds per call, up to 7 calls per text"). Since c9478a9, `_SETTLE_ROUNDS` = 4 gives up to 5 rounds per call (evidence/G7-1.md; redact.py:1751). "Up to 7 calls per text" stays a reviewer's reading (G7-r2 design M4), marked UNVERIFIED.
7. Escaped look-alikes (any kind exempt, or only SECRET): we used the G7 fix evidence (only `‹SECRET_n›` with ASCII digits), because it is newer and tested.
8. The forged-marker leak (fixed, or leaking): we use evidence/F-G0-1.md "Review round 2 fixes (final)" (reproduced, then fixed in work in progress); F-r3 design reads it as closed. Batch NOT RUN.
9. The glued-digit e-mail (not fixed, or fixed): we used the integration evidence; it is merged (d95a727), so FIXED.
10. G2 evidence (two failures, or fixed): we used its fix round (fixed, 7,879 passed), because it comes later in the same file.
11. The spacing-mark test (still red, or decided): we used the integration batch and the G text ticket (lead chose option a), because both are newer.
12. The G1 blockers (being fixed, or fixed): we used the G1 fix round (fixed, tests failed before). No independent re-review exists.
13. Whether folding is wired into the secret finder: since d95a727 it is on cloud/core-c (K47 FIXED). Not on main.
14. A failed call's booking ("about an hour", or longer): we used core-b's interface README and T1's expiry case: expiry closes the row but the amount stays booked. Day and month both keep it (worked out).
15. Dash, quote and slash choice: we used ORDER 014 item 9 (accepted).
16. The third-round chain: we used ORDER 020 MJ-B (a capped repeat that refuses), now built (c9478a9).
17. The overshoot example: the test holds three reservations of 1.00; one settles at 2.50: 1.00 + 1.00 + 2.50 = 4.50.
18. Base64 counts (41 of 41, or 52 of 142): both true: rows under 40 characters, and all rows, on the main code.
19. The 3.12 test job: the lead's 3.12 run of old branch P1a had one real failure; the G text ticket reads it as a test slip repaired in the folded code. That repair is UNVERIFIED on a real 3.12.
20. The deliberate code breaks (66 of 66, 24 stale, or 81 of 81): all true at different times. 66 of 66 ran in the pick worktree. 24 went stale. The gate builder recorded 81 of 81 on its edited code (81 = 66 + 15 added). This drafter counted 81 mutant definitions at HEAD; search-text matching at HEAD not checked.
21. The planted-word refusal scope: ORDER 017 item 6 (refuse on any marker word, tool name or call id) versus the builder's narrower rule. We describe the narrower rule, as it is the code in the WIP commits; the lead decides (decision 1).
22. The month cap (round-2 reviewer: not shown to be covered) versus evidence/T1-reserve-cap.md: we used T1, because it lists the case.
23. "If writing the row or settling fails, the reply is still returned" (round-2 reviewer: no test named) versus the gate tests t17 and m2: we used the tests.
24. K12 (dz2-M2 reading: the tail leaks) versus the builder's run (`<SECRET_1><SECRET_2>`, no leak): OPEN, NOT REPRODUCED, until a fresh review.
25. K32 (v2: runtime and reset logins) versus E7 item 5 and B-grants-rework finding 5: we used E7.
26. The producers registry test (v2: red on purpose) versus DECISIONS 07:40 (closed by aa7c5fa): we used DECISIONS.
27. "Verified" merge (d95a727 message) versus the PICK evidence: the batch ran on wip-pick before the merge and before the re-pin. We say "tested before the merge; the merge result was not re-tested".
28. Decision 3's "three questions" (v2) has no source: dropped. The "blocking problems" come from tickets/G4-review-1.md (8 Blockers, 6 distinct).
29. The size of the producers edit: v3 said "four-line"; git show --stat aa7c5fa says 2 lines added. We used git.
30. Gate round 2 batch: c9478a9's message says "302 passed in the gate and install files"; no evidence file holds that result line (F-r3 codebase M5: "evidence has no pytest result"). We keep NOT RUN for the batch and quote the message as a report.
31. c9478a9's title ("code F: gate round 2 fixes") versus its file list (G7 files, no model_gate.py): we date the gate code by the WIP commits (fb08bde last) and the G7 fix round 2 code by c9478a9.
32. The 2026-11-23 date: v3 4.7 said "confirmed by the lead"; neither ORDERS.md nor DECISIONS.md holds it (grep). We say "proposed by core-c, not confirmed in writing".
33. G7-r2 codebase counts: its header says 5 Majors; it lists M2 to M7 (6). We count 6. Also its citation table says the evidence's test counts differ (28 vs 29 non-perf): quoted as the evidence states, the difference noted here.
34. K35's source: G4 v2 cites "order 64 item 4"; ORDERS.md line 64 is ORDER 006 item 1 (build only gaps with a failing input). Source UNVERIFIED; status kept STATED because two written files call it accepted.

### 4.5 Requests to core-b (files in handover/core-c/requests)
1. 1-producers.patch: register the gate as a model caller (applied by core-c as aa7c5fa; decision 7).
2. 2-refused-before-response.md: the "refused before any answer" mark (K20).
3. 3-bind-mapping-required.md: required map, `GateRefused`, empty cost, catch sites, prompt-registry install check (K8, K18, K21). To add (core-c, not done in this file): "one writer per run map" (K17); the judge call sites (K67, F round 4 lane).
4. 4-error-reason-run-map.md: tool-error text with the run map (K42).
5. 5-card-ids-redact-defang.md: id fields on approval messages (K59).
Lead's orders to core-b without a request file: sum the cost of all attempts (ORDER 017 item 3, K23); the worst-case formula (ORDER 016c item 13, K25); an operator release for expired reservations (ORDER 017 item 4); the install test with core-b (ORDER 020 MJ-C). K63 has no request yet: core-c writes one if the lead agrees.

### 4.6 What is still moving at the time of writing (2026-11-20 07:52 UTC)
- Gate fix round 4 (F-result-review-3.md "Round 4 fix agent starts now"; lane: model_gate.py, runmap enforce functions, gate tests, request 3, ticket, evidence): NOT RUN. K3 (alias), K13, K14, K16, K64, K65, K66, K67, K69 depend on it; K10, K11, K15, K16 still need a recorded batch.
- G7 fix round 3 (G7-result-review-2.md "Round 3 fix agent starts now"; lane: redact.py, runmap.redact_text, G7 tests, ticket, evidence): NOT RUN. K39, K41, K68 depend on it. G7-r2 codebase M5 (clock) is in the gate round 4 lane.
- G4 plan v2 (330f4fb, 07:46 UTC): plan review round 2 running; decision 3. Nothing about its result is stated here.
- Fold false-hit measurement (`evrun`): STATUS-BOARD says running; no evidence file (K50).
- Lead verdicts pending: DECISIONS 07:35 (empty-map contest, decision 6; K69) and 07:40 (producers edit, decision 7); decision 1 (framing rule); F-r3 asks the lead about the planted tool-name value (refuse at call, or refuse at registration on core-b's producer side).

### 4.7 INTERNAL: change log of review round 3 (does not ship)

Findings from tickets/SEC-wording-review-3.md, in its order. Kept from rounds 1 and 2 (re-checked, not regressed): verdict first; glossary before part 1; one status per gap; a separate evidence column; three-line gaps; codes only in the appendix; made-up values note; no self-certifying line; FIXED / FIXED ON BRANCH tied to the main line and to review; "Shown by tests" headings and the banner; the 2.2 wording of what the T1 test shows; K2 rule and example; decision 4 "lets more / fewer names pass"; decision 5's five rights; decision 6 reasoning; Part 3 paragraph base (now hedged further); one NOT RUN list; the UnidataMismatch name kept for operators (round 2 contest stands).

Comprehension findings:

| finding | TAKEN / CONTESTED, and where or why |
|---|---|
| 1 Blocker, stop switch sentence | TAKEN: item 28 uses the proposed wording ("In the gate's tests a refused reservation means no call. That the store refuses while the stop switch is on is UNVERIFIED, and no stop of a live run was tested."), plus the three exclusions. |
| 2 "135 files with no failure" | TAKEN: 2.7 now says 2 failures (see 2.0), neither in these path tests, and that their presence in the batch is UNVERIFIED. |
| 3 second failure, FIXED definition | TAKEN: 2.0 names both failures and how each ended (re-pin, then 1 passed alone; registry test closed by aa7c5fa, 25 passed). FIXED redefined: passed in a recorded batch on the builder's copy before saving; the saved code was not re-tested as a whole. |
| 4 UNVERIFIED on K12, K13 | TAKEN: new evidence words NOT REPRODUCED (K12) and MEASURED (K13, plus UNVERIFIED for the unmeasured part), defined in part 0 and in part 2's word box. |
| 5 summary misses NOT RUN items | TAKEN in part: item 5 now lists the gate's fix batch, the merge result and both running fix rounds. CONTESTED for "the capped repeat": its batch has run since v3 (evidence/G7-1.md: 9,681 passed, 0 failed), so it is no longer NOT RUN; only the later sweep-deadline WIP (a2b6311) is, and 2.9 lists it. |
| 6 item 23 cites the wrong item; K24, K26 missing | TAKEN: items 20 (K24) and 21 (K26) added; item 29 says "items 20 and 21"; "item" everywhere, defined in part 0. |
| 7 "a tool states no map" | TAKEN: "the calling code states 'no map'"; "calling code" defined in part 0. |
| 8 measured leaks left out | TAKEN: item 15 ("Also leaking today") names K35, K46, K38 and says why they rank lower (one narrow shape each). K39/K40 tails: K40 is now FIXED, K39 is item 31. |
| 9 "before ... any other outside service" | TAKEN: part 3 and K58 say one test, on 3.13 with the version faked, shows the order for the secrets vault only; other services not checked. |
| 10 STATED with no who or when | TAKEN: STATED now means accepted and written down, with source and date in 4.2; each STATED line in part 2 names the kind of source and date; K19 in item 14 names the lead's frozen plan of 2026-11-20 and tells the owner how to change it. Not made a decision (the reviewer's alternative), because the plan already decided it. |
| 11 K17 STATED with a condition | TAKEN: K17 is OPEN, actor the text and masking team, who adds "one writer per run map" to request 3 (4.5). |
| 12 decisions 1, 3, 5 who / when | TAKEN: decision 1: the lead confirms in DECISIONS.md after round 4's batch; decision 3: the lead drafts the note by 2026-11-23 12:00 UTC and the owner decides on sending (item 6 says so); decision 5: the lead writes the order and the connector and store team changes the rights before any pilot uses the store. CONTESTED in part: for decisions 2, 4 and 6 no source gives a date, so the table says "No date is set" instead of inventing one. |
| 13 K8 PINNED with a core-b ask; "approved list"; v3 log false | TAKEN: the request is its own line ("Related request", WAITING); "prompt registry" defined in part 0 and in K8; v3's log line claiming K8 names no actor is superseded by this table. |
| 14 nit: items 10, 11 lack "main line" | TAKEN: items 11, 12 (old 10, 11) say "on the main line". |
| 15 nit: core-b's other open items; K63 no request | TAKEN: item 2 lists seven items, including the run status (K18) and the 3.12 install (K63, "no written request yet"). CONTESTED in part: the K63 request is not written here, because this task writes one file only; 4.5 says who writes it. |
| 16 nit: UNVERIFIED before certain K19 | TAKEN: K19 is item 14, K42 (UNVERIFIED) is item 16; the order rule in item 4 says so. |
| 17 nit: undefined terms | TAKEN: K10 "supplied its own masking function (allowed for tests)"; K13 "6 seconds"; K38 "the joined branch whose code is now on the shared branch"; K62 "staff admin page" (defined); money in USD everywhere. |
| 18 nit: "starts on 3.12" before hedge; no version check | TAKEN: part 3 puts "NOT RUN on 3.12; this is the design" first and adds `python3 --version`. |
| 19 nit: item 16 hedge first | TAKEN: item 22 starts "That a model connector leaves the cost field empty is UNVERIFIED." |

Style findings (the ticket header says 14 Majors; it lists M1 to M19, all handled):

| finding | TAKEN / CONTESTED, and where or why |
|---|---|
| B1 project words in shipped text | TAKEN: parts 2 and 3 say "the owner", "the connector and store team", "the text and masking team"; decision references are on `[INTERNAL]` lines; the header states the strip step. Checked by search after writing (4.7 note below). |
| M1 lists do not render; "line 18" | TAKEN: every numbered list in part 1 sits under its own heading with a blank line before it; "item N" used. |
| M2 12,392 tests vs 2 failures | TAKEN: 2.0 gives the full result line and how each failure ended. |
| M3 "135 files with no failure" | TAKEN: 2.7 rewritten (see comprehension 2). |
| M4 expected-fail tests; PINNED actor | TAKEN: 2.0 says the strict mark turns the pass into a batch failure and the connector and store team removes the marks; PINNED says "the team that closes the gap then removes the mark". |
| M5 K2 contradicts itself | TAKEN: K2 states that for secrets of 4+ characters the secret rule wins over the digit and common-word exemptions (read in redact.py `_sweep` 1905-1917). |
| M6 evidence words misused; "Evidence: none" | TAKEN: K12 NOT REPRODUCED, K13 MEASURED, K50 NOT RUN for the measurement; NONE defined and used. |
| M7 money without unit | TAKEN: USD on every amount in parts 1 and 2. |
| M8 decision 1 "adds no secrecy" | TAKEN: calibrated ("do not appear to protect more text"; the batch is NOT RUN; both rules still let a planted tool-name secret stop a run). |
| M9 date confirmed or not | TAKEN: item 7 says not confirmed in writing as of 07:52 UTC; v3's log claim was wrong (4.4 item 32). |
| M10 "a tool states no map" | TAKEN: see comprehension 7. |
| M11 part 3 states 3.12 refusal as fact; shared-branch wording | TAKEN: "by design ... NOT RUN on 3.12"; the shared-branch fact moved to an `[INTERNAL]` line; "before ... other service" hedged; "the order" replaced by "the refusal comes before the program builds its connection". |
| M12 "meant not to match" | TAKEN: "designed never to match", under "NOT RUN on 3.12; this is the design". |
| M13 K3 folding is the control | TAKEN: K3 now says the tests show only that the gate does not replace these spellings; the finder's catch is UNVERIFIED. |
| M14 K48 identical example | TAKEN: raw form `abc1`. |
| M15 K52 "very long" | TAKEN: 300,000 characters measured; the shortest refused length NOT RUN. |
| M16 rounds vs calls | TAKEN: part 0 and part 2's box define "search round" and "one call" (up to 5 rounds); 2.5 says one text can go through up to 7 calls (UNVERIFIED). |
| M17 K17, K8 status | TAKEN: see comprehension 11 and 13. |
| M18 K59 Slack claim | TAKEN: example marked UNVERIFIED, "could", not tried on Slack. |
| M19 dangling references in part 2 | TAKEN: "decision N" only on `[INTERNAL]` lines; "part 3" became "see README, section Python version"; "part 0" removed; part 2's word box now covers all marks. |
| N1 part 1 audience | TAKEN: header line 4. |
| N2 "10 of the open gaps" | TAKEN: part 0 note: 15 OPEN plus a batch for 4 FIXED ON BRANCH. |
| N3 items lack "main line" | TAKEN: see comprehension 14. |
| N4 summary NOT RUN incomplete | TAKEN: item 5 matches 2.9. |
| N5 jargon | TAKEN: "clock" -> time limit; "byte for byte" -> unchanged; "safe side" -> over-counts, never under-counts; "colour codes" -> control codes terminals use for colours; "within K40" -> "(K40)"; "not text" -> content that is not text; "audit marks" kept only in 2.0 as a named fix list; "glued" defined; "cleaning" -> masking; "an unique id" -> a unique id. |
| N6 one word per thing | TAKEN: placeholder (no "stand-in"); mask (no "swept", "replaced" only where the gate's replace step is meant); identifier; empty cost field vs unreadable cost defined. |
| N7 K13 / K41 before-after | TAKEN: K13 before (600 seconds possible, worked out) and after (0.018 seconds, measured); K41 0.167 -> 0.395 seconds. |
| N8 K16 example is a rule | TAKEN: concrete example. |
| N9 K18 example | TAKEN: example shows the "working" status. |
| N10 K29 "safe side" | TAKEN. |
| N11 "(by decision)"; "today's SECURITY.md" | TAKEN: K35 source on an `[INTERNAL]` line (UNVERIFIED source, 4.4 item 34); K46 "the SECURITY.md on the main line since 2026-11-04". |
| N12 UTC in 4.1, 4.6 | TAKEN. |
| N13 "shared busy machine", "at once" | TAKEN: "the builder's test machine" (the evidence says "this machine"); "50 separate database connections, started together". |
| N14 66 became 81 | TAKEN: "updated those 24 and added 15 new ones, 81 in all". |

Facts changed since v3 (read from the repo, not from the reviews): G7 fix round 2 committed (c9478a9) with its batch; a2b6311 WIP; G7-r2 findings (K39, K41, K68 and K13's clock); F-r3 findings (K3, K11, K14, K16, K64-K67, K69); G4 v2 ticket (decision 3); working copy clean; aa7c5fa is 2 lines.

Contested in all: 4 findings in part (comprehension 5 on the capped repeat; comprehension 10 on making K19 a decision; comprehension 12 on dates for decisions 2, 4, 6; comprehension nit 15 on writing the K63 request here). Each with its reason above.

Check after writing: a search of parts 2 and 3 (minus `[INTERNAL]` lines) for "lead", "core-b", "core-c", "incident", "refund", "invoice", "intake" found none.
