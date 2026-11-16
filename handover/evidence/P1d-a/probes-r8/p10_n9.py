"""P10: N9 rows on a tree. usage: PYTHONPATH=<tree>/src python p10_n9.py"""
from hadavin_sdk.approvals import channel, gate
from hadavin_sdk.guard import runmap
EM = "anna" + "." + "m" + "@" + "example" + "." + "org"
for x in ["see //evil。com/p now", "see //evil．com/p now", "see //evil｡com/p now", "visit www。evil。digital now",
          "mail anna。m@example。org now", "x `//evil。com/p` y", "see //evil。com now", "a http://evil。com/p b"]:
    print(repr(x), "| card", repr(channel.clean(x)), "| gate(defang=False)", repr(gate.sanitise_text(x, defang=False)), "| default", repr(gate.sanitise_text(x)))
