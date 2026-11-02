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

import ast
import base64
import hashlib
import html
import importlib
import ipaddress
import json
import re
import ssl
import sys
import threading
import time
import types
import urllib.error
import urllib.request
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote, quote_plus, unquote, urlsplit, urlunsplit

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
MIN_SCRUBBED_SECRET = (
    6  # a shorter secret would shred ordinary text if scrubbed: a tool is refused one
)
MIN_REDACTION_WINDOW = 4096  # redaction always sees at least this much, whatever the tool's cap
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
    # A regex for the generated suffix of a name this tool's results show (a pod's `-7f9d8c6b4-xk2lp`): the
    # ONLY way a proposal may name the front of a longer name (grounding is a whole-token match otherwise).
    generated_suffix: str = ""


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
_FORBIDDEN_NAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
        "metadata",
        "metadata.goog",
        "metadata.google.internal",
        "instance-data",
        "instance-data.ec2.internal",
    }
)


_NUMERIC_HOST = re.compile(r"(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*", re.IGNORECASE)


def forbidden_host(host: str) -> str | None:
    """Why a manifest host is refused, or None. An IP literal is refused (it names no service and skips the
    allowlist's meaning), and so are loopback and metadata names and anything under `.localhost`."""
    host = host.rstrip(".")  # `localhost.` is `localhost`
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        pass
    else:
        return "an IP literal (use the service's DNS name)"
    if not re.fullmatch(r"[a-z0-9.\-]+", host):
        return "not a plain lowercase ASCII hostname"
    if _NUMERIC_HOST.fullmatch(
        host
    ):  # 2130706433, 0x7f.1, 127.1: inet_aton reads these as addresses
        return "a numeric host (an IP address written another way)"
    if (
        host in _FORBIDDEN_NAMES
        or host.endswith((".localhost", ".metadata.google.internal"))
        or host.split(".")[0]
        in (
            "metadata",
            "instance-data",
        )
    ):
        return "a loopback or metadata name"
    return None


# `generated_suffix` is a deliberately tiny language, so no suffix can backtrack exponentially or match any
# longer name: literal characters, `\\.` and `\\-`, and character classes with a BOUNDED repeat (`{5}` or
# `{5,10}`). No `*`, `+`, `?`, group, alternation or lookaround. Time is polynomial, not linear: each VARIABLE
# repeat (`{lo,hi}` with lo != hi) can multiply the worst case by up to 64, so at most `_SUFFIX_MAX_VARIABLE` are
# allowed (a fixed `{5}` adds nothing).
_SUFFIX = re.compile(
    r"(?:[A-Za-z0-9_\-]|\\[.\-]|\[[A-Za-z0-9_\-]{1,40}\](?:\{[0-9]{1,2}(?:,[0-9]{1,2})?\})?)+"
)
_SUFFIX_MAX_LEN, _SUFFIX_MAX_REPEAT, _SUFFIX_MAX_VARIABLE = 200, 64, 2
_VARIABLE_REPEAT = re.compile(r"\{([0-9]+),([0-9]+)\}")


def suffix_problem(suffix: str) -> str | None:
    if len(suffix) > _SUFFIX_MAX_LEN:
        return f"is longer than {_SUFFIX_MAX_LEN} characters"
    if not _SUFFIX.fullmatch(suffix):
        return "uses more than literals and bounded character classes (no *, +, ?, groups or alternation)"
    for lo, hi in re.findall(r"\{([0-9]+)(?:,([0-9]+))?\}", suffix):
        if int(hi or lo) > _SUFFIX_MAX_REPEAT or int(lo) > int(hi or lo):
            return f"has a repeat that is not between 0 and {_SUFFIX_MAX_REPEAT} or runs backwards"
    if sum(1 for lo, hi in _VARIABLE_REPEAT.findall(suffix) if lo != hi) > _SUFFIX_MAX_VARIABLE:
        return f"has more than {_SUFFIX_MAX_VARIABLE} variable-length repeats (the match would take polynomial time)"
    try:
        re.compile(suffix)
    except re.error:
        return "is not a valid pattern"
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
    if spec.generated_suffix and (why := suffix_problem(spec.generated_suffix)):
        out.append(f"tool {spec.name}: generated_suffix {why}")
    return out


