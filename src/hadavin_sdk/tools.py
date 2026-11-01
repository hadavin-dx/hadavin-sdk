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
import re
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard import http as http_guard
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.egress import EgressRefused, egress_check

DEFAULT_MAX_OUTPUT_BYTES = defaults.MAX_OUTPUT_BYTES  # the manifest field's default
Binding = tuple[str, str]  # (METHOD, regex the URL path must fully match)
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
    # Tuples: a frozen model with list fields can still be mutated in place by a tool body.
    operations: tuple[str, ...] = ()
    hosts: tuple[str, ...] = ()
    secret_names: tuple[str, ...] = ()
    max_output_bytes: int = Field(default=DEFAULT_MAX_OUTPUT_BYTES, gt=0)
    cluster_http: bool = False
    # Settings the tool's own code reads (validated there, e.g. a source's `KubernetesSettings`): endpoints and
    # limits belong here, never in the tool module.
    options: dict[str, Any] = {}
    ports: tuple[int, ...] = ()  # empty: 443 for https, the in-cluster set for plain http


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
    """Checks that need nothing from `actions/`: the function reference, hosts, ports and the cluster rule. The
    operation list, the input schema and the agent's `tools_allowed` are checked by the registry."""
    out = []
    module, _, fn = spec.function.partition(":")
    if not fn or module not in tool_modules:
        out.append(f"tool {spec.name}: {spec.function} is outside tool_modules")
    for host in spec.hosts:
        if not host or host != host.lower() or "/" in host or ":" in host or "@" in host:
            out.append(f"tool {spec.name}: host {host!r} must be a bare lowercase hostname")
    if spec.cluster_http and not all(host_allowed_over_http(h) for h in spec.hosts):
        # One tool is either in-cluster (plain http allowed) or outside it (https only); never a mix (design 6.4).
        out.append(
            f"tool {spec.name}: cluster_http needs every host to end in .svc.cluster.local or .svc"
        )
    if spec.cluster_http and not spec.hosts:
        out.append(f"tool {spec.name}: cluster_http needs hosts")
    if bad := [p for p in spec.ports if not 0 < p < 65536]:
        out.append(f"tool {spec.name}: ports {bad} are not valid")
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


def read_operations(tool_modules: list[str]) -> dict[str, Binding]:
    """The union of `READ_OPERATIONS` the tool modules declare: operation id -> (METHOD, path regex). The read
    list a manifest's `operations` must stay inside, and the shape each call must fit: an operation id is not a
    label, it is bound in code to one method and one path pattern. A module without one allows no operation."""
    out: dict[str, Binding] = {}
    for module in tool_modules:
        try:
            declared = getattr(importlib.import_module(module), "READ_OPERATIONS", {})
        except ImportError as exc:
            raise ConfigError(f"tool_modules: {module} cannot be imported") from exc
        if not isinstance(declared, dict):
            raise ConfigError(
                f"tool_modules: {module}.READ_OPERATIONS must map each operation id to (METHOD, path regex)"
            )
        for op, binding in declared.items():
            try:
                method, pattern = binding
                re.compile(pattern)
            except (TypeError, ValueError, re.error):
                raise ConfigError(
                    f"{module}: operation {op!r} has no valid (METHOD, regex)"
                ) from None
            if method not in _METHODS:
                raise ConfigError(f"{module}: operation {op!r} uses method {method!r}")
            if out.get(op, (method, pattern)) != (method, pattern):
                raise ConfigError(
                    f"{module}: operation {op!r} is already bound differently by another module"
                )
            out[op] = (method, pattern)
    return out


