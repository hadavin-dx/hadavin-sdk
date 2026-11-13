# Lane 3 fix 7 (B7): tests for the Q8b survivors

Base f3c39cf89ec989f032ea48a23cfd824b88da9c68. Only one new file: tests/test_identity_claims_lane3.py (16 test cases, no product code changed). Patch: lane3-fix-7.patch (the new file only).

## What is not fully shown
- C03 and C19 are reached by calling the desk's own private steps (`_decide_once`, `_claim`, `_take_token`) by hand. They are not reached through a real two-thread race. The first guard is hidden behind the earlier check in `_process`, so no one-request test can reach it. The calls are what the second request in a race would do.
- C18 is left alone: equivalent (the claim only takes `pending` rows, so the `failed` branch of the CASE never runs). It stays "alive" and that is correct.
- Not checked: the full mutant list (only these 8 were re-run); no property/fuzz run.

## Per mutant (copy of the tree at /home/user/work/b7-mut, restored after each run; runner priv/b7-run.py reuses the Q8b mutant list)
| id | result | killed by (first failing) |
|---|---|---|
| I03 casefold | KILLED (3 tests fail) | test_key_is_lower_not_casefold, test_sharp_s_and_ss_are_two_leads |
| I04 NFKC | KILLED (3 tests fail) | test_key_is_not_unicode_normalised, test_compat_forms_are_two_leads |
| I06 email `<` | KILLED (1) | test_email_limit_is_254_inclusive |
| I11 field `>=` | KILLED (8) | test_field_limit_is_inclusive[name..message] |
| I12 len(v) | KILLED (4) | test_padded_value_is_measured_trimmed[...] |
| C03 write-once guard | KILLED (1) | test_second_decider_leaves_verdict (see above: direct call) |
| C18 | ALIVE, equivalent | none possible |
| C19 token lead id | KILLED (1) | test_token_of_other_lead_is_not_used (direct call; the earlier "weak gap" guess was too pessimistic) |

I03/I04 note: sharp s and long s differ under lower() but merge under casefold(); dotless i differs from i under both. Full-width a and the fi ligature stay separate keys although NFKC would merge them.

## Evidence
- New tests on unmutated tree: `pytest tests/test_identity_claims_lane3.py` rc=0, 16 passed.
- Mutant log: raw copy of runner output in raw/b7-mutants.log.
- Line length > 120: 0 lines. Hygiene test (after `git add -A`, nothing committed) with the new file: rc=0, 36 passed, 4 skipped.
- Full suite: see the last section.
