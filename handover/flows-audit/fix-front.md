# fix-front (front matter of RUNSHEET-WORDING.md and CLAIMS-TABLE.md), 2026-11-16

Source of the fixes: reviews/stranger-rw-ct-front-r4.md. Backup of both files before editing: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-front/. Nothing ran except the two read-only checkers.

## What failed, what is unfixed, what I did not check (first)
1. First check run FAILED: my two new tables had 5 cells and tools/check_runsheet_paste.py reads every table row as a paste row (allowed: 3, 4 or 6 cells). I rewrote both tables with 3 cells (who decides and default are inside the cells). Second run: PASS.
2. UNFIXED, question for the coordinator (only the coordinator can choose): renaming the old word "the lead" (= coordinator) and old "claim" (= claim row) across all rows. Defined at the top; not renamed. Logged as question Q-W (section 4 of RUNSHEET-WORDING.md).
3. UNFIXED, open input: who checks, before filming, that the stage service points at the local fake model (written as Q-J and as "Open input" in the status section; unverified; I did not check any stage file).
4. UNFIXED, open input: the channel for "tell the coordinator" in step 10 (Q-I). No file names one.
5. NOT DONE (outside the brief, review items 5 and 8 to 10, 27 to 36 partly): step 6 scene 2 wording of who reads P4a (the open-label table now says laptop agent runs, coordinator reads, no written command, but no command was invented); n8n node names (CrmIdOk and so on) left undefined for a stranger; psql check command for the studio owner not written; "R:" and "P:" key letters, T1.. test names, caption/lower third wording, 45 s lease read from film-v5 only: not touched. Rows resting on take scripts I could not see were not re-statused beyond the table.
6. Not checked: the new status table was built from the section 0b text, the row notes and section 5; I did not read every row of sections 2 and 3, so the group "all other rows of sections 2 and 3 = PASTE after APPROVED" assumes none of them has a wait I missed (their own notes still apply).
7. CT:27 in the review (line number of the old file) had no "may reuse"; the only one was CT line 14 (fixed). 

## What I changed (front matter and definitions only; no row, id, paste cell or verdict changed)
Check: all RUNSHEET-WORDING.md id rows with 5 or more cells are byte-identical to the backup (0 changed), and all 468 table rows of CLAIMS-TABLE.md are identical to the backup.
- Both files: top line "Nothing in this file is approved for the screen until the coordinator marks a row APPROVED; today no row is approved" (coordinator = the lead session, defined once).
- Words defined once at the top of both files: coordinator / lead, studio owner / owner, claim and claim row, typed answers (y and the 6-digit challenge number; end is a third word), verdict words, Z times with IST. Duplicate definitions in RUNSHEET-WORDING.md 0-words and Words and ids now point to the top. CLAIMS-TABLE.md Quick words points to the top for coordinator, the lead and claim.
- RUNSHEET-WORDING.md: the history paragraph is replaced by "Status at a glance": one status table (group of rows, status, who decides, what it waits for, default) with PASTE, CUT, HELD and NO PASTE defined once; the D1 "settled" against "wait" conflict resolved (D1 decided for the screen, rows with a number are CUT, still open: A-073a and A-073c on the page); A-051b is CUT (removed from the D1 and D2 wait lists in 0b); A-081a listed as PASTE because its string holds no number (the old list that called it CUT contradicted its row); the sentence "No relayed number is spoken or shown in this video; only the D2 decider can change that" (also in 0a D2); one table of open labels P1 P2 P4a P4b P4c Q-A Q-B Q-E Q-F Q-H D1 D2 D3 plus the one-line note that D1 to D3 are not the numbered lead decisions (ids not renamed).
- A-050c: now "optional" in 0b and step 9. Q-F: A-016f is the scene 3 caption whatever happens to the closing card (0b, section 4 Q-F, step 10); the old "lines 1, 3, 5, 6 default" text replaced by the one card line (Q15, Q19-2). Step 10 says the words on screen are only the general sentence and that the check is for the coordinator.
- "v3/v4/v5" defined as flow sets in both files. "40 = the 80 kills that ended unknown" is now "how many of those 80 kills ended in the state unknown".
- CLAIMS-TABLE.md: line 14 "may reuse" now says the take does NOT use the desk script (matches line 59 and Q13). Explained "95 claims in 87 rows" (a row can cover several claims, example row 13 with A-041, A-042, A-097; five rows have no claim id). Verdict sum line added.
- IST added next to Z times in the front parts of both files (10:23Z = 15:53, 10:29Z = 15:59, 10:58Z = 16:28, 11:10Z = 16:40, 11:20Z = 16:50, 17:05Z = 22:35 IST). Z times inside rows were not touched.
- Verdict counts (from python3 claims-count.py CLAIMS-TABLE.md): SUPPORTED 124 + RELAYED-ONLY 69 + OVERSTATED 54 + UNSUPPORTED 29 + UNTRACED 51 = 327. The earlier 273-of-327 gap was the 54 OVERSTATED.

## Commands and output
- python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md : RESULT: PASS (158 rows with a paste cell: 39, 17, 61, 41).
- python3 claims-count.py CLAIMS-TABLE.md : total 327; to-do rows 87; offenders: 0 []; ids 327 unique 327.
