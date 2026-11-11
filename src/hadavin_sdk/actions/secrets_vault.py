"""`vault` secrets: HashiCorp Vault or OpenBao, KV version 2 (standard library HTTP, no extra).

`<address>/v1/<mount>/data/<path_prefix><name>`, field `field` (default `value`). Sign-in, chosen by `auth`:
* `token`: the token in the environment variable `token_env` (default `VAULT_TOKEN`);
* `approle`: `role_id` from config, the secret id in the environment variable `secret_id_env`;
* `kubernetes`: `role` from config, the pod's service-account token from `jwt_path`.
The Vault token stays in memory; a 403 (expired token) signs in again once. TLS is always verified (`ca_cert`
adds a private CA); plain http only to this machine (a local server). `namespace` sets `X-Vault-Namespace`
(Vault Enterprise / HCP / OpenBao namespaces). Cache, single-flight and logging rules: `CachedSecrets`.

Neutral protocol: the Vault-compatible KV v2 HTTP API, served by HashiCorp Vault (BSL 1.1 from 1.15; checked 2026-11-01) and by
OpenBao (MPL-2.0, Linux Foundation; API-compatible with Vault 1.14 by its own statement). Not run against
OpenBao by us yet: that is why the kind stays `unverified`.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hadavin_sdk.actions.secrets_cache import CachedSecrets
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.http import NoRedirect

_NAME = re.compile(r"[A-Za-z0-9_.-]{1,255}")


class VaultError(RuntimeError):
    """Vault answered with an unexpected status (the response body is never included)."""


class VaultProvider(CachedSecrets):
    def __init__(
        self,
        address: str,
        login: Callable[[VaultProvider], str],
        *,
        mount: str = "secret",
        path_prefix: str = "",
        field: str = "value",
        namespace: str | None = None,
        context: ssl.SSLContext | None = None,
        timeout_s: float = 10.0,
        renewable: bool = True,
        ttl_s: float = 300,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__(ttl_s, clock)
        self.address = address.rstrip("/")
        self._login, self._renewable = login, renewable
        self.mount, self.path_prefix, self.field = mount, path_prefix, field
        self.namespace, self.timeout_s = namespace, timeout_s
        self._context = context or ssl.create_default_context()
        self._token: str | None = None
        # Never follow a redirect (a standby node's 307 would carry the token to an address nobody configured,
        # maybe over plain http); a loopback server is reached directly, never through HTTP(S)_PROXY.
        handlers: list = [NoRedirect(), urllib.request.HTTPSHandler(context=self._context)]
        if urllib.parse.urlsplit(self.address).hostname in {"127.0.0.1", "localhost", "::1"}:
            handlers.append(urllib.request.ProxyHandler({}))
        self._opener = urllib.request.build_opener(*handlers)

    def call(self, method: str, path: str, body: dict | None = None, token: str | None = None):
        """One Vault API call: (status, parsed JSON or {})."""
        headers = {"X-Vault-Request": "true", "Content-Type": "application/json"}
        if token:
            headers["X-Vault-Token"] = token
        if self.namespace:
            headers["X-Vault-Namespace"] = self.namespace
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(  # noqa: S310 - the scheme is checked in the settings (https or loopback)
            f"{self.address}/v1/{path}", data=data, headers=headers, method=method
        )
        try:
            with self._opener.open(req, timeout=self.timeout_s) as r:
                status, raw = r.status, r.read()
        except urllib.error.HTTPError as exc:  # also a refused redirect (3xx)
            exc.close()
            return exc.code, {}
        try:  # a proxy or load-balancer page can answer 200 with HTML
            parsed = json.loads(raw) if raw else {}
        except ValueError:
            raise VaultError(f"Vault answered {status} with a body that is not JSON") from None
        if not isinstance(parsed, dict):
            raise VaultError(f"Vault answered {status} with an unexpected JSON shape")
        return status, parsed

    def authed(self, method: str, path: str, body: dict | None = None):
        """A call with the Vault token; a 403 (expired or revoked token) signs in again, once. Not
        thread-safe by itself: callers hold a lock (CachedSecrets.get, the transit signer)."""
        if self._token is None:
            self._token = self._login(self)
        status, answer = self.call(method, path, body, token=self._token)
        if status == 403 and self._renewable:
            self._token = self._login(self)
            status, answer = self.call(method, path, body, token=self._token)
        return status, answer

    def _fetch(self, name: str) -> str:
        if not _NAME.fullmatch(name) or name in {
            ".",
            "..",
        }:  # the name becomes part of the URL path
            raise ConfigError(
                f"secret {name!r}: Vault names here are letters, digits, '.', '_', '-'"
            )
        status, body = self.authed("GET", f"{self.mount}/data/{self.path_prefix}{name}")
        if status == 404:
            raise ConfigError(f"secret {name!r} not found in Vault")
        if status != 200:
            raise VaultError(f"secret {name!r}: Vault answered {status}")
        fields = _mapping(_mapping(body.get("data")).get("data"))
        if self.field not in fields:
            raise ConfigError(f"secret {name!r} has no field {self.field!r} in Vault")
        value = fields[self.field]
        if not isinstance(value, str):  # never str(None) == "None"
            raise ConfigError(f"secret {name!r}: field {self.field!r} is not a string in Vault")
        return value


def _mapping(value: Any) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise VaultError("Vault answered with an unexpected JSON shape")
    return value


def _login_with(provider: VaultProvider, auth_mount: str, payload: dict[str, Any]) -> str:
    status, body = provider.call("POST", f"auth/{auth_mount}/login", payload)
    token = _mapping(body.get("auth")).get("client_token") if status == 200 else None
    if not isinstance(token, str) or not token:
        raise ConfigError(f"secrets vault: {auth_mount} sign-in refused ({status})")
    return token


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"secrets vault: environment variable {name} is not set")
    return value


def build(settings, deps) -> VaultProvider:
    return connect(
        settings,
        ttl_s=settings.ttl_s,
        mount=settings.mount,
        path_prefix=settings.path_prefix,
        field=settings.field,
    )


def connect(settings, **kw: Any) -> VaultProvider:
    """A Vault client from connection settings (address, auth, namespace, CA, timeout): the `vault`
    secrets kind, and the `vault_transit` signer's HTTP client."""
    if settings.auth == "token":

        def login(p: VaultProvider) -> str:
            return _env(settings.token_env)
    elif settings.auth == "approle":

        def login(p: VaultProvider) -> str:
            payload = {"role_id": settings.role_id, "secret_id": _env(settings.secret_id_env)}
            return _login_with(p, settings.auth_mount or "approle", payload)
    else:

        def login(p: VaultProvider) -> str:
            try:
                jwt = Path(settings.jwt_path).read_text(encoding="utf-8").strip()
            except (OSError, UnicodeDecodeError) as exc:
                raise ConfigError(
                    f"vault kubernetes sign-in: cannot read {settings.jwt_path} ({type(exc).__name__})"
                ) from None
            payload = {"role": settings.role, "jwt": jwt}
            return _login_with(p, settings.auth_mount or "kubernetes", payload)

    context = ssl.create_default_context(cafile=str(settings.ca_cert) if settings.ca_cert else None)
    return VaultProvider(
        settings.address,
        login,
        namespace=settings.namespace,
        context=context,
        timeout_s=settings.timeout_s,
        renewable=settings.auth != "token",
        **kw,
    )


