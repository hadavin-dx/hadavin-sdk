# M17: what `end` does at the film pause (16 Nov 2026)
Status: SETTLED as a decision by lead answer 3, but UNVERIFIED in the program (see "Source"). Older layout: decisions/M17-end-never-deletes-history-7.md (ignore it).

## The sentence (use exactly)
"The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list."
Where it goes: in the owner's step list (v5), at the film pause step (step F, with the new step F2). Exact edits: decisions/v5-edits-for-M17.md.

## Source: UNVERIFIED
UNVERIFIED: no one on this side has read the program. Source: the lead's answer 3 (work/LEAD-ANSWERS.md, 16:23Z). The program is scripts/run_real_check_n8n.py; it is not in our checkout, so this page cannot quote any line of it.
Before filming, run it with a test contact and confirm no delete call.
Every line below that states what the program does is "per the lead's answer 3, unverified".

## Words
- lead answer 3 = answer 3 in work/LEAD-ANSWERS.md, written by the studio lead on 16 Nov 2026 16:23 UTC / 21:53 IST: the take never deletes.
- core-hardening = the Claude session that owns the take code (the program) and the owner steps file v5.
- V5 = version 5 of the owner's step sheet (inputs/OWNER-STEPS-realrun-v5-core-hardening.md).
- card variant = a different version of an owner card (for example one with a delete step); a program that deletes would be a defect, not a variant.
- release phrase = a sentence the studio lead writes before the owner may delete something (for example "demo mails may be deleted").
- decisions/v5-edits-for-M17.md = the page listing, line by line, what to change in V5 so it matches this decision.
- owner = the only person involved: the human at the laptop, who owns the studio.
- take = the filmed demo run on made-up data. Film pause = the moment the program waits so the 3 made-up HubSpot contacts can be filmed. `end` = the word the owner types to close that pause.
- studio lead = the Claude session doing the technical steps.

## Consequences (all per the lead's answer 3, unverified)
1. `end` only closes the pause. The program deletes nothing, archives nothing and has no delete step.
2. After `end` the program prints a list of the made-up contacts still in HubSpot (lead id and contact id).
3. The owner deletes any left behind by hand in HubSpot, using a filtered list. Filter contacts whose email starts with take-<run name>- (the three are take-<run name>-a@example.com, -b@example.com, -c@example.com), and delete only those. Where the run name is shown in HubSpot: NOT KNOWN; the lead must name it.
4. No delete approval and no release phrase gate the program, because (per the lead's answer 3, unverified) it deletes nothing. The phrase "contacts may be deleted" is withdrawn. "demo mails may be deleted" stays for Gmail demo mails only.
5. If the program is ever found to delete a contact, that is a program defect: the studio lead reports it to core-hardening; it is not a card variant.
6. The take key can stay read-only for contacts (no delete right needed), per the lead's answer 3, unverified.

## Replacement wording for the owner's step list (V5)
"At the film pause, type `end`. Nothing is deleted. The program lists the made-up contacts left in HubSpot; you delete them yourself by a filtered list."

## Open items
- Read or test-run the program (see "Source") and confirm no delete call: not done.
- The lead names where the run name is shown in HubSpot: NOT KNOWN.
