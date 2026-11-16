Status: resolved

# Goldfish Annotated Review Report, PD Part 6 (mode banner and demo-only guard), round 13

**Target:** `/home/user/build/snap/pdbanner-63996217/DIFF.patch` (full), head `63996217d8c2e0f5c21218ac0ce7ca58e20081d4`, mode-safety path (no round cap).
**Inputs:** `pdbanner-63996217-design-r13.md` (0 Blocker, 1 Major, 7 Minor, 2 Nit) and `pdbanner-63996217-codebase-r13.md` (0 Blocker, 2 Major, 8 Minor, 4 Nit). Both reviewers read code only and ran nothing. Evidence runner a34f80e2 has not reported (`handover/evidence/PD-banner/63996217/RESULTS.md`); its findings are an addendum for the builder.
**Method:** every finding checked against what the reviewers could read; none contested. 26 findings merge into 6 issues (1 ESCALATE, 5 PROPOSE FIX). Settled from r11 and r12 stays settled: seal by identity; masker core limits equal main (Bearer 12+, Basic 8+); `is_stand_in` not called until Part 2 merges; deepcopy of an App raises on purpose; no suppressions and no per-file ignores except `tests/**` S101; named tuple plus surprise-error test for broad excepts (done for all five `READ_ERRORS` sites and `post_card`).
**Result:** no Blocker and no fail-open path found by either reviewer. All r12 classes are fixed in substance (five broad catches narrowed, waivers removed, 333 rows, strict expectation check). What remains: one ruff finding that needs a lead ruling, one probable surviving mutant row, masker text that now contradicts the code, wrong fail-before labels, and the sibling-file dependency. Batch 14 changes code on a mode-safety path, so a fresh round is required.

## ESCALATE first (lead decision)

**S603 at `tools/fixed_run.py:30`** (`return subprocess.run([exe, *argv[1:]], check=check, **kwargs)`): ruff S603 still fires; the builder confirms it is the only ruff error. The reviewer's evidence is the CI line (`ruff check src tests demos tools`, `extend-select` contains S) and the removed per-file ignores. No waiver and no per-file ignore is allowed.
Options for the lead:
1. **Restructure (recommended): no shared passthrough helper.** Each call site passes a literal list (`subprocess.run(["git", "-C", root, "ls-files", ...], ...)`) after resolving the program with `shutil.which`. S603 is only reported for a non-literal first argument when the rule cannot see a literal list; ruff does not fire on a literal list whose elements are variables. Delete `tools/fixed_run.py`, `tests/fixed_run.py` and the sibling-file import (this also removes design m3, m4, m5 and codebase m8, m9 in one step). Cost: three or four call sites repeat a four-line pattern. Test: a repo guard test that every `subprocess.run` call in `tools/` and `tests/` has a literal list first argument and no `shell`.
2. One per-file ignore of S603 for `tools/fixed_run.py`: refused earlier by the lead; listed only for completeness.
3. Inline marker: refused (suppression rule).
Until the lead rules, the builder does option 1 for the guard and `scan_repo.py` and reports the ruff result; if ruff still fires on a literal list, the builder reports the exact line and does not suppress.

## Decisions made here

1. **Design m4 (guard sibling-file dependency): the guard keeps ONE git call inside itself** and loads no sibling file. This removes the `exec_module` path, the `-I` fallback and the fake-`CompletedProcess` risk. (Consistent with option 1 above; if the lead keeps a shared helper instead, the guard must check that the file list is non-empty.)
2. **Design m3 (kwargs):** moot with option 1; if a helper survives, it passes only `cwd`, `env`, `capture_output`, `text`, `check`, `timeout`, `input`, `encoding` and refuses everything else, including `executable`, `preexec_fn`, `shell`, `stdin`.
3. **"LIVE" display word (design m6):** keep. The old stage word is `dev`; the three stage names are demo, pilot, prod. `LIVE` is the banner's display tag for prod (a display word, not a stage name). State it in one line in the CHANGELOG and in a test that the banner tag for prod is `LIVE`.
4. **Design m7 (pre-existing suppressions in untouched code):** declined for this diff; the claim is "this diff adds none", and the CHANGELOG and brief must say exactly that, not "no suppressions anywhere".

## Prioritized findings

### Issue 1, Major, class MUTANT-KILLER (codebase M1)
Row R13B2 ("bypass shown with any value", `tests/banner_mutants.py`) mutates `if not named_secret and end >= last_text:` (drops only the flag-word test). Every hidden-side case has trailing text (`bypass=abc123 tail`, `bypass=true x`, `a=b bypass=Off y=1`), so `end < last_text` hides them and the mutant still passes: a probable survivor; the label overstates the mutation. Rows R13B3 and R13B4 are out of numeric order; R13A4 and R9A4 share a search text (fine, different mutations).
PROPOSE FIX: add hidden-side cases with nothing after the value (`bypass=abc123`, `bypass=truex`, `bypass=2`, `x bypass=yes!`) to the killer test; rename the row text to say exactly what it removes; order the rows; the runner reports killed or survived for R13B1 to R13B4 and the builder re-runs until all are killed; add a CHANGELOG-independent check that every row killed in the table run is in the focused list.

