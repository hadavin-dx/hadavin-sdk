"""Evidence runner's own injection: a private Exception subclass at each READ_ERRORS site (records, does not judge)."""
import http.client, logging, threading
import pytest
from hadavin_sdk import bindguard, standins
from hadavin_sdk.approvals import receiver, requests as R
from tests import test_bindguard as TB

class Private(Exception):
    pass

def boom(err):
    def f(*a, **k):
        raise err("injected")
    return f

# (id, kind) each: callable(monkeypatch, err, tmp_path) -> result ; Private must propagate, RuntimeError (named) control must not
def s_bg143(m, err, tp):
    class M(dict):
        def items(self): raise err("x")
    return bindguard.held_services_found(M(a=1))
def s_bg174(m, err, tp):
    m.setattr(bindguard, "verdict", boom(err)); return bindguard.held_services_found({"x": object()})
def s_si245(m, err, tp):
    class D:
        def __get__(self, *a): raise err("x")
    m.setattr(standins, "_CLASS_ANNOTATIONS", D()); return standins._touch_annotations(type("K", (), {}))
def s_si250(m, err, tp):
    import copyreg
    m.setattr(copyreg, "_slotnames", boom(err)); return standins._touch_annotations(type("K", (), {}))
def s_si307(m, err, tp):
    m.setattr(standins, "live_class", boom(err)); return standins.pin_module(standins._PINNED_KEYS[0][0])
def s_si337(m, err, tp):
    m.setattr(standins, "live_class", boom(err)); return standins.pin_all()
def s_si349(m, err, tp):
    m.setattr(standins, "live_class", boom(err)); return standins.is_pinned_instance(object())
def s_si696(m, err, tp):
    m.setattr(standins, "_check", boom(err)); return standins.verdict(object(), None)
def s_rc62(m, err, tp):
    from hadavin_sdk.config import load_config
    from tests.conftest import make_cfg
    cfg = load_config(make_cfg(tp)).model_copy(update={"check_modules": []})
    a = TB._Approvals(cfg)
    m.setattr(standins, "is_pinned_instance", boom(err)); return receiver._recheck(a)
def s_rc90(m, err, tp):
    m.setattr(receiver, "_LAST_LOGGED", {}); m.setattr(receiver._LOG, "warning", boom(err)); return receiver._refused(("held zz: Q",))
def s_rc147(m, err, tp):
    from hadavin_sdk.config import load_config
    from tests.conftest import make_cfg
    cfg = load_config(make_cfg(tp)).model_copy(update={"check_modules": []})
    a = TB._Approvals(cfg)
    m.setattr(standins, "is_pinned_instance", boom(err))
    return receiver.serve(a, config=cfg, host=TB.ALL_ZEROS, port=0)
def s_rq441(m, err, tp):
    app = TB._built(tp); rt = TB._core_runtime(app)
    m.setattr(standins, "is_stand_in", boom(err)); return R._runtime_ok(rt)
def s_rq512(m, err, tp):
    app = TB._built(tp); rt = TB._core_runtime(app)
    TB._fields(rt)["extra_name"] = 1
    m.setattr(R, "_members_walk", boom(err)); return TB._runtime_counted(app, rt)

SITES = {k: v for k, v in globals().items() if k.startswith("s_")}

@pytest.mark.parametrize("site", sorted(SITES))
def test_private_propagates(site, monkeypatch, tmp_path):
    with pytest.raises(Private):
        SITES[site](monkeypatch, Private, tmp_path)

@pytest.mark.parametrize("site", sorted(SITES))
def test_control_named_error_is_caught(site, monkeypatch, tmp_path):
    try:
        SITES[site](monkeypatch, RuntimeError, tmp_path)
    except BindRefusedOK:
        pass
    except RuntimeError as e:  # a named error escaping would mean the injection is not reaching a guarded read
        pytest.fail(f"control escaped: {e}")

BindRefusedOK = bindguard.BindRefused

def test_receiver_observable_with_private_error_at_refused(monkeypatch, tmp_path, caplog, capfd):
    from hadavin_sdk.approvals import Approvals
    app = TB._built(tmp_path)
    monkeypatch.setattr(receiver, "_LAST_LOGGED", {})
    monkeypatch.setattr(bindguard, "_literal", lambda host: (TB.LOOP_1, __import__("socket").AF_INET))
    server = receiver.serve(app.approvals, config=app.config, host=TB.ALL_ZEROS, port=0)
    monkeypatch.setattr(Approvals, "real_now", lambda self: ("a real service",))
    out = {}
    for label, err in (("RuntimeError(named)", RuntimeError), ("Private", Private)):
        monkeypatch.setattr(receiver, "_LAST_LOGGED", {})
        monkeypatch.setattr(receiver._LOG, "warning", boom(err))
        t = threading.Thread(target=server.serve_forever, daemon=True); t.start()
        try:
            c = http.client.HTTPConnection(TB.LOOP_1, server.server_address[1], timeout=5)
            c.request("POST", receiver.PATH, body=b"{}", headers={"Content-Length": "2"})
            out[label] = f"status {c.getresponse().status}"
        except Exception as e:
            out[label] = f"client saw {type(e).__name__}: no status line"
        finally:
            server.shutdown(); t.join(5)
    server.server_close()
    err = capfd.readouterr().err
    print("OBSERVABLE", out, "| server stderr mentions Private:", "Private" in err, "| traceback printed:", "Traceback" in err)
