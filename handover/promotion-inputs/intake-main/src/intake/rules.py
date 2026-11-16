"""Pre-gate rule interface (stage 1: pure helpers that are fully specified are implemented and property-tested; the rest are
signatures). Policy comes from config/policy.json via `load_policy`; nothing here hard-codes a threshold.

Code -> exception table (one place): config/exceptions.json. X10 is raised by R-INTAKE-003 (value not in the document), -012 (cross-check)
and -013 (confidence floor); the audit event carries the rule id that fired. The ordered list of short-circuits and the cascade table
are in gate_rules.md section 2a.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

from .tools import ExceptionFlag, ExtractedOrder, Money, Tier, normalise_po

CONFIG = Path(__file__).resolve().parents[2] / "config"


@dataclass(frozen=True, slots=True)
class Policy:
    """Loaded policy. What is guaranteed: no attribute can be re-assigned (`frozen`), there is no instance `__dict__` to write into (`slots`),
    and the three table fields are read-only mappings (`load_policy` wraps them), so `policy.four_eyes_minor["USD"] = 1` raises TypeError.
    What is NOT guaranteed: Python cannot stop code running in the same process from calling `object.__setattr__(policy, ...)`; that is not
    a defence against a hostile caller, it only stops accidental mutation. The real control is that the file is read once at start-up and
    the live copy is compared with config/policy.json by the tests."""

    four_eyes_minor: Mapping[str, int]
    duplicate_window_days: int
    snapshot_max_age_minutes: int
    confidence_floor: float
    max_lines_per_draft: int
    max_drafts_per_sender_per_hour: int
    max_drafts_per_domain_per_hour: int
    max_unverified_notes_global_per_hour: int
    max_qty_base: int
    max_document_chars: int
    invoice_number_suffix_words: tuple[str, ...]
    po_pattern: str
    unit_synonyms: Mapping[str, str]
    legal_suffixes: tuple[str, ...]
    currency_symbols: Mapping[str, str]


def load_policy(path: Path = CONFIG / "policy.json") -> Policy:
    r = json.loads(path.read_text(encoding="utf-8"))
    return Policy(MappingProxyType(dict(r["four_eyes_minor"])), r["duplicate_window_days"], r["snapshot_max_age_minutes"], r["confidence_floor"], r["max_lines_per_draft"],
                  r["max_drafts_per_sender_per_hour"], r["max_drafts_per_domain_per_hour"], r["max_unverified_notes_global_per_hour"], r["max_qty_base"], r["max_document_chars"], tuple(r["invoice_number_suffix_words"]),
                  r["po_pattern"], MappingProxyType(dict(r["unit_synonyms"])), tuple(r["legal_suffixes"]), MappingProxyType(dict(r["currency_symbols"])))  # fmt: skip


def load_exceptions(path: Path = CONFIG / "exceptions.json") -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))


FOUR_EYES_CODES = frozenset({"X03", "X07", "X24"})  # stated price below the ERP price, credit hold, stale snapshot


def tier_for(codes: set[str], total: Money, policy: Policy) -> Tier:
    """R-INTAKE-016. Draft order tier: four_eyes if X03 / X07 / X24 is open or total >= the per-currency threshold; else human. A currency with
    no configured threshold is treated as four_eyes (conservative; such an order should already have stopped at X20). Never 'auto'.
    Exact boundary: total == threshold is four_eyes, threshold - 1 minor unit is human."""
    limit = policy.four_eyes_minor.get(total.currency)
    if codes & FOUR_EYES_CODES or limit is None or int(total.minor) >= limit:
        return "four_eyes"
    return "human"


def snapshot_stale(age_minutes: int, policy: Policy) -> bool:
    """R-INTAKE-021: stale only when strictly older than the limit (1440 minutes exactly is fresh, 1441 is stale). Integer minutes, no truncation."""
    return age_minutes > policy.snapshot_max_age_minutes


def in_duplicate_window(order_date: date, as_of: date, policy: Policy) -> bool:
    """R-INTAKE-008: day 30 is inside the window, day 31 is outside."""
    return (as_of - order_date).days <= policy.duplicate_window_days


def _po_key(po: str) -> str | None:
    try:
        return normalise_po(po)
    except ValueError:
        return None


def duplicate_po(customer_id: str, po: str, erp_orders: list, open_drafts: list, as_of: date, policy: Policy) -> bool:
    """R-INTAKE-008. `erp_orders`: objects with customer_id/po_number/date (ErpPort.list_recent_orders); `open_drafts`: OpenDraft rows
    (AgentDraftPort.list_open, OPEN versions only). The same customer, same normalised PO, inside the ERP window OR still open in
    Hadavin's own store. Revision wording is decided before this is called (X15 takes precedence)."""
    key = _po_key(po)
    if key is None:
        return False  # a PO outside the PO grammar cannot be compared; it already stops at X21 (po_valid) and is never a duplicate
    in_erp = any(
        o.customer_id == customer_id and _po_key(o.po_number) == key and in_duplicate_window(date.fromisoformat(o.date), as_of, policy)
        for o in erp_orders
    )
    in_drafts = any(d.customer_id == customer_id and d.po_norm == key for d in open_drafts)
    return in_erp or in_drafts


