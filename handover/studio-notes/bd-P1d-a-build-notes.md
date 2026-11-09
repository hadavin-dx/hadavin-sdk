# P1d-a build notes (builder, 2026-11-09; branch core/P1d-a; base main 2742c1b)

Plain wording: "base" = main before this work. "Property" = a test over 2,000 generated texts.

## Rows and mutants corrected at build (ORDER 191)
1. Row L9 input: `"a" * 2894 + " x.com"` is masked as a high-entropy key on the base (output `<HIGHENTROPY_1> x[.]com`), so it never reached the length check. Input now `("lorem " * 500)[:2894] + " x.com"` (2,900 characters, unmasked, shown text 2,902). Base cell and expected unchanged (the too-long notice).
2. Row L8 named assert: the ticket says "both fences kept"; I wrote six backtick triples, there are four (two fences, two lines each). Fixed to four.
3. Row/mutant additions from lead ORDER 192: rows K41 (card, model) and K41q (model), fail on base; mutants A44 (plain key prefix back to `{0,40}`, killer K41 model) and A45 (query key prefix back to `{0,40}`). Rows now 70 (fb 37, pb 30, ow 3).
4. A15 (query key lookbehind removed): killer assigned K41q; see mutant result below.
5. Ticket arithmetic: ALPHABET-A as spelled out has 72 entries (36 letters/digits, 23 other single characters, 13 tokens), not 63; ALPHABET-B has 66, not 57. Used the spelled-out list; asserts say 72 and 66. Ticket needs a revision of the two numbers. G-EH `w(1)` taken as ONE letter drawn by `pick` (no length draw).
6. `run_mutants` has no `forbid_skips` on this base; omitted (noted in `tests/p1d_a_mutants.py`).

## Product deviations from the ticket
- `_defang_prose` first reads `[.]` between name characters as `.`. Without it `defang_text` was not idempotent (`_NON_ASCII_HOST` looks behind `[` but not `]`: `e.rg<.f` defanged further on a second pass) and the pre-redaction differential failed on correct code. Side effect: `clean()` now also shows a typed `[.]` between name characters as `.` (before: kept). Needs the lead's yes; the slack path already did this (L15).
- INFO-K41 fix (ORDER 192): both generic-assignment entries use key prefix `[\w.\-]*` instead of `[\w.\-]{0,40}`. Timing probes (20,000-character token, 8,000 `&p`, 8,000 `a.`): same as base (0.03-0.05 s). `tests -m perf` of test_k5_perf: 8 passed.
- Ticket places to change for ORDER 192: R3/INFO-K41 mentions, the A15 "expected survivor/equivalence" text and NEEDS LEAD 4, Non-goal wording, mutant counts (50), row counts (70).

## Properties that FAIL on this build (stopped per the ticket rule; nothing edited)
- `test_stored_card_round_trip`: 29 of 2,000 texts differ (base: 137). Minimal: `m@e.na.@l.ln` -> card `<EMAIL_1>.@l[.]ln`; Slack path re-redacts to `<EMAIL_1><EMAIL_2>`. Cause: the e-mail pattern is not idempotent on its own output (a second pass finds `.@l.ln` as an address); outside P1d-a (P1d, e-mail formatting). The property cannot hold while the redactor is not idempotent. Lead decision needed: restrict, or fix the e-mail pattern in P1d.
- `test_no_link_outside_code_on_card`: 35 of 2,000 fail (base: 222 of 2,000 by the same test less the placeholder-dot regex). All 35 hold a backtick in the input (0 without). Minimal: "`````\n```l.sm```": the gate reads inline code line by line (`_INLINE_CODE`), CommonMark reads it across the paragraph, so `l.sm` is code to the gate and plain text to the parser. Also `` `．password=``` `` (an unpaired backtick). A real gap in the existing inline-code reading, not in the new code; fixing it means reading code spans from the CommonMark parse of the final text. Lead decision needed (own package or here).

## BS-1 (seed 1, both paths): exit 4
635 samples. Exact: all shapes except S5x (266 of 268 on each path). LEAK 0 everywhere. The 2 over-masks: `password=v&ziU&ne; delta ...` and `auth_token=vR&eU&ge; oscar sierra`: the secret ends in `&ne;` / `&ge;` (an HTML entity name), and the `;` is hidden too (one extra character). REAL 30/30 exact. S7 (report only) exact as predicted. Raw: handover/evidence/P1d-a/head-wip/bs1-overmask.txt.

## Not run / not done
- Step 7 of BS-0 (read the two fuzz tests of P1d V8) and the WHATWG reading (step 8; citation stays UNVERIFIED per ORDER 192): not done. BS-0 step 6 grep for other callers: not recorded in bs0-base.txt (only the full test run shows no caller broke).
- LIT collected only 18 strings (direct literal arguments); the differential and default-unchanged properties are weaker than the ticket intended for that reason.
- Evidence snapshot worktree, Python 3.12 run, perf run on 3.12, pip-audit, semgrep, zizmor, gitleaks, Trivy: not run. No pull request opened.
