import sys, ntpath, os, tempfile
repo = sys.argv[1]; sys.path.insert(0, repo); sys.path.insert(1, repo + "/src")
import tools.pathconfine as pc
jail = tempfile.mkdtemp(prefix="e-jail-")
cases = [
 ("NT object path", "\\??\\UNC\\host\\share\\x"), ("empty", ""), ("NUL text", "\x00"), ("a NUL b", "a\x00b"),
 ("C1 U+0080 inside", "a\x80b.db"), ("C1 U+0085 inside", "a\x85b.db"), ("C1 U+009F inside", "a\x9fb.db"),
 ("C1 U+0090 leading", "\x90book.db"), ("C1 U+0090 trailing", "book.db\x90"),
 ("leading space", " book.db"), ("trailing space", "book.db "), ("inner space", "my book.db"),
 ("only space", " "), ("only tab", "\t"), ("NBSP only", " "), ("NBSP inner", "a b.db"),
 ("NBSP leading", " book.db"), ("NBSP trailing", "book.db "),
 ("bytes", b"book.db"), ("bytes NUL", b"book\x00.db"), ("bytes non-UTF-8", b"book\xff\xfe.db"), ("bytes empty", b""),
 ("bytearray", bytearray(b"book.db")),
]
class Changing:
    def __init__(self, a, b): self.a=a; self.b=b; self.calls=0
    def __fspath__(self):
        self.calls+=1
        return self.a if self.calls==1 else self.b
    def __repr__(self): return f"Changing({self.a!r} then {self.b!r}) calls={self.calls}"
J = jail
cases += [
 ("stateful fspath good then other", Changing(J+"/book.db", J+"/other.db")),
 ("stateful fspath good then NUL", Changing(J+"/book.db", J+"/b\x00.db")),
 ("stateful fspath good then UNC", Changing(J+"/book.db", "\\\\host\\share\\x")),
 ("stateful fspath 1st empty then good", Changing("", J+"/book.db")),
 ("lone surrogate", "\ud800"), ("lone surrogate .db", "a\ud800b.db"),
 ("surrogate in longer path", J+"/sub/a\udcffb.db"), ("high+low surrogate pair split", "\ud83d\ude00.db"),
]

class SubStr(str):
    """str subclass whose methods answer differently on later calls"""
    def strip(self, *a):
        self.__dict__["n"] = self.__dict__.get("n", 0) + 1
        return "x" if self.n == 1 else ""
    def __str__(self): return "ELSE.db"
    def __len__(self): return 3
class PL:
    def __init__(self, v): self.v = v
    def __fspath__(self): return self.v
class Flip(str):
    """str subclass: replace() and startswith() lie"""
    def replace(self, *a): return "\\\\host\\share\\x"
    def startswith(self, *a): return True
    def __str__(self): return "\\\\host\\share\\x"
cases += [
 ("NEW str subclass (strip/__str__/__len__ lie), good text", SubStr(J+"/book.db")),
 ("NEW str subclass returned by __fspath__", PL(SubStr(J+"/book.db"))),
 ("NEW str subclass (replace/startswith/__str__ say UNC)", Flip(J+"/book.db")),
 ("NEW fspath returns int", PL(5)), ("NEW fspath returns None", PL(None)), ("NEW fspath returns bytes", PL(b"book.db")),
 ("NEW U+2028 in name", J+"/a\u2028b.db"), ("NEW U+2029 in name", J+"/a\u2029b.db"),
 ("NEW zero-width space in name", J+"/a\u200bb.db"), ("NEW bidi RLO in name", J+"/a\u202eb.db"),
 ("NEW DEL", J+"/a\x7fb.db"), ("NEW newline in name", J+"/a\nb.db"),
 ("NEW surrogate escape high \\udc80", J+"/a\udc80b.db"), ("NEW lone surrogate at end of long path", J+"/x"*10+"\ud800"),
 ("NEW real existing file", J+"/real.db"),
]
open(J+"/real.db","w").close()
def run(f):
    try: return "OK " + repr(f())
    except BaseException as e: return f"EXC {type(e).__name__}: {e}"
for label, t in cases:
    print("INPUT", label, repr(t))
    if isinstance(t, Changing):
        a,b=t.a,t.b
        for mname, m in (("ntpath", ntpath), ("os.path", os.path)):
            t=Changing(a,b)
            print("  uri/" + mname, "->", run(lambda: pc.readonly_sqlite_uri(t, m)), "| fspath calls =", t.calls)
        t=Changing(a,b); print("  confine_anywhere ->", run(lambda: str(pc.confine_anywhere(t, what="f"))), "| calls =", t.calls)
        t=Changing(a,b); print("  confine(roots=[jail]) ->", run(lambda: str(pc.confine(t, what="f", roots=[jail])).replace(jail, "<jail>")), "| calls =", t.calls)
        continue
    for mname, m in (("ntpath", ntpath), ("os.path", os.path)):
        print("  uri/" + mname, "->", run(lambda: pc.readonly_sqlite_uri(t, m)))
    print("  confine_anywhere ->", run(lambda: str(pc.confine_anywhere(t, what="f"))))
    print("  confine(roots=[jail]) ->", run(lambda: str(pc.confine(t, what="f", roots=[jail])).replace(jail, "<jail>")))
