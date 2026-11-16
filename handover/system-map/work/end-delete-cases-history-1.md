# What `end` does: replacement text for the owner cards (lead correction 16:41Z applied)
Written 16 Nov 2026; corrected the same day. Older layouts: work/end-delete-cases-history-7.md (and -history.md to -history-6.md); ignore them. The earlier claim "the take never deletes contacts" was WRONG and is withdrawn. Pages that still carry old wording: none of the pages this lane owns (the held pages of work/end-sentence-for-owners.md were edited with the corrected sentence).

## The sentence (use exactly)
"After you type end, the program archives this take's three made-up contacts in HubSpot (archived is not the same as erased: HubSpot keeps them for a time); any it could not archive are listed, and you archive or delete them by hand from the list it prints."

## Status: UNVERIFIED
1. UNVERIFIED: no one on this side has read the program. Source: the lead's correction (work/LEAD-ANSWERS.md Batch 2, 16:41Z, 16 Nov 2026 / 22:11 IST). The program is scripts/run_real_check_n8n.py; it is not in our checkout; the lead read it. It stays UNVERIFIED until the lead's test run (loopback re-smoke, Tue 17 or Wed 18 Nov; result in egm/duplicate-proof-lead-desk/wp6/). Statements below about the program are "per the lead's correction, unverified". The cards must not claim more than the sentence.
2. The owner is the only person. studio lead = the Claude session doing the technical steps.
3. The old proposals (the program erasing contacts with a "contacts may be deleted" release phrase; later "the take never deletes") are withdrawn. The first is kept only in work/end-delete-cases-history-5.md.

## Words
- take = the one filmed demo run on made-up data. `end` = the word the owner types to close the film pause. The pause = the moment the program waits after the 3 made-up contacts exist so the owner can film HubSpot. The program does not enforce the 10-minute pause; the owner sets his own clock alarm.
- run-day card = OWNER-RUN-DAY-CARD.md, the owner's typed steps for the day of the take.
- OWNER-VIEW row 3 = row 3 of the table in OWNER-VIEW.md (the plan page for the owner): the "Run day" row.
- clean-up card = OWNER-CLEANUP-CARD.md, the owner's steps after the take (step I).
- archived = hidden from the normal HubSpot contact list but kept by HubSpot for a time; not erased.
- archive-by-hand list = the list the program prints after `end` of contacts it could not archive ("left behind: archive them in HubSpot by hand"). The printed clean-up list also tells the owner to search Contacts for take-<tag>-a, -b, -c (addresses at example.com) and delete them.
- lead id = the id the program gives each made-up sales request; contact id = the number HubSpot gives a contact.

## Rule (per the lead's correction, unverified)
After `end` the program archives this take's three made-up contacts (archive_all). Any it cannot archive are listed. The owner archives or deletes those by hand from the printed list, matching only the three addresses take-<tag>-a, -b, -c at example.com. If the program does more than archive, that is a program defect: the studio lead reports it to core-hardening (the Claude session that owns the take code); it is not a card variant.

## Replacement text, and the file that holds each
- OWNER-RUN-DAY-CARD.md, heading over the pause steps: "`end` CLOSES THE PAUSE; THEN THE PROGRAM ARCHIVES THE 3 MADE-UP CONTACTS (archived is not erased)".
- OWNER-RUN-DAY-CARD.md, earlier notice step: "The 3 made-up contacts are archived by the program after you type end; any it could not archive are listed for you to archive or delete by hand."
- OWNER-RUN-DAY-CARD.md, after `end`: "The program prints which contacts it archived and which it left behind. Tell the studio lead the count and the contact ids only." (No sample of masked addresses exists in our files, so no "replaced by X" phrase is used.)
- OWNER-RUN-DAY-CARD.md, by-hand step (the owner's own action, no release phrase): "In the demo HubSpot account, open Contacts and search for take-<tag>-a, take-<tag>-b, take-<tag>-c (example.com). Archive or delete only contacts on the program's left-behind list whose email is exactly one of those three. If the count differs from the program's list, change nothing and tell the studio lead. Deleting cannot be undone. Reply 'contacts cleaned up' and the number." The number is the count the owner handled by hand (may be 0).
- Release words: none for contacts. "demo mails may be deleted" stays for the Gmail demo mails only.
- OWNER-VIEW.md, row 3: "The one careful moment is the film pause: typing `end` closes it. After you type end, the program archives this take's three made-up contacts in HubSpot (archived is not the same as erased: HubSpot keeps them for a time); any it could not archive are listed, and you archive or delete them by hand from the list it prints."
- OWNER-CLEANUP-CARD.md: add "Leftover made-up contacts: handle them once from the program's archive-by-hand list (search take-<tag>-a, -b, -c, example.com); never twice."

## Open items
- Lead's loopback re-smoke (Tue 17 or Wed 18 Nov) confirms the archive, the left-behind list and the clean-up list: not done.
- Whether the take's HubSpot key may archive contacts: NOT CHECKED.
