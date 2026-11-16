# DAY CARD v14 (run day: what you type, what the screen shows, when to stop). Print it.

Version 14, written Mon 16 Nov 2026 (draft until the stamp below is filled). UTC and IST. Words are in `OWNER-STEPS-realrun-v14.md`. **Two windows:** the **run window** (the WSL window of the program) and the **check window** (a second WSL window). **In the run window you type only:** `cd`, `clear`, the start line, `y`, the confirmation line, `end`, `echo $?`. Every other command (`ls`, `sha256sum`, `pgrep`, `date`, `grep`) goes in the check window. The studio lead shuts down and starts n8n itself; you never do. "THE STUDIO LEAD FILLS THIS IN" = a value only the studio lead has; a blank left on the card means the card is incomplete: ask, never guess.

## The blanks (the studio lead fills them in; the row numbers are the run card's)
**Stamp:** every command and screen on this card was checked in a rehearsal on ________ (UTC / IST) by the studio lead; transcript file: ________ . No stamp: Freeze, do not use this card. A screen that differs from this card on the day: Freeze.

| Item | Value (THE STUDIO LEAD FILLS THIS IN) |
|---|---|
| Run name; date; **latest start time** UTC / IST (row 3; = money stop minus run length, longest film pause and 5 minutes); normal run length (minutes); lease length (seconds) | ________ |
| Person who films (row 4; never you); who says "recording" (row 5); who edits and crops (row 6); who says "filmed" (row 7) | ________ / ________ / ________ / ________ |
| Deadlines UTC / IST: cancel the model key (same day, row 11); watch video; clean-up; post by Wed 25 Nov 2026 15:00 UTC = 20:30 IST | ________ |
| Run folder; run settings file name; model settings file; model key file (row 12), full paths | ________ |
| The `cd` line (must equal the run folder) | ________ |
| n8n address with the run's port (row 13; the port is not 5678 or 5679) | ________ |
| Minutes of silence before Freeze (row 16); longest film pause in minutes (row 17) | ________ / ________ |
| What the program does when the film pause ends without `end` (blank B11) | ________ |
| Commit id and checksum of `scripts/run_real_check_n8n.py` (row 19; 8 groups of 8 characters); every other file the program uses, with checksum (the checksum list) | ________ |
| Model program command line (row 23) | ________ |
| Model account: usage page address; key list page address; account name shown on both | ________ / ________ / ________ |
| Per-key spend limit: exists (page, amount) or "none exists" | ________ |
| Command that prints the ledger total | ________ |
| HubSpot test account name and last 4 digits of its number; take key permission names | ________ / ________ / ________ |
| Call ceiling; worst-case price per call; run total; expected rise before E (US$0 unless a trial ran) | ________ / ________ / ________ / ________ |
| Alert-mail address (one of your two throwaway accounts) | ________ |
| Exit-code rule for C "unknown": the cell reads `none`, or one number plus the exact printed result it covers; anything else: ask | ________ |

## Which word to use (precedence: the top row wins)
1. **Key exposed** (a long key-like string on screen, a checksum from `sha256sum` excepted; any doubt = key): **Recording OFF first; keep that take for the studio lead only, never publish it.** Cancel that key, revoke that app password or delete that private app, close the window it is in (not the run window while the program runs), send only "a key-like text was on the screen", then Freeze.
2. **Emergency cancel** (money): cancel every model key, **the run key too**, at the key list page above, check the list, send the figures, then Freeze. Cancelling is always allowed, also while frozen.
3. **Freeze:** type nothing more in the run window, close nothing, send the studio lead **words only** (never a screenshot or copied text; name the screen: "notice", "usage page"), wait. At "Type y to start" type `n`. Freeze never stops F.4 or I.0 (browser only).
4. **Stop:** this step ends, go on to nothing, tell the studio lead. Also used when a figure in a message changed: no run until a new typed yes.

## E.0 Before E (tick each; check window unless it says run window)
- [ ] Go message for this run name states all 9 go items (5 and 6 included) and says **REAL run**, with the run name you will type. A trial run: Recording stays OFF for the whole run.
- [ ] The alert-mail address in the message is one of your two throwaway accounts; the HubSpot last 4 digits match the blank (never on film). Otherwise no E.
- [ ] Recording OFF; nobody shares the screen. It starts at "Recording ON" below.
- [ ] Money rule redone, **E reading** written (balance, money used so far, time). Key list: run key only (plus keys with your reason and end date). Balance at least the run total. Ledger total printed by you with the command above equals the message; backstop in the file is no higher than that plus the run total. Any rise since the A reading beyond "expected rise before E": Emergency cancel.
- [ ] `ls -l --time-style=full-iso "<model settings file>"` shows the A.1 time. Changed: Freeze.
- [ ] `sha256sum` of each file in the checksum list equals the blanks above (all 8 groups). Different: Freeze.
- [ ] `pgrep -af "<model program command line>"` prints exactly one line with the process number from the go message. `date` is within 2 minutes of the Windows clock.
- [ ] **Time:** E.0 begins at least 20 minutes before the latest start time; E.1 is at or before it.
- [ ] The studio lead says in writing that n8n is up and that it will shut down and start n8n itself during the run. You do nothing for n8n.
- [ ] The people above are ready. In the run window: the `cd` line, then `clear`. [ ] Recording ON (person who says "recording").

