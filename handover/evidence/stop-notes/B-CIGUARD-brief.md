# Builder brief: CI guard fix for wip/cloud-* lane refs (ORDER 266, SECURITY path, small PR)

Branch to build: `core/ci-guard-wip`, created from `origin/main`. Push to the ref `wip/cloud-ci-guard-wip` (the lead opens the PR). NEVER commit anything under `handover/evidence|reviews|tickets/` on this branch (the rule this PR is about). Evidence for this work goes to `/home/user/build/evidence-raw/ciguard/`, not into the repo; the session copies it.
Use a private git worktree under /home/user/build/wt/ciguard. Never cd the main shell into it. Heavy jobs only through `/home/user/build/heavy.sh` (max 3 at once). No secrets, no secret-shaped literals, no live model calls, no merge, no PR state change.

## Why
PR #71 `security` job fails: step "Stale gitleaks ignore entries..." in `.github/workflows/ci.yml` (lines ~188-225) lists 611 to 681 files under `handover/(evidence|reviews|tickets)/` that exist in other remote branches. Those are `origin/wip/cloud-*` handover lane refs. They carry the same files as `origin/core/cloud-handover` (the allowlist lives and dies with that branch). The wip/cloud-* refs never merge into main.

## Change (two places in the same step, nothing weaker)
1. History range: `range="HEAD --all --not origin/core/cloud-handover"` must also subtract the wip lane refs. Add `--remotes='origin/wip/cloud-*'` after `--not` (verify with `git log -m --name-only -z --format= HEAD --all --not origin/core/cloud-handover --remotes='origin/wip/cloud-*' --` that it lists 0 files today; the lead measured 0).
2. "branch contains sha" regex at line ~198: add `wip/cloud-[A-Za-z0-9._-]+` to the alternation next to `core/cloud-handover`.
3. Keep a HEAD-history check that is NOT reduced by `--not`: files under `handover/(evidence|reviews|tickets)/` reachable from `HEAD` itself (the PR branch) must still fail even if the same commit is also on a wip lane ref. State in a comment why (the `--not` list subtracts commits reachable from the lane refs, so a PR branch built on lane commits would hide them).
4. Step names must be valid YAML (no colon followed by a space inside an unquoted name).
5. Regenerate `tests/fixtures/ci_security_golden.json` exactly as `tests/test_ci_gitleaks_scope.py` expects (read the test and its helper first; same PR). Update the test's constants only as needed.
6. NEGATIVE test or CI self-check (required): a branch NOT named `wip/cloud-*` or `core/cloud-handover` (for example `core/other`) that has such a file must still fail the guard; a branch named `wip/cloud-x` with the same file must pass. Preferably a pytest that builds a throwaway local git repo with a fake `origin/` remote-tracking layout and runs the guard's range and regex logic (extract the shell step text from ci.yml so the test runs the real lines, do not copy them). Add a mutant to `tests/` mutation tables only if the repo has a table that pins ci.yml (look for `ci_security_golden` users and `mutation_manifest.json`; keep the manifest hashes right).
7. PR body note (write to `/home/user/build/evidence-raw/ciguard/PR-BODY.md`): `wip/cloud-*` are handover lane refs that never merge into main; the guard still protects every other branch.

## Gates (once, at the final head)
`uv run --no-sync pytest tests/test_ci_gitleaks_scope.py` plus the new test, then ONE full suite via heavy.sh with a PRIORITY, ruff check and format --check, bandit -ll, gitleaks on origin/main..HEAD. Fail-before: run the new negative test against the old ci.yml (it must fail there).

## Report
Write `/home/user/build/evidence-raw/ciguard/NOTES.md`: what changed (files and lines), the commands with exit codes and last lines, what you did not run, the commit sha pushed. Failures and gaps first. Checkpoint every 30 min, stop at 60 min, commit, report. Do not defer problems: fix them or state which exception applies.
