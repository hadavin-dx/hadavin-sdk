Status: resolved

# Goldfish Annotated Review Report (round 18)

**Target:** P3a-2 batch 7, branch `wip/cloud-p3a2-b7`, head `aac26d60` (previous reviewed head `140a1268`). Files: `handover/reviews/P3a-2/p3a2b7-design-r18.md` (0 Blocker, 0 Major, 3 Minor, 3 Nit), `p3a2b7-codebase-r18.md` (0 Blocker, 0 Major, 2 Minor, 3 Nit); full files.
**Path:** SECURITY / least privilege (no round cap). Automated mode, recommended option for every item, nothing yielded.
**Evidence read:** `handover/evidence/P3a-2/aac26d60/RESULTS.md` (independent runner; written afterwards from the saved logs, nothing re-run). Facts: full pytest 0 failed, 12439 passed, 4 skipped, 29 deselected, exit 0; migrate mutants 129, 88, 98, 97 all killed; number mutants 40 of 40; stage mutants 37 of 37; fail-before on `140a1268`: 7 failed, 25 passed on the 32 new test ids. Not run (impossible now): PostgreSQL 17 tests (3 skipped by name), Python 3.12, semgrep, zizmor, trivy, pip-audit. The known timing test was deselected by the marker filter (result unknown; not to be touched).
**Reviewer result:** no Blocker, no Major. No readable secret, no regression against main, no guard bypassed. The code change is small and correct as read; the defects are one channel (`__context__`) that the claim "the SDK's words are not kept" does not cover, one narrow catch, two code paths with no mutant, and wording. Reviewer severities are unchanged. No finding is contested; each is checkable in the snapshot.

## Prioritized Findings & AI Suggestions

### Group 1 [design D1 and codebase C1] - Severity: Minor
*   **Affected Scope:** `src/hadavin_sdk/store/auth_aws.py` (`_refused`, raised `from None`), `store/migrate.py:1268-1270`, `store/postgres.py:148-151`; `tests/test_migration_verify.py:1561`; CHANGELOG line 13 and the docstrings ("never the SDK's own words").
*   **Discrepancy Description:** `raise ... from None` hides the SDK exception from the printed traceback only. It stays on `SignInError.__context__` (and `ConfigError(...) from e` in migrate.py holds the SignInError, so the SDK error is two hops away). A cloud error message can carry an account id or role ARN; a log handler that walks `__context__` and ignores `__suppress_context__` records the text the batch says it hides. The test asserts only `__cause__ is None`, which is also true with no `from` at all, so `from None` changed to `from exc` keeps it green; V122 changes the message only.
*   **Rationale:** Same class as r17 group 3: a claim stronger than the proof (a channel left open, and a test that cannot fail on the change that matters).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Close the channel at the choke point instead of rewording: build the error outside the `except` block (hold a variable, raise after) so `__context__` is empty on both `SignInError` and the wrapping `ConfigError`. Tests: `__cause__ is None`, `__context__ is None`, `__suppress_context__` as designed, and the new words absent from `"".join(traceback.format_exception(...))` (made-up words built from parts); a mutant that restores `from exc` and a mutant that raises inside the `except` block, each killed by a test that fails for that reason.
*   ***Proposed Edit:***
    *   Location: `store/auth_aws.py`, `store/postgres.py`, `store/migrate.py`, `tests/test_migration_verify.py`, `tests/migrate_mutants.py`, CHANGELOG.
    *   Change: as above; where a channel stays open, say "not printed" and not "never kept".

### Group 2 [design D2] - Severity: Minor
*   **Affected Scope:** `store/auth_aws.py:29`, `:35`; CHANGELOG line 13 ("a plain refusal with exit 2"); the two sign-in tests.
*   **Discrepancy Description:** The conversion catches only `BotoCoreError` and `ClientError`. Any other exception from `boto3.client` or `generate_db_auth_token` (`Boto3Error`, `OSError`, a JSON error from a credential file) escapes raw, exit 3, with the SDK text printed: the r17 group 3(b) defect for another type. Tests use only the two named classes.
*   **Rationale:** The class is "any failure of the sign-in step", not two library types.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Catch `Exception` in the two spots (the converted error names only the class); keep `KeyboardInterrupt` and `SystemExit` unconverted. Test with a plain `RuntimeError` and an `OSError` carrying made-up words; mutant narrowing the catch back to two types.
*   ***Proposed Edit:***
    *   Location: `store/auth_aws.py`, tests, mutants.
    *   Change: as above.

### Group 3 [design D3 and codebase C2] - Severity: Minor
*   **Affected Scope:** `store/postgres.py:143-151` (the `except (KeyError, ValueError)` guard), `store/migrate.py:1268` (`except SignInError`); `tests/migrate_mutants.py:4117-4137`; `tests/test_migration_verify.py:1530`, `:1564-1577`; `tests/test_migration_verify_pg.py:653`.
*   **Discrepancy Description:** Two of the four group-3 src changes have no mutant that removes them: the DSN guard and `except SignInError` (probably killed only indirectly). The DSN cases cover a missing host and a missing user (both KeyError); a non-numeric port (`port=abc`) and a multi-host DSN (`port=5432,5433`) are not tested and the test pins `match="KeyError"` only. Both docstrings name V122 ("the SDK error is not converted") while V122 is "prints the SDK's own words".
*   **Rationale:** The batch's own rule is a mutant per fix with a killer for the named reason.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One mutant per site, add `port=abc` and the multi-host DSN to the parametrised cases (match the exception word they really raise), correct both docstrings.
*   ***Proposed Edit:***
    *   Location: files named.
    *   Change: as above.

