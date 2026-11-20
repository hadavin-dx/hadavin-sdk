# round 5 scratch (a record, run from the repository root: m2.py puts "." on sys.path); it reuses the definitions of m2.py next to it
import sys, time
from pathlib import Path
sys.argv=[__file__]
exec(Path(__file__).with_name("m2.py").read_text().split('if __name__')[0])
def run(name, reg, probe):
    defaults.SPELLED_MAX_WORK = 4_000_000
    r = R._Redactor(None); r.find(reg)
    forms = sum(1 for _ in r._spelled_at)
    r.sweep("")
    defaults.SPELLED_MAX_WORK = 10**9
    def work(p):
        lo, hi = 0, 10**9
        def refused(limit):
            defaults.SPELLED_MAX_WORK = limit
            try: r._spelled_sweep(p, None); return False
            except runmap.InputTooLarge: return True
        while hi - lo > 1024:
            mid = (lo+hi)//2
            if refused(mid): lo = mid
            else: hi = mid
        defaults.SPELLED_MAX_WORK = 10**9
        return hi
    w = work(probe)
    t0 = time.thread_time(); r._spelled_sweep(probe, None); dt = time.thread_time() - t0
    print(f"{name}: reg {len(reg)} chars, forms {forms}, probe {len(probe)} chars, work ~{w}, scan {dt:.3f} s ({dt/max(w,1)*1e6:.2f} us/unit)")
reg = A(300)
probe = "\n".join(f"Cookie: _ga=GA1.2{'x'*(k%300)}; theme=dark; sid=<JWT_1>" for k in range(1700))
run("honest cookie copies", reg, probe[:262144])
u = str(uuid.UUID(int=random.Random(1).getrandbits(128)))
run("honest signed ids", B(300), "\n".join(f"copy <UUID_1>.sig{k%300}" for k in range(8000))[:262144])
# hostile: forms a^k<S1>Z^m
K, M = 300, 60
hreg = "\n".join(f"password={'a'*k}<SECRET_1>{'Z'*M}" for k in range(1, K+1))
tp = ("a"*K + "<SECRET_1>" + "Z"*(M-1) + "\n")
hprobe = (tp * (130000//len(tp)))
def hostile():
    defaults.SPELLED_MAX_WORK = 4_000_000
    r = R._Redactor({"<SECRET_1>": "ab9x"}); r.find(hreg); r.sweep("")
    defaults.SPELLED_MAX_WORK = 10**9
    t0=time.thread_time(); r._spelled_sweep(hprobe, None); dt=time.thread_time()-t0
    print("hostile (uncapped)", len(hreg), len(hprobe), round(dt,3), "s")
    defaults.SPELLED_MAX_WORK = 4_000_000
    t0=time.thread_time()
    try: r._spelled_sweep(hprobe, None)
    except runmap.InputTooLarge as e: print("refused", e, round(time.thread_time()-t0,3), "s")
hostile()