class ToolContext:
    """What a tool may touch. Built per call, so the digest, the deadline and the secrets handed out are per call.
    The secret resolver is held by a closure, not an attribute: a tool can only ask for the manifest's names."""

    def __init__(
        self,
        spec: ToolSpec,
        timeout_s: float,
        secret_resolver: Callable[[str], str] | None = None,
        bindings: dict[str, Binding] | None = None,
        *,
        fetch_ceiling: int = defaults.FETCH_CEILING_BYTES,
        https_ports: tuple[int, ...] = defaults.HTTPS_PORTS,
        cluster_ports: tuple[int, ...] = defaults.CLUSTER_PORTS,
    ) -> None:
        self._fetch_ceiling = fetch_ceiling
        self._https_ports, self._cluster_ports = frozenset(https_ports), frozenset(cluster_ports)
        # A deep copy: a tool body that edits `ctx.spec` edits its own copy, never the manifest the next call uses.
        # NOTE the ceiling: a tool body is trusted code running in this process (it can reach the closure that holds
        # the secret reader, import anything, open sockets). The manifest limits what the tool is *given*; the
        # in-process boundary is code review of tool modules and the egress proxy (K7), not Python.
        self.spec, self.timeout_s = spec.model_copy(deep=True), timeout_s
        self.deadline = time.monotonic() + timeout_s  # the whole call, not one socket operation
        self.bindings = dict(bindings or {})
        self.fetched = False
        self.handed_out: list[str] = []
        self._digest = hashlib.sha256()

        def secret(name: str) -> str:
            if name not in spec.secret_names:
                raise ToolRefused(f"secret {name!r} is not named in the manifest")
            if secret_resolver is None:
                raise ToolRefused("no secret resolver wired")
            self._remaining()
            value = secret_resolver(name)
            self.handed_out.append(value)
            return value

        self.secret = secret

    def _remaining(self) -> float:
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise ToolRefused("tool timed out")
        return left

    def _port(self, parts, scheme: str) -> int:
        try:
            port = parts.port or (443 if scheme == "https" else 80)
        except ValueError:
            raise ToolRefused("the URL's port is not valid") from None
        allowed = set(self.spec.ports) or (
            self._cluster_ports if scheme == "http" else self._https_ports
        )
        if port not in allowed:
            raise ToolRefused(f"port {port} is not allowed for this tool")
        return port

    def fetch(
        self,
        method: str,
        url: str,
        *,
        operation: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        max_bytes: int | None = None,
    ) -> str:
        """One read. Refused unless the operation, its bound method and path, the host, the port and the scheme
        are on the manifest; never follows a redirect; the whole call shares one deadline; the body is cut at
        `max_bytes` (default the manifest's `max_output_bytes`; an explicit larger cap is refused past
        the configured ceiling, and a response over an explicit cap is refused, never silently cut)."""
        spec = self.spec
        if operation not in spec.operations:
            raise ToolRefused(f"operation {operation!r} is not on the manifest's read list")
        binding = self.bindings.get(operation)
        if binding is None:
            raise ToolRefused(f"operation {operation!r} has no bound method and path")
        if method.upper() not in _METHODS or method.upper() != binding[0]:
            raise ToolRefused(f"method {method!r} is not the one bound to {operation!r}")
        parts = urlsplit(url)
        if not re.fullmatch(binding[1], parts.path or "/"):
            raise ToolRefused(f"path is not the one bound to {operation!r}")
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
        self._port(parts, parts.scheme)
        cap = min(max_bytes or spec.max_output_bytes, self._fetch_ceiling)
        req = urllib.request.Request(  # noqa: S310 - scheme and host checked above
            url, data=body, headers=headers or {}, method=method.upper()
        )
        # Plain http (loopback or in-cluster) is never handed to an environment proxy.
        direct = host in http_guard.LOOPBACK or parts.scheme == "http"
        opener = http_guard.LOCAL_OPENER if direct else http_guard.OPENER
        buf = bytearray()
        try:
            with opener.open(req, timeout=min(self.timeout_s, self._remaining())) as resp:  # nosec B310
                while len(buf) <= cap:
                    self._remaining()
                    chunk = resp.read(min(8192, cap + 1 - len(buf)))
                    if not chunk:
                        break
                    buf += chunk
        except urllib.error.HTTPError as exc:
            raise ToolRefused(f"HTTP {exc.code}") from None
        if len(buf) > cap:
            if max_bytes:
                raise ToolRefused(f"the response is larger than {cap} bytes")
            del buf[cap:]
            cut = True
        else:
            cut = False
        self.fetched = True
        self._digest.update(bytes(buf))
        # A cut reply says so: a silent cut reads as a complete answer.
        return bytes(buf).decode("utf-8", "replace") + (TRUNCATED if cut else "")

    def digest(self) -> str | None:
        return self._digest.hexdigest() if self.fetched else None


