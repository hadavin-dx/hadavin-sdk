"""P10: N8 (backtick pairing across lines) rows. usage: PYTHONPATH=<tree>/src python p10_n8.py"""
from hadavin_sdk.approvals import channel, gate
SV_B = "4xKp2Vb9Lr3NcW8dYh6uJs"
for x in ["`a\nevil.com` b evil.com", "x `evil.com\ny` z evil.com", "see `a` and evil.com", "`a evil.com password=" + SV_B + "` b",
          "see ``note `evil.com` x`` now", "```\nevil.com\n```\nthen evil.com", "a ` b\nevil.com ` c", "use \\`evil.com\\` now", "`x` ` y\nevil.com", "run `curl db01.corp.example.com` now"]:
    print(repr(x), "->", repr(gate.defang_text(x)))
