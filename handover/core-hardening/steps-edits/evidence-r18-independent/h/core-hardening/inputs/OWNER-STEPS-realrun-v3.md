# Owner steps v3 for the real take of the lead desk video (n8n take, plan-4 "N-lite")

Written Sat 14 Nov 2026 (about 18:10 UTC / 23:40 IST) by a document-only agent; updated Sun 15 Nov 2026 to match the code on branch `take/nlite-int` (worktree `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\nlite-int`). Independent review rounds 3 to 9 of the code are done; this file itself got a drift review (drift-report-1) and is corrected to it. Replaces `OWNER-STEPS-realrun.md` (v2, kept untouched as history). Sources: `replan\plan-4-nlite.md` (FROZEN; sections 3, WP6, 3.8, 7, amendments A1 to A12), `replan\resolve-3.md`, the demo run sheet `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\handover-demo\handover\demo\VIDEO-RUNSHEET.md` (crop list), and the built scripts in `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\nlite-wp1`, `nlite-wp3a`, `nlite-wp3b` (read only). No program was run to write this. If anything here differs from the frozen plan, the plan wins; tell the lead.

This file holds only what ONLY YOU can do. The lead does everything else (start the database, the model stage and n8n, import the flows, run the checks). The exact commands for the lead are in `egm\duplicate-proof-lead-desk\nlite\WP6-RUNBOOK.md`.

**UNVERIFIED** = I could not confirm it in the files; I did not invent it. Click paths for Google, HubSpot and n8n were not checked on your accounts: if a screen differs, stop and tell the lead what you see.

## Words used (read once)

- **The take**: one real recorded run on your own test accounts, with 3 made-up people (called A, B, C). A is sent twice, B is sent ten times at once, C is sent once while the lead stops and restarts n8n by hand.
- **n8n**: the flow tool that takes the leads in, writes the CRM contact and sends the mail. **The stage**: a small program of ours that asks the AI model once per lead and enforces the money cap. **The lead**: the Claude session that runs this with you.
- **RECEIVER**: a throwaway Gmail account that only receives the demo mails. **SENDER**: a second throwaway Gmail account that n8n sends from. **Company address**: your Hadavin company address; it appears only as the "From" line shown on the mail (through Gmail "Send mail as").
- **App password**: a 16-letter Google password for one program. It opens the WHOLE mailbox, not only one label. **Token**: HubSpot's version of the same idea.
- **The notice**: the screen of numbers the take program prints before it asks `y`.
- **WSL**: the Linux (Ubuntu) window inside Windows where the take runs. Secret files go on its own Linux disk (for example under `/home/<you>/...`), never under `/mnt/c/...` (that is the Windows disk; the program refuses it).

## Rules that hold in every step

1. **Never send the lead** a password, token, key, mailbox address or the contents of any secret file. Send only the short sentences a step asks for.
2. **You type secrets yourself**: into the n8n screen, or into a file you create in WSL. The lead never opens `C:\Users\rakes\Downloads\Hadavin\_local\secrets` or `C:\Users\rakes\Downloads\Hadavin\_local\real-run\secrets`.
3. **The typed answers are yours alone** (steps 17 and 18): the `y`, the 6-digit challenge with the take id, and `end`. The challenge only blocks blind and piped answers (and any answer typed in under 2 seconds). It does NOT stop a tool that reads the screen and types the number back. So you must never let any tool, script, assistant, agent or helper window read the screen and type for you. Run the take only on your laptop, in your own WSL window.
4. **Before every paid take you give a written yes WITH numbers** (step 16). No numbers, no take. The spending cap and the window end are only settings in the stage settings file, a backstop that YOU check by eye before you say yes. The program does not enforce a fixed ceiling: the worst-case-per-call figure typed into the take settings is only checked to be a number above 0. The real protection against a loop or a double call is in the design: one paid call per lead id, recorded before the call is made.
5. **You post. Claude never posts.**
6. Laptop on mains power on take days, sleep set to Never, "When I close the lid" set to Do nothing. Set both back after the last take.

## Phase 0: set-up, by Mon 16 Nov 18:29 UTC (23:59 IST); Sun evening is ideal. About 60 to 90 minutes.

