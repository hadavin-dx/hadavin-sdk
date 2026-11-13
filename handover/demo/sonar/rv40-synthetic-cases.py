import sys, importlib.util, textwrap, ast
root = sys.argv[1]
sys.path[:0] = [root, root + "/src", root + "/tests"]
spec = importlib.util.spec_from_file_location("tpc", root + "/tests/test_path_confinement.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
H = {"confine", "confine_existing"}
def run(name, src, expect_bad):
    f = m._function(textwrap.dedent(src), "f")
    c, bad = m._unused_result_sinks(f, H)
    got = bool(bad)
    verdict = "ok" if got == expect_bad else ("WRONGLY ACCEPTED" if expect_bad else "WRONGLY REJECTED")
    print(f"{verdict:17} {name}  count={c} bad={bad}")
C = [
("walrus in BoolOp rebinding p to raw", """
def f(p, raw, c):
    p = confine(p)
    _ = c and (p := raw)
    return p.read_text()
""", True),
("walrus in IfExp rebinding p to raw", """
def f(p, raw, c):
    p = confine(p)
    _ = 1 if c else (p := raw)
    return p.read_text()
""", True),
("walrus in comprehension element leaks", """
def f(p, raw):
    p = confine(p)
    _ = [(p := raw) for _x in range(2)]
    return p.read_text()
""", True),
("walrus in assert", """
def f(p, raw):
    p = confine(p)
    assert (p := raw)
    return p.read_text()
""", True),
("break path leaves p dirty", """
def f(p, raw, c):
    p = confine(p)
    for i in c:
        p = raw
        if i:
            break
        p = confine(raw)
    return p.read_text()
""", True),
("while True with break dirty", """
def f(p, raw, c):
    p = confine(p)
    while True:
        p = raw
        if c:
            break
        p = confine(raw)
    return p.read_text()
""", True),
("nonlocal rebinding in nested fn", """
def f(p, raw):
    p = confine(p)
    def swap():
        nonlocal p
        p = raw
    swap()
    return p.read_text()
""", True),
("nested fn defined then p reassigned", """
def f(p, raw):
    p = confine(p)
    def rd():
        return p.read_text()
    p = raw
    return rd()
""", True),
("list element overwritten", """
def f(p, raw):
    ps = [confine(p)]
    ps[0] = raw
    return ps[0].read_text()
""", True),
("bound method alias", """
def f(p, raw):
    q = confine(p)
    rd = raw.read_text
    return rd()
""", True),
("getattr call", """
def f(p, raw):
    q = confine(p)
    return getattr(raw, "read_text")()
""", True),
("mkdir not a sink", """
def f(p, raw):
    q = confine(p)
    raw.mkdir()
    return q.read_text()
""", True),
("os.replace to raw not a sink", """
def f(p, raw, tmp):
    q = confine(p)
    os.replace(tmp, raw)
    return q.read_text()
""", True),
("rename not a sink", """
def f(p, raw):
    q = confine(p)
    q.rename(raw)
    return q.read_text()
""", True),
("shutil.copy to raw not a sink", """
def f(p, raw):
    q = confine(p)
    shutil.copy(q, raw)
    return q.read_text()
""", True),
("clean / raw absolute", """
def f(p, raw):
    q = confine(p)
    return (q / raw).read_text()
""", True),
("Path(clean, raw)", """
def f(p, raw):
    q = confine(p)
    return Path(q, raw).read_text()
""", True),
("joinpath raw", """
def f(p, raw):
    q = confine(p)
    return q.joinpath(raw).read_text()
""", True),
("path built from file content", """
def f(p):
    q = confine(p)
    return Path(q.read_text()).read_text()
""", True),
("json content as path", """
def f(p):
    q = confine(p)
    d = json.loads(q.read_text())
    return Path(d["x"]).write_text("a")
""", True),
("handler calls .exit() on a non-sys object", """
def f(p, raw, thing):
    try:
        p = confine(p)
    except PathRefused:
        p = raw
        thing.exit()
    return p.read_text()
""", True),
("handler with bare exit()  (rejected: fine)", """
def f(p, raw):
    try:
        p = confine(p)
    except PathRefused:
        exit(2)
    return p.read_text()
""", False),
("match capture rebinds p", """
def f(p, raw):
    p = confine(p)
    match raw:
        case str() as p:
            pass
    return p.read_text()
""", True),
("except as p", """
def f(p, raw):
    p = confine(p)
    try:
        pass
    except OSError as p:
        pass
    return p.read_text()
""", False),
("for-else dirty", """
def f(p, raw, c):
    p = confine(p)
    for i in c:
        pass
    else:
        p = raw
    return p.read_text()
""", True),
("class body sink", """
def f(p, raw):
    q = confine(p)
    class K:
        data = raw.read_text()
    return q.read_text()
""", True),
("default arg sink in nested def", """
def f(p, raw):
    q = confine(p)
    def g(x=raw.read_text()):
        return x
    return q.read_text()
""", True),
("decorator expr", """
def f(p, raw):
    q = confine(p)
    @deco(raw.read_text())
    def g():
        pass
    return q.read_text()
""", True),
("global p rebinding", """
def f(p, raw):
    global p2
    p2 = confine(p)
    p2 = raw
    return p2.read_text()
""", True),
("del then rebind via setattr", """
def f(p, raw):
    q = confine(p)
    globals()["q"] = raw
    return q.read_text()
""", True),
("os.open(raw) false reject", """
def f(p, raw):
    q = confine(p)
    return os.open(q, 0)
""", False),
("Path.read_text(q) unbound false reject", """
def f(p):
    q = confine(p)
    return Path.read_text(q)
""", False),
("open(file=q) keyword false reject", """
def f(p):
    q = confine(p)
    return open(file=q)
""", False),
("sqlite3.connect(database=uri) keyword", """
def f(p):
    q = confine(p)
    return sqlite3.connect(database=uri(q))
""", False),
("with suppress", """
def f(p, raw):
    with suppress(OSError):
        p = confine(p)
    return p.read_text()
""", True),
("with other swallowing cm", """
def f(p, raw):
    with Quiet():
        p = confine(p)
    return p.read_text()
""", True),
("try/finally rebind", """
def f(p, raw):
    p = confine(p)
    try:
        pass
    finally:
        p = raw
    return p.read_text()
""", True),
("lambda param shadow", """
def f(p, raw):
    p = confine(p)
    g = lambda p: p.read_text()
    return g(raw)
""", True),
("lambda param shadow, sink only in lambda", """
def f(p, raw):
    p = confine(p)
    return list(map(lambda p: p.read_text(), [raw]))
""", True),
("comprehension over raw", """
def f(p, raw):
    p = confine(p)
    return [x.read_text() for x in raw]
""", True),
("comprehension over clean", """
def f(p, raw):
    ps = [confine(p)]
    return [x.read_text() for x in ps]
""", False),
("helper called on a constant", """
def f(p, raw):
    q = confine(Path("x"))
    return q.read_text()
""", False),
("helper result in other helper name (wrong helper)", """
def f(p, raw):
    q = confine_anywhere(p)
    return q.read_text()
""", True),
("AugAssign p += raw", """
def f(p, raw):
    p = confine(p)
    p += raw
    return Path(p).read_text()
""", True),
("tuple swap", """
def f(p, raw):
    p = confine(p)
    p, r = raw, p
    return p.read_text()
""", True),
("starred unpack", """
def f(p, raw):
    p = confine(p)
    p, *r = [raw, p]
    return p.read_text()
""", True),
("for target rebinding dirty then after loop", """
def f(p, raw, c):
    p = confine(p)
    for p in c:
        pass
    return p.read_text()
""", True),
("with-as rebinding dirty", """
def f(p, raw, c):
    p = confine(p)
    with c as p:
        pass
    return p.read_text()
""", True),
("del p then use (NameError)", """
def f(p, raw, c):
    p = confine(p)
    del p
    return p.read_text()
""", False),
("conditional helper only on one branch", """
def f(p, raw, c):
    if c:
        p = confine(p)
    return p.read_text()
""", True),
("continue skipping reassign", """
def f(p, raw, c):
    p = confine(p)
    for i in c:
        if i:
            p = raw
            continue
        p = confine(raw)
    return p.read_text()
""", True),
("try-else reassign", """
def f(p, raw, c):
    p = confine(p)
    try:
        c()
    except OSError:
        raise
    else:
        p = raw
    return p.read_text()
""", True),
("exception path: sink in handler after body rebinding", """
def f(p, raw, c):
    p = confine(p)
    try:
        p = raw
        c()
    except OSError:
        return p.read_text()
    return 0
""", True),
("sink in finally after rebinding", """
def f(p, raw, c):
    p = confine(p)
    try:
        p = raw
        c()
    finally:
        p.read_text()
""", True),
("async with / await", """
async def f(p, raw):
    p = confine(p)
    async with raw as p:
        pass
    return p.read_text()
""", True),
]
for n, s, e in C: run(n, s, e)
