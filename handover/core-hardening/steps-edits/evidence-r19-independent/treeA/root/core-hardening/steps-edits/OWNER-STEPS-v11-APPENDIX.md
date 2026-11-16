# Appendix to the owner's day sheet, version 11

Written Mon 16 Nov 2026. Times are UTC and IST (IST = UTC + 5:30). This file holds what the day sheet (`OWNER-STEPS-realrun-v11.md`) points to. Nothing here changes a rule of the day sheet. Sections: 1 More words, 2 The run card, 3 How the studio lead's messages fit, 4 Rule 10 in full, 5 Send counts, masked form, sample printed result, 6 Order table, 7 What to send, 8 J. What the post must NOT say, 9 Exit codes and other refusals, 10 n8n stop and start lines, 11 Step T (trial run), 12 Step G (failed run or after a trial), 13 Retire check results, 14 For the studio lead (what is not proven). There is no section about copying a connection value: that procedure of version 10 is gone; if n8n asks for a value, stop (day sheet C.3).

## 1. More words (the ones not needed until a step uses them)

- **Run settings file**: the small file with the settings of one run (run name, Gmail label to read, worst-case price per call). The studio lead prepares it and sends its path. You never edit it.
- **Model settings file** (`stage.env`): the file with the settings of the model program: backstop, price figures, model name, most model tokens per call and stop time. You never edit it and never open it with `cat`; in step A you print only the named lines with `grep`.
- **Run folder**: the WSL folder that holds the run's files; the studio lead sends the exact `cd` line, whose form is `cd <folder from run card row 8>`; if it differs from row 8, stop.
- **Company address**: your Hadavin company address; it may appear as the "From" line of the mail; you do nothing with it. **Gmail filter**: a rule in the receiver's settings that puts the incoming demo mails under the label `demo`; the studio lead makes both (row 17).
- **App password**: a password Google makes for one program. **Scope names**: the permission names HubSpot lists on a private app's page. (Step 0 calls the HubSpot key a "token" in a setting name only.)
- **Marker file**: `~/.hadavin-take-tags/<run name>.used`; it makes a run name unusable twice. You never delete or edit it.
- **Run lock file**: `take-<run name>.lock` beside the run folder; it stops a second run with the SAME run name. Removing it: section 9.
- **Retire check**: a program command that tries to log in with the keys you revoked and must be refused (I.4, section 13).
- **n8n's saved runs**: the records n8n keeps each time it handled a test person; they hold only test addresses and perhaps the company address; the studio lead removes them in I.5.
- **Database container**: the sealed box on this laptop that runs the database program (Postgres) for the run; the studio lead removes it. You do not start or stop Docker. **Database passwords**: made by the studio lead, who disposes of them. **Postgres preview**: the picture of the database's rows shown inside n8n; only the rehearsal's, never a live one.
- **Masked result file**: the file the program writes in the run folder; the studio lead reads only this masked file. Three different files: the **step 0 result file** (`~/hadavin-step0-result.txt`), the **rehearsal result file** (named by the studio lead in step A) and the masked result file of the real run. They are always called by these names. The words "printed result" mean only what the program prints on your screen after `end`.
- **Crash-safe**: if the program stops after sending a mail and before noting it down, no second mail goes out when it starts again. NOT shown yet; nothing may claim it until the studio lead states in writing a result on the real n8n that shows it (step J).
- **Separate login**: a second login that only counts mails and contacts. Not built; nothing may say a "separate check" or "separate login" exists. The program's own count is "the program's count".
- **Browser profile**: a Chrome user profile (the round picture top right), never a Gmail menu.
- **Portal** (only in the ban list): a customer web page where people approve actions. Nothing to do with the HubSpot account number.
- Three lists, three names: the **run card** (section 2), the **order table** (section 6) and the **result list** (the PASS/FAIL/SKIPPED lines step 0 prints). "Table" means nothing else; the database's own table is "the database".

## 2. The run card (17 rows; no card, no run)

