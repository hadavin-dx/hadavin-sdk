"""Count the demo mails that arrived in a mailbox you own, by the header X-Send-Key. Standard library only
(imaplib over TLS, certificate checked). Prints nothing and returns only counts: no body, no address, no subject is
read (only the one header X-Send-Key is fetched, with PEEK so no message is marked as read).

The password is read from a file at every call (never an argument, never in an error text).
A mail provider's IMAP search on a header is a substring match (and may split a value into words), so the
search only finds the candidates and the exact key is compared here: a count for `L-001` never includes `L-0010`.
`counts_for_keys` searches for each FULL key (never a one-letter prefix) and, if ANY wanted key was found in no
folder that way, also fetches the
headers of each folder's newest messages (at most FALLBACK_SCAN_MAX) and compares them here; per folder and key the
LARGER of the two counts is kept (never fewer than either way saw, so a second delivery is not hidden).
A folder that does not exist on the server is left OUT of the result (not shown as empty), so the caller can say
"could not check this folder" (a provider may name its spam folder in the user's language).
The scan runs only when a key EXPECTED in this mailbox (`expected`, default: every wanted key) was found in no folder:
with two mailboxes, a key that belongs to the other mailbox is never a reason to scan.
One call is bounded as a whole: `total_seconds`, counted from before the connection is opened. The TCP connect (for
each address of the host), the whole TLS handshake (Python counts its time-out for the handshake as a whole, so a
drip of handshake bytes cannot stretch it), every read and every write wait at most the smaller of
`timeout_seconds` and the time left, so no single step runs past the total (the one exception is the look-up of
the host name, which the standard library cannot bound). After the
deadline the connection is closed without a LOGOUT exchange (that would add two more waits). Both times must be finite
numbers above 0 and at most IMAP_SECONDS_MAX, else one fixed refusal line when the settings are made. The connection
checks the certificate chain and the host name:
no value in a settings file can switch that off (code that builds ImapSettings itself may pass its own ssl_context)."""

from __future__ import annotations

import imaplib
import re
import ssl
import time
from collections import Counter
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any, cast

from lead_desk.constants import IMAP_LITERAL_MAX_BYTES, IMAP_SECONDS_MAX, MAIL_SPAM_FOLDER, is_positive_seconds
from lead_desk.contract import SendRefused
from lead_desk.envnum import SettingRefused
from lead_desk.netconnect import connect_bounded
from lead_desk.scrub import secret_boundary
from lead_desk.smtp_outbox import _HOST_NAME
from lead_desk.smtp_provider import read_secret_file
from lead_desk.tls_trust import CaFileRefused, new_verifying_context, require_modern_protocol, require_verifying

_PREFIX = re.compile(r"[A-Za-z0-9._:-]{1,64}")
_HEADER = re.compile(rb"X-Send-Key:[\s]*([^\s]+)", re.IGNORECASE)
IMAP_SSL_PORT = 993
FALLBACK_SCAN_MAX = 300  # headers fetched by the fallback scan of one folder (the newest messages)
KEYS_MAX = 500
TOTAL_SECONDS_DEFAULT = 120.0  # one whole call (login, every search and fetch, every folder)


class ImapCountError(RuntimeError):
    """Fixed text only: never the server's words, never the password or its path."""


class ImapSettingRefused(SettingRefused, ImapCountError):
    """A mailbox setting the desk refuses (a user name that cannot be sent). It is a ValueError (SettingRefused), so
    every script that turns a refused setting into one refusal line also catches it, and still an ImapCountError for
    the callers that count mail. Fixed text only."""


class ImapConnectionError(ImapCountError):
    """The connection failed while connecting or after a successful login (reset, refused, TLS or socket error,
    server hung up): worth one repeat. NOT this class, so never repeated: a failure during the login itself (a
    wrong password may look like a hang-up, and a repeat would be a second login attempt), a step that timed out, a
    failure after the total time limit, a missing folder, a bad key."""


class ImapTotalTimeout(ImapCountError):
    """The call ran past its total time limit (a caller that already holds a full earlier result may keep it)."""


