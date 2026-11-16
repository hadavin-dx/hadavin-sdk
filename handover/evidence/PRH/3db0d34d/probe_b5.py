"""EVIDENCE RUNNER probe for PR H batch 5 (own script, made-up values built from parts).
Usage: python probe_b5.py   (run with the venv of the tree to be probed)
Prints one line per row: for each of the paths untrusted / tool / error / head, which named pieces of the secret
stand in the output (yes = readable), R = call raised or refused, W = output is the withheld note.
"""

import sys

from hadavin_sdk import tools
import importlib

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")
WN = getattr(redact_mod, "WITHHELD_NOTE", "(details withheld)")
from hadavin_sdk.guard import runmap

ESC, BEL = "\x1b", "\x07"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
KEY2 = "AKIA" + "ZZZZODNN7EXAMPL2"
MAIL = "bob.smith" + "@" + "example.com"
PW = "hunter" + "2secretXYZ"
HAND = "Tr0ub4dor" + "-3xyzQ"
i_m = MAIL.index("exam") + 4

# row: (text, pieces {name: string}, handed_out list for tool/error paths)
ROWS = {
    "L1": ("id " + KEY[:4] + ESC + "[0m" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "L2": ("id " + KEY[:4] + "️" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "L3": ("id " + KEY[:4] + "\x08" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "L4": ("to " + MAIL[:i_m] + "️" + MAIL[i_m:], {"MAIL": MAIL, "tail": MAIL[i_m:]}, []),
    "L5": ("pass͏word=" + PW, {"PW": PW}, []),
    "L6": ("auth failed for " + HAND[:9] + ESC + "[0m" + HAND[9:], {"HAND": HAND, "tail": HAND[9:]}, [HAND]),
    "L7": ("password=" + PW[:6] + ESC + "[0m" + PW[6:], {"PW": PW, "tail": PW[6:]}, []),
    "L8": ("id " + KEY[:4] + "\x00" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "L9": ("id " + KEY[:4] + ESC + "(B" + ESC + "[m" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "L10": ("id " + KEY[:4] + "ㅤ" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "L11": ("id " + KEY[:4] + "%1b[0m" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "L12": ("x " + HAND[:5] + "\x9b0m" + HAND[5:], {"HAND": HAND, "tail": HAND[5:]}, [HAND]),
    "M2a": ("id %4%1b[0m1KIA" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "M2b": ("id %4\\x1b[0m1KIA" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
    "G1": ("user" + BEL + KEY, {"KEY": KEY, "tail": KEY[4:]}, []),
    "G2": ("user" + ESC + "[0m" + KEY, {"KEY": KEY, "tail": KEY[4:]}, []),
    "G3": (
        "a " + KEY[:4] + ESC + "[0m" + KEY[4:] + " b user" + BEL + KEY2,
        {"KEY": KEY, "tail": KEY[4:], "KEY2": KEY2, "tail2": KEY2[4:]},
        [],
    ),
    # new rows of this batch
    "a(char-reading)": (
        "a " + ESC + HAND + " ; user" + BEL + KEY,
        {"HAND": HAND, "KEY": KEY, "tail": KEY[4:]},
        [HAND],
    ),
    "b(consuming)": (
        "a " + HAND[:9] + ESC + "(B" + ESC + "[m" + HAND[9:] + " ; user" + BEL + KEY,
        {"HAND": HAND, "tailH": HAND[9:], "KEY": KEY, "tail": KEY[4:]},
        [HAND],
    ),
    "b2(cut HAND by ESC(B ESC[m, no list)": (
        "a " + HAND[:9] + ESC + "(B" + ESC + "[m" + HAND[9:] + " ; user" + BEL + KEY,
        {"KEY": KEY, "tail": KEY[4:]},
        [],
    ),
    "ctl-plain-key": ("id " + KEY, {"KEY": KEY}, []),
    "ctl-plain-hand": ("id " + HAND, {"HAND": HAND}, [HAND]),
    "ctl-tab-cut(not hidden)": ("id " + KEY[:4] + "\t" + KEY[4:], {"KEY": KEY, "tail": KEY[4:]}, []),
}

HANDED_ROWS = {"L6", "L12", "a(char-reading)", "b(consuming)", "ctl-plain-hand"}


def paths(t, handed):
    return {
        "untrusted": lambda: runmap.redact_untrusted(t, {}),
        "tool": lambda: tools.prepare_output(t, {}, 4000, handed),
        "error": lambda: tools.error_reason(ValueError(t), handed),
        "head": lambda: runmap.safe_head(t, 4000),
    }


def verdict(call, pieces, handed_row, path):
    try:
        out = call()
    except Exception as e:  # recorded, not judged
        return "R(" + type(e).__name__ + ")"
    got = [n for n, p in pieces.items() if p in out]
    note = ""
    if out.strip() == WN:
        note = " W"
    no_list = handed_row and path in ("untrusted", "head")
    parts = []
    for n in pieces:
        parts.append(n + "=" + ("yes" if n in got else "no"))
    return ("any=" + ("yes" if got else "no")) + note + (" [no list on this path]" if no_list else "") + " {" + ",".join(parts) + "}"


def main():
    print("python", sys.version.split()[0], "tree", redact_mod.__file__)
    print("table: row | untrusted | tool | error | head   (any=yes: a named piece stands in the output)")
    for name, (t, pieces, handed) in ROWS.items():
        res = []
        for pn, call in paths(t, handed).items():
            res.append(pn + ": " + verdict(call, pieces, name in HANDED_ROWS, pn))
        print(name, "||", " | ".join(res))
    # (d) redact() direct call
    print("--- (d) redact() direct call (guard.redact.redact)")
    cases = {
        "d1 key cut by ESC[0m": "id " + KEY[:4] + ESC + "[0m" + KEY[4:],
        "d2 user BEL key + key cut": "user" + BEL + KEY + " and " + KEY2[:4] + ESC + "[0m" + KEY2[4:],
        "d3 key cut by ESC(B ESC[m": "id " + KEY[:4] + ESC + "(B" + ESC + "[m" + KEY[4:],
        "d4 key cut by title string": "id " + KEY[:4] + ESC + "]0;t" + BEL + KEY[4:],
        "d5 key cut, escape touches non-word": "id =" + ESC + "[0m" + KEY[:4] + ESC + "[0m" + KEY[4:],
        "d6 key cut next to combining mark": "id " + KEY[:4] + "́" + ESC + "[0m" + KEY[4:],
        "d7 email cut at the dot": "to " + MAIL[:3] + ESC + "[0m" + MAIL[3:],
        "d8 key twice cut, one gap on a digit": "id " + KEY[:4] + ESC + "[0m" + KEY[4:11] + ESC + "[1m" + KEY[11:],
    }
    for n, t in cases.items():
        try:
            r = redact_mod.redact(t)
            out = r.text
        except Exception as e:
            print(n, "-> R(" + type(e).__name__ + ")")
            continue
        readable = [p for p in (KEY, KEY[4:], KEY2[4:], MAIL, MAIL[3:]) if p in out]
        print(n, "-> withheld=" + str(out.strip() == WN), "readable_pieces=" + str(len(readable)), "esc_left=" + str(ESC in out), "out=" + repr(out)[:90])
    # d9: mapping already holds a value that the spaced reading cannot show whole: value with a digit/word edge cut by
    # an escape right after a non-word character
    big = " ".join(
        "id " + ("K%03d" % k) + "AKIA" + "ZZZZ%03dODNN7EXA" % k for k in range(300)
    )
    for variant, t in (
        ("d9 300 distinct valid-shaped keys each cut", " ".join("x AKIA" + ("%03d" % k) + ESC + "[0m" + "ABCDEFGHJKLMN" for k in range(300))),
    ):
        try:
            r = redact_mod.redact(t)
            out = r.text
            readable = sum(1 for k in range(300) if "ABCDEFGHJKLMN" in out)
            print(variant, "-> withheld=" + str(out.strip() == WN), "tails_readable=" + str(readable), "esc_left=" + str(ESC in out))
        except Exception as e:
            print(variant, "-> R(" + type(e).__name__ + ")")
    # d10: pre-seeded mapping value that the spaced reading shows only partly
    for n, t, m in (
        ("d10 seeded mapping value cut", "id " + HAND[:9] + ESC + "[0m" + HAND[9:], {"<SECRET_1>": HAND}),
        ("d11 seeded mapping value, escape then letter", ESC + HAND + " x", {"<SECRET_1>": HAND}),
    ):
        try:
            r = redact_mod.redact(t, mapping=dict(m))
            out = r.text
            print(n, "-> withheld=" + str(out.strip() == WN), "HAND_readable=" + str(HAND in out), "tail_readable=" + str(HAND[9:] in out), "out=" + repr(out)[:90])
        except Exception as e:
            print(n, "-> R(" + type(e).__name__ + ")")


main()
