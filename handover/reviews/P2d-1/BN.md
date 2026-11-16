# BN: what the P2d ticket (section P2d-1) got wrong

1. The ticket names `textnorm.LOOKALIKES`; in P1a it is the private `_LOOKALIKES`. Not imported by the tests.
2. The ticket expects the P1B-1 rows to be XFAIL. On the new code they PASS (P1a's fold drops unassigned code points, so the key is masked); on the old code they show XFAIL (see failbefore-raw.txt).
3. PEM-1 and ASCII-3 cannot force a withheld block with the real PEM pattern (the direct pass masks it). ASCII-3 uses a patched test pattern.
4. ASCII-2's bank-word premise needs a gap of more than 100 characters (_BANK_WINDOW); the test uses 300.
5. The FOLD_NOTE line hit text echoes non-captured pattern text (e.g. `BEGINX` before the secret), so "KEY=" not in out cannot be asserted.
6. P1a's fold does not casefold by default (casefold=False), so SWEEP-1's mixed-case line works as written.
7. Mutant REG-M ("register before the look-alike check") is EQUIVALENT: the journal rollback undoes the early registration whenever the round is discarded, so no test can tell. Replaced by REG-M "the rollback keeps the counters" (killed by REG-1b). The ticket's REG-M is therefore not testable.
8. Mutant 10 needed a non-parametrised killer (a new test, test_text_before_a_masked_value_is_kept_once_between_two_in_place_masks) because the runner's pinned id cannot hold a parametrised id with non-ASCII text.
