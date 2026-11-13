# G3 cross-check of /tmp/work/claims-pr-body.md (read-only; EGM skipped: read-only question)
Sources used: /tmp/review-tree and /tmp/final-series only (/tmp/v8work not read). `diff -rq` of the two trees (excluding .git) prints nothing: identical content. HEAD SHAs differ (review-tree 061f6f4, final-series 46d3093); the body names no SHA, so no claim is affected.

| Claim | Derived | OK/WRONG |
|---|---|---|
| 16 commits (f3c39cf8..HEAD) | `git log --oneline` gives 16 in both trees | OK |
| 31 files | `git diff --stat`: 31 files changed | OK |
| 490 insertions, 432 deletions | 490 / 432 (also summed from --numstat) | OK |
| 12 documentation files | 12 .md files (README, SECURITY, contract, versions, 8 under docs/) | OK |
| 4 workflow files (comments only) | codeql, lint, semgrep, sonar; each parses to identical YAML as main | OK |
| 15 code files | 14 .py + scripts/start_all.ps1 = 15 | OK |
| Other code files differ only in docstrings/comments (AST identical to main) | 13 .py files: AST identical with docstrings blanked; tests/test_input_edge_cases.py differs (the assertion). check_schema, hubspot_probe, reset_check, catcher, constants, db, desk, gate, imap_count, live_claude, loader, run_stats, trace all AST-same | OK |
| start_all.ps1 empty DESK_LEADFLOW_FILE treated like the shell script | ps1 line now adds `-not [string]::IsNullOrEmpty($env:DESK_LEADFLOW_FILE)`; start_all.sh line 17 has `[[ -n "$DESK_LEADFLOW_FILE" ]]` | OK (not run on Windows) |
| test assertion `in (1, 2)` -> `== 1` with docstring | diff shows `assert rig.qualifier.calls == 1` and new docstring | OK |
| lint.yml and sonar.yml time-limit comment says the same in both | both now read "# 60 minutes on purpose: ... set it to 1.6 times the longest observed run" (identical text) | OK |
| Item 3 is "comment only" as the only workflow change | lint.yml and sonar.yml also have other comment edits (secret wording, gitleaks, pip note); codeql/semgrep comments too. All YAML-equal to main | OK (wording of item 3 names only one of several comment edits) |
| Test files | `ls tests/test_*.py | wc -l` = 92 (body states no count) | n/a |
| test_broken_extension_leaves_no_socket in tests/test_portal_api.py | exists, line 1549 | OK |
| test_the_copy_keeps_the_promised_waits_then_gives_up_and_leaves_no_entry in tests/test_mirror_gate.py | exists, line 115 | OK |
| test_deeply_nested_json_is_bad_envelope in tests/test_input_edge_cases.py | exists, line 26 | OK |
| "a test for a restart on one port exists" | test_restart_same_port_portal_open, tests/test_portal_api.py:1458 | OK |
| "tests/test_http_guard.py has a test that a refused Host does not count" | test_http_guard.py has 3 tests (URL scheme, http address tried, scan covers scripts/); none about Host. The Host test is tests/test_portal_api.py::test_foreign_host_is_refused_on_every_route (line 1019, asserts rejected_envelopes() == 0 at line 1044). docs/limits.md line 104 states the not-counted rule but cites no file | WRONG (file name) |
| "main f3c39cf8 plus the 16 commits" | base f3c39cf8 resolves; 16 commits | OK |
| RESULTS-PLACEHOLDER still present | unfilled; the Checks section has no results yet | OPEN |

Test names cited in the added text (111 distinct test_* / tests/*.py tokens in the diff): all resolve to a file or function. Three tokens (test_all_unknown_book_*, test_two_messages_to_one_address_*, test_a_message_text_that_*) are wildcard prefixes that match real functions in tests/test_load_tools.py (lines 213, 342, 352); tests/test_name.py::test_name in docs/tests.md:88 is a deliberate placeholder.

Not checked: Windows behaviour of start_all.ps1; the pass/fail claims about running commands; the 11 other claims in the body table that need a run.
R-numbers: none cited (read-only diff comparison; bible not consulted).
