# Verifier output v4: /tmp/work/claims-pr-body.md against /tmp/final-series

Read-only check. Nothing run except git reads, a syntax-tree comparison script (/tmp/work/d/ast_cmp.py, outside the tree) and file reads. pytest NOT run. Bible and handoff files were not consulted (the brief is a read-only fact check; no R-numbers used).

Tree state: HEAD 11471ec1b10dcb76376bf8e76510bf42a5aaf6fe (17 commits after f3c39cf8). The working tree also has 15 uncommitted modified files (another agent is editing docs), so "the tree" and "HEAD" differ; committed-only numbers are given where they matter.

## What failed or is uncertain (first)
* FALSE (size-dependent, listed only): the body says 571 insertions. Committed HEAD gives 572 insertions and 528 deletions; the working tree currently gives 601 and 546.
* UNPROVEN: "stays green with both recursion guards removed" (no mutation run here, pytest not allowed).
* UNPROVEN: "each weak test is logged for a separate change" (no log file found in the tree; it may live in the studio folder, which was not searched).
* UNPROVEN: "a script and fresh readers went through every sentence" and "the Linux commands were run as written" (process claims; nothing in the tree records them).
* Not in the body but seen: the changed comment in src/lead_desk/desk.py:1354 now says "4401-digit number"; tests use 4301 digits (tests/test_server_hardening.py:82). The body lists this comment change nowhere. I did not check whether 4401 is correct.

## Table

