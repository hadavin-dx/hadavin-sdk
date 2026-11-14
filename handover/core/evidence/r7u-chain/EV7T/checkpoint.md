start Sat Nov 14 15:53:10 UTC 2026
full run started Sat Nov 14 15:53:28 UTC 2026 pid 26097
hostile a,b done Sat Nov 14 15:54:31 UTC 2026
mutant runners B(mutX) own(mutY) settle(mutZ) started Sat Nov 14 15:56:38 UTC 2026; before-run done: 78F/60P
mutY runner stopped by me after N01 (SIGTERM, copy deleted); N02+ rerun in 3 runners Sat Nov 14 16:02:33 UTC 2026
CHECKPOINT Sat Nov 14 16:40:54 UTC 2026: full run [100%], no failure chars in log so far; flake-load series done 30/30 rc=0; builder mutants 43 done (42 killed, 1 survived U6); own40/settle21 nearly done; broad re-runs of survivors running.
DISK OVERLAP: full run, flake-load series, all mutant runners ran during the ~16:00-16:05Z full-disk window. Hostile tables and the before-run on r7s finished 15:53-15:56Z, before it. No "No space left"/Errno 28 in any raw log of mine (grep done 16:06Z; re-grep at the end).
chain: quiet flake starts when mutant runners are gone or after ~14 min Sat Nov 14 16:41:33 UTC 2026
final report written Sat Nov 14 17:16:18 UTC 2026
