Status: resolved

# Goldfish Annotated Review Report: CI guard, round 2

**Target:** `/home/user/build/snap/ciguard-a001174b/DIFF.patch` (full file), head a001174b, SECURITY path (ORDER 266).
**Sources:** `ciguard-a001174b-design-r2.md` (0 Blocker, 2 Major, 2 Minor, 2 Nit), `ciguard-a001174b-codebase-r2.md` (0 Blocker, 0 Major, 2 Minor, 3 Nit). The independent evidence run was not finished when this was written.
**Mode:** automated, recommended option for every item. Source and snapshot not edited.

## Findings (all PROPOSE FIX unless stated)

### [Issue 1] design M1 - Major - PROPOSE FIX (class B)
*   **Description:** the history, tree and lane-entry checks sit behind `grep -qE 'targetRules|handover/' .gitleaks.toml`, read from the PR's own tree. A PR that rewrites the toml (no allowlist, or one spelled without those words) turns the checks off while a lane-only ignore entry hides a secret in a handover note.
*   **Fix brief:**
    *   File: `.github/workflows/ci.yml`, step "Stale gitleaks ignore entries...".
    *   Change: remove the toml gate around the tree check, the history range check and the HEAD-history check. A file under `handover/(evidence|reviews|tickets)/` in HEAD's tree or HEAD's history is refused whatever the toml says (the only branch that may carry them is core/cloud-handover, which does not run this step as a PR head). Keep the expiry rules conditional on the entries and the EXPIRES line only. Keep "allowlist outlived its branch" as a check that runs when the toml names `targetRules` or `handover/`, but it must no longer switch the other checks off.
    *   Test: throwaway repo; commit adds a handover note; PR replaces `.gitleaks.toml` with (a) no allowlist, (b) an allowlist with `paths` and no `targetRules`; both must fail. Control: no handover file, same toml, must pass.
    *   Mutant: put the gate back; both cases must flip to pass (mutant killed).
    *   Fail-before: run the new cases against ci.yml at a001174b; (a) and (b) must pass there (that proves the hole).
*   **Round needed:** confirming round (third fresh round).

### [Issue 2] design M2 and codebase m1 - Major - PROPOSE FIX (class A)
*   **Description:** short names `origin/main` and `origin/core/cloud-handover` resolve to a tag of the same name before the remote branch.
*   **Fix brief:** use `refs/remotes/origin/main` and `refs/remotes/origin/core/cloud-handover` in the `rev-parse`, `merge-base --is-ancestor`, `--not` and range lines (four places). Sibling search: grep ci.yml, the golden, the test and `check-no-handover-files.sh` (that script uses `origin/main..` and must also be qualified) for any other bare `origin/`.
*   **Test:** throwaway repo with a tag `origin/main` at the root commit; an entry for a commit that is in main history must still print "ignore entry is in main history". Second case: tag `origin/core/cloud-handover` with the branch deleted must still print "outlived".
*   **Mutant:** revert one of the four names to the short form; the test must fail. Fail-before: both cases pass on a001174b.
*   **Round needed:** confirming round.

### [Issue 3] design m2 - Minor - PROPOSE FIX (class B)
*   **Description:** the lane-only ignore-entry branch looks dead: gitleaks scans HEAD, and any HEAD commit with a handover path already fails the HEAD check. No legitimate use found in the diff or the notes.
*   **Fix brief:** delete the `elif ... wip/cloud-...` branch; an entry whose commit is only on a lane ref is "stale ignore entry (not on a named handover branch)". Update the comment, the golden, and PR-BODY.
*   **Test:** entry on a lane ref only (any path, and a handover note with generic-api-key) must fail as stale. Mutant: re-add the branch; test fails. Fail-before: the handover-note case passes on a001174b.
*   **Round needed:** batch only, checked in the third round.

### [Issue 4] design m1 and codebase m2 - Minor - PROPOSE FIX (class C)
*   **Description:** `branches=$(git branch -r --contains "$sha")` aborts under `bash -e` for a sha not in the clone (exit 129), skipping later checks.
*   **Fix brief:** `branches=$(git branch -r --contains "$sha" 2>/dev/null) || branches=`; an empty value takes the stale branch with the old message and the loop continues. Test: entry with a sha that does not exist; output has "stale ignore entry" and the later checks (EXPIRES) still print. Mutant: drop `|| branches=`. Fail-before: step aborts with a raw git error and no EXPIRES message.
*   **Round needed:** batch only.

### [Issue 5] design n1 and codebase 4 - Nit - PROPOSE FIX (class D)
*   **Fix brief:** restore a test that the step name has no ": " (the YAML rule in the builder brief item 4) and that the loader reads the name as a plain string. Mutant: add ": " to the name. Batch only.

### [Issue 6] codebase 3 and design lead actions - Nit - PROPOSE FIX (class D)
*   **Description:** the comment asks for a ruleset on `wip/cloud-*` only; the three fixed names carry the same risk; tags and CODEOWNERS are lead actions.
*   **Fix brief:** write in the ci.yml comment and in `PR-BODY.md` the CI-denial effect (a pushed branch or tag carrying a handover file makes every pull request's range check fail; by design) and the exact lead actions: ruleset restricting create, update and delete of `wip/cloud-*` and of `core/cloud-handover`, `handover-src/c1a-8460813`, `core/P2d-1` (block force-push, delete, and creation if absent); restrict tag creation for names starting `origin/` or `wip/`; CODEOWNERS plus required review on `.github/**`, `.gitleaks.toml`, `.gitleaksignore`. These are needed from the owner (exception 2(b)); next step: the lead sets the ruleset and CODEOWNERS and records the date. Batch only.

### [Issue 7] codebase 5 - Nit - DECLINE
*   **Description:** `git for-each-ref ... || true` swallows a failure. Fails closed (fewer lane refs subtracted, hygiene range only). Recorded, not changed.

### [Issue 8] design n2 - Nit - PROPOSE FIX (documentation, rolled into Issue 6).

## Test gaps named by the reviewers (all folded into the fix briefs above)
Tag shadow (Issue 2), unknown sha (Issue 4), toml-gate evasion (Issue 1), entry on a lane only (Issue 3). Reviewers also name: merge with a handover file on a side branch, `refs/pull`, sha on both a lane and a PR branch, paths with spaces. Add one throwaway-repo case each where the real step text can express it; the merge case is required (the `-m` flag is the control).

## Order of work and stop rule
One fix batch (Issues 1-6), gates once at the final head, independent evidence at the final head, then a THIRD fresh round (security path, no cap). Fix minors in the same push.

## Handoff
*   Accepted fixes (PROPOSE FIX): 7 (Issues 1-6 and 8)
*   Contested: 0
*   Escalated: 0 (the lead actions in Issue 6 need the owner and are listed there)
*   Declined: 1 (Issue 7)
*   Remaining unaddressed: 0 in this report; all fixes open until built and verified (ledger CIGUARD-r2-1..4)
