# Security wording v6: what the tests show and what is still open

DRAFT, version 6, written on 2026-11-20 by the lead's laptop job "wording" (job 3 of requests/lead-build-1.md). It is a copy of SECURITY-README-v5.md with the edits marked, and replaces it. It has had no fresh style review (core-c runs that). It describes the code at head a60da3394 of cloud/core-c. Every edited line in parts 0, 1 and 4 starts with "[v6]" or holds it; every edited gap in parts 2 and 3 carries an "[INTERNAL] v6" line with its file and line proof. The full proof table is in evidence-cword.md (egm/core-complete-2026-11-20/evidence-cword/).

Who reads what: part 0 and part 1 are for the owner only. Part 2 ships as SECURITY.md. Part 3 ships as README.md, section "Python version". Part 4 is internal and does not ship.

Strip step before shipping, for whoever copies the text:

1. Copy part 2 into SECURITY.md. Start at its heading. Stop before the `---` line that comes before part 3.
2. Copy part 3 into README.md. Start at its heading. Stop before the `---` line that comes before part 4.
3. In both copies, delete every line whose text starts with `[INTERNAL]`. Ignore any list dash and spaces in front of it.
4. Delete nothing else.

After step 3, parts 2 and 3 name no project, team code or session. They say "the owner", "the connector and store team" and "the text and masking team".

This draft changes no other file.

[v6] Reading rule for v6: v5 was written at head 6b990d9. Where the code at a60da3394 contradicts a v5 statement, v6 re-words it. Where v5 rested on the connector and store team's store code, which is not on this branch, v6 strikes the statement and lists it in evidence-cword.md (egm/core-complete-2026-11-20/evidence-cword/). Where v5 rested on a process fact (a review, an order, a running agent), v6 keeps only what a file at this head shows.

---

## 0. Plain glossary (read this first)

[v6] As of repository head a60da3394 (cloud/core-c, board commit 2026-11-20T12:25:45Z).

### How to read the marks (one list)

Evidence words (how we know). Every claim carries one of these:

- **TESTED**: a named test ran and passed in a recorded batch of tests. A recorded batch is one whose result line is in an evidence file.
- **MEASURED**: a recorded run measured the number given.
- **UNVERIFIED**: the only basis is someone reading the code or the text. Nothing was run to show it.
- **NOT REPRODUCED**: a reviewer reported a fault from reading. A builder then ran the reported case and did not see the fault. No fresh reviewer has checked the builder's run.
- **NOT RUN**: the check was not run at all, or no recorded result exists. Nothing is claimed about its result.
- **NONE**: no test, run or reading is named. The gap is written down from a plan, an order or the published SECURITY.md only.

Status words (one per known gap):

- **FIXED**: changed, and a test fails without the change. The change is on the shared branch. A recorded batch that holds that test passed on the builder's copy of the code or on the merged tree. The whole test suite was not run on it. It is not on the product's main line. [v6] An independent review is named in part 4 where one exists. [v6] FIXED ON BRANCH is retired: no gap uses it any more.
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
- [v6] **Gate fix round 4 and the secret finder fix rounds 3 to 7**: the rounds of fixes that answered the reviews. They are merged on the shared branch. Their codes are in 4.1.
- [v6] Note: the lead's laptop job "wording" wrote v6 from the code at head a60da3394 and lists its proof in evidence-cword.md (egm/core-complete-2026-11-20/evidence-cword/). Nobody outside that job has checked v6. Statements v5 made about the connector and store team's store code are struck, because that code is not on this branch.

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
- **Known gap**: a weakness we know about, or a gap fixed in this work. Each has a number K1 to K76, used in parts 2 and 4. Part 1 uses no K numbers.
- **Item**: one numbered line of part 1.

---

## 1. Owner summary

[v6] As of head a60da3394 (2026-11-20 12:25 UTC).

### What to know first

1. **Short answer: the gate is written but not installed. No agent in use goes through it. Do not promise a client any gate protection yet.**
2. [v6] TESTED: merged-tree batches of 15 test files, run after the gate's round-4 fixes, passed. The last recorded result is 2,687 passed, 1 skipped, 5 xfailed. The 5 xfails are the install tests, which pass only once the gate is installed.
3. [v6] UNVERIFIED (stated in DECISIONS.md, not in an evidence file): the test that every model-calling module is registered, which named the gate, has passed since a two-line change (DECISIONS.md line 39).
4. [v6] Reviewers found faults in the gate three times. Round 4 fixed their findings (merged). No independent review of the round-4 gate code is recorded, so treat that code as unreviewed.
5. The connector and store team must write the worst-case formula, add the "refused before any answer" mark and install the gate. It also has seven other open items:
   - empty cost fields;
   - retried calls;
   - tool-error text;
   - approval-message id fields;
   - the run's status after a refusal;
   - a start-up check that system prompts come only from the prompt registry;
   - installs on Python 3.12, which has no written request yet.
