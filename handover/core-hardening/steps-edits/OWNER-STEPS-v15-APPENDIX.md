# Appendix to the owner's sheet, version 15 (sections the sheet names are part of your steps)

Written Mon 16 Nov 2026. UTC and IST (IST = UTC + 5:30). The sheet is `OWNER-STEPS-realrun-v15.md`, the card `OWNER-DAY-CARD-v15.md`. Nothing here changes a rule of the sheet. Sections: 1 More words, 2 Value list, 3 Messages, 4 Rule 10 in full, 5 Counts, masked form, sample result, 6 Order table, 7 What to send, 8 Post ban, 9 Refusals and lock file, 10 n8n stop and start, 11 Step T trial run, 12 Step G failed run and demo mails, 13 Retire check, 14 Film rules and shot list (step D), 15 Saving the model key (A.0), 16 Screenshots and erase tests, 17 For the studio lead: not proven, 18 Secrets table. Sections 11, 12, 14, 15, 16, 18 are owner steps: the sheet says when to read them. Nothing in this file was run by the writer.

## 1. More words
- **Program settings file**: the small file with one run's settings (run name, Gmail label to read, worst-case price per call); the studio lead prepares it; you never edit it. **Model settings file** (`stage.env`): the model program's settings (backstop, prices, model name, token limits, money stop); you never edit it or `cat` it; you print only named lines with `grep`. **Program folder**: the WSL folder of the program's files; the `cd` line comes from the studio lead and must equal row 12.
- **Accounts and keys behind the run** (receiver and sender Gmail with app passwords, HubSpot test account and key, n8n account) were made by you earlier (your statement of 2026-11-16); the sheet makes only the model key, and the probe key if blank B20 says so; row 22 asks whether the separate sender account exists.
- **Company address**: your Hadavin company address; it may appear as the "From" line; you do nothing with it. **Gmail filter**: a rule in the receiver that puts the demo mails under label `demo` (row 22). **App password**: a password Google makes for one program. **Marker file** `~/.hadavin-take-tags/<run name>.used` makes a run name unusable twice; never delete it. **Lock file** `take-<run name>.lock` stops a second run with the same name (section 9).
- **Notice**: the numbers screen before "Type y to start". **Printed result**: what the program prints after `end`. **"Unknown"**: the program could not tell whether person C got a contact and a mail. **Database**: where the program keeps its records (Postgres). **`mf_leads`**: the database table that records each handled test person (its person id is the key that makes a repeat visible). **Retire check**: the program command that tries the revoked logins (section 13). **n8n's saved executions**: records n8n keeps per handled test person; the studio lead removes them in I.5. **Database container**: the sealed box on this laptop that runs Postgres; the studio lead removes it.
- Three files never mixed: the **step 0 result file** (`~/hadavin-step0-result.txt`), the **rehearsal result file** (named by full path in the go message) and the **masked result file** of the real run (the studio lead reads only this).
- **Crash-safe**: no second mail after a crash between sending and noting it down. NOT shown; nothing may claim it. **Separate login / separate check**: not built; never claimed. **Portal**: a customer web page where people approve actions; unrelated to the HubSpot account number.
- Three lists: **value list** (section 2), **order table** (section 6), **result list** (the PASS, FAIL or NOT NEEDED lines of step 0). The word "table" means nothing else; a database table is called "the database" or by its name.

**Worked example** (all numbers invented). Input price US$3, output price US$15 per million tokens; worst case 40,000 tokens in and 10,000 out. Per call: (40,000 x 3 + 10,000 x 15) / 1,000,000 = 0.27. Run total with a ceiling of 3 calls: 3 x 0.27 = **US$0.81**. Balance US$25.00 (at least 0.81: ok). Ledger total printed: US$12.40, so the backstop may be at most 12.40 + 0.81 = **US$13.21** (the file says 13.00: ok; 13.50: answer no). Money used so far at the E reading: US$3.10. After the run: 3.90, an increase of 0.80 (not over 0.81: ok). If it read 4.00, the increase 0.90 is over: Emergency cancel.
**Price command** (digits and dots only): `python3 -I -c 'print((<tokens in> * <input price> + <tokens out> * <output price>) / 1000000)'`.