### Step 1. Check that the old practice mailbox password is revoked FIRST
NEEDS-OWNER. Why first: an old app password still works until you revoke it, and it opens a whole mailbox. Open myaccount.google.com, Security, App passwords, on the OLD practice mailbox account; delete every entry named `desk-real-run` or similar.
- Expected: the list is empty or has none of the old demo names.
- STOP and tell the lead: you cannot see the list, or an entry will not delete.

### Step 2. Create the two throwaway Gmail accounts (RECEIVER and SENDER)
NEEDS-OWNER. Why (plan rule, not a lead preference): an app password opens a whole mailbox, so the mailbox must hold nothing else of yours. Each account is used for nothing else, is NOT the sign-in or recovery address of any other account of yours (check this), and gets 2-Step Verification turned on.
- Tell the lead only: "receiver and sender created, 2-step on, not recovery for anything". Do not send the addresses.
- Using your real company mailbox instead needs your separate written yes (plan-4 section 7, item 2). Default: throwaway.
- STOP and tell the lead: Google asks for a phone check you cannot pass, or you want to use the company mailbox.

### Step 3. Send mail as: the company address as the shown From
NEEDS-OWNER. In the SENDER account: Gmail, gear, See all settings, Accounts and Import, "Send mail as", Add another email address, enter the company address, finish the verification. Without this Gmail rewrites the From line to the SENDER address and the claim "the company address works live" fails.
- Expected: the company address is listed under Send mail as, verified.
- UNVERIFIED: whether Gmail's own SMTP accepts the company address as From without a delay or a "mailed-by" line showing the SENDER address in the mail details. The lead checks this in the smoke (WP6 checks (c), (d)).
- STOP and tell the lead: the verification mail never arrives.

### Step 4. RECEIVER: the Gmail filter and the label `demo`
NEEDS-OWNER, in the RECEIVER account.
1. Gmail, gear, See all settings, Filters and Blocked Addresses, Create a new filter.
2. In **Subject** type `[demo] lead`. Click Create filter.
3. Tick **Skip the Inbox (Archive it)** and **Apply the label**, New label, name it exactly `demo`. Create filter.
4. Open the label `demo`: it must be empty. The Inbox must be empty too.
- Why: the take reads ONLY the Gmail label named `demo`. The take config must carry the line `REAL_IMAP_1_FOLDERS=demo` (required; any other value is refused, a missing line stops the take) and the take refuses every other folder (Inbox, All Mail, Important, Starred, Sent). You make this filter BEFORE the recording; without it the take counts nothing. The mail must appear only there, once.
- UNVERIFIED: whether Gmail applies the filter to a mail sent from a different Gmail account within seconds; the smoke proves it.
- STOP and tell the lead: the label already holds mail, or you cannot tick Skip the Inbox.

### Step 5. Create two app passwords (one per account)
NEEDS-OWNER. myaccount.google.com, Security, 2-Step Verification, App passwords.
1. In RECEIVER: name `desk-read`. Copy the 16 letters. In WSL create a file and type them yourself (no spaces): `mkdir -p ~/take-secrets && umask 077 && nano ~/take-secrets/receiver.pw`, save, then `chmod 600 ~/take-secrets/receiver.pw` and check `ls -l ~/take-secrets` shows `-rw-------`. The file holds only the password, one line.
2. In SENDER: name `desk-send`. Keep it on screen only until step 8 (you type it into n8n, not into a file).
- Never paste either into chat. Both are revoked in step 22.
- STOP and tell the lead: the option "App passwords" is missing (2-Step not on, or the account type does not allow it).

### Step 6. HubSpot test account: the property
NEEDS-OWNER. Your own HubSpot TEST account only (made-up data). Settings, Properties, Contact properties, Create property: single-line text, Internal name exactly `hadavin_label` (keep the existing `hadavin_lead_id` from v2; if it does not exist, create it the same way).
- UNVERIFIED: whether the real n8n HubSpot flow also needs another property; the lead says at the smoke.

