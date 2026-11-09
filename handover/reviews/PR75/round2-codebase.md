# PR75 (P4d-a2) round 2 result review, codebase reviewer, head 6cdf67a (money path)
Reviewer: egm:egm-codebase-details (read-only, ran nothing). Report saved by the cloud session; reviewer claims unverified except where marked.
Verdict: no Blocker in code. 3 Majors, 4 Nits. Round NOT clean (money path, no cap).

## Findings
1. MAJOR (proof): snapshot has no mutant or fail-before run for the lock-order tests (vii-a/b/c: inverted-order mutant b15, b17, b11c/b11d/b28b/b28c). Only w-series mutants-final.md (40 killed, 1 survivor w10f); b/i mutants last run at c31f336. Missing too: P4d-venv-probe.md, ce70eb5 fail-before output, Postgres version/DSN, explicit HADAVIN_REQUIRE_PG line. 26 deselected in full-312.txt unexplained.
2. MAJOR (ticket compliance): memory.py:62 still threading.Lock() not RLock; reserve_spend reads self._kill.on (memory.py:293) while get_kill_switch reads the same field: ticket wants ONE private helper _kill_on(). test_memory_lone_caller.py comment about the run pre-check helper's lock is false (b29 equivalent). [CHECKED BY ME in snapshot: Lock at line 62 and self._kill.on at line 293 are present.]
3. MAJOR (no-suppression rule): tests/contracts/test_store_registry.py:307 adds `# noqa: S603`. [CHECKED BY ME: present in snapshot.] Restructure or justify to lead.
4. NIT: llm/fake.py:50-56 duplicates price_cost (llm/common.py); no InvalidOperation->ValueError translation; price_cost catches only InvalidOperation, decimal.Overflow possible for unvalidated routes.
5. NIT: test_cost_rounding.py:166 midnight-UTC race (two date reads).
6. NIT: check_usd/check_day/check_reserve run after set_config (one extra round trip; retry=False ignored for nested call).
7. NIT: 0006_spend_reservations.sql:54-55 update trigger does not keep expired_at NULL for open->settled/released.

## Fixed since round 1 (reviewer reading, unverified by me)
Lock-order tests present (lines 445-526), pass log 10723 passed/1 skipped on 3.12+3.13, timeouts via _checked_ms, transition matrix 40 rows P0001, uv.lock minimal, agent-loop rows on real Runtime, tenacity 9.2.1 valid, _purge_in_batches, type:ignore replaced by cast.

## NOT checked by reviewer
Postgres version/DSN; mutant kills at this head; ticket text after line 148; B1/B5/8-process/SIGKILL/T4 rows; test_p2_postgres.py:293 and test_k5_fixes2.py (M6); is_connectivity_error caller rows; check_id on existing writes; test_lockin_guard changes; CHANGELOG title scope; llm/fake callers; CodeQL/Sonar/CodeRabbit; Postgres 17 vs 16.15.
