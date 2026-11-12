Status: resolved

# Goldfish Annotated Review Report: CI guard (ORDER 266), round 3

**Target:** `/home/user/build/snap/ciguard-b8ea4f69/DIFF.patch` (full file), head b8ea4f69, SECURITY path.
**Sources:** `ciguard-b8ea4f69-design-r3.md` (0 Blocker, 2 Major, 3 Minor, 1 Nit), `ciguard-b8ea4f69-codebase-r3.md` (0 Blocker, 1 conditional Major, 4 Minor, 3 Nit). Evidence runner a2e85079 not finished; not waited for. Source and snapshot not edited.
**Lead measurements used (2026-11-12, live refs):** new range lists 0 handover files; handover-src/c1a-8460813 and core/P2d-1 carry 0 since main; origin/main's `.gitleaksignore` holds a legitimate fixed-branch entry for a NON-handover path (tests/test_redact_fold.py, commit on core/P2d-1); main's `.gitleaks.toml` already holds other allowlists. Any narrowing below keeps those files passing.

## Issue 1: forged fixed-name branch makes an ignore entry acceptable (design M1) - Major - PROPOSE FIX (needs confirming round)
*   **What can be narrowed now.** Why it matters: gitleaks scans every fetched ref, so an entry normally hides a finding on ANOTHER branch (the P2d-1 fixture, the handover lane). A secret reaches main only if its commit is in the pull request's own history. So: an entry whose commit is an ancestor of HEAD (`git merge-base --is-ancestor "$sha" HEAD`) is accepted ONLY if the identical entry line already exists in `refs/remotes/origin/main:.gitleaksignore`; otherwise "ignore entry hides a commit in this pull request's own history: <sha>". Entries for commits outside HEAD's history keep today's rule (on a fixed-name branch, not in main). Main's current entries pass (their commits are not in an ordinary PR's history; the PR that merges P2d-1 already finds its entry in main's file).
*   **What stays a lead action (owner-only):** protect the three fixed branch names (ruleset: no create, update, force-push or delete except owners). Without it a writer can still hide a finding on a branch that is NOT bound for main; the new rule makes that harmless for main.
*   **Brief:** file `.github/workflows/ci.yml` (ignore-entry loop) plus golden; test in `tests/test_ci_guard_wip_lanes.py`: throwaway repo, forged `origin/core/P2d-1` at C, PR head contains C, entry not in main's file: fails with the new message; the same entry already in origin/main's `.gitleaksignore`: passes; entry for C not in HEAD history: passes as before. Mutant: drop the ancestor test (test killed); accept every entry when HEAD contains it (killed). Fail-before: the first case passes (rc 0) on b8ea4f69.

## Issue 2: the toml and inline `gitleaks:allow` are trusted without a check (design M2) - Major - ESCALATE to the lead as an owner-only action, plus a wording fix (PROPOSE FIX)
*   **Why not code:** a rule "toml equals main" or "no new allowlist" would fail every legitimate fixture allowlist (main already has several) and has no owner-approved way through in CI (the owner-approved change would itself fail). A shape check by regex on the toml is brittle and was not asked for by the round 2 reviewers; it would be a guess. The gap predates this change and is not widened by it.
*   **Owner-only next step (exception 2(b)):** CODEOWNERS entry for `.gitleaks.toml`, `.gitleaksignore`, `.github/**` and a branch rule requiring code owner review, so the files that switch the scanner off cannot change without the owner. The lead sets it and records the date.
*   **Fix in this PR (batch only):** the ci.yml comment (:212-214) and PR-BODY must say what is true: the step keeps the handover-path checks on whatever the toml says; it does NOT make the toml trustworthy; that is the owner's review of those three files. Test: golden follows; no behaviour change.

## Issue 3: wording and unbacked claims (design minors, codebase n2) - Minor - PROPOSE FIX (batch only)
*   Messages (:229, :244, :248) drop "the temporary allowlist would hide generic keys" and say "handover notes must live only on core/cloud-handover and its wip/cloud-* lane branches". Comment :223-225: say the lanes are exempt from the hygiene range and list the two other fixed names as trusted for ignore entries only. Remove the unbacked claim that core/cloud-handover "does not run this step as a pull request head" (say it would fail, by design). Test: the new message text appears in the golden; a test asserts the old wording is gone (kills a revert).

## Issue 4: unkilled mutants and a swallowed error (codebase m1, m2, m3) - Minor - PROPOSE FIX (batch only, covered by the confirming round)
*   m1: test with `refs/remotes/origin/main` deleted and a tag `origin/main` present: rc 1 with "origin/main is missing". Mutant: `origin/main` short name at :192 (killed).
*   m2: test of an evil merge that introduces a note only in the merge result on a branch that is neither HEAD nor a lane: the range check lists it. Mutant: drop `-m` at :243 (killed).
*   m3: replace `2>/dev/null` with an explicit return code test (0 = ancestor, 1 = not, anything else prints the git message and fails). Test: a fake `git` earlier in PATH returns 128 for `merge-base`: the step fails with a message. Mutant: restore the swallow.

## Issue 5: a pushed ref that carries a handover note fails every pull request (design minor, codebase M1 and m4) - Major (conditional) / Minor - PROPOSE FIX for the message, owner-only for the ruleset
*   Not reproduced on the live refs (0 files). Standing risk, documented in the ci.yml comment and PR-BODY (it is a denial of service, not a bypass). Fix in code: the failure message names the first five offending paths AND the refs that hold them (`git for-each-ref --contains` of the commit that added the path is too heavy; use `git log --all --format=%H -1 -- <path>` then `git branch -r --contains`), so the lead can delete the ref at once. Test: the message names the ref. Ruleset on wip/cloud-* and the three fixed names and a tag-creation limit (names starting `origin/` or `wip/`) stay owner-only.

## Issue 6: nits - PROPOSE FIX (batch only)
*   Step-name test also rejects " #" and a leading indicator character (n1). `[ ] && range+=` becomes `if ... fi` (n3). The test file's imports from `tests.test_ci_gitleaks_scope`: assert in the test that `_load` and `_step` exist (it already runs, so no change needed beyond a note).

## Stop rule
Issue 1 changes the logic of a security path: a fresh FOURTH round is required after the fix batch, reading the snapshot of the new head and the independent evidence. Issues 2-6 are wording, tests and owner-only actions and ride in the same push; they get no round of their own.

## Handoff
*   Accepted fixes (PROPOSE FIX): 5 (Issues 1, 3, 4, 5, 6) plus the wording part of Issue 2
*   Contested: 0
*   Escalated: 1 (Issue 2: CODEOWNERS and required review, plus the ruleset and tag limit of Issues 1 and 5: owner-only)
*   Declined: 0
*   Remaining unaddressed: 0 in this report; all open until built and verified (ledger CIGUARD-r3-1..5)
