# P4d round 6, correctness (egm:egm-codebase-details), head a49b196 (rev 7). Condensed. Verdict: NOT CLEAN. 1 MAJOR, 6 MINOR, 3 NIT. Reviewer ran nothing (no shell, no PG); head not verifiable; all PG facts (ON CONFLICT DO NOTHING takes no row lock, wait_event, make_interval) UNVERIFIED. Rounding rows a1-a8 and 22 round-5 applications, counts (32 methods -> 38, 18 write methods, 26 contract tests, 21 psycopg test files, 8 demo_askdata importers) and most cites verified by reading.
| id | sev | problem | fix |
|---|---|---|---|
| R6-C1 | MAJOR | B4(vii-b) (line 172), b15 (196), line 32: second admin `FOR UPDATE NOWAIT` on the run row fails (55P03) under the INVERTED order too, because the reserve holds FK `FOR KEY SHARE`; row cannot kill b15 (still killed by vii-a). Same class as round-5 F1. (= ADV-R6-1) | `FOR NO KEY UPDATE NOWAIT`; correct line 32. |
| R6-C2 | MINOR | Memory month = SUM of day counters (memory.py:199-204): i8-day, b26b equivalent on memory. (= ADV-R6-2) | Scope to Postgres or accept in writing. |
| R6-C3 | MINOR | a2-ii T3 retry row only holds under T2 settings. (= ADV-R6-7) | Pin to T2. |
| R6-C4 | MINOR | Write wrapper holds `self._lock` (plain Lock, postgres.py:197) for the whole transaction while `_insert/_select/_one/_update_run/_missing_or_stale` each take it (:217,:226,:248,:271): self-deadlock. | RLock or locked/unlocked helper split; unit test that every wrapped write completes. |
| R6-C5 | MINOR | Prose says ROUND_HALF_UP dies only on a1,a2 and ROUND_DOWN a1-a5; table adds a7. | Align. |
| R6-C6 | MINOR | `P3a.md` line 100 cite wrong (item 6 is at :106). | Cite by item. |
| R6-C7 | MINOR | `round_cost_up` home left open; P4a fixes `llm.common`; helper needs `MAX_USD` placed with store validators: llm->store import cycle risk. | Adopt `llm/common.py`; say where `MAX_USD` lives. |
| R6-C8 | NIT | PENDING LEAD 16 mentions `adjust_reserved` (leftover). | Delete. |
| R6-C9 | NIT | Settle SQL: missing counter row gives zero rows even on a raise -> `CounterDamaged`; contradicts "raising never damages". | State. |
| R6-C10 | NIT | Relay list: P2a.md:9 cites P4d.md:31 (now :33); P4c.md:27 still says 6 decimals. | Add. |
