Status: round 2 of 3; Elephant decisions below (fresh reviewer egm-codebase-details, sonnet, read-only; not read: tests, cli, stores, requests/004)
| id | sev | finding | category | action |
|---|---|---|---|---|
| R2-1 | Major | ticket text contradicts the code (invariant 15, 6b, 7, 7b, line cites) | PROPOSE FIX | ticket-D2 (running) |
| R2-2 | Nit | missing core-b field = AttributeError, exit 3, not ConfigError naming the field | PROPOSE FIX | D-fix3 |
| R2-3 | Nit | slot release in same finally as shutdown_request | PROPOSE FIX | D-fix3 |
| R2-4 | Nit | cap hit logged only at DEBUG | PROPOSE FIX | D-fix3 (WARNING at most once a minute, no client data) |
| R2-5 | Nit | read_deadline_s, max_connections, port unvalidated | PROPOSE FIX | D-fix3 |
| R2-6 | Nit | private runner._ack_wait_s | PROPOSE FIX | D-fix3 |
| R2-7 | Nit | INFO handler on whole hadavin_sdk logger | PROPOSE FIX | D-fix3: handler on hadavin_sdk.triggers only (lead ORDER 020 said hadavin_sdk loggers; narrower is inside it) |
| R2-8 | Nit | endpoint trusts any start callable (invariant 7 holds for Runner.start) | PROPOSE FIX | docstring line |
Round clean? No (1 Major). Fix, then round 3 (last under the cap).
