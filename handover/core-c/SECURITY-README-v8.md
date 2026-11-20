# Security wording v7: what the tests show and what is still open

DRAFT, version 8, written on 2026-11-20 by the docs pass builder of the text and masking team. It is a revised copy of SECURITY-README-v7.md and replaces it. It describes the code at commit 2552bcc95 of cloud/core-c (the last change to src and tests, 2026-11-20 15:44 UTC). The repository head at the time of writing was beb2b3ea6 (board and notes commits only after 2552bcc95). It has had no fresh style review. v7 described fd1fb3e31; what merged since, and what each change did to a statement, is in 4.8. Line references on `[INTERNAL]` lines were moved from fd1fb3e31 to this head by a script that follows the diff of each file; a reference that lies inside a changed stretch is marked `[re-check]`, and the references of the entries this version rewrote were read from the head. Anything the builder could not check on this head says UNVERIFIED. Who reads what: see the next paragraph.

Who reads what: part 0 and part 1 are for the owner only. Part 2 ships as SECURITY.md. Part 3 ships as README.md, section "Python version". Part 4 is internal and does not ship.

Strip step before shipping, for whoever copies the text:

1. Copy part 2 into SECURITY.md. Start at its heading. Stop before the `---` line that comes before part 3.
2. Copy part 3 into README.md. Start at its heading. Stop before the `---` line that comes before part 4.
3. In both copies, delete every line whose text starts with `[INTERNAL]`. Ignore any list dash and spaces in front of it.
4. Delete nothing else.

After step 3, parts 2 and 3 name no project, team code, session, review round or document version. They say "the owner", "the connector and store team" and "the text and masking team".

This draft changes no other file. The repository's SECURITY.md, CHANGELOG.md and README.md are not edited by it.

Reading rule: every statement must be checkable against the code at 2552bcc95. Code facts carry a file and line on an `[INTERNAL]` line or in part 4. Where the only basis is reading, the statement says UNVERIFIED. Statements of earlier versions that rested on the connector and store team's store code are not repeated: that code is not on this branch.

---

## 0. Plain glossary (read this first)

As of commit 2552bcc95 of cloud/core-c (2026-11-20 15:44 UTC).

### How to read the marks (one list)

Evidence words (how we know). Every claim carries one of these:

- **TESTED**: a named test ran and passed in a recorded batch of tests. A recorded batch is one whose result line is written in a file of the project: an evidence file, a build note or the status board. Each TESTED claim names the test or the batch.
- **MEASURED**: a recorded run measured the number given, or a direct call printed the output given.
- **UNVERIFIED**: the only basis is someone reading the code or the text. Nothing was run to show it.
- **NOT REPRODUCED**: a fault was reported. A later run of the reported case, as it was understood, did not show it. The exact case of the report is not on file.
- **NOT RUN**: the check was not run at all, or no recorded result exists. Nothing is claimed about its result.
- **NONE**: no test, run or reading is named. The gap is written down from a plan, an order or the published SECURITY.md only.

Status words (one per known gap):

- **FIXED**: changed, and a test fails without the change. The change is on the shared branch. A recorded batch that holds that test passed on the builder's copy or on the merged code. It is not on the product's main line. Part 4 names the independent review where one exists.
- **PINNED**: not fixed, on purpose. A named test fails if the behaviour changes. This includes a "strict expected failure": a test that records the gap and fails once the gap closes. The team whose change closes the gap removes that mark. For the five install tests, that is the connector and store team.
- **STATED**: accepted and written down, with no test. The source is a plan, an order, a ticket, an evidence file, the code's own notes or the published SECURITY.md or README.md. Each STATED line names its source. Nobody is asked to act.
- **WAITING**: another team must act, and a written request or a written order exists.
- **OPEN**: nobody has fixed or decided it yet. The line names who must act.

Every example value in this file is made up. None is a real secret.

### People and teams

- **The owner**: the person who owns Hadavin, pays for the work and has the final say.
- **The lead**: the coordinating session (software, not a person) on the owner's laptop. It writes the orders and records verdicts. The lead is named in parts 0, 1 and 4 only.
- **DECISIONS.md**: the text and masking team's written record of its choices. The lead writes its verdict in one column of it.
- **The connector and store team** (internal code: core-b): the build team that owns the model connectors, the store, the agent loop and the approval-message code. It must install the gate.
- **The text and masking team** (internal code: core-c): the build team that built the gate, the secret finder changes and text folding. It wrote this file.
- **Builder**: a worker of the text and masking team that writes code and runs the tests. **Reviewer**: an independent checker. Reviewers only read; the builders and the team ran the tests.
- **Operator**: the person who installs and runs the kit for a client.
- Note: the docs pass builder wrote v8 from the code at 2552bcc95. Nobody outside that pass has checked v8.

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
- **Test and replay command lines**: two programs for staff. One runs saved test cases; the other re-plays a stored case for checking.
- **Planted text**: text an attacker put into a document or tool result so that the agent reads it.
- **Sensitive value**: a secret (password, key, token) or an identifier (e-mail address, host name, account number).
- **Known value**: a sensitive value already in the run map.
- **Mask**: put a placeholder where a sensitive value was. **Placeholder**: a fixed text such as `<SECRET_1>` that the model sees in place of the value. (This file uses only these two words for this.)
- **Run map**: one table per run, kept in memory, that records which real value each placeholder stands for. **Restore**: put the real value back in place of a placeholder, for a tool that needs it.
- **Secret finder**: the code that searches text for sensitive values by their shape and masks them. It runs where text enters a run (tool results, documents, approval messages). Only it adds to the run map.
- **Search round**: one pass of the secret finder's patterns over the text, then one masking of every copy of the known values. **One call of the secret finder** runs up to 5 search rounds.
- **Kind**: the type the secret finder gives each value it finds. Secret kinds: passwords, keys, tokens. Identifier kinds: e-mail, host name, IP address and the like.
- **Withheld**: the secret finder hides a whole line it cannot mask in place, and shows a fixed note.
- **Glued**: written directly against another character, with no space between.
- **Fail closed**: when in doubt, refuse the text or the call rather than let it through.
- **Text folding**: turning look-alike letters, invisible characters and accents into one plain spelling before searching. Look-alike letters are, for example, full-width letters and Cyrillic letters that look Latin.
- **Unicode**: the world standard list of characters. Each Python version carries one edition of it.
- **base64**: a common way of writing any data as letters and digits. The **base64 view** is the secret finder's step that decodes base64 text and searches the decoded text.
- **The gate**: one wrapper meant to sit in front of every model call. It masks known values, reserves money, makes the call, settles and writes an audit row. It searches for no new values.
- **Installed**: placed at every point in the code that calls a model. The gate is NOT installed yet.
- **Held back**: a known value at a placeholder's edge (it starts with `>` or ends with `<`), or a piece of a placeholder. The gate masks it last, so the placeholder text stays whole.
- **Safety net**: the gate's last check on each stretch of text before it is sent. It refuses the call when it finds a known secret that is still readable.
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
- **Database login**: a named account the software uses to reach the store. On this branch the grant map names a runtime login. The connector and store team's code adds others; it is not on this branch.

### Record and code words

- **Audit row**: one line in the permanent record of what happened. It holds short codes, not message text.
- **Refusal word**: the exact short word the gate or store prints when it refuses. The words are listed in the appendix (4.1).
- **The shared branch**: the text and masking team's pushed line of changes, from which the lead takes code. **The product's main line**: what clients get. Nothing of this work is on the main line.
- **Test**: a small program that checks one behaviour and fails when it changes. **Batch**: one recorded run of many tests.
- **Deliberate code break**: a planted fault in the code, used to prove a test can fail. A break that no test catches "survives". A break that cannot change any output is "equivalent".
- **Known gap**: a weakness we know about, or a gap fixed in this work. Each has a number K1 to K85, used in parts 2 and 4. Part 1 uses no K numbers.
- **Item**: one numbered line of part 1.

---

## 1. Owner summary

As of commit 2552bcc95 (2026-11-20 15:44 UTC).

### What to know first

1. **Short answer: the gate is written but not installed. No agent in use goes through it. Do not promise a client any gate protection yet.**
2. TESTED: a batch of the whole test suite, without the slow-timing and live tests, ran on the merged code from 14:06 to 14:17 UTC. It gave 15,955 passed, 561 skipped, 74 expected failures and 10 failures. A later batch is recorded on the status board: the same kind of batch gave 16,071 passed and 2 failed, and a batch of the slow-timing tests at commit 2552bcc95 gave 96 passed, 1 skipped and 0 failed in 427 seconds.
3. Of the 10 failures of the first batch, 6 were a fault the secret finder's newest change brought in; it was fixed, and the 4 test files it touched then passed (297 passed). Two more were approval-message rows, re-recorded twice since, from the measured output. One is a project file that names a vendor: it is still red, because files of the project's handover folder still hold the vendor's brand string, so one repository-rule test fails. One failed on the older code too; the board says a recording was re-keyed in 2552bcc95 (UNVERIFIED that this is that test). Of the 2 failures of the later batch, the board names the vendor-string file and the re-keyed recording.
4. UNVERIFIED which commit the later non-slow batch ran on: the status board names 2552bcc95 for the slow-timing batch only. Between the first batch and 2552bcc95 the gate's last check, the secret finder's punctuation, overlap and host-name rules, and some deliberate code breaks changed (4.8).
5. Reviewers keep finding faults. Two second-round reviews of earlier changes, written at 14:38 and 14:42 UTC, found 1 Blocker and 7 Major findings. Fixes for them are now built and merged (the gate's piece lookups, the secret finder's punctuation rules, the overlap step). No review of these fixes is on file yet. Item 22 names what the fixes do not close.
6. The connector and store team must write the worst-case formula and install the gate. The gate now honours a "refused before any answer" mark, but no model connector sets it yet. That team also has seven other open items:
   - empty cost fields;
   - retried calls;
   - tool-error text;
   - approval-message id fields;
   - the run's status after a refusal;
   - a start-up check that system prompts come only from the prompt registry;
   - installs on Python 3.12, which has no written request yet.
7. The text and masking team's host-name change and its base64 change are both merged. A planned change for long opaque tokens is written as a plan and not built. The lead owes many decisions on merged work (part 1b).
8. This summary names 41 of 85 known gaps. The groups come in this order: secrets that can reach the AI service, then money, then wrong actions, stopped work and set-up.
9. Within a group, the order is a rough judgement. Wider exposure comes first. Where two gaps are about as wide, a tested or measured one comes before an UNVERIFIED one.
10. NOT RUN on the code at 2552bcc95:
    - a whole-suite batch whose commit is named (item 4);
    - Python 3.12 (the whole suite ran on Python 3.12 at an earlier commit, before most changes named here);
    - the store's own tests on database version 17 (they skip: the store code is not on this branch);
    - any live call to an AI service;
    - any end-to-end stop of a live run;
    - the whole files of deliberate code breaks for text folding (268 breaks) and the gate (140). The files of the glued-text change (43), the base64 and host-name change (58) and the punctuation change (35) were run whole by their builders before merge (part 2.9).
11. **Your action (the owner):** read the eight decisions in 1a. Answer the lead by 2026-11-23 12:00 UTC for decisions 1 to 7. Decision 8 has no date. For each decision, keep the default or choose another answer.
12. If you have not answered by then, each default in 1a applies. Silence on decision 3 means the client note is not sent. The lead records each answer, or each default, in DECISIONS.md.
13. The text and masking team proposed this date. The lead has not confirmed it in writing (a search for "11-23" in ORDERS.md and DECISIONS.md finds nothing).
14. Today an agent in use is protected only by the secret finder as it is on the product's main line, without this work's changes.
15. Installing the gate and passing a fresh review will not be enough. The gaps below stay until each one is closed.

### Secrets that can reach the AI service (worst first)

16. NONE (written in the published README since 2026-11-04): a secret in a shape the secret finder does not know goes out as written. This stays after install too.
17. MEASURED on the main line: host names without a "host" label are not masked. 28 of 44 test lines leaked. On this branch the host-name change is merged and 7 of the same 44 lines still leave a label readable (MEASURED here). Part 2 lists them. Decision 3 now asks only about a client note.
18. TESTED (the base64 rows of the base64 and host-name test file): base64 text under 40 characters is now masked when its decoded text holds a value the secret finder knows. On the main line, 41 of 41 such test lines leaked.
19. Limits of item 18 stay (TESTED as expected failures, or read in the code). Base64 glued to other base64 characters stays readable. So does base64 split across fields, wrapped with a log prefix on each line, or padded with blank-looking characters. Hex and base32 are not decoded. Base64 whose decoded text holds no known shape stays readable.
20. TESTED: the gate never masks the system prompt or the tool descriptions.
21. UNVERIFIED (read in the install test's table of calls kept outside the gate): the guardrail call goes around the gate. It is neither masked nor counted against the cap. The lead's frozen plan of 2026-11-20 accepts this. Tell the lead if you want it changed.
22. MEASURED here: a password stored with punctuation inside it stays readable in its plain copy. Examples: `password=hunter22,x` then `hunter22`, and the same with `.x` or `&x=1`. A double-encoded edge (`%250A`) stays too. Open: no fix is built and nobody has decided to accept it.
23. TESTED: the plain copy of a password stored with punctuation, a wrapper or an escaped edge at its ends is now masked: `password=hunter22, hunter22`, `**hunter22**`, `hunter22%0A`, `hunter22&quot;`, `<br/>hunter22`, and an all-capital value such as `ADMIN_1`. Item 22 lists what stays.
24. UNVERIFIED (read in the code): some paths send text to the AI service with no masking. They are the replay command line with its "already masked" flag, its copy of the model's own tool call, an extraction function no code calls, and a demo. The lead decides.
25. Also leaking today, each in one narrow shape, so they rank below items 16 to 24:
    - MEASURED on the main line: a bare number with no label is often not masked. 24 of 43 test lines were not masked. The acceptance that two files cite was not found, so it is UNVERIFIED.
    - NONE (written in the published SECURITY.md since 2026-11-04): a secret that holds a space or `;` is masked only up to that character.
    - MEASURED here: a phone number directly before a full stop and a letter (`415-555-0132.Thanks`) stays readable. Before a full stop and a space it is now masked.
    - MEASURED here: a phone or card number as one digit run beside a letter, and an IBAN inside a file name or key, stay readable (item 50).
26. UNVERIFIED (read from the code, not run): a secret first seen in a tool's error message is not masked in later text. It waits on the connector and store team.
27. TESTED: the gate's last check is wider. It refuses a call when two known secrets overlap and a piece of 4 or more characters stays readable. It also refuses a known secret found in a decoded spelling, such as full-width letters or escapes.
28. Limits of item 27 (TESTED for three, read in the code for the rest). A base64 copy, a copy split by colour codes and an identifier in another spelling pass. So do a piece under 4 characters, a piece from the middle of a value, and other encodings.
29. TESTED: a secret that spans a fixed word of the framing marker goes out as written.

### Money (worst first)

30. UNVERIFIED (read from the code; nothing to test yet): the gate's worst-case function is not written. Until the connector and store team writes it, the cap has nothing real to reserve. A worst case of 0.00 USD is accepted.
31. TESTED: the gate does not settle a failed call, so its worst case stays booked. A failure the model connector marks "refused before any answer" is settled at 0.00 USD. UNVERIFIED (read): no connector sets that mark yet.
32. UNVERIFIED: what the store keeps booked after a failed call. That is the connector and store team's code, which is not on this branch.
33. TESTED (the gate's side): a reply that costs more than its worst case is passed on to settle at its real cost.
34. TESTED (the gate's side only): a reply with an empty cost field is booked as free. UNVERIFIED: that a model connector ever leaves the field empty.
35. UNVERIFIED (read from the code): when a call is retried, only the last attempt's cost is counted. Earlier billed attempts are lost, so spending is understated.
36. UNVERIFIED (read from the grant map; no database test run): the runtime login holds SELECT, INSERT and UPDATE on the spend counters. So faulty code could lower a booked amount. Decision 5 covers it.

### Wrong actions, stopped work and set-up

37. TESTED (two cases): after the secret finder undoes a half-made entry, no old record survives in the two tested cases. Before the fix, a tool could have got the wrong account or credential.
38. UNVERIFIED (read from the grant map and the migrations): the runtime login can change the stop switch, including back to off. It can also sign a stop record with any name. Decision 5 covers it.
39. TESTED: planted text can make a run's later tool-using calls refuse. It does so if it plants a secret of 4 or more characters that equals a tool's name or a piece of one. Decision 1 covers it.
40. TESTED (pinned as it is): a planted value whose first characters are common words can make the gate refuse every later call of a run. Ordinary text beside a placeholder then looks like a leak, and the refusal stays for the rest of the run. No fix is built; the lead's decisions on it are open (part 1b).
41. TESTED: the gate accepts up to 4,096 values at a placeholder's edge and 20,480 entries in all. Past that, every later call of that run refuses (worked out, not run). The agent loop stops a run earlier, at 2,000 values (UNVERIFIED, read). One value read beside a key stops at 4,096 hits of its first characters and refuses the call, for the rest of the run.
42. Hostile text can make one gate call run long. One budget per call covers characters, steps and two time limits of 6 seconds: processor time and wall-clock time. NOT REPRODUCED: a reported long stall inside one scan.
43. MEASURED earlier: one call of the secret finder on a text built to be slow took 4.5 to 5.4 seconds against its 6-second budget. A machine 12 to 33 percent slower refuses that text (worked out, not run).
44. Once the text-folding change ships: by design, a pilot or prod install on Python 3.12 succeeds, and then the program refuses to start. NOT RUN: a start on Python 3.12.

### Shown by tests (each in the teams' own tests, on the code alone)

45. TESTED: in the gate's tests, known values are masked before a call, in message text and documents only. They are not masked when the calling code states "no map".
46. TESTED: only the test and replay command lines may state "no map".
47. TESTED: in the gate's tests a refused reservation means no call. UNVERIFIED: that the store refuses while the stop switch is on. NOT RUN: any stop of a live run.
48. Item 47 does not cover a call already in flight, the test and replay command lines, or the guardrail call.
49. TESTED: in the gate's tests, its code holds no message or error text, and no audit row in those tests held a secret.

### New since the last version (merged work)

50. MEASURED here: glued shapes left readable as built. A phone or card number as one digit run with a letter beside it (`x4155550132`). An IBAN inside a file name, a path or a key (`acct_iban_DE89...`). Part 1b has the lead's decisions on these.
51. MEASURED here: a UUID, or a number of 10 or 11 digits, set off by `_` or a letter inside a long token cuts the token. A remainder of up to 39 characters stays readable. Before, the whole token was masked. The lead decides whether to accept this.
52. TESTED: two values that overlap in the secret finder's text are now masked whole, in either order, and a secret that overlaps a value held as another kind gets a secret entry of its own. The overlap limits of the last version are closed.
53. TESTED and MEASURED: a hostile text can make the secret finder refuse a whole document. Nothing is shown. A real document in the same text is lost.
54. TESTED: the secret finder's memory for very large values is now capped (about 360 MB per build, worked out). A run whose map holds more than 524,288 characters stops and asks for a person. The lead has not approved these numbers.
55. TESTED: a tool's error text read twice can make one extra map entry for each distinct token of another kind written after a key. No real value is stored in it.
56. TESTED: the planted-instruction check now also has a wall-clock limit of twice its 30-second processor budget.
57. UNVERIFIED (read in the code): 14 public functions of text folding have no caller in the product. Decision 8 asks whether to move or delete them.

### 1a. The eight decisions (the owner decides decisions 1 to 7 by 2026-11-23 12:00 UTC)

If there is no answer by then, the default in the fourth column applies. The last column says who then acts. No build date is set for any of them; the owner may ask for one.

| # | Question | What each answer means | Default if no answer | Who then acts |
|---|---|---|---|---|
| 1 | Planted text can make a known value equal part of a framing marker. When should the gate refuse the call? | Narrower rule: refuse only when a known secret of 4 or more characters equals a tool's name or a call number, or is a piece of a name in the tool list. It is built and TESTED. Wider rule (the lead's earlier order): also refuse when any known value equals a fixed marker word. Only the narrower rule was tested. A reviewer proposes a third way: never store a tool's name as a secret. UNVERIFIED that this closes the gap. | The narrower rule. Why: under the built rule the marker's fixed words stay exact (TESTED). The wider rule's extra refusals would stop more runs; that it protects no more text is UNVERIFIED. Both rules let a planted secret equal to a tool's name stop a run (item 39). | The text and masking team keeps the narrower rule in the code. The lead records the result in DECISIONS.md. |
| 2 | Should each audit row also say whether anything was masked, and which route was used? | Without it, nobody can tell from the record whether masking happened. Today the row says only how the run map was used: a map, an empty map, a test function or no map. | Add a "masked: yes or no" field and the route. No text goes in the row. | The text and masking team builds it in a later gate change. |
| 3 | The host-name change is merged (item 17). Should a note on host names go to clients? | The change masks names under a private suffix and after the word `host`. Seven of 44 test lines still leave a label readable (part 2). A note would tell clients which names stay readable. | No client note (the default of the earlier draft, written when the change was not merged). OPEN: whether that default still holds after the merge is the lead's and owner's to say. | The lead sends a draft client note on host names by 2026-11-22 12:00 UTC if the owner wants one. The owner says by 2026-11-23 12:00 UTC whether to send it. |
| 4 | Accept that the grounding check now counts a name as present in more cases in Korean, Japanese and Indian scripts? | This happens when an invisible character splits the name. Accepting lets more proposed names pass the check, with no tests for those scripts. | Go back to the older rule for those scripts until tests exist. The older rule lets fewer names pass. | The text and masking team makes the change in its next text-folding round. |
| 5 | Tighten wide database rights, or accept them in writing? | Runtime login: can rewrite the spend counters, and can change the stop switch and sign a stop record with any name (read from the grant map on this branch). Other logins belong to the connector and store team's code, which is not on this branch. Accepting leaves the cap and the stop record resting on code alone. | Tighten them: narrower rights, or one fixed database function per action. | The lead writes the order. The connector and store team changes its database rights in its next store change, before any pilot uses the store. |
| 6 | Should the gate refuse a call whose run map is empty? Or should it accept the call and mark the audit row? | The lead's written order says refuse. Today's code accepts and marks the row (UNVERIFIED, read). Refusing stops each run whose first document held no value the secret finder found. Either way the gate masks nothing in that call. The gate refuses a plain dict or a copy of the map. It cannot tell another run's map from the run's own (UNVERIFIED, stated in the code). | Refuse, as the written order says. It is the stricter choice. | The text and masking team changes the code to refuse. It also adds the check that the map is the run's own. |
| 7 | Accept the text and masking team's changes to two of the connector and store team's files, or have that team redo them? | The files are the Slack approval-message file and the list of code that calls a model. The list names the gate; that is a list entry, not an install. Two teams editing one file can collide. | Accept both. Either change can be undone with one commit. | The lead tells the connector and store team in its next order. |
| 8 | Move or delete the 14 text-folding functions that no product code calls (item 57)? | They are working code with their own tests and deliberate code breaks. Keeping them keeps unused code in the security path. Deleting them removes tests no product path needs. | No date and no change: nothing moves until the owner says yes. | The text and masking team moves or deletes them on the owner's yes. |

### 1b. Decisions the lead still owes (the wording depends on them)

These are the lead's, not the owner's. The default is what the merged code does. Each row is a LEAD DECISION until the lead answers in writing. None is recorded in DECISIONS.md at the time of writing (a search for each id finds nothing).

| id | question | default (built) | what the other answer does |
|---|---|---|---|
| L-D13 | A phone number directly before a full stop | Built on the lead's build order (escalation E19): masked when a space, the end, `)` or `,` follows the stop, in all four phone patterns. A stop followed by a letter or digit still ends no phone. | Option (c): the `+` pattern only (measured: two rows change). Whether all four patterns is the lead's choice is not written down. |
| L-D15 | An IBAN beside `_` | Masked only after a short word at the start of a name, or before a short ending. Of 24 hand-picked shapes, 16 leave the whole IBAN readable. | Option (b) leaves 13 readable but splits more map entries inside random tokens. |
| L-D17 | A card number of 13 to 19 digits glued to a letter | Not built. `card_4242424242424242` is masked as a phone number and kept in the map. | A card-number check before the phone pattern. Not built and not worked out. |
| E16 | A UUID or a 10 or 11 digit number inside a long opaque token | Accept the readable remainder of up to 39 characters. | Ticket G11 (written, not built) keeps the token whole. |
| G10 D1-D10, M3 | The planted-instruction check's budgets | 30 CPU seconds per check (D4) and a wall-clock limit of 2 times that (M3 factor 2.0, from the lead's "about 2x"). D1 to D10 are the drafter's defaults. | Other budgets (6 s, 48 s, none); another factor. |
| E9 | The extra map entry for a tool's error text read twice | Accept it (option a). | Exempt the escaped tokens of other kinds on the tool-error path only (option b). |
| G9 L-D1, L-D6', L-D7, L-D3b | The overlap fixed point | The gate masks an overlap with existing placeholders and never refuses (L-D1); the anchored deep check, now with one read-back per edge (L-D6'); 1,000,000 union characters per call (L-D7); finder passes not counted (L-D3b). | Each has a written alternative in the G9 ticket. |
| E17 | A long known value that is readable beside its own repeating pattern | A text that needs too much work is refused (stated limit, pinned). The perf shape that failed passes; at the input cap it uses 54.5 percent of the limit (measured). | Whether a real log can hold such a value is the lead's call. |
| G4 L24-L28, L-B8 | The base64 view | The gate's old re-sort branch is kept (L24); re-pins by the second lander (L25); long encoded values accepted (L26, since then capped by E14); loose blocks and lazy line parts (L27, L28); no fallback for padded blobs (L-B8). | L-B8: a fallback that reads ASCII strings from a non-text blob (measured: no output changes on the corpora). |
| E20 | Deliberate code break R8 survives: it is equivalent once the overlap fixed point is in | Keep the branch and R8; the gate break file exits 1 on R8. | Delete the branch with the gate owner and drop R8. |
| E14 | The finder memory caps | 524,288 characters per run map and 786,432 trie nodes per build: the ticket's defaults. | Other numbers. |
| G12 6.1-6.7 | Punctuation at a stored secret's ends | The ticket's defaults (one edge rule at both ends, floor of 3 characters; the leading bracket is now stripped too, which 6.4 had left out). | The ticket's alternatives. |
| G13 D1-D8 | The gate's net and the unmasked paths | The replay command line with "no map" (D1), the replay echo (D2) and the unused extraction function (D3) are unchanged; base64 is not read at the gate (D4); a piece from the middle of a value is a stated limit (D5). | Delete the extraction function; mask the replay echo and rendered results again; read base64 at the gate. |
| G13 round 2 | Ordinary words at a secret's start refuse text beside a placeholder, for the rest of the run | Stated limit, pinned by a test (the current behaviour); no separate refusal code; the letter-only minimum is not built. A strict expected failure records the wanted behaviour. | A longer minimum for letter-only pieces; its own refusal code. |
| Gate (c) | The "refused before any answer" mark on a call whose retries ran out | Honoured: settled at 0.00 USD. The gate cannot verify the mark; the connector must set it only when no attempt was billed. | Not honoured on a call whose retries ran out. |
| PU1 | Two approval-message rows, re-recorded twice from measured output: first after the overlap fixed point (one more placeholder number), then back to the original number because the map now holds one value (`ab&amp;`). Nothing is readable. The builder asked the lead to confirm. | Re-recorded to the measured output. | Restore the old record and change the code instead. |
| E21 | The finder's break runner reads a timing test in its baseline, so a loaded machine stops it | Unchanged (moving the timing test out would loosen a check). | Move the timing test out of the baseline. |
| G4c (host names) | The host-name start rule: a name starts at an ASCII label character, so a name glued after a non-Latin letter is masked from its first Latin character (up to two extra characters go into the placeholder). Names with a public-looking ending, the short in-cluster forms and a private word inside a name stay readable. | Built as measured; the readable names are pinned. | Mask the public-looking and in-cluster names too (more over-masking of code and prose). |
| G12c numbers | The large-value rule (no extra entry for a value over 4,096 characters whose core differs by 16 or fewer) and the list of edge forms | The builder's numbers and list. | Other numbers or a longer list. |
| G13c cap | At most 4,096 hits of a key's first characters are read per key, then the call is refused | The builder's number (a dense hostile input gave about 16,000 lookups per key before). | Another number. |
| E23 (G9b) | The work units of the overlap check: a periodic secret of up to about 7,000 characters beside its own period is accepted, 8,000 or more is refused | The builder's measured calibration. The escalation file still says OPEN. | Other weights; close E23 in the file. |

