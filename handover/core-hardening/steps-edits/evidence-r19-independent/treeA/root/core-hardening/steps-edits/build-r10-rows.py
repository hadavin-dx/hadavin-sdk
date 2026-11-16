# Round 10 row blocks (whole-row replacements). Imported by build-r10.py.
ROWS = {}

ROWS['E-09'] = '''### E-09: OWNER-STEPS-realrun-v3.md, line 78, status Apply now, type UNCLEAR WORD
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

'''

ROWS['E-11'] = '''### E-11: OWNER-STEPS-realrun-v3.md, line 87, status Apply now, type CONTRADICTION
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

'''

ROWS['E-12'] = '''### E-12: OWNER-STEPS-realrun-v3.md, line 92, status Apply now, type MISSING STEP
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
Why: EL-5 and D12: the tests come before any real take; plan line 505 requires independent egm:* reviewers to read the result before any owner-facing claim. Round 7: the owner is the one who answers no. Round 8: fact 5 (the preparation enquiry) is E-50 (held). Round 9: fact 4 says "no delete call" and names the evidence (Q23: not settled); the crash-check exception is the ONLY exception; N1 and N2; "missed" and "not run" defined; no offer to show a secret file; the yes carries the sentence that the assistant shares the owner's Linux user, clipboard and screen (Q24). Round 10: (a) design M2: the old text now includes the second yes example of line 92 ("You answer in one line, for example: ... window ends 2026-11-23 23:59 IST."), so that sentence is REPLACED by this row; it had no UTC time, no files and no "no delete call" fact, and an owner could have copied it into a yes that contradicts this row (NOT DECIDED 13 no longer needs the studio lead to delete it by hand); (b) naive M2: the assistant's message is "the request for your yes" and the owner's answer is "your reply" (the old words "yes message" meant both); (c) naive M3: the reply is ONE line to copy, with every placeholder explained, the closing sentence marked REQUIRED, a slot for the crash check (`tested` or `untested`) and the latest start time as a slot; (d) naive M3, naive M5, design m4: the last day (23 Nov) and the latest start time for the planned day (Wed 18 Nov) are stated in UTC and IST; the 18:14 UTC = 23:44 IST start that the program accepts leaves too little time before the last time to revoke (18:19 UTC = 23:49 IST, Q25), so for 23 Nov the assistant asks for no start later than 18:04 UTC = 23:34 IST (18:19 minus about 14 minutes 20 seconds, the program's own 860 seconds); that is the builder's reading, to be confirmed (FOR THE STUDIO LEAD TO CONFIRM h); Q25 also says no take on 23 Nov unless the studio lead's reading of the final code (Q27) is shown; (e) G1: the request cannot be sent until the line `CODE-GATE G1 OPEN: ...` exists and the rows of gate G1 (E-04, E-05, E-41, E-42) are applied, so steps 17 and 18 no longer say "archived" when fact 4 is read (rule R6 checks both). This is gating wording that follows EL-5, D12 and plan lines 14 and 505 but is not literal in them; the studio lead confirms it (FOR THE STUDIO LEAD TO CONFIRM d). The old text starts after E-51's old text (`... against a second file)` then `; and the planned window end **...**.`) and ends with "A yes covers ONE take."; the file's next sentence ("No numbers in the message means answer no.") still follows; E-50 anchors on it.

'''

ROWS['E-13'] = '''### E-13: OWNER-STEPS-realrun-v3.md, line 99 (and 11), status Hold (gate G3), type DEFERRED
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

'''

ROWS['E-14'] = '''### E-14: OWNER-STEPS-realrun-v3.md, line 107, status Apply now, type UNCLEAR WORD
OLD (exact):
~~~~
(4) the n8n execution list and execution detail panes: only made-up names and the `take-<id>-a/b/c@example.com` addresses, and not an old execution
~~~~
NEW (exact):
~~~~
(4) the n8n list of saved runs (the past runs that n8n keeps): only made-up names and the `take-<id>-a/b/c@example.com` mail addresses, and no run from before this take. By default do not open or film the detail of the mail step of a run: it may show the company mail address and the sender mail address. You decide what is filmed (rule 5: you post). If you want the detail of the mail step filmed, say so in your written reply to the request for your yes (step 16); the assistant then first tells you what the mail step shows in the stand-in test (a test with stand-in programs, so the real mail addresses may differ), and you film it only if you accept that. In every case, footage in which a real mail address is visible is not used
~~~~
Why: Saved runs ON (EL-2; DECISION-one-store OWNER CONFIRMATION) and step 19: only made-up mail addresses may be visible. What the saved mail step shows is a guess that the stand-in test can check. Round 7: the owner may overrule the default (rule R5). Round 8: an overruling yes does not let a real address be filmed. Round 9: nested brackets split; "saved runs" defined in E-52. Round 10 (naive minor, design M2 style): the two instructions "do not film" and "you may say it may be filmed" read as a contradiction; the new text has one default ("by default do not film the detail"), says who decides (the owner, as rule 5 already says), and says how the owner overrules (his written reply); "address" is "mail address" (E-52). The new text ends without a full stop because the file continues with "; (5) ..." (E-15).

'''

