# Appendix to the owner's day sheet, version 10

Written Mon 16 Nov 2026. Times are UTC and IST (IST = UTC + 5:30). This file holds what the day sheet (`OWNER-STEPS-realrun-v10.md`) points to. Nothing here changes a rule of the day sheet. Sections: 1 Words, 2 Send counts, 3 Step table, 4 What to send, 5 J. What the post must NOT say, 6 Exit codes and other refusals, 7 Old copy procedure, 8 For the studio lead (what is not proven yet).

## 1. Words (the ones not needed until a step uses them)

- **Run settings file**: the small file with the settings of one run (run name, Gmail label to read, worst-case price per call). The studio lead prepares it and sends its path. You never edit it.
- **Model settings file** (`stage.env`): the file with the settings of the model program: the backstop, the price figures and the stop time. You never edit it and never open it with `cat`; in step A you print only the two named lines with `grep`.
- **Spending backstop**: the highest total in US dollars written in the model settings file; a person checks it; the program does not print it and does not promise it. It is separate from the account credit (the studio lead's notes say a backstop of US$180 and a credit of US$189, ending Mon 23 Nov 2026 18:29 UTC = 23:59 IST; not re-checked). The money rule is in the day sheet.
- **Run folder**: the folder in WSL that holds the run's files; the studio lead sends the exact `cd` line, whose form is `cd <folder from run card row 8>`; if it differs from row 8, stop.
- **Stop time**: the time after which the run may not spend money or start; the program's screens call it "window end". Planned: Mon 23 Nov 2026 18:29 UTC = 23:59 IST (the studio lead confirms it). The program refuses a start that is too close (it needs about 14 minutes); at the default setting the latest start is before 18:14:40 UTC = 23:44:40 IST; row 3 gives the exact time.
- **Receiver**: the throwaway Gmail account that only receives the demo mails. **Sender**: the throwaway Gmail account n8n sends from (row 17 says whether it exists). **Company address**: your Hadavin company address; it may appear as the "From" line of the mail; you do nothing with it. **Label `demo`**: a Gmail label in the receiver; the program reads only this label; a Gmail filter (a rule in the receiver's settings) puts the incoming demo mails under it; the studio lead makes both (row 17).
- **App password**: a password Google makes for one program. **Private app (HubSpot)**: a named access setup in the HubSpot test account; each has a key. (Step 0 calls its key a "token".) **Scope names**: the permission names HubSpot lists on a private app's page.
- **Marker file**: `~/.hadavin-take-tags/<run name>.used`; it makes a run name unusable twice. You never delete or edit it.
- **Run lock file**: `take-<run name>.lock` beside the run folder; it stops a second run with the SAME run name (a new name is not stopped by it). Deleting it: section 6.
- **Retire check**: a program command that tries to log in with the keys you revoked and must be refused (step I.4).
- **n8n's saved runs**: the records n8n keeps of each time it handled a test person; they hold only test addresses and perhaps the company address; the studio lead removes them in I.5.
- **Database container**: the sealed box on this laptop that runs the database program (Postgres) for the run; the studio lead removes it. You do not start or stop Docker. **Database passwords**: made by the studio lead, who disposes of them.
- **Masked result file**: the file the program writes in the run folder; the studio lead reads only this masked file, not the run folder's other files. The step 0 result file is `~/hadavin-step0-result.txt`. The rehearsal result file is named by the studio lead in step A. The three are different files and are always called by those names.
- **Crash-safe**: if the program stops after sending a mail and before noting it down, no second mail goes out when it starts again. NOT shown yet; nothing may claim it until the studio lead states in writing a result on the real n8n that shows it (step J).
- **Separate login**: a second login that only counts mails and contacts. Not built; nothing may say a "separate check" or "separate login" exists. The program's own count is "the program's count".
- **Browser profile**: a Chrome user profile (the round picture top right), never a Gmail menu.
- **Portal** (used only in the ban list): a customer web page where people approve actions. It has nothing to do with the HubSpot account number.
- **The studio lead's commands run as the same Linux user as yours.** This is why you never put a secret in a message and why you create and cancel the model key yourself.
- **Stop and wait**: type nothing more, close nothing, tell the studio lead what you see, wait. Two exceptions: at the `y` prompt type `n` and Enter; in step 0 follow its own stop list.
- Three lists, three names: the **run card**, the **step table** (section 3) and the **result list** (the PASS/FAIL/SKIPPED lines step 0 prints). "Table" is not used for anything else; the database's own table is called "the database".

## 2. Send counts (what the run should show)

Person A is sent in twice, B ten times at once, C once while n8n is stopped and started again: 13 sends, all made by the program. Each test person should be treated once. At the end you should see one contact and one mail for A and for B; for C one contact and one mail, or, if the program reports C as "unknown" (it could not tell whether C got a contact and a mail), possibly no mail and an alert mail (a mail the system sends to an address the studio lead names on the card; not tested). Then a contact for C may or may not exist; the studio lead tells you which and where the alert mail goes. So you should see 2 or 3 contacts; another count: tell the studio lead. A and B must come out right; C may be "unknown", and then the exit code may be 0 or 3; the studio lead's written statement (go condition 7) says which counts as success. The program does not check the alert mail itself. After the run the contacts stay in HubSpot until you delete them by hand (F.3).

## 3. Step table: every owner step (who, what, where, expected)

| Step | Who | What is typed or clicked | Where | Expected |
|---|---|---|---|---|
| 1 Run card | studio lead | sends the run card | message | 17 rows |
| 2 Clean start | studio lead | fresh made-up person ids never used in a rehearsal; empties the database table of the rehearsal before the real run; says so | its own session | message "clean start done" (owner does nothing) |
| 3 Run name, proof screen | owner | picks a new word and one screen from row 10 | message | studio lead confirms |
| 4 Step 0.0 go | studio lead | "go step 0" and the HubSpot test account name | message | no go, no step 0 |
| 5 Step 0.1 account | owner | compares the account name; "HubSpot is the test account" | browser, message | reply |
| 6 Step 0.2 checksums | owner | `cd` line, then `sha256sum` per file on row 14 | WSL | same codes as row 14 |
| 7 Step 0.3 plan | owner | `python3 -I scripts/hubspot_probe.py --plan` | WSL | "planned calls: N", the host of row 14 |
| 8 Step 0.4 check | owner | the one-line command | WSL | one number |
| 9 Step 0.5 filter | owner | two counting lines; if both 0, `cat`, sends PASS/FAIL/SKIPPED lines and the code | WSL, message | list; exit code 0 alone does not mean the paths work |
| 10 Step 0.6 answer | studio lead | "paths work", "a path failed" or "unknown" | message | one line |
| 11 Rehearsal | studio lead | rehearsal values; runs it; names the rehearsal result file and its first line | message | file named; no pass, no run |
| 12 n8n credentials | studio lead | removes any model credential; confirms exactly two connection values; confirms the program does not delete or archive contacts | message | in writing before step A |
| 13 A.0 model key | owner | creates a run-only model key, saves it in the row 8 file; sends key name and path | model account, message | studio lead restarts the model program and sends the time |
| 14 A written yes | owner | A.1 to A.5 checks, one-line yes | WSL, browser, message | acknowledged |
| 15 B laptop | owner | plug in; sleep Never; lid Do nothing | Windows | shows after reopening |
| 16 C.1 to C.4 | owner | receiver empty; profile `demo-take`; n8n credentials list (names only); own accounts check | Gmail, Chrome, n8n, message | "label and inbox empty"; "profile ready"; "throwaway confirmed" |
| 17 D film check | owner | look only | `demo-take`, terminals | only test addresses, no account number |
| 18 Go | studio lead | `go trial run` or `go real run <run name>` with all go conditions | message | no go, no start |
| 19 E.0 to E.4 | owner | re-read settings, checksum, start line, compare notice, `y`, confirmation line; "run started" | WSL, message | the run starts |
| 20 n8n stop/restart | person on row 5 | the exact line in a second window | named on the card | n8n down once, back while C is sent |
| 21 Filming | person on row 4 | films | named on the card | contact list filmed |
| 22 F.1 `end` | owner | `end` after "filmed" | WSL run window | result printed, `$` back |
| 23 F.2 finish | owner | `echo $?`; usage page; sends code, last line, balance and money used before and after | WSL, browser | code 0 or see section 6 |
| 24 F.3 contacts | owner | deletes the listed contacts by hand; "contacts deleted" and the number | HubSpot | none left |
| 25 After the run | studio lead | stops the model program; says "model program stopped" and (if no run follows) "no more runs" | message | message |
| 26 T, G | owner | trial run or failed-run clean-up | WSL, Gmail, HubSpot | messages sent |
| 27 I.0 model key | owner | cancels the named key; "model key cancelled" | model account | key gone |
| 28 H | owner | watches the edited video twice; "accepted" or bad seconds | player | reply |
| 29 I.1 to I.7 | owner and studio lead | revoke, private apps, screenshots, retire check, studio lead's removals, secret files, laptop back | Google, HubSpot, WSL, Windows | see the day sheet |
| 30 J post | owner | posts; "posted" | LinkedIn or as told | someone else checked the text |

## 4. What to send the studio lead (never a secret)

| When | Send |
|---|---|
| Before a run | the run name and the proof screen you chose; "HubSpot is the test account"; step 0 PASS/FAIL/SKIPPED lines and the exit code, or the filter counts; the model key name and path (A.0); your written yes with numbers; the money figures you read; "receiver, sender and HubSpot are the throwaway accounts" |
| Run day | "label and inbox empty"; "profile ready"; any problem line |
| During a run | "run started"; "closed the terminal early" if it happens |
| End of a run | exit code, last printed line, balance and money used before and after; "contacts deleted" and the number |
| After a run | "model key cancelled"; "accepted" or the bad seconds; "an address is visible" |
| After a failed or trial run | "demo mails deleted" and the number of contacts; a new yes and run name |
| Clean-up | names of passwords or private apps left alone; names of private apps deleted; retire-check words and code; "secret files removed" |
| Posting | the post text; then "posted" |

## 5. J. What the post must NOT say

- that the same person through two doors is one contact;
- that no contact data stays in n8n, that recovery takes within 60 seconds, or that an alert comes within 30 seconds;
- that a portal, an approval step or an audit trail exists or shows these rows, or anything suggesting a person approves each action;
- that n8n cannot reach the internet (its outgoing traffic is switched off by settings and only watched, not blocked);
- that the run is crash-safe, or that no mail is sent twice after a crash between sending the mail and noting it (lifts only when the studio lead states in writing a result on the real n8n that shows it, and names it; a passing rehearsal does not lift it);
- that the count is made by a "separate check" or "separate login";
- that everything is in one database (the aim is one Postgres server with two databases, n8n's own and the run's; not proven until the rehearsal shows it; some files stay outside it);
- that the spend is capped by a hard limit (it is a setting a person checks);
- that test data was "deleted permanently" or "erased" (HubSpot may keep an archived copy, Gmail's deleted mail may stay for a time), or that the program deletes the contacts (you delete them by hand);
- that a lead sent twice is processed once with no mention of the lease: the allowed claim is only "a lead sent twice with the same id inside the lease is processed once";
- anything about which permissions any part has or does not have (for example "only reads", "least privilege", "each part has only what it needs").

## 6. Exit codes and other refusals

Exit codes of the program (step E): 0 success. 1 your answer was not `y`, or the confirmation line did not match. 2 the program refused to start or go on: a setting, a failed login check, no keyboard, closed input, an answer typed too fast, a run name or key used before, a lock file exists, the stop time too close, a second mailbox, Ctrl-C before the first send. 3 a count or verdict failed after the run, or Ctrl-C after the sends began. Rare: if the program is cut off at the very end the number can be 3, 120 or another, and the run lock file can stay behind; do not run again; the studio lead reads the masked result file. Any number other than 0: rule 12.
Exit codes of the retire check differ: 0 both logins refused (good); 3 a login still works; 2 anything else ("could not tell").

> **WARNING before deleting the run lock file. It cannot be undone and the lock protects against a second run with the same run name. Delete only the one file the studio lead names by its full path, only after it says so.**

- **Run lock file:** if the program stops hard it may leave `take-<run name>.lock` beside the run folder; the next run with that run name is refused. Remove it ONLY when the studio lead says so: `ls -l "<full path>"`, `readlink -f "<full path>"` (must equal the path), compare with the message and rule 10, then `rm -- "<full path>"`. The name must be exactly `take-<run name>.lock`, no `*` or `?`.
- **Start deadline:** see "Stop time" in section 1.

## 7. Old copy procedure (only if the studio lead releases it; unverified)

Kept from version 9 and used only if n8n asks you to type a connection value again and the studio lead names the secret file, which must be one row 8 lists as an n8n connection file (never the model key file). No recording, nobody watching; first check Windows clipboard sync is off (Settings, System, Clipboard: "Clipboard history across your devices" off; if on, do not copy). Show the value in WSL with `cat "<full path>"` (rule 9 first), select, copy, paste into the n8n field, type `clear`, close that terminal window, copy a harmless word to overwrite the clipboard, clear the clipboard history (Windows key + V, "Clear all"). Never paste the value into chat; send only "done". A way that does not print the value on screen (for example `clip.exe`) is not checked and is not used here. Stop and tell the studio lead if n8n shows a saved secret in clear text on screen or in an export.

## 8. For the studio lead (not an owner step; the owner can ignore it): what is not proven yet

- The rehearsal is written and has NOT been run. The code has never run against a live Gmail, HubSpot or model call. The only live check before the run is the loopback re-smoke plus one made-up lead.
- The code under test is a provisional head; row 14 gives the commit id.
- Not built yet (note BL-wp6-G1 in the audit): the flows read `$env.DESK_*` and `$env.MF_*` inside nodes, while the start script blocks environment access in nodes; the real run needs a take-time literal substitution into a local copy of the flows.
- Not shown: that nothing can spend before both typed answers. The model program and the n8n flows are started by the studio lead before `y`. A closed gate in the program (design item S9-1) is described, not built; the fallback "the studio lead switches on the flows after the owner's typed `y`" is not accepted (decision 5). The real limits are the balance and the model key.
- Not shown: that the program prints the masked sender and receiver (design item S9-4, deferred).
- Not shown, and contradicted by the scope sheet: that the program at the row 14 commit does not delete or archive contacts (the scope sheet says the code archives at the end by a DELETE call, `run_real_check_n8n.py:1051`, finding F-01). Decision 2 says the program never deletes. Go condition 5 therefore needs your written statement; if the program still deletes at `end`, steps F and G and the post ban need rewriting.
- Not shown: that the program ends the film pause with the word `end`, and that typed-ahead keys, a wrong line or a closed terminal end it early (assumed; rule 11).
- Not shown: that the program runs under `python3 -I` (isolated mode may not add the script's folder to the import path); the rehearsal must use exactly the printed command form.
- The program does not print the backstop or money spent so far. The notice text "B ten times at once" is a fixed string, not taken from a setting. The program does not check: the alert mail, mail in any folder other than `demo`, the contact id read back from HubSpot (only checked to be all digits), the manual n8n stop and restart.
- Not checked: HubSpot scope names, HubSpot search by run name, HubSpot behaviour on deleting a missing contact, Windows Snipping Tool and clipboard behaviour, Google and model-account click paths, the model account's usage-page delay, Gmail's label timing for mail sent from another Gmail account, whether Gmail accepts the company address as the shown sender.
- Not shown: that one Postgres server holds two databases and that removing saved runs works; that a crash between sending the mail and noting it sends no second mail.
- Where records are kept: one Postgres server is the aim; some files stay outside it (the model program's log written before each model call, a spending record, lock files, the run-name marker file).
- The video is the real-run scenes 1 to 4 only; the stand-in scenes and their unmeasured caption number are not in it.
- Lease claim: the claim is "a lead sent twice with the same id inside the lease is processed once"; what happens after the lease ends is not claimed. Spend limit: stays by the owner's own eye (money rule) plus the model program's stage checks; no hard cap is claimed.
