# Citation check r2 summary (agent ae32698a), saved by flows-audit; full table in citation-check-findings-r2.md; checker words unverified
94 MATCH, 4 MISMATCH, 5 NOT CHECKABLE of 103 claims (rows F-002, F-003, F-007, F-008, F-011, F-018, F-029, F-031, F-037, F-041).
MISMATCH 1 F-002: "TAKE-CHECKLIST.md line 295" for mailbox count -> actual line 310 (295 is ")").
MISMATCH 2 F-002 (4): "FIX-PLAN item 3 steps 9 and 10" for apply F-002/F-008 and rebuild real-v5 -> actual Step 1 (apply) and Step 2 (regenerate into NEW folder); step 9 = export back and compare, step 10 = T19/T20/T21; "step 9 for $EXPORT" correct.
MISMATCH 3 F-003: "60.1 to 61.9 s" and 18-run number said relayed in V7-NUMBERS-lead-read.md; file has neither (v3 lease-20 numbers); figures at demo/REPORT.md:44 and demo/VIDEO-RUNSHEET.md:90.
MISMATCH 4 F-041: Parts A/B print "GUARD OK: both viewer files found" / "GUARD OK: folders found, log path is new" but Block R7 (TAKE-CHECKLIST 337-348) has no such lines (Part B prints only "log path is new"); "GUARD OK" appears only in FINDINGS/LEDGER.
Minor: F-007 prose "over handover/demo/*.md" but command is recursive (non-recursive glob would show 2 lines not 4).
NOT CHECKABLE: F-002 n8n default 500 never observed (row says UNVERIFIED); F-002 claim about F-046; F-008 old 8-line pass line; F-011 n8n starts on SQLite (UNVERIFIED); F-029 scripts\n8n_api.py absent (searched only under handover/). None cites b4cce5b.
HELD: 211 HH:MMZ (IST) pairs correct; weekday/date pairs correct; 269-minute chain sums; source cites build_mainframe.py, PLAN-4, REPORT.md, Q31 items, placeholder counts, mf-recovery.json 177/178 match; F-003/F-004 patch effects checked in scratch copy.
