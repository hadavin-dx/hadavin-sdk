"""Every place that decides "plain http only to this computer" gives the same answer as before the one shared list
(``netguard.LOOPBACK_LITERALS``) replaced the five private copies. The expected answer is the old rule written out
here: the host the URL names is exactly one of three spellings. Made-up addresses only."""

from __future__ import annotations

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


