import sys, os, copy, dataclasses, tempfile, json, logging
from pathlib import Path
from types import SimpleNamespace
WT = os.getcwd(); sys.path.insert(0, WT)
import hadavin_sdk; print("sdk:", hadavin_sdk.__file__)
import tests.test_mode_banner as T
from hadavin_sdk import app as app_mod, mode_banner as mb
logging.disable(logging.NOTSET)
tmp = Path(tempfile.mkdtemp(prefix="probe-"))
n = [0]
class Surprise(Exception): pass
def fresh(change=None, seal=True):
    n[0] += 1
    a = T._built_app(tmp / f"a{n[0]}")
    if change: change(a)
    if seal: a._seal(T._given())
    return a
def show(label, fn):
    try:
        r = fn()
        if isinstance(r, tuple): r = {"tone": r}
        print(f"{label:70} -> tone={r.get('tone')!r} tag={r.get('tag')!r} text={str(r.get('text'))[:48]!r}")
    except BaseException as e:
        print(f"{label:70} -> RAISED {type(e).__name__}: {str(e)[:100]}")
tone = lambda a: a.mode_banner()
# control
show("control: untouched sealed app", lambda: tone(fresh()))
# deleted tool spec
a = fresh(lambda a: a.registry.tools.update({"agent": {"lookup": T._tool_spec()}})); show("control: sealed with real-host tool spec", lambda: tone(a))
del a.registry.tools["agent"]["lookup"]; show("deleted tool spec after seal", lambda: tone(a))
# deleted agent entry
a = fresh(); k = next(iter(a.registry.agents)); del a.registry.agents[k]; show("deleted registry.agents entry", lambda: tone(a))
a = fresh(); k = next(iter(a.registry.agents)); a.registry.agents[k] = copy.copy(a.registry.agents[k]); show("replaced registry.agents entry (copy)", lambda: tone(a))
# cleared config.sources
a = fresh(lambda a: a.config.sources.update({"s": SimpleNamespace(kind="unknown-kind", settings={})})); show("control: unknown source", lambda: tone(a)); a.config.sources.clear(); show("cleared config.sources", lambda: tone(a))
# replaced toolbox
def add(a): a.runtime.hooks.toolbox = SimpleNamespace(specs={"lookup": T._tool_spec("lookup", ())}, _fns={"lookup": lambda: None})
for lab, ch in (("toolbox _fns replaced", lambda b: b._fns.update({"lookup": lambda: "o"})), ("toolbox specs entry replaced", lambda b: b.specs.update({"lookup": T._tool_spec("lookup", ("x.example.com",))})), ("toolbox specs cleared", lambda b: b.specs.clear())):
    a = fresh(add); ch(a.runtime.hooks.toolbox); show(lab, lambda: tone(a))
# removed/renamed container
a = fresh()
object.__setattr__(a.config, "sources_x", a.config.sources); object.__delattr__(a.config, "sources") if hasattr(type(a.config), "__delattr__") else None
show("config.sources attribute removed", lambda: tone(a))
a = fresh()
try:
    object.__setattr__(a.registry, "tools", None); show("registry.tools = None", lambda: tone(a))
except Exception as e: print("registry.tools=None setup failed", type(e).__name__)
a = fresh(); object.__setattr__(a.config, "systems", None); show("config.systems = None", lambda: tone(a))
a = fresh(); a.config.systems.clear(); show("config.systems cleared", lambda: tone(a))
a = fresh(); a.config.systems["x-new"] = a.config.systems[next(iter(a.config.systems))]; show("config.systems entry added", lambda: tone(a))
# dataclasses.replace, copy, deepcopy, _seal(())
a = fresh(); show("dataclasses.replace(app)", lambda: dataclasses.replace(a).mode_banner())
show("copy.copy(app)", lambda: copy.copy(a).mode_banner())
show("copy.deepcopy(app)", lambda: copy.deepcopy(a).mode_banner())
a = fresh(seal=False); show("app._seal(()) on unsealed app (plain tuple)", lambda: (a._seal(()), tone(a))[1]); show("  ...then banner of that app", lambda: tone(a))
a = fresh(); show("app._seal(()) on sealed app (plain tuple)", lambda: (a._seal(()), tone(a))[1]); show("  ...then banner of that app", lambda: tone(a))
a = fresh(seal=False); show("never sealed", lambda: tone(a))
# forced stage change pilot/prod from demo
for st in ("pilot", "prod"):
    a = fresh(); object.__setattr__(a.config, "environment", st); show(f"object.__setattr__(config.environment,'{st}') after seal at demo", lambda: tone(a))
