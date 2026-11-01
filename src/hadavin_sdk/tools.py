"""Read-only tools (K5): the manifest, ``ToolContext`` and the box that runs one call.

A tool is a function ``fn(args: dict, ctx: ToolContext) -> str`` named in ``tools/<agent>.yaml`` and resolved
only from ``tool_modules``. It can read through ``ctx.fetch`` (https, or plain http to in-cluster hosts only
when the manifest says ``cluster_http``; the host must be in the manifest, no redirects, a timeout, a size cap,
and the operation id must be on the manifest's read list) and read the secrets the manifest names, nothing else.

This module imports nothing from ``actions/`` and no secret holder: the secret resolver and the argument check
are injected by ``app.py`` (tests/test_repo_rules.py scans the transitive imports).

Neutral protocol: HTTP/1.1 over the standard library.
"""

from __future__ import annotations

import hashlib
import importlib
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard import http as http_guard
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.egress import EgressRefused, egress_check

DEFAULT_MAX_OUTPUT_BYTES = 16384
# Hooks.tools callables given directly (replay, tests) have no manifest: they get the K1b replay cap.
LEGACY_MAX_OUTPUT_BYTES = 20_000
END_MARKER = "<<END TOOL RESULT>>"
START_MARKER = "<<TOOL RESULT"
TRUNCATED = "\n[truncated]"
ERROR_PREFIX = "ERROR: "
CLUSTER_SUFFIXES = (".svc.cluster.local", ".svc")
# Features the manifest names but that arrive in a later phase (design 6.4): refused with the phase.
_DEFERRED_KEYS = {"egress": "Phase 5", "reads_hadavin_store": "Phase 5"}
_METHODS = frozenset(
    {"GET", "POST", "HEAD"}
)  # POST only for read operations; the operation id is the control


class ToolRefused(Exception):
    """A tool broke its own manifest (host, operation, secret, scheme). Becomes `ERROR: ...` for the model."""


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(pattern=r"[a-z][a-z0-9_]{0,39}")
    function: str  # "module:function", the module must be in config.tool_modules
    description: str
    input_schema: dict[str, Any]
    side_effect: Literal["none"]
    operations: list[str] = []
    hosts: list[str] = []
    secret_names: list[str] = []
    max_output_bytes: int = Field(default=DEFAULT_MAX_OUTPUT_BYTES, gt=0)
    cluster_http: bool = False


def parse_manifest(raw: Any, where: str) -> list[ToolSpec]:
    """`tools/<agent>.yaml` is a list of entries. Every problem is a ConfigError naming the file."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ConfigError(f"{where}: expected a list of tools")
    out: list[ToolSpec] = []
    for entry in raw:
        if isinstance(entry, dict):
            for key, phase in _DEFERRED_KEYS.items():
                if key in entry:
                    raise ConfigError(f"{where}: key {key!r} is not available until {phase}")
        try:
            out.append(
                ToolSpec(**entry) if isinstance(entry, dict) else ToolSpec.model_validate(entry)
            )
        except ValidationError as exc:
            fields = ", ".join(".".join(str(p) for p in e["loc"]) or "?" for e in exc.errors())
            raise ConfigError(f"{where}: invalid tool entry ({fields})") from None
    names = [t.name for t in out]
    if dup := sorted({n for n in names if names.count(n) > 1}):
        raise ConfigError(f"{where}: duplicate tool {', '.join(dup)}")
    return out


def host_allowed_over_http(host: str) -> bool:
    return host.endswith(CLUSTER_SUFFIXES)


def spec_problems(spec: ToolSpec, tool_modules: list[str]) -> list[str]:
    """Checks that need nothing from `actions/`: the function reference, hosts and the cluster rule. The
    operation list, the input schema and the agent's `tools_allowed` are checked by the registry."""
    out = []
    module, _, fn = spec.function.partition(":")
    if not fn or module not in tool_modules:
        out.append(f"tool {spec.name}: {spec.function} is outside tool_modules")
    for host in spec.hosts:
        if not host or host != host.lower() or "/" in host or ":" in host or "@" in host:
            out.append(f"tool {spec.name}: host {host!r} must be a bare lowercase hostname")
    if spec.cluster_http and not any(host_allowed_over_http(h) for h in spec.hosts):
        out.append(
            f"tool {spec.name}: cluster_http needs a host ending in .svc.cluster.local or .svc"
        )
    return out


def resolve_function(spec: ToolSpec, tool_modules: list[str]) -> Callable[..., str]:
    module, _, name = spec.function.partition(":")
    if not name or module not in tool_modules:
        raise ConfigError(f"tool {spec.name}: {spec.function} is outside tool_modules")
    try:
        fn = getattr(importlib.import_module(module), name)
    except (ImportError, AttributeError) as exc:
        raise ConfigError(f"tool {spec.name}: {spec.function} cannot be loaded") from exc
    if not callable(fn):
        raise ConfigError(f"tool {spec.name}: {spec.function} is not callable")
    return fn


def read_operations(tool_modules: list[str]) -> set[str]:
    """The union of `READ_OPERATIONS` the tool modules declare: the read list a manifest's `operations` must
    stay inside. A module without one allows no operation."""
    out: set[str] = set()
    for module in tool_modules:
        try:
            out |= set(getattr(importlib.import_module(module), "READ_OPERATIONS", ()))
        except ImportError as exc:
            raise ConfigError(f"tool_modules: {module} cannot be imported") from exc
    return out


