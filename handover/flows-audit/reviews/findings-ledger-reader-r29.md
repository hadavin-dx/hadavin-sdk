# FINDINGS/LEDGER round 29 stranger read (agent a0fdd001, egm-comprehension), Blockers/Majors only, non-security (beyond round 2)
Saved by flows-audit, condensed. Reviewer words unverified; static. Read only the ten rows (FINDINGS 276-285) and ledger F-002 in full. NOT read: FINDINGS other parts, other nine ledger fix cells, QUESTIONS, ORDERS, RUNBOOK, TAKE-CHECKLIST, patches, flows. Severity and status agree FINDINGS vs LEDGER on ten rows (OPEN); UTC/IST pairs correct. 2 Blockers, 11 Majors.
B1 F-041: typed commands are a practice copy of Block R7 (2 phrases vs 6); real PASS needs an allowed-places list that does not exist, "JUDGED row 7" and a fresh review agent. Fix: paste Block R7 as the only block; PASS/FAIL printout; define "egm", "N7-7".
B2 F-002 T21: $KEY never set; step 2 sets NOLOGIN before step 4 can fail; step 1 count never compared. Fix: KEY="L$(openssl rand -hex 8)"; test -n "$KEY" as step 0; compare counts at step 6.
M1 F-002 patch-apply command unguarded (empty $REPO). Fix: need_set REPO && test -d "$REPO/handover/demo" && prefix.
M2 F-002 T21 step 2 psql command unguarded. M3 F-002 hook leg (KEYH, /webhook/mf-hook) untested, no pass condition.
M4 F-031 rating wording Major vs Nit; FIXED-VERIFIED overclaims when flaw remains; KEYS31 not in need_set.
M5 F-037 status "(new, ORDER 007)" contradicts rating basis; Blocker though take risk conditional; "all three listings" vs four PASS lines; "ls lists the 4 take files" contradicts "no ls" (F-029 same).
M6 F-003 status/rating basis inconsistent; unpublished run sheet stretches rubric; re-read greps print no PASS/FAIL.
M7 F-011/F-041 absence-check controls do not test the pattern; owner-sheet absence check has no command; F-011 cd unguarded; downgrade rests on a fresh review agent as "person".
M8 F-041 title "one database in 15 ways" overclaims (15 table rows, conflicts not counted).
M9 F-018 rating basis contradictory; Tuesday pass unreachable (Q31 item 31 resolves); awk alert-recipient match lacks a positive control.
M10 F-008/F-029 PASS depends on unchecked layout assumptions (exact JSON spacing, four mf-*.json names, SUB_WORKFLOW_ID absent pre-import). Fix: state which assumption is checked.
M11 Each row is one 6,000-12,000-word cell; terms defined elsewhere (READ-FIRST, TAG GO, Row 4, JUDGED, egm). Fix: short top block per row.
