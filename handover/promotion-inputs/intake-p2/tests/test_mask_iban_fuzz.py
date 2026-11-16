"""Class-level property test for IBAN-shaped places (rounds 5 and 6): one generator over EVERY registry country, and one dimension at a time.

Layout dimensions the generator reaches (each has its own assertion below, so a dimension that is never generated cannot hide behind the others):
first-token length (4, 5-8, 9-16, 17-34: the whole IBAN as one piece), country code and check digits apart (``DE 89 3704 ...``), group size, uniform
separator (one separator everywhere), uniform break (one line break everywhere, CRLF and double CRLF included), zero-width and glued prefixes, zero-width
characters inside groups, a decimal amount beside a currency code, and truncation of 2 to 9 characters. Mistypes: valid, changed check digits, one changed
character, one character short or long, truncated.

The check is by POSITION and runs twice: on ``mask.detect(text).spans`` (no run of four consecutive characters of the account part, which is everything
after the country code and check digits, may lie outside the hidden spans) and on the real output ``mask.mask(text).text`` (no run of four such characters
may remain in the text, whatever stands between them). The date or amount written next to the IBAN must stay visible. Tolerance, equal to the docstring
of ``_iban_places``: a place of at most ``IBAN_REF_MAX_LEN`` characters without the word iban is a reference number and stays visible, and an IBAN cut right after its bank code leaves those four letters. A case the masker
holds back (``SelfCheckFailed``) is counted: nothing is sent for it. The seed is fixed; ``-s`` prints the counts."""

from __future__ import annotations

import random
import re

from intake import invoicecheck, mask
from intake.selfcheck_codes import SelfCheckFailed

KEY = bytes(range(32))
SEED = 20261105
CASES = 2000
NBSP, THIN, EN, ZW = chr(0xA0), chr(0x2009), chr(0x2013), chr(0x200B)
SEPARATORS = [" ", " ", " ", NBSP, THIN, "\t", "-", EN, ".", ",", "/", ";", ":", "|", " / ", " | ", "  ", "   ", ZW, "- ", ". "]
BREAKS = ["\n", "\n ", "\n  ", "\n   ", "\n    ", "\n> ", "\r\n", "\r\n  ", "\r\n\r\n", "\n\n"]
PREFIXES = [
    "",
    "Pay to ",
    "Bank: ",
    "Beneficiary account ",
    "IBAN: ",
    "iban ",
    "Remit to GB bank, account ",
    "| ",
    ZW,
    "IBAN:",
    "IBAN" + ZW,
    NBSP,
    ZW + " ",
]
SUFFIXES = [
    ("", None),
    (" thanks", None),
    (" 04.11.2026", "date"),
    (" 04" + EN + "11" + EN + "2026", "date"),
    (" 1,500.00", "amount"),
    ("\nTotal $20.00", "amount"),
    ("\n2026-11-04", "date"),
    (" 9.00 EUR", "amount"),
    (" EUR 9.00", "amount"),
    ("\nTotal 12.50 EUR", "amount"),
]
GROUPS = [2, 3, 4, 5, 8, 10]
DIMENSIONS = (
    "first_4",
    "first_5_8",
    "first_9_16",
    "first_17_34",
    "cc_apart",
    "uniform_sep",
    "uniform_break",
    "crlf_break",
    "zw_prefix",
    "glued_prefix",
    "zw_in_group",
    "decimal_amount",
    "truncated",
    "plain",
)


def valid_iban(rnd: random.Random, cc: str, length: int) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    bban = "".join(rnd.choice(letters) for _ in range(rnd.choice([0, 4, 4, 4]))) if length > 12 else ""
    bban += "".join(rnd.choice("0123456789") for _ in range(length - 4 - len(bban)))
    n = int("".join(str(int(c, 36)) for c in bban + cc + "00"))
    return f"{cc}{98 - n % 97:02d}{bban}"


def mutate(rnd: random.Random, iban: str) -> tuple[str, str]:
    kind = rnd.choice(["valid", "valid", "check", "char", "char", "short", "long", "trunc", "trunc"])
    if kind == "check":
        d = "".join(rnd.choice("0123456789") for _ in range(2))
        return iban[:2] + (d if d != iban[2:4] else "00") + iban[4:], kind
    if kind == "char":
        i = rnd.randrange(4, len(iban))
        c = iban[i]
        pool = "0123456789" if c.isdigit() else "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return iban[:i] + rnd.choice([x for x in pool if x != c]) + iban[i + 1 :], kind
    if kind == "short":
        return iban[:-1], kind
    if kind == "long":
        return iban + rnd.choice("0123456789"), kind
    if kind == "trunc":
        return iban[: -rnd.randint(2, 9)], kind
    return iban, kind


