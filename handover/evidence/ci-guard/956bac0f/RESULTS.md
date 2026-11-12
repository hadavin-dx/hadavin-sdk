# CI guard evidence, head 956bac0f877bb54b9bbae83c773123f6f8618025 (base main a8b4d8e8) - EVIDENCE RUNNER, records only
## Not run / failed first
- FULL PYTEST: NOT RUN, stale head (coordinator order: fix incoming). No Postgres cluster started, no heavy.sh slot taken.
- Case g (lane ref at a commit that is also in the PR branch, plus ignore entry `<sha>:src/app.py:private-key:1`): guard step PASSED (rc=0). See 09-case-g.log. This is the Major the coordinator expected (an ignore entry for a PR's own commit is accepted because a wip/cloud-* ref contains it).
- Extra g2 (not asked): origin/wip/cloud-a/b (slash after cloud-) carrying a handover file PASSES (rc=0): git's --remotes glob `*` crosses `/`, though the test list only treats "feature/wip/cloud-x" as bad. Informational.
- gitleaks and zizmor were not installed; I fetched gitleaks 8.30.1 (sha256 checked against ci.yml: OK) and ran zizmor through uv.
## Results
1. tests/test_ci_gitleaks_scope.py + tests/test_ci_guard_wip_lanes.py: 102 passed, rc=0 (01-focused.log)
2. fail-before (new test file vs ci.yml from origin/main): 6 failed, 8 passed, rc=1 (02-failbefore.log). Failed: 3x lane-passes params, head-built-on-lane-commit, ignore-entry-on-wip-branch, step-text-quoted-glob.
3. Real step text (bash -e) in throwaway clones, hand-made refs (03-cases.log, h/case-*.log):
 - a PASS rc=0 OK; a2 (wip/cloud-245-B-P4da2) PASS OK
 - b HEAD authored file: FAIL rc=1 OK (tree, range and HEAD-history messages); b2 added then deleted: FAIL OK
 - c origin/core/other: FAIL OK; d origin/wip/cloudx: FAIL OK; e HEAD built on lane commit: FAIL OK ("history of HEAD itself")
 - f real remotes (243 refs), HEAD detached at 956bac0: NEW range 0 files (0 unique); HEAD-only 0; OLD range (origin/main ci.yml) 681 listed (611 unique). Full new step rc=0, full old step rc=1.
 - g: see above (passes, Major). g2: see above.
4. ruff check rc=0; ruff format --check rc=0 (321 files); bandit -ll rc=0 (only nosec warnings); scan_repo rc=0; gitleaks git origin/main..HEAD rc=0 (1 commit, no leaks); gitleaks --log-opts=HEAD (CI scope) rc=0; zizmor --offline rc=0 (no findings, 3 suppressed).
5. Full pytest: not run, stale head.
Cleanup: worktree ev-ciguard and all clones removed; no Postgres started; nothing committed anywhere.
