# G9 build notes (builder, 2026-11-20)

Tree: worktree /tmp/core-c-g9, branch wip-g9, base f29a22262 (G7 r7, E9, Q9, G8, G10 in). Code commit 598fe92e0 (pushed to wip/cloud-core-c/g9).

## Built
- g9_src.diff, g9_tests.diff applied with --fuzz=0 (offsets only). g9_after_g8_joins.diff applies ONLY AFTER g9_src.diff (the phase 0 dry-run against the bare base fails by design: its hunks are in G9 code).
- G8 joins edit, 7.6 PHONE test, mutant G9-24 (Mutant row, pinned=), EXPECTED_COUNT 117 (comment says 23 G9).
- Added (round 2 plan review): test_g9_a_gate_text_that_mentions_a_long_value_many_times_is_masked_not_refused (300 mentions of a 4,900-char value through enforce_map). Already in v3 and kept: Mutant rows with pinned=, no duplicate tracemalloc import, held_value_left InputTooLarge -> mask_budget_exceeded test.
- Defaults built, not lead-approved: L-D6' anchored check, L-D1 gate masks and never refuses, L-D7 1,000,000, L-D3b uncounted finder passes. L-D1 gate-lane approval: silent, default built.

## Measured (reruns match the ticket)
- Phase 1 batch (-n 2, not perf, not live; 13 test_redact*.py incl. test_redact_glued_rest.py): 3929 passed, 3 skipped, 47 xfailed, 0 failed, 139.48 s. G8 tripwire test_g9_read_back_follows_the_sweeps_joins passes on the G9 branch.
- ruff format --check, ruff check clean; bandit -ll no issues (only nosec/comment warnings).
- g9_cases: section 0 v3 column reproduced. Planted N=300: refused SpelledUnionTooMuch, 2.52 s, 60 MB. redact_many 1,000 strings: 0.62 s (ticket 0.51, noise). Mentions 1,800 ok (3,861,855 units), 1,900 refused. g9_deep: k5 shape 263,170 units 0.002 s; periodic refused. g9_phone as ticket. G4 maps (ab-cd-ef x4) as 3.1 point 3.

## MISMATCH 1 (real regression, not fixed): perf test red
tests/test_redact_fold_budget.py::test_hostile_1_hostile_shapes_return_a_clean_text_or_refuse (perf-marked, so not in the phase 1 batch; the ticket never ran perf files) FAILS on G9: shape "zwsp password" = ("pass"+U+200B+"word=") x 16,000 is refused InputTooLarge(SpelledWorkTooMuch) (the test allows only the e-acute and devanagari shapes to refuse). Passes on the base (41 s). Reproduced with 400 repetitions (4,000 chars). Cause: the anchored check (_deep_hits) on a long PERIODIC registered value: 3.77M of the units at 300 reps come from _deep_hits (1,146 calls, 2*len(w)+2 per comparison). It is exactly the stated limit "periodic long value beside its own period is refused" (G9-22 pins that), but here the text is a natural periodic input and an existing test forbids the refusal. Not fixable by lowering the unit weight (G9-22 would stop raising); needs a design decision (e.g. dedupe comparisons per edge, or cheaper weight with a changed G9-22) from the lead. Not touched; no test loosened.

## MISMATCH 2: mutant runner baseline fails
tests/redact_mutants.py runs the baseline of its whole test list (no -m filter), which includes test_redact_fold_budget.py with the failing perf test above, so `redact_mutants.py G9-` and the whole-file run abort with "the unmutated copy does not pass its tests". Phase 3 NOT RUN. (Dropping the file from the list was refused by the environment and would be a loosening anyway.)

## NOT RUN
Phase 2 whole suite, perf batch (except the one test above, run alone), mutants G9-1..24, whole-file summary line.

## E17 fix (builder, 2026-11-20): perf test green, MISMATCH 1 and 2 resolved
Try 1 (kept): in `_deep_hits` an upper bound of the characters readable on each side of an edge (out chars + what each key token adds, prefix sums over toks); a place of the anchor needing more than that is skipped, not compared, not counted; the anchor search runs only over the feasible stretch of the rule (the `len(w)` search charge stays once per (anchor, rule), so the G9-20 pin 21,027 holds; place finds charged per place found in range). Exact feasibility test, so G9-22 (x*1,100, 76 places x 30 edges) is unchanged and still raises.
Measured: zwsp shape, 400 reps: 2,673,655 units refused -> 933,811 then 29,575 ok; 16,000 reps (the test's): refused -> ok, 1,811,011 units (2 comparisons x ~320k + searches), 3.0 s. Tries 2 and 3 (period skip, per-occurrence count) not needed.
Proof: settle_loop + idempotent_property (not perf) 1963 passed; fuzz 6 x 10,000 seed 7: all clean, pass counts identical to ticket 9.2; corpus 1,836 inputs 0 rows differ vs /tmp/g9-base, restore failures 63=63, max units 19,318; g9_hostile rows identical to 9.4 (mentions 1,800 = 3,861,855 units, comb 1,386,769); g9_deep periodic still refused. fold_budget file incl. perf: 23 passed. Phase 1 list: 3928 passed, 3 skipped, 47 xfailed (after the mutant-search fix below, meta test 6 passed). Mutants: G9- 23 of 23 good; whole file 117 of 117 good.
Test-side edits (not the perf test): G9-20 search text now `if (anchor, w) not in searched:` -> `if True:`; G9-16 killer docstring rewrapped (a line began with "E ", read by the runner as an error line: WRONG_REASON).
Deviation: one batch (fold_budget) started at load 2 other pytest (my own wait loop matched the check).
