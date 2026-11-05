import socket
import threading

import pytest


def test_non_loopback_connect_is_refused():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(RuntimeError, match="offline"):
        s.connect(("192.0.2.1", 80))
    s.close()


def test_loopback_connect_is_allowed():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    t = threading.Thread(target=lambda: srv.accept()[0].close())
    t.start()
    c = socket.socket()
    c.connect(("127.0.0.1", srv.getsockname()[1]))
    c.close()
    t.join()
    srv.close()
