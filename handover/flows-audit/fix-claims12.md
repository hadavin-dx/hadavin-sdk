# fix-claims12 log
Edited CLAIMS-TABLE.md only. Row 54 why-cell: now says PLAN-4:46 names end.flag; OWNER-STEPS step 18 only describes typing end. Row 51 why-cell: dropped AGENT-SCOPE-DO-AND-DONT.md (lines 14-16 never name qualify_stage.py); cites DECISION-one-store.md:9 (names it as writer of stage.journal). Rows 80-84: appended 'Cite not checkable here: desk repo not in this checkout; lead or a desk checkout must confirm.' Quoted replace strings unchanged (pairs check before/after: 136 found, 0 missing).

## raw (pairs, refs, ruff, after edit)
## python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
paste strings in RW: 136 | found word for word in CT: 136
not found in CT: 0
rc=0
## python3 -I tools/check_runsheet_paste.py
usage: python3 -I check_runsheet_paste.py RUNSHEET-WORDING.md [CLAIMS-TABLE.md]
rc=2
## python3 -I tools/check_refs.py
PASS 5166 references
rc=0
## python3 claims-count.py
Traceback (most recent call last):
  File "/home/user/hadavin-sdk/handover/flows-audit/claims-count.py", line 60, in <module>
    v, lane, bad, ids, todo = count(sys.argv[1])
                                    ~~~~~~~~^^^
IndexError: list index out of range
rc=1
## ruff format --check tools claims-count.py
64 files already formatted
rc=0

## raw (paste, claims-count with args)
## python3 -I tools/check_runsheet_paste.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
section '1': 51 rows
section '2': 19 rows
section '3': 71 rows
section '7': 44 rows
total rows: 185
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 86 | with no row here: []
claim ids marked UNTRACED there: 48 | with no row here: 41 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
rc=0
## python3 claims-count.py CLAIMS-TABLE.md
verdicts: {'UNSUPPORTED': 27, 'OVERSTATED': 62, 'SUPPORTED': 119, 'UNTRACED': 49, 'RELAYED-ONLY': 70} total 327
lanes (A, B incl. X): {'A': 97, 'B': 226, 'X': 4}
to-do rows: 87
offenders: 0 []
ids: 327 unique: 327
rc=0
Note: first bare runs of check_runsheet_paste and claims-count showed usage/IndexError because args were missing; rerun with args passed.
