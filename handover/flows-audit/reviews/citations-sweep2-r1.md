# Citation check, sweep 2, round 1 (read-only checker, 2026-11-16 ~11:15 UTC)
Scope: FINDINGS, FIX-PLAN, CUT-LIST, EXCEPTIONS, REPORT, QUESTIONS, LEDGER-ROWS against fix-sweep2.md. Made-up data only.
CAUTION: another session edited FINDINGS (140 to 147 lines), FIX-PLAN (26 to 34), QUESTIONS, CUT-LIST and REPORT at 11:12:52 UTC while I was reading (new NOT COVERED items 22-27, ORDERS.md line 138 answers). I re-checked line-sensitive items against the 11:13 version. fix-sweep2.md does not describe that edit.

## WRONG (first)
| file:line | claim | source shows | verdict |
|---|---|---|---|
| QUESTIONS.md:5 | Q2 answer: "executions saved ON for the take only and deleted at clean-up (F-008 patch)" | Q19-1, Q21 and the F-008 patch comment: nothing deletes saved runs. No SUPERSEDED tag on this line. | WRONG (requirement "no file says deleted at clean-up" fails here) |
| QUEUE.md:8 and ORDERS.md:20 (outside the seven; fix-sweep2 flags QUEUE only) | "executions saved ON ... and deleted at clean-up" | same | WRONG; lead-owned; ORDERS.md:20 is the lead's order text, not flagged by fix-sweep2 |
| EXCEPTIONS.md:8 | "Rows 1 and 6 are DECIDED" | the table has 4 rows (lines 4-7); the ledger row is row 3 ("MERGED into row 1") | WRONG: should say rows 1 and 3 |
| FINDINGS.md:122 (F-010) vs F-041 (:112), F-011 (:110), FIX-PLAN:24 | F-041: "role count: F-010 is the one place (four with n8n's own role)"; fix-sweep2 (c): "F-010 named canonical for the role count" | F-010 row says "split into a reader and a writer role" (two) and gives no count; FIX-PLAN:24 says three plus n8n's own = four; ROLES-PROPOSAL.md:63 says four flow logins plus one table-owner login | WRONG: F-010 does not hold the count, and the three numbers disagree |
| FINDINGS.md:57 (NOT COVERED item 27) | reviewer read "FINDINGS 1 to 96 ... 97 to 136 not read" | after the 11:12 insert of items 22-27 the findings table is lines 103-147 | WRONG by shift (stale line ranges) |
| F6B-AUDIT.md:103, fix-f6b-r2.md:7 (outside the seven) | F-031 is at FINDINGS.md:93 | line 93 is now the "Scenes:" paragraph; F-031 row is line 106 | WRONG (shifted; fix-sweep2 item 5 predicted this) |
| QUESTIONS.md:81 and :91 | two headings both named "Q22" | FIX-PLAN item 3 cites "Q22-3", "Q22-4", "Q22-5": only the first Q22 (take-day read) has those meanings; the second Q22 items 3-5 mean other things | WRONG: one name, two meanings |
| fix-sweep2.md:6, :33, :44 | Q20 item 4 "stays open"; REPORT "open: Q20 item 4 and Q22" | QUESTIONS:68,72,96, FIX-PLAN:6 and REPORT:13 now say ANSWERED (ORDERS.md line 138) | stale log (files are right, the log is not) |

