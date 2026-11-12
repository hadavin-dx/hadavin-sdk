"""PR H: the inputs of the hidden-item tests (T1 and T6) and the recorder that runs them on MAIN.

Two uses. (1) Imported by `tests/test_prh_contract.py` and `tests/test_prh_clean_corpus.py`, which build the same inputs
and run them on the branch. (2) Run once as a script with main's source first on the import path, it records for every
(input, path) pair whether MAIN masks the value (`prh_main_verdicts.json`) and for every corpus item how many
placeholders MAIN writes (`prh_main_corpus.json`). The first output line names the directory the code was loaded from.

It imports the oracle (`tests/hidden_oracle.py`, which imports nothing from the package) and never
`hadavin_sdk.guard.hidden`, which main does not have. Every value is made up and built from parts; every control or
invisible character is written as an escape or `chr()`."""

from __future__ import annotations

import html
import importlib
import json
import sys
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

ESC, BEL, NUL = "\x1b", "\x07", "\x00"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
MAIL = "bob.smith" + "@" + "example.com"
PW = "hunter" + "2secretXYZ"
HAND = "Tr0ub4dor" + "-3xyzQ"
TOK = "abcDEF123456" + "ghiJKL7890mnop"
JWT = (
    "eyJhbGciOiJIUzI1NiJ9"
    + "."
    + "eyJzdWIiOiIxMjM0NTY3ODkwIn0"
    + "."
    + "sig1Abc2Def3Ghi4Jkl5Mno6Pqr7S"
)
UUID = "123e4567" + "-e89b-12d3-" + "a456-426614174000"
PEM_BODY = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC" + "BKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj"
PLACEHOLDER_LITERAL = "<" + "IPV4_2" + ">"
CAP = 262144

PATHS = ("untrusted", "tool", "error", "head", "card", "value", "direct")
PROMISED_PATHS = ("untrusted", "tool", "error", "head", "card", "value")
HANDED_PATHS = ("tool", "error")

# ---- the items (section 5, T1) ------------------------------------------------------------------------------------

REMOVED_SINGLES = [
    chr(c)
    for c in list(range(0x09))
    + list(range(0x0E, 0x1C))
    + [0x7F]
    + list(range(0x80, 0x85))
    + list(range(0x86, 0xA0))
]
SPACE_LIKE_ITEMS = ["\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x1f", "\x85", " ", " "]
SEQUENCES = {
    "csi7": ESC + "[0m",
    "csi8": "\x9b0m",
    "csi_private": ESC + "[?25l",
    "csi_inter": ESC + "[0 q",
    "csi_c0": ESC + "[1\x08m",
    "csi_can": ESC + "[1\x18",
    "osc_bel": ESC + "]0;t" + BEL,
    "osc_st": ESC + "]0;t" + ESC + "\\",
    "osc_c1st": ESC + "]0;t\x9c",
    "osc_open": ESC + "]0;t",
    "dcs": ESC + "Pq" + ESC + "\\",
    "sos": ESC + "Xq" + ESC + "\\",
    "pm": ESC + "^q" + ESC + "\\",
    "apc": ESC + "_q" + ESC + "\\",
    "dcs8": "\x90q\x9c",
    "nf": ESC + "(B",
    "fp": ESC + "7",
    "fe": ESC + "M",
    "fs": ESC + "c",
    "lone_esc": ESC,
}
IGNORABLES = {
    "zwsp": chr(0x200B),
    "zwj": chr(0x200D),
    "zwnj": chr(0x200C),
    "fe0f": chr(0xFE0F),
    "cgj": chr(0x034F),
    "hangul_fill": chr(0x115F),
    "jungseong_fill": chr(0x1160),
    "hangul_filler": chr(0x3164),
    "halfwidth_filler": chr(0xFFA0),
    "soft_hyphen": chr(0x00AD),
    "tag_a": chr(0xE0041),
    "vs_supp": chr(0xE0100),
}
VISIBLE_SEPARATORS = {"tab": "\t", "space": " ", "lf": "\n"}


class _Lcg:
    """A small seeded generator, the same on every Python version (the standard one is not promised to be)."""

    def __init__(self, seed: int) -> None:
        self.state = seed

    def choice(self, seq):
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        return seq[(self.state >> 33) % len(seq)]


