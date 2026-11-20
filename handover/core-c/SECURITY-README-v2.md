# Security wording v2: what the kit guarantees and what it does not

DRAFT, version 2, written by core-c on 2026-11-20 from the sources as they stood at about 07:35 UTC.
It replaces SECURITY-README-final.md (version 1). The lead decides where each part goes: part 2 into SECURITY.md, part 3 into README.md.
This file changes no other file. Code and test names appear only in the appendix (part 4).

How to read the marks:
- UNVERIFIED: a reviewer read the code and reported it. Nobody has run it yet.
- NOT RUN: the check was not run at all. Nothing is claimed about its result.
- Every example value below is made up. None is a real credential.

---

## 0. Plain glossary (read this first)

People and teams
- **The owner**: the person who owns Hadavin, pays for the work and has the final say.
- **The lead**: the coordinating session on the owner's laptop. It directs the build, writes the orders and decides open questions. The owner can overrule it.
- **core-b**: the build team that owns the model connectors, the store, the agent loop and the approval-message code. It must install the gate.
- **core-c**: the build team that built the gate, the secret finder and text folding. It wrote this file.
- **Reviewer**: an independent checker that reads code and reports. In this work no reviewer ran any code.

Product words
- **The kit**: this software package (the Hadavin SDK) that client projects are built on.
- **Stages**: the only three: demo (shows the product with made-up data), pilot (a first, limited use with a real client), prod (normal live use).
- **Model**: the outside AI service that reads text and answers. A **model call** is one request to it.
- **Model connector**: core-b's code that talks to one AI service and reports the cost of each call.
- **Run**: one job of one agent, from start to finish. The **agent loop** is core-b's code that drives a run step by step.
- **Sensitive value**: a secret (password, key, token) or an identifying value (e-mail address, host name, account number).
- **Mask**: replace a sensitive value with a placeholder. **Placeholder**: a stand-in such as `<SECRET_1>`; the model sees only the stand-in.
- **Run map**: one table per run that records which real value each placeholder stands for.
- **Secret finder** (in code: the redactor): core-c's code that searches text for sensitive values by their shape and masks them. It runs where text enters a run (tool results, documents, approval messages). Only it adds to the run map.
- **Kind**: the type the secret finder gives each value it finds. Secret kinds: passwords, keys, tokens. Identifier kinds: e-mail, host name, IP address and the like.
- **Text folding**: turning look-alike letters (full-width letters, Cyrillic letters that look Latin), invisible characters and accents into one plain spelling before searching.
- **The gate**: one wrapper meant to sit in front of every model call. It masks values already in the run map, reserves money, makes the call, settles and writes an audit row. It does not search for new values.
- **Installed**: placed at every point in the code that calls a model. The gate is NOT installed yet.
- **Framing marker**: the fixed line the agent loop puts around each tool result, `<<TOOL RESULT call_id=... tool=...>>`, so the model sees where tool output starts. Its fixed words are TOOL, RESULT, END, call_id and tool.

Money words
- **The store**: the database that records spending, reservations, the stop switch and the audit record.
- **Cap**: the most money one agent may spend in a day and in a month.
- **Worst case**: the most a model call could cost. core-b's code must compute it.
- **Reservation**: the worst case, set aside against the cap before the call. **Booked**: counted against the cap.
- **Settle**: after the call, replace the reservation with the real cost. "Not settled" means the worst case stays booked.
- **Stop switch**: a flag in the store. While it is on, every new reservation is refused, so no model call goes out.
- **Database login**: a named account the software uses to reach the store (runtime, purge, reset). Each has its own rights.

Record and code words
- **Audit row**: one line in the permanent record of what happened. It holds short codes, never message text.
- **Refusal code**: the exact short word printed when something is refused, for example `kill_switch`, `framing_refused`, `no_map`.
- **Branch**: a named line of code changes. **The shared branch** is core-c's pushed branch, from which the lead takes code. Nothing is on the product's main line yet.
- **Test**: a small program that checks one behaviour and fails when that behaviour changes. A **deliberate code break** is a planted fault used to prove a test can fail.
- **Known gap**: a weakness we know about. Each has a number K1 to K62, used to find it in the appendix.

Status words (one meaning each)
- **FIXED**: changed, and a test fails without the change. **FIXED ON BRANCH**: the same, but the change is not yet on the shared branch.
- **PINNED**: not fixed, on purpose. A named test fails if the behaviour changes.
- **STATED**: accepted and described. No test.
- **WAITING**: another team must act, and a written request exists.
- **OPEN**: nobody has fixed or decided it yet. The line names who must act.

---

## 1. Owner summary

1. **Short answer: built, not connected. Nothing is safe to promise a client until core-b installs the gate and core-c's open leak fixes pass a fresh review.**
2. Next steps: core-c finishes the leak fixes (being written, not yet tested). core-b adds the "refused before any answer" mark, then installs the gate. The lead takes seven decisions (table below).
3. Today a running agent is protected only by the older secret finder. None of the gate's protections reach it.
4. Not protected even after install: secrets in shapes the finder does not know; short base64 text; bare numbers; most host names; the system prompt and tool descriptions.
5. Money: reservations never pass the cap. Booked money can: a call that costs more than its worst case is booked in full.
6. Money: a failed call stays booked for the rest of the day, so three failures can stop an agent (worked out by reading, not run). A reply with no cost filled in may be booked as free (UNVERIFIED).
7. Open weaknesses, worst first (the first two are UNVERIFIED): a forged tool-result marker can carry a known secret out unmasked; a secret placed at a placeholder's edge can leak its tail.
8. Next in order: an empty cost field reads as free (UNVERIFIED); a planted word can stop a run's later tool calls; a secret first seen in a tool error stays readable later (UNVERIFIED).
9. Next: the "requested by" line on approval messages is not masked (UNVERIFIED); a failed call blocks money for the day.
10. Protected, in the gate's own tests only: known values are masked before a call; no call without a reservation; stop switch on means no call; audit rows hold no text.
11. Protected in the store's tests (core-b's code, one database version): 50 simultaneous requests never set aside more than the cap.
12. NOT RUN: the full test suite, Python 3.12, database version 17, any live model call, any end-to-end stop.

