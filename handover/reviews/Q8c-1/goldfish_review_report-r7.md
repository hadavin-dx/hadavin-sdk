Status: resolved

# Goldfish Annotated Review Report (Q8c-1, round 7)

**Target:** branch `wip/cloud-q8c1-b6`, head `d598d967`, snapshot `/home/user/build/snap/q8c1b6-d598d967`. Least-privilege page and guard path (security path, no round cap). No person was available: recommended option for every item. Reviews: `/home/user/build/reports/q8c1b6-design-r7.md` (0 Blocker, 0 Major, 4 Nit; saved abridged by the lead) and `q8c1b6-codebase-r7.md` (0 Blocker, 0 Major, 4 Nit); both read-only. Evidence (independent, head confirmed, tree clean): `handover/evidence/Q8c-1/d598d967/RESULTS.md`: full pytest 10876 passed, 13 skipped (12 Vault engine, 1 Stubber), 28 deselected; `policy_mutants` 103 of 103 good (exit code not captured; log says first-line check is weak for 41 of 103); ruff, format, bandit, scan_repo, `stage_mutants` 37 of 37, `policy_page --check`, gitleaks all exit 0. Fail-before: `5015c990` 18 failed, `origin/main` 233 failed, head 352 passed. The timing test failed 6 of 6 alone on head and on main (known flake, not in the diff). Round 6 Issues 1-7 were read as fixed by both reviewers and the evidence probes a1-g2 all exit 1 with the intended messages on head.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` N1] - Severity: Nit
*   **Affected Scope:** `handover/evidence/Q8c-1/d598d967/RESULTS.md` (fail-before notes); `{path_prefix}` guard test.
*   **Discrepancy Description:** The one-line-per-test table (why a test passes on old code, which mutant proves the guard live) was not in the snapshot.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The evidence now exists (lists `passes-on-old-5015c990.txt`, `passes-on-main.txt`) but the per-test reason and mutant name are still not written. Cheap, and round 6 Issue 7 asked for it.
*   ***Proposed Edit:*** Fix builder adds the table: for each test in `passes-on-old-5015c990.txt` that belongs to the delta, one line (control for an earlier class, or a plant against supplied data) and the mutant that kills it; the `{path_prefix}` guard test names its mutant, or gets one.

### [Issue 2] [`design` N2] - Severity: Nit
*   **Affected Scope:** `tools/policy_page.py` (builder-read rule, delta 1661-1665); `CHANGELOG.md` (delta 19-22).
*   **Discrepancy Description:** The rule "an entry naming a builder-only source and having a claim needs a builder-read claim" applies to any claim, so a new nobody-read claim on such an entry makes `--check` demand a builder-read one (cheapest silence: a false mark). CHANGELOG says moving a mark between two claims of one entry is "not caught by code"; pytest catches it for R17 only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Wording overclaims; the over-demand is in the safe direction (it asks for more review), so a wording fix is enough now.
*   ***Proposed Edit:*** CHANGELOG: "not caught by `--check`; caught for R17 only by the pinned test". Tool docstring: say the rule applies to every claim of such an entry, and that the builder-read mark must name the claim the builder read.

### [Issue 3] [`design` N3] - Severity: Nit
*   **Affected Scope:** sources-file head ("6 different texts", "the other 7", "9 ids").
*   **Discrepancy Description:** Counts in comments; test pins 7 and 9 but not 6.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One assertion, cheap.
*   ***Proposed Edit:*** Pin the 6 in the same test that pins 7 and 9, or drop the numbers from the head.

### [Issue 4] [`design` N4, `codebase` N2] - Severity: Nit
*   **Affected Scope:** `tools/policy_page.py:1444-1463`, `main` `:1842-1853`, `data_problems` `:835-858`; `tests/test_policy_guard.py:38` (DECIDED duplicate); about 20 tests that call `data_problems(root)` or `_check` without `today`.
*   **Discrepancy Description:** From 2026-12-12 `--write` and CI `--check` fail and many tests go red for a reason unrelated to their purpose; CHANGELOG does not say `--write` stops too; the decided date is written twice.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The ticket intends the red signal on that date (renew the dates), so the signal stays. The diagnosability cost is real and the fix is cheap: plant tests pass a fixed `today`, one DECIDED from the tool, one CHANGELOG sentence.
*   ***Proposed Edit:*** Plant tests pass `today=DECIDED` (a test that needs the real clock keeps it). Guard test imports DECIDED from the tool. CHANGELOG: "From 2026-12-12 `--write` and `--check` stop until the dates are renewed." Keep one test per dated list that proves the red signal on the date.

### [Issue 5] [`codebase` N1] - Severity: Nit
*   **Affected Scope:** `tools/policy_page.py:23-26` docstring.
*   **Discrepancy Description:** Says "Three checks ... live only in tests/test_policy_guard.py"; the tests-only set is larger (sender and paging-query checks, per-module import lists, Vault-client-only-in-declared-modules rule, Kubernetes never-list equality, engine tests, `PENDING_KINDS`). Docstring also omits the builder-read-mark rule and "decided in the future" rule on the `--check` side.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Overstated precision on what `--check` covers is the round 6 Issue 3 class.
*   ***Proposed Edit:*** Name the tests-only checks (call shape, import lists, sender and paging rules, Kubernetes equalities, placeholder check, engine tests, `PENDING_KINDS`) or drop the number; add the two omitted `--check` rules.

### [Issue 6] [`codebase` N3] - Severity: Nit (mutant strength)
*   **Affected Scope:** `tests/policy_mutants.py:684-689` (B5 reason exact text), killer `tests/test_policy_guard.py:3498-3514`.
*   **Discrepancy Description:** Killed at the first `same(_problems_of(_policies()), [])` because the real short key `reason:a write verb: this source only reads` is a prefix of the long `create` reason key; the planted cases at 3502-3514 are not what discriminates it.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Without it the mutant would survive if the real data changed.
*   ***Proposed Edit:*** Add a planted case whose reason has a unique prefix with no collision in real data, and an `expect` fragment only that case produces.

### [Issue 7] [`codebase` N4] - Severity: Nit
*   **Affected Scope:** `tools/policy_page.py:668` (`removeprefix`).
*   **Discrepancy Description:** A literal invisible U+FEFF is in the source; the mutant `old` uses the escape; an editor can strip it and the BOM mutant would then fail to apply.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One-line mechanical change, same value.
*   ***Proposed Edit:*** Write the escape sequence for U+FEFF in the tool; the mutant `old` already uses it.

### [Issue 8] [`evidence`, rounds 4-6 Issue 8] Vault engine tests never run - Severity: Major (process gate)
*   ***AI Suggestion:*** unchanged: IMPOSSIBLE-NOW (no server binary here and none may be fetched). With `HADAVIN_REQUIRE_VAULT_ENGINE=1`: 8 passed, 12 errors; without it 12 skipped. Merge gate: one CI run on the final head with 12 passed and 0 skipped; then set `ENGINE_RUN` and edit the pinned page test in the same commit. Ledger row stays OPEN; the page keeps saying "have not run yet".

### Items recorded, no change (evidence)
*   Evidence probe d0 (BOM at file start) exits 0 on head: the single reader strips one BOM by design; BOMs elsewhere are refused (d1-d5, exit 1). Probes a1-g2 behave as intended. `policy_mutants` exit code was not captured (log ends "103 of 103 good; problems: []"); the fix builder or the next evidence runner records the exit code. Not run: perf (ticket names none), CodeQL, SonarCloud, CodeRabbit, Python 3.12 job.

## Handoff counts
Accepted (PROPOSE FIX): 7 (Issues 1-7, all Nits). Contested: 0. Escalated: 0. Declined: 0. Open gate (not code): Issue 8. No Blocker or Major in this round. Per the cap rule for security paths, the Nits are fixed in one small push; a fresh review of that push is needed only if the delta changes behaviour (Issue 4 changes test `today` handling and the tool's `DECIDED` export: a light check by the next evidence runner is enough). Ledger: Q8c-1 has no OPEN Blocker or Major except Issue 8 (IMPOSSIBLE-NOW).
