"""Class: a path from a setting that OpenSSL would open itself (the file of trusted certificates) can hang on a named
pipe (FIFO) and can be any size. The library reads it through `lead_desk.regfile` and hands only the content to `ssl`.
Each case runs in a child process with a 5 second limit; the refusal text names the setting and never the path.
Entry points: lead_desk.tls_trust, the SMTP provider (DESK_SMTPP_CA_FILE) and the real-check script
(REAL_IMAP_n_CA_FILE). Made-up certificate, no network."""

from __future__ import annotations

import multiprocessing
import os
import sys
from pathlib import Path
from queue import Empty
from typing import Any

import pytest
from support import run_program, skip_or_fail_without_openssl

from demo_only.fake_smtp_tls import make_cert
from lead_desk.constants import CA_FILE_MAX_BYTES

REPO = Path(__file__).resolve().parents[1]
FIFO_SKIP = pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no named pipes on this platform")
SETTING = "DESK_SMTPP_CA_FILE"


def _outcome(entry: str, path: str, queue: Any) -> None:
    """Runs in a child process: use `path` as a CA file through one entry point; put "ok" or "Kind|text"."""
    sys.path.insert(0, str(REPO / "scripts"))
    from lead_desk.smtp_provider import ProviderSettings, SmtpProviderOutbox
    from lead_desk.tls_trust import context_from_ca_file

    try:
        if entry == "trust":
            context_from_ca_file(path, SETTING)
        elif entry == "smtp":
            SmtpProviderOutbox._context_from_file(Path(path))
        else:
            import run_real_check

            run_real_check.imap_settings(
                {"REAL_IMAP_1_USER": "u", "REAL_IMAP_1_PASSWORD_FILE": "pw", "REAL_IMAP_1_CA_FILE": path}
            )
        assert ProviderSettings  # imported only to prove the module loads
    except Exception as e:  # report every kind of failure to the parent
        queue.put(type(e).__name__ + "|" + str(e))
    else:
        queue.put("ok")


def _in_child(entry: str, path: Path) -> str:
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    child = ctx.Process(target=_outcome, args=(entry, str(path), queue))
    child.start()
    try:
        return str(queue.get(timeout=5))
    except Empty:
        pytest.fail(f"the {entry} reader waited for ever or took over 5 seconds on the CA file")
    finally:
        child.terminate()
        child.join(10)


ENTRIES = ["trust", "smtp", "imap"]


def _case(tmp_path: Path, how: str) -> Path:
    p = tmp_path / "ca-name.pem"
    if how == "fifo":
        os.mkfifo(p)
    elif how == "over_cap":
        p.write_bytes(b"A" * (CA_FILE_MAX_BYTES + 1))
    elif how == "empty":
        p.write_bytes(b"")
    elif how == "text":
        p.write_text("this is not certificate text\n", encoding="utf-8")
    elif how == "folder":
        p.mkdir()
    elif how == "missing":
        pass
    return p


@FIFO_SKIP
@pytest.mark.parametrize("entry", ENTRIES)
@pytest.mark.parametrize("how", ["fifo", "over_cap", "empty", "text", "folder", "missing"])
def test_an_unusable_ca_file_is_refused_at_once_with_fixed_text(tmp_path: Path, entry: str, how: str) -> None:
    out = _in_child(entry, _case(tmp_path, how))
    kind, _, text = out.partition("|")
    assert kind != "ok", "the file was accepted as a list of trusted certificates"
    assert text.endswith("cannot be read as a file of trusted certificates"), out
    assert "ca-name" not in text and str(tmp_path) not in text and "SSL" not in text


@pytest.mark.parametrize("entry", ENTRIES)
def test_a_valid_ca_file_still_works(tmp_path: Path, entry: str) -> None:
    made = make_cert(tmp_path, "localhost")
    if made is None:
        skip_or_fail_without_openssl()
    assert _in_child(entry, made[0]) == "ok"


def test_the_context_trusts_only_the_file_and_checks_the_name(tmp_path: Path) -> None:
    import ssl

    from lead_desk.tls_trust import context_from_ca_file

    made = make_cert(tmp_path, "localhost")
    if made is None:
        skip_or_fail_without_openssl()
    ctx = context_from_ca_file(made[0], SETTING)
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True
    assert ctx.cert_store_stats()["x509"] == 1  # the system authorities are not added


# -- what the file may hold ----------------------------------------------------------------------------------------


def _made(tmp_path: Path) -> tuple[Path, Path]:
    made = make_cert(tmp_path, "localhost")
    if made is None:
        skip_or_fail_without_openssl()
    return made


def _pem_with_words(tmp_path: Path, before: str, after: str) -> Path:
    cert, _key = _made(tmp_path)
    out = tmp_path / "with-words.pem"
    out.write_bytes(before.encode("utf-8") + cert.read_bytes() + after.encode("utf-8"))
    return out


