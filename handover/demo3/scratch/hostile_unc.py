import sys, ntpath, os
repo = sys.argv[1]
sys.path.insert(0, repo)
import tools.pathconfine as pc
print("module:", pc.__file__)
inputs = [r"\\host\share\x.db", "//host/share/x.db", r"\\?\UNC\host\share\x.db", "\\/host/share/x.db", "/\\host\\share\\x.db",
          r"\\?\C:\x.db", r"\\.\C:\x.db", r"C:\x.db", r"\\localhost\share\x.db", "//localhost/c$/x.db", r"\\host\share", "\\\\host", "/tmp/ok.db", "rel.db", "\\\\?\\UNC\\", "///host/share/x.db", "\\\\\\host\\share"]
for mod in (os.path, ntpath):
    print("== path_module", mod.__name__)
    for t in inputs:
        for fn in ("readonly_sqlite_uri",):
            try:
                if hasattr(pc, "_refuse_network_path"):
                    r = getattr(pc, fn)(t, mod)
                else:
                    r = getattr(pc, fn)(t) if mod is os.path else "N/A on main (no path_module param)"
                print(repr(t), "->", repr(r))
            except BaseException as e:
                print(repr(t), "-> EXC", type(e).__name__, str(e))
print("== confine/confine_existing/confine_anywhere on Linux os.path")
for t in inputs[:8]:
    for fn in ("confine","confine_existing","confine_anywhere"):
        try:
            print(fn, repr(t), "->", repr(str(getattr(pc,fn)(t, what="--x"))))
        except BaseException as e:
            print(fn, repr(t), "-> EXC", type(e).__name__, str(e))
