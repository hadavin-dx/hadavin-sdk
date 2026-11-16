"""Grounding (spec 6.3): every value the model returned must be found in ``send_text``. It stops values that are not in the text; it does NOT stop a
consistent fake summary block (the person and checks D06/D10 are the defence).

Limits, said in the README: the supplier name must appear as an ordered contiguous phrase on one line (words only, punctuation ``.,&-`` ignored), so
an invoice that names a different company with the same words in that order still grounds; a quantity is grounded by a whole number token
(``2`` or ``2.00``, not part of a grouped amount such as ``1,250.00`` or ``$ 3.00``) in the line's two-line window, so a neighbour line can supply it;
signs and adjustment labels are not grounded; US-style numbers only; a number followed by ``%`` or a letter, or glued to a letter on its left
(``20.00%``, ``12.50kg``, ``ABC12345.67``), is not money; a code glued to digits (``USD1250.00``) fails by design; ``US$3.00`` has no code and a
letter before ``$``, so it fails; a word-run glues ``Total-USD``; an invoice number with characters outside ASCII after NFKC folding is never grounded
(false-ungrounded: a person sees it).

Text and model values are prepared the same way: NFKC, runs of spaces and tabs collapsed (newlines are kept: the number windows use them), case
folded. Failing names are the top-level record fields, in schema order. Anything unexpected (a malformed record, an absurd number) counts as failing,
never as an exception."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_MONEY = re.compile(
    r"(?<![0-9.,])(?P<sym>[$£€])?\(?-?(?P<int>[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?P<dec>\.[0-9]{2})?\)?(?![0-9%]|,[0-9]|\.[0-9]|[^\W\d_])"
)
_QTY = re.compile(r"(?<![^\W_])(?<![._/,-])([0-9]{1,15}(?:\.00)?)(?![^\W_]|_|[/-]|[.,][0-9]|%)")
_CODE_BEFORE = re.compile(r"(?<![^\W\d_])(?:usd|gbp|eur|cad|aud)$")
_RUN = re.compile(r"[a-z0-9._/-]+")
_WORD = re.compile(r"\w+")
_SEP = re.compile(r"[.,&-]")
_LETTER_BEFORE = r"(?<![^\W\d_])"  # not directly preceded by a letter
_CURRENCY_SYMBOL = {  # code -> pattern on the prepared (case-folded) text, besides the code as a whole word-run
    "USD": _LETTER_BEFORE + r"\$",
    "GBP": "£",
    "EUR": "€",
    "CAD": _LETTER_BEFORE + r"ca\$",
    "AUD": _LETTER_BEFORE + r"a\$",
}
ORDER = ("invoice_no", "supplier_name", "po_ref", "currency", "invoice_date", "lines", "adjustments", "total_minor")
MAX_INT_DIGITS = 15  # a value above 10**12 can never pass validate_record; longer digit runs are not numbers here (and never reach int())


@dataclass(frozen=True)
class GroundResult:
    ok: bool
    failing_fields: tuple[str, ...]


def prep(s: str) -> str:
    """NFKC, collapse runs of spaces and tabs, case fold (newlines kept)."""
    return re.sub(r"[ \t]+", " ", unicodedata.normalize("NFKC", s)).casefold()


def find_money(text: str) -> list[str]:
    """Money tokens: only a token that carries a currency symbol or ends in ``.dd`` counts (a bare ``12`` or ``12.5`` is not money). A token is not
    money when a ``%`` or a letter follows it, or when it starts with a digit directly after a letter."""
    out = []
    for m in _MONEY.finditer(text):
        tok = m.group(0)
        if not (m.group("sym") or m.group("dec")):
            continue
        if tok[0].isdigit() and m.start() and text[m.start() - 1].isalpha():
            continue
        out.append(tok)
    return out


def parse_money(token: str) -> int | None:
    """Minor units of one token; the sign and parentheses are dropped (``(500.00)`` is 50000, ``$3`` is 300). None when it is not a number token or
    has more than 15 digits. Local on purpose: ``rules.parse_price_text`` fails on parentheses and bare integers."""
    m = _MONEY.fullmatch(token)
    if not m:
        return None
    digits = m.group("int").replace(",", "")
    if len(digits) > MAX_INT_DIGITS:
        return None
    return int(digits) * 100 + int((m.group("dec") or ".00")[1:])


def _money_values(text: str) -> set[int]:
    return {v for t in find_money(text) if (v := parse_money(t)) is not None}


def _runs(prepared: str) -> set[str]:
    """Word-runs: maximal runs of ``[a-z0-9._/-]`` with trailing ``.``, ``,`` and ``/`` removed."""
    return {r for w in _RUN.findall(prepared) if (r := w.rstrip("./,"))}


def _qty_tokens(window: str) -> set[str]:
    """Whole number tokens usable as a quantity: ``N`` or ``N.00`` that is not part of a grouped or symbol-prefixed amount, not glued to a letter,
    ``%``, ``/`` or ``-``, and not directly after a currency symbol (a space between the symbol and the number does not exempt it)."""
    out = set()
    for m in _QTY.finditer(window):
        prefix = window[: m.start()].rstrip(" \t")
        if prefix[-1:] and prefix[-1] in "$£€":
            continue
        if _CODE_BEFORE.search(prefix):  # "USD 3.00": the number belongs to the code, not to a quantity
            continue
        out.add(m.group(1))
    return out


def _words(prepared: str) -> list[str]:
    return _WORD.findall(_SEP.sub(" ", prepared))


def _supplier_ok(name: str, text: str) -> bool:
    ws = _words(prep(name).strip())
    if not ws:
        return False
    needle = " " + " ".join(ws) + " "
    return any(needle in " " + " ".join(_words(line)) + " " for line in text.split("\n"))


def _currency_ok(code: str, text: str, runs: set[str]) -> bool:
    if code.casefold() in runs:
        return True
    sym = _CURRENCY_SYMBOL.get(code)
    return bool(sym and re.search(sym, text))


def _date_ok(value: str, text: str) -> bool:
    d = prep(value).strip()
    return bool(d) and re.search(r"(?<![0-9a-z])" + re.escape(d) + r"(?![0-9a-z])", text) is not None


def _lines_ok(lines: list, text: str) -> bool:
    physical = text.split("\n")
    seen: dict[str, int] = {}
    for ln in lines:
        d = prep(ln["description"]).strip()
        if not d:
            return False
        k = seen[d] = seen.get(d, -1) + 1  # repeated descriptions match their occurrences in order
        pos = -len(d)
        for _ in range(k + 1):
            pos = text.find(d, pos + len(d))
            if pos < 0:
                return False
        i = text.count("\n", 0, pos)
        window = "\n".join(physical[i : i + 2])  # the physical line holding the match plus the next one
        money = _money_values(window)
        q = ln["qty"]
        toks = _qty_tokens(window)
        if str(q) not in toks and f"{q}.00" not in toks:
            return False
        if ln["unit_cost_minor"] not in money or ln["amount_minor"] not in money:
            return False
    return True


def ground(fields: dict, send_text: str) -> GroundResult:
    """``fields`` is a record that already passed ``validators.validate_record``; anything unexpected in it or in the text counts as failing."""
    try:
        text = prep(send_text)
        runs = _runs(text)
        money = _money_values(text)
    except Exception:
        return GroundResult(False, ORDER)

    def run_ok(v) -> bool:
        return isinstance(v, str) and prep(v).strip() in runs

    checks = {
        "invoice_no": lambda: run_ok(fields["invoice_no"]),
        "supplier_name": lambda: _supplier_ok(fields["supplier_name"], text),
        "po_ref": lambda: fields.get("po_ref") is None or run_ok(fields["po_ref"]),
        "currency": lambda: _currency_ok(fields["currency"], text, runs),
        "invoice_date": lambda: fields.get("invoice_date") is None
        or (isinstance(fields["invoice_date"], str) and _date_ok(fields["invoice_date"], text)),
        "lines": lambda: _lines_ok(fields["lines"], text),
        "adjustments": lambda: all(abs(a["amount_minor"]) in money for a in fields["adjustments"]),
        "total_minor": lambda: abs(fields["total_minor"]) in money,
    }
    failing = []
    for name in ORDER:
        try:
            ok = checks[name]()
        except Exception:
            ok = False
        if not ok:
            failing.append(name)
    return GroundResult(not failing, tuple(failing))