# The permissions this kind needs. Data only: nothing here is run. `tools/policy_page.py` reads this literal
# from the source text. `tests/test_policy_guard.py` fails when it differs from the requests written above in
# the call shapes that test lists; a request sent in a way no rule of that test lists is not seen.
# `verified` = (date, source ids): the name and the path form were found, spelled so, in those vendor sources
# (the ids resolve in tests/fixtures/policy_sources_2026-11-11.txt). `confirmed_live` = accepted by a real
# account; None everywhere so far.
POLICY = {
    "platform": "vault",
    "credential": {
        "how": (
            "A Vault token: read from an environment variable (auth `token`), or issued at sign-in through "
            "AppRole (the role's secret id is read from an environment variable) or through the pod's "
            "Kubernetes service account."
        ),
        "lifetime": "long",
        "exception": (
            "With auth `token` the operator supplies the token, so how long it lives is the operator's choice "
            "and this kind cannot shorten it. With auth `approle` the secret id in the environment is itself "
            "a long-lived credential unless the operator gives it an expiry in Vault. A token issued through "
            "AppRole or Kubernetes sign-in lives as long as the Vault role says. No ticket removes "
            "these long-lived credentials yet: ledger row BL-core-q8c1-lifetime tracks it."
        ),
    },
    "notes": (
        (
            "Create the token or the sign-in role so that it holds this policy only. Vault adds its `default` "
            "policy to every token unless told not to (`no_default_policy` when a token is created, "
            "`token_no_default_policy` on an AppRole or Kubernetes role)."
        ),
        (
            "In the call column, `{self.mount}` and `{self.path_prefix}` are the settings `mount` and "
            "`path_prefix` as the object holds them, and `{name}` is the secret's name: one path part, "
            "checked by the code before the request is sent."
        ),
    ),
    "grants": (
        {
            "id": "R17",
            "name": "read",
            "resource": "{mount}/data/{path_prefix}+",
            "bound": (
                "the `+` stands for exactly one path part, the secret's name, directly under this "
                "deployment's `path_prefix` setting (which must not be empty); nothing deeper is covered"
            ),
            "operations": (("GET", "{self.mount}/data/{self.path_prefix}{name}"),),
            "applies_when": "",
            "reason": "reads one named secret",
            "verified": (
                "2026-11-11",
                "V-KV",
                "V-POL",
                "V-ACL",
                "V-PARSE",
                "B-KV",
                "B-POL",
                "B-ACL",
            ),
            "confirmed_live": None,
            "claims_unverified": ("the + matches exactly one whole path part, nothing deeper",),
        },
    ),
    "free": (
        {
            "operations": (("POST", "auth/{auth_mount}/login"),),
            "reason": (
                "the sign-in request of auth `approle` and `kubernetes` carries no token; auth `token` sends "
                "no sign-in request"
            ),
            "note": "",
            "verified": ("2026-11-11", "V-API", "V-APPROLE", "V-K8S", "B-API"),
        },
    ),
    "never": (
        {
            "type": "role",
            "name": "root",
            "reason": "the built-in policy that may do everything",
            "verified": ("2026-11-11", "V-POL"),
        },
        {
            "type": "path",
            "name": "sys/*",
            "reason": "the server's own settings: mounts, policies, audit devices",
            "verified": ("2026-11-11", "V-POL"),
        },
        {
            "type": "path",
            "name": "{mount}/data/*",
            "capabilities": ("create", "update", "patch", "delete"),
            "reason": "the reader could replace, change or remove what it reads",
            "verified": ("2026-11-11", "V-POL", "V-KV"),
        },
        {
            "type": "path",
            "name": "{mount}/delete/*",
            "reason": "marks versions of a secret as deleted",
            "verified": ("2026-11-11", "V-KV", "B-KV"),
        },
        {
            "type": "path",
            "name": "{mount}/undelete/*",
            "reason": "brings deleted versions of a secret back",
            "verified": None,
        },
        {
            "type": "path",
            "name": "{mount}/subkeys/*",
            "reason": "shows the field names inside secrets this kind was not asked to read",
            "verified": None,
        },
        {
            "type": "path",
            "name": "{mount}/metadata/*",
            "reason": "lists every secret name and can delete every version of a secret",
            "verified": ("2026-11-11", "V-KV", "B-KV"),
        },
        {
            "type": "path",
            "name": "{mount}/destroy/*",
            "reason": "removes versions of a secret for good",
            "verified": ("2026-11-11", "V-KV", "B-KV"),
        },
    ),
}
