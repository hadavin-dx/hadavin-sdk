# review-price-guard-3 (fresh egm:egm-codebase-details, read-only, round 3, 2026-11-20 ~13:33 UTC)
Target: wip/lead-b-price-guard head 28f6a924e (base 20ef755fb). Static read only: no tests, no git, no mutants run by the reviewer.
Verdict: 0 Blocker, 0 Major, 2 Nit. Round 1 findings and round 2 nits (read-twice TOCTOU, unrelated bad route, AttributeError catch) verified CLOSED by reading; the swap test fails if chat reads the route twice (mutant G12).
Nit 1 common.py:363: build checks every route, chat only the called one; consistent with the config rule (only fake may have price 0). Intentional: add a comment if wanted.
Nit 2 common.py:376: unknown route name raises bare KeyError before any check (looks pre-existing, base not diffed); priced() return value unused. Optional.
Not checked by reviewer: tests/ruff/mutants (builder claims: 545 passed group, 32 failing ids identical to clean base 20ef755fb, 12 of 12 mutants); legitimate callers outside src; pydantic version behaviour of Route._price.
Lead note: round 3 fresh pass found no Blocker/Major: the review loop for this diff is complete. Remaining before FIXED-VERIFIED: the evidence campaign on the integrated branch.
