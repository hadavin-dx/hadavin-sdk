import re,itertools,sys
sys.path.insert(0,'/tmp/work/sn-og')
from tools import scrub_n8n_export as s
P=s.MAIL.pattern
M6=P.replace(r'example\.(?:com|test|invalid)(?![\w-]|\.[\w-]))"'[:0]+'','')  # placeholder
# M6: drop end guard after the allowed name in the OUTER lookahead's final position (inner)
idx=P.rindex(r'(?![\w-]|\.[\w-])')
M6=P[:idx]+P[idx+len(r'(?![\w-]|\.[\w-])'):]
M10=P[:idx]+r'(?![\w-])'+P[idx+len(r'(?![\w-]|\.[\w-])'):]
M10b=P.replace(r'(?![\w-]|\.[\w-])',r'(?![\w-])')
for name,pat in (("M6",M6),("M10",M10),("M10both",M10b)):
    r=re.compile(pat); d=0
    cases=["a@example.com.evil.test","a@example.com-x","a@sub.example.com.","a@example.com.","a@example.com.x"]
    for c in cases:
        if r.sub("<>",c)!=s.MAIL.sub("<>",c): print(name,"DIFF listed",c, r.sub("<>",c), s.MAIL.sub("<>",c))
    al=["a","@",".","-","example.","com","test","invalid","_","x"]
    n=0
    for L in range(7):
        for p in itertools.product(al,repeat=L):
            t="".join(p); n+=1
            if r.sub("<>",t)!=s.MAIL.sub("<>",t) or [m.span() for m in r.finditer(t)]!=[m.span() for m in s.MAIL.finditer(t)]:
                d+=1
                if d<4: print(name,"DIFF",repr(t))
    print(name,"texts",n,"diffs",d)
