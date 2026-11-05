# Gap register: what is still missing to build "any non-regulated project, any industry" from the core

Date: 2026-11-05 (UTC). Source: EGM gap hunt (design reviewer: 27 gaps G1-G27; zoom-out reviewer: scope and order, B1-B3 and M1-M6), the Core v1 plan (plan-v3), amendments A1-A12, the Assembly Kit plan (kit-plan-v2), the S0 report.
Who: CLOUD = bulk coding and tests in the cloud session; LAPTOP = needs the studio's own files (memory, bible, templates, contracts, hooks) so it is done on the laptop; OWNER = needs your decision or action. Severity: BLOCKER = a common project shape cannot be built or sold without it.
Honesty: these are findings from reviewers who read file names and some code; "none" means no keyword hit, not a full audit. Regulatory remarks (hiring-tool rules, anti-spam laws, privacy laws) are from general knowledge and must be checked before they appear in any client wording.

## A. Gaps in the BUILD (code and tests)
| # | Gap | Example | Sev | Who | Where planned |
|---|---|---|---|---|---|
| G1 | Conversational agent with tools: chat loop, tool-call loop, conversation store with retention and delete-by-user, human handoff, multi-turn test harness | e-commerce support bot | BLOCKER | CLOUD (code); LAPTOP (check bible R94-R98 wording) | new AK package "conversation kind" + recipe (g) |
| G2 | Inbound triggers and connectors: email inbox, webhook with signature check, scheduler, file drop, queue pull, one input kind feeding the step contract, dedupe with one final state | invoices by email | BLOCKER | CLOUD | new AK package "trigger kind"; P7a moves into the kit |
| G15 | Queue of "needs a person" items that survives restarts (assignment, age, reopen, content binding) | any approval flow | BLOCKER | CLOUD | P7k queue moves into the kit |
| G14 | Approvals screen (web) and a second approval channel (Teams or email), portal packaging decision | finance manager without Slack | BLOCKER | CLOUD (UI parts, channel); LAPTOP (premium-UI standard, portal kit); OWNER (portal packaging) | new AK package; D-kit decision |
| G16 | Deployment into the client's own cloud: container, infrastructure-as-code per cloud, minimal rights per part, runbook, smoke test; security-review pack | "must run in our AWS account" | BLOCKER | CLOUD (IaC, rights); LAPTOP (security pack from bible topic 36); OWNER (accounts, cost) | new package "deploy kit" |
| G3 | Connector wrapper and a tested catalogue of 5-8 common systems (OAuth refresh, pagination, idempotent writes, the manual executor) | CRM, ERP, ticketing | MAJOR | CLOUD; LAPTOP (which tools the studio sells) | new AK package |
| G4 | Client's own no-code tools (n8n, Zapier, Make, Power Automate) as trigger and actuator: "agent as an HTTP node" shape | marketing ops client with n8n | MAJOR | LAPTOP (policy memory, guide); CLOUD (endpoint) | new AK package |
| G5 | Extraction recipe lacks field-level evaluation, line items, master-list validation, correction loop into the golden set | invoice to ERP draft | MAJOR | CLOUD; LAPTOP (golden-set template C10) | recipe (a) extension |
| G6 | Images, scans and speech as inputs, behind the outbound gate | defect photos, scanned delivery notes, voice mail | MAJOR | CLOUD (code); OWNER (which vendor = sub-processor) | AK0 decides; deferred with trigger |
| G8 | Summaries and report drafting recipe (was deferred) | weekly status report, lease abstract | MAJOR | CLOUD | promote to recipe (h) |
| G9 | Agent evaluation: tool-routing and trajectory checks, simulated multi-turn user, judge calibration, regression gate in CI; AK4a needs P7f | any chat or tool agent | MAJOR | CLOUD | P7f moves into AK4a; new eval package |
| G10 | Prompt store with versions, hash in audit lines, diff and rollback, per-client overrides, change-then-rerun-golden-set command | tone change after a model upgrade | MAJOR | CLOUD (store); LAPTOP (studio prompt templates) | new AK package |
| G11 | Model fallback chain and routing by task, region pinning, per-model qualification, timeouts | model outage at peak; AU in-region need | MAJOR | CLOUD; LAPTOP (model choices memory) | new AK package; PR #48 breaker pieces |
| G12 | MCP client adapter (exact tool allowlist, results through the injection choke point, version pinning) and exposing governed actions as an MCP server | recruiting ATS, IT ops Jira | MAJOR | CLOUD; LAPTOP (vetted-vendor list) | new AK package (MCP was out of Core v1 scope) |
| G13 | Observability and cost dashboards: per-call log sink (P4e), cost per tenant per day, latency, abstain and error rates, alerts, drift monitor after go-live | "what did the bot cost in October" | MAJOR | CLOUD; LAPTOP (dashboard look) | P4e moves into the kit |
| G17 | Tenant separation beyond retrieval: tenant on store tables, per-tenant keys and budgets, per-tenant stop switch; or the rule "one deployment per client" written in the kit | platform serving many shops | MAJOR | CLOUD; OWNER (decide model) | P4d/AK1 carry tenant; decision needed |
| G18 | Retention and deletion: policy per data class, scheduled purge, delete-by-subject reaching vector store, caches, logs; coexistence with the hash-chained audit | UK/CA privacy requests | MAJOR | CLOUD (jobs); LAPTOP (contract clause) | new AK package |
| G21 | Long-running and batch jobs: worker pool, bounded concurrency, rate-limit budgeting, batch pricing, dead-letter replay, progress view | 5,000-document backlog | MAJOR | CLOUD | new AK package |
| G22 | Outbound messages as governed actions: recipient allowlist, send limits, tone check, consent flags, duplicate-send prevention | emails to candidates or suppliers | MAJOR | CLOUD; LAPTOP (consent rules, verify law) | P3b moves into the kit |
| G26 | Agent red-team suite in CI: direct and indirect injection, tool poisoning, link and image exfiltration | any agent reading outside text | MAJOR | CLOUD; LAPTOP (trifecta record C13) | new AK package |
| G7 | Classification quality: confusion matrix, per-class recall, confidence threshold to a person | ticket triage | MINOR | CLOUD | recipe (c) extension |
| G23 | Test-set production: sheet or tool, sampling protocol, inter-rater check, CSV-to-harness loader, minimum-size rule | every project | MINOR | LAPTOP (template); CLOUD (loader) | with P7f |
| G24 | Safe database questions beyond read-only: schema docs, column masking, query cost caps; depends on P3d | batch failure questions | MINOR | CLOUD | recipe (f) |
| G25 | Locale: dates, money, time zones, holidays, bilingual replies | Canadian French/English, AU holidays | MINOR | CLOUD | config in kit |
| New shapes | document generation with approval (letters, quotes), scheduled enrichment batch, monitoring agent with periodic checks | contracts, nightly product data | MAJOR | CLOUD | recipes (i), (j) |