@dataclass(frozen=True)
class ImapSettings:
    host: str
    user: str = field(repr=False)  # an address: kept out of every printout
    password_file: Path = field(repr=False)
    port: int = IMAP_SSL_PORT
    folders: tuple[str, ...] = ("INBOX", MAIL_SPAM_FOLDER)  # inbox and spam are counted apart
    timeout_seconds: float = 30.0  # one network step
    total_seconds: float = TOTAL_SECONDS_DEFAULT  # the whole call
    ssl_context: ssl.SSLContext | None = None  # None = the system authorities, chain and name checked

    def __post_init__(self) -> None:
        """The user name must be plain printable ASCII, not empty and without a space at either end: a line break or
        another control character could add a second IMAP command to the login line, and imaplib sends the user name
        as it is (the password it quotes), so a user of only spaces would send the password with a blank user. A fixed
        text, raised where the settings are made. Inside the name a space, a quote or a backslash is allowed: the name
        is quoted when it is sent (`quote_user`). The host must be a plain host name (the same rule as the mail sender's
        host: ASCII letters, digits, hyphens and dots only, upper case allowed, any other character refused; the name
        that is checked is the very text that is later looked up): a bad name is refused HERE, where the settings are
        made and before anything real happens, and not at the first look-up."""
        if not isinstance(self.host, str) or not self.host.isascii() or not _HOST_NAME.fullmatch(self.host.lower()):
            raise ImapSettingRefused("the mailbox host must be a host name (letters, digits, hyphens and dots)")
        if not self.user or not self.user.isascii() or not self.user.isprintable() or self.user != self.user.strip(" "):
            raise ImapSettingRefused(
                "the mailbox user must be plain printable ASCII text without a space at either end"
            )
        for value in (self.timeout_seconds, self.total_seconds):  # NaN, inf, 0, negative, bool, text, huge: one line
            if not (is_positive_seconds(value) and value <= IMAP_SECONDS_MAX):
                raise ImapSettingRefused(
                    "the mailbox time limits (step and total) must each be a number above 0 and at most "
                    f"{IMAP_SECONDS_MAX:.0f}"
                )


def quote_user(user: str) -> str:
    """The user name as an IMAP quoted string (RFC 3501 section 4.3): a backslash and a quote get a backslash in front,
    the whole name goes between quotes, so a space, a brace or a parenthesis in it is text, never syntax."""
    return '"' + user.replace("\\", "\\\\").replace('"', '\\"') + '"'


_RECV_PIECE = 65536


class _DeadlineReader:
    """The reading side of the connection (replaces imaplib's buffered file). Every network read waits at most
    min(one step, the time left until the TOTAL deadline), so a server that drips one byte every few seconds inside
    one greeting, one reply line or one literal cannot keep the call alive past `total_seconds` (the plain socket
    timeout restarts with every received byte). Past the deadline: ImapTotalTimeout."""

    def __init__(self, owner: _BoundedImap) -> None:
        self._owner = owner
        self._buf = bytearray()
        self._eof = False

    def _fill(self) -> None:
        o = self._owner
        left = o.deadline - time.monotonic()
        if left <= 0:
            raise ImapTotalTimeout(_TOTAL_TEXT)
        o.sock.settimeout(min(o.step_seconds, left))
        try:
            piece = o.sock.recv(_RECV_PIECE)
        except TimeoutError:
            if time.monotonic() >= o.deadline:
                raise ImapTotalTimeout(_TOTAL_TEXT) from None
            raise
        if not piece:
            self._eof = True
        self._buf += piece

    def read(self, size: int = -1) -> bytes:
        while not self._eof and (size < 0 or len(self._buf) < size):
            self._fill()
        n = len(self._buf) if size < 0 else min(size, len(self._buf))
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def readline(self, limit: int = -1) -> bytes:
        while True:
            i = self._buf.find(b"\n")
            if i >= 0:
                end = i + 1
                break
            if (limit >= 0 and len(self._buf) >= limit) or self._eof:
                end = len(self._buf)
                break
            self._fill()
        if limit >= 0:
            end = min(end, limit)
        out = bytes(self._buf[:end])
        del self._buf[:end]
        return out

    def close(self) -> None:
        self._buf.clear()


