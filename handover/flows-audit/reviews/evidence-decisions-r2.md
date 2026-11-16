## 1. FINDINGS vs LEDGER-ROWS
CURRENT FINDINGS ids 45 (dup ids: [] ) LEDGER ids 45 (dup: [] )
 only in FINDINGS: []  only in LEDGER: []
 FINDINGS counts {'Blocker': 8, 'Major': 8, 'Nit': 29}  LEDGER counts {'Blocker': 8, 'Major': 8, 'Nit': 29}
 severity mismatches (normalised first word group): []
 raw (unnormalised) severity text differences: []
BASE 12e709462^ FINDINGS ids 45 (dup ids: [] ) LEDGER ids 45 (dup: [] )
 only in FINDINGS: []  only in LEDGER: []
 FINDINGS counts {'Blocker': 8, 'Major': 8, 'Nit': 29}  LEDGER counts {'Blocker': 8, 'Major': 8, 'Nit': 29}
 severity mismatches (normalised first word group): []
 raw (unnormalised) severity text differences: []

## 2. 'when' column BEFORE/AFTER
BASE 12e709462^ 45 {'BEFORE': 17, 'AFTER': 28}
AFTER 12e709462 45 {'BEFORE': 17, 'AFTER': 28}
CURRENT 45 {'BEFORE': 17, 'AFTER': 28}
changed when values base->current: {'F-011': ('BEFORE 8 (only if the video says one database, else dated exception)', "BEFORE 8 as rated now (counted in the 17); the video does not say 'one database' (Q4 answer), so the fix is not done before the video, and the lead may move this row AFTER as a Nit (counts then 8/6/31, BEFORE 15) (lead decision 2026-11-16 item 10)"), 'F-041': ('BEFORE 8', "BEFORE 8 as rated now (the video does not say 'one database', Q4 answer; the lead may move this row AFTER as a Nit)")}
  stated FINDINGS.md:71: ['BEFORE 17', 'AFTER 28', 'BEFORE 15', 'AFTER 30']
  stated FIX-PLAN.md:22: ['BEFORE 17', 'AFTER 28']
  stated LEDGER-ROWS.md:1: ['BEFORE 17', 'AFTER 28']
  stated QUESTIONS.md:23: ['BEFORE 17', 'AFTER 28']

## 3. phrase occurrences
'scenes 5 to 11': marked 10, UNMARKED 0
'60.1': marked 13, UNMARKED 0
'61.9': marked 15, UNMARKED 1
    SCENE-FLOW-MAP.md:40
'flow-set switch': marked 8, UNMARKED 0
'film-v5': marked 51, UNMARKED 25
    FINDINGS.md:95, FINDINGS.md:109, CUT-LIST.md:8, CUT-LIST.md:14, F6B-AUDIT.md:39, F6B-AUDIT.md:62, F6B-AUDIT.md:81, F6B-AUDIT.md:91, F6-AUDIT.md:28, F6-AUDIT.md:40, F6-AUDIT.md:49, REPORT.md:63, PLAN-002.md:21, PLAN-002.md:25, PLAN-002.md:71(x2), PLAN-002.md:75, SCENE-FLOW-MAP.md:8, SCENE-FLOW-MAP.md:13, SCENE-FLOW-MAP.md:16, SCENE-FLOW-MAP.md:25, SCENE-FLOW-MAP.md:27(x3), SCENE-FLOW-MAP.md:33
'one database': marked 11, UNMARKED 9
    FINDINGS.md:10, FINDINGS.md:101(x2), FIX-PLAN.md:11(x2), QUESTIONS.md:4, QUESTIONS.md:10(x2), QUESTIONS.md:18
'8 files': marked 4, UNMARKED 0
'8 flows': marked 0, UNMARKED 0
'approval': marked 7, UNMARKED 11
    FINDINGS.md:49(x2), FINDINGS.md:65, FINDINGS.md:102(x5), QUESTIONS.md:11(x2), F6B-AUDIT.md:83
'audit trail': marked 4, UNMARKED 8
    FINDINGS.md:49(x2), FINDINGS.md:103(x3), LEDGER-ROWS.md:18, QUESTIONS.md:11(x2)

## 4. Q refs
Q14 heading in QUESTIONS.md: True ## Q14 (flows-audit, 2026-11-16 10:40 UTC): re-rate the rows
  cited at 17 : FINDINGS.md:71, FINDINGS.md:80, FINDINGS.md:90, FINDINGS.md:91, FINDINGS.md:99, FIX-PLAN.md:3, FIX-PLAN.md:22, LEDGER-ROWS.md:1, LEDGER-ROWS.md:5, QUESTIONS.md:23, QUESTIONS.md:40, F6B-AUDIT.md:41, F6B-AUDIT.md:81, F6B-AUDIT.md:93, REPORT.md:9, SCENE-FLOW-MAP.md:40, SCENE-FLOW-MAP.md:68
