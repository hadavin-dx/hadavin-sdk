"""CSV cell guard (spec 9). Every cell that reaches ``invoices.csv`` goes through ``guard_cell``; ``csvsink.regenerate`` calls it for every column of
every row, so nothing is written unguarded (the approver column included). Numeric columns are written as ``str(int)`` after a digits-only check
(a validated total is never negative). Text columns are the RAW value with TAB, CR and LF replaced by a space; an apostrophe is prefixed when the first
character of the RAW cell or of the FOLDED cell (``textfold.fold_text``: look-alikes, width forms, invisible characters) is a formula trigger.
The fold only decides the guard, it is never written. The guard is idempotent: a guarded cell starts with an apostrophe, which is no trigger."""

from __future__ import annotations

import re

from .textfold import fold_text

COLUMNS = (
    "row_id",
    "tenant_id",
    "invoice_no",
    "supplier_name",
    "po_ref",
    "currency",
    "invoice_date",
    "total_minor",
    "line_count",
    "flags",
    "source_sha256",
    "content_code",
    "approved_by",
    "approved_at",
)
MAX_CELL = 4096  # characters; a longer cell is refused (errata 36b), it is not truncated
NUMERIC = frozenset({"total_minor", "line_count"})
TRIGGERS = frozenset("=+-@ \t\r\n")  # first characters that make a spreadsheet read a cell as a formula (or hide one behind a space)
_DIGITS = re.compile(r"[0-9]+")
_BREAKS = str.maketrans({"\t": " ", "\r": " ", "\n": " "})


class BadCell(ValueError):  # noqa: N818 (a cell that cannot be written; never carries the cell value)
    pass


def guard_cell(column: str, value: object) -> str:
    """The text written for one cell. Raises ``BadCell`` for an unknown column, a non-numeric value in a numeric column, a non-string text value,
    a NUL character, a cell over ``MAX_CELL`` characters, or a value that cannot be encoded as UTF-8."""
    if column not in COLUMNS:
        raise BadCell("unknown column")
    if column in NUMERIC:
        s = str(value) if isinstance(value, int) and not isinstance(value, bool) else value
        if not isinstance(s, str) or not _DIGITS.fullmatch(s):
            raise BadCell(f"{column} must be digits only")
        return str(int(s))
    if value is None:
        return ""
    if not isinstance(value, str):
        raise BadCell(f"{column} must be text")
    if "\x00" in value:
        raise BadCell(f"{column} holds a NUL character")
    if len(value) > MAX_CELL:
        raise BadCell(f"{column} is longer than {MAX_CELL} characters")
    try:
        value.encode("utf-8")  # a lone surrogate cannot be written
    except UnicodeEncodeError:
        raise BadCell(f"{column} cannot be encoded as UTF-8") from None
    raw = value.translate(_BREAKS)
    folded = fold_text(raw)
    if raw[:1] in TRIGGERS or folded[:1] in TRIGGERS:
        return "'" + raw
    return raw


def guard_row(row: dict) -> dict[str, str]:
    """All 14 columns, guarded; any other key set is refused (so a column cannot be added or dropped unguarded)."""
    if set(row) != set(COLUMNS):
        raise BadCell("row must hold exactly the 14 columns")
    return {c: guard_cell(c, row[c]) for c in COLUMNS}
