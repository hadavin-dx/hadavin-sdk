# Security wording v5: what the tests show and what is still open

DRAFT, version 5, written by core-c's drafter on 2026-11-20. It replaces SECURITY-README-v4.md. It answers review round 4 (tickets/SEC-wording-review-4.md).

Who reads what: part 0 and part 1 are for the owner only. Part 2 ships as SECURITY.md. Part 3 ships as README.md, section "Python version". Part 4 is internal and does not ship.

Strip step before shipping, for whoever copies the text:

1. Copy part 2 into SECURITY.md. Start at its heading. Stop before the `---` line that comes before part 3.
2. Copy part 3 into README.md. Start at its heading. Stop before the `---` line that comes before part 4.
3. In both copies, delete every line whose text starts with `[INTERNAL]`. Ignore any list dash and spaces in front of it.
4. Delete nothing else.

After step 3, parts 2 and 3 name no project, team code or session. They say "the owner", "the connector and store team" and "the text and masking team".

This draft changes no other file.

---

## 0. Plain glossary (read this first)

As of 2026-11-20 08:09 UTC (repository head 6b990d9).

### How to read the marks (one list)

Evidence words (how we know). Every claim carries one of these:

- **TESTED**: a named test ran and passed in a recorded batch of tests. A recorded batch is one whose result line is in an evidence file.
- **MEASURED**: a recorded run measured the number given.
- **UNVERIFIED**: the only basis is someone reading the code or the text. Nothing was run to show it.
- **NOT REPRODUCED**: a reviewer reported a fault from reading. A builder then ran the reported case and did not see the fault. No fresh reviewer has checked the builder's run.
- **NOT RUN**: the check was not run at all, or no recorded result exists. Nothing is claimed about its result.
- **NONE**: no test, run or reading is named. The gap is written down from a plan, an order or the published SECURITY.md only.

Status words (one per known gap):

- **FIXED**: changed, and a test fails without the change. The change is on the shared branch. A recorded batch that holds that test passed on the builder's copy of the code, before it was saved. The code as saved was not re-tested as a whole. It is not on the product's main line. No independent reviewer has passed it.
- **FIXED ON BRANCH**: changed, and the builder showed that a test fails without the change. The change is saved on the shared branch, but no recorded batch covers it. No independent reviewer has passed it.
- **PINNED**: not fixed, on purpose. A named test fails if the behaviour changes. This includes a "strict expected failure": a test that records the gap and fails once the gap closes. The team whose change closes the gap removes that mark. For the three install tests, that is the connector and store team.
- **STATED**: accepted and written down, with no test. The source is a plan, an order, a ticket, an evidence file or the published SECURITY.md or README.md. Each STATED line names its source and date. Nobody is asked to act.
- **WAITING**: another team must act, and a written request or a written order exists.
- **OPEN**: nobody has fixed or decided it yet. The line names who must act.

Every example value in this file is made up. None is a real secret.

### People and teams

- **The owner**: the person who owns Hadavin, pays for the work and has the final say.
- **The lead**: the coordinating session (software, not a person) on the owner's laptop. It writes the orders and records verdicts. The owner decides the seven questions in part 1a. The lead is named in parts 0, 1 and 4 only.
- **DECISIONS.md**: the text and masking team's written record of its choices. The lead writes its verdict in one column of it.
- **The connector and store team** (internal code: core-b): the build team that owns the model connectors, the store, the agent loop and the approval-message code. It must install the gate.
- **The text and masking team** (internal code: core-c): the build team that built the gate, the secret finder changes and text folding. It wrote this file.
- **Builder**: a worker of the text and masking team that writes code and runs the tests. **Reviewer**: an independent checker. Reviewers only read; the builders ran the tests.
- **Operator**: the person who installs and runs the kit for a client.
- **Gate fix round 4**: the gate's current round of fixes, for the faults its third review found. It is running now. **Secret finder fix round 3**: the secret finder's current round of fixes. It is running now. Nothing about their results is said here.
- Note: the text and masking team wrote this file. It must act on 15 OPEN gaps. It must still run a recorded batch for the 4 FIXED ON BRANCH gaps (4.3). Independent reviewers read version 4. Nobody outside the team has checked these statuses against the code.

### Product words

- **The kit**: this software package (the Hadavin SDK) that client projects are built on.
- **Stages**: there are only three. Demo shows the product with made-up data. Pilot is a first, limited use with a real client. Prod is normal live use.
- **Model**: the outside AI service that reads text and answers. A **model call** is one request to it.
- **System prompt**: the standing instructions sent with each model call.
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
- **Mask**: put a placeholder where a sensitive value was. **Placeholder**: a fixed text such as `<SECRET_1>` that the model sees in place of the value. (This file uses only these two words for this.)
- **Run map**: one table per run, kept in memory, that records which real value each placeholder stands for. **Restore**: put the real value back in place of a placeholder, for a tool that needs it.
- **Secret finder**: the code that searches text for sensitive values by their shape and masks them. There is one secret finder. It runs where text enters a run (tool results, documents, approval messages). Only it adds to the run map.
- **Search round**: one pass of the secret finder's patterns over the text, then one masking of every copy of the known values. **One call of the secret finder** runs up to 5 search rounds.
- **Kind**: the type the secret finder gives each value it finds. Secret kinds: passwords, keys, tokens. Identifier kinds: e-mail, host name, IP address and the like.
- **Withheld**: the secret finder hides a whole line it cannot mask in place, and shows a fixed note.
- **Glued**: written directly against another character, with no space between.
- **Fail closed**: when in doubt, refuse the text or the call rather than let it through.
- **Text folding**: turning look-alike letters, invisible characters and accents into one plain spelling before searching. Look-alike letters are, for example, full-width letters and Cyrillic letters that look Latin.
- **Unicode**: the world standard list of characters. Each Python version carries one edition of it.
- **base64**: a common way of writing any data as letters and digits.
- **The gate**: one wrapper meant to sit in front of every model call. It masks known values, reserves money, makes the call, settles and writes an audit row. It searches for no new values.
- **Installed**: placed at every point in the code that calls a model. The gate is NOT installed yet.
- **Held back**: a known value at a placeholder's edge (it starts with `>` or ends with `<`). The gate masks it last, so the placeholder text stays whole. **Safety net**: the gate's last check, which refuses the call if a held-back secret is still readable.
- **Framing marker**: the fixed line the agent loop puts around each tool result, so the model sees where tool output starts. It holds fixed words, the call number and the tool's name. A **forged marker** is a copy of that line written by planted text.
- **Planted-instruction check**: the check that looks for planted orders such as "ignore previous instructions". **Guard failure**: its report that it could not finish.
- **Grounding check**: the check that a name an agent proposes to act on appears in a tool result it cites.
- **Judge**: a model call that rates a text. The planted-instruction check and the approval code use it. It is a model call and must go through the gate too.
- **Prompt registry**: the fixed list of system prompts that ship with the kit.
- **Approval message**: the message that asks a person to approve an action an agent proposes.
- **Slack**: the chat service where approval messages are posted.
- **Admin page**: the staff web page that shows stored approval summaries.

### Money words

All amounts are in US dollars (USD).

- **The store**: the database that records spending, reservations, the stop switch and the audit record. (The place secrets are kept is called the **secrets vault**.)
- **Cap**: the most money one agent may spend in a day and in a month.
- **Worst case**: the most a model call could cost. The connector and store team's code must compute it.
- **Reserve**: before a call, count its worst case against the cap. **Settle**: after the call, book the real cost instead of the worst case. **Booked**: the amount counted against the cap at any moment.
- **Empty cost field**: a reply whose cost was never filled in. It reads as 0.00 USD. **Unreadable cost**: a cost that is absent, negative or not a number.
- **Price table**: the list of prices per AI service used to work out the worst case.
- **Stop switch**: a flag in the store. While it is on, the store is meant to refuse every new reservation. A **stop record** says who turned it on.
- **Database login**: a named account the software uses to reach the store. There are three: runtime, purge and reset. Each has its own rights.

### Record and code words

- **Audit row**: one line in the permanent record of what happened. It holds short codes, not message text.
- **Refusal word**: the exact short word the gate or store prints when it refuses. The words are listed in the appendix (4.1).
- **The shared branch**: the text and masking team's pushed line of changes, from which the lead takes code. **The product's main line**: what clients get. Nothing of this work is on the main line.
- **Work-in-progress commit**: changes saved to the shared branch before their tests ran.
- **Test**: a small program that checks one behaviour and fails when it changes. **Batch**: one recorded run of many tests.
- **Deliberate code break**: a planted fault in the code, used to prove a test can fail.
- **Known gap**: a weakness we know about, or a gap fixed in this work. Each has a number K1 to K69, used in parts 2 and 4. Part 1 uses no K numbers.
- **Item**: one numbered line of part 1.

---

## 1. Owner summary

As of 2026-11-20 08:09 UTC.

### What to know first

