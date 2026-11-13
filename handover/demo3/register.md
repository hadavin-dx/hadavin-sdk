# Register (id | purpose | started UTC / IST | expected end | last checked | state | next action)
A | agent aebdbd..: full product suite, PR#12 8d65577 and main 61ded9e, 2 runs each (~16 min/run) | 09:39Z / 15:09 | ~10:45Z / 16:15 | 09:39Z | running | check 09:50Z
B | agent a2dce4..: hostile-input pass | 09:39Z / 15:09 | done 09:49Z | 09:52Z | reported, closed | none |
C | agent ae1559..: hang hunt | 09:53 Z | ~11:00Z | 09:53 Z | running | check progress-C.txt

A | stopped by container restart after 4 runs ended | - | - | 10:25Z | stopped | none
C2 | agent a107e0..: hang hunt d2 + c | 10:25Z / 15:55 | ~10:58Z | 10:25Z | running | check 10:35Z
D | agent a22cfb..: ORDER 3 suite twice on d5b4451 + F7 rerun | 10:25Z / 15:55 | ~11:05Z | 10:25Z | running | check 10:35Z
L | my shell: tests/test_real_check_dry.py alone on main, timeout 600, started 10:30Z | running | check 10:36Z
R1 | my rescue copy loops for orphaned logs of pids 652 (D run1) and 1351 (C2 full), 15 s, max 100 rounds | 10:40Z | ends when the pytest ends | running | check rescue.log
E | agent ab117a..: edadd00 full suite once + F7/C1/bytes | 10:42Z | ~11:05Z | 10:47Z | running | check 10:55Z
D | reported 10:57Z, closed (run 1 only, exit 0; suite-pr14.md corrected) | closed
C2 | reported 11:02Z, closed: no hang, no failure; c2 full main 3407 passed 198 skipped 0 failed exit 0 1067 s | closed
E | reported 11:05Z, closed: edadd00 3681 passed 0 failed 200 skipped exit 0 1215 s | closed
