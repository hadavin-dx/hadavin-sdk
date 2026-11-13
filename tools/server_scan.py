"""Finds code that can open a server socket, for the repo test ``tests/test_bindguard.py``.

Three scans, all lists of FORMS and not proof that no other form exists:

* ``resolved_forms(source)`` reads a Python file as a tree and resolves every import alias in the scope it is
  written in (module, function or class: an import inside one function does not rename a name in another;
  ``import a.b as c``, ``from m import n as k``, and ``from m import *`` for the modules that serve), then matches
  the full dotted name, so a server class imported under another name is still seen. It also reads class bases (a
  class that inherits from a server class or ``socketserver.BaseServer``), ``.run(...)`` calls with an address
  written out as the first argument or a ``host=`` keyword (the usual shape of a web framework's development
  server), ``importlib.import_module("<module that serves>")`` (the standard server modules and the serving
  libraries), the entry points of the serving libraries (``waitress.serve``, ``hypercorn.asyncio.serve``, ...)
  and gRPC ``add_*_port`` calls. An address is "written out" by ``netguard.parse_ip_literal`` and
  ``netguard.is_localhost_name``, the rule the guard itself uses;
* ``launcher_hits(text)`` reads a file that is not Python (a shell script, a Dockerfile, a compose file, a CI
  workflow, a Makefile, a justfile, a PowerShell script, a Kubernetes manifest, an entrypoint script) for the
  words a launcher uses to start a server; ``launcher_counts`` counts each word, because an allowed word is
  allowed a number of times and a second one is new;
* ``pyproject_hits(text)`` reads the script tables of a ``pyproject.toml`` (``[project.scripts]``,
  ``[project.gui-scripts]``, ``[project.entry-points.*]``, any ``scripts`` or ``tasks`` table of a tool) for a
  launcher word or an entry point in a module that serves.

What none of the scans can see: code another process runs (a launcher in a client's own repository), and a socket
made through the C type directly (``_socket.socket(...).bind``: its method cannot be replaced, so the run-time check
in the test, that only ``bindguard.listen`` reaches ``socket.socket.bind``, does not see it either). The run-time
check proves only the paths the tests execute."""

from __future__ import annotations

import ast
import re
import tomllib
from collections import Counter
from typing import cast

from hadavin_sdk.netguard import is_localhost_name, parse_ip_literal

STDLIB_SERVER_CLASS = re.compile(
    r"^(?:(?:Threading|Forking)?(?:HTTP|TCP|UDP|UnixStream|UnixDatagram)Server|(?:Simple|Doc)?XMLRPCServer|"
    r"BaseServer|WSGIServer)$"
)
STDLIB_SERVER_MODULES = {"http.server", "socketserver", "xmlrpc.server", "wsgiref.simple_server"}
# full dotted names that open a listener; a library that is not installed here is still named
DOTTED = {
    "wsgiref.simple_server.make_server",
    "werkzeug.serving.run_simple",
    "werkzeug.run_simple",
    "websockets.serve",
    "websockets.asyncio.server.serve",
    "websockets.sync.server.serve",
    "websockets.legacy.server.serve",
    "trio.serve_tcp",
    "trio.open_tcp_listeners",
    "anyio.create_tcp_listener",
    "anyio.create_unix_listener",
    "grpc.server",
    "grpc.aio.server",
    "asyncio.start_server",
    "asyncio.start_unix_server",
    "aiohttp.web.run_app",
    "aiohttp.web.TCPSite",
    "uvicorn.run",
}
SERVER_ATTRS = {"add_insecure_port", "add_secure_port"}
SERVER_ROOTS = {"hypercorn", "waitress", "gunicorn", "uvicorn", "cheroot", "twisted"}
# the last name of a dotted path under one of SERVER_ROOTS that starts a server (``waitress.serve``,
# ``hypercorn.asyncio.serve``, ``uvicorn.Server``, ``twisted.internet.reactor.listenTCP``, ...)
SERVER_ENTRY_NAMES = {
    "serve",
    "run",
    "Server",
    "create_server",
    "run_app",
    "serve_forever",
    "listenTCP",
    "listenSSL",
    "listenUNIX",
    "BaseApplication",
    "WSGIApplication",
}
NOT_A_SERVER_RUN = ("subprocess.", "runpy.", "asyncio.run", "trio.run", "anyio.run", "pytest.")