### Step 7. HubSpot: two private apps, one per function
NEEDS-OWNER. Settings, Integrations, Private Apps, Create.
1. App 1 for the take program, scope contacts **read** only. Copy the token and type it into a file in WSL: `nano ~/take-secrets/hubspot-read.tok`, `chmod 600`. (This is the old v2 step 5; the file name is yours, you tell the lead the path, never the content.)
2. App 2 for n8n, scopes contacts **read and write** only. Do not save its token to a file; you type it in step 8.
- Two apps because one identity per function (least privilege). Both are deleted in step 22.
- UNVERIFIED: the exact scope names HubSpot shows (expected "crm.objects.contacts.read" and ".write").

### Step 8. Type the three secrets into n8n yourself
NEEDS-OWNER. When the lead says n8n is running, open it in your Windows browser at the address the lead gives (it should be `http://localhost:5678` or similar; UNVERIFIED that Windows reaches WSL there, WP6 check (e)). Credentials, Add credential, create three and name them exactly as the lead says:
1. **SMTP (the sender)**: host smtp.gmail.com (UNVERIFIED: the lead confirms host and port), user = SENDER address, password = the SENDER app password.
2. **HubSpot**: the token of app 2.
3. **Postgres**: host, database, user as the lead names them; password = the one you set in WSL when you start the database (the lead gives the start command; you type the password).
Tell the lead only: "three credentials created".
- STOP and tell the lead: n8n shows a saved secret in clear text on screen or in an export.

### Step 9. Send the lead only these short sentences
"throwaway receiver and sender created, 2-step on, not recovery for anything"; "company address verified under Send mail as"; "filter and label done, label empty, inbox empty"; "two app passwords made, receiver file in WSL mode 600"; "property made, two HubSpot apps made"; "three credentials created"; the path of the receiver password file and of the HubSpot read token file (paths only); the HubSpot contact count if the test account has contacts.

## Phase 1: the lead checks (no steps for you except being reachable). Wed to Sun.

The lead runs the checks (a) to (f) of the smoke (WP6-RUNBOOK) with NO paid call. If a check fails the lead tells you what to change. You may be asked to confirm what a screen shows.

## Phase 2: each take

