# M17: what `end` does at the film pause (16 Nov 2026). RESTORED 17:46Z: the take never deletes contacts (the file name is right again)
Status: RESTORED by the lead (work/LEAD-ANSWERS.md, section RETRACTION, 16 Nov 2026 17:46Z = 23:16 IST). The lead's "archive" corrections of 16:41Z and 16:50Z were withdrawn by the lead at 17:46Z: they came from reading an old branch. The program that will be taken is the r34+ line (scripts/run_real_check_n8n.py, head r38 0cead2c). Per the lead, it has no create, update, delete or archive call on HubSpot. Everything about the program's behaviour stays UNVERIFIED until the lead's loopback re-smoke on the merged head (Tue 17 or Wed 18 Nov; result in egm/duplicate-proof-lead-desk/wp6/). Older layouts: decisions/M17-end-never-deletes-history-9.md (the 16:50Z version, withdrawn by the lead 17:46Z; ignore it) and the earlier -history files.

## The sentence (use exactly)
"The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list."
Where it goes: in the owner's step list (v5), at the film pause step (step F, with the new step F2). Exact edits: decisions/v5-edits-for-M17.md.

## Source: UNVERIFIED
UNVERIFIED: no one on this side has read the program (it is not in our checkout), so this page quotes no line of it. Per the lead: the program only reads HubSpot. After `end` it prints "this script only reads HubSpot and never deletes: it counts and lists them at the end and you delete them by hand" and "left in HubSpot (this take never deletes): N contact(s)". The clean-up list tells the owner to search take-<tag>-a, -b, -c (example.com). Where the tag first shows on screen: UNVERIFIED.
UNVERIFIED until the re-smoke: whether the program really prints those two lines and makes no write call on HubSpot. Every line below that states what the program does is "per the lead, unverified".

## Words
- lead retraction = the RETRACTION section at the end of work/LEAD-ANSWERS.md, written by the studio lead on 16 Nov 2026 at 17:46 UTC (23:16 IST); it replaces the Batch 2 and Batch 3 "archive" sentences.
- read-only key = the HubSpot login key of the take; it can look at contacts but cannot create, change, archive or delete them (decision 2 of 16 Nov 2026).
- tag = the run name in the made-up addresses: take-<tag>-a@example.com, take-<tag>-b@example.com, take-<tag>-c@example.com.
- core-hardening = the Claude session that owns the take code (the program) and the owner steps file v5.
- V5 = version 5 of the owner's step sheet (inputs/OWNER-STEPS-realrun-v5-core-hardening.md).
- card variant = a different version of an owner card.
- release phrase = a sentence the studio lead writes before the owner may delete something.
- decisions/v5-edits-for-M17.md = the page listing, line by line, what to change in V5.
- owner = the only person involved: the human at the laptop, who owns the studio.
- take = the filmed demo run on made-up data. Film pause = the moment the program waits so the 3 made-up HubSpot contacts can be filmed. `end` = the word the owner types to close that pause.
- studio lead = the Claude session doing the technical steps.

## Consequences (all per the lead, unverified)
1. `end` closes the pause. The program makes no change in HubSpot: it deletes nothing.
2. The program prints a clean-up list of the made-up contacts still in HubSpot ("left in HubSpot (this take never deletes): N contact(s)").
3. The owner deletes by hand, by a filtered list, only contacts whose address is exactly one of the three take-<tag>-a, -b, -c at example.com. If the count differs from the program's list, change nothing and tell the studio lead. The tag is in the address itself.
4. The take's HubSpot key stays read-only (decision 2). It gets no delete right. The idea "key needs an archive right" (P09 / OD-18) stays withdrawn.
5. "contacts may be deleted" as a release phrase stays withdrawn; the owner's own by-hand clean-up of listed contacts needs no release phrase. "demo mails may be deleted" stays for Gmail demo mails only.
6. If the program creates, changes, archives or deletes a contact, that is a program defect: the studio lead reports it to core-hardening.
7. The program does not enforce a 10-minute pause; the pause length is the owner's own clock alarm (lead answer 13; unchanged by the retraction).

## Replacement wording for the owner's step list (V5)
"At the film pause, type `end`. The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list. Expect all three on the list."

## Open items
- Loopback re-smoke on the merged head (Tue 17 or Wed 18 Nov): the program prints the two lines above and makes no write call on HubSpot: not done, UNVERIFIED.
- Key rights: settled by decision 2 (read-only); no open item.
