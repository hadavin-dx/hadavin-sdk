# Run-day card (owner): follow in order, one action per line
Made-up data only. Source: inputs/OWNER-STEPS-realrun-v5-core-hardening.md steps C to H (called "v5" below). Not run against real accounts yet; the "you will see" lines are what v5 expects, not tested results. Times: Mon 16 Nov 2026 is the date this was written; the run date and start time come from the studio lead in UTC and IST.

**Rules for the whole day.** Never send a secret or an address to the studio lead. Never use the real company mailbox. Never let any tool, script, assistant, agent or helper window type for you: the 6-digit number is only a weak block, so you type every answer yourself. If anything below does not match what you see, STOP and tell the studio lead.

**Before the start**
1. Check the Gmail label `demo` and the Inbox of the receiver account are empty. If the label holds mail or is missing: tell the studio lead and do not start. If empty, reply "label and inbox empty".
2. Make a Chrome profile `demo-take`, signed in only to HubSpot and the receiver account. Reply "profile ready".
3. Only if the studio lead asks: n8n login and connections (your n8n account already exists; this screen appears because the take uses a new, empty n8n database). Copy secrets with no recording running and nobody watching; then type `clear` in the window; never type the n8n password into the chat. If n8n shows a secret in clear text, stop and tell the studio lead. Reply "done".
4. What the film may show: only test addresses. Do not hover over the account picture, do not open mails, do not film the sender mailbox or the detail of n8n's mail-sending step, and keep addresses out of the terminal prompt and notifications. Check again on the finished footage.
5. Pick the proof screen (the one screen shown as proof) and tell the studio lead which.

**Start (STOP unless the studio lead has your written yes, see OWNER-VIEW row 1)**
6. Pick a NEW run name (one you have never used; used names are kept in `~/.hadavin-take-tags/`, never delete that folder's files). Send it to the studio lead.
7. Open the Ubuntu terminal (WSL). Type the `cd` line the studio lead sends and press Enter.
8. Type the start line the studio lead sends and press Enter. You will see two login lines. Both must say "still works". If not, nothing was sent: do not restart until the studio lead says so.
9. A notice appears with the money figures, what will happen (up to 3 contacts, up to 3 mails, n8n started once) and a random 6-digit number. Compare the money figures with your written yes. If one differs: type nothing and tell the studio lead.
10. If all agree: type `y` and Enter yourself at the first prompt. Then, at the second prompt, type the 6-digit number, a space and your run name, Enter (example: `123456 myrun1`). Piped input and an answer typed in under 2 seconds are refused; a wrong line sends nothing: tell the studio lead and wait.
11. If the run stops: type `echo $?` and report the number and the last line to the studio lead. If a count looks wrong or the laptop sleeps, stop and tell the studio lead.
12. You should see 3 contacts in HubSpot and one mail each in the label `demo`, and the program pauses.

**THE PAUSE: DANGER, `end` DELETES THE 3 CONTACTS**
13. Do NOT close the terminal, do NOT press Ctrl-C, do NOT type anything else. Each of those, or two wrong words in a row, ends the pause and deletes the contacts before they are filmed. HubSpot may keep a recoverable copy for some time (not checked).
14. The person who films (named by the studio lead; it may be you) films the contact list in HubSpot.
15. Only when that person says "film done" in the chat (or you finished filming yourself): type exactly `end` (three lower-case letters) and Enter. The program says the contacts were deleted. If the terminal was closed early, tell the studio lead; leftovers are deleted by hand and the studio lead gives the count.

**If the run failed (v5 step G)**
16. Empty the demo mails from the receiver Gmail (Inbox, label `demo`, then Trash). Delete only the HubSpot contacts the studio lead counted and that carry this run name; check first that you are in the demo account. Never delete `~/.hadavin-take-tags/<run name>.used`. Reply "demo mails deleted" plus the number of contacts.
17. Pick a new run name and give a new written yes.

**After the cut (v5 step H)**
18. Watch the edited video twice: once at full speed, once pausing at each cut. Look for any real address on screen. Reply "accepted", or the minute and second of each bad moment; if a real address shows, reply "an address is visible".