### 1a. The seven decisions (the lead takes them; the owner can overrule)

| # | Question | Consequence | Safer default |
|---|---|---|---|
| 1 | Should a planted word equal to a tool name keep stopping the run, or should the gate protect the marker line instead? | Keeping it lets any document stop a tool-using run. Honest names such as "web" may trigger it too (UNVERIFIED). | Protect the marker line. Refuse only when a secret of 4 or more characters equals a tool name or call number. |
| 2 | Should each audit row also say whether anything was masked, and which route and model were used? | Without it, nobody can tell from the record whether masking happened. | Add a "masked: yes or no" field and the route. No text. |
| 3 | Build the planned host-name and base64 change now, or keep both as known gaps? Three questions in its plan are unanswered. | Keeping them means such values reach the model. Building adds code; its plan review found 4 blocking problems. | Answer the three questions, fix the plan, then build. Until then, tell clients in writing. |
| 4 | Accept that the evidence check now matches more text in Korean, Japanese and Indian scripts with hidden characters? | Accepting makes the check more permissive in those scripts, without tests. | Keep the older, stricter matching for those scripts until tests exist. |
| 5 | Tighten four wide database rights (see K26, K27, K29), or accept them in writing? | Accepting leaves the cap and the stop record resting on code alone. | Tighten them (narrower rights or a fixed database function). Decided with core-b. |
| 6 | Should the gate refuse a call whose run map is empty, as ordered, or accept and mark it, as core-c proposes? | Refusing stops every run whose first document held no sensitive value. | Accept and mark it. An empty map has nothing to mask either way. |
| 7 | Accept core-c's change to core-b's approval-message file (Slack), or have core-b redo it? | Until decided, the approval-message fixes cannot land cleanly. Two teams may edit one file. | Accept it as core-c's change and tell core-b at once, as was done for the sibling file. |

---

## 2. For SECURITY.md: "What the kit guarantees and what it does not"

> **Every "What holds" item below is true of the code tested on its own (the gate module, the secret finder, the store). None of it describes a running agent until core-b has installed the gate.**

