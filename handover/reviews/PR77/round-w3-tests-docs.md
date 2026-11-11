# A11a / PR77 (core/P2d-1, snapshot 8b2b716) - fresh reviewer, slice: tests, fixtures, docs. Read only, nothing run.
Coverage: all test files read in full except test_k5_round12_fuzz/test_k5_round9/test_no_hardcoded_values (diff hunks) and textnorm_names.json (first 40 lines), textnorm_corpus.json (grep). NOT checked: sha256 values vs real files, mutation runner handling of duplicate snippets, ticket lines 211-400.
Findings (2 Major, 6 Minor, 3 Nit, 1 unchecked):
- F1 Major tests/test_redact_fold.py:354-363 test_digits_1 card half: asserts `[0-9]{8}` on a space-grouped card; no 8-digit run exists, so it cannot fail. Fix: strip spaces, search 16 digits.
- F2 Major test_redact_fold.py:458-467 test_sep_1: asserts only "exemple.fr" gone; never asserts the password (head) is gone. Add `fold(head) not in fold(out)`.
- F3 Minor test_map_6 vacuous for email alias. F4 Minor budget HOSTILE-2b fails by TypeError on old tree (fail-before = U not A). F5 Minor fake secrets as whole literals (V13 etc.) vs build-from-parts rule. F6 Minor HOSTILE-1 does not pin masked vs withheld. F7 Minor CHANGELOG cost/does-not-promise text differs from ticket; internal ids in user text. F8 Minor defaults.py REDACT_BUDGET_S "see CHANGELOG" dangling.
- F9 Nit CHANGELOG 90 mutants vs 91. F10 Nit private _LOOKALIKES. F11 Nit CountedClock global patch (check monkeypatch).
- F12 Unchecked redact_mutants mutant 21 old snippet appears twice in runmap.py (502, 525); runner behaviour unknown.
