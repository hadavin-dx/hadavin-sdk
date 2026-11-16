# Your steps for the recorded take of the lead desk video (version 4)

Written Mon 16 Nov 2026 from version 3, the owner facts file of the same day, and the reviewed edit list, then revised after the two reviews in `review-c4b-v4.md`. Nothing was run to write this. If something here differs from the studio lead's current plan, the plan wins; tell the studio lead.

This sheet holds only what ONLY YOU can do. Everything you already did is left out on purpose: the two throwaway Gmail accounts, the HubSpot test account and its keys, your n8n account, the model key and its credits, the push of the flows to the public repository, and the approval of the recorded take "once everything is ready". Do not redo any of it. The one exception is in step C.2: the take uses a new, empty database, so IF the studio lead asks, you log in to n8n and type its three connections once more. The studio lead does everything else: the database, the model program, n8n, importing the flows, the rehearsal and the checks.

## Order of the day

1. Step A: the studio lead sends the numbers; you answer with a written yes.
2. Step B: laptop settings.
3. Step C: check the receiver mailbox, n8n if asked, and prepare the browser profile (C.3).
4. Step D: start the take and type `y` and the confirmation line yourself.
5. Step E: the film pause; type `end` only when the studio lead says so.
6. After the take: steps F (check what the film shows), G (only if the take failed), H (watch the cut), I (clean-up), J (post).

**Take date:** the studio lead sets it. It is not fixed in the plan. The only fixed times are: the last start is 18:14 UTC = 23:44 IST on Mon 23 Nov 2026, and the window end is 18:29 UTC = 23:59 IST the same day. Until the studio lead names a date, do nothing.

## Who is who (read once)

- **The studio lead** is the Claude session that works with you. Only this word is used for it.
- **A contact** is one made-up person in the HubSpot test account (the customer-list entry). The take makes three: A, B and C.
- Apart from the video's name (the "lead desk"), the word "lead" appears ONCE below, inside a quoted claim of the post (step J): "the same lead id sent twice is processed once". There, "lead id" means the unique number the take gives each made-up contact when it sends it in. The program uses the word "lead" in its own screens and file names; it means the same as "contact".

## Words used (read once)

- **The take**: one recorded run on your own throwaway accounts, with 3 made-up people (A, B, C). A is sent twice, B is sent ten times at once, C is sent once while the studio lead stops and restarts n8n. "Recorded" means the run you film; every person in it is made up.
- **Take id**: a short name you invent for each take and never use again. The plan gives no fixed pattern. Until the studio lead gives you a pattern, ask; a word plus 4 digits is likely but is NOT confirmed. The program writes a marker file for each id (step D) and refuses a used id.
- **Take config**: the small settings file for one take. The studio lead prepares it and gives you its path. You do not edit it.
- **Window end**: the time after which the take may not spend money or run. Planned: 18:29 UTC = 23:59 IST on Mon 23 Nov 2026.
- **The secret files**: the files in your WSL home folder that hold the app passwords and keys for the take. You made them. Nobody else opens them.
- **Exit code**: a number the take program leaves behind when it ends. To see it, type `echo $?` and Enter in the same WSL window right after the program ends, before any other command. 0 means success.
- **n8n**: the tool that takes the made-up people in, writes the HubSpot contact and sends the mail.
- **Hook door**: a second way in to n8n (a web address that n8n listens on). The take does not check it by itself.
- **Postgres**: the database program that stores the take's table of people and, planned, n8n's own records. It runs in a Docker container on this laptop.
- **The model program**: a small program of ours that asks the AI model once per person and checks the spending settings.
- **Receiver**: the throwaway Gmail account that only receives the demo mails. **Sender**: the throwaway Gmail account n8n sends from.
- **The notice**: the screen of numbers the take program prints before it asks you to type `y`.
- **Proof screen**: the one screen in the video that shows the counts are right (step D).
- **Rehearsal**: a full practice run on this laptop with stand-in programs, made-up data, no real account, no real key and no model call. It is done first, always, and costs US$0. The studio lead runs it; you do nothing for it.
- **Loopback**: traffic that stays on this laptop; nothing leaves it.
- **Retire check**: a program command that tries to log in with the keys you revoked and must be refused (step I).
- **Crash-safe**: if the program or n8n dies at a bad moment, no mail is sent twice. This is NOT yet shown (see the last section).
- **Removed for good**: how this sheet names the act of taking a made-up contact out of HubSpot so it is gone. The program calls it "archive" and in the code it is a delete; it means the same. Gmail's own "Archive" button is a different thing and is not used. "Revoke" is used only for app passwords.
- **WSL**: the Linux (Ubuntu) window inside Windows where the take runs.

