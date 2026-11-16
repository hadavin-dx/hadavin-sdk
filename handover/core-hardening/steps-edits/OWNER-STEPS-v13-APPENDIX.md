# Appendix to the owner's sheet, version 13 (for the studio lead; sections the sheet names are part of the owner's steps)

Written Mon 16 Nov 2026. UTC and IST (IST = UTC + 5:30). The sheet is `OWNER-STEPS-realrun-v13.md`, the day card `OWNER-DAY-CARD-v13.md`. Nothing here changes a rule of the sheet. Sections: 1 More words, 2 Run card, 3 Messages, 4 Rule 10 in full, 5 Counts, masked form, sample result, 6 Order table, 7 What to send, 8 Post ban, 9 Exit codes and refusals, 10 n8n stop and start, 11 Step T trial run, 12 Step G failed run, 13 Retire check, 14 Film rules and shot list (step D), 15 Saving the model key (A.0), 16 Screenshots (I.3), 17 For the studio lead: what is not proven, and open answers. Sections 11, 12, 14, 15, 16 are owner steps: the sheet says when to read them. Nothing in this file was run by the writer.

## 1. More words
- **Run settings file**: the small file with one run's settings (run name, Gmail label to read, worst-case price per call); the studio lead prepares it; you never edit it. **Model settings file** (`stage.env`): the model program's settings (backstop, prices, model name, token limits, window end); you never edit it or `cat` it; you print only named lines with `grep`. **Run folder**: the WSL folder of the run's files; the `cd` line comes from the studio lead and must equal row 12.
- **Accounts and keys behind the run** (receiver and sender Gmail with app passwords, HubSpot test account and key, n8n account) were made by the owner earlier (owner statement 2026-11-16); the sheet creates none; row 22 asks whether the separate sender account exists.
- **Company address**: your Hadavin company address; it may appear as the "From" line; you do nothing with it. **Gmail filter**: a rule in the receiver that puts the demo mails under label `demo` (row 22). **App password**: a password Google makes for one program. **Marker file** `~/.hadavin-take-tags/<run name>.used` makes a run name unusable twice; never delete it. **Run lock file** `take-<run name>.lock` stops a second run with the same name (section 9).
- **Ledger, ledger total, backstop, run total, usage page, balance:** defined once, in the sheet's money rule; not repeated here. **Re-pin, commit id, checksum:** defined in the sheet's words. **`mf_leads`**: the database table that records each handled test person (its person id is the key that makes a repeat visible). **`DESK_*` and `MF_*`**: setting names written into the local flow copy; what they hold is not known to the writer (section 17). **Retire check**: the program command that tries the revoked logins (section 13). **n8n's saved executions**: records n8n keeps per handled test person; the studio lead removes them in I.5. **Database container**: the sealed box on this laptop that runs Postgres; the studio lead removes it.
- Three files that are never mixed: the **step 0 result file** (`~/hadavin-step0-result.txt`), the **rehearsal result file** (named in step A) and the **masked result file** of the real run (the studio lead reads only this). "Printed result" means only what the program prints after `end`.
- **Crash-safe**: no second mail after a crash between sending and noting it down. NOT shown; nothing may claim it. **Separate login / separate check**: not built; never claimed. **Portal**: a customer web page where people approve actions; unrelated to the HubSpot account number.
- Three lists: **run card** (section 2), **order table** (section 6), **result list** (PASS/FAIL/SKIPPED lines of step 0). The word "table" means nothing else; a database table is called "the database" or by its name (`mf_leads`).

## 2. The run card (23 rows; no card, no run)
A go message needs all 23 rows (rows 8 and 9 are printed "not used" so numbers stay stable). The day card holds the values of rows 3, 4 to 7, 11, 12, 13, 16, 17, 19 and 23 as blanks the studio lead fills in (day card, "The blanks"). A row changes only by a new complete card. **Every name on rows 4 to 7 is a human person; a row that names an agent, a Claude session, a script or a helper window makes the card incomplete.** Rows 20 and 21 "kept on purpose" count only with the owner's written yes (reason, end date UTC and IST).

