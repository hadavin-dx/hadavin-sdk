# P1b on P1a fix4 - evidence (head b700822065943a1460b4c7a8266e7951df7ca02b, local, pushed at the end)

Branch core/P1b, worktree <build-dir>, merged origin/core/P1a c05ba58 (fix4). Date 2026-11-06.

## Import path (every run used PYTHONPATH=<build-dir>/src)
```
3.13.18 15.1.0 <build-dir>/src/hadavin_sdk/__init__.py
3.12.13 15.0.0 <build-dir>/src/hadavin_sdk/__init__.py
```

## Full suite
3.13 (Unicode 15.1.0):
```
...........................................................              [100%]
10404 passed, 455 skipped in 428.97s (0:07:08)
RC=0
```
3.12 (Unicode 15.0.0):
```
...........................................................              [100%]
10404 passed, 455 skipped in 563.53s (0:09:23)
RC=0
```
Gate was pytest's own exit code (RC lines above). Full logs: <build-dir>/fix4run/pytest313.txt, pytest312.txt.

## Mutants (tests/textnorm_mutants.py, 99 = 77 P1a + 22 P1b)
3.13:
```
99 of 99 good; problems: []
RC=0
```
3.12:
```
99 of 99 good; problems: []
RC=0
```
Full lists: <build-dir>/fix4run/mut313.txt, mut312.txt.

## ruff-check
```
All checks passed!
RC=0
```

## ruff-format
```
326 files already formatted
RC=0
```

## bandit
```
[manager]	WARNING	Test in comment: SafeLoader is not a test name or id, ignoring
[manager]	WARNING	Test in comment: subclass is not a test name or id, ignoring
[manager]	WARNING	Test in comment: the is not a test name or id, ignoring
[manager]	WARNING	Test in comment: pinned is not a test name or id, ignoring
[manager]	WARNING	Test in comment: bytes is not a test name or id, ignoring
[tester]	WARNING	nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389
[tester]	WARNING	nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389
RC=0
```

## scan_repo
```

RC=0
```
(bandit: -ll, no medium/high findings; the warnings are pre-existing nosec comments. scan_repo prints nothing when clean.)

## Hygiene grep on added lines vs origin/core/P1a (repo hygiene pattern)
```
0
```
Count 0 (also 0 against origin/main).

## Requirements (P1b-notes.md)
1. could_be_same_person rename, fold_key unused, wording "spelling variants" / "check name": done.
2. Scans use fold_views AND squeeze_views AND scan keys; any view of text holds any view of value, on every scan path: scan_holds is the single choke point; injection uses scan_views. DONE.
3. Empty view refused (EmptyView), with test: done. Consequence: a value with no ASCII letter/digit (Chinese-only) cannot be scanned by scan_holds; it raises.
4. app.build calls require_pinned_unidata() for pilot and prod (src/hadavin_sdk/app.py:87). Fail-before: with the call replaced by `pass` the tests fail (app-guard-removed-fail-before.txt: the pilot and prod builds raise ConfigError, not UnidataMismatch).
5. Mc/Lm/Sk corpus from the interpreter's Unicode data on every scan path (tests/test_textnorm_siblings.py): 452/397/125 code points; 5 Mc and 140 Lm read as letters/digits, 0 Sk, derived from data.
6. CHANGELOG uses fold5 (P1b) / fold4 (P1a). 80% rung re-counted: `confusables` 54/141 = 38% (measured, script rung_measure.py); other candidates UNVERIFIED.

## Fail-before honesty
- P1b-owned tests use new names that do not exist on 37b9ca6, so they fail at import there. That is not a behaviour proof.
- Behaviour fail-before verified directly in a scratch copy of the old tree for the injection and runmap tests; each fix also has a mutant that reverts it (killed 99/99).
- Pins that PASS on old code (not fail-before): the Cn policy test, the egress test, the evidence-stays-exact decision test.
- The app guard has its own guard-removed run (above).

## Honest findings
- squeeze_views are redundant to the scan keys on the Mc/Lm/Sk corpus (a mutant removing only squeeze views survives); the mutant removes both together.
- Mc names in r174-r176 join by the scan key (over-match, safe side).
- Injection detector now flags oversize text as guard_unavailable (behaviour change).
- runmap.canonical no longer composes a base letter plus combining mark.
- KNOWN GAP: runmap.canonical and the evidence key miss Mc/Lm/Sk-hidden "password" for 0 of those code points matched. They are not secret scans; scan_holds is.
- 3.12 uses Unicode 15.0.0; pilot/prod refuse it by design.

## NEEDS LEAD (order 81 sibling items)
- src/hadavin_sdk/guard/runmap.py:276 `canonical`: now per-character NFKC (same text as _canonical_view[0]); composition lost. Why: Mc/Lm/Sk-safe path. Lead to confirm.
- src/hadavin_sdk/guard/injection.py:45 `_score`: scans raw + scan_views; oversize text raises and becomes a guard_unavailable flag. Lead to confirm the fail-closed flag.
- src/hadavin_sdk/runtime/evidence.py:56 `normalise`: deliberately UNCHANGED (exact). Grounding is an ALLOW comparison, so a look-alike fold would let fake evidence ground. Lead to confirm.

## NOT run
- No CI, no 3.14 job, no pilot/prod deployment, no live Postgres beyond what the full suite includes.
- PyPI candidates other than `confusables` not measured (UNVERIFIED).
- Egress (V11-1) and the look-alike placeholder marker (P1c): not done, by order.

