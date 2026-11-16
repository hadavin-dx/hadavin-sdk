"""P9: the three card properties on the final grammar, 2,000 texts each.  usage: PYTHONPATH=<tree>/src python p9_props.py [A|B]
A = 'defang_text idempotent', 'no link outside code on the card'; B = 'stored card round trip'.  Generator as the ticket's `d`/`pick`."""
import hashlib, sys, collections
from hadavin_sdk.approvals import channel, gate
from hadavin_sdk.guard import runmap
SEED = 20261109
K = collections.Counter()
def d(stream, n):
    k = K[stream]; K[stream] += 1
    return int.from_bytes(hashlib.sha256(f"{SEED}:{stream}:{k}".encode()).digest()[:8], "big") % n
def pick(stream, seq): return seq[d(stream, len(seq))]
EM = "anna" + "." + "m" + "@" + "example" + "." + "org"
SV_B = "4xKp2Vb9Lr3NcW8dYh6uJs"
LET = list("abcdefghijklmnopqrstuvwxyz"); DIG = list("0123456789")
SINGLE = [" ", "\n", ".", "@", "-", "_", "=", "&", "?", "/", ":", "#", ">", "*", "[", "]", "<", "é", "例", "`"]
WIDE = ["。", "．", "｡"]
TOK = ["```", "~~~", "[.]", "evil.com", "www.evil.digital", "db01.corp.example.com", EM, "<HOSTNAME_1>", "<EMAIL_1>", "password=", "?password=", SV_B, "-----BEGIN PRIVATE KEY-----"]
A = LET + DIG + SINGLE + WIDE + TOK
assert len(A) == 72, len(A)
B = [x for x in A if x not in ("[", "]", "[.]", *WIDE)]
assert len(B) == 66, len(B)
def gen(stream, alpha, count):
    K.clear()
    return ["".join(pick(stream, alpha) for _ in range(d(stream, 201))) for _ in range(count)]
def second(c):
    withheld = gate.withhold_commands(gate.undefang_text(c))
    seeded = runmap.RunMap({ph: "\0seed" + ph for ph in (m.group(0) for m in runmap.PLACEHOLDER.finditer(withheld))})
    return channel.redact_for_card(withheld, seeded)
def links(c):
    out = []
    for t in gate._MD.parse(c):
        for ch in (t.children or []):
            if ch.type == "text" and (gate._DOMAIN.search(ch.content) or gate._NON_ASCII_HOST.search(ch.content)
                                      or gate._PLACEHOLDER_DOT.search(ch.content) or gate._WIDE_DOTS.search(ch.content)):
                out.append(ch.content)
    return out
which = sys.argv[1] if len(sys.argv) > 1 else "A"
if which == "A":
    xs = gen("TXT-A", A, 2000)
    idem = [x for x in xs if gate.defang_text(gate.defang_text(x)) != gate.defang_text(x)]
    nolink, cls = [], collections.Counter()
    for x in xs:
        c = channel.clean(x)
        if links(c):
            nolink.append(x)
            cls["backtick" if "`" in x else "no-backtick"] += 1
    print("TXT-A texts", len(xs), "idempotent failures", len(idem), "no-link failures", len(nolink), dict(cls))
    for x in sorted(nolink, key=len)[:3]: print(" min", repr(x), "->", repr(channel.clean(x)))
    for x in sorted(idem, key=len)[:3]: print(" idem min", repr(x))
else:
    xs = gen("TXT-B", B, 2000)
    bad, kinds = [], collections.Counter()
    for x in xs:
        c = channel.clean(x)
        if len(c) > 2900: continue
        s = second(c)
        if s != c:
            bad.append((x, c, s))
            kinds["only-placeholders-added" if s.replace("[.]", ".") != c.replace("[.]", ".") and runmap.PLACEHOLDER.sub("", s) == runmap.PLACEHOLDER.sub("", c) else "other"] += 1
    print("TXT-B texts", len(xs), "round-trip failures", len(bad), dict(kinds))
    for x, c, s in sorted(bad, key=lambda t: len(t[0]))[:4]: print(" min", repr(x), "\n   clean", repr(c), "\n   slack", repr(s))
