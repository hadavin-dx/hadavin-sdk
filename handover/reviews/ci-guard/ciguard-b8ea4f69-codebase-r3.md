# ciguard-b8ea4f69-codebase-r3: CI guard (ORDER 266), head b8ea4f69, round 3, persona codebase details

Source: hand-back of the codebase reviewer (agent a618dd8d), saved by the lead (condensed). SECURITY path. Read-only, nothing run. Snapshot `/home/user/build/snap/ciguard-b8ea4f69`. 0 Blocker, 1 Major (conditional), 4 Minor, 3 Nit. Round 2 minors 1 and 2 and nit 4 look closed.

## Major (conditional, needs evidence)
- **M1** The tree, history and HEAD checks now run for every pull request (ci.yml:226-248), no longer behind the toml grep. The range (ci.yml:240-242) subtracts only core/cloud-handover and the strict wip/cloud-* lanes. If any other fetched branch or tag (candidates: handover-src/c1a-8460813, core/P2d-1, named at ci.yml:203) has a `handover/(reviews|tickets|evidence)/` path in its history, every pull request fails at ci.yml:244. Verify with for-each-ref and the range log before merge.
- **Lead check 22:00Z (live refs, after `git fetch --all`):** range `<guard head> --all --not origin/core/cloud-handover <all strict wip/cloud-* lanes>` lists 0 files; handover-src/c1a-8460813 and core/P2d-1 carry 0 such files since origin/main; origin/main's .gitleaks.toml has 4 lines matching the old gate words, so the old gated check already ran on main. M1 is not reproduced on the live refs today; it stays a standing risk only if someone pushes a ref with such a file (documented DoS, lead-action ruleset).

## Minor
- **m1** Unkilled mutant: `git rev-parse --verify -q refs/remotes/origin/main` (ci.yml:192) reverted to `origin/main` passes every test. Test: delete refs/remotes/origin/main, create tag origin/main, expect rc 1.
- **m2** `-m` in the range log (ci.yml:243) is killed by no test (test:234 kills only the control's `-m`; test:255 passes without it). Hygiene only. Add a merge-only note on a non-HEAD branch case or say the range `-m` is hygiene.
- **m3** `2>/dev/null` on merge-base (ci.yml:204): a real error exit 128 is read as "not in main"; no fail-open found; the error is invisible in the log.
- **m4** A tag or branch pushed with a note under an unlisted name fails every pull request (ci.yml:233-234, documented); `--all` includes tags and refs/remotes/pull/*/merge. Depends on the lead-action ruleset.

## Nit
- n1 test:270 checks only `": "` in the step name; a plain scalar also breaks at `" #"`. n2 messages at ci.yml:229, 244, 248 still say "the temporary allowlist would hide generic keys" though the checks now run without an allowlist. n3 `[ ] && range+=` (ci.yml:241) is safe under `bash -e` today; use `if`.

## Checked and found fine
Tests run the real step text (`_run_guard` writes `_step(_load(), STEP)["run"]`, `/bin/bash -e`, real temp repo); lane-only, unknown-sha, tag origin/main, deleted-branch tag, range tag, toml-independence and merge tests fail on the old code for the stated reasons; golden hunk equal on reading (not byte-exact); git semantics (`--all --not`, empty negative list, qualified refs, `for-each-ref | grep || true`, `branches=... || branches=` fail closed, `read -r` with IFS=:, `-m --name-only -z` with `tr`); no new fail-open found; step name still parses.

## Not checked
Nothing executed; whether origin/main, handover-src/c1a-8460813 or core/P2d-1 carry handover paths (lead measured 0, above); byte-exact golden and the regeneration test; fork pull request behaviour (no origin refs, fails at ci.yml:192 as before); gitleaks scan semantics; ruleset and CODEOWNERS lead actions; round 2 design report.
