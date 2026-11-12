# q8c1b16-codebase-r16: Q8c-1 batch 16, code head 43be04de, round 16, persona codebase details

Source: hand-back of the codebase reviewer (agent a0df7c6b), saved by the lead (condensed). SECURITY path. Read only; no run. Snapshot `/home/user/build/snap/q8c1b16-43be04de`. 0 Blocker, 0 Major, 8 Minor, 4 Nit. (The design reviewer of the same round found 4 Major: see q8c1b16-design-r16.md.)

## Checked fine
All 25 B16 notes-check mutants and 3 runner mutants present, each search text occurs once, each has a killer with matching expect text; all three runner blocks fail on the old runner; EXPECTED_MUTANTS 65 consistent; printed-figure regexes match RENEWAL_STEPS text; 375 policy mutants counted; limit strings present; no leaked secrets.

## Minor
1. tests/test_policy_renewal_copy.py:125-150 `_printed_row_count` and the printed-figure pin: no negative test, no mutant; names and kinds figures checked only in `_renew_and_check` (not a normal run); `asked == 0` passes for "about 1 row" (tolerance 5).
2. CHANGELOG.md:217 quotes the overdue message as one sentence; actual text is in policy_page.py:848-850 and KINDS_RENEWAL_STEPS (35 is another message). Drop quotes or quote each.
3. CHANGELOG.md:216 claims walrus in "a base class"; no test case. Untested and unmutated: `kw_defaults`, parameter annotations, `returns` (notes_lines_check.py:243-245); `lf` short form (356); keyword args of getfixturevalue/usefixtures (586); `no:` branch of `-p` (696); `name=` of `__import__`; `*named` in `dynamic_names` (457).
4. tools/mutation_runner.py:537 (+ docstring :394, CHANGELOG :218): a link in `extra_files` to a file outside the tree is refused (`_inside` raises), not "left out"; untested. Put `_through_a_link` first or say so.
5. mutation_runner.py:138-146 `_through_a_link` uses `is_symlink()`: false for a Windows junction; `_refuse_junctions` not applied to the folder part of an extra_files path.
6. notes_lines_check.py:798-802 DYNAMIC_FIXTURE expansion reads `scope.nodes`: an imported fixture (`from tests.fx import fx_a`) or one from a `pytest_plugins` module is not reached.
7. notes_lines_check.py:416-424 `plugin_names` reads Assign and AnnAssign only: `pytest_plugins += [...]` and `.append(...)` not followed; `pytest.toml` and `.pytest.ini` not read nor stated.
8. notes_lines_check.py:526-542 `_starts_with_package_name`: `chain[0] in imports` accepts a function or constant (`make.__name__ + ...`), and `f"{pkg.__name__}_x"` (sibling) is exempt; narrow to package/module imports and require a ".".

## Nit
9 test_notes_lines_check.py:1226 comment describes the removed exemption. 10 CHANGELOG:216 "two batch 14 and 15 mutants re-pointed": three rows changed. 11 notes_lines_check.py:74-83 docstring lines 170-230 chars. 12 CHANGELOG k1b "pass on old code too" not checkable without cli.py.

## Not checked
sha of mutation_runner.py (733a19c8...); no test run; cli.py not in snapshot; lint config; whether 36/1/35 figures still hold after wider reach.
