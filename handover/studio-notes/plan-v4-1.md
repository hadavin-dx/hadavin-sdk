# Plan v4.1 = AMENDMENT A8 to the frozen plan-v3 (market-aligned, client-chosen automation tool)

Status: DRAFT for EGM round 2 (STANDING-ORDERS 6b: three fresh reviewers, design, readiness, comprehension, reports in `handover/reviews/plan-v4-round2/`). Not binding until the lead records it after review.
Written: 2026-11-07 by the cloud session (plan author only; the lead runs the review and resolve steps, EGM-GATE v1).
Built from: `studio-notes/plan-v4-1-resolve-round1.md` (the lead's 12 rulings, called R1..R12 below), applied to `studio-notes/plan-v4-market-aligned.md` (plan-v4, left unchanged), with `studio-notes/amendments.md`, `LEAD-ORDERS.md` orders 138, 139, 140 (lines 952 to end), and the five round-1 reports in `handover/reviews/plan-v4-round1/` (structural, comprehension, zoom-out, readiness, design). Every round-1 finding id is in the change table (section 12).
Honesty note: the lead's resolve says it read the five reports only in part ("PARTLY READ"). Findings that no ruling answers are marked AUTHOR (an editorial fix made here, which round 2 must check) or OPEN (needs the lead). I did not open any vendor page; every vendor fact below is copied from a file in this checkout and keeps that file's marker.

Numbering note: `amendments.md` already holds an entry called "A8" (2026-11-05, lead verification of memo claims). The resolve names this plan "AMENDMENT A8". Two entries with one name: the lead picks a new number when recording it (OPEN, section 11).

CODE-LAST v1: this plan proposes components; its rung table is section 6.

## 0. What the words and ids mean (read first)

### 0.1 Verdict words (R1)
| Word | Meaning in A8 |
|---|---|
| ADOPT | use an outside tool or library as it is, behind a kind |
| WRAP | use an outside tool or library behind our wrapper module (R450(k): wrap, do not fork) |
| KEEP-CODE | our own code, because it carries a guarantee no tool gives (R448 list) |
| DROP | not built; nobody needs it now |

The rung table (section 6) uses the R448 verdict tokens instead, because the ticket check reads them: KEEP-CODE (we write it), CUT-TO-CONFIG+GLUE (a tool does it; we only configure and connect it; the part is still delivered, nothing is removed), CUT (dropped).
plan-v4 also used FINISH, KEEP BUILT and HOLD. In A8 these are not verdicts; they are a **Status** (column in section 5):
| Status | Meaning |
|---|---|
| IN FLIGHT | built or being built, in an open pull request; finish it |
| BUILT, NOT EXTENDED | built; keep as it is; no new work |
| OWNER-OPEN | the owner decides; the default applies until he does |
| DEFERRED | frozen ticket, not built until a lead order lifts it (order 57.2, order 59) |
| PAUSED | stopped by the owner (amendment A15 note, order 49) |
| UNCHANGED | the plan-v3 row stands; A8 did not re-examine it |

### 0.2 Rung (R1)
"Rung" = a step of the tool ladder in bible R447 (current order, owner 2026-11-06; `handover/bible-extract-R447-R450.md:3`):
gate first (scope, budget, client size and willingness, and the client's own tool, written as **rung 0**; a rung the client closed is written CLIENT-EXCLUDED with date and source, order 68(1)); then
1 no-code and low-code tools (n8n, Make and similar), 2 our core modules, 3 existing free or standard tools used as they are, 4 free libraries we test and build on, 5 our own new code, last, only for guarantee-class steps.
Some reviewers counted seven rungs. That is the older ladder: order 54.1 (1 studio code, 2 client's tool, 3 no-code, 4 MCP, 5 library, 6 model feature, 7 our code), which R447 replaced on 2026-11-06. A8 uses R447 only.

### 0.3 Terms
- **kind**: a swappable module with a neutral default and an alternative (bible R363, R450(j)). Examples here: `llm`, `redactor`, `channel`, `store`, `meter`, `trigger`.
- **door**: the signed webhook address where a client's tool hands work to our core (AK-G2-b, `triggers/webhook.py`).
- **ledger**: the table of received messages that remembers each delivery key (AK-G2-a, `inbound_receipts`), so the same message never starts work twice.
- **step**: one unit of work in the AK1 step contract (an input record with tenant and allowed readers, an output record, a result of done, needs a person, or refused; `studio-notes/kit-plan-v2.md:43`).
- **meter**: the spend meter that reserves money before a model call and settles after (P4b1).
- **stop_state**: the stop switch the agent cannot clear itself, with an audited reset (P2a).
- **mask / put-back**: in A8, "mask" means only one thing: replace personal data or secrets with placeholders before any text reaches a model. "Put-back" means our code (not the model) puts the real values back after the call.
- **Presidio**: Microsoft's open-source personal-data detector (MIT; `reviews/market-scan-2.md:853`).
- **execution** (n8n): one run of one workflow; n8n plans are capped by executions per month.
- **Sustainable Use 1.0**: the licence n8n is published under (fair-code, not open source).
- **EGM**: the studio's review process: fresh reviewer agents read the work (R450(j)); the lead resolves.
- **the lead** = the main Claude session that coordinates and merges; **the owner** = the studio owner (R450(j)). "Author: lead (laptop)" in plan-v4 meant the lead session running on the owner's laptop.
- **the open chain** = the pull requests listed in section 9 step 1 that are open today.

### 0.4 Package and ticket ids (R1)
| Id | What it is | Where defined |
|---|---|---|
| P1a, P1b | plan-v3 P1 split in two PRs: P1a moves the text-folding module and its version; P1b closes gaps 1-5 and 7 | amendments A9 F4, A12 |
| P1c | redactor gaps from the library comparison (base64 view, internal host names) | order 64; `tickets/P1c.md` rev 7 FROZEN |
| P2a | stop state (v3 row P2a) | plan-v3 s6 |
| P2d | v3 row P2d: land PR #50's change to `guard/redact.py`; built as P2d-1, P2d-2 (whole-text refusal when a hidden-channel flag is found), P2d-2b | plan-v3 s6; order 19E; freeze-list |
| P3a | migration rule | plan-v3 s6 |
| P4a, P4c, P4d | as plan-v3; P4d split into P4d-a/-b/-c | A13, A14 |
| P4b1, P4b2 | v3 P4b split: P4b1 meter kind; P4b2 billing classes and orphan sweep | A9 F2, A11 |
| P5a, P5b1..P5b5, P5c | v3 redesign steps (P5b1 = R1P, P5b2 = R3a, P5b3 = R3c+R3b, P5b4 = R2, P5b5 = R5) and the redactor kind | plan-v3 s6 lines 104-110 |
| P6a | client-profile check | plan-v3 s6 |
| P6b1, P6b2 | v3 P6b split: P6b1 no-training lock; P6b2 secret-boundary lint | A9 F6 |
| P0t | stage rename: the retired stage name is replaced by DEMO (stages are DEMO, PILOT, PROD only, R449) | `tickets/P0t.md` rev 1 DRAFT |
| AK-* | Assembly Kit tickets (second phase, amendment A10) | `studio-notes/kit-plan-v2.md`, `tickets/` |
| AK1 | pipeline step contract and the ONE outbound gate; AK1a/AK1c = its tenant parts, AK1b = its outbound gate | `tickets/AK1.md` rev 3 FROZEN |
| AK-G2 | inbound trigger kind: ledger (-a) and signed webhook door (-b); absorbs v3 P7a | `tickets/AK-G2.md` rev 3 FROZEN with build notes |
| AK-G15 | durable queue of "needs a person" items | `tickets/AK-G15.md`; DEFERRED |
| AK-G1 | chat agent with tools and hand-off | `tickets/AK-G1.md`; DEFERRED |
| AK-G16 | deployment into the client's own cloud | `tickets/AK-G16.md`; DEFERRED |
| AK0, AK2a, AK4a | research note; document reader; joined-pipeline test harness | kit-plan-v2; DEFERRED (order 59) |
| JG-3 | chat-ops notifier for the Jagrat demo | A15; PAUSED |

### 0.5 Pull requests named in this plan (from LEAD-ORDERS; state as of order 140)
| PR | Package | Branch or head named in the orders |
|---|---|---|
| 63 | P1a | core/P1a |
| 70 | P1b | core/P1b-fixwip, head b0f54b1 (order 136/138) |
| 66 | P4d-a1 (the "money chain" start) | core/P4d |
| 72 | P6a-1 | head 3adacac |
| 73 | P3a | stacked |
| 80 | P5b1 (with P5a parts) | core/P5b1, head 74ee54f |
| 83 | P0t follow-up | core/P0t-followup, head 72389db |
| 85 | P5b2 | head 26079f9 |
| 86 | P6b1 | core/P6b1, head 39b136a |
Merge state of each: UNVERIFIED here (not checked against GitHub).

### 0.6 Sources (full paths, all under `handover/`)
- `reviews/market-scan-1.md`, `reviews/market-scan-2.md` ("addenda" = Addendum A, line 850, lead-verified facts; "pass 4" = Addendum B, line 860, and the pass 4 text from line 868).
- `evidence/lead/lead-fetch-2026-11-07.md` (68 pages read by the lead).
- `evidence/gateway-check/evidence-1.md` and `reviews/gateway-check-lead-reading-1.md` (order 35 run, LiteLLM 1.108.1).
- ORDER 140 cap test: the resolve names `egm/hadavin-sdk/core-complete/captest-1.md`; that file is NOT in this checkout, so the numbers in section 8 come from the ORDER 140 text only.
- Owner policy names in plan-v4 ("client-chooses-tools-policy", "options-first-then-decide", "client-chooses rule 6") are memory files on the laptop; their content is in bible R445-R447 (the client chooses, options first). Not readable here: UNVERIFIED wording.

## 1. What A8 changes in plan-v3 (R1)
plan-v3 stays frozen; A8 changes only the items below. Everything else in plan-v3 and in amendments A1-A17 stands.

Changed:
1. plan-v3 section 5 (kinds) and the P5c row: unchanged default. The pattern redactor stays the default; Presidio is added as an OPTIONAL alternative backend of the `redactor` kind (R8). This is an addition, not a change of default.
2. plan-v3 v1.1 table row P7a (inbound ledger, trigger "second consumer"): AK-G2 (which absorbs P7a) is the first kit item to build after the open chain, but only when a lead order lifts the deferral rule and the open chain has merged (R9). Until then nothing changes.
3. plan-v3 s6 P4b row: P4b1's evidence set gains test T1 (own meter, 50 parallel; section 8). It adds to, and does not replace, the v3 s8 8-process Postgres race with zero overshoot. T1 is not an owner gate and does not stop P4b1 work (R7).
4. New rule for quotes and contract schedules: the n8n licence line and the cost model (sections 4.4 and 7).
5. New, outline only: the "channel" template packs for client tools (n8n first), built only for a tool a client has chosen (order 57.2 DEMAND rule).

Not changed (said because plan-v4 seemed to change them): P2d stays on (R2); P5b2/P5b5/P6b1 as built, owner decides (R11); AK-G15, AK-G1, AK-G16 stay DEFERRED (R9); no estimates (R12, plan-v3 s10); AK-G2 claim/lease/retry stays our code as the ticket designs it (R3).

## 2. Owner decisions that shape this plan (2026-11-07, condensed by the lead in plan-v4 s1)
1. The CLIENT chooses the automation tool: n8n self-hosted (licensed by the client), n8n Cloud, or Make. We do not name one. (Bible R445, R446.)
2. Per-seat tools (Port, Retool and similar) add up to sums small clients will not pay; they are NOT a default part of any build.
3. Do not cut anything that connects to n8n or Make.
4. Plan every module, v1 and later, with EGM and the best quality and performance; no time wasted.
Note: Activepieces is NOT in the owner's list. plan-v4 added it as a named alternative; A8 keeps it only as an option shown to a client, with no pack built until a client chooses it. The owner may strike it (OPEN, section 11).

## 3. What the research found (facts from files; markers kept)
Found (read at a source by the lead or a scan, file named):
- No ready-made product remembers a delivery key forever. Each forgets it after a window: SQS FIFO 5 minutes; Cloud Tasks task names 24 hours after deletion; Pub/Sub exactly-once is regional, pull-only and not publisher side; Hatchet uses a sliding TTL; pg-boss, Graphile Worker and Procrastinate dedupe only while a job lives or within a window (Addendum B). Cloudflare Workflows keeps instance state 3 to 30 days (`market-scan-2.md:242`, VERIFIED-SRC); Cloudflare Queues retention and the DBOS exactly-once claim: from the zoom-out report Z15, not read here, UNVERIFIED. We need "never forgets", so the AK-G2 ledger stays our code. Hatchet "sliding TTL" and pg-boss "no dedupe option" are inferences of the scan (design F18): UNVERIFIED.
- Spend caps: Cloudflare's own text says a burst of concurrent requests can briefly exceed its limit (Addendum A). LiteLLM: the lead's run of 2026-11-07 (ORDER 140) shows the proxy checks before the call and records spend after, so it overshoots by one call by design (section 8). The order 35 run (2026-11-06, LiteLLM 1.108.1, 20 concurrent) admitted 1 and refused 19, no overshoot seen; slow writes, several workers and streaming were not tested there.
- Billing of failed or cut-off provider calls: the Claude errors page lists codes with no billing statement. That is one page (design F18): "no vendor publishes it" is UNVERIFIED as a general claim. P4b2 stays ours either way.
- LiteLLM supply chain: releases 1.82.7 and 1.82.8 were malicious (GHSA-92x9-889m-jgmw, Addendum A, VERIFIED by the lead); 1.107.0 was compromised in October 2026 (BerriAI/litellm issue 47826, Addendum A; NOT among the 68 pages of lead-fetch). The proxy is never a core dependency; its price map may be used as data behind our validator.
- n8n: licence Sustainable Use 1.0 (Addendum A). Community (free) self-hosted lacks: sharing of workflows and credentials, projects, environments, external secrets, SSO, Git version control, log streaming, multi-main, custom variables, external binary storage (lead-fetch community page; the last two were missing in plan-v4, V4-10). Prices EUR 20 / 50 / 667 a month billed annually with 2.5K / 10K / 40K executions (Addendum A). Per R6, EUR 20 and 50 are n8n Cloud (Starter, Pro); EUR 667 Business is SELF-HOSTED only. Which paid plan unlocks which missing feature: lead-fetch says "Business/Enterprise" with no split, UNVERIFIED per feature. What Cloud Starter and Pro include (sharing, projects): NOT READ.
- Make: free plan 1,000 credits a month (lead-fetch). "One action costs about one credit": NOT in lead-fetch, UNVERIFIED. Plan prices: NOT READ. Proprietary SaaS; the client owns the account; R447 needs an exit plan in the quote for a SaaS tool with no self-host.
- Activepieces: MIT outside its `ee` folders (LICENSE read per scan-2); the `ee` boundary was not read. Among the tools in a limited scan it was the only one found with an MIT core; Make, Zapier, Pipedream and n8n Embed resale terms were not read, and Windmill sells a resale licence (Addendum A). Lead-fetch lists Activepieces Embed from USD 36k a year. Plus USD 20 a month is its CLOUD plan; the MIT licence covers the self-hosted core. (plan-v4's "only automation tool an agency may legally resell" is withdrawn: it was a legal conclusion with no source.)
- Presidio is MIT (Addendum A), PyPI 2.2.366 2026-10-27 (scan). On our hostile set its default masking missed 13 of 30 inputs and flagged 7 of 14 must-keep lines (order 35). Order 64: "no free library beats our redactor on our corpus". Whether Presidio handles look-alike letters: UNVERIFIED (scan-1 lists its Unicode handling as unverified; V4-03).
- Cloud filters: Cloudflare DLP flags or blocks only; Bedrock, Azure and GCP filters are remote, and "irreversible" rests on search snippets (pages did not render): UNVERIFIED.
- OpenTelemetry GenAI `error.type`: status "Development" per plan-v4; the page had moved and was NOT READ (V4-14): UNVERIFIED.

## 4. Shape of the connection, and the door contract

### 4.1 Picture (who calls whom)
```text
client's tool (n8n self-hosted | n8n Cloud | Make | Activepieces)    <- the client chooses, owns the account, pays the licence
   |  (1) client tool calls our door: signed webhook (AK-G2-b)
   v
[ door ] -> [ ledger: receipt, dedupe, claim/lease ] (AK-G2-a) -> AK1 step -> run
                                                                   |-- model call: masked first (P5c redactor kind in v1; AK1 gate in the kit)
                                                                   |-- meter (P4b1) reserve before / settle after
                                                                   |-- stop_state (P2a) read before each step
                                                                   '-- audit (signed, tamper-evident; plan-v3 kinds)
   (2) OUT: "governed action API" -- NO CONTRACT EXISTS YET (section 4.3). Nothing is built for it.
```
Store: Postgres. The ledger and the tenant rules need Postgres (one transaction per receipt in `receive_inbound`; row-level security for tenants). The memory store is for the demo stage and tests only; SQLite is a v1.1 outline (plan-v3 P7l). Whether pilot and prod must refuse any non-Postgres store for these paths: OPEN for the lead (design F20, V4-18).
Gates per path (V4-08): model calls in v1 go through the P5c masked wrapper and the P6a profile check; in the kit, AK1's one outbound gate (order 27 item 63: every outbound path goes through the AK1 gate or the AK-G22 recipient gate). The door itself sends no text (4.2). The OUT path has no gate named because it has no contract (4.3).

### 4.2 Inbound contract = AK-G2 ticket revision 3, verbatim (R4)
No new wording. The text below is copied from `tickets/AK-G2.md`; where this plan and the ticket differ, the ticket wins.
- Line 102: "**Signed inputs only, deny by default.** A webhook without a valid `hmac_v0` signature is refused with 401 before the body is parsed or anything is saved. The sender id is read ONLY from signed bytes (the body), and every source must name the field (`id_field` is required). The tenant, readers, agent and principal come ONLY from the source's config, never from the request. No two inbound sources, and no inbound source and the approval channel, may share a secret (row C7)."
- Line 103: "**No outbound text added (order 27 item 63).** Every reply of the webhook has an EMPTY body (status code and, for 503, a `Retry-After` header only). AK-G2 sends nothing to anyone: no notification, no message, no model call of its own. [...]"
- Line 107: "**Fail closed, and never lose.** A store error before the receipt commits answers 503 (the sender retries); after the commit, every failure leaves the receipt open or releases it, and the lease brings it back. **The run row is the commit point:** exactly one run per message per generation, because the run id is derived from the delivery key and the generation (INFORM I3), and once that run exists dispatch never calls the step again for it. [...]"
- Line 162 (the "one transaction" claim, exactly as the ticket states it): "`receive_inbound(...)`: ONE transaction. **Dedupe first:** if `rec.delivery_key` exists, compare `body_sha256`: equal gives `duplicate`, different gives `conflict`; nothing is written, even when the source is full. [...] A failure leaves no row. (The count and the insert are in one transaction but not serialised, so racing receivers can pass `max_open`; bound in L11.)"
- Line 194 gives the status codes in order: 404 unknown path, 413 too large (before any HMAC work), 401 bad signature, 400 bad body or id, 202 new or duplicate, 409 id reuse, 503 busy (with `Retry-After`) or store error, 500 anything else; every reply body is empty.
- Line 195, forwarder contract (what a sender must do): "Re-sign EVERY attempt with a fresh timestamp; a 401 after a retry means "re-sign and send again", not "give up". Send one JSON object per request, with unique keys. Put the message's id in `id_field` as a JSON string. Resend a retry byte for byte (a re-formatted retry is an id reuse, 409). On 503, wait `Retry-After` seconds and retry."
- The delivery key and body hash use a keyed hash (line 153, `inbound_key` from the deployment's restored-hash key; line 155, `body_sha256`). Signing keys: one or two secrets per source (current and previous, so a key can be rotated), read through the secrets kind, never logged (ticket "Secrets" field). A revocation test is not named in the ticket: UNVERIFIED (design F22).

plan-v4's rung-table phrase "effect in one transaction" is withdrawn. The ticket's claim is narrower: the receipt is written in one transaction, and the run row is the commit point. An effect in a client's own system (a CRM or a payment) is NOT inside our transaction.

### 4.3 What the guarantee does NOT cover (R4, plain words)
- The hop before the door is outside our guarantee. If the client's tool, or the system that feeds it, loses a message before our door answers 202, we never saw it and cannot recover it. n8n's own retry settings and whether n8n stores a webhook before it replies are not stated by n8n (order 57 A: no official statement found). A daily comparison of ids (`compare_ids`, ticket line 192) can show gaps after the fact; who runs it and how often: OPEN.
- The OUT direction ("governed action API", where our core asks the client's tool to act or the tool calls our executor) has NO contract in AK-G2 revision 3: the ticket sends nothing (line 103). R4 says the outbound text is the ticket's verbatim text, but there is no such text to copy. So A8 builds nothing for OUT; a contract (schema, who authenticates, idempotency key tied to the ledger key, credential holder, replay test with one effect) must be written and reviewed first. OPEN for the lead (V4-21, design F3).
- Retention: "forever" means the receipt row and its keyed delivery-key hash are kept; the raw body is deleted by `purge_inbound_bodies` (ticket line 170) and retention per data class is G18. Whether receipt rows themselves are ever deleted: UNVERIFIED from the ticket text I read.

### 4.4 Rules that stay outside any no-code flow
- High-risk steps (money, irreversible actions, masking, approval decisions, audit, the spend wall, retry, dead-letter, idempotency keys) never live inside a no-code flow; the flow calls a core module (R447, order 68(3)).
- A no-code flow never holds approver or executor credentials and gets redacted data only, unless it runs on the client's own instance (R447). So an n8n Wait/approval node, a Make step or a Close task may NOTIFY a person; the approval itself reaches our API under that person's own identity, outside the flow. (This removes plan-v4's AK-G15 row text that put the waiting screen in the tool; AK-G15 is DEFERRED anyway.)
- Licence line for every quote and contract schedule (R5): "the client runs n8n in the client's own account; Hadavin does not host or resell n8n". This is OUR READING of the Sustainable Use text, not legal advice (R450(f): "not reviewed by counsel"). Addendum A says "Service to clients is NOT permitted; the client owns the account"; no clause was quoted with URL and date in this checkout. Whether we may build, patch or operate flows inside the client's instance for a fee is UNVERIFIED. The owner confirms, or a lawyer checks, before the first quote.

## 5. Module decisions
Rows not listed here are UNCHANGED from plan-v3 and its amendments and were NOT re-examined by A8: P0a, P0b, P0c, P0d, P0e, P4c, P5b3, P5b4 (DEFERRED, order 59), P6b2 (DEFERRED, order 59), P8a, P8b (DEFERRED), P8c, the v1.1 table (P2b..P7n), the secrets, signer, audit, channel and executor kinds (plan-v3 s5, A6), and the kit tickets AK2b, AK2c, AK2d, AK3, AK4b, AK5, AK7, AK8, AK-G14, AK-G22 and gap tickets G3, G9-G12, G18, G26.

| Package | Phase | Verdict | Status | Reason and evidence |
|---|---|---|---|---|
| P1a | v1 | KEEP-CODE | IN FLIGHT (PR 63) | look-alike folding; no tool folds look-alikes (scan-1 cover table "40-60%", `reviews/market-scan-1.md`, row not re-located: UNVERIFIED) |
| P1b | v1 | KEEP-CODE | IN FLIGHT (PR 70) | as P1a; orders 136-140 |
| P1c | as order 64 | KEEP-CODE | FROZEN rev 7; build after P1b merges (order 70.1) | whether P1c is v1 or v1.1: UNVERIFIED, the lead says |
| P2a stop state | v1 | KEEP-CODE | IN FLIGHT / per chain | cloud kill switches do not give "agent cannot clear + audited reset" |
| P2d | v1 | KEEP-CODE | ON in v1, as built; no extension (R2) | owner order 11 (cited by resolve and three reviewers; order 11 is not in this copy of LEAD-ORDERS, UNVERIFIED wording), order 19E, order 54.3 |
| P3a | v1 | KEEP-CODE | IN FLIGHT (PR 73) | plan-v3 |
| P4a | v1 | KEEP-CODE | per chain | price table used as DATA; never the LiteLLM proxy |
| P4b1 meter | v1 | KEEP-CODE | per chain; T1 added to its evidence (R7) | no outside cap gives zero overshoot (section 8); order 35 item 1 Options paragraph (client's own gateway as a v1.1 adapter row) stands |
| P4b2 billing classes | v1 | KEEP-CODE | per chain | no billing statement found for failed calls (section 3) |
| P4d | v1 | KEEP-CODE | IN FLIGHT (PR 66) | money SQL (A11) |
| P5a, P5b1 | v1 | KEEP-CODE | IN FLIGHT (PR 80) | names aligned with OTel GenAI `error.type` as a pin (status UNVERIFIED, section 3) |
| P5b2 (v3 step R3a) | v1 | KEEP-CODE | BUILT (PR 85); OWNER-OPEN (R11) | scan: ast-grep covers 85-90% (scan-2, not re-located); a cut needs written evidence, the owner's yes, and an amendment that rewrites P5c's Depends-on (plan-v3.md:149). plan-v4's label "CI tables and pins" does not match v3's "step R3a": which is right is UNVERIFIED (C3) |
| P5b5 (v3 step R5) | v1 | KEEP-CODE | DEFERRED (order 59) and OWNER-OPEN (R11) | as P5b2 |
| P5c redactor | v1 | KEEP-CODE | per chain; scope UNCHANGED (order 35) | default = pattern backend (v3 s5). Presidio = OPTIONAL alternative backend behind the `redactor` kind, NOT the default (R8). Order 35: default Presidio missed 13 of 30 hostile inputs. Our wrapper (mask before the model, no model call after a redactor error, put-back in code) stays. Adding Presidio needs the v3 single-dependency check and a refusal-rate bound in the P5c ticket (OPEN) |
| P6a | v1 | KEEP-CODE | IN FLIGHT (PR 72) | plan-v3 |
| P6b1 | v1 | KEEP-CODE | BUILT, NOT EXTENDED (PR 86); OWNER-OPEN (R11) | laptop: 10,446 passed on both Pythons (order 138); owner may turn it into a config/doc check |
| AK-G2 door + ledger | kit (absorbs v3 P7a) | KEEP-CODE | first kit item after the open chain merges AND a lead order lifts the deferral (R9) | ledger and claim/lease/retry are our code per ticket rev 3 (R3). pg-boss and Graphile Worker are NOT in the core (Node in a Python core; they ignore the ticket's lease design); they appear only as a named OUTLINE for a client who already runs one (trigger: the client asks) |
| AK1 (step contract, tenant AK1a/1c, outbound gate AK1b) | kit | KEEP-CODE (AK1b); tenant: Postgres row-level security FORCE plus our tests | ACTIVE ticket (freeze-list) | no product gives one outbound gate (AK1b). Tenant isolation is Postgres-only (see 4.1, OPEN) |
| AK-G15 needs-a-person queue | kit | KEEP-CODE (store, digest binding, separate executor role) | DEFERRED (order 57.2; R9) | the client's tool may only notify (4.4) |
| AK-G1 hand-off lease | kit | KEEP-CODE | DEFERRED (order 57.2; R9) | no tool owns a conversation lease |
| AK-G16 deploy into client cloud | kit | ADOPT Helm/Kustomize/OpenTofu/wrangler/CDK mechanics | DEFERRED (order 57.2; R9) | five-part split stays ours |
| AK2a document reader | kit | WRAP docling/pypdf | DEFERRED (order 59) | docling licence not in lead-fetch: UNVERIFIED |
| AK4a eval gates | kit | WRAP DeepEval or Langfuse scoring (MIT core); promptfoo as alternative | DEFERRED (order 59) | release gate stays ours; "promptfoo bought by OpenAI" is UNVERIFIED (scan-1) |
| AK0 | kit | n/a | DEFERRED (order 59), not "dropped" | plan-v4's "dropped" was a scan recommendation, not a lead decision |
| JG-3 | Jagrat | n/a | PAUSED (A15 note) | |
| P0t | v1 | KEEP-CODE | ticket rev 1 DRAFT; follow-up PR 83 open | plan-v4's "shipped" is UNVERIFIED |
| Channel template packs (n8n, Make, Activepieces) | kit, after AK-G2-b | CUT-TO-CONFIG+GLUE (the pack is built as exported flows plus thin glue; nothing is cut) | built only for a tool a client has chosen (order 57.2 DEMAND; owner decision 3 kept: nothing that connects is removed) | n8n first when a client picks it |
| Portal screen | later | DROP as a default; client's own tool reads a read-only role | OWNER-OPEN per client | optional Appsmith (Apache-2.0) is ALSO per-user above 5 users (Business USD 15 per user per month, audit logs paid: scan-2, UNVERIFIED here), so it carries the same seat-price problem as decision 2; Port/Retool only if the client already has them |

## 6. Rung table (bible R448, preamble rule 20)
| Component | Need | Rung tried | Evidence (source, date) | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Ledger (AK-G2-a) | same delivery key never starts work twice, with no time limit | 3 (SQS FIFO, Cloud Tasks, Pub/Sub: paid managed services used as they are), 4 (pg-boss, Graphile, Procrastinate) | Addendum B and pass 4, `market-scan-2.md:860-870`, 2026-11-07; Workflows 3-30 days, `:242` | permanent keyed dedupe; receipt in one transaction; run row as commit point. Failing property: every tool found forgets the key after a window (Graphile replace mode can overwrite a payload, Addendum B) | KEEP-CODE |
| Claim, lease, retry (AK-G2-a) | one worker at a time per receipt, retry after a crash | 4 pg-boss, Graphile Worker (Node), Procrastinate (Python, DROP) | Addendum B, 2026-11-07; readiness V4-04 (Graphile locks a dead worker's job 4 h vs the ticket's stuck window; pg-boss deletes completed jobs after 7 days: from the report, UNVERIFIED here) | the lease in the same store and transaction as the ledger, in Python; R3 | KEEP-CODE |
| Door (AK-G2-b) | signed webhook in, empty replies | 1 n8n webhook node + a database | order 57 A, 2026-11-06: no n8n statement that a request is stored before reply | signature before parse, deny by default (4.2) | KEEP-CODE |
| Redactor detector (P5c) | find personal data and secrets before the model | 4 Presidio (MIT) | order 35, 2026-11-06: missed 13 of 30 hostile inputs; order 64 | fail-closed wrapper, put-back, our hostile-set coverage | KEEP-CODE (default pattern backend); Presidio optional alternative |
| Spend meter (P4b1) | never admit more than the cap | 3 LiteLLM key budget; 3 Cloudflare AI Gateway limit | ORDER 140, 2026-11-07: LiteLLM 1.108.0 admitted 2 calls at cap 1.50 / call 1.00 (one call over, by design); Addendum A: Cloudflare burst can exceed | reserve before, in exact decimal, zero overshoot | KEEP-CODE |
| Billing classes (P4b2) | a refused or never-sent call is not counted | 3 provider pages | Claude errors page, no billing statement (lead-fetch, 2026-11-07; one page only) | the release rule; UNVERIFIED as a property of all vendors | KEEP-CODE (evidence weak, verify at build start, R448) |
| Stop state (P2a) | agent cannot clear the stop; reset audited | 3 cloud kill switches | plan-v4 claim; no reproduction in this checkout: UNVERIFIED | separate reset credential (A14) | KEEP-CODE (UNVERIFIED-KEEP, order 68(5)) |
| Tenant isolation (AK1a/1c) | a tenant reads nothing of another | 3 Postgres row-level security FORCE | Postgres docs, not re-read here: UNVERIFIED | the negative tests and the tenant-from-config rule | CUT-TO-CONFIG+GLUE for the mechanism; KEEP-CODE for the tests; Postgres-only (OPEN) |
| Template packs | client tool sends signed webhooks and shows notices | 1 n8n, Make, Activepieces | vendor pages (lead-fetch, 2026-11-07); whether Make/Activepieces HTTP steps can compute an HMAC: UNVERIFIED | the contract tests (T5) | CUT-TO-CONFIG+GLUE |
| Portal screen | people see and act on items | 0 client's own tool; 1/3 Appsmith (Apache-2.0) | scan-2, date of scan; Appsmith seat price UNVERIFIED | read-only role, digest binding | CUT-TO-CONFIG+GLUE |
| CI checks P5b2/P5b5 | catch new unsafe sites | 3 ast-grep (MIT) | scan-2 "85-90%" (row not re-located: UNVERIFIED) | none beyond CI | KEEP-CODE as built until the owner decides (replacing working code needs his yes, R448) |
Rows for audit, signer, secrets, channel and executor kinds: not re-examined by A8 (UNCHANGED from plan-v3 s5); order 68(5) lists their tickets' KEEP-CODE rows as UNVERIFIED-KEEP, to be verified when each ticket is next touched.

## 7. Cost model the quote must show (per client; the client pays licences) (R6)
Rules: EUR and USD are never added together and never converted (no rate source chosen: OPEN); each currency is summed on its own line. A total is printed next to every unit price. Model tokens are NOT in these figures (they depend on the workload; priced separately from the official price page). "NOT READ" means do not quote.

### 7.1 Automation tool (choose one)
| Option | Per month | Per year | Executions or credits | Notes |
|---|---|---|---|---|
| n8n Cloud Starter | EUR 20 | EUR 240 | 2.5K executions a month | billed annually (Addendum A); team features on Cloud: NOT READ |
| n8n Cloud Pro | EUR 50 | EUR 600 | 10K executions a month | billed annually; team features: NOT READ |
| n8n self-hosted Community | EUR 0 licence | EUR 0 licence + hosting (NOT PRICED) | no cap stated | lacks the ten features listed in section 3 (no credential sharing, no SSO, no Git, no environments ...). plan-v4's "one-person team only" was an inference and is removed |
| n8n self-hosted Business | EUR 667 | EUR 8,004 | 40K executions per Addendum A (whether this cap applies to self-hosted: UNVERIFIED) | SELF-HOSTED only (R6); plus hosting (NOT PRICED). Said aloud: EUR 8,004 a year is more than the USD 3,600 a year for 10 Port seats that the owner called too much (decision 2); different currencies, no conversion |
| Make | NOT READ | NOT READ | free plan 1,000 credits a month | UNREAD; do not quote until read; quote must name an exit plan (R447) |
| Activepieces Plus (cloud) | USD 20 | USD 240 | not read | alternative, not a default; self-hosted MIT core priced as hosting only |

Volume check (R6): the reference small client in `market-scan-2.md:267` has about 3,000 inbound messages and 300 approvals a month. At one execution each that is at least 3,300 executions a month, above Cloud Starter's 2,500; at two or more executions per message (design F16 estimate, UNVERIFIED) it is at least 6,300, which fits Pro's 10,000. So Starter does not fit that client; what n8n charges above the cap: NOT READ.

### 7.2 Our part, in the client's account
| Item | Per month | Per year | Notes |
|---|---|---|---|
| Door runtime: Cloudflare Workers Paid minimum | USD 5 | USD 60 | VERIFIED-SRC in scan-2 (`:242`). It buys neither Postgres nor a Python runtime, so it is NOT the full door stack |
| Postgres hosting (needed by the ledger, section 4.1) | NOT PRICED | NOT PRICED | no Postgres price page read in this checkout: UNVERIFIED. Must be read before a quote |
| Presidio container (only if the client wants the optional backend) | NOT PRICED | NOT PRICED | UNVERIFIED |
The real door stack (Python runtime + Postgres) and its price: UNVERIFIED; plan-v4's "about USD 5-10, USD 60-120 a year" is withdrawn.

### 7.3 Yearly totals per tier (known parts only)
| Tier | EUR per year | USD per year | Not included |
|---|---|---|---|
| n8n Cloud Starter + door minimum | 240 | 60 | Postgres, Python runtime, tokens, execution overage; does not fit the reference volume |
| n8n Cloud Pro + door minimum | 600 | 60 | Postgres, Python runtime, tokens |
| n8n self-hosted Community + door minimum | 0 | 60 | n8n hosting, Postgres, tokens; missing team features |
| n8n self-hosted Business + door minimum | 8,004 | 60 | n8n hosting, Postgres, tokens |
| Activepieces Plus + door minimum | 0 | 300 | Postgres, tokens |
| Make + door minimum | NOT READ | 60 + NOT READ | everything Make costs |
Worked example: a client on n8n Cloud Pro pays EUR 600 and at least USD 60 a year for the parts priced here, plus Postgres and model tokens, which are not priced yet.

### 7.4 Seat-priced tools (shown only when the client asked for that tool)
| Tool | Unit price | Example total per year | Marker |
|---|---|---|---|
| Port | USD 30 per seat per month; free up to 5 seats (Addendum A) | 10 seats: USD 3,600 if all 10 are billed; USD 1,800 if the first 5 stay free | seat billing above 5 NOT READ |
| Retool Business | USD 50-65 per builder per month (annual vs monthly rate) | USD 600-780 per builder | Addendum A |
| Langfuse audit logs (Enterprise) | USD 2,499 a month | USD 29,988 | plan-v4 mixed the self-host licence key with the Cloud tier (Z12): UNVERIFIED which applies |
| Appsmith Business | USD 15 per user per month | 10 users: USD 1,800 | scan-2 per reviewers, not read here: UNVERIFIED |

## 8. Tests that decide open points (made-up data, no real keys, no real money)

### T1 spend cap: our own meter, 50 parallel (R7; ORDER 140)
- Owner: P4b1 (its evidence set). Where: test file on a draft branch (STANDING-ORDERS 6d). Not an owner gate; P4b1 work does not wait for it.
- Setup: one cap C and a worst-case reservation W per call, both integer micro-dollars inside the meter (A9 B1). 50 callers start at the same moment (a barrier), each reserves W, then calls a stub provider that sleeps, then settles. Run on the memory store and on Postgres (the P4d contract suite).
- Pass: the number of admitted calls is at most floor(C / W); the sum of reservations never exceeds C at any moment; final spend at most C (overshoot zero, as plan-v3 s8). With C = 1,500,000 (USD 1.50) and W = 1,000,000 (USD 1.00): at most 1 admitted. Repeat with C = 50 x W (all 50 admitted) and C = 49 x W + W - 1 (49 admitted).
- Adds to, does not replace, the v3 s8 8-process Postgres race (V7).
- Comparison fact (the lead's run, ORDER 140, 2026-11-07, laptop): LiteLLM 1.108.0 official image main-stable, sealed network, stub provider, key cap USD 1.50, call cost USD 1.00. Sequential 10 calls: 2 admitted, overshoot USD 0.50 = one call, by design (check before, spend after). 50 parallel with a 2 s stub: 2 admitted, final spend USD 2.00. Slow-provider run (25 s stub): PENDING, so the slow case is UNVERIFIED. The raw file `egm/hadavin-sdk/core-complete/captest-1.md` is not in this checkout: UNVERIFIED here.
- Earlier fact (order 35, 2026-11-06, LiteLLM 1.108.1): 20 concurrent calls, 1 admitted, 19 refused, no overshoot; odd "Current cost" figures in refusal messages not explained; several workers and streaming not tested.
- The cloud session runs no LiteLLM code (supply-chain risk, section 3). The LiteLLM half is done by the lead and is a comparison, not a gate.

### T2 ledger replay (R10)
- Owner: AK-G2-a. Where: test file on a draft branch (STANDING-ORDERS 6d), written against the ticket's store methods.
- Layer: the ledger directly (`Inbox.receive` / `receive_inbound`), with an injected fake clock. The HTTP door and the signature are NOT in this test.
- Steps: receive delivery D (key K, body B) at time t0. Replay the same K and B at t0 + 6 minutes, t0 + 25 hours, t0 + 31 days. Each replay must return `duplicate`; there is exactly one receipt row for K and at most one run row for `run_id_for(K, generation)`. A replay with the same K and a different body returns `conflict` (409 at the door).
- Why these delays: each is just past a window named in section 3: SQS FIFO 5 minutes, Cloud Tasks 24 hours, Cloudflare Workflows up to 30 days (my reading of plan-v4's choice; plan-v4 gave no reason).
- Crash points (named, not random; V4-23): stop the process (a) before the receipt commits, (b) after the receipt commits, (c) after the run row is written, (d) after the 202 answer. After restart and a replay, one run row per key.
- "Forever" cannot be proved by three samples. A schema check adds: no expiry column and no job that deletes receipt rows by age (only `purge_inbound_bodies` deletes bodies). Whether the ticket deletes receipt rows anywhere: UNVERIFIED (section 4.3).
- T2b, separate (R10): the signature time window. A replay with the OLD signature after the window is refused 401 before the ledger (`hmac_v0`); the same message re-signed with a fresh timestamp (forwarder contract, line 195) reaches the ledger and returns `duplicate`. T2b belongs to AK-G2-b.

### T3 mask failure (P5c)
Force the detector to raise; assert zero provider calls.

### T4 stop (P2a)
The agent role tries to clear the stop; assert the denial and an audit row.

### T5 door contract per tool (template packs, after AK-G2-b)
- Gating test (offline, in CI, which has no internet, plan-v3 rule 9(d)): recorded requests in each tool's shape, signed, replayed, out of order (a later message before an earlier one) and malformed, sent to the door; assert no loss after 202 and no second run.
- Manual end-to-end per tool, outside CI: n8n in a local container; Make cannot be self-hosted, so it needs a real account, network and credits, which the "no real keys" rule forbids without the owner's yes (OPEN); Activepieces in a local container (licence policy for running it: UNVERIFIED).
- Build a pack, and run its test, only for a tool a client has chosen (order 57.2).

## 9. Order of work (no estimates: R12, plan-v3 s10)
1. Now (cloud, in parallel): finish and verify the open chain: P1b batch and evidence (PR 70), PR 63, PR 66, PR 72, PR 73, PR 80, PR 83, PR 85, PR 86 (STANDING-ORDERS 6a). The laptop runs evidence for pushed heads; an unchanged head is not run twice; the lead still re-runs at the merge commit as plan-v3 s3 says (V6).
2. Read-only, in parallel: EGM round 2 of this plan (STANDING-ORDERS 6b).
3. Test files on a draft branch: T1 and T2 (STANDING-ORDERS 6d). T3 lives with P5c, T4 with P2a.
4. After the open chain merges AND a lead order lifts the deferral (R9): AK-G2-a (with T2), AK-G2-b (with T2b). Gates before build: ticket rev 3 with its build notes, a build-start review, and the UNVERIFIED-KEEP rows verified (order 68(5)).
5. Then a template pack only for a tool a client has chosen (T5). AK-G15, AK-G1, AK-G16 stay DEFERRED until the owner's yes.
No calendar total and no agent-time figure until the open chain's merge order is clear.

## 10. EGM sequence for this plan and each package
- This plan: round 1 done (five reviewers, reports in `reviews/plan-v4-round1/`); resolve by the lead (`plan-v4-1-resolve-round1.md`); round 2 = three fresh reviewers (design, implementation-readiness, comprehension) on this file only. Stop rule: two clean rounds, or the third round freezes (at most 3).
- Each package: ticket draft, then plan review, then build, then a separate evidence runner, then a fresh result review with the `egm:*` skills, then the lead's resolve, then a drift report. The evidence runner and the reviewer are different agents.
- Security, money and redaction paths have no round cap for real defects (R448; order 6(b)); plan-v3's rule to escalate in writing after round 5 still applies to them (V5).

## 11. Open items
For the owner (defaults apply if no answer):
1. P5b2/P5b5 cut to ast-grep: default keep PR 85 as built (R11).
2. P6b1 convert to a config/doc check: default keep PR 86 as built (R11).
3. n8n licence reading (4.4): owner confirms or a lawyer checks before the first quote; default: no quote names n8n until then (R5).
4. Lifting the deferral of AK-G15, AK-G1, AK-G16, and the start of AK-G2: default stays deferred (R9).
5. Activepieces as a shown option (section 2): default keep it as an option, no pack.
6. Make end-to-end test needs a real Make account (T5): default no live Make run.
For the lead:
7. Amendment number: "A8" is already used in `amendments.md` (2026-11-05 entry).
8. OUT "governed action API" has no contract in AK-G2 rev 3, so R4 cannot be applied to it verbatim (4.3): write one, or drop OUT from the plan.
9. Must pilot and prod refuse a non-Postgres store for the ledger and tenant paths (4.1)?
10. Currency rule for quotes (section 7).
11. Who runs the daily `compare_ids` reconciliation, and how often (4.3).
12. Make plan prices: the lead reads them when a browser session is available (default: unquoted, R6).
13. P5b2 meaning: v3 step R3a vs plan-v4's "CI tables and pins" (C3).
14. R1 lists four verdict words; the rung table must use the R448 tokens (KEEP-CODE / CUT-TO-CONFIG+GLUE / CUT). A8 uses both, each in its own table (0.1). Confirm.

## 12. Change table (every round-1 finding)
Decision key: Rn = the lead's ruling n in the resolve file, applied here; AUTHOR = fix made by this plan's author with no ruling (round 2 must check it); OPEN = needs the lead (section 11). Report ids: S structural, C/V/A comprehension, Z zoom-out, V4- readiness, F design.

| Finding | Decision | Where applied in v4.1 |
|---|---|---|
| S1 no delta list, not filed as amendment | R1 | header; s1 |
| S2 ids differ from v3, no mapping | R1 | s0.4 |
| S3 HOLD row omits v3 cut rule | R11 + AUTHOR | s5 P5b2 row (plan-v3.md:149); s11.1 |
| S4 rung legend vs ladder | R1 + AUTHOR | s0.2 (R447 current; old 7-step order 54.1 named) |
| S5 table broken by paragraph | AUTHOR | s7 (each table separate) |
| S6 Cloud row includes Business | R6 | s7.1 split rows; s3 |
| S7 no totals, EUR/USD mixed | R6 | s7 rules, s7.3 |
| S8 unmarked figures | R6 + AUTHOR | s7 markers; "one-person team only" removed |
| S9 T1 gate vs default "no" | R7 | s1.3, s8 T1, s9 |
| S10 "about 1 day" estimate | R12 | s9 |
| S11 CUT-TO-CONFIG vs decision 3; verdict words | R1 + AUTHOR | s0.1 (nothing is cut), s5 packs row |
| S12 "settled" holds NOT PROVEN; no status column | AUTHOR | s3 renamed "found"; s5 Status column |
| S13 T3/T4 not in work order, no owner | AUTHOR | s8 owners; s9 step 3 |
| S14 evidence cells cite no file | AUTHOR | s5, s6 cite files; unlocated rows marked UNVERIFIED |
| S15 one cell, three items | AUTHOR | s5 separate AK0, JG-3, P0t rows |
| S16 bare source names | AUTHOR | s0.6 |
| S17 Activepieces added; fence tag; rung table order | AUTHOR + OPEN | s2 note, s11.5; `text` fence; rung table now s6 |
| C1 AK ids undefined | R1 | s0.3, s0.4 |
| C2 sub-ids not in v3 | R1 | s0.4 |
| C3 P5b2/P5b5 meaning differs | R11 + OPEN | s5, s11.13 |
| C4 PR numbers undefined | AUTHOR | s0.5 |
| C5 verdict words undefined | R1 | s0.1 |
| C6 rung scale | R1 | s0.2 |
| C7 evidence column without file | AUTHOR | s5, s6 |
| C8 door, kind, meter undefined | AUTHOR | s0.3 |
| C9 "same key, one effect, forever" | AUTHOR | s3 first bullet |
| C10 names inconsistent; resale claim | R5 + R6 + AUTHOR | s3, s7.1; resale claim withdrawn |
| C11 T1 gate disappears | R7 | s8 T1 (own meter always; LiteLLM comparison only) |
| C12 no totals, volume, overage | R6 | s7.1 volume check, s7.3 |
| C13 policy names only | AUTHOR | s0.6 (R445-R447), s2 |
| C14 sources without file | AUTHOR | s0.6 |
| C15 Presidio, put-back, mask | AUTHOR | s0.3 |
| C16 T2 delays unexplained | R10 + AUTHOR | s8 T2 "why these delays", fake clock |
| C17 EGM shorthand | AUTHOR | s10 |
| C18 "Author: lead (laptop)" | AUTHOR | s0.3 |
| V1 AK-G2 "v1.1 FIRST" without amendment | R1 + R9 | s1.2, s5, s9 |
| V2 estimate vs v3 s10 | R12 | s9 |
| V3 Presidio default | R8 | s1.1, s5 P5c row |
| V4 P2d meaning | R2 + AUTHOR | s0.4, s5 P2d row (v3 meaning) |
| V5 "no round cap" vs v3 round 5 | AUTHOR | s10 |
| V6 "never the same head twice" | AUTHOR | s9 step 1 |
| V7 T1 add or replace | R7 | s1.3, s8 T1 |
| V8 Activepieces fourth tool | AUTHOR + OPEN | s2 note, s11.5 |
| A1 T1 runs third-party code, version unnamed | R7 | s8 T1 (lead ran 1.108.0; cloud runs none) |
| Z1 P2d off by default | R2 | s5 |
| Z2 pg-boss/Graphile in core | R3 | s5, s6 |
| Z3 LiteLLM test already run | R7 | s8 T1 (order 35 and ORDER 140 cited) |
| Z4 missing rows | AUTHOR | s5 "rows not listed" line; s6 last line |
| Z5 v4 not an amendment | R1 + R9 | header, s1 |
| Z6 licence guard narrower | R5 | s4.4 |
| Z7 n8n rows | R6 | s7.1 |
| Z8 "legally resell" | AUTHOR | s3 Activepieces |
| Z9 hosting USD 5-10 | R6 | s7.2 |
| Z10 1.107.0 source; CUT-TO-CONFIG wording | AUTHOR | s3 (Addendum A, issue 47826); s0.1 |
| Z11 P1c "later" in v1 row; HOLD owner | AUTHOR + R11 | s5 P1c row, s11.1 |
| Z12 Port free seats; Langfuse tier | AUTHOR | s7.4 |
| Z13 worked total | R6 | s7.3 worked example |
| Z14 Make credit claim | R6 + AUTHOR | s3, s7.1 UNVERIFIED |
| Z15 Workflows, Queues, DBOS | AUTHOR | s3 (Workflows from file; Queues and DBOS UNVERIFIED) |
| V4-01 P2d off by default | R2 | s5 |
| V4-02 Presidio default | R8 | s5, s6 |
| V4-03 Presidio and look-alikes | AUTHOR | s3 UNVERIFIED |
| V4-04 Node libraries | R3 | s5, s6 |
| V4-05 estimate; list gates | R12 + AUTHOR | s9 steps 4-5 gates |
| V4-06 not filed as amendment; id mapping | R1 | header, s1, s0.4 |
| V4-07 approval in a no-code node | AUTHOR (follows R447, order 68(3)) | s4.4; AK-G15 DEFERRED (R9) |
| V4-08 which gate per path | AUTHOR + OPEN | s4.1 gates; OUT open s11.8 |
| V4-09 n8n licence | R5 | s4.4 |
| V4-10 feature list, Business split | R6 + AUTHOR | s3 (two features added), s7.1 |
| V4-11 Make credit | R6 | s3, s7.1 |
| V4-12 Activepieces legal claim | AUTHOR | s3 |
| V4-13 hosting ignores Postgres | R6 | s7.2 |
| V4-14 OTel status; 1.107.0 source | AUTHOR | s3 |
| V4-15 Cloud vs Business row | R6 | s7.1 |
| V4-16 missing rows | AUTHOR | s5 "rows not listed" line |
| V4-17 rung row per module; scale | R1 + AUTHOR | s0.2, s6 (11 rows; audit/signer/secrets not re-examined) |
| V4-18 RLS Postgres-only | AUTHOR + OPEN | s4.1, s6, s11.9 |
| V4-19 promptfoo, docling, Appsmith | AUTHOR | s5 AK2a/AK4a/portal rows, s7.4 |
| V4-20 no inbound contract | R4 | s4.2 |
| V4-21 no OUT contract | R4 cannot apply (no text) -> OPEN | s4.3, s11.8 |
| V4-22 "effect in one transaction"; retention | R4 + AUTHOR | s4.2 last line, s4.3 retention |
| V4-23 T2 clock, crash points | R10 + AUTHOR | s8 T2 |
| V4-24 T5 Make not self-hostable | AUTHOR + OPEN | s8 T5, s11.6 |
| V4-25 T1 version, units | R7 | s8 T1 (1.108.0, micro-dollars) |
| V4-26 T1 default effect | R7 | s8 T1 "not an owner gate" |
| F1 P2d off by default | R2 | s5 |
| F2 redactor default | R8 | s5, s6 |
| F3 door contract only named; OUT arrow | R4 + OPEN | s4.1 picture, s4.2, s4.3 |
| F4 31 days vs signature window; retention; clock | R10 + AUTHOR | s8 T2 and T2b, s4.3 |
| F5 T5 packs offline, speculative | AUTHOR | s8 T5, s5 packs row (order 57.2) |
| F6 loss before the door | R4 | s4.3 |
| F7 n8n Wait resume link | AUTHOR (follows R447, order 68(3)) | s4.4 |
| F8 pg-boss/Graphile | R3 | s5, s6 |
| F9 missing rows incl. AK1 | AUTHOR | s5 AK1 row and "rows not listed" line |
| F10 rung table per order 57.4/68 | AUTHOR | s6 (failing property named where a file gives one; others UNVERIFIED) |
| F11 AK-G15/G1/G16 deferred | R9 | s5, s9, s11.4 |
| F12 order 35 ignored; version | R7 | s5 P4b1 row, s8 T1 |
| F13 n8n licence unbacked | R5 | s4.4 (quote with URL in TOOLS.md not done: UNVERIFIED) |
| F14 Community gap consequence | R6 + AUTHOR | s3, s7.1 "said aloud" |
| F15 Make credit and cost | R6 | s3, s7.1 |
| F16 cost table not a quote model | R6 | s7 (tokens excluded and said) |
| F17 P4b1 gate | R7 | s1.3, s5, s8 |
| F18 unbacked claims (7) | AUTHOR | s3 each marked |
| F19 "about 1 day" | R12 | s9 |
| F20 RLS and SQLite | AUTHOR + OPEN | s4.1, s11.9 |
| F21 Appsmith per-user | AUTHOR | s5 portal row, s7.4 |
| F22 key custody and rotation | AUTHOR | s4.2 (ticket secrets field; revocation test UNVERIFIED) |
| F23 rung labels for paid services | AUTHOR | s6 ledger row ("paid managed services") |
| F24 promptfoo ownership | AUTHOR | s5 AK4a row |
| F25 v3 sections not listed | R1 | s1 |
| F26 P0t/AK0/JG-3 evidence | AUTHOR | s5 rows |
Count: 111 findings (structural 17, comprehension 18 + 8 + 1, zoom-out 15, readiness 26, design 26). R12 ruling (section 7 estimates) and R11 are applied; every ruling R1-R12 is used at least once.

## 13. UNVERIFIED (collected)
1. ORDER 140 cap test raw file `egm/hadavin-sdk/core-complete/captest-1.md`: not in this checkout; numbers taken from the order text.
2. Slow-provider (25 s stub) LiteLLM run: PENDING.
3. Owner order 11 wording: not in this copy of LEAD-ORDERS.
4. n8n licence clause text, URL and date; whether we may build or operate flows in the client's instance.
5. n8n: which paid plan unlocks which feature; Cloud Starter/Pro team features; whether 40K executions applies to self-hosted Business; overage pricing.
6. Make prices and "one action about one credit".
7. Activepieces `ee` boundary, Embed and resale terms.
8. Postgres hosting price; the real door stack price; Presidio container price.
9. Port seat billing above 5; Langfuse tier; Appsmith Business price.
10. Cloudflare Queues retention; DBOS exactly-once claim; Hatchet and pg-boss inferences; Graphile 4 h lock and pg-boss 7-day deletion figures.
11. Presidio and look-alike letters; cloud filters "irreversible"; OTel GenAI status; promptfoo ownership; docling licence.
12. "No vendor publishes billing of failed calls" as a general claim.
13. Scan figures "40-60%", "85-90%", "55-70%" not re-located in the scan files by me.
14. AK-G2: whether receipt rows are ever deleted; a key revocation test.
15. Merge state of PRs 63-86.
16. P1c phase (v1 or v1.1); P0t "shipped".
17. Whether Make or Activepieces HTTP steps can compute an HMAC signature.
