# Coverage verification: topic files vs course notes

Date: 2026-10-29. Verifier: goldfish (fresh eyes, adversarial). Topic files were not edited.
Source: `..\Geeta or Bible for claude FDE\AI Forward Deployed Engineer - Notes.md` (16,649 lines). Targets: `topics\01..44-*.md`.

## Totals

| Item | Found in notes (banners) | Present in topic files | Faithful (no gap found) |
|---|---|---|---|
| Lessons | 104 | 104 | 99 (5 have a missing point) |
| Quizzes | 67 | 67 (each has a decision rule) | 67 (no wrong answer found) |
| Tasks | 86 | 86 (each has Goal / Method / Done) | ~40 (most gaps are dropped paths, file names or model names) |
| Diagram images (per `_topic-map.md`) | 90 in 41 topic folders | 90 | 90; the map matches the image folders on disk |
| Number spot checks | 20 | 20 | 20 pass |

Banner quirks, both handled correctly by the topic files:
- Topic 24 has two "Task 1" banners (lines 9383 and 9505). The file maps them to T1 (CSV) and T2 (SQLite).
- Topic 38 has two "Quiz 1" banners (lines 14699 and 14895) and one "Quiz 2" banner (line 14916). The file maps them, in order, to Q1, Q2 and Q3.

**Result: 44 findings (2 WRONG, 42 MISSING).** Most are task-level. Topics 07–44 never give the `/root/fde-*` lab directory, and many tasks also drop the script names, the input file names or the model. No quiz answer and no number was found wrong.

## Missing or wrong items

