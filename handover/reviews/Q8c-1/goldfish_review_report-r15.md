Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8c-1 batch 15, branch `wip/cloud-q8c1-b15`, head `ccb63021` (code `3ad1cc45`, delta against `a50d5b2e`), round 15 (SECURITY path: policy page, notes check, grant data; no round cap).
**Inputs:** `q8c1b15-design-r15.md` (0 Blocker, 1 Major N1, 4 Minor N2-N5, Nits), `q8c1b15-codebase-r15.md` (0 Blocker, 1 Major N1, 5 Minor N2-N6, Nits N7), previous report `goldfish_review_report-r14.md`, independent evidence `handover/evidence/Q8c-1/ccb63021/RESULTS.md`.
**Mode:** automated, recommended option for every item. No reviewer severity changed. Nothing contested, nothing escalated. No Blocker. One Major group stays open (group 1).

## Evidence summary (recorded by the runner, not judged)
- Full suite 11000 passed, 13 skipped (12 need a real Vault server: IMPOSSIBLE-NOW here, CI sets it; 1 Stubber), exit 0. stage_mutants 37 of 37. policy_mutants 350 of 350 at the real clock only. ruff, format, bandit, scan_repo, policy_page --check, gitleaks, notes check all exit 0. Fail-before on `a50d5b2e`: 41 failed, 574 passed; 13 of the 17 added test functions fail on old code. Four notes-check probes (walrus, usefixtures, star import, run-time import name with the name held in a variable) each exit 1 as plants and 0 as controls: the old rt3 case is closed only for a file that imports nothing from `tests` (group 1).
- Deviations: policy_mutants `--day 2026-12-11/12/13` and the B15 set were not run by the runner (group 7); `getfixturevalue`, `pytest_plugins`, `-p` in `addopts`, unittest `setUp` were not probed by the runner.
- Judgement of the 4 added tests that pass on old code (`tests/test_policy_renewal_copy.py`: full-renewal, kinds-alone, names-and-claims-alone, notes-check-of-a-renewed-copy): accepted. They check the renewal copy and the printed steps, not new product code; r14 group 2 asked that each plant be able to fail, and the ten B15 mutants (all killed in the 350 of 350) are what shows they can. No action.

## Prioritized Findings & AI Suggestions (all PROPOSE FIX)

### [Group 1] [design N1; codebase N1] - Major
Scope: `tools/notes_lines_check.py:488-492` (`_dynamic_files`), `:353-359`, docstring `:70-73`; test `test_a_module_imported_by_a_name_built_at_run_time_lists_every_test_that_could_reach_it`.
Gap (class: the notes check follows only some links between a changed unit and the tests that use it; same class as r13 group 1 and r14 group 3, run-time import branch): the docstring and CHANGELOG say an unreadable import name lists every test of the file; the code does so only when the file imports no package of `tests` (`:491`). A file with `from tests.helpers import make` plus `import_module(name)` (or `MODS[i]`, `.format(...)`) reaches only the imported folders, so changing a module it loads lists no test and the blocking CI step exits 0 (`tests/zz/dyn_c.py`; reviewer rt3). The fixture dodges it with `from tests import yy`. The prefix is read only from `n.args[0]`: `import_module(name=f"tests.x.{n}")` records no prefix. Also: `tests/zz/__init__.py` is not matched by the dotted-prefix rule (`tests.zz` against `tests.zz.`); an alias call (`imp = importlib.import_module`) is not seen (codebase N5).
Fix: apply the fallback (every Python file under `tests`) to every unreadable name regardless of other imports; read the keyword `name=` as well as `args[0]`; match the package `__init__` for a dotted prefix; treat a call through an alias of `import_module` or `__import__` as the same call (or refuse the alias with a plain message); tests for the mixed case, the keyword case, the `__init__` case and the alias case, each shown failing on `ccb63021`, one mutant per rule; correct the docstring and CHANGELOG so they state the rule the code keeps.

