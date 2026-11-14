# lane3-fix-9 notes (builder B9)

Base: f3c39cf89ec989f032ea48a23cfd824b88da9c68. Worktree: /home/user/work/m6-tree (changes added, not committed).
Patch: evidence/lane3-fix-9.patch (git diff --cached --binary f3c39cf8). Nothing committed or pushed.

## Problem and class
A full test run left an empty git-ignored `data/` folder in the repo root: three tests made `<repo>/data` and removed only
their own `reset-*` subfolder. Class: a test creates a shared folder it does not own and never removes it.

## What changed
- ONE source of truth (lead order 03:19Z): the helper `book_folder_in_repo(prefix)` was copied BYTE FOR BYTE from
  core patch `core-fix-on-frozen-r7e.patch` (copy at evidence/core/, sha256
  89ca3a2ddeba2a1a1c006d32a38520643861aa94848730b8fcdcf1a46457cee8, lines 6838-6855) into tests/support.py.
- Difference from core: my base tests/support.py had no `import shutil` and no `import tempfile`; I added those two
  imports (the helper text is unchanged). The core patch is on a much later base, so only the helper was taken, not the rest.
- Call sites now use it: tests/test_reset_scripts.py (test_reset_still_deletes_a_database_inside_the_data_folder and the
  `book` fixture), tests/test_mode_safety.py (test_reset_sh_refuses_when_ps_is_missing). Unused `tempfile` import removed
  from both.
- My own first helper (tests/data_folder.py) was deleted; it is not in the patch.
- New tests/test_data_folder_helper.py: absent-before means absent-after; pre-existing empty data/ kept; data/ holding a
  file untouched; data/ filled by someone else kept; folder removed when the body fails; a repo-wide guard that runs
  test_reset_scripts.py and test_mode_safety.py in a copy of the repo (git ls-files, fallback folder list) and asserts no
  data/ exists in the copy afterwards; a symlink test (below). The helper tests point `support.REPO` at tmp_path so the
  real repo is never touched.
- Symlink test: `test_a_data_folder_that_is_a_link_is_not_followed` is `xfail(strict=True)`, because the copied core helper
  follows a pre-existing `data` symlink (core's own independent review finding; core r7f is fixing it). This is a
  DIFFERENCE FROM CORE'S CURRENT BEHAVIOUR, reported, not hidden: I did not edit the helper. When core r7f lands: re-copy
  the helper byte for byte, remove the xfail mark, and the test must pass (strict xfail makes the run fail on its own
  when the helper is fixed, so the mark cannot be forgotten).

## Siblings searched
grep over tests, scripts, tools, src for `mkdir`, `chdir`, `Path("data")`, `./data`, `"data"`: other than the three sites,
none creates a folder under the repo root. All `monkeypatch.chdir` calls are restored by pytest. Other `data` hits use
tmp_path or are unrelated (portal route names, JSON keys). Not searched: files outside tests/scripts/tools/src.

## Fails before (raw)
- raw/b9-fails-before.log (first helper version) and raw/b9-fails-before2.log (core helper): on the base tree plus only the
  new test file and the helper, the guard fails: "assert True is False ... copy/data exists". The helper unit tests are for a
  new helper, so they cannot fail on old code; the guard is the test that proves the old three tests leave data/.
## Passes after (raw)
- raw/b9-new-313.log, raw/b9-new-312.log: first helper version, 93 passed 8 skipped each.
- raw/b9-new2-313.log: core helper, 92 passed 1 failed (my own wrong check in the symlink test, XPASS strict); fixed;
  raw/b9-link.log after the fix: 1 passed 1 xfailed.
- raw/b9-three-313.log and raw/b9-three-312.log: three files on a clean copy (/home/user/work/m6-chk, patch applied): see RESULTS below.
## Line length
awk >120: only pre-existing long lines (support.py base had 1; test_mode_safety has 1 that I did not check against base). New lines are within 120.
No ruff/mypy/bandit run (CI only).

## RESULTS
NOT FINISHED at hand-back time (03:24Z): the full serial run (raw/b9-full-313.log, ends with an rc= line) and the three-file reruns (raw/b9-three-313.log, raw/b9-three-312.log) were still running. No full-suite counts and no after-full-run data/ check exist yet. Read those logs for the result.

## NOT DONE / NOT CHECKED
- GITLEAKS_BIN run: not attempted (optional); the 30 gitleaks-binary failures are expected without it.
- ruff, bandit, mypy, gitleaks: not run by order; the new test file and imports are unchecked by ruff (e.g. import order, S603 notes).
- Windows path of the helper and the PowerShell reset script: not run (Linux only).
- The test_mode_safety line-length hit against base: not compared.
- A stray /helper.txt (865 bytes, root) was created by a mistaken command of mine; removal is blocked by the safety check; a person must delete it.

## WHAT I WOULD DO NEXT (ranked 3)
1. When core r7f lands, re-copy the helper byte for byte, drop the xfail mark, re-run the three files.
2. Run ruff/bandit on CI and fix findings in tests/test_data_folder_helper.py.
3. Apply the same clean-tree guard to the whole suite (assert git status --ignored unchanged after a full run) as a final fixture.
