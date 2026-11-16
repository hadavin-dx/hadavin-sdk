# PLAN for ORDER 002 (n8n flows audit), plan round 2, 2026-11-16
Written after plan round 1 (reviews/plan-r1-findings.md, resolved in reviews/plan-r1-resolve.md). Static review: no n8n runtime, no network, made-up data only. "Static" means we read the saved flow files only; anything that needs a running n8n is tagged UNVERIFIED. "Demo" is the only stage name used.

## 1. Scope (no narrowing of the order)
Measured by `python3` json.load over handover/demo/n8n-*/**/*.json (raw output goes to evidence-1.md): 54 flow files, 655 nodes. EVERY node of EVERY file gets a row.
- Tier A (full judgement table, 130 nodes): n8n-flows-real-v5 (mf-form 12, mf-hook 12, mf-recovery 10, mf-sub-crm-mail 20), n8n-flows-film-v5 (12, 12, 10, 20), n8n-table-screen-v2/mf-table-screen-v2.json (4), n8n-flows/desk-webhook-door.json (8), desk-form-door.json (8), desk-error-notifier.json (2).
- Tier B (older versions, 525 nodes): n8n-flows (mf-* 4 files), n8n-flows-v3, -v4, -real, -real-v3, -real-v4, -film, -film-v3, -film-v4, n8n-flows/v1-superseded (3 files), n8n-table-screen (v1). Every node still gets a row with the machine columns only (type, parameters digest, edges, retry settings, credential name, store written); the judgement columns are filled only where the node differs from its successor version or where a current document still points at the folder. Superseded is proven by evidence: the folder is older than a named successor AND no current document or script (grep over handover/demo/*.md, n8n-mainframe/*.py, n8n-tests/*.py) opens it. A folder that fails the second test is reported as LIVE-REFERENCE.
- Scripts and generator in handover/demo/n8n-mainframe (build_mainframe.py, build_mainframe_v1.py, mf.py, run_mf.py, run_chain.py, stage_server.py, crm_stub.py, count_table.py) and handover/demo/n8n-tests/*.py: one inventory row each in section 4 of FLOWS-AUDIT.md (purpose, stores read/written, ports, secrets names, who calls it, still used or not). Checked: does build_mainframe.py regenerate the v5 json (the generator is the source of truth, so patches target it first).
- Claims files: handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md and handover/demo/VIDEO-RUNSHEET.md. Neighbouring earlier audits (handover/demo/AUDIT-PAGE-STATEMENTS-V4.md, AUDIT-VIDEO-RUNSHEET.md, claims-audit/, PAGE-STATEMENTS-V4-DRAFT.md, PAGE-STATEMENTS-DRAFT.md, V5-NODE-DIFF.txt) are NOT inputs for judgement (reviewer independence); they are read only after a verdict is written, to list agreements and disagreements.
- Store decision: DECISION-one-store.md is ABSENT (searched handover/). The only source is the order text: one database for the take = n8n Postgres plus table mf_leads; desk SQLite and portal retired from the take; stage.journal (a file) the one exception. Each store found is classified KEEP-ONE / RETIRED / EXCEPTION; an exception row carries reason, owner, removal trigger or is marked MISSING.
- Not in scope: running anything; editing anything outside handover/flows-audit/.

## 2. Rung table (CODE-LAST: our own code is the last resort)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| node extraction and diff | list nodes, edges, differences | standard library script, read-only on the json (tools/dump_nodes.py exists, 1 file) | script ran on one flow, see REPORT.md | nothing | CUT-TO-CONFIG+GLUE: extend that one script, no new tool |
| reachability and counts | dead nodes, totals | same script | to be produced in evidence-1.md | nothing | CUT-TO-CONFIG+GLUE |
| judgement per node | purpose, error path, idempotency, secrets | reading by sonnet builders | n/a | nothing | keep (agents read) |
| claims check | statement backed by a node | reading + grep | n/a | nothing | keep |
CUT-TO-CONFIG+GLUE means: use what exists and add only thin glue.

## 3. Files this work creates (the write allowlist; nothing else may be written)
All paths are under handover/flows-audit/.
| path | create/modify | owner |
|---|---|---|
| tools/dump_nodes.py | modify (add: table output, reachability, node-diff between two flow files, row counts per file, secret-value masking) | L0 |
| tools/out/*.md, tools/out/counts.txt | create (script output) | L0 |
| lanes/L1-mf-v5.md | create (Tier A, 4 mf flows real-v5 + film-v5, full tables for both) | L1 |
| lanes/L2-other.md | create (table-screen-v2, desk-* doors, Tier B tables and inventory, scripts inventory) | L2 |
| lanes/L3-claims.md | create (claims table, store table) | L3 |
| checkpoint-L1.md, checkpoint-L2.md, checkpoint-L3.md | create (done / next / blockers / commit sha, every 30 min) | each lane |
| FLOWS-AUDIT.md, FINDINGS.md | create (lead merge, section 7) | lead |
| patches/NNN-slug.patch | create (one per finding; NNN = finding number) | lead |
| evidence-1.md, evidence-2.md | create (raw output, no judgement) | evidence runner |
| reviews/*.md | create (reviewer reports saved by the lead) | lead |
| LEDGER-ROWS.md | create (ready-to-append blocker ledger rows; the real ledger is outside this folder, so the lead applies them) | lead |
| REPORT.md | modify (register, status blocks, FINAL) | lead |

## 4. Column schema (identical for all lanes; one table per flow file, heading `### <folder>/<file> (<n> nodes)`)
`# | node | type | purpose | trigger or upstream | inputs | outputs or downstream | error path | retry and timeout | idempotency key | writes (store, table or file) | secrets (credential or env NAME only) | reachable | finding id`
Cell words: `none` (checked, nothing), `UNVERIFIED: <what needs a runtime>` (never guessed), evidence cited as `file:node` or `file:line`. Parameter values that look like secrets or personal data are never copied; write `<masked>` and the key name.
Findings table (FINDINGS.md): `id | severity | class | where (file + node or file:line) | evidence | proposed fix (patch file or OWNER/IMPOSSIBLE reason) | status`. Classes: duplicate, dead, inconsistent, claim-not-backed, store, security, ops, unverified.
Severity rubric: Blocker = a take or a client could lose or double-apply a lead or mail, leak a secret or personal data, or a published claim is false. Major = wrong behaviour on a failure path, a second store for one job, a claim with no backing node. Nit = naming, dead leftovers that nothing runs, wording.

## 5. Lanes (parallel; input and output lists fixed; all sonnet; brief starts with the BRIEF-PREAMBLE line and a MUST-NOT list)
- L0 (lead, script only, first, minutes): extend tools/dump_nodes.py, write tools/out/*; produce counts.txt (files, nodes per file, total 655) and machine diffs: real-v5 vs film-v5 per file, each Tier B folder vs its successor.
- L1 builder: inputs real-v5 and film-v5 json + tools/out. Output lanes/L1-mf-v5.md. Full tables for BOTH folders (film-v5 rows may say `same as real-v5 <node>` only when tools/out shows an identical node; differing nodes get their own row). Hunts: error path of every node, retry and idempotency (lease, claim_token, ON CONFLICT), kill/restart/duplicate/out-of-order/empty input walks, loops and stop conditions (mf-recovery every 30 s), identity and secrets, real vs film inconsistencies.
- L2 builder: inputs table-screen-v2, desk-* json, all Tier B json, n8n-mainframe scripts, n8n-tests scripts. Output lanes/L2-other.md. Hunts: dead and unreachable nodes, idle flows and folders (LIVE-REFERENCE test in section 1), duplicated logic across flows and versions, desk-* doors vs mf-* entries (second path into the same store).
- L3 builder: inputs PAGE-STATEMENTS-V4.md, VIDEO-RUNSHEET.md, tools/out. Output lanes/L3-claims.md. A statement = one sentence or one table cell that asserts something checkable; numbered S1.. per file with source line. Verdict per statement: BACKED (file:node), NOT BACKED, UNVERIFIED (needs a runtime), INCONSISTENT (number or name differs from the flow). Store table: `store | engine | path or table | writers | readers | retention | classification (KEEP-ONE / RETIRED / EXCEPTION) | evidence`; stores searched in all json (postgres nodes, writeFile, http calls to desk or portal), scripts and the two claims files.
Dead-node rule: no incoming edge AND not a trigger AND not the target of an Execute Workflow node (sub-workflow entry) AND not an error-workflow target. Duplicate rule: same node type and same parameters (ignoring name and position) in 2 or more flows of the CURRENT version, or a different parameter set doing the same job (same SQL table and key) in 2 places. Idle rule: a flow or script no trigger, schedule, document or script reaches.
Time box: 60 minutes per builder; checkpoint-Ln.md every 30 min (done / next / blockers / sha); at 60 min stop, commit, report; a lane file is always complete up to a marked row `-- DONE UP TO ROW <n> --`; a successor resumes from the note.

## 6. Steps and gates (EGM order)
1 plan review: egm:egm-review-loop with egm:egm-design and egm:egm-implementation-readiness (max 3 rounds), then egm:egm-resolve. 2 L0 script. 3 L1, L2, L3 builders in parallel. 4 EVIDENCE RUNNER (sonnet, brief says EVIDENCE RUNNER, runs only, never judges, writes evidence-1.md as command, exit code, raw output): (a) script rerun, counts per file and total equal the table row counts in lanes (python compares); (b) every node name in the lane tables exists in its json; (c) every `file:line` and `file:node` in FINDINGS.md resolves; (d) every patch passes `git apply --check` against a scratch copy of the target and the patched json still parses; (e) secret-pattern grep (bearer, key-like, connection string patterns) over everything new returns nothing; (f) no file outside handover/flows-audit/ changed (git status and git diff --stat against the start sha). 5 result review by fresh reviewers egm:egm-codebase-details, egm:egm-design, egm:egm-zoom-out (duplicates and dead things) reading FLOWS-AUDIT.md, FINDINGS.md, lanes, evidence and a snapshot copy path with the head sha; they get no builder verdict; the lead saves their reports to reviews/. 6 egm:egm-resolve; fix every Blocker and Major; max 2 result rounds for this static audit (findings are about money or secrets, so a Blocker found in round 2 is escalated to the lead, not dropped). 7 egm:egm-drift-report, output reviews/drift-report.md. At plan round 3 with a Blocker still open: stop and escalate to the lead.
Merge (lead): FLOWS-AUDIT.md = section 1 master map (folders, files, counts, flows, loops and schedules, stores, scripts, credential names, ports) + lane tables concatenated in file order + section 4 inventory. FINDINGS.md = rows from the lanes, de-duplicated, ranked. The lead does not review its own merge: step 5 reviewers do.
Patch rule: a patch is a unified diff against the repo file it fixes; flow json fixes go to handover/demo/n8n-mainframe/build_mainframe.py first (generator is the source) and the regenerated json diff is attached only if the generator can be run here; otherwise the patch to the json is marked UNVERIFIED (not regenerated).

## 7. Stop rule
A fresh reviewer pass with no Blocker or Major; evidence-1.md checks (a) to (f) all pass; every finding has evidence and a patch file or an OWNER/IMPOSSIBLE reason; every item needing a runtime is UNVERIFIED; FINAL block in REPORT.md pushed.

## 8. MUST-NOT for every agent
No write outside the section 3 allowlist; no write to handover/demo; no moving or deleting flow files; no push or merge by sub-agents (the lead commits and pushes to cloud/flows-audit only); no secrets, no network, no n8n runtime, no live model call; never copy a secret value (report the node and key name only); no claim of done without raw output; every Agent call sets the model (sonnet default; haiku only for plain lookups; opus only inside the egm planning skills); the lead registers each agent in REPORT.md before starting it and writes a status block (UTC and IST) every 10 minutes with a push.