Sources: handover/core-c/ESCALATIONS.md (E9, E14, E16, E17, E19, E20, E21, E22). Also tickets/G8-glued-rest-gap-v6.md section 6 (L-D13, L-D15, L-D17); tickets/G10-textfold-deadline-v4.md section 10; evidence/G9-build-notes.md line 10; evidence/G4-build-notes.md; evidence/G12-build-notes.md section "Lead decisions 6.1-6.7"; evidence/G13-build-notes.md section "Lead decisions"; tickets/G13-result-review-2-design.md "Resolution"; evidence/GATE-C-build-notes.md; evidence/TIDYP-build-notes.md (PU1).

---

## 2. For SECURITY.md: "What the tests show and what is still open"

As of 2026-11-20 15:44 UTC (commit 2552bcc95).

> **These items describe what tests showed on the gate, the secret finder and text folding, each run on its own. No test of the store ran on this branch. None of this describes an agent in use going through the gate. The shared branch is not the product's main line.**

### Words used here (this part ships alone)

Evidence words. Every claim carries one of these:

- TESTED: a named test ran and passed in a recorded batch of tests. A recorded batch is one whose result line is written in a file of the project. Each TESTED claim names the test or the batch.
- MEASURED: a recorded run measured the number given, or a direct call printed the output given.
- UNVERIFIED: the only basis is someone reading the code or the text. Nothing was run to show it.
- NOT REPRODUCED: a fault was reported. A later run of the reported case, as it was understood, did not show it. The exact case of the report is not on file.
- NOT RUN: the check was not run at all, or no recorded result exists. Nothing is claimed about its result.
- NONE: no test, run or reading is named. The gap is written down from a plan, an order or the published SECURITY.md only.

Status words (one per known gap):

- FIXED: changed, and a test fails without the change. The change is on the shared branch. A recorded batch that holds that test passed on the builder's copy or on the merged code. It is not on the main line.
- PINNED: not fixed, on purpose. A named test fails if the behaviour changes. This includes a "strict expected failure": a test that records the gap and fails once the gap closes. The team whose change closes the gap removes that mark.
- STATED: accepted and written down, with no test. Each STATED line names its source. Nobody is asked to act.
- WAITING: another team must act, and a written request or a written order exists.
- OPEN: nobody has fixed or decided it yet. The line names who must act.

People and code:

- The owner: the person who owns Hadavin and has the final say. The owner decides the open questions named below.
- The connector and store team: the team that owns the model connectors, the store, the agent loop and the approval-message code. It must install the gate.
- The text and masking team: the team that built the gate, the secret finder changes and text folding.
- Builder: a worker of the text and masking team that writes code and runs the tests. Reviewer: an independent checker who only reads.
- Operator: the person who installs and runs the kit for a client. The kit: this software package. Stages: demo (made-up data), pilot (a first, limited use with a real client) and prod (normal live use).
- The shared branch: the text and masking team's pushed line of changes. The main line: what clients get.
- Test: a small program that checks one behaviour. Batch: one recorded run of many tests.
- Deliberate code break: a planted fault in the code, used to prove a test can fail. A break that no test catches "survives". A break that cannot change any output is "equivalent".
- Kn: the number of a known gap in this list. A known gap is a weakness we know about, or a gap fixed in this work.

Model and run words:

- Model: the outside AI service that reads text and answers. A model call is one request to it. The system prompt holds the standing instructions sent with each model call.
- Guardrail call: a separate request to the cloud vendor's safety service. It is not a model call.
- Route: which AI service and which model a call goes to. Model connector: the code that talks to one AI service and reports the cost of each call.
- Run: one job of one agent, from start to finish. The agent loop is the code that drives a run step by step.
- Tool: an action an agent may use, such as a search. A tool result is the text a tool returns. Each tool call gets a call number. The tool list holds the tools' names and descriptions, sent with a model call.
- Calling code: the program code that hands a call to the gate. Test and replay command lines: two staff programs that run saved test cases or re-play a stored case.
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
- base64: a common way of writing any data as letters and digits. The base64 view: the secret finder's step that decodes base64 text and searches the decoded text.
- The gate: one wrapper meant to sit in front of every model call. It masks known values, reserves money, makes the call, settles and writes an audit row. It searches for no new values.
- Installed: placed at every point in the code that calls a model. The gate is not installed yet.
- Held back: a known value at a placeholder's edge (it starts with `>` or ends with `<`), or a piece of a placeholder. The gate masks it last.
- Safety net: the gate's last check on each stretch of text before it is sent. It refuses the call when it finds a known secret that is still readable.
- Framing marker: the fixed line the agent loop puts around each tool result. It holds fixed words, the call number and the tool's name. A forged marker is a copy of that line written by planted text.

Money and record words:

- All amounts are in US dollars (USD).
- The store: the database that records spending, reservations, the stop switch and the audit record. The secrets vault is the separate place where secrets are kept.
- Cap: the most money one agent may spend in a day and in a month. Worst case: the most a model call could cost.
- Reserve: before a call, count its worst case against the cap. Settle: after the call, book the real cost instead of the worst case. Booked: the amount counted against the cap at any moment.
- Empty cost field: a reply whose cost was never filled in; it reads as 0.00 USD. Unreadable cost: a cost that is absent, negative or not a number.
- Price table: the list of prices per AI service used to work out the worst case.
- Stop switch: a flag in the store. While it is on, the store is meant to refuse every new reservation. A stop record says who turned it on.
- Database login: a named account the software uses to reach the store. The grant map on this branch names a runtime login.
- Audit row: one line in the permanent record of what happened. It holds short codes, not message text. Refusal word: the exact short word the gate or store prints when it refuses.

### 2.0 State of the work

- WAITING: the gate is not installed. No point in the code that calls a model goes through it yet. The connector and store team must install it.
- NONE (the project's written order of 2026-11-20 06:30 UTC): the connector and store team will not install the gate before the model connectors can say "refused before any answer".
- TESTED: a batch of the whole test suite, without the slow-timing and live tests, gave 15,955 passed, 561 skipped, 74 expected failures and 10 failures. It ran on the merged code from 14:06 to 14:17 UTC on 2026-11-20.
- Of the 10 failures, 6 were a fault of a secret finder change; it was fixed, and its 4 test files then passed (297 passed). Two were approval-message rows, re-recorded twice since, from the measured output. One is a project file that names a vendor. One failed on the older code too.
- TESTED (a line on the project's status board): a later batch of the same kind gave 16,071 passed and 2 failed. The board names the vendor-string file and a recording that was re-keyed since. UNVERIFIED: the commit of that batch (the board names 2552bcc95 only for the next batch).
- TESTED (the same board line): the slow-timing tests on a quiet machine at commit 2552bcc95 gave 96 passed, 1 skipped and 0 failed in 427 seconds.
- One repository-rule test still fails: it checks every file of the project for a vendor's brand string, and some working notes outside the code hold one. It is not a security finding (MEASURED here: it is the only test that fails in a run of the documentation and brand tests on this head).
- TESTED: since the first batch the gate's safety net, the secret finder's punctuation, overlap and host-name rules, and four of the gate's deliberate code breaks changed. The builders' own batches for each are named in 4.2.
- NOT RUN: a batch of the whole test suite whose commit is named and is the code this file describes.
- UNVERIFIED (read in the test file): five install tests are marked as strict expected failures until the gate is installed. Once it is installed, they pass, and that pass fails the batch. Then the connector and store team removes the five marks.
- An independent review of the gate as changed in its fourth fix round exists only as a summary of another team's review. FIXED on the gate means the builder's tests pass, unless a review is named.
- [INTERNAL] Not installed: `grep -rn "ModelGate(" src` finds no construction outside guard/model_gate.py; tests/test_gate_install_callers.py holds 5 strict xfails (lines 233, 243, 280, 327, 353; `_xfail` at :230).
- [INTERNAL] Later batch: STATUS-BOARD.md line 4 (STATE, written 16:12Z): "Perf-marked tests at idle on cloud/core-c 2552bcc95: 96 passed, 1 skipped, 0 failed in 427 s ... Non-perf suite: 16071 passed, 2 failed (the vendor-string lead file; k5 recording fixed)". Which commit the non-perf batch used is not written. The recording commit is 2552bcc95 ("re-key the pii recording ... the old key held a leaked ' 678'"). Doc-test run for v8, `pytest -k "changelog or security or readme or brand or docs"` on the v8 worktree: one failure, the vendor-string test (see 4.8).
- [INTERNAL] First whole-suite batch: STATUS-BOARD.md line 16, entry "14:23Z WHOLE-SUITE RUN on the merged head (not perf/live, -n 3, 14:06-14:17Z, 647 s)". The 10 failures named there: 2 test_p1d_a_rows PU1 (re-pinned in 54c461ff8, TIDYP-build-notes.md), test_no_vendor_brand_string (a vendor brand string in handover/BRIEF-PREAMBLE.md, the lead's file), test_k5_tools::recorded_answers (fails at the base), 6 E9 own-output tests (G12b regression, fixed in 9806830d0; "297 passed in the four affected files"). The batch started after 01b355343 (14:06:40); the exact commit is not in the board line (UNVERIFIED which commit).
- [INTERNAL] Re-runs after it (STATUS-BOARD.md line 16): "core-c rerun of 10 gate/E9/b64 files: 509 passed 1 skipped 9 xfailed" (14:23Z, G13b merge); "core-c rerun test_model_gate+p1d_a_rows+p1d_a_paths+mutants_picked_up: 412 passed 1 skipped" (14:31Z, TIDY-P1D); "core-c rerun of b64_scan+p1c_gaps+own_output+g12: 1016 passed 24 xfailed" (14:31Z, G4 tidy fd1fb3e31). `git diff --stat 01b355343..fd1fb3e31 -- src` shows defaults.py, guard/model_gate.py, guard/redact.py, guard/runmap.py.
- [INTERNAL] Gate round 4 is commit b83accc65. Reviews on file: tickets/F-result-review-1.md to -3.md (before round 4). The core-a cross review of 7c31dbc97 (after round 4) is summarised in ESCALATIONS.md E18; its full text (handover/core-a/reviews/xreview-gate-g7.md on origin/cloud/core-a) was not read here. The gate files changed since: G13 and G13b (result reviews: tickets/G13-result-review-1-design.md, -1-codebase.md, -2-design.md), gate (c) (review round 1, STATUS-BOARD 13:23Z). Style review M10 asked for this line.

### 2.1 Masking before a model call (the gate)

Shown by tests (TESTED here means: test_model_gate.py and test_runmap_enforce_map.py passed in the batches named in 2.0; the tests added since passed in their builders' batches, named in 4.2):

- TESTED: before a call, the gate masks each known value with its placeholder. This covers message text and documents only. K8 lists what it skips.
- TESTED: the gate searches for no new values. The secret finder does that (K1).
- TESTED: if masking fails, the gate makes no call and reserves no money. Causes: text too long, content that is not text, past its size, step or time budget (its own refusal word), or text still changing after 4 maskings.
- TESTED: that refusal carries a refusal word and no text.
- TESTED: if no known value is present, the text goes out unchanged.
- TESTED: the gate does not change the calling code's messages, documents or run map.
- TESTED: the calling code must name its run map or state "no map". Leaving it out is an error, and so is a plain dict or a copy of the map. Only the test and replay command lines may state "no map" (K9).
- TESTED: the safety net refuses a call when a known secret of 4 or more characters is still readable. Since the latest change it also reads a piece of a secret beside a placeholder, and decoded spellings (K78, K3).
- NOT RUN: the whole file of deliberate code breaks for the gate on this code (140 breaks; one, R8, is known to survive as equivalent). Single breaks were run by hand (2.9).
- [INTERNAL] tests/gate_mutants.py holds 140 `mutant(` rows read here by grep; tests/test_gate_mutants_picked_up.py:20 `MIN_MUTANTS = 140` (12 added by the net lookup fix, E19t to E19ze). Four mutants (G13d, G13e, E19g, E19i) were repaired in 252ef2881 so that each is killed by its own test (evidence: the commit message; before, E19g and E19i were killed by another parameter first, per evidence/G13c-build-notes.md). Last whole-file run on record: laptop JOB 2 at ef5773ac4 (12:24Z): 104 of 105, R15 survived (inputs/evidence-cmut.md). Since: R15 killed alone (TIDYP-build-notes.md: `python tests/gate_mutants.py R15` -> 1 of 1 good); G13/G13b breaks E19a-s run by hand (G13b-build-notes.md "Mutants"); R8 survives as equivalent (ESCALATIONS.md E20 update).

Known gaps and fixed findings:

- **K1. Not protected:** a secret the secret finder never found.
  - Example: a raw `hunter2zz` that no shape matched goes out as written.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody; the secret finder is the control.
  - [INTERNAL] T::test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job (tests/test_model_gate.py:361).
- **K2. Not masked, even when known:** any value under 3 characters. Three more cases apply to an identifier and to a secret of exactly 3 characters. They are an all-digit value under 6 characters, a common word (`admin`, `test`), and a copy that a letter or digit touches.
  - Example: the known identifier `abc123` (an account number, not a secret) stays readable inside `xabc1234`, because a letter touches it (MEASURED here).
  - A known phone number is masked where no digit touches it: `build4155550132` becomes `build<PHONE_1>`; `74155550132` stays (MEASURED here).
  - Rule: a secret of 4 or more characters is masked wherever its exact text appears, even when it is all digits or a common word. The exceptions are K3 to K9 and K65.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept (tests/test_runmap_enforce_map.py:263), E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept (:291); rule guard/model_gate.py:8-15, guard/runmap.py:1122-1126, redact.py `_sweep` :2930, `_joins` :2957. Probe (python 3.13.18, direct `enforce_map`, fd1fb3e31 code): `xabc1234 and abc123` -> `xabc1234 and <TENANT_1>`; `build4155550132 and 74155550132` -> `build<PHONE_1> and 74155550132`; a SECRET `admin` is masked, a TENANT `admin` is not. Style review M6.
- **K3. Not masked by the gate:** a copy spelled differently from the run map. Such spellings include percent codes, web character codes, look-alike letters, hidden characters and the control codes terminals use for colours.
  - Example: the known identifier `qrs789`; the text `qrs&#55;89` (a web code for the digit 7) goes out as written (MEASURED here).
  - TESTED: for a known secret, the safety net now reads decoded spellings. A secret in full-width letters, in UTF-16, in percent codes, or split by NUL or zero-width characters refuses the call.
  - UNVERIFIED (read in the code): web character codes and backslash codes are decoded by the same step.
  - TESTED: an identifier in such a spelling still passes as written. A copy split by colour codes passes too (K79).
  - TESTED: for a known value that is not plain ASCII, the gate also masks its folded spellings.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody on the gate.
  - UNVERIFIED: whether the secret finder's text folding catches each such copy before the gate.
  - [INTERNAL] guard/model_gate.py:16-23 (rule and EXCEPTION), :26-31; runmap.py:1127-1132; `held_in_views` runmap.py:1503-1532. Tests T::test_t7_a_hidden_spelling_of_a_known_secret_refuses_the_call_an_identifier_passes (tests/test_model_gate.py:403), T::test_g13_10_a_secret_in_a_decoded_form_refuses_the_call (:2917), T::test_d7_a_copy_split_by_nul_or_utf16_refuses_the_call_an_ansi_split_copy_passes (:1888), E::test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced (tests/test_runmap_enforce_map.py:104), T::test_r3_c_m2_stated_rule_the_sweep_also_replaces_the_folded_spelling_of_a_non_ascii_value. Probe: `qrs&#55;89` with TENANT `qrs789` unchanged.
- **K4. Not masked:** the same value in other capital or small letters.
  - Example: known `db01.acme.example`, text `DB01.ACME.EXAMPLE` (MEASURED here).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced (tests/test_model_gate.py:1877).
- **K5. Not masked:** two known identifiers that overlap so that each is touched by a letter of the other. Neither is masked there.
  - Example: known identifiers `abcd` and `cdef`; the text `abcdef` goes out as written. Each standalone copy is still masked.
  - The rest of a held-back identifier also passes the safety net, which checks secrets only.
  - Two overlapping secrets, or a secret and an identifier, are now masked (K78).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] E::test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders (tests/test_runmap_enforce_map.py:180; the identifier case at :200-203); guard/model_gate.py:40-49 (the held-back identifier limit, G9 design review N2); runmap.py:1137-1143. Style review B1 asked "Who acts: the text and masking team" for the old overlap gap; that gap is now K78 (FIXED).
- **K6. Not protected:** a clean key and a clean value that look sensitive only when joined.
  - Example: `"user_id": "abc123"`, where neither part is in the run map.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched (tests/test_model_gate.py:2414).
- **K7. Not masked:** a known value that itself looks like a placeholder or sits in angle brackets.
  - Example: a known identifier `ab<X_1>cd` goes out as written. For a secret of that shape the safety net refuses the call.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced (tests/test_runmap_enforce_map.py:433), E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder (:441), E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass (:463); model_gate.py:32-39.
- **K8. Not masked:** the system prompt, tool descriptions, the role label (who speaks), extra message fields, the requested answer format and the route.
  - Example: an operator puts a customer's name in the system prompt; it goes out unmasked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody on the gate.
  - [INTERNAL] T::test_t20_system_and_tools_are_not_touched (tests/test_model_gate.py:1818), T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched (:1909); model_gate.py:3, :144-147. Separate request, WAITING on core-b: a start-up check that system prompts come only from the prompt registry (requests/3-bind-mapping-required.md section 6; ORDER 020 MJ-D).
- **K9. Not masked:** anything, when the calling code states "no map".
  - Example: a replay of an old case sends its text as stored.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] T::test_no_map_means_no_enforce_step_at_all (tests/test_model_gate.py:681); `NO_MAP` model_gate.py:528-530; NO_MAP placement checked by tests/test_gate_install_callers.py.
- **K10. Fixed:** the audit row said "map in use" when the map was empty. It also said so when the calling code had supplied its own masking function (allowed for tests). The row now says which.
  - Example: a run with an empty map writes "map empty", not the same row as one with 50 values.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] guard/model_gate.py:281-285 (MODE_*), :775-781; T::test_r2_m5_the_audit_decision_says_what_was_really_enforced (tests/test_model_gate.py:2454), T::test_d1_every_audit_row_says_whether_the_map_was_enforced (:1828).
- **K11. Fixed:** a known secret inside a forged marker went out unmasked. Now the gate keeps only the marker's fixed words and masks the rest.
  - Example: a document holds a forged marker whose call number contains the known `S3cr3tPw`. Before this fix, `S3cr3tPw` went out.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] guard/model_gate.py:794-852 (`_enforce_text`); T::test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client (tests/test_model_gate.py:2161).
