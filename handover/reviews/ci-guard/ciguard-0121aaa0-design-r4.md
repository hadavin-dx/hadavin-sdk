# ciguard-0121aaa0-design-r4: CI guard, head 0121aaa0, round 4, persona design

Source: hand-back of the design reviewer (agent a2e876ba), saved by the lead (condensed). SECURITY path. Read only the snapshot `/home/user/build/snap/ciguard-0121aaa0`; nothing run. 0 Blocker, 1 conditional Major, 3 Minor, 2 Nit.

## Major (conditional)
- **N1** ci.yml:237-273: the handover path checks (tree, range, HEAD) now run on every PR (before: only when `.gitleaks.toml` held `targetRules|handover/`). The range subtracts only core/cloud-handover and wip/cloud-*. If handover-src/c1a-8460813, core/P2d-1, any other branch, a tag or main itself carries such a path, every PR fails. Asked for a dry run on real refs. Lead check 2026-11-12 22:08Z: those two branches 0 files since origin/main; main history 0; remote has no tags; the independent runner's live-ref run at b8ea4f69 exited 0 (142 lane refs, 0 files). Does not reproduce today; stays a documented standing risk.

## Minor
- N2 ci.yml:240: guard pattern is root-anchored and not tied to the real allowlist path regex; add a test reading the repo `.gitleaks.toml` or confirm equal.
- N3 ci.yml:233: toggle `targetRules|handover/` matches any allowlist using targetRules (main has 4 matches); the "outlived branch" message may then be wrong for an unrelated allowlist. Old behaviour; mention in comment.
- N4 (accepted, documented): any writer-created ref named wip/cloud-* hides its commits from the range check; any branch or tag with a note under another name fails every PR (denial of service). HEAD history is re-checked with nothing subtracted.

## Nits
N5 step name and golden do not mention the own-history rule or handover path rules. N6 "System tools resolve outside the workspace" list lacks `sed`.

## Held
Forged fixed-name branch at a PR commit (refused, line 216); edited entry line; main's legitimate b12b7dd entry; lane-only or unknown sha; tag shadowing (full refs/remotes spelling); merge commits (-m plus HEAD log); renames; git exit codes; triggers; comments do not over-claim.

## Not checked
Real refs and real `.gitleaks.toml`, pytest, checkout layout beyond fetch-depth 0, refs/replace and grafts, shellcheck.
