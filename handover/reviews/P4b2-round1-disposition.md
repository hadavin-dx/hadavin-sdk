# P4b2 round 1 disposition (revision 1 to revision 2)

Author of revision 2 (revision author agent). Ticket: `handover/tickets/P4b2.md`, now 276 lines (revision 1 had 311). Input: `reviews/P4b2-round1-resolve.md` (26 rows, all PROPOSE FIX), checked against `P4b2-round1-adversarial.md` (A1-A18) and `P4b2-round1-correctness.md` (C1-C12). Nothing was run: file reads only; no test, no Postgres, no model call.

## Honest notes first
- I applied every row. Nothing was declined. Three places go slightly beyond the words of the resolve; each is marked in the ticket and needs the lead's eye (items X1-X3 below).
- Facts I re-read myself in `src/`: `with_retry` pass-through (`retry.py:95-96`), the single caller `_retry`, `NetworkLLM.chat` -> `_chat` -> `_retry`, `openai_compat.py:118-125` (two requests per chat), `bedrock.py:47-48`, `protocol.py:10-15`, `limits.py:35`, `tick.py:156,174`, `Reply` at `models.py:289-297`, `test_llm.py:73-96`. Facts marked "(round 1 resolve)" in the ticket I did not re-check (botocore MRO, PG 16.15 case B, P4a/P4d line cites other than the five I grepped: `P4d.md:160,178,267,286`, P4a PL51/54/55/60 names).
- I did not edit the ledger, P4b1, P4c, P4d, P4a or any other ticket (order of the task), so every coupling is written as a PENDING LEAD item, not applied.

