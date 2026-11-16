# PLAN for ORDER 002 (flows audit), written 06:47 UTC / 12:17 IST, plan round 1
Stage names: demo only. Static review: no n8n runtime; anything needing one is UNVERIFIED.

## Scope (measured)
Current flows: handover/demo/n8n-flows-real-v5 (4 json, 54 nodes), n8n-flows-film-v5 (4 json, 54 nodes), n8n-table-screen-v2 (1 json, 4 nodes), generator n8n-mainframe/build_mainframe.py. Other flow json: n8n-flows (desk-webhook-door, desk-form-door, desk-error-notifier, v1-superseded), and v3/v4/real/film older folders: classified as superseded or live by evidence, not audited node by node unless still referenced by a current doc. Claims: n8n-flows/PAGE-STATEMENTS-V4.md, VIDEO-RUNSHEET.md. Decision: one store (n8n Postgres + mf_leads; desk SQLite and portal retired from the take; stage.journal the one exception).

## Rung table (CODE-LAST v1)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| node table extraction | list every node, params, edges | script (python json, standard library) | node counts above from json.load | nothing | CUT-TO-CONFIG+GLUE: one throwaway script in this folder, not product code |
| claim-to-node check | each claim backed by a node | read + grep | n/a | nothing | manual read by agents |
| node-by-node judgement | purpose, error path, retry, idempotency, store, secrets | reviewer reading | n/a | nothing | agents read table + json |

## Lanes (parallel, non-overlapping output files)
L1 builder (sonnet): extraction script, then FLOWS-AUDIT.md tables for the 4 mf-* flows (real-v5 as base, film-v5 as diff only).
L2 builder (sonnet): table-screen-v2, desk-* flows, superseded-version inventory (which folders are referenced by which docs: dead/idle hunt) -> section files.
L3 builder (sonnet): claims check: every statement in PAGE-STATEMENTS-V4.md and VIDEO-RUNSHEET.md mapped to a node/file or marked NOT BACKED; two-store problem (every store named in the flows and docs) -> claims file.
Lead (me) merges into FLOWS-AUDIT.md and FINDINGS.md; patch files in handover/flows-audit/patches/.

## Steps and gates
1 plan review (egm-review-loop, max 3 rounds) then egm-resolve. 2 build (60 min box, checkpoint 30 min). 3 EVIDENCE RUNNER (sonnet, only runs scripts and greps, saves raw output to evidence-1.md, never judges). 4 two fresh egm reviewers (codebase-details + design, zoom-out for duplicates) read FLOWS-AUDIT.md, FINDINGS.md, evidence. 5 resolve; fix blockers/majors; max 2 result rounds. 6 drift report. 

## Stop rule
No Blocker or Major open from a fresh reviewer; every finding has evidence (node name or file:line) and a patch file or an OWNER/IMPOSSIBLE reason; every non-verifiable item marked UNVERIFIED.

## MUST-NOT for all agents
No edits outside handover/flows-audit/; no push/merge; no secrets; no network; no n8n runtime; no claim of done without raw output.