def _normalised(data: bytes) -> bytes:
    """Line endings folded to LF, so a checkout with CRLF (Windows) and one with LF carry the same pin."""
    return data.replace(b"\r\n", b"\n")


def _module_files(module: str) -> list[tuple[str, Path]]:
    """The files that run when `module` is imported, found WITHOUT importing anything: each parent package's
    `__init__.py` (a dotted import runs them first) and the module's own file, in import order. The first
    `sys.path` entry that holds the module wins, as it would for an import."""
    parts = module.split(".")
    if not all(p.isidentifier() for p in parts):
        raise ConfigError(f"tool module {module!r} is not a dotted module name")
    for entry in sys.path:
        root = Path(entry or ".")
        leaf = root.joinpath(*parts)
        # Python prefers a package directory to a module file of the same name
        own = leaf / "__init__.py" if (leaf / "__init__.py").is_file() else leaf.with_suffix(".py")
        if not own.is_file():
            continue
        files = []
        for i in range(1, len(parts)):
            init = root.joinpath(*parts[:i]) / "__init__.py"
            if init.is_file():
                files.append((".".join(parts[:i]), init))
        return [*files, (module, own)]
    raise ConfigError(f"tool module {module} cannot be found on the module path")


def _pin_digest(files: list[tuple[str, bytes]]) -> str:
    h = hashlib.sha256()
    for name, data in files:
        h.update(name.encode() + b"\0" + _normalised(data) + b"\0")
    return h.hexdigest()


_LOADERS = frozenset(
    {
        "import_module",
        "__import__",
        "importlib",
        "runpy",
        "exec",
        "eval",
        "compile",
        "builtins",
        "__builtins__",
        "spec_from_file_location",
        "pkgutil",
        "zipimport",
        "imp",
    }
)


def _reach_problems(module: str, files: list[tuple[str, Path, bytes]]) -> list[str]:
    """What the pin cannot cover, refused instead of left open: a parent package whose `__init__.py` holds code
    (the pinned module is executed from its hashed bytes, but a parent package would be imported from disk) and
    a relative import in the module (it would load a sibling from disk, unhashed)."""
    out = []
    for name, _, data in files[:-1]:
        body = ast.parse(data).body
        if any(not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)) for n in body):
            out.append(
                f"tool module {module}: package {name} has code in __init__.py, outside the pin"
            )
    tree = ast.parse(files[-1][2])
    if any(isinstance(n, ast.ImportFrom) and n.level > 0 for n in ast.walk(tree)):
        out.append(f"tool module {module}: a relative import loads a file the pin does not cover")
    # Best effort, by NAME and not only by call: a deny-list cannot be complete, so anything that can load code from
    # somewhere else is refused wherever it appears (a call, an alias, `getattr(importlib, "import_module")`).
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            seen = [n.id]
        elif isinstance(n, ast.Attribute):
            seen = [n.attr]
        elif isinstance(n, ast.alias):
            seen = [*n.name.split("."), n.asname or ""]
        elif isinstance(n, ast.ImportFrom):
            seen = (n.module or "").split(".")
        elif isinstance(n, ast.Call) and getattr(n.func, "id", "") in (
            "getattr",
            "hasattr",
            "setattr",
        ):
            seen = [
                a.value
                for a in n.args[1:2]
                if isinstance(a, ast.Constant) and isinstance(a.value, str)
            ]
        else:
            continue
        banned = (
            _LOADERS if isinstance(n, ast.Name) else _LOADERS - {"compile"}
        )  # `re.compile` is fine
        if banned.intersection(seen):
            out.append(
                f"tool module {module}: refused loader name (a best-effort tripwire against accidental dynamic "
                "loading, not a boundary: a tool body is trusted code, and the boundary is code review plus K7)"
            )
            break
    return out


