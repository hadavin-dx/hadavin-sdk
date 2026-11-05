"""Signer kind (neutral default: local Ed25519; ECDSA P-256 verify for key stores without Ed25519). The ONLY module here that imports `cryptography`.

Local re-implementation of the interface of core `audit/signer.py` (core PR #48, not merged; see CORE_COPIES.md): `Signer` protocol, `verify_signature`,
a local key. The APPROVER holds the private key (a passkey/HSM/KMS in a client build); the engine holds PUBLIC keys only (`KeyDirectory`), so the
verifier cannot mint an approval. Alternatives behind the same Protocol: AWS KMS, Azure Key Vault, GCP KMS, Vault (outlined, not built).
"""

from __future__ import annotations

import hashlib
from typing import Literal, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

_RAW = (serialization.Encoding.Raw, serialization.PublicFormat.Raw)
Alg = Literal["ed25519", "ecdsa-p256"]


class Signer(Protocol):
    key_id: str
    alg: Alg

    def sign(self, message: bytes) -> bytes: ...

    def public_key(self) -> bytes: ...


def verify_signature(public_key: bytes, signature: bytes, message: bytes, alg: Alg = "ed25519") -> bool:
    """Check with the public key alone."""
    try:
        if alg == "ed25519":
            ed25519.Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        elif alg == "ecdsa-p256" and len(signature) == 64:
            point = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), public_key)
            r, s = int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big")
            point.verify(encode_dss_signature(r, s), message, ec.ECDSA(hashes.SHA256()))
        else:
            return False
    except (InvalidSignature, ValueError):
        return False
    return True


class LocalSigner:
    """An Ed25519 key held by the APPROVER side (tests and the demo harness hold these; the engine never does)."""

    alg: Literal["ed25519"] = "ed25519"

    def __init__(self, existing: ed25519.Ed25519PrivateKey | None = None) -> None:
        self._key = existing or ed25519.Ed25519PrivateKey.generate()
        self.key_id = "ed25519:" + hashlib.sha256(self.public_key()).hexdigest()[:16]

    def sign(self, message: bytes) -> bytes:
        return self._key.sign(message)

    def public_key(self) -> bytes:
        return self._key.public_key().public_bytes(*_RAW)
