# Adversarial read v13 (lane d): tired owner, day card plus sheet only

Files: CARD = OWNER-DAY-CARD-v13.md, SHEET = OWNER-STEPS-realrun-v13.md, APP = OWNER-STEPS-v13-APPENDIX.md (all in handover/core-hardening/steps-edits/). Read only; nothing was run. Every item below is a failure of the text, not of code.

## A. Costs money or leaks a key

1. CARD:27 and SHEET:66: Emergency cancel cancels "every key not on your written list", and the run key is on that list. If the run key itself is overspending, the cancel leaves it alive. Fix: Emergency cancel also cancels the run key (and says so); the balance is the only ceiling.
2. CARD:26 (Key exposed) never says to switch recording off. A key on screen during the film goes into the video; H (APP:120) checks only addresses. Fix: first words of Key exposed: "Recording OFF, keep that take for the studio lead only, never publish it"; add "no key text" to the H list.
3. CARD:40 turns Recording ON unconditionally, but APP:101 says a trial run is never filmed. A tired owner follows the card on a trial run and films real accounts. Fix: E.0 tick "go message says REAL run (not trial); trial: Recording stays OFF"; also tick that the run name on the message equals the one you will type.
4. CARD:44: "masked accounts shown are not your two throwaway accounts" cannot be done when the program prints none (SHEET:101, APP:138 "not shown"). The owner has no instruction: type `y` or `n`? Fix: "No masked accounts on the notice: type `n`, unless the go message states, in the same message, that it does not print them and you accept it".
5. CARD:44 checks 3 people, calls and mails, but APP:51 admits an alert mail to an address "the studio lead names", not on the notice, not tested. A wrong yes could send a real mail to a real address. Fix: go message names that address; E.0 tick: it is one of your two throwaway accounts, else no E.
6. CARD:43: the start line shows a relative script path and a run settings file path; no `cd` line is on the card (SHEET:84 gives `cd` only for step 0). Wrong folder = possibly another copy of the script; right folder = the full `/home/<name>/...` path is filmed, and APP:120 item 10 crops only the notice path, not the start line. Fix: card prints "type the `cd` line from the go message, then `clear`", and the settings file is passed as a bare file name; or crop the start line too (APP:121 S1).
7. SHEET:84, SHEET:100, CARD:21: the HubSpot test account and both Gmail accounts are identified by NAME only. Two accounts with similar names pass. Fix: the studio lead sends the last 4 characters of each account number; the owner compares them before the film (numbers may be seen only outside the film, APP:120 item 8).

## B. A step that can be done twice, or an ending nobody owns

8. SHEET:79 heading says "once", but 0.4 (SHEET:87) has no guard: a second paste creates a second live contact. Fix: `ls ~/hadavin-step0-result.txt` must say "No such file" before 0.4; and the go message states how many contacts to expect.
9. SHEET:95: "cancel every older model key" also cancels keys other studio projects use. Fix: add "keys of other projects: ask first, write reason and end date" (the keep route already exists, make it the default question).
10. CARD:55: after one wrong line, a second wrong line, Ctrl-C or a closed window ends the pause (exit 3). Typing `end ` (space) or `End` once is easy. Fix: "type end only when the line asking for it is on the screen; look at the keyboard; no trailing space".
11. CARD:54: Freeze at F.1 ("do not type end") leaves the program waiting; its behaviour at the end of the pause is not on the card. Fix: the blanks get one cell: "what the program does when the pause ends with no `end`".
12. CARD:44 "5 minutes at most" has no action at minute 5. Fix: "at minute 5 type `n`" (as SHEET:10 already says).

## C. Stop words that two rules both claim

13. CARD:34 and CARD:61: a money rise before E is "Emergency cancel", but CARD:63 and SHEET:30 also give "a number you did not approve" to Freeze. The precedence line settles it but the owner reads two rows. Fix: delete "a number you did not approve" from Freeze; money figures belong to Emergency cancel only.
14. CARD:56 (exit code not 0 = Freeze, type nothing, close nothing) and CARD:57 (usage page, cancel the key "do not wait") collide: after a non-zero code is the owner frozen or doing F.4? Fix: "Freeze does not stop F.4 or I.0; they use the browser only, never the run window".
15. CARD:62: "A figure changes in any message: no run until a new typed yes" names no stop word, so the owner picks one. Fix: label it "Stop (no run)".
16. CARD:28: Freeze says "send the studio lead what the screen shows", and SHEET:70 (rule 1) forbids sending any mailbox address. A screen with an address cannot be both. Fix: Freeze message = words only, never a screenshot or copied text; name the screen ("notice", "usage page").

## D. Time and money blanks a rushed owner fills with a guess

17. CARD:38, SHEET:48, APP:95: the latest start (window end minus about 14 minutes, 18:14:40 UTC) ignores the film pause (CARD:15, up to row 17 minutes) and the n8n restart. A start at the "latest" time can cross the money stop mid-run. Fix: latest start = window end minus (run length plus longest film pause plus 5 minutes); the studio lead writes that time on the card.
18. CARD:34 and SHEET:64 admit the usage page lags. "Rise beyond expected = Emergency cancel" can fire on a trial's late charge (key cancelled for nothing), and an under-read at F.4 hides an overspend. Fix: the A.3 reading must be at least 30 minutes after the last model call of any earlier run (or the card says "wait"), and F.4 reads again after 15 minutes before the I.0 figure counts.
19. CARD:11 and SHEET:143: rows 4 to 7 and row 15 are people. For a one-person studio the owner is the only human, yet he types `y` in the run window and cannot also film and say "recording". Fix: the card states which rows the owner may hold (the owner may not be the person who films or checks the post alone), or says "recording started by hotkey from the keyboard you are not typing on", per rehearsal.
20. CARD:3 and CARD:57: "exit-code rule" cell can hold "none" or stay empty; both are described, but a pencilled "0" reads like a rule. Fix: the cell must read either `none` or a number with the exact printed result it covers; anything else: ask.

## E. What I could not break

Dates and times agree across the three files (Mon 23 Nov 18:29 UTC = 23:59 IST; Wed 25 Nov 15:00 UTC = 20:30 IST). The y, 6-digit, run-name and `end` answers are consistent between CARD:45-46, SHEET:71 and SHEET:77. Deleting contacts one by one with a count check (CARD:58) holds.

## Not checked

No script or program was run; wording of real screens is unknown. I did not read v13-OPEN-FOR-LEAD.md, handback-v13.md or check-v13.py, so some items above may already be listed there.
