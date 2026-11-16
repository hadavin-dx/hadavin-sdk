Status: resolved

# Goldfish Annotated Review Report (round 17)

**Target:** P3a-2 batch 6, branch `wip/cloud-p3a2-b6`, tip 140a1268 (`handover/reviews/P3a-2/p3a2b6-design-r16.md`, `p3a2b6-codebase-r16.md`; full file)
**Path:** SECURITY / least privilege (no round cap). Automated mode, recommended option for every item, nothing yielded.
**Evidence read:** `handover/evidence/P3a-2/140a1268/RESULTS.md` (independent evidence runner). Facts used: full pytest 1 failed and 12408 passed; the one failure (`tests/demo_askdata/test_validate_harm.py:179`) is the runner's own Postgres socket path, an environment cause, not a finding; migrate mutants 121, 88, 98 and 97 all killed; number mutants 40 of 40; stage mutants 37 of 37; fail-before on 989c02a3 5 failed and 1534 passed; of 18 new test names 3 fail on old code and 15 pass on old code; the timing test `test_the_timing_harness_flags_a_quadratic_stand_in` fails on main too (0 of 3) and 1 of 3 on the head (do not touch it); PostgreSQL 17 tests (3 skipped) are IMPOSSIBLE-NOW; CHANGELOG matrix numbers (580, 550, 518, 525 plus 25, 871) all match.
**Reviewer result:** 0 Blocker, 2 Major (D1 and M1, the same defect), 10 Minor, 7 Nit across the two reports. No regression against main, no readable secret, no guard bypassed. The code change is small and correct as read; the defects are in how tests and the CHANGELOG describe what is proven.

## Prioritized Findings & AI Suggestions

