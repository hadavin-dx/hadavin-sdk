# c6g changes (REPORT-c6f.md revised in place, file name kept; REPORT.md revision 3). One row per item. Nothing was run; no git; no flow or program file edited.

Base folders and the scratchpad copies are defined in REPORT-c6f.md ("Base folders"). Before-copies of both reports are in the scratchpad (REPORT-c6f.before-c6g.md, REPORT.before-c6g.md).

## Failures and things not fixed (first)
- Not run: n8n, Postgres, mail and CRM services. Every runtime claim (saved-run settings, error workflow firing, two flow sets, T7b results) stays UNVERIFIED.
- The files I read are scratchpad copies, not git. I did not diff them against origin/cloud/flows-audit or origin/demo/lane3, and the scratchpad can be cleared. The durable copy is C/raw-lane3/ (source commit 23f3101a).
- Still not found anywhere: qualify_stage.py, the take's n8n_start.sh (only a 2-line and a 16-line stub from other work exist), the take's scripts/n8n_api.py, the V7 laptop raw files (mf_result_*.json), the bible text (rule R460).
- Not re-read in c6g: owner steps v10 to v15 and OWNER-SHEET v16 to v18 (grep hits and v18-OPEN-FOR-LEAD.md only), so rows D2, D5a, D6, D8 and CS1 are not settled against the newest sheet; real-v5 flow JSON; FA/FINDINGS.md rows other than F-003, F-007, F-008, F-011, F-019.
- A new conflict I cannot fix (needs the lead): decision 2 says the take never deletes contacts; AGENT-SCOPE-DO-AND-DONT.md:20 says the take's code archives them with a DELETE call (finding F-01). Options: fix the code, or change decision 2 in writing (REPORT-c6f.md row D2).
- Not decided by any file (lead): Q1 (does the closing card stay), Q2 (kill-case sentence in scene 4), Q9 (rounded time wording), Q10 (which owner sheet; default now v18).

## Items of citation-check-c6.md

| id | what I did | where |
|---|---|---|
| X1 ("5678" 0 hits) | Re-ran the search myself: v9 lines 9 and 227, plan lines 121, 230, 421, 486, 489. Corrected the claim; "own free port" 0 hits stays. Added v18 item 4 (ports 5701 and 5702 proposed, unsourced). | REPORT-c6f.md section 0, row D6 |
| X2 ("twice" 0 hits) | Read plan line 341 (cases A and B) and QUESTIONS.md:22. Said the phrase search missed them; the plan fills film-v5, not real-v5. | section 0, section 2, row P1 note |
| X3 (v9 :408) | Read v9 :18 and :408. Counts are at :18; :408 is only the fixed notice text. | section 0, section 2 |
| X4 (no v10 sheet) | Listed steps-edits/: v10 to v15, appendixes, day cards, OWNER-SHEET v16 to v18. Q10 default now v18. Rows CS1, D10-archive corrected (clean start exists in v10 :24 and v15 :59). | section 0, Q10, rows CS1, D10-archive |
| X5 (T7b not found) | T7b is t7b() in A/n8n-mainframe/mf.py :274; read :275-296. | row M2, glossary |
| X6 (files absent) | Located all files in the scratchpad copies; kept NOT FOUND only for files not on disk anywhere. | section 0, section 9 item 4, rows N1, N2, F-007f, N3a, N3b, N5, c6b-1, c6b-5, review-design-3, F-023, F-025, section 7 |
| X7 (lane3 REPORT.md not opened) | Read L3/REPORT.md lines 9 to 20: old flows alert at 750 s (earlier n=2 runs 780 s); fixed flows 60 s in 3 of 3 runs; fixed flows not imported into the demo flows and not reviewed. The faster alert is a different fault (kill during alert send) and is not in the take's flows. | row N7 |
| X8 (HB194 only in a commit message) | Found HB194 in the run sheet :90, page :20 and :148 and evidence files. Withdrew the claim. I read no commit message. | section 0, row N8 |
| X9 (G5 undefined) | G5 is the core patch patches-ready/v5/G5-wording.patch (text and comments only); the plan's G5 row (:540) is a different thing. Applied or not: not checked. | row Z1b, glossary |
| X10 (REPORT.md "NOT READ") | Added a "Revision 3" box at the top of REPORT.md and replaced the "could not read" and "NOT READ (absent)" lines. | REPORT.md |
| X11 (mf.py:158 NOT FOUND) | Read mf.py :153-164: K3B and K3 definitions confirmed. | rows F-007a, F-007b, section 6 |

