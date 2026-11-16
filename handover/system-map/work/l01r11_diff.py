import re
P={'L01':'work/L01-owner-acceptance-line.md','OV':'OWNER-VIEW.md','LP':'LEAD-PAGE.md'}
T=["Stamp rule","Print rule","Precondition 1","What counts as written","Key rule","Failed-check rule","Deadline rule","More-time rule","Conditions for the approve line","Reply list","Status rule"]
D={}
for k,f in P.items():
    ls=open(f).read().split('\n'); D[k]={}
    for t in T:
        m=[l for l in ls if re.match(r'^\W*(\*\*)?'+re.escape(t),l)]
        D[k][t]=m
for t in T:
    v=[tuple(D[k][t]) for k in P]
    print(t,[len(x) for x in v],'identical' if len(set(v))==1 and v[0] else 'DIFF/MISSING')
