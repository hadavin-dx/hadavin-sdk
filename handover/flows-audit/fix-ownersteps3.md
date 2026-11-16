# Change log, OWNER-STEPS-q16-rows.md round 2 of 2 (applies reviews/stranger-owner-steps-r2.md; reviewer words checked against the sheet, ORDERS.md, inputs/DECISIONS-2026-11-16.md and reviews/contradictions-r1.md first; text only, nothing run)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os3/OWNER-STEPS-q16-rows.md

## Failures and uncertainty first
- Nothing was run. Every fact is still read from text. The sheet is still UNVERIFIED and "Re-check done" is still NOT YET.
- I did not open the n8n flow files again, the take scripts, or the claims-table lines; line citations to them are carried over from the earlier rounds.
- ORDERS.md itself contradicts itself on the practice run (line 147: a "loopback re-smoke" on Tuesday and a "practice run" on Wednesday). I could not resolve it; the sheet states both readings and puts it in box R9 for the lead.
- The six values the stranger asked for (credential creator, mail login route, who films, edits and posts, script paths, ledger path) are still LEAD FILLS; I did not invent them.
- A pass line for "the practice run passes" still depends on a definition only the lead has (V11).
- Round 2 of 2 is used; any remaining Blocker needs the lead.

## Each stranger finding checked, and what was done
B1 (import before check; "filled folder" never placed): TRUE. Fixed. Order is now L1 copy table, L2 database plus column check, L3 credentials and values file, L4 fill in two passes (filled-1, import sub-flow, read id, delete filled-1, fill into FILLED_FOLDER), L5 check on FILLED_FOLDER and only then import the other three, L6 first submission. Taken from the fill program README walk-through (steps 1 to 7). The three folders (TAKE_FOLDER, FILLED_FOLDER, filled-1) are defined once in the words box.
B2 (no step creates the n8n credentials): TRUE. Fixed: L3 names the three credentials (n8n-publish-pg, mf-mail-smtp, hubspot-app-token from the README), says the lead creates or confirms them right after L2 (marked as a proposal; V3), and reads their ids. Mail login route stays LEAD FILLS (V3, Q27 item 2).
B3 (Row 4 (c) needs a value set after Row 4): TRUE. Fixed: wait and tries get a first value before Row 4 (V10), the rehearsal measures the real values; Row 4 start condition (iv) added; "attempts" renamed and defined as "tries".
B4 (re-check boxes need later steps; unbounded last box; two meanings): TRUE. Fixed: re-check is exactly eleven boxes R1 to R11, facts readable before anything runs; step checks (database columns, the program's check, $env reads, id versus vid) moved into their steps and called "step checks"; the open-ended last box replaced by an explicit statement that anything else belongs to a step or to a LEAD FILLS value; "re-check" defined once.
B5 (nobody films, edits, posts; owner posts vs "owner only Step D"): PARTLY TRUE. The owner posting comes from the lead's answer Q26 item 1, so it stays, but the owner block now says posting is not a step on this sheet and the lead writes separately; who films, edits and posts and where is LEAD FILLS V5 (Q27 item 3).
B6 (Step D not doable from the sheet): TRUE. Fixed: the lead's "fill in before sending" notes are removed from the owner block; they are now in the value table (V1, V2); the owner text says what each message contains; the delete action and confirm step are written; "zero-results sentence" removed (it was undefined); reply "stop" is now handled in step 1 and 3 of Step D and in Row 4 part 3; a "no reply" contradiction removed (the owner replies only to Step D messages).

## Majors
- Two-meaning words: defined once in the words box: take, take prep, before filming, studio folder, send/submit/mail/message, row words, "Who does it" (column renamed from "Owner"), lead versus lead ID, ledger, ceiling, mailbox words, practice run, rehearsal, local stand-in, live, lease, takeover, takeover line, tries, wait, scene (1 to 4 explained), the plan, the audit, F-002, F-008, F-011, F-041, A-016f, FACTS-ALREADY-DONE.md path, take path, re-check, the chat. The caption in T13 keeps "sent" and "lead ID" on purpose (quoted text).
- T1 mailbox method UNVERIFIED: kept honest, now a pass line (0 mails before the first submission) and LEAD FILLS V4 (emptying method is NOT in Q27: gap).
- T6 "provides" versus step 1 (r21/r22): clarified: r21/r22 change those scripts; at re-pin the lead places the final merged versions.
- "Hard latest re-pin = money stop": TRUE. Fixed in the schedule: 23 Nov 18:29 UTC is the last moment for the take, not for the re-pin; the real latest re-pin time is V13 (Q27 item 6). ORDERS Q24 item 1 uses the same date for the re-pin; the sheet quotes that and says it is not a plan.
- L5 psql: added table_schema = current_schema() and the password rule (from the lead's own settings, never written). Still unrun.
- Pass lines that cannot fail: rehearsal now has a three-part pass line (step 12); ceiling has a written ledger entry with date and time as its pass line; T1 and T7 have pass lines; practice run "passes" is still V11 (needs the lead).
- T3 3 minutes versus rehearsal-measured; line 82 versus T3: merged into one "Scene 4 rule" (kept only if the rehearsal shows takeover inside 3 minutes; cut on the day if it does not show within 3 minutes; the lead may set a different limit before the take).
- T4 postponed versus never filmed: split (P4a fails: postponed; other check fails: that row is not filmed); P4a versus Row 4 (a): stated as the same thing, box R11 asks the lead whether Row 4 (a) satisfies P4a.
- Extra contacts: Step D now says one message per leftover contact, including retakes and a third rehearsal contact; T11 and the cost paragraph say a retake past the stated ceiling needs a new ceiling in the ledger first (proposed; lead confirms).
- Owner reply "stop": handled (Row 4 part 3).
- T12: marked SUPERSEDED, "nothing to do"; removed from "done at re-pin".
- Row 4 (a) to (d): a read-only method added to each.
- Line numbers inside the sheet (for example "line 4"): replaced by "the Re-check done line at the top".

## Contradictions with ORDERS (checked)
- Line 76 "practice run already done" versus ORDERS 147: reworded, and marked as an open reading in R9 (see failures above).
- Row 4 before the rehearsal versus decision 12: kept Q17 item 5, said so, put in R9.
- Q17 item 5 "written yes" superseded by Q25 item 1: now stated in the cost paragraph.
- Stale ORDERS lines (Q22 items 1 and 4: 2 minutes, owner phone stopwatch, 10 s proof, lines 134 and 135): the sheet follows Q25; a lead-only note says so. Not edited (ORDERS.md is not mine).
- Citation fixes: Q25 item 1 is ORDERS.md line 144 (heading 143), was cited as 143; the dropped v3 step 8 now cites Q25 item 7 (line 144), not Q20 item 2.
- Settings source (owner's settings in Q16 versus take program's settings in Q20 item 2): the sheet follows Q20 item 2; the take program's own settings.

## contradictions-r1.md items touching this file
- T12 superseded: done. Step A gone: one mention only, in the words box ("no longer exist"); the title no longer carries it. 10 s reply as proof: not part of the proof (T2, Q22 note). Owner S9 and typing items (item 6): none is an owner step by Q25 item 7; the owner block says only Step D; who does them is V15 (Q27 item 10). Item 12 (port unnamed): ports paragraph says the lead names the port at re-pin in T6 (V9). "No date invented" wording kept next to the dated schedule, with the schedule's own times marked as the lead's estimate.

## Gaps: LEAD FILLS values NOT yet listed in QUESTIONS.md Q27 (I may not edit QUESTIONS.md; the lead should add them to Q27)
- V4 (second part): how the receiving mailbox is emptied or filtered, and how the lead counts mails.
- V8: place of the values file, TAKE_FOLDER and FILLED_FOLDER.
- V9: the take's own port.
- V10: the wait and the tries value (first value before Row 4, measured value at the rehearsal).
- V11: what "the practice run passes" means (the named list of checks).
- V16: DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO values and where they are kept; whether the From address may be on screen.
- V1 and V2 are in QUESTIONS.md line 120 (Q25 item 11), not Q27; they are not duplicates of Q27 items.
- Q27 items 3 (who films, edits, posts), 2 (credentials, mail login, mailbox words), 1 (script paths), 5 (ledger), 6, 7, 9, 10 already cover V3, V5, V6, V7, V12, V13, V15.

## Stale lines in other files the lead should correct (not edited here)
ORDERS.md lines 134 and 135 (Q22 items 1 and 4); ORDERS.md line 117 Q17 item 5 ("written yes"); the practice run versus re-smoke wording in ORDERS.md line 147; FIX-PLAN.md lines 21, 25 and 39 (owner's written yes), 24, 31 (10 s reply as proof) and TAKE-CHECKLIST.md line 32 (as listed in reviews/contradictions-r1.md items 1 to 3).

## Check
Table T1 to T14: 14 rows, all with the same number of pipe fields (6 when split on "|"), counted by a script. Sheet markers: "LEAD FILLS" listed in the value table V1 to V16; V1..V16 are all referenced in the text. No other command was run. The checker python3 -I tools/check_runsheet_paste.py was not run (it checks RUNSHEET-WORDING.md and CLAIMS-TABLE.md, not this file).
