# Core plan v4 (delta to plan-v3): market-aligned, client-chosen automation tool

Date: 2026-11-07 (UTC 09:55 / IST 15:25). Author: lead (laptop). Status: DRAFT for EGM review. Basis: market-scan-1.md, market-scan-2.md (+ addenda, pass 4), `handover/evidence/lead/lead-fetch-2026-11-07.md` (68 pages read by the lead), the lead's earlier fact-check batch, owner decisions below. This file changes plan-v3 only where it says so; everything else in plan-v3 stands.

## 1. Owner decisions that shape this plan (2026-11-07, his words condensed)
1. The CLIENT chooses the automation tool: n8n self-hosted (licensed by the client), n8n Cloud, or Make. We do not name one. (Rule: `client-chooses-tools-policy`, `options-first-then-decide`.)
2. Per-seat tools (Port, Retool and similar) add up to sums small clients will not pay; they are NOT a default part of any build.
3. Do not cut anything that connects to n8n or Make.
4. Plan every module, v1 and later, with EGM and the best quality and performance; no time wasted.

## 2. What the research settled (facts read at the source on 2026-11-07; the unverified are marked)
- No ready-made product gives "same key, one effect, forever". Windows: SQS FIFO 5 minutes; Cloud Tasks names 24 h after deletion; Pub/Sub exactly-once regional, pull-only, not publisher side; Hatchet sliding TTL; pg-boss/Graphile/Procrastinate windowed. => the AK-G2 ledger stays our code.
- Hard spend cap: Cloudflare says a burst can briefly exceed its limit (read). LiteLLM docs (long page, tail summarised by a small model) describe a reservation before the call and a fail-closed option, but also overshoot when reservation is off or without a database. NOT PROVEN either way: a 50-parallel test decides (section 6, T1).
- No vendor publishes whether failed or cut-off provider calls are billed (Claude errors page lists codes, no billing statement). => P4b2 stays ours.
- n8n: licence Sustainable Use 1.0 (running it inside the client's own account for the client's own business is within it; hosting one n8n for several paying clients is NOT). Community (free) self-hosted lacks sharing of workflows and credentials, projects, environments, external secrets, SSO, Git version control, log streaming, multi-main; those need a paid self-hosted plan (Business EUR 667 a month annual) (docs page read). Cloud Starter EUR 20, Pro EUR 50, Business EUR 667 a month billed annually (2.5K, 10K, 40K executions) (read).
- Make: free 1,000 credits a month; one action costs about one credit; plan prices NOT READ (page did not render) => UNVERIFIED, quote only after a read. Proprietary SaaS; the client owns the account.
- Activepieces: MIT outside its `ee` folders, the only automation tool an agency may legally resell; Plus USD 20 a month (read). Offered as a named alternative, not a default.
- LiteLLM: malicious releases 1.82.7/1.82.8 (March 2026) and 1.107.0 (October 2026): the proxy is never a core dependency. Price map only, as data behind our validator.
- Presidio is MIT and the best detector to wrap; Cloudflare DLP only flags or blocks (cannot mask), Bedrock/Azure/GCP filters are irreversible and remote. Our wrapper (mask BEFORE the model, no model call after a redactor error, restore in code) stays ours.

## 3. Shape of the connection (what makes n8n, Make and the core work together)
```
client's tool (n8n self-hosted | n8n Cloud | Make | Activepieces)   <- the client chooses, owns the account, pays the licence
        |  signed webhook IN                              ^  governed action API OUT (executor, approvals, caps)
        v                                                |
   [ Hadavin door ]  AK-G2 receipt ledger -> AK1 step -> AK1b outbound gate (mask) -> llm kind -> executor kind
        |                       |                                   |
     store (Postgres / SQLite)  stop_state (P2a)           meter (P4b) + audit (signed, tamper-evident)
```
- The core stays tool-agnostic: the door is one signed-webhook contract and one action-API contract. A tool is a "channel" kind backend with a neutral default (plain webhook) and adapters for n8n, Make and Activepieces, each as a template pack of exported flows in git plus 5-10 end-to-end tests on made-up data (client-chooses rule 6).
- High-risk steps (money movement, irreversible actions, masking, approval binding, audit, spend wall) never live inside a no-code flow. No-code moves data and notifies.
- Licence guard in every quote and contract schedule: n8n runs in the CLIENT's account or infrastructure for the client's own business; we never host one shared n8n for several clients.

