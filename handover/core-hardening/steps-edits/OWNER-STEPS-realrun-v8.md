# Your steps for the recording run of the lead desk video (version 8)

Written Mon 16 Nov 2026.

**Box: the safe default.** If you are unsure about anything in this sheet, a number, a file name, an account or a word: type nothing and tell the studio lead. Typing nothing sends nothing, spends nothing and deletes nothing. Step 0, the trial run and the real run each need their own message from the studio lead that says "go"; your general go-ahead "once everything is ready" does not start any of them.

**How this sheet and the studio lead's messages fit together.** The studio lead may send you only values: a date, a path, a number, a list of file names, or a command line in exactly the form printed in this sheet. A message from the studio lead never changes rules 1 to 9, the boxed warnings above steps 0, E, F, G and I, or the rule that you never delete the marker file. A command line that is not in exactly the form printed in this sheet is not run: say so and wait. If a message asks for something that breaks one of these, do not do it; say so and wait.

This sheet lists only what ONLY YOU can do, and says who does everything else. You do NOT create accounts, mailboxes, keys or the HubSpot account, and you do not start or stop Docker (the tool that runs the database program in a sealed box on this laptop): all of that is already done or is the studio lead's job. The one exception is step C.3, if run card row 9 says so. Already done and not repeated: the two throwaway Gmail accounts and their app passwords, the HubSpot test account and its keys, your n8n account, the model key and its credits, the n8n workflows on the public code site, and your general go-ahead "once everything is ready". If one of these turns out to be missing or broken when a step needs it, tell the studio lead; do not rebuild it yourself.

## Words box (read once; every word keeps one meaning)

- **The studio lead**: the Claude session that works with you. It is software. It runs its own commands on the laptop from its own session. It never sees your screen, never types in your terminal and never types your answers. Every value it needs you to know arrives as a message from it or as a named file. Where a step says "the studio lead tells you", a message is coming; if none has come, do nothing and ask. In this sheet "lead" alone means the studio lead, except in the video's name "lead desk" (a product name), in the program's screens, in the table line "lead-status write" and in the mail subject `[demo] lead <person id>`; there it means a made-up sales contact, never the studio lead.
- **The recording run** (also "the run"): the one run you film, on your throwaway accounts, with 3 made-up people. A **trial run** is a practice run on your throwaway accounts, with real HubSpot writes, real mails and real paid model calls; it is a paid run and needs its own written yes (step A) and its own run name; the run card (row 6) says whether one happens (default: none). A **rehearsal** is the studio lead's own practice on this laptop with stand-in programs, made-up data, no live account, no key and no model call; the studio lead does it and you do nothing.
- **Test person**: one made-up person. The run makes three: A, B and C. Each has a **test address**: `take-<run name>-a@example.com`, `-b@` and `-c@`. They are made up. (The word `take` in file and address names just means "this run".) Each test person also gets a **person id**: the letter L and some letters and digits. Do not confuse it with an account id (the number HubSpot or n8n shows for your account; step D). The program's screens call it "lead key" or "lead id". It shows in the mail subject `[demo] lead <person id>`.
- **Contact**: one HubSpot record of a test person.
- **Send counts**: person A is sent in twice, B ten times at once, C once while n8n is stopped and started again: 13 sends in. The system should treat each person once. What you should see at the end: one contact and one mail for A; one contact and one mail for B; for C one contact and one mail, or (if the program reports C as "unknown") possibly no mail and an alert (this has not been tested). If C is "unknown", a contact for C may or may not exist; the studio lead tells you which and where the alert mail goes. So you should see 2 or 3 contacts in total; if the count is different, tell the studio lead. A and B must come out right; C may come out "unknown". The program does not check the alert mail itself.
- **Run name**: a short word you invent for each run and never use again. The program's screens call it "take id". You choose it BEFORE step A and send it to the studio lead (it is a word, not a secret). You also type it at the confirmation line in step E. The run card says which pattern is accepted and the studio lead confirms your word.
- **Run settings file**: the small file with the settings of one run (run name, Gmail label to read, worst-case price per call). The studio lead prepares it and tells you its path. You never edit it. The start command points at it.
- **Model settings file** (`stage.env`): the file with the settings of the model program: the spending backstop, the price figures and the stop time. The studio lead tells you its path. You never edit it. You open it to read only if run card row 8 says it holds settings and no key (see step A); otherwise the studio lead copies the lines you need into a message.
- **Spending backstop**: the highest total in US dollars written in the model settings file. A person (you) checks it by eye. It is not a promise the program makes. **It must be no higher than the total in your written yes** (3 times the worst-case price per call); a backstop above that total is a reason to answer no. The model account itself holds more credit than that total (the studio lead's notes say US$189 usable until Mon 23 Nov 2026 23:59 IST), and that rest stays usable by anything that holds the model key; this is why the model key is cancelled after the last run (step I.5b). The real values are in the message of step A.
- **Run folder**: the folder in WSL that holds the run's files. The studio lead sends you the exact `cd` line to type. The form is `cd <folder from run card row 8>`; if the folder differs from run card row 8, stop.
- **The studio lead's commands run as the same Linux user as yours** (the studio lead's session runs on this laptop under your Linux login). This is why you never put a secret in a message and why step I.5b cancels the model key.
- **n8n's saved runs**: the records n8n keeps of each time it handled a test person. In this run they hold only test addresses and perhaps the company address (in the mail step); the studio lead removes them in step I.5.
- **Database container**: the sealed box on this laptop that runs the database program (Postgres) for the run. The studio lead removes it in step I.5.
- **Rehearsal values**: the run name and settings the studio lead puts into the run settings file before the rehearsal and the run.
- **WSL**: the Ubuntu terminal inside Windows. To open it: Windows Start menu, type `Ubuntu`, press Enter (path not checked). The prompt ends with `$`. `~` means your Linux home folder.
- **Stop time**: the time after which the run may not spend money or start. The program's screens call it "window end". Planned: Mon 23 Nov 2026, 18:29 UTC = 23:59 IST (the studio lead confirms it). The program refuses a start that is too close (it needs about 14 minutes). At the default setting the latest start is before 18:14:40 UTC = 23:44:40 IST; the run card (row 3) gives the exact time.
- **Secret files**: files in your WSL home folder that hold the app passwords and keys for this run. You made them. The run card (row 8) gives their names and the folder. Printed form of a secret file path: `<secret folder from row 8>/<file name from row 8>`, always the full path starting with `/home/`. A path that does not start with the secret folder of row 8, or whose last name is not one of the names in row 8, is not a secret file of this run: stop.
- **Key**: a secret (a password, an app password, a token). It never means an id or an address. **App password**: a password Google makes for one program. **Private app (HubSpot)**: a named access setup in the HubSpot test account; each has a key. (The HubSpot check in step 0 calls its key a "token"; it is the HubSpot key.)
- **n8n**: the tool that takes the test people in, writes the HubSpot contact and sends the mail. **The program**: the checking program you start in WSL (`scripts/run_real_check_n8n.py`). **The model program**: a small program of ours that asks the AI model once per test person.
- **Receiver**: the throwaway Gmail account that only receives the demo mails. **Sender**: the throwaway Gmail account n8n sends from. **Company address**: your Hadavin company address; it may appear as the "From" line of the mail. You do nothing with it in this sheet. **Label `demo`**: a Gmail label in the receiver; the program reads only this label.
- **The notice**: the screen of numbers the program prints before it asks you to type `y`. The notice also shows the sender and the receiver as masked text (first 2 letters, then the domain), if the program prints them; step E says what you do if it does not. A **notification** is something else: a pop-up from Windows, Gmail or Chrome.
- **Proof screen**: the one screen the video shows to prove the counts. You choose it in step E from the screens the run card (row 10) offers. It may show test addresses and counts only.
- **Marker file**: `~/.hadavin-take-tags/<run name>.used`. It makes a run name unusable twice. You never delete or edit it.
- **Run lock file**: a file named `take-<run name>.lock` beside the run folder. It stops a second run with the SAME run name; a new run name is not stopped by it. Deleting it is boxed in "Other refusals".
- **Retire check**: a program command that tries to log in with the keys you cancelled and must be refused (step I.4). It tests only 2 of the run's secrets (the mailbox login and the HubSpot login), not the model key or the database passwords. The model key is cancelled by you in step I.5b.
- **Exit code**: a number the program leaves behind when it ends. To see it, type `echo $?` and Enter in the same terminal right after the program ends, before any other command. 0 means the program says it succeeded. For step 0, exit 0 does NOT mean delete works (step 0 item 7).
- **Delete**: remove it from the place you work in (HubSpot contacts, HubSpot private apps, secret files, demo mails: first Trash, then empty Trash). Deleting cannot be undone by you. HubSpot may keep a recoverable "archived" copy for some time (step 0 shows whether its delete is "permanent" or "archived"). The program's screens say "archive" for the contact deletion; it means delete. If a screen says something else, stop and tell the studio lead. **Gmail's Archive button**: this sheet never uses it. **Revoke**: cancel an app password so it stops working (the Google button is named "Remove"). This sheet uses no other word for these acts.
- **Crash-safe**: after a crash between sending the mail and noting it in the table, no second mail goes out. It is NOT shown and stays unclaimed until a result on the real program shows it; the rehearsal uses stand-in programs and does not lift it (step J).
- **Separate login**: a second login that only counts mails and contacts. It is not built and not shown to run; nothing in this sheet or the post may say a "separate check" or "separate login" exists (step J). The program's own count of mails and contacts is simply "the program's count".
- **Browser profile**: a Chrome user profile (the round picture top right), never a Gmail menu.
- **Stop and wait**: type nothing more, close nothing, tell the studio lead what you see, and wait for the answer.

