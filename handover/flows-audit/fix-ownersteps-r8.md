# Change log, OWNER-STEPS-q16-rows.md round 8 (applies reviews/stranger-ownersteps-r8.md; reviewer words checked against the sheet first; text only, nothing run)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os-r8/OWNER-STEPS-q16-rows.md
## Fixed
- B1 Step D: login, Contacts page path, one search box (the Contacts page's), zero-results branch ("not found"), "stop" reply, post-delete expectation, what the lead's message contains. Menu names and login are placeholders (below).
- B2 Step A: says which sends the yes covers (Row 4, rehearsal, take = up to 3 sends, up to 3 paid calls), not the practice run; "standing credits" defined; one number only (a ceiling for all three sends).
- B3: re-pin is now step 2 of a 15-step order; re-check is step 3 (after re-pin, before L1); r20/r21/r22 step 1; T5/T6/T12 placed at re-pin.
- M1 rehearsal wording: sheet follows Q17 item 5 (Row 4 before rehearsal); decision 12 "right after the practice run" flagged for lead to confirm. M2: lead sends nothing live before yes; practice run needs no yes; Step A/D only sent after re-check done. M3: "re-check done" defined. M4: mail-login-by-owner removed (owner does only A and D). M5: Row 4 parts 1-3; Step B/C gone. M6: the chat defined (name is a placeholder). M7: Row 4 flagged at the top of the T list; row and lead meanings defined. M8: scenes 2 and 4 defined; lead cuts scene 4. M9/T5: "about 6 hours" note dropped (no day; Q24-1 replaces it). M10: T2 owner now the lead.
- Nits: TAKE_FOLDER used in words and flagged; ports named in one paragraph; "letter for letter" replaced; "column" mostly replaced by "field"; Q14 aside removed; T1 to T12 (was T11).
## Lead fills in before sending (exact missing items)
1. which chat (app and conversation) is "the chat"; 2. reply deadline for the owner; 3. how the owner logs in to the HubSpot trial account; 4. exact HubSpot menu names to reach Contacts and what the page looks like; 5. what HubSpot shows after a delete; 6. model-provider credit amount (US$) the standing yes refers to; 7. what r20, r21, r22 are in plain words; 8. whether the rehearsal uses the real HubSpot trial (if yes, third Step D message); 9. T3 stopwatch (owner's phone clock vs lead's own); 10. who operates the screen recording (T8); 11. how the mail login gets into n8n without the owner.
## Lead decisions I assumed (confirm)
- The Step A number = ceiling for all up to 3 sends (not cost of one send); the "ceiling" wording is mine.
- Order: Row 4 before rehearsal (Q17-5) over decision 12.
## Not fixed
- id vs vid stays UNVERIFIED (needs a run). Everything remains unverified text.
## Check
python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md -> RESULT: PASS (rc 0). T rows: 12, all 6 pipe fields.
