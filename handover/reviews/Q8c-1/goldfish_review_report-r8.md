Status: resolved

# Goldfish Annotated Review Report (Q8c-1, round 8)

**Target:** branch `wip/cloud-q8c1-b8`, head `208a47d5694179a1d2deddbe211cfa3af001ec4d` (delta `ad588599..208a47d5`). SECURITY path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8c1b8-design-r8.md` (0 Blocker, 0 Major, 3 Nit) and `q8c1b8-codebase-r8.md` (0 Blocker, 0 Major, 3 Nit). Previous round: `goldfish_review_report-r7b.md`. Independent evidence: `handover/evidence/Q8c-1/208a47d5/RESULTS.md`.

**Evidence status (first).** ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 37 of 37; policy mutants 111 of 111 on the real clock and on the faked days 2026-12-11 and 2026-12-12 (identical lines). Full pytest exit 0: 10885 passed, 13 skipped, 0 failed (the runner's first full run lacked the database setting and gave 469 skips; the rerun is the reported one; that was the runner's slip, recorded). `policy_page.py --check`: exit 0 on the real clock and on 2026-12-11, exit 1 with 13 overdue lines on 2026-12-12. Fail-before on `ad588599`: 3 failed, 350 passed (the CI-step test, the CHANGELOG reminder test, the docstring-date test). The head's tests on main: 239 failed (the new policy rows do not exist on main, as expected).

**Not run:** the 12 Vault engine tests (no Vault server, no network: IMPOSSIBLE-NOW, Issue 8), perf tests, the timing test, the Python 3.12 job. Both reviewers found the claimed round 7b fixes present, no grant added or widened, the CI step blocking, and the CHANGELOG sentences matching the code. The six review Nits below are all on tests, documents and dates, none on a grant.

## Prioritized Findings & AI Suggestion

### [Issue 1] [`design` N-1, `codebase` N8-1] - Severity: Nit (one finding)
*   **Scope:** `tools/policy_page.py:1719` ("the review date 2026-12-11") and `:1759` ("review by 2026-12-11"); `docs/declared-permissions.md:21, :61`; `CHANGELOG.md:240`; `tests/test_policy_docs.py:117`; the new docstring test reads only `pp.__doc__`.
*   **Description:** The date is a literal in the page template, two docs lines and the CHANGELOG. After a renewal `--write` regenerates the same strings and `--check` stays green, so the published page states a date that is no longer the review date.
*   ***AI Suggestion:*** PROPOSE FIX (the stronger option)
*   ***Justification:*** The date guard exists to force a re-read; a page that keeps naming the old date after a renewal undermines the reminder it belongs to. Class: a date written as text in more than one place.
*   ***Proposed Edit:*** Build both page sentences from `min(p.review_by)` of the dated lists; docs lines carry the date through the generated page or a single marker the tool fills; CHANGELOG states "the earliest review date" without a literal, or the stray-date test reads page text, docs and CHANGELOG with the allowed set taken from the lists. Add a test that plants a renewed `review_by` and expects the page text to change; a mutant that fixes the date in the template.

### [Issue 2] [`design` N-2 and evidence E1] - Severity: Nit
*   **Scope:** no mutant for the CI-step test, the CHANGELOG-wording test or the docstring-date test; the policy mutant runner prints "first-line check is weak for 40 of 111 mutants" and no list; r7b Issue 2 asked for the list in the PR notes and it is in no artifact.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The weak-expect scan was accepted last round; no artifact shows it was done; a list that cannot be read cannot be acted on. Mutants for the new pins are cheap.
*   ***Proposed Edit:*** The runner prints each weak mutant on its own line (name, expect text, killer); the builder commits that list in the PR notes; strengthens every one that guards a grant, a never-line or the date guard; adds one mutant per new pin (CI step removed or moved, CHANGELOG reminder sentence removed, docstring date added) or states in the notes why a pin is covered otherwise.

### [Issue 3] [`design` N-3] - Severity: Nit
*   **Scope:** mutant B8 (kinds) moves the test's own `KINDS_DECIDED` constant, not the tool's `DECIDED`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The mutant shows the literal is pinned, not that the 16 kinds are independent of `pp.DECIDED`.
*   ***Proposed Edit:*** Add a mutant on `tools/policy_page.py:737` that moves `DECIDED` and expects the kinds test to stay green only through its own literal.

### [Issue 4] [`codebase` N8-2] - Severity: Nit
*   **Scope:** `tests/policy_mutants.py:10-14, :963-964` (`_killers_using_same`); the second `same()` call in the Transit wildcard bound test (`:1311-1317`), the never-line reason test (`:1361-1365`) and the D7 platform/no_wire/never-type test.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** D1, D3, D7 still count as weak though their expect now equals the first call's `what`; the second calls have a `what` no mutant names.
*   ***Proposed Edit:*** `_killers_using_same` ignores killers whose expect equals a `what` string; mutants for each second-call `what`, or reword the docstring so it does not claim more.

### [Issue 5] [`codebase` N8-3] - Severity: Nit
*   **Scope:** `tests/test_policy_changelog.py:29-38` duplicates `tests/test_policy_guard.py:4132-4136`; only the guard copy is mutant-pinned (`:947-954`); the 92-day assertion cannot be reached from the mutant runner; the changelog test docstring says "changelog states the days" but reads no CHANGELOG.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Keep one copy of the "16 decided equal the literal, count 16" pin; move the 92-day assertion into the guard file under a mutant; fix the changelog test docstring (or make it read the CHANGELOG sentence it names).

### [Issue 6] [`evidence` E2] - Severity: Nit
*   **Scope:** the fake-clock shim's confirmation line is not visible in the mutant runner's child pytest (the runner captures stderr); the evidence proved the fixed day reaches pytest and `--check` only in direct runs.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** "No mutant result changes with the date" rests on a fake day that was shown to reach the child process only indirectly.
*   ***Proposed Edit:*** One test or runner self-check that the fixed day reaches the child (the killer for one date-dependent mutant records the day it saw, or a mutant that fails only on 2026-12-12 and is killed when the fixed day is 2026-12-12). The next evidence runner repeats the faked days with that proof visible.

### [Issue 7] [`evidence` E3 and E4, r7b Issue 6, ledger `Q8c1-b8-issue6`] - Severity: Minor
*   **Scope:** ticket section 6.4 is older than this PR (ten kinds, `docs/least-privilege-policies.md`), so the ticket's literal F1 to F3 messages were not run; the per-test fail-before classification asked for in r7b Issue 6 is still open (the evidence gives 3 old-tree failures only).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Work that is worth doing is done now: the classification is the proof that new tests can fail; it stays in this batch.
*   ***Proposed Edit:*** The builder writes in the PR notes one line per new or changed test since `d598d967`: fails on the old head (command and output), or control with its reason, or the killing mutant. One line per ticket must-fail-on-main item mapping it to the test that covers it (state where the ticket is out of date, and what replaces the item). The next evidence runner repeats it on the final head.

### [Issue 8] [`evidence` Vault engine tests] - Severity: Major (gate, IMPOSSIBLE-NOW)
*   **Description:** The 12 Vault engine tests have never run here (no Vault server, no network to fetch one). The negative tests and the policy-widening plants are written from documentation, never seen to pass.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Needs a third party (a CI run). Safe default: no merge until CI is green. The ledger row stays OPEN: next step = one CI run on the branch with `HADAVIN_REQUIRE_VAULT_ENGINE=1` before 2026-12-11; after it, edit `ENGINE_RUN` and the pinned page test by hand.

## Handoff counts
Accepted (PROPOSE FIX): 7 (Issues 1 to 7). Escalated: 1 (Issue 8, impossible now). Declined: 0. Contested: 0. Remaining unaddressed: none. Because the path is security with no cap, one batch-9 builder fixes Issues 1 to 7, then a fresh evidence run (also the faked days with the Issue 6 proof, the weak list and the per-test classification) and two `egm:*` reviewers read the new head. All six review Nits were on tests, documents and dates; no finding touches a grant.

## Who fixes it
One batch-9 builder on `wip/cloud-q8c1-b8` (new branch from `208a47d5`; plain push to a new `wip/cloud-q8c1-b9`). Files: `tools/policy_page.py`, `tests/policy_mutants.py`, `tests/test_policy_guard.py`, `tests/test_policy_changelog.py`, `tests/test_policy_docs.py`, `docs/declared-permissions.md`, `CHANGELOG.md`, `ci.yml` unchanged. No other package edits these files.