def module_sha256(module: str) -> str:
    """The pin of a tool module: SHA-256 over its own file and its parent packages' `__init__.py` files (line
    endings folded to LF), computed WITHOUT importing any of them. It does not cover what the module imports,
    helper modules or data files: a pin is review of one file's text, not of a dependency tree."""
    return _pin_digest([(n, p.read_bytes()) for n, p in _module_files(module)])


def load_tool_module(module: str, pins: Mapping[str, str] | None = None) -> types.ModuleType:
    """Import a tool module. With a pin the module is NOT imported by name: its files are read once, hashed, and
    the very bytes that were hashed are what runs, so a file swapped between the check and the import cannot run.
    The digest is stored on the module (`__hadavin_pin__`); a module already in `sys.modules` is reused only if it
    carries the same digest, otherwise (imported by name, or from older bytes) it is refused. What the pin does
    NOT cover is refused where it can be seen (parent `__init__.py` with code, relative imports) and stated where
    it cannot: absolute imports of other project modules, data files and the standard library are outside it.
    Without a pin (dev only; pilot and prod require one) it is an ordinary import."""
    pin = (pins or {}).get(module)
    try:
        if pin is None:
            return importlib.import_module(module)
        files = [(n, p, p.read_bytes()) for n, p in _module_files(module)]
        digest = _pin_digest([(n, data) for n, _, data in files])
        if digest != pin:
            raise ConfigError(
                f"tool module {module}: its source hash is {digest[:12]}..., the pin says {pin[:12]}..."
            )
        if problems := _reach_problems(module, files):
            raise ConfigError("; ".join(problems))
        if module in sys.modules:
            if getattr(sys.modules[module], "__hadavin_pin__", None) == digest:
                return sys.modules[module]
            raise ConfigError(
                f"tool module {module} is already loaded from other bytes than the pinned ones; "
                "restart the process"
            )
        _, path, source = files[-1]
        mod = types.ModuleType(module)
        mod.__file__, mod.__package__ = str(path), module.rpartition(".")[0]
        mod.__hadavin_pin__ = digest
        if path.name == "__init__.py":  # a pinned package
            mod.__package__, mod.__path__ = module, [str(path.parent)]
        sys.modules[module] = mod
        try:
            exec(compile(source, str(path), "exec"), mod.__dict__)  # noqa: S102  # nosec B102 - the pinned bytes
        except BaseException:
            sys.modules.pop(module, None)
            raise
        return mod
    except ConfigError:
        raise
    except Exception as exc:  # noqa: BLE001 - whatever the module did on load, start-up refuses
        raise ConfigError(f"tool module {module} cannot be loaded ({type(exc).__name__})") from None


def resolve_function(
    spec: ToolSpec, tool_modules: list[str], pins: Mapping[str, str] | None = None
) -> Callable[..., str]:
    module, _, name = spec.function.partition(":")
    if not name or module not in tool_modules:
        raise ConfigError(f"tool {spec.name}: {spec.function} is outside tool_modules")
    try:
        fn = getattr(load_tool_module(module, pins), name)
    except AttributeError as exc:
        raise ConfigError(f"tool {spec.name}: {spec.function} cannot be loaded") from exc
    if not callable(fn):
        raise ConfigError(f"tool {spec.name}: {spec.function} is not callable")
    return fn


def read_operations(
    tool_modules: list[str], pins: Mapping[str, str] | None = None
) -> dict[str, Binding]:
    """The union of `READ_OPERATIONS` the tool modules declare: operation id -> (METHOD, path regex). The read
    list a manifest's `operations` must stay inside, and the shape each call must fit: an operation id is not a
    label, it is bound in code to one method and one path pattern. A module without one allows no operation."""
    out: dict[str, Binding] = {}
    for module in tool_modules:
        declared = getattr(load_tool_module(module, pins), "READ_OPERATIONS", {})
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


