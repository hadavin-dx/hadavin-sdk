# C4 steps versus decisions: exact edit list (round 7; draft by a builder, independent reviewers judge it)

Compared: `inputs/OWNER-STEPS-realrun-v3.md` (193 lines, called OWNER-STEPS below) and `inputs/AGENT-SCOPE-DO-AND-DONT.md` (35 lines, called AGENT-SCOPE) against: (a) the twelve decisions of `inputs/DECISIONS-2026-11-16.md`, cited as D1 to D12 with that file's own numbers (D1 scope and narrow claim; D2 take is read-only, never deletes contacts; D3 four-login proposal parked; D5 security items, part S9-3 the owner revokes the model key; D6 ports; D7 first-visit setup done; D8 no extra real smoke; D9 counts proof screen; D10 wording "one Postgres server with two databases", v4 replaces v3; D12 first laptop rehearsal); (b) `inputs/DECISION-one-store.md`; (c) `inputs/FACTS-ALREADY-DONE.md`; (d) plan v5 (`inputs/plan-wp6-resmoke-v5.md`; read: header and change tables, sections 0 to 3, the steps that touch the database, executions and clean-up, sections 5, 8, 9, 10, 11, the UNVERIFIED list and, in rounds 6 and 7, plan lines 14, 76, 81, 102, 121, 477, 489, 492, 502, 505, 506; round 7 also read OWNER-STEPS lines 1 to 26, 58, 69 to 92, 99 to 107, 120 to 126 and 176 to 193, AGENT-SCOPE lines 7 to 14 and 24 to 40, DECISION-one-store lines 14 and 20 and DECISIONS-2026-11-16 line 6); (e) seven earlier lead decisions that the C4 brief gave the builder and that are NOT a file in `inputs/`, cited as EL-1 to EL-7: EL-1 one Postgres server for everything we own; EL-2 saved runs ON for the take, deleted at clean-up; EL-3 narrow claim and no portal, approval or audit claim; EL-4 n8n's outgoing traffic is switched off by settings and only observed; EL-5 the tests on this laptop cost US$0 and come before any real take; EL-6 take branches stay on this laptop; EL-7 no real keys, mailboxes or client data for agents, the tests on this laptop and cloud sessions. EL-1 to EL-7 live only in this paragraph (FOR THE LEAD TO CONFIRM g). Where an EL item and a D item cover the same subject both are cited (EL-3 is also D1). Nothing was run except text checks; the inputs were not edited.

Round history: rounds 1 to 4 are in `resolve-r1.md` to `resolve-r4.md`; round 5 (`resolve-r5.md`) was reviewed by two independent reviewers (`review-c4-r5-design.md`: 0 Blockers, 4 Majors, 8 Minors; `review-c4-r5-naive.md`: 3 Blockers, 11 Majors, 8 Minors); round 6 (`resolve-r6.md`) applied all of it and was reviewed by two independent reviewers (`review-c4-r6-design.md`: 0 Blockers, 4 Majors, 9 Minors; `review-c4-r6-naive.md`: 8 Majors, many Minors); round 7 (`resolve-r7.md`, money, secret and delete paths: no round cap) applies all of it. The result of round 7 is NOT reviewed yet. The round 5 file is kept as `EDITS.round5.md` and the round 6 file as `EDITS.round6.md`.

## How to read a row (quoting convention, round 6)
Every old text and new text is a block between two lines of four tildes (`~~~~`). The text is EXACTLY the lines inside the block, joined by line breaks, and nothing else: no quotation marks, no backtick padding, no table bars. A backtick or a double quote inside a block is part of the text. A new text of several lines becomes several lines of the file. Old and new texts never start or end with a space. Each old text was checked by script to occur exactly once in its file, on the line stated, and no two old texts on the same line overlap (output in `resolve-r6.md`).

## Words used in this file and in the owner texts (round 7)
One word keeps one meaning. The owner texts define their words at first use in E-01 (line 3 of the sheet, the first edited place).
- **the assistant** (owner texts) = Claude working with the owner; the sheet's old words "the lead" mean the same (E-01 says so inside the sheet). **the studio lead** (this file) = the studio lead session that applies the rows, opens the gates and answers the NOT DECIDED items marked "studio lead". Rounds 1 to 6 wrote "the lead" for it; round 7 writes "the studio lead" outside the quoted texts. Inside a quoted AGENT-SCOPE text "the lead" is that file's own word.
- **enquiry** = one made-up sales message sent through the flows (the public post on line 131 keeps its own word "lead" for it). **contact** = the made-up person an enquiry creates in HubSpot. **lead key** = the made-up identifier the program gives an enquiry. **secret key** = a long text that works like a password for a service (HubSpot, the AI model provider); the sheet's old word "token" means the same. **password** = a word a person types (a database user's password, or the app password of a mailbox). Never a bare "key".
- **take** = one real recorded run on the owner's own test accounts (the sheet's "Words used"). **flows** = the automatic step chains that n8n runs. **model stage** = our small program that asks the AI model and enforces the money cap. **saved runs** = the past runs that n8n keeps and lists (n8n itself says "executions"). **preparation** = the last checks the assistant makes before it asks for the owner's yes (Phase 1); it includes the one preparation enquiry (E-11).
- **stand-in test** = the test on this laptop with stand-in programs and made-up data in plan v5 (D8, the loopback re-smoke). **flow rehearsal** = the first run of the changed flows on this laptop that follows it (D12). Both are planned at US$0 (EL-5); nothing about them is proven yet. The word "rehearsal" alone is not used in new texts.
- **counting check** = a small program of ours, not part of n8n, that counts mails, contacts and table rows. It is the one phrase used for this in E-15, E-18, E-31 and E-36. It has no read-only database user of its own (that user is not built; D3 parks it), so it is not claimed to be independent.
- **database server** = the one Postgres program in one **container**; **n8n's own database** and **the take's database** = the two databases on it; **database user** = a Postgres account. **login** = only a mailbox or HubSpot sign-in. (The decision file calls the parked proposal "four logins"; this file says "the proposal of four database users".)

## Gates (a row marked Hold is NOT applied until its gate is open)
- **G1, code change (E-04, E-05, E-40, E-41, E-42, E-44, E-45; carried into E-12 and E-37)**: D2 says the take never deletes contacts; today's code removes them (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, per `review-codebase-1.md` F-01). The gate is opened by the STUDIO LEAD (never by the builder and never by the owner) by writing the line `CODE-GATE G1 OPEN: <commit id>, <evidence file name>` into the newest checkpoint note, and only when all three hold: (1) the commit that removes the delete call from the take's end-of-take step is on the take branch; (2) a saved raw test output shows that the end-of-take step makes no delete call to HubSpot and prints the notice and list the rows describe (a test that fails on the old code and passes on the new); (3) independent `egm:*` reviewers have read the diff and that output and their saved report lists no open Blocker or Major (delete and money path: no round cap). If OWNER-STEPS v3 or v4 is issued before the line exists, these rows stay unapplied and no paid take starts. E-12 (fact 4 of the yes message) and E-37 carry this gate into text that is applied now: the assistant cannot state fact 4 until the line exists, so it cannot send the message. Whether the code already prints the list of leftover contacts by lead key and contact id is UNVERIFIED.
- **G2, later wording only, Windows reaching n8n in WSL (E-07, E-08)**: E-07 and E-08 are applied now with neutral words (round 7). G2 only decides a second wording: opened by the studio lead after reading the first-smoke evidence for plan item P14; the studio lead writes `ND5: proven <file>` or `ND5: not proven <file>`; if proven, the second wording in the Why of E-07 and E-08 replaces the neutral one.
- **G3, second edit pass (E-13)**: opened by the studio lead when the stand-in test result file (in `evidence-2`, its INDEX) exists and independent reviewers have read it; the lead writes the report name.
- **G4, saved-runs method (E-39)**: opened when NOT DECIDED 3 is answered (the answer decides the text).

## How the rows are used
OWNER-STEPS v3 is archived, never edited or deleted (D10). The OWNER-STEPS rows are the edit list the lead applies while writing OWNER-STEPS v4 (queue item C4b), which replaces v3 and keeps only what is still owner-only; a row about a step that v4 strips (Phase 0 steps 1 to 7 and 9, perhaps step 8) falls away there. If v3 is read before v4 exists, only E-37 (a status note) should be applied to it. The AGENT-SCOPE rows patch that file in place; the DECISION-one-store rows (E-39, E-43, E-46, E-47) are applied by the lead (the file is in `inputs/`; E-39 changes the written record of an owner approval and is not applied tonight). Ids are not renumbered: E-10 was deleted in round 3 (D7) and E-35 in round 5 (its content is part of E-34), so the ids run E-01 to E-48 without E-10 and E-35.

## Counts (computed by script, `resolve-r6.md`)
46 rows in total: E-01 to E-48 without E-10 and E-35. By file: OWNER-STEPS 29 rows, AGENT-SCOPE 13 rows, DECISION-one-store 4 rows (the lead applies those). By status: **Apply now 34**, **Hold 11** (gates G1 to G4: E-04, E-05, E-07, E-08, E-13, E-39, E-40, E-41, E-42, E-44, E-45), **Conditional 1** (E-48, on NOT DECIDED 7a); total 46. Among the Apply now rows, E-36 has two texts and applies text W by default. By type: STALE 15, UNCLEAR WORD 6, MISSING STEP 10, CONTRADICTION 12 (including the rows marked as code-change gated), DEFERRED 3; total 46.