6. [v6] The text and masking team's planned host-name and base64 change and its overlap fix are not on this branch: git log shows no code commit for either. Nothing in this file describes them. The lead owes three decisions on merged work (part 1b).
7. [v6] This summary names 32 of 76 known gaps. The groups come in this order: secrets that can reach the AI service, then money, then wrong actions, stopped work and set-up.
8. Within a group, the order is a rough judgement. Wider exposure comes first. Where two gaps are about as wide, a tested or measured one comes before an UNVERIFIED one.
9. [v6] NOT RUN on this work's code:
   - the full test suite (the lead's laptop jobs have not reported);
   - Python 3.12;
   - database version 17, the version the automatic test service is set to use;
   - the spend-cap tests on PostgreSQL: the store code they test is not on this branch, so they skip;
   - any live call to an AI service;
   - any end-to-end stop of a live run;
   - the whole-file deliberate-code-break runs for text folding (256 breaks; the builder ran 25), the gate and the secret finder at this head;
   - the merged code as a whole (the batches cover 15 test files).
10. **Your action (the owner):** read the seven decisions in 1a. Answer the lead by 2026-11-23 12:00 UTC. For each decision, keep the default or choose another answer.
11. If you have not answered by then, each default in 1a applies. Silence on decision 3 means the client note is not sent. The lead records each answer, or each default, in DECISIONS.md.
12. [v6] The text and masking team proposed this date. As of head a60da3394 the lead has not confirmed it in writing (a search for "11-23" in ORDERS.md and DECISIONS.md finds nothing).
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
   - [v6] MEASURED on this head: an IP address, phone number with `+`, UUID or bank account number with a letter or `_x` glued behind it is now masked (`10.20.30.40_x`). Shapes left readable by design are in items 49 and 50.
22. UNVERIFIED (read from the code, not run): a secret first seen in a tool's error message is not masked in later text. It waits on the connector and store team.
23. [v6] TESTED: the three leak paths named in v5 are closed. The safety net now checks every known secret of 4 or more characters. A known value inside a tool's name no longer splits the name. The hand-over list names the judge's call points.
   - One limit remains: a secret that spans a fixed framing word goes out as written (PINNED, TESTED).

### Money (worst first)

24. [v6] UNVERIFIED (read from the code; nothing to test yet): the gate's worst-case function is not written. The one worst-case function in the tree prices only the system prompt and the messages and serves the replay command line. Until the connector and store team writes the gate's function, the cap has nothing real to reserve.
25. TESTED: the gate does not settle a failed call, so its worst case stays booked.
26. [v6] TESTED (the gate's side): the gate does not settle a failed call. UNVERIFIED: what the store then keeps booked. That is the connector and store team's code, which is not on this branch. v5's example of three failed calls stopping an agent is struck (NOT PROVABLE here).
27. [v6] Struck: v5 said TESTED that booked money can pass the cap. That test needs the store code on PostgreSQL, which is not on this branch. What stays TESTED: the gate passes a higher real cost to settle at that cost.
28. [v6] Struck with item 27: the 4.50 USD example needs the store code.
29. TESTED (the gate's side only): a reply with an empty cost field is booked as free. UNVERIFIED: that a model connector ever leaves the field empty.
30. UNVERIFIED (read from the code): when a call is retried, only the last attempt's cost is counted. Earlier billed attempts are lost, so spending is understated.
31. [v6] UNVERIFIED (read from the grant map; no database test run): the runtime login holds SELECT, INSERT and UPDATE on the spend counters and on the stop switch. So faulty code could lower a booked amount. Decision 5 covers it. v5's claim that a purge login can delete an open reservation is struck: that table is not on this branch.

### Wrong actions, stopped work and set-up

32. [v6] FIXED (TESTED): after the secret finder undoes a half-made entry, no old record survives. So a later placeholder is restored to the right value.
33. [v6] Item 32 is closed. Nothing remains of the wrong-value restore.
34. [v6] UNVERIFIED (read from the grant map and the migrations): the runtime login can change the stop switch, including back to off. It can also sign a stop record with any name. So the record of who turned the stop switch on cannot be trusted. Decision 5 covers it.
35. [v6] TESTED: planted text can make a run's later tool-using calls refuse. It does so if it plants a secret of 4 or more characters that equals a tool's name or a piece of one. Decision 1 covers it.
36. [v6] TESTED: the gate now accepts up to 4,096 values at a placeholder's edge and 20,480 entries in all. Past that, every later call of that run refuses. UNVERIFIED: that the run map only grows.
37. [v6] Hostile text can still make one gate call run long, because one scan of one stretch of text cannot be interrupted. UNVERIFIED (a figure in the gate's own notes): about 7 seconds for 262,144 characters. A call past its budget is refused. v5's estimate of 128 million steps is struck.
38. [v6] MEASURED earlier: one call of the secret finder on a text built to be slow took 4.5 to 5.4 seconds against its 6-second budget. The budget is now read inside the masking step too, but not inside one pattern pass.
39. Once the text-folding change ships: by design, a pilot or prod install on Python 3.12 succeeds, and then the program refuses to start. NOT RUN on Python 3.12.

### Shown by tests (each in the teams' own tests, on the code alone)

40. TESTED: in the gate's tests, known values are masked before a call, in message text and documents only. They are not masked when the calling code states "no map".
41. TESTED: only the test and replay command lines may state "no map".
42. TESTED: in the gate's tests a refused reservation means no call. UNVERIFIED: that the store refuses while the stop switch is on. NOT RUN: any stop of a live run.
43. Item 42 does not cover a call already in flight, the test and replay command lines, or the guardrail call.
44. [v6] Struck: the 50-connection cap test (PostgreSQL 16, the store code) is not on this branch. It skips here (NOT PROVABLE).
45. [v6] Struck with items 27 and 44.
46. TESTED: in the gate's tests, its code holds no message or error text, and no audit row in those tests held a secret.
47. [v6] TESTED: in the secret finder's tests, a chain of planted values that needs a third search round is masked. The tests are in the merged-tree batches (the last: 2,687 passed).
48. [v6] TESTED: the repeated search runs until a round changes no text, at most 5 rounds, and refuses a text still changing after round 5. Two overlaps still leave part of a value readable (item 51).

### [v6] New since v5 (merged work, measured or tested on this head)

49. [v6] MEASURED on this head: glued shapes left readable by design. A phone or card number as one run of digits with a letter beside it (`x4155550132`). A phone number directly before a full stop (`call 415-555-0132.`). An IBAN inside a file name, a path or a key (`acct_iban_DE89...`). Part 1b has the lead's three decisions on these.
50. [v6] MEASURED on this head: a UUID, or a 10-digit number, set off by `_` inside a long token cuts the token. A remainder under 40 characters stays readable (32 characters in the measured rows). Before, the whole token was masked. The lead decides whether to accept this (part 1b).
51. [v6] TESTED: two overlaps leave part of a value readable. One is a written form completed in a later round. The other is two compound values that overlap as raw text. A log author who controls the order of lines can cause both.
52. [v6] STATED (in the code's notes), MEASURED: a hostile text can make the secret finder refuse a whole document. Nothing is shown. A real document in the same text is lost.
53. [v6] MEASURED earlier: a hostile document can make the secret finder hold about 1 GB of memory in one call. No limit exists yet.
54. [v6] TESTED: a tool's error text read twice can make one extra map entry for each distinct token of another kind written after a key. No real value is stored in it.

### 1a. The seven decisions (the owner decides each one by 2026-11-23 12:00 UTC)

If there is no answer by then, the default in the fourth column applies. The last column says who then acts. No build date is set for any of them; the owner may ask for one.

| # | Question | What each answer means | Default if no answer | Who then acts |
|---|---|---|---|---|
| 1 | Planted text can make a known value equal part of a framing marker. When should the gate refuse the call? | Narrower rule: refuse only when a known secret of 4 or more characters equals a tool's name or a call number. [v6] It is built and TESTED in the merged-tree batches. The built rule also refuses when a known secret is a piece of a name in the tool list. Wider rule (the lead's earlier order): also refuse when any known value equals a fixed marker word. A reviewer proposes a third way: never store a tool's name as a secret when the secret finder adds it. UNVERIFIED that this closes the gap. | The narrower rule. Why: [v6] TESTED (the narrower rule is built): under both rules the marker's fixed words stay exact. So the wider rule's extra refusals do not appear to protect more text, and they stop more runs. Both rules still let a planted secret equal to a tool's name stop a run (item 35). | The text and masking team keeps the narrower rule in the code. The lead records the result in DECISIONS.md. |
| 2 | Should each audit row also say whether anything was masked, and which route was used? | Without it, nobody can tell from the record whether masking happened. Today the row says only how the run map was used: a map, an empty map, or no map. | Add a "masked: yes or no" field and the route. No text goes in the row. | The text and masking team builds it in a gate fix round after gate fix round 4. |
| 3 | Build the planned host-name and base64 change, or keep both as known gaps for now? | Keeping them means such values reach the AI service (items 16, 17). Plan reviewers found 6 distinct blocking problems in the first plan. [v6] The plan has since had 8 versions and 8 review rounds (tickets/G4-P1c-redactor-gaps-v8.md, tickets/G4-review-8-design.md). It is not built on this branch. | Keep both as known gaps until a plan review is clean. Do not send the client note. | The lead sends a draft client note on both gaps by 2026-11-22 12:00 UTC. The owner says by 2026-11-23 12:00 UTC whether to send it. Once a plan review is clean, the text and masking team builds. |
| 4 | Accept that the grounding check now counts a name as present in more cases in Korean, Japanese and Indian scripts? | This happens when an invisible character splits the name. Accepting lets more proposed names pass the check, with no tests for those scripts. | Go back to the older rule for those scripts until tests exist. The older rule lets fewer names pass. | The text and masking team makes the change in its next text-folding round. |
| 5 | [v6] Tighten wide database rights, or accept them in writing? | [v6] Runtime login: can rewrite the spend counters, and can change the stop switch and sign a stop record with any name (read from the grant map on this branch). v5 also named a purge login and a reset login. They belong to the connector and store team's code, which is not on this branch, so those three rights are struck. Accepting leaves the cap and the stop record resting on code alone. | Tighten them: narrower rights, or one fixed database function per action. | The lead writes the order. The connector and store team changes its database rights in its next store change, before any pilot uses the store. |
| 6 | Should the gate refuse a call whose run map is empty? Or should it accept the call and mark the audit row? | The lead's written order says refuse. UNVERIFIED (read at the repository head): today's code on the shared branch accepts and marks the row. The text and masking team asked to keep that. Refusing stops each run whose first document held no value the secret finder found. Either way the gate masks nothing in that call. A secret the finder missed goes out in both cases. [v6] The gate now refuses a plain dict or a copy of the map. It cannot tell another run's map from the run's own (UNVERIFIED, stated in the code). | Refuse, as the written order says. It is the stricter choice. | The text and masking team changes the code to refuse. It also adds the check that the map is the run's own. |
| 7 | Accept the text and masking team's changes to two of the connector and store team's files, or have that team redo them? | The files are the Slack approval-message file and the list of code that calls a model. The list now names the gate; that is a list entry, not an install. Two teams editing one file can collide. | Accept both. Either change can be undone with one commit. | The lead tells the connector and store team in its next order. |


### 1b. [v6] Decisions the lead still owes (the wording depends on them)

These are the lead's, not the owner's. The default is what the merged code does. Each row is marked LEAD DECISION until the lead answers in writing.

| id | question | default (built) | what the other answer does | status |
|---|---|---|---|---|
| L-D13 | A phone number directly before a full stop (`call 415-555-0132.`) | Not masked. The shapes `call 415-555-0132.`, `call 4155550132.` and `call +44 20 5550 1234.` (last group only) stay readable. | Mask it with the end `(?![0-9]|\.\w)` in the `+` entry only. Measured in the ticket: only two rows change. | LEAD DECISION |
| L-D15 | An IBAN beside `_` where `_` is also a base64url token character | Masked only after a short word at the start of a name, or before a short ending. Of 24 measured shapes, 16 leave the whole IBAN readable (the base left all 24). | Option (b) leaves 13 readable but splits more map entries inside random tokens. | LEAD DECISION |
| L-D17 | A contiguous card number of 13 to 19 digits glued to a letter | Not built. Rows 97 to 99 are strict expected failures; `card_4242424242424242` is masked as a phone number and kept in the map. | A card-number check before the phone entry: about one random digit run in ten would pass it. Not built, not measured. | LEAD DECISION |
| E16 | A UUID or a 10-digit number inside a long opaque token | Accept the readable remainder under 40 characters (the limit, as built). | A follow-up change keeps the token whole. A candidate was measured on scratch copies; nothing is built. | LEAD DECISION |
| G10 D4 | The injection check's time budget | 30 CPU seconds per check, per text, not per run. | 6 s, 48 s or none. | LEAD DECISION |
| E9 | The extra map entry for a tool's error text read twice | Accept it (option a, as built). | Exempt the escaped tokens of other kinds on the tool-error path only (option b). | LEAD DECISION |

Sources: tickets/G8-glued-rest-gap-v6.md lines 1022-1060 and 6.1 (L-D13, L-D15, L-D17); handover/core-c/ESCALATIONS.md (E16, E9); tickets/G10-textfold-deadline-v4.md section 10 (D4; the ticket says D1 to D10 are the drafter's defaults, unapproved); handover/core-c/REPORT-1200Z.md item 7 ("Lead decisions open").

---

## 2. For SECURITY.md: "What the tests show and what is still open"

[v6] As of head a60da3394 (2026-11-20 12:25 UTC).

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

- FIXED: changed, and a test fails without the change. The change is on the shared branch. A recorded batch that holds that test passed on the builder's copy of the code or on the merged tree. The whole test suite was not run on it. It is not on the main line.
- STRUCK: a statement of an earlier version that this version removes because it cannot be shown from the code on this branch.
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
- TESTED: the gate tests named in 2.1 to 2.4 passed in recorded merged-tree batches of 15 test files, after the gate's round-4 fixes. The last recorded result is 2,687 passed, 1 skipped, 5 xfailed.
- NOT RUN: the whole test suite, and a recorded batch of every test file on the merged code.
- UNVERIFIED (read in the test file): five install tests are marked as strict expected failures until the gate is installed. Once it is installed, they pass, and that pass fails the batch. Then the connector and store team removes the five marks.
- [INTERNAL] v6 CHANGED. Not installed: `grep -rn "ModelGate(" src` finds no construction outside guard/model_gate.py; tests/test_gate_install_callers.py holds 5 strict xfails (lines 233, 243, 280, 327, 353; v5 said 3).
- [INTERNAL] v6 CHANGED. Batches: evidence/INT-merged-batch-1.md to -5.md (line 4 of each; batch 5: "2687 passed, 1 skipped, 5 xfailed in 151.76s" on 9d8bc580a plus notes). Batch 3 had one failure, fixed in the same file (line 5). Code merged since batch 5 and covered by builders' own batches only: G8 (evidence/G8-build-notes.md:7-11, :38-39), G10 (evidence/G10-build-notes.md:8-14, :29), E9 fix round (evidence/E9-own-output.md:53-54), E15 pins (handover/core-c/ESCALATIONS.md E15 update). No batch covers the merged head as a whole (STATUS-BOARD.md line 15: "Not run: whole suite, perf on this tree, mutants, Python 3.12, PostgreSQL 17").
- [INTERNAL] v6 CHANGED. Gate: round 4 is commit b83accc65 ("code F: gate round 4 ..."). Reviews on file: tickets/F-result-review-1.md to -3.md; none for round 4. Secret finder: G7 rounds 3 to 7, E9 (1)(2)(3), Q9 (E13 resolved), Q16 are merged (REPORT-1200Z.md lines 3-5); G8 (6a852c7d3, 9c83340d1, 0b6f4e1ef), G10 (a6484cc7c, 0e3da02cf), E15 pins (d399ac5f3).
- [INTERNAL] v6 STRUCK: v5's lines on gate fix round 4 and secret finder fix round 3 "running", the 12,392-test pick batch, the c9478a9 / a2b6311 / 0fcc5e1 commit story and the producers-edit story are process history of head 6b990d9 and are no longer needed; their sources are the files v5 named.

### 2.1 Masking before a model call (the gate)

Shown by tests (TESTED here means: in a recorded merged-tree batch, run after the gate's round-4 fixes):

- TESTED: before a call, the gate masks each known value with its placeholder. This covers message text and documents only. K8 lists what it skips.
- TESTED: the gate searches for no new values. The secret finder does that (K1).
- TESTED: if masking fails, the gate makes no call and reserves no money. Causes: text too long, content that is not text, out of its size, step or time budget (its own refusal word), or text still changing after 4 maskings.
- TESTED: that refusal carries a refusal word and no text.
- TESTED: if no known value is present, the text goes out unchanged.
- TESTED: the gate does not change the calling code's messages, documents or run map.
- TESTED: the calling code must name its run map or state "no map". Leaving it out is an error, and so is a plain dict or a copy of the map. Only the test and replay command lines may state "no map" (K9).
- NOT RUN: the deliberate-code-break run of the gate's tests on the merged head.
- [INTERNAL] v6 STRUCK: "66 of 66" and "81 of 81" (v5): the list at head is larger (requests/3-bind-mapping-required.md names 105 mutants in tests/gate_mutants.py) and no run of it at this head is recorded. The laptop's mutant job (job 2) is the source.

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
  - TESTED: for a known value that is not plain ASCII, the gate also masks its folded spellings. A known full-width name and its plain Latin spelling are both masked.
  - [INTERNAL] v6 CHANGED. guard/model_gate.py:15-19 (the EXCEPTION paragraph); tests/test_model_gate.py:2639 (`test_r3_c_m2_stated_rule_the_sweep_also_replaces_the_folded_spelling_of_a_non_ascii_value`).
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
- **K10. Fixed:** the audit row said "map in use" when the map was empty. It also said so when the calling code had supplied its own masking function (allowed for tests). The row now says which.
  - Example: a run with an empty map now writes "map empty", not the same row as one with 50 values.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] v6 CHANGED (was FIXED ON BRANCH). Code: guard/model_gate.py:244-248 (MODE_*), :725-731. Tests T::test_r2_m5_the_audit_decision_says_what_was_really_enforced and T::test_d1_every_audit_row_says_whether_the_map_was_enforced are in tests/test_model_gate.py, which every merged-tree batch lists (evidence/INT-merged-batch-1.md to -5.md, line 3; last result line 4: 2687 passed, 1 skipped, 5 xfailed).
- **K11. Fixed:** a known secret inside a forged marker went out unmasked. Now the gate keeps only the marker's fixed words and masks the rest.
  - Example: a document holds a forged marker whose call number contains the known `S3cr3tPw`. Before this fix, `S3cr3tPw` went out.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] v6 CHANGED (was FIXED ON BRANCH). Code: guard/model_gate.py:744-800 (`_enforce_text`: id and name slots enforced, fixed words exact). Test T::test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client (tests/test_model_gate.py:2025). Batches: see K10.
- **K12. Reported, not reproduced:** a secret at a held-back value's edge may leak its tail.
  - Example: known `S3cr3t` and `>abcdef`. A reviewer read that `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`. A builder ran it and got `<SECRET_1><SECRET_2>`, with no leak.
  - Status: OPEN. Evidence: NOT REPRODUCED. Who acts: the text and masking team (a fresh reviewer checks the builder's run).
  - TESTED: the safety net that refuses a call when a known secret stays readable is in the code and in the batches (see K65).
  - [INTERNAL] v6 CHANGED (the NOT RUN net line is now TESTED). Net: guard/runmap.py:936-949. The builder's note is in the comment at guard/runmap.py:678-682 (`test_r2_m2_*` pins the case).
- **K13. Not fully limited:** the time the gate spends on one model call. One budget per call now covers the characters, the steps and the time, and the time is read inside the masking step. One scan of one stretch of text inside the secret finder cannot be interrupted.
  - Example: UNVERIFIED (a figure in the gate's own source notes, not re-measured here). A text of 262,144 characters of `a` with 500 planted values of `aaa...` takes about 7 seconds before the deadline is read. A call past its budget is refused with the code `mask_budget_exceeded`.
  - MEASURED earlier: 100 messages against a run map of 2,000 entries took 0.018 seconds.
  - Status: OPEN. Evidence: MEASURED (the 0.018 s case); UNVERIFIED (the 7 s). Who acts: the text and masking team.
  - [INTERNAL] v6 CHANGED (the reviewer's "128 million steps" estimate is struck: superseded by the built budget). Code: guard/runmap.py:625-640 (limits), :643-675 (`EnforceBudget`: a CPU deadline and a monotonic wall deadline, both read in `check()`), :689-777 (`enforce_map` passes the CPU deadline into `sweep`); guard/model_gate.py:59-66 (budget bullet, the 7 s figure at :63), :221-222 and :430-434 (`mask_budget_exceeded`). The wall deadline belongs to the gate's enforce step only; this file claims no wall-clock guard anywhere else. Tests: T::test_r3_m2_a_deadline_inside_the_sweep_is_a_budget_refusal_with_its_own_code (tests/test_model_gate.py:2493). 0.018 s: evidence/F-G0-1.md.
- **K14. Not protected:** a run's later tool-using calls. A planted secret of 4 or more characters makes each of them refuse. It does so when it equals a tool's name or a call number, or is a piece of a name in the tool list.
  - Example: a tool result contains `password=search_web`, where `search_web` is a tool's name. Later calls in that run refuse.
  - Status: OPEN. Evidence: TESTED (the rule as built). Who acts: the owner decides which rule. If no answer arrives by 2026-11-23 12:00 UTC, the rule as built stays.
  - [INTERNAL] v6 CHANGED (the rule is now built and in batches; it also refuses a piece of a listed name). Code: guard/model_gate.py:368-396 (`framing_free`), docstring :80-86 ("A planted value that equals a tool name refuses every later call of the run"). Tests T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker (tests/test_model_gate.py:1897), T::test_r3_c_m1_a_secret_that_is_part_of_a_listed_tool_name_refuses_the_call (:2624). Decision 1 in part 1a.
- **K15. Fixed:** planted text could rewrite part of a tool's name in the line where the model asked for that tool.
  - Example: a document planted `password=logs`; the model then saw two names for one tool call.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody. See K66 for the tool list.
  - [INTERNAL] v6 CHANGED (was FIXED ON BRANCH). Code: guard/model_gate.py:744-800 (a name in the call's `tools` list stays exact in the line and the marker; `listed` from :398). Test T::test_r3_c_m1_a_tool_name_in_the_tools_list_stays_exact_when_a_known_value_lies_inside_it (tests/test_model_gate.py:2598).
- **K16. Fixed:** stopping the program by hand while the gate masked, worked out the worst case, asked for a reservation, or in the instant after it, left no audit row. Now a row is written.
  - Example: the program is stopped by hand while the gate waits for its reservation. The record now holds a row that says "reservation interrupted".
  - The reservation stays booked, on purpose: the worst case stays booked, not the real cost.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] v6 CHANGED (was FIXED ON BRANCH; the "two more places" of F-r3 design N4 are the enforce step and the instant after reserve: both now write a row). Code: guard/model_gate.py:570-575, :610, :616. Tests T::test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on (tests/test_model_gate.py:2340), T::test_r3_n4_a_keyboard_interrupt_in_the_enforce_step_writes_a_row_and_passes_on (:2705), T::test_r3_n4_an_interrupt_between_reserve_and_the_call_writes_a_row_and_passes_on (:2726). A stop by hand inside settle or the audit write: not claimed.
- **K17. Not safe:** two threads writing one run map at the same time can give one placeholder number to two values.
  - Example: two tools finish together and both values become `<SECRET_3>`.
  - Status: OPEN. Evidence: UNVERIFIED (stated in the code comments, not run).
  - Who acts: the text and masking team adds "one writer per run map" to its install request to the connector and store team.
  - [INTERNAL] v6 CHANGED (source lines). guard/runmap.py:603-606 ("two threads that write ONE map at the same time ... One run's map has one writer at a time today"); guard/model_gate.py:119-121 ("One writer per run map ... Not pinned by a test (a race)"). requests/3-bind-mapping-required.md does not name it (grep).
- **K64. Not protected:** a run's later calls, when planted text holds more than 4,096 values at a placeholder's edge (such as `password=>aaaa1`), or more than 20,480 values in all. The gate then refuses every later call of that run, because the run map only grows.
  - Example: one planted document with 4,097 such lines stops the run.
  - Status: OPEN. Evidence: TESTED (the old cap of 256 is gone; a run is no longer stopped by 257 values). UNVERIFIED: that the run map only grows. Who acts: the text and masking team.
  - [INTERNAL] v6 CHANGED (the cap was 256, it is now 4,096 held-back values and 20,480 entries; v5's 256 is struck). Code: guard/runmap.py:629-640 (comment at :629-634 says the cap is "set by memory and the deadline" and that the producer side should stop registering). Test T::test_r3_m1b_planted_held_values_past_the_old_cap_of_256_do_not_brick_the_run (tests/test_model_gate.py:2432). "The map only grows": guard/runmap.py:599 comment ("`current` is always the old map plus new entries").
- **K65. Not refused:** a known secret that spans a fixed framing word. The safety net checks each stretch of text between fixed framing words on its own.
  - Example: a known secret written as `tool read_logs` inside `password="tool read_logs"` is cut by the fixed word `tool ` and goes out as written.
  - TESTED: the safety net now covers every known secret of 4 or more characters, not only held-back ones. A secret hidden in a made-up placeholder-shaped token that is not a key of the map refuses the call.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] v6 CHANGED (v5 K65 said the net checks held-back values only: struck). Code: guard/runmap.py:936-949 (`held_value_left`, docstring states the spanning limit); guard/model_gate.py:51-58 (net bullet). Tests T::test_r3_m3_the_net_covers_every_secret_value_not_only_the_held_back_ones (tests/test_model_gate.py:2568), T::test_r3_m3_a_secret_hidden_in_a_placeholder_shaped_token_that_is_not_a_key_refuses_the_call (:2535), T::test_r3_n2_stated_limit_a_value_spanning_a_fixed_framing_word_is_not_replaced (:2585).
- **K66. Fixed:** a known value inside a tool's name. The gate masked it in the line where the model asked for the tool, but the tool list went out as written, so the model saw two names.
  - Now a name that is in the tool list stays exact in the line and in the marker. A secret that equals a listed name, or is a piece of one, refuses the call (see K14).
  - Example: the run map holds `<TENANT_1>` for `billing`. The tool `get_billing_info` is no longer rewritten to `get_<TENANT_1>_info`.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] v6 CHANGED (was OPEN). Code: guard/model_gate.py:368-396, :398-404, :744-800; docstring :80-86. Tests tests/test_model_gate.py:2598 and :2624 (see K14, K15).
- **K67. Fixed (the list); the install is still waiting:** the install hand-over list and the install test now name the judge's call points. They are the agent loop, the approval cards, the approval summaries and the replay loop. A test fails if a new call point appears that the list does not know.
  - Example: the approval summary reaches the judge from a place the old list did not name.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody for the list; the connector and store team installs the gate (K18).
  - [INTERNAL] v6 CHANGED (was OPEN). tests/test_gate_install_callers.py:56-63 (`JUDGE_SITES`), :296 (`test_the_judge_call_sites_in_src_are_all_in_the_table`), :353 (`test_install_behavioural_the_judge_is_built_on_a_bound_gate`, strict xfail until the install). The install test file now holds 5 strict xfails (lines 233, 243, 280, 327, 353); v5 said 3.
- **K69. Not checked:** that the run map given to the gate is the run's own, current map. The gate now refuses a plain dict and a `dict(run_map)` copy. It cannot tell the run's own map from another run's map, or from a `RunMap` built from a copy. An empty run map is accepted, and the audit row says "map empty".
  - Example: the calling code passes yesterday's run map object. Values found today are not masked, and the row says the map was used.
  - Status: OPEN. Evidence: TESTED (the dict refusal and the empty-map row); UNVERIFIED (the stale-map case, stated in the code).
  - Who acts: the owner decides it together with one question: whether the gate refuses a call when the run map is empty.
  - If no answer arrives by 2026-11-23 12:00 UTC, the default applies: the gate refuses an empty map. Then the text and masking team changes the code.
  - [INTERNAL] v6 CHANGED (the type check is built; a masking function supplied by the caller is still accepted but marked `enforce_custom`, and the install test refuses `enforce=` anywhere in src). Code: guard/model_gate.py:528-529 (RunMap check), :245 and :731 (`map_enforced_empty`), docstring :100-102, :490. Tests T::test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping (tests/test_model_gate.py:1635), T::test_r3_m4_an_enforce_function_other_than_the_default_is_marked_and_documented_as_test_only (:2739); tests/test_gate_install_callers.py:186. Decision 6 in part 1a.
- **K18. Not handled:** a gate refusal or a refused reservation leaves the run's status "working" instead of "stopped".
  - Example (UNVERIFIED, read from the code): after a refused reservation the run still shows "working". The planted-instruction check reports the same refusal as a guard failure.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written install request).
  - [INTERNAL] v6 CHANGED (line cite). The catch site is src/hadavin_sdk/runtime/agent_loop.py:476-478 (`except ProviderError`, v5 said :477). requests/3-bind-mapping-required.md section 3 and section 7.
- **K19. Not through the gate:** the guardrail call. It is neither masked by the gate nor counted against the cap.
  - Example: a run's guardrail calls cost money that the cap never sees.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: UNVERIFIED (read in the install test's table of calls kept outside the gate). Who acts: nobody.
  - [INTERNAL] v6 CHANGED (line cite). tests/test_gate_install_callers.py:43-47 (`BYPASS`, the bedrock_guardrail row at :44). The plan text: inputs/plan-v4-final.md line 29.

### 2.2 Spending cap

Shown by tests:

- TESTED (the gate's batch): the gate makes no model call without a reservation. Order: mask, reserve, call, settle, write the audit row.
- STRUCK: v5's tests of the spend cap under 50 separate database connections. The store code they test is the connector and store team's and is not on this branch, so the tests skip here (NOT PROVABLE).
- [INTERNAL] v6 STRUCK. tests/contracts/test_t1_reserve_cap.py:16 (skips when `Store.reserve_spend` is missing), :41 and :50 (`NOT_LANDED`, `skipif`); `grep -rn reserve_spend src` is empty; src/hadavin_sdk/store/migrations ends at 0005_evidence.sql. v5's "49 passed twice on PostgreSQL 16.15" is core-b's tree (evidence/T1-reserve-cap.md), not this head.
- TESTED (the gate's batch): when a reply arrives with a usable cost, the gate settles that real cost.

Known gaps:

- **K20. Not released:** the worst case of a failed call. The model connectors cannot yet say "refused before any answer", so the gate does not settle a failed call.
  - Example: the gate side is TESTED: a failed call is not settled. What the store keeps booked after that is the store's behaviour. The store's reservation code is the connector and store team's and is not on this branch (NOT PROVABLE here).
  - Status: WAITING. Evidence: TESTED (a failed call is not settled). Who acts: the connector and store team (written request).
  - [INTERNAL] v6 CHANGED. The 3.00 / 1.00 USD "three failed calls" example is struck (it needs the store). Gate side: tests/test_model_gate.py:1205 (`test_pin_an_unmarked_provider_error_is_not_settled`), :1197 (`test_pin_no_settle_on_keyboard_interrupt`). Store absent: `grep -rn reserve_spend src` is empty; src/hadavin_sdk/store/migrations ends at 0005_evidence.sql; tests/contracts/test_t1_reserve_cap.py:41 and :50 skip when `Store.reserve_spend` is missing. requests/2-refused-before-response.md exists.
- **K21. Booked as free:** a reply with an empty cost field. The connectors' reply form fills an empty cost with 0.00 USD, and the gate settles 0.00 USD.
  - Example: a connector forgets to fill in the cost; a 0.80 USD call is booked as 0.00 USD.
  - Status: WAITING. Evidence: TESTED (the gate's side). UNVERIFIED: that a connector leaves the field empty. Who acts: the connector and store team (written request).
- **K22. Not settled:** a reply with an unreadable cost. The worst case stays booked, not the real cost.
  - Example: a reply reports its cost as "not a number"; the full 1.00 USD stays booked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
- **K23. Not counted:** earlier attempts of a call that succeeded after retries. Only the last attempt is settled.
  - Example: attempt 1 times out but was billed 0.40 USD; attempt 2 costs 0.30 USD; only 0.30 USD is booked.
  - Status: WAITING. Evidence: UNVERIFIED (read from the code). Who acts: the connector and store team (written order).
- **K24. The gate passes a higher real cost to settle:** a call that costs more than its worst case is passed to settle at the real cost, on purpose. How the store books it is the store's code (not on this branch).
  - Example: the gate side is TESTED. The store side (booked money passing the cap once) is NOT PROVABLE here.
  - Status: PINNED (the gate's side). Evidence: TESTED. Who acts: nobody (by design). How often this happens depends on the worst-case formula, which does not exist yet (K25).
  - [INTERNAL] v6 CHANGED. Gate: tests/test_model_gate.py:283 (`test_a_settle_above_the_reservation_is_passed_through`). Struck: the 1.00 + 1.00 + 2.50 = 4.50 USD example and the PostgreSQL 16.15 test cited for it (tests/contracts/test_t1_reserve_cap.py skips on this branch, see K20).
- **K25. Not written:** the worst-case formula for the gate. The gate takes the function from the installer. It must cover the system prompt, the messages, the tool schemas and the documents, and the attempts. No function in this tree does that.
  - Example: the one worst-case function in the tree prices only the system prompt and the messages, and only the replay command line uses it. Until the connector and store team writes the gate's function, no installed gate has a real worst case to reserve.
  - Status: WAITING. Evidence: UNVERIFIED (read from the code; nothing to test). Who acts: the connector and store team (written order).
  - [INTERNAL] v6 CHANGED (v5 said "no function fits" with no cite). guard/model_gate.py:187-190 (what the function must cover; it names `llm.common.worst_case_usd`, which is not in this tree: `grep -n worst llm/common.py` is empty); k1b/loop.py:115 (`worst_case_usd(route, system, messages)`, no documents or tools) and :170 (its only caller, the replay loop). ORDER 016c item 13 (handover/core-c/ORDERS.md).
- **K26. Not enforced by the database:** the runtime login can rewrite the spend counters. On this branch it holds SELECT, INSERT and UPDATE on the tables `spend` and `spend_month`.
  - Example: faulty code could lower the booked amount.
  - Status: OPEN. Evidence: UNVERIFIED (read from the grant map; no database test was run here).
  - Who acts: the owner decides whether to tighten these rights. If no answer arrives by 2026-11-23 12:00 UTC, they are tightened. Then the connector and store team changes them.
  - [INTERNAL] v6 CHANGED. src/hadavin_sdk/store/migrate.py:40 (`_RW = "SELECT, INSERT, UPDATE"`), :53-54 (`spend`, `spend_month`). Struck: "the purge login can delete an open reservation" (v5): it rests on the connector and store team's `spend_reservations` table (evidence/B-grants-rework.md:60-61, ref cloud-core-b 576f292), which is not in this tree. Decision 5 in part 1a.
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

- **K29. Not narrowed by the database:** the runtime login can change the stop switch and sign a stop record with any name. On this branch it holds SELECT, INSERT and UPDATE on the table `kill_switch`, and the migrations add no trigger on it.
  - Example: a stop record says "by: operator" when the runtime wrote it. The runtime can also set the flag back to off.
  - Status: OPEN. Evidence: UNVERIFIED (read from the grant map and the migrations; no database test was run here).
  - Who acts: the owner decides whether to tighten these rights. If no answer arrives by 2026-11-23 12:00 UTC, they are tightened. Then the connector and store team changes them.
  - [INTERNAL] v6 CHANGED (v5 spoke of a reset login; there is none in this tree: `grep -n reset src/hadavin_sdk/store/migrate.py` is empty). src/hadavin_sdk/store/migrate.py:55 (`kill_switch`), store/migrations/0001_core.sql:94 (the table); triggers in the migrations cover only the audit tables (0002_audit_chain.sql:25-34). Decision 5 in part 1a.
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
  - [INTERNAL] v6 CHANGED (source). guard/model_gate.py:244-248 (the five `MODE_*` words cover map use only; there is no masked flag and no route field). The decision field is `AuditEvent.decision` (models.py).
- **K32. Struck in v6:** v5 said the reset login can add any audit row. The reset login belongs to the connector and store team's code and is not on this branch (NOT PROVABLE here). On this branch the audit tables are append-only for every login.
  - Status: STRUCK. Evidence: UNVERIFIED (read from the migrations). Who acts: nobody until that code is merged; the claim is restored then.
  - [INTERNAL] v6 CHANGED. src/hadavin_sdk/store/migrate.py:42-45 (comment: audit rows are read and appended only; triggers refuse UPDATE, DELETE and TRUNCATE), :57 (`audit_entries`, `_APPEND`), store/migrations/0002_audit_chain.sql:25-34. The v5 source (evidence/B-grants-rework.md finding 5, migrate.py:65 of ref cloud-core-b 576f292) is not in this tree. Decision 5 in part 1a lists five rights; two remain (K26, K29).
- **K33. Not in the record:** the test and replay command lines print their audit lines to the screen only.
  - Example: a replay leaves no row in the store.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.

### 2.5 The secret finder (what enters the run map)

Shown by tests (TESTED here means: in recorded merged-tree batches of the shared branch's code):

- TESTED: it finds the kinds it knows: addresses, keys, tokens, e-mail, passwords in web addresses and command lines, and supplier payment details (a bank account beside its bank code).
- TESTED: one call masks a bank account beside its bank code. It also masks the rest of a longer token that holds a shorter known secret (K40).
- TESTED: one call runs up to 5 search rounds. Past the 5th round, it refuses the whole text (fail closed).
- TESTED: a line it cannot mask in place is withheld.
- [INTERNAL] v6 CHANGED. Batches 1 to 5 (evidence/INT-merged-batch-1.md to -5.md) hold tests/test_redact_settle_loop.py, tests/test_redact_context_after_sweep.py and tests/test_redact_idempotent_property.py. v5's "which saved version" caveat and the 9,681-test batch of unrecorded code version are struck. The line "one text can go through up to 7 calls of the secret finder" (a reviewer's reading) is struck: it is not shown by the code at this head.

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
- **K38. Fixed:** a letter or `_x` glued behind an IPv4 address, a UUID, a phone number written with `+` or an IBAN beside `_` kept it unmasked. Now each is masked, and the glued text stays outside the placeholder.
  - Example: `10.20.30.40_x` now becomes `<IPV4_1>_x`; `DE89..._x` becomes `<IBAN_1>_x`. Shapes that are still not masked are in K70 and K71.
  - Status: FIXED. Evidence: TESTED; MEASURED (a probe on the merged head, `10.20.30.40_x`, `10.20.30.40x`, `x10.20.30.40`, `+14155550132_x`, a UUID with `x` behind it).
  - Who acts: nobody.
  - [INTERNAL] v6 CHANGED (was OPEN, "MEASURED on the joined branch"). Code: guard/redact.py:77-89 (`_IBAN_START`, `_IBAN_END`), module docstring :20-31. Builder's batch: evidence/G8-build-notes.md:38 (G8 file 451 passed, 43 xfailed; 35 of 35 mutants) and :9 (15 files, 6833 passed, 3 skipped, 4 xfailed). Probe: scratch script, python 3.13.3, head a60da3394; output in evidence-cword.md.
- **K39. Not proven:** that the repeated search finds every value. Each call repeats the patterns and the masking until a round changes no text, at most 5 rounds. A call still changing after round 5 is refused.
  - Example: planted text glues a bank code to a secret, then puts the account after that code elsewhere. This needed a third round and is masked.
  - Status: OPEN. Evidence: TESTED (the chain; the loop to a fixed point). Who acts: the text and masking team. Two limits that stay are in K72.
  - [INTERNAL] v6 CHANGED (the two UNVERIFIED reading lines are struck: the loop now re-reads the union of the strings the patterns and the sweep changed, guard/redact.py:1238-1262). Code: guard/redact.py:1283-1318 (loop; `NotSettled` at :1318), :2145 (`_SETTLE_ROUNDS = 4`: the first pass plus 4 rounds). Tests tests/test_redact_settle_loop.py and tests/test_redact_idempotent_property.py are in batches 1-5.
- **K40. Fixed:** the last part, up to 7 characters, of a longer token stayed readable in its other copies. This happened when the token was found only after a shorter known secret inside it.
  - Example: `password=ab9x`, then `Bearer ab9xqrstu`. The line `note ab9xqrstuvw end` used to show `note <SECRET_1>qrstuvw end`. It now shows `note <BEARER_1>vw end`.
  - Status: FIXED. Evidence: TESTED (the tail tests are in tests/test_redact_settle_loop.py, which every merged-tree batch lists).
  - Who acts: nobody. See K68.
  - [INTERNAL] v6 CHANGED (the "which saved version" caveat is closed by batches 1-5). The fail-before count "20 of 28" is WITHDRAWN by evidence/G7-1.md:290; v5 repeated it: struck.
- **K41. Not fully limited:** how long one call of the secret finder takes. Its time budget (6 seconds of processor time per call) is read before each search round and inside each masking step, the finder build and the written-forms scan. It is not read inside one pattern pass over one text, nor in the loop over the texts of one round.
  - Example (MEASURED, processor time, on the test machine): the text `curl -u ` repeated up to the size cap took 4.5 to 5.4 seconds against the 6.0-second budget. A machine about 25 percent slower refuses that text, and a real document of that shape is lost (fail closed).
  - Status: OPEN. Evidence: MEASURED. Who acts: the text and masking team.
  - [INTERNAL] v6 CHANGED (v5 said the budget was read only before each round, and gave 4.00 s: both struck; 4.00 s belongs to round 2 code, evidence/G7-1.md:318). Code: guard/redact.py:1238-1319 (`settle` and its docstring: "NOT checked: a pattern pass (`find`) over a string, and the loop over the strings of one round"), :1358-1364 (`_over_budget`), defaults.py:88 (`REDACT_BUDGET_S = 6.0`), defaults.py:35-45 (the figures). The 0.167 s to 0.395 s bank-lines figure is round 3 code (evidence/G7-1.md:314, :353); not repeated.
- **K42. Not masked later:** a secret first seen in a tool's error message. It never enters the run map.
  - Example: a tool fails with "bad password hunter2zz"; later results show `hunter2zz`.
  - Status: WAITING. Evidence: UNVERIFIED (a reviewer's reading). Who acts: the connector and store team (written request).
- **K43. Not masked:** a secret spelled exactly like the redactor's own escaped placeholder (`‹SECRET_1›`, with angle quotes), a run of such spellings, or the cut-off start of one (`<S`, `<SEC`, `<SECRET_`).
  - Example: `password=‹SECRET_1›` stays as written, on purpose. A tool's error text is read twice, and the first read wrote that placeholder. A real password `<S` or `<SEC` stays readable and gets no map entry.
  - Status: PINNED. Evidence: TESTED; MEASURED (a probe on the merged head: `password=‹SECRET_1›` unchanged, `password=<S` and `password=<SEC` unchanged). Who acts: nobody.
  - [INTERNAL] v6 CHANGED (E9: only SECRET-kind tokens are exempt; v5 K43 omitted the cut-off openings and the `;` `,` separators). Code: guard/redact.py:928-952 (`_OWN_TOKEN`, `_OWN_OUTPUT` and its comment), :1739-1740. Tests tests/test_redact_own_output.py::test_only_the_exact_escaped_shape_is_left_alone, tests/test_redact_own_output_hardening.py (a_stated_limit cases: tests/test_redact_context_after_sweep.py:498).
- **K44. Fixed:** a secret wrapped in look-alike angle quotes was left readable.
  - Example: `password=‹hunter2zz_1›` is now masked.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K45. Fixed for the one place found:** the secret finder, run again on its own output, turned real placeholders into new secrets. The place was the tool-error path.
  - Example: a tool error quoting `<SECRET_1>` no longer adds a new map entry.
  - Status: FIXED. Evidence: TESTED (that place). UNVERIFIED: that no other place does this. Who acts: nobody.
- **K46. Not masked whole:** a secret holding a space, `;`, `,` or `&`. It is masked only up to that character.
  - Example: `password="my secret phrase"` shows `secret phrase`.
  - Status: STATED (the published SECURITY.md on the main line, since 2026-11-04). Evidence: NONE. Who acts: nobody.
- **K68. Fixed:** after the secret finder undid a half-made entry, an old record could survive, so a later placeholder with the same number could be restored to the wrong value.
  - The text stayed masked; nothing raw went to the model. A tool could have got the wrong account or credential.
  - Example: a token found and then undone left a record for `<BEARER_1>`. A new `<BEARER_1>` for another value was later restored as the old one.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] v6 CHANGED (was OPEN, UNVERIFIED). Code: guard/redact.py:1665-1676 (`_rollback` removes the mapping entry, the reverse entry and the written form), :1816 (`_unspell`). Tests tests/test_redact_settle_loop.py:250 (`test_a_rolled_back_compound_entry_leaves_no_ghost_spelling`) and :261 (`test_a_number_reissued_after_a_rollback_does_not_revive_the_ghost_spelling`).
- **K70. Not masked, by design:** glued shapes the glued-text change leaves readable. A phone number or card number written as one run of digits with a letter right before or after it (`x4155550132`, `telephone4155550132`, `x4242424242424242`). A phone number without `+` with a letter after it (`415-555-0132x123`). A phone number directly followed by a full stop (written with spaces, only its last group stays: `+44 20 5550 1234.` becomes `<PHONE_1> 1234.`). An IBAN with a letter or digit glued before it, or written inside a file name, a path or an identifier (`acct_iban_DE89...`, `beneficiary_DE89...`). A US Social Security number with a letter glued to it. A host name with a letter, digit or `_` after its private suffix.
  - Example: `x4155550132` and `acct_iban_DE89370400440532013000` go out as written (MEASURED on the merged head). A card number written as one run beside `_` (`card_4242424242424242`) is masked as a phone number and kept in the run's map as one.
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The defaults are as built. A phone directly before a full stop is not masked. An IBAN beside `_` is masked only after a short word at the start of a name or before a short ending; this leaves the file, path and key shapes above readable and avoids a new split of long tokens. There is no card-number check, so the contiguous card shapes above stay readable.
  - [INTERNAL] v6 LEAD DECISION L-D13 (default: not masked), LEAD DECISION L-D15 (default: the short-word rule), LEAD DECISION L-D17 (default: no card check). Options in part 1b.
  - [INTERNAL] v6 NEW (E16 and the G8 limits). Tests tests/test_redact_glued_rest.py:104 (`test_limit_rows_are_pinned`), :137 (`test_phone_before_a_full_stop_is_a_stated_limit`), rows tests/g8_cases.py:54 (ROWS), :489 (FULL_STOP F1-F6). Defaults and options: tickets/G8-glued-rest-gap-v6.md section 6 (L-D13, L-D15 and L-D17 rows, lines 1022-1060) and 6.1; builder's note evidence/G8-build-notes.md:19-23 ("L-D15 stays at default"). Wording source: ticket section 13 (line 1594). MEASURED here (scratch probe, head a60da3394): `x4155550132`, `telephone4155550132`, `x4242424242424242`, `acct_iban_DE89...`, `xDE89...` unchanged; `card_4242424242424242` -> `card_<PHONE_1>`; `call +44 20 5550 1234.` -> `call <PHONE_1> 1234.`; `call 415-555-0132.` unchanged.
- **K71. Readable remainder of a long token:** a UUID or a number of 10 or 11 digits, set off by `_`, is now cut out of a long token. The rest of the token stays readable when it is under 40 characters. Before the change, the whole token was masked as one value.
  - Example (MEASURED on the merged head): `tok_<uuid>_` followed by 32 characters becomes `tok_<UUID_1>_` and the same 32 characters, readable. With a remainder of 40 characters or more the remainder is masked too.
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. This is the limit as built. A follow-up change that keeps the token whole was measured on scratch copies; nothing of it is built.
  - [INTERNAL] v6 LEAD DECISION E16 (default: accept the limit as merged; alternative: ticket G11, candidate 2 of handover/core-c/tickets/G11-files/).
  - [INTERNAL] v6 NEW. tests/g8_cases.py:247-309 (`OPAQUE_LIMITS` OL1-OL7: 7 rows, 6 strict xfails for the desired output), tests/test_redact_glued_rest.py:263 (`test_a_value_inside_an_opaque_token_is_a_stated_limit`); code comment guard/redact.py:30-31 (limit L15); evidence/G8-build-notes.md:30-34 ("pinned as limit L15, 6 strict xfail ... + 7 pinned as-measured"); handover/core-c/ESCALATIONS.md E16 ("DECISION FOR THE LEAD" and "E16 update"). Probe: `tok_123e4567-e89b-12d3-a456-426614174000_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef` -> `tok_<UUID_1>_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef` (32-character tail readable), head a60da3394.
- **K72. Not masked whole:** overlapping values. Two overlaps leave a readable part of a value the map holds. (1) A written form that is completed only in a later round cannot recover text an earlier round already masked, so its literal start or end stays readable. (2) Two compound values that overlap as raw text: the tail of one stays readable.
  - Example: plain values `abcdefgh` and `efghijkl` in `abcdefghijkl` become `<S1>ijkl`. A log author who controls the order of lines can cause both cases and needs no secret knowledge.
  - Status: PINNED. Evidence: TESTED. Who acts: the text and masking team (a planned change, not merged).
  - [INTERNAL] v6 NEW (E10). Pins tests/test_redact_settle_loop.py:607 (`test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit`) and :1376 (`test_two_overlapping_values_in_raw_text_leave_the_tail_readable_a_stated_limit`); defaults.py:112-114 ("Two OPEN limits (E10, pinned by tests)"); handover/core-c/ESCALATIONS.md E10 (round 6 paragraph). The fixed-point change (G9) is built on a worktree branch and is not merged (git log shows no G9 code commit; REPORT-1200Z.md "Building now"): nothing here describes it.
- **K73. Refused, not read:** a hostile text can make the secret finder refuse a whole document. The refusals fail closed: nothing is shown, and a real document in the same text is lost.
  - The refusal words are: `SpelledWorkTooMuch`, past 4,000,000 units of work in the written-forms scan; `SpelledMemoryTooMuch`, past 1,000,000 characters of written forms in one call; `InputTooLarge`, the time or size limit; `NotSettled`, a text still changing after round 5.
  - Example (MEASURED): a text of 2,800 written forms in 213,000 characters, then 262,000 characters of copies, needs 6.3 million units and is refused after 0.49 seconds of processor time.
  - Status: STATED (written in the code's own notes). Evidence: MEASURED. Who acts: nobody.
  - [INTERNAL] v6 NEW (G7 rounds 5 to 7). Code: guard/redact.py:1793 (`SpelledMemoryTooMuch`), :1996 (`SpelledWorkTooMuch`), :1364 (`InputTooLarge`), :1318 (`NotSettled`); defaults.py:98-125 (limits and the 0.49 s figure at :108-109; "A hostile author can therefore FORCE A REFUSAL of the whole document" at :111-112); evidence/G7-1.md "G7 fix round 6" and "round 7" (raw figures; not re-run here).
- **K74. Not limited:** the memory the secret finder holds for a very large plain value. A hostile document can force about 1 GB of finder memory in one call.
  - Example (MEASURED earlier): eight distinct plain values of 260,000 characters each, through one bundle call, peaked at 956 MB (tracemalloc).
  - Status: OPEN. Evidence: MEASURED. Who acts: the text and masking team (a ticket and a plan review come first). The caller's own memory guard is the connector and store team's.
  - [INTERNAL] v6 NEW (E14). handover/core-c/ESCALATIONS.md E14 ("Default until decided: unchanged (stated limit ...)"); defaults.py:119-120 ("956 MB with no registry at all: a separate cost, not this limit's"). No code limit exists (grep for a cap on the length of a stored value finds none at this head).
- **K75. Extra map entry, accepted:** a tool's error text read twice can make one extra map entry for each distinct token of another kind written after a key. The model sees a secret placeholder instead of the kind. Nothing real is stored in that entry.
  - Example: `token=<JWT_1>` becomes `token=<SECRET_1>`, and `<SECRET_1>` stands for `‹JWT_1›`. Also `password=‹EMAIL_1› host` becomes `password=<SECRET_1> host` (MEASURED on the merged head).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The alternative (exempt the escaped tokens of other kinds on the tool-error path only) is not built.
  - [INTERNAL] v6 LEAD DECISION E9 (default: option (a), as built; alternative: option (b)).
  - [INTERNAL] v6 NEW (E9). guard/redact.py:936-948 (the trade-off comment), tests/test_redact_own_output_hardening.py:202 and :229 (the pins, "makes_one_junk_entry"), evidence/E9-own-output.md:6 and :47-54 (the fix round and its measurements: 145 passed in the three files; 422 passed in the wider batch). CHANGELOG.md line 6 (the upgrade-step item).
- **K76. Fail-safe, accepted:** a placeholder written in a spelled form (`&lt;TENANT_1&gt;`, `%3CTENANT_1%3E`, `&#60;IPV4_1&#62;`) can come back from the secret finder as the decoded placeholder shape, when its digits are not masked. No value stands behind it: the run map has no such key, so a later restore gives nothing.
  - Example: `&lt;TENANT_4155550132&gt;` becomes `&lt;TENANT_<PHONE_1>&gt;`, as typed with the digits masked (MEASURED on the merged head).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] v6 NEW (E15, resolved as accepted fail-safe). tests/test_runmap_e15_placeholder_spellings.py (15 cases); handover/core-c/ESCALATIONS.md E15 update ("RESOLVED as accepted fail-safe"; the probe agent found no scenario where a real secret reaches model-controlled text). The probe of `&lt;TENANT_4155550132&gt;` was repeated here (scratch, `redact`, head a60da3394).

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
- **K50. Over-matching, measured:** the text-folding scan finds a known name inside a longer word or across a space. No masking path uses this scan yet.
  - Example: known `mary` found in `summary`.
  - MEASURED 2026-11-20 per scan of one 10,000-character chunk of ordinary Latin text (repository prose and code, library docstrings, generated text). The value was drawn at random. Rates: 4 letters 5.3 %; 5 letters 1.0 %; 6 letters 0.4 %; 8 or more 0; common words of 5 to 10 letters 3.9 to 4.5 %; ASCII ids of 4 to 5 characters 0.22 %; 6 digits 0.007 %.
  - The rate is a hit rate on this corpus with random values. It is an upper bound only in that a value that is a whole word counts as a hit. It is NOT a bound for tickets, e-mail, chat or real values.
  - The share of hits that cut a word: 94 % for 4 letters, 63.4 % for 5 letters, 99 % for short ids, 9 % for 6-letter names. Real Russian interface text 7.6 % and real Chinese interface text 5.2 % for short values; Arabic and Devanagari: synthetic text only, unknown.
  - Status: STATED. Evidence: MEASURED. Who acts: nobody (the first user of this scan measures again).
  - [INTERNAL] v6 CHANGED (was OPEN, UNVERIFIED, "NOT RUN"; wording from tickets/G10-textfold-deadline-v4.md section 8.4). Rates: evidence/G1-false-hits-and-cost.md:106-130 ("Round 2"; 5 letters 1.0 % is 0.986 % at :126; 63.4 % at :126), defaults.py:257-264. "No masking path uses this scan": grep over src finds `scan_holds` only in guard/textnorm.py and the comments of defaults.py; injection.py calls `scan_views_no_value` only. The street/host row is hash-seeded (two runs, 3.91 % and 4.46 %).
- **K51. Limited by a CPU budget:** the planted-instruction check stops at 30 seconds of processor time per check and then flags the run as "guard unavailable". The time is that of the thread that runs the check. It fails closed. Only processor time counts. No call site of this check has a wall-clock limit.
  - Example: a constructed text of 2,000,000 characters took 185 seconds of processor time without the budget and was flagged at 30.1 seconds with it (MEASURED on the build machine; maxima of named texts, not a bound for every text).
  - A machine about 1.9 times slower than the build machine flags the slowest ordinary 2,000,000-character text measured (16.0 s) on every run.
  - The work on a protected value inside one scan has no reading inside it (7.2 to 7.5 s measured for a value of 236,879 distinct letters).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The 30-second limit and its scope (per check) are the defaults as built.
  - [INTERNAL] v6 LEAD DECISION (G10 decision D4: 30.0 CPU seconds per check; default built; the ticket says D1 to D10 are unapproved defaults, tickets/G10-textfold-deadline-v4.md section 10).
  - [INTERNAL] v6 CHANGED (was OPEN, "no time limit"). Code: defaults.py:296-302 (`INJECTION_BUDGET_S = 30.0`), guard/injection.py:66-77, :94, :149, :166, :257 (`guard_unavailable`), guard/textnorm.py:250-262, :397-400 (`DeadlinePassed`), :601-615, :1464, :1571. Tests tests/test_textnorm_deadline.py:266 (`test_the_injection_check_flags_a_run_past_its_budget`) and :299. Builder's results: evidence/G10-build-notes.md:12-14 and :29. The 185 s and 30.1 s figures: tickets/G10-textfold-deadline-v4.md section 12 and CHANGELOG.md (Changed, G10). "Wall clock": none claimed; the only time read is `time.thread_time()` (textnorm.py:608, :614; injection.py:77, :83).
- **K52. Refused, not read:** a long text in Chinese or Japanese only. It is reported as a guard failure.
  - Example (MEASURED): 300,000 characters of Chinese, and of Japanese, were refused. Russian prose of that size is read.
  - NOT RUN: a measure of the shortest length that is refused.
  - Status: STATED (written down by the text and masking team, 2026-11-20). Evidence: MEASURED. Who acts: nobody.
- **K53. Chosen in a written order:** dashes and curly quotes are ordinary punctuation. Three slash look-alikes make the line withheld.
  - Example: a value right after an em dash (—) is masked in place.
  - A line holding DIVISION SLASH (∕), BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT (╱) or BIG SOLIDUS (⧸) plus a look-alike value is withheld.
  - This choice changed the class of 30 code points. They are 20 dashes and the minus sign, 6 quotes, 3 slash look-alikes and the replacement character U+FFFD, which the fold now drops. Each of the 30 has a test and a deliberate code break that the tests catch.
  - Status: PINNED (chosen in the project's written order of 2026-11-20 06:15 UTC). Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] v6 CHANGED (Q9: the 30 code points added). Code: guard/redact.py:1049-1073 (`_TYPED_PUNCT`, `_TYPED_CATEGORIES`, `_char_class`). Mutants: tests/redact_mutants.py:230-260 (30 `Q9 U+XXXX` mutants, killers at :243-256); table of 30 killers all KILLED: evidence/G1-mutants-run.md:154-186 (30 rows with KILLED); the class split 20 + 6 + 3 + 1 is the Q9 reviewer's, evidence/G1-mutants-run.md:194. Whole-file run after E13: "94 of 94 good" (handover/core-c/ESCALATIONS.md:107; the laptop re-run is JOB 2, not done here).
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
- [INTERNAL] evidence/G2-p1d-a.md fix round batch: 7,879 passed, 0 failed (the builder's). v6 STRUCK the "135-file pick batch" and "27 test functions" lines (head 6b990d9 process facts); tests/test_p1d_a_paths.py is in the merged-tree batches only if listed in their command line (batch 5 line 3).

Read, not tested:

- UNVERIFIED (read in the code; no recorded batch names its test): a message is re-read until it stops changing, at most 3 times. If it never settles, a fixed note is shown instead.
- Id fields are not masked (K59).

Known gaps and fixed findings:

- **K59. Not masked:** the "requested by" line and other id fields.
  - Example (UNVERIFIED: read from the code, not tried on Slack): a requester id `slack:U1|<!channel>` could make Slack notify everyone in the channel.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written request).
- **K60. Not proven:** that no clickable link remains. The old test used the same patterns as the code it tested. A new test now uses its own patterns and also checks against a link-finding library.
  - Example (UNVERIFIED): a link whose end is not in the test's own, finite list of web-address endings could still slip past both.
  - Status: OPEN. Evidence: TESTED (the independent test); UNVERIFIED (the missed link). Who acts: the text and masking team.
  - [INTERNAL] v6 CHANGED. tests/test_p1d_link_oracle.py:1-9 (shares no code with the package), :21 (its own suffix list), :218 (`test_oracle_agrees_with_linkify_it_py`; the library is not Slack's renderer, line 204); pyproject.toml:52-53 (linkify-it-py==2.0.3 in the dev group). evidence/INT-merged-batch-5.md:5 (the skip count fell from 2 to 1 because this test now runs).
- **K61. Fixed:** an e-mail address with a digit or `_` glued behind it was shown whole.
  - Example: `anna.m@example.org9` is now masked.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
- **K62. Not checked:** approval summaries stored before these fixes, as shown on the admin page.
  - Example: a summary stored before the fixes could still show an e-mail address; nobody has looked.
  - Status: OPEN. Evidence: NOT RUN. Who acts: the text and masking team.

MEASURED slowdown of approval-message masking on the joined code (median, on the builder's test machine):

- a 174-character message took 0.00126 seconds before and 0.00360 seconds now;
- a 71,179-character message took 0.367 seconds before and 0.655 seconds now.
- [INTERNAL] v6 CHANGED (source line). defaults.py:~84-86 ("a 174-character card 1.3 ms -> 3.6 ms ... a 71,179-character card 367 ms -> 655 ms"). The four-digit figures are v5's rounding of evidence/G2-p1d-a.md.

### 2.8 Set-up

- **K63. Late failure:** the project file allows installing on Python 3.12. Once the text-folding change ships, by design a pilot or prod install there succeeds and the program refuses to start.
  - Example: an operator installs on 3.12; the program then refuses to start (see README, section "Python version").
  - Status: OPEN. Evidence: NOT RUN (no install on 3.12 was tried). UNVERIFIED (read from the file): that the project file allows 3.12.
  - Who acts: the connector and store team.
  - [INTERNAL] No written request yet; core-c writes one if the lead agrees (4.5).

### 2.9 What was not run (NOT RUN)

- The full test suite.
- Python 3.12 on this work's code.
- Database version 17. The tests here ran on the builders' machines; the automatic test service is set to 17.10.
- The spend-cap tests on PostgreSQL on this branch. They skip, because the store code is not here.
- Any live call to an AI service. Any end-to-end stop of a live run. The gate installed at any call point.
- The planned host-name and base64 change and the overlap fixed-point change (not merged).
- The whole-file deliberate-code-break runs of text folding (256 breaks; the builder ran 25), the gate and the secret finder at this head.
- A recorded test batch on the merged code as a whole.
- [INTERNAL] v6 CHANGED. Database 17: .github/workflows/ci.yml:41 (`postgres:17.10`). Mutant counts: tests/textnorm_mutants.py (256 per CHANGELOG.md, G10 counts), tests/gate_mutants.py (105 per requests/3), tests/redact_mutants.py (94 after E13, handover/core-c/ESCALATIONS.md:107), tests/g8_mutants.py (35 per evidence/G8-build-notes.md:38). The laptop jobs 1 and 2 (requests/lead-build-1.md) will record their results; none is claimed here. v5's "238 of the 240" line and the spacing-mark line are struck.

---

## 3. For README.md: "Python version"

[v6] As of head a60da3394 (2026-11-20 12:25 UTC).

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

[INTERNAL] v6 proof for part 3. defaults.py:214 (`TEXTNORM_PINNED_UNIDATA = "15.1.0"`), :217 (`TEXTNORM_PINNED_PYTHON = "3.13"`); guard/textnorm.py:1720-1735 (`require_pinned_unidata`; the message names Python 3.13), :143 (the code's own note that 3.12 carries Unicode 15.0.0: not checked on a real 3.12, NOT RUN), :460 (the key tag holds `ud=` and the Unicode edition, so keys from two editions never match); app.py:128-134 (the refusal comes before any backend is built); pyproject.toml:8 (`requires-python = ">=3.12"`); `python -c "import unicodedata; print(unicodedata.unidata_version)"` printed 15.1.0 on Python 3.13.3 on this laptop (evidence-cword.md).

---

## 4. Technical appendix (INTERNAL, does not ship)

[v6] As of head a60da3394 (2026-11-20 12:25 UTC). Internal references (codes, test names, files, orders, commits) appear only here. Team codes: core-b = the connector and store team; core-c = the text and masking team.

### 4.1 Key to codes used in the sources

| code | meaning |
|---|---|
| cloud/core-c | [v6] the shared branch; head at the time of writing: a60da3394 (board commit 2026-11-20T12:25:45Z). v5's head was 6b990d9; `git diff --stat 6b990d9..HEAD -- src` shows 7 changed source files (approvals/gate.py, defaults.py, guard/injection.py, guard/model_gate.py, guard/redact.py, guard/runmap.py, guard/textnorm.py) |
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
| G4 | the planned base64 and host-name change (old ticket P1c), not built [v6: ticket v8, tickets/G4-P1c-redactor-gaps-v8.md, 8 plan review rounds; not merged]; v2 ticket tickets/G4-P1c-redactor-gaps-v2.md (330f4fb, 07:46 UTC); plan review round 2 tickets/G4-review-2.md (readiness 2 B, 9 M; codebase 3 B, 8 M); v3 drafter g4v3 running (STATUS-BOARD 08:09 UTC) |
| dz, cb / dz2, cb2 / F-r3 | first / second / third independent result review of the gate; third: tickets/F-result-review-3.md (design 0 B, 4 M, 5 N; codebase 0 B, 5 M, 7 N) |
| G7-r2 | result review round 2 of G7: tickets/G7-result-review-2.md (codebase 1 B, M2-M7 = 6 M (its header says 5), N8-N10; design 0 B, 5 M, 3 N) |
| gate fix round 4 | [v6] commit b83accc65 "code F: gate round 4 (review round 3 fixes: budget and deadline, net on every secret, slots, cost and interrupt rows, docs)"; merged; batches 1 to 5 |
| secret finder fix rounds 3 to 7 | [v6] G7 rounds 3 to 7, merged (REPORT-1200Z.md line 4; tickets/G7-result-review-3.md to -6.md); batches 1 to 5 |
| g4r | plan review round 1 of G4 (tickets/G4-review-1.md: 8 Blockers, 6 distinct, 12 Majors) |
| E1 to E7 | entries in ESCALATIONS.md (E7: database rights) |
| G7 to G11, E9 to E17, Q9, Q16 | [v6] G7 secret finder rounds, G8 glued-rest change (merged), G9 overlap fixed point (not merged), G10 text-fold deadline (merged), G11 candidate for E16 (not built); escalations E9 to E17 in ESCALATIONS.md; Q9 the 30 code points; Q16 the link library |
| ORDER nnn | orders from the lead in ORDERS.md; MJ-A to MJ-D = Majors of the lead's review round 3 (ORDER 020, about 07:25 UTC) |
| T:: / E:: | tests/test_model_gate.py / tests/test_runmap_enforce_map.py |
| sweep | the step that masks every copy of values already in the run map (the "masking step" of a search round) |
| NO_MAP | the named constant for "no map" |
| strict xfail | strict expected failure |
| refusal words | gate: `mask_refused`, `framing_refused`, `worst_case_failed`, `worst_case_invalid`, `reserve_refused`, `reservation_invalid` (type `GateRefused`); store: `kill_switch` (stop switch), `daily_budget`, `monthly_budget`, `limits_unavailable`, `bad_amount`, `usd_cap` |
| audit decision field | `map_enforced`, `map_enforced_empty`, `enforce_custom`, `map_failed`, `no_map`; codes `call_interrupted`, `reserve_interrupted`, `held_value_left` |
| framing marker | `<<TOOL RESULT call_id=ID tool=NAME>>` ... `<<END TOOL RESULT>>`; assistant line `tool NAME {json}` |
| UnidataMismatch | the start-up refusal of `textnorm.require_pinned_unidata` (textnorm.py:1720-1735 [v6]; app.py:128-134; accepts only `defaults.TEXTNORM_PINNED_UNIDATA` = "15.1.0") |
| REDACT_BUDGET_S | 6.0 CPU seconds of the calling thread per `redact_text` call (defaults.py) |
| `_SETTLE_ROUNDS` | 4 (redact.py:2145, [v6] v5 said :1751): rounds 2 to 5 after the first pass; RedactionError("NotSettled") past it (redact.py:1318) |

### 4.2 Table of known gaps

[v6] Rows changed in v6 carry "[v6]" or are listed in 4.8. K1, K3 to K9, K21 to K23, K25, K27, K28, K30, K31, K33 to K37, K42, K44 to K49, K52, K54 to K59, K61 to K63 are carried from v5; evidence-cword.md shows that each cited test exists at head.

| gap | status | evidence level | evidence | who acts |
|---|---|---|---|---|
| K1 secret not found passes | PINNED | TESTED | T::test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job | nobody |
| K2 short, digits, common words, touching | PINNED | TESTED | E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept; E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept; rule read in redact.py `_sweep` 2309-2330 [v6: v5 said 1905-1917] | nobody |
| K3 other spellings | PINNED | TESTED / UNVERIFIED (alias) | T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate; E::test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced; E::test_stated_limit_a_copy_split_by_nul_characters_is_not_found; T::test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced; alias spellings: F-r3 codebase M2 (reading) | nobody (gate); gate fix round 4 for the alias point |
| K4 letter case | PINNED | TESTED | T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced | nobody |
| K5 overlap tail | PINNED | TESTED | E::test_stated_limit_partial_overlap_leaves_a_tail; T::test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent | nobody |
| K6 joined key and value | PINNED | TESTED | T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched | nobody |
| K7 placeholder-shaped values | PINNED | TESTED | E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced; E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder; E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass | nobody |
| K8 fields not masked | PINNED | TESTED | T::test_t20_system_and_tools_are_not_touched; T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched. The prompt-registry install check is a separate request (requests/3-bind-mapping-required.md section 6, ORDER 020 MJ-D), WAITING on core-b, on an [INTERNAL] line in part 2 | nobody |
| K9 no map | PINNED | TESTED | T::test_no_map_means_no_enforce_step_at_all; NO_MAP placement checked by tests/test_gate_install_callers.py | nobody |
| K10 audit says map in use | FIXED | TESTED | T::test_r2_m5_the_audit_decision_says_what_was_really_enforced; T::test_d1_every_audit_row_says_whether_the_map_was_enforced; model_gate.py:244-248, :725-731; batches 1-5 | nobody |
| K11 forged marker | FIXED | TESTED | T::test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client[id,name,both]; model_gate.py:744-800; batches 1-5 | nobody |
| K12 edge value tail | OPEN | NOT REPRODUCED | dz2-M2 (reading); NOT REPRODUCED by the builder (evidence/F-G0-1.md "Review round 2 fixes (final)"); safety net runmap.py:936-949; comment runmap.py:678-682 | core-c |
| K13 per-call time and size | OPEN | MEASURED / UNVERIFIED | runmap.py:625-640, :643-675, :689-777; model_gate.py:59-66 (one scan of one stretch not interruptible, "about 7 s" at :63); 0.018 s: evidence/F-G0-1.md; T::test_r3_m2_a_deadline_inside_the_sweep_is_a_budget_refusal_with_its_own_code | core-c |
| K14 planted secret stops tool calls | OPEN | TESTED | model_gate.py:368-396, :80-86; T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker; T::test_r3_c_m1_a_secret_that_is_part_of_a_listed_tool_name_refuses_the_call | owner (decision 1) |
| K15 tool line rewritten | FIXED | TESTED | T::test_r3_c_m1_a_tool_name_in_the_tools_list_stays_exact_when_a_known_value_lies_inside_it; model_gate.py:744-800 | nobody |
| K16 interrupt leaves no row | FIXED | TESTED | T::test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on; T::test_r3_n4_a_keyboard_interrupt_in_the_enforce_step_writes_a_row_and_passes_on; T::test_r3_n4_an_interrupt_between_reserve_and_the_call_writes_a_row_and_passes_on; model_gate.py:570-575, :610, :616 | nobody |
| K17 two writers | OPEN | UNVERIFIED | runmap.py:603-606; model_gate.py:119-121; requests/3 does not name it (grep) | core-c (adds it to request 3) |
| K18 run left "working" | WAITING | UNVERIFIED | agent_loop.py:476-478 [v6: v5 said :477]; requests/3-bind-mapping-required.md sections 3 and 7 | core-b |
| K19 guardrail call outside gate | STATED | UNVERIFIED | inputs/plan-v4-final.md line 29 (frozen 2026-11-20); tests/test_gate_install_callers.py:43-47 (BYPASS, bedrock_guardrail row at :44) [v6: v5 said line 41] | nobody |
| K20 failed call not settled (gate); store not here | WAITING | TESTED (gate side) | T::test_pin_an_unmarked_provider_error_is_not_settled (test_model_gate.py:1205); requests/2-refused-before-response.md; store code absent: tests/contracts/test_t1_reserve_cap.py:41, :50 [v6: v5 cited T1 expiry case, core-b tree] | core-b |
| K21 empty cost booked as free | WAITING | TESTED / UNVERIFIED | T::test_m5_a_zero_cost_reply_is_settled_at_zero; models.py:299 `cost_usd: Decimal = Decimal(0)`; requests/3 section 4 | core-b |
| K22 unreadable cost not settled | PINNED | TESTED | T::test_pin_a_reply_with_no_usable_cost_is_not_settled; T::test_o17_2_... | nobody |
| K23 retries settle last attempt | WAITING | UNVERIFIED | llm/retry.py lines 92-107 (reading, E6 item 3); ORDER 017 item 3 (06:30 UTC) | core-b |
| K24 higher real cost passed to settle (gate side) | PINNED | TESTED (gate side) | T::test_a_settle_above_the_reservation_is_passed_through (test_model_gate.py:283) [v6: v5 also cited tests/contracts/test_t1_reserve_cap.py, which skips on this branch: struck] | nobody |
| K25 worst-case formula | WAITING | UNVERIFIED | model_gate.py:187-190; k1b/loop.py:115, :170; llm/common.py has no worst_case_usd (grep) [v6] | core-b |
| K26 spend counters rights | OPEN | UNVERIFIED | store/migrate.py:40, :53-54 (read) [v6: v5 cited evidence/B-grants-rework.md findings 1, 2 on core-b ref 576f292: struck] | owner (decision 5), then core-b |
| K27 stale price table | STATED | NONE | plan-v4-final line 29, frozen 2026-11-20 | nobody |
| K28 in-memory cap on command lines | STATED | NONE | plan-v4-final line 29; refusal `usd_cap` (ORDER 014) | nobody |
| K29 stop-switch rights | OPEN | UNVERIFIED | store/migrate.py:55; store/migrations/0001_core.sql:94; no trigger on kill_switch (0002_audit_chain.sql:25-34 covers audit tables only) [v6: v5 cited the reset login: struck] | owner (decision 5), then core-b |
| K30 in-flight call, command lines ignore stop | STATED | NONE | plan-v4-final line 30 (B3 "Stop"), frozen 2026-11-20 | nobody |
| K31 audit lacks masked flag and route | OPEN | UNVERIFIED | F-result-review-1.md nits (reading); model_gate.py decision constants cover map use only (read at HEAD) | owner (decision 2) |
| K32 reset login audit rights | STRUCK | UNVERIFIED | no reset login in this tree (`grep -n reset store/migrate.py` is empty); audit tables append-only: store/migrate.py:42-45, :57; 0002_audit_chain.sql:25-34 | nobody (restored when core-b code is merged) |
| K33 command lines audit to screen | STATED | NONE | plan-v4-final line 32 (B3 "Audit"), frozen 2026-11-20 | nobody |
| K34 unknown shape | STATED | NONE | README.md "Limits and trust" (origin/main, ce70eb5, 2026-11-04) | nobody |
| K35 bare number | STATED | MEASURED | evidence/P1c-probe.md (24 of 43, main code; "accepted property"); G4 v2 section 6 ("order 64 item 4": not in ORDERS.md) | nobody |
| K36 host names | OPEN | MEASURED | evidence/P1c-probe.md (28 of 44 leaked, main code); G4-review-1, G4-review-2 | owner (decision 3), then core-c |
| K37 short base64 | OPEN | MEASURED | evidence/P1c-probe.md (under 40 characters: 41 of 41; all base64 rows: 52 of 142; main code) | owner (decision 3), then core-c |
| K38 glued IPv4, phone, IBAN, UUID | FIXED | TESTED / MEASURED | redact.py:77-89; evidence/G8-build-notes.md:38; probe in evidence-cword.md (`10.20.30.40_x` -> `<IPV4_1>_x`) | nobody |
| K39 repeat not proven complete | OPEN | TESTED | redact.py:1238-1318, :2145; tests/test_redact_idempotent_property.py::test_one_pass_is_a_fixed_point_and_leaves_no_raw_copy[constructed:0]; tests/test_redact_settle_loop.py; limits: K72 | core-c |
| K40 tail up to 7 | FIXED | TESTED | tests/test_redact_settle_loop.py tail cases; batches 1-5; the "20 of 28" count is WITHDRAWN (evidence/G7-1.md:290): struck | nobody |
| K41 finder time | OPEN | MEASURED | redact.py:1238-1319, :1358-1364; defaults.py:35-45, :88 [v6: v5 cited round 2 code figures: struck] | core-c |
| K42 tool error not in map | WAITING | UNVERIFIED | G7 review dz-6 (reading); requests/4-error-reason-run-map.md | core-b |
| K43 escaped-placeholder spelling and cut-off start | PINNED | TESTED / MEASURED | redact.py:928-952, :1739-1740; tests/test_redact_own_output.py::test_only_the_exact_escaped_shape_is_left_alone; tests/test_redact_own_output_hardening.py::test_legitimate_own_output_is_left_alone; tests/test_redact_context_after_sweep.py:498 | nobody |
| K44 wrapped secret | FIXED | TESTED | tests/test_redact_own_output_hardening.py::test_a_secret_wrapped_in_lookalike_brackets_is_masked (10 failed before; ab6ff2f) | nobody |
| K45 finder on its own output | FIXED | TESTED / UNVERIFIED (other places) | tests/test_redact_own_output.py::test_the_tool_error_path_adds_no_map_entry_and_keeps_the_escaped_text (8 failed before); caller table in tickets/G7-context-after-sweep.md (reading) | nobody |
| K46 separators in a secret | STATED | NONE | SECURITY.md "Stated limits of redaction" (origin/main, ce70eb5, 2026-11-04) | nobody |
| K47 look-alike search in the finder | FIXED | TESTED | tests/test_redact_g3_port.py; pick batch; merged in d95a727 | nobody |
| K48 escapes, newer characters, hidden marks | STATED | UNVERIFIED | tickets/G1-result-review-1.md line 17 (documented limits confirmed by reading) | nobody |
| K49 Chinese zero (U+3007) | PINNED | TESTED | tests/test_textnorm_mixed_script_micro.py::test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed; evidence/TW-order020.md (1 of 852 table entries) | nobody |
| K50 over-matching (rates) | STATED | MEASURED | evidence/G1-false-hits-and-cost.md:106-130; defaults.py:257-264; no src caller of scan_holds (grep) | nobody |
| K51 injection CPU budget | PINNED | TESTED / MEASURED | defaults.py:296-302; injection.py:66-77, :257; textnorm.py:397, :601-615; tests/test_textnorm_deadline.py:266, :299; evidence/G10-build-notes.md:12-14 | nobody (LEAD DECISION D4) |
| K52 long Chinese or Japanese text | STATED | MEASURED | evidence/G1-fold.md "G1 fix round 1", M6 (300,000 characters; threshold not measured) | nobody |
| K53 dashes, quotes, slashes, 30 code points | PINNED | TESTED | redact.py:1049-1073; tests/test_redact_g3_port.py (test_q9_*); tests/redact_mutants.py:230-260; evidence/G1-mutants-run.md:154-194; ORDER 014 item 9 | nobody |
| K54 Latin accent matching | PINNED | TESTED | tests/test_evidence_decomposed.py::test_known_difference_from_main_an_invisible_character_between_a_letter_and_its_accent_now_joins_them; ORDER 010 item 3 (05:47 UTC) | nobody |
| K55 other scripts (grounding, runtime/evidence.py) | OPEN | UNVERIFIED | G1 review M7 (reading) | owner (decision 4) |
| K56 undo recombines | FIXED | TESTED | tests/test_undo_composes.py (9 of 10 failed before) | nobody |
| K57 boundary split | FIXED | TESTED | tests/test_injection_chunk_boundary.py (6 failed before) | nobody |
| K58 start-up order | FIXED | TESTED | tests/test_app_unicode_check_order.py::test_a_wrong_unicode_version_refuses_a_pilot_build_before_any_backend_is_made (3.13, version stubbed) | nobody |
| K59 requested-by line | WAITING | UNVERIFIED | G2 review M3 (reading); requests/5-card-ids-redact-defang.md | core-b |
| K60 link check | OPEN | TESTED / UNVERIFIED | tests/test_p1d_link_oracle.py:1-9, :21, :218; pyproject.toml:52-53 | core-c |
| K61 glued e-mail | FIXED | TESTED | tests/test_text_parts_together.py::test_glued_email_regression_digit_or_underscore_behind_the_address; tests/test_p1d_a_paths.py::test_glued_addresses_are_masked_whole_in_one_pass; merged in d95a727 | nobody |
| K62 admin page | OPEN | NOT RUN | G2 review "not checked" (the admin console) | core-c |
| K63 install on 3.12 succeeds | OPEN | NOT RUN | pyproject.toml line 8 `requires-python = ">=3.12"` (read at HEAD and on origin/main); no request file | core-b (core-c writes the request if the lead agrees) |
| K64 planted edge values over 4,096 | OPEN | TESTED / UNVERIFIED | runmap.py:629-640; T::test_r3_m1b_planted_held_values_past_the_old_cap_of_256_do_not_brick_the_run; requests/3 section 7 (the map only grows) | core-c |
| K65 net blind to a value spanning a framing word | PINNED | TESTED | runmap.py:936-949; model_gate.py:51-58; T::test_r3_m3_the_net_covers_every_secret_value_not_only_the_held_back_ones; T::test_r3_n2_stated_limit_a_value_spanning_a_fixed_framing_word_is_not_replaced | nobody |
| K66 tool name slot vs tool list | FIXED | TESTED | model_gate.py:368-404, :744-800; tests test_model_gate.py:2598, :2624 | nobody |
| K67 install list judge sites | FIXED | TESTED | tests/test_gate_install_callers.py:56-63, :296, :353 | nobody (install: core-b, K18) |
| K68 rolled-back spelled entry | FIXED | TESTED | redact.py:1665-1676, :1816; tests/test_redact_settle_loop.py:250, :261 | nobody |
| K69 map not checked as the run's own | OPEN | TESTED / UNVERIFIED | model_gate.py:528-529, :245, :731; T::test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping; tests/test_gate_install_callers.py:186 | owner (with decision 6), then core-c |
| K70 glued shapes left readable by design | PINNED | TESTED / MEASURED | tests/test_redact_glued_rest.py:104, :137; tests/g8_cases.py:54, :489; G8 ticket v6 section 6 and 13 | nobody (LEAD DECISIONS L-D13, L-D15, L-D17) |
| K71 remainder of a long token (L15) | PINNED | TESTED / MEASURED | tests/g8_cases.py:247-309; tests/test_redact_glued_rest.py:263; ESCALATIONS E16 | nobody (LEAD DECISION E16) |
| K72 overlaps leave a readable part (E10) | PINNED | TESTED | tests/test_redact_settle_loop.py:607, :1376; defaults.py:112-114 | core-c |
| K73 refusal of a whole document | STATED | MEASURED | redact.py:1318, :1364, :1793, :1996; defaults.py:98-125 | nobody |
| K74 finder memory (E14) | OPEN | MEASURED | ESCALATIONS E14; defaults.py:119-120 | core-c |
| K75 extra map entry on the tool-error path (E9) | PINNED | TESTED / MEASURED | redact.py:936-948; tests/test_redact_own_output_hardening.py:202, :229; evidence/E9-own-output.md | nobody (LEAD DECISION E9) |
| K76 spelled placeholder returned decoded (E15) | PINNED | TESTED / MEASURED | tests/test_runmap_e15_placeholder_spellings.py; ESCALATIONS E15 update | nobody |

State items (not gaps):

[v6] The items below are v5's, written at head 6b990d9. They are superseded by 2.0 and by the batch files named there, except where marked [v6].

- Gate not installed: tests/test_gate_install_callers.py holds 5 strict expected failures [v6] (lines 233, 243, 280, 327, 353; v5 said 3, lines 210-236) until core-b installs. tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered passes since aa7c5fa (commit message; DECISIONS 07:40 UTC).
- [v6] STRUCK, the test skips on this branch (see K20). The 50-connection test: tests/contracts/test_t1_reserve_cap.py::test_fifty_connections_against_a_cap_of_three_grant_exactly_three, plus 16 more cases (evidence/T1-reserve-cap.md), 49 passed twice on PostgreSQL 16.15, Python 3.13.18.
- Pick batch: 12,392 passed, 2 failed, 108 skipped, 7 xfailed in 135 files (-n 2, not perf). Failures and their ends: see the [INTERNAL] lines of 2.0. NOT RUN there: Python 3.12, PostgreSQL 17, the full suite, the full batch after the re-pin.
- G7 fix round 2 batch (evidence/G7-1.md): 9681 passed, 73 skipped, 5 xfailed, 0 failed (251 s). The commit it ran on is not recorded; the line was committed in 0fcc5e1 (07:44 UTC), after a2b6311 (07:41 UTC).
- Mutants: evidence/F-G0-1.md "Review round 2 fixes (final)" records "81 of 81 good; problems: []". This drafter counted 81 `mutant(` calls in tests/gate_mutants.py at HEAD (AST count, no mutant run). Search-text matching at HEAD not checked.
- Gate tests behind part 2.1 to 2.4: T::test_pin_no_client_call_without_a_reservation; T::test_t1_pass_path_order_is_enforce_reserve_call_settle_audit; T::test_t12_a_spend_refusal_passes_unchanged_and_no_call_is_made[kill_switch]; T::test_pin_every_outcome_writes_exactly_one_audit_row; T::test_i9_the_module_has_no_logger_no_exception_text_and_no_module_state; T::test_t18_no_secret_in_any_audit_row_exception_or_log_record; T::test_t17_a_raising_audit_sink_never_loses_the_reply_or_the_settle; T::test_m2_settle_raising_after_a_paid_call_returns_the_reply_and_the_row_says_ok.
- Those gate tests last ran in the gate builder's batch "1 failed, 2307 passed, 2 xfailed" (evidence/F-G0-1.md line 244, before the review-round-2 fixes). The one failure is named there: the producers registry test.

### 4.3 Counts by status (76 gaps)

[v6] Recomputed from the 4.2 table by a script (scratchpad build.py). v5's FIXED ON BRANCH status is retired. STRUCK is new: K32 only. The evidence-level tally of v5 (TESTED only, MEASURED only, and so on) is not carried: it was not recounted for K70 to K76 and the changed rows.

| status | count | gaps |
|---|---|---|
| PINNED | 22 | K1-K9, K22, K24, K43, K49, K51, K53-K54, K65, K70-K72, K75-K76 |
| STATED | 12 | K19, K27-K28, K30, K33-K35, K46, K48, K50, K52, K73 |
| WAITING | 7 | K18, K20-K21, K23, K25, K42, K59 |
| OPEN | 18 | K12-K14, K17, K26, K29, K31, K36-K37, K39, K41, K55, K60, K62-K64, K69, K74 |
| FIXED | 16 | K10-K11, K15-K16, K38, K40, K44-K45, K47, K56-K58, K61, K66-K68 |
| STRUCK | 1 | K32 |
| total | 76 | 22 + 12 + 7 + 18 + 16 + 1 = 76 |

Gaps named in part 1 (32 of 76):

- item 5: K25, K20, K21, K23, K42, K59, K18, K8 (request), K63;
- item 15 K34; item 16 K37; item 17 K36; item 18 K8; items 19-20 K19; item 21 K35, K46; item 22 K42; item 23 K65, K66, K67;
- item 24 K25; items 25-26 K20; items 27-28, 44-45 struck (K24, K26 store side); item 29 K21; item 30 K23; item 31 K26;
- items 32-33 K68; item 34 K29; item 35 K14; item 36 K64; item 37 K13; item 38 K41; item 39 K63;
- items 47-48 K39; item 49 K70; item 50 K71; item 51 K72; item 52 K73; item 53 K74; item 54 K75.

Distinct: K8, K13, K14, K18, K19, K20, K21, K23, K25, K26, K29, K34, K35, K36, K37, K39, K41, K42, K46, K59, K63, K64, K65, K66, K67, K68, K70, K71, K72, K73, K74, K75 = 32.

Order rule (item 8): groups first; within a group wider exposure first, roughly; a tested or measured gap before an UNVERIFIED one of about the same width. [v6] Money group: K25 (all reservations), K20, K21, K23, K26 (UNVERIFIED); v5's K24 items are struck.

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

38. [v6] K64: a v5 reviewer's cap of 256 held-back values versus the code's 4,096 (runmap.py:636). We used the code.
39. [v6] K26, K29, K32, K24 and items 27, 28, 31, 44, 45: v5 used the connector and store team's store code (ref cloud-core-b 576f292, evidence/B-grants-rework.md). That code is not at head a60da3394 (no `reserve_spend` in src; migrations stop at 0005). We kept what the grant map at this head shows and struck the rest.
40. [v6] K13: the reviewer's estimate "128 million steps" versus the gate's own note "about 7 s" (model_gate.py:63). The budget is built; we keep the note's figure as UNVERIFIED and strike the estimate.
41. [v6] K41: v5's "4.00 seconds" belongs to round 2 code (evidence/G7-1.md:318). We use the figures in defaults.py:35-45.
42. [v6] G8 L-D13: the ticket's section 6 default is "not masked"; the text of the same row also describes option (c). We use the default, because tests/test_redact_glued_rest.py:137 pins F1 to F6 as not masked and the probe on this head confirms `call 415-555-0132.` is unchanged.
43. [v6] Q9: the 30 code points are counted as 20 + 6 + 3 + 1 by the Q9 reviewer (evidence/G1-mutants-run.md:194); the builder's text (line 43) says 25 + 3 + 1 + 1. Both total 30. We use the reviewer's split.
44. [v6] Head: the lead's job named sha 7c31dbc97; the fetched head of origin/cloud/core-c is a60da3394 (it holds 7c31dbc97 and later notes and E15 pin tests). v6 is written against a60da3394.

### 4.5 Requests to core-b (files in handover/core-c/requests)

1. 1-producers.patch: register the gate as a model caller (applied by core-c as aa7c5fa; decision 7).
2. 2-refused-before-response.md: the "refused before any answer" mark (K20).
3. 3-bind-mapping-required.md: required map, `GateRefused`, empty cost, catch sites, prompt-registry install check (K8, K18, K21). To add (core-c, not done in this file): "one writer per run map" (K17); the judge call sites (K67, gate fix round 4 lane).
4. 4-error-reason-run-map.md: tool-error text with the run map (K42).
5. 5-card-ids-redact-defang.md: id fields on approval messages (K59).

Lead's orders to core-b without a request file: sum the cost of all attempts (ORDER 017 item 3, K23); the worst-case formula (ORDER 016c item 13, K25); an operator release for expired reservations (ORDER 017 item 4); the install test with core-b (ORDER 020 MJ-C). K63 has no request yet: core-c writes one if the lead agrees. [v6] Since v5 (git diff 6b990d9..HEAD -- handover/core-c/requests) only requests/3-bind-mapping-required.md changed (24 lines: the RunMap type rule, the new refusal words, section 7 on the registration side) and requests/lead-build-1.md was added. Request 3 now names the registration side (a planted value makes the map grow) but still not "one writer per run map" (K17).

### 4.6 What is still moving at the time of writing (head a60da3394)

[v6] Replaces v5's 4.6, which described head 6b990d9. Sources: handover/core-c/REPORT-1200Z.md and STATUS-BOARD.md (process facts, not code facts).

- Not merged: G4 (host-name and base64 change; ticket v8, builder on a worktree branch) and G9 (overlap fixed point; built on a worktree branch, one perf test fails on it, a fix is being tried). Nothing in this file describes them.
- Not built: E14 (finder memory), the E16 candidate (G11). Tickets are being drafted (STATUS-BOARD).
- Laptop jobs of requests/lead-build-1.md: job 1 (whole suite on 3.13 and 3.12, PostgreSQL 17, ruff, bandit), job 2 (all mutant runs), this job 3. Their results are not in v6.
- Lead decisions open: part 1b, plus G9 L-D1 and L-D6', L-D7, G4 L24 to L28 (REPORT-1200Z.md item 7).

### 4.7 INTERNAL: change log of review round 4 (does not ship)

[v6] This is v5's log, kept for the record. Its numbers and line references are v5's. v6's own log is 4.8.

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

### 4.8 [v6] Change log of version 6 (does not ship)

Every change from v5, with its reason. The proof per statement is evidence-cword.md (egm/core-complete-2026-11-20/evidence-cword/).

| change | where | reason |
|---|---|---|
| head and dates | all parts | v5 head 6b990d9 (08:09 UTC); v6 head a60da3394 |
| FIXED ON BRANCH retired; K10, K11, K15, K16 become FIXED | part 0, 2.1, 4.2 | the gate's round 4 and later fixes are merged and in batches 1 to 5 |
| K66, K67, K68 become FIXED | 2.1, 2.5 | round 4 (K66, K67), G7 rollback fix (K68) |
| K12, K13, K14, K17, K64, K65, K69 re-worded | 2.1 | gate budget, net on every secret, 4,096 cap, RunMap check, substring rule |
| K38 FIXED; K70, K71 new | 2.5 | G8 glued-rest change and its stated limits (L4 to L15) |
| K39, K41 re-worded; K72, K73, K74 new | 2.5 | G7 rounds 3 to 7 (fixed point, deadlines, E10 limits, refusals, E14) |
| K43 re-worded; K75 new | 2.5 | E9 (SECRET-only exemption, accepted extra entry) |
| K76 new | 2.5 | E15 pins |
| K50, K51 re-worded | 2.6 | G10: rates published, CPU budget on the injection read |
| K53 extended | 2.6 | Q9: the 30 code points |
| K60 re-worded | 2.7 | independent link test |
| K20, K24, K26, K29 re-scoped; K32 STRUCK; items 26 to 28, 31, 34, 44, 45 | 1, 2.2 to 2.4 | the store code is not on this branch |
| 2.2 bullets on 50 connections struck | 2.2 | tests skip on this branch |
| "66 of 66" and "81 of 81" breaks struck | 2.1 | no run at this head |
| "up to 7 calls" struck | 2.5 | not shown by the code |
| 2.0, 2.9, 4.1, 4.6 rewritten | 2, 4 | process history of head 6b990d9 removed |
| part 1b added | 1 | lead decisions L-D13, L-D15, L-D17, E16, G10 D4, E9 |
| part 1 items 2, 4, 6, 7, 9, 21, 23, 26 to 28, 31 to 38, 44, 45, 47, 48 changed; 49 to 54 new | 1 | as above |

Checks after writing, by a script (scratchpad build.py and check_v6.py): every K1 to K76 appears once in part 2 and once in 4.2; each part 2 status equals its 4.2 status; the 4.3 counts sum to 76; part 1 holds no K numbers; no project words in parts 2 and 3 outside [INTERNAL] lines; sentences over 30 words in parts 0 to 3 are listed in evidence-cword.md.