### 2.0 State of the work
- The gate is built and tested alone. core-b has not installed it anywhere. One test is red on purpose: it lists every place that calls a model and fails until the gate is registered. WAITING on core-b.
- core-b must not install it before the model connectors can say "refused before any answer" (lead's order).
- The approval-message fixes, the glued e-mail fix and the look-alike search inside the secret finder sit on an unpushed branch. core-c has copied them onto a local, unpushed copy of the shared branch. Its test batch has NOT RUN.
- The gate's second round of fixes and the text-folding fixes were committed in commits labelled "work in progress, not verified". The test numbers were measured by core-c's builders only.

### 2.1 Masking before a model call (the gate)

What holds:
- The gate masks values already in the run map, in message text and documents only. It does not mask the system prompt, tool descriptions, the role label, extra message fields, the output format or the route.
- It searches for no new values. Finding them is the secret finder's job.
- If masking fails (text too long, not text, out of time, still changing after 4 rounds), no model call is made and no money is reserved. The refusal carries a code and no text.
- If nothing known is present, the text goes out byte for byte as it came in.
- The gate does not change the caller's messages, documents or run map. Tests check this.
- The caller must name a run map or say "no map" outright. Leaving it out is an error, not a silent skip.
- Evidence: core-c's builder ran 66 deliberate code breaks on the gate files and the tests caught all 66. A later check found 24 of them no longer match the code being edited.

Known gaps:
- **K1.** Not protected: a secret the secret finder never found.
  - Example: a raw `hunter2zz` that no shape matched goes out as written.
  - Status: PINNED. Who acts: nobody; the secret finder is the control.
- **K2.** Not masked even when known: values under 3 characters; all-digit values under 6; common words (`admin`, `test`).
  - Example: names and identifiers touching a letter or digit stay: known `abc123` stays inside `xabc1234`. A 3-character secret follows these rules too. A secret of 4 or more characters is masked everywhere.
  - Status: PINNED. Who acts: nobody.
- **K3.** Not masked: a copy spelled differently from the run map (percent codes, web character codes, look-alike letters, hidden characters, colour codes).
  - Example: known `abc123`, text `abc&#49;23` goes out as written.
  - Status: PINNED. Who acts: nobody; text folding in the secret finder is the control (see K47).
- **K4.** Not masked: the same value in other capital or small letters.
  - Example: known `db01.acme.example`, text `DB01.ACME.EXAMPLE`.
  - Status: PINNED. Who acts: nobody.
- **K5.** Not protected: two known values that overlap. Masking the first hides part of the second, so its rest stays.
  - Example: known `abcd` and `cdef`; text `abcdef` becomes `<SECRET_1>ef`.
  - Status: PINNED. Who acts: nobody.
- **K6.** Not protected: a clean key and a clean value that look sensitive only when joined.
  - Example: `"user_id": "abc123"`, where neither part is in the run map.
  - Status: PINNED. Who acts: nobody.
- **K7.** Not masked: a known value that itself looks like a placeholder or sits in angle brackets.
  - Example: a known value `ab<X_1>cd` goes out as written.
  - Status: PINNED. Who acts: nobody.
- **K8.** Not masked: the system prompt, tool descriptions, role label, extra fields, output format and route.
  - Example: an operator puts a customer's name in the system prompt; it goes out unmasked.
  - Status: PINNED. Who acts: core-b (a start-up check that the system prompt comes only from the prompt list; requested).
- **K9.** Not masked: anything, when "no map" is named (only the test and replay command lines may do this).
  - Example: a replay of an old run sends its text as stored.
  - Status: PINNED. Who acts: nobody.
- **K10.** Not proven: the audit row can say "map in use" when the map was empty or a test replacement was plugged in.
  - Example: a run with an empty map writes the same row as one with 50 values.
  - Status: OPEN, UNVERIFIED. Who acts: core-c (fix being written).
- **K11.** Not protected: a known secret inside a forged tool-result marker. The gate leaves markers untouched.
  - Example: a document holds `<<TOOL RESULT call_id=x_S3cr3tPw_y tool=t>>`; `S3cr3tPw` goes out.
  - Status: OPEN, UNVERIFIED. Who acts: core-c (fix being written, not yet tested). A current test holds the leaking behaviour.
- **K12.** Not protected: a secret placed at a placeholder's edge. Edge values are held back so a placeholder is never cut, and later rounds skip them.
  - Example: known `S3cr3t` and `>abcdef`; text `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`.
  - Status: OPEN, UNVERIFIED. Who acts: core-c.
- **K13.** Not protected: speed. The time and size ceilings are checked after each round, and each message has its own clock.
  - Example: 100 messages could take 100 times the 6-second allowance.
  - Status: OPEN, UNVERIFIED. Who acts: core-c.
- **K14.** Not protected: a run's availability. A planted word equal to a marker word or tool name makes every later tool-using call refuse.
  - Example: a tool result contains `password=RESULT`; the run's later tool calls stop with `framing_refused`.
  - Status: OPEN. Who acts: the lead (decision 1).
- **K15.** Not protected: the line where the model asked for a tool. A planted word can rewrite part of the tool's name there.
  - Example: a document plants `password=logs`; the model then sees two names for one tool call.
  - Status: OPEN, UNVERIFIED. Who acts: core-c.
- **K16.** Not recorded: an interrupt (Ctrl-C) while the gate reserves money or works out the worst case.
  - Example: no audit row is written, and a reservation may stay booked.
  - Status: OPEN, UNVERIFIED. Who acts: core-c (fix being written).
- **K17.** Not safe: two threads writing one run map at once can give one placeholder number to two values.
  - Example: two tools finish together and both values become `<SECRET_3>`.
  - Status: STATED (one writer per map). Who acts: core-b keeps one writer per run map.
- **K18.** Not handled: a gate refusal or a stop leaves the run marked "working" instead of "stopped".
  - Example: the injection check reports a stop as a guard failure.
  - Status: WAITING, UNVERIFIED. Who acts: core-b (install request).
- **K19.** Not through the gate: the separate safety-check call to the cloud vendor's guardrail service. It is neither masked by the gate nor charged to the cap.
  - Example: that call is not limited by the cap.
  - Status: STATED (plan decision). Who acts: nobody.

### 2.2 Spending cap

What holds:
- The gate makes no model call without a reservation. Order: mask, reserve, call, settle, write the audit row.
- A reservation is granted only while the day and month totals stay within the cap and the stop switch is off.
- Tested on core-b's store code, database version 16, Python 3.13: 50 connections asked at once, cap 3.00, worst case 1.00. Exactly 3 were granted, 47 refused. The test ran twice.
- When a reply arrives with a usable cost, the gate settles that real cost.

Known gaps:
- **K20.** Not released: the worst case of a failed call. The connectors cannot yet say "refused before any answer".
  - Example: cap 3.00, worst case 1.00. Three failed calls book 3.00, so the agent is refused for the rest of the day.
  - Status: WAITING (the example is UNVERIFIED: worked out, not run). Who acts: core-b (request written).
- **K21.** Not protected: a reply whose cost field was left empty. It reads as 0 and is settled as free.
  - Example: a connector forgets to fill in the cost; a 0.80 call is booked as 0.00.
  - Status: WAITING, UNVERIFIED. Who acts: core-b (request written).
- **K22.** Not settled: a reply whose cost is missing, negative or not a number. The worst case stays booked (the safe side).
  - Example: a reply reports cost "NaN"; the full 1.00 stays booked.
  - Status: PINNED. Who acts: nobody.
- **K23.** Not counted: earlier attempts of a call that succeeded after retries. Only the last attempt is settled.
  - Example: attempt 1 times out but was billed 0.40; attempt 2 costs 0.30; 0.30 is booked.
  - Status: WAITING, UNVERIFIED. Who acts: core-b (lead's written order).
- **K24.** Not held: the cap, once, for a call that costs more than its worst case. The real cost is booked in full, on purpose.
  - Example: three calls each reserve 1.00 (cap 3.00). One settles at 2.50. Booked: 1.00 + 1.00 + 2.50 = 4.50. All later calls are refused.
  - Status: PINNED. Who acts: core-b (the worst-case formula must cover everything sent).
- **K25.** Not written: the worst-case formula. No function in the code fits the gate today.
  - Example: a formula that ignores documents would make K24 the normal case.
  - Status: WAITING. Who acts: core-b (lead's written order).
- **K26.** Not enforced by the database: the runtime login can rewrite a reserved amount; the purge login can delete an open reservation.
  - Example: faulty code could lower its own reservation.
  - Status: OPEN, UNVERIFIED (read, not run). Who acts: the lead with core-b (decision 5).
- **K27.** Not refused: an out-of-date price table.
  - Example: a vendor raises prices; the worst case is computed at the old price.
  - Status: STATED (plan). Who acts: core-b.
- **K28.** Not capped across processes: the test and replay command lines keep their cap in memory, per process.
  - Example: two replay processes each spend up to the cap.
  - Status: STATED (plan). Who acts: nobody.

### 2.3 Stop switch

What holds:
- While the stop switch is on, every reservation is refused with `kill_switch`, so no model call goes out. This follows from the reservation rule. No end-to-end stop of a live run was tested.

Known gaps:
- **K29.** Not limited by the database: the runtime login can sign a stop with any name; the reset login can change any stop row.
  - Example: a stop row says "by: operator" when the runtime wrote it. Any change the reset login makes reads as "on" (the safe side).
  - Status: OPEN, UNVERIFIED (read, not run). Who acts: the lead with core-b (decision 5).
- **K30.** Not stopped: a call already in flight, and the test and replay command lines (they do not read the switch).
  - Example: a 30-second call started before the stop still completes.
  - Status: STATED (plan). Who acts: nobody.

### 2.4 Audit record

What holds:
- Each gate call writes one audit row: run, kind of action, principal (who asked), result and a code from a fixed list. A test checks that the gate's code holds no logging and no error text.
- If writing the row or settling fails after the reply came back, the reply is still returned.

Known gaps:
- **K31.** Not recorded: whether anything was masked, the route, the model.
  - Example: an investigator cannot tell from the row whether a secret was swapped.
  - Status: OPEN. Who acts: the lead (decision 2).
- **K32.** Not limited: the runtime and reset logins can add any audit row, not only their own kind.
  - Example: faulty reset code could write a row that looks like a model call.
  - Status: OPEN, UNVERIFIED (read, not run). Who acts: the lead with core-b (decision 5).
- **K33.** Not in the record: the test and replay command lines print their audit lines to the screen only.
  - Example: a replay leaves no row in the store.
  - Status: STATED (plan). Who acts: nobody.

### 2.5 The secret finder (what enters the run map)

What holds:
- It finds the kinds it knows: addresses, keys, tokens, e-mail, web-address passwords, command-line passwords, supplier payment details (a bank account beside its bank code).
- One call now masks a bank account beside its bank code, and the part after a known secret inside a longer token (within K36).
- A line it cannot mask in place is withheld whole, with a fixed note.

Known gaps:
- **K34.** Not found: a secret in a shape the finder does not know.
  - Example: an unlabelled 40-character code in plain prose.
  - Status: STATED. Who acts: nobody.
- **K35.** Not masked: a bare number with no label.
  - Example: `ref 55556666 paid`.
  - Status: STATED (by decision). Who acts: nobody.
- **K36.** Not masked: host names with no "host" word in front; a private name with a public ending is masked only in part.
  - Example: `db01.acme.example` stays; `db01.corp.example` becomes `<HOSTNAME_1>.example`. Measured: 28 of 44 test lines leaked.
  - Status: OPEN. Who acts: the lead (decision 3), then core-c.
- **K37.** Not masked: base64 text (a common way of writing data as letters) under 40 characters.
  - Example: a short password written in base64. Measured on the older code: 41 of 41 such lines leaked.
  - Status: OPEN. Who acts: the lead (decision 3), then core-c.
- **K38.** Not masked: an IP address, phone number, bank number (IBAN) or unique id with a letter or `_x` glued behind it.
  - Example: `10.20.30.40_x` is shown whole. Measured on the unpushed branch.
  - Status: OPEN. Who acts: core-c (writes the next work ticket).
- **K39.** Not masked: a value that needs a third search round. The finder does at most two.
  - Example: a bank code glued to a secret, then the account after that code elsewhere. Text must be planted, and the attacker must know the bank code.
  - Status: OPEN. Who acts: core-c (the lead ordered a capped repeat that refuses past its cap).
- **K40.** Not masked: a short tail, up to 7 characters, of a longer token found late.
  - Example: `password=ab9x`, then `Bearer ab9xqrstu`; another copy shows `<SECRET_1>qrstu`.
  - Status: OPEN. Who acts: core-c.
- **K41.** Not bounded: time. A text with one secret takes 2.0 to 2.4 times longer; the time allowance is checked between rounds only.
  - Example: 100,000 characters took 0.206 s before, 0.484 s after (measured). One text may go through the finder up to 7 times.
  - Status: OPEN. Who acts: core-c.
- **K42.** Not masked later: a secret first seen in a tool's error message. It never enters the run map.
  - Example: a tool fails with "bad password hunter2zz"; later results show `hunter2zz`.
  - Status: WAITING, UNVERIFIED. Who acts: core-b (request written).
- **K43.** Not masked: a credential spelled exactly like an escaped placeholder (`‹SECRET_1›`).
  - Example: `password=‹SECRET_1›` stays as written, on purpose.
  - Status: PINNED. Who acts: nobody.
- Fixed in this round (no independent re-review yet):
  - **K44.** FIXED: a secret wrapped in look-alike brackets (`password=‹hunter2zz_1›`) was left readable; it is now masked.
  - **K45.** FIXED for the one caller found (the tool-error path): the finder run on its own output turned real placeholders into new secrets. UNVERIFIED that no other caller does this.
- **K46.** Not masked whole: a secret holding a space, `;`, `,` or `&`. It is masked only up to that character.
  - Example: `password="my secret phrase"` shows `secret phrase`.
  - Status: STATED (existing SECURITY.md text). Who acts: nobody.

### 2.6 Text folding (look-alike and hidden characters)

What holds:
- Before searching, text is folded: look-alike letters, invisible characters and accents become one plain spelling.
- Condition: the program runs on Python 3.13 (see part 3).

Known gaps:
- **K47.** Not on the shared branch: the secret finder's own look-alike search. Today only the injection check (the check for planted instructions) uses folding there.
  - Example: `password=x` written with a Cyrillic "а" relies on that search, which exists only on the unpushed branch.
  - Status: FIXED ON BRANCH. Who acts: core-c (local copy made, test batch NOT RUN, not pushed).
- **K48.** Not decoded by folding: escape codes; look-alikes added after Unicode 15.1 (the character list the folding tables are built from); hidden marks outside two character blocks.
  - Example: `abc1` is not read as `abc1`.
  - Status: STATED. Who acts: nobody.
- **K49.** Not flagged: the Chinese "zero" character inside a Latin word.
  - Example: `pay` + "〇" + `al` is not called mixed script.
  - Status: PINNED. Who acts: nobody.
- **K50.** Not measured: over-matching. A known name can be found inside a longer word.
  - Example: known `Mary` found in `summary`; innocent text may be masked or withheld.
  - Status: OPEN, UNVERIFIED. Who acts: core-c (a measurement is running, no result yet).
- **K51.** Not bounded: folding's own time. The injection check reads up to 2,097,152 characters with no clock.
  - Example: a very large planted text slows the check.
  - Status: OPEN, UNVERIFIED. Who acts: core-c.
- **K52.** Refused, not read: a very long text in Chinese or Japanese only. It is flagged as a guard failure.
  - Example: 300,000 characters of Chinese (measured). Russian prose of that size is read.
  - Status: STATED. Who acts: nobody.
- **K53.** Chosen by the lead: dashes and curly quotes are ordinary punctuation; three slash look-alikes make the line withheld.
  - Example: a value right after an em dash (—) is masked in place; a line with `∕` and a look-alike value is withheld.
  - Status: PINNED (tests on the unpushed branch). Who acts: nobody.
- **K54.** Matches more than before: an invisible character between a Latin letter and its accent. Accepted by the lead.
  - Example: `e` + hidden mark + accent now matches `é`.
  - Status: PINNED. Who acts: nobody.
- **K55.** Not decided: the same wider matching in Korean, Japanese and Indian scripts.
  - Example: a Korean name split by a hidden mark now counts as present.
  - Status: OPEN. Who acts: the lead (decision 4).
- Fixed in this round (no independent re-review yet):
  - **K56.** FIXED: a secret stored as `Müller` but shown with a separate accent mark was no longer masked by the tool-output scrub.
  - **K57.** FIXED: look-alike padding before a 32,768-character boundary could hide "ignore previous instructions" from the injection check.
  - **K58.** FIXED: on the wrong Python, the secrets backend was built before the start-up refusal; the refusal now comes first.

### 2.7 Approval messages

What holds (on the unpushed branch):
- On every path that writes free text for an approval message, the secret finder runs first. Web addresses are made unclickable last (a dot written as `[.]`). 27 path tests.
- A message is re-read until it stops changing, at most 3 times. If it never settles, a fixed note is shown instead.
- An e-mail address with a digit or `_` glued behind it is masked (K61).

Known gaps:
- **K59.** Not masked: the "requested by" line and other id fields; Slack reads them as formatting.
  - Example: a requester id `slack:U1|<!channel>` pings the whole channel.
  - Status: WAITING, UNVERIFIED. Who acts: core-b (request written).
- **K60.** Not proven: "no clickable link remains". The check uses the same patterns as the code it checks.
  - Example: `see/evil.com` may slip past both.
  - Status: OPEN, UNVERIFIED. Who acts: core-c.
- **K61.** Fixed on the unpushed branch: an e-mail address with a digit or `_` glued behind it was shown whole.
  - Example: `anna.m@example.org9` is now masked.
  - Status: FIXED ON BRANCH. Who acts: core-c (land the branch).
- **K62.** Not checked: old stored summaries in the admin console.
  - Example: a summary stored before these fixes may show unmasked there.
  - Status: OPEN, UNVERIFIED (nobody looked). Who acts: core-c.

Measured cost: a 174-character message went from 1.26 ms to 3.60 ms; a 71,179-character message from 367 ms to 655 ms (median, busy machine).

### 2.8 What was not run
- The full test suite. Python 3.12. Database version 17 (the CI uses 17.10). Any live model call.
- An end-to-end stop of a live run. The gate installed at any call point.
- The planned host-name and base64 change (never built). Most deliberate code breaks for text folding (238 of 240).
- The test batch on core-c's local copy of the unpushed work on top of the shared branch.

---

## 3. For README.md: "Python version"

**Operators must run pilot and prod on Python 3.13.** Text folding uses the Unicode character data built into Python. Its tables are built for Unicode 15.1.0, which Python 3.13 carries. Python 3.12 carries Unicode 15.0.0.

What happens on another Python:
- Pilot or prod: the program refuses to start. It stops with the error `UnidataMismatch` before it connects to any secret store or other backend. Nothing runs. This check is not loosened.
- Demo: the program starts. Every folded check name carries a tag with the Unicode version, so a name made on 3.12 never equals one made on 3.13. Do not mix results from the two.
- The project file still allows installing on Python 3.12. A pilot or prod install on 3.12 therefore succeeds and fails only at start.

What is tested on 3.12: the repository has a separate 3.12 test job; it is not a required check. Nothing of this release's text folding, gate or secret finder has been run on 3.12 (NOT RUN). The start-up order test ran on 3.13 with the version faked.

Moving to a later Python (for example 3.14) means rebuilding the character tables, not only changing a version number.

---

## 4. Technical appendix

### 4.1 Key to codes used in the sources
| code | meaning |
|---|---|
| F, G, B, T1 | work packages: F the gate; G the text work; B database rights; T1 the 50-connection cap test |
| G0 | the check-only mask function (later deleted by lead decision) |
| G1 | text folding; G2 approval-message text (old branch P1d-a); G3 the look-alike search ported into the secret finder (old branch P2d-1) |
| G4 | the planned base64 and host-name change (old ticket P1c), not built; G5/G6 docstring wording; G7 the extra search round after the sweep |
| P1a, P1b, P1c, P1d-a, P2d-1 | older input branches and tickets from earlier plans |
| dz, cb | first independent result review of the gate: design reviewer (dz), code reviewer (cb) |
| dz2, cb2 | second independent result review of the gate |
| dz-1 to dz-8, cb-M1 to cb-M4 (G7 review) | independent result review of G7 |
| B1, B2, M3 to M10 (G1 review) | independent result review of text folding |
| M1 to M7, N1 to N8 (G2 review) | independent result review of the approval-message text |
| g4r | plan review of G4 |
| E1 to E7 | entries in ESCALATIONS.md (E7: database rights findings) |
| ORDER nnn | orders from the lead in ORDERS.md |
| MJ-A to MJ-D | Majors of the lead's review round 3 (ORDER 020) |
| T:: / E:: | tests/test_model_gate.py / tests/test_runmap_enforce_map.py |
| sweep | the step that masks every copy of values already in the run map |
| held back | a value skipped by the sweep's first rounds so a placeholder is never cut |
| NO_MAP | the named constant for "no run map" |

### 4.2 Table of known gaps
| gap | evidence | status | who acts |
|---|---|---|---|
| K1 secret not found passes | T::test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job | PINNED | nobody |
| K2 short, digits, common words, touching | E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept; E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept | PINNED | nobody |
| K3 other spellings | T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate; E::test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced; E::test_stated_limit_a_copy_split_by_nul_characters_is_not_found; T::test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced | PINNED | nobody |
| K4 letter case | T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced | PINNED | nobody |
| K5 overlap tail | E::test_stated_limit_partial_overlap_leaves_a_tail; T::test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent | PINNED | nobody |
| K6 joined key and value | T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched | PINNED | nobody |
| K7 placeholder-shaped values | E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced; E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder; E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass | PINNED | nobody |
| K8 fields not masked | T::test_t20_system_and_tools_are_not_touched; T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched; install check asked in requests/3-bind-mapping-required.md section 6 (ORDER 020 MJ-D) | PINNED | core-b |
| K9 no map | T::test_no_map_means_no_enforce_step_at_all | PINNED | nobody |
| K10 audit says map in use | dz2-M5 (reading); fix in core-c's uncommitted working copy; no test result | OPEN, UNVERIFIED | core-c |
| K11 forged marker | dz2-B1 (reading); ORDER 020 MJ-A; committed test T::test_o17_6_a_value_that_only_lies_inside_a_framing_token_leaves_the_token_alone holds the leak and never checks the secret is gone | OPEN, UNVERIFIED | core-c |
| K12 edge value tail | dz2-M2 (reading); no test | OPEN, UNVERIFIED | core-c |
| K13 ceilings not hard | dz2-M3 (reading); ORDER 020 minors; measured only for 100 messages and 2,000 entries (evidence/F-G0-1.md) | OPEN, UNVERIFIED | core-c |
| K14 planted word stops run | T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker (the reproduction); dz2-M4, cb2-M1 (reading) | OPEN | lead |
| K15 tool line rewritten | cb2-M2 (reading) | OPEN, UNVERIFIED | core-c |
| K16 interrupt leaves no row | dz2-M7 (reading); new codes listed in requests/3-bind-mapping-required.md section 6, not tested | OPEN, UNVERIFIED | core-c |
| K17 two writers | none (a race); ticket F stated limits | STATED | core-b |
| K18 run left "working" | F-result-review-2.md call-site list (reading); requests/3-bind-mapping-required.md section 3 | WAITING, UNVERIFIED | core-b |
| K19 vendor guardrail outside gate | plan-v3 call-site table; plan-v4-final B3 | STATED | nobody |
| K20 failed call booked for the day | T::test_pin_an_unmarked_provider_error_is_not_settled; requests/2-refused-before-response.md; interface README 2.1 (expired rows stay booked) | WAITING | core-b |
| K21 empty cost reads as free | models.py line 299 (reading); requests/3-bind-mapping-required.md section 4 | WAITING, UNVERIFIED | core-b |
| K22 unusable cost not settled | T::test_pin_a_reply_with_no_usable_cost_is_not_settled | PINNED | nobody |
| K23 retries settle last attempt | llm/retry.py lines 92-107 (reading, E6 item 3); ORDER 017 item 3 | WAITING, UNVERIFIED | core-b |
| K24 overshoot booked in full | tests/contracts/test_t1_reserve_cap.py::test_a_settle_above_the_reserve_books_the_actual_amount_past_the_cap (core-b 576f292, PostgreSQL 16.15) | PINNED | core-b |
| K25 worst-case formula | ORDER 016c item 13; ticket F "For core-b (install)" item 3; no contract test yet | WAITING | core-b |
| K26 reservation rights | evidence/B-grants-rework.md findings 1 and 2 (read); E7 items 1-2 | OPEN, UNVERIFIED | lead |
| K27 stale price table | plan-v4-final B3 | STATED | core-b |
| K28 in-memory cap on command lines | plan-v4-final B3; interface README 2.1 | STATED | nobody |
| K29 stop-row rights | evidence/B-grants-rework.md findings 3 and 4 (read); E7 items 3-4 | OPEN, UNVERIFIED | lead |
| K30 in-flight call, command lines ignore stop | plan-v4-final B3 | STATED | nobody |
| K31 audit lacks masked flag, route, model | F-result-review-1.md nits | OPEN | lead |
| K32 audit append rights | evidence/B-grants-rework.md finding 5 (read); E7 item 5 | OPEN, UNVERIFIED | lead |
| K33 command lines audit to screen | plan-v4-final B2 | STATED | nobody |
| K34 unknown shape | README "Limits and trust" | STATED | nobody |
| K35 bare number | evidence/P1c-probe.md (24 of 43 not masked) | STATED | nobody |
| K36 host names | evidence/P1c-probe.md (28 of 44 leaked, main code); tickets/G4-review-1.md | OPEN | lead |
| K37 short base64 | evidence/P1c-probe.md (under 40 characters: 41 of 41 leaked; all base64 rows: 52 of 142; main code, not re-measured) | OPEN | lead |
| K38 glued IPv4, phone, IBAN, UUID, host label | evidence/INT-g2-g3.md follow-up (c) | OPEN | core-c |
| K39 third round | tests/test_redact_idempotent_property.py::test_one_pass_is_a_fixed_point_and_leaves_no_raw_copy[constructed:0] (strict expected failure); ORDER 020 MJ-B; DECISIONS.md 07:35 | OPEN | core-c |
| K40 tail up to 7 | tests/test_redact_idempotent_property.py::test_limit_the_tail_of_a_compound_value_found_late_is_not_swept_from_its_other_copies (strict expected failure; its example tail has 5 characters); G7 review dz-2 | OPEN | core-c |
| K41 time 2.0 to 2.4 times | evidence/G7-1.md perf, try 1; G7 review dz-3 | OPEN | core-c |
| K42 tool error not in map | G7 review dz-6 (reading); requests/4-error-reason-run-map.md | WAITING, UNVERIFIED | core-b |
| K43 escaped-placeholder spelling | tests/test_redact_own_output.py::test_only_the_exact_escaped_shape_is_left_alone; tests/test_redact_own_output_hardening.py::test_legitimate_own_output_is_left_alone | PINNED | nobody |
| K44 wrapped secret | tests/test_redact_own_output_hardening.py::test_a_secret_wrapped_in_lookalike_brackets_is_masked (10 failed before the change; commit ab6ff2f) | FIXED | nobody |
| K45 finder on its own output | tests/test_redact_own_output.py::test_the_tool_error_path_adds_no_map_entry_and_keeps_the_escaped_text (8 failed before); caller table in tickets/G7-context-after-sweep.md (reading) | FIXED | nobody |
| K46 space and separators in a secret | SECURITY.md "Stated limits of redaction" | STATED | nobody |
| K47 look-alike search not on shared branch | tests/test_redact_g3_port.py (unpushed branch); G1 review M3 | FIXED ON BRANCH | core-c |
| K48 escapes, newer characters, hidden marks | G1 review (documented limits confirmed by reading) | STATED | nobody |
| K49 Chinese zero in Latin word | tests/test_textnorm_mixed_script_micro.py::test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed | PINNED | nobody |
| K50 over-matching | G1 review M5 (reading) | OPEN, UNVERIFIED | core-c |
| K51 folding has no clock | G1 review M4 (reading) | OPEN, UNVERIFIED | core-c |
| K52 long Chinese or Japanese text | evidence/G1-fold.md "G1 fix round 1", M6 (measured) | STATED | nobody |
| K53 dashes, quotes, slashes | tests/test_redact_g3_port.py::test_typography_an_em_dash_is_ordinary_the_value_beside_it_is_masked_in_the_line, ::test_typography_a_curly_quote_is_ordinary_the_value_inside_the_quotes_is_masked_in_the_line, ::test_typography_the_division_slash_u2215_withholds_a_line_with_a_lookalike_value, ::test_typography_the_box_drawing_diagonal_u2571_withholds_a_line_with_a_lookalike_value, ::test_typography_the_big_solidus_u29f8_withholds_a_line_with_a_lookalike_value (unpushed branch); ORDER 014 item 9 | PINNED | nobody |
| K54 Latin accent matching | tests/test_evidence_decomposed.py::test_known_difference_from_main_an_invisible_character_between_a_letter_and_its_accent_now_joins_them; ORDER 010 item 3 | PINNED | nobody |
| K55 other scripts | G1 review M7 | OPEN | lead |
| K56 undo recombines | tests/test_undo_composes.py (9 of 10 failed before) | FIXED | nobody |
| K57 boundary split | tests/test_injection_chunk_boundary.py (6 failed before) | FIXED | nobody |
| K58 start-up order | tests/test_app_unicode_check_order.py::test_a_wrong_unicode_version_refuses_a_pilot_build_before_any_backend_is_made | FIXED | nobody |
| K59 requested-by line | G2 review M3 (reading); requests/5-card-ids-redact-defang.md | WAITING, UNVERIFIED | core-b |
| K60 link check shares patterns | G2 review M6 (reading) | OPEN, UNVERIFIED | core-c |
| K61 glued e-mail | tests/test_text_parts_together.py::test_glued_email_regression_digit_or_underscore_behind_the_address; tests/test_p1d_a_paths.py::test_glued_addresses_are_masked_whole_in_one_pass (unpushed branch) | FIXED ON BRANCH | core-c |
| K62 admin console | G2 review "not checked" | OPEN, UNVERIFIED | core-c |

State items (not gaps): the gate is not installed: tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered is red on purpose; requests/1-producers.patch; tests/test_gate_install_callers.py holds strict expected failures until core-b installs. The 50-connection test: tests/contracts/test_t1_reserve_cap.py::test_fifty_connections_against_a_cap_of_three_grant_exactly_three. The unpushed branch: evidence/INT-g2-g3.md ("never pushed"), evidence/PICK-int-onto-core-c.md ("batch NOT yet run").

### 4.3 Counts by status (62 gaps)
| status | count | gaps | of these UNVERIFIED |
|---|---|---|---|
| PINNED | 15 | K1-K9, K22, K24, K43, K49, K53, K54 | 0 |
| STATED | 11 | K17, K19, K27, K28, K30, K33, K34, K35, K46, K48, K52 | 0 |
| WAITING (all on core-b) | 7 | K18, K20, K21, K23, K25, K42, K59 | 5 (K18, K21, K23, K42, K59) |
| OPEN, core-c acts | 14 | K10-K13, K15, K16, K38-K41, K50, K51, K60, K62 | 10 |
| OPEN, the lead acts | 8 | K14, K26, K29, K31, K32, K36, K37, K55 | 3 (K26, K29, K32) |
| FIXED | 5 | K44, K45, K56, K57, K58 | 0 |
| FIXED ON BRANCH | 2 | K47, K61 | 0 |
| total | 62 | | 18 |

Two more gaps carry an UNVERIFIED part beside a firm status: K20 (the three-failure example) and K45 (that no other caller exists).

### 4.4 Where two sources disagreed
1. Two sources disagreed about the exemptions for short values. We used the later gate ticket (they do not apply to a secret of 4 or more characters) because it was checked against the sweep's code.
2. Two sources disagreed about settling after a plain connector error (settle 0, or not at all). We used the lead's single settle rule (ORDER 011: not at all) because it replaced the earlier order.
3. Two sources disagreed about a bind without a map (silent skip, or an error). We used ORDER 017 (an error; "no map" must be named) because it is newer.
4. Two sources disagreed about the judge (no map, or the run's map). We used ORDER 017 item 1 (the run's map) because it is newest. The first draft left this unsettled.
5. Two sources disagreed about the tool-error double pass ("harmless" or a gap). We used the G7 review (a gap, K42) because the ticket's author withdrew "harmless".
6. Two sources disagreed about "two search rounds" (per text, or per call) and the tail size (5 or 7). We used the G7 review (per call, up to 7 calls per text; tail up to 7) because it traced the code.
7. Two sources disagreed about escaped look-alikes (any kind exempt, or only the SECRET label). We used the G7 fix evidence (only `‹SECRET_n›` with plain digits) because it is newer and tested.
8. Two sources disagreed about the marker fix (fixed, or leaking). We used the second gate review (leaking, K11, UNVERIFIED) because it is newer and its scenario matches the committed test.
9. Two sources disagreed about the glued-digit e-mail (not fixed, or fixed). We used the integration evidence (FIXED ON BRANCH) because it is newer.
10. Two sources disagreed inside the G2 evidence (two failures, or fixed). We used its fix round (fixed, 7,879 passed) because it comes later in the same file.
11. Two sources disagreed about the spacing-mark test (still red, or decided). We used the integration batch (no such failure) and the G text ticket (lead chose option a) because both are newer.
12. Two sources disagreed about the G1 blockers (being fixed, or fixed). We used the G1 evidence fix round (fixed, tests failed before) because it is newer. No independent re-review exists.
13. Two sources disagreed about whether folding is wired into the secret finder. We used the branch state: only on the unpushed branch (K47). The first draft's summary claimed look-alike text "is found" without this condition.
14. Two sources disagreed about a failed call's booking ("about an hour", or for the day). We used core-b's interface README: the clean-up after 3,600 seconds closes the row but the amount stays booked. The first draft said "about an hour".
15. Two sources disagreed about the dash, quote and slash choice (awaiting the lead, or accepted). We used ORDER 014 item 9 (accepted) because the first draft missed it.
16. Two sources disagreed about the third-round chain (needs the lead, or decided). We used ORDER 020 MJ-B (a capped repeat that refuses) because it is newer.
17. The first draft's overshoot example ("reserve 1.00, settle 2.50 books 4.50") omitted the two other open reservations. The test holds three reservations of 1.00; one settles at 2.50: 1.00 + 1.00 + 2.50 = 4.50. We used the test.
18. Two sources disagreed about base64 counts (41 of 41, or 52 of 142). Both are true: 41 of 41 rows under 40 characters, 52 of 142 rows overall, on the main code.
19. Two sources disagreed about the 3.12 test job (expected green, or a failure). The lead's 3.12 run of old branch P1a had one real failure; the G text ticket reads it as a test slip repaired in the folded code. That repair is UNVERIFIED on a real 3.12.
20. Two sources disagreed about the deliberate code breaks (66 of 66 caught, or 24 stale). Both are true at different times: 66 of 66 on the tree of that run; later edits left 24 search texts unmatched. Not re-run.
21. Two sources disagreed about the planted-word refusal scope. The committed code refuses for any known value equal to a marker word, tool name or call number in a call with framing. Request 3 (07:21) describes a narrower rule being written. We describe the committed code (K14).

### 4.5 Requests to core-b (files in handover/core-c/requests)
1. 1-producers.patch: register the gate as a model caller.
2. 2-refused-before-response.md: the "refused before any answer" mark (K20).
3. 3-bind-mapping-required.md: required map, the gate's refusal type, empty cost, catch sites, install checks (K8, K18, K21).
4. 4-error-reason-run-map.md: tool-error text with the run map (K42).
5. 5-card-ids-redact-defang.md: id fields on approval messages (K59).
Lead's orders to core-b without a request file: sum the cost of all attempts (ORDER 017 item 3, K23); the worst-case formula (ORDER 016c item 13, K25); an operator release for expired reservations (ORDER 017 item 4).

---

## 5. How each review finding was handled

Findings are from tickets/SEC-wording-review-1.md, in its order.

| finding | resolved where / contested why |
|---|---|
| Blocker 1: summary leads with the wrong thing; banner | Part 1 line 1 is the verdict and next step; then not protected, money, weaknesses, decisions, protected. Banner under the part 2 heading. CONTESTED in part: the banner covers the gate module, the secret finder and the store, because the "What holds" items cover all three. |
| Blocker 2: summary does not stand alone; labels undefined | Part 0 glossary before part 1; teams, the lead and the owner introduced. CONTESTED in part: the lead is described as a coordinating session, not a person, because the sources show it messaging session to session. |
| Blocker 3: guarantees stronger than their gaps | Each "What holds" line now names its conditions; "every message and document" now says which fields; look-alike finding moved to K47 with its branch condition; "never writes", "everywhere", "nothing runs" checked against tests or dropped. |
| Blocker 4: self-certifying line | Dropped; replaced by the reading guide at the top. |
| Major: status words used loosely | Five words defined once (part 0); one status per gap; STATED added; FIXED ON BRANCH used for K47, K61; UNVERIFIED removed from measurements and decisions. CONTESTED: K24 stays PINNED, because booking the real cost in full is the design ("overshoot booked in full") and a test holds it. |
| Major: words with two meanings | "model" only for the AI service (connectors renamed); "run" only for a job (code is "agent loop"); "limit" replaced by "known gap", "cap" only for money, "ceiling" for size, "allowance" for time; "mask" versus "find" separated; one name each for gate, run map, secret finder, stop switch; "kit" defined; teams named. |
| Major: undefined labels | Defined in part 0 or moved to the appendix key; refusal codes explained once as exact printed words. |
| Major: internal codes in owner text | Codes moved to part 4; "Disagreements" rewritten as "Two sources disagreed about X. We used Y because Z." (4.4). |
| Major: summary versus body | Decisions counted as seven (1a). CONTESTED in part: the members differ from the reviewer's count, because the lead has since decided dashes and slashes (ORDER 014) and the third-round chain (ORDER 020); the empty-map contest and the Slack file entered. 3.12 wording fixed (part 3); "not masked" used for system prompt with all fields (K8); both cost outcomes shown (K21, K22); the three-failure example marked UNVERIFIED (K20); branch condition added (K47, K61); red test explained (2.0). |
| Major: money wording and arithmetic | "Reservations never pass the cap; booked money can" (summary line 5, K24); 4.50 explained (K24, 4.4 item 17); why overlap and edge leaks happen (K5, K12); 3-character secrets and kinds explained (K2, part 0); marker word and decision 1 explained. |
| Major: README paragraph | Part 3 names operators as the actor, explains the late refusal on a 3.12 install, says what ran on 3.12; editor's note removed. |
| Major: appendix table | Code key (4.1); column renamed "evidence"; full test names; counts by status (4.3); not-gaps moved to "state items"; K21/K22 split; owner column now "who acts". |
| Major: long sentences | Each gap is three short lines; sentences kept to about 30 words. |
| Major: passive voice | Each gap names who acts; the lead places the parts. |
| Major: file status | This file is version 2, marked DRAFT; the "codes only in the appendix" sentence is now true. CONTESTED: the old file is not renamed, because this task changes no other file. |
| Nit: long summary lines | One claim per line where possible. |
| Nit: "text work" undefined | Replaced by named parts. |
| Nit: "NOT RUN" not in the summary | Now in summary line 12. |
| Nit: builder not named | "core-c's builder" named. |
| Nit: "140 tests, later suites" vague | Dropped. |
| Nit: made-up values note | Moved to the reading guide. |
| Nit: defensive caveat with no decision | Dropped. |
