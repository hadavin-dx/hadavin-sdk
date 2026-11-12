# ciguard-a001174b-design-r2: CI guard (ORDER 266), head a001174b, round 2, persona design

Source: hand-back of the design reviewer (agent a7c3ae0d), saved by the lead (condensed). SECURITY path. Static read only; no evidence existed. 0 Blocker, 2 Major (both pre-existing, neither fixed by this change), 2 Minor, 2 Nit. Snapshot `/home/user/build/snap/ciguard-a001174b`. Verdict: the two round 1 holes are closed in the code as written; the guard is not hole-free.

## Round 1 findings
Closed: (a) lane-only commit entries are accepted only for `handover/(reviews|tickets|evidence)/<name>.md` with rule generic-api-key (ci.yml:204-205); (b) lane refs listed by for-each-ref and filtered by the same pattern (:233): nested, empty-suffix, `+` names no longer subtracted or accepted; the HEAD-only log (:238-239) still catches a PR branch reachable from a lane ref.

## Major
- **M1** The history, tree and lane-entry checks sit behind a toml gate the PR itself controls: `grep -qE 'targetRules|handover/' .gitleaks.toml` read from the PR's own tree (:217; main :209). Failing input: commit C adds `handover/reviews/n.md` with a generic-api-key-shaped secret; the PR replaces `.gitleaks.toml` with no allowlist, or an allowlist written `paths=['''^handover\/reviews\/...''']` with no `targetRules` key; `.gitleaksignore` gains `C:handover/reviews/n.md:generic-api-key:1` and an EXPIRES line; a writer pushes `origin/wip/cloud-n` at C. Line 205 passes, the gate is off, tree and history checks are skipped, gitleaks honours the fingerprint: green step, a secret in a handover note reaches main. The second spelling alone (an allowlist the grep does not match) suppresses every rule on handover files for any PR author. Round 1 rated the gate Minor and answered it with CODEOWNERS; nothing here addresses it. Fix: make the checks unconditional, or gate on a parsed toml; pin CODEOWNERS and a required review on ci.yml, .gitleaks.toml, .gitleaksignore.
- **M2** Bare revision names are ambiguous with tags: `origin/main` and `origin/core/cloud-handover` (:192, :207, :219, :233). Git resolves `refs/tags/<name>` before `refs/remotes/<name>`; checkout with fetch-depth 0 fetches tags. Failing input: `git push origin <unrelated-sha>:refs/tags/origin/main`: the `merge-base --is-ancestor "$sha" origin/main` test (:207) runs against the tag, so "entry is in main history" never fires; an entry for a secret already in main on a commit that also sits under core/P2d-1 or core/cloud-handover passes. A tag named `origin/core/cloud-handover` spoofs the :219 existence check and the `--not` subtraction (hygiene only). Fix: `refs/remotes/origin/main` and `refs/remotes/origin/core/cloud-handover` everywhere.

## Minor
- **m1** :202 `branches=$(git branch -r --contains "$sha")` is a bare assignment under `bash -e`: a sha not in the clone (usual "stale entry, branch deleted") exits 129 and aborts, skipping the stale message and later checks. Fix: `|| branches=`. No test for a non-existent sha.
- **m2** Lane-only entries look dead: gitleaks scans HEAD; any HEAD commit with a handover path fails the HEAD check (gate on), so a lane-only entry is inert or contradicted by it; the lane branch (:204-205) adds attack surface (M1) with no apparent legitimate use. Consider deleting it. The fixed-name case is also at risk if core/cloud-handover is in HEAD history.

## Nit
- n1 test `test_the_step_text_has_no_unquoted_glob_and_a_valid_name` removed (DELTA-vs-r1.patch); the no ": " in step name check rests on the golden or the loader.
- n2 a writer-pushed branch or tag carrying a handover file fails every PR's range check (CI DoS); by design, undocumented; lane-ref hygiene range hiding other branches by reachability is acknowledged and tested.

## Golden and test truth
Golden `run` string matches ci.yml:189-242 on a visual comparison (not mechanical). Tests run the real text through `_step(_load(), STEP)["run"]` under `/bin/bash -e` (matches the runner default, no pipefail); `_load`/`_step` not read. Fail-on-old reasoning given. HEAD-control test asserts the message only the second `git log` can emit. Gaps: no tests for M1, M2, m1; none for a merge with handover on a side branch, a tag, `refs/pull`, or a sha on both a lane and a non-handover branch.

## Lead actions, not code defects
Repository ruleset: creation and update of `wip/cloud-*` restricted to owners; force-push and delete blocked on the three fixed branches (re-creating core/P2d-1 at a PR commit would grant any path and rule); tag creation restricted (names starting `origin/`); CODEOWNERS and a required review on ci.yml, .gitleaks.toml, .gitleaksignore.

## Checked and found fine
Shell: IFS only for `read`; loop not a subshell; `range` array quoted; lane refs as full refnames (no option injection); `|| true` correct; unset `$branches` falls to stale (fail-closed); no `set -u` issue. Entry parsing: `-z` plus `tr` safe; format regex rejects CRLF, uppercase hex, trailing space, `path:rule:line` without a sha; duplicate shas handled per line. Ref names: dots and leading dash inside `wip/cloud-` fine; nested rejected in both places; `origin/origin/wip/...` cannot spoof (anchored); `--contains` ignores tags and refs/pull. History: `-m` covers merges; rename out of handover safe; deletion lists the path; fork PR creates no origin refs; shallow clone fails closed.

## Not checked
`_load`, `_step`, real `.gitleaks.toml` and `.gitleaksignore` on main; nothing executed; gitleaks 8.30.1 fingerprint handling; inline `gitleaks:allow` comments (suppress with no entry; untouched by this guard); `pull_request_target` or required-workflow settings.