_TOTAL_TEXT = "the mailbox read took longer than its total time limit"


class _BoundedImap(imaplib.IMAP4_SSL):
    """imaplib reads a server-announced literal of any size in one `read(size)`. Here one read above
    IMAP_LITERAL_MAX_BYTES ends the call (ImapCountError, no repeat), and a read after the total deadline ends it with
    ImapTotalTimeout. The connection is shut at once (deadline set to the past, so `_session` does not send LOGOUT).
    The total deadline is set BEFORE the connection is opened (it covers the server greeting) and is enforced inside a
    single slow line or literal too (`_DeadlineReader`)."""

    deadline: float = float("inf")
    step_seconds: float = 30.0

    def __init__(self, host: str, port: int, *, ssl_context: ssl.SSLContext, timeout: float, deadline: float) -> None:
        self.deadline = deadline
        self.step_seconds = timeout
        super().__init__(host, port, ssl_context=ssl_context, timeout=timeout)

    def _create_socket(self, timeout: float | None) -> Any:
        """The TCP connect and the whole TLS handshake are bounded by the TOTAL deadline. The connect waits at most
        min(one step, the time left) for each address of the host. For the handshake the socket time-out is set to
        the same value just before the wrap; Python's TLS handshake counts that time-out for the handshake AS A WHOLE
        (it does not start again with every received byte, unlike a plain read), so a server that drips one handshake
        byte at a time cannot keep it past that value (tests: a silent and a dripping server). The look-up of the host
        name is bounded the same way (lead_desk.netconnect). None of the time left: ImapTotalTimeout before
        anything is opened. A time-out when the total deadline was the limit is reported as ImapTotalTimeout, a
        time-out of one step as TimeoutError."""
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise ImapTotalTimeout(_TOTAL_TEXT)
        limited_by_total = left <= self.step_seconds
        try:  # the look-up of the host name and the connect, together, in at most min(one step, the time left)
            sock = connect_bounded(self.host, self.port, min(self.step_seconds, left))
        except TimeoutError:
            if limited_by_total:
                raise ImapTotalTimeout(_TOTAL_TEXT) from None
            raise
        left_now = self.deadline - time.monotonic()
        handshake_limited_by_total = left_now <= self.step_seconds
        try:
            sock.settimeout(min(self.step_seconds, max(0.001, left_now)))
            return self.ssl_context.wrap_socket(sock, server_hostname=self.host)
        except OSError as e:
            sock.close()
            if isinstance(e, TimeoutError) and handshake_limited_by_total:
                raise ImapTotalTimeout(_TOTAL_TEXT) from None
            raise

    def open(self, host: str = "", port: int = IMAP_SSL_PORT, timeout: float | None = None) -> None:
        super().open(host, port, timeout)
        self.file = cast("IO[bytes]", _DeadlineReader(self))  # replaces the buffered file of imaplib

    def send(self, data: bytes) -> None:
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise ImapTotalTimeout(_TOTAL_TEXT)
        self.sock.settimeout(min(self.step_seconds, left))
        super().send(data)

    def read(self, size: int) -> bytes:
        if size > IMAP_LITERAL_MAX_BYTES:
            self.deadline = float("-inf")
            raise ImapCountError("the mailbox sent a reply part that is too long")
        if time.monotonic() > self.deadline:
            raise ImapTotalTimeout(_TOTAL_TEXT)
        return super().read(size)

    def readline(self) -> bytes:
        """imaplib reads every reply line here (also an endless run of untagged lines that announce no literal, which
        `read` never sees): past the total deadline the call ends."""
        if time.monotonic() > self.deadline:
            raise ImapTotalTimeout(_TOTAL_TEXT)
        return super().readline()


