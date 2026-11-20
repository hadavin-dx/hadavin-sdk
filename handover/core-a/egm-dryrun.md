# EGM dry run: egm:egm-review-loop on a 3-line test paragraph (ORDER 001, proof only)

Run: 2026-11-20 04:09 to 04:10 UTC (09:39 to 09:40 IST). EGM plugin 0.1.1 (commit 70406c4).
Started through the Skill tool (`egm:egm-review-loop`). Reviewers dispatched directly from the main session, in parallel, each Agent call with model `fable`.

## Configuration
- Target: `handover/core-a/egm-dryrun-target.md`, full file, lines 1-3
- Reviewers: `egm:egm-style`, `egm:egm-comprehension` (2 of the 10 EGM agents; enough to prove the loop runs)
- Standards: none. Reading list for reviewers: empty.
- Rounds run: 1. Fixes applied: none (proof only, the target is a throwaway).

## Target text
1. The ledger records every money movement as one line that is never changed after it is written.
2. A door is the single entry point where a request from a channel is checked before it reaches a module.
3. If a check fails, the door rejects the request and writes the reason to the audit log.

## Reviewer status
| reviewer | model | status | tokens | seconds |
|---|---|---|---|---|
| egm:egm-style | fable | completed | 10,032 | 10 |
| egm:egm-comprehension | fable | completed | 10,279 | 14 |

## Findings, round 1 (0 Blocker, 2 Major, 6 Nit)
| id | severity | line | finding |
|---|---|---|---|
| comprehension-1-1 | Major | 2 | "channel" and "module" are used to define "door" but are not defined; a new reader cannot tell what a door sits between. |
| comprehension-1-2 | Major | 2-3 | The checks are never named; "the single entry point" could mean one door for the system or one per module; only the failure path is described. |
| comprehension-1-3 | Nit | 3 | "the audit log" appears as if already known; its relation to the ledger is not stated. |
| comprehension-1-4 | Nit | 1 vs 2-3 | The ledger sentence does not connect to the door sentences. |
| comprehension-1-5 | Nit | 1 | "line" is unusual for a ledger record; "never changed" does not say how mistakes are corrected. |
| style-1-1 | Nit | 1 | "every" and "never" are absolutes with no evidence in scope; fine as a design rule, needs proof if it claims tested behaviour. |
| style-1-2 | Nit | 2 | Same subject as comprehension-1-1 (undefined "channel", "module"), rated Nit by this reviewer. |
| style-1-3 | Nit | 2 | Same subject as comprehension-1-2 ("is checked" names no criterion), rated Nit by this reviewer. |

## Loop result
- Round 1 is NOT clean (2 Major open). The loop was stopped here on purpose: the order asks for proof that EGM runs, not for a converged paragraph.
- Not done: resolve step (egm:egm-resolve), fixes, round 2, convergence (two clean rounds). Not tested: the synthesizer route (egm:egm-synthesizer) and the other 8 agents.

## Deviations from the skill text (stated, not hidden)
- The skill asks the user to confirm the configuration and to answer a decision gate after each round. Nobody was there to answer, so the configuration above was chosen by this session and the run ended after round 1.
- The plugin's own `docs/claude.md` says the Skill tool refuses EGM skills. In this session the Skill tool accepted `egm:egm-review-loop` and loaded it.