_CREDENTIAL_HEADER = re.compile(r"auth|token|secret|key|cookie|credential|session", re.IGNORECASE)


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
        on_fetch: Callable[[], None] | None = None,
    ) -> None:
        self._on_fetch = on_fetch
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
            if len(value) < MIN_SCRUBBED_SECRET:
                raise ToolRefused(
                    f"secret {name!r} is shorter than {MIN_SCRUBBED_SECRET} characters and could not be scrubbed"
                )
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
        if re.search(r"[\\\s\x00-\x1f\x7f]", url) or not url.isascii():
            raise ToolRefused(
                "the URL holds a backslash, whitespace, a control or a non-ASCII character"
            )
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
        if parts.scheme == "http" and (
            spec.secret_names or any(_CREDENTIAL_HEADER.search(k) for k in (headers or {}))
        ):
            raise ToolRefused(
                "a credential never travels over plain http, whatever the host suffix"
            )
        try:
            egress_check(url, frozenset(spec.hosts))
        except EgressRefused:
            raise ToolRefused(f"host {host!r} is not in this tool's manifest hosts") from None
        self._port(parts, parts.scheme)
        if self._on_fetch is not None:
            self._on_fetch()  # every request to the client's system counts toward the box's rate cap
        cap = min(max_bytes or spec.max_output_bytes, self._fetch_ceiling)
        # The request carries the host the checks read (lower case, no trailing dot), never the spelling that was
        # sent in: the Host header, SNI and the certificate name are the checked name.
        shown = f"[{host}]" if ":" in host else host
        netloc = shown + (f":{parts.port}" if parts.port is not None else "")
        url = urlunsplit((parts.scheme, netloc, parts.path, parts.query, ""))
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
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, EgressRefused):
                raise ToolRefused("the host resolves to an address that is refused") from None
            raise
        if len(buf) > cap:
            if max_bytes:
                err = ToolRefused(f"the response is larger than {cap} bytes")
                err.too_large = True
                raise err
            del buf[cap:]
            del buf[_boundary(bytes(buf)) :]  # never end on half a token (half a key)
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


escape_markers = (
    runmap.escape_markers
)  # one definition, in guard/runmap.py, shared with the second pass


def truncate(text: str, limit: int) -> str:
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    return data[:limit].decode("utf-8", "ignore") + TRUNCATED


TAIL_WINDOW = 256  # bytes looked back over for a place to cut that is not inside a token


def _boundary(data: bytes) -> int:
    """Where to cut `data` (already at its byte cap): after the last whitespace in the final TAIL_WINDOW bytes, so
    a secret or key is never cut to a prefix that no pattern recognises; with none, TAIL_WINDOW bytes earlier."""
    window_start = max(len(data) - TAIL_WINDOW, 0)
    last = max(
        data.rfind(b"\n", window_start),
        data.rfind(b" ", window_start),
        data.rfind(b"\t", window_start),
    )
    return last + 1 if last >= 0 else window_start


_B64_TOKEN = re.compile(r"[A-Za-z0-9+/_=-]{12,}")


def _b64_holds(token: str, secrets: list[str], depth: int) -> bool:
    """Does `token` decode (base64, standard or URL-safe) to text holding a secret, or, `depth` levels down, to
    more base64 that does?"""
    padded = token + "=" * (-len(token) % 4)
    padded32 = token + "=" * (-len(token) % 8)
    for decode, data in (
        (base64.b64decode, padded),
        (base64.urlsafe_b64decode, padded),
        (lambda t: base64.b32decode(t, casefold=True), padded32),
    ):
        try:
            inner = decode(data).decode("utf-8", "ignore")
        except ValueError:
            continue
        if any(sec in inner for sec in secrets):
            return True
        if depth > 0 and any(_b64_holds(t, secrets, depth - 1) for t in _B64_TOKEN.findall(inner)):
            return True
    return False


