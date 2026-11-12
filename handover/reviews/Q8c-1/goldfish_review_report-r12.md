Status: resolved

# Goldfish Annotated Review Report

**Target:** Q8c-1 batch 12, branch `wip/cloud-q8c1-b12`, code head `6d219217` (the builder's gates ran on local `cf5702ad`), round 12 (SECURITY path: policy page, notes check, grant data; no round cap).
**Inputs:** `q8c1b12-design-r12.md` (0 Blocker, 3 Major, 2 Minor, 4 Nit), `q8c1b12-codebase-r12.md` (0 Blocker, 3 Major, 5 Minor, 2 Nit), previous report `goldfish_review_report-r9.md` (newest before this one), independent evidence `handover/evidence/Q8c-1/6d219217/RESULTS.md`.
**Mode:** automated, recommended option for every item. No severity changed. Nothing contested. No Blocker; five Major stay open.

## Evidence summary (recorded, not judged)
- Full pytest: 1 failed, 10950 passed, 13 skipped, 28 deselected, exit 1. The failure is `tests/demo_askdata/test_validate_harm.py` dblink-connect, caused by the runner not setting PGHOST and PGPORT in its own server environment; that file alone gave 253 passed after the restart. **The whole suite was NOT re-run after the restart**, so there is no clean full-suite run on this head yet (group 10).
- Fail-before on `e4f1b2a4` with the changed test files: 18 failed, 401 passed; the builder said 17 failed. Failing-test lists were not compared.
- `git diff --stat origin/main..HEAD -- src`: 3 files, 536 insertions (`actions/secrets_vault.py`, `audit/signer_vault.py`, `sources/kubernetes.py`); empty against `e4f1b2a4`. This is the PR's earlier reviewed grant data; both reviewers found nothing under `src/` in this batch's delta and no grant added or widened.
- Green: ruff, format, bandit -ll, scan_repo, `policy_page --check`, gitleaks exit 0; `stage_mutants` 37 of 37; `policy_mutants` 235 of 235 good (weak 0 of 235) on the real clock, 235 of 235 at `--day 2026-12-11`, 234 of 234 at `--day 2026-12-12` (B12 not run by design); `notes_lines_check --auto e4f1b2a4` and `--auto origin/main` exit 0; the notes plant (a new test with no row) exits 1 with the right message.
- Not run: perf, the flaky timing test, the 12 Vault-server tests (no Vault server).

## Prioritized Findings & AI Suggestions (all PROPOSE FIX)

### [Issue 1] [design D12-1, codebase M1, m5] - Major
Scope: `tools/notes_lines_check.py:305-312` (`kind_of`), `:498-524` (`auto_files`), `:536`, `:225-257` (`closure`), `:207-257`, `:405`.
Gap: imports are followed one way. A PR that changes only a helper (`tests/contracts/vault_fake.py`, `tests/fixtures/fake_slack.py`, any `tests/**` file not named `test_*`, or `stray_days`, `changelog_entry`, `DAY_FORMS` in `tests/test_policy_guard.py`, `Pending` or `_fold` in `tests/test_lockin_guard.py`) gets "nothing to check", exit 0, or demands rows only for the same file's tests; importing files that did not change (`test_policy_changelog.py`, `test_policy_docs.py`) are never read. Unit tests pass explicit loaders and never go through `auto_files`. Follow gaps: `import tests.x` with no alias (usage `tests.x.name` yields only `tests.x`), and `_file_matches` accepts a basename cell so one row serves `tests/test_x.py` and `tests/contracts/test_x.py`. This is the r11 Issue 3 vector, closed in one direction.
Fix: compute signatures for every `tests/**/test_*.py` at merge base and head (`git ls-tree`), or add a reverse-import pass so every file importing a changed file is evaluated; resolve `import tests.x` attribute chains; match rows by full path; add an `auto_files` test whose only change is a helper module and one test per follow gap, each failing on `6d219217`. The CHANGELOG sentence is corrected to what the code then does.

### [Issue 2] [design D12-2] - Major
Scope: `notes_lines_check.py:143-170` (`_Module`), `:225-255`, `:298-302`.
Gap: a module-level `pytestmark` (skip or xfail) or conftest module state (`collect_ignore`, `pytest_plugins`, other module-level assignments) can switch off every test in a file with no row required. Same class as the autouse vector.
Fix: treat `pytestmark` as used by every test of its file; treat any module-level assignment in a conftest as a unit; plant tests for both, each failing on `6d219217`.

### [Issue 3] [design D12-3, codebase m1] - Major
Scope: `tests/test_policy_guard.py:1672-1678`, `:5398-5406`, `:220`, `:2888`; NOTES section B Issue 5.
Gap: hard-coded days fail on the first renewal (2026-12-12) with an unrelated message: `Pending('r','t',DECIDED, date(2026,12,10))` is overdue once `DECIDED` is 2026-12-12; `canary_day(date(2026,12,11), None)` returns the live floor, so both asserts at `:5399` and `:5402` fail. The notes omit these.
Fix: build every day from `DECIDED + timedelta(...)`, pass an explicit floor at `:5398`, correct the notes sentence and list, and add a test that scans the test files for date literals inside the renewal window and fails on any that is not derived.

### [Issue 4] [codebase M2, design D12-4] - Major
Scope: `tools/policy_page.py:826-863` (`RENEWAL_RULE`, `RENEWAL_STEPS`, `pending_problems`); kinds use it at `tests/test_policy_guard.py:103, :126`.
Gap: seven kinds go overdue on 2026-12-12 and are told to give `PENDING_NAMES` and `PENDING_CLAIMS` the same `DECIDED` day; kinds use `KINDS_DECIDED`, kept apart by design. Nothing says all 16 kinds share one day, or names `KINDS_LITERAL`, `KINDS_GROUPS` (`tests/test_policy_changelog.py:22-23`) and `_PR2[2]` (`tests/test_policy_guard.py:53`). The steps never name `tests/policy_mutants.py`: four mutants carry the old days as snippet text and a fifth carries "2026-12-11, whichever comes first" (`:1275`), so after a renewal none match and the blocking mutants step goes red with no hint. Step 3 says the changelog sentence "names the review day", but for names and claims it names none. The list test only checks that tokens and files appear.
Fix: kinds get their own message and steps (`KINDS_DECIDED`, the pin, `_PR2`, `KINDS_LITERAL`/`KINDS_GROUPS`, the changelog kinds sentence, the `policy_mutants.py` literals), or the mutant snippets are built from the live values; correct step 3; add a plant that performs the full renewal in a temporary copy and shows the guard and the mutants pass.

### [Issue 5] [codebase M3] - Major
Scope: `CHANGELOG.md:309`; code `tools/policy_page.py:13-16, :829`; tests `test_policy_guard.py:4440-4451, :4454-4462`.
Gap: the CHANGELOG says "every entry of the same list is renewed with it"; code and tests require BOTH lists (names and claims) to carry the same `decided` day, and kinds separately.
Fix: rewrite the sentence; add a test comparing it with the code constant.

### [Issue 6] [codebase m2, m4; design D12-8] - Minor
Scope: `notes_lines_check.py:429`, `_IDENTIFIER` (`:2785` in the delta); NOTES rows 60-62, 63, 66, 69, 70, 72, 209.
Gap: a mutant with no row can pass on another mutant's cell by substring (`X a` borrows the row of `X a b`); a row is checked for form only (any backticked text after "control" or "plant" passes; named mutants and log files are never checked to exist); several "control" rows explain why a test passes, not why it can fail.
Fix: match the whole cell or an exact `;`-separated item; cross-check each named mutant against `tests/policy_mutants.py` and each log file against `logs/`; rewrite the listed rows with the killing mutant.

### [Issue 7] [codebase m3, design D12-6] - Minor
Scope: `tests/test_policy_guard.py:4868-4938` (`_cleared_policy`, `_end_state`), `tools/policy_page.py:401, :1426`.
Gap: the end-state test is partly synthetic and its docstring says "nothing is stubbed": `_cleared_policy` sets `verified=(DECIDED.isoformat(),)`, which the real loader refuses (it needs at least 2 items); `pp.load`, `NOTE_CLASSES` and both dated lists are monkeypatched; the written page prints "sources " with an empty list.
Fix: use a real source id (for example V-POL) and reword the docstring to say exactly what is stubbed.

### [Issue 8] [design D12-5, codebase n2] - Minor
Scope: `tests/test_policy_changelog.py:22-40` (pin), `:48-69` (plant), `tests/policy_mutants.py:2370`.
Gap: the `KINDS_LITERAL` pin has no mutant; the runner runs only `[TEST, NOTES_TEST]`, so weakening `_kinds_pin_problem` together with its plant in one commit fails nothing.
Fix: add the file to the runner and a mutant of `_kinds_pin_problem` killed by the plant.

### [Issue 9] [codebase n1; design D12-7, D12-9] - Nit
Gap: `DAY_FORMS` misses `12-12-2026`, `20261212`, `12/12/26`, spelled numbers and flags plain text such as "7 may be"; the weak scan counts assert texts of every helper a killer calls transitively, so "0 of 235 weak" is an upper bound; `changelog_entry` ends the entry at the first column-0 line starting with `- `, `* `, `+ ` or `#`.
Suggestion: fix those in files the builder already edits (the day forms and the entry cut sit in `test_policy_guard.py`); list the rest with a reason. No new review round for Nits.

### [Issue 10] [evidence deviations] - Minor
Gap: no clean full-suite run exists for this head (see above); the fail-before count 18 against the builder's 17 has no failing-test list.
Fix: the final-head evidence of the next batch runs the whole suite clean with PGHOST and PGPORT in the server environment; the builder states the real fail-before count with the list of failing test ids.

### [Issue 11] [evidence] - closed
The green items in the evidence summary are recorded as closed by independent evidence.

## IMPOSSIBLE-NOW (not fixable here)
- The 12 Vault-server tests in `tests/test_policy_engine.py` (need `HADAVIN_TEST_VAULT_ADDR`): a CI run with `HADAVIN_REQUIRE_VAULT_ENGINE=1` before 2026-12-11; `ENGINE_RUN` stays None. Already ledgered (`Q8c1b8-r8-vault`).
- The CI notes step has never run on GitHub. Next step: a real PR run after the lead opens the PR (new row below).

## Handoff
- Findings in: design 3 Major, 2 Minor, 4 Nit; codebase 3 Major, 5 Minor, 2 Nit; merged into 11 groups.
- PROPOSE FIX: 10 groups (Major 1-5; Minor 6-8 and 10; Nit 9). CONTEST 0. ESCALATE 0. DECLINE 0. Closed by evidence: 1. IMPOSSIBLE-NOW: 2.
- Applied edits: none to code by this skill. Remaining unaddressed: groups 1-10 (OPEN). No Blocker.
- **Who fixes it:** one batch-13 builder (general-purpose, Sonnet) on `core/q8c1-b13` from `6d219217`, pushing to `wip/cloud-q8c1-b13`. Files: `tools/notes_lines_check.py`, `tools/policy_page.py`, `tests/test_notes_lines_check.py`, `tests/test_policy_guard.py`, `tests/test_policy_changelog.py`, `tests/policy_mutants.py`, `CHANGELOG.md`, the handover notes file, builder notes. Order: groups 1 and 2 (the check decides what else needs rows), 3, 4, 5, 6, 8, 7, then 9 and 10. Method per bug: name the class, fix at the shared choke point, grep for siblings, show each new test failing on `6d219217`, one mutant per fix; the day tests run at the real day, `--day 2026-12-11` and `--day 2026-12-12`. Gates once on the final head, gates run on the pushed commit, gitleaks after the final squash. Security path: no round cap.
