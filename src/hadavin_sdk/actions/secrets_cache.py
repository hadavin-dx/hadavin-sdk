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

# One fixed word for the kind of failure, taken from the NAMES OF THE CLASSES of the library error (never from its
# text). First match wins; the words are written here.
_HINTS = (
    (("TimeoutError", "Timeout", "ReadTimeout", "ConnectTimeout", "ReadTimeoutError"), "timeout"),
    (("SSLError", "SSLCertVerificationError", "CertificateError"), "TLS"),
    (
        (
            "PermissionError",
            "AccessDenied",
            "AccessDeniedException",
            "Forbidden",
            "PermissionDenied",
            "Unauthorized",
            "ClientAuthenticationError",
        ),
        "access denied",
    ),
    (
        (
            "NotFound",
            "ResourceNotFoundError",
            "ResourceNotFoundException",
            "NoSuchKey",
            "ResourceNotFound",
            "FileNotFoundError",
            "NotFoundError",
        ),
        "not found",
    ),
    (
        (
            "URLError",
            "ConnectionError",
            "ConnectError",
            "EndpointConnectionError",
            "ServiceUnavailable",
        ),
        "network",
    ),
)


def _class_names(exc: BaseException) -> set[str]:
    """The class names of the error, of its parents and of the error it wraps (urllib's `reason`): names only."""
    names: set[str] = set()
    todo: list[BaseException | None] = [exc, getattr(exc, "reason", None)]
    for item in todo:
        if isinstance(item, BaseException):
            names.update(c.__name__ for c in type(item).__mro__)
    return names


def failure_hint(exc: BaseException) -> str:
    """`, timeout`, `, TLS`, `, access denied`, `, not found`, `, network` or nothing: one fixed word chosen from the class
    names of the library error. The error's text is not read."""
    names = _class_names(exc)
    for classes, word in _HINTS:
        if names.intersection(classes):
            return f", {word}"
    return ""


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
            failure = ""
            try:
                value = self._fetch(name)
            except Exception as exc:
                # A cloud SDK error can quote the path or name it was asked for (a project id and a secret name sit in the resource path of GCP, an ARN in AWS, a URL in Azure), so the
                # text of the library error is never passed on: its class and one fixed word taken from the class
                # (`failure_hint`) are enough to find the cause. An error class of this package (`ConfigError`,
                # `VaultError`) holds a sentence this package wrote and passes as it is. The new error is raised after
                # this block, so it has no cause and no context (a `from None` inside the block leaves the library
                # error in `__context__`, where a debugger can read its text).
                if type(exc).__module__.startswith("hadavin_sdk"):
                    raise
                failure = (
                    f"secrets: reading a secret failed ({type(exc).__name__}{failure_hint(exc)})"
                )
            if failure:
                raise ConfigError(failure)
            if not value:  # an empty value would pass the start-up probe and fail at call time
                raise ConfigError("the secret is empty")
            if self.ttl_s > 0:
                self._cache[name] = (now + self.ttl_s, value)
            return value

    def _fetch(self, name: str) -> str:
        raise NotImplementedError
