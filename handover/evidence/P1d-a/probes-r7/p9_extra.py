"""P9: strings for rev 9 rows Q24, S8b, S8c and the wide-dot gap N9, model path and card path. Usage: PYTHONPATH=<tree>/src python p9_extra.py"""
import hadavin_sdk
from hadavin_sdk.guard import runmap
from hadavin_sdk.approvals import channel
print("tree", hadavin_sdk.__file__)
HOSTS = ["secretsmanager.eu-west-1.example.com", "token-service.internal.example.com", "session-store.corp.example.com"]
cases = {"Q24": "?password=ab&this_field_name_has_over_twenty_chars=1 x",
         "Q24b": "?password=ab&" + "a" * 21 + "=1 x", "Q24c": "?password=ab&" + "a" * 22 + "=1 x"}
for h in HOSTS:
    for p in ("443", "5432", "8080"):
        cases[f"S8b {h[:12]}:{p}"] = f"x {h}:{p} y"
    cases[f"S8c {h[:12]}"] = f"x {h}: connection refused y"
for k, x in cases.items():
    print(k, "| model", repr(runmap.redact_text(x, runmap.RunMap())), "| card", repr(channel.clean(x)))
