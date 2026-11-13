import glob, json, re, statistics as st, collections, sys
L="/home/user/work/q4-logs"
def mm(v): v=sorted(v); return f"{v[0]:g} / {st.median(v):g} / {v[-1]:g} (n={len(v)})"
print("== pytest measure_burst")
for N,R in ((150,0),(300,0),(300,1)):
    for P in (1,2):
        fs=sorted(glob.glob(f"{L}/burst-{N}-r{R}-p{P}-*.log"))
        if not fs: continue
        ref=[];res=[];loads=[]
        for f in fs:
            t=open(f).read(); m=re.search(r"first_try_refused=(\d+) status_counts=(\{[^}]*\})",t)
            res.append("PASS" if "1 passed" in t else "FAIL"); loads.append(re.search(r"load_before=(\S+)",t).group(1))
            if m: ref.append(int(m.group(1)))
        print(f"N={N} retry={R} pass{P}: results={res} first_try_refused={mm(ref) if ref else 'not printed'} load1_before={loads}")
print("== load driver")
for P in (1,2):
    for sc in ("burst_300","rate_100_10","dupmix_1000_0.3_200"):
        fs=sorted(glob.glob(f"{L}/drv-{sc}-p{P}-?.log"))
        if not fs: continue
        ds=[];dr=[];lag=[];r503=[];oc=[];ac=[];ld=[]
        for f in fs:
            t=open(f).read()
            ds.append(float(re.search(r"driver_seconds=([\d.]+)",t).group(1))); dr.append(float(re.search(r"drain_after_driver_end_seconds=([\d.]+)",t).group(1)))
            m=re.search(r"REQS (\d+) TRIES (\d+) CODES (\{.*?\}) saw503 (\d+) end503 (\d+) accepted (\d+) maxlag ([\d.]+)",t)
            lag.append(float(m.group(7))); r503.append(f"{int(m.group(4))}/{m.group(1)}req,tries={m.group(2)}"); ac.append(f"{m.group(6)}/{m.group(1)}")
            oc.append(int(re.search(r"OUTBOX_COUNT (\d+)",t).group(1))); ld.append(re.search(r"load_before=(\S+)",t).group(1))
        print(f"pass{P} {sc}: driver_s={mm(ds)} drain_after_end_s={mm(dr)} maxlag_s={mm(lag)} saw503={r503} accepted={ac} outbox={oc} load1_before={ld}")
print("== classify")
for P in (1,2):
    try: rows=[json.loads(l) for l in open(f"{L}/classify-p{P}.jsonl") if l.startswith("{")]
    except FileNotFoundError: continue
    by=collections.defaultdict(list)
    for r in rows: by[r["N"]].append(r)
    for n,rs in by.items(): print(f"pass{P} N={n}: "+"; ".join(f"{r['outcomes']}" for r in rs)+f" load1={[r['load1'] for r in rs]}")
print("== proto")
for P in (1,2):
    try: rows=[json.loads(l) for l in open(f"{L}/proto-p{P}.jsonl") if l.startswith("{")]
    except FileNotFoundError: continue
    by=collections.defaultdict(list)
    for r in rows: by[r["test"]].append(r)
    for t,rs in by.items():
        keys=[k for k in rs[0] if k not in("test","pass","rep","claim","load1","stdout","body","ss")]
        print(f"pass{P} {t}: "+" | ".join(f"{k}={[r.get(k) for r in rs]}" for k in keys)+f" load1={[r['load1'] for r in rs]}")
