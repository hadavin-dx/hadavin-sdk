# Hand-off v16: what changed from v15 (v15 files are unchanged)

**Failures and gaps first.** (1) Not run: unit tests of this change (none is written), `bandit` of this change, CodeQL, the EGM skills (I cannot invoke them; review of this text is owed). (2) The baseline gate script ran once on the UNCHANGED tree: `ruff check`, `ruff format --check`, the timing tests and `bandit` ended `rc=0`; `pytest` ended `rc=1` (2 failed, 9364 passed, 454 skipped) because of two repository guard tests that read files under `handover/` outside this folder (lead question L20). (3) Postgres results are 16.15 only (CI uses 17.10; 14 is not installed here): L18. (4) The citation, planned-name and import-graph programs were NOT re-run in v16 (carried). (5) Prototype code (`add_spend_v16`, `spend_totals_v16`, `blocked_v16`, `reader_problems`, `secdef_guard_v16.py`) is not product code; the product code and tests are not written. (6) A 429/5xx storm can still use up an agent's day (the breaker only spaces attempts). (7) The runtime role can still lower totals and switch the kill switch off; DB-1 and DB-2 refuse bad values and record changes; the real control is dated design L-2 (5.10b).

Postgres evidence: `evidence-handoff-v16/pg_v16.py` through `pg_run_v16.sh`, 175 of 175 checks in each of two runs (`raw-pg-v16-run1.txt`, `raw-pg-v16-run2.txt`), every login by `scram-sha-256` password (checks Q1 to Q5), 16.15.

## Security review of v15 (6 majors, 8 minors; file `review-handoff-v15-security.md`)
| Finding | Old (v15) | New (v16) | Test that fails on the old design |
|---|---|---|---|
| Major 1 | Negative-total refusal rested on DB-1's held file | `add_spend` raises `ValueError` and rolls back on a negative or not-finite returned total, no held file (5.4 item 4b) | K1 (old shape accepts -1), K2 to K9; `test_negative_total_refused_without_held_file` (planned) |
| Major 2 | NaN or Infinity row crashed `Limits.blocked` | `spend_totals` refuses such a row; `blocked` returns `bad_amount`; card; `limits status` prints it (5.4 item 4b) | L1 (real `blocked` raises on NaN), L2 to L5 |
| Major 3 | Evidence author-run, `trust` login | password logins (Q1 to Q5), two runs, 175 of 175; independent re-run on 14 and 17 asked for: L18 | Q2 to Q5 (a wrong or missing password is refused) |
| Major 4 | The agent held the audit-reader secret | operator command line only; credential policy; `reader_problems` TEMP check; negative test (5.5b item 6, 5.6 item 1(g2)); code owned by the DB-2 PR | P1 to P7, G1 to G8; `test_agent_never_requests_audit_reader_secret` (planned) |
| Major 5 | Runtime can switch the kill switch off, unrecorded; L-2 "post-demo" | kill-switch record in DB-2 (5.6 item 1(m)); L-2 dated design 5.10b, due 2026-12-04 | M1 to M9 |
| Major 6 | No class guard for `SECURITY DEFINER` | guard over every SQL file (5.6 item 1(j)); 13 mutants | O1 to O3 |
| m1 | `lock_timeout` line undisclosed | deviation (vi); item 1(n) | none (text) |
| m2 | no default-to-variant path | `spend_nonneg_upgrade.sql`; item 1(k); needs L7 and PG 14 | N1 to N4 |
| m3 | lowest Postgres version unknown | question L18 | none |
| m4 | no append-only trigger | append-only triggers on both records; the owner limit stated (item 1(l)) | H1 to H5 |
| m5 | alarm owner, log growth | alarm owner under L13; size 110.6 B per row measured; retention under L16 | I1, I2 |
| m6 | qualify allowlist claimed, absent | stated in 5.3 (`v.reason_code in {None, "injection_suspected"}`); v15's row "Sec m2 | qualify mode switch | allowlist stated" was WRONG (the blacklist at `guard/judge.py:108` was not changed in v15); builder must read all reason codes: UNVERIFIED | planned E0-S2-4 |
| m7 | G-4(v) not asked | question L19 | none |
| m8 | 429/5xx storm | circuit breaker (5.3), config `breaker_failures`, `breaker_cooldown_s`; it spaces attempts, it does not change the daily bound | planned `tests/test_breaker.py` |
| other | DB-2 header cited a missing file; E0-S2-2 vs 5.6(c); two sets of timing numbers | header cites `raw-pg-v16-run1.txt`; inline ALTER texts in E0-S2-2; two runs measured (+0.061 and +0.049 ms, 110.6 B per row) | grep |

## Readiness review of v15 (5 majors, 9 minors; file `review-handoff-v15-readiness.md`)
| Finding | New (v16) | Where |
|---|---|---|
| M1 two gate types | one `Gate` protocol, both gates implement it, seam check, S-2a tightens; S-1 `chat` does not set `booked_usd`, S-2a adds it | 5.3 |
| M2 audit-reader code unowned | DB-2 PR writes `Grant(audit_read=)`, `migrate(audit_reader_role=)`, `reader_problems`; S-2b writes the two settings; the move PR adds two `GRANTS` entries | 5.5b item 6, 5.6 (g2), 7.1 |
| M3 S-2a test needed DB-1 | inline `ALTER TABLE` statements (`spend_usd_ok`, `spend_month_usd_ok`) in E0-S2-2; real node id `tests/test_spend_store_pg.py::test_store_emits_update_for_negative_deltas` for G-4(i); `test_inline_text_equals_default_held_file` in DB-1 | 7.2, 7.1 |
| M4 hot files | S-2a: `llm/anthropic.py`, `llm/gemini.py`, `config.py`, `limits.py`, `llm/retry.py`; S-2b: `PostgresSettings` fields; DB-1: `tests/test_lockin_guard.py`, `tests/test_secdef_guard.py`, `cli.py`; DB-2: `cli.py` | 7.1 |
| M5 `gate4.sh`, E0-S1-5 path, S-1 size | script ran once (baseline above); E0-S1-5 now reads v16's table; S-1 size unmeasured: question L21 with a proposed split | 7.2, section 10 |
| m1 `status_of` chain | public `retry.chain_status` (S-1) | 5.3 |
| m2 `extra` in snippet | snippet passes `extra=defaults.RELEASE_EXTRA_STATUSES` | 5.3 |
| m3 `worst_case_usd` clash | S-1 deletes the local one in `k1b/loop.py:115`; demo meter left alone | 5.3 |
| m4 heading | "S-2a; item 2 is owned by S-1" | 5.4 |
| m5 `Limits.charge` clock | `charge`, `reserve`, `settle` use `self.clock()` | 5.3 |
| m6 row 7 extra cell | merged | 5.9 |
| m7 13 vs 14 | other-tracks file says 14 | `CORE-PR-HANDOFF-v16-other-tracks.md` |
| m8 direct `NetworkLLM(...)` | grep list in S-1, `WindowOnlyGate(None)` in tests; list UNVERIFIED | 5.3 |
| m9 | no defect | none |
| Unverified items without a way | table "Unverified items and how each is settled" | section 10 |

## Independent evidence of v15 (`evidence-handoff-v15-independent/`)
`00-SUMMARY.md` was absent at 16:58 UTC; raw files read; see `resolve-handoff-v16.md` last section.

## Edits to carried PRs (L15)
Hot-file lists in 7.1 and the count in the other-tracks file (13 to 14). No PR content of the other tracks changed.
