"""Round 7C, mail pass 6 finding F-C: the reply cap of the mail sender covers the WHOLE reply, not only an unfinished
line. A multi-line reply ('250-x' lines, then '250 done') over the cap is refused whole; a short one still reads."""

from __future__ import annotations

import socket
import threading

import pytest

from lead_desk.smtp_outbox import _REPLY_MAX_BYTES, _Budget, _Closed, _read_reply


def _read_from(data: bytes) -> int:
    a, b = socket.socketpair()

    def feed() -> None:
        try:
            b.sendall(data)
        except OSError:
            pass  # the reader refused and closed: fine

    t = threading.Thread(target=feed, daemon=True)
    t.start()
    try:
        return _read_reply(a, _Budget(5.0), bytearray())
    finally:
        a.close()
        b.close()
        t.join(5)


def test_a_multi_line_reply_over_the_cap_is_refused_whole() -> None:
    one_line = b"250-" + b"x" * 64 + b"\r\n"
    lines = one_line * (_REPLY_MAX_BYTES // 70 * 4)
    with pytest.raises(_Closed):
        _read_from(lines + b"250 done\r\n")


# CONTROL (r7e, with the r7c helper): passes on r7b, a pin; mutant NOT run, the intended one:
# a reply under the cap is refused.
def test_a_multi_line_reply_under_the_cap_is_read() -> None:
    assert _read_from(b"250-a\r\n250-b\r\n250 done\r\n") == 250
