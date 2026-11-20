"""G9 evidence: the honest worst shapes at the size cap and the two hostile ones of the cost table (H1 forged copies of a long secret's key,
H2 overlapping pairs to the cap), as `SHAPES`. Imported by g9_cost.py and g9_hostile.py (the tree is argv[1]). Every credential is made up."""

import importlib
import sys
import time

tree = sys.argv[1]
sys.path.insert(0, tree + "/src")
R = importlib.import_module("hadavin_sdk.guard.redact")
from hadavin_sdk import defaults  # noqa: E402
from hadavin_sdk.guard import runmap  # noqa: E402

CAP = defaults.MAX_REDACT_CHARS
JWT = "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiJ1c2VyMSJ9" + "." + "c2lnbmF0dXJlMTIzNDU2Nzg5"
SIG = ("sig" + "AbCdEfGh") * 8


def jar(lines, sig):
    rows = []
    for k in range(1, lines + 1):
        cookies = ";".join(f"a{(k - j) % 10}=1" for j in range(k))
        rows.append(f"Cookie: {cookies}; sid={JWT}~{SIG[:sig]}")
    return "\n".join(rows)


def cookie(lines):
    return "\n".join(f"Cookie: _ga=GA1.2{'x' * k}; theme=dark; sid={JWT}" for k in range(lines))


def signed(lines):
    v = "0b5d2c1e-7f3a-4c9d-8e21-5a6b7c8d9e0f"
    return "\n".join(f"password={v}.sig{n}" for n in range(lines))


def uuids5000():
    import random
    import uuid

    rng = random.Random(4242)  # noqa: S311
    return "\n".join(f"password={uuid.UUID(int=rng.getrandbits(128))}.k_{i % 10}" for i in range(5000))


def fill(text):
    """the text, then its lines again as raw copies, to the cap"""
    out = text
    while len(out) + 1 + len(text) <= CAP:
        out += "\n" + text
    return out[:CAP]


SHAPES = {
    "curl -u at cap": ("curl -u " * (CAP // 8 + 1))[:CAP],
    "password= at cap": ("password= " * (CAP // 10 + 1))[:CAP],
    "jar 330x64 + copies to cap": fill(jar(330, 64)),
    "jar 275x128 + copies to cap": fill(jar(275, 128)),
    "cookie 300 prefix lengths + copies to cap": fill(cookie(300)),
    "signed ids 300 + copies to cap": fill(signed(300)),
    "5000 password=uuid.k_i (250k)": uuids5000(),
}

import random  # noqa: E402
import string  # noqa: E402


def overlaps_at_cap():
    rng = random.Random(9); al = string.ascii_letters + string.digits; head, see = [], []
    while True:
        base = "".join(rng.choice(al) for _ in range(20)); a, b = base[:12], base[6:]
        head.append(f"password={a}\ntoken={b}"); see.append(f"see {base} end")
        t = "\n".join(head + see)
        if len(t) > CAP - 200: return t
def forged():
    long = ("Qz9" * 700)[:2000]
    return ("password=" + long + "\n" + ("x<SECRET_1> " * 30000))[:CAP]
SHAPES["H1 forged copies of a 2,000-char secret's key"] = forged()
SHAPES["H2 overlapping pairs to the cap"] = overlaps_at_cap()
