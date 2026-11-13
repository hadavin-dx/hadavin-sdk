# Docs and comments: make every number and promise match what the code and tests show

## What this changes

The desk is the lead-handling program in `src/lead_desk`. The reaper is its background job that puts stuck follow-ups back in line. This change touches text (documents, comments, docstrings) and almost nothing else.

Text only, apart from two small behaviour changes and one comment change listed below. Every sentence in the changed text (README, SECURITY, versions.md, contract.md, docs/*.md, workflow comments, and the docstrings that make a promise) that states a number, a guarantee, a command output or a test result was looked up in the code and the tests. Sentences that did not match were rewritten to what the code does. Sentences that could not be proved from this repository (results of earlier runs, outside facts) were deleted. A sentence that says "no test checks" or "read from the code" says in itself that it is not backed by a test.

This is a series of 19 commits, 41 files, 602 insertions and 547 deletions. Each commit says what it changes. Of the 41 files, 12 are documentation, 6 are workflow or settings files (comments only: four workflow files, `.coderabbit.yaml`, `requirements-semgrep.in`), and 23 are code files (comments and docstrings only, plus the two behaviour changes below).

| Kind of change | What was done |
|---|---|
| False or out-of-date sentences | rewritten to what the code does (for example a background pass can run longer than 55 s because the CRM-copy and reminder parts of the same pass each add their own time; a send timeout above 9 s is accepted, the call is still cut off at 9 s, and the value lengthens the wait before a stuck follow-up is put back; the exit codes of the desk; a repeated request does use up a receipt number and can start a due follow-up; the crash-script command needs `PYTHONPATH=src:.`) |
| Sentences about tests | every "no test checks ...", "not tested" and "tests/x.py checks ..." was searched against `tests/`: wrong denials were corrected (a test for a restart on one port exists; `tests/test_portal_api.py::test_foreign_host_is_refused_on_every_route` checks that a refused Host does not count) and citations that said more than the test asserts were narrowed |
| Numbers and names | a script compared the backticked names, paths, routes, constants, exit codes and numbers in the docs with the code (output: 1065 items, 1 explained mismatch); sentences found wrong, by the script or by readers, are fixed |
| What a command prints | sentences about what a command prints were corrected where a run showed a different output (no single log of those runs is kept); the commands that need Windows were not run on Windows |
| Results of earlier runs and outside facts | deleted where this repository cannot prove them (test counts of earlier runs, timings, the author's runs of the HubSpot probe, an independent rerun, the Semgrep run log) |
| Plain wording | the longest and most confusing paragraphs were split and the first-use terms defined |

## The code changes (nothing else changes behaviour)

1. `scripts/start_all.ps1`: an empty `DESK_LEADFLOW_FILE` is now treated like the shell script treats it (same condition as `start_all.sh`).
2. `tests/test_input_edge_cases.py`: one assertion is tightened from `in (1, 2)` to `== 1`: the test now requires the AI step to be asked exactly once when two threads drive the same follow-up (before: once or twice), with its docstring.
3. Comment only, no behaviour: `.github/workflows/lint.yml` and `sonar.yml`: the time-limit comment now says the same in both.

The other code files differ from main only in docstrings and comments (checked: the syntax tree of each is identical to main once docstrings and comments are ignored, except the one assertion above). The workflow files are equal to main when parsed as YAML.

## What was NOT done

* No code behaviour changed apart from items 1 and 2 (a start-up script condition and one test assertion; item 3 is a comment).
* Numbers that only a run can give (a full-suite time, an earlier pass count, the Semgrep run log) are no longer in the text; they are not replaced by new ones.
* Three tests were found that do not catch the behaviour the docs cited them for: `tests/test_portal_api.py::test_broken_extension_leaves_no_socket` (it shows that nothing is left listening, not the order of two lines in `make_server`), `tests/test_mirror_gate.py::test_the_copy_keeps_the_promised_waits_then_gives_up_and_leaves_no_entry` (it takes the expected waits from the constant, not from written-out values) and `tests/test_input_edge_cases.py::test_deeply_nested_json_is_bad_envelope` (on a scratch copy, removing both `except RecursionError` guards in `server.py` left this test passing: its nesting depth of 5000 does not reach the guard on Python 3.12.3, where the guard starts to matter at about 10000). The sentences now say what the tests assert. The three tests are not changed here: this series changes text only (apart from the one tightened assertion listed above and docstring or comment edits); they are named here so they can be fixed in a separate change.
* One behaviour difference was found and is not changed here (this series changes text only, so a behaviour change belongs in its own change; it is named here so it is not lost): a start-up without the background reaper drives pending follow-ups without waiting for their backoff (the server always starts the reaper first, so the server is not affected).

## Checks

Run on the final tree (main f3c39cf8 plus the 19 commits applied with `git am`; head commit 36dbb1060c3c5023e918344449730c5a56960a75; the resulting tree is identical to the build tree, tree hash 49d3c85938fe5323a3378a49195d3b8da434b3ca). The raw logs are kept outside this repository, in the author's handover folder `handover/demo/tools-claims/`.

* gitleaks 8.30.1 with the repository config: `dir`, `git` (all history) and `git` over f3c39cf8..HEAD: no leaks found (exit 0 each).
* `ruff check .`: exit 0. `ruff format --check .`: 159 files already formatted.
* `mypy --platform linux` and `mypy --platform win32`: no issues in 28 source files each.
* `bandit -ll -r src tools scripts -c pyproject.toml`: exit 0.
* `scripts/check_schema.py`: RESULT ALL PASS.
* Syntax-tree comparison with docstrings blanked: 21 of the 22 changed .py files are identical to main; the one different file is `tests/test_input_edge_cases.py` (the tightened assertion). YAML parse equality with main: the four workflows and `.coderabbit.yaml`.
* Link check over the docs on the final tree: 356 references found, 7 reported as broken (quoted section names that are not headings, and the placeholder file name `tests/test_name.py`); these 7 were not changed. Name and number check over the docs on the final tree: 1065 items, 1 mismatch, a deliberate test-name prefix in `docs/limits.md` (a full test name there would break the secret-scan rule on long tokens).
* Full suite, Python 3.12, loopback-only network, on the tree before the last round of wording fixes: 1 failed, 3878 passed, 4 skipped. The failure was `tests/test_path_confinement.py::test_v1_a_config_below_a_traverse_only_folder_is_refused_with_a_message_as_an_unprivileged_user` with `ModuleNotFoundError: No module named 'tools'`; that test runs as an unprivileged user and the clone folder had mode 700, so I take it as a fault of the run set-up (the clone folder is mode 755 in later runs). Python 3.13, same stage: 1 failed, 3713 passed, 169 skipped; the failure was `tests/test_hygiene.py::test_term_scan_finds_a_planted_term`, where `git commit` exited with status 128; I take the cause to be commit signing that needs the network (inferred; with signing switched off the hygiene tests pass). FULL-SUITE-FINAL-PLACEHOLDER
* Semgrep could not be run here (the rule registry is not reachable from the sandbox); the semgrep workflow was compared as YAML only.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
