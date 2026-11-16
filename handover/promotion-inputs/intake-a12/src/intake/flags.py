"""The one flag table the service uses (spec 6.5). It does not call ``rules.blocking``: that returns only truthy values, so null or false
codes would not block. An unknown code raises."""

from __future__ import annotations

from dataclasses import dataclass


class UnknownFlag(ValueError):  # noqa: N818 (name fixed by the spec)
    pass


@dataclass(frozen=True)
class Flag:
    meaning: str
    needs_person: bool
    reject_only: bool
    needs_reason: bool = False  # a person may approve only with a valid reason (D06, D12)


FLAGS = {
    "D06": Flag("total or a line does not add up", True, False, True),
    "D12": Flag("a number in the text is not accounted for (unexplained_number): a person must look", True, False, True),
    "D10": Flag("a bank detail in the text is not the supplier's on file", True, True),
    "X10": Flag("values not found in the text, or the record failed schema validation", True, True),
    "X18": Flag("unreadable, binary, wrong suffix, contains delimiter", True, True),
    "X28": Flag("text over 20000 characters", True, True),
    "L01": Flag("supplier not on file", True, True),
    "L02": Flag("no model reply (budget, gate, API refused, crash)", True, True),
    "L03": Flag("the AI answered in plain text instead of reading the invoice; a person must read it", True, True),
    "M01": Flag("a check on hiding sensitive values failed; the AI result is not used", True, True),
    "M02": Flag("a hiding mark that we did not issue was found; a person must check", True, True),
}


def _get(code: str) -> Flag:
    try:
        return FLAGS[code]
    except (KeyError, TypeError):
        raise UnknownFlag(str(code)[:40]) from None


def is_blocking(code: str) -> bool:
    """True when the flag sends the item to a person (every flag does)."""
    return _get(code).needs_person


def is_reject_only(code: str) -> bool:
    return _get(code).reject_only


def reject_only_codes() -> tuple[str, ...]:
    """Sorted; the database triggers are built from this."""
    return tuple(sorted(c for c, f in FLAGS.items() if f.reject_only))


def sorted_codes(codes) -> list[str]:
    """The ``flags`` column value: sorted, unique, every code known."""
    items = list(codes)
    for c in items:  # validate every element first: an unhashable or mixed-type element raises UnknownFlag, never TypeError
        _get(c)
    return sorted(set(items))


def approvable(codes) -> bool:
    """False when any code is reject-only. Flags that also need a valid reason (D06, D12) are NOT decided here: use ``approval_blocker``."""
    return not any(is_reject_only(c) for c in codes)


def reason_required(codes) -> bool:
    """True when any code is approvable only with a valid reason (D06, D12). ``decisions.may_approve`` (WP4) uses this with ``valid_reason``."""
    return any(_get(c).needs_reason for c in codes)


def approval_blocker(codes, reason_ok: bool) -> str | None:
    """THE single approval decision helper (``decisions.may_approve`` and the exporter use only this): ``"reject_only"`` when any code is reject-only,
    ``"invalid_reason"`` when a flag needs a valid reason (D06, D12) and ``reason_ok`` is false, else ``None`` (approval allowed)."""
    items = list(codes)
    if not approvable(items):
        return "reject_only"
    if reason_required(items) and not reason_ok:
        return "invalid_reason"
    return None
