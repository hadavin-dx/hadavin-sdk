EVIDENCE RUNNER

Run from /home/user/hadavin-sdk/handover/system-map on 2026-11-16. Raw output below; no judgement.

## Command 1
```
python3 tools/partition.py ../.. /tmp/manifests ; echo rc=$?
```
Exit code of the whole command line: 0
```
{'L1': 148, 'L2': 756, 'L3': 1420, 'L4': 1659, 'L5a': 111, 'L5b': 376} total 4470 of 4470 problems 0
rc=0
```

## Command 2
```
python3 -m unittest discover tests 2>&1 | tail -5
```
Exit code of the whole command line: 0
```
....................
----------------------------------------------------------------------
Ran 21 tests in 0.008s

OK
```

## Command 3
```
python3 tools/scan_outputs.py . ; echo rc=$?
```
Exit code of the whole command line: 0
```
no defects 
count 0
rc=0
```

## Command 4
```
python3 tools/check_citations.py ../.. /tmp/cit-lanes.tsv work/L1.md work/L1c.md work/L2.md work/L2c.md work/L3.md work/L3c.md work/L4.md work/L4c.md work/L5a.md work/L5ac.md work/L5b.md work/L6.md ; echo rc=$?
```
Exit code of the whole command line: 0
```
{'FOUND': 1879} total 1879
rc=0
```

## Command 5
```
python3 tools/check_citations.py ../.. /tmp/cit-out.tsv MASTER-MAP.md SWEEP.md ONE-PLACE-TABLE.md ; echo rc=$?
```
Exit code of the whole command line: 0
```
{'FOUND': 2006} total 2006
rc=0
```

## Command 6
```
cut -f4 /tmp/cit-lanes.tsv | sort | uniq -c ; cut -f4 /tmp/cit-out.tsv | sort | uniq -c
```
Exit code of the whole command line: 0
```
   1879 FOUND
   2006 FOUND
```

## Command 7
```
grep -c '^| ' MASTER-MAP.md ; grep -c '^Owner:' ONE-PLACE-TABLE.md ; grep -n '^## ' SWEEP.md ONE-PLACE-TABLE.md
```
Exit code of the whole command line: 0
```
814
7
SWEEP.md:5:## Findings
SWEEP.md:323:## Fix plan
SWEEP.md:337:## Exceptions
SWEEP.md:353:## Claims check
SWEEP.md:366:## Lessons
SWEEP.md:373:## Counts
ONE-PLACE-TABLE.md:5:## Job: STORE
ONE-PLACE-TABLE.md:24:## Job: LOG
ONE-PLACE-TABLE.md:42:## Job: FILTER
ONE-PLACE-TABLE.md:59:## Job: COUNTER
ONE-PLACE-TABLE.md:73:## Job: RETRY
ONE-PLACE-TABLE.md:90:## Job: NOTICE
ONE-PLACE-TABLE.md:104:## Job: OTHER
ONE-PLACE-TABLE.md:113:## Seed check against DECISION
ONE-PLACE-TABLE.md:124:## Not visible
```

## Command 8
```
git status --short | head -20 ; git diff --stat HEAD~3 -- ../../src ../../tests | tail -3
```
Exit code of the whole command line: 0
```
```

Note on command 8: output was empty (no lines printed by git status or git diff --stat); the exit code shown is that of the final pipe stage.
