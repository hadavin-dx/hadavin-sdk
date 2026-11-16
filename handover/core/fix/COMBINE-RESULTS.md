# COMBINE RESULTS (builder; tree /home/user/build/rr6/tree-COMBINE; nothing pushed; baseline tree-EV = 9f5dc1f in the copy)

FAILED / NOT CHECKED FIRST
- Full suite NOT run (as instructed). Only the 13 test files below were run.
- gitleaks is not installed: the gitleaks parts of tests/test_hygiene.py are SKIPPED (4 skips). The literal-scan part now passes.
- Mutation checks, Windows (.ps1 scripts) and the other 20+ existing test files that touch the same code: NOT run by me.
- Two real problems found while combining (both fixed, see CONFLICTS.md): (a) tests/test_cli_refusals.py:327 (F2) pinned
  "JSONDecodeError" but F1b's shared reader now gives "FileRefused": first run 1 failed / 492 passed, expectation updated
  (same behaviour, not weakened); (b) F2b's comment made scripts/run_live_check.py:192 140 chars (ruff E501): shortened.
- Order deviation: applied F1, F3, F1b (not F1, F1b, F3): F1b needs F3's regfile.py.

HYGIENE (asked fix)
- Before: hygiene-before.log: `1 failed, 20 passed, 3 skipped` (test_hygiene_scan_public: literals in
  tests/test_special_files_and_plain_text.py lines 156-194, and ALSO tests/test_file_reader_refusals.py:136 where "try:\n"
  matched the drive-path pattern).
- After: hygiene-after.log: `20 passed, 4 skipped` (the extra skip is the same test now reaching its gitleaks step; no gitleaks program).
  Addresses are built from HTTP = "http" + "://" / HTTPS = "https" + "://"; test meaning unchanged.

TESTS ON THE FINAL HEAD (tests-final.log): `522 passed, 5 skipped, 41 warnings in 164.24s`
Command: TMPDIR=/home/user/build/rr6/tmpC PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<tree>/src venv-br/bin/python -m pytest -q -p no:cacheprovider -rfs
 <13 files> run under `unshare -n` + drivers/lo_up-q4g.py. lead_desk.__file__ = tree-COMBINE/src/lead_desk/__init__.py.
Files: test_script_refusals_feed (F1), test_file_reader_refusals (F1b), test_cli_refusals (F2), test_special_files_and_plain_text (F3),
 test_special_output_files, test_wrapper_setting_refusals, test_reset_scripts (F6), test_n8n_api_url, test_survivor_r20_config_read,
 test_sonar_p2_feed_optional, test_core_key_readers (existing, changed by patches), test_hygiene, test_clock_steps.
 Earlier runs: tests-new.log (1 failed, 492 passed, 5 skipped, before fix 9 of CONFLICTS.md), tests-cli-after-fix.log (126 passed), tests-clock.log (29 passed).
 Skips = 4 gitleaks (test_hygiene) + 1 (test_n8n_api_url.py:512, needs a non-root user).
LINT: ruff.log: `ruff check .` All checks passed; `ruff format --check .` 176 files already formatted (repo config, line length 120).
BANDIT: `bandit -ll -r src tools scripts` rc=0, High 0, Medium 0 (9 Low shown, below the -ll bar). bandit.log.

PATCH
- out/COMBINE/core-fix-v1.patch: 3569 lines, 48 files (git diff --cached --binary vs tree-EV, new files included), 2297 insertions, 174 deletions.
- sha256 e0458dda3836ad814e58836e2e51f203888034935ecdffdc2972b473de1401cb
- Verified: fresh copy of tree-EV + `git apply --check` + `git apply` ok; `diff -rq --exclude=.git` fresh vs tree-COMBINE: no difference (rc 0), after removing my own .ruff_cache/__pycache__/empty data dir from tree-COMBINE.
- Files list: files.txt (new: scripts/desk_setting.py, scripts/refusals.py, src/lead_desk/regfile.py, tools/refusing_args.py, 6 new test files: test_cli_refusals, test_file_reader_refusals, test_script_refusals_feed, test_special_files_and_plain_text, test_special_output_files, test_wrapper_setting_refusals).
- Shared helpers: one definition each: regfile.py (read + write opener), tools/refusing_args.py (refusal line, codes, parser; scripts/refusals.py only re-exports).
Processes: none of mine left running. Rules cited: R448 (config+glue, no new component), least privilege (no new identity), no secrets (fake keys from parts in tests). No EGM review run by me (builder; the lead runs EGM).
