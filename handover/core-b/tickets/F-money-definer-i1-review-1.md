# F-money-definer-i1-review-1 (hostile review of I1: 168f10f43, 9e18334bf)

## Blocker / Major

### M1 (Major) The idempotent reserve succeeds for a hold that is no longer live (settled / expired / released)
- 0011_money_definer.sql ~L137-143 (`PERFORM 1 FROM spend_reservations ... IF FOUND THEN RETURN`); memory.py ~L352-360.
- The retry match compares agent, day, amount, run_id but NOT `status`. Scenario: reserve R (open) -> call fails/times out
  -> settle/expire/release_expired_spend (status settled/expired, counters lowered or settled) -> caller retries
  reserve R with the same arguments -> returns success, books nothing; the caller then calls the model on a reservation
  that holds no worst case on the counters (a settled-at-0 row after release_expired = a free model call; a settled row =
  a second call on a closed hold, and the later settle returns the first result with applied=False, so the real
  cost of the second call is never booked). This is exactly the "dead reservation" case.
- Fix: in the retry match add `AND r.status = 'open'` (PG) / `prior.status == "open"` (memory); any other status stays 23505 / StaleState.
  (An 'expired' hold still holds its worst case on the counters and could arguably be accepted; refuse it too, simplest and fail closed.)
  Add contract tests: retry after settle, after expire, after release_expired -> StaleState on both stores.

## Minor

### m1 Concurrency of the duplicate path (verified by reading, no defect, but untested)
- Two sessions inserting the same id: the second blocks on the unique index until the first ends; on commit DO NOTHING -> `NOT FOUND`,
  then the PERFORM runs as a new statement and (READ COMMITTED) sees the committed row -> success without touching counters;
  on rollback the second inserts. Counter UPDATEs are after the RETURN, so no double count, and a retry at the cap is not refused
  (the cap check is not reached). Correct only under READ COMMITTED: under REPEATABLE READ/SERIALIZABLE the PERFORM could not
  see the row and would raise 23505 (fail closed, acceptable). Fix: add a two-connection concurrent identical-reserve test
  (one row, counters booked once) and note READ COMMITTED in the function comment.

### m2 Existence leak (N6 residual, not widened)
- Another agent's id with identical arguments does not succeed: agent_id is in the match, so it is still 23505, the same as
  before. Only the owner of the row (same agent) gets the new success path. Residual N6 unchanged. No fix needed; the test
  for "other agent, same id/args -> StaleState" should be present (not seen).

### m3 Retry after purge is a new hold
- purge_spend_reservations deletes settled rows; a retry then books a fresh hold (counters booked again). That is a new
  reservation, consistent with the id being free again; but combined with M1 the "retry after settle" window is only
  bounded by the purge age. Fixed by M1 for the pre-purge window; post-purge is accepted.

### m4 Parity
- Memory has no HD005 (no caps row) / day-skew refusal, and ignores the PG-only cap source: pre-existing documented divergence, not new.
  Memory retry path is before the cap check, PG retry path is after the caps-row/skew/arg checks (a retry across the skew window or
  with caps row removed is refused on PG, accepted in memory): negligible; the retry should be tried at the cap boundary in both (see test).

## Checked, clean
- NULL p_agent in hadavin_settle_spend is refused 22023 before any lookup; the `p_agent IS NULL OR` branches are gone from both lock and fallback.
- Every Python path now passes an agent: Limits.settle/settle_for/_settle, Budget.settle/settle_for (check_store_id on agent), Store.settle_spend
  (memory + PG) keyword-only required. No remaining `None` caller in src (grep). A custom store with the old two-arg signature breaks by design (TypeError).
- check_spend_day (< 1970-01-01 refused): callers are add_spend, reserve_spend, release_expired_spend (postgres.py:645,931,1005) and the
  memory add_spend/reserve_spend. The DB already refuses these (reserve: 22023; add: same limit), so no legitimate caller regresses; only tests use pre-1970 dates (updated).

## Tests
Requested two test files were started on own DB hadavin_test_rv1 but had not finished inside the review window; no result claimed.
