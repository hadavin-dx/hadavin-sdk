# Market scan 2 (third pass, lead order 122): module table with "changed since scan 1"

Date: 2026-11-07. Cloud session, from four parallel research agents (pass 3-1 to 3-4) plus the scan-1 files. Research only, no ticket changes, no EGM review (EGM skipped: read-only research). Scan 1 is handover/reviews/market-scan-1.md; rows not re-examined in pass 3 are carried over and marked "no change (scan 1 only)".

## Honest limits (read first)
- Reachable from this machine: PyPI, npm, NuGet JSON, raw.githubusercontent.com (LICENSE files, docs repos), the AWS Price List JSON feed, and a few vendor pages (GCP pricing). NOT reachable: most vendor pricing and docs sites (DNS failures or 403), GitHub API and releases pages.
- Price labels: VERIFIED <date> (read the primary number: GCP Workflows/Cloud Tasks/Pub/Sub pages, AWS Price List feed), VERIFIED-SRC (vendor docs repo on raw.githubusercontent.com: Cloudflare, Azure docs examples), UNVERIFIED (everything else; aggregator numbers often conflict). Nothing UNVERIFIED should be quoted to a client.
- Licences: strict. SPDX from the LICENSE file is VERIFIED; claims from search summaries are UNVERIFIED. Flagged: AGPL (Lago, Unleash, Windmill, PyMuPDF), SSPL (Inngest server), BUSL (immudb, Budibase paid parts), ELv2 (Convoy), Sustainable-Use (n8n), source-available (Pipedream repo).
- Cover % remains each agent's judgement, not a measurement. No candidate was installed or run.
- Not searched even in pass 3: Restate, DBOS, Windmill (embedding), Svix, Hookdeck, pg-boss, Graphile Worker, Procrastinate (a Postgres queue library is the likeliest cheap WRAP for claim/lease/retry in AK-G2); Power Automate approvals; Rasa, Voiceflow, Crisp; Qdrant.
- The LEAD-FETCH list at the end has the URLs the lead can fetch from the laptop. (Counted by line: 79 raw lines across the four pass files, with overlaps; the de-duplicated list is below.)

## Corrections to scan 1 found in this pass
1. Cloudflare AI Gateway DLP: scan 1 said it can redact. The DLP setup page read in pass 3-1 offers only flag or block (pass 3-4 also lists it as "block/flag/redact, irreversible" from a snippet, so the two agents disagree: UNVERIFIED, LEAD-FETCH below).
2. LLM Guard: README says ARCHIVED (VERIFIED, pass 3-4). Scan 1 had only a third-party claim.
3. LiteLLM "$764 through a $50 cap" is issue 12977: a client-library bypass, closed stale, no concurrency. The race claim is unproven, not disproven. litellm 1.82.7 and 1.82.8 are removed from PyPI (VERIFIED); the malicious-release story still rests on secondary sources.
4. Helicone maintenance-mode: the README shows no such notice; the claim is secondary only.
5. Lakera: sale to Check Point reported closed 2025-10-22 (several secondary outlets).
6. AK-G15: native waits (Step Functions callbacks, Cloudflare Workflows waitForEvent, GCP Workflows callbacks, Azure Durable Functions) cover 55-70 percent of "wait and resume" for under USD 5 a month; none checks the item digest or separates the executor identity.

## Module table
Cover % = function / guarantee where the agent split them. Verdict values: ADOPT / WRAP / KEEP-CODE / DROP.

| Module | Best existing candidates (licence) | Cover % | What it cannot guarantee | Verdict | Changed since scan 1 |
|---|---|---|---|---|---|
| P1 / P1c text folding, redactor gaps | stdlib unicodedata NFKC, UTS #39 confusables data, Presidio recognisers (MIT) | 40-60 (P1c: base64 decode view and bare numbers not found) | folded copy of a known value impossible to send; evidence in tests | WRAP (P1) / KEEP-CODE (P1c) | no change (scan 1 only) |
| P2d fold scan + hidden-channel refusal | prompt-canon (S), guardrail products | low (~30 classifiers) | refuse the whole text when a folded known value survives masking | KEEP-CODE if redaction is sold as a guarantee; DROP for first-client scope | pass 3-4 now agrees KEEP-CODE-conditional; otherwise no change |
| P5c redactor kind + safe put-back | Presidio (MIT 2.2.366, 2026-10-27 VERIFIED), LiteLLM pii_masking, Cloudflare/Bedrock/Azure/GCP filters | detection 50-70; fail-closed + put-back 0-10 | masking BEFORE the model; no model call after a redactor error; restore in code | WRAP (detector) + KEEP-CODE (wrapper/put-back) | Bedrock, Azure, GCP, Cloudflare now compared: all irreversible, no put-back; LLM Guard confirmed archived |
| P5a closed error codes | OTel error.type vocabulary | 30 | closed vocabulary, nothing foreign in an error record | KEEP-CODE | no change |
| P5b1 provider error plumbing | OTel GenAI error.type (Development status: pin names), SDK exception classes | 55-65 | billing-safe retry classification | WRAP | no change |
| P5b2 / P5b5 CI site tables and pins | ast-grep (MIT), Semgrep CE, Opengrep | 85-90 | none beyond CI | ADOPT | no change |
| P5b3 rewire writers / P5b4 output guard | OTel Collector redaction processor, Langfuse mask fn | 15-25 / 40-50 | nothing raw reaches logs/stderr/crash hooks | KEEP-CODE | no change |
| P2a stop state | Cloudflare Durable Object + separate Worker, AWS IAM deny, Azure Durable Functions terminate; flag tools | 30-45 function / 5-15 guarantee | stop the running agent cannot clear; reset by a separate role; audited | KEEP-CODE | NEW detail (cloud services compared) |
| P3a migration rule, P4d store contract | Postgres migration tools, test suites | scan 1 | forward-only numbering, previous release reads new schema | WRAP (P3a) / KEEP-CODE (P4d) | no change (scan 1 only) |
| P0a backups, secrets kind, P6a/P6b2 profile + boundary checks, signer, audit | cloud secrets managers, config checks; audit logs (paid on every product read) | scan 1 | tamper-evident audit (no source shows write-once storage); separate executor identity | ADOPT / WRAP / KEEP-CODE per scan 1 | pass 3-3: audit logs paid on Langfuse Enterprise, Retool Business, Appsmith Business, Budibase Enterprise; guarantee stays ours |
| P4a usage / price tiers / refuse-instead-of-estimate | LiteLLM budgets (MIT core + commercial enterprise/ dir), gateways | visibility 70-90; hard cap under concurrency unproven | refuse instead of estimate | WRAP | LiteLLM incident re-examined (see corrections) |
| P4b1 reserve/settle meter | none found; TigerBeetle is a separate cluster | 0 for atomic reserve | hard cap under concurrent calls | KEEP-CODE | no change; proposed test: 50 parallel calls against a cap |
| P4b2 billing contract (billed vs unbilled failed calls) | no vendor publishes it | 0 | which failed/cut-off calls are billed | KEEP-CODE | no change |
| P4c alert ledger + max_run_usd | n8n/Slack alerts | scan 1 | loud wall at daily limit | WRAP | no change |
| Client invoicing (not a core module) | Stripe Billing (proprietary, SDK MIT), Lago (AGPL-3.0 VERIFIED, FLAG), Orb, OpenMeter | invoicing 85-90, spend wall 0 | spend wall | ADOPT Stripe for invoicing only; DROP Orb/Lago/OpenMeter for a small client | Lago licence VERIFIED AGPL; OpenMeter licence UNVERIFIED (repo moved); Orb acquisition rumour (single source) |
| P6b1 no-training check | provider terms, config check | scan 1: DROP as code | statement check | DROP as code (replace by a config/doc check; lead call) | no change; agent's weakest verdict |
| AK-G1 chat agent + hand-off | Port, Retool, Appsmith (Apache-2.0, v2.6.0, 2026-10-28 VERIFIED), Budibase (GPLv3 + BSL parts) as UI | UI 60-75; hand-off lease 10-20 | one lease per conversation, no double answer | WRAP in scan 1; pass 3-3 says KEEP-CODE for the lease/hand-off part | CHANGED: builders cannot hold the conversation lease |
| AK-G2 inbound trigger + ledger | SQS FIFO, Cloudflare Queues, GCP Pub/Sub exactly-once, Step Functions, Temporal (MIT), Hatchet (MIT) | function 50-70; guarantee 25-40 | same key, one effect, forever (every native service has a time-limited dedupe window: SQS FIFO 5 min, Cloud Tasks hours, Cloudflare Queues 24 h retention) | KEEP-CODE | CHANGED: Cloudflare Queues' 24 h ruled out for the ledger; test idea: replay same id after 6 min, 25 h, 31 d |
| AK-G15 needs-a-person queue | Step Functions waitForTaskToken, Cloudflare Workflows waitForEvent, GCP Workflows callbacks, Azure Durable Functions; Port/Retool/Appsmith UI | 55-70 wait+resume / 20-30 guarantee; UI 60-75 | item digest binding, separate executor identity, tenant isolation, one paid re-run | WRAP (waits) + KEEP-CODE (store, role, digest) | CHANGED: cloud waits quantified; GCP/Azure gaps closed |
| AK-G16 deploy into client cloud | Cloudflare per-Worker roles + wrangler, AWS CDK/SAM, Azure Functions, Kubernetes tooling | 40-60 mechanics; ~0 for the five-part split | five least-privilege parts | ADOPT (mechanics) | NEW: targets other than Kubernetes |
| JG-3 chat-ops notifier | n8n/Slack | n/a | n/a | DROP (paused by owner) | no change |
| AK0 research note | n/a | n/a | n/a | DROP | no change |
| AK1a step contract / AK1c tenant | Postgres RLS with FORCE | 85-90 tenant isolation | cross-tenant leakage tests | WRAP | no change |
| AK1b the ONE outbound gate | none | 0 | masking before every outbound call | KEEP-CODE | no change |
| AK2a document reader | docling, unstructured (licences per scan 1), PyMuPDF AGPL, MinerU/Marker restricted | scan 1 | hostile-file limits | WRAP | no change |
| AK4a eval gates + joined harness | Langfuse datasets/experiments (scoring ~50, gate stays ours), promptfoo (bought by OpenAI), DeepEval | scoring 50 | block release when eval fails; canaries across a whole run (no tool found) | WRAP (4a-1) / KEEP-CODE (4a-2) | pass 3-3: Langfuse evals provisional, LEAD-FETCH docs page |
| P8a/b/c repin, READMEs, proof pack | git, docs generators | scan 1 | n/a | ADOPT | no change |
| P0t stage rename | n/a | n/a | n/a | DROP (shipped; PR 83 follow-up open) | no change |

Several rows carry mixed verdicts (WRAP for the adapter, KEEP-CODE for the guarantee part), so I give no single tally for the table. The per-product pass-3 verdicts: pass 3-1: ADOPT 1, WRAP 1, KEEP-CODE 2, DROP 0; pass 3-2 (12 products): ADOPT 2 (n8n, Activepieces), WRAP 2 (Temporal, Hatchet), DROP 8; pass 3-3 (9 rows): ADOPT 2, WRAP 2, KEEP-CODE 5; pass 3-4 (13 products): ADOPT 2, WRAP 2, DROP 9, plus modules WRAP 3 / KEEP-CODE 3.

## Top 3 offers Hadavin can sell on n8n + Close + Claude alone (first client, small budget)
Evidence (secondary, UNVERIFIED prices): n8n Starter about EUR 20-24 a month, Pro about EUR 50-60; Close roughly USD 9-139 per user per month; Close has a hosted MCP server, but its help centre reportedly limits n8n to read scope (conflicting snippets); n8n has Meta CAPI templates. No ready Close-to-CAPI n8n template found; Datahash sells a hosted sync.
1. Lead capture to Close with dedupe and an alert (forms and Meta lead ads), plus Meta CAPI feedback from Close stages (hash e-mail/phone, event id for dedup). Low risk: no money moves, no regulated data.
2. Speed-to-lead: Claude drafts the first reply, a person sends it (n8n human-in-the-loop step), plus lead qualification and scoring written to Close fields.
3. Call and meeting summaries with follow-up task drafts into Close, or an FAQ bot over a few clean documents with an "ask a person" fallback.
Licence note: n8n is Sustainable-Use, not OSI. The client can own and run it for their own internal use; reselling n8n as the agency's product is the trap. Activepieces (MIT outside ee dirs) is the resale-safe alternative.
Needs our modules: any offer where a model sees regulated personal data and the client must prove masking happened first (AK1b gate, P5c); any action that moves money (P4b1/P4b2, approvals with a separate executor, P2a); several clients on one store (AK1c or RLS config); public file uploads (AK2a); a contracted quality promise (AK4a); retries that must not double-apply (AK-G2 ledger).

## Per KEEP-CODE module: the single guarantee it protects and a test idea
| Module | Single guarantee | Test idea |
|---|---|---|
| P1c / P1 | a folded copy of a known value cannot reach a model | fixture table of look-alike forms must be masked or refused |
| P2d | text with a hidden channel is refused when raw masking missed a folded known value | folded known value inside folded text, raw mask misses, expect refusal |
| P5c wrapper + put-back | masking happens BEFORE the model; no model call after a redactor error; restore in code only | force the redactor to raise; assert zero provider calls |
| P5a / P5b3 / P5b4 | no foreign text in diagnostics, logs, stderr | hostile corpus through every writer; assert nothing raw |
| P2a | a stop cannot be cleared by the stopped agent | agent role attempts reset; expect denial and audit row |
| P4b1 | the cap holds under concurrent calls | 50 parallel reservations against one cap; sum never exceeds cap |
| P4b2 | which failed provider calls were billed is classified | recorded provider-error fixtures map to billed/unbilled |
| P4d | one contract over memory and Postgres | same suite runs on both stores |
| AK-G2 ledger | same key, one effect, forever | replay the same id after 6 minutes, 25 hours, 31 days; one effect |
| AK-G15 store | approver is a separate DB role; item digest bound; one paid re-run | approve with a changed digest; expect refusal |
| AK-G1 hand-off | one lease per conversation | two humans claim at once; one wins |
| AK1b outbound gate | masking before every outbound call | route a call around the gate; test fails |
| AK4a-2 harness | canaries planted and found across logs, audit and cross-tenant output | planted canary in one tenant never appears elsewhere |

