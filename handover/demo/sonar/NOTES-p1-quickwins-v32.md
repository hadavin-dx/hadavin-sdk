# P1 quick wins v3.2: NOTES (base db54e13, patch sonar-p1-quickwins-v3.2.patch, replaces v3.1 completely)

Preamble points applied: 5, 6, 7, 20. EGM (13) NOT run by me: the lead runs it. No bible access in this shell, no R-numbers cited. No push, no network write; the only network use was none (all tests local). No suppression comments added.

## What did not work, is uncertain or was not run (first)
- I cannot see the SonarCloud result. Everything under "expected to clear" is a prediction (same as v3.1: the rule texts of githubactions:S6506 and S8541 are still not served by the rules API).
- The new tripwire is NOT a shell parser and is much weaker than the v3.1 scanner on purpose (see "What the tripwire does NOT do"). The real control for shell:S7688 is SonarCloud on the PR, not this file.
- "crlf-guard-v5.patch" does not exist in /tmp/demo-push/handover/demo/skips/ or in the lead's skips folder. I used /tmp/work/b10-v5.patch (the file the reviewer called v5) as "C5". If the lead has another v5, re-run the matrix line.
- crlf-guard-v4.patch and crlf-guard-v4-autocrlf-fix.patch are alternatives: each creates .editorconfig, so they never apply together (with or without P1). Not a P1 issue.
- Not run: full suite (the lead runs it), the 8 playwright tests (no playwright in my venv: 8 skipped), actionlint, Windows, real CI, SonarCloud, the 11-shell guard matrix (guard byte-identical to v3.1, cmp shown).
- Bandit prints 9 Low-severity findings in its metrics; the `-ll` gate (medium and above) reports "No issues identified", exit 0. I did not compare the 9 against the base.
- Mutant list is mine (31 scanner + 4 real-file); the reviewer's own mutants were not re-run.

## What changed against v3.1
| item | v3.1 | v3.2 |
|---|---|---|
| tests/test_hygiene.py | edited (imports bisect, Any, yaml; 390 lines added) | NOT TOUCHED (0 lines). No conflict with crlf v4/v4-fix/v5, nodemo-optional-hygiene, or any later edit of that file |
| scanner | `_scan` + `_code_only` + `_single_bracket_lines`: a character state machine (heredocs, quotes, `$(`, `[[ ]]`), ~230 lines, quadratic on `<<x<<x` / `<<'` | new file tests/test_shell_single_bracket.py: one function `single_bracket_lines`, 13 lines, one pass, line by line, no state between lines |
| raw direction-control-character test (rule text:S6389) | in test_hygiene.py | moved unchanged in behaviour to the new tests/test_raw_bidi_chars.py (the only other thing v3.1 added to test_hygiene.py besides the scanner and `_run_blocks`/`_workflow_shell_problems`, which moved to the scanner file) |
| guard lines, scripts/reset.sh, scripts/start_all.sh, lint.yml, README.md, test_reset_scripts.py, test_followup_edge_cases.py, test_lead_step_route.py, test_smtp_provider.py, test_workflow_run_flags.py | | cmp: byte-identical to v3.1 (evidence-p1v32-8) |
Files v3.2 touches (11): lint.yml, README.md, reset.sh, start_all.sh, test_followup_edge_cases.py, test_lead_step_route.py, test_reset_scripts.py, test_smtp_provider.py and three NEW files test_raw_bidi_chars.py, test_shell_single_bracket.py, test_workflow_run_flags.py. Of these only the new files are not in v3.1 (the first two) or not in db54e13.

