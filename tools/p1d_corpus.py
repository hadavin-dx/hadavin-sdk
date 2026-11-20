"""P1d-a test tooling (ticket revision 5): the base-row check (BS-0), the frozen gate fixture, and the BS-1 corpus.

Run from the worktree root as ``python -m tools.p1d_corpus ...``. Made-up data only. No product code is changed.

    --rows --out FILE --fixture JSON     run every row on the code that is imported; exit 0 if all cells FIT, 3 otherwise
    --freeze-gate --out JSON             write the gate's output on every LIT string (run on the base)
    --kind amp --seed 1 --path both --out FILE   the BS-1 over-mask and leak corpus; exit 0 within the gates, 4 otherwise
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from tests.fixtures import p1d_cases as C

_PH = re.compile(r"<[A-Z][A-Z0-9]*_[0-9]+>")


def _git_head() -> str:
    try:
        r = subprocess.run(
            ["/usr/bin/git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
        )
        return r.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def _pkg_path() -> str:
    import hadavin_sdk

    return str(Path(hadavin_sdk.__file__).resolve().parent)


def _run(row_id: str, entry: str, x: str) -> tuple[str, dict]:
    try:
        return C.run_entry(row_id, entry, x)
    except C.NewSurface as exc:
        return str(exc), {}


def _fit(row: C.Row, entry: str, out: str, ctx: dict, base_json: dict) -> str:
    cell = C.cell(row.base, entry)
    after = C.cell(row.after, entry)
    new_surface = out.startswith("NEW_SURFACE")
    if cell == C.NS:
        return "FIT" if new_surface else "MISMATCH"
    if new_surface:
        return "FIT" if row.cls == "fb" else "MISMATCH"
    if cell != C.BS0 and out != cell:
        return "MISMATCH"
    extra = (
        C.check_extra(row.id, entry, out, ctx, after=False) if row.id in ("L8", "T1", "W1") else ""
    )
    if extra:
        return f"MISMATCH: {extra}"
    # class fit, on the written or recorded base output
    exp_after = out if after == C.SAME else (None if after in (C.BS0, C.ASSERTS) else after)
    if row.cls == "fb" and exp_after is not None and out == exp_after:
        return "MISFIT: fb row whose base equals its expected after"
    if row.cls == "ow" and exp_after is not None and out == exp_after:
        return "MISFIT: ow row whose base equals its expected after"
    if row.cls == "pb" and after not in (C.SAME, C.BS0, C.ASSERTS) and out != after:
        return "MISFIT: pb row whose base differs from its expected after"
    return "FIT"


def cmd_rows(args) -> int:
    from hadavin_sdk.guard import runmap

    lines = [f"base {_git_head()}", f"hadavin_sdk {_pkg_path()}"]
    rows_json: dict[str, str] = {}
    bad = 0
    for row in C.ROWS:
        for entry in row.entries:
            out, ctx = _run(row.id, entry, row.input)
            rows_json[f"{row.id}/{entry}"] = out
            status = _fit(row, entry, out, ctx, rows_json)
            bad += status != "FIT"
            lines.append(f"{row.id}\t{entry}\t{json.dumps(out, ensure_ascii=True)}\t{status}")
    info = runmap.redact_text("a" * 41 + "password=hunter22 x", runmap.RunMap())
    lines.append(f"INFO-K41\t{json.dumps(info, ensure_ascii=True)}")
    lines.append(f"LIT\t{len(C.lit_strings())}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    if args.fixture:
        payload = {"base": _git_head(), "rows": rows_json}
        Path(args.fixture).write_text(
            json.dumps(payload, indent=1, ensure_ascii=True, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(f"rows={sum(len(r.entries) for r in C.ROWS)} not_fit={bad}")
    return 3 if bad else 0


def cmd_freeze(args) -> int:
    from hadavin_sdk.approvals import gate

    lit = C.lit_strings()
    frozen = {x: gate.sanitise_text(x) for x in lit}
    payload = {"base": _git_head(), "count": len(lit), "frozen": frozen}
    Path(args.out).write_text(
        json.dumps(payload, indent=1, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"frozen={len(lit)}")
    return 0


# --- BS-1 ---------------------------------------------------------------------------------------------------------
S_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!$%*+-./:@^_~"
KEYS = ["password", "passwd", "pwd", "api_key", "token", "client_secret", "auth_token"]
WORDS20 = [
    "alpha",
    "bravo",
    "charlie",
    "delta",
    "echo",
    "foxtrot",
    "golf",
    "hotel",
    "india",
    "juliet",
    "kilo",
    "lima",
    "mike",
    "november",
    "oscar",
    "papa",
    "quebec",
    "romeo",
    "sierra",
    "tango",
]
FIELD_KEYS = ["user", "next", "page", "lang", "id", "ref"]
ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"
FLAGS = ["&debug", "&raw", "&x1"]


class Gen:
    def __init__(self, shape: str, seed: int = 1) -> None:
        self.s = f"BS1-{shape}"
        self.draws = C.Draws(seed)
        self.redraws = 0

    def d(self, n):
        return self.draws.d(self.s, n)

    def pick(self, seq):
        return self.draws.pick(self.s, seq)

    def plain_secret(self) -> str:
        return "".join(self.pick(S_ALPHABET) for _ in range(8 + self.d(33)))

    def with_amps(self, base: str) -> str:
        chars = list(base)
        positions: list[int] = []
        for _ in range(1 + self.d(3)):
            for _try in range(1000):
                p = 1 + self.d(len(base) - 2)
                if all(abs(p - q) > 1 for q in positions):
                    positions.append(p)
                    break
        for p in positions:
            chars[p] = "&"
            chars[p + 1] = self.pick(C.LETTERS)
        return "".join(chars)

    def accepted(self, s: str) -> bool:
        from hadavin_sdk.guard import runmap

        return runmap.redact_text("x " + s + " y", runmap.RunMap()) == "x " + s + " y"

    def secret(self, amps: bool) -> str:
        while True:
            s = self.plain_secret()
            if amps:
                s = self.with_amps(s)
            if self.accepted(s):
                return s
            self.redraws += 1

    def words(self) -> str:
        return " " + " ".join(self.pick(WORDS20) for _ in range(1 + self.d(6)))

    def fields(self) -> str:
        out = ""
        for _ in range(1 + self.d(3)):
            k = self.pick(FIELD_KEYS)
            v = "".join(self.pick(ALNUM) for _ in range(1 + self.d(12)))
            out += f"&{k}={v}"
        return out

    def fields_maybe_words(self) -> str:
        f = self.fields()
        return f + (self.words() if self.d(2) == 1 else "")

    def tail(self, kind: str | None = None) -> str:
        kind = kind or self.pick(["END", "WORDS", "SEMI", "QUOTE"])
        t = {
            "END": "",
            "WORDS": self.words(),
            "SEMI": ";" + self.words(),
            "QUOTE": '"' + self.words(),
        }[kind]
        if len(t) > 100:
            t = t[: t.rfind(" ", 0, 100)]
        return t


def norm(s: str) -> str:
    return _PH.sub("<P>", s.replace("[.]", ".").replace(C.ZW, ""))


def inner_placements(n: int) -> list[tuple[int, ...]]:
    inner = list(range(1, n - 1))
    singles = [(p,) for p in inner]
    pairs = [(p, q) for p in inner for q in inner if q - p >= 2]
    return singles + pairs


def exhaustive_secrets() -> list[str]:
    g = Gen("X")
    out = []
    for n in (8, 9, 10):
        base = "".join(
            g.pick("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
            for _ in range(n)
        )
        for pl in inner_placements(n):
            chars = list(base)
            for p in pl:
                chars[p] = "&"
                chars[p + 1] = g.pick(C.LETTERS)
            out.append("".join(chars))
    return out


def build_samples() -> dict[str, list[tuple[str, str, str, str]]]:
    """shape -> list of (input, prefix, hidden, tail); the expected output is prefix + <P> + tail."""
    shapes: dict[str, list[tuple[str, str, str, str]]] = {}
    redraws: dict[str, int] = {}

    def query(g: Gen, key: str, hidden: str, flags: str, rest: str):
        prefix = f"GET /p?{key}="
        return (prefix + hidden + flags + rest, prefix, hidden + flags, rest)

    for shape, n, amps in (("S1", 50, False), ("S2", 25, True)):
        g = Gen(shape)
        shapes[shape] = []
        for _ in range(n):
            key = g.pick(KEYS)
            s = g.secret(amps)
            shapes[shape].append(
                query(g, key, s, "", g.fields_maybe_words() if not amps else g.fields())
            )
        redraws[shape] = g.redraws
    g = Gen("S2x")
    shapes["S2x"] = []
    for s in exhaustive_secrets():
        key = g.pick(KEYS)
        shapes["S2x"].append(query(g, key, s, "", g.fields()))
    g = Gen("S3")
    shapes["S3"] = []
    for _ in range(25):
        key = g.pick(KEYS)
        s = g.secret(False)
        flags = "".join(g.pick(FLAGS) for _ in range(1 + g.d(2)))
        shapes["S3"].append(query(g, key, s, flags, g.fields()))
    redraws["S3"] = g.redraws
    for shape, n, amps in (("S4", 50, False), ("S5", 50, True)):
        g = Gen(shape)
        shapes[shape] = []
        for _ in range(n):
            key = g.pick(KEYS)
            s = g.secret(amps)
            tail = g.tail()
            shapes[shape].append((f"{key}={s}{tail}", f"{key}=", s, tail))
        redraws[shape] = g.redraws
    g = Gen("S5x")
    shapes["S5x"] = []
    for s in exhaustive_secrets():
        key = g.pick(KEYS)
        for kind in ("END", "WORDS", "SEMI", "QUOTE"):
            tail = g.tail(kind)
            shapes["S5x"].append((f"{key}={s}{tail}", f"{key}=", s, tail))
    g = Gen("S6")
    shapes["S6"] = []
    for _ in range(50):
        key = g.pick(KEYS)
        s = g.secret(False)
        f = g.fields()
        words = g.words() if g.d(2) == 1 else ""
        shapes["S6"].append((f"{key}={s}{f}{words}", f"{key}=", s + f, words))
    redraws["S6"] = g.redraws
    g = Gen("S7")
    shapes["S7"] = []
    for _ in range(20):
        key = g.pick(KEYS)
        a = "".join(g.pick(S_ALPHABET) for _ in range(4 + g.d(9)))
        b = "".join(g.pick(S_ALPHABET) for _ in range(4 + g.d(9)))
        name = g.pick(C.LETTERS) + g.pick(C.LETTERS)
        f = g.fields()
        prefix = f"GET /p?{key}="
        # N4: the URL grammar reads `&name=` as a new field; the part after it is shown.
        shapes["S7"].append(
            (prefix + a + "&" + name + "=" + b + f, prefix, a, "&" + name + "=" + b + f)
        )
    shapes["REAL"] = []
    for _id, line, hidden in C.REAL:
        i = line.index(hidden)
        shapes["REAL"].append((line, line[:i], hidden, line[i + len(hidden) :]))
    shapes["_redraws"] = redraws  # type: ignore[assignment]
    return shapes


def classify(out: str, prefix: str, tail: str) -> str:
    o, p, t = norm(out), norm(prefix), norm(tail)
    exp = p + "<P>" + t
    if o == exp:
        return "exact"
    if o.startswith(p + "<P>") and len(o) < len(exp) and t.endswith(o[len(p) + 3 :]):
        return "OVERMASK"
    if (
        o.startswith(p)
        and o.endswith(t)
        and len(o) >= len(p) + len(t)
        and o[len(p) : len(o) - len(t)] != "<P>"
    ):
        return "LEAK"
    return "OTHER"


GATED = {"S1", "S2", "S2x", "S3", "S4", "S5", "S5x", "S6", "REAL"}
COUNTS = {
    "S1": 50,
    "S2": 25,
    "S2x": 67,
    "S3": 25,
    "S4": 50,
    "S5": 50,
    "S5x": 268,
    "S6": 50,
    "S7": 20,
    "REAL": 30,
}


def cmd_amp(args) -> int:
    from hadavin_sdk.guard import runmap

    shapes = build_samples()
    redraws = shapes.pop("_redraws")  # type: ignore[arg-type]
    paths = {"card": C.e_card, "model": C.e_model}
    if args.path != "both":
        paths = {args.path: paths[args.path]}
    lines = [f"base {_git_head()}", f"hadavin_sdk {_pkg_path()}", f"seed {args.seed}"]
    failed = False
    shown_bad = 0
    total = 0
    for shape, samples in shapes.items():
        if len(samples) != COUNTS[shape]:
            raise SystemExit(f"BS-1 sample count of {shape}: {len(samples)}")
        total += len(samples)
        for pname, fn in paths.items():
            tally = {"exact": 0, "LEAK": 0, "OVERMASK": 0, "OTHER": 0}
            longest = 0
            for text, prefix, hidden, tail in samples:
                out = fn(text)
                label = classify(out, prefix, tail)
                tally[label] += 1
                o = norm(out)
                if label == "OVERMASK":
                    longest = max(
                        longest, len(hidden) + len(norm(tail)) - len(o[len(norm(prefix)) + 3 :])
                    )
                else:
                    longest = max(longest, len(hidden))
                if label != "exact" and shown_bad < 400:
                    shown_bad += 1
                    lines.append(
                        f"  {label} {shape} {pname}: input={text!r} output={out!r} expected={norm(prefix) + '<P>' + norm(tail)!r}"
                    )
            lines.append(
                f"{shape}\t{pname}\tsamples={len(samples)}\tredraws={redraws.get(shape, 0)}\texact={tally['exact']}"
                f"\tLEAK={tally['LEAK']}\tOVERMASK={tally['OVERMASK']}\tOTHER={tally['OTHER']}\tlongest_hidden={longest}"
            )
            if shape in GATED and tally["exact"] != len(samples):
                failed = True
    lines.append(f"total samples {total}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(line for line in lines if not line.startswith("  "))[-1800:])
    del runmap
    return 4 if failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", action="store_true")
    ap.add_argument("--freeze-gate", action="store_true")
    ap.add_argument("--kind")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--path", default="both", choices=["both", "card", "model"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--fixture")
    args = ap.parse_args(argv)
    if args.rows:
        return cmd_rows(args)
    if args.freeze_gate:
        return cmd_freeze(args)
    if args.kind == "amp":
        return cmd_amp(args)
    ap.error("choose --rows, --freeze-gate or --kind amp")
    return 2


if __name__ == "__main__":
    sys.exit(main())
