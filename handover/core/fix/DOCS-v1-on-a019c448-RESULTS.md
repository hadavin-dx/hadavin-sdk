# DOCS RESULTS (builder-claimed only; nothing independent has checked this)

Base: frozen tree, `git rev-parse HEAD^{tree}` = a019c44835f26e0ef314129d7d92a047eb67d1b8 (checked on the original and on every fresh copy). Work tree: /home/user/build/rr6/tree-DOCS (copy; original untouched). Deliverable: out/DOCS/docs-on-frozen.patch (456 lines, 10 files changed + new tests/test_docs_match_tools.py; sha256 b0069c2a...8179d).

## Failed, uncertain, not done (first)
1. **My slip:** the first 8-file docs-reader run had 1 failure, `tests/test_hygiene.py::test_hygiene_scan_public`: the test name I cited in docs/tests.md (59 characters) matches the pattern for a 40+ character token (`[A-Za-z0-9+/=_-]{40,}`). Fixed by renaming the test to `test_a_repeat_uses_up_a_receipt_number` (38 characters). After the fix I re-ran only test_hygiene.py (20 passed, 4 skipped) and the docs test (3 times); **the full 8-file reader set was not re-run after the rename** (it takes 5 min 41 s; the earlier run before the rename: 1 failed (this one), 206 passed, 27 skipped).
2. **Not run:** any CI, Windows, macOS, gitleaks (4 hygiene tests skip: no gitleaks program here), `bandit -ll`, the full test suite, any browser test (no playwright in this venv; they skip), mutation runs of code (I changed no code).
3. **Dropped on purpose, lead may disagree:** the test-count sentence, the three count tests, `DPLD_REQUIRE_COUNT` (workflows and settings bullet) and the 3 surviving mutants of it. Reason: the frozen series deleted the count sentence and says "no count of collected tests is stored" (docs/limits.md:62); a switch that guards no test would be dead config. Consequence: step (3) as ordered (the 3 mutants in docs/settings.md) **cannot be done as stated: those sentences do not exist in the frozen docs.** Instead I killed 7 analogous doc/config mutants (below).
4. **N/A:** `scripts/precheck.py` does not exist in the frozen tree, so its test and README note are dropped.
5. Some of my doc additions are "read from the code, not run" and say so in the text: full paths for the real-run config (`cwd=REPO`), key file reopened per CRM call, password file reopened per send.
6. 2 pytest processes of another agent were running on the machine at the end (started 14:28, `tests/test_book_f...`); not mine, left alone. Mine: 0 left.

## What changed (tree-DOCS vs frozen)
- docs/hubspot-probe.md: `--token-env` refusal order (catch 1). contract.md:323: 5-second wait for follow-ups given back for lack of resources (catch 2).
- README.md (4 places), docs/tests.md P1 row: the repeat uses up a receipt number; steps show `"receipt_id": 3`; "no test pins this" removed (a test pins it).
- docs/real-services.md: byte-order mark, full paths, `--assume-yes`. docs/settings.md: when the HubSpot key file / mail password file are opened.
- load_tools/README.md: the "A whole run" recipe re-added; I ran it on a copy of the frozen tree (`unshare -n`, loopback): exit code 0, 30 requests, 24 request numbers, 21 leads, 21 mails, 7 checks PASS (work/recipe-run.log; log not shipped, said so in the text; not repeated by any test).
- scripts/crash_desk.py (docstring only), versions.md and docs/limits.md (92 -> 93 test files, because our file is the 93rd).
- tests/test_docs_match_tools.py: 14 tests (10 adapted/kept, 4 new: byte-order mark, `--assume-yes`, `cwd=REPO`, workflow DPLD_REQUIRE_DEMO value; file-count test replaces the collector tests).
Details per hunk: HUNKS.md. Real mismatches found: CATCHES.md (**2 real, 4 gaps**).

## Evidence (commands, outputs in out/DOCS/)
- Run recipe: `TMPDIR=<outside> PYTHONPATH=<tree>/src PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_*(gpgsign off) unshare -n python lo_up-q4g.py python -m pytest -q -p no:cacheprovider -rfs ...` (work/run.sh); `lead_desk.__file__` printed earlier = /home/user/build/rr6/tree-DOCS/src/lead_desk/__init__.py.
- tests/test_docs_match_tools.py with DPLD_REQUIRE_COUNT=1, three runs (run3.log): `14 passed in 1.64s`, `14 passed in 1.65s`, `14 passed in 1.99s`. (The variable is no longer read by anything; kept only because the order named it.)
- Fail before (failing-before.log): same test file, frozen docs without our doc fixes (docs/scripts/versions/README restored, test file kept): **10 failed, 4 passed**. Honest note: 2 of the 10 are real tool-vs-doc mismatches (catches 1, 2); the other 8 fail because the page lacks a sentence or number the test pins (gaps, or the 93 count).
- Mutants (mutants.log), each run in a scratch copy of tree-DOCS, all KILLED (1 failed, 13 passed): M1a settings.md "both set it to 1" -> 0; M1b lint.yml `DPLD_REQUIRE_DEMO "1"` -> "0"; M2 remove the `--plan` clause; M3 BOM message text changed; M4 remove the 5-second clause; M5 `"receipt_id": 3` -> 2; M6 versions.md 93 -> 92. 0 survived. (These replace the 3 count mutants, see item 3.)
- docs-reading files the frozen series changed, plus others that read docs (readers.log; 8 files: test_gitleaks_exceptions, test_hygiene, test_infra, test_input_edge_cases, test_portal_wording_and_masking, test_real_check_dry, test_portal_mode, test_clock_steps): `1 failed, 206 passed, 27 skipped in 340.89s`; the 1 failure is item 1, fixed; hygiene re-run after the fix: `20 passed, 4 skipped in 45.64s`.
- ruff on the whole tree (repo pyproject): `ruff check .` All checks passed; `ruff format --check .` 160 files already formatted.
- Patch: `git apply --check` on a fresh copy of the frozen tree: OK (tree hash a019c448... on the copy); after applying, `diff -rq --exclude=.git --exclude=__pycache__` against tree-DOCS: no difference. (__pycache__ folders exist in tree-DOCS only; ignored by git, not in the patch.)

## Step 6 (report only)
core-fix-v1.patch does **not** apply to the frozen tree: `git apply --check` exit 1; 30 of 120 hunks reject in 15 files, 3 files missing. List: CODE-ON-FROZEN.md. Not resolved.

## Files (all in /home/user/build/rr6/out/DOCS/)
docs-on-frozen.patch, HUNKS.md, CATCHES.md, CODE-ON-FROZEN.md, RESULTS.md, checkpoint.md, failing-before.log, run3.log, readers.log, mutants.log, work/ (scripts, recipe log). Work tree: /home/user/build/rr6/tree-DOCS.
