# run.py r11 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw: mutation-lane/evidence-r11-independent/00-TABLE.md. Recorded, not judged. sha256 of run.r11.py and safety-tests.r11.sh matched before and after.
## Failures and deviations first
1. Signals during --restore (140 runs, root and nobody): start-up window STILL OPEN on r11. Delay 0 INT/TERM: 10 of 10 per uid died by default action (exit -2/-15), marker kept, file planted. TERM at 0.01 and 0.02 s: 20 of 20 per uid exit -15. INT at 0.01 and 0.02 s: 20 of 20 per uid exit 1 with KeyboardInterrupt (traceback lines 0 except 17 in S16 and 11 in S44). Exit codes 1, -2, -15 are not 128+N. All 140 follow-up --restore --sha gave exit 0.
2. Default-action deaths also later (marker already gone, file restored): root INT 0.08 s 2 of 5, TERM 0.08 s 1 of 5, INT 0.12 s 1 of 5; nobody INT 0.08 s 1 of 5; nobody TERM 0.05 s 1 of 5 with marker kept and file planted. Cause not investigated.
3. Plain --restore with forged marker + matching backup: exit 0, forged text written (N2); with --sha exit 3, nothing written (limit d open).
4. Plain --restore forged mode 0777: exit 0, file mode 777 (group/other write kept); 4755, 2755, 1755 give mode 755.
5. --sha: 4755, 2755, 1755, 0777 exit 3, nothing written; 0664 exit 0 (git archive 0664 header). The 0777 refusal message prints git mode 0o644 (extracted mode, not header).
6. Runner slips: first 1755 row used decimal 989 (octal 1735), re-run with 1005; first -k/-m 100000 rows lacked --pythonpath (replaced by K2 rows).
7. Other agents' r12 jobs shared the machine (load 2-6); a run.r12 .pyc appeared in the lane at 17:44:39 and two /tmp/safety-only.*.sh files exist (not the runner's).
## Passes
Path lengths 4095, 4096, 120000 for --root, --sha, --file, --repo: 88 rows, all exit 2, 0 traceback lines. -k/-m 99999 and 100000 bytes exit 5, 100001 exit 2, 0 traceback lines. check_child_call/Child called directly: all listed bad starts refused (shell=True, relative argv0, executable=, preexec_fn, pass_fds, extra env, NUL, tuple), 2 good controls start; on r10 no check, Child started every bad call except NUL and ./true. ONLY="T95 T97 T98 T99": r11 0 of 52 failed (148 s); r10 15 of 52 failed (T97e, T99a, T99b x4, b2, b3, b4, c, d, e, f x2, g). Controls N0-N10 (root and nobody, 17 rows each) all matched; N2/N6 exit 0 as documented. ruff 0 findings, 0 noqa, format clean (same on r10, so it does not show the S603 change). bash -n ok. git status src tests 0 lines. Banned scan 0.
## Not run
Full safety-tests (builder's 0 of 458 not reproduced); mutation runs; signals against --restore --sha or a normal run; an idle machine; positional-argument bypass of Child (reviewer M1 not tested here).
