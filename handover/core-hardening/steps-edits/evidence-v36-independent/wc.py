import re,sys
for k in 'AB':
    names=['OWNER-SHEET-v36-%s.md','OWNER-CARD-v36-%s.md','OWNER-APPENDIX-v36-%s.md','OWNER-FILM-PERSON-v36.md','OWNER-HELPER-v36.md']
    tot=0; tot2=0; tot3=0
    for n in names:
        b=open(n%k if '%s' in n else n,'rb').read()
        t=b.decode('utf-8')
        a=len(re.findall(r'\S+',t))            # my counter: runs of non-space
        c=len([w for w in re.split(r'[ \t\r\n\f\v  -   　]+',t) if w])  # explicit whitespace set
        d=len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'_.\-/:]*",t))  # token-ish
        print(k,n%k if '%s' in n else n,'nonspace',a,'ws-set',c,'alnum-tokens',d,'wc',len(t.split()))
        tot+=a;tot2+=c;tot3+=d
    print(k,'TOTAL nonspace',tot,'ws-set',tot2,'alnum',tot3)
