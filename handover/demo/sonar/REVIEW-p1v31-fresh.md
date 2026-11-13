# rv21: fresh review of sonar-p1-quickwins-v3.1.patch (base db54e13)
Reviewer: fresh, shell, scratch /tmp/work/rv21-main (clones only; no push, no network write). Preamble read; no bible access (R-numbers not cited). EGM not run by me (lead runs it). Full suite NOT run.

## Verdict: P1 v3.1 NOT CLEAN: 1 Major (scanner still quadratic on a 1 MB line, different shape from the one v3.1 fixed, so the NOTES "linear" claim is false), 1 Major for the series (v3.1 now conflicts with the crlf v5 patch), 3 Minor, 3 Nit. Guard, scripts, flag tests, Windows/lint all fine.

## Failures first
### MAJOR 1: scanner is quadratic (measured, extrapolated to hours at 1 MB)
`_HEREDOC` word may contain `<`, so `<<x<<x<<x...` (and `<<'` and `<<"` repeated) makes EVERY `<<` match the whole rest of the line.
Measured, one line, `_single_bracket_lines`: `"<<x"*5000` (15 KB) 3.4 s, `*10000` 16 s (x4.7 for x2 size); `"<<'"*10000` 5.0 s, `*20000` 21.9 s; `"<<\""*10000` 6.7 s, `*20000` 33.7 s. Extrapolation to 1 MB: hours (NOT measured at 1 MB, I stopped the runs). Shapes that ARE linear (measured 1 MB): `<<`, `<<<`, `<<'a `, `<<\`, `<<EOF ` x many, 100k lines, 300k lines of `[[ `, nested `$(` 500k deep, many heredocs, `if`/`;` + 1M blanks, 25 shapes at 0.1 to 0.7 s, `[[ ` x333k 2.5 s.
The shipped test test_the_scan_of_one_very_long_line_is_linear does not use these shapes, so it passes. Impact: a hostile or odd tracked .sh file or run block can hang CI (test code only, no security effect); no such text exists in the repo. rv16 Minor 3 is therefore only closed for the `<<` shape. Fix: make the word match not consume `<` (or stop after a match at a fixed length), or advance `i` past the matched word; add these shapes to the timing test.
Files: /tmp/work/rv21-main/h/t1.py (shape runner), h/timing.py, h/timing2.py.

### MAJOR 2 (series order): v3.1 does not apply together with crlf v5
The lead's order ends P1 v3.1, nodemo, P2 v2.1, P3 v3, crlf v5, yaml. I took crlf v5 to be /tmp/work/b10-v5.patch (the only v5 crlf file I found; if the lead has another, re-test). Measured with git apply on db54e13:
- `P1(v3.1) then b10-v5`: FAIL tests/test_hygiene.py hunk 1 (import block, line 3); `b10-v5 then P1`: FAIL the same way. Whole lead order up to crlf: FAIL at crlf.
- With P1 v3 instead of v3.1: `P1v3, b10-v5` and `b10-v5, P1v3` apply. So the new conflict is introduced by v3.1 (it adds `import bisect` next to the lines v5 edits: `import copy`; also adds `Any`).
- crlf-guard-v4-autocrlf-fix.patch conflicts with v3.1 in the same file, both orders.
A conflict in an import block only, but the series cannot be applied by git apply as ordered; the crlf patch (not P1) must be regenerated on top of v3.1 (or the other way round). I did NOT test a hand-resolved merge.

## Minor
3. Scanner tests do not kill 3 anchor mutants (my own): dropping `|` from the command-start set, dropping `{`, and the `;` before `#` in the comment rule: 66 passed each (/tmp/work/rv21-main/h/mut.py M3, M4, M6). No snippet has `| [`, `{ [` (the form the base reset.sh line 20 had) or `a;# [ x ]`. Today's files have no `[ `, so the repo test cannot notice. Add three snippets.
4. False positive (safe side): a case pattern `[ a]*)` on its own line is flagged (probe case-pat). Contrived, no such line.
5. Documented holes confirmed: `sudo [`, `env [`, `xargs [` not flagged (probes). NOTES lists them. Fine.

## Nit
6. CRLF: a .sh with CRLF: heredoc end lines never match, so the scan reports "ends open" and the test fails loudly (probes crlf-heredoc: open=True); plain CRLF text is still scanned (`[ x ]` found). Behaviour is safe; the failure message says "ends inside a quote" which would mislead for a CRLF file (a CR hint would help). .gitattributes + test_sh_blobs_no_cr already cover this.
7. The two surviving "mutants" M7 (dropping `--proto-redir` from the flag list inside the test) and M18 (deleting the run-block check inside the test) are edits of the test itself, not real survivors; real-file mutants (below) are killed.
8. A mutant list in NOTES says 26 killed; I re-ran my own, not theirs.

## What I checked (evidence)
1. Guard/scripts. `diff`/`cmp` v3 vs v3.1 of scripts/reset.sh and scripts/start_all.sh (patch applied on db54e13 each): byte-identical (cmp silent for both). The guard line, with BASH_VERSION=5.2 exported: bash, zsh, busybox sh, ksh, mksh go on; dash and posh print "refused: run this script with bash ..." rc 2. Real scripts: `BASH_VERSION=5.2 dash scripts/reset.sh` and posh with a made-up data/ dir (db file + desk.pid) rc 2, files untouched; busybox sh and zsh pass the guard (then stop at python import in my bare dir: expected). Mutants G1/G2 (`&&` to `;`), G3/G4 (guard by BASH_VERSION), exit 2 to 0 (M1), guard removed (M2): all KILLED by tests/test_reset_scripts.py -k dash.
2. Scanner. 95 own probes (/tmp/work/rv21-main/h/probes.py): here-strings of 7 forms, heredocs with `E-1`, `E.1`, `"E 1"`, `\E`, `1`, `__END__`, `<<-` tabs, two heredocs on a line, heredoc inside function and `$( )`, redirect after the word, `[ ` in `$( )`/backticks/`"$(..)"`, `[[ ]]` incl. regex, arrays, case patterns, continuation, `if !`, `&& || ; |`, quoted/commented `[`, `$(( ))`, nested quotes, CRLF, no trailing newline, empty, only-newline, delimiter-only file, binary garbage. 90 agree with my expectation; 5 diffs: case-pat, sudo/env/xargs (Minors 4/5) and one wrong expectation of mine (binary). Never raises.
   Base comparison: scanner on db54e13 scripts finds 7 lines (reset.sh 15,20,25,28,33; start_all.sh 12,16) = the 10 S7688 occurrences (lines 20, 12, 16 hold two each; the scanner reports lines), and lint.yml run block lines 5,7 (the two `[ ` at 76 and 78); on v3.1: no hit in any tracked .sh or workflow run block, no "ends open". Ends-open net tested by the shipped 8+6 snippets, 16 and 17 mutant (pending ignored) KILLED.
3. New file tests/test_workflow_run_flags.py: tests curl `--proto '=https'`, `--proto-redir '=https'`, `--tlsv1.2`, pip `--only-binary=:all:` and `--require-hashes` per workflow; test_workflow_files_parse.py untouched (git diff shows no edit). Real-file mutants KILLED: lint.yml without --tlsv1.2 (M8), without --proto-redir (M11), without --require-hashes (M9), pip in the `--only-binary :all:` form (M10); `if [` back in lint.yml (M18b) and reset.sh `[` back (M19) killed by the double-brackets test. Only workflows with curl/pip: lint.yml and sonar.yml.
4. Apply matrix (git apply on fresh db54e13 clones, /tmp/work/rv21-main/h/matrix.py). OK: each patch alone (P1, P2 v2, P2 v2.1, P3 v3, nodemo-fix-v2, nodemo-optional-hygiene-repo-v2, ruff-isort, yaml trimmed); P1 with each of them in both orders, EXCEPT nodemo-optional-hygiene-repo-v2 BEFORE P1 (fails at P1, tests/test_hygiene.py; expected, brief says after v3.1; NH alone applies on db54e13). Order P1, nodemo-fix-v2, P2 v2.1, P3 v3, NH-v2, ruff-isort, yaml trimmed: OK; same with P2 v2. 200 random orders of {P1, ND, NH, NR, Y, P2 or P2.1, P3}: the only failures are P1 after NH (90 failure classes, all that one). v3 + yaml trimmed fails (known, v3.1 fixes); v3.1 + yaml trimmed ok both orders. Crlf: see Major 2.
   On the combined tree (P1 ND P21 P3 NH NR Y, git add -A): ruff check and format clean; test_hygiene + test_workflow_run_flags + test_workflow_files_parse 123 passed with DPLD_REQUIRE_SCAN=1 and gitleaks 8.30.1.
5. v3.1 tree alone (git add -A, DPLD_REQUIRE_SCAN=1, GITLEAKS_BIN=/tmp/work/gl/gitleaks): hygiene + run_flags + files_parse 116 passed; reset_scripts, mode_safety, followup_edge_cases, lead_step_route, smtp_provider 227 passed, 8 skipped. ruff check, ruff format --check (147 files), mypy --platform linux and win32 (26 files), bandit -ll -r src tools scripts -c pyproject.toml: all clean. Windows: not run on Windows; reading: shell tests are skipif WINDOWS, the file reads use read_text (newline translation) so the scan test is safe with autocrlf; no Windows path in new code.
6. Own mutants: 18 real-file/scanner mutants killed, 3 survived (Minor 3), 2 non-meaningful.

## Earlier findings (rv7, rv10, rv16) closed?
rv7: all closed (lint.yml 77/79 fixed, holes `do`, `)`, tab covered by probes, README, empty-pid test present). rv10 Major 1 (BASH_VERSION bypass): closed (measured above). rv10 Minor 3 pip spelling: closed. rv16 Major 1 (here-string): closed (7 probes + mine). rv16 Minor 2 (quoted array keys, regex alternation): closed. rv16 Minor 3 (quadratic): NOT closed, see Major 1. rv16 Minor 4 (README wording): closed ("where `[[` does not run"). rv16 Nit 5 (guard `;` mutants): killed.

## Not checked
Windows run, real CI/SonarCloud, actionlint, playwright tests, full suite, bash 3.2, a hand merge of v3.1 with crlf v5, 1 MB `<<x` run to completion (extrapolated). Token use: modest, not tracked.

P1 v3.1 NOT CLEAN: Major 1 (scanner quadratic on `<<x<<x...`, `<<'`, `<<"` lines: 16 s at 30 KB, hours at 1 MB, NOTES linear claim false) and Major 2 (does not git-apply together with crlf v5 / crlf v4 fix in tests/test_hygiene.py imports; the lead order breaks at crlf).
