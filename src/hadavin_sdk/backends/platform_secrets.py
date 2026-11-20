"""Platform secrets: the credentials a backend itself needs (a Slack token, a database DSN, an API key).

Kept apart from the executor's provider (design §4.4): a backend factory gets a ``resolve`` that reads only the
``*_secret_name`` values in its own settings, and no platform name may also be an action's executor secret.
``runtime/``, ``approvals/`` and ``llm/`` never import this module (tests/test_repo_rules.py).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

from pydantic import BaseModel

from hadavin_sdk.actions.secrets import SecretProvider
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.secret_name import canonical_secret_name, is_path_shaped


def secret_names(settings: BaseModel) -> set[str]:
    """Every set ``*_secret_name`` value in one backend's settings."""
    return {v for k, v in settings if k.endswith("_secret_name") and v}


def bound(provider: SecretProvider, settings: BaseModel, label: str) -> Callable[[str], str]:
    allowed = secret_names(settings)

    def resolve(name: str) -> str:
        if name not in allowed:
            raise ConfigError(
                f"{label}: may read only the secrets named in its own settings, not {name!r}"
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
            f"secret names used by both a backend and a read tool: {sorted(shared)}; "
            "give the tool its own secret"
        )
    platform = backend | tools
    if overlap := platform & executor_names:
        raise ConfigError(
            f"secret names used by both a backend and an action executor: {sorted(overlap)}; "
            "give the backend its own secret"
        )
    for name in sorted(platform | executor_names):
        # Any provider failure is a start-up failure; the value is never shown.
        try:
            provider.get(name)
        except Exception as exc:
            raise ConfigError(f"secret {name!r} cannot be read at start-up") from exc


def sender_field(sender_id: str) -> str:
    return f"triggers.senders.{sender_id}.secret_names"


def check_senders(
    provider: SecretProvider, senders: Mapping[str, Iterable[str]], other_names: set[str]
) -> None:
    """Start-up, the signed trigger endpoint: no sender secret name is also a name another part of the app uses
    (`other_names`: backends, action executors, read tools, sources, the restored-hash key), and every one resolves
    once. Every refusal is found before the first read. A message names the sender and the field, never the name:
    a mistyped config may hold the secret itself there, so the provider's own error is not chained either."""
    senders = {sender_id: sorted(set(names)) for sender_id, names in sorted(senders.items())}
    if any(is_path_shaped(n) for n in other_names):
        # A mounted_file provider resolves "a/../x" to the file "x": refused, not folded (a name is not shown).
        raise ConfigError(
            "a secret name elsewhere in the config has a path form (a '.' or '..' segment, or a leading or "
            "trailing '/'); write it as a plain name so that it can be compared with the sender names"
        )
    other_names = {canonical_secret_name(n) for n in other_names}
    if shared := [
        f"{sender_field(sender_id)}: a name is also used by another part of the config "
        "(a backend, an action, a read tool, a source or the restored-hash key); give the sender its own secret"
        for sender_id, names in senders.items()
        if other_names.intersection(canonical_secret_name(n) for n in names)
    ]:
        raise ConfigError("; ".join(shared))
    for sender_id, names in senders.items():
        for name in names:
            unreadable = False
            try:
                provider.get(name)
            except Exception:  # noqa: BLE001 - any provider failure is a start-up failure
                unreadable = True
            if unreadable:  # raised after the handler: the provider's error (and the name) is not in __context__
                raise ConfigError(
                    f"{sender_field(sender_id)}: a named secret cannot be read at start-up"
                ) from None
