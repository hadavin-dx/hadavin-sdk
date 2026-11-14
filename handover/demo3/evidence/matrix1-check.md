# MATRIX-1 check (evidence runner, read-only, 2026-11-14)

| claim | source read | what the source says | result |
|---|---|---|---|
| M1/M2/M3 full: 3684/30/169, rc 1, wall 881/882/904 (pytest 880.06/879.94/903.24) | raw/m1-run.log, m2-run.log, m3-run.log tails | "30 failed, 3684 passed, 169 skipped in 880.06s" / "...879.94s" / "...903.24s"; "EXIT_CODE=1 WALL_SECONDS=881/882/904" | MATCH |
| M4 full: 3714/0/169, rc 0, 924 (923.92) | raw/m4-full.log tail | "3714 passed, 169 skipped in 923.92s"; "rc=0 wall=924s" | MATCH |
| M4 full seed 20261114 | raw/m4-full.log head (no seed); m4-report.md run table; /home/user/work/priv/m4-run.sh | log shows no seed; report table: "FULL suite (tests/) | set | 20261114"; run script takes seed as argument 2 and passes --shuffle-seed | NOT FOUND in log; stated only in m4-report.md (MATRIX already says "per report"; fine) |
| gitleaks version 8.30.1 | ran /home/user/work/priv/gitleaks-bin/x/gitleaks version | 8.30.1 | MATCH |
| gitleaks URL | m4-report.md line 11 | https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz | MATCH (report only; no raw log holds it) |
| sha256 551f6fc8...470eb | sha256sum of gitleaks_8.30.1_linux_x64.tar.gz; gitleaks_8.30.1_checksums.txt | computed 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb; checksums file line identical | MATCH, but it is the sha256 of the ARCHIVE. The extracted binary x/gitleaks has sha256 88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509. MATRIX should say "archive". |
| 3-file runs: 72 passed, seed 20261114 66.52 s / seed 0 65.47 s, rc 0, wall 67/66 | raw/m4-bin-s20261114.log, m4-bin-s0.log | "72 passed in 66.52s" rc=0 wall=67s; "72 passed in 65.47s" rc=0 wall=66s | MATCH |
| M4 no program: 42/30, rc 1, wall 35 | raw/m4-nobin.log | "30 failed, 42 passed in 34.13s"; "rc=1 wall=35s" | MATCH |
| Re-runs 30 failed/42 passed; times M1 default 34.22/35.35/33.60; shuf 35.27/34.21/34.46; M2 default 34.04/34.53/34.53; reversed 37.24/35.09/34.61 | raw/m1-rerun-*.log, raw/m2-rerun/*.log tails | all equal the MATRIX numbers | MATCH |
| rc of M1/M2 re-runs (MATRIX: not in log tail) | raw/m1-rerun-*.log, m2-rerun/*.log, m1-report.md, m2-report.md | no rc/exit line in any of the 12 logs; reports give rc only for the full runs | NOT FOUND (cannot be read anywhere; "30 failed" implies pytest rc 1 but that is inference) |
| 30 failures split 24/2/4 | raw/m2-rerun/ids-d1 counted | 24 tests/test_gitleaks_exceptions.py, 2 tests/test_gitleaks_semgrep_lock.py, 4 tests/test_hygiene.py (30 lines) | MATCH |
| m3-failed.txt same ids | raw/m3-failed.txt | 30 lines (I did not diff) | MATCH on count; diff not run |
| Failure cause text | raw/m1-run.log, m4-nobin.log | "gitleaks binary not found: put it on PATH or set GITLEAKS_BIN" | MATCH |
| Skips 169 = 113+28+22+3 playwright, 1+1+1 | raw/m1-run.log and m2-run.log SKIPPED lines | 9 lines each: [113] lead_pages:113, [28] browser:27, [22] mode_safety:110, [1]x3 wording (204,171,257), [1] stall_eviction:526, [1] server_hardening:224, [1] n8n_api_url:510 | MATCH |
| m3-run.log and m4-full.log have no SKIPPED lines | grep -c "^SKIPPED" | 0 and 0 | MATCH |
| playwright 1.63.0, greenlet 3.5.6, pyee 13.0.1, pytest 9.2.0 | raw/m6-pip-list.txt | greenlet 3.5.6, playwright 1.63.0, pyee 13.0.1, pytest 9.2.0 | MATCH (MATRIX says "not re-read"; now verified) |
| pip install rc 0, 9.7 s | raw/m6-pip-install.log; m6-report.md | log has "real 0m9.674s"; no rc line in the log (rc 0 only in m6-report.md line 16) | MATCH for time; rc NOT FOUND in log (report only) |
| chromium revision 1243 | m6-report.md; ls /opt/pw-browsers | chromium-1243, chromium_headless_shell-1243, ffmpeg-1011, chromium | MATCH |
| M6 run1 113 passed 97.52 s rc 0 wall 98; run2 533 passed 421.98 s rc 0 wall 422 | raw/m6-run1.log/.rc, m6-run2.log/.rc | "113 passed in 97.52s"; "533 passed in 421.98s"; rc files "rc=0 wall=98" and "rc=0 wall=422" | MATCH |
| M6 run2 file list (11 files) | raw/m6-run2-files.txt | 11 files, test_portal_api ... test_stage_confirm_browser | MATCH |
| Section 1: m7-tree/data exists, created 03:28:38 | stat | m7-tree/data 2026-11-14 03:28:38 +0000; m6-report.md line 23 says "No ... data folders" | MATCH (disagreement real) |
| data/ times m1 02:57:14, m2 03:00:31, m3 03:26:32, m4 03:20:49; none in m5, m6, m6-chk | stat | identical times; m5-tree, m6-tree, m6-chk: no such file | MATCH |
| M2 report "only __pycache__" vs m2-tree/data on disk | m2-report.md line 30; stat | report: only pyc; disk: m2-tree/data exists | MATCH (disagreement real) |
| fix-9 patch sha b56dfdde...ac08 | sha256sum lane3-fix-9.patch | b56dfdde4af159429a0bed82c37a27a5906bdf2fe43fe5aab62eaa716ebbac08 | MATCH |
| core-fix-on-frozen-r7e.patch sha 89ca3a2d...cee8, equals notes | sha256sum; lane3-fix-9-notes.md line 13 | computed 89ca3a2ddeba2a1a1c006d32a38520643861aa94848730b8fcdcf1a46457cee8; notes same | MATCH |
| patch adds import shutil / tempfile (lines 9, 15) | grep lane3-fix-9.patch | "9:+import shutil", "15:+import tempfile" (also "55:+import shutil" in another file of the patch) | MATCH |
| B9 three-file 3.13/3.12: 92 passed, 8 skipped, 1 xfailed, rc 0; 64.98 / 64.36 s | raw/b9-three-313.log, b9-three-312.log | "92 passed, 8 skipped, 1 xfailed in 64.98s"; "...64.36s"; rc=0 | MATCH |
| B9 fails-before: 32.87 / 32.41 s, 1 failed | raw/b9-fails-before2.log, b9-fails-before.log | "1 failed in 32.87s"; "1 failed in 32.41s"; log also has an rc? not shown in tail | MATCH (MATRIX table says 0 passed / 1 failed; log says "1 failed", no passed count, fine) |
| B9 full 3690/199/1 xfailed, 945.14 s, rc 0 | raw/b9-full-313.log | "3690 passed, 199 skipped, 1 xfailed in 945.14s (0:15:45)"; "rc=0" | MATCH |
| /helper.txt 865 bytes root 03:20, first line @contextmanager | ls -l, head | -rw-r--r-- 1 root root 865 Nov 14 03:20; "@contextmanager" | MATCH |
| Python 3.13.18 | py313-venv python -V | Python 3.13.18 | MATCH |
| pyproject requires-python >=3.12 line 5 | grep m1-tree/pyproject.toml | 5:requires-python = ">=3.12" | MATCH |
| m5-report.md absent | ls evidence/m*-report.md | m1,m2,m3,m4,m6 only | MATCH |
| "M1 re-run: M1 default and shuffled seed 20261114" ; M2 report on seed | m1-report.md line 5 | seed 20261114 | MATCH |
| M4 report on m4-run flags | m4-run.sh | pytest -q -rs -rf, seed via -p shuffleorder --shuffle-seed | MATCH |

Not re-run by me (no pytest runs allowed): which gitleaks/semgrep, diffs of failed ids between runs.
