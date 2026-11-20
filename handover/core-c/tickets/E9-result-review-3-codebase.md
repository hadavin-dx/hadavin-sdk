# E9 result review, round 3 (fresh, codebase). Read only, nothing run.

Verdict: 0 Blocker, 2 Major, 4 Nit. E9 code and tests do what E9 claims
(`_OWN_TOKEN`/`_OWN_OUTPUT` SECRET-only, `_decide` use, mutants E9-1..3 each
unique and killed by the named test, option (a) pinned, core-c guard traced).

## Major
1. The look-alike guard in `_place` (redact.py, drops the `_bare` core when the
   value holds ‹ or ›) has no mutant of its own, and its comment is narrower than
   the code. A value that merely contains one stray `›` (`password=hunter22!›`)
   gets no core entry, so a bare later copy of `hunter22` stays in clear (fail
   open, stated nowhere but the G12c plan). Needed: a mutant per disjunct, a test
   for a single stray ‹ or ›, rewrite of the comment. Owner: G12c (narrow guard).
2. README draft K43 (inputs/SECURITY-README-v6.md ~598-601, table ~889) is stale:
   line refs (code now 967-990 and 1781-1786), wrong cited test, and it omits two
   stated limits (a run of genuine typed `<SECRET_n>` tokens; a value made of
   genuine placeholders of any kind, `password=<EMAIL_1> <IPV4_1>`) and the full
   cut-off range up to `<SECRET_12`. Owner: docs pass (v7).

## Nit
1. ESCALATIONS.md:80 limit wording omits the any-kind genuine-placeholder case.
2. ESCALATIONS.md:80 "pinned by 5 tests" is unclear; count is 3 parametrised, 1
   cut-off, 1 effect (N4), 1 redact_untrusted pin.
3. redact.py ~1826-1827: two comments run together; `‹EMAIL_1›` attribution
   ambiguous (guard and `_placeholder_like` both catch it).
4. Test-file docstrings could cross-reference the junk-entry trade-off.

## Not verified
No tests or mutants run; G9/G13 effects on the junk-entry run-map test
(hardening.py:245-262) by reading only; runmap.py and tools.py not read.
