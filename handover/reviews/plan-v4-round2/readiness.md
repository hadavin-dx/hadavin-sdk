# Plan v4.1 round 2: implementation readiness (fresh reviewer, read only plan-v4-1.md; ids kept, condensed)
Verdict: NOT READY as written for T1, T2, AK-G2-a, AK-G2-b and the Presidio backend. Line numbers are the plan's.
## A. T1 (section 8)
- A1 BLOCKER: no file, module, API, test name, base commit or branch; P4b1/P4d still in flight; step 9.3 runs T1 in parallel with the chain it depends on.
- A2 BLOCKER: pass rule "at most floor(C/W)" but expected numbers are exact (1, 50, 49); a meter admitting 0 passes; no assertion on refused callers making zero provider calls or on wrongly refused affordable calls.
- A3 MAJOR: settled amount versus reservation W not given; retries after refusal; whether all 50 reservations are held at once (barrier plus sleeping stub, no duration).
- A4 MAJOR: concurrency model undefined (threads/processes/asyncio, connections, Postgres version, memory store safety).
- A5 MAJOR: "sum of reservations never exceeds C at any moment" has no measurement method.
- A6 MAJOR: no failure rule ("not an owner gate" can read as ignorable); should block P4b1 merge for money-path defects.
- A7 NIT: "A9 B1", "STANDING-ORDERS 6d" undefined in the plan; cap scope unstated; slow-provider run has no owner or date; micro-dollars vs minor units.
## B. T2
- B1 BLOCKER: contradicts itself on layer (door not in test, but crash point (d) is after the 202 answer from the door).
- B2 BLOCKER: store API and clock injection point unspecified (Inbox.receive vs receive_inbound; no signature).
- B3 BLOCKER: crash injection mechanism and expected end state per crash point missing; store used not stated (memory store loses all state).
- B4 MAJOR: "at most one run row for run_id_for(K, generation)" needs a dispatcher; what bumps generation; lease window unstated.
- B5 MAJOR: replay schedule ambiguous (cumulative offsets; time of conflict check; bodies B and B').
- B6 MAJOR: schema check not testable (no table, column pattern, job list); whether the ticket deletes receipt rows is UNVERIFIED.
- B7 MAJOR: T2 scheduled before the code it tests (step 3 vs step 4); owner AK-G2-a does not exist yet.
- B8 MAJOR: T2b has no numbers (window length, HMAC parameters, key source).
- B9 NIT: add exact just-past-window values (24 h + 1 min).
## C. Other tests
- C1 MAJOR: T3 and T4 are one-line stubs. C2 MAJOR: T5 has no fixtures; whether Make/Activepieces can compute an HMAC is UNVERIFIED; gate on a pack ticket first.
## D. Packages
- D1 MAJOR: section 5 is a verdict table, not a work breakdown (no files, tests, dependencies, owner; "per chain" has no PR number or order; P2a, P4a, P4b1, P4b2, P5c, P4d-b/c have no PR).
- D2 MAJOR: step 9.1 "finish and verify the open chain" has no per-PR owner, stop rule or done criterion.
- D3 MAJOR: Presidio backend not buildable (build or outline? no trigger, interface, entity list, threshold, language set; refusal-rate bound OPEN).
- D4 MAJOR: AK-G2 build gates vague (which UNVERIFIED-KEEP rows, who verifies; reviewer set and round rule).
- D5 MAJOR: open items that change code: Postgres-only refusal in pilot/prod (4.1, 11.9), compare_ids reconciliation owner and frequency (11.11), P1c phase.
- D6 MAJOR: door runtime target undecided (triggers/webhook.py vs priced Workers "not the full door stack").
- D7 NIT: stop-rule wording (priority between "two clean rounds" and "third round freezes"). D8 NIT: EUR 8,004 vs USD 3,600 compared aloud against the plan's own rule.
## E. Resolve before handing to a builder: T1 (A1-A6), T2 (B1-B7), Presidio (D3), per-package files/deps/owners/merge order (D1, D2), Postgres-only question, compare_ids ownership, door runtime target (D5, D6).
Good: ticket-wins rule (4.2), OUT builds nothing (4.3), section 7 arithmetic checks out.
