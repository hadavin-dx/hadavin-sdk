# Diagram verification: topics 1 to 20

**Date:** 2026-10-29
**Method:** I opened every image listed in `_topic-map.md` for topics 1 to 20 with the Read tool and compared each one with its Mermaid redraw in `topics/NN-*.md`. For each image I checked that:
- every box and label is present with the same wording;
- every arrow points the same way;
- every branch, decision and decision label is present;
- every loop is present;
- the grouping into subgraphs matches.

**Result: 47 images checked. 47 PASS, 0 FAIL.** No corrected Mermaid blocks are needed.

| Topic | Image | Result | Notes |
|---|---|---|---|
| 1 | 175112 | PASS | Four steps in "one engagement", dashed arrows top to bottom |
| 1 | 175120 | PASS | Vendor side (ML engineer, architect) has two dashed arrows to customer side (FDE). Layout note A |
| 1 | 175134 | PASS | Five steps in "one FDE day" |
| 2 | 175554 | PASS | Four stages in "twelve week engagement" |
| 2 | 175604 | PASS | Four exit artifacts, wording matches |
| 3 | 175637 | PASS | Loop: text so far → predict next token → add token to text → text so far. The subgraph has an arrow to "stop token ends the loop" |
| 3 | 175646 | PASS | Training subgraph has an arrow to the inference subgraph |
| 4 | 175717 | PASS | your text in → prompt_tokens, model text out → completion_tokens, both → total_tokens |
| 4 | 175727 | PASS | Four boxes and no arrows, as in the image. Layout note B |
| 4 | 175743 | PASS | Two products feed into "add them" |
| 5 | 175814 | PASS | Loop: loop takes one item → build prompt → handle reply → loop takes one item |
| 5 | 175822 | PASS | Four steps in a line |
| 6 | 175856 | PASS | Three inputs → API inside the subgraph, and the subgraph → JSON response. Layout note A |
| 6 | 175907 | PASS | Script subgraph → API → response object → content and usage. Layout note A |
| 6 | 175916 | PASS | system → user question → user question, and the subgraph → model follows rules. Layout note A |
| 7 | 175945 | PASS | Three boxes in "the trade" → pick per use case |
| 7 | 175955 | PASS | Two decisions with their no/yes labels, all correct |
| 8 | 180032 | PASS | Prompt subgraph (4 boxes) → model → answer in the same pattern |
| 9 | 180109 | PASS | Five sections of the system prompt → every single call |
| 9 | 180123 | PASS | yes/no decision, and the loop back from fix prompts to run test set |
| 10 | 180204 | PASS | Five-step line |
| 10 | 180218 | PASS | Five-step line |
| 10 | 180229 | PASS | "valid" decision: yes → use record, no → retry → parse again → failures file |
| 11 | 180304 | PASS | Six-step line |
| 11 | 180318 | PASS | Six-step line |
| 12 | 180359 | PASS | Two separate subgraphs (call 1, call 2) with no link between them, as in the image |
| 12 | 180407 | PASS | Six-step line |
| 12 | 180419 | PASS | Three boxes in "history sent" → model |
| 13 | 180447 | PASS | texts subgraph (3 boxes) → embedding model → vectors → cosine score |
| 13 | 180457 | PASS | question → embed question → cosine vs each, stored vectors → cosine vs each → highest score wins |
| 14 | 180534 | PASS | Four-step line |
| 14 | 180546 | PASS | Four-step line |
| 15 | 180631 | PASS | question and store.json (drawn as a cylinder) both → retrieve top k → … → answer |
| 15 | 180645 | PASS | ingestion → retrieval → generation, each with its failure box |
| 16 | 180719 | PASS | Five steps, with store drawn as a cylinder |
| 16 | 180730 | PASS | Two fans: small chunks and large chunks, two outcomes each |
| 16 | 180740 | PASS | Four-step line |
| 17 | 180907 | PASS | Two subgraphs with two boxes each and no arrows, as in the image |
| 17 | 180917 | PASS | query and store (drawn as a cylinder) each → vector top k and keyword matches → merge and dedupe → final candidates |
| 17 | 180929 | PASS | Four-step line |
| 18 | 181026 | PASS | retrieved chunks and question → model with grounding rules → answer from chunks or NOT IN SOURCES |
| 18 | 181034 | PASS | labeled chunks and question → model → answer plus citation ids → show answer with sources |
| 19 | 181109 | PASS | HR drive and wiki → indexer → one flat store (drawn as a cylinder) → any user query → restricted chunk in results |
| 19 | 181117 | PASS | user identity and index (drawn as a cylinder) → filter → score → top k → model prompt |
| 20 | 181215 | PASS | user question → LLM → "the loop" (LLM picks a tool ⇄ your code runs it) → final answer. Mermaid note C |
| 20 | 181234 | PASS | Agent subgraph: goal → LLM picks next step ⇄ tool result. The image is cut off partway through the chain |
| 20 | 181248 | PASS | Chain subgraph: fetch data → format → LLM summarize → save. This is the rest of the chain from 181234, and one Mermaid block covers both images |

## Notes (not failures, optional)

None of these notes changes a label, an arrow, a branch, a loop or a grouping, so all of these images still PASS.

**A. Direction inside a subgraph (Topic 1 175120; Topic 6 175856, 175907, 175916).**
- **What differs:** these redraws use `flowchart LR` without a `direction` line inside the subgraph. The image stacks the subgraph's contents vertically, except Topic 1 175120, where the two vendor boxes sit side by side. In Topic 6, 175856's inputs sit in a row above API.
- **Effect:** Mermaid's default puts the subgraph contents in a different orientation from the image. The content is the same.
- **Optional fix:** add `direction TB` inside the subgraph for 175907 and 175916, as Topics 7, 8, 9 and 12 already do. Only the look changes.

**B. Topic 4 175727.**
- **What differs:** the four boxes have no links between them, so `flowchart TD` puts them in one horizontal row. The image stacks them vertically.
- **Optional fix:** add invisible links. Only the look changes:
  ```mermaid
  flowchart TD
    subgraph W["one context window"]
      A[instructions] ~~~ B[pasted documents] ~~~ C[question] ~~~ D[space for the answer]
    end
  ```

**C. Mermaid structure (Topic 20 181215).**
- **What differs:** the redraw links to `LOOP` (`L -.-> LOOP`) before it declares `subgraph LOOP`. Some renderers create a stray node named `LOOP` instead of linking to the subgraph. I did not test which renderers do this.
- **Optional fix:** move the `L -.-> LOOP` line below the `end` of the subgraph if a renderer shows a duplicate box.
