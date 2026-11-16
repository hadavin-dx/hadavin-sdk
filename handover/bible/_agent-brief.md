# Brief for topic agents (bible build, 2026-10-29)

## Who we are
Hadavin is a solo AI studio run by one owner, with Claude doing the build work. It sells fixed-price AI builds to small and mid-size businesses, startups and agencies in the US, UK, Canada and Australia. Typical builds:
- invoice/PO automation;
- support assistants;
- document Q&A;
- agents with governed actions.

Claude does three jobs: **FDE**, **architect** and **ML engineer**.

The FDE course is the studio's rule book ("Geeta/Bible") for every project and demo:
- every process, step and order comes from it;
- for diagrams and flows, the **images** are the authority;
- for everything else, the **.md** notes are the authority.

## Your job
For each topic assigned to you, read **every line** of that topic's range in the notes and **open every image** of the topic with the Read tool. Use `bible\_topic-map.md` for the line ranges and image files. Then write one file per topic: `<studio>/bible\topics\NN-<short-slug>.md`, with NN zero-padded (01..44). Don't stop to ask questions.

Each file has these sections, in this order:
1. `# NN — <title>`, then a line `Source: notes lines A–B; images: <file list or none>`.
2. **Why it matters**: 2–4 lines, in the FDE's terms.
3. **Process / steps**: numbered, exactly as the course teaches. Keep the course's order.
4. **Diagrams**: one entry per image:
   - the image's relative path;
   - a faithful **Mermaid** redraw of what the image shows (boxes, arrows, labels, branches, as drawn);
   - one line saying what it teaches.

   If the `.md` has an ASCII version of the same diagram that differs, write `Text vs image:` and the difference. The image wins.
5. **Rules and numbers**: every concrete rule, threshold, number, default and anti-pattern stated in the lessons. Write them as short imperative rules, each tagged with its lesson, e.g. `(L2)`.
6. **Decision rules from quizzes**: for each quiz, the scenario in one line, the right move, and why. Mention the wrong options only when they are a common trap.
7. **Tasks**: for each task, its goal, the method/steps, and what "done" looks like. Describe the method; don't paste the toy code. A short snippet is fine only when the snippet *is* the lesson (e.g. a validation loop).
8. **Course → real world**: how Hadavin does this in a real client build. Use this mapping and add topic-specific detail:
   - **Course models via the OpenAI-compatible gateway**: deepseek-v4-flash/pro, gpt-4.1-nano, glm-5.2, gpt-oss-120b, minimax-m3; embeddings `text-embedding-3-small`.
     - **Real:** Claude through the client's own cloud. Claude on Amazon Bedrock is the recommended option for AWS clients after the client has chosen (R446). Microsoft Foundry is used on Azure, Vertex AI on GCP, and the direct Claude API only on request.
     - **Model tiers:** Haiku 5.5 (cheap and fast), Sonnet 5.5 (the usual result for hard work; the tier comes from the workload chart, R278, R279) and Opus 5.5 (hardest tasks).
     - **Embeddings:** for example Cohere Embed v4 or Titan on Bedrock, or the client cloud's own embeddings.
     - Pin model ids and keep them in config; no literals in code.
   - **JSON-file vector store**: Bedrock Knowledge Bases on S3 Vectors, or pgvector when the client already runs Postgres. Keep the course's id + text + vector + metadata record shape.
   - **Mock stdlib HTTP APIs, SQLite and CSV**: real connectors to the client's systems (REST/GraphQL SaaS, databases, file drops), using least-privilege service accounts. Secrets go in the client's secret store (SSM SecureString or Secrets Manager), never in env files in the repo.
   - **Print scripts and toy code**: typed Python packages (uv, ruff, pytest) with clear modules: config, adapters (one interface plus backends), core logic, evals, CLI or API. Each module has tests, structured logs and OpenTelemetry traces. CI gates run on every PR.
   - **The pipeline's guards** (input/output filters, PII redaction, permission filtering): one interface each, with backends that match the client's cloud. Example: injection checks run on Bedrock Guardrails, Azure Prompt Shields, Model Armor or a Haiku screen. Regex PII redaction is always on.
   - **Agents and actions**: governed actions only. Each tool has an allowlist and a schema, risky actions need a human approval step, and every action is audited. Context comes from a "context lake" of the client's systems. Every agent sits in an agent registry with its owner, tools and permissions. Executions get scorecards. These are the [vendor-inspired name removed] "AI Software Factory" pillars.
   - **Course timelines** (e.g. a 12-week engagement): Hadavin compresses them and runs several deals at once. Keep every stage and its exit artifact, but shorten the calendar. Never skip a stage.
9. **Checklist**: 3–8 checkbox lines an engineer ticks before leaving this topic's stage on a real project.

**Style:**
- Plain, short sentences; no filler.
- Keep every number and term exact as the notes give them.
- Don't invent facts the notes don't contain, except in section 8, and label anything there that comes from outside the course as "Hadavin practice".

When you finish, reply with: the files written; the count of lessons, quizzes, tasks and images covered per topic; and any image/text conflicts you found.
