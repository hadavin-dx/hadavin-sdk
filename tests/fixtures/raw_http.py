"""A tiny local HTTP server that sends EXACT bytes (status line, headers, body) and counts requests.

``tests/fixtures/http_fake.py`` builds a well-formed reply with ``http.server``, so it cannot send a status line like
``HTTP/1.1 777 <text>``, a 70,000-byte header or ``HTTP/1.1 1000 X``. This server writes the bytes a test gives it, one
reply per request, then closes the connection. It reads the whole request first (headers and ``Content-Length`` body), so
the client never sees a reset before it has finished sending.
"""

from __future__ import annotations

import socket
import threading
from typing import Self


class RawServer:
    def __init__(self, replies: list[bytes] | None = None, *, repeat: bytes | None = None) -> None:
        self.replies = list(replies or [])
        self.repeat = repeat  # sent for every request once ``replies`` is empty
        self.requests = 0
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(16)
        self._sock.settimeout(0.05)
        self.url = f"http://127.0.0.1:{self._sock.getsockname()[1]}"
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)
        self._sock.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            threading.Thread(target=self._one, args=(conn,), daemon=True).start()

    @staticmethod
    def _read_request(conn: socket.socket) -> bool:
        conn.settimeout(5)
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(65536)
            if not chunk:
                return False
            data += chunk
        head, _, rest = data.partition(b"\r\n\r\n")
        length = 0
        for line in head.split(b"\r\n")[1:]:
            name, _, value = line.partition(b":")
            if name.strip().lower() == b"content-length":
                length = int(value.strip() or 0)
        while len(rest) < length:
            chunk = conn.recv(65536)
            if not chunk:
                break
            rest += chunk
        return True

    def _one(self, conn: socket.socket) -> None:
        try:
            if not self._read_request(conn):
                return
            with self._lock:
                self.requests += 1
                reply = self.replies.pop(0) if self.replies else self.repeat
            if reply is not None:
                try:
                    conn.sendall(reply)
                except OSError:
                    pass  # the client gave up (a 70,000-byte header line): the count is already kept
        except OSError:
            pass
        finally:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conn.close()


def reply(status_line: str, headers: dict[str, str] | None = None, body: bytes = b"") -> bytes:
    """Exact reply bytes: ``status_line`` is sent as written (``"HTTP/1.1 777 TEXT"``)."""
    lines = [status_line, *(f"{k}: {v}" for k, v in (headers or {}).items())]
    if not any(k.lower() == "content-length" for k in (headers or {})):
        lines.append(f"Content-Length: {len(body)}")
    lines.append("Connection: close")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1") + body
