"""Checkpoint signers (OD-4): Ed25519, or ECDSA P-256 where the key store has no Ed25519 (Azure Key Vault), so
an auditor verifies a checkpoint with the public key alone.

This module holds the Protocol, the local check, the `ed25519_local` kind and the key helpers ported from
WARDEN `audit.py` (main c78d7709: `key_path`, `generate_key`, `load_private_key`, `load_public_key`); every
cloud or Vault signer lives in its own kind module (`signer_aws`, `signer_azure`, `signer_gcp`, `signer_vault`)
and imports its SDK there. Needs only `cryptography` (`pip install hadavin-sdk[signer]`).

Neutral protocol: a local PEM Ed25519 key, verified with the public key alone (RFC 8032).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Literal, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from hadavin_sdk import pathguard
from hadavin_sdk.errors import ConfigError

_RAW = (serialization.Encoding.Raw, serialization.PublicFormat.Raw)


Alg = Literal["ed25519", "ecdsa-p256"]


class Signer(Protocol):
    key_id: str
    alg: Alg

    def sign(self, message: bytes) -> bytes:
        """64 bytes over the raw message: an Ed25519 signature, or ECDSA P-256/SHA-256 as raw r || s."""
        ...

    def public_key(self) -> bytes:
        """Raw: 32 bytes (Ed25519), or the 65-byte uncompressed SEC1 point (ECDSA P-256)."""
        ...


def verify_signature(
    public_key: bytes, signature: bytes, message: bytes, alg: Alg = "ed25519"
) -> bool:
    """Local check with the public key alone: what an auditor runs."""
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
    """An Ed25519 key in a PEM file (demo and pilot; refused in prod by the environment table)."""

    alg: Literal["ed25519"] = "ed25519"

    def __init__(self, key: ed25519.Ed25519PrivateKey) -> None:
        self._key = key
        self.key_id = "ed25519:" + hashlib.sha256(self.public_key()).hexdigest()[:16]

    def sign(self, message: bytes) -> bytes:
        return self._key.sign(message)

    def public_key(self) -> bytes:
        return self._key.public_key().public_bytes(*_RAW)


def probe(signer: Signer, label: str) -> Signer:
    """Start-up: sign a test message and verify it, so an unreachable or wrong key fails before the first run."""
    message = b"hadavin-signer-probe"
    try:
        ok = verify_signature(signer.public_key(), signer.sign(message), message, signer.alg)
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(f"{label}: cannot sign at start-up ({exc.__class__.__name__})") from exc
    if not ok:
        raise ConfigError(f"{label}: the key's signature does not verify with its public key")
    return signer


# --------------------------------------------------------------------------- table factories


def build_local(settings, deps) -> LocalSigner:
    """The PEM from `private_key_secret_name` (any secrets kind: Vault, a mounted Secret, a cloud store), or
    from `private_key_path` (demo and pilot only: a key file in an image or on a disk can be copied)."""
    name = settings.passphrase_secret_name
    passphrase = deps.resolve(name).encode("utf-8") if name else None
    if settings.private_key_secret_name:
        source = f"secret {settings.private_key_secret_name!r}"
        pem = deps.resolve(settings.private_key_secret_name).encode("utf-8")
    else:
        # Operator config: the operator picks any key file (no outer folder exists, so nothing "contains" it);
        # its shape is checked and the resolved path is what is read.
        try:
            typed = Path(settings.private_key_path)
            path = pathguard.join(
                typed.parent, typed.name, what="signer key file", must_exist=True, kind="file"
            )
        except (
            pathguard.PathRefused
        ) as exc:  # a control character or an over-long path is refused as it is
            text = f"signer ed25519_local: no key file at {settings.private_key_path}"
            raise pathguard.mapped(exc, R10=text, R11=text) from None
        source, pem = (
            str(settings.private_key_path),
            path.read_bytes(),
        )  # as typed, never the resolved path
    try:
        key = _private_key(pem, passphrase, source)
    except (TypeError, ValueError) as exc:
        # The class only: a parse error must never echo key material.
        raise ConfigError(
            f"signer ed25519_local: cannot load {source} ({type(exc).__name__})"
        ) from None
    return probe(LocalSigner(key), "signer ed25519_local")


# --------------------------------------------------------------------------- keys

# Key files are written inside one folder only: a path from a command line must never reach `~/.bashrc`, a
# synced folder, or a file through `..` or a symlink. The folder is HADAVIN_KEY_DIR, or ~/.hadavin.
KEY_DIR_ENV = "HADAVIN_KEY_DIR"


def key_dir() -> Path:
    return Path(os.environ.get(KEY_DIR_ENV) or Path.home() / ".hadavin").expanduser()


def key_path(path: Path, base: Path | None = None) -> Path:
    """The real location of `path` when it lies inside `base` (default: the key folder, created 0700 if
    missing); else ValueError. The file itself must not be a symlink, and its folder must already exist."""
    try:  # ``~name`` for a user that does not exist raises RuntimeError; a NUL raises ValueError: fixed text, no value
        folder = (base or key_dir()).expanduser()
        target = Path(path).expanduser()
    except RuntimeError:
        raise ValueError(
            "the key file or folder path cannot be read (home folder not found)"
        ) from None
    except (ValueError, OSError, TypeError):
        raise ValueError("the key file or folder path cannot be read (not a valid path)") from None
    # the shape of the key FILE and of the key folder is checked before any folder is made (a NUL, a control character
    # or a name too long is refused here, not after mkdir); the folder is then made and resolved with every error of the
    # system turned into a fixed refusal with no path (``create_mode``)
    try:  # shape only; a link that leaves its folder is refused below, with its own words
        pathguard.inside(target.parent, target, what="key file")
    except pathguard.PathRefused as exc:
        if exc.rule != "R8":
            raise
    folder = pathguard.operator_dir(folder, what="key folder", must_exist=False, create_mode=0o700)
    try:  # a name too long for the system makes this check itself raise; it is a refusal, with no path in the text
        linked = target.is_symlink()
    except (OSError, ValueError):
        raise ValueError("the key file path cannot be checked (too long or not valid)") from None
    if linked:
        raise ValueError("the key file is a symlink: a key file is never used through one")
    real: Path | None
    try:
        parent = pathguard.inside(folder, target.parent, what="key file", must_exist=True)
        real = pathguard.inside(folder, parent / target.name, what="key file")
    except pathguard.PathRefused as exc:
        if exc.rule != "R8":
            raise
        real = None  # leaves the key folder: the refusal below, with its pinned wording
    if real is None or real == folder:
        raise ValueError(  # no path in the text: the value as typed and the resolved folder both stay out
            "the key file is outside the key folder: key files are kept only there "
            f"(set {KEY_DIR_ENV} to choose another folder)"
        )
    return real


def _create(real: Path, data: bytes, mode: int) -> None:
    """Create `real` holding `data`, never over an existing file; a file this call could not fill is removed."""
    fd = os.open(real, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), mode)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
    except BaseException:
        real.unlink(missing_ok=True)
        raise


def generate_key(
    private_path: Path,
    public_path: Path,
    passphrase: bytes | None = None,
    base: Path | None = None,
) -> None:
    """A new Ed25519 pair, both files inside `base` (default: the key folder), neither written over an existing
    file. The private key is created 0600 (POSIX; on Windows the profile folder's ACL keeps others out)."""
    public_real = key_path(public_path, base)
    private_real = key_path(private_path, base)
    if public_real == private_real:
        raise ValueError(f"{private_path} and {public_path} are the same file: the pair needs two")
    if public_real.exists():
        raise FileExistsError(f"{public_path} exists; refusing to overwrite it")
    key = ed25519.Ed25519PrivateKey.generate()
    encryption = (
        serialization.BestAvailableEncryption(passphrase)
        if passphrase
        else serialization.NoEncryption()
    )
    pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, encryption
    )
    _create(private_real, pem, 0o600)
    try:
        _create(
            public_real,
            key.public_key().public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            ),
            0o644,
        )
    except BaseException:
        private_real.unlink()  # no half pair
        raise


def load_private_key(path: Path, passphrase: bytes | None = None) -> ed25519.Ed25519PrivateKey:
    # an operator-chosen key file (no outer folder): shape checked, the resolved path is read
    path = Path(path)
    real = pathguard.join(
        path.parent, path.name, what="private key file", must_exist=True, kind="file"
    )
    return _private_key(real.read_bytes(), passphrase, str(path))


def _private_key(pem: bytes, passphrase: bytes | None, source: str) -> ed25519.Ed25519PrivateKey:
    key = serialization.load_pem_private_key(pem, password=passphrase)
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        raise TypeError(f"{source} is not an Ed25519 private key")
    return key


def load_public_key(path: Path) -> bytes:
    """A PEM public key file as the raw 32 bytes (what `verify_signature` takes)."""
    # operator-chosen file, shape checked
    path = Path(path)
    real = pathguard.join(
        path.parent, path.name, what="public key file", must_exist=True, kind="file"
    )
    key = serialization.load_pem_public_key(real.read_bytes())
    if not isinstance(key, ed25519.Ed25519PublicKey):
        raise TypeError(f"{path} is not an Ed25519 public key")
    return key.public_bytes(*_RAW)
