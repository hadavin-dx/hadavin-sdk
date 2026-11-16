# PR63 (core/P1a, head bf955e9) result review, codebase-details, round 1 re-run (condensed; ran nothing)
Evidence: ruff/format/bandit exit 0; sync only; full-312 truncated (8 lines, ~3%, no summary/exit); no 3.13 run, no mutation output, no perf output.
B1 No passing test run on 3.13 (production interpreter, Unicode 15.1.0); no raw output for "128 mutants all killed"; no perf output. No green claim supported.
M1 Stale/wrong docstrings: textnorm.py:818 names_equal says "NFKC, case and whitespace insensitive" but _canon (:743-749) is NFKD/casefold x3; :796 VARIANT comment; module docstring :22-23. VARIANT also fires for NFC/NFD, superscripts, circled digits.
M2 Docstring :58 "size cap checked first, once" false: _checked runs 2-3 times per call (allow_equal :806 -> could_be_same_person :786; scan_needles :672 -> value_scripts, squeeze_views); repeated cost at cap.
M3 Reuse: textnorm.py:324-354 (_char_weight,_pass_weight,_weight,_checked) re-implement guard/runmap.py:181-203 (_nfkd_len,_expanded_len,fits_after_nfkc, MAX_REDACT_CHARS); write down why runmap was not extended or share helper.
M4 Mutants that edit docstring prose, killed by tests asserting prose (~28 of 128; e.g. :446, :495, "words:"): inflate the quality figure; meta-test asserts literal CHANGELOG sentence.
M5 test_textnorm_perf.py wall-clock ceilings (0.5/5/8 s), marked perf, excluded from evidence run; linearity not shown.
Nits: _LOOKALIKES (:270) dead in production; duplicate squeeze/squeeze_views and has_mixed_script vs _kept; hardcoded "15.1.0" (:852) and _PINNED_PYTHON "3.13" (:262); _canon docstring/untestable second fold; has_mixed_script docstring vs _DROP_CATEGORIES (Mc kept); CHANGELOG "20th name" noise; test_k5_round9.py:4119 escape (verify same code point); generator tests skip on Unicode other than 15.0.0/15.1.0 (silent on 3.14).
Checked correct: mutant count 128 (28+12+9+3+16+9+14+5+32); view bounds 6 squeeze / 9 fold / 6 without casefold; 3.13=15.1.0, 3.12=15.0.0; _view_pairs ordering; hidden-channel regex; generator 16 supplements + U+04CF override.
NOT REVIEWED: ticket P1.md (358 KB), fixtures, tests bodies, tools, other guard modules.
