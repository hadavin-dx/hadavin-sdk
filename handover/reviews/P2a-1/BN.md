# BN: errors and conflicts found in ticket P2a-1 (builder notes)

1. B0 start gate (P3a, P4d must be merged) was not met when I started. Only P3a-1 (pure functions) and P4d-a1 (harness) existed. I did not merge them then. Later the lead asked me to merge origin/core/P4d-a2; done (merge commit f0465df).
2. B1 (a PostgreSQL 16 job in CI) needs a change to .github/workflows/ci.yml. The brief forbids touching ci.yml. NOT done. Needs the lead.
3. Migration number: the ticket says the stop-state migration is 0006. P4d-a2 took 0006 (spend_reservations), so mine is 0007_kill_switch_guard. Any text that still says 0006 (ticket, runbook, contract notes) must say 0007.
4. Stage names: the ticket and the preamble (rule 21) say demo/pilot/prod, but the base config still accepts "dev". `Limits` treats {"dev","demo"} as the demo stage. The "dev" refusal belongs to P0t and is not done here.
5. P4d-a2's `reserve_spend` read the kill switch flag directly (memory `_kill.on`; PostgreSQL `SELECT "on" FROM kill_switch`). With stop requests as rows, that read misses an open request and, for the runtime role, is denied by the grant map. Fixed in this branch (both stores read the state view). P4d-a2 should be told: any new reader of the switch must use `kill_switch_state` / `get_kill_switch()`.
6. `hypothesis` is not a test dependency; the label fuzz tests use exhaustive enumeration over a small alphabet instead of adding a dependency.
