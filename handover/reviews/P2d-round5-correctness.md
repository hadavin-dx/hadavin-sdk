# P2d round 5, correctness review (ticket revision 5, 341 lines)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority).
Reviewer: `egm:egm-codebase-details`, read-only, nothing run, did not open `reviews/`. Rerun of a lost run. Round 1 of at most 3 under order 16. Cites checked against snapshot 748849c and the on-disk tree.

Verdict: NOT CLEAN. 0 Blocker, 4 Major, 7 Nit. Code citations accurate; Majors are drift against later orders/P1 revisions plus one mutant table error.

## MAJOR

- **M1. Stale against orders 11 and 13.** Order 11 (owner order) says the look-alike hole L19 is CLOSED in v1; the ticket still says "deliberately left open" per order 9 at lines 78 (8)(iii), 101 CHANGELOG, 174 VARIANT-1(c), 257 Done, 262-269 P2d-2 header, 289 bug class H, 304 v1.1 row V11, 332 L19, 336 D9. P2d-2 has no `check_lookalike`, `LookalikeCopy`, new public name or refusal ("no new refusal", line 268) and no P2d-2b. Order 13(1) (NAME/ADDRESS evidence rule) missing. Per the design (section 8) rev 6 must carry: the P2d-2 `check_lookalike` scope with `LookalikeCopy` in runmap.py and call sites; the P2d-2b `error_reason` PR with rows and mutants; order 13(1) wording; VARIANT-1(a),(c) asserting refusal; supersession of V15 (line 308); replacement of (8)(iii) and the CHANGELOG sentence; LK-PART, the partial-copy sentence, and the self-refusal cost.
- **M2. P1 dependency lines stale against P1 rev 15.** P1.md:22 says P2d-2 follows P1b (order 11); the ticket says it does NOT at lines 3, 30, 33, 34, 264, 266, 315, 334, 339. It cites P1 "rev 8" and "tier N limit 4 per text" at 22, 78, 170, 264, 274, 307, 335, 339; P1 now cuts both tiers (PL35) and `has_hidden_channel` keeps rules 1 and 2. Rows built on that limit (UNASS-1, HIDDEN-1, L22, V14, P1B-1) need rework. Merge list at line 33 conflicts with P1's order.
- **M3. Mutant/killer table for 18, 19, N1 wrong against the old mutant file.** Old 18 (lines 1937-1943) and 19 (1944-1951) sit on the slash condition (`_char_class` 928-931). The ticket (line 96) redefines 18 as "delete the `.replace("⁄","/")` in `_aligned_fold` line 1107", which is existing mutant 7's snippet (re-pointed by `_RETARGET` 1831-1834); edit (a) does not change that code, so old 18/19 still match unchanged and redefining 18 drops the old 18 from the "targets unchanged" list (line 202). Claimed killer ALIGN-1 cannot see line 1107 (it tests `_char_class`); D1-1 and test 30's first half would. Mutant 19 is "weakens the guard to `c == "/"`", not "deletes". Fix: keep old 18 and 19 (killer test 30), make the `.replace` mutant a new numbered one with killers D1-1 and test 30; recount 41/45.
- **M4. P2d-2's hook does not say whether it runs on ASCII-only text.** Line 268 calls `has_hidden_channel` once per `redact()` on the whole cleaned text with no ASCII exemption; guarantee (1) (line 77) says ASCII-only text takes only the ordinary patterns; `find` enters the fold scan only for non-ASCII (`redact.py` 977). Without a `not out.isascii()` gate, an ASCII text with control characters could be withheld and ASCII-1 and the 66 warden_port oracle could break. Add the statement and a row.

## NIT

1. V5 "stage 1 at 490 to 493" wrong: `redact(` call is 492-494, `views =` is 490.
2. Line 90 cites "P1 lint"; the item is "P1b: the caller rule and the refusal lint".
3. Line 182 SWEEP-1 label "A (line 1 stays on old code)" likely wrong (pattern value class may include ZWSP; UNVERIFIED).
4. Lines 248, 333 require evidence "BEFORE round 5"; order 16 says settle unknowns by running at build time. Line 70 "no round cap", line 256: add ticket review freezes after at most 3 rounds.
5. Header says "depends on P1 rev 8"; P1 is rev 15; update in one pass.
6. GAP-1 hole rows fine, but P1b is a dependency again (M2).
7. Line 96 "reviewer's line numbers 1937-1951 UNVERIFIED": the reviewer verified them; they are correct.

## Verified

redact.py/runmap.py/textnorm.py line cites (all read); BUDGET-2 counts; V27 adopt rule; 66 warden_port tests (64+2 perf); 16 producers; callers of bare `redact()` (runmap.py 447, 468); V24 callers; ban test at test_k5_round11.py:238; 32 moved tests (15+12+4+1); 10 edited tests; new rows 32+5+8 = 45, P2d-2 9, total 54; mutants old 21 (3+5+6+7) + 20 new = 41, P2d-2 4, total 45; SL-D mechanism; order 8(5) (no real-looking secrets); 19:40 UTC = 01:10 IST.

## Not checked

All git claims (numstat, merge-base, c1a branch); every trace of new rows/mutants and probe figures (614/677, 67/67, 437/614, timings); test 14 split; P1a merged behaviour; P1.md beyond greps; STUDIO-RULES, plan-v3, bible; PASSWORD pattern ZWSP; design file beyond sections 1, 8, 9.
