import sys, types, dataclasses, traceback
sys.path.insert(0, "/home/user/build/B-Q8a1-b8/src"); sys.path.insert(0, "/home/user/build/EV-q8a1-a1869655/wt")
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from decimal import Decimal
from pydantic import field_validator
import probe_old as P
from probe_old import MARK, load_config, fresh, yaml
from hadavin_sdk.backends import table as T
sys.modules["hadavin_sdk._x"] = types.ModuleType("hadavin_sdk._x")
class XS(T.KindSettings):
    n: str
    @field_validator("n")
    @classmethod
    def _c(cls, x): return Decimal(x)
XS.__module__ = "hadavin_sdk._x"
T.TABLE["secrets"]["xx"] = dataclasses.replace(T.TABLE["secrets"]["env"], settings=XS)
root = fresh(); p = root / "config.yaml"
d = yaml.safe_load(p.read_text()); d["backends"]["secrets"] = {"kind": "xx", "n": MARK}; p.write_text(yaml.safe_dump(d))
try:
    load_config(root); print("no error")
except BaseException as e:
    full = "".join(traceback.format_exception(e))
    print(type(e).__module__ + "." + type(e).__name__, "| str:", str(e)[:120], "| marker in str/repr/traceback:", MARK in str(e), MARK in repr(e), MARK in full)
