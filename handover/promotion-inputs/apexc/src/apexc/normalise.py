"""Normalisation: the only values the gate ever compares (R-APEXC-001). Pure, stdlib only, no floats."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, date, datetime

from apexc.textnorm import fold, squeeze  # noqa: F401  (the ONE fold: a temporary copy of the core module, see CORE_COPIES.md)

WHITESPACE_BREAKS = chr(10) + chr(13) + chr(9) + chr(11) + chr(12)
_NON_ALNUM = re.compile(r"[^A-Z0-9]")
_LEAD_ZEROS = re.compile(r"(?<![0-9])0+(?=[0-9])")


def minor(value: str | int) -> int:
    """Money is an integer string in minor units. Floats and decimals with a point are refused."""
    if isinstance(value, (bool, float)):
        raise TypeError("money must be an int or an integer string")
    if isinstance(value, str) and not re.fullmatch(r"-?[0-9]+", value):
        raise ValueError(f"not an integer minor-unit string: {value!r}")
    return int(value)


def round_half_even_div(numerator: int, denominator: int) -> int:
    """Integer division rounding half to even (non-negative inputs)."""
    q, r = divmod(numerator, denominator)
    twice = 2 * r
    if twice > denominator or (twice == denominator and q % 2 == 1):
        q += 1
    return q


def tax_minor(qty: int, unit_minor: int, rate_bp: int) -> int:
    """Line tax in minor units, rate in basis points, half-even (R-APEXC-007)."""
    return round_half_even_div(qty * unit_minor * rate_bp, 10_000)


def clean_text(raw: str) -> str:
    """NFKC, then drop control and format characters (zero-width space/joiner, bidi marks, soft hyphen)."""
    s = unicodedata.normalize("NFKC", raw)
    s = "".join(
        " " if (ch in WHITESPACE_BREAKS or ch.isspace()) else ch for ch in s
    )  # every Unicode space (NEL, U+001C-U+001F, ...) and line break is a word separator, never deleted (they must not join words and hide a pattern)
    return "".join(ch for ch in s if unicodedata.category(ch) not in ("Cc", "Cf"))


def norm_id(raw: str) -> str:
    """Tax ids, accounts, routing codes, bank names: NFKC, upper-case, letters and digits only."""
    return _NON_ALNUM.sub("", clean_text(raw).upper())


def norm_number(raw: str) -> str:
    """Invoice number key: norm_id plus stripped leading zeros of each digit run (INV-0482 == INV482). O/0 and I/1
    are NOT merged (that is what makes a typo a near-duplicate rather than an exact one)."""
    return _LEAD_ZEROS.sub("", norm_id(raw))


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def fmt_ts(d: datetime) -> str:
    return d.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


def norm_po_refs(refs: list[str]) -> list[str]:
    return sorted(norm_id(r) for r in refs)


_BANK_CLAIM = re.compile(r"(bank|account|iban|routing|remit\w*)\W.{0,60}(chang|updat|new)|new\s+(bank|account)", re.I | re.S)
_APPROVAL_CLAIM = re.compile(r"(cfo|ceo|director|manager|owner)\b.{0,40}(approv|authori[sz]|signed\s*off)", re.I | re.S)
_INSTRUCTION = re.compile(
    r"(ignore|disregard|skip|bypass|override)\b.{0,50}(check|approval|rule|instruction|duplicate)|system\s*:|assistant\s*,", re.I | re.S
)


def scan_text(*texts: str) -> list[str]:
    """Demo-side flags over attacker-controlled free text (memo, footer, email, line text, names). Text is NFKC-cleaned
    first so zero-width tricks do not hide a pattern. Flags only ADD scrutiny (R-APEXC-015); no flag ever lowers a
    tier, and the structural rules hold even if every pattern is missed."""
    blob = "\n".join(clean_text(t) for t in texts)
    out = []
    if _BANK_CLAIM.search(blob):
        out.append("bank_change_claim")
    if _APPROVAL_CLAIM.search(blob):
        out.append("approval_claim")
    if _INSTRUCTION.search(blob):
        out.append("instruction_in_data")
    return out
