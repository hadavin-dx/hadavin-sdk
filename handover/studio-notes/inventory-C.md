# Inventory C: generic code to promote into hadavin-sdk (Phase 0, lane C, read-only)

Date: 2026-11-05 (UTC; IST = +5:30). EGM skipped: read-only inventory. The lead runs EGM on the plan built from this.
Scope: projects\jagrat, reference\warden, reference\helios, reference\agent-killswitch, reference\temporal-cloud-sample.
Core compared against: projects\hadavin-sdk main working tree, HEAD 6608146 (#46). Jagrat pins core at 660814674ece.
Bible R-numbers: not grepped (this is a code inventory, no client/method answer); the lead cites R-numbers in the plan.

## 0. Key facts that shape the plan

1. Jagrat is a rename-derivative of Warden. Jagrat's src (10,748 lines, 29 py files) is a trimmed copy of Warden's
   (50,959 lines, 110 files). Same module names, same docstrings with "WARDEN" replaced. So for most capabilities
   "Jagrat copy" and "Warden original" are the same design. Promote ONE of them, once, rewritten to the core's
   kind/Protocol style (the 2026-10-30 audit `egm\hadavin-sdk\warden-reuse-audit.md` says the same: the core
   rewrites, it does not copy-paste).
2. Provenance, all owner-authored except one:
   - reference\warden: Apache-2.0, "Copyright 2026 Veera Rakesh Kethari" (LICENSE + NOTICE read). Copy-out allowed
     (owner is the licensor). Keep the Apache header and NOTICE line when a file is copied nearly verbatim.
   - reference\helios: Apache-2.0 (LICENSE file; Cargo.toml authors = Veera Rakesh Kethari). Rust. Owner-authored.
   - reference\agent-killswitch: Apache-2.0 (LICENSE; pyproject license = "Apache-2.0"). Owner-authored (README
     links github veerarakesh56). Published on PyPI as `agent-killswitch`; zero required dependencies.
   - reference\temporal-cloud-sample: MIT, "Copyright (c) 2023 temporal.io". THIRD-PARTY tutorial code (Temporal's
     money-transfer template). MIT lets us copy if the notice is kept, but it is toy code; nothing worth copying.
   - projects\jagrat: no LICENSE file at repo root (checked: none). Owner-authored, "all rights reserved" per
     memory jagrat-od-decisions (owner only, reuse for clients ok). Core is Apache-2.0? NOT VERIFIED here; the lead
     must confirm core's LICENSE before any Warden/Jagrat file lands, and that mixing is fine (owner is sole author).
3. Core guards that bite a promotion (read from tests):
   - tests\test_no_reference_material.py bans vendor brand strings ([vendor-inspired name removed], "[vendor-inspired name removed]", "[vendor-inspired name removed]", ...)
     and reference-material file hashes. Warden/Jagrat docstrings do not use those strings, but grep before copying.
   - tests\test_lockin_guard.py (name only, not read in detail): vendor SDK imports only inside kind modules. Warden
     modules import boto3, temporalio, kubernetes directly; they cannot move as-is.
   - Jagrat has its own tests\test_no_reference_names.py (J0 scrub). Names like "Warden", "Helios", "Eldane",
     "Wave 4" must be removed from any code promoted from reference\warden (core's warden_port tests already show
     the pattern).
4. Core's current inventory (hadavin_sdk, 13,229 py lines) already has these, so they are NOT promotion targets:
   audit chain + signers + S3/GCS/Azure anchors; approvals gate/channel/cards/requests/slack/hmac_v0; redact (1132
   L, includes Warden patterns); injection detector; egress; judge; llm (anthropic, bedrock, gemini, openai_compat,
   retry); secrets kinds (env/file/aws/azure/gcp/vault); store (memory/postgres/migrate); limits (spend meter +
   kill switch flag); runtime agent_loop/tick; k1b replay/score/report; evals; registry; config.
   Not in core (grep for names, zero source hits): freeze, environments policy, expected-down, grounding,
   quarantine, trust/confidence level, landed-check, symptom check, hand-back labels, safe argv paths, passkeys,
   per-target locks, circuit breaker, heartbeat, cascading kill, budget auto-kill, autonomy levels, numbers check,
   language detect, model routing, webhook front door, Temporal payload codec.
   Caveat: stale .pyc files in core src show other branches once had runtime\control, actions\outbox, reservations,
   guard\leakcheck, guard\egress_text, guard\identity_fold. Those are NOT on main source; they may live on open
   core PRs (#41-#50 dirs in egm\hadavin-sdk\). I did not read those PR branches (see section 6).

## 1. Capability table (generic, promotion candidates)

Columns: capability | file paths (J = projects\jagrat\src\jagrat, W = reference\warden\src\warden) | in core? |
licence/provenance | size | promotion risk | consuming demos. "Demos": Intake, Refunds, DealDesk, Apexc(dropped),
Jagrat, Warden-derived, client builds.

### 1A. Trust and grounding (model output checked by plain code)

| # | Capability | Files | In core? | Licence | Size | Risk | Consumers |
|---|---|---|---|---|---|---|---|
| A1 | Grounding: every citation names an existing evidence id and quotes a span verbatim (whitespace-collapsed, case kept); deterministic, no model | J\grounding.py (1147 L), W\grounding.py (815 L); tests warden_port has none | no (warden-reuse-audit ranks it #3) | Apache-2.0 (W), owner | M. Generic core is the quote-in-evidence check, ~150-250 L; the rest of the 1147 L is incident-specific claim types | MED: must be split; incident claim kinds stay in Jagrat | Intake (cite source doc spans), Refunds, DealDesk, any RAG-style build, Jagrat |
| A2 | Evidence ids: numbered items (L/E/..) so a claim can point at support | J\facts.py (425 L), W\evidence.py (296 L) | no | Apache-2.0 | S (~120 L generic part) | LOW: id scheme becomes config (prefix per source kind) | same as A1 |
| A3 | Numbers check: numbers in model prose must match metrics/fields read ("42%" vs 0.042) | W\numbers.py (105 L) | no (audit rank #3 pairs it with grounding); core has extract.py amount check only | Apache-2.0 | S | LOW | Intake money read, Refunds amounts, DealDesk, Jagrat |
| A4 | Quarantine: untrusted text reaches the model only as typed facts; closed word list neutralises steering | J\quarantine.py (588 L) + data\steering_action_words.txt, W\quarantine.py (380 L) | partial: core has guard\injection.py (100 L regex + Protocol) and judge; no typed-fact quarantine | Apache-2.0 | M-L. Generic mechanism ~200 L; word list is ActionKind-specific | MED-HIGH: security path, no review-round cap; the closed ActionKind list is Jagrat-specific and must be injected as config | Intake (untrusted emails/PDFs), Refunds, any agent reading outside text |
| A5 | Injection tripwire as second independent signal | W\tripwire.py (297 L) | partial: guard\injection.py + judge.py exist; Warden's uses a trained detector with a hosted model | Apache-2.0 | S | LOW if only the Detector Protocol fit is reused (core already has `Detector`, `AnyOf`, `combine`); likely nothing to promote | all |
| A6 | Level-not-number confidence: Low/Medium/High from checkable signals, never the model's self-score | J\confidence.py (97 L), J\trust.py (235 L), W\confidence.py (83 L), W\trust.py (202 L) | no (core stats.py/judge use the words only) | Apache-2.0 | S | LOW: signal set is domain data, mechanism ~80 L | Intake review queue, Refunds, DealDesk, Jagrat |
| A7 | Hand-back outcome log: approver labels right/wrong/unclear on what the system said (for pilot numbers) | J\handback.py (58 L), W\labels.py (64 L) | no; core has k1b score/report for evals, not live approver labels | Apache-2.0 | S | LOW; needs sticky-label rule (memory sticky-harmful-labels) and false-abstain reporting (memory false-abstain-reporting) | every pilot (R413-R416 per memory, not re-read) |
| A8 | Model routing: cheap classifier up front, doubt goes to strong lane, logged | W\routing.py (351 L) | no | Apache-2.0 | M | MED: must follow rule 18 (no cheap-then-retry cascade on money steps); Warden's hard-case signals are incident-specific | Intake, Refunds (money steps stay single model per DF5) |
| A9 | Language detect: flag non-English lines so keyword checks are not silently blind | W\language.py (40 L) | no | Apache-2.0 | XS | LOW | Intake (multi-language docs), Jagrat |
| A10 | Gate text rules for model prose (hedge, withhold commands, sanitise) | J\gate_text.py (30 L) | YES (core approvals\gate.py has hedge, withhold_commands, sanitise_text; Jagrat imports them) | n/a | - | none | done |

### 1B. Control, safety and policy

| # | Capability | Files | In core? | Licence | Size | Risk | Consumers |
|---|---|---|---|---|---|---|---|
| B1 | Change freeze windows: no apply inside a declared window; unreadable file refuses (fail closed) | J\freeze.py (57 L)+data\freeze.yaml (10 L), W\freeze.py (47 L) | no | Apache-2.0 | XS | LOW; env var JAGRAT_FREEZE_FILE becomes config path | Jagrat, any write-capable client build (Refunds payouts, DealDesk) |
| B2 | Per-environment policy: tier, allowlist, approver, auto-resolve vs hand-off (dev->prod gradient) | J\environments.py (346 L)+data\environments.yaml (75 L), W\environments.py (429 L) | partial: core registry.py + actions\authorizer.py (41 L) hold allowlists, no environment gradient | Apache-2.0 | M | MED: Jagrat's action tiers are incident-specific; generic = "scope x action class -> tier/approver" table. Fictional env names required (J0 note) | Jagrat, Warden-derived, client builds with dev/stage/prod |
| B3 | Autonomy levels L0..Ln per (environment, action class), derived from the audit, never a flag | W\autonomy.py (298 L) | no | Apache-2.0 | M | MED-HIGH (decides what runs unattended: security/money path, uncapped review). Not in Jagrat's trimmed copy | Jagrat later, client builds with earned autonomy |
| B4 | Expected-down: alarm/event on something a person declared off is not an incident | J\expected.py (184 L), W\expected.py (157 L) | no | Apache-2.0 | S | LOW generic as "declared-state suppression"; incident wording stays | Jagrat |
| B5 | Landed-check: before undoing own change, look for anything else that changed the target since | J\landed.py (106 L), W\landed.py (184 L) | no | Apache-2.0 | S | LOW-MED: needs a target-history reader Protocol; core executor has rollback in actions\executor.py, this is the guard before it | Refunds (reversal), DealDesk, Jagrat |
| B6 | Symptom check: success = symptom gone, not only trigger cleared | J\symptom.py (454 L), W\symptom.py (339 L) | no | Apache-2.0 | M | MED: metric semantics are cloud-alarm specific (INSUFFICIENT_DATA); generic = verify-after-apply Protocol, already partly in core actions\contract.py verify/undo | Jagrat |
| B7 | Safe path from argv: after `..` and symlinks resolved must lie inside permitted roots | J\paths.py (68 L), W\paths.py (55 L) | no (core cli.py 406 L; not checked for equivalent) | Apache-2.0 | XS | LOW; Sonar S8707 origin | every CLI/agent-driven repo |
| B8 | Per-target single-writer lock recorded in the audit, durable across workers | W\locks.py (72 L) | no (core has idempotency keys in contract/executor; store has no target lock) | Apache-2.0 | S | MED: needs Store Protocol method + Postgres migration; concurrency tests (memory no-lost-messages) | Intake (one writer per case), Refunds, Jagrat |
| B9 | Bounds + circuit breaker + kill switch read from the audit log (`blocked()` reasons; rechecked inside apply) | W\bounds.py (161 L); J\bounds is HELD (absent, owner J2) | partial: core limits.py (51 L) has spend meter + daily/monthly budget + kill switch; no breaker, reset not signed (audit note) | Apache-2.0 | S-M | MED: money/safety path | all |
| B10 | Actor-role permission preflight: check the executing role can do the plan before asking for approval | W\permits.py (304 L) | no | Apache-2.0 | M | MED: AWS IAM specifics; generic part = "dry-run the executor identity before approval" Protocol (core has an executor + authorizer) | Jagrat, client builds |
| B11 | Passkey (WebAuthn) approval bound to exactly one plan hash | W\passkeys.py (154 L), W\approval_page.py (1866 L, mostly page HTML) | no (audit rank #8; W2-W6 hardening plans exist, "read before porting") | Apache-2.0 | M | HIGH: security path, uncapped review; a WebAuthn library dependency must sit behind a kind (no single dependency) | Jagrat, Intake approver (X1 uses laptop passphrase approver first), client builds |
| B12 | Approval edge auth (API-gateway authorizer in front of approval routes) | W\edge_auth.py (104 L) | no | Apache-2.0 | S | HIGH: AWS-specific, belongs in a kind module | Warden-derived only; low priority |
| B13 | Webhook front door: who may send, rate, authenticity (shared-secret header) | W\webhooks.py (244 L) | partial: core approvals\hmac_v0.py + receiver.py (65 L) cover signed callbacks | Apache-2.0 | S | LOW | Intake mail/webhook intake, Jagrat |
| B14 | Read-scope: what an alert from an MCP caller may make the system read | W\read_scope.py (65 L) | no | Apache-2.0 | XS | LOW; least-privilege flavoured, generic as allowlist-by-source | any agent with tools |
| B15 | MCP tool output schemas (structuredContent conforming to outputSchema) | W\mcp_schemas.py (105 L), W\mcp_server.py (780 L) | no MCP server in core | Apache-2.0 | M | MED: MCP SDK dependency must sit behind a kind; tool-ladder rung "MCP" | client builds, Jagrat |
| B16 | Sealed vault + reveal: real values behind placeholders, shown to people only | W\vault.py (321 L), W\reveal.py (255 L) | no; core redact masks but reveal path not found | Apache-2.0 | M | HIGH: PII/redaction path, uncapped review. Synthetic data only in laptop sessions | Intake (PII docs), Refunds |
| B17 | Temporal payload codec (AES-256-GCM before history) | W\codec.py (136 L) | no; core has no Temporal | Apache-2.0 | S | MED: only useful if a Temporal runtime kind exists; key via secrets kind | Warden-derived, client builds using Temporal |

### 1C. Records, audit extras, reporting (generic shells)

| # | Capability | Files | In core? | Licence | Size | Risk | Consumers |
|---|---|---|---|---|---|---|---|
| C1 | Typed pydantic contracts per pipeline stage | J\models.py (597 L), W\models.py (538 L) | n/a: core models.py (276 L) is separate | Apache-2.0 | - | not promoted (incident types); only patterns | - |
| C2 | Linked records (signed link: same-root-cause, recurrence-of, ...) | W\links.py (361 L) (J\links HELD) | no | Apache-2.0 | M | LOW-MED; signed-by-person uses audit chain | Jagrat |
| C3 | Change record for every applied change in a place teams look | W\changes.py (94 L) | no | Apache-2.0 | XS | LOW | client builds |
| C4 | Timeline: which change broke it (deploys/commits near an event) | W\timeline.py (216 L) | no | Apache-2.0 | S | MED: GitHub reader kind | Jagrat |
| C5 | Postmortem draft from signed record | J\postmortem.py (273 L), W\postmortem.py (199 L) | no | Apache-2.0 | S | LOW; wording incident-specific | Jagrat |
| C6 | Records store/CLI (records.py 1287 L, records_cli.py 385 L), history.py (397 L, J HELD) | W | partial: core audit sink + store | Apache-2.0 | L | MED; mostly Jagrat/Warden-specific record pages | Jagrat |
| C7 | Settings pattern: frozen, validated, every field documented | J\settings.py (95 L), W\settings.py (380 L) | yes in spirit: core config.py (291 L) pydantic YAML | n/a | - | none | done |
| C8 | Render config from template, idempotent | J\render_config.py (60 L) + tools\render_config.py | no | owner | XS | LOW; Jagrat-repo tooling | Jagrat only (keep) |
| C9 | Held-modules guard and removal guard tests | J tests\held_modules.py, test_held_modules_format.py, test_removed_features.py, test_import_closure.py, test_socket_guard.py | no | owner | S | LOW; test PATTERNS worth porting: socket guard (no network in tests), import closure, steering-words test | all repos |

### 1D. Agent safety: agent-killswitch (Python, Apache-2.0, 3,756 L, zero deps)

Read: file list and README head only; code bodies NOT read (see section 6).

| # | Capability | Files (agent_killswitch\) | In core? | Size | Risk | Consumers |
|---|---|---|---|---|---|---|
| D1 | Kill switch (out-of-band, agent cannot argue its way out) | core\killswitch.py (581 L), core\enums.py, core\models.py, backends\base+memory+redis | partial: core limits.py kill flag + store.get_kill_switch | M | MED: core has a boolean; this adds scoped/levelled kills and a backend Protocol (memory, redis). Redis stays a kind module | all agent loops |
| D2 | Circuit breaker | core\circuit_breaker.py (323 L) | no | S-M | LOW-MED | all |
| D3 | Heartbeat monitor (silent/hung agent detection) | core\heartbeat.py (313 L) | no (core tick.py has runtime ticks, not heartbeat) | S-M | LOW-MED | long-running agents |
| D4 | Budget kill (stop at spend cap) | core\budget_kill.py (281 L) | partial: core limits.py budgets | S | LOW; merge with limits.py, do not duplicate | all |
| D5 | Cascading kill (parent kills child agents) | core\cascading.py (280 L) | no | S | LOW | multi-agent builds |
| D6 | Decorators + framework integrations (langchain, langgraph, crewai, openai-agents, asyncio tasks) | decorators.py 302 L, integrations\* (~790 L) | no | M | HIGH for lock-in: framework imports must live in kind modules; core agent_loop does not use these frameworks, so likely NOT promoted | skip unless a client uses them |

Decision options for the lead (tool ladder, rung "reuse studio code"): (a) depend on the published
`agent-killswitch` package behind a kind (it is owner-authored, zero deps); (b) copy D1-D5 into hadavin_sdk with
Apache header kept. (b) fits "no single dependency" and "core modules identical everywhere" better; (a) avoids drift.

### 1E. Helios (Rust, Apache-2.0, owner-authored)

| # | Capability | Files | In core? | Size | Risk | Consumers |
|---|---|---|---|---|---|---|
| E1 | Deterministic failure simulation over `terraform show -json` (18 AWS kinds, 6 scenarios) + GitHub Action + web viewer | crates\helios-{aws,cli,engine,graph,models} 8,502 L Rust; web\; action\ | no | L | HIGH: Rust, not Python; AWS-specific; a CLI to call, not a library to merge | Warden-derived, infra clients (optional paid add-on); NOT a core module |
| E2 | helios-ai: Claude explain + fix generator over a failure report, with mock and glossary | helios-ai\src\helios_ai\* (873 L Python, 6 modules) | no | S | LOW; `_claude_cli.py` shells out to the claude CLI (single-vendor), `_mock.py` is the fake. Pattern only (explain + fix proposal behind llm kind) | Warden-derived |

Recommendation: do not promote Helios code into hadavin-sdk. Treat as a separate tool a client build may call (tool ladder rung 1). Not read in detail.

### 1F. Temporal-cloud-sample (MIT, third party)

| Capability | Files | In core? | Note |
|---|---|---|---|
| Money-transfer tutorial: activities, workflow, worker, a mock banking service | activities.py (101), banking_service.py (204), workflows.py (63), run_worker.py (32), run_workflow.py (43), shared.py (15), tests\test_run_worker.py | no | Toy tutorial code, third party (MIT, temporal.io). Value is only as a reference for a Temporal runtime kind; no code worth copying. Warden's workflows.py (1294 L) and activities.py (2416 L) are the real Temporal usage |

### 1G. Warden Temporal runtime (generic shell inside incident code)

| # | Capability | Files | In core? | Size | Risk |
|---|---|---|---|---|---|
| G1 | Durable workflow runtime: activities, workflows, runtime_base/runtime, worker | W\workflows.py (1294), W\activities.py (2416), W\runtime.py (412), W\runtime_base.py (140), W\temporal_history.py (327) | no (core has its own runtime\tick + store); no Temporal | XL, mostly incident logic | HIGH: Temporal SDK must sit behind a runtime kind; not core-first. Defer unless a client build chooses Temporal (options-first). Extract only the generic shape (approval wait, signal, timeout, rollback) as a spec |

## 2. Cloud-specific code that must NOT go to core as-is (kind modules or stay)

Warden: aws_backend (715), aws_stack (2278), aws_describe, aws_docs, awswatch (841), platforms\aws (3279), db (640),
infra (325), k8s (508), k8s_backend (720), lambdas (556), xray (87), quotas (212), reachability (339),
health_signals (128), datadog (181), grafana (260), redis_reads (254), github_app (540), slack_login (135),
eldane + eldane_slack (721), depwatch (1112), deploy_watch (159), code_fix (687), code_gate (997).
These carry boto3/kubernetes/vendor SDKs; core's lock-in guard forbids them outside kind modules. They belong in
Jagrat (or a separate Warden-derived repo), never in core. Jagrat has platforms\__init__.py (173 L) as the neutral
platform Protocol (live/apply/healthy/rollback); that Protocol is the generic seam and MAY map onto core
actions\contract.py (verify/undo) rather than become a second interface. Needs a decision (section 5).

## 3. Project-specific, must stay in Jagrat (do not promote)

- J\catalog.py (1137 L): remediation catalogue; the ONLY writes Jagrat can apply (restart, scale, rollback...).
- J\playbook.py (1659 L): follow-up by failure pattern for on-call/dev/platform teams.
- J\verifier.py (1358 L): the deterministic gate for incidents. Rule ids P1..P32 are Jagrat policy. Generic rule
  classes (action allowlist, evidence-must-exist, observed-only) overlap core actions\authorizer.py + approvals\gate.py;
  promote only if a rule is shown generic (docs\gate_rules.md lists 27 rules by class a-e; class (b) text rules read
  model text and are flagged HEURISTIC).
- J\resolver.py (589 L): diagnosis to fix plan. J\knowledge.py (305 L) + data\incident_signatures.yaml (858 L, 43
  signatures, reclassified PRODUCT by J2): incident catalogue. J\symptom.py, J\expected.py, J\postmortem.py wording.
- J\platforms\sim_k8s.py (634 L): DELETED by J2 per j0-classification; if still present on disk it is dead.
- J\checks.py (61 L): verify/undo callables for the simulator. J\paths.py generic (B7), J\render_config.py tooling.
- Demo-only data (generator, fault families, baits, canned replies) is under Jagrat demo_only\, not in src; nothing to
  promote, and core must never reference it (rule: demo-only folder).
- Held modules absent today: bounds (J2), history, chain, tools, links, cards, report (J4/J5), platforms\sim_db,
  cli (J5). They are not inventoried because they do not exist; do not promote before Jagrat builds them.

## 4. Suggested promotion batches (lead decides; ranked by value / risk)

Value is judged by how many demos consume it and whether the warden-reuse-audit already ranked it.
1. Batch P-A (cheap, low risk, wide use): A3 numbers, A2 evidence ids, A1 grounding core, A9 language, B1 freeze,
   B7 safe_path, A6+A7 confidence level + hand-back labels. ~800 L new core, 7 modules, each with tests that fail on
   a mutant. Consumers: Intake first, then Refunds.
2. Batch P-B (control plane, money/safety, uncapped review): B9 breaker+bounds merged with limits.py, D1-D5
   killswitch mechanics (decide copy vs package, see 1D), B8 per-target lock, B5 landed-check, B2 env policy
   table, B3 autonomy levels.
3. Batch P-C (security, uncapped review): A4 quarantine mechanism, B11 passkeys (behind a WebAuthn kind),
   B16 vault+reveal, B13/B14 webhook + read-scope.
4. Defer: B10 permits, B12 edge_auth, B15 MCP server, B17 codec, G1 Temporal runtime, C2-C6 record extras,
   Helios (separate tool), killswitch framework integrations (D6).

Existing open core PRs (#41, #42, #43, #47, #48; egm\hadavin-sdk\pr*\) were not read; some of the above may overlap
them (e.g. runtime control, outbox, reservations, leakcheck seen as stale .pyc). The lead must diff the plan
against those PRs before building (memory: check core first, extend rather than duplicate).

## 5. Decisions the lead should put to EGM / the owner

- Copy vs rewrite: audit says core rewrites to its own Protocol style. Recommend rewrite-from-spec with the Warden
  test as the oracle (copy the tests, adapt names), keeping Apache header where code is near-verbatim.
- agent-killswitch: copy into core (no new dependency) vs depend on the PyPI package behind a kind. Needs a call.
- Jagrat platforms Protocol (live/apply/healthy/rollback) vs core actions\contract.py (verify/undo): unify, do not
  create a second interface.
- Core licence vs Jagrat "all rights reserved": confirm core LICENSE and that promoting Jagrat-origin text is fine
  (prefer promoting from Warden's Apache copy, which has the same design).
- Rename hygiene: strip "WARDEN", "Eldane", "Helios", "Jagrat" from promoted docstrings and env var names
  (WARDEN_FREEZE_FILE etc. become core config keys). Core's reference-material guard and Jagrat's
  test_no_reference_names must both stay green.
- Re-pin sweep: after any core merge, Jagrat's pin (660814674ece) and all demo pins move (core-modules rule 5).
- Warden reference copy is stale vs GitHub (3 merges ahead per the 2026-10-30 audit: #203, #204 Slack member check,
  #205 licence; PR #206 bank-redaction patterns open). I did not re-check GitHub (read-only, no network). Re-sync
  or fetch before copying anything security-relevant.

## 6. Files read and what I could not verify

Read in full: templates\agents\BRIEF-PREAMBLE.md, memory\core-modules-one-source-of-truth.md,
memory\promote-generic-fixes-to-core.md, egm\jagrat\j0-classification.md, egm\hadavin-sdk\warden-reuse-audit.md
(lines 1-80), projects\jagrat\tests\held_modules.py, projects\hadavin-sdk\tests\test_no_reference_material.py
(first 60 L), core limits.py (first 40 L).
Read in part (docstring/first lines only, via a script): every projects\jagrat\src\jagrat\*.py, platforms\__init__.py,
about 40 reference\warden\src\warden\*.py module docstrings, reference\warden LICENSE/NOTICE head, LICENSE heads of
helios, agent-killswitch, temporal-cloud-sample, README heads of agent-killswitch, helios, temporal-cloud-sample,
head of projects\jagrat\docs\gate_rules.md. Directory listings and line counts for all five sources and core src.

NOT verified (treat the table's "in core?" and "size" columns accordingly):
1. Function bodies. Sizes are whole-file line counts, not the size of the generic slice; my "generic slice" numbers
   (e.g. grounding ~150-250 L) are estimates from docstrings, not measured.
2. Whether Jagrat modules differ materially from Warden's (only line counts and docstrings compared). Jagrat
   grounding is 1147 L vs Warden 815 L, so Jagrat has grown; diff before choosing a source.
3. "In core?" came from filename and keyword grep of src (.py) only. Core's cli.py, actions\executor.py, runtime\,
   approvals\gate.py (698 L) may implement parts of freeze/paths/lock ideas under other names.
4. Open core PR branches, other core worktrees (projects\wt-pr47, wt-kit-f7f297a) and the stale .pyc names: not read.
5. agent-killswitch, Helios, Temporal sample code bodies and tests: not read; capability descriptions come from
   README heads and file names. Test counts for any of them: not measured. I ran no tests.
6. Core's LICENSE and whether it is Apache-2.0; Jagrat has no LICENSE file.
7. Jagrat tests (test_socket_guard etc.) not opened; described by name only.
8. Bible R-numbers not grepped; the lead must cite them (bible-before-answering) when the plan turns into client or
   method claims. Nothing here states a measured metric.
9. Token use: about 14 tool calls, roughly 60k tokens of reading.