| # | Topic | Item | Notes line | Type | What is missing or wrong | Fix text |
|---|---|---|---|---|---|---|
| 1 | 01 | L3 | 138 | MISSING (minor) | It drops the fact that about a quarter of the wiki-export pages are empty templates. | "09:00: about a quarter of the wiki-export pages are empty templates; filter them out." |
| 2 | 03 | T1 | 423 | MISSING (minor) | It doesn't say that line 1 of `steps.txt` is the starting sentence. | "Line 1 of `steps.txt` is the starting sentence; each later line adds one token." |
| 3 | 04 | T2 | 818, 826 | MISSING | The path `/root/tokens-cost/big-input.txt` is missing, and so is the requirement that both files exist. | "Generate the input with the given command into `/root/tokens-cost/big-input.txt`; done = `big-input.txt` and `limit-error.json` both exist." |
| 4 | 07 | T1 | 1854–1856 | MISSING | It uses bare names `race.sh`, `flash.json` and `pro.json` without their directory. | "Files: `/root/fde-choosing-a-model/{race.sh,flash.json,pro.json}`." |
| 5 | 07 | T2 | 1994, 2000 | MISSING | The path is missing, and so is the rule "use only model names that exist in this lab". | "Write `/root/fde-choosing-a-model/choices.txt` in the exact `name: model` format, using only lab model names." |
| 6 | 08 | T1 | 2133–2134 | MISSING | It uses bare file names. | "Files: `/root/fde-prompting-basics/summary-prompt.txt` and `summary-output.txt`." |
| 7 | 08 | T2 | 2266–2267 | MISSING | Three things are missing: the path, the "at least two solved examples" minimum, and "save only the reply text". | "`/root/fde-prompting-basics/tag-prompt.txt` needs ≥2 solved examples in the exact format; save only the reply text to `tag-output.txt`." |
| 8 | 08 | T3 | 2388–2389 | MISSING | It uses bare names, and the one-line output rule is missing. | "Script `/root/fde-prompting-basics/status-line.py`; output `status-line.txt` must be exactly one line." |
| 9 | 09 | T1 | 2536–2539 | MISSING | It uses bare names, and the two test inputs are paraphrased instead of quoted. | "Files under `/root/fde-production-prompting/` (`system-prompt.txt`, `offtopic-reply.txt`, `refund-reply.txt`). Test inputs: 'Can you give me a good recipe for pasta carbonara?' and 'Your ferry was cancelled and I want my money back right now!'." |
| 10 | 09 | T2 | 2657–2659 | MISSING | The repo path is missing. | "Repo at `/root/fde-production-prompting/promptrepo`; done = the git log shows both prompt versions." |
| 11 | 10 | T1 | 2905–2906 | MISSING | The exact prose prompt is missing, and the file names are bare. | "Prompt exactly: 'Read this support ticket and tell me the category, the priority, the customer, and a one-sentence summary.' Files: `/root/fde-structured-output/prose-reply.txt`, `parse-result.txt`." |
| 12 | 10 | T2 | 3032, 3045–3047 | MISSING | It uses bare names, and the allowed-value lists are not stated as task requirements. | "All files under `/root/fde-structured-output/`; save the fixture exactly as given; category ∈ billing/login/bug/other, priority ∈ high/medium/low." |
| 13 | 10 | T3 | 3201–3206 | MISSING | It uses bare names, and append mode is not stated. | "Files: `/root/fde-structured-output/{pipeline.py,record.json,failures.txt}` (`failures.txt` opened in append mode)." |
| 14 | 11 | T1–T3 | 3445, 3598, 3723 | MISSING | Model, directory and script names are all missing. | "All tasks use `deepseek-v4-flash` in `/root/fde-tool-calling/`, with scripts `weather-tool.py`, `loop.py` and `dispatcher.py`." |
| 15 | 12 | T1–T3 | 3910, 4021, 4184 | MISSING | T1 and T3 name no model. Scripts and directory are missing. | "All tasks use `deepseek-v4-flash` in `/root/fde-conversation-state/`, with scripts `forget.py`, `chat.py` and `capped-chat.py`." |
| 16 | 13 | T1, T2 | 4536 | MISSING | T2 must create `tickets.txt` with the exact 10 tickets, and Submit checks for it. The scripts `compare.py` and `search.py` are not named. | "T2: first create `/root/fde-embeddings/tickets.txt` with the exact 10 tickets, one per line; script `search.py` writes `nearest.txt`. T1 script: `compare.py`." |
| 17 | 14 | T1, T2 | 4703, 4865 | MISSING | It never says to create `snippets.txt` (8 exact lines). The scripts and `text-embedding-3-small` are not named. | "Create `/root/fde-vector-search/snippets.txt` with the exact 8 snippets; scripts `build_store.py` and `query.py`; model `text-embedding-3-small`." |
| 18 | 15 | T1, T2 | 5065, 5241 | MISSING | It never says to create `chunks.json` (the 6 policy strings). The T2 script and the directory are not named. | "First create `/root/fde-rag-pipeline/chunks.json` (a JSON array of the 6 policy strings); T2 script `break_retrieval.py`." |
| 19 | 16 | T1–T3 | 5427, 5604, 5774 | MISSING | It never says to create the input files `policy.md`, `manual.txt` and `export.txt` (Submit checks for them). It drops "blank lines included" for `manual.txt`, and T2's embedding model is not stated. | "Create `policy.md`, `manual.txt` (blank lines kept, 5 paragraphs) and `export.txt` in `/root/fde-chunking-enterprise-docs/`; T2 uses `text-embedding-3-small`." |
| 20 | 17 | T1–T3, L1 | 5978, 6158, 6336, 5937 | MISSING | It never says to create `runbook.json` (8 records; rb-06 is the long maintenance note) or `candidates.json` (6 vpn records). The scripts are not named. It doesn't say the lab scores come from `text-embedding-3-small`. | "Create `runbook.json` and `candidates.json` in `/root/fde-retrieval-quality/`; scripts `rank_check.py`, `hybrid.py`, `rerank.py`; the lab scores were measured with `text-embedding-3-small`." |
| 21 | 18 | T1, T2 | 6542, 6684 | MISSING (minor) | Scripts and directory are not named. The fac-1..3 and ref-1..4 chunk texts are not given. | "Scripts `grounded.py` and `cite.py` in `/root/fde-citations-grounding/`; the context is the fac-1..3 and ref-1..4 lines verbatim from the notes." |
| 22 | 19 | T1, T2 | 6896, 7107 | MISSING (minor) | Scripts and directory are not named. The embedding model appears only in Course → real world. T2's "rebuild index.json if missing" step is missing. | "Scripts `leak.py` and `safe_search.py` in `/root/fde-permissions-aware-retrieval/`, embeddings from `text-embedding-3-small`; T2 rebuilds `index.json` via `leak.py` if it is missing." |
| 23 | 23 | T2 | 9016, 9048 | MISSING | The secret `demo-secret-123` and its grep pass check are missing. | "The mock's token is `demo-secret-123`; `grep -c` for it in `auth_agent.py` must return 0." |
| 24 | 23 | T2 | 9017–9020 | MISSING (minor) | It doesn't say the auth mock serves only orders 1001 and 1002. | "The auth mock serves only orders 1001 and 1002." |
| 25 | 26 | L2 | 10207 | MISSING (minor) | The "desk-only set scores 95 percent" warning is missing. | "A set of only clean, desk-written questions can score 95 percent while real users fare much worse. (L2)" |
| 26 | 26 | T1, T2 | 10056 | MISSING (minor) | The docs file is not named, and neither is the ticket dump. | "T1: save the docs to `courier-docs.txt`. T2: save the dump to `tickets.txt`." |
| 27 | 27 | T2 | 10646, 10665 | MISSING | The exact files `rubric-v1.txt` (verbatim) and `rubric-v2.txt` are missing. | "Save v1 verbatim to `rubric-v1.txt`, write the tightened rubric to `rubric-v2.txt`, and pass the rubric path to the judge." |
| 28 | 28 | T1 | 10883 | MISSING | The eval model `deepseek-v4-flash` is not named anywhere in the file. | "The runner asks `deepseek-v4-flash` each golden question, with the prompt file as the system prompt." |
| 29 | 29 | T1 | 11224 | MISSING | `text-embedding-3-small` is not named. | "Embed the chunk texts and the questions with `text-embedding-3-small` in one batch." |
| 30 | 29 | T2 | 11399 | MISSING | The judge model and `faithfulness.py` are not named. | "`faithfulness.py` sends each answer and its context to `deepseek-v4-flash` as the judge." |
| 31 | 31 | T3 | 12159, 12170, 12176 | MISSING | The script `rag_safe.py`, the model `deepseek-v4-flash` and the directory are not named. | "Write `/root/fde-guardrails/rag_safe.py`, which saves `docs.json`, asks `deepseek-v4-flash` the vacation question and writes `safe_answer.txt`." |
| 32 | 37 | T1 | 14524, 14542 | MISSING | It gives `brief.txt` and `scoping.md` without their directory. | "Save `/root/fde-discovery-scoping/brief.txt`; write `/root/fde-discovery-scoping/scoping.md`." |
| 33 | 37 | Rules (T1), line 72 | 14542 | **WRONG** | It says "must have exactly 4 H2s". The notes only say the doc must contain these four H2s, spelled exactly. | "The scoping doc must contain these 4 H2s, spelled exactly: `## Use case`, `## Out of scope`, `## Success metric`, `## Risks`." |
| 34 | 38 | T1 | 14726–14758 | MISSING | Paths are missing, and the three doc texts ("exactly these filenames and contents") are not stored. | "Paths `/root/fde-rapid-prototyping/docs/{vpn,passwords,devices}.txt`, `store.json`, `answer.txt`; doc texts verbatim from notes 14729–14752 (GlobalConnect, 12 h sessions; ≥14 chars, 180 days, reset.copperline.internal, 5 failures → 30 min lock; disk encryption + Sentinel agent, managed mail app, lost device reported within 4 h)." |
| 35 | 40 | T1 | 15179 | MISSING | The output path is missing. | "Write `/root/fde-pilot-metrics/success-criteria.md` with the 4 exact H2s." |
| 36 | 40 | T2 | 15351–15366 | MISSING | Paths are missing. The 5 seed lines (meant to be copied exactly) are not stored, and the new entry is only summarised. | "Files `/root/fde-pilot-metrics/{feedback.jsonl,log_feedback.py,escalate.py,escalations.txt}`; seed lines verbatim from notes 15354–15358; new entry: question 'which customs form do i need for a UK shipment', answer 'You need form CN22 for all UK shipments regardless of value.', feedback 'down'." |
| 37 | 40 | L2 | 15284–15285 | MISSING | The "feedback loop is your review-meeting defence" rule is missing. | "Use the feedback loop as your answer in the review meeting: say when it was logged, the root cause, the fix date and the score since. A managed failure builds more confidence than a hidden one. (L2)" |
| 38 | 41 | T1 | 15677 | MISSING | The output path is missing. | "Write `/root/fde-production-handoff/runbook.md` with the 4 exact H2s." |
| 39 | 41 | L2 | 15610 | MISSING | The three-role failure path is missing. | "With all three roles trained, a bad answer has a path: the reviewer catches it, the operator fixes it, the owner sees the trend. (L2)" |
| 40 | 42 | T1 | 15783–15797 | MISSING | The seed command, the exact covered question and the deliverable paths are missing. | "Seed: `curl -fsSL https://raw.githubusercontent.com/Esc-Bash/project-init-scripts/main/ai-fde/project-1/init.sh \| bash`. Covered question: 'How much can I expense for meals during business travel?'. Deliverables: `/root/project-1/{chunks.json,store.json,ask.py,answer-expenses.txt,answer-trap.txt}`." |
| 41 | 42 | T1 Method step 2 (line 67) | 15839–15847 | **WRONG** | It says "split each chunk over 50 chars in half". The code splits only when half the length is over 50, i.e. chunks over ~100 chars. Rules line 53 states this correctly. | "If there are under 20 chunks, split each chunk whose half-length is over 50 chars (i.e. over ~100 chars) in half (`_a`/`_b`)." |
| 42 | 43 | T1 | 15996–16013 | MISSING | The seed command and the base directory are missing, and the API URL is only partly given. | "Seed: `curl -fsSL https://raw.githubusercontent.com/Esc-Bash/project-init-scripts/main/ai-fde/project-2/init.sh \| bash`. Files in `/root/project-2/` (`assistant.py`, `golden.jsonl`, `eval.py`, `scores.json`, `gate.sh`). API at `http://localhost:8100/orders/<order_id>`." |
| 43 | 44 | T1 | 16359–16372 | MISSING | The seed command and the base directory are missing, and the tracking endpoint appears only in the diagram. | "Seed: `curl -fsSL https://raw.githubusercontent.com/Esc-Bash/project-init-scripts/main/ai-fde/project-3/init.sh \| bash`. Deliverables in `/root/project-3/`. Tracking API at `http://localhost:8200/shipments/<id>`." |
| 44 | 25–30 | file end | — | WRONG (format) | Six files have an odd number of ``` fences, with a stray closing fence after the Checklist: 25, 26, 27, 28, 29, 30. | Delete the trailing stray ``` line in each of the six files. |

