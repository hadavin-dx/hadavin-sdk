# C4 steps versus decisions: exact edit list (round 10; draft by a builder, independent reviewers judge it)

Compared: `inputs/OWNER-STEPS-realrun-v3.md` (193 lines, called OWNER-STEPS below) and `inputs/AGENT-SCOPE-DO-AND-DONT.md` (35 lines, called AGENT-SCOPE) against: (a) the twelve decisions of `inputs/DECISIONS-2026-11-16.md`, cited as D1 to D12 with that file's own numbers (D1 scope and narrow claim; D2 take is read-only, never deletes contacts; D3 proposal of four database users parked; D5 security items, part S9-3 the owner revokes the secret key for the model; D6 ports; D7 first-visit setup done; D8 no extra real smoke; D9 counts proof screen; D10 wording "one Postgres server with two databases", v4 replaces v3; D12 first laptop rehearsal); (b) `inputs/DECISION-one-store.md`; (c) `inputs/FACTS-ALREADY-DONE.md`; (d) plan v5 (`inputs/plan-wp6-resmoke-v5.md`; read: header and change tables, sections 0 to 3, the steps that touch the database, executions and clean-up, sections 5, 8, 9, 10, 11, the UNVERIFIED list and, in rounds 6 and 7, plan lines 14, 76, 81, 102, 121, 477, 489, 492, 502, 505, 506; round 7 also read OWNER-STEPS lines 1 to 26, round 8 also OWNER-STEPS lines 16, 87 and 92, AGENT-SCOPE lines 20 to 28 and plan v5 section 8 and step 3.3, 58, 69 to 92, 99 to 107, 120 to 126 and 176 to 193, AGENT-SCOPE lines 7 to 14 and 24 to 40, DECISION-one-store lines 14 and 20 and DECISIONS-2026-11-16 line 6); (e) seven earlier lead decisions that the C4 brief gave the builder and that are NOT a file in `inputs/`, cited as EL-1 to EL-7: EL-1 one Postgres server for everything we own; EL-2 saved runs ON for the take, deleted at clean-up; EL-3 narrow claim and no portal, approval or audit claim; EL-4 n8n's outgoing traffic is switched off by settings and only observed; EL-5 the tests on this laptop cost US$0 and come before any real take; EL-6 take branches stay on this laptop; EL-7 no real keys, mailboxes or client data for agents, the tests on this laptop and cloud sessions. EL-1 to EL-7 live only in this paragraph (NOT DECIDED 10). Where an EL item and a D item cover the same subject both are cited (EL-3 is also D1). Round 9 also read `ORDERS.md` Q19 to Q34 (the answers of the studio lead of 2026-11-16, quoted as Q19 to Q34 where a row rests on one: Q23 on the contact delete, Q24 on the yes sentence, Q25 and Q26 on the revoke-by time) and the two round-8 reviews. D4 and D11 of the decision file need no row (D4 is about core patches that are not in the take path; D11 is about licence copies in another folder). Nothing was run except text checks; the inputs were not edited.

