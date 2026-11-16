# E3 cite check (raw; no judgement on whether quotes match)
Script: /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/r2-e3e4.py. Read from a pristine copy (work-new-pristine, same as new/) because work-new has patches applied and patched files shift line numbers.
FINDINGS.md has NO section titled top-10 / top ten (grep found none). I used the 16 rows rated Blocker or Major in the table: F-001 F-002 F-003 F-004 F-005 F-006 F-007 F-008 F-011 F-023 F-029 F-031 F-037 F-041 F-042 
Citations are taken from the 'where' column of each row, plus any other path:line in the same row. A bare file name with no folder is resolved by a unique-suffix search in the tree; when several files share the name the first is used and the line says 'first of N matches' (ambiguous, so treat as unresolved).
Rows in TSV: 49. ABSENT-IN-TREE rows: 18. Line out of range rows: 2.

## ABSENT-IN-TREE (finding, path, line)
F-002 PLAN-4-NLITE-FROM-LEAD.md 47
F-002 PLAN-4-NLITE-FROM-LEAD.md 77
F-002 PLAN-4-NLITE-FROM-LEAD.md 94
F-002 dn1_common.py 124-132
F-003 VIDEO-RUNSHEET.md 85
F-003 handover/demo/VIDEO-RUNSHEET.md 33
F-005 handover/demo/VIDEO-RUNSHEET.md 35
F-005 n8n-tests/smtp_catcher.py 40
F-006 handover/demo/VIDEO-RUNSHEET.md 4
F-007 handover/demo/VIDEO-RUNSHEET.md 24
F-023 DOUBTFUL-SCENE.md 13
F-023 VIDEO-RUNSHEET.md 39
F-023 n8n-table-screen-v2/README.md 3
F-023 n8n-table-screen/README.md 3
F-037 dn1_common.py 16
F-041 PLAN-4-NLITE-FROM-LEAD.md 106
F-042 RUN-ON-LAPTOP.md 58
F-042 VIDEO-RUNSHEET.md 38

## line out of range
F-037	REPORT.md	695	no (file has 114 lines)
F-041	REPORT.md	622	no (file has 114 lines)

## ambiguous basename resolutions
F-029	mf-recovery.json	yes (handover/demo/n8n-flows-film-v5/mf-recovery.json (first of 4 matches))
F-029	mf-sub-crm-mail.json	yes (handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json (first of 3 matches))
F-029	mf-form.json	yes (handover/demo/n8n-flows-film-v5/mf-form.json (first of 4 matches))
F-029	mf-hook.json	yes (handover/demo/n8n-flows-film-v5/mf-hook.json (first of 4 matches))
F-037	mf-sub-crm-mail.json	yes (handover/demo/n8n-flows-film-v5/mf-sub-crm-mail.json (first of 3 matches))
F-037	mf-recovery.json	yes (handover/demo/n8n-flows-film-v5/mf-recovery.json (first of 4 matches))

Note: absent files are outside this snapshot (only handover/demo and handover/flows-audit are in it); e.g. VIDEO-RUNSHEET.md, PLAN-4-NLITE-FROM-LEAD.md, n8n-tests/, dn1_common.py.
