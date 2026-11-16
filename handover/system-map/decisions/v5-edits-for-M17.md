# v5 line edits so the owner steps file matches M17 (corrected 16:41Z: after `end` the program archives the take's contacts). For core-hardening, who own v5. 16 Nov 2026. Made-up data only.
Sentence (lead correction, work/LEAD-ANSWERS.md Batch 2, 16:41Z; replaces answer 3; UNVERIFIED until the lead's loopback re-smoke, Tue 17 or Wed 18 Nov): "After you type end, the program archives this take's three made-up contacts in HubSpot (archived is not the same as erased: HubSpot keeps them for a time); any it could not archive are listed, and you archive or delete them by hand from the list it prints."
Older layouts: decisions/v5-edits-for-M17-history-4.md (before the correction), decisions/v5-edits-for-M17-history-3.md (and -history.md, -history-2.md); ignore them.

## Terms
| term | meaning |
|---|---|
| M17 | the settled decision in decisions/M17-end-never-deletes.md that after `end` the program archives the take's made-up contacts (file name keeps the old word) |
| decision 2 / lead answer 3 / lead correction | item 2 of inputs/DECISIONS-2026-11-16.md; answer 3 in work/LEAD-ANSWERS.md said "never deletes" and was WRONG; the Batch 2 correction (16:41Z) says the program archives |
| take | the one filmed run of the lead-intake demo on made-up data |
| film pause | the moment the program waits so the 3 made-up contacts can be filmed (V5 step F) |
| `end` | the word the owner types to close that pause |
| step F, F2, G | F = the step where the film pause happens; F2 = the new step "archive or delete by hand the contacts the program listed as left behind"; G = the closing checks step (what to do after a failed run) |
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
| 31 | - **Delete**: make it gone for good. Used for: HubSpot contacts, HubSpot private apps, secret files, and demo mails (move to Trash, then emp | replace the two sentences about the program saying "archive" and a recoverable copy with: "After you type end, the program archives this take's three made-up contacts in HubSpot (archived is not the same as erased: HubSpot keeps them for a time); any it could not archive are listed, and you archive or delete them by hand from the list it prints." (the program does archive; the by-hand step handles only what it lists) |
| 43 | 6. F: the film pause; you type `end` only when filming of the contact list is done. | add: "`end` closes the pause; then the program archives this take's three made-up contacts (archived is not erased)." |
| 44 | 7. After the run: G (only if it failed), H (watch the edited video), I (clean-up), J (post). | new step F2 "you archive or delete the contacts the program listed as left behind (search take-<tag>-a, -b, -c, example.com)"; renumber old item 7 as 8 |
| 63 | 7. **Words you type that delete things** are listed in a boxed line right above the step. Read the box first. | "Words you type that end the film pause or change things ..." (keep wording true: typing `end` makes the program archive contacts) |
| 114 | Read the notice: 3 test people, up to 3 model calls and the worst case, up to 3 contacts deleted at the end, up to 3 mails (one per test per | "up to 3 contacts deleted at the end" becomes "up to 3 contacts archived by the program at the end; any it cannot archive are listed for you to archive or delete by hand" |
| 124 | > **WARNING before step F. When the program asks for `end`, closing the terminal, pressing Ctrl-C, or typing two wrong words in a row ENDS t | warning: `end` ends the pause and the program then archives the 3 made-up contacts; closing the terminal, Ctrl-C or two wrong words also end the pause (what the program does with contacts on those exits: NOT CHECKED, the lead tests it). Do not add "the pause cannot be reopened" to v5 until the program is checked. |
| 127 | The program prints: "Film the contact list now: type `end` and press Enter to archive" (it means delete). The person who films (set before t | program's on-screen question: the lead read the program, our side did not (scripts/run_real_check_n8n.py is not in our checkout), so the exact on-screen words are not quoted here; core-hardening writes them to match the sentence. After `end` the program archives the 3 contacts (archive_all) and prints the left-behind list ("left behind: archive them in HubSpot by hand") and a clean-up list naming take-<tag>-a, -b, -c (example.com). Replace "The program then deletes this run's contacts." with "The program then archives this run's three made-up contacts (archived is not erased)."; replace "also ends the pause and deletes the contacts" with "also ends the pause (contact handling on those exits is not checked)"; drop "(it means delete)" and say "it means archive" |
| 128 | You should see HubSpot show no contacts of this run afterwards, and the program print its result. | "HubSpot still shows the 3 contacts of this run, and the program prints the leftover list" |
| 129 | - Stop and tell the studio lead: you closed the terminal or pressed Ctrl-C early. Leftover contacts are deleted by the owner by a filtered list in HubSpot; the stud | "are deleted by hand" becomes "are archived or deleted by hand by the owner from the program's left-behind list" |
| 129 (insert after) | (new text; nothing to quote) | NEW heading "Step F2. Archive or delete by hand what the program left behind (you)": the program archived the 3 contacts after `end`; if its list shows any left behind, in HubSpot Contacts search take-<tag>-a, -b, -c (example.com), match the id from the program's list AND the address, then archive or delete them (More, Archive or Delete). No release word is needed. End with "contacts cleaned up" and the number (may be 0). The warning above G (line 132) names F2 for contacts |
| 130 | - If the HubSpot key the program uses cannot delete contacts, the deletion can fail after the sends. Unless the studio lead tells you otherw | replace: the take key must be allowed to archive contacts (it is NOT read-only for contacts; whether archive equals the delete right in HubSpot: NOT CHECKED). If archiving fails, the contact is listed as left behind and the owner archives it by hand |
| 132 | > **WARNING before step G. In step G delete ONLY mails in the receiver account and ONLY HubSpot contacts of the failed run (the studio lead  | contacts the program could not archive are handled only in step F2, not in G |
| 137 | 2. In HubSpot, delete any leftover contacts the studio lead counted: Contacts, tick them, More, Delete. Delete only contacts whose name or a | move the contact clean-up to F2 (exact address take-<tag>-a@example.com, -b@, -c@); G item 2 points to F2 |
| 138 | 3. Tell the studio lead: "demo mails deleted" and the number of contacts you deleted. | G item 3: "demo mails deleted" and the number of MAILS deleted (contacts move to F2) |
| 182 | / After a failed run / "demo mails deleted" and the number of contacts deleted; a new written yes / | failed-run row becomes "demo mails deleted" and the number of mails deleted; add row: after `end`: "contacts cleaned up" and the number (may be 0) |

Owner-facing reply words: after `end` "contacts cleaned up" + number; after a failed run "demo mails deleted" + number (the run-day card uses "contacts cleaned up" for contacts).
