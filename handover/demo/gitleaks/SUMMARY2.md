# Lane 10a2: gitleaks allowlist fix v2 (BUILDER; a fresh reviewer re-reads)
Head 558d37fe5372f8c378e7ea07c6193a738f4497ed (fresh clone of pr-3-tests). gitleaks 8.30.1. Made-up values only, built at run time, never kept in files (raw files hold rule, file, line only). Nothing committed or pushed in the real repo; scratch copies only. No process left running.

## FAILURES, HOLES, UNCERTAIN (first)
1. HOLE FOUND IN v1 (now closed in v2): v1's exceptions.txt line (`projectKey=hadavin-dx_[a-z0-9-]+`) let a DIFFERENT lowercase project key (`projectKey=hadavin-dx_other-project-<22 random letters>`) pass tests/test_hygiene.py when planted in sonar-project.properties AND in .gitleaks.toml (v1: 10 passed in both). With v2 both plants make test_hygiene fail (evidence-v2-3). The gitleaks layer is not a backstop for such lowercase plants: gitleaks does NOT report a lowercase made-up `hadavin-dx_<lowercase>` key anywhere (controls k1/k2 in evidence-v2-5: not reported even in a non-allowlisted file; a mixed-case one is reported, k3/k4). So the narrow hygiene exception is the only guard for that case; v2 has it.
2. The old coverage patch (coverage/sonar-coverage-v1.patch, 3 lines of context) still does NOT apply with plain `git apply` AFTER v2 (exceptions.txt:21 context). The rewritten coverage/sonar-coverage.patch (mtime 20:19, 1 line of context) works in both orders. `--3way` works for all four combinations. See the table below. I did not touch coverage/ or fixes/.
3. CRLF: with `dir` mode a CRLF line ending on the key line IS reported (false positive, safe direction; cases iii1, iii2). In `git` mode it is not reported because .gitattributes (`* text=auto eol=lf`, `*.toml text eol=lf`) normalises the committed blob to LF. CI scans a git checkout, so no CI impact; a Windows user running `dir` on a CRLF working file would see a finding. Not changed.
4. Not checked: CI itself, the full pytest suite (only tests/test_hygiene.py, as told), Windows paths, the CI-downloaded gitleaks tarball hash (the binary is /tmp/work/gl/gitleaks 8.30.1 from an earlier lane), gitleaks source or docs (behaviour by experiment only). The v1-coverage-then-v2 merged tree was tested by apply only (gitleaks/hygiene on the merged tree were run with the current coverage patch).

## ANSWER
- v2 on 558d37f: gitleaks `dir` exit 0 no leaks; `git` exit 0 no leaks (history incl. a scratch commit of v2); tests/test_hygiene.py 10 passed (evidence-v2-1).
- v2 + coverage/sonar-coverage.patch (20:19) merged in a scratch tree: `dir` exit 0, `git` exit 0, tests/test_hygiene.py 11 passed (the coverage patch adds one test) (evidence-v2-2). Note: gitleaks `dir` also scanned the untracked requirements-coverage.* files the coverage patch creates (0 findings).
- Narrowness matrix (all with the real binary, dir and git): NO hole found for the allowlist. Every same-line extra (space, `#`, `;`, tab, `"`, extension `-x`, `_x`, `-`/`_`+random) is REPORTED. See the table.
- The `(?m)` variant (regexTarget "line") also works with the real binary and was as narrow in the 5 narrowness cases run; `match` stays the shipped version: it is simpler (matched text only, no reliance on how gitleaks adds the line break).

## What v2 changes (gitleaks-toml-fix-v2.patch, unified=1, against 558d37f; `git apply --check` OK on a second fresh clone)
- .gitleaks.toml (same result as v1, blob c6f07f8 -> 1a1f919): `regexTarget = "match"`, regexes `^sonar\.projectKey=hadavin-dx_duplicate-proof-lead-desk-n8n$`, path unchanged.
- exceptions.txt line 27 only: `^(sonar-project\.properties|\.gitleaks\.toml):[0-9]+:projectKey=hadavin-dx_[d]uplicate-proof-lead-desk-n8n$` (bracket trick: the key literal does not appear in the file, and the exception matches only the exact key). Proven: exact key accepted in both files (the real files pass hygiene); a different key `hadavin-dx_other-project-...` fails in both files; the exact key plus `-x` in sonar-project.properties fails; the exact key in docs/x.properties fails (evidence-v2-3, -7).
- Why no clash with the coverage patch: v2 changes only line 27 with 1 context line (26); the coverage hunks change lines 9 and 24 with context 8-10 and 23-25. A separate new line was not needed (v1 line 27 had to change anyway to be narrowed).

