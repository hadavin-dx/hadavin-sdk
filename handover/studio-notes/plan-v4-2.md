# Plan v4.2 = AMENDMENT A18 to the frozen plan-v3 (client-chosen automation tool, market-aligned)

Status: DRAFT for EGM review round 3, the LAST round for this plan (order 143): the reviewers check that the lists in sections 12 and 13 are complete, then the plan freezes. Not binding until the lead records it in `studio-notes/amendments.md`.
Written: 2026-11-07 by the cloud session (author step only; the lead runs the fresh `egm:*` reviewers and the resolve step, EGM-GATE v1). I did not review my own work.
Number: order 142 says "use A9". `studio-notes/amendments.md` already holds A9 (2026-11-05, review-memos resolve) and A10 to A17. A18 is the first free amendment number (grep of `handover/` for an amendment called A18: none; the string "A18" exists only as finding ids in review files). This file uses A18. The lead confirms the number when recording (section 11, item L1).
One name: "A18" means this file (`studio-notes/plan-v4-2.md`). Its two drafts were plan-v4 (`studio-notes/plan-v4-market-aligned.md`) and plan v4.1 (`studio-notes/plan-v4-1.md`, which called itself "A8"); neither was ever recorded. Their withdrawn statements are only in section 14.
CODE-LAST v1: this plan proposes components; its rung table is section 6.

