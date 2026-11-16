EVIDENCE RUNNER

## Command 1
$ python3 tools/partition.py ../.. /tmp/manifests ; echo rc=$?
```
{'L1': 148, 'L2': 756, 'L3': 1420, 'L4': 1659, 'L5a': 111, 'L5b': 376} total 4470 of 4470 problems 0
rc=0
```

## Command 2
$ python3 -m unittest discover tests 2>&1 | tail -5  (rc shown is PIPESTATUS[0])
```
....................
----------------------------------------------------------------------
Ran 21 tests in 0.006s

OK
rc(tail)=0 pipestatus=0
```

## Command 3
$ python3 tools/scan_outputs.py . ; echo rc=$?
```
no defects 
count 0
rc=0
```

## Command 4
$ python3 tools/check_citations.py ../.. /tmp/cit-lanes.tsv work/L1.md work/L1c.md work/L2.md work/L2c.md work/L3.md work/L3c.md work/L4.md work/L4c.md work/L5a.md work/L5ac.md work/L5b.md work/L6.md ; echo rc=$?
```
{'FOUND': 1879} total 1879
rc=0
```

## Command 5
$ python3 tools/check_citations.py ../.. /tmp/cit-out.tsv MASTER-MAP.md SWEEP.md ONE-PLACE-TABLE.md ; echo rc=$?
```
{'FOUND': 2010} total 2010
rc=0
```

## Command 6
$ cut -f4 /tmp/cit-lanes.tsv | sort | uniq -c ; cut -f4 /tmp/cit-out.tsv | sort | uniq -c  (output: lanes, ---, out)
```
   1879 FOUND
---
   2010 FOUND
rc=0
```

## Command 7
$ grep -c '^| ' MASTER-MAP.md ; grep -c '^Owner:' ONE-PLACE-TABLE.md ; grep -n '^## ' SWEEP.md ONE-PLACE-TABLE.md ; grep -c 'KEEP-CORE' ONE-PLACE-TABLE.md ; grep -c 'ARCHIVE' ONE-PLACE-TABLE.md  (each followed by its own rc line; counts in order: 814, 7, headings, KEEP-CORE 13, ARCHIVE 20)
```
814
rc=0
7
rc=0
SWEEP.md:11:## How to read this file
SWEEP.md:23:## Findings
SWEEP.md:344:## Fix plan
SWEEP.md:372:## Exceptions
SWEEP.md:392:## Claims check
SWEEP.md:412:## Lessons
SWEEP.md:419:## Counts
ONE-PLACE-TABLE.md:5:## How to read this file
ONE-PLACE-TABLE.md:17:## Job: STORE
ONE-PLACE-TABLE.md:35:## Job: LOG
ONE-PLACE-TABLE.md:51:## Job: FILTER
ONE-PLACE-TABLE.md:67:## Job: COUNTER
ONE-PLACE-TABLE.md:86:## Job: RETRY
ONE-PLACE-TABLE.md:101:## Job: NOTICE
ONE-PLACE-TABLE.md:116:## Job: OTHER
ONE-PLACE-TABLE.md:124:## Appendix: build-process rows (not places of a take job)
ONE-PLACE-TABLE.md:139:## Seed check against DECISION
ONE-PLACE-TABLE.md:150:## Not visible
rc=0
13
rc=0
20
rc=0
```

## Command 8
$ git status --short | head -20 ; git diff --stat HEAD~3 -- ../../src ../../tests | tail -3  (both printed nothing, rc=0 each)
```
rc=0
rc=0
```
