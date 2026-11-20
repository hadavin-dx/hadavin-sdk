import sys, time, uuid, random, importlib, collections
sys.path.insert(0, ".")
from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap
importlib.import_module("hadavin_sdk.guard.redact"); R = sys.modules["hadavin_sdk.guard.redact"]
jwt = "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiJ1c2VyMSJ9" + "." + "c2lnbmF0dXJlMTIzNDU2Nzg5"
def A(n):
    return "\n".join([f"GET /a token={jwt}"] + [f"Cookie: _ga=GA1.2{'x'*k}; theme=dark; sid={jwt}" for k in range(n)])
def B(n):
    u = str(uuid.UUID(int=random.Random(1).getrandbits(128)))
    return "\n".join(f"password={u}.sig{k}" for k in range(n))
def work_of(text, copies=1):
    """units of work the scan needs on the text `find` leaves, by bisecting the limit"""
    def refused(limit):
        defaults.SPELLED_MAX_WORK = limit
        r = R._Redactor(None); out = r.find(text)
        try: r._spelled_sweep(out, None); return False
        except runmap.InputTooLarge: return True
    lo, hi = 0, 10**9
    saved = 4_000_000
    if refused(hi): return None
    while hi - lo > 1024:
        mid = (lo + hi) // 2
        if refused(mid): lo = mid
        else: hi = mid
    defaults.SPELLED_MAX_WORK = saved
    return hi
def tokens(text):
    r = R._Redactor(None); out = r.find(text); return len(R._PLACEHOLDER.findall(out))
if __name__ == "__main__":
    for name, t in (("A300", A(300)), ("A1500 (200KB)", A(1500)), ("B300", B(300)), ("B5000", B(5000))):
        r=R._Redactor(None); out=r.find(t)
        defaults.SPELLED_MAX_WORK = 4_000_000; t0=time.thread_time(); r.sweep(out); dt=time.thread_time()-t0
        print(name, len(t), "tokens", tokens(t), "work<=", work_of(t), "sweep s", round(dt,3), "jwt left", jwt in out)
