# Hadavin FDE bible

This is the studio's rule book, its "Geeta/Bible". It is the owner's **AI Forward Deployed Engineer (FDE) course**, turned into one file per topic. Every Hadavin project and demo follows it. Every process, step and order comes from the course.

- **Authority:** the **images** win for diagrams and flows. The **.md notes** win for everything else.
  - Notes: `../Geeta or Bible for claude FDE/AI Forward Deployed Engineer - Notes.md`.
  - Images: `../Geeta or Bible for claude FDE/fde-diagrams-workflows images/Topic N/`.
  - Line ranges and image files per topic are in [_topic-map.md](_topic-map.md).
- **Course lab vs real world:** the course runs in a lab, with an OpenAI-compatible gateway, deepseek/gpt-4.1-nano/glm/gpt-oss/minimax models, `text-embedding-3-small`, JSON-file vector stores, stdlib mock APIs, SQLite and CSV, all under `/root`. Real Hadavin builds use:
  - Claude in the client's own cloud (Bedrock recommended on AWS after the client has chosen (R446); Foundry on Azure, Vertex AI on GCP, the direct API only on request);
  - real vector stores and connectors;
  - typed Python packages, guards, governed actions and CI gates.

  Each topic's "Course → real world" section, and [REAL-WORLD.md](REAL-WORLD.md), give the mapping. Anything not from the course is labelled "Hadavin practice".

**Names** [Hadavin practice]: the studio's client-facing name is **Hadavin**; the studio rename (old name Hadavin to Hadavin) was executed on 2026-11-03; the old name survives only in history records (owner decisions 2026-10-30 and 2026-11-01). Write Hadavin in anything a client reads; the label `[Hadavin practice]` stays as a studio-internal tag.

## Files

| File | What it is |
|---|---|
| [RULES.md](RULES.md) | The rules to follow on every project: R1–R374, R413–R444 and R445–R447 (R375–R412 reserved). R1–R291 follow the course topic order, but rules or parts marked [Hadavin practice] are studio rules; R292–R336 come from the system-design book and the support-agent lecture, R337–R374 from the 2026-11-01 audits and owner rules, R413–R444 from public LinkedIn posts (unverified, mostly TRIAL), R445–R447 from owner rules of 2026-11-03/04 |
| [LIFECYCLE.md](LIFECYCLE.md) | The engagement lifecycle: stages, steps, exit artifacts, kill points |
| [ROLES.md](ROLES.md) | Who does and who decides what (course roles and Hadavin roles) |
| [TIMELINES.md](TIMELINES.md) | The Hadavin compressed calendar for the lifecycle |
| [PROJECT-PLAYBOOK.md](PROJECT-PLAYBOOK.md) | The ordered procedure for a new project or demo: setup, each stage's steps, hats, EGM points, exit artifacts and sign-offs; templates in `..\templates\project\` (includes `tool-safety-review.md`, and the bucket checklist and metric menu in `eval-contract.md`) |
| [REAL-WORLD.md](REAL-WORLD.md) | Course lab → real client stack mapping |
| [_topic-map.md](_topic-map.md) | Topic → notes line range → image files |
| `topics/NN-*.md` | One file per course topic (table below) |

## How to use it