## What the take can cost

The most the take can cost is the number in your written yes: 3 model calls at the worst-case price per call the studio lead states, so 3 times that price. What stops it going over: the take allows at most 3 model calls, and the design records each paid call before it is made, so one person cannot be paid for twice. The spending limit and window end are settings in a file that the program checks; you look at them yourself before you say yes. The program does NOT enforce a fixed ceiling in dollars, and it only checks that the worst-case price is a number above zero. So you judge whether the price is sensible.

## Rules that hold in every step

1. **Never send the studio lead** a password, token, key, mailbox address or the contents of any secret file. Send only short sentences. A file path is fine.
2. **The typed answers are yours alone**: the `y`, the 6-digit number with the take id, and `end`. The 6-digit number only blocks blind and piped answers. It does NOT stop a tool that reads the screen and types the number back. So never let any tool, script, assistant, agent or helper window read the screen and type for you. Run the take only on your laptop, in your own WSL window.
3. **Before every paid take you give a written yes WITH numbers** (step A). No numbers, no take.
4. **You post. Claude never posts.**
5. **Never point the take at your real company mailbox.** The take uses only the throwaway receiver and sender.
6. On take days: laptop on mains power, sleep set to Never, "When I close the lid" set to Do nothing (step B). Set both back after the last take.

## Before a take