@pytest.mark.parametrize("entry", ENTRIES)
@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("# Zertifikat für localhost – äöü\n", ""),
        ("", "\n# Ende: ünïcode ✓\n"),
        ("Subject: Müller GmbH\n", "trailing words: é\n"),
    ],
    ids=["comment-before", "comment-after", "words-around"],
)
def test_a_pem_file_with_non_ascii_words_around_the_certificate_still_loads(
    tmp_path: Path, entry: str, before: str, after: str
) -> None:
    """The old `cafile=` loading accepted such a file (OpenSSL skips text outside the BEGIN and END lines)."""
    assert _in_child(entry, _pem_with_words(tmp_path, before, after)) == "ok"


def test_a_certificate_and_its_key_in_one_file_load_and_only_the_certificate_counts(tmp_path: Path) -> None:
    from lead_desk.tls_trust import context_from_ca_file

    cert, key = _made(tmp_path)
    both = tmp_path / "both.pem"
    both.write_bytes(cert.read_bytes() + key.read_bytes())
    assert context_from_ca_file(both, SETTING).cert_store_stats()["x509"] == 1


@pytest.mark.parametrize("entry", ENTRIES)
def test_a_der_certificate_still_loads(tmp_path: Path, entry: str) -> None:
    import ssl

    cert, _key = _made(tmp_path)
    der = tmp_path / "c.der"
    der.write_bytes(ssl.PEM_cert_to_DER_cert(cert.read_text(encoding="ascii")))
    assert _in_child(entry, der) == "ok"


@pytest.mark.parametrize("how", ["key_only", "key_with_words", "no_certificate_with_words", "broken_certificate"])
def test_a_pem_file_without_a_usable_certificate_is_still_refused(tmp_path: Path, how: str) -> None:
    from lead_desk.tls_trust import CaFileRefused, context_from_ca_file

    cert, key = _made(tmp_path)
    p = tmp_path / "x.pem"
    if how == "key_only":
        p.write_bytes(key.read_bytes())
    elif how == "key_with_words":
        p.write_bytes("# Schlüssel – nur ein Schlüssel\n".encode() + key.read_bytes())
    elif how == "no_certificate_with_words":
        p.write_bytes("# Zertifikat fehlt – äöü\n-----BEGIN NOTHING-----\nAAAA\n-----END NOTHING-----\n".encode())
    else:  # a certificate whose body was cut: the lenient decoding must not turn it into a trusted one
        lines = cert.read_text(encoding="ascii").splitlines()
        p.write_bytes(("\n".join([*lines[:3], "é" + lines[3][1:], *lines[4:]]) + "\n").encode())
    with pytest.raises(CaFileRefused) as seen:
        context_from_ca_file(p, SETTING)
    assert str(seen.value) == f"{SETTING} cannot be read as a file of trusted certificates"


# -- a certificate that is not marked as an authority (a made-up server certificate) --------------------------------


def _leaf_cert(tmp_path: Path, host: str) -> tuple[Path, Path]:
    """A self-signed certificate that says it is NOT a certification authority (basicConstraints CA:FALSE)."""
    import shutil

    exe = shutil.which("openssl")
    if exe is None:
        skip_or_fail_without_openssl()
    cert, key = tmp_path / "leaf.pem", tmp_path / "leaf-key.pem"
    run_program(
        [exe, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key), "-out", str(cert), "-days", "2"]
        + ["-subj", f"/CN={host}", "-addext", f"subjectAltName=DNS:{host}"]
        + ["-addext", "basicConstraints=critical,CA:FALSE"],
        check=True,
        capture_output=True,
    )
    return cert, key


def _handshake(ctx: object, cert: Path, key: Path, name: str) -> str:
    """Connect a client with context `ctx` (for server name `name`) to a server that shows `cert`, over a socket pair.
    Returns "ok" or the kind of error the client got."""
    import socket
    import ssl
    import threading

    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ctx.load_cert_chain(cert, key)
    near, far = socket.socketpair()
    near.settimeout(5)
    far.settimeout(5)

    def serve() -> None:
        try:
            with server_ctx.wrap_socket(near, server_side=True) as s:
                s.sendall(b"hi")
        except (ssl.SSLError, OSError):  # the client refused the certificate: the handshake fails on this side too
            near.close()

    th = threading.Thread(target=serve)
    th.start()
    try:
        with ctx.wrap_socket(far, server_hostname=name) as c:  # type: ignore[attr-defined]
            return "ok" if c.recv(2) == b"hi" else "no data"
    except ssl.SSLCertVerificationError:
        return "SSLCertVerificationError"
    finally:
        far.close()
        th.join(10)


