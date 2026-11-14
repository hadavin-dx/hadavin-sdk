# Doc patch D (text only). Patch: the .patch file next to this one
Commit on top of the 19-commit series (copy at <scratch>/tree, head 7f3afb7; after git am on a fresh copy: 835ab2b, same file content).
Rules used: R-numbers not looked up (no bible folder reachable from this task); preamble rules 5, 6, 14 applied. EGM skipped: wording-only doc patch, the lead runs the EGM step.

## Fix 1 GITLEAKS (README.md paragraph "The tests need development tools"; docs/tests.md new section "The gitleaks program", before "## Semgrep")
Old: README test paragraph ended "...read the list of tracked files with git)." and docs/tests.md had no section for the program.
New: README adds two sentences (Node/Chromium skip; gitleaks needed only with DPLD_REQUIRE_SCAN) and points to docs/tests.md. docs/tests.md: new section with when needed, version 8.30.1 (from .github/workflows/lint.yml GITLEAKS_VERSION), releases page of the project (words only), sha256sum -c on the archive with the release checksums file, unpack, GITLEAKS_BIN (path of the program) or PATH, then DPLD_REQUIRE_SCAN=1 python -m pytest -q.
Evidence: no gitleaks on PATH, no DPLD_REQUIRE_SCAN, python3.12 venv, `pytest tests/test_hygiene.py -q -rs` -> 20 passed, 4 skipped, rc=0; skip reasons "no gitleaks program on PATH (set GITLEAKS_BIN); set DPLD_REQUIRE_SCAN=1 to make this a failure" (lines 150, 343, 532) and "...(set GITLEAKS_BIN)" (579). So the lead's belief is confirmed. The same skip rule is in tests/test_gitleaks_exceptions.py and tests/test_gitleaks_semgrep_lock.py (read in code, reason text differs a little). With DPLD_REQUIRE_SCAN set and no program, tests/test_hygiene.py asserts "gitleaks binary not found: put it on PATH or set GITLEAKS_BIN" (read in code). NOT run: the full suite without the program (the 30 failures are the lead's number; I did not reproduce the count). NOT done: the actual download and checksum steps (no network use; steps are taken from lint.yml's own install step, with sha256sum --ignore-missing being the standard option, not run here).

## Fix 2 G2 crash scene (docs/tests.md, paragraph starting "The desk alone")
Old: "The desk alone: `PYTHONPATH=src python -m lead_desk.server`. The crash scene: ..."
New: inserted after the first sentence: stop the running desk with `kill "$(cat data/desk.pid)"` from the repository root (not scripts/reset.sh, which deletes the records); leave the demo server running; export DESK_LEADFLOW_FILE (demo: demo_only/leadflow.json) and DESK_NUDGE_TO (names only) before the crash scene and before a hand restart; restart with `PYTHONPATH=src:. python -m lead_desk.server`.
Evidence: read scripts/start_all.sh (sets both names, PYTHONPATH=src:., pid files under the database folder: desk.pid, fakes.pid) and scripts/crash_desk.py. Ran start_all.sh, feed, reset.sh in a scratch copy: rc=0. Started `python -m lead_desk.server` with PYTHONPATH=src and with src:. and no demo server: both print "cannot reach the demo servers" (so the restart command starts; the full restart with the demo server up was NOT run). The kill line itself was NOT run; the pid-file path comes from start_all.sh. Linux only; Windows not touched.

## Fix 3 G3 (README.md Linux and Windows quick start, webhook feed line)
Old: `# same person through the other door: "verdict": "duplicate"` / Windows `# same person, other door: "verdict": "duplicate"`
New: `... prints 200 (not 201) ... "verdict": "duplicate"` in both.
Evidence: ran start_all.sh keyed + feed form 1, form 1, webhook 1 on Linux: `201 new`, `201 ... replayed: true`, `200 {"verdict": "duplicate"...}`; outbox count 1; reset.sh rc=0. The Windows copy was NOT run; the status comes from the same server code.

## Fix 4 G5 (README.md Linux and Windows)
Old: `curl -i http://127.0.0.1:8765/counts # waits`, `curl http://.../counts`, `curl http://.../fake/outbox`
New: `curl -si ...` on the wait-loop command, `curl -s ...` on the two count/outbox lines; every other word kept (comment columns re-aligned by spaces only). The Windows block uses Invoke-WebRequest, no curl, so no change there. Not run with a terminal to compare progress-meter output; the flags are standard curl.

## Fix 5 G6 (README test paragraph, same added sentences as Fix 1)
Text: some tests need Node and a Playwright browser (Chromium); without them they are skipped, not failed; install steps in docs/tests.md section "Browser tests".
Evidence: docs/tests.md "Browser tests" says "Without them these tests are skipped, not failed"; run: tests/test_portal_wording_and_masking.py skipped 3 with "could not import 'playwright.sync_api': No module named 'playwright'". Node-missing skip not run (docs/tests.md names "node is not installed" lines).

## Fix 6 G8 (README.md Linux block)
Old: first line `python3 -m venv .venv && . .venv/bin/activate`
New: before it `python3 -V   # must print 3.12 or higher; if not, use python3.12 in place of python3 in the next line`. Windows unchanged.

## Test runs (one pytest at a time; rc from pytest itself)
- tests/test_hygiene.py, DPLD_REQUIRE_SCAN=1, GITLEAKS_BIN=<real 8.30.1 program>: 24 passed, rc=0 (so the repo's own scan accepts the new words). My added text has no link, host name, e-mail or 40+ character run; existing 127.0.0.1 lines were only edited by flags.
- gitleaks_exceptions, gitleaks_semgrep_lock, env_numbers, vendor_hosts, load_tools, path_confinement (same env): 866 passed, 1 skipped (needs Python 3.13), rc=0.
- portal_api, portal_mode, portal_wording_and_masking, scrub_n8n_export (no gitleaks env): 488 passed, 3 skipped (no playwright), rc=0.
- NOT run: the whole suite; no test pins the new wording (no test failed on old code because the new text is not tested).
- git am on a fresh copy of the frozen tree: applied (message "Applying: Docs: ..."), no error; README.md and docs/ identical to the working copy (diff rc=0). The am exit code itself was not captured separately (my slip); success is shown by the applied commit 835ab2b and the identical files.
Processes started were stopped (reset.sh ran; pgrep shows none).
