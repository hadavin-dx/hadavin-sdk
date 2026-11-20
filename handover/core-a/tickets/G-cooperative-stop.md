# TICKET (write-only, not built): cooperative stop at SIGTERM in the agent loop
Written 13:50 UTC by core-a on the lead's order (13:46): ticket only. agent_loop.py is core-b's B2 file; nothing is built here.
## Problem
The signed-trigger worker drains on SIGTERM: `serve()` stops accepting, then `Runner.close(30 s)` WAITS for the running loops (worker.py serve/close). A run still working after 30 s is cut by the process exit: the row stays WORKING (or the state it had), the tick later marks it NEEDS_PERSON with no notification and no stored document (E-door-1). The loop itself has no way to learn that the process is stopping, so it cannot finish the current step and park the run in a clean, resumable state.
## Proposal (for core-b's B2 builder to decide)
1. A stop flag the loop can read between steps (a `threading.Event` or a callable `should_stop()` passed in by the caller, default never): checked at the top of each step, before a model call and before a tool call, never in the middle of one.
2. On stop: finish the step in flight, write the state the loop already knows how to write for 'cannot continue' (the existing abstain/needs-person path with a distinct reason code, for example `stopped_by_shutdown`), audit it, return.
3. The worker passes `Runner.stopping` as that flag; `Runner.close` sets it first, then waits (so the wait normally ends in seconds, not 30).
## Acceptance (draft)
- A loop with a stop flag set before step 2 ends after step 2 with state X and an audit event with the reason code; no further model call or tool call is made (assert on the fakes).
- A flag that is never set changes nothing (all existing agent_loop tests unchanged).
- Worker test: SIGTERM during a slow fake step ends the process within the step time, run row in state X, not WORKING.
- A mutant: ignore the flag -> killed by the first test.
## Not decided here
Which state X (RECEIVED/WORKING stay for the tick vs a new parked state); whether resume after restart is wanted (needs the stored document: E-door-1, owner decision, default 'sender polls'); the reason-code spelling (audit field rules: no spaces, 128 chars).