A go message is valid only with all 17 rows filled. A card with a row missing is not complete: do what the right-hand column says and ask for a new card. A row changes only by a new complete card, never by a chat line, and never during clean-up. A row 15 or 16 "kept on purpose" counts only with your written yes (reason and end date in UTC and IST).

| Row | The card holds | If missing |
|---|---|---|
| 1 | run date; how many days before it you start steps B to D | ask |
| 2 | run name pattern; the studio lead confirms your word | ask |
| 3 | latest start time (UTC and IST); how long a run normally takes | ask |
| 4 | who films, who starts the recording, who edits (and crops), who says "filmed" | no run |
| 5 | who stops and restarts n8n while person C is sent; the exact words of the program's line that tells them to stop, and the one that tells them to start (section 10) | no run |
| 6 | trial run: yes or no (paid; its own yes) | no trial |
| 7 | deadlines (UTC and IST) for watching the video (H), clean-up (I), cancelling the model key (I.0) and the latest post time | ask |
| 8 | paths: run folder, run settings file, model settings file, the names of its setting lines, secret folder and names, which secret files are n8n connection files and which is the model key file | ask |
| 9 | the address where you sign in to n8n (step C.3), with the port the run's n8n uses | do not open n8n |
| 10 | proof-screen candidates (pictures of counts only) | no proof screen |
| 11 | who checks the post text | do not post |
| 12 | minutes to wait with no new line before you tell the studio lead; the longest film pause in minutes | tell the studio lead and wait |
| 13 | I.3 (cropped screenshots): yes or no | skip I.3, ask |
| 14 | for step 0 and E: folder of `scripts/hubspot_probe.py`; checksums of every file used and of `scripts/run_real_check_n8n.py` (a checksum is a short code proving a file is the right copy); the commit id; the secret file path of the HubSpot key; the exact HubSpot permission names; the number of calls `--plan` prints; the one HubSpot host | no step 0 |
| 15 | HubSpot key and each app password: deleted or revoked in clean-up, or kept on purpose (written reason and end date) | delete nothing |
| 16 | model key: cancelled by you in I.0 (default), or kept with reason and end date | I.0 as default |
| 17 | yes or no for each: the receiver's label `demo` and its Gmail filter; the separate sender Gmail account | no start; ask |

## 3. How the studio lead's messages fit

The studio lead may send only values: a date, a path, a number, a list of names, or a command line in exactly the form printed in the sheet. A message never changes rules 1 to 12, steps A, E, F and I, the money rule, the go conditions, the boxed warnings, or the rule that you never erase the marker file. You never let anyone type `y` for you, you give no paid-run yes without numbers, and you never use another account or erase secret files before the retire check. If a message asks for any of that, answer no. (This does not claim that nothing can start before your typed answers: the studio lead may already have started the model program and the n8n flows.) A command line not in a printed form is not run.
The studio lead works in the same Linux login as you, so the laptop itself would let it read your files. It promises not to: it reads only masked outputs (the lines you send and the masked result file) and never your secret files. That is its own working rule, not something the laptop enforces; this is why you make and cancel the model key yourself.

## 4. Rule 10 in full