ROWS['E-16'] = '''### E-16: OWNER-STEPS-realrun-v3.md, line 121, status Apply now, type STALE
OLD (exact):
~~~~
deletes all saved executions of the take (made-up data only, owner decision 2026-11-16), turns "save successful production executions" back off in each workflow, stops n8n, removes the take folder and the Postgres container
~~~~
NEW (exact):
~~~~
deletes all saved runs of the take (made-up data only, owner decision 2026-11-16), turns off the setting that saves successful runs (a setting of the take's own n8n, not of each workflow), stops n8n, removes the take folder and the container of the database server. Before it removes anything, it copies the take's result file and its counts (names and numbers only, no secret) into a folder of its own, because removing the container also deletes n8n's database and the take's table of enquiries. It removes only the container that it started for the take: the assistant tells you that container's name, which is on the list of containers it recorded when the run began, and it touches no other container. The assistant does all of this and there is nothing for you to do. It reports each part as done or not done, and tells you before you start your own steps (items 2 to 6) if a part is not done. The stand-in test is planned to test only whether removing the container also removes the saved runs. The method at the real take is not decided yet, and you may be asked one yes or no question about it: whether the saved runs may be deleted only by removing the container. You answer `Yes, remove the container only` or `No`; no answer counts as No
~~~~
Why: EL-2: saved runs ON for the take, deleted at clean-up. Plan v5 section 2 and step 1.2 set saving through settings of the take's own n8n. The approved step "turn saving off" stays; container removal is the method of the stand-in test only, because plan line 81 says the real-take method is undecided and line 502 says it is not proven (NOT DECIDED 3; follow-on texts per answer are in E-39). Round 8: the clean-up has a pass and a fail for the owner (each part reported done or not done). Round 9: "executions" becomes "saved runs". Round 10 (naive M6, naive M3-style): (a) removing the container destroys both n8n's database and the take's table, so the assistant first copies the result file and the counts out (names and numbers only; the plan's evidence folder is the studio lead's choice, UNVERIFIED which); (b) the container is identified: only the one the assistant started for the take, named to the owner, from the list recorded at the start of the run (the same rule as AGENT-SCOPE E-34); (c) "before you sign off" (no such step exists in the sheet) becomes "before you start your own steps (items 2 to 6)"; (d) the yes or no question has an exact reply (`Yes, remove the container only` or `No`; silence is No), the same as in NOT DECIDED 3. The old text ends before the file's full stop, so the new text also has none. Step 22 item 1 is the assistant's job. The file's own words before the old text ("1. The lead: deletes the 3 credentials in n8n,") are not touched by any row; whether "3" must say four is FOR THE STUDIO LEAD TO CONFIRM g.

'''

ROWS['E-39'] = '''### E-39: DECISION-one-store.md, line 23, status Hold (gate G4), type STALE
OLD (exact):
~~~~
delete them and turn saving off at clean-up
~~~~
NEW [HOLD G4: DO NOT APPLY], NEW if NOT DECIDED 3 is answered (b) only remove the container (apply only after the owner has said yes to it in one line, because it is not the step the owner approved) (exact):
~~~~
delete them at clean-up by removing the container (the owner approved "delete them and turn saving off at clean-up"; method changed on <date and time in UTC and IST that the owner said yes>)
~~~~
Why: DECISION-one-store line 23 records an owner approval, so it is not rewritten without the answer to NOT DECIDED 3 (plan lines 81 and 502). Round 6 (naive B2): the text per answer is given. Round 10 (naive M7): ONE version of the follow-on texts replaces the round-6 and round-9 versions, which disagreed, and the invented words "deletes the 3 credentials in n8n" are gone (no decision backs a new credential delete; the file's own words "1. The lead: deletes the 3 credentials in n8n," come before E-16's old text and stay). Per answer: answer (a), turn saving off, delete the runs, then remove the container: nothing changes in this file (it already says "delete them and turn saving off at clean-up"), and E-16 and E-38 keep their texts. Answer (b), remove the container only: this row's text replaces the old text, and the studio lead changes E-16's new text so that the part "deletes all saved runs of the take (made-up data only, owner decision 2026-11-16), turns off the setting that saves successful runs (a setting of the take's own n8n, not of each workflow), stops n8n, removes the take folder and the container of the database server" reads "stops n8n, removes the take folder and the container of the database server, which also removes the saved runs"; the rest of E-16's text is unchanged, and the sentence about the one yes or no question is deleted because it has been answered. E-38's bracket then says "the lead removes the container, which also removes the executions" in place of "the lead deletes the executions and turns saving off". The studio lead applies those follow-ons together with this row. Held: the NEW text is not applied until NOT DECIDED 3 is answered.

'''

ROWS['E-48'] = '''### E-48: OWNER-STEPS-realrun-v3.md, line 123, status Apply now (safe default text), type MISSING STEP
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

'''

ROWS['E-55'] = '''### E-55: OWNER-STEPS-realrun-v3.md, line 119, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
### Step 22. Retirement, by Mon 23 Nov 18:29 UTC (23:59 IST)
~~~~
NEW (exact):
~~~~
### Step 22. Retirement. The secret key for the model is revoked by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke); the rest of the retirement is done by 18:29 UTC = 23:59 IST (the end of the spending window). The take is planned for Wed 18 Nov 2026, so retirement normally follows the take on the same day.
~~~~
Why: Design M1 of round 9: the heading of step 22 said "by Mon 23 Nov 18:29 UTC (23:59 IST)" for the whole retirement while E-48 puts the model-key revoke inside step 22 with the last time to revoke 18:19 UTC = 23:49 IST (Q25: at least 10 minutes before the stop). The two deadlines are now on the heading: model-key revoke 18:19 UTC = 23:49 IST, rest 18:29 UTC = 23:59 IST (all arithmetic checked: 18:19 + 5:30 = 23:49; 18:29 + 5:30 = 23:59; Mon 23 Nov 2026 is a Monday). "Wed 18 Nov, same day" is Q21.1 (target Wed 18 Nov, not fixed; the owner cancels the run key right after the take, same day). The old text is the whole heading line 119 and occurs once; it overlaps no other row.

'''

ROWS['E-56'] = '''### E-56: AGENT-SCOPE-DO-AND-DONT.md, line 20, status Apply now, type CONTRADICTION
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

'''
