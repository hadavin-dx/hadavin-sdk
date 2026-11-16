Status: resolved

# Goldfish Annotated Review Report (Q8c-1 batch 9, round 9)

**Target:** branch `wip/cloud-q8c1-b9`, head `c6bd7108d3843f9d22f5344966af8e9783969251` (delta `208a47d5..c6bd7108`). SECURITY path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8c1b9-design-r9.md` (0 Blocker, 2 Major, 3 Nit) and `q8c1b9-codebase-r9.md` (0 Blocker, 0 Major, 5 Nit). Previous round: `goldfish_review_report-r8.md`. Independent evidence: `handover/evidence/Q8c-1/c6bd7108/RESULTS.md`.

**Evidence status (first).** ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 37 of 37; full pytest exit 0: 10892 passed, 13 skipped, 0 failed (no dblink failure with PGHOST and PGPORT in the server environment; the builder's one failure was its own set-up slip); `policy_mutants` 122 of 122 on the real clock and with `--day 2026-12-11` and `--day 2026-12-12`, probe line printed, weak 0 of 122, per-mutant lines identical in the three runs; `policy_page.py --check` exit 0. Fail-before on `208a47d5` (delta test files only): 3 failed, 357 passed. Of the 8 new tests, 5 PASS on the old code (CI-step plant, changelog-reminder plant, the two decision-day tests, the fixed-day-seen test): each needs a stated control reason or a killing mutant (Issue 6). Overlay on main: 241 failed, 127 passed.

**Not run (listed, not hidden):** the 12 Vault engine tests (IMPOSSIBLE-NOW: no Vault here; needs a CI run with `HADAVIN_REQUIRE_VAULT_ENGINE=1` before 2026-12-11, then `ENGINE_RUN` and the pinned page test edited by hand; the gate stays honest, `ENGINE_RUN` is still `None`), the perf step, pip-audit, Semgrep, zizmor, the real ticket 6.4 table (stale: it names ten modules and an old page name; F1 and F2 mapped by the builder, F3 not run).

**A claim the evidence does not back.** The builder and the evidence runner both show the fixed day reaches the tool's clock (`pp.datetime`). Neither shows it reaches the tests that read a real clock (`TODAY`). The design reviewer's reading of the code (`tests/test_policy_guard.py:36, :159, :1497, :1504`, `TODAY` fixed once at import) is checkable and I find no code reason it is wrong. The claim "no mutant result changes with the date" is therefore not shown (Issue 1).

## Prioritized Findings & AI Suggestion

### [Issue 1] [`design` B9-1] - Severity: Major
*   **Scope:** `tests/test_policy_guard.py:36, :159, :1497, :1504, :985-991` (autouse fixture); `tests/test_lockin_guard.py:23` (`TODAY`); `tests/policy_mutants.py` (`--day`, probe); `handover/evidence/Q8c-1/b9/NOTES.md` Issue 6, `GATES.md`.
*   **Description:** The fixed day patches only `pp.datetime`. The date-guard tests of the 16 kinds, the names and the claims use `TODAY` (the real day at import). So `--day 2026-12-12` gives a green baseline and "122 of 122" although a real clock on that day would make those three tests fail. The probe proves the variable reaches a clock that no date-dependent test reads: the same class of error as the earlier shim slip.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid and checkable in the files named; the evidence confirms only the narrow part.
*   ***Proposed Edit:*** One source for "today" in the guard file: a function (patched by the fixture, read from the fixed-day variable only under Issue 4's marker) used by `:159`, `:1497`, `:1504` and any other `TODAY` consumer (grep for siblings in all `tests/test_policy_*.py`, `tests/test_lockin_guard.py` and `tests/fixtures`). Then `--day 2026-12-12` must give a RED baseline for those tests: the runner reports that as the correct result (a baseline that is red only because of the faked day is named as such, not as a broken tree). The honest claim replaces "no mutant result changes with the date": the runner prints the list of mutants killed ONLY by date-dependent tests (found by running the three days and comparing the per-mutant killers, or by the killers' use of the clock function); the probe asserts on a consumer that exists (the kinds test at a faked 2026-12-12 must fail). Reword NOTES and GATES to say exactly what was shown. Mutant: the clock function reverts to the real day; killed by the probe consumer.

### [Issue 2] [`design` B9-2, `codebase` N9-1: one finding] - Severity: Major
*   **Scope:** `tools/policy_page.py:783-788` (`review_date()`), `:1699-1705` (`head()`, `.replace("REVIEW_DATE", ...)`), `:1730`, `:1770`.
*   **Description:** `review_date()` is `min()` over `PENDING_NAMES` and `PENDING_CLAIMS` with no default. The ticket's end state is both lists empty (nothing pending). Then `head()` raises `ValueError`; `--write`, `--check` and every page test crash instead of reporting. The two page sentences also keep a date slot with no date. The code of this batch creates the failure; no test empties the lists.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid; a crash at the goal state of the whole ticket is a defect, not a limit.
*   ***Proposed Edit:*** `review_date()` returns `None` when both lists are empty; `head()` renders the two sentences only when there is a date, and otherwise says plainly that no name or claim is pending (wording per `wording-clear-for-everyone`). Tests: plant both lists empty (and one empty, one not) and expect `--write` and `--check` to succeed and the page to hold no date text; a mutant that makes `review_date()` raise again, and one that keeps the sentence without a date.

### [Issue 3] [`design` B9-3, `codebase` N9-2: one finding] - Severity: Nit
*   **Scope:** `tests/policy_mutants.py:85-97` (`weak_mutants`, `_same_calls`: `m.expect not in calls[m.only_test][1]`), comment `:47-52`; NOTES Issue 4.
*   **Description:** "Specific" is decided by the expect text appearing anywhere in the killer's source after the `same()` lines are cut: loop literals, `any("..." in p ...)` predicates, comments, the def line. So `weak 0 of 122` is weaker than its docstring. Two named cases: "B5 the two paths of a prefix check" (text only as a loop literal; the failing `same(...)` has no `what`) and "B5 a reason needs no class" (text inside an `any(...)`; the assert message does not hold it).
*   ***AI Suggestion:*** PROPOSE FIX (worth doing: a measure that overstates is the thing round 8 Issue 2 asked to fix)
*   ***Proposed Edit:*** Count only string constants that are the message argument of an `assert` or the `match=` of `pytest.raises` (AST, not text), plus `what=` of `same()`. Recompute the weak list; commit the new list as `weak-expect-after.txt`; strengthen each newly weak mutant's killer by naming the expect text in its message. Mutants for the scan (a killer whose text is only in a comment stays weak).

### [Issue 4] [`design` B9-4] - Severity: Nit
*   **Scope:** `tests/test_policy_guard.py:985-991` (autouse fixture reads `HADAVIN_POLICY_FIXED_DAY`).
*   **Description:** If the variable is set in any developer or CI environment, it silently rewrites the clock for the whole file; after Issue 1 this would switch off the date reminder inside pytest.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Honour it only when a second marker is present that only the mutant runner sets (for example `HADAVIN_POLICY_MUTANT_RUN=1` in `CHILD_FIXED_ENV`); when the day variable is set without the marker, fail the session with a one-line message. A test for each of the three states; a mutant that drops the marker check.

### [Issue 5] [`codebase` N9-3] - Severity: Nit
*   **Scope:** `tests/policy_mutants.py:1124-1136`; `tests/test_policy_guard.py:4223-4228`.
*   **Description:** With `--day <today>` the probe mutant (clock hook dropped) survives, the runner prints a false "BAD ... did not reach the child pytest" and exits 1. `--day` with no value raises `IndexError`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** The probe always runs with the canary day, whichever day the main run uses; `--day` without a valid `YYYY-MM-DD` value exits 2 with one plain line. Tests for both (run the runner's argument parser).

### [Issue 6] [evidence: 5 of 8 new tests pass on old code; `design` review on plants] - Severity: Minor
*   **Scope:** the CI-step plant, the changelog-reminder plant, the two decision-day tests, `test_the_day_the_tool_sees_is_the_fixed_day_the_run_was_given` (see `RESULTS.md` fail-before); NOTES section C.
*   **Description:** Round 8 Issue 7 asked one line per test: fails on old code, or a control with a reason, or the killing mutant. The builder's table covers them, but the plant tests check helpers defined in the same file, so a regression of the real `ci.yml` or CHANGELOG is caught only by the control tests and no mutant can reach them (the runner's temp tree has no `ci.yml`). The fixed-day-seen test is the Issue 1 consumer problem.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Reuse and extend: no new mechanism, a tighter line per test.
*   ***Proposed Edit:*** In NOTES section C, for each of the five: the exact command that shows it can fail (a planted wrong input run by hand, output saved) or the mutant; for the two helper-plant tests also name the real-file control test that reads the real `ci.yml` / CHANGELOG and show it failing on a planted bad copy. The fixed-day-seen test is covered by Issue 1's probe consumer. A tool check reads the section and fails on a test id without a line (same as Q8b Issue 13).

### [Issue 7] [`codebase` N9-4] - Severity: Nit
*   **Scope:** `tests/policy_mutants.py` mutant "B9 the decision day of the names and claims moves"; `tests/test_policy_guard.py:~4262-4270`.
*   **Description:** The mutant is killed by `assert pp.DECIDED == date(2026, 11, 11)`, a copy of the constant; it does not show the kinds' decided values stay independent. Held today by two other pins; partial.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** A test that sets `pp.DECIDED` to another day and asserts every kind's `decided` is unchanged; the mutant is killed by it.

### [Issue 8] [`codebase` N9-5] - Severity: Nit
*   **Scope:** `tests/test_policy_changelog.py:31-41`; `tests/test_policy_docs.py` `_date_guard_sentence_problem` (string `"7 of them from 2026-12-12"`, `CHANGELOG.md:298`); `tests/test_policy_guard.py:4191-4195`.
*   **Description:** The CHANGELOG test flags only `review by \d{4}-\d{2}-\d{2}`; "review date 2026-12-11" or "from 2026-12-12" for the names list passes. The docstring test accepts any date that is `decided` or `review_by` of any entry, so a stale docstring date that belongs to another entry passes. Evidence confirms ISO day text still at `docs/declared-permissions.md:21, :61` (generated), `CHANGELOG.md:298` (kinds days, checked by an existing test) and in tests as data.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** The tool docstring holds no literal date (the stray-day mutant keeps working). The CHANGELOG test flags any date in the entry other than the kinds-list days that the existing kinds test already checks (those days are read from the list, not written in the test). Rows: "review date 2026-12-11", "from 2026-12-12" for the names list, a stale docstring date of another entry. Mutants for each.

### [Issue 9] [`design` B9-5, `codebase` evidence-document slips] - Severity: Nit
*   **Scope:** `handover/evidence/Q8c-1/b9/NOTES.md` ("0 weak of 121", "B9 x6" lists 7), `GATES.md` (headed "final head", gitleaks line names `8c8b6338`, one full pytest with 1 failure and no repeat), `CHANGELOG.md:240` (one overlong line).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Counts become 122 and "B9 x7" (recomputed after this batch); GATES is rewritten for the new final head with the gitleaks line and ONE full pytest on that head; CHANGELOG:240 wrapped. Say in NOTES that the batch-9 full run had a set-up slip and the evidence runner's run (10892 passed) is the independent one.

## Handoff counts
Accepted (PROPOSE FIX): 9 (Issues 1-9; two Majors). Contested: 0. Escalated: 0. Declined: 0. Remaining unaddressed: none, except the IMPOSSIBLE-NOW Vault engine run (Issue 8 of round 8: needs a CI run with `HADAVIN_REQUIRE_VAULT_ENGINE=1` before 2026-12-11; the ledger row stays IMPOSSIBLE-NOW and the page stays honest). Severity unchanged from the reviews. Because the path is security with no cap: one batch-10 builder fixes Issues 1-9 and reports once; then an independent evidence run (full suite, `policy_mutants` on three days with the red-baseline reading, `--check`, the fail-before and per-test line check) and two `egm:*` reviewers read the new head.

## Who fixes it
One batch-10 builder on a new branch `core/q8c1-b10` from `c6bd7108`, plain push to `wip/cloud-q8c1-b10`. Files: `tools/policy_page.py`, `tests/policy_mutants.py`, `tests/test_policy_guard.py`, `tests/test_policy_changelog.py`, `tests/test_policy_docs.py`, `tests/test_lockin_guard.py` only if the `TODAY` source must change there (stated), `tests/fixtures/policy_sources_2026-11-11.txt`, `CHANGELOG.md`, `handover/evidence/Q8c-1/b9` notes (or a new `b10` folder), `docs/declared-permissions.md` only by regeneration. `tools/mutation_runner.py` only if a change there is unavoidable (stated, with the reason). No grant added or widened; nothing under `src/`.
