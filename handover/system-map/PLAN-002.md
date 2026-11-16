# PLAN for ORDER 002 (system-map), 2026-11-16 06:47 UTC / 12:17 IST. STATIC review: no runtime, no network, made-up data only.
Ladder line (rung table, CODE-LAST): all work is reading and grep plus a small checker script; no product code written. Rung 1 reuse: ARCHITECTURE-AUDIT-CHECKLIST.md and DECISION-one-store.md are the method and the baseline. KEEP-CODE: only the citation checker (evidence runner), because nothing higher covers "does each file:line quote exist".

## Outputs (all in handover/system-map/)
1. MASTER-MAP.md  whole system as the repo shows it: components, stores, workflows (node by node), scripts, jobs/loops, credentials (names only), ports, docs, tests, agents/sessions, repos/branches. Each row: purpose, owner, in/out, failure path, retry, identity, where tested, evidence (file:line).
2. SWEEP.md  duplicates, dead, idle, inconsistent, unverified claims, security, ops. Each hit: id, severity, file:line, short quote, what it conflicts with.
3. ONE-PLACE-TABLE.md  jobs (store, log, filter, counter, retry engine, notice, plus anything the sweep finds): single owner, every extra copy, verdict NEEDED / DUPLICATE / NOT-NEEDED / CRM-COULD-DO, cut-or-archive proposal (never delete). Checked against DECISION-one-store.md.
4. patches/ only if a fix is proposed (lead applies). Not visible: the "take code repo" duplicate-proof-lead-desk (listed, not guessed).

## Lanes (parallel, non-overlapping inputs, one writer per file, sonnet, read-only; each writes ONLY handover/system-map/work/<lane>.md)
L1 handover/demo (ORDERS, REPORT 660 KB, APPLY-LIST, pr-text, pr-stack, followup, merge-ready, speed, reuse, drift)
L2 handover/demo3 kill/ (flows-go1 node walk, mf_leads.sql, harness, run_*.sh, data/results, RESULTS.md) = the workflow walk
L3 handover/demo3 evidence/ + tools/ + scratch + register/MATRIX/REPORT/ORDERS (lane3 fix r1..r12 patch chains, checkpoints)
L4 handover/demo evidence folders: layout, sonar, triage, semgrep, coverage, skips, hang, integration, real-run, xss, outsider*, stranger, gitleaks, scans, fixes
L5 repo outside handover/: src/hadavin_sdk, demos/ask-your-data, tests, tools, docs, .github/workflows, .claude hooks and rules, handover/tools (stores, logs, retry, counters, filters, notices: grep by job)
Lead (me): merge lanes into the 3 outputs, resolve conflicts, check DECISION-one-store.

## Stop rules
Plan review max 3 rounds then egm-resolve; stop plan after round with 0 Blockers. Build time box 60 min per lane (checkpoint note every 30 min). Then EVIDENCE RUNNER (sonnet, runs script check_citations.py that opens every cited file:line and records found / not found / quote mismatch, never judges). Then fresh egm:* reviewers (codebase-details, zoom-out, comprehension; direct dispatch, sonnet) read outputs + evidence; egm-resolve; max 2 result rounds; fix every Blocker and Major.
Heavy jobs: none (grep/read only). Max agents at once: 5 lanes + 0.
Claims never made without file:line; anything needing a runtime is marked UNVERIFIED.
