# Checkpoint: hand-off v6 (2026-11-16)

Start 13:07 UTC (18:37 IST). Checkpoint 1 at 13:10 UTC.
Done: read v5, both v5 reviews, citation check v5, ORDERS.md lines 185-198 (core paused; hand-off not on the demo's critical path). Opened in source: llm/common.py, retry.py, protocol.py, anthropic.py, bedrock.py (88-160), fake.py, limits.py, app.py (60-250), cli.py (60-260, 383-410), backends/factory.py, backends/table.py (llm entries, ALLOWED), store/migrate.py (GRANTS, grant apply), store/protocol.py, memory.py and postgres.py spend methods, migrations 0001 and 0003 spend DDL, agent_loop.py sites, k1b/loop.py, guard/judge.py, guard/injection.py, evals.py, config.py (Money, Config, anchor refusals), defaults.py, tests that build Limits and Store doubles.
Decisions taken (to be written in v6): per-attempt reservation inside the shared retry choke point; totals computed from append-only spend_op under a per-agent advisory lock; run cost in the same transaction; gate reaches kinds through Deps; k1b keeps its own Budget under a window-only scope.
Next: write CORE-PR-HANDOFF-v6.md, v6-CHANGES.md, run banned-string count, report.
Blockers: none. No commit (no git here; the lead commits).
