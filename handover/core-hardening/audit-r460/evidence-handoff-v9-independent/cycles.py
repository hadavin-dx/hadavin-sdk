import ast,os,sys
ROOT='/home/user/hadavin-sdk/src'
PKG='hadavin_sdk'
mods={}
for d,_,fs in os.walk(ROOT+'/'+PKG):
    for f in fs:
        if f.endswith('.py'):
            p=os.path.join(d,f); rel=os.path.relpath(p,ROOT)[:-3].split(os.sep)
            isinit = rel[-1]=='__init__'
            if isinit: rel=rel[:-1]
            mods['.'.join(rel)]=(p,isinit)
def edges(include_tc, include_func, parent_edges):
    E={m:set() for m in mods}
    for m,(p,isinit) in mods.items():
        tree=ast.parse(open(p,encoding='utf-8').read())
        base=m if isinit else m.rpartition('.')[0]
        def tc(n): # is `if TYPE_CHECKING:`
            t=n.test
            return (isinstance(t,ast.Name) and t.id=='TYPE_CHECKING') or (isinstance(t,ast.Attribute) and t.attr=='TYPE_CHECKING')
        def add(name):
            # name could be module or attr; resolve longest module prefix
            parts=name.split('.')
            while parts:
                c='.'.join(parts)
                if c in mods:
                    E[m].add(c)
                    if parent_edges:
                        pp=c.split('.')[:-1]
                        while pp:
                            E[m].add('.'.join(pp)); pp.pop()
                    return
                parts.pop()
        def walk(nodes,in_func,in_tc):
            for n in nodes:
                if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    if include_func: walk(n.body,True,in_tc)
                    continue
                if isinstance(n,ast.If) and tc(n):
                    if include_tc: walk(n.body,in_func,True)
                    walk(n.orelse,in_func,in_tc); continue
                if isinstance(n,ast.Import):
                    for a in n.names:
                        if a.name.startswith(PKG): add(a.name)
                elif isinstance(n,ast.ImportFrom):
                    if n.level:
                        b=base.split('.')
                        b=b[:len(b)-(n.level-1)]
                        full='.'.join(b+([n.module] if n.module else []))
                    else: full=n.module or ''
                    if full.startswith(PKG):
                        add(full)
                        for a in n.names:
                            add(full+'.'+a.name) if (full+'.'+a.name) in mods else None
                else:
                    for fld in ('body','orelse','finalbody','handlers'):
                        v=getattr(n,fld,None)
                        if isinstance(v,list) and v and isinstance(v[0],ast.AST):
                            walk([x for x in v if not isinstance(x,ast.ExceptHandler)] + [y for x in v if isinstance(x,ast.ExceptHandler) for y in x.body],in_func,in_tc)
        walk(tree.body,False,False)
        E[m].discard(m)
    return E
def sccs(E):
    idx={};low={};st=[];on=set();out=[];c=[0]
    sys.setrecursionlimit(10000)
    def sc(v):
        idx[v]=low[v]=c[0];c[0]+=1;st.append(v);on.add(v)
        for w in E[v]:
            if w not in idx: sc(w);low[v]=min(low[v],low[w])
            elif w in on: low[v]=min(low[v],idx[w])
        if low[v]==idx[v]:
            comp=[]
            while True:
                w=st.pop();on.discard(w);comp.append(w)
                if w==v:break
            if len(comp)>1: out.append(sorted(comp))
    for v in E:
        if v not in idx: sc(v)
    return out
for tcf in (False,True):
  for ff in (False,True):
    for pe in (False,True):
        E=edges(tcf,ff,pe); s=sccs(E)
        print(f'TYPE_CHECKING={tcf} function-level={ff} parent-pkg-edges={pe}: modules={len(mods)} edges={sum(len(v) for v in E.values())} cycles(SCC>1)={len(s)}')
        for c in s: print('   ',c)

print('\n=== planned overlay (table of section 4.2, read from the document) with parent-package edges')
import re
txt=open('/home/user/hadavin-sdk/handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v9.md',encoding='utf-8').read()
tab=txt.split('<!-- PLANNED-EDGES-BEGIN -->')[1].split('<!-- PLANNED-EDGES-END -->')[0]
rows=[]
for l in tab.strip().split('\n')[2:]:
    c=[x.strip() for x in l.strip('|').split('|')]
    rows.append((c[0],[x.strip() for x in c[1].split(',') if x.strip()],[x.strip() for x in c[2].split(',') if x.strip()]))
for tcf in (False,True):
    for pe in (False,True):
        E=edges(tcf,False,pe)
        before={frozenset(c) for c in sccs(E)}
        for m in ('llm.spend','llm.callgate'):
            E.setdefault('hadavin_sdk.'+m,set())
        for m,rt,ty in rows:
            M='hadavin_sdk.'+m
            E.setdefault(M,set())
            for t in rt+(ty if tcf else []):
                E[M].add('hadavin_sdk.'+t); E.setdefault('hadavin_sdk.'+t,set())
            if pe:
                pp=M.split('.')[:-1]
                while pp: E[M].add('.'.join(pp)); pp.pop()
        after=[set(c) for c in sccs(E)]
        newc=[c for c in after if frozenset(c) not in before]
        print(f'TYPE_CHECKING={tcf} parent-pkg-edges={pe}: cycles before={len(before)} after={len(after)}; changed/new cycles={len(newc)}')
        for c in newc: print('    ',sorted(c))
