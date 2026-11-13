"""First-try outcome of N simultaneous POST /leads (no retry): status codes and socket error classes. usage: q4_classify.py PORT PASS REPS N [N...]"""
import json, os, socket, subprocess, sys, tempfile, threading, time, collections, urllib.request
PB=int(sys.argv[1]); PASS=sys.argv[2]; REPS=int(sys.argv[3]); NS=[int(x) for x in sys.argv[4:]]
tmp=tempfile.mkdtemp(prefix="q4cls.")
env=dict(os.environ, DESK_DB_PATH=f"{tmp}/desk.db", DESK_PORT=str(PB), DESK_FAKES_PORT=str(PB+1), TMPDIR=tmp)
fk=subprocess.Popen([sys.executable,"-m","demo_only.fakes_server","--outbox","keyed","--port",str(PB+1)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
dk=subprocess.Popen([sys.executable,"-m","lead_desk.server"],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
for _ in range(100):
    try: urllib.request.urlopen(f"http://127.0.0.1:{PB}/counts",timeout=2); break
    except Exception: time.sleep(0.1)
def one(i,tag,bar,res):
    body=json.dumps({"source":"form","source_ref":f"{tag}-{i}","payload":{"email":f"{tag}{i}@example.test","name":"A","message":"m"}}).encode()
    req=(f"POST /leads HTTP/1.1\r\nHost: 127.0.0.1:{PB}\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode()+body
    bar.wait()
    try:
        s=socket.create_connection(("127.0.0.1",PB),timeout=60); s.sendall(req); buf=b""
        while True:
            c=s.recv(65536)
            if not c: break
            buf+=c
        res[i]=buf.split(b"\r\n",1)[0].decode("latin1")[9:12] or "EMPTY"
    except Exception as e: res[i]=type(e).__name__
try:
    for n in NS:
        for rep in range(1,REPS+1):
            tag=f"c{PASS}n{n}r{rep}"; bar=threading.Barrier(n); res={}
            ths=[threading.Thread(target=one,args=(i,tag,bar,res)) for i in range(n)]
            l0=open("/proc/loadavg").read().split()[0]; t=time.monotonic()
            [x.start() for x in ths]; [x.join() for x in ths]
            print(json.dumps({"test":"first_try_classify","N":n,"pass":PASS,"rep":rep,"load1":l0,"seconds":round(time.monotonic()-t,2),"outcomes":dict(collections.Counter(res.values()))}),flush=True)
            time.sleep(4)
finally:
    for p in (dk,fk):
        p.terminate()
        try: p.wait(10)
        except Exception: p.kill()