### Issue 2, Major, class MASKER-TRUTH (codebase M2, m3, edge row)
The code now hides more than main (`_hide_shaped_scheme_token`, `authorization=<scheme> <token>` at any length), but: `tools/demo_only_guard.py:281-284` still says rule 2 is "EXACTLY the two rules of hadavin_sdk.guard.redact ... shorter tokens stay visible, as in the core"; `:296-297` says "11 characters or fewer after a bearer word stays visible" (a mixed token is hidden); `CHANGELOG.md:14` (batch 10) says "same patterns and order as main"; the test `test_a_bare_scheme_word_hides_what_the_core_hides_and_no_more_by_a_table` keeps "and no more" while its token changed from `"a1"*30` to `"a"*30`, so the table no longer covers the divergence. The CHANGELOG limit "letters only, 11 or fewer (7 after Basic)" is looser than the code: `_SCHEME_TOKEN` accepts `. - ~ _`, so `Basic abc-defghijk` (12, no digit) stays visible and non-letters-only tokens with no digit stay visible up to 15 characters. Edge: `authorization=Bearer "abc def"` hides `"abc` and leaves `def"` visible (token stops at white space).
PROPOSE FIX (one choke point, the rule text is written once in the guard and the CHANGELOG quotes it): rewrite the guard comments to say "the two core rules, plus these extra hiding rules (list them); the guard shows no more than the core on any input"; state the visible limit exactly: a token after a bare scheme word stays visible only if it has no digit and is shorter than the core limit (11 for Bearer, 7 for Basic) and under 16; fix the CHANGELOG batch 10 paragraph; rename the test `..._hides_at_least_what_the_core_hides_by_a_table`; add a mixed-token row marked as an intended difference; add rows for `Basic abc-defghijk` (visible, stated) and `authorization=Bearer "abc def"` (hide to the end of the line; fix the code to hide a quoted value, or state and pin the exact shown text if the lead prefers). Run the full redaction and stage-name test files, not a focused list.

### Issue 3, Minor, class LABEL-TRUTH (codebase m4, m5, m6; design nit)
1. Log-once rule is misleading: `App.mode_banner` calls `banner_or_unconfirmed` (`app.py:316`) which logs on every call (`mode_banner.py:744`); `_warn_once` covers only `_known_overrides` and the `registry.tools` read. State both paths in the CHANGELOG and docstrings, with a claim test for each.
2. `test_the_changelog_states_the_row_count_of_the_table` says it fails on c7eb5c79 with "does not say that the table has 332 rows": old ROW_COUNT and CHANGELOG say 320, so it passes there; 332 exists at neither head. Fix the text to the real raw line; the comment in `test_banner_mutant_table.py` that says "332" becomes 333.
3. The shared-start pins (`test_pin_the_shared_start_of_a_program_*`) say "passes there (the helper file is copied in)" but on an unmodified old head `tools.fixed_run` does not exist (ImportError). With option 1 above these tests are replaced by the literal-list guard test; label that new test from a raw run at dd827d79 and c7eb5c79.
4. The deleted test `..._whatever_the_name_of_the_log_helper` removed the only helper-independent log-name check: restore it for the new log lines or state the drop in the CHANGELOG.
5. `test_the_changelog_names_the_exact_error_types...` uses `delivery.split(", ")[:-1]` (drops `RuntimeError`) and `name in text` anywhere: assert the full `_DELIVERY_ERRORS` phrase.
PROPOSE FIX: as listed; labels come from raw runs of the new and changed tests at dd827d79 and c7eb5c79 in `git worktree`s.

### Issue 4, Minor, class SIBLING-FILE / SUBPROCESS (design m3, m4, m5; codebase m8, m9)
`run_fixed` refuses only `shell=True` and passes `executable=`, `cwd=`, `preexec_fn=`; "fixed list" is convention (callers pass `cmd`, `*flags`, `*pytest_args`); the guard loads `tools/fixed_run.py` by path with `exec_module` (a fake `CompletedProcess` would make the guard pass an empty file list; a foreign installed `tools` package could be imported first when run without `-I`); `scan_repo.py:17-20` has a different bare-name fallback that fails under `-I`.
PROPOSE FIX: option 1 and decision 1 above: literal lists at each call site, no sibling file, no importlib fallback, one subprocess guard test (literal first-argument list, no `shell`, no `executable`); delete `tests/fixed_run.py`; guard test that the guard and `scan_repo` import nothing from `tools/`. If a call site needs a variable-length list, build it as `["git", "-C", root, "ls-files", *fixed_flags]` where `fixed_flags` is a module constant tuple.

