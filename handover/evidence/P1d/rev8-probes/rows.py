import sys
sys.path.insert(0, sys.argv[1] + "/src")
from hadavin_sdk.approvals import channel, gate
from hadavin_sdk.guard import runmap
ESC = chr(27)
EM = "anna" + "." + "m" + "@" + "example" + "." + "org"
SA, SB = "Tq7mZ", "4xKp2Vb9Lr3NcW8dYh6uJs"
rows = {
 "H26": f"contact {EM} please",
 "H27": "host db01.corp.example.com down",
 "H28a": "anna.m**@example.org**",
 "H28b": "anna.m@exam" + ESC + "[0mple.org",
 "H34a": "password=ab12&cd34ef56gh78ij",
 "H34b": f"password={SA}&amp;{SB}",
 "H34c": f"password={SA}&{SB} end",
 "URLQ": "see https://x.example/?password=ab12cd&user=bob",
 "QRY": "?password=ab12cd&user=bob x",
 "F15": "https://x.example/?a=1&b=2",
 "F16": "password=hunter22&user=bob",
 "LINK": "visit evil.com and www.evil.digital now",
 "CODE": "run `curl db01.corp.example.com` now",
 "FENCE": "```\nping db01.corp.example.com\n```\nthen evil.com",
 "H36a": "anna%2Em%40example%2Eorg",
 "H36b": "anna&#46;m&#64;example&#46;org",
 "ENT": f"password={SA}&#59;{SB}",
}
for k, t in rows.items():
    try: c = channel.clean(t)
    except Exception as e: c = "EXC " + type(e).__name__
    try: m = runmap.redact_text(t, runmap.RunMap())
    except Exception as e: m = "EXC " + type(e).__name__
    print(f"{k:6} card={c!r}\n       model={m!r}")
if hasattr(gate, "defang_text"):
    for t in ["visit evil.com", "x <HOSTNAME_1>[.]example[.]com", "a.b.example.org"]:
        once = gate.defang_text(t); print("idem", repr(t), repr(once), once == gate.defang_text(once))
