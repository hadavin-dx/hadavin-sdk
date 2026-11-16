"""The record schema and the validators (spec 6.2). ``validate_record`` is called by the pipeline, ``decisions.may_approve`` and the exporter.

Entries of the returned list are top-level field names (schema order, no duplicates); an empty list means valid. Integers only: ``bool`` and
floats are rejected."""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable

from . import settings
from .codes import ConfigError
from .textfold import fold_text


def _max_lines_from_policy() -> int:
    """``max_lines_per_draft`` from ``config/policy.json`` (the single source): a real integer from 1 to 100, otherwise the module's own error."""
    v = settings.read_policy_value("max_lines_per_draft")
    if type(v) is not int or not 1 <= v <= 100:
        raise ConfigError("bad_config", "policy.json: max_lines_per_draft must be an integer from 1 to 100")
    return v


MAX_LINES = _max_lines_from_policy()
MAX_ADJUSTMENTS = 10
MAX_MINOR = 10**12
# character caps (errata 36a): they change content codes, so they must hold before any approval is stored
MAX_LEN = {"invoice_no": 64, "po_ref": 64, "supplier_name": 200, "invoice_date": 32}
MAX_DESCRIPTION = 200
MAX_LABEL = 64
MAX_BYTES_PER_CHAR = 4  # UTF-8 bytes of a capped string are bounded by 4 x the cap
REQUIRED = ("invoice_no", "supplier_name", "currency", "lines", "adjustments", "total_minor")
OPTIONAL = ("po_ref", "invoice_date")
LINE_KEYS = ("description", "qty", "unit_cost_minor", "amount_minor")
ADJ_KEYS = ("label", "amount_minor")

# the tool input schema of the ``record_invoice`` tool (the live backend sends it as is)
RECORD_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": list(REQUIRED),
    "properties": {
        "invoice_no": {"type": "string", "minLength": 1, "maxLength": MAX_LEN["invoice_no"]},
        "supplier_name": {"type": "string", "minLength": 1, "maxLength": MAX_LEN["supplier_name"]},
        "po_ref": {"type": ["string", "null"], "maxLength": MAX_LEN["po_ref"]},
        "currency": {"type": "string"},
        "invoice_date": {"type": ["string", "null"], "maxLength": MAX_LEN["invoice_date"]},
        "lines": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_LINES,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": list(LINE_KEYS),
                "properties": {
                    "description": {"type": "string", "maxLength": MAX_DESCRIPTION},
                    "qty": {"type": "integer"},
                    "unit_cost_minor": {"type": "integer"},
                    "amount_minor": {"type": "integer"},
                },
            },
        },
        "adjustments": {
            "type": "array",
            "maxItems": MAX_ADJUSTMENTS,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": list(ADJ_KEYS),
                "properties": {"label": {"type": "string", "maxLength": MAX_LABEL}, "amount_minor": {"type": "integer"}},
            },
        },
        "total_minor": {"type": "integer"},
    },
}


def _is_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


BAD_CATEGORIES = ("Cc", "Cs", "Cf", "Zl", "Zp")  # control, lone surrogate, format (zero-width, bidi, BOM), line and paragraph separators


def _clean_str(v: object) -> bool:
    """A string with none of the BAD_CATEGORIES characters (U+202E, zero-width characters and U+2028/9 included)."""
    return isinstance(v, str) and not any(unicodedata.category(c) in BAD_CATEGORIES for c in v)


def _within(v: str, cap: int) -> bool:
    """The cap on the characters FIRST (nothing else runs on an over-long string), then on the FOLDED text (compatibility forms expand: U+FDFA folds to
    18 characters) and on the UTF-8 bytes."""
    return len(v) <= cap and len(fold_text(v)) <= cap and len(v.encode("utf-8")) <= MAX_BYTES_PER_CHAR * cap


def _cap_ok(v: object, cap: int, required: bool = False) -> bool:
    if not isinstance(v, str) or len(v) > cap:  # length before any scan or fold
        return False
    if not _clean_str(v) or not _within(v, cap):
        return False
    return not required or (bool(v.strip()) and bool(fold_text(v, collapse_ws=True).strip()))


def _line_ok(line: object) -> bool:
    if not isinstance(line, dict) or set(line) != set(LINE_KEYS):
        return False
    return _cap_ok(line["description"], MAX_DESCRIPTION) and all(_is_int(line[k]) and 0 <= line[k] <= MAX_MINOR for k in LINE_KEYS[1:])


def _adj_ok(adj: object) -> bool:
    if not isinstance(adj, dict) or set(adj) != set(ADJ_KEYS):
        return False
    return _cap_ok(adj["label"], MAX_LABEL) and _is_int(adj["amount_minor"]) and abs(adj["amount_minor"]) <= MAX_MINOR


def validate_record(fields: object, currencies: Iterable[str] | None = None) -> list[str]:
    """Field names that fail; ``[]`` = valid. ``currencies`` defaults to ``service.currencies`` of ``config/service.json``."""
    if not isinstance(fields, dict):
        return ["record"]
    allowed = tuple(currencies) if currencies is not None else tuple(settings.read_config()["service"]["currencies"])
    bad: list[str] = []

    def need(name: str, ok: bool) -> None:
        if not ok and name not in bad:
            bad.append(name)

    for name in REQUIRED:
        need(name, name in fields)
    for name in (*REQUIRED, *OPTIONAL):
        if name not in fields:
            continue
        v = fields[name]
        if name in ("invoice_no", "supplier_name"):
            need(name, _cap_ok(v, MAX_LEN[name], required=True))
        elif name in ("po_ref", "invoice_date"):
            need(name, v is None or _cap_ok(v, MAX_LEN[name]))
        elif name == "currency":
            need(name, isinstance(v, str) and v in allowed)
        elif name == "lines":
            need(name, isinstance(v, list) and 1 <= len(v) <= MAX_LINES and all(_line_ok(x) for x in v))
        elif name == "adjustments":
            need(name, isinstance(v, list) and len(v) <= MAX_ADJUSTMENTS and all(_adj_ok(x) for x in v))
        elif name == "total_minor":
            need(name, _is_int(v) and 0 <= v <= MAX_MINOR)
    if any(name not in REQUIRED and name not in OPTIONAL for name in fields):
        need("unknown_field", False)  # never echo a model-supplied key name
    order = {n: i for i, n in enumerate((*REQUIRED, *OPTIONAL, "unknown_field"))}
    return sorted(bad, key=lambda n: order[n])
