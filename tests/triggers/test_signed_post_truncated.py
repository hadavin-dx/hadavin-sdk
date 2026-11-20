"""`signed_post` of the crash launcher: a truncated 2xx answer is no complete ack."""

from __future__ import annotations

import socket
import threading

from tests.triggers import crash_launcher


def _serve(payload: bytes):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def run():
        conn, _ = srv.accept()
        try:
            conn.settimeout(5)
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            head, _, rest = data.partition(b"\r\n\r\n")
            for line in head.split(b"\r\n"):
                if line.lower().startswith(b"content-length:"):
                    need = int(line.split(b":")[1])
                    while len(rest) < need:
                        rest += conn.recv(4096)
            conn.sendall(payload)
        finally:
            conn.close()
            srv.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return srv.getsockname()[1], thread


def _post(payload: bytes):
    port, thread = _serve(payload)
    out = crash_launcher.signed_post(port, b'{"a": 1}', "secret")
    thread.join(10)
    return out


def test_status_line_only_is_incomplete():
    assert _post(b"HTTP/1.1 200 OK\r\n") == (None, b"IncompleteResponse")


def test_short_body_is_incomplete():
    out = _post(b"HTTP/1.1 200 OK\r\nContent-Length: 50\r\n\r\n" + b"x" * 10)
    assert out == (None, b"IncompleteResponse")


def test_no_content_length_is_incomplete():
    out = _post(b"HTTP/1.1 200 OK\r\n\r\nabc")
    assert out == (None, b"IncompleteResponse")


def test_complete_answer_passes():
    out = _post(b"HTTP/1.1 202 Accepted\r\nContent-Length: 5\r\n\r\nhello")
    assert out == (202, b"hello")
