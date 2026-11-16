# fix-tcfp4 (TAKE-CHECKLIST and FIX-PLAN, readiness r3 findings M1-M6 and Minors)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-tcfp4/
- M1: one "Placeholder table" in TAKE-CHECKLIST (REPO, BRANCH, SHA_R20-23, FLOWS = REPO/handover/demo/<new folder>, EXPORT, LOG, LOG2, EVLOG, REPORT, LEDGER_OUT, GREPOUT, PGCONN, PGCONN_SELECT_ONLY, KEY, ADDR, TAKE_TREE, TAKE_FOLDER, RUNSHEET); inline LOG= assignments removed; FIX-PLAN points to the table.
- M2: Inputs 1-17 each cite their ORDERS line or say "no line"; rows 3, 6, 7 and checks 2, 5b, 9, 11 cite too; FIX-PLAN header maps its LEAD FILLS to Inputs items.
- M3: "Honest limit" paragraph above the Tuesday table: GO on rows 2, 3, 5, 6, 7 is judgement until filled before 14:00Z (19:30 IST).
- M4: S9-2/S9-3 cites corrected (QUESTIONS.md lines 116, 322, 330, 350 as read now; search by words). 
- M5: cd "$REPO" && added: check 1, 7, 13, FIX-PLAN steps 5 and items 5, 7.
- M6: one F-007 grep scope (handover/demo, *.md); allowed-hit list written as "audit proposal, lead to confirm"; F-041 allowed places proposal in row 7.
- Minors: 30 min gap explained as inference; IST added (Inputs heading, checks 12, 13, re-smoke line); ORDER 035 named at line 173.
Commands (cwd handover/flows-audit): check_secrets exit 0 (PASS 0 hits in 1767 files); check_refs exit 0 (PASS 5146 references); ruff check exit 0.
Not checked: commands were not run; EGM result review is the lead's step. Nothing committed.
