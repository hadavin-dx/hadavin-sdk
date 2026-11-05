"""Circuit breaker example for agent-killswitch.

Demonstrates the circuit breaker pattern for protecting against
cascading failures in AI agent API calls.
"""

from __future__ import annotations

import random
import time

from agent_killswitch import CircuitBreaker, CircuitBreakerOpen


def main() -> None:
    # Create a circuit breaker for an unreliable API
    breaker = CircuitBreaker(
        name="openai-api",
        failure_threshold=3,  # Open after 3 consecutive failures
        recovery_timeout=5.0,  # Try recovery after 5 seconds
        half_open_max_calls=1,  # Allow 1 test call in half-open
        on_state_change=lambda name, old, new: print(
            f"  Circuit '{name}': {old.value} -> {new.value}"
        ),
    )

    # Simulate API calls
    call_count = 0
    success_count = 0
    failure_count = 0
    rejected_count = 0

    def unreliable_api(success_rate: float) -> str:
        """Simulated API that fails at a configurable rate."""
        if random.random() > success_rate:
            raise ConnectionError("API timeout")
        return "API response"

    print("Phase 1: API is healthy (90% success rate)")
    for i in range(10):
        call_count += 1
        try:
            breaker.call(unreliable_api, 0.9)
            success_count += 1
        except CircuitBreakerOpen:
            rejected_count += 1
            print(f"  Call {i}: REJECTED (circuit open)")
        except ConnectionError:
            failure_count += 1
            print(f"  Call {i}: FAILED")

    print(f"  State: {breaker.get_state().value}")
    print(f"  Success: {success_count}, Failed: {failure_count}, Rejected: {rejected_count}")

    print("\nPhase 2: API goes down (10% success rate)")
    for i in range(10):
        call_count += 1
        try:
            breaker.call(unreliable_api, 0.1)
            success_count += 1
        except CircuitBreakerOpen as e:
            rejected_count += 1
            print(f"  Call {i}: REJECTED (retry in {e.time_until_half_open:.1f}s)")
        except ConnectionError:
            failure_count += 1
            print(f"  Call {i}: FAILED")

    print(f"  State: {breaker.get_state().value}")

    print("\nPhase 3: Waiting for recovery timeout...")
    time.sleep(5.5)
    print(f"  State after wait: {breaker.get_state().value}")

    print("\nPhase 4: API recovers (95% success rate)")
    for i in range(5):
        call_count += 1
        try:
            breaker.call(unreliable_api, 0.95)
            success_count += 1
            print(f"  Call {i}: SUCCESS")
        except CircuitBreakerOpen:
            rejected_count += 1
        except ConnectionError:
            failure_count += 1

    print(f"\n  Final state: {breaker.get_state().value}")
    print(
        f"  Total: {call_count} calls, {success_count} success, "
        f"{failure_count} failed, {rejected_count} rejected"
    )


if __name__ == "__main__":
    main()