Round history: rounds 1 to 4 are in `resolve-r1.md` to `resolve-r4.md`; round 5 (`resolve-r5.md`) was reviewed by two independent reviewers (`review-c4-r5-design.md`: 0 Blockers, 4 Majors, 8 Minors; `review-c4-r5-naive.md`: 3 Blockers, 11 Majors, 8 Minors); round 6 (`resolve-r6.md`): `review-c4-r6-design.md` 0 Blockers, 4 Majors, 9 Minors, `review-c4-r6-naive.md` 8 Majors, many Minors; round 7 (`resolve-r7.md`): `review-c4-r7-design.md` 0 Blockers, 3 Majors, 7 Minors, `review-c4-r7-naive.md` 0 Blockers, 8 Majors, many Minors; round 8 (`resolve-r8.md`): `review-c4-r8-design.md` 0 Blockers, 6 Majors, 5 Minors, `review-c4-r8-naive.md` 3 Blockers, many Majors; round 9 (`resolve-r9.md`): `review-c4-r9-design.md` 0 Blockers, 4 Majors, 7 Minors, `review-c4-r9-naive.md` 2 Blockers, 13 Majors, many Minors; round 10 (`resolve-r10.md`, money, secret and delete paths: no round cap) applies all of it, or says why a finding is left. The result of round 10 is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round9.md`.

**Finding ids in the Why lines** name a finding of the review of the round written next to it: "design M1" and "design m1" are the Major and Minor findings of `review-c4-rN-design.md`; "naive A1" (for the studio lead) and "naive B1" (for the owner on take day) are findings of `review-c4-rN-naive.md`; "D-M1" and "D-M5" are findings of round 1 (`review-c4-r1.md`). Q19 to Q34 are answers of the studio lead in `ORDERS.md`.

## Read first (round 10)
- **Apply now** = an instruction to the studio lead: put this text into a working copy of the file named in the row. The original `OWNER-STEPS-realrun-v3.md` stays unedited in `inputs/`; the owner reads the working copy with all Apply now rows applied, and the studio lead names that file.
- **Hold** = do not apply until the named gate is open. **E-nn** = the number of one row of this file. **Conditional** = applies only after a named answer (none today).
- **The studio lead** = the Claude session on the laptop that applies the rows, opens the gates and answers the NOT DECIDED questions; **the owner** = the person. **The assistant** (in owner texts) = Claude working with the owner.
- **builder** = a Claude session that writes or edits text or code; **runner** (evidence runner) = a session that runs tests and saves raw output and never judges; **round** = one pass of independent review followed by one batch of fixes; **re-pin** = the studio lead's step that points the demos at the final commit; **final head** = the newest commit of the take code.
- Studio terms that appear only in notes for the studio lead: `egm:*` = the independent review programs; r17 review = one of them (an earlier one); C4b = the queue item that writes OWNER-STEPS v4; `evidence-2` and its INDEX = the folder where the stand-in test results are written; S9-n = a numbered security item of the decision file; `smk_n8n` = a name in the plan; person A, B, C = the three made-up people the take sends; receiver = the mailbox that receives the take's mails; role = one named set of permissions.
- **Contact id and contact number**: the HubSpot number of one contact. Owner texts say "HubSpot contact number".

## How to read a row (quoting convention, round 6)
Every old text and new text is a block between two lines of four tildes (`~~~~`). The text is EXACTLY the lines inside the block, joined by line breaks, and nothing else: no quotation marks, no backtick padding, no table bars. A backtick or a double quote inside a block is part of the text. A new text of several lines becomes several lines of the file. Old and new texts never start or end with a space. Each old text was checked by script to occur exactly once in its file, on the line stated, and no two old texts on the same line overlap (output in `resolve-r9-check-output.txt`).

**Hold rows (round 9):** the new text of every Hold row is fenced under a label that starts with `NEW [HOLD Gx: DO NOT APPLY]`. A Hold row is never applied until its gate is open, whatever the row's text says.

## Words used in this file and in the owner texts (round 9)
One word keeps one meaning. The owner texts define their words in the list "Words used (read once)" of the sheet (E-52); E-01 only says who "the assistant" is.
- **the assistant** (owner texts) = Claude working with the owner; the sheet's old words "the lead" mean the same (E-01 and E-52 say so inside the sheet). **the lead** inside a quoted AGENT-SCOPE text = the Claude session that leads the work and talks to the owner (E-26 defines it there). **the studio lead** (this file) = the studio lead session that applies the rows, opens the gates and answers the NOT DECIDED items marked "studio lead". Outside the quoted texts this file writes "the studio lead" and never "the lead". "Lead" has five older meanings that this file keeps apart: the Claude session (the assistant), the studio lead, an enquiry (the public post keeps its own word "lead" for it), a "enquiry key" (now: **enquiry key**) and a "table of enquiries" (now: **table of enquiries**); the identifier that the owner chooses for one take is the **take id**, and nothing else is called an id, a tag or a lead id in new texts.
- **enquiry** = one made-up sales message sent through the flows. **contact** = the made-up person an enquiry creates in HubSpot. **enquiry key** = the made-up identifier the program gives an enquiry. **secret key** = a long text that works like a password for a service (HubSpot, the AI model provider); the sheet's old word "token" means the same. **password** = a text a person types (a database user's password, or the app password of a mailbox). Never a bare "key".
- **take** = one real recorded run on the owner's own test accounts (the sheet's "Words used"). **flows** = the automatic step chains that n8n runs. **model stage** = our small program that asks the AI model and enforces the money cap. **saved runs** = the past runs that n8n keeps and lists (n8n itself says "executions"). **preparation** = the last checks the assistant makes before it asks for the owner's yes (Phase 1); it includes the one preparation enquiry (E-49, held; the word is defined in E-49).
- **stand-in test** = the test on this laptop with stand-in programs and made-up data in plan v5 (D8, the loopback re-smoke). **flow rehearsal** = the first run of the changed flows on this laptop that follows it (D12). Both are planned at US$0 (EL-5); nothing about them is proven yet. The word "rehearsal" alone is not used in new texts.
- **counting check** = a small program of ours, not part of n8n, that counts mails, contacts and table rows. It is the one phrase used for this in E-15, E-18, E-31 and E-36. It has no read-only database user of its own (that user is not built; D3 parks it), so it is not claimed to be independent.
- **database server** = the one Postgres program in one **container**; **n8n's own database** and **the take's database** = the two databases on it; **database user** = a Postgres account. **login** = only a mailbox or HubSpot sign-in. (The decision file calls the parked proposal "four logins"; this file says "the proposal of four database users".)
- **spending window** = the last day and time the model stage may spend money, 2026-11-23 18:29 UTC = 23:59 IST (the sheet's old words: "window end"). The **last time to revoke** the secret key for the model is 2026-11-23 18:19 UTC = 23:49 IST (Q25: at least 10 minutes before the stop; to revoke is to delete it at the company that issued it, so that it stops working). **latest start time** = the latest time the take program accepts a start, about 18:14 UTC = 23:44 IST on that day (a reading of OWNER-STEPS line 171, UNVERIFIED by code).
- **Plan codes** (studio notes only; never put one in owner text): **DM** = the plan's row where n8n is killed while the mail is stored (a crash between sending the mail and recording in the take's database that it was sent). **crash case 1** = the plan's case "mail stored, reply held back" (the plan calls it E); **crash case 1, repeat** = the one repeat of it (the plan calls it E2). **NC** = the plan's row that lists the crash windows no test covers. **L4** = the plan's row for the read-only counting user (not built). **P14** = the plan's item "Windows browser reaches n8n inside WSL". **Step 1.2b** = the plan step that writes n8n's database settings; **S1b** and **step 1b** = the plan step that creates the database users, the two databases and the table; **step 2.7** = the plan check that every n8n table sits in n8n's own database; **step 12.5 and 12.5b** = the plan checks of `.n8n/config` and of the saved runs. **EG** = the plan's name for the list of n8n settings that switch off outgoing traffic. **Step 3.3** = the plan step that starts the model stage for the stand-in test against the stand-in model server on port 48767 with a made-up `stage.key`. **Plan UNVERIFIED item 1 and 4** = the plan's own list at its end (section "UNVERIFIED in this plan").

## Gates (a row marked Hold is NOT applied until its gate is open)
**Key (read first).** **ND** = a NOT DECIDED item (numbered 1 to 13 in the list below the gates). **Apply now** = the studio lead applies the row today to a working copy of the file named in the row (OWNER-STEPS v3, AGENT-SCOPE, DECISION-one-store). **Hold** = not applied until its gate is open. **Conditional** = applies only after a named answer (none today). **NEEDS-STUDIO-LEAD** = only the studio lead can supply the missing input; it is in none of the six inputs. **G1 to G5** = the five gates below. The "needs" column of the index names what a row waits for or depends on.
- **G1, the take program makes no delete call to HubSpot (E-04, E-05, E-40, E-41, E-42, E-44, E-45; carried into E-12, E-37 and E-56)**: D2 says the take never deletes contacts. Whether the code at the final head contains a delete call is NOT SETTLED (Q23): an earlier reading found one (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, `review-codebase-1.md` F-01); the r17 review (egm reviewer, 11:00Z) found no delete or archive path (only a GET, `rows_with_prefix`); line 1051 is UNVERIFIED stale text; the HubSpot key is not widened; the studio lead shows the final head's grep at re-pin. The gate is opened by the STUDIO LEAD (never by the builder and never by the owner) by writing the line `CODE-GATE G1 OPEN: <final head commit id>, <evidence file name>, route 1|2` into the newest checkpoint note, and only when all three hold: (1) one of two routes is shown by saved raw output: route 1, a delete call exists at the final head and a commit removes it, shown by a test that fails on the old code and passes on the new; route 2, no delete call exists, shown by the saved raw search of the final head (the Q23 grep: command and output) and a saved raw test output in which a fake HubSpot records every call the end-of-take step makes and none is a delete; (2) the same evidence shows the notice and the list the rows describe, or the studio lead lists the rows whose wording differs; (3) independent `egm:*` reviewers have read the diff (if any) and the output and their saved report lists no open Blocker or Major (delete and money path: no round cap). If OWNER-STEPS v3 or v4 is issued before the line exists, these rows stay unapplied and no paid take starts. E-12 (fact 4 of the request for your yes), E-37 (one bullet) and E-56 (one flag) carry this gate into text that is applied now: the assistant cannot state fact 4 until the line exists, so it cannot send the request. **When G1 opens, the studio lead applies E-04, E-05, E-40, E-41, E-42, E-44 and E-45 together and deletes the bullet "NOT SETTLED, BEFORE ANY TAKE" of E-37 and the leading bullet that E-56 put in front of AGENT-SCOPE line 20** (rule R9). Whether the code prints the list of leftover contacts by enquiry key and contact id is UNVERIFIED.
- **G2, later wording only, Windows reaching n8n in WSL (E-07, E-08)**: E-07 and E-08 are Apply now with neutral words. G2 only decides a second wording: opened by the studio lead after reading the first-smoke evidence for plan item P14; the studio lead writes `ND5: proven <file>` or `ND5: not proven <file>`; if proven, the second wording in the Why of E-07 and E-08 replaces the neutral one.
- **G3, second edit pass (E-13)**: opened by the studio lead when the stand-in test result file (in `evidence-2`, its INDEX) exists and independent reviewers have read it; the studio lead writes the report name.
- **G4, saved-runs method (E-39)**: opened when NOT DECIDED 3 is answered (the answer decides the text).
- **G5, the preparation enquiry (E-49, E-50, E-53)**: the one made-up enquiry through the real accounts is not allowed by any scope row today (AGENT-SCOPE line 27 forbids a real key and answering a prompt), the route is not decided (NOT DECIDED 8) and nothing proves that a paid model call is impossible there (NOT DECIDED 6). Opened by the STUDIO LEAD only, by writing `GATE G5 OPEN: ND8 <A|B>, ND6 <A <evidence file>|B <owner message>>` into `ANSWERS-c4.md`, and only when both hold: (1) NOT DECIDED 8 is answered; (2) NOT DECIDED 6 is answered, and for A a saved raw test output shows the model stage started with the stand-in model and a made-up key file, read by independent `egm:*` reviewers whose saved report lists no open Blocker or Major (money path: no round cap). When G5 opens, the studio lead applies E-49, E-50 and E-53 together (rule R8); E-53 is not a condition of the gate. E-49 and E-53 are written for route B of NOT DECIDED 8; if the answer is A, the studio lead first rewrites item (a) of E-49 and does not apply E-53. The owner's consent for the enquiry is the written line `Yes, send the one enquiry on <day>` (E-49, E-53). While G5 is closed no preparation enquiry is sent (safe default; D8's "one made-up lead" is then not done and the take rests on the tests). E-11 and E-12 contain nothing of G5, so they apply now.

## How the rows are used
**What "Apply now" means.** OWNER-STEPS v3 is archived, never edited or deleted (D10). The OWNER-STEPS rows are an edit list for a working copy of v3 (the studio lead names the file; the original stays unedited) and for OWNER-STEPS v4 (queue item C4b), which replaces v3 and keeps only what is still owner-only. An **Apply now** row is applied TODAY to the working copy of v3, so that v3 is safe to read even if v4 is late; the same text is then carried into v4. A row about a step that v4 strips (Phase 0 steps 1 to 7 and 9, perhaps step 8) falls away there: that is E-04 (step 7), E-06, E-07, E-08 (step 8) and E-37 (the note in front of Phase 0). E-09 does NOT fall away: it is the only place that says how the password file is made, so v4 carries it. Everything else (Phase 1, steps 16 to 23, the status lists) stays in v4. The old advice "if v3 is read before v4 exists, apply only E-37 and E-52" is withdrawn: apply every Apply now row to v3 (E-37 needs E-12, because it points to the request for your yes that E-12 describes). When v4 is issued is NOT DECIDED 12 (no input gives a date); until it is issued, v3 plus the Apply now rows is what the owner reads. The AGENT-SCOPE rows patch that file in place; the DECISION-one-store rows (E-39, E-43, E-46, E-47) are applied by the studio lead (the file is in `inputs/`; E-39 changes the written record of an owner approval and is held). Ids are not renumbered: E-10 was deleted in round 3 (D7) and E-35 in round 5 (its content is part of E-34), so the ids run E-01 to E-56 without E-10 and E-35 (E-49 to E-53 are new in round 8, E-54 in round 9, E-55 and E-56 in round 10).

## Counts (computed by script, `resolve-r10.md` and `resolve-r10-check-output.txt`)
54 rows in total: E-01 to E-56 without E-10 and E-35. By file: OWNER-STEPS 35 rows, AGENT-SCOPE 15 rows, DECISION-one-store 4 rows (the studio lead applies those). By status: **Apply now 42**, **Hold 12** (G1: E-04 E-05 E-40 E-41 E-42 E-44 E-45, G3: E-13, G4: E-39, G5: E-49 E-50 E-53; the Hold rows are E-04, E-05, E-13, E-39, E-40, E-41, E-42, E-44, E-45, E-49, E-50, E-53), **Conditional 0**; total 54. The Apply now ids (42) are: E-01, E-02, E-03, E-06, E-07, E-08, E-09, E-11, E-12, E-14, E-15, E-16, E-17, E-18, E-19, E-20, E-21, E-22, E-23, E-24, E-25, E-26, E-27, E-28, E-29, E-30, E-31, E-32, E-33, E-34, E-36, E-37, E-38, E-43, E-46, E-47, E-48, E-51, E-52, E-54, E-55, E-56. Round 10 added E-55 (the heading of step 22) and E-56 (a flag in front of AGENT-SCOPE line 20 while gate G1 is closed), rewrote E-09, E-11, E-12, E-13, E-14, E-16, E-39 and E-48. Round 9 added E-54 (the Phase 1 heading), rewrote E-09 as sub-steps, split E-11 into a structural control, and put a `[HOLD Gx: DO NOT APPLY]` label on every held NEW text. Among the Apply now rows, E-36 has two texts (text W is live, text N is labelled DO NOT APPLY) and E-07 and E-08 apply their neutral wording (gate G2 only decides a second wording). By type: STALE 15, UNCLEAR WORD 10, MISSING STEP 14, CONTRADICTION 14 (including the rows marked as code-change gated), DEFERRED 1 (E-13); total 54.

## NOT DECIDED: studio lead or owner only (items 1 to 13). Each item says who answers, the options with cost and risk, the default, and where the answer is written
Where answers are recorded: the studio lead creates `steps-edits/ANSWERS-c4.md` and writes one line per answer: `ND<number>: <answer>, <who>, <date and time in UTC and IST>` (for the owner's answers the line quotes his message). Until a line exists the default applies.
1. **Where the password of n8n's database user (a line in `n8n.env`) is kept, so that the assistant never opens secret files** (E-09, E-30). Who answers: the studio lead. Premise not verified: D3 parks the proposal of four database users, so whether n8n gets its own database user or shares one is UNVERIFIED (DECISION-one-store line 20), and nothing read proves that the start script supports options b and c. Options: (a) the owner types the password himself into `n8n.env` in WSL, in an editor and NOT on a command line (a command line is saved in the shell history), and the assistant never opens the file (no code change; the assistant cannot check the value; risk: a typing slip stops n8n and delays the take); (b) the start script asks for the password at the keyboard each time, hidden as you type and NOT as a word on the command line (a code change in a script that handles a secret: it needs independent review with no round cap; the password is in no file; risk: the assistant cannot start n8n alone); (c) the start script writes a random password into a file readable only by its owner that nobody reads (a code change in a script that handles a secret: independent review with no round cap; no human password; risk: the file is a secret on disk until clean-up). Cost: assistant time only, no money. Default: (a); E-09 says that the owner types the table user's password into a password file (steps a to e) and n8n's own database user's password as one line of `n8n.env` (step g), and that the assistant opens neither (the programs that read them are UNVERIFIED); E-09 writes its steps with the placeholders `<password file name>`, `<folder>` and `<database user name>`, which this item and item 4 fill; the prompt of (b) and the file of (c) are unproven code changes and appear in no owner text unless this item is answered b or c. Pass or fail for (a): n8n starts and the assistant's own check shows that n8n can open its database (the assistant sees only "ok" or "not ok", never the password). Record: `ND1: a|b|c`.
2. **The address (port number) of the real take's n8n** (E-06). Who answers: the studio lead. D6: it uses its own free port, not 5678 or 5679 (your own n8n) and not the ports of plan v5 section 2 (5690 to 5693, 8765, 48767, 8771, 2526, 55433); the number is in no document. Answer: one free port number, written in the plan's port table and in the answers file. No cost. Default: until answered, the assistant names the port in its message that says n8n is running (E-06 and E-07 say "the address the assistant gives you for the take's n8n"); the studio lead then writes it into the plan's port table and the answers file. Record: `ND2: <number>`.
3. **How saved runs are deleted at the real take** (E-16, E-38, E-39). Who answers: the studio lead for (a); the owner's one-line yes is needed for (b), because (b) is not the step he approved. Facts: plan v5 line 81 says the real-take method is undecided (the stand-in test uses container removal); line 502 lists it as not proven. Options: (a) turn the saving setting off, delete the runs, then remove the container (matches the approved owner decision; a few minutes of assistant time; a deletion step that can fail); (b) only remove the container (one step; less proof that the runs are gone before the container goes; not the approved wording). Default: until answered, E-16 and E-38 keep the approved step and name container removal as the stand-in test's method only, and E-39 is not applied (texts per answer are in E-39). Owner's answer text for (b): `Yes, remove the container only` (the question and the exact reply are in E-16; no reply counts as No); the studio lead records it with the owner's written message. Record: `ND3: a|b <owner message>`.
4. **Which database user's password the owner types for the n8n table steps** (E-09). Who answers: the studio lead names the database user (never the password); the owner types its password. Only one option is allowed: the table user (the database user the take's table steps use: plan v5 section 10 points to it; planned as a restricted user, not yet proven; the plan calls it the table user). NOT allowed, because of least privilege: the administrator of the database server; n8n's own database user (it belongs to n8n's own database, not to the table of enquiries); the read-only counting user (not built; D3 parks it). Default: the table user. Pass or fail: as for ND1 (a). Record: `ND4: <user name>`.
5. **Windows reaching n8n in WSL (E-07, E-08; plan item P14).** Who answers: the studio lead. The plan says it was proven in the first smoke; nobody on this branch has read that evidence. Action: the studio lead reads the first-smoke evidence for item P14 and writes `proven` or `not proven` with the file name (opens gate G2). E-07 and E-08 are already applied with neutral words; G2 only chooses a second wording and is moot if v4 drops step 8. Record: `ND5: proven|not proven <file>`.
6. **Money: how a paid model call is made impossible in the tests and in the preparation enquiry (E-11, E-49, E-53).** Who answers: the studio lead for option A (it needs evidence, not a guess); the owner only for option B. Facts: for the tests on this laptop a paid call is excluded by the ABSENCE of the real key, and since round 9 E-11 makes that a structural control for both tests (the model stage starts only with the stand-in model address on this laptop, 127.0.0.1, and a key file in the test's own folder; the assistant names both and waits for the owner's written reply): the assistant never opens the secret folders (OWNER-STEPS rule 2) and AGENT-SCOPE line 27 gives it no real key; plan v5 step 3.3 starts the model stage for the stand-in test against the stand-in model server with a made-up `stage.key`. UNVERIFIED: that the flow rehearsal and the preparation enquiry can start the stage the same way, and that the stage accepts a made-up key value outside the stand-in test. "Stop and ask" is not a control and is not used as one. Option A: the stage is started with the stand-in model and a made-up key file, shown by one saved raw test output that independent reviewers have read; cost US$0; risk: the preparation enquiry then does not exercise the real model path. Option B: ONE paid call, outside the take's 3 calls (D8 does not say it is paid and no input describes a separate consent), under the same US$ cap and window end. Owner's answer text for B: `Yes, ONE paid model call in the preparation test, up to US$<one figure the assistant states>, outside the 3 calls of the take, same cap, spending window ends 2026-11-23 18:29 UTC = 23:59 IST.` The studio lead's task for B: take the per-call worst-case figure from the stage settings (as for step 16) and give it to the assistant to state. Cost: US$0 for A; that one figure for B; risk of B: money spent before the take. Default: neither is proven, so gate G5 stays closed and NO preparation enquiry is sent. Record: `ND6: A <evidence file>` or `ND6: B <owner message>`.
7. **Are the keys dedicated and of the right scope?** Who answers: the owner, in one line each (or the assistant checks the key lists with him). In plain words: (a) "Is the secret key for the model that you saved one that you made only for this take, and does nothing else use it?" The owner replies `yes`, `no, other things use it` or `not sure`; the studio lead records `7a: yes` / `7a: no, others use it` / `7a: not sure`. (FACTS names a "new key 2026-11-13"; revoking a shared secret key at clean-up (E-48) would break the other things.) (b) "In HubSpot, Private Apps: does app 1 show only the permission contacts read (no write, no delete), and does app 2 exist?" The owner replies in plain words; the studio lead records `7b: app 1 read-only, app 2 exists` / `7b: no` / `7b: not sure`. ("Scope" means the list of things a key is allowed to do. FACTS says only "key given", and the keys were "already used in earlier local runs", so the permissions are unknown.) Cost of a wrong answer: a full-permission HubSpot secret key used by the take breaks the least-privilege rule; a shared secret key for the model revoked by mistake breaks other work. Default: unanswered counts as "not sure" (a failed confirmation means no yes to the take: E-04, E-37): E-48 still applies, with its safe default (the assistant asks the owner at clean-up whether to revoke; the owner revokes only after a clear yes, and the second ask comes before 18:19 UTC = 23:49 IST) and E-04 and E-37 keep the assistant's confirmation step. Record: `ND7a:` and `ND7b:` lines.
8. **How the one made-up preparation enquiry reaches your throwaway accounts (E-49, E-50, E-53).** Who answers: the studio lead; the owner only if money is involved (ND6). No input says which way it goes in, no AGENT-SCOPE row allows either way until E-53 is applied, and nothing shows whether it counts against the take's 3 model calls, its spend ledger and its journal (UNVERIFIED). Options: (A) through the take program: the owner types `y`, the confirmation number and the take id himself (AGENT-SCOPE line 27 forbids the assistant from answering those prompts), and the single-use take id and the notice are spent on the preparation; risk: the real take then needs a new take id and notice; the take program also posts its own three people, not one enquiry (OWNER-STEPS Words used), so route A cannot send ONE enquiry without a code change; (B) the assistant posts the enquiry straight to the take's own n8n web address on this laptop, only after the owner's written `Yes, send the one enquiry on <day>` (E-49, E-53); n8n then uses the credentials you typed into it, the assistant holds no real secret key and answers no prompt; risk: the take program's ledger and journal are bypassed unless the flow writes them (UNVERIFIED). E-53 is the AGENT-SCOPE MAY and MUST NOT pair for B. Cost: assistant time; no money unless ND6 is B. Default: nothing is sent (gate G5 closed). Record: `ND8: A|B <date and time in UTC and IST>`.
9. **How `.n8n/config` is removed at clean-up: plain `rm` or `shred -u`** (E-30). Who answers: the studio lead. Facts: the file holds n8n's encryption key, readable only by its owner; the plan removes it with the take folder by a plain delete and gives no reason for or against `shred -u`; `shred -u` is used today only for the secret files in `~/take-secrets` that the owner deletes (step 22 item 6). A wipe is not reliable on every disk type, so it adds little on a journaling or flash disk (UNVERIFIED for this laptop). Options: (a) plain `rm` with the take folder (no change; the key stays in free disk space until overwritten; the key belongs to a throwaway n8n); (b) `shred -u` for that one file first (one more step; may fail on a read-only or special disk). Cost: assistant time only. Default: (a). Record: `ND9: a|b`.
10. **Checks only the studio lead can make, because the source is not in this folder** (E-31, the first paragraph). (i) EL-1 to EL-7 against the C4 brief (they are only in the first paragraph of this file; if one is wrong, the rows that cite it change: EL-1: E-09, E-27, E-30; EL-2: E-14, E-16, E-38; EL-3: E-17, E-18; EL-4: E-18, E-29, E-34; EL-5: E-03, E-12; EL-6: E-23, E-34; EL-7: confirmation a). (ii) Finding M-1 of `review-codebase-1.md` (the table named without its schema), taken from earlier drafts as quoted in AGENT-SCOPE line 20. Who answers: the studio lead. Default: the texts stay as written and are marked UNVERIFIED in the owner-facing text where they appear. Record: `ND10: EL ok|EL wrong <items>; M-1 ok|M-1 differs <file>`.
11. **The text of the owner's security rules A, E, F and I (decision D5, items S9-5 and S9-12).** Who answers: the studio lead supplies the text (it is in none of the six inputs). Missing input, exact: the four rule texts. Partly covered today: OWNER-STEPS rules 1 and 2 and AGENT-SCOPE line 25 (never read the secret folders). Default: no row is written (a row would be a guess); when the text is supplied, one AGENT-SCOPE MUST NOT row is written. Record: `ND11: <file name>`.
12. **When OWNER-STEPS v4 is issued, and what "Apply now" does until then** (all OWNER-STEPS rows). Who answers: the studio lead. No input gives a date or a condition for v4 (queue item C4b; "tonight" in earlier drafts was a guess). Options: (a) issue v4 only after the Apply now rows are applied and the gates G1 and G5 are decided (v3 plus the rows is what the owner reads meanwhile); (b) issue v4 first and apply the rows to it only (v3 stays as it is and is unsafe to read: it still says "archived" and shows the old yes example). Cost: studio lead time only. Default: (a). Record: `ND12: a|b <date and time in UTC and IST>`.
13. **Words in OWNER-STEPS v3 that no row touches** (naive B16 of round 8). Examples: "plan-4 N-lite" (lines 1 and 133), the older word "the stage" (line 12), "smoke" (line 7) and the old second yes example of step 16 (line 92: "You answer in one line, for example: ..."; E-12 gives one example, E-12 now includes that old sentence in its old text and replaces it). Who answers: the studio lead. Options: (a) leave the words and rely on E-01 and E-52, which name the older words and their meaning; (b) one more row each (more rows, more review). Default: (a) for the words; the old second example is replaced by E-12 itself, so the studio lead deletes nothing by hand. Record: `ND13: a|b`.

## FOR THE STUDIO LEAD TO CONFIRM (a reading or a source, not a decision; letters run a to j without gaps)
a. EL-7 read literally ("no real keys, mailboxes or client data") would void the real take's throwaway Gmail accounts, the HubSpot test account and the secret key for the model. FACTS-ALREADY-DONE.md and AGENT-SCOPE lines 27 and 32 show it applies to agents, the tests on this laptop and cloud sessions, not to the owner's own approved take accounts. Edits are made on that reading.
b. E-36: do the mail count and the contact count really run on credentials of their own (only the table count runs as one database user through `docker exec psql`)? Answer yes or no. Default no: text W is applied; yes: text N replaces it before the post is written.
c. E-23, E-34: EL-6 (take branches stay on this laptop) is in no input file; the plan only says the runner never commits, pushes or merges (plan v5 line 489). The rows follow that plan wording; add a rule about cloud sessions only if you confirm EL-6.
d. E-12 (the assistant's message and the owner's yes state four facts: both tests ran with counts, where the written result is, that independent reviewers read it, that the last step of the take program makes no delete call to HubSpot (gate G1; Q23); a fifth fact about the preparation enquiry is E-50, held; and what "passed" means, with the plan's one exception for a crash check that was "missed" twice) is gating wording that follows EL-5, D12 and plan lines 14 and 505 but is not literal in them; confirm it. The gate "no paid take starts before independent reviewers have read the result" (plan line 505) is not owner text on its own. E-14 (do not film the mail step) rests on a guess about what the saved mail step shows and stays flagged.
e. E-37: whether step 8 is wholly obsolete, and whether the take's own n8n needs the three credentials typed by the owner (FACTS says they are in the owner's own n8n on port 5678, which the take never touches; the plan gives the take a fresh n8n). Until confirmed, E-37 tells the owner not to do step 8 unless asked.
f. Whether the plan's step S1b and row L4 (the database users) still run, given D3.
g. The fourth saved credential: E-09 step f says the owner types the table user's password into n8n's form for a Postgres credential, besides HubSpot, the model and Gmail (plan v5 lines 223 and 505). OWNER-STEPS line 121 (step 22 item 1) and E-37 say "three credentials". Is it four, and does step 22 item 1 say four?
h. E-12 and E-48: on 23 Nov the assistant asks for no start later than 18:04 UTC = 23:34 IST (the program itself accepts about 18:14 UTC = 23:44 IST, UNVERIFIED), and if a take is still running at 18:19 UTC = 23:49 IST the owner revokes the model key anyway unless the assistant says otherwise. Both are the builder's choices from Q25. Confirm or change.
i. Q22(c) ("item 1 wording plus one honest sentence that a gap longer than the lease is not claimed") is in ORDERS as an answer about the v19 hand-off item 8. Round 10 did NOT add a lease sentence to the public post of E-17: no input says the post concerns a lease. If the studio lead means the post, the exact sentence is needed.
j. E-56 puts the UNVERIFIED flag as a bullet in front of AGENT-SCOPE line 20 because an edit inside the clause would overlap the held rows E-40 and E-44. Confirm that placement, or name another.

Removed in round 3 (each was answered by a decision, or is not for the studio lead): old item 1 (HubSpot app 1 and the delete right: D2); item 2 (kept above as confirmation a); item 5 (real-account smoke: D8); item 6 (first-visit setup: D7; row E-10 deleted); item 8 (proof screen: D9); item 9 (two meanings of "round": plan v5 line 76, see E-02); item 10 (wording: D10); item 11 (filming the mail step: the owner's request for your yes, see E-14 and R5); item 12 (rewrite of Phase 0: v4 replaces v3, D10 and queue item C4b). From the first draft: the fill-step question (E-33), the second edit pass after the run (now E-13), and the clean-up method for saved runs (now NOT DECIDED 3; plan v5 lines 81 and 502).

## Rules for the studio lead (round 9)
Where the evidence is: the stand-in test's results are written into the INDEX of `evidence-2` (plan v5 line 477, row NC; line 505, row DM). Who judges: independent `egm:*` reviewers read them (plan line 505), never the runner and never the builder. "Passed" is as defined in E-12.
- **R1 (E-17)**: after the stand-in test, delete the clause "a crash at exactly the moment between sending the mail and recording in the take's database that it was sent may send the mail twice" only if plan row DM PASSED (no row with two mails) AND (crash case 1 passed or crash case 1, repeat passed, not both missed) AND independent reviewers have read the INDEX; if DM was not tested, was missed, or showed two mails, keep the clause. When it is deleted the studio lead also updates E-22's sentence on line 166 and E-25 item 18.
- **R2 (E-18)**: drop only the narrow item "that the counting check is independent", and only when the read-only count user (plan row L4) is built and its run is shown in the INDEX and read by independent reviewers. The item "that the take is crash-safe" is NOT dropped while plan row NC lists crash windows that no test covers (before the claim; after the model call and before the contact is written; and the mail window if DM was missed); "crash-safe" stays forbidden. All other items stay.
- **R3 (E-36)**: text W applies by default; text N applies only if confirmation b is answered yes.
- **R4 (E-39)**: not applied tonight; when NOT DECIDED 3 is answered, apply the text for that answer (E-39 gives text per answer, with the follow-on for E-16 and E-38). The record of the owner approval itself is never rewritten.
- **R5 (E-14)**: apply as written. If the owner wants the mail step filmed, he says so in his written reply to the request for your yes; the assistant then reads what the mail step shows in the stand-in test before it is filmed.
- **R6 (E-12, E-37)**: before the assistant sends the request for your yes (step 16), the studio lead checks that the files named in the four facts exist (five once gate G5 is open), that the list of checks is attached, that the latest start time and the spending window are stated in UTC and IST, that the reviewers' report lists no open Blocker or Major, that the line `CODE-GATE G1 OPEN: ...` exists and that the rows of gate G1 (E-04, E-05, E-41, E-42) are applied. If any is missing, the request is not sent. This check does not replace the owner's: the owner answers no to a message that lacks a fact (E-12).
- **R7 (E-48)**: if the owner answers "no" or "not sure" at clean-up, the assistant asks once more before 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 (the last time to revoke, Q25; the spending window itself ends 18:29 UTC = 23:59 IST) and the studio lead writes the outcome into `ANSWERS-c4.md` as `ND7a-late: <answer>, <date and time in UTC and IST>`; an unrevoked key is listed in the handoff with that date.
- **R8 (E-49, E-50, E-53)**: when gate G5 opens the studio lead applies E-49, E-50 and E-53 together, then R6 checks five facts. If G5 never opens, nobody sends a preparation enquiry.
- **R9 (E-04, E-05, E-40, E-41, E-42, E-44, E-45, E-37, E-56)**: when gate G1 opens, apply E-04, E-05, E-40, E-41, E-42, E-44 and E-45 together and delete the bullet "NOT SETTLED, BEFORE ANY TAKE" of E-37 and the flag bullet of E-56 (they are true only until then). Before that, no one writes that the take program deletes contacts or that it no longer does (Q23).

## Decision D5 (security items S9-1 to S9-5, S9-12): where each one stands (round 9)
- S9-3 (the owner revokes the model secret key at clean-up): E-48 (applies always, with the safe default question; the second ask and the last time to revoke are 18:19 UTC = 23:49 IST).
- S9-2 (the owner compares the settings-file figures by eye; the program does not print them): E-51 adds the honest sentence that the program does not print the two values (D5's statement; no code was read). Round 7 wrote "no row needed"; that was wrong because OWNER-STEPS rule 4 and step 16 say "a backstop that you check by eye" and not that the program prints nothing.
- S9-5 and S9-12 ("apply as text": rules A, E, F, I are not overridable in the middle of a take; the assistant reads only masked take outputs and never the owner-only secret or real-run folders): NEEDS-STUDIO-LEAD, NOT DECIDED 11. Not fixable from this folder: the text of rules A, E, F and I is in none of the six inputs. Partly covered today: OWNER-STEPS rules 1 and 2 and AGENT-SCOPE line 25.
- S9-1 and S9-4 (need program code): D5 defers them as describe-only. D5 forbids the claim "nothing can spend before both typed answers" unless a closed gate exists; round 7 and round 8 searched OWNER-STEPS for that claim and found none (command: grep "nothing can spend": no match).

## The edit index (no texts here; the texts are in the row blocks below)
| id | file | line | status | gate | needs | type |
|---|---|---|---|---|---|---|
| E-01 | OWNER-STEPS-realrun-v3.md | 3 | Apply now | - | E-52 | STALE |
| E-02 | OWNER-STEPS-realrun-v3.md | 3 | Apply now | - | - | UNCLEAR WORD |
| E-03 | OWNER-STEPS-realrun-v3.md | 5 | Apply now | - | - | MISSING STEP |
| E-04 | OWNER-STEPS-realrun-v3.md | 69 | Hold | G1 | G1, ND7b | CONTRADICTION (code-change gate) |
| E-05 | OWNER-STEPS-realrun-v3.md | 95 | Hold | G1 | G1 | CONTRADICTION (code-change gate) |
| E-06 | OWNER-STEPS-realrun-v3.md | 75 | Apply now | - | ND2 (the number) | CONTRADICTION |
| E-07 | OWNER-STEPS-realrun-v3.md | 75 | Apply now | G2 (second wording only) | ND2, ND5 (second wording only) | UNCLEAR WORD |
| E-08 | OWNER-STEPS-realrun-v3.md | 187 | Apply now | G2 (second wording only) | ND5 (second wording only) | UNCLEAR WORD |
| E-09 | OWNER-STEPS-realrun-v3.md | 78 | Apply now | - | ND1, ND4 (placeholders) | UNCLEAR WORD |
| E-11 | OWNER-STEPS-realrun-v3.md | 87 | Apply now | - | ND6 (flow rehearsal set-up) | CONTRADICTION |
| E-12 | OWNER-STEPS-realrun-v3.md | 92 | Apply now | - | G1 line before the message is sent; E-37 | MISSING STEP |
| E-13 | OWNER-STEPS-realrun-v3.md | 99 (and 11) | Hold | G3 | G3, stand-in test result (method) | DEFERRED |
| E-14 | OWNER-STEPS-realrun-v3.md | 107 | Apply now | - | - | UNCLEAR WORD |
| E-15 | OWNER-STEPS-realrun-v3.md | 107 | Apply now | - | - | CONTRADICTION |
| E-16 | OWNER-STEPS-realrun-v3.md | 121 | Apply now | - | ND3 (default text) | STALE |
| E-17 | OWNER-STEPS-realrun-v3.md | 131 | Apply now | - | - | CONTRADICTION |
| E-18 | OWNER-STEPS-realrun-v3.md | 131 | Apply now | - | - | MISSING STEP |
| E-19 | OWNER-STEPS-realrun-v3.md | 159 | Apply now | - | - | STALE |
| E-20 | OWNER-STEPS-realrun-v3.md | 162 | Apply now | - | - | STALE |
| E-21 | OWNER-STEPS-realrun-v3.md | 164 | Apply now | - | - | STALE |
| E-22 | OWNER-STEPS-realrun-v3.md | 166 | Apply now | - | - | MISSING STEP |
| E-23 | OWNER-STEPS-realrun-v3.md | 151 | Apply now | - | - | STALE |
| E-24 | OWNER-STEPS-realrun-v3.md | 178 | Apply now | - | E-25 | STALE |
| E-25 | OWNER-STEPS-realrun-v3.md | 193 | Apply now | - | E-24 | MISSING STEP |
| E-26 | AGENT-SCOPE-DO-AND-DONT.md | 2 | Apply now | - | - | STALE |
| E-27 | AGENT-SCOPE-DO-AND-DONT.md | 5 | Apply now | - | - | CONTRADICTION |
| E-28 | AGENT-SCOPE-DO-AND-DONT.md | 9 | Apply now | - | - | STALE |
| E-29 | AGENT-SCOPE-DO-AND-DONT.md | 9 | Apply now | - | - | MISSING STEP |
| E-30 | AGENT-SCOPE-DO-AND-DONT.md | 7 | Apply now | - | ND1, ND9 | MISSING STEP |
| E-31 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Apply now | - | ND10 | MISSING STEP |
| E-32 | AGENT-SCOPE-DO-AND-DONT.md | 23 | Apply now | - | - | STALE |
| E-33 | AGENT-SCOPE-DO-AND-DONT.md | 23 | Apply now | - | - | UNCLEAR WORD |
| E-34 | AGENT-SCOPE-DO-AND-DONT.md | 27 | Apply now | - | confirmation c | MISSING STEP |
| E-36 | OWNER-STEPS-realrun-v3.md | 131 | Apply now | - | confirmation b | CONTRADICTION |
| E-37 | OWNER-STEPS-realrun-v3.md | 27 | Apply now | - | E-12; G1 (one bullet); ND7 | STALE |
| E-38 | AGENT-SCOPE-DO-AND-DONT.md | 9 | Apply now | - | ND3 (default text) | STALE |
| E-39 | DECISION-one-store.md | 23 | Hold | G4 | ND3, G4 | STALE |
| E-40 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Hold | G1 | G1 | CONTRADICTION |
| E-41 | OWNER-STEPS-realrun-v3.md | 103 | Hold | G1 | G1 | CONTRADICTION (code-change gate) |
| E-42 | OWNER-STEPS-realrun-v3.md | 104 | Hold | G1 | G1 | CONTRADICTION (code-change gate) |
| E-43 | DECISION-one-store.md | 14 | Apply now | - | - | UNCLEAR WORD |
| E-44 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Hold | G1 | G1 | CONTRADICTION |
| E-45 | AGENT-SCOPE-DO-AND-DONT.md | 23 | Hold | G1 | G1 | STALE |
| E-46 | DECISION-one-store.md | 14 | Apply now | - | - | STALE |
| E-47 | DECISION-one-store.md | 1 | Apply now | - | - | UNCLEAR WORD |
| E-48 | OWNER-STEPS-realrun-v3.md | 123 | Apply now | - | ND7a | MISSING STEP |
| E-49 | OWNER-STEPS-realrun-v3.md | 87 | Hold | G5 | G5, ND6, ND8, E-50, E-53 | MISSING STEP |
| E-50 | OWNER-STEPS-realrun-v3.md | 92 | Hold | G5 | G5, E-49, E-53 | MISSING STEP |
| E-51 | OWNER-STEPS-realrun-v3.md | 92 | Apply now | - | - | MISSING STEP |
| E-52 | OWNER-STEPS-realrun-v3.md | 16 | Apply now | - | - | UNCLEAR WORD |
| E-53 | AGENT-SCOPE-DO-AND-DONT.md | 28 | Hold | G5 | G5, ND8, E-49, E-50 | MISSING STEP |
| E-54 | OWNER-STEPS-realrun-v3.md | 85 | Apply now | - | - | UNCLEAR WORD |
| E-55 | OWNER-STEPS-realrun-v3.md | 119 | Apply now | - | E-48 | CONTRADICTION |
| E-56 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Apply now | G1 (the studio lead deletes it when G1 opens) | E-40, E-44 | CONTRADICTION |

## The row blocks
### E-01: OWNER-STEPS-realrun-v3.md, line 3, status Apply now, type STALE
OLD (exact):
~~~~
wt\nlite-int`).
~~~~
NEW (exact):
~~~~
wt\nlite-int`). Edited on Mon 16 Nov 2026 to follow the plan for the stand-in test (version 5) and the decisions of 2026-11-16. This edit is still to be checked by a second person; what is still to be checked in the facts is listed at the end of this file under UNVERIFIED. In the edited parts, "the assistant" is Claude, who works with you; the older parts of this sheet call the same helper "the lead". The older parts also call an enquiry a "lead" and the table of enquiries the "table of leads". The other new words are explained in the list "Words used" below.
~~~~
Why: Plan v5 header (pinned head is a temporary choice; later fix rounds in progress). Round 8 (naive minor: the glossary was one 400-word block that did not define n8n, "HubSpot private app" or "take program"): the glossary moves out of line 3 into the existing list "Words used (read once)" as separate lines (E-52); line 3 now only says who "the assistant" is and where the other words are. "Edited ... still to be checked" stays (E-07, E-08, E-13 and E-36 are not verified against code). The personal folder path is not copied: the old text stops at the closing bracket. E-02 follows in the same line and does not overlap. Round 9 (naive A5, five meanings of "lead"): the older words "lead", "lead key" and "table of leads" are named in this line so that the owner knows they mean "enquiry", "enquiry key" and "table of enquiries".

### E-02: OWNER-STEPS-realrun-v3.md, line 3, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
Independent review rounds 3 to 9 of the code are done; this file itself got a drift review (drift-report-1) and is corrected to it.
~~~~
NEW (exact):
~~~~
Independent reviews of the code (review rounds 3 to 9) are done. Later fix rounds (batches of code changes made after the reviews): fix rounds 3 and 4 are on the branches `take/nlite-int-r3` and `take/nlite-int-r4`, and fix round 5 is being built on `take/nlite-int-r5` (a branch is a named copy of the code). Which code is under test is named in one place, at the top of the plan for the stand-in test, and that choice is not final. This file itself got a drift review (a check that its text still matches the code and the notes; the report is named drift-report-1) and is corrected to it.
~~~~
Why: Plan v5 header and line 76 use "round" for review rounds and for fix rounds; one word keeps one meaning. Round 7 (naive minor): the old text now runs to the full stop of the sentence, so the new text ends with a full stop too (round 6 left the stop out on purpose and that was easy to paste wrongly); the nested brackets are split into short sentences. The old text was read in `OWNER-STEPS-realrun-v3.md` line 3 by eye: after it comes " Replaces `OWNER-STEPS-realrun.md` (v2" (checked by script that the old text occurs once). AGENT-SCOPE lines 16 and 22 keep their own dates and are read as review rounds. Round 9 (naive B14): the wording of fix rounds now agrees with E-23 (rounds 3 and 4 exist, round 5 is being built); "drift review" and "drift-report-1" are explained in one clause.

### E-03: OWNER-STEPS-realrun-v3.md, line 5, status Apply now, type MISSING STEP
OLD (exact):
~~~~
The lead does everything else (start the database, the model stage and n8n, import the flows, run the checks). The exact commands for the lead are in `egm\duplicate-proof-lead-desk\nlite\WP6-RUNBOOK.md`.
~~~~
NEW (exact):
~~~~
The assistant does everything else (start the database server, the model stage and n8n, import the flows, run the checks). The assistant keeps the exact commands in its own run book; you do not need it.

Before any real take the assistant runs two tests on this laptop. Both are planned at US$0, and nothing about them is proven yet:
- The stand-in test uses stand-in programs and made-up data only. No real account, no real secret key and no paid model call are planned. What n8n sends over the network is watched, not blocked, so we do not claim that nothing leaves the laptop.
- The flow rehearsal comes after the stand-in test has passed: the changed flows are run once on this laptop with made-up data, also planned at US$0.

The take is planned to keep its data in Postgres (a free database program). This is planned, not yet proven: in the first trial n8n kept its data in a simpler one-file database. One Postgres program, called the database server, is planned to run in one container (a sealed box in which a program runs) and to hold two separate databases: n8n's own database (flows, saved credentials, saved runs) and the take's database (our table of enquiries).

You do nothing for the two tests unless the assistant asks you, for example to start Docker Desktop (the program that runs containers). Blocking the network would need a Windows firewall rule (a setting that stops a program from using the network), which only you could set; none is planned.
~~~~
Why: EL-5 (the tests cost US$0 and come before any real take), D8 and D12. Round 7 (design M-A, design m6, naive minors): the Postgres design is stated as "planned, not yet proven" (E-25 item 15, E-27, E-28 and ND1 say the same; smoke-1 ran SQLite), and the flow rehearsal is "planned at US$0" (no input proves the cost; EL-5 gives it as a decision). The one long paragraph is split into short parts; the old text now runs to the end of line 5 so that the new text can end with its own line. The glossary words "take", "flows" and "model stage" are defined in E-01 on line 3, before this line. "the lead" becomes "the assistant" in the two places of the old text (E-01 says why). Plan line 102: network use is OBSERVED, not ENFORCED, so that sentence is limited to the stand-in test (what the flow rehearsal watches is not stated in any input). Plan P-4 and line 506: Docker Desktop is started by the assistant or the owner; a firewall rule is only option (c) of line 506 and none is planned. Whether the flow rehearsal also uses only stand-in programs is UNVERIFIED in the inputs; EL-5 gives only its cost. The file name `WP6-RUNBOOK.md` was already in the old text (it is a file name, not a code word in a sentence); the studio lead may replace it when v4 is written. Round 8 (naive minor): the studio file name and its folder path are removed from the owner text; the owner does not need the run book, so one plain sentence replaces them. Round 9 (naive B14): "saved passwords" becomes "saved credentials" (a credential is one saved access setting in n8n; E-52 defines it), so "password" keeps one meaning (something a person types).

### E-04: OWNER-STEPS-realrun-v3.md, line 69, status Hold (gate G1), type CONTRADICTION (code-change gate)
OLD (exact):
~~~~
the file name is yours, you tell the lead the path, never the content.)
~~~~
NEW [HOLD G1: DO NOT APPLY] (exact):
~~~~
the file name is yours, you tell the assistant the path, never the content.) Keep app 1 read only: the take program never removes contacts (decision of 16 Nov 2026). Before the take the assistant asks you three questions about HubSpot, and you answer in plain words (it never asks for the secret key itself). (1) Open app 1 in the HubSpot website (Settings, Integrations, Private Apps, then the name of app 1) and tell the assistant which permissions it shows (HubSpot calls the list of things an app may do its "scopes"); the only one allowed is reading contacts. (2) Tell the assistant whether app 2 exists. (3) Tell the assistant which of the two apps you took the secret key from (do not show the key or the file). If an answer is "no" or "not sure", or app 1 shows more than reading contacts, you do not say yes to the take: the assistant tells you what to change in the HubSpot website, you change it, and the assistant asks again. After the take you delete this take's contacts by hand in the HubSpot website. The assistant gives you the list: the enquiry key of each contact and its HubSpot contact number, if the program printed them; otherwise the made-up names to look for
~~~~
Why: The decision of 2026-11-16 (item 2) is that the take is read-only and never deletes contacts; the owner deletes leftovers by hand. FACTS-ALREADY-DONE.md line 3 says only "HubSpot test account, users created, key given": it does not say that app 1 or app 2 exist or what the saved key can do, so the assistant asks (NOT DECIDED 7b). Round 9: (a) naive B3: the new sentences now sit AFTER the sentence about the file path (round 8 put them before "Copy the token"), they name what to open and what to answer ("secret key" for the old word "token"; "scopes", "HubSpot website" and "contact number" are explained), and an answer "no" or "not sure" means no yes to the take; (b) premise: round 8 said that today's code removes contacts. The studio lead's answer Q23 says that is NOT settled: an earlier reading found a delete, the r17 review found none. This row therefore states only the decision (the take never removes contacts) and does not claim anything about the code. Why held (gate G1): the decision is only true for the take once the final code is shown to make no delete call (gate G1 gives two ways to show it). The old text now ends at the closing bracket of the path sentence; the words "tell the lead" become "tell the assistant" (E-01, E-52). Missing input (exact), why the row is held: the line `CODE-GATE G1 OPEN: <final head commit id>, <evidence file name>, route 1|2`.

### E-05: OWNER-STEPS-realrun-v3.md, line 95, status Hold (gate G1), type CONTRADICTION (code-change gate)
OLD (exact):
~~~~
up to 3 contacts archived at the end
~~~~
NEW [HOLD G1: DO NOT APPLY] (exact):
~~~~
up to 3 contacts created in HubSpot and left there (the take program removes none; you delete them by hand afterwards)
~~~~
Why: The decision of 2026-11-16 (item 2): the take never deletes contacts. The old words "archived at the end" are the notice text that an earlier reading tied to a delete call (AGENT-SCOPE line 20); a later review found no delete path, and Q23 says this is not settled, so this row claims nothing about the code. Gate G1 (final head shown to make no delete call): the notice the program prints must say the same as the new text, so apply the text only after the final code's notice is read; its exact words are UNVERIFIED (the studio lead quotes them from the evidence file). The same word on OWNER-STEPS lines 103 and 104 is handled in E-41 and E-42; Gmail's "Archive it" on line 50 is a different thing and stays. Round 7: "made-up" is dropped because "contacts" is now defined (E-01) as made-up people. Round 9: premise changed as stated (Q23). Apply together with E-04, E-41 and E-42 when G1 opens.

### E-06: OWNER-STEPS-realrun-v3.md, line 75, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
the address the lead gives (it should be `http://localhost:5678` or similar;
~~~~
NEW (exact):
~~~~
the address the assistant gives (it is NOT `http://localhost:5678`, which is your own n8n and which the take does not touch; the take's n8n has an address of its own, the same kind of web address with a different number after the colon, called the port number; the assistant tells you the whole address;
~~~~
Why: Plan v5 section 2 ports and D6 (the decision of 2026-11-16, item 6): the take n8n uses its own free port; 5678 and 5679 are the owner's own n8n. The number is in no document (NOT DECIDED 2). Round 9 (naive B7): "port number" is explained in the text; the old words "the address the lead gives" are now inside the old text and become "the address the assistant gives", so the sentence has one helper name. The old and new texts both stop at the semicolon; the one space that follows it stays, so the next words (E-07's text) read on correctly. If v4 drops step 8 this row falls away.