def bad_folder_name(folder: str) -> bool:
    """True for a folder name this module cannot send: not plain ASCII, a quote, a backslash or a control character
    (IMAP wants other characters in a special encoding; use the ASCII form of the name your provider shows)."""
    return not folder or not folder.isascii() or any(c in '"\\' or ord(c) < 32 for c in folder)  # noqa: PLR2004


@secret_boundary(ImapCountError, "the mailbox could not be read")
def _password(s: ImapSettings) -> str:
    try:
        return read_secret_file(s.password_file, "mailbox password")
    except SendRefused as e:
        raise ImapCountError(str(e)) from None  # a fixed text that names no path


@secret_boundary(ImapCountError, "the mailbox could not be read")  # the server may echo the LOGIN line in its error
def _session(
    s: ImapSettings, folders_work: Callable[[imaplib.IMAP4_SSL], dict[str, dict[str, int]]]
) -> dict[str, dict[str, int]]:
    if any(bad_folder_name(f) for f in s.folders):
        raise ImapCountError("a mailbox folder name has characters this program cannot send (use plain ASCII letters)")
    password = _password(s)
    try:
        ctx = (
            require_verifying(s.ssl_context, "ssl_context")
            if s.ssl_context is not None
            else new_verifying_context()  # imaplib's own None default is an UNVERIFIED context
        )
    except CaFileRefused as e:
        raise ImapCountError(str(e)) from None
    deadline = time.monotonic() + s.total_seconds  # starts BEFORE the connection and the server greeting
    logging_in = False
    try:
        m = _BoundedImap(s.host, s.port, ssl_context=ctx, timeout=s.timeout_seconds, deadline=deadline)
        try:
            try:
                require_modern_protocol(m.sock, "ssl_context")  # before the login line goes out
            except CaFileRefused as e:
                m.deadline = float("-inf")  # no LOGOUT on a connection that is refused
                raise ImapCountError(str(e)) from None
            _tick(m)
            logging_in = True
            m.login(quote_user(s.user), password)
            logging_in = False
            return folders_work(m)
        finally:
            try:
                if time.monotonic() > m.deadline:
                    m.shutdown()  # past the deadline: no LOGOUT round trip, just close the socket
                else:
                    m.logout()
            except (imaplib.IMAP4.error, OSError):
                pass
    except UnicodeError:  # a user name or password the login cannot carry (non-ASCII)
        raise ImapCountError("the mailbox user or password has characters the mailbox login cannot carry") from None
    except (imaplib.IMAP4.abort, OSError) as e:
        if logging_in or isinstance(e, TimeoutError) or time.monotonic() > deadline:
            raise ImapCountError("the mailbox could not be read") from None  # not repeated: see ImapConnectionError
        raise ImapConnectionError("the mailbox could not be read") from None
    except imaplib.IMAP4.error:
        raise ImapCountError("the mailbox could not be read") from None


def counts_by_key(s: ImapSettings, prefix: str) -> dict[str, dict[str, int]]:
    """{folder: {send key: messages}} for every message whose X-Send-Key starts with `prefix`."""
    if not _PREFIX.fullmatch(prefix):
        raise ImapCountError("prefix has characters outside the allowed set")
    return _session(s, lambda m: {f: _count_folder(m, f, prefix) for f in s.folders if _select(m, f)})


def counts_for_keys(
    s: ImapSettings, keys: Collection[str], expected: Collection[str] | None = None, scan: bool = True
) -> dict[str, dict[str, int]]:
    """{folder: {send key: messages}} for exactly the given keys: one search per full key, then (only when some key
    was expected here and not found that way) a bounded scan of the newest headers; every candidate is compared here,
    exactly. `expected` = the keys that should be in THIS mailbox (default: all of `keys`). `scan=False` never runs
    the slow scan (a caller that polls many times asks for it on the first and the last poll only)."""
    wanted = set(keys)
    if not wanted or len(wanted) > KEYS_MAX or not all(_PREFIX.fullmatch(k) for k in wanted):
        raise ImapCountError("keys are empty, too many, or have characters outside the allowed set")
    return _session(s, lambda m: _count_keys(m, s.folders, wanted, wanted if expected is None else set(expected), scan))


