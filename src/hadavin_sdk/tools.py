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

import base64
import hashlib
import importlib
import ipaddress
import re
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote, quote_plus, urlsplit

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
MIN_SCRUBBED_SECRET = 6  # a shorter secret would shred ordinary text if scrubbed
# Features the manifest names but that arrive in a later phase (design 6.4): refused with the phase.
_DEFERRED_KEYS = {"egress": "Phase 5", "reads_hadavin_store": "Phase 5"}
_METHODS = frozenset(
    {"GET", "POST", "HEAD"}
)  # POST only for read operations; the operation id is the control


class ToolRefused(Exception):
    """A tool broke its own manifest (host, operation, secret, scheme). Becomes `ERROR: ...` for the model."""

    too_large = False  # the reply was over an explicit cap: asking for less may work


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")
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
    # The CA that signs the endpoint (a private cluster's API server): a path relative to the config folder, or
    # the name of a secret holding the PEM. https only; the system CAs are not used when either is set.
    ca_file: str | None = None
    ca_secret_name: str | None = None


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


def host_allowed_over_http(
    host: str, suffixes: tuple[str, ...] = defaults.CLUSTER_SUFFIXES
) -> bool:
    return host.endswith(tuple(suffixes))


# Names that reach this machine or the cloud's instance metadata service, whatever they resolve to.
_FORBIDDEN_NAMES = frozenset({"localhost", "metadata", "metadata.google.internal", "instance-data"})


_NUMERIC_HOST = re.compile(r"(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*", re.IGNORECASE)


def forbidden_host(host: str) -> str | None:
    """Why a manifest host is refused, or None. An IP literal is refused (it names no service and skips the
    allowlist's meaning), and so are loopback and metadata names and anything under `.localhost`."""
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        pass
    else:
        return "an IP literal (use the service's DNS name)"
    if _NUMERIC_HOST.fullmatch(
        host
    ):  # 2130706433, 0x7f.1, 127.1: inet_aton reads these as addresses
        return "a numeric host (an IP address written another way)"
    if host in _FORBIDDEN_NAMES or host.endswith((".localhost", ".internal.metadata")):
        return "a loopback or metadata name"
    return None


def spec_problems(
    spec: ToolSpec,
    tool_modules: list[str],
    suffixes: tuple[str, ...] = defaults.CLUSTER_SUFFIXES,
) -> list[str]:
    """Checks that need nothing from `actions/`: the function reference, hosts, ports and the cluster rule. The
    operation list, the input schema and the agent's `tools_allowed` are checked by the registry."""
    out = []
    module, _, fn = spec.function.partition(":")
    if not fn or module not in tool_modules:
        out.append(f"tool {spec.name}: {spec.function} is outside tool_modules")
    for host in spec.hosts:
        if not host or host != host.lower() or "/" in host or ":" in host or "@" in host:
            out.append(f"tool {spec.name}: host {host!r} must be a bare lowercase hostname")
        elif why := forbidden_host(host):
            out.append(f"tool {spec.name}: host {host!r} is {why}")
    if spec.cluster_http and not all(host_allowed_over_http(h, suffixes) for h in spec.hosts):
        # One tool is either in-cluster (plain http allowed) or outside it (https only); never a mix (design 6.4).
        out.append(
            f"tool {spec.name}: cluster_http needs every host to end in one of {list(suffixes)}"
        )
    if spec.cluster_http and not spec.hosts:
        out.append(f"tool {spec.name}: cluster_http needs hosts")
    if spec.ca_file and spec.ca_secret_name:
        out.append(f"tool {spec.name}: set ca_file or ca_secret_name, not both")
    if (spec.ca_file or spec.ca_secret_name) and spec.cluster_http:
        out.append(f"tool {spec.name}: a CA applies to https; cluster_http is plain http")
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


def module_sha256(module: str) -> str:
    """SHA-256 of a module's source file, found without importing it (a pin is checked before the code runs)."""
    import importlib.util

    try:
        found = importlib.util.find_spec(module)
    except (ImportError, ValueError):
        found = None
    if found is None or not found.origin or not Path(found.origin).is_file():
        raise ConfigError(f"tool module {module} cannot be found")
    return hashlib.sha256(Path(found.origin).read_bytes()).hexdigest()


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


