"""Platform secrets: the credentials a backend itself needs (a Slack token, a database DSN, an API key).

Kept apart from the executor's provider (design §4.4): a backend factory gets a ``resolve`` that reads only the
``*_secret_name`` values in its own settings, and no platform name may also be an action's executor secret.
``runtime/``, ``approvals/`` and ``llm/`` never import this module (tests/test_repo_rules.py).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from pydantic import BaseModel

from hadavin_sdk.actions.secrets import SecretProvider
from hadavin_sdk.errors import ConfigError, shown_name


def _names(names: Iterable[str]) -> str:
    """Secret NAMES (never values) for an error text, each through `shown_name`. The names are the configured ones
    (the caller passes the sets it just read), so each is a loaded name."""
    names = sorted(names)
    return ", ".join(shown_name(n, names) for n in names)


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
    if shared := backend & tools:
        raise ConfigError(
            f"secret names used by both a backend and a read tool: {_names(shared)}; "
            "give the tool its own secret"
        )
    platform = backend | tools
    if overlap := platform & executor_names:
        raise ConfigError(
            f"secret names used by both a backend and an action executor: {_names(overlap)}; "
            "give the backend its own secret"
        )
    for name in sorted(platform | executor_names):
        # Any provider failure is a start-up failure; the value is never shown.
        try:
            provider.get(name)
        except Exception as exc:  # noqa: BLE001 - any provider failure stops start-up; the type is all that is kept
            raise ConfigError(
                f"secret {shown_name(name, platform | executor_names)} cannot be read at start-up ({type(exc).__name__})"
            ) from None