## The 26 rows and where each landed in the ticket
| Row | What the ticket now says | Where |
|---|---|---|
| A1 (blocker) | Counts per chat (one call-scoped counter, defined in `llm/retry.py`, added into by every `_retry` of a chat); counts ride on success via one `Reply` field (`unknown_attempts`, default 0, read rule stated); unit `a = ceil(reserved_micro / request_bound(inner))`; booking table (success, kept with readable stamp, kept with no stamp = whole-call maximum); "success needs no stamp" line and the `prior_unknown_requests` deferral deleted; made-up example numbers; cap-overshoot stated; rows G15, L7, L8, T11; mutants a17, a18, a19, a22, a23 | Rules 3, 6; P4b2-a Interface; G11, G15 |
| N1 (mine, money) | Request 1 answered then request 2 failing: counted unknown through the shared counter; pin row G15 / L8 / T11; mutant a19 (counter reset per request) | Rules 2, 3; T11, L8, G15, a19 |
| A2 + C3 | `REFUSED_STATUSES = (400, 401, 403, 404, 405, 413, 415, 422, 429)` allow-list in `llm/retry.py`, reason per entry; everything else (402, 408, 409, 418, 424, 499, 777, 5xx) unknown; T3 rows; mutant a3; PENDING LEAD 3 replaced by 14 | Rule 2; Interface; T3; a3; PL14 |
| A3 + C6 | Pass-through merges: stamps the call counter with the attempt as unknown and re-raises; the "unless it already carries stamps" clause deleted; T7(b); mutant a20 | Interface `with_retry`; T7; a20 |
| A4 + C4 | One frozen `AttemptCounts` stamp, built only in `llm/retry.py`, read with `vars(exc).get`, accepted only if `type(v) is AttemptCounts`; class attributes and `attempts == 0` release clause deleted; T5 gains `billing_outcome(ProviderError("x"))` and `ProviderExhausted("x")` keep rows (kills old a1); T9 guard on `AttemptCounts(` with its limit stated | Rule 4; Interface; T5, T9; a1, a7, a8, a21 |
| A5 (narrowed) | Residual stated in the Problem text and Rollback; no connect-phase rule; v1.1 row with trigger and owner | P4b2-a Problem; v1.1 list |
| A6 + C1 | Closed by the cut (no grant, no column list). The fallback list (starting with `expired_at`) is in PENDING LEAD 12 | PL12 |
| A7 (cut) | Maintenance identity cut: no role, grant, trigger, migration, DSN secret, CLI flag, App field, about 20 mutants. Plain reason and plain statement that expiry does not give money back until the day or month counter rolls over. Overrides amendment F2: PENDING LEAD 12 (NEEDS LEAD 13 already raised by the lead) | P4b2-b Problem, "Why the maintenance identity is cut"; PL12 |
| A8 | Closed by the cut: sweep as the runtime role per P4d, Protocol identity-agnostic, no P4d amendment. Pruning not owned by P4b2; P4c must own its exit path | "NOT taken"; PL5 |
| A9 | Closed by the cut (no discriminator trigger); fallback in PL12 | PL12 |
| A10 + C10 | Step uses `app.store` on every kind; no new secret; one upgrade row U1 (old config, exit 0, old row expired); `test_p7_tick.py` step-list change named | P4b2-b step item 1; U1; Files |
| A11 + C7 | Load-time warning and `call_bound_s` deleted; relay to P4b1 (`METER_MAX_HOLD_S` 400) kept as PL9; words "hold age" and "reservation age" defined; M4 and b4 shrunk to "the step passes `orphan_age_s()`" | Words; P4b2-b config item; M4; b4 |
| A12 + E2 | CONTESTED the ticket's own fact (k1b failure under-count is closed by P4a-2 PL54); old item 6 and old K1-K2 deleted. New scope per E2: k1b answered path books answered + `prior_unknown x W`, then PL55's fake-only guard deleted in `k1b/replay.py`; new K1 (two timeouts then answer books answered + 2W), K2 (real-kind label loads), K3 (`bedrock_guardrail` still refused); failure bookings (6W) and PL62 allowlist untouched; hot files and the P5b2 `ConfigError(` count 8 to 7 | Verified facts; P4b2-a k1b item; K1-K3; a24, a25; PL6 |
| A13 | a/b split kept; G12 and G13 cut (pointer to P4d's 8-process row and P4c-2 T8); T1-T10, L rows, G1-G11, G14 kept; mutant tables renumbered | Tests; mutation tables |
| A14 | Closed by the cut (no migration) | PL12 |
| A15 + C9 | Moved out: pseudo-role refusal recorded as an OPEN ledger row text (names listed, split into regression pins and fail-before), recommended owner P2a-1 build notes; not dropped | "v1.1 list and items moved out"; PL13 |
| A16 | One order on `llm/metered.py`: P4b1-b, P4b2-a, P4c-2 | Depends on; PL15 |
| A17 | G14 (every `UsageMissing` reason, `UnpricedUsage`, request-2 re-raise: kept, booked per rule 6); `run_id="-"` precedent `limits.py:35` | G14; step item 3 |
| A18 | "orphan" renamed "abandoned reservation" everywhere; step name `expire_spend_reservations` (audit operation renamed `expire_reservations`) | Words; whole ticket |
| C2 (narrowed) | Per-kind L applicability table; Bedrock connection failure (`EndpointConnectionError`, not an `OSError`) declared unknown and kept in v1, no `unsent_of` hook (v1.1 row); Bedrock L4 replaced by a keep row, L5 by a `_parse` unit test | L rows; v1.1 list |
| C5 | Header names P4d revision 10 with five sub-tickets and P4a revision 12 FROZEN; every "PENDING P4a" replaced by P4a's real names; `older_than_s`, `limit`, `expired_at` re-read at `P4d.md:160,178` | First paragraph; Depends on |
| C8 | The rights table copying the sweep SQL deleted; the ticket cites `P4d.md:178` | Verified facts |
| C11, C12 | "two classes with docstrings and no attributes"; `tests/contracts/test_llm.py:73-108` | Verified facts; Tests |
| E1 (lead erratum) | P3a dropped from the `cli.py` order list; with the cut P4b2-b no longer edits `cli.py`, `store/migrate.py`, `app.py`, `backends/table.py` at all and those hot-file lines are removed | P4b2-b Depends on |
| N2 (mine) | The "NO new method on Hold" line deleted; P4b1 must compare only answered usage with the reservation and take the extra separately (`Hold.record(actual, *, unanswered=0)` as an example); PL16; row G16 and mutant a26 | P4b2-a Interface (wrapper); PL16; G16; a26 |
| N3 (mine) | `llm` file order P4a-1, P4a-2, P5b1, P4b2-a recommended; `status_of` reads facts; no `detail` reads; `retry_count` derived from or checked against the stamp's attempts; P4a's `common.py` line read as superseded; PL17 | Depends on; PL8; PL17 |

Row count check: 26 rows applied; 0 declined; 0 escalated; unaddressed 0. Resolve's PENDING LEAD 12-18 are PENDING LEAD 12-18 in the ticket (same numbers).

## Counts (recounted from the new file, not copied)
- Mutants: P4b2-a 26 (a1-a26; revision 1: 19); P4b2-b 11 (b1-b11; revision 1: 20). Total 37 (revision 1: 39).
- Rows: P4b2-a 36 = T 11 (T1-T11) + L 8 (L1-L8) + G 14 (G1-G11, G14, G15, G16; G12 and G13 cut and not reused) + K 3 (K1-K3). P4b2-b 13 = E 6 (E1, E2, E3, E5, E6, E9; E4, E7, E8 cut and not reused) + U 1 + M 5 (M1-M5) + Q 1 (Q3). Total 49. Revision 1 had 57 named rows (T 10, L 7, G 13, K 2, S 4, H 1, E 9, M 5, C 3, Q 3).
- Template fields: 17 in each of P4b2-a and P4b2-b.
- PENDING LEAD items: 18 (1-11 from revision 1, of which 2, 3, 4, 6 are moot or replaced; 12-18 new).
- Lines: 276.

## Not applied, or applied beyond the resolve (the lead should look)
- X1. Failure side of N2. The resolve names the interface change only for a success (`Hold.record(actual, *, unanswered=0)`). Its booking table also books MORE than the reservation on a kept failure (`max(reserved, unknown x a)`, whole-call maximum). That cannot be booked without the same no-halt path, so the ticket asks P4b1 for a second call (example name `Hold.keep(*, unanswered=n)`). This is my inference, put in PENDING LEAD 16. Names are examples, not decisions.
- X2. Non-`ProviderError` exceptions (`KeyboardInterrupt`, `SystemExit`, any other exception). Revision 1 settled them at the reservation. The resolve's rule "kept failure with no readable stamp = whole-call maximum" does not name them; I applied it to them too (order 14(3): where billing is unknown, book the upper bound). Rule 6, rows G5, a23. Say so if the lead wants them left at the reservation.
- X3. Where the stamp and decision function live. The resolve puts `REFUSED_STATUSES` and `AttemptCounts` in `llm/retry.py`; revision 1 had `billing_outcome` and `BillingOutcome` in `llm/protocol.py`. Because `billing_outcome` must test `type(v) is AttemptCounts` and `protocol.py` would then import `retry.py`, I moved `billing_outcome`, `BillingOutcome` and `BILLING_REASONS` to `llm/retry.py` and dropped `llm/protocol.py` from the files this sub-ticket edits. `BILLING_REASONS` gained `no_stamp`.
- Also: the `Reply` field name `unknown_attempts` and the way the counter reaches `_retry` (argument or `ContextVar`) are the builder's/lead's choice, as the resolve said the author picks the name; both marked UNVERIFIED.
- Ledger row for the pseudo-role refusal (A15/C9): written as text in the ticket, NOT added to the ledger (I may touch only the two files). The lead or the next resolve adds it.
- Couplings that need other authors (not done by me, per task): P4b1 interface (PL16, PL9), P4a `llm/common.py` order line (PL17), P4c exit path for `wall_alerts` (PL5), P5b2 `ConfigError(` count 8 to 7 (K2 note).
- Order 20 item 1 (build tests on PostgreSQL 16 and 17) is applied to P4b2 as the safe reading; order 20 was read by grep and cut only, as told.
- Wording changes I made on my own to meet the rules: removed the drafting-model name from the header; removed two studio-file names from the "not read" list; no model ids, owner names, studio paths or real-looking values remain (grep checked: the only hit for "studio" is the file name `STUDIO-RULES`).
