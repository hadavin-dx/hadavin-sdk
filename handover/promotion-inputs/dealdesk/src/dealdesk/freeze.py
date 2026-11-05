"""Read-only views for configuration (matrix, policy). `freeze` returns nested MappingProxyType / tuple copies; `thaw` returns plain JSON-able
copies (for hashing). `Sealed` stops rebinding of an engine object's attributes after construction. HONEST LIMIT: this is protection against ordinary
assignment and in-place edits, not against hostile code in the same process (which can call `object.__setattr__`); that boundary is a process or
service boundary in a client build (docs: runbook.md, README.md)."""

from __future__ import annotations

from types import MappingProxyType


def freeze(obj):
    if isinstance(obj, dict | MappingProxyType):
        return MappingProxyType({k: freeze(v) for k, v in obj.items()})
    if isinstance(obj, list | tuple):
        return tuple(freeze(v) for v in obj)
    return obj


def thaw(obj):
    if isinstance(obj, dict | MappingProxyType):
        return {k: thaw(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [thaw(v) for v in obj]
    return obj


class Sealed:
    """Call `self._seal()` at the end of __init__; afterwards `obj.attr = value` raises."""

    def _seal(self) -> None:
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name, value) -> None:
        if self.__dict__.get("_sealed"):
            raise AttributeError(f"{type(self).__name__} is sealed: {name} cannot be rebound")
        object.__setattr__(self, name, value)