@dataclass(frozen=True)
class ToolOutput:
    text: str  # what the model sees: scrubbed, escaped, redacted, truncated
    sha256: str  # of the raw bytes the tool received (fetch cap), or of its return value if it fetched nothing
    error: bool
    duration_ms: int


_MARKER = re.compile(r"<<(?=\s*(?:end\s+)?tool\s+result)", re.IGNORECASE)


def escape_markers(text: str) -> str:
    """Neutralise anything shaped like our result markers, in any case and spacing. Callers pass canonical text
    (`runmap.canonical`), so full-width and zero-width variants are already plain."""
    return _MARKER.sub("[[", text)


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
    return truncate(
        runmap.redact_untrusted(escape_markers(runmap.canonical(raw)), mapping), max_bytes
    )


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
        bindings: dict[str, Binding] | None = None,
        fetch_ceiling: int = defaults.FETCH_CEILING_BYTES,
        https_ports: tuple[int, ...] = defaults.HTTPS_PORTS,
        cluster_ports: tuple[int, ...] = defaults.CLUSTER_PORTS,
        stored_kinds: frozenset[str] | None = None,
    ) -> None:
        self._limits = {
            "fetch_ceiling": fetch_ceiling,
            "https_ports": https_ports,
            "cluster_ports": cluster_ports,
        }
        self._kinds = stored_kinds
        self.specs, self._fns, self.timeout_s = specs, fns, timeout_s
        self._secrets, self._arg_errors = secret_resolver, arg_errors
        self._bindings = dict(bindings or {})

    def names(self) -> set[str]:
        return set(self.specs)

    def _call(self, name: str, restored: dict[str, Any], ctx: ToolContext) -> str:
        """The tool body under one total deadline (`tool_timeout_s`): it, its secret reads and its fetches share
        it. A body that does not return is abandoned (its thread ends at its next fetch or secret read)."""
        box: dict[str, Any] = {}
        done = threading.Event()

        def work() -> None:
            try:
                box["value"] = str(self._fns[name](restored, ctx))
            except BaseException as exc:  # noqa: BLE001 - handed to the caller below
                box["error"] = exc
            finally:
                done.set()

        # A daemon thread: a body that never returns (sleep, a lock, a busy loop) must not keep the process alive
        # at exit, which a pool's non-daemon worker would.
        threading.Thread(target=work, daemon=True, name="hadavin-tool").start()
        if not done.wait(self.timeout_s):
            raise ToolRefused("tool timed out")
        if "error" in box:
            raise box["error"]
        return box["value"]

    def invoke(self, name: str, args: dict[str, Any], mapping: dict[str, str]) -> ToolOutput:
        spec = self.specs[name]
        ctx = ToolContext(spec, self.timeout_s, self._secrets, self._bindings, **self._limits)
        started = time.monotonic()
        error = False
        try:
            restored = runmap.restore_value(args, mapping, self._kinds)
            if runmap.has_placeholder(restored):
                raise ToolRefused("an argument could not be resolved")
            if self._arg_errors is not None and (
                bad := self._arg_errors(spec.input_schema, restored)
            ):
                raise ToolRefused("arguments invalid: " + ", ".join(bad)[:200])
            raw = self._call(name, restored, ctx)
        except Exception as exc:  # noqa: BLE001 - a failing tool becomes a result the model can react to
            error = True
            raw = ERROR_PREFIX + error_reason(exc)
        digest = ctx.digest() or hashlib.sha256(raw.encode("utf-8")).hexdigest()
        text = prepare_output(raw, mapping, spec.max_output_bytes, ctx.handed_out)
        return ToolOutput(text, digest, error, int((time.monotonic() - started) * 1000))
