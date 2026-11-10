# Mutant recount at head d392200 (tools/p6a1_mutants.py, throw-away worktree of HEAD, cloud variables removed)

Result line: TOTAL mutants 63  planted 63  KILLED 63 (named 63, no named killer 0, killed by another test 0)  SURVIVED 0  other problems 0  (89s). Baseline (unmutated) PASS: 270 passed. Raw: mutants-repo-tool-63.txt.

Origin of the 63: ids 1-35 and 46-51 = 41 re-fitted to the current code (original list not kept); ids 52-55 = 4 written from one-line descriptions; ids 56-73 = 18 written later (56-72 = 17, plus 73). Ids 36-45 are reserved for the second pull request. 41 + 4 + 18 = 63. So 63 of 63 does not prove the original 62 were killed.
Ids 56-73 now each name a killer; 57 and 73 are also killed by the new exact-list row. The baseline covers the files named by 61 and 62.
The earlier by-hand script is a different script: its id 33 and id 57 were NOT-LOCATED; the repo tool's 33 and 57 are located and killed.
Full suite at this head (Python 3.13, cloud variables removed, Postgres not available so its tests skip): 10089 passed, 455 skipped, exit=0 (full-suite.txt). Python 3.12 not run in this round.