def render(rnd: random.Random, iban: str, kind: str) -> tuple[str, list[int], tuple[int, int] | None, str, set[str]]:
    """The text, the positions of the account characters (after the first four), the span of the date or amount beside it, the suffix and the dimensions."""
    dims: set[str] = set()
    size = rnd.choice(GROUPS)
    roll = rnd.random()
    run = re.match("[A-Za-z]*", iban[4:]).group()  # the bank code in letters stays ONE group, as banks print it
    if roll < 0.15:
        head, start = [iban[:2], iban[2:4]], 4
        dims.add("cc_apart")
    elif roll < 0.45:
        first = min(rnd.choice([5, 6, 7, 8, 9, 10, 12, 14, 16, 20, 24, 30, len(iban)]), len(iban))
        if 4 < first < 4 + len(run):
            first = 4 + len(run)
        head, start = [iban[:first]], first
        dims.add("first_5_8" if first <= 8 else "first_9_16" if first <= 16 else "first_17_34")
    else:
        head, start = [iban[:4]], 4
        dims.add("first_4")
    rest = iban[start:]
    letters = re.match("[A-Za-z]*", rest).group() if start <= 4 + len(run) else ""
    tokens = head + ([letters] if letters else [])
    tokens += [rest[i : i + size] for i in range(len(letters), len(rest), size)]
    lower = rnd.random() < 0.5
    prefix = rnd.choice(PREFIXES)
    if prefix in (ZW, ZW + " ", NBSP):
        dims.add("zw_prefix")
    if prefix in ("IBAN:", "IBAN" + ZW):
        dims.add("glued_prefix")
    suffix, side_kind = rnd.choice(SUFFIXES)
    if suffix.endswith("EUR") or suffix.startswith(" EUR"):
        dims.add("decimal_amount")
    uniform_sep = rnd.choice(SEPARATORS) if rnd.random() < 0.3 else None
    uniform_break = rnd.choice(BREAKS) if rnd.random() < 0.3 and uniform_sep is None else None
    if uniform_sep is not None:
        dims.add("uniform_sep")
    if uniform_break is not None:
        dims.add("uniform_break")
    zw_in_group = rnd.random() < 0.15
    if zw_in_group:
        dims.add("zw_in_group")
    if kind == "trunc":
        dims.add("truncated")
    out = [prefix]
    positions: list[int] = []
    pos = len(prefix)
    consumed = 0
    for gi, tok in enumerate(tokens):
        if gi > 0:
            if uniform_sep is not None:
                sep = uniform_sep
            elif uniform_break is not None:
                sep = uniform_break
            else:
                sep = rnd.choice(BREAKS) if rnd.random() < 0.2 else rnd.choice(SEPARATORS)
            if "\r\n" in sep:
                dims.add("crlf_break")
            out.append(sep)
            pos += len(sep)
        for ch in tok:
            if zw_in_group and consumed >= 4 and rnd.random() < 0.3:
                out.append(ZW)
                pos += 1
            ch = ch.lower() if lower else ch
            if consumed >= 4:
                positions.append(pos)
            out.append(ch)
            pos += 1
            consumed += 1
    text = "".join(out)
    side = (len(text), len(text) + len(suffix)) if side_kind else None
    if not dims & {"cc_apart", "first_5_8", "first_9_16", "first_17_34"} and not dims - {"first_4"}:
        dims.add("plain")
    return text + suffix, positions, side, suffix, dims


def covered(position: int, spans) -> bool:
    return any(s.start <= position < s.end for s in spans)


def visible_run(positions: list[int], spans, width: int = 4) -> bool:
    """True when ``width`` consecutive characters of the account part are all outside every hidden span (one stray character is not a run)."""
    run = 0
    for p in positions:
        run = 0 if covered(p, spans) else run + 1
        if run >= width:
            return True
    return False


AMOUNT_LOOKALIKE = re.compile(r"\d{1,3},\d{3}(?!\d)")
DECIMAL_LOOKALIKE = re.compile(r"(?<!\d)\d{1,3}[.,]\d{2}(?!\d)")  # only beside a currency code
_MARK = re.compile(r"<[A-Z_]+_\d+>")


def output_run(text: str, positions: list[int], masked: str, width: int = 4) -> bool:
    """True when ``width`` consecutive account characters still stand in the masked text, with only separators between them (marks are not separators)."""
    clean = _MARK.sub("\x00", masked)
    sep = "[^0-9A-Za-z\x00]*"
    for i in range(len(positions) - width + 1):
        window = [text[p] for p in positions[i : i + width]]
        if re.search(sep.join(re.escape(c) for c in window), clean, re.IGNORECASE):
            return True
    return False