## OK (checked against source)
| file:line | claim | source shows | verdict |
|---|---|---|---|
| tools/count_findings.py | 45 rows, 5/7/33, BEFORE 13, AFTER 32 | printed exactly that (run twice, before and after the 11:12 edit) | OK |
| LEDGER-ROWS.md | 45 rows, ids and severity words equal FINDINGS, 9 columns | python comparison: equal, 45 rows, 11 pipe-fields each | OK |
| FINDINGS table | counts table only; old 8/8/29, 17/28 appear only tagged SUPERSEDED/AUDIT TRAIL in FINDINGS, QUESTIONS:23, REPORT:10 | OK in the seven; untagged old count remains in STATUS-BOARD.md:29 (outside) | OK / note |
| F-008 patch line 12 | saveManualExecutions True | line 12 `+ST = {... "saveManualExecutions": True}` | OK |
| n8n-owns-vs-desk-owns.md:12 | item 9, "n8n marked the run 'crashed' after the restart and did not run it again" | line 12 item 9; source has double quotes around crashed (quote marks differ only) | OK |
| table-screen-v2 README:3, :49, :51 | "NOT run in n8n" at 3 and 51; "public" at 49; v1 README:3 "NOT RUN"; v2 README says v1 "was run live ... works" | all match | OK |
| mf.py (demo/n8n-mainframe) | T17 339-347, T18 348-357, M0 :119, M1 :129, mf.py:77-78 reads crm_id, :8 import, :44-47 DDL, :12 journal name | all match | OK |
| build_mainframe.py | :82-83 INSERT, :84 Claimed IF, :44 ST none, :54, :56 retry false, :99 SKIP LOCKED LIMIT 5, :100/:102/:103/:106/:111/:113 continueRegularOutput, :27, :109, :116, :75, :87, :102 RunSub | all match | OK |
| PLAN-4-NLITE-FROM-LEAD.md | :77 key pattern, :79 single flight, :82 hyphenated "single-flight", :47 resend, :106 "up to 3 model calls", :64 stage.journal | match. Note: :106 also says "up to 3 HubSpot contacts archived at the end", which is the opposite of lead decision 2 (never delete); the audit already says the take scripts are unseen | OK / note |
| REPORT cites (demo/REPORT.md) :695, :622, :29, :32, :84, :21, :38 | full path; contents match each use | match | OK |
| mf_leads.sql | v4 has 5 lines with alert_, v3==v4 byte-identical (cmp), n8n-flows copy has 0, 15 columns vs 11 | match | OK |
| flow counts | 52 files / 655 nodes; 40 older files in 11 folders = 525 nodes; real-v5 4 .json | recount from JSON: 52/655; 130 = 54+54+4+18 | OK |
| 'interval 45 seconds' 3 times in each v5 folder; build default LEASE 120 | | match | OK |
| patches F-003/F-004 | regenerated 10:38 UTC, "+" lines have no 60.1 or 61.9 | mtime 10:38:34; grep of + lines: 0 | OK |
| mf-recovery.json lines 124, 178, 204, 228 | alert columns; DESK_ALERT_TO at 178 | match | OK |
| CUT-LIST per-folder nodes (51,52,53,...,4) | | match the JSON recount | OK |
| CUT-LIST referrers (N8N-START:53, VIDEO-RUNSHEET:8 and :74, PAGE-STATEMENTS-V4:8, N8N-RERUN-1:20 and :127, ORDERS:547,:550,:555, kill-note cross cites, skip-on-conflict:20, kill-between:40, compare:43, RUN-ON-LAPTOP:51,:82,:45, dn1_common:84,:97,:103) | | match | OK |
| FIX-PLAN:15 N8N-START.md 15-27, DESIGN-A-README.md:23 "Execution saving off" | | match | OK |
| FINDINGS F-029 | placeholder lines 103, 177 (178 is toEmail DESK_ALERT_TO), 256-257; the two credential names 16 times | match | OK |
| F-037 | REPORT:695 n8n blocks env; dn1_common.py:16 false; Qualify 2 reads (real-v5), 3 (film-v5) | match | OK |
| F-003/F-007 | RUNSHEET :33 :39 :41 :50 :62 :82 :85 :90, PAGE-STATEMENTS-V4 :120 :150 :153, mf.py :153-164 | match | OK |
| F-013 | stage_server.py :50, :51, :54; PLAN-4 :79, :82 | match | OK |
| saved-runs wording in the seven (other than QUESTIONS:5) | no "deleted at clean-up" as a promise; remaining mentions are tagged SUPERSEDED or are the original question text (QUESTIONS:62, :78) | grep | OK |
| F-001 not a live step | all mentions say DROPPED, archived, CLOSED-DROPPED, or trail | grep | OK |
| QUESTIONS Q20-4, FIX-PLAN:6, REPORT:13 | agree with each other (answered) | read | OK |

## Not checked
- Lane files, FLOWS-AUDIT.md per-node tables, CLAIMS-TABLE, RUNSHEET-WORDING, OWNER-STEPS (other sessions own them; STATUS-BOARD.md:29 and CLAIMS-TABLE/RUNSHEET-WORDING A-007/A-010 deletion wording not judged).
- External repo cites (scripts/run_real_check.py:993, :1101-1107, crm_hubspot.py:492-499, harness.py:26): not in this tree.
- "Live-reference hits" counts in the CUT-LIST table (7, 9, 4 ...), lane ids (L1-1 ...), lane3 numbers (60.1-61.9 s, 144.3 s): raw files absent.
- tools/check_patches.sh: here it printed "SKIP no patches" (this folder is not a git repo), so "PASS 4 patches" is taken from lanes7/evidence-q14-q17.txt only.
- Nothing was run in n8n; no secret scan done.
- Old FINDINGS line cites in reviews/*.md (contra-vs-decisions-r2, citations-new-r4, review-decisions-apply-r1, adversarial-gate-r2): not re-checked; they cite older versions.
