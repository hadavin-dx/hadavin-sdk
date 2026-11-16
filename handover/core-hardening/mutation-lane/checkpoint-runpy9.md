# checkpoint runpy9 start 13:46 UTC; r7 backed up
13:57 dev2 started: new blocks + changed blocks
14:01 dev2 on r8: 0 failed (53 root-run, 47 nonroot child). Now new tests on r7 code
14:05 new tests on r7 code: 33 of 61 fail (evidence-r8/new-tests-on-r7code.txt). r8 final edits (ruff fmt, RESTORE_ERRORS) done; next: ONE full run on final files
14:05 FINAL full run started on run.py 39059b7c5a1d; no edits until it ends
14:09 first full run aborted by me at T43: 5 older checks (T23a T23b T32b T39 T43c) still expected r7 exit codes; updated them to the r8 M1/N2 semantics (exit 3 / unsettled). Second FINAL full run starts now; no edits until it ends
