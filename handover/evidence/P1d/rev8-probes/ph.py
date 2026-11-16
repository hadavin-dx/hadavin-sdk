import sys, re
sys.path.insert(0, sys.argv[1] + "/src")
from hadavin_sdk.approvals import gate, channel
PH_DOT = re.compile(r"(<[A-Z][A-Z0-9]*_\d+>)\.(?=[\w-])")
def defang_text(t):
    return gate.defang_text(PH_DOT.sub(r"\1[.]", t))
for t in ["host <HOSTNAME_1>.example.com down", "x <EMAIL_1>. Next", "run `<HOSTNAME_1>.example.com`", "visit evil.com"]:
    a = defang_text(t); print(repr(t), "->", repr(a), "idem", a == defang_text(a))
print(repr(defang_text(channel.clean("host db01.corp.example.com down"))))