Built from (all read for this draft unless marked): `studio-notes/plan-v4-1.md` (458 lines), `studio-notes/plan-v4-1-resolve-round1.md` (the lead's 12 rulings), `studio-notes/plan-v4-round1-missed.md` (30 round-1 findings the resolve missed or only partly covered), `reviews/plan-v4-round2/` (readiness, design, comprehension; all three are CONDENSED copies; the full reviewer texts are in earlier transcripts that are NOT available to me), `LEAD-ORDERS.md` orders 11, 35, 57, 59, 64, 68, 70, 140, 142, 143, `STANDING-ORDERS.md`, `tickets/AK-G2.md`, `tickets/P4b1.md`, `tickets/P5b2.md`, `tickets/P5b5.md` (headings and named lines), `tickets/P6a.md` (lines 16, 29), `tickets/P5c.md` (lines 151, 704 and greps), `tickets/P4a.md` (BN-15, BN-16), `studio-notes/plan-v3.md` (sections 4, 6, 8), `studio-notes/amendments.md`, `reviews/market-scan-2.md` (lines 1-80, 155-300, 440-470, 845-900), `evidence/lead/lead-fetch-2026-11-07.md` (all 32 lines), `evidence/redactor-eval/README.md` and `lead-reading-1.md`, `questions-for-lead.md` q334-q336, the branch `origin/core/T1-T2-tests` at `e00a047` (test names and the parallel test body), `bible-extract-R447-R450.md`, `BRIEF-PREAMBLE.md`.

## 0. Read first: markers, letters, words

### 0.1 Marker legend (one meaning each)
| Marker | Meaning |
|---|---|
| VERIFIED (read) | I read it myself in the named file of this checkout. It is still only as good as that file. |
| VERIFIED-SRC | the named scan file says it read the vendor's own docs source (raw GitHub docs repo); I did not open the vendor page |
| lead-fetch | in `evidence/lead/lead-fetch-2026-11-07.md`: pages fetched by the lead's small fetch models on 2026-11-07; the file says parts marked S are model summaries |
| UNVERIFIED | nobody in a file I read has checked it, or I could not find the file; the file or fact I could not reach is named next to the marker |
| UNVERIFIED-KEEP | a KEEP-CODE verdict whose failing property is UNVERIFIED; it must be verified before that ticket's build start (R448, order 68(5)) |
| NOT READ | the page was fetched or searched but the fact was not visible; never guess it |
| NOT PRICED | no price source exists in this checkout; nothing with this marker may appear in a quote |
| PARTLY READ | the reader read only part of the source (the lead's round-1 resolve says it read the five round-1 reports only in part) |
| PENDING | a run that was started or planned and has no result yet |
| AUTHOR | a change I made with no ruling behind it; round 3 must check it |
| NEEDS-LEAD | the lead must decide; my recommendation is given; listed in section 11 |
| NEEDS-OWNER | only the owner can decide (money, scope, a promise to clients, his own rules); my recommendation is given; listed in section 11 |
| OWNER-OPEN | a row whose verdict waits for the owner; the stated default applies until he answers |
| CLIENT-EXCLUDED | a rung the client closed (R447), written with date and source; it counts as tried |
| CONTESTED | a review finding I did not apply; the reason is given and can be checked |

### 0.2 Letters and numbers
- **R<number>** = a bible rule only (for example R447, R448). Nothing else in this file starts with a bare R.
- **ruling N** = the lead's ruling N in `studio-notes/plan-v4-1-resolve-round1.md` (rulings 1 to 12; plan v4.1 called them R1 to R12).
- **order N** = order N in `LEAD-ORDERS.md`; "order 57.2" = order 57, item A.2.
- **amendment A<n>** = an entry in `studio-notes/amendments.md`; always written with the word "amendment" (for example "amendment A9 item F4").
- **step R1P, R3a, R5 ...** = a step of the diagnostics redesign in `studio-notes/design-v3.md`; always written with the word "step".
- **plan-v3 section N** = a section of `studio-notes/plan-v3.md`; "section N" alone = a section of this file.
- **T1 to T5** = the tests in section 8. **L, D, W, C, B rows** = test rows in `tickets/AK-G2.md`. **BN-n** = a build note at the end of a ticket.
- **round-1 S1, C1, V1, Z1, V4-01, F1** = round-1 finding ids (structural, comprehension, comprehension contradictions, zoom-out, readiness, design). **round-2 A1, M-A, comprehension 1** = round-2 ids (readiness, design, comprehension).
- **q<number>** = an entry in `questions-for-lead.md`.

### 0.3 The tool ladder and "rung"
"Rung" = one step of the tool ladder in R447 (owner order 2026-11-06; `bible-extract-R447-R450.md:3`). Before rung 1 comes a check of scope, budget, the client's size and willingness and the client's own tool; in a rung table the client's own tool is written **rung 0**.
1 no-code and low-code tools (n8n, Make and similar); 2 our core modules (already built and tested); 3 existing free or standard tools used as they are; 4 free libraries we test and build on; 5 our own new code, last, only for guarantee-class steps.
**guarantee-class** (R447 list): decisions, approval binding with a separate executor identity, redaction before the model, exact money and budget caps (reserve and settle), audit tamper-evidence, tenant isolation and least privilege, eval gates, no lost or double-applied message.
The repo rule file `.claude/rules/tool-ladder-before-code.md` still shows an older 7-step ladder (2026-11-03). R447 replaced it on 2026-11-06; A18 uses R447 only. Rung numbers stay in studio notes; text for the owner or a client says "a ready-made tool does it" or "our own code does it" (repo wording rule).

### 0.4 Verdict words: two vocabularies, one per table
Section 5 (module decisions) uses only these four words:
| Word | Meaning |
|---|---|
| ADOPT | use an outside tool, service or data as it is (configuration only) |
| WRAP | use an outside library, unmodified and pinned, behind our own wrapper module (R450(k)) |
| KEEP-CODE | our own code, because it carries a guarantee-class property no rung above gives |
| DROP | not built, because nobody needs it now (a frozen ticket stays; nothing is deleted) |

Section 6 (rung table) uses only the three R448 tokens, because the ticket check reads them:
| Token | Meaning |
|---|---|
| KEEP-CODE | same as above |
| CUT-TO-CONFIG+GLUE | a tool does it; we only configure it and connect it with thin glue. The part is still DELIVERED; only our own code is cut |
| CUT | the component is dropped; nobody needs it |

Mapping, so one row never has two verdicts: ADOPT or WRAP in section 5 = CUT-TO-CONFIG+GLUE in section 6; KEEP-CODE = KEEP-CODE; DROP = CUT.
Owner decision 3 ("do not cut anything that connects to n8n or Make", section 2) is about what is delivered. No row that connects to n8n or Make carries DROP or CUT in A18.
The scan files use the words ADOPT/WRAP/KEEP-CODE/DROP for their own verdicts; this file always writes those as "scan verdict: WRAP (line N)".
**glue** (thin glue) = under about 50 lines per component with no branching on business data (R447, order 68(2)); above that it is a component with its own row.

### 0.5 Status words (section 5, column "Status"; one meaning each)
| Status | Meaning |
|---|---|
| IN PR | an open pull request exists (section 0.8); work on it continues; merge state UNVERIFIED (not checked on GitHub) |
| TICKET FROZEN, NOT STARTED | the ticket text is frozen; no pull request yet; built in chain order (plan-v3 section 7) |
| ACTIVE TICKET | listed as active in the freeze list (order 59 item 4); may be built when its dependencies merge |
| DEFERRED | frozen ticket, not built. A deferral is LIFTED only by the OWNER (his yes); the lead only records the lift in an order (ruling 9; order 142(a)). The start condition that makes us ask him is in order 59 item 4: "a client or a chain item names the need" |
| PAUSED | stopped by the owner (amendment A15, PAUSED line; order 49) |
| UNCHANGED | the plan-v3 row stands; A18 did not re-examine it |

### 0.6 Words (defined before use; one meaning each)
- **the owner** = the studio owner. **the lead** = the main Claude session on the owner's laptop that coordinates, reviews through `egm:*` agents and merges (R450(j)). **the cloud session** = the Claude Code session in the cloud container that writes tickets, builds on branches and opens pull requests (it never merges). "Author: lead (laptop)" in plan-v4 meant the lead session.
- **EGM** = the studio's review process: fresh reviewer agents (`egm:*` types) read the work and the evidence; the lead resolves (R450(j)).
- **kind** = a swappable module with a neutral default and at least one alternative (R363, R450(j)), for example `llm`, `redactor`, `store`, `meter`, `secrets`, `signer`, `audit`, `channel` (the approval channel), `executor` (the single write path).
- **client's tool** = the automation tool the client chooses and owns (n8n self-hosted, n8n Cloud, Make, or Activepieces).
- **door** = the component that receives a signed web request from a client's tool and hands it to the ledger: `triggers/webhook.py` (AK-G2-b). Its **address** is the URL path `/inbound/<source>`. In v1 the door runs only in a demo-stage server (`serve`, ticket line 194); hosting it for pilot or prod is AK-G16 (DEFERRED, ticket line 101).
- **source** = one configured inbound sender (one flow of one client's tool), with its own tenant, readers, agent, principal and signing secret.
- **tenant** = the client organisation a record belongs to; every new record carries it (order 27 item 56: one deployment per client, plus a tenant field on every record).
- **readers** = the allowed readers of a record (AK1 `Readers`).
- **principal** = the identity a run acts for (`principals.yaml`); for a door it comes only from the source's config.
- **delivery id** = the sender's own id of a message, read from the signed body field `id_field`. **delivery key** = our keyed hash of tenant, source and delivery id (ticket line 156).
- **restored-hash key** = an existing secret of the deployment (`app.py:202-205`, required in pilot and prod, at least 16 bytes); the inbound key used for delivery keys and body hashes is derived from it (ticket line 153).
- **receipt** = one row in `inbound_receipts`: our record that a delivery arrived (key, keyed body hash, state, tries, run id). Not a payment receipt.
- **ledger** = the receipt table plus its store methods (AK-G2-a). It remembers every delivery key, so the same message never starts work twice.
- **claim / lease** = a worker takes ONE receipt for a limited time (the lease, `lease_s`); if it crashes, the lease runs out and another worker may take it again (ticket line 24).
- **run row** = the row in `runs` for one run; its id is derived from the delivery key and the **generation** (a counter raised only when a person reopens a message). The run row is the commit point (ticket line 107).
- **tick** = one idempotent pass of `runtime/tick.py` "run every 30-60 s by any scheduler"; a **tick step** (`TickStep`) is one task in that pass.
- **AK1 step** = one unit of work in the AK1 step contract (input record with tenant and readers, output record, result done / needs a person / refused).
- **outbound gate (AK1b)** = the one place every outbound text passes, masked first (AK1 ticket). **recipient gate** = AK-G22's gate for messages to people (no ticket yet).
- **forwarder** = a sender's flow (or a small relay) that signs and sends messages to the door.
- **hmac_v0** = our existing request-signing scheme (`approvals/hmac_v0.py`): HMAC-SHA256 over `v0:` + timestamp + `:` + body, timestamp at most 300 s from now (ticket line 76).
- **meter** = the spend meter (P4b1): **reserve** sets money aside before a model call equal to the worst case; **settle** replaces it with the real cost; **release** gives it all back (P4b1 ticket line 6). **micro-dollar** = one millionth of a US dollar, the integer unit inside the meter (amendment A9 item B1).
- **spend cap** = the most an agent may spend per run, day or month. Not the same as an n8n **execution allowance** (the number of workflow runs a plan includes per month) or a Make **credit** (Make's billing unit; what one credit buys: UNVERIFIED).
- **stop_state** = the stop switch the agent cannot clear itself, with an audited reset (P2a).
- **mask** = replace personal data or secrets with placeholders before any text reaches a model. **put-back** = our code (not the model) puts the real values back afterwards. **redactor** = the kind that masks; its **backend** = the detector used inside it.
- **hostile set** = the redactor test corpus in `evidence/redactor-eval/corpus.json`: 30 hostile inputs, 48 must-mask lines, 14 must-keep lines (README line 2).
- **Presidio** = Microsoft's open-source personal-data detector (MIT, Addendum A of `reviews/market-scan-2.md`).
- **execution** (n8n) = one run of one workflow.
- **Sustainable Use 1.0** = n8n's licence (fair-code, not open source). **ee folders** = the directories of n8n or Activepieces under a separate commercial licence.
- **Close** = a sales CRM product named in the scans; a "Close task" is a to-do item inside Close.
- **Jagrat** = the showcase demo of amendment A15 (PAUSED).
- **digest binding** = an approval is valid only for the exact content hash of the item approved.
- **ast-grep** = a free (MIT) code-pattern search tool usable in CI. **OTel** = OpenTelemetry, an open telemetry standard.
- **RLS FORCE** = Postgres row-level security with `FORCE ROW LEVEL SECURITY` (the rule also binds the table owner). **SKIP LOCKED** = a Postgres row-lock option that lets two workers never take the same row.
- **pg-boss, Graphile Worker** = Node.js job-queue libraries on Postgres; **Procrastinate** = a Python one (market-scan-2 pass 4).
- **template pack** = exported flows for one client tool plus thin glue, so the tool can call our door (section 5). Not the approval `channel` kind.
- **work item 9.N** = item N of the order of work (section 9). **build start** = the review that releases a frozen ticket to a builder. **owner gate** = a step that waits for the owner's answer.
- **dedupe window** = how long a product remembers a key. **signature age limit** = 300 s in `hmac_v0`. **lease time** = `lease_s`. (These replace the bare word "window".)
- **package** = one plan-v3 work package (P1a, P4b1 ...); **kit** = the Assembly Kit of amendment A10 (AK-* tickets).
- **start condition** = the named event that lets a deferred or outline item start (plan-v3 calls these "triggers"; A18 says "start condition" so that "trigger" means only the inbound trigger kind of AK-G2).

### 0.7 Package and ticket ids
| Id | What it is | Where defined |
|---|---|---|
| P1a, P1b | plan-v3 package P1 split in two pull requests: P1a moves the text-folding module out of PR #50 with its version; P1b closes gaps 1-5 and 7 | amendment A9 item F4; amendment A12 |
| P1c | redactor gaps found by the library comparison: base64 decoded view, whole internal host names | order 64; `tickets/P1c.md` |
| P2a | stop state | plan-v3 section 6; `tickets/P2a.md` |
| P2d | land PR #50's change to `guard/redact.py`; built as P2d-1, P2d-2 (refuse the whole text when a hidden-channel flag is found), P2d-2b | plan-v3 section 6; orders 11 and 19 E |
| P3a | migration rule (forward-only numbering, previous release reads the new schema) | plan-v3 section 6 |
| P4a | refuse instead of estimate, five-class usage, price tiers | plan-v3 section 6 |
| P4b1, P4b2 | plan-v3 P4b split: P4b1 meter kind; P4b2 billing classes and orphan sweep | amendment A9 item F2; amendment A11 |
| P4d | one store contract suite over memory and Postgres; money SQL (P4d-a, -b, -c) | amendments A11, A13, A14 |
| P5a | diagnostics redesign step R1: closed error codes, safe diagnostic text, hostile test corpus | plan-v3 section 6 |
| P5b1 | diagnostics redesign step R1P: provider error plumbing | `tickets/P5b1.md:1` |
| P5b2 | diagnostics redesign step R3a: "a checked-in table that classifies every place where the SDK builds a `ConfigError` (the error that stops the program at start-up); a generator that rebuilds that table by reading the source text; and a CI test that fails when a new place is not classified. Tests and one tool only. No change under `src/`." | `tickets/P5b2.md:15` (VERIFIED, read) |
| P5b5 | diagnostics redesign step R5: "pin that no old error-text path comes back, pin the one backstop, write the operator page, close the hostile corpus" | `tickets/P5b5.md:1` (VERIFIED, read) |
| P5c | redactor kind and masked model wrapper plus put-back | plan-v3 section 6 line 110 |
| P6a | client-profile check (demo-stage kinds refused in pilot and prod) | plan-v3 section 6; `tickets/P6a.md` |
| P6b1, P6b2 | plan-v3 P6b split: P6b1 no-training lock; P6b2 secret-boundary lint | amendment A9 item F6 |
| P0t | stage rename (stages are DEMO, PILOT, PROD only, R449) | `tickets/P0t.md` |
| AK1 | step contract (AK1a, AK1c tenant parts) and the one outbound gate (AK1b) | `tickets/AK1.md` revision 3 (AK-G2.md:15 calls it DRAFT) |
| AK-G2 | inbound trigger kind: ledger (AK-G2-a) and signed door (AK-G2-b); absorbs plan-v3 v1.1 row P7a | `tickets/AK-G2.md` revision 3 FROZEN, build notes BN-1 to BN-23 |
| AK-G15, AK-G1, AK-G16 | needs-a-person queue; chat agent with hand-off; deployment into the client's own cloud | `tickets/`; DEFERRED (order 57.2) |
| AK0, AK2a, AK4a | research note; document reader; joined-pipeline test harness | DEFERRED (order 59 item 4(a)) |
| JG-3 | chat-ops notifier for Jagrat | PAUSED (amendment A15) |
Open item 13 of plan v4.1 (what P5b2 means) is CLOSED: plan-v3's "step R3a" and the scan's "CI site tables and pins" (market-scan-2 line 31) name the same package; the ticket title above decides.

### 0.8 Pull requests named in this plan (the "open chain")
Heads move; this table copies the newest lines I read (q334 at 10:23Z, q336 at 10:28Z, 2026-11-07). Merge state: UNVERIFIED (no GitHub check here).
| PR | Package | Branch, head (source) |
|---|---|---|
| 63 | P1a | core/P1a; head not in q334: UNVERIFIED |
| 70 | P1b | PR head e3f946f; work branch core/P1b-fixwip d28d2bc (q336) |
| 66 | P4d-a1, first of the money chain | head da08ce2 (q334); NOT merged (q334) |
| 75, 76, 78, 79 | rest of the money chain (q334); which package each is: UNVERIFIED | f8b9056, e323ac7, 4a0976f, 8cc2021 |
| 77 | P2d-1 | 8b2b716 |
| 72 | P6a-1 | core/P6a 84bc5d5 pushed (q336) |
| 73 | P3a | d01c84b; batch on core/P3a-2-wip 7ed4c10 (q336) |
| 80 | P5b1 with P5a parts | b2a65ea (fix a6b664a on core/P5b1-wip) |
| 83 | P0t follow-up | e2d8971 (fix 9694b98 on fix/P0t-fix132-wip) |
| 85 | P5b2 | 0b54631 |
| 86 | P6b1 | b42383b |

### 0.9 Sources (paths under `handover/`)
- `reviews/market-scan-1.md`, `reviews/market-scan-2.md` (Addendum A at line 850: lead-verified facts; Addendum B and pass 4 from line 860). Scan-2 line 9 says plainly: "Cover % remains each agent's judgement, not a measurement. No candidate was installed or run." Every cover figure below inherits that.
- `evidence/lead/lead-fetch-2026-11-07.md` (marker lead-fetch). It names the pages it read but holds no URL per fact.
- `reviews/gateway-check-lead-reading-1.md` (order 35 run, LiteLLM 1.108.1). The raw evidence file is on the lead's side.
- ORDER 140 cap test raw file `egm/hadavin-sdk/core-complete/captest-1.md`: NOT in this checkout; numbers come from the order 140 text.
- Owner policies "client-chooses-tools-policy" and "options-first-then-decide" are in `.claude/rules/` and in bible R445-R447 (read in the rules folder; R445 and R446 texts themselves are not in the bible extract: UNVERIFIED wording).

## 1. What A18 changes in plan-v3
plan-v3 stays frozen; A18 changes only the items below; everything else in plan-v3 and amendments A1-A17 stands.
Changed:
1. plan-v3 section 5 (kinds), P5c row: the pattern redactor stays the default. A new rule for EVERY redactor backend, the default included: it must pass the hostile set (section 8, T3b) or the pilot and prod stages refuse it. Presidio may run only as an EXTRA layer after our backend, never instead of it (section 5, P5c row).
2. AK-G2 (which absorbs plan-v3 v1.1 row P7a): its door gains a duplicate-retry rule (section 4.4), which needs a new AK-G2 build note (NEEDS-LEAD L3). When AK-G2 starts is unchanged: amendment A10 says the kit starts after core v1 (P8c); ruling 9 adds that the open chain must have merged and the deferral must be lifted (owner's yes). A18 does not move AK-G2 earlier. P8a (demo re-pin) does not wait for AK-G2, because AK-G2 is not a v1 row (round-1 Z5).
3. plan-v3 section 6 P4b row and section 8 (b): P4b1's evidence gains T1 (section 8). T1 adds to the plan-v3 section 8 eight-process Postgres race (zero overshoot); it replaces nothing and is not an owner gate.
4. New rules for quotes and contract schedules: the n8n licence line (section 4.7), "reconciliation not delivered" (section 4.5) and the cost rules (section 7).
5. New, outline only: template packs for client tools (section 5), built only for a tool a client has chosen, and only for the IN direction until an OUT contract exists (section 4.5).
6. Answer to plan v4.1 open item 9 (store in pilot and prod): Postgres only, fail closed (section 4.2).

Not changed: P2d stays on in v1 as built (ruling 2); P5b2 and P6b1 stay as built until the owner decides, P5b5 stays DEFERRED (ruling 11, order 59); AK-G15, AK-G1, AK-G16 stay DEFERRED (ruling 9); no time estimates (ruling 12, plan-v3 section 9 line 194); AK-G2 claim/lease/retry stays our code as the ticket designs it (ruling 3).
Supersedes: plan-v4 and plan v4.1 entirely (neither was recorded).

## 2. Owner decisions that shape A18 (2026-11-07; as condensed by the lead in plan-v4 section 1, wording not re-checked against the owner's own message: UNVERIFIED)
1. The CLIENT chooses the automation tool: n8n self-hosted (licensed by the client), n8n Cloud, or Make. We do not choose for him (R445, R446; options-first rule).
2. Per-seat tools (Port, Retool and similar) add up to sums small clients will not pay; they are NOT a default part of any build.
3. Do not cut anything that connects to n8n or Make.
4. Plan every module, v1 and later, with EGM and the best quality and performance.
Activepieces is NOT in the owner's list. A18 shows it to a client only as an option, with no pack built until a client chooses it (NEEDS-OWNER O5).

## 3. What the research found
### 3.1 Read at a source (marker per line)
- Dedupe windows (lead-fetch): SQS FIFO "within the 5-minute deduplication interval"; Cloud Tasks task names remembered up to 24 h after deletion; Pub/Sub exactly-once is pull-only, one region, publish-side duplicates not covered; Google Workflows/Eventarc 24 h. Cloudflare Workflows instance id: duplicate refused only until retention 3, 7 or at most 30 days (VERIFIED-SRC, market-scan-2 section 6). Cloudflare Queues: at-least-once, no dedupe, Paid retention 4 days default, 14 at most (VERIFIED-SRC, market-scan-2 section 3 item 7). pg-boss: dedupe by policy or time slot, completed jobs deleted after `deleteAfterSeconds`, default 7 days; Graphile Worker: `job_key` only while pending, "no permanent job_key log", replace mode overwrites the payload; Procrastinate: `queueing_lock` only in `todo` (all from docs read on raw GitHub, market-scan-2 pass 4 table, 2026-11-07).
- Spend caps: Cloudflare AI Gateway docs text "a burst of concurrent requests can briefly exceed the limit" (VERIFIED-SRC, market-scan-2 section 5 item 3; Addendum A). LiteLLM 1.108.0 (lead's laptop run, order 140, 2026-11-07): checks before the call and records spend after, so it overshoots by up to one call (details in section 8, T1).
- Our own meter: main's `Limits` (check, then charge after) admitted 50 of 50 parallel callers at cap USD 2.00, call cost USD 1.00 (branch core/T1-T2-tests `e00a047`, `tests/test_t1_meter_parallel.py`, q335; order 142 item 3 accepts it as a real finding). That is the evidence P4b1's reserve/settle is needed.
- Failed-call billing: the Claude errors page lists codes (400, 401, 402 billing_error, 403, 404, 409, 413, 429, 500, 504, 529) with no billed or not-billed statement (lead-fetch). One page of one vendor.
- LiteLLM supply chain: 1.82.7 and 1.82.8 were malicious (GHSA-92x9-889m-jgmw; docs.litellm.ai/blog/security-update-march-2026, published 2026-03-24, lead-fetch). 1.107.0 compromised in October 2026: BerriAI/litellm issue 47826, from the lead's earlier fact-check batch (Addendum A); that issue page is NOT among the pages of lead-fetch, so its text is UNVERIFIED here.
- n8n: licence Sustainable Use 1.0; scan-2 quotes LICENSE.md (raw GitHub, read 2026-11-07): "use or modify the software only for your own internal business purposes or for non-commercial or personal use". Addendum A (lead): "Service to clients is NOT permitted; the client owns the account" (the clause the lead read is not quoted with URL in this checkout). n8n Community lacks (lead-fetch): custom variables, environments, external secrets, external binary storage, log streaming, multi-main, projects, SSO, sharing of workflows and credentials, Git version control; lead-fetch says these need "Business/Enterprise self-hosted", with no split per feature. Prices EUR 20 / 50 / 667 a month billed annually with 2.5K / 10K / 40K executions; EUR 667 is self-hosted only (lead-fetch; Addendum A).
- n8n duplicates: "you must build dedupe yourself" (community and vendor-adjacent snippets, market-scan-2 n8n section, marked S); n8n's own statement on whether a webhook request is stored before the reply: none found (order 57 A, the lead's own search, 2026-11-06).
- Make: free plan 1,000 credits a month; plan prices NOT READ (lead-fetch).
- Activepieces: MIT outside `packages/ee/` and `packages/server/api/src/app/ee` (LICENSE read, market-scan-2). Prices (lead-fetch): Free 1,000 credits and 5 users; Plus USD 20 a month, 10,000 credits; Team USD 200 a month; overage USD 0.007 a credit; Embed from USD 36k a year. Plus is the vendor's CLOUD plan; the MIT licence covers the self-hosted core.
- Redactors on our hostile set (`evidence/redactor-eval/lead-reading-1.md` lines 3-4, one run each, home advantage stated by the lead): hostile inputs FULL/PARTIAL/MISS, must-mask, must-keep KEPT/ALTERED:
  - our chokepoint `runmap.redact_text`: 24/0/6, 46/2/0, 14/0;
  - Presidio default: 14/3/13, 29/5/14, 7/7;
  - Presidio plus 4 custom recognisers and a normaliser: 23/2/5, 33/5/10, 7/7.
  Order 64: "no free library beats our redactor on our corpus". The run scripts `t_*.py` named in the README are NOT in this checkout (directory listing: README.md, corpus.json, lead-reading-1.md, score_common.py).
- Unicode folding, run by me today (python 3.13.18, `python3 -I -c` with `unicodedata.normalize('NFKC', ...)`): Cyrillic U+0430 stays U+0430, Greek omicron stays U+03BF, a zero-width space inside a word stays; fullwidth "a" becomes "a". So the standard-library normaliser alone does not fold look-alike letters or remove zero-width characters.
- Store kinds: `store/memory` is a demo-stage-only kind (`DEV_ONLY`, `backends/table.py:593-602`, per `tickets/P6a.md:16`), and demo-stage-only kinds are refused outside the demo stage (`config.py:350`, per `tickets/P6a.md:29`). I read the ticket text, not the code.
- Appsmith: Free up to 5 users; Business USD 15 per user per month; Enterprise USD 2,500 a month for 100 users (lead-fetch). Port: free up to 5 seats; USD 30 or 48 per seat per month billed annually (lead-fetch). Retool Business builder USD 50 (annual) / 65 (monthly) per month (lead-fetch). Langfuse Enterprise USD 2,499 a month (lead-fetch).
### 3.2 Not proven (UNVERIFIED, with what is missing)
- Hatchet "sliding TTL" (lead-fetch S) and pg-boss "no option named dedupe" (lead-fetch): read on pages, but whether they forget a key in our sense is the scan's inference.
- DBOS exactly-once claim: lead-fetch line 8 says DBOS "claims" it; retention UNVERIFIED (pass 4).
- "No vendor publishes billing of failed calls" as a claim about all vendors: one page read.
- Cloud filters (Bedrock, Azure, GCP) "irreversible, no put-back": from search snippets (market-scan-2 line 28).
- OTel GenAI `error.type` status: page moved, status NOT READ (lead-fetch).
- Whether Presidio folds look-alike letters: not tested on its own; the hostile-set run above includes look-alike rows inside the 30, but the per-row result is in the raw evidence on the lead's side, NOT in this checkout.
- Which n8n paid plan unlocks which missing feature; what n8n Cloud Starter and Pro include (sharing, projects): NOT READ.
- Whether n8n, Make and Activepieces can compute an HMAC signature and re-sign a webhook on each retry: UNKNOWN (section 4.4).
- Make "one action costs about one credit": not in lead-fetch.
- promptfoo ownership, docling licence: not in lead-fetch.

## 4. The connection, and the door contract
### 4.1 Picture (who calls whom)
```text
client's tool (n8n self-hosted | n8n Cloud | Make | Activepieces)   <- the client chooses, owns the account, pays the licence
   | (1) IN: the tool sends a signed web request to our door (AK-G2-b)
   v
[ door ] --> [ ledger: receipt, dedupe, claim/lease ] (AK-G2-a) --> AK1 step --> run (run row = commit point)
                                                                     |-- model call: masked first (P5c in v1; AK1b gate in the kit)
                                                                     |-- meter (P4b1): reserve before, settle after
                                                                     |-- stop_state (P2a): read before each step
                                                                     '-- audit (plan-v3 kinds)
   (2) OUT: our core asks the client's tool to act, or the tool calls our executor: NO CONTRACT EXISTS (section 4.5). Nothing is built for it.
```
The request the tool sends carries the text the client's own systems gave it. That text is NOT masked before it reaches our door; masking happens inside the run, before any model call. The rule "a no-code flow gets redacted data only" (R447) is about data our core SENDS to a flow; in v1 our core sends nothing to a flow (the door's replies are empty, section 4.3).
Gate per path: model calls in v1 pass the P5c masked wrapper and the P6a profile check; in the kit, AK1's one outbound gate (order 27 item 63). The door adds no outbound path (ticket line 103). OUT has no gate because it has no contract.

### 4.2 Store rule for pilot and prod (the plan's answer to plan v4.1 open item 9)
- The ledger, the claim/lease and the run rows need Postgres. In pilot and prod any other store is REFUSED at start-up (fail closed). This is already how the config works: `store/memory` is a demo-stage-only kind and such kinds are refused outside the demo stage (section 3.1, `tickets/P6a.md:16`, `:29`). A18 adds a negative test row to AK-G2-b's config rows: a pilot config with `store: memory` and an inbound source refuses to start (NEEDS-LEAD L3, same build note). SQLite (plan-v3 v1.1 row P7l) is never allowed for these paths.
- Contract wording for any Postgres store used by these paths: (a) the claim uses `FOR UPDATE SKIP LOCKED` (ticket line 163, already in the ticket); (b) a database that holds more than one tenant's rows must have RLS FORCE on every table with a tenant column. Today's design is one deployment per client (order 27 item 56), so (b) is a second wall, not the only one. No ticket I read carries (b) (grep of AK1, AK-G2 and P4d tickets for RLS: no match). NEEDS-LEAD L4: a build note on AK1 for (b), or a recorded "not needed while one deployment per client".

### 4.3 Inbound contract = AK-G2 ticket revision 3, quoted (ruling 4)
Where this plan and the ticket differ, the ticket wins, except the one change in section 4.4, which needs a build note.
- Line 102 (quoted): "**Signed inputs only, deny by default.** A webhook without a valid `hmac_v0` signature is refused with 401 before the body is parsed or anything is saved. The sender id is read ONLY from signed bytes (the body), and every source must name the field (`id_field` is required). The tenant, readers, agent and principal come ONLY from the source's config, never from the request. No two inbound sources, and no inbound source and the approval channel, may share a secret (row C7)."
- Line 103 (quoted, start): "**No outbound text added (order 27 item 63).** Every reply of the webhook has an EMPTY body (status code and, for 503, a `Retry-After` header only). AK-G2 sends nothing to anyone: no notification, no message, no model call of its own."
- Line 107 (quoted, start): "**Fail closed, and never lose.** A store error before the receipt commits answers 503 (the sender retries); after the commit, every failure leaves the receipt open or releases it, and the lease brings it back. **The run row is the commit point:** exactly one run per message per generation, because the run id is derived from the delivery key and the generation (INFORM I3), and once that run exists dispatch never calls the step again for it." "Never lose" covers only messages after our 202 reply (section 4.5).
- Line 162 (quoted, start): "`receive_inbound(...)`: ONE transaction. **Dedupe first:** if `rec.delivery_key` exists, compare `body_sha256`: equal gives `duplicate`, different gives `conflict`; nothing is written, even when the source is full." The transaction covers the receipt and its body only. The claim (line 163) and the run row (Interface 6) are separate statements in the SAME database; one run per message comes from the run id derived from the key, not from one shared transaction.
- Line 194, reply codes in order: 404 unknown path; 413 too large (before any HMAC work); 401 bad signature; 400 bad body or id; 202 new or duplicate; 409 id reuse; 503 busy (with `Retry-After`) or store error; 500 anything else; every reply body is empty.
- Line 195, forwarder contract (quoted): "Re-sign EVERY attempt with a fresh timestamp; a 401 after a retry means "re-sign and send again", not "give up". Send one JSON object per request, with unique keys. Put the message's id in `id_field` as a JSON string. Resend a retry byte for byte (a re-formatted retry is an id reuse, 409). On 503, wait `Retry-After` seconds and retry." Section 4.4 relaxes the first sentence for duplicates.
- Line 177 (quoted, end): "Nobody deletes receipts in v1 (V6)." Line 222, secrets: "One or two signing secrets per source, named in config, read once through the secrets kind; never logged". Row W15: with two secrets, either verifies; a third gives 401.

### 4.4 Change: a retry of an already received delivery does not need a fresh signature (order 142(b); NEEDS-LEAD L3)
Plain fact: it is UNKNOWN whether n8n, Make and Activepieces can compute an `hmac_v0` signature at all, and UNKNOWN whether their built-in retry re-computes it with a fresh timestamp on each attempt or re-sends the first request unchanged. No file in this checkout answers it (market-scan-2 says for n8n only "HMAC check only via custom code", marked as a judgement). T5 tries it per tool as a TRIAL; it is not a promise to any client.
Problem: under the ticket, a tool that re-sends its first signed request after 300 s gets 401, even though we already hold the message. The message is safe (we hold it), but the tool reports a failure and may alert or stop.
Rule A18 proposes (option A, recommended): when `hmac_v0.verify` fails ONLY because the timestamp is older than the signature age limit (the HMAC itself is valid for one of the source's configured secrets), the door may parse the signed body, compute the delivery key, and look it up:
- receipt exists, same keyed body hash: 202 (`duplicate`), nothing written;
- receipt exists, different body hash: 409, nothing written (no reuse row on this path);
- no receipt: 401, as today (a NEW message always needs a fresh signature);
- a timestamp too far in the FUTURE, a bad HMAC, an empty or unknown secret: 401, as today.
Other options considered: (B) accept an exact body match with no signature at all, by looking up the keyed body hash before parsing. Rejected: it parses or hashes unauthenticated input, needs a new index on the body hash (schema change in a frozen ticket), and tells anyone who holds a copy of a body (for example from a tool's execution log) whether we received it. (C) keep the ticket as is and refuse a pack for any tool that cannot re-sign. Kept as the fallback if the lead rejects A.
Consequences of option A, stated plainly:
- An attacker who recorded one complete signed request and replays it at any later time gets 202 and nothing else: no new receipt, no new run, no model call, no spend. Before A he got 401 after 300 s. What he learns: that this one message was received, which he could only test because he already holds the signed request.
- The same id with a DIFFERENT body and an old signature gets 409 and writes nothing. With a fresh valid signature it gets 409 and the ticket's reuse row (line 162, row W8), as today.
- Each replay costs us one HMAC check and one primary-key read; flood and rate limits stay AK-G16's (DEFERRED), so in v1 a replay flood is limited only by the demo-stage server. This is a real cost of A.
- After a signing secret is removed from config (rotation done, or revoked after a leak), old signed requests no longer verify, so old duplicates get 401 again. The doors and secrets are built once at start (ticket line 194), so a removal takes effect at the next start. Row: T5.
- "Never forgets" still holds only while the restored-hash key and the receipt rows are kept (section 4.6).
This changes the ticket's row W1 for one case ("a timestamp 301 s old: 401" stays true for a NEW message only) and sentence 1 of line 195. The build note must carry rows for all five cases above, plus a mutant that accepts an old timestamp for a new id.

### 4.5 What the guarantee does NOT cover
- **Before the door.** If the client's tool, or the system that feeds it, loses a message before our door answers 202, we never saw it and cannot recover it. n8n has published no statement on whether it stores a webhook request before replying (order 57 A).
- **Reconciliation is NOT delivered in v1.** `compare_ids` (ticket line 192) compares the sender's own ids with the ledger. The ticket says plainly that it has no caller in v1, and "nobody can compare ids or list waiting messages without code until V7 or AK-G15 ships". A tick step cannot call it, because the tick has no source of the sender's own id list (no tool exports one to us). So A18 names no runner and says: v1 does not check whether the client's tool lost messages before they reached us. Quote wording (every quote and contract schedule that uses the door): "We record and process each message your tool delivers to us exactly once. We do not check whether your tool lost messages before they reached us; that check is not part of this build." Bible R368 (owner hard rule) asks for "reconciliation against the source's own ids", so leaving it out needs the owner's yes: NEEDS-OWNER O3. Until he answers, the quote wording above applies and no quote promises reconciliation.
- **OUT direction.** AK-G2 revision 3 sends nothing (line 103), so there is no OUT text to copy (ruling 4 cannot apply). Nothing is built for OUT. Before anything is: a written and reviewed contract (request schema, who authenticates, an idempotency key tied to the ledger key, which identity holds the executor credential, a replay test with one effect). NEEDS-LEAD L2.
- **Effects in the client's systems.** An effect in a client's own CRM or payment system is not inside our database.

### 4.6 "Forever", retention and erasure
- "Never forgets" means: the receipt row and its keyed delivery key are never deleted in v1 (ticket line 177; the runtime role cannot delete either table; only the purge role deletes bodies, and only final ones, line 170). It holds ONLY while (a) the restored-hash key is unchanged (a new key gives every old message a new delivery key, so a replay looks new and starts a second run), and (b) the receipt rows survive (a database restored from a backup older than a receipt forgets it). T2 tests both and the plan asks for a start-up guard for (a): NEEDS-LEAD L3.
- Retention per data class is G18's (ticket line 101). Receipt rows grow by one per message with no end; size per row: NOT MEASURED.
- Erasure: a receipt holds a keyed hash of tenant, source and sender id, not text. Whether such a hash counts as personal data that a deletion request must reach: UNVERIFIED (not legal advice; R450(f)). G18 owns the answer.

### 4.7 Rules that stay outside any no-code flow
- Money, irreversible actions, masking, approval decisions, audit, the spend wall, retry, dead-letter and idempotency keys never live inside a no-code flow; the flow calls a core module (R447, order 68(3)).
- A no-code flow never holds approver or executor credentials (R447). A flow (n8n Wait node, a Make step, a Close task) may only NOTIFY a person. In v1 the only approval path is the approvals module's channel (`approvals/receiver.py`), and the approval channel's secret may not equal any door secret (ticket row C7), so a flow that holds its door secret cannot approve. The person-facing approval API with the person's own identity is AK-G15 and G14 (DEFERRED; G14 has no ticket); its negative test ("the flow's token cannot approve") belongs to them.
- Each flow (source) has its own signing secret (row C7). In n8n Community the secret sits in n8n's own credential store, because "external secrets" is a paid feature (lead-fetch); how n8n protects stored credentials: UNVERIFIED.
- Licence line for every quote and contract schedule (ruling 5), exact text: "The client runs n8n in the client's own account; Hadavin does not host or resell n8n. This line does not cover Hadavin building, changing or running flows inside the client's n8n for a fee; whether that is allowed is not confirmed yet." It is our reading of the Sustainable Use text, not legal advice ("not reviewed by counsel", R450(f)). The owner confirms or a lawyer checks before the first quote that names n8n (NEEDS-OWNER O1).

## 5. Module decisions (vocabulary: ADOPT / WRAP / KEEP-CODE / DROP)
Not re-examined by A18 (UNCHANGED from plan-v3 and its amendments): P0a, P0b, P0c, P0d, P0e, P4c, P5b3, P5b4 (DEFERRED, order 59), P6b2 (DEFERRED, order 59), P8a, P8b (DEFERRED), P8c, the plan-v3 v1.1 table (P2b to P7n), the secrets, signer, audit, channel and executor kinds (plan-v3 section 5, amendment A6), client invoicing (not a core module; scan-2 line 40), and the kit tickets AK2b, AK2c, AK2d, AK3, AK4b, AK5, AK7, AK8, AK-G14, AK-G22 and gap tickets G3, G9-G12, G18, G26. Order 68(5) lists the KEEP-CODE rows of those tickets as UNVERIFIED-KEEP, verified when each ticket is next touched.
"Scan verdict" = market-scan-2's verdict and line; an A18 verdict that differs says why.

| Package (ticket) | Phase | Verdict | Status | Scan verdict | Reason |
|---|---|---|---|---|---|
| P1a, P1b look-alike folding (`tickets/P1.md`) | v1 | KEEP-CODE | IN PR (63, 70) | WRAP, 40-60 (line 26) | the scan's candidates are the standard library and Unicode's confusables data, not a library to wrap; our code reads that data (order 59 item 6(5)) and adds the named views and fold key. Standard NFKC alone keeps Cyrillic and zero-width characters (section 3.1) |
| P1c redactor gaps (`tickets/P1c.md`) | v1 or v1.1: UNVERIFIED (the lead says) | KEEP-CODE | TICKET FROZEN, NOT STARTED; after P1b merges (order 70.1) | KEEP-CODE (line 26) | order 64: our chokepoint misses 6 of 30 hostile inputs |
| P2a stop state (`tickets/P2a.md`) | v1 | KEEP-CODE | TICKET FROZEN, NOT STARTED (P2a-1) | KEEP-CODE (line 33) | no cloud switch compared gives "the agent cannot clear it, a separate role resets it, audited" (5-15 cover) |
| P2d (`tickets/P2d.md`) | v1 | KEEP-CODE | IN PR (77 is P2d-1); on in v1, no extension (ruling 2) | KEEP-CODE if redaction is sold as a guarantee (line 27) | owner order 11 (read, line 24: the look-alike leak must be closed in core v1); order 19 E |
| P3a migration rule (`tickets/P3a.md`) | v1 | KEEP-CODE | IN PR (73) | WRAP (line 34) | no named migration tool was tested; built code is replaced only with evidence and the owner's yes (R448); row UNVERIFIED-KEEP |
| P4a usage and price tiers (`tickets/P4a.md`) | v1 | KEEP-CODE | TICKET FROZEN, NOT STARTED | WRAP LiteLLM budgets (line 36), read as "data only" (Addendum A) | refuse instead of estimate. Prices = a pinned, dated snapshot table with source URL and date per entry, never fetched at run time; LiteLLM's price file only as a cross-check (P4a BN-16) |
| P4b1 meter (`tickets/P4b1.md`) | v1 | KEEP-CODE | TICKET FROZEN, NOT STARTED; T1 added to its evidence | KEEP-CODE, 0 (line 37) | the two tools examined overshoot by up to one call; our own check-then-charge admitted 50 of 50 (section 3.1). Order 35 item 1 Options paragraph (client's own gateway as a v1.1 adapter row) stands |
| P4b2 billing classes (`tickets/P4b2.md`) | v1 | KEEP-CODE | TICKET FROZEN, NOT STARTED | KEEP-CODE (line 38) | no billing statement for failed calls on the one page read; UNVERIFIED-KEEP |
| P4d store contract (`tickets/P4d.md`) | v1 | KEEP-CODE | IN PR (66 and the money chain) | KEEP-CODE (line 34) | money SQL (amendment A11) |
| P5a closed error codes (`tickets/P5a.md`) | v1 | KEEP-CODE (diagnostic record, hostile corpus, old-writers test); its codes table, validation text and mutant file are planned as stdlib enum, pydantic and nothing (order 70.3) | IN PR (80, parts) | KEEP-CODE (line 29) | order 70.3: stdlib logging, structlog and traceback printed the message 4 of 4 |
| P5b1 provider error plumbing (`tickets/P5b1.md`) | v1 | KEEP-CODE | IN PR (80) | WRAP, 55-65 (line 30) | the scan's own "cannot guarantee" column: billing-safe retry classification; OTel names are used only as a pin (status NOT READ); UNVERIFIED-KEEP |
| P5b2 step R3a (`tickets/P5b2.md`) | v1 | KEEP-CODE | IN PR (85); OWNER-OPEN | ADOPT ast-grep, 85-90 (line 31) | the 85-90 is a judgement, not a count of need lines (R448 needs a count); built code is replaced only with the owner's yes. Cutting it also needs an amendment that rewrites P5c's Depends-on (plan-v3.md:149) |
| P5b5 step R5 (`tickets/P5b5.md`) | v1 | KEEP-CODE for the parts not moved; its rules 3 and 4 go to ruff banned-api (order 57 A.1) | DEFERRED (order 59 item 4(b)); OWNER-OPEN for the rest | ADOPT ast-grep (line 31) | not built. P5c's Depends-on names P5b5 (plan-v3.md:110) while P5b5 is DEFERRED: NEEDS-LEAD L5 |
| P5c redactor kind and wrapper (`tickets/P5c.md`) | v1 | KEEP-CODE (wrapper, put-back, pattern backend) | TICKET FROZEN, NOT STARTED | WRAP detector + KEEP-CODE wrapper (line 28) | detector WRAP overridden by order 64 (Presidio missed 13 of 30). Presidio = optional EXTRA layer that runs after our backend and can only mask more; never replaces it. Every backend passes the hostile set or is refused in pilot and prod (T3b). A Presidio layer needs the single-dependency check and a refusal-rate bound in the P5c ticket (NEEDS-LEAD L6) |
| P6a profile check (`tickets/P6a.md`) | v1 | KEEP-CODE | IN PR (72) | none specific (line 35) | demo-stage kinds refused in pilot and prod; UNVERIFIED-KEEP |
| P6b1 no-training lock (`tickets/P6b1.md`) | v1 | KEEP-CODE | IN PR (86); OWNER-OPEN | DROP as code, "agent's weakest verdict" (line 41) | no counted evidence; laptop run 10,446 passed on Python 3.12 and 3.13 (order 138 lines in LEAD-ORDERS, read); owner may turn it into a config or doc check |
| P0t stage rename (`tickets/P0t.md`) | v1 | KEEP-CODE | follow-up IN PR (83) | DROP "shipped" (line 53) | R449 owner rule; "shipped" means PR 67 merged: UNVERIFIED here |
| AK-G2-a ledger | kit | KEEP-CODE | TICKET FROZEN; DEFERRED start (A10, ruling 9) | KEEP-CODE (line 43) | see rung table |
| AK-G2-a claim, lease, retry | kit | KEEP-CODE | as above | Addendum B: WRAP pg-boss or Graphile Worker | ruling 3 overrides: Node libraries in a Python core, and a second job table beside our compare-and-set store (pass 4 key finding). pg-boss and Graphile Worker appear only as a named OUTLINE for a client who already runs one (start condition: the client asks) |
| AK-G2-b door | kit | KEEP-CODE | as above; plus section 4.4 | (no row) | see rung table; UNVERIFIED-KEEP |
| AK1b outbound gate | kit | KEEP-CODE | ACTIVE TICKET | KEEP-CODE, 0 (line 49) | no product gives one outbound gate |
| AK1 tenant isolation mechanism | kit | ADOPT (Postgres features: tenant column in every key; RLS FORCE where one database holds several tenants, section 4.2) | ACTIVE TICKET | WRAP, 85-90 (line 48) | a database feature used as it is, so ADOPT, not WRAP |
| AK1 tenant isolation tests | kit | KEEP-CODE | ACTIVE TICKET | (same line) | cross-tenant negative tests and canaries (R369) are ours |
| AK-G15 needs-a-person queue | kit | KEEP-CODE (store, digest binding, separate executor role) | DEFERRED | WRAP waits + KEEP-CODE store (line 44) | the client's tool may only notify (section 4.7) |
| AK-G1 hand-off lease | kit | KEEP-CODE | DEFERRED | KEEP-CODE for the lease (line 42) | no tool owns a conversation lease |
| AK-G16 deploy into the client's cloud | kit | ADOPT (Helm, Kustomize, OpenTofu, wrangler, CDK mechanics) | DEFERRED | ADOPT (line 45) | the five-part split stays ours |
| AK2a document reader | kit | WRAP docling or pypdf | DEFERRED | WRAP (line 50) | docling licence: UNVERIFIED |
| AK4a eval gates | kit | WRAP DeepEval or Langfuse scoring | DEFERRED | (line 51) | release gate ours; promptfoo ownership UNVERIFIED |
| AK0 research note | kit | n/a | DEFERRED (order 59) | DROP (line 47) | a lead decision deferred it; the scan's DROP is not a decision |
| JG-3 notifier | Jagrat | n/a | PAUSED | DROP (line 46) | |
| Template packs (n8n, Make, Activepieces) | kit, after AK-G2-b | ADOPT (the client's tool as it is, plus exported flows and glue under 50 lines) | built only for a tool a client has chosen (order 57.2), and only IN-direction until the OUT contract exists (NEEDS-LEAD L2) | (no row) | nothing that connects is removed (owner decision 3); T5 decides per tool whether the tool can sign |
| Portal screen | later | ADOPT (the client's own tool reads a read-only database role) | OWNER-OPEN per client | (no row) | a portal tool such as Appsmith is also priced per user above 5 users (section 7.4), so it has the same seat-price problem as owner decision 2; Port or Retool only if the client already has them |

## 6. Rung table (R448 tokens only)
Columns: rungs tried (0 = client's own tool, then 1 to 4; "0: none" = no client yet, nothing to exclude); failing property = the one property the higher rung fails; reproduction = failing test or doc quote with source and date, or UNVERIFIED with what blocks it. One verdict per row. A verdict resting on an UNVERIFIED cell must be verified before that ticket's build start (R448).
| Component | Need | Rungs tried | Failing property and reproduction | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Ledger (AK-G2-a) | the same delivery key never starts work twice, with no time limit | 0: none; 1 n8n (no dedupe store: "build dedupe yourself", S, scan-2); 2 dealdesk `inbox.py` promoted (ticket line 137); 3 SQS FIFO, Cloud Tasks, Pub/Sub, Cloudflare Queues/Workflows; 4 pg-boss, Graphile, Procrastinate | every product read forgets a key after its dedupe window or when the job ends. Doc quotes: SQS FIFO "within the 5-minute deduplication interval" (lead-fetch 2026-11-07; URL not recorded in the file); Graphile "no permanent job_key log" (pass 4, raw docs, 2026-11-07). And a queue product keeps its key in its own store, so it cannot share a database with our run row | receipt, lease and run row in the SAME database: the run id derived from the key makes a second run impossible (not one shared transaction, section 4.3) | KEEP-CODE |
| Claim, lease, retry (AK-G2-a) | one worker per receipt; retry after a crash | 0: none; 2 our tick compare-and-set (`tick.py:17`); 4 pg-boss (Node), Graphile (Node), Procrastinate (Python) | pg-boss and Graphile run on Node (a second runtime in a Python core) and keep a second job table; Procrastinate "stalled jobs stay stuck until YOUR periodic task retries them" (pass 4 table, 2026-11-07). No library was installed or run (scan-2 line 9) | the lease as a compare-and-set in the same store as the receipt | KEEP-CODE |
| Door (AK-G2-b) | signed request in, refused before parse, empty replies, retry of a received delivery accepted (4.4) | 0: none; 1 n8n webhook node; 3 Svix, Hookdeck: NOT searched (scan-2 line 11) | UNVERIFIED: no reproduction. Blocked by: a forced-kill test of n8n's webhook node or a read of the Svix and Hookdeck docs (order 57 A said "not worth the time now") | signature before parse, deny by default, the 4.4 rule | KEEP-CODE (UNVERIFIED-KEEP) |
| Redactor pattern backend (P5c) | find personal data and secrets before the model | 0: none; 2 our `runmap.redact_text`; 4 Presidio, GLiNER, LLM Guard, scrubadub, detect-secrets, gitleaks | Presidio default 14/3/13 on 30 hostile inputs, must-keep 7 of 14 altered (`evidence/redactor-eval/lead-reading-1.md:4`, run 2026-11-06); run scripts not in this checkout | coverage on our hostile set; ours also fails 6 of 30 today (T3b) | KEEP-CODE |
| Redactor wrapper and put-back (P5c) | mask before the model, no model call after a redactor error, restore in code | 3 Cloudflare DLP, Bedrock, Azure, GCP filters | Cloudflare DLP offers only Flag and Block (VERIFIED-SRC, `ai-gateway/features/dlp/set-up-dlp.mdx`, 2026-11-07, scan-2 section 5 item 1); "no put-back" for the others: UNVERIFIED (snippets) | fail closed and restore in our code | KEEP-CODE |
| Look-alike folding (P1a, P1b) | a folded copy of a known value cannot reach a model | 3 stdlib `unicodedata` NFKC; Unicode confusables data (used as input, order 59 item 6(5)) | NFKC keeps Cyrillic U+0430 and a zero-width space (my run, python 3.13.18, 2026-11-07, section 3.1) | named views and fold key on top of the data | KEEP-CODE |
| Hidden-channel refusal (P2d) | refuse the whole text when a folded known value survived masking | 4 guardrail classifiers (scan-2 line 27, "low, ~30") | UNVERIFIED against a tool (no tool run); the need is owner order 11 (the lead's run: look-alike copies leaked through core main) | the whole-text refusal | KEEP-CODE (UNVERIFIED-KEEP; built) |
| Migration rule (P3a) | forward-only numbering; the previous release reads the new schema or fails loudly | 3 "Postgres migration tools" (scan-2 line 34, none named) | UNVERIFIED: no tool named or tested | the downgrade-read test | KEEP-CODE (UNVERIFIED-KEEP; built) |
| Usage and prices (P4a) | refuse instead of estimate; dated exact prices | 3 LiteLLM budgets and price file | LiteLLM price file: float noise, no dates (P4a BN-15, `pip download litellm --no-deps`, 2026-11-06); proxy releases 1.82.7 and 1.82.8 malicious (lead-fetch) | refuse instead of estimate; pinned dated price table | KEEP-CODE |
| Spend meter (P4b1) | never admit more than the cap under concurrent calls | 3 LiteLLM key budget; 3 Cloudflare AI Gateway spend limit; 2 our `Limits` | LiteLLM 1.108.0: 50 parallel, cap USD 1.50, cost 1.00: 2 admitted, spend USD 2.00 (order 140, 2026-11-07); Cloudflare "a burst of concurrent requests can briefly exceed the limit" (VERIFIED-SRC, 2026-11-07); our `Limits`: 50 of 50 at cap 2.00 (`tests/test_t1_meter_parallel.py`, `e00a047`) | reserve before the call in exact integers | KEEP-CODE |
| Billing classes (P4b2) | a refused or never-sent call is not counted | 3 provider pages | Claude errors page: no billing statement (lead-fetch, 2026-11-07); one page only: UNVERIFIED for other vendors. Blocked by: reading each used provider's billing page at P4b2 build start | the release rule | KEEP-CODE (UNVERIFIED-KEEP) |
| Store contract (P4d) | one contract over memory and Postgres | 3 test suites (none named, scan-2 line 34) | UNVERIFIED: no tool named | the contract suite and money SQL | KEEP-CODE (UNVERIFIED-KEEP; built) |
| Stop state (P2a) | the agent cannot clear the stop; reset by a separate role, audited | 3 Cloudflare Durable Object + separate Worker, AWS IAM deny, Azure terminate | UNVERIFIED: compared on docs (scan-2 line 33, guarantee 5-15), not run. Blocked by: a run on one cloud needs a cloud account (owner's yes, no spend) | separate reset credential (amendment A14) | KEEP-CODE (UNVERIFIED-KEEP) |
| Diagnostic record (P5a) | no foreign text in a diagnostic | 3 stdlib logging, structlog, traceback | printed the message 4 of 4 (order 70.3, 2026-11-06) | the closed diagnostic record | KEEP-CODE |
| P5a codes table, validation text, mutant file | closed codes; safe validation text | 3 stdlib enum; pydantic | covers it (order 70.3, approved in principle) | nothing | CUT-TO-CONFIG+GLUE |
| Provider error plumbing (P5b1) | billing-safe retry classes | 3 OTel `error.type`; SDK exception classes | UNVERIFIED: OTel page NOT READ; the scan lists the classification as what it cannot give (line 30) | the class table | KEEP-CODE (UNVERIFIED-KEEP; built) |
| ConfigError site table (P5b2, step R3a) | classify every `ConfigError` site; CI fails on a new one | 3 ast-grep, Semgrep CE, Opengrep | UNVERIFIED: the 85-90 is a judgement; no count of need lines against ast-grep rules exists. Blocked by: that count (R448: the author counts, the lead settles) | the class judgement LITERAL/OPERATOR/FOREIGN (142 unproven-origin class judgements, LEAD-ORDERS.md lines 889-892) | KEEP-CODE (OWNER-OPEN) |
| P5b5 rules 3 and 4 | ban old error-text calls | 3 ruff banned-api | covers them (order 57 A.1, accepted) | nothing | CUT-TO-CONFIG+GLUE |
| Profile check (P6a) | demo-stage kinds refused in pilot and prod | 3 config validation (scan 1 only) | UNVERIFIED: no tool named | the cross-check list | KEEP-CODE (UNVERIFIED-KEEP; built) |
| No-training lock (P6b1) | the llm kind refuses a provider setting that allows training | 3 provider terms plus a config check | UNVERIFIED: scan-2 line 41 gives no cover figure | the lock in the llm kind | KEEP-CODE (OWNER-OPEN; built) |
| Outbound gate (AK1b) | masking before every outbound call | none found (scan-2 line 49) | UNVERIFIED: no reproduction | the one gate | KEEP-CODE (UNVERIFIED-KEEP) |
| Tenant isolation mechanism (AK1) | a tenant reads nothing of another | 3 Postgres tenant keys; RLS FORCE | Postgres docs not re-read here: UNVERIFIED | nothing | CUT-TO-CONFIG+GLUE |
| Tenant isolation tests (AK1) | prove the above | 3 none | no tool runs our cross-tenant canary tests (R369) | negative tests and canaries | KEEP-CODE |
| Template packs | the client's tool signs and sends to the door; shows notices | 0 the client's chosen tool; 1 n8n, Make, Activepieces | whether each tool can sign and re-sign: UNKNOWN (T5 trial) | the contract tests (T5) | CUT-TO-CONFIG+GLUE |
| Portal screen | people see items | 0 the client's own tool with a read-only role; 1/3 Appsmith (Apache-2.0) | Appsmith per-user price above 5 users (lead-fetch) | the read-only role and digest binding | CUT-TO-CONFIG+GLUE |
Rows for the audit, signer, secrets, channel and executor kinds: not re-examined (UNCHANGED, plan-v3 section 5); order 68(5) marks their KEEP-CODE rows UNVERIFIED-KEEP. Licence, version and date of each tool named above: in the scan lines cited; A18 adds no tool to a client build, so the R450(d) licence check is done when a ticket adds one.

## 7. Cost model the quote must show (per client; the client pays licences) (ruling 6)
Rules: EUR and USD are never added together, never converted and never compared with each other; each currency has its own line. A yearly figure is printed next to every monthly price (per year = per month x 12). Model tokens are excluded (priced separately from the official price page for the workload). Every table in this section is a LOWER BOUND, NOT A QUOTE. "NOT READ" and "NOT PRICED" lines may not be quoted.

### 7.1 Automation tool (the client chooses one)
| Option | Per month | Per year | Executions or credits | Notes |
|---|---|---|---|---|
| n8n Cloud Starter | EUR 20 | EUR 240 | 2,500 executions a month | billed annually (lead-fetch); team features on Cloud: NOT READ |
| n8n Cloud Pro | EUR 50 | EUR 600 | 10,000 executions a month | billed annually; team features: NOT READ |
| n8n self-hosted Community | EUR 0 licence | EUR 0 licence; hosting NOT PRICED | no cap stated | lacks the ten features listed in section 3.1 |
| n8n self-hosted Business | EUR 667 | EUR 8,004 | 40,000 per lead-fetch; whether that cap applies to self-hosted: UNVERIFIED | self-hosted only; hosting NOT PRICED |
| Make | NOT READ | NOT READ | free plan 1,000 credits a month | do not quote; the quote must name an exit plan (R447: SaaS with no self-host) |
| Activepieces Plus (cloud) | USD 20 | USD 240 | 10,000 credits a month (lead-fetch) | an option, not a default (section 2); self-hosted MIT core: hosting NOT PRICED |
Volume check: the reference small client (`market-scan-2.md:267`) has about 3,000 inbound messages and 300 approvals a month. At one execution each that is at least 3,300 executions a month, above Cloud Starter's 2,500. At two or more executions per message (an estimate from round-1 design F16, UNVERIFIED) it is at least 6,300, under Pro's 10,000. What n8n charges or does above the cap: NOT READ (scan-2 cites one aggregator saying over-limit runs are not queued on Starter and Pro: UNVERIFIED).

### 7.2 Our part, in the client's own cloud
| Item | Per month | Per year | Notes |
|---|---|---|---|
| Door stack: a Python runtime for `triggers/webhook.py` and the core, plus Postgres (section 4.2) | NOT PRICED | NOT PRICED | no price page for a Python host or a managed Postgres is in this checkout. In v1 the door has only a demo-stage server; pilot and prod hosting is AK-G16 (DEFERRED), NEEDS-OWNER O4 |
| Presidio extra layer (only if the client wants it) | NOT PRICED | NOT PRICED | container hosting |
Door stack: NOT PRICED.

### 7.3 Known licence lines per tier (LOWER BOUND, NOT A QUOTE; door stack: NOT PRICED in every row)
| Tier | EUR per year | USD per year | Not included |
|---|---|---|---|
| n8n Cloud Starter | 240 | none known | door stack (NOT PRICED), tokens, execution overage; too small for the reference volume |
| n8n Cloud Pro | 600 | none known | door stack (NOT PRICED), tokens |
| n8n self-hosted Community | 0 | none known | n8n hosting, door stack (both NOT PRICED), tokens; missing team features |
| n8n self-hosted Business | 8,004 | none known | n8n hosting, door stack (NOT PRICED), tokens |
| Activepieces Plus | none known | 240 | door stack (NOT PRICED), tokens |
| Make | NOT READ | NOT READ | everything |
No total is printed: the door stack is not priced, so any total would look like a price and is not one. Whether a small client pays for the door stack at all, or the build offers a no-door option (n8n alone, no guarantee-class step), is a commercial choice: NEEDS-OWNER O4.

### 7.4 Seat-priced tools (shown only when the client asked for that tool; per year = unit x seats x 12)
| Tool | Unit price | Example per year | Marker |
|---|---|---|---|
| Port | USD 30 per seat per month (Basic, annual); free up to 5 seats | 10 seats: USD 3,600 if all 10 are billed; USD 1,800 if the first 5 stay free | which applies: NOT READ |
| Retool Business | USD 50 (annual) or 65 (monthly) per builder per month | 1 builder: USD 600 or 780 | lead-fetch |
| Appsmith Business | USD 15 per user per month; free up to 5 users | 10 users: USD 1,800 if all 10 are billed; USD 900 if the first 5 stay free | which applies: NOT READ |
| Langfuse Enterprise (audit logs) | USD 2,499 per month | USD 29,988 | whether a self-hosted Enterprise licence key costs the same: UNVERIFIED |

## 8. Tests (made-up data, no real keys, no real money, no live model call)
Every test below that sits on a money, redaction or security path blocks its package's merge when it fails; none of them waits for the owner.

### T1 spend cap: our own meter, 50 at once (package P4b1, store package P4d)
- Where today: branch `core/T1-T2-tests` at `e00a047` (no pull request): `tests/test_t1_meter_cap.py`, `tests/test_t1_meter_parallel.py`, `tests/meter_support.py`, `tests/meter_mutants.py`. Those tests run 50 threads against main's `Limits` on the memory store; 4 fail on purpose (real finding, order 142 item 3). They stay as they are, failing, until P4b1 merges; then they must pass, never xfail.
- The exact rule, from the P4b1 ticket: a reservation of W is granted only when, for each set cap (run, day, month), settled spend plus open reservations plus W is at most the cap; exactly at the cap passes, one micro-dollar over is refused and writes nothing (P4b1 T2.3, T3 row P1). A refused reservation makes no provider call. When every granted hold stays open until all callers have answered, the number granted EQUALS floor(cap / W), exactly; "a meter that always refuses must fail" (P4b1 T5.1). Overshoot happens only when a call's real cost is higher than its reservation; then the settle books the full real cost, signals `overshoot`, and the next reservation is refused (P4b1 line 104).
- Weakness to fix in the branch, found while reading it: its parallel test asserts "at most floor", and another test is named "overshoot a non-multiple cap by less than one call", which accepts overshoot. When P4b1 lands, add equality and zero-overshoot assertions next to them (adding, not weakening; order 142 item 3 keeps the old tests).
- Cases (cap C and worst case W in integer micro-dollars):
  - T1.1 50 threads, memory store, barrier, all holds open until a second barrier: C = 2,000,000, W = 1,000,000: exactly 2 granted, 48 `OverBudget`, the stub provider called exactly 2 times, day counter 2,000,000 at the second barrier. Repeat with C = 50 x W (50 granted), C = 50 x W - 1 (49 granted), C = W - 1 (0 granted).
  - T1.2 settle below: after the second barrier each hold settles at half; the counter equals the sum of halves; then exactly floor((C - counter) / W) more reservations are granted.
  - T1.3 settle above: reserve 20, actual 2,000: books 2,000, overshoot 1,980, `on_overshoot` once, the next reservation refused (P4b1 T3 row P10).
  - T1.4 failed call: a call refused BEFORE it was sent releases its reservation (counter back to before). A call that was SENT and then failed is never released; it settles at the reserved worst case (P4b1 caller rule, line 48).
  - T1.5 crash between reserve and settle: one process killed with SIGKILL inside the hold after reserving: the reservation stays open at the worst case; another process settles it with `settle(id, None)` and the counter stays at the worst case (P4b1 T5.3).
  - T1.6 50 processes on Postgres: 50 OS processes, each with its own connection and `Meter`, a process barrier, C = 2,000,000, W = 1,000,000: exactly 2 granted. PostgreSQL 16 (binaries exist in the cloud box, q334); PostgreSQL 17 availability: UNVERIFIED. Needs at least 55 allowed connections. Runs alone (no parallel heavy job).
  - T1.7 mutants, each must be killed: a non-atomic check-then-reserve (read the counter, then write it in a second statement); `<=` turned into `<`; a meter that always refuses.
- How "never above the cap at any moment" is measured: with all holds open until the second barrier, the peak is at that barrier; assert counter <= C there and counter = granted x W.
- Adds to, and does not replace, the plan-v3 section 8 (b) eight-process Postgres race (P4b1 T5.1).
- LiteLLM comparison, not a gate: the lead's run (order 140, 2026-11-07, laptop, LiteLLM 1.108.0 official image `main-stable`, sealed network, stub provider, key cap USD 1.50, call cost USD 1.00): 10 calls one at a time, 2 admitted, overshoot USD 0.50; 50 parallel with a 2 s stub, 2 admitted, final spend USD 2.00. Slow-provider run (25 s stub): PENDING, on the lead's side, no date. The cloud session runs no LiteLLM code. Earlier (order 35, 2026-11-06, LiteLLM 1.108.1): 20 at once, 1 admitted, 19 refused, no overshoot seen; several workers and streaming not tested.

### T2 receipt ledger replay (package AK-G2-a; written and run WITH AK-G2-a, because the receipt ledger does not exist on main; the T2 on branch `core/T1-T2-tests` tests the SPEND totals ledger, not this one, q335)
- Layer: the store method `receive_inbound(rec, body, *, max_reuse, max_open)` and `Inbox.receive`; the door and signatures are NOT in T2. Clock: the fake clock passed to `Inbox(..., clock, monotonic, ...)` and the `now` argument of `claim_inbound` (ticket lines 163, 180).
- Stores: the memory store and Postgres 16 (17 if available, as ticket row L15).
- Replays, each offset from t0 (not added up): deliver D = (key K, body B) at t0: `new`. Replay K, B at t0 + 5 min + 1 s (SQS FIFO), t0 + 24 h + 1 min (Cloud Tasks), t0 + 14 d + 1 min (Cloudflare Queues Paid maximum), t0 + 30 d + 1 min (Cloudflare Workflows maximum): each `duplicate`; one receipt row; after a dispatch between replays, one run row for `run_id_for(K, 0)`.
- Conflict: at t0 + 30 d + 1 min, K with body B' (B with one byte changed): `conflict` (409 at the door); the first receipt is unchanged.
- Same-key race (Postgres, 8 connections, barrier): 8 receives of K, B: exactly one `new`, seven `duplicate`, one row. Mixed race: one with B, one with B': one `new`, one `conflict`.
- Crash points on the ledger layer: (a) store raises before the commit: no row; the retry gets `new`; (b) store raises after the write (outcome unknown to the caller): the retry gets `duplicate`; (c) crash after the run was created and before `finish_inbound`: after the lease, dispatch finds the run, the receipt ends `done`, one run (as ticket row D1). The crash "after the 202 reply" is a door case and moved to T5.
- Key cases: (d) same restored-hash key across a restart: `duplicate`. (e) a CHANGED key: the replay gets `new` and would start a second run. The test pins this hazard, and the plan asks for a start-up guard: the deployment stores a keyed fingerprint of the inbound key and refuses to start when it differs (NEEDS-LEAD L3; not in ticket revision 3). (f) restore from a backup taken before D: the replay gets `new` (pinned; runbook warning; not prevented).
- Hard schema criterion (Postgres): `inbound_receipts` has no column whose name contains `expir`, `ttl` or `delete`; `has_table_privilege` gives false for DELETE on `inbound_receipts` for the runtime role and the purge role; the immutability trigger exists; a source search finds no `DELETE FROM inbound_receipts` under `src/`.
- T2b, signature age limit (package AK-G2-b): limit 300 s (`hmac_v0.py:19`), HMAC-SHA256 over `v0:` + timestamp + `:` + body, secrets from config through the secrets kind, built from parts in tests. A fresh signature reaches the ledger. The same request at +301 s: 202 `duplicate` when the receipt exists, 401 when it does not (section 4.4).

### T3 mask failure (package P5c)
- T3a, each must end with ZERO provider calls and the run handed to a person: the detector raises; the detector exceeds its time limit (whether the P5c ticket names a time limit: NOT CHECKED, the builder adds a build note if not); put-back fails (a placeholder in the reply has no entry in the map, or the map is missing): the reply is held for a person, no placeholder text is delivered as if real, no second model call.
- The case "the detector returns nothing for a hostile text" cannot be seen at run time. It is caught by T3b (before release) and, for a known value, by P2d's whole-text refusal.
- T3b hostile-set gate, for EVERY redactor backend including our default: all 30 hostile inputs and all 48 must-mask lines FULL, all 14 must-keep lines KEPT, except rows the lead has written down as an accepted property (order 64 item 4: a bare number with no context is not masked). A backend that fails is refused in pilot and prod by the profile check (P6a cross-check list). Honest consequence: our own chokepoint scores 24 of 30 and 46 of 48 today; P1b closes 2 look-alike misses, P1c closes 3 base64 misses and the 2 partial host names (order 64); the sixth hostile miss is not named in the files I read (UNVERIFIED; perhaps the accepted bare-number row). Until those land, the pilot and prod stages would refuse our own default, which is the fail-closed direction.

### T4 stop (package P2a)
Each attempt is denied AND leaves an audit row: the agent's role calls the reset; the runtime role writes the stop table directly (UPDATE and DELETE); a config value or start-up flag that would clear the stop. Whether the P2a ticket rows already cover each: NOT CHECKED line by line; the builder maps each to a ticket row or adds a build note.

### T5 door contract per tool (template packs; after AK-G2-b; a TRIAL per tool, not a promise)
- Offline, in CI (CI has no internet, plan-v3 rule 9(d)): recorded requests in each tool's shape, sent to the door: signed, replayed, re-sent unchanged after 301 s (section 4.4), out of order, malformed; assert no loss after 202 and no second run. Door crash: kill the door after the receipt commits and before the reply; the sender's retry gets 202 `duplicate` (moved from T2).
- Key rotation and revocation row: two secrets configured, either verifies (row W15); after the old secret is removed and the door restarted, a request signed with it gets 401, also for a duplicate.
- Per-tool re-sign trial, manual, outside CI, recorded per tool: (i) can the tool compute HMAC-SHA256 over `v0:` + timestamp + `:` + body; (ii) on its own retry, does it send a fresh signature or the first one unchanged; (iii) is the retried body byte for byte the same. n8n: a local container (owner rule 5b allows local containers on made-up data). Activepieces: a local container of the MIT core with the `ee` parts not enabled (where the `ee` boundary lies in a running build: UNVERIFIED). Make: cannot be self-hosted; it needs a real account and network, which needs the owner's yes (NEEDS-OWNER O6). A tool that cannot sign gets no pack, or a forwarder, or the ticket's own-scheme outline (ticket line 209); this is decided per client.
- Build a pack, and run its trial, only for a tool a client has chosen (order 57.2).

## 9. Order of work (no time estimates: ruling 12, plan-v3 section 9)
1. Now, in parallel: finish and verify the open chain (section 0.8) per STANDING-ORDERS item 6a. Done for one pull request = the lead merges it after independent evidence and a fresh `egm:*` review that meets the stop rule in section 10. An unchanged head is not run twice; the lead still re-runs at the merge commit (plan-v3 section 3).
2. Now: EGM round 3 of A18 (last round; order 143).
3. T1 assertions added when P4b1-a lands (section 8); T1.6 needs P4d's Postgres methods.
4. After the open chain merges, core v1 is done (amendment A10), and the owner lifts the deferral: AK-G2-a with T2, then AK-G2-b with T2b and the section 4.4 build note. Gates before build start: ticket revision 3 with its build notes plus the new one, a build-start review, and the UNVERIFIED-KEEP rows of section 6 for AK-G2 verified.
5. Then a template pack only for a tool a client has chosen, IN-direction only until the OUT contract exists (T5).
AK-G15, AK-G1, AK-G16 stay DEFERRED until the owner's yes.

## 10. EGM for this plan and for each package (stated once)
- This plan: round 1 (five reviewers), the lead's resolve, round 2 (three reviewers), A18, round 3 = the last round (order 143); then it freezes, and anything left becomes a build-time fix for the ticket it touches.
- Each package: ticket, plan review, build, a separate evidence runner, a fresh result review by `egm:*` agents, the lead's resolve, a drift report. Money, redaction and security paths have no round cap for real defects (R448; order 6(b); owner decision 8); after round 5 such a package escalates to the lead in writing (plan-v3 section 4 item 3). Other packages: at most 2 rounds. The plan-level cap above does not apply to package reviews.

## 11. Open items, ranked by what they block ("needed by" = the work item or step that waits)
Each table is ranked: the item needed earliest comes first. The ids are labels only (O = owner, L = lead) and are cited elsewhere in this file.
For the owner (NEEDS-OWNER; the default applies until he answers):
| Rank | Id | Item | Needed by | Recommendation / default |
|---|---|---|---|---|
| 1 | O7 | P5b2 (built, PR 85): keep, or replace by ast-grep rules (a cut also rewrites P5c's Depends-on, plan-v3.md:149) | the PR 85 merge, then P5c build start | default: keep as built |
| 2 | O8 | P6b1 (built, PR 86): keep, or turn into a config or doc check | the PR 86 merge | default: keep as built |
| 3 | O1 | the licence line of section 4.7, and whether Hadavin may build or run flows inside a client's n8n for a fee | the first quote that names n8n | default: no quote names n8n until he or a lawyer confirms |
| 4 | O3 | reconciliation against the sender's own ids (R368) is not delivered in v1 (section 4.5) | the first quote that uses the door | recommend: accept for v1 with the 4.5 quote wording; start condition for building it: the first client whose tool can export its delivered ids |
| 5 | O4 | where the door runs in pilot and prod (AK-G16 DEFERRED), and whether a small client pays for the door stack at all | the first pilot that uses the door; any priced quote | recommend: lift AK-G16 only for the first named client; until then quotes say "door stack: NOT PRICED" |
| 6 | O5 | Activepieces shown as an option | the next options list for a client | default: shown, no pack |
| 7 | O9 | lift the deferral of AK-G2 (AK-G15, AK-G1, AK-G16 each separately) | work item 9.4 | default: stays deferred |
| 8 | O6 | a live Make run for T5 needs a real account | a Make pack | default: no live Make run |
(There is no O2: plan v4.1's two licence items are one item, O1.)
For the lead (NEEDS-LEAD):
| Rank | Id | Item | Needed by | Recommendation |
|---|---|---|---|---|
| 1 | L1 | amendment number: A18 (A9 is taken) | recording A18 | A18 |
| 2 | L9 | the two-vocabulary rule of section 0.4 (ruling 1 named four words; R448 needs its tokens in the rung table) | round 3 | confirm |
| 3 | L5 | P5c's Depends-on names P5b5 (plan-v3.md:110), but P5b5 is DEFERRED (order 59 item 4(b)); the P5c ticket's PENDING LEAD 12 asks to narrow it to "P2d-2, P5a, P5b3" (`tickets/P5c.md:704`); whether it was answered: UNVERIFIED | P5c build start (chain) | narrow it by a written amendment line |
| 4 | L7 | currency rule of section 7 (no conversion, no comparison) | the first quote | confirm |
| 5 | L8 | which wins on AK-G2's start: amendment A10 (kit after P8c) or ruling 9 (after the open chain) | work item 9.4 | A10 stands; the owner's lift may name an earlier start |
| 6 | L3 | AK-G2 build note: the duplicate-retry rule (4.4), the key-fingerprint start-up guard (4.6, T2 case e), the pilot `store: memory` refusal row (4.2) | AK-G2-a and -b build start | accept option A |
| 7 | L4 | RLS FORCE contract line in AK1, or a recorded "not needed while one deployment per client" (4.2) | AK1 build start | build note on AK1 |
| 8 | L6 | refusal-rate bound and single-dependency check for a Presidio extra layer, in the P5c ticket | a client asking for Presidio | add as a P5c build note |
| 9 | L2 | OUT contract: write one, or drop OUT; packs stay IN-only until then | any pack step that asks our core to act | write it only when a client needs OUT |
Closed here: plan v4.1 items 9 (Postgres only, 4.2), 11 (compare_ids: no runner, 4.5 and O3), 13 (P5b2 meaning, 0.7), 14 (two vocabularies, now L9).

## 12. The 30 round-1 findings the resolve missed or only partly covered (order 143; source `studio-notes/plan-v4-round1-missed.md`)
Outcome key: FIXED = fixed in A18 at the named place; CONTESTED = not applied, with a checkable reason; OWNER-OPEN = waits for the owner.
| Finding | Was | Outcome | Where / reason |
|---|---|---|---|
| S3 cut of P5b2-P5b5 needs the P5c Depends-on rewrite | not covered | FIXED | section 5 P5b2 row (plan-v3.md:149); section 11 O7, L5 |
| S5 paragraph glued to a table | not covered | FIXED | every table in A18 has a blank line or heading around it (section 7 split into 7.1-7.4) |
| S11 owner decision 3 vs CUT-TO-CONFIG+GLUE | partly | FIXED | section 0.4 (delivered, not removed; no connecting row is DROP or CUT); packs row ADOPT in section 5 |
| S12 settled vs unproven; status column | not covered | FIXED | section 3.1 vs 3.2; section 5 Status column with the legend in 0.5 |
| S13 T3 and T4 missing owners | not covered | FIXED | section 8 headings name P5c, P2a; section 9 |
| C4 PR numbers and "open chain" undefined | not covered | FIXED | section 0.8 |
| C7 evidence cells cite no file | not covered | FIXED | sections 5 and 6 cite file and line (market-scan-2 lines 26-53) |
| C8 door, kinds, meter, stop_state, audit undefined | not covered | FIXED | section 0.6 |
| C9 "same key, one effect, forever" unexplained | not covered | FIXED | section 0.6 (ledger), section 4.6 |
| C10 terms (execution, Sustainable Use, ee folders, Close task) and "legally resell" | partly | FIXED | section 0.6; resale claim withdrawn (section 14) |
| Z4 missing module rows | not covered | FIXED | section 5 first paragraph names every unchanged id (the finding allowed one line) |
| Z5 AK-G2 vs P8a order; list of what v4 supersedes | partly | FIXED | section 1 item 2 and "Supersedes"; L8 |
| Z8 "only tool an agency may legally resell" | not covered | FIXED | section 3.1 Activepieces line; section 14 |
| Z10 LiteLLM 1.107.0 source; decision 3 vs packs; n8n Wait node | not covered | FIXED | section 3.1 (issue 47826, not in lead-fetch, UNVERIFIED text); section 0.4; section 4.7 |
| V4-03 Presidio and look-alikes | not covered | FIXED | section 3.2 (UNVERIFIED; per-row result on the lead's side) |
| V4-07 approval identity; the flow's token cannot approve | not covered | FIXED for v1 | section 4.7 (row C7: door secret cannot equal the approval channel secret); the person-identity API test belongs to AK-G15/G14 (DEFERRED) |
| V4-08 one gate per path | not covered | FIXED | section 4.1 "Gate per path" |
| V4-12 Activepieces licence wording | not covered | FIXED | section 3.1 (MIT outside ee, LICENSE read; Plus is the cloud plan) |
| V4-16 a row per plan-v3 and kit id | not covered | CONTESTED | R448: "a table is at most one page"; rows for unchanged ids would restate plan-v3 with no new evidence. Section 5 names each id as UNCHANGED, which round-1 Z4 accepted |
| V4-17 rung row per non-KEEP-CODE module | partly | FIXED | section 6 rows for P5a parts, P5b5 rules, tenant mechanism, packs, portal |
| V4-18 RLS Postgres-only, no alternative | not covered | FIXED | section 4.2 (Postgres only in pilot and prod, fail closed; memory store demo-stage only; SQLite never) |
| V4-22 retention vs erasure | partly | FIXED | section 4.6 (erasure question UNVERIFIED, owned by G18) |
| V4-23 fake clock, crash points, no-expiry assertion | partly | FIXED | section 8 T2 |
| V4-24 T5: offline recorded test plus manual runs; Make | not covered | FIXED | section 8 T5; O6 |
| F5 per-tool test method; packs only for chosen tools | not covered | FIXED | section 8 T5; section 5 packs row |
| F7 approval outside the flow; n8n only notifies | not covered | FIXED | section 4.7 |
| F9 missing rows (AK1, audit, signer, secrets, P6b2, P0a, P8, invoicing, AK2*/AK3/AK4b) | not covered | MIXED: FIXED for AK1 (section 5, three rows; section 6, three rows); CONTESTED for the rest | same reason as V4-16; each other id, invoicing included, is named as UNCHANGED in section 5's first paragraph |
| F10 guarantee and reproduced failing property per KEEP-CODE row; licence, version, date; rung 0 | partly | FIXED | section 6 (each row: failing property with source and date, or UNVERIFIED with the blocker; rung 0 shown); licence and version stay in the scan lines cited (section 6 last line) |
| F18 seven unbacked claims | not covered | FIXED | section 3.2 lists each as UNVERIFIED or inference; Langfuse tier in 7.4 |
| F20 ledger and AK1c need Postgres; SQLite demo only; negative test | not covered | FIXED | section 4.2 and its negative test row (L3) |
Counts (one outcome per finding, 30 in all): FIXED 28, CONTESTED 1 (V4-16), MIXED 1 (F9: fixed for AK1, contested for the rest), OWNER-OPEN 0. V4-07 is FIXED for v1 only; its person-identity test waits for the DEFERRED AK-G15. Also from that file, findings marked "covered" with a gap: S7 currency rule (section 7, L7), C1 legend (section 0.7), F4 retention and clock (sections 4.6, 8 T2), F6 reconciliation (section 4.5, O3): all FIXED.

## 13. Round-2 findings and where A18 answers them (reports are condensed; the full texts are in earlier transcripts I could not read, so finding wording beyond the condensed lines is UNVERIFIED)
| Finding | Outcome | Where |
|---|---|---|
| Readiness A1 T1 has no file, branch, base | FIXED | section 8 T1 (branch, files, head) |
| A2 "at most floor" passes a meter that admits nothing | FIXED | T1 exact rule, T1.1 |
| A3 settle vs W; holds held at once | FIXED | T1.1-T1.4 |
| A4 concurrency model | FIXED | T1.1 threads on memory, T1.6 processes on Postgres |
| A5 measuring "never above the cap" | FIXED | T1 "How ... is measured" |
| A6 failure rule | FIXED | section 8 first line |
| A7 undefined labels; cap scope; slow run owner | FIXED | section 0.2, 0.6; T1 (run, day, month); slow run PENDING on the lead's side, no date (stated) |
| B1 crash point (d) after the 202 | FIXED | moved to T5 |
| B2 store API and clock injection | FIXED | T2 "Layer", "Clock" |
| B3 crash mechanism, end states, which store | FIXED | T2 crash points (a)-(c); stores |
| B4 dispatcher; generation; lease | FIXED | T2 (dispatch between replays; generation only on reopen, 0.6) |
| B5 replay schedule | FIXED | T2 offsets from t0, bodies B and B' |
| B6 schema check not testable; receipt deletion | FIXED | T2 hard schema criterion; ticket line 177 |
| B7 T2 before its code | FIXED | T2 heading: written and run with AK-G2-a |
| B8 T2b numbers | FIXED | T2b |
| B9 exact just-past values | FIXED | T2 replays |
| C1 T3/T4 stubs | FIXED | T3a, T3b, T4 |
| C2 T5 fixtures; HMAC unknown | FIXED | T5; section 4.4 |
| D1 section 5 not a work breakdown | CONTESTED | a plan names packages; each row now cites its ticket file, which holds files, tests and dependencies (ruling 1 made A18 an amendment, not a ticket) |
| D2 open-chain done criterion | FIXED | work item 9.1 |
| D3 Presidio not buildable | FIXED | section 5 P5c row: an extra layer only, gated by T3b and L6; no build planned until a client asks |
| D4 AK-G2 build gates vague | FIXED | work item 9.4 (section 6 AK-G2 rows named) |
| D5 open items that change code | FIXED | 4.2, 4.5, section 11 (P1c phase stays UNVERIFIED, the lead's) |
| D6 door runtime target | FIXED | section 0.6 door; 7.2; O4 |
| D7 stop-rule wording | FIXED | section 10 |
| D8 EUR vs USD comparison | FIXED | removed; section 7 rule |
| Design M-A reconciliation | FIXED (as NOT delivered) | section 4.5, O3 |
| M-B scan figures | FIXED | sections 5, 6 cite lines 19, 26, 31, 44 (and 27-53); override reasons in section 5 |
| M-C Workers fee as door floor | FIXED | section 7.2 ("door stack: NOT PRICED"); Workers removed |
| M-D Postgres refusal; RLS FORCE + SKIP LOCKED | FIXED | section 4.2 |
| M-E every backend passes the hostile set; Presidio extra layer | FIXED | T3b; section 5 P5c row |
| M-F rung table vs R448 | FIXED | section 6. One part CONTESTED: "ledger argument = one transaction shared by table, claim/lease and run row" is not what the ticket says (line 162: one transaction for receipt and body; claim and run row are separate statements). A18 writes the true argument: same database, run id derived from the key |
| M-G T1 cases and wording | FIXED | T1.1-T1.7; section 6 P4b1 row wording |
| M-H T2 cases; T3; T4 | FIXED | T2 (d)-(f), races, schema; T3; T4 |
| M-I forwarder re-sign | FIXED | section 4.4; T5 trial |
| M-J totals look quotable | FIXED | section 7.3 (no totals; "lower bound, not a quote"); O4 |
| M-K OUT contract gates packs | FIXED | section 5 packs row; L2 |
| Design extras: key custody and rotation; ruling names; title; price map; line 177; retention and erasure | FIXED | 4.7, T5; 0.2; section 8 title; P4a row; 4.3; 4.6 |
| Design nits: P5b2 = R3a; "marked UNVERIFIED" counted as fixed; item counts | FIXED | 0.7; section 12 says FIXED only where text changed; section 11 counts |
| Comprehension 1 letter R | FIXED | section 0.2 |
| Comprehension 2 P5b2/P5b5 | FIXED | section 0.7 titles; P5b5 DEFERRED everywhere; ast-grep in 0.6 |
| Comprehension 3 who lifts a deferral | FIXED | section 0.5 DEFERRED |
| Comprehension 4 mixed vocabulary; portal; CUT; DROP twice | FIXED | section 0.4; portal ADOPT = CUT-TO-CONFIG+GLUE; Procrastinate called "rejected" (no DROP); 0.4 decision-3 line |
| Comprehension majors: status words, legend, letter A, three names, history in body, terms before use, two ladders, "rung 3" in owner text, missing rows, gate/window/step/package/channel/trigger/cap, door as address, "verbatim" paraphrase, 4.1/4.3/4.4 contradictions, "forever", currency, "owner called too much", seat examples, defaults clash, stop rule | FIXED | 0.5; 0.1; 0.2; header "One name"; section 14; 0.6; 0.3; section 6 rows; 0.6; 4.3 marked "quoted"; 4.1 (raw input to the door), 4.5, 4.7; 4.6; section 7; the unsourced "owner called too much" sentence removed; 7.4 one formula; O1 default kept with reason; section 10 |
| Comprehension nits (section number for estimates, heading, PR table columns, two "chain" meanings, prose in cells, cover shares, word clashes, unglossed tools, omitted numbers, voice) | FIXED where text changed; "300 approvals" and "10,446 passed" are now in sections 7.1 and 5 | |
Counts (45 rows; several rows group findings, so this is not a count of single findings): FIXED 44 (one of them, M-F, has one CONTESTED part: "one transaction"), CONTESTED 1 (D1), OWNER-OPEN 0 (the owner choices these findings raise are in section 11).

## 14. History: plan-v4 and plan v4.1 statements withdrawn (kept here only)
- plan-v4: P2d "off by default" (withdrawn by ruling 2). Presidio as the default detector (ruling 8). pg-boss or Graphile Worker in the core (ruling 3). "BUILD NEXT: AK-G2" and "v1.1 FIRST" (ruling 9). "About 1 day of agent time" (ruling 12). T1 as an owner gate with default "no" (ruling 7). Cloudflare Workers "USD 5-10 a month, USD 60-120 a year" as the door cost. n8n "one-person team only" (an inference). Activepieces "the only automation tool an agency may legally resell" (a legal conclusion with no source; scan-2 line 536 is that scan's own summary). AK0 "dropped" (it is DEFERRED). P0t "shipped" (UNVERIFIED). "Effect in one transaction" (the ticket's claim is narrower, 4.3). An AK-G15 row that put the waiting screen in the client's tool. Status words FINISH, KEEP BUILT, HOLD.
- plan v4.1: called itself "A8" (taken). Used R1-R12 for rulings. Priced Cloudflare Workers Paid (USD 5 / 60) as the door's floor and printed totals with it. T1 pass rule "at most floor(C / W)". T2 crash point (d) "after the 202". Scan figures marked UNVERIFIED although they are at market-scan-2 lines 19, 26, 31, 44. "Whether the ticket deletes receipt rows: UNVERIFIED" (answered by ticket line 177). Compared EUR 8,004 with USD 3,600 aloud. P5b5 called both "as built" and DEFERRED. Portal DROP in one table and CUT-TO-CONFIG+GLUE in the other. Graphile 4 h and pg-boss 7 days marked UNVERIFIED (they are in the pass 4 table). Owner order 11 marked "not in this copy" (it is at LEAD-ORDERS.md line 24).

## 15. UNVERIFIED and NOT PRICED (collected)
1. Order 140 raw cap file `egm/hadavin-sdk/core-complete/captest-1.md`: not in this checkout; slow-provider run PENDING.
2. n8n licence clause read by the lead (URL and date); whether we may build or run flows in a client's n8n for a fee (O1).
3. n8n: paid feature split; Cloud Starter and Pro team features; 40K cap for self-hosted Business; overage behaviour; credential protection.
4. Make prices and credit meaning; whether n8n, Make, Activepieces can sign and re-sign (T5 trial).
5. Activepieces `ee` boundary in a running build.
6. Door stack price (Python host, Postgres), n8n hosting, Presidio container: NOT PRICED.
7. Port and Appsmith billing of the first 5 seats; Langfuse self-hosted Enterprise price.
8. Cloudflare Queues and Workflows URLs (docs source paths only); SQS quote URL; DBOS retention; Hatchet and pg-boss inferences.
9. Presidio per-row look-alike results; cloud filters "no put-back"; OTel status; promptfoo ownership; docling licence.
10. Failed-call billing beyond the Claude errors page.
11. Reproductions blocked: door (n8n forced-kill test), P2a cloud switches, P3a and P4d tools, P5b1 OTel, P5b2 count, P6a, P6b1, AK1b, tenant mechanism (Postgres docs).
12. Whether a keyed hash of a sender id is personal data under erasure rules (G18).
13. Merge state of every pull request in section 0.8; heads of PR 63; packages of PRs 75, 76, 78, 79.
14. P1c phase; P0t "shipped".
15. Whether the P5c ticket names a detector time limit; whether P2a rows cover all T4 attempts; whether the lead answered P5c PENDING LEAD 12.
16. PostgreSQL 17 availability for T1.6 and T2.
17. The sixth hostile miss of our chokepoint (order 64 names five).
18. Owner decision wording of section 2 (condensed by the lead); R445 and R446 full text.
19. Round-2 full reviewer texts (only condensed copies exist here).
