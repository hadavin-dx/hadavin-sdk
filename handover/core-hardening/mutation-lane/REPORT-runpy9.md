# REPORT-runpy9: run.py r8 and safety-tests.sh r8 (builder report; NOT self-approved, independent review comes next)

## Failures, gaps and unverified, first
1. The ONE full run was not clean on its first try, and I did not get a second full run. First full run on the final run.py: `FAILED CHECKS: 3 (of 395 checks run)` (evidence-r8/full-run.txt). Causes, all in safety-tests.sh, none in run.py: T51b x2 still expected exit 0 where r8 now correctly gives exit 3 (a group member that cannot be verified is left alone, so the group is unsettled: the same N2 rule); T88 used a relative `$0`, so the non-root child could not find the script copy. I fixed those lines and re-ran only T42+T51+T88 (needed helpers) on the fixed script: `FAILED CHECKS: 0 (of 56)` and the non-root child `0 (of 50)` (evidence-r8/targeted-T51-T88-after-fix.txt). So the final safety-tests.sh (sha below) has NOT had a complete run; the full-run.txt was on the previous version (sha c5611b30...; copy in evidence-r8/safety-tests.sh.fullrun-version). The diff is three lines. An aborted earlier attempt (5 old checks T23a T23b T32b T39 T43c expecting r7 exit codes; updated to r8 semantics) is kept as full-run-aborted-first-attempt.txt. An independent reviewer should run the full file once.
2. (d) forged marker with a swapped backup whose hash matches: CANNOT be fully closed. A same-user attacker can rewrite the state folder, run.py and the tests; only a signature or a secret the user cannot read would stop that. Partial fix: `--restore --sha COMMIT [--repo R] [--patch F]` rebuilds the original from git and refuses (exit 3) if the backup differs. A plain `--restore` still accepts a forged-but-consistent backup. T95d1 pins that limit; T95d2/d3 test the --sha path.
3. N5 (a test that escapes with setsid/setpgid): impossible to stop without a cgroup or PID namespace. Documented in the docstring (PROCESS GROUP ONLY); T89 pins the behaviour. N6 simultaneous-start race: documented, not tested.
4. Q32 unchanged: a real SEGV/BUS/FPE/ILL still spins forever; text accurate.
5. Not done: no EGM skills invoked, no git (folder is not a repo), no R-numbers. Evidence for r7-vs-r8 is by my own runs, not independent.
6. Deliberate behaviour changes the tests now pin: exit 3 (not 2) whenever a marker exists and the restore did not finish (T17, T23a/b, T32b, T69a, T76d, T87); `--no-control` plus a test that chmods the file gives verdict SURVIVED, exit 5.
7. T77d/e only prove option semantics (they cannot fail on r6 except via an unknown option); T77f is the guard. The derived-script copy is gone: ONLY="T76 T87" now cuts blocks out of the shipped file at run time (byte-identical by construction). Subsets need the helpers of earlier blocks (T51 needs T42's setmarker).
8. Non-root: T88 delegates to a child run as uid 65534 (setpriv). Verified: T52 T53 T76 T85 T87 T88 T92 T93 T94 T95 in the dev run (0 of 47) and T88 in the targeted run. In the full run the non-root child failed only through the path bug in item 1; its result on the final script is the targeted run above, not the full set.

## Lead's four extra findings (a)-(d)
| # | Fix | Test | Fails on r7 |
|---|---|---|---|
| a /dev/full stdout exit 1 | SafeOut writes with os.write, swallows OSError | T95a (a2 guard) | yes (got 120/2 vs 0) |
| b 200000-deep JSON traceback | loads_json maps RecursionError to ValueError; INTERNAL ERROR text truncated, short traceback | T95b, T95b2 | yes |
| c dangling symlink blocks --restore | text now says exactly "rm -- PATH then --restore" (folder link: "mv -- X X.link, put the folder back, --restore") | T95c, T95c2 | yes |
| d forged backup | partly: --restore --sha (see failure 2) | T95d1 (pin), T95d2/d3 | d2 yes |

## r7 review findings
| Finding | Fix | Test | Fails on r7 |
|---|---|---|---|
| M1 exit code says nothing planted while planted | one choke point may_be_planted(); every path with a marker after restore maps to 3; Forged stays 2 | T87a-h (exit 3), T87i-k guards, T17, T69a, T76d, T94 | yes (T87a-h, T17, T69a, T76d, T94) |
| N1 control-marker problem aborted the restore | settle_control() records, continues, exit 3 | T93a-c | yes |
| N2 unsettled orphan reported as success | settled honoured; file written, state KEPT, "STILL RUN", exit 3 | T93d, T93e, T39, T43c, T51b | yes (T93d) |
| N3 SIGTERM in final cleanup gave nonzero | SIG.exiting before return | T92 | yes (130) |
| N4 --out-json equal to script/list/patch/raw | reject_output_inputs, duplicate check | T90a-d (+T90e guard) | yes |
| N5 setsid escapee | documented | T89 | n/a (documents) |
| N6 other TMPDIR run | other_run_check with non-blocking flock probe | T91a | yes |
| N7 read-only/000 target as normal user | _make_writable via /proc/self/fd chmod, same-inode check | T88a-f, T76c | yes |
| evidence items | T77c-f real behaviour via NOBASE_OPT; T76d expects 3; derived script dropped | T77, T76 | yes (T76c/d) |

New tests on the r7 copy: `FAILED CHECKS: 33 (of 61)` as root and `32 (of 55)` in the non-root child (evidence-r8/new-tests-on-r7code.txt). Guards that pass on r7 by design: T87i/j/k, T76a/b, T89 behaviour, T90e, T95a2, T95d1.

## Checks
- ruff format --check (repo pyproject): 1 file already formatted. ruff check: only the 2 known S603, no noqa. py_compile ok, bash -n ok.
- Banned vendor strings: 0 hits in run.py, safety-tests.sh, checkpoint, evidence-r8.
- Full run (previous script version): 395 checks, 3 failed (item 1), then fixed and targeted-rerun clean.
- Q29: run.py stays out of every PR.

## Hashes (evidence-r8/hashes.txt)
- run.py 39059b7c5a1dc031cf1b47ab6fe2242f8c0c09e4afc1c1763a51fa52d897e009
- safety-tests.sh 6915bbe96fdbcd61d3e65c941ae06cdf94c0761cd70a54834febc03ffbfffd92
- r7 backups (raw/.codecopies/run.py.r7, safety-tests.sh.r7) and r6 backups untouched.

Cleanup: scratch r8 folders and /tmp/r8ruff removed; no stray processes found; the other agent's scratchpad venv left alone.
