# ciguard-956bac0f-design-r1: ORDER 266 CI guard, head 956bac0f, round 1, persona design

Source: hand-back of the design reviewer (agent a97495a30d38c2cf8), saved by the lead session (condensed). SECURITY path. Static read only; nothing run. Snapshot `/home/user/build/snap/ciguard-956bac0f`. Verdict: do not accept yet. 0 Blocker, 1 Major (+1 minor-to-major), minors.
Bounds on the attack surface: CI runs only on pull_request to main, push to main and schedule (lane branches never run CI); fork PRs do not create origin/wip/cloud-x; every attack below needs write access to the base repo.

## Major
- **M1 The open name `wip/cloud-[A-Za-z0-9._-]+` in the ignore-entry check (ci.yml:198, golden same) lets any writer suppress a real secret.** The entry-format regex (:195, unchanged) is not tied to `handover/(reviews|tickets|evidence)/*.md` nor to rule generic-api-key. Attack: commit a real secret on the PR branch; push `origin/wip/cloud-x` at the same commit; add `<sha>:src/app.py:private-key:N` to .gitleaksignore; :198 passes (commit on a wip/cloud-* branch), :199 passes (not in main); gitleaks honours the fingerprint. The old rule accepted only three fixed names. Fix: restrict the entry regex to path `handover/(reviews|tickets|evidence)/[^/]+\.md` and rule generic-api-key (re-check whether curl-auth-user and private-key entries still need the named branches); require a repository ruleset that restricts creation of `wip/cloud-*` to owners (owner/lead action) and say so.
## Minor-to-Major
- **M2 Lane subtraction in the history range is by reachability, not name** (:222-224): a writer can push `origin/wip/cloud-<x>` at any branch tip and exclude its handover commits from the range; the comment "any other branch name stays in the range and fails" is false. Impact limited: gitleaks scans only `--log-opts=HEAD` and HEAD is re-checked unsubtracted (:227), which is the real control. Fix: say the non-HEAD range is hygiene only and HEAD is the control (or drop the glob subtraction); the ruleset from M1 keeps it honest.
## Minor
Glob vs regex mismatch (`*` matches `/` in the git glob, the regex class has no `/`): align, use the stricter regex in both; `grep -qE 'targetRules|handover/' .gitleaks.toml` gate (:209) evadable by an allowlist written another way (pre-existing; CODEOWNERS and branch protection on ci.yml, .gitleaks.toml, .gitleaksignore are the answer, existence not checked); unused `ignore_line` parameter (test :136); `test_the_step_text_has_no_unquoted_glob_and_a_valid_name` (:223-227) only asserts string presence.
Missing tests: wip/cloud-* ref pointing at another branch's commits; ignore entry with a non-handover path or the private-key rule; lane ref with `/` in its name; absent or fork-style origin ref.
## Does the guard still fail for every non-lane branch?
For HEAD yes (tree and history, including a HEAD built on lane or core/cloud-handover commits: newly closed). For other refs only while they are not reachable from a ref an attacker can name (M2).
## Test honesty
Mostly honest: runs the step's run text unmodified under `/bin/bash -e` (no pipefail, the runner default); checks exit code and message; covers a merge of a lane commit then deleting the file.
## Not checked
git `--not`/`--remotes` semantics executed; tests run; tests/test_ci_gitleaks_scope.py `_load`/`_step`; real .gitleaks.toml anchoring; repo rulesets, CODEOWNERS; gitleaks 8.30.1 handling of fingerprint ignores in the `path:rule:line` form.