def _derived(text: str, secrets: list[str]) -> str:
    """Tokens that decode (base64, standard or URL-safe, twice) to something holding a secret: a derived
    Basic-auth header, a token wrapping the secret, a doubly encoded one. Replaced whole."""
    return _B64_TOKEN.sub(
        lambda m: "<SECRET_REDACTED>" if _b64_holds(m.group(0), secrets, 2) else m.group(0), text
    )


def _decoded(text: str) -> str:
    """The text with the encodings an attacker or a log pipeline layers over a value undone: JSON `\\uXXXX`
    escapes, percent-encoding in either case, HTML entities, then NFKC and invisible characters."""
    unescaped = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
    decoded = html.unescape(unquote(unquote(unescaped)))
    # NFKC expands some characters (U+FDFA becomes 18): refuse BEFORE normalising a text whose canonical form would
    # pass the redactor's cap (InputTooLarge, a RedactionError), as redact_text does for its own views.
    return runmap.canonical(runmap.fits_after_nfkc(decoded))


def _sanitise(text: str) -> str:
    """NUL and lone surrogates (a JSON `\\ud800` a tool parsed) cannot be encoded, sent or stored."""
    return text.replace("\x00", "\ufffd").encode("utf-8", "replace").decode("utf-8")


def _cut(text: str, limit: int) -> str:
    """At most `limit` bytes, cut where no token is split, with the cut said."""
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    cut = data[:limit]
    return cut[: _boundary(cut)].decode("utf-8", "ignore") + TRUNCATED


