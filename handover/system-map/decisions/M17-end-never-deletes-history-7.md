# M17: what `end` does at the film pause (16 Nov 2026)
Status: SETTLED by lead answer 3 (work/LEAD-ANSWERS.md, 16 Nov 2026 16:23 UTC / 21:53 IST). Older layout: decisions/M17-end-never-deletes-history-6.md (ignore it).

## The sentence (use exactly)
"The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list."

## Source and what was not checked
Source: lead answer 3 (work/LEAD-ANSWERS.md), which says the take program's own text and the decision of 2026-11-16 confirm it. The program itself (scripts/run_real_check_n8n.py) is not in our checkout and was not read by this session. So the sentence rests on the lead's answer, not on a quoted line of the program. The "Quoted lines" check that older versions of this page asked for is no longer a condition for using the sentence.

## Words
- owner = the one person: the human at the laptop, who owns the studio. There is no other person ("studio head" is closed: no such person).
- take = the filmed demo run on made-up data. Film pause = the moment the program waits so the 3 made-up HubSpot contacts can be filmed. `end` = the word the owner types to close that pause.
- studio lead = the Claude session doing the technical steps.

## Consequences
1. `end` only closes the pause. The program deletes nothing, archives nothing and has no delete step.
2. After `end` the program prints a list of the made-up contacts still in HubSpot (lead id and contact id).
3. The owner deletes any left behind by hand in HubSpot, using a filtered list (filter the contact list by the run name in the address, take-<run name>-a@example.com, -b@, -c@) and deleting only those.
4. No delete approval and no release phrase gate the program, because the program deletes nothing. The phrase "contacts may be deleted" is withdrawn. "demo mails may be deleted" stays for Gmail demo mails only.
5. If the program is ever found to delete a contact, that is a program defect: the studio lead reports it to core-hardening; it is not a card variant.
6. The take key can stay read-only for contacts (no delete right needed).

## Replacement wording for the owner's step list (V5)
"At the film pause, type `end`. Nothing is deleted. The program lists the made-up contacts left in HubSpot; you delete them yourself by a filtered list." Where each sentence goes: decisions/v5-edits-for-M17.md.
