# REPORT from core-c (newest on top, UTC and IST)

## SESSION MODEL PROOF, 2026-11-20T07:22Z (owner order: nothing may use the retired tier, including this session)
Source: `get_session` (claude-code-remote MCP), session_014pRo384P1BXVp7wjAEE89z, read twice at 07:20 and 07:22 UTC:
- `configured_model`: claude-sonnet-5-5
- `session_context.model`: claude-sonnet-5-5
- `external_metadata.model`: claude-sonnet-5-5
- `external_metadata.last_served_model`: claude-sonnet-5-5
- `external_metadata.user_switched_model`: claude-sonnet-5-5 (switched with `/model` by the user at about 06:36 UTC)
The older statement in this file (the ORDER 001 block, 04:12 UTC: session model claude-fable-5-2) is history: it described the session before the switch.
Agents: every Agent call since the restart sets the model explicitly (opus for the drafters, sonnet for reviewers, builders and test writers, haiku not needed yet). The EGM plugin model lines were proven reverted above (6 opus, 66 sonnet, 0 retired-tier). The board was cleaned of every mention of the retired tier.

## EGM SETUP REVERTED AND PROVEN, 2026-11-20T06:38Z (owner order after the Fable limit; this container was restarted at about 06:37 UTC: BOOT_ID 1e29cf8a)
Command: `grep -rh '^model:' ~/.claude/plugins/*/egm* | sort | uniq -c`
Output:
```
      6 model: claude-opus-5-5
     66 model: claude-sonnet-5-5
```
What was done: `sed -i 's/^model: claude-fable-5-2/.../'` on the 72 files that carried that line (cache copy and marketplace copy, skills, agents, `.claude-plugin/agents`, `.cursor-plugin/agents`): `claude-opus-5-5` ONLY in the skills egm-brainstorm, egm-draft, egm-resolve (6 files: both copies); `claude-sonnet-5-5` in the other 66. The issue template `.github/ISSUE_TEMPLATE/feature_proposal.md` carries no `model:` line (checked: no match), so nothing to change there. `grep -rli fable` over both egm plugin trees: 0 files. No patch script was used. Zero fable lines.
Agents: every Agent call from now sets the model explicitly: sonnet for EGM reviewers, builders and agents, haiku for lookups; opus only for egm-brainstorm / draft / resolve; never fable.
The restart agents I started on sonnet at 06:40 were stopped by the container restart: see RESUME-NOTE-2026-11-20.md (addendum).

## Build status after ORDERS 002 to 011. 2026-11-20T05:53Z (IST = UTC + 5:30)

