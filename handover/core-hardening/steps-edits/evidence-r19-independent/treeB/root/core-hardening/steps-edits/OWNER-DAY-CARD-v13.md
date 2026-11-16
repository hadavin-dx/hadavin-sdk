# DAY CARD v13 (run day: what you type, what the screen shows, when to stop). Print it.

Version 13, written Mon 16 Nov 2026 (draft until the stamp below is filled). UTC and IST. Words are in `OWNER-STEPS-realrun-v13.md`. **You type in the run window only**: the start line, `y`, the confirmation line, `end`, `echo $?`. **Run window** = the WSL window of the program. The studio lead shuts down and starts n8n itself; you never do. "THE STUDIO LEAD FILLS THIS IN" = a value only the studio lead has; a blank left on the card means the card is incomplete: ask, never guess.

## The blanks (the studio lead fills them in; the row numbers are the run card's)
**Stamp:** every command and screen on this card was checked in a rehearsal on ________ (UTC / IST) by the studio lead; transcript file: ________ . No stamp: Freeze, do not use this card. A screen that differs from this card on the day: Freeze.

| Item | Value (THE STUDIO LEAD FILLS THIS IN) |
|---|---|
| Run name; date; latest start time UTC / IST (row 3); normal run length (minutes); lease length (seconds) | ________ |
| Person who films (row 4); who says "recording" (row 5); who edits and crops (row 6); who says "filmed" (row 7) | ________ / ________ / ________ / ________ |
| Deadlines UTC / IST: cancel the model key (same day, row 11); watch video; clean-up; post by Wed 25 Nov 2026 15:00 UTC = 20:30 IST | ________ |
| Run folder; run settings file; model settings file; model key file (row 12), full paths | ________ |
| n8n address with the run's port (row 13; the port is not 5678 or 5679) | ________ |
| Minutes of silence before Freeze (row 16); longest film pause in minutes (row 17) | ________ / ________ |
| Commit id and checksum of `scripts/run_real_check_n8n.py` (row 19; 8 groups of 8 characters); every other file the program uses, with checksum | ________ |
| Model program command line (row 23) | ________ |
| Model account: usage page address; key list page address; account name shown on both | ________ / ________ / ________ |
| Per-key spend limit: exists (page, amount) or "none exists" | ________ |
| Command that prints the ledger total | ________ |
| HubSpot test account name; take key permission names | ________ / ________ |
| Worst-case price per call; run total; expected rise before E (US$0 unless a trial ran) | ________ / ________ / ________ |
| Exit-code rule for C "unknown" (a number, or "none": then C "unknown" is Freeze) | ________ |

## Which word to use (precedence: the top row wins)
1. **Key exposed** (a long key-like string on screen, a checksum from `sha256sum` excepted; any doubt = key): cancel that key or delete that private app first, close the window it is in (not the run window while the program runs), send only "a key-like text was on the screen", then Freeze.
2. **Emergency cancel** (money): cancel every model key not on your written list at the key list page above, check the list, send the figures, then Freeze. Cancelling is always allowed, also while frozen.
3. **Freeze:** type nothing more, close nothing, send the studio lead what the screen shows, wait. Only exception: at "Type y to start" type `n`.
4. **Stop:** this step ends, go on to nothing, tell the studio lead.

## E.0 Before E (tick each)
- [ ] Go message for this run name states all 9 go items (5 and 6 included). One missing: no E.
- [ ] Recording OFF; nobody shares the screen. It starts at "Recording ON" below.
- [ ] Money rule redone, **E reading** written (balance, money used so far, time). Key list: run key only (plus keys with your reason and end date). Balance at least the run total. Ledger total printed by you with the command above equals the message; backstop in the file is no higher than that plus the run total. Any rise since the A reading beyond "expected rise before E": Emergency cancel.
- [ ] `ls -l --time-style=full-iso "<model settings file>"` shows the A.1 time. Changed: Freeze.
- [ ] `sha256sum` of each file in the checksum cell equals the blanks above (all 8 groups). Different: Freeze.
- [ ] `pgrep -af "<model program command line>"` prints exactly one line with the process number from the go message. `date` is within 2 minutes of the Windows clock.
- [ ] Start is at least 20 minutes before the latest start time.
- [ ] The studio lead says in writing that n8n is up and that it will shut down and start n8n itself during the run. You do nothing for n8n.
- [ ] The people above are ready. `clear` in the run window. [ ] Recording ON (person who says "recording").