## NOT DECIDED: lead or owner only (items 1 to 7). Each item says who answers, the options with cost and risk, the default, and where the answer is written
Where answers are recorded: the studio lead creates `steps-edits/ANSWERS-c4.md` and writes one line per answer: `ND<number>: <answer>, <who>, <date and time in UTC and IST>` (for the owner's answers the line quotes his message). Until a line exists the default applies.
1. **Where the password of n8n's database user (a line in `n8n.env`) is kept, so that the assistant never opens secret files** (E-09, E-30). Who answers: the studio lead. Premise not verified: D3 parks the four-login proposal, so whether n8n gets its own database user or shares one is UNVERIFIED (DECISION-one-store line 20), and nothing read proves that the start script supports options b and c. Options: (a) you type the password yourself into `n8n.env` in WSL, in an editor and NOT on a command line (a command line is saved in the shell history), and the assistant never opens the file (no code change; the assistant cannot check the value; risk: a typing slip stops n8n and delays the take); (b) the start script asks for the password at the keyboard each time, hidden as you type and NOT as a word on the command line (a code change in a script that handles a secret: it needs independent review with no round cap; the password is in no file; risk: the assistant cannot start n8n alone); (c) the start script writes a random password into a file readable only by its owner that nobody reads (a code change in a script that handles a secret: independent review with no round cap; no human password; risk: the file is a secret on disk until clean-up). Cost: assistant time only, no money. Default: (a). Pass or fail for (a): n8n starts and the assistant's own check shows that n8n can open its database (the assistant sees only "ok" or "not ok", never the password). Record: `ND1: a|b|c`.
2. **The address (port number) of the real take's n8n** (E-06). Who answers: the studio lead. D6: it uses its own free port, not 5678 or 5679 (your own n8n) and not the ports of plan v5 section 2 (5690 to 5693, 8765, 48767, 8771, 2526, 55433); the number is in no document. Answer: one free port number, written in the plan's port table and in the answers file. No cost. Default: until answered, the assistant names the port in its message that says n8n is running (E-06 says "the address the lead gives", and the lead there is the assistant); the studio lead then writes it into the plan's port table and the answers file. Record: `ND2: <number>`.
3. **How saved runs are deleted at the real take** (E-16, E-38, E-39). Who answers: the studio lead for (a); the owner's one-line yes is needed for (b), because (b) is not the step he approved. Facts: plan v5 line 81 says the real-take method is undecided (the stand-in test uses container removal); line 502 lists it as not proven. Options: (a) turn the saving setting off, delete the runs, then remove the container (matches the approved owner decision; a few minutes of assistant time; a deletion step that can fail); (b) only remove the container (one step; less proof that the runs are gone before the container goes; not the approved wording). Default: until answered, E-16 and E-38 keep the approved step and name container removal as the stand-in test's method only, and E-39 is not applied (texts per answer are in E-39). Owner's answer text for (b): `Yes, at clean-up you may delete the saved runs only by removing the container of the database server, instead of turning saving off and deleting the runs first.` Record: `ND3: a|b <owner message>`.
4. **Which database user's password you type for the n8n table steps** (E-09). Who answers: the studio lead names the database user (never the password); you type its password. Only one option is allowed: the app user (the user the n8n table steps use: plan v5 section 10 points to it; planned as a restricted user, not yet proven). NOT allowed, because of least privilege: the administrator of the database server; n8n's own database user (it belongs to n8n's own database, not to the table of leads); the read-only counting user (not built; D3 parks it). Default: the app user. Pass or fail: as for ND1 (a). Record: `ND4: <user name>`.
5. **Windows reaching n8n in WSL (E-07, E-08; plan item P14).** Who answers: the studio lead. The plan says it was proven in the first smoke; nobody on this branch has read that evidence. Action: the studio lead reads the first-smoke evidence for item P14 and writes `proven` or `not proven` with the file name (opens gate G2). E-07 and E-08 are already applied with neutral words; G2 only chooses a second wording and is moot if v4 drops step 8. Record: `ND5: proven|not proven <file>`.
6. **Money: may the one made-up test contact in take preparation make a paid model call (E-11)?** Who answers: the owner, only for option B; option A needs no answer. Question for the studio lead: see ND8 (how the enquiry gets in). Option A (default, written in E-11): no paid call; cost US$0; if the test contact cannot pass without a call, the assistant stops and asks (mechanism UNVERIFIED); risk: the preparation test does not exercise the real model path. Option B: ONE paid call, outside the take's 3 calls (D8 does not say it is paid and no input describes a separate consent), under the same US$ cap and window end. Owner's answer text for B: `Yes, ONE paid model call in the preparation test, up to US$<one figure the assistant states>, outside the 3 calls of the take, same cap, window end 2026-11-23 23:59 IST.` The studio lead's task for B: take the per-call worst-case figure from the stage settings (as for step 16) and give it to the assistant to state; the assistant does not compute its own figure. Cost: that one figure; risk: money spent before the take. Record: `ND6: A` or `ND6: B <owner message>`.
7. **Are the keys dedicated and of the right scope?** Who answers: the owner, in one line each (or the assistant checks the key lists with him). In plain words: (a) "Is the secret key for the model that you saved one that you made only for this take, and does nothing else use it?" Answer: `7a: yes` / `7a: no, others use it` / `7a: not sure`. (FACTS names a "new key 2026-11-13"; revoking a shared secret key at clean-up (E-48) would break the other things.) (b) "In HubSpot, Private Apps: does app 1 show only the permission contacts read (no write, no delete), and does app 2 exist?" Answer: `7b: app 1 read-only, app 2 exists` / `7b: no` / `7b: not sure`. ("Scope" means the list of things a key is allowed to do. FACTS says only "key given", and the keys were "already used in earlier local runs", so the permissions are unknown.) Cost of a wrong answer: a full-permission HubSpot key used by the take breaks the least-privilege rule; a shared model key revoked by mistake breaks other work. Default: unanswered counts as "not sure": E-48 still applies, with its safe default (the assistant asks you at clean-up whether to revoke; you revoke only after a clear yes) and E-04 and E-37 keep the assistant's confirmation step. Record: `ND7a:` and `ND7b:` lines.
8. **How the one made-up preparation enquiry reaches your throwaway accounts (E-11, E-12).** Who answers: the studio lead; the owner only if money is involved (ND6). No input says which way it goes in, no AGENT-SCOPE row allows either way, and nothing shows whether it counts against the take's 3 model calls, its spend ledger and its journal (UNVERIFIED). Options: (A) through the take program: you type `y`, the confirmation number and the take id yourself (AGENT-SCOPE line 27 forbids the assistant from answering those prompts), and the single-use take id and the notice are spent on the preparation; risk: the real take then needs a new take id and notice; (B) the assistant posts the enquiry straight to the take's own n8n web address on this laptop; n8n then uses the credentials you typed into it, the assistant holds no real secret key and answers no prompt; risk: the take program's ledger and journal are bypassed unless the flow writes them (UNVERIFIED). For (B) the studio lead adds one AGENT-SCOPE row (section 2, a new MAY and MUST NOT pair): MAY post ONE made-up enquiry to the take's own n8n address in the preparation, after the owner's message naming the day; MUST NOT post a second one, read or print n8n's credentials, use a secret key of its own, or cause a model call that ND6 does not allow. Cost: assistant time; no money unless ND6 is B. Default: nothing is sent until ND8 is answered; E-11 already says the assistant tells you the way before it sends. Record: `ND8: A|B <date and time in UTC and IST>`.

## FOR THE LEAD TO CONFIRM (a reading or a source, not a decision; letters run a to g without gaps)
a. EL-7 read literally ("no real keys, mailboxes or client data") would void the real take's throwaway Gmail accounts, the HubSpot test account and the model key. FACTS-ALREADY-DONE.md and AGENT-SCOPE lines 27 and 32 show it applies to agents, the tests on this laptop and cloud sessions, not to the owner's own approved take accounts. Edits are made on that reading.
b. E-36: do the mail count and the contact count really run on credentials of their own (only the table count runs as one database user through `docker exec psql`)? Answer yes or no. Default no: text W is applied; yes: text N replaces it before the post is written.
c. E-23, E-34: EL-6 (take branches stay on this laptop) is in no input file; the plan only says the runner never commits, pushes or merges (plan v5 line 489). The rows follow that plan wording; add a rule about cloud sessions only if you confirm EL-6.
d. E-12 (the assistant's message and the owner's yes state five facts: both tests ran with counts, where the written result is, that independent reviewers read it, that the end-of-take step no longer deletes (gate G1), that the preparation enquiry was sent and cleaned; and what "passed" means) is gating wording that follows EL-5, D12 and plan line 505 but is not literal in any of them; confirm it. The gate "no paid take starts before independent reviewers have read the result" (plan line 505) is not owner text on its own. E-14 (do not film the mail step) rests on a guess about what the saved mail step shows and stays flagged.
e. E-37: whether step 8 is wholly obsolete, and whether the take's own n8n needs the three credentials typed by the owner (FACTS says they are in the owner's own n8n on port 5678, which the take never touches; the plan gives the take a fresh n8n). Until confirmed, E-37 tells the owner not to do step 8 unless asked.
f. Whether the plan's step S1b and row L4 (the database users) still run, given D3.
g. NEEDS-LEAD (not fixable from this folder: the C4 brief is not in it): EL-1 to EL-7 are only in the first paragraph of this file, from the C4 brief; the studio lead checks that text against the brief and writes the result into `ANSWERS-c4.md`. If one is wrong, the rows that cite it change (EL-1: E-09, E-27, E-30; EL-2: E-14, E-16, E-38; EL-3: E-17, E-18; EL-4: E-18, E-29, E-34; EL-5: E-03, E-12; EL-6: E-23, E-34; EL-7: confirmation a).

Removed in round 3 (each was answered by a decision, or is not for the lead): old item 1 (HubSpot app 1 and the delete right: D2); item 2 (kept above as confirmation a); item 5 (real-account smoke: D8); item 6 (first-visit setup: D7; row E-10 deleted); item 8 (proof screen: D9); item 9 (two meanings of "round": plan v5 line 76, see E-02); item 10 (wording: D10); item 11 (filming the mail step: the owner's yes message, see E-14 and R5); item 12 (rewrite of Phase 0: v4 replaces v3, D10 and queue item C4b). From the first draft: the fill-step question (E-33), the second edit pass after the run (now E-13), and the clean-up method for saved runs (now NOT DECIDED 3; plan v5 lines 81 and 502).

## Rules for the lead (round 6)
Where the evidence is: the stand-in test's results are written into the INDEX of `evidence-2` (plan v5 line 477, row NC; line 505, row DM). Who judges: independent `egm:*` reviewers read them (plan line 505), never the runner and never the builder. "Passed" is as defined in E-12.
- **R1 (E-17)**: after the stand-in test, delete the clause "a crash at exactly the moment between sending the mail and noting it in the table may send the mail twice" only if plan row DM PASSED (no row with two mails) AND (E passed or E2 passed, not both missed) AND independent reviewers have read the INDEX; if DM was not tested, was missed, or showed two mails, keep the clause. When it is deleted the lead also updates E-22's sentence on line 166 and E-25 item 18.
- **R2 (E-18)**: drop only the narrow item "that the count is made by a different database user", and only when the read-only count user (plan row L4) is built and its run is shown in the INDEX and read by independent reviewers. The item "that the take is crash-safe" is NOT dropped while plan row NC lists crash windows that no test covers (before the claim; after the model call and before the contact is written; and the mail window if DM was missed); "crash-safe" stays forbidden. All other items stay.
- **R3 (E-36)**: text W applies by default; text N applies only if confirmation b is answered yes.
- **R4 (E-39)**: not applied tonight; when NOT DECIDED 3 is answered, apply the text for that answer (E-39 gives text per answer, with the follow-on for E-16 and E-38). The record of the owner approval itself is never rewritten.
- **R5 (E-14)**: apply as written. If the owner wants the mail step filmed, he says so in his yes message; the assistant then reads what the mail step shows in the stand-in test before it is filmed.
- **R6 (E-12, E-37)**: before the assistant sends the yes message (step 16), the studio lead checks that the files named in the five facts exist, that the reviewers' report lists no open Blocker or Major, and that the line `CODE-GATE G1 OPEN: ...` exists. If any is missing, the message is not sent. This check does not replace the owner's: the owner answers no to a message that lacks a fact (E-12).

## The edit index (no texts here; the texts are in the row blocks below)
| id | file | line | status | gate | type |
|---|---|---|---|---|---|
| E-01 | OWNER-STEPS-realrun-v3.md | 3 | Apply now | - | STALE |
| E-02 | OWNER-STEPS-realrun-v3.md | 3 | Apply now | - | UNCLEAR WORD |
| E-03 | OWNER-STEPS-realrun-v3.md | 5 | Apply now | - | MISSING STEP |
| E-04 | OWNER-STEPS-realrun-v3.md | 69 | Hold | G1 | CONTRADICTION (code-change gate) |
| E-05 | OWNER-STEPS-realrun-v3.md | 95 | Hold | G1 | CONTRADICTION (code-change gate) |
| E-06 | OWNER-STEPS-realrun-v3.md | 75 | Apply now | - | CONTRADICTION |
| E-07 | OWNER-STEPS-realrun-v3.md | 75 | Apply now | - (second wording: G2) | UNCLEAR WORD |
| E-08 | OWNER-STEPS-realrun-v3.md | 187 | Apply now | - (second wording: G2) | UNCLEAR WORD |
| E-09 | OWNER-STEPS-realrun-v3.md | 78 | Apply now | - | UNCLEAR WORD |
| E-11 | OWNER-STEPS-realrun-v3.md | 87 | Apply now | - | CONTRADICTION |
| E-12 | OWNER-STEPS-realrun-v3.md | 92 | Apply now | - | MISSING STEP |
| E-13 | OWNER-STEPS-realrun-v3.md | 99 (and 11) | Hold | G3 | DEFERRED |
| E-14 | OWNER-STEPS-realrun-v3.md | 107 | Apply now | - | UNCLEAR WORD |
| E-15 | OWNER-STEPS-realrun-v3.md | 107 | Apply now | - | CONTRADICTION |
| E-16 | OWNER-STEPS-realrun-v3.md | 121 | Apply now | - | STALE |
| E-17 | OWNER-STEPS-realrun-v3.md | 131 | Apply now | - | CONTRADICTION |
| E-18 | OWNER-STEPS-realrun-v3.md | 131 | Apply now | - | MISSING STEP |
| E-19 | OWNER-STEPS-realrun-v3.md | 159 | Apply now | - | STALE |
| E-20 | OWNER-STEPS-realrun-v3.md | 162 | Apply now | - | STALE |
| E-21 | OWNER-STEPS-realrun-v3.md | 164 | Apply now | - | STALE |
| E-22 | OWNER-STEPS-realrun-v3.md | 166 | Apply now | - | MISSING STEP |
| E-23 | OWNER-STEPS-realrun-v3.md | 151 | Apply now | - | STALE |
| E-24 | OWNER-STEPS-realrun-v3.md | 178 | Apply now | - | STALE |
| E-25 | OWNER-STEPS-realrun-v3.md | 193 | Apply now | - | MISSING STEP |
| E-26 | AGENT-SCOPE-DO-AND-DONT.md | 2 | Apply now | - | STALE |
| E-27 | AGENT-SCOPE-DO-AND-DONT.md | 5 | Apply now | - | CONTRADICTION |
| E-28 | AGENT-SCOPE-DO-AND-DONT.md | 9 | Apply now | - | STALE |
| E-29 | AGENT-SCOPE-DO-AND-DONT.md | 9 | Apply now | - | MISSING STEP |
| E-30 | AGENT-SCOPE-DO-AND-DONT.md | 7 | Apply now | - | MISSING STEP |
| E-31 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Apply now | - | MISSING STEP |
| E-32 | AGENT-SCOPE-DO-AND-DONT.md | 23 | Apply now | - | STALE |
| E-33 | AGENT-SCOPE-DO-AND-DONT.md | 23 | Apply now | - | UNCLEAR WORD |
| E-34 | AGENT-SCOPE-DO-AND-DONT.md | 27 | Apply now | - | MISSING STEP |
| E-36 | OWNER-STEPS-realrun-v3.md | 131 | Apply now | - | CONTRADICTION |
| E-37 | OWNER-STEPS-realrun-v3.md | 27 | Apply now | - | STALE |
| E-38 | AGENT-SCOPE-DO-AND-DONT.md | 9 | Apply now | - | STALE |
| E-39 | DECISION-one-store.md | 23 | Hold | G4 | STALE |
| E-40 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Hold | G1 | CONTRADICTION |
| E-41 | OWNER-STEPS-realrun-v3.md | 103 | Hold | G1 | CONTRADICTION (code-change gate) |
| E-42 | OWNER-STEPS-realrun-v3.md | 104 | Hold | G1 | CONTRADICTION (code-change gate) |
| E-43 | DECISION-one-store.md | 14 | Apply now | - | UNCLEAR WORD |
| E-44 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Hold | G1 | CONTRADICTION |
| E-45 | AGENT-SCOPE-DO-AND-DONT.md | 23 | Hold | G1 | STALE |
| E-46 | DECISION-one-store.md | 14 | Apply now | - | STALE |
| E-47 | DECISION-one-store.md | 1 | Apply now | - | UNCLEAR WORD |
| E-48 | OWNER-STEPS-realrun-v3.md | 123 | Apply now | - | MISSING STEP |

## The row blocks
### E-01: OWNER-STEPS-realrun-v3.md, line 3, status Apply now, type STALE
OLD (exact):
~~~~
wt\nlite-int`).
~~~~
NEW (exact):
~~~~
wt\nlite-int`). Edited on Mon 16 Nov 2026 to follow the plan for the stand-in test (version 5) and the decisions of 2026-11-16; this edit is still to be checked by a second person, and what is still to be checked in the facts is listed at the end of this file under UNVERIFIED. Words used in the edited parts, each with one meaning: "the lead" in this sheet means the assistant (Claude) who works with you (new texts say "the assistant"); the stand-in test is a test of the take run on this laptop only, with stand-in programs (small fake versions of Gmail, HubSpot and the model) and made-up data; the take is one real recorded run on your own test accounts (see Words used below); the flows are the automatic step chains that n8n runs; the model stage is our small program that asks the AI model and enforces the money cap; an enquiry is one made-up sales message sent through the flows (the public post on line 131 keeps its own word, "lead", for the same thing); a contact is the made-up person that an enquiry creates in HubSpot; a lead key is the made-up identifier the program gives to an enquiry; a secret key is a long text that works like a password for a service (HubSpot, the AI model provider), which this sheet also calls a token; saved runs are the past runs that n8n keeps and lists (n8n itself calls them executions); the preparation is the last checks the assistant makes before it asks for your yes (see Phase 1).
~~~~
Why: Plan v5 header (pinned head is a temporary choice; later fix rounds in progress). Round 7 (naive glossary major, design order 7): the sheet's first edited place now defines, once, the words that the owner texts use: assistant versus "the lead", stand-in test, take, flows, model stage, enquiry, contact, lead key, secret key (and "token"), saved runs, preparation. "Flow rehearsal" and the "counting check" are defined where they are first used (E-03, E-15). "Edited ... still to be checked" stays (round 6: E-07, E-08, E-13 and E-36 are not verified against code). The personal folder path is not copied: the old text stops at the closing bracket. E-02 follows in the same line and does not overlap.

### E-02: OWNER-STEPS-realrun-v3.md, line 3, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
Independent review rounds 3 to 9 of the code are done; this file itself got a drift review (drift-report-1) and is corrected to it.
~~~~
NEW (exact):
~~~~
Independent reviews of the code (review rounds 3 to 9) are done. Later fix rounds 3 to 5 (batches of code changes made after the reviews) sit on the branches `take/nlite-int-r3` to `-r5` (a branch is a named copy of the code). Which code is under test is named in one place, at the top of the plan for the stand-in test, and that choice is not final. This file itself got a drift review (drift-report-1) and is corrected to it.
~~~~
Why: Plan v5 header and line 76 use "round" for review rounds and for fix rounds; one word keeps one meaning. Round 7 (naive minor): the old text now runs to the full stop of the sentence, so the new text ends with a full stop too (round 6 left the stop out on purpose and that was easy to paste wrongly); the nested brackets are split into short sentences. The old text was read in `OWNER-STEPS-realrun-v3.md` line 3 by eye: after it comes " Replaces `OWNER-STEPS-realrun.md` (v2" (checked by script that the old text occurs once). AGENT-SCOPE lines 16 and 22 keep their own dates and are read as review rounds.

### E-03: OWNER-STEPS-realrun-v3.md, line 5, status Apply now, type MISSING STEP
OLD (exact):
~~~~
The lead does everything else (start the database, the model stage and n8n, import the flows, run the checks). The exact commands for the lead are in `egm\duplicate-proof-lead-desk\nlite\WP6-RUNBOOK.md`.
~~~~
NEW (exact):
~~~~
The assistant does everything else (start the database server, the model stage and n8n, import the flows, run the checks). The exact commands for the assistant are in `egm\duplicate-proof-lead-desk\nlite\WP6-RUNBOOK.md`.

Before any real take the assistant runs two tests on this laptop. Both are planned at US$0, and nothing about them is proven yet:
- The stand-in test uses stand-in programs and made-up data only. No real account, no real secret key and no paid model call are planned. What n8n sends over the network is watched, not blocked, so we do not claim that nothing leaves the laptop.
- The flow rehearsal comes after the stand-in test has passed: the changed flows are run once on this laptop with made-up data, also planned at US$0.

The take is planned to keep its data in Postgres (a free database program). This is planned, not yet proven: in the first trial n8n kept its data in a simpler one-file database. One Postgres program, called the database server, is planned to run in one container (a sealed box in which a program runs) and to hold two separate databases: n8n's own database (flows, saved passwords, saved runs) and the take's database (our table of leads).

You do nothing for the two tests unless the assistant asks you, for example to start Docker Desktop (the program that runs containers). Blocking the network would need a Windows firewall rule (a setting that stops a program from using the network), which only you could set; none is planned.
~~~~
Why: EL-5 (the tests cost US$0 and come before any real take), D8 and D12. Round 7 (design M-A, design m6, naive minors): the Postgres design is stated as "planned, not yet proven" (E-25 item 15, E-27, E-28 and ND1 say the same; smoke-1 ran SQLite), and the flow rehearsal is "planned at US$0" (no input proves the cost; EL-5 gives it as a decision). The one long paragraph is split into short parts; the old text now runs to the end of line 5 so that the new text can end with its own line. The glossary words "take", "flows" and "model stage" are defined in E-01 on line 3, before this line. "the lead" becomes "the assistant" in the two places of the old text (E-01 says why). Plan line 102: network use is OBSERVED, not ENFORCED, so that sentence is limited to the stand-in test (what the flow rehearsal watches is not stated in any input). Plan P-4 and line 506: Docker Desktop is started by the assistant or the owner; a firewall rule is only option (c) of line 506 and none is planned. Whether the flow rehearsal also uses only stand-in programs is UNVERIFIED in the inputs; EL-5 gives only its cost. The file name `WP6-RUNBOOK.md` was already in the old text (it is a file name, not a code word in a sentence); the studio lead may replace it when v4 is written.

### E-04: OWNER-STEPS-realrun-v3.md, line 69, status Hold (gate G1), type CONTRADICTION (code-change gate)
OLD (exact):
~~~~
App 1 for the take program, scope contacts **read** only.
~~~~
NEW (exact):
~~~~
App 1 for the take program, scope contacts **read** only. Keep it read only: the take program never removes contacts (decision of 16 Nov 2026). Before the take the assistant confirms with you that the secret key the take uses is this read-only one and that app 2 exists. After the take you delete by hand in HubSpot the contacts of this take (the assistant gives you the list: the lead key of each contact and its HubSpot contact id, if the program printed it; otherwise the made-up names to look for). The one contact of the assistant's preparation enquiry is deleted by you before the take (see the paragraph in Phase 1 that begins "The assistant first runs the stand-in test").
~~~~
Why: D2: the take's secret key is read-only and the take never deletes contacts; the owner deletes leftovers by hand. FACTS-ALREADY-DONE.md line 3 says only "HubSpot test account, users created, key given": it does not say that app 1 or app 2 exist or what the saved key can do, so the assistant confirms (NOT DECIDED 7b). Round 7: the pointer to the preparation paragraph now names its first words (naive: it was never labelled); "key" is "secret key" and "lead key" is explained by E-01. Missing input (exact), why the row is held: the line `CODE-GATE G1 OPEN: <commit id>, <evidence file name>` (gate G1). GATE G1: the text is true only after the code change; today's code still removes contacts (see E-40, E-44).

### E-05: OWNER-STEPS-realrun-v3.md, line 95, status Hold (gate G1), type CONTRADICTION (code-change gate)
OLD (exact):
~~~~
up to 3 contacts archived at the end
~~~~
NEW (exact):
~~~~
up to 3 contacts created in HubSpot and left there (the take program removes none; you delete them by hand afterwards)
~~~~
Why: D2: the take never deletes contacts. The old words "archived at the end" are a delete call in today's code (AGENT-SCOPE line 20). GATE G1: the notice the program prints must change with the code. Missing input (exact), why the row is held: the line `CODE-GATE G1 OPEN: <commit id>, <evidence file name>`; the exact words of the changed notice are UNVERIFIED (apply this text only if the notice says the same). The same word on OWNER-STEPS lines 103 and 104 is handled in E-41 and E-42; Gmail's "Archive it" on line 50 is a different thing and stays. Round 7: "made-up" is dropped because "contacts" is now defined (E-01) as made-up people.

### E-06: OWNER-STEPS-realrun-v3.md, line 75, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
(it should be `http://localhost:5678` or similar;
~~~~
NEW (exact):
~~~~
(it is NOT `http://localhost:5678`, which is your own n8n and which the take does not touch;
~~~~
Why: Plan v5 section 2 ports and D6: the take n8n uses its own free port, 5678 and 5679 are the owner's own n8n. The number is in no document (NOT DECIDED 2). The old and new texts both stop at the semicolon; the one space that follows it in the file stays, so the next words (now E-07's applied text) read on correctly: "(it is NOT `http://localhost:5678`, which is your own n8n and which the take does not touch; it is not yet confirmed that your Windows browser can open that address ...". Round 7 (naive major): E-07 is applied now with neutral words, so no "there", "WP6", "WSL" code or "UNVERIFIED" label is left dangling in the owner text. The words "the address the lead gives" stay in the file and, by E-01, mean the assistant. If v4 drops step 8 this row falls away.

### E-07: OWNER-STEPS-realrun-v3.md, line 75, status Apply now (neutral text; a second text follows gate G2), type UNCLEAR WORD
OLD (exact):
~~~~
UNVERIFIED that Windows reaches WSL there, WP6 check (e))
~~~~
NEW (exact):
~~~~
it is not yet confirmed that your Windows browser can open that address (n8n runs inside WSL, the Linux window of your laptop); the assistant checks this with you before you type anything)
~~~~
Why: Round 7 (naive major: E-06 plus a held E-07 left "there" without a referent and shipped "WP6", "WSL" and "UNVERIFIED" to the owner). The neutral text says only what is true today: not yet confirmed. Plan v5 section 0 says the Windows reach to n8n in WSL was proven in the first smoke (plan item P14); nobody on this branch read that evidence (NOT DECIDED 5). Second text (apply only when the studio lead writes `ND5: proven <file>`, gate G2): "the first smoke showed that your Windows browser can open that address; the assistant checks it again with you before you type anything)". If `not proven`, keep the neutral text. The old text begins right after E-06's semicolon-and-space and ends the sentence's bracket; E-06 and E-07 do not overlap (checked by script).