### Issue 5, Minor, class TEXT (design m1, m2, nits; codebase nits, m7)
`tests/test_mode_banner.py:1587` comment "refuses in prod for being dev-only" (old stage word in a test; reword to "demo-only"); `:3768` `getattr(mb, "READ_ERRORS", None) or mb._READ_ERRORS` is dead compatibility code (use `mb.READ_ERRORS`); `ROW_COUNT` (`banner_mutants.py:2528`) is a typed constant (derive `len(M)`, keep the AST test as the independent count; CHANGELOG states 333 or the derived number); `test_demo_only_guard.py:2555,2573` import `run_fixed` locally while the module aliases `tests.fixed_run.run as run_fixed` (line 28) (goes away with option 1); odd hard-wrap orphan lines (`app.py:58-63`, `mode_banner.py:142-145,164-174,752-758`, `demo_only_guard.py:360-362`); added lines over 100 columns (`demo_only_guard.py:292,1391`, long fail-before comments, `banner_mutants.py` rows; two docstring lines the builder already named in `app.py` and `tests/fixed_run.py`).
PROPOSE FIX: do all of these; `grep -rniw "dev" tests/test_mode_banner.py` and the repo stage-name scanner both clean.

### Issue 6, Minor, DECLINE
Design m7 (pre-existing suppressions in untouched files): see decision 4. Codebase m10 (R13A4 near-duplicate of R9A4): kept, different mutation.

## Handoff counts

- PROPOSE FIX accepted: 5 issues (1, 2, 3, 4, 5). ESCALATE: 1 (S603). DECLINE: 1 (issue 6, two items). CONTEST: 0.
- Remaining unaddressed: 0. **Round 14 is REQUIRED** (mode-safety path, no cap; the batch changes code and the masker).

## ONE FIX BRIEF (single small builder, batch 14; fast-forward only onto `wip/cloud-pd-banner` from 63996217)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and focused rows only, at most 2 heavy processes, each command under 8 minutes and resumable); real fail-before runs in `git worktree`s at dd827d79 and c7eb5c79 with raw lines; no suppressions and no per-file ignores; fake credentials built from parts; never commit under `handover/`; commit first, push, then finish runs; run the FULL redaction, stage-name and repository-text test files (not a focused list) and list every test file you did not run; a suppression-marker count on added lines against `origin/main` in the report; **NEVER answer y/yes to a start or confirm prompt of any script that can reach a network or send mail; run only loopback settings; a prompt means STOP and report.**

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | MASKER-TRUTH | issue 2: guard comments, CHANGELOG batch 10 and 13 text, test rename, mixed-token row, `Basic abc-defghijk` row, quoted-value row (hide or pin) | table rows both sides | row for the quoted-value rule if code changes | raw lines |
| B | MUTANT-KILLER | issue 1: end-of-line hidden-side cases, R13B2 label, row order | the planted cases | R13B1-B4 all killed | the runner and the builder run the rows |
| C | LABEL-TRUTH | issue 3: log rule per path, 332 to 333 text, helper-pin labels, full delivery phrase, restored log-name test | claim tests | none | raw lines at dd827d79 and c7eb5c79 |
| D | SIBLING-FILE / SUBPROCESS | issue 4: literal lists per call site, delete `tools/fixed_run.py` and `tests/fixed_run.py`, guard keeps ONE git call; report the ruff result; no suppression | literal-list guard test; no import from `tools/` test | row restoring a variable list | raw lines |
| E | TEXT | issue 5 | stage-word scanner clean; `READ_ERRORS` used directly; ROW_COUNT derived | none | n/a |

Builder reports once when ALL of A-E are done: new head sha, `ruff check src tests tools` raw output (S603 count must be 0, else the exact line), raw fail-before lines, masker rows that differ from main (full list), the list of test files not run, suppression grep on added lines, `pyproject.toml` diff against main, anything not done and why.

## Round 14 and evidence for the final head

- **Round 14 is required.** Fresh design and codebase reviewers on a new snapshot; they count suppression markers on added lines, inspect `pyproject.toml` for per-file ignores beyond `tests/**`, and look for any row where the masker shows more than main.
- **Cloud evidence (one runner on the FINAL head, records only):** focused tests on Python 3.12 and 3.13 including the full redaction, stage-name and repository-text files; all new and changed rows plus a 60-row sample; the 20 `COMPUTED_EXPECT` rows against their first failing lines; fail-before with raw lines; suppression grep; masker table against main; surprise exception injected at each of the five `READ_ERRORS` sites and `post_card`.
- **RUN ON LAPTOP (Linux Docker, final head only, after a fresh round finds 0 Blocker and 0 Major):** hadavin-sdk `<final sha>` full pytest plus the complete banner_mutants (333+ rows) and stage_mutants tables, py313 and py312, Postgres, CI flags, bandit, demo-only guard. Windows is not valid evidence.
- Ledger rows PDBANNER-r13-1..5 exist (r13-1 is the S603 ESCALATE).
