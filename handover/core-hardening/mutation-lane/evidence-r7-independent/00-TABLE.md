# Independent evidence run, mutation runner r7 (EVIDENCE RUNNER: runs and records, does not judge)
Run 2026-11-16, toy repository only, no network, no spend. Copies run from a scratch folder; originals untouched.

## Failures and surprises first
1. Closed/full output: with standard output pointing at /dev/full (I4) the run ends with exit 1 (Python's own flush error), not one of the tool's exit codes. The file under test was back and the state folder empty.
2. Very deeply nested mutants JSON (200000 nested brackets, J-deep): prints a full Python traceback inside an "INTERNAL ERROR (RecursionError ...)" message, exit 2, nothing planted. Not a clean refusal text.
3. Cases that leave the mutant planted on purpose (marker and backup kept, exit 3), all recoverable or needing a hand step:
   - R2 src/ swapped for a symlink mid-run then SIGTERM: exit 3, planted text stays in the real file; --restore refuses while the symlink is there; after renaming back, --restore puts the original back.
   - T-rm (a test deletes the file under test): exit 3; later --restore works (file back).
   - T-ln (a test deletes the file and leaves a dangling symlink): exit 3; --restore refuses (symlink) until the link is removed by hand; no planted text exists anywhere (the planted file was deleted).
   - SIGKILL (expected): planted, exit 137, --restore puts it back.
4. ruff: default settings (no repo config, copy in /tmp) say "1 file would be reformatted" for run.py; with the repo config (pyproject.toml, line length 100) format check passes. ruff check with repo config: 2 findings, both S603 (run.py lines 569 and 1380). Details in 02-*.
5. Not checked: the full run used the builder's method (VENV = an existing scratch venv with pytest 9.2.0). Kill cases used --no-control (no baseline) for speed. root user: file modes do not block writes (P1 not meaningful), so read-only was tested with chattr +i (P2) and a read-only mount (P3).

## Headline numbers
| Item | Result |
|---|---|
| Hashes | run.py 01a741d2...d7a7 and safety-tests.sh 5a06a0f5...208f equal the builder's hashes.txt (copies equal originals). r6 copies equal the builder's listed r6 hashes. |
| py_compile, bash -n | both rc 0, nothing printed |
| ruff check (default) / (repo config) | rc 0 "All checks passed" / rc 1, 2 errors S603 |
| ruff format --check (default) / (repo config) | rc 1 "1 file would be reformatted" / rc 0 "1 file already formatted" |
| Full safety-tests.sh on r7 | `FAILED CHECKS: 0 (of 353 checks run; skipped: none)`, 353 PASS lines, 0 FAIL lines, script exit 0, about 20 min |
| T76-T86 (36 checks) on r7 | `FAILED CHECKS: 0 (of 36 checks run; skipped: none)` |
| T76-T86 on r6 code (NCF= exported) | `FAILED CHECKS: 31 (of 36 checks run; skipped: none)`: 31 FAIL, 5 PASS (T76a genuine restore, T76b genuine restore, T76c genuine restore, T76d forged backup guard, T82c reversed patch) |
| Hostile cases | see below |

## Kill cases: after EVERY case, is the original file text back?
| Case | Exit | Original text back | Marker/backup left | Stray pytest |
|---|---|---|---|---|
| SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGUSR1, SIGUSR2, SIGALRM, each at the instant the planted text appears (7 cases) | 130,143,129,131,138,140,142 | YES (7 of 7) | none | 0 |
| same 7 signals 3 s after plant (tests running) | same | YES (7 of 7) | none | 0 |
| SIGINT, SIGTERM, SIGHUP sent to the whole process group at plant (3) | 130,143,129 | YES (3 of 3) | none | 0 |
| TERM, TERM, INT, HUP back to back | 129 | YES | none | 0 |
| Spray: SIGTERM, SIGINT, SIGHUP each at 13 delays 0.05 to 3.5 s after start (39 runs) | not tabled per run | 39 of 39 YES; 0 left planted | none | 0 |
| SIGKILL at plant | 137 | NO (planted, as expected) | marker+backup kept | 1 (killed by me) |
| SIGKILL then --restore | 0 | YES | none | - |
| stdin closed, SIGTERM at plant (I2) | 143 | YES | none | 0 |
| --root swapped for a symlink to the moved folder, SIGTERM (R1) | 143 | YES (in the moved folder) | none | 0 |
| src/ swapped for a symlink, SIGTERM (R2) | 3 | NO (kept planted on purpose, see item 3) | kept | 0 |

## Other hostile cases (all rows in 05b and 05c)
| Case | Exit | Observed |
|---|---|---|
| F1 forged marker, file = ../../victim.txt | 3 | victim not overwritten, RESTORE FAILED text |
| F2 forged marker in the private state folder, file=docs/note.txt, backup swapped with matching hash | 0 | docs/note.txt now holds the swapped text (needs write access to the user's own state folder) |
| F3 marker not JSON | 2 | refused, no traceback, file still planted |
| F4 marker with absolute paths | 2 | /etc files unchanged |
| F5 marker is a symlink | 2 | /etc/hostname unchanged |
| R3 --root is a symlink to the real folder | 5 | ran normally (no baseline: 5), file back |
| O1 --out-json is a symlink | 2 | refused, victim untouched |
| O2 --out-json inside root | 2 | refused before planting, file back |
| O3 --out-json outside (control) | 5 | json written (5 because --no-control) |
| O4 --out-json /dev/full | 2 | refused, no traceback |
| L1 file under test hard-linked outside root | 2 | refused ("exactly one name"), other name untouched |
| L2 hard link inside root | 2 | refused, both names original |
| J: deep, obj, dup, escape, abs, nul, bignew (60 MB), idweird, types, bigint, empty, bom, nan | 2 except nul and bignew 5 | all targets back, no state left, /etc/hostname unchanged; only J-deep has a traceback (item 2); J-many (20000 mutants) exit 5, file back |
| I1 stdin closed | 5 | file back |
| I3 stdout and stderr closed | 5 | file back |
| I4 stdout /dev/full | 1 | file back (item 1) |
| P1 modes 555/444 as root | 5 | file back (modes do not stop root) |
| P2 chattr +i | 2 | refused ("Operation not permitted"), file back |
| P3 read-only mount of src/ | 2 | refused ("src is a mount point"), file back |
| T-perm, T-corrupt (a test changes mode / content of the file under test) | 5 | file back |
| S1 state folder is a symlink | 2 | refused, nothing created in target |
| S2 --restore with no marker | 0 | "no marker" message |
