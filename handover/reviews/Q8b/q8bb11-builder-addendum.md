# Q8b b11 builder addendum (builder claim, unverified until the independent evidence lands)

Head 2153ad85. Builder says the full pytest passed (10661 passed, 457 skipped, exit 0, log /home/user/build/b11-notes/full-pytest.log). Builder says the full tests/q8b_mutants.py table showed 17 BAD rows out of 227 read (reached M227, no summary line):
- SURVIVED: M159, M163, M190
- WRONG_REASON: M192, M198, M199, M200, M215, M216
- OTHER_TEST: M193, M196, M197, M203, M223, M224, M225
- CRASH: M226 (killer raises InputTooLarge)
Not run: stage_mutants, mutation_runner_mutants as user nobody, ticket acceptance commands, groups 6 and 9, fail-before re-record for groups 1, 3, 4, 5, notes corrections.
This agrees with codebase review r12 findings C2 (M190) and C3 (M192, M193, M196-M200, M203).
