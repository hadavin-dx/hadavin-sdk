import sys
import os; sys.path.insert(0, os.environ["HTREE"])
import hostile_run as h
class Stop(Exception): pass
orig = h.alive_note
def an(cls):
    orig(cls)
    raise Stop()
h.alive_note = an
h.OUT.write_text("")
import shutil; shutil.rmtree(h.DBDIR, ignore_errors=True)
h.start_fakes()
try:
    h.classes()
except Stop:
    print("class A done, stopping", flush=True)
finally:
    h.stop_desk()
    if h.procs.get("f"): h.procs["f"].terminate()