### E-08: OWNER-STEPS-realrun-v3.md, line 187, status Apply now (neutral text; a second text follows gate G2), type UNCLEAR WORD
OLD (exact):
~~~~
8. The Windows browser reaching n8n in WSL at localhost.
~~~~
NEW (exact):
~~~~
8. Whether the Windows browser can open the address that the assistant gives for n8n (n8n runs inside WSL, the Linux window of the laptop; the plan says the first smoke showed it, and nobody has read that evidence yet).
~~~~
Why: Round 7 (naive: the row was not applicable without guessing). The old item is a bare label; the new text says what is unverified and why, without guessing the answer. Second text (only after `ND5: proven <file>`, gate G2): the same item with the end "(the first smoke showed it once; the assistant checks it again at the take)". If v4 drops step 8, the item is dropped there.

### E-09: OWNER-STEPS-realrun-v3.md, line 78, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
host, database, user as the lead names them; password = the one you set in WSL when you start the database (the lead gives the start command; you type the password).
~~~~
NEW (exact):
~~~~
host, database and user as the assistant names them (planned and not yet proven: this database user is a restricted one that may only read, add and change the rows of the table of leads, and it is not the administrator of the database server); password = the one you set in WSL for THAT database user when you start the database server (it is the password of a database user, not an app password and not a secret key). The assistant gives the start command and names the database user, never the password. You type the password yourself where the assistant tells you (a file you create in WSL, or a prompt of the start program), never as a word inside a command line, because a command line is saved in your shell's history list.
~~~~
Why: EL-1 and DECISION-one-store decision 1 (D10 wording). The owner types and keeps the password (OWNER-STEPS rule 2); the assistant names only the database user (NOT DECIDED 4: one allowed option, the app user); where n8n's own database user's password is kept is NOT DECIDED 1. D3 parks the proposal of four database users, so the privileges stay "planned and not yet proven". Round 7 (design m1, m3): the old text now runs through the full stop, so the old tail "(the lead gives the start command; you type the password)." is replaced and no duplicated sentence or "the lead" is left; "not on a command line" is added because a typed command is saved in the shell history. "login" means a mailbox or HubSpot sign-in only; Postgres accounts are "database users" and the three kinds of "password" are told apart.

