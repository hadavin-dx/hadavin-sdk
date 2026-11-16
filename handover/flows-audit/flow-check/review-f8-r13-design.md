# F8 flow-check round 13 design review (agent af9239e4, egm-design), static, security path uncapped
Saved by flows-audit, condensed. Reviewer words unverified; nothing executed. 0 Blocker, 1 Major, 14 Minor. No path found where run_all.sh exits 0 after a failed, skipped, timed-out or killed step, except M1.
M1 run_all.sh:493 `trap '' INT TERM HUP` around publish_raw IGNORES the signal: a stop during `--refresh` is lost, run prints status 0 and exits 0. Stop tests A-H never use --refresh. Fix: trap 'SIGPEND=1', restore traps after copy, `[ -z "${SIGPEND:-}" ] || exit 143`.
m1 `lim` jobs inherit lock fd 9 (README:32 says closed in every job); fix `9<&-` in lim.
m2 test_run_all_stop.sh:92,96 grep '^fc-selftest-[^o]' hides folders starting with "o" (~12.7% over 5 tries).
m3 same bug class not fixed in siblings: selftest.py:1608 OUT before cleanup armed; run_all.sh RAW/W mktemp before trap/MADE_W.
m4 selftest.py handler cannot run inside a long C call; fc-selftest-* left outside $W; fix TMPDIR="$W/st-tmp".
m5 RUN_ALL_RC read from environment, not scrubbed; unset at top.
m6 run_all.sh:237 missing mf_leads.sql silently drops --ddl; abort exit 3.
m7 test_run_all_stop.sh:72,101 silent skip of missing files; use REQUIRED-list pattern.
m8 build_mainframe.py run without -I.
m9 git steps run foreground subshell; trap deferred; README Ctrl-C precondition missing.
m10 README:35 "every step that starts a program has a limit" stronger than code.
m11 no handler for SIGQUIT/SIGPIPE.
m12 comment "never holds half a refresh" true only for signals.
m13 deny-list passes STRIPE_SECRET_KEY, SSH_AUTH_SOCK, DOCKER_*, KUBECONFIG, SSLKEYLOGFILE, TMOUT.
m14 test_take_check.sh:894 source-text grep; README 12 vs script 10 minutes; pkill regex from unescaped $T.
NOT read/done: ~1000 of 1070 lines of test_take_check.sh, ~3000 selftest.py case lines, check_flows.py, build_mainframe.py, take_check.sh beyond greps; the fixer's 592/725/case H claims not verified.