A path or name may hold only: A-Z a-z 0-9 . _ / - and a full path starts with `/home/`. A setting name matches only A-Z 0-9 and `_` and contains none of KEY, TOKEN, SECRET, PASSWORD. Do not type, and tell the studio lead about, a value that holds: a space, a quote (single or double), `;`, `$`, a backtick, `|`, `&`, `<`, `>`, `(`, `)`, `*`, `?`, `~`, `\`, `..`, a leading `-`, a line break. (Exception inside the sheet's own printed lines: the sheet's lines hold quotes, `$`, `<`, `>` and `|` where they are printed; only the VALUES you receive are held to the list.) Before `shred` or `rm` on each path: `ls -l "<path>"` and `readlink -f "<path>"`: any `->`, or a `readlink` line different from the path you typed, means stop. Also `ls -ld "<secret folder>"`: stop if it shows `->`. Never erase a file that row 15 or 16 keeps on purpose.

## 5. Send counts, masked form, sample printed result

**Send counts.** Person A is sent in twice, B ten times at once, C once while n8n is stopped and started again: 13 sends, all made by the program. Each test person should be treated once. At the end you should see one contact and one mail for A and for B. For C: one contact and one mail, or, if the program reports C as "unknown", possibly no mail and an alert mail (a mail the system sends to an address the studio lead names on the card; not tested). A contact for C may or may not exist; the studio lead tells you which and where the alert mail goes. So you should see 2 or 3 contacts; another count: tell the studio lead. A and B must come out right; C may be "unknown", and then the exit code may be 0 or 3; go condition 7 says which counts as success. The program does not check the alert mail itself. After the run the contacts stay in HubSpot until you delete them by hand (F.3), unless the studio lead's go condition 5 statement says otherwise.
**Masked form.** First 2 letters, three dots, the last letter before the `@`, then the domain. Invented example: the address `demoreceiver@example.net` reads `de…r@example.net`.
**Sample printed result (INVENTED: the real wording and layout are not known; compare meaning, not layout).**
```
  Person A: 1 contact, 1 mail      Person B: 1 contact, 1 mail
  Person C: unknown (could not tell whether it got a contact and a mail)
  Model calls made: 3              Sends made: 13
  Exit code will be: 3 (a count or verdict failed)
