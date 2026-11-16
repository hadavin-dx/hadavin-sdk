"""The `signer` kind: how an approval is signed and checked (no single dependency; least privilege).

Two roles, two objects. A `Signer` holds the private material and can mint. A `SignatureVerifier` is what the write path receives.
  ed25519   (the DEFAULT; needs the optional `cryptography` package, imported ONLY in this module and only when this kind is chosen) ASYMMETRIC: the
            verifier holds the public key only, so the write path cannot mint. `can_mint` is False and a test walks every attribute reachable from the
            verifier and the gate looking for the private key bytes.
  hmac      (stdlib only, DEV ONLY, explicit opt-in) SYMMETRIC: the verifier holds the same key, so whoever holds the verifier COULD mint. `can_mint` is True.
            It is never picked by default: `ApprovalIssuer` needs `key=` or `signer=` to get it, and with neither it FAILS CLOSED
            (`SignerNotConfigured`) when the ed25519 extra is not installed, so an image built without the extra cannot start a minting verifier by accident.
A client build adds a kind here (a KMS/HSM sign call, a passkey assertion check) without touching approval.py or writegate.py.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Protocol


class SignerNotConfigured(RuntimeError):
    """No asymmetric signer is available and no signer or dev key was passed: start-up stops instead of falling back to a verifier that can mint."""


class SignatureVerifier(Protocol):
    can_mint: bool
    kind: str  # written into every applied audit row

    def verify(self, body: bytes, sig: str) -> bool: ...


class Signer(Protocol):
    def sign(self, body: bytes) -> str: ...

    def verifier(self) -> SignatureVerifier: ...


def default_kind() -> str:
    """ed25519 when the optional extra is installed. Otherwise there is NO default: raises `SignerNotConfigured` (fail closed). HMAC must be asked for."""
    import importlib.util

    if importlib.util.find_spec("cryptography") is None:
        raise SignerNotConfigured(
            "no asymmetric signer: install the ed25519 extra (uv sync --all-extras), or pass key= / signer= for a DEV HMAC signer that can mint"
        )
    return "ed25519"


class HmacVerifier:
    can_mint = True  # symmetric: this object holds the signing key
    kind = "hmac (dev, can mint)"

    def __init__(self, key: bytes) -> None:
        self._key = key

    def verify(self, body: bytes, sig: str) -> bool:
        try:
            return hmac.compare_digest(hmac.new(self._key, body, hashlib.sha256).hexdigest(), sig)
        except (TypeError, ValueError):  # compare_digest raises on non-ASCII text: an unusable signature, never a crash
            return False


class HmacSigner:
    def __init__(self, key: bytes | None = None) -> None:
        if key is not None and (not isinstance(key, bytes) or len(key) < 16):
            raise ValueError("an HMAC key is at least 16 bytes (an empty or short key signs nothing worth checking)")
        self._key = key if key is not None else secrets.token_bytes(32)

    def sign(self, body: bytes) -> str:
        return hmac.new(self._key, body, hashlib.sha256).hexdigest()

    def verifier(self) -> HmacVerifier:
        return HmacVerifier(self._key)


class Ed25519Verifier:
    can_mint = False  # holds the public key only
    kind = "ed25519"

    def __init__(self, public_bytes: bytes) -> None:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        self._pub = Ed25519PublicKey.from_public_bytes(public_bytes)

    def verify(self, body: bytes, sig: str) -> bool:
        from cryptography.exceptions import InvalidSignature

        try:
            self._pub.verify(bytes.fromhex(sig), body)
        except (InvalidSignature, ValueError, TypeError):
            return False
        return True


class Ed25519Signer:
    def __init__(self, private_bytes: bytes | None = None) -> None:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        self._priv = (
            Ed25519PrivateKey.from_private_bytes(private_bytes) if private_bytes is not None else Ed25519PrivateKey.generate()
        )

    def sign(self, body: bytes) -> str:
        return self._priv.sign(body).hex()

    def verifier(self) -> Ed25519Verifier:
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

        return Ed25519Verifier(self._priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))


KINDS = {"hmac": HmacSigner, "ed25519": Ed25519Signer}


def make_signer(kind: str = "hmac", secret: bytes | None = None) -> Signer:
    """The kind comes from client config. An unknown kind is an error at start-up, never a silent fallback to a weaker one."""
    if kind not in KINDS:
        raise ValueError(f"unknown signer kind {kind!r}; known: {sorted(KINDS)}")
    return KINDS[kind](secret)  # type: ignore[return-value]
