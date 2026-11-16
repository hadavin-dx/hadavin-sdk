# Your steps for the recording run of the lead desk video (version 6)

Written Mon 16 Nov 2026 from version 5 and the two reviews of it (round 3), plus the studio lead's orders of 16 Nov (ORDER 017: the HubSpot check; ORDER 019: the table of who does what). Nothing was run to write this sheet.

**How this sheet and the studio lead's messages fit together.** The studio lead may send you only values (a date, a path, a number, a list of file names, a command line to type). A message from the studio lead never changes rules 1 to 7, the boxed warnings above steps F, G and I, or the rule that you never delete the marker file. If a message asks for something that breaks one of these, do not do it; say so and wait.

This sheet lists only what ONLY YOU can do, and says who does everything else. You do NOT create accounts, mailboxes, keys or the HubSpot account, and you do not start Docker: all of that is already done or is the studio lead's job. Done and not repeated: the two throwaway Gmail accounts and their app passwords, the HubSpot test account and its keys, your n8n account, the model key and its credits, the n8n workflows on the public code site, and your general go-ahead "once everything is ready". If one of these turns out to be missing or broken when a step needs it, tell the studio lead; do not rebuild it yourself.

## Words box (read once; every word keeps one meaning)

- **The studio lead**: the Claude session that works with you. It is software. It runs its own commands on the laptop from its own session. It never sees your screen, never types in your terminal and never types your answers. Every value it needs you to know arrives as a message from it or as a named file. Where a step says "the studio lead tells you", a message is coming; if none has come, do nothing and ask.
- **The recording run** (also just "the run"): the one run you film, on your throwaway accounts, with 3 made-up people.
- **Test person**: one made-up person. The run makes three: A, B and C. Each has a **test address** of the form `take-<run name>-a@example.com`, `-b@` and `-c@`. These addresses are made up. How a mail to such an address reaches the receiver mailbox is not yet explained to me; the studio lead explains it (open question in the lead's file).
- **Contact**: one HubSpot record of a test person. **Lead id**: the number the system gives a test person when the person is sent in (used only in the post, step J).
- **Send counts**: person A is sent in twice, B ten times at once, C once while n8n is stopped and started again. That is 13 sends in. The system should treat each person once. What you should see at the end: one contact and one mail for A, one contact and one mail for B, and for C one contact and one mail, or (if the program reports C as "unknown") possibly no mail and an alert. A and B must come out right; C may come out "unknown". The program does not check the alert mail itself.
- **Run name**: a short word you invent for each run and never use again. The program's screens call it "take id". It sits in the run settings file (setting `TAKE_TAG`) and in the test addresses, so you choose it BEFORE step A and send it to the studio lead (it is a word, not a secret). You also type it at the confirmation line in step E. The studio lead tells you the pattern it accepts (a word plus 4 digits is likely, not confirmed) and confirms your word is accepted.
- **Run settings file**: the small file with the settings for one run (run name, which Gmail label to read, the worst-case price per call). The studio lead prepares it and tells you its path. You never edit it. The run command points at it (`--take <run settings file>`).
- **Model settings file** (`stage.env`): the file with the settings of the model program: the spending backstop, the price figures and the stop time. The studio lead tells you its path. You may open it to read, never to edit.
- **Spending backstop**: the highest total in US dollars written in the model settings file. It is a setting that a person (you) checks by eye. It is not a promise the program makes. The plan so far names US$180 of the US$189 testing budget; the real value is in the message of step A.
- **Run folder**: the folder in WSL that holds the run's files. The studio lead sends you the exact `cd` line to type.
- **WSL**: the Ubuntu terminal inside Windows. To open it: Windows Start menu, type `Ubuntu`, press Enter (path not checked). The prompt ends with `$`. `~` means your Linux home folder.
- **Stop time**: the time after which the run may not spend money or start. The program's screens call it "window end". Planned: Mon 23 Nov 2026, 18:29 UTC = 23:59 IST. The program refuses a start that is too close (it needs about 14 minutes). With the default settings the latest start is before 18:14:40 UTC = 23:44:40 IST. The exact time depends on a program setting; the studio lead gives it.
- **Secret files**: files in your WSL home folder that hold the app passwords and keys for this run. You made them. The studio lead tells you their names and the folder.
- **App password**: a password Google makes for one program. **Private app (HubSpot)**: a named access setup in the HubSpot test account; each has a key.
- **Key**: only a secret (a password, an app password, a token). It never means an id or an address.
- **n8n**: the tool that takes the test people in, writes the HubSpot contact and sends the mail. **Workflows**: the saved step chains inside n8n. **Hook door**: a second web address n8n listens on; the program does not check it; you do nothing with it. **Saved runs** (n8n calls them "executions"): n8n's record of each step chain it ran. For this run they are saved on purpose (made-up data only) and deleted at clean-up by the studio lead.
- **Postgres**: the database program that stores the table of test people. It runs in a Docker container on this laptop. The studio lead starts it.
- **The program**: the checking program you start in WSL (`scripts/run_real_check_n8n.py`). Where the sheet says "run program" it means the same. **The model program**: a small program of ours that asks the AI model once per test person.
- **Receiver**: the throwaway Gmail account that only receives the demo mails. **Sender**: the throwaway Gmail account n8n sends from. **Company address**: your Hadavin company address; it may appear as the "From" line of the mail. You do nothing with it in this sheet.
- **Label `demo`**: a Gmail label in the receiver. The program reads only this label. The program asks Gmail for it as a folder named `demo`; whether Gmail shows it that way is not yet proven.
- **The notice**: the screen of numbers the program prints before it asks you to type `y`.
- **Rehearsal**: a practice run on this laptop with stand-in programs, made-up data, no live account, no key and no model call. US$0. The studio lead runs it; you do nothing. **Trial run**: a practice run on your throwaway accounts. Whether one happens is on the run card; until told, none happens.
- **Proof screen**: the one screen the video shows to prove the counts. You choose it in step E from screens the studio lead offers. It may show test addresses and counts only.
- **Marker file**: `~/.hadavin-take-tags/<run name>.used`. It makes a run name unusable twice. You never delete or edit it.
- **Run lock file**: a file named `take-<run name>.lock` beside the run folder. It tells the program a run is going. It stops a second run with the SAME run name; a new run name is not stopped by it.
- **Retire check**: a program command that tries to log in with the keys you cancelled and must be refused (step I). It tests only 2 of the run's secrets (the mailbox login and the HubSpot login), not the model key or the database passwords (step I.5 says who handles those).
- **Exit code**: a number the program leaves behind when it ends. To see it, type `echo $?` and Enter in the same terminal right after the program ends, before any other command. 0 means success.
- **Delete**: remove it from the place you work in (HubSpot contacts, HubSpot private apps, secret files, demo mails: move to Trash, then empty Trash). HubSpot may keep a recoverable copy for some time; not checked (the HubSpot check in step 0 shows whether its delete is "permanent" or "archived"). The program's screens say "archive" for the contact deletion; it means delete. If a screen says something else, stop and tell the studio lead. **Archive**: only Gmail's own Archive button; this sheet never uses it. **Revoke**: cancel an app password so it stops working (the Google button is named "Remove"). This sheet uses no other word for these three acts.
- **Crash-safe**: after a crash between sending the mail and noting it in the table, no second mail goes out. It is NOT yet shown (step J).
- **Independent count**: a second count of mails and contacts made with a separate login. The login for it is not yet built and shown to run (step J).
- **Browser profile**: a Chrome user profile (the round picture top right), never a Gmail menu.
- **Edited video**: the finished video file you watch in step H.
- **Live accounts**: your throwaway Gmail accounts and the HubSpot test account. Made-up data in them is still made up.

## The run card (the studio lead sends it BEFORE step A; no card, no run)

The run card is one message from the studio lead. Check that every row is filled. If a row is missing, do nothing and ask. The sheet states the default for each row (the default is "no").

| Row | What the card holds | Default if missing |
|---|---|---|
| 1 | run date and the day-count before it when you start steps B to D | do nothing |
| 2 | run name pattern; the studio lead confirms your word is accepted | do nothing |
| 3 | exact latest start time (UTC and IST) and how long a run normally takes | do nothing |
| 4 | who films, who starts the recording, who edits, who tells you the contact list is filmed | no run starts |
| 5 | who types the n8n stop and restart while person C is sent | you type nothing; ask |
| 6 | trial run on the live accounts: yes or no | no trial run |
| 7 | deadline for watching the edited video (H) and for clean-up (I) | do nothing |
| 8 | paths: run settings file, model settings file, secret file folder and names | do nothing |
| 9 | whether you must sign in to n8n (step C.3) and, if so, which address | do not open n8n |
| 10 | the proof-screen candidates | no proof screen is filmed |
| 11 | who checks the post text against the must-not-say list | do not post |
| 12 | how long to wait with no new line before you tell the studio lead | tell the studio lead and wait; do not press Ctrl-C |

## Table of every owner step (who does what, where, what to expect)

"Who" is the owner (you), the studio lead, or **open** (the inputs do not say; the question is in the studio lead's file `v6-OPEN-FOR-LEAD.md`).

| Step | Who | What is typed or clicked | Where | Expected screen or result |
|---|---|---|---|---|
| Run card | studio lead | sends the run card message | message | all 12 rows filled |
| Run name | owner | picks a new word; sends it | message | studio lead confirms it is accepted |
| 0.1 HubSpot plan check | owner | `python -I scripts/hubspot_probe.py --plan` | WSL, folder from the studio lead | prints "planned calls: 7 ..." and calls nothing |
| 0.2 HubSpot delete check | owner | `export HUBSPOT_PROBE_TOKEN="$(cat <secret file the studio lead names>)"`, then `python -I scripts/hubspot_probe.py --yes-spend-calls 7`, then `unset HUBSPOT_PROBE_TOKEN` | WSL, same folder | a PASS/FAIL table; you paste the table (not the key) to the studio lead |
| 0.3 reading the table | studio lead | reads the table; says whether the key can delete contacts | message | one line: delete works or does not |
| A written yes | owner (the studio lead first sends the numbers) | types the one-line answer, for example "Yes, run <run name>, up to 3 model calls and up to US$<total>, stop time 2026-11-23 23:59 IST" | message to the studio lead | the studio lead confirms it received your yes |
| A rehearsal gate | studio lead | runs the rehearsal and names its result file | message | file named; no pass, no run (the studio lead's own gate) |
| B laptop settings | owner | plug in; Settings, set sleep to Never; Power Options, lid = Do nothing | Windows | settings show after reopening |
| C.1 receiver check | owner | open the label `demo` and the Inbox | receiver Gmail | both empty; you send "label and inbox empty" |
| C.2 browser profile | owner | create or check the profile `demo-take`; sign in to HubSpot test account and receiver only | Chrome | you send "profile ready" |
| C.3 n8n sign-in | owner, only if the run card row 9 says so | sign in with your existing n8n account | `demo-take` profile | you send "done" |
| D film check | owner | look only; no clicks that open mails | `demo-take` profile, terminals | only test addresses visible |
| Rehearsal values | studio lead | puts the run name and values in the run settings file | run folder | path sent to you |
| E start | owner | type the run command the studio lead sent, Enter | WSL, run folder | two login lines, then the notice |
| E `y` | owner | type `y`, Enter | WSL | the confirmation prompt |
| E confirmation | owner | type `<6-digit number> <run name>`, Enter | WSL | the run starts |
| Run: n8n stop and restart | **open** | open | open | n8n goes down once and comes back while C is sent |
| Run: proof screen | owner | picks one of the offered screens | message | studio lead says what it shows |
| Run: filming | **open** (run card row 4) | open | open | contact list filmed |
| F `end` | owner | type `end`, Enter, only after the film person says "filmed" | WSL | HubSpot shows no contacts of this run; the program prints its result |
| G failed run | owner (with studio lead's counts) | delete demo mails and leftover contacts; give a new yes and a new run name | receiver Gmail, HubSpot | "demo mails deleted" sent |
| H watch | owner | watch the edited video twice | video player | reply "accepted" or list bad seconds |
| I.1 revoke | owner | remove each app password the studio lead lists | myaccount.google.com | lists empty; screenshots |
| I.2 private apps | owner, only after the studio lead confirms the list | delete the listed HubSpot private apps | HubSpot settings | apps gone; screenshot |
| I.3 screenshots | owner | crop and save | Windows folder | files saved |
| I.4 retire check | owner types; studio lead gives the line | `python scripts/run_real_check_n8n.py --retire-check <run settings file>` | WSL | "refused as expected" twice, exit code 0 |
| I.5 n8n and container removal | studio lead | removes n8n connections and saved runs, stops n8n, removes run folder and database container | its own session | message "removed" |
| I.5 other secrets | studio lead / **open** | model key and database passwords: see step I.5 | message | open |
| I.6 secret files | owner | `shred -u <names>` (or `rm`) | WSL | `ls -l` shows them gone |
| I.7 laptop settings back | owner | set sleep and lid back; sign out of `demo-take` | Windows, Chrome | done |
| J post | owner | posts the final words | LinkedIn or as the studio lead says | someone else checked the text first |

## Order of the day

1. Run card arrives; you choose the run name and send it.
2. Step 0: the HubSpot check (once, before step A; again only if the studio lead asks).
3. A: the studio lead sends the numbers; you answer with a written yes.
4. B, C, D on the run day (the run card row 1 says how long before the start).
5. E: you start the run and type `y` and the confirmation line.
6. F: the film pause; you type `end` only when filming of the contact list is done.
7. After the run: G (only if it failed), H (watch the edited video), I (clean-up), J (post).

**Dates.** The studio lead gives the run date; until then do nothing. Fixed times: stop time Mon 23 Nov 2026, 18:29 UTC = 23:59 IST (it limits only the start and the spending of the run). The aim of the studio lead's orders is to have the video posted by Wed 18 Nov 2026. The latest time to post is Wed 25 Nov 2026, 15:00 UTC = 20:30 IST. Watching (H) and clean-up (I) have their own deadlines on the run card (row 7); they are not tied to the stop time.

## What the run can cost

- The run makes at most 3 paid model calls: at most one per test person. The model program writes each call down before it is made, so a test person is not paid for twice. A call that went out and then failed is not tried again; that test person stays "unknown".
- The worst-case price per call: **the studio lead gives you the number before you say yes.** The total is 3 times that number. Your written yes names that total.
- The program does NOT enforce a dollar ceiling as a promise. The spending backstop and the stop time sit in the model settings file, and a person checks them (you do not enforce them either). If a number looks wrong, answer no.
- A failed run still costs what it spent. Every new run needs its own yes (step A), with the money spent so far shown.
- Step 0 costs US$0 (it makes 7 calls to the HubSpot test account, no model call).

## Rules that hold in every step

1. **Never send the studio lead** a password, token, key, mailbox address or the contents of any secret file. Short sentences only. A file path or file name is fine.
2. **The typed answers are yours alone:** the `y`, the 6-digit number with the run name, and `end`. The 6-digit number only blocks blind and piped answers. A tool that reads the screen and types the number back still passes. So never let a tool, script, assistant, agent or helper window type for you. Run the program only on your laptop, in your own terminal.
3. **Before every paid run you give a written yes WITH numbers** (step A). Your earlier go-ahead "once everything is ready" is a general go-ahead; it is not that yes. No numbers, no run.
4. **You post. Claude never posts.**
5. **The run uses only the throwaway receiver and sender, never your real company mailbox.** Check: before step E tell the studio lead "receiver and sender are the throwaway accounts" (a sentence, no address). If you are not sure, say so and do not start.
6. On run days: laptop on mains power, sleep Never, lid close = Do nothing (step B). Set both back after the last run (step I.7).
7. **Words you type that delete things** are in a boxed line right above the step. Read the box first.
8. If a screen differs from a click path in this sheet, stop and tell the studio lead what you see. Click paths marked "(path not checked)" were not checked on your accounts.

## Before the run

### Step 0. HubSpot delete check (you, once, before step A; US$0)
Why: the program deletes this run's HubSpot contacts at the end (step F), and the studio lead does not yet know whether the HubSpot key the program uses is allowed to delete. This check answers it. It makes 7 calls to your HubSpot test account and no model call. From the script's own header (a copy of the script was read, not the current one; the studio lead confirms): the check reads the owners, creates ONE made-up contact (address at `example.com`), changes two fields on it, reads it back, and then deletes it again. If the delete fails the check warns you and you delete that one contact by hand in HubSpot.
The studio lead sends: the `cd` line to the folder that holds `scripts/hubspot_probe.py`, and the NAME of the secret file that holds the key the run program will use (a name, never the key).
1. In WSL type the `cd` line. Then type `python -I scripts/hubspot_probe.py --plan` and Enter. You should see: "planned calls: 7 (hard budget 8 ...)". It calls nothing. Any other number: stop and tell the studio lead.
2. Type `export HUBSPOT_PROBE_TOKEN="$(cat <the secret file name>)"` and Enter. Nothing is shown (the key stays out of the screen; never type the key itself, and never write it in chat or in this sheet).
3. Type `python -I scripts/hubspot_probe.py --yes-spend-calls 7` and Enter. The number must be 7 (it must equal the planned count).
4. You should see a table of PASS/FAIL lines. From the script: lines such as "owners readable", "contact create", "owner write", "lead-status write", the read-back, and "delete". The script ends with exit code 0 only if every line says PASS or SKIPPED, else 1. What a pass looks like for THIS run: the studio lead tells you. Select the table text (it holds no key; the script never prints the key) and paste it to the studio lead. Type `echo $?` first and send the number too.
5. Type `unset HUBSPOT_PROBE_TOKEN` and Enter.
What the table tells the studio lead: the "delete" line says whether this key can delete a contact. "PASS (permanent)" or "PASS (normal delete: archived, not permanent)" means yes (the second also shows HubSpot keeps an archived copy). "FAIL" means the program's deletion at step F will fail after the sends, and leftover contacts must be deleted by hand; the studio lead then decides the next step. A different line failing (for example "lead-status write") shows a limit of the HubSpot plan; the studio lead tells you if it matters.
- Stop and tell the studio lead: the script prints "refused", or the table shows a warning about a contact that may still exist (delete that one contact by hand in HubSpot only after the studio lead names it).

### Step A. The written yes with numbers (you, once per paid run)
The studio lead sends one message with:
- at most 3 model calls in this run;
- the worst-case cost per call, and 3 times that figure;
- the money spent so far;
- the spending backstop and the stop time as they stand in the model settings file (`stage.env`), copied into the message by the studio lead, with the file's path; you may open that file in WSL to compare;
- the planned stop time 2026-11-23 18:29 UTC = 23:59 IST;
- that the rehearsal passed, with the name of its result file. (This is the studio lead's own gate; no plan names it. No rehearsal pass, no run.)

You answer in one line, for example: "Yes, run <run name>, up to 3 model calls and up to US$<the total in the message>, stop time 2026-11-23 23:59 IST." One yes covers ONE run. A message with no numbers: answer no.
You should see: the studio lead confirms it received your yes.

### Step B. Run-day laptop settings (you)
1. Plug the laptop into mains power.
2. Windows 11: Start, Settings, System, Power & battery, Screen, sleep & hibernate timeouts. For "plugged in", set "put my device to sleep after" to Never (path not checked).
3. Control Panel, Hardware and Sound, Power Options, "Choose what closing the lid does". For "When I close the lid", plugged in: Do nothing. Save changes (path not checked).
4. Close programs that show addresses or alerts.
5. After the last run set both back (step I.7).
You should see the new settings after you reopen each screen. If your screens differ, tell the studio lead what you see.

### Step C. Run day, before the studio lead says go (you)
1. **Receiver mailbox.** Open the receiver account in Gmail. In the left list click the label `demo` (if hidden, click "More") (path not checked). It must hold no mail. Click Inbox; it must be empty too. Tell the studio lead: "label and inbox empty". If the label holds mail, or you cannot find the label `demo`, tell the studio lead and do not start. (The program reads only the label `demo`. If the label is gone, the studio lead tells you what to do; you do not guess.)
2. **Browser profile (so the film is clean).** [Not in the studio lead's done-or-owner-only list: the studio lead confirms before you act.] In Chrome click your account picture at the top right, then "Add", then "Continue without an account", and name the profile `demo-take` (path not checked). If the profile already exists, use it. In that profile sign in only to the HubSpot test account and the receiver account (with the label `demo`). This is a Chrome profile, not a new account. Sign in to nothing else. Tell the studio lead: "profile ready".
3. **n8n sign-in, only if run card row 9 says so.** Your n8n account already exists and holds the HubSpot, Claude and Gmail connections (the connection list in the studio lead's notes does not match this one; not reconciled, open). So you do nothing in n8n unless the studio lead tells you that the n8n for this run is new. If it says so: sign in with your existing n8n account (never type the password into chat; keep it only where you keep your own passwords). If a screen asks you to type a connection value again, the studio lead sends the name of the secret file that holds it and the command to show it. Do this with no recording running and nobody watching: show the value in WSL, select it, copy, paste into the n8n field, then type `clear` in WSL. Tell the studio lead only: "done". If the studio lead offers an n8n screen as a film or proof screen, it will ask for this sign-in; if it does not ask, n8n is not filmed.
   - Stop and tell the studio lead: n8n shows a saved secret in clear text on screen or in an export.

### Step D. What the film may show (you, before the run and again on the finished footage)
[Not in the studio lead's done-or-owner-only list: the studio lead confirms before you act.] Who films, who starts the recording and who edits is on the run card (row 4). Until it is filled, no run starts.
Check in the `demo-take` profile that NONE of these shows an address other than the test addresses `take-<run name>-a@example.com`, `-b@` and `-c@`:
1. Receiver mailbox: do not click or hover your account picture. Do not open a mail or "show details". Look at the mail LIST only. If a list row shows another address (the sender column), tell the studio lead; the studio lead decides what is filmed.
2. Do not film the sender mailbox or its "Send mail as" settings.
3. Tab titles and the address bar, if they carry an address.
4. n8n's list of runs, only if n8n is a film or proof screen: only made-up names and test addresses, and no old run. Do not film the detail of the mail-sending step (it may show the company address and the sender address). Until the studio lead says that detail is safe, do not open it.
5. The proof screen: you choose it in step E from the screens the studio lead offers. It may show test addresses and counts only.
6. Terminal windows: no address in the prompt, history or settings output.
7. Mail notifications, desktop pop-ups, the system tray.
You should see only test addresses. Stop and tell the studio lead: any other address is visible. The footage is then cropped or retaken before any use.

## The run

### Step E. Start the run and type `y` (you, in your own terminal)
Have ready: WSL open, the `cd` line from the studio lead typed (you are in the run folder), the `demo-take` profile ready (C.2), laptop on mains, the written yes sent (A), run card complete. The studio lead sends you one line to run, of this form: `python scripts/run_real_check_n8n.py --take <run settings file>`. Type it, press Enter. The run name is in the run settings file, not in the command. You should see, in this order:
1. The program prints `mailbox login: still works` and `HubSpot login: still works`. A bad login stops the run here (exit code 2), before you type anything.
2. The notice, with a random 6-digit "Confirmation number (type it, a space and the take id)".
3. "Type y to start".
4. "Now type the confirmation number shown above, a space and the take id to confirm:".

Read the notice: 3 test people, up to 3 model calls and the worst case, up to 3 contacts deleted at the end, up to 3 mails (see "Send counts"), n8n stopped once. Compare the money figures with your written yes. If a number is not what you approved, type nothing and tell the studio lead.
- Type `y` and Enter **yourself**. A piped or scripted `y` is refused on purpose. Closed input ends the run with exit code 2 and nothing is sent. The flags `--yes` and `-y` do not exist.
- Then type the 6-digit number the notice showed (new every run), a space, your run name, and Enter. Example: `123456 <run name>`. An answer typed faster than the program's minimum (2 seconds unless the studio lead changed it; allowed 1 to 60) is refused with exit code 2. A wrong line ends the run with exit code 1 and nothing is sent.
- Pick a NEW run name for every run, also after a failed one. After both typed answers the program writes the marker file in the Linux home folder. See which run names are used with `ls ~/.hadavin-take-tags`.
- If a login line says anything other than "still works", nothing was sent. Tell the studio lead. Do not start again until the studio lead says so (repeated failed logins can trigger a Google sign-in alert).
- **How long it takes and when it is finished.** The run card (row 3) gives the normal length. The run is finished when the program prints its result and the `$` prompt comes back; then type `echo $?`. If nothing new prints for longer than the run card (row 12) says, tell the studio lead and wait; do not press Ctrl-C and do not close the terminal.
- During the run: contacts appear in HubSpot and mails appear in the label `demo`. n8n is stopped and started again once while person C is sent. Who types that is OPEN (run card row 5); planned by the earlier sheet: the studio lead does it from its own session. You touch nothing unless the card says you type a given line.
- Stop and tell the studio lead: a number in the notice is not what you approved; a count is wrong; the laptop sleeps.
- **The proof screen is your choice.** The studio lead offers candidate screens (the run card row 10). You pick one and say which. The studio lead says what it shows. The video must not show or claim any portal, approval step or audit trail.

> **WARNING before step F. When the program asks for `end`, closing the terminal, pressing Ctrl-C, or typing two wrong lines in a row ENDS the pause and DELETES the test contacts from HubSpot BEFORE they are filmed. A closed input on the FIRST prompt ends the pause at once. After the contacts are deleted they cannot be filmed, the money is already spent, and a new run needs a new yes (step A) and a new run name. Type exactly `end` (three letters, lower case), and only when the filming of the contact list is done.**

### Step F. The film pause: type `end` (you)
The program prints: "Film the contact list now: type `end` and press Enter to archive" (it means delete). The person who films (run card row 4) films the HubSpot contact list. To find this run's contacts in HubSpot: Contacts, then the search box, type your run name (path not checked). Type `end` and Enter yourself only when that person tells you the contact list is filmed (if you film, when you have filmed it). The program then deletes this run's contacts. Only the exact word `end` ends the pause. Any other line makes the program print "type exactly: end" and ask once more; a second wrong line also ends the pause and deletes the contacts.
You should see HubSpot show no contacts of this run afterwards, and the program print its result.
- Stop and tell the studio lead: you closed the terminal or pressed Ctrl-C early. Leftover contacts are deleted by hand in HubSpot; the studio lead gives you the count.
- If the HubSpot key the program uses cannot delete contacts (step 0 shows this before the run), the deletion fails after the sends and you delete the leftover contacts by hand in HubSpot.

> **WARNING before step G. In step G delete ONLY mails in the receiver account and ONLY HubSpot contacts of the failed run (the studio lead gives you the count and the run name). Never delete the marker file `~/.hadavin-take-tags/<run name>.used`.**

### Step G. If a run fails (you)
[Not in the studio lead's done-or-owner-only list: the studio lead confirms before you act.] The studio lead says why, by message. Then:
1. In the receiver Gmail open the label `demo` and the Inbox. Select only the demo mails (subject starts with `[demo] lead`). Click the Trash icon. Open Trash: it must hold only these demo mails. Then click "Empty Trash now" (path not checked). (This is "delete" in the Words box.)
2. In HubSpot, delete any leftover contacts the studio lead counted: Contacts, search your run name, tick them, More, Delete (path not checked). Delete only contacts whose name or address carries this run name.
3. Tell the studio lead: "demo mails deleted" and the number of contacts you deleted.
4. Give a NEW written yes with numbers (step A) and pick a NEW run name. A run that got past both typed answers has used its name even if it failed.
If the studio lead later says a new run is no longer possible before the stop time, no new run happens.

## After the run

### Step H. You watch the edited video
The studio lead tells you the deadline. Watch from the first second to the last: once at full speed, once pausing on each cut. No address may show except test addresses. Reply "accepted" or list the bad seconds with times. If any real address shows, say "an address is visible" and the second. Clean-up (I) starts only after you reply "accepted" and the studio lead says the last run is done. After clean-up starts, no further run happens.

> **WARNING before step I. The deletes in step I cannot be undone. Delete only what the studio lead's confirmed list names. Never delete `~/.hadavin-take-tags/<run name>.used`. Do not delete the secret files until the retire check has passed.**

### Step I. Clean-up (you, with the studio lead; deadline on the run card)
Starts when the studio lead says the last run is done. Order matters.
1. **Revoke the app passwords made for this run, in both accounts** (receiver and sender). The studio lead sends the list of app password names to revoke (the earlier plan named them `desk-read` and `desk-send`; the studio lead confirms the names). Go to myaccount.google.com, Security, App passwords (this needs 2-Step Verification, which is already on), click the bin or "Remove" next to each named one (path not checked). Take a screenshot of each empty list. Before saving, crop or cover any address that shows (account picture, name, address). To crop on Windows use the Snipping Tool: Start menu, type `Snipping`, Enter (path not checked).
2. **Delete the HubSpot private apps made for this run.** [Not in the studio lead's done-or-owner-only list: only do this after the studio lead confirms it is wanted.] First answer the studio lead's question: "Which private apps did you make for this run, and is the key the program used one of them, or a different key of the test account that stays?" Only you know. Look at each app's name and creation date in HubSpot (Settings, Integrations, Private Apps) (path not checked). If you cannot tell which one the program used, do not delete; tell the studio lead the app names. The studio lead names the secret file that holds the program's key, but no file maps to an app; that mapping is open. Deleting a private app cannot be undone; anything using its key (the program, n8n's HubSpot connection) stops working. Delete only after the studio lead confirms the list, then take a screenshot.
3. Save the screenshots in `C:\Users\<your-user>\Downloads\Hadavin\_local\real-run\` under the names the studio lead gives.
4. **Retire check.** The studio lead sends the exact command (form: `python scripts/run_real_check_n8n.py --retire-check <run settings file>`) and says which folder to type it in. Run it BEFORE the secret files are deleted, and while the run settings file still exists (the studio lead keeps the run settings file and the run folder until the check has passed; they are removed in item 5). It must print "refused as expected" for the mailbox and for HubSpot, exit code 0.
   - "STILL WORKS" (exit code 3): a key still works; revoke or delete it again (items 1 and 2) and rerun.
   - "could not tell" (exit code 2): the studio lead tells you when to rerun.
   - Keep the secret files until the check passes. See the exit code with `echo $?`.
5. Only after it passed, tell the studio lead "retire check passed". The studio lead (not you) then removes n8n's connections and saved runs (made-up data only), turns the saving of runs off, stops n8n, and removes the run folder and the database container. The retire check does not test the model key or the database passwords: the studio lead tells you whether the model key is cancelled by you, kept, or handled by the studio lead (open); do nothing about it until told.
6. Then delete the secret files in WSL. The studio lead sends the list of file names and the folder. Type `shred -u <the names, separated by spaces>`. If it says `shred: command not found`, type `rm <the same names>` instead. These deletes cannot be undone. Check with `ls -l` on the folder that the files are gone. Do NOT delete `~/.hadavin-take-tags/<run name>.used`.
7. Set laptop sleep and lid settings back. Sign out of the `demo-take` browser profile.
- The copy of the passwords inside n8n ends only by your revocation in item 1; you can only show that with a screenshot, not a check.

### Step J. Post (you; latest Wed 25 Nov 2026, 15:00 UTC = 20:30 IST)
You post; Claude never posts. The post says only: contacts arrive through n8n; n8n writes the HubSpot contact and sends the mail; our code asks the model once per test person, writes each paid call down before it is made, and counts the mails and contacts with a separate check of ours; **"the same lead id sent twice is processed once"** ("lead id" here is the number the system gives each test person when it sends them in).
It must NOT say:
- that the same person through two doors is one contact;
- that no contact data stays in n8n, or that recovery takes within 60 seconds, or that an alert comes within 30 seconds;
- that a portal, an approval step or an audit trail exists or shows these rows;
- that n8n cannot reach the internet (its outgoing traffic is switched off by settings and only watched, not blocked);
- that the run is crash-safe (unless the rehearsal's crash test passed);
- that the count is made with an independent login (until that login is built and shown to run);
- that everything is in one database (the aim is one Postgres program with n8n's data in its own database inside it; it is not proven until the re-smoke shows it; some files stay outside it);
- that the spend is capped by a hard limit (it is a setting a person checks).
The exact final words come from the studio lead after the rehearsal. Until you have them, do not post. Someone other than the author of the words checks the post against this list before you post (run card row 11 names who).

## What to send the studio lead (never a secret)

| When | Send |
|---|---|
| Before a run | your answer on the run date; the run name you picked (a word, no secret); "receiver and sender are the throwaway accounts"; the step 0 table and its exit code; your written yes with numbers (step A) |
| Run day | "label and inbox empty"; "profile ready"; "done" for n8n, only if asked; any problem line from step C |
| During a run | the exit code and the last printed line if the run stops; "closed the terminal early" if it happens; the proof screen you picked |
| After a run | "accepted" or the bad seconds; "an address is visible" if you see one |
| After a failed run | "demo mails deleted" and the number of contacts deleted; a new written yes |
| Clean-up | the names of the HubSpot private apps you made; the screenshots; the retire-check output (words and exit code only); "retire check passed"; "secret files deleted" |
| Before posting | the post text, for comparison with the final claim |

## Refusals and exit codes you may meet

Exit codes of the run program (step E):
- 0: pass.
- 1: your answer was not `y`, or the confirmation line did not match.
- 2: the program refused to start or to go on: a setting, a failed login check, no keyboard, closed input, an answer typed too fast, a run name or key used before, a lock file exists, the stop time too close, a second mailbox, Ctrl-C before the first send.
- 3: a count or verdict failed after the run, or Ctrl-C after the sends began ("interrupted after the sends began").
- Rare: a signal at the very end can turn a pass into exit 3 or leave the exit status as 120, and can leave the run lock file. If that happens, do not run again: tell the studio lead; it reads the result file the program wrote in the run folder.

Exit codes of the retire check (step I) are different:
- 0: both logins refused (good).
- 3: a login still works.
- 2: anything else ("could not tell").

Other refusals:
- **Run lock file:** if the program stops hard it may leave `take-<run name>.lock` beside the run folder; the next run with the same run name is refused. Delete it by hand ONLY when the studio lead says so.
- **Start deadline:** the program refuses to start unless it can finish about 14 minutes before the stop time. With stop time 18:29 UTC the latest start is before 18:14:40 UTC = 23:44:40 IST at the default setting. The studio lead gives the exact time.

## What is not proven yet (short; the full list is in the studio lead's file)

- The rehearsal is written and has NOT been run. The code has never run against a live Gmail, HubSpot or model call.
- Not shown: how Gmail applies the label to a mail sent from another Gmail account, and how fast; whether Gmail accepts the company address as the shown sender.
- Not shown: that n8n keeps its own records in the same Postgres as our table of test people (the aim), and that removing saved runs at clean-up works.
- Not shown: that a crash between sending the mail and noting it sends no second mail.
- The program does not check by itself: the alert mail, mail in any folder other than `demo`, the contact id read back from HubSpot (only checked to be all digits), the manual n8n stop and restart, and the hook door.
- Click paths marked "(path not checked)" were not checked on your accounts.
- Where records are kept: one Postgres for the run is the aim. Files outside it: `stage.journal` (the model program's log written before each model call), a spending record, lock files (the run lock, the model program's lock, the spending record's lock), the run-name marker file and `n8n.pid`.
