# Checkpoint: hand-off v5 (2026-11-16)

Start 12:52 UTC. Checkpoint 1 at about 13:10 UTC.
Done: read v4, security review (5 blockers, 10 majors), readiness review (0 blockers, 7 majors, nits; it landed at 12:53 UTC and IS covered), citation check (9 failures), window-end audit and review, G-rules evidence. Re-read in the source: limits.py, llm/common.py, llm/retry.py, llm/protocol.py, app.py, cli.py, config.py, extract.py, guard/runmap.py, guard/injection.py, guard/judge.py, evals.py, store (memory, postgres, protocol, migrations list), agent_loop.py sites, audit/chain.py verify path, anchor_s3/gcs/azure, actions/secrets_file.py, audit/signer.py, approvals/gate.py, backends/table.py. Scratch regex compile only (stdlib re, in the scratchpad), no repo code run.
Next: write CORE-PR-HANDOFF-v5.md and v5-CHANGES.md, re-open every cited line, report.
Blockers: none. Commit SHA: none (no git here; the lead commits).