| Row | The card holds | If missing |
|---|---|---|
| 1 | run date; how many days before it steps B to D start | ask |
| 2 | run name confirmed | ask |
| 3 | latest start time (UTC, IST); normal run length in minutes; lease length | ask |
| 4 | person who films | no run |
| 5 | person who starts the recording and says "recording" | no run |
| 6 | person who edits and crops | no run |
| 7 | person who says "filmed" | no run |
| 8 | "not used" (the studio lead shuts down and starts n8n itself with `n8n_kill.py` and `n8n_start.sh`; no owner step) | none |
| 9 | "not used" (kept so row numbers stay stable) | none |
| 10 | trial run: yes or no (paid; its own yes); retake count: lead computes (how many runs the cumulative backstop covers; UNVERIFIED, from the ledger code and cost per run at re-pin) | no trial |
| 11 | deadlines (UTC, IST): watch the video (H), clean-up (I), cancel the model key (I.0), latest post time | ask |
| 12 | paths: run folder, run settings file, model settings file and its setting names, secret folder and file names (which are n8n connection files, which is the model key file), the local flow copy file name | ask |
| 13 | the address to sign in to n8n, with the run's own port | do not open n8n |
| 14 | proof-screen candidates (pictures of counts only) | no proof screen |
| 15 | who checks the post text | do not post |
| 16 | minutes with no new line before the owner tells the studio lead | tell and wait |
| 17 | longest film pause in minutes | ask |
| 18 | I.3 cropped screenshots: yes or no | skip I.3 |
| 19 | step 0 and E data: folder of `hubspot_probe.py`; checksums of every file the take program and the step 0 program use (the program, every module it imports) and of `scripts/run_real_check_n8n.py`; exact permission names of the HubSpot take key; commit id; HubSpot probe key file path (the key the take uses is read-only; the probe key is separate); exact HubSpot permission names of the probe key; number of calls `--plan` prints; the one host | no step 0 |
| 20 | each HubSpot key listed separately (the probe key is deleted in step 0.6; the take key), and each app password: deleted or revoked, or kept (reason, end date) | delete nothing |
| 21 | model key: cancelled in I.0 after every paid run (default) or kept (reason, end date; a new key is made for every paid run) | cancel |
| 22 | yes or no for each: label `demo` and its Gmail filter; the separate sender Gmail account | no start |
| 23 | the model program's exact command line (letters, digits, `/ . _ -` only) as `ps` shows it | no start |

