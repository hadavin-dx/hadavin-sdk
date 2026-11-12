"""The rules every remote secrets kind shares: a TTL cache, one refresh at a time, no empty values.

A value is cached for `ttl_s` seconds (0 = no cache), so a rotated value is picked up within one TTL. Fetches
run one at a time: two concurrent fetches straddling a rotation could otherwise let the older value land last
and be cached for a whole TTL. Values are never logged; errors name no secret and no value, only a fixed sentence and the error class.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from hadavin_sdk.errors import ConfigError


class CachedSecrets:
    """Subclasses implement `_fetch(name) -> str` and raise ConfigError for a missing secret."""

    def __init__(self, ttl_s: float = 300, clock: Callable[[], float] = time.monotonic) -> None:
        self.ttl_s, self._clock = ttl_s, clock
        self._cache: dict[str, tuple[float, str]] = {}
        # ponytail: one lock for every name; per-name locks if fetch latency ever matters (fetches are rare:
        # once per name per TTL).
        self._lock = threading.Lock()

    def get(self, name: str) -> str:
        with self._lock:
            now = self._clock()
            hit = self._cache.get(name)
            if hit is not None and now < hit[0]:
                return hit[1]
            try:
                value = self._fetch(name)
            except Exception as exc:
                # A cloud SDK error can quote the path or name it was asked for (a project id and a secret name sit in the resource path of GCP, an ARN in AWS, a URL in Azure), so the
                # text of the library error is never passed on: its class is enough to find the cause. An error class
                # of this package (`ConfigError`, `VaultError`) holds a sentence this package wrote and passes as it is.
                if type(exc).__module__.startswith("hadavin_sdk"):
                    raise
                raise ConfigError(
                    f"secrets: reading a secret failed ({type(exc).__name__})"
                ) from None
            if not value:  # an empty value would pass the start-up probe and fail at call time
                raise ConfigError("the secret is empty")
            if self.ttl_s > 0:
                self._cache[name] = (now + self.ttl_s, value)
            return value

    def _fetch(self, name: str) -> str:
        raise NotImplementedError