### E-11: OWNER-STEPS-realrun-v3.md, line 87, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
The lead runs the checks (a) to (f) of the smoke (WP6-RUNBOOK) with NO paid call. If a check fails the lead tells you what to change.
~~~~
NEW (exact):
~~~~
The assistant first runs the stand-in test and then the flow rehearsal on this laptop (made-up data, no real account, planned at US$0 and with no paid model call). Then comes the preparation (the last checks before the assistant asks for your yes): the assistant sends ONE made-up enquiry through your throwaway accounts. Before it sends the enquiry, the assistant tells you which way it goes in (through the take program, where you type the answers yourself, or straight into the take's own n8n) and whether it counts against the 3 model calls of the take, and it does not send it before you have read that. No paid model call is planned for this enquiry. If the assistant finds that the enquiry cannot pass through without a paid model call, it stops and asks you; a paid call needs your separate written yes with a number first. The enquiry leaves one contact in HubSpot and one mail in the label `demo`: the assistant tells you so, you delete both by hand, and you tell the assistant "label and inbox empty" before the take. Pass: HubSpot shows exactly one new made-up contact, the label `demo` holds exactly one mail from this enquiry, and the assistant reports no error. Fail: none, more than one of either, or an error; then the assistant stops and tells you what to change. This one enquiry is the only run through real accounts before the take; there is no other real-account smoke test.
~~~~
Why: D8: the real-account smoke (checks a to f) is replaced by the tests on this laptop plus ONE made-up enquiry in take preparation; D12: it is sent right after the tests pass. EL-5: the tests cost US$0, so the text says "planned at US$0" (design m6; the cost is a decision, not proven). Round 7 (design M-D, naive: "no pass or fail, hidden mechanism, three names for the preparation"): (1) how the enquiry reaches the accounts is UNVERIFIED and is the studio lead's NOT DECIDED 8 (two options, an AGENT-SCOPE MAY and MUST NOT row text for the second); the owner text promises only that the assistant tells him the way and whether it counts against the 3 calls before it sends; (2) pass and fail are written; (3) the one word is "preparation" for the last checks and "enquiry" for the thing sent; (4) the preparation enquiry is added to E-12 as fact 5. The mechanism for "no paid model call" stays UNVERIFIED (round 6 M4): the real flow calls the model stage and no input shows that an enquiry can pass without a call (AGENT-SCOPE lines 14 to 16 allow only a capped paid call; the assistant's own stand-in model belongs to the stand-in test); whether to allow one paid call is NOT DECIDED 6. The contact and mail are deleted by the owner BEFORE the take because step 4 needs the label and the inbox empty.

