"""Apply the 3 documented server.py hook edits (CONTRACT-DELTA.md, "server.py hooks") to the UNPACKED COPY only.
Fails loudly (exit 1) if the original text is not found. If the hooks are already in the file, says so and does nothing
(exit 0, prints ALREADY-PATCHED). Hook 3 (listen queue) is not an edit here: the tree's constants.LISTEN_QUEUE is read
and printed; the script does not change it.
usage: patch_hooks.py TREE"""
import pathlib, re, sys
tree = pathlib.Path(sys.argv[1]); f = tree / "src/lead_desk/server.py"; s = f.read_text()
if "start_background()" in s and "LockHeldError" in s and "stop_background()" in s:
    print("ALREADY-PATCHED (hooks 1 and 2 present in the tarball's server.py)"); sys.exit(0)
def rep(old, new):
    global s
    if s.count(old) != 1: sys.exit(f"PATCH FAILED: text found {s.count(old)} times (need exactly 1):\n{old}")
    s = s.replace(old, new)
# hook 2: lock handling
rep('''    except OSError:
        print("another desk is using this database", flush=True)
        sys.exit(EXIT_ANOTHER_DESK)
''', '''    except lockfile.LockHeldError:
        print("another desk is using this database", flush=True)
        sys.exit(EXIT_ANOTHER_DESK)
    except OSError as e:
        print(f"cannot take the lock file: {type(e).__name__}", flush=True)
        sys.exit(EXIT_ANOTHER_DESK)
''')
# hook 1: start_background before startup, stop_background first in finally
rep('''    try:
        desk.startup()
        host, port''', '''    try:
        desk.start_background()
        desk.startup()
        host, port''')
rep('''    finally:
        server.server_close()
        desk.close()
        lock.close()''', '''    finally:
        desk.stop_background()
        server.server_close()
        desk.close()
        lock.close()''')
f.write_text(s)
q = re.search(r"LISTEN_QUEUE[^=\n]*=\s*(\d+)", (tree / "src/lead_desk/constants.py").read_text())
print("PATCHED hooks 1 and 2 in", f, "| hook 3: constants.LISTEN_QUEUE =", q.group(1) if q else "NOT FOUND (not changed by this script)")
