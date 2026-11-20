# INTERFACE (ii): the Meter the model gate calls. FINAL after the F-store ticket review and the lead's ORDER 010 (2026-11-20 05:50 UTC)
BUILT: src/hadavin_sdk/limits.py on cloud/core-b (commit 8db9c29 and fix round 1; tests tests/test_limits_reserve.py, tests/contracts/test_store_spend.py, tests/contracts/test_t1_reserve_cap.py: 471 passed on PostgreSQL 16 in this container; the lead's PostgreSQL 17 run is the one that counts). The in-memory Budget meter arrives with step F-install. Full context: interfaces/README.md (version 2.3).

```python
class SpendRefused(RuntimeError):
    """Do not call the model. reason is one of:
    kill_switch | daily_budget | monthly_budget | limits_unavailable | bad_amount | usd_cap"""
    def __init__(self, reason: str) -> None:
        super().__init__(reason); self.reason = reason

class Meter(Protocol):   # implemented by Limits (store-backed) and by k1b Budget (in memory, with a lock)
    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str: ...
    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal: ...
```

SIX reasons since 06:20 UTC (lead ORDER 014): usd_cap is raised only by the in-memory Budget meter (the eval and replay command lines) when its one total cap would be passed or the budget was closed after an abandoned call. Allowlist all six.
Provider errors: `ProviderError.refused_before_response` (class attribute, default False; set True only in llm/retry.py with_retry) marks an error where the provider refused before any response: every attempt was a refused connection or a failed name lookup, or the final answer was HTTP 400, 401, 403, 404, 413 or 422 with no earlier attempt answered or timed out. Built in commit "code F: providers mark an error ..." on cloud/core-b. OPEN (request to core-c, requests/to-core-c-1-exhausted-mark.md): an error that used up its retries arrives as ProviderExhausted, which the gate excludes by type even when the mark is True; HTTP 429 and refused connections end that way.

What the gate can rely on:
1. reserve returns a reservation id only after the worst case is booked. Any exception from reserve means: do not call the model. SpendRefused.reason is the audit error code. An unknown agent raises KeyError (still no call).
2. worst_usd must be exactly a Decimal, finite, 0 or more and below 1000000000. A float, bool, int, None, NaN, Infinity or negative value raises SpendRefused("bad_amount").
3. settle returns the overshoot, max(0, settled minus reserved), taken from the STORED row: the first settle wins; a repeat with another amount returns the first result and changes nothing.
4. settle with an unknown reservation id raises NotFound (a KeyError subclass) from both meters. settle with a bad amount raises ValueError.
5. Cost known (also 0 for a request that was refused before sending): settle(rid, cost). Cost unknown (timeout, abandoned thread, crash): either settle(rid, worst_usd) or do not settle; both keep the worst case booked. Never settle lower than the truth.
6. If settle raises (store down after the call), return the reply anyway; the worst case stays booked. Never retry reserve.
7. One reserve covers the whole chat call including the client's own retries; so worst_usd must cover system prompt, messages, tool schemas and documents at the input price (at most one token per byte) plus route.max_tokens at the output price, times the client's max_attempts. core-b supplies this as the worst_case= callable at each install site (helper worst_case_usd in src/hadavin_sdk/llm/common.py).
8. The settled cost is added to the run's cost by the store (when run_id was given). The gate and the agent loop must not add it again; nothing calls Limits.charge for a gated call.
9. A stop set between the stop-state read and the booking lets that one call through; it takes effect at the next reserve. The Budget meter (command-line eval and replay) does not read the stop state.
10. An open reservation older than the expiry age (the larger of 3600 seconds and the stuck-run age) is closed by a tick step at its worst case; a later settle can only raise the booked amount, never lower it.
