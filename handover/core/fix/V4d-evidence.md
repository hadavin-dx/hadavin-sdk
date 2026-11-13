# V4d EVIDENCE (raw output only; no judging). Subject: copy tree-V4d of tree-F4c (HEAD e1bc257 + F4d changes). Date 2026-11-13.
lead_desk.__file__ = /home/user/build/rr6/tree-V4d/src/lead_desk/__init__.py (checked). Python venv-br, ruff 0.17.4.

## Failed / uncertain first
- 3 of 9 mutations SURVIVED (the docs test did not notice them):
  - M6 docs/settings.md "set it to `1`" -> "`0`" (rc 0). The test checks the two workflow files, not that sentence.
  - M7 docs/settings.md: deleted ", with or without the `(H:MM:SS)` time that a run of a minute or more adds" (rc 0).
  - M8 docs/settings.md: deleted " (even `0`, as for `DPLD_REQUIRE_SCAN`)" (rc 0).
- Numbers differ from builder claim: 20-file run measured 1566 passed, 30 skipped (builder: 1563 passed, 33 skipped). Same total 1596. Builder's readers-final.log has no skip list (no -rs), so which 3 tests differ is not known. Mine skip: 24 gitleaks_exceptions + 4 hygiene (no gitleaks) + 1 root + 1 ntpath (Python 3.13).
- Not run: gitleaks, playwright browser tests (not installed), CI, other OS. A first attempt to read handover/ from the wrong folder failed (cwd mistake, no effect).

## (1) tests/test_docs_match_tools.py, DPLD_REQUIRE_COUNT=1, 3 runs (docs-3x.log)
16 passed in 6.00s / 16 passed in 6.87s / 16 passed in 5.47s; rc=0 each.

## (2) 20-file set (out/V4b/doc-readers.txt, includes test_hygiene.py) once, DPLD_REQUIRE_COUNT=1 (readers20.log)
1566 passed, 30 skipped in 303.56s (0:05:03), rc=0.

## (3) ruff (repo pyproject, line-length 120) whole tree (ruff.log)
`ruff check .`: All checks passed! rc=0. `ruff format --check .`: 167 files already formatted, rc=0.

## (4) Failing-before (failing-before.log): copy tree-V4d-old = tree-F4c at HEAD, `git stash` (0 changes left), new test file copied in (cmp-identical to the F4d one), DPLD_REQUIRE_COUNT=1
5 failed, 11 passed in 6.03s, rc=1. Failed:
- test_the_q_form_prints_one_line_per_test_and_a_total_as_its_last_line
- test_the_settings_page_says_what_the_require_count_switch_really_does
- test_the_page_states_the_number_of_tests_and_files_that_the_collector_counts
- test_the_probe_checks_the_token_variable_name_only_when_calls_are_confirmed
- test_every_page_about_a_repeated_request_says_it_can_start_a_follow_up_that_is_due

## (5) Mutations on docs in copy tree-V4d-mut, one at a time, restore + cmp (mutations.log, script mut.py), DPLD_REQUIRE_COUNT=1
| id | change | result | restore cmp |
|---|---|---|---|
| M1 | README.md "also waits 5 seconds" -> "3 seconds" | KILLED (rc 1) | identical |
| M2 | contract.md:303 5 seconds -> 3 seconds | KILLED | identical |
| M3 | docs/tests.md "(H:MM:SS)" -> "(H:MM)" | KILLED | identical |
| M4 | hubspot page: removed "when you give `--yes-spend-calls 7`" | KILLED | identical |
| M5 | docs/tests.md 3998 -> 3997 | KILLED | identical |
| M6 | settings.md "set it to `1`" -> "`0`" | SURVIVED | identical |
| M7 | settings.md: removed "with or without the (H:MM:SS) time" | SURVIVED | identical |
| M8 | settings.md: removed "(even `0`, ...)" | SURVIVED | identical |
| M9 | docs/tests.md "exit with code 2" -> "code 1" | KILLED | identical |
6 killed, 3 survived. (The pytest-count regex itself is in the test file, not the docs; the docs-side wording of the regex rule is M3 killed / M7 survived.)

## (6) Builder claim vs measured
- 3998 collected in 97 files: measured `3998 tests collected in 3.39s`; `-qq` file lines = 97. Match.
- 1563 passed 33 skipped: measured 1566 passed 30 skipped (differs, see above).
- 5 failed / 11 passed before: measured 5 failed / 11 passed. Match.
- Docs test: builder 16 passed (before hygiene fix) / measured 16 passed x3.

## Housekeeping
tree-F4c unchanged (6 modified files, same as before; I did not edit it). Copies: tree-V4d, tree-V4d-old, tree-V4d-mut, tmp-V4d. None of my processes is left running; pgrep still shows pytest runs on tree-V6 (another agent, not mine, not touched). No spend, no network, no prompts answered.
