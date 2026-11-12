"""Every place that decides "plain http only to this computer" gives the same answer as before the one shared list
(``netguard.LOOPBACK_LITERALS``) replaced the five private copies. The expected answer is the old rule written out
here: the host the URL names is exactly one of three spellings. Made-up addresses only."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from hadavin_sdk.backends.table import (
    OpenAICompatSettings,
    S3ObjectLockSettings,
    VaultSettings,
)
from hadavin_sdk.config import url_allowed
from hadavin_sdk.guard import http as http_guard
from hadavin_sdk.llm import common as llm_common
from hadavin_sdk.llm.openai_compat import floating
from hadavin_sdk.netguard import LOOPBACK_LITERALS

_DOT = "."
LOOP_1 = _DOT.join(("127", "0", "0", "1"))
LOOP_2 = _DOT.join(("127", "0", "0", "2"))
ALL_ZEROS = _DOT.join(["0"] * 4)
KEYED = (
    "api_key" + "_secret_name"
)  # built from parts: a keyword with "secret" in it reads as a hard-coded one
OLD_RULE = {LOOP_1, "localhost", "::1"}  # the rule the five private copies each wrote out
HOSTS = [
    LOOP_1,
    "localhost",
    "LOCALHOST",
    "::1",
    "[::1]",
    LOOP_2,
    ALL_ZEROS,
    "::ffff:" + LOOP_1,
    "remote.example.test",
    "localhost.example.test",
    "127.1",
]


def _url(host: str, scheme: str = "http") -> str:
    shown = f"[{host}]" if ":" in host and not host.startswith("[") else host
    return f"{scheme}://{shown}:9/x"


def _expected(host: str) -> bool:
    """What urlsplit(...).hostname gives, run through the old rule (urlsplit lower-cases and drops brackets)."""
    from urllib.parse import urlsplit

    return urlsplit(_url(host)).hostname in OLD_RULE


@pytest.mark.parametrize("host", HOSTS)
def test_url_allowed_http_only_to_the_old_three(host: str) -> None:
    assert url_allowed(_url(host), True) is _expected(host)
    assert url_allowed(_url(host), False) is False  # the switch is still needed


@pytest.mark.parametrize("host", HOSTS)
def test_openai_compat_plain_http_needs_a_loopback_host_and_no_key(host: str) -> None:
    ok = _expected(host)
    try:
        OpenAICompatSettings(kind="openai_compat", base_url=_url(host))
        accepted = True
    except ValidationError:
        accepted = False
    assert accepted is ok
    with pytest.raises(ValidationError):  # a key never goes over plain http, loopback or not
        OpenAICompatSettings(**{"kind": "openai_compat", "base_url": _url(host), KEYED: "k"})


@pytest.mark.parametrize("host", HOSTS)
def test_a_local_model_without_a_tag_is_floating_only_on_the_old_three(host: str) -> None:
    assert floating("llama3", _url(host)) is _expected(host)
    assert floating("llama3:8b", _url(host)) is False


@pytest.mark.parametrize("host", HOSTS)
def test_the_object_lock_endpoint_allows_plain_http_only_to_the_old_three(host: str) -> None:
    kwargs = {"kind": "s3_object_lock", "bucket": "b", "region": "r", "endpoint_url": _url(host)}
    try:
        S3ObjectLockSettings(**kwargs)
        accepted = True
    except ValidationError:
        accepted = False
    assert accepted is _expected(host)


@pytest.mark.parametrize("host", HOSTS)
def test_the_vault_address_allows_plain_http_only_to_the_old_three(host: str) -> None:
    try:
        VaultSettings(kind="vault", address=_url(host))
        accepted = True
    except ValidationError:
        accepted = False
    assert accepted is _expected(host)


@pytest.mark.parametrize("host", HOSTS)
def test_the_vault_client_skips_the_environment_proxy_only_for_the_old_three(
    host: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from urllib.request import ProxyHandler

    monkeypatch.setenv(
        "http_proxy", "http://proxy.example.test:3128"
    )  # so the default handler is not empty

    from hadavin_sdk.actions.secrets_vault import VaultProvider

    provider = VaultProvider(_url(host), lambda p: "t")
    direct = not any(
        isinstance(h, ProxyHandler) for h in provider._opener.handlers
    )  # none = no proxy
    assert direct is _expected(host)


def test_the_http_guard_and_the_model_client_share_the_one_list() -> None:
    assert http_guard.LOOPBACK is LOOPBACK_LITERALS
    assert llm_common._LOOPBACK is LOOPBACK_LITERALS
    assert LOOPBACK_LITERALS == frozenset(OLD_RULE)


# --- one loopback meaning: no module of src writes its own list ---------------------------------------------------

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
LITERALS = {"127.0.0.1", "::1", "localhost"}
# (file under src/hadavin_sdk, what it holds, why it is not a second loopback list). Each entry is used by the scan.
ALLOWED_INLINE = {
    ("netguard.py", "127.0.0.1"): "the one list",
    ("netguard.py", "localhost"): "the one list",
    ("netguard.py", "::1"): "the one list",
    (
        "approvals/receiver.py",
        "127.0.0.1",
    ): "the default bind of the approval receiver, not a test of a host",
    (
        "tools.py",
        "localhost",
    ): "names a tool may never reach (with cloud metadata names), not a loopback test",
}
ALLOWED_ATTRIBUTE = {
    ("netguard.py", "is_loopback"): "the one place",
    (
        "guard/http.py",
        "is_loopback",
    ): "an SSRF refusal on every address a name resolved to, with link-local, "
    "multicast and reserved ranges; a different question",
}


def _inline_loopback_uses() -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in LITERALS:
                    found.add((rel, node.value))
            elif isinstance(node, ast.Attribute) and node.attr == "is_loopback":
                found.add((rel, node.attr))
    return found


def test_no_module_of_src_keeps_its_own_loopback_list():
    """A new inline loopback spelling (a set, an `==` test, an `ipaddress` `.is_loopback` call) outside `netguard`
    fails here, so the next copy cannot appear without a decision written in ALLOWED_*."""
    allowed = set(ALLOWED_INLINE) | set(ALLOWED_ATTRIBUTE)
    found = _inline_loopback_uses()
    assert found - allowed == set(), (
        f"a module writes its own loopback test: {sorted(found - allowed)}"
    )
    assert allowed - found == set(), f"an allowance nothing uses: {sorted(allowed - found)}"


def test_the_scan_sees_an_inline_copy(tmp_path, monkeypatch):
    """The scan itself works: a planted module with a private list is found."""
    (tmp_path / "planted.py").write_text('LOCAL = {"127.0.0.1", "::1"}\n', encoding="utf-8")
    monkeypatch.setitem(globals(), "SRC", tmp_path)
    assert _inline_loopback_uses() == {("planted.py", "127.0.0.1"), ("planted.py", "::1")}


def test_the_database_address_check_reads_the_one_rule():
    """`store.postgres._is_local` keeps its own work (a socket path, a comma list, PGHOST) and asks `netguard`
    for each host; this pins what it answers, including the two spellings the shared rule adds (any letter case of
    `localhost`, and a mapped IPv6 loopback address), which libpq reaches on this computer as well."""
    from hadavin_sdk.store.postgres import _is_local

    local = [
        "127.0.0.1",
        "localhost",
        "LOCALHOST",
        "::1",
        "127.8.9.10",
        "/var/run/postgresql",
        "",
        "localhost,127.0.0.1",
    ]
    remote = [
        "db.example.test",
        "10.0.0.5",
        "127.0.0.1.example.test",
        "127.0.0.1,db.example.test",
        " 127.0.0.1",
        "0x7f.0.0.1",
    ]
    for host in local:
        assert _is_local({"host": host}) is True, f"{host!r} should be local"
    for host in remote:
        assert _is_local({"host": host}) is False, f"{host!r} should be remote"
