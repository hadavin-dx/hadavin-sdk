import sys, socket, threading, errno, urllib.request, urllib.error
sys.path[:0]=[sys.argv[1]+"/src"]
from lead_desk import server
S=server._Server
from http.server import BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(204); self.send_header('Content-Length','0'); self.end_headers()
    def log_message(self,*a): pass
print("MRO", [c.__name__ for c in S.__mro__])
print("attrs", S.allow_reuse_address, S.request_queue_size, hasattr(S,"server_bind"), S.server_bind is S.__mro__[S.__mro__.index(server._ExclusiveBind)].server_bind)
a=S(("127.0.0.1",0),H); port=a.server_address[1]
try: S(("127.0.0.1",port),H); print("second bind: NO ERROR")
except OSError as e: print("second bind errno", e.errno==errno.EADDRINUSE, e.errno)
print("server_name/port", a.server_name, a.server_port==port)
t=threading.Thread(target=a.serve_forever,daemon=True); t.start()
try: print("status", urllib.request.urlopen(f"http://127.0.0.1:{port}/x".replace("htt"+"p","htt"+"p"),timeout=3).status)
except urllib.error.HTTPError as e: print("request answered", e.code)
else: print('request answered ok')
a.shutdown(); a.server_close(); t.join(3)
b=S(("127.0.0.1",port),H); print("rebind ok", b.server_address[1]==port); b.server_close()
# faked win32: options set before bind
calls=[]
class Sock:
    def __init__(s,real): s.r=real
    def setsockopt(s,*x): calls.append(("setsockopt",x[1]==getattr(socket,"SO_EXCLUSIVEADDRUSE",-1) , x[2])); 
    def bind(s,*x): calls.append(("bind",)); return s.r.bind(*x)
    def __getattr__(s,n): return getattr(s.r,n)
import unittest.mock as m
with m.patch.object(server.sys,"platform","win32"), m.patch.object(socket,"SO_EXCLUSIVEADDRUSE",0x7fff,create=True):
    class W(S): pass
    orig=S.__init__
    def fake_bind(self):
        self.socket=Sock(self.socket); S.server_bind(self)
    try:
        w=S(("127.0.0.1",0),H,bind_and_activate=False)
        w.socket=Sock(w.socket)
        w.server_bind()
        print("win32 calls", calls); w.server_close()
    except Exception as e: print("win32 err", type(e).__name__, e)
