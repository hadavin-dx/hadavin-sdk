Status: resolved

# Goldfish Annotated Review Report (Q8c-1, round 7 second pass)

**Target:** branch `wip/cloud-q8c1-b7`, head `ad588599` (delta `d598d967..ad588599`). SECURITY path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8c1b7-design-r7.md` (0 Blocker, 0 Major, 1 Minor, 2 Nit) and `q8c1b7-codebase-r7.md` (0 Blocker, 0 Major, 3 Nit). Independent evidence: `handover/evidence/Q8c-1/ad588599/RESULTS.md`: ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 37/37; policy mutants 108/108; full pytest 10878 passed, 13 skipped (12 are the Vault engine tests); 13 tests fail on the old tree with the clock faked to 2026-12-12 and all pass on head.

Both reviewers found the claimed fixes of the earlier round true on reading, no grant added or broadened, the clock seam not reachable from the command line, and the engine-test gate honest and enforced in CI.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` F1] - Severity: Minor
*   **Scope:** `tools/policy_page.py:850` (`today = datetime.now(UTC).date() if today is None else today`); `tests/test_policy_guard.py` (every call passes `today=`); `ci.yml` (no `--check` step).
*   **Description:** No test uses the tool's own default clock. A change that fixes the default to a date passes all 346 tests and 108 mutants, and the command line then stays green after 2026-12-11. The date guard is the only forced reminder that 13 unverified names and claims must be re-read.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Security path; the one forced reminder must be proven for the command people actually run.
*   ***Proposed Edit:*** (a) One test that patches `pp.datetime` with a fixed subclass (as the evidence `fakeclock.py` does), calls `pp.main(["--check"])` with no `today`, expects 1 on 2026-12-12 and 0 on 2026-12-11; (b) a mutant on line 850 (fixed default date) that this test kills, with its own message; (c) add the CI step `python tools/policy_page.py --check` beside the other policy steps if `ci.yml` allows it, and extend the YAML test that pins the steps.

### [Issue 2] [`design` F2, `codebase` N2] - Severity: Nit (one class)
*   **Scope:** `tests/policy_mutants.py:923-930` (B7 "check command ignores the day it is given"); `tests/test_policy_guard.py:3891-3899`; `ci.yml:96-97`.
*   **Description:** The mutant depends on the real clock and on a short `expect` (`== 1`). It is killed at the write assertion, not its own check assertion. From 2026-12-12 it fails earlier at `:3891` with `assert 1 == 0`, which does not contain the expect, so the blocking CI step `python tests/policy_mutants.py` would report BAD on top of the intended overdue signal. 40 of 108 mutants have a weak first-line check.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A mutant run that turns red for the wrong reason on a known date hides the real signal; the class (mutant outcome depends on the real date or on a generic assertion text) is fixed at the choke point.
*   ***Proposed Edit:*** Give each assertion its own message; make write and check mutants separable (two mutants, each anchored on its own assertion); run the killers with `today=` given so no mutant result depends on the real date; scan all 108 `expect` fragments for strings of 6 characters or fewer or that match a bare `assert a == b` and list the weak ones in the PR notes, then strengthen those that guard grants, never lines or the date guard.

### [Issue 3] [`codebase` N1] - Severity: Nit
*   **Scope:** `tests/test_policy_guard.py:38, :50-67, :164, :173`; `tools/policy_page.py:735`.
*   **Description:** `DECIDED = pp.DECIDED` also sets the `decided` of the 16 `PENDING_KINDS`. Moving the tool's date to renew names and claims silently renews the 16 kinds, and the 92-day cap compares `review_by` with `decided`, so it can be dodged. `test_policy_changelog.py` pins `review_by` and counts, not `decided`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Keep `today=pp.DECIDED` in the plant tests; `PENDING_KINDS` gets its own literal `date(2026, 11, 11)` again; pin the 16 `decided` values in `test_policy_changelog.py`; add a mutant that moves the tool's `DECIDED` and expect the kinds test to stay green only through its own literal.

### [Issue 4] [`codebase` N3] - Severity: Nit
*   **Scope:** `tools/policy_page.py:20-21`; `CHANGELOG.md:299-301`.
*   **Description:** "2026-12-12" is hard-coded in the docstring and CHANGELOG; false after a renewal.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Say "from the day after the earliest `review_by`"; add a one-line test that the docstring does not contain a date literal that is not in the dated lists.

### [Issue 5] [`design` F3] - Severity: Nit
*   **Scope:** `tools/policy_page.py:782-805`; CHANGELOG.
*   **Description:** The guard is a reminder, not a lock: a new `decided` and a `review_by` up to 92 days later pass without an evidence run.
*   ***AI Suggestion:*** DECLINE (design as stated) with a wording fix
*   ***Justification:*** This is the stated design ("decide again") and was recorded in r4 N2; making it a lock would need an evidence artifact tied to the date, which is a ticket change, not a defect.
*   ***Proposed Edit:*** One CHANGELOG sentence: "the date guard is a reminder, not a check that anyone re-read the names; it stops the page and the tests, and a person must renew it with a dated decision." Recorded in the owner question list as a design note, no new question.

### [Issue 6] [`design` N1 of the previous pass, evidence] - Severity: Minor
*   **Description:** The fail-before table for `d598d967` and the ticket's "must fail on main" proofs at this head are not in the evidence; the evidence shows only that the new tests fail on the old tree. Also, of the tests that gained `today=DECIDED`, those using `any(...)` pass on the old tree even with the faked clock (harmless but not needed); the `startswith` test passes on the old tool by design (it guards a mutant).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** The batch 8 builder writes in the PR notes one line per new or changed test: fails on the old head (command and output), or control with reason, or the killing mutant; and runs the ticket's must-fail-on-main list once with output. The independent evidence runner repeats it on the final head.

### [Issue 7] [`evidence` Vault engine tests] - Severity: Major (gate, IMPOSSIBLE-NOW)
*   **Description:** The 12 Vault engine tests have never run here: no Vault server and no network to fetch one (OpenBao). The negative tests (the never-list requests are refused, the admin control is not) and the policy-widening plants are written from documentation, never seen to pass.
*   ***AI Suggestion:*** ESCALATE (the next step needs a CI run, which needs the owner's push to a CI-enabled branch; the safe default is no merge until CI is green)
*   ***Justification:*** Impossible now, needs a third party (CI). The ledger row stays OPEN with: next step = one CI run on `wip/cloud-q8c1-b7` with `HADAVIN_REQUIRE_VAULT_ENGINE=1` before 2026-12-11; after it, edit `ENGINE_RUN` and the pinned page test by hand (a reminder, since forgetting understates what was tested).

## Handoff counts
Accepted (PROPOSE FIX): 5 (Issues 1, 2, 3, 4, 6) plus the wording fix of Issue 5. Declined: 1 (Issue 5 design, wording accepted). Escalated: 1 (Issue 7, impossible now). Contested: 0. Because the path is security with no cap, a batch-8 builder fixes Issues 1-6, then a fresh evidence run and two `egm:*` reviewers read the new head. The CI run for Issue 7 stays the merge gate and is not closed.