def _request_host(req: urllib.request.Request) -> str:
    """The host urllib's own request parser takes from the URL (what it will connect to)."""
    host = (req.host or "").rsplit("@", 1)[-1]
    if host.startswith("["):
        host = host[1:].split("]", 1)[0]
    elif ":" in host:
        host = host.rsplit(":", 1)[0]
    return host.lower().rstrip(".")


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
        cluster_suffixes: tuple[str, ...] = defaults.CLUSTER_SUFFIXES,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        self._fetch_ceiling = fetch_ceiling
        self._suffixes = tuple(cluster_suffixes)
        self._opener = http_guard.opener_for(ssl_context) if ssl_context is not None else None
        self._opener_direct = (
            http_guard.opener_for(ssl_context, direct=True) if ssl_context is not None else None
        )
        self._lock = (
            threading.Lock()
        )  # the body may outlive its deadline: reads below take a snapshot
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
            with self._lock:
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
        # One parser, one answer: a URL the checks read differently from the HTTP client (backslashes, a `#` before
        # an `@`, percent-encoded hosts, control characters) is refused.
        if re.search(r"[\\\s\x00-\x1f\x7f]", url):
            raise ToolRefused("the URL holds a backslash, whitespace or a control character")
        parts = urlsplit(url)
        if "%" in parts.netloc or "%" in parts.path or "." + "." in parts.path:
            raise ToolRefused("percent-encoding in the host or path, and '..', are refused")
        if not re.fullmatch(binding[1], parts.path or "/"):
            raise ToolRefused(f"path is not the one bound to {operation!r}")
        host = (parts.hostname or "").lower().rstrip(".")
        if parts.scheme != "https" and not (
            parts.scheme == "http"
            and spec.cluster_http
            and host_allowed_over_http(host, self._suffixes)
        ):
            raise ToolRefused("https only (plain http only to in-cluster hosts when cluster_http)")
        if parts.username or parts.password:
            raise ToolRefused("credentials in the URL are refused")
        try:
            egress_check(url, frozenset(spec.hosts))
        except EgressRefused:
            raise ToolRefused(f"host {host!r} is not in this tool's manifest hosts") from None
        self._port(parts, parts.scheme)
        cap = min(max_bytes or spec.max_output_bytes, self._fetch_ceiling)
        req = urllib.request.Request(  # noqa: S310 - scheme and host checked above
            url, data=body, headers=headers or {}, method=method.upper()
        )
        if _request_host(req) != host:
            raise ToolRefused("the HTTP client would read a different host from the one checked")
        # Plain http (loopback or in-cluster) is never handed to an environment proxy.
        direct = host in http_guard.LOOPBACK or parts.scheme == "http"
        if self._opener is not None:  # a pinned CA: its own openers
            opener = self._opener_direct if direct else self._opener
        else:
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
            code = exc.code
            exc.close()
            raise ToolRefused(f"HTTP {code}") from None
        if len(buf) > cap:
            if max_bytes:
                err = ToolRefused(f"the response is larger than {cap} bytes")
                err.too_large = True
                raise err
            del buf[cap:]
            cut = True
        else:
            cut = False
        with self._lock:
            self.fetched = True
            self._digest.update(bytes(buf))
        # A cut reply says so: a silent cut reads as a complete answer.
        return bytes(buf).decode("utf-8", "replace") + (TRUNCATED if cut else "")

    def digest(self) -> str | None:
        with self._lock:
            return self._digest.hexdigest() if self.fetched else None

    def secrets_handed_out(self) -> list[str]:
        with self._lock:
            return list(self.handed_out)


@dataclass(frozen=True)
class ToolOutput:
    text: str  # what the model sees: scrubbed, escaped, redacted, truncated
    sha256: str  # of the raw bytes the tool received (fetch cap), or of its return value if it fetched nothing
    error: bool
    duration_ms: int


_MARKER = re.compile(r"<<(?=\s*(?:end\s+)?tool\s+result)", re.IGNORECASE)


def escape_markers(text: str) -> str:
    """Neutralise anything shaped like our result markers, in any case and spacing, including full-width and
    zero-width spellings (found in the canonical form, rewritten in the original; the rest of the text is left
    as it was written)."""
    return runmap.replace_canonical(text, _MARKER, lambda m: "[[")


def truncate(text: str, limit: int) -> str:
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    return data[:limit].decode("utf-8", "ignore") + TRUNCATED


def _secret_forms(secret: str) -> set[str]:
    raw = secret.encode("utf-8")
    b64 = base64.b64encode(raw).decode()
    return {
        secret,
        quote(secret, safe=""),
        quote_plus(secret),
        b64,
        b64.rstrip("="),
        base64.urlsafe_b64encode(raw).decode(),
        base64.urlsafe_b64encode(raw).decode().rstrip("="),
    }


def prepare_output(
    raw: str,
    mapping: dict[str, str],
    max_bytes: int,
    secrets: list[str] | None = None,
    raw_cap: int = defaults.FETCH_CEILING_BYTES,
) -> str:
    """Cut a runaway return value, scrub handed-out secrets (as they are, URL-quoted and base64), drop NULs,
    escape the result markers, redact with the run's map, then truncate to `max_bytes`."""
    raw = raw.replace("\x00", "\ufffd")
    if len(raw.encode("utf-8")) > raw_cap:
        raw = raw.encode("utf-8")[:raw_cap].decode("utf-8", "ignore") + TRUNCATED
    for secret in secrets or []:
        if len(secret) >= MIN_SCRUBBED_SECRET:
            for form in _secret_forms(secret):
                if form in raw:
                    raw = raw.replace(form, "<SECRET_REDACTED>")
                elif not raw.isascii() and form in (canon := runmap.canonical(raw)):
                    # the secret hides behind invisible or compatibility characters: use the folded text
                    raw = canon.replace(form, "<SECRET_REDACTED>")
    return truncate(runmap.redact_untrusted(escape_markers(raw), mapping), max_bytes)


