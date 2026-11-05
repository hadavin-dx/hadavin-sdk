# Cloud agent register (live). One row per agent, written BEFORE it starts.
Times UTC. Model column = the model set explicitly on the Agent call (MODEL-ROUTING.md rule 2/6).

| agent | purpose | model | started | expected end | last checked | state | next action |
|---|---|---|---|---|---|---|---|
| drafter-P1 | draft handover/tickets/P1.md (text folding) from TICKET-TEMPLATE; read-only on code, no build | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | - | running | read report, verify claims, then egm-review-loop |
| drafter-P3a | draft handover/tickets/P3a.md (migration rule) | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | - | running | same |
| drafter-P2a | draft handover/tickets/P2a.md (stop state, 3 PRs) | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | - | running | same |
| drafter-P4d | draft handover/tickets/P4d.md (store contract suite) | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | - | running | same |