### [Group 2] [design N2; codebase N5] - Minor
Scope: `tools/notes_lines_check.py:282` (`getfuncargvalue`), `:308`, `:314` (walrus in a default argument or module-level decorator), `FIXTURE_BY_TEXT`, `_used`.
Gap (same class as group 1: links the check does not follow, neither followed nor stated): `parametrize(..., indirect=True)`, `@pytest.fixture(name="alias")`, `getfixturevalue(var)` with a non-literal argument, `lazy_fixture("x")`, run-time fixture names (`getfixturevalue(f"fx_{n}")`, entry-point plugins, `PYTEST_ADDOPTS`.
Fix: follow each one the code can follow (the `name=` alias and `indirect=True` are plain text reads); for the rest (non-literal fixture names, entry-point plugins, `PYTEST_ADDOPTS`) either list every test of the file as in group 1 or state the limit in the docstring AND the CHANGELOG with one pinning test each.

### [Group 3] [design N3; codebase N3] - Minor
Scope: `tools/policy_page.py:846-849`, `:873-874`; CHANGELOG.md:325; `tests/test_policy_renewal_copy.py:164`.
Gap: the printed renewal figures ("36 rows", "35 rows", "1") are not pinned; the plant asserts only `asked > 0`. First real renewal is 2026-12-12.
Fix: assert the plant's count against the printed number within a stated tolerance, or reword the page and CHANGELOG to "about N" and say how the number was measured and on what day.

### [Group 4] [codebase N4] - Minor
Scope: `tools/notes_lines_check.py` `getfuncargvalue` (:282), `_literal_start` `%` branch, `__import__` prefix (:356), the `-pNAME` attached form, `pytest.ini`/`tox.ini`/`setup.cfg` in `_config_plugins` (:511-521), `pytest_plugins` as an annotated assignment, relative or chained star imports, walrus inside AugAssign.
Gap (class: a code branch with no test that can fail): eight branches have no input.
Fix: one input per branch in `tests/test_notes_lines_check.py`, shown failing when the branch is removed (a mutant for each if the repo style needs one).

### [Group 5] [codebase N6; design nit] - Minor
Scope: `tools/mutation_runner.py` `extra_files` (patch 2007-2009, 2017-2020; test ~1199-1230).
Gap: the docstring says a link is left out but no test shows it; the per-mutant copy makes no parent folder (a nested entry raises OSError, the snapshot step does mkdir); the new lines have no mutant, only a unit test.
Fix: add a link test, a `mkdir(parents=True, exist_ok=True)` in the per-mutant copy (same as the snapshot step) with a nested-path test, and a mutant for each; or reduce the docstring to "root files only" and refuse a nested entry with a plain error.

### [Group 6] [codebase N2] - Minor
Scope: CHANGELOG.md:325.
Gap: names `tests/test_policy_changelog.py` for the four fast tests; they are in `tests/test_policy_renewal_copy.py:138-163`.
Fix: name the right file. Check every other file name in the batch 15 CHANGELOG entry against the tree with one script and fix each mismatch (sibling search).

### [Group 7] [design N4; evidence deviations] - Minor
Scope: builder evidence heads (stage and policy mutants at `d6f396f1`, mutants log at `49c874e5`, notes-check and gitleaks at `1d62c19d`, lint at `fd85c0bf`, full pytest at `3ad1cc45`); `GATES.md:13`, `:16`.
Gap: the builder's evidence is spread over older heads; the runner's evidence covers `ccb63021` except the `--day 2026-12-11/12/13` policy runs and the B15 set; `GATES.md:13` records `--auto a50d5b2e` not `--auto <PR base>` as `ci.yml:111`; `GATES.md:16` gitleaks on an earlier head.
Fix: the batch-16 builder runs every gate ONCE on the final head and stamps each evidence file with `git rev-parse HEAD`, including policy_mutants at `--day 2026-12-11`, `2026-12-12`, `2026-12-13` and the B15 set; correct the two `GATES.md` lines.

### [Group 8] [design N5] - Minor
Scope: `src/hadavin_sdk/sources/kubernetes.py:6-9`.
Gap: states as fact that the Kubernetes API accepts the review request "as a `create` of a review object that is not kept"; POLICY (`:455-471`, `:497-509`) says it was not found in a vendor source and lists it under `claims_unverified`.
Fix: use the POLICY wording. Comment-only change in `src`: state that, and that the policy tests still pass.

### [Group 9] [design nits; codebase N7] - Nit
Scope: `tests/test_policy_changelog.py:324-329` (`_renew_and_check` docstring is a dead expression after an import); `tests/test_policy_renewal_copy.py:1832-1834` (redundant `expected -= {"CHANGELOG.md"}`); `tests/test_k1b_cli.py` ~300 (CLI refusal test covers `tick` only while the CHANGELOG says "the commands that load the config exit 2"); `tools/notes_lines_check.py:65-67` (stale "not in a conftest" paragraph).
Fix: fix all four in the batch (cheap): move the docstring above the import, drop the redundant line, either test every command that loads the config or reword the CHANGELOG to "the `tick` command", update the docstring.

### [Group 10] [lead items; owner-only; impossible-now] - Minor
- LEAD ITEM (not a fix, do not touch the demos): `tools/mutation_runner.py` changed (manifest sha `a36adb7d9d68e4a9...`); the copies in the demos must be re-synced by the lead.
- IMPOSSIBLE-NOW: 12 Vault-server tests (no Vault server here; CI sets `HADAVIN_TEST_VAULT_ADDR`); next step: CI run on the PR.
- OWNER-ONLY: the Kubernetes start-up check does not refuse an over-broad read (documented and pinned); changing it needs the owner's decision (`q-q8c1-kubernetes-over-broad-read`).
- First real renewal 2026-12-12 (unchanged).

## Handoff
- PROPOSE FIX: 9 groups (1 Major, 7 Minor, 1 Nit). CONTEST: 0. ESCALATE: 0 (group 10 items are owner-only or lead items, recorded). DECLINE: 0. Remaining unaddressed: 0 beyond group 10.
- **Who fixes it:** one batch-16 builder on `core/q8c1-b16` from `ccb63021`, pushing to `wip/cloud-q8c1-b16`. Method per bug: name the class first, fix at the shared choke point (`tools/notes_lines_check.py` link-following), grep siblings, new tests shown failing on `ccb63021`, one mutant per fix, ONE full pytest and every gate at the final head, CHANGELOG counts recomputed, builder reports once.
- **Stop rule (lead ORDER 256), recommendation:** the Major (group 1) forces batch 16. After batch 16, run ONE confirming round because the path is a policy/security gate; if that round has 0 Blocker and 0 Major, fix its minors in one push without another review, record them in the ledger and mark the package READY. No third round for minors.