## 2. The value list (23 rows; no list, no run)
A go message needs all 23 rows (rows 8 and 9 print "not used" so numbers stay stable). The card holds the values of the rows it names. A row changes only by a new complete list. **Rows 4 to 7 and 15 name humans** (never an agent, a session, a script or a helper window); who may hold which of them is blank B23. Rows 20 and 21 "kept on purpose" count only with your written yes (reason, end date UTC and IST). A row on the card is filled with one value per underline.

| Row | The list holds | If missing |
|---|---|---|
| 1 | run date; how many days before it steps B to D start | ask |
| 2 | run name confirmed | ask |
| 3 | latest start (date and time, UTC and IST) = the earlier of the money stop and the cancel deadline on row 11, minus (normal run length + longest film pause on row 17 + the margin of blank B19, which is at least the program's own start margin); normal run length in minutes; lease length in seconds (read from the flow file at the program commit; one source). It is the only source of the latest start | ask |
| 4 | person who films (browser and mouse only; never the program window) | no run |
| 5 | person who starts the recording and says "recording" | no run |
| 6 | person who edits and crops | no run |
| 7 | person who says "filmed" | no run |
| 8 | "not used" (the studio lead shuts down and starts n8n itself; no owner step) | none |
| 9 | "not used" | none |
| 10 | trial run: yes or no (paid; its own yes); retake count: the studio lead computes it from the ledger code and the cost per run at re-pin (UNVERIFIED) | no trial |
| 11 | deadlines (UTC and IST): cancel the model key (I.0, the run day), watch the video (H), clean-up (I), latest post time | ask |
| 12 | paths: program folder, program settings file, model settings file and its setting names, secret folder and file names (which are n8n connection files, which is the model key file), the local flow copy file name | ask |
| 13 | the port of the take's own n8n (named once, here; never 5678 or 5679, which are your own n8n). You never open it | none |
| 14 | proof-screen candidates, numbered (pictures of counts only) | no proof screen |
| 15 | who checks the post text (a human; blank B23) | do not post |
| 16 | minutes with no new line before you tell the studio lead (longer than the longest silence the studio lead expects while it restarts n8n) | tell and wait |
| 17 | longest film pause in minutes | ask |
| 18 | I.3 cropped screenshots: yes or no | skip I.3 |
| 19 | step 0 and E data: folder of `hubspot_probe.py`; checksums of every file the program, the step 0 program and the flows use (every module imported, every flow file as imported and as activated) and of `scripts/run_real_check_n8n.py`; commit id; the HubSpot identities named separately with exact permission names: (1) the HubSpot key in n8n, which writes contacts, (2) the program's own HubSpot login (blank B15), (3) the probe key (file path, separate); number of calls `--plan` prints; the one host | no step 0 |
| 20 | each HubSpot key and private app listed separately (the probe app is deleted in 0.6) and each app password: deleted (private app) or revoked (app password), or kept (reason, end date) | delete nothing |
| 21 | model key: cancelled in I.0 after every paid run (default) or kept (reason, end date; a new key is made for every paid run) | cancel |
| 22 | yes or no for each: label `demo` and its Gmail filter; the separate sender Gmail account | no start |
| 23 | the model program's exact command line (letters, digits, `/ . _ -` only) as `ps` shows it | no start |

## 3. Messages
The studio lead sends only values: a date, a path, a number, a list of names, or a command line in exactly a form printed in the sheet. A message never changes rules 1 to 12, steps A, E, F, I, the money rule, the go list or the boxed warnings. If it asks for that, you answer no. A command line not in a printed form is not run. The studio lead shares your Linux user and promises to read only masked outputs of the run and never secret files or the real-run folders: its own working rule, not enforced by the laptop (accepted exposure, A.0).
**Step A message holds:** model name; tokens in and tokens out per call; both prices per million tokens; price page address; worst-case price per call; run total; the answers of blanks B8, B10 and B25 (before you make the key); model account address and the page that shows prepaid and auto-reload; that the account holds only this studio project's keys (money rule item 2); the highest balance you accept (B24); every setting name with its value (model name, token limits, prices, backstop, money stop); the **ledger total so far** and the sentence that the backstop counts against the ledger; masked sender and receiver and the second fact per Gmail account (B26); the HubSpot account name and last 4 digits; whether the notice prints the masked accounts; the real wording of the notice and printed result (B9); the rehearsal result file path and exact first line; the answer of step 0 or why it is not run; the statements for go items 4 and 5; the model program's command line (row 23); the key deadline (row 11); the **expected rise before E**; whether a per-key spending limit exists (page, amount) or that none exists; the call ceiling and whether the backstop refuses a fourth call; the alert-mail address (one of your two throwaway accounts); the command that prints the ledger total; the permission names (B7); the written plan for how the three connection values get into n8n (B1, B14); the exit-code rule (B2); the list **by name** of older model keys it thinks belong to this project (A.0b). Any change of one figure is a new message and needs a new typed yes.

## 4. Rule 10 in full
A path or name may hold only A-Z a-z 0-9 . _ / - and a full path starts `/home/`. A setting name matches only A-Z 0-9 `_` and holds none of KEY, TOKEN, SECRET, PASSWORD. Do not type, and tell the studio lead about, a VALUE it sends that holds: a space, a quote, `;`, `$`, a backtick, `|`, `&`, `<`, `>`, `(`, `)`, `*`, `?`, `~`, `\`, `..`, a leading `-`, a line break. (Lines printed in the sheet and card hold quotes, `$`, `<`, `>`, `|` where printed: only the values the studio lead sends are held to the list.) Before `shred` or `rm`: `ls -l "<path>"`, `readlink -f "<path>"`; any `->`, or a different path: stop; also `ls -ld "<secret folder>"`.

## 5. Counts, masked form, sample notice, sample result
**Counts.** A twice, B ten times at once, C once while n8n is shut down and started again: 13 submissions, all by the program. At the end A and B each have one contact and one mail; C one contact and one mail, or "unknown" (possibly no mail and an alert mail to an address the studio lead names; not tested). So 2 or 3 contacts and 2 or 3 mails; another count: tell the studio lead. The program does not check the alert mail. Contacts stay in HubSpot until you delete the listed ones by hand (card F.5). That A was sent twice with the same person id is shown only if the printed result says so (blank B9) or the studio lead names the file and line.
**Sample notice (INVENTED; the real wording is blank B9; compare numbers and names, not layout).**
```
  Run name: <run name>        People: 3   Model calls: <ceiling>   Mails: 3
  Price per call: <price>   Total: <run total>   Money stop (window end): 2026-11-23 18:29 UTC
  Sender: de…r@example.net   Receiver: de…r@example.net   Folder: /home/<user>/...
  Type y to start
```
If the real notice still says contacts will be "archived" or "deleted" at the end (the old desk program did), you type `n`; the studio lead then fixes the wording or states in writing that the line is old text and the go item 5 statement shows no delete or archive.
**Masked form.** First 2 letters, three dots, the last letter before `@`, then the domain: `demoreceiver@example.net` reads `de…r@example.net` (invented).
**Sample printed result (INVENTED; real wording unknown, blank B9; compare meaning).**
```
  Person A: sent 2 times, same person id: 1 contact, 1 mail   Person B: 1 contact, 1 mail
  Person C: unknown (could not tell whether it got a contact and a mail)
  Model calls made: 3              Submissions made: 13
  (an exit code line may follow; no value for C "unknown" is stated here)
```
No exit code for C "unknown" is stated anywhere in your files: the studio lead reads it from the program at the final head and writes the rule before the day (go item 7).

## 6. Order table
| No. | Who | What | Where | Expected |
|---|---|---|---|---|
| 1 | studio lead | value list and card | message | 23 rows, no underscore left |
| 2 | studio lead | clean start at take prep: fresh person ids; empties the take's table of handled people with the take database's admin role; database server and names (B3) | own session | "clean start done" |
| 3 | you | run name, proof-screen number | message | confirmed |
| 4 | studio lead | "go step 0" with your quoted yes and HubSpot account name, or why step 0 is not run | message | |
| 5 | you | step 0 | browser, WSL | PASS, FAIL or NOT NEEDED lines |
| 6 | studio lead | rehearsal; statements for go items 4 and 5 | message | before A.6 |
| 7 | you | A.0 exposure, key made (section 15); A.0b checks, old keys | model account, WSL | studio lead restarts model program |
| 8 | you | A.1 to A.6 | WSL, browser | acknowledged |
| 9 | you | B, C.1, C.2, D | Windows, Gmail, Chrome | "label and inbox empty"; "profile ready" |
| 10 | studio lead | go message for the run | message | |
| 11 | you | card: before E, E | WSL | "run started" |
| 12 | studio lead | shuts down and starts n8n with the take scripts (section 10) | own session | n8n down once, back while C is submitted |
| 13 | person on row 4 | films the contact list and mail list | browser | |
| 14 | you | F.1 to F.4: `end`, `echo $?`, usage page | WSL, browser | |
| 15 | studio lead | switches n8n off, writes "n8n is off"; sends the contact list | message | |
| 16 | you | F.5 delete listed contacts | HubSpot | "contacts deleted" |
| 17 | you | I.0 right after F.4, by the row 11 deadline, after every paid run | model account | "model key cancelled" |
| 18 | studio lead | shuts down the model program; "no more runs" | message | |
| 19 | you | H | player | "accepted" |
| 20 | you, studio lead | I.1 to I.7 | | |
| 21 | you | J | | "posted" |
| 22 | you | trial run (11) or step G (12) | | |

## 7. What to send (never a secret)
Before a run: run name; proof-screen number; written yes for step 0; "HubSpot is the test account"; step 0 lines and exit code, or filter counts; "I veto the exposure" only if so; the model key's name and path; decisions on older keys; the written yes with numbers; money figures; "receiver, sender and HubSpot are the throwaway accounts". Run day: "label and inbox empty"; "profile ready"; "refused at the notice"; "run started"; any problem line. End of a run: exit code, the last printed line in words, balance and money used before and after; "contacts deleted" and the number. After: "model key cancelled", the figures and key names left; "accepted" or bad seconds; "an address is visible". After a failed or trial run: "demo mails deleted" and contacts count; new yes and run name. Clean-up: names left alone or deleted; retire-check words and code; "secret files erased". Posting: "posted".

## 8. Post ban (the post, and every spoken or written word of the video: captions, voice-over, title, thumbnail, must NOT say)
1. that nothing can start or spend before your typed answers (the model program and flows start earlier with a live key; no closed gate exists); 2. that the same person through two doors is one contact; 3. that no contact data stays in n8n, that recovery takes within 60 seconds, or an alert within 30 seconds; 4. that a portal, approval step or audit trail exists, or that a person approves each action (the typed `y` and challenge are a start check, not an approval step); 5. that n8n cannot reach the internet; 6. that the run is crash-safe or no mail goes out twice after a crash; 7. that the count is made by a "separate check" or "separate login"; 8. that everything is in one database; 9. that the spend is capped by a hard limit (a setting a person checks); 10. that test data was "deleted permanently" or "erased", or that the program deletes or does not delete contacts unless the go item 5 statement and the printed result both show it; 11. any sentence about recovery after a crash, the lease or three tries, unless the studio lead approved that exact sentence in writing with the file and line it read and has told you the crash-test result; 12. anything about which permissions a part has; 13. "Postgres is the one store".
Two further lines, separate from the list: the caption **"one Postgres server, two databases"** is allowed only with the studio lead's written evidence (file and line, blank B3); a rehearsal picture carries the label "rehearsal, made-up data".
**The studio lead's candidate lease sentence (NOT APPROVED; not an owner step; blank B13).** "Recovery re-claims an unfinished lead whose lease (row 3) ran out, up to three tries in total including the first; a duplicate is skipped while the earlier record exists; a gap longer than the lease is not claimed." Facts it rests on, read from the flow files and not run (UNVERIFIED): the claim step stores the person id once and skips a repeat while the stored row exists, whatever the lease; the recovery flow takes a row that is not finished, whose lease is over and with fewer than three tries. The studio lead tells you the crash-test result before you post it, and until then you do not.

## 9. Refusals and lock file
The sheet names no exit code of the program except that 0 is the usual sign of success; the studio lead reads the program's own codes at the final head (blank B2) and writes the rule you follow. Reasons the program may refuse to start or go on (UNVERIFIED): a setting, a failed login check, no keyboard, closed input, an answer faster than it allows, a used run name or key, a lock file, the money stop too close, a second mailbox, Ctrl-C before the first submission. If the program is cut off at the very end its exit code may be a number the card does not list and the lock file may stay: do not run again. Any number other than 0 in a run: Freeze (card F.3), unless the studio lead's written rule names exactly that number for exactly that printed result.
> **WARNING before removing the lock file: it cannot be undone. Remove only the one file the studio lead names, after it says so.**
Lock file `take-<run name>.lock` beside the program folder: `ls -l`, `readlink -f` (must equal the path), compare with rule 10, then `rm -- "<path>"`. **Start deadline:** row 3 gives the latest start (date and time); it is the only source.

## 10. n8n shutdown and start (studio lead only)
You never stop or start n8n and never sign in to it. The studio lead does it with the take scripts `n8n_kill.py` (identity check on the process, no process number from any card) and `n8n_start.sh` (take branch, local only), against the take's own n8n port only (row 13), never your own n8n on ports 5678 or 5679. The program is meant to print cue lines for `y`, the challenge and `end` only; that it prints no extra cue is UNVERIFIED (the studio lead checks at re-pin). How the studio lead times the shutdown while person C is submitted is its own step, rehearsed before the card is sent. After F.4 the studio lead switches n8n off and writes "n8n is off" (blank B27) before it sends the F.5 list.

## 11. Step T. Trial run (owner step; only if row 10 says yes; happens BEFORE the real run)
A trial run is a real, paid run: its own written "yes step T" quoting why, its own `go trial run <run name>`, its own step A (new yes, new run name, A.0 to A.6, money rule redone), the boxed warnings of E and F. Nothing is filmed or posted; at F.1 you look at the contact list yourself, then type `end`; afterwards step G. The trial's money counts in the next A reading and in the ledger total. The model key is cancelled after the trial (I.0); the real run needs a new key, a new yes, a new run name and a fresh C.1. A new take after a real run is the same: new complete card, go message, run name, model key and yes.

## 12. Step G. Failed run, trial run, and demo mails of any run (owner step; the studio lead sends the counts)
> **WARNING. Delete ONLY demo mails in the receiver and ONLY HubSpot contacts of the failed or trial run (the studio lead gives count and run name). Check the account before each delete (Gmail: name and the second fact of blank B26; HubSpot: name and last 4 digits). If Trash holds anything else, do NOT empty it. Never erase the marker file.**
(1) Receiver Gmail: open label `demo` and Inbox; tick only the demo mails one by one (subject starts `[demo] lead`; "lead" is a made-up sales contact); never "Select all conversations"; Trash icon; open Trash: only those mails, else stop; "Empty Trash now". Never Archive. (2) HubSpot: delete leftover contacts as card F.5, only the counted ones on the studio lead's list. (3) Send "demo mails deleted" and the count. (4) New written yes and new run name. A run that got past both typed answers has used its name. C "unknown": the studio lead says whether a contact or alert mail may remain; until then delete only what it counted. No new run is possible after the money stop.

## 13. Retire check results (I.4; the printed words, not the exit code, decide)
| Prints | Row 20 says | You do |
|---|---|---|
| both "refused as expected" | any | send "retire check succeeded" |
| mailbox "STILL WORKS" (bad) | revoked | revoke again (I.1), run again |
| mailbox "STILL WORKS" | kept | counts only if HubSpot is refused; the studio lead says "succeeded, mailbox app password kept on purpose" |
| HubSpot "STILL WORKS" (bad) | deleted | delete the private app again (I.2), run again |
| HubSpot "STILL WORKS" | kept | counts only if the mailbox is refused; the studio lead says so |
| both kept | both | the studio lead writes "retire check not required: kept on purpose" with end date |
| "could not tell" | any | wait |
Cannot succeed (could not tell twice, a row missing): keep every secret file, remove nothing more; the studio lead writes what is left and the date to finish.

## 14. Step D and filming (owner step: read before the day)
**Check in the `demo-take` profile, and again on the finished video (H): no address except `take-<run name>-a@example.com`, `-b@`, `-c@`.** (1) Receiver mail LIST only: no clicking or hovering the account picture, no opened mail, no "show details"; a Gmail tab title may carry your address: crop. (2) Never the sender mailbox or "Send mail as" settings. (3) Tab titles and address bars. (4) The proof screen is made by the studio lead from the rehearsal (never a live table); counts only, fewest words, no address except test addresses, no account number; its caption reads "rehearsal, made-up data"; you film nothing for it. (5) Terminal windows: no address in prompt, history or settings output; `clear` first. (6) Notifications, pop-ups, system tray. (7) **Account numbers**: none in HubSpot's address bar or header or the account picture menus; the editor (row 6) crops the address bar from every frame; you check in H. (8) The HubSpot contact list: step 0's made-up contact must be gone (0.6). (9) Captions, voice-over, title and thumbnail follow section 8. (10) **The notice and the start line** show masked sender and receiver accounts (if the program does), the program settings file name and a Linux path: the editor (row 6) crops or cuts them from every frame; you check in H (also: no key text).
**Shot list (PROPOSED by the writer; the studio lead's run sheet has the real scenes).** Recording is OFF through steps A, step 0, every command that prints a file, and the whole of E.0. Recording ON after `clear`, just before the start line. S1 program window: start line, the notice (masked accounts and path cropped), `y`, confirmation line. S2 HubSpot contact list search at F.1 (row 4). S3 receiver mail LIST under label `demo` at F.1 (row 4). S4 printed result after `end`. Recording OFF before `echo $?`, the usage page, any key page and every settings output. n8n is not filmed.

## 15. Saving the model key (step A.0; owner step; every command UNVERIFIED)
1. **Before copying anything:** Windows Settings, System, Clipboard: switch off "Clipboard history" and "Sync across your devices" (labels unverified on Windows 11); switch off Windows Recall and every screen recorder (Game Bar capture too); nobody in the room or on a call can see your screen. Use your normal browser profile, not `demo-take`.
2. In the model account (address by hand, from the card; check the account name) create a key for this run only (a trial has its own key). If the step A message says a per-key spending limit exists, set it as the message says and check it shows; if it says none exists, do not call the key limited. The page shows the key once: this is the only time a key is on your screen on purpose. Copy it with the page's copy button, then close the page (page labels unverified; the studio lead gives the page names in the step A message; if you cannot find the key list: Freeze).
3. In WSL `echo $BASH_VERSION` prints a version (else stop). Type, with `<model key file>` the full path from row 12 and the file form the studio lead states (key alone on its line, or `NAME=` before it): `( set -C; umask 077; read -rs -p 'paste key, Enter: ' K; printf '%s\n' "$K" > "<model key file>" ); echo "exit $?"`. For the `NAME=` form the studio lead sends the same line with `printf '%s\n' "NAME=$K"`; type that line only if it is in a message and rule 10 passes. Paste with a right-click only after the prompt `paste key, Enter:` is on screen, then Enter. Nothing shows; `set -C` refuses to overwrite (exit not 0: stop; never overwrite an older key file).
4. Check: `ls -l "<model key file>"` starts `-rw-------`; `wc -c "<model key file>"` shows 20 or more. Then copy a harmless word (this overwrites the clipboard).
5. **Paste empty or short:** the key is still on the browser page: copy it again, `rm -- "<model key file>"` (after rule 10 checks; it holds nothing valid), repeat step 3. Page closed: cancel that key and make another.
6. The key passes through the clipboard and browser; the studio lead shares your Linux user (accepted exposure, A.0), so the guard is that the key is yours, for one run, and cancelled in I.0 by its deadline (limited only if step A said a limit exists).
7. **Check the model program (A.0b, go item 6)**, in WSL (UNVERIFIED): `ls -l --time-style=full-iso "<model settings file>" "<model key file>"`, `ps -o pid=,lstart=,args= -p <process number>`, `pgrep -af "<model program name from row 23>"`, `date`. Needed: `ps` shows that process number and the command line written on row 23; `pgrep` prints exactly one line; the start time is later than both file times; `date` is within the clock tolerance (blank B21) of the Windows clock (WSL can drift after sleep). Example: the files changed one after the other and the program started after both: passes; started before the later file change: fails.

## 16. Screenshots (I.3) and the erase tests (I.6)
**Erase tests (I.6):** each path starts with the secret folder of row 12 (the flow copy: with the program folder of row 12), ends in a name listed on row 12, does not end `.used`, is not the program settings file, is not kept on purpose; the model key file only after I.0.
**Screenshots (only if row 18 says yes).** After I.1 and I.2, one screenshot of each list, cropping any address or name (Snipping Tool: Start, type `Snipping`). Save in `C:\Users\<your Windows user name>\Downloads\Hadavin_local\real-run\` (the user name is the folder under `C:\Users`) under the names the studio lead gives. Delete the uncropped originals the same day (Pictures, `Screenshots`) and empty the Recycle Bin (and OneDrive's).

## 17. For the studio lead: not proven, and open answers
**Not proven (nothing in the sheet, card or here was run):** all new commands (`ls -l --time-style=full-iso`, `ps -o pid=,lstart=,args=`, `pgrep -af`, `read -rs`, `set -C`, `wc -c`, `python3 -I -c`) are standard but UNVERIFIED on this laptop. The rehearsal is written, not run; the code never ran against live Gmail, HubSpot or a model call; the loopback re-smoke is "real-v5 minus one node" (the HubSpot contact step is a stand-in); never call it "real run passed". The row 19 commit is a provisional head on a local-only branch: checksums prove only equality with the card. Not shown: that nothing can spend before both typed answers (no closed gate; the fallback "the studio lead switches on flows after the typed `y`" is not accepted); that the program prints the masked accounts on the notice; how it ends the film pause (blank B11); that it runs under `python3 -I`; that no extra stop cue is printed; that it accepts the key file form; that the start time and key file times prove which key loaded; that the settings file is not re-read after start. The flow-copy contents (blank B8): another session read from files that the real flows use only the three settings `DESK_URL`, `DESK_TIMEOUT_MS` and `DESK_ALERT_TO` plus six placeholders (ids and addresses, no key); not verified here; the file is treated as secret until the studio lead states it with file and line.
**Inputs that disagree (the studio lead owns them; I may not edit inputs):** the scope sheet section 3 should read "no delete call exists in the take program; leftovers are listed; you delete by hand" (its older text about archiving describes the old desk harness); the one-store input still says "ONE database" (the studio lead's wording is "one Postgres server with two databases"). Figures: the notes name US$180 and US$189; which is the backstop and which the credit is not clear and neither is used in the sheet.
**Open items:** numbered B1 to B29 in the sheet; each is listed with its missing input in `v15-OPEN-FOR-LEAD.md`.

## 18. Secrets table (owner steps; one line per secret; no value is ever sent or filmed)
| Secret | Made | Kept in | Read by | Ends by |
|---|---|---|---|---|
| Model key | you, model account page, A.0 (shown once) | model key file (row 12) | the model program; the studio lead can read it (accepted exposure, A.0) | you cancel it, I.0, by the row 11 deadline; file erased I.6 |
| Probe key | where it comes from: blank B20 | probe key file (row 19) | step 0 program, only in the 0.4 command | you delete the probe app and erase the file, 0.6 (also if step 0 stops) |
| HubSpot key (n8n) | you, private app in the HubSpot test account | n8n's connection (put in as blank B1 says) and its file (row 12) | n8n | you delete the private app, I.2 (unless row 20 keeps it), by the clean-up deadline (row 11); file erased I.6 |
| The program's own HubSpot login | blank B15: the same key as the HubSpot key in n8n, or a separate one | its file (row 12), if separate | the program (it prints "HubSpot login: still works") | same deadline; if separate, its own row on 20 |
| Postgres app-role value | blank B14 | n8n's connection (as B1 says) | n8n | the studio lead removes it with the database container, I.5 |
| Receiver app password | you, receiver Gmail, Security, App passwords | secret file (row 12) | the program (to read mails); n8n does not hold it | you revoke it, I.1, by the clean-up deadline; file erased I.6 |
| Sender app password | you, sender Gmail | n8n's connection and its file (row 12) | n8n | you revoke it, I.1, by the clean-up deadline; file erased I.6 |
A key or password on screen any other time: Key exposed. The retire check (I.4) shows whether the revoked logins are refused.
