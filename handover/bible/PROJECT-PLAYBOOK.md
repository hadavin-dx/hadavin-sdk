# Project playbook: a new project or demo, step by step

This is the ordered procedure for **every** new Hadavin project: a client build or a demo, of any type (docs Q&A, support assistant, invoice/PO, agents, data pipeline, anything new). It adds no new method. It puts the bible's stages, rules and exit artifacts in the order you do them, so that no step is skipped.

- **Authority:** [LIFECYCLE.md](LIFECYCLE.md) (stages, gates, exit artifacts), [RULES.md](RULES.md) (rules R1–R374, R413–R447 and any later R-number, and "Deliverables per stage"; R1–R291 follow the course topic order, but rules or parts marked [Hadavin practice] are studio rules; R292 onward are studio additions, listed in README), [ROLES.md](ROLES.md) (hats, who decides), [TIMELINES.md](TIMELINES.md) (calendar) and `topics/NN-*.md`. If this file disagrees with them, they win and this file is fixed the same day.
- **Labels:** a citation like `R45` or `37 T1` is course-derived. **[Hadavin practice]** marks studio practice that is not course text.
- **Names** [Hadavin practice, owner 2026-10-30 and decisions 2026-11-01 evening item 4]: everything a client reads (proposals, SOWs, contracts, invoices, and the templates once copied into a project) says **Hadavin**. Studio-internal names (the folder `Hadavin`, `hadavin-sdk`, memory and handoff paths, the `[Hadavin practice]` label) are all Hadavin since the rename of 2026-11-03. Never write "Hadavin" in a client deliverable.
- **Templates:** `..\templates\project\` holds one template per exit artifact, and `STAGE-CHECKLIST.md` is the tick list. Copy them; never write an exit artifact from memory.
- **The one rule (R2, R5):** compress the calendar, never a stage. A stage ends only when its exit artifact exists and the person who decides has signed. When pushed to skip: "Happy to move on once we have X." (R3)
- **Order:** doing Build after the PoC exit, and Prove plus Price before the pilot group goes live, is [Hadavin practice] (pricing-plan §3.2, §3.5), supported by R161, 43 T1 and 38 Q2. Stage 3 steps 1–2 (baseline, success criteria) still finish before pilot day 1.
- **Demos** [Hadavin practice]: a Hadavin demo runs the same seven steps with every exit artifact. The owner is the sponsor. A studio marketing demo may use synthetic data when it is labelled on screen ("Staged on synthetic data"); this is a deliberate exception to R236 ("use real customer data, live") and R48, decided by the owner on 2026-11-01. It makes no accuracy claim and never satisfies the Stage 2 exit, which needs the client's real data and a real user (R48). Real client data is not used in laptop sessions at all until the data-handling rule exists (Step 0.10). A demo for a named prospect uses the prospect's real data or says plainly that it does not. The "real user" and pilot group are named people other than Claude. For a demo, payment, invoice and contract-clause items read "the owner's written go, dated in the handoff" (evidence `demo: N/A`); client sign-offs become the owner's own.

---

## How the seven steps map onto the four lifecycle stages

The course lifecycle has **four stages** (02 L1, Topic 1 image 175112, Topic 2 image 175554). Hadavin works through them in seven steps. Build, Prove and Harden are not extra stages: they are the course's own steps inside stages 2, 3 and 4 (LIFECYCLE Stage 2 step 2, Stage 3 step 3, Stage 4 step 1).

| Step | LIFECYCLE stage | Course arc (44) | Exit artifact (file) | Who signs | Hadavin calendar (TIMELINES) |
|---|---|---|---|---|---|
| 0 Setup | Day 0 entry | — | folders, handoff, EGM brief, access checklist | Hadavin owner (order and price) | Day 0 |
| 1 Discovery | 1 Discovery and scoping | scope | `docs\scoping.md`, `docs\eval-contract.md`, frozen test set | Sponsor | Days 1–5 |
| 2a Prototype / PoC | 2 Prototype | build | recorded demo on real data, `egm\<p>\demo-script.md`, user's "useful" | Real user + sponsor | Days 6–~9 (demo by about day 4 of the stage) |
| 2b Build | 2 Prototype (build-topic map, LIFECYCLE Stage 2 step 2) | build | typed package, portal configured, gate green in CI | — (gate, not a person) | to Day 15 |
| 3a Prove (evals) | 3 Pilot (step 3, "Build the proof") | prove + price | `evals\golden.jsonl`, scores, gate, `docs\score-report.md`, `docs\cost-estimate.md` | Sponsor (acceptance run) | end of week 3 |
| 3b Pilot | 3 Pilot | prove | `docs\success-criteria.md` (before day 1), `docs\pilot-report.md` with the verdict | Sponsor | weeks 4–6 or more |
| 4a Harden | 4 Hardening and handoff | hand off | hardening boxes ticked with evidence | — (gate) | after the pilot's go (day-one guards built in 2b; training started in 3b) |
| 4b Handoff | 4 Hardening and handoff | hand off | `docs\runbook.md`, `README.md`, named owner, exit-test week | Sponsor; owner's manager agrees the owner | last week(s) |

**Pilot means one thing** [Hadavin practice, owner delegation 2026-11-01, Q2]. In client documents the course's pilot (Stage 3, about ten real users in daily work) is the **user pilot** (Step 3b), and nothing else is called a pilot. The first paid phase is **Week 1 (target setting)**: the target is set in its week 1 on the client's real data, then the system is built and proved (the **build**). The proposal and SOW alone may add "sometimes called a paid pilot" so a prospect who searches the term recognises it. The product name "watch-only pilot" stays (it is the user pilot). Mapping:

| Sales-flow term | Playbook step |
|---|---|
| free call and architecture plan | before Step 0 |
| demo on sample data (pre-sale) | a studio demo, not Stage 2 |
| fixed quote and first payment | Step 0 |
| Week 1 (target setting; the Week-1 Fee buys the frozen test set, the baseline report and the proposed target) | Step 1 (1.10, 1.11) and the first scored runs |
| build (the rest of the first paid phase) | Steps 2a, 2b and 3a (build and prove) |
| go live (after the final payment) | Step 3b, the user pilot |
| care plan | after Step 4b |

The cheap exits (R4; 38 L1; pricing-plan §3.2 [Hadavin practice]) sit after Discovery, after the PoC demo and after Prove (the acceptance run and final payment). After the user pilot the exits are the sponsor's options (continue, close or restart, R262), not a refund: the final payment is already due (3a). Killing a bad use case early is a success (02 L1). Superseded by this text on 2026-11-01: "the cheap exits sit ... after the Pilot".

---

## Rules that apply at every step

- **Hat tag on every decision** (R19, ROLES §6): `[ARCH]` advise, `[FDE]` ship, `[MLE]` model layer. One record per hat when a change crosses hats. Template: `decision-record.md`.
- **EGM wherever it helps** (owner rule 2026-11-01, root `CLAUDE.md`; superseded by this text on 2026-11-01: "EGM on every plan, prompt, design or change, even a small one", owner rule 2026-10-28) [Hadavin practice]. Run it for every plan, prompt, script, design, document, config, cloud/DNS action, client-facing work and any code change that is more than trivial or where fresh reviewers could catch gaps. Skip only for typos, status checks, read-only questions and one-line mechanical edits, and write "EGM skipped: reason". "Urgent" and "the owner said go" are not reasons to skip. When in doubt, run it.
  - new idea → `egm:egm-brainstorm`; brief or notes → `egm:egm-draft`;
  - big plan → `egm:egm-review` (5 stages); small item → `egm:egm-review-loop` (1–2 reviewers);
  - after every review → `egm:egm-resolve`;
  - new or moved folder → `egm:egm-bootstrap`; after each merge batch and before any "done" → `egm:egm-drift-report`.
  - Invoke every EGM skill through the `Skill` tool (`egm:egm-*`), never by reading its SKILL.md in-thread: the Skill call is what switches the model (Opus 5.5 plans, Sonnet 5.5 reviews and builds). If the Skill tool refuses, tell the owner and ask him to type the command; do not fall back to reading SKILL.md. Superseded by this text on 2026-11-01: "EGM skills refuse the Skill tool: read ... SKILL.md ... and follow it in-thread". Artifacts go in `egm\<project>\`; no report means not done.
- **Sessions** [Hadavin practice]: start every Claude session on this project with its working folder set to `projects\<p>` (so `settings.local.json` memory applies).
- **Notes stay in the main folder** (owner rule 2026-10-29) [Hadavin practice]: memory in `memory\projects\<project>\`, handoff in `handoff\projects\<project>.md`, EGM in `egm\<project>\`, research in `research\<project>\`. The repo holds only what ships: code, tests, `README.md`, `docs\` (scoping, criteria, cost, score report, runbook, reports, decisions, demo recordings) and `evals\`. Before each commit, `git diff --cached --name-only` lists no notes, handoff, memory or EGM files.
- **Fix, don't defer** (owner rule 2026-10-29) [Hadavin practice]: a problem found is fixed and verified in the same piece of work. The only exceptions are (a) physically impossible now, (b) needs the owner, (c) needs a third party; each is stated with the exact next step and written in the handoff.
- **Safety rules** (root `CLAUDE.md`): no secrets, account ids or personal emails in any repo; no literals for env, region, account or model id (R17); zero extra money; deploys and DNS need the owner's yes; times in UTC and IST.
- **Parallel deals** (TIMELINES): at most 3 projects in active build; one significant change at a time per project; no client data or prompts cross projects.
- **Change control** [Hadavin practice, pricing-plan §3.2.5; 37 L1, 44 risks]: anything not in the signed `scoping.md` goes to the parking lot. A change is a written change order (price, dates, a new `scoping.md` version) signed by the sponsor and the Hadavin owner before work on it starts.
- **Client data** [Hadavin practice, owner decision 2026-11-01 evening item 10]: see Step 0.10. No real client data in laptop sessions or the Drive backup until the data-handling rule exists.

---

## Step 0 — Setup (Day 0)

**Entry gate** (TIMELINES Day 0):
- the signed order is paid: a Blueprint (paid discovery, 100% upfront), or a direct Core order after the free call and the architecture plan (`egm\pricing\pricing-plan.md` §3.2.3, §3.5; there is no free sample check, removed 2026-10-30). The accuracy target is set in week 1 of the paid phase. Payments follow the one schedule of decisions 2026-11-01 evening item 5 (Net 14; the old "20% pilot fee" is now the **Week-1 Fee** and buys a deliverable the client keeps: frozen test set, baseline report, proposed target). Superseded by this text on 2026-11-01: "a direct order after the free sample check";
- data and system access granted, or a dated request for it; sponsor named;
- fewer than 3 projects in active build (TIMELINES).

**Steps:**

| # | Step | Hat | Source |
|---|---|---|---|
| 0.1 | Confirm the owner's signed order is filed in the handoff (the Hadavin owner signs the order and the price; Claude never does) | — | ROLES §3 |
| 0.2 | Create the repo, memory, handoff, EGM and research folders (commands below) | [FDE] | root `CLAUDE.md` "New project setup" |
| 0.3 | Copy `templates\project\` into place (table below) | [FDE] | this file |
| 0.4 | Run `/egm:egm-bootstrap` on the new repo folder | [FDE] | EGM rule |
| 0.5 | Save the client brief verbatim to `research\<project>\brief.md` (course: `brief.txt` 37 T1, `customer-brief.md` 44 T1) | [FDE] | LIFECYCLE Stage 1 entry |
| 0.6 | Run `/egm:egm-brainstorm` on the brief; the RFC goes to `egm\<project>\` | [FDE] | EGM rule |
| 0.7 | Access checklist: which systems, which accounts, which cloud and region; the client's data classes (36 L1–L2); recorded in `docs\scoping.md` § Data sources and access | [ARCH] | ROLES §2 Day 0 |
| 0.8 | Confirm the client's cloud offers the Claude tiers needed in the client's region; recorded in `docs\scoping.md` § Target cloud and model provider | [MLE] | ROLES §2 Day 0 |
| 0.9 | Portal check: Portal v0 must pass CLIENT-PORTAL-SPEC §9 (`research\port-ui-catalog\CLIENT-PORTAL-SPEC.md`) before the order is signed (§0.2). If it does not, the owner either (i) dates v0's finish (§8.4) before Step 2b day 1, written under handoff "Owner actions", or (ii) signs a Discovery-only (Blueprint) order | [ARCH] | CLIENT-PORTAL-SPEC §0.2, §8.4, §9 |
| 0.10 | **Client data location** (standing rule, owner 2026-11-01). Real client documents, exports and samples are NOT placed in laptop sessions, in `projects\`, `research\`, `memory\`, `egm\` or `handoff\`, or in the Drive backup, until the owner has agreed a data-handling rule in writing. Until then, real client data stays in the client's environment and the work that needs it (Step 2a exit, the sealed acceptance run) runs there; the studio side uses synthetic data only. Safety net, not permission: the backup filter excludes any folder named `client-data\` at any depth (`<studio>/tools\hadavin_filters.txt`), so a file that must exist on the laptop goes there once the rule allows it. The rule must also settle how "nothing on Drive is ever deleted" (backup) fits the delete-or-return promise in the DPA, and a written deletion confirmation at close | [ARCH] | decisions 2026-11-01 evening item 10; RULES R12, R41 |

**Setup commands** (PowerShell; set `$p` first, a lowercase-hyphen slug) [Hadavin practice]:
```powershell
$lab = '<studio>/'; $p = '<project>'; $t = "$lab\templates\project"  # $p = lowercase-hyphen slug
if (Test-Path "$lab\projects\$p") { throw "projects\$p exists" }
New-Item -ItemType Directory -Force "$lab\projects\$p\.claude", "$lab\projects\$p\docs\decisions", "$lab\projects\$p\docs\demo", "$lab\projects\$p\evals", "$lab\memory\projects\$p", "$lab\egm\$p", "$lab\research\$p" | Out-Null
git -C "$lab\projects\$p" init
$s = [IO.File]::ReadAllText("$t\settings.local.json.template").Replace('<project>', $p)
[IO.File]::WriteAllText("$lab\projects\$p\.claude\settings.local.json", $s)
Add-Content "$lab\projects\$p\.git\info\exclude" '.claude/settings.local.json'
Copy-Item "$t\HANDOFF.md" "$lab\handoff\projects\$p.md"
New-Item -ItemType File "$lab\memory\projects\$p\MEMORY.md" | Out-Null
Copy-Item "$t\decisions-index.md" "$lab\memory\projects\$p\decisions.md"
Copy-Item "$t\README.md" "$lab\projects\$p\README.md"
Copy-Item "$t\scoping.md", "$t\eval-contract.md", "$t\success-criteria.md", "$t\cost-estimate.md", "$t\score-report.md", "$t\runbook.md", "$t\pilot-report.md", "$t\tool-safety-review.md" "$lab\projects\$p\docs\"
Copy-Item "$t\demo-script.md", "$t\STAGE-CHECKLIST.md" "$lab\egm\$p\"
Copy-Item "$t\golden.jsonl" "$lab\projects\$p\evals\golden.jsonl"
```
`WriteAllText` writes UTF-8 without a BOM, so the JSON stays valid. Check with `git -C "$lab\projects\$p" status --short`: `settings.local.json` must not be listed.

**Where each template lands:**

| Template | Lands in | Why there |
|---|---|---|
| `scoping.md`, `eval-contract.md`, `success-criteria.md`, `cost-estimate.md`, `score-report.md`, `runbook.md`, `pilot-report.md`, `tool-safety-review.md` (only for a project whose system calls tools, R317) | `projects\<p>\docs\` | Client deliverables (44 table); the README links them |
| `demo-script.md`, `STAGE-CHECKLIST.md` | `egm\<p>\` | Internal plan and gate record, not shipped; notes stay in the main folder. The demo recording ships in `projects\<p>\docs\demo\` with its trace ids (44 table #9), and the baseline worksheet's numbers go into `success-criteria.md` |
| `baseline.yaml`, `data-readiness.md`, `replay-report.md`, `engagement-scorecard.md`, `weekly-review.md`, `agent-incident-runbook.md` (engagement templates, added by kernel PR K0; used only for the incident-response pilot shape) | `projects\<p>\docs\` | Client deliverables. `baseline.yaml` `ceiling` is a copy of `scoping.md ## Success metric and ceiling`; `templates\test_k0_templates.py` checks the two match. The trifecta (R306) lives in `scoping.md ## Risks` |
| `decision-record.md` | `projects\<p>\docs\decisions\NNNN-<slug>.md`, one per decision | ROLES §6: records live in the client repo. This is the ONE home of the decision log (R305 step-ups included) |
| `decisions-index.md` | `memory\projects\<p>\decisions.md` | Pointer index only (number, title, date, path), so the studio can find the records without a second copy of them |
| `golden.jsonl` | `projects\<p>\evals\golden.jsonl` | 26, 43, 44; replace the 3 example lines |
| `README.md` | `projects\<p>\README.md` | LIFECYCLE Stage 4 |
| `HANDOFF.md` | `handoff\projects\<p>.md` | Notes stay in the main folder |
| `settings.local.json.template` | `projects\<p>\.claude\settings.local.json` | Memory goes to `memory\projects\<p>\` |

**Exit:** every Step 0 box in `egm\<p>\STAGE-CHECKLIST.md` ticked with evidence; the handoff names the stage ("Step 1 Discovery") and the next step. **Who signs:** the Hadavin owner (order and price).

---

## Step 1 — Discovery and scoping (stage 1: find the problem)

**Goal:** about 15 ideas → **one** use case that can visibly win in weeks; decline bad fits without losing the sponsor (37). **Write no code** (02 L1).

**Entry gate:** a sponsor with a request; the brief saved verbatim (LIFECYCLE Stage 1). Step 0 done.

**Steps** (LIFECYCLE Stage 1 order):

| # | Step | Hat | Rules / topics |
|---|---|---|---|
| 1.1 | Collect the wish list (about 15 ideas within an hour); turn "AI everywhere" into one painful, measurable problem; offer short team interviews | [FDE] | R20; 37 L1, 01 Q1 |
| 1.2 | Filter every idea in order: painful? → data reachable? → measurable win? Pass all three = candidate; fail one = parking lot with a written reason | [FDE] | R21–R23, R25, R31; 37 L1 (image 182710) |
| 1.3 | Prefer the boring, reachable, measurable idea, and internal users first | [FDE] | R26; 37 L1, Q1 |
| 1.4 | Screen the four bad-fit shapes; decline with the three-move "no"; never let an LLM own a lawsuit-grade decision; kill a doomed idea openly | [FDE] | R27–R30; 37 L2, Q2; 02 Q2 |
| 1.4a | Write the outcome with its ceiling number on the worst failure (one line under `## Success metric and ceiling`), narrow the intervention to one pattern, one workflow and a human who disposes, ask the design-changing questions by written questionnaire, list the data assumptions, check the three scoping traps (changed 2026-11-01; advice for a PoC or pilot under US$5k). Write the "how it breaks" lines under `## Risks` (mechanism, blast radius, human checkpoint) and answer the four architecture questions (know, act, remember, coordinate) in `scoping.md`; if the honest answer is a smaller scope or a decline, say so in writing | [FDE] + [ARCH] | R294–R298 |
| 1.5 | Map the data: four homes, smallest useful source first; sample documents, permissions and id formats in week one; where the data lives and who grants access on day one | [ARCH] + [FDE] | R23, R24, R36–R39; 24 L1, 16 L3, 19 L1, 36 L3 |
| 1.5a | Trifecta check, after the data map exists: untrusted content, private data and power to act never share one ungated path; record it under `## Risks` (changed 2026-11-01) | [ARCH] | R306 |
| 1.6 | Security pack: data classes, the data-flow answer, deployment by data class, the provider's data-processing terms; show the security engineer early | [ARCH] | R12, R40–R44; 36 L1–L2, Q1 |
| 1.7 | Set expectations about the model: frozen, learns nothing from use, can be wrong; "fine-tune on our data" is a knowledge problem → RAG | [FDE] + [MLE] | R8, R284; 03, 30 L2 |
| 1.8 | Workload profile per route (difficulty, human waiting, calls per day) and a first cost envelope per tier | [MLE] | R278, R209; 07 L2, 04 L3; ROLES §2 |
| 1.9 | Chain or agent per use case | [ARCH] | R99; 20 L2 |
| 1.9a | **Options first** [Hadavin practice, owner HARD guardrail 2026-11-04]: for every component that needs an outside tool (model provider, cloud, vector store, no-code automation, connector), list (a) the client's own tool, (b) a vendor tool used directly, (c) our code behind a swappable layer, each with cost and risk in plain words; climb the tool ladder (reuse, client tool, no-code node, MCP, plain RAG, and GraphRAG only when a golden set shows multi-hop or relationship questions, model features, custom code only for the brain; R447 gives the full ladder and the ladder line every plan carries). Hybrid (no-code plumbing, our code as the brain) is the first option we recommend; nothing is applied until the client has chosen. The client chooses and pays its own licences. Write the choice, who pays and who carries the risk if the tool breaks or changes in `scoping.md` § Tool choices and who carries the risk, in the quote and in the contract tool schedule. If the client does not choose, ask once and record the answer before continuing; never apply a default silently. Pilot data (owner decision 2026-11-04, B3): client data stays in the client's own cloud by default; a third-party tool may touch pilot data only if it is named in the signed tool list with the client's informed written yes; a pilot on a public model service with strict masking only when the client asks | [ARCH] | R445–R447; memory\options-first-then-decide.md, memory\tool-ladder-before-code.md |
| 1.10 | Measure 20–50 of the client's real samples. Build **two sets** [Hadavin practice]: a **tuning set** (Hadavin sees the answers; it feeds the starter golden set and the CI gate, which is advisory while the set is small, R326) and a **sealed scoring set** (the client keeps the answers; Hadavin never sees them before a scoring run's outputs are locked by checksum). Freeze items, scoring script and checksums. The accuracy target is counts on the sealed set ("N of M"), derived as in pricing-plan §3.2.5 (3 runs, worst count, margin, `pass_check.py`). Set sizes: `eval-contract.md` is the one home of the golden-set minimum. Superseded by this text on 2026-11-01: "freeze a test set of 20–50 items ... items, answers, scoring script, checksum" (one set whose answers Hadavin agrees) | [FDE] + [MLE] | TIMELINES Days 1–5; pricing-plan §3.2, §3.2.5 |
| 1.11 | Agree the eval contract: golden question source, written grading rule, numeric threshold; SMEs own the answers | [FDE] | R45, R159–R161; 25 L2, Q2 |
| 1.12 | Write the four handoff exit criteria now, and ask "who will own this?" Add the fifth, Hadavin's own: our access closed and the evidence filed (3a.12, 4b.12). Name a deputy for the operator and the owner, or record that none exists (4b.7) | [FDE] | R46, R276; 41 L1; decisions 2026-11-01 evening item 6 |
| 1.13 | Write `scoping.md` (both H2 sets) and get sponsor sign-off; page 1 is the one-pager (R33) | [FDE] | R32–R35; 37 T1, 44 T1, 02 L2 |
| 1.14 | Before any client access: draft the identity inventory (one identity per function, read rights, write rights, justification, the negative test planned) and agree it with the client's security engineer; deny-all start, no long-lived keys [Hadavin practice, owner 2026-11-01, changing needs owner's yes] | [ARCH] | R365-R367; 36 |

