import re,sys
v8=open('CORE-PR-HANDOFF-v8.md',encoding='utf-8').read().split('\n')
sec=lambda a,b:'\n'.join(v8[a-1:b])
body=sec(550,636)
def sub1(s,old,new):
    assert s.count(old)==1,(old,s.count(old)); return s.replace(old,new)
body=sub1(body,"- **Siblings (S1 also covers):**","- **Siblings (K1 also covers):**")
body=sub1(body,"I did not search for a test forbidding `audit` importing a neutral module; E0-1 runs the guard.","Searched in v9 (`evidence-handoff-v9/raw-greps-v9.txt`, grep `fileguard` over `src` and `tests`: no hit; `tests/test_lockin_guard.py` lists vendor modules only, e.g. lines 42-51): no test forbids `audit` importing a neutral module. E0-O1 still runs the guard.")
body=sub1(body,"### 4.6 Audit claims","### O-4.6 Audit claims")
for a,b in [("### 4.7 ","### O-4.7 "),("### 4.8 ","### O-4.8 "),("### 4.9 ","### O-4.9 "),("### 4.10 ","### O-4.10 "),("### 4.11 ","### O-4.11 ")]:
    body=sub1(body,a,b)
body=body.replace("(PR-2 first and alone)","(PR-2 first and alone)")
head=open('/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/other_head.md',encoding='utf-8').read()
tail=open('/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/other_tail.md',encoding='utf-8').read()
open('CORE-PR-HANDOFF-v9-other-tracks.md','w',encoding='utf-8').write(head+'\n'+body+'\n\n'+tail)
