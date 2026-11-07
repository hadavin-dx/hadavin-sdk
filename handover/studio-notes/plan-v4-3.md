# Plan v4.3 = AMENDMENT A18 to the frozen plan-v3 (client-chosen automation tool, market-aligned)

## What this plan proposes (plain words, for a reader who has never seen the project) [AUTHOR]
1. Hadavin is a one-person studio that sells fixed-price AI automations. Every build starts from one shared code library, the **core**. An **agent** is the AI program that does one client job; a **run** is one attempt by an agent at one incoming message.
2. Many clients already use, or will choose, a ready-made automation tool (n8n, Make or Activepieces) to move data between their own systems. This plan says how the core works next to such a tool.
3. The client chooses the tool, owns its account and pays its licence. We never choose it for the client.
4. The tool only moves data and tells people that something is waiting. Everything that must never go wrong stays in our own tested code: limits on what AI calls may cost, hiding personal data before an AI model sees it, approvals, the audit record, keeping each client's data apart, and never losing or doubling a message.
5. The tool sends each message to one signed web address of ours, the **door**. The door stores the message once before it answers, so the same message never starts two runs.
6. For each part, the plan says whether a ready-made tool does it or our own code must, with the evidence (section 6); which tests prove each promise (section 8); which price lines a quote must show (section 7); and what the owner or the lead still has to decide (section 11).
7. Stages are **demo** (made-up data only), **pilot** (first real client data) and **prod** (live). **v1** is the first finished version of the core; the **kit** (Assembly Kit) is the set of later building blocks.
8. This plan changes no code by itself. Each part is built later through its own frozen ticket, after its own review.

## OWNER DECISIONS still open (order 145 item 3; the lead carries them, nobody decides them here) [AUTHOR]
- **O3 reconciliation.** Bible rule R368 asks us to compare the messages we received with the sender's own list of ids. v1 does NOT do this (section 4.5). Until the owner answers, no quote promises it, and the quote sentence of section 4.5 applies.
- **O4 where the door runs in pilot and prod.** In v1 the door runs only in a demo-stage server. Hosting it for pilot or prod is the deferred ticket AK-G16. Until the owner answers, no quote prices the door's hosting ("door stack: NOT PRICED").
- Eight more owner items (O1, O5-O11) and every lead item are in section 11.

## How to read this file (process notes, moved below the summary in v4.3) [AUTHOR]
- Status: v4.3 = the ONE final author pass of order 145. There is no review round 4; the lead reads it and freezes it (order 145 item 2). Not binding until the lead records it in `studio-notes/amendments.md` and writes a FROZEN line in `LEAD-ORDERS.md` (order 145 item 4).
- Written: 2026-11-07 by the cloud session, EGM step: author only (EGM-GATE v1, defined in 0.7). I did not review my own work.
- **Every change from v4.2 carries the marker AUTHOR.** A reader who wants to check only what changed searches this file for "AUTHOR"; the table in section 17 lists each change requested by order 145 and where it landed.
- Number: A18, CONFIRMED by order 145 item 1. Checked again for v4.3: `studio-notes/amendments.md` holds A1 to A17 (A9 line 15, A10 line 28, A11 line 30, A12 line 31, A13 line 33, A14 line 35, A15 line 37 and its PAUSED line 58, A16 line 60, A17 line 63) and no A18 (grep, 2026-11-07). [AUTHOR]
- One name: "A18" means this plan. Its drafts were plan-v4 (`studio-notes/plan-v4-market-aligned.md`), plan v4.1 (`studio-notes/plan-v4-1.md`, which called itself "A8") and plan v4.2 (`studio-notes/plan-v4-2.md`); none was recorded. Withdrawn statements are only in section 14. [AUTHOR]
- CODE-LAST v1 (defined in 0.7): this plan proposes components; its rung table is section 6.1.

**Read for v4.3 in this session (VERIFIED (read) applies only to these; everything else is carried from v4.2 and not re-read):** [AUTHOR]
- whole files: `studio-notes/plan-v4-2.md`; the three round-3 reports and the three round-2 reports (all six are CONDENSED copies; the full reviewer texts are not available here); `studio-notes/plan-v4-round1-missed.md`; `studio-notes/plan-v4-1-resolve-round1.md`; `bible-extract-R447-R450.md`; `bible-extract-R448-R449.md`; `BRIEF-PREAMBLE.md`; `evidence/redactor-eval/README.md` and `lead-reading-1.md`; `src/hadavin_sdk/approvals/hmac_v0.py` (repo source).
- parts: `tickets/AK-G2.md` lines 1-140 (by search), 194-200, 223-224, 232-262, 296, 396, 425-440, 479-700; `tickets/P4b1.md` lines 1-12, 27-50, 94-112, 127-240 (by search), 266-302; `tickets/P4d.md` lines 196-225; `tickets/P1c.md` lines 1-5, 18, 41, 57, 106; `tickets/P5c.md` lines 151, 284, 704; `tickets/P4a.md` BN-15, BN-16; `LEAD-ORDERS.md` orders 11 (line 24), 57 A, 59 items 4 and 6, 64, 68, 69, 70, 138-145; `STANDING-ORDERS.md` item 6; `studio-notes/amendments.md` (first line of every entry); `freeze-list.md` lines 34-49; `studio-notes/GAPS.md` rows G3, G9, G14, G18, G22, G26; `studio-notes/plan-v3.md` lines 78-79 and 145; `reviews/market-scan-2.md` lines 10, 83-122, 876-925; `.github/workflows/ci.yml` lines 36-44; branch `core/T1-T2-tests` at `e00a047` (file list and the assertions of `tests/test_t1_meter_parallel.py`).
- PARTLY READ: `evidence/lead/lead-fetch-2026-11-07.md` (I read the first 400 characters of each line; facts quoted from it below were read by the v4.2 author in full and are carried).
- Carried from v4.2, not re-read now: `questions-for-lead.md` q334-q336, `tickets/P5b2.md`, `P5b5.md`, `P6a.md`, `plan-v3.md` other sections, `reviews/market-scan-2.md` other lines, `reviews/gateway-check-lead-reading-1.md`.

## 0. Read first: markers, letters, rules, words

### 0.1 Marker legend (one meaning each; every marker below is used in this file) [AUTHOR]

| Marker | Meaning |
|---|---|
| VERIFIED (read) | I read it myself in the named file of this checkout. It is still only as good as that file. |
| VERIFIED-SRC | the named scan file says it read the vendor's own docs source (raw GitHub docs repo); I did not open the vendor page |
| lead-fetch | in `evidence/lead/lead-fetch-2026-11-07.md`: pages fetched by the lead's small fetch models on 2026-11-07; the file says parts marked S are model summaries |
| UNVERIFIED | nobody in a file I read has checked it, or I could not find the file; the file or fact I could not reach is named next to the marker |
| UNVERIFIED-KEEP | a KEEP-CODE verdict whose failing property is UNVERIFIED; it must be verified before that ticket's build start (R448, order 68 item 5) |
| NOT READ | the page was fetched or searched but the fact was not visible; never guess it |
| NOT PRICED | no price source exists in this checkout; nothing with this marker may appear in a quote |
| PARTLY READ | the reader read only part of the source |
| PENDING | a test that was started or planned and has no result yet |
| AUTHOR | a change I made in v4.3 (or a v4.2 change round 3 asked to mark); the lead's freeze read checks these |
| NEEDS-LEAD | the lead must decide; my recommendation is given; listed in section 11 |
| NEEDS-OWNER | only the owner can decide (money, scope, a promise to clients, his own rules); my recommendation is given; listed in section 11 |
| OWNER-OPEN | a row whose verdict waits for the owner; the stated default applies until he answers |
| CONTESTED | a review finding or order wording I did not apply; the reason is given and can be checked |

Removed in v4.3: CLIENT-EXCLUDED (defined in v4.2, never used: no client has closed a rung yet, so every rung table row writes "0: none"). [AUTHOR]

### 0.2 Letters and numbers [AUTHOR: collision table added]
- **R<number>** = a bible rule only (for example R447, R448). Nothing else in this file starts with a bare R.
- **ruling N** = the lead's ruling N in `studio-notes/plan-v4-1-resolve-round1.md` (rulings 1 to 12; plan v4.1 called them R1 to R12). That file says the lead read the five round-1 reports only in part (PARTLY READ).
- **order N** = order N in `LEAD-ORDERS.md`; "order 57 A.2" = order 57, part A, item 2.
- **amendment A<n>** = an entry in `studio-notes/amendments.md`; always written with the word "amendment".
- **redesign step R1P, R3a, R5** = a named step of the diagnostics redesign in `studio-notes/design-v3.md`; always written with "redesign step".
- **plan-v3 section N** = a section of `studio-notes/plan-v3.md`; "section N" alone = a section of this file.
- **BN-n** = a build note at the end of a ticket, always with the ticket name (for example "AK-G2 BN-3").
- **q<number>** = an entry in `questions-for-lead.md`.

**The same letters mean different things in different files. In this file every id below is ALWAYS written with its owner word in front:** [AUTHOR]

