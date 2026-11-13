# P1 quick wins v3: NOTES (base db54e13, patch sonar-p1-quickwins-v3.patch, replaces v2)

Preamble points applied: 5, 6, 7, 20. EGM (13) NOT run by me: the lead runs it. Bible R-numbers not available in this shell, none cited.
Reviewed v2: /tmp/work/rv10-report.md (1 Major, 3 Minor, 1 Nit). Each is handled below.

## What did not work, is uncertain or was not run (first)
- I cannot see the SonarCloud result. "Expected to clear" is a prediction. The rule texts of shell:S7688, githubactions:S6506 and S8541 are not served by the rules API, so which spellings Sonar accepts is UNVERIFIED: the `--only-binary=:all:` form is a hedge (sonar.yml uses it and has no S8541 finding; the issue message prints the flag with a space, which tells nothing about what is accepted), and "no new S7688 hit on the guard `case`" is a prediction.
- Hygiene scan: still a character scanner, not a shell parser. Holes left: (a) `test -e x` is NOT flagged (the rule is about `[`; whether Sonar also flags `test` is unknown; flagging it would be a guess and could create false positives); (b) a backtick opened in plain code (not inside double quotes) is treated as a command separator only, so an unterminated backtick is not reported (the unterminated-quote check covers `'`, `"`, `$(`, `$'`); (c) a heredoc whose body holds `$( [ ... )` is blanked, so code in it is not scanned; (d) the heredoc recogniser needs a word starting with a letter or `_` and skips lines that contain `((`, so `<<EOF` on a line with `((` is read as no heredoc; (e) `case x in (a|b)) [ ...` (a pattern ending in `))`) is missed because `))` is treated as the end of arithmetic; (f) `[` after other command prefixes (`sudo`, `env`, `xargs`...) is not looked for. None occurs in the repo; the scan runs over every tracked .sh file and every workflow run block.
- Not run: full suite (the lead runs it), the 8 playwright tests (no playwright in my venv), 3 gitleaks tests (no gitleaks), actionlint (not installed here; lint.yml changed one more token, `:all:` spelling), Windows, real CI, SonarCloud, ksh/mksh. Combined test run of v3 with P2 and P3: NOT run, only `git apply --check` in 7 orders (evidence-p1v3-7).
- The 4 dash tests whose BASH_VERSION is unset also fail on v2, but only because the message wording changed to "not bash" (the test now asserts it). The exported-BASH_VERSION tests are the ones that prove the bypass; see below.

## MAJOR (guard bypass): fixed
The v2 guard tested the variable BASH_VERSION. dash takes every environment variable, so `export BASH_VERSION=5.2.0; dash scripts/reset.sh` skipped the guard, printed `[[: not found`, treated the "database inside ./data" test as false and deleted a database outside ./data. v3 tests the feature, in both scripts, using the reviewer's form:
`case "$( (eval '[[ a == a ]]') 2>/dev/null && echo bash)" in bash) ;; *) echo "refused: run this script with bash (...); this shell is not bash, so its [[ ]] tests would not work and a safety check could be skipped" >&2; exit 2 ;; esac`
(`eval` keeps the `[[` out of the parse, so dash and the other shells parse the file; the check runs in a subshell, so a failure only prints to /dev/null.) I did not find a better one that stays one line.
- Bypass transcript, made-up database in a temp dir outside the repo (evidence-p1v3-2): v2 under dash with BASH_VERSION exported: three `[[: not found`, "reset done", rc 0, file DELETED; v3: refused, rc 2, file kept; bash on both: refused by the data/ check, rc 2.
- Shell matrix, reset.sh with an outside database, BASH_VERSION unset and exported (evidence-p1v3-4): dash refuses with the new message; busybox sh, busybox ash, zsh, zsh --emulate sh, bash --posix and bash run the file and stop at the data/ refusal (they do support `[[`), rc 2, database kept in all 14 runs. `-n` parse: dash, busybox sh/ash, zsh, zsh --emulate sh, bash --posix, bash: rc 0 for both scripts.
- Tests: the dash test is now parametrized over BASH_VERSION unset / exported (made-up value) and both scripts; it asserts rc 2, the words "run this script with bash" and "not bash", no "not found" in stderr, the made-up database untouched, and that the stand-in python was never called.
- Wording (nit 4): "not bash" instead of "do not work in dash"; the README sentence now describes the refusal. The not-executable file mode of reset.sh (portal_demo.js tells people to run it directly) is pre-existing and not changed here.