**EGM here:** `/egm:egm-draft` turns the brainstorm RFC and interview notes into the `scoping.md` draft. `scoping.md` is the big plan: `/egm:egm-review` (5 stages), then `/egm:egm-resolve`. `eval-contract.md`: `/egm:egm-review-loop`, then `/egm:egm-resolve`.

**Exit artifacts:**
- `docs\scoping.md`: both course H2 sets plus the Hadavin sections (template). Includes the idea list with pass/fail per filter (the parking lot), the data map, the security pack, the four exit criteria, `## Success metric and ceiling` and `## Assumptions about the data`.
- the identity table (each identity, read rights, write rights, justification, negative test) drafted and agreed with the client's security engineer before any client access (1.14; R365)
- `scoping.md` § Tool choices and who carries the risk, filled and copied into the quote and the contract tool schedule (1.9a; R446).
- `docs\eval-contract.md` and the frozen test set (file list and checksum).
- `docs\decisions\`: `[ARCH]` cloud route, deployment by data class, chain vs agent; `[MLE]` workload profiles.

**Exit test (02 L2):** the use case is on one page with a success number. No success number = discovery is not done.

**Exit / kill decision:**
- **Go:** exactly one use case passes all three filters, and data access is proven (a sample export or a scoped credential in hand, R24).
- **Kill or reshape:** nothing passes, or the favourite is a bad fit. Stop, or switch openly to the idea the evidence supports (R30). The customer lost a week, not twelve.
- **Who signs:** the **sponsor** signs `scoping.md`. The **Hadavin owner** signs the build order and its price, pinned to the signed `scoping.md` (R35). No build starts without both.

---

## Step 2a — Prototype / PoC (stage 2: build fast)

**Goal:** prove the risky part on the customer's **own data** in days (38 L1).

**Entry gate** (LIFECYCLE Stage 2): `scoping.md` signed; data access proven (not promised); sample documents arrived.

**Steps:**

| # | Step | Hat | Rules / topics |
|---|---|---|---|
| 2a.1 | Thin architecture note: modules, adapters and backends for this client; an ADR per non-obvious choice | [ARCH] | ROLES §2; REAL-WORLD §1, §3 |
| 2a.2 | Pick the risky part (for a handbook assistant: retrieval plus grounded, cited answers) | [FDE] | R47; 38 L1 |
| 2a.2b | Name the risky part for THIS type [Hadavin practice]: SQL correct on the client's real schema (ask-your-data); field accuracy on real invoices (extraction); tool-call correctness on the real API (tool assistant); retrieval plus citation only for document Q&A. The PoC proves that one thing on real data, from a terminal. The four-step order in 2a.3 and the embedder items in 2a.7 apply to document Q&A | [FDE] | 38 L1; R47 |
| 2a.3 | Build the core only (document Q&A order): customer docs → embed and store → retrieve → cited answer; every answer names its source. The PoC must also be able to say "I do not have that in the documents": a similarity floor tuned on the customer's own documents, tested with one out-of-scope question (the live limit demo in 2a.9 needs it) | [FDE] | R49, R55, R151; 38 L1 (image 182748), T1; 39 L1 |
| 2a.4 | Run it from a terminal or plain script; web UI, auth and deployment wait; never cut retrieval or citations; no polish | [FDE] | R50–R53; 38 Q1, Q3 |
| 2a.5 | A small typed package (uv, ruff, pytest on the retrieval/citation core), a read-only connector, regex PII redaction on from day one | [FDE] | R59, R18; 38 real world |
| 2a.6 | If real access is pending, build against a mock with the same response shape | [FDE] | R56; 23 Q1, T1 |
| 2a.7 | Cheapest viable tier on 20 real examples; upgrade only on side-by-side evidence; pin the embedder; same-meaning vs different-meaning check on client samples | [MLE] | R279–R283, R130; 07 L2, 13 T1 |
| 2a.8 | Measure real `usage` early; first monthly estimate | [MLE] | R206–R209; 04 L3 |
| 2a.9 | Prepare the demo with `demo-script.md`: rehearsed questions on the same data the same day, one limit shown on purpose, the mechanism narrated, the boundary stated as a feature. Before real documents are ingested for a demo: the NDA/DPA is signed, and the demo shows only documents every attendee may see (document-level permission, 19); rehearse at the audience's access level. With the Step 0.10 rule in force, a laptop demo uses synthetic data and is labelled so | [FDE] | R236–R241; 39 L1; 19 |
| 2a.10 | Demo by about day four, live, on real data. If it fails live: thank, open the cited source, explain citations, log the question for the eval set | [FDE] | R51, R241; 39 Q1 |
| 2a.11 | Fill the baseline worksheet with the customer after the demo: today's numbers (theirs, never invented), the pilot target, the test-set owner | [FDE] | R242–R245; 39 L2 (image 182825) |
| 2a.12 | Note where retrieval fails on messy documents while scope can still change | [FDE] | R54; 38 L1 |
| 2a.13 | "Ship the PoC Monday?": yes to the goal, no to the timeline; a named hardening plan and a small logged pilot | [FDE] | R58; 38 Q2 |

**Portal at this step:** none for the client. A PoC never gets a client-signed-in portal. If a screen is needed, show the Portal v0 shell on the Hadavin demo deployment with demo data (CLIENT-PORTAL-SPEC §0.4) [Hadavin practice]. If no Hadavin demo deployment exists, show no portal screen.

**EGM here:** the PoC plan and every prompt: `/egm:egm-review-loop`, then `/egm:egm-resolve`. The architecture note: `/egm:egm-review-loop`, then `/egm:egm-resolve`.

**Exit artifacts:** a recorded terminal demo on the client's real data, saved to `projects\<p>\docs\demo\` with its trace ids, `egm\<p>\demo-script.md` filled in (questions, results, the live-failure log, the baseline worksheet), the user's written "useful", ADRs.

**Exit test (02 L2, R57):** real documents from the customer's systems went in, and **one real user** watched it answer and said "useful". A run on your own sample documents never counts (R48).

**Exit / kill decision:** go to build and pilot; or rescope or stop when retrieval fails on their real documents (38 L1). **Never** roll the prototype out to all users (R58). **Who signs:** the real user's "useful" plus the **sponsor's** go. If the order has a mid-point demo payment, it is invoiced on delivery of the demo, not on its results (pricing-plan §3.5) [Hadavin practice].

---

## Step 2b — Build (stage 2, the build-topic map)

**Goal:** grow the PoC into the typed, tested, gated package and the client portal, with the gate in CI from the start (TIMELINES Days 6–15).

**Entry gate:** step 2a exit met; the sponsor's go; Portal v0 passes CLIENT-PORTAL-SPEC §9.

**Steps:**

| # | Step | Hat | Rules / topics |
|---|---|---|---|
| 2b.1 | Architecture note final, ADRs written; code layout config / adapters / core / evals / cli-or-api; one interface per capability, backends from client config | [ARCH] | R18, R61; REAL-WORLD §3 |
| 2b.2 | Build only the capabilities this use case uses (prompts, structured output, tools, state, agents, MCP, connectors, RAG, chunking, hybrid, grounding, ACL); follow each one's topic Checklist and cite it in the PR. Every tool the system can call gets a `tool-safety-review.md` block before it ships; no direct-action tool until an eval justifies the agency (R305, R317) | [FDE]/[MLE] | R60–R157, R317; 05–24 |
| 2b.3 | Day-one guards so the pilot can teach something: regex PII redaction with the outbound test, structured logs and traces, a daily budget cap (38 Q2: no pilot without logs) | [FDE] | R233, R221, R214; 38 Q2; TIMELINES Stage 4 row |
| 2b.4 | Starter golden set and the gate as a required CI check from the first PR | [FDE] | R178–R179; TIMELINES Days 6–15 |
| 2b.5 | Configure the portal for the plan in the client's cloud per CLIENT-PORTAL-SPEC §0.1–§0.4 (T1 ≈ 3 days); a named pack only when the SOW names it (§4.2) | [FDE] + [ARCH] | CLIENT-PORTAL-SPEC §0, §4.2 |
| 2b.6 | With the client's admin, create a disabled, least-privilege emergency role for Hadavin and write its enable-and-expire steps in the runbook; test it once (enable, then expire) | [FDE] | R265; contracts 02 H4.7(d) |
| 2b.7 | Build the identity table (each identity, read rights, write rights, justification, negative test), run every negative test and the access-analysis check (Access Analyzer, policy simulator or equivalent), and test the masks with canaries; no agent holds approver or executor credentials [Hadavin practice, owner 2026-11-01, changing needs owner's yes] | [ARCH] + [FDE] | R365-R367; 36 |

**Portal look** [Hadavin practice, owner rule 2026-10-29]: never on Hadavin.com; our own code and design; never Port's name, logo, text, icons, images, exact colours or pixel-identical screens (spec §1.3).

**EGM here:** the final architecture note is a big plan: `/egm:egm-review`, then `/egm:egm-resolve`. Every PR and every prompt change: `/egm:egm-review-loop`, then `/egm:egm-resolve`. Each new module folder: `/egm:egm-bootstrap`. After each merge batch: `/egm:egm-drift-report`.

**Exit artifacts** (RULES Deliverables §3): the identity table with every negative test passed and the masks tested with canaries (2b.7); chunk set and vector store with metadata; re-runnable ingest that stamps `built_at`; assistant code (grounded prompt, citation validation, bounded tool loop, timeouts, readable errors, not-found handling); prompts as files; model versions pinned; the portal configured for the plan; CI green (ruff, pytest, contract tests, golden gate).

**Exit gate:** CI green on `main`, the drift report clean; Portal v0 passes spec §9. This is a gate, not a person's sign-off. Build is inside stage 2, so the next gate is Prove.

---

## Step 3a — Prove (stage 3, "Build the proof")

**Goal:** a measured number you can rerun tomorrow (R6), and the agreed target met on the frozen test set.

**Entry gate:** step 2b exit met.

**Steps:**

| # | Step | Hat | Rules / topics |
|---|---|---|---|
| 3a.1 | Golden set from real tickets, logs and SME memory, in the users' own wording; easy / hard / trap buckets; traps expect the refusal; exact facts; SME-approved; items for every route (cite, tool, refuse); an unknown id for a lookup tool; bucket coverage for the system type; PII redacted. Set size and the bucket checklist: `eval-contract.md` | [FDE] | R163–R170; 26, 43 T1 |
| 3a.2 | Grading: case-insensitive "contains" for simple facts, a rubric judge with a binary JSON verdict for sentences; judge on a cheap model, never self-grading; audit the judge on known cases incl. one confidently wrong answer | [MLE] | R171–R176; 27 |
| 3a.3 | If an LLM judge grades items: calibrate on ≥100 SME-labelled cases with a held-out part of ≥50 (≥25 pass and ≥25 fail); gate on the true positive and true negative rate lower bounds ≥0.70 (high-stakes tier: 150 labels, 40 per class, bounds 0.80 true negative and 0.75 true positive), report kappa (R325) [Hadavin practice, eval-floors 2026-11-01] | [MLE] | ROLES §5.4 |
| 3a.4 | Runner and gate: capped loop, exceptions scored as failures, scores saved per version; gate exits non-zero below the contract threshold; the threshold never moved to go green. The CI gate runs on the tuning set only; the sealed set is touched only by the acceptance run (3a.11) | [FDE] | R177–R182; 28, 43 |
| 3a.5 | RAG halves: hit rate at k first, then faithfulness against the retrieved chunks; route each fix to the half that failed | [MLE] | R183–R186; 29 |
| 3a.6 | Abstain rate on traps and the false-abstain rate on answerable questions | [MLE] | R190–R191; 32 |
| 3a.7 | Read every failure before reporting; bucket by cause; write `docs\score-report.md` with threshold, previous run and human baseline; fix and disclose eval errors | [FDE] | R187–R191; 29 L3 |
| 3a.8 | Model and route per workload on the golden set: cheapest within about 2 points of the best; decision record per route; fallback model chosen | [MLE] | R277–R283, R290; ROLES §5.1 |
| 3a.9 | Fine-tune only if all three conditions hold, with the eval history as proof | [MLE] | R284–R291; 30; ROLES §5.2 |
| 3a.10 | Price it: real `usage` tokens per question × volume from the brief × the live price sheet, every model named | [MLE] | R208–R210; 44 T1, 04 L3, 33 |
| 3a.11 | Acceptance run: the client's engineer runs the frozen scoring script on the locked outputs for the sealed scoring set in the test environment (outputs locked by checksum before the answers are opened); the report goes with the final invoice [Hadavin practice]. Payment follows the frozen-set count in the contract; a near-miss is never settled by a rerun until green. The zones signed with the target at the end of week 1 of the build (`success-criteria.md`, R361) govern only the "demonstrated" word, and a band result allows one extension on a fresh locked set by change order [Hadavin practice; owner's yes pending] | [FDE] | pricing-plan §3.2, §3.2.5; R180 |
| 3a.12 | Closure Step the working day the counts show the target is met [Hadavin practice; owner's yes pending: money-adjacent. The decision file says the lock day; a run is a winner only once scored, so access stays open until scoring and the final invoice moves later by the days the closure takes]: list every access we held (Access Closure Record Part 1); remove what we control; send the client the written request naming each remaining item and how to remove it; the Hadavin owner signs and files Part 1 with the evidence. From then on we use no access. Go-live is run by the client's engineer from the runbook; later work uses a Grant (2 working days for go-live help, 5 for a fix; expiry set in the client's system) or the client-held dormant emergency role, each logged. The final invoice waits only for the closure condition: client confirmation, 5 working days, or a signed retention instruction | [FDE] | R265, R276; contracts 02 H4.7 |

**EGM here:** the golden set, the judge rubric and the gate threshold: `/egm:egm-review-loop`, then `/egm:egm-resolve`. `cost-estimate.md`: `/egm:egm-review-loop`, then `/egm:egm-resolve`. Before calling Prove done: `/egm:egm-drift-report`.

**Exit artifacts** (RULES Deliverables §4): `evals\golden.jsonl`; `scores.json` (`{total, passed, score}` in 28; `results` + `pass_rate` in 43) or `eval-report.json` (`results` + `pass_rate`, 44) with a failure reason per item; the gate as a required CI check; `docs\score-report.md`; `docs\cost-estimate.md`; `[MLE]` decision records.

**Exit / kill decision** [Hadavin practice, pricing-plan §3.2, §3.5]:
- **Target met:** the final payment falls due (the last gate of the one schedule, Net 14 from the invoice date, which is the day the target counts as met or, if later, the day the closure condition is met; decisions 2026-11-01 evening item 5; contracts 02 H4.5); **go-live of the pilot group comes only after the final payment.** Exception [Hadavin practice, pricing-plan §3.2.5]: for the Incident Response watch-only pilot, read-only use before the final payment is pilot use, not live use; production use never is. The Closure Step (3a.12) runs the same working day the counts show the target is met.
- **Target missed:** one automatic extension; missed after it, the final payment is not due, the build and Hadavin's access are removed (or the client takes it as-is for a reduced payment).
- **Who signs:** the **sponsor** (the target counts as met unless a joint run is booked within 10 working days; that run is final).

---

## Step 3b — Pilot (stage 3: prove it works)

**Goal:** a small group of real users (maybe ten) in daily work; measure how often answers are right, where it fails, whether users come back; a verdict (02 L1).

**Entry gate** (LIFECYCLE Stage 3, plus Hadavin):
- `docs\success-criteria.md` agreed and signed by the sponsor **before day 1** (R250);
- baseline numbers captured before day 1, from the client's own systems (R252; 40 real world);
- no "100%" clause in the contract, and no protection deleted without a replacement (R246, R247);
- the final payment received, so go-live is allowed [Hadavin practice, pricing-plan §3.5];
- staged rollout ready: feature flag or user allowlist, per-user and per-day budgets, traces live (R275); a named client person can switch the pilot off in one step (flag or allowlist), written in the runbook's Escalation table;
- the pass/fail band signed by the sponsor with the target at the end of week 1 in `success-criteria.md`: the stage-1 size (50 answered items), the target, the zones as counts of wrong answers (R361: 0 or 1 green, 2 or 3 band, 4 or more not shown at 50 answered) and the one-extension rule (a fresh locked set of at least 80 answered items, by change order) [Hadavin practice];
- baseline weeks (median), the written "normal" rule, excluded weeks with reasons, the hard-week definition in numbers, the maximum extension, the buyer-chosen fallback ("go live with the limit written", which does not raise the autonomy level, or "quiet weeks only") and the pass bar parts signed in `success-criteria.md` before day 1 (studio addition 2026-11-02, R413 to R415).
- the SOW states the remedies for a quality miss as capped, specific and chosen by Hadavin from a ladder (re-work at no charge for N weeks, a service credit up to X% of the fee, or termination without further fees). The price pays for delivery plus honest measurement; a miss triggers the ladder, not a refund of delivered work. Until a client exists and money exists, contract text says "not reviewed by counsel" and claims nothing legal (decisions 2026-11-01 evening item 9) [Hadavin practice];
- the data flow reviewed again with the client's security engineer before go-live (R12; ROLES §2 Stage 3).

**Steps:**

| # | Step | Hat | Rules / topics |
|---|---|---|---|
| 3b.1 | Set the baseline in image order: current process today → pilot target number → shared test set → fair judgment. Where history exists, score the baseline on the same test set (past human answers marked by the same reviewer), not a spot-check estimate; record both and state which one the target compares against | [FDE] | R242–R245, R252; 39 L2 (image 182825); 40 T1 |
| 3b.2 | 2 or 3 criteria (one quality, one usage or time, maybe one satisfaction), each with metric → target → how measured → time window; final-window measurement that excludes week one. The accuracy criterion is the contract number on the frozen set (R180) and is copied, not re-decided; the usage and time criteria are the user pilot's own. Report the interval beside every score | [FDE] | R250–R255; 40 L1 (image 182857), T1 |
| 3b.3 | One-click capture at the moment of the answer (question, answer, signal, cited sources, model id, trace id). The feedback log is a store of employee questions and answers: redact PII before it is stored (R228 method), restrict access to the reviewer, operator and owner, set the retention period in the SOW and delete at pilot end unless the client keeps it under its own policy [Hadavin practice] | [FDE] | R257, R228; 40 L2 |
| 3b.4 | Weekly loop: capture → review thumbs-down (about 20 minutes) → fix the cluster → tell the users; every fixed thumbs-down becomes an eval candidate | [FDE] | R256, R258, R9; 40 L2 (image 182910) |
| 3b.5 | Count human actions on drafts weekly: sent unchanged, edited, discarded, escalated | [FDE] | R259; 40 L3 (image 182921) |
| 3b.6 | Escalation rule: a safety thumbs-down, or 3 on the same question, goes straight to a daily-checked place with a named human (the full rule, not the task's simplified one) | [FDE] | R260; 40 L3, real world |
| 3b.7 | Tell the customer the refusal trade-off; review every refusal weekly, tagged "doc missing" or "retrieval miss" | [FDE] | R201, R205, R264; 32 |
| 3b.8 | Model-layer fixes only after solution-layer fixes, with failing examples; router, fallback and judge per route | [MLE] | R10; 01 Q2; ROLES §2 Stage 3 |
| 3b.9 | Status meetings on the score trend and the failing questions, never a demo | [FDE] | R162; 25 L2 |
| 3b.10 | Start the responsibility shift: "you do, they watch" for each duty (41 L2 starts about 4 weeks before the end) | [FDE] | R268; 41 L2 |
| 3b.11 | Review meeting on the agreed window: verdict against the agreed numbers; a miss is a miss; do not read high usage with a high thumbs-down rate as success (mandated usage is compliance, not adoption: find which metric tells the truth) | [FDE] | R261–R263; 40 Q1, Q2 |

**Portal at this step** [Hadavin practice]: the pilot group uses the client's portal. Home tiles show the pack's value KPI next to its control KPI (spec §4.3). For a support-assistant pack, Drafts review counts R259 actions, Refusals carries the R264 tags, and Escalations implements R260.

**EGM here:** `success-criteria.md` before day 1: `/egm:egm-review-loop`, then `/egm:egm-resolve`. Each weekly fix PR: `/egm:egm-review-loop`, then `/egm:egm-resolve`. `pilot-report.md` before the review meeting: `/egm:egm-review-loop`, then `/egm:egm-resolve`. At exit: `/egm:egm-drift-report`.

**Exit artifacts:** `docs\pilot-report.md` (the numbers report: users, real questions, percent correct, worst failures listed honestly, compared with the discovery number, and the verdict); the feedback log and escalation record (course: `feedback.jsonl`, `escalations.txt`, 40 T2); weekly human-action counts; golden-set additions.

**Exit / kill decision** (LIFECYCLE Stage 3):
- **Go to hardening:** the agreed numbers met in the agreed window.
- **Stop before hardening:** the numbers are bad (02 L1). The final payment is already due at 3a, so the sponsor's options after the user pilot are continue, close or restart (R262), not a refund; the SOW says so.
- **Restart after fixing the root cause** (40 Q2).
- **Never** lower the bar, extend without a fix, or reframe a miss (R262).
- **Who signs:** the FDE gives the honest verdict; the **sponsor** decides continue, close or restart.

---

## Step 4a — Harden (stage 4: make it survive)

**Entry gate:** the pilot verdict is "go"; the exit criteria from week one are in hand (LIFECYCLE Stage 4). If pushed to roll out wide now: stage the rollout while hardening happens (R234; 02 Q1).

**Steps** (Harden = 31–36; many pieces were built in 2b.3 and proved in the pilot; here every box gets its evidence):

| # | Step | Hat | Rules / topics |
|---|---|---|---|
| 4a.1 | Guardrails: input filter on a cheap model, output filter on the customer's rules, boundary markers on retrieved text and tool results, minimal tool permissions, fail closed | [FDE] + [ARCH] | R192–R199; 31 |
| 4a.2 | Hallucination controls: an exit to refuse, confidence routing, fake-entity probes | [FDE] | R200–R205; 32, 03 T2 |
| 4a.3 | Cost: exact-match cache, then classify-first router (R213), plus a hard daily budget in code from the first live call that fails loudly; atomic shared counter | [MLE] + [FDE] | R211–R216; 33 |
| 4a.4 | Latency: stream for chat, never batch; timeouts sized from p95; a fallback model (transport errors only, R219), logged and alarmed | [FDE] | R217–R220; 34 |
| 4a.5 | Observability: one metadata line per call, a trace per request, zero-doc retrieval alarm, cost summed from the log | [FDE] | R221–R226; 35 |
| 4a.6 | Security: data flow, redaction before every external call with the seeded-PII CI test, content logs only with security's approval, corpus scanned for credentials | [ARCH] + [FDE] | R227–R233; 36 |
| 4a.7 | Deployment hardening: private endpoint, IAM, secrets store, log retention | [ARCH] | R15, R44; ROLES §2 Stage 4 |
| 4a.8 | Replace the snapshot export with sync; permission-filter any non-all-staff source; pin model ids; prompt and model changes only through the eval gate | [FDE] | R124–R125, R153–R157, R77, R177; 24 L2, 19, 09, 28 |
| 4a.9 | Model lifecycle: every pinned model's platform EOL date in the runbook, alarm 60 days before | [MLE] | ROLES §5.6 |
| 4a.10 | Portal pack tests: empty/loading/error states, light and dark, Playwright + axe-core, SQL-view contract tests, cross-user and cross-project leak tests, golden gate | [FDE] | CLIENT-PORTAL-SPEC §4.5 |
| 4a.11 | [at hardening] Supplement exit evidence: audit chain anchored outside the app's write access, seven design-review questions in the runbook, scale review, sandbox for any code-running agent, trifecta re-check, deletable prompt rules with evals (changed 2026-11-01) | [ARCH] + [FDE] | R306, R316, R330–R332, R334 |

**EGM here:** the hardening plan is a big plan: `/egm:egm-review`, then `/egm:egm-resolve`. Each PR: `/egm:egm-review-loop`, then `/egm:egm-resolve`. After each merge batch: `/egm:egm-drift-report`.

**Exit artifacts** (RULES Deliverables §5): every Harden box ticked in `egm\<p>\STAGE-CHECKLIST.md` with the file, test or alarm that proves it. **Exit gate:** CI green, drift report clean.

---

## Step 4b — Handoff (stage 4: the system runs without us)

**Entry gate:** step 4a exit met; the responsibility shift under way since the pilot.

**Steps:**

| # | Step | Hat | Rules / topics |
|---|---|---|---|
| 4b.1 | Shift one duty at a time: you do, they watch → they do, you watch → they do alone, you review (the last two weeks in the course) | [FDE] | R268; 41 L2 (image 183007) |
| 4b.2 | Train three roles, each with its own session and runbook section: operator, reviewer, owner; never a slide deck. Each role has a named deputy who completes the same do/watch cycle [Hadavin practice] | [FDE] | R269; 41 L2, Q1 |
| 4b.3 | Write `runbook.md` (both heading sets): restart, re-index, key rotation via the client's secret store, the top five failure modes with fixes, fenced commands that are real package entry points; never swap the model without evals | [FDE] | R266, R267, R274; 41 T1, 44 T1; REAL-WORLD §3.11 |
| 4b.4 | Write `README.md` | [FDE] | LIFECYCLE Stage 4 |
| 4b.5 | Wire monitoring to their people: scheduled evals, weekly thumbs-down review on the reviewer's calendar, accuracy and cost drift alerts to the named owner | [FDE] + [MLE] | R270; 41 L1, Q2 |
| 4b.6 | Record the owner and the three roles in the agent registry; model pins and lifecycle dates handed over | [ARCH] + [MLE] | R276; ROLES §4 |
| 4b.7 | Name the owner: a person, not a team, agreed in writing by their manager. Name a deputy for the operator and the owner; the runbook lists both. If no deputy exists, record it as an open exit criterion for the sponsor (R272) [Hadavin practice] | [FDE] | R265, R273; 41 L1, Q1 |
| 4b.8 | Raise any unmet exit criterion with the sponsor, with options, before the last week: part-time owner, paid retainer (a Hadavin care plan, pricing-plan §3.4), or scale down; never quiet free support | [FDE] | R272, R273; 41 Q1 |
| 4b.9 | Exit-test week: the customer's engineer runs a full week, including one failure, without messaging us. If no real failure occurs that week, the sponsor and the owner's manager agree a drill in advance (for example a stale index or an expired test key in the test environment); the operator fixes it using only the runbook; log it [Hadavin practice] | — | R271; 02 L2 |
| 4b.10 | Record a demo or walkthrough against the success criteria, saved to `docs\demo\` with its trace ids [Hadavin practice] | [FDE] | 44 table #9 |
| 4b.11 | Self-contained delivery: a frozen vendored copy plus a hash file, hash-locked dependencies with an SBOM, nothing fetched from the owner's GitHub or org [Hadavin practice] | [ARCH] | REAL-WORLD §3.10 |
| 4b.12 | **Fifth exit criterion, Hadavin's own** (owner decision 2026-11-01 evening item 6) [Hadavin practice]: sign Part 2 of the Access Closure Record at hand-over: the Grant Log with every Grant closed and confirmed, the status of each item left open at 3a.12, a second written notice for anything still open; attach it to the runbook. The obligation is ours, not the client's | [ARCH] | H-04; R265, R276; `memory\laptop-compromise-lesson.md` |

**Portal at this step** [Hadavin practice]: the portal is deployed in the client's cloud as part of the project; the owner role is trained on Home and the cost tiles; the operator on Runs & audit.

**EGM here:** `runbook.md` and `README.md`: `/egm:egm-review-loop`, then `/egm:egm-resolve`. The final `/egm:egm-drift-report` before "done".

**Exit artifacts** (RULES Deliverables §8): `docs\runbook.md`, `README.md`, the named owner in writing (and the deputies), the trained three-role team, monitoring wired, the registry entry, the recorded walkthrough, the Access Closure Record, Parts 1 and 2, with its evidence (3a.12, 4b.12), `handoff\projects\<p>.md` updated with the final state.

**Exit test (02 L2):** "handoff is done when you are not needed": the customer's engineer handled a full week including one failure without messaging us; documentation exists; limits are set; someone owns it by name.

**Exit / kill decision:** an unmet criterion is the sponsor's decision (R272). **Who signs:** the **sponsor**; the owner's **manager** agrees the named owner (41 L1); the **Hadavin owner** signs both parts of the Access Closure Record. Timing: Part 1 is filed at the Closure Step (3a.12) and is the only access condition on the final invoice; Part 2 is signed here, at hand-over, and gates no payment.

---

## Calendar (TIMELINES)

| Day / week | Steps | What cannot be compressed (client-owned; log every client delay the same day) |
|---|---|---|
| Day 0 | 0 Setup | data and system access |
| Days 1–5 | 1 Discovery ("Blueprint") | stakeholder interview slots; the client's security review |
| Days 6–15 | 2a PoC (demo by about day 4 of the stage), 2b Build, 3a Prove at the end | the client's review and approval time |
| Weeks 4–6 or more | 3b User pilot: at least 3 weeks (week 1 teething, then a final window of at least 2 weeks that excludes week 1, R253); 4 if the KPI follows a weekly or monthly cycle | the pilot measurement window |
| After the pilot's go (day-one guards built in 2b; training started in 3b), at least 1 week | 4a Harden, 4b Handoff and the exit-test week | — |

Typical build: 6–8 weeks (3 weeks to the acceptance run, at least 3 weeks of user pilot, at least 1 week to harden and hand off). Course calendar for comparison: 12 weeks, whose pilot is 4 weeks (LIFECYCLE, "Course calendar").

---

## Done means

Every stage's exit box in `egm\<p>\STAGE-CHECKLIST.md` is ticked with evidence; topic Checklists are working aids, not gates. The project or demo is done when the "Done means" boxes in `STAGE-CHECKLIST.md` are ticked with evidence and the heading check and the deferral grep below are clean.

**Heading check** (exact course H2s; PowerShell):
```powershell
$d = "<studio>/projects\<project>\docs"
'## Use case','## Out of scope','## Success metric','## Risks','## Problem','## Users','## Success criteria' | % { if (-not (Select-String -Path "$d\scoping.md" -Pattern ('^' + [regex]::Escape($_) + '\s*$') -Quiet)) { "scoping.md missing: $_" } }
'## Metrics','## Baseline','## Measurement','## Review date' | % { if (-not (Select-String -Path "$d\success-criteria.md" -Pattern ('^' + [regex]::Escape($_) + '\s*$') -Quiet)) { "success-criteria.md missing: $_" } }
'## Owner','## Routine operations','## Known failure modes','## Escalation','## How to run','## Monitoring','## Known limitations' | % { if (-not (Select-String -Path "$d\runbook.md" -Pattern ('^' + [regex]::Escape($_) + '\s*$') -Quiet)) { "runbook.md missing: $_" } }
```
No output means every heading is present, each on its own line.

**Deferral grep** (run from `<studio>/`):
```bash
rg -n -i "todo|tbd|fixme|deferred|not verified|unverified|placeholder|<!--|<[a-z][a-z -]*>" "projects/<project>" "handoff/projects/<project>.md"
```
Leftover template text (`<!--` guide comments, `<placeholders>`) is filled or deleted. Every other hit is fixed, or written in the handoff as an (a)/(b)/(c) exception with its next step. The headings `## Out of scope` (scoping) and `## Known limitations` (runbook and README) are allowed; Known limitations lists only inherent boundaries of the system, never an unfixed bug or gap. Subagent reports count as unverified until checked.

