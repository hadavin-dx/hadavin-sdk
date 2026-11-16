start Sat Nov 14 17:00:28 UTC 2026
full run pid 8167 Sat Nov 14 17:00:42 UTC 2026
before pid 8558 Sat Nov 14 17:00:48 UTC 2026
hostile a + loopback standalone done Sat Nov 14 17:01:20 UTC 2026
probe 8524
before done; probe started Sat Nov 14 17:23:44 UTC 2026
mutA pid 25580
probe done, mutA started Sat Nov 14 17:35:04 UTC 2026
probe table done Sat Nov 14 17:35:12 UTC 2026
chain 25935
watchdog pid 10145 kills 8173 at ~18:40; replaced 3600s timeout (killed timeout pid 8172, my own) because the run needs more than 60 min Sat Nov 14 17:49:26 UTC 2026
NOTE wrapper.log rc=137 is from my kill -9 of the timeout wrapper at 17:49:25Z, NOT pytest's rc
mutants done (A 38 killed; B 15 killed + B13/B15 re-pointed to loopback.py killed; C 26 killed 1 survived L11) Sat Nov 14 18:06:53 UTC 2026; flake quiet starting
flakeQ 2780
quiet series stopped after 3 runs: killed my pids 2780,30575 (run 4 interrupted) Sat Nov 14 18:25:44 UTC 2026
loader mutA pid 30830  Sat Nov 14 18:25:48 UTC 2026
flakeL pid 30832 Sat Nov 14 18:25:48 UTC 2026
flakeL stopped by WRAP-1 after run 1; run 2 interrupted (log removed); killed my pids 30832 30830 1727 30841 Sat Nov 14 18:30:53 UTC 2026