## B. Gaps outside the code (process, knowledge, commercial)
| # | Gap | Sev | Who |
|---|---|---|---|
| C1 | Contract and statement-of-work template: scope, acceptance criteria, change control, IP of rules and prompts, liability cap, support after handover | BLOCKER | LAPTOP (draft; client-facing wording follows the bible), OWNER (terms) |
| C2 | Data-handling rule and data-processing terms: whether any real client data may enter laptop sessions, cloud sessions or the public repo; what the studio sees, stores and sends to model vendors; sub-processor list | BLOCKER | OWNER (decision), LAPTOP (write it) |
| C3 | Core licence and what the client receives (core is public and marked proprietary: undecided); third-party list per build (SBOM) | BLOCKER before any contract | OWNER |
| C4 | Security-questionnaire answers v0 and a data-flow and threat summary (derived from the kinds table and the client-profile gate) | BLOCKER for first security review | LAPTOP |
| C5 | Fixed-price build sheet and quote script per shape and per connector count; refuse-list screen (regulated work); capacity rule | MAJOR | OWNER, LAPTOP |
| C6 | Acceptance period, warranty and support terms (the 3-4 week limit is already your rule) | MAJOR | OWNER, LAPTOP |
| C7 | Client handover pack generator: runbook (stop switch, key rotation, restore, spend cap), operator guide, evaluation report, change log | MAJOR | LAPTOP (templates), CLOUD (generator) |
| C8 | Live smoke test: one real model call through the masking wrapper and the meter with a small owner-approved spend on the chosen backend (all four model backends are unverified live) | BLOCKER before any honest quote | OWNER (approve spend with numbers), LAPTOP (run) |
| C9 | Consumption model: demos hold byte copies of the core; decide pinned dependency or copies; project template that imports a pinned core (the scaffolder AK6 is then needed early) | MAJOR | OWNER (decide), CLOUD (scaffolder) |
| C10 | Budget line for cloud agent work and review services | MINOR | OWNER |
| C11 | Studio-file updates after decisions: memory notes (A1-A12, handover, model routing), bible rules to add (fold key carries a version; RAG masking policy), `templates\project\` extended (scoping, cost estimate, golden schema = the studio template's `golden.jsonl` wins), sync tool `core_sync_check.py` must skip `.venv*` folders, hooks kept equal in both repos | MAJOR | LAPTOP |

## C. Recommended order (from the zoom-out reviewer; needs your yes)
The reviewer judged Core v1 (25 packages, about 30 pull requests, nearly all strict review) plus the kit to be a hardening programme with no first client attached, and says the biggest risk is weeks of review with nothing to sell. It recommends a thin first slice:
1. Choose the first shape now: document intake with approvals (the Intake demo already exists); RAG second.
2. Core-slice (about 11 of the 25 packages): P1a, P2a, P3a, P4d, P4a, P4b1, P4b2, P5c, P6b1, P6a and the Intake consumer, plus the first inbound trigger and the approvals queue and screen (G2, G15, G14) which the slice also needs. The long redaction-diagnostics chain (P5a-P5b5), P4c, P6b2, P2d beyond what P5c needs, and re-pinning the other three demos move to run in the background after the slice.
3. One live smoke call (C8) and the commercial minimum (C1-C6) in parallel, owned by you and me.
4. Client-ready gate: slice passes, deployment runbook for one cloud, handover pack, commercial documents exist. Then quote a first project.
5. Extract recipes from the first real project; take the other kit packages when a named client needs them (small generic ones like the step contract and the test harness early; the scaffolder early because it is the real "hours" mechanism).
Tension to be honest about: your earlier decision was "full core first". This order keeps everything but puts the first sellable slice first and the rest in the background, so the cloud can work on both at once.
