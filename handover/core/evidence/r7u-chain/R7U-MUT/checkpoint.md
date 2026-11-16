Sat Nov 14 17:00:52 UTC 2026 start
Sat Nov 14 17:04:24 UTC 2026 baseline A running on tree; runner Z on tree2
Sat Nov 14 17:09:41 UTC 2026 killed first Z runner (pid 20685, mine) after 8 min on Z01 (survived C+B, T suite too slow); tree2 restored byte-equal; tests narrowed
Sat Nov 14 17:12:48 UTC 2026 runners started: tree(pid 7678) X01-24,Y01-12; tree2(pid 7679) Z,Y13-30; baseline note: full test_r7u_a run on untouched copy gave 1 failed (a4 no_open_create, line 407) 40 passed, passes alone
Sat Nov 14 17:18:54 UTC 2026 killed both runners (wide reruns too long); restored; runner changed: narrow first, wide phase later
Sat Nov 14 17:19:22 UTC 2026 runners restarted with narrow -k (kmap.py); wide reruns deferred to a later phase
Sat Nov 14 17:27:06 UTC 2026 running: res1 6/35, res2 9/34
Sat Nov 14 17:33:33 UTC 2026 wide phase 1 (Z survivors, 300s cap each) on tree2 pid 23391
Sat Nov 14 17:37:33 UTC 2026 runner1 done 35 rows; wide phase RR survivors on tree (200s cap) pid 28246
Sat Nov 14 17:39:48 UTC 2026 restarted wide phase with caps 120s (tree) / 100s (tree2) to fit the box; Z01 wide done earlier (300s, ~46% of set, survived); tree/tree2 restored byte-equal after the kill
Sat Nov 14 17:46:47 UTC 2026 wide: 3/9 4/17
Sat Nov 14 17:51:27 UTC 2026 STOPPED wide phase on lead order; trees restored/verified