def error_reason(exc: BaseException) -> str:
    """A short reason for the model. Network and driver errors carry hosts and users: their type says enough."""
    if isinstance(exc, ToolRefused):
        return str(exc)[:200]
    if isinstance(exc, OSError | urllib.error.URLError):
        return f"{type(exc).__name__} (network error)"
    return f"{type(exc).__name__}: {str(exc)[:160]}"


class ToolBox:
    """The tools of one deployment. `invoke` never raises for a failing tool (the model gets `ERROR: ...`); it
    raises `runmap.RedactionError` when redaction fails, because then nothing may be sent.

    What the box defends against: a MODEL that misuses a tool (wrong host, wrong operation, a secret it was not
    given, a runaway reply). It does not defend against a hostile tool AUTHOR: a tool body is code running in this
    process, so "read-only" means "as safe as the reviewed tool module". Pin the modules with
    `Config.tool_module_hashes` (required in pilot and prod) and review them like the rest of the release."""

    def __init__(
        self,
        specs: dict[str, ToolSpec],
        fns: dict[str, Callable[..., str]],
        *,
        timeout_s: float,
        secret_resolver_for: Callable[[ToolSpec], Callable[[str], str]] | None = None,
        arg_errors: Callable[[dict[str, Any], dict[str, Any]], list[str]] | None = None,
        bindings: dict[str, Binding] | None = None,
        fetch_ceiling: int = defaults.FETCH_CEILING_BYTES,
        https_ports: tuple[int, ...] = defaults.HTTPS_PORTS,
        cluster_ports: tuple[int, ...] = defaults.CLUSTER_PORTS,
        cluster_suffixes: tuple[str, ...] = defaults.CLUSTER_SUFFIXES,
        stored_kinds: frozenset[str] | None = None,
        max_abandoned: int = defaults.MAX_ABANDONED_TOOL_THREADS,
        ssl_context_for: Callable[[ToolSpec], ssl.SSLContext | None] | None = None,
    ) -> None:
        self._limits = {
            "fetch_ceiling": fetch_ceiling,
            "https_ports": https_ports,
            "cluster_ports": cluster_ports,
            "cluster_suffixes": cluster_suffixes,
        }
        self._fetch_ceiling = fetch_ceiling
        self._kinds = stored_kinds
        self.specs, self._fns, self.timeout_s = specs, fns, timeout_s
        self._secrets_for, self._arg_errors = secret_resolver_for, arg_errors
        self._ssl_for = ssl_context_for
        self._bindings = dict(bindings or {})
        self._max_abandoned = max_abandoned
        self._abandoned: set[threading.Thread] = set()
        self._abandoned_lock = threading.Lock()

    def names(self) -> set[str]:
        return set(self.specs)

    def abandoned(self) -> int:
        """Tool bodies still running after their deadline."""
        with self._abandoned_lock:
            self._abandoned = {t for t in self._abandoned if t.is_alive()}
            return len(self._abandoned)

    def _call(self, name: str, restored: dict[str, Any], ctx: ToolContext) -> str:
        """The tool body under one total deadline (`tool_timeout_s`): it, its secret reads and its fetches share
        it. A body that does not return is abandoned (its thread ends at its next fetch or secret read); too many
        abandoned bodies and further calls are refused."""
        if self.abandoned() >= self._max_abandoned:
            raise ToolRefused("too many earlier tool calls are still running past their deadline")
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
        worker = threading.Thread(target=work, daemon=True, name="hadavin-tool")
        worker.start()
        if not done.wait(self.timeout_s):
            with self._abandoned_lock:
                self._abandoned.add(worker)
            raise ToolRefused("tool timed out")
        if "error" in box:
            err = box["error"]
            if isinstance(err, Exception):
                raise err
            # SystemExit, KeyboardInterrupt, GeneratorExit raised INSIDE the tool body's thread: not this
            # process's exit or interrupt, just a failed tool.
            raise ToolRefused(f"the tool raised {type(err).__name__}")
        return box["value"]

    def invoke(self, name: str, args: dict[str, Any], mapping: dict[str, str]) -> ToolOutput:
        spec = self.specs[name]
        resolver = self._secrets_for(spec) if self._secrets_for else None
        ssl_ctx = self._ssl_for(spec) if self._ssl_for else None
        ctx = ToolContext(
            spec, self.timeout_s, resolver, self._bindings, ssl_context=ssl_ctx, **self._limits
        )
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
        text = prepare_output(
            raw, mapping, spec.max_output_bytes, ctx.secrets_handed_out(), self._fetch_ceiling
        )
        return ToolOutput(text, digest, error, int((time.monotonic() - started) * 1000))
