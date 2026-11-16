# v5 line edits so the owner steps file matches M17 (the take never deletes). For core-hardening, who own v5. 16 Nov 2026. Made-up data only.
Older layout: decisions/v5-edits-for-M17-history.md (ignore it).

## Terms
| term | meaning |
|---|---|
| M17 | the proposal in decisions/M17-end-never-deletes.md that `end` never deletes anything |
| decision 2 | item 2 of inputs/DECISIONS-2026-11-16.md: the take never deletes |
| take | the one filmed run of the lead-intake demo on made-up data |
| film pause | the moment the program waits so the 3 made-up contacts can be filmed (V5 step F) |
| `end` | the word the owner types to close that pause |
| step F, F2, G | F = the step where the film pause happens; F2 = the new step "delete the leftover test contacts by hand"; G = the closing checks step (what to do after a failed run) |
| studio lead | the Claude session that sends the owner steps |
| v5 | inputs/OWNER-STEPS-realrun-v5-core-hardening.md |
| run-day card | OWNER-RUN-DAY-CARD.md |
| program's on-screen question | the text the program prints when it asks the owner to type something (older text: "prompt text") |
| take key | the HubSpot access key the program uses during the take |
| leftover list | the program's list of made-up contacts still in HubSpot after `end` (by lead id and contact id) |
| failed-run row | the row in v5's reply-words table for what the owner replies after a failed run |

## How to use this page
The table lists the edit to make. Its middle column quotes what v5 says today on that line (v5 as checked on 16 Nov; the quote is cut to 140 characters and any address is masked). Cite rows by the OLD v5 line numbers, because the lines move after the insert. The source is a read of M17 and v5 (agent text, UNVERIFIED; check each quote against the file). The program's own notice text must change FIRST, or v5 will describe output that does not exist (M17, the section on the program's notice). Use "lead id and contact id", not "lead key" (v5 says a key means a secret).

| v5 line (old number) | v5 says today | change |
|---|---|---|
| 31 | - **Delete**: make it gone for good. Used for: HubSpot contacts, HubSpot private apps, secret files, and demo mails (move to Trash, then emp | delete the two sentences about the program saying "archive" and a recoverable copy; add "The program deletes no HubSpot contact; you delete them by hand." |
| 43 | 6. F: the film pause; you type `end` only when filming of the contact list is done. | add: "`end` only closes the pause; the program deletes nothing." |
| 44 | 7. After the run: G (only if it failed), H (watch the edited video), I (clean-up), J (post). | new step F2 "you delete the 3 leftover test contacts by hand in HubSpot from the studio lead's list"; renumber old item 7 as 8 |
| 63 | 7. **Words you type that delete things** are listed in a boxed line right above the step. Read the box first. | "Words you type that end the film pause or delete things ..." |
| 114 | Read the notice: 3 test people, up to 3 model calls and the worst case, up to 3 contacts deleted at the end, up to 3 mails (one per test per | "up to 3 contacts deleted at the end" becomes "up to 3 contacts left in HubSpot for you to delete by hand" |
| 124 | > **WARNING before step F. When the program asks for `end`, closing the terminal, pressing Ctrl-C, or typing two wrong words in a row ENDS t | warning: `end` ends the pause, deletes nothing; closing the terminal, Ctrl-C or two wrong words also end the pause and delete nothing. Do not add "the pause cannot be reopened" to v5 until the program is checked; M17 does not say it either. |
| 127 | The program prints: "Film the contact list now: type `end` and press Enter to archive" (it means delete). The person who films (set before t | prompt text: the studio lead gives the exact words after the program is changed; after `end` the program prints leftover contacts by lead id and contact id. Also replace "The program then deletes this run's contacts." with "The program deletes nothing."; replace "also ends the pause and deletes the contacts" with "also ends the pause; nothing is deleted"; drop "(it means delete)" |
| 128 | You should see HubSpot show no contacts of this run afterwards, and the program print its result. | "HubSpot still shows the 3 contacts of this run, and the program prints the leftover list" |
| 129 | - Stop and tell the studio lead: you closed the terminal or pressed Ctrl-C early. Leftover contacts are deleted by hand in HubSpot; the stud | "are deleted by hand" becomes "are always deleted by hand" |
| 129 (insert after) | (new text; nothing to quote) | NEW heading "Step F2. Delete the leftover test contacts by hand (you)": in HubSpot, Contacts, tick the 3 contacts take-<run name>-a@example.com, -b@ and -c@ (match the id from the program's list AND the address), More, Delete. Done only after the studio lead's list; ends with "contacts deleted" and the number. The warning above G (line 132) names F2 for contacts |
| 130 | - If the HubSpot key the program uses cannot delete contacts, the deletion can fail after the sends. Unless the studio lead tells you otherw | remove (the take key is read-only, decision 2) |
| 132 | > **WARNING before step G. In step G delete ONLY mails in the receiver account and ONLY HubSpot contacts of the failed run (the studio lead  | contacts are deleted only in step F2, not in G |
| 137 | 2. In HubSpot, delete any leftover contacts the studio lead counted: Contacts, tick them, More, Delete. Delete only contacts whose name or a | move the contact delete to F2 (exact address take-<run name>-a@example.com, -b@, -c@); G item 2 points to F2 |
| 138 | 3. Tell the studio lead: "demo mails deleted" and the number of contacts you deleted. | G item 3: "demo mails deleted" and the number of MAILS deleted (contacts move to F2) |
| 182 | / After a failed run / "demo mails deleted" and the number of contacts deleted; a new written yes / | failed-run row becomes "demo mails deleted" and the number of mails deleted; add row: after `end`: "contacts deleted" and the number |

Owner-facing reply words: after `end` "contacts deleted" + number; after a failed run "demo mails deleted" + number (the run-day card now uses "contacts deleted" at both).
