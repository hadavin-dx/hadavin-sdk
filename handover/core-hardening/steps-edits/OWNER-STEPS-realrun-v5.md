# Your steps for the recording run of the lead desk video (version 5)

Written Mon 16 Nov 2026 from version 4 and the two reviews of it. Nothing was run to write this sheet. If the studio lead's current instructions differ from this sheet, the studio lead's instructions win; ask before you act.

This sheet lists only what ONLY YOU can do. Things you already did are left out on purpose: the two throwaway Gmail accounts, the HubSpot test account and its keys, your n8n account, the model key and its credits, putting the n8n workflows on the public code site, and your general go-ahead for the recording run "once everything is ready". Do not redo them. The studio lead does the rest (database, model program, n8n, importing the workflows, the rehearsal and the checks). The studio lead's own to-do list is in a separate file, not here.

## Words box (read once; every word below keeps one meaning)

- **The studio lead**: the Claude session that works with you. It is software. You never see its screen, and it never sees yours. Every value it needs you to know arrives as a message from it or as a named file. Where a step says "the studio lead tells you", a message is coming; if none has come, do nothing and ask.
- **The recording run**: the one run you film, on your throwaway accounts. It uses 3 made-up people. "Run" means only this.
- **Test person**: one made-up person. The recording run makes three: A, B and C. Their addresses are **test addresses** of the form `take-<run name>-a@example.com`, `-b@` and `-c@`. Nothing is ever really sent to an `example.com` address; the studio lead explains how the mails reach the receiver (open question in the lead's file).
- **Send counts**: person A is sent in twice, B ten times at once, C once while n8n is stopped and started again. That is 13 sends in. The system must treat each person once, so you should see exactly 3 contacts and 3 mails (one per test person), not 13.
- **Run name**: a short word you invent for each run and never use again. It is typed at the confirmation line (step E) and is NOT part of the command. The program's screens call it "take id". The studio lead tells you the pattern (a word plus 4 digits is likely, not confirmed). Whether the studio lead also needs it earlier is open; if so the studio lead asks you to send it.
- **Settings file**: the small file with the settings for one run. The studio lead prepares it and tells you its path. You never edit it. The command you run points at it (`--take <settings file>`).
- **Run folder**: the folder in WSL that holds the run's files. The studio lead sends you the exact `cd` line to type to go into it.
- **WSL**: the Ubuntu terminal inside Windows. To open it: Windows Start menu, type `Ubuntu`, press Enter. The prompt ends with `$`. `~` means your Linux home folder.
- **Stop time**: the time after which the run may not spend money or start. The program's screens call it "window end". Planned: 2026-11-23 18:29 UTC = 23:59 IST (Mon 23 Nov 2026). The program refuses a start that is too close to it (it needs about 14 minutes), so the latest start is before about 18:15 UTC = 23:45 IST; the studio lead gives you the exact latest start time.
- **Secret files**: the files in your WSL home folder that hold the app passwords and keys for this run. You made them. Nobody else opens them. The studio lead tells you their names.
- **App password**: a password Google makes for one program. **Private app (HubSpot)**: a named access setup in the HubSpot test account; each has a key (token).
- **Key**: only a secret (a password, an app password, a token). It never means an id or an address.
- **n8n**: the tool that takes the test people in, writes the HubSpot contact and sends the mail. **Workflows**: the saved step chains inside n8n. **Hook door**: a second web address n8n listens on; the program does not check it.
- **Postgres**: the database program that stores the table of test people. It runs in a Docker container on this laptop.
- **The program**: the checking program you start in WSL (`scripts/run_real_check_n8n.py`). **The model program**: a small program of ours that asks the AI model once per test person.
- **Receiver**: the throwaway Gmail account that only receives the demo mails. **Sender**: the throwaway Gmail account n8n sends from.
- **The notice**: the screen of numbers the program prints before it asks you to type `y`.
- **Rehearsal**: a practice run on this laptop with stand-in programs, made-up data, no live account, no key and no model call. It costs US$0. The studio lead runs it; you do nothing. **Trial run**: a practice run on your throwaway accounts. Whether one happens is open (see the lead's file); until told, none happens.
- **Marker file**: `~/.hadavin-take-tags/<run name>.used`. The program makes it so a run name cannot be used twice. You never delete or edit it.
- **Run lock file**: a file ending in `.lock` beside the run folder (the studio lead tells you the exact name). It tells the program that a run is going.
- **Retire check**: a program command that tries to log in with the keys you cancelled and must be refused (step I).
- **Exit code**: a number the program leaves behind when it ends. To see it, type `echo $?` and Enter in the same terminal right after the program ends, before any other command. 0 means success.
- **Delete**: make it gone for good. Used for: HubSpot contacts, HubSpot private apps, secret files, and demo mails (move to Trash, then empty Trash). The program's own screens say "archive" for the contact deletion; it means delete. HubSpot may keep a recoverable copy for some time; the studio lead has not checked how long (open). **Archive**: only Gmail's own Archive button. This sheet never uses it. **Revoke**: cancel an app password so it stops working (the Google button is named "Remove"). This sheet uses no other word for these three acts.
- **Browser profile**: a Chrome user profile (the round picture top right), never a Gmail menu.
- **Edited video**: the finished video file you watch in step H.
- **Live accounts**: your throwaway Gmail accounts and the HubSpot test account. Made-up data in them is still made up.

## Order of the day

1. A: the studio lead sends the numbers; you answer with a written yes.
2. B: laptop settings.
3. C: check the receiver mailbox, make the browser profile, n8n sign-in only if asked.
4. D: check what the film may show.
5. E: start the run; you type `y` and the confirmation line.
6. F: the film pause; you type `end` only when filming of the contact list is done.
7. After the run: G (only if it failed), H (watch the edited video), I (clean-up), J (post).

**Date:** the studio lead gives the run date. Until it does, do nothing. Fixed times: stop time 18:29 UTC = 23:59 IST on Mon 23 Nov 2026. The stop time limits only the start and the spending of the run. Watching (H) and clean-up (I) have their own deadlines, which the studio lead gives you (open); they are not tied to the stop time. The post is planned for Wed 25 Nov 2026, 15:00 UTC = 20:30 IST.

## What the run can cost

- The run makes at most 3 paid model calls (one per test person). The model program writes down each call before it is made, so one test person is never paid for twice.
- The worst-case price per call: **the studio lead gives you the number before you say yes.** The total is 3 times that number. Your written yes names that total.
- The program does NOT enforce a dollar ceiling. A spending backstop and the stop time sit in a settings file that a person checks (you do not enforce them either). If a number looks wrong to you, answer no.
- A failed run still costs what it spent. Every new run needs its own yes (step A), with the money spent so far shown.

## Rules that hold in every step

1. **Never send the studio lead** a password, token, key, mailbox address or the contents of any secret file. Short sentences only. A file path is fine.
2. **The typed answers are yours alone:** the `y`, the 6-digit number with the run name, and `end`. The 6-digit number only blocks blind and piped answers. A tool that reads the screen and types the number back still passes. So never let a tool, script, assistant, agent or helper window type for you. Run the program only on your laptop, in your own terminal.
3. **Before every paid run you give a written yes WITH numbers** (step A). Your earlier go-ahead "once everything is ready" is a general go-ahead; it is not that yes, and the written yes does not exist yet. No numbers, no run.
4. **You post. Claude never posts.**
5. **Never point the run at your real company mailbox.** It uses only the throwaway receiver and sender.
6. On run days: laptop on mains power, sleep Never, lid close = Do nothing (step B). Set both back after the last run.
7. **Words you type that delete things** are listed in a boxed line right above the step. Read the box first.

## Before the run

### Step A. The written yes with numbers (you, once per paid run)
The studio lead sends one message with:
- at most 3 model calls in this run;
- the worst-case cost per call, and 3 times that figure;
- the money spent so far;
- the spending backstop and the stop time as they stand in the settings file `stage.env` in the run folder, copied into the message by the studio lead, with the file's path; you may open that file in WSL yourself to compare;
- the planned stop time 2026-11-23 18:29 UTC = 23:59 IST;
- that the rehearsal passed, with the name of its result file. No rehearsal pass, no run.

You answer in one line, for example: "Yes, run <run name>, up to 3 model calls and up to US$<the total in the message>, stop time 2026-11-23 23:59 IST." One yes covers ONE run. A message with no numbers: answer no.
You should see: the studio lead confirms it received your yes.

### Step B. Run-day laptop settings (you)
1. Plug the laptop into mains power.
2. Windows 11: Start, Settings, System, Power & battery, Screen, sleep & hibernate timeouts. For "plugged in", set "put my device to sleep after" to Never.
3. Control Panel, Hardware and Sound, Power Options, "Choose what closing the lid does". For "When I close the lid", plugged in: Do nothing. Save changes.
4. Close programs that show addresses or alerts.
5. After the last run set both back.
You should see the new settings after you reopen each screen. If your screens differ, tell the studio lead what you see.

### Step C. Run day, before the studio lead says go (you)
1. **Receiver mailbox.** Open the receiver account in Gmail. In the left list click the label `demo` (if hidden, click "More"). It must hold no mail. Click Inbox; it must be empty too. Tell the studio lead: "label and inbox empty". If the label holds mail, or you cannot find the label `demo`, tell the studio lead and do not start. (The program reads only the label `demo`. You made the label during set-up; if it is gone, the studio lead tells you what to do.)
2. **Browser profile (so the film is clean).** In Chrome click your account picture at the top right, then "Add", then "Continue without an account", and name the profile `demo-take`. In that profile sign in only to the HubSpot test account and the receiver account (with the label `demo`). Sign in to nothing else. Tell the studio lead: "profile ready". If a screen differs from these clicks, stop and tell the studio lead what you see.
3. **n8n, only if the studio lead asks.** The run starts with a new, empty n8n database. So n8n may show a first-visit screen asking you to create an owner login, and the three connections (HubSpot, mail sending, database) may have to be typed again. The studio lead sends you the n8n address and, per connection, the name of the secret file that holds its value and the command to show it. Do this with no recording running and nobody watching: show the value in WSL, select it, copy, paste into the n8n field, then type `clear` in WSL. Choose a new n8n password; never type it into chat. Then sign in to n8n in the `demo-take` profile. Tell the studio lead only: "done". If the studio lead does not ask, do nothing here and do not open n8n.
   - Stop and tell the studio lead: n8n shows a saved secret in clear text on screen or in an export.

### Step D. What the film may show (you, before the run and again on the finished footage)
Who films, who starts the recording, and who edits is set by the studio lead before the run (open). Until told, no run starts.
Check in the `demo-take` profile that NONE of these shows an address other than the test addresses `take-<run name>-a@example.com`, `-b@` and `-c@`:
1. Receiver mailbox: do not click or hover your account picture. Do not open a mail or "show details". Look at the mail LIST only. If a list row shows another address (the sender column), tell the studio lead; the studio lead decides what is filmed.
2. Do not film the sender mailbox or its "Send mail as" settings.
3. Tab titles and the address bar, if they carry an address.
4. n8n's list of runs: only made-up names and test addresses, and no old run. Do not film the detail of the mail-sending step (it may show the company address and the sender address). Until the studio lead says that detail is safe, do not open it.
5. The proof screen: you choose it in step E from the screens the studio lead offers. It may show test addresses and counts only.
6. Terminal windows: no address in the prompt, history or settings output.
7. Mail notifications, desktop pop-ups, the system tray.
You should see only test addresses. Stop and tell the studio lead: any other address is visible. The footage is then cropped or retaken before any use.

## The run

### Step E. Start the run and type `y` (you, in your own terminal)
Have ready: WSL open, the `cd` line from the studio lead typed (you are in the run folder), the `demo-take` profile ready (C.2), laptop on mains, the written yes sent (A). The studio lead sends you one line to run, of this form: `python scripts/run_real_check_n8n.py --take <settings file>`. Type it, press Enter. You should see, in this order:
1. The program prints `mailbox login: still works` and `HubSpot login: still works`. A bad login stops the run here, before you type anything.
2. The notice, with a random 6-digit "Confirmation number (type it, a space and the take id)".
3. "Type y to start".
4. "Now type the confirmation number shown above, a space and the take id to confirm:".

Read the notice: 3 test people, up to 3 model calls and the worst case, up to 3 contacts deleted at the end, up to 3 mails (one per test person; see "Send counts"), n8n stopped once. Compare the money figures with your written yes. If a number is not what you approved, type nothing and tell the studio lead.
- Type `y` and Enter **yourself**. A piped or scripted `y` is refused on purpose. Closed input ends the run with exit code 2 and nothing is sent. The flags `--yes` and `-y` do not exist.
- Then type the 6-digit number the notice showed (new every run), a space, your run name, and Enter. Example: `123456 <run name>`. An answer typed in under 2 seconds is refused. A wrong line ends the run with nothing sent.
- Pick a NEW run name for every run, also after a failed one. After both typed answers the program writes the marker file in the Linux home folder. See which run names are used with `ls ~/.hadavin-take-tags`.
- If a login line says anything other than "still works", nothing was sent. Tell the studio lead. Do not start again until the studio lead says so (repeated failed logins can trigger a Google sign-in alert).
- **Exit codes of the run program** (see step "Refusals and exit codes" below). Tell the studio lead the number and the last line printed.
- During the run: contacts appear in HubSpot and one mail per test person appears in the label `demo`. The studio lead's session stops and restarts n8n while person C is sent (who types the stop command is open in the lead's file). You touch nothing.
- Stop and tell the studio lead: a number in the notice is not what you approved; a count is wrong; the laptop sleeps.
- **The proof screen is your choice.** The studio lead offers candidate screens (n8n's list of runs, the rows of the people table, HubSpot, Gmail). You pick one and say which. The studio lead says what it shows. The video must not show or claim any portal, approval step or audit trail.

> **WARNING before step F. When the program asks for `end`, closing the terminal, pressing Ctrl-C, or typing two wrong words in a row ENDS the pause and DELETES the test contacts from HubSpot BEFORE they are filmed. Type exactly `end` (three letters, lower case), and only when the filming of the contact list is done.**

### Step F. The film pause: type `end` (you)
The program prints: "Film the contact list now: type `end` and press Enter to archive" (it means delete). The person who films (set before the run) films the HubSpot contact list. Type `end` and Enter yourself only when that person tells you the contact list is filmed (if you film, when you have filmed it). The program then deletes this run's contacts. Only the exact word `end` ends the pause. Any other line makes the program print "type exactly: end" and ask once more; a second wrong line also ends the pause and deletes the contacts. Closed input on the first prompt ends the pause at once.
You should see HubSpot show no contacts of this run afterwards, and the program print its result.
- Stop and tell the studio lead: you closed the terminal or pressed Ctrl-C early. Leftover contacts are deleted by hand in HubSpot; the studio lead gives you the count.
- If the HubSpot key the program uses cannot delete contacts, the deletion can fail after the sends. Unless the studio lead tells you otherwise, expect to delete leftover contacts by hand in HubSpot (open in the lead's file).

> **WARNING before step G. In step G delete ONLY mails in the receiver account and ONLY HubSpot contacts of the failed run (the studio lead gives you the count and the run name). Never delete the marker file `~/.hadavin-take-tags/<run name>.used`.**

### Step G. If a run fails (you)
The studio lead says why, by message. Then:
1. In the receiver Gmail, select the demo mails in the label `demo` and in the Inbox, click the Trash icon, open Trash, click "Empty Trash now". (This is "delete" in the Words box.)
2. In HubSpot, delete any leftover contacts the studio lead counted: Contacts, tick them, More, Delete. Delete only contacts whose name or address carries this run name.
3. Tell the studio lead: "demo mails deleted" and the number of contacts you deleted.
4. Give a NEW written yes with numbers (step A) and pick a NEW run name. A run that got past both typed answers has used its name even if it failed.
If the studio lead later says a new run is no longer possible before the stop time, no new run happens.

## After the run

### Step H. You watch the edited video
The studio lead tells you the deadline. Watch from the first second to the last: once at full speed, once pausing on each cut. No address may show except test addresses. Reply "accepted" or list the bad seconds with times. If any real address shows, say "an address is visible" and the second. Clean-up (I) starts only after you reply "accepted" and the studio lead says the last run is done. After clean-up starts, no further run happens.

> **WARNING before step I. The deletes in step I cannot be undone. Delete only what the studio lead's confirmed list names. Never delete `~/.hadavin-take-tags/<run name>.used`. Do not delete the secret files until the retire check has passed.**

### Step I. Clean-up (you, with the studio lead; deadline from the studio lead)
Starts when the studio lead says the last run is done. Order matters.
1. **Revoke the app passwords made for this run, in both accounts** (receiver and sender): myaccount.google.com, Security, App passwords, click the bin or "Remove" next to each. Take a screenshot of each empty list. Before saving, crop or cover any address that shows (account picture, name, address).
2. **Delete the HubSpot private apps made for this run.** First answer the studio lead's question: "Which private apps did you make for this run, and is the key the program used one of them, or a different key of the test account that stays?" Only you know. Look at each app's name and creation date in HubSpot (Settings, Integrations, Private Apps). If you cannot tell which one the program used, do not delete; tell the studio lead the app names. Deleting a private app cannot be undone; anything using its key (the program, n8n's HubSpot connection) stops working. Delete only after the studio lead confirms the list, then take a screenshot.
3. Save the screenshots in `C:\Users\<your-user>\Downloads\Hadavin\_local\real-run\` under the names the studio lead gives.
4. **Retire check.** The studio lead sends the exact command (form: `python scripts/run_real_check_n8n.py --retire-check <settings file>`) and says which folder to type it in. Run it BEFORE the secret files are deleted, and while the settings file still exists (the studio lead keeps the settings file and the run folder until the check has passed; they are removed in step 6). It must print "refused as expected" for the mailbox and for HubSpot, exit code 0.
   - "STILL WORKS" (exit code 3): a key still works; revoke or delete it again (steps 1 and 2) and rerun.
   - "could not tell" (exit code 2): the studio lead tells you when to rerun.
   - Keep the secret files until the check passes. See the exit code with `echo $?`.
5. Only after it passed, tell the studio lead "retire check passed". The studio lead then removes n8n's connections and saved runs (made-up data only) from n8n, turns the saving of executions off, stops n8n, and removes the run folder and the database container.
6. Then delete the secret files in WSL. The studio lead sends the list of file names. Type `shred -u <the names, separated by spaces>`. If it says `shred: command not found`, type `rm <the same names>` instead. These deletes cannot be undone. Check with `ls -l` on the folder (the studio lead gives the folder) that the files are gone. Do NOT delete `~/.hadavin-take-tags/<run name>.used`.
7. Set laptop sleep and lid settings back. Sign out of the `demo-take` browser profile.
- The copy of the passwords inside n8n ends only by your revocation in step 1; you can only show that with a screenshot, not a check.

### Step J. Post on Wed 25 Nov 2026, 15:00 UTC = 20:30 IST (you)
You post; Claude never posts. The post says only: contacts arrive through n8n; n8n writes the HubSpot contact and sends the mail; our code caps the spend, asks the model once per test person, and counts the mails and contacts with a separate check of ours; **"the same lead id sent twice is processed once"** ("lead id" here is the number the system gives each test person when it sends them in).
It must NOT say:
- that the same person through two doors is one contact;
- that no contact data stays in n8n, or that recovery takes within 60 seconds, or that an alert comes within 30 seconds;
- that a portal, an approval step or an audit trail exists or shows these rows;
- that n8n cannot reach the internet (its outgoing traffic is switched off by settings and only watched, not blocked);
- that the run is crash-safe (unless the rehearsal's crash test passed);
- that the count is made with an independent login (until that login is built and shown to run).
The exact final words come from the studio lead after the rehearsal. Until you have them, do not post. Someone other than the author of the words should check the post against this list before you post (the studio lead names who).

## What to send the studio lead (never a secret)

| When | Send |
|---|---|
| Before a run | your answer on the run date; the run name you picked (a word, no secret); your written yes with numbers (step A) |
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
- 2: the program refused to start or to go on (a setting, no keyboard, closed input, too fast, a run name used before, a lock file exists, the stop time too close).
- 3: a count or verdict failed after the run.

Exit codes of the retire check (step I) are different:
- 0: both logins refused (good).
- 3: a login still works.
- 2: anything else ("could not tell").

Other refusals:
- **Run lock file:** if the program stops hard it may leave a `.lock` file beside the run folder; the next run with the same name is refused. Delete it by hand ONLY when the studio lead says so.
- **Start deadline:** the program refuses to start unless it can finish about 14 minutes before the stop time. With stop time 18:29 UTC, the latest start is before about 18:15 UTC (23:45 IST). The studio lead gives the exact time.

## What is not proven yet (plain words)

- The rehearsal is written and has NOT been run. No evidence for it exists yet.
- The code has never run against a live Gmail, HubSpot or model call. It ran once against a real n8n with stand-in programs for everything else (that first run left items open).
- Not yet shown: how Gmail applies the label to a mail sent from another Gmail account, and how fast; whether the program sees the label `demo` as a folder named `demo`; whether Gmail accepts the company address as the shown sender without a "mailed-by" line (a line in the mail header saying which account really sent it).
- Not yet shown: that n8n keeps its own records in the same Postgres as our table of test people (the aim; in the first run it used its default file database), and that removing saved runs at clean-up works.
- Not yet shown: that a crash between sending the mail and noting it in the table sends no second mail.
- The program does not check by itself: the alert mail, mail in any folder other than `demo`, the contact id read back from HubSpot (only checked to be all digits), the manual n8n stop and restart, and the hook door.
- Click paths in Google, HubSpot, Chrome, Windows and n8n were not checked on your accounts. If a screen differs from a step, stop and tell the studio lead what you see.
- Your written yes with numbers does not exist yet. No paid run happens without it.
- Where records are kept: the aim is one database for the run (its Postgres, shared by n8n and our table of test people). One small file in the run folder (`stage.journal`, a log the model program writes before each model call) is the one stated exception. Some other bookkeeping files exist outside the database (a spending record, lock files, the run-name marker file).