## 4. Module decisions (verdict, rung, why). Rung: 1 no-code, 2 our core modules, 3 existing free tool, 4 free library, 5 new own code (R447/R448)
| Module / package | v1 or later | Decision | Rung and evidence |
|---|---|---|---|
| P1a, P1b text folding, P1c | v1 (P1c later) | FINISH what is built; Presidio is NOT a replacement (it detects, it does not fold look-alikes) | 5 for the fold; evidence: scan table 40-60% cover only |
| P5c redactor | v1 | WRAP: Presidio (MIT) as the detector backend behind the `redactor` kind (alternative: the pattern backend); our wrapper and put-back stay | 4 + 5; scan pass 3-4 |
| P2a stop state | v1 | KEEP-CODE | cloud kill switches do not give "agent cannot clear + audited reset" |
| P4a usage and price, P4b1 meter, P4b2 billing classes, P4c alerts, P4d store contract | v1 | KEEP-CODE; P4a uses a price table as DATA, never the LiteLLM proxy; before building more of P4b1, run test T1 | 5; sections 2 and 6 |
| P3a migrations | v1 | FINISH (PR 73) | 5 |
| P5a, P5b1 diagnostics and provider errors | v1 | FINISH (PR 80); align names with OTel GenAI `error.type` as a pin (status Development) | 4 |
| P5b2, P5b5 CI tables and pins | v1 | HOLD, owner decides: ast-grep covers 85-90% per scan; PR 85 is built and reviewed. Cut only with written evidence and his yes (improve-before-replace) | 3 |
| P2d fold scan + hidden-channel refusal | v1 -> later | KEEP BUILT, do not extend; off by default for a first client without regulated data | scan: 'drop for first-client scope' |
| P6a client-profile check | v1 | FINISH (PR 72) | 5 |
| P6b1 no-training check | v1 | KEEP BUILT (PR 86 passes 10,446 tests on both Pythons on the laptop); do not extend; owner may convert it to a config/doc check | scan: 'weakest verdict' |
| AK-G2 door + ledger | v1.1 FIRST | BUILD NEXT: it is the n8n/Make door and the permanent no-double-apply ledger; claim/lease/retry may WRAP pg-boss or Graphile Worker (MIT) on the client's Postgres | 4 + 5; pass 4 |
| AK-G15 needs-a-person queue | v1.1 | KEEP-CODE for store, digest binding, separate executor role; the waiting screen is the client's own tool (n8n Wait/approval node, Make, a Close task) | scan 55-70% wait, 20-30% guarantee |
| AK-G1 hand-off lease | v1.1 | KEEP-CODE | no tool owns a conversation lease |
| AK1a/1c tenant | v1.1 | WRAP Postgres row-level security (FORCE) + our tests | 3 |
| AK1b the ONE outbound gate | v1.1 | KEEP-CODE | no product does it |
| AK2a document reader | v1.1 | WRAP docling/pypdf; our limits on hostile files | 3/4 |
| AK4a eval gates | v1.1 | WRAP promptfoo/DeepEval or Langfuse scoring (MIT core) for scoring; the release gate stays ours | 3 |
| AK-G16 deploy into client cloud | v1.1 | ADOPT Helm/Kustomize/OpenTofu/wrangler/CDK mechanics; five-part split ours | 3 |
| P0t, AK0, JG-3 | - | already shipped / dropped / paused | n/a |
| Portal | later | NO per-seat product in any default build. Default: the client's own tool reads a read-only role; optional Appsmith (Apache-2.0) if a client wants a screen and pays; Port/Retool only if the client already has them | options-first |

