# G8 build notes (builder, branch wip-g8, base bf5b0368e)
Adopted G8 v6 (tickets/G8-glued-rest-gap-v6.md, appeared mid-build) over v5 + the round 5 acceptance list. Appendices A, B from v6; C, D, E, F
byte-equal to v5's (checked with diff against v6's text). D and E applied with `patch -p1 --fuzz=0`, no offsets reported, no regeneration.
My own first-draft rows (93-101 in a different order, kind `card`, AT8 only) were replaced by v6's; same 9 shapes, same measured outputs.

## Results (TESTED)
- Phase 0 on `git archive HEAD`: step 0 `0 differ`; fail-before (v5 appendices) `109 failed, 310 passed, 26 xfailed`; with v6 files `110 failed, 331 passed, 35 xfailed` (matches v6).
- With G8, v5 files: `419 passed, 26 xfailed` (-n 2). With v6 files: `441 passed, 35 xfailed` (-n 2). Matches v6.
- Step 2 suites (15 files, -n 2): `6833 passed, 3 skipped, 4 xfailed`.
- Perf (G8 file, no xdist): `14 passed`.
- `python tests/g8_mutants.py`: `34 of 34 good`. ruff check clean; ruff format --check `352 files already formatted`; bandit -ll: 0 issues.
- NOT RUN: full suite, tests.g8_cost compare, phase 0 (d)(e)(f), other mutant suites, G8a-only variant.

## Measured outcomes (through redact(), G8 tree) for the round 5 rows
x4242424242424242, card4242424242424242, 4242424242424242x: unchanged (readable); card_4242424242424242 -> card_<PHONE_1>, stored and
storable as PHONE (base: left readable, nothing stored: so entry 7 widens storage; AT8 pins it); beneficiary_, recipient_, customer-iban_, iban__ + DE89...:
unchanged; telephone4155550132, cellphone4155550132: unchanged.

## M1 exposure comparison (L-D15 stays at default)
Default closes rows 36, 37, 41, 42, 44 and leaves 87-96 as limits (full IBAN readable in file/path/dashed shapes, deterministic); fallback (b) closes
88, 90-92 (+ round 5's 93, 94 style shapes per v6 6.1) but loses 41, 42 and splits K84 (14 vs 9 readable per 80,000 base64url tokens in v5's figures;
v6 6.1 re-measured 17 vs 9). Default optimises for equality with the base inside tokens, not fewest IBAN leaks. Lead decides.

## Deviations
- SECURITY.md / CHANGELOG.md (phase 5): not edited; ticket says wording goes through the security wording review and v6 splits the bullet (section 13). Left to the SECURITY lane.
- evidence/G8-1.md (raw phase output) not written; this file replaces it. Round 5 readiness N1-N4 are ticket-text fixes, already in v6; no code comment needed changing.
- G9 not merged: tripwire took the no-G9 branch (green).
