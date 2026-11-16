# v7 notes for the studio lead (editor notes moved out of the owner sheet; never send this file to the owner as a step list)

## 1. Questions only the studio lead can answer (exact question, then where it shows in the owner sheet)
- **Who stops and restarts n8n while person C is sent (was L8).** v7 owner text says: "the person named on run card row 5". Exact question: "Name the person who types the n8n stop and the n8n restart during the run, and the exact two command lines (and in which window). If it is the owner, the owner types them and rule 2 still applies; if it is you, your own session does it and the card says so." No input says who; I did not invent an answer. Sheet places: run card row 5, table row "Run: n8n stop and restart".
- **Who films, starts the recording, edits, and says "filmed" (was L7).** Exact question: "Name the person (or role) for each of the four jobs; if the owner films his own screen, say so." Sheet places: run card row 4, steps D and F, table row "Run: filming".
- **C9 (S9-1..S9-5 from system-map APPLIED-S9.md) is NOT available yet.** Placeholder only: when it exists, check whether it changes step E (notice wording), the "Send counts" wording, the "not proven yet" box and the step J must-not-say list. Nothing from C9 is in v7.
- L1 to L28 from `v6-OPEN-FOR-LEAD.md` still stand unless listed below. New or changed:
  - L3 (editor note was in the Words box "Test person"): the mail path from `example.com` test addresses to the receiver label `demo` is still unexplained in the inputs. Design N4 says the question may be wrong because the intake address is the receiver; please check. v7 owner text no longer says anything about it.
  - L8 and L7: see above.
  - L19: script copy for step 0. v7 asks run card row 14 for the folder, a checksum, the full path of the key file and the key permissions. The safety facts in step 0 ("7 calls", create, change two fields, read back, delete) came from a copy under `/tmp/c8b/.../hubspot_probe.py` in an evidence folder, not a current copy; v7 words them as "should" and makes the owner compare a checksum. You must supply the checksum of the CURRENT script.
  - L29 (new): `python3` versus `python`. The plan uses `python3`; v6 used `python`. v7 uses `python3 -I` everywhere and tells the owner to stop if `python3` is not found. Confirm.
  - L30 (new, design M1): I added a rule that the owner does not give the written yes until the studio lead's step 0 answer is "delete works" or the lead says in writing what happens next. This is my reading, not an order: confirm or change it.
  - L31 (new, design M4): run card row 15 (HubSpot key revoked or kept on purpose). FACTS says the HubSpot keys were used in earlier local runs. You must decide whether the key the program uses is revoked or kept. If kept, v7 step I.4 accepts "STILL WORKS" for HubSpot as success provided the mailbox is "refused as expected". Confirm that this counts as the retire check succeeded; the code's own exit code will be 3 in that case.
  - L32 (new, design M3): the shred list rule in I.6 (refuse names outside the secret folder, ending `.used`, under `~/.hadavin-take-tags`, the run settings file, the model key file). Confirm the model key file is not to be shredded by the owner until you say so.
  - L33 (new, naive 6): the aim "video posted by Wed 18 Nov" versus a run date and stop time of 23 Nov. v7 says the card's run date wins and the aim is missed if the date is later. Give the real run date.
  - L34 (new, naive 8): US$189 is explained from FACTS ("US$180 of 189 in-code backstop, window to Mon 23 Nov 23:59 IST"). Confirm the wording "your model account holds US$189 of credit usable until 23 Nov 23:59 IST".

## 2. Editor notes removed from the owner text (v6 line, what it said, where it went)
- v6 L3: "Nothing was run ... orders 017 and 019" header sentences: kept only "Nothing was run to write this sheet"; the order numbers are removed from owner text.
- v6 L13: "how a mail to such an address reaches the receiver mailbox is not yet explained to me": here, L3 above.
- v6 L66: "'open' (the inputs do not say; the question is in v6-OPEN-FOR-LEAD.md)": replaced by "named on run card row N"; questions above.
- v6 L136: "a copy of the script was read, not the current one": here, L19 above.
- v6 L153: "This is the studio lead's own gate; no plan names it": here. The rehearsal gate is the lead's invention (L20); owner text just says "no rehearsal pass, no run".
- v6 L168, L173, L214, L231: "[Not in the studio lead's done-or-owner-only list: the studio lead confirms before you act]" on C.2, D, G, I.2: replaced by run card row 13 (steps C.1, C.2, D, G, I.2, I.3, I.7 are skipped unless the card lists them) and row 15 for I.2. You must fill row 13 with your memory check result (L28 still open: the memory files named in FACTS were not readable here).
- v6 L169: "the connection list in the studio lead's notes does not match this one; not reconciled, open": here, L10 from v6 (connection list differs: v3 says HubSpot, mail sending, database; FACTS says HubSpot, Claude, Gmail).
- v6 L199: "Who types that is OPEN; planned by the earlier sheet: the studio lead does it": here, L8 above.
- v6 L214, L231: see above. v6 L231 also said "no file maps to an app; that mapping is open": here (L22): no mapping from secret files to HubSpot private apps exists; v7 tells the owner to delete nothing if he cannot tell which app the program used.

## 3. Things I did not do or check
- I read the plan `inputs/plan-wp6-resmoke-v5.md` only by search (grep for the double-mail row DM, probe, example.com), not in full chunks. The facts in the owner sheet come from the v6 sheet, FACTS, the scope sheet, DECISION-one-store (read) and v3. Nothing in v7 depends on a plan line I did not read, but I cannot claim I read all 558 lines.
- The memory files named in FACTS were not readable here. Every v3-only step (C.1, C.2, D, G, I.2 to I.7) is therefore supported only by the inputs; the memory check is OPEN (L28).
- I ran nothing: no command in the sheet was run; click paths were not checked; the `sha256sum`, `echo $?`, `shred` and the Windows clipboard history paths are untested.
- The Gmail tab-title wording in step D.1 ("Inbox (1) - <address>") is from my knowledge of Gmail, not from a screen; v3's line only said "the tab title".
