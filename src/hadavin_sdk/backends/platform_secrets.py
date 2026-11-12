"""Platform secrets: the credentials a backend itself needs (a Slack token, a database DSN, an API key).

Kept apart from the executor's provider (design §4.4): a backend factory gets a ``resolve`` that reads only the
``*_secret_name`` values in its own settings, and no platform name may also be an action's executor secret.
``runtime/``, ``approvals/`` and ``llm/`` never import this module (tests/test_repo_rules.py).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from pydantic import BaseModel

from hadavin_sdk.actions.secrets import SecretProvider
from hadavin_sdk.errors import ConfigError


def _labels(settings: Iterable[BaseModel]) -> dict[str, str]:
    """Where each platform secret name is set: `<Settings class>.<field>` (words written in code), never the name."""
    out: dict[str, str] = {}
    for s in settings:
        for k, v in s:
            if k.endswith("_secret_name") and v:
                out.setdefault(v, f"{type(s).__name__}.{k}")
    return out


def _place(
    name: str, labels: dict[str, str], executors: Iterable[str], tools: Iterable[str]
) -> str:
    """The place of one secret for an error text: the settings field that names it, else its position among the
    tool secrets or the action executor secrets (sorted). The name itself is configured text and is never printed:
    a password pasted into a name field must not come back in a message."""
    if name in labels:
        return f"the secret set in {labels[name]}"
    for group, word in ((sorted(tools), "read-tool"), (sorted(executors), "action executor")):
        if name in group:
            return f"{word} secret {group.index(name) + 1} of {len(group)} (sorted by name)"
    return "a configured secret"


def _places(
    names: Iterable[str], labels: dict[str, str], executors: Iterable[str], tools: Iterable[str]
) -> str:
    return ", ".join(_place(n, labels, executors, tools) for n in sorted(names))


def secret_names(settings: BaseModel) -> set[str]:
    """Every set ``*_secret_name`` value in one backend's settings."""
    return {v for k, v in settings if k.endswith("_secret_name") and v}


def bound(provider: SecretProvider, settings: BaseModel, label: str) -> Callable[[str], str]:
    allowed = secret_names(settings)

    def resolve(name: str) -> str:
        if name not in allowed:
            raise ConfigError(
                f"{label}: may read only the secrets named in its own settings (a name that is not one of them is never quoted)"
            )
        return provider.get(name)

    return resolve


def check(
    provider: SecretProvider,
    settings: Iterable[BaseModel],
    executor_names: set[str],
    tool_names: set[str] | None = None,
) -> None:
    """Start-up: platform and executor names never overlap, and every one of them resolves once. A read tool's
    secret (K5) is a platform secret: it must not be an action executor's either."""
    settings = list(settings)
    backend: set[str] = set().union(*(secret_names(s) for s in settings))
    tools = tool_names or set()
    labels = _labels(settings)
    if shared := backend & tools:
        raise ConfigError(
            f"secret names used by both a backend and a read tool: {_places(shared, labels, executor_names, tools)}; "
            "give the tool its own secret"
        )
    platform = backend | tools
    if overlap := platform & executor_names:
        raise ConfigError(
            f"secret names used by both a backend and an action executor: {_places(overlap, labels, executor_names, tools)}; "
            "give the backend its own secret"
        )
    for name in sorted(platform | executor_names):
        # Any provider failure is a start-up failure; the value is never shown.
        try:
            provider.get(name)
        except Exception as exc:  # noqa: BLE001 - any provider failure stops start-up; the type is all that is kept
            raise ConfigError(
                f"{_place(name, labels, executor_names, tools)} cannot be read at start-up ({type(exc).__name__})"
            ) from None
