# PR84 round 7, design critic (head ac7afea). Verdict: NOT CLEAN. 0 Blocker, 3 Major.
Read-only review; ran nothing (258/249 test counts, ruff/bandit/zizmor, Docker/Vault output unverified).

## Major
1. M4 only closed for a list of spellings. Verdict can still be neutralised: `; true`, final `exit 0`, `| tee x` (no pipefail), `|| echo ignored`, `trap 'exit 0' EXIT`, `set +o errexit`. Guard: tests/test_evidence_workflow_guard.py:64-66, 257-263. Fix at choke point: verdict script must equal a golden text (last logical line is the `report` command; no | ; && || & trap exit set inside).
2. Job-level `if`, matrix exclude/include and the `on:` block are not guarded (guard 110-196, 209-387). `if: ${{ false }}` on the evidence job gives green with no tests. Added trigger (push/pull_request_target) passes every rule. Fix: `on` exactly workflow_dispatch; no job `if`; strategy only fail-fast:false and matrix.python.
3. test_the_mask_pattern_is_built_once_per_value (guard ~1868-1876) writes os.environ directly and `del`s HADAVIN_TEST_VAULT_TOKEN: removes the real token for later tests (order dependent). Fix: monkeypatch.setenv, clear `_pattern` on teardown.

## Round-6 Majors: 9 of 10 closed; M4 partly (see 1); codebase M2 reopened in new form (see 3).

## Nits
- Step-level empty HADAVIN_TEST_VAULT_ADDR passes addr-missing; prints-token/prints-env only match lines starting echo/printf/env/cat; SHELLOPTS via GITHUB_ENV in script not caught; local/reusable action crashes workflow_problems (IndexError/KeyError) at guard 153.
- Helper skip rule fires only for reasons containing HADAVIN_TEST_ (evidence_step.py:243); HADAVIN_REQUIRE_PINNED_UNIDATA (py3.14 leg) not matched. Commit id on first log line not compared with plan SHA. token-reader check is a mistake catcher only.
- Runner facts and Vault start steps not in verdict list. evidence.yml:21-22 wording. Unseal key protected only by grep word match, not add-mask. uv cache poisoning by tested code (write-access users only).
- Vault-start detection misses `docker container run`, podman, compose, script file.

## Not leaked: no path found for a Vault token to reach the artifact/summary as files stand (reading only).