### E-07: OWNER-STEPS-realrun-v3.md, line 75, status Apply now (a second wording follows only after gate G2), type UNCLEAR WORD
OLD (exact):
~~~~
UNVERIFIED that Windows reaches WSL there, WP6 check (e))
~~~~
NEW (exact):
~~~~
it is not yet confirmed that your Windows browser can open the address the assistant gives you for the take's n8n. n8n runs inside WSL, the Linux part of your laptop (WSL). The assistant checks this with you before you type anything. If your browser cannot open the address, stop, tell the assistant, and type nothing until the assistant says the address works)
~~~~
Why: Round 7 (naive major: a held E-07 left "there" without a referent and shipped "WP6", "WSL" and "UNVERIFIED" to the owner). The neutral text says only what is true today: not yet confirmed. Round 8 (naive major 1): "that address" is replaced by "the address the assistant gives you for the take's n8n". Plan v5 section 0 says the Windows reach to n8n in WSL was proven in the first smoke (plan item P14, the plan's number for "Windows browser reaches n8n inside WSL"); nobody on this branch read that evidence (NOT DECIDED 5). Second text (apply only when the studio lead writes `ND5: proven <file>`, gate G2): "the first smoke showed that your Windows browser can open the address the assistant gives you for the take's n8n; the assistant checks it again with you before you type anything)". If `not proven`, keep the neutral text. The old text begins right after E-06's semicolon-and-space and ends the sentence's bracket; E-06 and E-07 do not overlap (checked by script). Round 9 (naive B7): the text now says what the owner does if the browser cannot open the address. Gate display (design M5): this row is Apply now with the neutral text; gate G2 decides only the SECOND wording, so the index shows "G2 (second wording only)". Second text (apply only when the studio lead writes `ND5: proven <file>`): "the first smoke showed that your Windows browser can open the address the assistant gives you for the take's n8n. The assistant checks it again with you before you type anything)". If v4 drops step 8 this row falls away.

