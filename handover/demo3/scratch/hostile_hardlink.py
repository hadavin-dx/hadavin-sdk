import sys, os, tempfile
from pathlib import Path
repo = sys.argv[1]; base = Path(sys.argv[2]).resolve()
sys.path.insert(0, repo)
import tools.pathconfine as pc
print("module:", pc.__file__, "cwd:", os.getcwd(), "tmp:", tempfile.gettempdir())
root = base / "root"; out = base / "outside"
root.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
secret = out / "secret.txt"; secret.write_text("FAKE-OUTSIDE\n")
inside = root / "inside.txt"; inside.write_text("FAKE-INSIDE\n")
for n in ("hl_out.txt", "hl_in.txt", "sym_out.txt"):
    p = root / n
    if p.exists() or p.is_symlink(): p.unlink()
os.link(secret, root / "hl_out.txt"); os.link(inside, root / "hl_in.txt"); os.symlink(secret, root / "sym_out.txt")
print("nlink secret:", os.stat(secret).st_nlink, "inode eq:", os.stat(secret).st_ino == os.stat(root/"hl_out.txt").st_ino)
os.chdir(root)
for n in ("hl_out.txt", "hl_in.txt", "sym_out.txt", str(secret)):
    for fn in ("confine_existing", "confine", "confine_anywhere"):
        try:
            r = getattr(pc, fn)(n, what="--f"); print(fn, n, "->", r)
        except BaseException as e:
            print(fn, n, "-> EXC", type(e).__name__, e)
# write through a confined hard link (what an output option does)
try:
    p = pc.confine("hl_out.txt", what="--out"); p.write_text("FAKE-OVERWRITTEN-VIA-HARDLINK\n")
    print("write via confine(hl_out.txt) done; outside now:", repr(secret.read_text()))
except BaseException as e: print("write EXC", type(e).__name__, e)
secret.write_text("FAKE-OUTSIDE\n")
try:
    p = pc.confine_existing("hl_out.txt", what="--f"); print("read via hardlink:", repr(p.read_text()))
except BaseException as e: print("read EXC", type(e).__name__, e)