## LEAD-FETCH (de-duplicated by URL where possible; full per-item lists are inside the pass files below)
LEAD-FETCH: https://aws.amazon.com/bedrock/pricing/ for P5c
LEAD-FETCH: https://aws.amazon.com/sqs/pricing/ for AK-G2 (free tier and retention maximum)
LEAD-FETCH: https://aws.amazon.com/step-functions/pricing/ for AK-G15 (free tier 4,000 transitions; how a
LEAD-FETCH: https://azure.microsoft.com/en-us/pricing/details/functions/ for AK-G15 (Durable Task Scheduler Dedicated per CU and Consumption per action; Flex Consumption)
LEAD-FETCH: https://azure.microsoft.com/en-us/pricing/details/logic-apps/ for AK-G15 (Consumption per-action and connector rates; Standard plan)
LEAD-FETCH: https://azure.microsoft.com/pricing/details/language/ for P5c
LEAD-FETCH: https://budibase.com/pricing/ for AK-G15 portal UI price and audit logs
LEAD-FETCH: https://cloud.google.com/security/products/model-armor/pricing for P5c
LEAD-FETCH: https://dagster.io/pricing for AK1 pipeline step
LEAD-FETCH: https://developers.cloudflare.com/agents/guides/human-in-the-loop for AK-G15 (
LEAD-FETCH: https://developers.cloudflare.com/ai-gateway/reference/pricing/ for P5c
LEAD-FETCH: https://developers.cloudflare.com/queues/platform/pricing/ for AK-G2 (confirm the rendered page matches the docs source: USD 0.40/million, 4-day default and 14-day retention)
LEAD-FETCH: https://developers.cloudflare.com/workflows/reference/pricing/ for AK-G15 (steps USD 0.80 per 100,000; billing start 2026-08-10)
LEAD-FETCH: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html for AK-G2 (5-minute dedupe window; URL from memory, may need search)
LEAD-FETCH: https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html for AK-G2 (exactly-once wording for Standard)
LEAD-FETCH: https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html for AK-G15 (90-day history, 1-year duration, 25,000 events)
LEAD-FETCH: https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery for AK-G2 (regional, pull-only limits)
LEAD-FETCH: https://docs.cloud.google.com/tasks/docs/how-to for AK-G2 (task-name dedupe window)
LEAD-FETCH: https://docs.cloud.google.com/workflows/docs/creating-callback-endpoints for AK-G15 (callback idempotency, IAM, slots)
LEAD-FETCH: https://docs.cloud.google.com/workflows/quotas for AK-G15 (retention 90 days, duration 1 year)
LEAD-FETCH: https://docs.hatchet.run/v1/idempotency for AK-G2 dedupe semantics
LEAD-FETCH: https://docs.litellm.ai/blog/security-update-march-2026 for P4 gateway decision
LEAD-FETCH: https://docs.litellm.ai/blog/security-update-march-2026 for P4 gateway decision.
LEAD-FETCH: https://docs.litellm.ai/docs/proxy/guardrails/pii_masking_v2 for P5c (fail open/closed, streaming)
LEAD-FETCH: https://docs.litellm.ai/docs/proxy/users for P4b1 (budget enforcement semantics)
LEAD-FETCH: https://docs.n8n.io/hosting/community-edition-features/ for AK-G15 (Enterprise-only features)
LEAD-FETCH: https://docs.retool.com/org-users/guides/audit-logs for AK-G15 audit view and retention
LEAD-FETCH: https://github.com/Azure/azure-functions-durable-extension/releases for AK-G15 (release notes; NuGet date already read)
LEAD-FETCH: https://github.com/cloudflare/workerd/releases for AK-G16 (release date of the runtime; npm dates already read)
LEAD-FETCH: https://hatchet.run/pricing for AK-G2/AK-G15 backend cost
LEAD-FETCH: https://kestra.io/pricing for AK-G15 (Pause task edition)
LEAD-FETCH: https://langfuse.com/docs/evaluation/overview for evals gates
LEAD-FETCH: https://langfuse.com/pricing for Langfuse price (all tiers, units, retention)
LEAD-FETCH: https://langfuse.com/self-hosting/license-key for Langfuse audit-log/masking gating
LEAD-FETCH: https://microsoft.github.io/presidio/anonymizer/ for P5c (reversibility)
LEAD-FETCH: https://n8n.io/pricing for AK-G2/AK-G15 forwarder and approval channel cost
LEAD-FETCH: https://opentelemetry.io/docs/specs/semconv/gen-ai/ for P5a/P5b1 attribute names and status
LEAD-FETCH: https://pipedream.com/pricing for n8n comparison
LEAD-FETCH: https://retool.com/pricing for AK-G15 portal UI price (audit logs, external users)
LEAD-FETCH: https://temporal.io/pricing for AK-G2/AK-G15 backend cost
LEAD-FETCH: https://temporal.io/pricing for AK-G2/AK-G15 backend cost.
LEAD-FETCH: https://trigger.dev/pricing for AK-G15 approval channel cost
LEAD-FETCH: https://www.activepieces.com/pricing for n8n comparison
LEAD-FETCH: https://www.appsmith.com/pricing for AK-G15 portal UI price and audit logs
LEAD-FETCH: https://www.helicone.ai/pricing for Helicone price
LEAD-FETCH: https://www.inngest.com/pricing for AK-G2 backend cost
LEAD-FETCH: https://www.lakera.ai/pricing for P2d
LEAD-FETCH: https://www.make.com/en/pricing for n8n comparison
LEAD-FETCH: https://www.mintlify.com/blog/mintlify-acquires-helicone for Helicone maintenance-mode wording
LEAD-FETCH: https://www.prefect.io/pricing for AK-G15
LEAD-FETCH: https://zapier.com/pricing for n8n comparison

(Entries listed as 'https://... , https://...' or with notes are in the pass files; a few lines name a path with no URL, e.g. the Budibase licence file.)

# PASS 3-1 (full agent file)

# Market scan, pass 3, group 1: Cloudflare, GCP Workflows, Azure (Logic Apps, Durable Functions), AWS (Step Functions, SQS, EventBridge)

Written 2026-11-07 by the pass-3 research agent for lead ORDER 122. Research only, no ticket changes. EGM skipped: read-only research (EGM-GATE v1).
Modules: P2a stop state, AK-G2 inbound ledger, AK-G15 needs-a-person queue, AK-G16 deployment into the client's cloud. Scan 1 (`reviews/market-scan-1.md`) is extended and corrected, not repeated.

## 0. How strong is this evidence (read first)

- Reachable from this machine (tested 2026-11-07): `raw.githubusercontent.com` (LICENSE files and vendor docs repos), `registry.npmjs.org`, `pypi.org`, `api.nuget.org`, `pricing.us-east-1.amazonaws.com` (AWS Price List files), `cloud.google.com/*/pricing` pages. NOT reachable (CONNECT 403 or DNS fail): `developers.cloudflare.com`, `aws.amazon.com`, `docs.aws.amazon.com`, `azure.microsoft.com`, `learn.microsoft.com`, `prices.azure.com`, `docs.cloud.google.com` (cloud.google.com docs pages redirect to it), `api.github.com`, `github.com`.
- Price labels used below:
  - **VERIFIED 2026-11-07 (page)**: I fetched the vendor pricing page and read the number (GCP Workflows, Cloud Tasks, Pub/Sub).
  - **VERIFIED 2026-11-07 (feed)**: AWS Price List JSON, the machine feed AWS publishes (not the marketing page). Free tiers are not in that feed.
  - **VERIFIED-SRC 2026-11-07**: read in the vendor's own docs repository (`cloudflare/cloudflare-docs` branch `production`, `MicrosoftDocs/azure-docs` branch `main`) via raw.githubusercontent.com. It is the source file of the rendered page; I could not read the rendered page. A LEAD-FETCH line is given for each so the lead can confirm.
  - **UNVERIFIED**: search-result snippet, aggregator or memory.
- Last release dates come from npm, PyPI and NuGet JSON (primary registry data). GitHub releases pages were blocked, so a GitHub release date is never claimed.
- Hosted cloud services (Workers, Queues, Step Functions, ...) are proprietary vendor terms; I did not read the terms of service (UNVERIFIED), so their licence column says "proprietary SaaS, terms UNVERIFIED". No GPL, AGPL, SSPL, BUSL, ELv2 or Sustainable-Use item turned up in this group.

## 1. Summary table

Cover % is my judgement of the need as the ticket words it, with the evidence in section 3. "Guarantee gap" is what the product cannot give.

| Module | Need (one line) | Best candidates in this group | Cover % function / guarantee | Changed since scan 1 | Verdict |
|---|---|---|---|---|---|
| P2a stop state | Durable stop the running agent cannot clear; reset by a separate role; audited | Cloudflare Durable Object + separate Worker (role per Worker); AWS IAM deny + session revoke; Azure Durable Functions terminate | 30-45 function / 5-15 guarantee | New (scan 1 listed only flag tools) | KEEP-CODE (unchanged) |
| AK-G2 inbound ledger | Signed door + receipt keyed by stable id; no lost, no double-applied | SQS FIFO; Cloudflare Queues + Durable Object ledger; GCP Pub/Sub exactly-once; Step Functions Standard; Azure Durable Functions instance id | 50-70 function / 25-40 guarantee (effect in same transaction) | Cloudflare retention corrected; GCP and Azure gaps closed | KEEP-CODE (unchanged); cloud queue only as optional front buffer |
| AK-G15 needs-a-person queue | Queue of items, claim with lease, one final outcome, binding, separate executor | Cloudflare Workflows `waitForEvent`; GCP Workflows callbacks; AWS Step Functions `waitForTaskToken`; Azure Durable Functions human-interaction | 55-70 function (wait + resume) / 20-30 guarantee | GCP and Azure gap closed; Cloudflare added | WRAP (unchanged) |
| AK-G16 deploy into client cloud | Render, lint, run five least-privilege parts in client's cloud | Cloudflare per-Worker roles + wrangler; AWS CDK / SAM; Azure Functions; GCP | 40-60 for "deploy mechanics" on these four platforms; ~0 for the five-part split | New: these targets are not Kubernetes; part split maps to roles per Worker or per function | ADOPT for mechanics (unchanged); no per-cloud adapter |

Verdict counts for my four modules: ADOPT 1, WRAP 1, KEEP-CODE 2, DROP 0. Same as scan 1 for these modules; evidence is firmer and two sub-claims of scan 1 were wrong (section 5).

## 2. Queries run (all WebSearch, 2026-11-07; plus fetches listed in Sources)

Cloudflare group (7 searches, 20+ doc-source fetches)
1. Cloudflare Workflows waitForEvent human approval step.waitForEvent sendEvent
2. Cloudflare Durable Objects SQLite point-in-time recovery transactional storage output gates alarms at-least-once
3. Cloudflare Queues exactly-once delivery dead letter queue pull consumer idempotency 2026
4. Terraform provider Cloudflare Workers deploy customer account least privilege API token scopes ...
5. Cloudflare Agents SDK human-in-the-loop approval tool confirmation needsApproval Durable Object 2026
6. (earlier in this session) Cloudflare pricing of Queues, Workflows, Durable Objects, AI Gateway: read from docs source
7. Cloudflare AI Gateway spend limits / DLP / guardrails: read from docs source

GCP group (6)
1. Google Cloud Workflows callbacks human approval at-least-once execution idempotency Eventarc Cloud Tasks exactly once
2. Google Cloud Workflows execution retention 90 days maximum execution duration one year quotas limits steps
3. Cloud Tasks task name deduplication one hour tombstone "at least once"
4. Pub/Sub exactly-once delivery pull subscriptions regional limitation
5. Workflows callbacks await_callback authorize callback endpoint IAM workflows.callbacks.send
6. Pricing pages fetched (Workflows, Cloud Tasks, Pub/Sub)

Azure group (7)
1. Azure Logic Apps Consumption pricing per action execution $0.000025 standard connector
2. Azure Durable Functions at-least-once orchestrator activity idempotent external events human interaction approval timeout
3. Azure Durable Task Scheduler pricing per month dedicated capacity unit
4. Azure Logic Apps approvals connector "Create an approval" Approvals connector Teams Outlook
5. Azure Functions Durable Functions Flex Consumption pricing storage transactions task hub
6. Azure Durable Functions start orchestration same instance ID idempotent singleton
7. Logic Apps pricing and Durable Task docs read from the Azure docs repo

AWS group (8)
1. AWS Step Functions waitForTaskToken callback human approval standard workflow exactly-once execution history 90 days
2. AWS Step Functions pricing state transition $0.025 per 1,000 free tier 4,000
3. SQS FIFO exactly-once processing deduplication ID 5 minute window message group
4. Step Functions Standard workflows exactly-once workflow execution Express at-least-once
5. Step Functions Standard execution history retained 90 days maximum duration one year quotas
6. EventBridge Scheduler SQS dead-letter queue redrive Step Functions idempotency StartExecution same name
7. AWS IAM explicit deny emergency kill switch revoke agent role sessions
8. AWS Price List files for Step Functions, SQS, EventBridge (feed)

## 3. Per-module detail

### 3.1 P2a stop state