### Group 4 [design D4, D5 and codebase C3, C4] - Severity: Nit
*   **Affected Scope:** `store/postgres.py:148-151`, `:161-166`; `store/migrate.py:1268-1271`; `tests/test_migration_verify_pg.py:675`; CHANGELOG ("a close which fails as well does not hide the first error").
*   **Discrepancy Description:** The DSN-guard text ends `... in the address (KeyError)` with no full stop, then migrate.py appends " Nothing was started."; it names the Python exception, meaningless to an operator, and a test pins `match="KeyError"`. `suppress(psycopg.Error)` around `conn.close()` is narrower than the claim: an `OSError` or `BrokenPipeError` from `close()` still hides the first error.
*   **Rationale:** Wording for people (one word one meaning) and a claim wider than the code.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Say "host", "user" or "port" by name and end with a full stop; use `suppress(Exception)` for the close and test it with an `OSError`; fix the matching tests.
*   ***Proposed Edit:***
    *   Location: files named.
    *   Change: as above.

### Group 5 [codebase C5 and runtime-path note] - Severity: Nit
*   **Affected Scope:** CHANGELOG line 14 ("tries no connection"); `tests/test_migration_verify.py:1546-1549`, `:1567-1577`; `store/postgres.py:207-225` (`build()` calls `password_source` first).
*   **Discrepancy Description:** The `no_connection` stub proves "no connection is tried" only in the sign-in unit test, not in the DSN-guard test or the migrate-level test. Separately, a missing region at runtime build is now a `SignInError` (ConfigError) and not a raw botocore error, and is not mapped to StoreUnavailable (deliberate); the CHANGELOG does not say the runtime build path changed.
*   **Rationale:** True for the code as read; the proof is thinner than the sentence, and a changed path is undocumented.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Reuse the stub in the DSN-guard and migrate-level tests; add one CHANGELOG sentence on the runtime build path.
*   ***Proposed Edit:***
    *   Location: tests, CHANGELOG.
    *   Change: as above.

### Group 6 [evidence] - Severity: Minor
*   **Affected Scope:** `handover/evidence/P3a-2/aac26d60/RESULTS.md`, `handover/evidence/P3a-2/b7/passes-on-old-code.md`, builder notes.
*   **Discrepancy Description:** (a) The timing test was deselected by the marker filter, so its result at this head is unknown. (b) The 25 tests that pass on old code were not compared line by line with the reasons file. (c) The builder's fail-before denominators (7 failed and 37 passed over four changed files) differ from the runner's (7 failed, 25 passed over the 32 new ids). (d) The builder's claim "1 failed" in the full suite was an environment failure (dblink on the fixed socket) that did not repeat on an own server. (e) No builder notes file exists for batch 7.
*   **Rationale:** Every "passes on old code" test needs a written reason; counts must be measured, not remembered.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The batch-8 builder writes the per-test reason table with measured numbers on `aac26d60`, states the denominators it uses, and writes a notes file. The timing test stays untouched; its result is listed as not run, never as passed.
*   ***Proposed Edit:***
    *   Location: batch-8 notes under `handover/evidence/P3a-2/`.
    *   Change: as above.

### Group 7 [owner item O8 `q-p3a2-o8-schema-owner`] - Severity: Major (carried)
*   **Affected Scope:** `store/migrate.py` (schema owner check stays OFF, "NOT refused", CHANGELOG line 11).
*   **Discrepancy Description:** The decision on turning the check on is the owner's; nothing in the delta marks it done.
*   **Rationale:** Needs the owner's decision, outside every file a reviewer could read.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Do not build, do not report closed.
*   ***Proposed Edit:***
    *   Location: none.
    *   Change: none. The question stays in `questions-for-lead.md`.

## Handoff

*   Accepted fixes (PROPOSE FIX): 6 groups (3 Minor groups 1, 2, 3, plus Minor evidence group 6; Nit groups 4 and 5), covering all 5 Minor and 6 Nit items of the reviewers (D1 to D6, C1 to C5; D6 is "not a defect" and needs no change).
*   Contested: 0.
*   Escalated: 1 (group 7, O8, OWNER-ONLY).
*   Declined: 0.
*   Remaining unaddressed: all of the above until batch 8 lands. Gate state at `aac26d60`: green on every command that ran; PostgreSQL 17, Python 3.12 and the CI-only scanners are IMPOSSIBLE-NOW; the timing test result is unknown. No Blocker or Major open, so this is the last round only if a fresh pass after batch 8 finds nothing real.

## Who fixes it

One batch-8 builder on a new branch `core/p3a2-b8` from `aac26d60`, pushing to `wip/cloud-p3a2-b8`. Order: group 1, 2, 3, 4, 5, 6. Method per bug: name the class, fix at the shared choke point, grep siblings, show each new test failing on `aac26d60`, one mutant per fix with a killer that fails for the named reason, final-head full suite and all four mutant sets and the number and stage mutants, one written reason per test that passes on old code. O8 stays OFF and OWNER-ONLY. The builder does not touch `test_the_timing_harness_flags_a_quadratic_stand_in`.
