# Ledger rows proposed by core-hardening (7 columns like handover/ledger.md: id | package | severity | summary | status | verifying artifact | reviewed commit). The checklist asks for 9 columns: lead decides. Only Blockers and the confirmed or money/approval Majors; all other Majors are in AUDIT-FINDINGS.md.

| id | package | severity | summary | status | verifying artifact | reviewed commit |
|---|---|---|---|---|---|---|
| core-hardening-A-01 | audit | Blocker | audit outbox events never reconciled in production (chain.py:216-232) | OPEN | AUDIT-FINDINGS.md A-01; cross.md re-read | b4cce5b |
| core-hardening-A-02 | redaction | Blocker | second redaction check G5 promised, no code (redact.py:15-17, gate.py:42-63) | OPEN (reword patch ready: patches/C-01-and-A-02.patch) | same patch; cross.md | b4cce5b |
| core-hardening-B-01 | runtime | Blocker | disabled_sources is a per-process set (tick.py:235); other process may not see it. UNVERIFIED process layout | OPEN | cross.md X-04 | b4cce5b |
| core-hardening-C-01 | money | Blocker | zero or negative model price turns spend limits off (config.py:55-60, limits.py:20-29) | OPEN (patch ready, ruff check and format pass, tests not run) | patches/C-01-and-A-02.patch | b4cce5b |
| core-hardening-D2-01 | demo | Blocker | demo ask bypasses kill switch, meter, audit, ledger (cli.py:255-278) | OPEN (lead decides severity) | cross.md | b4cce5b |
| core-hardening-A-03 | approval | Major | Runtime.execute trusts the approval argument (agent_loop.py:760-846, executor.py:111-114) | OPEN | cross.md | b4cce5b |
| core-hardening-X-02 | money | Major | spend checked before the model call, charged after, in 3 loops (agent_loop.py:421-440, k1b/loop.py:40-52, evals.py:73-84); lead may raise to Blocker | OPEN | cross.md | b4cce5b |
| core-hardening-X-16 | approval | Major | one database role does agent work, approvals, kill switch and spend UPDATE (migrate.py:50-55); lead may raise to Blocker | OPEN (owner yes needed) | cross.md | b4cce5b |
| core-hardening-D3-01 | repo-guard | Major | banned vendor strings under handover/ make tests/test_no_reference_material.py fail (static reading) | OPEN | AUDIT-FINDINGS.md D3-01 | b4cce5b |
| core-hardening-X-15 | repo-guard | Major | same guard: audit files themselves quoted the strings; scrubbed in handover/core-hardening | FIXED-UNVERIFIED (script grep 0 left; guard test not run) | grep result in REPORT.md | b4cce5b |