## 5. Cost model the quote must show (per client, per year; the client pays licences; unverified prices marked)
| Automation tool | Per month | Per year | Notes |
|---|---|---|---|
| n8n Cloud Starter / Pro / Business | EUR 20 / 50 / 667 | EUR 240 / 600 / 8,004 | billed annually; 2.5K / 10K / 40K executions; Business is self-hosted only |
| n8n self-hosted Community | EUR 0 licence + hosting (not priced) | hosting only | NO credential sharing, no SSO, no Git, no environments; one-person team only |
| Make | NOT READ | NOT READ | free 1,000 credits; do not quote until read |
| Activepieces Plus | USD 20 | USD 240 | MIT; alternative |
| Our hosting of the door | client's cloud, about USD 5-10 (Cloudflare Workers Paid USD 5 read; others unverified) | USD 60-120 | client account |
Seat-priced tools shown to a client only as an option: Port Basic USD 30 per seat per month (10 seats = USD 3,600 a year), Retool Business USD 50-65 per builder (read), Langfuse audit logs need Enterprise USD 2,499 a month (read). Rule: the quote lists these only when the client asked for that tool; a total is always printed next to the unit price.

## 6. Tests that decide open points (all free, made-up data, no real keys)
- T1 cap: 50 parallel calls against one cap on our meter AND against a LiteLLM key with `max_budget`, stub provider that sleeps; sum of admitted must not exceed the cap. LiteLLM runs only in a locked-down container with no secrets, version pinned by hash to a known-good release. Needs the owner's yes (runs third-party code).
- T2 ledger: replay the same signed delivery after 6 minutes, 25 hours and 31 days; kill the process at random points; one effect.
- T3 mask failure: force the detector to raise; assert zero provider calls.
- T4 stop: agent role attempts to clear the stop; denial and audit row.
- T5 door contract: each tool's template pack (n8n, Make, Activepieces) sends signed, replayed, reordered and malformed webhooks to the door; no loss, no double effect.

## 7. Order of work and lanes (agent time; test queue is the limit, not agents)
1. Now (cloud, parallel): finish and verify the open chain: P1b fix batch -> PR 63+70 merge; PR 66 money chain; PR 80; PR 72; PR 73; PR 83; PR 85/86 fixes. Laptop takes evidence runs for pushed heads (never the same head twice).
2. In parallel, read-only: EGM reviews of THIS plan (section 8).
3. After the open chain: AK-G2 door + ledger (with T2), then the channel-kind template packs for n8n, Make, Activepieces (T5), then AK-G15, AK1b, AK-G1.
4. Estimate: no calendar total until the open chain's merge order is clear; the first door+ledger PR is about 1 day of agent time after the P1b/P4d merges.

## 8. EGM sequence for this plan and each package
Plan: `egm-review` (design, implementation-readiness, zoom-out "should this exist", comprehension) on the cloud, then `egm-resolve` (lead, Opus), then freeze after at most 3 rounds. Each package follows the standing sequence: draft -> plan review -> build -> evidence runner -> `egm:*` result review -> resolve -> drift report; security/money/redaction paths have no round cap.

## 9. Rung table (R448) for the changes this plan makes
| Component | Need | Rung tried | Evidence | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Door + ledger | no loss, no double effect, forever | 3 (SQS, Pub/Sub, Hatchet), 4 (pg-boss, Graphile) | primary pages 2026-11-07 | permanent dedupe, receipt before ack, effect in one transaction | KEEP-CODE; WRAP queue lib for lease/retry |
| Detector | find personal data | 4 Presidio MIT | PyPI 2.2.366 2026-10-27 | fail-closed wrapper, put-back | WRAP |
| Template packs | n8n/Make/Activepieces flows | 1 | vendor pages | the contract tests | CUT-TO-CONFIG+GLUE |
| Portal screen | people approve items | 1/3 client's own tool; Appsmith Apache-2.0 | scan 3-3 | read-only role, digest binding | CUT-TO-CONFIG |
| CI tables P5b2/P5b5 | catch new unsafe sites | 3 ast-grep MIT | scan: 85-90% | none beyond CI | HOLD for owner |

## 10. Open items needing the owner (defaults apply if no answer within the work block)
1. T1 (runs LiteLLM in a sealed container): yes or no. Default: no, we test our own meter only and mark the LiteLLM claim UNVERIFIED.
2. P5b2/P5b5 cut (ast-grep): default keep PR 85 as built.
3. P6b1 convert to config/doc check: default keep PR 86 as built.
4. Make plan prices: lead reads them in a browser session when the Playwright server is available (default: unquoted).
