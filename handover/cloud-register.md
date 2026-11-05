# Cloud agent register (live). One row per agent, written BEFORE it starts.
Times UTC. Model column = the model set explicitly on the Agent call (MODEL-ROUTING.md rule 2/6).

| agent | purpose | model | started | expected end | last checked | state | next action |
|---|---|---|---|---|---|---|---|
| drafter-P1 | draft P1 ticket | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | 2026-11-05 14:36Z | reported; RESUMED for revision (amendments A2, A8, A9) | expected end 15:06Z; then verify + egm-review-loop |
| drafter-P3a | draft P3a ticket | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | 2026-11-05 14:36Z | reported; RESUMED for revision (A3, A8, A9, F6, F10) | expected end 15:06Z; then verify + egm-review-loop |
| drafter-P2a | draft handover/tickets/P2a.md (stop state, 3 PRs) | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | - | running | same |
| drafter-P4d | draft P4d ticket | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | 2026-11-05 14:36Z | reported; RESUMED for revision (F7, F2, D1, A8) | expected end 15:06Z; then verify + egm-review-loop |