## 3. Messages
The studio lead sends only values: a date, a path, a number, a list of names, or a command line in exactly a form printed in the sheet. A message never changes rules 1 to 12, steps A, E, F, I, the money rule, the go list or the boxed warnings. If it asks for that, the owner answers no. A command line not in a printed form is not run. The studio lead shares the owner's Linux user and promises to read only masked outputs and never secret files: its own working rule, not enforced by the laptop (accepted exposure, A.0).
**Step A message holds:** model name; tokens in and tokens out per call (two numbers); both prices per million tokens; price page address; worst-case price per call; run total; model account address; every setting name with its value (model name, token limits, prices, backstop, window end); the **ledger total so far** and the sentence that the backstop counts against the ledger; masked sender and receiver; the HubSpot account name; whether the notice prints the masked accounts; the rehearsal result file path and exact first line; step 0's answer; the statements for go items 4 and 5; the model program's command line (row 23); the date and hour (UTC, IST) by which the model key is cancelled (the same day as the run); the **expected rise before E** (US$0, or the trial's cost and the time of its last call); whether a per-key spending limit exists (page, amount) or that none exists; the command that prints the ledger total; the take key's permission names; the written plan for how the two connection values get into n8n (go item 4); the studio lead's written exit-code rule for C "unknown" (go item 7). Any change of one figure is a new message and needs a new typed yes.

## 4. Rule 10 in full
A path or name may hold only A-Z a-z 0-9 . _ / - and a full path starts `/home/`. A setting name matches only A-Z 0-9 `_` and holds none of KEY, TOKEN, SECRET, PASSWORD. Do not type, and tell the studio lead about, a VALUE it sends that holds: a space, a quote, `;`, `$`, a backtick, `|`, `&`, `<`, `>`, `(`, `)`, `*`, `?`, `~`, `\`, `..`, a leading `-`, a line break. (Lines printed in the sheet and card hold quotes, `$`, `<`, `>`, `|` where printed: only the values the studio lead sends are held to the list.) Before `shred` or `rm`: `ls -l "<path>"`, `readlink -f "<path>"`; any `->`, or a different path: stop; also `ls -ld "<secret folder>"`.

## 5. Counts, masked form, sample result
**Send counts.** A twice, B ten times at once, C once while n8n is shut down and started again: 13 sends, all by the program. At the end A and B each have one contact and one mail; C one contact and one mail, or "unknown" (possibly no mail and an alert mail to an address the studio lead names; not tested). So 2 or 3 contacts; another count: tell the studio lead. The program does not check the alert mail. Contacts stay in HubSpot until the owner deletes the listed ones by hand (day card F.5).
**Masked form.** First 2 letters, three dots, the last letter before `@`, then the domain: `demoreceiver@example.net` reads `de…r@example.net` (invented).
**Sample printed result (INVENTED; real wording unknown; compare meaning).**
```
  Person A: 1 contact, 1 mail      Person B: 1 contact, 1 mail
  Person C: unknown (could not tell whether it got a contact and a mail)
  Model calls made: 3              Sends made: 13
  (an exit code line may follow; no value for C "unknown" is stated here)
```
No exit code for C "unknown" is stated anywhere in the owner's files: the studio lead reads it from `scripts/run_real_check_n8n.py` at the final head and writes the rule before the day (go item 7); without that rule any number other than 0 is Freeze.

## 6. Order table
| No. | Who | What | Where | Expected |
|---|---|---|---|---|
| 1 | studio lead | run card | message | 23 rows |
| 2 | studio lead | clean start at take prep: fresh person ids; empties `mf_leads` with the take database's admin role; fresh container, same schema (one Postgres server, two databases); names UNVERIFIED, filled at re-pin | own session | "clean start done" |
| 3 | owner | run name, proof screen | message | confirmed |
| 4 | studio lead | "go step 0" with the owner's quoted yes and HubSpot account name | message | |
| 5 | owner | step 0 | browser, WSL | PASS/FAIL/SKIPPED lines |
| 6 | studio lead | rehearsal; removes model credential in n8n; statements for go items 4 and 5 | message | before A.6 |
| 7 | owner | A.0 exposure, key made (section 15); A.0b checks, old keys cancelled | model account, WSL | studio lead restarts model program |
| 8 | owner | A.1 to A.6 | WSL, browser | acknowledged |
| 9 | owner | B, C.1 to C.3, D | Windows, Gmail, Chrome, n8n | "label and inbox empty"; "profile ready" |
| 10 | studio lead | go message for the run | message | |
| 11 | owner | day card: before E, E | WSL | "run started" |
| 12 | studio lead | shuts down and starts n8n with the take scripts (section 10) | own session | n8n down once, back while C is sent |
| 13 | person on row 4 | films the contact list | | |
| 14 | owner | F: `end`, `echo $?`, usage page, delete listed contacts | WSL, HubSpot | "contacts deleted" |
| 15 | studio lead | shuts down the model program; "model program shut down"; "no more runs" | message | |
| 16 | owner | I.0, right after F.4, same day, after every paid run | model account | "model key cancelled" |
| 17 | owner | H | player | "accepted" |
| 18 | owner, studio lead | I.1 to I.7 | | |
| 19 | owner | J | | "posted" |
| 20 | owner | trial run (11) or step G (12) | | |

## 7. What to send (never a secret)
Before a run: run name; proof screen; written yes for step 0; "HubSpot is the test account"; step 0 lines and exit code, or filter counts; "I veto the exposure" only if so; the model key's name and path; decisions on older keys; the written yes with numbers; money figures; "receiver, sender and HubSpot are the throwaway accounts". Run day: "label and inbox empty"; "profile ready"; "run started"; any problem line. End of a run: exit code, last printed line, balance and money used before and after; "contacts deleted" and the number. After: "model key cancelled", the figure and key names left; "accepted" or bad seconds; "an address is visible". After a failed or trial run: "demo mails deleted" and contacts count; new yes and run name. Clean-up: names left alone or deleted; retire-check words and code; "secret files erased". Posting: the text, then "posted".

## 8. Post ban (the post must NOT say)
1. that nothing can start or spend before the owner's typed answers (the model program and flows start earlier with a live key; no closed gate exists); 2. that the same person through two doors is one contact; 3. that no contact data stays in n8n, that recovery takes within 60 seconds, or an alert within 30 seconds; 4. that a portal, approval step or audit trail exists, or that a person approves each action; 5. that n8n cannot reach the internet; 6. that the run is crash-safe or no mail goes out twice after a crash; 7. that the count is made by a "separate check" or "separate login"; 8. that everything is in one database (aim: one Postgres server with two databases; not proven until the rehearsal shows it); 9. that the spend is capped by a hard limit (a setting a person checks); 10. that test data was "deleted permanently" or "erased", or that the program deletes or does not delete contacts unless the studio lead's go item 5 statement and the printed result both show it; 11. any sentence about recovery after a crash, the lease or three tries, unless the studio lead approved that exact sentence in writing with the file and line it read (sheet, step J); 12. anything about which permissions a part has; 13. "Postgres is the one store" (the caption says "one Postgres server, two databases"; the model program's journal file is a second record).

## 9. Exit codes and refusals
0 success. 1 the answer was not `y` or the confirmation line did not match. 2 the program refused to start or go on (a setting, a failed login check, no keyboard, closed input, an answer faster than 2 seconds, a used run name or key, a lock file, the window end too close, a second mailbox, Ctrl-C before the first send). 3 a count or verdict failed after the run, or Ctrl-C after the sends began (UNVERIFIED; this table gives no code for C "unknown"; see section 5). If cut off at the very end the number may be 3, 120 or another and the lock file may stay: do not run again. Retire check codes: 0 both refused (good); 3 a login still works; 2 could not tell. Any number other than 0 in a run: Freeze (day card F.3), unless the studio lead's written exit-code rule names exactly that number for exactly that printed result.
> **WARNING before removing the run lock file: it cannot be undone. Remove only the one file the studio lead names, after it says so.**
Lock file `take-<run name>.lock` beside the run folder: `ls -l`, `readlink -f` (must equal the path), compare with rule 10, then `rm -- "<path>"`. **Start deadline:** the program needs about 14 minutes before the window end; at the default setting the latest start is before Mon 23 Nov 2026 18:14:40 UTC = 23:44:40 IST; row 3 has the exact time.

## 10. n8n shutdown and start (studio lead only)
The owner never stops or starts n8n. The studio lead does it with the take scripts `n8n_kill.py` (identity check on the process, no process number from any card) and `n8n_start.sh` (take branch, local only), against the run's own n8n port only, never the owner's everyday n8n on ports 5678 or 5679. The program prints cue lines for `y`, the challenge and `end` only; that it prints no extra cue is UNVERIFIED (lead checks at re-pin). How the studio lead times the shutdown while person C is sent is the studio lead's step and is rehearsed before the card is sent; the owner has no part in it.

## 11. Step T. Trial run (owner step; only if row 10 says yes; happens BEFORE the real run)
A trial run is a real, paid run: its own written "yes step T" quoting why, its own `go trial run <run name>`, its own step A (new yes, new run name, A.0 to A.6, money rule redone), the boxed warnings of E and F. Nothing is filmed or posted; at F.2 you look at the contact list yourself, then type `end`; afterwards step G. The trial's money counts in the next A reading and in the ledger total. The key is cancelled after the trial (I.0, same day); the real run needs a new key, a new yes, a new run name and a fresh C.1.

## 12. Step G. Failed run or after a trial (owner step; the studio lead sends the counts)
> **WARNING. Delete ONLY demo mails in the receiver and ONLY HubSpot contacts of the failed or trial run (the studio lead gives count and run name). Check the account before each delete. If Trash holds anything else, do NOT empty it. Never erase the marker file.**
(1) Receiver Gmail: open label `demo` and Inbox; tick only the demo mails one by one (subject starts `[demo] lead`; "lead" is a made-up sales contact); never "Select all conversations"; Trash icon; open Trash: only those mails, else stop; "Empty Trash now". Never Archive. (2) HubSpot: delete leftover contacts as day card F.5, only the counted ones on the studio lead's list. (3) Send "demo mails deleted" and the count. (4) New written yes and new run name. A run that got past both typed answers has used its name. C "unknown": the studio lead says whether a contact or alert mail may remain; until then delete only what it counted. No new run is possible after the window end.

## 13. Retire check results (I.4)
| Prints (code) | Row 20 says | Owner does |
|---|---|---|
| both "refused as expected" (0) | any | send "retire check succeeded" |
| mailbox "STILL WORKS" (3) | revoked | revoke again (I.1), run again |
| mailbox "STILL WORKS" (3) | kept | counts only if HubSpot is refused; studio lead says "succeeded, mailbox app password kept on purpose" |
| HubSpot "STILL WORKS" (3) | deleted | delete the private app again (I.2), run again |
| HubSpot "STILL WORKS" (3) | kept | counts only if the mailbox is refused; studio lead says so |
| both kept | both | studio lead writes "retire check not required: kept on purpose" with end date |
| "could not tell" (2) | any | wait |
Cannot succeed (code 2 twice, a row missing): keep every secret file, remove nothing more; the studio lead writes what is left and the date to finish.

## 14. Step D and filming (owner step: read before the day)
**Check in the `demo-take` profile, and again on the finished video (H): no address except `take-<run name>-a@example.com`, `-b@`, `-c@`.** (1) Receiver mail LIST only: no clicking or hovering the account picture, no opened mail, no "show details"; a Gmail tab title may carry your address: crop. (2) Never the sender mailbox or "Send mail as" settings. (3) Tab titles and address bars. (4) n8n's list of runs only as a film screen, made-up names, no old run; not the mail step's detail. (5) The proof screen is made by the studio lead from the rehearsal (never a live table); it is counts only, fewest words, no address except test addresses, no account number; you film nothing for it. (6) Terminal windows: no address in prompt, history or settings output; `clear` first. (7) Notifications, pop-ups, system tray. (8) **Account numbers**: none in HubSpot's address bar or header, the account picture menus, n8n's account or project name, your n8n address; the editor (row 6) crops the address bar from every frame; you check in H. (9) The HubSpot contact list: step 0's made-up contact must be gone. (10) **The notice** prints masked sender and receiver accounts (if the program does) and a Linux path: the editor (row 6) crops or cuts them from every frame; you check in H.
**Shot list (PROPOSED by the writer; the studio lead's run sheet has the real scenes).** Recording is OFF through steps A, step 0, every command that prints a file, and the whole of "Before E" on the day card. Recording ON (row 5 person says "recording") after `clear`, just before the start line. S1 run window: start line, the notice (masked accounts and path cropped by the editor), `y`, confirmation line. S2 n8n's list of runs during the sends (made-up names). S3 HubSpot contact list search at F.1 (row 4). S4 receiver mail LIST under label `demo`. S5 printed result after `end`. Recording OFF before `echo $?` follow-up, the usage page, any key page and every settings output.

## 15. Saving the model key (step A.0; owner step; every command UNVERIFIED)
1. **Before copying anything:** Windows Settings, System, Clipboard: switch off "Clipboard history" and "Sync across your devices" (labels unverified on Windows 11); do not rely on "Clear all" after that; switch off Windows Recall and every screen recorder (Game Bar capture too); nobody shares the screen.
2. In the model account (address by hand, from the card; check the account name) create a key for this run only (a trial has its own key). If the step A message says a per-key spending limit exists, set it as the message says and check it shows; if it says none exists, do not call the key limited. The page shows it once; copy it with the page's copy button (page labels unverified; the studio lead gives the page names in the step A message; if you cannot find the key list: freeze).
3. In WSL `echo $BASH_VERSION` prints a version (else stop). Type, with `<model key file>` the full path from row 12 and the file form the studio lead states (key alone on its line, or `NAME=` before it, written `"NAME=$K"`): `( set -C; umask 077; read -rs -p 'paste key, Enter: ' K; printf '%s\n' "$K" > "<model key file>" ); echo "exit $?"`. Paste with a right-click only after the prompt `paste key, Enter:` is on screen, then Enter. Nothing shows; `set -C` refuses to overwrite (exit not 0: stop; never overwrite an older key file); only you can read the file.
4. Check: `ls -l "<model key file>"` starts `-rw-------`; `wc -c "<model key file>"` shows 20 or more. Then copy a harmless word (this overwrites the clipboard).
5. **Paste empty or short:** the key is still on the browser page: copy it again, `rm -- "<model key file>"` (after rule 10 checks; it holds nothing valid), repeat step 3. Page closed: cancel that key and make another.
6. The key passes through the clipboard and browser; the studio lead shares your Linux user (accepted exposure, A.0), so the guard is that the key is yours, for one run, and cancelled in I.0 the same day (limited only if step A said a limit exists).

7. **Check the model program (A.0b, go item 6)**, in WSL (UNVERIFIED): `ls -l --time-style=full-iso "<model settings file>" "<model key file>"`, `ps -o pid=,lstart=,args= -p <process number>`, `pgrep -af "<model program name from row 23>"`, `date`. Needed: `ps` shows that process number and the command line written on row 23; `pgrep` prints exactly one line; the start time is later than both file times; `date` is within 2 minutes of the Windows clock (WSL can drift after sleep). Example: files changed 14:02 and 14:05, start 14:11: passes; start 14:04: fails.

## 16. Screenshots (I.3) and the erase tests (I.6)
**Erase tests (I.6):** each path starts with the secret folder of row 12 (the flow copy: with the run folder of row 12), ends in a name listed on row 12, does not end `.used`, is not the run settings file, is not kept on purpose; the model key file only after I.0.
**Screenshots (only if row 18 says yes).** After I.1 and I.2, one screenshot of each list, cropping any address or name (Snipping Tool: Start, type `Snipping`). Save in `C:\Users\<your Windows user name>\Downloads\Hadavin_local\real-run\` (the user name is the folder under `C:\Users`) under the names the studio lead gives. Delete the uncropped originals the same day (Pictures, `Screenshots`) and empty the Recycle Bin (and OneDrive's).

## 17. For the studio lead: not proven, and open answers
**Not proven (nothing in the sheet, card or here was run):** all new commands (`ls -l --time-style=full-iso`, `ps -o pid=,lstart=,args=`, `pgrep -af`, `read -rs`, `set -C`, `wc -c`, `python3 -I -c`, `cut`) are standard but UNVERIFIED on this laptop. The rehearsal is written, not run; the code never ran against live Gmail, HubSpot or a model call; the loopback re-smoke is "real-v5 minus one node" (the HubSpot contact step is a stand-in); never call it "real run passed". The row 19 commit is a provisional head on a local-only branch: checksums prove only equality with the card. Not shown: that nothing can spend before both typed answers (the model program and flows start earlier; no closed gate; the fallback "the studio lead switches on flows after the typed `y`" is not accepted: lead's default decision 5 of 2026-11-16). Not shown: that the program prints the masked sender and receiver on the notice; that it ends the film pause with `end` and ends early on a wrong line or closed terminal (assumed); that the program runs under `python3 -I`; that the stop-n8n cue is printed (Q20.1); that the program accepts the key file form; that the start time and key file times prove which key loaded; that the settings file is not re-read after start (do not edit after start; lead verifies at re-pin).
**Scope sheet text to rewrite (lead; I may not edit inputs):** AGENT-SCOPE section 3 should read "no delete call exists in the take program; leftovers are listed; the owner deletes by hand" (`run_real_check_n8n.py`, read-only HubSpot identity, archive_contacts "no"); its older text that the take archives contacts by a DELETE call (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, review finding on contact archiving) describes the old desk harness. Go item 5 is given only after the lead's final-head check. Also stale: scope lines 5, 9, 13, 20 and decisions lines 2 and 9 (Q20.5).
**Figures:** the notes name US$180 and US$189; the facts file says "US$180 of 189 in-code backstop". Which is the backstop and which the credit is not clear; neither is used in the sheet; the step A message names backstop, credit, ledger total.
**Open items:** items the studio lead has not re-read are marked UNVERIFIED, "lead verifies at re-pin" or "THE STUDIO LEAD FILLS THIS IN"; each is listed with its exact missing input in `v13-OPEN-FOR-LEAD.md` (stop/start cue, role and database names, exit code for C "unknown", lease and index claims, retake count, key scopes, the settings re-read, console page names, per-key limit, credential loading plan, rehearsal stamp). Unlisted new question: what do `DESK_*` and `MF_*` hold (I.6 treats the flow copy as a secret).
**Decision labels:** "decision N of 2026-11-16" always means the studio lead's default decisions (the owner may veto), never an owner decision.
