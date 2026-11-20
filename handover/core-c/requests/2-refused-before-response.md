# Request 2 from core-c (TEXT) to core-b (owner of src/hadavin_sdk/llm/retry.py and llm/protocol.py)
Date 2026-11-20. Source: lead ORDER 011 (review round 1, finding M2 + m1, the ONE settle rule). core-c has NOT touched llm/.

## What is asked
A mark on `ProviderError` that says: THE PROVIDER REFUSED THIS REQUEST BEFORE IT PRODUCED ANY RESPONSE, SO NOTHING WAS BILLED.
The gate reads it with one predicate (`guard/model_gate.py`, `refused_before_response`, in the marked interface block):

    getattr(exc, "refused_before_response", False) is True
    and isinstance(exc, ProviderError) and not isinstance(exc, ProviderExhausted)

Either form satisfies it, your choice:
- a flag: `ProviderError.refused_before_response: bool = False` as a class attribute in `llm/protocol.py`, set to True on the instance where the refusal is known; or
- a subclass: `class ProviderRefused(ProviderError): refused_before_response = True`.
The attribute name and the exact value `True` are the contract (a truthy value that is not `True` is ignored).

## Where it would be set
`llm/retry.py` `with_retry`, the branch that raises at once for a non-transient failure (today lines 96-99):

    except Exception as exc:
        if not transient(exc, retryable):
            raise ProviderError(f"{label}: {describe(exc, detail)}") from exc

Set the mark there ONLY when the failure is an HTTP refusal of the request itself, with no model output: a status the module can read (`status(exc)`) in the 4xx range that is not retryable (400, 401, 403, 404, 413, 422 ...), or the kind's own SDK error class for "bad request / bad key / not found" (each kind already passes `retryable` and `detail`; a third hook, or the kind raising the marked error itself, would do).
Do NOT set it for:
- a `ProviderError` raised or converted after a response body was received (a reply that does not parse: the `ValueError` at `llm/gemini.py:106`, "a malformed answer is a ProviderError" at `llm/common.py:193-196`). That call was billed.
- the `except ProviderError: raise` pass-through at line 94-95, unless the inner raiser set it itself.
- `ProviderExhausted` (an attempt may have been answered or billed; the gate ignores the mark on it anyway).
- a non-transient error with no HTTP status (a TLS or certificate error, a local `TypeError`): unknown, leave unmarked.

## Why
The gate's settle rule (ORDER 011) is: (a) real cost known: settle it; (b) marked refused before any response: settle 0; (c) everything else: do NOT settle, the worst case stays booked until the store's sweep closes the reservation.
Today a plain `ProviderError` cannot be told apart: `with_retry` turns BOTH "401 bad key" (cost nothing) and "the billed reply did not parse" into the same class. The gate used to settle 0 for both, so a model steered off schema was paid for and booked at 0 on every call, and the cap was not exact (review finding M2).
UNTIL THE MARK EXISTS the gate treats NO error as refused-before-response: every failed call keeps its worst case booked. That is safe for the cap and costs head-room: an agent whose key is wrong books one worst case per attempt until the store's sweep closes it (`RESERVATION_EXPIRE_S` in the F-store draft; not built yet). The mark gives that head-room back.

## Tests on core-c's side (already there, with a fake exception carrying the flag)
tests/test_model_gate.py: `test_t13_rule_b_an_error_marked_refused_before_response_is_settled_at_zero`, `test_t13_rule_c_a_failed_call_is_not_settled_and_the_same_error_comes_out`, `test_no_error_the_adapters_raise_today_carries_the_mark` (this last one pins TODAY's state of `with_retry` and `ProviderError`: it will fail when you add the mark, on purpose: tell core-c, the test is then turned into "a 401 is marked, a parse failure is not").
Nothing to change in the gate when the mark lands.
