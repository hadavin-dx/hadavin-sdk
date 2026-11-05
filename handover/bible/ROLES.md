# Roles: the three hats, and who decides

Claude does the work of three course roles at Hadavin: **solutions architect**, **FDE** and **ML engineer**. The course says one person at a small vendor may wear two hats, and the roles still split cleanly by question (01 L2). This file keeps them split, so every piece of work and every decision says which hat made it.

**Sources and labels**
- Course: `topics/NN-*.md` (cited as `01 L2`, `07 Q1` and so on) and [LIFECYCLE.md](LIFECYCLE.md). The course text wins on process.
- `[Hadavin practice]`: studio rule, not in the course.
- `[research 2026-10-29: <file> §n]`: a dated outside fact. The files are in `..\research\research_notes\FDE stack and AI software factory 2026\`:
  - `ml_engineer_work.md` (ML);
  - `practitioner_stack.md` (PS);
  - `ai_software_factory.md` (ASF).
- `[research 2026-10-28: stack]`: `..\archive\warden-archive\research-2026-10-28-stack.md`.
- `[decision 2026-10-28]`: `..\memory\decisions-2026-10-28.md`.
- Prices and availability change. Re-check them live before quoting a client.

---

## 1. What the course says each role is (01 L2, notes lines 76–108)

| | Solutions architect | ML engineer | FDE |
|---|---|---|---|
| **Course verb** | advises | builds the model | ships the solution |
| **What they do** | "draws the plan": meets IT leaders, reviews the systems, produces diagrams and recommendations ("put the model here, connect these two systems, budget for this") | works on the model itself: "training it, tuning it, making it faster and cheaper to run" | "takes the model the ML engineer built, follows a plan like the one the architect drew, and actually makes it work": code, data cleaning, testing answers, sitting with compliance |
| **Where** | vendor side; then leaves; "rarely opens a terminal at the customer site" | vendor side, "far from any single customer"; the work helps every customer at once | customer side, deployed forward into one customer |
| **Test question** | Who recommended the overall shape? | Who decided the model's training data? | Who wrote the deployed code at the customer? |
| **Not their layer** | building it | "the bank's scanned PDFs" | the model layer (report weaknesses with failing examples, 01 Q2) |

Image `Topic 1/Screenshot 2026-10-29 175120.png`: the ML engineer and the architect sit in the vendor box; only the FDE sits in the customer box.

**The course boundary rule (01 Q2):** when the model is weak on a case, the FDE improves what they control first (retrieval, instructions, data: the solution layer). Then they report the remaining model weakness to the ML team with concrete failing examples. They do not retrain the model themselves, and they do not pause work while waiting.

### How Hadavin differs `[Hadavin practice]`
- All three hats are Claude, and all three work for **one client** at a time. The architect does not "leave"; the plan is revised as discovery finds facts.
- Hadavin **does not train base models.** The ML-engineer hat is the *model layer for this client*: choosing and routing models, the customisation decision, embeddings and rerankers, judge calibration, small classifiers, and the minimum MLOps. Section 5 covers it in depth.
- The 01 Q2 loop still runs, inside one head: the FDE hat fixes the solution layer first. Then it hands the failing examples to the ML-engineer hat, which tries a tier, effort or route change on the golden set.
- The human owner of Hadavin (the studio's folders still say Hadavin) signs the SOW and the price. Every plan, prompt, script, design, document, config and non-trivial change goes through EGM wherever it helps; skip only typos, status checks, read-only questions and one-line mechanical edits, and write "EGM skipped: reason" (owner rule 2026-11-01; superseded by this text on 2026-11-01: "every plan, prompt and design goes through EGM review before it acts", owner rule 2026-10-28). EGM is invoked through the `Skill` tool.

---

## 2. Each hat at each lifecycle stage

Stages and exit artifacts are from [LIFECYCLE.md](LIFECYCLE.md). The rows say what each hat produces; LIFECYCLE says when the stage may end.

| Stage | Architect (advise) | FDE (ship) | ML engineer (model layer) |
|---|---|---|---|
| **Day 0: entry** `[Hadavin practice]` | Access checklist: which systems, which accounts, which cloud and region; the client's data classes (36 L1–L2) | Signed order paid, sponsor named, access granted (TIMELINES.md Day 0) | Confirm the client's cloud offers the Claude tiers needed in the client's region `[research 2026-10-28: stack R3]` |
| **1 Discovery** | Data map: each source to one of the four homes (24 L1). Deployment by data class (36). A request-flow diagram and a "what data leaves your network" sheet for the security engineer (01 L3; 01 §8). Chain or agent per use case (20) | Wish list → three filters → one use case; declines bad fits (37). Sample documents and permissions in week one (16 L3, 19 L1). Eval contract (25 L2). Exit criteria written (41 L1). `scoping.md` | Workload profile per route: difficulty, human waiting, calls per day (07 L2). First cost envelope per tier (04 L3). Answers "fine-tune on our data" with the 30 L2 tree: knowledge goes to RAG |
| **2 Prototype** | Thin architecture note: modules, adapters and backends picked for this client (REAL-WORLD.md); an ADR per non-obvious choice | The risky core only: docs → embed and store → retrieve → cited answer (38 L1). Demo by about day four; one real user says "useful" (39 L1, 02 L2) | Cheapest viable tier on 20 real examples; upgrade only on side-by-side evidence (07 L2). Embedder picked and pinned. Same-meaning vs different-meaning sanity check on client samples (13 T1) |
| **3 Pilot** | Reviews the data flow with the client's security engineer before go-live. Staged rollout design: feature flag or allowlist, per-user and per-day budgets (02 Q1 §8) | `success-criteria.md` agreed first (40 L1). Golden set with SMEs (26). Weekly thumbs-down loop (40 L2). HITL signals (40 L3). Price (44 T1). Honest verdict (40 Q2) | Router and fallback chosen per route on the golden set (§5.1). Judge written and calibrated (§5.4). Hit rate and faithfulness split (29). Hybrid and reranker on evidence (§5.3). Fine-tune considered only if evals prove a plateau (30) |
| **4 Hardening and handoff** | Deployment hardening: private endpoint, IAM, secrets store, log retention (36). Guard backends per cloud (31). Durable approvals for governed actions | Guards wired, cost caps, streaming and timeouts, traces (31–35). Runbook (41 T1). Training: you do → they do with you → they do alone (41 L2). Owner named | Model ids pinned with lifecycle dates and an alarm (§5.6). Scheduled evals and drift alerts handed to the owner (41 L1). Model cards for any trained classifier |

---

## 3. Decisions each hat owns

"Owns" means the hat makes the recommendation and writes the decision record. The person in the last column approves it.

| Hat | Decisions owned | Who approves |
|---|---|---|
| **Architect** | Cloud route (Bedrock, Foundry, Vertex, or the direct API on request). Deployment shape by data class (36). Vector store. Connector pattern (export vs sync, 24 L2). Chain vs agent (20). Guard backends (31, 36). Orchestration and approval channel. Which hadavin-sdk modules and backends are used (REAL-WORLD.md) | Client security engineer for the data flow (01 L3). Sponsor for anything that changes cost or scope |
| **FDE** | Use case and declines (37). `scoping.md`. Eval contract terms proposed (25). Prompts and system prompt (08, 09). Chunking, top-k, threshold and rerank depth (14, 16, 17). Citation and refusal contract (18, 32). Pilot verdict (40). Runbook and training plan (41) | Sponsor signs `scoping.md`, `success-criteria.md` and the verdict (LIFECYCLE). SMEs approve expected answers (26). The owner's manager agrees the named owner (41 L1) |
| **ML engineer** | Model and effort per route, and the fallback model (07, 34). Embedder and reranker (13, 17). Judge model, rubric calibration and the judge audit (27). Customisation route: prompting, RAG, small classifier, or fine-tune of a non-Claude model (30). Price sheet per pinned model id (33). Pins, lifecycle alarms, drift signals and retraining triggers | Sponsor for any change that alters cost, quality or the provider. A threshold change needs the client's written OK (25 §8) |
| **Hadavin owner (human)** | SOW, fixed price, go/no-go to start a project | — |

**Design layers** [Hadavin practice, research 2026-11-01: audit J; our own label]. In every design document and proposal the architect states which layer carries the weight and why: (1) the model; (2) the wrapping around it (knowledge, tools, memory); (3) evals and guardrails; (4) production and operations; (5) optimisation (routing, caching, any multi-agent split). Light layers get one line. The evals and the failure story ("how it breaks" in `scoping.md`) go into the design from day one. Use this label in client documents, not another author's framework names.

**Client-side roles the hats work with (course):**
- **sponsor:** signs scope and criteria and the pilot's pass/fail band, decides continue/close/restart (40 Q2), and decides unmet exit criteria (41 Q1);
- **real user:** says "useful" at the prototype (02 L2);
- **SMEs:** own the golden answers (26);
- **security engineer:** approves the data flow (01 L3);
- **the three handoff roles** (41 L2): operator (the engineer), reviewer (support lead or domain expert), owner (the manager). [Hadavin practice] Each has a named deputy; with none, the gap is an open exit criterion for the sponsor (41 Q1: the owner resigns).

---

## 4. Hand-offs between hats

Each hand-off is a file in the client repo or deal folder, never a chat message `[Hadavin practice]`.

| From → to | What is handed over | When |
|---|---|---|
| Architect → FDE | Architecture note and ADRs: cloud route, data-flow sheet, store, connectors, guard backends | End of discovery, before build |
| FDE → ML engineer | Workload profiles (difficulty, waiting, volume); the golden set with SME sign-off; the **failing examples**, after solution-layer fixes are tried (01 Q2) | Prototype, then every pilot week |
| ML engineer → FDE | Model id per route and fallback, in config; judge model and rubric version; the decision record with pass rate, latency and cost | After each model-layer change |
| ML engineer → Architect | Any route that needs a non-Claude model, a new region or a new vendor, such as a fine-tuned open model or a separate embedding vendor | Before quoting it to the client |
| FDE → Architect | New facts that change the shape: a new data class, a residency rule, a permission model, an extra source | As soon as found |
| All three → client owner | Runbook, model pins and lifecycle dates, alarms, registry entry (41) | Stage 4 |

---

## 5. ML-engineer hat in depth

The course has no ML-engineer *process* for a client; its rules come from 07, 13, 17, 27, 29, 30 and 33. Everything below that is not from those topics is labelled.

### 5.1 Model selection and routing on the client's golden set

**Course rules (07):**
- never pick on quality alone; weigh quality, latency and cost (L1);
- ask per workload: how hard is one call? Is a human waiting? How many calls per day? (L2);
- start cheap: run 20 real examples on the cheap model; if good enough, stop (L2);
- upgrade only with side-by-side evidence on the same 20 examples, shown to the customer (L2);
- mixing models in one project is normal (L2);
- start cheap because "downgrade later" rarely happens (L2).

**Claude tiers on 2026-10-29** `[research 2026-10-29: ML §1, Anthropic models overview]`, per million tokens, input / output. **Verify on the day before any quote** (prices, ids and access change); last re-checked 2026-11-01 `[research 2026-11-01: audit M, platform.claude.com models overview and pricing, 2026-11-01]`:

| Tier | List price | Use for (course mapping, 07 §8) |
|---|---|---|
| Haiku 5.5 | $0.10 / $0.50 for prompts up to 100K tokens, $0.50 / $2.50 above that (cache reads count toward the 100K) | classifiers, triage, routing, high-volume extraction, the judge, the injection screen |
| Sonnet 5.5 | $2 / $10 | the default |
| Opus 5.5 | $4 / $20 | the hardest low-volume work, only when evals justify it |
| Fable 5.1 | $10 / $50 | not a Hadavin default tier; the same rule as Opus, evidence first |

- All four have a 1M-token context (full 1M at standard pricing except Haiku 5.5, see its row), 128K max output, adaptive thinking and a June 2026 knowledge cutoff. Reasoning depth is set by adaptive thinking plus an effort level; the old `budget_tokens` form is rejected with a 400 on these models (Claude 4.6 still accepts it, deprecated), `max_tokens` is required on every Messages call and thinking tokens count against it `[research 2026-11-01: audit B2, B3, platform.claude.com extended-thinking page, 2026-11-01]`. Among the 5.5 tiers thinking can be switched off only on Haiku 5.5 (effort high or below); on Sonnet 5.5 the lowest setting is `between_tools`; on Opus 5.5 lower the effort level `[research 2026-11-01: platform.claude.com/docs/en/build-with-claude/thinking]`. Default effort is `medium` on Opus 5.5 and Haiku 5.5, `high` on Sonnet 5.5 and Fable 5.1 `[research 2026-10-29: ML §1]`.
- Batch is 50% off. A prompt-cache read costs 10% of base input, but 5% on Opus 5.5 and Sonnet 5.5 and 2.5% on Fable 5.1 `[research 2026-10-29: ML §1; research 2026-11-01: audit M, pricing page]`. Bedrock's Claude endpoint has no Anthropic Message Batches API, Files API, MCP connector or server-side tools; Bedrock's own batch inference product was not checked `[research 2026-10-28: stack R3; research 2026-11-01: audit M]`. Set the prompt-cache TTL explicitly (5 minutes or 1 hour) (the default lifetime is 5 minutes `[research 2026-11-01: platform.claude.com/docs/en/build-with-claude/prompt-caching]`). The Bedrock Messages endpoint has no Message Batches, so the 50% batch discount applies to the Claude API only.
- Bedrock price is the same globally, plus 10% on regional endpoints `[research 2026-10-28: stack R3]`.
- Confirm the exact rate on the client cloud's pricing page before quoting. Bedrock access is set per model: Sonnet 5.5, Opus 5.5 and Haiku 5.5 showed per-model access criteria, not "open to all" (2026-11-01). Confirm model access for the pinned ids in the client account before the user pilot starts, and keep a fallback id that is open to all accounts in config (open on 2026-11-01: Sonnet 5, Opus 4.8, Haiku 4.5, Fable 5 and 5.1; Opus 5 is not open) `[research 2026-11-01: audit M, Bedrock page]`.
- **The model is a kind** [Hadavin practice, no single dependency; owner decision 2026-11-01 evening item 7]. Claude is the recommended default, offered as an option the client chooses (R446), chosen per task by eval (Haiku 5.5 / Sonnet 5.5 / Opus 5.5). The `llm` adapter has a second backend, built only when a client needs it and otherwise outlined with its trigger: an open-weight model served in the client's cloud or on its GPUs, another vendor's model on the same cloud, or an OpenAI-compatible gateway; triggers: air-gap, a client veto, a provider outage or deprecation with no acceptable successor, a price change, or an eval showing parity. Swapping needs a config change plus a green golden-set run. Vendor SDK imports live only inside the adapter module.
- **Conflict:** Anthropic's overview says to start with Opus 5.5 for most workloads. The course says start cheap and climb on evidence (07 L2). **Hadavin follows the course chart (R278, R279):** start on the cheap tier where the chart says so and climb on evidence; hard, low-volume steps start on the strong tier. Fixed prices make the cost of an unneeded tier Hadavin's loss.

**Procedure** `[Hadavin practice, from research 2026-10-29: ML §1 inference]`:
1. Take each route's golden cases (at least the course's 20 real examples; more once the pilot golden set exists).
2. Run them on the tier the chart gives (R278, R279), [Hadavin practice] at its default effort. Run the next tier up, one tier at a time, only if it falls short or the client needs agreement shown (R290). [Hadavin practice] Try a second effort level only on the tier being chosen. The race script is an eval in the repo (07 §8).
3. Record pass rate, p50/p95 latency, tokens and $ per 1,000 cases from the response `usage`.
4. Pick the cheapest tier and effort that meets the eval threshold ([Hadavin practice] within about 2 points of the best measured pass rate). The choice is per route and made before launch. At run time a route uses its one chosen tier or a classify-first router (R213), never a confidence-triggered retry on a stronger tier (R290).
5. Write the decision record with the hat label (§6) and show the client the evidence (07 checklist).
6. Re-run the set on any model id, alias or effort change. Ids are pinned snapshots; changes go through the CI gate (09, 28).

**Router and fallback:**
- the router is a Haiku classifier with JSON output that fails to the strong lane (33 §8);
- the fallback is for transport errors only (timeout, 5xx, 429 after bounded backoff; R219, R290). For money, approval and permission steps it follows R219: the same tier on another endpoint (for example a cross-region inference profile where the client allows it), then the strong tier, then a person. Sonnet 5.5 → Haiku 5.5 only where the workload profile says a wrong answer is harmless. The fallback must be on the client's approved model and region list and run the same guards (34 §8, G12).

### 5.2 The fine-tune decision

**Course rule (30 L2, image `Topic 30/Screenshot 2026-10-29 182145.png`):**
- missing knowledge → RAG;
- behaviour fixable by instructions → prompting;
- not fixable, but not proven at the limit with evals → keep prompting;
- proven at the limit → **consider** fine-tuning.

Fine-tune only when all three hold: the problem is behaviour, prompting is at its eval-proven limit, and volume or consistency justifies weeks of work plus a custom model to maintain forever (30 L2). Split mixed requests: knowledge → RAG, behaviour → prompting or fine-tuning (30 Q3).

**FACT, 2026-10-29: no current Claude model can be fine-tuned or distilled** on Bedrock, Microsoft Foundry or the Anthropic API `[research 2026-10-29: ML §2]`:
- Claude 3 Haiku was the only fine-tunable Claude model (Bedrock, us-west-2). AWS says it reached end of life on 2026-09-10.
- Bedrock: "Distillation is not currently available for Anthropic models … no confirmed timeline."
- Foundry's fine-tuning list (updated 2026-10-19) has no Claude model.
- No Anthropic API fine-tuning (secondary source).

So **customisation means leaving Claude on that route**, for a non-Claude model. Options with their region limits, as seen 2026-10-29 `[research 2026-10-29: ML §2]`:

| Platform | Customisable models | Region limits |
|---|---|---|
| Bedrock SFT | Nova 2 Lite, Nova Lite/Micro/Pro; Llama 3.1/3.2/3.3 | Nova in us-east-1, Llama in us-west-2. Pay-per-token inference only for Nova Lite, Nova 2 Lite, Micro, Pro and Llama 3.3 70B; others need hourly Provisioned Throughput |
| Bedrock RFT | Nova 2 Lite, gpt-oss-20B, Qwen3 32B | us-east-1 / us-west-2. $80 per training hour plus $1.95 per model per month storage. Tuned inference: gpt-oss-20b $0.09 / $0.39, Qwen3 32B $0.20 / $0.78 per 1M |
| Bedrock distillation | Nova Premier/Pro → Nova Lite/Micro; Llama 405B/70B → Llama 8B/1B/3B/70B | us-east-1 / us-west-2 |
| Bedrock Custom Model Import | Llama, Mistral, Qwen and others | us-east-1/us-west-2; also eu-central-1 (Frankfurt) |
| Vertex AI | Gemini 3.5/3.1/2.5 SFT; preference and RL tuning | Gemini 3.x only on the `us` and `eu` multi-region endpoints |
| Microsoft Foundry | Llama-3.3-70B, Qwen3-32B, gpt-oss, gpt-4.1 family and others (SFT/DPO/RFT) | Standard training is in-region (residency); Global and Developer have no residency |

Region warning `[research 2026-10-29: ML §2 inference]`: for UK, EU, Canadian or Australian clients with residency rules, Bedrock customisation is usually out, except Custom Model Import in Frankfurt. Vertex `eu` and Foundry Standard are the residency-friendly options.

**The Hadavin ladder:** prompt → RAG → tools, routing or a small classifier (§5.5) → fine-tune a non-Claude model only for a narrow, high-volume, measurable behaviour. Before fine-tuning, try the cheaper levers on the eval: prompt work, few-shot, structured output, a tier or effort change, and prompt caching for a long stable prompt (30 §8). `[research 2026-10-29: ML §2; Hadavin practice]`

**Realistic cases for a fine-tune** `[research 2026-10-29: ML §2 inference]`:
- (a) a high-volume narrow route (classify or extract) where a tuned Nova Micro/Lite or Llama 8B beats Haiku 5.5 on $ or latency at an equal pass rate;
- (b) data residency in a region where the needed Claude endpoint is missing;
- (c) RFT on gpt-oss-20B or Qwen3 32B when a cheap programmatic grader exists.

At $80 per training hour, a short RFT run is roughly $100–$500. That fits a fixed price only if the SOW scopes it.

Even at Haiku 5.5's floor price, a tuned open model (Qwen3 32B at $0.20 in) is not clearly cheaper. **Price is rarely the reason; residency, latency or behaviour is.**

**If it goes ahead** `[Hadavin practice]`:
- an ADR with the eval history proving the plateau (30 checklist);
- client sign-off: the route changes provider, so the Architect hat re-checks the data flow (§4);
- the golden set held out of the training data;
- the tuned model id pinned in config, through the same CI gate;
- a second model lifecycle tracked in the runbook.

### 5.3 Embeddings and reranker choice

**Course rules (13, 17):**
- embed the corpus once; embed only the query at runtime (13 L2);
- top match ≠ correct answer (13 L2);
- hybrid search for exact ids: keyword hits first, then vector, deduped (17 L2);
- rerank a wider shortlist (top 10) down to 3, with a cheap model returning validated JSON ids (17 L3);
- reranking cannot rescue a chunk that never made the candidate list: breadth first, precision second (17 L3, Q1).

**Hadavin default** `[Hadavin practice; prices from research 2026-10-29: ML §3 and research 2026-10-28: stack R3]`:
- **Embedder:** the embedder is a kind with a neutral default and an alternative, pinned in config. Neutral default: an open-weight embedding model the studio or client hosts. Alternative: the client cloud's managed embedder (on Bedrock, Cohere Embed v4, about $0.12 per 1M tokens per third-party sources, not confirmed on the AWS page on 2026-11-01, or Titan). Pin the model id and dimension; changing either means a full re-index.
- **Order of upgrades:** hybrid first, then a reranker, then (rarely) a different or tuned embedder. A practitioner test found "a reranker moved Recall@10 more than the difference between any two embedders" `[research 2026-10-29: ML §3]`.
- **Reranker:** a kind. Neutral default: an open-weight cross-encoder reranker we host, or a cheap LLM returning JSON ids (17 §8). Alternative: Cohere Rerank on Bedrock ($2.00 per 1,000 queries for Rerank 3.5, AWS pricing page 2026-11-01). Validate the ids every time.
- **Measure:** recall@k / hit rate on 50–100 labelled query → chunk pairs from the golden set, before and after each change (29; `[research 2026-10-29: ML §3 inference]`). Measure with the test user's real permissions (29 §8).
- **Fine-tune an embedder** only when the domain is far from general text and there are thousands to tens of thousands of query–passage pairs `[research 2026-10-29: ML §3]`.
- **Store the embedding model id and version with every vector.** Changing the embedder means a full re-embed, because vectors from different models are not comparable (13 §8).
- **Vector store:** a kind. Neutral default: pgvector (self-hostable, any cloud). Alternatives: Bedrock Knowledge Bases on S3 Vectors, Azure AI Search, Vertex vector search.
- **Watch:** S3 Vectors has no native keyword or hybrid search in the sources found. Hybrid on AWS needs pgvector plus Postgres full-text (or pg_search), or a keyword lane elsewhere `[research 2026-10-29: PS §6; research 2026-10-28: stack R3]`.

### 5.4 Judge calibration

**Course rules (27):**
- the judge always gets the question, the expected answer and the assistant answer, plus a fact-based rubric (L1);
- the verdict is binary JSON `{pass, reason}`; no 1–10 scales (L2);
- the judge runs on a cheap fast model (L1);
- audit the judge on known cases, including a confidently wrong one, when the rubric is written and on every change (L2);
- self-grading adds bias (Q1).

**Calibration on top** `[research 2026-10-29: ML §4]`. 2026 research found LLM judges agree with each other far more than with humans, so each judge is checked against people:
1. The client SME labels **100–150 real cases** (R325): pass/fail plus a reason, with at least 25 human-pass and 25 human-fail items held out. Collect them through the FDE hat, with SME sign-off as in 26.
2. The ML-engineer hat writes the rubric judge (27 L1).
3. Measure the true positive rate and true negative rate against the SME labels on the held-out part, each with its one-sided 95% lower bound (gate: both at least 0.70, i.e. 22 of 25 per class; high-stakes tier, where a miss costs money or security: 150 labels, 40 per class, true negative rate bound 0.80 and true positive rate bound 0.75; R325). Report Cohen's kappa with its interval and the confusion matrix, but do not gate on it: raw agreement looks good when one label dominates, and kappa on 50 items is too wide to decide. (κ = (observed agreement − chance agreement) / (1 − chance agreement).)
4. Iterate the rubric on the dev part until the dev rates look right. Never iterate on the held-out part; after two failed test parts stop and escalate to the owner.
5. Report the pass rate with the judge-error correction and a confidence interval (ICML 2026, PMLR v306).
6. Re-calibrate on every judge-model, rubric or system-model change.

Rules:
- use a judge from a different family or tier than the system under test (extends 27 Q1);
- synthetic cases only widen coverage: tag them, and report real-case scores separately;
- **conflict:** one 2026 paper found human–LLM agreement highest on a 0–5 scale. Hadavin keeps the course's binary verdict (27 L2: numeric scales drift) unless a calibration on the client's data shows otherwise, recorded in an ADR.

### 5.5 Small classifiers: when they beat an LLM call

`[research 2026-10-29: ML §5]`
- **Evidence:** on an 8-class intent task, SetFit (22M params) trained on 64 examples reached 91.1% at 2–5 ms. Zero-shot gpt-oss-20b reached 68.8% at about 3.4 s (arXiv 2602.18922, Feb 2026).
- **A classifier also can't be instruction-hijacked**, which makes it a useful extra injection tripwire. No independent benchmark was found; it is a tripwire, not the defence (31; `[research 2026-10-28: stack R1]`).

**Use a small model when all hold:**
- the label set is fixed;
- volume is above about 10k calls a day, or the latency budget is under 100 ms;
- the labels are stable for months;
- 50–500 labelled examples exist. Claude can pre-label; the SME corrects.

**Keep the LLM when:**
- labels change often;
- the task needs reasoning over long context;
- volume is low.

At SMB volumes Haiku 5.5 is often cheap enough, so a classifier is justified by latency, determinism or injection resistance, not cost.

**Tool ladder:**
1. scikit-learn (TF-IDF + logistic regression) as the baseline.
2. SetFit on a small sentence-transformer when labels are few.
3. ModernBERT fine-tune for thousands of labels or longer inputs.
4. Export to ONNX. Serve on CPU in any container host (neutral default); on AWS a Lambda container image, or SageMaker Serverless (1–6 GB memory, CPU only) when it doesn't fit Lambda.
5. Low-confidence predictions go to Claude.

**PII:** keep always-on regex first, then a detector behind it before training one: neutral default regex plus Presidio; alternatives the cloud's managed detectors (Comprehend PII, Bedrock Guardrails sensitive-information filters, Azure Language PII, GCP Sensitive Data Protection) (36 §8).

### 5.6 Minimal MLOps

For a Claude-first build, MLOps is mostly pins, the gate, logs and lifecycle dates. A real model registry and drift monitoring are needed only for routes with a trained model `[research 2026-10-29: ML §6 inference; Hadavin practice]`.

1. **Versioning:** every logged call stores the model id, prompt version, embedding model and judge version (35 §8).
2. **Gate:** the golden set runs in CI as a pass-rate gate on any prompt, model, retrieval or rubric change (28). The threshold is in config, never lowered without the client's written OK (28 §8).
3. **Logs:** invocation logging only with redaction, short retention and restricted access (35 §8, 36 §8).
4. **Labels keep flowing:** a weekly job samples 20–50 production cases into a human-review queue. Fixed thumbs-down cases become golden entries (40 L2, 26 §8).
5. **Drift signals (cheap):**
   - the label distribution of the router or classifier;
   - the share of low-confidence escalations;
   - the retrieval "0 docs" or no-answer rate (35 §8);
   - the judge pass rate on the weekly sample;
   - cost per request.
6. **Retraining or re-routing triggers:**
   - the sampled pass rate is below the gate for two weeks in a row;
   - the label set changes;
   - the base model enters Legacy.
7. **Lifecycle:**
   - every pinned model's platform EOL date goes in the runbook, with an alarm 60 days before;
   - take Bedrock dates from the Bedrock model card, not Anthropic's dates (Bedrock sets its own lifecycle; in Legacy, access can be lost after 15 days unused, and new fine-tune jobs are blocked) `[research 2026-10-29: ML §1, §6]`;
   - on a deprecation notice, follow 09 §8: a branch, the test set on the new id, a diff, a switch date before retirement.
8. **Registry:**
   - for Claude routes, the agent-registry entry (owner, tools, permissions, model ids) is enough (41 §8);
   - for a trained classifier or tuned model, add a versioned object-store path (S3, Blob or GCS) plus a model-card JSON: training data version, golden pass rate, kappa if judged, owner, base-model EOL;
   - SageMaker Model Registry is optional at SMB scale.

---

## 6. Labelling decisions with the hat

`[Hadavin practice]` Every decision record, ADR, PR description and weekly status line starts with the hat tag:

- `[ARCH]`: advise. The shape, cloud, data flow, stores, connectors, backends.
- `[FDE]`: ship. Scope, prompts, retrieval settings, evals with SMEs, pilot, runbook, deployed code.
- `[MLE]`: model layer. Model and route, embedder and reranker, judge calibration, customisation, MLOps.

Use the course's test question to pick the tag: who **recommended** the shape (ARCH), who decided **what the model is or learns** (MLE), who **wrote the deployed code** (FDE) (01 L2). When one change crosses hats, write one record per hat and link them.

**Decision record format:**
```
[MLE] 2026-11-03 — Route "ticket-triage" → Haiku 5.5, effort medium
Evidence: golden v4 (60 cases): Haiku 93.3% / Sonnet 95.0%; p95 0.9 s / 2.1 s; $0.04 / $0.71 per 1k cases
Rule: cheapest within ~2 points of best (ROLES §5.1); course 07 L2
Approved by: sponsor (email 2026-11-03)   Hand-off: model id in config → FDE
```
(The numbers above are an illustration only.)

Records live in the client repo (`docs/decisions/`), so the client sees which hat decided what, on what evidence.