### E-12: OWNER-STEPS-realrun-v3.md, line 92, status Apply now, type MISSING STEP
OLD (exact):
~~~~
A yes covers ONE take.
~~~~
NEW (exact):
~~~~
A yes covers ONE take. Before you say yes, the assistant's message must state these five facts, each with the name of the file that shows it, and your yes repeats them in one line each: (1) the stand-in test and the flow rehearsal have been run, and how their checks ended, in numbers (for example "41 pass, 0 missed, 0 not run"; "missed" means the check could not see what it was looking for); (2) the file where their written result is saved; (3) reviewers who are not the assistant (separate review programs, named in their report) have read that result, and the file where their report is saved; (4) the last step of the take program no longer removes any contact from HubSpot: the assistant names the code change (a commit id, which is the name of one saved version of the code), the saved test output that shows it, and the reviewers' report that read both; (5) the one made-up enquiry of the preparation has been sent, and you have deleted its contact and its mail. "Passed" means: every check the plan lists ended "pass"; a check that ended "missed" or "not run", or a finding the reviewers left open, is NOT a pass. The one exception is the crash check: it may end "missed" or "not tested" if the message says so in words, and then you must not post that the take is crash-safe (crash-safe means: the take survives a crash at any moment without a double mail or a lost enquiry). You, the owner, are the one who answers no: answer no if the message leaves out any of the five facts or a file name, or says that anything did not pass. The assistant does not start the take on anything but your written yes, and you may ask it to show any named file on screen.
~~~~
Why: EL-5 and D12: the tests come before any real take; plan line 505 requires independent egm:* reviewers to read the result before any owner-facing claim (design M2: the assistant must not certify its own test to the owner). Round 7 (naive major: nobody was named who answers no; the owner could not check "every check ended pass" without the plan; circular): (a) the owner is named as the one who answers no; (b) the assistant must supply the facts in numbers and with file names, and the owner only repeats them, so he does not judge a technical result; (c) the reviewers are separate programs named in their own report, so the assistant does not certify itself; before the message is sent, the studio lead checks the files exist (rule R6), which does not replace the owner's no. Design M-B: gate G1 is carried in as fact 4 (v3 lines 69 and 95 still say "archived at the end" and today's code deletes, AGENT-SCOPE line 20), so a take cannot start before the code change, its test output and the reviewers' report exist; fact 5 is design m7 (the preparation enquiry of E-11). "Passed" is defined from plan lines 14 and 505 (a MISSED E or E2 is not a pass and limits the claim). This is gating wording that follows EL-5, D12 and plan line 505 but is not literal in them; the studio lead confirms it (FOR THE LEAD TO CONFIRM d). The old text ends with a full stop and the new text starts with the same sentence, so the file's next sentence ("No numbers in the message means answer no.") still follows.

### E-13: OWNER-STEPS-realrun-v3.md, line 99 (and 11), status Hold (gate G3), type DEFERRED
OLD 1 (exact):
~~~~
The lead stops and restarts n8n by hand while person C is posted; you do not touch anything.
~~~~
OLD 2 (exact):
~~~~
C is sent once while the lead stops and restarts n8n by hand.
~~~~
NEW: (no change now)
Why: DEFERRED to a second edit pass after the stand-in test. Plan v5 section 10 says OWNER-STEPS lines 75, 99 and 164 to 166 and AGENT-SCOPE lines 7 to 10 are edited again after the test to match its results; the same "by hand" wording on line 11 goes into that pass. The test kills n8n with a held reply, not "by hand". Both old strings occur exactly once, on lines 99 and 11 (checked by script). Round 7 (naive: not applicable without guessing): MISSING INPUT (exact), no text is written until it exists: the stand-in test result (its INDEX in `evidence-2`) that says how n8n is stopped at the real take (by the assistant by hand, or by the program with a held reply); then the new text is "... the assistant stops and restarts n8n <the method named in that result> while person C is posted; you do not touch anything." Gate G3 is opened by the studio lead (above).

### E-14: OWNER-STEPS-realrun-v3.md, line 107, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
(4) the n8n execution list and execution detail panes: only made-up names and the `take-<id>-a/b/c@example.com` addresses, and not an old execution
~~~~
NEW (exact):
~~~~
(4) the n8n list of saved runs: only made-up names and the `take-<id>-a/b/c@example.com` addresses, and not an old run; do not open or film the detail of the mail step of a run (n8n now keeps its saved runs, and that detail may show the company address and the sender address; the assistant checks in the stand-in test what the mail step shows, with stand-in programs so real addresses may differ, and tells you; you may overrule this in your yes message and say the mail step may be filmed, and then the assistant first reads what the mail step shows)
~~~~
Why: Saved runs ON (EL-2; DECISION-one-store OWNER CONFIRMATION) and step 19: only made-up addresses may be visible. What the saved mail step shows is a guess the stand-in test can check; the text says so. Round 7 (naive minor): the owner is told in the text that he may overrule it (rule R5); "saved runs" is defined in E-01. Same cell covers all of item (4) of line 107, so there is no separate row. The new text ends without a full stop because the file continues with "; (5) ..." (E-15).

