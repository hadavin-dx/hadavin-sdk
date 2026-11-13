# Register (id | purpose | started UTC / IST | expected end | last checked | state | next action)
A | agent aebdbd..: full product suite, PR#12 8d65577 and main 61ded9e, 2 runs each (~16 min/run) | 09:39Z / 15:09 | ~10:45Z / 16:15 | 09:39Z | running | check 09:50Z
B | agent a2dce4..: hostile-input pass | 09:39Z / 15:09 | done 09:49Z | 09:52Z | reported, closed | none |
C | agent ae1559..: hang hunt | 09:53 Z | ~11:00Z | 09:53 Z | running | check progress-C.txt
D | NOT STARTED (ORDER 3) | waits for A | - | - | waiting | start on A report
A | stopped by container restart after 4 runs ended | - | - | 10:25Z | stopped | none
C2 | agent a107e0..: hang hunt d2 + c | 10:25Z / 15:55 | ~10:58Z | 10:25Z | running | check 10:35Z
D | agent a22cfb..: ORDER 3 suite twice on d5b4451 + F7 rerun | 10:25Z / 15:55 | ~11:05Z | 10:25Z | running | check 10:35Z
