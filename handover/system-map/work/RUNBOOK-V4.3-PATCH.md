Status: DRAFT, unverified

# Take-day runbook v4.3: ONE PATCH FILE (merge of parts 1, 2 and 3)

Merged 2026-11-16 from the three part files by a merger agent. Static work only: I read the three parts and wrote this file. I did not re-open any original source (decisions, owner steps, timing check, lane D reports). Every quote below is carried over from the parts; I did not check it against its source file.

## In plain words

A patch file is a list of edits to another document. Each row says: which line of the old document, what it says now, what it should say, and where the new wording came from. The patch file never changes the old document. Whoever applies it does that by hand, after checking each row.

The old document here is the take-day runbook v4.2 (the step list for the video take). Version 4.2 is NOT in this checkout, so I cannot say which line any row belongs to, and no "old text" has been compared with it. Where a row says "V5" or "v5", the old text is a sentence from the owner steps v5 file (a different document), used only as the nearest known stand-in; the laptop lead must compare it with v4.2.

Nothing was run. No program, test, rehearsal or model call happened. Nothing in this file is verified.

How to read the state column:
- quoted: the new text comes from a named source (a lead decision or a work file), word for word or closely paraphrased, but it is still unchecked against v4.2.
- PROPOSAL: the wording was proposed by a builder (not a decision); the lead must accept it.
- SOURCE MISSING: the file that holds the wording is not in this checkout; the row is an empty slot.
- HELD: do not apply yet; it waits for something named in the row (for example a check of what the program really does).
- CONFLICT: two rows edit the same sentence or contradict each other. I show both and choose neither.

## MISSING SOURCES

