# F8 flow-check round 13 codebase review (agent a4b5d2d7, egm-codebase-details), static, security path uncapped
Saved by flows-audit, condensed. Reviewer words unverified; no shell, nothing executed. 0 Blocker, 0 Major, 8 Minor. Says counts pin (725 / 0 / 62 / 592 / 0) match the code regexes; stop-test 56 cases counted (8 x 6 + 2 + 6); fixer's 725/592 totals not checkable statically (only the fixer's own evidence).
m1 test_run_all_stop.sh:92,96 grep '^fc-selftest-[^o]' misses folders starting with "o" (same as design m2).
m2 run_all.sh:227,229 git steps in foreground subshell delay signals; comment at :34 false for these.
m3 run_all.sh:493 `trap ''` ignores, not holds, signals during publish (design reviewer rates this Major, M1).
m4 test_run_all_stop.sh:57,95 `wait "$RUNPID"` unbounded.
m5 test_run_all_stop.sh process patterns assume $T has no symlink.
m6 test_take_check.sh:1027-1029 relative scratch path fails (standalone only).
m7 selftest.py:1608 OUT folder not removed by handler when FC_OUT unset.
m8 README:115 stale ("fix-f8-r9.md"), README:32 says three env variables but script reads more, run_all.sh:113 omits --lock-only.
Verified by reviewer (static): lim and <&0 here-doc, set -u only, signal handler window, nested-run ancestry.
NOT read: take_check.sh, check_flows.py, take-warns.pin, test_run_all_raw.sh, repeat_run_all.sh, most of selftest.py and test_take_check.sh.
