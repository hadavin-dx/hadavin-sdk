# P1a fix6 evidence (head 2ff0afef3fc8d44afaacac5415255e09458b5b14)

Logs in this folder, each with the head SHA in its header: mutants-py313.txt, mutants-py312.txt, pytest-py313.txt, pytest-py312.txt, fail-before.txt, static-checks.txt.

## Slips first
- I ran ruff format after writing mutant search strings and edited tests while the first finals started. That finals run was invalid (90 of 96 mutants good); I killed my own processes, deleted its logs and redid ALL finals at this head. Nothing from the invalid run is used.
- The first fail-before run used -x and stopped at the first failure; it was redone without -x (the log is the second run).
- The perf and pin tests cannot fail on old src (they test the test side). They are NOT in the 16 below. Evidence for them: the old perf texts have a weight above the cap, so the old tests timed a refusal; the old pin test with the variable set to "true" on 3.12 skipped instead of failing.
- Not run: Postgres (455 skips on each interpreter), Windows, Python 3.14, gitleaks, upstream sha256 check (needs network), CI.

## Results at this head
- mutants: 96 of 96 good on 3.13 (Unicode 15.1.0) and 3.12 (15.0.0).
- pytest: 10406 passed, 455 skipped, 10 xfailed, 0 failed on each; 3.13 ran with HADAVIN_REQUIRE_PINNED_UNIDATA=true.
- fail-before (fix6 test files against old 2572847 src): 16 failed, 635 passed (list in fail-before.txt).
- ruff check and format --check clean; bandit -ll rc 0; scan_repo rc 0; hygiene grep on the pushed diff: 0 hits.

## Items
- p1a6-001: done. New script view in fold_views (non-ASCII letters and marks of the marks-dropped view). DEVIATION: ASCII letters and digits are dropped too, otherwise an inserted ASCII letter hides the value. fold_views now has up to 9 views. Minimum view length: defaults.TEXTNORM_MIN_VIEW_CHARS = 2 via scan_needles / ViewTooShort, one number for every view (judgment call: the order said refuse an empty view; 2 is stricter). Pinned tests: space, hyphen, line break, ASCII letter found; benign negatives not found. Coverage sentence updated everywhere.
- p1a6-002: done. Perf tests assert _weight(text) <= CAP, Greek-pairs unit fixed, ceilings about 8x measured time on the real fold.
- p1a6-003: done. The MAX_VALUE_LEN claim is dropped from gen_confusables.py; CHANGELOG pointer fixed. The ticket pointer wording in the order was unclear; I dropped the claim and added a fix6 note.
- p1a6-004: done. Default casefold=False kept; THE RULE FOR A SCAN says pass casefold=True with the reason; one test fails if a scan without casefold misses a case variant.
- p1a6-005: done. Insertion-only wording and R13-LM-MIX not caught; Sk wording; step 3; one identical coverage sentence in textnorm.py, gen_confusables.py, CHANGELOG (tested identical); alias CONFUSABLES renamed _CONFUSABLES (not exported, tested); stale ticket names note; mutant count 96; "none is skipped" made true.
- p1a6-006: done. Sweep row or named exclusion per unread class; mathematical forms; circled 11-20 named as a gap; real Thai case; escape dropped; _read_by_data replaced by a cached reading; G4 checks which letter.
- p1a6-007: done. sup merged into out before the name rules; test fails on the old code.
- p1a6-008: done. Pin test accepts "1", "true", "yes" case-insensitively and rejects other values loudly; a test calls require_pinned_unidata from product code.

## Disagreements and notes
- Script view drops ASCII (above). Minimum 2 vs "empty". New public names (ViewTooShort, scan_needles; 22 names). alg stays fold4; only the fold_views golden hash changed. Equivalent Sk mutant remains.
