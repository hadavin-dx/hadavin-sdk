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