### What failed or is open (first)
- Combined tree on cloud/core-c (53ee2b2): 2 tests red. tests/test_k5_producers.py (the new gate module is not in SPINE's guard/producers.py; requests/1-producers.patch) and test_m16 in tests/test_textnorm_round1.py (two heads disagree; ORDER 010 decided, fix running).
- P1d-a (G2): 2 property tests fail, inherited from the input head (the lead's baseline shows the same two, ORDER 009). Fix try 1 running; cap 2 more tries, else P1d-a is left out as ORDER 009 allows.
- Redactor gap confirmed by a run (E3): one redaction pass leaves a bank account number readable beside a bank code. Pinned as a strict expected failure; not fixed (waiting for the lead: build as part G7 or accept).
- Lead code review round 1 of the gate (ORDER 011: 1 Blocker, 4 Majors, 9 Minors): the Blocker (old design) is already replaced by commit 45156c1; the Majors and Minors are being applied now. Round 1 of at most 3.
- One-minute board cron: refused by the session's permission layer (E1). Boards go out per tool batch.
- NOT RUN anywhere in this session: the full test suite, Python 3.12, PostgreSQL 17, the textnorm and P1d-a mutant runners.

### Code branches and tips (ORDER 010 item 4)
| branch | tip | what |
|---|---|---|
| cloud/core-c | 53ee2b2 | "code B:" grants negative tests; "code G: G0" is_masked + enforce_map; "code F:" gate wrapper; "code G: G1 step 1 to 4" the fold. Code commits touch only src/, tests/, tools/ and the fold's own docs/config files |
| wip/cloud-core-c/g1-fold | 8e4d234 | the fold alone on main 51c9fc4 (same 5 commits) |
| wip/cloud-core-c/g2-p1d-a | 4bd78f6 | P1d-a picked onto main + 27 path tests; 2 inherited failures, fix in progress (not pushed yet) |
| (local only) wip-g3-p2d | in progress | P2d-1 fold-scan port on top of the fold |

### FILE-INDEX (handover/core-c/)
CAPABILITY.md, LANE-MAP.md, PLAN-READBACK.md, DECISIONS.md, ESCALATIONS.md (E1 to E4), QUESTIONS.md, STATUS-BOARD.md;
tickets/: F-gate-wrapper-body.md (with Amendment 1 and As Built), F-review-1.md, G-text-deltas.md, G-review-1.md, G-survey-P1a-P1b.md, G-survey-P2d-P1d-P1c.md, G4-P1c-redactor-gaps.md, B-mutant-cases.md;
evidence/: F-G0-1.md, G1-fold.md, G2-p1d-a.md, P1c-probe.md, p1c_probe.py; requests/: 1-producers.patch.
R-numbers used (from the handover files only; the bible is not in this box): R454 needed-check, R447/R448 rung table, R456 work conduct, R461 capacity, R462 best-first.

## ORDER 001 proof: EGM VISIBLE. 2026-11-20T04:12:22Z (2026-11-20T09:42:22+05:30 IST)

### Status block
- State: ORDER 001 done, waiting for GO. No work started.
- Agents running: 0 language-model agents, 0 script lanes. (2 reviewer agents ran for the dry run and are finished.)
- Capacity: 4 cores idle, memory 0 of 15 GB used, disk 60 GB free. Boot id 292eaa9f.
- Failed: none. Interrupted: none.
- Not checked: see the end of this block.

### 1. EGM skills in my Skill tool (exact names, 8)
egm:egm-bootstrap, egm:egm-brainstorm, egm:egm-draft, egm:egm-drift-report, egm:egm-lite, egm:egm-resolve, egm:egm-review, egm:egm-review-loop.

### 2. EGM agents in my Agent tool (exact names, 10)
egm:egm-bootstrap-orchestrator, egm:egm-codebase-details, egm:egm-comprehension, egm:egm-design, egm:egm-implementation-readiness, egm:egm-inventive-catalyst, egm:egm-structural, egm:egm-style, egm:egm-synthesizer, egm:egm-zoom-out.

### 3. Model lines
Command: grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c
Output (complete):
     72 model: claude-fable-5-2
No opus line, no sonnet line. The 72 lines are one per file: 8 skills and 10 agents in plugins/cache/egm/egm/0.1.1 and again in plugins/marketplaces/egm, including the copies under .claude-plugin/agents and .cursor-plugin/agents.
Plugin record: egm@egm version 0.1.1, git commit 70406c4d22cc7ea8299637c2c5b44625c48b3f08, installed 2026-11-20T04:10:54Z.

### 4. Session model
get_session says: configured_model claude-sonnet-5-5, session_context.model claude-fable-5-2, last_served_model claude-fable-5-2, user_switched_model claude-fable-5-2.
Plain words: the session was created as Sonnet 5.5 and switched to Fable 5.2; the turns are served by Fable 5.2. I changed no setting.

### 5. Dry run
egm:egm-review-loop ran through the Skill tool on a 3-line test paragraph. 2 reviewers (egm:egm-style, egm:egm-comprehension), both called with model 'fable', both completed. Result: 1 Blocker, 6 Major, 1 Nit. One round only, no fix applied (proof only). Full result: handover/core-c/egm-dryrun.md. Input: handover/core-c/egm-dryrun-input.md.

### What I did not check, and oddities
- Only 2 of the 10 EGM agents were actually started. The other 8 are listed in my Agent tool but not run.
- The synthesizer path, document standards, fix application and a second review round were not run.
- The plugin's own note (docs/claude.md) says the Skill tool refuses EGM skills. Here it did not refuse: the skill launched. The setup script seems to have enabled this; I did not look into how.
- The model lines prove what the files say. I have no direct proof of which model served the 2 reviewer agents beyond setting model 'fable' on each call.
- Bible and studio folder (C:\Users\rakes\Downloads\Hadavin) are on the laptop, not in this container, so I could not grep RULES.md. R-numbers cited from the handover files only: R456 (work conduct), R461 (capacity line), R278-R281 and R290 (model choice, all-Fable order).
- EGM skipped for this report itself: status check, proof only.
- CODE-LAST n/a: no component created.

### Files changed (all in handover/core-c/)
REPORT.md, egm-dryrun.md, egm-dryrun-input.md
