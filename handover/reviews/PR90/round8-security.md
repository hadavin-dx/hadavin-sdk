# PR90 round 8 (egm-design, sonnet), head 051a18d, snapshot 90-051a18d
Verdict: no Blocker, no Major against the three purposes. Read-only; ran nothing.
Round-7 tool-path Major FIXED: step "System tools resolve outside the workspace" (ci.yml:173-175) covers 13 tools, fails on non-absolute path or path under $GITHUB_WORKSPACE; pinned in golden JSON, SECURITY_STEP_NAMES, negative case "tool shadow check dropped".
Purpose 1 (scan scope = head): met (--log-opts=HEAD, fetch-depth 0, persist-credentials false, SCAN_BAD 14 variants).
Purpose 2 (curl retries): met (both downloads, flags, checksum adjacency, CURL_BAD 13 mutants).
Purpose 3 (pin test): met (golden= flag, GOLDEN_ONLY checked, gitleaks config negatives reach tracked-files check, ALLOWED_HITS fix).
Nits for follow-up guard PR: symlink not resolved by command -v; python3/uv/uvx not in shadow list (venv by design; round-6 finding 5 owner item); stale-ignore regex/+90 days is hygiene; suppression markers per ORDER 187.
