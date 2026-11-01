"""The registry of read-source kinds: how a configured source (`Config.sources`) is validated and built.

A kind brings its settings model, a factory that wraps a bound fetch into a `Source`, the operation bindings its
calls fit (operation id -> (METHOD, path regex)), and the operation-id prefix that marks a tool as reading it. A
second kind (Prometheus, CloudWatch, PagerDuty) is one entry here and one adapter module; nothing else changes.

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
