# run.py r12 independent evidence (EVIDENCE RUNNER, condensed copy), 2026-11-16T18:45:49Z
Raw output: mutation-lane/evidence-r12-independent/ (00-TABLE.md). Recorded, not judged. run.r12.py and safety-tests.r12.sh hashes equal the brief before and after.
## Failures and deviations first
- D1 start-up signal window NOT closed (120 runs, INT and TERM, 6 delays, root and uid 65534): INT at 0 s 10 of 10 exit -2, marker kept, file planted; INT at 0.01 s 9 of 10 exit 1 with KeyboardInterrupt (up to 20 traceback lines); TERM at 0, 0.01, 0.02 s 30 of 30 exit -15, marker kept; later default-action deaths at 0.05 and 0.08 s in single runs. All 120 follow-up --restore --sha runs exit 0, file restored.
- D2 the runner's own test R07 (--raw /, as root) wrote 3 toy-data files into the filesystem root (/N-m1.txt, /N-summary.txt, /N-tree-diff.txt); its rm was blocked by the safety check and not worked around. Someone must delete them. As uid 65534 --raw / is refused. --raw . and paths with .. are accepted and write into that folder.
- D3 plain --restore with a forged marker writes the forged text (limit d); with --sha exit 3. Marker mode 0777 leaves 775; special bits cut (4755, 2755, 1755 give 755; 1735 gives 735).
- D4 Child checks only program name and path text: STARTED a script named git in any folder, a symlink named git to /bin/sh, any file at */.venv/bin/python, /usr/../usr/bin/git, a cwd through a symlink. 35 hostile cases otherwise refused.
- D5 runner slips: git2 name in case 35 (fixed, re-run STARTED); R22 exit 0 was the wrapper (re-run exit 2); R24 8 MB arg hit E2BIG (replaced).
- D6 other agents' jobs shared the cores; nobody full run skipped T62.
## Passes
Full safety-tests.r12.sh: root exit 0, 0 of 469 failed, 16 min 15 s (nested uid 65534 0 of 114); direct uid 65534 exit 0, 0 of 472, skipped T62, 11 min 34 s. ruff check and format clean, noqa 0, S603 clean. Long arguments 84 rows exit 2, 0 traceback lines; test arguments over 60000 bytes exit 2 (r11 limit was 100000 per argument). git status src tests 0 entries. Banned scan 0.
## Not run
Mutation checks; r11 versus r12 comparison of T97-T100 blocks; the builder's 0 of 53 / 9 of 53 claim not repeated.
Leftovers: /tmp/r12-indep-nobody, 3 /tmp/chd.* folders (one holds a symlink to /), the 3 files in /.
