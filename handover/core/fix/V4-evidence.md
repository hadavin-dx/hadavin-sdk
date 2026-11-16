# V4 evidence (runner; no judging). Lead clock start 12:51Z, end ~13:00Z
Head sha (both trees): 61ded9ebdb17397904aa850830f3d9837114f8f7 + uncommitted patches. fix.patch sha256 d9c02df3134e8...e1fa.
lead_desk.__file__: /home/user/build/rr6/tree-V4old/src/lead_desk/__init__.py ; /home/user/build/rr6/tree-V4/src/lead_desk/__init__.py
Tree check: diff -rq V4old V4 differs only in README.md, docs/{hubspot-probe,real-services,settings,tests}.md, load_tools/README.md, scripts/{crash_desk.py,real-run.env.example}, + new tests/test_docs_match_tools.py.

| run | tree | file(s) | passed | failed | skipped | wall | hang |
|---|---|---|---|---|---|---|---|
| 1 | V4old (new test file copied in) | test_docs_match_tools.py | 2 | 5 | 0 | 10s | no |
| 2 | V4 | test_docs_match_tools.py | 7 | 0 | 0 | 10s | no |
| 3 | V4 | 14 touched files (list in touched-files.txt, incl. test_hygiene.py) | 1246 | 0 | 32 | 416s | no |
Skips in run 3: playwright not installed (e.g. test_portal_wording_and_masking.py:171,204,257), others in log.

## Fails-before (V4old)
FAILED q_form (doc lacks 'one line for each test'); FAILED page_states_number (docs/tests.md must say 'This tree holds N tests...': None);
FAILED crash_script_starts (desk child exited 1: RuntimeError the folder demo_only is missing); FAILED repeated_request_receipt (README text assertion); FAILED probe_checks_token_name (`--plan` does not look at the name not in docs/hubspot-probe.md).
PASSED on old: qq_form (tool-only check), two_texts_same_path (both old texts said `src`, so equal).

## Ruff (V4): ruff check: All checks passed (rc0); ruff format --check: 2 files already formatted (rc0)

## Mutation (copy of V4, one at a time, restored, diff -rq identical)
| test | mutant | killed | first error |
|---|---|---|---|
| q_form | docs/tests.md `N tests collected in S seconds`->`found` | yes | assert ('one line for each test' in ...) AssertionError |
| qq_form | pyproject addopts="-v" (tool side) | yes | AssertionError: ['tests/test_ai_after_claim.py::...'] |
| qq_form | docs/tests.md "with no total line"->"with a total line" | NO (survived; test does not read that sentence) | 1 passed |
| count | 3989->3988 | yes | docs/tests.md: the test count is out of date (3988==3989) |
| count | 97->96 files | yes | the test file count is out of date |
| two_texts | crash_desk.py docstring `src:.`->`src` | yes | assert 'src:.' == 'src' |
| crash_starts | docs/tests.md:26 `src:.`->`src` | yes | desk child exited with 1 ... demo_only is missing |
| repeated_request | README "can skip but are never reused"->"never skip" | yes | assert (...'"receipt_id": 3' in README...) failed |
| probe_checks | hubspot-probe.md `--plan` does not look at the name -> checks the name | yes | assert '`--plan` does not look...' in PROBE_PAGE |
Logs: out/V4/mut-*.log, run-*.log.
Not run: all other test files (full suite), Windows, playwright tests (not installed), no unshare used (tests are loopback-only).