## Apply orders with the coverage patch (evidence-v2-6)
| order | coverage-v1 (20:07, 3 ctx lines) | coverage (20:19, current) |
|---|---|---|
| coverage then v2, plain `git apply` | OK | OK |
| v2 then coverage, plain `git apply` | FAILS (exceptions.txt:21 context contains line 27) | OK |
| either order, `--3way` | OK | OK |
Merged result (current coverage + v2), exceptions.txt tail: line 24 `^[^:]+:[0-9]+:(requirements-(dev|coverage)\.in|(start_all|reset|all)\.sh|log\.info\(|P\.page\(|counts\.info)[^A-Za-z0-9_-]?$`, 25 README, 26 SECURITY, 27 the v2 narrow line above; line 9 `^requirements-(dev(-win)?|coverage)\.txt:...`. .gitleaks.toml: coverage's host-name regex `^requirements-(dev|coverage)\.in...`, the long-hex path `(^|[/\\])requirements-(dev(-win)?|coverage)\.txt$`, and v2's sonar allowlist (`match` + exact key). Full diff in evidence-v2-2.

## Narrowness matrix (real gitleaks 8.30.1, scratch copies of 558d37f + v2, dir | git; rule generic-api-key unless noted; evidence-v2-4/-5)
| case | result (dir and git the same unless noted) |
|---|---|
| clean v2 tree | not reported |
| control: plant alone in config.properties; plant appended at sonar-project.properties:13 | reported |
| (i) exact key + space + plant / ` # ` + plant / `#` + plant / `;` + plant / tab + plant / `"` + plant, line 4 | all reported (sonar-project.properties:4) |
| (i) exact key extended `-x`, `_x`, `-`+30 random, `_`+30 random | all reported |
| (ii) exact key line again at line 20 (twice in file); exact key line only at line 20 | not reported (allowed: it is the public key, by design) |
| (iii) CRLF on all lines / on the key line | dir: reported (false positive); git: not reported (.gitattributes LF) |
| (iii) CRLF file + plant at line 13 | plant reported in both |
| (iv) exact key in sub/sonar-project.properties | not reported (allowed by design, path regex is any folder) |
| (iv) exact key in docs/x.properties; in old-sonar-project.properties | reported |
| (iv) different random key in sub/sonar-project.properties | reported |
| (v) different random 40 mixed key on line 4 of sonar-project.properties; `hadavin-dx_`+40 mixed; near-miss (last char changed) | reported |
| (v) `hadavin-dx_`+40 random LOWERCASE; `hadavin-dx_other-project-`+22 lowercase, line 4 | not reported by gitleaks, but also NOT reported in a non-allowlisted file (k1/k2): the rule does not fire on them, so this is not the allowlist; hygiene (narrow v2 exception) catches them |
| ORIGINAL toml at 558d37f, real tree (control) | reported at sonar-project.properties:4 (the bug) |
| (?m)+line toml: real tree | not reported (works) |
| (?m)+line: different key, key+plant, `-x`, `;`+plant, exact key in docs/x.properties | all reported |

## Corrections to lane 10a SUMMARY
- "Allowlist narrow as written: not testable (it allows nothing)" was wrong: the original allowlist allowed a match on the FIRST line of a file (P3 in 05-neg-orig: the real key on line 1 of sub/sonar-project.properties was not reported), and nothing else.
- The "(?m) and match both worked" claim now has a raw file with the real binary: evidence-v2-5 (m0 to m5, rerun of the tail; the first run of m5 and o0 stopped on a script name error in my driver and was rerun).

## Files in /tmp/demo-wt/handover/demo/gitleaks/
gitleaks-toml-fix-v2.patch, SUMMARY2.md, evidence-v2-1-v2only.txt, evidence-v2-2-merged.txt, evidence-v2-3-exception-narrow.txt, evidence-v2-4-narrowness-matrix.txt, evidence-v2-5-controls-and-multiline.txt, evidence-v2-6-apply-orders.txt, evidence-v2-7-hygiene-extra.txt. v1 patch kept as the record. R-numbers: bible not read (preamble pointer to the private folder ignored as told); rules 3, 5, 6, 12 followed.
