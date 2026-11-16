# DAY CARD v15 (run day: what you type, what the screen shows, when to stop). Print it, and print the sheet's page "The four stop words" next to it.

Version 15, written Mon 16 Nov 2026 (draft until the stamp below is filled). UTC and IST. Words are in `OWNER-STEPS-realrun-v15.md`; this card is part of that sheet. **Two windows:** the **program window** (the WSL window of the program) and the **check window** (a second WSL window; the first line you type in each new check window is the `cd` line below). **In the program window you type only:** `cd`, `clear`, the start line, `y` or `n`, the confirmation line, `end`, `echo $?`. Every other command (`ls`, `sha256sum`, `pgrep`, `date`, `grep`) goes in the check window. The studio lead shuts down and starts n8n itself; you never do and never sign in to it.

**Complete card = no underscore line left, not even one.** A row with an underscore line is open: the card is incomplete: ask, never guess, never fill it yourself. "Row N" = a row of the studio lead's value list (appendix 2); "Bn" = a blank of the sheet's list.

## The blanks (the studio lead fills them in; one value per row)
| Item | Row or blank | Value |
|---|---|---|
| Stamp: the studio lead typed every command and checked every screen of this card in a rehearsal, including the exact start line of E.1 and the command of step 0.4 (no import error printed), on (UTC / IST); transcript file. No stamp: Freeze, do not use this card | B29 | ________ |
| Run name | row 2 | ________ |
| Run date | row 1 | ________ |
| Latest start: date and time UTC | row 3 | ________ |
| Latest start: date and time IST | row 3 | ________ |
| Normal run length (minutes) | row 3 | ________ |
| Lease length (seconds) | row 3 | ________ |
| Start margin (minutes) in the latest-start formula | B19 | ________ |
| Person who films (browser and mouse only) | row 4, B23 | ________ |
| Person who says "recording" | row 5, B23 | ________ |
| Person who edits and crops | row 6, B23 | ________ |
| Person who says "filmed" | row 7, B23 | ________ |
| Deadline to cancel the model key: UTC | row 11 | ________ |
| Deadline to cancel the model key: IST | row 11 | ________ |
| Deadlines: watch the video; clean-up (UTC / IST) | row 11 | ________ |
| Program folder (full path) | row 12 | ________ |
| Program settings file name | row 12 | ________ |
| Model settings file (full path) | row 12 | ________ |
| Model key file (full path) | row 12 | ________ |
| The `cd` line (must equal the program folder) | row 12 | ________ |
| Minutes of silence before Freeze (longer than the longest silence the studio lead expects while it restarts n8n) | row 16 | ________ |
| Longest film pause (minutes) | row 17 | ________ |
| What the program does when the film pause ends without `end` | B11 | ________ |
| Commit id | row 19 | ________ |
| Checksum of `scripts/run_real_check_n8n.py` (8 groups of 8 characters) | row 19 | ________ |
| Every other file the program, the step 0 program and the flows use, each with its checksum | row 19 | ________ |
| Model program command line | row 23 | ________ |
| Model account: usage page address | B4 | ________ |
| Model account: key list page address | B4 | ________ |
| Model account: page that shows prepaid and auto-reload | B4 | ________ |
| Account name shown on those pages | B4 | ________ |
| Per-key spend limit: exists (page, amount) or "none exists" | B6 | ________ |
| Command that prints the ledger total | step A | ________ |
| HubSpot test account name | row 19 | ________ |
| Last 4 digits of its number (never on film) | row 19 | ________ |
| Permission names of the HubSpot key in n8n; of the probe key; of the program's own HubSpot login | B7, B15 | ________ |
| Call ceiling | B10 | ________ |
| Worst-case price per call | step A | ________ |
| Run total | step A | ________ |
| Expected rise before E (US$0 unless a trial ran) | step A | ________ |
| Highest balance you accept | B24 | ________ |
| Alert-mail address (one of your two throwaway accounts) | step A | ________ |
| Exit-code rule for C "unknown": the cell reads `none`, or one number plus the exact printed result it covers; anything else: ask | B2 | ________ |
| Real wording of the notice and of the printed result: sent in the step A message (yes, with its date) | B9 | ________ |
| Time you have at "Type y to start" (minutes) | B16 | ________ |
| E.0 begins at least this long before the latest start (minutes) | B18 | ________ |
| Clock tolerance between `date` and the Windows clock (minutes) | B21 | ________ |
| Usage page lag and gap before the second reading (minutes) | B22 | ________ |
| Retire-check runs allowed | B17 | ________ |
| Length used by the long-string filter of step 0.5 | B28 | ________ |

The stop words are only in the sheet (print its page). On this card "Freeze" and the other three words mean exactly that table; if two apply, the top row wins.

## E.0 Before E (tick each; check window unless it says program window)
- [ ] Type the `cd` line above.
- [ ] Go message for this run name states all nine go items (1 card complete and people named; 2 rehearsal file; 3 step 0 answered or not run; 4 the three n8n connection values and no model credential; 5 hard stop statement; 6 model program restarted, process number and start time; 7 exit-code rule; 8 your yes, accounts, exposure; 9 clean start) and says **REAL run** with the run name you will type. A trial run: recording stays OFF for the whole run.
- [ ] The alert-mail address in the message is one of your two throwaway accounts; the HubSpot last 4 digits match the card (never on film). Otherwise no E.
- [ ] Recording OFF; nobody in the room or on a call can see your screen. It starts at "Recording ON" below.
- [ ] Money rule redone (items 1 to 4: key list; prepaid, auto-reload off and balance; backstop; readings), **E reading** written (balance, money used so far, time). Ledger total printed by you with the card's command equals the message. Any rise since the A reading beyond "expected rise before E": Emergency cancel.
- [ ] `ls -l --time-style=full-iso "<model settings file>"` shows the A.1 time. Changed: Freeze.
- [ ] `sha256sum` of each file in the checksum list equals the card, every group of 8. Different: Freeze.
- [ ] `pgrep -af "<model program command line>"` prints exactly one line with the process number and start time from the go message. `date` is within the clock tolerance of the Windows clock.
- [ ] **Time:** E.0 begins at least the card's minutes before the latest start; E.1 is at or before it (date and time on the card).
- [ ] The studio lead says in writing that n8n is up and that it will shut down and start n8n itself during the run. You do nothing for n8n.
- [ ] The people above are ready. In the program window: the `cd` line, then `clear`. [ ] Recording ON (REAL run only; the person who says "recording").