| Letter | Meanings that exist | How this file writes them |
|---|---|---|
| A | amendments A1-A18; round-2 readiness findings A1-A7; plan v4.1's self-name "A8" | "amendment A9"; "round-2 readiness A1"; "A18" alone only for this plan |
| B | round-2 readiness B1-B9; amendment A9 item B1; AK-G2 burst rows B1-B3; P4b1 MeteredLLM rows B1-B19 | "round-2 readiness B1"; "amendment A9 item B1"; "AK-G2 row B1"; "P4b1 row B16" |
| C | round-1 comprehension C1-C12; round-2 readiness C1-C2; AK-G2 config rows C1-C9 | "round-1 C1"; "round-2 readiness C1"; "AK-G2 row C7" |
| D | round-2 readiness D1-D8; AK-G2 dispatch rows D0-D14 | "round-2 readiness D1"; "AK-G2 row D1" |
| F | round-1 design F1-F20; amendment A9 items F1-F10; the "facts F1-F10" of the AK-G2 round-3 resolve | "round-1 F9"; "amendment A9 item F4" |
| L | lead items L1-L17 (section 11); AK-G2 ledger rows L1-L21 | "lead item L3"; "AK-G2 row L15" |
| O | owner items O1-O11 (section 11) | "owner item O3" or "O3" (no other O ids exist in this file) |
| T | this plan's tests T1-T5 (section 8); P4b1 test groups T1-T6 (for example T2.3, T5.1) | "plan test T1.4" or "T1.4" for this plan; "P4b1 test T5.1" |
| M | round-2 design M-A to M-K; P4b1 mutants M1-M55; AK-G2 mutants M-a1.., M-b1..; P4d-b mutants b1-b21 | "round-2 design M-F"; "P4b1 mutant M24"; "AK-G2 mutant M-b18"; "P4d-b mutant b3" |
| V | round-1 V1-V4 and V4-01 to V4-25; AK-G2 later rows V1-V15 | "round-1 V4-07"; "AK-G2 row V7" |
| W | AK-G2 door rows W1-W17 (proposed W18-W28 in section 4.4) | "AK-G2 row W1" |
| I | AK-G2 decisions I1-I9 ("INFORM": the ticket author's decision, final unless the lead objects) | "AK-G2 decision I3" |
| G | GAPS rows (G3, G9, G14, G18, G22, G26) in `studio-notes/GAPS.md` | "GAPS row G18" |

### 0.3 Rules, orders and rulings this plan relies on (one plain sentence each, at first use) [AUTHOR]
Bible rules (owner hard rules; text in `bible-extract-R447-R450.md`):
- **R363**: every outside dependency sits behind a swappable module (a "kind") with a neutral default and at least one alternative.
- **R368**: no message may be lost or applied twice; this includes checking our received messages against the sender's own list of ids.
- **R369**: one tenant (client organisation) can never read another tenant's data, enforced in the data layer and proven by tests.
- **R371**: data of one client, one demo or one training set never affects another.
- **R445, R446**: the client decides whether outside tools touch his data, chooses among listed options, and the choice and its risk are written into the quote (full wording not in the extract: UNVERIFIED).
- **R447**: the tool ladder: try the client's own tool, then no-code tools, then our core modules, then free standard tools, then tested free libraries, and only then our own new code, which is reserved for the "guarantee-class" parts listed in 0.4.
- **R448** (CODE LAST): our own new code is allowed only for a guarantee-class part that no higher rung gives; every plan carries a rung table, and a KEEP-CODE verdict must name the guarantee and the one property the tool fails, with a reproduction (a failing test or a doc quote with its URL). Full text: section 16.
- **R449** (STAGES): the only stage names are DEMO, PILOT and PROD; "dev", "staging" and "test" are never stage names. Full text: section 16.
- **R450**: every rung decision needs dated research, a cost calculation, a test and a licence check; items used here: (d) licence check before anything ships, (f) contract text keeps "not reviewed by counsel", (j) the meanings of kind, EGM, the lead, guarantee-class, (k) wrap an outside library unmodified, never fork it.
- **owner decision 8** (2026-11-01): money, redaction and security work gets independent review rounds with no round limit.

Lead rulings (plan-v4 round-1 resolve):
- ruling 1: A18 is an amendment to plan-v3, not a replacement, and uses plan-v3's package ids. ruling 2: P2d stays on in v1. ruling 3: AK-G2's claim, lease and retry stay our own code (no Node job library in the core). ruling 4: the door contract text is the AK-G2 ticket's text; the hop before the door is outside the guarantee. ruling 5: the n8n licence sentence is our reading, not legal advice. ruling 6: the cost table rules. ruling 7: plan test T1 is not an owner gate. ruling 8: Presidio is an optional redactor backend, never the default. ruling 9: AK-G15, AK-G1, AK-G16 stay deferred; AK-G2 starts only after the open chain merges and a lead order releases it. ruling 10: the T2 long replay tests the ledger layer directly. ruling 11: P5b2, P5b5, P6b1 unchanged until the owner decides. ruling 12: no time estimates.

Lead orders (in `LEAD-ORDERS.md`):
- order 6(b): security, money and redaction tickets have no review round limit. order 11: the owner ordered the look-alike letter leak closed in core v1. order 19 E: P2d stays on (carried from v4.2, not re-read). order 27 items 56 and 63: one deployment per client plus a tenant field on every record; no new outbound text path. order 35: the gateway overlap check (LiteLLM and others do not replace our meter or redactor). order 49: the owner paused the Jagrat-first plan (amendment A15). order 57 A: the door stays our code until a forced-kill test shows otherwise; A.1 accepted small cuts (P5b5 rules 3 and 4 to ruff); A.2 deferred AK-G16, AK-G15, AK-G1 until a client or chain item needs them. order 59 item 4: seven more tickets deferred, AK-G2 stays ACTIVE; item 6(5): Unicode confusables data is the source of the fold table. order 64: our redactor misses 6 of 30 hostile inputs; ticket P1c fixes ours; no library is adopted; item 4: a bare number in prose is NOT masked, by decision. order 68: rung 0 is the client's tool (1); thin glue is under about 50 lines (2); retry, dead-letter, idempotency and approval records are guarantee-class (3); 20 tickets carry UNVERIFIED-KEEP rows to verify before build start (5). order 70 item 1: the look-alike test rows move to P2d-1; item 3: P5a's three cut-to-config verdicts are approved in principle. order 140: the lead's LiteLLM spend-cap test numbers. order 142: v4.2 go, with five must-fix points. order 143: the 30 round-1 findings must each get an outcome. order 145: the v4.3 points of this pass, A18 confirmed, freeze after a lead read.

### 0.4 The tool ladder and "rung" [AUTHOR: second ladder sentence merged]
"Rung" = one level of the tool ladder in R447 (owner order 2026-11-06). Before rung 1 comes a check of scope, budget, the client's size and willingness and the client's own tool; in a rung table the client's own tool is written **rung 0**.
1 no-code and low-code tools (n8n, Make and similar); 2 our core modules (already built and tested); 3 existing free or standard tools used as they are; 4 free libraries we test and build on; 5 our own new code, last, only for guarantee-class parts.
**guarantee-class** (R447 list, eight items): decisions; approval binding with a separate executor identity; redaction before the model; exact money and budget caps (reserve and settle); audit tamper-evidence; tenant isolation and least privilege; eval gates; no lost or double-applied message.
This is the only ladder this plan uses. (The repo file `.claude/rules/tool-ladder-before-code.md` is an older 2026-11-03 version of the same rule; R447 replaced it.) Text for the owner or a client says "a ready-made tool does it" or "our own code does it", never a rung number.

### 0.5 Verdict words: two vocabularies, one per table [AUTHOR: deferred rows]
Section 5 (module decisions) uses only these four words:

| Word | Meaning |
|---|---|
| ADOPT | use an outside tool, service or data as it is (configuration only) |
| WRAP | use an outside library, unmodified and pinned, behind our own wrapper module (R450(k)) |
| KEEP-CODE | our own code, because it carries a guarantee-class property no rung above gives |
| DROP | not built, because nobody needs it now (a frozen ticket stays; nothing is deleted) |

For a DEFERRED or PAUSED row, section 5 writes "if built: <word>" (the verdict that applies when the deferral is lifted), or "no verdict (not examined)". A deferred row is never built just because it has a verdict. [AUTHOR]

Section 6.1 (rung table) uses only the three R448 tokens, because the ticket check reads them:

| Token | Meaning |
|---|---|
| KEEP-CODE | same as above |
| CUT-TO-CONFIG+GLUE | a tool does it; we only configure it and connect it with thin glue. The part is still PROVIDED to the client; only our own code is cut |
| CUT | the component is dropped; nobody needs it (no row uses it today) |

Mapping, so one row never has two verdicts: ADOPT or WRAP in section 5 = CUT-TO-CONFIG+GLUE in section 6.1; KEEP-CODE = KEEP-CODE; DROP = CUT.
Owner decision 3 ("do not cut anything that connects to n8n or Make", section 2) is about what is provided. No row that connects to n8n or Make carries DROP or CUT.
**Scan verdict and cover figure** [AUTHOR]: `reviews/market-scan-2.md` gives each module a verdict word and a "cover" range, for example "WRAP, 40-60" = the scan agent's judgement that a library could be wrapped and would cover about 40 to 60 percent of the module's needs. Scan-2 line 9: "Cover % remains each agent's judgement, not a measurement. No candidate was installed or run." So no cover figure in this file is a count in the R448 sense. "Guarantee 5-15" (P2a row) is the same kind of judgement for how much of the guarantee a tool gives.
**glue** (thin glue) = under about 50 lines per component with no branching on business data (R447, order 68 item 2).

### 0.6 Status words (section 5, column "Status"; one meaning each)

| Status | Meaning |
|---|---|
| IN PR | an open pull request exists (section 0.9); work on it continues; merge state UNVERIFIED (not checked on GitHub) |
| TICKET FROZEN, NOT STARTED | the ticket text is frozen; no pull request yet; built in chain order |
| ACTIVE TICKET | listed as active in `freeze-list.md` (order 59 item 4); may be built when its dependencies merge and its start is released |
| DEFERRED | frozen ticket, not built. A deferral is LIFTED only by the OWNER (his yes); the lead only records the lift in an order (ruling 9; order 142 item 1). The start condition that makes us ask him is in order 59 item 4: "a client or a chain item names the need" |
| PAUSED | stopped by the owner (amendment A15, PAUSED line; order 49) |
| UNCHANGED | the plan-v3 row stands; A18 did not re-examine it |

### 0.7 Words (defined before use; one meaning each) [AUTHOR: words marked * were added or narrowed in v4.3]
People and process:
- **the owner** = the studio owner. **the lead** = the main Claude session on the owner's laptop that coordinates, reviews through `egm:*` agents and merges (R450(j)). **the cloud session** = the Claude Code session in the cloud container that writes tickets, builds on branches and opens pull requests (it never merges).
- **EGM** = the studio's review process: fresh reviewer agents (`egm:*` types) read the work and the evidence; the lead resolves (R450(j)).
- ***EGM-GATE v1** = the marker of preamble rule 13 (owner hard rule 2026-11-01): every plan, design, client text and non-trivial code change goes through EGM in order (brainstorm, draft, review, resolve, build, evidence, result review, drift report); the author never reviews his own work.
- ***CODE-LAST v1** = the marker of preamble rule 20 (R448): a plan or ticket must carry a rung table before build-start review.
- ***chain** = the merge order of core packages (plan-v3 section 7; amendment A15 J3 (a) quotes it as "order 20 item 4 merge order stands"). **open chain** = the pull requests of that order that are open now (section 0.9). "Chain order" = that merge order. No other meaning.
- **package** = one plan-v3 work package (P1a, P4b1 ...); **kit** = the Assembly Kit of amendment A10 (AK-* tickets).
- **work item 9.N** = item N of the order of work (section 9). **build start** = the review that releases a frozen ticket to a builder.
- ***gate** = a check that must pass before something may go further. Every gate in this file is named with its noun: "outbound gate (AK1b)", "recipient gate (AK-G22)", "live-call gate (P4b1)", "hostile-set gate (T3b)", "owner gate" (an item that waits for the owner's answer). "EGM-GATE v1" is the rule marker above.
- ***step** = an **AK1 step**: one unit of work in the AK1 step contract (input record with tenant and readers, output record, result done / needs a person / refused). Three other uses always carry their full name: **tick step** (one task in one pass of `runtime/tick.py`), **redesign step** (0.2), and "EGM step" (one stage of the EGM order).
- **tick** = one idempotent pass of `runtime/tick.py`, "run every 30-60 s by any scheduler".
- **start condition** = the named event that lets a deferred or outline item start. (plan-v3 and the no-single-dependency rule call these "triggers"; this file does not, see "trigger".)
Product and data:
- ***kind** = a swappable module with a neutral default and at least one alternative (R363, R450(j)), for example `llm`, `redactor`, `store`, `meter`, `secrets`, `signer`, `audit`, `channel`, `executor`. What it buys: a vendor or tool can be replaced, or a client's own tool plugged in, without changing the core; a vendor's library is imported only inside its kind module.
- **client's tool** = the automation tool the client chooses and owns (n8n self-hosted, n8n Cloud, Make, or Activepieces).
- ***sender** = the flow in the client's tool (or a small relay, a **forwarder**) that signs and sends messages to our door.
- ***source** (inbound source) = our config entry for one sender, with its own tenant, readers, agent, principal and signing secret. "source" alone always means this; files are "evidence files", and a price's origin is a "price page".
- **door** = the component that receives a signed web request from a sender and hands it to the ledger: `triggers/webhook.py` (AK-G2-b). Its **address** is the URL path `/inbound/<source>`. In v1 the door runs only in a demo-stage server (`serve`, AK-G2 line 194); hosting it for pilot or prod is AK-G16 (DEFERRED).
- ***trigger** = only inside the name "inbound trigger kind" (AK-G2: the kind through which an outside message starts a run). The Postgres rule that blocks forbidden changes to a receipt row (the ticket's "immutability trigger", AK-G2 line 175) is called the **receipt write guard** here.
- **tenant** = the client organisation a record belongs to (order 27 item 56). **readers** = the allowed readers of a record (AK1 `Readers`). **principal** = the identity a run acts for (`principals.yaml`); for a door it comes only from the source's config.
- **delivery id** = the sender's own id of a message, read from the signed body field `id_field`. **delivery key** = our keyed hash of tenant, source and delivery id (AK-G2 line 156).
- ***delivered message** = a message our door accepted and answered with 202. "Delivered" has no other meaning here (a part of a build is "provided"; a feature is "included").
- **restored-hash key** = an existing secret of the deployment (`app.py:202-205`, required in pilot and prod, at least 16 bytes); the inbound key used for delivery keys and body hashes is derived from it (AK-G2 line 153).
- **receipt** = one row in `inbound_receipts`: our record that a delivery arrived (key, keyed body hash, state, tries, run id). Not a payment receipt.
- ***ledger** = the receipt table plus its store methods (AK-G2-a), and nothing else. It remembers every delivery key, so the same message never starts work twice. The meter's day and month counters are the **spend totals**, never a ledger.
- ***lease** = the limited time (`lease_s`) for which ONE worker holds ONE receipt it has claimed; if the worker crashes, the lease runs out and another worker may claim the receipt (AK-G2 line 24). Nothing else is called a lease (AK-G1's conversation lock is a "hand-off lock").
- ***run** (noun) = one attempt of one agent at one message, stored as one row in `runs`; its id is derived from the delivery key and the **generation** (a counter raised only when a person reopens a message). The run row is the commit point (AK-G2 line 107). A single execution of an n8n workflow is an **execution**; a single test is a "test", never a "run".
- **outbound gate (AK1b)** = the one place every outbound text passes, masked first. **recipient gate** = GAPS row G22's gate for messages to people (no ticket yet).
- **hmac_v0** = our existing request-signing scheme (`approvals/hmac_v0.py`): HMAC-SHA256 over `v0:` + timestamp + `:` + body; `verify` returns one true/false and refuses a timestamp more than 300 s from now in either direction (`hmac_v0.py:47`, VERIFIED (read)).
- **meter** = the spend meter (P4b1): **reserve** sets money aside before a model call equal to the worst case; **settle** replaces it with the real cost; **release** gives it all back. ***hold** (noun) = one reservation as seen from the code that made it (P4b1 line 6); the verb "holds" keeps its ordinary meaning (contains, keeps). **micro-dollar** = one millionth of a US dollar, the integer unit inside the meter (amendment A9 item B1).
- ***cap** = a spend cap only: the most an agent may spend per run, day or month. An n8n plan's number of included workflow executions is an **execution allowance**; a Make **credit** is Make's billing unit (what one credit buys: UNVERIFIED); the number of review rounds is a **round limit**.
- **stop_state** = the stop switch the agent cannot clear itself, with an audited reset (P2a).
- **mask** = replace personal data or secrets with placeholders before any text reaches a model. **put-back** = our code (not the model) puts the real values back afterwards. **redactor** = the kind that masks; its **backend** = the detector used inside it.
- ***hidden copy** = a known secret or personal value that survived masking in a disguised spelling (look-alike letters, zero-width characters). P2d-2 refuses the whole text when it finds one; the P2d ticket calls this a "hidden-channel" flag.
- ***approval channel** = the `channel` kind through which a person's approval reaches us (`approvals/receiver.py`). "channel" has no other meaning here.
- **hostile set** = the redactor test corpus `evidence/redactor-eval/corpus.json`: 30 hostile inputs, 48 must-mask lines, 14 must-keep lines (README line 2).
- **Presidio** = Microsoft's open-source personal-data detector (MIT). **execution** (n8n) = one execution of one workflow. **Sustainable Use 1.0** = n8n's licence (fair-code, not open source). **ee folders** = directories of n8n or Activepieces under a separate commercial licence. **Close** = a sales CRM product; a "Close task" is a to-do item inside it. **Jagrat** = the showcase demo of amendment A15 (PAUSED).
- **digest binding** = an approval is valid only for the exact content hash of the item approved.
- **ast-grep** = a free (MIT) code-pattern search tool usable in CI. **OTel** = OpenTelemetry, an open telemetry standard.
- **RLS FORCE** = Postgres row-level security with `FORCE ROW LEVEL SECURITY` (the rule also binds the table owner). **SKIP LOCKED** = a Postgres row-lock option that lets two workers never take the same row.
- **pg-boss, Graphile Worker** = Node.js job-queue libraries on Postgres; **Procrastinate** = a Python one (market-scan-2 pass 4).
- ***template pack** = for one client tool: its exported flows (a flow file the tool can import) that sign and send messages to our door, plus thin glue, plus the T5 contract tests (section 5). Not the approval channel.
- ***window** = only in **dedupe window** (how long a product remembers a key). The 300 s of `hmac_v0` is the **signature age limit**; `lease_s` is the **lease time**.

### 0.8 Package and ticket ids

| Id | What it is | Where defined |
|---|---|---|
| P1a, P1b | plan-v3 package P1 split in two pull requests: P1a moves the text-folding module out of PR #50 with its version; P1b closes gaps 1-5 and 7 | amendment A9 item F4; amendment A12 |
| P1c | redactor gaps found by the library comparison: base64 decoded view, whole internal host names, the bare number as a decided property, a permanent corpus test | order 64; `tickets/P1c.md:1` (revision 7, FROZEN) [AUTHOR] |
| P2a | stop state | plan-v3 section 6; `tickets/P2a.md` |
| P2d | land PR #50's change to `guard/redact.py`; built as P2d-1, P2d-2 (refuse the whole text when a hidden copy is found), P2d-2b | plan-v3 section 6; orders 11 and 19 E |
| P3a | migration rule (forward-only numbering, previous release reads the new schema) | plan-v3 section 6 |
| P4a | refuse instead of estimate, five-class usage, price tiers | plan-v3 section 6 |
| P4b1, P4b2 | plan-v3 P4b split: P4b1 meter kind; P4b2 billing classes and orphan sweep | amendment A9 item F2; amendment A11 |
| P4d | one store contract suite over memory and Postgres; money SQL (P4d-a, -b, -c) | amendments A11, A13, A14 |
| P5a | redesign step R1: closed error codes, safe diagnostic text, hostile test corpus | plan-v3 section 6 |
| P5b1 | redesign step R1P: provider error plumbing | `tickets/P5b1.md:1` |
| P5b2 | redesign step R3a: "a checked-in table that classifies every place where the SDK builds a `ConfigError` (the error that stops the program at start-up); a generator that rebuilds that table by reading the source text; and a CI test that fails when a new place is not classified. Tests and one tool only. No change under `src/`." | `tickets/P5b2.md:15` (VERIFIED (read) by the v4.2 author; carried) |
| P5b5 | redesign step R5: "pin that no old error-text path comes back, pin the one backstop, write the operator page, close the hostile corpus" | `tickets/P5b5.md:1` (carried from v4.2) |
| P5c | redactor kind and masked model wrapper plus put-back | plan-v3 section 6 line 110 |
| P6a | client-profile check (demo-stage kinds refused in pilot and prod) | plan-v3 section 6; `tickets/P6a.md` |
| P6b1, P6b2 | plan-v3 P6b split: P6b1 no-training lock; P6b2 secret-boundary lint | amendment A9 item F6 |
| P0t | stage rename (stages are DEMO, PILOT, PROD only, R449) | `tickets/P0t.md` |
| AK1 | step contract (AK1a, AK1c tenant parts) and the one outbound gate (AK1b) | `tickets/AK1.md` revision 3 |
| AK-G2 | inbound trigger kind: ledger (AK-G2-a) and signed door (AK-G2-b); absorbs plan-v3 v1.1 row P7a | `tickets/AK-G2.md` revision 3 FROZEN (line 5), build notes BN-1 to BN-23 (they win over the body) |
| AK-G15, AK-G1, AK-G16 | needs-a-person queue; chat agent with hand-off; deployment into the client's own cloud | `tickets/`; DEFERRED (order 57 A.2) |
| AK0, AK2a, AK4a | research note; document reader; joined-pipeline test harness | DEFERRED (order 59 item 4(a)) |
| JG-3 | chat-ops notifier for Jagrat | PAUSED (amendment A15) |

Open item 13 of plan v4.1 (what P5b2 means) is CLOSED: plan-v3's "redesign step R3a" and the scan's "CI site tables and pins" (market-scan-2 line 31) name the same package; the ticket title above decides.

### 0.9 Pull requests named in this plan (the "open chain")
Heads move; this table copies the newest lines the v4.2 author read (q334 at 10:23Z, q336 at 10:28Z, 2026-11-07; not re-read for v4.3). Merge state: UNVERIFIED (no GitHub check here).

| PR | Package | Branch, head (where the head was read) |
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

### 0.10 Evidence files (paths under `handover/`) [AUTHOR: heading renamed from "Sources", see "source"]
- `reviews/market-scan-1.md`, `reviews/market-scan-2.md` (Addendum A at line 850: lead-verified facts; Addendum B and pass 4 from line 860). Every cover figure below is a judgement (0.5).
- `evidence/lead/lead-fetch-2026-11-07.md` (marker lead-fetch). It names the pages it read but holds no URL per fact.
- `reviews/gateway-check-lead-reading-1.md` (order 35 test, LiteLLM 1.108.1). The raw evidence file is on the lead's side.
- Order 140 spend-cap test raw file `egm/hadavin-sdk/core-complete/captest-1.md`: NOT in this checkout; numbers come from the order 140 text.
- Owner policies "client-chooses-tools-policy" and "options-first-then-decide" are in `.claude/rules/` and in bible R445-R447 (R445 and R446 texts themselves are not in the bible extract: UNVERIFIED wording).

## 1. What A18 changes in plan-v3
plan-v3 stays frozen; A18 changes only the items below; everything else in plan-v3 and amendments A1-A17 stands.
Changed:
1. plan-v3 section 5 (kinds), P5c row: the pattern redactor stays the default. A new rule for EVERY redactor backend, the default included: it must pass the hostile set (section 8, T3b) or the pilot and prod stages refuse it. Presidio may run only as an EXTRA layer after our backend, never instead of it (section 5, P5c row). The pilot and prod refusal is wired in only after P1c and the look-alike fix have merged (section 8 T3b; lead item L13). [AUTHOR]
2. AK-G2 (which absorbs plan-v3 v1.1 row P7a): its door rule is UNCHANGED: the frozen ticket's 401 for a request without a valid signature stays the default (section 4.4). A18 adds only a CONDITIONAL option for late verbatim retries, built only if the T5 trial shows a chosen tool needs it, and then only through its own ticket amendment (order 145 item 2(b)). A18 also asks for one config test row (section 4.2; lead item L3). When AK-G2 starts is unchanged: amendment A10 says the kit starts after core v1 (P8c); ruling 9 adds that the open chain must have merged and a lead order must release it. A18 does not move AK-G2 earlier. P8a (demo re-pin) does not wait for AK-G2, because AK-G2 is not a v1 row (round-1 Z5). [AUTHOR]
3. plan-v3 section 6 P4b row and section 8 (b): P4b1's evidence gains T1 (section 8). T1 adds to the plan-v3 section 8 eight-process Postgres race (zero overshoot); it replaces nothing and is not an owner gate.
4. New rules for quotes and contract schedules: the n8n licence line (section 4.7), the quote sentence on messages and on reconciliation not included in v1 (section 4.5) and the cost rules (section 7). [AUTHOR]
5. New, outline only: template packs for client tools (section 5), built only for a tool a client has chosen, and only for the IN direction until an OUT contract exists (section 4.5).
6. Answer to plan v4.1 open item 9 (store in pilot and prod): Postgres only, fail closed (section 4.2), with a proposed dated exception and the SQLite outline as the named alternative (section 6.2; owner item O11). [AUTHOR]
7. New: a single-dependency audit (section 6.2), which the repo's CLAUDE.md requires of every design. [AUTHOR]

Not changed: P2d stays on in v1 as built (ruling 2); P5b2 and P6b1 stay as built until the owner decides, P5b5 stays DEFERRED (ruling 11, order 59); AK-G15, AK-G1, AK-G16 stay DEFERRED (ruling 9); no time estimates (ruling 12, plan-v3 section 9 line 194); AK-G2 claim/lease/retry stays our code as the ticket designs it (ruling 3).
Supersedes: plan-v4, plan v4.1 and plan v4.2 entirely (none was recorded). [AUTHOR]

## 2. Owner decisions that shape A18 (2026-11-07; as condensed by the lead in plan-v4 section 1, wording not re-checked against the owner's own message: UNVERIFIED)
1. The CLIENT chooses the automation tool: n8n self-hosted (licensed by the client), n8n Cloud, or Make. We do not choose for him (R445, R446; options-first rule).
2. Per-seat tools (Port, Retool and similar) add up to sums small clients will not pay; they are NOT a default part of any build.
3. Do not cut anything that connects to n8n or Make.
4. Plan every module, v1 and later, with EGM and the best quality and performance.
Activepieces is NOT in the owner's list. A18 shows it to a client only as an option, with no pack built until a client chooses it (NEEDS-OWNER O5).

## 3. What the research found
### 3.1 Read at a source (marker per line)
- Dedupe windows (lead-fetch): SQS FIFO "within the 5-minute deduplication interval"; Cloud Tasks task names remembered up to 24 h after deletion; Pub/Sub exactly-once is pull-only, one region, publish-side duplicates not covered; Google Workflows/Eventarc 24 h. Cloudflare Workflows instance id: duplicate refused only until retention 3, 7 or at most 30 days (VERIFIED-SRC, market-scan-2 section 6). Cloudflare Queues: at-least-once, no dedupe, Paid retention 4 days default, 14 at most (VERIFIED-SRC, market-scan-2 section 3 item 7). pg-boss: dedupe by policy or time slot, completed jobs deleted after `deleteAfterSeconds`, default 7 days; Graphile Worker: `job_key` only while pending, "no permanent job_key log", replace mode overwrites the payload, and a same-key job added while one runs makes a second job; Procrastinate: `queueing_lock` only in `todo` (all from docs read on raw GitHub, market-scan-2 pass 4 table and lines 905-917, 2026-11-07). [AUTHOR: Graphile second-job fact added]
- Spend caps: Cloudflare AI Gateway docs text "a burst of concurrent requests can briefly exceed the limit" (VERIFIED-SRC, market-scan-2 section 5 item 3; Addendum A). LiteLLM 1.108.0 (lead's laptop test, order 140, 2026-11-07): checks before the call and records spend after, so it overshoots by up to one call (details in section 8, T1).
- Our own meter: main's `Limits` (check, then charge after) admitted 50 of 50 parallel callers at cap USD 2.00, call cost USD 1.00 (branch core/T1-T2-tests `e00a047`, `tests/test_t1_meter_parallel.py`, q335; order 142 item 3 accepts it as a real finding). VERIFIED (read) for v4.3: the branch exists at `e00a047` with the five files named in T1, and its parallel test asserts "at most floor" and "overshoot by less than one call" (lines 34-53). That is the evidence P4b1's reserve/settle is needed. [AUTHOR]
- Failed-call billing: the Claude errors page lists codes (400, 401, 402 billing_error, 403, 404, 409, 413, 429, 500, 504, 529) with no billed or not-billed statement (lead-fetch). One page of one vendor.
- LiteLLM supply chain: 1.82.7 and 1.82.8 were malicious (GHSA-92x9-889m-jgmw; docs.litellm.ai/blog/security-update-march-2026, published 2026-03-24, lead-fetch). 1.107.0 compromised in October 2026: BerriAI/litellm issue 47826, from the lead's earlier fact-check batch (Addendum A); that issue page is NOT among the pages of lead-fetch, so its text is UNVERIFIED here.
- n8n: licence Sustainable Use 1.0; scan-2 quotes LICENSE.md (raw GitHub, read 2026-11-07): "use or modify the software only for your own internal business purposes or for non-commercial or personal use". Addendum A (lead): "Service to clients is NOT permitted; the client owns the account" (the clause the lead read is not quoted with URL in this checkout). n8n Community lacks (lead-fetch): custom variables, environments, external secrets, external binary storage, log streaming, multi-main, projects, SSO, sharing of workflows and credentials, Git version control; lead-fetch says these need "Business/Enterprise self-hosted", with no split per feature. Prices EUR 20 / 50 / 667 a month billed annually with 2.5K / 10K / 40K executions; EUR 667 is self-hosted only (lead-fetch; Addendum A).
- n8n duplicates: "you must build dedupe yourself" (community and vendor-adjacent snippets, market-scan-2 n8n section, marked S); n8n's own statement on whether a webhook request is stored before the reply: none found (order 57 A, the lead's own search, 2026-11-06).
- Make: free plan 1,000 credits a month; plan prices NOT READ (lead-fetch).
- Activepieces: MIT outside `packages/ee/` and `packages/server/api/src/app/ee` (LICENSE read, market-scan-2). Prices (lead-fetch): Free 1,000 credits and 5 users; Plus USD 20 a month, 10,000 credits; Team USD 200 a month; overage USD 0.007 a credit; Embed from USD 36k a year. Plus is the vendor's CLOUD plan; the MIT licence covers the self-hosted core.
- Redactors on our hostile set (`evidence/redactor-eval/lead-reading-1.md` lines 3-4, one test each, home advantage stated by the lead; VERIFIED (read)): hostile inputs FULL/PARTIAL/MISS, must-mask, must-keep KEPT/ALTERED:
  - our chokepoint `runmap.redact_text`: 24/0/6, 46/2/0, 14/0;
  - Presidio default: 14/3/13, 29/5/14, 7/7;
  - Presidio plus 4 custom recognisers and a normaliser: 23/2/5, 33/5/10, 7/7.
  Our six hostile misses, named in `lead-reading-1.md:6` (the caveats line) (VERIFIED (read)): the Cyrillic look-alike e-mail and key (2), three base64-encoded values (3), and "ref 55556666 paid" (a bare number with no context, 1). The two PARTIAL must-mask lines are host names whose ".example" suffix stayed. Order 64: "no free library beats our redactor on our corpus". The test scripts `t_*.py` named in the README are NOT in this checkout (directory listing: README.md, corpus.json, lead-reading-1.md, score_common.py). [AUTHOR: the six misses named]
- Unicode folding, re-run by me for v4.3 (python 3.13.18, `python3 -I -c` with `unicodedata.normalize('NFKC', ...)`, 2026-11-07): Cyrillic U+0430 stays U+0430, Greek omicron stays U+03BF, a zero-width space inside a word stays; fullwidth "a" becomes "a". So the standard-library normaliser alone does not fold look-alike letters or remove zero-width characters. [AUTHOR: re-run]
- Store kinds: `store/memory` is a demo-stage-only kind (`DEV_ONLY`, `backends/table.py:593-602`, per `tickets/P6a.md:16`), and demo-stage-only kinds are refused outside the demo stage (`config.py:350`, per `tickets/P6a.md:29`). The v4.2 author read the ticket text, not the code. plan-v3 line 78 (VERIFIED (read)): store kind default Postgres; memory for demo and tests only; alternative "outline: SQLite; trigger: Intake moves onto the core meter".
- CI Postgres: `.github/workflows/ci.yml:40` runs `postgres:17.10` (VERIFIED (read)). [AUTHOR]
- Appsmith: Free up to 5 users; Business USD 15 per user per month; Enterprise USD 2,500 a month for 100 users (lead-fetch). Port: free up to 5 seats; USD 30 or 48 per seat per month billed annually (lead-fetch). Retool Business builder USD 50 (annual) / 65 (monthly) per month (lead-fetch). Langfuse Enterprise USD 2,499 a month (lead-fetch).

### 3.2 Not proven (UNVERIFIED, with what is missing)
- Hatchet "sliding TTL" (lead-fetch S) and pg-boss "no option named dedupe" (lead-fetch): read on pages, but whether they forget a key in our sense is the scan's inference.
- DBOS exactly-once claim: lead-fetch line 8 says DBOS "claims" it; retention UNVERIFIED (pass 4).
- "No vendor publishes billing of failed calls" as a claim about all vendors: one page read.
- Cloud filters (Bedrock, Azure, GCP) "irreversible, no put-back": from search snippets (market-scan-2 line 28).
- OTel GenAI `error.type` status: page moved, status NOT READ (lead-fetch).
- Whether Presidio folds look-alike letters: not tested on its own; the per-row result is in the raw evidence on the lead's side, NOT in this checkout.
- Which n8n paid plan unlocks which missing feature; what n8n Cloud Starter and Pro include (sharing, projects): NOT READ.
- Whether n8n, Make and Activepieces can compute an HMAC signature and re-sign a webhook on each retry: UNKNOWN (section 4.4).
- Make "one action costs about one credit": not in lead-fetch.
- promptfoo ownership, docling licence: not in lead-fetch.
- Postgres default `max_connections` of 100 (used in T1.6): from general knowledge of PostgreSQL, not read in a file here: UNVERIFIED. [AUTHOR]

## 4. The connection, and the door contract
### 4.1 Picture (who calls whom)
```text
client's tool (n8n self-hosted | n8n Cloud | Make | Activepieces)   <- the client chooses, owns the account, pays the licence
   | (1) IN: the sender signs a web request and sends it to our door (AK-G2-b)
   v
[ door ] --> [ ledger: receipt, dedupe, claim/lease ] (AK-G2-a) --> AK1 step --> run (run row = commit point)
                                                                     |-- model call: masked first (P5c in v1; AK1b gate in the kit)
                                                                     |-- meter (P4b1): reserve before, settle after
                                                                     |-- stop_state (P2a): read before each AK1 step
                                                                     '-- audit (plan-v3 kinds)
   (2) OUT: our core asks the client's tool to act, or the tool calls our executor: NO CONTRACT EXISTS (section 4.5). Nothing is built for it.
```
The request the sender sends carries the text the client's own systems gave it. That text is NOT masked before it reaches our door; masking happens inside the run, before any model call. The rule "a no-code flow gets redacted data only" (R447) is about data our core SENDS to a flow; in v1 our core sends nothing to a flow (the door's replies are empty, section 4.3).
Gate per path: model calls in v1 pass the P5c masked wrapper and the P6a profile check; in the kit, AK1's outbound gate (order 27 item 63). The door adds no outbound path (AK-G2 line 103). OUT has no gate because it has no contract.

### 4.2 Store rule for pilot and prod (the plan's answer to plan v4.1 open item 9)
- The ledger, the claim/lease and the run rows need Postgres. In pilot and prod any other store is REFUSED at start-up (fail closed). This is already how the config works: `store/memory` is a demo-stage-only kind and such kinds are refused outside the demo stage (section 3.1, `tickets/P6a.md:16`, `:29`). A18 adds a negative test row to AK-G2-b's config rows: a pilot config with `store: memory` and an inbound source refuses to start (NEEDS-LEAD L3). SQLite (plan-v3 v1.1 row P7l, AK-G2 row V10) is the named alternative store; it is refused for these paths in pilot and prod until P7l exists and passes the ledger, claim and tenant contract rows (section 6.2; owner item O11). [AUTHOR: v4.2 said "never allowed"]
- Contract wording for any Postgres store used by these paths: (a) the claim uses `FOR UPDATE SKIP LOCKED` (AK-G2 line 163, already in the ticket); (b) a database that holds more than one tenant's rows must have RLS FORCE on every table with a tenant column. Today's design is one deployment per client (order 27 item 56), so (b) is a second wall, not the only one. No ticket the v4.2 author read carries (b) (search of AK1, AK-G2 and P4d tickets for RLS: no match). NEEDS-LEAD L4: a build note on AK1 for (b), or a recorded "not needed while one deployment per client".

### 4.3 Inbound contract = AK-G2 ticket revision 3, quoted (ruling 4)
Where this plan and the ticket differ, the ticket wins. A18 changes nothing in this contract (section 4.4). [AUTHOR]
- Line 102 (quoted): "**Signed inputs only, deny by default.** A webhook without a valid `hmac_v0` signature is refused with 401 before the body is parsed or anything is saved. The sender id is read ONLY from signed bytes (the body), and every source must name the field (`id_field` is required). The tenant, readers, agent and principal come ONLY from the source's config, never from the request. No two inbound sources, and no inbound source and the approval channel, may share a secret (row C7)."
- Line 103 (quoted, start): "**No outbound text added (order 27 item 63).** Every reply of the webhook has an EMPTY body (status code and, for 503, a `Retry-After` header only). AK-G2 sends nothing to anyone: no notification, no message, no model call of its own."
- Line 107 (quoted, start): "**Fail closed, and never lose.** A store error before the receipt commits answers 503 (the sender retries); after the commit, every failure leaves the receipt open or releases it, and the lease brings it back. **The run row is the commit point:** exactly one run per message per generation, because the run id is derived from the delivery key and the generation (INFORM I3), and once that run exists dispatch never calls the step again for it." "Never lose" covers only messages after our 202 reply (section 4.5). INFORM I3 = AK-G2 decision I3 (line 396): at most one run per message per generation; a cut-off run goes to a person, and only a person's reopen starts a new run. [AUTHOR: I3 explained]
- Line 162 (quoted, start): "`receive_inbound(...)`: ONE transaction. **Dedupe first:** if `rec.delivery_key` exists, compare `body_sha256`: equal gives `duplicate`, different gives `conflict`; nothing is written, even when the source is full." The transaction covers the receipt and its body only. The claim (line 163) and the run row (Interface 6) are separate statements in the SAME database; one run per message comes from the run id derived from the key, not from one shared transaction.
- Line 194, Interface 7, the door's order of work: (1) unknown path 404; (2) too large 413 before any HMAC work; (3) `hmac_v0.verify` with each resolved secret, none true gives 401; (4) only now is the body parsed (bad body or id 400); (5) id check; (6) `inbox.receive`: new or duplicate 202, id reuse 409, busy 503 with `Retry-After` or store error 503; anything else 500; every reply body is empty. [AUTHOR: step numbers named]
- Line 195, forwarder contract (quoted): "Re-sign EVERY attempt with a fresh timestamp; a 401 after a retry means "re-sign and send again", not "give up". Send one JSON object per request, with unique keys. Put the message's id in `id_field` as a JSON string. Resend a retry byte for byte (a re-formatted retry is an id reuse, 409). On 503, wait `Retry-After` seconds and retry." A18 keeps it unchanged. [AUTHOR]
- Line 223 (quoted): "Unsigned, stale (more than 300 s either way) or wrongly signed requests are refused before the body is parsed and before any write. Replay inside 300 s is a `duplicate`. Replay after 300 s fails the signature." [AUTHOR]
- Line 177 (quoted, end): "Nobody deletes receipts in v1 (V6)." V6 = AK-G2 row V6, a later purge of old receipt rows (hashes only), start condition "the receipts table passes a size the lead sets, or GAPS row G18's policy" (line 433). Line 222, secrets: "One or two signing secrets per source, named in config, read once through the secrets kind; never logged". AK-G2 row W15: with two secrets, either verifies; a third gives 401. [AUTHOR: V6 explained]

### 4.4 A retry that arrives after the signature age limit: the frozen rule stays, one conditional option (order 145 item 2(b); order 142 item 1(b)) [AUTHOR: section rewritten]
**The rule (default, binding):** the frozen ticket text stands. A request without a valid `hmac_v0` signature, including one whose timestamp is more than 300 s from now in either direction, is refused with 401 before the body is parsed or anything is saved (AK-G2 line 102; Interface 7 items (3) and (4); line 223). A sender re-signs every attempt (line 195). A18 does not change this, and nothing in v1 is built differently because of this section.
**Plain fact:** it is UNKNOWN whether n8n, Make and Activepieces can compute an `hmac_v0` signature at all, and UNKNOWN whether their built-in retry re-computes it with a fresh timestamp on each attempt or re-sends the first request unchanged. No file in this checkout answers it (market-scan-2 says for n8n only "HMAC check only via custom code", marked as a judgement). T5 tries it per tool as a TRIAL; it is not a promise to any client.
**Who the rule hurts, and the real benefit of the option (the only case it helps).** The option below helps only a sender that meets ALL of these: (1) it re-sends a retry byte for byte with its FIRST signature (it cannot re-sign); (2) that retry reaches us more than 300 s after the first signature's timestamp; (3) its first attempt DID reach our door and commit a receipt, but the sender did not see our 202 (a cut connection or a timeout). In that case the message is already safe with us; under the rule the late retry gets 401, so the tool reports a failure that did not happen and may alert a person or stop the flow. That is the whole benefit: no false failure report. It saves no message. If the first attempt did NOT commit, the late verbatim retry is a new message for us and gets 401 under every option: such a tool loses messages unless a forwarder re-signs them (line 195; AK-G2 row V4 for per-sender schemes). A retry inside 300 s already gets 202 `duplicate` under the rule (line 223).
**Conditional option A (not built in v1).** When `hmac_v0` fails ONLY because a well-formed timestamp is too old, and the HMAC is valid for one of the source's configured secrets, the door parses the signed body, computes the delivery key and looks it up: receipt exists with the same keyed body hash: 202, nothing written; receipt exists with a different body hash: 409, nothing written; anything else: 401.
- **Adopted only if** the T5 trial (section 8) records that a tool a client has chosen re-sends retries byte for byte more than 300 s after signing. Then it needs its own AK-G2 ticket amendment (order 145 item 2(b)); the lead decides (lead item L17).
- **What that amendment must carry** (round-3 design M1-M4, readiness 4.4 items):
  - (a) A **door-only stale-aware verifier** in `triggers/webhook.py`, because `hmac_v0.verify` returns one true/false for every failure (malformed, future, old, bad HMAC alike; `hmac_v0.py:37-51`, VERIFIED (read)). It returns a closed reason: `ok`, `stale`, or `bad`. `hmac_v0.verify` and the approval channel's strict path `parse_button` (`hmac_v0.py:54-79`) stay unchanged and never call it.
  - (b) **The exact stale test:** the timestamp header is 1 to 12 ASCII digits, and `now_ts - ts > 300`, and `now_ts - ts <= stale_max_age_s`, and the HMAC matches one configured secret. A timestamp more than 300 s in the FUTURE, a non-digit or over-12-digit timestamp, an empty secret or a wrong HMAC is `bad`: 401 as today.
  - (c) A **configurable maximum stale age** `stale_max_age_s` per source (name proposed; validated config, documented default in one place; my recommendation: default set from the longest retry delay measured for the chosen tool in T5, with a ceiling the lead sets). Past it: 401.
  - (d) **401 for every failure on the stale branch**: bad HMAC, past the maximum age, body that does not parse, missing or bad `id_field`, no receipt, a store error, the rate bound hit. The branch can only ever add the answers 202 and 409, and only for a receipt that exists, so it never writes and never starts a run.
  - (e) A **per-source rate bound** on the stale branch in AK-G2-b (bringing AK-G2 row V9, the per-sender rate cap, forward for this branch only), because each stale replay costs us the body read (up to `max_body_bytes`, by default `evidence.max_document_bytes` per AK-G2 BN-18, ceiling 10 MiB), one HMAC per configured secret over that body, a JSON parse, a keyed body hash and one database read; production flood limits stay AK-G16's.
  - (f) A **new read-only store method** that reads one receipt by tenant, source and delivery key: none of the 10 store methods after AK-G2 BN-3 and BN-14 reads a receipt without writing (`receive_inbound` writes on a new key).
  - (g) The **multi-secret loop**: the stale branch tries each configured secret (current, previous) as Interface 7 item (3) does; tested with the PREVIOUS secret.
  - (h) **Revocation needs a restart:** doors and secrets are built once at start (line 194), so a removed secret stops verifying stale replays only after the next start. The runbook says so.
  - (i) Build notes (numbers proposed; the amendment assigns them): **BN-24** stale-aware verifier; **BN-25** stale branch in `handle_inbound`; **BN-26** `stale_max_age_s` and the per-source rate bound.
  - (j) Test rows (proposed AK-G2 rows): **W18** stale, same body, receipt exists: 202, nothing written; **W19** stale, same id, different body: 409, no reuse row written; **W20** stale, no receipt: 401; **W21 "bad HMAC and stale: body never parsed"**: 401 and a spy on the JSON parse saw no call; **W22** timestamp 301 s in the future: 401; **W23** non-digit and 13-digit timestamps: 401; **W24** stale beyond `stale_max_age_s`: 401; **W25** stale signed with the previous secret, receipt exists: 202; **W26** stale signed with a removed secret after a restart: 401; **W27** store error on the stale branch: 401, nothing written; **W28** rate bound hit: 401. AK-G2 row W1 ("a timestamp 301 s old: 401") stays true for every request that does not reach the stale branch.
  - (k) Mutants (proposed): **M-b38** the stale branch accepts a new id (killed by W20); **M-b39** the stale branch skips the HMAC check (W21); **M-b40** `parse_button` or `hmac_v0.verify` uses the stale-aware verifier, so a stale approval-button callback is accepted (killed by an approval-channel row: a stale signed button callback still returns `None`); **M-b41** the 409 on the stale branch writes a reuse row (W19); **M-b42** `stale_max_age_s` ignored (W24); **M-b43** only the first secret tried on the stale branch (W25); **M-b44** a future timestamp treated as stale (W22).
- **Consequences, stated plainly, if adopted:** an attacker who recorded one complete signed request can replay it until `stale_max_age_s` and learn one bit (202 or 409: we hold this message; 401: we do not or the age is past). He gets no new receipt, no new run, no model call and no spend. The rate bound limits the cost. "Never forgets" still holds only while the restored-hash key and the receipt rows are kept (section 4.6).
**Other options considered:** (B) accept an exact body match with no signature at all, by looking up the keyed body hash before parsing. Rejected: it hashes unauthenticated input, needs a new index on the body hash (schema change in a frozen ticket), and tells anyone who holds a copy of a body whether we received it. (C) keep the ticket as is and give no pack (or a forwarder) to a tool that cannot re-sign: this is now the DEFAULT.

### 4.5 What the guarantee does NOT cover
- **Before the door.** If the client's tool, or the system that feeds it, loses a message before our door answers 202, we never saw it and cannot recover it. n8n has published no statement on whether it stores a webhook request before replying (order 57 A).
- **Reconciliation is NOT included in v1.** [AUTHOR: rewritten] AK-G2 BN-14 (2026-11-06) CUT `compare_ids`, `IdComparison` and `list_inbound` from AK-G2-a and moved them, with the command `hadavin-sdk inbound compare-ids`, to AK-G2 row V7, "built in AK-G15", start condition "before any pilot (R368: comparison against the source's own ids)" (AK-G2 lines 614-618, VERIFIED (read)). v4.2 still cited the cut `compare_ids` (line 192) as if it were in AK-G2-a; that was wrong. So v1 contains no code that compares our received ids with the sender's ids, and no runner is named. Section 5 carries an explicit row for it. Bible R368 (owner hard rule) asks for "reconciliation against the source's own ids", so leaving it out needs the owner's yes: NEEDS-OWNER O3 (options there, including removing the promise). Until he answers, the quote sentence below applies and no quote promises reconciliation.
- **The quote sentence** (every quote and contract schedule that uses the door; order 145 item 2(e); the only client copy of this claim in A18): [AUTHOR]
  > "We record each message your tool delivers to us once and start at most one run for it; a run that is interrupted or refused is handed to a person. We do not check whether your tool lost messages before they reached us; that check is not part of this build."

  What the ledger proves for each part: "record ... once" = one receipt per delivery key, never deleted in v1 (AK-G2 lines 162, 177); "at most one run" = the run id derived from the key and the generation (AK-G2 decision I3); "interrupted ... handed to a person" = `needs_person run_interrupted` (AK-G2 BN-2 rule 4); "refused ... handed to a person" = a run stopped by a spend or stop limit ends `needs_person run_limits` (BN-2 rule 2). Two honest gaps, NEEDS-LEAD L16: a message the door itself refuses (401, 400, 409) never becomes a run and the sender only gets the status; and an AK1 step that returns `refused invalid_input` is final on the first try without a person (AK-G2 row D3a). The sentence does not say otherwise, but a reader could read "refused" more widely. "Your tool delivers to us" uses "delivered" in this file's sense: accepted by our door with 202.
- **OUT direction.** AK-G2 revision 3 sends nothing (line 103), so there is no OUT text to copy (ruling 4 cannot apply). Nothing is built for OUT. Before anything is: a written and reviewed contract (request schema, who authenticates, an idempotency key tied to the ledger key, which identity holds the executor credential, a replay test with one effect). NEEDS-LEAD L2.
- **Effects in the client's systems.** An effect in a client's own CRM or payment system is not inside our database.

### 4.6 "Forever", retention and erasure
- "Never forgets" means: the receipt row and its keyed delivery key are never deleted in v1 (AK-G2 line 177; the runtime role cannot delete either table; only the purge role deletes bodies, and only final ones, line 170). It is true ONLY while (a) the restored-hash key is unchanged (a new key gives every old message a new delivery key, so a replay looks new and starts a second run), and (b) the receipt rows survive (a database restored from a backup older than a receipt forgets it). [AUTHOR: wording]
- (a) has a start-up guard ALREADY in the ticket: AK-G2 BN-3 stores a keyed check value of the inbound key per source and, when it differs, refuses inbound (503, nothing lost) until a person copies the new check value into `inbound.key_check_ack`; after that acknowledgement, a retry of an older message can start a second paid run (AK-G2 lines 508-528, VERIFIED (read)). v4.2 said this guard was "not in ticket revision 3"; that was wrong (it is a build note, which wins over the body). The ticket's open choice is PENDING LEAD 9 (a: keep the derived key with this check, recommended; b: a dedicated inbound key). Whether the lead answered it: UNVERIFIED. [AUTHOR]
- Retention per data class is GAPS row G18's (retention and deletion policy per data class; AK-G2 line 101). Receipt rows grow by one per message with no end; size per row: NOT MEASURED.
- Erasure: a receipt holds a keyed hash of tenant, source and sender id, not text. Whether such a hash counts as personal data that a deletion request must reach: UNVERIFIED (not legal advice; R450(f)). GAPS row G18 owns the answer.

### 4.7 Rules that stay outside any no-code flow
- Money, irreversible actions, masking, approval decisions, audit, the spend wall, retry, dead-letter and idempotency keys never live inside a no-code flow; the flow calls a core module (R447, order 68 item 3).
- A no-code flow never holds approver or executor credentials (R447). A flow (n8n Wait node, a Make module, a Close task) may only NOTIFY a person. In v1 the only approval path is the approval channel (`approvals/receiver.py`), and the approval channel's secret may not equal any door secret (AK-G2 row C7), so a flow that holds its door secret cannot approve. The person-facing approval API with the person's own identity is AK-G15 and GAPS row G14 (the approvals screen; DEFERRED; G14 has no ticket); its negative test ("the flow's token cannot approve") belongs to them.
- Each flow (source) has its own signing secret (AK-G2 row C7). In n8n Community the secret sits in n8n's own credential store, because "external secrets" is a paid feature (lead-fetch); how n8n protects stored credentials: UNVERIFIED.
- Licence line for every quote and contract schedule (ruling 5), exact text: "The client runs n8n in the client's own account; Hadavin does not host or resell n8n. This line does not cover Hadavin building, changing or running flows inside the client's n8n for a fee; whether that is allowed is not confirmed yet." It is our reading of the Sustainable Use text, not legal advice ("not reviewed by counsel", R450(f)). The owner confirms or a lawyer checks before the first quote that names n8n (NEEDS-OWNER O1).

## 5. Module decisions (vocabulary: ADOPT / WRAP / KEEP-CODE / DROP)
Not re-examined by A18 (UNCHANGED from plan-v3 and its amendments): P0a, P0b, P0c, P0d, P0e, P4c, P5b3, P5b4 (DEFERRED, order 59), P6b2 (DEFERRED, order 59), P8a, P8b (DEFERRED), P8c, the plan-v3 v1.1 table (P2b to P7n), the secrets, signer, audit, channel and executor kinds (plan-v3 section 5, amendment A6), client invoicing (not a core module; scan-2 line 40), and the kit tickets AK2b, AK2c, AK2d, AK3, AK4b, AK5, AK7, AK8, AK-G14, AK-G22 and GAPS tickets G3, G9-G12, G18, G26. Order 68 item 5 lists the KEEP-CODE rows of those tickets as UNVERIFIED-KEEP, verified when each ticket is next touched.
"Scan verdict" = market-scan-2's verdict word, cover figure (0.5) and line; an A18 verdict that differs says why.

| Package (ticket) | Phase | Verdict | Status | Scan verdict | Reason |
|---|---|---|---|---|---|
| P1a, P1b look-alike folding (`tickets/P1.md`) | v1 | KEEP-CODE | IN PR (63, 70) | WRAP, 40-60 (line 26) | the scan's candidates are the standard library and Unicode's confusables data, not a library to wrap; our code reads that data (order 59 item 6(5)) and adds the named views and fold key. Standard NFKC alone keeps Cyrillic and zero-width characters (section 3.1) |
| P1c redactor gaps (`tickets/P1c.md`) | v1 or v1.1: UNVERIFIED (NEEDS-LEAD L14) [AUTHOR] | KEEP-CODE | TICKET FROZEN (revision 7), NOT STARTED; after P1b merges (order 70 item 1) | KEEP-CODE (line 26) | order 64: our chokepoint misses 6 of 30 hostile inputs; P1c closes the 3 base64 ones and the 2 partial host names and pins the bare number as a decided property |
| P2a stop state (`tickets/P2a.md`) | v1 | KEEP-CODE | TICKET FROZEN, NOT STARTED (P2a-1) | KEEP-CODE, guarantee 5-15 (line 33) | no cloud switch compared gives "the agent cannot clear it, a separate role resets it, audited" |
| P2d (`tickets/P2d.md`) | v1 | KEEP-CODE | IN PR (77 is P2d-1); on in v1, no extension (ruling 2) | KEEP-CODE if redaction is sold as a guarantee (line 27) | owner order 11 (line 24: the look-alike leak must be closed in core v1); order 19 E |
| P3a migration rule (`tickets/P3a.md`) | v1 | KEEP-CODE | IN PR (73) | WRAP (line 34) | no named migration tool was tested; built code is replaced only with evidence and the owner's yes (R448); no guarantee class named (section 6.1) [AUTHOR]; row UNVERIFIED-KEEP |
| P4a usage and price tiers (`tickets/P4a.md`) | v1 | KEEP-CODE | TICKET FROZEN, NOT STARTED | WRAP LiteLLM budgets (line 36), read as "data only" (Addendum A) | refuse instead of estimate. Prices = a pinned, dated snapshot table with price page URL and date per entry, never fetched at run time; LiteLLM's price file only as a cross-check (P4a BN-16), pinned by version and hash (section 6.2; lead item L12) [AUTHOR] |
| P4b1 meter (`tickets/P4b1.md`) | v1 | KEEP-CODE | TICKET FROZEN, NOT STARTED; T1 added to its evidence | KEEP-CODE, 0 (line 37) | the two tools examined overshoot by up to one call; our own check-then-charge admitted 50 of 50 (section 3.1). Order 35 item 1 Options paragraph (client's own gateway as a v1.1 adapter row) stands |
| P4b2 billing classes (`tickets/P4b2.md`) | v1 | KEEP-CODE | TICKET FROZEN, NOT STARTED | KEEP-CODE (line 38) | no billing statement for failed calls on the one page read; UNVERIFIED-KEEP |
| P4d store contract (`tickets/P4d.md`) | v1 | KEEP-CODE | IN PR (66 and the money chain) | KEEP-CODE (line 34) | money SQL (amendment A11) |
| P5a closed error codes (`tickets/P5a.md`) | v1 | KEEP-CODE (diagnostic record, hostile corpus, old-writers test); its codes table, validation text and mutant file: CUT-TO-CONFIG+GLUE planned as stdlib enum, pydantic and nothing (order 70 item 3), OWNER-OPEN (O10) [AUTHOR] | IN PR (80, parts) | KEEP-CODE (line 29) | order 70 item 3: stdlib logging, structlog and traceback printed the message 4 of 4 |
| P5b1 provider error plumbing (`tickets/P5b1.md`) | v1 | KEEP-CODE | IN PR (80) | WRAP, 55-65 (line 30) | the scan's own "cannot guarantee" column: billing-safe retry classification; OTel names are used only as a pin (status NOT READ); UNVERIFIED-KEEP |
| P5b2 redesign step R3a (`tickets/P5b2.md`) | v1 | KEEP-CODE | IN PR (85); OWNER-OPEN (O7) | ADOPT ast-grep, 85-90 (line 31) | the 85-90 is a judgement, not a count of need lines (R448 needs a count); built code is replaced only with the owner's yes. Cutting it also needs an amendment that rewrites P5c's Depends-on (plan-v3.md:149) |
| P5b5 redesign step R5 (`tickets/P5b5.md`) | v1 | if built: KEEP-CODE for the parts not moved; its rules 3 and 4 go to ruff banned-api (order 57 A.1) [AUTHOR] | DEFERRED (order 59 item 4(b)); OWNER-OPEN for the rest | ADOPT ast-grep (line 31) | not built. P5c's Depends-on names P5b5 (plan-v3.md:110) while P5b5 is DEFERRED: NEEDS-LEAD L5 |
| P5c redactor kind and wrapper (`tickets/P5c.md`) | v1 | KEEP-CODE (wrapper, put-back, pattern backend) | TICKET FROZEN, NOT STARTED | WRAP detector + KEEP-CODE wrapper (line 28) | detector WRAP overridden by order 64 (Presidio missed 13 of 30). Presidio = optional EXTRA layer that runs after our backend and can only mask more; never replaces it. Every backend passes the hostile set or is refused in pilot and prod (T3b), wired in only after P1c and the look-alike fix merge (L13). A Presidio layer needs the single-dependency check (section 6.2) and a refusal-rate bound in the P5c ticket (NEEDS-LEAD L6) [AUTHOR] |
| P6a profile check (`tickets/P6a.md`) | v1 | KEEP-CODE | IN PR (72) | none specific (line 35) | demo-stage kinds refused in pilot and prod; UNVERIFIED-KEEP |
| P6b1 no-training lock (`tickets/P6b1.md`) | v1 | KEEP-CODE | IN PR (86); OWNER-OPEN (O8) | DROP as code, "agent's weakest verdict" (line 41) | no counted evidence; laptop test 10,446 passed on Python 3.12 and 3.13 (order 138, VERIFIED (read)); owner may turn it into a config or doc check |
| P0t stage rename (`tickets/P0t.md`) | v1 | KEEP-CODE | follow-up IN PR (83) | DROP "shipped" (line 53) | R449 owner rule; "shipped" means PR 67 merged: UNVERIFIED here |
| AK-G2-a ledger | kit | KEEP-CODE | ACTIVE TICKET (`freeze-list.md:48`, order 59 item 4); start released only by a lead order after the open chain merges (ruling 9) and after P8c (amendment A10) (L8, L10) [AUTHOR] | KEEP-CODE (line 43) | see rung table |
| AK-G2-a claim, lease, retry | kit | KEEP-CODE | as above | Addendum B: WRAP pg-boss or Graphile Worker | ruling 3 overrides: Node libraries in a Python core, and a second job table beside our compare-and-set store (pass 4 key finding). pg-boss and Graphile Worker appear only as a named OUTLINE for a client who already runs one (start condition: the client asks) |
| AK-G2 reconciliation (`compare_ids`, `list_inbound`) [AUTHOR] | kit | no verdict: OUT of AK-G2-a scope (cut by AK-G2 BN-14, moved to AK-G2 row V7 inside AK-G15) | DEFERRED with AK-G15 | (no row) | v1 has no reconciliation code (section 4.5); owner item O3 decides: accept for v1, remove the promise, or build V7 before the first pilot |
| AK-G2-b door | kit | KEEP-CODE | as AK-G2-a; the 4.4 option is not built (conditional) [AUTHOR] | (no row) | see rung table; UNVERIFIED-KEEP |
| AK1b outbound gate | kit | KEEP-CODE | ACTIVE TICKET | KEEP-CODE, 0 (line 49) | no product gives one outbound gate |
| AK1 tenant isolation mechanism | kit | ADOPT (Postgres features: tenant column in every key; RLS FORCE where one database holds several tenants, section 4.2) | ACTIVE TICKET | WRAP, 85-90 (line 48) | a database feature used as it is, so ADOPT, not WRAP |
| AK1 tenant isolation tests | kit | KEEP-CODE | ACTIVE TICKET | (same line) | cross-tenant negative tests and canaries (R369) are ours |
| AK-G15 needs-a-person queue | kit | if built: KEEP-CODE (store, digest binding, separate executor role) [AUTHOR] | DEFERRED | WRAP waits + KEEP-CODE store (line 44) | the client's tool may only notify (section 4.7) |
| AK-G1 conversation hand-off lock [AUTHOR: was "hand-off lease"] | kit | if built: KEEP-CODE | DEFERRED | KEEP-CODE for the lock (line 42; the scan says "lease") | no tool owns a conversation lock |
| AK-G16 deploy into the client's cloud | kit | if built: ADOPT (Helm, Kustomize, OpenTofu, wrangler, CDK mechanics) [AUTHOR] | DEFERRED | ADOPT (line 45) | the five-part split stays ours |
| AK2a document reader | kit | if built: WRAP docling or pypdf [AUTHOR] | DEFERRED | WRAP (line 50) | docling licence: UNVERIFIED |
| AK4a eval gates | kit | if built: WRAP DeepEval or Langfuse scoring [AUTHOR] | DEFERRED | (line 51) | release gate ours; promptfoo ownership UNVERIFIED |
| AK0 research note | kit | no verdict (not examined) [AUTHOR: was "n/a"] | DEFERRED (order 59) | DROP (line 47) | a lead decision deferred it; the scan's DROP is not a decision |
| JG-3 notifier | Jagrat | no verdict (not examined) [AUTHOR: was "n/a"] | PAUSED | DROP (line 46) | |
| Template packs (n8n, Make, Activepieces) | kit, after AK-G2-b | ADOPT (the client's tool as it is, plus exported flows and glue under 50 lines) | built only for a tool a client has chosen (order 57 A.2), and only IN-direction until the OUT contract exists (NEEDS-LEAD L2) | (no row) | nothing that connects is removed (owner decision 3); T5 decides per tool whether the tool can sign |
| Portal screen | later | ADOPT (the client's own tool reads a read-only database role) | OWNER-OPEN per client | (no row) | a portal tool such as Appsmith is also priced per user above 5 users (section 7.4), so it has the same seat-price problem as owner decision 2; Port or Retool only if the client already has them |

## 6. Rung table and single-dependency audit

### 6.1 Rung table (R448 tokens only) [AUTHOR: columns "guarantee class" and "single failing property" added; every row re-checked]
Columns: rungs tried (0 = client's own tool, then 1 to 4; "0: none" = no client yet, nothing to exclude); guarantee class = the item of the R447 list (0.4) the row protects, or "none named"; single failing property = the ONE property the higher rung fails, which must NOT also be true of our own design; reproduction = a failing test, or a doc quote with its URL, or the word UNVERIFIED with what blocks it. One verdict per row. A verdict resting on an UNVERIFIED cell must be verified before that ticket's build start (R448). Rows for DEFERRED or PAUSED items are not in this table: they are not built (section 5).

| Component | Need | Guarantee class | Rungs tried | Single failing property | Reproduction | What only our code gives | Verdict |
|---|---|---|---|---|---|---|---|
| Ledger (AK-G2-a) | the same delivery key never starts work twice, with no time limit | no lost or double-applied message | 0: none; 1 n8n (no dedupe store: "build dedupe yourself", S, scan-2); 2 dealdesk `inbox.py` promoted (AK-G2 line 137); 3 SQS FIFO, Cloud Tasks, Pub/Sub, Cloudflare Queues/Workflows; 4 pg-boss, Graphile, Procrastinate | the tool forgets a key after its dedupe window or when the job ends. SQS FIFO: after 5 minutes. Graphile: a completed job's key is deleted | SQS: quote "within the 5-minute deduplication interval" (lead-fetch, 2026-11-07); URL UNVERIFIED (lead-fetch records no URL per fact; the page requested was `market-scan-2.md:96`, marked "URL from memory"). Graphile: "no permanent job_key log", raw repo file `website/docs/job-key.md` of graphile/worker, read 2026-11-07 (`market-scan-2.md:907`, `:910`); full URL not printed: UNVERIFIED | a permanent receipt row in the SAME database as the run row; the run id derived from the key makes a second run impossible (not one shared transaction, section 4.3) | KEEP-CODE |
| Claim, lease, retry (AK-G2-a) | one worker per receipt; retry after a crash | no lost or double-applied message | 0: none; 2 our tick compare-and-set (`tick.py:17`); 4 pg-boss (Node), Graphile (Node), Procrastinate (Python) | Graphile: a job added with the same key while the first job runs creates a SECOND job. pg-boss: none reproduced. (Fixed in v4.3: "stalled jobs stay stuck until a periodic task retries them" is also true of our design, whose expired leases are taken again by the tick; "runs on Node" is a runtime fact, not a guarantee property) | Graphile: `job-key.md` as above, `market-scan-2.md:907` and `:910`, summary line 864, URL UNVERIFIED. pg-boss: UNVERIFIED (the scan's reading of `docs/api/jobs.md`, "not tested", `market-scan-2.md:899`) | the lease as a compare-and-set on the receipt row itself: one state record per message | KEEP-CODE (ruling 3; UNVERIFIED-KEEP against pg-boss) |
| Door (AK-G2-b) | signed request in, refused before parse, receipt committed before 202, empty replies | no lost or double-applied message; least privilege (deny by default) | 0: none; 1 n8n webhook node; 3 Svix, Hookdeck: NOT searched (scan-2 line 10) | none reproduced (n8n publishes no statement that a request is stored before the reply: an absence, not a reproduced failure) | UNVERIFIED. Blocked by: a forced-kill test of n8n's webhook node or a read of the Svix and Hookdeck docs (order 57 A said "not worth the time now") | signature before parse, deny by default, commit before 202 | KEEP-CODE (UNVERIFIED-KEEP) |
| Redactor pattern backend (P5c) | find personal data and secrets before the model | redaction before the model | 0: none; 2 our `runmap.redact_text`; 4 Presidio, GLiNER, LLM Guard, scrubadub, detect-secrets, gitleaks | Presidio default: misses 13 of 30 hostile inputs and alters 7 of 14 must-keep lines | failing test result `evidence/redactor-eval/lead-reading-1.md:4` (test 2026-11-06; one test, home advantage); test scripts not in this checkout, so a re-run is blocked | coverage on our hostile set; ours also fails 6 of 30 today (T3b) | KEEP-CODE |
| Redactor wrapper and put-back (P5c) | mask before the model, no model call after a redactor error, restore in code | redaction before the model | 3 Cloudflare DLP, Bedrock, Azure, GCP filters | Cloudflare DLP: offers only Flag and Block, no mask-and-restore | VERIFIED-SRC, docs source file `ai-gateway/features/dlp/set-up-dlp.mdx`, 2026-11-07 (scan-2 section 5 item 1); URL UNVERIFIED (path only). Others: UNVERIFIED (snippets) | fail closed and restore in our code | KEEP-CODE |
| Look-alike folding (P1a, P1b) | a folded copy of a known value cannot reach a model | redaction before the model | 3 stdlib `unicodedata` NFKC; Unicode confusables data (used as input, order 59 item 6(5)) | NFKC keeps Cyrillic U+0430 and a zero-width space | my test, python 3.13.18, re-run 2026-11-07 (section 3.1) | named views and fold key on top of the data | KEEP-CODE |
| Hidden-copy refusal (P2d) | refuse the whole text when a folded known value survived masking | redaction before the model | 4 guardrail classifiers (scan-2 line 27, "low, ~30") | none reproduced against a tool; the need is owner order 11 (the lead's test: look-alike copies leaked through core main) | UNVERIFIED | the whole-text refusal | KEEP-CODE (UNVERIFIED-KEEP; built) |
| Migration rule (P3a) | forward-only numbering; the previous release reads the new schema or fails loudly | none named (closest: no lost message across a release) | 3 "Postgres migration tools" (scan-2 line 34, none named) | none reproduced | UNVERIFIED: no tool named or tested | the downgrade-read test | KEEP-CODE as built: R448's condition (a named guarantee) is NOT met; kept only because built code is replaced only with evidence and the owner's yes (UNVERIFIED-KEEP) |
| Usage and prices (P4a) | refuse instead of estimate; dated exact prices | exact money and budget caps | 3 LiteLLM budgets and price file | LiteLLM price file: prices as JSON floats with no per-entry date | P4a BN-15 (`pip download litellm --no-deps`, 1.108.1, 2026-11-06: a package read, no URL needed); proxy releases 1.82.7 and 1.82.8 malicious (lead-fetch) | refuse instead of estimate; pinned dated price table | KEEP-CODE |
| Spend meter (P4b1) | never admit more than the cap under concurrent calls | exact money and budget caps | 3 LiteLLM key budget; 3 Cloudflare AI Gateway spend limit; 2 our `Limits` | the tool checks the cap before the call and books spend after it, so parallel calls pass the same check | LiteLLM 1.108.0: 50 parallel, cap USD 1.50, cost 1.00: 2 admitted, spend USD 2.00 (order 140 text, 2026-11-07; raw file not here); Cloudflare quote "a burst of concurrent requests can briefly exceed the limit" (VERIFIED-SRC, 2026-11-07; URL UNVERIFIED); our `Limits`: 50 of 50 at cap 2.00 (`tests/test_t1_meter_parallel.py` at `e00a047`, VERIFIED (read)) | reserve before the call in exact integers | KEEP-CODE |
| Billing classes (P4b2) | a refused or never-sent call is not counted | exact money and budget caps | 3 provider pages | the page states nothing about billing of failed calls | Claude errors page (lead-fetch, 2026-11-07; URL UNVERIFIED per fact); other vendors: UNVERIFIED. Blocked by: reading each used provider's billing page at P4b2 build start | the release rule | KEEP-CODE (UNVERIFIED-KEEP) |
| Store contract (P4d) | one contract over memory and Postgres | exact money and budget caps (the money SQL) | 3 test suites (none named, scan-2 line 34) | none reproduced | UNVERIFIED: no tool named | the contract suite and money SQL | KEEP-CODE (UNVERIFIED-KEEP; built) |
| Stop state (P2a) | the agent cannot clear the stop; reset by a separate role, audited | tenant isolation and least privilege (the agent cannot clear its own stop); exact budget caps (the stop) | 3 Cloudflare Durable Object + separate Worker, AWS IAM deny, Azure terminate | none reproduced (compared on docs, scan-2 line 33, guarantee 5-15) | UNVERIFIED. Blocked by: a test on one cloud needs a cloud account (owner's yes, no spend) | separate reset credential (amendment A14) | KEEP-CODE (UNVERIFIED-KEEP) |
| Diagnostic record (P5a) | no foreign text in a diagnostic | redaction (masking before logs; R447 names "before the model", the least-privilege rule adds logs) | 3 stdlib logging, structlog, traceback | each printed the message text, 4 of 4 | order 70 item 3 (the lead's test, 2026-11-06; raw output not here) | the closed diagnostic record | KEEP-CODE |
| P5a codes table, validation text, mutant file | closed codes; safe validation text | none named | 3 stdlib enum; pydantic | (a tool covers it) | order 70 item 3, "approved in principle", 2026-11-06 | nothing | CUT-TO-CONFIG+GLUE (OWNER-OPEN, O10) [AUTHOR: was a final CUT-TO-CONFIG+GLUE] |
| Provider error plumbing (P5b1) | billing-safe retry classes | exact money and budget caps | 3 OTel `error.type`; SDK exception classes | none reproduced; the scan lists the classification as what it cannot give (line 30) | UNVERIFIED: OTel page NOT READ | the class table | KEEP-CODE (UNVERIFIED-KEEP; built) |
| ConfigError site table (P5b2, redesign step R3a) | classify every `ConfigError` site; CI fails on a new one | none named (a CI hygiene check) | 3 ast-grep, Semgrep CE, Opengrep | none reproduced | UNVERIFIED: the 85-90 is a judgement; no count of need lines against ast-grep rules exists. Blocked by: that count (R448: the author counts, the lead settles) | the class judgement LITERAL/OPERATOR/FOREIGN (142 unproven-origin class judgements, LEAD-ORDERS.md lines 889-892) | KEEP-CODE (OWNER-OPEN, O7; R448's condition NOT met; kept as built) |
| P5b5 rules 3 and 4 | ban old error-text calls | none named | 3 ruff banned-api | (a tool covers it) | order 57 A.1, accepted, 2026-11-06 | nothing | CUT-TO-CONFIG+GLUE |
| Profile check (P6a) | demo-stage kinds refused in pilot and prod | tenant isolation and least privilege | 3 config validation (scan 1 only) | none reproduced | UNVERIFIED: no tool named | the cross-check list | KEEP-CODE (UNVERIFIED-KEEP; built) |
| No-training lock (P6b1) | the llm kind refuses a provider setting that allows training | none named in the R447 list (closest: R371, no client's data used for other work) | 3 provider terms plus a config check | none reproduced | UNVERIFIED: scan-2 line 41 gives no cover figure | the lock in the llm kind | KEEP-CODE (OWNER-OPEN, O8; R448's condition NOT met; built) |
| Outbound gate (AK1b) | masking before every outbound call | redaction before the model | none found (scan-2 line 49) | none reproduced | UNVERIFIED | the one gate | KEEP-CODE (UNVERIFIED-KEEP) |
| Tenant isolation mechanism (AK1) | a tenant reads nothing of another | tenant isolation and least privilege | 3 Postgres tenant keys; RLS FORCE | (the tool is adopted) | UNVERIFIED: Postgres docs not re-read here; verify before AK1 build start [AUTHOR] | nothing | CUT-TO-CONFIG+GLUE (UNVERIFIED) |
| Tenant isolation tests (AK1) | prove the above | tenant isolation and least privilege; eval gates | 3 none | none reproduced (no tool searched for one) | UNVERIFIED [AUTHOR: v4.2 had no marker] | negative tests and canaries (R369) | KEEP-CODE (UNVERIFIED-KEEP) |
| Template packs | the client's tool signs and sends to the door; shows notices | none (plumbing) | 0 the client's chosen tool; 1 n8n, Make, Activepieces | whether each tool can sign and re-sign: UNKNOWN | UNVERIFIED until the T5 trial | the contract tests (T5) | CUT-TO-CONFIG+GLUE (UNVERIFIED) |
| Portal screen | people see items | none (display) | 0 the client's own tool with a read-only role; 1/3 Appsmith (Apache-2.0) | Appsmith per-user price above 5 users | lead-fetch, 2026-11-07 (URL UNVERIFIED per fact) | the read-only role and digest binding | CUT-TO-CONFIG+GLUE |

**Open at build start (rows whose verdict rests on an UNVERIFIED cell; each must be verified before that ticket's build start, R448, order 68 item 5):** Door, Claim/lease (pg-boss), Hidden-copy refusal, P3a, P4b2, P4d, P2a, P5b1, P5b2, P6a, P6b1, AK1b, Tenant mechanism, Tenant tests, Template packs; plus the missing URLs of the SQS, Graphile, Cloudflare DLP, Cloudflare spend-limit, Claude errors and Appsmith quotes. [AUTHOR]
**KEEP-CODE rows that name no guarantee class:** P3a, P5b2, P6b1. Under R448 their KEEP-CODE is valid only as "built code is not replaced without evidence and the owner's yes"; they are not proof that our code is needed. [AUTHOR]
Rows for the audit, signer, secrets, channel and executor kinds: not re-examined (UNCHANGED, plan-v3 section 5); order 68 item 5 marks their KEEP-CODE rows UNVERIFIED-KEEP. Licence, version and date of each tool named above: in the scan lines cited; A18 adds no tool to a client build, so the R450(d) licence check is done when a ticket adds one.

### 6.2 Single-dependency audit (repo CLAUDE.md "No single dependency"; R363) [AUTHOR: new section]
Each external dependency of the parts this plan touches, its kind, its neutral default, its alternative (built, or a written outline with its start condition), and what is still open.

| Dependency | Kind / place | Default | Alternative and start condition | Open, and who decides |
|---|---|---|---|---|
| Postgres (the only store for pilot and prod on the ledger, claim/lease, run rows, the meter's reservations and RLS) | `store` kind | Postgres (self-hostable) | memory store: demo stage only (P6a). Outline: SQLite store, plan-v3 v1.1 row P7l (plan-v3:78 and :145; AK-G2 row V10). Start conditions: plan-v3's "Intake moves onto the core meter", and order 145 item 2(d)'s "a client without Postgres". Until P7l exists and passes the ledger, claim and tenant contract rows, SQLite is refused for these paths in pilot and prod | **Proposed dated exception** (to be written into the rule register by the owner or the lead): "Postgres is the only pilot and prod store for inbound sources, spend reservations and multi-tenant row-level security; reason: these paths rely on `FOR UPDATE SKIP LOCKED`, `FORCE ROW LEVEL SECURITY` and database roles, which SQLite does not offer in the same form (SQLite facts not re-read here: UNVERIFIED); review_by 2027-01-31." NEEDS-OWNER O11 (owner yes) with NEEDS-LEAD L11 (the date and wording) |
| The door's host in pilot and prod | AK-G16 (DEFERRED) | none in v1: the door runs only in the demo-stage stdlib server `serve` (AK-G2 line 194) | none built; AK-G16 owns production hosting, rate and connection limits | the door is DEMO-ONLY in v1. No pilot or prod door exists until the owner lifts AK-G16 (NEEDS-OWNER O4) |
| The inbound key (delivery keys and body hashes) | derived from the single restored-hash key (AK-G2 PENDING LEAD 6 (c); line 153) | derived key plus the AK-G2 BN-3 key check: a changed key stops inbound until a person acknowledges the new check value (start-up guard); BN-3's runbook text: "Rotate the key only after every sender's retry horizon has passed ..." | AK-G2 PENDING LEAD 9 (b): a dedicated inbound key, so rotating the restored-hash key never touches inbound | whether the lead answered PENDING LEAD 9: UNVERIFIED. The guard and runbook exist in the ticket; nothing new is asked here |
| Signature scheme | `hmac_v0` (`approvals/hmac_v0.py`) | `hmac_v0` (open HMAC-SHA256) | AK-G2 row V4: per-sender schemes, start condition "a sender that cannot sign `hmac_v0` and cannot sit behind a forwarder" | none |
| The client's automation tool | outside the core (the client's) | the client's choice (R445, R446) | the door contract is tool-neutral: any sender that can sign, or a forwarder | one-tool risk is the client's, written into the quote (R446) |
| Make (SaaS, no self-host) | client's tool | n/a (client's choice) | **Exit plan** (R447 asks every quote naming Make for one): (1) message data: every delivered message is already stored on our side (receipts and bodies), so no message data is locked inside Make; (2) flows: whether Make can export a scenario as a file we can keep in git: UNVERIFIED (not read); (3) code alternative: the same door contract with n8n self-hosted, Activepieces, or a forwarder (AK-G2 line 195); (4) cost of a switch: NOT PRICED | the exit plan stays UNVERIFIED in part (2); no quote names Make until it is read (section 7.1) |
| n8n (fair-code) | client's tool | the client's own instance and licence (R450(d), (i)) | Make, Activepieces, or a forwarder (same door contract) | licence reading: NEEDS-OWNER O1 |
| Presidio (optional extra redactor layer) | `redactor` kind backend | our pattern backend (P5c) | Presidio only as an extra layer after ours; never the default (ruling 8) | before any client uses it: its own single-dependency and licence check, a refusal-rate bound and the hostile-set gate (T3b) in the P5c ticket (NEEDS-LEAD L6) |
| LiteLLM price file (cross-check only) | P4a price table input | the pinned, dated price table read from each vendor's price page (P4a BN-16) | none needed (cross-check only) | proposed P4a build note: pin the exact LiteLLM version and the sha256 of the downloaded wheel and of the JSON file; download wheels only (no source build, so no package code runs); never 1.82.7, 1.82.8 or 1.107.0 (section 3.1). NEEDS-LEAD L12 |
| The model vendor (Claude is the sold default) | `llm` kind | no default configured in code (`config.py:70`, amendment A6); Claude is the default we sell | four backends exist in code (anthropic, bedrock, openai_compat, gemini), all "unverified live" (amendment A6) | dated exception from the owner's no-single-dependency rule: "Claude is the sold default; the llm kind needs a second backend or a written outline with its start condition (dated exception, review_by 2027-01-31)" (`.claude/rules/no-single-dependency.md`). Nothing new is asked here; the exception is due for review on 2027-01-31 |

## 7. Cost model the quote must show (per client; the client pays licences) (ruling 6)
Rules: EUR and USD are never added together, never converted and never compared with each other; each currency has its own line. A yearly figure is printed next to every monthly price (per year = per month x 12). Model tokens are excluded (priced separately from the official price page for the workload). Every table in this section is a LOWER BOUND, NOT A QUOTE. "NOT READ" and "NOT PRICED" lines may not be quoted.

### 7.1 Automation tool (the client chooses one)

| Option | Per month | Per year | Executions or credits | Notes |
|---|---|---|---|---|
| n8n Cloud Starter | EUR 20 | EUR 240 | 2,500 executions a month | billed annually (lead-fetch); team features on Cloud: NOT READ |
| n8n Cloud Pro | EUR 50 | EUR 600 | 10,000 executions a month | billed annually; team features: NOT READ |
| n8n self-hosted Community | EUR 0 licence | EUR 0 licence; hosting NOT PRICED | no execution allowance stated | lacks the ten features listed in section 3.1 |
| n8n self-hosted Business | EUR 667 | EUR 8,004 | 40,000 per lead-fetch; whether that allowance applies to self-hosted: UNVERIFIED | self-hosted only; hosting NOT PRICED |
| Make | NOT READ | NOT READ | free plan 1,000 credits a month | do not quote; the quote must name the exit plan (R447: SaaS with no self-host; section 6.2) [AUTHOR] |
| Activepieces Plus (cloud) | USD 20 | USD 240 | 10,000 credits a month (lead-fetch) | an option, not a default (section 2); self-hosted MIT core: hosting NOT PRICED |

Volume check: the reference small client (`market-scan-2.md:267`) has about 3,000 inbound messages and 300 approvals a month. At one execution each that is at least 3,300 executions a month, above Cloud Starter's 2,500. At two or more executions per message (an estimate from round-1 design F16, UNVERIFIED) it is at least 6,300, under Pro's 10,000. What n8n charges or does above the allowance: NOT READ (scan-2 cites one aggregator saying over-limit executions are not queued on Starter and Pro: UNVERIFIED).

### 7.2 Our part, in the client's own cloud

| Item | Per month | Per year | Notes |
|---|---|---|---|
| Door stack: a Python runtime for `triggers/webhook.py` and the core, plus Postgres (section 4.2) | NOT PRICED | NOT PRICED | no price page for a Python host or a managed Postgres is in this checkout. In v1 the door has only a demo-stage server; pilot and prod hosting is AK-G16 (DEFERRED), NEEDS-OWNER O4 |
| Presidio extra layer (only if the client wants it) | NOT PRICED | NOT PRICED | container hosting |

Door stack: NOT PRICED.

### 7.3 Known licence lines per tier (LOWER BOUND, NOT A QUOTE; door stack: NOT PRICED in every row) [AUTHOR: "none known" replaced]

| Tier | EUR per year | USD per year | Not included |
|---|---|---|---|
| n8n Cloud Starter | 240 | no USD price (EUR tool) | door stack (NOT PRICED), tokens, execution overage; too small for the reference volume |
| n8n Cloud Pro | 600 | no USD price (EUR tool) | door stack (NOT PRICED), tokens |
| n8n self-hosted Community | 0 | no USD price (EUR tool) | n8n hosting, door stack (both NOT PRICED), tokens; missing team features |
| n8n self-hosted Business | 8,004 | no USD price (EUR tool) | n8n hosting, door stack (NOT PRICED), tokens |
| Activepieces Plus | no EUR price (USD tool) | 240 | door stack (NOT PRICED), tokens |
| Make | NOT READ | NOT READ | everything |

No total is printed: the door stack is not priced, so any total would look like a price and is not one. Whether a small client pays for the door stack at all, or the build offers a no-door option (n8n alone, no guarantee-class part), is a commercial choice: NEEDS-OWNER O4.

### 7.4 Seat-priced tools (shown only when the client asked for that tool; per year = unit x seats x 12)

| Tool | Unit price | Example per year | Marker |
|---|---|---|---|
| Port | USD 30 per seat per month (Basic, annual); free up to 5 seats | 10 seats: USD 3,600 if all 10 are billed; USD 1,800 if the first 5 stay free | which applies: NOT READ |
| Retool Business | USD 50 (annual) or 65 (monthly) per builder per month | 1 builder: USD 600 or 780 | lead-fetch |
| Appsmith Business | USD 15 per user per month; free up to 5 users | 10 users: USD 1,800 if all 10 are billed; USD 900 if the first 5 stay free | which applies: NOT READ |
| Langfuse Enterprise (audit logs) | USD 2,499 per month | USD 29,988 | whether a self-hosted Enterprise licence key costs the same: UNVERIFIED |

## 8. Tests (made-up data, no real keys, no real money, no live model call)
Every test below that sits on a money, redaction or security path blocks its package's merge when it fails; none of them waits for the owner.

### T1 spend cap: our own meter, 50 at once (package P4b1, store package P4d; owner of the tests: the P4b1 builder) [AUTHOR: owner named]
- Where today: branch `core/T1-T2-tests` at `e00a047` (no pull request): `tests/test_t1_meter_cap.py`, `tests/test_t1_meter_parallel.py`, `tests/meter_support.py`, `tests/meter_mutants.py` (VERIFIED (read): file list). Those tests run 50 threads against main's `Limits` on the memory store; 4 fail on purpose (real finding, order 142 item 3). They stay as they are, failing, until P4b1 merges; then they must pass, never xfail.
- API under test, from the P4b1 ticket (VERIFIED (read), lines 98-104): `Meter.reserve(agent_id, worst, caps, *, run_id=None) -> Hold`, `Meter.settle(id, actual)`, the context manager `Meter.hold(...)` with `h.record(actual, measured=...)`, and `Limits.hold` (P4b1 line 107). Unless a case says otherwise: ONE agent id (made up, for example `agent-t1`), `Caps(day=C, month=None, run=None)`, `run_id=None` (allowed because `caps.run` is `None`, P4b1 line 98), the memory store. [AUTHOR]
- The exact rule, from the P4b1 ticket: a reservation of W is granted only when, for each set cap (run, day, month), settled spend plus open reservations plus W is at most the cap; exactly at the cap passes, one micro-dollar over is refused and writes nothing (P4b1 test T2.3, parity row P1). A refused reservation makes no provider call. When every granted hold stays open until all callers have answered, the number granted EQUALS floor(cap / W), exactly; "a meter that always refuses must fail" (P4b1 test T5.1). Overshoot happens only when a call's real cost is higher than its reservation; then the settle books the full real cost in the run, day and month counters alike, signals `overshoot`, and the next reservation is refused (P4b1 line 104).
- Weakness to fix in the branch, found while reading it: its parallel test asserts "at most floor" (line 38), and another test is named "overshoot a non-multiple cap by less than one call" (line 45), which accepts overshoot. When P4b1 lands, add equality and zero-overshoot assertions next to them (adding, not weakening; order 142 item 3 keeps the old tests).
- Cases (cap C and worst case W in integer micro-dollars):
  - T1.1 50 threads, memory store, barrier, all holds open until a second barrier: C = 2,000,000, W = 1,000,000: exactly 2 granted, 48 `OverBudget`, the stub provider called exactly 2 times, day counter 2,000,000 at the second barrier. Repeat with C = 50 x W (50 granted), C = 50 x W - 1 (49 granted), C = W - 1 (0 granted).
  - T1.2 settle below: after the second barrier each hold settles at half; the counter equals the sum of halves; then exactly floor((C - counter) / W) more reservations are granted.
  - T1.3 settle above [AUTHOR: wording]: with a cap at or below the booked total (for example C = 1,000 with W = 20): reserve 20 through `Meter.hold`, record an actual of 2,000 with `h.record(SpendMicro(2_000), measured=True)`: the settle books 2,000 (P4d never refuses an excess), overshoot 1,980, `on_overshoot` called exactly once (only a `measured` hold signals, P4b1 test T1.20), the day and month counters each rise by 2,000, and the next reservation is refused (P4b1 parity row P10).
  - T1.4 failure inside `reserve` [AUTHOR: rewritten; order 145 item 2(f)]: at P4b1 merge there is NO caller-level release: for a call that was SENT, P4b1 never releases (P4b1 line 48, caller rule; P4b1 row B16: "No `Hold.release` and no `release_spend` for a SENT call ... until P4b2"). The only releases of a never-sent call are inside `reserve` itself, by its release table (P4b1 lines 33-47): on `StoreBusy` or an unknown store outcome, `reserve` makes ONE best-effort `release_spend` with the same id, and the counter is back to its value before the attempt (P4b1 tests T1.12, T1.13); on a P4d refusal (`SpendCapExceeded`, `KillSwitchOn`) or a conflict it releases nothing. A SENT call that then fails settles at the reserved worst case. This case can pass at P4b1 merge.
  - T1.4b (moved to P4b2) [AUTHOR]: a sent call that the provider refused with a non-billing error is released by P4b2's classification. Written and run with P4b2, not at P4b1 merge.
  - T1.5 crash between reserve and settle: one process killed with SIGKILL inside the hold after reserving: the reservation stays open at the worst case; another process settles it with `settle(id, None)` and the counter stays at the worst case (P4b1 test T5.3).
  - T1.6 50 processes on Postgres [AUTHOR: harness and fallback]: 50 OS processes, each with its own connection and `Meter`, a process barrier, C = 2,000,000, W = 1,000,000: exactly 2 granted. Harness as P4b1 test T5 (P4b1 line 168): `pg_schema(runtime=True)` from `tests/contracts/kinds/store_postgres.py`, `multiprocessing.get_context("spawn")`, the DSN from `HADAVIN_TEST_PG_DSN` built from parts, `HADAVIN_REQUIRE_PG=1` so a skipped test is a FAILED evidence run. Postgres: the CI image is `postgres:17.10` (`ci.yml:40`, VERIFIED (read)); PostgreSQL 16 binaries exist in the cloud box (q334). Connections: 50 processes need about 55 connections (50 workers plus the harness and fixture connections); PostgreSQL's default `max_connections` is 100 (UNVERIFIED here, section 3.2). Where the server allows fewer, the test runs 8 processes (the shape of P4b1 test T5.1) and the evidence file records the limit and why; it never skips silently. Runs alone (no parallel heavy job; on the laptop through the heavy-slot tool).
  - T1.7 mutants, each must be killed [AUTHOR: mapped to ticket mutant ids]: (a) a meter that always refuses = P4b1 mutant M24 ("`reserve` raises `OverBudget` without calling the store", killed by P4b1 tests T5.1 and T2.8); (b) a non-atomic check-then-reserve = P4d-b mutants b4 ("cap checked in Python before the write") and b12 ("memory: lock removed from `reserve_spend`"); (c) `<=` turned into `<` = P4d-b mutant b3. (b) and (c) live in the store, so they are P4d-b's mutants (P4d lines 200-214, VERIFIED (read)); the P4b1 evidence runner plants them once more and T1.1 and T1.6 must kill them too.
- How "never above the cap at any moment" is measured: with all holds open until the second barrier, the peak is at that barrier; assert counter <= C there and counter = granted x W.
- Adds to, and does not replace, the plan-v3 section 8 (b) eight-process Postgres race (P4b1 test T5.1).
- LiteLLM comparison, not a gate: the lead's test (order 140, 2026-11-07, laptop, LiteLLM 1.108.0 official image `main-stable`, sealed network, stub provider, key cap USD 1.50, call cost USD 1.00): 10 calls one at a time, 2 admitted, overshoot USD 0.50; 50 parallel with a 2 s stub, 2 admitted, final spend USD 2.00. Slow-provider test (25 s stub): PENDING, on the lead's side, no date. The cloud session runs no LiteLLM code. Earlier (order 35, 2026-11-06, LiteLLM 1.108.1): 20 at once, 1 admitted, 19 refused, no overshoot seen; several workers and streaming not tested.

### T2 receipt ledger replay (package AK-G2-a; written and run WITH AK-G2-a, because the receipt ledger does not exist on main; the T2 on branch `core/T1-T2-tests` tests the meter's SPEND TOTALS, not the ledger, q335) [AUTHOR: wording]
- Layer and entry point [AUTHOR: one entry point]: `Inbox.receive` (the ledger's choke point, which builds the receipt and calls `receive_inbound(rec, body, *, max_reuse, max_open)`), and `Inbox.dispatch(sources, steps)` (AK-G2 BN-1) for the dispatch between replays. The door and signatures are NOT in T2. Fixtures: the AK-G2-a test fixtures of `tests/test_inbound_ledger.py` (sources, fake step, fake model, settings), so T2 builds no receipt by hand.
- Clock: the fake clock passed to `Inbox(..., clock, monotonic, ...)` and the `now` argument of `claim_inbound` (AK-G2 lines 163, 180). Postgres check [AUTHOR]: the test moves the fake clock 30 days ahead of the database server's clock; every result must be the same as with equal clocks (time comes only from the injected clock).
- Stores: the memory store and Postgres (17.10 in CI, `ci.yml:40`; 16 also, as AK-G2 row L15).
- Replays, each offset from t0 (not added up): deliver D = (key K, body B) at t0: `new`. Replay K, B at t0 + 5 min + 1 s (SQS FIFO), t0 + 24 h + 1 min (Cloud Tasks), t0 + 14 d + 1 min (Cloudflare Queues Paid maximum), t0 + 30 d + 1 min (Cloudflare Workflows maximum): each `duplicate`; one receipt row; after one dispatch between replays (the ticket fixture's fake step and lease time, 360 s for the 4-step fake agent per AK-G2 BN-17), one run row for `run_id_for(K, 0)`.
- Conflict: at t0 + 30 d + 1 min, K with body B' (B with one byte changed): `conflict` (409 at the door); the first receipt is unchanged.
- Same-key race (Postgres, 8 connections, barrier): 8 receives of K, B: exactly one `new`, seven `duplicate`, one row. Mixed race: one with B, one with B': one `new`, one `conflict`.
- Crash points on the ledger layer, using the ticket's own fault hooks (no new mechanism) [AUTHOR: round-3 readiness BLOCKER]: (a) store raises before the commit = the fault injected in the body insert of AK-G2 row L1: no row; the retry gets `new`; (b) store raises after the write, outcome unknown to the caller = the spy store of AK-G2 row W2 that commits and then raises (on Postgres a wrapper around the store object): the retry gets `duplicate`; (c) crash after the run was created and before `finish_inbound` = the crash injection of AK-G2 rows D1 and D5 (iii): after the lease, dispatch finds the run, the receipt ends `done`, one run. The crash "after the 202 reply" is a door case and is in T5.
- Key cases [AUTHOR: (d)-(f) mechanisms; (e) follows AK-G2 BN-3]: (d) restart with the same restored-hash key = a NEW `Inbox` over the same store (memory: the same store object; Postgres: a new connection): `duplicate`. (e) a CHANGED key = a new `Inbox` built with another key over the same store: `receive` raises `InboundKeyChanged`, nothing is written, dispatch claims nothing for that source (AK-G2 row L20 (ii)); then with `key_check_ack` set to the new check value, the replay gets `new` and would start a second run: the test pins this acknowledged hazard (AK-G2 row L20 (iii) plus one replay). (f) restore from a backup taken before D: Postgres only, delete D's receipt and body rows as the table owner (not the runtime role) to stand for the restore; the replay gets `new` (pinned; runbook warning; not prevented). On the memory store (f) is a new empty store and says nothing new; it is not run there.
- Hard schema criterion (Postgres): `inbound_receipts` has no column whose name contains `expir`, `ttl` or `delete`; `has_table_privilege` gives false for DELETE on `inbound_receipts` for the runtime role and the purge role (the roles of AK-G2 row L14); the receipt write guard of AK-G2 line 175 exists (AK-G2 row L15 tests its rules); `git grep -n "DELETE FROM inbound_receipts" -- src/` finds nothing. [AUTHOR: names]
- T2b, signature age limit (package AK-G2-b): limit 300 s (`hmac_v0.py:19`, VERIFIED (read)), HMAC-SHA256 over `v0:` + timestamp + `:` + body, secrets from config through the secrets kind, built from parts in tests. A fresh signature reaches the ledger. The same request at +301 s: 401, also when the receipt exists (AK-G2 line 223, row W1; the frozen rule, section 4.4). Only if the conditional option of 4.4 is adopted later do its rows W18-W28 replace this case for an existing receipt. [AUTHOR]

### T3 mask failure (package P5c)
- T3a, each must end with ZERO provider calls and the run handed to a person: the detector raises; the detector exceeds its time limit (the P5c ticket names the time budget `defaults.REDACT_BUDGET_S`, applied per `redact_text` call, `tickets/P5c.md:284`, VERIFIED (read); which P5c rows test the overrun: NOT CHECKED, the builder maps it or adds a build note) [AUTHOR]; put-back fails (a placeholder in the reply has no entry in the map, or the map is missing): the reply is held for a person, no placeholder text is delivered as if real, no second model call. Hook points (where the test injects each fault): NOT CHECKED in the P5c ticket; the builder names them in a build note before writing T3a.
- The case "the detector returns nothing for a hostile text" cannot be seen at run time. It is caught by T3b (before release) and, for a known value, by P2d's whole-text refusal.
- T3b hostile-set gate, for EVERY redactor backend including our default: all 30 hostile inputs and all 48 must-mask lines FULL, all 14 must-keep lines KEPT, except rows the lead has written down as an accepted property. [AUTHOR from here] The runner is P1c's permanent corpus test (order 64 item 5; `tickets/P1c.md:57`): the corpus copied into the repo as data with the span-level rule of `score_common.py`; known misses are strict xfail with their owner ticket. The accepted property is written in `guard/redact.py`'s module docstring and pinned by `test_redactor_accepted_properties.py` and `test_accepted_property_bare_number_not_masked_order64_item4` (P1c lines 41, 57, 106).
- **The six misses of our own default today, each with its disposition:** (1, 2) the Cyrillic look-alike e-mail and key (hostile rows 14 and 15): strict xfail; owner P2d-1's fold scan per order 70 item 1 and `tickets/P1c.md:57`, while order 64 item 2 named P1b (NEEDS-LEAD L13); (3-5) three base64-encoded values (hostile rows 25-27): closed by P1c's decoded view; (6) **the sixth miss is hostile row 6, "ref 55556666 paid", a bare number with no context**: NOT masked by decision (order 64 item 4, an accepted property), so it counts as passed once the property is written and pinned. The two PARTIAL must-mask lines (host names keeping ".example") are closed by P1c's whole-host-name rule. So the pilot and prod stages refuse our own default redactor until P1c and the look-alike fix have merged (order 145 item 2(c)); after that our default is expected to pass (27 FULL plus 2 fixed look-alike rows plus 1 accepted; expected, not measured).
- **Wiring rule (deadlock risk):** T3b must NOT be wired into the P6a pilot and prod cross-check before P1c and the look-alike fix have merged and the bare-number property is pinned. Wired earlier, it would refuse every redactor we have (our default scores 24 of 30 today, Presidio 14 of 30), so pilot and prod could not start at all. NEEDS-LEAD L13.
- Presidio: order 145 item 2(c) calls Presidio "the optional stronger backend". CONTESTED wording: on the only test in this checkout Presidio is WEAKER than ours on our corpus (14/3/13 hostile and 7 of 14 must-keep lines altered, against our 24/0/6 and 0 altered; with 4 custom recognisers 23/2/5, still 7 altered; section 3.1), so it would also fail T3b. A18 keeps ruling 8's wording: Presidio is an OPTIONAL EXTRA layer after our backend that can only mask more. NEEDS-LEAD L15.

### T4 stop (package P2a)
Each attempt is denied AND leaves an audit row: the agent's role calls the reset; the runtime role writes the stop table directly (UPDATE and DELETE); a config value or start-up flag that would clear the stop. Whether the P2a ticket rows already cover each, and the table and column names: NOT CHECKED line by line (the P2a ticket was not read for v4.3); the builder maps each attempt to a P2a ticket row, or adds a build note naming a new test file, before build start. [AUTHOR: build-time item made explicit]

### T5 door contract per tool (template packs; after AK-G2-b; a TRIAL per tool, not a promise) [AUTHOR: order, statuses, recording]
- Order: the manual trial comes FIRST, because the offline test replays recordings that only the trial produces.
- Per-tool re-sign trial, manual, outside CI: (i) can the tool compute HMAC-SHA256 over `v0:` + timestamp + `:` + body; (ii) on its own retry, does it send a fresh signature or the first one unchanged, and how long after the first attempt does its last retry come; (iii) is the retried body byte for byte the same. Recording format: one file per tool and date, `evidence/T5/<tool>-<yyyy-mm-dd>.md`, with the tool name and version, the three answers, the measured retry delays, and the raw request headers and bodies of each attempt with the secret replaced by a placeholder. n8n: a local container (owner rule 5b allows local containers on made-up data). Activepieces: a local container of the MIT core with the `ee` parts not enabled (where the `ee` boundary lies in a running build: UNVERIFIED). Make: cannot be self-hosted; it needs a real account and network, which needs the owner's yes (NEEDS-OWNER O6). A tool that cannot sign gets no pack, or a forwarder, or the ticket's own-scheme outline (AK-G2 row V4); this is decided per client. Answer (ii) is the input to lead item L17 (the 4.4 option).
- Offline, in CI (CI has no internet, plan-v3 rule 9(d)), from the recordings, with the expected door status from AK-G2 Interface 7 (line 194): signed new message: 202; the same signed request again inside 300 s: 202 (`duplicate`); the same request re-sent unchanged after 301 s: 401 (section 4.4 default); messages out of order: 202 each; malformed body or missing `id_field`: 400; same id with a different body and a fresh signature: 409; unknown path: 404; body over the limit: 413. Door crash: with the spy store of AK-G2 row W2, the door fails after the receipt commits and before the reply; the sender's retry gets 202 `duplicate`. Assert no loss after 202 and no second run.
- Key rotation and revocation row: two secrets configured, either verifies (AK-G2 row W15); after the old secret is removed and the door restarted, a request signed with it gets 401, also for a duplicate.
- Build a pack, and run its trial, only for a tool a client has chosen (order 57 A.2).

## 9. Order of work (no time estimates: ruling 12, plan-v3 section 9)
1. Now, in parallel: finish and verify the open chain (section 0.9) per STANDING-ORDERS item 6a. Done for one pull request = the lead merges it after independent evidence and a fresh `egm:*` review that meets the stop rule in section 10. An unchanged head is not tested twice; the lead still re-tests at the merge commit (plan-v3 section 3).
2. Now: the lead's freeze read of A18 v4.3 (order 145 items 2 and 4). No build starts from A18 before the lead's FROZEN line is in `LEAD-ORDERS.md`. [AUTHOR]
3. T1 assertions added when P4b1-a lands (section 8); T1.6 needs P4d's Postgres methods; T1.4b waits for P4b2. [AUTHOR]
4. P1c (after P1b merges, order 70 item 1) and the look-alike fix; only then T3b is wired into P6a's pilot and prod cross-check (lead item L13). [AUTHOR]
5. After the open chain merges, core v1 is done (amendment A10), and a lead order releases AK-G2: AK-G2-a with T2, then AK-G2-b with T2b. Checks before build start: ticket revision 3 with its build notes BN-1 to BN-23, the config row of section 4.2, a build-start review, and the UNVERIFIED-KEEP rows of section 6.1 for AK-G2 verified. The 4.4 option is NOT part of this. [AUTHOR]
6. Then a template pack only for a tool a client has chosen, IN-direction only until the OUT contract exists (T5, trial first).
AK-G15, AK-G1, AK-G16 stay DEFERRED until the owner's yes.

## 10. EGM for this plan and for each package (stated once)
- This plan: round 1 (five reviewers), the lead's resolve, round 2 (three reviewers), v4.2, round 3 = the last review round (order 143), v4.3 = one author pass without a new round (order 145); then the lead's read freezes it, and anything left becomes a build-time fix for the ticket it touches. [AUTHOR]
- Each package: ticket, plan review, build, a separate evidence runner, a fresh result review by `egm:*` agents, the lead's resolve, a drift report. Money, redaction and security paths have no round limit for real defects (R448; order 6(b); owner decision 8); after round 5 such a package escalates to the lead in writing (plan-v3 section 4 item 3). Other packages: at most 2 rounds. The plan-level limit above does not apply to package reviews. [AUTHOR: "cap" renamed]

## 11. Open items, ranked by what they block ("needed by" = the work item or event that waits)
Each table is ranked: the item needed earliest comes first. The ids are labels only (O = owner item, L = lead item) and are cited elsewhere in this file. **There is no O2** (plan v4.1's two licence items became one item, O1) and no L1 is open (closed by order 145 item 1); the ids are kept stable because reviews and order 145 cite them. [AUTHOR: note moved above the table]

For the owner (NEEDS-OWNER; the default applies until he answers):

| Rank | Id | Item | Needed by | Recommendation / default |
|---|---|---|---|---|
| 1 | O7 | P5b2 (built, PR 85): keep, or replace by ast-grep rules (a cut also rewrites P5c's Depends-on, plan-v3.md:149). Gain if replaced: less code of our own to maintain; loss: the built class judgements and the PR 85 work, plus an amendment [AUTHOR] | the PR 85 merge, then P5c build start | default: keep as built |
| 2 | O8 | P6b1 (built, PR 86): keep, or turn into a config or doc check. Gain if changed: less code; loss: the llm kind no longer refuses a training-allowed provider setting by itself [AUTHOR] | the PR 86 merge | default: keep as built |
| 3 | O10 [AUTHOR] | P5a's codes table, validation text and mutant file as stdlib enum, pydantic and nothing (order 70 item 3 "approved in principle"; order 70 item 3 also says no owner yes is needed because the code is unbuilt, so this item may be closed by the lead: lead item L9 asks) | P5a build start | default: CUT-TO-CONFIG+GLUE as order 70 item 3 plans |
| 4 | O11 [AUTHOR] | the dated exception "Postgres is the only pilot and prod store for inbound sources, spend reservations and multi-tenant row-level security", review_by 2027-01-31, with SQLite (P7l) as the named outline (section 6.2) | the first pilot | recommend: yes, with the date |
| 5 | O1 | the licence line of section 4.7, and whether Hadavin may build or run flows inside a client's n8n for a fee | the first quote that names n8n | default: no quote names n8n until he or a lawyer confirms |
| 6 | O3 | reconciliation against the sender's own ids (R368) is not included in v1 (section 4.5). Options [AUTHOR]: (a) accept for v1 with the section 4.5 quote sentence; (b) remove the reconciliation promise for the kit too (AK-G2 row V7 never built), which goes against R368 and needs his written yes; (c) build AK-G2 row V7 inside AK-G15 before the first pilot, as AK-G2 BN-14 says | the first quote that offers the door to a client (the quote must carry the 4.5 sentence) [AUTHOR] | recommend (a) for the demo stage and (c) before the first pilot that uses the door; start condition for (c): the first pilot, or the first client whose tool can export its delivered ids |
| 7 | O4 | where the door runs in pilot and prod (AK-G16 DEFERRED), and whether a small client pays for the door stack at all | the first pilot that uses the door; any quote that prices the door [AUTHOR] | recommend: lift AK-G16 only for the first named client; until then quotes say "door stack: NOT PRICED" and the door is demo-only |
| 8 | O5 | Activepieces shown as an option | the next options list for a client | default: shown, no pack |
| 9 | O9 | lift the deferral of AK-G15, AK-G1, AK-G16 (each separately). AK-G2 is NOT deferred (it is ACTIVE, `freeze-list.md:48`); its start is lead item L10 [AUTHOR] | work item 9.5 | default: stay deferred |
| 10 | O6 | a live Make trial for T5 needs a real account | a Make pack | default: no live Make trial |

For the lead (NEEDS-LEAD):

| Rank | Id | Item | Needed by | Recommendation |
|---|---|---|---|---|
| - | L1 | amendment number | recording A18 | CLOSED: A18 confirmed by order 145 item 1 [AUTHOR] |
| 1 | L9 | the two-vocabulary rule of section 0.5 (ruling 1 named four words; R448 needs its tokens in the rung table); and whether O10 needs the owner at all (order 70 item 3 says not) [AUTHOR] | the freeze read | confirm; close O10 as a lead decision |
| 2 | L10 [AUTHOR] | AK-G2's status: `freeze-list.md:48` and order 59 item 4 say ACTIVE, ruling 9 speaks of "lifting the deferral" of AK-G2. Which applies, and who releases its start | the freeze read; work item 9.5 | ACTIVE; its start is released by a lead order after the open chain merges (ruling 9) and after P8c (amendment A10, see L8); no owner lift needed |
| 3 | L13 [AUTHOR] | T3b wiring and the misses: (a) wire T3b into P6a only after P1c, the look-alike fix and the pinned bare-number property have merged; (b) the owner ticket of hostile rows 14 and 15: P1b (order 64 item 2) or P2d-1 (order 70 item 1, `tickets/P1c.md:57`); (c) confirm the sixth miss (row 6, bare number) as the accepted property of order 64 item 4 | P1c build; P6a's cross-check list | (a) yes; (b) P2d-1, as the newer order and the frozen P1c ticket say; (c) yes |
| 4 | L14 [AUTHOR] | P1c's phase: v1 or v1.1 (section 5) | P1c build start; T3b wiring | v1: it closes misses on a redaction path that pilot and prod need (T3b) |
| 5 | L15 [AUTHOR] | order 145 item 2(c) calls Presidio "the optional stronger backend"; the only test here shows it weaker on our corpus (T3b) | the freeze read | keep ruling 8's wording: an optional extra layer after ours |
| 6 | L16 [AUTHOR] | the quote sentence's word "refused" (section 4.5): door refusals (401, 400, 409) and an AK1 step's `refused invalid_input` are not handed to a person | the first quote that uses the door | keep the order 145 sentence, and add to the contract schedule (not the quote line): "refused" means stopped by a spending or safety limit |
| 7 | L5 | P5c's Depends-on names P5b5 (plan-v3.md:110), but P5b5 is DEFERRED (order 59 item 4(b)); the P5c ticket's PENDING LEAD 12 asks to narrow it to "P2d-2, P5a, P5b3" (`tickets/P5c.md:704`); whether it was answered: UNVERIFIED | P5c build start (chain) | narrow it by a written amendment line |
| 8 | L7 | currency rule of section 7 (no conversion, no comparison) | the first quote | confirm |
| 9 | L12 [AUTHOR] | P4a build note: pin the LiteLLM version and the sha256 of the wheel and of the price JSON used for the cross-check; wheels only; never 1.82.7, 1.82.8, 1.107.0 (section 6.2) | P4a build start | add as a P4a build note |
| 10 | L11 [AUTHOR] | wording and date of the Postgres dated exception (section 6.2), for the owner's yes (O11) | the first pilot | review_by 2027-01-31, as the llm exception |
| 11 | L8 | which wins on AK-G2's start: amendment A10 (kit after P8c) or ruling 9 (after the open chain) | work item 9.5 | A10 stands; a later lead order may name an earlier start |
| 12 | L3 [AUTHOR: "accept option A" removed] | AK-G2 build note: the pilot `store: memory` refusal row (4.2). The key start-up guard is already AK-G2 BN-3 (answer its PENDING LEAD 9). The 4.4 option is NOT part of this note | AK-G2-a and -b build start | add the config row; answer PENDING LEAD 9 with (a) |
| 13 | L4 | RLS FORCE contract line in AK1, or a recorded "not needed while one deployment per client" (4.2) | AK1 build start | build note on AK1 |
| 14 | L6 | refusal-rate bound, single-dependency and licence check for a Presidio extra layer, in the P5c ticket | a client asking for Presidio | add as a P5c build note |
| 15 | L17 [AUTHOR] | adopt the conditional 4.4 option or not | a T5 recording that shows a chosen tool retrying byte for byte more than 300 s after signing | adopt only then, through its own AK-G2 amendment with everything listed in 4.4; otherwise never |
| 16 | L2 | OUT contract: write one, or drop OUT; packs stay IN-only until then | any pack flow that asks our core to act | write it only when a client needs OUT |

Closed here: plan v4.1 items 9 (Postgres only, 4.2), 11 (compare_ids: cut by AK-G2 BN-14, 4.5 and O3), 13 (P5b2 meaning, 0.8), 14 (two vocabularies, now L9). [AUTHOR]

## 12. The 30 round-1 findings the resolve missed or only partly covered (order 143; source `studio-notes/plan-v4-round1-missed.md`)
Outcome key: FIXED = fixed in A18 at the named place; SPLIT = fixed for one part, open for a named other part; CONTESTED = not applied, with a checkable reason; MIXED = fixed for some named ids, contested for the rest; OWNER-OPEN = waits for the owner. [AUTHOR: SPLIT added]

| Finding | Was | Outcome | Where / reason |
|---|---|---|---|
| S3 cut of P5b2-P5b5 needs the P5c Depends-on rewrite | not covered | FIXED | section 5 P5b2 row (plan-v3.md:149); section 11 O7, L5 |
| S5 paragraph glued to a table | not covered | FIXED in v4.3 [AUTHOR] | every table now has a blank line before it (v4.2 still glued sections 6 and 7.1 tables to their first line) |
| S11 owner decision 3 vs CUT-TO-CONFIG+GLUE | partly | FIXED | section 0.5 (provided, not removed; no connecting row is DROP or CUT); packs row ADOPT in section 5 |
| S12 settled vs unproven; status column | not covered | FIXED | section 3.1 vs 3.2; section 5 Status column with the legend in 0.6 |
| S13 T3 and T4 missing owners | not covered | FIXED | section 8 headings name P5c, P2a; section 9 |
| C4 PR numbers and "open chain" undefined | not covered | FIXED | section 0.9; "chain" in 0.7 |
| C7 evidence cells cite no file | not covered | FIXED | sections 5 and 6.1 cite file and line (market-scan-2 lines 26-53) |
| C8 door, kinds, meter, stop_state, audit undefined | not covered | FIXED | section 0.7 |
| C9 "same key, one effect, forever" unexplained | not covered | FIXED | section 0.7 (ledger), section 4.6 |
| C10 terms (execution, Sustainable Use, ee folders, Close task) and "legally resell" | partly | FIXED | section 0.7; resale claim withdrawn (section 14) |
| Z4 missing module rows | not covered | FIXED | section 5 first paragraph names every unchanged id (the finding allowed one line) |
| Z5 AK-G2 vs P8a order; list of what v4 supersedes | partly | FIXED | section 1 item 2 and "Supersedes"; L8 |
| Z8 "only tool an agency may legally resell" | not covered | FIXED | section 3.1 Activepieces line; section 14 |
| Z10 LiteLLM 1.107.0 source; decision 3 vs packs; n8n Wait node | not covered | FIXED | section 3.1 (issue 47826, not in lead-fetch, UNVERIFIED text); section 0.5; section 4.7 |
| V4-03 Presidio and look-alikes | not covered | FIXED | section 3.2 (UNVERIFIED; per-row result on the lead's side) |
| V4-07 approval identity; the flow's token cannot approve | not covered | SPLIT [AUTHOR: was "FIXED for v1"] | FIXED for v1: section 4.7 (AK-G2 row C7: a door secret cannot equal the approval channel secret). OPEN: the person-identity approval API and its negative test "the flow's token cannot approve" belong to AK-G15 and GAPS row G14, both DEFERRED |
| V4-08 one gate per path | not covered | FIXED | section 4.1 "Gate per path" |
| V4-12 Activepieces licence wording | not covered | FIXED | section 3.1 (MIT outside ee, LICENSE read; Plus is the cloud plan) |
| V4-16 a row per plan-v3 and kit id | not covered | CONTESTED [AUTHOR: reason] | unchanged rows create no new component: R448 says "a task that creates no new component ... writes 'CODE-LAST n/a: <reason>' instead of a table", and a row for an unchanged id would restate plan-v3 with no new evidence. Section 5 names each id as UNCHANGED, which round-1 Z4 accepted |
| V4-17 rung row per non-KEEP-CODE module | partly | FIXED | section 6.1 rows for P5a parts, P5b5 rules, tenant mechanism, packs, portal |
| V4-18 RLS Postgres-only, no alternative | not covered | FIXED | section 4.2 (Postgres only in pilot and prod, fail closed; memory store demo-stage only); section 6.2 (SQLite outline P7l with start conditions; dated exception O11) [AUTHOR] |
| V4-22 retention vs erasure | partly | FIXED | section 4.6 (erasure question UNVERIFIED, owned by GAPS row G18) |
| V4-23 fake clock, crash points, no-expiry assertion | partly | FIXED | section 8 T2 (crash points now name the ticket's fault hooks) |
| V4-24 T5: offline recorded test plus manual tests; Make | not covered | FIXED | section 8 T5; O6 |
| F5 per-tool test method; packs only for chosen tools | not covered | FIXED | section 8 T5; section 5 packs row |
| F7 approval outside the flow; n8n only notifies | not covered | FIXED | section 4.7 |
| F9 missing rows (AK1, audit, signer, secrets, P6b2, P0a, P8, invoicing, AK2*/AK3/AK4b) | not covered | MIXED: FIXED for AK1 (section 5, three rows; section 6.1, three rows); CONTESTED for the rest | same reason as V4-16 (unchanged rows create no new component); each other id, invoicing included, is named as UNCHANGED in section 5's first paragraph |
| F10 guarantee and reproduced failing property per KEEP-CODE row; licence, version, date; rung 0 | partly | FIXED in v4.3 [AUTHOR] | section 6.1 now has a guarantee-class column and a single-failing-property column per row; rows with no reproduction say UNVERIFIED and are listed "open at build start"; rung 0 shown; licence and version stay in the scan lines cited |
| F18 seven unbacked claims | not covered | FIXED | section 3.2 lists each as UNVERIFIED or inference; Langfuse tier in 7.4 |
| F20 ledger and AK1c need Postgres; SQLite demo only; negative test | not covered | FIXED | section 4.2 and its negative test row (L3) |

Counts (one outcome per finding, 30 in all): FIXED 27, SPLIT 1 (V4-07), CONTESTED 1 (V4-16), MIXED 1 (F9), OWNER-OPEN 0. 27 + 1 + 1 + 1 = 30. [AUTHOR]

**Outside the 30** [AUTHOR: new table]: four findings that `plan-v4-round1-missed.md` marks "covered" by a ruling, each with a remaining gap the same file names. They are not among the 30 (23 not covered plus 7 partly); they are listed so nothing is lost.

| Finding | Gap named in the file | Where A18 answers it |
|---|---|---|
| round-1 S7 no totals; EUR/USD mixed | "currency rule not named" | section 7 first paragraph; lead item L7 |
| round-1 C1 ids and "step" undefined | "legend/definitions of each not stated" | sections 0.7 ("step") and 0.8 (ids) |
| round-1 F4 replay vs signature tolerance; forever vs retention; clock source | "retention/erasure and clock source not addressed" | section 4.6 (retention, erasure); section 8 T2 (clock) |
| round-1 F6 no loss before the door; reconciliation | "daily reconciliation not addressed" | section 4.5 (not included in v1); owner item O3 |

## 13. Round-2 findings and where A18 answers them (reports are condensed; the full texts are in earlier transcripts that are not available, so finding wording beyond the condensed lines is UNVERIFIED)
v4.3 re-checked each "FIXED" against the text; where the v4.2 claim was not true, the row now says so. [AUTHOR]

| Finding | Outcome | Where |
|---|---|---|
| Readiness A1 T1 has no file, branch, base | FIXED (v4.3 adds the test owner and the API under test) [AUTHOR] | section 8 T1 |
| A2 "at most floor" passes a meter that admits nothing | FIXED | T1 exact rule, T1.1 |
| A3 settle vs W; holds held at once | FIXED | T1.1-T1.4 |
| A4 concurrency model | FIXED | T1.1 threads on memory, T1.6 processes on Postgres (harness named in v4.3) |
| A5 measuring "never above the cap" | FIXED | T1 "How ... is measured" |
| A6 failure rule | FIXED | section 8 first line |
| A7 undefined labels; cap scope; slow test owner | FIXED | section 0.2, 0.7; T1 (run, day, month); slow test PENDING on the lead's side, no date (stated) |
| B1 crash point (d) after the 202 | FIXED | moved to T5 |
| B2 store API and clock injection | FIXED | T2 "Layer", "Clock" |
| B3 crash mechanism, end states, which store | FIXED in v4.3 (v4.2 named the points but not the mechanism; round-3 readiness BLOCKER) [AUTHOR] | T2 crash points use AK-G2 rows L1, W2, D1, D5 |
| B4 dispatcher; generation; lease | FIXED | T2 (dispatch between replays; generation only on reopen, 0.7) |
| B5 replay schedule | FIXED | T2 offsets from t0, bodies B and B' |
| B6 schema check not testable; receipt deletion | FIXED (role and guard names added in v4.3) [AUTHOR] | T2 hard schema criterion; AK-G2 line 177 |
| B7 T2 before its code | FIXED | T2 heading: written and run with AK-G2-a |
| B8 T2b numbers | FIXED | T2b |
| B9 exact just-past values | FIXED | T2 replays |
| C1 T3/T4 stubs | PARTLY: T3 hook points and T4 table names stay build-time items (stated in T3a and T4) [AUTHOR] | T3a, T3b, T4 |
| C2 T5 fixtures; HMAC unknown | FIXED | T5 (trial first, recording format, expected statuses); section 4.4 |
| D1 section 5 not a work breakdown | CONTESTED | a plan names packages; each row cites its ticket file, which holds files, tests and dependencies (ruling 1 made A18 an amendment, not a ticket). Round-3 readiness: acceptable only if the tickets are complete; that is UNVERIFIED for tickets not read here |
| D2 open-chain done criterion | FIXED | work item 9.1 |
| D3 Presidio not buildable | FIXED | section 5 P5c row: an extra layer only, gated by T3b and L6; no build planned until a client asks |
| D4 AK-G2 build gates vague | FIXED | work item 9.5 (section 6.1 AK-G2 rows named) |
| D5 open items that change code | FIXED | 4.2, 4.5, section 11 (P1c phase now lead item L14) [AUTHOR] |
| D6 door runtime target | FIXED | section 0.7 door; 7.2; 6.2; O4 |
| D7 stop-rule wording | FIXED | section 10 |
| D8 EUR vs USD comparison | FIXED | removed; section 7 rule |
| Design M-A reconciliation | FIXED (as NOT included; v4.3 corrects the cut `compare_ids`) [AUTHOR] | section 4.5, section 5 row, O3 |
| M-B scan figures | FIXED (cover figures explained in v4.3) [AUTHOR] | sections 0.5, 5, 6.1 cite lines 19, 26, 31, 44 (and 27-53); override reasons in section 5 |
| M-C Workers fee as door floor | FIXED | section 7.2 ("door stack: NOT PRICED"); Workers removed |
| M-D Postgres refusal; RLS FORCE + SKIP LOCKED | FIXED | section 4.2 |
| M-E every backend passes the hostile set; Presidio extra layer | FIXED | T3b; section 5 P5c row |
| M-F rung table vs R448 | FIXED in v4.3 (guarantee and failing-property columns) [AUTHOR]. One part CONTESTED: "ledger argument = one transaction shared by table, claim/lease and run row" is not what the ticket says (line 162: one transaction for receipt and body; claim and run row are separate statements). A18 writes the true argument: same database, run id derived from the key | section 6.1 |
| M-G T1 cases and wording | FIXED | T1.1-T1.7; section 6.1 P4b1 row wording |
| M-H T2 cases; T3; T4 | FIXED | T2 (d)-(f), races, schema; T3; T4 |
| M-I forwarder re-sign | FIXED (v4.3: the frozen rule stays; the option is conditional) [AUTHOR] | section 4.4; T5 trial |
| M-J totals look quotable | FIXED | section 7.3 (no totals; "lower bound, not a quote"); O4 |
| M-K OUT contract gates packs | FIXED | section 5 packs row; L2 |
| Design extras: key custody and rotation; ruling names; title; price map; line 177; retention and erasure | FIXED | 4.7, 4.6 (AK-G2 BN-3), T5; 0.2; section 8 title; P4a row; 4.3; 4.6 |
| Design nits: P5b2 = R3a; "marked UNVERIFIED" counted as fixed; item counts | FIXED | 0.8; section 12 says FIXED only where text changed; section 11 counts |
| Comprehension 1 letter R | FIXED | section 0.2 |
| Comprehension 2 P5b2/P5b5 | FIXED | section 0.8 titles; P5b5 DEFERRED everywhere; ast-grep in 0.7 |
| Comprehension 3 who lifts a deferral | FIXED | section 0.6 DEFERRED; AK-G2's status is lead item L10 [AUTHOR] |
| Comprehension 4 mixed vocabulary; portal; CUT; DROP twice | FIXED | section 0.5; portal ADOPT = CUT-TO-CONFIG+GLUE; Procrastinate called "rejected" (no DROP); 0.5 decision-3 line; CUT is defined and marked unused |
| Comprehension majors: status words, legend, letter A, three names, history in body, terms before use, two ladders, "rung 3" in owner text, missing rows, gate/window/step/package/channel/trigger/cap, door as address, "verbatim" paraphrase, 4.1/4.3/4.4 contradictions, "forever", currency, "owner called too much", seat examples, defaults clash, stop rule | FIXED in v4.3 for the word list (v4.2 claimed FIXED, but round-3 comprehension BLOCKER 4 showed gate, step, cap, trigger and channel still had several meanings) [AUTHOR] | 0.6; 0.1; 0.2; "One name"; section 14; 0.7 (gate, step, cap, trigger, channel, window, chain, ledger, lease, run, sender, source, hold, kind, delivered); 0.4 (one ladder); section 6.1 rows; 4.3 marked "quoted"; 4.1, 4.5, 4.7; 4.6; section 7; 7.4 one formula; O1 default kept with reason; section 10 |
| Comprehension nits (section number for estimates, heading, PR table columns, two "chain" meanings, prose in cells, cover shares, word clashes, unglossed tools, omitted numbers, voice) | FIXED where text changed ("chain" and cover shares in v4.3) [AUTHOR]; "300 approvals" and "10,446 passed" are in sections 7.1 and 5 | |

Counts (45 rows; several rows group findings, so this is not a count of single findings): FIXED 43 (one of them, M-F, has one CONTESTED part), PARTLY 1 (C1), CONTESTED 1 (D1), OWNER-OPEN 0. 43 + 1 + 1 = 45. [AUTHOR]

### 13.1 Round-3 findings and where v4.3 answers them [AUTHOR: new]
Source: the three condensed round-3 reports in `reviews/plan-v4-round3/`.

| Finding | Where v4.3 answers it |
|---|---|
| Design M1-M4 door rule (contradicts AK-G2 line 102 and Interface 7; `verify` returns one bool; replay cost and oracle; accepting option A premature) | section 4.4 rewritten: the frozen rule stays; option A conditional on T5 with every required part; L3 no longer accepts it; L17 |
| Design M3b quote line "exactly once" | section 4.5 quote sentence (order 145 wording); L16 |
| Design M5 R448 validity of KEEP-CODE rows | section 6.1 columns; open-at-build-start line; claim/lease row fixed; P5a row OWNER-OPEN; V4-16/F9 reason in section 12 |
| Design M6 T3b can make pilot and prod unstartable | section 8 T3b (six misses named, wiring rule); L13 |
| Design M7 no single-dependency audit | section 6.2 |
| Design M8 T1.4 cannot pass at P4b1 merge | T1.4 rewritten; T1.4b moved to P4b2 |
| Design T1 nits (T1.3 wording and `measured`; T1.6 connections; T1.7 mutant ids) | T1.3, T1.6, T1.7 |
| Design nits (compare_ids no caller; A9-A17; row 349 UNVERIFIED; S7/C1/F4/F6; V4-07 split; sixth miss and P1c in section 11) | section 4.5 and section 5 row (cut by AK-G2 BN-14); "How to read this file"; section 6.1 tenant row; section 12 "outside the 30"; V4-07 SPLIT; L13, L14 |
| Comprehension BLOCKER 1 (AUTHOR, CLIENT-EXCLUDED, PARTLY READ unused) | every change marked AUTHOR; CLIENT-EXCLUDED removed; PARTLY READ used ("How to read", 0.2) |
| Comprehension BLOCKER 2 (no product statement) | "What this plan proposes" at the top; process notes moved below it |
| Comprehension BLOCKER 3 (decisions justified by number only; R448 never stated) | section 0.3 (one sentence per rule, ruling and order); section 16 (R448 and R449 in full) |
| Comprehension BLOCKER 4 (gate, step, cap, trigger, channel) | section 0.7; body uses renamed (receipt write guard, hand-off lock, spend totals, round limit, hidden copy) |
| Comprehension majors (EGM-GATE v1, CODE-LAST v1; id collisions; statuses vs verdicts; scan figures; hidden-channel; chain and source; kind; INFORM I3, V6, GAPS rows; hold) | 0.7; 0.2 collision table; 0.5 "if built"; 0.5 cover figure; 0.7; 4.3; 0.2 |
| Comprehension nits (second ladder; O2 gap; "none known"; template pack by contrast; section 15 not cross-referenced; CUT unused; 16 markers) | 0.4; section 11 note; 7.3; 0.7; section 15 ids; 0.5; 0.1 (14 markers) |
| Readiness BLOCKER (T2 crash injection) | T2 crash points use the ticket's fault hooks |
| Readiness T1 (files, owner, API, caps, counters, harness) | T1 owner, API, caps, T1.3 counters, T1.6 harness |
| Readiness T2 (dispatch, fixtures, clock, (d)-(f), schema names) | T2 layer, clock, replays, key cases, schema criterion |
| Readiness 4.4 (stale reason, branches, lookup method, more mutants, flood, trial before fixtures) | section 4.4 (a)-(k); T5 order |
| Readiness T3, T4, T5 | T3a time budget named, hook points build-time; T3b runner and property location; T4 build-time item; T5 statuses, W2 spy store, recording format |
| Readiness: 19 UNVERIFIED remain | section 15 updated: three closed (Postgres 17 in CI, the sixth miss, the P5c time budget) |

## 14. History: withdrawn statements (kept here only)
- plan-v4: P2d "off by default" (withdrawn by ruling 2). Presidio as the default detector (ruling 8). pg-boss or Graphile Worker in the core (ruling 3). "BUILD NEXT: AK-G2" and "v1.1 FIRST" (ruling 9). "About 1 day of agent time" (ruling 12). T1 as an owner gate with default "no" (ruling 7). Cloudflare Workers "USD 5-10 a month, USD 60-120 a year" as the door cost. n8n "one-person team only" (an inference). Activepieces "the only automation tool an agency may legally resell" (a legal conclusion with no source; scan-2 line 536 is that scan's own summary). AK0 "dropped" (it is DEFERRED). P0t "shipped" (UNVERIFIED). "Effect in one transaction" (the ticket's claim is narrower, 4.3). An AK-G15 row that put the waiting screen in the client's tool. Status words FINISH, KEEP BUILT, HOLD.
- plan v4.1: called itself "A8" (taken). Used R1-R12 for rulings. Priced Cloudflare Workers Paid (USD 5 / 60) as the door's floor and printed totals with it. T1 pass rule "at most floor(C / W)". T2 crash point (d) "after the 202". Scan figures marked UNVERIFIED although they are at market-scan-2 lines 19, 26, 31, 44. "Whether the ticket deletes receipt rows: UNVERIFIED" (answered by AK-G2 line 177). Compared EUR 8,004 with USD 3,600 aloud. P5b5 called both "as built" and DEFERRED. Portal DROP in one table and CUT-TO-CONFIG+GLUE in the other. Graphile 4 h and pg-boss 7 days marked UNVERIFIED (they are in the pass 4 table). Owner order 11 marked "not in this copy" (it is at LEAD-ORDERS.md line 24).
- plan v4.2 [AUTHOR]: option A (stale signature accepted for a duplicate) as the recommended door rule, and lead item L3 "accept option A". The quote line "We record and process each message your tool delivers to us exactly once". T1.4 "a call refused BEFORE it was sent releases its reservation" (P4b1 has no caller release). "`compare_ids` (ticket line 192) ... has no caller in v1" (AK-G2 BN-14 cut it). "the plan asks for a start-up guard ... not in ticket revision 3" (it is AK-G2 BN-3). AK-G2 status "DEFERRED start" (it is ACTIVE). "the sixth hostile miss is not named in the files I read" (it is named in `lead-reading-1.md:6`). "SQLite ... is never allowed for these paths" (now: refused until P7l exists and passes the contract rows). Claim/lease failing property "stalled jobs stay stuck until YOUR periodic task retries them" (also true of our design). The legend marker CLIENT-EXCLUDED (never used). "Built from (all read for this draft)" as a claim for files the v4.3 author did not re-read.

## 15. UNVERIFIED and NOT PRICED (collected; the owner or lead item that depends on each is named) [AUTHOR: ids added, closed items removed]
1. Order 140 raw spend-cap file `egm/hadavin-sdk/core-complete/captest-1.md`: not in this checkout; slow-provider test PENDING. (T1 comparison only; no item)
2. n8n licence clause read by the lead (URL and date); whether we may build or run flows in a client's n8n for a fee. (O1)
3. n8n: paid feature split; Cloud Starter and Pro team features; 40K allowance for self-hosted Business; overage behaviour; credential protection. (O1; section 7)
4. Make prices and credit meaning; whether n8n, Make, Activepieces can sign and re-sign (T5 trial); whether Make exports scenarios as files (exit plan). (O6, L17; section 6.2)
5. Activepieces `ee` boundary in a running build. (O5)
6. Door stack price (Python host, Postgres), n8n hosting, Presidio container: NOT PRICED. (O4, L6)
7. Port and Appsmith billing of the first 5 seats; Langfuse self-hosted Enterprise price. (section 7.4; no item)
8. URLs of the SQS, Graphile, Cloudflare DLP, Cloudflare spend-limit, Claude errors and Appsmith quotes; Cloudflare Queues and Workflows URLs (docs source paths only); DBOS retention; Hatchet and pg-boss inferences. (section 6.1 "open at build start")
9. Presidio per-row look-alike results; cloud filters "no put-back"; OTel status; promptfoo ownership; docling licence. (L6, L15)
10. Failed-call billing beyond the Claude errors page. (P4b2 build start)
11. Reproductions blocked: door (n8n forced-kill test), claim/lease against pg-boss, P2a cloud switches, P3a and P4d tools, P5b1 OTel, P5b2 count (O7), P6a, P6b1 (O8), AK1b, tenant mechanism and tests (L4). (section 6.1 "open at build start")
12. Whether a keyed hash of a sender id is personal data under erasure rules (GAPS row G18). (no item; G18)
13. Merge state of every pull request in section 0.9; heads of PR 63; packages of PRs 75, 76, 78, 79. (work item 9.1)
14. P1c phase (L14); P0t "shipped".
15. Whether P2a rows cover all T4 attempts; which P5c rows test the redactor time budget and where T3a injects its faults; whether the lead answered P5c PENDING LEAD 12 (L5) and AK-G2 PENDING LEAD 9 (L3).
16. Owner decision wording of section 2 (condensed by the lead); R445 and R446 full text.
17. Round-2 and round-3 full reviewer texts (only condensed copies exist here).
18. SQLite's lack of SKIP LOCKED and row-level security (O11, L11); PostgreSQL's default `max_connections` of 100 (T1.6).
Closed in v4.3: PostgreSQL 17 availability (CI runs `postgres:17.10`, `ci.yml:40`); the sixth hostile miss (row 6, `lead-reading-1.md:6`); whether the P5c ticket names a detector time limit (`defaults.REDACT_BUDGET_S`, `tickets/P5c.md:284`).

## 16. Rule texts used for decisions, in full (verbatim from `bible-extract-R448-R449.md`, read 2026-11-07) [AUTHOR: new]
**R448.** [Hadavin practice, owner HARD rule 2026-11-06, said repeatedly; changing needs the owner's explicit yes] CODE LAST. Writing our own code is the last resort, never the default. THE LADDER is R447 (owner order 2026-11-06): no-code first, then our core modules, then existing free tools, then tested free libraries built on top, then our own new code; 'thin glue and configuration' (a few lines connecting tools, no business logic) counts as using the tool, not as new code. Our own new code is allowed only for what the ladder shows no tool can give (the guarantee-class list in R447): a safety guarantee (exact money caps and reserve/settle, redaction before the model, audit tamper-evidence, approval binding with a separate executor identity, tenant isolation and least privilege, eval gates, no lost or double-applied message). GATE: no plan, design, ticket, spec or agent brief may be handed to a builder, and no ticket may enter build-start review, without a RUNG TABLE (the artifact itself carries it; planning documents carry a short one): one row per component with the need, the rungs tried, evidence (source and date, or marked UNVERIFIED), what only our code gives, and a verdict KEEP-CODE (we write it) / CUT-TO-CONFIG+GLUE (a tool does it, we only configure and connect it) / CUT (the component is dropped, nobody needs it). '80 percent' means the share of the component's listed needs (the need column, one line per behaviour) that the higher rung already provides; the ticket author counts it with the evidence, reviewers re-count it, and a doubtful count is settled by the lead. If a higher rung covers 80 percent or more, the component is cut to config plus thin glue unless a written guarantee gap with a test idea proves otherwise. KEEP-CODE is valid only if the 'what only our code gives' cell names one of the guarantees above AND names the single property the tool fails, with a reproduction against the tool (a failing test, or a doc quote with its URL); the code covers only that guarantee path, everything around it stays config and glue. A table row's recommendation is input to the client options list of R446 (the client chooses in client builds; in the demo stage we choose). A thin kind module around a chosen tool (R363) is glue and does not count against the tool's coverage. Deterministic standard-library code or config beats a model call, and a model call beats new code (so 'newer model features' in R447 comes after deterministic code). A guarantee-class step may never live inside a no-code flow, because a flow has no tests or review; no-code tools carry only plumbing, and their licence terms are checked before they ship to a client. Tool facts live in one dated shared register (the cloud handover's TOOLS.md and the studio's research files), tickets cite its lines, a table is at most one page, and components of one kind share one epic-level table. The rung decision is made inside the EGM plan-review round, not as an extra round; security, money and redaction paths keep their no-cap rule and the 80 percent cut does not apply to the guarantee itself. Cut evidence may include the running cost of keeping existing code, but replacing working code still needs the owner's yes. A task that creates no new component (a lookup, an evidence run, a review, a bug fix in existing code) writes 'CODE-LAST n/a: <reason>' instead of a table. A row marked UNVERIFIED may stay in the table, but any verdict (KEEP-CODE, CUT-TO-CONFIG+GLUE or CUT) that rests on an UNVERIFIED row must be verified (a dated source read, or a small test of the tool) before the build starts; the lead checks it. Cuts need written evidence (improve-before-replace: never discard existing working code without evidence and the owner's yes). Reviewers must ask "should this exist at all, and what higher rung covers it?"; a missing or empty rung table is a Major finding. WASTE STOP: a component whose rung table lists a higher rung at 80 percent or more is decided in the same plan-review round and gets no review round of its own. Reasons that do NOT justify code: "we already wrote the ticket", "it is cleaner", "the demo had it". Tool facts are dated; whoever touches the ticket re-checks any fact older than 90 days, and an older fact counts as UNVERIFIED. A review round here means one full pass by the reviewers on the plan or ticket.

**R449.** [Hadavin practice, owner HARD rule 2026-11-06; changing needs the owner's explicit yes] Stages are named DEMO, PILOT and PROD, in that order, and nothing else: never "dev", "staging" or "test" as a stage name in code, config, URLs, docs, tickets or tests. Demo = synthetic or sandbox data, relaxed kinds, labelled as a demo; pilot and prod keep all gates (approvals, least privilege, audit separation). Core config accepts exactly these three stage values; any other value, including "dev", is refused with a message that names the rename. Persisted values: where an old 'dev' value is already stored (config, tenant records, audit entries, hash chains), it is mapped to demo on read and history is never rewritten; the startup check refuses an unknown stage and a half-renamed flag (fail closed, never 'allowed'). The class test looks at stage positions only (config values, enum members, URLs, docs headings), not words such as developer or the ordinary word test. Pilot is the first stage with real client data and the rehearsal of any risky prod change must be written into the pilot plan. Third-party tools that use dev or staging (GitHub environments, Helm values, cloud accounts) are labels mapped to demo or pilot. A project may keep its own environment labels (for example a client's "uat") only as labels mapped to one of the three stages in the project's config; core code tests the stage, never a label.

(Frozen ticket text that still says "dev", for example AK-G2's "dev-only stdlib server", is read as "demo" by P0t's build note; this plan writes "demo-stage".)

## 17. What changed from v4.2 (order 145 list, item by item) [AUTHOR]

| Item of the order 145 brief | What was done | Where it landed |
|---|---|---|
| 1 Door rule 4.4 | frozen 401-before-parse rule kept as the default; option A made conditional on the T5 trial; real benefit (the only case it helps) stated; stale-aware door-only verifier, exact stale test, `stale_max_age_s`, 401 for every stale-branch failure, per-source rate bound, read method, previous-secret test, restart note, build notes BN-24 to BN-26, rows W18-W28 (with "bad HMAC and stale: body never parsed" = W21), mutants M-b38 to M-b44 including the approval channel; "accept option A" removed from L3 | 4.4; 4.3; T2b; T5; L3, L17; section 1 item 2; section 14 |
| 2 Quote wording | "exactly once" replaced by the order 145 sentence; what the ledger proves per clause; the gap around "refused" sent to the lead; the claim checked across the file (no other client copy; the AK-G2 line 107 quote stays a quote of the ticket) | 4.5; L16; section 1 item 4 |
| 3 T1 | T1.4 rewritten to P4b1's release table inside `reserve` (passes at P4b1 merge); P4b2 release moved to T1.4b; T1.3 "cap at or below the booked total" with `measured=True`; T1.6 about 55 connections and the 8-process fallback, with the P4b1 T5 harness; T1.7 mapped to P4b1 M24 and P4d-b b3, b4, b12; owner and API named | section 8 T1; work item 9.3 |
| 4 Single-dependency audit | new section: Postgres dated exception (owner yes O11, lead L11) with the SQLite outline and start conditions; the door demo-only; inbound key and the existing AK-G2 BN-3 guard and runbook; Make exit plan (part UNVERIFIED); Presidio; LiteLLM pin and hash (L12); llm dated exception | 6.2; 4.2; O11, L11, L12 |
| 5 Rung table | guarantee-class and single-failing-property columns; URL or UNVERIFIED per quote; "open at build start" line; claim/lease property fixed; V4-16/F9 contest reason "unchanged rows create no new component"; P5a row OWNER-OPEN (O10); tenant row UNVERIFIED | 6.1; section 12; O10 |
| 6 T3b | the six misses named with dispositions (the sixth = hostile row 6, bare number, accepted property); wiring rule against the pilot and prod deadlock; P1c phase and the look-alike owner as NEEDS-LEAD; Presidio "stronger" CONTESTED | T3b; L13, L14, L15; section 1 item 1; work item 9.4 |
| 7 compare_ids; S7/C1/F4/F6; V4-07 | explicit row (out of AK-G2-a scope, cut by AK-G2 BN-14; removal as option (b) of O3); the four "covered" findings in a separate table outside the 30; V4-07 marked SPLIT | section 5; 4.5; O3; section 12 |
| 8 Comprehension blockers | (a) changes marked AUTHOR, CLIENT-EXCLUDED removed, PARTLY READ used; (b) plain product summary at the top, process notes below it; (c) one sentence per rule, ruling and order in 0.3, R448 and R449 in full in section 16; (d) glossary words in 0.7 with body uses renamed; EGM-GATE v1 and CODE-LAST v1 defined; id collisions in 0.2; "if built" verdicts and "no verdict" for deferred rows; cover figures explained; INFORM I3, V6, GAPS rows explained; one ladder; O2 note above the table; "none known" replaced; section 15 cross-referenced; section 13 FIXED claims re-checked | top of file; 0.1-0.7; 4.3; 5; 7.3; 11; 13; 15; 16 |
| 9 Readiness | wording and structure fixes done (T2 crash mechanisms, T1 API and harness, T2 fixtures, clock, key cases, schema names, T5 order and statuses, T3b runner); items needing a decision went to section 11 (L13, L16, L17); T3 hook points and T4 table names stay build-time items, said plainly | section 8; section 11; 13.1 |
| 10 Honesty | facts I did not read are marked UNVERIFIED or "carried from v4.2"; no ticket edited; the file stays the single plan | "How to read this file"; sections 3, 15 |
