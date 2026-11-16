# Owner appendix v29, sheet A: the long detail (it binds you the same as the sheet; each part says where the sheet points to it)

## Appendix part 1: The words in full (every definition of the sheet)
**The words.**
- **UTC** = world clock time. **IST** = UTC + 5:30; your phone alarms use IST. **UNVERIFIED** = nobody has run or seen it (every vendor page, button, Windows, WSL, n8n and HubSpot step, and every printed wording, is UNVERIFIED); if what you see differs, stop (STOP RULE below), except **tolerated** items (marked at each step; only button, menu and page-path wording): describe it and proceed. A difference in a number, name, count, account, time or key state is never tolerated.
- **Lead** = the AI session (an AI, not a person) in the chat where you got this sheet; that chat is the **message place**: a message from anywhere else is not accepted. The lead sends the **numbers message** (every value for this run; sample in section 3); you check it by hand, type a yes and wait for "go". A **run name** is 4 to 12 lowercase letters and digits, starting with a letter, never used before. The **other channel** and the **backup person** (a human you can call who can reach whoever runs the lead) are named in the numbers message; none named: no run.
- **WSL** = the Ubuntu window inside Windows (Start menu, type Ubuntu, Enter). The **test terminal** and **read terminal** (card words) are two WSL windows; the read terminal is for `date -u`, `ls -l`, `clear` and the grep of 5.7 only.
- **Send** = type in the message place and press Enter. **Describe** = send which step you are at, what kind of line you see and plain numbers. Never copy, type or photograph a key, app password, long random-looking text or real mail address (the one copy at 6.3 and the paste at 6.4 are the only exception). **Set phrase** = words you send exactly (list ends section 2). **Run** as a verb = type a command and press Enter; a **run** = this one filmed attempt. **Key** alone = a model key; the words take in `take-` and `--take` are plain text.
- **Clean-up message** = the lead's message after the run (8.2) with the lists to delete and revoke.
- **Model key** = a key to the paid model's account; it lets a program spend money; it is **alive** from the create press until card step 5 is done. **Model account** = the paid model company's account where you pay and make keys; open it only from your own bookmark or an address you type. **Key list** = its page that lists keys with name, creation time, last-used time and a **state word** (the word that says whether a key works). **Per-key limit** = a spending cap on one key, if the create form offers one (the message says "none exists" otherwise). **Key scopes** = the permission list on the create form (the message names the ones to choose). **Tokens** = small pieces of text a model reads or writes (a word is about 1.3 tokens). **Run day** is a UTC date: after 18:30 UTC your phone's IST date is already the next day. The **test program** (started by you) sends three made-up people through **n8n** (a ready-made linking tool) into **HubSpot** (a ready-made customer-record service; here a free test account): one **contact** (customer record) and one mail per person. **Older key** = a paid-model key you saved earlier, if the numbers message names one. **Valid key** = any key whose state word is not the cancelled word (a state word you cannot judge counts as valid; an older key can be valid without being alive). **Look key** = a throwaway key `look-<run name>` you make at 5.9 only to see the real cancel words; it is a real key, alive until card step 4 is done for it. **Cancelled word** = the state word of a cancelled key (or "row gone"); the message gives a word or "from the look key" (the lead cannot see your screen); you see the real word at 5.9 and the lead answers "confirmed"; a word that differs from a given sample: no run.
- **Film pause** = the wait while the film person films; it starts at the **film cue** (a printed line copied in the numbers message, or minutes after you sent "run started"). **Recording OFF** = every screen recording or sharing is off. **Privacy switches** = Windows Clipboard history, Sync across your devices, Recall. **Film profile** = the Chrome profile `demo-take` (5.5). The numbers message names the film person, the **editor** (cuts the film) and the **post checker** (compares your post with the sentences); you are none of them.
- **Demo mail** = a mail in the receiver Gmail under label `demo` that R7 allows you to delete. **Throwaway accounts** = the receiver Gmail (gets the demo mails), the sender Gmail (sends them) and the HubSpot test account you made earlier, never your real mailbox. **App passwords** = Gmail passwords made for one application; **HubSpot app secrets** = secret values of the small HubSpot programs ("private apps") that n8n's workflows use to write contacts. **Shell prompt** = the line ending in `$` in an Ubuntu window where you can type a command. **The y question** = the line `Type y to start`. **Paste line** = `paste key, Enter:`. **Step** = a numbered item such as 6.3; **window** = a program window on your screen; **profile** = a Chrome profile.
- **Made-up people** = person A, B and C, with addresses `take-<run name>-a@example.com` (`-b@`, `-c@`); **submitted N times** = the test program sends that person's sign-up N times on purpose; **person id** = the made-up code the program gives that person (not an address); a printed line "unknown" for C is allowed (the program could not confirm that one); the **prep contact** = one extra practice contact. **Key file** = the file in WSL holding the model key. **Model program** = the lead's software that sends the made-up people's text to the paid model with your key; you never edit its settings. The lead starts and stops it on your laptop (it shares your Linux user, R1); **"restarted"** = the lead's word that it started again and now reads the key file. **Spend lock** = a lock that stops the model program making paid calls until the test program has accepted your challenge; "NOT SHOWN" = nobody has shown it exists, so the model program might spend between "restarted" and your `y` (the yes names this).
- **Money.** **Prepaid** = you pay first and calls draw it down; **auto-reload** = the account tops itself up when low (must be off). **Balance** = the whole prepaid amount: the most you can lose. **Last-resort step** = one action in the model account that only stops spending; the numbers message names it and says whether it can be undone (UNVERIFIED).
- **Times** (all in the numbers message). **Run day** = the one day of the run, as in `Wed 18 Nov 2026`. **Deadline** = the end of the period your spending approval covers, Mon 23 Nov 2026 18:29 UTC = 23:59 IST: after it nothing may spend. **Earliest key time**: before it you do not press create of the run key (the look key of 5.9 is made after "go", also before it). **Latest start** (card words; 7.3). **Take folder** = the WSL folder the message names (it holds the test program). **Run length** = the minutes the test program is expected to run from your `y` to the waiting line (the message states it). **Give-up minutes** = how long the test program waits for `end`, counted from your "run started", before it gives up. **Alarm time** and **cancel-by time** = when the run should be over, and the backup; **silence minutes** = how long the test terminal may print nothing before it counts as stuck. **FREEZE** = type and close nothing more in the test terminal (except `n` at "Type y to start"); in the read terminal run only `date -u` and `ls -l "<path from the message>"`; in the browser do only the card (its list L2 included, at 7.11) and the deleting R7 allows; describe; wait for the lead's word "continue". FREEZE is not a cancel: a live key is cancelled only by a danger sign (W1 to W9 on the card); a run whose key was alive ends after the card: no word resumes it. A FREEZE never stops 7.11: the older key is cancelled by the older-key time even while frozen (the card's list L2 is allowed in a FREEZE), and alarm 4 rings during a FREEZE too. "Continue" = the lead's word that you may go on to the next step (7.9 or 8.1) after a FREEZE in which no key was alive; it never resumes a run whose key was alive.

