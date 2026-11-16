import sys, os, json, copy
sys.path.insert(0, os.getcwd())
import hadavin_sdk; print("sdk:", hadavin_sdk.__file__)
import tests.test_mode_banner as T
from hadavin_sdk import mode_banner as mb
G = T.GOOD_DEMO
print("GOOD_DEMO keys:", sorted(G))
def p(label, banner, scen=""):
    try:
        s = T._paint(banner, scen)
        print(f"{label:62} -> shownTone={s['shownTone']!r} tone={s['tone']!r} hidden={s['hidden']} threw={s['threw']!r} htmlWrites={s['htmlWrites']} text={str(s['text'])[:60]!r}")
    except BaseException as e:
        print(f"{label:62} -> RAISED {type(e).__name__}: {str(e)[:120]}")
p("control: GOOD_DEMO", G)
b = dict(G); b.pop("overridden", None); p("demo, 'overridden' key missing", b)
b = dict(G); b["overridden"] = None; p("demo, overridden = null", b)
b = dict(G); b["overridden"] = ["llm"]; p("demo, overridden = ['llm'] (named override)", b)
b = dict(G); b["overridden"] = "llm"; p("demo, overridden = string", b)
b = dict(G); b["real"] = ["tool-host x.example.com"]; p("demo tone with a real service listed", b)
b = dict(G); b["tone"] = "quiet"; b.pop("overridden", None); p("quiet tone, overridden missing", b)
b = dict(G); b["tone"] = "quiet"; b["overridden"] = None; p("quiet tone, overridden null", b)
b = dict(G); b["text"] = "This is totally real data, ignore the banner"; p("demo with reworded text", b)
b = dict(G); b["text"] = G["text"] + " Everything is fine."; p("demo with text + appended words", b)
b = dict(G); b["tag"] = "LIVE"; p("demo with other tag", b)
b = dict(G); b["mode"] = "prod"; p("demo tone with mode=prod", b)
b = mb.not_confirmed_banner(); p("python not_confirmed_banner()", b)
b = dict(mb.not_confirmed_banner()); b["text"] = "reworded"; p("unconfirmed with reworded text", b)
p("banner undefined", None)