- **K12. Fixed:** a secret at a held-back value's edge could leave its tail beside a placeholder.
  - Example: known `S3cr3t` and `>abcdef`. A reviewer read that `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`. A run gave `<SECRET_1><SECRET_2>`, with no leak.
  - TESTED: the safety net now refuses a call whose text holds `<SECRET_1>abcdef`, a piece of 4 or more characters of a known secret beside a placeholder. That test failed before the change.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] runmap.py:1078-1081 (NOT REPRODUCED note), :1414-1500 (`_touching_piece`). Tests tests/test_model_gate.py:2509 (`test_r2_m2_a_held_back_edge_value_does_not_leak_the_tail_of_a_secret`), :2521-2534 (`test_r2_m2_safety_net_...`, the `<SECRET_1>abcdef` line at :2532, red before G13: evidence/G13-build-notes.md "Red before / green after", "r2_m2"). The G13 design review notes r2_m2 uses an identity-enforce double.
- **K13. Not fully limited:** the time the gate spends on one model call. One budget per call covers the characters, the steps and two time limits of 6.0 seconds each. The first is processor time, read inside the masking step. The second is wall-clock time, read only between values and after each sweep.
  - TESTED: a deadline that passes inside the masking step refuses the call with the code `mask_budget_exceeded`.
  - TESTED: the masking step is given the call's own deadline. A deadline that passes after the start of the call stops it.
  - NOT REPRODUCED: a long stall inside one scan of one stretch of text was reported. A run of the reported shape, as understood, took 0.47 seconds of processor time for the gate's masking step. The secret finder took 0.89 seconds on the same text.
  - MEASURED earlier, before the current budget: 100 messages against a run map of 2,000 entries took 0.018 seconds.
  - Status: OPEN. Evidence: TESTED; NOT REPRODUCED (the stall). Who acts: the text and masking team.
  - [INTERNAL] runmap.py:1044-1071 (`EnforceBudget`: `deadline` = monotonic + REDACT_BUDGET_S, `cpu_deadline` = thread_time + REDACT_BUDGET_S, both read in `check()`), :1167-1178 (`check()` every 64th held-back value and after each sweep; `step()` reads it every 16 steps), :1169 (`first.sweep(out, deadline)` with the CPU deadline); defaults.py:94-97, :102. Tests T::test_r3_m2_a_deadline_inside_the_sweep_is_a_budget_refusal_with_its_own_code (tests/test_model_gate.py:2631), T::test_r15_the_sweep_is_given_the_calls_deadline_so_a_deadline_that_passes_after_the_snapshot_stops_it (:3051; killer of break R15). Stall: the gate's builder measured 6.8 s with a 0.5 s budget on round 4 code (ESCALATIONS.md E8 item 1); the code note model_gate.py:97-99 still says "about 7 s"; core-c's run (ESCALATIONS.md E18, third bullet: 500 held values of 20 to 49 `a`s, 262,144 characters) did not see it. 0.018 s: evidence/F-G0-1.md (before round 4). Style review M2, M3.
- **K14. Not protected:** a run's later tool-using calls. A planted secret of 4 or more characters makes each of them refuse. It does so when it equals a tool's name or a call number, or is a piece of a name in the tool list.
  - Example: a tool result contains `password=search_web`, where `search_web` is a tool's name. Later calls in that run refuse.
  - Status: OPEN. Evidence: TESTED (the rule as built). Who acts: the owner decides which rule. If no answer arrives by 2026-11-23 12:00 UTC, the rule as built stays.
  - [INTERNAL] guard/model_gate.py:417-444 (`framing_free`), docstring :109-129. Tests T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker (tests/test_model_gate.py:2033), T::test_r3_c_m1_a_secret_that_is_part_of_a_listed_tool_name_refuses_the_call (:2762). Decision 1 in part 1a.
- **K15. Fixed:** planted text could rewrite part of a tool's name in the line where the model asked for that tool.
  - Example: a document planted `password=logs`; the model then saw two names for one tool call.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody. See K66 for the tool list.
  - [INTERNAL] guard/model_gate.py:804-808, :828-829 (`slot`: a listed name stays exact); T::test_r3_c_m1_a_tool_name_in_the_tools_list_stays_exact_when_a_known_value_lies_inside_it (tests/test_model_gate.py:2736).
- **K16. Fixed:** stopping the program by hand while the gate masked, worked out the worst case, asked for a reservation, or in the instant after it, left no audit row. Now a row is written.
  - Example: the program is stopped by hand while the gate waits for its reservation. The record now holds a row that says "reservation interrupted".
  - The reservation stays booked: the worst case stays booked, not the real cost.
  - Not covered: a stop by hand inside settle or inside the audit write. Settle catches ordinary errors only, so such a stop after a paid reply leaves no row (UNVERIFIED, read in the code).
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] guard/model_gate.py:619-623, :640-644, :656-660, :664-666; `_settle` :706-719 (`except Exception` only); `_note` :870 (`contextlib.suppress(Exception)`). Tests T::test_r2_m7_a_keyboard_interrupt_in_worst_case_or_reserve_writes_a_row_and_passes_on (tests/test_model_gate.py:2476), T::test_r3_n4_a_keyboard_interrupt_in_the_enforce_step_writes_a_row_and_passes_on (:2843), T::test_r3_n4_an_interrupt_between_reserve_and_the_call_writes_a_row_and_passes_on (:2864). E18 nit 7; style review M9.
- **K17. Not safe:** two threads writing one run map at the same time can give one placeholder number to two values.
  - Example: two tools finish together and both values become `<SECRET_3>`.
  - Status: OPEN. Evidence: UNVERIFIED (stated in the code's notes, not run).
  - Who acts: the text and masking team adds "one writer per run map" to its install request to the connector and store team.
  - [INTERNAL] runmap.py:1001-1003; model_gate.py:154-156 ("Not pinned by a test (a race)"). requests/3-bind-mapping-required.md does not name it (grep "writer").
- **K64. Not protected:** a run's later calls, when planted text holds more than 4,096 values at a placeholder's edge (such as `password=>aaaa1`), or more than 20,480 values in all. The gate then refuses every later call of that run.
  - Example: one planted document with 4,097 such lines would stop the run (worked out from the code, not run).
  - The agent loop stops a run before that. At its default limit of 2,000 values, or 524,288 characters of values, the run ends asking for a person (UNVERIFIED, read in the code).
  - One key of the map reads at most 4,096 hits of a secret's first characters beside it. Past that the call is refused with `mask_budget_exceeded`, and the refusal stays while that text is in the run's history (K85).
  - Status: OPEN. Evidence: TESTED (the old limit of 256 is gone; 257 values no longer stop a run). Who acts: the text and masking team.
  - [INTERNAL] runmap.py:1031-1041 (ENFORCE_MAX_HELD 4096, ENFORCE_MAX_ENTRIES 20480, ENFORCE_MAX_STEPS 32768; "Above defaults.MAX_MAP_ENTRIES on purpose" at :1041); runtime/agent_loop.py:433-439 and :556-562 (`max_map_entries` / `max_map_chars` -> `document_too_complex`); config.py:245, :250 (defaults MAX_MAP_ENTRIES 2000, MAX_MAP_CHARS 524,288). Test T::test_r3_m1b_planted_held_values_past_the_old_cap_of_256_do_not_brick_the_run (tests/test_model_gate.py:2570). Style review M7; lead review N1.
- **K65. Not refused:** a known secret that spans a fixed framing word. The safety net checks each stretch of text between fixed framing words on its own.
  - Example: a known secret written as `tool read_logs` inside `password="tool read_logs"` is cut by the fixed word `tool ` and goes out as written.
  - TESTED: the safety net covers every known secret of 4 or more characters, not only held-back ones. A secret hidden in a made-up placeholder-shaped token that is not a key of the map refuses the call.
  - The safety net reads decoded spellings of a secret (K3), but not every spelling (K79, K80).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] runmap.py:1557-1576 (`held_value_left`), model_gate.py:61-65. Tests T::test_r3_m3_the_net_covers_every_secret_value_not_only_the_held_back_ones (tests/test_model_gate.py:2706), T::test_r3_m3_a_secret_hidden_in_a_placeholder_shaped_token_that_is_not_a_key_refuses_the_call (:2673), T::test_r3_n2_stated_limit_a_value_spanning_a_fixed_framing_word_is_not_replaced (:2723). Style review B1 (K65 sentence), re-worded after G13.
- **K66. Fixed:** a known value inside a tool's name. The gate masked it in the line where the model asked for the tool, but the tool list went out as written, so the model saw two names.
  - Now a name that is in the tool list stays exact in the line and in the marker. A secret that equals a listed name, or is a piece of one, refuses the call (see K14).
  - Example: the run map holds `<TENANT_1>` for `billing`. The tool `get_billing_info` is no longer rewritten to `get_<TENANT_1>_info`.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] guard/model_gate.py:417-453, :794-852; tests tests/test_model_gate.py:2736, :2762.
- **K67. Fixed (the list); the install is still waiting:** the install hand-over list and the install test name the judge's call points. They are the agent loop, the approval cards, the approval summaries and the replay loop. A test fails if a new call point appears that the list does not know.
  - Example: the approval summary reaches the judge from a place the old list did not name.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody for the list; the connector and store team installs the gate (K18).
  - [INTERNAL] tests/test_gate_install_callers.py:56 (`JUDGE_SITES`), :296 (`test_the_judge_call_sites_in_src_are_all_in_the_table`), :353-354 (`test_install_behavioural_the_judge_is_built_on_a_bound_gate`, strict xfail).
- **K69. Not checked:** that the run map given to the gate is the run's own, current map. The gate refuses a plain dict and a `dict(run_map)` copy. It cannot tell the run's own map from another run's map, or from a run map built from a copy. An empty run map is accepted, and the audit row says "map empty".
  - Example: the calling code passes yesterday's run map object. Values found today are not masked, and the row says the map was used.
  - Status: OPEN. Evidence: TESTED (the dict refusal and the empty-map row); UNVERIFIED (the stale-map case, stated in the code).
  - Who acts: the owner decides it together with one question: whether the gate refuses a call when the run map is empty.
  - If no answer arrives by 2026-11-23 12:00 UTC, the default applies: the gate refuses an empty map. Then the text and masking team changes the code.
  - [INTERNAL] guard/model_gate.py:577-578 (RunMap check), :573-575 (cannot tell another RunMap), :282 and :780 (`map_enforced_empty`), docstring :135-137. Tests T::test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping (tests/test_model_gate.py:1770), T::test_r3_m4_an_enforce_function_other_than_the_default_is_marked_and_documented_as_test_only (:2877). Decision 6 in part 1a.
- **K18. Not handled:** a gate refusal or a refused reservation leaves the run's status "working" instead of "stopped".
  - Example (UNVERIFIED, read from the code): the agent loop turns a model connector's error into a stop that asks for a person. A gate refusal is a different error, so it is not caught there. The planted-instruction check reports the same refusal as a guard failure.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written install request).
  - [INTERNAL] runtime/agent_loop.py:485-492 (`except ProviderError` -> NEEDS_PERSON); `GateRefused` is a RuntimeError (guard/model_gate.py:456), not a ProviderError. requests/3-bind-mapping-required.md sections 3 and 7.
- **K19. Not through the gate:** the guardrail call. It is neither masked by the gate nor counted against the cap.
  - Example: a run's guardrail calls cost money that the cap never sees.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: UNVERIFIED (read in the install test's table of calls kept outside the gate). Who acts: nobody.
  - [INTERNAL] tests/test_gate_install_callers.py:43-44 (`BYPASS`, the bedrock_guardrail row). The plan text: inputs/plan-v4-final.md line 29.
- **K78. Fixed:** two known secrets that overlap in the text left part of one readable, and the safety net missed it.
  - Example: known `hunter2-ABCDEFGH` and `ABCDEFGH-ZZZZZZZZ`. The text `x hunter2-ABCDEFGH-ZZZZZZZZ y` used to go out as `x hunter2-<SECRET_2> y`. It now goes out as `x <SECRET_1><SECRET_2> y`, in either map order (MEASURED here).
  - TESTED: a secret and an identifier that overlap are masked with their own placeholders.
  - TESTED: a piece of 4 or more characters of a known secret beside a placeholder refuses the call (K12).
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] runmap.py:1137-1143 (G9: read back, existing placeholders, map not written), :1414-1500 (`_touching_piece`, G13). Tests E::test_g13_1_the_review_input_leaves_no_piece_in_either_map_order (tests/test_runmap_enforce_map.py:866), E::test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders (:180), E::test_trap3_an_overlap_of_two_identifiers_is_masked_with_their_placeholders (:212), E::test_g13_2_a_secret_prefix_beside_a_key_is_held (:880), E::test_g13_3_a_secret_suffix_beside_a_key_is_held (:887). The E19 M1 input was closed by G9 (evidence/G13-build-notes.md "Phase 0"). Probe here: `enforce_map` on that input -> `x <SECRET_1><SECRET_2> y`. Style review B1 (K78).
- **K79. Not refused by the safety net:** a base64 copy of a known secret, an identifier split by NUL characters, and any copy split by terminal colour codes. Each goes out as written.
  - Example: a known secret written in base64 inside a message reaches the model. A base64 copy is the secret finder's work (K37).
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] guard/model_gate.py:26-31, :80-82; T::test_g13b_5_the_stated_limits_a_base64_copy_and_a_nul_split_identifier_are_sent (tests/test_model_gate.py:3036), T::test_d7_a_copy_split_by_nul_or_utf16_refuses_the_call_an_ansi_split_copy_passes (:1888). LEAD DECISION G13 D4 (base64 not read at the gate) and D8 (identifiers in decoded forms pass).
- **K80. Not read by the safety net:** these spellings and pieces of a known secret pass as written.
  - A piece shorter than 4 characters, a piece one character away from a placeholder, and a piece from the middle of a value between two placeholders.
  - The same value in other capital or small letters (K4).
  - Text encodings the decoder does not undo: UTF-7, quoted-printable, hex or ROT13 dumps, reversed text, look-alike letters that the standard folding keeps, and a secret wrapped across lines.
  - A copy in several stacked escape layers that crosses a window edge of a text over 65,536 characters.
  - Example: with known `abcdefghijkl` and two placeholders, a text that keeps `defghi` between them is sent.
  - The rest of a held-back identifier passes too, because the safety net checks secrets only (K5).
  - Not a limit any more: a known secret made only of punctuation (`!!!!!!!!`). A piece of 4 or more of its characters that starts or ends it beside a placeholder is now read and refuses the call (MEASURED here: `!!!!<HOST_1>` and `<HOST_1>!!!!` are refused). Separators that start a private key's header line stay exempt.
  - Not read as a piece, in any letter case: the public words that start an authorization value. They are `Bearer`, `Basic`, `Token`, `Digest`, `OAuth`, `ApiKey`, `Negotiate`, `NTLM`, `AWS4-HMAC-SHA256`, `Bot` and `Key`. The same word plus one more character of the secret is read.
  - Status: STATED (the gate's own code notes). Evidence: TESTED (the punctuation and word-list lines); UNVERIFIED (the rest, read in the code; one limit is pinned in K79). Who acts: nobody.
  - [INTERNAL] guard/model_gate.py:80-91 (the NOT read list and the G13c wording); runmap.py:1354-1358 (`_LEAD`, `_SEPARATORS`), :1373-1400 (`_piece_index`: values of only separators in their own lists), :1503-1514 (`held_in_views` stacked-layer limit, "Not pinned"), :1537-1554 (VIEW_WINDOW 65,536, WINDOW_OVERLAP_MAX 16,384); `NET_MIN_PIECE = 4` runmap.py:1350. Tests E::test_g13c_4_a_piece_of_a_value_of_only_separators_is_a_piece (tests/test_runmap_enforce_map.py:1128), E::test_g13c_5_the_public_auth_words_are_exempt_in_any_case_and_one_secret_character_is_not (:1156); mutants E19t, E19u, E19zc, E19zd (tests/gate_mutants.py:522-565), not run whole here. Probe (Python 3.13.18, `runmap.held_value_left`, 2552bcc95): `!!!!!!!!` with `!!!!<HOST_1>`, `<HOST_1>!!!!` -> True; `Bearer abcdef123456` with `bearer <HOST_1>` -> False and with `bearer a<HOST_1>` -> True. The middle-piece example is the G13 design review's (tickets/G13-result-review-1-design.md "Blind spots": `abc<K>defghi<K>jkl`); not run here (my probe of a middle piece, `<HOST_1>ABCDEFGH` for `hunter2-ABCDEFGH-ZZ`, returned False). LEAD DECISION G13 D5 (middle pieces).
- **K85. Refused more than needed:** the safety net can refuse ordinary text beside a placeholder. One planted value can make every later call of a run refuse.
  - Example: a known secret `the quick brown fox` makes the text `the <HOST_1>` look like a leak (MEASURED here: the net answers "leak"). The gate reports that as the code `held_value_left`, the same code as a real leak. The message stays in the run's history, so each later call refuses.
  - TESTED: the refusal is pinned as it is. A strict expected failure records the wanted behaviour (ordinary words beside a placeholder sent). The letter-only minimum and a refusal code of its own are not built.
  - TESTED: a bare web address start (`https://`) beside a placeholder is not read as a piece. So are the public authorization words, in any letter case (K80).
  - TESTED: one key of the map reads at most 4,096 hits of its first characters (both sides together). A dense hostile text is refused with `mask_budget_exceeded` after about 4,096 lookups, in 0.02 s. The shape: a value `aaaa` followed by 16,380 `c`, beside eight runs of 16,000 `a` and a placeholder. Before, it was accepted after about 16,000 lookups per key and 0.54 s (MEASURED by the builder). The refusal stays while the text is in the run's history. On 1,978 ordinary inputs the cap was never reached (builder's measurement).
  - TESTED and MEASURED by the builder: the lookups no longer cut a slice before the first-characters test. A 65,536-character value beside 16 placeholders took 1.74 s before and 0.13 s after.
  - TESTED and MEASURED by the builder: long pieces already looked up are kept as a 16-byte digest. The peak memory of the builder's worst shape was 367 MB before and 7.1 MB after.
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The letter-only minimum and a refusal code of its own are decisions the lead has not made (OPEN); the cap of 4,096 is the builder's number.
  - [INTERNAL] runmap.py:1354-1360 (`_LEAD` case-insensitive, `_SEPARATORS`, `_KEY_HITS_MAX = 4096`), :1403-1411 (the digest of a long piece), :1414-1500 (`_touching_piece`: head test before the slice; the cap at :1461 and :1487); guard/model_gate.py:67-91 (docstring: permanent refusal, the cap, the word list). Tests E::test_g13c_1 to _6b (tests/test_runmap_enforce_map.py:1079-1190), T::test_g13c_3_a_dense_head_beside_a_key_is_refused_as_mask_budget_exceeded (tests/test_model_gate.py:3064), T::test_g13b_1_a_url_scheme_beside_a_key_is_sent_while_a_webhook_value_is_in_the_map, E::test_g13b_1_the_public_start_of_a_value_and_separators_are_not_a_piece; mutants E19t to E19ze (tests/gate_mutants.py:522-568). Evidence: evidence/G13c-build-notes.md (all figures above; no pass count for the new tests is written in it: UNVERIFIED that they ran in a recorded batch other than the later board batch). Findings answered: tickets/G13-result-review-2-design.md M-A, M-B, m1, m2, budget. Probe (Python 3.13.18, `runmap.held_value_left`): `the quick brown fox` with `the <HOST_1>` -> True; the dense shape -> `InputTooLarge`. LEAD DECISION (G13 round 2): the letter-only prefix rule and a separate refusal code (not built).

### 2.2 Spending cap

