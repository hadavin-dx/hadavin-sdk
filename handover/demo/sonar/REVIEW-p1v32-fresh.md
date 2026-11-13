# rv24: fresh review of sonar-p1-quickwins-v3.2.patch (base db54e13)
Fifth reader, shell, scratch /tmp/work/rv24-x (clones only; no push, no network write besides the read-only clone). EGM not run (lead runs it). Full suite NOT run. rv21 read only afterwards: both of its Majors are closed (scanner replaced by a linear one; no test_hygiene.py edit, 18/18 crlf orders apply).

## Verdict: P1 v3.2 CLEAN (0 Blocker, 0 Major, 3 Minor, 5 Nit)

## Failures / findings first
Minor 1: `_workflow_shell_problems` checks the job-level `defaults.run.shell` and step `shell:`, not workflow-level `defaults: run: shell: sh`. Probe: `defaults:\n run:\n  shell: sh\njobs:...` returns [] (no problem). No repo workflow has it; add a top-level check.
Minor 2: `_tracked("*.sh")` uses `git ls-files` without `-z`. A tracked name with a newline or non-ASCII letters is printed quoted (`"scripts/\303\251.sh"`), then `(REPO / n).read_text` raises FileNotFoundError. Fails loudly (no silent pass; measured), but the cause is unclear. The bidi test does use `-z` and handled a name with a newline and a bidi char (failed correctly).
Minor 3: tripwire false negative not in the NOTES list: an assignment prefix `FOO=1 [ x ]` (and `a=1 [ x ]` alone) is not flagged. Also not listed: an unquoted apostrophe pair hiding a test (`echo don't; [ x ]; echo it's` is blanked from the first to the second apostrophe) and an escaped quote `\" ; [ x ] ; \"`. All contrived; none in repo.
Nit 4: `jobs:` with no value (null) crashes `_workflow_shell_problems`/`_run_blocks` with AttributeError (invalid workflow anyway). Composite action files (action.yml) are not scanned (none exist).
Nit 5: two test-code mutants survive: removing the bash shebang assert, and `*.yaml` glob dropped (no unit test; only the real tree, which has no such file). Detection of a non-bash shebang is untested by a mutant.
Nit 6: message for an unnamed step with a non-bash shell says "step None".
Nit 7: `echo a ! [ x ]` is a false positive (an argument); `[ a]*)` at line start and heredoc bodies are the documented false positives (confirmed).
Nit 8: timing bound is 2 s per shape; measured max 0.10 s per 1 MB (Linux). Ample margin on a Windows runner.

## (1) Byte identity and guard
git apply of v3.1 and v3.2 on separate db54e13 clones; cmp silent (identical) for scripts/reset.sh, scripts/start_all.sh, .github/workflows/lint.yml, README.md, tests/test_workflow_run_flags.py, tests/test_reset_scripts.py, tests/test_followup_edge_cases.py, tests/test_lead_step_route.py, tests/test_smtp_provider.py (9 of 9). Patch touches 8 modified + 3 new files; tests/test_hygiene.py not touched.
Guard re-run with BASH_VERSION=5.2 exported, made-up db in a temp dir: dash and posh: reset.sh and start_all.sh print "refused: run this script with bash" exit 2, db file untouched. busybox sh, ksh, mksh, zsh, bash pass the guard (they run [[ ]]) and then stop at the data/ path refusal, exit 2 (db outside data/).