1. **Short answer: the gate is written but not installed. No agent in use goes through it. Do not promise a client any gate protection yet.**
2. TESTED: the gate's own tests passed in a recorded batch. That batch ran before the gate's second-review fixes. Its one failure was the list of code that calls a model, which did not name the gate yet.
3. UNVERIFIED (reported in a commit message and DECISIONS.md, not in an evidence file): a later two-line change closed that failure.
4. Reviewers keep finding faults. UNVERIFIED (two reviewers' reading): the gate's third independent review found 9 major faults and no blocking one. Gate fix round 4 is fixing them (NOT RUN).
5. The connector and store team must write the worst-case formula, add the "refused before any answer" mark and install the gate. It also has seven other open items:
   - empty cost fields;
   - retried calls;
   - tool-error text;
   - approval-message id fields;
   - the run's status after a refusal;
   - a start-up check that system prompts come only from the prompt registry;
   - installs on Python 3.12, which has no written request yet.
6. The text and masking team must finish gate fix round 4 and secret finder fix round 3 (both running). Then it must run their test batches and get a fresh review.
7. This summary names 28 of 69 known gaps. The groups come in this order: secrets that can reach the AI service, then money, then wrong actions, stopped work and set-up.
8. Within a group, the order is a rough judgement. Wider exposure comes first. Where two gaps are about as wide, a tested or measured one comes before an UNVERIFIED one.
9. NOT RUN on this work's code:
   - the full test suite;
   - Python 3.12;
   - database version 17, the version the automatic test service is set to use (the tests here ran on version 16.15);
   - any live call to an AI service;
   - any end-to-end stop of a live run;
   - 238 of the 240 deliberate code breaks for text folding (the 2 that ran cover one rule about accent marks);
   - a recorded batch for the gate's second-review fixes;
   - the merged code as a whole;
   - gate fix round 4 and secret finder fix round 3.
10. **Your action (the owner):** read the seven decisions in 1a. Answer the lead by 2026-11-23 12:00 UTC. For each decision, keep the default or choose another answer.
11. If you have not answered by then, each default in 1a applies. Silence on decision 3 means the client note is not sent. The lead records each answer, or each default, in DECISIONS.md.
12. The text and masking team proposed this date. As of 08:09 UTC the lead has not confirmed it in writing (searched in ORDERS.md and DECISIONS.md).
13. Today an agent in use is protected only by the secret finder as it is on the product's main line, without this work's changes.
14. Installing the gate and passing a fresh review will not be enough. The gaps below stay until each one is closed.

### Secrets that can reach the AI service (worst first)

15. NONE (written in the published README since 2026-11-04): a secret in a shape the secret finder does not know goes out as written. This stays after install too.
16. MEASURED on the main line: short base64 text, under 40 characters, is not masked. 41 of 41 such test lines leaked.
17. MEASURED on the main line: host names without a "host" label are not masked. 28 of 44 test lines leaked. Decision 3 covers this item and item 16.
18. TESTED: the gate never masks the system prompt or the tool descriptions.
19. UNVERIFIED (read in the install test's table of calls kept outside the gate): the guardrail call goes around the gate. It is neither masked nor counted against the cap.
20. The lead's frozen plan of 2026-11-20 accepts item 19. Tell the lead if you want it changed.
21. Also leaking today, each in one narrow shape, so they rank below items 15 to 20:
   - MEASURED on the main line: a bare number with no label is often not masked. 24 of 43 test lines were not masked.
   - Two written files call that bare-number gap accepted. The written order they cite as the acceptance was not found. So that acceptance is UNVERIFIED.
   - NONE (written in the published SECURITY.md since 2026-11-04): a secret that holds a space, `;`, `,` or `&` is masked only up to that character.
   - MEASURED: an IP address, phone number, international bank account number or unique id with a letter or `_x` glued behind it is not masked.
22. UNVERIFIED (read from the code, not run): a secret first seen in a tool's error message is not masked in later text. It waits on the connector and store team.
23. UNVERIFIED (reviewers' reading): three more leak paths. Their fixes are in gate fix round 4 (NOT RUN).
   - The gate's safety net checks only held-back values.
   - A known value inside a tool's name is masked in one place but not in the tool list.
   - The hand-over list for the install misses the judge's call points.

### Money (worst first)

24. NOT RUN (nothing to test yet): nobody has written the worst-case formula. Until the connector and store team writes it, the cap has nothing real to reserve.
25. TESTED: the gate does not settle a failed call, so its worst case stays booked.
26. UNVERIFIED (worked out from the store's rules, not run): that amount stays booked for the rest of the day and month. With a cap of 3.00 USD and a worst case of 1.00 USD, three failed calls stop an agent.
27. TESTED: booked money can pass the cap, on purpose. A call that costs more than its worst case is booked in full.
28. In that test, three reservations of 1.00 USD meet a cap of 3.00 USD. One settles at 2.50 USD. Then 4.50 USD is booked.
29. TESTED (the gate's side only): a reply with an empty cost field is booked as free. UNVERIFIED: that a model connector ever leaves the field empty.
30. UNVERIFIED (read from the code): when a call is retried, only the last attempt's cost is counted. Earlier billed attempts are lost, so spending is understated.
31. UNVERIFIED (read from the database set-up code): the database does not stop two of the software's own logins. The runtime login can lower a reservation. The purge login can delete an open one. Decision 5 covers it.

### Wrong actions, stopped work and set-up

32. UNVERIFIED (two reviewers' reading): after the secret finder undoes a half-made entry, a later placeholder can be restored to the wrong real value. A tool could then get the wrong account or credential.
33. Item 32 sends nothing raw to the AI service, so it ranks below the secrets group. Its fix is in secret finder fix round 3 (NOT RUN).
34. UNVERIFIED (read from the database set-up code): the runtime login can sign a stop record with any name. So the record of who turned the stop switch on cannot be trusted. Decision 5 covers it.
35. Planted text can make a run's later tool-using calls refuse, if it plants a secret equal to a tool's name. UNVERIFIED (a reviewer's reading): this still happens under the narrower rule. Decision 1 covers it.
36. UNVERIFIED (a reviewer's reading): planted text with more than 256 values at a placeholder's edge makes every later call of that run refuse.
37. UNVERIFIED (a reviewer's estimate, not run): hostile text can make one gate call run far past its time limit. The estimate is about 128 million steps for one text of 262,144 characters.
38. MEASURED: one call of the secret finder on a text built to be slow took 4.00 seconds, within its 6-second limit. UNVERIFIED (a reviewer's reading): one call can take its limit plus one whole search round.
39. Once the text-folding change ships: by design, a pilot or prod install on Python 3.12 succeeds, and then the program refuses to start. NOT RUN on Python 3.12.

### Shown by tests (each in the teams' own tests, on the code alone)

40. TESTED: in the gate's tests, known values are masked before a call, in message text and documents only. They are not masked when the calling code states "no map".
41. TESTED: only the test and replay command lines may state "no map".
42. TESTED: in the gate's tests a refused reservation means no call. UNVERIFIED: that the store refuses while the stop switch is on. NOT RUN: any stop of a live run.
43. Item 42 does not cover a call already in flight, the test and replay command lines, or the guardrail call.
44. TESTED, twice, on database version 16: 50 separate database connections, started together, asked for reservations. The cap was 3.00 USD and each worst case 1.00 USD. 3.00 USD was reserved and 47 requests were refused.
45. Booked money can still pass the cap (items 27 and 31).
46. TESTED: in the gate's tests, its code holds no message or error text, and no audit row in those tests held a secret.
47. TESTED: in the secret finder's tests, a chain of planted values that needs a third search round is now masked. UNVERIFIED: which saved version of the code that batch ran on.
48. UNVERIFIED (a reviewer's reading): a case the repeated search may skip. Its fix is in secret finder fix round 3 (NOT RUN).

### 1a. The seven decisions (the owner decides each one by 2026-11-23 12:00 UTC)

If there is no answer by then, the default in the fourth column applies. The last column says who then acts. No build date is set for any of them; the owner may ask for one.

| # | Question | What each answer means | Default if no answer | Who then acts |
|---|---|---|---|---|
| 1 | Planted text can make a known value equal part of a framing marker. When should the gate refuse the call? | Narrower rule: refuse only when a known secret of 4 or more characters equals a tool's name or a call number. It is saved on the shared branch; its batch is NOT RUN. Wider rule (the lead's earlier order): also refuse when any known value equals a fixed marker word. A reviewer proposes a third way: never store a tool's name as a secret when the secret finder adds it. UNVERIFIED that this closes the gap. | The narrower rule. Why: UNVERIFIED (read from the code; its batch is NOT RUN): under both rules the marker's fixed words stay exact. So the wider rule's extra refusals do not appear to protect more text, and they stop more runs. Both rules still let a planted secret equal to a tool's name stop a run (item 35). | The text and masking team keeps the narrower rule in the code. Gate fix round 4 may touch this code. The lead records the result in DECISIONS.md. |
| 2 | Should each audit row also say whether anything was masked, and which route was used? | Without it, nobody can tell from the record whether masking happened. Today the row says only how the run map was used: a map, an empty map, or no map. | Add a "masked: yes or no" field and the route. No text goes in the row. | The text and masking team builds it in a gate fix round after gate fix round 4. |
| 3 | Build the planned host-name and base64 change, or keep both as known gaps for now? | Keeping them means such values reach the AI service (items 16, 17). Plan reviewers found 6 distinct blocking problems in the first plan. Version 2 of the plan was reviewed at 07:59 UTC. Both of its reviewers found blocking problems too. Version 3 is being written. | Keep both as known gaps until a plan review is clean. Do not send the client note. | The lead sends a draft client note on both gaps by 2026-11-22 12:00 UTC. The owner says by 2026-11-23 12:00 UTC whether to send it. Once a plan review is clean, the text and masking team builds. |
| 4 | Accept that the grounding check now counts a name as present in more cases in Korean, Japanese and Indian scripts? | This happens when an invisible character splits the name. Accepting lets more proposed names pass the check, with no tests for those scripts. | Go back to the older rule for those scripts until tests exist. The older rule lets fewer names pass. | The text and masking team makes the change in its next text-folding round. |
| 5 | Tighten five wide database rights, or accept them in writing? | Runtime login: can rewrite a reserved amount, and can sign a stop record with any name. Purge login: can delete an open reservation. Reset login: can change any stop-switch row, and can add any audit row. Accepting leaves the cap and the stop record resting on code alone. | Tighten them: narrower rights, or one fixed database function per action. | The lead writes the order. The connector and store team changes its database rights in its next store change, before any pilot uses the store. |
| 6 | Should the gate refuse a call whose run map is empty? Or should it accept the call and mark the audit row? | The lead's written order says refuse. UNVERIFIED (read at the repository head): today's code on the shared branch accepts and marks the row. The text and masking team asked to keep that. Refusing stops each run whose first document held no value the secret finder found. Either way the gate masks nothing in that call. A secret the finder missed goes out in both cases. A reviewer also read that the gate does not check that the map is the run's own map (UNVERIFIED). | Refuse, as the written order says. It is the stricter choice. | The text and masking team changes the code to refuse. It also adds the check that the map is the run's own. |
| 7 | Accept the text and masking team's changes to two of the connector and store team's files, or have that team redo them? | The files are the Slack approval-message file and the list of code that calls a model. The list now names the gate; that is a list entry, not an install. Two teams editing one file can collide. | Accept both. Either change can be undone with one commit. | The lead tells the connector and store team in its next order. |

---

## 2. For SECURITY.md: "What the tests show and what is still open"

As of 2026-11-20 08:09 UTC.

> **These items describe what tests showed on the gate, the secret finder and the store, each run on its own. None of this describes an agent in use going through the gate. The shared branch is not the product's main line.**

### Words used here (this part ships alone)

Evidence words. Every claim carries one of these:

- TESTED: a named test ran and passed in a recorded batch of tests. A recorded batch is one whose result line is in an evidence file.
- MEASURED: a recorded run measured the number given.
- UNVERIFIED: the only basis is someone reading the code or the text. Nothing was run to show it.
- NOT REPRODUCED: a reviewer reported a fault from reading. A builder then ran the reported case and did not see the fault. No fresh reviewer has checked the builder's run.
- NOT RUN: the check was not run at all, or no recorded result exists. Nothing is claimed about its result.
- NONE: no test, run or reading is named. The gap is written down from a plan, an order or the published SECURITY.md only.

Status words (one per known gap):

- FIXED: changed, and a test fails without the change. The change is on the shared branch. A recorded batch that holds that test passed on the builder's copy of the code, before it was saved. The code as saved was not re-tested as a whole. It is not on the main line. No independent reviewer has passed it.
- FIXED ON BRANCH: changed, and the builder showed that a test fails without the change. The change is saved on the shared branch, but no recorded batch covers it. No independent reviewer has passed it.
- PINNED: not fixed, on purpose. A named test fails if the behaviour changes. This includes a "strict expected failure": a test that records the gap and fails once the gap closes. The team whose change closes the gap removes that mark.
- STATED: accepted and written down, with no test. Each STATED line names its source and date. Nobody is asked to act.
- WAITING: another team must act, and a written request or a written order exists.
- OPEN: nobody has fixed or decided it yet. The line names who must act.

People and code:

- The owner: the person who owns Hadavin and has the final say. The owner decides the open questions named below.
- The connector and store team: the team that owns the model connectors, the store, the agent loop and the approval-message code. It must install the gate.
- The text and masking team: the team that built the gate, the secret finder changes and text folding.
- Builder: a worker of the text and masking team that writes code and runs the tests. Reviewer: an independent checker who only reads.
- Operator: the person who installs and runs the kit for a client. The kit: this software package. Stages: demo (made-up data), pilot (a first, limited use with a real client) and prod (normal live use).
- The shared branch: the text and masking team's pushed line of changes. The main line: what clients get. A work-in-progress commit holds changes saved before their tests ran.
- Test: a small program that checks one behaviour. Batch: one recorded run of many tests. Deliberate code break: a planted fault in the code, used to prove a test can fail.
- Kn: the number of a known gap in this list. A known gap is a weakness we know about, or a gap fixed in this work.

Model and run words:

- Model: the outside AI service that reads text and answers. A model call is one request to it. The system prompt holds the standing instructions sent with each model call.
- Guardrail call: a separate request to the cloud vendor's safety service. It is not a model call.
- Route: which AI service and which model a call goes to. Model connector: the code that talks to one AI service and reports the cost of each call.
- Run: one job of one agent, from start to finish. The agent loop is the code that drives a run step by step.
- Tool: an action an agent may use, such as a search. A tool result is the text a tool returns. Each tool call gets a call number. The tool list holds the tools' names and descriptions, sent with a model call.
- Calling code: the program code that hands a call to the gate. Test and replay command lines: two staff programs that run saved test cases or re-play a stored run.
- Judge: a model call that rates a text. The planted-instruction check and the approval code use it. Prompt registry: the fixed list of system prompts that ship with the kit.
- Planted text: text an attacker put into a document or tool result so that the agent reads it.
- Planted-instruction check: the check that looks for planted orders such as "ignore previous instructions". Guard failure: its report that it could not finish.
- Grounding check: the check that a name an agent proposes to act on appears in a tool result it cites.
- Approval message: the message that asks a person to approve an action an agent proposes. Slack: the chat service where approval messages are posted. Admin page: the staff web page that shows stored approval summaries.

Masking words:

- Sensitive value: a secret (password, key, token) or an identifier (e-mail address, host name, account number). Known value: a sensitive value already in the run map.
- Mask: put a placeholder where a sensitive value was. Placeholder: a fixed text, such as `<SECRET_1>`, that the model sees in place of the value.
- Run map: one table per run, kept in memory, that records which real value each placeholder stands for. Restore: put the real value back for a tool that needs it.
- The secret finder: the code that searches new text for sensitive values by their shape and masks them. Only it adds to the run map.
- Search round: one pass of the secret finder's patterns, then one masking of every copy of the known values. One call of the secret finder runs up to 5 search rounds.
- Kind: the type the secret finder gives each value it finds, such as password, key, token, e-mail or host name.
- Withheld: the secret finder hides a whole line it cannot mask in place, and shows a fixed note. Glued: written directly against another character, with no space between.
- Fail closed: when in doubt, refuse the text or the call rather than let it through.
- Text folding: turning look-alike letters, invisible characters and accents into one plain spelling before searching. Unicode: the world standard list of characters; each Python version carries one edition of it.
- base64: a common way of writing any data as letters and digits.
- The gate: one wrapper meant to sit in front of every model call. It masks known values, reserves money, makes the call, settles and writes an audit row. It searches for no new values.
- Installed: placed at every point in the code that calls a model. The gate is not installed yet.
- Held back: a known value at a placeholder's edge (it starts with `>` or ends with `<`). The gate masks it last. Safety net: the gate's last check, which refuses the call if a held-back secret is still readable.
- Framing marker: the fixed line the agent loop puts around each tool result. It holds fixed words, the call number and the tool's name. A forged marker is a copy of that line written by planted text.

Money and record words:

- All amounts are in US dollars (USD).
- The store: the database that records spending, reservations, the stop switch and the audit record. The secrets vault is the separate place where secrets are kept.
- Cap: the most money one agent may spend in a day and in a month. Worst case: the most a model call could cost.
- Reserve: before a call, count its worst case against the cap. Settle: after the call, book the real cost instead of the worst case. Booked: the amount counted against the cap at any moment.
- Empty cost field: a reply whose cost was never filled in; it reads as 0.00 USD. Unreadable cost: a cost that is absent, negative or not a number.
- Price table: the list of prices per AI service used to work out the worst case.
- Stop switch: a flag in the store. While it is on, the store is meant to refuse every new reservation. A stop record says who turned it on.
- Database login: a named account the software uses to reach the store. There are three: runtime, purge and reset.
- Audit row: one line in the permanent record of what happened. It holds short codes, not message text. Refusal word: the exact short word the gate or store prints when it refuses.

### 2.0 State of the work

- WAITING: the gate is not installed. No point in the code that calls a model goes through it yet. The connector and store team must install it.
- NONE (the project's written order of 2026-11-20 06:30 UTC): the connector and store team will not install the gate before the model connectors can say "refused before any answer".
- TESTED: the gate tests named in 2.1 to 2.4 passed in a recorded batch. That batch ran before the gate's latest fixes.
- NOT RUN: the gate's latest fixes are saved on the shared branch, but no recorded batch covers them.
- UNVERIFIED (read in the test file): three install tests are marked as strict expected failures until the gate is installed. Once it is installed, they pass, and that pass fails the batch. Then the connector and store team removes the three marks.
- UNVERIFIED (a reading by two reviewers): the gate's third independent review found 9 faults it rates as major and none it rates as blocking. Their fixes are NOT RUN.
- [INTERNAL] Gate tests behind 2.1 to 2.4: the batch "1 failed, 2307 passed, 2 xfailed" (evidence/F-G0-1.md line 244). The failure was tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered.
- [INTERNAL] That failure was closed by aa7c5fa at 07:36 UTC (2 lines in guard/producers.py, core-b's file). "25 passed" is in the commit message and DECISIONS 07:40 UTC only.
- [INTERNAL] Merged into cloud/core-c at 07:28 UTC (d95a727): the approval-message fixes, the glued e-mail fix, the look-alike search in the secret finder and its second search round.
- [INTERNAL] Before that merge, a builder ran 135 test files on wip-pick: 12,392 passed, 2 failed, 108 skipped, 7 xfailed. The merge result as a whole was not re-tested (NOT RUN).
- [INTERNAL] Failure 1 was tests/test_redact_fold_budget.py::test_dm_2_257_...; the builder re-pinned it (cfda4d0); it then passed alone. Failure 2 was the producers test, closed by aa7c5fa.
- [INTERNAL] The gate's second-review fixes are in WIP commits; fb08bde last changed model_gate.py. c9478a9's message reports "302 passed" and 81 of 81 mutants. Its files are mostly G7 code (DECISIONS 08:05 UTC).
- [INTERNAL] Third gate review: tickets/F-result-review-3.md (design 0 B, 4 M; codebase 0 B, 5 M). Gate fix round 4 is running: NOT RUN.
- [INTERNAL] G7 second review: tickets/G7-result-review-2.md (codebase 1 B, 6 M; design 0 B, 5 M). Secret finder fix round 3 is running: NOT RUN.
- [INTERNAL] The 9,681-test G7 batch (evidence/G7-1.md) was committed at 07:44 UTC (0fcc5e1), after a2b6311 (07:41 UTC). Its code version is not recorded.
- [INTERNAL] a2b6311 (sweep deadline argument, WIP) has its own test; no batch is known to cover it (NOT RUN).

### 2.1 Masking before a model call (the gate)

Shown by tests (TESTED here means: in the gate's recorded batch, run before its latest fixes):

- TESTED: before a call, the gate masks each known value with its placeholder. This covers message text and documents only. K8 lists what it skips.
- TESTED: the gate searches for no new values. The secret finder does that (K1).
- TESTED: if masking fails, the gate makes no call and reserves no money. Causes: text too long, content that is not text, out of time, or text still changing after 4 maskings.
- TESTED: that refusal carries a refusal word and no text.
- TESTED: if no known value is present, the text goes out unchanged.
- TESTED: the gate does not change the calling code's messages, documents or run map.
- TESTED: the calling code must name a run map or state "no map". Leaving it out is an error. Only the test and replay command lines may state "no map" (K9).
- TESTED: in a recorded run on the builder's copy before the latest fixes, the tests caught each of 66 deliberate code breaks.
- UNVERIFIED (one recorded run, not repeated): on the edited code, the tests caught each of 81 deliberate code breaks.
- [INTERNAL] 66 of 66 ran on wip-pick. 24 then matched no code; the builder updated them and added 15 (81). evidence/F-G0-1.md records "81 of 81 good". This drafter counted 81 at HEAD.

Known gaps and fixed findings:

- **K1. Not protected:** a secret the secret finder never found.
  - Example: a raw `hunter2zz` that no shape matched goes out as written.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody; the secret finder is the control.
- **K2. Not masked, even when known:** any value under 3 characters. Three more cases apply to an identifier and to a secret of exactly 3 characters. They are an all-digit value under 6 characters, a common word (`admin`, `test`), and any copy that a letter or digit touches.
  - Example: the known identifier `abc123` (an account number, not a secret) stays readable inside `xabc1234`, because a letter touches it.
  - Rule: a secret of 4 or more characters is masked wherever its exact text appears, except as K3 to K7 describe. This holds even when it is all digits or a common word.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K3. Not masked by the gate:** a copy spelled differently from the run map. Such spellings include percent codes, web character codes, look-alike letters, hidden characters and the control codes terminals use for colours.
  - Example: known `qrs789`; the text `qrs&#55;89` (a web code for the digit 7) goes out as written.
  - Status: PINNED. Evidence: TESTED (the gate does not mask these spellings). Who acts: nobody on the gate.
  - UNVERIFIED: whether the secret finder's text folding catches each such copy.
  - UNVERIFIED (a reviewer's reading): the gate does mask some other spellings of known values written in non-Latin letters.
  - [INTERNAL] Gate fix round 4 either tests the non-Latin spellings or writes them down (F-r3 codebase M2).
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
  - [INTERNAL] Separate request, WAITING on core-b: a start-up check that system prompts come only from the prompt registry (requests/3-bind-mapping-required.md section 6; ORDER 020 MJ-D).
- **K9. Not masked:** anything, when the calling code states "no map".
  - Example: a replay of an old run sends its text as stored.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K10. Fixed on branch:** the audit row said "map in use" when the map was empty. It also said so when the calling code had supplied its own masking function (allowed for tests). The row now says which.
  - Example: a run with an empty map now writes "map empty", not the same row as one with 50 values.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (no recorded batch). Who acts: the text and masking team (a batch, then a fresh review).
- **K11. Fixed on branch:** a known secret inside a forged marker went out unmasked. Now the gate keeps only the marker's fixed words and masks the rest.
  - Example: a document holds a forged marker whose call number contains the known `S3cr3tPw`. Before this fix, `S3cr3tPw` went out.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (no recorded batch). Who acts: the text and masking team (a batch).
  - The builder reproduced the leak before the fix. UNVERIFIED (a reviewer's reading): the fix closes it.
- **K12. Reported, not reproduced:** a secret at a held-back value's edge may leak its tail.
  - Example: known `S3cr3t` and `>abcdef`. A reviewer read that `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`. A builder ran it and got `<SECRET_1><SECRET_2>`, with no leak.
  - Status: OPEN. Evidence: NOT REPRODUCED. Who acts: the text and masking team (a fresh reviewer checks the builder's run).
  - NOT RUN: a safety net that refuses such a call is saved on the shared branch, in no recorded batch.
- **K13. Not limited:** the total time the gate spends on one model call. One time and size budget per call now exists. The final masking step inside it has no time limit.
  - Example: UNVERIFIED (worked out, not run): before the change, 100 messages at 6 seconds each could take 600 seconds. MEASURED after the change: 100 messages against a run map of 2,000 entries took 0.018 seconds.
  - Status: OPEN. Evidence: MEASURED (that one case). Who acts: the text and masking team.
  - UNVERIFIED (read from the code): the final masking step gets no time limit from the gate, and the two parts use different clocks.
  - UNVERIFIED (a reviewer's estimate, not run): one hostile text of 262,144 characters with 500 planted values needs about 128 million steps in that step.
  - [INTERNAL] In gate fix round 4 (NOT RUN). Clock mismatch: G7-r2 codebase M5.
- **K14. Not protected:** a run's later tool-using calls. A planted secret that equals a tool's name or a call number makes each of them refuse.
  - Example: a tool result contains `password=search_web`, where `search_web` is a tool's name. Later calls in that run refuse.
  - Status: OPEN. Evidence: TESTED (the earlier, wider rule); NOT RUN (the narrower rule, no recorded batch).
  - UNVERIFIED (a reviewer's reading): the narrower rule still refuses in this example.
  - Who acts: the owner decides which rule. If no answer arrives by 2026-11-23 12:00 UTC, the narrower rule stays.
  - [INTERNAL] Decision 1 in part 1a.
- **K15. Fixed on branch:** planted text could rewrite part of a tool's name in the line where the model asked for that tool.
  - Example: a document planted `password=logs`; the model then saw two names for one tool call.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (no recorded batch). Who acts: the text and masking team. See K66 for the tool list.
- **K16. Fixed on branch:** stopping the program by hand, while the gate worked out the worst case or asked for a reservation, left no audit row. Now a row is written.
  - Example: the program is stopped by hand while the gate waits for its reservation. The record now holds a row that says "reservation interrupted".
  - The reservation stays booked, on purpose: the worst case stays booked, not the real cost.
  - Status: FIXED ON BRANCH. Evidence: NOT RUN (no recorded batch). Who acts: the text and masking team.
  - UNVERIFIED (a reviewer's reading): two more places where a stop by hand still leaves no row.
  - [INTERNAL] The two places are in gate fix round 4 (F-r3 design N4).
- **K17. Not safe:** two threads writing one run map at the same time can give one placeholder number to two values.
  - Example: two tools finish together and both values become `<SECRET_3>`.
  - Status: OPEN. Evidence: UNVERIFIED (reasoned from the code in the gate's written plan, not run).
  - Who acts: the text and masking team adds "one writer per run map" to its install request to the connector and store team.
- **K64. Not protected:** a run's later calls, when planted text holds more than 256 values at a placeholder's edge (such as `password=>aaaa1`). The gate then refuses every later call of that run, because the run map only grows.
  - Example: one planted document with 257 such lines stops the run.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team.
  - [INTERNAL] In gate fix round 4 (NOT RUN).
- **K65. Not refused:** a known secret left readable outside the held-back case. The safety net checks held-back values only. The audit row still says the map was used.
  - Example: a known secret `AKIAEXAMPLE123` written as `<AKIAEXAMPLE123_1>` (see K7), or written across a fixed marker word.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team.
  - [INTERNAL] In gate fix round 4 (NOT RUN).
- **K66. Not consistent:** a known value inside a tool's name. The gate masks it in the line where the model asked for the tool, but the tool list goes out as written.
  - Example: the run map holds `<TENANT_1>` for `billing`. The model sees `tool get_<TENANT_1>_info` and may call a tool that does not exist.
  - A secret that is only part of a tool's name, such as `logs` in `read_logs`, stays readable in the tool list.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team.
  - [INTERNAL] In gate fix round 4 (NOT RUN).
- **K67. Not complete:** the install hand-over list and the install test. They miss the judge's call points, so after install a judge call could still go around the gate.
  - Example: the approval code reaches the judge from three places that the list does not name.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team corrects the list and the test. Then the connector and store team installs.
  - [INTERNAL] In gate fix round 4 (NOT RUN).
- **K69. Not checked:** that the run map given to the gate is the run's own, current map. An earlier copy, or another run's map, still reads "map used" in the audit row. A masking function supplied by the calling code is accepted outside tests too.
  - Example: the calling code passes yesterday's run map. Values found today are not masked, and the row says the map was used.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading).
  - Who acts: the owner decides it together with one question: whether the gate refuses a call when the run map is empty.
  - If no answer arrives by 2026-11-23 12:00 UTC, the default applies: the gate refuses an empty map. Then the text and masking team adds the check.
  - [INTERNAL] Decision 6 in part 1a; F-r3 design M4.
- **K18. Not handled:** a gate refusal or a refused reservation leaves the run's status "working" instead of "stopped".
  - Example (UNVERIFIED, read from the code): after a refused reservation the run still shows "working". The planted-instruction check reports the same refusal as a guard failure.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written install request).
- **K19. Not through the gate:** the guardrail call. It is neither masked by the gate nor counted against the cap.
  - Example: a run's guardrail calls cost money that the cap never sees.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: UNVERIFIED (read in the install test's table of calls kept outside the gate). Who acts: nobody.

### 2.2 Spending cap

Shown by tests:

- TESTED (the gate's batch): the gate makes no model call without a reservation. Order: mask, reserve, call, settle, write the audit row.
- TESTED, twice, on the connector and store team's store code, database version 16, Python 3.13: 50 separate database connections, started together, each asked for a reservation.
- In that test the cap was 3.00 USD for the day and the month, and the worst case 1.00 USD. 3.00 USD was reserved and 47 requests were refused.
- TESTED (same test file): five other cap and worst-case pairs, two agents, and a month cap reached over two days.
- These tests show that reservations stop at the cap. They do not show that booked money stays under it: K24 shows it can pass, and K26 is not tested.
- TESTED (the gate's batch): when a reply arrives with a usable cost, the gate settles that real cost.

Known gaps:

- **K20. Not released:** the worst case of a failed call. The model connectors cannot yet say "refused before any answer".
  - Example: UNVERIFIED (worked out, not run): with a cap of 3.00 USD and a worst case of 1.00 USD, three failed calls book 3.00 USD. It stays booked for the rest of the day (day cap) and month (month cap).
  - Status: WAITING. Evidence: TESTED (a failed call is not settled). Who acts: the connector and store team (written request).
- **K21. Booked as free:** a reply with an empty cost field. The connectors' reply form fills an empty cost with 0.00 USD, and the gate settles 0.00 USD.
  - Example: a connector forgets to fill in the cost; a 0.80 USD call is booked as 0.00 USD.
  - Status: WAITING. Evidence: TESTED (the gate's side). UNVERIFIED: that a connector leaves the field empty. Who acts: the connector and store team (written request).
- **K22. Not settled:** a reply with an unreadable cost. The worst case stays booked, not the real cost.
  - Example: a reply reports its cost as "not a number"; the full 1.00 USD stays booked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K23. Not counted:** earlier attempts of a call that succeeded after retries. Only the last attempt is settled.
  - Example: attempt 1 times out but was billed 0.40 USD; attempt 2 costs 0.30 USD; only 0.30 USD is booked.
  - Status: WAITING. Evidence: UNVERIFIED (read from the code). Who acts: the connector and store team (written order).
- **K24. The cap can be passed once:** a call that costs more than its worst case is booked in full, on purpose.
  - Example: three calls each reserve 1.00 USD against a cap of 3.00 USD. One settles at 2.50 USD. Booked: 1.00 + 1.00 + 2.50 = 4.50 USD. Later calls are refused.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody (by design). How often this happens depends on the worst-case formula, which does not exist yet (K25).
- **K25. Not written:** the worst-case formula. No function in the code fits the gate today.
  - Example: until it exists, no installed gate has a real worst case to reserve.
  - Status: WAITING. Evidence: NOT RUN (nothing to test). Who acts: the connector and store team (written order).
- **K26. Not enforced by the database:** the runtime login can rewrite a reserved amount. The purge login can delete an open reservation.
  - Example: faulty code could lower its own reservation.
  - Status: OPEN. Evidence: UNVERIFIED (read from the database set-up code).
  - Who acts: the owner decides whether to tighten these rights. If no answer arrives by 2026-11-23 12:00 UTC, they are tightened. Then the connector and store team changes them.
  - [INTERNAL] Decision 5 in part 1a.
- **K27. Not refused:** an out-of-date price table.
  - Example: a vendor raises prices; the worst case is computed at the old price.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.
- **K28. Not capped across processes:** the test and replay command lines keep their cap in memory, per process.
  - Example: two replay processes each spend up to the cap.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.

### 2.3 Stop switch

Shown by tests:

- TESTED (the gate's batch): a refused reservation, including the stop switch's refusal, means no model call.
- UNVERIFIED: that the store refuses every reservation while the switch is on. This is in the connector and store team's code. No test of it is named here.
- NOT RUN: any end-to-end stop of a live run.

Known gaps:

- **K29. Not narrowed by the database:** the runtime login can sign a stop record with any name. The reset login can change any stop-switch row.
  - Example: a stop record says "by: operator" when the runtime wrote it. Any change the reset login makes reads as "on", so the store then refuses reservations.
  - Status: OPEN. Evidence: UNVERIFIED (read from the database set-up code).
  - Who acts: the owner decides whether to tighten these rights. If no answer arrives by 2026-11-23 12:00 UTC, they are tightened. Then the connector and store team changes them.
  - [INTERNAL] Decision 5 in part 1a.
- **K30. Not stopped:** a call already in flight, and the test and replay command lines (they do not read the switch).
  - Example: a 30-second call started before the stop still completes.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.

### 2.4 Audit record

Shown by tests:

- TESTED (the gate's batch): the gate tries to write one audit row per call. The row holds the run, the type of action, who asked, the result, and a code from a fixed list.
- TESTED (the gate's batch): the gate's code holds no logging and no error text, and no audit row in those tests held a secret.
- TESTED (the gate's batch): if writing the row or settling fails after the reply came back, the gate still returns the reply.

Known gaps:

- **K31. Not recorded:** whether anything was masked, and the route.
  - Example: an investigator cannot tell from the row whether a secret was masked.
  - Status: OPEN. Evidence: UNVERIFIED (read from the code: the row's map field covers map use only).
  - Who acts: the owner decides whether to add a "masked: yes or no" field and the route. If no answer arrives by 2026-11-23 12:00 UTC, both are added.
  - [INTERNAL] Decision 2 in part 1a.
- **K32. Not narrowed:** the reset login can add any audit row, not only a reset record.
  - Example: faulty reset code could write a row that looks like a model call.
  - Status: OPEN. Evidence: UNVERIFIED (read from the database set-up code).
  - Who acts: the owner decides whether to tighten this right. If no answer arrives by 2026-11-23 12:00 UTC, it is tightened. Then the connector and store team changes it.
  - [INTERNAL] Decision 5 in part 1a.
- **K33. Not in the record:** the test and replay command lines print their audit lines to the screen only.
  - Example: a replay leaves no row in the store.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.

### 2.5 The secret finder (what enters the run map)

Shown by tests (TESTED here means: in recorded batches of the shared branch's code, before it was saved):

- TESTED: it finds the kinds it knows: addresses, keys, tokens, e-mail, passwords in web addresses and command lines, and supplier payment details (a bank account beside its bank code).
- TESTED: one call masks a bank account beside its bank code. It also masks the rest of a longer token that holds a shorter known secret (K40).
- TESTED: one call runs up to 5 search rounds. Past the 5th round, it refuses the whole text (fail closed).
- TESTED: a line it cannot mask in place is withheld.
- UNVERIFIED: which saved version of the code the latest of these batches ran on.
- [INTERNAL] Batches: the 135-file pick batch before the merge, and the 9,681-test G7 batch (evidence/G7-1.md; code version not recorded).

Read, not tested:

- UNVERIFIED (a reviewer's reading): one text can go through up to 7 calls of the secret finder. There is one call for each way of reading it, such as the decoded and the folded text.

Known gaps and fixed findings:

- **K34. Not found:** a secret in a shape the secret finder does not know.
  - Example: an unlabelled 40-character code in plain prose.
  - Status: STATED (the published README, section "Limits and trust", since 2026-11-04). Evidence: NONE. Who acts: nobody.
- **K35. Not masked:** a bare number with no label.
  - Example: `ref 55556666 paid`. MEASURED on the main line: 24 of 43 such test lines were not masked.
  - Status: STATED (an evidence file and a ticket of the text and masking team, 2026-11-20, call it accepted). Evidence: MEASURED. Who acts: nobody.
  - The written order those two files cite as the acceptance was not found. So that acceptance is UNVERIFIED.
  - [INTERNAL] Source: ticket G4 v2 section 6 cites "order 64 item 4"; ORDERS.md line 64 is ORDER 006 item 1. evidence/P1c-probe.md says "accepted property".
- **K36. Not masked:** host names with no "host" word in front. A private name with a public ending is masked only in part.
  - Example: `db01.acme.example` stays; `db01.corp.example` becomes `<HOSTNAME_1>.example`.
  - Status: OPEN. Evidence: MEASURED (on the main line, which lacks the planned change: 28 of 44 test lines leaked).
  - Who acts: the owner decides whether to build the planned change. If no answer arrives by 2026-11-23 12:00 UTC, it stays a known gap until a plan review is clean.
  - [INTERNAL] Decision 3 in part 1a. G4 v2 plan review round 2: NOT READY (tickets/G4-review-2.md); G4 v3 being drafted.
- **K37. Not masked:** base64 text under 40 characters.
  - Example: a short password written in base64.
  - Status: OPEN. Evidence: MEASURED (on the main line: 41 of 41 such lines leaked).
  - Who acts: the owner decides whether to build the planned change. If no answer arrives by 2026-11-23 12:00 UTC, it stays a known gap until a plan review is clean.
  - [INTERNAL] Decision 3 in part 1a.
- **K38. Not masked:** an IP address, phone number, international bank account number or unique id with a letter or `_x` glued behind it.
  - Example: `10.20.30.40_x` goes out unmasked.
  - Status: OPEN. Evidence: MEASURED (on the joined branch whose code is now on the shared branch). Who acts: the text and masking team writes the next work item.
- **K39. Not proven:** that the repeated search finds every value. Each call now runs up to 5 search rounds.
  - Example: planted text glues a bank code to a secret, then puts the account after that code elsewhere. This needed a third round and is now masked.
  - Status: OPEN. Evidence: TESTED (the chain). UNVERIFIED: which saved version that batch ran on. Who acts: the text and masking team.
  - UNVERIFIED (a reviewer's reading; no leaking text was built): a line changed by the patterns, but not by the masking step, is not searched again in later rounds.
  - UNVERIFIED (read from the code): planted text that needs a 6th round makes the secret finder refuse the whole document.
  - [INTERNAL] In secret finder fix round 3 (NOT RUN).
- **K40. Fixed:** the last part, up to 7 characters, of a longer token stayed readable in its other copies. This happened when the token was found only after a shorter known secret inside it.
  - Example: `password=ab9x`, then `Bearer ab9xqrstu`. The line `note ab9xqrstuvw end` used to show `note <SECRET_1>qrstuvw end`. It now shows `note <BEARER_1>vw end`.
  - Status: FIXED. Evidence: TESTED (20 of 28 new tests failed before the change). Who acts: nobody. See K68.
  - UNVERIFIED: which saved version of the code the passing batch ran on.
- **K41. Not limited:** how long one call of the secret finder takes. Its time budget (6 seconds of processor time per call) is checked before each search round, not inside one.
  - Example (MEASURED, processor time): 100,000 characters of bank lines took 0.167 seconds before the repeat and 0.395 seconds with it.
  - MEASURED: a text at the size cap, built to be slow, took 4.00 seconds against the 6-second budget.
  - Status: OPEN. Evidence: MEASURED (those numbers). Who acts: the text and masking team.
  - UNVERIFIED (a reviewer's reading): one call can take its budget plus one whole search round. One step grows with the number of values times the text length, with no time check.
  - [INTERNAL] In secret finder fix round 3 (NOT RUN).
- **K42. Not masked later:** a secret first seen in a tool's error message. It never enters the run map.
  - Example: a tool fails with "bad password hunter2zz"; later results show `hunter2zz`.
  - Status: WAITING. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the connector and store team (written request).
- **K43. Not masked:** a secret spelled exactly like an escaped placeholder (`‹SECRET_1›`, with angle quotes).
  - Example: `password=‹SECRET_1›` stays as written, on purpose.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K44. Fixed:** a secret wrapped in look-alike angle quotes was left readable.
  - Example: `password=‹hunter2zz_1›` is now masked.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K45. Fixed for the one place found:** the secret finder, run again on its own output, turned real placeholders into new secrets. The place was the tool-error path.
  - Example: a tool error quoting `<SECRET_1>` no longer adds a new map entry.
  - Status: FIXED. Evidence: TESTED (that place). UNVERIFIED: that no other place does this. Who acts: nobody.
- **K46. Not masked whole:** a secret holding a space, `;`, `,` or `&`. It is masked only up to that character.
  - Example: `password="my secret phrase"` shows `secret phrase`.
  - Status: STATED (the published SECURITY.md on the main line, since 2026-11-04). Evidence: NONE. Who acts: nobody.
- **K68. Wrong value restored:** after the secret finder undoes a half-made entry, an old record can survive. A later placeholder with the same number can then be restored to the wrong value.
  - The text stays masked; nothing raw goes to the model. A tool could get the wrong account or credential.
  - Example: a token found and then undone leaves a record for `<BEARER_1>`. A new `<BEARER_1>` for another value is later restored as the old one.
  - Status: OPEN. Evidence: UNVERIFIED (two reviewers' reading). Who acts: the text and masking team.
  - [INTERNAL] In secret finder fix round 3 (NOT RUN).

### 2.6 Text folding (look-alike and hidden characters)

Shown by tests (in the recorded batch before the merge):

- TESTED: before the secret finder searches, it folds the text. Look-alike letters, invisible characters and accents become one plain spelling.
- Condition: the program runs on Python 3.13 (see README, section "Python version").

Known gaps and fixed findings:

- **K47. Fixed:** the secret finder's own look-alike search was missing from the shared branch. It is there now.
  - Example: `password=x` written with a Cyrillic "а" is now found.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K48. Not decoded by folding:** escape codes; look-alikes added after Unicode edition 15.1; hidden marks outside two character blocks.
  - Example: the escape code `&#49;` (the code for the digit 1) is not read as `1`, so `abc&#49;` stays as written.
  - Status: STATED (the text folding work's written limits, 2026-11-20). Evidence: UNVERIFIED (a reviewer's reading confirms the limits). Who acts: nobody.
- **K49. Not flagged:** the Chinese character for zero (Unicode name IDEOGRAPHIC NUMBER ZERO, 〇) inside a Latin word.
  - Example: `pay` + 〇 + `al` is not called mixed script. MEASURED: it is the only such character in the folding table.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K50. Not measured:** how often folding finds a known name inside an innocent longer word.
  - Example: known `mary` found in `summary`; innocent text may be masked or withheld.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). NOT RUN: the measurement (no result is recorded). Who acts: the text and masking team.
- **K51. Not limited:** the time text folding takes. The planted-instruction check folds up to 2,097,152 characters with no time limit.
  - Example: a planted text of 2,097,152 characters slows that check.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team.
- **K52. Refused, not read:** a long text in Chinese or Japanese only. It is reported as a guard failure.
  - Example (MEASURED): 300,000 characters of Chinese, and of Japanese, were refused. Russian prose of that size is read.
  - NOT RUN: a measure of the shortest length that is refused.
  - Status: STATED (written down by the text and masking team, 2026-11-20). Evidence: MEASURED. Who acts: nobody.
- **K53. Chosen in a written order:** dashes and curly quotes are ordinary punctuation. Three slash look-alikes make the line withheld.
  - Example: a value right after an em dash (—) is masked in place.
  - A line holding DIVISION SLASH (∕), BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT (╱) or BIG SOLIDUS (⧸) plus a look-alike value is withheld.
  - Status: PINNED (chosen in the project's written order of 2026-11-20 06:15 UTC). Evidence: TESTED. Who acts: nobody.
- **K54. Finds more than before:** an invisible character between a Latin letter and its accent.
  - Example: `e` + hidden mark + accent now matches `é`.
  - Status: PINNED (accepted in the project's written order of 2026-11-20 05:47 UTC). Evidence: TESTED. Who acts: nobody.
- **K55. Not decided:** the same wider matching in Korean, Japanese and Indian scripts, for the grounding check.
  - Example: a Korean name split by a hidden mark now counts as present.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading).
  - Who acts: the owner decides whether to accept it. If no answer arrives by 2026-11-23 12:00 UTC, the older rule returns for those scripts. Then the text and masking team changes it.
  - [INTERNAL] Decision 4 in part 1a.
- **K56. Fixed:** a secret stored as `Müller` but shown with a separate accent mark was not masked in tool output.
  - Example: `Mu` + combining accent + `ller` is masked again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K57. Fixed:** look-alike padding before a 32,768-character boundary could hide a planted order from the planted-instruction check.
  - Example: "ignore previous instructions" split across that boundary is found again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K58. Fixed:** on the wrong Python, the connection to the secrets vault was built before the start-up refusal. The refusal now comes first.
  - Example: a pilot build on the wrong Python stops before it builds the connection to the secrets vault.
  - Status: FIXED. Evidence: TESTED (one test, on Python 3.13 with the version faked). Who acts: nobody.
  - NOT RUN: a check of other outside services.

### 2.7 Approval messages

Shown by tests:

- TESTED (in a recorded batch on the branch where the change was built): the secret finder runs first on each free-text path found that writes an approval message.
- That batch ran before the change joined the shared branch.
- TESTED (same batch): web addresses are made unclickable last (a dot written as `[.]`).
- [INTERNAL] evidence/G2-p1d-a.md fix round batch: 7,879 passed, 0 failed. tests/test_p1d_a_paths.py holds 27 test functions (counted at HEAD); "27 passed" alone. In the 135-file pick batch: UNVERIFIED (file list not recorded).

Read, not tested:

- UNVERIFIED (read in the code; no recorded batch names its test): a message is re-read until it stops changing, at most 3 times. If it never settles, a fixed note is shown instead.
- Id fields are not masked (K59).

Known gaps and fixed findings:

- **K59. Not masked:** the "requested by" line and other id fields.
  - Example (UNVERIFIED: read from the code, not tried on Slack): a requester id `slack:U1|<!channel>` could make Slack notify everyone in the channel.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written request).
- **K60. Not proven:** that no clickable link remains. The test for it uses the same patterns as the code it tests.
  - Example (UNVERIFIED): a link the patterns miss, such as `see/evil.com`, would slip past both.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the text and masking team adds a link check with its own patterns.
- **K61. Fixed:** an e-mail address with a digit or `_` glued behind it was shown whole.
  - Example: `anna.m@example.org9` is now masked.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K62. Not checked:** approval summaries stored before these fixes, as shown on the admin page.
  - Example: a summary stored before the fixes could still show an e-mail address; nobody has looked.
  - Status: OPEN. Evidence: NOT RUN. Who acts: the text and masking team.

MEASURED slowdown of approval-message masking on the joined code (median, on the builder's test machine):

- a 174-character message took 0.00126 seconds before and 0.00360 seconds now;
- a 71,179-character message took 0.367 seconds before and 0.655 seconds now.

### 2.8 Set-up

- **K63. Late failure:** the project file allows installing on Python 3.12. Once the text-folding change ships, by design a pilot or prod install there succeeds and the program refuses to start.
  - Example: an operator installs on 3.12; the program then refuses to start (see README, section "Python version").
  - Status: OPEN. Evidence: NOT RUN (no install on 3.12 was tried). UNVERIFIED (read from the file): that the project file allows 3.12.
  - Who acts: the connector and store team.
  - [INTERNAL] No written request yet; core-c writes one if the lead agrees (4.5).

### 2.9 What was not run (NOT RUN)

- The full test suite.
- Python 3.12 on this work's code.
- Database version 17. The tests here ran on version 16.15 only.
- Any live call to an AI service. Any end-to-end stop of a live run. The gate installed at any call point.
- The planned host-name and base64 change (never built).
- 238 of the 240 deliberate code breaks for text folding.
- A recorded test batch on: the merged code as a whole; the gate's latest fixes; the time limit inside the secret finder's masking step.
- [INTERNAL] Python 3.12: only the lead's run of old branch P1a. Database 17: the automatic test service is set to 17.10 (evidence/B-grants-rework.md line 71); no result from it is recorded.
- [INTERNAL] The 2 text folding code breaks that ran cover the ORDER 010 spacing-mark rule (tickets/G-text-deltas.md line 141).
- [INTERNAL] Gate fix round 4 and secret finder fix round 3: running; no results here.

---

## 3. For README.md: "Python version"

As of 2026-11-20 08:09 UTC.

[INTERNAL] This section describes the text folding change. As of 2026-11-20 it is on the shared branch only, not on the product's main line. Ship it with the release that contains that change.

Words used here: an operator is the person who installs and runs the kit (this software package) for a client. The stages are demo (made-up data), pilot (a first, limited use with a real client) and prod (normal live use).

Text folding turns look-alike letters, invisible characters and accents into one plain spelling before the kit searches text for secrets. Unicode is the world standard list of characters. Each Python version carries one edition of it.

The marks: NOT RUN means the check was not run. UNVERIFIED means someone read the code and nothing was run. TESTED means a named test passed in a recorded batch.

**Operators must run pilot and prod on Python 3.13.**

To check, run `python3 --version`, or use the Python you install the kit with. To see its Unicode edition, run `python3 -c "import unicodedata; print(unicodedata.unidata_version)"`. Pilot and prod need `15.1.0`.

Why: text folding uses the Unicode character data built into Python. The folding tables are built for edition 15.1.0, which Python 3.13 carries. Python 3.12 carries 15.0.0.

Pilot and prod on Python 3.12: NOT RUN on Python 3.12. By design, the program refuses to start and prints the error UnidataMismatch. The fix is to install Python 3.13.

TESTED: one test on Python 3.13, with the version number faked, shows that refusal. In that test, the refusal comes before the program connects to the secrets vault (the place where secrets are kept). NOT RUN: a check of other outside services.

UNVERIFIED (read from the project file): the project file allows installing on 3.12. So the install succeeds, and the failure shows only when the program starts.

Demo on Python 3.12: NOT RUN on Python 3.12. By design, the program starts. Text folding gives each folded name a tag with the Unicode edition. So names folded on 3.12 and on 3.13 never match. Do not compare results from the two versions.

Python 3.11 or older: UNVERIFIED (read from the project file): the install is refused, because the project file asks for 3.12 or later.

Python 3.14 or later: UNVERIFIED (read from the code): pilot and prod refuse to start on any Python whose Unicode edition is not 15.1.0. Do not run pilot or prod on Python 3.14 or later until the release notes say the character tables were rebuilt for it.

---

## 4. Technical appendix (INTERNAL, does not ship)

As of 2026-11-20 08:09 UTC. Internal references (codes, test names, files, orders, commits) appear only here. Team codes: core-b = the connector and store team; core-c = the text and masking team.

### 4.1 Key to codes used in the sources

| code | meaning |
|---|---|
| cloud/core-c | the shared branch; head at the time of writing: 6b990d9 (08:09:52 UTC, equal to origin/cloud/core-c). No file under src/ or tests/ changed since v4's head 11935aa (git diff --stat 11935aa..HEAD: handover files only) |
| d95a727 | the merge of the integration (P1d-a card fixes, P2d-1 fold scan, G7, glued-rest fixes) into cloud/core-c, 07:28 UTC. Second parent cfda4d0 = the pick branch wip-pick; first parent 1c884b2 = a gate snapshot "work in progress, NOT verified" |
| wip-pick | the worktree branch /tmp/core-c-pick, cut from bd4446c, where the pick batch ran (evidence/PICK-int-onto-core-c.md) |
| fb08bde, 89af120, 1c884b2 | work-in-progress commits on cloud/core-c ("NOT verified"); guard/model_gate.py last changed in fb08bde (07:22 UTC, git log at HEAD) |
| aa7c5fa | core-c's edit of guard/producers.py (core-b's file), 07:36 UTC: 1 file, 2 lines added (git show --stat); tests/test_k5_producers.py 25 passed (commit message; DECISIONS 07:40 UTC) |
| c9478a9 | 07:38 UTC, title "code F: gate round 2 fixes ..."; message: "81 of 81 mutants good, 302 passed in the gate and install files". Files: G7 fix round 2 code (guard/redact.py, defaults.py, tests incl. tests/test_redact_settle_loop.py), runmap.py 4 lines, evidence/G7-1.md; no model_gate.py. DECISIONS 08:05 UTC: swept in by `git add -A` while the G7 builder was editing |
| a2b6311 | 07:41 UTC, "code G: work in progress of the running G7 fix round 2 builder, NOT verified": `_Redactor.sweep(out, deadline=None)` and its test; last change of guard/redact.py at HEAD |
| 0fcc5e1 | 07:44 UTC: the commit that added the G7 batch line "9681 passed" to evidence/G7-1.md (git log -S) |
| origin/main | the product's main line; none of d95a727, c9478a9, a2b6311 is on it; `UnidataMismatch` is not on it (git grep origin/main) |
| F, G, B, T1 | work packages: F the gate; G the text work; B database rights; T1 the 50-connection cap test |
| G1 / G2 / G3 | text folding / approval-message text (old branch P1d-a) / the look-alike search ported into the secret finder (old branch P2d-1) |
| G4 | the planned base64 and host-name change (old ticket P1c), not built; v2 ticket tickets/G4-P1c-redactor-gaps-v2.md (330f4fb, 07:46 UTC); plan review round 2 tickets/G4-review-2.md (readiness 2 B, 9 M; codebase 3 B, 8 M); v3 drafter g4v3 running (STATUS-BOARD 08:09 UTC) |
| dz, cb / dz2, cb2 / F-r3 | first / second / third independent result review of the gate; third: tickets/F-result-review-3.md (design 0 B, 4 M, 5 N; codebase 0 B, 5 M, 7 N) |
| G7-r2 | result review round 2 of G7: tickets/G7-result-review-2.md (codebase 1 B, M2-M7 = 6 M (its header says 5), N8-N10; design 0 B, 5 M, 3 N) |
| gate fix round 4 | builder gfix4 (STATUS-BOARD), on the F-r3 findings; worktree branch wip-gate4. Running; NOT RUN |
| secret finder fix round 3 | builder g7fix3 (STATUS-BOARD), "G7 fix round 3", on the G7-r2 findings; worktree branch wip-g7r3. Running; NOT RUN |
| g4r | plan review round 1 of G4 (tickets/G4-review-1.md: 8 Blockers, 6 distinct, 12 Majors) |
| E1 to E7 | entries in ESCALATIONS.md (E7: database rights) |
| ORDER nnn | orders from the lead in ORDERS.md; MJ-A to MJ-D = Majors of the lead's review round 3 (ORDER 020, about 07:25 UTC) |
| T:: / E:: | tests/test_model_gate.py / tests/test_runmap_enforce_map.py |
| sweep | the step that masks every copy of values already in the run map (the "masking step" of a search round) |
| NO_MAP | the named constant for "no map" |
| strict xfail | strict expected failure |
| refusal words | gate: `mask_refused`, `framing_refused`, `worst_case_failed`, `worst_case_invalid`, `reserve_refused`, `reservation_invalid` (type `GateRefused`); store: `kill_switch` (stop switch), `daily_budget`, `monthly_budget`, `limits_unavailable`, `bad_amount`, `usd_cap` |
| audit decision field | `map_enforced`, `map_enforced_empty`, `enforce_custom`, `map_failed`, `no_map`; codes `call_interrupted`, `reserve_interrupted`, `held_value_left` |
| framing marker | `<<TOOL RESULT call_id=ID tool=NAME>>` ... `<<END TOOL RESULT>>`; assistant line `tool NAME {json}` |
| UnidataMismatch | the start-up refusal of `textnorm.require_pinned_unidata` (textnorm.py:1644-1660; app.py:132; accepts only `defaults.TEXTNORM_PINNED_UNIDATA` = "15.1.0") |
| REDACT_BUDGET_S | 6.0 CPU seconds of the calling thread per `redact_text` call (defaults.py) |
| `_SETTLE_ROUNDS` | 4 (redact.py:1751): rounds 2 to 5 after the first pass; RedactionError("NotSettled") past it |

### 4.2 Table of known gaps

| gap | status | evidence level | evidence | who acts |
|---|---|---|---|---|
| K1 secret not found passes | PINNED | TESTED | T::test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job | nobody |
| K2 short, digits, common words, touching | PINNED | TESTED | E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept; E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept; rule read in redact.py `_sweep` 1905-1917 | nobody |
| K3 other spellings | PINNED | TESTED / UNVERIFIED (alias) | T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate; E::test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced; E::test_stated_limit_a_copy_split_by_nul_characters_is_not_found; T::test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced; alias spellings: F-r3 codebase M2 (reading) | nobody (gate); gate fix round 4 for the alias point |
| K4 letter case | PINNED | TESTED | T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced | nobody |
| K5 overlap tail | PINNED | TESTED | E::test_stated_limit_partial_overlap_leaves_a_tail; T::test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent | nobody |
| K6 joined key and value | PINNED | TESTED | T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched | nobody |
| K7 placeholder-shaped values | PINNED | TESTED | E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced; E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder; E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass | nobody |
| K8 fields not masked | PINNED | TESTED | T::test_t20_system_and_tools_are_not_touched; T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched. The prompt-registry install check is a separate request (requests/3-bind-mapping-required.md section 6, ORDER 020 MJ-D), WAITING on core-b, on an [INTERNAL] line in part 2 | nobody |
| K9 no map | PINNED | TESTED | T::test_no_map_means_no_enforce_step_at_all; NO_MAP placement checked by tests/test_gate_install_callers.py | nobody |
| K10 audit says map in use | FIXED ON BRANCH | NOT RUN | dz2-M5; T::test_r2_m5_the_audit_decision_says_what_was_really_enforced; mutants G22a-c; WIP commits; no pytest result recorded (F-r3 codebase M5) | core-c |
| K11 forged marker | FIXED ON BRANCH | NOT RUN / UNVERIFIED (closed, reading) | dz2-B1, ORDER 020 MJ-A; reproduced by the builder (evidence/F-G0-1.md); T::test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client[id,name,both]; mutants B1a, B1b; F-r3 design "verified closed" (reading) | core-c |
| K12 edge value tail | OPEN | NOT REPRODUCED | dz2-M2 (reading); NOT REPRODUCED by the builder (evidence/F-G0-1.md "Review round 2 fixes (final)"); safety net `held_value_left`; mutant G24 | core-c |
| K13 per-call time and size | OPEN | MEASURED / UNVERIFIED | dz2-M3 PARTLY FIXED; measured 0.018 s for 100 texts / 2,000 entries (F-G0-1.md); missing deadline: runmap.py:742 and :746 call `sweep(out)` with no deadline (read at HEAD); clock mismatch G7-r2 codebase M5; F-r3 design M2 (256 KB = 262,144 characters, 500 values, about 128 million steps, estimate) | core-c (gate fix round 4) |
| K14 planted secret stops tool calls | OPEN | TESTED (old rule) / NOT RUN (new rule) / UNVERIFIED | T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker; new rule: T::test_r2_m4_..., T::test_r2_m1_...; mutants O6-O8; F-r3 design M1a, codebase N3 (reading) | owner (decision 1) |
| K15 tool line rewritten | FIXED ON BRANCH | NOT RUN | cb2-M2; T::test_r2_m2_the_assistant_line_and_the_token_name_the_tool_alike_when_a_value_sits_inside_it; mutants O9, O10 | core-c |
| K16 interrupt leaves no row | FIXED ON BRANCH | NOT RUN / UNVERIFIED (two more places) | dz2-M7; T::test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on; mutants G23a-d; F-r3 design N4 | core-c (gate fix round 4) |
| K17 two writers | OPEN | UNVERIFIED | tickets/F-gate-wrapper-body.md line 186 ("ONE WRITER PER RUN MAP ... not pinned (a race)"); requests/3 does not name it (grep) | core-c (adds it to request 3) |
| K18 run left "working" | WAITING | UNVERIFIED | F-result-review-2.md call-site list; agent_loop.py:477; requests/3-bind-mapping-required.md section 3 | core-b |
| K19 guardrail call outside gate | STATED | UNVERIFIED | inputs/plan-v4-final.md line 29 (frozen 2026-11-20); tests/test_gate_install_callers.py line 41 BYPASS row for guard/bedrock_guardrail.py (read; no batch named for that test after c9478a9 changed the file) | nobody |
| K20 failed call stays booked | WAITING | TESTED / UNVERIFIED (example) | T::test_pin_an_unmarked_provider_error_is_not_settled; T1 expiry case; requests/2-refused-before-response.md | core-b |
| K21 empty cost booked as free | WAITING | TESTED / UNVERIFIED | T::test_m5_a_zero_cost_reply_is_settled_at_zero; models.py:299 `cost_usd: Decimal = Decimal(0)`; requests/3 section 4 | core-b |
| K22 unreadable cost not settled | PINNED | TESTED | T::test_pin_a_reply_with_no_usable_cost_is_not_settled; T::test_o17_2_... | nobody |
| K23 retries settle last attempt | WAITING | UNVERIFIED | llm/retry.py lines 92-107 (reading, E6 item 3); ORDER 017 item 3 (06:30 UTC) | core-b |
| K24 overshoot booked in full | PINNED | TESTED | tests/contracts/test_t1_reserve_cap.py::test_a_settle_above_the_reserve_books_the_actual_amount_past_the_cap (PostgreSQL 16.15); T::test_a_settle_above_the_reservation_is_passed_through | nobody |
| K25 worst-case formula | WAITING | NOT RUN | ORDER 016c item 13 (06:21 UTC) | core-b |
| K26 reservation rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md findings 1, 2 (migrate.py:56, read); E7 items 1-2 | owner (decision 5), then core-b |
| K27 stale price table | STATED | NONE | plan-v4-final line 29, frozen 2026-11-20 | nobody |
| K28 in-memory cap on command lines | STATED | NONE | plan-v4-final line 29; refusal `usd_cap` (ORDER 014) | nobody |
| K29 stop-switch rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md findings 3, 4 (migrate.py:61-62, read); E7 items 3-4 | owner (decision 5), then core-b |
| K30 in-flight call, command lines ignore stop | STATED | NONE | plan-v4-final line 30 (B3 "Stop"), frozen 2026-11-20 | nobody |
| K31 audit lacks masked flag and route | OPEN | UNVERIFIED | F-result-review-1.md nits (reading); model_gate.py decision constants cover map use only (read at HEAD) | owner (decision 2) |
| K32 reset login audit rights | OPEN | UNVERIFIED | evidence/B-grants-rework.md finding 5 (migrate.py:65, read); E7 item 5 | owner (decision 5), then core-b |
| K33 command lines audit to screen | STATED | NONE | plan-v4-final line 32 (B3 "Audit"), frozen 2026-11-20 | nobody |
| K34 unknown shape | STATED | NONE | README.md "Limits and trust" (origin/main, ce70eb5, 2026-11-04) | nobody |
| K35 bare number | STATED | MEASURED | evidence/P1c-probe.md (24 of 43, main code; "accepted property"); G4 v2 section 6 ("order 64 item 4": not in ORDERS.md) | nobody |
| K36 host names | OPEN | MEASURED | evidence/P1c-probe.md (28 of 44 leaked, main code); G4-review-1, G4-review-2 | owner (decision 3), then core-c |
| K37 short base64 | OPEN | MEASURED | evidence/P1c-probe.md (under 40 characters: 41 of 41; all base64 rows: 52 of 142; main code) | owner (decision 3), then core-c |
| K38 glued IPv4, phone, IBAN, UUID | OPEN | MEASURED | evidence/INT-g2-g3.md follow-up (c); now in d95a727 | core-c |
| K39 repeat not proven complete | OPEN | TESTED / UNVERIFIED | tests/test_redact_idempotent_property.py::test_one_pass_is_a_fixed_point_and_leaves_no_raw_copy[constructed:0]; tests/test_redact_settle_loop.py; evidence/G7-1.md batch 9681 passed, 0 failed (code version not recorded); G7-r2 design M1, M2, codebase M3 (reading) | core-c (secret finder fix round 3) |
| K40 tail up to 7 | FIXED | TESTED / UNVERIFIED (batch version) | tests/test_redact_settle_loop.py tail cases (fail-before 20 of 28 on round 1 code); evidence/G7-1.md batch above (line added in 0fcc5e1 at 07:44 UTC, after a2b6311) | nobody |
| K41 finder time | OPEN | MEASURED / UNVERIFIED | evidence/G7-1.md round 2 timings (T1 0.167 -> 0.395 s; T4 `curl -u` 4.00 s, budget 6.0); G7-r2 design M4, M5 (reading) | core-c (secret finder fix round 3) |
| K42 tool error not in map | WAITING | UNVERIFIED | G7 review dz-6 (reading); requests/4-error-reason-run-map.md | core-b |
| K43 escaped-placeholder spelling | PINNED | TESTED | tests/test_redact_own_output.py::test_only_the_exact_escaped_shape_is_left_alone; tests/test_redact_own_output_hardening.py::test_legitimate_own_output_is_left_alone | nobody |
| K44 wrapped secret | FIXED | TESTED | tests/test_redact_own_output_hardening.py::test_a_secret_wrapped_in_lookalike_brackets_is_masked (10 failed before; ab6ff2f) | nobody |
| K45 finder on its own output | FIXED | TESTED / UNVERIFIED (other places) | tests/test_redact_own_output.py::test_the_tool_error_path_adds_no_map_entry_and_keeps_the_escaped_text (8 failed before); caller table in tickets/G7-context-after-sweep.md (reading) | nobody |
| K46 separators in a secret | STATED | NONE | SECURITY.md "Stated limits of redaction" (origin/main, ce70eb5, 2026-11-04) | nobody |
| K47 look-alike search in the finder | FIXED | TESTED | tests/test_redact_g3_port.py; pick batch; merged in d95a727 | nobody |
| K48 escapes, newer characters, hidden marks | STATED | UNVERIFIED | tickets/G1-result-review-1.md line 17 (documented limits confirmed by reading) | nobody |
| K49 Chinese zero (U+3007) | PINNED | TESTED | tests/test_textnorm_mixed_script_micro.py::test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed; evidence/TW-order020.md (1 of 852 table entries) | nobody |
| K50 over-matching | OPEN | UNVERIFIED / NOT RUN | G1 review M5 (reading; "Mary" in "summary"; the views case-fold); fold evidence runner (STATUS-BOARD: running; no evidence file) | core-c |
| K51 folding has no time limit | OPEN | UNVERIFIED | G1 review M4 (reading) | core-c |
| K52 long Chinese or Japanese text | STATED | MEASURED | evidence/G1-fold.md "G1 fix round 1", M6 (300,000 characters; threshold not measured) | nobody |
| K53 dashes, quotes, slashes (U+2215, U+2571, U+29F8) | PINNED | TESTED | tests/test_redact_g3_port.py::test_typography_* (five tests); ORDER 014 item 9 (06:15 UTC) | nobody |
| K54 Latin accent matching | PINNED | TESTED | tests/test_evidence_decomposed.py::test_known_difference_from_main_an_invisible_character_between_a_letter_and_its_accent_now_joins_them; ORDER 010 item 3 (05:47 UTC) | nobody |
| K55 other scripts (grounding, runtime/evidence.py) | OPEN | UNVERIFIED | G1 review M7 (reading) | owner (decision 4) |
| K56 undo recombines | FIXED | TESTED | tests/test_undo_composes.py (9 of 10 failed before) | nobody |
| K57 boundary split | FIXED | TESTED | tests/test_injection_chunk_boundary.py (6 failed before) | nobody |
| K58 start-up order | FIXED | TESTED | tests/test_app_unicode_check_order.py::test_a_wrong_unicode_version_refuses_a_pilot_build_before_any_backend_is_made (3.13, version stubbed) | nobody |
| K59 requested-by line | WAITING | UNVERIFIED | G2 review M3 (reading); requests/5-card-ids-redact-defang.md | core-b |
| K60 link check shares patterns | OPEN | UNVERIFIED | G2 review M6 (reading) | core-c |
| K61 glued e-mail | FIXED | TESTED | tests/test_text_parts_together.py::test_glued_email_regression_digit_or_underscore_behind_the_address; tests/test_p1d_a_paths.py::test_glued_addresses_are_masked_whole_in_one_pass; merged in d95a727 | nobody |
| K62 admin page | OPEN | NOT RUN | G2 review "not checked" (the admin console) | core-c |
| K63 install on 3.12 succeeds | OPEN | NOT RUN | pyproject.toml line 8 `requires-python = ">=3.12"` (read at HEAD and on origin/main); no request file | core-b (core-c writes the request if the lead agrees) |
| K64 planted edge values over 256 | OPEN | UNVERIFIED | F-r3 design M1(b) (reading) | core-c (gate fix round 4) |
| K65 safety net held values only | OPEN | UNVERIFIED | F-r3 design M3 (reading); runmap.py:827-833 `held_value_left` checks `snap.secret_held` only (read) | core-c (gate fix round 4) |
| K66 tool name slot vs tool list | OPEN | UNVERIFIED | F-r3 codebase M1 (reading) | core-c (gate fix round 4) |
| K67 install list misses judge sites | OPEN | UNVERIFIED | F-r3 codebase M3, M4 (reading) | core-c (gate fix round 4), then core-b |
| K68 rolled-back spelled entry | OPEN | UNVERIFIED | G7-r2 codebase M4, design M3 (reading; redact.py 1520-1532, 1613-1614) | core-c (secret finder fix round 3) |
| K69 map not checked as the run's own | OPEN | UNVERIFIED | F-r3 design M4 (reading); overlaps ORDER 020 m-2 (contested, DECISIONS 07:35 UTC) | owner (with decision 6), then core-c |

State items (not gaps):

- Gate not installed: tests/test_gate_install_callers.py holds 3 strict expected failures (lines 210-236) until core-b installs. tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered passes since aa7c5fa (commit message; DECISIONS 07:40 UTC).
- The 50-connection test: tests/contracts/test_t1_reserve_cap.py::test_fifty_connections_against_a_cap_of_three_grant_exactly_three, plus 16 more cases (evidence/T1-reserve-cap.md), 49 passed twice on PostgreSQL 16.15, Python 3.13.18.
- Pick batch: 12,392 passed, 2 failed, 108 skipped, 7 xfailed in 135 files (-n 2, not perf). Failures and their ends: see the [INTERNAL] lines of 2.0. NOT RUN there: Python 3.12, PostgreSQL 17, the full suite, the full batch after the re-pin.
- G7 fix round 2 batch (evidence/G7-1.md): 9681 passed, 73 skipped, 5 xfailed, 0 failed (251 s). The commit it ran on is not recorded; the line was committed in 0fcc5e1 (07:44 UTC), after a2b6311 (07:41 UTC).
- Mutants: evidence/F-G0-1.md "Review round 2 fixes (final)" records "81 of 81 good; problems: []". This drafter counted 81 `mutant(` calls in tests/gate_mutants.py at HEAD (AST count, no mutant run). Search-text matching at HEAD not checked.
- Gate tests behind part 2.1 to 2.4: T::test_pin_no_client_call_without_a_reservation; T::test_t1_pass_path_order_is_enforce_reserve_call_settle_audit; T::test_t12_a_spend_refusal_passes_unchanged_and_no_call_is_made[kill_switch]; T::test_pin_every_outcome_writes_exactly_one_audit_row; T::test_i9_the_module_has_no_logger_no_exception_text_and_no_module_state; T::test_t18_no_secret_in_any_audit_row_exception_or_log_record; T::test_t17_a_raising_audit_sink_never_loses_the_reply_or_the_settle; T::test_m2_settle_raising_after_a_paid_call_returns_the_reply_and_the_row_says_ok.
- Those gate tests last ran in the gate builder's batch "1 failed, 2307 passed, 2 xfailed" (evidence/F-G0-1.md line 244, before the review-round-2 fixes). The one failure is named there: the producers registry test.

### 4.3 Counts by status (69 gaps)

| status | count | gaps |
|---|---|---|
| PINNED | 15 | K1-K9, K22, K24, K43, K49, K53, K54 |
| STATED | 10 | K19, K27, K28, K30, K33, K34, K35, K46, K48, K52 |
| WAITING (all on core-b) | 7 | K18, K20, K21, K23, K25, K42, K59 |
| OPEN, core-c acts | 15 | K12, K13, K17, K38, K39, K41, K50, K51, K60, K62, K64, K65, K66, K67, K68 |
| OPEN, the owner decides or core-b acts | 10 | K14, K26, K29, K31, K32, K36, K37, K55, K69 (owner); K63 (core-b) |
| FIXED | 8 | K40, K44, K45, K47, K56, K57, K58, K61 |
| FIXED ON BRANCH | 4 | K10, K11, K15, K16 |
| total | 69 | 15 + 10 + 7 + 15 + 10 + 8 + 4 = 69 |

By evidence level (each gap counted once; 57 single + 12 mixed = 69):

- TESTED only: 20 (K1, K2, K4-K9, K22, K24, K43, K44, K47, K49, K53, K54, K56, K57, K58, K61).
- MEASURED only: 5 (K35, K36, K37, K38, K52).
- UNVERIFIED only: 20 (K17, K18, K19, K23, K26, K29, K31, K32, K42, K48, K51, K55, K59, K60, K64, K65, K66, K67, K68, K69).
- NOT REPRODUCED: 1 (K12).
- NOT RUN only: 5 (K10, K15, K25, K62, K63).
- NONE: 6 (K27, K28, K30, K33, K34, K46).
- Mixed: 12 (K3 TESTED+UNVERIFIED; K11 NOT RUN+UNVERIFIED; K13 MEASURED+UNVERIFIED; K14 TESTED+NOT RUN+UNVERIFIED; K16 NOT RUN+UNVERIFIED; K20 TESTED+UNVERIFIED; K21 TESTED+UNVERIFIED; K39 TESTED+UNVERIFIED; K40 TESTED+UNVERIFIED; K41 MEASURED+UNVERIFIED; K45 TESTED+UNVERIFIED; K50 UNVERIFIED+NOT RUN).

Changes from v4 (statuses unchanged; evidence levels only): K17 NONE to UNVERIFIED (its source is the gate ticket's reading). K19 NONE to UNVERIFIED (the install test's BYPASS table). K31 NONE to UNVERIFIED (a review's reading and the code). K40 TESTED to TESTED + UNVERIFIED (batch version). Totals: TESTED only 21 to 20; UNVERIFIED only 17 to 20; NONE 9 to 6; mixed 11 to 12. Actor column: "lead (decision N)" became "owner (decision N)".

Gaps named in part 1 (28 of 69):

- item 5: K25, K20, K21, K23, K42, K59, K18, K8 (request), K63;
- item 15 K34; item 16 K37; item 17 K36; item 18 K8; items 19-20 K19; item 21 K35, K46, K38; item 22 K42; item 23 K65, K66, K67;
- item 24 K25; items 25-26 K20; items 27-28 K24; item 29 K21; item 30 K23; item 31 K26;
- items 32-33 K68; item 34 K29; item 35 K14; item 36 K64; item 37 K13; item 38 K41; item 39 K63;
- item 47-48 K39.

Distinct: K8, K13, K14, K18, K19, K20, K21, K23, K24, K25, K26, K29, K34, K35, K36, K37, K38, K39, K41, K42, K46, K59, K63, K64, K65, K66, K67, K68 = 28.

Order rule (item 8): groups first; within a group wider exposure first, roughly; a tested or measured gap before an UNVERIFIED one of about the same width. Money group in v5: K25 (all reservations), K20, K24, K21 (TESTED parts), K23, K26 (UNVERIFIED).

### 4.4 Where two sources disagreed

1. Short-value exemptions: we used the later gate ticket (they do not apply to a secret of 4 or more characters), because it was checked against the sweep's code; v4's drafter read the same rule in redact.py `_sweep`.
2. Settling after a plain connector error: we used ORDER 011 (not at all), because it replaced the earlier order.
3. A bind without a map: we used ORDER 017 (an error; NO_MAP must be named), because it is newer.
4. The judge (no map, or the run's map): we used ORDER 017 item 1 (the run's map), because it is newest.
5. The tool-error double pass ("harmless", or a gap): we used the G7 review (a gap, K42), because the ticket's author withdrew "harmless".
6. Search rounds per call: since c9478a9, `_SETTLE_ROUNDS` = 4 gives up to 5 rounds per call. "Up to 7 calls per text" stays a reviewer's reading (G7-r2 design M4), marked UNVERIFIED.
7. Escaped look-alikes: we used the G7 fix evidence (only `‹SECRET_n›` with ASCII digits), because it is newer and tested.
8. The forged-marker leak: we use evidence/F-G0-1.md (reproduced, then fixed in work in progress); F-r3 design reads it as closed. Batch NOT RUN.
9. The glued-digit e-mail: we used the integration evidence; it is merged (d95a727), so FIXED.
10. G2 evidence (two failures, or fixed): we used its fix round (fixed, 7,879 passed), because it comes later in the same file.
11. The spacing-mark test: we used the integration batch and the G text ticket (the lead chose option a), because both are newer.
12. The G1 blockers: we used the G1 fix round (fixed, tests failed before). No independent re-review exists.
13. Whether folding is wired into the secret finder: since d95a727 it is on cloud/core-c (K47 FIXED). Not on main.
14. A failed call's booking: we used core-b's interface README and T1's expiry case. Expiry closes the row, but the amount stays booked. Day and month both keep it (worked out: UNVERIFIED).
15. Dash, quote and slash choice: we used ORDER 014 item 9 (accepted, 06:15 UTC).
16. The third-round chain: we used ORDER 020 MJ-B (a capped repeat that refuses), now built (c9478a9).
17. The overshoot example: the test holds three reservations of 1.00; one settles at 2.50: 1.00 + 1.00 + 2.50 = 4.50.
18. Base64 counts (41 of 41, or 52 of 142): both true: rows under 40 characters, and all rows, on the main code.
19. The 3.12 test job: the lead's 3.12 run of old branch P1a had one real failure; the G text ticket reads it as a test slip repaired in the folded code. That repair is UNVERIFIED on a real 3.12.
20. The deliberate code breaks (66 of 66, 24 stale, or 81 of 81): all true at different times. 81 = 66 + 15 added.
21. The planted-word refusal scope: ORDER 017 item 6 (refuse on any marker word, tool name or call id) versus the builder's narrower rule. We describe the narrower rule, as it is the code in the WIP commits; the owner decides (decision 1).
22. The month cap: we used evidence/T1-reserve-cap.md, because it lists the case.
23. "If writing the row or settling fails, the reply is still returned": we used the gate tests t17 and m2.
24. K12: OPEN, NOT REPRODUCED, until a fresh review.
25. K32: we used E7 item 5.
26. The producers registry test (v2: red on purpose) versus DECISIONS 07:40 UTC (closed by aa7c5fa): we used DECISIONS, and mark the closing pass UNVERIFIED (no evidence file holds it).
27. "Verified" merge (d95a727 message) versus the PICK evidence: we say "tested before the merge; the merge result was not re-tested".
28. Decision 3's "blocking problems" come from tickets/G4-review-1.md (8 Blockers, 6 distinct) and, for v2, tickets/G4-review-2.md.
29. The size of the producers edit: git show --stat aa7c5fa says 2 lines added; DECISIONS 07:40 UTC says "a 4-line edit". We used git.
30. Gate round 2 batch: c9478a9's message says "302 passed"; no evidence file holds that result line. We keep NOT RUN for the batch.
31. c9478a9's title versus its file list: DECISIONS 08:05 UTC now confirms it swept in G7 work in progress. We date the gate code by fb08bde.
32. The 2026-11-23 date: neither ORDERS.md nor DECISIONS.md holds it (grep for "11-23" at HEAD). We say "proposed by core-c, not confirmed in writing". The 2026-11-22 draft-note date of decision 3 is this drafter's proposal (review 4 style M12).
33. G7-r2 codebase counts: its header says 5 Majors; it lists M2 to M7 (6). We count 6.
34. K35's source: G4 v2 cites "order 64 item 4"; ORDERS.md line 64 is ORDER 006 item 1. Status kept STATED because two written files call it accepted. v5 says in part 1 and part 2 that the cited order was not found.
35. New: the "1 failed" of the gate batch (review 4 comprehension M1 calls it unidentified) versus evidence/F-G0-1.md line 244, which names it (the producers registry test). We used the evidence file.
36. New: decision 6 default "refuse, as ordered" versus the code at HEAD: model_gate.py line 201 `MODE_EMPTY = "map_enforced_empty"` accepts and marks an empty map. Part 1a now says both.
37. New: K33's source line: v4 cited "plan-v4-final B2"; the text is in B3 "Audit" (line 32). K30 is B3 "Stop" (line 30).

### 4.5 Requests to core-b (files in handover/core-c/requests)

1. 1-producers.patch: register the gate as a model caller (applied by core-c as aa7c5fa; decision 7).
2. 2-refused-before-response.md: the "refused before any answer" mark (K20).
3. 3-bind-mapping-required.md: required map, `GateRefused`, empty cost, catch sites, prompt-registry install check (K8, K18, K21). To add (core-c, not done in this file): "one writer per run map" (K17); the judge call sites (K67, gate fix round 4 lane).
4. 4-error-reason-run-map.md: tool-error text with the run map (K42).
5. 5-card-ids-redact-defang.md: id fields on approval messages (K59).

Lead's orders to core-b without a request file: sum the cost of all attempts (ORDER 017 item 3, K23); the worst-case formula (ORDER 016c item 13, K25); an operator release for expired reservations (ORDER 017 item 4); the install test with core-b (ORDER 020 MJ-C). K63 has no request yet: core-c writes one if the lead agrees. None of the request files changed since v4 (git diff 11935aa..HEAD).

### 4.6 What is still moving at the time of writing (2026-11-20 08:09 UTC)

- Gate fix round 4 (builder gfix4; F-result-review-3.md "Round 4 fix agent starts now"; lane: model_gate.py, runmap enforce functions, gate tests, request 3, ticket, evidence): NOT RUN. K3 (alias), K13, K14, K16, K64, K65, K66, K67, K69 depend on it. K10, K11, K15, K16 still need a recorded batch. Nothing about its result is stated here.
- Secret finder fix round 3 (builder g7fix3, "G7 fix round 3"; G7-result-review-2.md "Round 3 fix agent starts now"; lane: redact.py, runmap.redact_text, G7 tests, ticket, evidence): NOT RUN. K39, K41, K68 depend on it. G7-r2 codebase M5 (clock) is in the gate fix round 4 lane. Nothing about its result is stated here.
- G4: v2 plan review round 2 reported at 07:53 and 07:59 UTC (NOT READY); the v3 drafter (g4v3) is running; decision 3.
- Fold false-hit measurement: STATUS-BOARD says "fold evidence" running; no evidence file (K50).
- Also running per STATUS-BOARD 08:09 UTC (no gap status depends on them here): p1dr2 (P1d-a M6 independent link oracle: K60), g8 (glued-rest ticket: K38), drift report.
- Lead verdicts pending: DECISIONS 07:35 UTC (empty-map contest, decision 6; K69) and 07:40 UTC (producers edit, decision 7); decision 1 (framing rule); F-r3 asks the lead about the planted tool-name value.

### 4.7 INTERNAL: change log of review round 4 (does not ship)

Findings from tickets/SEC-wording-review-4.md, in its order.

Kept from rounds 1 to 3 (re-checked, not regressed):

- verdict first; glossary before part 1; one status per gap; a separate evidence column; three-line gaps;
- codes only in the appendix; the made-up values note; no self-certifying line;
- FIXED and FIXED ON BRANCH tied to the main line and to review; "Shown by tests" headings and the banner;
- the 2.2 wording of what the 50-connection test shows; the K2 rule and example;
- decision 4 "lets more / fewer names pass"; decision 5's five rights; decision 6 reasoning;
- one NOT RUN list; the UnidataMismatch name kept for operators;
- the stop-switch sentence of item 42 (round 3 Blocker); the 2 pick-batch failures named with their ends;
- NOT REPRODUCED for K12; "item N" wording; "calling code";
- the round 3 contests: the capped-repeat batch; K19 not made a decision; K63 request not written here;
- no invented dates for decisions 2, 4 and 6, now said as "no build date; the owner may ask for one".

Comprehension findings (the ticket lists 9 Majors and 14 nits, numbered 10 to 23):

| finding | TAKEN / CONTESTED, and where or why |
|---|---|
| M1 gate tests ran before the review fixes; reviewers keep finding faults | TAKEN: items 2-4, 2.0 and the 2.1 lead-in say the batch ran before the latest fixes; item 4 says reviewers keep finding faults (9 Majors). CONTESTED in part: the one failure is not unidentified; evidence/F-G0-1.md line 244 names it (4.4 item 35). |
| M2 3.12 refusal in present tense | TAKEN: item 39 and K63 start "Once the text-folding change ships"; part 3 keeps its [INTERNAL] ship-with line. |
| M3 part 2 word box incomplete; FIXED caveats dropped | TAKEN: part 2's box now copies every part 0 definition it uses, including every term listed, and the full FIXED definition. |
| M4 part 3 does not stand alone | TAKEN: part 3 defines operator, kit, stages, text folding, Unicode, the marks and the secrets vault; says what happens on 3.11 and 3.14; "the text and masking team" removed. |
| M5 two actors; empty-map question on a stripped line | TAKEN: the owner decides each of the seven; every part 2 line names the default and the date; K69 states the empty-map question in one line. |
| M6 defaults incomplete; DECISIONS.md undefined | TAKEN: item 11 and decision 3 say silence means the note is not sent. 1a says "no build date; the owner may ask for one". Decision 1 no longer waits on a fix round. DECISIONS.md is defined in part 0. |
| M7 summary omits K13/K41, K68, K29 | TAKEN: items 32-33 (K68), 34 (K29), 37-38 (K13, K41) added; item 33 says why K68 ranks below the secrets group. |
| M8 ordering rule broken in money | TAKEN: both. The money group is reordered (TESTED parts first after the formula) and item 8 says the order is rough. |
| M9 K35 shows "accepted" | TAKEN: a visible sentence in item 21 and in K35: the cited order was not found, so the acceptance is UNVERIFIED. Status kept STATED (4.4 item 34). |
| N10 "now names the gate" | TAKEN: decision 7 says "a list entry, not an install". |
| N11 round naming | TAKEN: "gate fix round 4" and "secret finder fix round 3" everywhere; defined in part 0 and 4.1. |
| N12 "worked out, not run" | TAKEN: now "UNVERIFIED (worked out, not run)" (K13, K20, item 26). |
| N13 K19 NONE but a test table | TAKEN: K19 evidence UNVERIFIED (read in the install test's table). |
| N14 "302 passed" commit holds the finder's files | TAKEN: moved to an [INTERNAL] line of 2.0 with DECISIONS 08:05 UTC. |
| N15 "short base64" undefined | TAKEN: item 16 "under 40 characters"; base64 defined in part 0. |
| N16 why 2 of 240 ran; why database 17 matters | TAKEN: item 9 says both. |
| N17 "audit marks" | TAKEN: the phrase is gone. |
| N18 two logins | TAKEN: item 31 names the runtime and purge logins. |
| N19 "no numbers" | TAKEN: "Part 1 uses no K numbers". |
| N20 copied sections end with `---` | TAKEN: the strip step stops before the `---` line. |
| N21 PINNED actor | TAKEN: PINNED names the team whose change closes the gap, and the connector and store team for the install tests. v4's log claim was wrong. |
| N22 v4 log said "audit marks" handled | TAKEN: this log replaces it; the phrase is now gone. |
| N23 `python3 --version` | TAKEN: "or use the Python you install the kit with", plus a command that prints the Unicode edition. |

Style findings (the ticket says 12 Majors and 12 or more nits). It lists change log (a) to (e), M1 to M12, nits 13 to 24, a long-sentence list and two markdown items:

| finding | TAKEN / CONTESTED, and where or why |
|---|---|
| (a) M14 K48 example false | TAKEN: K48 now shows `&#49;` and `abc&#49;` in code spans. |
| (b) comprehension 10: K34 no date | TAKEN: K34 names the README on the main line since 2026-11-04. Every STATED line now has a source and a date. |
| (c) v4 counted comprehension 10 as contested | TAKEN: v4's closing count was wrong; its round 3 contests were comprehension 5, 12, nit 15 and the K19 alternative inside 10. |
| (d) DECISIONS times lack UTC | TAKEN: "UTC" after every time. |
| (e) one round, two names | TAKEN: see comprehension N11. |
| M1 word box incomplete | TAKEN: see comprehension M3. Part 3 defines pilot, prod, demo and kit. |
| M2 FIXED definition in part 2 | TAKEN: the full definition, as written in part 0. |
| M3 9,681 batch version | TAKEN in part: the caveat "which saved version ... UNVERIFIED" is on K39, K40, item 47 and 2.5. CONTESTED: K40 stays FIXED, because FIXED needs a recorded batch on the builder's copy, and that exists (4.4, 4.1 0fcc5e1). |
| M4 K63 hedge after the fact | TAKEN: "Once the text-folding change ships, by design ..."; NOT RUN and the UNVERIFIED file reading are stated. |
| M5 "never under-counts" false | TAKEN in part: the claim is dropped from K16 and K22. CONTESTED: the proposed "never lower than the real cost" is also false when a call costs more than its worst case (K24). So both say "the worst case stays booked, not the real cost". |
| M6 empty-map question; one actor | TAKEN: see comprehension M5. |
| M7 build history in SECURITY.md | TAKEN: batch counts, commits and fix rounds are on [INTERNAL] lines. 2.0 keeps: not installed (WAITING), fixes saved but in no batch (NOT RUN), and 2.9 the NOT RUN list. |
| M8 2.7 "Shown by tests" | TAKEN: 2.7 splits "Shown by tests" (TESTED) from "Read, not tested" (UNVERIFIED); the function count is on an [INTERNAL] line. 2.5 split the same way. |
| M9 K17 NONE | TAKEN: "UNVERIFIED (reasoned from the code in the gate's written plan, not run)". |
| M10 K24, K25 speculation | TAKEN: dropped; K24 says the overshoot depends on a formula that does not exist yet. |
| M11 unseen sources, hidden actors | TAKEN: "the project's written plan, frozen on 2026-11-20" and "the project's written order of 2026-11-20 hh:mm UTC" (K19, K27, K28, K30, K33, K53, K54, 2.0). |
| M12 decision 3 two actors | TAKEN: the lead sends the draft by 2026-11-22 12:00 UTC; the owner says by 2026-11-23 12:00 UTC whether to send it. The first date is a proposal (4.4 item 32). |
| N13 slowdown evidence word | TAKEN: MEASURED, in seconds. |
| N14 database 17 | TAKEN: 2.9 says the tests ran on 16.15 only. |
| N15 "256 KB" | TAKEN: 262,144 characters. |
| N16 K51 "very large" | TAKEN: 2,097,152 characters. |
| N17 replace -> mask | TAKEN: "masks" in 2.1 and K3; the Mask and Settle definitions no longer say "replace". |
| N18 K10, K11, K15, K16 titles | TAKEN: "Fixed on branch:". |
| N19 K50 letter case | TAKEN: the example is lower case (`mary` in `summary`). |
| N20 items lack evidence words; K18 example | TAKEN: every part 1 item and every "Shown by tests" line starts with its evidence word; K18 example marked UNVERIFIED. |
| N21 3.14 no action | TAKEN: "Do not run pilot or prod on Python 3.14 or later until the release notes say the character tables were rebuilt for it." |
| N22 UnidataMismatch fix | TAKEN: "The fix is to install Python 3.13." |
| N23 strip step `---`; long sentence | TAKEN: four numbered steps, short sentences, "stop before the `---` line". |
| N24 K8 carries a WAITING line | TAKEN: the request is on an [INTERNAL] line; K8 has one status. |
| Sentences over 30 words | TAKEN: every listed line split; a script checked parts 0 to 3 and the 4.7 tables (none over 30 words). |
| Markdown: header lines 3-6; lists in 4.2, 4.3 | TAKEN: blank lines between header paragraphs and before every list. |

Owner-summary additions asked by the coordinator: hostile text that stalls a run (K13, K41: items 37-38), a wrong value restored (K68: items 32-33), the stop-record signing gap (K29: item 34). All TAKEN as items, not ranked lower.

Facts changed since v4 (read from the repo at 6b990d9, not from the reviews):

- G4 v2 plan review round 2 reported NOT READY (tickets/G4-review-2.md); a v3 drafter runs.
- DECISIONS 08:05 UTC records how c9478a9 was made.
- No file under src/, tests/ or requests/ changed since 11935aa.
- The G7 batch line was committed at 07:44 UTC, after a2b6311.
- The code at HEAD accepts an empty map (decision 6).
- The gate batch's one failure is named in evidence/F-G0-1.md.

Contested in all: 3 findings, each in part, each with its reason above:

- comprehension M1 (the failure is identified);
- style M3 (K40 status kept FIXED);
- style M5 (the proposed wording is also false).

All other findings are TAKEN.

Checks after writing, by a script (scratchpad check_v5.py):

- each part 2 status equals the 4.2 status, and each 4.2 evidence word appears in the part 2 entry;
- every K1 to K69 appears once in part 2 and once in 4.2; the 4.3 counts and evidence levels match 4.2;
- part 1 holds no K numbers, and the 4.3 list of part 1 gaps holds 28 distinct gaps;
- no project words in parts 2 and 3 outside `[INTERNAL]` lines;
- no sentence over 30 words in parts 0 to 3 or in 4.7; a blank line before every list and table.
