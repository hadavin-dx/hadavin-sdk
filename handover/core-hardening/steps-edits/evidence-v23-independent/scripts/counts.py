import re
D='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
rd=lambda n:open(D+n,encoding='utf-8').read()
def st(name,t):
    L=t.splitlines(); w=[len(l.split()) for l in L]
    print('%-28s lines %4d  words %5d  bytes %6d  lines>100w %2d  >200w %2d  longest %3d w  UNVERIFIED %3d  FREEZE %3d'%(name,len(L),len(t.split()),len(t.encode()),sum(x>100 for x in w),sum(x>200 for x in w),max(w),t.count('UNVERIFIED'),t.count('FREEZE')))
pairs=[('OWNER-SHEET-v22.md','OWNER-SHEET-v23.md'),('LEAD-RELEASE-NOTE-v6.md','LEAD-RELEASE-NOTE-v7.md'),('v22-OPEN-FOR-LEAD.md','v23-OPEN-FOR-LEAD.md'),('v22-CHANGES.md','v23-CHANGES.md')]
for a,b in pairs: st(a,rd(a)); st(b,rd(b)); print()
S=rd('OWNER-SHEET-v23.md')
print('markers: [[A: %d  [[B: %d  ]] %d  [[ total %d'%(S.count('[[A:'),S.count('[[B:'),S.count(']]'),S.count('[[')))
def build(s,keep):
    drop='B' if keep=='A' else 'A'
    s=re.sub(r'\[\[%s:.*?\]\]'%drop,'',s,flags=re.S)
    return re.sub(r'\[\[%s:(.*?)\]\]'%keep,r'\1',s,flags=re.S)
# independent builder: scan manually for markers (non-regex) to confirm nesting-free
def scan(s):
    spans=[];i=0
    while True:
        i=s.find('[[',i)
        if i<0: break
        j=s.find(']]',i)
        k=s.find('[[',i+2)
        spans.append((s[i+2],i,j,k!=-1 and k<j))
        i=j+2
    return spans
sp=scan(S); print('marker spans',len(sp),'kinds',{k:sum(1 for x in sp if x[0]==k) for k in 'AB'},'nested',sum(1 for x in sp if x[3]))
for k in 'AB':
    v=build(S,k); L=v.splitlines()
    print('variant %s builds: words %d lines %d markers left %d'%(k,len(v.split()),len(L),v.count('[[')+v.count(']]')))
    print('   section headings',len(re.findall(r'^## ',v,re.M)),'rule ids',re.findall(r'^\| (R\d+) \|',v,re.M))
    print('   double spaces created by removal:',len(re.findall(r'[^ ]  +[^ ]',v))-len(re.findall(r'[^ ]  +[^ ]',build(S,'A' if k=='B' else 'B'))) if False else 'n/a')
    # check text around removed spans reads: print the variant A/B text of each marker region (first 80 chars)
for kk,x in enumerate(sp): print('span',kk,x[0],'chars',x[2]-x[1],'|',S[x[1]:x[1]+70].replace('\n',' '))
# dangling words after removal: for variant A and B print the 40 chars around each removal point
for k in 'AB':
    drop='B' if k=='A' else 'A'
    v=build(S,k)
    print('--- variant',k,'joins:')
    for m in re.finditer(r'\[\[%s:.*?\]\]'%drop,S,flags=re.S):
        pre=build(S[:m.start()],k)[-45:].replace('\n',' '); post=build(S[m.end():],k)[:45].replace('\n',' ')
        print('   ...%s |REMOVED| %s...'%(pre,post))
