# Result review round 2: resolve report (egm:egm-resolve, run by the lead)
Status: resolved (fixes applied; lead re-ran check_counts, check_names, check_refs, check_secrets and check_patches after the edits: all PASS)
Inputs: reviews/result-r2-design.md (D2-1 to D2-12), reviews/result-r2-codebase.md (C2-1 to C2-11), evidence-2.md. Mode: automatic (lead instruction), no questions asked.
Totals: accepted fix groups 19, contested 0, escalated 1, declined 1. Two pairs are the same finding (D2-1 = C2-5, D2-3 = C2-3).

| Finding | Category | Judgement on evidence | Edit made |
|---|---|---|---|
| D2-1 / C2-5 (Major) caption pools 4 kill points, omits stand-in flows | PROPOSE FIX | Valid: PAGE-STATEMENTS-V4.md:148-161 give K1 5 runs, median 60.8 s, max 61.9 s and say K3B and K3 end unknown; the film flows use the real CRM node. | patches/F-003: scene 4 caption, closing card line 3, number cell, lease and recovery bullets, risk 2, open question 5 now use K1 only and name film-v4 stand-in flows. |
| D2-2 (Major) statement 14 vs 17, "Total: 18" | PROPOSE FIX | Valid: :105 says 144.3 s n=1; :134-149 hold 20 statements. | patches/F-004 regenerated (1 merged hunk): 120 s part reads "144.3 s in one run (n=1; a second relayed line gives 144.2 to 144.4 s, n not stated)"; "Total: 20 statements". |
| D2-3 / C2-3 (Major) dn1_common.py cannot be archived | PROPOSE FIX | Valid: mf.py:8, RUN-ON-LAPTOP.md:45, PLAN-4:47. | CUT-LIST: dn1_common.py stays, new steps 3a/3b; F-034 now fixed by a path guard, not by archiving; FIX-PLAN step 9. |
| D2-4 (Major) F-013 proposes what the stand-in already does | PROPOSE FIX | Valid: stage_server.py:50-51 read by the lead. | F-013 reworded as a design trade-off, the fix dropped, real stage service stays UNVERIFIED. |
| D2-5 (Major, argues Blocker) F-002 empty key | PROPOSE FIX | Valid: build_mainframe.py:82-84; a resend cannot help; the stage key check is reached only after Claim. Severity is changed by the lead on the reviewer's evidence (the rubric says a lost lead is a Blocker); whether n8n passes an empty string or null stays UNVERIFIED. | F-002 is now Blocker, 500 half kept as described, PLAN-4:47 and :77 cited. |
| D2-6 (a)(c)(b) notes | PROPOSE FIX (b), no change (a)(c) | (c) answered by evidence-2 (m): 3 new nodes, no dangling edge. (b) trim: real. | F-002 row notes the trim. |
| D2-6 (d) / C2-11 layout x=550 | DECLINE | Cosmetic canvas position, no behaviour. | none |
| D2-7 (Major) one-store reading | ESCALATE | The decision text is outside what the reviewer could read (the lead's wording); both readings are supported by N8N-START.md:4 and REPORT.md:622. | F-011 states both readings; QUESTIONS.md Q2 asks the lead; EXCEPTIONS.md row updated; F-019 and EXCEPTIONS.md now classify the spend ledger the same way (proposed exception). |
| D2-8 (Major) F-008 vs log decision | PROPOSE FIX | Valid: saveData none in all 8 files (build_mainframe.py:44). | F-008 evidence extended (execution list empty, scene 1 and risk 3, patch F-003 does not touch scene 1). |
| D2-9 (Nit) F-001 patch comment | PROPOSE FIX | Valid (build_mainframe.py:104-106). | patches/F-001 comment uses the v5 backoff wording; v2 note says "until archived". |
| D2-10 (Nit) F-015, F-016, F-024 severity | PROPOSE FIX | Reviewer is right by the rubric (Nit = leftovers; behaviour identical, V5-README calls F-016 a known small effect, F-024 risk only if an old folder is loaded). | The three rows are Nit; counts line, ledger rows, row order updated: 34 = 2 Blocker, 23 Major, 9 Nit. |
| D2-11 (Nit) backoff wording | PROPOSE FIX | Valid. | F-014 says "capped at 5 x 60 s". |
| D2-12 (Nit) "nothing uses" | PROPOSE FIX | Valid (F-026 shows documents mention old folders). | Short answer item 1: "no script or flow uses". |
| C2-1 (Major) docker-native-pg-shim.py | PROPOSE FIX | Valid: RUN-ON-LAPTOP.md:51. | CUT-LIST: only after that line is changed (step 3b). |
| C2-2 (Major) draft and audit documents still referenced | PROPOSE FIX | Valid (referrers verified by the reviewer by line). | CUT-LIST lists each referrer; documents move only with their referrers or after the citation is updated. |
| C2-4 (Nit) notes, rerun copies, scratch logs referenced | PROPOSE FIX | Valid. | Same CUT-LIST block. |
| C2-6 (Nit) F-003 coverage | PROPOSE FIX | Valid. | F-003 row names the two lines it leaves (VIDEO-RUNSHEET.md:85 and :90, the latter fixed by F-007). |
| C2-7 (Nit) L3-claims S9 cite | PROPOSE FIX | Valid. | :6 changed to :16. |
| C2-8 (Nit) F-020 cites | PROPOSE FIX | Valid. | PLAN-4:64 and mf.py:12; reason cited at PLAN-4:78. |
| C2-9 (Nit) F-014 not Blocker | PROPOSE FIX | Valid. | One sentence on why Major. |
| C2-10 (Nit) FINDINGS header | PROPOSE FIX | Valid. | Header says 28 merged plus 6 added (34). |

Not done by me, said plainly: no rerun of the n8n runtime (impossible here), no new round 3 (cap of 2 result rounds; mail and security paths are uncapped, and D2-5 touches intake, so the lead may order a round 3 on F-002 only).
