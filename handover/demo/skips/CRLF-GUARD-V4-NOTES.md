# crlf-guard-v4.patch (applies on db54e13 and 2db3926; 4 files: .editorconfig, docs/tests.md, pyproject.toml, tests/test_hygiene.py; +228/-4)
Changes from v3:
- Cure text: `git checkout -- <file>` first (works everywhere, drops your edits), then a Python one-liner that keeps edits and turns CRLF and lone CR into LF. `sed -i` is gone from the message (GNU-only; leaves a lone CR: measured, evidence-b7-5). docs/tests.md says why.
- test_every_cure_in_the_message_works: takes the backtick commands out of the real guard failure, runs each on a planted file (CRLF, lone CR), asserts the guard passes and the file equals the LF text. `python` runs as sys.executable.
- test_gitleaks_on_a_planted_crlf_tree_names_the_file_and_the_cure (marker `gitleaks`, registered in pyproject.toml; `pytest -m gitleaks`; about 1 s on a two-file tree, not 50 s; skips without gitleaks, fails if DPLD_REQUIRE_SCAN is set). The scan call is now one helper, _gitleaks_scan, used by test_hygiene_scan_public too.
- Guard test parametrized over real file names for every LF_ONLY_FILES entry (names are hard-coded in the test, so cutting the list in code is seen); small tests for bad JSON, .PS1 case, empty-list safety assert.
Limits: N17, N18, M3b die only when gitleaks is present (measured: they survive without it). Cures not run on real Windows or macOS. Test file grew +221 lines (v3: +143).
Evidence: evidence-b7-1 (28 mutants), -3 (gates), -4 (apply matrix), -5 (cure measure).
