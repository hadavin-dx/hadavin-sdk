# P1 v3.2.1 delta: NOTES (patch sonar-p1-quickwins-v3.2.1-delta.patch; base db54e13 + sonar-p1-quickwins-v3.2.patch)

Preamble points applied: 5, 6, 7, 20. EGM (13) NOT run by me: the lead runs it. No bible access in this shell, no R-numbers cited. No push, no network write. No suppression comments added (a first draft used `noqa` on two `subprocess` calls; ruff flagged S603/S607; I removed them and used the repo's existing `hygiene._git_text` helper instead).

## What did not work, is uncertain or was not run (first)
- Delta only works AFTER v3.2: alone on db54e13 it fails (`tests/test_raw_bidi_chars.py: No such file`). Checked: P1 then D ok, D then P1 fails (expected).
- Two of my own first drafts were wrong and are fixed before the patch: (a) an assignment prefix with an unbounded `*` made `then a=then a=...` quadratic (10.1 s for 250 lines of 4000 chars); fixed by `{0,8}+` (at most 8 assignments, possessive) and the shape is now in the timing test; a mutant that puts the unbounded form back is killed (11.5 s run, fails the 2 s bound). (b) hygiene scan (rules: drive path, TLD) flagged my new test text (`jobs:` followed by backslash-n, `run.sh"`); rewritten with line lists and a built name; no suppression.
- Mutants first run: 3 survivors of mine (`"` escape inside double quotes, `is_file` check in the bidi test, `splitlines` in the bidi test); three tests added; rerun: 63 of 63 killed.
- Not run: full suite (lead runs it), the 8 playwright tests (skipped here), actionlint, real Windows, SonarCloud, bash 3.2. The Windows safety of the new temp-repo tests is by reading only: they use plain tmp_path, `newline="\n"`, no shell, utf-8; the accented name needs a file system with Unicode names (NTFS has them). The newline-in-name case is NOT tested (Windows cannot create it); the accented name shows the same `git ls-files` quoting.
- I cannot see the SonarCloud result. Test-only delta: no scripts, no workflow, no README change, so no Sonar issue count changes by this patch (the 15 issues of v3.2 stay as predicted there).

## Files touched: 2, both from v3.2
tests/test_shell_single_bracket.py (+232 lines in the diffstat) and tests/test_raw_bidi_chars.py (+29). Never tests/test_hygiene.py, never scripts, lint.yml, README. +219 -42 lines in all.

## What the delta fixes (reviewer rv24 item -> change -> proof)
| rv24 | change | proof |
|---|---|---|
| Minor 1 workflow-level `defaults: run: shell:` | `_workflow_shell_problems` checks the workflow default, job default, step | 2 table cases; mutant "workflow default ignored" killed; old code returns [] (evidence 3) |
| Minor 2 `ls-files` without -z | `_tracked(repo, pattern)` uses `-z` and `\0`; a tracked name missing on disk is skipped (its two shipped scripts must still be listed) | tmp git repo with an accented name (test): old way gives `"caf\303\251_run.sh"` then FileNotFoundError (evidence 3); mutant without -z killed |
| Minor 3 `FOO=1 [ x ]` | regex: up to 8 assignments (`name=value`, `name+=value`, empty value ok) allowed before `[`; value cannot hold `; & \| ( ) { `` ` (so `a=$(b [ x ])` is not flagged) | 7 flagged + 4 not-flagged probes; 3 mutants killed |
| Minor 3 stray apostrophe `echo don't; [ x ]; echo it's` | NOT a bug: bash itself reads `'t; [ x ]; echo it'` as one quoted string, so no test runs. Documented in the docstring and pinned as a not-flagged probe | probe |
| Minor 3 escaped quote `\" ; [ x ]; \"` | the quote regex now consumes a backslash escape (outside quotes and inside `"..."`; inside `'...'` the backslash stays literal) | 3 flagged probes, 2 not-flagged (`echo a\;  [ x ]`, `"a\" ; [ x ]; \"b"`); mutants killed after one extra probe |
| Nit 4 `jobs:` null crash; composite actions | `or {}` / list checks; `_step_groups` reads jobs and `runs.steps`; `_load_tree` reads `.github/actions/*/action.yml\|yaml` | 6 null shapes test; tmp tree test with .yml, .yaml, 2 action files and a .txt (not read) |
| Nit 5 two survivors | the tree check moved into `_problems(scripts, workflows, allowed)` and `_load_tree(repo)`, tested with synthetic input | shebang (4 wrong shebangs), `*.yaml`, action globs: all killed |
| Nit 6 "step None" | `step N (name or unnamed)`, N 1-based | test + mutants |
| Nit 7 `echo a ! [ x ]` | fixed: `!` counts only as `!` + blank right after a command start (`if ! [`, `{ ! [`, `! a=1 [`) | probes both ways; mutant "! anywhere again" killed |
| Nit 8 timing | kept the 2 s bound, shapes added (assignments, escapes, `!`) | evidence 6 |

New known gaps, listed in the test docstring: `env FOO=1 [` not seen; more than 8 assignments before a `[` not seen; a `\` at the end of a line does not join lines.

## Measurements
- Tests (evidence 1; git add -A; DPLD_REQUIRE_SCAN=1; gitleaks 8.30.1): hygiene, shell_single_bracket, raw_bidi_chars, workflow_run_flags, reset_scripts, gitleaks_exceptions, workflow_files_parse: 264 passed. Other affected (followup_edge_cases, lead_step_route, smtp_provider, mode_safety): 182 passed, 8 skipped (playwright). Combined tree P1 D ND P2 P3 NH NR Y C5: 280 passed in the same set.
- ruff check, ruff format --check (149 files; 153 combined), mypy --platform linux and win32 (26 files; 28 combined), bandit -ll: all clean (evidence 2, 8).
- Fails before (evidence 3): old v3.2 code gives the wrong answer on all 5 probes, raises AttributeError on `jobs:`, returns [] for the workflow default, prints `step None`, and `git ls-files` without -z gives a quoted name that raises FileNotFoundError.
- Mutants (evidence 4): 63 of 63 killed, 0 survived: the 31 builder mutants of v3.2 re-mapped to the new text (30 map one to one; the "ls-files only scripts" one now cuts the list in `_load_tree`), the reviewer's 16 (the 2 survivors now killed, the other 14 inside or next to the 31), and 20 new ones (assignment prefix dropped, `+=`, value class, unbounded repetition, escape handling x2, `!` anywhere, glob x3, actions steps, null crashes x3, unnamed, number from 0, bidi: -z, `\0`, binary, is_file, splitlines, 4 character-range cuts). Real files (evidence 5): `if [ -e x ]` put into reset.sh, start_all.sh, lint.yml, sonar.yml fails the repo test (4 of 4); a raw direction character in a tracked file fails the bidi test (12 of 12).
- Timing (evidence 6): every 1 MB shape, 3999 and 4000 char lines: worst 0.57 s (500k short lines), shapes 0.1-0.5 s; the new `then a=` shapes 0.3 s; test bound 2 s each. The 110 rv24 probes: old and new differ on 2 items only: `FOO=1 [ x ]` (now flagged, was the rv24 miss) and `echo a ! [ x ]` (now not flagged; rv24's list had labelled it "ideal 1", which was the false positive).
- Apply matrix (evidence 7, git apply on db54e13): each of P1, P2, P3, ND, NH, NR, Y, C4, C4f, C5 alone ok; D alone FAILS (needs P1); P1>D ok; lead order P1 D ND P2 P3 NH NR Y C5: ok, D last ok, with C4 or C4f ok, crlf first ok; 200 random orders of 8 patches (P1 before D) 200 ok; +C5, +C4, +C4f 150 ok each; exhaustive orders of P1 D NH ND Y with each crlf (360 each) all ok. Patch names used: P2 = sonar-p2-regex-http-bug-v2.1, P3 = sonar-p3-path-helper-v3, ND = nodemo-fix-v2, Y = merge-ready/sonar-yaml-test-trimmed-v2, C5 = skips/crlf-guard-v5; NH/NR = nodemo-optional-hygiene-repo-v2 / nodemo-ruff-isort. D touches only the two test files, so it can only conflict with a patch that edits them (none does).

## Per-rule count (Sonar): 0 changed (test-only delta). The 15 expected clears of v3.2 are unchanged.

## Rung table
| component | need | rung tried | verdict |
|---|---|---|---|
| tripwire fixes | close rv24 gaps | still a regex tripwire; shellcheck SC2292 not a repo dependency (not checked) | KEEP as tripwire, no new tool |
| temp-repo tests | prove -z, glob, action loading | standard pytest tmp_path + the repo's own git helper | CUT-TO-CONFIG+GLUE |

## Fresh read rv28 (05:24Z, session lead): P1 v3.2.1 CLEAN, one regression to list as a KNOWN GAP
0 Blocker, 0 Major, 1 Minor, 4 Nit (sonar/REVIEW-p1v321-fresh.md). Minor 1 (NOT listed above by the builder): the double negation `! ! [ x ]`, `if ! ! [ x ]; then` and `{ ! ! [ x ]; }` were flagged by v3.2 and are NOT flagged by the delta (the new pattern allows exactly one `!\s+` before the assignments). Contrived, not in the repo. Fix if wanted: allow `(?:!\s+){0,4}+`. Other differences from v3.2 are corrections (`echo a ! [ x ]`, `echo ! [ x ]`, `FOO=1 ! [ x ]`, escaped `\;`/`\"` were false positives). Nit: one reader mutant survives (single-quoted strings also consuming a backslash escape; the probe `echo 'a\'; [ x ]; echo 'b'` kills it and is flagged correctly); `.github/actions` does not exist in the repo (composite-action scan only runs on synthetic trees; a malformed action.yml would raise from yaml); temp-repo tests do not clear GIT_DIR/GIT_INDEX_FILE (as the existing hygiene tests; matters only from a git hook); the action glob is one level deep (GitHub's layout). Evidence of the reader: 488 comparisons + 400k-snippet fuzz; 460 shape/width timing cases at 1 MB worst 0.34 s, linear to 16 MB (5.38 s); base flags 9 lines, v3.2.1 tree 0, combined 10-patch tree 0; 200 random orders of 10 patches 0 bad; 216 tests passed on py3.13, 283 on the combined tree py3.12; 25 of 26 mutants killed.