## E. Start (run window)
1. Type: `python3 -I scripts/run_real_check_n8n.py --take <run settings file name>` Enter (the file name only, no folder). Screen, in order: `mailbox login: still works`, `HubSpot login: still works`, then the notice, then "Type y to start". Anything else: Freeze; do not start again (repeated failed logins can trigger a Google alert).
2. **Compare the notice, 5 minutes at most; at minute 5 type `n`.** The studio lead's sample of the notice is appendix 5 (invented; the real wording is blank B9: compare numbers and names, not layout). Type `n` and Enter (nothing is sent to n8n or HubSpot; the model program keeps running and the run key stays valid until I.0) if ANY is true: price per call is not the blank above; total is not the run total above or is more than your yes; you cannot find a line; money stop ("window end") is not 2026-11-23 18:29 UTC = 23:59 IST; people, calls or mails are more than 3; run name is not yours; any line says contacts will be deleted or archived (the notice may keep old wording, see blank B9: type `n` and send the line); the notice shows masked accounts and they are not your two throwaway accounts; **the notice shows no masked accounts and the go message did not say, in the same message, that the program does not print them and that you accept it.** Masked accounts and the path on this screen are cropped from the video (appendix 14 item 10).
3. Type `y` Enter with your own hands. Never a tool, script or helper window (any other window or program that types for you).
4. Read the 6-digit number off the screen and type it, a space, the run name, Enter. Under 2 seconds: exit code 2, nothing sent; wrong line: exit code 1, nothing sent. In either case do not start again: send the number; the studio lead says in writing whether the run name can be used again and sends a new go message. Otherwise send "run started".

## While it runs (you type nothing in the run window)
- 13 sends and the paid model calls. The studio lead shuts down and starts n8n during the sends; you do nothing.
- No new line printed for the minutes in the blanks (not counting the film pause): Freeze. No Ctrl-C, no closing the window.
- Contacts appear in HubSpot, mails under label `demo`. The model program keeps running during the film pause.

## F. Film pause and finish
1. The program prints a line asking you to film the contact list and type `end`. The person who films shows HubSpot Contacts, search `take-<run name>` (else newest first). Expect 2 or 3 contacts (C may be "unknown"). Other number: Freeze, do not type `end`; send the count; type `end` only after the studio lead's written word, before the longest film pause (blank above) is over; if it runs out first, the blank above says what the program does. The silence rule does not apply during the pause.
2. The person who says "filmed" says it (a trial run: you look at the contact list yourself). Then **look at the screen for the line that asks for `end`, look at the keyboard, and type exactly `end` with no space and a small e, Enter.** A wrong word prints "type exactly: end" once; a second wrong line, Ctrl-C or closing the window ends the pause early with exit code 3 and deletes nothing (lead verifies at re-pin).
3. Recording OFF. With `$` back: `echo $?` Enter. **0 = ok. Any other number: Freeze, unless the studio lead's written exit-code rule (blank above) names exactly that number for exactly this printed result.** Send the number and the last printed line; delete nothing.
4. Usage page (browser; Freeze does not stop this): write balance and money used so far; add the increase to the running total. Over the run total: Emergency cancel. Send: exit code, last printed line, balance and money used before and after. Read the printed result: A and B each 1 contact and 1 mail; C "unknown" only if the exit-code rule allows it. A or B different: do not post, send the printed result. **Then cancel the model key (step I.0), the same day; do not wait for the studio lead.**
5. Contacts by hand: the studio lead sends the list (it includes any leftover contact of step 0): per contact, the test address (a made-up address ending `@example.com`) and the masked contact id. In HubSpot (account name equals the blank above) search the run name, tick only contacts whose address is on the list, one by one (never select-all), count the ticks: if the count differs from the list, or a ticked address is not on it: Stop and send. Then More, Delete. Send "contacts deleted" and the number.

## Stop rules (any time; the table above says which word)
- Money: running total of increases above the run total, or a rise before E beyond the expected figure: Emergency cancel (the money figure is never a Freeze).
- A figure changes in any message (price, tokens, call ceiling, backstop, ledger total, money stop): Stop (no run) until a new typed yes.
- A screen you do not recognise or a laptop sleep: Freeze.
- Exit code not accepted (F.3): Freeze; no second start; deletions only from the studio lead's list.

## After
- [ ] I.0 cancel the model key (same day, deadline in the blanks). [ ] Watch the video (H). [ ] Clean-up (I). [ ] Post (J) only with the studio lead's written confirmations.
