"""Secret provider: only the executor is given one. Runtime, approvals and llm never import this module."""

from __future__ import annotations

from typing import Protocol

from hadavin_sdk.standins import stand_in


class SecretProvider(Protocol):
    def get(self, name: str) -> str: ...


@stand_in
class FakeSecretProvider:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = dict(values)

    def get(self, name: str) -> str:
        return self._values[name]
