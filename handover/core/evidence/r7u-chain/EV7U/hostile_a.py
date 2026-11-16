import socket, sys, os, tempfile
from pathlib import Path
H="/home/user/build/rr6/out/EV7U/hcopy"
sys.path[:0]=[H+"/src",H]
from http.server import BaseHTTPRequestHandler
from demo_only.bad_request import QuietServer
from demo_only.fake_hubspot import FakeHubspot, HubspotState, serve
from demo_only.fakes_server import make_fakes_server, FakesServer
from demo_only import fake_model_server as fm
from demo_only.fake_imap import FakeImap
from demo_only.fake_smtp_tls import FakeSmtp, make_cert
tmp=Path(tempfile.mkdtemp(dir=os.environ["TMPDIR"]))
cert=make_cert(tmp,"localhost")
print("make_cert:", "ok" if cert else "NONE (no openssl)")
made=[]; binds=[]
orig=socket.socket.__init__; ob=socket.socket.bind
def spy(self,*a,**k): made.append(1); orig(self,*a,**k)
def bspy(self,addr): binds.append(addr); return ob(self,addr)
socket.socket.__init__=spy; socket.socket.bind=bspy
def closeit(r):
    objs=r if isinstance(r,tuple) else (r,)
    for o in objs:
        for m in ("server_close","close"):
            if hasattr(o,m):
                try: getattr(o,m)(); break
                except Exception: pass
def attempt(name,fn):
    made.clear(); binds.clear()
    try:
        r=fn(); res="ACCEPTED"
        try:
            addr=r.server_address if hasattr(r,"server_address") else (r[0].server_address if isinstance(r,tuple) and hasattr(r[0],"server_address") else None)
        except Exception: addr=None
        res+=f" bound={binds[:] or addr}"
        closeit(r)
    except ValueError as e: res="REFUSED ValueError"
    except Exception as e: res="OTHER "+type(e).__name__+":"+str(e)[:70]
    print(f"{name:34s} sockets_made={len(made):d} -> {res}")
hosts=["0.0.0.0","192.0.2.1","","::","example.com",None," ","LOCALHOST","localhost.","[::]","0","127.1","::ffff:127.0.0.1","[::1]",b"127.0.0.1"]
c,k=cert if cert else (Path("/nonexistent/c"),Path("/nonexistent/k"))
for h in hosts:
    print("== host",repr(h))
    attempt("QuietServer",lambda h=h:QuietServer((h,0),BaseHTTPRequestHandler))
    attempt("FakeHubspot",lambda h=h:FakeHubspot((h,0),BaseHTTPRequestHandler))
    attempt("FakesServer",lambda h=h:FakesServer((h,0),BaseHTTPRequestHandler))
    attempt("hubspot serve()",lambda h=h:serve(HubspotState("k"),h))
    attempt("make_fakes_server",lambda h=h:make_fakes_server(host=h))
    attempt("make_model_server",lambda h=h:fm.make_model_server(host=h))
    attempt("FakeImap",lambda h=h:FakeImap(c,k,h,{"INBOX":[]}))
    attempt("FakeSmtp",lambda h=h:FakeSmtp(c,k,h))