### E-08: OWNER-STEPS-realrun-v3.md, line 187, status Apply now (a second wording follows only after gate G2), type UNCLEAR WORD
OLD (exact):
~~~~
8. The Windows browser reaching n8n in WSL at localhost.
~~~~
NEW (exact):
~~~~
8. Whether the Windows browser can open the address that the assistant gives for n8n. n8n runs inside WSL, the Linux part of the laptop (WSL). The plan says the first smoke showed it, and nobody has read that evidence yet.
~~~~
Why: Round 7 (naive: the row was not applicable without guessing). The old item is a bare label; the new text says what is unverified and why, without guessing the answer. Second text (only after `ND5: proven <file>`, gate G2): the same item with the end "(the first smoke showed it once; the assistant checks it again at the take)". If v4 drops step 8, the item is dropped there. Round 9 (naive minor): the nested bracket is split into short sentences. Gate display as in E-07.

### E-09: OWNER-STEPS-realrun-v3.md, line 78, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
host, database, user as the lead names them; password = the one you set in WSL when you start the database (the lead gives the start command; you type the password).
~~~~
NEW (exact):
~~~~
host, database and user as the assistant names them; password = the password of THAT database user. You create the password file in the sub-steps a to e below. Steps a to e come FIRST: the assistant starts the database server and n8n only after your message "password file created". (A database user is an account inside the database program Postgres. Its password is not an app password and not a secret key.) The assistant starts the database server itself; you do not start anything. The assistant gives you the names `<password file name>`, `<folder>` and `<database user name>` in a message; it never tells you the password.
   a. Before you type any password, ask the assistant to stop looking at your display (the laptop screen) and your clipboard (the place where copied text waits), and wait for its written reply "not looking". This is a promise by the assistant, not a control: nothing in the computer stops it from looking, because it shares your Linux user, your clipboard and your screen, and a file that only you may read (step d) can still be read by the assistant. The same promise is asked again every time you type a password (step f and step g). The assistant looks again only after you write "you may look again".
   b. In WSL (the Linux part of your laptop), open a new empty file in an editor, for example `nano <password file name>`, inside the folder the assistant names (a folder on the Linux disk, never under `/mnt/c/...`).
   c. Type ONE line: the password for the database user named in the message. Make it at least 20 letters and digits, used nowhere else and different from the password of n8n's own database user. Save the file and close the editor. Never type the password as a word inside a command line, because the shell saves every command line in a history list.
   d. Run `chmod 600 <password file name>` (this keeps other Linux users out; it does not keep the assistant out).
   e. Write to the assistant: "password file created", the file's path and "you may look again". Never write the password or the content of the file. The assistant does not open the file; the program that starts the database server is planned to read the password from that file (not yet proven). If the assistant tells you that the program cannot read it, you type the password nowhere else until the assistant tells you how.
   f. Later, when n8n is running, the assistant tells you when to type the SAME password into n8n's form for the saved credential of the take's database. This is a fourth saved credential, besides HubSpot, the model and Gmail. Repeat step a first (ask, wait for "not looking"), type it, then write "you may look again".
   g. A second password belongs to n8n's own database user. It is one line in the file `n8n.env`. The assistant tells you the name of that line and the folder; you repeat steps a to e for that one line (another password, at least 20 letters and digits, used nowhere else), and the assistant does not open `n8n.env`. How n8n and the database server then get that password is planned, not yet proven.
