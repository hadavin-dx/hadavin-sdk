# EGM dry run: egm:egm-review-loop, round 1 (ORDER 001 proof)

- When: 2026-11-20 04:11 UTC / 2026-11-20 09:41 IST
- Skill: egm:egm-review-loop, started through the Skill tool ("Launching skill: egm:egm-review-loop").
- Target: handover/core-b/egm-dryrun-input.md, full file, lines 1-3 (a made-up 3-line test paragraph).
- Dispatch: direct (two reviewers started by the main session in parallel, no synthesizer). Agent model set to 'fable' on both calls.
- Reviewers: egm:egm-comprehension = completed; egm:egm-style = completed. Not run: none.
- Standards: none (each reviewer used its own persona file). Reading list: empty.
- Result: round 1 is NOT clean (Major findings open). No fix applied: this is a proof run, and the skill stops at the human checkpoint after each round.

## Target text
1. The needs-a-person queue holds every task that the system must not finish on its own.
2. A task leaves the queue only when a named person approves or rejects it, and the system records who decided and when.
3. If nobody decides within the configured time, the task stays in the queue and the system raises an alert.

## Findings (deduplicated)
| id | reviewer | severity | line | finding |
|---|---|---|---|---|
| comprehension-1-1 | comprehension | Major | 1-3 | Not stated whether this is current behaviour, a requirement or a proposal. (style-1-6 raises the same as a Nit.) |
| comprehension-1-2 | comprehension | Major | 1 | "the system" and "task" are not defined. |
| comprehension-1-3 | comprehension | Major | 1 | No rule for what makes a task one the system "must not finish on its own", or who decides that. (style-1-3: Nit.) |
| comprehension-1-4 / style-1-1 | both | Major | 2 | "a named person" has two readings: a person assigned in advance, or anyone whose identity is recorded. |
| comprehension-1-5 | comprehension | Major | 2 | What happens after approve and after reject is not described. |
| comprehension-1-6 / style-1-2 | both | Major | 3 | "the configured time": no setting name, unit, default, owner, or clock start. |
| comprehension-1-7 / style-1-2 | both | Major | 3 | "raises an alert": no recipient, channel, or repeat rule. |
| comprehension-1-n1 / style-1-4 | both | Nit | 1 | "needs-a-person queue" used as a term without marking it as a formal name. |
| comprehension-1-n2 / style-1-5 | both | Nit | 2 | Where the record is kept is not stated; the decision itself (approve or reject) is not listed as recorded. |
| comprehension-1-n3 | comprehension | Nit | 2 | "only when" does not say whether withdrawal or admin deletion can also remove a task. |

Blockers: 0. Majors: 7. Nits: 3. Style also checked for hype, filler and repetition: none found.

## Not done
- egm:egm-resolve was not run and no text was changed (proof only; waiting for GO).
- Only one round and only two of the reviewers were used; this proves the mechanism, not the paragraph.