---
# Merge of origin/core/P1a 2572847 (fix5 + main 13ebfaf) into core/P1b - head 06de58995df8bde34871f3d203d6bc40ee2f5169

Plain merge (no rebase, no force, no amend). All runs with PYTHONPATH=<build-dir>/src; import path:
```
3.13.18 15.1.0 <build-dir>/src/hadavin_sdk/__init__.py
3.12.13 15.0.0 <build-dir>/src/hadavin_sdk/__init__.py
```

## Full suite (pytest exit code)
```
3.13:
10544 passed, 455 skipped in 496.84s (0:08:16)
RC=0
3.12:
10544 passed, 455 skipped in 650.62s (0:10:50)
RC=0
```

## textnorm_mutants (113 = 77 P1a fix4 + 22 P1b + 14 P1a fix5)
```
3.13:
113 of 113 good; problems: []
RC=0
3.12:
113 of 113 good; problems: []
RC=0
```

## ruff-check
```
All checks passed!
RC=0
```

## ruff-format
```
329 files already formatted
RC=0
```

## bandit
```
[manager]	WARNING	Test in comment: SafeLoader is not a test name or id, ignoring
[manager]	WARNING	Test in comment: subclass is not a test name or id, ignoring
[manager]	WARNING	Test in comment: the is not a test name or id, ignoring
[manager]	WARNING	Test in comment: pinned is not a test name or id, ignoring
[manager]	WARNING	Test in comment: bytes is not a test name or id, ignoring
[tester]	WARNING	nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389
[tester]	WARNING	nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389
RC=0
```

## scan_repo
```

RC=0
```

## Hygiene grep on lines added vs origin/core/P1a
```
0
```

## How the conflicts were resolved
- textnorm.py: all nine conflicts were docstrings; the code merged cleanly. P1a fix5's marks-dropped views (`_without_spacing_marks`, `_views(marks_dropped=)`) and P1b's `scan_keyset`, `scan_holds`, `EmptyView`, `_PUNCT` map and fold5 both hold. One real fix: `_all_views` (behind `scan_views`/`scan_holds`) now reads the six-view `fold_views` (marks_dropped=True) so it matches the public `fold_views`; `scan_views` is now at most 6 + 6 + 8 = 20 views (was 14).
- Generator: name rules (fix5) kept, `_SMALL_CAP` dropped, Scripts.txt/_scripts.py (P1b) kept. Output of the generator equals the checked-in `_confusables.py` (852 entries) and `_scripts.py` (751 ranges).
- app.py: `is_live(cfg.environment)` (main) plus `textnorm.require_pinned_unidata()` (P1b).
- Golden regenerated on 3.12 (15.0.0) and 3.13 (15.1.0), alg fold5; manifest regenerated (five files; data files kept).
- Mutants: both lists kept (113). Meta counts updated. The P1b mutant "scan_views: only fold_views are read" lost its old killer, because fix5 makes fold_views alone find every Mc/Lm/Sk hiding; it now has its own unparametrized killer in test_textnorm_scan.py (`test_scan_views_has_the_fold_the_squeeze_and_the_scan_keys_and_no_empty_view`).
- NOT weakened, but changed because fix5 changed the facts (each is a test of P1b that assumed the old facts):
  * siblings: the `_reads_as_letters` exemption (5 Mc, 140 Lm) is gone; every Mc/Lm/Sk code point must be found by scan_holds, scan_views, fold_views AND squeeze_views (stricter than before).
  * `test_no_value_of_the_table_is_zero_or_one` became `test_no_letter_of_the_table_is_read_as_zero_or_one`: fix5's name rules add digit forms that NAME 0, 1 and 10 (category No); a letter-like source mapping to 0/1 still fails. The digit-decision table has three new entries.
  * enclosed-forms pin: the selection without a table entry fell from the ticket's 135 to 30 because fix5 reads most of them from their names. The test now requires (selected + in table) >= 100 and selected >= 20, and still requires no ASCII key for the 30.
  * `scan_holds` both-sides test: dropped the assertion that fold_views misses a spacing mark (false after fix5); added a punctuation case ("pass-word") that only the squeeze half finds, on both sides.
  * `test_textnorm_app.py`: `dev_cfg` became `demo_cfg`, `deferred.LIVE` became `stages.is_live` (main's stage rename).
  * differential: rows r114 to r117 (dashes, quotes) are strict expected failures in P1a; here P1b reads them, so the P1b version of the test (which has no xfail for them) is kept.
- Behaviour kept from P1b: `scan_holds` still raises `EmptyView` for a value with no ASCII letter or digit (Chinese-only), although fix5 can scan such a value through `fold_views`. This is the P1b notes' order ("refuse an empty view"); a lead may want to relax it now that fix5 exists.
- The changelog "squeeze views are redundant" finding is obsolete: fix5 makes fold_views and squeeze_views each find all 974 Mc/Lm/Sk code points.

## NEEDS LEAD (unchanged)
- src/hadavin_sdk/guard/runmap.py `canonical`; src/hadavin_sdk/guard/injection.py `_score` (and the oversize-text guard_unavailable flag); src/hadavin_sdk/runtime/evidence.py `normalise` (left exact on purpose).

## NOT run
- No CI, no 3.14 job, no gitleaks, no live Postgres beyond the full suite.
