# Checkpoint: hand-off v8 (2026-11-16)

Start about 13:45 UTC (19:15 IST). Checkpoint 1 at 13:50 UTC (19:20 IST) (clock read with `date -u`).
Done: read the brief, the preamble, v7 in full, both v7 reviews, v7-CHANGES.md, the v7 import-graph program and its output. Re-read the cited code before changing a claim: llm/common.py (40-70, 150-330), llm/openai_compat.py (20-160), llm/anthropic.py (100-135), llm/bedrock.py (85-120), llm/retry.py (25-110), models.py (15-60, 280-312), limits.py (whole), config.py (30-60), registry.py (25-60, 335-352), store/migrate.py (25-420, whole control flow incl. the purge role at 395-410), store/postgres.py (120-200, 395-445), store/protocol.py, app.py (120-200), backends/table.py (66-125, 591-604), runtime/agent_loop.py (180-222, 300-345), cli.py (165-215), audit/signer.py (98-112, 190-212), k1b/replay.py (80-95), tests k5_support, test_k3_pilot, test_k5_fixes1, test_p6_detectors, test_p5p6_followups, tests/contracts/kinds/store_postgres.py and detectors.py.
Found: v7 line 309 is stale (NetworkLLM.chat and _chat already exist, common.py:208-231; Reply is a pydantic Shape); Grant has the fields kind, runtime, portal, purge, purge_cols (not runtime_privileges); the Postgres store is ONE connection behind ONE threading lock (postgres.py:191-197), so the reviewer's "do not hold the Python lock across the wait" cannot be done as worded (a second thread's statement would join the open transaction); the fix is a lock_timeout bound plus a named trigger for a second connection.
Wrote and ran (read-only, AST): evidence-handoff-v8/import_graph_v8.py and raw-import-graph-v8.txt (today: 1 cycle, approvals; v8 shape: no new cycle; v6 shape: llm.common <-> llm.gate).
Next: write CORE-PR-HANDOFF-v8.md and v8-CHANGES.md; re-check the citation file if it exists; count banned strings; report.

## Checkpoint 2 (final), 14:03 UTC (19:33 IST)
Done: CORE-PR-HANDOFF-v8.md and v8-CHANGES.md written; the coordinator's six citation fixes applied (plus the E0-12 trivially-true note); citation-check-v7.md read (6 rows, all fixed). Assembled from v7 line ranges with exact-once replacements (zero replacement misses) plus new text for the head, section 0, 4.1, 4.2, section 5 and section 7.
Not done / not run: no test, ruff, bandit or Postgres; all Postgres behaviour specified, unverified. No independent review (the lead runs it).
Deviation from my own earlier plan: dropped the new class SpendBookkeepingError (reason in 4.2).
Stopped at about 18 minutes of the 60-minute box; reporting now.