_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def _outer_parts(node: ast.AST) -> list[ast.AST]:
    """The parts of a function, class or lambda that run in the scope AROUND it (bases, decorators, defaults)."""
    if isinstance(node, ast.ClassDef):
        return [*node.bases, *node.keywords, *node.decorator_list]
    args = cast(ast.FunctionDef | ast.Lambda, node).args
    parts: list[ast.AST] = [*args.defaults, *(d for d in args.kw_defaults if d is not None)]
    parts += getattr(node, "decorator_list", [])
    return parts


def _body_of(node: ast.AST) -> list[ast.AST]:
    return [node.body] if isinstance(node, ast.Lambda) else list(cast(ast.FunctionDef, node).body)


def _scope_nodes(roots: list[ast.AST]) -> list[ast.AST]:
    """Every node of one scope: a nested function, class or lambda is listed but its body is not entered."""
    out: list[ast.AST] = []
    stack = list(reversed(roots))
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(
            _outer_parts(node) if isinstance(node, _SCOPES) else ast.iter_child_nodes(node)
        )
    return out


def _imports(nodes: list[ast.AST]) -> tuple[dict[str, str], list[str]]:
    """(name used in this scope -> the dotted name it stands for, the modules imported with ``*``)."""
    found: dict[str, str] = {}
    stars: list[str] = []
    for node in nodes:
        if isinstance(node, ast.Import):
            for a in node.names:
                found[a.asname or a.name.split(".")[0]] = (
                    a.name if a.asname else a.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for a in node.names:
                if a.name == "*":
                    stars.append(node.module)
                else:
                    found[a.asname or a.name] = f"{node.module}.{a.name}"
    return found, stars


def _dotted(node: ast.AST, aliases: dict[str, str], stars: list[str]) -> str | None:
    """``a.b.c`` for a name chain, with its first name replaced by what it was imported as (a name that no import
    gives is looked for in the modules imported with ``*``)."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    root = aliases.get(node.id)
    if root is None:
        root = next(
            (f"{m}.{node.id}" for m in stars if _is_server(f"{m}.{node.id}", as_base=True)), node.id
        )
    return ".".join([root, *reversed(parts)])


def _is_server(dotted: str, *, as_base: bool = False) -> bool:
    """``BaseServer`` counts only as a base class or when it is made (a type annotation names it and starts nothing)."""
    module, _, last = dotted.rpartition(".")
    if last == "BaseServer" and not as_base:
        return False
    return (
        dotted in DOTTED
        or (module in STDLIB_SERVER_MODULES and bool(STDLIB_SERVER_CLASS.match(last)))
        or (dotted.split(".")[0] in SERVER_ROOTS and bool(module) and last in SERVER_ENTRY_NAMES)
    )


def _serving_module(name: str) -> bool:
    """A module that only serves: a standard server module (or one under it) or a serving library."""
    return (
        name in STDLIB_SERVER_MODULES
        or any(name.startswith(m + ".") for m in STDLIB_SERVER_MODULES)
        or name.split(".")[0] in SERVER_ROOTS
    )


def _host_like(text: str) -> bool:
    """An empty text, ``localhost`` or an address written out (the rule of ``netguard``): the first argument of a
    development server's ``run``. A word that only looks like hexadecimal (``add``, ``bad``, ``cafe``) is not."""
    return text == "" or is_localhost_name(text) or parse_ip_literal(text) is not None


def _form_of(node: ast.AST, aliases: dict[str, str], stars: list[str]) -> str | None:
    name = None
    if isinstance(node, ast.Name | ast.Attribute):
        dotted = _dotted(node, aliases, stars)
        if dotted and _is_server(dotted):
            name = dotted
        elif isinstance(node, ast.Attribute) and node.attr in SERVER_ATTRS:
            name = node.attr
    elif isinstance(node, ast.ClassDef):
        for base in node.bases:
            dotted = _dotted(base, aliases, stars)
            if dotted and _is_server(dotted, as_base=True):
                name = f"class {node.name}({dotted})"
    elif isinstance(node, ast.Call):
        func = _dotted(node.func, aliases, stars) or ""
        if func and _is_server(func, as_base=True) and not _is_server(func):
            name = func  # ``BaseServer(...)`` made directly
        if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
            literal_host = (
                bool(node.args)
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and _host_like(node.args[0].value)
            )
            if (
                literal_host or any(k.arg == "host" for k in node.keywords)
            ) and not func.startswith(NOT_A_SERVER_RUN):
                name = ".run(host)"
        elif (
            func in ("importlib.import_module", "__import__")
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
            and _serving_module(node.args[0].value)
        ):
            name = f"import {node.args[0].value}"
    return name


def _visit(
    roots: list[ast.AST],
    parent_aliases: dict[str, str],
    parent_stars: list[str],
    found: list[str],
) -> None:
    """One scope: its own imports are added to what the scope around it imported, then every node is read with
    that, then each nested scope is read the same way (an import in one function renames nothing in another)."""
    nodes = _scope_nodes(roots)
    aliases, stars = _imports(nodes)
    aliases = {**parent_aliases, **aliases}
    stars = [*parent_stars, *stars]
    for node in nodes:
        if (name := _form_of(node, aliases, stars)) is not None:
            found.append(f"{name}@{node.lineno}")
    for node in nodes:
        if isinstance(node, _SCOPES):
            _visit(_body_of(node), aliases, stars, found)


def resolved_forms(source: str) -> list[str]:
    """``"<form>@<line>"`` for every server form in ``source`` after alias resolution (in scope)."""
    found: list[str] = []
    _visit(list(ast.parse(source).body), {}, [], found)
    return found


# each word is one alternative, so a test can take each away alone (``tests/bind_mutants.py``)
LAUNCHER_WORD_LIST = (
    r"http\.server",
    r"flask\s+run",
    r"uvicorn",
    r"gunicorn",
    r"hypercorn",
    r"waitress",
    r"serve_forever",
    r"--host\b",
    r"0\.0\.0\.0",
    r"\bnc\s+-l",
    r"\bsocat\b",
    r"python\s+-m\s+\w*server",
    r"\brunserver\b",
)
LAUNCHER_WORDS = re.compile("|".join(LAUNCHER_WORD_LIST), re.IGNORECASE)
LAUNCHER_GLOBS = (
    "*.sh",
    "*.bash",
    "*.ps1",
    "*.service",
    "*.mk",
    "Dockerfile*",
    "compose*.y*ml",
    "docker-compose*.y*ml",
    "Procfile",
    "Makefile",
    "makefile",
    "GNUmakefile",
    "justfile",
    "Justfile",
    "entrypoint*",
    "k8s/**/*.y*ml",
    "kubernetes/**/*.y*ml",
    "deploy/**/*.y*ml",
    "charts/**/*.y*ml",
    "manifests/**/*.y*ml",
)


def launcher_hits(text: str) -> list[str]:
    """``"<word>@<line>"`` for each launcher word in a non-Python file."""
    return [
        f"{m.group(0).lower()}@{i}"
        for i, line in enumerate(text.splitlines(), 1)
        for m in LAUNCHER_WORDS.finditer(line)
    ]


def launcher_counts(text: str) -> Counter[str]:
    """How many times each launcher word is written in a file (the words, lower case, without the line)."""
    return Counter(hit.split("@")[0] for hit in launcher_hits(text))


def _strings(value: object) -> list[str]:
    """Every text inside a parsed TOML value (a text, a list or a table, at any depth)."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [t for item in value for t in _strings(item)]
    if isinstance(value, dict):
        return [t for item in value.values() for t in _strings(item)]
    return []


def _script_tables(node: object, path: tuple[str, ...] = ()) -> list[object]:
    """The tables of a parsed ``pyproject.toml`` that hold commands or entry points: any table whose name is
    ``scripts``, ``gui-scripts``, ``tasks`` or ``entry-points`` (under ``project`` or a tool)."""
    found: list[object] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"scripts", "gui-scripts", "tasks", "entry-points"}:
                found.append(value)
            else:
                found += _script_tables(value, (*path, key))
    return found


def pyproject_hits(text: str) -> list[str]:
    """The launcher words, and the entry points in a module that serves, found in the script and task tables of a
    ``pyproject.toml`` (the dependency lists are not read: naming ``uvicorn`` there starts nothing)."""
    hits: list[str] = []
    for table in _script_tables(tomllib.loads(text)):
        for command in _strings(table):
            hits += [h.split("@")[0] for h in launcher_hits(command)]
            module = command.split(":")[0].strip()
            if re.fullmatch(r"[A-Za-z_][\w.]*", module) and _serving_module(module):
                hits.append(f"entry point {module}")
    return hits
