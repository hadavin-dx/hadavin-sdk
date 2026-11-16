# Take-day runbook v4.3: PATCH FILE, part 1 (builder A)
Status: DRAFT, unverified

Written 2026-11-16 from static files only. Nothing was run. v4.2 is never edited by this file. Part 1 covers the edits forced by the 12 lead decisions of 2026-11-16 (inputs/DECISIONS-2026-11-16.md, cited below as DEC n with its file line). Part 2 (round 28 to 36 marks, timing sentences for the 49-minute window) is not in this file.

## MISSING SOURCES (not in this checkout; laptop only; the lead must push them or a laptop session must fill the rows)
1. The take-day runbook v4.2 itself. Because it is missing, EVERY row below says "v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills)". I do not know its line numbers, row names or exact wording. A file "WP6-RUNBOOK.md" is cited elsewhere (flowset/REPORT.md line 10) as also missing; whether it is the same document as v4.2 is NOT KNOWN.
2. Lane D sources: egm/duplicate-proof-lead-desk/wp6/fix-p13/review-fix-13o, 13p, 13q, 13r, 13s (LANE-D-REPORT-SUMMARY.md). Not used in part 1. Rounds 28, 32, 33, 34 and 36 wording is NOT in this file.
3. scripts/run_real_check_n8n.py. Nobody has read it here, so what `end` does today is UNVERIFIED (decisions/M17-end-never-deletes.md lines 3 and 8).
4. The run sheet (scenes 1 to 4 and 5 to 11) and the flow folders real-v5 and film-v5. I did not find them. The scene numbers below come only from DEC 1.
5. handover/promotion-inputs/ is not in this checkout (ls shows no such folder), so decision 11 cannot be checked against files.
6. The take port number: DEC 6 says the real take "uses its own free port" and does not give the number. I did not invent one. Placeholder below: TAKE_PORT.

## How to read a row
Columns: ID | v4.2 line or row | old text | new text | source (file and line). "Old text" is what v4.2 says; because v4.2 is missing I give "OLD UNKNOWN" and, where useful, the closest known sentence from the owner steps v5 (inputs/OWNER-STEPS-realrun-v5-core-hardening.md, cited as V5 with its line). A V5 sentence is NOT v4.2 text; the laptop lead must compare. Every "new text" is quoted or closely paraphrased from the named source; where I have added a connecting word it is marked [mine].

