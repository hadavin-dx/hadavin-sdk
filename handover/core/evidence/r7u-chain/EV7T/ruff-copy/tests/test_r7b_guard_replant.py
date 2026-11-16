"""Round 7B (review part 2, M3): the file-and-socket call guard misses names it did not list: name lookups
(getaddrinfo, gethostbyname), the event loop's own socket calls (sock_connect), a pool made from a context (ctx.Pool),
a name given to getattr as a text, and a TLS context made by name (ssl.SSLContext). The shapes are planted again
here, in a lot of spellings (module name, alias, `from` import, a method of any object, a `getattr` with the name as
text), and EVERY one must be found. The count is printed with -s (and pinned: a shape taken out is a failure)."""

from __future__ import annotations

import pytest
from test_file_call_guard import _plant, _problems

MODULE_FUNCTIONS = {
    "socket": [
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "getnameinfo",
        "getfqdn",
        "create_connection",
        "create_server",
        "fromfd",
        "socketpair",
    ],
    "ssl": ["wrap_socket", "get_server_certificate"],
    "multiprocessing.pool": ["ThreadPool", "Pool"],
    "multiprocessing.dummy": ["Pool"],
}
OBJECT_METHODS = [
    "Pool",
    "ThreadPool",
    "sock_connect",
    "sock_recv",
    "sock_recv_into",
    "sock_sendall",
    "sock_accept",
    "getaddrinfo",
    "getnameinfo",
    "gethostbyname",
    "create_connection",
    "create_server",
    "create_datagram_endpoint",
    "create_unix_connection",
    "create_unix_server",
    "connect_read_pipe",
    "connect_write_pipe",
    "add_reader",
    "add_writer",
    "wrap_socket",
]
LITERAL_NAMES = [
    "open",
    "read_text",
    "read_bytes",
    "write_text",
    "write_bytes",
    "system",
    "popen",
    "Popen",
    "listdir",
    "scandir",
    "walk",
    "unlink",
    "mkdir",
    "chmod",
    "glob",
    "rglob",
    "iterdir",
    "touch",
    "eval",
    "exec",
    "compile",
    "__import__",
    "input",
    "breakpoint",
]


def shapes() -> dict[str, str]:
    out: dict[str, str] = {}
    for mod, names in MODULE_FUNCTIONS.items():
        for n in names:
            out[f"{mod}.{n} by module name"] = f"import {mod}\n{mod}.{n}()"
            out[f"{mod}.{n} by from-import alias"] = f"from {mod} import {n} as _f\n_f()"
    for n in OBJECT_METHODS:
        out[f"x.{n}(...) on any object"] = f"def f(x):\n    return x.{n}(1)"
        out[f"loop.{n}(...) on the running loop"] = f"import asyncio\nasyncio.get_running_loop().{n}(1)"
        out[f"await loop.{n}(...)"] = f"async def f(loop):\n    await loop.{n}(1)"
    for n in LITERAL_NAMES:
        out[f"getattr(o, {n!r})"] = f"def f(o):\n    return getattr(o, {n!r})"
        out[f"getattr(os, {n!r}) called"] = f"import os\ngetattr(os, {n!r})('x')"
    out["ssl.SSLContext(...)"] = "import ssl\nssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)"
    out["SSLContext from-import alias"] = "from ssl import SSLContext as C\nC(1)"
    out["ssl alias SSLContext"] = "import ssl as s\ns.SSLContext()"
    out["ssl.SSLContext handed on as a value"] = "import ssl\nmake = ssl.SSLContext\nmake(1)"
    out["setattr with a literal name"] = "def f(o, v):\n    setattr(o, 'open', v)"
    out["hasattr with a literal name"] = "def f(o):\n    return hasattr(o, 'open')"
    out["delattr with a literal name"] = "def f(o):\n    delattr(o, 'open')"
    return out


ALL = shapes()


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_the_count_of_replanted_shapes_is_pinned() -> None:
    assert len(ALL) >= 140, len(ALL)
    assert len(ALL) == 145, len(ALL)  # a shape taken out of the list shows here


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_every_replanted_shape_is_found(
    tmp_path_factory: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    missed = []
    for shape, source in ALL.items():
        root = _plant(tmp_path_factory.mktemp("r7b"), source)
        if not [p for p in _problems(root, {}, {}) if p.startswith("scripts/planted.py")]:
            missed.append(shape)
    with capsys.disabled():
        print(f"\nREPLANT: {len(ALL) - len(missed)} of {len(ALL)} shapes found; missed: {missed}")
    assert not missed, f"the guard did not find: {missed}"


# CONTROL (r7e, new since frozen): passes on the frozen tree, pins behaviour that must stay; no mutant run.
def test_a_type_name_in_a_signature_is_no_call(tmp_path_factory: pytest.TempPathFactory) -> None:
    for source in (
        "import ssl\ndef f(c: ssl.SSLContext | None = None) -> ssl.SSLContext: return c",
        "from ssl import SSLContext\nx: SSLContext | None = None",
    ):
        root = _plant(tmp_path_factory.mktemp("r7bn"), source)
        assert [p for p in _problems(root, {}, {}) if p.startswith("scripts/planted.py")] == [], source
