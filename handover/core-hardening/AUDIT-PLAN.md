# AUDIT PLAN (ORDER 002 part 1): architecture audit of the hadavin-sdk core (static, no runtime)
Ladder line: rung 1 (reuse): reading and grep/AST scripts only; no new product code. Nothing outside handover/core-hardening/ is edited; fixes are patch files here.

## Goal
Lead gets evidence-backed findings: (a) MASTER-MAP.md of every module, kind, store, log, script, job, test, doc, hook and credential path; (b) AUDIT-FINDINGS.md table: id, severity, evidence file:line, proposed fix, verdict NEEDED / DUPLICATE / NOT-NEEDED / CRM-COULD-DO. Claims with no evidence are marked UNVERIFIED.

## Scope (non-overlapping, one writer per file)
- Lane A (security paths): src/hadavin_sdk/actions, approvals, audit, guard
- Lane B (state and runtime): store, backends, runtime, k1b, sources, registry.py, deferred.py
- Lane C (models and top level): llm, app.py, cli.py, config.py, defaults.py, evals.py, extract.py, hashing.py, identity.py, limits.py, models.py, replay_records.py, scrub_settings.py, stats.py, tools.py, errors.py
- Lane D (everything around code): tests/, demos/, docs/, .github/, .claude/ (rules, hooks, settings), pyproject.toml, README/SECURITY/CHANGELOG, handover/ top-level index only (file names, not the 16k evidence files; handover/core-hardening excluded)
Each lane writes handover/core-hardening/parts/map-<lane>.md and parts/findings-<lane>.md. I (lead of this session) merge them.

## Steps
1. Plan review: egm:egm-review-loop (design_critic + implementation_readiness), then egm:egm-resolve. Max 3 rounds.
2. Evidence script (EVIDENCE RUNNER, sonnet): import graph, modules never imported, functions never referenced, test-to-module map, duplicate store/log paths grep, doc claim numbers (counts, versions, ports) vs code. Raw output to parts/evidence-1.md. Runs, never judges.
3. 4 builders (sonnet) in parallel, one per lane, 60 min box, checkpoint note every 30 min. They read the evidence file but must open the code themselves for each finding.
4. Merge into MASTER-MAP.md and AUDIT-FINDINGS.md. Checklist items covered: master map, DUPLICATES, DEAD/IDLE, INCONSISTENT, UNVERIFIED, STORE RULE, SECURITY, OPS. WORKFLOW WALK: the core has no n8n flow; the nearest are runtime/agent_loop, plan, tick and the approval path; walked in lanes A and B.
5. Result review: egm-codebase-details, egm-zoom-out (duplicates/dead), egm-design, egm-comprehension (fresh agents, read the two files + evidence, never my verdict). egm-resolve. Max 2 result rounds; security/money/redaction items uncapped.
6. Findings go in handover/ledger.md ONLY via patch file (outside my folder): handover/core-hardening/patches/ledger-rows.md.

## Rules for every brief
Starts with STUDIO-PREAMBLE v1 and EGM-GATE v1 text. MUST-NOT: edit any file outside handover/core-hardening/parts/<own files>; run git commit/push; call any model or network; print or copy a secret value (names only); run tests that rewrite files; write "known limitation" instead of a finding. Every finding needs file:line; unverified claims are labelled UNVERIFIED.

## Stop rule
No Blocker or Major left open from a fresh egm pass, or max rounds reached with the rest listed. FINAL block in REPORT.md.