### Step 16 (order number kept for the take list). The written yes WITH numbers, once per paid take
NEEDS-OWNER. The lead sends one message with: at most **3 model calls** in this take; the worst case per call (a dollar figure the lead types from the stage settings; the program only checks that it is a finite number above 0 that it can show in the notice (a huge, odd or so-small-it-shows-as-zero figure is refused with exit 2), so you judge whether it is sensible; UNVERIFIED until then); 3 times that worst case; the money spent so far; the cap and the window end as they stand in the stage settings (you look at those two values yourself on the lead's screen: they are a backstop you check by eye, not a ceiling the program enforces against a second file); and the planned window end **2026-11-23 18:29 UTC = 23:59 IST**. You answer in one line, for example: "Yes, take <tag>, up to 3 calls and up to US$X, window ends 2026-11-23 23:59 IST." A yes covers ONE take. No numbers in the message means answer no.

### Step 17. Watch the take and answer the first typed prompt: `y`
NEEDS-OWNER, in your own WSL window, take folder open, fresh browser profile (step 19 below), laptop on mains. The lead gives you the one line to run (form: `python scripts/run_real_check_n8n.py --take <take config>`). True order on screen: (a) first the program prints `mailbox login: still works` and `HubSpot login: still works` (a bad login stops the take here, before you type anything); (b) then the notice, which already shows the random 6-digit "Confirmation number (type it, a space and the take id)"; (c) then "Type y to start"; (d) then "Now type the confirmation number shown above, a space and the take id to confirm:". Read the notice: 3 people, up to 3 model calls and the worst case, up to 3 contacts archived at the end, up to 3 mails, n8n killed once by hand. Type `y` and Enter **yourself**. A piped or scripted `y` is refused by the program on purpose. If the input is closed or ends at this prompt (end of input), the take stops with exit code 2 and sends nothing. The flags `--yes` and `-y` do not exist and are refused.
- After the `y`, type the random 6-digit number that the notice already showed (new every take), a space, and the take id, then Enter, for example `123456 <take id>`. An answer typed in under 2 seconds is refused (you could not have read it). A wrong line ends the take with nothing sent. Nobody and no agent may type this for you.
- A take id can be used once, and you pick a NEW id for every take (also after a failed one). The program writes a small marker file only after both typed answers and the ledger read (a refusal before that spends no id): `~/.hadavin-take-tags/<id>.used` in the Linux home folder (in the WSL window, outside the studio folder on purpose: the studio folder is on the Windows disk and the take refuses it for journals). Do not delete that file to reuse an id: a reused id is refused, and deleting the marker would defeat the check. If you ever want to see which ids are used, list that folder; do not edit it.
- If a login line (shown first, see above) says anything else, nothing was sent; tell the lead; retry at most once (repeated failed logins can trigger a Google sign-in alert).
- During the take: contacts appear in HubSpot, one mail per person appears in the `demo` label. The lead stops and restarts n8n by hand while person C is posted; you do not touch anything.
- STOP and tell the lead: a notice number is not what you approved; any count wrong; the laptop sleeps.

### Step 18. The film pause: type `end`
NEEDS-OWNER. When the script says "Film the contact list now: type `end` and press Enter to archive", the lead films the contact list first. Type `end` and Enter yourself only when the lead says so. The script then archives this take's contacts. Only the exact word `end` ends the pause: a bare Enter or any other line makes the script print "type exactly: end" and ask once more; the second wrong line also prints "type exactly: end" and then the script goes ahead and archives anyway; a closed input on the first prompt ends the pause at once. Ctrl-C or closing the window also still archives.
- STOP and tell the lead: closing the window or Ctrl-C early still archives, but tell the lead; leftover contacts are deleted by you in the HubSpot UI, the lead gives the count.

### Step 19. Filming and cropping hygiene (from the run sheet crop list)
NEEDS-OWNER. Use a fresh Chrome profile named `demo-take`, signed in only to the HubSpot test account, RECEIVER (label `demo` only) and n8n. Before and during recording, make sure NONE of these shows an address other than the made-up take addresses `take-<id>-a@example.com`, `-b@` and `-c@` (the code makes them with `example.com`, not `example.test`): (1) RECEIVER mailbox: the account address in the top bar, the profile menu, the To and From lines of each mail header, the tab title; (2) SENDER mailbox or the Send mail as settings: address fields (do not film them); (3) tab titles and the address bar if they carry an address; (4) the n8n execution list and execution detail panes: only made-up names and the `take-<id>-a/b/c@example.com` addresses, and not an old execution; (5) the table screen: lead keys only; (6) terminal windows: no address in the prompt, history or env output; (7) mail notifications, desktop pop-ups, the system tray. Do not hover your account picture; do not open "show details" on a mail.
- After the take, you scan every frame of the cut: one pass at full speed, one pass of stills at each cut (the frame scan finds no address except `take-<id>-a/b/c@example.com`).
- STOP and tell the lead: any real address is visible. No footage is used until it is cropped or retaken.

### Step 20. If a take fails
NEEDS-OWNER. The lead says why. Remove the demo mails from the `demo` label and the Inbox yourself, delete any leftover HubSpot contacts the lead counted, and give a NEW written yes with numbers (step 16). A take that got past both typed answers uses up its take id even if it fails (a reused id is refused; a refusal before that spends no id): pick a NEW id, never delete the `.used` marker.

## Phase 3: cut, retire, post

### Step 21. Mon 23 Nov before 18:29 UTC: you watch the cut
NEEDS-OWNER (owner decision 3 in plan-4 sense: watch on Mon 23, before the window ends; Claude default). Watch from the first second to the last; reply "accepted" or list the bad seconds. Retirement follows; after it there is no third take.

### Step 22. Retirement, by Mon 23 Nov 18:29 UTC (23:59 IST)
NEEDS-OWNER, after the lead says the last take is done (plan 3.8; the lead does item 1 of step 22, you do items 2 to 6 as listed there).
1. The lead: deletes the 3 credentials in n8n, deletes all saved executions of the take (made-up data only, owner decision 2026-11-16), turns "save successful production executions" back off in each workflow, stops n8n, removes the take folder and the Postgres container.
2. You: revoke BOTH app passwords (RECEIVER `desk-read`, SENDER `desk-send`): myaccount.google.com, Security, App passwords, Remove. Screenshot each empty list.
3. You: delete BOTH HubSpot private apps (Settings, Integrations, Private Apps, Delete). Screenshot.
4. Save the screenshots in `C:\Users\rakes\Downloads\Hadavin\_local\real-run\` under the names the lead gives (v2 used `retire-app-passwords-1.png` and `-2.png`).
5. Run `python scripts/run_real_check_n8n.py --retire-check <take config>` BEFORE you delete the two secret files and while your take config file still exists (keep the config OUTSIDE the take folder, for example in `~/take-secrets`, because the lead removes the take folder in item 1 and the check reads the config; the check needs the two files to try the logins; the code's own clean-up list puts it last, after the revocations, at run_real_check_n8n.py:593-611). It must print "refused as expected" for the mailbox and for HubSpot; exit code 0. "STILL WORKS" (exit 3): delete that credential again and rerun. "could not tell" (exit 2): rerun later. Keep the two files until it passes.
6. Only after the check passed: delete the two secret files in WSL: `shred -u ~/take-secrets/*` (UNVERIFIED that shred is installed; otherwise `rm`). Do NOT delete `~/.hadavin-take-tags/<id>.used`.
- The copy of the passwords inside n8n dies ONLY by your revocation in this step; that is a screenshot, not a check.
- Set laptop sleep and lid settings back; sign out of the demo-take profile.

### Step 23. Post Wed 25 Nov 2026, 15:00 UTC = 20:30 IST
NEEDS-OWNER. You post; Claude never posts. The post says only: leads arrive through n8n; n8n writes the CRM contact and sends the mail; our code caps the spend, asks the model once per lead and counts the mails and contacts on its own credentials; **a lead sent twice with the same id is processed once**. It must NOT say: the same person through two doors is one lead; no lead data stays in n8n; recovery within 60 s; alert within 30 s.

## The three owner decisions in plan-4 section 7, with the lead's defaults

1. **Narrower claim:** "the same lead sent twice with the same id is processed once", NOT "the same person through two doors". Default: yes.
2. **Mailboxes:** throwaway RECEIVER and SENDER, company address only as the shown From. Using the real company mailbox needs your written yes. Default: throwaway.
3. **The 16-hour rule fails** (build about 20 hours on the critical path, about 41 hours total, UNMEASURED estimates). Accept N-lite anyway because of n8n-first and because your steps, not the build, are the real gate. Default: yes.
(Plain-words note: the step numbers 16 to 23 above are kept in the order of the take, so the numbers jump from 9 to 16 on purpose; ignore the gap.)

## What to send the lead (never a secret)

| When | Send |
|---|---|
| By Mon 16 | the sentences of step 9; answers to the three decisions |
| Each take | your yes with numbers (step 16); "label and inbox empty" |
| After a take | "accepted" or the bad seconds |
| Mon 23 | retirement screenshots, retire-check output (counts and words only) |

## Status of the code behind these steps (read before you trust them)

The code is committed on a local take branch; the pinned head is PROVISIONAL and lives in one place: `HEAD_PIN` at the top of the current `wp6\plan-wp6-resmoke-v*.md` (at the time of writing round 3 `take/nlite-int-r3`, round 4 on `take/nlite-int-r4`; source: lead instruction 2026-11-16). The numbers below are from OLD records on OLDER heads (4d7c335 is not the current head; `evidence-int-6\INDEX.md` was on 4d7c335, `evidence-int-5\INDEX.md` on c371935; the later heads 8eba53a and onward changed `n8n_start.sh`, `n8n_kill.py`, the env example and tests, per `architecture-audit\take\review-codebase-1.md` F-02), so they are UNVERIFIED for the current head until a new raw evidence run exists. All records are stand-in services only (no real mailbox, HubSpot, n8n or model call).
Counts on the older head 4d7c335 (copied from `evidence-int-6\INDEX.md`), by test file:
- Six core test files, Windows: 697 passed, 115 skipped (POSIX-only), 0 failed. Same six files, WSL: 810 passed, 2 skipped.
- `test_real_check_take` (the OLD take file) on Windows: 166 passed.
- `test_real_check_n8n` (this take's file), WSL: 445 passed, 0 failed.
- `test_n8n_drive.py`, WSL, 8 runs: 118 passed, 2 skipped each. `qs_01` x20: 20 of 20 on Windows and on WSL. Real-piece tests (WSL): 3 passed.
- Ruff check and format on the 4 source files and on the 2 test files: clean. Bandit: 2 Low notes.
- Mutation batches (run on the earlier head, not re-run): `evidence-int-mut-1` 71 killed, 6 survived (survivors addressed by tests); `evidence-int-mut-2` (money core) 18 killed, 0 survived.
- Independent review rounds 3 to 9 are done. WP6 smoke plan v3 is pending.

NOT YET VERIFIED (do not read the numbers above as "ready"):
- A real n8n run, and the Code-node key probe (the WP6 smoke test): not run.
- Real Gmail label behaviour (the filter, the label `demo`, how IMAP shows it): not run.
- The code was never run against a real Gmail, HubSpot, n8n or model call: every click path and server behaviour in the steps above is still UNVERIFIED.
- Your written yes with the numbers (step 16) does not exist yet. No paid take happens without it.
- The take does not check by itself: the alert mail, mail in any folder other than `demo`, the CRM id read back from HubSpot (it is only checked to be all digits; it is not compared with the table's crm_id), the manual n8n kill and restart, and the second door (the hook door).

## Refusals, deadline and exit codes (from the code)

- Lock file: if the take stops hard and leaves `take-<tag>.lock` beside the take folder, the next take with the same tag is refused ("a take with this TAKE_TAG is running (or died): its lock file exists beside the take folder"). Delete that file by hand ONLY when the lead says so. (A normal end removes it; if removal fails the take says "delete it by hand".)
- Take-start deadline: the take refuses to start unless it can finish about 860 s (about 14 minutes; the code's message says "about 15 minutes") before `TAKE_WINDOW_END_UTC`. With the window end at 23 Nov 2026 18:29Z the last start is about 18:14Z (the refusal is now + 860 s >= end, so before 18:14:40Z at the default lease). The exact figure depends on the lease setting (`need_seconds` in the script).
- Exit codes: 0 pass; 1 the answer was not y or the confirmation line did not match; 2 a refusal (config, probe, no keyboard, end of input, Ctrl-C BEFORE the first send (after the sends began it is exit 3 with the text 'interrupted after the sends began'), too fast, tag or keys already used, lock exists, window too close, second mailbox); 3 a count or verdict failure. For `--retire-check`: 0 both refused, 3 a login still works, 2 anything else.

## Optional name in the take config file

`TAKE_MIN_ANSWER_SECONDS` (default 2, allowed 1 to 60): an answer typed faster is refused. Leave it unset unless the lead asks. The Gmail label is still `demo`, but it is now a REQUIRED config line: `REAL_IMAP_1_FOLDERS=demo` (any other value is refused; an omitted line stops the take with "the take config lacks: REAL_IMAP_1_FOLDERS"). The example file is `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\nlite-int\scripts\real-run-n8n.env.example`.

## UNVERIFIED list (count: 13)

1. Click paths in Google (app passwords, filter, Send mail as), HubSpot and n8n were not checked on your accounts.
2. Gmail SMTP accepting the company address as From, and what "mailed-by" shows.
3. Gmail filtering a mail that another Gmail account sent, and the delay.
4. Whether the receiver account is allowed app passwords (2-Step, account type).
5. HubSpot scope names for the private apps.
6. Whether the n8n HubSpot flow needs properties beyond `hadavin_label` and `hadavin_lead_id`.
7. SMTP host and port for the n8n credential.
8. The Windows browser reaching n8n in WSL at localhost.
9. The per-call worst-case dollar figure (the lead types it from the stage settings; the program only checks it is a finite number above 0 that can be shown).
10. (Removed: the typed 6-digit challenge plus take id now exists in the code; still not run against a real keyboard session.)
11. Exact take command line and config path (the lead gives them).
12. Whether `shred` exists in your WSL.
13. The window end text format: the code expects `YYYY-MM-DDTHH:MMZ` (read from the code, not run).
14. Whether Gmail's IMAP shows the label `demo` as a folder named `demo` for the take program.
