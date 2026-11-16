# run.py r13 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16
Raw output: mutation-lane/evidence-r13-independent/ (00-TABLE.md). Recorded, not judged.
## Failures and deviations first
1. Start-up signal window NOT closed on r13 (120 runs, INT and TERM, delay 0-0.2 s, root and uid 65534): INT at 0 s exit -2 10/10 and TERM at 0/0.01/0.02 s exit -15 30/30, marker kept, file left planted; INT at 0.01-0.02 s mostly exit 1 with KeyboardInterrupt traceback; 0.05 and 0.08 s mixed (130/143 marker kept, or exit 0 restored); at 0.2 s all exit 0. All 120 follow-up `--restore --sha` exit 0, file restored.
2. A hostile `git` first on PATH IS run by r13 (logging wrapper started 8 times in the run form, 6 in `--restore --sha`, both uids). Refused (exit 2): symlink git -> /bin/sh; script named git in cwd with `.` on PATH. Not run: git in cwd without `.` on PATH.
3. Child hostile, 44 cases: only the control starts; case 36 (symlink named git to the real git, other folder) REFUSED although the r13 text says a link to the real git is accepted.
4. Runner's own slips: first `--raw /etc/zz` test wrote 3 toy files into /etc/zz as root (two-level paths allowed by design); removed and checked gone. First read-only-mount `--raw /` test proved nothing, re-run with a writable bind: exit 2, / unchanged. First nobody launch failed (cannot read /home/user). First r12 run used wrong ONLY names.
5. Not the runner's: /N-m1.txt, /N-summary.txt, /N-tree-diff.txt still in /.
6. Two full suites ran at once; peak load not sampled (samples 1.4-2.6).
7. Nobody full run skipped T62 (as r12).
## Passes
Hashes equal evidence-r13/hashes.txt. Full safety-tests.r13.sh as root via heavy-slot: 0 of 476 failed (nested nobody child 0 of 121), none skipped; direct nobody run 0 of 479, skipped T62. `--raw` refused (exit 2, nothing written) for ., ./, ./., .., ../x, ../.., mid-path .., /tmp, /usr, new top-level name; `--raw /` refused as root (read-only bind) and nobody; 25 other shapes no traceback. Forged marker plain `--restore`: modes 4755, 2755, 1755, 0777 give exit 0 written as 755; 1735 -> 715; 0664 -> 644; with `--sha`: special modes exit 3, nothing written; 0664 exit 0. Long arguments (4095-120000 bytes, `-k`/`-m` 99999-100001, total 59990+) exit 2, no traceback. r13 tests T98e2, T99h, T100a, T101a, T101a2, T101b, T101c all FAIL on r12 (11 of 41). Banned scan 0; ruff check and format pass, noqa 0; git status src and tests 0 lines.
## Not run
Mutation checks; `--raw /` as root without the read-only mount.
## Left behind
/tmp/r13-indep-nobody and scratchpad r13i. No process still running.
