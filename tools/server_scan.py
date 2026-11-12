"""Finds code that can open a server socket, for the repo test ``tests/test_bindguard.py``.

Two scans, both lists of FORMS and not proof that no other form exists:

* ``resolved_forms(source)`` reads a Python file as a tree, first resolves every import alias (``import a.b as c``,
  ``from m import n as k``) and then matches the full dotted name, so a server class imported under another name is
  still seen. It also reads class bases (a class that inherits from a server class or ``socketserver.BaseServer``),
  ``.run(...)`` calls with an address written out as the first argument or a ``host=`` keyword (the usual shape of a web framework's
  development server), ``importlib.import_module("<module that only serves>")`` and gRPC ``add_*_port`` calls.
* ``launcher_hits(text)`` reads a file that is not Python (a shell script, a Dockerfile, a compose file, a CI
  workflow) for the words a launcher uses to start a server.

What neither scan can see: code another process runs (a launcher in a client's own repository). The runtime check
in the test (only ``bindguard.listen`` reaches a socket bind) proves only the paths the tests execute."""

from __future__ import annotations

import ast
import re

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
NOT_A_SERVER_RUN = ("subprocess.", "runpy.", "asyncio.run", "trio.run", "anyio.run", "pytest.")


def _aliases(tree: ast.AST) -> dict[str, str]:
    """name used in the file -> the dotted name it stands for."""
    found: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                found[a.asname or a.name.split(".")[0]] = (
                    a.name if a.asname else a.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                found[a.asname or a.name] = f"{node.module}.{a.name}"
    return found


def _dotted(node: ast.AST, aliases: dict[str, str]) -> str | None:
    """``a.b.c`` for a name chain, with its first name replaced by what it was imported as."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    root = aliases.get(node.id, node.id)
    return ".".join([root, *reversed(parts)])


def _is_server(dotted: str, *, as_base: bool = False) -> bool:
    """``BaseServer`` counts only as a base class or when it is made (a type annotation names it and starts nothing)."""
    module, _, last = dotted.rpartition(".")
    if last == "BaseServer" and not as_base:
        return False
    return dotted in DOTTED or (
        module in STDLIB_SERVER_MODULES and bool(STDLIB_SERVER_CLASS.match(last))
    )


def _host_like(text: str) -> bool:
    """An empty text, ``localhost`` or an address written out: the first argument of a development server's ``run``."""
    return (
        text == ""
        or text.lower() == "localhost"
        or re.fullmatch(r"[0-9a-fA-F:.\[\]]+", text) is not None
    )


def resolved_forms(source: str) -> list[str]:
    """``"<form>@<line>"`` for every server form in ``source`` after alias resolution."""
    tree = ast.parse(source)
    aliases = _aliases(tree)
    found: list[str] = []
    for node in ast.walk(tree):
        name = None
        if isinstance(node, ast.Name | ast.Attribute):
            dotted = _dotted(node, aliases)
            if dotted and _is_server(dotted):
                name = dotted
            elif isinstance(node, ast.Attribute) and node.attr in SERVER_ATTRS:
                name = node.attr
        elif isinstance(node, ast.ClassDef):
            for base in node.bases:
                dotted = _dotted(base, aliases)
                if dotted and _is_server(dotted, as_base=True):
                    name = f"class {node.name}({dotted})"
        elif isinstance(node, ast.Call):
            func = _dotted(node.func, aliases) or ""
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
                and node.args[0].value.split(".")[0] in SERVER_ROOTS
            ):
                name = f"import {node.args[0].value}"
        if name is not None:
            found.append(f"{name}@{node.lineno}")
    return found


LAUNCHER_WORDS = re.compile(
    r"http\.server|flask\s+run|uvicorn|gunicorn|hypercorn|waitress|serve_forever|--host\b|0\.0\.0\.0|"
    r"\bnc\s+-l|\bsocat\b|python\s+-m\s+\w*server",
    re.IGNORECASE,
)
LAUNCHER_GLOBS = (
    "*.sh",
    "Dockerfile*",
    "compose*.y*ml",
    "docker-compose*.y*ml",
    "*.service",
    "Procfile",
)


def launcher_hits(text: str) -> list[str]:
    """``"<word>@<line>"`` for each launcher word in a non-Python file."""
    return [
        f"{m.group(0).lower()}@{i}"
        for i, line in enumerate(text.splitlines(), 1)
        for m in LAUNCHER_WORDS.finditer(line)
    ]