def _secret_forms(secret: str) -> set[str]:
    raw = secret.encode("utf-8")
    b64 = base64.b64encode(raw).decode()
    return {
        secret,
        raw.hex(),
        raw.hex().upper(),
        json.dumps(secret)[1:-1],  # as it appears inside a JSON string
        json.dumps(secret, ensure_ascii=False)[1:-1],
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
    """Sanitise (NUL, lone surrogates), cut a runaway return value to `raw_cap` and then to twice `max_bytes`
    (redaction is bounded work: it never sees more than the model could be shown), scrub handed-out secrets (as
    they are, URL-quoted, base64 even twice, and behind \\u, percent, HTML-entity and invisible-character
    layers), escape the result markers and placeholder look-alikes, redact with the run's map, then truncate to
    `max_bytes`."""
    raw = _cut(_sanitise(raw), raw_cap)
    raw = _cut(raw, min(max(2 * max_bytes, MIN_REDACTION_WINDOW), defaults.MAX_REDACT_CHARS))
    long_enough = [x for x in secrets or [] if len(x) >= MIN_SCRUBBED_SECRET]
    if long_enough:
        raw = _derived(raw, long_enough)
        seen: tuple[str, str] | None = (
            None  # (raw, its decoded view): decoded once per distinct raw, not per form
        )
        for secret in long_enough:
            for form in _secret_forms(secret):
                if form in raw:
                    raw = raw.replace(form, "<SECRET_REDACTED>")
                    continue
                if seen is None or seen[0] != raw:
                    seen = (raw, _decoded(raw))
                if seen[1] != raw and form in seen[1]:
                    # the secret hides behind an encoding layer: use the decoded text (that one reply loses its
                    # original spelling, which is the price of not showing the secret)
                    raw = seen[1].replace(form, "<SECRET_REDACTED>")
    return truncate(runmap.redact_untrusted(raw, mapping), max_bytes)


def error_reason(exc: BaseException) -> str:
    """A short reason for the model. Network and driver errors carry hosts and users: their type says enough."""
    if isinstance(exc, ToolRefused):
        return str(exc)[:200]
    if isinstance(exc, OSError | urllib.error.URLError):
        return f"{type(exc).__name__} (network error)"
    return f"{type(exc).__name__}: {str(exc)[:160]}"


class FetchCounter:
    """Requests to client systems per minute, for one process: shared by every tool's fetches and the app's own
    source reads, so the cap in R372 covers both."""

    def __init__(self, per_minute: int) -> None:
        self._per_minute = per_minute
        self._lock = threading.Lock()
        self._seen: deque[float] = deque()

    def note(self) -> None:
        now = time.monotonic()
        with self._lock:
            while self._seen and now - self._seen[0] > 60:
                self._seen.popleft()
            if len(self._seen) >= self._per_minute:
                raise ToolRefused("request rate limit reached; try again later")
            self._seen.append(now)


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
        max_concurrent: int = defaults.MAX_CONCURRENT_TOOL_CALLS,
        max_per_minute: int = defaults.MAX_TOOL_CALLS_PER_MINUTE,
        fetch_counter: FetchCounter | None = None,
        disabled: Callable[[ToolSpec], str | None] | None = None,
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
        self._max_concurrent, self._max_per_minute = max_concurrent, max_per_minute
        self._admit_lock = threading.Lock()
        self._active = 0
        self._started: deque[float] = deque()
        self._fetch_counter = fetch_counter or FetchCounter(max_per_minute)
        self._disabled = (
            disabled  # why a tool may not run now (its source was switched off), or None
        )

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
            self._release()
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
                self._release()  # the slot is held until the body ENDS, not until the caller stops waiting

        # A daemon thread: a body that never returns (sleep, a lock, a busy loop) must not keep the process alive
        # at exit, which a pool's non-daemon worker would.
        try:
            worker = threading.Thread(target=work, daemon=True, name="hadavin-tool")
            worker.start()
        except BaseException:
            self._release()
            raise
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

    def _admit(self) -> None:
        """A cap on the load the agent can put on the client's systems, whatever the model asks: reads at once and
        reads per minute, for the whole process. A refused call is an `ERROR:` result the model sees."""
        now = time.monotonic()
        with self._admit_lock:
            while self._started and now - self._started[0] > 60:
                self._started.popleft()
            if self._active >= self._max_concurrent:
                raise ToolRefused("too many tool calls at once; try again")
            if len(self._started) >= self._max_per_minute:
                raise ToolRefused("tool call rate limit reached; try again later")
            self._active += 1
            self._started.append(now)

    def _release(self) -> None:
        with self._admit_lock:
            self._active -= 1

    def _note_fetch(self) -> None:
        """One request to a client system: counted against the per-minute cap (shared with source reads)."""
        self._fetch_counter.note()

    def invoke(self, name: str, args: dict[str, Any], mapping: dict[str, str]) -> ToolOutput:
        spec = self.specs[name]
        resolver = self._secrets_for(spec) if self._secrets_for else None
        ssl_ctx = self._ssl_for(spec) if self._ssl_for else None
        ctx = ToolContext(
            spec,
            self.timeout_s,
            resolver,
            self._bindings,
            ssl_context=ssl_ctx,
            on_fetch=self._note_fetch,
            **self._limits,
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
            if self._disabled is not None and (why := self._disabled(spec)):
                raise ToolRefused(why)  # a source this tool reads failed its scope re-probe
            self._admit()  # `_call` frees the slot when the tool's thread ends
            raw = self._call(name, restored, ctx)
        except Exception as exc:  # noqa: BLE001 - a failing tool becomes a result the model can react to
            error = True
            raw = ERROR_PREFIX + error_reason(exc)
        raw = _sanitise(
            raw if isinstance(raw, str) else str(raw)
        )  # a lone surrogate must not abort the call
        digest = ctx.digest() or hashlib.sha256(raw.encode("utf-8")).hexdigest()
        text = prepare_output(
            raw, mapping, spec.max_output_bytes, ctx.secrets_handed_out(), self._fetch_ceiling
        )
        return ToolOutput(text, digest, error, int((time.monotonic() - started) * 1000))