## (2) Tripwire
- 110 own probes (/tmp/work/rv24-x/probe/p.py): 65 flagged, 43 not flagged, 2 raise ValueError as designed (CRLF; 4001 chars). Differences from the ideal are only the documented ones: here-doc bodies (2), case pattern at line start (1), `test -e`, `sudo [`, `exec [`, `command [`, `time [`, `env FOO=1 [`, `FOO=1 [` (Minor 3). Every separator/keyword listed in the brief is flagged: line start, `; & | |& ( ) { !`, backtick, `$(`, `$( [`, `if !`, then/do/else/elif/while/until, `&&`, `||`, tab after `[`, `[` at line end, continuation line (flagged, documented), `function f { [`, `f() [`. Not flagged: quoted `[`, regex args of grep/sed/awk, `[[`, arrays `a[ 1 ]=2`, `m=(['a']=1)`, `${#a[@]}`, case pattern mid-line, `a;# [`, `a # [`, `echo [ ]`. Lengths 3998..4000 read, 4001 refused. The NOTES' 36 flagged / 30 not flagged of 66 matches the two lists in the test file (counted: 36 + 30).
- Timing (probe/t.py), one 1 MB text each, 250 lines of 3999 and of 4000 chars of 46 shapes (quote mixes `'"`, nested alternation text, spaces, tabs, `!`, `;`, `(`, backtick, `{ `, `; ; `, `if `, `then`, `do `, `#`, `\`, `[`, `[ [ `, `; \t`, ...): worst 0.10 s. 1M empty lines 0.26 s, 500k short lines 0.34 s, 330k `[ ` lines 0.21 s, 3990 spaces then `x` x250 0.08 s. Linear. The cap does not hide a slow regex (4000-char lines measured directly).
- Base vs patched: db54e13 flagged = 9 lines (start_all.sh 12,16; reset.sh 15,20,25,28,33; lint.yml block 8 lines 5,7); patched tree 0.
- Run-block extraction (probe/y.py, 15 YAML snippets): `|`, `>`, `|-`, `|+`, quoted one-liner, plain one-liner, multi-job, anchors/aliases, `on: push`: found and flagged. A step name containing `run:` or `with: run:` is not scanned as a block (correct). `>-` folds lines into one (`echo a` + `[ x ]` -> argument): correct, as bash gets the folded text. Gap: Nit 4.
- `shell:` assertion test: step `sh`/`pwsh` and job default caught; workflow-level default not (Minor 1).

## (3) Bidi
Mutant: one raw U+202E in tests/test_lead_step_route.py (tracked via git add): tests/test_raw_bidi_chars.py fails; same for all 12 (202A-202E, 2066-2069, 200E, 200F, 061C): 12 of 12 killed. `git ls-files -z` handles a tracked name holding newline, accented letters and a raw bidi char (failed correctly). Binary files skipped by UnicodeDecodeError.

## (4) Apply matrix (git apply, sequential, on db54e13)
Each alone ok: P1 v3.2, P2 v2.1, P3 v3, nodemo-fix-v2, nodemo-optional-hygiene-repo-v2, nodemo-ruff-isort, merge-ready/sonar-yaml-test-trimmed, crlf v4, v4-autocrlf-fix, crlf v5 (skips/crlf-guard-v5.patch is byte-identical to /tmp/work/b10-v5.patch; cmp). 120 random orders of the 7 sonar patches: 120 ok; with +C4, +C4f, +C5: 120 ok each (480 total, 0 bad). Exhaustive 120 orders of {P1, NH, ND, Y, C} for each of C4, C4f, C5: 360 ok, 0 bad. (C4 + C4f together excluded: both create .editorconfig, not a P1 matter.)
Lead order P1 ND P2 P3 NH NR Y C5 on one tree, git add -A, DPLD_REQUIRE_SCAN=1, gitleaks 8.30.1: ruff clean, format clean (153 files), mypy win32 clean (28), hygiene + shell_single_bracket + raw_bidi + run_flags + reset_scripts: 185 passed.

## (5) Gates on the v3.2 tree alone (git add -A, DPLD_REQUIRE_SCAN=1, gitleaks)
hygiene, shell_single_bracket, raw_bidi_chars, workflow_run_flags, reset_scripts: 176 passed (39 s). ruff check ok, ruff format --check 149 files ok, mypy --platform linux and win32: no issues (26 files), bandit -ll -r src tools scripts -c pyproject.toml: "No issues identified".
Mutants of my own (16, on the new test file): killed: drop `{` separator, drop `!`, drop `|`, drop backtick, drop `while|until`, require blank after `[` (end-of-line case), quote blanking off, comment cut off, cap 400000, workflow blocks not scanned, scripts list cut to reset.sh, allowlist ignored, line numbers from 0, step-shell check off. Survived: shebang check removed, `*.yaml` glob dropped (Nit 5).
Windows safety (read, not run on Windows): files read with encoding utf-8; text mode translates CRLF so the CR guard only fires on odd text; the tests need no shell (scripts are read, not run), no drive-path or backslash text; .gitattributes gives eol=lf for *.sh/*.yml.

## Not checked
Real Windows run, SonarCloud result, actionlint, playwright, full suite, bash 3.2.
Files: /tmp/work/rv24-report.md; probes under /tmp/work/rv24-x/probe/.

P1 v3.2 CLEAN