1. Need: a stop switch the running agent cannot clear; reset only by a separate role; every reset audited; version-and-count token against stale resets (P2a ticket revision 10, first 25 lines read; its Route A is a Postgres guard plus separate reset credential).
2. Candidates and evidence (all about hosting the switch on the client's cloud instead of Postgres):
   - **Cloudflare Worker + Durable Object (DO) as the switch.** A DO has "private, transactional, and strongly consistent" storage (VERIFIED-SRC, `durable-objects/best-practices/access-durable-objects-storage.mdx`); SQLite-backed DOs have a 30-day point-in-time restore API (VERIFIED-SRC, `api/sqlite-storage-api.mdx`); DOs have no roles of their own, they inherit the role on the Worker that implements them, and Data Studio can modify DO data with Editor on that Worker (VERIFIED-SRC, `workers/authorization/durable-objects.mdx`); per-Worker roles (Metadata Read-Only, Content Read-Only, Editor, Admin) exist since 2026-09-15 (VERIFIED-SRC changelog). Cover 40 (function). Guarantee gap: a stop and a reset are separated only if the agent Worker holds no binding that can write; that is a deployment discipline, not a database guard (my reading; UNVERIFIED on service-binding details). Anyone with Editor on the stop Worker can edit the table by hand in Data Studio, so "audited reset by a separate role" needs our own append-only table and our own trigger-equivalent. Price: Workers Paid USD 5 per month minimum (VERIFIED-SRC 2026-11-07, `workers/platform/pricing.mdx`), DO requests USD 0.15 per million after 1 million (VERIFIED-SRC). Licence: proprietary SaaS; `workerd` runtime Apache-2.0 (LICENSE file read), wrangler `MIT OR Apache-2.0` (npm). Lock-in: high on DO.
   - **AWS IAM explicit deny / revoke sessions.** Revoking sessions attaches an inline policy `AWSRevokeOlderSessions` that denies everything for sessions issued before a time (AWS docs, search snippet); it does not affect long-term IAM user credentials; active tokens may keep working per a third-party tool's notes (snippets). Cover 35: this is an infrastructure kill of the agent identity, good for "freeze this role"; it does not stop calls the agent makes to Close or Meta with its own keys, and it has no stop-request table, count token or audit row. Price: IAM free (UNVERIFIED). The client can own it: yes.
   - **Azure Durable Functions terminate/suspend.** Instance-management API has terminate, suspend, resume, purge (VERIFIED-SRC 2026-11-07, `durable-task/common/durable-task-instance-management.md`). Cover 30: stops running orchestrations, no durable global switch. Licence MIT (extension LICENSE file read); NuGet `Microsoft.Azure.Functions.Worker.Extensions.DurableTask` 1.21.1 published 2026-11-05 (NuGet).
   - **GCP**: no stop-switch feature found for Workflows (cancel an execution exists in my memory, UNVERIFIED; docs host unreachable). Est cover 20, UNVERIFIED.
3. Cannot guarantee (of the seven classes): tamper-evident audit of reset; reset by a separate identity enforced at the data layer; "agent role cannot clear" proven by a test (cloud IAM gives it by policy, but nobody ships a test for it). Money exactness, masking, tenant isolation, eval gates: not applicable.
4. Verdict: **KEEP-CODE.** Guarantee: after a stop, no agent-side role can clear it, and every reset writes an audit row by a different role. Test idea: from the agent identity attempt delete/update/disable-alarm/restore-bookmark on the switch store; all must fail; reset by the stopper identity succeeds and writes an audit row. If a client is already all-Cloudflare or all-AWS, the module needs a second backend (not a decision for this scan).
5. First-client offers with only n8n + Close + Claude: a pause toggle (deactivate the n8n workflow). Truly needs our module: an agent that spends money or messages customers unattended.
6. Monthly price small client: Cloudflare USD 5 (Paid minimum, VERIFIED-SRC); AWS about USD 0 for IAM (UNVERIFIED). Client can own the licence: yes (their account).
7. Changed since scan 1: new candidates only; scan-1 verdict stands.

### 3.2 AK-G2 inbound ledger (no lost, no double-applied)

1. Need: one signed door; receipt row written before the sender hears "accepted"; delivery key; one `StepInput` per message; reopen creates a new generation (AK-G2 ticket, first 30 lines read).
2. Candidates and evidence:
   - **AWS SQS FIFO.** Dedup id kept at least 5 minutes, "continues to track the dedup id even after the message is received and deleted"; reusing the id after the window may queue another message (AWS SDK reference and a third-party article, snippets; UNVERIFIED on the primary page; LEAD-FETCH below). Price VERIFIED 2026-11-07 (feed, publication 2026-09-11, US East N. Virginia): standard USD 0.40 per million requests, FIFO USD 0.50 per million (tier 1). Cover 50 function, 25 guarantee: the dedupe window is minutes, not forever, and the dedupe record is not in the effect's transaction. Licence: SDK `@aws-sdk/client-sqs` Apache-2.0, 3.1164.0 published 2026-11-06 (npm).
   - **Cloudflare Queues (+ Durable Object ledger).** "At least once" delivery, "may be delivered more than once"; Cloudflare itself tells you to use a unique id as an idempotency key or primary key (VERIFIED-SRC, `queues/reference/delivery-guarantees.mdx`). Messages "should never be lost once the write succeeds" but are not ordered (VERIFIED-SRC, `how-queues-works.mdx`). Retention: Free 24 hours fixed; Paid default 4 days, configurable to 14 days (VERIFIED-SRC, queues_pricing partial). Price: Workers Paid USD 5 minimum; 1 million operations/month included then USD 0.40 per million; 3 operations per message (VERIFIED-SRC). A DO with SQLite and `transactionSync` could hold the receipt table and the effect rows in one transaction when the effect is also in that DO's storage (my reading of "transactional" docs; UNVERIFIED for a cross-object effect). Cover 60 function, 30 guarantee (only if the effect is in the same store). Lock-in high.
   - **GCP Pub/Sub exactly-once.** Pull and StreamingPull only, scoped to one region, and Google says it does not extend to side effects in downstream systems (Google docs, search snippet). Price VERIFIED 2026-11-07 (page): first 10 GiB/month free then USD 40 per TiB; Cloud Tasks first 1,000,000 operations free then USD 0.40 per million (page). **Cloud Tasks** name dedupe: tombstone window reported as 1 h, 4 h, 24 h or 9 days by different Google pages (snippets, conflicting); designed for at-least-once delivery. Cover 50 / 20.
   - **AWS Step Functions Standard.** AWS says Standard workflows are exactly-once execution ("tasks and states never run more than once unless you specify Retry") and Express are at-least-once (async) or at-most-once (sync) (AWS docs, search snippet; LEAD-FETCH). Whether `StartExecution` with a repeated name is rejected for 90 days: not found (UNVERIFIED, I will not claim it). Cover 40 / 25.
   - **Azure Durable Functions.** Activity functions and external events are "at-least-once"; Microsoft recommends events carry an id so the orchestrator can de-duplicate them (VERIFIED-SRC, `durable-task-external-events.md`). Fixed instance id gives a singleton, but the check-then-start pattern has a race: "both calls might report success, but only one orchestration instance actually starts" (VERIFIED-SRC, `durable-task-singletons.md`). Cover 45 / 25.
   - **EventBridge.** Price feed (VERIFIED 2026-11-07, feed 2026-09-24): custom events USD 1.00 per million; archive USD 0.10 per GB; the feed also lists an `EventsV2-DeduplicationByContent` meter. I did not read what that feature guarantees (UNVERIFIED); not counted in cover.
3. Cannot guarantee: "no lost AND no double-applied" is end to end. Every service above is at-least-once or has a time-limited dedupe window; none puts the dedupe record in the same transaction as the business effect; none gives a per-tenant keyed hash of the sender id; none lets you reopen with a new generation. Tenant isolation (separate signing key per tenant): not provided by any of them.
4. Verdict: **KEEP-CODE** for the ledger. Guarantee: same delivery key results in exactly one `StepInput` run across crash and replay, forever (not a 5-minute window). Test idea: fire the same signed delivery 100 times concurrently and kill the process at random points; assert one effect and no unprocessed receipt; additionally replay the id after 6 minutes, after 25 hours and after 31 days, and assert still one effect (this kills SQS FIFO and Cloud Tasks as sole dedupe). Optional ADOPT of SQS or Cloudflare Queues as a front buffer to absorb bursts; they are cheap but are not the ledger.
5. First-client offers on n8n + Close + Claude alone: "form to CRM", "email in, lead out". Truly needs our ledger: any inbound message that triggers money or an irreversible action.
6. Monthly price small client (3,000 messages): SQS about USD 0 (under 1 million requests; free tier itself UNVERIFIED); Cloudflare USD 5; GCP under USD 1 (page: a month with 6,500 internal and 3,999 external steps costs USD 0.07). Client can own the licence: yes (their cloud account).
7. Changed since scan 1: (a) Scan 1 rejected Cloudflare Queues for "24-hour retention". That is the Free plan only; Paid is 4 days default, up to 14. The rejection still holds for a permanent ledger (at-least-once, no dedupe, 14 days max). (b) GCP and Azure rows are now evidenced. (c) Verdict unchanged.

### 3.3 AK-G15 durable queue of "needs a person" items and approvals

1. Need: items, claim with a lease, close with one outcome; action bound to the item digest; executor is a separate identity; item survives erasure; per-tenant ceiling (AK-G15 ticket, first 30 lines read).
2. Candidates and evidence:
   - **Cloudflare Workflows `waitForEvent` + `sendEvent`.** Wait with a `type` (up to 100 chars, letters, digits, `-`, `_`), timeout default 24 hours, 1 second to 365 days (VERIFIED-SRC, `events-and-parameters.mdx`); waiting instances do not count against concurrency (VERIFIED-SRC, limits); instance state kept 3 days (Free) or 7 days default, up to 30 (Paid) (VERIFIED-SRC); event payload max 1 MiB; steps may be retried so side effects must be idempotent (VERIFIED-SRC, `rules-of-workflows.mdx`). Cloudflare's Agents SDK documents `waitForApproval()` backed by Workflows (search snippet of the Cloudflare docs; `agents` npm 0.33.0, MIT, 2026-11-03; pre-1.0). Price VERIFIED-SRC 2026-11-07: Workers Paid USD 5/month; 500,000 steps/month included then USD 0.80 per 100,000; storage 1 GB-month included then USD 0.20; step and storage billing started 2026-08-10 (docs text). Free plan: 3,000 steps/day. Cover 60 function (durable wait, timeout, resume, idempotent id), 20 guarantee. Gap: the party that can call `sendEvent` is whoever holds the Workflow binding or API token; there is no digest check and no lease/claim queue or UI.
   - **GCP Workflows callbacks.** `events.create_callback_endpoint` plus `events.await_callback`; caller needs `workflows.callbacks.send` (bundled in the Workflows Invoker role); callbacks are "fully idempotent" so a failed callback can be retried; 10 concurrent callbacks; execution retention 90 days, maximum duration 1 year, 100,000 steps (Google docs snippets; LEAD-FETCH). Price VERIFIED 2026-11-07 (page): 5,000 internal steps/month free, then USD 0.01 per 1,000; 2,000 external steps free, then USD 0.025 per 1,000. Cover 60 / 20. Closes the scan-1 gap "GCP Workflows callbacks: UNVERIFIED".
   - **AWS Step Functions `.waitForTaskToken`.** Standard only (Express has no callback integration); max duration 1 year; history 90 days after close; 25,000 events per execution (AWS docs, snippets; LEAD-FETCH). Price VERIFIED 2026-11-07 (feed 2026-11-04): USD 0.000025 per state transition (= USD 25 per million); free tier 4,000/month UNVERIFIED (snippet). Cover 65 / 20: the token holder can act; no digest binding.
   - **Azure Durable Functions human-interaction.** Orchestrator calls an activity to notify, starts a durable timer, waits on an external event, `WhenAny` of the two; "cancel timers you no longer need" (VERIFIED-SRC, `durable-task-human-interaction.md`). External events are at-least-once, so the approval must carry an id (VERIFIED-SRC). Price: Durable Task Scheduler is billed separately from compute; Dedicated = fixed per Capacity Unit, HA needs 3 CU; Consumption = per action, 30-day retention (VERIFIED-SRC, `durable-task-scheduler-billing.md`, dated 2026-05-01); the dollar amounts are on `azure.microsoft.com` (unreachable): UNVERIFIED. Cover 60 / 20.
   - **Azure Logic Apps.** No native Approvals connector (Microsoft Q&A answers, search snippet; workarounds: Teams "post adaptive card and wait for response", or call Power Automate). Consumption per-action rates in aggregators: built-in about USD 0.000025, standard connector about USD 0.000125 (UNVERIFIED, sources conflict). The Standard hosting plan WS1 is USD 175.16/month in Microsoft's own docs example for "an example region" (VERIFIED-SRC 2026-11-07, `logic-apps-pricing.md`; illustrative only). Cover 40 / 10.
3. Cannot guarantee: approval bound to the exact item digest; executor under a different identity than the agent; one final state with compare-and-set; item remains after content erasure with ids only; tenant ceiling that refuses loudly. These are guarantee-class for the money or record-changing paths.
4. Verdict: **WRAP.** Unchanged. A client already on one of these clouds can get the wait-and-resume part (55-70%) from the native service for cents; ours stays the thin table with version compare-and-set, digest binding and the worker role. Test idea: two workers close the same item concurrently, exactly one wins; send the callback or event with a wrong digest and assert refusal; erase the subject and assert the item row remains without text.
5. First-client offers on n8n alone: "draft reply, human approves in Slack, then send". Truly needs our module: approvals that move money or change records and must be provable later with a separate executor.
6. Monthly price small client (300 approvals): Cloudflare USD 5; AWS under USD 1 (about 8 transitions each: 2,400 transitions; USD 0.06 if outside the free tier); GCP under USD 1; Azure Consumption roughly cents (UNVERIFIED); Logic Apps Standard about USD 175 (docs example). Client can own the licence: yes.
7. Changed since scan 1: GCP and Azure rows filled; Cloudflare Workflows added; Logic Apps "no approvals connector" re-confirmed from a second search; Step Functions price now VERIFIED (feed) at USD 25 per million; the 4,000 free-transition claim stays UNVERIFIED. Verdict unchanged.

### 3.4 AK-G16 deployment into the client's own cloud

1. Need: render files, lint, run the assembled agent as five least-privilege parts in the client's cloud, options-first quote (AK-G16 ticket, first 30 lines read).
2. Candidates and evidence (what these four platforms add beyond Helm/Kustomize/OpenTofu in scan 1):
   - **Cloudflare**: `wrangler` 4.158.0 published 2026-11-05 (npm, `MIT OR Apache-2.0`); `miniflare` MIT; `workerd` Apache-2.0 (LICENSE file). Deploy tokens can be scoped to specific Workers with Editor role, so a CI token cannot delete or touch other Workers (VERIFIED-SRC changelog 2026-09-15). The five-part split maps onto five Workers each with its own bindings and secrets, which gives per-part least privilege by construction (my reading, UNVERIFIED in practice). Queue consumer CPU limit 15 minutes; Workers Paid USD 5. Cover 50 for mechanics.
   - **AWS**: AWS CDK `aws-cdk` Apache-2.0 (LICENSE file read); SAM CLI Apache-2.0 (LICENSE file read); `boto3` 1.43.126 Apache-2.0, 2026-11-06 (PyPI). IAM roles per Lambda/task give the same split. Cover 55.
   - **Azure**: Durable Functions extension MIT (LICENSE file), `azure-functions-durable` (Python) 1.7.0 MIT, 2026-07-30 (PyPI); `durable-functions` (npm) 3.6.0 MIT, 2026-10-14. Cover 45; Logic Apps is a designer/ARM template product, poor fit for our rendered files.
   - **GCP**: `google-cloud-workflows` 1.24.0 Apache-2.0, 2026-10-01 (PyPI); `@google-cloud/workflows` 6.2.0 Apache-2.0, 2026-10-12 (npm). Cover 45.
3. Cannot guarantee: that the purge or reset part truly cannot read the signing key; "what is running in the cloud" equals what was rendered. These come from our build and tests, not from the platform.
4. Verdict: **ADOPT** for deploy mechanics, same as scan 1: no home-made per-cloud adapter. Part split stays ours. Test idea (unchanged): render the purge part, list mounted secrets or bindings, assert signer and anchor secrets absent; inject the signer secret and assert refusal.
5. First-client offers on n8n alone: none need a deploy module. Truly needs it: a regulated client that insists on its own cloud.
6. Monthly price: tooling USD 0; cloud bill under USD 10 on Cloudflare/AWS/GCP at small volume (see rows above), Azure UNVERIFIED. Client can own the licence: yes.
7. Changed since scan 1: scan 1 assumed Kubernetes-style targets; Cloudflare Workers and serverless functions are different targets, so the "five parts" in AK-G16 need to be stated per platform before any client on these clouds is quoted. No verdict change.

## 4. Price and ownership table (small client: about 3,000 inbound messages, 300 approvals per month)

| Service | Monthly price | Label | Client owns licence/account | Last release (SDK or tool) | Licence |
|---|---|---|---|---|---|
| Cloudflare Workers Paid (Queues, Workflows, DO inside included amounts) | USD 5 | VERIFIED-SRC 2026-11-07 | Yes | wrangler 4.158.0 on 2026-11-05 | Proprietary SaaS (UNVERIFIED terms); wrangler MIT OR Apache-2.0 (npm); workerd Apache-2.0 (LICENSE file) |
| Cloudflare Free plan | USD 0 (Queues 24 h retention, 10,000 ops/day; Workflows 3,000 steps/day) | VERIFIED-SRC | Yes | same | same |
| Cloudflare AI Gateway (core) | free; logs follow Workers Logs pricing for gateways created from 2026-09-24 | VERIFIED-SRC | Yes | n/a | Proprietary |
| AWS Step Functions Standard | USD 25 per million transitions; about USD 0 to 1 | VERIFIED feed 2026-11-04 | Yes | client-sfn 3.1164.0 on 2026-11-06 | Proprietary; SDK Apache-2.0 (npm) |
| AWS SQS | USD 0.40 per million (standard), USD 0.50 FIFO | VERIFIED feed 2026-09-11 | Yes | client-sqs 3.1164.0 on 2026-11-06 | same |
| AWS EventBridge | USD 1.00 per million custom events | VERIFIED feed 2026-09-24 | Yes | client-eventbridge 3.1164.0 on 2026-11-06 | same |
| GCP Workflows | USD 0.01 per 1,000 internal steps (5,000 free), USD 0.025 per 1,000 external (2,000 free) | VERIFIED page 2026-11-07 | Yes | google-cloud-workflows 1.24.0 on 2026-10-01 | Proprietary; client Apache-2.0 (PyPI) |
| GCP Cloud Tasks / Pub/Sub | USD 0.40 per million ops after 1 million free / USD 40 per TiB after 10 GiB free | VERIFIED page 2026-11-07 | Yes | n/a | Proprietary |
| Azure Logic Apps Consumption | about USD 0.000025 per built-in action; connectors about USD 0.000125 | UNVERIFIED | Yes | n/a | Proprietary |
| Azure Logic Apps Standard | WS1 USD 175.16 (docs example, example region) | VERIFIED-SRC example only | Yes | n/a | Proprietary |
| Azure Durable Functions + Durable Task Scheduler | compute + scheduler; scheduler dollar rates not read | UNVERIFIED | Yes | extension 1.21.1 on 2026-11-05 (NuGet) | Extension MIT (LICENSE file); scheduler proprietary |

## 5. Corrections to scan 1 found in this pass

1. Scan 1 (partA/E) said Cloudflare AI Gateway DLP can "flag/block/redact". The DLP setup page I read offers only **Flag** and **Block** (VERIFIED-SRC 2026-11-07, `ai-gateway/features/dlp/set-up-dlp.mdx`; a grep for "redact" or "mask" in the DLP and Guardrails pages found nothing). So it cannot mask before the model; it can only refuse. Matters for P5c, not this group.
2. Scan 1: "Cloudflare Queues Free: 24-hour retention" is right but incomplete: Paid is 4 days default, 14 max.
3. Scan 1: Cloudflare spend limits "briefly exceed under concurrency" is confirmed word for word in the docs source ("a burst of concurrent requests can briefly exceed the limit"), beta badge, 20 rules per gateway, 429 on block (VERIFIED-SRC).
4. Scan 1 priced Step Functions only by snippet; now VERIFIED in the AWS Price List feed (USD 0.000025 per transition). The free-tier 4,000 is still a snippet.
5. Scan 1 said GCP callbacks were a gap; filled (idempotent callbacks, IAM permission `workflows.callbacks.send`).

## 6. Rejected candidates (dated reason, 2026-11-07)

- Cloudflare Queues as the ledger: at-least-once, 14 days maximum retention, no dedupe (docs source). Fine as a buffer.
- Cloudflare Workflows instance id as ledger: duplicate id throws only until the retention limit (3, 7 or max 30 days) (docs source).
- `@cloudflare/actors` (npm): latest `0.0.1-beta.6` published 2025-09-15, 13 months stale (npm).
- GCP Cloud Tasks name dedupe: tombstone period reported as 1 h / 4 h / 24 h / 9 days in different Google pages (snippets, conflicting).
- GCP Pub/Sub exactly-once: pull-only, one region, not extended to side effects (Google docs snippet).
- SQS Standard for dedupe: at-least-once.
- Step Functions Express: at-least-once (async) or at-most-once (sync), no callback integration (AWS docs snippet).
- Azure Logic Apps Standard for a small client: hosting plan alone USD 175/month in the docs example; no native Approvals connector (Q&A, 2025 snippet).
- Azure Durable Task Scheduler Dedicated for a small client: HA needs 3 CU (docs); price not read.
- `awskillswitch` (third-party Go tool, SCP freeze): not evaluated beyond a package-page snippet; maintenance unknown.
- No GPL/AGPL/SSPL/BUSL/ELv2/Sustainable-Use item found in this group.

## 7. Sources (read 2026-11-07)

Fetched and read (primary):
- https://raw.githubusercontent.com/cloudflare/cloudflare-docs/production/src/content/partials/workers/queues_pricing.mdx
- .../docs/queues/reference/delivery-guarantees.mdx, .../queues/reference/how-queues-works.mdx, .../queues/platform/pricing.mdx
- .../partials/workflows/workflows-pricing.mdx, .../docs/workflows/reference/pricing.mdx, .../workflows/reference/limits.mdx, .../workflows/build/events-and-parameters.mdx, .../workflows/build/rules-of-workflows.mdx, .../workflows/build/workers-api.mdx
- .../partials/durable-objects/durable-objects-pricing.mdx, .../durable-objects/api/alarms.mdx, .../durable-objects/api/sqlite-storage-api.mdx, .../durable-objects/best-practices/access-durable-objects-storage.mdx, .../workers/authorization/durable-objects.mdx
- .../docs/workers/platform/pricing.mdx, .../changelog/workers/2026-09-15-granular-worker-permissions.mdx
- .../docs/ai-gateway/reference/pricing.mdx, .../ai-gateway/features/spend-limits.mdx, .../ai-gateway/features/dlp/set-up-dlp.mdx, .../ai-gateway/features/guardrails/index.mdx
- https://cloud.google.com/workflows/pricing, https://cloud.google.com/tasks/pricing, https://cloud.google.com/pubsub/pricing
- https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonStates/current/index.json (version 20261104213423), .../AWSQueueService/current/index.json (20260911124607), .../AWSEvents/current/index.json (20260924163903)
- https://raw.githubusercontent.com/MicrosoftDocs/azure-docs/main/articles/logic-apps/logic-apps-pricing.md; .../articles/durable-task/common/durable-task-human-interaction.md, durable-task-external-events.md, durable-task-singletons.md, durable-task-instance-management.md, durable-task-code-constraints.md, durable-task-orchestrations.md; .../articles/durable-task/scheduler/durable-task-scheduler-billing.md
- LICENSE files via raw.githubusercontent.com: cloudflare/workerd, cloudflare/agents, cloudflare/workers-sdk (LICENSE-MIT), cloudflare/workflows-starter, Azure/azure-functions-durable-extension, Azure/azure-functions-durable-js, Azure/azure-functions-durable-python, microsoft/durabletask-dotnet, microsoft/durabletask-python, microsoft/durabletask-go, aws/aws-cdk, awslabs/aws-sam-cli, awslabs/aws-lambda-powertools-python
- Registry JSON: registry.npmjs.org (wrangler, miniflare, agents, @cloudflare/workers-types, @cloudflare/actors, durable-functions, @azure/functions, @aws-sdk/client-sfn, -sqs, -eventbridge, @google-cloud/workflows); pypi.org (azure-functions-durable, durabletask, google-cloud-workflows, boto3, aws-lambda-powertools); api.nuget.org (Worker.Extensions.DurableTask, WebJobs.Extensions.DurableTask)

Search snippets only (page not opened, lower trust): Google Workflows callbacks, quotas and Cloud Tasks / Pub/Sub docs (docs.cloud.google.com); AWS Step Functions "choosing workflow type", service quotas, IAM revoke-sessions docs (docs.aws.amazon.com); SQS FIFO dedupe (AWS SDK reference, oneuptime.com); Azure Logic Apps approvals Q&A (learn.microsoft.com/answers); Cloudflare Agents human-in-the-loop (developers.cloudflare.com); Azure Logic Apps rates (aggregators).

## 8. LEAD-FETCH lines

- LEAD-FETCH: https://developers.cloudflare.com/queues/platform/pricing/ for AK-G2 (confirm the rendered page matches the docs source: USD 0.40/million, 4-day default and 14-day retention)
- LEAD-FETCH: https://developers.cloudflare.com/workflows/reference/pricing/ for AK-G15 (steps USD 0.80 per 100,000; billing start 2026-08-10)
- LEAD-FETCH: https://developers.cloudflare.com/agents/guides/human-in-the-loop for AK-G15 (`waitForApproval` and approval API names)
- LEAD-FETCH: https://aws.amazon.com/step-functions/pricing/ for AK-G15 (free tier 4,000 transitions; how a `.waitForTaskToken` wait is billed)
- LEAD-FETCH: https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html for AK-G2 (exactly-once wording for Standard)
- LEAD-FETCH: https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html for AK-G15 (90-day history, 1-year duration, 25,000 events)
- LEAD-FETCH: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html for AK-G2 (5-minute dedupe window; URL from memory, may need search)
- LEAD-FETCH: https://aws.amazon.com/sqs/pricing/ for AK-G2 (free tier and retention maximum)
- LEAD-FETCH: https://docs.cloud.google.com/workflows/docs/creating-callback-endpoints for AK-G15 (callback idempotency, IAM, slots)
- LEAD-FETCH: https://docs.cloud.google.com/workflows/quotas for AK-G15 (retention 90 days, duration 1 year)
- LEAD-FETCH: https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery for AK-G2 (regional, pull-only limits)
- LEAD-FETCH: https://docs.cloud.google.com/tasks/docs/how-to for AK-G2 (task-name dedupe window)
- LEAD-FETCH: https://azure.microsoft.com/en-us/pricing/details/logic-apps/ for AK-G15 (Consumption per-action and connector rates; Standard plan)
- LEAD-FETCH: https://azure.microsoft.com/en-us/pricing/details/functions/ for AK-G15 (Durable Task Scheduler Dedicated per CU and Consumption per action; Flex Consumption)
- LEAD-FETCH: https://github.com/Azure/azure-functions-durable-extension/releases for AK-G15 (release notes; NuGet date already read)
- LEAD-FETCH: https://github.com/cloudflare/workerd/releases for AK-G16 (release date of the runtime; npm dates already read)

## 9. Closing

Verdict counts for my four modules: ADOPT 1 (AK-G16), WRAP 1 (AK-G15), KEEP-CODE 2 (P2a, AK-G2), DROP 0.

Three findings (under 150 words):
1. Every native service here is at-least-once or has a time-limited dedupe (SQS FIFO 5 minutes, Cloud Tasks hours, Cloudflare Workflows id until retention); only our permanent ledger gives "same key, one effect, forever". A 6-minute/25-hour/31-day replay test proves it.
2. Native waits (Cloudflare `waitForEvent`, GCP callbacks, Step Functions `waitForTaskToken`, Durable Functions events) cover 55-70% of AK-G15 for under USD 5 a month, but none checks the item digest or separates the executor.
3. Scan 1 was wrong that Cloudflare AI Gateway DLP can redact: the setup page offers only flag or block.

---

# PASS 3-2 (full agent file)

# Market scan pass 3, part 2: workflow engines and no-code automation vs AK-G2 / AK-G15 / AK1 pipeline step

Author: research agent, ORDER 122, read 2026-11-07. Research only. No tickets changed. EGM skipped: read-only research (lead runs reviews).

## 0. What I could and could not read (honest)

- Vendor sites (inngest.com, hatchet.run, trigger.dev, temporal.io, docs.temporal.io, kestra.io, prefect.io, dagster.io, zapier.com, make.com, pipedream.com, activepieces.com, n8n.io, dev.to, vercel.app mirrors) did NOT resolve from this machine: WebFetch gave `getaddrinfo ENOTFOUND`, curl gave `CONNECT tunnel failed, response 403`. So EVERY PRICE below is UNVERIFIED (search snippets of vendor pages and third-party aggregators, which disagree with each other).
- What I DID read first-hand on 2026-11-07: LICENSE files from raw.githubusercontent.com (all 10 repos), package metadata from the PyPI JSON API and npm registry JSON (version, upload date, declared licence). GitHub API and releases.atom were refused for unattached repos ("GitHub access to this repository is not enabled"), so "last release" is the latest SDK/package upload, not a GitHub release tag. Server release dates are UNVERIFIED.
- Capability claims (dedupe window, wait tokens, idempotency) come from WebSearch snippets of vendor docs pages, not from a full page read. Marked (S).
- Percent cover figures are MY JUDGEMENT against the ticket needs, not measured. Test ideas given where it matters.

## 1. Needs (one line each, from the tickets)

- AK-G2 (inbound trigger, absorbs P7a ledger): a signed webhook is written to a durable receipt BEFORE the sender hears "accepted"; same sender id plus same body is a no-op; same id with different body is refused and recorded without body; keyed hash of sender id (no raw ids stored); claim/lease, counted tries, infrastructure failures not counted, dead letter, per-source backpressure, run row as commit point, person-triggered reopen with a new run id.
- AK-G15 (durable queue of "needs a person" items): items survive restarts, are listed and reopened by a person, a re-run is a money path.
- AK1 (pipeline step): one `Step` contract, one outbound gate, `run_step` maps errors to `done / needs_person / refused`.

## 2. Summary table

Verdict words are per product, relative to the three modules. "WRAP-later" = a thin adapter is plausible if a client already runs it; not recommended to build now. The modules themselves stay KEEP-CODE for the guarantee part (see section 5).

| Product | Licence (SPDX, source) | Price small client / month (UNVERIFIED) | Cover AK-G2 / G15 / AK1 step | Client can own licence | Verdict |
|---|---|---|---|---|---|
| Temporal (server + Cloud) | MIT, VERIFIED 2026-11-07 raw LICENSE | Cloud: sources conflict ($100 Essentials min vs usage-based $50 per 1M actions from Sept 2026); self-host free + ops | 55 / 60 / 40 | yes (own Cloud account or self-host) | WRAP-later |
| Hatchet | MIT, VERIFIED | Cloud: $180 "Starter" per vendor snippet, aggregators say $10 per 1M runs / Team $500; conflict | 50 / 50 / 35 | yes | WRAP-later |
| Trigger.dev | Apache-2.0, VERIFIED | Free $0 (+$5 credit); Hobby $10; Pro $50 (aggregators agree) | 25 / 45 / 25 | yes | DROP |
| Inngest | SSPL-1.0 server with Apache-2.0 future grant, VERIFIED; npm SDK Apache-2.0 | Hobby $0 (50k executions per vendor snippet); Pro $75 or $99, conflict | 45 / 45 / 30 | server: SSPL trap | DROP |
| Kestra | Apache-2.0, VERIFIED (core); EE features separate | OSS $0; Enterprise quote | 20 / 35 / 15 | yes (OSS) | DROP |
| Prefect | Apache-2.0, VERIFIED | Hobby $0, Starter ~$100, Team ~$400 floor; conflict | 10 / 25 / 10 | yes | DROP |
| Dagster | Apache-2.0, VERIFIED | Solo $10 + $0.04/credit, Starter $100 + $0.035/credit (support article, May 2026) | 5 / 10 / 10 | yes | DROP |
| n8n | Sustainable-Use (not OSI) + `.ee.` Enterprise files, VERIFIED text | Cloud Starter EUR 20 annual / 24 monthly (2,500 exec), Pro EUR 50 annual (10,000); Community self-host $0 | 35 / 40 / 20 | yes if CLIENT runs it for own internal use | ADOPT as forwarder / approval channel only |
| Activepieces | MIT outside `ee` dirs, VERIFIED | Free; Plus $20 or $25; Business $150 (conflict); self-host $0 | 30 / 40 / 15 | yes, MIT | ADOPT as MIT alternative forwarder |
| Zapier | proprietary SaaS | Professional $19.99 annual / $29.99 monthly (750 tasks); Team $69 annual | 15 / 15 / 5 | account only | DROP |
| Make | proprietary SaaS | Core ~$9 annual / $10.59 monthly (10,000 credits) | 15 / 15 / 5 | account only | DROP |
| Pipedream | repo: Pipedream Source Available License (not OSI); platform proprietary | Basic $29, Advanced $49, Connect $99 annual; Oct 2026 snapshot shows $150 Startup; unconfirmed | 25 / 20 / 10 | account only | DROP |

Verdict counts for my 12 items: ADOPT 2 (n8n, Activepieces), WRAP 2 (Temporal, Hatchet, both "later"), KEEP-CODE 0 products (the AK-G2 ledger and AK-G15 queue guarantee stay KEEP-CODE as modules), DROP 8 (Trigger.dev, Inngest, Kestra, Prefect, Dagster, Zapier, Make, Pipedream).

## 3. Per product detail

Columns asked for each item: need covered, cannot guarantee, price, client-owns-licence, last release, changed since scan 1.

### Temporal (open source server, Temporal Cloud)
- Licence: MIT, LICENSE read 2026-11-07 (https://raw.githubusercontent.com/temporalio/temporal/main/LICENSE). Python SDK `temporalio` 1.35.0 uploaded 2026-10-28, MIT (PyPI JSON read 2026-11-07). npm `@temporalio/client` 1.25.0 on 2026-10-27, MIT. Server release date UNVERIFIED here; scan 1 recorded v1.32.2 on 2026-11-02 from the GitHub API.
- Covers: durable execution, workflow-id conflict and reuse policies for dedupe (S: docs.temporal.io Java Nexus walkthrough snippet, read 2026-11-07), signals and signal-with-start for human approval waits (S). It gives retries and a queryable "waiting for a person" workflow list.
- Cover: AK-G2 about 55 (dedupe by workflow id, durable start, retries; NOT webhook signature check, NOT keyed-hash sender id, NOT id-reuse-with-different-body conflict row, NOT per-source backpressure answer before saving, NOT "infrastructure failures do not count" semantics, which would be custom workflow code). AK-G15 about 60. AK1 step about 40 (activities, but our outbound gate and `REASONS` mapping remain ours).
- Cannot guarantee: money exactness; masking before the model; tamper-evident audit (event history is not a signed chain); approver identity separate from executor (you design it); exactly-once side effects (activities are at-least-once; need idempotent calls; search returned nothing confirming this, so the at-least-once point is from my background knowledge, UNVERIFIED).
- Price: Cloud pricing sources conflict. Older: Essentials from $100/month with 1M actions. Newer third-party captures (Sept 2026): $100 minimum replaced by usage $50 per 1M actions plus support add-ons. UNVERIFIED either way. Self-host: $0 plus running Postgres/Cassandra, matching a small client badly.
- Client owns: yes. Lock-in: workflow code written to the SDK.
- Changed since scan 1: possible Cloud price restructure in Sept 2026 (third-party only). Licence unchanged (MIT).
- LEAD-FETCH: https://temporal.io/pricing for AK-G2/AK-G15 backend cost.

### Hatchet
- Licence MIT, LICENSE read 2026-11-07 (https://raw.githubusercontent.com/hatchet-dev/hatchet/main/LICENSE). Python `hatchet-sdk` 1.45.1 on 2026-11-05 MIT; npm `@hatchet-dev/typescript-sdk` 1.46.1 on 2026-11-05 MIT. Actively maintained.
- Covers: Postgres-backed task queue, durable tasks with checkpoints and `waitFor`/`waitForEvent` (S: docs.hatchet.run durable-tasks, read 2026-11-07), run-level idempotency keys with TTL or status-based (S: docs.hatchet.run/v1/idempotency).
- Cover: AK-G2 about 50 (queue and retries yes; the idempotency page describes run-level key dedupe, not "same id different body" conflict, not signature, not receipt-before-ack proof). AK-G15 about 50. AK1 step about 35.
- Cannot guarantee: same list as Temporal. The idempotency TTL is a time window (cannot promise dedupe forever). I found nothing on how retries interact with idempotency keys.
- Price: vendor snippet shows Free $0 and "Starter" $180; aggregators show Developer usage-based ($10 per 1M runs), Team $500. Conflict, UNVERIFIED. Self-host free on Postgres, which fits our existing Postgres-based design.
- Client owns: yes. Changed since scan 1: not in scan 1 (gap), now covered.
- LEAD-FETCH: https://hatchet.run/pricing and https://docs.hatchet.run/v1/idempotency for AK-G2.

### Trigger.dev
- Licence Apache-2.0, LICENSE read 2026-11-07 (raw.githubusercontent.com/triggerdotdev/trigger.dev/main/LICENSE). npm `@trigger.dev/sdk` 4.8.3 on 2026-10-30, MIT declared in npm metadata (differs from the repo LICENSE; the SDK package metadata says MIT, the repo file is Apache-2.0: treat as both permissive, UNVERIFIED which governs which part).
- Covers: waitpoint tokens `wait.createToken` / `wait.forToken` / `wait.completeToken` with `idempotencyKey` and TTL; completion by a callback URL that needs no API key (S: trigger.dev/docs/wait-for-token, read 2026-11-07). Good fit for a human-approval email.
- Cover: AK-G2 about 25 (task triggering with idempotency keys, no signed ingress or ledger). AK-G15 about 45. AK1 step about 25.
- Cannot guarantee: approver identity (a bearer callback URL is not a separate identity; whoever holds the URL completes it); all items in the common list.
- Price (aggregators agree, UNVERIFIED): Free $0 with $5 credit, Hobby $10, Pro $50, usage on top.
- Client owns: yes. Hosted runtime is the product; self-host is heavy. Changed since scan 1: not covered before.
- LEAD-FETCH: https://trigger.dev/pricing.

### Inngest
- Licence: server repo LICENSE.md is Server Side Public License v1 with an "Apache 2.0 Future License" grant (file lines 1-2 and "Grant of Future License", effective on the third anniversary of the release, read 2026-11-07). FLAG: SSPL. npm `inngest` SDK 4.26.2 on 2026-10-29, Apache-2.0. PyPI `inngest` 0.5.20 on 2026-11-02, no licence field.
- Covers: event-id dedupe for 24 hours (a duplicate is stored but starts no run), function-level CEL idempotency for 24 hours, durable steps (S: inngest.com/docs idempotency and send-events pages, read 2026-11-07). The docs themselves warn that dedupe does not stop a retried step from repeating a payment or email call.
- Cover: AK-G2 about 45. The 24-hour window is the gap: a duplicate arriving on day 2 is a new event, whereas the ledger needs a permanent key. No signed ingress, no id-reuse-conflict row. AK-G15 about 45 (waitForEvent; I could not confirm timeout behaviour). AK1 step about 30.
- Cannot guarantee: permanent no-double-apply; money; masking; tamper-evident audit; approver identity.
- Price (UNVERIFIED): Hobby $0 with 50k executions (one aggregator says 100k); Pro $75 (freetier.co) or $99 (toolradar/projects.dev). Hobby pauses execution at quota.
- Client owns: SDK yes; self-hosting the server under SSPL is a trap for an agency that resells a hosted service. Changed since scan 1: SSPL now confirmed by LICENSE file with the Apache future grant (scan 1 said "SSPL" only).
- LEAD-FETCH: https://www.inngest.com/pricing.

### Kestra
- Licence Apache-2.0 for the open core, LICENSE (develop branch) read 2026-11-07. PyPI `kestra` 2.0.0 on 2026-09-07 is probably the Python client, not the server; server release date UNVERIFIED. Audit logs, RBAC, SSO, multi-tenancy are Enterprise (S: kestra.io pricing snippet).
- Covers: YAML flows with webhook triggers, retries, a Pause task. Sources conflict on whether human-approval Pause is OSS or Enterprise (S: toolradar says OSS, getapp says Enterprise).
- Cover: AK-G2 about 20, AK-G15 about 35, AK1 about 15. It is a JVM data/orchestration platform with its own repository DB; heavy for a small client and a different programming model from Python modules.
- Price: OSS $0; Enterprise quote-only (UNVERIFIED). Client owns: OSS yes. Changed since scan 1: not covered before.
- LEAD-FETCH: https://kestra.io/pricing and Kestra docs Pause task page for AK-G15.

### Prefect
- Licence Apache-2.0 (LICENSE read 2026-11-07). PyPI `prefect` 3.9.2 on 2026-11-06, Apache-2.0. Actively maintained.
- Covers: Python flows, retries, pause/suspend flow runs awaiting input (my knowledge; the search returned nothing on pause, UNVERIFIED). Built for scheduled and data pipelines, not inbound-message ledgers.
- Cover: AK-G2 about 10, AK-G15 about 25, AK1 about 10.
- Price (UNVERIFIED, conflicting): Hobby free; Starter ~$100; Team ~$100 per user with 4-user minimum ($400); packaging changes logged in March, April and August 2026 by pricingsaas.com. Client owns: yes. Changed since scan 1: not covered before; plan tables changed repeatedly in 2026.
- LEAD-FETCH: https://www.prefect.io/pricing.

### Dagster
- Licence Apache-2.0 (LICENSE read 2026-11-07). PyPI `dagster` 1.13.29 on 2026-11-05. Asset/data-pipeline orchestrator; no inbound-queue or approval model. Cover 5 / 10 / 10.
- Price: Dagster+ Solo $10 + $0.040 per credit, Starter $100 + $0.035 per credit, pure pay-as-you-go from 2026-05-01 per Dagster's own support article (snippet, read 2026-11-07; UNVERIFIED because not fully fetched). Older aggregator pages still show included credits.
- Changed since scan 1: not covered before; pricing model changed May 2026.
- LEAD-FETCH: https://dagster.io/pricing.

### n8n (cloud and self-host)
- Licence: Sustainable Use License v1.0 plus separate Enterprise licence for files with `.ee.` in name or `.ee` dirs (LICENSE.md read 2026-11-07, https://raw.githubusercontent.com/n8n-io/n8n/master/LICENSE.md). FLAG: not OSI. Text: "use or modify the software only for your own internal business purposes or for non-commercial or personal use"; distribution only free of charge for non-commercial purposes. Consequence for an agency: running n8n inside the CLIENT's own account/infra for the client's own business is within the licence; hosting one n8n for several clients and charging them is not (my reading of the text, not legal advice). npm `n8n` 2.46.6 on 2026-11-04, "SEE LICENSE IN LICENSE.md".
- Covers: webhook trigger, Wait node and human-in-the-loop approval, retry on fail, error workflows, Slack/email messaging. Duplicates: community and vendor-adjacent sources say you must build dedupe yourself (Remove Duplicates node compares executions; concurrency behaviour undocumented; keys from `$now` or `$execution.id` defeat dedupe; queue mode can duplicate at job boundaries) (S: community.n8n.io and webhookrelay.com snippets, read 2026-11-07).
- Cover: AK-G2 about 35 (webhook yes; HMAC check only via custom code; no receipt-before-ack guarantee, no commit-point semantics). AK-G15 about 40 (Wait node holds executions; no reopen with new run id, no money-safe re-run). AK1 step about 20.
- Cannot guarantee: no lost/double-applied message, money, masking before model, tamper-evident audit (execution history is editable by the admin), approver identity separate from executor.
- Price (UNVERIFIED): Starter EUR 20/month annual or EUR 24 monthly for 2,500 executions (a July 2026 re-check cited by an aggregator); Pro EUR 50 annual / ~EUR 60 monthly for 10,000; Business ~EUR 667 for 40,000 and self-host only; Community self-host $0. Over-limit runs are not queued on Starter/Pro per one aggregator. Client owns: yes (client's own account).
- Changed since scan 1: scan 1 left the licence "assumed"; now VERIFIED from LICENSE.md. Price figures unchanged. Latest package 2.46.6 on 2026-11-04.
- LEAD-FETCH: https://n8n.io/pricing and https://docs.n8n.io/hosting/community-edition-features/ for which features are Enterprise-only.

### Activepieces
- Licence: MIT outside `packages/ee/` and `packages/server/api/src/app/ee`, which are commercial (LICENSE read 2026-11-07, raw.githubusercontent.com/activepieces/activepieces/main/LICENSE). FLAG: ee directories. npm `@activepieces/shared` 0.96.2 on 2026-06-21 (not the server; stale as a signal, UNVERIFIED maintenance of the server).
- Covers: webhook trigger, flows that pause for approval and resume after approve/reject by email or Slack (S: syncgtm/automationatlas snippets). Which tier carries approvals is unconfirmed.
- Cover: AK-G2 about 30, AK-G15 about 40, AK1 about 15. Cannot guarantee: the same list as n8n.
- Price (UNVERIFIED, conflicting): Free; Plus $20 (October 2026 blog snippet) or $25; Business $150; the model reportedly moved from tasks to active flows in 2026. Self-host free. Client owns: yes, and MIT lets an agency resell. Changed since scan 1: not covered before.
- LEAD-FETCH: https://www.activepieces.com/pricing.

### Zapier
- Proprietary SaaS. Professional $19.99 annual or $29.99 monthly for 750 tasks; Team $69 annual or $103.50 monthly (2,000 base tasks) (UNVERIFIED, third-party). Task counting includes AI, code and SDK steps (changed 2026-06-15 per one source).
- Duplicates: Zapier "can't prevent triggers the app itself sends"; guard inside the Zap with filters or stored ids; a "never replay" thread reports failed webhooks resent anyway (community.zapier.com snippets, read 2026-11-07, unconfirmed).
- Cover: 15 / 15 / 5. Cannot guarantee anything on the list. Client owns the account only; no code control.
- Changed since scan 1: AI pricing model change 2026-06-15 (secondary). LEAD-FETCH: https://zapier.com/pricing.

### Make
- Proprietary SaaS. Free 1,000 credits; Core ~$9 annual / $10.59 monthly, Pro ~$16 / $18.82, Teams ~$29 / $34.12, all 10,000 credits (September 2026 pages quoting Make's page; UNVERIFIED because not fetched). Incomplete executions and replay: found no source (gap).
- Cover: 15 / 15 / 5. Cannot guarantee the list. Client owns account only.
- Changed since scan 1: not covered before. LEAD-FETCH: https://www.make.com/en/pricing.

### Pipedream
- Repo licence: "Pipedream Source Available License Version 1.0" (LICENSE read 2026-11-07, raw.githubusercontent.com/PipedreamHQ/pipedream/master/LICENSE). FLAG: source-available, not OSI; it covers the component repo, the platform itself is proprietary SaaS. Workday agreed to acquire Pipedream (announced about Nov-Dec 2025, third-party, UNVERIFIED close). A 2026-10-04 snapshot (usagepricing.com) reports a $150 "Startup" plan replacing tiers; unconfirmed. Earlier: Free, Basic $29, Advanced $49, Connect $99 annual.
- Cover: 25 / 20 / 10 (code steps, webhook trigger, workflow retries and approval via `$.flow.suspend`, my knowledge, UNVERIFIED). Ownership/pricing risk after acquisition. Client owns account only.
- Changed since scan 1: Workday acquisition and October 2026 pricing change (secondary). LEAD-FETCH: https://pipedream.com/pricing.

## 4. Queries run (WebSearch, all 2026-11-07)

Engines group (11): Inngest pricing; Temporal Cloud pricing; Hatchet pricing; Trigger.dev pricing + wait token; Kestra pricing + Pause; Prefect pricing + pause_flow_run; Dagster+ pricing; Inngest idempotency + waitForEvent; Trigger.dev wait.createToken idempotency; Hatchet durable waitFor idempotency; Temporal workflow ID reuse + signal approval.
No-code group (7): n8n cloud pricing; Zapier pricing; Make pricing; Pipedream pricing + Workday; Activepieces pricing + approval; n8n webhook duplicate / Wait node; Zapier/Pipedream/Make duplicate delivery and replay.
First-hand reads: 10 raw LICENSE files; PyPI JSON for 6 packages; npm JSON for 6 packages.

Rejected candidates (dated 2026-11-07):
- Prefect, Dagster: data/scheduled-pipeline orchestrators with no inbound-ledger or approval model; cover under 25 percent.
- Kestra: JVM platform; approval feature edition unclear; Enterprise features (audit, RBAC, multi-tenancy) are quote-priced.
- Inngest self-hosted server: SSPL; 24-hour dedupe window is shorter than a ledger needs.
- Zapier, Make: no durable receipt, no way to prove no lost message, no licence the client can host.
- Pipedream: ownership change and unconfirmed plan restructure in October 2026.
- Trigger.dev: bearer-URL approvals, hosted-runtime model, weak ingress fit.

Not searched in this pass (gaps, say so): Restate, DBOS, Windmill, Svix, Hookdeck, Convoy, pg-boss, Graphile Worker, Procrastinate, Camunda, AWS Step Functions and Cloudflare Queues/Workflows (scan 1 touched Step Functions). A Postgres queue library (pg-boss/Graphile/Procrastinate) is the most likely cheap ADOPT/WRAP for the claim/lease/retry part of AK-G2 and deserves a pass.

## 5. Module-level verdicts and test ideas

- AK-G2 inbound ledger: KEEP-CODE for the guarantee "no lost, no double-applied message": the receipt is committed before the ack, keyed-hash dedupe is permanent, id reuse with a different body is refused and recorded, the run row is the commit point. Best off-the-shelf cover is about 55 (Temporal), under the 80 percent bar. Test idea: send the same signed body 50 times concurrently while killing the process mid-write; assert one receipt, one run, one ack per delivery; send same id with a changed body; assert conflict and no stored body. Optional WRAP-later: use Temporal or Hatchet as the worker back end behind the store interface for a client that already runs one.
- AK-G15 needs-a-person queue: KEEP-CODE for the reopen-with-new-generation money path; the waiting UI/channel can be ADOPT (n8n, Activepieces, Trigger.dev tokens). Test idea: reopen twice in a race; assert one new run id and one spend.
- AK1 step contract: KEEP-CODE; none of the products provides our `REASONS` mapping or outbound gate.

## 6. Which first-client small-budget offers need our modules

With n8n (or Activepieces) + Close + Claude alone you can sell: lead capture to Close, reply drafting, draft-and-approve with a Wait/approval node, a Meta CAPI relay; cost roughly EUR 20-50/month for n8n Cloud on the client's own account. Duplicate sends are possible if the sender retries and the client does not build dedupe. You need our AK-G2/AK-G15 only when the offer promises "no message lost or applied twice" in writing, unattended actions that spend money or message customers, or an audit a client can show.

## 7. SOURCES (all read 2026-11-07)

First-hand: raw.githubusercontent.com LICENSE files: inngest/inngest/main/LICENSE.md; hatchet-dev/hatchet/main/LICENSE; triggerdotdev/trigger.dev/main/LICENSE; temporalio/temporal/main/LICENSE; kestra-io/kestra/develop/LICENSE; PrefectHQ/prefect/main/LICENSE; dagster-io/dagster/master/LICENSE; n8n-io/n8n/master/LICENSE.md; activepieces/activepieces/main/LICENSE; PipedreamHQ/pipedream/master/LICENSE. https://pypi.org/pypi/{prefect,dagster,hatchet-sdk,inngest,temporalio,kestra}/json. https://registry.npmjs.org/{inngest,@trigger.dev/sdk,n8n,@hatchet-dev/typescript-sdk,@temporalio/client,@activepieces/shared}.
Search snippets (S): inngest.com/docs idempotency and send-events; docs.hatchet.run/v1/idempotency, /v1/durable-tasks; trigger.dev/docs/wait-for-token; docs.temporal.io Java Nexus send-messages; support.dagster.io pricing update May 2026; automationatlas.io, toolradar.com, costbench.com, freetier.co, jetadmin.io, latenode.com, usagepricing.com, pricingsaas.com, activepieces.com/blog, community.n8n.io, webhookrelay.com, community.zapier.com. These are secondary except where marked vendor.

## 8. LEAD-FETCH lines

- LEAD-FETCH: https://www.inngest.com/pricing for AK-G2 backend cost
- LEAD-FETCH: https://hatchet.run/pricing for AK-G2/AK-G15 backend cost
- LEAD-FETCH: https://docs.hatchet.run/v1/idempotency for AK-G2 dedupe semantics
- LEAD-FETCH: https://trigger.dev/pricing for AK-G15 approval channel cost
- LEAD-FETCH: https://temporal.io/pricing for AK-G2/AK-G15 backend cost
- LEAD-FETCH: https://kestra.io/pricing for AK-G15 (Pause task edition)
- LEAD-FETCH: https://www.prefect.io/pricing for AK-G15
- LEAD-FETCH: https://dagster.io/pricing for AK1 pipeline step
- LEAD-FETCH: https://zapier.com/pricing for n8n comparison
- LEAD-FETCH: https://www.make.com/en/pricing for n8n comparison
- LEAD-FETCH: https://pipedream.com/pricing for n8n comparison
- LEAD-FETCH: https://www.activepieces.com/pricing for n8n comparison
- LEAD-FETCH: https://n8n.io/pricing for AK-G2/AK-G15 forwarder and approval channel cost
- LEAD-FETCH: https://docs.n8n.io/hosting/community-edition-features/ for AK-G15 (Enterprise-only features)

## 9. Three findings (under 150 words)

1. No product in the set reaches 80 percent of AK-G2 or AK-G15; best is about 55 (Temporal), and the gap is exactly the ledger guarantees.
2. Licences: Inngest server is SSPL (with an Apache future grant), n8n and Pipedream are not OSI; Activepieces (MIT outside ee) is the only no-code tool an agency may legally resell.
3. All prices unverified: every vendor site is blocked here, and aggregators conflict (Temporal, Hatchet, Pipedream, Activepieces look like they changed in Sept-Oct 2026).

---

# PASS 3-3 (full agent file)

# Market scan pass 3, part 3: portal builders and LLM tracing/audit (read 2026-11-07)

Scope: Port, Retool, Appsmith, Budibase (approvals UI, client portals, audit views) and Langfuse, Helicone, OpenTelemetry plus managed OTel backends (tracing/audit of model calls). Our modules: AK-G15 approvals queue/portal, AK-G1 hand-off, P5a-P5b5 diagnostics/audit, evals gates. Extends and corrects `reviews/market-scan-1.md`. No ticket changes.

## Network reality, stated first
- Reachable from this machine: raw.githubusercontent.com (LICENSE, README), github.com `releases.atom`, pypi.org. WebSearch works.
- NOT reachable (DNS ENOTFOUND, host not on the session allowlist): langfuse.com, retool.com, appsmith.com, budibase.com, port.io, helicone.ai. So NO vendor price page was read. Every price below is UNVERIFIED (secondary: blogs/aggregators via search snippets, dated 2026-11-07). Licences and release dates marked VERIFIED were read from GitHub/PyPI.

## Summary table

| Module | Need | Candidates (this pass) | Cover % | Verdict |
|---|---|---|---|---|
| AK-G15 approvals queue | Durable "needs a person" queue, tenant isolation, approver is a different DB role from the agent, re-run is a paid second run | Port manual approval; Retool Workflows user tasks + Business portals; Appsmith/Budibase as UI only | UI/approval inbox 60-75; the guarantee parts 5-15 | KEEP-CODE (store, roles, rerun); WRAP optional for the UI |
| AK-G1 hand-off | Agent stops, person takes over, one lease per conversation, no double answer | Same builders; none own a conversation lease | 10-20 | KEEP-CODE |
| P5a closed error codes | Error records only of fixed words | OTel `error.type` vocabulary; Langfuse/Helicone store whatever you send | 30 (unchanged) | KEEP-CODE |
| P5b1 provider error plumbing | Provider errors to closed codes + retry | OTel GenAI `error.type`; Langfuse/Helicone record, do not classify | 55-65 | WRAP (unchanged) |
| P5b2 config-error table + CI | CI test | not in this pass | 85-90 (scan 1) | ADOPT (unchanged) |
| P5b3 rewire writers | Every writer prints a diagnostic | none (edits to our call sites) | 15-25 | KEEP-CODE |
| P5b4 output guard | Nothing raw reaches logs/stderr | OTel Collector redaction processor; Langfuse mask fn; Helicone none seen | 40-50 (denylist) | KEEP-CODE |
| P5b5 pin no old path | Pin tests | not in this pass | 85 (scan 1) | ADOPT (unchanged) |
| Evals gates | Block release if eval fails | Langfuse datasets/experiments, scores | UNVERIFIED, about 50 for scoring; the gate stays ours | WRAP (provisional) |

Verdict counts for my items (9 rows): ADOPT 2 (P5b2, P5b5, carried from scan 1, not re-examined), WRAP 2 (P5b1, evals gates), KEEP-CODE 5 (AK-G15, AK-G1, P5a, P5b3, P5b4), DROP 0.

## Queries run (16 searches, plus about 25 fetches)
Portal group (7): (1) Retool pricing 2026 plans/external users/audit logs; (2) Appsmith pricing 2026 Business audit logs; (3) Budibase pricing 2026 audit logs GPL; (4) Port pricing/self-service/manual approval; (5) Port manual approval approvers docs; (6) Retool Workflows human approval / external users / audit export; (7) Windmill approval steps, licence, price. Tracing group (8): (8) Langfuse pricing 2026 tiers; (9) Helicone maintenance mode/Mintlify; (10) Grafana Cloud free tier traces; (11) Honeycomb pricing; (12) OTel GenAI semantic conventions status; (13) SigNoz/Uptrace pricing; (14) Phoenix licence; (15) Langfuse audit logs/licence key/masking; (16) tamper-evident LLM audit hash chain OTel.
Rejected or not pursued (dated 2026-11-07):
- Arize Phoenix: reported Elastic License 2.0 (secondary, UNVERIFIED); source-available, not a client-ownable open licence. Rejected as a base; OpenInference (reported Apache-2.0) is only an instrumentation vocabulary.
- Windmill: approval steps exist (suspend step, per-approver resume URLs, approval count, timeout; docs mirror read, not official). Approval form and disabling self-approval are reported as Cloud/Enterprise only. Licence and price not found. Not rejected on merit, just not verified; candidate for a later pass.
- Uptrace: a comparison table marks it weak for LLM-specific views (competitor-written). Rejected.
- Hash-chain add-ons (bijotel, ai-audit-trail, llm-audit-log, auditant, ttt-otel): tiny, unvetted, vendor claims; ttt-otel needs a hosted chain service. Not adopted; they show the pattern exists, not that it is safe to depend on.
- Superblocks, ToolJet, UI Bakery, Jet Admin: appear only as competitor-blog authors; not searched.

## Per-item detail

Columns used per item: licence (SPDX), last release, price for a small client, can client own the licence, changed since scan 1.

### Langfuse
- Licence: MIT for everything outside `ee/`, `web/src/ee/`, `worker/src/ee/`, `packages/shared/src/server/ee/`; those use a separate Langfuse Enterprise licence. Copyright ClickHouse, Inc. 2023-2026. VERIFIED 2026-11-07 https://raw.githubusercontent.com/langfuse/langfuse/main/LICENSE and /ee/LICENSE. The ee text says a valid Enterprise licence and an agreement with Langfuse GmbH or ClickHouse are required; dev/test use is allowed. SPDX for PyPI SDK `langfuse` 5.2.0: MIT, VERIFIED https://pypi.org/pypi/langfuse/json 2026-11-07.
- Last release: v4.76.0, 2026-11-05 (previous v4.75.0, 2026-11-04). VERIFIED https://github.com/langfuse/langfuse/releases.atom 2026-11-07. Actively maintained.
- Gated to Enterprise licence key (secondary search result citing langfuse.com docs, UNVERIFIED): audit logs, server-side data masking, project RBAC, data retention policies, SCIM. Removing the key removes the audit viewer and read API.
- Price, UNVERIFIED (blogs, 2026): Cloud Hobby free (50k units, 30 days, 2 users); Core $29/mo (100k units, overage $8 per 100k); Pro $199/mo (3-year retention); Teams add-on $300 or $499 (sources conflict); Enterprise $2,499/mo with audit logs. Self-host MIT core is free plus your own Postgres/ClickHouse/Redis/S3 hosting.
- Client can own: yes for MIT core (self-host or own cloud account). Audit logs need a paid licence.
- Covers: trace storage of model calls, cost, scores, datasets/experiments. Cover for our P5 audit: 30-40 (it records what you send; a client-side `mask` function exists, scan 1).
- Cannot guarantee: tamper-evident audit (no evidence of hash chaining or write-once in anything I read; the search found none, UNVERIFIED), money exactness, approvals with separate executor, tenant isolation of OUR queue, masking before the model (mask runs on data sent to Langfuse, not on what the model saw), no lost/double message. Eval gates: it scores and compares; blocking a release is CI glue.
- Changed since scan 1: licence/release now VERIFIED from primary files (scan 1 had README only). Audit logs paid-only is new emphasis. Otherwise no change.

### Helicone
- Licence: Apache-2.0, copyright Helicone Inc 2023. VERIFIED 2026-11-07 https://raw.githubusercontent.com/Helicone/helicone/main/LICENSE and README.
- Last release tag seen: deploy-20261010-025755, 2026-10-10 (earlier 2026-09-16, 2026-09-13). VERIFIED https://github.com/Helicone/helicone/releases.atom 2026-11-07. These are deploy tags, not versioned releases; the tagging is continuing.
- Maintenance mode: the README I read has NO maintenance notice. A search result says Mintlify acquired Helicone in March 2026 and Mintlify's announcement says it will run in maintenance mode (security, bug fixes, new models), and will help customers migrate (secondary snippet of the mintlify.com blog via dealroom, UNVERIFIED). Treat as: not a base for a new client product.
- Price: README says free tier 10k requests/month (VERIFIED README); paid prices not found, UNVERIFIED. Self-host via docker-compose (Web, Worker, Jawn, Supabase, ClickHouse, Minio); Helm chart only via enterprise contact (README). That is a heavy stack for a small client.
- Client can own: yes (Apache-2.0 self-host).
- Covers: gateway-style request logging, cost, sessions. Cover for P5/audit: 25-35. Same gaps as Langfuse.
- Changed since scan 1: README now read directly; the maintenance-mode claim is still from secondary text; no maintenance wording in the repo README. Verdict stays: do not build on it.

### OpenTelemetry (spec, SDK, Collector)
- Licence: Collector Apache-2.0 VERIFIED https://raw.githubusercontent.com/open-telemetry/opentelemetry-collector/main/LICENSE 2026-11-07. Other repos Apache-2.0: UNVERIFIED (not fetched).
- Last releases (VERIFIED, releases.atom, 2026-11-07): Collector releases v0.165.0 on 2026-11-07; Python SDK 1.45.2/0.66b2 on 2026-10-29; specification 1.62.0 on 2026-10-22.
- GenAI conventions: status Development; prompt/response content is Opt-In (secondary, search of opentelemetry.io snippet, UNVERIFIED). One guide says they moved to a dedicated repo on 2026-06-12 (single-source, UNVERIFIED). So attribute names may still change; a pin on exact names is needed.
- Price: software free. Cover for P5b4 redaction: Collector redaction processor is a denylist/regex (scan 1), 40-50.
- Cannot guarantee: allowlist default-deny, tamper-evident audit (no standard exists; the search found no official OTel standard), masking before the model, anything about approvals/tenants.
- Client can own: yes.
- Changed since scan 1: versions now VERIFIED; GenAI status re-confirmed as Development.

### Managed OTel backends (price for a small client, all UNVERIFIED secondary 2026-11-07)
| Backend | What | Price evidence | Note |
|---|---|---|---|
| Grafana Cloud | Tempo traces, OTLP | Free: 50 GB traces/mo, 14-day retention, 3 users; Pro base about $19/mo + usage (rates conflict $0.40-0.50/GB) | Free tier likely enough for one small client |
| Honeycomb | Events/traces | Free 20M events/mo, 60-day retention; Pro price changed 2026-07-01 (docs.honeycomb.io page lists $3.00 per million events; entry prices conflict) | Retention 60 days is too short for audit by itself |
| SigNoz Cloud | OTel-native, LLM views | traces about $0.30/GB, 15-day default retention; plans $19-49/mo (conflict) | Open source core; licence not checked |
LEAD-FETCH lines below for each pricing page. None provides tamper-evident or write-once retention as a documented feature that I read; retention of 14-60 days is below any audit need.

### Port
- Not open source (SaaS developer portal). Licence: proprietary vendor terms, UNVERIFIED; client cannot own the licence beyond a subscription.
- Approvals: docs describe "Enforce manual approval", approvers by user or team, all-or-one rule, run state WAITING_FOR_APPROVAL, email notification, auto-approve by automation (docs.port.io snippets via search, 2026-11-07, UNVERIFIED as primary). Roadmap items show gaps: conditional approval, admin override, bypass if submitter is approver are feature requests (so the approver/requester rules are not fully configurable, UNVERIFIED).
- Price: free plan exists (10,000 catalog entities footnote). Free-plan limits conflict: one listing says 3 self-service actions and 30 days audit retention, another 15 seats; paid $19-40/seat/mo (conflict). All UNVERIFIED.
- Fit: built for engineering teams (catalog, actions on infrastructure). Wrong shape for an end customer's inbox of "needs a person" messages. Cover for AK-G15 about 40 for the approve/reject step only.
- Cannot guarantee: tenant isolation of our data (their tenancy is the org), separate executor DB identity, durable queue tied to inbound messages, paid re-run exactness.
- Changed since scan 1: scan 1 did not cover Port at all.

### Retool
- Not open source; self-hosting is an Enterprise feature (secondary). Licence proprietary, UNVERIFIED.
- Plans (secondary, 2026, UNVERIFIED): Free up to 5 users, no external users, audit logs or SSO. Team $10/builder and $5/internal user per month annual ($12/$7 monthly), no audit logs. Business: audit logs, portals, external users (first 50 free, then $8/$6/$4 per external user annual); builders $50 annual ($65 monthly), internal users $15 ($18 monthly). Enterprise custom: SAML/OIDC, Git, self-host. A source gives $46 for Business, a mismatch.
- A 3-builder-plus-clients setup is then roughly 3 x $50 = $150/mo for Business before external users (UNVERIFIED arithmetic on secondary prices).
- Approvals: Workflows "user tasks" pause a run until a person submits a form in a Retool app; the post I found is an early-access announcement (community.retool.com, date not confirmed), so GA and external-user assignment are UNVERIFIED. Audit log: admin-only, UI about 3 months, CSV export about 1 year (a tutorial, UNVERIFIED).
- Cover for AK-G15 portal UI: 60-75. Can client own: pay for their own subscription; no source ownership.
- Cannot guarantee: the same list as Port. Also audit log is vendor-kept, not tamper-evident (nothing I read says it is).
- Changed since scan 1: new (not covered).

### Appsmith
- Licence: Apache-2.0. The LICENSE file read is Apache-2.0, copyright Appsmith Inc 2021 (VERIFIED https://raw.githubusercontent.com/appsmithorg/appsmith/release/LICENSE 2026-11-07); README says Apache-2.0. The repo has an `ee` folder under `app/client/src/ee` with no licence note visible there, so which code is commercial is UNVERIFIED. Search results say audit logs need a paid Business/Enterprise licence even when self-hosted (UNVERIFIED).
- Last release: v2.6.0, 2026-10-28 (v2.5.1 2026-10-21, v2.5.0 2026-10-09). VERIFIED https://github.com/appsmithorg/appsmith/releases.atom 2026-11-07. Active.
- Price (UNVERIFIED): Business $15/user/mo up to 99 users with audit logs and custom roles; Enterprise about $2,500/mo for 100 users; community self-host free.
- Fit: you build the approvals UI yourself on top of an API/DB. Good as the screen for AK-G15; it does not give the queue state machine. Cover about 50 for the UI, 5-10 for guarantees.
- Client can own: yes (Apache-2.0 community edition self-host; own the Business subscription for logs).
- Changed since scan 1: new.

### Budibase
- Licence: root LICENSE says GPLv3 is the default; paid features under BSL in `/packages/pro`; packages shipped inside generated apps under MPL-2.0; Structured Query Server under its own licence. VERIFIED https://raw.githubusercontent.com/Budibase/budibase/master/LICENSE 2026-11-07 (read as a summary). Flag: GPLv3 and BSL. The BSL file URL I tried returned 404, so BSL change date and use grant are UNVERIFIED. A search snippet also says AGPL for the builder; that conflicts with the file I read, so I trust the file and mark the snippet unreliable.
- Last release: v3.51.0-cloud.15, 2026-11-05 (cloud tag series). VERIFIED https://github.com/Budibase/budibase/releases.atom 2026-11-07. These are cloud deploy tags, so a stable self-host version number is not established.
- Price (UNVERIFIED): Premium about $50/creator and $5/app user annual ($60/$6 monthly); cloud free tier reportedly discontinued March 2026 (single source); audit logs reported Enterprise only; self-host free under GPLv3 with a possible 20-user or single-workspace limit (sources conflict).
- Fit: same as Appsmith, with a GPL flag for anything we would embed or modify. Cover about 45 for the UI; weaker audit story.
- Client can own: yes for self-host GPLv3, but copyleft applies if we modify and distribute.
- Changed since scan 1: new.

## Per-module notes for our items

### AK-G15 approvals queue (REVISION 3 FROZEN, build notes win; read first lines of the ticket)
1. Need: a durable queue of "needs a person" items; two DB roles (agent cannot start a paid re-run itself, R1-RES-1 in the ticket); no message text stored; erasure wins; tenant isolation; a per-tenant ceiling.
2. Candidates: Port and Retool Workflows for the approve/reject UI; Appsmith/Budibase as the screen; Windmill suspend steps for a flow-level approval (not verified).
3. None of them stores our queue items in our database under our two roles. They would hold an approval record in the vendor's database, which is a second copy of the item and breaks "item never holds message text" unless we pass only ids.
4. Cannot guarantee: approvals with a separate executor identity (the vendor's approver is a vendor user, not a DB role), tenant isolation, paid re-run exactly once, no lost/double-applied message.
5. Verdict: KEEP-CODE for the queue and the re-run transaction. Test idea: with the agent role, try UPDATE to `rerun` on a queue item; Postgres must refuse. If an owner wants a nicer screen, WRAP: Appsmith (Apache-2.0) or Retool reads the queue through a read-only role. This is the ~70 percent of the need that is only a screen, and it is not part of the ticket's guarantee.
6. First-client offers: with n8n + Close + Claude, a "send to a person" step can be an n8n Wait node or a Close task (scan 1). That is enough when no second paid run, no tenant separation and no separate executor are promised. The queue module is needed only when those are promised.

### AK-G1 hand-off
1. Need: the agent stops, a person takes over, conversation lease so two messages are not answered at once, fixed reply, item into the AK-G15 queue.
2. Candidates: the portal builders have no conversation lease; Close/n8n can assign a lead to a person.
3. Cover 10-20.
4. Cannot guarantee: no double-answered message (lease tied to a run heartbeat).
5. Verdict: KEEP-CODE. Test idea: two concurrent inbound messages on one conversation, kill the first run mid-exchange; the second must wait until the lease is dead, then run once.
6. Offers: "assign lead to human and stop the bot" is a CRM flag in Close/n8n; the lease is only needed for volume.

### P5a to P5b5 (diagnostics and audit trail)
- Langfuse, Helicone and OTel are places to PUT records. None of them makes the record safe. P5a/P5b3/P5b4 guarantee that the record contains only closed words and that nothing raw reaches logs; these tools store what we send (Langfuse server masking is paid; client `mask` only covers data sent to it).
- A real new point: for tamper-evident audit, none of Langfuse, Helicone, OTel or the managed backends advertises write-once or hash-chained storage in anything I read. Small PyPI hash-chain packages exist but are unvetted. So the audit-trail guarantee remains ours or needs S3 Object Lock / immudb (scan 1).
- Offers: a client wanting "see what the bot did" is served by Langfuse Hobby/Core or Grafana free with a redaction step; a client wanting proof that nothing leaked or was altered needs P5a-P5b4 plus an immutable store.

### Evals gates
- No ticket was named in my list; I did not read one. Langfuse has datasets, experiments and scores (README level, UNVERIFIED depth). The pass/fail gate in CI is glue we write. Provisional WRAP; no price beyond Langfuse tiers. Not verified in depth. A later pass should read the evals gate ticket and Langfuse's experiments docs.

## Findings (under 150 words)
1. No primary vendor price page was reachable (langfuse, retool, appsmith, budibase, port, helicone all fail DNS). Every price here is UNVERIFIED; licences and release dates for 6 projects are VERIFIED from GitHub/PyPI.
2. Audit logs are paid on every product: Langfuse needs an Enterprise key ($2,499/mo reported), Retool Business, Appsmith Business, Budibase Enterprise. None shows tamper-evidence. Audit stays our guarantee or an immutable store.
3. Appsmith (Apache-2.0, release 2026-10-28) is the only portal builder a client can fully own; Budibase is GPLv3/BSL. Helicone has no maintenance notice in its README, only a secondary claim.

## LEAD-FETCH lines
- LEAD-FETCH: https://langfuse.com/pricing for Langfuse price (all tiers, units, retention)
- LEAD-FETCH: https://langfuse.com/self-hosting/license-key for Langfuse audit-log/masking gating
- LEAD-FETCH: https://langfuse.com/docs/evaluation/overview for evals gates
- LEAD-FETCH: https://www.helicone.ai/pricing for Helicone price
- LEAD-FETCH: https://www.mintlify.com/blog/mintlify-acquires-helicone for Helicone maintenance-mode wording
- LEAD-FETCH: https://retool.com/pricing for AK-G15 portal UI price (audit logs, external users)
- LEAD-FETCH: https://docs.retool.com/org-users/guides/audit-logs for AK-G15 audit view and retention
- LEAD-FETCH: https://www.appsmith.com/pricing for AK-G15 portal UI price and audit logs
- LEAD-FETCH: https://budibase.com/pricing/ for AK-G15 portal UI price and audit logs
- LEAD-FETCH: https://raw.githubusercontent.com/Budibase/budibase/master/packages/pro/LICENSE.md (404 here; find the correct path) for BSL terms
- LEAD-FETCH: https://www.port.io/pricing and https://docs.port.io/actions-and-automations/create-self-service-experiences/set-self-service-actions-rbac/ for AK-G15 approvals
- LEAD-FETCH: https://grafana.com/pricing/ , https://www.honeycomb.io/pricing , https://signoz.io/pricing/ for managed OTel backend price
- LEAD-FETCH: https://opentelemetry.io/docs/specs/semconv/gen-ai/ for P5a/P5b1 attribute names and status

## Sources (all read 2026-11-07)
VERIFIED (fetched):
- https://raw.githubusercontent.com/langfuse/langfuse/main/LICENSE and /ee/LICENSE
- https://pypi.org/pypi/langfuse/json (version 5.2.0, MIT)
- https://github.com/langfuse/langfuse/releases.atom
- https://raw.githubusercontent.com/Helicone/helicone/main/LICENSE and README.md; https://github.com/Helicone/helicone/releases.atom
- https://raw.githubusercontent.com/open-telemetry/opentelemetry-collector/main/LICENSE; releases.atom of opentelemetry-collector-releases, opentelemetry-python, opentelemetry-specification
- https://raw.githubusercontent.com/appsmithorg/appsmith/release/LICENSE and README.md; https://github.com/appsmithorg/appsmith/releases.atom; https://github.com/appsmithorg/appsmith/tree/release/app/client/src/ee
- https://raw.githubusercontent.com/Budibase/budibase/master/LICENSE; https://github.com/Budibase/budibase/releases.atom
Secondary (WebSearch snippets only, UNVERIFIED): jetadmin.io, usagepricing.com, uibakery.io, activepieces.com blog (Retool, Appsmith, Budibase, Langfuse prices); community.retool.com (user tasks); rapidevelopers.com (Retool audit log); docs.port.io and port.io blog (approvals); roadmap.port.io; dealroom and plushcap copies of the Mintlify Helicone post; windmilldocs.pages.dev mirror; costbench/last9/cubeapm blogs (Grafana, Honeycomb, SigNoz prices); docs.honeycomb.io 2026 pro plan changes; dash0.com and oneuptime.com (OTel GenAI status); langfuse.com/self-hosting/license-key (as a search result); pypi.org project pages bijotel, auditant, ttt-otel; mlflow.org compliance article.

---

# PASS 3-4 (full agent file)

# Pass 3, part 4: masking/guardrails and metering/billing (read 2026-11-07)

Role: research/evidence only. No ticket changes. EGM skipped: read-only research.

## 0. Fetch reality (read this first)

- VERIFIED-capable hosts from this machine: `pypi.org/pypi/<pkg>/json` and `raw.githubusercontent.com` (curl, HTTP 200). Everything else failed: `microsoft.github.io`, `docs.litellm.ai`, `docs.stripe.com`, `stripe.com`, `getlago.com`, `withorb.com`, `openmeter.io`, `aws.amazon.com`, `docs.aws.amazon.com`, `lakera.ai`, `developers.cloudflare.com` all returned DNS failure (curl code 000 / WebFetch ENOTFOUND). `api.github.com` returned 403. `github.com/BerriAI/litellm/issues/12977` WebFetch worked.
- Consequence: **no vendor price was read from a primary page. Every price below is UNVERIFIED** (search snippets or aggregator sites). Licences and release dates marked VERIFIED come from PyPI JSON or a LICENSE/README file on raw.githubusercontent.com, read 2026-11-07.
- WebSearch results are secondary. Where a snippet quoted a vendor doc, I say so; I did not open the vendor doc.

## 1. Summary table

| Item | Module(s) | Need cover % (my estimate) | Licence (SPDX) | Last release | Small-client price/month | Client can own it | Verdict | Changed since scan 1 |
|---|---|---|---|---|---|---|---|---|
| Microsoft Presidio | P5c, P1c | detection 60-70; fail-closed + safe put-back 0-10 | MIT VERIFIED (raw LICENSE + PyPI) | 2.2.366, 2026-10-27 VERIFIED (PyPI) | $0 + a few USD hosting (UNVERIFIED) | yes | WRAP | no change (licence/date now confirmed by me) |
| Guardrails AI (`guardrails-ai`) | P5c, P2d | detection via Presidio wrapper ~60; no put-back | Apache-2.0 VERIFIED (PyPI + raw LICENSE) | 0.11.0, 2026-08-14 VERIFIED | $0; "Guardrails Pro" price not public (UNVERIFIED) | yes (OSS) | DROP as dependency (adds a layer over Presidio, default on_fail is noop per one blog) | no change; on_fail default noted |
| Lakera Guard | P2d, P5c | injection/PII classification ~30; not a masker | proprietary / UNVERIFIED | n/a (SaaS) | free community tier ~10K req (UNVERIFIED); paid = enterprise quote | contract only | DROP | changed: deal confirmed closed 2025-10-22 (secondary, several outlets); scan 1 had conflicting dates |
| Protect AI LLM Guard | P5c | Anonymize+Vault+Deanonymize ~60 as design | MIT VERIFIED | 0.3.16, 2025-05-19 VERIFIED | $0 | yes, but dead | DROP (design reference only) | **changed: repo README says "THIS PROJECT HAS BEEN ARCHIVED ... no longer under active development or maintained" VERIFIED** (scan 1 only had a third-party claim) |
| AWS Bedrock Guardrails | P5c, P2d | PII detect/mask ~50; block ~50; no reversible put-back; text already left client to AWS | proprietary service | n/a | ~$0.10 per 1K text units for ML PII filter, regex free (UNVERIFIED, snippet) | client's own AWS account | DROP for the guarantee (optional second detector) | no change |
| Azure AI Language PII / Content Safety | P5c | detect/redact ~50; irreversible | proprietary | n/a | 5K text records/month shared free tier; paid rate not read (third party says $1.00 to $0.25 per 1K records, UNVERIFIED) | client's own Azure | DROP | partly new (Azure was a stub in scan 1) |
| GCP Model Armor + Sensitive Data Protection | P5c, P2d | ~40 | proprietary | n/a | free 2M tokens/mo then $0.10 per 1M tokens (UNVERIFIED, snippet quoting Google page; one Medium post says $1.50, conflicts) | client's own GCP | DROP | new |
| Cloudflare AI Gateway DLP | P5c | block/flag/redact ~40; irreversible | proprietary | n/a | DLP scanning free on all plans per pricing page snippet (UNVERIFIED, not opened); Guardrails billed as Workers AI tokens | yes | ADOPT as optional extra layer only | no change |
| Stripe Billing (Meters) | billing the CLIENT; not P4 | invoicing 90+; spend wall 0 | proprietary | SDK stripe-python 16.1.0, 2026-10-29 VERIFIED (MIT) | 0.7% of Billing volume on top of processing (UNVERIFIED, one source; another says 0.5/0.8) | yes | ADOPT (for invoicing only) | **changed: Stripe docs (snippet) now say use Metronome for new usage-based billing, not Billing Meters; LLM token billing runs on Metronome, private preview per docs** |
| Orb | billing client | invoicing 90+; spend wall 0 | proprietary service; SDK `orb-billing` Apache-2.0 VERIFIED (PyPI 4.96.0, 2026-11-07) | SDK only | sales-led, no public price (UNVERIFIED) | yes, contract | DROP for small client | changed: one 2026 roundup says Adyen completed acquisition 2026-07-01 (single source, UNVERIFIED) |
| Lago | billing client | invoicing 85+; spend wall 0 | **AGPL-3.0 core, VERIFIED (raw LICENSE "GNU AFFERO GENERAL PUBLIC LICENSE v3") - FLAG** | python client 1.57.0, 2026-11-05 VERIFIED (MIT) | self-host $0; Cloud/Premium = quote (UNVERIFIED; README says "Talk to us about Lago Cloud") | yes (self-host), AGPL obligations if modified and exposed | DROP for first client (ADOPT only if a client needs self-hosted invoicing) | changed: README now ships MCP server, CLI, Python Agent SDK (MIT) for LLM token events; AI demo prices input/output token events |
| OpenMeter | billing client | metering+billing ~80 | Apache-2.0 claimed by search summary, repo LICENSE not read: UNVERIFIED (raw URLs for openmeter/openmeter and kong/openmeter returned 404, repo moved) | PyPI `openmeter` 1.0.0b236, 2026-10-09 VERIFIED (Apache-2.0 on PyPI) | Cloud being migrated into Kong Konnect mid-2026; price not found | self-host yes | DROP for first client | no change (Kong acquired Sept 2025) |
| LiteLLM budgets | P4a, P4b1, P4c | visibility/budgets 70-90; hard cap under concurrency: not proven either way | MIT core + `enterprise/` commercial dir VERIFIED (raw LICENSE text) | 1.108.2, 2026-11-06 VERIFIED (PyPI) | $0 self-host | yes | WRAP (visibility, coarse key budgets); KEEP-CODE for the cap | **changed: incident re-checked (section 4); the #12977 "$764 vs $50" claim in secondary blog is NOT a concurrency bug (section 4)** |

## 2. Per-module findings

### P5c redactor + masked model wrapper + safe put-back (also P1, P1c, P2d)

1. Need: mask PII/account numbers BEFORE any model call; restore only into the right place; if the masker fails, no call is made.
2. Candidates: Presidio (+ own wrapper), LiteLLM Presidio guardrail, Cloudflare/Bedrock/Azure/GCP managed filters. Rejected: LLM Guard (archived), Lakera (SaaS, text leaves first, Check Point), Guardrails AI (thin layer over Presidio).
3. Evidence per candidate:
   - Presidio: MIT, 2.2.366, 2026-10-27 (VERIFIED). Reversible only via encrypt/decrypt operators with a stored key and saved result metadata; replace/mask/redact/hash cannot be reversed (search snippet quoting Presidio docs; Presidio docs not reachable, UNVERIFIED). No vault is provided; the round trip is ours.
   - LiteLLM Presidio guardrail: `output_parse_pii` only restores tokens masked on input and does not scan output; scanning output needs `presidio_filter_scope: output/both` (snippet quoting LiteLLM docs, UNVERIFIED). Behaviour when Presidio is down (fail open or closed), and streaming behaviour: NOT FOUND in any source. This is exactly the guarantee gap and I could not close it by reading.
   - Guardrails AI `DetectPII`: wraps Presidio; `on_fail` values reask/fix/filter/refrain/noop/exception; one Nov-2026 blog says default is noop (UNVERIFIED), so fail-closed needs explicit `exception`.
   - Cloud filters: all run after text leaves our process, and redaction is not reversible (Cloudflare per scan 1 and snippet; Bedrock ML PII filter masks to tags).
4. Cannot guarantee: masking BEFORE the model as fail-closed (no source documents timeouts/errors blocking the call); restore into the correct field only, no double restore, no restored text re-entering a prompt; tool-call arguments and streaming.
5. Verdict: WRAP. Presidio (or another detector) is adopted; ours is the guarantee layer. P1/P1c (folding, base64 view, host names): KEEP-CODE small, no product found. P2d (hidden channels, look-alikes): DROP from first-client scope; the only candidates (Lakera/Bedrock/Cloudflare) classify after the text left.
   - Test idea (guarantee): inject detector exceptions, timeouts and a detector returning malformed spans; assert the model client is never called and the typed refusal is recorded. Second test: a model reply containing a placeholder token it invented or duplicated; assert no restore and a typed refusal.
6. n8n+Close+Claude alone: n8n Guardrails Sanitize Text (regex) or HTTP call to a Presidio container covers lead enrichment/reply drafting masking. Truly needs our module: an offer that promises "account numbers never reach the model" with a failure-time proof.
7. Price: Presidio free; Bedrock ~$0.10/1K units (UNVERIFIED); Azure and GCP see table. Client can own Presidio: yes.

### P6b1 no-training statement check

Not in the market for this pass; unchanged from scan 1: DROP as code for v1 offers (ADOPT checklist + signed DPA). No change.

### P4a exact cost / P4c alerts and max_run_usd

- LiteLLM price map and cost calc remain the best data source (MIT, 1.108.2, 2026-11-06 VERIFIED). No new candidate. Verdict P4a WRAP, P4c WRAP (n8n delivers alerts; exactly-once ledger stays ours only if sold). No change.

### P4b1 reserve/settle hard cap under concurrency (the guarantee to test)

1. Need: reserve worst case before the call, settle after, never exceed cap with N parallel callers, and refuse instead of estimate.
2. Candidates and evidence:
   - LiteLLM budgets: spend is recorded after the response, written asynchronously (secondary write-up). I found NO source (primary or secondary) showing a reservation step. A blog cites issues #12977 and #18730 as concurrency overshoot; I opened #12977 (VERIFIED 2026-11-07): it is "Budget Limitations Can Be Bypassed Using AzureOpenAI Library", state closed as not planned (stale bot, 2025-10-31), reporter saw a 400 "Budget has been exceeded! Current cost: 764.78, Max budget: 50.0" on one client and success on the AzureOpenAI client, no mention of concurrency, and one commenter could not reproduce. So that claim is a client-path bypass, not a proven race. #18730 and #20977 were NOT opened (GitHub issue pages beyond the one fetched not tried), so the race claim stays UNVERIFIED either way.
   - Anthropic console workspace/org spend limits: secondary guides say batch jobs may slightly exceed, check happens between requests, and error code is reported variously as 400 or 429 (all UNVERIFIED). Verdict: provider-side limit is a backstop, not a per-tenant cap.
   - Bifrost (vendor blog): pre-request budget check, HTTP 402 on exhaustion; atomic reservation under concurrency not described (UNVERIFIED).
   - Portkey: budget limits and alerts; blocking behaviour unclear in snippet.
   - Tollgate (JumpMasters/tollgate, small OSS project): reserves, then commits or releases, but its own README says the reservation engine has not landed (per search summary, UNVERIFIED).
   - liter-llm (Rust crate): its own source documents that its hard limit is best-effort under concurrency because cost is recorded after the response (search summary of docs.rs source).
3. Cover: gateways 30-40 for visibility-plus-coarse-cap; reservation under concurrency 0 proven.
4. Cannot guarantee: cap never exceeded with concurrent in-flight calls; refuse instead of estimate when usage is missing.
5. Verdict: KEEP-CODE. Test idea: set cap to 1 call's worst case, fire 50 parallel calls against a stub provider that sleeps; assert at most one is admitted, others get a typed refusal, and spent+reserved never exceeds cap. Repeat with provider returning no usage: assert refusal, not an estimate. The same harness, pointed at a LiteLLM key with `max_budget`, is the cheap way to settle the unproven claim.
6. n8n+Close+Claude alone: fine for alerts and monthly provider-side limits. Needs our module only if the offer promises a hard per-client dollar wall.

### P4b2 billed vs unbilled failed calls

1. Need: classify each failure (429, 529, timeout, stream cut, 400 content) as cost-incurred or not, then release or keep the reservation.
2. Search: Anthropic error doc (`platform.claude.com/docs/claude/reference/errors`) lists 529 overloaded and 504 timeout guidance but, per the search summary, says nothing on billing. One non-vendor site says overloaded errors are not charged; nothing on tokens of an interrupted stream. No product publishes a per-failure billed/unbilled table. Stripe/Lago/Orb/OpenMeter bill the CLIENT and do not decide what the provider charged us.
3. Cover ~5%. Cannot guarantee anything: the provider-side truth is unpublished (UNVERIFIED).
4. Verdict: KEEP-CODE. Conservative rule available without knowing: keep the reservation (assume billed) for stream cuts and ambiguous timeouts, release only for errors where the response never started (connection refused, 4xx before generation), then reconcile against the provider's usage report. Test idea: table-driven test over every error class asserting the reservation outcome, plus a reconciliation test that flags any call the provider billed but we released.

### Billing the client (Stripe, Orb, Lago, OpenMeter)

- All four turn usage events into invoices for the client; none is a spend wall or provider-cost classifier.
- Stripe: SDK stripe-python 16.1.0 (2026-10-29, MIT, VERIFIED). Billing fee 0.7% of volume (UNVERIFIED single snippet, another source 0.5/0.8%). Stripe docs (snippet) say new usage-based builds should use Metronome; LLM token billing in private preview per docs vs public preview per one analysis (conflict, UNVERIFIED). Client can own a Stripe account: yes.
- Lago: AGPL-3.0 VERIFIED; flag. README (VERIFIED 2026-11-07) lists MCP server, CLI, Agent SDK for Python (MIT) normalising token events.
- OpenMeter: Kong acquired Sept 2025; repo path moved; licence only from a search summary.
- Orb: sales-led; single-source Adyen acquisition claim.
- Verdict for a small first client invoicing by hand or flat fee: not needed. If usage invoicing is ever sold: ADOPT Stripe (client-owned).

## 3. Queries run (all WebSearch, standard mode, 2026-11-07)

Guardrails group (9): LiteLLM presidio output_parse_pii / fail open; Presidio deanonymize encrypt-decrypt vault limitations; Bedrock Guardrails pricing per 1,000 text units; Azure AI Language PII + Content Safety pricing; GCP Model Armor pricing + SDP; Cloudflare AI Gateway DLP; Lakera pricing + Check Point; Guardrails AI DetectPII on_fail; plus scan 1's LLM Guard queries (README read directly).
Billing/metering group (10): Stripe Billing meters price; Stripe token billing / Metronome; Orb pricing; OpenMeter licence + Kong; Lago Cloud pricing; LiteLLM budget race; LiteLLM supply chain 1.82.7/1.82.8; Anthropic spend limit hard cap concurrency; Portkey/Bifrost/Helicone budgets + atomic reservation; Anthropic 529 billing of failed requests.
Direct reads: PyPI JSON for presidio-analyzer/anonymizer, guardrails-ai, llm-guard, litellm, lago-python-client, openmeter, orb-billing, stripe, nemoguardrails; raw LICENSE for presidio, llm-guard, guardrails, lago, litellm; raw README for lago, llm-guard; GitHub issue 12977.

## 4. LiteLLM March 2026 incident, from primary sources

- VERIFIED (PyPI JSON, 2026-11-07): litellm releases between 2026-03-15 and 2026-04-05 are 1.82.3 (03-16), 1.82.4 (03-18), 1.82.5 (03-21), 1.82.6 (03-22 06:35 UTC), then 1.83.0 (03-31), 1.83.1, 1.83.2. **1.82.7 and 1.82.8 are absent from the release list**, consistent with removal. 1.82.6 is the last version before the gap. Current is 1.108.2 (2026-11-06).
- NOT verified from a vendor source: cause, timeline, payload. Secondary sources (NetSPI, Integrity360, Comet, Arthur, others) say first malicious upload 2026-03-24 ~10:39 UTC, 1.82.8 added `litellm_init.pth`, PyPI quarantined the project ~13:38 UTC, root cause is a Trivy compromise exposing PyPI credentials (one source instead says maintainer GitHub account); official Docker image said unaffected. These sources disagree on cause. A LiteLLM post-mortem `docs.litellm.ai/blog/security-update-march-2026` was named by a source but I could not open it. Issues #24512 and #24515 not opened.
- Operational read: pin by hash to a known-good version, never "latest"; run the official image; this incident is a reason to treat any gateway in the path as an attack surface that sees all keys and prompts.
- LEAD-FETCH: https://docs.litellm.ai/blog/security-update-march-2026 for P4 gateway decision.

## 5. Rejected candidates (dated 2026-11-07)

- LLM Guard: archived (README VERIFIED), last release 2025-05-19.
- Lakera Guard: SaaS, text leaves before masking, acquired by Check Point (closed 2025-10-22 per secondary), enterprise pricing.
- Guardrails AI: no new capability over Presidio; fail-closed needs explicit config; hub install deprecation per one blog (UNVERIFIED).
- Orb: sales-led, no public price.
- Lago: AGPL, quote pricing for cloud; no need for first client.
- OpenMeter: licence unverified, product folded into Kong Konnect.
- Tollgate / Hardcap: early-stage, reservation engine not landed per README summary.
- Bedrock/Azure/GCP guardrails as the core masker: irreversible, remote, per-use fees.

## 6. Verdict counts

Product items (13 rows in section 1): ADOPT 2 (Cloudflare DLP optional layer, Stripe for invoicing), WRAP 2 (Presidio, LiteLLM budgets), KEEP-CODE 0, DROP 9 (Guardrails AI, Lakera, LLM Guard, Bedrock, Azure, GCP, Orb, Lago, OpenMeter).
Module level: WRAP 3 (P5c, P4a, P4c), KEEP-CODE 4 (P1/P1c, P4b1, P4b2, plus P2d only if redaction is sold as a guarantee), DROP 2 (P2d for first client, P6b1 as code).

## 7. LEAD-FETCH lines

- LEAD-FETCH: https://docs.litellm.ai/blog/security-update-march-2026 for P4 gateway decision
- LEAD-FETCH: https://docs.litellm.ai/docs/proxy/guardrails/pii_masking_v2 for P5c (fail open/closed, streaming)
- LEAD-FETCH: https://docs.litellm.ai/docs/proxy/users for P4b1 (budget enforcement semantics)
- LEAD-FETCH: https://github.com/BerriAI/litellm/issues/18730 and /20977 for P4b1 (race claims)
- LEAD-FETCH: https://aws.amazon.com/bedrock/pricing/ for P5c
- LEAD-FETCH: https://azure.microsoft.com/pricing/details/language/ for P5c
- LEAD-FETCH: https://cloud.google.com/security/products/model-armor/pricing for P5c
- LEAD-FETCH: https://developers.cloudflare.com/ai-gateway/reference/pricing/ for P5c
- LEAD-FETCH: https://stripe.com/pricing and https://docs.stripe.com/billing/token-billing for client billing
- LEAD-FETCH: https://getlago.com/pricing and https://www.withorb.com/pricing and https://openmeter.io/pricing for client billing
- LEAD-FETCH: https://www.lakera.ai/pricing for P2d
- LEAD-FETCH: https://platform.claude.com/docs/claude/reference/errors and Anthropic/OpenAI billing pages for P4b2 (failed-call billing)
- LEAD-FETCH: https://microsoft.github.io/presidio/anonymizer/ for P5c (reversibility)
- LEAD-FETCH: https://github.com/openmeter/openmeter/blob/main/LICENSE (repo moved; find current path) for billing

## 8. Three findings (under 150 words)

1. Still no product proves a hard cap under concurrency. The popular "LiteLLM let $764 through a $50 cap" claim is issue #12977, which I read: a client-library bypass, closed stale, not a race. The race claim is unproven, not disproven; one 50-parallel-call test settles it.
2. LLM Guard is confirmed archived by its own README; PyPI shows litellm 1.82.7/1.82.8 removed, but cause and timeline rest on secondary sources only.
3. No vendor publishes whether failed or cut-off provider calls are billed, so P4b2 remains KEEP-CODE. Prices: none verified, the vendor hosts are unreachable here.

---