### E-15: OWNER-STEPS-realrun-v3.md, line 107, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
(5) the table screen: lead keys only
~~~~
NEW (exact):
~~~~
(5) the count screen (it shows how many rows the table of leads holds, with lead keys only): a test screenshot that the assistant takes in the stand-in test, or the row preview of n8n's table step, labelled "test screenshot" on screen; it is not a live view of the table and not the result of the counting check (the counting check is a small program of ours, not part of n8n, that counts mails, contacts and table rows); pass = only lead keys and made-up addresses are visible, fail = any other text is visible, and then you do not film it
~~~~
Why: D9: the counts proof screen is a stand-in-test screenshot or the Postgres node preview, not a live table screen. DECISION-one-store line 15 (no portal claim in the video) still holds (EL-3, D1). Round 7 (design m5, naive major): the screenshot is labelled as a test screenshot; who takes it (the assistant), when (in the stand-in test), what "count screen" is, and pass and fail are written; "the counting check" is the one phrase for the counts check in E-15, E-18, E-31 and E-36 and its meaning is inside this text. The new text ends without a full stop because the file continues with "; (6) ...". Whether the row preview shows lead keys only is UNVERIFIED (it is the assistant's job to look before the owner films).

### E-16: OWNER-STEPS-realrun-v3.md, line 121, status Apply now, type STALE
OLD (exact):
~~~~
turns "save successful production executions" back off in each workflow, stops n8n, removes the take folder and the Postgres container
~~~~
NEW (exact):
~~~~
turns off the setting that saves successful runs (a setting of the take's own n8n, not of each workflow), stops n8n, removes the take folder and the container of the database server (Postgres) (this is the assistant's job, nothing for you to do; the stand-in test is planned to test only whether removing the container also removes the saved runs; the method at the real take is not decided yet, and you may be asked one yes or no question about it)
~~~~
Why: EL-2: saved runs ON for the take, deleted at clean-up. Plan v5 section 2 and step 1.2 set saving through settings of the take's own n8n. The approved step "turn saving off" stays; container removal is the method of the stand-in test only, because plan line 81 says the real-take method is undecided and line 502 says it is not proven (NOT DECIDED 3; follow-on texts per answer are in E-39). Round 7 (naive minor): the owner is told that part of the open decision is his (NOT DECIDED 3, option b needs his one-line yes). Step 22 item 1 is the assistant's job.

### E-17: OWNER-STEPS-realrun-v3.md, line 131, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
**a lead sent twice with the same id is processed once**
~~~~
NEW (exact):
~~~~
**a lead sent twice with the same id is processed once; a crash at exactly the moment between sending the mail and noting it in the table may send the mail twice**
~~~~
Why: D1, EL-3 (narrow claim) and plan v5 section 10 (row DM in every owner-facing claim). This row changes the POST text on line 131 (what the owner publishes). E-22 changes a different place, the status list on line 166. Rule R1 says when the crash clause may later be deleted from the post, and by whom it is judged.

### E-18: OWNER-STEPS-realrun-v3.md, line 131, status Apply now, type MISSING STEP
OLD (exact):
~~~~
recovery within 60 s; alert within 30 s.
~~~~
NEW (exact):
~~~~
recovery within 60 s; alert within 30 s. It must also NOT say: that a portal, an approval step or an audit trail exists or shows these rows; that n8n cannot reach the internet (its outgoing traffic is meant to be switched off by settings, which is not yet shown to work, and is only watched, not blocked); that the take is crash-safe (a crash at some moments, listed in the plan for the stand-in test, is not tested); that the counting check is independent (the counting check is a small program of ours, not part of n8n, that counts mails, contacts and table rows; it has no read-only database user of its own, because that user is not built).
~~~~
Why: EL-3, EL-4, D1, plan v5 section 0 ("Loopback only is OBSERVED, not ENFORCED") and section 10 (row DM, row NC); DECISION-one-store lines 23 and 28 (read-only count user not built; D3 parks it). Round 7 (naive major, order 6): the forbidden phrase "a different database user" is replaced by the one phrase "the counting check" with its meaning inside the text; "crash-safe" is explained in E-12 (line 92, earlier in the sheet) and "plan row NC" is no longer a code in owner text. The two studio-lead-side conditions for dropping items are in rule R2.

### E-19: OWNER-STEPS-realrun-v3.md, line 159, status Apply now, type STALE
OLD (exact):
~~~~
Independent review rounds 3 to 9 are done. WP6 smoke plan v3 is pending.
~~~~
NEW (exact):
~~~~
Independent reviews of the code (review rounds 3 to 9) are done. The plan for the stand-in test (version 5, text of 2026-11-16) is written and NOT run; no evidence exists for it yet.
~~~~
Why: Plan v5 status line; the sheet still names plan v3. Round 6 (naive M3): the plan file name is removed from owner text, as E-03 removed it; the plan itself never says "rehearsal", so the owner text uses the two names of E-03. The first sentence is in the old text so line 159 and line 3 (E-02) use "review rounds" the same way.

### E-20: OWNER-STEPS-realrun-v3.md, line 162, status Apply now, type STALE
OLD (exact):
~~~~
- A real n8n run, and the Code-node key probe (the WP6 smoke test): not run.
~~~~
NEW (exact):
~~~~
- The stand-in test has NOT been run. It is planned to test, on this laptop only, with stand-in programs and made-up data: (1) real n8n (release number 2.46.6) keeping its data in Postgres (a free database program); (2) whether a program step inside n8n can read the secret key that locks n8n's saved passwords, with a check that the test itself would notice a leak; (3) n8n keeping its saved runs; (4) a watch on whether n8n sends anything out of the laptop. A first smoke test (an earlier trial) did run real n8n on this laptop and left four things open: n8n used a simpler one-file database (SQLite); the key test had no check that it could notice a leak; no request was being handled at the moment n8n was stopped; and the time n8n needed to come back after a restart was measured against the wrong waiting time.
~~~~
Why: Plan v5 section 0 table (open items M2 to M5 and "smoke-1 n8n ran on SQLite") and EL-1. Planned, not proven (naive M8): the text says "planned to test" and "has NOT been run". The first smoke is explained as an earlier trial. Round 7 (naive minor): "2.46.6" is called a release number, and item (2) says in words which secret key and what is tested.

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
the second door (the hook door), and a crash between sending the mail and noting it in the table (the stand-in test is planned to test this once, and once more if the first try missed, which means it could not see what it was looking for; until it has run and passed, it is untested).
~~~~
Why: Plan v5 section 10 row DM and section 9 (crash windows not proven). This row changes the status list on line 166 only; the post text is E-17. After the stand-in test the studio lead updates this sentence to the result (rule R1 evidence). Round 7 (naive minor): "missed" is explained in the text.

### E-23: OWNER-STEPS-realrun-v3.md, line 151, status Apply now, type STALE
OLD (exact):
~~~~
the pinned head is PROVISIONAL and lives in one place: `HEAD_PIN` at the top of the current `wp6\plan-wp6-resmoke-v*.md` (at the time of writing round 3 `take/nlite-int-r3`, round 4 on `take/nlite-int-r4`; source: lead instruction 2026-11-16)
~~~~
NEW (exact):
~~~~
the code under test is named in one place, at the top of the current plan for the stand-in test, and that choice is not final (at the time of writing fix round 3 on `take/nlite-int-r3`, fix round 4 on `take/nlite-int-r4`, fix round 5 being built on `take/nlite-int-r5`; source: the plan's own header notes of 2026-11-16)
~~~~
Why: Plan v5 line 76 (round 5 is `nlite-fix5` on `take/nlite-int-r5`); line 151 itself says "local take branch". The words "all take branches stay on this laptop" are not used: they rest on EL-6, which is in no input file (FOR THE LEAD TO CONFIRM c); plan line 489 says only that the runner never commits, pushes or merges. The old text includes the labels HEAD_PIN and PROVISIONAL, so the owner reads no internal label. "source: lead instruction" is replaced by the plan's header, which the owner can read, so "lead" is not used for two people.

### E-24: OWNER-STEPS-realrun-v3.md, line 178, status Apply now, type STALE
OLD (exact):
~~~~
## UNVERIFIED list (count: 13)
~~~~
NEW (exact):
~~~~
## UNVERIFIED list (count: 17 live items; item 10 was removed, so the numbers run 1 to 18)
~~~~
Why: Four items are added by E-25 (items 15 to 18); 13 live items plus 4 = 17. Item 10 of the file is already marked "(Removed: ...)", so the numbering runs to 18 while the live count is 17 (naive M9).

### E-25: OWNER-STEPS-realrun-v3.md, line 193, status Apply now, type MISSING STEP
OLD (exact):
~~~~
14. Whether Gmail's IMAP shows the label `demo` as a folder named `demo` for the take program.
~~~~
NEW (exact, several lines):
~~~~
14. Whether Gmail's IMAP shows the label `demo` as a folder named `demo` for the take program.
15. That n8n (release number 2.46.6) runs on Postgres (a free database program), with its data kept in its own database apart from the take's database (our table of leads), owned by a database user that is planned to have no other right (the studio lead's instruction of 2026-11-16, not proven; in the first smoke test n8n kept its data in a simpler one-file database).
16. That the saved runs are kept in Postgres and that deleting them at clean-up works at the real take (the stand-in test is planned to delete them by removing the container).
17. That n8n sends nothing out: its outgoing traffic is meant to be switched off by settings (not yet shown to work) and is only watched in samples taken every half second, never blocked; lookups of names cannot be watched.
18. Whether a crash between sending the mail and noting it in the table sends the mail twice (the stand-in test is planned to test it once, and once more if the first try missed, which means it could not see what it was looking for).
~~~~
Why: EL-1, EL-2, EL-4 and plan v5 section 10. The new text is the whole of line 193 followed by four new lines; each line in the fence is its own line of the file, and the file ends after item 18. The count line becomes 17 live items (E-24; checked in round 7 against v3 lines 178 to 193: items 1 to 9 and 11 to 14 are live, 13 items, item 10 is the "(Removed ...)" line). Round 7 (design m4): item 15 no longer cites "decision of 2026-11-16" for the database user with no other right: D3 parks the role split, so the source is the studio lead's instruction (DECISION-one-store CORRECTIONS (a)) and "no other right" is "planned", not proven.

### E-26: AGENT-SCOPE-DO-AND-DONT.md, line 2, status Apply now, type STALE
OLD (exact):
~~~~
DRAFT 2026-11-15 by the lead
~~~~
NEW (exact):
~~~~
DRAFT 2026-11-15 by the lead, edited 2026-11-16 for the owner decision on saved runs, for decision 10 of the lead decisions (one Postgres server) and for the plan for the stand-in test (version 5). In this sheet "stand-in test" means the assistant's test run on this laptop only, with stand-in programs and made-up data, US$0 (the lead decision list also calls it the loopback re-smoke); "flow rehearsal" means the first run of the changed flows on this laptop that follows it (decision 12 of that list)
~~~~
Why: The sheet says "Update whenever a scope changes". Round 6: the two events have one name each (naive M4); "one Postgres server" is lead decision 10, not an owner decision (design m8): only the saved-runs decision is the owner's (DECISION-one-store OWNER CONFIRMATION).

### E-27: AGENT-SCOPE-DO-AND-DONT.md, line 5, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
Identity: n8n test account and its own Postgres table; credentials for HubSpot and SMTP live only in n8n's credential store.
~~~~
NEW (exact):
~~~~
Identity: n8n test account; the take uses one database server (Postgres, in one container) that holds two databases: n8n's own database (workflows, encrypted credentials, saved runs) and the take's database (our table of leads). This is a goal, not yet proven, until the stand-in test has run (in the first smoke n8n kept its data in SQLite, a one-file database); credentials for HubSpot and SMTP live only in n8n's credential store (planned to be kept encrypted in n8n's own database).
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
the encryption key itself is in n8n's environment (and n8n 2.46.6 is expected to copy it into `<take>/n8n/.n8n/config`, a file readable only by its owner (mode 600), that is planned to be removed together with the take folder by a plain `rm` (an ordinary delete, not `shred`); stand-in test step 12.5 is planned to check both) and, once n8n runs on Postgres (planned, proven only by the stand-in test), the password of n8n's database user is a value in `n8n.env`;
~~~~
Why: Plan v5 step 12.5 says the scope sheet must list it; EL-1 puts a database user's password into n8n.env (step 1.2b). Stated as a plan. Who may open that file is NOT DECIDED 1. Round 7 (design m8): the removal by `rm` is "planned" and "expected", not a fact. Why `rm` and not `shred`: the file lies inside the take folder that the assistant removes; the plan gives no further reason, so the reason is UNVERIFIED (see E-48): `shred -u` of step 22 item 6 applies only to the secret files in `~/take-secrets`, which the owner deletes.