## Open Majors of review-design.md

| item | result |
|---|---|
| M1 caption number not backed | Read the lane3 raw and recomputed it (python3 -I): 18 kept runs, 60.1 to 61.9 s, median 60.85; per case K1 5 runs 60.1/60.8/61.9, K2 5 runs 60.4/60.9/61.2, K3 5 runs 60.1/60.4/61.6, K6 3 runs 60.1/60.1/61.5. Backed for film-v4 stand-in flows only; the lead's decision 1 cuts the number. If reversed: K1-only caption as in the F-003 patch. Found a third contradiction (scene 4 row :33 keeps the dropped "lease plus 25 to 30 s" caption). Row M1. |
| M2 T7b invalid with saved runs on | Re-scoped. t7b() forces saving off itself (mf.py:278), so it tests a setting the take does not use. New rule: key and mail password 0 hits (a real test that can fail: N8N-START.md:27 reports a laptop test where the key was found with saving off); name and e-mail allowed only in n8n's own database, 0 hits in the stage journal, stage logs and spend ledger. Not run. Row M2; REPORT.md T7b block. |
| M3 F-007 reach (K3B, mf.py:158) | Confirmed from the files: nine run-sheet lines contain K3; :90 permits the false sentence; page :49 is right but :150 and :153 are wrong; mf.py:158 says mail NOT yet delivered. Data now backs the K3B words: mail_sent t at the kill and 0 intake mails in 5 of 5. Rows F-007a to F-007g, K3B-mail-before-kill. |

## Items of review-codebase.md not yet in c6f

All its corrections (K3 on :36, nine K3 lines, F-025 30 s sweep, N2 wording, N3 split, F-023 cites, F-011 DB_ names) were already in c6f or in C/REPORT.md. What c6g added: the F-003 patch has five hunks (not one), re-opened and dry-run on the copy (nothing changed); the "allowed on the closing card" claim stays dropped; N1 sets differ shallowly: not needed after decision 1.

## New corrections found while re-opening files (not on any list)
- c6f and the citation check read the fourth field of rows_at_kill as a CRM flag. L3/kill/harness.py:192 selects lead_key, state, attempts, mail_sent, crm_id: it is mail_sent. Fixed in rows F-007a, F-007d, K3B-mail-before-kill and sections 6 and 8. The CRM fact comes from the CRM id (set at the kill in all 8 lane3 K3 and K6 runs, empty in K1 and K2).
- c6b-1 (voided runs): the reviewer's guess that another test queue emptied the claim table is not supported by the harness, since each queue has its own database and ports (harness.py:22-25). The cause stays UNPROVEN.
- Run sheet :24 is incomplete, not false.
- Scene 4 kills at the K1 point (run sheet :33); the closing card is the last scene (:41). Q1 and Q2 rewritten.
- "F-01" in the lead's note is finding F-01 of review-codebase-1.md (AGENT-SCOPE-DO-AND-DONT.md:20).
- The 20-second settle wait (harness.py:341) comes after kill_to_final_s and recovery_s are taken (:339-340), so it does not inflate them.

## Counts and hygiene
Files edited: REPORT-c6f.md, REPORT.md; file written: c6g-CHANGES.md. Scratch scripts are in the scratchpad only. No process, shell or container was started that is still running. The word list of the repo guard was applied to both edited reports with a plain search (0 hits); no banned word is printed here.
