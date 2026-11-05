# Diagram verification: topics 21–41

**Method:** a goldfish check, done with no memory of how the redraws were made. Each image listed in `_topic-map.md` was opened from `..\Geeta or Bible for claude FDE\fde-diagrams-workflows images\Topic N\` and compared with its Mermaid block in `topics\NN-*.md`. The checks were: box and label wording, arrow direction, decision branches and their labels, loops, and grouping (subgraphs).

**Result:** 43 images checked. 43 PASS, 0 FAIL.

| Topic | Image (HHMMSS) | Diagram | Verdict |
|---|---|---|---|
| 21 | 181313 | Planning multi-step work: question → message history → [each pass: model rereads history → picks next tool → result appended] → final answer | PASS |
| 21 | 181327 | Failure handling: model calls tool → tool runs → result / error text as result → [model reacts: retry the tool, try another tool, tell the user] | PASS |
| 21 | 181338 | Stopping conditions: [agent loop: model call → plain text reply? yes → return answer; no → steps left? yes → model call; no → forced stop] | PASS |
| 22 | 181422 | [MCP clients: Claude Code, IDE assistant, your agent] —one protocol→ [MCP servers: inventory tools, ticket tools] | PASS |
| 22 | 181429 | user question → client app → [one round trip: 4 steps] → answer to user | PASS |
| 22 | 181448 | .mcp.json → claude starts → [startup handshake: 3 steps] → model can call get_stock | PASS |
| 23 | 181523 | model ⇄ wrapper function (order_id 1001 / order data) ⇄ [the part the model never sees: GET request → customer API → JSON response] | PASS |
| 23 | 181538 | env variable → tool wrapper —Bearer token in header→ customer API; back: 200 data, 401 when wrong | PASS |
| 24 | 181654 | [customer systems: 4 homes] → connector code → chunks and embeddings → your index | PASS |
| 24 | 181704 | [continuous sync: source ⇄ scheduled ingest → index stays fresh] and [one-time export: snapshot → index frozen in time] | PASS |
| 24 | 181721 | source changes → run ingest again → [rebuild: read all rows → embed texts → overwrite index file] → index matches source again | PASS |
| 25 | 181755 | [Agree with customer: 3 items] → run the eval → score → above threshold? yes → launch / no → fix and rerun → run the eval | PASS |
| 26 | 181818 | [golden.jsonl: 3 × question and expected] → eval runner → score | PASS |
| 27 | 181913 | rubric → judge model; [Judge inputs: question, expected answer, assistant answer] → judge model → JSON verdict | PASS |
| 28 | 182007 | golden.jsonl + prompt file → eval runner → model answers → grade each answer → scores.json | PASS |
| 28 | 182017 | prompt change → eval runner → scores.json → gate script → "score at or above threshold, exit 0" → change proceeds / "score below threshold, exit 1" → change blocked | PASS |
| 29 | 182045 | golden question → retriever → top k chunk ids → expected id in list? yes → hit / no → miss | PASS |
| 29 | 182055 | retrieved chunks + assistant answer + faithfulness rubric → judge model → pass or fail with reason | PASS |
| 30 | 182145 | Decision path: 3 diamonds, use RAG / use prompting (yes and no both reach it) / consider fine-tuning | PASS |
| 31 | 182212 | user message → filter model → allow → main model → answer / block → polite refusal | PASS |
| 31 | 182225 | main model → draft answer → policy check → clean → user sees answer / violation → safe fallback | PASS |
| 31 | 182235 | user question → retrieval ← [document store: normal doc, poisoned doc]; retrieval → prompt with docs → model → bad answer | PASS |
| 32 | 182318 | model answer → confidence (diamond) → high / low / none → 3 outcomes | PASS |
| 33 | 182346 | prompt → hash it → in cache file? hit → return saved answer / miss → call model → save answer → return answer | PASS |
| 33 | 182358 | question → router flash call → simple → deepseek-v4-flash / complex → deepseek-v4-pro → answer | PASS |
| 33 | 182410 | request → spent under limit? yes → call model → add cost to counter file → answer / no → budget exceeded message | PASS |
| 34 | 182448 | [streaming call: first words fast → rest flows in] and [normal call: wait 9 seconds → full answer at once] | PASS |
| 34 | 182457 | request → primary model → answer in time → answer / timeout → fallback model → answer | PASS |
| 35 | 182523 | request → model call → answer to user; model call → append line to calls.jsonl → jq and python read it later | PASS |
| 35 | 182533 | calls.jsonl → usage counts / cost sums / slow and failed calls | PASS |
| 35 | 182544 | question req-104 → retrieval line → prompt line → model call line → answer line | PASS |
| 36 | 182615 | [customer network: user question, retrieved documents] → prompt → external model API | PASS |
| 36 | 182626 | [where the model runs: SaaS API - customer VPC - on-prem, plain dashed lines] → easiest, least control / hardest, most control | PASS |
| 36 | 182635 | raw ticket → redact function → clean ticket → model API; redact function → PII never leaves | PASS |
| 37 | 182710 | 15 ideas → [Filter: painful? → data reachable? → measurable win?] → 1 use case | PASS |
| 38 | 182748 | [PoC only: customer docs → embed and store → retrieve → cited answer] → [Later: web UI, auth, deployment, unconnected] | PASS |
| 39 | 182813 | [Demo flow: rehearsed questions → show a limit → narrate mechanism] → trust → realistic expectations | PASS |
| 39 | 182825 | [Set the baseline: current process today → pilot target number → shared test set] → fair judgment of pilot | PASS |
| 40 | 182857 | [Each criterion: metric → target number → how measured → time window] → agreed with sponsor → review meeting has a verdict | PASS |
| 40 | 182910 | [Weekly loop: capture q and a and signal → review thumbs down → fix the cluster → tell the users → back to capture] | PASS |
| 40 | 182921 | AI draft → human agent → [Signals from actions: 4 unconnected boxes] → feedback log | PASS |
| 41 | 183000 | [Exit criteria: named owner → runbook written → customer has operated it → monitoring runs without you] → clean handoff | PASS |
| 41 | 183007 | [Responsibility shift: you do, they watch → they do, you watch → they do alone, you review] → system runs without you | PASS |

## Corrected Mermaid blocks
None. No image failed.

## Note: layout only, not a failure
Several blocks in topics 21–36 use `flowchart LR` with a subgraph whose inner chain the image draws top to bottom: 21/181313, 22/181429, 22/181448, 23/181523, 24/181721, 36/182626. The same applies to the stacked members in 22/181422, 24/181654, 26/181818, 27/181913 and 34/182448. Every box, label, arrow and grouping is correct; only the inner orientation can differ when rendered. Topics 37–41 already add `direction TB` inside such subgraphs. To match the images visually, add `direction TB` as the first line inside those subgraphs too. This is optional. Mermaid ignores a subgraph's `direction` when an edge links to the subgraph node itself, so the rendered result may not change.
