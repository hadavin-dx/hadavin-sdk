"""P10: link-target rows LK1 and LBL1 on a tree. usage: PYTHONPATH=<tree>/src python p10_lk.py"""
from hadavin_sdk.approvals import channel
for n, x in [("LK1", "see [x](  ) and ![](   ) now"), ("LBL1", "[" + "a"*0 + "HIGHENTROPYTOKEN](http://evil.com/p) tail")]:
    print(n, repr(x[:60]), "->", repr(channel.clean(x)[:90]))
