# fix-rwct18 (round 12, RW and CT only; fixer). Not committed. Reviewer words (reviews/rw-ct-reader-r11.md, citation-r13-summary.md) were unverified; each point re-read below.

## Not verified (first)
- Nothing was run in n8n, Postgres, HubSpot or a mail program. All order and flow statements are readings of the text in RW, CT, QUESTIONS.md, ORDERS.md, inputs/DECISIONS-2026-11-16.md, PLAN-4 line 46, DECISION-one-store.md line 9, ONS step 18.
- I did not re-read RW 305 to 540 or CT beyond the lines I edited, did not re-check the name-list membership or Q31 item truth beyond the items I cite, and did not read the flow files. The statement in step 3 that the mail step comes after the CRM write rests on the K2 definition in RW (after the CRM write, before the mail step), not on the flow JSON.
- CT rows 80 to 84 (desk repo cites) stay CANNOT-CHECK (third-party repo not in this checkout).

## Reviewer points: held or wrong
- B1 holds. RW had no list of what the prepared screen set and six-column preview are. Added input-table rows (l) and (m) under step 1a and rewrote the step 10 definition. "decision 9" = item 9 of inputs/DECISIONS-2026-11-16.md (line 10), now named. Source of the arrangement: UNANSWERED: lead (no file builds the windows).
- B2 holds. No file says how a pane message shows its lead ID (R:31 / A-012 give only the subject start "[demo] lead"). Added input-table row (n) with the crop risk (A-005, A-084, steps 9 and 16). UNANSWERED: lead.
- B3 holds. Rows (d), (e), (f) were already marked UNANSWERED; the two rehearsal start values (Wed 07:30Z ORDERS.md line 171 / Q30 item 1; 07:40Z Q31 item 13) are now written once, in step 6, flagged for the lead, with the re-pin required before the start (and in step 1a). Verified both values by reading ORDERS.md 171 and QUESTIONS.md item 13.
- B4 holds. Added "Who the lead is in the steps below" after the 1a table and input-table row (o) (speaker, recording operator, mailbox emptier) and (p) (APPROVED name spelling). Steps 12/15 vs "owner has no scene action": reconciled in the 0c intro (no scene action during filming; the edit after filming, step 15, is the owner's work, Q27 item 3).
- M1 holds. RW line 3 "no row adds another claim" was false as written; it now lists A-016b, A-008a, A-007, N-5a, N-5b, N-12, A-016g and the explaining voice rows and says each waits for its own condition and gives no recovery time. Status counts unchanged (no row added or removed).
- M2 holds. One cut limit now defined only in step 6 (f) (3 minutes = 180 s, unless the lead writes another); the wait and the expected attempts value are defined only in step 6 (a) and (b). Step 13, N-5a note, RWQ-3 (section 4), CT 60, 70, 87 now say "cut limit (defined in step 6)". CT 86 and 98 disambiguated (lease threshold N superseded by Q25 item 12; "pause" is not "wait"). Step 6 (d) now says takeover time is a measurement, not the limit. 6 (e) frame time: UNANSWERED: lead sets it at the rehearsal. I left the paste strings of N-9 and N-10 ("real waiting time") unchanged: the words list already names it as its own waiting time, and changing a paste string needs lead approval and an RW/CT pair edit.
- M3 holds. New words bullet (table row, claim, label, lead, take) in RW; 9 step-1a references renamed to "input-table row (x)"; CT line 91 contradiction ("no longer says table row") corrected; CT 108 now "rating labels".
- M4 holds. CT scenes 1 and 2 (CRM list) marked DIFFERENCE with RW (RW wins; whether a CRM window is open is UNANSWERED: lead, input-table row (l)). CT 81: A-002 edits R:4 and A-015 is the R:32 caption, so card line 1 is deleted by A-016e only (A-049 SUPERSEDED by it); corrected.
- M5 holds in part. Step 3 before step 4 is kept on purpose (step 4's messages leave the flows only if CrmIdOk passes, found by P4a) and is now flagged as ORDER FLAG with its cost. Step 4 "no model call" now says it is the lead's answer with no file saying how. Step 10 gate now includes step 6. Step 14 now says the card line A-016h is added in step 15. Q-F no answer-by time: stated UNANSWERED. Step 2a setting source: input-table row (q). "Q-J open" unchanged.
- SOFT rows (CT lane rows B-093 and B-045; Table 2 rows 54 and 51): fixed. Row 54: ONS step 18 only says type `end`; PLAN-4:46 names end.flag (read both). Row 51: AGENT-SCOPE lines 14 to 16 do not name qualify_stage.py (read); cell now cites only DECISION-one-store.md:9.

## UNANSWERED lines (input missing; who; step blocked)
- Prepared screen set arrangement and CRM window yes/no: lead; blocks steps 6, 10 to 15. No Q31 item (item 81 covers only the count/row frame).
- Lead ID display in a pane message: lead; blocks 12a (4), 13a, 15. No Q31 item.
- Voice speaker, recording operator, mailbox emptier, address hider: owner and lead; blocks 5, 7, 9, 10 to 14. No Q31 item (76 (a) and (c) are different questions).
- Rehearsal start 07:30Z or 07:40Z: lead; blocks step 6. No Q31 item asks it.
- Re-pin date and hour before the rehearsal: lead; blocks 1a, 6 (Q-H says lead sets it; no Q31 item asks the date; items 6 and 85 are about the latest end).
- Proof frame time (6 (e)): lead at rehearsal; no item. APPROVED name spelling: lead; no item. Q-F answer-by time: lead; no item. Model-check setting name and place: lead; no item (73 (c), 76 (e) ask who and where written).
- Already with items: P4a send command (d), HubSpot property (e), Gmail filter (f) have NO Q31 item (per RW grep, 2026-11-16); items 77, 87, 58, 33, 39 (c), 73 (c), 3, 81, 45, 13 exist.

## Q31 items needed (for the lead to add; I did not edit QUESTIONS.md or ORDERS.md)
1 prepared screen set and CRM window; 2 how the lead ID shows in a pane message; 3 named humans for voice, recording, mailbox emptying; 4 which rehearsal start time (07:30Z or 07:40Z); 5 re-pin date and hour; 6 proof frame time; 7 APPROVED name spelling; 8 Q-F answer-by time; 9 the model-check setting name; 10 P4a send command, HubSpot property check, Gmail filter (rows d, e, f).

## Checks run (from flows-audit, after the edits)
- check_rw_ct_pairs: 140 of 140 found, 0 missing. check_runsheet_paste: RESULT: PASS (195 rows). claims-count: 15/84/65/102/64 = 330, 0 offenders. check_refs PASS 5176; check_names PASS 655; check_secrets PASS 0 hits; check_counts PASS; ruff format --check . : 748 files already formatted.
- Counts lines unchanged (no verdict, row or status changed).
