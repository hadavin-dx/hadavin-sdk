# E14 build notes (finder memory cap, run-level character cap)

Branch wip-e14 (base cloud/core-c 90227c0c5). Constants are the ticket's DEFAULTS, NOT approved by the lead: MAX_MAP_CHARS 524,288, MAX_FINDER_CHARS 786,432, refusal InputTooLarge("FinderMemoryTooMuch").

## Phases
- 0: tests/test_redact_finder_cap.py (T1-T12). Red on base: 10 non-perf failed (T1-T9, T12; T4-T7 for their reasons), perf T10 (accepted, 8 x 260,000) and T11 (missing constant) failed. Measurement scripts copied to handover/core-c/tickets/E14-files/.
- 1 defaults.py + config.py; 2 redact.py `_trie(limit)` and the `_build` call; 3 agent_loop.py `_map_chars` and both checks; 4 tests/e14_mutants.py.
- Green after: 10 non-perf passed, perf T10 4.4 s, T11 3.1 s (box loaded).
- Mutants: 8 of 8 KILLED, each with its `E14-Tn ` expect. (A first run showed CRASH/WRONG_REASON because pytest.fail is not an assertion; the test now raises AssertionError.)

## Existing tests run (TESTED)
- test_k5_round10 + test_runmap_enforce_map: 80 passed.
- test_k5_perf + test_redact_fold_budget + test_redact_idempotent_property (whole corpus, perf included): 1873 passed.
- test_redact_settle_loop + test_k5_round5: 177 passed (SpelledMemoryTooMuch pins unchanged, stop rule 9.3 not hit).
- ruff check/format --check on src tests tools clean; bandit -ll: no finding (only nosec warnings).

## NOT RUN
- The whole suite with `-n 2`: the box held 5-10 pytest processes throughout (stop rule 9.6). The batch above was run file by file, serially.
- Re-measure of sections 2.3/2.4 (m_seq, m_honest) on this tree: not run (load). Base has no G4/G9, so 9.4 is untested here. T12 asserts the k5 run's map is under MAX_MAP_CHARS // 30.
- Timing ratio 1.2x of the k5_perf `curl -u` test vs base (9.2): not measured (tests passed under load).

## Deviations
- The comment at SPELLED_MAX_CHARS ("bounded since E14 by MAX_FINDER_CHARS") was NOT appended: G4 and G9 both edit that block; left for the rebase.
- Constants' comment lines in defaults.py: ruff format wraps a trailing comment on a short assignment badly, so the notes sit on the line above each constant.
- T6 asserts NO_ACTION for the state only (reason code is whatever the run gives).
- `_build`'s MEMORY comment is in `_build`; `sweep`'s comment block was not edited (keeping redact.py edits minimal).
- E14-files copied in the notes commit (code commits touch only src/tests/tools).

## Not bounded (ticket section 11)
The `find` passes before the build; a refused build still costs up to the cap in nodes; run cap counts values only; retained compiled finders are not counted.
