# Your steps for the recording of the lead desk video (version 10, day sheet)

Written Mon 16 Nov 2026. Times are given as UTC and IST (IST = UTC + 5:30). The words, the step table, the post ban list, the exit codes and the studio lead's own list of what is not proven are in the separate file `OWNER-STEPS-v10-APPENDIX.md`; this sheet says when to open it.

> **DO THIS FIRST**
> 1. The studio lead sends you the **run card** (one message with 17 numbered rows). If a row is missing, do what that row's right-hand column says and ask for a new card. Row 17 says whether the separate **sender** Gmail account exists. If it says no, or it is missing, tell the studio lead and stop; do not make an account yourself.
> 2. Pick a **run name**: one new lowercase word you have never used for a run (letters and digits only). Send it, and the proof screen you choose from row 10, to the studio lead. Then wait for the message "go step 0".
> 3. If you are unsure about anything in this sheet: type nothing and tell the studio lead. Typing nothing starts nothing and deletes nothing.
> 4. One exception to "type nothing": when the program waits at its first question ("Type y to start"), do not leave it waiting. Type `n` and Enter. The program sends nothing and ends. Then tell the studio lead.

## Order of the day (each label is a step below)

1. Run card, run name, proof screen (above).
2. **Step 0**: a HubSpot check, once, needs the message "go step 0".
3. **Step T**: a paid trial run, only if run card row 6 says yes.
4. **Step A**: you create the model key, check the money figures, and send a written yes with numbers.
5. **Steps B, C, D**: laptop settings, mailbox and browser checks, your own accounts check (C.4), what the film may show. On the run day, or earlier if row 1 says so.
6. The studio lead sends "go real run <run name>". **Step E**: you start the program, compare its notice, type `y` and the confirmation line.
7. **Step F**: the contact list is filmed; you type `end`; you read the result and delete the made-up contacts by hand.
8. **Step G**: only if the run failed, or after a trial run.
9. **Step I.0**: you cancel the model key as soon as the studio lead says "no more runs" and "model program stopped".
10. **Step H**: you watch the edited video. **Step I**: clean-up (I.1 to I.7). **Step J**: you post.