Q15 heading in QUESTIONS.md: True ## Q15 ANSWERED by the lead 10:31Z (no closing card with num
  cited at 1 : QUESTIONS.md:43
Q16 heading in QUESTIONS.md: True ## Q16 (flows-audit, 2026-11-16 10:55 UTC): which table defi
  cited at 1 : QUESTIONS.md:46

## 5b. secret-like

## 5a. git diff --stat (base = 12e709462^ = 082d2e5af, the commit before the decisions pass)
commits touching FINDINGS.md: 163e16b7a patch evidence, Q15;12e709462 claims r6, decisions applied (56 edits), F3 r6, F8 r4 wip;628b1235a flows-audit: ORDER 007 round 2 fixes, drift report, REPORT;664e6279c board 2026-11-16T08:41:36Z;43c255058 flows-audit: ORDER 007 review round 1 resolved, ORDER 012 applied;823830b69 board 2026-11-16T08:34:34Z;f28fa6d17 board 2026-11-16T08:29:14Z;35235ace2 flows-audit: ORDER 004 applied (Reading A): F-011 full size, patch F-008 saves runs for the take;
-- base..HEAD:
 handover/flows-audit/CUT-LIST.md       |  2 +-
 handover/flows-audit/EXCEPTIONS.md     |  8 +++----
 handover/flows-audit/F6-AUDIT.md       |  2 +-
 handover/flows-audit/F6B-AUDIT.md      | 34 +++++++++++++-------------
 handover/flows-audit/FINDINGS.md       | 44 +++++++++++++++++-----------------
 handover/flows-audit/FIX-PLAN.md       | 12 +++++-----
 handover/flows-audit/LEDGER-ROWS.md    | 12 +++++-----
 handover/flows-audit/PLAN-002.md       |  4 ++--
 handover/flows-audit/QUESTIONS.md      | 21 +++++++++++-----
 handover/flows-audit/QUEUE.md          |  8 +++----
 handover/flows-audit/REPORT.md         |  6 ++---
 handover/flows-audit/SCENE-FLOW-MAP.md | 36 ++++++++++++++--------------
 12 files changed, 99 insertions(+), 90 deletions(-)
-- 12e709462 alone (the pass commit):
 handover/flows-audit/CUT-LIST.md       |  2 +-
 handover/flows-audit/EXCEPTIONS.md     |  6 +++---
 handover/flows-audit/F6-AUDIT.md       |  2 +-
 handover/flows-audit/F6B-AUDIT.md      | 14 +++++++-------
 handover/flows-audit/FINDINGS.md       | 28 ++++++++++++++--------------
 handover/flows-audit/FIX-PLAN.md       |  6 +++---
 handover/flows-audit/LEDGER-ROWS.md    |  6 +++---
 handover/flows-audit/PLAN-002.md       |  4 ++--
 handover/flows-audit/QUESTIONS.md      |  8 ++++----
 handover/flows-audit/QUEUE.md          |  4 ++--
 handover/flows-audit/REPORT.md         |  2 +-
 handover/flows-audit/SCENE-FLOW-MAP.md | 28 ++++++++++++++--------------
 12 files changed, 55 insertions(+), 55 deletions(-)
-- working tree vs HEAD for the 12 files:
(empty = no uncommitted changes)

-- SCENE-FLOW-MAP.md:40 context (unmarked 61.9), 200 chars:
heck is the timer "Every30s" in mf-recovery | The only 45 s recovery figure (K1, median 60.8 s, max 61.9 s) was measured on older film-v4 flows with a stand-in CRM, relayed, not seen here | Caption: "Abou
sks the lead whether this caption keeps the K1 numbers and recommends cutting them with the 60.1 to 61.9 s number, so the caption is HELD until the lead answers (lead decision 2026-11-16 item 1) | CHECKED

## 5c. secret grep result: no lines printed above under 5b = no match for AKIA|ghp_|xox|password=|@gmail in the 12 files (own script and grep -c below)
handover/flows-audit/FINDINGS.md:0
handover/flows-audit/FIX-PLAN.md:0
handover/flows-audit/CUT-LIST.md:0
handover/flows-audit/EXCEPTIONS.md:0
handover/flows-audit/LEDGER-ROWS.md:0
handover/flows-audit/QUESTIONS.md:0
handover/flows-audit/F6B-AUDIT.md:0
handover/flows-audit/F6-AUDIT.md:0
handover/flows-audit/REPORT.md:0
handover/flows-audit/QUEUE.md:0
handover/flows-audit/PLAN-002.md:0
handover/flows-audit/SCENE-FLOW-MAP.md:0
