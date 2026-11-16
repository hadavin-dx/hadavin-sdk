"""Stage-1 pure-function checks (R-INTAKE-003/004/018): the invoice structure, the bank-detail check, SKU resolution, unit conversion and the strict order-line parser.

Every function here is TOTAL: any text, any bytes-decoded-with-errors-replaced, any Unicode gives a result or a hand-back code, never an exception. The grammars are read from
`config/*.json`; `data/goldcheck.py` reads the same files but is a separate implementation, and `tests/test_differential.py` compares the two over the whole gold set plus fuzz.
The source-level mutation script (`tools/mutate_src.py`) mutates THIS file and the other `src/` modules."""

from __future__ import annotations

import base64
import binascii
import html
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

from . import strictjson

CONFIG = Path(__file__).resolve().parents[2] / "config"


def _j(name: str) -> dict:
    return strictjson.load_path(CONFIG / name)


POLICY, SCREEN_SPEC, BANK, INV = _j("policy.json"), _j("screen_spec.json"), _j("bank_spec.json"), _j("invoice_spec.json")
_ROW, _TOTAL, _ROWLIKE = re.compile(INV["row"]), re.compile(INV["total_line"]), re.compile(INV["row_shaped"])
_URL = re.compile(BANK["url_or_email"])
_EXEMPT = [re.compile(v) for v in BANK["exempt_lines"].values()]


# ---------------------------------------------------------------- document hygiene (M7)
def normalise_document(text: str) -> str:
    """Strip leading BOMs, make every line ending LF. Applied BEFORE anything else (and before the hash that spans index)."""
    return text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")


def _digits_ascii(t: str) -> str:
    return "".join(str(unicodedata.decimal(c)) if unicodedata.category(c) == "Nd" else c for c in t)


def fold(text: str) -> str:
    """NFKD, tag characters to ASCII, drop Cf/Mn/Me, EVERY Unicode decimal digit to ASCII, casefold, confusables, upper-case."""
    t = unicodedata.normalize("NFKD", html.unescape(text))
    t = "".join(chr(ord(c) - 0xE0000) if 0xE0020 <= ord(c) <= 0xE007E else c for c in t)
    t = "".join(c for c in t if unicodedata.category(c) not in ("Cf", "Mn", "Me"))
    t = _digits_ascii(t).casefold()
    for k, v in SCREEN_SPEC["confusables"].items():
        t = t.replace(k, v)
    return t.upper()


def decoded_extras(text: str) -> list[str]:
    """Base64 / base64url blobs and percent-encoded text, decoded, to be scanned like the document itself."""
    out = []
    for blob in re.findall(r"[A-Za-z0-9+/_-]{16,}={0,2}", text):
        try:
            pad = blob + "=" * (-len(blob) % 4)
            out.append(base64.urlsafe_b64decode(pad.replace("+", "-").replace("/", "_")).decode("utf-8"))
        except (binascii.Error, UnicodeDecodeError, ValueError):
            pass
    if "%" in text:
        out.append(unquote(text))
    return out


# ---------------------------------------------------------------- invoice structure (B2, M1, M9)
@dataclass
class ParsedInvoice:
    ok: bool
    reason: str = ""
    invoice_no: str = ""
    supplier_name: str = ""
    po_ref: str = ""
    currency: str = ""
    rows: list[tuple[str, int, int, int]] = field(default_factory=list)  # (sku, qty, cost_minor, amount_minor)
    total_minor: int | None = None
    total_symbol_ok: bool = True


def _minor(s: str) -> int:
    whole, frac = s.split(".")
    return int(whole) * 100 + int(frac)


