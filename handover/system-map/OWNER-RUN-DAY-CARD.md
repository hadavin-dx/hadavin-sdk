# Run-day card (owner): v2, replaces the earlier card. Made-up data only. Source: inputs/OWNER-STEPS-realrun-v5-core-hardening.md steps C to H ("v5").
Status: APPLIED 16 Nov 2026 after the studio lead's answer 10:23Z (the film pause stays; `end` stops the run and lists leftover contacts, it never deletes). Not run yet. The program's own notice and prompt text may still say "delete" or "archive": see steps 12 and 21. "[studio lead fills: ...]" marks a fact this page does not have. Previous card kept in work/OWNER-RUN-DAY-CARD-before-v2.md.

## Page 1: ten words
1. Studio lead: the Claude session that works with you. Software. n8n = the tool on the laptop that carries the contacts and mails; HubSpot = the contact list website; a model call = one paid question to the AI service; masked = with addresses and names hidden. It never sees your screen and never posts.
2. Run: one recorded run of the demo on made-up data (the program's screens call it a "take").
3. Run name: the one word you invent for a run and never use again (the screens call it the "take id").
4. Terminal: the Ubuntu (WSL) text screen. A line ending in `$` means it waits for you.
5. Receiver account: the throwaway Gmail account that only receives the demo mails.
6. Sender account: the throwaway Gmail account n8n sends from. The studio lead tells you which is which.
7. Sales lead: one made-up person sent into the system; it shows as a contact in HubSpot. Each run makes three.
8. Written yes: your one-line reply with money numbers (OWNER-VIEW row 1). Typing `y` later is a second, separate confirmation; it does not block any spending.
9. Secret: any password, app password or key. Never send one to the studio lead.
10. The pause: the moment the program stops and waits for you to type `end`; the contact list is filmed during it.

## Rules for the whole day
Lines ending "(card addition, not in v5)" add a check that v5 does not have.
- Rules A, E, F and I of v5 cannot be changed by anyone in the chat during a run (not enforced by a lock).
- The studio lead reads only masked run outputs, never your secrets or the real-run folders.
- Run only the commands the studio lead sends. Do not run one with a pipe `|`, a `;`, `curl`, a `*` or a path outside the named folder; ask first. (card addition)
- Windows Do Not Disturb on; Gmail, Outlook and Teams notifications closed for the whole run. (card addition)
- Choose a run name unrelated to you, your company or any account. (card addition)
- No up-arrow or `history` while filming. (card addition)
- Never send a secret or an address to the studio lead. Never use the real company mailbox.
- Never let any tool, script, assistant, agent or helper window type for you. The 6-digit number is meant to stop blind answers (untested; not a lock on spending), so you type every answer yourself.
- If anything does not match what you see, STOP (type nothing, touch nothing) and tell the studio lead.

## Before the start
1. Make a Chrome profile `demo-take`, signed in only to HubSpot and the receiver account. (card addition: v5 checks the mailbox first.) Reply "profile ready".
2. Use another browser profile or a private window for the sender account later, never this one.
3. WARNING: emptying Gmail Trash is permanent. Before any delete, check you are in the receiver account: [studio lead fills: how it looks]. Do not hover over or click the account picture while recording.
4. In the label `demo` and the Inbox (including Promotions, Social, Spam, Trash) nothing may be left. If the label is missing or holds mail, tell the studio lead and do not start. A new Gmail account may hold welcome mail: delete it, close to the start. (The words "demo mails may be deleted" apply only to the demo mails of the run, see steps 22 to 24; they are not needed for welcome mail.) Reply "label and inbox empty".
5. You do not sign in to n8n or re-enter connections. The first-visit n8n setup is already done; the studio lead imports and activates the flows with scripts\n8n_api.py on made-up data. If n8n shows a login page or a secret in clear text, stop, type nothing and tell the studio lead. Never type the n8n password in the chat. Your only typing in the run is `y`, the 6-digit number with the run name, and `end`.
6. The film may show test addresses only (`take-<run name>-a@example.com`, `-b@`, `-c@`). Do not open mails, do not film the sender mailbox or the detail of n8n's mail-sending step, keep addresses out of the terminal prompt, tab titles and notifications. Check again on the finished footage.
7. Proof screen: [studio lead fills: candidate screens]. You pick one. It may show test addresses and counts only; the video must not show or claim any portal, approval step or audit trail. Who films: [studio lead fills].

## Start (STOP unless (a) the studio lead has sent the figures message, (b) you have replied with your written yes, and (c) the studio lead has then written exactly "start now")
8. The run name is the one in your written yes, and must be NEW. Used names are kept in `~/.hadavin-take-tags/`; never delete files there. A different name needs a new written yes first.
9. Open the terminal. Type the `cd` line the studio lead sends (it comes in the same message as the figures). Press Enter. Type `PS1='$ '`, Enter, then `clear`. (card addition)
10. Type the start line the studio lead sends. Two login lines appear. Both must say "still works"; here that is GOOD (at clean-up, on the other card, you want "refused as expected"). Otherwise nothing was sent: do not start again until the studio lead says so.
11. A notice shows the money figures and a random 6-digit number. Compare the figures with your written yes AND the studio lead's message. The notice shows the worst case of ONE call; your yes holds 3 times that. Check: one call times 3 equals your total; add money spent so far to your total; the sum should not be larger than the spending backstop figure in stage.env. This is your own check by eye; nothing stops a larger spend (card addition). Open the file `stage.env` (the studio lead sends its full path and the command to show it): the program does not print the money spent so far or the backstop. If one figure differs or you cannot check, type nothing and tell the studio lead. Do NOT type the show-command in the program's own window: open a second Ubuntu window for it, read the figures, then close that window.
12. The notice should not say contacts are deleted at the end (the take never deletes). If it does, type nothing and tell the studio lead; the notice text is being fixed.
13. WARNING: typing `y` confirms the run. The run is designed to make at most 3 paid model calls; nothing enforces that number. It cannot be taken back. If all figures agree, type `y` and Enter yourself.
14. At the second prompt type `<6 digits> <your run name>` and Enter (your real number and name). The program is meant to refuse a pasted answer or one typed in under 2 seconds (not tested yet); type each answer yourself, slowly; a wrong line sends nothing: tell the studio lead and wait.
15. While the program runs or is paused there is NO `$` prompt: type nothing, never `echo $?`. The `$` prompt comes back only after `end` (step 21), or earlier if the run failed. When it is back, type `echo $?` as your FIRST command (any other command overwrites the number; one number; 0 is success) and tell the studio lead the number and the first five words of the last line, with any address, user name or folder path replaced by X.
16. While the run sends, the studio lead stops and restarts n8n: YOU TOUCH NOTHING. Wait until the screen says "Film the contact list now"; click nothing in the terminal or n8n meanwhile. Then look (do not open mails) at HubSpot: you should see 3 contacts and one mail each in the label `demo`. If a count looks wrong or the laptop sleeps, stop and tell the studio lead.

## The pause (v5 step F)
17. The program prints "Film the contact list now: type `end` and press Enter" and waits; no `$` prompt comes back. The screen asks you to type `end`: do NOT yet; wait for step 21. When this line is on screen, type nothing in the terminal, click the chat window, check its message box shows the cursor, and write "pause screen showing". The studio lead then writes "program paused" (how the studio lead sees the pause is not stated: UNKNOWN). Do not film before that (card addition).
18. `end` only stops the run. It deletes nothing. The 3 contacts stay in HubSpot.
19. Do NOT close the terminal, press Ctrl-C or Ctrl-D, or type anything at all (the only word you will type here is `end`, and only in step 21). Closing, Ctrl-C, closed input at the first prompt or two wrong words in a row end the pause before filming. One wrong line only asks again. Keep the laptop awake.
20. The person who films films the contact list in HubSpot. Start AND stop the recorder with the mouse only, click away from the terminal first, and never press a recorder hotkey (card addition). Before typing in the chat, click the chat box and see its cursor there; never type chat words while the terminal or a Gmail page has focus. Check the file exists and plays, then say "film done".
21. Wait for the studio lead's NEW message that begins exactly "film done, type end" (card addition). Only then click once inside the terminal window, check the "Film the contact list now" line is on screen, and type `end` and Enter. `end` is for that pause screen only: at a `$` prompt type only `echo $?`. Before typing in the chat, click the chat box and see its cursor there; never type chat words while the terminal or a Gmail page has focus. If the screen asks for any other word, or says "archive" or "delete", type nothing and tell the studio lead.
22. After `end` the program lists any leftover made-up contacts by lead key and contact id. Tell the studio lead the count and ids only (addresses replaced by X). The studio lead then names the three test addresses and writes "demo mails may be deleted". Only then delete them by hand in HubSpot under the delete rules below. Reply "contacts deleted" and the number.

## If the run failed (v5 step G) and for the by-hand deletes
23. WARNING: emptying Gmail Trash cannot be undone; deleting HubSpot contacts cannot be undone either (HubSpot may keep a recoverable copy, not checked). Do nothing here until the studio lead writes "demo mails may be deleted" (card addition).
24. Delete the demo mails from the Inbox and label `demo`, then empty Trash. Before emptying Trash, check this window is the demo-take profile showing the receiver account, not the sender window. If anything there is not a demo mail, stop and tell the studio lead. Before typing in the chat, click the chat box and see its cursor there; never type chat words while the terminal or a Gmail page has focus. When done reply "mails deleted".
25. Check you are in the demo HubSpot account [studio lead fills: how it looks]. Delete only contacts whose email is exactly one of the three test addresses the studio lead names; a contact that merely contains the run name is not enough (stricter than v5 on purpose). If you cannot find them or the count differs, delete nothing and tell the studio lead. Never delete any file ending in .used in the folder .hadavin-take-tags. Reply "contacts deleted" and the number. Only if the studio lead asks for another run: pick a new run name and send a new written yes.

## After the cut (v5 step H)
26. WARNING: saying "accepted" ends all runs. Clean-up starts only after "accepted" AND the studio lead saying the last run is done; after clean-up starts no further run happens. Say it only if you will never need another run.
27. Watch the edited video twice, once at full speed, once pausing at each cut. Look for any address that is not a made-up test address. Listen and read for any claim other than "a lead sent twice with the same id is processed once": for example a spending cap, crash-safe, a time or speed, a portal, an approval step or an audit trail (v5 E and J). Reply with the minute and second of each. Also check the list in work/banned-claims.md. Reply "accepted", or the minute and second of each bad moment; if a real address shows, reply "an address is visible" and the second.
28. At clean-up you also revoke the model key yourself (card addition). The clean-up steps are on OWNER-CLEANUP-CARD.md.