1. Lane D reports (laptop only, under egm/duplicate-proof-lead-desk/wp6/fix-p13/): review-fix-13o (round 28 marks), review-fix-13p (round 32 money additions), review-fix-13q (round 33 marks), review-fix-13r (round 36 exact wording, items 1 to 9), review-fix-13s (round 34 take-program wording, items 1 to 7). Asked paths: 13o, 13r and 13s: `.../LANE-D-REPORT-SUMMARY.md`; 13p and 13q: the whole folder (the order names no file). No `egm/` folder exists in this checkout. Item counts (1 to 9, 1 to 7) were copied from ORDERS.md line 182 and are not confirmed.
2. The take-day runbook v4.2 itself. Every "v4.2 line or row" cell is therefore UNKNOWN. Whether the file "WP6-RUNBOOK.md" (cited elsewhere as missing) is the same document is NOT KNOWN.
3. The run program (`scripts/run_real_check_n8n.py`). Nobody has read it here, so what `end` does today is UNVERIFIED. Also not in the checkout: the settings file `stage.env` (where the program's "about 14 minutes" might live).
4. The run sheet (scenes 1 to 4 and 5 to 11) and the flow folders real-v5 and film-v5. Scene numbers come only from decision 1.
5. handover/promotion-inputs/ is not in this checkout, so decision 11 cannot be checked against files.
6. The take port number. No source gives it. Placeholder used: TAKE_PORT.

Also missing, found while merging: no rows exist anywhere for decision 4 (C5 patches) and decision 5 (S9 items). Part 1 says they belong to "part 2", but part 2 holds only lane D slots and part 3 only timing. See open question 12.

## Edit table

Source key. DEC n = inputs/DECISIONS-2026-11-16.md (lead decision n). V5 = inputs/OWNER-STEPS-realrun-v5-core-hardening.md (v5 owner steps). TCA = work/timing-check-a.md. EDC = work/end-delete-cases.md. In the "source" column of rows M59 to M73 the line shown is the v5 target line; the TCA row is named in the new-text cell's note or in the source cell.

Ids are new (M01 to M73). The old id from the part file is in brackets: A, B, C, D, E, F, G, H = part 1; 28-a etc. = part 2; P = part 3. Rows are kept in part order. "UNKNOWN" in the v4.2 cell stands for "v4.2 LINE: UNKNOWN (file not in checkout; laptop lead fills)" plus the hint the part gave.

| id | v4.2 line or row | old text | new text | source file:line | state |
|---|---|---|---|---|---|
| M01 [A1] | UNKNOWN (title or scope paragraph) | OLD UNKNOWN | "The ONE video is REAL-V5 ONLY: scenes 1-4 of the run sheet. Claim: a lead sent twice with the same id is processed once. The stand-in scenes 5-11 (film-v5) are NOT in this video; they are a possible later video." | DEC 1 (inputs/DECISIONS-2026-11-16.md line 2) | quoted |
| M02 [A2] | UNKNOWN (every row, step or timing line for scenes 5-11) | OLD UNKNOWN: any row that names scenes 5 to 11 or film-v5 | Delete the row or mark it "NOT IN THIS VIDEO (film-v5, later video)". Do not delete the film-v5 flow files. | DEC 1 line 2; "do not delete files" half is the part-1 builder's own words | quoted |
| M03 [A3] | UNKNOWN (flow-set switch step, if any) | OLD UNKNOWN | Remove the flow-set switch step. Only the real-v5 flows are imported. | DEC 1 line 2 ("no flow-set switch"); ORDERS.md line 97 | quoted |
| M04 [A4] | UNKNOWN (mail-credential check for film-v5, if any) | OLD UNKNOWN | Remove the film-v5 mail-credential check (the risk no longer exists in this video). | DEC 1 line 2 | quoted |
| M05 [A5] | UNKNOWN (scene 5 row and its caption) | OLD UNKNOWN | Cut scene 5. Cut the caption number "60.1 to 61.9 s" (it was never measured). | DEC 1 line 2 | quoted |
| M06 [A6] | UNKNOWN (post or claim sentence) | OLD UNKNOWN. Closest known: V5 line 164 | One claim only: "the same lead id sent twice is processed once". Keep the V5 must-not-say list (portal, approval step, audit trail, crash-safe unless the rehearsal's crash test passed). | DEC 1 line 2; V5 lines 164 to 172 | quoted |
| M07 [A7] | OPEN, not an edit | V5 line 12 describes 13 sends (A twice, B ten times at once, C once while n8n is stopped and started) | Cannot tell whether the B and C sends belong to scenes 1 to 4 (run sheet missing). Laptop lead: keep or cut B and C to match scenes 1 to 4; if cut, also change V5 lines 12 and 114 ("n8n stopped once"). Not decided. CONFLICT X5 (same V5 line 114 as M17). | V5 lines 12, 114; DEC 1 | HELD (open question 2) |
| M08 [B1] | UNKNOWN (any sentence saying `end` deletes or archives contacts) | OLD UNKNOWN. Closest known: V5 line 127 "The program then deletes this run's contacts." and V5 line 31 ('The program's own screens say "archive" for the contact deletion; it means delete') | "`end` only closes the pause and deletes nothing. The owner deletes leftover made-up contacts by hand." CONFLICT X2 (with M61) and X3 (with M69). | EDC line 12 (Rule); DEC 2 line 3 | HELD (end behaviour UNVERIFIED; open question 5) |
| M09 [B2] | UNKNOWN (warning before the film pause) | OLD UNKNOWN. Closest known: V5 line 124 "closing the terminal, pressing Ctrl-C, or typing two wrong words in a row ENDS the pause and DELETES the test contacts from HubSpot BEFORE they are filmed." | Heading: "`end` ONLY CLOSES THE PAUSE (it deletes nothing)". The deletion half of the V5 warning goes away only after VERIFIED; the "type exactly `end`, only when filming is done" half stays. CONFLICT X2 (with M61). | EDC line 19 (heading text); V5 line 124 | HELD |
| M10 [B3] | UNKNOWN (run-day step 9 in the owner card numbering) | OLD UNKNOWN | "Up to 3 made-up contacts are left for you to delete by hand." CONFLICT X2 (with M61, which says the run's contacts must be deleted before 18:29 UTC). | EDC line 19 | HELD |
| M11 [B4] | UNKNOWN (new run-day step 15) | none | "STOP. `end` has closed the pause. The made-up contacts are still in HubSpot. Do nothing. Wait for the studio lead's chat message with the list. If no list arrives within 15 minutes of your `end` (write down the time you typed `end`), message the studio lead and delete nothing." CONFLICT X3 (with M69). | EDC line 20 | HELD |
| M12 [B5] | UNKNOWN (new run-day step 16) | none | "The studio lead's list gives, for each leftover contact, the lead id (the number the program gives each made-up test person; the program may print it as 'lead key') and the HubSpot contact id, at most 3, ids only, no names or addresses. The message shows its send time in UTC and IST." | EDC line 21 | HELD |
| M13 [B6] | UNKNOWN (new run-day steps 17 and 18) | none | Step 17: "STOP. Wait for the exact words 'contacts may be deleted'. ... Do not accept a similar phrase such as 'demo mails may be deleted'; that one is for Gmail mails only." Step 18: open one listed contact by its contact id in the demo HubSpot account; read its lead id; if it differs from the list, STOP and tell the studio lead. | EDC lines 22, 23 | HELD (word not confirmed; open question 4) |
| M14 [B7] | UNKNOWN (new run-day steps 19 and 20) | none | Step 19: "STOP. Deleting cannot be undone. Click Delete on that one contact only. Then go back to step 18 for the next listed contact." Step 20: "Reply in chat: 'contacts deleted: N of M' ... If a listed contact is missing, delete nothing more and tell the studio lead." | EDC lines 24, 25 | HELD |
| M15 [B8] | UNKNOWN (old run-day steps 13 to 16) | OLD UNKNOWN: still say `end` deletes (per the M17 notes) | New steps 15 to 20 (M11 to M14) REPLACE old steps 13 to 16 of OWNER-RUN-DAY-CARD.md (the owner card's numbering, not necessarily v4.2's). Laptop lead maps to v4.2. | EDC line 4 (Status) | HELD |
| M16 [B9] | UNKNOWN (release-word row and clean-up row) | OLD UNKNOWN. Known old word: 'demo mails may be deleted' | New word "contacts may be deleted" for HubSpot contacts; the old word stays for Gmail demo mails. Clean-up step 3a: "STOP. Do this only if the studio lead wrote 'contacts may be deleted'. Delete only the contacts the studio lead listed. Reply 'contacts deleted: N'." The new word is NOT confirmed: due Tue 17 Nov 12:00 UTC / 17:30 IST (proposal, nobody agreed). | EDC lines 26, 29 | HELD (open question 4) |
| M17 [B10] | UNKNOWN (failed-take step, V5 step G equivalent) and V5 line 114 ("up to 3 contacts deleted at the end") | OLD UNKNOWN. Closest known: V5 line 114 and V5 lines 135 to 138 | Change the notice sentence to match: the take deletes nothing; leftover contacts are listed. Whether the program's own printed notice still says "deletes" is a program text issue (EDC line 15): core-hardening, not this runbook. CONFLICT X5 (same V5 line 114 as M07). | EDC line 15; V5 lines 114, 135-138 | HELD |
| M18 [B11] | UNKNOWN (the HubSpot key can/cannot delete question) | Closest known: V5 line 130 "If the HubSpot key the program uses cannot delete contacts, the deletion can fail after the sends." | Remove: the HubSpot delete-scope question is moot. (Moot only if the program really deletes nothing, which is UNVERIFIED.) | DEC 2 line 3 | HELD |
| M19 [C1] | UNKNOWN (n8n port line or rows) | OLD UNKNOWN | "Rehearsal: n8n on port 5690. The real take uses its own free port (TAKE_PORT: NUMBER NOT GIVEN in any source; the lead names it, once, in the plan). Ports 5678 and 5679 are the owner's own n8n and are never used by the take." | DEC 6 (line 7); plan-wp6-resmoke-v5.md lines 271, 421 | quoted (TAKE_PORT open; question 3) |
| M20 [C2] | UNKNOWN (any row that names one port for both rehearsal and take) | OLD UNKNOWN | Split into two rows: rehearsal 5690; take TAKE_PORT. The plan names the take port in ONE place only; every other mention points to it. | DEC 6 | quoted |
| M21 [C3] | OPEN, not an edit | n/a | 5691 is the n8n runner broker port in the re-smoke plan; whether the take also needs a second port next to TAKE_PORT is NOT KNOWN. | plan-wp6-resmoke-v5.md line 271 | HELD (open question 3) |
| M22 [D1] | UNKNOWN (any step or gate "checks a to f on real accounts") | OLD UNKNOWN. Closest known: OS:87 as quoted in drift/REPORT.md line 41 "(a) to (f) of the smoke (WP6-RUNBOOK) with NO paid call" | "The real-account smoke (checks a to f) is replaced by the loopback re-smoke plus ONE made-up lead in take prep. No extra real smoke." | DEC 8 (line 9) | quoted |
| M23 [D2] | UNKNOWN (gate before the take) | OLD UNKNOWN | The take gate now reads: loopback re-smoke passed AND one made-up lead sent in take prep. Not proven by anything yet (the re-smoke has not been run: plan-wp6-resmoke-v5.md line 4 "NOTHING was run"). | DEC 8; plan-wp6-resmoke-v5.md line 4 | quoted |
| M24 [E1] | UNKNOWN (proof screen row) | OLD UNKNOWN. Closest known: V5 line 122 "The proof screen is your choice. The studio lead offers candidate screens (n8n's list of runs, the rows of the people table, HubSpot, Gmail)." and V5 line 100 | "The counts proof is a rehearsal screenshot or the Postgres node preview, not a live table screen." The owner no longer picks a live table screen. Keep: the video shows no portal, approval step or audit trail. CONFLICT X4 (same sentence as M25; the two are not contradictory). | DEC 9 (line 10); V5 line 122 | quoted |
| M25 [E2] | UNKNOWN (step E in V5: "you pick one and say which") | Closest known: V5 line 100 and line 122 | Remove "you choose it" for the live table screen; the studio lead names the screenshot file. File name NOT GIVEN in any source. CONFLICT X4 (same sentence as M24; not contradictory). | DEC 9 | quoted (file name open; question 10) |
| M26 [F1] | UNKNOWN (every sentence that says "one database", "one store" or "one Postgres") | OLD UNKNOWN. Closest known: V5 line 213 "the aim is one database for the run (its Postgres, shared by n8n and our table of test people)" and DECISION-one-store.md line 14 "ONE database for everything we own: the single Postgres instance of the take (one container, one engine). n8n's internal data in its own schema or database" | "one Postgres server with two databases (n8n's own and the take's)" CONFLICT X6 (same V5 line 213 as M28; compatible). | DEC 10 (line 11) | quoted |
| M27 [F2] | system-map/DECISION-one-store.md line 14 (and its copy inputs/DECISION-one-store.md line 14; the two copies differ, not diffed in detail) | see M26 | Replace line 14's heading "ONE database for everything we own" with the DEC 10 wording. NOT in the runbook; listed so the laptop lead does not miss it. Consistent with DECISION-one-store.md line 26 (a), where n8n lives in a separate database `n8n`. | DEC 10 line 11 | quoted |
| M28 [F3] | UNKNOWN (records note) | Closest known: V5 line 213 (also lists `stage.journal` as the one file exception) | Keep the `stage.journal` exception sentence; only the "one database" count changes. CONFLICT X6 (same V5 line 213 as M26; compatible). | V5 line 213; DECISION-one-store.md line 17 | quoted (no change to the exception) |
| M29 [F4] | UNKNOWN (owner steps version) | OLD: V3 (inputs/OWNER-STEPS-realrun-v3.md) | DEC 10: OWNER-STEPS v4 and later replace v3; archive v3, never delete. | DEC 10 line 11 | quoted |
| M30 [G1] | UNKNOWN (any "clean up / archive handover folders" step) | OLD UNKNOWN | "Licence copies under handover/promotion-inputs (Apache-2.0 from other holders) are never overwritten or re-licensed. Verdict KEEP-AS-IS only (never ARCHIVE or MERGE-INTO). They are a BRANCH ARTEFACT. Patch tests run on a clean sdk tree." | DEC 11 (line 12); PLAN-002.md line 50; ORDERS.md line 177 | quoted (folder not in checkout) |
| M31 [H1] | UNKNOWN (n8n setup step) | OLD UNKNOWN. Closest known: V5 line 40 "C: ... n8n sign-in only if asked." | "n8n first-visit owner setup is already done (FACTS-ALREADY-DONE.md). The lead imports and activates the flows with scripts/n8n_api.py on made-up data. The owner only types y, the challenge and end." | DEC 7 (line 8); inputs/FACTS-ALREADY-DONE.md line 3 | quoted |
| M32 [H2] | UNKNOWN (rehearsal step or owner of the first rehearsal) | OLD UNKNOWN | "First laptop rehearsal of the changed flows: the lead runs it, right after the loopback re-smoke passes (target tonight or tomorrow morning IST). The times go in the handoff." Owner does nothing in a rehearsal (V5 line 26). | DEC 12 (line 13); V5 line 26 | quoted |
| M33 [H3] | UNKNOWN (rehearsal gate in the written yes) | V5 line 74 "that the rehearsal passed, with the name of its result file. No rehearsal pass, no run." | Unchanged in rule. It now rests on rows M23 and M32. Not yet proven: V5 line 205 says the rehearsal "has NOT been run". | V5 lines 74, 205 | quoted (no text change) |
| M34 [28-a] | ? | ? | ? | 13o/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M35 [28-b] | ? | ? | ? | 13o/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M36 [28-c] | ? | ? | ? | 13o/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING (round 28 item count unknown; add rows) |
| M37 [32-a] | ? | ? | ? (money wording: do not paraphrase when filling) | 13p/?:? | SOURCE MISSING |
| M38 [32-b] | ? | ? | ? (money wording: do not paraphrase) | 13p/?:? | SOURCE MISSING |
| M39 [32-c] | ? | ? | ? (money wording: do not paraphrase) | 13p/?:? | SOURCE MISSING |
| M40 [33-a] | ? | ? | ? | 13q/?:? | SOURCE MISSING |
| M41 [33-b] | ? | ? | ? | 13q/?:? | SOURCE MISSING |
| M42 [33-c] | ? | ? | ? | 13q/?:? | SOURCE MISSING |
| M43 [34-1] | ? | ? | ? | 13s/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M44 [34-2] | ? | ? | ? | 13s/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M45 [34-3] | ? | ? | ? | 13s/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M46 [34-4] | ? | ? | ? | 13s/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M47 [34-5] | ? | ? | ? | 13s/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M48 [34-6] | ? | ? | ? | 13s/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M49 [34-7] | ? | ? | ? | 13s/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M50 [36-1] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M51 [36-2] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M52 [36-3] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M53 [36-4] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M54 [36-5] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M55 [36-6] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M56 [36-7] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M57 [36-8] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M58 [36-9] | ? | ? | ? | 13r/LANE-D-REPORT-SUMMARY.md:? | SOURCE MISSING |
| M59 [P1] | V5 line 17 (Stop time bullet); v4.2 line UNKNOWN | "The program refuses a start that is too close to it (it needs about 14 minutes), so the latest start is before about 18:15 UTC = 23:45 IST; the studio lead gives you the exact latest start time." | "The whole run, in its slowest case, takes up to 49 minutes. The program refuses a start that leaves less than 49 minutes before this time, so the latest start is 17:40 UTC = 23:10 IST; the studio lead gives you the exact latest start time." Depends on open question 1. | TCA row 1; V5 line 17 | PROPOSAL |
| M60 [P2] | V5 line 201 (Start deadline bullet); v4.2 line UNKNOWN | "- **Start deadline:** the program refuses to start unless it can finish about 14 minutes before the stop time. With stop time 18:29 UTC, the latest start is before about 18:15 UTC (23:45 IST). The studio lead gives the exact time." | "- **Start deadline:** the program refuses to start unless the slowest case of the run (49 minutes) fits before the stop time. With stop time 18:29 UTC, the latest start is 17:40 UTC (23:10 IST). The studio lead gives the exact time." Also removes a wording clash (line 17 says "needs" 14 minutes, line 201 says "finish" 14 minutes before). The matching change in the program or `stage.env` is a separate item; neither file is in this checkout. | TCA row 2 and its arithmetic section; V5 line 201 | PROPOSAL (needs open question 1 and 6) |
| M61 [P3] | V5 line 127 (Step F, film pause); v4.2 line UNKNOWN | (sentence to extend; rest of line stays) "Type `end` and Enter yourself only when that person tells you the contact list is filmed (if you film, when you have filmed it)." | Same sentence plus: "The film pause lasts at most N minutes. If filming is not finished N minutes after the pause starts, tell the studio lead at once. This run's contacts must be deleted before 18:29 UTC = 23:59 IST." N is the lead's choice, not measured. CONFLICT X2: the last sentence says the run's contacts are deleted by the stop time; M08 to M10 say `end` deletes nothing and the owner deletes by hand. | TCA row 15; V5 line 127 | PROPOSAL, CONFLICT X2 |
| M62 [P4 option 1] | V5 lines 134-140 (Step G, failed run), edits line 140; v4.2 line UNKNOWN | "If the studio lead later says a new run is no longer possible before the stop time, no new run happens." | "There is no spare time for a second run on the take day: one run in its slowest case fills the whole window (17:40 UTC plus 49 minutes is 18:29 UTC). A failed run therefore means a new run day." Only holds if the 49 minutes are a full run from start to last deletion. CONFLICT X1 (alternative to M63). Line 139 ("Give a NEW written yes with numbers ... pick a NEW run name") stays, but the new yes must carry the latest start time (M66). | TCA row 16 | PROPOSAL, CONFLICT X1 |
| M63 [P4 option 2] | same as M62 | same as M62 | "A second run is possible only if the first run failed and was cleaned up early enough that the new start still comes before 17:40 UTC = 23:10 IST. The studio lead decides this and says so by message; otherwise no new run happens." Needed if the 49 minutes are not a full run. CONFLICT X1 (alternative to M62). | TCA row 16 | PROPOSAL, CONFLICT X1 |
| M64 [P5] | OTHER FILE: RUNBOOK-SPEED-3.md, add after line 75 (test-speed windows) | (quoted by TCA, not re-read) "Per window add 20 minutes slack ... a full demo item = 2 x 15 + 3 x 7 = about 51 min + 20 slack = about 71 min." and "sdk-Linux ... 2 x 14 + 3 x 8 + broken 8 + posix 1 = about 61 min + 20 = about 81 min." and "Run demo and sdk in SEPARATE windows, never at the same time" | Add: "Do not run these windows on the take day, or on the take laptop, between 17:00 UTC and 18:29 UTC on Mon 23 Nov 2026. The two windows together take 71 + 81 = 152 minutes; each alone is longer than the 49-minute take window." TCA checked the arithmetic. | TCA rows 22, 23, 24 (row 26 for the laptop rule) | PROPOSAL |
| M65 [P6] | OTHER FILE: RUNBOOK-INPUTS.md, add after line 32 (serial run lengths) | (quoted by TCA, not re-read) serial runs of 886 s, 1026 s, 894.6 s, 953 s, and "about 15 minutes without Playwright and about 17 minutes with it" | Add: "A full serial run takes 15 to 17 minutes. Do not start one inside the take window." | TCA row 32 | PROPOSAL |
| M66 [P7, line 76 part] | V5 line 76 (example yes); v4.2 line UNKNOWN | `"Yes, run <run name>, up to 3 model calls and up to US$<the total in the message>, stop time 2026-11-23 23:59 IST."` | `"Yes, run <run name>, up to 3 model calls and up to US$<the total in the message>, start no later than 2026-11-23 23:10 IST (17:40 UTC), stop time 2026-11-23 23:59 IST (18:29 UTC)."` | TCA rows 8, 9 | PROPOSAL |
| M67 [P7, line 73 part] | V5 lines 72-73 (step A list) | `- the planned stop time 2026-11-23 18:29 UTC = 23:59 IST;` | Add after it: `- the latest start time, 17:40 UTC = 23:10 IST, and the slowest-case length of the run, 49 minutes;` | TCA rows 8, 9 | PROPOSAL |
| M68 [P8] | V5 lines 38-45 (Order of the day), add after line 45 | the seven numbered steps A to J with no times | Add one line: `Steps A to D must be finished by 17:25 UTC = 22:55 IST (15 minutes before the latest start of 17:40 UTC = 23:10 IST). Step E starts at the time the studio lead names, never later than 17:40 UTC.` The 17:25 UTC deadline and 15-minute margin are proposed, not measured. | TCA row 10 | PROPOSAL |
| M69 [P9] | V5 line 46 (Fixed times) | `The stop time limits only the start and the spending of the run. Watching (H) and clean-up (I) have their own deadlines, which the studio lead gives you (open); they are not tied to the stop time.` | `By the stop time the run must have finished spending and must have deleted its contacts (steps E and F). Watching (H) and clean-up (I) come later and have their own deadlines, which the studio lead gives you in UTC and IST.` Only after the lead confirms which steps sit inside the 49 minutes. CONFLICT X3: says the run deletes its contacts; M08 and M11 say the owner deletes them by hand after `end`. H and I deadlines are still empty (V5 lines 145, 150-152). | TCA rows 4, 5 (and 18, 19) | PROPOSAL, CONFLICT X3 |
| M70 [P10] | V5 lines 206-213 ("What is not proven yet"), add a bullet | none | Add: `The 49-minute worst case is a planning figure. It has not been measured; the rehearsal measures it.` Only if true; the lead confirms. Same line range as M26 and M28 (X6). | TCA row 21 | PROPOSAL |
| M71 [P11] | V5 line 52 (settings file sentence) | `A spending backstop and the stop time sit in a settings file that a person checks` | `A spending backstop, the stop time and the 49-minute start rule sit in a settings file that a person checks` Only valid if the program really takes the rule from the settings file; neither the program nor `stage.env` is visible: UNVERIFIED. | TCA row 7 | PROPOSAL (UNVERIFIED) |
| M72 [P12, step C part] | V5 lines 87-90 (step C: mailbox, browser profile, n8n sign-in) | no length written | Add at the end of step C: "allow 20 minutes (PROPOSED, not measured)". Do not invent other numbers. | TCA rows 11, 12, 14 | PROPOSAL |
| M73 [P12, lines 108 and 120 part] | V5 lines 108-113 and 120 (step E command to notice, notice to sends; n8n stop and restart) | no length written | Add "(length to be measured in the rehearsal)" at lines 108 and 120. The rehearsal has not run. | TCA rows 11, 12, 14 | PROPOSAL |

## Rows kept as "no change" in part 3 (TCA "NO")

V5 line 116 (2 seconds), line 164 (post time 20:30 IST), line 191 (exit code 2 wording), RUNBOOK-SPEED-3 line 9 and line 72. No edit. Note: M06 (A6) also touches V5 line 164 (claim sentence, different content from the post time).

## CONFLICTS (shown, none resolved; the lead chooses)

| id | rows | what clashes |
|---|---|---|
| X1 | M62 vs M63 | Two alternative wordings for the same sentence (V5 line 140, failed run): no second run on the take day (option 1) or a second run allowed if it still starts before 17:40 UTC (option 2). Depends on open question 1, item 3. |
| X2 | M61 vs M08, M09, M10 | M61 (V5 line 127) says this run's contacts must be deleted before 18:29 UTC. M08 to M10 say `end` deletes nothing and the owner deletes leftover contacts by hand (and V5 lines 124 and 127 are where the old "program deletes" wording sits). |
| X3 | M69 vs M08, M11 | M69 says the run must have deleted its contacts by the stop time (steps E and F). M08 and M11 say the contacts are still in HubSpot after `end` and are deleted later by hand after the studio lead's list. |
| X4 | M24 vs M25 | Both edit the same V5 sentence about who picks the proof screen (lines 100 and 122). They do not contradict each other, but they overlap; merge or keep both. |
| X5 | M07 vs M17 | Both name V5 line 114 (the "n8n stopped once" wording and the "up to 3 contacts deleted at the end" wording). The sentences may differ; not compared with the line itself. |
| X6 | M26 vs M28 (and M70 nearby) | Both edit V5 line 213 ("one database for the run" and the `stage.journal` exception). Compatible in wording. M70 adds a bullet in the same range, lines 206 to 213. |

Same block but not the same sentence (not marked, checked by line number only): M62 and M63 are in V5 lines 134 to 140, M17 is in lines 135 to 138. Also M33 (V5 line 74) sits beside M66 and M67 (lines 72 to 73, 76).

## OPEN QUESTIONS (who must answer)

| # | Question | Blocks | Who must answer |
|---|---|---|---|
| 1 | What exactly do the 49 minutes contain? (a) Does the count start at typing the command (step E) or at step A; does it include steps A to D? (b) Does it include the film pause, and how long (N in M61)? (c) Does it include a failed run's clean-up and a second run (M62 or M63)? (d) Does it include the n8n stop and restart while person C is sent (V5 line 120)? (e) Is 49 minutes measured or a planning figure (M70)? The only mention is ORDERS.md line 183. | M59, M60, M61, M62, M63, M68, M69, M70 | Studio lead (the order's author); the rehearsal can measure it later |
| 2 | A7: do the B and C sends (ten at once; one while n8n is stopped and started) belong to scenes 1 to 4? The run sheet is missing. | M07 and V5 lines 12, 114 | Laptop lead (holds the run sheet) |
| 3 | TAKE_PORT: what number is the take's own free port? Does the take also need a second port next to it (5691 is the runner broker port in the re-smoke plan)? | M19, M20, M21 | Studio lead (names it once in the plan) |
| 4 | The word "contacts may be deleted": is it the agreed release word for HubSpot contacts? Proposed, nobody agreed; due Tue 17 Nov 2026 12:00 UTC / 17:30 IST. | M13, M16 | Owner and studio lead |
| 5 | What does `end` really do? Unverified because the run program is not in the checkout. Release of M08 to M18 waits for the studio lead to quote the program's `end` lines on the M17 page and write VERIFIED. If it still deletes, it is a program defect for core-hardening, not a runbook variant. | M08 to M18, M61, M69 | Studio lead (reads `scripts/run_real_check_n8n.py`) |
| 6 | Where does the program's "about 14 minutes" live (program source or `stage.env`), and does the program take the 49-minute rule from the settings file? | M60, M71 | Studio lead (program and `stage.env` are not in the checkout) |
| 7 | Is "WP6-RUNBOOK.md" the same document as runbook v4.2? And please push v4.2 so the line column can be filled. | all rows (v4.2 column) | Laptop lead |
| 8 | Please push the five lane D reports (13o, 13p, 13q, 13r, 13s). Are the item counts (1 to 7, 1 to 9) right? | M34 to M58 | Laptop lead |
| 9 | Which N minutes for the film pause; which margin before the latest start (17:25 UTC is proposed); do steps C and E durations get measured in the rehearsal (M72, M73)? | M61, M68, M72, M73 | Studio lead |
| 10 | Which screenshot file serves as the counts proof? Not named in any source. | M25 | Studio lead |
| 11 | Are handover/promotion-inputs and the DEC 11 licence copies present on the laptop branch? Not in this checkout, so decision 11 cannot be checked. | M30 | Laptop lead |
| 12 | No rows exist for decision 4 (C5 patches) and decision 5 (S9 items: S9-5, S9-12, S9-3 as text; S9-2 keeps the owner compare with the honest sentence; S9-1 and S9-4 describe-only; do not claim "nothing can spend before both typed answers"). Who writes them? Decision 3 (roles proposal parked): if v4.2 mentions four logins or read-only group L, mark "after the video" (the part-1 builder's own suggestion, UNKNOWN whether it applies). | missing rows | Studio lead |

## Counts

Total rows: 73 (M01 to M73).

By state:
- quoted: 20 (M01 to M06, M19, M20, M22 to M33)
- PROPOSAL: 15 (M59 to M73; of these M71 is also UNVERIFIED, and M61, M62, M63, M69 also carry a CONFLICT)
- SOURCE MISSING: 25 (M34 to M58)
- HELD: 13 (M07, M08 to M18, M21)
- Total: 20 + 15 + 25 + 13 = 73.

Rows by part: part 1 = 33 (A 7, B 11, C 3, D 2, E 2, F 4, G 1, H 3), part 2 = 25, part 3 = 15 (from 12 patch entries; P4, P7 and P12 are split in two).

Conflicts: 6 (X1 to X6). Rows involved: M07, M08, M09, M10, M11, M17, M24, M25, M26, M28, M61, M62, M63, M69 (14 rows, plus M70 as a neighbour of X6).

## Not checked

- No row was compared with runbook v4.2 (not in checkout).
- I did not open any source file named in the source column. All quotes and line numbers are carried from the three part files, which were written from static reading and are themselves DRAFT, unverified.
- I did not diff the three parts against each other beyond the same-line check listed under CONFLICTS; sentences on the same V5 line were not compared word by word.
- The part files are unchanged.