# surprise exception at each of five broad-except sites
def site(label, patch):
    a = fresh()
    undo = patch(a)
    show(label, lambda: tone(a)); undo()
def p_known(a):       # app.py ~295: _stage raises
    o = app_mod.App._stage; app_mod.App._stage = lambda self: (_ for _ in ()).throw(Surprise("x")); return lambda: setattr(app_mod.App, "_stage", o)
site("app.py ~295 (_known_overrides): _stage raises Surprise", p_known)
def p_conn(a):
    o = app_mod.App._connected_parts; app_mod.App._connected_parts = lambda self: (_ for _ in ()).throw(Surprise("x")); return lambda: setattr(app_mod.App, "_connected_parts", o)
site("app.py ~295 (_known_overrides): _connected_parts raises Surprise", p_conn)
def p_mb(a):          # app.py ~312: banner_or_unconfirmed raises
    o = app_mod.banner_or_unconfirmed; app_mod.banner_or_unconfirmed = lambda *x, **k: (_ for _ in ()).throw(Surprise("x")); return lambda: setattr(app_mod, "banner_or_unconfirmed", o)
site("app.py ~312 (App.mode_banner): banner_or_unconfirmed raises Surprise", p_mb)
# mb.py ~731: banner_from_config raises (use app path and direct)
o = mb.banner_from_config; mb.banner_from_config = lambda *x, **k: (_ for _ in ()).throw(Surprise("x"))
a = fresh(); show("mode_banner.py ~731 (banner_or_unconfirmed): banner_from_config raises, via app", lambda: tone(a))
show("mode_banner.py ~731 direct banner_or_unconfirmed(config)", lambda: mb.banner_or_unconfirmed(a.config, None, mb.DEFAULT_WORDS, tool_specs=a.registry.tools, overridden=()))
mb.banner_from_config = o
# mb.py ~759: words getter raises
class BadWords:
    def __getattr__(self, k): raise Surprise("words")
    @property
    def tag_by_mode(self): raise Surprise("words")
a = fresh(); show("mode_banner.py ~759 (_not_confirmed_that_cannot_fail): words raise (direct)", lambda: mb._not_confirmed_that_cannot_fail(BadWords()))
o = mb.banner_from_config; mb.banner_from_config = lambda *x, **k: (_ for _ in ()).throw(Surprise("x"))
show("both ~731 and ~759: banner_from_config raises + bad words, direct", lambda: mb.banner_or_unconfirmed(a.config, None, BadWords(), tool_specs=a.registry.tools, overridden=()))
show("both, via app.mode_banner(words=BadWords)", lambda: a.mode_banner(words=BadWords()))
mb.banner_from_config = o
# 471: post_card
from hadavin_sdk.approvals.channel import FakeChannel
ch = FakeChannel()
def boom(card): raise Surprise("channel")
ch.post_card = boom
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.config import load_config
from hadavin_sdk.registry import load_registry
from tests.conftest import make_cfg, qualify
cd = make_cfg(tmp / "pc"); qualify(load_registry(load_config(cd)))
ap = app_mod.build(cd, ["test-agent"], channel=ch, secrets=FakeSecretProvider({"fixture-token": "t"*8}))
from hadavin_sdk.approvals.cards import Card
import inspect
print("app.py ~471 is the approval-card post, not a banner site; hooks.post_card:", end=" ")
try:
    c = Card.__dataclass_fields__.keys(); card = Card(**{k: ("x" if k not in ("buttons","actions") else ()) for k in c if Card.__dataclass_fields__[k].default is dataclasses.MISSING and Card.__dataclass_fields__[k].default_factory is dataclasses.MISSING})
    print(ap.runtime.hooks.post_card(card))
except BaseException as e: print("RAISED", type(e).__name__, str(e)[:100])
print("banner after that:", ap.mode_banner()["tone"])