### E-31: AGENT-SCOPE-DO-AND-DONT.md, line 20, status Apply now, type MISSING STEP
OLD (exact):
~~~~
`n8n_drive.py:40-41`)
~~~~
NEW (exact):
~~~~
`n8n_drive.py:40-41`; open, finding M-1 of `review-codebase-1.md` (that file is not in `inputs/`, so the finding is taken as the earlier drafts quoted it, UNVERIFIED here): the read uses a table name without its schema name (`app`, a named section inside a database) as one database user while the table is in the schema `app` of the take's database, and the read-only database user of its own for the counting check is not built, so this count is not yet an independent counting check; the stand-in test's grant check (plan v5, the step on database users) is planned to prove the grants only, and the proposal of four database users was parked on 2026-11-16)
~~~~
Why: DECISION-one-store OWNER CONFIRMATION (b), (c) and CORRECTIONS (c) name this finding "M-1"; the same line of AGENT-SCOPE (line 20) cites "F-01" for the contact delete (E-40, E-44). M-1 is the table-name finding and F-01 is the contact delete. "Schema" is explained in the text. "is planned to prove" (design m4). Round 7: "counting check" is the one phrase (E-15, E-18, E-36); `review-codebase-1.md` is not in `inputs/`: NEEDS-LEAD, the studio lead checks M-1 against that file (next step: read it, or drop the quoted words if it differs). The old text is only the closing of the sentence that contains `n8n_drive.py:40-41`; the new text keeps that closing bracket.

### E-32: AGENT-SCOPE-DO-AND-DONT.md, line 23, status Apply now, type STALE
OLD (exact):
~~~~
Real Gmail label behaviour, real HubSpot ids, real n8n Code-node reads of the key and a real n8n run are not exercised (WP6 smoke)
~~~~
NEW (exact):
~~~~
Real Gmail label behaviour, real HubSpot ids and a real model call are not exercised in any smoke yet; a first smoke ran real n8n on this laptop only and left items open, and the stand-in test (plan v5) has not run, so the key reads by n8n Code nodes are not proven
~~~~
Why: Plan v5 sections 0 and 9 (smoke-1 happened; the stand-in test is not run).

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
say "went rogue" (name the missing control). The stand-in test runner (plan v5 section 8) also never commits, pushes or merges, never does a name lookup, a `docker pull` or a new network tool, and never touches the owner's own n8n (ports 5678 and 5679) or any Docker container outside its own start-of-run list.
~~~~
Why: EL-4 and EL-5 (and D6 for the ports); plan v5 section 8 MUST-NOT is stricter than this section (it speaks of the containers in the P-4 baseline). The rule "no commit, push or merge" is plan line 489. EL-6 (take branches stay on this laptop) is in no input; this row follows the plan wording only (FOR THE LEAD TO CONFIRM c).

### E-36: OWNER-STEPS-realrun-v3.md, line 131, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
counts the mails and contacts on its own credentials
~~~~
NEW, TEXT W (default; applied unless confirmation b says otherwise):
~~~~
counts the mails and contacts with a small counting program of ours (not part of n8n)
~~~~
NEW, TEXT N (replaces text W only if confirmation b says the mail count and the contact count run on credentials of their own):
~~~~
counts the mails and contacts on its own credentials, and the table of leads with a small counting program of ours (not part of n8n)
~~~~
Why: D-M1 of round 1: the old words claim an independent login for everything. DECISION-one-store lines 23 and 28: the table count runs as one database user through `docker exec psql`; the read-only count user is not built; plan v5 section 9 says its password is never exercised. A claim in a public post must not outrun that (D1, EL-3). Round 7 (naive major, order 6): the post says "a small counting program of ours (not part of n8n)", which is the public wording of "the counting check" (E-15, E-18); "separate" is dropped because it reads as "independent". Default W (the smaller claim) so that nothing depends on an unanswered question. Whether the counting program really counts the mails and contacts is UNVERIFIED (confirmation b); the owner has no way to verify the post alone, so fact 1 of E-12 (the stand-in test result with counts) is what he relies on, and the assistant says in the yes message which counts the test ran. The post says nothing about "logins".

### E-37: OWNER-STEPS-realrun-v3.md, line 27, status Apply now, type STALE
OLD (exact):
~~~~
## Phase 0: set-up, by Mon 16 Nov 18:29 UTC (23:59 IST); Sun evening is ideal. About 60 to 90 minutes.
~~~~
NEW (exact):
~~~~
## Phase 0: set-up, by Mon 16 Nov 18:29 UTC (23:59 IST); Sun evening is ideal. About 60 to 90 minutes.

