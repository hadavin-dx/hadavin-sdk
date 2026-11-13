# Docs and comments: make every number and promise match what the code and tests show

## What this changes

Text only, apart from two small behaviour changes and one comment change listed below. Every sentence of the changed text (README, SECURITY, versions.md, contract.md, docs/*.md, workflow comments, and the docstrings that make a promise) that states a number, a guarantee, a command output or a test result was looked up in the code and the tests. Sentences that did not match were rewritten to what the code does. Sentences that could not be proved from this repository (results of earlier runs, outside facts) were deleted. A sentence that says "no test checks" or "read from the code" says in itself that it is not backed by a test.

This is a series of 17 commits, 41 files, 571 insertions and 528 deletions. Each commit says what it changes. Of the 41 files, 12 are documentation, 6 are workflow or settings files (comments only: four workflow files, `.coderabbit.yaml`, `requirements-semgrep.in`), and 23 are code files (comments and docstrings only, plus the two behaviour changes below).

| Kind of change | What was done |
|---|---|
| False or out-of-date sentences | rewritten to what the code does (for example a reaper pass can overrun by more than 55 s because the CRM copy and reminder parts add their own time; a send timeout above 9 s is accepted but has no effect; the exit codes of the desk; a repeated request does use up a receipt number and can start a due follow-up; the crash-script command needs `PYTHONPATH=src:.`) |
| Sentences about tests | every "no test checks ...", "not tested" and "tests/x.py checks ..." was searched against `tests/`: wrong denials were corrected (a test for a restart on one port exists; `tests/test_portal_api.py::test_foreign_host_is_refused_on_every_route` checks that a refused Host does not count) and citations that said more than the test asserts were narrowed |
| Numbers and names | a script and readers compared every backticked name, path, route, constant, default, exit code and number with the code; a handful were wrong and are fixed |
| What a command prints | the Linux commands named in the docs were run as written and the sentences about what they print were corrected; the commands that need Windows were not run on Windows |
| Results of earlier runs and outside facts | deleted where this repository cannot prove them (test counts of earlier runs, timings, the author's runs of the HubSpot probe, an independent rerun, the Semgrep run log) |
| Plain wording | the longest and most confusing paragraphs were split and the first-use terms defined |

## The code changes (nothing else changes behaviour)

1. `scripts/start_all.ps1`: an empty `DESK_LEADFLOW_FILE` is now treated like the shell script treats it (same condition as `start_all.sh`).
2. `tests/test_input_edge_cases.py`: one assertion is tightened from `in (1, 2)` to `== 1` model call, with its docstring.
3. Comment only, no behaviour: `.github/workflows/lint.yml` and `sonar.yml`: the time-limit comment now says the same in both.

The other code files differ from main only in docstrings and comments (checked: the syntax tree of each is identical to main once docstrings and comments are ignored, except the one assertion above). The workflow files are equal to main when parsed as YAML.

## What was NOT done

* No code behaviour changed apart from items 1 and 2 (a start-up script condition and one test assertion; item 3 is a comment).
* Numbers that only a run can give (a full-suite time, an earlier pass count, the Semgrep run log) are no longer in the text; they are not replaced by new ones.
* Three tests were found that do not catch the behaviour the docs cited them for: `tests/test_portal_api.py::test_broken_extension_leaves_no_socket` (it shows that nothing is left listening, not the order of two lines in `make_server`), `tests/test_mirror_gate.py::test_the_copy_keeps_the_promised_waits_then_gives_up_and_leaves_no_entry` (it takes the expected waits from the constant, not from written-out values) and `tests/test_input_edge_cases.py::test_deeply_nested_json_is_bad_envelope` (it stays green with both recursion guards removed). The sentences now say what the tests assert. The tests are not changed here.
* One behaviour difference was found and is not changed: a start-up without the background reaper drives pending follow-ups without waiting for their backoff (the server always starts the reaper first, so the server is not affected).

## Checks

Results are filled in from the final tree (main f3c39cf8 plus the 17 commits, applied with `git am`):

* RESULTS-PLACEHOLDER

🤖 Generated with [Claude Code](https://claude.com/claude-code)