def parse_invoice(text: str) -> ParsedInvoice:
    """Strict, total parser. ok=False means hand back as X27 with `reason`."""
    lines = normalise_document(text).split("\n")
    inv = sup = po = None
    for ln in lines:
        if inv is None and (m := re.fullmatch(INV["invoice_line"], ln)):
            inv = m.group(1).strip()
        elif sup is None and (m := re.fullmatch(INV["supplier_line"], ln)):
            sup = m.group(1)
        elif po is None and (m := re.fullmatch(INV["po_line"], ln)):
            po = (m.group(1), m.group(2))
    if not inv or not inv.isascii() or sup is None or po is None:
        return ParsedInvoice(False, "missing or invalid INVOICE / Supplier / Your PO line")
    res = ParsedInvoice(True, invoice_no=inv, supplier_name=sup, po_ref=po[0], currency=po[1])
    hdr = [i for i, ln in enumerate(lines) if ln == INV["table_header"]]
    tot = [i for i, ln in enumerate(lines) if ln.startswith("TOTAL ")]
    if len(hdr) != 1 or len(tot) != 1 or tot[0] < hdr[0]:
        return ParsedInvoice(False, "table header or TOTAL missing or repeated", inv, sup, po[0], po[1])
    for ln in lines[hdr[0] + 1 : tot[0]]:
        if not ln.strip():
            continue
        m = _ROW.fullmatch(ln)
        if not m:
            return ParsedInvoice(False, f"unparsed row: {ln[:40]!r}", inv, sup, po[0], po[1])
        res.rows.append((m.group(1), int(m.group(2)), _minor(m.group(3)), _minor(m.group(4))))
    for ln in lines[tot[0] + 1 :]:
        if ln.strip() and (_ROWLIKE.fullmatch(ln.strip()) or ln == INV["table_header"] or ln.startswith("TOTAL ")):
            return ParsedInvoice(False, f"row-shaped line after TOTAL: {ln[:40]!r}", inv, sup, po[0], po[1])
    if not res.rows:
        return ParsedInvoice(False, "zero parsed rows", inv, sup, po[0], po[1])
    tm = _TOTAL.fullmatch(lines[tot[0]])
    if tm:
        from .rules import parse_price_text

        try:
            res.total_minor = parse_price_text((tm.group(1) + " " + tm.group(2)).strip() if tm.group(2) else tm.group(1))[1]
        except ValueError:
            res.total_minor = None
    return res


# ---------------------------------------------------------------- bank detail (B1, M8)
def components(display: str) -> list[str]:
    n = re.sub(r"[ \-.]", "", fold(display))
    for f in BANK["formats"]:
        if mm := re.search(f["pattern"], n):
            return list(mm.groups())
    return [re.sub(r"[^0-9]", "", n)]


def _scan_text(text: str) -> str:
    """Remove what is NOT payment evidence: table rows, TOTAL, the INVOICE / Your PO / Supplier lines, ISO dates, strict VAT / ABN / phone lines, delimited money amounts on money lines."""
    keep = []
    for ln in text.split("\n"):
        s = ln.strip()
        if (
            _ROW.fullmatch(ln)
            or ln.startswith("TOTAL ")
            or re.fullmatch(INV["invoice_line"], ln)
            or re.fullmatch(INV["po_line"], ln)
            or re.fullmatch(INV["supplier_line"], ln)
        ):
            continue
        if any(e.fullmatch(s) for e in _EXEMPT):
            continue
        if re.search(BANK["money_line_marker"], s):
            s = re.sub(BANK["money_amount"], " ", s)
        keep.append(s)
    t = re.sub(BANK["iso_date"], " ", "\n".join(keep))
    return t


def bank_clean(on_file_display: str, text: str) -> bool:
    """POSITIVE EVIDENCE. True only if every on-file component appears and every account-shaped token, URL, email or wallet is accounted for."""
    n = fold(normalise_document(text))
    extras = [fold(x) for x in decoded_extras(normalise_document(text))]
    comps = components(on_file_display)
    flat = re.sub(r"[ \-./\t\n_]", "", n)
    if not all(c in flat for c in comps):
        return False
    for body in [n, *extras]:
        s = _scan_text(body)
        if _URL.search(s):
            return False
        toks = []
        for pat in (BANK["iban_spaced"], BANK["iban_contiguous"]):
            toks += [m.group(0).replace(" ", "") for m in re.finditer(pat, s)]
            s = re.sub(pat, " ", s)
        prev = None
        while prev != s:
            prev, s = s, re.sub(r"(?<=[0-9])[^A-Z0-9]+(?=[0-9])", "", s)
        toks += re.findall("[0-9]{" + str(BANK["min_long_digit_run"]) + ",}", s)
        if any(t not in comps for t in toks):
            return False
    return True


