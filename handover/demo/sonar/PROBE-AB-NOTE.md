# probe-ab.patch: one draft PR, two sanitizer shapes at once

Patch: `sonar/probe-ab.patch` (applies on db54e13 alone and after P1, P1v2 and P2; `git apply --check` measured, see evidence-p3v2-7-probe-ab.txt). Push it as a separate draft PR to main, then read the Sonar flows with:
`https://sonarcloud.io/api/issues/search?componentKeys=hadavin-dx_duplicate-proof-lead-desk-n8n&pullRequest=<new PR>&resolved=false&rules=pythonsecurity:S8707,pythonsecurity:S8706&additionalFields=_all`
I cannot see any Sonar result. Everything below says what to LOOK FOR, not what will happen.

## Naming (the earlier single-function probes use other letters; do not mix them up)
* In THIS patch: shape A = the helper form (a call to `tools/pathconfine.confine`, new file in the patch; it resolves the path, checks the allowed folders, then rebuilds the path from a directory listing, so the returned text is the file system's, not the argument's; a NEW output file's name is rebuilt from a table of allowed characters). Shape B = inline realpath + commonpath check + raise + open(real), in the same function, no helper.
* sonar-p3-probe-a.patch (read_jsonl only) = inline realpath + commonpath + raise + open(real) = the SAME shape as B here. sonar-p3-probe-b.patch (read_jsonl only) = inline walk through os.scandir listings = the shape of helper A here, without the helper call.

## Which flagged line gets which shape (lines are those of issues-pr4-0253.json, base db54e13)
| flagged line | rule | function | shape in this patch |
|---|---|---|---|
| load_tools/check_invariants.py:63 | S8707 | read_jsonl | A (helper) |
| load_tools/check_invariants.py:597 | S8707 | _intended | A (helper) |
| tools/scrub_n8n_export.py:178 | S8707 | main (input file) | A (helper) |
| tools/scrub_n8n_export.py:179 | S8707 | main (output file) | A (helper; new output name from the character table) |
| load_tools/load_driver.py:366 | S8707 | run (facts write) | A (helper; output) |
| load_tools/load_driver.py:377 | S8707 | run (log write) | A (helper; output) |
| load_tools/check_invariants.py:82 | S8707 | read_crm | B (inline) |
| load_tools/check_invariants.py:605 | S8707 | _facts_say_live | B (inline; a refused path answers "not live") |
| load_tools/check_invariants.py:614 | S8707 | _drain_marker | B (inline) |
| scripts/n8n_api.py:192 | S8707 | main (import FILE) | B (inline) |
| load_tools/check_invariants.py:96 | S8706 | read_book | UNTOUCHED (control) |
| scripts/run_real_check.py:645 | S8707 | load_env | UNTOUCHED (control) |

Allowed folders for B: current folder, repository, temporary folder, LEAD_DESK_PATH_ROOTS (a small no-argument function `_probe_roots()` builds the list; the check itself is inline).

## How to read the result (12 issues: 6 A, 4 B, 2 controls)
* The two controls must STILL be open. If either vanished, something else changed; do not trust the rest.
* A issues gone, B issues open: the engine credits the listing-based helper but not an inline guard. Go with v2 (sonar-p3-path-helper-v2.patch) as built.
* B issues gone, A open: the engine credits a realpath+commonpath guard in the function but not the helper. Then inline that guard in each flagged function (probe-a shape); drop the helper for the readers.
* Both gone: take the simpler one (B inline) or keep v2; both are sound.
* Both open: this probe set cannot be accepted by what I tried. Read the new flow text of the still-open issues (the sink should move or the step list should change). Next candidates, not built: a name-only contract (basename into one fixed folder), or the owner marks the 12 as reviewed in the Sonar UI (not a code comment).
* Inside A, the read sites (63, 597, 178) and the output sites (179, 366, 377) differ: outputs also depend on the new-name character table. If 63/597/178 vanish and 179/366/377 stay, the helper is accepted and only the output-name step is not; say so and I will change just that step.
* A site that vanishes only because the guard moved the sink (new issue at another line) counts as NOT cleared: look for new issues on the PR too.

## Does candidate B differ from the core session's pathguard.py?
Read from `hadavin-dx/hadavin-sdk`, branch `wip/cloud-sonar-probe`, commit 247caa5, `src/hadavin_sdk/pathguard.py` (read-only fetch; nothing written there). Yes, B differs, in four ways:
1. Core's guard is a helper (`pathguard.join` / `inside`), B is inline in the function that opens the file. (My helper A is also not core's.)
2. Core resolves with `Path.resolve()` and tests `real.is_relative_to(root)`; B uses `os.path.realpath` and `os.path.commonpath` after `normcase`.
3. In core's probe (k1b/atomic.py L13) the base folder is `path.parent`, derived from the same argument that is being checked, so the check can never refuse the parent; B tests against fixed allowed folders that do not come from the argument. (core's `operator_dir/operator_file` check only the SHAPE: control characters and length.)
4. Core hands the resolved `Path` back to the caller to open, B opens `real` right there. Core also has name rules (separator, colon, Windows device names...) that B does not.
So a result for B says nothing about core's form, and the other way round; if core's probe is pushed too, compare the two by file:line.

## What was run (evidence-p3v2-7-probe-ab.txt)
New test file tests/test_probe_ab.py (6 tests: inside works, outside, `..`, link out, prefix-sibling refused, for all 8 changed functions): 6 fail on the old code, 6 pass on the probe. ruff check, ruff format --check, mypy linux and win32 clean. test_probe_ab + test_load_tools + test_scrub_n8n_export + test_n8n_api_url + test_real_check_dry + test_hygiene: 560 passed, 4 skipped. Not run: the full suite, Sonar, CodeQL, Windows, bandit on this patch. This is a measuring probe, not a fix: it does not carry the documented-real-run changes of the v2 patch (run_real_check --config outside the repository is unchanged here, and read_book stays as it was).
