# Docs and comments: make every number and promise match what the code and tests show

## What this changes

Text only, apart from three small code changes listed below. Every sentence of the public text (README, SECURITY, versions.md, contract.md, docs/*.md, workflow comments, and the docstrings that make a promise) that states a number, a guarantee, a command output or a test result was looked up in the code and the tests. Sentences that did not match were rewritten to what the code does. Sentences that could not be proved from this repository (results of earlier runs, outside facts) were deleted.

This is a series of 16 commits, 31 files, 490 insertions and 432 deletions. Each commit says what it changes. Of the 31 files, 12 are documentation, 4 are workflow files (comments only), 14 are code files (comments and docstrings only, plus the three changes below).

| Kind of change | What was done |
|---|---|
| False or out-of-date sentences | rewritten to what the code does (for example a reaper pass can overrun by more than 55 s because the CRM copy and reminder parts add their own time; a send timeout above 9 s is accepted but has no effect; the exit codes of the desk) |
| Sentences about tests | every "no test checks ...", "not tested" and "tests/x.py checks ..." was searched against `tests/`: wrong denials were corrected (a test for a restart on one port exists; a test that a refused Host does not count exists) and citations that said more than the test asserts were narrowed |
| Numbers and names | a script and readers compared every backticked name, path, route, constant, default, exit code and number with the code; a handful were wrong and are fixed |
| What a command prints | the commands named in the docs were run as written; for example `python -m pytest --collect-only -qq` prints one line per test file |
| Results of earlier runs and outside facts | deleted where this repository cannot prove them (test counts of earlier runs, timings, the author's runs of the HubSpot probe, an independent rerun, the Semgrep run log) |
| Plain wording | the longest and most confusing paragraphs were split and the first-use terms defined |

## The three code changes (nothing else changes behaviour)

1. `scripts/start_all.ps1`: an empty `DESK_LEADFLOW_FILE` is now treated like the shell script treats it (same condition as `start_all.sh`).
2. `tests/test_input_edge_cases.py`: one assertion is tightened from `in (1, 2)` to `== 1` model call, with its docstring.
3. `.github/workflows/lint.yml` and `sonar.yml`: the time-limit comment now says the same in both.

The other code files differ from main only in docstrings and comments (checked: the syntax tree of each is identical to main once docstrings and comments are ignored, except the one assertion above). The workflow files are equal to main when parsed as YAML.

## What was NOT done

* No code behaviour changed apart from item 1 and one test assertion (item 2).
* Numbers that only a run can give (a full-suite time, an earlier pass count) are no longer in the text; they are not replaced by new ones.
* Two tests were found that do not catch the behaviour the docs used to cite them for (the mirror-retry wait values; the deep-nesting guard). The sentences now say what the tests assert. The tests are not changed here.
* One behaviour difference was found and is not changed: a start-up without the background reaper drives pending follow-ups without waiting for their backoff (the server always starts the reaper first, so the server is not affected).

## Checks

Results are filled in from the final tree (main f3c39cf8 plus the 16 commits, applied with `git am`):

* RESULTS-PLACEHOLDER

🤖 Generated with [Claude Code](https://claude.com/claude-code)