## A. Scope: real-v5 only, scenes 1 to 4, one claim (DEC 1)
| ID | v4.2 line or row | old text | new text | source |
|---|---|---|---|---|
| A1 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (title or scope paragraph) | OLD UNKNOWN | "The ONE video is REAL-V5 ONLY: scenes 1-4 of the run sheet. Claim: a lead sent twice with the same id is processed once. The stand-in scenes 5-11 (film-v5) are NOT in this video; they are a possible later video." | DEC 1 (inputs/DECISIONS-2026-11-16.md line 2) |
| A2 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (every row, step or timing line for scenes 5-11) | OLD UNKNOWN: any row that names scenes 5 to 11 or film-v5 | Delete the row or mark it "NOT IN THIS VIDEO (film-v5, later video)". Do not delete the film-v5 flow files. | DEC 1 line 2 ("scenes 5-11 (film-v5) are NOT in this video"). The "do not delete files" half is [mine]. |
| A3 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (flow-set switch step, if any) | OLD UNKNOWN | Remove the flow-set switch step. Only the real-v5 flows are imported. | DEC 1 line 2 ("no flow-set switch"); ORDERS.md line 97 |
| A4 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (mail-credential check for film-v5, if any) | OLD UNKNOWN | Remove the film-v5 mail-credential check (the risk no longer exists in this video). | DEC 1 line 2 ("no film-v5 mail-credential risk") |
| A5 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (scene 5 row and its caption) | OLD UNKNOWN | Cut scene 5. Cut the caption number "60.1 to 61.9 s" (it was never measured). | DEC 1 line 2 ("scene 5 and the unmeasured caption number '60.1 to 61.9 s' are cut") |
| A6 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (post or claim sentence) | OLD UNKNOWN. Closest known: V5 line 164 | One claim only: "the same lead id sent twice is processed once". Keep the V5 must-not-say list (portal, approval step, audit trail, crash-safe unless the rehearsal's crash test passed). | DEC 1 line 2; V5 lines 164 to 172 |
| A7 | OPEN, not an edit | V5 line 12 describes 13 sends (A twice, B ten times at once, C once while n8n is stopped and started) | I cannot tell whether B and C belong to scenes 1 to 4 (the run sheet is missing). Laptop lead: keep or cut the B and C sends to match scenes 1 to 4; if cut, also change V5 lines 12 and 114 ("n8n stopped once"). Not decided here. | V5 lines 12, 114; DEC 1 |

## B. The take never deletes (DEC 2; M17 page)
Caution carried with every row of this block: UNVERIFIED that the program deletes nothing; nobody has read scripts/run_real_check_n8n.py (work/end-delete-cases.md line 5 and line 31; decisions/M17-end-never-deletes.md line 3). Per work/end-delete-cases.md line 5 the replacement text is HELD and "not applied to any card" until the studio lead quotes the program's `end` lines on the M17 page and writes VERIFIED. So rows B1 to B9 are DRAFT wording for v4.3; do not release them before that quote exists. If the program still deletes, work/end-delete-cases.md line 12 says: it is a program defect reported to core-hardening, not a runbook variant.
| ID | v4.2 line or row | old text | new text | source |
|---|---|---|---|---|
| B1 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (any sentence saying `end` deletes or archives contacts) | OLD UNKNOWN. Closest known: V5 line 127 "The program then deletes this run's contacts." and V5 line 31 ('The program's own screens say "archive" for the contact deletion; it means delete')  | "`end` only closes the pause and deletes nothing. The owner deletes leftover made-up contacts by hand." | work/end-delete-cases.md line 12 (Rule); DEC 2 line 3 |
| B2 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (warning before the film pause) | OLD UNKNOWN. Closest known: V5 line 124 "closing the terminal, pressing Ctrl-C, or typing two wrong words in a row ENDS the pause and DELETES the test contacts from HubSpot BEFORE they are filmed." | Heading: "`end` ONLY CLOSES THE PAUSE (it deletes nothing)". The deletion half of the V5 warning goes away only after VERIFIED; the "type exactly `end`, only when filming is done" half stays. | work/end-delete-cases.md line 19 (heading text); V5 line 124 |
| B3 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (run-day step 9 in the owner card numbering) | OLD UNKNOWN | "Up to 3 made-up contacts are left for you to delete by hand." | work/end-delete-cases.md line 19 |
| B4 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (new run-day step 15) | none | "STOP. `end` has closed the pause. The made-up contacts are still in HubSpot. Do nothing. Wait for the studio lead's chat message with the list. If no list arrives within 15 minutes of your `end` (write down the time you typed `end`), message the studio lead and delete nothing." | work/end-delete-cases.md line 20 |
| B5 | UNKNOWN (new run-day step 16) | none | "The studio lead's list gives, for each leftover contact, the lead id (the number the program gives each made-up test person; the program may print it as 'lead key') and the HubSpot contact id, at most 3, ids only, no names or addresses. The message shows its send time in UTC and IST." | work/end-delete-cases.md line 21 |
| B6 | UNKNOWN (new run-day steps 17 and 18) | none | Step 17: "STOP. Wait for the exact words 'contacts may be deleted'. ... Do not accept a similar phrase such as 'demo mails may be deleted'; that one is for Gmail mails only." Step 18: open one listed contact by its contact id in the demo HubSpot account; read its lead id; if it differs from the list, STOP and tell the studio lead. | work/end-delete-cases.md lines 22 and 23 |
| B7 | UNKNOWN (new run-day steps 19 and 20) | none | Step 19: "STOP. Deleting cannot be undone. Click Delete on that one contact only. Then go back to step 18 for the next listed contact." Step 20: "Reply in chat: 'contacts deleted: N of M' ... If a listed contact is missing, delete nothing more and tell the studio lead." | work/end-delete-cases.md lines 24 and 25 |
| B8 | UNKNOWN (old run-day steps 13 to 16) | OLD UNKNOWN: still say `end` deletes (per the M17 notes) | New steps 15 to 20 REPLACE old steps 13 to 16 of OWNER-RUN-DAY-CARD.md (that is the owner card's numbering, not necessarily v4.2's). Laptop lead maps to v4.2. | work/end-delete-cases.md line 4 (Status) |
| B9 | UNKNOWN (release-word row and clean-up row) | OLD UNKNOWN. Known old word: 'demo mails may be deleted' | New word "contacts may be deleted" for HubSpot contacts; the old word stays for Gmail demo mails. Clean-up step 3a: "STOP. Do this only if the studio lead wrote 'contacts may be deleted'. Delete only the contacts the studio lead listed. Reply 'contacts deleted: N'." The new word is NOT confirmed: due Tue 17 Nov 12:00 UTC / 17:30 IST (proposal, nobody agreed). | work/end-delete-cases.md lines 26 and 29 |
| B10 | UNKNOWN (failed-take step, V5 step G equivalent) and V5 line 114 ("up to 3 contacts deleted at the end") | OLD UNKNOWN. Closest known: V5 line 114 and V5 lines 135 to 138 | Change the notice sentence to match: the take deletes nothing; leftover contacts are listed. Whether the program's own printed notice still says "deletes" is a program text issue (work/end-delete-cases.md line 15: "the program's own notice"): core-hardening, not this runbook. | work/end-delete-cases.md line 15; V5 lines 114, 135-138 |
| B11 | UNKNOWN (the HubSpot key can/cannot delete question) | Closest known: V5 line 130 "If the HubSpot key the program uses cannot delete contacts, the deletion can fail after the sends." | Remove: the HubSpot delete-scope question is moot. | DEC 2 line 3 ("the HubSpot delete scope question is moot") |

## C. Ports (DEC 6)
| ID | v4.2 line or row | old text | new text | source |
|---|---|---|---|---|
| C1 | v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills) (n8n port line or rows) | OLD UNKNOWN | "Rehearsal: n8n on port 5690. The real take uses its own free port (TAKE_PORT: NUMBER NOT GIVEN in any source; the lead names it, once, in the plan). Ports 5678 and 5679 are the owner's own n8n and are never used by the take." | DEC 6 (line 7); plan-wp6-resmoke-v5.md lines 271 and 421 show the loopback re-smoke on 5690/5691 and the owner's 5678/5679 check |
| C2 | UNKNOWN (any row that names one port for both rehearsal and take) | OLD UNKNOWN | Split into two rows: rehearsal 5690; take TAKE_PORT. The plan names the take port in ONE place only; every other mention points to it. | DEC 6 |
| C3 | OPEN, not an edit | n/a | 5691 is the n8n runner broker port in the re-smoke plan; whether the take also needs a second port next to TAKE_PORT is NOT KNOWN. | plan-wp6-resmoke-v5.md line 271 |

## D. No real-account smoke (DEC 8)
| ID | v4.2 LINE | old text | new text | source |
|---|---|---|---|---|
| D1 | UNKNOWN (file not in checkout; laptop lead fills) (any step or gate "checks a to f on real accounts") | OLD UNKNOWN. Closest known: OS:87 as quoted in drift/REPORT.md line 41 "(a) to (f) of the smoke (WP6-RUNBOOK) with NO paid call" | "The real-account smoke (checks a to f) is replaced by the loopback re-smoke plus ONE made-up lead in take prep. No extra real smoke." | DEC 8 (line 9) |
| D2 | UNKNOWN (gate before the take) | OLD UNKNOWN | The take gate now reads: loopback re-smoke passed AND one made-up lead sent in take prep. Not proven by anything yet (the re-smoke has not been run: plan-wp6-resmoke-v5.md line 4 "NOTHING was run"). | DEC 8; plan-wp6-resmoke-v5.md line 4 |

## E. Counts proof screen (DEC 9)
| ID | v4.2 LINE | old text | new text | source |
|---|---|---|---|---|
| E1 | UNKNOWN (file not in checkout; laptop lead fills) (proof screen row) | OLD UNKNOWN. Closest known: V5 line 122 "The proof screen is your choice. The studio lead offers candidate screens (n8n's list of runs, the rows of the people table, HubSpot, Gmail)." and V5 line 100 | "The counts proof is a rehearsal screenshot or the Postgres node preview, not a live table screen." The owner no longer picks a live table screen. Keep: the video shows no portal, approval step or audit trail. | DEC 9 (line 10); V5 line 122 for the no-portal sentence |
| E2 | UNKNOWN (step E in V5: "you pick one and say which") | Closest known: V5 line 100 and line 122 | Remove "you choose it" for the live table screen; the studio lead names the screenshot file. File name NOT GIVEN in any source. | DEC 9 |

## F. One Postgres server, two databases (DEC 10)
| ID | v4.2 LINE | old text | new text | source |
|---|---|---|---|---|
| F1 | UNKNOWN (file not in checkout; laptop lead fills) (every sentence that says "one database", "one store" or "one Postgres") | OLD UNKNOWN. Closest known: V5 line 213 "the aim is one database for the run (its Postgres, shared by n8n and our table of test people)" and DECISION-one-store.md line 14 "ONE database for everything we own: the single Postgres instance of the take (one container, one engine). n8n's internal data in its own schema or database" | "one Postgres server with two databases (n8n's own and the take's)" | DEC 10 (line 11) |
| F2 | system-map/DECISION-one-store.md line 14 (and its copy inputs/DECISION-one-store.md line 14; the two copies differ, I did not diff them in detail) | see F1 | Replace line 14's heading "ONE database for everything we own" with the DEC 10 wording. NOT in the runbook; listed so the laptop lead does not miss it. Consistent with DECISION-one-store.md line 26 (a), where n8n lives in a separate database `n8n`. | DEC 10 line 11 |
| F3 | UNKNOWN (records note) | Closest known: V5 line 213 (also lists `stage.journal` as the one file exception) | Keep the `stage.journal` exception sentence; only the "one database" count changes. | V5 line 213; DECISION-one-store.md line 17 |
| F4 | UNKNOWN (owner steps version) | OLD: V3 (inputs/OWNER-STEPS-realrun-v3.md) | DEC 10: OWNER-STEPS v4 and later replace v3; archive v3, never delete. | DEC 10 line 11 |

## G. Licence copies (DEC 11)
| ID | v4.2 LINE | old text | new text | source |
|---|---|---|---|---|
| G1 | UNKNOWN (file not in checkout; laptop lead fills) (any "clean up / archive handover folders" step) | OLD UNKNOWN | "Licence copies under handover/promotion-inputs (Apache-2.0 from other holders) are never overwritten or re-licensed. Verdict KEEP-AS-IS only (never ARCHIVE or MERGE-INTO). They are a BRANCH ARTEFACT. Patch tests run on a clean sdk tree." | DEC 11 (line 12); PLAN-002.md line 50; ORDERS.md line 177 (change only the test so it accepts Apache-2.0 there) |

## H. Who runs what: lead imports flows, lead runs the first rehearsal (DEC 7, DEC 12)
| ID | v4.2 LINE | old text | new text | source |
|---|---|---|---|---|
| H1 | UNKNOWN (file not in checkout; laptop lead fills) (n8n setup step) | OLD UNKNOWN. Closest known: V5 line 40 "C: ... n8n sign-in only if asked." | "n8n first-visit owner setup is already done (FACTS-ALREADY-DONE.md). The lead imports and activates the flows with scripts/n8n_api.py on made-up data. The owner only types y, the challenge and end." | DEC 7 (line 8); inputs/FACTS-ALREADY-DONE.md line 3 |
| H2 | UNKNOWN (rehearsal step or owner of the first rehearsal) | OLD UNKNOWN | "First laptop rehearsal of the changed flows: the lead runs it, right after the loopback re-smoke passes (target tonight or tomorrow morning IST). The times go in the handoff." Owner does nothing in a rehearsal (V5 line 26). | DEC 12 (line 13); V5 line 26 |
| H3 | UNKNOWN (rehearsal gate in the written yes) | V5 line 74 "that the rehearsal passed, with the name of its result file. No rehearsal pass, no run." | Unchanged in rule. It now rests on rows D2 and H2. Not yet proven: V5 line 205 says the rehearsal "has NOT been run". | V5 lines 74, 205 |

## Decisions that do NOT touch the runbook in part 1 (so no rows)
- DEC 3 (roles proposal parked): no runbook edit; if v4.2 mentions four logins or read-only group L, mark "after the video" [mine, UNKNOWN whether it does].
- DEC 4 (C5 patches) and DEC 5 (S9 items): part 2; they need their own rows (S9-5, S9-12, S9-3 as text; S9-2 keeps the owner compare with the honest sentence; S9-1 and S9-4 describe-only; do not claim "nothing can spend before both typed answers").

## Not checked
- No row was compared against v4.2, because v4.2 is not here. Every "old text" is UNKNOWN or a V5 stand-in.
- I did not read scripts/run_real_check_n8n.py (not in checkout), the run sheet, or any lane D file.
- Line numbers for sources were read from the files in this checkout on 2026-11-16; work/end-delete-cases.md and M17 pages are themselves "PROPOSED, on HOLD" and UNVERIFIED.
