"""Issue 4/10: the fixed-seed fuzz (seed 20261112, 3000 texts, same generator as the independent evidence). Records, per text,
whether an 8-character window of the handed-out value or of the allowed example key stands in prepare_output's output, and
whether the output is withheld. Usage: python fuzz_classify.py [N] -> prints summary; with --dump FILE writes per-text JSON lines."""

import json
import random
import sys

from hadavin_sdk import tools
from hadavin_sdk.guard import runmap

ESC = "\x1b"
HAND = "Qx7mLp" + "-9vRtzKw2"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
HID = [
    ESC + "[0m",
    ESC + "[31m",
    ESC + "(B",
    "\u200b",
    "\u202e",
    "\u2066",
    "\x07",
    "%1b",
    "&#27;",
    "\\u001b",
    ESC,
]
WORDS = ["ok", "error", "Company", "user", "log line", "10.0.0.1", "done"]


def piece(r):
    k = r.random()
    if k < 0.25:
        return r.choice(WORDS)
    if k < 0.45:
        return HAND
    if k < 0.55:
        return KEY
    if k < 0.75:
        s = r.choice([HAND, KEY])
        i = r.randrange(1, len(s))
        return s[:i] + r.choice(HID) + s[i:]
    return r.choice(HID)


def texts(n=3000):
    r = random.Random(20261112)
    for _ in range(n):
        yield " ".join(piece(r) for _ in range(r.randrange(2, 9)))


def windows(o):
    return [s[i : i + 8] for s in (HAND, KEY) for i in range(len(s) - 7) if s[i : i + 8] in o]


CAUSE = {"piece": False, "limit": False}
_hp = getattr(tools, "_has_piece", None)
if _hp:

    def _wrap_piece(*a, **k):
        r = _hp(*a, **k)
        CAUSE["piece"] = CAUSE["piece"] or r
        return r

    tools._has_piece = _wrap_piece
_ru = tools.runmap.redact_untrusted


def _wrap_ru(*a, **k):
    try:
        return _ru(*a, **k)
    except getattr(tools.runmap, "RedactionLimit", ()):
        CAUSE["limit"] = True
        raise


tools.runmap.redact_untrusted = _wrap_ru


def strict(o):
    return o == tools.MARKER + tools.TRUNCATED or "withheld" in o


def run(n=3000):
    for t in texts(n):
        CAUSE["piece"] = CAUSE["limit"] = False
        try:
            o = tools.prepare_output(t, {}, 4000, [HAND])
        except runmap.RedactionError as e:  # the redactor's own errors (InputTooLarge, RedactionLimit) are counted; any other error stops the run
            yield t, None, type(e).__name__
            continue
        yield t, o, None


if __name__ == "__main__":
    dump = sys.argv[sys.argv.index("--dump") + 1] if "--dump" in sys.argv else None
    rows = []
    w = rd = st = 0
    exc = {}
    causes = {}
    for t, o, e in run():
        if e:
            exc[e] = exc.get(e, 0) + 1
            continue
        withheld = (
            o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == ""
            or "withheld" in o
        )
        win = windows(o)
        w += withheld
        rd += bool(win)
        sw = strict(o)
        st += sw
        if sw:
            c = "limit" if CAUSE["limit"] else "piece" if CAUSE["piece"] else "readings-or-other"
            causes[c] = causes.get(c, 0) + 1
        rows.append(json.dumps({"t": t, "o": o, "withheld": withheld, "strict": sw, "win": win}))
    print("tree", tools.__file__)
    print(
        "markers-only-or-withheld (the independent runner's count)",
        w,
        "| strict withheld (MARKER+TRUNCATED or note)",
        st,
        "| causes",
        causes,
        "| readable windows",
        rd,
        "| exceptions",
        exc,
    )

    if dump:
        with open(dump, "w") as f:
            f.write("\n".join(rows) + "\n")
