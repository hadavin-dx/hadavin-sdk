# PR89 round 13, slice tests/test_mutation_runner_keywords.py (egm-codebase-details, fresh), head 0cd10b99f3c5
Coverage: test file 2,008 / 2,008; runner 1,101 / 1,101; DIFF hunks of three sibling test files read; all 84 minus-lines grepped. No code run.
Verdict: no confirmed Blocker; 4 Major, 6 Nit. The file is NEW in the diff against main, so the 47 deleted tests cannot be judged from DIFF.patch: needs the deletion table or a diff against b855a8f. Findings 1 and 2 become Blockers if deleted tests covered them.
F1 (Major, tests 1113/1156/1167/1197; runner 898, 901): COLLECTION ERROR and FIXTURE ERROR messages have no secret-bearing test; deleting either _masked() call fails nothing. Input: module-level or fixture `assert go(True) is True, os.environ[DSN var]`.
F2 (Major, tests 733-755; runner 1078-1084): canary-skip message never tested with a secret; dropping `secrets` at runner line 1080 fails nothing. Input: parametrized test with id [<dsn>] that skips when the state file exists.
F3 (Major, test 398): baseline-skip test asserts only absence, no "[REDACTED]" check and no positive control; passes if the id stops carrying the DSN.
F4 (Major, rule: fake credentials built from parts): whole literals at 1301, 1307, 1482, 1793, 1637, 1671-1672, 1527, 1839, 1846, 1853, 1857, 1866, 1911, 1917, 523, 1694-1710. Build each from parts as _secret_dsn does.
F5 (Nit): percent forms %C2%80, %00, %0A not sampled; key=value form never reaches the "password in it" branch.
F6 (Nit, 1836-1848): pins that 2-character pieces (Zz, Qw) are NOT masked; state it in a comment or the test passes any regression.
F7 (Nit, 583): partial assertion ("glacier", "north-"); compare the exact string.
F8 (Nit): no test at MAX_FRAGMENT_HITS + 1.
F9 (Nit): 4-character secret next to "..." not tested through a real run.
F10 (Nit): timing bounds loose and paired with exact checks; 3,000,000-character case may take seconds on a loaded runner.
Sound: positive controls (495, 1726), seeded property test (1757), refusal tests print only parts, substring secrets (583, 1807, 1858), %40/%20/%2F/plus/DEL covered, overlapping "....".