## Appendix part 2: The sample numbers message (made-up values, never real)
SAMPLE (made-up values, never real):
```
Run name: demo7   Run day: Wed 18 Nov 2026   REAL run (paid model calls happen)   Earliest key time: 10:30 UTC = 16:00 IST
Sheet letter: A   Older key: "studio-key-1" made 2026-11-10, last used [OWNER FILLS: older key last-used time], no file the lead read uses it (or "none"; "unknown" means no run)   Older-key time: 16:00 UTC = 21:30 IST on the run day
Message place: this chat   Other channel: <name and how>   Backup person: <name and how to call>   Date you decided to use the existing balance: <date>
Button words: [OWNER FILLS: cancel button word and confirmation box word, from the look key at 5.9]   Cancelled word: [OWNER FILLS: cancelled word and where you saw it] (the lead's row may only give a sample or "from the look key"; UNVERIFIED; the lead answers "confirmed")   Key scopes: <scopes the key page offers>   Last-resort step: [LEAD FILLS at re-pin: last-resort step] (can it be undone: <yes or no>)   Key list time zone: <zone>   Model settings file: <model settings file>
Key file: <key file>   Take folder: <folder path>   cd line: <the cd line>   Key list address: <address>   Prepaid page address: <address>
Accounts: model company and account <name>, receiver Gmail <name>, sender Gmail <name>, HubSpot test <name>   Masked in the notice: receiver <masked address>, sender <masked address>   Gap before 8.1: <minutes>
Start line: python3 -I scripts/run_real_check_n8n.py --take <test settings file name>   Spend lock: shown (or NOT SHOWN)   Key file size in bytes: <range> (UNVERIFIED)   Test program asks you to type a figure: no   Model key outside the model program: none (the lead checked n8n's credential store and shows it)   n8n credentials: exactly the three, by name: [LEAD FILLS at re-pin: the three names] (the lead read n8n's own credential list)
Model: model-x   Tokens in and out per call: 40000 and 10000   Prices per million: in USD 3.00, out USD 15.00   Price page: <page address>   Price per call at full size: USD 0.27   Call ceiling (the lead's figure): 3   Expected total: USD 0.81 (not a limit)   Per-key limit: none exists
Balance on the prepaid page: USD 189.00   Auto-reload (the lead's reading): off
Settings to compare, each name = value (unit): MODEL_NAME = model-x | TOKENS_IN = 40000 | TOKENS_OUT = 10000 | PRICE_IN_CENTS = 300 | PRICE_OUT_CENTS = 1500 (US cents per million tokens) | CALL_CEILING = 3 | DEADLINE = 2026-11-23T18:29:00Z
Minutes at "Type y to start": 5   Minimum think time: [LEAD FILLS at re-pin: minimum think time] seconds   Run length: [LEAD FILLS at re-pin: run length] minutes (the made-up times of this sample assume 15)   Film pause: 10   Latest start: 11:30 UTC = 17:00 IST   Alarm time: 12:00 UTC = 17:30 IST   Cancel-by time: 12:10 UTC = 17:40 IST   Silence minutes: 3   Give-up minutes: 40
Film cue: <the printed line, copied, or minutes after "run started">   Waiting line: <copied>   Demo mail subject start: <words>   Earlier demo mails expected: 0
People: film person <name>, editor <name>, post checker <name>   Recording tool: <name>   Posting place: <place>   Video by: <how>
Expected after the run (never changed after y): A submitted 2 times with the same person id, 1 contact, 1 mail; B submitted 10 times, 1 contact, 1 mail; C 1 contact, 1 mail (its printed line says "unknown": accepted); the HubSpot search for `take-<run name>` shows 3 contacts and the demo mail list 3 mails   Exit codes accepted: 0 only
The day in order: earliest key time 10:30 UTC = 16:00 IST, latest start 11:30 UTC = 17:00 IST, alarm time 12:00 UTC = 17:30 IST, cancel-by time 12:10 UTC = 17:40 IST, older-key time 16:00 UTC = 21:30 IST, deadline 18:29 UTC = 23:59 IST
Post sentences: <the lead's exact sentences, the only words you may post>
The yes sentence: <the lead's exact sentence>
If you cancel the key during the run or right after `end`, the test program: <lead's answer>; exit code accepted then: <number or none>
```