# ---------------------------------------------------------------- SKU and unit (R-INTAKE-003/004)
def sku_norm(text: str) -> str | None:
    """ASCII only; ONLY the separators space - / _ are dropped. Non-ASCII text never resolves."""
    return re.sub(r"[ \-/_]", "", text.upper()) if text.isascii() else None


def check_sku(erp, customer_id: str, sku_text: str) -> list[str]:
    """Union of customer alias and global alias/code. [] = X01, more than one = X14."""
    return [s.sku for s in erp.resolve_sku(customer_id, sku_text)]


class LineError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


_QTY = re.compile(r"[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+")


def convert_units(erp, customer_id: str, sku: str, qty_text: str, unit_text: str | None) -> tuple[int, int]:
    """(qty_base, unit_factor) or LineError('X17' | 'X02')."""
    if not _QTY.fullmatch(qty_text):
        raise LineError("X17")
    rec = erp.get_sku(sku)
    cust = erp.get_customer(customer_id)
    if rec is None or cust is None:
        raise LineError("X02")
    if unit_text is None:
        if len(rec.uoms) == 1:
            name, fac = rec.base_uom, 1
        elif cust.default_uom and cust.default_uom in rec.uoms:
            name, fac = cust.default_uom, rec.uoms[cust.default_uom]
        else:
            raise LineError("X02")
    else:
        name = POLICY["unit_synonyms"].get(unit_text.lower().strip("."))
        if name is None or name not in rec.uoms:
            raise LineError("X02")
        fac = rec.uoms[name]
    if "," in qty_text and (name == "kg" or rec.base_uom == "kg" and name == rec.base_uom):
        raise LineError("X17")
    q = int(qty_text.replace(",", "")) * fac
    if q > POLICY["max_qty_base"]:
        raise LineError("X17")
    return q, fac


_UNITS = set(POLICY["unit_synonyms"]) | set(POLICY["unit_words_not_in_table"])
_UNIT_RE = "|".join(sorted(_UNITS, key=len, reverse=True))
_ITEM_PATTERNS = [
    re.compile(rf"- (?P<qty>\S+)(?: (?P<unit>{_UNIT_RE}))? x (?P<ref>.+?)(?: @ (?P<price>.+))?", re.I),
    re.compile(rf"- (?P<ref>.+?): (?P<qty>\S+)(?: (?P<unit>{_UNIT_RE}))?(?: @ (?P<price>.+))?", re.I),
    re.compile(rf"(?P<qty>[0-9]\S*)(?: (?P<unit>{_UNIT_RE}))? (?P<ref>[A-Za-z0-9].*?)(?: @ (?P<price>.+))?", re.I),
]


def _itemlike(line: str) -> bool:
    """A line that LOOKS like a line item: optional sign or bullet, then a decimal digit of ANY script; or a bullet line containing such a digit."""
    s = line.lstrip()
    if not s:
        return False
    if unicodedata.category(s[0]) == "Nd":
        return True
    if s[0] in "-+" and len(s) > 1:
        rest = s[1:].lstrip()
        return bool(rest) and (
            unicodedata.category(rest[0]) == "Nd" or (s[0] == "-" and s[1] == " " and any(unicodedata.category(c) == "Nd" for c in rest))
        )
    return False


def parse_email_items(text: str) -> tuple[list[dict], list[str]]:
    """(items, unparsed item-like lines). The caller hands back X27 when the second list is not empty (R-INTAKE-004, M9)."""
    items, bad = [], []
    for ln in normalise_document(text).split("\n"):
        for p in _ITEM_PATTERNS:
            if m := p.fullmatch(ln):
                items.append({k: m.group(k) for k in ("ref", "qty", "unit", "price")})
                break
        else:
            if _itemlike(ln):
                bad.append(ln)
    return items, bad
