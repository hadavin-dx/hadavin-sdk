# B-Q8b-b14 PR notes (builder), redaction path, round 15

## Tests that PASS on the old head 120f3f78 (each with its reason)
- test_b14_1_the_generator_covers_the_key_and_non_key_characters (meta test of the generator, not product code; fail-before output: 1 passed on old code). Its job is to stop the generator from shrinking.
- test_b14_3_the_rare_breaks_are_every_break_that_str_splitlines_knows_besides_the_line_feed_and_the_carriage_return and the three new cases of test_b13_7 (file, group, record separator): the card path was already right on 120f3f78 (it writes all eight breaks as a line feed). They close a PROOF gap (no mutant named the three separators), proven by mutants M268 to M271 (each drops one or more breaks from the card path and is killed for the named reason).
- test_b14_5_a_header_whose_first_word_holds_authorization_masks_its_folded_lines[*] (N4): the shape in the review (`Authorization: x-authorization:v` then an indented line) is MASKED on 120f3f78 and on the b12 head: the inner `authorization:` starts its own match. Not reproducible as written; 8 shapes probed (x-authorization, xauthorization, x_authorization, `=`, no value, no space, X- prefix, doubled): 0 readable on old and new. No code change was made, so no mutant exists that this test kills (a mutant `_FIRST_WORD = (?!authorization)\S` leaves all 8 shapes masked, measured). The test stays as a control of the class.
- The wall-clock tests (b13_3 nine units, b8_8, b8_10, b9_1, b9_4, b9_5, b10_1, b10_2, b7_6, r1) pass on the old code by design (they time a rule that is linear on the head); their proof is the planted fault of the mutant table (M258 to M267, M272 to M279).

## Fail-before on 120f3f78 (clean tree, only the new tests copied in)
- G1: /home/user/build/b14-notes/failbefore-g1.txt: 16 failed, 1 passed (the meta test); the generator test reports 1950 of 20850 cells readable on old.
- G2: /home/user/build/b14-notes/failbefore-g2.txt: the new gate test_b13_4_every_wall_clock_test_and_every_case... FAILS on the old table with 17 wall-clock cases without a planted fault; test_no_control_is_without_a_planted_fault FAILS with 3 controls without a planted fault.
- G5 LIMITS test: fails on old (LIMITS lacks the sentences).

## Behaviour change against 120f3f78
`-bypass=v` and `--bypass=v` (a word with a key character in front, equal sign) are masked again, as on main. The bare word and `--bypass v` (flag with a space) stay shown (owner item q-q8b-bare-bypass, NOT built).

## Gate results (builder, NOT independent) 
- gitleaks (origin/main..HEAD, at 1bce8ea5): rc 0. ruff check rc 0, ruff format --check rc 0, scan_repo rc 0 (1bce8ea5 and later test-only commits re-checked ruff), bandit -ll -r src rc 0.
- stage_mutants (at 1bce8ea5): 37 of 37 good, rc 0.
- mutation_runner_mutants as nobody (head 50e0f083+): 64 of 64 good, rc 0.
- q8b_mutants as root (snapshot of 50e0f083, BEFORE the last 4 commits): 258 of 277 good, 19 BAD, rc 1. Details: gate/q8bmut-root.txt in /home/user/build/b14-notes/. Fixed afterwards without a re-run: M252, M254, M271, M280 (killer named the wrong case: OTHER_TEST), M256/M257 (my output-keeping plant did not slow the rule: survived; restored the b13 plants). STILL BAD, not fixed: M259, M265 (WRONG_REASON), M262, M263, M267 (survived), M272, M273, M274, M276, M277, M278, M279 (survived), M275 (OTHER_TEST).
- full pytest: NOT RUN (stayed in the heavy queue for 49 minutes).