---

## Review log

| Date | Review | Resolution |
|---|---|---|
| 2026-10-30 | EGM zoom-out (Z1–Z8), implementation readiness (R1–R11) and codebase details (F1–F7 and nits) on this file and `templates\project\` | `egm\project-playbook\resolution-2026-10-30.md`: all findings applied |
| 2026-11-01 | Bible audit I, L, H, J, M applied to this file and `templates\project\` | `egm\bible-audit-2026-11-01\applied-lifecycle-playbook-templates.md` |

## Studio addition 2026-11-02: extra checks per stage (TRIAL, advisory; tick only if used; unverified source, adopt after own test)

- [ ] (trial) Scoping: recipient test, delegation test, client owns data and definition of done, front-desk person named (R419, R426, R431, R437).
- [ ] (trial) Build: graduation bar and production owner (written at scoping, checked here), reward source in the eval contract, builder and reviewer separate, reclassification triggers (written at scoping, re-run at hardening) (R421, R432, R428, R423).
- [ ] (trial) Pilot: front-desk step checked, time-to-trusted-answer logged, failure layer named per failure (R437, R443, R427).
- [ ] (trial) Handoff: owner, watcher, rollback for each output; locked core proved after the N tasks written at scoping; definitions, permissions and audit carried; durable work record (R418, R425, R422, R444).

Source: Idea from public LinkedIn posts by Moonveil AI quoting others; unverified; we adopt only after our own test.
