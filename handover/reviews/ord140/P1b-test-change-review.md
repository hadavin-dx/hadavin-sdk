# Fresh review: P1b 1-2 character test change (b0f54b1 -> 864e793)
Reviewer: egm-codebase-details (fresh, read-only, did not run mutants). Verdict: WEAKER (narrowly).
- Old: `short.strip()=="" or short not in str(caught)`. New: raw check dropped for stripped length < 3; only `repr(short)` checked.
- Only the value "x" collides with the fixed message (contains "exact-match"); "Li", "7", the one-character ideograph and its padded forms do not.
- A mutant that leaks the raw value unquoted or in double quotes now survives for those values (old test killed it).
- Gap that existed before and after: the first assertion does not check TEXTNORM_MIN_DIGIT_CHARS, so a digit-minimum mutant is not killed there.
- Nit: the new test comment says the quoted form "is what would show the value": true only for a single-quoted repr.
- Ticket wording for the minimums (P1.md line 209: scan 6, id 8, digits 6) differs from what the code pins (digits 6 in code; spelling 2, squeeze 4, script 4, ideograph 2); not resolved by the reviewer.
Action: builder told to restore the raw check except for "x", add a killing mutant and the digit-minimum assertion (q327).
