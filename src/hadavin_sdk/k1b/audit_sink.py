"""K1b audit: events go to the configured sink (``local_dir`` or ``chain``) through ``write_intent`` only.

``write_intent`` raises ``AuditUnavailable``; a failed append is a failed command, even in report-only mode.
A ``chain`` over the ``memory`` store keeps events only until the process exits: ``build_audit`` returns a warning
and carries on (lite is report-only).
"""

from __future__ import annotations

import getpass
from typing import Any

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.backends import make, platform_secrets
from hadavin_sdk.config import Config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import AuditEvent

DOMAIN = "k1b"
MEMORY_WARNING = (
    "audit events are lost at exit (chain over the memory store); lite is report-only, continuing"
)


class K1bAudit:
    def __init__(self, sink: AuditSink, principal: str | None = None) -> None:
        self.sink = sink
        self.principal = principal or _os_user()

    def emit(
        self,
        operation: str,
        run_id: str,
        *,
        object_ref: str | None = None,
        inputs_hash: str | None = None,
        decision: str | None = None,
        rule_id: str | None = None,
        result: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """Write one event (fresh ``event_id`` each time). Raises ``AuditUnavailable``."""
        self.sink.write_intent(
            AuditEvent(
                run_id=run_id,
                domain=DOMAIN,
                operation=operation,
                principal=self.principal,
                source="cli",
                object_ref=object_ref,
                inputs_hash=inputs_hash,
                decision=decision,
                rule_id=rule_id,
                result=result,
                error_code=error_code,
            )
        )


def _os_user() -> str:
    try:
        return getpass.getuser()
    except Exception:  # noqa: BLE001 - no login name available (containers): still audit, as "unknown"
        return "unknown"


def build_audit(cfg: Config, secrets: Any) -> tuple[K1bAudit, list[str]]:
    """The K1b audit for ``cfg.backends.audit`` and any warnings to show the operator."""
    b = cfg.backends
    if b.audit.kind not in ("local_dir", "chain"):
        raise ConfigError(f"K1b audit supports local_dir and chain, not {b.audit.kind!r}")
    if b.audit.kind == "local_dir":  # needs no store, signer or anchor
        platform_secrets.check(secrets, [b.audit], set())
        return K1bAudit(make("audit", b.audit, secrets)), []
    platform_secrets.check(secrets, [b.signer, b.anchor, b.store, b.audit], set())
    signer = make("signer", b.signer, secrets)
    anchor = make("anchor", b.anchor, secrets)
    store = make("store", b.store, secrets)
    sink = make("audit", b.audit, secrets, store=store, signer=signer, anchor=anchor)
    return K1bAudit(sink), [MEMORY_WARNING] if b.store.kind == "memory" else []