Most of Phase 0 is already done (status below). The deadline in the heading above applies only to the steps the assistant names to you, and this sentence wins over the heading. Status on 2026-11-16, from your own statement of that day: the throwaway Gmail mailbox (2-step on, settings done, app passwords saved in files; the assistant asks you where, so that the clean-up deletes them), the HubSpot test account (users created, secret key given), your own n8n account (it holds credentials for HubSpot, the model and Gmail in n8n's own credential store; the take uses a fresh n8n, so these are not the take's) and a saved secret key for the model are DONE. Not yet confirmed: whether that secret key for the model was made for this take only, and what the saved HubSpot secret key is allowed to do. Do not redo a step whose result already exists. That statement does NOT cover the two HubSpot private apps or the property `hadavin_label`, so before the take the assistant confirms with you that the secret key the take uses is the read-only one (step 7, app 1) and that app 2 exists. Do NOT do step 8 until the assistant asks you in a message (the take uses a fresh n8n that the assistant starts; the assistant tells you when and where to type the three credentials into it). The assistant tells you before the take which of steps 1 to 9 still need you. One more thing before any take: the take program as it is today still removes the contacts at its last step (steps 16 and 18 below say "archived", which is that old behaviour), and with the read-only secret key a take would fail after the enquiries were sent and money was spent. So do not say yes to a take, and the assistant does not start one, until the assistant's message names the code change that stops this (see the yes message in step 16). At the take you type `y`, the confirmation number and `end`, plus the take-day items.
~~~~
Why: FACTS-ALREADY-DONE.md names only what the owner did; line 3 says "HubSpot test account, users created, key given" and "Anthropic key saved" and nothing about key scope or about the apps. D7: first-visit n8n setup is done; the owner only types y, the challenge and end. The full rewrite of Phase 0 is OWNER-STEPS v4 (queue item C4b); this row is the fallback note if v3 is read before v4 exists (the only row to apply to v3 then). Round 7: design M-B (gate G1 carried into this note: v3 lines 69 and 95 and steps 16 and 18 still say "archive" until G1 opens, and today's code deletes, so the take would fail after the sends); naive major (which wins, heading or body: the sentence says the body wins; "app passwords saved in files" no longer implies a path that E-48 might contradict: the assistant asks where; the step 8 prohibition is explained in the text, and it still rests on FOR THE LEAD TO CONFIRM e). The new text is the heading line, a blank line and one paragraph, so the paragraph is not a heading.
### E-38: AGENT-SCOPE-DO-AND-DONT.md, line 9, status Apply now, type STALE
OLD (exact):
~~~~
the lead deletes the executions and turns saving off at clean-up
~~~~
NEW (exact):
~~~~
the lead deletes the executions and turns saving off at clean-up (saving is a setting of the take's own n8n, not of each workflow; in the stand-in test the runs are planned to be deleted by removing the Postgres container and the take folder; the method at the real take is not decided yet)
~~~~
Why: Same idea as E-16 on AGENT-SCOPE line 9; plan v5 section 2 and lines 81 and 502 (NOT DECIDED 3). The old text does not overlap the old texts of E-28 and E-29 (all on line 9; checked by script).

### E-39: DECISION-one-store.md, line 23, status Hold (gate G4), type STALE
OLD (exact):
~~~~
delete them and turn saving off at clean-up
~~~~
NEW, NEW if NOT DECIDED 3 is answered (a) turn saving off, delete the runs, then remove the container: NO EDIT (the record already says what is done):
(no text)
NEW, NEW if NOT DECIDED 3 is answered (b) only remove the container (apply only after the owner has said yes to it in one line, because it is not the step the owner approved):
~~~~
delete them at clean-up by removing the container (the owner approved "delete them and turn saving off at clean-up"; method changed on <date and time in UTC and IST that the owner said yes>)
~~~~
NEW, NEW if NOT DECIDED 3 is not answered: NOT APPLIED tonight (default):
(no text)
Why: DECISION-one-store line 23 records an owner approval, so it is not rewritten without the answer to NOT DECIDED 3 (plan lines 81 and 502). Round 6 (naive B2): the text per answer is given; tonight the row is not applied. Follow-on for E-16 and E-38 once answered: (a) their text becomes "... turns off the setting that saves successful runs, deletes the saved runs, stops n8n, removes the take folder and the container ..."; (b) it becomes "... removes the take folder and the container, which also removes the saved runs ...". The lead applies those follow-ons together with this row.

### E-40: AGENT-SCOPE-DO-AND-DONT.md, line 20, status Hold (gate G1), type CONTRADICTION
OLD (exact):
~~~~
at the end ARCHIVE the take's own HubSpot contacts, which the code does as a DELETE call (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, per `review-codebase-1.md` F-01)
~~~~
NEW (exact):
~~~~
at the end LIST the take's own HubSpot contacts by lead key and contact id for the owner, who deletes them by hand in HubSpot after the take (the take never deletes contacts); CODE-CHANGE-NEEDED: today's code still removes them with a delete call (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, per `review-codebase-1.md` F-01), and whether the code already prints that list is UNVERIFIED
~~~~
Why: D2: the take never deletes contacts; leftovers are listed by lead key and contact id and the owner deletes them by hand. GATE G1 (round 6, naive m3): the row describes target behaviour, so it is held until the code change is made and tested, like E-04 and E-05. F-01 is the contact-delete finding (E-31 uses M-1 for the table-name finding).

### E-41: OWNER-STEPS-realrun-v3.md, line 103, status Hold (gate G1), type CONTRADICTION (code-change gate)
OLD (exact):
~~~~
NEEDS-OWNER. When the script says "Film the contact list now: type `end` and press Enter to archive", the lead films the contact list first. Type `end` and Enter yourself only when the lead says so. The script then archives this take's contacts. Only the exact word `end` ends the pause: a bare Enter or any other line makes the script print "type exactly: end" and ask once more; the second wrong line also prints "type exactly: end" and then the script goes ahead and archives anyway; a closed input on the first prompt ends the pause at once. Ctrl-C or closing the window also still archives.
~~~~
NEW (exact):
~~~~
NEEDS-OWNER. When the script pauses so that the assistant can film the contact list (the assistant tells you the exact words that appear on screen once the code is changed), the assistant films the contact list first. Type `end` and Enter yourself only when the assistant says so. The script then ends the take; it removes no contact (you delete this take's contacts by hand afterwards, see the next line). Only the exact word `end` ends the pause: a bare Enter or any other line makes the script print "type exactly: end" and ask once more; the second wrong line also prints "type exactly: end" and then the script goes ahead and ends the take anyway; a closed input on the first prompt ends the pause at once. Ctrl-C or closing the window also ends the take and removes no contact.
~~~~
Why: D2: the word "archive" (a delete call in today's code) leaves this line. GATE G1: the pause prompt and the behaviour on a second wrong line, Ctrl-C and a closed input are today's code with "archive" in them, so the new text is true only after the code change, and the program's prompt wording after the change is UNVERIFIED (hence "the assistant tells you the exact words"). The old text is one whole line (103); no quoted prompt is invented. Missing input (exact), why the row is held: the line `CODE-GATE G1 OPEN: <commit id>, <evidence file name>` and the evidence file's quote of the changed pause prompt; when both exist, put the quoted prompt in place of the words in the first bracket.

### E-42: OWNER-STEPS-realrun-v3.md, line 104, status Hold (gate G1), type CONTRADICTION (code-change gate)
OLD (exact):
~~~~
- STOP and tell the lead: closing the window or Ctrl-C early still archives, but tell the lead; leftover contacts are deleted by you in the HubSpot UI, the lead gives the count.
~~~~
NEW (exact):
~~~~
- STOP and tell the assistant: closing the window or Ctrl-C early also ends the take and removes no contact, but tell the assistant; you delete this take's contacts by hand in the HubSpot UI, and the assistant gives you the count and, if the program printed them, the list (lead key and contact id).
~~~~
Why: D2: the owner deletes the contacts by hand, from a list by lead key and contact id (the old line gave only the count). GATE G1 as in E-41; after Ctrl-C or a closed window the list exists only "if the program printed it" (UNVERIFIED). Missing input (exact), why the row is held: the line `CODE-GATE G1 OPEN: <commit id>, <evidence file name>`, and the evidence file's statement whether the program prints the list on Ctrl-C.

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
NEW (exact):
~~~~
NOTE (F-01, CODE-CHANGE-NEEDED, not fixed here): decision D2 of 2026-11-16 settles it: app 1 stays read-only (OWNER-STEPS:69) and the take never deletes contacts, so the program's delete at the end must be removed (or turned into a list for the owner); until that code change is made and tested, a take would pass the pre-take GET probe and fail at the delete after the sends, so no paid take starts before it. Leftover contacts are deleted by the owner by hand.
~~~~
Why: D2 closes the question "app 1 scope or an archive path" that the note leaves open. GATE G1 (round 6, naive m3): held with E-40 because it speaks of the code change as pending; whether the program already prints the list is UNVERIFIED.

### E-45: AGENT-SCOPE-DO-AND-DONT.md, line 23, status Hold (gate G1), type STALE
OLD (exact):
~~~~
(archive, result.json, final print)
~~~~
NEW (exact):
~~~~
(the end-of-take step, result.json, final print; today's code runs the contact delete in this step, which D2 removes)
~~~~
Why: D2: the word "archive" (a delete call) leaves the sheet. GATE G1 (naive m3). The rest of that sentence (exit 3 behaviour) may change with the code and is UNVERIFIED after the change.

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
3. You: delete BOTH HubSpot private apps (Settings, Integrations, Private Apps, Delete). Screenshot; crop it so that it shows no secret key text, no account name and no address. Then the assistant asks you: "Did you make the secret key for the model only for this take, and does nothing else use it?" If you answer yes, revoke that secret key in the website of the model provider (the assistant tells you the exact place before the clean-up; that click path is not checked) and screenshot the key list showing it gone, cropped the same way. If you answer no or you are not sure, do NOT revoke it and tell the assistant, who writes down that it stays. The screenshot is only a record: no check in item 5 tests the secret key for the model. The assistant's copy of that secret key is planned to be deleted together with the take folder in item 1, which is not a revoke. If you saved your own copy of it in `~/take-secrets`, delete it in item 6 with the two other secret files, the same way; if you saved it anywhere else, delete that file the same way after the revoke.
~~~~
Why: DECISIONS-2026-11-16.md item 5, part S9-3 (the decision file numbers its items 1 to 12; the studio lead's own short name for the part is D5 S9-3): the owner revokes the model key at clean-up, owner-only; FACTS-ALREADY-DONE.md lists the clean-up revoke as owner-only. Step 22 names only app passwords and HubSpot apps. Round 7 (design M-C, order 3): the row ALWAYS applies; the former condition on NOT DECIDED 7a silently dropped S9-3 when the answer was "not sure". The safe default is in the text: the assistant asks at clean-up, the owner revokes only after a clear yes, and S9-3 stays the rule. If ND7a is answered "yes, made only for this take" the question can be dropped and the text says "revoke". The place to revoke is UNVERIFIED (not read), so the assistant names it before clean-up; step numbers are named in the text (item 1, item 5, item 6 of step 22). The assistant's copy lies in the take folder that item 1 removes first (AGENT-SCOPE line 13: the key file sits in the take folder by procedure), so the owner deletes only his own copy by the method item 6 already gives (`shred -u`, else `rm`). If v4 is written, use this row there.

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
