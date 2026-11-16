# DAY CARD v12 (run day: what you type, what the screen shows, when to stop). Print it.

Mon 16 Nov 2026 draft. UTC and IST. Words are in `OWNER-STEPS-realrun-v12.md`. **FREEZE** = type nothing more, close nothing, send the studio lead what the screen shows, wait. **STOP** = this step ends, go on to nothing. `[UNVERIFIED]` = the writer never ran this command; a different screen means FREEZE. "Row N" = run card row. **Run window** = the WSL window of the program. **You type in the run window only**: the start line, `y`, the confirmation line, `end`, `echo $?`. The studio lead shuts down and starts n8n itself; you never do.

## Before E (tick each)
- [ ] Go message for this run name received; it states all 9 go items (items 5 and 6 included). One missing: no E.
- [ ] Recording OFF; nobody shares the screen. It starts at the tick "Recording ON" below, not before.
- [ ] Money rule redone, E reading written (balance, money used): key list = run key only (plus keys you wrote a reason and end date for); balance at least the run total; backstop no higher than the ledger total in the message plus the run total; any increase since the A reading: EMERGENCY CANCEL.
- [ ] Settings lines unchanged since A.1: `ls -l --time-style=full-iso "<model settings file>"` shows the A.1 time [UNVERIFIED]. Changed: FREEZE (restart and go item 6 repeat).
- [ ] `sha256sum scripts/run_real_check_n8n.py` equals row 19 [UNVERIFIED].
- [ ] `pgrep -af "<model program name, row 23>"` prints exactly one line with the process number from the go message [UNVERIFIED]. `date` within 2 minutes of the Windows clock [UNVERIFIED].
- [ ] Start is at least 20 minutes before the latest start time (row 3).
- [ ] The studio lead says in writing that n8n is up and that it will shut down and start n8n itself during the run with `n8n_kill.py` and `n8n_start.sh`. You do nothing for n8n. Lead checks at re-pin that the program prints no extra cue: UNVERIFIED.
- [ ] Persons on rows 4, 5, 7 ready. `clear` in the run window. [ ] Recording ON (person on row 5).

## E. Start
1. Type: `python3 -I scripts/run_real_check_n8n.py --take <run settings file>` Enter [UNVERIFIED]. Screen, in order: `mailbox login: still works`, `HubSpot login: still works`, then the notice, then "Type y to start". Anything else: FREEZE; do not start again (repeated failed logins can trigger a Google alert).
2. **Compare the notice, 5 minutes at most.** Type `n` and Enter if ANY is true: the price per call is not the one in your yes; the total is not 3 times it or more than your yes; you cannot find a line; the window end differs (2026-11-23 18:29 UTC = 23:59 IST); people, calls or mails are more than 3; the run name shown is not yours; any line says contacts will be deleted or archived; the notice prints masked accounts that are not your two throwaway accounts. (Layout may differ from the sheet's sample in appendix 5; compare numbers and names.)
3. Type `y` Enter yourself, at once. Never a tool, script or helper window.
4. Type the 6-digit number from the notice, a space, the run name, Enter. Faster than 2 seconds: exit code 2, nothing sent. Wrong line: exit code 1, nothing sent. Then send "run started".

## While it runs (you type nothing in the run window)
- The program makes 13 sends and 3 paid model calls. The studio lead shuts down and starts n8n during the sends; you do nothing.
- Nothing new printed for row 16 minutes: FREEZE. No Ctrl-C, no closing the window.
- Contacts appear in HubSpot, mails under label `demo`. The model program keeps running during the film pause.

## F. Film pause and finish
1. The program prints a line asking you to film the contact list and type `end`. Person on row 4 films HubSpot Contacts, search `take-<run name>` (else newest first). Expect 2 or 3 contacts (C may be "unknown"). Other number: FREEZE, do not type `end`. The film pause is at most row 17 minutes.
2. Person on row 7 says "filmed" (a trial run: you look). Then type exactly `end` Enter. Another word makes it print "type exactly: end" once; a second wrong line, Ctrl-C or closing the window ends the pause early with exit code 3 and deletes nothing (lead verifies at re-pin).
3. Recording OFF. With `$` back: `echo $?` Enter [UNVERIFIED]. **0 = ok. Any other number: FREEZE**, send the number and the last printed line; delete nothing.
4. Usage page: write balance and money used, add the increase to the running total. Over the run total: EMERGENCY CANCEL. Send: exit code, last printed line, balance and money used before and after. Read the printed result: A and B each 1 contact and 1 mail; C may be "unknown" only if the studio lead's written exit-code rule allows it (go item 7). Wait for "model program shut down".
5. Contacts by hand: the studio lead sends the list (person id and masked contact id). In HubSpot (account name checked) search the run name, tick each listed contact one by one (never select-all), More, Delete. If the number ticked differs from the list: STOP and send. Send "contacts deleted" and the number.

## Stop rules (any time)
- A key-like long text on screen: treat that key as exposed: cancel it, close the window, send only "a key-like text was on the screen".
- Money: running total of increases above the run total, or any increase before E: EMERGENCY CANCEL (cancel every key you cannot account for), then send figures.
- A figure changes in any message (price, tokens, backstop, ledger total, window end): no run until a new typed yes.
- A screen you do not recognise, a laptop sleep, a number you did not approve: FREEZE.
- Exit code other than 0: FREEZE; no second start; deletions only from the studio lead's list.

## After
- [ ] I.0 cancel the model key (deadline row 11; or 60 minutes after F.4). [ ] Watch the video (H). [ ] Clean-up (I). [ ] Post (J) only with the studio lead's written confirmations.
