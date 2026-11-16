"""The trust list for a server with its own certificate: the ONE place a path from a setting becomes an `ssl` context.

OpenSSL opens a path itself, and a named pipe (FIFO) or a device given as that path makes it wait for ever. So the file
is read here through `lead_desk.regfile` (a regular file or a refusal, at most CA_FILE_MAX_BYTES) and only its CONTENT
is handed to `ssl` (cadata). A file with no certificate in it is refused, because a context without any trusted
authority would refuse every server later with a confusing text. The refusal is a ValueError with a fixed text that
names the setting, never the path or the library's words.

What the file may hold: PEM text (one or more certificates; text around them, such as a comment with a non-ASCII
letter, is allowed, as it is for OpenSSL's own file reader) or one certificate in DER form. Any certificate in the
file becomes a trust anchor, also one that is not marked as a certification authority: a self-signed server
certificate (the made-up one of the test servers) is trusted this way, and ONLY for the names written in it (the
name check stays on). This is the behaviour of the old `cafile=` loading, kept on purpose."""

from __future__ import annotations

import ssl
from pathlib import Path

from lead_desk.constants import CA_FILE_MAX_BYTES
from lead_desk.regfile import read_regular_bytes

PEM_MARK = b"-----BEGIN"  # a PEM block starts with this line
_BOM = b"\xef\xbb\xbf"  # a UTF-8 byte-order mark in front of the text is harmless


# words in a cipher name that no mail login may use (they appear only when the context was made with a lowered
# security level such as "@SECLEVEL=0"; a normal context lists none). This is a check of the offered cipher list: the
# security level itself cannot be read from a context.
WEAK_CIPHER_WORDS = ("NULL", "RC4", "EXPORT", "MD5", "ADH-", "AECDH-", "DES-CBC-")  # ADH-, AECDH-: no server login


class CaFileRefused(ValueError):
    """The file of trusted certificates cannot be used. The text names the setting and nothing typed."""


def _ascii_outside_blocks(raw: bytes) -> str | None:
    """`raw` as ASCII text with every non-ASCII byte dropped from the lines OUTSIDE a BEGIN..END block, or None when a
    non-ASCII byte is inside a block or on a BEGIN or END line (a character put into a certificate must never be
    silently removed: what is trusted would then differ from what the file shows)."""
    if raw.startswith(_BOM):
        raw = raw[len(_BOM) :]
    lines = []
    inside = False
    for line in raw.splitlines(keepends=True):
        text = line.decode("ascii", errors="ignore")
        begins = text.lstrip().startswith("-----BEGIN")
        ends = "-----END" in text
        if (inside or begins or ends) and not line.isascii():
            return None
        if begins:
            inside = True
        if ends:
            inside = False
        lines.append(text)
    return "".join(lines)


def context_from_ca_file(path: str | Path, setting_name: str) -> ssl.SSLContext:
    """A verifying client context that trusts only the certificates in the file `path` (the system's authorities are
    NOT added). Raises CaFileRefused for a missing file, a pipe or device, a file over CA_FILE_MAX_BYTES, an empty
    file, text that is not a certificate, or a file that holds no certificate."""
    refused = CaFileRefused(f"{setting_name} cannot be read as a file of trusted certificates")
    try:
        raw = read_regular_bytes(path, CA_FILE_MAX_BYTES)
    except (OSError, ValueError):  # not a regular file, missing, too big (FileRefused is a ValueError)
        raise refused from None
    if not raw.strip():  # ssl treats an empty cadata as "no file given" and loads the system authorities instead
        raise refused from None
    data: str | bytes
    if PEM_MARK in raw:
        # PEM: ssl wants an ASCII string. Bytes outside ASCII OUTSIDE a BEGIN..END block are a comment around the
        # certificates (OpenSSL's file reader skips them too) and are dropped; one INSIDE a block (or on a BEGIN or
        # END line) is a changed certificate and is refused.
        cleaned = _ascii_outside_blocks(raw)
        if cleaned is None:
            raise refused from None
        data = cleaned
    else:
        data = raw  # DER: bytes
    try:
        ctx = new_verifying_context(data)
    except (OSError, ValueError):  # ssl.SSLError is an OSError
        raise refused from None
    return ctx


def _below_tls12(ctx: ssl.SSLContext) -> bool:
    """True when the context names a minimum TLS version lower than 1.2. MINIMUM_SUPPORTED means "the library's own
    floor" (the system's OpenSSL setting, which a context cannot show), so it is not refused here; the contexts this
    program makes itself (`new_verifying_context`) always set 1.2."""
    low = ctx.minimum_version
    return low != ssl.TLSVersion.MINIMUM_SUPPORTED and low < ssl.TLSVersion.TLSv1_2


def new_verifying_context(cadata: str | bytes | None = None) -> ssl.SSLContext:
    """The ONE place this program makes a verifying client context: chain and name checked, TLS 1.2 or higher."""
    ctx = ssl.create_default_context(cadata=cadata)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


TLS_OK_VERSIONS = ("TLSv1.2", "TLSv1.3")


def require_modern_protocol(conn: ssl.SSLSocket, setting_name: str) -> None:
    """Refuse a connection that negotiated a TLS version below 1.2. `require_verifying` cannot read the floor of a
    context whose minimum_version is MINIMUM_SUPPORTED (the library's own floor, which a lowered security level or an
    old system setting can put at TLS 1.0), so the RESULT of the handshake is checked, before any login is sent."""
    if conn.version() not in TLS_OK_VERSIONS:
        raise CaFileRefused(f"{setting_name}: the server connection uses a TLS version below 1.2")


def require_verifying(ctx: ssl.SSLContext, setting_name: str) -> ssl.SSLContext:
    """`ctx` itself when it checks the server's certificate chain AND its name (verify_mode CERT_REQUIRED and
    check_hostname on, a minimum TLS version of 1.2 or higher, no weak cipher offered); a CaFileRefused
    otherwise. Why: code that builds a sender or a mailbox reader may pass its own context; one made with CERT_NONE
    (or without the name check) would send a mail login to anyone. The weak-cipher test sees the ciphers a lowered
    security level ("@SECLEVEL=0") switches on (NULL, RC4, EXPORT, MD5, anonymous); the level itself cannot be read
    from a context, so "DEFAULT:@SECLEVEL=0" with no weak cipher left is NOT detected. No setting can reach this
    path (a settings file only names a file of trusted certificates), so this guards code that builds the classes
    itself."""
    if ctx.verify_mode != ssl.CERT_REQUIRED or not ctx.check_hostname:
        raise CaFileRefused(f"{setting_name}: the TLS context given does not check the server certificate and name")
    if _below_tls12(ctx) or any(w in c["name"] for c in ctx.get_ciphers() for w in WEAK_CIPHER_WORDS):
        raise CaFileRefused(f"{setting_name}: the TLS context given allows a TLS version or a cipher that is too weak")
    return ctx
