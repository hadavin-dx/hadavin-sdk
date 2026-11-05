# Core inventory, lane A (Phase 0), 2026-11-05

Read-only research. EGM skipped: read-only inventory. Facts are from files/commands named; "not verified" marks what I did not run. No tests were run, no repo edited.

## 0. Headline findings (read first)
1. **Core main moved and nothing else did.** `origin/main` = `ce70eb5` ("K5-core ... one choke point", PR #42, merged 2026-11-04 02:02Z). Local `projects\hadavin-sdk` `main` is still `6608146` (stale). EVERY demo pin (`core_copies.json` core_commit) is `6608146`. The handoffs and mission file do not mention #42 as merged.
2. **C18a and C1a branches are based on the OLD main `6608146`** (18 and 10 commits ahead). `ce70eb5` rewrote or added files they also touch (`guard/injection.py`, `runtime/tick.py`, `extract.py`, `guard/redact.py`, `registry.py`, `config.py`, `backends/table.py`, `k1b/redaction.py`, `store/*`). Expect real conflicts on rebase; not tested (no merge run).
3. **PR #50 on GitHub (`2e8a28c`) already contains `ce70eb5`** (ancestor check passed). The local worktree `pr50b3-wt` (`748849c`, branch `pr50b3-local`) is 6 commits AHEAD of the pushed `2e8a28c` (ancestor check passed): origin lacks the batch 3/3b fixes. The PR's diff is far bigger than "promote apexc": 183 files, +33k/-414, including `runtime/stop_gate.py`, `rowstore.py`, `config_view.py`, `audit/capped.py`, `testing/*`, `sources/*`, `tools.py`, `guard/http.py`, `guard/runmap.py` (the last few are K5 files, now in main; `git diff --stat origin/main...origin/core/promote-apexc-review8` was not run, so the true size against new main is unknown).
4. **PR #49 and PR #50 both add `guard/textnorm.py`** with different content (c1f9a177 vs 954ae52c) and both change `limits.py`, `approvals/gate.py`, `models.py`, `store/*`. Migration number 0005 collides (#41 `0005_measure`, #49 `0005_reservations`; #42's `0005_evidence` is now in main). Source: SYNC-STATUS-2026-11-02.md (measured then; branch heads may have moved). Demos copy PR50's.
5. **`python egm\tools\ledger_check.py --topic core` errors now**: `LEDGER ERROR: line 1907: 5 columns, expected 9`. Row `BL-core-c1a-015` has a literal newline inside its text (a regex written with a real line break). The check cannot pass until that row is repaired (not edited by me).
6. **Open core ledger rows (parsed `| BL-core-<topic>-` rows):** c18a 32 MAJOR + 19 MINOR OPEN; c1a 27 MAJOR + 16 MINOR OPEN (+1 MAJOR with unparsed status, the broken row); pr50 19 MAJOR OPEN + 1 MAJOR FIXED-UNVERIFIED + 1 MAJOR unparsed + 26 MINOR OPEN. No BL-core rows exist for #41, #43, #47, #48, #49 (their rows sit under other topic names, see section 8).
7. Single-dependency gaps: section 6 (short: `executor` has only `http`; `channel` has only `fake` and `slack`; `store` has one durable backend; no second `redactor` backend yet).

Heads (verified with git): `origin/main` ce70eb5; local main 6608146; PR41 `06a75b0`; PR43 `fa12aeb`; PR47 `03755d1`; PR48 `8986cb5`; PR49 `cd62212`; PR50 pushed `2e8a28c`; PR50 local `748849c`; C18a `198a6b6`; C1a `8460813`. PRs #51-#56 are Dependabot bumps (setup-uv, pytest 9.2.0, moto 5.2.5, sqlglot 30.25, boto3 1.43.120, azure-keyvault-secrets 4.12.0).

## 1. Modules and kinds on core (`src\hadavin_sdk`, from docstrings and `backends\table.py`)
Tests live flat in `projects\hadavin-sdk\tests\` (`test_*.py`, plus `tests\warden_port\`, `tests\contracts\`, `tests\demo_askdata\`); no per-module tests dir. Lists are from the `6608146` tree; main `ce70eb5` adds the K5 files in the last row of 1b.

### 1a. Pluggable capabilities (table-driven kinds)
| Capability | Kinds (neutral default first) | Interface | Second backend? | Tests | Notes / risk |
|---|---|---|---|---|---|
| secrets | `fake`, `env` (dev only), `mounted_file`, `vault` (Vault/OpenBao, stdlib HTTP), `aws_secrets_manager`, `azure_key_vault`, `gcp_secret_manager` | `actions/secrets.py`; remote kinds share `secrets_cache.py` | yes | test_p4_secrets, test_p4b_secrets | strong |
| signer | `none`, `ed25519_local`, `aws_kms`, `azure_key_vault_key` (ECDSA P-256), `gcp_kms`, `vault_transit` | `audit/signer.py` Protocol | yes | test_p3b_neutral_audit | strong |
| anchor | `none`, `s3_object_lock` (MinIO/Ceph via endpoint_url), `azure_immutable_blob`, `gcs_retention_lock` | `audit/anchors.py` | yes | test_p3b_neutral_audit | strong |
| store | `memory`, `postgres` (RDS IAM optional) | `store/protocol.py` | PARTIAL: one durable backend | test_p2_postgres, test_p7_store, test_k2_migrations | low lock-in (open standard) but no second durable kind found |
| audit | `local_dir`, `chain` (hash chain in the store DB, signed checkpoints, anchors) | `audit/protocol.py` | yes (2 sinks) | test_s2_audit, test_p3b | strong |
| llm | `fake`, `anthropic` (Claude API, Vertex, Foundry), `bedrock`, `openai_compat` (OpenAI/Groq/OpenRouter/Ollama), `gemini` | `llm/protocol.py`; `common.py`, `retry.py` | yes (5) | test_p5_llm, test_p5p6_followups, test_s4_llm_guard | `common.py` cost handling is the C2/C3/C4a/C17 target |
| detector | `regex`, `llm_judge`, `bedrock_guardrail` | `guard/injection.py` tripwire, fail closed | yes | test_p6_detectors | strong |
| channel (approvals) | `fake`, `slack` | `approvals/channel.py` | NO real second channel | test_s6_approvals | single-vendor gap |
| executor | `http` only (`actions/executor.py`, the only holder of a client secret) | `actions/contract.py`, `authorizer.py` | NO second kind | test_executor | gap |
| redactor | NOT a kind on main; `guard/redact.py` is one fixed pattern module (1132 lines) | n/a | C1a makes it a kind (`guard/redactor.py`, branch only) | test_c1a_redactor (branch) | section 2 |

### 1b. Fixed modules
| Module | Purpose | Tests | State / risk |
|---|---|---|---|
| `app.py`, `config.py`, `registry.py`, `deferred.py`, `errors.py`, `models.py`, `identity.py`, `cli.py` | wiring from one client config, config load, agent registry check, deferred-feature refusal, shared shapes, principals, CLI | test_s1_foundation, test_p1a_fixes, test_p1b_backends, test_repo_rules | in main |
| `runtime/agent_loop.py`, `plan.py`, `runs.py`, `tick.py` | agent loop (model only proposes), frozen plan, run state machine, idempotent tick | test_s5_runtime, test_p7_tick, test_cuj | C1, C8, C18a touch these |
| `approvals/{gate,requests,cards,receiver,hmac_v0,slack,slack_channel}.py` | text cleaning, requests (timeout never approves), cards, signed callbacks | test_s6_approvals | |
| `actions/authorizer.py` | deterministic allow/needs_approval/deny with rule id | test_s3_gate, test_g4_parity | |
| `guard/egress.py` | outbound host allowlist | test_s3, test_s4, test_p1b | |
| `guard/redact.py` | pattern redaction for logs/audit/channel text; documents go to the model UNREDACTED on main (C1 blocker) | warden_port/test_redaction_* | PR50 and C1a both change it; slow-pattern rows BL-core-c1a-001/015 |
| `limits.py` (51 lines) | spend meter, daily/monthly budgets, kill switch, audited | test_s1, test_s3 | #48, #49, #50 all touch it |
| `evals.py`, `stats.py`, `extract.py` | eval gate, stats, structured extraction (one retry + dead letter) | test_k1a_pass_k, test_k3_* | C9 not built; extract leak fixes are in #48 |
| `k1b/*` (13 files) | K1b-lite replay, count-only score, redaction before model, bundle allowlist | test_k1b_* (9 files) | in main |
| `store/migrate.py` + `migrations/` | forward-only migrations | test_k2_migrations, test_migrate_regex_linear | number collisions across PRs |
| K5 on main `ce70eb5` | `guard/producers.py` (tool-result and card producers via one choke point), `guard/runmap.py`, `guard/http.py`, `runtime/evidence.py`, `sources/{kinds,kubernetes}.py`, `tools.py`, `scrub_settings.py`, `defaults.py`, `backends/factory.py`, `0005_evidence.sql` | new tests in that commit (not listed) | merged; no demo pins it yet |

## 2. Open PRs and worktrees (src changes read with `git diff --name-status main...<head> -- src`, `main` = local 6608146)
| Item | Head | Adds | Overlaps | Open ledger rows | State |
|---|---|---|---|---|---|
| #41 `k6` | 06a75b0 | `measure.py`, `0005_measure.sql`, approvals/agent_loop/tick/store touches; 38 files +8.1k | base 308558a, behind main; migration 0005 collides | none BL-core; review `egm\hadavin-sdk\k6-egm-review-2026-11-01.md` | open; rebase + renumber |
| #43 `demo-gaps` | fa12aeb | llm retry/common/protocol/provider fixes, config, models; ask-your-data demo; 51 files +8.5k | llm/* with #48 | none BL-core | open, behind main |
| #47 `demo-askdata-export` | 03755d1 | demo export adapter only, no `src` change; 35 files | none | none BL-core | open; worktrees `.wt-d1`, `projects\wt-pr47` |
| #48 `core-hardening-1` | 8986cb5 | `llm/metered.py`, `llm/resilient.py` (reserve-then-settle, spend-cap 429), extract leak fixes, limits, store hooks, agent_loop, judge, evals; 54 files +7.5k | llm/*, limits, store/* with #43/#49/#50 | not under BL-core (see section 8) | open, behind main; WP C17 target |
| #49 `core/promote-refunds-r8` | cd62212 | `actions/outbox.py`, `approvals/signed.py`, `audit/refusal.py`, `guard/{identity_text,reply_check,textnorm}.py`, `store/reservations.py`, `0005_reservations.sql`; 24 files +2.5k; draft | textnorm CONFLICT with #50; limits, gate, models, store | `BL-demos-refunds-*` (31 rows) | draft, behind main; dealdesk copies `signed.py` from it |
| #50 pushed `core/promote-apexc-review8` | 2e8a28c | see next row; 183 files +33k/-414; contains main ce70eb5 | textnorm CONFLICT with #49; limits, gate, models | BL-core-pr50-*: 19 MAJOR OPEN, 1 MAJOR FIXED-UNVERIFIED, 26 MINOR OPEN | draft |
| #50 local `pr50b3-wt` (`pr50b3-local`) | 748849c (6 ahead of pushed; 0 dirty at last refresh) | text fold (`guard/textnorm.py`, `_confusables.py` UTS#39-generated by `tools\gen_confusables.py`), `egress_text.py`, `http.py`, `runmap.py`, `producers.py`, `runtime/{stop_gate,rowstore,config_view,evidence}.py`, `audit/{capped,labelkey}.py`, `backends/factory.py`, `defaults.py`, `scrub_settings.py`, `sources/*`, `testing/{contracts,mutation}.py`, `tools/mutation_runner.py`, `tests\test_promoted_controls.py` (2863 lines) + 4 fix-batch test files | as above | same rows; limit-stop: round 3 = 0 blocker, 8 majors | NOT pushed. Mission: fix its failing test + BAD mutant row first (not verified by me); then evidence + reviewers |
| C18a `core/c18a-injection-log-redact` (`_local\scratch\wt\core-c18a`) | 198a6b6 | `guard/safe_message.py` (318 lines); changes in `cli.py`, `extract.py`, `injection.py`, `tick.py`, `registry.py`, `config.py`, `llm/anthropic.py`; 4 new test files (~2.1k lines); 18 commits | based on OLD main; K5 touched injection/tick/extract | BL-core-c18a: 32 MAJOR + 19 MINOR OPEN | **SUPERSEDED by the frozen redesign** `egm\hadavin-sdk\c18a-redesign\design-v3.md` + `-FROZEN-amendments.md`; old branch = source of tests and ledger knowledge |
| C1a `core/c1a-redactor-kind` (`_local\scratch\wt\core-c1a`) | 8460813 | `guard/redactor.py` (774 lines; kind, MaskSession, marks), table/builtin/registry/config wiring, CHANGELOG, `tests\test_c1a_redactor.py` (1767 lines); 10 commits | based on OLD main; `redact.py` owner is PR50 | BL-core-c1a: 27 MAJOR + 16 MINOR OPEN (+ broken row) | BL-core-c1a-001/015 (slow patterns in `redact.py`) BLOCK merge |

About 50 other worktrees under `_local\scratch\wt\` and `old\from-C-root\...` (e.g. `pr50c`, `pr50d`, `core-pr49`, `k5-*`, `gaps-1..5`, `lite-a/b/c`) are earlier iterations of merged or open work; listed, not inspected.

## 3. Work packages (`egm\course-reread\pass2\WORK-PACKAGES.md`, C1 tickets)
Status = branch/PR exists for the id, ledger topic exists, handoff lane table. Nothing was run.
| WP | What (short) | Where | State |
|---|---|---|---|
| C1 (BLOCKER) | mask the document before the model | core | split into C1a-C1d, C1f; only C1a has a branch (in review, 43 open rows). Main `guard/redact.py` docstring still says documents go unredacted |
| C1a | redactor kind + MaskSession + marks | core | IN BRANCH 8460813 |
| C1b/C1c/C1d | masked LLM wrapper, eval gate restore (`evals._restore_all`), agent_loop/k1b plumbing | core | NOT STARTED (handoff: only after C18a and C1a are clean) |
| C1f | put-back / approval card restore | core | NOT STARTED; needs its own plan review |
| KERNEL-1 | kernel promotion | core | NOT STARTED (no branch; k5/k6/k1b are earlier kernel parts) |
| C2 | refuse instead of estimate, `UsageMissing`, `or`-zero sweep (`llm/common.py` l.163-168) | core | NOT STARTED (no `core/c2-*` branch) |
| C3 | five-class `Usage` | core | NOT STARTED |
| C4a | price tiers in `Route` config | core | NOT STARTED |
| C4b | tier fields in Intake `budget.py` | Intake | after C15; Intake lane (not verified) |
| C5 | loud budget wall | Intake (+ core hook) | Intake cost controls A on `wp2c-p45-df5-a12` (b6592b9, round 2); core part not started |
| C6 | per-call log fields | Intake + core `finally` record | not started in core |
| C7 | approver screen "Read by: model" | Intake | Intake lane |
| C8 | run cost cap `Agent.budget_usd.per_run` | core `runtime/agent_loop.py` | NOT STARTED |
| C9 | eval gate buckets and minimum size | core `evals.py` | NOT STARTED (B12 first) |
| C10, C11, C13, C16, C19-C22 | golden-set template, duplicate-invoice erratum, trifecta record, text-check erratum, bible follow-ups, Mermaid render, Claude Code checks, sibling text | Intake/bible/lead | docs/lead items, not core code; not checked |
| C12 | tamper-evident audit for Intake via core `audit/chain.py` | Intake | unblocked 2026-11-04; consumer work |
| C14 / C15 | DNS time-out / `FALLBACK_CODES` transport only | Intake | Intake lane |
| C17 | reserve-then-settle | core PR #48 | IN PR (8986cb5); lead checks against R214 before merge; behind new main |
| C18a | log/exception redaction | core | old branch SUPERSEDED; redesign R1/R1P frozen, unbuilt |
| C18b | hygiene batch (judge model id differs, boundary markers CD-20, retirement date, runaway test) | core | NOT STARTED |

Order per the WP file: C1 and C18a first; C2 -> C3 -> C4a -> C17 (money chain); C15 -> C4b -> C5/C6/C7; B12 before C9.

## 4. Pinned copies (`core_copies.json`)
Read: `projects\hadavin-demo-{apexc,dealdesk,intake,refunds}\core_copies.json` (first ~1500 chars each, so apexc and dealdesk file lists may be cut), SYNC-STATUS and DUPLICATION-MAP of 2026-11-02 (measured then, not re-run). No `core_copies.json` exists in `jagrat`, `hadavin-portal-kit`, `website` or the duplicate `hadavin-demos-*` folders (find to depth 4; `egm\one-project\snapshot-*` hits are snapshots).
| Core file (PR source) | apexc | dealdesk | intake | refunds | Pin |
|---|---|---|---|---|---|
| `guard/textnorm.py` (PR50) | `src/apexc/textnorm.py` sha 576b4cba, snap 153d2178 | `core_copy/textnorm.py` sha 576b4cba, snap 153d217 | `core_copy/textnorm.py` sha **954ae52c**, snap 855b4e0 | `core_copy/textnorm.py` sha 576b4cba, snap 153d217 | hashes differ between demos (two PR50 revisions); PR49 has a third (c1f9a177). Real drift |
| `guard/_confusables.py` (PR50) | via rewrite | `core_copy/_confusables.py` sha 41740c11 | same sha | same sha | same hash in 3 demos; PR50 head later added a `DATA_UNICODEDATA` line |
| `guard/egress_text.py` (PR50) | `src/apexc/egress_text.py` sha 632fac99 | `core_copy/egress_text.py` sha 632fac99 | none | none | PR50 round 4 changed it (+107 lines per 11-02 check) |
| `runtime/config_view.py` (PR50) | `src/apexc/config_view.py` sha c129597c | not seen (list cut) | none | none | |
| `approvals/signed.py` (PR49) | none | `core_copy/approvals_signed.py` sha 5a303583 (2 import rewrites) | none | none | PR49 only |
| `demos/ask-your-data/askdata/safe_text.py` (a demo module inside core) | none | none | `src/intake/safe_text.py` sha 49ef89fc | none | not a kind module; limit-stop says a hand edit vs pin fails a 6b test |
| apexc other entries | list cut at 1500 chars; more likely (ledger r2-001 names rowstore, config_view, capped, testing) | | | | read the whole file before the re-pin plan |

`allowed_local` (expire 2026-12-31): dealdesk `signing.py` (stale duplicate of core `audit/signer.py`, which main has), dealdesk `textnorm.py` wrapper; intake `textfold.py`; refunds `textnorm.py`, `gate.py`.
11-02 duplication map: no demo `src` imports `hadavin_sdk` (only tests do). Generic code written separately in several demos: RateCap, ReadLog, canonical_json/sha256, live-run gate, inbound ledger, hash-chained audit (apexc+refunds+dealdesk), kill switch (3), egress check (4), text fold (4), mutation runner (4), test-split guard. Whether Intake has since moved to core `audit/chain.py` (C12) is not verified.
What is in core: main has chain audit, signers, anchors, secrets, llm kinds, approvals gate, k1b, K5. PR50 only: text fold, egress text, stop gate, row store, capped audit, config view, mutation runner. PR49 only: signed approvals, outbox, reservation store, refusal, reply check, identity text. PR48 only: reserve-then-settle meter. PR41 only: measurement/demotion.

## 5. Inventory table (capability | where | in core | pinned copy | state | risk)
| Capability | Where it lives now | In core? | Pinned copy | State | Risk |
|---|---|---|---|---|---|
| Secrets kinds (7) | core main | yes | none | merged | low |
| Audit chain + signers + anchors | core main | yes | dealdesk stale local `signing.py` | merged | low; apexc/refunds/dealdesk re-implement chains |
| LLM kinds (5) + retry | core main; #43 | yes / PR43 | none | merged; #43 open | medium: cost accounting C2/C3/C4a |
| Reserve-then-settle, spend-cap 429 | PR #48; Intake lane A1/A2 | partial (PR) | none | #48 open, behind main | HIGH money; three PRs touch `limits.py` |
| Cost controls C2/C3/C4a/C5/C8 | not built in core | no | n/a | not started | HIGH money, uncapped review |
| Redaction before model (C1) | `guard/redact.py` main; `redactor.py` C1a branch | partial | textnorm in 4 demos | branch, 43 open rows | HIGH redaction, uncapped |
| Log/exception redaction (C18a) | old branch; redesign frozen, unbuilt | no | n/a | old branch superseded | HIGH |
| Text fold / confusables | PR50 (and PR49 variant) | PR only | 4 demos, 2 hash versions | both PRs open, conflict | HIGH: two competing files |
| Egress text checks | PR50 | PR only | apexc, dealdesk | open | medium |
| Stop gate / kill switch | PR50 `runtime/stop_gate.py`; main `limits.py` | partial | none (dealdesk local) | rows r2-005/007/022 | medium-high: restore without audit |
| Row store, config view, capped audit | PR50 | PR only | apexc (config_view) | open | medium |
| Signed approvals, outbox, reply check, refusal, reservations | PR #49 | PR only | dealdesk (signed) | draft, behind main | medium-high |
| Approval channel | core main (`slack`) | yes | none | merged | medium: one real channel |
| Executor / authorizer / contracts | core main (`http`) | yes | none | merged | medium: one executor kind |
| K1b replay + score | core main | yes | none | merged | low |
| K5 evidence sources + producers | core main ce70eb5 | yes | none | merged, no demo pins it | low-medium |
| K6 measurement/demotion | PR #41 | PR only | none | open, behind main | medium |
| Scan / work-queue / approval service (6b/6d) | Intake worktrees `wp6-6b` (870f61c), `wp6-6d` (8bcadfc) | no | n/a | evidence failing at last note | lane B, not inventoried |
| Invoice/payment checks (WP3) | Intake `intake-wp3-fix` (179681e) | no | n/a | round 7 | money; lane B |
| Jagrat incident logic, Warden gates | `projects\jagrat`, `reference\warden` | partial (`tests\warden_port`, llm ports) | none | not read by me | lane B |
| Eval gate buckets (C9) | not built | no | n/a | not started | medium |
| Mutation runner | PR50 `testing/mutation.py` + `tools/mutation_runner.py`; local copies in 4 demos | PR only | none | open | medium |

## 6. Single-dependency and lock-in gaps
1. Vendor SDK imports are all inside kind modules (grep over `src\hadavin_sdk` hits only `actions/secrets_{aws,azure,gcp}.py`, `audit/{anchor_*,signer*}.py`, `guard/bedrock_guardrail.py`, `llm/{anthropic,bedrock}.py`, `store/{auth_aws,postgres,migrate}.py`). `store/migrate.py` imports `psycopg.sql` outside the `postgres` module: acceptable but ties migrations to one driver.
2. `executor`: only `http`; no second kind or written outline found.
3. `channel`: only `slack` besides `fake`; no email/Teams/webhook kind or outline found.
4. `store`: `postgres` is the only durable backend (open standard, low risk; `memory` is dev only).
5. `llm`: five kinds, so the "Claude default + second backend" rule is met; `bedrock_guardrail` is AWS-only but has `regex` and `llm_judge` as neutral alternatives.
6. K5 `sources`: `kubernetes` is the named source; a second source kind not verified.
7. No redactor kind on main (fixed regex module). C1a adds the kind but no second backend yet; needs a model/NER-style alternative or a written outline with trigger.
8. Demos copy `textnorm` bytes instead of importing: drift risk, two hash versions today.
9. Three PRs fight over `limits.py`, `models.py`, `store/*`, `approvals/gate.py` and a duplicate `textnorm.py`; merge order must be decided first.
10. Process gaps: stale local main and stale pins (0.1); malformed ledger row blocks `ledger_check` (0.5); PR50 local head not pushed; `git status` in `projects\hadavin-sdk` shows ` M README.md`, untracked `.claude/` and `snap855.tar` (untouched).

## 7. Merge-order facts for the lead
- Conflict-forced order: PR50 first (already contains main), then #49 (drop its `textnorm`, keep `signed`, `outbox`, `reservations`; renumber migration), then #48 (limits/llm), then #43, then #41 (renumber `0005_measure.sql`); C1a after PR50 (redact.py ownership); C18a redesign on the new main.
- Demo pins (`6608146`) are already one core commit behind main (`ce70eb5`).

## 8. Not verified / not read
- No tests, evidence scripts or CI run; PR check status (CI, Sonar, CodeRabbit) not queried.
- `git diff --stat origin/main...<pr>` for each PR not run; sizes above are against local main 6608146.
- Merge conflicts of C18a, C1a, #49, #48, #43, #41 against `ce70eb5` not tried.
- Full apexc and dealdesk `core_copies.json` lists (read ~1500 chars each); hashes of copies vs current core not recomputed (11-02 SYNC-STATUS numbers quoted).
- `projects\jagrat`, `reference\*`, `hadavin-portal-kit`, `website`, duplicate `hadavin-demos-*` folders not read; demo-side generic code beyond the 11-02 map is lane B.
- Ledger rows for #48, #49, #43, #41 live under other topic names (`BL-hadavin-sdk-*` 37 rows, `BL-demos-refunds-*`, `egm\core-hardening-1\`, `egm\hadavin-sdk\k5/k6-egm-review-*`); not read.
- Test file to module mapping is by name only.
- Local worktree heads: confirmed 748849c, 198a6b6, 8460813 with `git log -1`; the rest from handoff section 9 (refreshed 13:21Z).

## 9. Files read
`handoff\CORE-FIRST-MISSION-2026-11-05.md` (first 6 kB), `handoff\lead-state-2026-11-05-limit-stop.md` (sections 2, 9), `egm\course-reread\pass2\WORK-PACKAGES.md`, `C1-ticket-v3.md` and `-FROZEN-amendments.md` (grep), `egm\BLOCKER-LEDGER.md` (parsed BL-core rows), `egm\hadavin-sdk\core-sync-check\SYNC-STATUS-2026-11-02.md`, `DUPLICATION-MAP-2026-11-02.md` (first 3.5 kB), four `core_copies.json`, `pyproject.toml`, `backends\table.py` (grep), all module docstrings in `src\hadavin_sdk`, git diff/log/worktree/branch output, `gh pr list`.