def _tick(m: imaplib.IMAP4_SSL) -> None:
    """Called before every network step: past the total deadline the call ends with the fixed error text."""
    if time.monotonic() > getattr(m, "deadline", float("inf")):
        raise ImapTotalTimeout(_TOTAL_TEXT)


def _select(m: imaplib.IMAP4_SSL, folder: str) -> bool:
    _tick(m)
    typ, _ = m.select(f'"{folder}"', readonly=True)
    return typ == "OK"  # a folder that does not exist is left out of the result


def _key_of(m: imaplib.IMAP4_SSL, number: str) -> str | None:
    _tick(m)
    typ, parts = m.fetch(number, "(BODY.PEEK[HEADER.FIELDS (X-SEND-KEY)])")
    if typ != "OK" or not parts or not isinstance(parts[0], tuple):
        return None
    found = _HEADER.search(parts[0][1])
    return found.group(1).decode("ascii", "replace") if found else None


def _ids(m: imaplib.IMAP4_SSL, *criteria: str) -> list[str]:
    _tick(m)
    typ, data = m.search(None, *criteria)
    if typ != "OK" or not data or not data[0]:
        return []
    return [i.decode("ascii") for i in data[0].split()]


def _search_keys(m: imaplib.IMAP4_SSL, wanted: set[str], scan: bool) -> dict[str, int]:
    """Messages per wanted key in the selected folder. scan=False: one search per full key. scan=True: the fallback,
    the headers of the folder's newest FALLBACK_SCAN_MAX messages compared here."""
    found: list[str] = []
    if scan:
        for i in _ids(m, "ALL")[-FALLBACK_SCAN_MAX:]:
            if (got := _key_of(m, i)) in wanted:
                found.append(str(got))
    else:
        seen: set[str] = set()
        for k in sorted(wanted):
            for i in _ids(m, "HEADER", "X-Send-Key", f'"{k}"'):
                if i not in seen:
                    seen.add(i)
                    if (got := _key_of(m, i)) in wanted:
                        found.append(str(got))
    return dict(Counter(found))


def _count_keys(
    m: imaplib.IMAP4_SSL, folders: Sequence[str], wanted: set[str], expected: set[str], scan: bool = True
) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for f in folders:
        if _select(m, f):
            out[f] = _search_keys(m, wanted, scan=False)
    unseen = expected - {k for per in out.values() for k in per}  # an expected key seen nowhere: the search may split
    if scan and unseen:  # values
        for f in out:
            _select(m, f)
            for k, n in _search_keys(m, wanted, scan=True).items():
                out[f][k] = max(out[f].get(k, 0), n)
    return out


def _count_folder(m: imaplib.IMAP4_SSL, folder: str, prefix: str) -> dict[str, int]:
    tally: Counter[str] = Counter()
    for i in _ids(m, "HEADER", "X-Send-Key", f'"{prefix}"'):
        key = _key_of(m, i)
        if key is not None and key.startswith(prefix):
            tally[key] += 1
    return dict(tally)


def counts_by_inbox(
    inboxes: Sequence[ImapSettings],
    prefix: str,
    keys: Collection[str] | None = None,
    expected_by_inbox: Sequence[Collection[str]] | None = None,
    scan: bool = True,
) -> list[dict[str, dict[str, int]]]:
    """One result per configured mailbox, in the same order (one login each): `counts_for_keys` when `keys` is given
    (with `expected_by_inbox[n]` as mailbox n's expected keys when given; `scan` as in `counts_for_keys`), else
    `counts_by_key` by prefix. A failure names no mailbox detail: it stays the fixed ImapCountError text."""
    if keys is None:
        return [counts_by_key(s, prefix) for s in inboxes]
    return [
        counts_for_keys(s, keys, None if expected_by_inbox is None else expected_by_inbox[n], scan)
        for n, s in enumerate(inboxes)
    ]
