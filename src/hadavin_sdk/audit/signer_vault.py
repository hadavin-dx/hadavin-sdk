"""`vault_transit` signer: an `ed25519` key in the Transit engine of HashiCorp Vault or OpenBao.

Works on any cloud or none, through Vault's HTTP API (the same client and sign-in as the `vault` secrets kind:
token, AppRole or Kubernetes; TLS verified; never follows redirects). Vault signs; the private key never leaves
it. The signature is plain Ed25519 over the raw message, so it verifies locally like every other signer.

`key_version` pins one version: `sign` asks for it explicitly, and `public_key()` reads that version's key, so
checkpoints signed before a `rotate` still verify with the key that signed them.

Neutral protocol: the Vault-compatible Transit HTTP API (HashiCorp Vault, BSL 1.1 from 1.15; OpenBao, MPL-2.0, API-compatible
with Vault 1.14; both checked live 2026-11-01). OpenBao's Transit also has extras newer than 1.14; this kind uses
only `sign` and `keys/<name>` for an `ed25519` key. Not run against OpenBao by us yet (kind `unverified`).
"""

from __future__ import annotations

import base64
import threading
from typing import Any, Literal

from hadavin_sdk.actions.secrets_vault import VaultError, connect
from hadavin_sdk.audit.signer import probe
from hadavin_sdk.errors import ConfigError


class VaultTransitSigner:
    alg: Literal["ed25519"] = "ed25519"

    def __init__(self, client: Any, mount: str, key_name: str, key_version: int) -> None:
        self._vault = client
        self.mount = mount
        self.key_name = key_name
        self.key_version = key_version
        self.key_id = f"vault-transit:{mount}/{key_name}:v{key_version}"
        self._lock = threading.Lock()  # the client's token refresh is not thread-safe by itself
        self._public: bytes | None = None

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        with self._lock:
            status, answer = self._vault.authed(method, f"{self.mount}/{path}", body)
        if status != 200:
            raise VaultError(
                f"transit {path.split('/')[0]} {self.key_name}: Vault answered {status}"
            )
        data = answer.get("data")
        if not isinstance(data, dict):
            raise VaultError("Vault answered with an unexpected JSON shape")
        return data

    def sign(self, message: bytes) -> bytes:
        body = {"input": base64.b64encode(message).decode(), "key_version": self.key_version}
        signature = self._call("POST", f"sign/{self.key_name}", body).get("signature")
        prefix = f"vault:v{self.key_version}:"
        if not isinstance(signature, str) or not signature.startswith(prefix):
            raise VaultError(
                f"transit sign {self.key_name}: not signed by version {self.key_version}"
            )
        return base64.b64decode(signature.removeprefix(prefix))

    def public_key(self) -> bytes:
        if self._public is None:  # a key version's public half never changes
            data = self._call("GET", f"keys/{self.key_name}")
            version = (data.get("keys") or {}).get(str(self.key_version))
            if data.get("type") != "ed25519" or not isinstance(version, dict):
                raise ConfigError(
                    f"signer vault_transit: {self.key_name} v{self.key_version} is not an ed25519 key"
                )
            raw = base64.b64decode(version.get("public_key") or "")
            if len(raw) != 32:
                raise ConfigError(
                    f"signer vault_transit: {self.key_name} has no ed25519 public key"
                )
            self._public = raw
        return self._public


def build(settings, deps) -> VaultTransitSigner:
    version = settings.key_version
    client = connect(settings, ttl_s=0)
    signer = VaultTransitSigner(client, settings.transit_mount, settings.key_name, version)
    return probe(signer, "signer vault_transit")


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
            "The same Vault client and sign-in as the `vault` secrets kind. A Vault token: read from an "
            "environment variable (auth `token`), or issued at sign-in through AppRole (the role's secret id "
            "is read from an environment variable) or through the pod's Kubernetes service account."
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
            "The sign-in request of this kind is written in the imported module `actions/secrets_vault.py` "
            "and is declared there, not here."
        ),
        (
            "In the call column, `{self.mount}` is the `transit_mount` setting and `{self.key_name}` the "
            "`key_name` setting, as the signer object holds them; the permission is written with the "
            "setting's name."
        ),
        (
            "Vault's sign path has an optional last part naming a hash algorithm. R18 is the exact path "
            "without it, so that longer form is not allowed by this policy, and the code never sends it."
        ),
        (
            "In plain words: Vault calls signing `update`, but signing stores nothing; the permission lets "
            "the identity ask for a signature, not change any key or secret."
        ),
        (
            "The signer signs a test message when it is built, and verifying the audit trail builds the "
            "signer, so a process that only verifies needs R18 too."
        ),
        (
            "Create the token or the sign-in role so that it holds this policy only. Vault adds its `default` "
            "policy to every token unless told not to (`no_default_policy` when a token is created, "
            "`token_no_default_policy` on an AppRole or Kubernetes role)."
        ),
    ),
    "grants": (
        {
            "id": "R18",
            "name": "update",
            "resource": "{transit_mount}/sign/{key_name}",
            "bound": "",
            "operations": (("POST", "{self.mount}/sign/{self.key_name}"),),
            "applies_when": "",
            "reason": "signs each audit checkpoint and the start-up test message",
            "verified": ("2026-11-11", "V-TR", "B-TR", "V-POL"),
            "confirmed_live": None,
            "claims_unverified": (),
        },
        {
            "id": "R19",
            "name": "read",
            "resource": "{transit_mount}/keys/{key_name}",
            "bound": "",
            "operations": (("GET", "{self.mount}/keys/{self.key_name}"),),
            "applies_when": "",
            "reason": "reads the pinned version's public key and the key type",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
            "confirmed_live": None,
            "claims_unverified": (),
        },
    ),
    "free": (),
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
            "name": "{transit_mount}/keys/{key_name}",
            "capabilities": ("delete",),
            "reason": "deletes the key that signs the audit trail",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
        },
        {
            "type": "path",
            "name": "{transit_mount}/keys/{key_name}/config",
            "reason": "can allow the key to be deleted or exported",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
        },
        {
            "type": "path",
            "name": "{transit_mount}/export/*",
            "reason": "copies the private key out",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
        },
        {
            "type": "path",
            "name": "{transit_mount}/byok-export/*",
            "reason": "copies the private key out, wrapped for another system",
            "verified": None,
        },
        {
            "type": "path",
            "name": "{transit_mount}/keys/{key_name}/rotate",
            "reason": "makes a new key version, so new signatures no longer match the pinned version",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
        },
        {
            "type": "path",
            "name": "{transit_mount}/keys/{key_name}/trim",
            "reason": "removes old key versions for good",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
        },
        {
            "type": "path",
            "name": "{transit_mount}/restore",
            "reason": "replaces a key with one from a backup",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
        },
        {
            "type": "path",
            "name": "{transit_mount}/restore/*",
            "reason": "replaces the named key with one from a backup",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
        },
        {
            "type": "path",
            "name": "{transit_mount}/backup/*",
            "reason": "copies the private key out as a backup",
            "verified": ("2026-11-11", "V-TR", "B-TR"),
        },
    ),
}