### Step A. The written yes with numbers (once per paid take)
The studio lead sends one message with: at most 3 model calls in this take; the worst-case cost per call; 3 times that figure; the money spent so far; the spending limit and the window end as they stand in the settings (you look at those two values yourself on the studio lead's screen); and the planned window end 2026-11-23 18:29 UTC = 23:59 IST. The message also says that the rehearsal has passed and names its result file. No rehearsal pass, no take.
You answer in one line, for example: "Yes, take <take id>, up to 3 calls and up to US$X, window ends 2026-11-23 23:59 IST." A yes covers ONE take. No numbers in the message means answer no.
- Whether a practice run on your throwaway accounts also happens is the studio lead's open point (the rehearsal always happens first and does not prove real Gmail or HubSpot). Until the studio lead tells you, do nothing for it.

### Step B. Take-day laptop settings
Mains power plugged in, sleep Never, "When I close the lid" Do nothing. Close other programs that show addresses or alerts. Set the settings back after the last take.

### Step C. Take day, before the studio lead says go
1. **Receiver mailbox.** Open the receiver account in Gmail. In the left list click the label `demo` and check it holds no mail; then click Inbox and check it is empty. Tell the studio lead "label and inbox empty". If the label holds mail, tell the studio lead and do not start. (The take reads only the label `demo`.)
2. **n8n, only if the studio lead asks.** The take starts a new, empty database, so n8n may show a first-visit screen asking you to create an owner login, and may need the three connections (HubSpot, mail sending, database) typed again. If the studio lead asks, you type the password yourself, into the n8n screen, never into chat, and tell the studio lead only "done". If the studio lead does not ask, do nothing here. The studio lead tells you the address to open; until then, do not open n8n.
   - Stop and tell the studio lead: n8n shows a saved secret in clear text on screen or in an export.
3. **Browser profile (needed before the take, so the film is clean).** In Chrome click your account picture at the top right, then "Add", then continue without signing in to Chrome, and name the profile `demo-take`. In that profile sign in only to the HubSpot test account, the receiver (label `demo` only) and n8n. Do not sign in to anything else. Tell the studio lead "profile ready". If a screen differs from these clicks, stop and tell the studio lead what you see.

## The take

### Step D. Start the take and type `y`
In your own WSL window, take folder open, the `demo-take` browser profile ready (step C.3), laptop on mains. The studio lead gives you the one line to run (form: `python scripts/run_real_check_n8n.py --take <take config>`). What you will see, in this order:
1. The program prints `mailbox login: still works` and `HubSpot login: still works`. A bad login stops the take here, before you type anything.
2. The notice, which already shows the random 6-digit "Confirmation number (type it, a space and the take id)".
3. "Type y to start".
4. "Now type the confirmation number shown above, a space and the take id to confirm:".

Read the notice: 3 people, up to 3 model calls and the worst case, up to 3 contacts removed for good at the end, up to 3 mails, n8n stopped once by hand. Type `y` and Enter **yourself**. A piped or scripted `y` is refused on purpose; closed input ends the take with exit code 2 and nothing is sent. The flags `--yes` and `-y` do not exist.
- Then type the 6-digit number the notice showed (new every take), a space, the take id, and Enter, for example `123456 <take id>`. An answer typed in under 2 seconds is refused. A wrong line ends the take with nothing sent.
- You pick a NEW take id for every take, also after a failed one. After both typed answers the program writes a marker file `~/.hadavin-take-tags/<id>.used` in the Linux home folder. Never delete or edit that file: a reused id is refused. To see which ids are used, list that folder.
- If a login line says anything other than "still works", nothing was sent. Tell the studio lead. Retry at most once (repeated failed logins can trigger a Google sign-in alert).
- **Exit codes at this step** (see them with `echo $?`): 1 means your answer was not `y` or the confirmation line did not match; 2 means the program refused to start or go on (a setting, no keyboard, closed input, too fast, a used id, a lock file, the window end too close); 3 means a count or verdict failed after the take ran. In all three cases tell the studio lead the number and the last line the program printed.
- During the take: contacts appear in HubSpot and one mail per person appears in the label `demo`. The studio lead stops and restarts n8n while person C is sent. You do not touch anything.
- Stop and tell the studio lead: a number in the notice is not what you approved; any count is wrong; the laptop sleeps.
- **The proof screen is your choice.** The studio lead offers candidates (n8n's list of runs, the rows of the people table, HubSpot, Gmail), you pick one, and the studio lead says what it shows. The video must not show or claim any portal, approval step or audit trail.

**WARNING before step E: when the program asks for `end`, closing the window, pressing Ctrl-C, or typing two wrong words in a row ends the pause and removes the made-up contacts from HubSpot for good, BEFORE the studio lead has filmed them. Type exactly `end`, and only when the studio lead says so.**

### Step E. The film pause: type `end`
When the program says "Film the contact list now: type `end` and press Enter to archive", the studio lead films the contact list first. Type `end` and Enter yourself only when the studio lead says so. The program then removes this take's contacts for good. Only the exact word `end` ends the pause: any other line makes it print "type exactly: end" and ask once more; a second wrong line also ends the pause and the program goes ahead and removes the contacts. A closed input on the first prompt ends the pause at once. Ctrl-C or closing the window also removes them.
- Stop and tell the studio lead: you closed the window or pressed Ctrl-C early. Leftover contacts are then removed by hand in HubSpot; the studio lead gives you the count.
- If the HubSpot key the take program uses cannot delete contacts, the final removal can fail after the sends. Until the studio lead tells you otherwise, expect that you may have to delete leftover contacts by hand in HubSpot.

### Step F. What the film may show (before and during recording, and after)
Everything here is checked in the `demo-take` profile of step C.3. Make sure NONE of these shows an address other than the made-up take addresses `take-<id>-a@example.com`, `-b@` and `-c@`:
1. Receiver mailbox: the account address in the top bar, the profile menu, the To and From lines of each mail, the tab title.
2. Sender mailbox or its "Send mail as" settings: do not film them.
3. Tab titles and the address bar, if they carry an address.
4. n8n's list of runs: only made-up names and made-up addresses, and no old run. Do not film the detail of the mail-sending step: n8n keeps its saved runs, and that detail may show real addresses (the company address and the sender address). Until the studio lead says the detail is safe, do not open it.
5. The proof screen you chose in step D: made-up keys only.
6. Terminal windows: no address in the prompt, history or settings output.
7. Mail notifications, desktop pop-ups, the system tray.
Do not hover your account picture; do not open "show details" on a mail.
- After the take you scan every frame of the cut: one pass at full speed, one pass of stills at each cut. No address may show except `take-<id>-a/b/c@example.com`.
- Stop and tell the studio lead: any real address is visible. No footage is used until it is cropped or retaken.

### Step G. If a take fails
The studio lead says why. You remove the demo mails from the label `demo` and the Inbox, delete any leftover HubSpot contacts the studio lead counted, and give a NEW written yes with numbers (step A). A take that got past both typed answers uses up its take id even if it fails: pick a NEW id and never delete the marker file.

## After the take

### Step H. Mon 23 Nov before 18:29 UTC (23:59 IST): you watch the cut
Watch from the first second to the last. Reply "accepted" or list the bad seconds. Clean-up (step I) follows; after it there is no further take.

### Step I. Clean-up, by Mon 23 Nov 18:29 UTC (23:59 IST)
Starts when the studio lead says the last take is done. The studio lead first removes n8n's connections and saved runs (made-up data only), stops n8n and removes the take folder and the database container. Your part:
1. Revoke the app passwords made for the take, in both accounts (receiver and sender): myaccount.google.com, Security, App passwords, Remove. Screenshot each empty list.
2. Delete the HubSpot private apps made for the take (Settings, Integrations, Private Apps, Delete). **First answer the studio lead's question: which private apps did you make for the take, and is the key the take used one of them, or a different key of the test account that stays?** Only you know this. Delete only after the studio lead confirms the list. Screenshot.
3. Save the screenshots in `C:\Users\<your-user>\Downloads\Hadavin\_local\real-run\` under the names the studio lead gives.
4. Run `python scripts/run_real_check_n8n.py --retire-check <take config>` BEFORE you delete the secret files and while your take config file still exists (keep the config outside the take folder, because the studio lead removes the take folder). It must print "refused as expected" for the mailbox and for HubSpot, exit code 0. "STILL WORKS" (exit code 3): remove that credential again and rerun. "could not tell" (exit code 2): rerun later. Keep the secret files until it passes. See the exit code with `echo $?`.
5. Only after it passed: delete the secret files in WSL (`shred -u <the files>`; if `shred` is not there, use `rm`; not checked whether it exists). Do NOT delete `~/.hadavin-take-tags/<id>.used`.
- The copy of the passwords inside n8n dies only by your revocation in this step; that is a screenshot, not a check.
- Set laptop sleep and lid settings back; sign out of the `demo-take` profile.

### Step J. Post on Wed 25 Nov 2026, 15:00 UTC = 20:30 IST
You post; Claude never posts. The post says only: contacts arrive through n8n; n8n writes the HubSpot contact and sends the mail; our code caps the spend, asks the model once per contact and counts the mails and contacts with a separate check of ours; **"the same lead id sent twice is processed once"** (here "lead id" is the number the take gives each contact, as explained under "Who is who").
It must NOT say:
- that the same person through two doors is one contact;
- that no contact data stays in n8n, or that recovery takes within 60 seconds, or that an alert comes within 30 seconds;
- that a portal, an approval step or an audit trail exists or shows these rows;
- that n8n cannot reach the internet (its outgoing traffic is switched off by settings and only watched, not blocked);
- that the take is crash-safe (unless the rehearsal's crash test passed);
- that the count is made with an independent login (until that login is built and shown to run).
The exact final words of the claim come from the studio lead after the rehearsal. Until the studio lead gives them, do not post.

## What to send the studio lead (never a secret)

| When | Send |
|---|---|
| Before a take | your answer on the take date; the take id you picked (word only, no secret); your written yes with numbers (step A) |
| Take day | "label and inbox empty"; "profile ready"; "done" for n8n, only if asked; any problem line from step C |
| During a take | the exit code and the last printed line if the take stops; "closed the window early" if it happens; the proof screen you picked |
| After a take | "accepted" or the bad seconds; "a real address is visible" if you see one |
| After a failed take | confirmation that the demo mails are removed; a new written yes |
| Clean-up | which HubSpot private apps you made; the screenshots; the retire-check output (words, counts and exit code only); "secret files deleted" |
| Before posting | the post text for the studio lead to compare with the final claim |

## Refusals and exit codes you may meet

- Lock file: if the take stops hard and leaves a file `take-<name>.lock` beside the take folder, the next take with the same name is refused. Delete it by hand ONLY when the studio lead says so.
- Start deadline: the take refuses to start unless it can finish about 14 minutes before the window end. With the window end at 23 Nov 2026 18:29 UTC the last start is about 18:14 UTC (23:44 IST).
- Exit codes: 0 pass; 1 the answer was not `y` or the confirmation line did not match; 2 a refusal (settings, no keyboard, closed input, too fast, name or keys already used, lock exists, window too close); 3 a count or verdict failure. For the retire check: 0 both refused, 3 a login still works, 2 anything else.

## What is not proven yet (plain words)

- The rehearsal is written and has NOT been run. No evidence for it exists yet.
- The code has never run against a real Gmail, HubSpot or model call. It ran once against a real n8n with stand-in programs for everything else (that first run left items open).
- Not yet shown: how Gmail applies the label to a mail sent from another Gmail account, and how fast; whether the take program sees the label `demo` as a folder named `demo`; whether Gmail accepts the company address as the shown sender without a "mailed-by" line (a line in the mail header saying which account really sent it).
- Not yet shown: that n8n keeps its own records in the same Postgres as our people table (the aim; in the first run it used its default file database), and that removing saved runs at clean-up works at the take.
- Not yet shown: that a crash between sending the mail and noting it in the table sends no second mail.
- The take does not check by itself: the alert mail, mail in any folder other than `demo`, the contact id read back from HubSpot (only checked to be all digits), the manual n8n stop and restart, and the hook door.
- Click paths in Google, HubSpot, Chrome and n8n were not checked on your accounts: if a screen differs from what a step says, stop and tell the studio lead what you see.
- Your written yes with numbers does not exist yet. No paid take happens without it.
- Where records are kept: the aim is one database for the take (its Postgres, shared by n8n and our people table). One small file in the take folder (`stage.journal`) is the one stated exception: it guards the model calls independently of n8n. Some bookkeeping files also exist outside the database (spend record, lock files, the take-id marker).

## For the studio lead (not for the owner to act on)

Open points the studio lead decides. Each has a default for the owner: do nothing until the studio lead says.
1. Order of the rehearsal and any practice run on the real throwaway accounts (the rehearsal does not prove real Gmail or HubSpot).
2. Whether the take's fresh n8n needs the first-visit owner login and the three connections at all; which address and password; who switches the flows on. The n8n database login is meant to be a limited one (read, add and change rows of the people table only, never the administrator login); who creates its password and who types it is open. The v3 rule that the owner types secrets still applies; privileges are planned, not proven.
3. The address and port the owner opens n8n at. The rehearsal used `http://localhost:5690`; 5678 and 5679 are the owner's own n8n and are not touched. The port for the take is not chosen. Not checked: whether the Windows browser reaches n8n inside WSL (re-check).
4. The take date (the plan has none) and the pattern for take ids.
5. Whether the owner's HubSpot key used by the take may delete contacts (a read-only key can check but not delete).
6. Whether n8n's mail-sending step detail shows real addresses (the rehearsal can check).
7. Candidate proof screens to offer the owner (step D).
8. Which HubSpot private apps are the take's (ask the owner, step I.2) and the final list to confirm.
9. The exact final words of the claim after the rehearsal, with a limit sentence if a crash between sending the mail and noting it can send the mail twice or was not tested.
10. Whether `shred` exists in the owner's WSL.
