Status: round 3 of 3 (the cap) resolved by the Elephant; Majors left after this round go to ESCALATIONS.md (E7). Fresh reviewer egm-zoom-out (sonnet, read-only; did not read hmac_v0, agent_loop.handle, stores, tests).
| id | sev | finding | category | action |
|---|---|---|---|---|
| R3-1 | Major | server.py is 316 lines of wsgiref subclassing; ticket RIGHT-SIZE says ~250 lines in two modules, disk has 352+672+316 in three; waitress rung never tried | ESCALATE | E7 for the lead: accept stdlib or vet a server library; correct the RIGHT-SIZE sentence either way (PROPOSE FIX for the text) |
| R3-2 | Major | config errors print only the class name; a typo in config.yaml gives no field | PROPOSE FIX | print str(exc) for the ConfigError family (core-b messages name fields; check none carries a value); generic Exception branch stays class-name-only |
| R3-3 | Major | log format %(message)s: no time, no level | PROPOSE FIX | "%(asctime)s %(levelname)s %(message)s" |
| R3-4 | Major | ticket file lengths and line numbers stale | PROPOSE FIX | one re-take at the end, after the last code edit |
| R3-5 | Nit | knobs reachable only by tests (make_server bounds, Runner poll_s/max_waiting validation, check_port 0) | DECLINE (recorded, E7 note) | they are guards, each pinned by a test and a mutant; deleting is a lead decision with R3-1 |
| R3-6 | Nit | double/dead paths (check_secrets twice, MAX_SENDERS twice, NUL test in derive_run_id, list branch of sender_map) | DECLINE this round | deleting would move mutant anchors; listed for the lead with R3-1 |
| R3-7 | Nit | _decide closed pre-check without lock | PROPOSE FIX only if equivalent; mutant for it is on the left-out list as equivalent | take it with R3-3 if safe |
| R3-8 | Nit | is_store_error module sniffing; check_spend tests for step F method | DECLINE | E7 note |
| R3-9 | Nit | --host "" silently becomes loopback | PROPOSE FIX | default=LOOPBACK, drop the `or`, test |
| R3-10 | Nit | start-up line gives port only; stop prints nothing | PROPOSE FIX | log "listening on http://HOST:PORT/PATH" and "stopping, waiting for N runs" |
| R3-11 | Nit | stale text (check_bind docstring, endpoint.py:257 wording, server.py 11 vs 15) | PROPOSE FIX | |
| R3-12 | Nit | header buffering 6.4 MB per connection x 256 | DECLINE | stdlib behaviour, port is loopback by default; README states it |
Fixes R3-2,3,4(last),7,9,10,11 run as d-fix4 after the evidence batch finishes (batch5 reads the tree now); then the evidence for the changed files is re-run (fast subset + mutants), not a new whole-suite batch unless the lead asks.
