# Your steps for the real take of the lead desk video (version 4)

Written Mon 16 Nov 2026 from version 3, the owner facts file of the same day, and the reviewed edit list. Nothing was run to write this. If something here differs from the lead's current plan, the plan wins; tell the lead.

This sheet holds only what ONLY YOU can do. Everything you already did is left out on purpose: the two throwaway Gmail accounts, the HubSpot test account and its keys, your n8n account, the model key and its credits, the push of the flows to the public repository, and the approval of the real take "once everything is ready". Do not redo any of it. The lead does everything else: the database, the model program, n8n, importing the flows, the rehearsal and the checks.

Lines that start with "To be decided by the lead:" are open points. Until the lead answers them, do what the line says and nothing more.

## Words used (read once)

- **The take**: one real recorded run on your own test accounts, with 3 made-up people (A, B, C). A is sent twice, B is sent ten times at once, C is sent once while the lead stops and restarts n8n.
- **n8n**: the tool that takes the leads in, writes the customer-list entry (the contact in HubSpot) and sends the mail. **The model program**: a small program of ours that asks the AI model once per lead and enforces the money limit. **The lead**: the Claude session that runs this with you.
- **Receiver**: the throwaway Gmail account that only receives the demo mails. **Sender**: the throwaway Gmail account n8n sends from.
- **The notice**: the screen of numbers the take program prints before it asks you to type `y`.
- **The rehearsal**: a full practice run on this laptop with stand-in programs, made-up data and no real account, no real key and no model call (cost: US$0). The lead runs it before any real take.
- **WSL**: the Linux (Ubuntu) window inside Windows where the take runs.
- **Removing the take's contacts**: at the end the take program deletes the made-up contacts it created in HubSpot (the program calls this "archive"; in the code it is a delete). Gmail's own "Archive" button is a different thing and is not used here.

## Rules that hold in every step

1. **Never send the lead** a password, token, key, mailbox address or the contents of any secret file. Send only short sentences. A file path is fine.
2. **The typed answers are yours alone**: the `y`, the 6-digit number with the take id, and `end`. The 6-digit number only blocks blind and piped answers. It does NOT stop a tool that reads the screen and types the number back. So never let any tool, script, assistant, agent or helper window read the screen and type for you. Run the take only on your laptop, in your own WSL window.
3. **Before every paid take you give a written yes WITH numbers** (step A). No numbers, no take. The spending limit and the window end are only settings in a file, a backstop that YOU check by eye before you say yes. The program does not enforce a fixed ceiling. The real protection against a loop or a double call is the design: one paid call per lead id, recorded before the call is made.
4. **You post. Claude never posts.**
5. On take days: laptop on mains power, sleep set to Never, "When I close the lid" set to Do nothing (step B). Set both back after the last take.

## Before a take

