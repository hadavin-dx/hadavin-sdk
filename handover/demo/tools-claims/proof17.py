import ast, subprocess, sys, yaml
B="f3c39cf8"
files=subprocess.check_output(["git","diff","--name-only",B,"HEAD"]).decode().split()
def strip(t):
    for n in ast.walk(t):
        if isinstance(n,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(getattr(n.body[0],'value',None),ast.Constant) and isinstance(n.body[0].value.value,str):
            n.body[0].value.value=''
    return ast.dump(t)
for f in files:
    old=subprocess.check_output(["git","show",f"{B}:{f}"]).decode(); new=open(f,encoding="utf-8").read()
    if f.endswith(".py"):
        print(f, "AST EQUAL" if strip(ast.parse(old))==strip(ast.parse(new)) else "AST DIFFERENT")
    elif f.endswith((".yml",".yaml")):
        print(f, "YAML EQUAL" if yaml.safe_load(old)==yaml.safe_load(new) else "YAML DIFFERENT")
