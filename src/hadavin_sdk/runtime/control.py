"""Compatibility re-export (one release): ``runtime.control`` was split into ``runtime.config_view`` and ``runtime.stop_gate``.

``KillSwitch`` (the old in-process class) is now ``StopGate``; it takes a ``Limits`` for the durable, audited stop. Import from the
two new modules; this file is removed after the next release."""

from hadavin_sdk.runtime.config_view import (  # noqa: F401
    ConfigConflict,
    ConfigHolder,
    ConfigView,
    FrozenDict,
    FrozenList,
    freeze,
    thaw,
)
from hadavin_sdk.runtime.stop_gate import EffectBlocked, EngageResult, StopGate, StopGateBusy  # noqa: F401