Shown by tests (the gate's tests in the batches named in 2.0):

- TESTED: the gate makes no model call without a reservation. Order: mask, reserve, call, settle, write the audit row.
- TESTED: when a reply arrives with a usable cost, the gate settles that real cost.
- TESTED: when the model connector marks an error "refused before any answer", the gate settles 0.00 USD. This holds also for a call whose retries ran out, if every attempt carries that mark.
- NOT RUN: any test of the store's cap on this branch. The store code those tests check is not here, so they skip.
- [INTERNAL] Gate tests: T::test_pin_no_client_call_without_a_reservation; T::test_t1_pass_path_order_is_enforce_reserve_call_settle_audit; T::test_pin_a_marked_exhausted_is_settled_at_zero_with_the_refused_code (tests/test_model_gate.py:1421); `refused_before_response` guard/model_gate.py:340-358. Store tests skip: tests/contracts/test_t1_reserve_cap.py skips when `Store.reserve_spend` is missing; `grep -rn reserve_spend src` is empty; src/hadavin_sdk/store/migrations ends at 0005_evidence.sql. The PostgreSQL 17 run of laptop JOB 1 (inputs/evidence-cfull.md run c) reports 19 skips "Store.reserve_spend missing".

Known gaps:

- **K20. Not released:** the worst case of a failed call. The gate settles 0.00 USD only for an error the model connector marks "refused before any answer". No connector sets that mark yet, so every failed call keeps its worst case booked.
  - Example: a throttled call fails before any answer. With no mark, its worst case stays booked.
  - What the store keeps booked after that is the store's behaviour, and its code is not on this branch.
  - The gate cannot check the mark. A connector must set it only when no attempt may have been billed.
  - Status: WAITING. Evidence: TESTED (an unmarked failure is not settled; a marked one is settled at 0.00 USD); UNVERIFIED (no connector sets the mark, read in the code). Who acts: the connector and store team (written request).
  - [INTERNAL] guard/model_gate.py:340-358 (docstring: "llm/retry.py sets no mark yet"), :683-690; `grep -rn refused_before_response src/hadavin_sdk/llm` is empty. Tests T::test_pin_an_unmarked_provider_error_is_not_settled (tests/test_model_gate.py:1267), T::test_pin_a_marked_exhausted_is_settled_at_zero_with_the_refused_code (:1421). requests/2-refused-before-response.md (with the 13:2xZ update). LEAD DECISION gate (c) contract (part 1b). evidence/GATE-C-build-notes.md.
- **K21. Booked as free:** a reply with an empty cost field. The connectors' reply form fills an empty cost with 0.00 USD, and the gate settles 0.00 USD.
  - Example: a connector forgets to fill in the cost; a 0.80 USD call is booked as 0.00 USD.
  - Status: WAITING. Evidence: TESTED (the gate's side). UNVERIFIED: that a connector leaves the field empty. Who acts: the connector and store team (written request).
  - [INTERNAL] T::test_m5_a_zero_cost_reply_is_settled_at_zero (tests/test_model_gate.py:1132); models.py:299 `cost_usd: Decimal = Decimal(0)`; requests/3 section 4.
- **K22. Not settled:** a reply with an unreadable cost. The worst case stays booked, not the real cost.
  - Example: a reply reports its cost as "not a number"; the full 1.00 USD stays booked.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] T::test_pin_a_reply_with_no_usable_cost_is_not_settled (tests/test_model_gate.py:1290); T::test_o17_2_...; model_gate.py:148-153, :392-399.
- **K23. Not counted:** earlier attempts of a call that succeeded after retries. Only the last attempt is settled.
  - Example: attempt 1 times out but was billed 0.40 USD; attempt 2 costs 0.30 USD; only 0.30 USD is booked.
  - Status: WAITING. Evidence: UNVERIFIED (read from the code). Who acts: the connector and store team (written order).
  - [INTERNAL] llm/retry.py:83-108 (`with_retry`); ORDER 017 item 3 (06:30 UTC); ESCALATIONS.md E6 item 3.
- **K24. The gate passes a higher real cost to settle:** a call that costs more than its worst case is passed to settle at the real cost, on purpose. How the store books it is the store's code, which is not on this branch.
  - Example: the gate side is TESTED. The store side is not shown on this branch.
  - Status: PINNED (the gate's side). Evidence: TESTED. Who acts: nobody (as built). How often this happens depends on the worst-case formula, which does not exist yet (K25).
  - [INTERNAL] T::test_a_settle_above_the_reservation_is_passed_through (tests/test_model_gate.py:283); `CODE_OVERSHOOT` model_gate.py:279, :715-716. Style review M9.
- **K25. Not written:** the worst-case formula for the gate. The gate takes the function from the installer. It must cover the system prompt, the messages, the tool schemas and the documents, and the attempts. No function in this tree does that.
  - Example: the one worst-case function in the tree prices only the system prompt and the messages, and only the replay command line uses it.
  - The gate accepts a worst case of 0.00 USD, so a faulty function could reserve nothing (UNVERIFIED, read in the code).
  - Status: WAITING. Evidence: UNVERIFIED (read from the code; nothing to test). Who acts: the connector and store team (written order).
  - [INTERNAL] guard/model_gate.py:224-226 (what the function must cover; it names `llm.common.worst_case_usd`, not in this tree), :380-389 (`usable_amount` accepts Decimal(0)), :645-646; k1b/loop.py:115 (`worst_case_usd(route, system, messages)`) and :170 (its only caller). ORDER 016c item 13. ESCALATIONS.md E18 nit 6 (refuse a zero worst case when anything is sent: a behaviour change, not built).
- **K26. Not enforced by the database:** the runtime login can rewrite the spend counters. On this branch it holds SELECT, INSERT and UPDATE on the tables `spend` and `spend_month`.
  - Example: faulty code could lower the booked amount.
  - Status: OPEN. Evidence: UNVERIFIED (read from the grant map; no database test was run here).
  - Who acts: the owner decides whether to tighten these rights. If no answer arrives by 2026-11-23 12:00 UTC, they are tightened. Then the connector and store team changes them.
  - [INTERNAL] src/hadavin_sdk/store/migrate.py:40 (`_RW = "SELECT, INSERT, UPDATE"`), :53-54. Decision 5 in part 1a.
- **K27. Not refused:** an out-of-date price table.
  - Example: a vendor raises prices; the worst case is computed at the old price.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.
  - [INTERNAL] inputs/plan-v4-final.md line 29.
- **K28. Not capped across processes:** the test and replay command lines keep their cap in memory, per process.
  - Example: two replay processes each spend up to the cap.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.
  - [INTERNAL] inputs/plan-v4-final.md line 29; refusal `usd_cap` (model_gate.py:303-312, ORDER 014).

### 2.3 Stop switch

Shown by tests:

- TESTED (the gate's tests): a refused reservation, including the stop switch's refusal, means no model call.
- UNVERIFIED: that the store refuses every reservation while the switch is on. This is in the connector and store team's code. No test of it ran on this branch.
- NOT RUN: any end-to-end stop of a live run.
- [INTERNAL] T::test_t12_a_spend_refusal_passes_unchanged_and_no_call_is_made[kill_switch].

Known gaps:

- **K29. Not narrowed by the database:** the runtime login can change the stop switch and sign a stop record with any name. On this branch it holds SELECT, INSERT and UPDATE on the table `kill_switch`, and the migrations add no trigger on it.
  - Example: a stop record says "by: operator" when the runtime wrote it. The runtime can also set the flag back to off.
  - Status: OPEN. Evidence: UNVERIFIED (read from the grant map and the migrations; no database test was run here).
  - Who acts: the owner decides whether to tighten these rights. If no answer arrives by 2026-11-23 12:00 UTC, they are tightened. Then the connector and store team changes them.
  - [INTERNAL] src/hadavin_sdk/store/migrate.py:55 (`kill_switch`), store/migrations/0001_core.sql:94; the triggers in the migrations cover only the audit tables (0002_audit_chain.sql:25-34). Decision 5 in part 1a.
- **K30. Not stopped:** a call already in flight, and the test and replay command lines (they do not read the switch).
  - Example: a 30-second call started before the stop still completes.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.
  - [INTERNAL] inputs/plan-v4-final.md line 30 (B3 "Stop").

### 2.4 Audit record

Shown by tests:

- TESTED (the gate's tests): the gate tries to write one audit row per call. The row holds the run, the type of action, who asked, the result, and a code from a fixed list.
- TESTED (the gate's tests): the gate's code holds no logging and no error text, and no audit row in those tests held a secret.
- TESTED (the gate's tests): if writing the row or settling fails with an ordinary error after the reply came back, the gate still returns the reply.
- [INTERNAL] T::test_pin_every_outcome_writes_exactly_one_audit_row; T::test_i9_the_module_has_no_logger_no_exception_text_and_no_module_state; T::test_t18_no_secret_in_any_audit_row_exception_or_log_record; T::test_t17_a_raising_audit_sink_never_loses_the_reply_or_the_settle; T::test_m2_settle_raising_after_a_paid_call_returns_the_reply_and_the_row_says_ok. `AUDIT_CODES` model_gate.py:315-337.

Known gaps:

- **K31. Not recorded:** whether anything was masked, and the route.
  - Example: an investigator cannot tell from the row whether a secret was masked.
  - Status: OPEN. Evidence: UNVERIFIED (read from the code: the row's map field covers map use only).
  - Who acts: the owner decides whether to add a "masked: yes or no" field and the route. If no answer arrives by 2026-11-23 12:00 UTC, both are added.
  - [INTERNAL] guard/model_gate.py:281-285 (the five `MODE_*` words; no masked flag, no route field). Decision 2 in part 1a.
- **K32. Not shown on this branch:** whether a login other than the runtime login can add audit rows. Such logins belong to the connector and store team's store code, which is not on this branch.
  - On this branch the audit tables are append-only for every login (UNVERIFIED, read from the migrations).
  - Status: OPEN. Evidence: UNVERIFIED. Who acts: the connector and store team, when its store code reaches this branch.
  - [INTERNAL] src/hadavin_sdk/store/migrate.py:41 (`_APPEND`), :42-45 (comment), :57-58 (`audit_entries`, `audit_checkpoints`); store/migrations/0002_audit_chain.sql:25-34. `grep -n reset src/hadavin_sdk/store/migrate.py` finds no reset login. ESCALATIONS.md E7 item 5 (a reset login on core-b's tree). Style review M16.
- **K33. Not in the record:** the test and replay command lines print their audit lines to the screen only.
  - Example: a replay leaves no row in the store.
  - Status: STATED (the project's written plan, frozen on 2026-11-20). Evidence: NONE. Who acts: nobody.
  - [INTERNAL] inputs/plan-v4-final.md line 32 (B3 "Audit").

### 2.5 The secret finder (what enters the run map)

Shown by tests (TESTED here means: in the batches named in 2.0; the tests added since passed in their builders' batches, named in 4.2):

- TESTED: it finds the kinds it knows: addresses, keys, tokens, e-mail, passwords in web addresses and command lines, and supplier payment details (a bank account beside its bank code).
- TESTED: it decodes base64 text and masks the whole base64 text when the decoded text holds a value it knows (K37).
- TESTED: one call runs up to 5 search rounds. A text still changing in the last round is refused whole (fail closed).
- TESTED: two values that overlap in the text are masked whole (K72).
- TESTED: a line it cannot mask in place is withheld.
- [INTERNAL] tests/test_redact_settle_loop.py, tests/test_redact_idempotent_property.py, tests/test_redact_context_after_sweep.py, tests/test_b64_scan.py, tests/test_p1c_gaps.py. The base64 view: runmap.py:554-955 (`_ScanBudget`, `_B64Unit`, `_b64_units`, `_b64_hits`, `_only_encoded`, `_pass_one`, `_scan`), redact.py:3027 (`place_encoded`).

Known gaps and fixed findings:

- **K34. Not found:** a secret in a shape the secret finder does not know.
  - Example: an unlabelled 40-character code in plain prose.
  - Status: STATED (the published README, section "Limits and trust", since 2026-11-04). Evidence: NONE. Who acts: nobody.
- **K35. Not masked:** a bare number with no label.
  - Example: `ref 55556666 paid` stays as written (MEASURED here). On the main line, 24 of 43 such test lines were not masked (MEASURED).
  - Status: STATED (an evidence file and a ticket of the text and masking team, 2026-11-20, call it accepted). Evidence: MEASURED. Who acts: nobody.
  - The written order those two files cite as the acceptance was not found. So that acceptance is UNVERIFIED.
  - [INTERNAL] Ticket G4 v2 section 6 cites "order 64 item 4"; ORDERS.md line 64 is ORDER 006 item 1. evidence/P1c-probe.md says "accepted property". Probe here: `ref 55556666 paid` unchanged.
- **K36. Fixed:** host names with no "host" word in front. A name under a private suffix is now masked whole. So is a label after the word `host` or `hostname` that ends in two digits or in a hyphen and a digit. The private suffixes are `.corp`, `.lan`, `.intranet`, `.intra`, `.localdomain`, `.home.arpa`, and `.internal` or `.local` when no label or call follows.
  - Example: `db01.corp.example` becomes `<HOSTNAME_1>` (before: `<HOSTNAME_1>.example`); `host db01 is down` becomes `host <HOSTNAME_1> is down`; `hostname=db01 state=down` becomes `hostname=<HOSTNAME_1> state=down` (MEASURED here).
  - On the main line, 28 of 44 test lines left a label of the name readable (MEASURED). On this branch 7 of the same 44 do (MEASURED here: the 44 lines through `redact_text`); 19 lines are pinned as closed.
  - Names that stay readable, each pinned by a test:
    - a name with a public-looking ending and no private suffix (`db01.acme.example`, `db01.acme.test`);
    - the short in-cluster forms (`billing.payments.svc`, `billing.payments.svc.cluster.local`);
    - a private word in the middle of a name (`db01.internal.acme.example`);
    - a cloud name that mixes an address and a name (`ip-10-0-3-22.eu-west-1.compute.internal` becomes `ip-<IPV4_1>.eu-west-1.compute.internal`).
  - A label after `host` with one trailing digit (`host web1 down`) also stays. A strict expected failure records it.
  - Masked more than before (as built):
    - a program package name that holds a private word (`com.acme.corp.billing.Service`) is masked whole;
    - a build triple after `host` (`host x86_64-w64-mingw32 build`) is masked;
    - a name glued after a non-Latin letter is masked from its first Latin letter, digit, `_` or `-`; up to two characters before it can go into the placeholder.
  - A list of CPU and platform names after `host` (`host x86_64`, `host arm64 runner`) is kept.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody. Whether to send clients a note on host names is OPEN (the owner decides).
  - [INTERNAL] guard/redact.py:195-225 (`_HOST_LABEL` .. `HOSTKEY`; the start look-behinds name ASCII label characters, `[A-Za-z0-9_-]`), :474-477 (the two patterns), :954 (`_KEPT_HOST`), :1831 (`_decide`). Tests tests/test_host_names.py (TB-4.1 to TB-4.13; `test_host_starts_after_a_non_ascii_word_character` is TB-4.13, :122; `test_limit_host_single_trailing_digit` :191, strict xfail L-H4); tests/test_p1c_gaps.py:46-52 (`HOST_CLOSED_IDS` = the 19 ids, `OPEN_ROWS` empty), :179 (`test_host_row`: the other 25 rows keep the base digests, which pins the readable names; L-H1 Java package over-mask, L-H2 `.svc` forms, L-H3 public-looking endings); tests/g8_cases.py `G4C_MERGED = True`. Builder batches: evidence/G4C-build-notes.md (2,992 passed, 6 xfailed in the p1d_a, p1c, host, property and base64 files; then 575 passed, 45 xfailed in the host, glued-rest and g3-port files; `python tests/b64_mutants.py` 58 of 58, which includes 14 host breaks; `python tests/g8_mutants.py` 43 of 43; `python tests/p1d_a_mutants.py` 50 of 51, A15 known equivalent). The STOP that kept it unmerged (evidence/G4-build-notes.md "STOP") was closed by the ASCII start look-behind. Probe (Python 3.13.18, 2552bcc95): the three examples above; the 7 readable rows are host-06, -08, -09, -10, -15, -16 and -42 of tests/p1c_cases.py (`host_kept_labels`). Not run: the full suite on the builder's branch, perf, the redact, gate and textnorm break files. Decision 3 in part 1a.
- **K37. Fixed:** base64 text under 40 characters was not masked. Now the secret finder decodes base64 text of 12 or more characters. It masks the whole text as `<ENCODED_n>` when the decoded text holds a value it knows.
  - Example: `secret is cGFzc3dvcmQ9aHVudGVyMnp6` (base64 of `password=hunter2zz`) becomes `secret is <ENCODED_1>` (MEASURED here).
  - On the main line, 41 of 41 such test lines leaked (MEASURED). The limits that stay are in K82.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] defaults.py:164-181 (B64_* limits); runmap.py:844-913 (`_pass_one`), :753-816 (`_b64_hits`), :833-842 (`_only_encoded`, the E22 shortcut); tests tests/test_p1c_gaps.py:80 (`test_base64_row`), :101 (`test_must_keep_b64`), tests/test_b64_scan.py (TB tests; TB-3.44 to TB-3.47 pin the shortcut and the unit cap). FAIL-BEFORE on the base: 76 strict xfails, the 57 base64 ids among them (evidence/G4-build-notes.md "Phase 0"). Reviews: tickets/G4-result-review-1-design.md and -1-codebase.md (no Blocker; their Majors fixed in fd1fb3e31). `python tests/b64_mutants.py` 44 base64 breaks of 44 at fd1fb3e31 (G4-build-notes.md "State at ca469a0bf"); 58 of 58 with the 14 host breaks on the builder's G4c branch (G4C-build-notes.md). Probe here: output as quoted; the map also holds `<SECRET_1>` = `hunter2zz`.
- **K38. Fixed:** a letter or `_x` glued behind an IPv4 address, a UUID, a phone number written with `+` or an IBAN beside `_` kept it unmasked. Now each is masked, and the glued text stays outside the placeholder.
  - Example: `10.20.30.40_x` now becomes `<IPV4_1>_x` (MEASURED here). An IBAN with `_x` glued behind it becomes `<IBAN_1>_x`. Shapes that are still not masked are in K70 and K71.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] guard/redact.py:91-97 (`_IBAN_START`, `_IBAN_END`), module docstring :25-33 [re-check]. tests/test_redact_glued_rest.py; evidence/G8-build-notes.md:38. Reviews: tickets/G8-result-review-1-*.md, G8-result-review-2-codebase.md (no Blocker, no Major).
- **K39. Not proven:** that the repeated search finds every value. Each call repeats the patterns and the masking until a round changes no text. A call that still changes a text in the fourth repeat round (round 5 of the call) is refused.
  - Example: planted text glues a bank code to a secret, then puts the account after that code elsewhere. This needed a third round and is masked.
  - Status: OPEN. Evidence: TESTED (the chain; the loop to a fixed point). Who acts: the text and masking team.
  - [INTERNAL] guard/redact.py:1351-1431 (`settle`; `RedactionError("NotSettled")` at :1431), :2792 (`_SETTLE_ROUNDS = 4`). Tests tests/test_redact_settle_loop.py; tests/test_redact_idempotent_property.py:205 (`test_one_pass_is_a_fixed_point_and_leaves_no_raw_copy`). Style review M12.
- **K40. Fixed:** the last part, up to 7 characters, of a longer token stayed readable in its other copies. This happened when the token was found only after a shorter known secret inside it.
  - Example: `password=ab9x`, then `Bearer ab9xqrstu`. The line `note ab9xqrstuvw end` used to show `note <SECRET_1>qrstuvw end`. It now shows `note <BEARER_1>vw end` (MEASURED here).
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody. See K68.
  - [INTERNAL] tail tests in tests/test_redact_settle_loop.py. The fail-before count "20 of 28" is withdrawn (evidence/G7-1.md:290).
- **K41. Not fully limited:** how long one call of the secret finder takes. Its time budget is 6 seconds of processor time per call. It is read before each search round and inside each masking step, the finder build and the written-forms scan.
  - The budget is not read inside one pattern pass over one text, nor in the loop over the texts of one round.
  - The secret finder has no wall-clock limit. A caller that needs one must add it.
  - Example (MEASURED, processor time, on the test machine): the text `curl -u ` repeated up to the size cap took 4.5 to 5.4 seconds against the 6.0-second budget.
  - A machine 12 to 33 percent slower than the test machine refuses that text (worked out from those runs, not run). A real document of that shape is then lost.
  - Status: OPEN. Evidence: MEASURED. Who acts: the text and masking team.
  - [INTERNAL] guard/redact.py:1351-1431 (`settle`), :1471-1477 (`_over_budget`); defaults.py:66-101 (the checks, the figures at :38-44: 4.51 to 5.36 s; "only the CPU clock ... a caller that needs a wall-clock bound ... must add its own guard" at :90-94), :102. 6.0 / 5.36 = 1.12 and 6.0 / 4.51 = 1.33. Style review M14.
- **K42. Not masked later:** a secret first seen in a tool's error message. It does not enter the run map.
  - Example: a tool fails with "bad password hunter2zz"; later results show `hunter2zz`.
  - Status: WAITING. Evidence: UNVERIFIED (read in the code: the error text is masked with a throw-away map). Who acts: the connector and store team (written request).
  - [INTERNAL] src/hadavin_sdk/tools.py:1009 (`runmap.redact_bounded(message, {}, ...)` inside `error_reason`, :987); requests/4-error-reason-run-map.md.
- **K43. Not masked:** a secret spelled like the secret finder's own placeholders. Four shapes stay as typed and get no map entry.
  - A value made only of escaped secret placeholders (`‹SECRET_1›`, with angle quotes), alone or in a run.
  - A value made only of typed secret placeholders (`<SECRET_1> <SECRET_2>`).
  - A value made only of typed placeholders of any kind (`password=<EMAIL_1> <IPV4_1>`).
  - The cut-off start of a secret placeholder, from `<S` to `<SECRET_12`, alone or after such a run.
  - Example: `password=‹SECRET_1›` stays as written, on purpose. A tool's error text is read twice, and the first read wrote that placeholder. A real password `<S` or `<SEC` stays readable (MEASURED here).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] guard/redact.py at 2552bcc95: :1036-1060 (comment, `_OWN_TOKEN` :1054, `_OWN_OUTPUT` :1055-1057), `_decide` :1822-1853 (genuine placeholders of any kind, and the `_OWN_OUTPUT.fullmatch` at :1853). Tests tests/test_redact_own_output_hardening.py:86 (`test_legitimate_own_output_is_left_alone`), tests/test_redact_context_after_sweep.py:498 (`..._a_stated_limit`). Record: tickets/E9-result-review-3-codebase.md.
- **K44. Fixed:** a secret wrapped in look-alike angle quotes was left readable.
  - Example: `password=‹hunter2zz_1›` is now masked (MEASURED here).
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] tests/test_redact_own_output_hardening.py:46 (`test_a_secret_wrapped_in_lookalike_brackets_is_masked`).
- **K45. Fixed for the one place found:** the secret finder, run again on its own output, turned real placeholders into new secrets. The place was the tool-error path.
  - Example: a tool error quoting `<SECRET_1>` no longer adds a new map entry.
  - Status: FIXED. Evidence: TESTED (that place). UNVERIFIED: that no other place does this. Who acts: nobody.
  - [INTERNAL] tests/test_redact_own_output.py:51 (`test_the_tool_error_path_adds_no_map_entry_and_keeps_the_escaped_text`).
- **K46. Not masked whole:** a secret that holds a space or `;`. It is masked only up to that character.
  - Example: `password=my secret phrase` shows `password=<SECRET_1> secret phrase` (MEASURED here). A quoted value with spaces is masked whole.
  - A comma or `&` inside a value does not end it; then the plain copy can stay readable (K84).
  - Status: STATED (the published SECURITY.md on the main line, since 2026-11-04). Evidence: MEASURED (here). Who acts: nobody.
  - [INTERNAL] Probe: `password="my secret phrase"` -> masked whole; `password=my secret phrase` -> `password=<SECRET_1> secret phrase`; `password=abc;def123 then def123` -> `password=<SECRET_1>;def123 then def123`. The published text ("a space, `;`, `,` or `&`") does not hold for `,` and `&` in the key=value form on this code.
- **K68. Fixed:** after the secret finder undid a half-made entry, an old record could survive, so a later placeholder with the same number could be restored to the wrong value.
  - The text stayed masked; nothing raw went to the model. A tool could have got the wrong account or credential.
  - Example: a token found and then undone left a record for `<BEARER_1>`. A new `<BEARER_1>` for another value was later restored as the old one.
  - Status: FIXED. Evidence: TESTED (two rollback cases). Who acts: nobody.
  - [INTERNAL] guard/redact.py:1778 (`_rollback`), :1956 (`_unspell`). Tests tests/test_redact_settle_loop.py:250 (`test_a_rolled_back_compound_entry_leaves_no_ghost_spelling`), :261 (`test_a_number_reissued_after_a_rollback_does_not_revive_the_ghost_spelling`). Style review M5.
- **K70. Not masked, as built:** glued shapes the glued-text change leaves readable.
  - A phone number or card number written as one run of digits with a letter right before or after it (`x4155550132`, `telephone4155550132`, `x4242424242424242`).
  - A phone number without `+` with a letter after it (`415-555-0132x123`).
  - A phone number directly before a full stop that a letter, digit or `_` follows (`call 415-555-0132.Thanks`, `call +1 415-555-0142.x`).
  - An IBAN with a letter or digit glued before it, or written inside a file name, a path or an identifier (`acct_iban_DE89...`, `xDE89...`).
  - A US Social Security number with a letter glued to it. A host name with a letter, digit or `_` after its private suffix.
  - Example: `x4155550132` and `acct_iban_DE89370400440532013000` go out as written (MEASURED here).
  - Masked more than before (as built): a number of 10 to 16 digits before a full stop and a space is now masked as a phone number (`ref 1234567890. Next`). Later copies of it glued to a dot are then masked too (`1234567890.tar`).
  - A card number written as one run beside `_` (`card_4242424242424242`) is masked as a phone number and kept in the run's map as one.
  - A phone number with a country code and spaced groups before a full stop and a letter or digit is masked only in part: `call +44 20 7946 0958.Thanks` becomes `call <PHONE_1> 0958.Thanks`, and `call 0044 20 5550 1234.5` becomes `call <PHONE_1> 1234.5` (MEASURED here). A strict expected failure pins each (the earlier code did the same).
  - Masked more than before (as built): `tok 4155550132.-Ab9 x` becomes `tok <PHONE_1>.-Ab9 x` (MEASURED here); the earlier code left it. A test pins this output and a strict expected failure records the wanted one.
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The defaults are as built; the lead has not decided them in writing.
  - [INTERNAL] LEAD DECISION L-D13 (built: all four PHONE patterns end `(?!\w|\.\w)`, redact.py:557-590), L-D15 (default: the short-word rule), L-D17 (default: no card check). Options in part 1b.
  - [INTERNAL] Tests tests/test_redact_glued_rest.py:106 (`test_limit_rows_are_pinned`), :139 (`test_phone_before_a_full_stop_is_masked`, F1-F6); rows tests/g8_cases.py:527 (FULL_STOP), :476-481 (KEEP rows "K85" to "K90": a separate numbering of the G8 test file, not these K numbers). evidence/F3-build-notes.md; review tickets/G7F3-result-review-1-design.md (1 Major, fixed; N1 the follow-on sweep of dotted copies, N2 `.word` partial mask). Probe here: `call 415-555-0132.` -> `call <PHONE_1>.`; `call +44 20 5550 1234.` -> `call <PHONE_1>.`; `call 415-555-0132.Thanks` and `call +1 415-555-0142.x` unchanged; `ref 1234567890. Next and 1234567890.tar` -> `ref <PHONE_1>. Next and <PHONE_1>.tar`; `1732095071.123` unchanged; `x4155550132`, `telephone4155550132`, `x4242424242424242`, `acct_iban_DE89370400440532013000`, `xDE89370400440532013000` unchanged; `card_4242424242424242` -> `card_<PHONE_1>`. Style review M11. Rows 102 and 103 (`+44` and `0044` shapes) and K91 to K93 (the dotted tokens) of tests/g8_cases.py, evidence/G8T-build-notes.md (G8 file 483 passed, 46 xfailed; `python tests/g8_mutants.py` 43 of 43 good). Probe here (Python 3.13.18, 2552bcc95): the three outputs quoted above.
- **K71. Readable remainder of a long token:** a UUID or a number of 10 or 11 digits is cut out of a long token. It must be set off by `_` or a letter. The rest of the token stays readable when it is under 40 characters. Before the change, the whole token was masked as one value.
  - Example (MEASURED here): `tok_<uuid>_` followed by 32 characters becomes `tok_<UUID_1>_` and the same 32 characters, readable. A remainder of 40 characters or more is masked too.
  - A letter does the same: `tok_<uuid>x` followed by the same 32 characters becomes `tok_<UUID_1>x` and the 32 characters (MEASURED here).
  - A remainder can be up to 39 characters; the measured rows hold 20, 30 and 32.
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. This is the limit as built. A change that keeps the token whole is planned and not built.
  - [INTERNAL] LEAD DECISION E16 (default: accept the limit; alternative: ticket tickets/G11-opaque-token-postpass.md, written, builder starts only on the lead's word).
  - [INTERNAL] tests/g8_cases.py:255 (`OPAQUE_LIMITS` OL1-OL7: 7 rows, 6 strict xfails), tests/test_redact_glued_rest.py:267; guard/redact.py:29-31 [re-check] (limit L15). Probe here: `tok_123e4567-e89b-12d3-a456-426614174000_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef` -> `tok_<UUID_1>_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef`; `tok_4155550132_` + 32 -> `tok_<PHONE_1>_` + 32. Style review M20.
- **K72. Fixed:** two overlapping values left a readable part of a value the map holds. One case was a written form completed only in a later round. The other was two values that overlap as raw text.
  - Example: plain values `abcdefgh` and `efghijkl` in `abcdefghijkl` used to become `<S1>ijkl`. Both are now masked whole, in either order.
  - A secret that overlaps a value held as another kind now gets a secret entry of its own, and a standalone copy of it is masked as a secret. Before, it reused the other kind's placeholder. Two secrets, or two identifiers, still reuse the held placeholder.
  - The work of the overlap check is counted as it is found, every 256 occurrences. It is no longer counted after the list of occurrences exists, so a hostile text is refused before it uses the memory.
  - The read-back at an edge is made once per edge and rule. Each further place of the same anchor costs a 32nd of a comparison.
  - Limits that stay, each a refusal of the whole call (K73): a sweep still changing after 4 passes, and more than 1,000,000 characters of overlap unions in one call.
  - A long known value written beside its own repeating pattern can need too much work and is refused. MEASURED by the builder: a value `ab` repeated 2,000 times (4,000 characters) beside its own period in a 12,002-character text is accepted (1.94 million units). A periodic value of up to about 7,000 characters is accepted. One of 8,000 or more is refused (4.50 million units; the limit is 4 million). A test pins the numbers.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] guard/redact.py:2158 (`_read_back`), :2271-2326 (`_overlaps`: `_OCC_CHARGE_EVERY` charge), :2364-2440 (`_deep_hits`: one read-back per (edge, rule), `_COMPARE_SHARE` :2795), :2594-2610 (`_place_union`, `_union_upgraded` :1326, :2573-2576), :2728; defaults.py:129-150 (the stated limit of the anchored check, the clocks, the order of the caps), :152-163 (SPELLED_MAX_PASSES 4, SPELLED_READBACK_REACH 1024, SPELLED_MAX_UNION_CHARS 1,000,000). Tests tests/test_redact_settle_loop.py:1821 (`test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole`), :1837 (`test_g9_two_overlapping_values_in_raw_text_are_masked_whole`), :1932 (`test_g9_a_secret_union_never_takes_a_restorable_placeholder_of_its_value`), :2375, :2394, :2407, :2426, :2436 (the five `test_g9b_...` tests: charge as found, the remainder, the 200-secret chain (perf-marked), the 12,000-character acceptance, the numbers). Builder batches: evidence/G9-build-notes.md (phase 1: 3929 passed; E17 fix: 3928 passed, redact mutants 117 of 117), evidence/G9b-build-notes.md (2,498 passed in ten files; `python tests/redact_mutants.py` 130 of 130 good after the fix, 7 mutants added: G9-31 to G9-37). Reconciliation: redact_mutants 123 of 123 (STATUS-BOARD 14:07Z; evidence/REC-notes.md). Reviews: tickets/G9-result-review-1-design.md, -1-codebase.md (no Blocker; Majors fixed in 27149e0de); tickets/G9-result-review-2-design.md (M1, M2, M3, N1 to N4: answered by G9b; no review of G9b is on file). ESCALATIONS.md E10, E17 (cap-sized periodic shape: 54.5 percent of the limit, linear), E23 (the file still says OPEN: UNVERIFIED that the lead closed it). Not run by the builder: test_redact_fold_budget.py, test_redact_glued_rest.py, the whole suite, the E22 perf failure. The unit weights were not re-calibrated against the review's microsecond claim (evidence/G9b-build-notes.md). LEAD DECISIONS G9 L-D1, L-D6', L-D7, L-D3b and E17.
- **K73. Refused, not read:** a hostile text can make the secret finder refuse a whole document. The refusals fail closed: nothing is shown, and a real document in the same text is lost.
  - The refusal words are `InputTooLarge` (the time or size limit) and `NotSettled` (a text still changing in the last round).
  - `SpelledWorkTooMuch` is used past 4,000,000 units of work in one masking step. `SpelledMemoryTooMuch` is used past 1,000,000 characters of written forms in one call.
  - `SpelledNotSettled` and `SpelledUnionTooMuch` come from the overlap step (K72). `FinderMemoryTooMuch` comes from the memory cap (K74).
  - Example (MEASURED): a text of 2,800 written forms in 213,000 characters, then 262,000 characters of copies, needs 6.3 million units. It is refused after 0.49 seconds of processor time.
  - Example (MEASURED by the builder): a text that names one known value of 4,900 characters 1,800 times is masked; 1,900 times is refused.
  - All clocks of these limits read the processor time of the thread (`time.thread_time()`). The "10 seconds" in an older note of the overlap work is a wall-clock figure of one measuring run on a loaded machine, not a limit.
  - Status: STATED (written in the code's own notes). Evidence: MEASURED. Who acts: nobody.
  - [INTERNAL] guard/redact.py:1431 (`NotSettled`), :1477 (`InputTooLarge`), :1933 (`SpelledMemoryTooMuch`), :2592 (`SpelledWorkTooMuch`), :2612 (`SpelledUnionTooMuch`), :2728 (`SpelledNotSettled`), :2836 (`FinderMemoryTooMuch`); defaults.py:103-163 (the 0.49 s figure at :121-123; "FORCE A REFUSAL" at :125-126). evidence/G7-1.md "G7 fix round 6" and "round 7"; evidence/G9-build-notes.md:15 (1,800 / 1,900 mentions; the total work is the same after G9b, which only moves the charge earlier: evidence/G9b-build-notes.md). defaults.py:129-150 (G9b wording: CPU clocks, the order of the caps). The base64 view also refuses a call past 2,000 decodable units or 262,144 decoded characters (defaults.py:174-177).
- **K74. Fixed:** the memory the secret finder held for very large plain values had no limit. Eight values of 260,000 characters in one call peaked at 956 MB.
  - Now one build of the finder is refused past 786,432 entries of its search tree (about 360 MB, worked out from measured rates). The refusal word is `FinderMemoryTooMuch`.
  - A run whose map holds more than 524,288 characters of values stops and asks for a person.
  - TESTED: the eight-value shape above is now refused.
  - Not bounded: the pattern passes before the build, finders kept from earlier builds, and the extra spellings of values that are not plain ASCII.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody. The two limits are the plan's defaults; the lead has not approved them.
  - [INTERNAL] defaults.py:48-61 (MAX_MAP_CHARS 524,288; MAX_FINDER_CHARS 786,432; "about 360 MB and 2 s"; the measured rates at :49), redact.py:2654 (comment), :2826-2836 (`_trie(limit)`); runtime/agent_loop.py:98-100 (`_map_chars`), :433-439, :556-562; config.py:250. Tests tests/test_redact_finder_cap.py (T1-T12; T10 `test_t10_e14_shape_is_refused` at :251 is perf-marked); evidence/E14-build-notes.md ("Not bounded (ticket section 11)"); reviews tickets/E14-result-review-1-design.md, -1-codebase.md (no Blocker, no Major); `e14_mutants.py` 10 of 10 (STATUS-BOARD 13:58Z). LEAD DECISION E14 (constants).
- **K75. Extra map entry, accepted:** a tool's error text read twice can make one extra map entry for each distinct token of another kind written after a key. The model sees a secret placeholder instead of the kind. Nothing real is stored in that entry.
  - Example: `password=‹EMAIL_1› host` becomes `password=<SECRET_1> host`, and `<SECRET_1>` stands for `‹EMAIL_1›` (MEASURED here).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The alternative (exempt the escaped tokens of other kinds on the tool-error path only) is not built.
  - [INTERNAL] LEAD DECISION E9 (default: option (a), as built; alternative: option (b)).
  - [INTERNAL] guard/redact.py:1045-1051 at fd1fb3e31 (the trade-off comment), `_decide` :1853; tests/test_redact_own_output_hardening.py:202, :229 ("makes_one_junk_entry"); evidence/E9-own-output.md.
- **K76. Accepted:** a placeholder written in a spelled form can come back from the secret finder decoded. Examples are `&lt;TENANT_1&gt;`, `%3CTENANT_1%3E` and `&#60;IPV4_1&#62;`. This happens when its digits are not masked.
  - No value stands behind such a placeholder: the run map has no such key, so a later restore gives nothing.
  - A probe found no case in which this returns a real value. That is a probe, not a proof.
  - Example: `&lt;TENANT_1&gt;` comes back as `<TENANT_1>`; `&lt;TENANT_4155550132&gt;` becomes `&lt;TENANT_<PHONE_1>&gt;` (MEASURED here).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] tests/test_runmap_e15_placeholder_spellings.py (15 cases); ESCALATIONS.md E15 update. Style review M18.
- **K77. Fixed:** a password stored with punctuation, a wrapper or an escaped edge at its ends left its plain copy readable.
  - Example: `password=hunter22, hunter22` used to leave the second `hunter22` readable. It now becomes `password=<SECRET_1> <SECRET_2>` (MEASURED here).
  - The same holds for a leading bracket (`password=(hunter22), hunter22`) and a wrapper such as `**hunter22**`.
  - It also holds for an escaped or encoded edge: `%0A`, `%XX`, a backslash-u or backslash-x code, `&quot;`, `&#10;`, a tag such as `<br/>` or `</b>`, at the start or the end (`hunter22%0A then hunter22`, `<br/>hunter22 then hunter22`). At the end only, a cut-short form from a closed list (`<br`, `&quot`) is read too.
  - An all-capital value of the shape `ADMIN_1` or `DB_PASS_2` now gets its plain copy too (`password=ADMIN_1, ADMIN_1` becomes `password=<SECRET_1> <SECRET_2>`, MEASURED here). A value that holds one stray `‹` or `›` keeps its plain copy as well (`password=hunter22!› then hunter22`, MEASURED here).
  - One secret then has two placeholders. Both restore to their own text.
  - No plain copy is made when the value is a "no value" word with punctuation (`none!`).
  - No plain copy is made when its core is the text of a real placeholder. Example: `password=EMAIL_1, EMAIL_1 and a@example.com` masks the real address, and the typed `EMAIL_1` stays as written (a stated limit).
  - No plain copy is made when the value holds a look-alike placeholder token (`‹SECRET_1›`), or the edge cut removed both look-alike brackets of one.
  - No plain copy is made when the value is over 4,096 characters and the core differs from it by 16 characters or fewer. A long private key would otherwise take twice the memory.
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody. What stays readable is in K84.
  - [INTERNAL] guard/redact.py:966-991 (`_EDGE_FORM`, `_EDGE_OPEN`, `_EDGE_CLOSE`, `_bare`), :995-996 (`_CORE_BIG` 4096, `_CORE_DELTA` 16), :1014-1033 (`_placeholder_like`, `_LOOKALIKE`, `_LABEL_TEXT`), :1868-1918 (`_place`: the no-core conditions at :1897-1907; `_decide` exemption unchanged at :1822). Tests tests/test_redact_g12_trailing_punct.py (33 tests; G12-1 to G12-28: edge forms G12-23 :355, G12-24 :363, G12-27 closed list, large value G12-26 :376, one stray bracket G12-28 :406). Builders: evidence/G12-build-notes.md (G12 and G12b: 2,760 passed, 41 xfailed; G12c section: `python tests/g12_mutants.py` 35 of 35 good; measured delta on 2,185 rows: text byte-identical, rows with fewer masks 0; map entries 2,145 -> 2,141). Not run by the G12c builder: the perf tests, the whole suite, other break files (evidence/G12-build-notes.md "G12c"). Reviews: tickets/G12-result-review-1-design.md, tickets/G12-result-review-2-design.md (B1, M1 to M4: answered by G12c; no review of G12c is on file). Probe (Python 3.13.18, 2552bcc95): the examples quoted above; `password=hunter22%0A, hunter22` -> `password=<SECRET_1> <SECRET_3>`. The E18 G7-F4 probe was mis-built (ESCALATIONS.md "E18 correction"). Style review B1 (K77).
- **K81. Not masked by any step:** some text reaches the AI service on paths that skip the secret finder. The gate's safety net, where it runs, is the only check left.
  - The replay command line, when the operator states the stored cases are already masked: the cases go out as stored, and the gate has no map.
  - The replay loop's copy of the model's own tool call, and its alert time field, which is checked only as a timestamp.
  - An extraction function that sends the caller's document unmasked; no code calls it.
  - A demo that sends the question a user typed.
  - The check that every model-calling module is registered works per module, not per call (UNVERIFIED, read).
  - Status: OPEN. Evidence: UNVERIFIED (read in the code). Who acts: the connector and store team, once a decision on each path is written.
  - [INTERNAL] k1b/replay.py:119-123 (`--i-know-data-is-already-masked` when `k1b.redact` is false); k1b/loop.py:147 (`alert_time_text`), :211-212 (assistant echo `tool {call.name} {_dumps(call.input)}`), :214 (rendered result, masked at source only); extract.py:51 (`documents=[document]`), tests/test_gate_install_callers.py:46 (BYPASS: "no caller in src; F-install deletes it"); guard/producers.py:64, :70 (the demo, OUTSIDE_THE_CHOKE_POINT); tests/test_k5_producers.py:78-107 (module-level registration). Source: evidence/E19-M2-producers-table.md rows 8 to 13, 16. LEAD DECISIONS G13 D1 (replay NO_MAP), D2 (echo), D3 (extract.py); ESCALATIONS.md E19 "Lead decision for items 2 and 3". Style review B1 (unredacted paths).
- **K82. Not decoded by the base64 view:** these base64 texts stay readable even when they hold a secret.
  - A blob glued to other base64 characters, such as a path (`/v1/blob/` + the blob).
  - A blob split across fields, or wrapped with a log prefix on each line.
  - Hex, base32, base85, compressed data and quoted-printable text.
  - A decoded text in which 10 percent or more of the characters are not printable, such as a blob padded with blank-looking characters.
  - A blob of capital letters, digits and `_` written between angle brackets.
  - Base64 whose decoded text holds no shape the secret finder knows (`aHVudGVyMnp6IQ==`, MEASURED here).
  - Status: PINNED. Evidence: TESTED (strict expected failures for five of them); UNVERIFIED (the bracket and no-shape cases, read in the code). Who acts: nobody.
  - [INTERNAL] tests/test_b64_scan.py:978-1010 (strict xfails: L-B1 `test_limit_glued_prefix`, L-B4 `test_limit_split_fields`, L-B5 `test_limit_log_prefixed_lines`, L-B2 `test_limit_base32_hex`, L-B8 `test_limit_padded_blob`); L-B6 runmap.py:606 (`_B64_TOKEN_SKIP`), TB-3.3b; L-B3 (a direct `redact()` or `redact_many` call has no base64 step); L-B7 measured as no leak (test_b64_scan.py:1023). defaults.py:168-171 (B64_PRINTABLE_SHARE). Ticket tickets/G4-P1c-redactor-gaps-v8.md (L-B1 to L-B7). LEAD DECISION L-B8 (fallback measured, not built: evidence/G4-build-notes.md "State at ca469a0bf").
- **K84. Not masked:** the plain copy of a password stored with punctuation inside it, or with an escape that is not on the list.
  - Example: `password=hunter22,x and hunter22` leaves the second `hunter22` readable (MEASURED here). The same holds for `hunter22.x` and `hunter22&x=1`.
  - A double-encoded edge stays: `password=hunter22%250A then hunter22` leaves the second `hunter22` readable (MEASURED here).
  - Not done, from the builder's list (UNVERIFIED here, not run):
    - a named entity outside the list at the start of a value (`&copy;`);
    - a mixed-case cut-short entity (`&QUOT`);
    - a tag longer than 16 characters at an edge.
  - Closed since the last version (see K77): `%0A`, `&quot;` and `<br/>` at an edge, an all-capital value such as `ADMIN_1`, and a value with one stray `‹` or `›`. Still open by design of the fix: a password wrapped in a look-alike token (`‹SECRET_x›`) gets no second entry.
  - Status: OPEN. Evidence: MEASURED; UNVERIFIED (the not-done list). Who acts: the text and masking team; no fix for interior punctuation is built, and whether to accept it as a stated limit is the lead's to decide (OPEN).
  - [INTERNAL] guard/redact.py:966-991 (`_bare` strips only non-alphanumerics, the listed tags, escaped `\n` `\r` `\t`, `%XX`, `\uXXXX`, `\xXX`, `&#n;` and `&name;` at the ends), :1014-1033 (`_placeholder_like`), :1897-1907. Probes (Python 3.13.18, 2552bcc95; `runmap.redact_text`): `password=hunter22,x and hunter22` -> `password=<SECRET_1> and hunter22`; `password=hunter22.x and hunter22` and `password=hunter22&x=1 then hunter22` the same shape; `password=hunter22%250A then hunter22` -> `password=<SECRET_1> then hunter22`. evidence/G12-build-notes.md "G12c" (the NOT done list); tickets/G12-result-review-2-design.md M2, M3, M4; tickets/E9-result-review-3-codebase.md Major 1. Limit L-G12 (interior punctuation, a different value).

### 2.6 Text folding (look-alike and hidden characters)

Shown by tests (in the batches named in 2.0):

- TESTED: before the secret finder searches, it folds the text. Look-alike letters, invisible characters and accents become one plain spelling.
- Condition: the program runs on Python 3.13 (see README, section "Python version").
- [INTERNAL] tests/test_textnorm*.py, tests/test_redact_g3_port.py. M3 builder gate run: 1253 passed (evidence/M3-build-notes.md "Runs").

Known gaps and fixed findings:

- **K47. Fixed:** the secret finder's own look-alike search was missing from the shared branch. It is there now.
  - Example: `password=x` written with a Cyrillic "а" is now found.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] tests/test_redact_g3_port.py; merged in d95a727.
- **K48. Not decoded by folding:** escape codes; look-alikes added after Unicode edition 15.1; hidden marks outside two character blocks.
  - Example: the escape code `&#49;` (the code for the digit 1) is not read as `1`, so `abc&#49;` stays as written (MEASURED here).
  - Status: STATED (the text folding work's written limits, 2026-11-20). Evidence: UNVERIFIED (a reviewer's reading confirms the limits). Who acts: nobody.
  - [INTERNAL] tickets/G1-result-review-1.md line 17.
- **K49. Not flagged:** the Chinese character for zero (Unicode name IDEOGRAPHIC NUMBER ZERO, 〇) inside a Latin word.
  - Example: `pay` + 〇 + `al` is not called mixed script. MEASURED: it is the only such character in the folding table.
  - Status: PINNED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] tests/test_textnorm_mixed_script_micro.py:117 (`test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed`); evidence/TW-order020.md.
- **K50. Over-matching, measured:** the text-folding scan finds a known name inside a longer word or across a space. No masking path uses this scan yet (K83).
  - Example: known `mary` found in `summary`.
  - MEASURED on 2026-11-20 as hit rates per scan of one 10,000-character chunk of ordinary Latin text (repository prose and code, library docstrings, generated text). The values were drawn at random.
  - Hit rates of names: 4 letters 5.3 %; 5 letters 1.0 %; 6 letters 0.4 %; 8 letters or more 0.
  - Corpus words of 5 to 10 letters: 3.9 to 4.1 % in the two recorded runs.
  - ASCII ids of 4 to 5 characters 0.22 %; 6 digits 0.007 %.
  - The corpus-word draw is hash-seeded, so its figure moves between runs. A third figure of 4.5 % is in a review only (UNVERIFIED).
  - A value that is a whole word of the text counts as a hit. These rates are not a bound for tickets, e-mail, chat or real values.
  - Share of the hits that mask a fragment of a word: 94 % (4 letters), 63.4 % (5 letters), 99 % (ids), 9 % (6-letter names).
  - These shares are not false-hit rates.
  - Hit rates on real interface text: Russian values of 4 to 8 letters 7.6 %; Chinese values of 2 characters 5.2 %. Arabic and Devanagari: synthetic text only, unknown.
  - Status: STATED. Evidence: MEASURED. Who acts: nobody (the first user of this scan measures again).
  - [INTERNAL] evidence/G1-false-hits-and-cost.md:106-130 ("Round 2"; 5 letters 0.986 % and the share 63.4 % = 1244/1962 at :126; 3.914 % at :128); the 4.10 % row of the first round at :32; 4.46 % appears only in tickets/G10-review-2-design.md:6. defaults.py:313-320. `grep -rn scan_holds src` finds only guard/textnorm.py and comments in defaults.py. Style review M13; lead review N4.
- **K51. Limited by two time budgets:** the planted-instruction check stops at 30 seconds of processor time per check, or at 60 seconds of wall-clock time. It then flags the run as "guard unavailable" (fail closed).
  - The processor time is that of the thread that runs the check. The wall-clock limit is 2 times the processor budget.
  - From the second step of one check on, the processor time still needed may not pass half the wall-clock time left. This is stricter than 2 times: it can flag a check early, not late.
  - The real bound is the deadline plus the longest stretch between two readings of the clocks.
  - Example: a constructed text of 2,000,000 characters took 185 seconds of processor time without the budget and was flagged at 30.1 seconds with it. MEASURED on the build machine, before the wall-clock limit existed.
  - A machine about 1.9 times slower than the build machine would flag the slowest ordinary 2,000,000-character text measured (16.0 s) on every run (worked out, not run).
  - The work on a protected value inside one scan has no clock reading inside it (MEASURED: 7.2 to 7.5 s for a value of 236,879 distinct letters).
  - Status: PINNED. Evidence: TESTED; MEASURED. Who acts: nobody. The budgets and their scope (per check) are the defaults as built.
  - [INTERNAL] LEAD DECISION (G10 D1-D10 unapproved defaults, D4 = 30.0 CPU seconds per check; M3 factor 2.0 from the lead's "about 2x").
  - [INTERNAL] defaults.py:352-366 (`INJECTION_BUDGET_S = 30.0`, `INJECTION_WALL_FACTOR = 2.0`, the stricter rule at :362-363, the bound at :364); guard/injection.py:68-97 (`_deadline`, `_left`); guard/textnorm.py:414-416 (`DeadlinePassed`), :622-649 (`_deadline_of`, `_tick`). Tests tests/test_textnorm_deadline.py:287 (`test_the_injection_check_flags_a_run_past_its_budget`), :492, :502 (`test_the_injection_check_flags_a_wall_wait_and_hands_both_deadlines_to_the_fold`), :529. evidence/G10-build-notes.md, evidence/M3-build-notes.md; review tickets/M3-result-review-1-design.md (2 Majors fixed as statements; a one-line test of the stricter rule still wanted). The 185 s and 30.1 s figures: tickets/G10-textfold-deadline-v4.md section 12. Style review M14, M15.
- **K52. Refused, not read:** a long text in Chinese or Japanese only. It is reported as a guard failure.
  - Example (MEASURED): 300,000 characters of Chinese, and of Japanese, were refused. Russian prose of that size is read.
  - NOT RUN: a measure of the shortest length that is refused.
  - Status: STATED (written down by the text and masking team, 2026-11-20). Evidence: MEASURED. Who acts: nobody.
  - [INTERNAL] evidence/G1-fold.md "G1 fix round 1", M6.
- **K53. Chosen in a written order:** dashes and curly quotes are ordinary punctuation. Three slash look-alikes make the line withheld.
  - Example: a value right after an em dash (—) is masked in place.
  - A line holding DIVISION SLASH (∕), BOX DRAWINGS LIGHT DIAGONAL UPPER RIGHT TO LOWER LEFT (╱) or BIG SOLIDUS (⧸) plus a look-alike value is withheld.
  - This choice changed the class of 30 code points. They are 20 code points (dashes and the minus sign), 6 quotes and 3 slash look-alikes. The last is the replacement character U+FFFD, which the fold now drops.
  - Each of the 30 has a test and a deliberate code break that the tests catch.
  - Status: PINNED (chosen in the project's written order of 2026-11-20 06:15 UTC). Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] guard/redact.py:1155-1178 (`_TYPED_PUNCT`, `_char_class`); tests/redact_mutants.py (30 "Q9 U+XXXX" rows); evidence/G1-mutants-run.md:154-194 (30 KILLED; the split 20 + 6 + 3 + 1 at :229). Whole redact_mutants file: 123 of 123 on the reconciliation builder's tree (STATUS-BOARD 14:07Z), before the G12b fix of 9806830d0.
- **K54. Finds more than before:** an invisible character between a Latin letter and its accent.
  - Example: `e` + hidden mark + accent now matches `é`.
  - Status: PINNED (accepted in the project's written order of 2026-11-20 05:47 UTC). Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] tests/test_evidence_decomposed.py:157.
- **K55. Not decided:** the same wider matching in Korean, Japanese and Indian scripts, for the grounding check.
  - Example: a Korean name split by a hidden mark now counts as present.
  - Status: OPEN. Evidence: UNVERIFIED (a reviewer's reading).
  - Who acts: the owner decides whether to accept it. If no answer arrives by 2026-11-23 12:00 UTC, the older rule returns for those scripts. Then the text and masking team changes it.
  - [INTERNAL] Decision 4 in part 1a. G1 review M7.
- **K56. Fixed:** a secret stored as `Müller` but shown with a separate accent mark was not masked in tool output.
  - Example: `Mu` + combining accent + `ller` is masked again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] tests/test_undo_composes.py.
- **K57. Fixed:** look-alike padding before a 32,768-character boundary could hide a planted order from the planted-instruction check.
  - Example: "ignore previous instructions" split across that boundary is found again.
  - Status: FIXED. Evidence: TESTED. Who acts: nobody.
  - [INTERNAL] tests/test_injection_chunk_boundary.py.
- **K58. Fixed:** on the wrong Python, the connection to the secrets vault was built before the start-up refusal. The refusal now comes first.
  - Example: a pilot build on the wrong Python stops before it builds the connection to the secrets vault.
  - Status: FIXED. Evidence: TESTED (one test, on Python 3.13 with the version faked). Who acts: nobody.
  - NOT RUN: a check of other outside services.
  - [INTERNAL] tests/test_app_unicode_check_order.py:18; app.py:130-132.
- **K83. Not wired:** 14 public functions of text folding have no caller in the product. They are working code with tests and deliberate code breaks, kept in the security path.
  - Example: the name-matching scan of K50 is one of them; no masking or approval step calls it.
  - The module's own note now also names 8 other public names (`FILLERS`, `key_tag`, `FOLD_VERSION`, `squeeze`, `AllowVerdict`, `fold_views`, `squeeze_views`, `scan_keyset`) as internal helpers, reached only from inside the module.
  - Status: OPEN. Evidence: UNVERIFIED (read in the code). Who acts: the owner decides whether to move or delete them. Until then nothing moves.
  - [INTERNAL] guard/textnorm.py:20-30 (PRODUCTION CALLERS paragraph: `scan_holds`, `register_value`, `Coverage`, `scan_cache`, `scan_needles`, `identity_key`, `identity_keys`, `could_be_same_person`, `allow_equal`, `names_equal`, `has_mixed_script`, `has_hidden_channel`, `value_scripts`, `scan_views`). Owner item O-1 (ESCALATIONS.md E19, M4, "CODE-LAST rung"); requests/xr-textfold-lead-1.md M4. The M3 review (N6) noted 8 more public names in neither list; the tidy (TIDYT-build-notes.md, commit 2be75e38c) named them as internal helpers in the module docstring. Decision 8 in part 1a.

### 2.7 Approval messages

Shown by tests:

- TESTED (in a recorded batch on the branch where the change was built): the secret finder runs first on each free-text path found that writes an approval message.
- That batch ran before the change joined the shared branch.
- TESTED (same batch): web addresses are made unclickable last (a dot written as `[.]`).
- [INTERNAL] evidence/G2-p1d-a.md fix round batch: 7,879 passed, 0 failed (the builder's). tests/test_p1d_a_paths.py and tests/test_p1d_a_rows.py are in the whole-suite batch; PU1 card and model failed there and were re-pinned after it (54c461ff8; evidence/TIDYP-build-notes.md: the map now holds `ab&amp;`, `ab&amp`, `ab&`; nothing readable). `p1d_a_mutants.py` 50 of 51, A15 equivalent (TIDYP-build-notes.md).

Read, not tested:

- UNVERIFIED (read in the code; no recorded batch names its test): a message is re-read until it stops changing, at most 3 times. If it never settles, a fixed note is shown instead.
- Id fields are not masked (K59).

Known gaps and fixed findings:

- **K59. Not masked:** the "requested by" line and other id fields.
  - Example (UNVERIFIED: read from the code, not tried on Slack): a requester id `slack:U1|<!channel>` could make Slack notify everyone in the channel.
  - Status: WAITING. Evidence: UNVERIFIED. Who acts: the connector and store team (written request).
  - [INTERNAL] requests/5-card-ids-redact-defang.md.
- **K60. Not proven:** that no clickable link remains. The old test used the same patterns as the code it tested. A new test uses its own patterns and also checks against a link-finding library.
  - Example (UNVERIFIED): a link whose end is not in the test's own, finite list of web-address endings could still slip past both.
  - Status: OPEN. Evidence: TESTED (the independent test); UNVERIFIED (the missed link). Who acts: the text and masking team.
  - [INTERNAL] tests/test_p1d_link_oracle.py:218 (`test_oracle_agrees_with_linkify_it_py`); pyproject.toml:52-53 (linkify-it-py==2.0.3).
- **K61. Fixed:** an e-mail address with a digit or `_` glued behind it was shown whole.
  - Example: `anna.m@example.org9` becomes `<EMAIL_1>9` (MEASURED here).
  - Status: FIXED. Evidence: TESTED; MEASURED. Who acts: nobody.
  - [INTERNAL] tests/test_text_parts_together.py:213.
- **K62. Not checked:** approval summaries stored before these fixes, as shown on the admin page.
  - Example: a summary stored before the fixes could still show an e-mail address; nobody has looked.
  - Status: OPEN. Evidence: NOT RUN. Who acts: the text and masking team.

MEASURED slowdown of approval-message masking on the joined code (median, on the builder's test machine):

- a 174-character message took 0.00126 seconds before and 0.00360 seconds now;
- a 71,179-character message took 0.367 seconds before and 0.655 seconds now.
- [INTERNAL] defaults.py:100-101 ("a 174-character card 1.3 ms -> 3.6 ms ... a 71,179-character card 367 ms -> 655 ms"); evidence/G2-p1d-a.md.

### 2.8 Set-up

- **K63. Late failure:** the project file allows installing on Python 3.12. Once the text-folding change ships, by design a pilot or prod install there succeeds and the program refuses to start.
  - Example: an operator installs on 3.12; the program then refuses to start (see README, section "Python version").
  - Status: OPEN. Evidence: NOT RUN (no pilot start on 3.12 was tried). UNVERIFIED (read from the file): that the project file allows 3.12.
  - Who acts: the connector and store team.
  - [INTERNAL] pyproject.toml:8 (`requires-python = ">=3.12"`). No written request yet; core-c writes one if the lead agrees (4.5).

### 2.9 What was not run (NOT RUN)

- A batch of the whole test suite whose commit is named and is the code this file describes (2.0 has the batches that are on record).
- Python 3.12 on this code. The whole suite ran on Python 3.12 at an earlier commit.
- The store's tests on database version 17. The database test files ran on version 17 at an earlier commit, and the store's own tests skipped there.
- Any live call to an AI service. Any end-to-end stop of a live run. The gate installed at any call point.
- The long-token change (not built).
- The whole files of deliberate code breaks for text folding (268 breaks), the gate (140) and the finder (130) on this code. The files for the base64 and host-name change (58), the glued-text change (43) and the punctuation change (35) ran whole on their builders' branches before they merged.
- [INTERNAL] Python 3.12 and PostgreSQL 17: laptop JOB 1 at 9aeedc22f (inputs/evidence-cfull.md: run a py3.13 14,822 passed 8 failed; run b py3.12 14,823 passed 7 failed; run c PostgreSQL 17, 19 files + tests/contracts, 623 passed 341 skipped 0 failed). .github/workflows/ci.yml:41 (`postgres:17.10`).
- [INTERNAL] Code-break files at or near 2552bcc95: `b64_mutants.py` 58 of 58 on the G4c branch (G4C-build-notes.md; 44 of 44 at fd1fb3e31); `g12_mutants.py` 35 of 35 on the G12c branch (G12-build-notes.md); `redact_mutants.py` 130 of 130 on the G9b branch (G9b-build-notes.md; EXPECTED_COUNT 130 in tests/test_redact_mutants_meta.py:16); `g8_mutants.py` 43 of 43 (G4C and G8T notes); `textnorm_mutants.py` 268 entries (TIDYT-build-notes.md), the whole file not run since; `gate_mutants.py` 140 entries, four repaired in 252ef2881, whole file not run (GATE-C-build-notes.md says the runner stopped at its baseline on a base-commit test failure); older: `b64_mutants.py` 44 of 44 at fd1fb3e31 (G4-build-notes.md); `p1d_a_mutants.py` 50 of 51 (A15 equivalent) and gate R15 1 of 1 (TIDYP-build-notes.md); `e14_mutants.py` 10 of 10 (STATUS-BOARD 13:58Z); `redact_mutants.py` 123 of 123 before 9806830d0 (STATUS-BOARD 14:07Z); `textnorm_mutants.py` 263 entries, last whole run 256 of 256 before M3 (inputs/evidence-cmut.md); `gate_mutants.py` 128 entries, R8 survives as equivalent (E20), E19a-s by hand only; `g8_mutants.py` 43 entries, whole file NOT RUN on the merged tree (E20 update), G8-P15 killed alone (tickets/G7F3-result-review-1-design.md); `g12_mutants.py` 18 of 18 by the G12b builder (the two stale `old` texts that the round 2 review named were repaired in G12c).

---

## 3. For README.md: "Python version"

As of 2026-11-20 15:44 UTC (commit 2552bcc95).

[INTERNAL] This section describes the text folding change. As of 2026-11-20 it is on the shared branch only, not on the product's main line. Ship it with the release that contains that change.

Words used here: an operator is the person who installs and runs the kit (this software package) for a client. The stages are demo (made-up data), pilot (a first, limited use with a real client) and prod (normal live use).

Text folding turns look-alike letters, invisible characters and accents into one plain spelling before the kit searches text for secrets. Unicode is the world standard list of characters. Each Python version carries one edition of it.

The marks: NOT RUN means the check was not run. UNVERIFIED means someone read the code and nothing was run. TESTED means a named test passed in a recorded batch. MEASURED means a recorded run printed the figure given.

**Operators must run pilot and prod on Python 3.13.**

To check, run `python3 --version`, or use the Python you install the kit with. To see its Unicode edition, run `python3 -c "import unicodedata; print(unicodedata.unidata_version)"`. Pilot and prod need `15.1.0`.

Why: text folding uses the Unicode character data built into Python. The folding tables are built for edition 15.1.0, which Python 3.13 carries. MEASURED: Python 3.12 carries edition 15.0.0 (a test run on Python 3.12 printed it).

Pilot and prod on Python 3.12: NOT RUN (no pilot or prod start on Python 3.12 was tried). By design, the program refuses to start and prints the error UnidataMismatch. The fix is to install Python 3.13.

TESTED: one test on Python 3.13, with the version number faked, shows that refusal. In that test, the refusal comes before the program connects to the secrets vault (the place where secrets are kept). NOT RUN: a check of other outside services.

UNVERIFIED (read from the project file): the project file allows installing on 3.12. So the install succeeds, and the failure shows only when the program starts.

Demo on Python 3.12: by design, the program starts. Text folding gives each folded name a tag with the Unicode edition. So names folded on 3.12 and on 3.13 do not match. Do not compare results from the two versions. UNVERIFIED (read in the code): the tag rule.

Python 3.11 or older: UNVERIFIED (read from the project file): the install is refused, because the project file asks for 3.12 or later.

Python 3.14 or later: UNVERIFIED (read from the code): pilot and prod refuse to start on any Python whose Unicode edition is not 15.1.0. Do not run pilot or prod on Python 3.14 or later until the release notes say the character tables were rebuilt for it.

[INTERNAL] Proof for part 3. defaults.py:270 (`TEXTNORM_PINNED_UNIDATA = "15.1.0"`), :273 (`TEXTNORM_PINNED_PYTHON = "3.13"`); guard/textnorm.py:1758-1773 (`require_pinned_unidata`; the message names Python 3.13), :155 (the code's note that 3.12 carries Unicode 15.0.0), :1154-1160 and :477 (the key tag holds `ud=` and the Unicode edition); app.py:130-132 (the refusal comes before any backend is built); pyproject.toml:8 (`requires-python = ">=3.12"`). Python 3.12 carries 15.0.0: inputs/evidence-cfull.md run b failure 9 (`assert '15.0.0' >= '15.1.0'`), also ESCALATIONS.md E4 (Python 3.12.3, measured); the test was made version-aware in 266ae1977 and passed on a real 3.12 (STATUS-BOARD 13:57Z, "20 passed on py3.13 AND py3.12"). `python3 -c "import unicodedata; print(unicodedata.unidata_version)"` printed 15.1.0 on Python 3.13.18 in this pass. Style review M17.

---

## 4. Technical appendix (INTERNAL, does not ship)

As of commit 2552bcc95 (2026-11-20 15:44 UTC; repository head beb2b3ea6 at the time of writing, board and notes commits only after 2552bcc95). Internal references (codes, test names, files, orders, commits) appear only here and on `[INTERNAL]` lines. Team codes: core-b = the connector and store team; core-c = the text and masking team. "Probe" below means a direct call written for this pass: Python 3.13.18 (`/usr/local/bin/python3.13`), Unicode 15.1.0, `sys.path` = src of the docs worktree (src identical to 2552bcc95), scripts in the builder's scratch folder, not committed. Line references: moved from fd1fb3e31 to 2552bcc95 by a script that follows `git diff -U0 fd1fb3e31 HEAD` per file; `[re-check]` marks a reference inside a changed stretch; the entries rewritten in v8 (K36, K64, K70 to K73, K77, K80, K83 to K85) were read from the head.

### 4.1 Key to codes used in the sources

| code | meaning |
|---|---|
| cloud/core-c | the shared branch; code described: 2552bcc95 (last change to src and tests, 15:44 UTC). v7 described fd1fb3e31; `git diff --stat fd1fb3e31 HEAD -- src` shows 6 changed source files (approvals/gate.py (a comment), defaults.py, guard/model_gate.py, guard/redact.py, guard/runmap.py, guard/textnorm.py) |
| origin/main | the product's main line; none of this work is on it |
| F, G, B, T1 | work packages: F the gate; G the text work; B database rights; T1 the 50-connection cap test (core-b's store; skips here) |
| G1 / G2 / G3 | text folding / approval-message text (old branch P1d-a) / the look-alike search ported into the secret finder (old branch P2d-1) |
| G4 / G4c | base64 and host-name change (ticket v8). Phases 0-3 (the base64 view, kind ENCODED, limits L-B1 to L-B8) merged; Phase 4 and 5 (G4c, host names: `HOSTNAME` and `HOSTKEY` patterns) merged in 299bb3038 and ab8ee0440 after the STOP was closed by an ASCII start look-behind (evidence/G4C-build-notes.md); G4 tidy fd1fb3e31 (result review round 1 Majors). Host limits: L-H1 package names over-masked, L-H2 `.svc` forms, L-H3 public-looking endings, L-H4 one trailing digit |
| G4PERF / E22 | the `_only_encoded` shortcut in `_pass_one` (9b9ea8bbd): a perf ratio regression of G4 Phase 3 fixed; pinned by TB-3.44 to TB-3.47 |
| G7, G7-F3 | secret finder rounds (merged); G7-F3 = phone before a full stop (core-a cross review finding), built as G8 option B on all four PHONE entries (e3975b0e6, review fix d56eafa19) |
| G7-F4 / G12 / G12b / G12c | trailing punctuation of a SECRET value (G12, c3d51ac84); both ends and wrappers (G12b, 027bde9c5, 3409c5f80, ce56b3c9f; regression fix 9806830d0); G12c = round 2 review fixes (d6d545f6c, notes 3f3519ef1): placeholder-like core narrowed to real placeholder text, look-alike guard narrowed, edge forms `%XX` `\uXXXX` `&#n;` tags, no core for a large value |
| G8 | glued-rest change (merged; L-D13, L-D15, L-D17; limits L4 to L15) |
| G9 / G9b | spelled-form fixed point, E10 (9652b20aa, 67367e9fd; review fixes 27149e0de); closes E10 and the E19 M1 input. G9b = G9 result review 2 (E23): occurrences charged as found, a SECRET union registers its own entry, one read-back per edge, stated limits (1a0965361, fe2f1f9d2, notes 282d7d40f) |
| G10 / M3 / M4 | text-fold deadline (CPU, merged) / wall-clock deadline 2x (bb98410f7, review fix 34921b466) / textnorm docstrings and the unwired-API paragraph |
| G11 | ticket for E16 (opaque-token post-pass); written (tickets/G11-opaque-token-postpass.md), NOT built |
| G13 / G13b / G13c | gate net: piece beside a key and decoded views (bc6e2acd0, 97973ed29) / public-start exemption and window cap (3f467df1e, 1fba35a09) / round 2 review fixes (5d8c8ca04, notes 0a3f93a7e): head test before the slice, digest in `seen`, per-key cap `_KEY_HITS_MAX` 4096, separators-only values, auth words in any case. Merged |
| E14 | finder memory caps MAX_MAP_CHARS, MAX_FINDER_CHARS, `FinderMemoryTooMuch` (222b08d1f to 608be6874; tidy 82fb4bdc7) |
| gate (c) | the "refused before any answer" mark honoured on ProviderExhausted (5b371f6fb; review fix e05cee9f0) |
| TIDYP / REC / TIDYT | gate break R15 killer, p1d_a breaks A3d/A43, A15 equivalent, PU1 re-pin (efbc68675, 54c461ff8); REC re-pinned PU1 again from the measured output (5219a3320; evidence/REC-notes.md); TIDYT = the wall-clock deadline tidy (2be75e38c, d927df43d) |
| MIX / E20 | reconciliation of G9 + G4 + G8 (1bda9b7aa ...): TB-2.8, TB-2.11, TB-3.4 re-pinned; gate break R8 equivalent |
| E1 to E22, O-1 | entries in handover/core-c/ESCALATIONS.md; O-1 = owner item "move or delete the unwired textnorm DENY API" (E19) |
| L-D13, L-D15, L-D17 | G8 lead decisions (phone before a full stop; IBAN beside `_`; card number) |
| L-B1 to L-B8 | G4 base64-view limits: L-B1 glued prefix; L-B2 hex, base32, base85, gzip, quoted-printable; L-B3 no base64 step in a direct `redact()`; L-B4 split fields; L-B5 log-prefixed lines; L-B6 marker-shaped blobs; L-B7 JWT segment copy (measured: no leak); L-B8 decoded text under 90 percent printable |
| L-G12 | G12 limit: interior punctuation (a different value); the leading-bracket case L-G12a closed by G12b |
| L15 | G8 limit: a UUID or 10-11 digit number inside a long opaque token (E16) |
| ORDER nnn | orders from the lead in ORDERS.md |
| T:: / E:: | tests/test_model_gate.py / tests/test_runmap_enforce_map.py |
| sweep | the step that masks every copy of values already in the run map (the "masking step") |
| NO_MAP | the named constant for "no map" (model_gate.py:528-530) |
| strict xfail | strict expected failure |
| refusal words | gate: `mask_refused`, `mask_budget_exceeded`, `framing_refused`, `held_value_left`, `worst_case_failed`, `worst_case_invalid`, `reserve_refused`, `reservation_invalid` (`GateRefused` and subclasses, model_gate.py:256-279, :456-510); store reasons: `kill_switch`, `daily_budget`, `monthly_budget`, `limits_unavailable`, `bad_amount`, `usd_cap` (model_gate.py:304-313); finder: `InputTooLarge` with `SpelledWorkTooMuch`, `SpelledMemoryTooMuch`, `SpelledNotSettled`, `SpelledUnionTooMuch`, `FinderMemoryTooMuch`; `RedactionError("NotSettled")` |
| audit decision field | `map_enforced`, `map_enforced_empty`, `enforce_custom`, `map_failed`, `no_map` (model_gate.py:281-285); codes `call_interrupted`, `reserve_interrupted`, `held_value_left`, `provider_refused`, `cost_unknown`, `overshoot` |
| framing marker | `<<TOOL RESULT call_id=ID tool=NAME>>` ... `<<END TOOL RESULT>>`; assistant line `tool NAME {json}` (model_gate.py:286-299) |
| UnidataMismatch | the start-up refusal of `textnorm.require_pinned_unidata` (textnorm.py:1758-1773; app.py:130-132; accepts only `defaults.TEXTNORM_PINNED_UNIDATA` = "15.1.0") |
| REDACT_BUDGET_S | 6.0 CPU seconds of the calling thread per `redact_text` call (defaults.py:102); the gate's `EnforceBudget` uses it for both its CPU and its wall deadline (runmap.py:1052-1054) |
| `_SETTLE_ROUNDS` | 4 (redact.py:2792): rounds 2 to 5 after the first pass; `RedactionError("NotSettled")` past it (redact.py:1431) |
| G8 test rows "K1" to "K90" | the KEEP rows of tests/g8_cases.py (e.g. "K85" at :468). A separate numbering from the K numbers of this file |

### 4.2 Table of known gaps

Every K1 to K85 appears once in part 2 and once here. The status here equals the status in part 2 (checked by a script, 4.8). "probe" = a direct call of this pass (4 header).

| gap | status | evidence level | evidence | who acts |
|---|---|---|---|---|
| K1 secret not found passes | PINNED | TESTED | T::test_t5_... (test_model_gate.py:361) | nobody |
| K2 short, digits, common words, touching | PINNED | TESTED | E::test_stated_limit_short_values_... (test_runmap_enforce_map.py:263), :291; redact.py `_sweep` :3000, `_joins` :3027; probe | nobody |
| K3 other spellings (gate) | PINNED | TESTED | T::test_t7_... (:403), T::test_g13_10_... (:2917), T::test_d7_... (:1888); runmap.py:1503-1532; probe | nobody (gate) |
| K4 letter case | PINNED | TESTED | T::test_d7_stated_limit_another_letter_case_... (:1877); probe | nobody |
| K5 two touching overlapping identifiers | PINNED | TESTED | E::test_trap3_a_partial_overlap_... (:180, identifier lines :200-203); model_gate.py:40-49 | nobody |
| K6 joined key and value | PINNED | TESTED | T::test_stated_limit_a_clean_key_and_value_... (:2414) | nobody |
| K7 placeholder-shaped values | PINNED | TESTED | E:: :433, :441, :463 | nobody |
| K8 fields not masked | PINNED | TESTED | T::test_t20_... (:1818), T::test_d7_role_... (:1909); request 3 section 6 (WAITING, core-b) | nobody |
| K9 no map | PINNED | TESTED | T::test_no_map_means_no_enforce_step_at_all (:681) | nobody |
| K10 audit says map in use | FIXED | TESTED | model_gate.py:281-285, :775-781; T:: :2454, :1828 | nobody |
| K11 forged marker | FIXED | TESTED | model_gate.py:794-852; T::test_r2_b1_... (:2161) | nobody |
| K12 edge value tail | FIXED | TESTED | runmap.py:1078-1081, :1414-1500; T::test_r2_m2_safety_net_... (:2521-2534, red before G13) | nobody |
| K13 per-call time and size | OPEN | TESTED / NOT REPRODUCED | runmap.py:1044-1071, :1167-1178; T:: :2631, :3051 (R15 killer); E8 item 1, E18 (stall) | core-c |
| K14 planted secret stops tool calls | OPEN | TESTED | model_gate.py:417-444; T:: :2033, :2762 | owner (decision 1) |
| K15 tool line rewritten | FIXED | TESTED | model_gate.py:804-808, :828-829; T:: :2736 | nobody |
| K16 interrupt leaves no row | FIXED | TESTED | model_gate.py:619-666, :706-719; T:: :2476, :2843, :2864 | nobody |
| K17 two writers | OPEN | UNVERIFIED | runmap.py:1001-1003; model_gate.py:154-156 | core-c (adds it to request 3) |
| K18 run left working | WAITING | UNVERIFIED | agent_loop.py:485-492; model_gate.py:456; request 3 sections 3, 7 | core-b |
| K19 guardrail call outside gate | STATED | UNVERIFIED | plan-v4-final line 29; test_gate_install_callers.py:43-44 | nobody |
| K20 failed call not settled unless marked | WAITING | TESTED / UNVERIFIED | model_gate.py:340-358, :683-690; T:: :1267, :1421; request 2 | core-b |
| K21 empty cost booked as free | WAITING | TESTED / UNVERIFIED | T:: :1132; models.py:299; request 3 section 4 | core-b |
| K22 unreadable cost not settled | PINNED | TESTED | T:: :1290; model_gate.py:392-399 | nobody |
| K23 retries settle last attempt | WAITING | UNVERIFIED | llm/retry.py:83-108; ORDER 017 item 3 | core-b |
| K24 higher real cost passed to settle (gate side) | PINNED | TESTED | T:: :283; model_gate.py:715-716 | nobody |
| K25 worst-case formula; zero accepted | WAITING | UNVERIFIED | model_gate.py:224-226, :380-389; k1b/loop.py:115, :170 | core-b |
| K26 spend counters rights | OPEN | UNVERIFIED | store/migrate.py:40, :53-54 | owner (decision 5), then core-b |
| K27 stale price table | STATED | NONE | plan-v4-final line 29 | nobody |
| K28 in-memory cap on command lines | STATED | NONE | plan-v4-final line 29; `usd_cap` | nobody |
| K29 stop-switch rights | OPEN | UNVERIFIED | store/migrate.py:55; 0001_core.sql:94; 0002_audit_chain.sql:25-34 | owner (decision 5), then core-b |
| K30 in-flight call, command lines ignore stop | STATED | NONE | plan-v4-final line 30 | nobody |
| K31 audit lacks masked flag and route | OPEN | UNVERIFIED | model_gate.py:281-285 | owner (decision 2) |
| K32 audit rights of other logins not shown | OPEN | UNVERIFIED | store/migrate.py:41-45, :57-58; 0002_audit_chain.sql:25-34; E7 item 5 | core-b (when its store code is merged) |
| K33 command lines audit to screen | STATED | NONE | plan-v4-final line 32 | nobody |
| K34 unknown shape | STATED | NONE | README.md "Limits and trust" (origin/main, 2026-11-04) | nobody |
| K35 bare number | STATED | MEASURED | evidence/P1c-probe.md (24 of 43, main); probe | nobody |
| K36 host names (G4c) | FIXED | TESTED / MEASURED | redact.py:195-225, :474-477; test_host_names.py (TB-4.1 to TB-4.13); test_p1c_gaps.py:46-52, :179 (7 of 44 rows readable, pinned); G4C-build-notes.md; probe | nobody (decision 3: client note, OPEN) |
| K37 short base64 | FIXED | TESTED / MEASURED | runmap.py:844-913; test_p1c_gaps.py:80, :101; test_b64_scan.py; probe | nobody |
| K38 glued IPv4, phone, IBAN, UUID | FIXED | TESTED / MEASURED | redact.py:91-97; G8-build-notes.md:38; probe | nobody |
| K39 repeat not proven complete | OPEN | TESTED | redact.py:1351-1431, :2792; test_redact_idempotent_property.py:205 | core-c |
| K40 tail up to 7 | FIXED | TESTED / MEASURED | test_redact_settle_loop.py tail cases; probe | nobody |
| K41 finder time | OPEN | MEASURED | redact.py:1351-1431, :1471-1477; defaults.py:38-44, :90-94, :102 | core-c |
| K42 tool error not in map | WAITING | UNVERIFIED | tools.py:1009; request 4 | core-b |
| K43 escaped-placeholder spelling and cut-off start | PINNED | TESTED / MEASURED | redact.py:1035-1057, :1845-1853; test_redact_own_output_hardening.py:86; test_redact_context_after_sweep.py:498; probe | nobody |
| K44 wrapped secret | FIXED | TESTED / MEASURED | test_redact_own_output_hardening.py:46; probe | nobody |
| K45 finder on its own output | FIXED | TESTED / UNVERIFIED (other places) | test_redact_own_output.py:51 | nobody |
| K46 space or `;` in a secret | STATED | MEASURED | SECURITY.md "Stated limits of redaction" (origin/main, 2026-11-04); probe | nobody |
| K47 look-alike search in the finder | FIXED | TESTED | test_redact_g3_port.py | nobody |
| K48 escapes, newer characters, hidden marks | STATED | UNVERIFIED | G1-result-review-1.md line 17 | nobody |
| K49 Chinese zero (U+3007) | PINNED | TESTED | test_textnorm_mixed_script_micro.py:117 | nobody |
| K50 over-matching (rates) | STATED | MEASURED | G1-false-hits-and-cost.md:106-130; defaults.py:313-320 | nobody |
| K51 injection CPU and wall budgets | PINNED | TESTED / MEASURED | defaults.py:352-366; injection.py:68-97; textnorm.py:622-649; test_textnorm_deadline.py:287, :502, :529 | nobody (LEAD DECISION D4, M3) |
| K52 long Chinese or Japanese text | STATED | MEASURED | G1-fold.md M6 | nobody |
| K53 dashes, quotes, slashes, 30 code points | PINNED | TESTED | redact.py:1155-1178; redact_mutants.py Q9 rows; G1-mutants-run.md:154-194 | nobody |
| K54 Latin accent matching | PINNED | TESTED | test_evidence_decomposed.py:157 | nobody |
| K55 other scripts (grounding) | OPEN | UNVERIFIED | G1 review M7 | owner (decision 4) |
| K56 undo recombines | FIXED | TESTED | test_undo_composes.py | nobody |
| K57 boundary split | FIXED | TESTED | test_injection_chunk_boundary.py | nobody |
| K58 start-up order | FIXED | TESTED | test_app_unicode_check_order.py:18; app.py:130-132 | nobody |
| K59 requested-by line | WAITING | UNVERIFIED | request 5 | core-b |
| K60 link check | OPEN | TESTED / UNVERIFIED | test_p1d_link_oracle.py:218; pyproject.toml:52-53 | core-c |
| K61 glued e-mail | FIXED | TESTED / MEASURED | test_text_parts_together.py:213; probe | nobody |
| K62 admin page | OPEN | NOT RUN | G2 review (admin console not checked) | core-c |
| K63 install on 3.12 succeeds | OPEN | NOT RUN / UNVERIFIED | pyproject.toml:8 | core-b |
| K64 planted edge values over 4,096 | OPEN | TESTED / UNVERIFIED | runmap.py:1031-1041; agent_loop.py:433-439, :556-562; T:: :2570 | core-c |
| K65 value spanning a framing word | PINNED | TESTED | runmap.py:1557-1576; T:: :2706, :2673, :2723 | nobody |
| K66 tool name slot vs tool list | FIXED | TESTED | model_gate.py:417-453, :794-852; T:: :2736, :2762 | nobody |
| K67 install list judge sites | FIXED | TESTED | test_gate_install_callers.py:56, :296, :353 | nobody (install: core-b, K18) |
| K68 rolled-back spelled entry | FIXED | TESTED | redact.py:1778, :1956; test_redact_settle_loop.py:250, :261 | nobody |
| K69 map not checked as the run's own | OPEN | TESTED / UNVERIFIED | model_gate.py:573-578, :780; T:: :1770, :2877 | owner (with decision 6), then core-c |
| K70 glued shapes left readable as built | PINNED | TESTED / MEASURED | test_redact_glued_rest.py:104, :137; g8_cases.py:468-473, :495, rows 102-103, K91-K93; G8T-build-notes.md; probe | nobody (LEAD DECISIONS L-D13, L-D15, L-D17) |
| K71 remainder of a long token (L15; `_` or a letter) | PINNED | TESTED / MEASURED | g8_cases.py:255; test_redact_glued_rest.py:263; probe | nobody (LEAD DECISION E16) |
| K72 overlaps in the finder (E10, G9b) | FIXED | TESTED | redact.py:2158, :2271-2326, :2364-2440, :2594-2610; test_redact_settle_loop.py:1821, :1837, :1932, :2375-2436; G9b-build-notes.md | nobody (LEAD DECISIONS G9, E17; E23 file status OPEN) |
| K73 refusal of a whole document | STATED | MEASURED | redact.py:1431, :1477, :1933, :2592, :2612, :2728, :2836; defaults.py:129-163 | nobody |
| K74 finder memory (E14) | FIXED | TESTED / MEASURED | defaults.py:48-61; redact.py:2826-2836; agent_loop.py:98-100; test_redact_finder_cap.py | nobody (LEAD DECISION E14) |
| K75 extra map entry on the tool-error path (E9) | PINNED | TESTED / MEASURED | redact.py:1045-1051, :1853; test_redact_own_output_hardening.py:202, :229; probe | nobody (LEAD DECISION E9) |
| K76 spelled placeholder returned decoded (E15) | PINNED | TESTED / MEASURED | test_runmap_e15_placeholder_spellings.py; probe | nobody |
| K77 punctuation, wrappers and escaped edges at a stored secret's ends (G12, G12b, G12c) | FIXED | TESTED / MEASURED | redact.py:966-1033, :1868-1918; test_redact_g12_trailing_punct.py (G12-1 to G12-28); G12-build-notes.md; probe | nobody |
| K78 overlapping secrets at the gate (E19 M1) | FIXED | TESTED / MEASURED | runmap.py:1137-1143, :1414-1500; E:: :866, :180, :212, :880, :887; probe | nobody |
| K79 net passes base64, NUL-split identifier, ANSI split | PINNED | TESTED | T::test_g13b_5_... (:3036), T::test_d7_... (:1888); model_gate.py:26-31, :80-82 | nobody (LEAD DECISION G13 D4, D8) |
| K80 net blind spots | STATED | TESTED / UNVERIFIED | model_gate.py:80-91; runmap.py:1350-1358, :1373-1400, :1503-1554; test_runmap_enforce_map.py:1128, :1156; probe | nobody (LEAD DECISION G13 D5) |
| K81 paths with no masking (E19 M2) | OPEN | UNVERIFIED | k1b/replay.py:119-123; k1b/loop.py:147, :211-214; extract.py:51; producers.py:64, :70; E19-M2-producers-table.md | core-b (LEAD DECISIONS G13 D1-D3) |
| K82 base64 view limits (L-B1 to L-B8) | PINNED | TESTED / UNVERIFIED | test_b64_scan.py:978-1010; runmap.py:606; defaults.py:168-171 | nobody (LEAD DECISION L-B8) |
| K83 unwired text-folding API (O-1) | OPEN | UNVERIFIED | textnorm.py:20-30; E19 M4; TIDYT-build-notes.md (8 helpers named) | owner (decision 8) |
| K84 interior punctuation, unlisted escapes (L-G12) | OPEN | MEASURED / UNVERIFIED | redact.py:966-1033, :1897-1907; probe; G12-build-notes.md "G12c" (not done); G12-result-review-2-design.md M2-M4 | core-c (no fix built; lead decision) |
| K85 net refuses ordinary text beside a key (permanent for the run; per-key cap) | PINNED | TESTED / MEASURED | runmap.py:1354-1360, :1403-1411, :1414-1500; test_runmap_enforce_map.py:1079-1190; test_model_gate.py:3064; G13c-build-notes.md; probe | nobody (LEAD DECISIONS: letter-only minimum, refusal code) |

Batches behind the TESTED words (each result line is in the file named):

- Whole suite, not perf, not live, -n 3, 14:06-14:17 UTC, 647 s: 15955 passed, 561 skipped, 74 xfailed, 10 failed (STATUS-BOARD.md line 16, entry 14:23Z). The 10 failures and what became of each: 2.0.
- After it: 509 passed, 1 skipped, 9 xfailed (10 gate, E9 and b64 files, G13b merge); 412 passed, 1 skipped (test_model_gate, p1d_a_rows, p1d_a_paths, mutants_picked_up, TIDYP); 1016 passed, 24 xfailed (b64_scan, p1c_gaps, own_output, g12, G4 tidy); 297 passed (four E9 own-output files after 9806830d0). All core-c runs, STATUS-BOARD.md line 16.
- Later, on the status board (STATUS-BOARD.md line 4, STATE): non-perf suite 16071 passed, 2 failed (commit not written: UNVERIFIED); perf-marked tests at idle on 2552bcc95: 96 passed, 1 skipped, 0 failed in 427 s.
- Builders' batches after fd1fb3e31: evidence/G13c-build-notes.md (figures only, no pass counts for the new tests), G12-build-notes.md "G12c" (35 of 35 breaks; no pass count), G9b-build-notes.md (2,498 passed in ten files; 130 of 130 breaks), G4C-build-notes.md (2,992 passed, 6 xfailed; then 575 passed, 45 xfailed; 58 of 58 base64 and host breaks; 43 of 43; 50 of 51), G8T-build-notes.md (2,544 passed, 46 xfailed; 43 of 43), REC-notes.md (4,879 passed, 2 failed, then 139 passed after the PU1 re-pin; 123 of 123 breaks before G9b), TIDYT-build-notes.md.
- Merged-tree batch 9, 13:28Z, 20 files, -n 3: 3794 passed, 4 skipped, 45 xfailed, 3 failed (the three E20 failures, re-pinned since in 1bda9b7aa).
- Builders' own batches: evidence/G9-build-notes.md, G12-build-notes.md, G13-build-notes.md, G13b-build-notes.md, E14-build-notes.md, M3-build-notes.md, G4-build-notes.md, GATE-C-build-notes.md, TIDYP-build-notes.md, G4PERF-build-notes.md, F3-build-notes.md (F3: "Test runs: see the builder report", no batch line in the file).
- Laptop JOB 1 at 9aeedc22f (12:54Z, before G9, G4, E14, G12, G13, M3): inputs/evidence-cfull.md runs a, b, c.
- v6's batches 1 to 5 (evidence/INT-merged-batch-1.md to -5.md: 2687 passed, 1 skipped, 5 xfailed in 15 files) ran at a60da3394 and earlier; they are not cited for any claim about fd1fb3e31.

### 4.3 Counts by status (85 gaps)

Recomputed from the 4.2 table by a script (docs8_work/table.py). v7 had PINNED 23, OPEN 20, FIXED 22; K36 moved OPEN to FIXED and K85 moved OPEN to PINNED. No gap is STRUCK; that status is retired.

| status | count | gaps |
|---|---|---|
| PINNED | 24 | K1-K9, K22, K24, K43, K49, K51, K53-K54, K65, K70-K71, K75-K76, K79, K82, K85 |
| STATED | 13 | K19, K27-K28, K30, K33-K35, K46, K48, K50, K52, K73, K80 |
| WAITING | 7 | K18, K20-K21, K23, K25, K42, K59 |
| OPEN | 18 | K13-K14, K17, K26, K29, K31-K32, K39, K41, K55, K60, K62-K64, K69, K81, K83-K84 |
| FIXED | 23 | K10-K12, K15-K16, K36-K38, K40, K44-K45, K47, K56-K58, K61, K66-K68, K72, K74, K77-K78 |
| total | 85 | 24 + 13 + 7 + 18 + 23 = 85 |

Gaps named in part 1 (41 of 85):

- item 6: K25, K20, K21, K23, K42, K59, K18, K8 (request), K63;
- item 16 K34; item 17 K36; item 18 K37; item 19 K82; item 20 K8; item 21 K19; item 22 K84; item 23 K77; item 24 K81; item 25 K35, K46, K70; item 26 K42; item 27 K78, K3; item 28 K79, K80; item 29 K65;
- item 30 K25; items 31-32 K20; item 33 K24; item 34 K21; item 35 K23; item 36 K26;
- item 37 K68; item 38 K29; item 39 K14; item 40 K85; item 41 K64; item 42 K13; item 43 K41; item 44 K63;
- item 50 K70; item 51 K71; item 52 K72; item 53 K73; item 54 K74; item 55 K75; item 56 K51; item 57 K83.

Distinct: K3, K8, K13, K14, K18, K19, K20, K21, K23, K24, K25, K26, K29, K34, K35, K36, K37, K41, K42, K46, K51, K59, K63, K64, K65, K68, K70, K71, K72, K73, K74, K75, K77, K78, K79, K80, K81, K82, K83, K84, K85 = 41.

Order rule (item 9): groups first; within a group wider exposure first, roughly; a tested or measured gap before an UNVERIFIED one of about the same width. Items 45 to 49 are the "shown by tests" lines and name no gap.

### 4.4 Where two sources disagreed

Items 1 to 37 of v6's list (decisions about sources at heads 6b990d9 and a60da3394) are not repeated; they are in inputs/SECURITY-README-v6.md 4.4. The ones still in force and the new ones:

1. Short-value exemptions: the gate docstring and `_sweep` agree (model_gate.py:8-15; redact.py:2968): a secret of 4 or more characters is masked in every copy.
2. The 2026-11-23 date: neither ORDERS.md nor DECISIONS.md holds it (grep "11-23"). "Proposed by core-c, not confirmed in writing". The 2026-11-22 draft-note date of decision 3 is a drafter's proposal.
3. K35's source: G4 v2 cites "order 64 item 4"; ORDERS.md line 64 is ORDER 006 item 1. Status kept STATED.
4. Decision 6 default "refuse, as ordered" versus the code: model_gate.py:282 `MODE_EMPTY` accepts and marks an empty map. Part 1a says both.
5. K13 stall: the gate builder's measurement (E8 item 1: 6.8 s with a 0.5 s budget, round 4 code) and the code note (model_gate.py:97-99, "about 7 s") versus core-c's run (E18: 0.47 s and 0.89 s CPU with 500 held values of 20 to 49 `a`s). The reviewer's exact shape is unknown. We say NOT REPRODUCED and drop the figure from part 2 (style review M2).
6. K50 corpus-word row: the evidence has 3.914 % (G1-false-hits-and-cost.md:128) and 4.10 % (:32); defaults.py:316 says "3.9-4.5% (two runs)"; 4.46 % is only in tickets/G10-review-2-design.md:6. We say 3.9 to 4.1 % in the two recorded runs, and mark 4.5 % UNVERIFIED (lead review N4 over style review M13's "4.46").
7. K46: the published SECURITY.md says a space, `;`, `,` or `&` ends the masked value. The probe shows `,` and `&` inside a key=value value do not end it (K84). We keep the STATED status for space and `;` and point `,` and `&` to K84.
8. K12: v6 kept OPEN / NOT REPRODUCED. The G13 change refuses the reviewer's output text (`<SECRET_1>abcdef`) and that test line was red before G13. We call it FIXED; the G13 design review notes the test uses an identity-enforce double.
9. K5 and style review B1's K78: B1 asked for K78 OPEN ("two overlapping known secrets"). G9 closed the exact input (MEASURED here and in evidence/G13-build-notes.md "Phase 0"). We record K78 as FIXED and keep K5 for the identifier limit that remains.
10. Style review B1's K77: B1 named "full-width spelling" as part of K77. The E18 correction (G12 drafter) shows the full-width probe was mis-built and the leak is the trailing punctuation. K77 describes that, FIXED by G12/G12b.
11. Style review M10 ("no independent review of round 4 on file") versus ESCALATIONS.md E18 (core-a cross review of 7c31dbc97, after round 4). We say the review exists only as a summary here (its file is on origin/cloud/core-a and was not read).
12. Style review M15 ("No call site has a wall-clock limit") was overtaken by M3: the injection check now has a wall-clock deadline (defaults.py:359-366). K51 says so.
13. Style review M17 ("Python 3.12 carries 15.0.0" is UNVERIFIED): the laptop's Python 3.12 run printed '15.0.0' (inputs/evidence-cfull.md run b, failure 9) and E4 measured it. We write MEASURED.
14. Style review M11 quoted `call +44 20 5550 1234.` -> `call <PHONE_1> 1234.`. On fd1fb3e31 the probe gives `call <PHONE_1>.` (G7-F3). K70 uses the current output.
15. G8 build notes count 35 mutants; tickets/G7F3-result-review-1-design.md counts 43 after G7-F3 (G8-P15 to P22). We use 43.
16. Gate breaks: tests/test_gate_mutants_picked_up.py:20 [re-check] `MIN_MUTANTS = 128` and 128 rows (grep), while evidence/G4-build-notes.md "State at ca469a0bf" says 121 (before G13b). We use the file at fd1fb3e31.
17. E19 M2 table row 11 says the replay path is "covered only if cfg.k1b.redact true"; the producers test (test_k5_producers.py:98-107) still registers modules, not call sites, although the board says core-a's call-site change merged. We describe the test as read at fd1fb3e31.

18. The status board's STATE line gives "16071 passed, 2 failed" for the non-perf suite and names commit 2552bcc95 for the perf batch only. We do not assign a commit to the first figure (UNVERIFIED).
19. G4c: the board says the start rule "closes the 19+6 open host rows"; tests/test_p1c_gaps.py `HOST_CLOSED_IDS` holds 19 ids and the other 25 rows keep the base digests. K36 uses the file: 19 pinned as closed, 7 of 44 measured readable.
20. G8T notes: records said the OL3 shape masks as one HIGHENTROPY; measured it is two placeholders (`<HIGHENTROPY_1><ACCOUNTID_1>`). K71 does not name OL3's placeholders, so no change.
21. v7's K84 listed `%0A`, `&quot;`, `<br/>`, `ADMIN_1` and a stray `‹` or `›` as leaks (MEASURED on fd1fb3e31). On 2552bcc95 all five are masked (MEASURED here). K84 keeps interior punctuation and `%250A`.
22. ESCALATIONS.md E23 still says "OPEN, fix to be built (G9b)" while G9b is merged. We follow the code and the build notes; the lead updates the file.
23. G13c notes say E19g and E19i were red for another parameter at HEAD; commit 252ef2881 (four gate mutants) repaired them. We use the commit.
24. REC re-pinned PU1 to `<SECRET_2>`; TIDYP had pinned `<SECRET_3>`. The REC note asks the lead to confirm; part 1b keeps PU1 as a lead decision.
25. The repository-rule test of vendor brand strings scans every file of the project, the handover folder included. At the time of writing it fails on five handover files (the lead's brief preamble, the status board, two evidence files and v7 of this draft). v7 and v8 hold no brand string after this pass. The other four are not this draft's to change, so the test stays red until the lead cleans them.

### 4.5 Requests to core-b (files in handover/core-c/requests)

1. 1-producers.patch: register the gate as a model caller (applied by core-c as aa7c5fa; decision 7).
2. 2-refused-before-response.md: the "refused before any answer" mark (K20), with the 13:2xZ update for ProviderExhausted (gate (c)). The gate side is built; no adapter sets the mark.
3. 3-bind-mapping-required.md: required map, `GateRefused`, empty cost, catch sites, prompt-registry install check (K8, K18, K21). Not yet in it: "one writer per run map" (K17).
4. 4-error-reason-run-map.md: tool-error text with the run map (K42).
5. 5-card-ids-redact-defang.md: id fields on approval messages (K59).

Lead's orders to core-b without a request file: sum the cost of all attempts (ORDER 017 item 3, K23); the worst-case formula (ORDER 016c item 13, K25); an operator release for expired reservations (ORDER 017 item 4); the install test with core-b (ORDER 020 MJ-C). K63 has no request yet: core-c writes one if the lead agrees. K81 (replay echo, extract.py deletion) needs a lead decision first (E19 M2 answer, G13 D1-D3). The stale contract test tests/contracts/test_model_gate_contract.py (`_bind` passes a dict) is core-a's (E18).

### 4.6 What is open at the time of writing (2552bcc95)

Merged since fd1fb3e31 and described in v8: 2be75e38c (M3 tidy: textnorm.py docstrings, `NotText` for a huge int budget), 53df94aee (G8/G7-F3 leftovers: tests, wording), 5d8c8ca04 (G13c), d6d545f6c (G12c), 299bb3038 and ab8ee0440 (G4c), 1a0965361 and fe2f1f9d2 (G9b), 252ef2881 (four gate mutants), 5219a3320 (PU1 re-pin), 2552bcc95 (a recording re-keyed). `git diff --stat fd1fb3e31 HEAD -- src`: approvals/gate.py (a comment), defaults.py (+12), guard/model_gate.py, guard/redact.py, guard/runmap.py, guard/textnorm.py.

Not built:

- G11 (E16 opaque-token post-pass, K71): ticket written, NOT built; waits for the lead's E16 word.
- K84: interior punctuation and `%250A`; no fix built. The G12c builder's own "not done" list is in evidence/G12-build-notes.md.
- The letter-only minimum and a refusal code of its own for the net (K85): not built, lead decisions.

Stated limits that stay open (each in part 2):

- Gate net blind spots (K79, K80): base64 of a secret is not in the views; UTF-7, quoted-printable, hex, ROT13 and reversed text; a secret wrapped across lines; pieces under 4 characters (`NET_MIN_PIECE`); a piece one character from a key; interior pieces between two keys; stacked escape layers across a window edge.
- K85: ordinary words at a secret's start refuse text beside a placeholder, for the rest of the run; one key reads at most 4,096 hits.
- 4-character limits: a secret under 4 characters is masked only standalone (3 characters) or not at all (under 3) (K2); the net reads pieces of 4 or more only (K80).
- Phone before `.` + letter, digit or `_` (K70): readable; the spaced `+44` shape is masked in part.
- E16 (K71): LEAD DECISION pending; the default (accept L15) is what the code does.
- The base64 view limits L-B1 to L-B8 (K82).
- Host names (K36): public-looking endings, `.svc` forms, a private word inside a name, one trailing digit after `host`.
- Unmasked paths (K81): k1b replay with the acknowledgement flag, the k1b echo and rendered results, extract.py, alert_time_text, the ask-your-data demo.
- The unwired textnorm DENY API (K83, O-1), 14 names: `scan_holds`, `register_value`, `Coverage`, `scan_cache`, `scan_needles`, `identity_key`, `identity_keys`, `could_be_same_person`, `allow_equal`, `names_equal`, `has_mixed_script`, `has_hidden_channel`, `value_scripts`, `scan_views` (textnorm.py:23-25).

Lead decisions open (part 1b): L-D13 (built by order, option not confirmed), L-D15, L-D17; G10 D1-D10 and the M3 factor; G4 L24-L28 and L-B8; G4c start rule; G9 L-D1, L-D6', L-D7, L-D3b; E23 numbers; E17; E20 (R8); E14 constants; G13c cap; G12 6.1-6.7 and the G12c numbers; G13 D1-D8 (incl. extract.py deletion, k1b replay and echo) and the round 2 letter-only prefix rule; gate (c) contract; E9 option (b); PU1 re-pin (twice); E21 (redact_mutants baseline perf test). Owner item O-1 is decision 8; decision 3 is now only the client note.

Verification gaps: a whole-suite batch with a named commit; Python 3.12 and PostgreSQL 17 after 9aeedc22f; whole code-break files for textnorm (268), gate (140), finder (130) on this head; live calls; install; no review of G9b, G12c, G13c or G4c is on file.

### 4.7 How the style review of v6 was used (tickets/SEC-v6-style-review-1.md)

Each finding checked against the code at fd1fb3e31. APPLIED = taken as written or with the current facts; CHANGED = the replacement text was overtaken by later code and the fix it names was applied to the new facts.

| finding | result and where |
|---|---|
| B1 leaks missing from the gap list | APPLIED with current facts: K77 (trailing punctuation, now FIXED, with K84 for what stays), K78 (overlapping secrets, now FIXED), K81 (unredacted paths: extract.py, replay flag, k1b echo and rendered results, alert_time_text, demo), K79 and K80 (gate sees only some spellings; G13 widened it), K65 sentence re-worded; counts 76 -> 85 in 4.3, item 8, glossary. K5's "Who acts" no longer applies: K5 now holds the identifier limit only (4.4 item 9). |
| M1 banner | APPLIED: "No test of the store ran on this branch." (part 2 banner). |
| M2 7 s stall | APPLIED: NOT REPRODUCED in K13 and item 42; the figure dropped from shipped text (4.4 item 5). |
| M3 clocks | APPLIED: K13 sentence names both 6.0 s limits and where each is read; item 42; the 0.018 s figure marked "before the current budget". |
| M4 item 23 "closed" | APPLIED: item 23 now says what is fixed and item 22 what stays; no "closed". |
| M5 rollback | APPLIED: item 37 and K68 say "two tested cases"; "A tool could have got the wrong account or credential." kept. |
| M6 K2 PHONE | APPLIED: K2 says "where no digit touches it" with a probe; rule exceptions K3 to K9 and K65. |
| M7 K64 | APPLIED: the 2,000-value agent-loop stop (UNVERIFIED, read), 4,097 "worked out, not run", "because the run map only grows" dropped. |
| M8 decision 1 | APPLIED: "Only the narrower rule was tested." |
| M9 "booked" claims | APPLIED: item 32, K20, K24 say the store side is not on this branch; K16 adds the settle and audit-write stop limit. |
| M10 round 4 review | CHANGED: 2.0 says the only independent review of round 4 is the core-a cross review, known here as a summary (4.4 item 11); "FIXED on the gate means the builder's tests pass, unless a review is named." |
| M11 "by design" | APPLIED: K70 "as built", the lead has not decided. The phone examples were updated to the G7-F3 code (4.4 item 14). |
| M12 round numbers | APPLIED: K39 and CHANGELOG-lines-v7.md C6. |
| M13 K50 | APPLIED with the lead's N4 correction (4.4 item 6): hit rates, corpus words, shares not false-hit rates, real-text rates. |
| M14 arithmetic | APPLIED: K41 "12 to 33 percent slower ... (worked out, not run)" and "no wall-clock limit; a caller must add it"; K51 "would flag ... (worked out, not run)". |
| M15 wall clock not shown | CHANGED: M3 built a wall-clock deadline; K51 says so, and CHANGELOG.md line 664 already holds the M3 entry (4.4 item 12). |
| M16 hygiene | APPLIED: no "[v6]", "STRUCK", "NOT PROVABLE", "v5" or "v6" in parts 2 and 3; K32 re-worded as "Not shown on this branch" with UNVERIFIED; STRUCK retired. |
| M17 Python 3.12 | CHANGED: now MEASURED (4.4 item 13); "NOT RUN" kept for a pilot start on 3.12. |
| M18 K76 | APPLIED: "Accepted" plus "A probe found no case ... that is a probe, not a proof." |
| M19 item 21 IBAN | APPLIED in K38 ("An IBAN with `_x` glued behind it"); part 1 no longer lists that shape as a leak. |
| M20 figures | APPLIED: K71 and item 51 "10 or 11 digits", "up to 39; the measured rows hold 20, 30 and 32"; L-D15 "hand-picked"; L-D17 "not worked out". |
| Nits | Applied: item 34's successor wording; K12 now FIXED by a named test; 2.1 "past its size, step or time budget"; K42 UNVERIFIED; `<S1>ijkl` no longer an example (K72 FIXED; CHANGELOG-lines-v7.md C8 now has no example); K53 "20 code points (dashes and the minus sign)"; STRUCK retired; decision 2 and item 3 re-worded; CHANGELOG heading levels, C10/C11 sentences and the internal-code note (CHANGELOG-lines-v7.md). Not applied: "part 2 order note" (the K order inside 2.1 and 2.5 is kept as v6 had it: K64, K65 to K67, K69 after K17; new K78 to K80 and K85 after K19; this note records it). |

None of the 20 Majors was left unapplied. Three (M10, M15, M17) were changed because the code or the evidence moved after the review.

### 4.8 Change log of version 8 (does not ship)

| change | where | reason |
|---|---|---|
| code described 2552bcc95 (was fd1fb3e31); line references moved by diff, `[re-check]` where the stretch changed | all parts | G13c, G12c, G9b, G4c, gate mutant repairs, TIDYT, G8T, REC merged since |
| batches: the later board batch (16,071 passed, 2 failed) and the perf batch (96 passed) added; the NOT RUN whole-suite claim narrowed to "a batch with a named commit" | 1, 2.0, 2.9, 4.2 | STATUS-BOARD.md line 4 |
| K36 OPEN to FIXED (host names), 7 of 44 rows still readable, limits listed | 1 (items 7, 17), 1a decision 3, 2.5, 4.2 | G4c, evidence/G4C-build-notes.md, probe |
| K85 OPEN to PINNED; per-key cap, digest, head test, auth words in any case | 1 (items 40, 41), 2.1, 4.2 | G13c, evidence/G13c-build-notes.md, probe |
| K80: punctuation-only secret now read; auth word list | 2.1 | G13c m1, m2 |
| K77 widened (escaped edges, `ADMIN_1`, stray `‹` `›`, large value); K84 cut to interior punctuation and `%250A` | 1 (items 22, 23), 2.5, 4.2 | G12c, evidence/G12-build-notes.md |
| K72, K73: charge as found, SECRET union entry of its own, one read-back per edge, numbers, CPU clocks | 1 (item 52), 2.5, 4.2 | G9b, evidence/G9b-build-notes.md |
| K70: two partial-mask shapes and one over-mask added; K71: a letter also sets a UUID off | 2.5 | G8T, G8 leftovers, probe |
| K83: the 8 helper names are now in the module note | 2.6 | TIDYT |
| 1b: PU1 (twice re-pinned), new rows G4c, G12c numbers, G13c cap, E23; G9, G12 and G13 round 2 rows reworded | 1b | the same changes, REC-notes.md |
| counts: PINNED 24, STATED 13, WAITING 7, OPEN 18, FIXED 23 (v7: 23, 13, 7, 20, 22) | 4.3 | K36, K85 |
| the brand string removed from v7 and not written in v8 | 2.0 line, 4.4 | repository-rule test |

Checks after writing, by a script (docs8_work/check_v8.py): every K1 to K85 appears once in part 2 and once in 4.2; each part 2 status equals its 4.2 status; the 4.3 counts sum to 85; part 1 holds no K numbers outside item text that v7 already had; no brand string anywhere in the file.

### 4.9 Change log of version 7 (does not ship)

| change | where | reason |
|---|---|---|
| code described fd1fb3e31 (was a60da3394) | all parts | G9, E14, G4 Phases 0-3, G12/G12b, G7-F3, M3/M4, gate (c), G13/G13b, E22, TIDYP merged since |
| "[v6]" marks, STRUCK, NOT PROVABLE removed; K32 re-worded | all parts | style review M16 |
| batches: whole-suite run of 14:06-14:17 UTC and the re-runs after it | 1, 2.0, 4.2 | newer than v6's batch 5 |
| K3 (decoded spellings refuse a secret), K5 (identifier limit only), K12 FIXED, K13 (two clocks, stall NOT REPRODUCED), K16 (settle/audit limit), K18 (agent loop catch), K64 (2,000-value stop), K65 | 2.1 | G13, G9, R15 killer, style review M2, M3, M6, M7, M9 |
| K20 (mark honoured; no adapter sets it), K24, K25 (zero worst case accepted), K32 | 2.2, 2.4 | gate (c), E18 nit 6, style review M9, M16 |
| K36 (G4c not merged), K37 FIXED (base64 view), K39, K41, K46 (example and K84 pointer), K70 (G7-F3), K71, K72 FIXED (G9), K73 (new refusal words), K74 FIXED (E14), K76 | 2.5 | G4, G7-F3, G9, E14, probes, style review M11-M14, M18, M20 |
| K50, K51 (wall deadline), K53 | 2.6 | M3, lead review N4, style review M13-M15, nit |
| new K77 to K85 | 2.1, 2.5, 2.6 | style review B1, G12/G12b, G13/G13b and its round 2 review, E19 M2 table, G4 limits, O-1, G12 round 2 review |
| part 1: items renumbered 1-57; decision 3 re-worded (base64 half merged); decision 8 (O-1) added; 1b rebuilt | 1 | the merged work and the open lead decisions |
| part 3: Python 3.12 edition MEASURED | 3 | style review M17, evidence-cfull run b |
| 4.1, 4.4, 4.5, 4.6 rewritten; v6's 4.7 (round 4 log) dropped, it stays in v6 | 4 | process history of a60da3394 |

Checks after writing, by a script (docs7_work/check_v7.py): every K1 to K85 appears once in part 2 and once in 4.2; each part 2 status equals its 4.2 status and each 4.2 evidence word appears in the part 2 entry; the 4.3 counts sum to 85; part 1 holds no K numbers; no team code, ticket code, version mark or the words STRUCK and NOT PROVABLE in parts 2 and 3 outside `[INTERNAL]` lines; no sentence over 30 words in parts 0 to 3 outside `[INTERNAL]` lines and tables.
