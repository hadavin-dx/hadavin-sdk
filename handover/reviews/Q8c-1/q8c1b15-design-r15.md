# q8c1b15-design-r15: Q8c-1 batch 15, head ccb63021 (code = 3ad1cc45), round 15, persona design

Source: hand-back of the design reviewer (agent a0384ce0f23f1ea08), saved by the lead (condensed). SECURITY path (no round cap). Static read only; no independent evidence existed when read. 0 Blocker, 1 Major (N1), 4 Minor (N2-N5), Nits N6. Snapshot `/home/user/build/snap/q8c1b15-ccb63021`. Verdict: groups 1, 2, 4, 5 and the evidence group fixed; group 3 partly fixed.

## Major
- **N1** An unreadable run-time import name (`import_module(name)`, f-string, `.format`, `.join`) lists nothing in most real files (tools/notes_lines_check.py:488-492, DELTA.patch 2248-2252): the "every Python file under tests" reach applies only if the file imports nothing from `tests` (`elif not any(stem ...)`; `_imports` returns only tests-stem imports). A file with `from tests.helpers import make` plus `import_module(name)` is exempt; changing `tests/zz/dyn_c.py` lists no test and the blocking CI step exits 0. Same class as r13 group 1 and r14 rt3. The tool's own rule says an unreadable name lists every test of the file. The test fixture dodges it with `from tests import yy`. Fix: reach every Python file under `tests` regardless of imports, or refuse; test plus mutant.

## Minor
- **N2** Sibling fixture-by-text links not followed or stated: `parametrize(..., indirect=True)`, `@pytest.fixture(name="alias")`, `getfixturevalue(var)` with a non-literal argument, entry-point or `PYTEST_ADDOPTS` plugin (`FIXTURE_BY_TEXT`, `_used`). Follow them, or state them as limits in CHANGELOG and docstring and pin with a test.
- **N3** Figures "36 rows / 35 rows / 1" in tools/policy_page.py:846-849 and :873-874 and the CHANGELOG are not pinned: the plant asserts only `asked > 0`. Dated 2026-11-12; first real renewal 2026-12-12. Reword to "about", or assert the plant count against the printed number within a tolerance.
- **N4** Builder evidence is not at the final code head: stage and policy mutants at d6f396f1, mutants-b15.log at 49c874e5, notes-check and gitleaks at 1d62c19d, lint and static at fd85c0bf, full pytest and plants at 3ad1cc45. Code between d6f396f1 and 3ad1cc45 not checked. The independent runner reruns stage and policy mutants (including `--day 2026-12-12`) at ccb63021.
- **N5** src/hadavin_sdk/sources/kubernetes.py:6-9 states "the Kubernetes API accepts it as a `create` of a review object that is not kept" as fact; POLICY (:455-471, :497-509) says not found in a vendor source and lists it under claims_unverified. Use the POLICY wording.

## Nits (N6)
`_renew_and_check` (tests/test_policy_changelog.py) docstring is a dead expression after an import; redundant `expected -= {"CHANGELOG.md"}` (tests/test_policy_renewal_copy.py:1832-1834); `extra_files` in the per-mutant copy makes no parent folder for a nested path (tools/mutation_runner.py, harmless today).

## Checked and found fine
Empty-prefix refusal order in `_fetch` (name, prefix, sign-in); `build()` with `model_construct`; Vault Transit signer untouched; no new grant; star-import closure; walrus Assign and AnnAssign; `-p` parser forms; `pytest_plugins` text added to each test unit; SHAPES line pins; fail-before 13 failed, 4 passed with stated reasons.

## Not checked
No code run, no mutant bodies read one by one, unchanged parts of notes_lines_check.py, signer_vault.py, CI on GitHub, Vault server tests, Windows or symlink behaviour of `extra_files`.
