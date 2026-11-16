# evidence-gates-1 (EVIDENCE RUNNER, raw, no judgement)

START HEAD=6262474a167a28fc7309ee41fe6c8d2920d24975 status_lines=1 date=2026-11-16T14:16:02Z

### check_secrets
$ python3 -I tools/check_secrets.py
FAIL 2 hits: flow-check/evidence-f8-r8.md:55 token-like (length 152); flow-check/raw/test-take-check.txt:178 token-like (length 47)
[exit 1]

### check_refs
$ python3 tools/check_refs.py
PASS 5166 references
[exit 0]

### count_findings
$ python3 -I tools/count_findings.py FINDINGS.md
rows 45 unique 45
| Blocker | 5 | 0 | 5 |
| Major | 5 | 0 | 5 |
| Nit | 1 | 34 | 35 |
| all | 11 | 34 | 45 |
sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
[exit 0]

### count_review
$ python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md
rows 28 ['C-1', 'C-2', 'C-3', 'C-4', 'C-5', 'C-6', 'C-7', 'C-8', 'A-1', 'A-2', 'A-3', 'A-4', 'A-5', 'A-6', 'A-7', 'A-8', 'A-9', 'G-1', 'G-2', 'D-1', 'D-2', 'D-3', 'X-1', 'X-2', 'X-3', 'X-4', 'X-5', 'X
severity {'Nit': 11, 'Major': 5, 'Minor': 12}
decision {'DECLINE': 3, 'PROPOSE FIX': 25}
[exit 0]

### claims-count
$ python3 claims-count.py CLAIMS-TABLE.md
verdicts: {'UNSUPPORTED': 27, 'OVERSTATED': 62, 'SUPPORTED': 119, 'UNTRACED': 49, 'RELAYED-ONLY': 70} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 327 unique: 327
[exit 0]

### check_runsheet_paste
$ python3 tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
section '1': 51 rows
section '2': 19 rows
section '3': 71 rows
section '7': 44 rows
total rows: 185
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 86 | with no row here: []
claim ids marked UNTRACED there: 48 | with no row here: 41 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
[exit 0]

### ruff check
$ ruff check .
All checks passed!
[exit 0]

### ruff format --check
$ ruff format --check .
602 files already formatted
[exit 0]

### check_patches.sh
$ bash handover/flows-audit/tools/check_patches.sh
PASS 4 patches
[exit 0]

### clock-block diff
lines TAKE=47 FIX=47
40c40
< | the owner | tells the lead which permissions the HubSpot trial-account key has (one short answer; the key is the secret code that lets our flows write to HubSpot) | asked Wed about 07:00Z (12:30 I
---
> | the owner | tells the lead which permissions the HubSpot trial-account key has (one short answer; the key is the secret code that lets our flows write to HubSpot) | asked Wed about 07:00Z (12:30 I
[exit 1]

### run_all.sh  (exit 2, 0s, lines 1)
REFUSED: another run_all.sh holds the lock for the raw folder /home/user/hadavin-sdk/handover/flows-audit/flow-check/raw; wait for it to end, or use another raw folder (RUN_ALL_RAW is for the nested t

### run_all.sh --strict (exit 2, 0s, lines 1)
REFUSED: another run_all.sh holds the lock for the raw folder /home/user/hadavin-sdk/handover/flows-audit/flow-check/raw; wait for it to end, or use another raw folder (RUN_ALL_RAW is for the nested t

END HEAD=11a9ef4aeb602cb744a5d814e3fbc86607b4f501 status_lines=0

### run_all.sh note
Both run_all.sh runs were REFUSED (exit 2) because another process (pid 7478 'bash run_all.sh', started by another agent, plus nested children) held the lock on flow-check/raw. Not killed, not retried. Not run to completion by this runner.

## Table

command | exit code | last raw line
check_secrets | 1 | FAIL 2 hits: flow-check/evidence-f8-r8.md:55 token-like (length 152); flow-check/raw/test-take-check.txt:178 token-like (length 47)
check_refs | 0 | PASS 5166 references
count_findings | 0 | sev {'Blocker': 5, 'Major': 5, 'Nit': 35}
count_review | 0 | decision {'DECLINE': 3, 'PROPOSE FIX': 25}
claims-count | 0 | ids: 327 unique: 327
check_runsheet_paste | 0 | RESULT: PASS
ruff check | 0 | All checks passed!
ruff format --check | 0 | 602 files already formatted
check_patches.sh | 0 | PASS 4 patches
clock-block diff (block 47 lines) | 1 | > | the owner | tells the lead which permissions the HubSpot trial-account key has (one short answer; the key is the secret code that lets our flows write to HubSpot) | asked Wed about 07:00Z (12:30 IST); reply wanted by 08:00Z (13:30 IST); no reply by 08:30Z (14:00 IST) means no recording that day; the lead decides by Mon 16 Nov 22:00Z (Tue 03:30 IST) whether this Wednesday-only row moves to Tue 05:54Z (11:24 IST); with no decision it stays on Wednesday (QUESTIONS Q31 items 27 and 30) |
run_all.sh  | 2 | REFUSED: another run_all.sh holds the lock for the raw folder /home/user/hadavin-sdk/handover/flows-audit/flow-check/raw; wait for it to end, or use a
run_all.sh --strict | 2 | REFUSED: another run_all.sh holds the lock for the raw folder /home/user/hadavin-sdk/handover/flows-audit/flow-check/raw; wait for it to end, or use a