## Appendix part 3: Rules in full - the longer rule details
R6, the shape check of each filled-in part: : the start line is exactly `python3 -I scripts/run_real_check_n8n.py --take ` and one file name; paths, folders and file names use only letters, digits and `/ . _ -`, a path starts with `/home/`, has no `..` and no part starting with `.`; the key file name contains the run name and lies inside the Take folder of the message; none of ; & | $ () < > \ ' " * ? ~, a backtick, a space in a path or a line break appears (the fixed printed commands of 5.7, 6.4 and 8.1 are typed as printed, with their quotes and pipes; only their filled-in parts are checked)

R7, deleting contacts: Contacts: those in the clean-up message (addresses `take-<run name>-a@example.com`, `-b@` and `-c@` or `prep-<run name>@example.com`, the prep contact included): search the exact address, see exactly one result whose page shows it, then delete (a HubSpot delete is UNVERIFIED: treat it as final). 

R10, the silence rule: no new line in the test terminal for the silence minutes, counted only from your Enter on the start line until the notice, from your `y` until the challenge is printed, and from your challenge answer until you send "run started" (silence at the y question, before the film cue, in the film pause and while waiting for `end` is normal: the y minutes, the film cue, the alarms and the give-up minutes bound those)

## Appendix part 4: Steps 5 and 6 - click paths and page names (all UNVERIFIED, tolerated)
5.3: (Windows Settings, System, Power & battery; the lid: Control Panel, Power Options; UNVERIFIED, tolerated)