| Sentence | Verdict | Evidence |
|---|---|---|
| The desk is the lead-handling program in `src/lead_desk` | TRUE | src/lead_desk/ exists (desk.py, server.py, gate.py ...) |
| The reaper is its background job that puts stuck follow-ups back in line | TRUE | src/lead_desk/constants.py:60-75 (reaper puts back a stuck `sending` row); server.py:1195 `desk.start_background()` |
| Text only, apart from two small behaviour changes and one comment change | TRUE | git diff f3c39cf8: the Python files are syntax-tree identical to main once docstrings/comments are ignored, except tests/test_input_edge_cases.py (DIFF, the one assertion); workflow and .coderabbit.yaml files parse to the same YAML as main (all 5 YAMLSAME); the only other non-text change is scripts/start_all.ps1:9 |
| A series of 17 commits | TRUE | `git log f3c39cf8..HEAD` = 17 |
| 41 files | TRUE | `git diff f3c39cf8 HEAD --name-only` = 41 (also 41 in working tree) |
| 571 insertions and 528 deletions | FALSE at HEAD (572 / 528); working tree 601 / 546; size-dependent, listed only | `git diff f3c39cf8 HEAD --shortstat` |
| 12 are documentation | TRUE | 12 .md files: README, SECURITY, contract, versions, docs/{hubspot-probe,limits,n8n-recipe,portal,real-services,settings,tests,why-this-code} |
| 6 are workflow or settings files (four workflow files, `.coderabbit.yaml`, `requirements-semgrep.in`) | TRUE | codeql.yml, lint.yml, semgrep.yml, sonar.yml, .coderabbit.yaml, requirements-semgrep.in |
| 23 are code files (comments and docstrings only, plus the two behaviour changes) | TRUE | 41-12-6 = 23: 1 .ps1, 22 .py (src 11, scripts 4, tests 6, load_tools 1, tools 1 -> 23 with ps1). Syntax-tree check: 21 of 22 .py identical, 1 differs by the assertion |
| Sentences that did not match were rewritten; unprovable ones deleted | UNPROVEN (process claim) | versions.md diff replaces run results with "No run result is stored here"; shows the pattern, not completeness |
| "no test checks" / "read from the code" sentences say a test does not back them | TRUE as a pattern | e.g. README.md:20 "(no test pins this)"; src/lead_desk/desk.py `_nudge_pass` docstring "(constants; no test of their values)" |
| A background pass can run longer than 55 s because the CRM-copy and reminder parts add their own time | TRUE | src/lead_desk/gate.py:30-35; docs/limits.md:73; 10+27+18=55 with REAPER_PASS_SECONDS 10 (gate.py:36), 3x CALL_DEADLINE_MAX 9 (constants.py:82); own clocks MIRROR_PASS_SECONDS/NUDGE_PASS_SECONDS 2.5 (gate.py:39-40) |
| A send timeout above 9 s is accepted, the call is still cut off at 9 s | TRUE | src/lead_desk/constants.py:82,116; config.py:521-522 (accepts up to 600); docs/settings.md:36 |
| The value lengthens the wait before a stuck follow-up is put back | TRUE | constants.py:116 comment "the stuck grace grows with it"; constants.py:68-70 (grace = send timeout + busy waits); docs/limits.md:49 |
| The exit codes of the desk (as rewritten) | TRUE | docs/limits.md:112 vs constants.py:25-32,256 (0,1,2,3,4,5; 137 for the simulated kill) and server.py:1127-1213 |
| A repeated request does use up a receipt number and can start a due follow-up | TRUE for the docs wording; the receipt-number part is stated as untested | README.md:20,38,105; docs/tests.md:116 ("no test pins the skipped number"; follow-up start via `_pending_and_due`). I did not trace the code path that skips the number |
| The crash-script command needs `PYTHONPATH=src:.` | TRUE | scripts/crash_desk.py:3; docs/tests.md:26 |
| "Every no-test denial and test citation was searched against tests/" | UNPROVEN (process claim) | not recorded in the tree |
| A test for a restart on one port exists | TRUE | tests/test_http.py:321 (restart on the same port), tests/test_portal_api.py:1458 `test_restart_same_port_portal_open` |
| `tests/test_portal_api.py::test_foreign_host_is_refused_on_every_route` checks that a refused Host does not count | TRUE | tests/test_portal_api.py:1019,1044-1045 (`receipts` count 0 and `rejected_envelopes() == 0`) |
| Citations that said more than the test asserts were narrowed | UNPROVEN (process claim) | not checkable without the old text per sentence |
| A script and readers compared every backticked name, path, route, constant, default, exit code and number; a handful were wrong and fixed | UNPROVEN (process claim) | not recorded in the tree |
| Linux commands in the docs were run as written; Windows commands were not run on Windows | UNPROVEN | docs/tests.md:26 says "the Linux form was run, the Windows form was not run", but no run record exists in the tree |
| Results of earlier runs deleted (test counts, timings, author's HubSpot probe runs, independent rerun, Semgrep run log) | TRUE in the examples I could see | git diff versions.md (run result removed), docs/hubspot-probe.md (54 lines changed, -), requirements-semgrep.in, sonar.yml comment "message as quoted by the author; not checked here" |
| The longest paragraphs were split, first-use terms defined | UNPROVEN (judgement) | README.md:42 now defines "Crash point"; not measured elsewhere |
| Code change 1: `scripts/start_all.ps1` treats an empty `DESK_LEADFLOW_FILE` like the shell script (same condition as `start_all.sh`) | TRUE | scripts/start_all.ps1:9 adds `-not [string]::IsNullOrEmpty(...)`; scripts/start_all.sh:17 `-n "$DESK_LEADFLOW_FILE"`. Not run on Windows |
| Code change 2: assertion tightened from `in (1, 2)` to `== 1`, with its docstring | TRUE | tests/test_input_edge_cases.py (diff above); docstring points to tests/test_ai_after_claim.py, which exists |
| Code change 3: lint.yml and sonar.yml time-limit comment says the same in both; comment only | TRUE | both lines read "60 minutes on purpose: the run time on a hosted runner is not measured yet; after real runs, set it to 1.6 times the longest observed run"; YAML parses equal to main |
| Other code files differ from main only in docstrings and comments (AST identical) | TRUE | /tmp/work/d/ast_cmp.py: 21 files SAME, test_input_edge_cases.py DIFF (the assertion). Note: stripping only docstrings; plain comments are not in the syntax tree anyway |
| Workflow files are equal to main when parsed as YAML | TRUE | script: codeql, lint, semgrep, sonar, .coderabbit.yaml all YAMLSAME |
| No code behaviour changed apart from items 1 and 2 | TRUE (given the two checks above) | same evidence |
| Numbers that only a run can give are no longer in the text, not replaced by new ones | UNPROVEN | spot-checks consistent (versions.md, hubspot-probe.md); no full scan done |
| `test_broken_extension_leaves_no_socket` shows that nothing is left listening, not the order of two lines in `make_server` | TRUE | tests/test_portal_api.py:1549-1560 (patches `load_demo_portal` to raise, then binds the port) |
| `test_the_copy_keeps_the_promised_waits...` takes the expected waits from the constant, not written-out values | TRUE | tests/test_mirror_gate.py:115-135 builds `starts` from `MIRROR_RETRY_WAIT_SECONDS` (constants.py:159); the comment `# 0, 10, 70, 250, 670` is not asserted literally |
| `test_deeply_nested_json_is_bad_envelope` stays green with both recursion guards removed | UNPROVEN | test is at tests/test_input_edge_cases.py:26; guards at src/lead_desk/server.py:971 and desk.py:1353 (plus server.py:913/938 for resolve). Needs a mutation run |
| The sentences now say what the tests assert | UNPROVEN (judgement) | not checked sentence by sentence |
| The tests are not changed here (only text) | FALSE in a narrow sense | tests/test_input_edge_cases.py assertion is changed (item 2), plus docstring/comment edits in 6 test files; the sentence means "those three tests", which is TRUE: none of the three was touched |
| Each weak test is logged for a separate change | UNPROVEN | no log in the repository |
| A start-up without the background reaper drives pending follow-ups without waiting for backoff; the server always starts the reaper first | TRUE | contract.md:327,336; src/lead_desk/server.py:1195 (`start_background()` before startup) |
| Results "filled in from the final tree (main f3c39cf8 plus the 17 commits, applied with `git am`)"; `RESULTS-PLACEHOLDER` | FALSE / not done yet | the body still contains the literal `RESULTS-PLACEHOLDER`; the tree has uncommitted edits, so it is not yet a "final tree" of exactly 17 commits; `git am` use is not checkable |
| Ends with the Claude Code line | TRUE | claims-pr-body.md:41 |

## Not checked
* pytest, ruff, bandit, any mutation run (not allowed).
* Windows behaviour of start_all.ps1.
* Every other sentence inside the 12 documents; I checked the sentences the body names, not all of them.
* Studio bible, memory and handoff files (not needed for this read-only check).

## Files written
/tmp/work/d/out-v4.md (this file), /tmp/work/d/ast_cmp.py (helper script, outside the tree). Nothing under /tmp/final-series was edited. No processes left running. Head SHA of the tree read: 11471ec1b10dcb76376bf8e76510bf42a5aaf6fe (plus 15 uncommitted modified files).
