import ast,sys,pathlib
for p in sorted(pathlib.Path(sys.argv[1]).rglob("*.py")):
    src=p.read_text(); t=ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            body=[b for b in n.body if not (isinstance(b,ast.Expr) and isinstance(b.value,ast.Constant) and isinstance(b.value.value,str))]
            if not body or all(isinstance(b,ast.Pass) or (isinstance(b,ast.Expr) and isinstance(b.value,ast.Constant) and b.value.value is Ellipsis) for b in body):
                print(f"EMPTY {p}:{n.lineno} {n.name}")
        if isinstance(n,ast.ExceptHandler) and all(isinstance(b,ast.Pass) for b in n.body): print(f"EXCEPT-PASS {p}:{n.lineno}")
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="next" and len(n.args)==1 and not n.keywords:
            print(f"NEXT {p}:{n.lineno} {ast.unparse(n)[:100]}")
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in("exec","eval"): print(f"EXEC {p}:{n.lineno} {ast.unparse(n)[:100]}")
        if isinstance(n,ast.Compare):
            for op,c in zip(n.ops,n.comparators):
                if isinstance(op,(ast.Is,ast.IsNot)) and isinstance(c,ast.Constant) and c.value not in (None,True,False,Ellipsis): print(f"IS-LITERAL {p}:{n.lineno} {ast.unparse(n)[:90]}")
                if isinstance(op,(ast.Eq,ast.NotEq)) and isinstance(c,ast.Constant) and c.value in (None,True,False) : print(f"EQ-SINGLETON {p}:{n.lineno} {ast.unparse(n)[:90]}")
                if ast.dump(n.left)==ast.dump(c): print(f"SELF-CMP {p}:{n.lineno} {ast.unparse(n)[:90]}")
        if isinstance(n,ast.Assert) and isinstance(n.test,ast.Tuple): print(f"ASSERT-TUPLE {p}:{n.lineno}")
