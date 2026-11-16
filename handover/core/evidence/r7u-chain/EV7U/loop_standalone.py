import sys, importlib.util
before=set(sys.modules)
p="/home/user/build/rr6/out/EV7U/hcopy/src/lead_desk/loopback.py"
sys.path[:0]=["/home/user/build/rr6/out/EV7U/hcopy/src/lead_desk"]
import loopback  # file imported as top-level module, only src/lead_desk on path
print("module file:", loopback.__file__)
new=sorted(set(sys.modules)-before)
print("modules loaded by import:", new)
print("lead_desk in sys.modules:", any(m=="lead_desk" or m.startswith("lead_desk.") for m in sys.modules))
for h in ["localhost","LOCALHOST","127.0.0.1","::1","[::1]","::ffff:127.0.0.1","0.0.0.0","::","[::]","","  ","example.com","127.1","::1%eth0","localhost."]:
    print(repr(h), loopback.is_loopback_host(h))
for h in [None,b"127.0.0.1",5," "]:
    try: print(repr(h), loopback.require_loopback_host(h))
    except Exception as e: print(repr(h),"RAISED",type(e).__name__)
