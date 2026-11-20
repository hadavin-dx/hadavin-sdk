# EGM dry run: egm:egm-review-loop on a 3-line test paragraph (ORDER 001, core-c)

Run at 2026-11-20T04:12:22Z (2026-11-20T09:42:22+05:30 IST). Proof only: no fix was applied to the test paragraph.

## Setup
- Skill: egm:egm-review-loop, started through the Skill tool (it launched; plugin egm 0.1.1).
- Target: handover/core-c/egm-dryrun-input.md, full file, lines 1-3.
- Dispatch: direct (flat), 2 reviewers in parallel, each in a fresh context, Agent model set to 'fable' on both calls.
- Standards: none (a 3-line paragraph is not a design document). GoldfishContext: empty.
- Rounds: 1 of at most 5. Halted on purpose after round 1 (dry run). NOT converged: round 1 is not clean (2 blockers).

## Target text
1. The deploy kit copies one recipe folder into a client project and runs its checks.
2. It is fast and always works, so no rollback step is needed.
3. The harness then replays the recorded inputs and compares the outputs to the saved ones.

## Reviewer status
| reviewer (agent type) | model set | status | agent id | tokens | seconds |
|---|---|---|---|---|---|
| egm:egm-style | fable | completed | a39c0f8be8e5454eb | 10131 | 12 |
| egm:egm-comprehension | fable | completed | a997db3cfc0f94dec | 11169 | 24 |

Both reviewers stated they read their persona file and the target in full and changed no file.

## Findings (round 1, 11 raw, 8 after merging duplicates)
| id | severity | line | finding | also raised by |
|---|---|---|---|---|
| style-1-1 | Blocker | 2 | "always works, so no rollback step is needed": absolute claim with no evidence is the only reason given for leaving out rollback; lines 1 and 3 run checks, which only exist because something can fail | comprehension-1-1 (Blocker) |
| style-1-2 | Major | 2 | "fast" has no number, unit or baseline | comprehension-1-7 (Nit) |
| comprehension-1-2 | Major | 2 | "It" has no clear subject (kit, copy step, or checks) | style-1-3 (Nit) |
| comprehension-1-3 | Major | 1 | "deploy kit", "recipe folder", "client project" are not defined or linked | |
| comprehension-1-4 | Major | 1 | "runs its checks": whose checks, what they verify, what happens on failure | |
| comprehension-1-5 | Major | 3 | "the harness" is not introduced; its relation to the deploy kit and what triggers it are not stated | |
| comprehension-1-6 | Major | 3 | "recorded inputs" and "saved ones": who recorded them, where they are stored, match rule, what happens on mismatch | |
| comprehension-1-8 | Nit | 1-3 | does not say if this is current behaviour or a proposal | |

Totals after merge: 1 Blocker, 6 Major, 1 Nit. Where two reviewers gave different severities the higher one is kept.

## Resolution (Elephant view, egm-resolve step)
All 8 are PROPOSE FIX, none CONTEST: line 2 was written as a planted weak claim and both reviewers caught it independently.
No fix applied and no second round run, because ORDER 001 is proof only. The egm-resolve decision gate (auto accept / continue / interactive) was not shown: there is no human at this session to answer it.

## What this proves and what it does not
- Proven: the skill starts through the Skill tool, the egm:* reviewer agents start with model 'fable', read their persona files from the plugin cache, and return graded findings with line numbers.
- Not checked: the synthesizer path (egm:egm-synthesizer), the other 6 reviewer agents, document standards, fix application, a second round, convergence.
