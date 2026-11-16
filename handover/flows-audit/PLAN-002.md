# PLAN for ORDER 002 (n8n flows audit), plan round 3, 2026-11-16
Round 2 resolved in reviews/plan-r2-resolve.md. Static review: we read saved flow files only; nothing runs, no network, made-up data only. Anything that needs a running n8n is tagged UNVERIFIED. "Demo" is the only stage name used. Correction of my own slip: round 1 and 2 said 54 flow files; the real count is 52 files and 655 nodes (54 was the node count of one v5 folder).

## 1. Scope
Exact file set: every `*.json` that holds a `nodes` list under `handover/demo/n8n-*/`, EXCLUDING `handover/demo/n8n-tests/` (5 test-result json there are not flows). Counts come from `python3 tools/dump_nodes.py counts handover/demo` (raw output in evidence-1.md).
| folder (under handover/demo) | files | nodes | tier | successor (diff partner) |
|---|---|---|---|---|
| n8n-flows-real-v5 | 4 | 54 | A | none (current; partner for diff: n8n-flows-film-v5) |
| n8n-flows-film-v5 | 4 | 54 | A | none (current) |
| n8n-table-screen-v2 | 1 | 4 | A | none |
| n8n-flows (desk-webhook-door 8, desk-form-door 8, desk-error-notifier 2) | 3 | 18 | A | none (no counterpart) |
| n8n-flows (mf-form, mf-hook, mf-recovery, mf-sub-crm-mail) | 4 | 51 | B | n8n-flows-v3 |
| n8n-flows/v1-superseded | 3 | 53 | B | n8n-flows (mf-*) |
| n8n-flows-v3 | 4 | 52 | B | n8n-flows-v4 |
| n8n-flows-v4 | 4 | 53 | B | n8n-flows-real-v5 |
| n8n-flows-real | 4 | 51 | B | n8n-flows-real-v3 |
| n8n-flows-real-v3 | 4 | 52 | B | n8n-flows-real-v4 |
| n8n-flows-real-v4 | 4 | 53 | B | n8n-flows-real-v5 |
| n8n-flows-film | 4 | 51 | B | n8n-flows-film-v3 |
| n8n-flows-film-v3 | 4 | 52 | B | n8n-flows-film-v4 |
| n8n-flows-film-v4 | 4 | 53 | B | n8n-flows-film-v5 |
| n8n-table-screen | 1 | 4 | B | n8n-table-screen-v2 |
Total 52 files, 655 nodes (Tier A 130, Tier B 525). The per-folder node numbers above are the lead's own quick sums; check (a) in section 6 is the oracle and any difference is fixed in the plan, not argued. Order of versions = folder version suffix and the README text inside the folder (V5-README.md and similar); file dates are not used.
Files that are not flows but are inputs: handover/demo/n8n-flows/mf_leads.sql (the schema of the one store), N8N-START.md, DESIGN-A-README.md, v1-superseded/README.txt, n8n-table-screen*/README.md, n8n-flows-real-v5/V5-README.md and V5-NODE-DIFF.txt (the diff file is an unverified claim to be checked against the machine diff, not a source).
Scripts: handover/demo/n8n-mainframe (build_mainframe.py, build_mainframe_v1.py, mf.py, run_mf.py, run_chain.py, stage_server.py, crm_stub.py, count_table.py) and handover/demo/n8n-tests/*.py (build_flows, desk_proxy, dn1, dn1_common, run_dn1, runcfg, smtp_catcher, test_crmid_regex, test_envpass and any others found): one inventory row each (purpose, stores read or written, ports, secret names, caller, still used or not). Generator check: rebuild real-v5 and film-v5 into tools/scratch/ with the exact commands in n8n-flows-real-v5/V5-README.md (placeholder ids as written there) and diff against the saved json; if it cannot run here, UNVERIFIED.
Claims files: handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md and handover/demo/VIDEO-RUNSHEET.md. Earlier audits (handover/demo/AUDIT-PAGE-STATEMENTS-V4.md, AUDIT-VIDEO-RUNSHEET.md, claims-audit.md, claims-audit/ folder if present, claims-code-bugs.md, PAGE-STATEMENTS-V4-DRAFT.md, PAGE-STATEMENTS-DRAFT.md) are NOT inputs to a verdict; only the lead reads them, after verdicts are written, for the agreement list (FLOWS-AUDIT.md section 5).
Store decision: DECISION-one-store.md is ABSENT (searched handover/). Only source = order text: one database for the take = n8n Postgres plus table mf_leads; desk SQLite and portal retired from the take; stage.journal (a file) the one exception. Every store found is classified KEEP-ONE, RETIRED or EXCEPTION; an exception needs reason, owner, removal trigger or is marked MISSING.
Scope decision for lead acceptance (QUESTIONS.md Q1): for Tier B (525 nodes) every node gets a row with machine columns pasted unchanged from the script; judgement columns are filled only where a mechanical diff against the successor shows ANY change in type, parameters, credentials, onError/retry settings or edges, or where the file has no counterpart; an identical node says `same as <successor-folder>/<file>:<node> (machine diff identical)`. This is mechanical, not a judgement call. If the lead wants full judgement for all 525, say so and the lane is resized.
Not in scope: running anything; editing outside handover/flows-audit/.

## 2. Rung table (our own code is the last resort)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| node table, counts, diff, reachability | machine facts per node | python standard library on the json | tools/dump_nodes.py ran on 3 files in this session (counts 655, diff real/film, table of mf-recovery); no REPORT line before, now logged in evidence-1.md | nothing | CUT-TO-CONFIG+GLUE: extend the one existing script, no new tool |
| judgement per node | purpose, error path, idempotency | agents reading | n/a | nothing | keep |
| claim check | statement backed by node | agents reading + grep | n/a | nothing | keep |
CUT-TO-CONFIG+GLUE = use what exists, add only thin glue.

## 3. Write allowlist (all under handover/flows-audit/; nothing else may be written; builders never use git)
| path | what | owner |
|---|---|---|
| tools/dump_nodes.py | modify: subcommands table, counts, diff, check; CLI in section 5 | L0 |
| tools/mask_patterns.json | create: key-name regex and value regexes used by every script and by check (e) | L0 |
| tools/fixtures/*.json, tools/test_dump_nodes.py | create: 4 test cases (section 5) | L0 |
| tools/check_counts.py, check_names.py, check_refs.py, check_secrets.py, check_patches.sh | create: evidence checks (section 6) | L0 |
| tools/out/<folder>__<file>.md, tools/out/diff__<a>__<b>.txt, tools/out/counts.txt | create: script output, machine columns | L0 |
| tools/scratch/ | scratch for generator rebuild and patch checks; not committed | evidence runner |
| lanes/L1-mf-v5.md, lanes/L2a-tierA-extras.md, lanes/L2b-tierB.md, lanes/L3-claims.md | create | L1, L2a, L2b, L3 |
| checkpoint-L1.md, checkpoint-L2a.md, checkpoint-L2b.md, checkpoint-L3.md | create every 30 min: done / next / blockers / row marker (no sha) | each lane |
| FLOWS-AUDIT.md, FINDINGS.md, FIX-PLAN.md, CUT-LIST.md, EXCEPTIONS.md, LESSONS.md, LEDGER-ROWS.md | create (lead merge) | lead |
| patches/F-NNN-slug.patch | create, one per finding | lead |
| evidence-1.md (after builders), evidence-2.md (after fixes) | create, raw output | evidence runner |
| reviews/*.md, snapshot/ (copy of deliverables, committed, with head sha in snapshot/HEAD.txt) | create | lead |
| REPORT.md, QUESTIONS.md | modify | lead |
The lead alone commits and pushes (branch cloud/flows-audit). The start sha is recorded in REPORT.md before L1.

## 4. Column schema (identical in all lanes; one table per flow file, heading `### <folder>/<file> (<n> nodes)`; every node a row, disabled nodes included; no sticky-note nodes exist in the 52 files)
Machine columns, pasted unchanged from tools/out (never retyped): `# | node | type | parameters (masked) | downstream (out,node) | onError | retry/tries/wait | disabled | credential name | reachable`.
Judgement columns, filled by the lane: `purpose | trigger or upstream | inputs | outputs | error path | idempotency key | writes (store, table or file) | secrets (names only) | identity it runs as | logs to | what a person sees | stop condition | finding id`.
Vocabulary: reachable = Y | NO-INCOMING | UNREACHED-FROM-TRIGGER | ENTRY | ERROR-TARGET; retry = retryOnFail/maxTries/waitBetweenTries, or `none`; any other cell = a sentence, `none` (checked, nothing) or `UNVERIFIED: <what needs a runtime>`; evidence cited as `file:node` or `file:line`. Secret-looking values and personal data are never copied: write `<masked>` plus the key name. Masking rule = tools/mask_patterns.json only (key names matching token, secret, password, apikey, authorization, bearer; values matching Bearer text, 32+ character key-like strings, connection strings with a scheme and credentials); URLs, SQL text and credential NAMES are copied.
FINDINGS.md columns: `id | severity | class | where (file + node, or file:line) | evidence | proposed fix (patch file or OWNER/IMPOSSIBLE reason) | status`. Id = F-001, F-002 ... numbered by the lead after de-duplication. Classes: duplicate, dead, inconsistent, claim-not-backed, store, security, ops, unverified.
Severity: Blocker = a take or client could lose or double-apply a lead or mail, leak a secret or personal data, or a published claim is false. Major = wrong behaviour on a failure path, a second store for one job, a claim with no backing node. Nit = naming, leftovers nothing runs, wording.
LEDGER-ROWS.md (9 columns, per the blocker ledger rule): `id | source | severity | area | summary | status | fixing artifact | verified-by | date`.

## 5. Script interface and its tests (L0, first)
`python3 tools/dump_nodes.py table <json>...` (one markdown table per file, section 4 machine columns, masked); `counts <root>` (per-file node counts, total, parse failures; excludes n8n-tests); `diff <a.json> <b.json>` (keyed by node NAME; compares type, typeVersion, parameters, credentials, onError, retry fields, disabled, edges; ignores position and node id); `check <json>` (exits 1 on dangling edge, duplicate node name, unparsable file). Entry nodes = types ending webhook, scheduleTrigger, executeWorkflowTrigger, errorTrigger, or any type containing "trigger"; error target = the node an errorTrigger flow starts from or `settings.errorWorkflow`. Dead-node rule: no incoming edge AND not an entry AND not reached from an entry. Output files named `tools/out/<folder>__<file>.md`.
Tests (tools/test_dump_nodes.py, fixtures in tools/fixtures/): (1) a flow with one orphan node must give NO-INCOMING; (2) an executeWorkflowTrigger flow must give ENTRY, not dead; (3) an errorTrigger flow must give ENTRY for the trigger; (4) a node with `password` and a 40-character value must print `<masked>`. Expected outputs are stored next to the fixtures. Run with `python3 tools/test_dump_nodes.py`, exit 0.

## 6. Lanes, steps and gates (EGM order; all agents sonnet; every brief starts with the BRIEF-PREAMBLE line `STUDIO-PREAMBLE v1 | EGM-GATE v1 | CODE-LAST v1` and the MUST-NOT list; the lead registers each agent in REPORT.md before starting it; status block with UTC and IST every 10 minutes with a push)
1 plan review (done twice; round 3 now), `egm:egm-review-loop` with `egm:egm-design` and `egm:egm-implementation-readiness`, then `egm:egm-resolve`. At plan round 3 with a Blocker still open: stop and tell the lead.
2 L0 (lead, script only): build tools, produce tools/out for all 52 files, counts.txt, machine diffs (real-v5 vs film-v5 per file; each Tier B folder vs successor per table in section 1).
3 Builders in parallel, 60 minute box, checkpoint note every 30 minutes, stop at 60 and report; a lane file is always complete up to a marked row `-- DONE UP TO <file>:<row> --`; a lane may be resumed ONCE by a fresh agent launched by the lead from the note.
- L1: inputs real-v5, film-v5 json + tools/out. Output lanes/L1-mf-v5.md: full tables for BOTH folders (a film row may say `same as real-v5 <node> (machine diff identical)` only when the diff file shows identical). Hunts: error path of every node, retry and idempotency (lease, claim_token, ON CONFLICT), kill/restart/duplicate/out-of-order/empty-input walk per flow, loops and stop conditions (mf-recovery every 30 s), identity and secrets, real vs film inconsistencies (cause: generator variant MF_REAL; reported as class inconsistent, EXCLUDED from the duplicate rule).
- L2a: inputs table-screen-v2, desk-* doors, n8n-mainframe and n8n-tests scripts, mf_leads.sql, README files. Output lanes/L2a-tierA-extras.md: full tables for 3 + 1 files (22 nodes), script inventory, generator check, second-path hunt (desk doors vs mf entries writing the same store).
- L2b: inputs all Tier B json + diff files + tools/out. Output lanes/L2b-tierB.md per the Tier B rule in section 1; dead and idle hunt; LIVE-REFERENCE test = a folder or file name found with word-boundary regex `(?<![\w-])NAME(?![\w-])` in any text file under handover/ (md, txt, py, sh, json) or in an Execute Workflow or errorWorkflow reference; a folder with a hit is LIVE-REFERENCE (hit listed), otherwise SUPERSEDED (evidence: successor named in section 1 and zero hits).
- L3: inputs PAGE-STATEMENTS-V4.md, VIDEO-RUNSHEET.md, all current json (Tier A), mf_leads.sql, the scripts, tools/out. Output lanes/L3-claims.md. A statement = one sentence or table cell asserting something checkable; numbered S1.. per file with source line. Verdict: BACKED (file:node), NOT BACKED, UNVERIFIED (needs a runtime), INCONSISTENT (number or name differs from a flow). Store table: `store | engine | path or table | writers | readers | retention | classification (KEEP-ONE / RETIRED / EXCEPTION) | evidence`, searching every postgres node, file write, http call to desk or portal, script and the two claims files.
Hunt rules: duplicate = same node type and same parameters (ignoring name, position, id) in 2 or more flows of the current version (real-v5 vs film-v5 pair excluded), or a different parameter set doing the same job (same SQL table and key) in 2 places, with both nodes cited; idle = a flow or script that no trigger, schedule, document or script reaches; the lane builder cites the evidence and the lead rules in merge.
4 EVIDENCE RUNNER (sonnet; brief says EVIDENCE RUNNER; runs only, never judges; writes evidence-1.md as command, exit code, raw output): (a) `python3 tools/check_counts.py` = per-file and total node counts from the script equal 52 files / 655 nodes and equal the row counts in the lane tables; (b) `check_names.py` = every node name in a lane table exists in its json and the machine columns equal tools/out cell for cell; (c) `check_refs.py` = every `file:line` and `file:node` in FINDINGS.md and lanes resolves; (d) `check_patches.sh` = every patch passes `git apply --check` against a copy in tools/scratch/ and the patched json parses; (e) `check_secrets.py` = tools/mask_patterns.json patterns found in no new file (0 hits); (f) `git status` and `git diff --stat <start sha>` list only paths in section 3; (g) `python3 tools/test_dump_nodes.py` exit 0.
5 Result review: fresh `egm:egm-codebase-details` (do the tables match the json and scripts), `egm:egm-design` (are findings real, store and claims verdicts right) and `egm:egm-zoom-out` (duplicates, dead and idle, anything left out) read snapshot/ (head sha in snapshot/HEAD.txt), evidence-1.md and the order; they get no builder verdict; the lead saves their reports to reviews/. The lead does not review its own merge.
6 `egm:egm-resolve`; fix every Blocker and Major; evidence-2.md after fixes. Round caps: findings about security, money, mail or redaction have NO cap (the order allows a cap of 2 only for other paths; where the checklist and the order differ, the stricter one applies and the lead is told); other findings max 2 rounds. 7 `egm:egm-drift-report`, output reviews/drift-report.md.
Merge (lead): FLOWS-AUDIT.md = section 1 master map (folders, files, counts, flows, loops and schedules, stores, scripts, credential names, ports, external systems and hosts, docs and specs, tests, identities, owner of each job) + lane tables in file order + script inventory + section 5 agreement list with earlier audits. FINDINGS.md = lane findings de-duplicated and ranked. FIX-PLAN.md = ordered fixes. CUT-LIST.md = what to remove, merge or archive: owner yes first, move to archive, never delete; patches never delete a file. EXCEPTIONS.md = every exception with reason, owner, removal trigger. LESSONS.md = lessons for the checklist.
Patch rule: unified diff against the repo file; a flow fix goes first to handover/demo/n8n-mainframe/build_mainframe.py (the generator is the source) and the json diff is attached only if the generator rebuild ran here; otherwise the json patch is marked UNVERIFIED (not regenerated).

## 7. Stop rule
A fresh reviewer pass with no Blocker or Major; evidence checks (a) to (g) all pass; every finding has evidence and a patch file or an OWNER/IMPOSSIBLE reason; everything needing a runtime is UNVERIFIED; FINAL block in REPORT.md pushed. If a Blocker stays open after the round cap the lead decides; the audit is not called done on its own.

## 8. MUST-NOT for every agent
No write outside the section 3 allowlist; no write to handover/demo; no moving or deleting flow files; no git commands (the lead commits and pushes); no secrets, no network, no n8n runtime, no live model call; never copy a secret value (node and key name only); no claim of done without raw output; every Agent call sets the model (sonnet default; haiku only plain lookups; opus only inside the egm planning skills).