### Group 1 [design D1 and codebase M1] - Severity: Major
*   **Scope:** `tests/test_migration_matrix.py` (`EMPTY_PROBES`, `_MAP_NAMES`, `_empty_pairs`, `test_every_empty_reason_is_the_answer_of_a_real_server`, `test_every_empty_pair_has_a_probe_and_its_reason_carries_the_measured_text`); `CHANGELOG.md` lines 9 and 32.
*   **Discrepancy:** The test that is said to fail "if the written text and the server's answer differ" compares the server's answer with the probe's own hard-coded tuple (for example `("42P01", "does not exist")`), never with the reason strings `O_EMPTY_BY_LOGIC`, `C8_EMPTY_BY_LOGIC`, `C13_EMPTY_BY_LOGIC`, `_MAP_REASON`, `_NO_RELATION`. The only link is the word "measured". For the 13 map pairs the probed objects exist in no schema, so every probe fails with 42P01 whatever the schema and no control shows the same statement succeeding on the schema of the run. Changing `_NO_RELATION` to "42P05" or "16.99", or O05's "42883", fails nothing.
*   **Class:** a test that checks a claim against a copy of itself (r15 Issue 4 class).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Both reviewers found it independently and the evidence run does not contradict it: the test passes on 140a1268, which is what the finding predicts. Fix at the one place every reason is read.
*   ***Proposed Edit:***
    *   Build each empty reason from its probe tuple (the SQLSTATE, the server's quoted text and the server version are taken from `EMPTY_PROBES`), so no reason is a free-hand string. Where a reason is kept as written text, assert that the quoted state and text occur in it.
    *   Probe each pair as a (control, probe) pair: create the object in `s`, show the statement succeeds against `s`, and show it fails against `s2` with the quoted state. The 13 map pairs need the object created in a schema, or the reason must say the object does not exist in any schema and the control must be the server's answer for an object that does.
    *   Weaken-and-fail proof: a test (and one mutant) that edits one reason to a wrong state and one that edits one probe tuple, each failing for the named reason.
    *   Reword CHANGELOG line 9 and line 32 to say exactly what the test compares.

### Group 2 [design D2, D3; codebase m1, N1, N3] - Severity: Minor
*   **Scope:** `tests/test_migration_matrix.py` C8 and C13 cells; `CHANGELOG.md` line 32.
*   **Discrepancy:** Many "new cells" never reach the check. Of the 12 C8 cells, 6 ("administrator owns the schema") end at the server's own refusal ("must be owner of schema app") before the effect statement. Of the 12 C13 cells, 6 schema-rename cells end in "permission denied for database", 2 "function moved" cells end at the trigger rule, and only 4 sequence cells judge a right. The O05 C13 test runs only `runtime_role=rt` and `C13_CELLS` counts O05 twice (the no-roles half is counted and never run). The count test checks only `len()`. Nine pairs share `_NO_RELATION` and two share the large-object text while the text says "each pair with its own written reason"; nine C13 empties for O19 to O27 are equivalence arguments, not impossibilities.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The numbers are right but the sentence "12 cells to C8, 12 to C13" overstates what is judged. A reader counts them as judged rights.
*   ***Proposed Edit:***
    *   CHANGELOG line 32: state the split in words: C8 "6 of 12 end at the server's own refusal, 6 judge a right"; C13 "of these 12, 8 end at the server's own refusal or the trigger rule, 4 judge a right"; say the nine O19 to O27 empties are equivalence arguments.
    *   Parametrize the O05 C13 test over `O_VARIANTS`, or count its no-roles half once and say so; make the count test assert the judged and the refused numbers, not `len()`.
    *   Say "nine pairs share one reason" where the text says "each pair with its own".

### Group 3 [design D4, D8; codebase m5] - Severity: Minor
*   **Scope:** `src/hadavin_sdk/store/migrate.py` (`_connected_before_commit` 1250-1262, message 1234-1262); `src/hadavin_sdk/store/postgres.py` (IAM branch 138-145); `tests/test_migration_verify_pg.py` 1100-1183; `CHANGELOG.md` lines 13 and 32.
*   **Discrepancy:** (a) "three real-server tests pin it" overstates: the three connect tests inject the failure (an `OperationalError` from a hook and two `_FailsOnSetup` wrappers); no real unreachable host and no real failing `SET TIME ZONE`. (b) "a connection that cannot be made" gives exit 2 only for driver errors; an IAM sign-in failure (an SDK error from `auth_aws.rds_iam`) still gives exit 3 and no test covers it. (c) The connect-failure message says "The whole run is rolled back ... Run migrate again" for a refused connection (a wrong password), which is odd advice.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** (b) is a real inconsistency at the one connect choke point and is fixable now, not a documentation matter.
*   ***Proposed Edit:***
    *   (b) Catch around the sign-in call inside `connect` and raise a `ConfigError` that does not print the SDK's words, so the exit is 2 for every failure to connect; add a test with a failing signer; grep every other exit-3 path that happens before a connection exists; one mutant.
    *   (a) CHANGELOG: "three tests with an injected driver error".
    *   (c) Use a connection-specific sentence: "could not connect or set up the connection; nothing was started".

### Group 4 [design D5, D6; codebase m2, m3; evidence] - Severity: Minor
*   **Scope:** `tests/migrate_mutants.py:3714-3717` (V88, V89); `tests/test_migration_verify_pg.py` 892-897, 901, 919, 921-923, 939-970, 1045-1048, 1024-1027; `tests/test_migration_verify.py` 1519; the 15 new tests that pass on old code.
*   **Discrepancy:** (a) V88's killer tuple still lists the real-server test while its docstring says it does not discriminate V88 (and V89 needs the same check). (b) The dropped `"25P03" in err` assertion rests on a false comment (the classifier unit tests pin `_is_a_files_own_error`, not the refusal text); nothing now pins that the exit-2 message names 25P03. (c) The 25P03 timing flake of r15 M4 remains: a Python or CI pause over 200 ms between two statements inside the transaction ends the session before the wait. (d) The 25P04 test asserts only `"25P04"`, which is no evidence until the first 17.10 run. (e) The new `needs_pg` re-implementation (lines 1024-1027) is fragile (`_is_not_dsn` demands a literal local `DSN`). (f) The independent run shows 15 of 18 new tests pass on old code; each needs a written reason (a mutant that it kills, or a pin).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** (a) leaves a killer list that contradicts its own docstring; (b) and (c) are the r15 class again; (f) is the lead's standing rule that a new test that passes on old code must say why.
*   ***Proposed Edit:***
    *   Remove the non-discriminating killer from V88 and check V89; run the two mutants and show the remaining killers fail for the named reason.
    *   Add a unit test of `_driver_error_before_commit` that the sqlstate appears for 25P03 and 25P04; fix the comment.
    *   Raise the limit and the sleep together (for example 1 s and 6 s) or assert on the outcome only.
    *   Keep the "first CI run on 17.10 decides" note for 25P04; do not tighten the 25P04 assertion until that run exists (IMPOSSIBLE-NOW).
    *   Replace the `needs_pg` re-implementation with the shared helper, or add a guard test that proves it matches.
    *   Write one reason per row for the 15 tests that pass on old code in `handover/evidence/P3a-2/b7/`.

### Group 5 [design D9; codebase m4] - Severity: Minor
*   **Scope:** `tests/test_migration_rules.py` (`states_its_condition` 1211-1232, `_PG17_AS_FACT` 1262-1292 and 819-830, 888-892).
*   **Discrepancy:** The wording guards are still bypassable: "The schema must be owned by a family role at the start and must not change owner during the run" passes while stating the strict reading with the switch OFF; the PostgreSQL 17 regex misses "green on 17.10", "was run on PostgreSQL 17", "was verified on PostgreSQL 17", "tested on PG 17", "seen passing on 17.10", "confirmed on PostgreSQL 17".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Both guards protect a claim the lead has said must stay honest (O8 OFF, PostgreSQL 17 unrun).
*   ***Proposed Edit:*** Require the switch name in any "must be owned" sentence; add the verbs above and flag "17" within 40 characters of "passing", "green", "verified", "tested" or "confirmed"; one test per new form, each failing on 140a1268; mutants for both guards.

### Group 6 [design D7; codebase N2, N4; lead step M6 and row P3a24b-r16-8] - Severity: Nit
*   **Scope:** `tests/test_migration_matrix.py` (`C10_EVERYONE`, the partition test 832-835, 919-931; reason texts hard-code "PostgreSQL 16.15" while `ci.yml:41` and `:122` run 17.10); `src/hadavin_sdk/store/postgres.py:154`; `handover/questions-for-lead.md:1831`.
*   **Discrepancy:** `C10_EVERYONE` and its partition test are inert (O17's expectation comes from the default rule); reason texts name 16.15 only; a raising `close()` in `except BaseException: conn.close(); raise` would mask the original error; `questions-for-lead.md:1831` still has the old text ("built and tested ... Safe default: keep it OFF") and the replacement text is in BUILDER-notes.md.
*   ***AI Suggestion:*** PROPOSE FIX (the item is worth doing in the same batch; no re-review round is needed for it)
*   ***Justification:*** Cheap, and the reword is a lead-owned step on a file outside the snapshot.
*   ***Proposed Edit:*** Remove or use `C10_EVERYONE`; take the server version in a reason from the probe (group 1); guard the close with `try` and re-raise the first error; the batch-7 builder applies the `questions-for-lead.md` reword from BUILDER-notes.md (M6 of r15, row P3a24b-r16-8) and records it. The lead does not edit that file here.

### Group 7 [owner item, escalation unchanged] - Severity: not rated (OWNER-ONLY)
*   **Scope:** `q-p3a2-o8-schema-owner`: `migrate.py:1286-1294`, `CHANGELOG.md` line 11.
*   **Discrepancy:** O8 stays OFF. A non-superuser role outside the family that owns the run schema can drop or alter the package's tables and the run returns. The text states it honestly and real-server ON and OFF cells exist.
*   ***AI Suggestion:*** ESCALATE (no fix; do not mark fixed; do not merge as "O8 done")
*   ***Justification:*** Switching O8 ON refuses setups an owner may still run; that trade-off needs the owner's decision, which is outside every file the reviewers could read.
*   ***Proposed Edit:*** none. Row stays OWNER-ONLY.

### Evidence group - Severity: Minor
*   **Scope:** `handover/evidence/P3a-2/140a1268/RESULTS.md`.
*   **Facts:** one failed test, environment only (own Postgres socket path), not rerun; the builder's own failure (`test_no_migration_test_skips_silently[tests/test_migration_verify.py]`) is fixed in this head and did not occur; timing test fails on main as well; three PostgreSQL 17 tests skipped; Python 3.12, semgrep, zizmor, trivy, pip-audit not run (IMPOSSIBLE-NOW); the perf suite was not run (no perf item in the ticket).
*   ***AI Suggestion:*** PROPOSE FIX: the batch-7 builder runs the final-head full suite with the runtime Postgres socket path set to its own folder (or states the environment cause with the log), so the final head has zero unexplained failures.

## Handoff

*   Accepted fixes (PROPOSE FIX): 6 groups (1 Major, 5 Minor/Nit groups holding 22 reviewer items: D1 M1 D2 D3 D4 D5 D6 D8 D9 m1 m2 m3 m4 m5 N1 N3 plus nits D7 N2 N4, the lead step and the evidence item).
*   Contested: 0.
*   Escalated: 1 (`q-p3a2-o8-schema-owner`, OWNER-ONLY, stays open).
*   Declined: 0 (25P04 tightening deferred only because it is IMPOSSIBLE-NOW: needs the first 17.10 CI run).
*   Remaining unaddressed: all of the above until batch 7 lands; reviewer severities unchanged.

## Who fixes it

One batch-7 builder on a new branch `core/p3a2-b7` from 140a1268, pushing to `wip/cloud-p3a2-b7`. Method per bug: name the class, fix at the shared choke point, grep siblings, show each new test failing on 140a1268, one mutant per fix with a killer that fails for the named reason, a final-head full suite once, and one reason per test that passes on old code. O8 stays OFF and OWNER-ONLY. The builder does not touch the timing test `test_the_timing_harness_flags_a_quadratic_stand_in`.