## What the tripwire does
For every tracked `*.sh` file and every workflow `run:` block (yaml.safe_load of .github/workflows/*.yml and *.yaml), per line: (1) text inside `'..'` or `".."` on that line becomes `_`; (2) a `#` that starts the line or follows a blank cuts the rest off; (3) one precompiled regex looks for `[` followed by a blank or the line end where a command can start: line start, or after `; & | ( ) { !` or a backtick, or after then, do, else, elif, if, while, until. A line over 4000 characters, or any CR, raises ValueError with a message naming the cause (not "ends inside a quote"). Also kept from v3.1, short: a `shell:` key other than bash in a workflow fails; the scripts must start with the bash shebang; an explicit allowlist `_ALLOWED` (path -> reason, empty today; a test shows it skips exactly the listed file).
Proofs: 66 probes in two lists (36 flagged, 30 not flagged), incl. every survivor from rv21 (`a | [ x ]`, `{ [ x ]; }`, `a;# [ x ]`, `then [ x ]`, `if ! [ x ]`, `&& [`, `|| [`, `$( [ x ]`, backtick, `[[ x ]]`, `[ ]` in grep/sed/awk args, case pattern, CRLF message). The base db54e13 text is flagged (the 5+2 script lines holding the 10 S7688 occurrences, copied verbatim, and the 2 lint.yml lines): on the real base files 9 lines (reset.sh 15,20,25,28,33; start_all.sh 12,16; lint.yml block 8 lines 5,7), on the patched tree 0 (evidence-p1v32-5 shows the repo test failing on db54e13 with those 9 lines, evidence-p1v32-3 the base/patched listing method).

## What the tripwire does NOT do (honestly)
- It does not parse shell. No heredoc, quote-across-lines, `$( )` or `[[ ]]` state. So it has false positives: a line inside a heredoc body or multi-line string that looks like a test; a case pattern `[ a]*)` that starts a line (a pattern in the middle of a line is not flagged); a continuation line `\` + `[ x ]` that is an argument of the line before; `then`/`do`/`if` words in an echo followed by `[ `; an unquoted regex alternation `[[ $x =~ a|[ ]b ]]` (quoted it is fine). A file that really needs one goes into `_ALLOWED` with a reason, or the line is reworded. None occurs in the repo today.
- False negatives (a real `[ ... ]` it does not see): `test -e x` (not a bracket), `sudo [`, `env [`, `xargs [`, `exec [`, `time [`, `command [`; a test inside quotes (`"$( [ x ]; )"`, which step 1 blanks); a test after a `#` that follows a blank inside a string (the comment cut); any line over 4000 characters is refused, not scanned (the test fails with a message; nothing is silently skipped).
- It does not check that a script runs under bash beyond the first line (shebang) and the workflow `shell:` keys; it does not run shellcheck. If the owner accepts a new CI tool, shellcheck (rule SC2292 "prefer [[ ]]") would replace this file: rung to revisit, not verified by me.
- It does not prove S7688 is gone: SonarCloud decides.

## Linear time (evidence-p1v32-3; the whole new file runs in 2.3 s)
Per-line work is regex substitution, one search, one search; none nests, and every line is at most 4000 characters. Measured, ~1 MB each (lines of 3000 chars): 26 shapes including `<<x`, `<<x<<x`, `<<'`, `<<"`, `[ ` x many, `[[ `, `(( `, `$(`, backtick, quotes, blanks, tabs, `if `, `then `, `# `, `\`: 0.006 s to 0.24 s; 130k lines of `[[ x ]]` 0.13 s; 100k lines of `if [ x ]; then` 0.11 s; 1M newlines 0.23 s; 300k lines `[ ` 0.18 s; 250 lines of exactly 4000 chars of `<<x<<x` 0.07 s; one 1 MB line is refused in 0.0004 s. The v3.1 shapes that took 3.4 to 22 s now: one line is refused at once; cut into 3000-char lines 0.001 to 0.003 s. The test uses a 2 s bound per shape (a 10x margin over the slowest measured shape) and checks the cap by a 4001-char line (refused) and a 4000-char line (read).
Caveat: the cap is what bounds the regexes; I also measured 4000-char lines directly (0.035 to 0.072 s per 250 lines), so the cap is not hiding a slow regex.

## Mutants (evidence-p1v32-4): 31 of 31 killed, 0 survived
Scanner: drop each of `| { ; & ( ) backtick !`, drop each of the 7 keywords, drop the `^` alternative, drop the line cap, cap off by one, cap too large, no CR check, comments not stripped, comment cut without the blank rule, quotes not blanked, `[` at line end not seen, run blocks not extracted, run blocks not added to the scanned texts, allowlist ignored, shell-key check for the job default and for a step, scripts list cut to one file, line numbers off by one. One mutant survived in the first run ("only scripts/reset.sh listed"); killed after adding an assertion that both shipped scripts are in the list (this assertion fails loudly if a script is renamed). Real files: a `if [ -e x ]` put into reset.sh, start_all.sh, lint.yml and sonar.yml makes the repo test fail (codeql.yml has no `run:` step, so no mutant there).

## Tests run (evidence-p1v32-1, -2, -5, -7)
- hygiene, shell_single_bracket, raw_bidi_chars, workflow_run_flags, workflow_files_parse, reset_scripts, mode_safety, followup_edge_cases, lead_step_route, smtp_provider after `git add -A`, DPLD_REQUIRE_SCAN=1, gitleaks 8.30.1 (/tmp/work/gl/gitleaks): 362 passed, 8 skipped (all playwright), 0 failed. The first run failed once: the hygiene scan found `x.sh`-style names (a TLD rule) and a `s:\n` (drive-path rule) in my new test text; I changed the test text (plain names, real newlines) and re-ran; no suppression.
- ruff check, ruff format --check (149 files), mypy --platform linux and win32 (26 files each), bandit -ll: clean.
- New tests on db54e13 (copied in): the repo test fails (names the 9 lines) and the raw-bidi test fails on test_followup_edge_cases.py:439,445 (the base has raw characters; v3.1 and v3.2 fix them). 107 + 2 other tests of the two new files pass on the base: the probes do not depend on the files.
- Combined tree P1 ND P2.1 P3 NH-v2 NR Y C5 (git add -A): ruff clean, 196 passed in hygiene, scanner, bidi, run_flags, files_parse, reset_scripts.

## Apply matrix (evidence-p1v32-6; git apply, sequential, on db54e13)
Each patch alone: ok (P1 v3.2, P2 v2.1, P3 v3, ND v2, NH v2, NR, yaml trimmed, crlf v4, v4-autocrlf-fix, b10-v5). P1 with each, both orders: ok. SPECIFIC requirement: P1 before/after crlf (v4, v4-fix, v5) and nodemo-optional-hygiene-repo-v2 in all 6 orders each: ok (18 of 18). Lead order P1 ND P2 P3 NH NR Y then C4 or C5, and crlf first: ok. 150 random orders of the 7 patches: 150 ok; plus C5: 100 of 100 ok; plus C4: 60 of 60 ok; plus C4f: 60 of 60 ok; all 24 orders of P1, NH, ND, C4 and of P1, NH, ND, C4f (with yaml): 24 of 24 each. Not exhaustive. Note NH-v2 no longer needs P1 first (v3.1 needed it for the `import yaml` line): it applies before or after.

## Per-rule count (issues of issues-pr4-0253.json): 15, as v3.1
githubactions:S6506 1, githubactions:S8541 1, shell:S7688 10, text:S6389 2, python:S5863 1. Expected to clear for the reasons in v3.1 (every flagged `[`, flag and character changed; the scripts, lint.yml and README are byte-identical to v3.1). Risks as in v3.1: S7688 on the guard `case`; the spellings accepted for S8541 and S6506.

## Behaviour change for the PR text
Unchanged from v3.1: `sh scripts/reset.sh` and `sh scripts/start_all.sh` under a shell where `[[` does not run (dash) stop with exit 2 ("run this script with bash").

## Rung table
| component | need | rung tried | verdict |
|---|---|---|---|
| guard line (1 per script) | unchanged | no standard option stops a run | KEEP-CODE (safety guarantee) |
| single-bracket tripwire (test code, one regex, ~20 lines of logic) | stop `[ ` returning between Sonar runs | SonarCloud itself is the control; shellcheck not a repo dependency (not checked whether it flags it) | KEEP as a cheap tripwire only; revisit with shellcheck |
| flags, `[[`, escapes | 15 findings | standard options | CUT-TO-CONFIG |
