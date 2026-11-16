# M17: what `end` does at the film pause (16 Nov 2026). CORRECTED 16:41Z: the program archives; it does not "never delete"
Status: CORRECTED by the lead (work/LEAD-ANSWERS.md Batch 2, 16:41Z). The lead read the program code; our side has not. The correction is UNVERIFIED until the lead's test run (loopback re-smoke, Tue 17 or Wed 18 Nov; result in egm/duplicate-proof-lead-desk/wp6/). The file name keeps the old word "never-deletes" so links still work; the old claim "the take never deletes contacts" was WRONG. Older layout kept at decisions/M17-end-never-deletes-history-8.md (ignore it).

## The sentence (use exactly)
"After you type end, the program archives this take's three made-up contacts in HubSpot (archived is not the same as erased: HubSpot keeps them for a time); any it could not archive are listed, and you archive or delete them by hand from the list it prints."
Where it goes: in the owner's step list (v5), at the film pause step (step F, with the new step F2). Exact edits: decisions/v5-edits-for-M17.md.

## Source: UNVERIFIED
UNVERIFIED: no one on this side has read the program. Source: the lead's correction (work/LEAD-ANSWERS.md Batch 2, 16:41Z), which replaces answer 3 (16:23Z, now known to be wrong). The program is scripts/run_real_check_n8n.py; it is not in our checkout, so this page cannot quote any line of it. The lead read it: after the owner types end it ARCHIVES this take's made-up contacts in HubSpot (archive_all); any it cannot archive are listed "left behind: archive them in HubSpot by hand"; the printed clean-up list tells the owner to search take-<tag>-a, -b, -c (example.com) and delete them.
Before filming, the lead's loopback re-smoke (Tue 17 or Wed 18 Nov) must confirm this; its result goes to egm/duplicate-proof-lead-desk/wp6/.
Every line below that states what the program does is "per the lead's correction, unverified".

## Words
- lead correction = Batch 2 of work/LEAD-ANSWERS.md, written by the studio lead on 16 Nov 2026 at 16:41 UTC (22:11 IST); it replaces lead answer 3.
- archived = hidden from the normal HubSpot contact list but kept by HubSpot for a time; not the same as erased.
- tag = the run name in the made-up addresses: take-<tag>-a@example.com, take-<tag>-b@example.com, take-<tag>-c@example.com.
- core-hardening = the Claude session that owns the take code (the program) and the owner steps file v5.
- V5 = version 5 of the owner's step sheet (inputs/OWNER-STEPS-realrun-v5-core-hardening.md).
- card variant = a different version of an owner card.
- release phrase = a sentence the studio lead writes before the owner may delete something (for example "demo mails may be deleted").
- decisions/v5-edits-for-M17.md = the page listing, line by line, what to change in V5 so it matches this decision.
- owner = the only person involved: the human at the laptop, who owns the studio.
- take = the filmed demo run on made-up data. Film pause = the moment the program waits so the 3 made-up HubSpot contacts can be filmed. `end` = the word the owner types to close that pause.
- studio lead = the Claude session doing the technical steps.

## Consequences (all per the lead's correction, unverified)
1. `end` closes the pause and then the program archives this take's three made-up contacts in HubSpot (archive_all). It is an archive, not an erase: HubSpot keeps archived contacts for a time.
2. The program prints a clean-up list. Any contact it could not archive is listed as "left behind: archive them in HubSpot by hand".
3. The printed list tells the owner to search HubSpot Contacts for take-<tag>-a, -b, -c (addresses at example.com) and delete them. The owner archives or deletes by hand only contacts on that list whose address is exactly one of the three. Where the tag is shown in HubSpot: it is in the address itself (take-<tag>-a@example.com).
4. Because the program archives, the take's HubSpot key needs the right to archive contacts, so it is NOT read-only for contacts. The earlier line "the take key can stay read-only" is WITHDRAWN. Whether the archive right is the same as the delete right in HubSpot: NOT CHECKED.
5. "contacts may be deleted" as a release phrase for the program stays withdrawn: the program archives on its own after `end`. The owner's own by-hand delete of listed leftovers needs no release phrase. "demo mails may be deleted" stays for Gmail demo mails only.
6. If the program does anything beyond archiving (for example erases a contact for good), that is a program defect: the studio lead reports it to core-hardening.
7. The program does not enforce a 10-minute pause; the pause length is the owner's own clock alarm (lead answer 13).

## Replacement wording for the owner's step list (V5)
"At the film pause, type `end`. The program then archives this take's three made-up contacts in HubSpot (archived is not the same as erased: HubSpot keeps them for a time); any it could not archive are listed, and you archive or delete them by hand from the list it prints."

## Open items
- Loopback re-smoke (Tue 17 or Wed 18 Nov) confirms archive_all, the left-behind list and the clean-up list: not done.
- Whether the take key's HubSpot rights allow archiving: NOT CHECKED.