def test_a_certificate_that_is_not_an_authority_is_trusted_only_for_its_own_name(tmp_path: Path) -> None:
    """Pinned on purpose (the old `cafile=` loading did the same): the file's certificates are trust anchors even when
    they are not marked as authorities, so a self-signed server certificate works, and only for the names written in
    it; every other name is refused."""
    from lead_desk.tls_trust import context_from_ca_file

    cert, key = _leaf_cert(tmp_path, "localhost")
    ctx = context_from_ca_file(cert, SETTING)
    stats = ctx.cert_store_stats()
    assert stats["x509"] == 1 and stats["x509_ca"] == 0  # a trust anchor that is not an authority
    assert _handshake(ctx, cert, key, "localhost") == "ok"
    assert _handshake(ctx, cert, key, "other.example") == "SSLCertVerificationError"


# -- a character inside a certificate is never silently dropped ------------------------------------------------------


@pytest.mark.parametrize("entry", ENTRIES)
@pytest.mark.parametrize("where", ["body-line", "begin-line", "end-line", "between-two-letters"])
def test_a_non_ascii_character_inside_a_certificate_block_is_refused(tmp_path: Path, entry: str, where: str) -> None:
    """Round-3 finding 7: the lenient decoding dropped a character put INSIDE the base64 body and still accepted the
    file, so the trusted certificate differed from the one the file shows. Outside a block it stays allowed."""
    cert, _key = _made(tmp_path)
    lines = cert.read_text(encoding="ascii").splitlines()
    if where == "body-line":
        lines[2] = lines[2][:10] + "é" + lines[2][10:]  # an inserted character: the body is otherwise whole
    elif where == "between-two-letters":
        lines[1] = lines[1][:5] + "​" + lines[1][5:]  # an invisible character
    elif where == "begin-line":
        lines[0] = lines[0].replace("CERTIFICATE", "CERTIFICATÉ")
    else:
        lines[-1] = lines[-1].replace("END", "ÉND")
    bad = tmp_path / "inserted.pem"
    bad.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    out = _in_child(entry, bad)
    kind, _, text = out.partition("|")
    assert kind != "ok", "a certificate with an inserted character was accepted"
    assert text.endswith("cannot be read as a file of trusted certificates"), out


def test_a_utf8_byte_order_mark_and_comments_around_a_certificate_are_still_accepted(tmp_path: Path) -> None:
    from lead_desk.tls_trust import context_from_ca_file

    cert, _key = _made(tmp_path)
    p = tmp_path / "bom.pem"
    p.write_bytes(b"\xef\xbb\xbf# Zertifikat \xc3\xa4\n" + cert.read_bytes() + "# Ende ✓\n".encode())
    assert context_from_ca_file(p, SETTING).cert_store_stats()["x509"] == 1


# -- a setting that is there but empty is refused, never read as "no file" ------------------------------------------


BLANKS = ["", " ", "   \t"]


@pytest.mark.parametrize("blank", BLANKS)
def test_an_empty_smtp_ca_file_setting_is_refused_not_read_as_unset(blank: str) -> None:
    """Round-3 finding 6 (mail path): `DESK_SMTPP_CA_FILE=` used to count as unset and silently trust the SYSTEM
    authorities. The line must be removed or must name a file."""
    from lead_desk.envnum import SettingRefused
    from lead_desk.smtp_provider import ProviderSettings

    base = {
        "DESK_SMTPP_HOST": "mail.example.test",
        "DESK_SMTPP_USER": "u",
        "DESK_SMTPP_PASSWORD_FILE": "p.txt",
        "DESK_SMTPP_FROM": "a@example.test",
        "DESK_SMTPP_RECIPIENTS": "b@example.test",
        "DESK_SMTPP_MAX_SENDS": "5",
    }
    assert ProviderSettings.from_env(base).ca_file is None  # the line left out is still fine
    with pytest.raises(SettingRefused) as seen:
        ProviderSettings.from_env({**base, "DESK_SMTPP_CA_FILE": blank})
    assert str(seen.value) == "DESK_SMTPP_CA_FILE is empty: remove the line or name a file"


@pytest.mark.parametrize("blank", BLANKS)
def test_an_empty_imap_ca_file_setting_is_refused_not_read_as_unset(blank: str) -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import run_real_check

    base = {"REAL_IMAP_1_USER": "u", "REAL_IMAP_1_PASSWORD_FILE": "pw"}
    assert run_real_check.imap_settings(base)[0].ssl_context is None  # the line left out is still fine
    with pytest.raises(ValueError) as seen:
        run_real_check.imap_settings({**base, "REAL_IMAP_1_CA_FILE": blank})
    assert str(seen.value) == "REAL_IMAP_1_CA_FILE is empty: remove the line or name a file"
