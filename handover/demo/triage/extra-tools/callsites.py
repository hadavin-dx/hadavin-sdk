import ast,sys,pathlib
H={"row":(2,),"follow":(2,),"col":(1,),"_set_outcome":(2,)}
bad=0;tot=0
for p in sorted(pathlib.Path("tests").glob("*.py")):
  t=ast.parse(p.read_text())
  defs={n.name for n in ast.walk(t) if isinstance(n,ast.FunctionDef)}
  for n in ast.walk(t):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in H and n.func.id in defs:
      i=H[n.func.id][0]
      if len(n.args)>i:
        tot+=1
        a=n.args[i]
        if not isinstance(a,ast.Constant): bad+=1;print(f"NONCONST {p}:{n.lineno} {ast.unparse(n)[:100]}")
print(tot,"calls checked",bad,"non-constant")
