"""G9 v3 evidence: the body of G8 v5 8.1's G9 test, run without pytest, on tree argv[1] (a tree with G8 and G9)."""
import importlib, sys
sys.path.insert(0, sys.argv[1] + "/src"); R = importlib.import_module("hadavin_sdk.guard.redact")
def _registering(m):
    r = R._Redactor(m); r._may_register = True; return r
phone = "415" + "555" + "0132"
r = _registering({"<TENANT_1>": phone[:8], "<PHONE_1>": phone})
print(repr(r.sweep("x<TENANT_1>32 y")), repr(r.sweep("7<TENANT_1>32 y")), r.mapping == {"<TENANT_1>": phone[:8], "<PHONE_1>": phone})
print("gate:", repr(importlib.import_module("hadavin_sdk.guard.runmap").enforce_map("x<TENANT_1>32 y", {"<TENANT_1>": phone[:8], "<PHONE_1>": phone})))
