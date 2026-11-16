import sys
sys.path.insert(0, "/home/user/build/rr6/tree-R7U-B")
from demo_only.bad_request import require_loopback_host
from demo_only.fakes_server import make_fakes_server
from demo_only.fake_model_server import make_model_server
import inspect
print(inspect.signature(make_fakes_server), inspect.signature(make_model_server))
for h in ["LOCALHOST","[::1]","::ffff:127.0.0.1","localhost","127.0.0.1"]:
    try: print(h, "rule->", require_loopback_host(h))
    except Exception as e: print(h, "rule refused", e)
    for name, f in (("fakes", make_fakes_server),):
        try:
            s = f(host=h); print("  bound", name, s.server_address, s.address_family); s.server_close()
        except Exception as e: print("  bind failed", name, type(e).__name__, e)