## E. Start
1. Type: `python3 -I scripts/run_real_check_n8n.py --take <run settings file>` Enter. Screen, in order: `mailbox login: still works`, `HubSpot login: still works`, then the notice, then "Type y to start". Anything else: Freeze; do not start again (repeated failed logins can trigger a Google alert).
2. **Compare the notice, 5 minutes at most** (layout may differ from appendix 5; compare numbers and names). Type `n` and Enter (nothing is sent) if ANY is true: price per call is not the blank above; total is not the run total above or is more than your yes; you cannot find a line; window end is not 2026-11-23 18:29 UTC = 23:59 IST; people, calls or mails are more than 3; run name is not yours; any line says contacts will be deleted or archived; the masked accounts shown are not your two throwaway accounts. Masked accounts and the path on this screen are cropped from the video (appendix 14 item 10).
3. Type `y` Enter with your own hands. Never a tool, script or helper window (any other window or program that types for you).
4. Read the 6-digit number off the screen and type it, a space, the run name, Enter. Under 2 seconds: exit code 2, nothing sent; wrong line: exit code 1, nothing sent. Then send "run started".

## While it runs (you type nothing in the run window)
- 13 sends and 3 paid model calls. The studio lead shuts down and starts n8n during the sends; you do nothing.
- No new line printed for the minutes in the blanks (not counting the film pause): Freeze. No Ctrl-C, no closing the window.
- Contacts appear in HubSpot, mails under label `demo`. The model program keeps running during the film pause.

## F. Film pause and finish
1. The program prints a line asking you to film the contact list and type `end`. The person who films shows HubSpot Contacts, search `take-<run name>` (else newest first). Expect 2 or 3 contacts (C may be "unknown"). Other number: Freeze, do not type `end`. The film pause is at most the minutes in the blanks; the silence rule does not apply during it.
2. The person who says "filmed" says it (a trial run: you look at the contact list yourself). Then type exactly `end` Enter. A wrong word prints "type exactly: end" once; a second wrong line, Ctrl-C or closing the window ends the pause early with exit code 3 and deletes nothing (lead verifies at re-pin).
3. Recording OFF. With `$` back: `echo $?` Enter. **0 = ok. Any other number: Freeze, unless the studio lead's written exit-code rule (blank above) names exactly that number for exactly this printed result.** Send the number and the last printed line; delete nothing.
4. Usage page: write balance and money used so far; add the increase to the running total. Over the run total: Emergency cancel. Send: exit code, last printed line, balance and money used before and after. Read the printed result: A and B each 1 contact and 1 mail; C "unknown" only if the exit-code rule allows it. **Then cancel the model key (step I.0), the same day; do not wait for the studio lead.**
5. Contacts by hand: the studio lead sends the list: per contact, the test address (a made-up address ending `@example.com`) and the masked contact id. In HubSpot (account name equals the blank above) search the run name, tick only contacts whose address is on the list, one by one (never select-all), count the ticks: if the count differs from the list, or a ticked address is not on it: Stop and send. Then More, Delete. Send "contacts deleted" and the number.

## Stop rules (any time; the table above says which word)
- Money: running total of increases above the run total, or a rise before E beyond the expected figure: Emergency cancel.
- A figure changes in any message (price, tokens, backstop, ledger total, window end): no run until a new typed yes.
- A screen you do not recognise, a laptop sleep, a number you did not approve: Freeze.
- Exit code not accepted (F.3): Freeze; no second start; deletions only from the studio lead's list.

## After
- [ ] I.0 cancel the model key (same day, deadline in the blanks). [ ] Watch the video (H). [ ] Clean-up (I). [ ] Post (J) only with the studio lead's written confirmations.