## The run card (the studio lead sends it BEFORE step A; no card, no run)

The run card is one message from the studio lead. Check that every row is filled. If a row is missing, do what the right-hand column says for that row. The right-hand column is not the same for every row: read each one.

| Row | What the card holds | If the row is missing |
|---|---|---|
| 1 | run date and the number of days before it when you start steps B to D | do nothing and ask |
| 2 | run name pattern; the studio lead confirms your word is accepted | do nothing and ask |
| 3 | exact latest start time (UTC and IST) and how long a run normally takes | do nothing and ask |
| 4 | who films, who starts the recording, who edits, who tells you the contact list is filmed | no run starts |
| 5 | who stops and restarts n8n while person C is sent (the person's name, and the exact line if you are that person) | you type nothing in n8n or WSL during the run; ask |
| 6 | trial run on the live accounts: yes or no (a trial run is paid and needs its own yes) | no trial run |
| 7 | deadlines for watching the edited video (H) and for clean-up (I) | do nothing and ask |
| 8 | paths: run settings file, model settings file, secret file folder and names | do nothing and ask |
| 9 | whether you must sign in to n8n (step C.3) and, if so, which address | do not open n8n |
| 10 | the proof-screen candidates | no proof screen is filmed |
| 11 | who checks the post text against the must-not-say list | do not post |
| 12 | how long to wait with no new line before you tell the studio lead | tell the studio lead and wait; do not press Ctrl-C |
| 13 | which of the steps C.1, C.2, C.3, D, T, G, I.2, I.3 and I.7 the studio lead confirms are wanted | skip those steps and ask |
| 14 | for step 0 and E: the folder with `scripts/hubspot_probe.py`; the checksum (a short code that proves a file is the right copy) of every file the check uses, and of `scripts/run_real_check_n8n.py`; the commit id of the code; the full path of the secret file that holds the HubSpot key (inside the secret folder of row 8, with a name from row 8); the exact HubSpot key permissions (scope names) it needs; the number of calls that `--plan` prints (including a fallback delete, if there is one) | do not do step 0 |
| 15 | the HubSpot key: revoked in step I.2, or kept on purpose (then with a written reason and an end date; without an end date it is revoked by the stop time), and for each app password: revoked in step I.1 or kept on purpose with reason and end date; the answer if the studio lead names the same app password or HubSpot private app for another use | do not delete any HubSpot private app and do not revoke any app password |
| 16 | the model key: cancelled by you in step I.5b (default), or kept with a written reason and an end date | step I.5b is done as the default (you cancel it) |

**A card row changes only by a new complete run card message from the studio lead, never by a chat line in the middle of a step, and never during clean-up (step I).** If a row is missing or unclear in clean-up, do the step's "if it cannot pass" action; do not guess.

## Table of every owner step (who does what, where, what to expect)

"Who" is you (the owner), or the studio lead. Where the person is named on the run card, the row says which card row.

| Step | Who | What is typed or clicked | Where | Expected screen or result |
|---|---|---|---|---|
| Run card | studio lead | sends the run card message | message | all 16 rows filled |
| Run name | owner | picks a new word; types it in a message | message | studio lead confirms it is accepted |
| 0.0 go | studio lead | sends a message that says "go step 0" | message | no go, no step 0 |
| 0.1 checksums | owner | `cd` line from the studio lead, then `sha256sum` on each file named on run card row 14 | WSL | same codes as row 14; if different, stop |
| 0.2 plan | owner | `python3 -I scripts/hubspot_probe.py --plan` | WSL, same folder | "planned calls: <N>" with N as on row 14; calls nothing |
| 0.3 delete check | owner | `export HUBSPOT_PROBE_TOKEN="$(cat <full path from run card row 14>)"`, then `python3 -I scripts/hubspot_probe.py --yes-spend-calls <N>`, then at once `echo $?`, then `unset HUBSPOT_PROBE_TOKEN` | WSL, same folder | a PASS/FAIL table, then one number; you read the table, then paste the table and the number (never a key) to the studio lead; exit 0 alone does not mean delete works |
| 0.4 answer | studio lead | reads the table; sends one of three answers: "delete works", "delete not shown", "unknown"; if a line looks like a key, the owner sends only "a key-like text is in the table" | message | one line |
| Rehearsal values | studio lead | puts the run name and values in the run settings file | run folder | path sent to you |
| Rehearsal gate | studio lead | runs the rehearsal; names its result file | message | file named; no pass, no run (the studio lead's own gate) |
| A written yes | owner (the studio lead first sends the numbers; a trial run needs its own yes) | types the one-line answer, for example "Yes, run <run name>, up to 3 model calls and up to US$<total>, stop time 2026-11-23 23:59 IST" | message | studio lead confirms it received your yes |
| B laptop settings | owner | plug in; Settings, sleep Never; Power Options, lid = Do nothing | Windows | settings show after reopening |
| C.1 receiver check (only if run card row 13 lists it) | owner | open the label `demo` and the Inbox; types "label and inbox empty" | receiver Gmail, message | both empty |
| C.2 browser profile (only if row 13 lists it) | owner | create or check the profile `demo-take`; sign in to the HubSpot test account and the receiver; types "profile ready" | Chrome, message | profile ready |
| C.3 n8n sign-in | owner, only if run card row 9 says so (and row 13 lists C.3) | sign in with your existing n8n account; if a screen asks for a connection value again, copies it from WSL as step C.3 says; types "done" | `demo-take` profile, message | n8n opens |
| D film check (only if row 13 lists it) | owner | look only; no clicks that open mails | `demo-take` profile, terminals | only test addresses visible and no account id |
| E.0 throwaway accounts | owner | compares the masked sender and receiver in the notice or in the studio lead's step A message with your own two throwaway accounts, then types "receiver and sender are the throwaway accounts" (no address) | message to the studio lead | studio lead replies |
| E.1 start | owner | types the start command the studio lead sent, Enter | WSL, run folder | two login lines, then the notice |
| E.2 compare | owner | reads the notice and compares it with your written yes and the lead's message (rules in step E); types nothing if anything differs | WSL | numbers match |
| E.3 `y` | owner | types `y`, Enter | WSL | the confirmation prompt |
| E.4 confirmation | owner | types `<6-digit number> <run name>`, Enter | WSL | the run starts |
| Run: n8n stop and restart | the person named on run card row 5 | the exact line on the card | named on the card | n8n goes down once and comes back while C is sent |
| Run: proof screen | owner | picks one of the offered screens; types which one | message | studio lead says what it shows |
| Run: filming | the person named on run card row 4 | films | named on the card | contact list filmed |
| E.5 finish | owner | after the program prints its result and `$` returns: `echo $?`; sends the number and the last printed line | WSL, message | number 0, or see the exit-code list |
| After the run: model program | studio lead | stops the model program right after the run's last printed line; says "model program stopped" | its own session | message |
| F `end` | owner | types `end`, Enter, only after the film person says "filmed" | WSL | HubSpot shows no contacts of this run; the program prints its result |
| T trial run done (only if run card row 6 says yes) | owner | the trial is a paid run with its own yes and run name, steps E and F, then step G's clean-up; then the real run gets a new yes and a new run name | WSL, receiver Gmail, HubSpot, message | trial result sent, demo mails and contacts deleted |
| G failed run or finished trial (only if row 13 lists it) | owner (with the studio lead's counts) | deletes demo mails and leftover contacts; types "demo mails deleted" and the number of contacts; gives a new yes and a new run name | receiver Gmail, HubSpot, message | messages sent |
| H watch | owner | watches the edited video twice; types "accepted" or the bad seconds | video player, message | reply sent |
| I.1 revoke | owner | removes each app password the studio lead lists (and no other); takes a screenshot of each list | myaccount.google.com | named passwords gone |
| I.2 private apps | owner, only after run card row 15 and the studio lead's list | deletes the listed HubSpot private apps; takes a screenshot; types the app names | HubSpot settings, message | apps gone |
| I.3 screenshots | owner | crops and saves them with the names the studio lead gives | Windows folder | files saved |
| I.4 retire check | owner types; studio lead gives the line | `python3 scripts/run_real_check_n8n.py --retire-check <run settings file>`, then `echo $?`; sends the output words and the number | WSL, message | "refused as expected" twice, number 0 (or the case in I.4) |
| I.5 n8n and container removal | studio lead | removes n8n connections and saved runs, stops n8n, removes run folder and database container | its own session | message "removed" |
| I.5b model key | owner (default, run card row 16) | cancels the model key in the model account (path not checked) after the studio lead says the model program is stopped and the retire check succeeded; types "model key cancelled" | model account console, message | key gone |
| I.5 database passwords | studio lead | tells you in a message what happens to them | message | you do nothing until told |
| I.6 secret files | owner | `ls -l <full paths>`, compare with run card row 8, then `shred -u -- <full paths>` (or `rm --`), then `ls -l <secret folder>`; types "secret files removed" | WSL, message | files gone |
| I.7 laptop settings back | owner | sets sleep and lid back; signs out of `demo-take` | Windows, Chrome | done |
| J post | owner | posts the final words; types "posted" | LinkedIn or as the studio lead says; message | someone else checked the text first |

## Order of the day

1. Run card arrives; you choose the run name and send it.
2. Step 0: the HubSpot delete check (once, before step A; again only if the studio lead asks; it needs the studio lead's "go step 0").
   2b. If run card row 6 says yes: the trial run (step T) comes before the real run, with its own yes and run name.
3. A: the studio lead sends the numbers; you answer with a written yes.
4. B, C, D on the run day (run card row 1 says how long before the start).
5. E: you start the run and type `y` and the confirmation line.
6. F: the film pause; you type `end` only when filming of the contact list is done.
7. After the run: the studio lead stops the model program; G (only if the run failed or after a trial run), H (watch the edited video), I (clean-up), J (post).

**Dates.** The studio lead gives the run date; until then do nothing. The studio lead's aim is to have the video posted by Wed 18 Nov 2026. If the run date on the card is later than that, the card's date counts and the posting moves later; the studio lead tells you. Fixed times: stop time Mon 23 Nov 2026, 18:29 UTC = 23:59 IST (it limits only the start and the spending of the run; the model credit ends then). Earlier plan: watch the video (H) and finish the clean-up (I) by Mon 23 Nov 2026, 18:29 UTC = 23:59 IST; run card row 7 may set earlier deadlines. The latest time to post is Wed 25 Nov 2026, 15:00 UTC = 20:30 IST.

## What the run can cost

- The run makes at most 3 paid model calls: at most one per test person. The model program writes each call down before it is made. A call that went out and then failed is not tried again; that test person stays "unknown".
- The worst-case price per call: **the studio lead gives you the number before you say yes.** The total is 3 times that number. Your written yes names that total. A trial run costs the same again and needs its own yes.
- The program does NOT enforce a dollar ceiling as a promise. The spending backstop and the stop time sit in the model settings file and a person checks them. Your checks are in step E: the numbers on the notice must equal the numbers in your yes, and the backstop must be no higher than the total in your yes and equal to the backstop in the studio lead's message. If a number differs, answer no.
- A failed run still costs what it spent. Every new run needs its own yes (step A), with the money spent so far shown.
- The model account holds more credit than your yes (see "Spending backstop"). Until the model key is cancelled, anything that holds that key could use the rest. So the studio lead stops the model program right after the run, and you cancel the model key after the last run (step I.5b).
- Step 0 makes no model call (the model costs US$0). It makes the HubSpot calls named on run card row 14 (the studio lead expects 7) to the HubSpot test account.

## Rules that hold in every step

1. **Never send the studio lead** a password, key, mailbox address or the contents of any secret file. Short sentences only. A file path or file name is fine.
2. **The typed answers are yours alone:** the `y`, the 6-digit number with the run name, and `end`. The 6-digit number only blocks blind answers and answers fed in by another program. A tool that reads the screen and types the number back still passes. So never let a tool, script, assistant, agent or helper window type for you. Run the program only on your laptop, in your own terminal.
3. **Before every paid run you give a written yes WITH numbers** (step A). Your earlier go-ahead "once everything is ready" is a general go-ahead; it is not that yes. No numbers, no run.
4. **You post. Claude never posts.**
5. **The run uses only the throwaway receiver and sender, never your real company mailbox.** Before step E you send the studio lead the sentence in the table row E.0. If you are not sure, say so and do not start.
6. On run days: laptop on mains power, sleep Never, lid close = Do nothing (step B). Set both back after the last run (step I.7).
7. **Words you type that delete things** are in a boxed line right above the step. Read the box first.
8. If a screen differs from a click path in this sheet, stop and tell the studio lead what you see. Click paths marked "(path not checked)" were not checked on your accounts.
9. **Before you type any command that prints a file (`cat`) or paste anything to the studio lead:** nobody films or shares your screen at that moment, and no recording is running. If a printed line is a long string of letters and digits that looks like a key, do not paste it and do not copy it; send only "a key-like text is on the screen" and close the terminal window.

## Before the run

> **WARNING before step 0. Step 0 is a live write to your HubSpot test account: it creates ONE made-up contact (an address at `example.com`), changes two fields on it, reads it back and tries to delete it. The HubSpot key is put into your terminal for the length of the check. It makes no model call and spends no money. It needs its own message from the studio lead that says "go step 0"; your general go-ahead (the intro) does not cover it. If you are unsure about any file name, folder, number or screen: type nothing and tell the studio lead. Typing nothing changes nothing.**

### Step 0. HubSpot delete check (you, once, before step A; no model call)
Why: the program deletes this run's HubSpot contacts at the end (step F), and it is not yet known whether the HubSpot key the program uses is allowed to delete. This check answers it. It makes the calls counted by `--plan` (the studio lead expects 7: check a property, read the owners, create ONE made-up contact, change the owner on it, change its lead status, read it back, delete it) to your HubSpot test account, and no model call. The studio lead has not shown that the copy of the script it read is the current one; that is why you compare checksums (item 1). If the delete fails, the check should warn you and you delete that one contact by hand in HubSpot, so it is never on film.

The key needs permission to create and to delete contacts. Run card row 14 names the exact permissions (scope names); use only a key that has exactly those and no others. A key that cannot create or delete is a permission problem in your HubSpot private app, not a limit of the HubSpot plan; the studio lead tells you what to change. (Whether one key may hold both the counting rights and the delete right is the studio lead's decision, recorded on the card; until then the run counts a read-only key as unable to delete and you delete leftover contacts by hand.)
The run card (row 14) gives: the folder that holds `scripts/hubspot_probe.py`, the checksums, the commit id, the number N of planned calls, and the full path of the secret file that holds the key. The printed form of that path is `<secret folder from run card row 8>/<file name from row 8>`. If the path does not start with that folder, or the file name is not one of the names in row 8, stop.
1. In WSL type the `cd` line the studio lead sent. Then type `sha256sum` followed by each file named on run card row 14 and Enter. Compare each code with the card. If any differs, stop (see "If you stop" below).
2. Type `python3 -I scripts/hubspot_probe.py --plan` and Enter. You should see a line "planned calls: N" with N as on run card row 14. It calls nothing. Any other number: stop. If `python3` is not found, stop and tell the studio lead; do not try `python`. (The studio lead expects N = 7. If the script counts a fallback delete, N may be 8; then the card says 8. You always type the number the card gives, never a number of your own.)
3. Type `export HUBSPOT_PROBE_TOKEN="$(cat <the full path from run card row 14>)"` and Enter. A plain `cat <name>` does not work from the scripts folder. Nothing is shown (the key stays out of the screen). Never type the key itself, and never write it in chat or in this sheet. If you see "No such file", stop. If the screen prints a long string, close the terminal window (rule 9).
4. Type `python3 -I scripts/hubspot_probe.py --yes-spend-calls N` and Enter, with the number N from the card; it must equal the number from item 2. The words "spend calls" are the script's own name for "make these calls"; they do not mean model money.
5. At once, before any other command, type `echo $?` and Enter, and note the number. Then type `unset HUBSPOT_PROBE_TOKEN` and Enter.
6. Read the table. You should see PASS, FAIL or SKIPPED lines, for example "owners readable", "contact create", "owner write", "lead-status write", the read-back, "delete" and, if the script has it, "read back after delete" (the table may have fewer or more lines than calls; one line is not one call). **The number from item 5 being 0 does NOT mean delete works.** 0 only means no line says FAIL; SKIPPED lines also give 0. Before you copy anything: if any text looks like a key (a long string, for example one that starts `pat-`), do not paste anything; tell the studio lead only "a key-like text is in the table". Otherwise select the table text and paste it, with the number, to the studio lead.
7. The studio lead answers with one of three words:
   - **"delete works"**: the "delete" line says PASS (permanent) or PASS (normal delete: archived, not permanent; HubSpot then keeps an archived copy) AND a line shows the contact is gone or archived when read again after the delete. Only this answer means the program's deletion at step F should work. The studio lead also tells you which delete route the check used and whether it is the same call the program uses at step F; if the studio lead cannot say, the answer is "unknown".
   - **"delete not shown"**: the "delete" line says FAIL or SKIPPED, or the create line failed or was SKIPPED (so the delete was never tried), or there is no read after the delete. Exit 0 does not change this. The program's deletion at step F should then fail after the sends, and leftover contacts would have to be deleted by hand. **Do not give the written yes (step A) until the studio lead tells you in writing what happens next.**
   - **"unknown"**: the table is incomplete or does not match the script. Do nothing and wait.
   - If the "delete" line says "NOT NEEDED (nothing was created)", the number from item 5 is 1 even though no line says FAIL. Read it as "delete not shown" (the create did not work): paste the table as usual and wait for the studio lead's answer.
   A different line failing (for example "lead-status write") may be a permission problem of the key or a limit of the HubSpot plan; the studio lead tells you which and whether it matters.
- **If you stop for any reason in step 0** (the number is not N, a checksum differs, "No such file", the script prints "refused", the table warns that a contact may still exist, a key-like text shows, a path is not in the form above): type `unset HUBSPOT_PROBE_TOKEN` and Enter, close the terminal window, then tell the studio lead what you saw. Delete a leftover contact by hand in HubSpot only after the studio lead names it.

### Step A. The written yes with numbers (you, once per paid run)
The studio lead sends one message with:
- at most 3 model calls in this run;
- the worst-case cost per call, and 3 times that figure;
- the money spent so far;
- the spending backstop (which must be no higher than that total) and the stop time as they stand in the model settings file (`stage.env`), copied into the message by the studio lead, with the file's path. You may open that file in WSL to compare only if run card row 8 says it holds settings and no key. Printed form: `cat <path from run card row 8>`; the path must equal the row 8 path. Before you type it, follow rule 9. If a long string shows, stop (rule 9);
- the sender and the receiver accounts, masked (first 2 letters, then the domain), for you to compare with your own two throwaway accounts;
- the planned stop time 2026-11-23 18:29 UTC = 23:59 IST;
- that the rehearsal passed, with the name of its result file (no rehearsal pass, no run).

You answer in one line, for example: "Yes, run <run name>, up to 3 model calls and up to US$<the total in the message>, stop time 2026-11-23 23:59 IST." One yes covers ONE run, and a trial run is a run. A message with no numbers: answer no. Do not give this yes until step 0's answer is "delete works", or the studio lead has told you in writing what happens next.
You should see: the studio lead confirms it received your yes.

### Step B. Run-day laptop settings (you)
1. Plug the laptop into mains power.
2. Windows 11: Start, Settings, System, Power & battery, Screen, sleep & hibernate timeouts. For "plugged in", set "put my device to sleep after" to Never (path not checked).
3. Control Panel, Hardware and Sound, Power Options, "Choose what closing the lid does". For "When I close the lid", plugged in: Do nothing. Save changes (path not checked).
4. Close programs that show addresses or notifications.
5. After the last run set both back (step I.7).
You should see the new settings after you reopen each screen. If your screens differ, tell the studio lead what you see.

### Step C. Run day, before the studio lead says go (you)
1. **Receiver mailbox** (only if run card row 13 lists C.1). Open the receiver account in Gmail. In the left list click the label `demo` (if hidden, click "More") (path not checked). It must hold no mail. Click Inbox; it must be empty too. Tell the studio lead: "label and inbox empty". (The sheet needs no contact count from C.1.) If the label holds mail, or you cannot find the label `demo`, tell the studio lead and do not start. If the label is gone, the studio lead tells you what to do; you do not guess.
2. **Browser profile, so the film is clean** (only if run card row 13 lists C.2). In Chrome click your account picture at the top right, then "Add", then "Continue without an account", and name the profile `demo-take` (path not checked). If the profile already exists, use it. In that profile sign in only to the HubSpot test account and the receiver account (with the label `demo`), and to n8n only if item 3 says so. This is a Chrome profile, not a new account. Tell the studio lead: "profile ready".
3. **n8n sign-in, only if run card row 9 says so.** Your n8n account already exists and holds its connections. So you do nothing in n8n unless run card row 9 says you must sign in. If it does: sign in with your existing n8n account (never type the password into chat; keep it only where you keep your own passwords). If a screen asks you to type a connection value again, the studio lead sends the full path of the secret file that holds it and the command to show it. Do this with no recording running and nobody watching: show the value in WSL, select it, copy, paste into the n8n field, then type `clear` in WSL, close that terminal window (`clear` does not remove everything the window kept above), and clear the clipboard history (Windows key + V, then "Clear all"; path not checked). Never paste the value into chat. Tell the studio lead only: "done". The printed form of the command the studio lead sends is `cat <full path from run card row 8>`; if the path is not inside the secret folder of row 8, stop. Follow rule 9 first. (This is the one place you copy a connection value yourself; elsewhere you rebuild no connections.)
   - Stop and tell the studio lead: n8n shows a saved secret in clear text on screen or in an export.

### Step D. What the film may show (you, before the run and again on the finished footage; only if run card row 13 lists D)
Who films, who starts the recording and who edits is on the run card (row 4). Until it is filled, no run starts.
Check in the `demo-take` profile that NONE of these shows an address other than the test addresses `take-<run name>-a@example.com`, `-b@` and `-c@`:
1. Receiver mailbox: do not click or hover your account picture. Do not open a mail or "show details". Look at the mail LIST only. If a list row shows another address (the sender column), tell the studio lead; the studio lead decides what is filmed. Also check the Gmail tab title and the Gmail top bar: a Gmail tab title can carry the account address (for example in the title "Inbox (1) - <address>"). If it does, the studio lead decides: crop or retake. Do not film the window with that tab visible.
2. Do not film the sender mailbox or its "Send mail as" settings.
3. Tab titles and the address bar, if they carry an address (see item 1).
4. n8n's list of runs, only if n8n is a film or proof screen: only made-up names and test addresses, and no old run. Do not film the detail of the mail-sending step (it may show the company address and the sender address). Until the studio lead says that detail is safe, do not open it.
5. The proof screen: only test addresses and counts.
6. Terminal windows: no address in the prompt, history or settings output.
7. Notifications, desktop pop-ups, the system tray.
8. **Account ids.** None of these may show on film: a HubSpot portal or account number (it appears in the address bar after the site name, and in the page header); the account picture menu in HubSpot, Gmail or n8n; n8n's account or project name and its list of runs with old runs; your n8n address or login name; any address bar that shows a number or name that is yours. Crop or retake; the studio lead decides.
9. The HubSpot contact list: step 0 makes one made-up contact at `example.com` and deletes it; if it is still there, do not film it (delete it by hand first, as step 0 says).
You should see only test addresses and no account number. Stop and tell the studio lead: any other address or any account number is visible. The footage is then cropped or retaken before any use.

## The run

> **WARNING before step E. This is the first live run. After you type the confirmation line (E.4) the program makes up to 3 paid model calls (real money, up to the total in your written yes), writes real contacts to the HubSpot test account and sends real mails from the sender Gmail account to the receiver Gmail account. None of this can be undone and the money is not refunded. Anything that holds the model key could spend more than your yes until the key is cancelled (step I.5b). If you are unsure about anything on the screen, a number, an account or a word: type nothing and tell the studio lead. Typing nothing sends nothing and spends nothing. Typing anything other than `y` at the first prompt (for example `n`) ends the run with nothing sent.**

### Step E. Start the run and type `y` (you, in your own terminal)
Have ready: WSL open, the `cd` line from the studio lead typed (you are in the run folder), the `demo-take` profile ready (C.2), laptop on mains, the written yes sent (A), the run card complete. Before you start, compare the masked sender and receiver (from the notice if the program prints them, otherwise from the studio lead's step A message) with your own two throwaway accounts. If they do not match, do not start. Then send the studio lead the sentence of row E.0: "receiver and sender are the throwaway accounts". Also check the program file: type `sha256sum scripts/run_real_check_n8n.py` and compare with run card row 14; if it differs, do not start. The studio lead sends you one line to run, of this form: `python3 scripts/run_real_check_n8n.py --take <run settings file>`. Type it, press Enter. The run name is in the run settings file, not in the command. You should see, in this order:
1. The program prints `mailbox login: still works` and `HubSpot login: still works`. A bad login stops the run here (exit code 2), before you type anything.
2. The notice, with a random 6-digit "Confirmation number (type it, a space and the take id)". ("take id" is your run name.)
3. "Type y to start".
4. "Now type the confirmation number shown above, a space and the take id to confirm:".

**Compare the notice (E.2).** The notice shows: 3 test people, up to 3 model calls and the worst case, up to 3 contacts deleted at the end, up to 3 mails (see "Send counts"), n8n stopped once. Answer no (type nothing, tell the studio lead) if ANY of these is true:
- the worst-case price per call on the notice is not the price in the studio lead's message;
- the worst-case total on the notice is not 3 times that price, or is more than the total in your written yes;
- the spending backstop in the studio lead's message (and, if run card row 8 allows it, in the model settings file) is more than the total in your written yes, or the two differ. The notice's numbers and the lead's message both come from the lead's files, so this compares the lead with itself; the real protection is your yes: more than the total in your yes means no;
- the masked sender or receiver (if the notice prints them) is not one of your two throwaway accounts;
- the stop time on the notice is not 2026-11-23 18:29 UTC = 23:59 IST;
- the number of test people, model calls or mails is more than 3.

Then:
- Type `y` and Enter **yourself**. A `y` fed in by another program is refused on purpose. If the input is closed (for example the terminal is closed), the run ends with exit code 2 and nothing is sent. The flags `--yes` and `-y` do not exist.
- Then type the 6-digit number the notice showed (new every run), a space, your run name, and Enter. Example: `123456 <run name>`. An answer typed faster than the program's minimum (2 seconds unless the studio lead changed it; allowed 1 to 60) is refused with exit code 2. A wrong line ends the run with exit code 1 and nothing is sent.
- Pick a NEW run name for every run, also after a failed one. After both typed answers the program writes the marker file in the Linux home folder. See which run names are used with `ls ~/.hadavin-take-tags`. If the run stopped at a login line before you typed anything, the name is not yet used; the studio lead says whether you may reuse it.
- If a login line says anything other than "still works", nothing was sent. Tell the studio lead. Do not start again until the studio lead says so, not even once. (The earlier sheet allowed one retry; this sheet is stricter because repeated failed logins can trigger a Google sign-in alert.)
- **How long it takes and when it is finished.** The run card (row 3) gives the normal length. The run is finished when the program prints its result and the `$` prompt comes back; then type `echo $?` and send the number and the last printed line to the studio lead. The studio lead then stops the model program and says "model program stopped". If nothing new prints for longer than run card row 12 says, tell the studio lead and wait; do not press Ctrl-C and do not close the terminal.
- After you type the confirmation line (E.4), send the studio lead one line: "run started". The studio lead then gives the person named on run card row 5 the cue to stop and restart n8n and the person named on row 4 the cue to film. If the card names nobody for row 4 or row 5, no run starts.
- During the run: contacts appear in HubSpot and mails appear in the label `demo`. n8n is stopped and started again once while person C is sent. The person named on run card row 5 does that. You touch nothing unless the card says you are that person and gives you the line; you do not use Docker.
- Stop and tell the studio lead: a number in the notice is not what you approved; a count is wrong; the laptop sleeps.
- **The proof screen is your choice.** The run card (row 10) offers candidate screens. You pick one and say which. The studio lead says what it shows. The video must not show or claim any portal, approval step or audit trail.

> **WARNING before step F. When the program asks for `end`, closing the terminal, pressing Ctrl-C, or typing two wrong lines in a row ENDS the pause and DELETES the test contacts from HubSpot BEFORE they are filmed. A closed input on the FIRST prompt ends the pause at once. After the contacts are deleted they cannot be filmed, the money is already spent, and a new run needs a new yes (step A) and a new run name. Type exactly `end` (three letters, lower case), and only when the filming of the contact list is done.**

### Step F. The film pause: type `end` (you)
The program prints: "Film the contact list now: type `end` and press Enter to archive" (it means delete). The person named on run card row 4 films the HubSpot contact list. To find this run's contacts in HubSpot: Contacts, then the search box, type your run name (path not checked). You should see 2 or 3 contacts (see "Send counts"). If the search shows nothing, or a different number, tell the studio lead and wait; do not type `end`. Type `end` and Enter yourself only when that person tells you the contact list is filmed (if you film, when you have filmed it). The program then deletes this run's contacts. Only the exact word `end` ends the pause. Any other line makes the program print "type exactly: end" and ask once more; a second wrong line also ends the pause and deletes the contacts.
You should see HubSpot show no contacts of this run afterwards, and the program print its result.
- Stop and tell the studio lead: you closed the terminal or pressed Ctrl-C early. Leftover contacts are deleted by hand in HubSpot; the studio lead gives you the count.
- If step 0 did not show that the HubSpot key can delete contacts, the deletion fails after the sends and you delete the leftover contacts by hand in HubSpot (step G rules).

### Step T. Trial run (only if run card row 6 says yes and row 13 lists T)
A trial run is a real run on your throwaway accounts: real model calls (real money), real HubSpot contacts, real mails. So it needs its own written yes with numbers (step A), its own new run name, the boxed warnings of steps E and F, and then step G's clean-up. Its run name is used up. After the trial the real run needs a NEW written yes and a NEW run name, and step C.1 (empty label and inbox) is done again; C.1 is satisfied only after step G has emptied them. The trial's money counts in "the money spent so far" in the next yes. Nothing from a trial is filmed or posted.

> **WARNING before step G. In step G delete ONLY mails in the receiver account and ONLY HubSpot contacts of the failed run (the studio lead gives you the count and the run name). Emptying the Trash cannot be undone: if the Trash holds anything other than these demo mails, do NOT empty it; tell the studio lead. Never delete the marker file `~/.hadavin-take-tags/<run name>.used`.**

### Step G. If a run fails, or after a trial run (you; only if run card row 13 lists G)
The studio lead says why, by message. Then:
1. In the receiver Gmail open the label `demo` and the Inbox. Select only the demo mails (subject starts with `[demo] lead`; "lead" here is a made-up sales contact). Click the Trash icon (path not checked). Open Trash: it must hold only these demo mails. If it holds anything else, stop and tell the studio lead. Otherwise click "Empty Trash now" (path not checked). (This is "delete" in the Words box.)
2. In HubSpot, delete any leftover contacts the studio lead counted: Contacts, search your run name, tick each contact one by one (never the select-all box at the top of the list), More, Delete (path not checked). Delete only contacts whose name or address carries this run name, and only as many as the studio lead counted; if the number ticked differs, stop.
3. Tell the studio lead: "demo mails deleted" and the number of contacts you deleted.
4. Give a NEW written yes with numbers (step A) and pick a NEW run name. A run that got past both typed answers has used its name even if it failed. If the failed run's contact count was an "unknown" for C, the studio lead tells you whether a contact or an alert mail may remain and where the alert mail goes (the studio lead's question); until then delete only what the studio lead counted.
If the studio lead later says a new run is no longer possible before the stop time, no new run happens.

## After the run

### Step H. You watch the edited video
The studio lead tells you the deadline (run card row 7). Watch from the first second to the last: once at full speed, once pausing on each cut. No address may show except test addresses. Reply "accepted" or list the bad seconds with times. If any real address shows, say "an address is visible" and the second. Clean-up (I) starts only after you reply "accepted" and the studio lead says the last run is done. After clean-up starts, no further run happens.

> **WARNING before step I. The deletes and cancellations in step I cannot be undone. Remove only what the studio lead's confirmed list names AND what run card rows 8, 15 and 16 allow. Never delete `~/.hadavin-take-tags/<run name>.used`. Do not remove the secret files until the retire check has succeeded (or step I.4 says what to do instead). If anything on a list, a card row or a screen is unclear, remove nothing and tell the studio lead.**

### Step I. Clean-up (you, with the studio lead; deadline on the run card row 7)
Starts when the studio lead says the last run is done and has said "model program stopped". Order matters. Use your normal browser profile for Google and HubSpot pages in this step, not `demo-take`; nothing in step I is filmed.
1. **Revoke the app passwords named by the studio lead, in both accounts** (receiver and sender). The studio lead sends the list of app password names to revoke, and run card row 15 says for each whether it is revoked or kept on purpose. Open myaccount.google.com, Security, App passwords (this needs 2-Step Verification, which is already on) (path not checked). Compare the names in the account with the studio lead's list. Revoke only the names on the list, with the bin or "Remove" next to each (path not checked). A name that is in the account but not on the list is left alone; tell the studio lead its name, because something else may use it. Take a screenshot of each list afterwards. Before saving, crop or cover any address that shows (account picture, name, address). To crop on Windows use the Snipping Tool: Start menu, type `Snipping`, Enter (path not checked). The Snipping Tool may have saved the uncropped original too (a pop-up offers it, and a copy may sit in the Pictures folder, in `Screenshots`; path not checked): delete the uncropped originals the same day.
2. **Delete the HubSpot private apps made for this run** (only if run card row 15 says the key is revoked, and only after the studio lead sends the list of app names). Look at each app's name and creation date in HubSpot (Settings, Integrations, Private Apps) (path not checked). If you cannot tell which app the program used, delete nothing and tell the studio lead the app names. Deleting a private app cannot be undone; anything using its key (the program, n8n's HubSpot connection) stops working. Then take a screenshot and send the studio lead the names of the apps you deleted. (A HubSpot key may not end by itself; that is not checked. A key kept on purpose is revoked by the end date on row 15, or by the stop time if row 15 has none.)
   - **If run card row 15 says the HubSpot key is kept on purpose:** do not delete any HubSpot private app. The HubSpot line of the retire check (item 4) is then expected to say "STILL WORKS". That is not a failure of the clean-up. The studio lead writes the end date down.
3. Save the screenshots in `C:\Users\<your-user>\Downloads\Hadavin\_local\real-run\` under the names the studio lead gives (only if run card row 13 lists I.3).
4. **Retire check.** The studio lead sends the exact command (form: `python3 scripts/run_real_check_n8n.py --retire-check <run settings file>`) and says which folder to type it in. Run it BEFORE the secret files are removed, and while the run settings file still exists (the studio lead keeps the run settings file and the run folder until the check has succeeded). Then type `echo $?` and send the studio lead the printed words and the number. It should print "refused as expected" for the mailbox and for HubSpot, exit code 0. That is "retire check succeeded".
   - "STILL WORKS" for the mailbox (exit code 3): revoke the app password again (item 1), then run the check again.
   - "STILL WORKS" for HubSpot (exit code 3), run card row 15 says "revoked": delete the HubSpot private app again (item 2), then run the check again.
   - "STILL WORKS" for HubSpot, run card row 15 says "kept on purpose": this counts as succeeded only if the mailbox line says "refused as expected". The studio lead then says "retire check succeeded, HubSpot key kept on purpose". Keep the secret file of the kept key if the studio lead says so.
   - "could not tell" (exit code 2): wait for the studio lead; do not rerun more than twice in all (repeated failed logins can trigger a Google sign-in alert).
   - **If the check cannot succeed** (exit code 2 twice, a run card row missing, or the studio lead cannot say what counts): keep every secret file, remove nothing more, tell the studio lead, and the studio lead writes down what is left and the date to finish. Do not remove secret files to get past this item.
   - Keep the secret files until the check has succeeded.
5. Only after it succeeded, tell the studio lead "retire check succeeded". The studio lead (not you) then removes n8n's connections and saved runs (the records n8n keeps of each time it handled a test person: made-up data and perhaps the company address), stops n8n, and removes the run folder and the database container (see the Words box). The retire check does not test the model key or the database passwords: the studio lead tells you by message what happens to the database passwords; do nothing about them until told.
   **5b. Cancel the model key (default; run card row 16).** The studio lead has said "model program stopped". In the model account (path not checked), open the list of keys, find the key the studio lead names (by its name, never its value), and delete it. Type "model key cancelled" to the studio lead. If run card row 16 says the key is kept, the studio lead gives a written reason and an end date on the card; without an end date it is cancelled by the stop time Mon 23 Nov 2026 18:29 UTC = 23:59 IST. Cancelling it ends any spending after the run; the credit left in the account stays for now and is not yours to move.
6. **Remove the secret files in WSL.** The studio lead sends the list as FULL paths (printed form `<secret folder from row 8>/<file name from row 8>`). Check each one: it starts with the secret folder of row 8; its last name is a name in row 8; it holds no `*`, no `?`, no `..`, no `~` and no leading `-`; it does not end `.used`; it is not under `~/.hadavin-take-tags`; it is not the run settings file; it is not the model key file unless item 5b is done (the model key file is removed after the key is cancelled). If any path fails a check, remove nothing and tell the studio lead. Then type `ls -l <the full paths, separated by spaces>` and Enter and compare the names, one by one, with run card row 8 and the studio lead's list. Only if they match, type `shred -u -- <the same full paths>` and Enter. If it says `shred: command not found`, type `rm -- <the same full paths>` instead. These cannot be undone. Then type `ls -l <secret folder>` and check that the named files are gone. Then tell the studio lead: "secret files removed". Do NOT delete `~/.hadavin-take-tags/<run name>.used`.
7. Set laptop sleep and lid settings back. Sign out of the `demo-take` browser profile (only if run card row 13 lists I.7).
- The copy of the passwords inside n8n ends only by your revocation in item 1; you can only show that with a screenshot, not a check.

### Step J. Post (you; latest Wed 25 Nov 2026, 15:00 UTC = 20:30 IST)
You post; Claude never posts. The post says only: contacts arrive through n8n; n8n writes the HubSpot contact and sends the mail; our code asks the model at most once per test person and writes each paid call down before it is made, and the program counts the mails and contacts; **"the same person id sent twice is processed once", but only if the studio lead confirms in writing that the run's own result shows it for this run (the plan's check for a double mail passed); otherwise this sentence is left out** ("person id" is the id the system gives each test person when it sends them in).
It must NOT say:
- that the same person through two doors is one contact;
- that no contact data stays in n8n, or that recovery takes within 60 seconds, or that an alert comes within 30 seconds;
- that a portal, an approval step or an audit trail exists or shows these rows, or anything that suggests a person approves each action;
- that n8n cannot reach the internet (its outgoing traffic is switched off by settings and only watched, not blocked);
- that the run is crash-safe, or that no mail is sent twice after a crash between sending the mail and noting it. This ban does NOT lift when the rehearsal passes, because the rehearsal uses stand-in programs; it lifts only on a result from the real program that the studio lead states in writing;
- that the count is made by a "separate check" or "separate login" (not built);
- that everything is in one database (the aim is one Postgres database program with n8n's data in its own database inside it; it is not proven until the rehearsal shows it; some files stay outside it);
- that the spend is capped by a hard limit (it is a setting a person checks);
- that test data was "deleted permanently" or "erased" (HubSpot may keep an archived copy, and Gmail's deleted mail may stay for a time);
- anything about which permissions any part has or does not have (for example "only reads", "least privilege", "each part has only what it needs").
The exact final words come from the studio lead after the rehearsal. Until you have them, do not post. Someone other than the author of the words checks the post against this list before you post (run card row 11 names who). After you post, type "posted" to the studio lead.

## What to send the studio lead (never a secret)

| When | Send |
|---|---|
| Before a run | the run name you picked (a word, no secret); the step 0 table and its exit-code number (or "a key-like text is in the table"); your written yes with numbers (step A); "receiver and sender are the throwaway accounts" (row E.0) |
| Run day | "label and inbox empty"; "profile ready"; "done" for n8n, only if asked; any problem line from step C |
| During a run | "run started" after E.4; the proof screen you picked; "closed the terminal early" if it happens |
| End of a run | the exit-code number and the last printed line (the studio lead then says "model program stopped") |
| After a run | "accepted" or the bad seconds; "an address is visible" if you see one |
| After a failed run or a trial run | "demo mails deleted" and the number of contacts deleted; a new written yes and a new run name |
| Clean-up | the names of any app password or HubSpot private app you left alone; the names of the HubSpot private apps you deleted; the screenshots (saved as the studio lead says; the screenshots are not sent in chat unless the studio lead asks for them in step I.3); the retire-check words and exit-code number; "retire check succeeded"; "model key cancelled"; "secret files removed" |
| Before posting | the post text, for comparison with the final claim |
| After posting | "posted" |

## Refusals and exit codes you may meet

Exit codes of the run program (step E):
- 0: success.
- 1: your answer was not `y`, or the confirmation line did not match.
- 2: the program refused to start or to go on: a setting, a failed login check, no keyboard, closed input, an answer typed too fast, a run name or key used before, a lock file exists, the stop time too close, a second mailbox, Ctrl-C before the first send.
- 3: a count or verdict failed after the run, or Ctrl-C after the sends began ("interrupted after the sends began").
- Rare: a signal at the very end can turn a success into exit 3 or leave the exit status as 120, and can leave the run lock file. If that happens, do not run again: tell the studio lead; it reads the result file the program wrote in the run folder.

Exit codes of the retire check (step I) are different:
- 0: both logins refused (good).
- 3: a login still works.
- 2: anything else ("could not tell").

Other refusals:
> **WARNING before deleting the run lock file. This delete cannot be undone and the lock protects against a second run with the same run name. Delete only the one file the studio lead names by its full path, only after the studio lead says so.**

- **Run lock file:** if the program stops hard it may leave `take-<run name>.lock` beside the run folder; the next run with the same run name is refused. Remove it ONLY when the studio lead says so. Printed form: `ls -l <full path>`, compare with the studio lead's message, then `rm -- <full path>`. The name must be exactly `take-<run name>.lock`, with no `*` or `?`; anything else: stop.
- **Start deadline:** the program refuses to start unless it can finish about 14 minutes before the stop time. With stop time 18:29 UTC the latest start is before 18:14:40 UTC = 23:44:40 IST at the default setting. Run card row 3 gives the exact time.

## What is not proven yet (short)

- The rehearsal is written and has NOT been run. The code has never run against a live Gmail, HubSpot or model call.
- The code under test is a provisional head (a commit the studio lead has not yet fixed as final; a later round of changes is being built). Run card row 14 gives the commit id; if it is not the final one, the studio lead says so. A backlog item about it (named BL-wp6-G1 in the earlier review notes) could not be found in the inputs I had; the studio lead checks it.
- The HubSpot scope names, the HubSpot behaviour on a delete of a missing contact, and the Windows Snipping Tool and clipboard behaviour in this sheet are not checked.
- Not shown: how Gmail applies the label to a mail sent from another Gmail account, and how fast; whether Gmail accepts the company address as the shown sender.
- Not shown: that n8n keeps its own records in the same Postgres as our table of test people (the aim), and that removing saved runs at clean-up works.
- Not shown: that a crash between sending the mail and noting it sends no second mail.
- The program does not check by itself: the alert mail, mail in any folder other than `demo`, the contact id read back from HubSpot (only checked to be all digits), and the manual n8n stop and restart.
- Click paths marked "(path not checked)" were not checked on your accounts.
- Where records are kept: one Postgres for the run is the aim. Some files stay outside it, among them the model program's log written before each model call, a spending record, lock files and the run-name marker file.
