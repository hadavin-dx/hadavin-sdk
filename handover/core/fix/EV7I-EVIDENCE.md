# EV7I EVIDENCE (r7i, the one full run). EVIDENCE RUNNER: raw facts, no judgement.
Raw files: /home/user/build/rr6/out/EV7I/ (wrapper.log, pytest-full.log, stage-*.log, stage-summary.txt, fail-ids.txt, ruff-*.txt, machine.txt, checkpoint.md, run-full.sh, t.sh, stage.sh). Frozen tree and tree-R7B..R7I etc. not edited. Made-up data, loopback only (unshare -n + lo_up driver), no spend, nothing pushed.

## NOT RUN (first)
1. Full suite run ONCE only, in the plain copy (no .git, no data/). In the staged git copy (git init, git add -A, no commit, no data/) only the 8 listed git-needing files were run (not the whole suite).
2. No re-run of any failing test file alone was needed: the 7 failures are the same 7 ids as EV7G (all git-work-tree tests); each passes in the staged copy.
3. Not run: the new file tests/test_r7i_findings.py alone (it ran inside the full run; -q output does not name it; I did not count its tests separately). No mutation run, no hostile-input drivers, no Windows/PowerShell/Python 3.13+.
4. Load was NOT quiet: other agents' pytest runs were active (see machine state).

## Step 1: patch
- gunzip of core-fix-on-frozen-r7i-crlf.patch.gz = 5a25f99ef409fec2dd8dadda63baec48d7a0ed6c140e8cfdee1da634dbd32d0e (equals sha256-r7i.txt crlf entry). LF patch = 1d0aa766...e0b60 (equals). The .gz file itself: 9b313490...5c9e (not listed in sha256-r7i.txt).
- Fresh copy of /home/user/build/rr6/demo-frozen/repo2 (HEAD tree 49d3c85938fe5323a3378a49195d3b8da434b3ca; HEAD commit 58aa4031) without .git and data/ -> /home/user/build/rr6/tree-EV7I. In a temp git init: `git apply --check` rc=0, `git apply` rc=0, then .git removed.
- `diff -r -x __pycache__` of src, scripts, tests, load_tools, docs against tree-R7I: all rc=0 (empty). Without the pycache exclusion tree-R7I shows only __pycache__ dirs. Whole-tree `diff -rq -x __pycache__` differs only by "Only in tree-R7I: .ruff_cache".

## Step 2: machine state before start (06:27:39Z)
load average 1.59 1.91 1.58, nproc 4. Other agents' pytest/unshare runs active (pids 7713, 9873/9875 on tests/test_r7i_findings.py, 25680, 26765); not touched. Load at my full-run start 1.46, at end 8.62 (4.52, 3.17).

## Step 3: full run
- Method as EV7G (run-full.sh copied, only the output dir changed), env -i with PLAYWRIGHT_BROWSERS_PATH, GITLEAKS_BIN, DPLD_REQUIRE_SCAN=1, DPLD_REQUIRE_DEMO=1, PATH bin first, TMPDIR outside tree, PYTHONPATH=<tree>/src, PYTHONDONTWRITEBYTECODE=1, limit 2700 s, under `unshare -n python3 lo_up-q4g.py venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs`.
- wrapper.log: start 2026-11-14T06:27:42Z, end 06:57:26Z, rc=1, signal=none.
- Result line: `7 failed, 5554 passed, 8 skipped, 60 warnings in 1782.18s (0:29:42)`. EV7G: 7 failed, 5468 passed, 8 skipped (+86 passed).
- Failing ids (identical by name to EV7G, `diff` of the two sorted lists is empty; none fails in only one run):
  test_hygiene.py::test_hygiene_scan_public, ::test_no_control_characters_in_markdown, ::test_sh_blobs_no_cr, ::test_the_secret_scan_files_have_no_carriage_return; test_nosemgrep_form.py::test_no_bare_nosemgrep_comment; test_raw_bidi_chars.py::test_no_tracked_file_holds_a_raw_direction_control_character; test_shell_single_bracket.py::test_no_tracked_script_or_workflow_run_block_holds_a_single_bracket_test.
- No timing-looking failure, so no alone re-run was made. 8 skipped (reasons): root can read any file; root/Windows file with no permissions; no_placeholders not a git work tree; ntpath.isreserved needs 3.13; 2x only model fake has /v1/messages; LEAD_DESK_LOAD_N measurement run; Windows-only reset (same list as EV7G).
- Stray files: no file with a control character in its name in the tree; tree differs from tree-R7I only by .ruff_cache after the run.

## Step 4: staged git copy (/home/user/build/rr6/tree-EV7I-stage, 310 tracked files), each file alone via t.sh
| file | result | rc |
|---|---|---|
| test_hygiene | 24 passed in 50.69s | 0 |
| test_nosemgrep_form | 114 passed in 1.47s | 0 |
| test_raw_bidi_chars | 3 passed in 0.10s | 0 |
| test_shell_single_bracket | 146 passed in 3.72s | 0 |
| test_file_call_guard | 11 passed in 1.72s | 0 |
| test_no_placeholders | 2 passed in 0.14s | 0 |
| test_gitleaks_exceptions | 44 passed in 13.90s | 0 |
| test_gitleaks_semgrep_lock | 4 passed in 8.15s | 0 |
After each file `git ls-files -o --exclude-standard` and `git ls-files -o` (minus .pyc) were EMPTY (no stray a/newline/b file). The stage copy held __pycache__ dirs copied from the frozen tree (ignored by .gitignore).

## Step 5: ruff 0.17.1 (/.cache/uv/archive-v0/ZEdxvAeJ4u4VOBJM/.../ruff, --no-cache, on tree-EV7I)
- `ruff check .`: All checks passed!, rc=0
- `ruff format --check .`: rc=0