~~~~
Why: EL-1 and DECISION-one-store decision 1 (the wording of decision 10): one database server, two databases. The owner types and keeps the password (OWNER-STEPS rule 2); the assistant names only the database user (NOT DECIDED 4: one allowed option, the table user); where n8n's own database user's password is kept is NOT DECIDED 1. The proposal of four database users is parked (decision 3), so the privileges stay "planned and not yet proven". Round 9 (naive B1): the 250-word paragraph is steps a to f; the file name, folder and database user name are PLACEHOLDERS (they depend on NOT DECIDED 1 and 4). Round 10 (naive B2, design m1, m2): (a) step a now says plainly that it is a promise and not a control (Q24: the assistant shares the owner's Linux user, clipboard and screen; chmod 600 does not hide the file from the assistant) and has a "you may look again" signal; the promise applies to every typing of a password (f and g); (b) steps a to e come before the database server and n8n start (the row sits in step 8, which opens "when n8n is running"; the first sentences say so); (c) reconciled with NOT DECIDED 1 default a: the table user's password is in the password file (steps a to e, then typed into n8n's form, step f); n8n's own database user's password is one line of `n8n.env` (step g), typed by the owner; how the start program or n8n reads them is UNVERIFIED (NOT DECIDED 1; the text says "planned, not yet proven"); (d) the fourth saved credential is stated: plan v5 line 223 (`fill_flows.py`: flows Postgres credential = `smk_app` with `pg-app.pw`) and line 505 (the Postgres credential set to the table user) show that the flows hold a Postgres credential besides HubSpot, the model and Gmail; E-37 says the same; whether step 22 item 1 ("the 3 credentials") must say four is FOR THE STUDIO LEAD TO CONFIRM g; (e) this row does NOT fall away if v4 drops step 8: it is the only place that tells how the password file is made, so v4 carries it (see "How the rows are used"). "Login" means a mailbox or HubSpot sign-in only.

### E-11: OWNER-STEPS-realrun-v3.md, line 87, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
The lead runs the checks (a) to (f) of the smoke (WP6-RUNBOOK) with NO paid call. If a check fails the lead tells you what to change.
~~~~
NEW (exact):
~~~~
The assistant first runs the stand-in test and then the flow rehearsal on this laptop, with made-up data and no paid model call. Both tests are planned at US$0, and nothing about either is proven yet. The stand-in test is planned to use no real account; for the flow rehearsal that is not yet confirmed.
How the assistant keeps a paid call out. This is a procedure that the assistant follows. The program does not enforce it, and nothing here proves that the assistant follows it. For each of the two tests the assistant starts the model stage only with these two things:
- The web address of the stand-in model (a small fake program on this laptop). It must be exactly `127.0.0.1`, a colon and a port number, for example `127.0.0.1:48767`, with nothing before it and nothing after the port number. (127.0.0.1 means this laptop only. A web address such as `127.0.0.1.example.com` is a different address and is not allowed.)
- A secret key file inside the own folder of that test, holding a made-up value.
Before each test the assistant tells you in a message the full web address and the full path of the secret key file, and waits for your written reply. Answer "ok" only if both are right: the web address is exactly `127.0.0.1` plus a port number, and the secret key file is NOT the file you saved for the real take. If either is wrong, answer "no" and say which one. The assistant then does not run the test, tells you what it will change, and asks again.
Your "ok" is about what the assistant says it will start. Nothing here checks what it really started. The assistant never starts the model stage with the path of the real secret key file and never opens that file (rule 2 above). If the assistant cannot set up a test this way, it does not run that test. It is also not proven that the model stage accepts a made-up key value and a stand-in web address outside the stand-in test; if it does not, the assistant tells you before it runs the flow rehearsal. If a check fails the assistant tells you what to change.
~~~~
Why: D8 (the decision of 2026-11-16, item 8): the real-account smoke (checks a to f) is replaced by the tests on this laptop plus ONE made-up enquiry in take preparation; D12: the flow rehearsal follows the stand-in test; EL-5: the tests cost US$0. Round 8 (design Major 1): E-11 applies only the laptop tests; the preparation enquiry is E-49 (held, gate G5). Round 9: "no paid call" was not a control (a stage started with `--key-file <real path>` opens it, and a wrong model address is a paid call), so the assistant NAMES the stand-in address and a key file in the test's own folder and WAITS for the owner's written reply. Round 10 (design M3, naive B1, naive M10): (a) the claim "a control that does not depend on anyone's care" is dropped: it is a procedure the assistant follows, nothing in code enforces it, and the text says so; (b) the owner's "ok" covers BOTH the web address and the key file, before EACH test (round 9 covered only the key file, before the flow rehearsal); (c) the address is exactly 127.0.0.1 plus a port ("starts with 127.0.0.1" would let `127.0.0.1.example.com` pass); (d) the refusal reply is given ("no", and which one); (e) the owner is told that "ok" says what the assistant intends, not what it did; (f) the cost is stated ONCE the same way in E-03, E-11 and E-52 ("both planned at US$0, nothing proven; the stand-in test planned to use no real account, the flow rehearsal not yet confirmed"). The model stage accepting a made-up key value and a stand-in address outside the stand-in test is UNVERIFIED (NOT DECIDED 6) and the owner text says so. The old text ends at "change." and the file's next sentence ("You may be asked to confirm what a screen shows.") stays; E-49 anchors on it. Pass and fail of the tests are those of the request for your yes (E-12).

### E-12: OWNER-STEPS-realrun-v3.md, line 92, status Apply now, type MISSING STEP
OLD (exact):
~~~~
You answer in one line, for example: "Yes, take <tag>, up to 3 calls and up to US$X, window ends 2026-11-23 23:59 IST." A yes covers ONE take.
~~~~
NEW (exact):
~~~~
A yes covers ONE take. Before you say yes, the assistant sends you one message, called the request for your yes, and it must contain all of the following. If any one is missing, you answer no.
- Four facts, each with the name of the file that shows it:
  1. The stand-in test and the flow rehearsal have been run, and how their checks ended, in numbers. The form is: "stand-in test: N1 pass, 0 missed, 0 not run; flow rehearsal: N2 pass, 0 missed, 0 not run". N1 and N2 are the numbers of checks on the list of each test. "Missed" means the check could not see what it was looking for. "Not run" means the check was never carried out.
  2. The file where their written result is saved.
  3. Reviewers who are not the assistant (separate review programs, named in their own report) have read that result, and the file where their report is saved.
  4. The last step of the take program makes no delete call to HubSpot. The assistant names its evidence: either a saved search of the final code that finds no delete call, or the commit (the name of one saved version of the code) that removes it with the saved test output; and the reviewers' report that read it.
- The list of checks of the plan, attached to the request.
- The last day and the latest start time, in UTC and IST. The take is planned for Wed 18 Nov 2026: the request states the planned start time and the latest start time the assistant will accept that day. Mon 23 Nov 2026 is the LAST day on which a take may run, because the spending window ends on that day at 18:29 UTC = 23:59 IST (after that the model stage may not spend money; the older text calls it "the window end"). No take is planned for 23 Nov. If the assistant asks for one that day, it asks for no start later than 18:04 UTC = 23:34 IST, so that the take is over before 18:19 UTC = 23:49 IST, the last time to revoke the secret key for the model (step 22). The take program itself accepts a start until about 18:14 UTC = 23:44 IST, because it needs about 14 minutes; that figure is a reading of step 17 and is not checked in the code.
"Passed" means both of these: every check ended "pass", and the reviewers left no finding open. A check that ended "missed" or "not run" is not a pass, and then you do not say yes and the take does not go ahead; the assistant tells you what happens next. There is ONE exception, the check of a crash between sending the mail and recording in the take's database that it was sent. The plan runs it a second time if the first run ended "missed". If both runs ended "missed", that check counts as "crash check untested" (it is not counted as missed): the request must say "crash check untested" in these words, the take may go ahead on your yes, and you must not post that the take is crash-safe. (Crash-safe means: the take survives a crash at any moment without a double mail or a lost enquiry.)
Your reply is ONE line that you type in the chat. Copy this form, replace every part in angle brackets and keep the rest as written: "Yes, take <take id>; stand-in test <N1> pass, 0 missed, 0 not run; flow rehearsal <N2> pass, 0 missed, 0 not run; crash check <tested or untested>; result in <result file>; reviewers' report <report file>; no delete call to HubSpot, evidence <evidence file>; up to 3 model calls and up to US$<X>; spending window ends 2026-11-23 18:29 UTC = 23:59 IST; latest start <latest start time in UTC and IST>; I know that the assistant shares my Linux user, my clipboard and my screen."
- `<take id>` is the short name you chose for this take. `<N1>` and `<N2>` are the two numbers in the request. `<tested or untested>`: write `tested`, or `untested` only if the request says "crash check untested". The three file names are copied from the request. `<X>` is the dollar figure that the request gives as 3 times the worst case per call. `<latest start time in UTC and IST>` is copied from the request.
- The last part, "I know that the assistant shares my Linux user, my clipboard and my screen.", is REQUIRED. Without it the assistant does not start the take.
You are the one who answers no: answer no if the request leaves out a fact, a file name or the list of checks, or says that anything did not pass. If a part of your reply is missing or wrong, the assistant does not start the take and tells you which part. The assistant does not start the take on anything but your written reply in this form. You may ask the assistant to show a named result file or report file in the chat; it never shows a secret file (`n8n.env`, a key file, a password file).
~~~~
Why: EL-5 and D12: the tests come before any real take; plan line 505 requires independent egm:* reviewers to read the result before any owner-facing claim. Round 7: the owner is the one who answers no. Round 8: fact 5 (the preparation enquiry) is E-50 (held). Round 9: fact 4 says "no delete call" and names the evidence (Q23: not settled); the crash-check exception is the ONLY exception; N1 and N2; "missed" and "not run" defined; no offer to show a secret file; the yes carries the sentence that the assistant shares the owner's Linux user, clipboard and screen (Q24). Round 10: (a) design M2: the old text now includes the second yes example of line 92 ("You answer in one line, for example: ... window ends 2026-11-23 23:59 IST."), so that sentence is REPLACED by this row; it had no UTC time, no files and no "no delete call" fact, and an owner could have copied it into a yes that contradicts this row (NOT DECIDED 13 no longer needs the studio lead to delete it by hand); (b) naive M2: the assistant's message is "the request for your yes" and the owner's answer is "your reply" (the old words "request for your yes" meant both); (c) naive M3: the reply is ONE line to copy, with every placeholder explained, the closing sentence marked REQUIRED, a slot for the crash check (`tested` or `untested`) and the latest start time as a slot; (d) naive M3, naive M5, design m4: the last day (23 Nov) and the latest start time for the planned day (Wed 18 Nov) are stated in UTC and IST; the 18:14 UTC = 23:44 IST start that the program accepts leaves too little time before the last time to revoke (18:19 UTC = 23:49 IST, Q25), so for 23 Nov the assistant asks for no start later than 18:04 UTC = 23:34 IST (18:19 minus about 14 minutes 20 seconds, the program's own 860 seconds); that is the builder's reading, to be confirmed (FOR THE STUDIO LEAD TO CONFIRM h); Q25 also says no take on 23 Nov unless the studio lead's reading of the final code (Q27) is shown; (e) G1: the request cannot be sent until the line `CODE-GATE G1 OPEN: ...` exists and the rows of gate G1 (E-04, E-05, E-41, E-42) are applied, so steps 17 and 18 no longer say "archived" when fact 4 is read (rule R6 checks both). This is gating wording that follows EL-5, D12 and plan lines 14 and 505 but is not literal in them; the studio lead confirms it (FOR THE STUDIO LEAD TO CONFIRM d). The old text starts after E-51's old text (`... against a second file)` then `; and the planned window end **...**.`) and ends with "A yes covers ONE take."; the file's next sentence ("No numbers in the message means answer no.") still follows; E-50 anchors on it.

### E-13: OWNER-STEPS-realrun-v3.md, line 99 (and 11), status Hold (gate G3), type DEFERRED
OLD 1 (exact):
~~~~
The lead stops and restarts n8n by hand while person C is posted; you do not touch anything.
~~~~
NEW 1 [HOLD G3: DO NOT APPLY] (exact; template, the part in angle brackets is filled from the stand-in test result when gate G3 opens):
~~~~
The assistant stops and restarts n8n <the method named in the stand-in test result> while person C is posted; you do not touch anything.
~~~~
OLD 2 (exact):
~~~~
C is sent once while the lead stops and restarts n8n by hand.
~~~~
NEW 2 [HOLD G3: DO NOT APPLY] (exact; template, as NEW 1):
~~~~
C is sent once while the assistant stops and restarts n8n <the method named in the stand-in test result>.
~~~~
Why: DEFERRED to a second edit pass after the stand-in test. Plan v5 section 10 says OWNER-STEPS lines 75, 99 and 164 to 166 and AGENT-SCOPE lines 7 to 10 are edited again after the test to match its results; the same "by hand" wording on line 11 goes into that pass. The test kills n8n with a held reply, not "by hand". Both old strings occur exactly once, on lines 99 and 11 (checked by script). Round 10 (naive minor: this Hold row had two OLD blocks and no NEW block): the two NEW blocks are written as TEMPLATES under the Hold label; they are not final text because the method is a MISSING INPUT (exact): the stand-in test result (its INDEX in `evidence-2`) that says how n8n is stopped at the real take (by the assistant by hand, or by the program with a held reply). When gate G3 opens the studio lead puts that method in place of the part in angle brackets. Gate G3 is opened by the studio lead (above).

### E-14: OWNER-STEPS-realrun-v3.md, line 107, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
(4) the n8n execution list and execution detail panes: only made-up names and the `take-<id>-a/b/c@example.com` addresses, and not an old execution
~~~~
NEW (exact):
~~~~
(4) the n8n list of saved runs (the past runs that n8n keeps): only made-up names and the `take-<id>-a/b/c@example.com` mail addresses, and no run from before this take. By default do not open or film the detail of the mail step of a run: it may show the company mail address and the sender mail address. You decide what is filmed (rule 5: you post). If you want the detail of the mail step filmed, say so in your written reply to the request for your yes (step 16); the assistant then first tells you what the mail step shows in the stand-in test (a test with stand-in programs, so the real mail addresses may differ), and you film it only if you accept that. In every case, footage in which a real mail address is visible is not used
~~~~
Why: Saved runs ON (EL-2; DECISION-one-store OWNER CONFIRMATION) and step 19: only made-up mail addresses may be visible. What the saved mail step shows is a guess that the stand-in test can check. Round 7: the owner may overrule the default (rule R5). Round 8: an overruling yes does not let a real address be filmed. Round 9: nested brackets split; "saved runs" defined in E-52. Round 10 (naive minor, design M2 style): the two instructions "do not film" and "you may say it may be filmed" read as a contradiction; the new text has one default ("by default do not film the detail"), says who decides (the owner, as rule 5 already says), and says how the owner overrules (his written reply); "address" is "mail address" (E-52). The new text ends without a full stop because the file continues with "; (5) ..." (E-15).

### E-15: OWNER-STEPS-realrun-v3.md, line 107, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
(5) the table screen: lead keys only
~~~~
NEW (exact):
~~~~
(5) the count screen. It shows how many rows the table of enquiries holds, with enquiry keys only. It is one of two things, and the assistant chooses which and tells you: a screenshot that the assistant takes in the stand-in test and labels "test screenshot", or the row preview of the table step of n8n (the step that reads the table of enquiries). It is not a live view of the table and not the result of the counting check (a small program of ours, not part of n8n, that counts mails, contacts and table rows). Pass: only enquiry keys and made-up addresses are visible. Fail: any other text is visible; then you do not film this screen and the assistant tells you what to do instead
~~~~
Why: D9: the counts proof screen is a stand-in-test screenshot or the Postgres node preview, not a live table screen. DECISION-one-store line 15 (no portal claim in the video) still holds (EL-3, D1). Round 7: the screenshot is labelled; who takes it, when, what "count screen" is, pass and fail are written; "the counting check" is the one phrase for the counts check in E-15, E-18, E-31 and E-36. Round 8 (naive minor): who chooses between the test screenshot and the row preview (the assistant, and it tells the owner) and "n8n's table step" is explained in the text. The new text ends without a full stop because the file continues with "; (6) ...". Whether the row preview shows enquiry keys only is UNVERIFIED (the assistant looks before the owner films). Round 9 (naive B6): who labels the screenshot (the assistant), what "count screen" and "row preview" are, and what happens on a fail (this screen is not filmed; the assistant says what to do instead) are written; "enquiry keys" are "enquiry keys".

### E-16: OWNER-STEPS-realrun-v3.md, line 121, status Apply now, type STALE
OLD (exact):
~~~~
deletes all saved executions of the take (made-up data only, owner decision 2026-11-16), turns "save successful production executions" back off in each workflow, stops n8n, removes the take folder and the Postgres container
~~~~
NEW (exact):
~~~~
deletes all saved runs of the take (made-up data only, owner decision 2026-11-16), turns off the setting that saves successful runs (a setting of the take's own n8n, not of each workflow), stops n8n, removes the take folder and the container of the database server. Before it removes anything, it copies the take's result file and its counts (names and numbers only, no secret) into a folder of its own, because removing the container also deletes n8n's database and the take's table of enquiries. It removes only the container that it started for the take: the assistant tells you that container's name, which is on the list of containers it recorded when the run began, and it touches no other container. The assistant does all of this and there is nothing for you to do. It reports each part as done or not done, and tells you before you start your own steps (items 2 to 6) if a part is not done. The stand-in test is planned to test only whether removing the container also removes the saved runs. The method at the real take is not decided yet, and you may be asked one yes or no question about it: whether the saved runs may be deleted only by removing the container. You answer `Yes, remove the container only` or `No`; no answer counts as No
~~~~
Why: EL-2: saved runs ON for the take, deleted at clean-up. Plan v5 section 2 and step 1.2 set saving through settings of the take's own n8n. The approved step "turn saving off" stays; container removal is the method of the stand-in test only, because plan line 81 says the real-take method is undecided and line 502 says it is not proven (NOT DECIDED 3; follow-on texts per answer are in E-39). Round 8: the clean-up has a pass and a fail for the owner (each part reported done or not done). Round 9: "executions" becomes "saved runs". Round 10 (naive M6, naive M3-style): (a) removing the container destroys both n8n's database and the take's table, so the assistant first copies the result file and the counts out (names and numbers only; the plan's evidence folder is the studio lead's choice, UNVERIFIED which); (b) the container is identified: only the one the assistant started for the take, named to the owner, from the list recorded at the start of the run (the same rule as AGENT-SCOPE E-34); (c) "before you sign off" (no such step exists in the sheet) becomes "before you start your own steps (items 2 to 6)"; (d) the yes or no question has an exact reply (`Yes, remove the container only` or `No`; silence is No), the same as in NOT DECIDED 3. The old text ends before the file's full stop, so the new text also has none. Step 22 item 1 is the assistant's job. The file's own words before the old text ("1. The lead: deletes the 3 credentials in n8n,") are not touched by any row; whether "3" must say four is FOR THE STUDIO LEAD TO CONFIRM g.

### E-17: OWNER-STEPS-realrun-v3.md, line 131, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
**a lead sent twice with the same id is processed once**
~~~~
NEW (exact):
~~~~
**a lead sent twice with the same id is processed once; a crash at exactly the moment between sending the mail and recording in the take's database that it was sent may send the mail twice**
~~~~
Why: D1, EL-3 (narrow claim) and plan v5 section 10 (row DM in every owner-facing claim). This row changes the POST text on line 131 (what the owner publishes). E-22 changes a different place, the status list on line 166. Rule R1 says when the crash clause may later be deleted from the post, and by whom it is judged. Round 9 (naive B9): "recording in the take's database that it was sent" (which table?) becomes "recording in the take's database that it was sent", in every text of this file. The public post keeps its own word "lead" for an enquiry.

### E-18: OWNER-STEPS-realrun-v3.md, line 131, status Apply now, type MISSING STEP
OLD (exact):
~~~~
recovery within 60 s; alert within 30 s.
~~~~
NEW (exact):
~~~~
recovery within 60 s; alert within 30 s. The post must also NOT say any of these four things. The words after each colon are explanations for you; they are not for the post.
- That a portal, an approval step or an audit trail exists or shows the take's contacts, mails or table rows: none is built or claimed.
- That n8n cannot reach the internet: its outgoing traffic is meant to be switched off by settings, which is not yet shown to work, and it is only watched, not blocked.
- That the take is crash-safe: a crash at some moments, listed in the plan, is not tested.
- That the counting check is independent: the counting check is a small program of ours, not part of n8n, that counts mails, contacts and table rows. It has no read-only database user of its own, because that user is not built.
~~~~
Why: EL-3, EL-4, D1, plan v5 section 0 ("Loopback only is OBSERVED, not ENFORCED") and section 10 (row DM, row NC); DECISION-one-store lines 23 and 28 (read-only count user not built; D3 parks it). Round 7: the forbidden phrase "a different database user" is replaced by the one phrase "the counting check" with its meaning inside the text. Round 8 (naive minor): "It must also NOT say" had no subject; it is now "The post must also NOT say". The sentence before it in the file is "It must NOT say: the same person through two doors is one lead; no lead data stays in n8n; recovery within 60 s; alert within 30 s." The two studio-lead-side conditions for dropping items are in rule R2. Round 9 (naive B9): the forbidden items are a list; "these rows" (no referent) is "the take's contacts, mails or table rows"; the explanation of each item follows a colon so the owner does not copy it into the post.

### E-19: OWNER-STEPS-realrun-v3.md, line 159, status Apply now, type STALE
OLD (exact):
~~~~
Independent review rounds 3 to 9 are done. WP6 smoke plan v3 is pending.
~~~~
NEW (exact):
~~~~
Independent reviews of the code (review rounds 3 to 9) are done. The plan for the stand-in test (version 5, text of 2026-11-16) is written. The stand-in test has not been carried out, and no evidence exists for it yet.
~~~~
Why: Plan v5 status line; the sheet still names plan v3. Round 6 (naive M3): the plan file name is removed from owner text, as E-03 removed it; the plan itself never says "rehearsal", so the owner text uses the two names of E-03. The first sentence is in the old text so line 159 and line 3 (E-02) use "review rounds" the same way. Round 9 (naive minor): "is written and NOT run" becomes "has not been carried out".

### E-20: OWNER-STEPS-realrun-v3.md, line 162, status Apply now, type STALE
OLD (exact):
~~~~
- A real n8n run, and the Code-node key probe (the WP6 smoke test): not run.
~~~~
NEW (exact):
~~~~
- The stand-in test has NOT been run. It is planned to test, on this laptop only, with stand-in programs and made-up data: (1) real n8n (release number 2.46.6) keeping its data in Postgres (a free database program); (2) whether a program step inside n8n can read n8n's encryption key (the long text that locks n8n's saved credentials), with a check that the test itself would notice a leak; (3) n8n keeping its saved runs; (4) a watch on whether n8n sends anything out of the laptop. A first smoke test (an earlier trial) did run real n8n on this laptop and left four things open: n8n used a simpler one-file database (SQLite); the test of reading the encryption key had no check that it could notice a leak; no request was being handled at the moment n8n was stopped; and the time n8n needed to come back after a restart was measured against the wrong waiting time.
~~~~
Why: Plan v5 section 0 table (open items M2 to M5 and "smoke-1 n8n ran on SQLite") and EL-1. Planned, not proven (naive M8): the text says "planned to test" and "has NOT been run". The first smoke is explained as an earlier trial. Round 8 (naive minor: "secret key" had two meanings): the key that n8n uses to lock its saved passwords is called "n8n's encryption key" (E-52 separates it from a secret key for a service). Whether the key the plan means is n8n's encryption key is read from plan lines 261 and 271 (`N8N_ENCRYPTION_KEY`).

### E-21: OWNER-STEPS-realrun-v3.md, line 164, status Apply now, type STALE
OLD (exact):
~~~~
The code was never run against a real Gmail, HubSpot, n8n or model call
~~~~
NEW (exact):
~~~~
The code was never run against a real Gmail, HubSpot or model call, and only once (the first smoke, an earlier trial, with stand-in programs for everything else) against a real n8n
~~~~
Why: Plan v5 section 0 and its "Already proven in smoke-1" line: a real n8n 2.46.6 ran in smoke-1. The text says it ran once and left items open (E-20), so it does not read as proof (naive M8).

### E-22: OWNER-STEPS-realrun-v3.md, line 166, status Apply now, type MISSING STEP
OLD (exact):
~~~~
and the second door (the hook door).
~~~~
NEW (exact):
~~~~
the second door (the hook door: the second way into the flows, named after the flow `mf-hook`), and a crash between sending the mail and recording in the take's database that it was sent. The stand-in test is planned to try this crash once. If the first try "missed" (the test could not see what it was looking for), it is tried once more. Until the test has run and passed, this case is untested.
~~~~
Why: Plan v5 section 10 row DM and section 9 (crash windows not proven). This row changes the status list on line 166 only; the post text is E-17. After the stand-in test the studio lead updates this sentence to the result (rule R1 evidence). Round 7: "missed" is explained in the text. Round 8 (naive minor): "the hook door" is explained from the flow file names in plan step 2.4 (`mf-form` and `mf-hook` are the two entry flows; that the hook flow is the second door is the sheet's own phrase, UNVERIFIED beyond the name) and the list reads "..., the manual n8n kill and restart, the second door (...), and a crash ..." (the old text began with "and", so the new text begins with "the second door" and carries one "and" before the last item). Round 9 (naive B11): the timing sentence is split into short sentences.

### E-23: OWNER-STEPS-realrun-v3.md, line 151, status Apply now, type STALE
OLD (exact):
~~~~
the pinned head is PROVISIONAL and lives in one place: `HEAD_PIN` at the top of the current `wp6\plan-wp6-resmoke-v*.md` (at the time of writing round 3 `take/nlite-int-r3`, round 4 on `take/nlite-int-r4`; source: lead instruction 2026-11-16)
~~~~
NEW (exact):
~~~~
the code under test is named in one place, at the top of the current plan for the stand-in test, and that choice is not final (at the time of writing fix round 3 on `take/nlite-int-r3`, fix round 4 on `take/nlite-int-r4`, fix round 5 being built on `take/nlite-int-r5`; source: the plan's own header notes of 2026-11-16)
~~~~
Why: Plan v5 line 76 (round 5 is `nlite-fix5` on `take/nlite-int-r5`); line 151 itself says "local take branch". The words "all take branches stay on this laptop" are not used: they rest on EL-6, which is in no input file (FOR THE STUDIO LEAD TO CONFIRM c); plan line 489 says only that the runner never commits, pushes or merges. The old text includes the labels HEAD_PIN and PROVISIONAL, so the owner reads no internal label. "source: lead instruction" is replaced by the plan's header, which the owner can read, so "lead" is not used for two people.

### E-24: OWNER-STEPS-realrun-v3.md, line 178, status Apply now, type STALE
OLD (exact):
~~~~
## UNVERIFIED list (count: 13)
~~~~
NEW (exact):
~~~~
## UNVERIFIED list (17 live items, numbered 1 to 18; item 10 was removed)
~~~~
Why: Four items are added by E-25 (items 15 to 18); 13 live items plus 4 = 17. Item 10 of the file is already marked "(Removed: ...)", so the numbering runs to 18 while the live count is 17. Round 8 (naive minor): the count is written as a short plain sentence.

### E-25: OWNER-STEPS-realrun-v3.md, line 193, status Apply now, type MISSING STEP
OLD (exact):
~~~~
14. Whether Gmail's IMAP shows the label `demo` as a folder named `demo` for the take program.
~~~~
NEW (exact):
~~~~
14. Whether Gmail's IMAP shows the label `demo` as a folder named `demo` for the take program.
15. That n8n (release number 2.46.6) runs on Postgres (a free database program), with its data kept in its own database, apart from the take's database (our table of enquiries). The database user that owns n8n's database is planned to have no other right. Source: a design decision of 2026-11-16; not proven. In the first smoke test n8n kept its data in a simpler one-file database.
16. That the saved runs are kept in Postgres and that deleting them at clean-up works at the real take (the stand-in test is planned to delete them by removing the container).
17. That n8n sends nothing out. Its outgoing traffic is meant to be switched off by settings; this is not yet shown to work. The test only watches it, taking a sample every half second, and never blocks it. The watch cannot see when n8n asks the internet for the address of a website by its name, so such a request would go unseen.
18. Whether a crash between sending the mail and recording in the take's database that it was sent sends the mail twice. The stand-in test is planned to test this once. If the first try "missed" (the test could not see what it was looking for), it is tried once more.
~~~~
Why: EL-1, EL-2, EL-4 and plan v5 section 10. Line 193 of the file is item 14 only (naive: "line 193 only item 14?": yes, the last line of the file). The new text is the whole of line 193 followed by four new lines; each line in the fence is its own line of the file, and the file ends after item 18. The count line becomes 17 live items (E-24; checked against v3 lines 178 to 193: items 1 to 9 and 11 to 14 are live, 13 items, item 10 is the "(Removed ...)" line). Round 7 (design m4): item 15 cites the studio lead's instruction (DECISION-one-store CORRECTIONS (a)) and "no other right" is "planned", not proven. Round 8 (naive minor): items 15, 17 and 18 are split into short sentences with no nested brackets. Round 9 (naive B11): "the studio lead's instruction" is removed from owner text (item 15 now says "a design decision of 2026-11-16"); "Lookups of names cannot be watched" is explained in plain words; the timing sentences of items 17 and 18 are split.

### E-26: AGENT-SCOPE-DO-AND-DONT.md, line 2, status Apply now, type STALE
OLD (exact):
~~~~
DRAFT 2026-11-15 by the lead
~~~~
NEW (exact):
~~~~
DRAFT 2026-11-15 by the lead, edited 2026-11-16 for the owner decision on saved runs, for decision 10 of the lead decisions (one Postgres server) and for the plan for the stand-in test (version 5). In this sheet "the lead" is the Claude session that leads the work and talks to the owner (the owner sheet calls it "the assistant"); "executions" are what the owner sheet calls "saved runs" (n8n's own word); "stand-in test" means the assistant's test run on this laptop only, with stand-in programs and made-up data, US$0 (the lead decision list also calls it the loopback re-smoke); "flow rehearsal" means the first run of the changed flows on this laptop that follows it (decision 12 of that list)
~~~~
Why: The sheet says "Update whenever a scope changes". Round 6: the two events have one name each (naive M4); "one Postgres server" is lead decision 10, not an owner decision (design m8): only the saved-runs decision is the owner's (DECISION-one-store OWNER CONFIRMATION). Round 8 (naive major 2): this sheet never defined "the lead" (it appears in E-38's text, in line 20 and in other lines) and used "executions"; the first line now defines both, once. The old text ends before the file's next comma and the new text keeps that join (", written from plan-4 ...").

### E-27: AGENT-SCOPE-DO-AND-DONT.md, line 5, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
Identity: n8n test account and its own Postgres table; credentials for HubSpot and SMTP live only in n8n's credential store.
~~~~
NEW (exact):
~~~~
Identity: n8n test account; the take uses one database server (Postgres, in one container) that holds two databases: n8n's own database (workflows, encrypted credentials, saved runs) and the take's database (our table of enquiries). This is a goal, not yet proven, until the stand-in test has run (in the first smoke n8n kept its data in SQLite, a one-file database); credentials for HubSpot and SMTP live only in n8n's credential store (planned to be kept encrypted in n8n's own database).
~~~~
Why: EL-1 and decision 10: n8n's state is in Postgres too, so "its own Postgres table" hides the second store. The aim is marked as an aim (DECISION-one-store CORRECTIONS (a)). One word each: "database server", "n8n's own database", "the take's database", "container".

### E-28: AGENT-SCOPE-DO-AND-DONT.md, line 9, status Apply now, type STALE
OLD (exact):
~~~~
n8n execution history is the one execution log in Postgres
~~~~
NEW (exact):
~~~~
n8n execution history is the one execution log in Postgres (a goal, not yet proven, until the stand-in test shows n8n runs on Postgres: plan v5 steps 1.2b, 2.7, 12.5b; in the first smoke n8n ran on SQLite)
~~~~
Why: DECISION-one-store CORRECTIONS (a): the decision is an aim until the test proves it; EL-1.

### E-29: AGENT-SCOPE-DO-AND-DONT.md, line 9, status Apply now, type MISSING STEP
OLD (exact):
~~~~
UNVERIFIED (flow JSON not read, WP6): the alert cap of 3 and "no lead data in the alert".
~~~~
NEW (exact):
~~~~
UNVERIFIED (flow JSON not read, WP6): the alert cap of 3 and "no lead data in the alert". n8n's own outgoing traffic (update checks, templates, usage reports, community packages) is MEANT to be switched off by environment settings (the list named `EG` in plan v5 section 2, and `N8N_DISABLED_MODULES`); that this works is not shown yet (plan v5 UNVERIFIED item 1). In the stand-in test it is only watched, in samples every half second; it is not blocked and not guaranteed, and lookups of names cannot be watched.
~~~~
Why: EL-4; stated as intent, not as fact (plan v5 UNVERIFIED item 1; sections 0 and 10 forbid claiming no outgoing traffic).

### E-30: AGENT-SCOPE-DO-AND-DONT.md, line 7, status Apply now, type MISSING STEP
OLD (exact):
~~~~
the encryption key itself is in n8n's environment;
~~~~
NEW (exact):
~~~~
the encryption key itself is in n8n's environment, and n8n 2.46.6 is expected to copy it into `<take>/n8n/.n8n/config` (a file readable only by its owner, mode 600; it is planned to be removed together with the take folder by a plain `rm`, an ordinary delete, and whether to use `shred -u` instead is not decided; stand-in test step 12.5 is planned to check both) and, once n8n runs on Postgres (planned, proven only by the stand-in test), the password of n8n's database user is a value in `n8n.env`;
~~~~
Why: Plan v5 step 12.5 says the scope sheet must list it; EL-1 puts a database user's password into n8n.env (step 1.2b, the plan's step that writes n8n's database settings). Stated as a plan. Who may open that file is NOT DECIDED 1. Round 7 (design m8): the removal by `rm` is "planned" and "expected", not a fact. Round 8 (design m5): `shred -u` of step 22 item 6 applies only to the secret files in `~/take-secrets`, which the owner deletes; the file `.n8n/config` holds the encryption key and is removed by plain `rm` with the take folder (UNVERIFIED reason: the plan gives none), so the choice between `rm` and `shred -u` is now NOT DECIDED 9, with the plan's `rm` as the default, and the text says it is not decided. Nested brackets are reduced.

### E-31: AGENT-SCOPE-DO-AND-DONT.md, line 20, status Apply now, type MISSING STEP
OLD (exact):
~~~~
`n8n_drive.py:40-41`)
~~~~
NEW (exact):
~~~~
`n8n_drive.py:40-41`; open finding M-1 of `review-codebase-1.md`, taken as earlier drafts quoted it because that file is not in `inputs/` (UNVERIFIED). Defect 1: the read names the table without its schema name. The table is planned to be in the schema `app` (a named section inside a database; this is an aim, not proven). The read runs as one database user whose search path may not include `app`, and then the read fails. A failed read stops the take safely (UNVERIFIED). Defect 2: the read-only database user for the counting check is not built, so this count is not yet an independent counting check. The stand-in test's grant check (plan step 1b) is planned to prove the grants only, and the proposal of four database users was parked on 2026-11-16. If `review-codebase-1.md` disagrees, the lead corrects this text)
~~~~
Why: DECISION-one-store OWNER CONFIRMATION (b), (c) and CORRECTIONS (c) name this finding "M-1"; the same line of AGENT-SCOPE (line 20) cites "F-01" for the contact delete (E-40, E-44). M-1 is the table-name finding and F-01 is the contact delete. Round 8 (naive major 8): the one long sentence is split into short ones: what is wrong (the read names the table without its schema), what follows (a failed read, safe), the second defect, and what to do if the review file disagrees. Design minor: the schema `app` is "planned", an aim, not a fact (DECISION-one-store CORRECTIONS (a)). `review-codebase-1.md` is not in `inputs/`: NOT DECIDED 10 (the studio lead checks M-1 against that file). The old text is only the closing of the sentence that contains `n8n_drive.py:40-41`; the new text keeps one closing bracket at its end, because the file continues with ", the HubSpot contacts ...". Plan step 1b: the plan's step that creates the database users, databases and the table (1b.2).

### E-32: AGENT-SCOPE-DO-AND-DONT.md, line 23, status Apply now, type STALE
OLD (exact):
~~~~
Real Gmail label behaviour, real HubSpot ids, real n8n Code-node reads of the key and a real n8n run are not exercised (WP6 smoke)
~~~~
NEW (exact):
~~~~
Real Gmail label behaviour, real HubSpot ids and a real model call are not exercised in any smoke yet; a first smoke ran real n8n on this laptop only and left items open, and the stand-in test (plan v5) has not run, so reads of the encryption key by n8n Code nodes are not proven
~~~~
Why: Plan v5 sections 0 and 9 (smoke-1 happened; the stand-in test is not run). Round 8 (naive minor): "key reads" is "reads of the encryption key" (E-52 separates the key senses).

### E-33: AGENT-SCOPE-DO-AND-DONT.md, line 23, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
the real take needs a take-time literal substitution into a local copy of the flows, not yet built.
~~~~
NEW (exact):
~~~~
the real take needs a take-time literal substitution into a local copy of the flows; a throwaway fill step (`fill_flows.py`) is used by stand-in test step 2.1 and is not the real-take version, and whether it replaces the `$env.DESK_*` and `$env.MF_*` reads is UNVERIFIED.
~~~~
Why: Plan v5 step 2.1 runs a fill step on the film flows; "not yet built" needs this qualification. Whether the fill step also replaces the `$env.DESK_*` and `$env.MF_*` reads is a lead question answerable from plan step 2.1. Round 6 (naive m2): the new text ends with a full stop because the old text ended with one.

### E-34: AGENT-SCOPE-DO-AND-DONT.md, line 27, status Apply now, type MISSING STEP
OLD (exact):
~~~~
say "went rogue" (name the missing control).
~~~~
NEW (exact):
~~~~
say "went rogue" (name the missing control). The stand-in test runner (plan v5 section 8) also never commits, pushes or merges, never does a name lookup (asking for the address of a host by its name), a `docker pull` or a new network tool, and never touches the owner's own n8n (ports 5678 and 5679) or any Docker container that was not on the list of containers recorded at the start of the run.
~~~~
Why: EL-4 and EL-5 (and D6 for the ports); plan v5 section 8 MUST-NOT is stricter than this section (it speaks of the containers in the P-4 baseline: the plan's first check, which records the containers that exist before the run). The rule "no commit, push or merge" is plan line 489. EL-6 (take branches stay on this laptop) is in no input; this row follows the plan wording only (FOR THE STUDIO LEAD TO CONFIRM c). Round 8 (naive minor): "name lookup" and "start-of-run list" are explained in the text.

### E-36: OWNER-STEPS-realrun-v3.md, line 131, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
counts the mails and contacts on its own credentials
~~~~
NEW, TEXT W (default; this is the only live text until confirmation b is answered yes in writing):
~~~~
counts the mails and contacts with a small counting program of ours (not part of n8n)
~~~~
NEW, TEXT N [HOLD: DO NOT APPLY unless confirmation b is answered yes in writing] (replaces text W only if confirmation b says the mail count and the contact count run on credentials of their own):
~~~~
counts the mails and contacts on its own credentials, and the table of enquiries with a small counting program of ours (not part of n8n)
~~~~
Why: D-M1 of round 1: the old words claim an independent login for everything. DECISION-one-store lines 23 and 28: the table count runs as one database user through `docker exec psql`; the read-only count user is not built; plan v5 section 9 says its password is never exercised. A claim in a public post must not outrun that (D1, EL-3). Round 7: the post says "a small counting program of ours (not part of n8n)", the public wording of "the counting check" (E-15, E-18); "separate" is dropped because it reads as "independent". Default W (the smaller claim). Round 8 (naive minor, post grammar): with text W the post sentence reads "... our code caps the spend, asks the model once per lead and counts the mails and contacts with a small counting program of ours (not part of n8n); **a lead sent twice with the same id is processed once; a crash at exactly the moment between sending the mail and recording in the take's database that it was sent may send the mail twice**." With text N it reads "... and counts the mails and contacts on its own credentials, and the table of enquiries with a small counting program of ours (not part of n8n); **a lead ...**". Whether the counting program really counts the mails and contacts is UNVERIFIED (confirmation b); the owner has no way to verify the post alone, so fact 1 of E-12 (the stand-in test result with counts) is what he relies on, and the assistant says in the request for your yes which counts the test ran. The post says nothing about "logins". Round 9 (design m5): text W is marked as the only live text; text N carries a DO NOT APPLY label until confirmation b is answered yes in writing. The post sentence reads with text W as before; the old words "table of enquiries" in text N are "table of enquiries" (the post itself says "lead" for an enquiry, so text N says "table of enquiries" only because the public post must not use the older internal name).

### E-37: OWNER-STEPS-realrun-v3.md, line 27, status Apply now, type STALE
OLD (exact):
~~~~
## Phase 0: set-up, by Mon 16 Nov 18:29 UTC (23:59 IST); Sun evening is ideal. About 60 to 90 minutes.
~~~~
NEW (exact):
~~~~
## Phase 0: set-up. The original deadline was Mon 16 Nov 2026 18:29 UTC = 23:59 IST; it is not the spending window (that ends Mon 23 Nov 2026 18:29 UTC = 23:59 IST). Sun evening was ideal. About 60 to 90 minutes if nothing were done yet.

Most of Phase 0 is already done. Read this note first: where it differs from the steps below, this note applies.
- DONE, from your own statement of 2026-11-16: the throwaway Gmail mailbox (2-step on, settings done, app passwords saved in files; the assistant asks you where the files are, so that the clean-up deletes them); the HubSpot test account (users created, secret key given); your own n8n account (it holds credentials for HubSpot, the model and Gmail in n8n's own credential store; the take uses a fresh n8n, so those are not the take's); a saved secret key for the model. Do not redo a step whose result already exists.
- NOT YET CONFIRMED: whether the secret key for the model was made for this take only, and what the saved HubSpot secret key is allowed to do. Your statement does not cover the two HubSpot private apps or the property `hadavin_label`. Before the take the assistant confirms with you that the secret key the take uses is the read-only one (step 7, app 1) and that app 2 exists. If either is not so, you do not say yes to a take until the assistant has told you what to change and you have changed it.
- Do NOT do step 8 until the assistant asks you in a message. The take uses a fresh n8n that the assistant starts, and the assistant tells you when and where to type the credentials into it (HubSpot, the model, Gmail and the take's database; see step 8, sub-step f).
- NOT SETTLED, BEFORE ANY TAKE: whether the take program deletes the take's contacts in HubSpot at its end. An earlier reading of the code found a step that does; a later independent review found none. Nobody has settled which is right, and steps 17 and 18 below still say "archived" (the earlier reading). If the program does delete contacts, a take with the read-only secret key (step 7, app 1) would fail after the enquiries were sent and money was spent. Before the take the assistant shows you the result of searching the final code for a delete call and tells you which case it is. Do not say yes to a take until it has done so. The assistant's request for your yes (step 16) lists this as its fourth fact.
- The assistant tells you before the take which of steps 1 to 9 still need you.
- AT THE TAKE you type three things yourself: (1) `y` and Enter; (2) the 6-digit confirmation number that the program shows (it is new for every take), a space and the take id, on one line; (3) later, `end`, when the assistant tells you. The take id is a short name that you choose for each take, new every time (step 17 says more). Take-day settings: mains power, sleep Never, lid Do nothing (rule 6 above).
~~~~
Why: FACTS-ALREADY-DONE.md names only what the owner did; line 3 says "HubSpot test account, users created, key given" and "Anthropic key saved" and nothing about key scope or about the apps. D7: first-visit n8n setup is done; the owner only types y, the challenge and end. The full rewrite of Phase 0 is OWNER-STEPS v4 (queue item C4b); this row is the note at the top of Phase 0 in v3 and falls away if v4 replaces Phase 0. Round 9: (a) design M1 and naive B10: the bullet "BEFORE ANY TAKE: the take program as it is today still removes the contacts" stated an unsettled fact as fact. Q23 (ORDERS, 12:50Z): decision 2 stays, the take never deletes; the r17 review found no delete or archive path in `run_real_check_n8n.py` (only a GET); line 1051 of earlier readings is UNVERIFIED stale text; the studio lead shows the final head's search at re-pin. The bullet now says "NOT SETTLED", gives both readings, uses one word ("deletes", with the old "archived" quoted once), names the action (the assistant shows the search result before the take) and says the request for your yes carries it as fact 4; (b) naive A1: this row NEEDS E-12 (it points to the request for your yes in step 16, which E-12 extends); apply both together; the instruction "if v3 is read before v4 exists, only apply E-37 and E-52" is withdrawn (all Apply now rows go to v3, see "How the rows are used"); (c) naive A3: when gate G1 opens the studio lead deletes this bullet and applies E-04, E-05, E-41 and E-42; (d) naive B10: where the take id comes from is stated (the owner chooses it, new every take); "confirmation number" is explained; the old check "NOT YET CONFIRMED ... a check the owner cannot do" is now an action of the assistant; (e) Q25 and Q26 times: the heading gives UTC and IST. The step 8 prohibition still rests on FOR THE STUDIO LEAD TO CONFIRM e. The new text is the heading line, a blank line, one sentence and bullets, so no bullet is a heading.

### E-38: AGENT-SCOPE-DO-AND-DONT.md, line 9, status Apply now, type STALE
OLD (exact):
~~~~
the lead deletes the executions and turns saving off at clean-up
~~~~
NEW (exact):
~~~~
the lead deletes the executions and turns saving off at clean-up (saving is a setting of the take's own n8n, not of each workflow; in the stand-in test the runs are planned to be deleted by removing the Postgres container and the take folder; the method at the real take is not decided yet)
~~~~
Why: Same idea as E-16 on AGENT-SCOPE line 9; plan v5 section 2 and lines 81 and 502 (NOT DECIDED 3). The old text does not overlap the old texts of E-28 and E-29 (all on line 9; checked by script). Round 8 (naive major 2, "the lead" and "executions"): E-26 now defines "the lead" and "executions" in this sheet's first line, so this text needs no extra words.

### E-39: DECISION-one-store.md, line 23, status Hold (gate G4), type STALE
OLD (exact):
~~~~
delete them and turn saving off at clean-up
~~~~
NEW [HOLD G4: DO NOT APPLY], NEW if NOT DECIDED 3 is answered (b) only remove the container (apply only after the owner has said yes to it in one line, because it is not the step the owner approved) (exact):
~~~~
delete them at clean-up by removing the container (the owner approved "delete them and turn saving off at clean-up"; method changed on <date and time in UTC and IST that the owner said yes>)
~~~~
Why: DECISION-one-store line 23 records an owner approval, so it is not rewritten without the answer to NOT DECIDED 3 (plan lines 81 and 502). Round 6 (naive B2): the text per answer is given. Round 10 (naive M7): ONE version of the follow-on texts replaces the round-6 and round-9 versions, which disagreed, and the invented words "deletes the 3 credentials in n8n" are gone (no decision backs a new credential delete; the file's own words "1. The lead: deletes the 3 credentials in n8n," come before E-16's old text and stay). Per answer: answer (a), turn saving off, delete the runs, then remove the container: nothing changes in this file (it already says "delete them and turn saving off at clean-up"), and E-16 and E-38 keep their texts. Answer (b), remove the container only: this row's text replaces the old text, and the studio lead changes E-16's new text so that the part "deletes all saved runs of the take (made-up data only, owner decision 2026-11-16), turns off the setting that saves successful runs (a setting of the take's own n8n, not of each workflow), stops n8n, removes the take folder and the container of the database server" reads "stops n8n, removes the take folder and the container of the database server, which also removes the saved runs"; the rest of E-16's text is unchanged, and the sentence about the one yes or no question is deleted because it has been answered. E-38's bracket then says "the lead removes the container, which also removes the executions" in place of "the lead deletes the executions and turns saving off". The studio lead applies those follow-ons together with this row. Held: the NEW text is not applied until NOT DECIDED 3 is answered.

### E-40: AGENT-SCOPE-DO-AND-DONT.md, line 20, status Hold (gate G1), type CONTRADICTION
OLD (exact):
~~~~
at the end ARCHIVE the take's own HubSpot contacts, which the code does as a DELETE call (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, per `review-codebase-1.md` F-01)
~~~~
NEW [HOLD G1: DO NOT APPLY] (exact):
~~~~
at the end LIST the take's own HubSpot contacts by enquiry key and contact id for the owner, who deletes them by hand in HubSpot after the take (the take never deletes contacts). Whether the final code still contains a contact delete call is NOT SETTLED (Q23): an earlier reading found one (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, per `review-codebase-1.md` F-01), a later review found none; gate G1 settles it at the final head. Whether the code already prints that list is UNVERIFIED
~~~~
Why: D2: the take never deletes contacts; leftovers are listed by enquiry key and contact id and the owner deletes them by hand. Gate G1: the row describes target behaviour, so it is held until the final code is shown to make no delete call (E-04 and E-05 are held for the same reason). Round 9 (design M1): the new text no longer states that today's code deletes; Q23 says an earlier reading found a delete (line 1051, now UNVERIFIED stale text) and the r17 review found none. F-01 is the contact-delete finding (E-31 uses M-1 for the table-name finding).

### E-41: OWNER-STEPS-realrun-v3.md, line 103, status Hold (gate G1), type CONTRADICTION (code-change gate)
OLD (exact):
~~~~
NEEDS-OWNER. When the script says "Film the contact list now: type `end` and press Enter to archive", the lead films the contact list first. Type `end` and Enter yourself only when the lead says so. The script then archives this take's contacts. Only the exact word `end` ends the pause: a bare Enter or any other line makes the script print "type exactly: end" and ask once more; the second wrong line also prints "type exactly: end" and then the script goes ahead and archives anyway; a closed input on the first prompt ends the pause at once. Ctrl-C or closing the window also still archives.
~~~~
NEW [HOLD G1: DO NOT APPLY] (exact):
~~~~
NEEDS-OWNER. When the script pauses so that the assistant can film the contact list (the assistant tells you the exact words that appear on screen once the final code is read), the assistant films the contact list first. Type `end` and Enter yourself only when the assistant says so. The script then ends the take; it removes no contact (you delete this take's contacts by hand afterwards, see the next line). Only the exact word `end` ends the pause: a bare Enter or any other line makes the script print "type exactly: end" and ask once more; the second wrong line also prints "type exactly: end" and then the script goes ahead and ends the take anyway; a closed input on the first prompt ends the pause at once. Ctrl-C or closing the window also ends the take and removes no contact.
~~~~
Why: D2: the word "archive" leaves this line. Gate G1: the pause prompt and the behaviour on a second wrong line, Ctrl-C and a closed input are read from the older text with "archive" in them; the program's prompt wording at the final head is UNVERIFIED (hence "the assistant tells you the exact words"). The old text is one whole line (103); no quoted prompt is invented. Round 9 (design M1): no claim about today's code; the row is true only once the final code is read and shown to make no delete call (gate G1). Round 9 (naive B12): "the assistant films" is kept because the older text has "the lead films the contact list"; who films and who posts is the owner's decision (rule 5: you post). Missing input (exact), why the row is held: the line `CODE-GATE G1 OPEN: <final head commit id>, <evidence file name>, route 1|2` and the evidence file's quote of the pause prompt; when both exist, put the quoted prompt in place of the words in the first bracket. Apply together with E-04, E-05 and E-42.

### E-42: OWNER-STEPS-realrun-v3.md, line 104, status Hold (gate G1), type CONTRADICTION (code-change gate)
OLD (exact):
~~~~
- STOP and tell the lead: closing the window or Ctrl-C early still archives, but tell the lead; leftover contacts are deleted by you in the HubSpot UI, the lead gives the count.
~~~~
NEW [HOLD G1: DO NOT APPLY] (exact):
~~~~
- STOP and tell the assistant: if you close the window or press Ctrl-C early, the take also ends and removes no contact, but tell the assistant. You delete this take's contacts by hand in the HubSpot website, and the assistant gives you the count and, if the program printed them, the list (enquiry key and contact id).
~~~~
Why: D2: the owner deletes the contacts by hand, from a list by enquiry key and contact id (the old line gave only the count). Gate G1 as in E-41; after Ctrl-C or a closed window the list exists only "if the program printed it" (UNVERIFIED). Round 9 (naive B12): "UI" becomes "website"; the STOP trigger is a plain "if" sentence. Missing input (exact), why the row is held: the line `CODE-GATE G1 OPEN: <final head commit id>, <evidence file name>, route 1|2`, and the evidence file's statement whether the program prints the list on Ctrl-C.

### E-43: DECISION-one-store.md, line 14, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
**ONE database for everything we own: the single Postgres instance of the take** (one container, one engine). n8n's internal data in its own schema or database, our claim table `mf_leads` in an `app` schema,
~~~~
NEW (exact):
~~~~
**ONE Postgres server for everything we own: the single Postgres instance of the take** (one container, one engine) with two databases (n8n's own and the take's). n8n's internal data lives in its own database, our claim table `mf_leads` in an `app` schema of the take's database,
~~~~
Why: Decision 10: wording "one Postgres server with two databases (n8n's own and the take's)". The studio lead applies the row (the file is in `inputs/`, which the builder does not edit). The three roles in the same sentence are not changed: D3 parks the proposal of four database users and line 20 keeps "three roles or one" as UNVERIFIED. Apply order on DECISION-one-store: E-43 (line 14), then E-46 (line 14, no overlap), then E-47 (line 1). Round 7 (naive minor): the sentence after E-43 reads "1. **ONE Postgres server for everything we own: the single Postgres instance of the take** (one container, one engine) with two databases (n8n's own and the take's). n8n's internal data lives in its own database, our claim table `mf_leads` in an `app` schema of the take's database, three least-privilege roles (n8n, the app role ...". The join after the last comma is the file's own " three least-privilege roles" (read from line 14).

### E-44: AGENT-SCOPE-DO-AND-DONT.md, line 20, status Hold (gate G1), type CONTRADICTION
OLD (exact):
~~~~
NOTE (F-01, CODE-CHANGE-NEEDED, not fixed here): OWNER-STEPS:69 sets HubSpot app 1 to read-only, but the archive is a DELETE: a read-only token passes the pre-take GET probe and fails only at archive after the sends; until the lead decides (app 1 scope or an archive path), treat the archive as needing delete rights and leftover contacts as deleted by hand.
~~~~
NEW [HOLD G1: DO NOT APPLY] (exact):
~~~~
NOTE (F-01, not settled): decision D2 of 2026-11-16 settles the key: app 1 stays read-only (OWNER-STEPS:69) and the take never deletes contacts. Whether the final code still contains a delete call is NOT SETTLED (Q23: an earlier reading found one, the r17 review found none). If the final-head search finds one, it must be removed (or turned into a list for the owner) before any paid take, because a read-only key passes the pre-take GET probe and would fail at the delete after the sends. Leftover contacts are deleted by the owner by hand.
~~~~
Why: D2 closes the question "app 1 scope or an archive path" that the note leaves open. Gate G1: held with E-40 because the note speaks of a possible code change. Round 9 (design M1): the new text no longer states that the code deletes; it states the conditional consequence and points at gate G1. Whether the program already prints the list is UNVERIFIED.

### E-45: AGENT-SCOPE-DO-AND-DONT.md, line 23, status Hold (gate G1), type STALE
OLD (exact):
~~~~
(archive, result.json, final print)
~~~~
NEW [HOLD G1: DO NOT APPLY] (exact):
~~~~
(the end-of-take step, result.json, final print; whether this step still makes a contact delete call is not settled (Q23), and D2 says it must make none)
~~~~
Why: D2: the word "archive" (a delete call in the earlier reading) leaves the sheet. Gate G1. The rest of that sentence (exit 3 behaviour) may change with the code and is UNVERIFIED. Round 9 (design M1): no claim that today's code runs the delete.

### E-46: DECISION-one-store.md, line 14, status Apply now, type STALE
OLD (exact):
~~~~
tables in schema n8n,
~~~~
NEW (exact):
~~~~
tables in the separate database n8n,
~~~~
Why: DECISION-one-store CORRECTIONS (a): n8n's own state lives in a SEPARATE database `n8n` owned by the role `smk_n8n`, not a schema; decision 10 wording. Same line as E-43; the old texts do not overlap. Round 7 (naive minor): the phrase after E-46 reads "(no sqlite file, tables in the separate database n8n, DB_* names in n8n's process environment)" (the file's own text on either side, read from line 14).

### E-47: DECISION-one-store.md, line 1, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
# DECISION: one database for the take
~~~~
NEW (exact):
~~~~
# DECISION: one Postgres server for the take
~~~~
Why: Decision 10 wording; the title says "one database" while the text (after E-43) has two databases on one server.

### E-48: OWNER-STEPS-realrun-v3.md, line 123, status Apply now (safe default text), type MISSING STEP
OLD (exact):
~~~~
3. You: delete BOTH HubSpot private apps (Settings, Integrations, Private Apps, Delete). Screenshot.
~~~~
NEW (exact):
~~~~
3. You: delete BOTH HubSpot private apps (Settings, Integrations, Private Apps, Delete). Take a screenshot. Before you save it, crop it (cut away the parts of the picture) so that it shows no secret key text, no account name and no web address.
   Before the assistant starts item 1, it asks you this question and waits for your reply: "Is the secret key for the model that you saved one that you made only for this take, and does nothing else use it?" Reply `yes`, `no, other things use it` or `not sure`.
   - If you reply `yes`: revoke that secret key (to revoke is to delete it at the company that issued it, so that it stops working) in the website of the company that provides the AI model (Anthropic). Do it right after the take, and in every case by 2026-11-23 18:19 UTC = 23:49 IST, the last time to revoke. (The spending window ends 10 minutes later, at 18:29 UTC = 23:59 IST; that is when the model stage must stop spending.) The assistant tells you the exact page before the clean-up; that click path is not checked. Take a screenshot of the list of secret keys showing it gone, cropped in the same way.
   - If you reply `no, other things use it` or `not sure`: do NOT revoke it. The assistant writes down that the key stays and asks you once more before 2026-11-23 18:19 UTC = 23:49 IST. Because the key stays alive, the copy of it in the take folder is still a live secret, and item 1 removes that folder with a plain delete (`rm`), which is not a wipe. So BEFORE the assistant starts item 1, you delete that copy yourself with `shred -u <path>` (the assistant tells you the path and never opens the file; if shred is not installed, use `rm <path>`).
   - If a take is still running at 18:19 UTC = 23:49 IST: tell the assistant at once. If you replied `yes`, revoke the key at 18:19 UTC = 23:49 IST anyway (a revoked key cannot spend money; the take then fails), unless the assistant tells you otherwise before that time.
   - Every OLDER secret key for the model, one that was not made for this take: revoke it too, unless you tell the assistant a reason and an end date.
   The screenshot is only a record: no check in item 5 tests the secret key for the model. The model stage reads a copy of that secret key that you place in the take folder; the assistant never opens it (this is a procedure, not enforced by a program). Item 1 removes the take folder with a plain delete, which is not a revoke and not a wipe.
   Your own copies of the secret key are the files where you saved it; tell the assistant only the path, never the content. If you revoked the key, delete every file that holds a copy of it with `shred -u <file>` (if shred is not installed, use `rm <file>`), as in item 6. The two secret files in `~/take-secrets` (the file with the app password of the receiver mailbox and the file with the HubSpot read secret key) are covered by item 6. If you did not revoke the key, keep the copy that other work uses and delete only a copy made for this take, if there is one; the assistant asks you which is which.
~~~~
Why: DECISIONS-2026-11-16.md item 5, part S9-3 (the decision file numbers its items 1 to 12; the studio lead's short name for the part is D5 S9-3): the owner revokes the secret key for the model at clean-up, owner-only; FACTS-ALREADY-DONE.md lists the clean-up revoke as owner-only. Step 22 names only app passwords and HubSpot apps. Round 7: the row ALWAYS applies; the safe default is in the text. Round 8: in the "no or not sure" case the key stays live, so the assistant asks once more and writes the outcome down (rule R7 sends it to `ANSWERS-c4.md`). Round 9 (design M2, Q25, Q26): the second ask and the last time to revoke are 18:19 UTC = 23:49 IST, not the window end; the owner revokes the key himself, no timer is invented. Round 10: (a) naive M5: the last time to revoke (18:19 UTC = 23:49 IST, Q25) and the money stop (the end of the spending window, 18:29 UTC = 23:59 IST) are two different things and are named apart; the owner is told what to do if a take is still running at 18:19 (revoke anyway on a `yes`: a revoked key spends nothing; confirmation h asks the studio lead to confirm); "revoke" is the only verb (Q25 says "cancel"); the question text is the same as in NOT DECIDED 7 (a); the reply words are plain (no internal codes); "receiver password file" is described; "where the files are": the owner tells the assistant only the path; (b) naive M5: on `no` or `not sure` the live key's copy in the take folder was removed only by plain `rm` (item 1), so the owner now shreds it BEFORE item 1, which is why the assistant asks the question before item 1 (a wipe is not reliable on every disk, NOT DECIDED 9, so revoking stays the safe course); (c) Q19.5 (cancel all old model keys except the run key unless the owner writes a reason and an end date): the bullet on older keys; (d) design M1: the same times are on the heading of step 22 (E-55). The click path of the model provider's key list is unchecked. If v4 is written, use this row there.

### E-49: OWNER-STEPS-realrun-v3.md, line 87, status Hold (gate G5), type MISSING STEP
OLD (exact):
~~~~
You may be asked to confirm what a screen shows.
~~~~
NEW [HOLD G5: DO NOT APPLY] (exact):
~~~~
You may be asked to confirm what a screen shows.

Then comes the preparation (the last checks the assistant makes before it asks for your yes). In it the assistant sends ONE made-up enquiry through your throwaway accounts. This is the only run through real accounts before the take; there is no other real-account smoke test (a smoke test is a short first run of a whole chain, only to see whether it works at all).
- How: the assistant sends the enquiry straight to the address of the take's own n8n on this laptop. n8n then uses the credentials you typed into it. The assistant holds no real secret key and answers no prompt of the take program.
- What you read first: the assistant sends nothing until you have read its message that says all of this: (a) the way described above; (b) that no paid model call is possible, either because the model stage was started with the stand-in model and a secret key file that holds a made-up value, or because you gave a separate written yes with a number for one paid call; (c) which traces the enquiry leaves: one contact in HubSpot, one mail in the label `demo`, one row in the table of enquiries, one saved run in n8n and, if the model stage was called, a line in its journal and spend record; (d) which of these traces stay until clean-up and whether the take's counts include them.
- Your consent: the assistant sends the enquiry only after you answer in writing: `Yes, send the one enquiry on <day>` (<day> is the weekday and the date). Reading the message is not consent. Any other answer, "no" or "not sure" means nothing is sent.
- What you do afterwards, before the take: delete the contact in the HubSpot website (Contacts, find the made-up name, open it, Actions, Delete; this click path is not checked) and remove the mail from the label `demo` and from the Inbox in Gmail (as in step 20). Then tell the assistant "label and inbox empty".
- Pass: HubSpot shows exactly one new made-up contact, the label `demo` holds exactly one mail from this enquiry, and the assistant reports no error. Fail: no new contact, or no mail, or more than one of either, or an error. Then the assistant stops and tells you what to change.
~~~~
Why: Design Major 1 of round 8 (E-11 split) and minor m2 (traces). Moved out of E-11 and held: the paragraph on the preparation enquiry. D8 says ONE made-up lead in the preparation; EL-5 and D8 give no mechanism. Why held (gate G5): (1) how the enquiry reaches the accounts is NOT DECIDED 8 and only one route is written here (route B; the take program cannot post one enquiry: it posts its own three people, A twice, B ten times and C once with n8n killed, up to 3 model calls: OWNER-STEPS Words used and step 17); (2) AGENT-SCOPE has no row that allows the assistant to post it (E-53 writes the rows, also held); (3) a paid call must be impossible by construction (NOT DECIDED 6). Round 9: (a) design M4: consent was weaker than the scope row: "only after you have read a message" is not agreeing; the owner now answers in writing `Yes, send the one enquiry on <day>` and E-53 uses the same words; (b) naive A2: the definition of "the preparation" lives here (round 8 had it in E-52 whose only use was this held row); (c) naive B5: the heading "no steps for you" of Phase 1 is corrected in E-54; the click path for deleting the contact is given (UNVERIFIED), the mail is removed as in step 20; "none" is spelled out in the fail case; "smoke test" is defined in E-52 (apply now, line 16, before this line); sub-points are bullets. The old text is the file's own last sentence of line 87; the new text is that sentence followed by a blank line and one paragraph with bullets. If gate G5 never opens, no preparation enquiry is sent (safe default; D8's "one made-up lead" is then not done and the take rests on the tests).

### E-50: OWNER-STEPS-realrun-v3.md, line 92, status Hold (gate G5), type MISSING STEP
OLD (exact):
~~~~
No numbers in the message means answer no.
~~~~
NEW [HOLD G5: DO NOT APPLY] (exact):
~~~~
No numbers in the message means answer no. When the preparation has sent its one enquiry (see Phase 1), the message states a fifth fact, again with the name of the file that shows it: (5) the enquiry was sent after your written "Yes, send the one enquiry on <day>", which traces it left, and that you have deleted its contact and its mail. Answer no if this fifth fact is missing.
~~~~
Why: Design Major 1: fact 5 of round 7's E-12 (the preparation enquiry, design m7 of round 6) is held with E-49 (gate G5), because the enquiry itself is held. Anchored on the file's own next sentence so it does not overlap E-12. When G5 opens the studio lead applies E-49, E-50 and E-53 together, and rule R6 then checks five facts instead of four. Round 9 (design M4): fact 5 names the consent line. Apply together with E-49 and E-53 when gate G5 opens.

### E-51: OWNER-STEPS-realrun-v3.md, line 92, status Apply now, type MISSING STEP
OLD (exact):
~~~~
not a ceiling the program enforces against a second file)
~~~~
NEW (exact):
~~~~
not a ceiling the program enforces against a second file; the take program does not print these two values (the spending cap and the window end), so you read them in the stage settings file that the assistant shows you in the chat and compare them with the figures in its message. The assistant shows only that settings file, never `n8n.env`)
~~~~
Why: Design m7 and D5 item S9-2: D5 says KEEP the owner's own compare of the settings-file figures, "with the honest sentence that the program does not print them". Round 7 wrote "no row needed" for S9-2, but OWNER-STEPS rule 4 and step 16 say only "a backstop that you check by eye", not that the program does not print the figures: so the honest sentence was missing. That the program does not print them is D5's statement; no code was read (UNVERIFIED by code). The old text lies on line 92 inside step 16's message list; it does not overlap E-12's old text or E-50's. Round 9 (naive B13 and design M6): the two values are named (the spending cap and the window end), the file shown is only the stage settings file, and the assistant never offers a secret file (OWNER-STEPS rule 2).

### E-52: OWNER-STEPS-realrun-v3.md, line 16, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
never under `/mnt/c/...` (that is the Windows disk; the program refuses it).
~~~~
NEW (exact):
~~~~
never under `/mnt/c/...` (that is the Windows disk; the program refuses it).
- **The assistant** (in the edited parts) is Claude, who works with you. The older parts of this sheet call the same helper "the lead".
- **The plan**: the written plan for the stand-in test, version 5 (file `plan-wp6-resmoke-v5.md`). The assistant attaches its list of checks to the request for your yes (step 16) and shows the plan in the chat when you ask.
- **The stand-in test**: a test of the take on this laptop only, with stand-in programs (small fake versions of Gmail, HubSpot and the AI model) and made-up data. **The flow rehearsal**: the first run of the changed flows on this laptop, after the stand-in test has passed. Both are planned at US$0; nothing about either is proven yet.
- **The flows**: the automatic step chains that n8n runs. **The model stage**: our small program that asks the AI model and enforces the money cap (the older text calls it "the stage"). **The take program**: the script `scripts/run_real_check_n8n.py` that runs the take (the older text also says "the script" or "the program"). **The take id**: a short name that you choose for each take, new every time (the older text also says "the tag" or "the id").
- **An enquiry**: one made-up sales message sent through the flows (the public post on the line about the post keeps its own word "lead" for the same thing; the older text also says "lead"). **A contact**: the made-up person that an enquiry creates in HubSpot. **An enquiry key**: the made-up identifier the take program gives to an enquiry (the older text says "lead key" or "lead id"). **The table of enquiries**: the take's table with one row per enquiry (the older text says "table of leads").
- **A secret key**: a long text that works like a password for a service (HubSpot, the AI model provider); the older text calls it a "token" or a "key". **A password**: a text that you type yourself: the 16-letter app password of a mailbox, or a database user's password. **The encryption key**: the long text n8n uses to lock its own saved credentials; it is not a secret key in the sense above.
- **A database user**: an account inside the database program Postgres (not a mailbox and not a HubSpot sign-in). **A HubSpot private app**: a named access pass inside HubSpot that gives one program a limited list of permissions; each has its own secret key. **A credential (in n8n)**: one saved access setting in n8n that holds the secret key or password for one service.
- **Saved runs**: the past runs that n8n keeps and lists (n8n itself calls them "executions").
- **A smoke test**: a short first run of a whole chain, only to see whether it works at all.
- **The spending window**: the last day and time the model stage may spend money: 2026-11-23 18:29 UTC = 23:59 IST (the older text calls it "the window end"). It has nothing to do with a screen window.
~~~~
Why: Round 8 (naive minors: glossary split, n8n and "HubSpot private app" not defined, "take program" interchangeable with "script" and "program", "key" with several meanings, "smoke test" used before it is defined, "executions" versus "saved runs"; naive major: "the plan" named but never identified). The old text is the end of the bullet on line 16 (the last bullet of the list "Words used (read once)"); the new text is that end followed by new bullet lines. n8n is already defined in the list (second bullet of the list). "The lead" is defined by the first new bullet; E-01 points here. Round 9: (a) naive A2: "The preparation" is defined where it is used (E-49, held), not here; (b) naive A5: "enquiry key", "table of enquiries" and "take id" are named, with the older words they replace; (c) naive B15: "password" is "a text that you type yourself", with the 16-letter app password named; (d) design M6 and naive B2: "the spending window" is defined (UTC and IST); "credential" is defined; (e) the plan bullet follows E-12 (list attached). The plan file name appears once, here, so every later "the plan" has a referent.

### E-53: AGENT-SCOPE-DO-AND-DONT.md, line 28, status Hold (gate G5), type MISSING STEP
OLD (exact):
~~~~
- Enforced by: the preamble gate hook, rule 24 NEVER-DO-GATE, `bible\NEVER-DO.md`.
~~~~
NEW [HOLD G5: DO NOT APPLY] (exact):
~~~~
- Enforced by: the preamble gate hook, rule 24 NEVER-DO-GATE, `bible\NEVER-DO.md`.

## 4b. The lead in the take preparation (planned; written only after the owner's preparation question is answered)
- MAY: post ONE made-up enquiry to the take's own n8n address on this laptop, only after the owner's written `Yes, send the one enquiry on <day>`; read the counts that follow (names and counts only); tell the owner which traces the enquiry leaves.
- MUST NOT: post a second enquiry; read or print n8n's credentials or any secret file; hold or use a real secret key of its own; start the model stage with a real key file unless the owner's written yes with a number for one paid call is quoted in the lead's message; answer a prompt of the take program; delete a contact, a mail or a table row by itself.
- Enforced by: nothing in code is known for the posting itself; the model stage refuses a second paid call per enquiry key (section 2); that the stage can run with the stand-in model and a made-up key file in a real take folder is UNVERIFIED (plan v5 step 3.3 shows it for the stand-in test only).
~~~~
Why: Design Major 1: no AGENT-SCOPE row allows the assistant to send the preparation enquiry (line 27 forbids a real key and an answer to a prompt of a script that can reach a network; the sheet has no section for the lead in the preparation). This is the MAY and MUST NOT pair that ND8 describes. Held with E-49 and E-50 (gate G5), because the route (ND8) and the way a paid call is excluded (ND6) are not decided. "The lead" is the Claude session defined in E-26. The old text is the "Enforced by" line that closes section 4 (line 28); the new text keeps it and adds the new section 4b, so no section is renumbered. The place of the section after section 4 and before section 5 is the studio lead's to confirm when G5 opens. Round 9 (design M4): the MAY line now names the same written consent as E-49 (`Yes, send the one enquiry on <day>`), not "the owner's message naming the day". Apply together with E-49 and E-50 when gate G5 opens.

### E-54: OWNER-STEPS-realrun-v3.md, line 85, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
## Phase 1: the lead checks (no steps for you except being reachable). Wed to Sun.
~~~~
NEW (exact):
~~~~
## Phase 1: the assistant checks. You only need to be reachable and to answer the questions it asks. The days are not fixed: the take is aimed at Wed 18 Nov 2026.
~~~~
Why: Round 9 (naive B5, B16): the heading said "no steps for you" and "Wed to Sun" while rows E-09 and E-11 add replies and the held row E-49 adds owner steps; "Wed to Sun" is a timetable that no input fixes. Q21.1 of the studio lead answers in ORDERS (take target Wed 18 Nov, not fixed) gives the take target, so the heading says only that. "The lead" becomes "the assistant" (E-01, E-52). The old text is the whole heading line 85 (occurs once).

### E-55: OWNER-STEPS-realrun-v3.md, line 119, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
### Step 22. Retirement, by Mon 23 Nov 18:29 UTC (23:59 IST)
~~~~
NEW (exact):
~~~~
### Step 22. Retirement. The secret key for the model is revoked by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke); the rest of the retirement is done by 18:29 UTC = 23:59 IST (the end of the spending window). The take is planned for Wed 18 Nov 2026, so retirement normally follows the take on the same day.
~~~~
Why: Design M1 of round 9: the heading of step 22 said "by Mon 23 Nov 18:29 UTC (23:59 IST)" for the whole retirement while E-48 puts the model-key revoke inside step 22 with the last time to revoke 18:19 UTC = 23:49 IST (Q25: at least 10 minutes before the stop). The two deadlines are now on the heading: model-key revoke 18:19 UTC = 23:49 IST, rest 18:29 UTC = 23:59 IST (all arithmetic checked: 18:19 + 5:30 = 23:49; 18:29 + 5:30 = 23:59; Mon 23 Nov 2026 is a Monday). "Wed 18 Nov, same day" is Q21.1 (target Wed 18 Nov, not fixed; the owner cancels the run key right after the take, same day). The old text is the whole heading line 119 and occurs once; it overlaps no other row.

### E-56: AGENT-SCOPE-DO-AND-DONT.md, line 20, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
- MAY: post this take's own generated lead keys (L plus hex);
~~~~
NEW (exact):
~~~~
- UNVERIFIED (Q23): two statements later in this line (the clause "ARCHIVE ... DELETE call" and the NOTE (F-01) at the end of the MAY part of this line; the word "archive" in line 23 is the same) say that the end of the take removes the take's HubSpot contacts. That is an earlier reading of the code. A later independent review (r17) found no delete or archive path, and decision 2 of 2026-11-16 says the take never deletes contacts. Which reading is right is NOT SETTLED; the lead shows a search of the final code at re-pin. Until then do not rely on either statement, and do not widen the HubSpot key.
- MAY: post this take's own generated lead keys (L plus hex);
~~~~
Why: Design M4 of round 9: during the hold (E-40, E-44, E-45 are held on gate G1) line 20 of the sheet that the assistant obeys still stated as fact that the take deletes ("which the code does as a DELETE call (`run_real_check_n8n.py:1051`, ...)"), against Q23 (line 1051 is UNVERIFIED stale text). The flag is put in FRONT of the line as its own bullet, not inside the clause, because an edit inside the clause would overlap the old texts of E-40 and E-44 (the script checks that no two old texts overlap). The flag states neither reading as fact. When gate G1 opens the studio lead applies E-40, E-44 and E-45 and deletes this bullet (rule R9). The old text is the first words of line 20 and occurs once; E-31 (end of the same sentence) does not overlap.

## Lines checked and found consistent
Numbers in brackets such as (EL-7) name the earlier-list item the line was checked against (EL-n and D-n are explained at the top). Covered means read line by line.

**OWNER-STEPS-realrun-v3.md**
- 1-2, 4, 6-17: title, words used, framing. Consistent ((EL-7) made-up data; (EL-2) none says execution saving is off).
- 18-26 (the six rules): consistent with (EL-7) for secrets typed by the owner, and with the money design (one paid call per lead id). Rule 4 is consistent with AGENT-SCOPE lines 14-16 (backstop cap checked by eye).
- 27-72 except 69: steps 1 to 7 (accounts, app passwords, filter, HubSpot property and apps). No line touches Postgres, executions, portal, approval, audit trail, egress or branches, so they do not contradict the decisions; but they list items the owner has ALREADY DONE (FACTS-ALREADY-DONE.md), which is the stale item handled in E-37 (round 1 review D-M5).
- 74-77, 80-84: step 8 apart from the rows E-06 to E-09; step 9 sentences.
- 85-86, 88-91, 93-94, 96-98, 100-105, 108-120, 122-130, 132-138 apart from the rows: steps 17 to 23 text not named in a row (typed answers, tag marker, filming, take failure, cut, retirement items 2 to 6, the three decisions). Step 22 item 1 (line 121) is consistent with EL-1 and EL-2 except the one phrase in E-16. Step 22 item 5 (retire check) is consistent with AGENT-SCOPE line 20 (two of four secrets).
- 140-150, 152-158, 160-161, 163, 165, 167-177, 179-192: sections "What to send", "Status", exit codes, optional name, UNVERIFIED items 1 to 7, 9 to 13. The test counts on lines 152 to 158 equal those on AGENT-SCOPE lines 16 and 22 (697/115, 810/2, 166, 445, 118/2, 71/6, 18/0).
- Whole file, word search for "portal", "approv", "audit": no claim of a portal, approval step or audit trail. Consistent with EL-3 and D1. "branch" appears only for the local take branch (EL-6).
- Whole file: no line says execution saving is off or that no executions are kept, except the cleanup wording in E-16 (EL-2).

**AGENT-SCOPE-DO-AND-DONT.md**
- 1, 3-4, 6, 8, 10-14: section 1 MAY list, start-script enforcement (allowed names `DB_*`, `EXECUTIONS_*`, forced `N8N_BLOCK_ENV_ACCESS_IN_NODE`: consistent with EL-1, EL-2 and plan v5 step 1.2/1.2b), other enforcement, section 2 identity and MAY.
- 7 (apart from the key phrase in E-30): "save executions that hold real data ... saved ON, made-up data only, and deleted at clean-up" is consistent with EL-2.
- 9 first sentences: "executions saved only for the made-up take data and deleted at clean-up" consistent with EL-2.
- 15-17: money stage (cap and window end backstop, journal write-ahead, `stage.journal` as the one exception: consistent with EL-1).
- 18-19, 20 (apart from E-31), 21-22, 23 (apart from E-32, E-33): take script. The F-01 note itself is consistent with today's delete call; D2 now says the take never deletes, so the line is changed in E-40 and E-44 (E-31 and E-45 cover other parts of lines 20 and 23).
- 24-26, 28-31 (apart from E-34), 33-35: builders rule "no push", "no live model call", "no real key", sections 5 and 6.
- Whole file, word search for "portal", "approv", "audit": no claim of a portal, approval step or audit trail (the word "audit" occurs only inside the path `architecture-audit`). Consistent with EL-3 and D1.

**Plan v5 and DECISION-one-store compared with both documents**: the rehearsal costs US$0 (EL-5) matches AGENT-SCOPE line 27 ("no live model call or real key"); `stage.journal` stays a file (EL-1) matches AGENT-SCOPE lines 14 to 16 and 20.

## What I did not check
- Nothing was run: no command, no test, no network. I did not read the plan's steps 0.1 to S11 line by line (only the steps that touch Postgres, executions, clean-up and the tail sections), so a step order change outside those could be missing from this list (plan v5 lines 225 to 400, except S1b, S2, are only skimmed).
- I did not read smoke-1 evidence, the code (`n8n_start.sh`, `n8n_kill.py`, `run_real_check_n8n.py`), the run book `WP6-RUNBOOK.md`, `plan-4-nlite.md` or `review-codebase-1.md`; every line number and code claim in the two inputs is taken as written.
- I did not verify HubSpot, Gmail, Google or n8n click paths, scope names, SMTP host, or what n8n stores in a saved mail step.
- Dates and times (IST/UTC conversions, 14 versus 15 minutes) were not recomputed.
- Round 3 added: I did not run anything; I did not re-read the plan beyond lines 76, 151 and 485-492; EL-1 to EL-7 (the earlier lead decisions) are taken from the C4 brief as the round 2 reviewers listed them, not from a file; I did not check whether the code already prints a list of leftover contacts, nor what the program's pause prompt will say after the change (E-41, E-44).
- The plan's 558 lines: sections named "12" and "13" do not exist as numbered sections; I read the steps S12 and S13 instead (clean-up, one-store checks) and used them.
- The old-evidence numbers on OWNER-STEPS lines 152 to 158 and AGENT-SCOPE lines 16 and 22 are stale for the current head by their own admission; I did not try to replace them.
- Round 5 added: nothing was run except the text check (old texts occur once, counts); I did not read the code, the smoke evidence or any click path; EL-1 to EL-7 are still taken from the C4 brief; the new NOT DECIDED options in items 1, 3 and 6 are proposals and nothing read proves that the start script or the code supports them.

- Round 6 added: nothing was run except text and count checks by script (`resolve-r6.md`); I did not read the code, the smoke evidence, any click path, `review-codebase-1.md`, `WP6-RUNBOOK.md` or the plan beyond the lines named at the top; EL-1 to EL-7 are still taken from the C4 brief; the options in NOT DECIDED 1, 3 and 6 are proposals and nothing read proves the start script or the code supports them; the mechanism that lets the preparation test contact pass without a paid model call is UNVERIFIED (E-11); the plan's meaning of "flow rehearsal" (D12) is not in any input beyond the decision line, so E-03 only states its cost from EL-5; the new owner texts are not yet read by a stranger.

- Round 7 added: nothing was run except text and count checks by script (`resolve-r7-check-output.txt`); I did not read the code, the smoke evidence, any click path, `review-codebase-1.md` (NEEDS-STUDIO-LEAD, E-31), `WP6-RUNBOOK.md`, or the plan beyond the lines named at the top; EL-1 to EL-7 are still taken from the C4 brief (NEEDS-STUDIO-LEAD, NOT DECIDED 10); the text of rules A, E, F and I of D5 is not in any input (NEEDS-STUDIO-LEAD, section on D5); how the preparation enquiry reaches the accounts (ND8), whether it passes without a paid call (ND6), the meaning of "flow rehearsal" beyond its cost (D12), the start-script options (ND1), the program's pause prompt after the code change (G1) and what the row preview of n8n's table step shows (E-15) are unproven; the new owner texts are not yet read by a stranger; the Hold rows' texts are not applied-tested except as text. The egm:egm-resolve skill was not used (see `resolve-r7.md`).

- Round 8 added: nothing was run except text and count checks by script (`resolve-r8-check-output.txt`). I did not read the code, the smoke evidence, any click path, `review-codebase-1.md` (NOT DECIDED 10), `WP6-RUNBOOK.md`, or the plan beyond the lines named at the top and section 8 and step 3.3. The mechanism that keeps a paid model call impossible in the flow rehearsal and in the preparation enquiry (ND6) is UNVERIFIED; the route of the preparation enquiry (ND8) is not decided; whether the stage accepts a made-up key value outside the stand-in test is unproven; the glosses of the plan codes in the words list are my reading of the plan; the click path of the model provider's key list (E-48) is unchecked; the new owner texts (E-01, E-09, E-11, E-12, E-14, E-15, E-16, E-48, E-49, E-52) are not yet read by a stranger. The egm:egm-resolve skill was not used (see `resolve-r8.md`).

- Round 9 added: nothing was run except text and count checks by script (`resolve-r9-check-output.txt`). I did not read the code, the smoke evidence, any click path, `review-codebase-1.md` (NOT DECIDED 10), `WP6-RUNBOOK.md`, or the plan beyond the lines named at the top. Whether the take program contains a contact delete call at the final head is not settled (Q23) and nothing in this file claims either; the evidence is the studio lead's grep at re-pin. The mechanism that keeps a paid model call impossible in the flow rehearsal and in the preparation enquiry (ND6) is a control written in E-11, but that the model stage accepts a made-up key value and a stand-in address in the flow rehearsal is UNVERIFIED; the route of the preparation enquiry (ND8) is not decided; that the start program reads a database password from a file (E-09, ND1) is unproven; the click paths of E-04, E-48 and E-49 (HubSpot website, the model provider's key list) are unchecked; the latest start time of about 18:14 UTC = 23:44 IST comes from a reading of OWNER-STEPS line 171, not from the code; the new owner texts (E-04, E-09, E-11, E-12, E-14, E-15, E-16, E-18, E-37, E-48, E-49, E-52, E-54) are not yet read by a stranger; no one has checked that v4 can be written from these rows in one pass. The egm:egm-resolve skill was not used (see `resolve-r9.md`).