### Cross-cutting pattern (not counted above)
Several tasks say "save exactly as given" but the topic files only summarise the seed data: 31 T3 `docs.json`, 32 T2 `traps.jsonl` (the 4 answerable questions are not listed), 35 T2 `calls.jsonl`, 35 T3 `trace.jsonl`, 36 T1 `tickets.txt`, 37 T1 `brief.txt` (and rows 16–21 and 34 above). The pass criteria are stated in every case. If a topic file must be enough to redo a task without the notes, add "seed data verbatim: notes lines N–M" to each.

## 20 number spot checks

| # | Notes line | Value in notes | Topic file | Result |
|---|---|---|---|---|
| 1 | 879 | deepseek-v4-pro $1.20 in / $4.80 out per 1M | 04 line 64 | PASS |
| 2 | 927 | deepseek-v4-flash $0.10 / $0.40 per 1M | 04 line 64 | PASS |
| 3 | 894–896 | 8,000 prompt tokens → $0.0008; total $0.0010 | 04 line 66 | PASS |
| 4 | 818 | big input `'server log line: request handled ok. ' * 80000` | 04 line 80 | PASS |
| 5 | 3013 | prompt gets you to ~95%; three-line cleanup | 10 line 50 | PASS |
| 6 | 5937 | ERR-4092 chunk 0.398 vs 0.404, ranked 2nd | 17 line 55 | PASS |
| 7 | 5938 | 0.561 vs 0.550 with 4 look-alike codes | 17 line 56 | PASS |
| 8 | 7420 | X-100 stock 96, daily_usage 8 | 20 line 63 | PASS |
| 9 | 9714 | KB-3 webhook timeout "within 10 seconds" | 24 lines 97–98 | PASS |
| 10 | 9924 | threshold example: at least 85 percent | 25 lines 13, 43 | PASS |
| 11 | 10084 | at least 10 Q&A pairs in golden.jsonl | 26 lines 58, 70 (10–20 entries) | PASS |
| 12 | 10290 | helpdesk extension 4357 | 26 line 59 | PASS |
| 13 | 10771 | 500 euros / 30 days vs 1000 / 90 | 27 line 53 | PASS |
| 14 | 11044 | gate threshold 0.85 | 28 lines 12, 46, 57 | PASS |
| 15 | 11552–11565 | 78% on 18 questions, threshold 85, up from 64 | 29 line 63 | PASS |
| 16 | 13205 | 10,000 req/day, 40% repeats, ~70% simple | 33 line 76 | PASS |
| 17 | 13092, 13173 | DAILY_LIMIT_USD 0.002; 0.001845 → 0.003776; requests 3–10 blocked | 33 lines 98, 101, 105 | PASS |
| 18 | 15230 | ≥85% on the 50-question test set | 40 lines 96, 154 | PASS |
| 19 | 15462 | 38 percent thumbs-down | 40 line 126 | PASS |
| 20 | 16396, 16405–16408 | ≥80% weekly active; 600/day = 18,000/month, $0.30/$1.20 → $6.48 | 44 lines 24, 75, 80 | PASS |

