# RETRACTION rules (lead 2026-11-16T17:46Z; source: end of work/LEAD-ANSWERS.md, section RETRACTION). Read that section first.

The lead's Batch 2 and Batch 3 "archive" correction was WRONG (lead read an old branch). The final program (r34+ line, head r38 0cead2c) never deletes AND never archives. It has no create, update, delete or archive call on HubSpot. It prints "this script only reads HubSpot and never deletes: it counts and lists them at the end and you delete them by hand" and "left in HubSpot (this take never deletes): N contact(s)".

MASTER SENTENCE (put back, word for word): "The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list."
Still marked UNVERIFIED until the lead's loopback re-smoke on the merged head.

Replace EVERYWHERE in your pages: the Batch 3 sentence ("The take's HubSpot key cannot archive or delete. After end the program tries once; ...") and any wording that says the program archives, tries to archive, "archive or delete by hand", an archive call, a refusal print of an archive call, or "whether HubSpot's filtered list shows archived contacts". Also: the owner "deletes" the left-behind contacts (not "archives or deletes"). The HubSpot key stays read-only (decision 2): that part is still true, keep it only if the page already says it.
Filter text for the clean-up list (lead item 12, from the r38 list): search take-<tag>-a, -b, -c (domain example.com). Where <tag> first shows on screen stays UNVERIFIED.
Pause (item 13): unchanged, no timer in the code the lead read.
Keep: all other batch 3 facts, the UNVERIFIED marks, placeholders, rules.
Do NOT touch: v4.2 (inputs/LEAD-RUNBOOK-TAKE-DAY-v4.2.md and its lines 453 and 507 are CORRECT for the final program; in the v4.3 patch, rows that were drafted to rewrite v4.2 lines 453 and 507 must now say: NO CHANGE, v4.2 is right; mark them and the status table accordingly).
Old wrong text may remain only inside a -history backup or in a short line that quotes and withdraws it (say "withdrawn by the lead 17:46Z").
Work: copy each page to <name>-history-N.md (next free number, never overwrite) before editing. Static text only; never write the owner's personal name (write "owner"); no secrets. Times in UTC and IST. Plain words.
After editing run: grep -n -i -E "archiv" on your pages and list every remaining hit with its line and why it stays.
