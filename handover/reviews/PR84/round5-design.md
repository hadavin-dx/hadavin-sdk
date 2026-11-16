# PR84 round 5 (head de18d59), egm-design (a25637c4). Snapshot only; nothing run.
Round-4 items closed: token masked in logs/summary (evidence_step.py mask, behavioural test), host-side readiness probe, no `root` fallback, loopback publish, removal by name, mask before GITHUB_ENV, no literal token, guard plants on both workflows.
BLOCKER 1: evidence logs inside git tree: evidence_step.py:29 LOG_DIR=Path("evidence-logs") relative to checkout root; evidence.yml:139,217 same; .evidence-tools/ nested checkout (evidence.yml:119-124). Use $RUNNER_TEMP via EVIDENCE_DIR env. (Reviewer: downgrade to Major if ORDER 175 only wants gitignore. ORDER 175 as written concerns my local evid.sh; lead to say.)
MAJOR 1: pyyaml imported in tests/test_evidence_workflow_guard.py:29; confirm declared+locked in test group.
MAJOR 2: guards are text checks: no-print rule only echo/printf; bypasses env, printenv, curl -v, docker inspect, shell: bash -x, ${!v}. Ban in Vault job or declare best-effort.
MAJOR 3: mask exact value only; truncated/split token passes; soften docstring or mask first/last 8.
Nits: reader check regex; redundant source-text test; last_test matches Verdict step not perf step; probe guard checks words only; add --security-opt no-new-privileges / --cap-drop ALL; token reaches all later steps (say so); curl argv accepted; ci tests-py312 has no fail-on-skip for Vault vars; zizmor github-env audit may flag GITHUB_ENV writes.
Not checked: ORDER 175/180 text, CLAUDE.md, real Vault, GitHub semantics, tests run.