def items() -> list[tuple[str, str]]:
    """(id, text) of every item, in a fixed order."""
    out = [(f"r{ord(c):02x}", c) for c in REMOVED_SINGLES]
    out += [(f"s{ord(c):04x}", c) for c in SPACE_LIKE_ITEMS]
    out += [(f"q_{k}", v) for k, v in SEQUENCES.items()]
    out += [(f"i_{k}", v) for k, v in IGNORABLES.items()]
    out += [(f"v_{k}", v) for k, v in VISIBLE_SEPARATORS.items()]
    return out


# ---- the kinds ----------------------------------------------------------------------------------------------------

# kind -> (prefix, value, suffix); the value is what must not stand in the output
KINDS = {
    "key": ("id ", KEY, " end"),
    "jwt": ("token ", JWT, " end"),
    "uuid": ("request_id ", UUID, " end"),
    "password": ("password=", PW, " end"),
    "bearer": ("Authorization: Bearer ", TOK, " end"),
    "mail": ("to ", MAIL, " end"),
    "flag": ("mysql -u root -p ", PW, " now"),
    "pem": (
        "-----" + "BEGIN PRIVATE" + " KEY-----\n",
        PEM_BODY,
        "\n-----" + "END PRIVATE" + " KEY-----",
    ),
    "handed": ("auth failed for ", HAND, " ; done"),
}
EVERY_OFFSET_KINDS = ("key", "mail", "password")
POSITIONS = ("name", "sep", "start", "inside", "end", "lineend", "before_ph")


@dataclass
class Case:
    id: str
    text: str
    kind: str
    value: str
    paths: tuple[str, ...]
    decoded: str  # the text as it reads once a spelled item is decoded (the same as `text` for a raw item)
    axis: str = "single"
    extra: dict = field(default_factory=dict)

    @property
    def handed(self) -> list[str]:
        return [HAND] if self.kind == "handed" else []


def _paths(kind: str) -> tuple[str, ...]:
    return HANDED_PATHS if kind == "handed" else PROMISED_PATHS


def _offset(kind: str, pos: str) -> int:
    prefix, value, _ = KINDS[kind]
    word = prefix.rstrip(" =:\n-") or prefix
    return {
        "name": max(len(word) - 3, 1),
        "sep": len(prefix) - 1,
        "start": len(prefix),
        "inside": len(prefix) + len(value) // 2,
        "end": len(prefix) + len(value),
        "lineend": len("".join(KINDS[kind])),
        "before_ph": len("".join(KINDS[kind])),
    }[pos]


def _build(
    kind: str,
    offset: int | None,
    pos: str,
    run: str,
    spelled: str | None = None,
    decoded_run: str | None = None,
) -> tuple[str, str]:
    base = "".join(KINDS[kind])
    if pos == "before_ph":
        base = base + " " + PLACEHOLDER_LITERAL
        off = len("".join(KINDS[kind])) + 1
    else:
        off = offset if offset is not None else _offset(kind, pos)
    ins = spelled if spelled is not None else run
    dec = decoded_run if decoded_run is not None else run
    return base[:off] + ins + base[off:], base[:off] + dec + base[off:]


