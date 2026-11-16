NOTE (system-map, 2026-11-16): only the section 'Current step 3a' at the end of this file is current. Everything above it is SUPERSEDED, do not apply. Do not use any of it. Use one term, 'lead id'.

# Held edits for OWNER-CLEANUP-CARD.md (from an independent naive read, 16 Nov); they wait on QUESTIONS item 8 and the program text fix (M17 line 24)
- New step 3a (after step 3, before step 4, so the contacts are gone before step 5 removes n8n's saved runs): release by the studio lead's message "delete these contacts: ..." with a list (lead key, contact id). Check you are in the demo HubSpot account; delete only a listed contact whose id matches and whose e-mail is exactly take-<run name>-a@example.com, -b@ or -c@; cannot be undone; any mismatch: stop and ask; do not put the HubSpot account number in the reply; reply "contacts deleted" and the number (0 to 3).
- Line 2: "Deletes (steps 2, 3a and 6)"; line 4: add the 3a release word; step 5: "do not say 'retire check passed' until step 3a is finished"; step 2: "if any name on the list is not one you made, stop and ask".
- Step 6: the "~" rule vs `~/.hadavin-take-tags/<run name>.used` contradict: say "never delete any file ending in .used in the folder .hadavin-take-tags"; "use rm" becomes "ask the studio lead for the rm line"; remove "v5 says".
- Verbs: remove (revoke) in steps 1 and 6a; delete in steps 2 and 3a; erase in step 6. Remove "a card addition, not in v5" brackets from owner text.

## Replacement for step 3a (digest 386, from a cold read; UNVERIFIED against the program and not applied to the card; the card is the owner's page and is applied by the lead)
**3a. Demo contacts.** Starts only after step 3 is finished, and only when the studio lead writes "delete these contacts: ..." (lead id, HubSpot contact id and run name for each). **STOP: without that message, do nothing. Deleting a contact cannot be undone.**
1. Open the demo HubSpot account the studio lead named. Never write its account number in chat.
2. Open each listed contact by its HubSpot contact id. Continue only if its e-mail is exactly `take-<run name>-a@example.com` (or `-b@`, `-c@`). On any mismatch, stop, delete nothing and ask.
3. Delete only the matching contacts.
4. Reply only "contacts deleted: N" (N = how many you deleted, out of the number listed).
No deadline releases this step (as with step 2). Times from the studio lead are in UTC and IST. Also needed on the card: step 4 must say it starts after 3a; step 7 must name 3a among the steps that use the `demo-take` Chrome profile; use one verb for step 6 ("delete") everywhere; keep the "card addition, not in v5" marker; the stale lines 3-4 of this file (the ".used" rule and the "stop and ask" line already exist on the card) must be dropped before applying.


## Current step 3a (system-map, 2026-11-16, after cold read 4; replaces every earlier 3a; UNVERIFIED against the program; decision 2: the take never deletes and the assistant deletes nothing, ever)
Reader of the steps marked (Owner) = the owner. Steps without a mark = the assistant (the studio lead's helper), who deletes nothing.
3a. Leftover demo contacts: LIST FIRST, then the owner deletes by hand. Never write the HubSpot account number in chat.
3a-1. After step 3, the studio lead sends the owner AND the assistant a list: lead id, HubSpot contact id and run name for each leftover contact (e-mail domain shown as X). The assistant replies only 'contacts listed: N'.
3a-2. STOP. Nobody deletes anything until the studio lead writes 'contacts may be deleted' (an exact phrase; it is not the same as 'demo mails may be deleted' on the run-day card).
3a-3. (Owner) Open each listed contact by its contact id. If the contact id does not match its run name, or a listed contact is already gone, STOP and tell the studio lead (the program may have deleted it, a defect). Delete nothing yet.
3a-4. (Owner) STOP: deleting cannot be undone. Only when every listed contact passed 3a-3, delete exactly those contacts by hand in HubSpot, then reply 'contacts deleted: N of M'.
Terms: run name = the short name you chose for this run; lead id = the number the program gives each made-up test person; demo-take Chrome profile = the browser profile made for this demo.

ADDED 16 Nov 2026 (cold read r3, wins over the 3a text above): 'Step 3' means step 3 of OWNER-CLEANUP-CARD.md (save the screenshots), and 3a comes right after it. In the list the studio lead sends, 'e-mail domain shown as X' means the part after the @ is replaced by the letter X, so the list holds no real address. Match rule in 3a-3: the contact's e-mail must be exactly take-<run name>-a@example.com (or -b@ or -c@); the lead id is the number the lead uses to find the row and is not used again. 'demo mails may be deleted' is the lead's release phrase for the Gmail demo mails on OWNER-RUN-DAY-CARD.md. In 3a-4, 'N of M' means N contacts deleted out of M listed. Open HubSpot in the demo-take Chrome profile for 3a-3 and 3a-4. 'Decision 2' = inputs/DECISIONS-2026-11-16.md item 2 (the take never deletes). UNVERIFIED means the program has not been run, so what it lists on `end` is not yet seen.
