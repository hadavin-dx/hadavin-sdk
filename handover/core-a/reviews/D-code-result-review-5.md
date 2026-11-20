Status: E1 code, fresh review round 1 (behaviour-changing code, no cap). No Blocker, 4 Major, test gaps, nits. Elephant decisions; fixes by builder e1-fix2.
| id | sev | finding | category | action |
|---|---|---|---|---|
| E1-1 | Major | _recover leaks the App/store on every failed try | PROPOSE FIX | close in finally |
| E1-2 | Major | Runner.health wedges if Thread.start raises | PROPOSE FIX | start first, assign after |
| E1-3 | Major | conflict audit write is synchronous, unbounded | PROPOSE FIX | bounded thread, 2 s, one pending |
| E1-4 | Major | persistent non-store error in _recover loops forever | PROPOSE FIX | 5 consecutive: exit 3 |
| E1-5 | Test | no test that an unsigned/wrong-signature request writes no event | PROPOSE FIX | test |
| E1-6 | Test | cap 'per sender' vacuous (one sender only) | PROPOSE FIX | two-sender test, bounded dict |
| E1-n1 | Nit | degraded socket timeout ACK_WAIT_S not runner.ack_wait_s | PROPOSE FIX | |
| E1-n2 | Nit | store_failures restarts after swap; inflated counts on a hung ping | PROPOSE FIX (docs) | |
| E1-n3 | Nit | 409 WARNING per request outside the cap | DECLINE | signed-only, no payload; volume only |
Answers (a)-(d) of the reviewer: no payload/signature/secret reaches event, log or /health; failing audit cannot change the 409; no 2xx before the real Runner exists; one run per key holds.
