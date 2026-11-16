# M17: what `end` does at the film pause (16 Nov 2026). CORRECTED again 16:50Z: the take's HubSpot key is read-only, so the program's archive call is refused
Status: CORRECTED by the lead (work/LEAD-ANSWERS.md Batch 3, 16:50Z, which replaces the 16:41Z sentence "the program archives with the take's key"). The lead read the program code; our side has not. Everything about the program's behaviour is UNVERIFIED until the lead's loopback re-smoke (Tue 17 or Wed 18 Nov; result in egm/duplicate-proof-lead-desk/wp6/). The file name keeps the old words "never-deletes" so links still work; neither "never deletes" nor "the key can archive" is true. Older layout kept at decisions/M17-end-never-deletes-history-1.md (the 16:41Z version; it is wrong, ignore it).

## The sentence (use exactly)
"The take's HubSpot key cannot archive or delete. After you type end, the program tries once to archive this take's three made-up contacts; whatever it cannot archive it lists, and you archive or delete those by hand from the printed list."
Expected case (UNVERIFIED): because the key is read-only, the program's archive call is refused for all three contacts, so all three appear on the printed list and the owner archives or deletes all three by hand.
Where it goes: in the owner's step list (v5), at the film pause step (step F, with the new step F2). Exact edits: decisions/v5-edits-for-M17.md.

## Source: UNVERIFIED
UNVERIFIED: no one on this side has read the program. Source: the lead's correction (work/LEAD-ANSWERS.md Batch 3, 16:50Z) on top of Batch 2 (16:41Z). The program is scripts/run_real_check_n8n.py; it is not in our checkout, so this page quotes no line of it. Per the lead: after the owner types end the program still calls archive; with a read-only key HubSpot refuses the call and all three contacts are listed as left behind ("archive them in HubSpot by hand"); the printed clean-up list tells the owner to search take-<tag>-a, -b, -c (example.com).
UNVERIFIED until the re-smoke: (1) whether the refusal prints cleanly (no crash, no confusing message); (2) whether HubSpot's filtered list shows archived contacts. Every line below that states what the program does is "per the lead, unverified".

## Words
- lead correction = Batch 3 of work/LEAD-ANSWERS.md, written by the studio lead on 16 Nov 2026 at 16:50 UTC (22:20 IST); it replaces the 16:41Z Batch 2 sentence.
- read-only key = the HubSpot login key of the take; it can look at contacts but cannot archive or delete them (decision 2 of 16 Nov 2026).
- archived = hidden from the normal HubSpot contact list but kept by HubSpot for a time; not the same as erased.
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
1. `end` closes the pause. The program then tries once to archive this take's three made-up contacts. With the read-only key the attempt is refused (expected, UNVERIFIED).
2. The program prints a clean-up list. Whatever it cannot archive is listed as "left behind: archive them in HubSpot by hand". Expected: all three.
3. The owner archives or deletes by hand only contacts on that list whose address is exactly one of the three take-<tag>-a, -b, -c at example.com. If the count differs from the program's list, change nothing and tell the studio lead. The tag is in the address itself.
4. The take's HubSpot key stays read-only (decision 2). It gets no archive or delete right. The idea "key needs an archive right" (P09 / OD-18) is withdrawn. The program is not expected to finish any clean-up itself.
5. "contacts may be deleted" as a release phrase stays withdrawn; the owner's own by-hand clean-up of listed contacts needs no release phrase. "demo mails may be deleted" stays for Gmail demo mails only.
6. If the program erases a contact for good, that is a program defect: the studio lead reports it to core-hardening.
7. The program does not enforce a 10-minute pause; the pause length is the owner's own clock alarm (lead answer 13).

## Replacement wording for the owner's step list (V5)
"At the film pause, type `end`. The take's HubSpot key cannot archive or delete. The program tries once to archive this take's three made-up contacts; whatever it cannot archive it lists, and you archive or delete those by hand from the printed list. Expect all three on the list."

## Open items
- Loopback re-smoke (Tue 17 or Wed 18 Nov): does the refusal print cleanly; does HubSpot's filtered list show archived contacts: not done, UNVERIFIED.
- Key rights: settled by decision 2 (read-only); no open item.
