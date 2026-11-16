# B-PRH-b5 PR notes (batch 5 of PR H, base head d08ec151)

## Files outside the ticket's allowed list (Issue 7): why each is needed
- `src/hadavin_sdk/defaults.py`: holds `MAX_REDACT_PASSES` (the counted pass bound the ticket's step 6 needs, one place for the number, no hardcoding) and its comment, now reworded to say what the tests assert. Needed.
- `tests/fixtures/prh_accidental_pairs.json`: the 92 accidental pairs (cases where a hidden item sits between two ordinary characters) that the "nothing ordinary is changed" gate reads. Needed by the existing gate tests.
- `tests/fixtures/prh_main_passes.json`: the pass counts that origin/main made on the same texts, read by the G1/G2 gates that compare head with main. Needed.
- `tests/test_k5_fixes3.py`: the test patches `tools._decoded_readings`; the helper was renamed in this PR, so the test follows the rename. Needed.
- Proposal: add these four to the ticket's allowed list (lead decides).

## Suppressions (Issue 7)
`tests/test_prh_perf.py`: the two added suppressions are gone. `pytest = None` has no type comment; the timing child is started with `asyncio.create_subprocess_exec` (fixed argument list, no shell), so no `noqa` is needed. `git diff origin/main | grep '^+' | grep -E 'noqa|type: ignore|nosec'` prints nothing (rc of grep 1; see raw gate log).

## New tests that pass on the old code (Issue 8), fail-before run
Raw: evidence-raw/PRHb5/failbefore.log (new tests and fixture on d08ec151 src: 32 failed, 2126 passed). 38 test ids are new; 31 fail on the old code. The 7 that pass, with the reason:
- `test_tail_row_trail_is_masked`, `test_tail_row_on_the_next_line_is_masked`, `test_tail_row_long_tail_is_masked`: these rows pass on d08ec151 (the code was right); they pin the consuming reading. Killers: mutants 44b, 44c, 44d (consuming reading removed), killed each by its own test.
- `test_undo_entity_cut_by_a_control_reference_is_whole`: the old code was right; killer mutant 21b (the strip between control references and entity decoder removed).
- `test_pass_bound_holds_for_a_seeded_search`: bound test; killer mutant 67 (bound 8).
- `test_every_regression_row_needs_at_most_seven_passes`: bound test; killer mutant 68 (bound 6).
- `test_a_refusal_is_not_masked_unless_the_row_says_so`: tests the harness (`verdict`), not src; control reason: it fails if the harness again reads a refusal as masked.
The three ids named earlier as passing on the previous head (already in d08ec151): `test_named_ids_exist_and_the_converse_holds` and `test_pinned_secret_rows_count` are self-checks of the fixture file (they fail when a named row is missing or the pinned count changes; control, not a src test); `test_regression_row[b4_ctl_colour]` is a control row (a coloured key that is not cut stays masked before and after).
Honest note: mutant "end-of-round strip alone" in `undo` survives (the next round's entity-branch strip removes the same item, only a round later), so it is an equivalent change; mutant 21 now removes both strip points again (as before), 21b removes the entity-branch one.

## Class check (Issue 1)
Class: a reading with the hidden items deleted (no glue space) handed on as the result. Sites searched: every `return` of a joined reading in `tools.py`, `guard/runmap.py`, `guard/redact.py`. Found and fixed: `tools._scrub` (`return alt`), `redact.redact` (three `return found`, now `(details withheld)`). `runmap` character/consuming views probed with `B-PRH-b5-scratch/probe_red.py`: they behave as main on the ESC-A row. Design caveat: when the character reading is the only reading that holds a secret and the text has a control sequence body, the scrub shows the marker plus the truncation note (fail closed) instead of a masked text.

## Pass counts (Issue 3)
17 passes is a one-time measurement outside the repository. Tests assert: seeded search of 600 texts peaks at 13 or less (>= 11), every regression row needs at most 7 (max exactly 7), bound 24.
