# FINDINGS r30 reader A: F-002, F-003, F-007, F-031 (snap-f30 rows 276-279). Non-security; saved condensed; unverified; static. UTC/IST pairs all correct. 0 Blockers, 12 Majors.
1 F-002 T19/T19H/T21 use $WAIT_S, mailbox_count, $FLOWS_PW not in shas.env/need_set; T21 could hang at password prompt.
2 F-002 T21 step 2 NOLOGIN guard does not check SECOND_ADMIN works; add test -n KEY/BEFORE21 and file test, dry run.
3 F-002 closing rule: four tests (T19,T19H,T20,T21) vs three in status move/table line 32.
4 F-002 rating words: Blocker by order vs "audit would rate Major"; "three Blockers" vs five in table.
5 F-003 rating basis stated two opposite ways (evidence cell vs fix cell).
6 F-003 "(1) to (3)" / three outputs vs four blocks F003-1..4.
7 F-003 table summary lists retention and late-alert lines the fix says are SUPERSEDED/must not appear.
8 F-007 rating contradiction (Blocker by rubric vs Major).
9 F-007 "no block uses cd" false (F007-1 uses cd after REPO guard).
10 F-007 table text "not written/LEAD FILLS" vs DETAIL gives it; lane3 mapping blocks nothing.
11 F-007 F007-1 positive control checks the heading not the phrase; overlaps F007-2.
12 F-031 PGSELECT_PW and KEYS31 have no named supplier; list in RUNBOOK inputs.
Not flagged: crowded practice hour; "3 new nodes" for two flows.