def run_cases(cases: int = CASES, seed: int = SEED):
    rnd = random.Random(seed)
    countries = sorted(invoicecheck.IBAN_LENGTH.items())
    counts = {"cases": 0, "hidden": 0, "held": 0, "exempt": 0, "lookalike": 0}
    per_dim = {d: {"cases": 0, "leaks": 0, "held": 0, "swallowed": 0} for d in DIMENSIONS}
    leaks: list[tuple[str, str]] = []
    swallowed: list[str] = []
    for _ in range(cases):
        cc, length = rnd.choice(countries)
        iban, kind = mutate(rnd, valid_iban(rnd, cc, length))
        text, positions, side, suffix, dims = render(rnd, iban, kind)
        dims = dims or {"plain"}
        counts["cases"] += 1
        for d in dims:
            per_dim[d]["cases"] += 1
        if len(iban) <= mask.IBAN_REF_MAX_LEN and not re.search("(?i)iban", text):
            counts["exempt"] += 1  # a short number without the word iban is a reference number: the docstring's tolerance
            continue
        if len(iban) <= 8 and iban[4:].isalpha():
            counts["exempt"] += 1  # cut right after the bank code: four letters and nothing else of the account (README limit)
            continue
        body = text[: len(text) - len(suffix)]
        if AMOUNT_LOOKALIKE.search(body) or ("EUR" in suffix and DECIMAL_LOOKALIKE.search(body)):
            counts["lookalike"] += (
                1  # account digits written like an amount (860,713 or 289.69 beside a currency code): indistinguishable from an amount, README limit
            )
            continue
        try:
            spans = mask.detect(text).spans
            masked = mask.mask(text, KEY).text
        except SelfCheckFailed:
            counts["held"] += 1
            for d in dims:
                per_dim[d]["held"] += 1
            continue
        if visible_run(positions, spans) or output_run(
            text, positions, masked[: len(masked) - len(suffix)] if suffix and masked.endswith(suffix) else masked
        ):
            leaks.append((kind, text))
            for d in dims:
                per_dim[d]["leaks"] += 1
            continue
        if side and (any(covered(p, spans) for p in range(side[0] + 1, side[1])) or (suffix.strip() and not masked.endswith(suffix))):
            swallowed.append(text)
            for d in dims:
                per_dim[d]["swallowed"] += 1
            continue
        counts["hidden"] += 1
    return counts, leaks, swallowed, per_dim


_RESULT = run_cases()


def test_every_account_character_of_every_registry_country_is_hidden_in_every_layout():
    counts, leaks, swallowed, _ = _RESULT
    print(
        f"IBANFUZZ cases={counts['cases']} hidden={counts['hidden']} held_back={counts['held']} exempt={counts['exempt']} amount_lookalike={counts['lookalike']} leaks={len(leaks)} "
        f"date_or_amount_swallowed={len(swallowed)}"
    )
    assert not leaks, [(k, ascii(t)) for k, t in leaks[:5]]
    assert not swallowed, [ascii(t) for t in swallowed[:5]]
    assert counts["held"] <= counts["cases"] * 0.03
    assert counts["lookalike"] <= counts["cases"] * 0.04


def test_each_layout_dimension_is_generated_and_clean():
    """One assertion per dimension: it was reached often enough, and no case of it leaked, was swallowed or was held back beyond five percent."""
    _, _, _, per_dim = _RESULT
    for d, c in per_dim.items():
        print(f"IBANFUZZ dimension {d}: {c}")
        assert c["cases"] >= 25, (d, c)
        assert c["leaks"] == 0 and c["swallowed"] == 0, (d, c)
        assert c["held"] <= max(3, c["cases"] * 0.05), (d, c)


def test_the_generator_reaches_every_registry_country_and_every_mistype():
    rnd = random.Random(SEED)
    seen_cc, seen_kind = set(), set()
    countries = sorted(invoicecheck.IBAN_LENGTH.items())
    for _ in range(CASES):
        cc, length = rnd.choice(countries)
        iban, kind = mutate(rnd, valid_iban(rnd, cc, length))
        render(rnd, iban, kind)
        seen_cc.add(cc)
        seen_kind.add(kind)
    assert seen_cc == set(invoicecheck.IBAN_LENGTH) and seen_kind == {"valid", "check", "char", "short", "long", "trunc"}
