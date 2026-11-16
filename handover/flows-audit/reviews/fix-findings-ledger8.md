# fix-findings-ledger8 (2026-11-16), fixer for reviews/findings-ledger-reader-r7.md items 1 to 9 plus 3 items from the coordinator

NOT VERIFIED: nothing ran in n8n, Postgres or HubSpot; the reviewer words were re-read against the cells but cites in other files were checked only by grep and line reads; QUESTIONS.md was not edited (another fixer), so line numbers I cite there can move; ruff format --check on the whole repository reports 93 files to reformat (not caused by these two markdown files; check_flows.py:342 is the known one); egm steps not run (text edit of audit files, EGM skipped: wording fixes under the lead's brief).

Reviewer items, each re-read:
1 HOLDS. F-003 pass needs the re-read, dated Wed 06:00Z, after the Tue 14:00Z GO test. Added to the F-003 fix cell (TUESDAY AND THE WEDNESDAY DATE) and the applier is now "NOT NAMED: lead decides".
2 HOLDS. F-018 had 07:00Z for the T19 wait, probe and menu path; now 05:45Z (F-002 and WEDNESDAY CLOCK). Source conflict written once in WEDNESDAY CLOCK and pointed to from F-018: Q31 item 50 says item 25 governs the wait value (Tue 06:00Z) and asks 05:45Z only for the count command; item 54 gives 05:45Z for the HubSpot search method.
3 HOLDS. New top paragraph in FINDINGS.md: Tuesday 14:00Z is NO-GO under unanswered defaults, with the causing rows (F-018, F-037, F-008, F-029, F-011, F-041, F-003 as proposal) and the non-causing rows. LEDGER-ROWS header points to it.
4 HOLDS. Runners now "NOT NAMED: lead decides" at F-037 grep, F-031 part 2, F-007 lane3 mapping, F-011 fix A slot, F-003 applier, F-018 reader (owner at the screen or studio lead).
5 HOLDS for "owner": F-001 "owner: the lead" became "runner: the studio lead" (both files). The F-001 Nit-stops-take point was already in the F-001 fix cell; also in the new top paragraph.
6 HOLDS. F-037 "If open at the take" now says the failure happens only with a copy that still has $env (the filled route has 0), as its evidence says.
7 HOLDS. F-006 fix cell now says the F-003 patch was regenerated 2026-11-16 (patches/REGENERATED-NOTE.md; patch line 7 "real-v5, scenes 1 to 4").
8 HOLDS. 14 terms added to the words list with file and first words of the entry (TAG GO has no definition line; grep finds only uses, and the cell says so).
9 HOLDS. 5 grep lines = 1 comment line (mf_leads.sql line 16) + 4 column lines 17 to 20 (grep -n run now: 5 lines). "was Major (to Nit)" reworded. N=10 s ordering: written as a conflict, lead decides, with the audit proposal.
Coordinator: (1) F-041 stray pipe was `-E 'one database|single database'` in the fix cell; reworded without a pipe in both files; cell counts of all 45 rows re-checked (FINDINGS 10, LEDGER 9 when split on " | "). (2) NOT COVERED 15 now has next steps and who, and names exception 2(b) for client numbers; whether the studio lead runs M1 on real-v5 is marked UNANSWERED. (3) FINDINGS line 95 now says 8 numbered items plus 8b = 9 steps, F-041 in 8b.

Checks run: python3 -I tools/count_findings.py (45 rows, 5/5/35, BEFORE 11); check_refs PASS 5176; check_names PASS 655; check_secrets PASS 0 hits; a script compared all 45 fix cells, severities and status first words between the two files: 0 differences. No rating, status or count changed.