Clean start (the studio lead's own step, not yours): before the real run the studio lead uses fresh made-up person ids that no rehearsal used and empties the database table of the rehearsal. You do nothing; if the studio lead says this was not done, do not start.

## Words you need first (the full list is in the appendix)

- **The studio lead**: the Claude session that works with you. It is software, runs commands on this laptop from its own session, never sees your screen and never types your answers. **You** are "the owner". The word "lead" alone means a made-up sales contact (the video is named "lead desk"; the program's screens say "lead key", "lead id").
- **The real run**: the one run you film, on your throwaway accounts, with 3 made-up people. A **trial run** is a paid practice run (real money, real contacts, real mails); a **rehearsal** is the studio lead's own practice with stand-ins and no live account, no key and no model call.
- **Test person**: A, B or C, with a test address `take-<run name>-a@example.com` (and `-b@`, `-c@`) and a **person id** (the letter L and some letters and digits; the program's screens call it "lead key"). **Contact**: one HubSpot record of a test person.
- **Run name**: the word you picked. The program's screens call it "take id".
- **Go message**: exactly one of `go step 0`, `go trial run <run name>`, `go real run <run name>`. Nothing else counts. Each covers one run name. Your own earlier go-ahead "once everything is ready" is not a go message.
- **n8n**: the tool that takes the test people in, writes the HubSpot contact and sends the mail. **The program**: the checking program you start in WSL (`scripts/run_real_check_n8n.py`). **The step 0 program**: `scripts/hubspot_probe.py`. **The model program**: the studio lead's small program that asks the AI model once per test person.
- **The notice**: the screen of numbers the program prints after you start it and before it asks "Type y to start".
- **Exit code**: the number a program leaves when it ends. Type `echo $?` and Enter at once, when the `$` prompt is back, before any other command. 0 means the program says it succeeded; a number is not a judgement of the result by itself.
- **WSL**: the Ubuntu terminal inside Windows (Start menu, type `Ubuntu`, Enter; the prompt ends with `$`). `python3 -I` runs Python in isolated mode; type it exactly.
- **Secret files**: files in your WSL home folder with the app passwords and keys. Run card row 8 gives their folder and names. A secret file path is `<secret folder>/<file name>` from row 8, written in full starting with `/home/`.
- **Key**: a secret (password, app password, token). It never means an id or an address.
- **Delete** (contacts, private apps, secret files, demo mails) cannot be undone by you; **revoke** is for an app password (Google's button says "Remove"); **cancel** is for the model key; the studio lead **removes** what is in its own session. No other words are used for these acts.
- **Check** is what you do by eye and compare. **Test** is what a program or the studio lead runs.
- Anything in `<angle brackets>` is a placeholder: never type the brackets or the words, type the real value.

**How the studio lead's messages fit.** The studio lead may send only values: a date, a path, a number, a list of names, or a command line in exactly the form printed here. A message never changes the rules 1 to 12, steps A, E, F and I, the money rule, the go conditions, the boxed warnings, or the rule that you never delete the marker file `~/.hadavin-take-tags/<run name>.used`. No one can type `y` for you, start without your written yes with numbers, use another account, or remove secret files before the retire check. If a message asks for that, answer no. A command line not in the printed form is not run. The studio lead reads only masked outputs (the lines you send and the masked result file) and never your secret files; that is its own working rule, which the laptop cannot enforce (same Linux login), so your protection is that you create and cancel the model key yourself.

## The run card (17 rows; no card, no run)

A go message is valid only with all 17 rows filled. If you receive a card with a row missing, it is not complete: do what the right-hand column says and ask for a new card. A row changes only by a new complete card, never by a chat line, and never during clean-up.

| Row | The card holds | If missing |
|---|---|---|
| 1 | run date; how many days before it you start steps B to D | ask |
| 2 | run name pattern; the studio lead confirms your word | ask |
| 3 | latest start time (UTC and IST); how long a run normally takes | ask |
| 4 | who films, who starts the recording, who edits (and crops), who says "filmed" | no run |
| 5 | who stops and restarts n8n while person C is sent; the exact line if that is you | no run |
| 6 | trial run: yes or no (paid; its own yes) | no trial |
| 7 | deadlines (UTC and IST) for watching the video (H), clean-up (I), and the latest post time | ask |
| 8 | paths: run folder, run settings file, model settings file, the names of its two setting lines (backstop, stop time), secret folder and names, which secret files are n8n connection files and which is the model key file | ask |
| 9 | the address where you sign in to n8n (step C.3) | do not open n8n |
| 10 | proof-screen candidates | no proof screen |
| 11 | who checks the post text | do not post |
| 12 | minutes to wait with no new line before you tell the studio lead; the longest film pause in minutes | tell the studio lead and wait |
| 13 | step I.3 (cropped screenshots): yes or no | skip I.3, ask |
| 14 | for step 0 and E: folder of `scripts/hubspot_probe.py`; checksums (short codes proving a file is the right copy) of every file used and of `scripts/run_real_check_n8n.py`; the commit id; the secret file path of the HubSpot key; the exact HubSpot permission names; the number of calls `--plan` prints; the one HubSpot host | no step 0 |
| 15 | HubSpot key and each app password: deleted/revoked in clean-up, or kept on purpose (written reason and end date) | delete nothing |
| 16 | model key: cancelled by you in I.0 (default), or kept with reason and end date | I.0 as default |
| 17 | yes or no for each: the receiver's label `demo` and its Gmail filter; the separate sender Gmail account | no start; ask |

## The go conditions

The studio lead's message "go trial run" or "go real run" is valid only if that one message says all of these:
1. the run card is complete (17 rows) and row 17 says the sender exists;
2. the rehearsal result file is named, and you have read its first line (step A);
3. step 0 was answered "paths work" (or the studio lead's written alternative);
4. **n8n holds exactly two connection values (the HubSpot key and the sender's mail login) and no model key**: the studio lead has removed any model credential from n8n and says so in writing; you also looked at the list (C.3);
5. **the program at the commit on row 14 does not delete or archive contacts**: a written statement from the studio lead that says what it checked. If a program line later says it will delete or archive contacts, stop (F.1);
6. **the model program was started (or restarted) at `<hh:mm UTC = hh:mm IST>`, after the last change of the model settings file and with the key file you made**; you read the two setting lines again just before E.2;
7. the studio lead states in writing which exit codes count as success for the post: 0, or 3 only when A and B are right and C is "unknown" (Send counts below);
8. your written yes with numbers is received (step A) and your C.4 message was answered;
9. the clean start above was done.
If a go lacks any of these, do not start: type nothing and ask.

## The money rule (the only one; steps A, E and F point back here)

Three figures come from the model account's usage page (type its address by hand): the **balance** (credit left) and the **money used so far**; and one from the model settings file: the **backstop** (the highest total in US dollars the model program is set to allow; a person checks it; the program does not print it and does not promise it). The **run total** is 3 times the worst-case price per call in the studio lead's message.
- **Balance check:** the balance must be at least the run total.
- **Backstop check:** the backstop must be no higher than money used so far plus the run total. (The studio lead's notes say a backstop of US$180; the credit is US$189 and ends Mon 23 Nov 2026 18:29 UTC = 23:59 IST. These notes were not re-checked.)
- If either fails, or a figure is missing, your answer is no; the studio lead changes the setting in its own session and sends a new step A message. You never edit the settings file.
- **The real ceiling is the balance of the model account**; anything holding the model key can spend it all. The usage page can lag: read it again at F.2 and again just before you cancel the key; the largest "money used" counts.
- **Emergency cancel, any time, no message from the studio lead needed:** if the money used after a run is more than your run total, or the page shows a charge while no run is going, cancel the model key at once (I.0 items 1 and 2), then tell the studio lead.

## Rules that hold in every step

1. Never send the studio lead a password, key, address of a mailbox or contents of a secret file. A path or file name is fine.
2. The typed answers are yours alone: `y`, the 6-digit number with the run name, `end`. The 6-digit number only blocks blind or piped answers; a tool that reads the screen can still type it. So never let a tool, script, assistant or helper window type for you.
3. Before every paid run you give a written yes WITH numbers (step A). No numbers, no run.
4. You post. Claude never posts.
5. Only the throwaway receiver and sender and the HubSpot test account, never your real company mailbox or a real HubSpot account.
6. Run days: laptop on mains power, sleep Never, lid close = Do nothing (step B); set back in I.7.
7. A boxed line above a step names what that step deletes: read it first.
8. If a screen differs from a click path here, stop and tell the studio lead. No click path in this sheet was checked on your accounts.
9. Before any command that prints a file (`cat`, `head`, `grep`) or before you paste anything to the studio lead: nobody films or shares your screen and no recording runs. If a printed line is a long string that looks like a key, do not copy it; send only "a key-like text is on the screen" and close the terminal window.
10. Values from the studio lead (path, name, number, command line): type them yourself character by character, do not paste. A path or name may hold only A-Z a-z 0-9 . _ / - and a full path starts with `/home/`. A setting name must match only A-Z 0-9 and `_` and must not contain KEY, TOKEN, SECRET or PASSWORD; otherwise stop. Anything else (a space, a quote, `;`, `$`, a backtick, `|`, `&`, `<`, `>`, `(`, `)`, `*`, `?`, `~`, `\`, `..`, a leading `-`, a line break): do not type it, tell the studio lead. Put each path in double quotes. Before `shred` or `rm`, type `ls -l "<path>"` and `readlink -f "<path>"` on each path: any `->`, or a `readlink` line different from the path you typed, means stop. Also type `ls -ld "<secret folder>"` and stop if it shows `->`. Never delete a file that row 15 or 16 keeps on purpose.
11. In the run window type only `y`, `n` (to end at the first question), the 6-digit number with the run name, `end`, and later, with the `$` back, `echo $?`. Nothing else, and do not press Enter to wake it up. The n8n stop line goes only in a second, separate window.
12. After any exit code other than 0, at any step: delete nothing, do not start again, send the number and the last printed line, wait.
Made-up example of a filled command (type your own values, not these): `grep -E '^EXAMPLE_NAME=' "/home/example/runs/settings.env"`.

## Step 0. HubSpot check (once, before step A; no model call)

> **WARNING. Step 0 writes live to your HubSpot test account: it creates ONE made-up contact (an address at `example.com`), changes two fields on it, reads it back and tries to delete it. The HubSpot key is read from its file into that one command only. No model call, no money. It needs the message "go step 0"; your general go-ahead does not cover it. If you stop for any reason after you typed the line of 0.4: type `unset HUBSPOT_PROBE_TOKEN` and Enter, close the terminal window, tell the studio lead.**

Why: it shows that the HubSpot key and the call kinds (read, create, change) work before money is spent. The planned calls (the studio lead expects 7) are listed by `--plan`. The step 0 program's own "delete" line only cleans up after itself; the main program never deletes contacts (go condition 5).
The key needs permission to read, create and change contacts: open the private app's page in HubSpot and compare its permission names with row 14; only exactly those.
**0.0 Go.** Wait for "go step 0" and the name of the HubSpot test account.
**0.1 Account.** Open HubSpot in your normal browser profile (nothing is filmed). Compare the account NAME (not the number) with the name in the go message. Differs or missing: stop. Matches: type "HubSpot is the test account" and wait for the reply.
**0.2 Checksums.** In WSL type the `cd` line from the studio lead, then `sha256sum <each file on row 14>`. Compare each code with row 14: every character if you can; at least the first 8, the last 8 and the length. Any difference: stop.
**0.3 Plan.** `python3 -I scripts/hubspot_probe.py --plan`. You should see "planned calls: N" with N and the one host as on row 14; it calls nothing. Anything else: stop. If `python3` is not found, stop; do not try `python`.
**0.4 Check.** One line, with the full key path and N from row 14: `HUBSPOT_PROBE_TOKEN="$(cat "<key path from row 14>")" python3 -I scripts/hubspot_probe.py --yes-spend-calls N > ~/hadavin-step0-result.txt 2>&1; echo $?` (the words "spend calls" mean "make these calls", not model money). Only one number shows: the exit code. Note it. "No such file", or a long string on screen (rule 9): stop.
**0.5 Filter, then read.** Type these two lines (nothing is printed except a count; each should print 0):
`grep -cE '[A-Za-z0-9_-]{30,}' ~/hadavin-step0-result.txt`
`grep -oE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+' ~/hadavin-step0-result.txt | grep -vcE '@example\.com$'`
If a count is not 0: look at the matching lines yourself (rule 9), then tell the studio lead only "filter count 1: a key-like text" or "filter count 1: harmless, <what kind>"; paste nothing. (A key: the studio lead names the HubSpot private app to delete. Real-looking addresses or a key mean paste nothing.) The filter does not catch names or account numbers: you read the file before you send it. If both counts are 0: rule 9, then `cat ~/hadavin-step0-result.txt`, and send the studio lead only the PASS, FAIL or SKIPPED lines and the exit code from 0.4. **Exit code 0 does not mean the paths work**: it means no line says FAIL; SKIPPED also gives 0.
**0.6 Answer.** The studio lead replies one of: "paths work" (owners read, contact create, owner change, lead-status change and read-back all PASS; "lead-status" is a HubSpot field that holds a contact's sales stage; the "delete" line does not matter), "a path failed" (any of those is FAIL or SKIPPED, or exit 1 with "NOT NEEDED (nothing was created)"; give no yes until the studio lead says in writing what happens next), or "unknown" (wait). Then `rm -- ~/hadavin-step0-result.txt`.
**Leftover from step 0.** If the "delete" line says FAIL or SKIPPED, the studio lead names the one made-up contact by its `@example.com` address; only then delete it by hand in HubSpot (search the address, tick that one, More, Delete).
If you stop in step 0 for any reason (number not N, checksum differs, "No such file", "refused", a key-like text, a path not in the printed form): `unset HUBSPOT_PROBE_TOKEN`, close the terminal window, tell the studio lead.

## Step A. Model key, money figures and the written yes (once per paid run)

**A.0 Create the model key yourself.** In the model account (address from the studio lead's message, typed by hand) create a new key used only for this run (and its trial run), and save it in the model key file that row 8 names. Send the studio lead only the key's name (as shown in the account's list, never its value) and the path of the file. The studio lead never makes, sees or receives the key. The studio lead then restarts the model program with this file and tells you the time (go condition 6). If you cannot create the key: tell the studio lead; do not proceed.
The studio lead's step A message holds: the model name; the most tokens one call may send and receive; the two prices per million tokens; the address of the model company's price page; the worst-case price per call and the run total; the address of the model account page; the two setting names and values, and the path of the model settings file (it must equal row 8); the sender, the receiver (masked: first 2 letters, then the domain, and the last letter before the `@`) and the HubSpot account name; whether this program version prints the masked sender and receiver on the notice; the planned stop time 2026-11-23 18:29 UTC = 23:59 IST; the rehearsal result file path and its exact first line; step 0's answer (or the reason, which you quote in your yes); the written confirmations of go conditions 4 and 5; the date by which the key is cancelled.
Then you do these checks yourself:
1. **Settings.** Rule 9, then, for each of the two setting names, one command: `grep -E '^<name>=' "<model settings file path>"`. Only that line prints. The stop time must be 2026-11-23 18:29 UTC; the backstop must equal the studio lead's message. Any other line, or a long string: stop. The program does not print these figures, so this is your only look.
2. **Price.** Type the price page address by hand, find the model, compare the two prices with the message, compute (most tokens in x input price + most tokens out x output price) / 1,000,000 on a calculator. It must equal the worst-case price per call. (A token is a small piece of a word; the model company charges by tokens.)
3. **Money rule.** Read the balance and the money used so far on the usage page; apply the balance check and the backstop check. Write the numbers down; you read them again in F.2.
4. **Rehearsal.** `head -n 1 "<rehearsal result file path>"`; compare with the first line in the message. Different: answer no.
5. **Accounts.** The masked values and the HubSpot name in the message must be your own throwaway accounts (you check them properly in C.4).
Answer in one line, for example: "Yes, run <run name>: 3 paid model calls planned, worst-case total US$<run total>, backstop US$<value I read>, balance US$<value>, used so far US$<value>, stop time 2026-11-23 18:29 UTC = 23:59 IST." One yes covers ONE run; a trial run is a run. A message with no numbers: answer no. Do not give the yes until step 0 is "paths work" (or its quoted reason). If the program does not print the masked sender and receiver on the notice, add: "the program does not show me the accounts; I rely on the studio lead's message". If the message does not say whether it prints them: answer no.

## Step B. Run-day laptop settings

Plug in. Windows 11: Start, Settings, System, Power & battery, Screen, sleep & hibernate timeouts: for "plugged in", sleep = Never. Control Panel, Hardware and Sound, Power Options, "Choose what closing the lid does": plugged in = Do nothing, save. Close programs that show addresses or notifications. The new settings should show when you reopen each screen. Set both back in I.7.

## Step C. Run day, before the go

**C.1 Receiver.** Open the receiver Gmail; click the label `demo` (hidden? click "More"): empty; Inbox: empty. Send "label and inbox empty". Mail in it, or no label `demo`: do not start; tell the studio lead.
**C.2 Film profile.** In Chrome: account picture top right, Add, "Continue without an account", name `demo-take` (or use it if it exists). In it sign in only to the HubSpot test account and the receiver account. Nothing else. Send "profile ready".
**C.3 n8n credentials list (look only).** Sign in to n8n with your own n8n account at the address on row 9, in your normal profile (never ports 5678 or 5679, which are your own n8n). Open only the list of credentials: read the names only, open none. There must be exactly two (the HubSpot key and the sender's mail login) and none named like a model, Claude or Anthropic key. Otherwise stop and tell the studio lead. Do not type a connection value into n8n; if a screen asks for one, stop and ask (the appendix holds the one old procedure the studio lead may release).
**C.4 Your own accounts check.** In your normal profile (not `demo-take`), nothing filmed: sign in to the receiver Gmail and read the account name at the account picture menu; sign out; sign in to the sender Gmail (it asks for your password and a 2-step prompt on your phone; have the phone ready) and read the account name; sign out; open the HubSpot test account page and read its name. Compare each with the masked values and the name in the step A message. Send exactly: "receiver, sender and HubSpot are the throwaway accounts". The studio lead's reply "throwaway confirmed" only shows your message arrived; the check itself is yours, because the program does not show the accounts. Doubt: say so and do not start.

## Step D. What the film may show (before the run, and again on the finished video in H)

Check in the `demo-take` profile that none of these shows an address other than `take-<run name>-a@example.com`, `-b@` and `-c@`:
1. The receiver mail LIST only: do not click or hover your account picture, do not open a mail or "show details". A list row showing another address: tell the studio lead. A Gmail tab title may carry your address (for example "Inbox (1) - <address>"): crop or retake; never film that tab visible.
2. Never film the sender mailbox or its "Send mail as" settings.
3. Tab titles and address bars that carry an address.
4. n8n's list of runs only if it is a film screen: made-up names, test addresses, no old run. Do not open the detail of the mail-sending step (it may show the company address) until the studio lead says it is safe.
5. The proof screen (a rehearsal screenshot or the n8n Postgres preview, never a live table screen; test addresses and counts only). The studio lead makes it from the rehearsal and gives it to the person on row 4 who edits; you film nothing for it.
6. Terminal windows: no address in the prompt, history or settings output.
7. Notifications, pop-ups, the system tray.
8. **Account numbers.** None may show: HubSpot's account number (HubSpot's address bar always carries it, and the page header too), the account picture menu in HubSpot, Gmail or n8n, n8n's account or project name, your n8n address or login. Default: the person on row 4 who edits crops the address bar out of every frame; you check that on the finished video in H.
9. The HubSpot contact list: step 0's made-up contact must be gone (delete it by hand first).
Tell the studio lead if any other address or any account number is visible; the footage is cropped or retaken before use.

## Step E. The real run

> **WARNING. After you type the confirmation line (E.5) the program makes the planned 3 paid model calls (real money), writes real contacts to the HubSpot test account and sends real mails from the sender Gmail to the receiver Gmail. None of this can be undone and the money is not refunded. Anything that holds the model key could spend more than your yes until the key is cancelled (I.0). The sheet cannot show that nothing is spent before both typed answers: the account balance and the model key are the real limits. If you are unsure about anything: at the first question type `n` and Enter. The program sends nothing and ends. Do not leave the question waiting.**

**E.0 Have ready:** WSL open and the `cd` line typed (you are in the run folder); steps C.1 to C.4 and D done; the rehearsal result named and read; the written yes acknowledged; the go message "go real run <run name>" (or trial) received with all go conditions; the start before the latest start time on row 3 (the clock keeps running while you check; the program refuses a start that is too close to the stop time, and at the default setting the latest start is before 18:14:40 UTC = 23:44:40 IST; row 3 gives the exact time); the person on row 5 has a second, separate Ubuntu window open (side by side; if you are that person, type `echo SECOND WINDOW` in it now, before you start the program, so you can tell the windows apart; never type that in the run window) with the exact line ready; the person on row 4 is ready. Then re-read the two setting lines as in A.1: unchanged, and the studio lead's restart time (go condition 6) is later than the file's last change. And `sha256sum scripts/run_real_check_n8n.py`: it must equal row 14; if it differs, do not start.
**E.1 Start.** The studio lead sends one line of this exact form: `python3 -I scripts/run_real_check_n8n.py --take <run settings file>` (the run name is in that file). Type it and Enter. You should see, in order: `mailbox login: still works` and `HubSpot login: still works` (anything else: nothing was sent; tell the studio lead; do not start again, not even once, until told, because repeated failed logins can trigger a Google alert); then the notice; then "Type y to start".
**E.2 Compare the notice.** The notice shows 3 test people, the planned model calls and the worst-case price, up to 3 mails, n8n stopped once, the stop time. It does not show the backstop or the money used. Made-up example (every number is invented, and the real layout may differ; compare numbers and names, not the layout):
```
  Test people: 3        Model calls planned: 3
  Worst-case price per call: US$0.0123    Worst-case total: US$0.0369
  Mails: up to 3        n8n stopped and started: once
  Stop time: 2026-11-23 18:29 UTC = 23:59 IST     Run name: example
  Confirmation number: 123456 (type it, a space and the run name)
  Type y to start
```
At "Type y to start" type `n` and Enter, and tell the studio lead, if ANY of these is true: the price per call is not the one in the message and your yes; the total is not 3 times it or is more than your yes; you cannot find a line; the stop time differs; people, calls or mails are more than 3; the run name (if shown) is not yours; the notice prints masked accounts and they are not your two throwaway accounts (first 2 letters, domain, last letter); the message said it prints them and the notice does not. The real protection is your own A.1 reading, your yes and the balance (money rule).
**E.3 `y`.** If E.2 passed, type `y` and Enter yourself at once. A `y` fed in by another program is refused on purpose; closed input ends the run with exit code 2 and nothing is sent. The flags `--yes` and `-y` do not exist.
**E.4 Confirmation line.** Type the 6-digit number from the notice, a space, your run name, Enter (example `123456 example`). An answer faster than the minimum think time (2 seconds unless the studio lead changed it) ends the run with exit code 2. A wrong line ends it with exit code 1 and nothing is sent; the studio lead says whether the run name can be used again (the marker file `~/.hadavin-take-tags/<run name>.used` is written only after a correct line; `ls ~/.hadavin-take-tags` shows used names). Then send "run started". The studio lead gives the cues: row 5 stops and restarts n8n, row 4 films. No name on row 4 or 5: no run.
**What is normal.** The program, not you, sends the 13 sends: A twice, B ten times at once, C once while n8n is stopped and started again, treating each person once (planned: the claim the video makes is only that a lead sent twice with the same id inside the lease is processed once). Contacts appear in HubSpot, mails in the label `demo`. The run card gives the normal length. The model program keeps running during the film pause. The program prints its result only after you type `end`. If nothing new prints for longer than row 12 says, before the film-pause text, tell the studio lead and wait: no Ctrl-C, no closing. Tell the studio lead if a number is not what you approved, a count is wrong or the laptop sleeps.

## Step F. Film pause, `end`, finish, contacts

> **WARNING. When the program asks for `end`: closing the terminal, Ctrl-C, or two wrong lines in a row ENDS the film pause early; a run stopped after the sends began ends with exit code 3. Type nothing else. Type exactly `end` (lower case), only when the contact list is filmed.**

**F.1 `end`.** The program prints a line asking you to film the contact list and type `end`. **If that line says it will delete or archive contacts, stop: type nothing, do not close the window, tell the studio lead and wait** (go condition 5 should have excluded this). The person on row 4 films the HubSpot contact list. To find this run's contacts search HubSpot Contacts for `take-<run name>`; if nothing shows, sort by create date, newest first, and look at the newest 2 or 3 (not checked: HubSpot's search behaviour). You should see 2 or 3 contacts (C may be "unknown"). No contacts or another number: tell the studio lead and do not type `end`. If the film or the search lasts longer than the minutes on row 12, tell the studio lead; still do not close or press Ctrl-C. When the person on row 4 says "filmed" (or you filmed it), type `end` and Enter. Any other line makes it print "type exactly: end" once more; a second wrong line also ends the pause. The program then prints its result and the `$` returns.
**F.2 Finish.** With `$` back: `echo $?`. Open the model usage page: apply the money rule (balance and money used now). Send the studio lead: the exit code, the last printed line, and the balance and money used before and after. Read the printed result yourself: A and B each have one contact and one mail. Any code other than 0: rule 12; if the code is 3 and only C is "unknown", wait for the studio lead's written statement (go condition 7). Money used more than your run total: emergency cancel (money rule). The studio lead then stops the model program and says "model program stopped".
**F.3 Delete the contacts by hand.** The program deletes nothing. The studio lead sends the list of leftover contacts by person id and contact id (masked). In HubSpot (account name checked), search your run name, tick each listed contact one by one (never the select-all box), More, Delete. Only contacts whose address carries this run name and that are on the list; if the number ticked differs from the list, stop. Send "contacts deleted" and the number. HubSpot may keep an archived copy.

## Step T (trial run, only if row 6 says yes) and step G (failed run or after a trial)

A trial run is a real run: its own "go trial run", its own written yes (step A), its own new run name, the boxed warnings of E and F, then step G. The trial's money counts as "used so far" in the next yes. Nothing from a trial is filmed or posted. The key is not cancelled after a trial (no "no more runs"). Afterwards the real run needs a new yes, a new run name and a fresh C.1.

> **WARNING before step G. Delete ONLY demo mails in the receiver account and ONLY HubSpot contacts of the failed or trial run (the studio lead gives the count and run name). Before each delete check the account shown. If the Trash holds anything other than these demo mails, do NOT empty it; tell the studio lead. Never delete the marker file.**

**G.** The studio lead says why. (1) In the receiver Gmail open the label `demo` and the Inbox; tick only the demo mails one by one (subject starts with `[demo] lead`, where "lead" is a made-up sales contact); never "Select all conversations"; Trash icon; open Trash: only those mails, else stop; then "Empty Trash now". Gmail's Archive button is never used. (2) In HubSpot delete leftover contacts as in F.3, only as many as the studio lead counted. (3) Send "demo mails deleted" and the number of contacts. (4) Give a new written yes and a new run name. A run that got past both typed answers has used its name, even if it failed. If C was "unknown", the studio lead says whether a contact or an alert mail may remain and where the alert mail goes; until then delete only what it counted. If a new run is no longer possible before the stop time, none happens.

## Step I.0. Cancel the model key (first thing after the last run, before step H)

> **WARNING. Cancelling cannot be undone. Cancel only the key the studio lead names by its name, in the model account whose name matches the message.**

Do it when the studio lead has said "model program stopped" and "no more runs". (If a failed run will be repeated, the key stays; the balance is then the only limit; tell the studio lead. If the edited video is later rejected and a new run is needed, you create a new key as in A.0 and give a new yes.) (1) Open the model account (address typed by hand); check the account name. (2) Open the list of keys, find the named key (by name, never value), delete it, check it is gone. (3) Send "model key cancelled". The credit left stays in the account. Row 16 may keep the key with a reason and end date; with no end date it is cancelled by the stop time Mon 23 Nov 2026 18:29 UTC = 23:59 IST. The retire check cannot see the model key. Read the usage page once more now (money rule, largest figure counts) and send the figure.

## Step H. You watch the edited video

Deadline: row 7 (UTC and IST). Watch it twice: once at full speed, once pausing on each cut, and apply step D items 1 to 9. Reply "accepted" or list the bad seconds with times; if a real address or account number shows, say "an address is visible" and the second. Clean-up starts only after "accepted" and the studio lead's "last run is done". After clean-up starts, no run happens.

> **WARNING before step I. Deletes and cancellations here cannot be undone. Remove only what the studio lead's confirmed list names AND what rows 8, 15 and 16 allow. Before each delete check the account shown (your normal profile may be signed in to real accounts). Never delete `~/.hadavin-take-tags/<run name>.used`. Keep the secret files until the retire check succeeded (or I.4 says what to do instead). If anything is unclear, remove nothing and tell the studio lead. (I.0 is not held back by this.)**

## Step I. Clean-up (deadline: row 7; use your normal profile, nothing is filmed)

1. **I.1 Revoke app passwords** named by the studio lead, in both accounts: sign in to the receiver, do this, sign out; sign in to the sender (own password and 2-step), do it again. myaccount.google.com, Security, App passwords (2-Step Verification is already on). Revoke only the listed names (the bin or "Remove"); a name not on the list is left alone and its name sent to the studio lead. Screenshot each list after, cropping any address or name. Delete the uncropped originals the same day (Snipping Tool: Start, type `Snipping`; originals may sit in Pictures, `Screenshots`), and empty the Windows Recycle Bin (and OneDrive's, if Pictures syncs). The copy inside n8n ends only by this revocation.
2. **I.2 HubSpot private apps** (only if row 15 says the key is deleted, after the studio lead's list): check the account name; Settings, Integrations, Private Apps; look at each app's name and creation date. Cannot tell which app the program used: delete nothing, send the names. Deleting cannot be undone and stops anything using that key (n8n's HubSpot connection too). Screenshot (crop), send the names. If row 15 says the key is kept on purpose, delete none; the HubSpot line of I.4 will say "STILL WORKS", which is expected.
3. **I.3 Screenshots** (only if row 13 says yes): save in `C:\Users\<your user name>\Downloads\Hadavin_local\real-run\` under the names the studio lead gives.
4. **I.4 Retire check.** The studio lead sends: `python3 -I scripts/run_real_check_n8n.py --retire-check <run settings file>` and the folder. Run it BEFORE the secret files are removed (the studio lead keeps the run settings file and folder until it succeeded). Then `echo $?`; send the printed words and the code. It tries to log in with the revoked keys (two tests only: the mailbox and HubSpot; not the model key, not the database passwords) and Google may count each as a failed sign-in. **At most 3 runs of it in all, counting every run whatever the outcome; ask before a 4th.**

| It prints (code) | Row 15 says | You do |
|---|---|---|
| both "refused as expected" (0) | any | send "retire check succeeded" |
| mailbox "STILL WORKS" (3) | app password revoked | revoke again (I.1), run again |
| mailbox "STILL WORKS" (3) | kept on purpose | expected; counts as succeeded only if HubSpot is "refused as expected"; the studio lead says "retire check succeeded, mailbox app password kept on purpose" |
| HubSpot "STILL WORKS" (3) | key deleted | delete the private app again (I.2), run again |
| HubSpot "STILL WORKS" (3) | kept on purpose | counts only if the mailbox is "refused as expected"; the studio lead says "retire check succeeded, HubSpot key kept on purpose" |
| both kept on purpose | both | the studio lead writes "retire check not required: kept on purpose" and the end date; I.6 covers only the files it lists |
| "could not tell" (2) | any | wait for the studio lead |

If the check cannot succeed (code 2 twice, a row missing, or the studio lead cannot say what counts): keep every secret file, remove nothing more, tell the studio lead; it writes down what is left and the date to finish. Never remove secret files to get past this.
5. **I.5 n8n, container, database passwords:** after "retire check succeeded" the studio lead (not you) removes n8n's connections and saved runs, stops n8n, removes the run folder and the database container, and tells you what happens to the database passwords. You do nothing until told.
6. **I.6 Remove secret files.** The studio lead sends full paths. For each: it starts with the secret folder of row 8; its last name is in row 8; it does not end `.used`; not under `~/.hadavin-take-tags`; not the run settings file; not kept on purpose; not the model key file unless I.0 is done. Any failure: remove nothing. Then (rule 10) `ls -l "<path>"`, `readlink -f "<path>"` and `ls -ld "<secret folder>"`; any `->` or different `readlink`: stop. Names must match row 8 and the studio lead's list. Then `shred -u -- "<path>" "<path>"` (if "command not found": `rm -- "<path>" "<path>"`). Then `ls -l "<secret folder>"`: the files are gone. Send "secret files removed". A leftover lock file: appendix, "Other refusals".
7. **I.7 Laptop back.** Sleep and lid settings back; sign out of `demo-take`.

## Step J. Post (latest post time: Wed 25 Nov 2026 15:00 UTC = 20:30 IST, taken from the earlier sheet; the studio lead confirms it on row 7)

> **WARNING. A public post cannot be taken back. If you are unsure about any word, number or claim: do not post; tell the studio lead.**

You post; Claude never posts. Post only if ALL are true: the exit code is one the studio lead's go condition 7 counts as success; you read the printed result yourself and A and B came out right; the studio lead confirmed both in writing. The post may contain no number and no claim the printed result does not show.
It says only: contacts arrive through n8n; n8n writes the HubSpot contact and sends the mail. The claim is exactly: **a lead sent twice with the same id inside the lease is processed once** (the lease is the time n8n holds a claim on an id; after it ends the same id could be processed again, so the post must not say more), allowed only if the studio lead confirms in writing that the printed result shows it for this run. Three more sentences are allowed only if the printed result shows them for this run: our code asks the model at most once per test person; each paid call is written down before it is made; the program counts the mails and contacts. Do not repeat the send counts unless the printed result shows exactly them.
**Open the appendix section "J. What the post must NOT say" and read every line before you post.** Someone other than the writer checks the post against it (row 11 names who). The exact final words come from the studio lead after the rehearsal; until then do not post. After posting, send "posted".
