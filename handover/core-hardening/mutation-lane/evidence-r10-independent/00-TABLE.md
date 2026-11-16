# evidence-r10-independent (EVIDENCE RUNNER; records, does not judge)
Inputs: copies in `in/` of evidence-r10/frozen/run.py (sha256 de731766...c7528, matches hashes.txt) and safety-tests.sh (19388489...7250, matches); run.r9.py c81a7ba9...3e6a and safety-tests.r9.sh b498dd03...bc5 (the r9 backups). Lane originals have the same hashes as the frozen copies (hashes-before.txt, hashes-after.txt equal). All runs used copies under the session scratchpad (r10-indep/in), python3 -B -I, 4 cores shared with other agents' jobs (load 2 to 4, RAM free above 1.3 GB of 16 GB used 10 percent, disk 72 percent).

## Failures and deviations (first)
| id | what was seen | file |
|---|---|---|
| D1 | Signals sent 0 to 0.2 s after launch of `--restore` (30 runs, uid 0, python -B -I): 15 of 30 runs ended with an exit other than 0, 130 or 143. 11 runs died by the default signal action (exit -2 or -15): H5-1, 3, 7, 8, 13, 19, 20, 26, 28 (marker kept, file still planted, delay 0 to 0.05 s) and H5-22, 23 (TERM, --sha path, delay 0.08 and 0.12 s: output says the file was restored and marker_left=0, yet exit -15, i.e. the signal ended the process after the restore text). All 30 follow-up `--restore --sha` runs: exit 0, file back to return1. The 0 to ~0.05 s cases are the start-up window the builder documented as impossible-now; H5-22/23 at 0.08 to 0.12 s are later than that. | hostile-signals-root.txt |
| D2 | 4 runs ended exit 1 with KeyboardInterrupt text (INT): H5-2 (plain, 0.02 s), H5-14 (sha, 0.02 s), H5-25 (plain, 0.01 s), H5-27 (sha, 0.01 s); traceback line counts from the grep: H5-27 12 lines, H5-3 9 lines (exit -2), the others 0. Marker kept in all, file planted. The builder claim (early handlers right after the imports, exit 128+N) held in H5-9, 15, 21 (exit 143 or 130, text INTERRUPTED, marker kept) but not in these runs. Elapsed 0.04 to 0.08 s measured from before Popen; machine load average was 2 to 4. I did not classify the cause. | hostile-signals-root.txt |
| D3 | Plain `--restore` with a forged marker + backup whose hash matches: exit 0, the swapped text (`return 99 # forged`) WAS written (uid 0 and nobody). Matches the documented limit (d); `--restore --sha` refused, exit 3, nothing written (H3a, H3b). | hostile-root.txt, hostile-nobody.txt |
| D4 | Plain `--restore` with a forged marker mode: marker mode 0777 gave file mode 777, mode 4755 gave file mode 4755 (setuid), mode 2755 gave 2755 (setgid), exit 0, as root AND as user nobody (H4 rows). With `--sha` all three: exit 3, nothing written, file stayed planted. (Builder test T98e2 text says mode "masked to 0777 at most"; the observed file modes above are 777, 4755, 2755, i.e. special bits were NOT masked off in plain mode.) | hostile-root.txt, hostile-nobody.txt |
| D5 | Builder claim "T98 fails 7 of 7 on r9 code" (dev3-r9code-T98only.txt) not reproduced: T98 on run.r9.py = 4 of 7 fail (T98a, b, c, f); T98d, T98e, T98e2 PASS on r9 code. Cause seen in dev3 file: with ONLY=T98 alone the helpers `forge97` and `setmarker97` (defined in T97) are "command not found" (lines 27, 30, 34), so T98d/e/e2 failed for a harness reason, not a code reason. T96 T97 T98 together are needed. | t96-98-on-r9code.txt |
| D6 | `ruff check` on run.r9.py: 2 S603 findings (expected). noqa count 0 in both files. | ruff-check-run.r9.py.txt |
| D7 | Not mine, observed: other agents' jobs were running during my runs (pytest of the repo, mutate_run.py, mutate.py, later safety-tests.r11.sh). I did not touch them. 3 `/tmp/safety-only.*.sh` files exist: two created at 16:47 by someone else's running job, one (L5arBV) dated 15:42, before my start; none are mine. | ps-before.txt, ps-after.txt |

## Passes
| check | result | file |
|---|---|---|
| (1) one full safety-tests.sh as root, includes child uid 65534 (T88) | exit 0, 832 s; root FAILED CHECKS 0 of 442; child (uid 65534) FAILED CHECKS 0 of 87; skipped none | full-run.txt, full-run.exit, full-run.timing |
| (2a) `--restore` with --root / --sha / --file / --repo of 4097 bytes, 120,000 bytes and a 300-byte name (12 cases) + --restore given first | all 13 exit 2, 0 traceback lines, state empty, file unchanged; as root and as nobody | hostile-root.txt, hostile-nobody.txt (rows H1-*) |
| (2b) name with a newline in --root, --sha, --file, --repo | all exit 2, 0 traceback lines, file unchanged; as root and as nobody | rows H2-* |
| (2c) forged marker + matching backup with `--sha` | exit 3, nothing written, marker and backup kept | row H3b |
| (2d) mode 0777, 4755, 2755 with `--sha` | exit 3, nothing written | rows H4-*-sha |
| (2e) signals: all 30 follow-up restores | exit 0, file return1 | hostile-signals-root.txt |
| (3) T96 T97 T98 on run.r9.py | FAILED CHECKS 23 of 46 (T96e 1, T97 18 [T97f2 passes], T98 4); on r10 code the same blocks pass inside the full run | t96-98-on-r9code.txt |
| (4) ruff check run.py | All checks passed, 0 S603, 0 noqa (ruff 0.16.9, repo pyproject config) | ruff-check-run.py.txt |
| (4) ruff format --check run.py and run.r9.py | already formatted, exit 0 | ruff-format-*.txt |
| (4) bash -n safety-tests.sh | exit 0, no output | bash-n.txt |
| (5) git status --short src tests | 0 lines before, 0 lines after | gitstatus-src-tests-before/after.txt |
| (6) stray processes | none of mine left (0 processes with the r10-indep path; my nobody temp folder removed). Other agents' processes listed in ps-before/ps-after. No __pycache__ created. | ps-*.txt |
| banned-vendor scan (list read at run time) | 10 entries read, 0 matches in this folder's files (counts only) | banned-scan-counts.txt |

## Not run
- Signals as user nobody (the brief asked signals once, 30 runs; run as root only).
- Mode checks of the marker with setgid combined with sticky (1755) from my own plan: not run; only 0777, 4755, 2755.
- No mutation run, no negative-control block N0-N10 (not requested).
- Raw per-run traceback text of the signal runs is not kept (each run overwrote h5.out); only counts of traceback lines are in the file.
- The "one fixed pointer file in the state folder" from REPORT-runpy11 (builder: not done): not testable, not run.
- Timing: signal results depend on machine load (load average 2 to 4 from other agents' jobs); I did not repeat the 30 runs on an idle machine.