## E. Start (program window)
1. Type: `python3 -I scripts/run_real_check_n8n.py --take <program settings file name>` Enter (the file name only, no folder). Screen, in order: `mailbox login: still works`, `HubSpot login: still works` (here "still works" is GOOD; in I.4 "STILL WORKS" is BAD), then the notice, then "Type y to start". Anything else: Freeze; do not start again (repeated failed logins can trigger a Google alert).
2. **Compare the notice within the time on the card; when it is used up, type `n` and Enter.** The sample is appendix 5 (invented; the real wording is B9: compare numbers and names, not layout). Type `n` and Enter if ANY is true: price per call is not the same value as on the card; total is not the run total or is more than your yes; you cannot find a line; money stop ("window end") is not 2026-11-23 18:29 UTC = 23:59 IST; calls are more than the call ceiling on the card, or people or mails are not 3; run name is not yours; any line says contacts will be deleted or archived (the notice may keep old wording: type `n` and send the line in words); the notice shows masked accounts and they are not your two throwaway accounts; **the notice shows no masked accounts and the go message did not say, in the same message, that the program does not print them and that you accept it.** Masked accounts and the path on this screen are cropped from the video (appendix 14 item 10). **After `n`:** send "refused at the notice"; the model program keeps running and the model key stays valid until I.0; the studio lead says in writing whether the run name can be used again.
3. Type `y` Enter with your own hands. Never a tool, script or helper window.
4. Read the challenge off the screen and type it, a space, the run name, Enter. If the program refuses (it prints a reason): do not start again; send the reason in words (not the challenge); the studio lead says in writing whether the run name can be used again and sends a new go message. Otherwise send "run started".

## While it runs (you type nothing in the program window)
- 13 submissions and the paid model calls. The studio lead shuts down and starts n8n during the submissions; you do nothing; silence while it restarts is expected.
- No new line printed for the minutes on the card (not counting the film pause): Freeze. No Ctrl-C, no closing the window.
- Contacts appear in HubSpot, mails under label `demo`. The model program keeps running during the film pause.

## F. Film pause and finish
1. The program prints a line asking you to film the contact list and type `end`. The person on row 4 (browser and mouse only; never the program window) films (a) HubSpot Contacts, search `take-<run name>` (else newest first): expect 2 or 3 contacts (C may be "unknown"); (b) the receiver's mail list under label `demo`: expect 2 or 3 mails. Other number: Freeze, do not type `end`, send the counts; type `end` only after the studio lead's written word and before the longest film pause on the card is over; if it runs out first, the card says what the program does (B11). The silence rule does not apply during the pause.
2. The person who says "filmed" says it (a trial run: you look at the contact list yourself). Then **look at the screen for the line that asks for `end`, look at the keyboard, and type exactly `end` with no space and a small e, Enter.** A wrong word: the program asks again (UNVERIFIED); a second wrong line, Ctrl-C or closing the window may end the pause early (UNVERIFIED; B11). Nothing in this card makes the program delete anything.
3. Recording OFF. With `$` back: `echo $?` Enter. **0 = ok. Any other number: Freeze, unless the studio lead's written exit-code rule (card) names exactly that number for exactly this printed result.** Send the exit code number and, in words, what the last printed line says; copy no address or path. Delete nothing.
4. Usage page (browser; Freeze does not stop this): write balance and money used so far; add the increase to the running total. The page lags and shows spending after the fact: no rise does not prove nothing was spent. Over the run total: Emergency cancel. Send: exit code, the last line in words, balance and money used before and after. Read the printed result: A and B each 1 contact and 1 mail; the line that shows A was sent twice with the same person id; C "unknown" only if the exit-code rule allows it. A or B different: do not post, send the printed result in words. **Then cancel the model key (I.0), now; do not wait for the studio lead.**
5. Contacts by hand, only after the studio lead writes "n8n is off" (B27) and sends the list (test address per contact; it holds no step 0 contact, which was deleted in 0.6). In HubSpot (account name and last 4 digits equal the card; "More, Delete" is UNVERIFIED): search each address on the list, tick only contacts whose address is on the list, one by one (never select-all), count the ticks: if the count differs from the list, or a ticked address is not on it: Stop and send. Then More, Delete. Send "contacts deleted" and the number.

## Stop rules (any time; the sheet's table says which word)
- Money: running total of increases above the run total, or a rise before E beyond the expected figure: Emergency cancel (a money figure is never a Freeze).
- A figure changes in any message: Stop (no run) until a new typed yes.
- A screen you do not recognise or a laptop sleep: Freeze.
- Exit code not accepted (F.3): Freeze; no second start; deletions only from the studio lead's list.

## After
- [ ] I.0 cancel the model key by the deadline on the card. [ ] Watch the video (H). [ ] Clean-up (I). [ ] Post (J) only with the studio lead's written confirmations.
