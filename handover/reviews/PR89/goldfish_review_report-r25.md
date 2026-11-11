Status: resolved

# Goldfish Annotated Review Report (PR89, round 25)

**Target:** branch `wip/cloud-PR89-r20`, head `580b4adf` (snapshot `/home/user/build/snap/pr89r24-580b4adf`). Mutation runner, security path: no round cap. No person was available: recommended option for every item. Reviews: `/home/user/build/reports/pr89r25-design.md` (0 Blocker, 1 Major, 5 Nit) and `pr89r25-codebase.md` (0 Blocker, 0 Major, 5 Nit); both read-only.
**Evidence (independent, head confirmed):** `handover/evidence/PR89/r25/RESULTS.md`. ruff, format, bandit, scan_repo, stage_mutants 37/37, gitleaks: exit 0. Full pytest 10816 passed, 3 skipped (2 extra skips are the mypy-win32 tests; mypy is not in the locked venv). Full mutants 320/320 good. mypy win32: 13 errors on 3.12 and 3.13, same lines. 498-case leak probe: 0 shown. Builtin-class probe 1185 cases: 8 shown, all a piece of the class name (the documented design). Fail-before: 16 new tests, 13 fail on old code, 3 pass on old code; against origin/main the overlay fails at collection (`PASS_ENV_ALLOWED`).

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` D1, `codebase` N1] - Severity: Major (design) / Nit (codebase)
*   **Affected Scope:** `tools/mutation_runner.py:1043-1060` (`_shown_class`; case-insensitive equality only when head in `_BUILT_IN_CLASSES`; caller-owned names via `_own_text` -> `_masked` case-sensitive); docstring table `:175-178`; CHANGELOG round 24; test `test_the_module_docstring_says_a_class_equal_to_a_secret_is_not_shown` (phrases only).
*   **Discrepancy Description:** `shown_classes=("PostgresError",)` with password `postgreserror` and a child raising `PostgresError` shows the name, which equals the password up to letter case. Secret forms do not include lower/title case. The docstring table reads as case-insensitive for all shown classes.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the rule must be one rule at the choke point. Reviewers disagree on severity (Major vs Nit); severity is not changed here, the fix is cheap and the path is security.
*   ***Proposed Edit:*** One equality rule for every name in shown.classes: hide when its `casefold()` equals the `casefold()` of any secret (or of any derived form). Test with `crash_type` and `shown_classes` plus a different-case password; a mutant that restores the case-sensitive path for caller-owned names. Docstring and CHANGELOG say "any letter case" for all shown classes.

### [Issue 2] [`design` D2] - Severity: Nit
*   **Affected Scope:** `_shown_class` `:1056-1059`.
*   **Discrepancy Description:** hiding on equality is an oracle when the real class can be inferred (KILLED row implies AssertionError; declared `crash_type`); the "[class not shown]" marker tells the reader the password equals that name.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the address check already refuses odd passwords; refusing a password casefold-equal to an allowlisted class name removes both the oracle and the special case, which is also the simplest way to make Issue 1 uniform.
*   ***Proposed Edit:*** In `_refuse_unsafe_address`, refuse a password whose casefold equals any allowlisted or built-in class name (fixed sentence). If the builder keeps the hiding rule instead, state the inference in the docstring. Tests plus mutant.

### [Issue 3] [`design` D3] - Severity: Nit
*   **Affected Scope:** `_row` `:1787-1842`, `_baseline_failure` `:1752`, `_refuse_skips_in_baseline` `:1731`, `_canary_refusal` `:1763`, rebuild message `:2037`.
*   **Discrepancy Description:** no single choke point for reader-visible text; a convention, guarded by the seeded 13-output test; the AST pin covers creation sites, not output sites.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** the seeded 13-output test and the 498-case independent probe (0 shown) cover the present sites; an output-site AST pin is a new guard, not a defect in this change. Recorded in the ledger as a candidate for the next round only if a site is found. Not contested: the reviewer is right that it is a convention.
*   ***Proposed Edit:*** none; ledger line.

### [Issue 4] [`design` D4] - Severity: Nit
*   **Affected Scope:** class-name piece-of-name asymmetry (built-ins: pieces do not hide; caller-owned: substring `_masked` hides the whole name).
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** coherent and documented (docstring `:225-226`, pinned by tests); the independent probe found only the 8 piece-of-name cases the design names. Add one sentence next to the Issue 1 docstring change so the asymmetry is stated, no code change.
*   ***Proposed Edit:*** one docstring sentence only.

### [Issue 5] [`design` D5] - Severity: Nit
*   **Affected Scope:** docstring `:227-229` "every folder ... whatever the umask and is checked" vs `_make_dirs` `:1202-1212` (intermediate parts `os.mkdir(here, 0o700)`, no chmod back, no check; AST pin lists `_make_dirs` as allowed).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the wording overclaims; routing through `_make_private_dir` is the better fix (fixes the claim at its source).
*   ***Proposed Edit:*** route the intermediate parts through `_make_private_dir` (checked, 0700 whatever the umask); if a part may legitimately pre-exist, say so. Test with umask 0277; docstring and CHANGELOG match.

### [Issue 6] [`design` D6, `codebase` N3] - Severity: Nit
*   **Affected Scope:** `tests/test_mutation_runner_keywords.py` mypy test (skipif no mypy; `:5878-5882`), `pyproject.toml` (no mypy entry), docstring `:46-50`, CHANGELOG.
*   **Discrepancy Description:** the 13-error count rests on a one-off measurement; CI does not run it; the test would fail with a mypy config or a typed `hadavin_sdk`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** a claim with a number needs a run that CI performs, or plain words that it does not.
*   ***Proposed Edit:*** add mypy to the test dependency group and pin the version in the locked environment, run `--no-project --platform win32 --no-incremental` with fixed flags (`--no-error-summary` etc.) so the output shape is stable; make the test parse errors robustly. If adding the dependency needs a lock change the lead must approve, say so in the docstring instead and keep the AST name-count table.

### [Issue 7] [`codebase` N2] - Severity: Nit
*   **Affected Scope:** `tests/test_mutation_runner_keywords.py:5994-6034` (AST pin).
*   **Discrepancy Description:** docstring says "every call of a creating function of the standard library is found"; the set omits `shutil.copytree/copy`, `os.rename/replace/symlink/link/mkfifo`, `tempfile.TemporaryDirectory`, aliased imports; module-level code is not walked; `p.write_text` depends on the local name `p`. Independent evidence lists the same unhelpered sites (`shutil.copytree` 1911, 1918, 1963, 1972; `shutil.copy` 1915, 1969; `p.write_text` 2011 overwrites an existing file).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** soften the claim and cover the listed spellings, including module-level code and `from x import y` aliases; each copy site stays documented as on purpose (caller's modes) or gets its check.
*   ***Proposed Edit:*** extend the set and the walk (module body, aliases); docstring says "the listed spellings"; list the allowed sites by line-free name.

### [Issue 8] [`codebase` N4] - Severity: Nit
*   **Affected Scope:** `tests/test_mutation_runner_meta.py:714-726, 690-711` (`_true_on_windows`).
*   **Discrepancy Description:** any `skipif` condition not built from `sys.platform`/`os.name` comparisons with a constant, `or`/`and`/`not` evaluates to "no skip" silently; `pytest.skip` inside a body and module `pytestmark` are not seen.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** make `_true_on_windows` raise on a condition it cannot evaluate; scan module-level `pytestmark`; the header keeps naming in-body skips by hand, with a test that each named killer contains `pytest.skip`.

### [Issue 9] [`codebase` N5] - Severity: Nit
*   **Affected Scope:** runner `:1253-1264` (`_make_private_file`: `O_TRUNC` open, `os.chmod(fd)`, then `_file_problem` link-count check).
*   **Discrepancy Description:** a pre-existing file with `st_nlink > 1` is emptied before the refusal (only same-user can plant it, in a private folder: a limit, not a bypass).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** open without `O_TRUNC`, check on the descriptor, then `ftruncate`. Test with a hard link: the linked file keeps its content when refused; mutant.

### [Issue 10] [`evidence` fail-before] - Severity: Minor
*   **Affected Scope:** 16 new test functions; 3 pass on old code (`password that is only a piece of a class name does not hide the class`, `password that holds a whole class name does not hide the class`, `header names every mutant whose killer is skipped on Windows`); 4 older changed tests also fail on old code (names in RESULTS.md).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** one line each in the builder notes: why it passes on old code (a control for a class fixed earlier; header derivation test checks a list that existed) and the mutant that proves the guard is live; any test with neither a failing old case nor a mutant gets one. The overlay failing at collection on origin/main is expected (main has an older runner) and is recorded, not fixed.

### Items recorded, no change
*   Evidence deviations: `uv sync --locked --no-build` fails here (used `--all-extras --group test`); fail-before against origin/main gives no per-test result (collection); leak and builtin-class probes use the builder's scripts with paths changed; Windows, macOS, perf, CodeQL, Sonar, CodeRabbit not run (CI only). Checked fine by both reviewers: `os.chmod(fd)` under the platform guard, 320 = EXPECTED_MUTANTS, 52 POSIX-only names, order-swap mutants, `_file_problem`, bare-string guard order, junit parse errors.

## Handoff counts
Accepted (PROPOSE FIX): 8 (Issues 1, 2, 5, 6, 7, 8, 9, 10). Declined: 2 (Issues 3, 4; with reasons above). Contested: 0. Escalated: 0. Round 26 review needed after the fix batch (security path, no round cap): reviewers on the new snapshot plus independent evidence on the fixed head.