5.4: (Gmail on the web: gear icon, See all settings, Filters and Blocked Addresses, Create a new filter, subject words, Apply the label `demo`; Conversation view: See all settings, General, off; UNVERIFIED, tolerated; a filter matches words anywhere in the subject)

5.5: (click your profile picture at the top right, Add profile, Continue without an account, name it; UNVERIFIED, tolerated)

6.1: (Settings, System, Clipboard)

## Appendix part 5: Steps 7 to 10 - page and screen details
7.3: a masked address looks like `de…1@gmail.com`; match each by its first two letters, the character before the @ and the domain)

7.6, what the film person does (the film person's own page repeats it): They say "recording", turn Recording ON, film the two pages, say "filmed" and read both counts aloud, switch Recording OFF and leave.

7.7: (the recording tool's own window says stopped, and no red dot or "recording" text shows on the screen or taskbar; UNVERIFIED)

8.3: (Gmail on the web: account picture, Manage your Google Account, Security, 2-Step Verification, App passwords; UNVERIFIED, tolerated; sign that account in at `demo-take` for this step only)

8.4: (HubSpot: Settings (gear), Integrations, Private Apps; UNVERIFIED, tolerated)

## Appendix part 6: The words used on the card
Card, **Words on this card.** **Key list** = the model account page that lists keys with name, creation time, last-used time and a state word. **Alive** = from the moment you press the create button of the key list until step 5 is done (a look key: until step 4 is done). **Latest start**, **Lead**, **send**, **other channel**, **backup person**: as in the sheet. **Phone alarm** = one of the four alarms of 6.2. **Read terminal** = a second Ubuntu window where you only type `date -u`, `ls -l`, `clear` and the grep of 5.7. **Test terminal** = the Ubuntu window where the test program runs. **Normal profile** = the Chrome profile you always use. **Recording** = any screen recording or sharing.

## Appendix part 7: Why and background (rationale that is not a step)
5.1, why the 7-day rule: Why: sheet A cancels the older key, and a key used in the last 7 days probably still serves a program of yours; sheet B leaves it alone until the older-key time, so it can spend money until then (R4). 

5.1:  (not found: describe what the account menu shows and wait; nothing is alive; check the account name)

6.7:  (a new key can always be made; only a program that uses the older key would be hurt)

## Appendix part 8: Steps 6 and 7 - small notes
6.3 c:  (the page shows it once)

6.4:  Nothing shows while you paste; press Enter; the line `exit 0` appears;

7.4:  (the program refuses faster answers)

7.6:  (keep the chat, minimised; if the chat is in the film profile, move it before the film cue)

7.9:  (the **exit code**: 0 means the program says it passed; only codes the message accepts)

8.6:  (the lead's test that a revoked item refuses)

## Appendix part 9: The yes sentence pattern
In this pattern: "Yes, run <run name>: <call ceiling> expected paid model calls, expected total USD <expected total>, balance USD <the balance you read on the prepaid page>, auto-reload <the word you read, it must be off>, per-key limit <amount or none>, older key <its name or none>, older key last used <its last-used time, never or none>, last-resort step <step>. I will cancel the older key myself after my new model key is saved, or by <the older-key time of the message> on the run day at the latest if the run ends earlier, even if the lead is silent, and I understand this cancel cannot be undone. I accept the risks of R1 and R4: the look key and the run key are real keys that can spend until I cancel them; I could lose the whole balance, cancelling a key may not end the calls, the lead and the film person could read my key file, clipboard or screen, and the model program may spend before I type y unless the message says Spend lock shown. Deadline 2026-11-23 18:29 UTC = 23:59 IST."

## Appendix part 10: What you may type outside the shell
What you send or type outside the shell (the yes, set phrases, description text): letters, digits, single spaces and `. _ / - : = @ + , '` only; the lead's exact post sentences are posted as given, only after the post checker's written "matches the sentences" (section 10).

---
End of the appendix, sheet A (OWNER-APPENDIX-v29-A.md).
