"""Secret provider: only the executor is given one. Runtime, approvals and llm never import this module."""

from __future__ import annotations

from typing import Protocol


class SecretProvider(Protocol):
    def get(self, name: str) -> str: ...


class FakeSecretProvider:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = dict(values)

    def get(self, name: str) -> str:
        return self._values[name]


# The bind guard (``hadavin_sdk.standins``, a leaf module) pins ``FakeSecretProvider`` now, as the class is
# created: the approvals side must not import this module, so this module tells the guard instead.
from hadavin_sdk import standins as _standins

_standins.pin_module(__name__)