def is_revision(subject: str, lines_mentioning_po: list[str]) -> bool:
    """X15 wording check over the SUBJECT and over lines that mention a PO only (an item called 'Rev B bracket' or 'amended terms' does not count)."""
    text = subject + "\n" + "\n".join(lines_mentioning_po)
    return bool(
        re.search(
            r"\b(revised|amended|replaces)\b[^.!?;\n]{0,30}\b(po|purchase order|order)\b|\bpo\b[^.!?;\n]{0,20}\brev [a-z]\b", text, re.I
        )
    )


def po_valid(po: str | None, policy: Policy) -> bool:
    """R-INTAKE-017: a PO number is required, ASCII, and fullmatches po_pattern (no trailing-newline or formula-looking value)."""
    return bool(po) and po.isascii() and re.fullmatch(policy.po_pattern, po) is not None


def document_too_large(text: str, policy: Policy) -> bool:
    """R-INTAKE-016: a document above max_document_chars is handed back (X28) BEFORE any parsing or screening (a 5 MB token took 7 s in the screen)."""
    return len(text) > policy.max_document_chars


def norm_invoice_no(text: str, policy: Policy) -> str | None:
    """Invoice numbers: ASCII only; a trailing REV/R/DUP/COPY/CPY/RESEND word is dropped; letters and digits only; O folds to 0 and I to 1; leading zeros stripped."""
    if not text.isascii():
        return None
    s = text.upper().strip()
    s = re.sub(r"[-_ ](" + "|".join(policy.invoice_number_suffix_words) + r")[0-9]*$", "", s)
    s = re.sub(r"[^A-Z0-9]", "", s).replace("O", "0").replace("I", "1")
    return re.sub(r"(?<![0-9])0+(?=[0-9])", "", s)


def parse_iso_date(text: str | None) -> date | None:
    """R-INTAKE-011: only YYYY-MM-DD with ASCII digits and a real calendar day. '20261114', '2026-W46-1', '03/12/2026', '2026-02-30' -> None (X22)."""
    if not text or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def delivery_feasible(requested: date, as_of: date, lead_days: int, transit_days: int) -> bool:
    """Equal to the earliest date is feasible."""
    return requested >= as_of + timedelta(days=lead_days + transit_days)


