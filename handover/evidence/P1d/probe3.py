import sys; sys.path.insert(0, sys.argv[1])
from hadavin_sdk.guard import runmap
K = "AKIA" + "IOSFODNN7" + "EXAMPLE"
for t in ["fooBarBazQux1234567890abc/anotherLongIdentifier99xyz", "keyz"+K, K[:4]+"&"+K[4:], K[:4]+"."+K[4:], "password=ab&cd"+"efghijkl"]:
    print(repr(runmap.redact_text(t, runmap.RunMap({}))))
