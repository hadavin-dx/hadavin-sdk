# checkpoint-B (lane B, state and runtime). Audited sha b4cce5b (HEAD on disk at start: 1c50990, only handover/core-hardening/ differs).
Start 2026-11-16 07:03 UTC (12:33 IST). Checkpoint written 07:09 UTC (14:39... see IST column in final report: 12:39 IST).

## Done (opened and read in full unless noted)
- runtime/: agent_loop.py (all 869 lines), runs.py, plan.py, tick.py, evidence.py (walk of the agent loop done first)
- store/: protocol.py, memory.py, postgres.py, auth_aws.py, migrate.py, all five migrations
- backends/: builtin.py, factory.py, platform_secrets.py, __init__.py, table.py (all)
- registry.py (all), deferred.py (all)
- k1b/: audit_sink.py, causelist.py, atomic.py, bundle.py, redaction.py, replay.py, loop.py; tools.py/score.py/diagnosis.py (first 50-130 lines and grep only)
- sources/: __init__.py, kinds.py, kubernetes.py (lines 1-100 and 100-351)

## Next
- k1b report.py, rest of score.py/tools.py (leaf code), evidence section 5/6 hit-by-hit exclusions, then write map-B, findings-B, claims-B, walk-B.

## Blockers
- None. Nothing was run (no pytest, no repo code). Tests are only grepped, never run, so "test found" never means "test passes".
