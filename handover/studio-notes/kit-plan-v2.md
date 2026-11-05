# Assembly Kit plan v2

Author: Hadavin lead session, for the owner. Date: 2026-11-05 (UTC; IST = UTC+5:30).
Status: DRAFT for EGM plan review round 2 of max 3. Replaces kit-plan-v1.md. Answers review round 1 (design, readiness, comprehension, structure reviewers; findings quoted by short names below).
Builds on plan-v3 (the frozen Core v1 plan; glossary in plan-v3 section 1; rules in plan-v3 section 4) and amendments.md. The Assembly Kit starts only after Core v1 is done (plan-v3 package P8c).
Package ids here start with AK (Assembly Kit) so they never clash with `K6` (the pilot-kernel measurement) or the folder `k1b` of plan-v3.

## 1. What this gives the owner, in plain words
At the end you can: (1) pick, for a new client, the closest ready "shape" from six working examples, each with passing tests on made-up data; (2) copy its recipe, change the configuration and write only the client's own rules, prompts and test set; (3) run the joined-pipeline test harness, which proves the pieces work together and that personal data, spend and customer separation stay safe; (4) give an honest estimate from the mapping playbook; (5) quote one measured example (AK8) as an example, never as a promise.
It will NOT: shorten discovery, getting the client's data, building the client's test set from their real examples (expert hours), the security review in their cloud, deployment or the acceptance period; guarantee answer quality (passing tests prove the plumbing, not quality on real documents); read scanned documents unless AK0 finds a licensed default; connect to the client's source systems for you (one connector per source is client-specific work); cover regulated or licensed work (outside Hadavin's positioning); cover shapes that are not in the six (extra build needed).
What you may say to a client before AK8 exists: "I have ready-made building blocks for several kinds of projects. The software part goes faster. I cannot name your project's time until I have seen your documents and access and you have given me a test set of your real examples." Never a number of days before AK8, never "quality is guaranteed", never "we read scans".
Industries versus shapes: the kit covers SHAPES (what the system does), not industries (the client's field). An industry fits when its work has one of the six shapes and is not regulated or licensed; industry knowledge goes into the client's rules, prompts and test set.

## 2. New terms (plan-v3 section 1 defines the rest)
| Term | Meaning |
|---|---|
| shape | a kind of project: what goes in, what the system does, what comes out |
| recipe | a runnable, tested example of one shape on made-up data with the fake model |
| kind | a replaceable part with a fixed interface, a default and an alternative (plan-v3) |
| RAG | answering questions from the client's own documents: find the relevant passages, then write an answer that cites them |
| chunk, chunker | a passage of a document, and the part that cuts documents into passages |
| embedding, embedder | a list of numbers that stands for the meaning of a passage, and the part that makes them |
| vector store | the database that finds passages whose numbers are close to the question's |
| retriever, reranker | the part that picks passages for a question; an optional second pass that re-orders them |
| golden set, buckets | the client's real examples with the right answers, sorted into easy, hard and trap (questions that must be refused) |
| abstain, false abstain | the system refuses to answer; refusing when it could have answered |
| grounding | checking that an answer is supported by the passages it cites |
| prompt injection | text inside a document that tries to give the model orders |
| tenant | one customer of the system; one tenant must never see another's data |
| terminal state | a message or job ends in exactly one final state (done, needs a person, refused) |
| fault injection | breaking things on purpose in a test (timeouts, bad replies) to see the system cope |
| masking wrapper | the part that hides personal data before text leaves the system (plan-v3 P5c) |
| meter | the part that counts spend and refuses calls over the cap (plan-v3 P4b1) |
| shape coverage matrix | a table: which shape each client request needs, which parts exist, which are missing |

## 3. Packages
Tier A and Tier B are defined in plan-v3 section 4 rule 3. Here all AK packages except AK0, AK6, AK7 and AK8 are Tier A by this plan's decision (they touch masking, spend, permissions or tenant separation).
Columns: Id | What (one sentence; detail in the ticket) | Depends on | Tier

| Id | What | Depends on | Tier |
|---|---|---|---|
| AK0 | Research and decisions note (`handover/ak0-decisions.md`): inventory what the core and the studio template already have (`extract.py`, `guard/injection.py`, `guard/judge.py`, `guard/egress.py`, `k1b/replay.py`, `llm/fake.py`, `sources/`, `evals.py`, `templates/project/`), list options with cost, licence and risk for each RAG part, adopt the bible defaults (Postgres vector search plus full-text search; no reranker by default; reranker and managed stores as alternatives) unless a reason is written, write the masking policy for RAG (what is masked when stored and when queried, same pseudonyms in both, where raw text lives and who reads it, fail closed), the tenant-separation design (namespace per tenant or tenant column plus filter, and why), and the file-overlap table | Core v1 (P8c) | B |
| AK1 | The pipeline step contract: one standard shape (input record with tenant and allowed-readers fields, output record, result of done, needs a person or refused, cost and audit hooks) plus ONE shared gate every call that sends text outside the process goes through (mask, meter, audit, no-training flag) for the llm, embedder, reranker and scan readers; also takes over the tenant namespace of plan-v3 P7b (P7b is retired by amendment); test file `tests/test_pipeline_step_contract.py` | AK0, P6a, P4b2 | A |
| AK2a | Reader and chunker: PDF text reader with a per-document quality report (characters per page, share of non-text, language, suspected scan; a poor document goes to "needs a person" and is not indexed), a cleaning step with a removal report, structure-aware chunking; sample files under `tests/fixtures/kit/docs/` (text PDF, corrupt PDF, empty PDF, PDF with an injected instruction) | AK1 | A |
| AK2d | Ingestion lifecycle: a manifest per document (id, content hash, source date, chunk ids, readers); a re-run adds, updates (atomic replace), deletes (tombstone then removal) and re-permissions; tests: a deleted document returns zero hits, a user who lost access sees nothing | AK2a | A |
| AK2b | Embedder and vector store kinds: a deterministic fake embedder for tests (no paid or network call), an in-memory store for tests, the real default and alternative from AK0 in an opt-in job; an index manifest (model id, dimension, build date; a query against an index built with another model fails loudly); re-index by building a second index and swapping; every embedding call through the AK1 gate; the embedding price record and batch reserve/settle against the meter; stop and resume at the spend cap without duplicate chunks | AK2d, P4b1, P4b2 | A |
| AK2c | Retriever kind: filter by tenant and allowed readers BEFORE scoring (a user who sees 3 of 1000 chunks still gets the requested count), the same filter on every lane (keyword lane, cache, citation lookup); retrieval metrics (recall at k, rank of the right chunk, zero-hit alarm); reranker interface with "none" as default | AK2b | A |
| AK3 | Grounding and citation check: promote the grounding, numbers check and evidence-id code from Warden/Jagrat (plan-v3 P7h is owned by this package); every retrieved chunk goes through the injection check and is fenced as data; refuse before calling the model when no chunk passes a similarity floor; cited ids must be among the chunks sent; refusal read from a status field; report abstain and false abstain separately with a worked example | AK2c | A |
| AK4a | Joined-pipeline test harness, first part: run a whole pipeline with the fake model and recorded replies (reuse `k1b/replay.py`, `llm/fake.py`, `evals.py` buckets and gates, absorbing plan-v3 P7f); checks run on every pipeline run: no personal data in logs (a canary string must not appear), spend never above the cap including a many-process run, a job ends in exactly one terminal state, tenant A never sees tenant B; fault injection (timeout, 429, bad reply, partial reply, injected document); each check has a test that fails when the check is broken on purpose | AK1 merged | A |
| AK4b | Harness, second part: re-run every check and add the retrieval faults (embedder timeout mid-ingest, store down, reranker garbage, model/index mismatch, duplicate delivery, partial index write) over the RAG chain; the load item is called a wiring check | AK3, AK4a | A |
| AK5 | Recipes, each with its own end-to-end test set and a "what this does not do" section, each depending only on the parts it uses: (a) document intake with an approval queue (existing approvals kinds), (b) RAG questions with citations (AK2c, AK3, AK4b), (c) triage and sorting with escalation to a person (AK1, AK4a), (d) governed operations from the Jagrat/Warden shape: plan, approval, execute, verify, roll back, stop switch (plan-v3 P2a, plus the needed part of P7i/P7j), (e) governed customer actions from the refunds/dealdesk shape: draft, approval, signed action, no duplicate (plan-v3 P3b), (f) questions over the client's database from the ask-your-data shape (safe query checks) | per recipe | A |
| AK7 | Project-mapping playbook with the shape coverage matrix: from a client brief name the shape, the parts, the missing pieces, the client-specific work and an estimate with what could stretch it; the honest limits of section 1 | AK5 | B |
| AK8 | Measured proof: a builder who did not write AK5 assembles one sample project from a recipe using only the kit, on a messy real-shaped document set; raw timing log (start at the first command, stop when the end-to-end tests pass; wall time and hands-on time), defect list, what was not covered, written by that builder and checked by a separate runner; no pass threshold, the record is the result; a second run after fixes | AK7 | B |
Deferred with a trigger: AK6 project scaffolder (trigger: AK8 shows copy-and-edit of a recipe is the slow step); reranker implementation (trigger: AK2c metrics show misses a reranker would fix); scan reading (trigger: AK0 finds a licensed default or a client needs it); report-drafting recipe (trigger: a client asks).

## 4. Order
AK0; then AK1; then AK2a and AK4a (AK4a starts when AK1 is merged); then AK2d, AK2b, AK2c in order; then AK3; then AK4b; then recipes as their parts land: (c) and (a) after AK4a, (d) and (e) after their plan-v3 packages, (f) after AK4a, (b) after AK4b; then AK7; then AK8. Plan-v3 packages P7a, P7b, P7f, P7h are absorbed or owned as written above; the other v1.1 packages continue in parallel only where files do not overlap (AK0's file-overlap table decides; hot-file rule 10 of plan-v3 applies).

## 5. Rules for every AK package
Plan-v3 section 4 (ticket first, evidence by a separate runner, two independent reviews, stop rule, fail-before tests, one pull request per row, least privilege, model routing) plus: every part that sends text outside the process goes through the AK1 gate (a lint test lists every such kind); retrieved text is data, never instructions; made-up data and the fake model in tests; real embedding or model calls only in an opt-in job with the owner's approval and numbers; each recipe states what it does not do.

## 6. Done conditions
Command form everywhere: `uv run --all-extras --group test pytest <path>` in the core repository root. A file is created by the package named in the second column.
| Condition | Created by | Command or file | Expected |
|---|---|---|---|
| Step contract | AK1 | `tests/test_pipeline_step_contract.py`; `tests/test_outbound_gate_lint.py` | pass |
| Reader and chunker | AK2a | `tests/test_kit_reader.py tests/test_kit_chunker.py` | pass; poor and corrupt files go to "needs a person" |
| Ingestion lifecycle | AK2d | `tests/test_kit_ingest_lifecycle.py` | pass |
| Embedder, store, index | AK2b | `tests/test_kit_embed_store.py` | pass on the in-memory store; embedding payload never contains the seeded personal data string |
| Retrieval | AK2c | `tests/test_retrieval_isolation.py tests/test_retrieval_metrics.py` | pass; mutating the filter turns the isolation test red |
| Grounding | AK3 | `tests/test_grounding.py` | pass; abstain and false abstain reported separately |
| Harness | AK4a, AK4b | `tests/test_pipeline_invariants.py` | pass; each check fails when broken on purpose |
| Recipes | AK5 | `tests/recipes/` | each recipe passes its own end-to-end set |
| Mapping playbook | AK7 | file `handover/kit-playbook.md` plus a script check that it has the matrix and the limits section | present |
| Measured proof | AK8 | file `handover/kit-proof.md` plus raw log `handover/kit-proof-log.txt`; script check for start time, end time, defect count, commands run | present and checked by a separate runner |

## 7. Owner decisions (asked once, after AK0)
(a) Approve AK0's defaults (cost, licence). (b) Is scan reading wanted if only a paid option exists. (c) Approve the estimate wording in AK7. (d) May the AK8 number be shown to clients. (e) Any real model or embedding spend for the opt-in job (needs numbers).

## 8. Open risks
No scan-reading default may exist. Real documents are messier than made-up ones. A client's security review can reject a default. Licences can change (AK0 dates its check). The six recipes are written by the same studio that wrote the parts; AK8 uses an outside builder for that reason. The kit grows the work after Core v1 by many packages; no total is promised before AK0.