def cases() -> list[Case]:
    out: list[Case] = []
    its = items()
    # singles: every offset inside the value for three kinds, the seven positions for the others
    for kind, (prefix, value, _s) in KINDS.items():
        for item_id, item in its:
            if kind in EVERY_OFFSET_KINDS:
                for k in range(1, len(value)):
                    off = len(prefix) + k
                    text, dec = _build(kind, off, "inside", item)
                    out.append(
                        Case(f"s|{kind}|{item_id}|o{k}", text, kind, value, _paths(kind), dec)
                    )
            for pos in POSITIONS:
                text, dec = _build(kind, None, pos, item)
                out.append(Case(f"s|{kind}|{item_id}|{pos}", text, kind, value, _paths(kind), dec))
    # run length axis: runs of 1 to 3 items of mixed families, with one space-like or one ignorable between them
    runs = {
        "bell2": [BEL, BEL],
        "bell3": [BEL, BEL, BEL],
        "csi2": [ESC + "[0m", ESC + "[1m"],
        "mix3": ["\x01", ESC + "[0m", ESC + "(B"],
        "mix_space": [BEL, "\x0c", BEL],
        "mix_ign": [BEL, chr(0xFE0F), ESC + "[0m"],
    }
    for kind in ("key", "mail", "password", "handed"):
        prefix, value, _s = KINDS[kind]
        for rid, parts in runs.items():
            for k in (1, len(value) // 2, len(value) - 1):
                text, dec = _build(kind, len(prefix) + k, "inside", "".join(parts))
                out.append(
                    Case(f"run|{kind}|{rid}|o{k}", text, kind, value, _paths(kind), dec, "run")
                )
    # encoding axis: the item written as percent, backslash text or an entity (removed singles only)
    spellings = {
        "pct": lambda c: urllib.parse.quote(c, safe=""),
        "bsx": lambda c: "\\x" + f"{ord(c):02x}",
        "bso": lambda c: "\\" + f"{ord(c):03o}",
        "bsu": lambda c: "\\u" + f"{ord(c):04x}",
        "ent": lambda c: "&#" + str(ord(c)) + ";",
    }
    decoders = {
        "pct": lambda c: c,
        "bsx": lambda c: c,
        "bso": lambda c: c,
        "bsu": lambda c: c,
        "ent": lambda c: html.unescape("&#" + str(ord(c)) + ";"),
    }
    for kind in ("key", "mail", "password", "handed"):
        prefix, value, _s = KINDS[kind]
        for c in REMOVED_SINGLES:
            for sid, spell in spellings.items():
                k = len(value) // 2
                text, dec = _build(kind, len(prefix) + k, "inside", c, spell(c), decoders[sid](c))
                out.append(
                    Case(
                        f"enc|{kind}|{sid}|{ord(c):02x}",
                        text,
                        kind,
                        value,
                        _paths(kind),
                        dec,
                        "enc",
                    )
                )
    # a hidden item inside the percent token of the first letter of the key (design M2): `%4` + item + `1KIA...`
    for item_id, item in its:
        text = "id %4" + item + "1" + KEY[1:]
        out.append(Case(f"m2|key|{item_id}", text, "key", KEY, PROMISED_PATHS, text, "m2"))
    # the NFKC axis: two letters of the key in full-width form plus one item
    wide = "".join(
        chr(ord(c) + 0xFEE0) if c in "AO" and i in (0, 5) else c for i, c in enumerate(KEY)
    )
    for item_id, item in its:
        for k in (3, 10):
            text = "id " + wide[:k] + item + wide[k:] + " end"
            out.append(
                Case(f"nfkc|key|{item_id}|o{k}", text, "key", KEY, PROMISED_PATHS, text, "nfkc")
            )
    # pairs: ALL unordered pairs of two different items, one input each, the kind and position drawn with the seeded generator (seed 77)
    rng = _Lcg(77)
    drawn = [k for k in KINDS if k != "handed"]
    for a in range(len(its)):
        for b in range(a + 1, len(its)):
            kind = rng.choice(drawn)
            pos = rng.choice(POSITIONS)
            run = its[a][1] + its[b][1]
            text, dec = _build(kind, None, pos, run)
            out.append(
                Case(
                    f"pair|{kind}|{its[a][0]}+{its[b][0]}|{pos}",
                    text,
                    kind,
                    KINDS[kind][1],
                    PATHS_FOR[kind],
                    dec,
                    "pair",
                )
            )
    # size seam: an item at character 262,143 (the last one inside the cap) and one at the `prepare_output` cut
    for item_id, item in (("bel", BEL), ("csi7", ESC + "[0m")):
        pad = "pad " * ((CAP - 1) // 4)
        head = pad[: CAP - 1 - len("id " + KEY[:4])]
        text = head + "id " + KEY[:4] + item + KEY[4:] + " end"
        out.append(Case(f"seam_cap|key|{item_id}", text, "key", KEY, PROMISED_PATHS, text, "seam"))
        text2 = "z" * 3900 + " id " + KEY[:4] + item + KEY[4:] + " end"
        out.append(
            Case(f"seam_cut|key|{item_id}", text2, "key", KEY, PROMISED_PATHS, text2, "seam")
        )
    return out


PATHS_FOR = {k: _paths(k) for k in KINDS}

# ---- running a case on whichever package is loaded --------------------------------------------------------------


def run_path(path: str, case: Case) -> str:
    from hadavin_sdk import tools
    from hadavin_sdk.approvals import channel

    redact_mod = importlib.import_module("hadavin_sdk.guard.redact")
    from hadavin_sdk.guard import runmap

    text = case.text
    if path == "untrusted":
        return runmap.redact_untrusted(text, {})
    if path == "tool":
        return tools.prepare_output(text, {}, 4000, case.handed)
    if path == "error":
        return tools.error_reason(ValueError(text), case.handed)
    if path == "head":
        return runmap.safe_head(text, 4000)
    if path == "card":
        return channel.clean(text)
    if path == "value":
        return runmap.redact_value({"k": text}, {})["k"]
    if path == "direct":
        return redact_mod.redact(text).text
    raise ValueError(path)


def evaluate(path: str, case: Case) -> str | None:
    """The output, or None when the path refuses the text (a refusal shows nothing)."""
    try:
        return run_path(path, case)
    except Exception as exc:
        # by class AND its parents (`RedactionLimit`, batch 7, is an `InputTooLarge`)
        if {c.__name__ for c in type(exc).__mro__} & {"RedactionError", "InputTooLarge", "TooDeep"}:
            return None
        raise


def masked(out: str | None, value: str, size: int = 5) -> bool:
    """No piece of `size` or more characters of the value stands in the output (None, a refusal, shows nothing)."""
    if out is None:
        return True
    return not any(value[i : i + size] in out for i in range(len(value) - size + 1))


# ---- the clean corpus (T6) --------------------------------------------------------------------------------------

_BS = "\\"
CORPUS = {
    "kubectl_tab_table": "NAME\tREADY\tSTATUS\tRESTARTS\tAGE\nweb-1\t1/1\tRunning\t0\t3d\nweb-2\t0/1\tPending\t2\t5m\n",
    "six_cell_row": "a\tb\tc\td\te\tf\n1\t2\t3\t4\t5\t6\n",
    "log_lines": "2026-11-11T10:00:00Z INFO start\n2026-11-11T10:00:01Z WARN slow query 1200ms\n",
    "json": '{"name": "pod-1", "ready": true, "restarts": 0, "tags": ["a", "b"]}',
    "coloured_test_output": ESC
    + "[32m"
    + "PASSED"
    + ESC
    + "[0m tests/test_a.py::test_one\n"
    + ESC
    + "[31m"
    + "FAILED"
    + ESC
    + "[0m tests/test_a.py::test_two\n",
    "grep_match_inside_word": "the "
    + "fail"
    + ESC
    + "[01;31m"
    + ESC
    + "[K"
    + "ure"
    + ESC
    + "[m"
    + ESC
    + "[K"
    + " of the pod\n",
    "hindi": "नमस्ते दुनिया",
    "persian_zwnj": "می" + chr(0x200C) + "خواهم",
    "emoji_joiners": "family \U0001f468"
    + chr(0x200D)
    + "\U0001f469"
    + chr(0x200D)
    + "\U0001f467 and heart ❤"
    + chr(0xFE0F),
    "curl_continuation": "curl -X POST https://example.com/api "
    + _BS
    + "\n  -H 'Content-Type: application/json' "
    + _BS
    + "\n  -d '{}'\n",
    "dockerfile_run": "RUN apt-get update "
    + _BS
    + "\n    && apt-get install -y curl "
    + _BS
    + "\n    && rm -rf /var/lib/apt/lists/*\n",
    "makefile_rule": "build:\n\tgcc -o app main.c " + _BS + "\n\t\t-O2 -Wall\n",
    "windows_path_line_end": "copy C:" + _BS + "temp" + _BS + "\nnext line\n",
    "nroff_overstrike": "N\x08NA\x08AM\x08ME\x08E\n",
    "cp1252_c1": "price \x80 12 and quote \x93done\x94",
}


def corpus_count(text: str) -> int:
    from hadavin_sdk.guard import runmap

    out = runmap.redact_untrusted(text, {})
    return sum(1 for _ in runmap.PLACEHOLDER.finditer(out))


# ---- the recorder ---------------------------------------------------------------------------------------------------


def main() -> int:
    argv = sys.argv[1:]
    out_dir = Path(argv[argv.index("--out") + 1]) if "--out" in argv else Path("tests/fixtures")
    import hadavin_sdk

    print("hadavin_sdk loaded from", hadavin_sdk.__file__, flush=True)
    verdicts: dict[str, str] = {}
    for case in cases():
        bits = ""
        for path in PATHS_FOR[case.kind] + (("direct",) if case.kind != "handed" else ()):
            bits += "1" if masked(evaluate(path, case), case.value) else "0"
        verdicts[case.id] = bits
    corpus = {name: corpus_count(text) for name, text in CORPUS.items()}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prh_main_verdicts.json").write_text(
        json.dumps(verdicts, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    (out_dir / "prh_main_corpus.json").write_text(
        json.dumps(corpus, sort_keys=True, indent=1) + "\n", encoding="utf-8"
    )
    print(f"recorded {len(verdicts)} verdicts and {len(corpus)} corpus counts")
    return 0


if __name__ == "__main__":
    # the repository root comes AFTER the entries of PYTHONPATH, so main's source is loaded first
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    raise SystemExit(main())
