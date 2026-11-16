# Topic map: the course source for each topic

**Source notes:** `..\Geeta or Bible for claude FDE\AI Forward Deployed Engineer - Notes.md`. Topic banners look like `----Topic N - …----`.

**Images:** `..\Geeta or Bible for claude FDE\fde-diagrams-workflows images\Topic N\Screenshot 2026-10-29 HHMMSS.png`. The table lists only the HHMMSS part of each file name.

**Rule:** images are the authority for diagrams and flows; the `.md` is the authority for everything else.

| # | Title | Lines | Images (HHMMSS) |
|---|---|---|---|
| 1 | What an FDE does | 8–201 | 175112, 175120, 175134 |
| 2 | The engagement lifecycle | 202–357 | 175554, 175604 |
| 3 | How LLMs work | 358–591 | 175637, 175646 |
| 4 | Tokens, context, and cost | 592–1005 | 175717, 175727, 175743 |
| 5 | Just enough Python | 1006–1398 | 175814, 175822 |
| 6 | Calling LLMs over an API | 1399–1800 | 175856, 175907, 175916 |
| 7 | Choosing a model | 1801–2075 | 175945, 175955 |
| 8 | Prompt engineering basics | 2076–2472 | 180032 |
| 9 | Prompts in production | 2473–2851 | 180109, 180123 |
| 10 | Structured output | 2852–3357 | 180204, 180218, 180229 |
| 11 | Tool calling | 3358–3867 | 180304, 180318 |
| 12 | Conversation state | 3868–4347 | 180359, 180407, 180419 |
| 13 | Embeddings | 4348–4652 | 180447, 180457 |
| 14 | Vector search | 4653–5008 | 180534, 180546 |
| 15 | The RAG pipeline | 5009–5391 | 180631, 180645 |
| 16 | Chunking enterprise documents | 5392–5923 | 180719, 180730, 180740 |
| 17 | Retrieval quality | 5924–6482 | 180907, 180917, 180929 |
| 18 | Citations and grounding | 6483–6828 | 181026, 181034 |
| 19 | Permissions-aware retrieval | 6829–7365 | 181109, 181117 |
| 20 | Agents | 7366–7690 | 181215, 181234, 181248 |
| 21 | Multi-step agents | 7691–8328 | 181313, 181327, 181338 |
| 22 | MCP | 8329–8697 | 181422, 181429, 181448 |
| 23 | Connecting to customer APIs | 8698–9279 | 181523, 181538 |
| 24 | Getting data out of customer systems | 9280–9856 | 181654, 181704, 181721 |
| 25 | Why evals | 9857–10001 | 181755 |
| 26 | Golden datasets | 10002–10457 | 181818 |
| 27 | LLM as judge | 10458–10801 | 181913 |
| 28 | Prompt regression testing | 10802–11149 | 182007, 182017 |
| 29 | Measuring RAG quality | 11150–11595 | 182045, 182055 |
| 30 | The fine-tuning decision | 11596–11748 | 182145 |
| 31 | Guardrails | 11749–12283 | 182212, 182225, 182235 |
| 32 | Reducing hallucinations | 12284–12662 | 182318 |
| 33 | Cost control | 12663–13227 | 182346, 182358, 182410 |
| 34 | Latency and streaming | 13228–13509 | 182448, 182457 |
| 35 | Observability | 13510–13970 | 182523, 182533, 182544 |
| 36 | Security, PII, and deployment | 13971–14398 | 182615, 182626, 182635 |
| 37 | Discovery and scoping | 14399–14644 | 182710 |
| 38 | Rapid prototyping | 14645–14940 | 182748 |
| 39 | Demos and expectations | 14941–15106 | 182813, 182825 |
| 40 | Running a pilot | 15107–15518 | 182857, 182910, 182921 |
| 41 | Production rollout and handoff | 15519–15775 | 183000, 183007 |
| 42 | Project: internal docs Q&A bot | 15776–15988 | none |
| 43 | Project: support assistant with evals | 15989–16351 | none |
| 44 | Project: full engagement simulation | 16352–16649 | none |

**Course lab environment** (what the notes assume, which is not our real-world setup):
- **API access:** an OpenAI-compatible gateway reached through `$OPENAI_BASE_URL` and `$OPENAI_API_KEY`.
- **Chat models:** `deepseek-v4-flash`, `deepseek-v4-pro`, `gpt-4.1-nano`, `glm-5.2`, `gpt-oss-120b` and `minimax-m3`.
- **Embeddings:** `text-embedding-3-small`.
- **Storage:** JSON-file vector stores.
- **Tools:** mock HTTP APIs built on stdlib, SQLite and CSV data, FastMCP 1.x, and the `claude -p` command.
- **Setup:** the lab runs as root in `/root/...`.