**Starting a new project or demo:** follow [PROJECT-PLAYBOOK.md](PROJECT-PLAYBOOK.md) from Step 0 and copy `..\templates\project\`.

**At session start (any project or demo):**
1. Read this README and [RULES.md](RULES.md).
2. Find the project's current stage in [LIFECYCLE.md](LIFECYCLE.md) and read that stage's section.
3. Open the topic files listed for that stage. Read their **Process / steps** and **Checklist** first, then "Course → real world".

**Per stage:**
1. Check the stage's **entry condition**. If it is not met, go back; never skip a stage.
2. Follow the steps in course order, using the cited topic files.
3. Work through every relevant topic **Checklist**; it is a working aid, not a gate. The stage's gate is its exit box in the project's `STAGE-CHECKLIST.md`.
4. Produce the **exit artifact** with the exact file names and sections.
5. Get the exit/kill decision from the person who decides (see [ROLES.md](ROLES.md)).
6. Check dates against [TIMELINES.md](TIMELINES.md).

**When a diagram and its text disagree:** use the image. Each topic file records this under "Text vs image".

## Topics

| # | Topic | One line |
|---|---|---|
| 01 | [What an FDE does](topics/01-what-an-fde-does.md) | Four responsibilities: find the problem, build fast, prove it works, make it survive. FDE vs architect vs ML engineer. |
| 02 | [The engagement lifecycle](topics/02-engagement-lifecycle.md) | Discovery → prototype → pilot → hardening and handoff, each with an exit artifact and a cheap exit point. |
| 03 | [How LLMs work](topics/03-how-llms-work.md) | Next-token prediction, a model frozen at training, and hallucination as the default risk. |
| 04 | [Tokens, context, and cost](topics/04-tokens-context-cost.md) | The `usage` block, the context window as one budget, and per-request and monthly cost. |
| 05 | [Just enough Python](topics/05-just-enough-python.md) | Scripts over curl, prompts as template plus data, JSON ↔ dicts. |
| 06 | [Calling LLMs over an API](topics/06-calling-llms-over-an-api.md) | The chat request contract, stateless calls, and the system message as the key configuration. |
| 07 | [Choosing a model](topics/07-choosing-a-model.md) | A per-workload choice on quality, latency and cost, proved on 20 real examples. |
| 08 | [Prompt engineering basics](topics/08-prompt-engineering-basics.md) | Clear instructions, few-shot examples and format control for parseable output. |
| 09 | [Prompts in production](topics/09-prompts-in-production.md) | The system prompt as a versioned, reviewed file; pinned models; rehearsed upgrades. |
| 10 | [Structured output](topics/10-structured-output.md) | Schema in the prompt; parse, validate, one retry, and a failures store. |
| 11 | [Tool calling](topics/11-tool-calling.md) | The model picks when to call a tool and with what arguments; your code controls what runs. |
| 12 | [Conversation state](topics/12-conversation-state.md) | Store and resend history; trim or summarize to fit. |
| 13 | [Embeddings](topics/13-embeddings.md) | Meaning as vectors; embed the corpus once and only queries at runtime. |
| 14 | [Vector search](topics/14-vector-search.md) | Records with vectors, ranked top-k, and score thresholds; a high rank ≠ relevant. |
| 15 | [The RAG pipeline](topics/15-rag-pipeline.md) | Retrieve → augment → generate, and proving which stage failed. |
| 16 | [Chunking enterprise documents](topics/16-chunking-enterprise-documents.md) | Clean messy exports, cut on structure, and attach metadata to every chunk. |
| 17 | [Retrieval quality](topics/17-retrieval-quality.md) | Hybrid search for exact ids; reranking for "on topic but not the answer". |
| 18 | [Citations and grounding](topics/18-citations-and-grounding.md) | Answer only from sources or refuse; validate the citations. |
| 19 | [Permissions-aware retrieval](topics/19-permissions-aware-retrieval.md) | Rebuild the source's locks in the index, and filter before scoring. |
| 20 | [Agents](topics/20-agents.md) | An LLM plus tools plus a loop; when a fixed chain is the better build. |
| 21 | [Multi-step agents](topics/21-multi-step-agents.md) | Dependent tool calls, errors fed back to the model, and a hard max-steps guard. |
| 22 | [MCP](topics/22-mcp.md) | Tools as reusable servers any client can call. Reuse is not safety. |
| 23 | [Connecting to customer APIs](topics/23-connecting-to-customer-apis.md) | Wrappers with trimmed responses, timeouts, readable errors and scoped service accounts. |
| 24 | [Getting data out of customer systems](topics/24-getting-data-out-of-customer-systems.md) | The four homes of knowledge, export vs sync, re-runnable ingest, and a `built_at` stamp. |
| 25 | [Why evals](topics/25-why-evals.md) | Golden questions, grading rule and threshold, agreed early as the definition of done. |
| 26 | [Golden datasets](topics/26-golden-datasets.md) | Real-traffic questions in easy, hard and trap buckets, with SME-owned answers. |
| 27 | [LLM as judge](topics/27-llm-as-judge.md) | Rubric-based binary JSON verdicts; audit the judge itself. |
| 28 | [Prompt regression testing](topics/28-prompt-regression-testing.md) | An eval runner plus an exit-code gate in CI on every change. |
| 29 | [Measuring RAG quality](topics/29-measuring-rag-quality.md) | Retrieval hit rate vs answer faithfulness, reported with comparisons. |
| 30 | [The fine-tuning decision](topics/30-fine-tuning-decision.md) | Prompting → RAG → fine-tuning; climb a step only on eval evidence. |
| 31 | [Guardrails](topics/31-guardrails.md) | Input and output filters, and injection through retrieved documents. |
| 32 | [Reducing hallucinations](topics/32-reducing-hallucinations.md) | Permission to refuse, citations, confidence routing, and a measured abstain rate. |
| 33 | [Cost control](topics/33-cost-control.md) | Cache, then classify-first router (R213), plus a hard daily budget in code from the first live call. |
| 34 | [Latency and streaming](topics/34-latency-and-streaming.md) | Streaming for perceived latency; timeouts and a fallback model. |
| 35 | [Observability](topics/35-observability.md) | Log every call, trace every request, and read the trace backward. |
| 36 | [Security, PII, and deployment](topics/36-security-pii-deployment.md) | A data-flow answer, deployment by data class, and redaction with proof. |
| 37 | [Discovery and scoping](topics/37-discovery-and-scoping.md) | Three filters take ~15 ideas to one use case; decline bad fits; `scoping.md`. |
| 38 | [Rapid prototyping](topics/38-rapid-prototyping.md) | A PoC in days on real data: docs → embed and store → retrieve → cited answer. |
| 39 | [Demos and expectations](topics/39-demos-and-expectations.md) | An honest demo that shows a limit, a baseline and target, and no "100%" clauses. |
| 40 | [Running a pilot](topics/40-running-a-pilot.md) | `success-criteria.md` up front, the weekly feedback loop, HITL signals, an honest verdict. |
| 41 | [Production rollout and handoff](topics/41-production-rollout-and-handoff.md) | Four exit criteria, the responsibility shift, three roles, `runbook.md`. |
| 42 | [Project: internal docs Q&A bot](topics/42-docs-qa-bot.md) | Capstone RAG: chunk, embed, store, retrieve, ground, cite, refuse. The docs Q&A template. |
| 43 | [Project: support assistant with evals](topics/43-support-assistant-evals.md) | A tool-calling assistant proved by a golden set, an eval and a pass-rate gate. |
| 44 | [Project: full engagement simulation](topics/44-full-engagement-simulation.md) | Scope, build, prove, price, hand off. The per-engagement deliverables template. |