```
Meaning: A and B are right (this is what J needs); C "unknown" gives exit code 3, which counts as success only if the studio lead said so in writing (go condition 7). A line saying A or B has 0 or 2 contacts or mails: not right; rule 12.

## 6. Order table: every owner step (who, what, where, expected)

(The first column is a plain number so it cannot be confused with the lettered steps.)

| No. | Who | What is typed or clicked | Where | Expected |
|---|---|---|---|---|
| 1 | studio lead | sends the run card | message | 17 rows |
| 2 | studio lead | clean start: fresh made-up person ids; empties the database table of the rehearsal; says so | its own session | "clean start done" (owner does nothing) |
| 3 | owner | picks a run name and one screen from row 10 | message | studio lead confirms |
| 4 | studio lead | "go step 0" quoting your written yes, and the HubSpot test account name | message | no go, no step 0 |
| 5 | owner | step 0.1 to 0.6 | browser, WSL, message | list of PASS/FAIL/SKIPPED lines; answer |
| 6 | studio lead | rehearsal; names the rehearsal result file; removes any model credential in n8n; statements for go conditions 4 and 5 | message | in writing before A.6 |
| 7 | owner | A.0 key list review; new run key saved; key name and path sent | model account, WSL, message | studio lead restarts the model program, sends time and process number |
| 8 | owner | A.1 to A.6: settings, price, money, rehearsal, accounts, the yes | WSL, browser, message | acknowledged |
| 9 | owner | B laptop; C.1 to C.3; D look only | Windows, Gmail, Chrome, n8n | "label and inbox empty"; "profile ready" |
| 10 | studio lead | `go trial run` or `go real run <run name>` with all go conditions | message | no go, no start |
| 11 | owner | E.0 money rule again, settings, checksum; E.1 start; E.2 notice; E.3 `y`; E.4 line; "run started" | WSL, message | the run starts |
| 12 | person on row 5 | the stop and start lines (section 10) in a second window, on the program's own cue | named on the card | n8n down once, back while C is sent |
| 13 | person on row 4 | films the contact list | named on the card | contact list filmed |
| 14 | owner | F.1 `end`; F.2 `echo $?`, usage page, send code and figures; F.3 delete listed contacts | WSL, browser, HubSpot | code 0 or see section 9; "contacts deleted" |
| 15 | studio lead | stops the model program; "model program stopped"; "no more runs" | message | messages |
| 16 | owner | I.0 cancels the named keys; "model key cancelled" | model account | key gone |
| 17 | owner | H watches the edited video twice; "accepted" or bad seconds | player | reply |
| 18 | owner and studio lead | I.1 to I.7 | Google, HubSpot, WSL, Windows | see the day sheet |
| 19 | owner | J posts; "posted" | LinkedIn or as told | someone else checked the text |
| 20 | owner | trial run (section 11) or failed-run clean-up (section 12) | WSL, Gmail, HubSpot | messages sent |

## 7. What to send the studio lead (never a secret)

| When | Send |
|---|---|
| Before a run | the run name and the proof screen you chose; your written yes for step 0; "HubSpot is the test account"; step 0 PASS/FAIL/SKIPPED lines and the exit code, or the filter counts; the new model key's name and path (A.0) and your decision on older keys (no values); your written yes with numbers; the money figures you read; "receiver, sender and HubSpot are the throwaway accounts" |
| Run day | "label and inbox empty"; "profile ready"; any problem line |
| During a run | "run started"; "closed the terminal early" if it happens |
| End of a run | exit code, last printed line, balance and money used before and after; "contacts deleted" and the number |
| After a run | "model key cancelled" and the usage figure; "accepted" or the bad seconds; "an address is visible" |
| After a failed or trial run | "demo mails deleted" and the number of contacts; a new yes and run name |
| Clean-up | names of app passwords or private apps left alone; names of private apps deleted; retire-check words and code; "secret files erased" |
| Posting | the post text; then "posted" |

## 8. J. What the post must NOT say

- that nothing can start or spend before the owner's typed answers (the model program and the n8n flows are started earlier with a live key; no closed gate exists);
- that the same person through two doors is one contact;
- that no contact data stays in n8n, that recovery takes within 60 seconds, or that an alert comes within 30 seconds;
- that a portal, an approval step or an audit trail exists or shows these rows, or anything suggesting a person approves each action;
- that n8n cannot reach the internet (its outgoing traffic is switched off by settings and only watched, not blocked);
- that the run is crash-safe, or that no mail is sent twice after a crash between sending the mail and noting it (lifts only when the studio lead states in writing a result on the real n8n that shows it, and names it; a passing rehearsal does not lift it);
- that the count is made by a "separate check" or "separate login";
- that everything is in one database (the aim is one Postgres server with two databases, n8n's own and the run's; not proven until the rehearsal shows it; some files stay outside it);
- that the spend is capped by a hard limit (it is a setting a person checks);
- that test data was "deleted permanently" or "erased" (HubSpot may keep an archived copy, Gmail's deleted mail may stay for a time), or that the program deletes or does not delete the contacts unless the studio lead's go condition 5 statement and the printed result both show it;
- that a lead sent twice is processed once with no mention of the lease: the allowed claim is only "a lead sent twice with the same id inside the lease is processed once";
- anything about which permissions any part has or does not have (for example "only reads", "least privilege", "each part has only what it needs").

## 9. Exit codes and other refusals

Exit codes of the program (step E): 0 success. 1 your answer was not `y`, or the confirmation line did not match. 2 the program refused to start or go on: a setting, a failed login check, no keyboard, closed input, an answer typed too fast, a run name or key used before, a lock file exists, the stop time too close, a second mailbox, Ctrl-C before the first send. 3 a count or verdict failed after the run, or Ctrl-C after the sends began. Rare: if the program is cut off at the very end the number can be 3, 120 or another, and the run lock file can stay behind; do not run again; the studio lead reads the masked result file. Any number other than 0: rule 12. Exit codes of the retire check differ: 0 both logins refused (good); 3 a login still works; 2 anything else ("could not tell").

> **WARNING before removing the run lock file. It cannot be undone and the lock protects against a second run with the same run name. Remove only the one file the studio lead names by its full path, only after it says so.**

- **Run lock file:** if the program stops hard it may leave `take-<run name>.lock` beside the run folder; the next run with that run name is refused. Remove it ONLY when the studio lead says so: `ls -l "<full path>"`, `readlink -f "<full path>"` (must equal the path), compare with the message and rule 10, then `rm -- "<full path>"`. The name must be exactly `take-<run name>.lock`, no `*` or `?`.
- **Start deadline:** the program needs about 14 minutes before the stop time; at the default setting the latest start is before Mon 23 Nov 2026 18:14:40 UTC = 23:44:40 IST; row 3 gives the exact time.

## 10. n8n stop and start lines (permitted forms; the studio lead supplies only the values)

The person on row 5 types only these forms, in the second window, and only after the program's own line tells them to. **UNVERIFIED: no source file gives the real commands (the earlier sheet says only "n8n killed once by hand"); the studio lead must replace these forms with the real ones and check them in the rehearsal before the card is sent.**
- Look first: `ps -o pid=,args= -p <n8n process number>` must show the run's n8n (the port on row 9), not your own everyday n8n on port 5678 or 5679. Any doubt: do not stop it.
- Stop: `kill <n8n process number>` (digits only, from the card).
- Start again: `<start line>` exactly as printed on the card; it must begin with `cd "<run folder>"` and hold only characters allowed by rule 10 and no `;` or `|`.
Do not type anything else in that window, and nothing from it in the run window.

## 11. Step T. Trial run (only if row 6 says yes; it comes last on purpose)

A trial run is a real, paid run: its own written "yes step T" message from you quoting why you want it (owner decision 8 of 2026-11-16 replaced extra real-account checks, so a trial is a studio lead addition that needs your yes), its own "go trial run <run name>", its own step A (new yes, new run name, A.0 to A.6, money rule redone), the boxed warnings of E and F. Differences: nothing is filmed or posted; at F.1 you look at the contact list yourself (no film) and then type `end`; afterwards step G. The trial's money counts as "used so far" in the next A reading. The model key is not cancelled after a trial (no "no more runs") unless you decide so in the money rule's key-list review. Afterwards the real run needs a new yes, a new run name and a fresh C.1.

## 12. Step G. Failed run or after a trial

> **WARNING before step G. Delete ONLY demo mails in the receiver account and ONLY HubSpot contacts of the failed or trial run (the studio lead gives the count and run name). Before each delete check the account shown. If the Trash holds anything other than these demo mails, do NOT empty it; tell the studio lead. Never erase the marker file.**

The studio lead says why. (1) In the receiver Gmail open the label `demo` and the Inbox; tick only the demo mails one by one (subject starts with `[demo] lead`, where "lead" is a made-up sales contact); never "Select all conversations"; Trash icon; open Trash: only those mails, else stop; then "Empty Trash now". Gmail's Archive button is never used. (2) In HubSpot delete leftover contacts as in F.3, only as many as the studio lead counted, and only those it lists by person id and contact id. (3) Send "demo mails deleted" and the number of contacts. (4) Give a new written yes and a new run name. A run that got past both typed answers has used its name, even if it failed. If C was "unknown", the studio lead says whether a contact or an alert mail may remain and where the alert mail goes; until then delete only what it counted. If a new run is no longer possible before the stop time, none happens.

## 13. Retire check results (I.4)

| It prints (code) | Row 15 says | You do |
|---|---|---|
| both "refused as expected" (0) | any | send "retire check succeeded" |
| mailbox "STILL WORKS" (3) | app password revoked | revoke again (I.1), run again |
| mailbox "STILL WORKS" (3) | kept on purpose | expected; counts as succeeded only if HubSpot is "refused as expected"; the studio lead says "retire check succeeded, mailbox app password kept on purpose" |
| HubSpot "STILL WORKS" (3) | key deleted | delete the private app again (I.2), run again |
| HubSpot "STILL WORKS" (3) | kept on purpose | counts only if the mailbox is "refused as expected"; the studio lead says "retire check succeeded, HubSpot key kept on purpose" |
| both kept on purpose | both | the studio lead writes "retire check not required: kept on purpose" and the end date (UTC and IST); I.6 covers only the files it lists |
| "could not tell" (2) | any | wait for the studio lead |

If the check cannot succeed (code 2 twice, a row missing, or the studio lead cannot say what counts): keep every secret file, remove nothing more, tell the studio lead; it writes down what is left and the date to finish.

## 14. For the studio lead (not an owner step; the owner can ignore it): what is not proven yet

- Nothing in the day sheet or this appendix was run by the writer: no command, no click path, no program. All new commands (`ls -l --time-style=full-iso`, `ps -o lstart=`, `read -rs`, `set -C`, `wc -c`, `python3 -I -c`, `cut`) are standard Linux/WSL but UNVERIFIED on this laptop.
- The rehearsal is written and has NOT been run. The code has never run against a live Gmail, HubSpot or model call. The only live check before the run is the loopback re-smoke ("real run minus one node": the HubSpot contact step replaced by a stand-in) plus one made-up lead; the HubSpot step itself is covered only by step 0 and the run. Evidence must never be called "real run passed".
- The code under test is a provisional head; row 14 gives the commit id. The run branch's files are local only (never pushed), so the owner cannot compare the commit with a public page; the checksums prove only equality with what the studio lead says.
- Not built yet (audit note on environment access in the flows): the flows read `$env.DESK_*` and `$env.MF_*` inside nodes while the start script blocks environment access in nodes; the real run needs a literal substitution into a local copy of the flows at run time.
- Not shown: that nothing can spend before both typed answers. The model program and the n8n flows are started before `y`. A closed gate in the program (design item "gate before the model call") is described, not built; the fallback "the studio lead switches on the flows after the owner's typed `y`" is not accepted (owner decision 5 of 2026-11-16). The real limits are the balance and the model key; the sheet now says so openly in four places.
- Not shown: that the program prints the masked sender and receiver on the notice (deferred).
- Not shown, and contradicted by the scope sheet: that the program at the row 14 commit does not delete or archive contacts (scope sheet: the code archives at the end by a DELETE call, `run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, finding F-01). Owner decision 2 says the program never deletes. Go condition 5 is now a hard stop before E and needs your written statement of what you checked; if the program still deletes at `end`, steps F, G, the film, the post ban and F.3 need rewriting and the program needs a code change.
- Not shown: that the program ends the film pause with the word `end`, and that typed-ahead keys, a wrong line or a closed terminal end it early (assumed). Not shown: what closing the terminal at the delete line does (F.1 safe exit).
- Not shown: that the program prints a line that tells row 5 when to stop and start n8n, and what its words are; section 10's command forms are guesses.
- Not shown: that the program runs under `python3 -I` (isolated mode may not add the script's folder to the import path); the rehearsal must use exactly the printed command form.
- Not shown: that the model program's start time and key file can be checked by the owner as written (go condition 6) and that its process loads the key file the owner made; the owner can see only file and start times.
- The program does not print the backstop or the money spent so far. Which counter the backstop uses (account total or the run's own) is not known to the writer: the step A message must state it. The notice text "B ten times at once" is a fixed string, not taken from a setting. The program does not check: the alert mail, mail in any folder other than `demo`, the contact id read back from HubSpot (only checked to be all digits), the manual n8n stop and restart.
- Not checked: HubSpot scope names, HubSpot search by run name, HubSpot behaviour on deleting a missing contact, Windows Snipping Tool and clipboard behaviour, Google, HubSpot and model-account click paths (including that the model account shows a new key once and has a copy button), the usage page's delay and its per-model line, Gmail's label timing for mail sent from another Gmail account, whether Gmail accepts the company address as the shown sender, whether the model program accepts the key file form.
- Not shown: that one Postgres server holds two databases and that removing saved runs works; that a crash between sending the mail and noting it sends no second mail.
- Where records are kept: one Postgres server is the aim; some files stay outside it (the model program's log written before each model call, a spending record, lock files, the run-name marker file).
- The video is the real-run scenes 1 to 4 only; the stand-in scenes and their unmeasured caption number are not in it.
- Lease claim: "a lead sent twice with the same id inside the lease is processed once"; what happens after the lease ends is not claimed. Spend limit: stays by the owner's own eye (money rule) plus the model program's stage checks; no hard cap is claimed.