Note: the notes use two flash price sheets. Topic 4 L3 uses $0.10/$0.40, and the T33/T35/P3 labs use $0.30/$1.20. Each topic file mirrors the sheet its own section uses, which is correct.

## Diagrams check
Every topic file's Diagrams section lists every image that `_topic-map.md` gives for that topic: 90 images across topics 1–41 (41 topic folders), with none missing and none extra. Topics 42–44 have no images, and none are listed. The map's HHMMSS lists also match the files in each `Topic N` image folder on disk.

## Method
- Banners were enumerated with `grep -nE "^-{5,}.*[A-Za-z]"`, giving 104 lessons, 67 quizzes, 86 tasks and 44 topic banners. A script compared per-topic counts against the topic files.
- Fidelity was read in five parallel slices (1–10, 11–19, 20–29, 30–37, 38–44). Each slice read the full notes range against its topic files. The two WRONG items were re-checked by hand against notes 14540–14544 and 15836–15850.
- Number checks were sampled from notes lines matching threshold/price patterns and grepped in the topic files.

## Fixes applied (date 2026-10-29)

Each fix was checked against the notes at the cited line before it was written. Mermaid blocks and section structure were left unchanged. Result: **44 of 44 FIXED, 0 not fixed.**

| # | Topic | Status | What was done |
|---|---|---|---|
| 1 | 01 L3 | FIXED | The 09:00 step now says about a quarter of the wiki-export pages are empty templates. |
| 2 | 03 T1 | FIXED | Step 1 now says line 1 of `steps.txt` is the starting sentence and each later line adds one token. |
| 3 | 04 T2 | FIXED | The exact generator command now writes to `/root/tokens-cost/big-input.txt`; Done now requires both `big-input.txt` and `limit-error.json`. |
| 4 | 07 T1 | FIXED | Added `/root/fde-choosing-a-model/{race.sh,flash.json,pro.json}`. |
| 5 | 07 T2 | FIXED | Added the `/root/fde-choosing-a-model/choices.txt` path, the exact `name: model` format and "only lab model names". |
| 6 | 08 T1 | FIXED | Added the `/root/fde-prompting-basics/` paths for `summary-prompt.txt` and `summary-output.txt`. |
| 7 | 08 T2 | FIXED | Added the `tag-prompt.txt` path, the "at least 2 solved examples" minimum and "save only the reply text" to `tag-output.txt`. |
| 8 | 08 T3 | FIXED | Added the `status-line.py` path and the rule that `status-line.txt` must be exactly one line. |
| 9 | 09 T1 | FIXED | Added the `/root/fde-production-prompting/` file paths and both test inputs, quoted. |
| 10 | 09 T2 | FIXED | Added the repo path `/root/fde-production-prompting/promptrepo`; Done = the git log shows both prompt versions. |
| 11 | 10 T1 | FIXED | The exact prose prompt is quoted; `prose-reply.txt` and `parse-result.txt` now have full paths. |
| 12 | 10 T2 | FIXED | Added the `/root/fde-structured-output/` paths, "exactly as given" with seed data at notes 3034–3041, and the allowed category and priority values. |
| 13 | 10 T3 | FIXED | Added `/root/fde-structured-output/{pipeline.py,record.json,failures.txt}`, with `failures.txt` in append mode (verified against notes 3293). |
| 14 | 11 T1–T3 | FIXED | Added a line under Tasks: `deepseek-v4-flash`, `/root/fde-tool-calling/`, and the scripts `weather-tool.py`, `loop.py` and `dispatcher.py`. |
| 15 | 12 T1–T3 | FIXED | Added a line under Tasks: `deepseek-v4-flash`, `/root/fde-conversation-state/`, and the scripts `forget.py`, `chat.py` and `capped-chat.py`. |
| 16 | 13 T1, T2 | FIXED | Added `compare.py`, the step that creates `tickets.txt` (seed data at notes 4539–4548), `search.py`, `nearest.txt` and `text-embedding-3-small`. |
| 17 | 14 T1, T2 | FIXED | Added the step that creates `snippets.txt` (seed data at notes 4706–4713), `build_store.py`, `query.py` (with the rebuild-if-missing step) and `text-embedding-3-small`. |
| 18 | 15 T1, T2 | FIXED | Added the step that creates `/root/fde-rag-pipeline/chunks.json` (seed data at notes 5068–5075 and 5244–5251), `rag.py`, `break_retrieval.py` and the embedding model. |
| 19 | 16 T1–T3 | FIXED | Added the directory plus the steps that create `policy.md`, `manual.txt` (blank lines kept, 5 paragraphs) and `export.txt`, with seed lines for each. Added the T2 script `compare_chunks.py` with `text-embedding-3-small`, and the T3 script `clean_export.py`. |
| 20 | 17 T1–T3, L1 | FIXED | Added the directory, the steps that create `runbook.json` (rb-06 is the long note) and `candidates.json` with seed lines, and the scripts `rank_check.py`, `hybrid.py` and `rerank.py`. The L1 lab line now says the scores came from `text-embedding-3-small`. |
| 21 | 18 T1, T2 | FIXED | Added the directory, `grounded.py` and `cite.py`, and the verbatim context lines for fac-1..3 (notes 6537–6539) and ref-1..4 (notes 6673–6676). |
| 22 | 19 T1, T2 | FIXED | Added the directory, `docs.json` (seed data at notes 6886–6893), `leak.py` with `text-embedding-3-small`, and `safe_search.py` with the rebuild-`index.json`-if-missing step. |
| 23 | 23 T2 | FIXED | Added the token `demo-secret-123` and the check `grep -c "demo-secret-123" /root/customer-apis/auth_agent.py` = 0. |
| 24 | 23 T2 | FIXED | Added that the auth mock serves only orders 1001 and 1002. Seed data for `auth_api.py` is at notes 9013–9043. |
| 25 | 26 L2 | FIXED | Added the rule that a desk-only set can score 95 percent while real users fare much worse. |
| 26 | 26 T1, T2 | FIXED | Added `/root/golden-datasets/courier-docs.txt` (notes 10059–10080) and `tickets.txt` (notes 10236–10258). |
| 27 | 27 T2 | FIXED | Added `rubric-v1.txt` saved verbatim (notes 10649–10651), `rubric-v2.txt`, the rubric path passed to the judge, and `deepseek-v4-flash`. T1 also now names `judge.py` and the model. |
| 28 | 28 T1 | FIXED | Added that `/root/regression/run_eval.py` asks `deepseek-v4-flash` each golden question, with the prompt file as the system prompt. |
| 29 | 29 T1 | FIXED | Added `hitrate.py` and `text-embedding-3-small` in one batch. |
| 30 | 29 T2 | FIXED | Added `faithfulness.py` with `deepseek-v4-flash` as the judge. |
| 31 | 31 T3 | FIXED | Added `/root/fde-guardrails/rag_safe.py`, `deepseek-v4-flash`, `safe_answer.txt`, and `docs.json` saved exactly (notes 12162–12166). |
| 32 | 37 T1 | FIXED | Added `/root/fde-discovery-scoping/brief.txt` (notes 14527–14539) and the `scoping.md` path. |
| 33 | 37 Rules | FIXED (WRONG) | The rule now reads "must contain these 4 H2s, spelled exactly". The same overstated wording ("exactly these H2s") was also corrected in 40 Rules and 41 Rules, for consistency with notes 15179 and 15677. |
| 34 | 38 T1 | FIXED | Added `/root/fde-rapid-prototyping/docs/{vpn,passwords,devices}.txt` with seed lines and key facts, `store.json`, `answer.txt`, `text-embedding-3-small` and `deepseek-v4-flash`. |
| 35 | 40 T1 | FIXED | Added `/root/fde-pilot-metrics/success-criteria.md` with the 4 H2s named. |
| 36 | 40 T2 | FIXED | Added the four `/root/fde-pilot-metrics/` files, seed lines (notes 15354–15358), and the exact question, answer and feedback values of the new entry. |
| 37 | 40 L2 | FIXED | Added the review-meeting rule: logged, root cause, fix date, score since; a managed failure beats a hidden one. |
| 38 | 41 T1 | FIXED | Added `/root/fde-production-handoff/runbook.md`. |
| 39 | 41 L2 | FIXED | Added the three-role failure path (reviewer catches, operator fixes, owner sees the trend). |
| 40 | 42 T1 | FIXED | Added the seed command, `/root/project-1/docs/` (13 files), the exact covered and trap questions, and the 5 deliverable paths. |
| 41 | 42 T1 step 2 | FIXED (WRONG) | The step now says split each chunk whose half-length is over 50 chars (i.e. over about 100 chars), which matches Rules line 53 and notes 15843–15844. |
| 42 | 43 T1 | FIXED | Added the seed command, `/root/project-2/` with all 5 files, and `http://localhost:8100/orders/<order_id>`. |
| 43 | 44 T1 | FIXED | Added the seed command, `/root/project-3/`, and `http://localhost:8200/shipments/<id>` (verified against notes 16433). |
| 44 | 25–30 | FIXED | Removed the trailing stray fence from all six files. Every topic file now has an even number of fences. |

Cross-cutting "save exactly as given" pointers: in addition to rows 12, 16–22, 26, 27, 31, 32, 34 and 36 above, "Seed data: notes lines A–B" was added to 05 T2 (1183–1195), 23 T1 (8759–8784), 24 T1 (9391–9396), 32 T1 (12325–12328, 12333–12334), 32 T2 (12493–12500, and the 4 answerable questions are now listed), 33 T3 (13053–13055), 35 T2 (13728–13737), 35 T3 (13870–13881) and 36 T1 (14149–14156). The first and last line of every cited range were checked against the notes.
