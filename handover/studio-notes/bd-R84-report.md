# bd-R84 report: PR84 (core/ci-evidence) round-1 findings. New head 5a78d59 (was 8a677ad)

## NOT DONE / UNCERTAIN (first)
- The workflow has NEVER run on GitHub. actionlint 1.7.12 (via uvx) reports no problem, but that is a syntax check only. Untested: `gh api repos/.../commits/<ref>` resolving the ref, the sparse second checkout (`.evidence-tools`), the `docker run` Vault step and its readiness loop, `::add-mask::`, and that the pinned Vault image accepts `-e VAULT_DEV_ROOT_TOKEN_ID` without a value. First real run must be watched (finding 6 stays open until then; the PR text must say "untested on GitHub").
- Full suite at b60d99f: 1 failed, 9961 passed, 454 skipped (log: handover/reviews/PR84/bd-R84-fullsuite-b60d99f.log, exit=1). The failure was my own new test text tripping tests/test_stage_names.py (old stage word). Fixed in 5a78d59; re-verified only the 3 affected files (155 passed), NOT a second full suite. Skips are the Postgres/Vault tests (no service here); they run in CI.
- (FIXED later in head 0cc446a, hardened in de18d59) Sibling: .github/workflows/ci.yml had the fixed Vault token `root` in two service containers (check, tests-py312). Changing it alters the required CI check and cannot be run here; needs the lead's decision. Next step: same random-token step as evidence.yml.
- Postgres 16+17 matrix: no ticket was found in the review files, so not done.
- Perf exit 5 (no perf tests collected) now shows as a failed step (visible, not hidden); not special-cased.
- bandit: 3 Low findings (subprocess use) in tools/evidence_step.py; `bandit -ll` ignores Low (not run as a CI-identical command; used uvx bandit).

## Findings
| Finding | Class | Fix | Fail before | Pass after |
|---|---|---|---|---|
| M1 design: exit= lost under bash -e | exit code swallowed by shell | tools/evidence_step.py `run` records exit of every command | old text: step "Stage-rename mutants" has no recording; test_the_old_pattern_lost_the_exit_code | test_a_failing_command_keeps_its_exit_code... |
| M2 design: first failing runner aborts loop, refused names unrecorded | loop aborts | loop sets fail=1, continues; names validated up front in plan job (refusal fails the run before any runner) | old text rule set (14 problems, list below) | guard 18 passed |
| M3 design: cancel-in-progress destroys evidence | concurrency | cancel false; group has ref+pythons+runners; upload/summary/vault removal `always()` | "concurrency must set cancel-in-progress: false" | pass |
| M4 design: skipped steps not recorded | silent skip | `report` shows NOT RUN for any expected step with no row and fails | test_the_report_fails_on_..._never_ran | pass |
| M5 design: Vault token `root` | fixed credential | Vault is a step: `openssl rand -hex 24`, masked, loopback only, removed at end | "fixed Vault token 'root'", "Vault must be a step" | pass |
| M6 design: never linted/run | no check | actionlint clean; guard test of 10 rule classes + 10 plants; PR text must say untested | n/a | actionlint rc=0 |
| M7 design: pythons input unvalidated, PY into env | untrusted input | plan job allowlists (3.12+, max 4, `^3\.[0-9]+$`), ref allowlist, runner-name allowlist, max 8; jobs read only needs.plan.outputs | no plan job in old text | test_allowlists_refuse_odd_input, test_the_plan_command_writes_only_checked_values |
| M1 codebase: `--no-build` unverified | unverified claim | same command as ci.yml lines 78/146 (CI uses it); kept | n/a | n/a (not run here) |
| M2 codebase: hashFiles silent skip | silent skip | no hashFiles; missing runner = recorded exit 2, run red | | |
| M3 codebase: example runner missing | wrong doc | description now names tests/mutation_runner_mutants.py (exists) | | |
| M4 codebase: `exit $rc` in subshell | = M2 design | = M2 | | |
| M5 codebase: `|| true`, head/env listed | masked failure | report reads status rows; no `|| true` (guard rule) | "'|| true' hides a failure" | pass |
| Nits | psql under -e: own recorded step `psql-present`; ref resolved once to sha in plan job; install log saved and tests skipped (NOT RUN) if install fails; per-step timeouts; HADAVIN_REQUIRE_PINNED_UNIDATA only on 3.13 (as ci.yml); uv cache already via setup-uv; permissions per job | | |

Old workflow text, guard problems (fail-before, 14): cancel-in-progress not false; group lacks ref/pythons; job permissions not set; Vault service with fixed token; 7 steps without timeout; `|| true`; upload without always(); token root. Saved: /home/user/build/B-R84-oldproblems.txt. After: `18 passed`.

## Commands and output
- ruff check src tests demos tools: All checks passed. ruff format --check: 318 files already formatted.
- pytest tests/test_stage_names.py tests/test_evidence_workflow_guard.py tests/test_repo_rules.py: 155 passed. tools/scan_repo.py exit 0.
- Full suite via heavy.sh at b60d99f: see above.
- Files: .github/workflows/evidence.yml, tools/evidence_step.py, tests/test_evidence_workflow_guard.py. Commits b60d99f, 5a78d59 pushed (no force).

