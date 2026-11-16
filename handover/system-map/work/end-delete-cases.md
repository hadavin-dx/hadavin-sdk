# What `end` does: replacement text for the owner cards (lead correction 16:50Z applied)
Written 16 Nov 2026; corrected twice the same day (16:41Z, 16:50Z). Older layout: work/end-delete-cases-history-1.md (the 16:41Z version, now wrong: it said the key can archive; ignore it; earlier ones -history.md to -history-7.md). The claims "the take never deletes contacts" and "the take's key can archive" are both WRONG and withdrawn.

## The sentence (use exactly)
"The take's HubSpot key cannot archive or delete. After you type end, the program tries once to archive this take's three made-up contacts; whatever it cannot archive it lists, and you archive or delete those by hand from the printed list."
Expected case: the key is read-only, so all three contacts are on the printed list. UNVERIFIED.

## Status: UNVERIFIED
1. UNVERIFIED: no one on this side has read the program. Source: the lead's correction (work/LEAD-ANSWERS.md Batch 3, 16:50Z, 16 Nov 2026 / 22:20 IST), on top of Batch 2. The program is scripts/run_real_check_n8n.py; it is not in our checkout. It stays UNVERIFIED until the lead's loopback re-smoke (Tue 17 or Wed 18 Nov; result in egm/duplicate-proof-lead-desk/wp6/): whether the refusal prints cleanly; whether HubSpot's filtered list shows archived contacts. The cards must not claim more than the sentence.
2. The owner is the only person. studio lead = the Claude session doing the technical steps.
3. Withdrawn: the program erasing contacts with a "contacts may be deleted" release phrase (kept only in work/end-delete-cases-history-5.md); "the take never deletes"; "the program archives with the take's key".

## Words
- take = the one filmed demo run on made-up data. `end` = the word the owner types to close the film pause. The program does not enforce the 10-minute pause; the owner sets his own clock alarm.
- read-only key = the take's HubSpot key: it can look, not archive or delete (decision 2 of 16 Nov 2026).
- run-day card = OWNER-RUN-DAY-CARD.md, the owner's typed steps for the day of the take.
- OWNER-VIEW row 3 = the "Run day" row of the table in OWNER-VIEW.md.
- clean-up card = OWNER-CLEANUP-CARD.md, the owner's steps after the take (step I).
- archived = hidden from the normal HubSpot contact list but kept for a time; not erased.
- by-hand list = the list the program prints after `end` of contacts it could not archive ("left behind: archive them in HubSpot by hand"), with the search text take-<tag>-a, -b, -c (example.com).
- lead id = the id the program gives each made-up sales request; contact id = the number HubSpot gives a contact.

## Rule (per the lead, unverified)
After `end` the program tries once to archive the three contacts; the read-only key is expected to make this fail, so all three are listed. The owner archives or deletes those by hand, matching only the three addresses take-<tag>-a, -b, -c at example.com. If the program does more than try to archive, that is a program defect: the studio lead reports it to core-hardening; it is not a card variant.

## Replacement text, and the file that holds each
- OWNER-RUN-DAY-CARD.md, heading over the pause steps: "`end` CLOSES THE PAUSE; THE PROGRAM THEN TRIES ONCE TO ARCHIVE THE 3 MADE-UP CONTACTS (the take's key is read-only, so expect all 3 on a list for you to clear by hand)".
- OWNER-RUN-DAY-CARD.md, earlier notice step: "The take's HubSpot key cannot archive or delete. After you type end, whatever the program cannot archive it lists, and you archive or delete those 3 made-up contacts by hand."
- OWNER-RUN-DAY-CARD.md, after `end`: "The program prints which contacts it could not archive (expected: all three). Tell the studio lead the count and the contact ids only."
- OWNER-RUN-DAY-CARD.md, by-hand step (the owner's own action, no release phrase): "In the demo HubSpot account, open Contacts and search for take-<tag>-a, take-<tag>-b, take-<tag>-c (example.com). Archive or delete only contacts on the program's left-behind list whose email is exactly one of those three. If the count differs from the program's list, change nothing and tell the studio lead. Deleting cannot be undone. Reply 'contacts cleaned up' and the number." The number is the count handled by hand.
- Release words: none for contacts. "demo mails may be deleted" stays for the Gmail demo mails only.
- OWNER-VIEW.md, row 3: "The one careful moment is the film pause: typing `end` closes it. The take's HubSpot key cannot archive or delete. After you type end, the program tries once to archive this take's three made-up contacts; whatever it cannot archive it lists, and you archive or delete those by hand from the printed list."
- OWNER-CLEANUP-CARD.md: add "Leftover made-up contacts: clear them once by hand from the program's printed list (search take-<tag>-a, -b, -c, example.com); never twice."

## Open items
- Lead's loopback re-smoke (Tue 17 or Wed 18 Nov): refusal prints cleanly? does HubSpot's filtered list show archived contacts? Not done, UNVERIFIED.
- Key rights: settled (read-only, decision 2).