def parse_price_text(text: str) -> tuple[str | None, int]:
    """R-INTAKE-004/019 price grammar: optional symbol or code, optional single space, digits with US grouping or plain, dot decimal, exactly
    two decimals. Returns (symbol-or-code as written, minor units). Raises ValueError for `4,94`, `1.092,40`, `1,09`, `USD $5`, `12`."""
    m = re.fullmatch(
        r"(?:(US\$|CA\$|AU\$|C\$|A\$|\$|"
        + chr(0xA3)
        + "|"
        + chr(0x20AC)
        + r"|[A-Za-z]{3}) ?)?([1-9][0-9]{0,2}(?:,[0-9]{3})+\.[0-9]{2}|(?:0|[1-9][0-9]*)\.[0-9]{2})",
        text,
    )  # raw text: no strip, no leading-zero group
    if not m:
        raise ValueError("ambiguous or invalid price")
    whole, frac = m.group(2).replace(",", "").split(".")
    return m.group(1), int(whole) * 100 + int(frac)


def currency_class(symbol: str | None, erp_currency: str, policy: Policy) -> tuple[str | None, bool]:
    """-> (explicit currency or None, informational flag). A bare dollar sign is the ERP currency; on a non-USD account it also raises X23.
    An explicit symbol or code is returned so the caller can compare it with the ERP currency (a mismatch is X20)."""
    if symbol is None:
        return None, False
    mapped = policy.currency_symbols.get(symbol.lower())
    if mapped == "BARE_DOLLAR":
        return None, erp_currency != "USD"
    return (mapped or symbol.upper()), False


def live_run_allowed(raw_policy: object, today: date | None = None) -> bool:
    """segregation/purpose-limit: refuse a live model run unless ALL hold: `allowed` is the boolean true; the provider no-training / no-retention setting is named
    and `training_use` is the boolean false; the region and the owner's quoted yes are non-empty text; `setting_checked_on` is a real ISO date
    (YYYY-MM-DD), not in the future and not older than `setting_max_age_days` (a non-negative int in the same block). Anything else, including a
    missing, null or wrongly typed `live_run` block, is False and never raises. Same semantics as the other demos' live-run gates (segregation)
    `today` defaults to the REAL clock. Pass the raw policy.json dict. Nothing is set today, so this is False."""
    lr = raw_policy.get("live_run") if isinstance(raw_policy, dict) else None
    if not isinstance(lr, dict) or lr.get("allowed") is not True or lr.get("training_use") is not False:
        return False
    if not all(isinstance(lr.get(k), str) and lr[k].strip() for k in ("provider_no_training_setting", "region", "owner_yes_quote")):
        return False
    max_age = lr.get("setting_max_age_days")
    checked_text = lr.get("setting_checked_on")
    if type(max_age) is not int or max_age < 0 or not isinstance(checked_text, str):
        return False
    checked = parse_iso_date(checked_text)
    if checked is None:
        return False
    return 0 <= ((today or datetime.now(UTC).date()) - checked).days <= max_age


def blocking(codes: set[str], exceptions: dict[str, dict]) -> set[str]:
    return {c for c in codes if exceptions[c]["blocking"]}


def confidence_ok(conf: float, policy: Policy) -> bool:
    """R-INTAKE-013: at the floor passes (>=), below goes to a person. SCRIPTED confidences: plumbing only."""
    return conf >= policy.confidence_floor


# --- signatures only (stage 2) ---------------------------------------------------------------------------------------------


def check_sku(erp, customer_id: str, sku_text: str) -> list[str]:
    """R-INTAKE-003: ASCII-only exact normalised customer alias, then global alias or code, UNION of both; 0 = X01, >1 = X14."""
    raise NotImplementedError("stage 2")


def convert_units(erp, customer_id: str, sku: str, qty_text: str, unit_text: str | None) -> tuple[int, int]:
    """R-INTAKE-004: returns (qty_base, unit_factor) or raises ValueError carrying X02 / X17."""
    raise NotImplementedError("stage 2")


def run_checks(order: ExtractedOrder, ctx: object) -> list[ExceptionFlag]:
    """Ordered short-circuits then the cascade (gate_rules.md section 2a): all findings are reported unless a short-circuit stops the run."""
    raise NotImplementedError("stage 2")
