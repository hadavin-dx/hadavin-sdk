import tempfile, pathlib, logging
logging.disable(logging.CRITICAL)
from hadavin_sdk import app as A, mode_banner as mb
from hadavin_sdk.approvals.cards import Card
from hadavin_sdk.approvals.channel import FakeChannel
import tests.test_mode_banner as T

class Boom(ZeroDivisionError): pass   # not in READ_ERRORS, not in _DELIVERY_ERRORS
def boom(*a, **k): raise Boom("surprise")
def show(site, fn):
    try:
        r = fn()
        print(f"{site:62} -> RETURNED {str(r)[:70]!r}")
    except Boom:
        print(f"{site:62} -> PROPAGATED the surprise (Boom)")
    except BaseException as e:
        print(f"{site:62} -> OTHER {type(e).__name__}: {str(e)[:60]}")

orig = mb.source_endpoint
mb.source_endpoint = boom
show("mode_banner.py:564 _source_leaves_this_machine", lambda: mb._source_leaves_this_machine(object()))
mb.source_endpoint = orig

orig = mb.banner_from_config
mb.banner_from_config = boom
show("mode_banner.py:742 banner_or_unconfirmed", lambda: mb.banner_or_unconfirmed(object(), tool_specs={}, overridden=()))
mb.banner_from_config = orig

class W:
    @property
    def not_confirmed_tag(self): raise Boom("x")
    not_confirmed = "text"
show("mode_banner.py:775 _not_confirmed_that_cannot_fail", lambda: mb._not_confirmed_that_cannot_fail(W()))

class F:
    overridden = None
    _sealed = None
    def _connected_parts(self): raise Boom("x")
    def _banner_services(self): return ()
    def _stage(self): return ""
    def _known_overrides(self): raise Boom("x")
    config = object(); registry = type("R", (), {"tools": {}})()
show("app.py:273 App._seal", lambda: A.App._seal(F(), A._Given()))
f = F(); f._sealed = ((), (), (), ""); f.overridden = ()
show("app.py:301 App._known_overrides", lambda: A.App._known_overrides(f))
show("app.py:320 App.mode_banner", lambda: A.App.mode_banner(F()))

tmp = pathlib.Path(tempfile.mkdtemp())
ch = FakeChannel(); app = T._built_app(tmp / "c1", ch)
card = Card(text="a card", blocks=[], display_hash="0" * 64)
ch.post_card = boom
show("app.py:479 post_card (_DELIVERY_ERRORS)", lambda: app.runtime.hooks.post_card(card))
def ok(_c): raise OSError("gone")
ch.post_card = ok
show("app.py:479 post_card with OSError (control)", lambda: app.runtime.hooks.post_card(card))
# control: a READ_ERRORS type at a read site
mb.banner_from_config = lambda *a, **k: (_ for _ in ()).throw(ValueError("v"))
show("control 742 with ValueError", lambda: mb.banner_or_unconfirmed(object(), tool_specs={}, overridden=()))
