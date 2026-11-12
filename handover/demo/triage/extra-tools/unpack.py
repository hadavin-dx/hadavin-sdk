import ast,sys,pathlib
for root in sys.argv[1:]:
  for p in sorted(pathlib.Path(root).rglob("*.py")):
    src=p.read_text();t=ast.parse(src)
    for n in ast.walk(t):
      tg=it=None
      if isinstance(n,ast.Assign) and isinstance(n.targets[0],(ast.Tuple,ast.List)): tg,it=n.targets[0],n.value
      elif isinstance(n,(ast.For,ast.comprehension)) and isinstance(n.target,(ast.Tuple,ast.List)): tg,it=n.target,n.iter
      if tg is None: continue
      if isinstance(it,ast.Tuple) and not any(isinstance(e,ast.Starred) for e in tg.elts): continue
      print(f"{p}:{n.lineno if hasattr(n,'lineno') else it.lineno}: {len(tg.elts)} <- {ast.unparse(it)[:90]}")
