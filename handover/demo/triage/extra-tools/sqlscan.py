import ast,sys,pathlib
FN={"execute","executemany","executescript","query","sql","sql_exec","rows","select","_q","q"}
for root in sys.argv[1:]:
 for p in sorted(pathlib.Path(root).rglob("*.py")):
  t=ast.parse(p.read_text())
  for n in ast.walk(t):
    if isinstance(n,ast.Call):
      f=n.func; name=f.attr if isinstance(f,ast.Attribute) else f.id if isinstance(f,ast.Name) else None
      if name not in FN or not n.args: continue
      # sql text is first arg, or second for sql(rig,text)/sql_exec(db,sql)/rows(db,sql)
      idx=1 if name in("sql","sql_exec","rows") else 0
      if len(n.args)<=idx: continue
      a=n.args[idx]
      if isinstance(a,ast.Constant): continue
      if isinstance(a,ast.JoinedStr) or isinstance(a,ast.BinOp) or (isinstance(a,ast.Call) and isinstance(a.func,ast.Attribute) and a.func.attr=="format") or isinstance(a,ast.Name):
        print(f"{p}:{n.lineno}: {name}({ast.unparse(a)[:110]})")