### Step A. The written yes with numbers (once per paid take)
The lead sends one message with: at most 3 model calls in this take; the worst-case cost per call (a dollar figure the lead reads from the model program's settings; the program only checks that it is a number above zero, so you judge whether it is sensible); 3 times that figure; the money spent so far; the spending limit and the window end as they stand in the settings (you look at those two values yourself on the lead's screen); and the planned window end **2026-11-23 18:29 UTC = 23:59 IST**. The message also says whether the rehearsal has passed and names its result file. No rehearsal pass, no take.
You answer in one line, for example: "Yes, take <name>, up to 3 calls and up to US$X, window ends 2026-11-23 23:59 IST." A yes covers ONE take. No numbers in the message means answer no.
- To be decided by the lead: the exact order of the rehearsal and any practice run on your real throwaway accounts (the lead's earlier plan had both; the rehearsal does not prove real Gmail or HubSpot). You do nothing for the rehearsal.

### Step B. Take-day laptop settings
Mains power plugged in, sleep Never, "When I close the lid" Do nothing. Close other programs that show addresses or alerts. Set the settings back after the last take.

### Step C. Check the receiver mailbox and the new n8n (take day, before the lead says go)
1. In the receiver account: the Gmail label `demo` is empty and the Inbox is empty. Tell the lead "label and inbox empty". If the label holds mail, tell the lead and do not start. (The take reads only the label `demo`.)
2. Possible, only if the lead asks: n8n for the take is a fresh n8n, so it may ask you to create an owner login on its first screen and may need the three connections (HubSpot, mail sending, database) typed in again. If the lead asks, you type any password yourself, into the n8n screen, never into chat, and tell the lead only "done".
   - To be decided by the lead: whether the take's fresh n8n needs this first-visit login and these connections at all, which address and password to use, and who switches the flows on. The database login for n8n is a limited one (it may only read, add and change the rows of the lead table, never the administrator login); who creates its password and who types it is not decided.
   - To be decided by the lead: the address you open n8n at. The rehearsal used `http://localhost:5690`; ports 5678 and 5679 are your own n8n and the rehearsal does not touch them. The port for the real take is not yet chosen. Not yet checked: whether your Windows browser reaches n8n inside WSL (the lead re-checks this).
   - Stop and tell the lead: n8n shows a saved secret in clear text on screen or in an export.

## The take

### Step D. Start the take and type `y`
In your own WSL window, take folder open, fresh browser profile (step F), laptop on mains. The lead gives you the one line to run (form: `python scripts/run_real_check_n8n.py --take <take config>`). What you will see, in this order:
1. The program prints `mailbox login: still works` and `HubSpot login: still works`. A bad login stops the take here, before you type anything.
2. The notice, which already shows the random 6-digit "Confirmation number (type it, a space and the take id)".
3. "Type y to start".
4. "Now type the confirmation number shown above, a space and the take id to confirm:".

Read the notice: 3 people, up to 3 model calls and the worst case, up to 3 contacts removed at the end, up to 3 mails, n8n stopped once by hand. Type `y` and Enter **yourself**. A piped or scripted `y` is refused on purpose; closed input ends the take with exit code 2 and nothing is sent. The flags `--yes` and `-y` do not exist.
- Then type the 6-digit number the notice showed (new every take), a space, the take id, and Enter, for example `123456 <take id>`. An answer typed in under 2 seconds is refused. A wrong line ends the take with nothing sent.
- You pick a NEW take id for every take, also after a failed one. After both typed answers the program writes a marker file `~/.hadavin-take-tags/<id>.used` in the Linux home folder. Never delete or edit that file: a reused id is refused. To see which ids are used, list that folder.
- If a login line says anything other than "still works", nothing was sent. Tell the lead. Retry at most once (repeated failed logins can trigger a Google sign-in alert).
- During the take: contacts appear in HubSpot and one mail per person appears in the label `demo`. The lead stops and restarts n8n while person C is posted. You do not touch anything.
- Stop and tell the lead: a number in the notice is not what you approved; any count is wrong; the laptop sleeps.
- To be decided by the lead: which screen the video shows as proof of the counts (candidates: n8n's list of runs, the rows of the lead table, HubSpot, Gmail). The video must not show or claim any portal, approval step or audit trail.

### Step E. The film pause: type `end`
When the program says "Film the contact list now: type `end` and press Enter to archive", the lead films the contact list first. Type `end` and Enter yourself only when the lead says so. The program then removes this take's contacts. Only the exact word `end` ends the pause: any other line makes it print "type exactly: end" and ask once more; a second wrong line also ends the pause and the program goes ahead and removes the contacts. A closed input on the first prompt ends the pause at once. Ctrl-C or closing the window also removes them.
- Stop and tell the lead: you closed the window or pressed Ctrl-C early. Leftover contacts are then removed by hand in HubSpot; the lead gives you the count.
- To be decided by the lead: whether your HubSpot key used by the take program is allowed to delete contacts. A read-only key can check but cannot delete, so the final removal could fail after the sends. Until the lead decides, expect that you may have to delete leftover contacts by hand in HubSpot.

### Step F. Filming and cropping (before and during recording, and after)
Use a fresh Chrome profile named `demo-take`, signed in only to the HubSpot test account, the receiver (label `demo` only) and n8n. Make sure NONE of these shows an address other than the made-up take addresses `take-<id>-a@example.com`, `-b@` and `-c@`:
1. Receiver mailbox: the account address in the top bar, the profile menu, the To and From lines of each mail, the tab title.
2. Sender mailbox or its "Send mail as" settings: do not film them.
3. Tab titles and the address bar, if they carry an address.
4. n8n's list of runs: only made-up names and the made-up addresses, and no old run. Do not film the detail of the mail-sending step: n8n now keeps its saved runs, and that detail may show real addresses (the company address and the sender address). To be decided by the lead: whether that detail shows real addresses at all (the rehearsal can check).
5. The proof screen (see step D): lead keys only.
6. Terminal windows: no address in the prompt, history or settings output.
7. Mail notifications, desktop pop-ups, the system tray.
Do not hover your account picture; do not open "show details" on a mail.
- After the take you scan every frame of the cut: one pass at full speed, one pass of stills at each cut. No address may show except `take-<id>-a/b/c@example.com`.
- Stop and tell the lead: any real address is visible. No footage is used until it is cropped or retaken.

### Step G. If a take fails
The lead says why. You remove the demo mails from the label `demo` and the Inbox, delete any leftover HubSpot contacts the lead counted, and give a NEW written yes with numbers (step A). A take that got past both typed answers uses up its take id even if it fails: pick a NEW id and never delete the marker file.

## After the take

### Step H. Mon 23 Nov before 18:29 UTC (23:59 IST): you watch the cut
Watch from the first second to the last. Reply "accepted" or list the bad seconds. Clean-up (step I) follows; after it there is no further take.

### Step I. Clean-up, by Mon 23 Nov 18:29 UTC (23:59 IST)
Starts when the lead says the last take is done. The lead first deletes n8n's connections and saved runs (made-up data only), stops n8n and removes the take folder and the database container. Your part:
1. Revoke the app passwords made for the take, in both accounts (receiver and sender): myaccount.google.com, Security, App passwords, Remove. Screenshot each empty list.
2. Delete the HubSpot private apps made for the take (Settings, Integrations, Private Apps, Delete). Screenshot.
   - To be decided by the lead: whether the HubSpot key already in use is one of these private apps or a different key of the test account that stays; the lead tells you which to delete.
3. Save the screenshots in `C:\Users\rakes\Downloads\Hadavin\_local\real-run\` under the names the lead gives.
4. Run `python scripts/run_real_check_n8n.py --retire-check <take config>` BEFORE you delete the secret files and while your take config file still exists (keep the config outside the take folder, because the lead removes the take folder). It must print "refused as expected" for the mailbox and for HubSpot, exit code 0. "STILL WORKS" (exit 3): remove that credential again and rerun. "could not tell" (exit 2): rerun later. Keep the secret files until it passes.
5. Only after it passed: delete the secret files in WSL (`shred -u <the files>`; not checked whether `shred` exists on your WSL, otherwise `rm`). Do NOT delete `~/.hadavin-take-tags/<id>.used`.
- The copy of the passwords inside n8n dies only by your revocation in this step; that is a screenshot, not a check.
- Set laptop sleep and lid settings back; sign out of the `demo-take` profile.

### Step J. Post on Wed 25 Nov 2026, 15:00 UTC = 20:30 IST
You post; Claude never posts. The post says only: leads arrive through n8n; n8n writes the customer-list entry and sends the mail; our code caps the spend, asks the model once per lead and counts the mails and contacts with a separate check of ours; **a lead sent twice with the same id is processed once**.
It must NOT say:
- that the same person through two doors is one lead;
- that no lead data stays in n8n, or that recovery takes within 60 seconds, or that an alert comes within 30 seconds;
- that a portal, an approval step or an audit trail exists or shows these rows;
- that n8n cannot reach the internet (its outgoing traffic is switched off by settings and only watched, not blocked);
- that the take is crash-safe (unless the rehearsal's crash test passed);
- that the count is made with an independent login (until that login is built and shown to run).
- To be decided by the lead: the exact final words of the claim after the rehearsal. If a crash between sending the mail and noting it in the table can send the mail twice (or was not tested), the lead adds a limit sentence. Use the lead's words.

## What to send the lead (never a secret)

| When | Send |
|---|---|
| Take day | "label and inbox empty"; any answers the lead asks for in step C |
| Each take | your written yes with numbers (step A) |
| After a take | "accepted" or the bad seconds |
| Clean-up | the two screenshots, the retire-check output (words and counts only) |

## Refusals and exit codes you may meet

- Lock file: if the take stops hard and leaves a file `take-<name>.lock` beside the take folder, the next take with the same name is refused. Delete it by hand ONLY when the lead says so.
- Start deadline: the take refuses to start unless it can finish about 14 minutes before the window end. With the window end at 23 Nov 2026 18:29 UTC the last start is about 18:14 UTC (23:44 IST).
- Exit codes: 0 pass; 1 the answer was not `y` or the confirmation line did not match; 2 a refusal (settings, no keyboard, closed input, too fast, name or keys already used, lock exists, window too close); 3 a count or verdict failure. For the retire check: 0 both refused, 3 a login still works, 2 anything else.

## What is not proven yet (plain words)

- The rehearsal is written and has NOT been run. No evidence for it exists yet.
- The code has never run against a real Gmail, HubSpot or model call. It ran once against a real n8n with stand-in programs for everything else (that first run left items open).
- Not yet shown: how Gmail applies the label to a mail sent from another Gmail account, and how fast; whether the take program sees the label `demo` as a folder named `demo`; whether Gmail accepts the company address as the shown sender without a "mailed-by" line.
- Not yet shown: that n8n keeps its own state in the same database as our lead table (the aim; in the first run it used its default file database), and that deleting saved runs at clean-up works at the real take.
- Not yet shown: that a crash between sending the mail and noting it in the table sends no second mail.
- The take does not check by itself: the alert mail, mail in any folder other than `demo`, the contact id read back from HubSpot (only checked to be all digits), the manual n8n stop and restart, and the second door (the hook door).
- Click paths in Google, HubSpot and n8n were not checked on your accounts: if a screen differs from what a step says, stop and tell the lead what you see.
- Your written yes with numbers does not exist yet. No paid take happens without it.
- Where records are kept: the aim is one database for the take (its Postgres, shared by n8n and our lead table). One small file in the take folder (`stage.journal`) is the one stated exception: it guards the model calls independently of n8n. Some bookkeeping files also exist outside the database (spend record, lock files, the take-id marker).
