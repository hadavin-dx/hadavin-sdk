Status: resolved (round 1 of 3; fixes queued for builder d-fix2)
# Goldfish Annotated Review Report: tests/endpoint_mutants.py (fresh reviewer egm-design, sonnet, read-only)
| id | sev | finding | category | action |
|---|---|---|---|---|
| B1 | Blocker (verified) | G7a anchor `self._take()` gone from crash.py (now `self._disarm()`): would ERROR | PROPOSE FIX | change anchor; keep it verified |
| M1 | Major | G12d, G18c killers skip on Windows -> read as SURVIVED | PROPOSE FIX | on win32 mark "not run here" loudly; docstring says POSIX |
| M2 | Major | log has 68 rows, stitched from two runs/script versions | PROPOSE FIX | ONE complete run on the final tree, unedited log with hashes |
| M3 | Major | two survivors (closed flag, handle_error) leave exit 0 | PROPOSE FIX | write both tests (already in d-fix1); until then named expected-SURVIVED |
| M4 | Major | guarantees with no mutant (parse_body duplicates, _answer agent/principal, check_senders, `is not True`, _content_length digits, ...) | PROPOSE FIX | add G21+ in priority order given; rest listed as left out with reason |
| N1 | Nit | G5a/G5b same mutant; G20a/c message-only; equivalent `if closed` lines | PROPOSE FIX | label them; add to left-out list |
| N2 | Nit | weak expect fragments (G7a first conjunct) | PROPOSE FIX (G7a only); rest DECLINE | |
| M5 | ok | G20j CRASH override sound | tally says "73 killed, 1 crash-accepted" | |
| F1 | Nit | fragile anchors, no uniqueness count, baseline_timeout 300 | PROPOSE FIX | assert old count == 1; baseline_timeout=900 |
