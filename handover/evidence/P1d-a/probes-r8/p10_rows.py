"""P10: new and re-checked rows on a tree. usage: PYTHONPATH=<tree>/src python p10_rows.py  (prints row, entry, repr(output))"""
import sys
from types import SimpleNamespace
from hadavin_sdk.approvals import channel, gate, slack_channel
from hadavin_sdk.guard import runmap
EM = "anna" + "." + "m" + "@" + "example" + "." + "org"
SV_B = "4xKp2Vb9Lr3NcW8dYh6uJs"
sl = slack_channel.SlackChannel.__new__(slack_channel.SlackChannel); sl.max_card_chars = 2900
def slack(x):
    req = SimpleNamespace(summary=x, current_step=0, steps=[1], approval_id="a", status="PENDING")
    return sl._blocks(req, None)[0]["text"]["text"]
def model(x): return runmap.redact_text(x, runmap.RunMap())
def gate0(x): return gate.sanitise_text(x, defang=False) if "defang" in gate.sanitise_text.__code__.co_varnames or True else None
def tryit(f, x):
    try: return f(x)
    except Exception as e: return f"{type(e).__name__}: {e}"[:80]
R = [
 ("N9a", "card", channel.clean, "see //evil。com/p now"), ("N9a", "slack", slack, "see //evil。com/p now"),
 ("N9b", "gate", gate0, "see //evil。com/p now"), ("N9c", "default", gate.sanitise_text, "see //evil。com/p now"),
 ("N9d", "card", channel.clean, "visit www。evil。digital now"), ("N9e", "card", channel.clean, "x `//evil。com/p` y"),
 ("N9f", "card", channel.clean, "see //evil．com now"),
 ("N8a", "defang", gate.defang_text, "x ` y\n` evil.com `"), ("N8b", "defang", gate.defang_text, "`a\nevil.com` b evil.com"),
 ("N8c", "defang", gate.defang_text, "use \\`evil.com\\` now"), ("N8d", "card", channel.clean, "x ` y\n` evil.com `"),
 ("N8e", "defang", gate.defang_text, "a ` b\nevil.com ` c"),
 ("D5a", "defang", gate.defang_text, "see www.evil.digitalg‹.2 now"),
 ("E2", "model", model, EM + EM), ("E2", "card", channel.clean, EM + EM), ("E2b", "model", model, "a " + EM + " b"),
 ("E2c", "model", model, EM + "x" + EM),
 ("BTK1", "card", channel.clean, "`a evil.com password=" + SV_B + "` b"), ("BTK1", "slack", slack, "`a evil.com password=" + SV_B + "` b"),
 ("BTK2", "card", channel.clean, "`a https://evil.com/p password=" + SV_B + "` b"), ("BTK2", "slack", slack, "`a https://evil.com/p password=" + SV_B + "` b"),
 ("MENT1", "card", channel.clean, "`<!channel> x password=" + SV_B + "` b"), ("MENT1", "slack", slack, "`<!channel> x password=" + SV_B + "` b"),
 ("D3g", "defang", gate.defang_text, "total <MONEY_1>.50 due"),
]
for r, e, f, x in R:
    print(r, e, repr(tryit(f, x)))