## MINOR 2 (hygiene scan holes): closed where cheap
`_scan` in tests/test_hygiene.py replaces the line-by-line blanker. It reads the whole text, so now: code inside `"$( ... )"` (nested too) and inside backticks in double quotes is scanned; a backtick in code is a command start; `command [`, `time [`, `exec [` are caught; an escaped quote (`\'`, `\"`, `$'..\'..'`) no longer flips the quote state; multi-line quoted strings are blanked; heredoc bodies (`<<EOF`, `<<-'EOF'`) are blanked and scanning resumes after the end line; `$(( 1 + 2 )) [` is not a command start (the `)` of `))` is excluded) and `$(( 1 << 2 ))` is not a heredoc. New safety net: the test fails when the scan of a .sh file or run block ends inside an open quote or `$( `, so a scanner slip cannot silently hide the rest of a file.
- Probes: 38 snippets (was 20); the v2 scan gets 13 of them wrong, the v3 scan 0 (evidence-p1v3-5). Plus 4 "ends open" probes.
- Scan mutants (evidence-p1v3-6): dropping `command|time`, the `)` exclusion, the backtick separator, the `$(` handling in double quotes, the heredoc blanking: each KILLED.
- Holes left: see the first section (a to f).

## MINOR 3 (pip spelling): done
lint.yml now `--only-binary=:all:` like sonar.yml. The S8541 issue message (issues-pr4-0253.json, lint.yml line 51) is "Omitting "--only-binary :all:" can lead to the execution of setup scripts", and S6506's message is about not enforcing HTTPS (line 38): neither message says which spelling the rule accepts. test_workflow_files_parse now requires the `=` form (mutant back to the space form: killed). The `run: |` block already is a block scalar, so `:all: ` does not break the YAML (the test file parses lint.yml and passes).

## MINOR 5 (surviving mutant): closed
New test test_reset_sh_deletes_an_empty_pid_file (desk.pid and fakes.pid): an empty pid file is removed and the reset goes on. Mutant `-e` -> `-s` on the pid-file test: KILLED. The lint.yml `-gt 1` / `-s` logic from rv10 ("no test, only syntax") is still not behaviour-tested (those lines are CI shell, not run by the tests); only the double-bracket syntax is guarded.

## Evidence (all in /tmp/demo-push/handover/demo/sonar/, copy of the patch also in /tmp/demo-lead/handover/demo/sonar/)
| what | result | file |
|---|---|---|
| 7 test files (the 6 affected + test_mode_safety) on db54e13 + v3 | 292 passed, 11 skipped (8 playwright, 3 gitleaks), 0 failed | evidence-p1v3-1 |
| bypass transcript v2 vs v3 | v2 deletes, v3 refuses | evidence-p1v3-2 |
| ruff check, ruff format --check, mypy linux and win32, bandit -ll | clean, clean, no issues in 26 files x2, bandit exit 0 (9 Low hidden by -ll) | evidence-p1v3-3 |
| shells matrix | table above | evidence-p1v3-4 |
| v3 test files on the v2 scripts/workflows | 5 failed (4 dash tests, 2 of them the exported-BASH_VERSION bypass; lint.yml pip spelling), 105 passed; probes: v2 scan wrong on 13 of 38 | evidence-p1v3-5 |
| 12 mutants (guard in both scripts, exit code, condition, name-test regression, pid -e/-s, pip spelling, 5 in the scan) | all 12 KILLED | evidence-p1v3-6 |
| git apply --check on db54e13: v3 alone, with P2, with P3, both orders, all three | all OK | evidence-p1v3-7 |
Venv: uv, py3.13, requirements-dev.txt with --require-hashes --only-binary :all: (the repo has no uv `test` group). Busybox 1.36.1 and zsh 5.9 were installed with apt in this sandbox for the matrix.

## Changes since v2 (10 files, same as v2; +455/-20 vs db54e13)
scripts/reset.sh and start_all.sh (guard line); .github/workflows/lint.yml (`=:all:`); README.md (one sentence); tests/test_hygiene.py (scanner, probes); tests/test_reset_scripts.py (dash test x2 variants, empty pid file); tests/test_workflow_files_parse.py (`=` form). The rest is unchanged from v2.

## Series overlap
Same files as v2: lint.yml, README.md, scripts/*.sh, 6 test files. No conflict with P2 or P3 (apply --check, 7 orders). Their combined tests were not run.

## Per-rule count (issues of issues-pr4-0253.json): 15, same as v2
githubactions:S6506 1, githubactions:S8541 1, shell:S7688 10, text:S6389 2, python:S5863 1. Expected to clear for the same reasons as v2 (every flagged `[`, flag and character is changed). Risks: S7688 flagging the guard `case` (no `[` command in it; I expect not), S8541/S6506 wanting other spellings (unknown).

## Behaviour change for the PR text
`sh scripts/reset.sh` and `sh scripts/start_all.sh` under dash now stop at once with exit 2 ("run this script with bash"); they worked before this series. busybox ash and zsh run the scripts (they support `[[`).

## Rung table
| component | need | rung tried | verdict |
|---|---|---|---|
| feature-test guard (1 line per script) | `[[` false in a non-bash shell skipped a deletion safety check; a name test is bypassable | no standard option stops a run; POSIX `case` plus eval is the smallest | KEEP-CODE (safety guarantee) |
| scan rewrite (`_scan`) | stop `[ ` returning; v2 had 9 known holes | no existing linter in the repo; shellcheck not a dependency | KEEP (test code, about 90 lines); rung to revisit: replace by shellcheck in CI if the owner accepts a new tool |
| flags, `[[`, escapes | 15 findings | standard options | CUT-TO-CONFIG |
