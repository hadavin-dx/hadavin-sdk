import re
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
S=open(DIR+'OWNER-SHEET-v23.md',encoding='utf-8').read()
L=S.splitlines()
a=[i for i,l in enumerate(L) if l.startswith('### THE CARD')][0]; b=[i for i,l in enumerate(L) if l.startswith('### The rules')][0]
print('card lines %d-%d (1-based); card words %d; sheet words %d'%(a+1,b,len(' '.join(L[a:b]).split()),len(S.split())))
tot=0
for i,l in enumerate(L):
    if a<=i<b: continue
    ms=[m for m in re.finditer(r'\bthe card\b|\bcard (?:step|list|Part)s?\b|\bcard\b',l)]
    cm=[m for m in re.finditer(r'\bcancel\w*|\bproof|\bproved?\b|\bpress the cancel|\bN minus K',l,re.I)]
    if ms or cm:
        tot+=1
        print('--- line %d (%d card mentions, %d cancel/proof words): %s'%(i+1,len(ms),len(cm),l[:60]))
        for m in ms: print('   CARD  ...%s...'%l[max(0,m.start()-70):m.end()+70])
        for m in cm: print('   CANCEL...%s...'%l[max(0,m.start()-60):m.end()+60])
print('lines',tot)