@dataclass
class ToolContext:
    """What a tool may touch. Built per call, so the digest and the secrets handed out are per call."""

    spec: ToolSpec
    timeout_s: float
    secret_resolver: Callable[[str], str] | None = None
    _digest: Any = field(default_factory=hashlib.sha256, repr=False)
    fetched: bool = False
    handed_out: list[str] = field(default_factory=list, repr=False)

    def secret(self, name: str) -> str:
        if name not in self.spec.secret_names:
            raise ToolRefused(f"secret {name!r} is not named in the manifest")
        if self.secret_resolver is None:
            raise ToolRefused("no secret resolver wired")
        value = self.secret_resolver(name)
        self.handed_out.append(value)
        return value

    def fetch(
        self,
        method: str,
        url: str,
        *,
        operation: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> str:
        """One read. Refused unless the operation, host and scheme are on the manifest; never follows a
        redirect; the body is cut at `max_output_bytes` and the digest covers the bytes received."""
        spec = self.spec
        if operation not in spec.operations:
            raise ToolRefused(f"operation {operation!r} is not on the manifest's read list")
        if method.upper() not in _METHODS:
            raise ToolRefused(f"method {method!r} is not allowed")
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
        if parts.scheme != "https" and not (
            parts.scheme == "http" and spec.cluster_http and host_allowed_over_http(host)
        ):
            raise ToolRefused("https only (plain http only to in-cluster hosts when cluster_http)")
        if parts.username or parts.password:
            raise ToolRefused("credentials in the URL are refused")
        try:
            egress_check(url, frozenset(spec.hosts))
        except EgressRefused as exc:
            raise ToolRefused(str(exc)) from None
        req = urllib.request.Request(  # noqa: S310 - scheme and host checked above
            url, data=body, headers=headers or {}, method=method.upper()
        )
        opener = http_guard.LOCAL_OPENER if host in http_guard.LOOPBACK else http_guard.OPENER
        try:
            with opener.open(req, timeout=self.timeout_s) as resp:  # nosec B310
                raw = resp.read(spec.max_output_bytes + 1)
        except urllib.error.HTTPError as exc:
            raise ToolRefused(f"HTTP {exc.code}") from None
        self.fetched = True
        raw = raw[: spec.max_output_bytes]
        self._digest.update(raw)
        return raw.decode("utf-8", "replace")

    def digest(self) -> str | None:
        return self._digest.hexdigest() if self.fetched else None


@dataclass(frozen=True)
class ToolOutput:
    text: str  # what the model sees: scrubbed, escaped, redacted, truncated
    sha256: str  # of the raw bytes the tool received (fetch cap), or of its return value if it fetched nothing
    error: bool
    duration_ms: int


def escape_markers(text: str) -> str:
    return text.replace(END_MARKER, "[END TOOL RESULT]").replace(START_MARKER, "[TOOL RESULT")


def truncate(text: str, limit: int) -> str:
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    return data[:limit].decode("utf-8", "ignore") + TRUNCATED


def prepare_output(
    raw: str, mapping: dict[str, str], max_bytes: int, secrets: list[str] | None = None
) -> str:
    """Scrub handed-out secrets, escape the end marker, redact with the run's map, then truncate."""
    for secret in secrets or []:
        if secret:
            raw = raw.replace(secret, "<SECRET_REDACTED>")
    return truncate(runmap.redact_text(escape_markers(raw), mapping), max_bytes)


def error_reason(exc: BaseException) -> str:
    """A short reason for the model. Network and driver errors carry hosts and users: their type says enough."""
    if isinstance(exc, ToolRefused):
        return str(exc)[:200]
    if isinstance(exc, OSError | urllib.error.URLError):
        return f"{type(exc).__name__} (network error)"
    return f"{type(exc).__name__}: {str(exc)[:160]}"


class ToolBox:
    """The tools of one deployment. `invoke` never raises for a failing tool (the model gets `ERROR: ...`); it
    raises `runmap.RedactionError` when redaction fails, because then nothing may be sent."""

    def __init__(
        self,
        specs: dict[str, ToolSpec],
        fns: dict[str, Callable[..., str]],
        *,
        timeout_s: float,
        secret_resolver: Callable[[str], str] | None = None,
        arg_errors: Callable[[dict[str, Any], dict[str, Any]], list[str]] | None = None,
    ) -> None:
        self.specs, self._fns, self.timeout_s = specs, fns, timeout_s
        self._secrets, self._arg_errors = secret_resolver, arg_errors

    def names(self) -> set[str]:
        return set(self.specs)

    def invoke(self, name: str, args: dict[str, Any], mapping: dict[str, str]) -> ToolOutput:
        spec = self.specs[name]
        ctx = ToolContext(spec, self.timeout_s, self._secrets)
        started = time.monotonic()
        error = False
        try:
            restored = runmap.restore_value(args, mapping)
            if runmap.has_placeholder(restored):
                raise ToolRefused("an argument could not be resolved")
            if self._arg_errors is not None and (
                bad := self._arg_errors(spec.input_schema, restored)
            ):
                raise ToolRefused("arguments invalid: " + ", ".join(bad)[:200])
            raw = str(self._fns[name](restored, ctx))
        except Exception as exc:  # noqa: BLE001 - a failing tool becomes a result the model can react to
            error = True
            raw = ERROR_PREFIX + error_reason(exc)
        digest = ctx.digest() or hashlib.sha256(raw.encode("utf-8")).hexdigest()
        text = prepare_output(raw, mapping, spec.max_output_bytes, ctx.handed_out)
        return ToolOutput(text, digest, error, int((time.monotonic() - started) * 1000))
