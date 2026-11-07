"""Helpers shared by the provider-error tests: build a wire, run one call, rebuild the expected message."""

from __future__ import annotations

import ssl
import urllib.error
from collections.abc import Callable

import pytest

from hadavin_sdk.codes import ProviderErrorType as T
from hadavin_sdk.guard.diagnostic import class_name_of
from hadavin_sdk.llm import ProviderError, ProviderExhausted
from hadavin_sdk.llm.retry import with_retry
from tests.contracts.kinds.llm_wire import (
    AnthropicWire,
    BedrockWire,
    GeminiWire,
    OpenAICompatWire,
)

CALL = {
    "messages": [{"role": "user", "content": "Process the attached request document."}],
    "system": "Be exact.",
    "route": "default",
}
LIB = {"foreign_class", "dynamic_class"}
CANARY = "CANARY" + "-zq7"  # built from parts; never in an error text


def make_wire(kind: str):
    if kind == "anthropic":
        return AnthropicWire("api")
    if kind == "openai":
        return OpenAICompatWire()
    if kind == "gemini":
        return GeminiWire()
    if kind == "bedrock":
        return BedrockWire("in.anthropic.contract-model")
    raise AssertionError(kind)


def label_of(kind: str) -> str:
    return {
        "anthropic": "anthropic",
        "openai": "openai_compat",
        "gemini": "gemini",
        "bedrock": "bedrock",
    }[kind]


def run_chat(wire, *fixtures, build=None):
    """Serve the fixtures and call ``chat`` once; return the raised error (the call must fail)."""
    llm = build() if build else wire.serve(*fixtures)
    with pytest.raises(ProviderError) as got:
        llm.chat(**CALL)
    return got.value


def expected_message(label: str, err: ProviderError, attempts_suffix: bool) -> str:
    text = class_name_of(err.__context__)
    parts = [text]
    status, etype = getattr(err, "status", None), getattr(err, "error_type", None)
    if status is not None:
        parts.append(str(status))
    if etype is not None:
        parts.append(etype.value)
    msg = f"{label}: " + " ".join(parts)
    return msg + (f" after {getattr(err, 'retry_count', None)} attempts" if attempts_suffix else "")


class Counter:
    """A callable that raises ``make()`` each time and counts its calls."""

    def __init__(self, make: Callable[[], BaseException]) -> None:
        self.make, self.calls = make, 0

    def __call__(self):
        self.calls += 1
        raise self.make()


def _hooks(cls) -> dict:
    """The kind's hooks; ``facts`` is left out when the code has none (the fail-before base)."""
    out = {"retryable": cls.retryable}
    if getattr(cls, "facts", None) is not None:
        out["facts"] = cls.facts
    return out


def kind_hooks(kind: str) -> dict:
    if kind == "anthropic":
        from hadavin_sdk.llm.anthropic import AnthropicLLM

        return _hooks(AnthropicLLM)
    if kind == "bedrock":
        from hadavin_sdk.llm.bedrock import BedrockLLM

        return _hooks(BedrockLLM)
    return {}


# The built-in exception families a crashed hook or a missed guard lets escape (every concrete class a test hook raises is one of these).
RAW_ESCAPES: tuple[type[Exception], ...] = (
    ArithmeticError,
    AttributeError,
    LookupError,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
)


def run_retry(make, kind="std", *, label=None, max_attempts=3, sleeps=None, **extra):
    """Run ``with_retry`` on an error factory; return ``(error, calls)``."""
    call = Counter(make)
    waits = [] if sleeps is None else sleeps
    try:
        with_retry(
            call,
            label=label or ("openai_compat" if kind == "std" else kind),
            max_attempts=max_attempts,
            sleep=waits.append,
            **(kind_hooks(kind) | extra),
        )
    except ProviderError as e:
        return e, call.calls
    except RAW_ESCAPES as e:  # a raw escape is the failure these tests exist to catch
        raise AssertionError(
            f"a raw {type(e).__name__} escaped with_retry after {call.calls} calls"
        ) from None
    raise AssertionError("with_retry returned instead of raising")


def cert_error() -> urllib.error.URLError:
    return urllib.error.URLError(ssl.SSLCertVerificationError(1, "certificate verify failed"))


__all__ = [
    "CALL",
    "CANARY",
    "LIB",
    "ProviderError",
    "ProviderExhausted",
    "T",
    "cert_error",
    "expected_message",
    "kind_hooks",
    "label_of",
    "make_wire",
    "run_chat",
    "run_retry",
]
