# v5 line edits so the owner steps file matches M17 (the take never deletes). For core-hardening, who own v5. 16 Nov 2026. Made-up data only.
Source: a read of M17 and inputs/OWNER-STEPS-realrun-v5-core-hardening.md (agent text, unverified; check each quote). The program's own notice text must change FIRST or v5 will describe output that does not exist (M17 line 24).
Use "lead id and contact id", not "lead key" (v5 line 20 says key means a secret).
| v5 line | change |
|---|---|
| 31 | delete the two sentences about the program saying "archive" and a recoverable copy; add "The program deletes no HubSpot contact; you delete them by hand." |
| 43 | add: "`end` only closes the pause; the program deletes nothing." |
| 44 | new step F2 "you delete the 3 leftover test contacts by hand in HubSpot from the studio lead's list"; renumber old item 7 as 8 |
| 63 | "Words you type that end the film pause or delete things ..." |
| 114 | "up to 3 contacts deleted at the end" becomes "up to 3 contacts left in HubSpot for you to delete by hand" |
| 124 | warning: `end` ends the pause, deletes nothing; closing the terminal, Ctrl-C or two wrong words also end the pause and delete nothing. Add "the pause cannot be reopened" only after the program is checked (not in v5 or M17). |
| 127 | prompt text: the studio lead gives the exact words after the program is changed; after `end` the program prints leftover contacts by lead id and contact id. Also replace "The program then deletes this run's contacts." with "The program deletes nothing."; replace "also ends the pause and deletes the contacts" with "also ends the pause; nothing is deleted"; drop "(it means delete)" |
| 128 | "HubSpot still shows the 3 contacts of this run, and the program prints the leftover list" |
| 129 | "are deleted by hand" becomes "are always deleted by hand" |
| 130 | remove (the take key is read-only, decision 2) |
| 132 | contacts are deleted only in step F2, not in G |
| 138 | G item 3: "demo mails deleted" and the number of MAILS deleted (contacts move to F2) |
| 137 | move the contact delete to F2 (exact address take-<run name>-a@example.com, -b@, -c@); G item 2 points to F2 |
| 182 | failed-run row becomes "demo mails deleted" and the number of mails deleted; add row: after `end`: "contacts deleted" and the number |
| after 129 | NEW heading "Step F2. Delete the leftover test contacts by hand (you)": in HubSpot, Contacts, tick the 3 contacts take-<run name>-a@example.com, -b@ and -c@ (match the id from the program's list AND the address), More, Delete. Done only after the studio lead's list; ends with "contacts deleted" and the number. The warning above G (line 132) names F2 for contacts |
Owner-facing reply words: after `end` "contacts deleted" + number; after a failed run "demo mails deleted" + number (the run-day card now uses "contacts deleted" at both).