## NOT RUN
Real GitHub run; docker/Vault step; Postgres-backed tests; mutation scripts; second full suite; EGM steps (evidence runner, reviewers: lead's). Least privilege: workflow identity = GITHUB_TOKEN contents:read per job (plan reads commit info via gh api; evidence job reads the repo); no other identity; the Vault token is per run, masked.
Token use: not measured. R-numbers: bible not available here; rules used: CLAUDE.md least privilege, class-level fixes.

## Round 2 (bd-R84 fix round), head: see below
Fixed: runner/built-in name collision (extra- prefix, repeated name refused in `run`, report fails on repeated rows); token reader check step + header note; report shows skipped counts and fails on "HADAVIN_TEST_ ... not set" skips; guard plants for verdict !cancelled(), Vault removal always(), install outcome, report list drift, uv run / python -m pytest, concurrency with runners; nits: PYTHONUNBUFFERED, unused SHA env removed, Postgres on loopback, job timeout 150, concurrency comment, docstrings, pull/N/head message, version regex 3.12-3.99 (huge digits now Refused), runner name length cap, "never finished" wording, "same test selection" wording, safe Vault removal.
Fail-before on 5a78d59 files: 12 of the new/updated tests fail (/home/user/build/B-R84-failbefore-r2.txt); after: guard + test_stage_names 130 passed; ruff check/format clean; actionlint rc=0.
NOT done: no full suite (ordered); still never run on GitHub; upload-artifact pin and whether the suite reads HADAVIN_TEST_VAULT_TOKEN at every tested ref are only checked by the new step at run time; raw logs are unmasked (artifact kept 30 days, nit accepted: logs hold test output only, no secrets by repo rule); third queued run replaces second (GitHub behaviour, commented); ci.yml sibling still open.

## ORDER 180 (ci.yml Vault token), head 0cc446a
Failures/uncertain first: none of ci.yml has run on GitHub (the required check changes: both test jobs now start Vault with `docker run` in a step; actionlint clean, nothing executed). Docker availability on the runner, loopback port publish and the `vault status` wait are untested. Full suite NOT run.
Done: ci.yml jobs `check` and `tests-py312`: Vault service removed; step makes `openssl rand -hex 24`, `::add-mask::`, HADAVIN_TEST_VAULT_TOKEN to GITHUB_ENV, same value to container via exported VAULT_DEV_ROOT_TOKEN_ID, loopback port, removal step with always(). evidence.yml already did this. No literal `root` token left in any workflow.
Guard (tests/test_evidence_workflow_guard.py): vault_problems() runs on every .github/workflows/*.yml; 10 plants x 2 files (literal token, fixed value, no mask, tests not given token, container different value, second value, printed token, public port, no removal). Fail-before: old ci.yml (cbcf868) gives 3 problems (/home/user/build/B-R84-failbefore-r4.txt). After: guard + test_stage_names 163 passed; ruff check/format clean; actionlint rc 0 for ci.yml and evidence.yml; scan_repo 0. tools/evidence_step.py unchanged (nothing to change).

## Round 4 fixes, head de18d59
Failures/uncertain first: nothing ran on GitHub. No local Vault binary, so the real-server contract tests were NOT run (only the local fake: tests/contracts -k vault 12 passed). Not applied: container hardening flags (no-new-privileges, memory), Dependabot docker entry, start step not recorded as an evidence row (job still goes red and the verdict shows NOT RUN). Full suite NOT run.
Done: (A) tools/evidence_step.py mask() removes HADAVIN_TEST_VAULT_TOKEN from saved logs, status, report and summary (test with planted token). (B) host-side readiness probe (curl with X-Vault-Token on 127.0.0.1:8200), fast fail if the container exited, docker ps/logs (token filtered) on failure, in ci.yml (both jobs) and evidence.yml. (C) vault_target() raises a clear error when the address is set without the token (no ROOT fallback); the only consumers are secrets_neutral, audit_neutral and test_p3b_neutral_audit, all via vault_target(); no pytest.skip in the Vault kinds so a connection or sign-in failure fails the test; stale docstrings fixed; token-reader step moved right after checkout, comment updated. (D) guard: print detection (echo, printf, text, braces, set -x), exactly one -p 127.0.0.1:8200:8200, no -P/host network/privileged/by-value token, every docker run step inspected, container named vault-ci, removal by exact name after the last test step, mask before GITHUB_ENV write, *.yml and *.yaml, jobs that use the server must start one. (E) one VAULT_IMAGE digest in ci.yml env, guard that all digests are equal; artifact name has run_attempt; ci.yml Postgres published on loopback. (F) notes updated.
Fail-before vs 0cc446a files: 16 tests fail (/home/user/build/B-R84-failbefore-r5.txt). After: guard + test_stage_names 206 passed; test_p4b_secrets + test_p3b_neutral_audit pass; ruff clean; actionlint rc 0 (both); scan_repo 0.
