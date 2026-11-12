FAILED: gitleaks reports findings on 558d37f (dir: 1, git: 2), so the allowlist in .gitleaks.toml does not work as written. A corrected version is in gitleaks-toml-fix.patch (0 findings, hygiene test 10 passed). Allowlist narrow as written: not testable (it allows nothing); narrow after the fix: yes.

EVIDENCE RUNNER: ran and recorded, no verdicts. Head 558d37fe5372f8c378e7ea07c6193a738f4497ed (fresh full clone, 14 commits, not shallow). Binary /tmp/work/gl/gitleaks, `gitleaks version` = 8.30.1, sha256 of the binary in 01-version.txt (the tarball sha256 was not re-checked: the binary came from the earlier lane, not downloaded by me). All planted values are made up, built at run time from random letters in /tmp/work/scr/neg.py, only in scratch copies, never committed to the real tree; no real secrets.

## Commands (copied from .github/workflows/lint.yml, flags literal)
gitleaks dir . --config .gitleaks.toml --redact --no-banner --ignore-gitleaks-allow   -> exit 1, leaks found: 1 (02-dir.txt)
gitleaks git . --config .gitleaks.toml --redact --no-banner --ignore-gitleaks-allow   -> exit 1, leaks found: 2 (03-git.txt)
Detail (02b-findings-detail.txt; that file was produced after pytest had left cache folders in the tree, so its pycache lines are my own noise; the first two runs above were before pytest): the real finding is generic-api-key, sonar-project.properties line 4 (the projectKey line), in the tree, and in commits 7ec367b and a0b97a4.
tests/test_hygiene.py only, GITLEAKS_BIN + DPLD_REQUIRE_SCAN=1, venv from requirements-dev.txt with --require-hashes: 1 failed, 9 passed (04-hygiene.txt). The gitleaks part ran (not skipped) and failed on "gitleaks dir reported findings".

## Cause (tested with the real binary in /tmp/work/gl-fix)
With regexTarget = "line", gitleaks hands the regex the line WITH the line break before it, so `^sonar\.projectKey=...$` fails on every line except the first line of a file (in the negative test the same real line on line 1 of sub/sonar-project.properties was allowed, on line 4 of the real file it was reported). Adding (?m), or using regexTarget = "match" (the matched text only), both made the real line pass. The original line regex is also too broad: `hadavin-dx_[a-z0-9-]+` accepts any value after the prefix (06-regex-test.txt).

## Fix (gitleaks-toml-fix.patch, git diff vs 558d37f, `git apply --check` OK on a fresh clone, 07-apply-check.txt)
.gitleaks.toml: regexTarget = "match"; regexes = ['''^sonar\.projectKey=hadavin-dx_duplicate-proof-lead-desk-n8n$'''] (the exact key); paths unchanged: `(^|[/\\])sonar-project\.properties$`.
exceptions.txt: the git-grep exception for sonar-project.properties now also lists .gitleaks.toml, because the new exact literal in the toml is itself flagged by tests/test_hygiene.py (first version of my fix failed that test at line 124; the exceptions line cannot contain the literal either, so it uses the same `[a-z0-9-]+` shape as the existing line).
With the fix on a fresh clone at 558d37f: dir exit 0 no leaks, git exit 0 no leaks (14 commits), hygiene 10 passed (08-fixed-dir-git.txt, 09-fixed-hygiene.txt).

## Negative tests (scratch copies /tmp/work/gl-neg-orig and gl-neg-fixed, plants committed there only; 05-neg-orig.txt, 05-neg-fixed.txt). Result = reported by gitleaks dir and git
| Case | Plant | Original toml (558d37f) | Fixed toml |
|---|---|---|---|
| real | sonar-project.properties:4 real projectKey line | REPORTED (bug) | not reported (allowed, as intended) |
| N1 | sonar.token=<made-up 40 mixed>, line 13 same file | reported (rule sonar-api-token) | reported |
| N2 | sonar.projectKey=<made-up 40 mixed>, line 14 | reported | reported |
| N3 | sonar.projectKey=hadavin-dx_<made-up 40>, line 15 | reported only because of the line-break bug; the regex itself would allow it | reported |
| N4 | sonar.token=<made-up> in sub/sonar-project.properties | reported | reported |
| N5 | sonar.projectKey=hadavin-dx_<made-up> in docs/y.properties | reported | reported |
| P1 | real line in docs/x.properties | reported | reported (path does not match) |
| P2 | real line in old-sonar-project.properties | reported | reported (path does not match) |
| P3 | real line in sub/sonar-project.properties | not reported (line 1) | not reported: allowed, because the path regex matches any folder |
Both the dir and git scans gave the same per-plant result (git also still showed the two old history commits with the original toml, none with the fixed one).

## What the regexes match (python re, 06-regex-test.txt; gitleaks uses Go RE2, same results for these simple patterns except that Python is not the real engine)
Path: `(^|[/\\])sonar-project\.properties$` matches sonar-project.properties, sub/sonar-project.properties, a\sonar-project.properties; not old-sonar-project.properties, xsonar-project.properties, sonar-project.properties.bak, docs/x.properties. So the path part is any folder, not only the repo root.
Fixed match regex: only the exact text sonar.projectKey=<the one key>; not the made-up key, not sonar.token.

## Not checked
Gitleaks docs not read (no lookup; behaviour found by experiment only). Tarball sha256 from lint.yml not re-verified. Full pytest suite not run. CI itself not run. P3 (sub folder allowed) is left as is; restricting to the repo root would need `^sonar-project\.properties$` (not tested). Windows path behaviour not tested. The tree gl-tree was touched only by my own pytest run (caches removed afterwards); no commits, no push. No processes left running.
