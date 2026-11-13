"""The registry of read-source kinds: how a configured source (`Config.sources`) is validated and built.

A kind brings its settings model, a factory that wraps a bound fetch into a `Source`, the operation bindings its
calls fit (operation id -> (METHOD, path regex)), and the operation-id prefix that marks a tool as reading it. A
second kind (Prometheus, CloudWatch, PagerDuty) is one entry here and one adapter module. That is an SDK edit
(the registry is a module-level dict, not a plugin point); a client needing a second source before then asks
for it under trigger K5-ITO, and the Kubernetes adapter stays the only built one until a client does.

Neutral protocol: plain Python registry.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from hadavin_sdk.sources import Source
from hadavin_sdk.sources.kubernetes import READ_OPERATIONS, KubernetesSettings, KubernetesSource


@dataclass(frozen=True)
class SourceKind:
    settings: type[BaseModel]
    build: Callable[
        [Any, Callable[..., str]], Source
    ]  # (validated settings, bound fetch) -> source
    operations: Mapping[str, tuple[str, str]]
    operation_prefix: (
        str  # a tool listing an operation with this prefix reads a source of this kind
    )
    endpoint: Callable[
        [Any], str
    ]  # the settings' API URL: its host is what a tool's `hosts` must cover


KINDS: dict[str, SourceKind] = {
    "kubernetes": SourceKind(
        settings=KubernetesSettings,
        build=lambda settings, fetch: KubernetesSource(fetch, settings),
        operations=READ_OPERATIONS,
        operation_prefix="k8s.",
        endpoint=lambda settings: settings.api_url,
    ),
}


def source_endpoint(source: Any) -> str:
    """The API url of a configured source (`Config.sources` entry): its kind's `endpoint` applied to
    the validated settings. The one place this is worked out; the app reads its host, the mode
    banner reads the whole url."""
    kind = KINDS[source.kind]
    return kind.endpoint(kind.settings(**source.settings))


def register(name: str, kind: SourceKind) -> None:
    """Add a kind. Two kinds whose operation prefixes overlap (`k8s.` and `k8s.metrics.`) would both claim a tool's
    operation: refused here, not at the first run."""
    for other_name, other in KINDS.items():
        if other_name != name and (
            kind.operation_prefix.startswith(other.operation_prefix)
            or other.operation_prefix.startswith(kind.operation_prefix)
        ):
            raise ValueError(
                f"source kind {name!r}: prefix {kind.operation_prefix!r} overlaps {other_name!r}"
            )
    KINDS[name] = kind
