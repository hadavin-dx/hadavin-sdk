# Q8c-1 batch 17 fix, builder notes (one survivor of the full policy mutant run)

Base: 7010aa44. Survivor: `B15 notes check does not reach every module for an unreadable run-time import name` (466 of 467 good, log `policy.log` of that run).

## Diagnosis (first)

- The mutant was equivalent, not a missing test. It replaced the `else` of the prefix loop in `tools/notes_lines_check.py` (the branch for an empty text, listing every Python file under `tests/`) by `set()`. Every place that adds an empty text to `dynamic_prefixes` (a call with no name, a name that starts with a value, a relative name, a loader handed on as a value) also calls `unresolved_edge`, and one reason lists every test whenever a file under `tests/` changes (batch 17). So the branch repeated that rule and no test can tell the two apart: the killer test still passed with the mutation applied.
- Fix: the branch was removed (with a comment saying why) and the mutant was removed from `tests/policy_mutants.py` (a comment there states the reason). The rule itself is still pinned by the `unresolved_edge` mutants and by the assert `an unreadable name: a changed module listed` of the killer test.
- Side effect found by the first re-run (465 of 466): the sibling mutant `B15 notes check does not follow the text a run-time import name starts with` (`if prefix:` to `if False:`) had been killed only through the removed branch, and its first failing line no longer carried its expect text (WRONG_REASON). Its expect text is now `a changed module listed`, the text of the first assert that fails.

## Rows

| file | unit | status | reason |
|---|---|---|---|
| tests/policy_mutants.py | `B15 notes check does not reach every module for an unreadable run-time import name` | removed | equivalent mutant (see above); removed with a written reason in the file |
| tests/policy_mutants.py | `B15 notes check does not follow the text a run-time import name starts with` | changed | expect text re-pointed to `a changed module listed`; killer `test_a_module_imported_by_a_name_built_at_run_time_lists_every_test_that_could_reach_it` |
