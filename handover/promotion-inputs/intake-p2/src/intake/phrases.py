"""The plain sentences a stored trace row may carry as ``reason_plain`` (design WP2c B6).

A leaf module: it imports only ``flags`` and ``selfcheck_codes``. The table is built on each call (a repo test bans module-level caches), so a flag row that is not there yet cannot break
the import. No query words and no rule-number words appear in any sentence (a repo test scans them).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType

from . import flags, selfcheck_codes

_FIXED = {
    "bank_ok": "Not a verification. The bank details the tool recognised match the details on file for <supplier> (supplier chosen from a header "
    "line). Numbers written without a bank word near them are not checked.",
    "bank_changed": "Possible difference: a bank detail the tool recognised (<n> found, after the words <bank words>) is not among the details on "
    "file for <supplier> (supplier chosen from a header line). A person must compare them; this can also be a number that only looks like a bank "
    "detail.",
    "bank_none_found": "No bank details were recognised in this invoice; nothing was compared (supplier chosen from a header line: <supplier>).",
    "bank_no_details_on_file": "No bank details are on file for <supplier>; nothing was compared (supplier chosen from a header line).",
    "bank_not_run": "Bank check not run: supplier unknown (no single supplier name on file appears as a whole line near the top).",
    "approved": "approved by a person",
    "rejected": "rejected by a person",
    "exported": "written to the output file",
    "trace_refused": "A trace step was skipped because the invoice had already been decided by a person.",
    "manual_path": "This invoice was held back and can only be rejected here; it must be processed by hand outside this tool.",
}


def phrases() -> Mapping[str, str]:
    """Every allowed sentence by key: flag codes, self-check codes, then the fixed sentences. The three key groups must not share a key (a clash
    raises at once instead of silently replacing a sentence). The five bank sentences are TEMPLATES (``<supplier>``, ``<n>``, ``<bank words>``)
    and are stored as templates; see ``fill``."""
    groups = ({code: f.meaning for code, f in flags.FLAGS.items()}, dict(selfcheck_codes.PLAIN), dict(_FIXED))
    out: dict[str, str] = {}
    for g in groups:
        clash = out.keys() & g.keys()
        if clash:
            raise ValueError("phrase key clash")
        out.update(g)
    return MappingProxyType(out)


_FILL_RX = re.compile(r"<(supplier|n|bank words)>")
_FILL_NAMES = {"supplier": "supplier", "n": "n", "bank words": "bank_words"}


def fill(key: str, **values: object) -> str:
    """DISPLAY-TIME only: the template of ``key`` with ``<supplier>``, ``<n>`` and ``<bank words>`` replaced by the given values in ONE pass (a value
    that itself contains a placeholder is not rewritten). No escaping here: the page escapes when it renders. A tuple or list is joined with commas.
    The result is never stored in a trace row; the trace keeps the template."""
    if any(name not in _FILL_NAMES.values() for name in values):
        raise KeyError("unknown placeholder")

    def sub(m: re.Match[str]) -> str:
        v = values.get(_FILL_NAMES[m.group(1)])
        if v is None:
            raise KeyError("missing value")  # a placeholder must never reach the page
        return ", ".join(str(x) for x in v) if isinstance(v, tuple | list) else str(v)

    template = phrases()[key]
    if (
        key == "bank_changed" and values.get("bank_words", 0) is not None and "bank_words" in values and not values["bank_words"]
    ):  # no word to name: the sentence keeps its count only
        template = template.replace(", after the words <bank words>", "")
    return _FILL_RX.sub(sub, template)


def texts() -> frozenset[str]:
    """The set a ``TraceRow`` checks ``reason_plain`` against."""
    return frozenset(phrases().values())
