Status: resolved

# Goldfish Annotated Review Report (Q8c-1 batch 10, round 10)

**Target:** branch `wip/cloud-q8c1-b10`, head `d84412189fd92962b0769302007714c301f8823d` (delta `c6bd7108..d8441218`). SECURITY path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8c1b10-design-r10.md` (0 Blocker, 1 Major, 6 Nit) and `q8c1b10-codebase-r10.md` (0 Blocker, 1 Major, 6 Nit). Previous round: `goldfish_review_report-r9.md`. Independent evidence: `handover/evidence/Q8c-1/d8441218/RESULTS.md`.

**Evidence status (first).** ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 37 of 37; full pytest exit 0 (10908 passed, 13 skipped); `policy_mutants` 141 of 141 on the real clock, `--day 2026-12-11`, `--day 2026-12-12`, `--day 2026-11-12`; weak 0 of 141; 1 of 141 killed only by a clock-reading test; red baseline at 2026-12-12 is exactly 3 tests. **Mismatch to fix:** the builder said fail-before on `c6bd7108` was "3 failed, 368 passed"; the independent run gives 7 failed, 365 passed, 1 collection error (four files) and 3 failed, 369 passed, 1 collection error (with `policy_mutants.py`). **Probe result:** with both dated lists empty, `--check` and `--write` exit 1 unless `data_problems` is stubbed, because the kind modules still hold unchecked claims.

**Not run:** the 12 Vault engine tests (IMPOSSIBLE-NOW: need a CI run with `HADAVIN_REQUIRE_VAULT_ENGINE=1` before 2026-12-11; `ENGINE_RUN` stays `None`), perf, pip-audit, Semgrep, zizmor, CodeQL, SonarCloud, CodeRabbit, Python 3.12, the timing flake test.

## Prioritized Findings

### [Issue 1] [`codebase` C10-1] - Severity: Major
*   **Scope:** `tests/test_policy_guard.py` (`test_the_three_date_tests_read_the_clock_function_and_go_red_after_the_review_day`, `:1539`, `:4033-4036`, `:222`, `:4363`); `tests/policy_mutants.py` (`earliest_review_day`, `latest_review_day`, probe `failing_date_tests`); `tests/test_policy_changelog.py` (`kinds_sentence()`); `tests/test_policy_docs.py` (`str(pp.review_date())`).
*   **Description:** The date tests and the runner fail on a partial renewal or empty lists, the states this batch says it handles. The first honest renewal on 2026-12-12 would break them and push an engineer to edit or drop tests.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid, each point is checkable in the named lines; evidence confirms the empty-list failure.
*   ***Proposed Edit:*** One helper (also closes Issue 12) gives the review day of each list from that list's own entries and `None` when empty. The date test asserts per helper only for non-empty lists, with an explicit assertion that an empty list reports no overdue line. The runner and probe use the same helper and treat empty lists as a stated state. `kinds_sentence()` handles any number of day groups (none, one, many). The docs test branches on `None`. Replace date literals with values read from the lists. One test per state: renew only names and claims, renew a subset of kinds, both lists empty. The empty-list tests must run the real `--check`/`--write` path without stubbing `data_problems`, or the builder states in NOTES exactly which end state is covered and why. Mutants: helper takes the wrong list; `kinds_sentence` assumes two groups; docs test ignores `None`. Show each new test failing on `d8441218`.

### [Issue 2] [`design` D10-1, `codebase` C10-3: one finding] - Severity: Major
*   **Scope:** `tools/notes_lines_check.py:24-30, :41-51, :54-65, :85-92`; `tests/test_notes_lines_check.py`; `NOTES.md:29, :76-84, :88`; `.github/workflows/ci.yml`.
*   **Description:** The check can pass with a missing id: an id is found in any cell, the file part is dropped from the key, `MIN_REASON=12`, only top-level sync tests are read, helpers and constants are not compared, a mistyped base commit makes every test new, and the tool is not in CI. The words "every test" and "no test weakened" are not shown by it.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; checked against the line ranges.
*   ***Proposed Edit:*** Key on (file, id) read from the first two cells only; read `AsyncFunctionDef` and class methods; exit 1 when the base commit does not resolve; compare, for each test, the helpers, fixtures and constants it calls (same-file, one level at least) so a helper change lists its tests; raise the reason check to a real predicate (not just length); run it in CI on the files the PR touches. Drop "every" and "no test weakened" from docstring and NOTES wherever the tool cannot show them. Plants: id only in another row's reason cell, same name in two files, an async test, a method, a helper change, a bad base. A mutant for each new branch.

### [Issue 3] [`design` D10-2] - Severity: Nit
*   **Scope:** `tests/test_policy_guard.py:4577`.
*   **Description:** The `re.search(...head.split("## ")[0])` assertion cannot fail.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Scan the whole head, strip `policy_sources_*.txt` names, require no day; show it failing on a planted day.

### [Issue 4] [`design` D10-3, `codebase` C10-5: one finding] - Severity: Nit
*   **Scope:** `tools/policy_page.py:1712-1722, :1746, :1786, :792-802`.
*   **Description:** With no dated list, the OpenBao trigger text borrows a date that no longer exists, and a second sentence sits in the Kubernetes bullet.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** State the OpenBao trigger on its own: the date trigger does not apply, only the deployment trigger remains. Plain words. Test reads the page without stubbing.

### [Issue 5] [`design` D10-4, `codebase` C10-2, C10-4: one finding] - Severity: Nit
*   **Scope:** `tests/policy_mutants.py:60-106, :1476-1481, ~1139-1305`; `weak-expect-after.txt`; NOTES section C.
*   **Description:** The weak scan is printed only (no exit 1), counts every string in a message expression (a dict of per-case texts is a union), `weak-expect-after.txt` is empty though NOTES says it holds the count, and an 8-row table is called "the five tests".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Count only direct string and f-string pieces of the message; exit 1 on a non-empty weak list; state the dict case in the docstring; write the real count into the file; fix the NOTES wording; strengthen newly weak killers.

### [Issue 6] [`design` D10-5, `codebase` C10-6: one finding] - Severity: Nit
*   **Scope:** `tests/test_policy_changelog.py:16-28, :47-50`; `tests/test_policy_docs.py:15-20`.
*   **Description:** The old test keeps date literals and the literal sentence; two different entry cuts; day guards know only the ISO form.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** One shared entry-cut function; old test reduced to the structural pin; widen day guards to "12 December 2026", `2026/12/12`, "Dec 12", or state ISO-only in the guard's message and test it.

### [Issue 7] [`design` D10-6] - Severity: Nit
*   **Scope:** `tests/policy_mutants.py:1282-1299, :1320-1343, :1425-1448`; `tools/policy_page.py:826-828`.
*   **Description:** The red-baseline reading accepts any red set equal to the three tests (`--day 2020-01-01` gives the same three), `--day=` is not parsed, ERROR lines are not counted.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Require "is overdue" in the red output, refuse a day before DECIDED, accept `--day=`, count ERROR lines; tests and mutants for each.

### [Issue 8] [`design` D10-7] - Severity: Nit
*   **Scope:** `handover/evidence/Q8c-1/b10/`.
*   **Description:** GATES.md for b10 and the cited logs live outside the repo.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Commit GATES.md and the logs (`plant.log`, `fail-before.log`, `policy-1212.log`, `old-tree-day-1212.log`, `g-pm-*.log`) from `/home/user/build/b10-ev/`; gitleaks first; correct the fail-before count to the independent figure.

### [Issue 9] [`codebase` C10-7] - Severity: Nit
*   **Description:** "Earliest review day" computed in four places.
*   ***AI Suggestion:*** PROPOSE FIX (one helper, part of Issue 1).

## Handoff
Accepted fixes (PROPOSE FIX): 9 findings (2 Major, 7 Nit; the two reviewers' 14 items merge into these). Contested: 0. Escalated: 0. Declined: 0. Unaddressed: 0 (all go to the batch-11 builder). Severities unchanged.

**Who fixes it:** one batch-11 builder on a new branch from `d8441218`, pushing to `wip/cloud-q8c1-b11`. Files: `tools/policy_page.py`, `tools/notes_lines_check.py`, `tests/policy_mutants.py`, `tests/test_policy_guard.py`, `tests/test_policy_changelog.py`, `tests/test_policy_docs.py`, `tests/test_notes_lines_check.py`, `CHANGELOG.md`, `.github/workflows/ci.yml` (one step), `handover/evidence/Q8c-1/b10` and `b11` notes. `tools/mutation_runner.py` only if unavoidable and stated.
