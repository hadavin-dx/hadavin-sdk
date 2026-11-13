import os, socket, ipaddress
_LOG = os.environ.get("RV_LOG")
def _log(kind, target, verdict):
    if _LOG:
        with open(_LOG, "a") as f:
            f.write(f"{os.getpid()} {kind} {target!r} {verdict}\n")
def _is_lo(h):
    if isinstance(h, bytes): h = h.decode()
    if h in ("localhost", None, ""): return True
    h = h.strip("[]")
    try: return ipaddress.ip_address(h).is_loopback
    except ValueError: return False
_gai = socket.getaddrinfo
def getaddrinfo(host, *a, **k):
    ok = _is_lo(host)
    _log("getaddrinfo", host, "allow" if ok else "BLOCK")
    if not ok: raise OSError("rv-block: non-loopback name resolution " + str(host))
    return _gai(host, *a, **k)
socket.getaddrinfo = getaddrinfo
_c = socket.socket.connect
def connect(self, addr):
    h = addr[0] if isinstance(addr, tuple) else addr
    ok = isinstance(addr, str) or _is_lo(h)
    _log("connect", addr, "allow" if ok else "BLOCK")
    if not ok: raise OSError("rv-block: non-loopback connect")
    return _c(self, addr)
socket.socket.connect = connect
_ce = socket.socket.connect_ex
def connect_ex(self, addr):
    h = addr[0] if isinstance(addr, tuple) else addr
    ok = isinstance(addr, str) or _is_lo(h)
    _log("connect_ex", addr, "allow" if ok else "BLOCK")
    if not ok: raise OSError("rv-block: non-loopback connect_ex")
    return _ce(self, addr)
socket.socket.connect_ex = connect_ex

