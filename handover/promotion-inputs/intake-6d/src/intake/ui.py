"""The ONLY place that builds HTML (portal plan B2.2). Pure functions: frozen view objects in, ``Html`` out. No database, no settings, no network.

The escaping choke point: ``Html`` marks safe markup and can be built only in this file. ``h()`` escapes every value that is not ``Html``, once, in one
pass; ``text()`` makes hidden characters visible and applies the HTML escape as the LAST step. Templates are string literals with quoted attributes
only; ``href`` and ``action`` values come only from ``url()`` (a ``Url``, route names from ``routes``, never from data).
Untrusted text (invoice text, extracted fields, file names, reasons, trace reasons) always goes through ``h()`` or ``text()``.
The theme follows the system setting by CSS only (no cookie, no route). Money is carried in integer minor or micro units and formatted here.
The approval rule is NOT here: the view builder sets ``may_approve``, ``approve_needs_reason`` and ``approve_refusal`` from the decision module.
"""

from __future__ import annotations

import base64
import hashlib
import html as _html
import re
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from dataclasses import InitVar, dataclass, field
from pathlib import Path
from types import MappingProxyType
from urllib.parse import parse_qsl

from . import routes

# ---------------------------------------------------------------------------------------------- the choke point
_KEY = object()


@dataclass(frozen=True, slots=True, repr=False)
class Html:
    """Safe markup. Not a ``str``: it cannot be added to, joined with or sliced like text, so markup and text never mix by accident (``str(x)`` gives
    the markup string). The constructor is private (only this file holds the key); ordinary code cannot subclass it, copy it into a new instance,
    pickle it or change it after it is built. This is a guard against mistakes and against hostile DATA, not against code that already runs in this
    process: such code can bypass it (``object.__setattr__``), and tests ban those calls outside this file."""

    _s: str
    _key: InitVar[object] = None

    def __post_init__(self, _key: object) -> None:
        if _key is not _KEY or type(self._s) is not str:
            raise TypeError("Html can be built only inside ui.py, from a str")

    def __init_subclass__(cls, **kw: object) -> None:
        raise TypeError("Html cannot be subclassed")

    def __str__(self) -> str:
        return self._s

    def __repr__(self) -> str:
        return f"Html(<{len(self._s)} characters>)"

    def __reduce__(self) -> tuple:
        raise TypeError("Html cannot be pickled")

    def __copy__(self) -> Html:
        return self

    def __deepcopy__(self, memo: dict) -> Html:
        return self


@dataclass(frozen=True, slots=True, repr=False)
class Url:
    """An ``href`` or ``action`` value. Minted only by ``url()``: a free string can never become a link."""

    _v: str
    _key: InitVar[object] = None

    def __post_init__(self, _key: object) -> None:
        if _key is not _KEY or type(self._v) is not str:
            raise TypeError("Url can be built only by url()")

    def __init_subclass__(cls, **kw: object) -> None:
        raise TypeError("Url cannot be subclassed")

    def __str__(self) -> str:
        return self._v

    def __repr__(self) -> str:
        return f"Url({self._v!r})"

    def __reduce__(self) -> tuple:
        raise TypeError("Url cannot be pickled")

    def __copy__(self) -> Url:
        return self

    def __deepcopy__(self, memo: dict) -> Url:
        return self


def _mk(s: str) -> Html:
    return Html(s, _KEY)


def _blank_lookalikes() -> frozenset[str]:
    """Blank-looking letters and symbols that a reason check refuses (the one seam: the decision module's public list replaces this body)."""
    return frozenset(chr(c) for c in (0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0))


_BLANKS = _blank_lookalikes()
# Unicode categories shown as a marker: control, format, surrogate, line and paragraph separators, private use, unassigned
_HIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp", "Zs", "Co", "Cn"})
# invisible combining marks (Khmer inherent vowels, Mongolian free variation selectors) that look like nothing
_INVISIBLE_MARKS = frozenset({0x17B4, 0x17B5, 0x180B, 0x180C, 0x180D, 0x180F})


def _is_hidden(ch: str) -> bool:
    """True for a character that must be shown as a visible marker. Newline and tab stay."""
    if ch in "\n\t" or ch == " ":
        return False
    o = ord(ch)
    return (
        unicodedata.category(ch) in _HIDDEN_CATEGORIES
        or 0xFE00 <= o <= 0xFE0F  # variation selectors
        or 0xE0100 <= o <= 0xE01EF  # variation selectors supplement
        or o == 0x034F  # combining grapheme joiner
        or o in _INVISIBLE_MARKS
        or ch in _BLANKS
    )


def _esc_piece(s: str) -> str:
    return _html.escape(s, quote=True)


# more than this many combining marks in a row are replaced by one count marker (they would paint over neighbouring lines)
_MAX_MARK_RUN = 3


def _shown(value: str, span: bool) -> str:
    """Escaped text in which every hidden character is replaced by its visible marker and a run of more than ``_MAX_MARK_RUN`` combining marks is
    cut to that many plus one count marker. The HTML escape is applied to each piece, markers are added after it, so a typed marker is escaped like
    any other text. ``span`` wraps a marker in a styled element (element text only: never inside an attribute)."""
    out: list[str] = []
    buf: list[str] = []
    run = 0
    extra = 0

    def put_marker(label: str) -> None:
        out.append(_esc_piece("".join(buf)))
        buf.clear()
        marker = _esc_piece(label)
        out.append(f'<span class="mark">{marker}</span>' if span else marker)

    for ch in value:
        if _is_hidden(ch):
            if extra:
                put_marker(f"<{extra} more combining marks>")
                extra = 0
            run = 0
            put_marker(f"<U+{ord(ch):04X}>")
        elif unicodedata.category(ch) in ("Mn", "Me"):
            run += 1
            if run > _MAX_MARK_RUN:
                extra += 1
            else:
                buf.append(ch)
        else:
            if extra:
                put_marker(f"<{extra} more combining marks>")
                extra = 0
            run = 0
            buf.append(ch)
    if extra:
        put_marker(f"<{extra} more combining marks>")
    out.append(_esc_piece("".join(buf)))
    return "".join(out)


def text(value: str | int) -> Html:
    """Untrusted text to safe markup (plain markers, safe in any context): the HTML escape comes last for every piece."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError("text() takes a str or an int")
    return _mk(_shown(str(value), False))


def _text_span(value: str) -> Html:
    return _mk(_shown(value, True))


def _esc(value: object) -> str:
    if isinstance(value, Html):
        return value._s
    if isinstance(value, Url):
        return _html.escape(value._v, quote=True)
    return text(value)._s  # type: ignore[arg-type]


_SLOT = re.compile(r"\{\{|\}\}|\{([a-z][a-z0-9_]*)\}")


def h(template: str, /, **values: object) -> Html:
    """Fill ``{name}`` slots of a literal template. Every non-``Html`` value is escaped exactly once; substituted values are never rescanned.
    ``{{`` and ``}}`` give literal braces. A missing or unused value, or a stray brace in the template, is an error."""
    if re.search(r"[{}]", _SLOT.sub("", template)):
        raise ValueError("stray brace in template")
    used: set[str] = set()

    def sub(m: re.Match[str]) -> str:
        name = m.group(1)
        if name is None:
            return "{" if m.group(0) == "{{" else "}"
        used.add(name)
        return _esc(values[name])

    out = _SLOT.sub(sub, template)
    if used != set(values):
        raise ValueError("unused template values: " + ", ".join(sorted(set(values) - used)))
    return _mk(out)


def join(parts: Iterable[object], sep: object = "") -> Html:
    return _mk(_esc(sep).join(_esc(p) for p in parts))


def _u(link: object) -> Url:
    """The gate for every href and action slot: only a ``Url`` from ``url()`` passes."""
    if not isinstance(link, Url):
        raise TypeError("a link must come from url()")
    return link


# ---------------------------------------------------------------------------------------------- routes and queries
SORTS = ("created", "state", "supplier", "total")
DIRS = ("asc", "desc")
STATE_ORDER = ("NEEDS_PERSON", "READY", "RECEIVED", "APPROVED", "REJECTED", "EXPORTED")
_QUERY_VALUES = MappingProxyType({"sort": SORTS, "dir": DIRS, "state": STATE_ORDER})  # the allowed KEYS are Route.query: one source


def url(name: str, *, id: str | None = None, **query: str) -> Url:
    """The only source of ``href`` and ``action`` values. Route names come from the route table; ``id`` must match the item id grammar; query keys
    are the route's own and the values are whitelisted."""
    r = routes.route(name)
    path = r.path
    if "{id}" in path:
        if not isinstance(id, str) or not re.fullmatch(routes.ITEM_ID_RE, id):
            raise ValueError("this route needs an item id")
        path = path.replace("{id}", id)
    elif id is not None:
        raise ValueError("this route takes no id")
    if not query:
        return Url(path, _KEY)
    if any(k not in r.query or v not in _QUERY_VALUES[k] for k, v in query.items()):
        raise ValueError("query not allowed on this route")
    return Url(path + "?" + "&".join(f"{k}={v}" for k, v in sorted(query.items())), _KEY)  # values are from closed sets: no encoding needed


@dataclass(frozen=True)
class ListQuery:
    sort: str | None = None  # None = the default order (NEEDS_PERSON, READY, then decided; each by created_at)
    dir: str = "desc"
    state: str | None = None


class QueryRefused(ValueError):  # noqa: N818 (plain name: it is a refusal of input, not a fault)
    """A bad query string. Carries nothing from the request: the page never echoes request text."""


def parse_list_query(raw: str) -> ListQuery:
    """Whitelisted keys and values only, each key at most once. Anything else raises ``QueryRefused`` (the page answers 422)."""
    try:
        pairs = parse_qsl(raw, keep_blank_values=True, max_num_fields=8)
    except ValueError:
        raise QueryRefused from None
    allowed = routes.route("home").query
    seen: dict[str, str] = {}
    for k, v in pairs:
        if k not in allowed or k in seen or v not in _QUERY_VALUES[k]:
            raise QueryRefused
        seen[k] = v
    return ListQuery(seen.get("sort"), seen.get("dir", "desc"), seen.get("state"))


# ---------------------------------------------------------------------------------------------- labels
TONES = ("info", "ok", "warn", "bad", "neutral")


def _tone(t: str) -> str:
    return t if t in TONES else "neutral"


STATE_LABELS = MappingProxyType(
    {
        "RECEIVED": ("Being read", "info"),
        "READY": ("Ready to approve", "info"),
        "NEEDS_PERSON": ("Needs a person", "warn"),
        "APPROVED": ("Approved", "ok"),
        "REJECTED": ("Rejected", "neutral"),
        "EXPORTED": ("Written to the spreadsheet file", "ok"),
    }
)

# code -> (plain sentence, person may only reject). Copy pinned by a test against flags.py.
FLAG_TEXT = MappingProxyType(
    {
        "D06": ("The total does not equal the lines plus adjustments.", False),
        "D10": ("Bank details in the invoice differ from the supplier on file.", True),
        "D12": (
            "A long number in the invoice is not explained by the supplier's details or the extracted values; a person must look.",
            False,
        ),
        "X10": ("Some values were not found in the invoice text.", True),
        "X18": ("The file could not be read as a text invoice.", True),
        "X28": ("The text is longer than 20,000 characters.", True),
        "L01": ("The supplier is not on file.", True),
        "L02": ("The AI model gave no usable reply.", True),
        # held-back flags (the masking step adds them to flags.py; neutral wording until its label table lands)
        "M01": ("The invoice was held back: a check found a value in a field where it did not belong.", True),
        "M02": ("The invoice was held back: its text contains something that looks like one of our masking marks.", True),
    }
)
FLAG_FALLBACK = ("A check raised a flag that this page has no sentence for. A person must look.", True)
KIND_WORDS = MappingProxyType(
    {
        "BANK": "bank number",
        "IBAN": "IBAN",
        "ROUTING": "routing number",
        "EMAIL": "email address",
        "PHONE": "phone number",
        "SECRET": "secret value",
    }
)
_PLACEHOLDER = re.compile(r"<([A-Z]{2,12})_([0-9]{1,3})>")
_LOOKALIKE = re.compile(r"<[A-Z]{2,12}_[0-9]{1,3}>")
_KIND = re.compile(r"[a-z][a-z_]{0,31}")
_HEX64 = re.compile(r"[0-9a-f]{64}")


# ---------------------------------------------------------------------------------------------- render data objects
@dataclass(frozen=True)
class SessionView:
    login_name: str = field(repr=False)
    role: str
    csrf: str = field(repr=False)


@dataclass(frozen=True)
class BannerView:
    kind: str  # a short machine name for tests and logs; validated, never rendered
    text: str
    tone: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str) or not _KIND.fullmatch(self.kind):
            raise ValueError("banner kind must be a short lower-case name")


@dataclass(frozen=True)
class FlagView:
    code: str
    sentence: str
    tone: str
    reject_only: bool


@dataclass(frozen=True)
class SensitiveValue:
    placeholder: str  # "<BANK_1>"
    kind: str
    restored: str | None = field(repr=False)


@dataclass(frozen=True)
class FieldView:
    name: str = field(repr=False)
    value: str | SensitiveValue = field(repr=False)
    grounded: bool


@dataclass(frozen=True)
class DecisionView:
    decision: str  # "approved" or "rejected"
    approver: str  # the login name that was recorded: not a proven person
    at_utc: str
    reason: str | None
    approved_although: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExportView:
    row_id: str  # 64 hex
    at_utc: str
    content_code_prefix: str

    def __post_init__(self) -> None:
        if not isinstance(self.row_id, str) or not _HEX64.fullmatch(self.row_id):
            raise ValueError("row id must be 64 hex characters")
        if not isinstance(self.content_code_prefix, str) or not re.fullmatch(r"[0-9a-f]{1,16}", self.content_code_prefix):
            raise ValueError("content code prefix must be 1 to 16 hex characters (never the whole code)")
        if not isinstance(self.at_utc, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]+)?)?(Z|\+00:00)?", self.at_utc
        ):
            raise ValueError("time must look like 2026-11-04 11:00, 2026-11-04T11:00:00Z or 2026-11-04T11:00:00+00:00 (UTC only)")


class ViewInconsistent(ValueError):  # noqa: N818 (plain name)
    """The view says "may approve" next to a refusal or a reject-only flag."""


@dataclass(frozen=True)
class InvoiceView:
    item_id: str
    state: str
    supplier: str | None
    invoice_no: str | None
    invoice_date: str | None
    total_minor: int | None  # None = the stored record has no valid total: shown as "not recorded"
    currency: str
    flags: tuple[FlagView, ...] = ()
    fields: tuple[FieldView, ...] = field(default=(), repr=False)
    source_text: str | None = field(default=None, repr=False)  # None for every non-approver session
    bank_on_file: SensitiveValue | None = field(default=None, repr=False)
    bank_in_text: tuple[SensitiveValue, ...] = field(default=(), repr=False)  # the D10 candidates found in the text
    d12_numbers: tuple[str, ...] = field(default=(), repr=False)  # the D12 unexplained numbers (approver only)
    content_code: str = ""
    version: int = 0
    created_at: str = ""  # sortable UTC text, set by the view builder
    order: int = 0  # tie-break for equal created_at, set by the view builder
    may_approve: bool = False  # from the decision module only
    approve_needs_reason: bool = False  # from the decision module only
    approve_refusal: str | None = None  # plain sentence shown when may_approve is False
    reason_max_chars: int = 200
    decision: DecisionView | None = None
    export: ExportView | None = None
    restore_available: bool = True
    refusal: str | None = None  # a plain sentence when the last decision attempt was refused
    banners: tuple[BannerView, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.item_id, str) or not re.fullmatch(routes.ITEM_ID_RE, self.item_id):
            raise ValueError("item id must match the item id grammar")
        # fail closed: the decision module owns the rule; a view that says "may approve" next to a refusal or a reject-only flag is a builder bug
        if self.may_approve and (self.approve_refusal is not None or any(_rejects(f) for f in self.flags)):
            raise ViewInconsistent("may_approve contradicts a refusal or a reject-only flag")
        if self.total_minor is not None and type(self.total_minor) is not int:
            raise TypeError("total_minor must be an int or None")


@dataclass(frozen=True)
class QueueView:
    rows: tuple[InvoiceView, ...]
    query: ListQuery
    refused_files: tuple[tuple[str, str], ...] = ()
    banners: tuple[BannerView, ...] = ()


@dataclass(frozen=True)
class OverviewView:
    counts_by_state: tuple[tuple[str, str, int], ...]  # (state, label, count)
    n_items: int
    spend_settled_micro: int | None  # None = the spend counter could not be read
    spend_cap_micro: int | None
    provider_limit_micro: int | None
    halted: bool | None  # None = unknown: shown as "Spending status unavailable", never as "not halted"
    prices_date: str | None
    banners: tuple[BannerView, ...] = ()


@dataclass(frozen=True)
class ExportRowView:
    item_id: str
    supplier: str | None
    invoice_no: str | None
    invoice_date: str | None
    total_minor: int
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.item_id, str) or not re.fullmatch(routes.ITEM_ID_RE, self.item_id):
            raise ValueError("item id must match the item id grammar")


@dataclass(frozen=True)
class ExportPageView:
    rows: tuple[ExportRowView, ...]
    kill_switch: bool | None = None  # None or True: no Write form and an engaged banner (fail closed); only False allows writing
    may_export: bool = False
    results: tuple[tuple[str, str], ...] = ()  # (item id, plain outcome text) after a run
    file_text: str | None = None  # plain text about the file after a run
    skipped: tuple[str, ...] = ()  # row ids skipped
    refusal: str | None = None
    banners: tuple[BannerView, ...] = ()
    preview_token: str | None = None  # 64 hex: what the approver previewed; the Write form sends it back as the hidden field ``preview``

    def __post_init__(self) -> None:
        if self.preview_token is not None and (not isinstance(self.preview_token, str) or not _HEX64.fullmatch(self.preview_token)):
            raise ValueError("preview token must be 64 hex characters")


def _rejects(f: FlagView) -> bool:
    """True if this flag allows rejecting only. An unknown code counts as reject-only (fail closed)."""
    return f.reject_only or FLAG_TEXT.get(f.code, FLAG_FALLBACK)[1]


def flag_view(code: str) -> FlagView:
    """The label-map entry for a flag code; an unknown code gets the neutral, reject-only fallback."""
    sentence, reject_only = FLAG_TEXT.get(code, FLAG_FALLBACK)
    return FlagView(code, sentence, "bad" if reject_only else "warn", reject_only)


def safe_invoice_view(**kw: object) -> InvoiceView:
    """``InvoiceView(**kw)`` for a list row: an inconsistent approve verdict degrades THIS row to "Approve not offered" instead of raising and
    turning the whole list into an error page. Any other fault (a bad id, a bad total) still raises."""
    try:
        return InvoiceView(**kw)  # type: ignore[arg-type]
    except ViewInconsistent:
        kw = {
            **kw,
            "may_approve": False,
            "approve_needs_reason": False,
            "approve_refusal": kw.get("approve_refusal")
            or "Approve is not offered: the data for this invoice does not agree with itself. Reject it or ask for a check.",
        }
        return InvoiceView(**kw)  # type: ignore[arg-type]


def default_order(rows: Iterable[InvoiceView]) -> tuple[InvoiceView, ...]:
    """NEEDS_PERSON first, then READY, then the decided ones, each group by created_at then order."""
    rank = {"NEEDS_PERSON": 0, "READY": 1}
    return tuple(sorted(rows, key=lambda r: (rank.get(r.state, 2), r.created_at, r.order)))


# ---------------------------------------------------------------------------------------------- money
# ponytail: only JPY and KRW are zero-decimal. Three-decimal currencies (BHD, KWD) would be shown wrongly; add them when a client needs one.
_ZERO_EXPONENT = frozenset({"JPY", "KRW"})


def money(minor: int, currency: str) -> Html:
    if type(minor) is not int:
        raise TypeError("money takes integer minor units")
    exp = 0 if currency in _ZERO_EXPONENT else 2
    whole, frac = divmod(abs(minor), 10**exp)
    s = f"{whole:,}" + (f".{frac:0{exp}d}" if exp else "")
    return h("{n} {c}", n=("-" if minor < 0 else "") + s, c=currency)


def _total(minor: int | None, currency: str) -> Html:
    return text("not recorded") if minor is None else money(minor, currency)


def placeholder(kind: str, n: int) -> str:
    """The masking mark text for a kind and a number, for example ``<BANK_2>``. Built here so no other module holds a less-than literal. A kind or
    number that does not fit the mark grammar raises ``ValueError`` (``sensitive`` would show such a mark as a plain "hidden value" chip)."""
    mark = f"<{kind}_{n}>"
    if type(n) is not int or not _PLACEHOLDER.fullmatch(mark):
        raise ValueError("kind must be 2 to 12 capital letters and n a number of 1 to 3 digits")
    return mark


def usd_micro(micro: int) -> Html:
    if type(micro) is not int:
        raise TypeError("spend takes integer micro units")
    if 0 < micro < 5_000:
        return _mk("less than US$ 0.01")
    cents = (abs(micro) + 5_000) // 10_000
    return h("{s}US$ {n}", s="-" if micro < 0 and cents else "", n=f"{cents // 100:,}.{cents % 100:02d}")


# ---------------------------------------------------------------------------------------------- sensitive values and untrusted text
def _chip_word(v: SensitiveValue) -> str:
    m = _PLACEHOLDER.fullmatch(v.placeholder) if isinstance(v.placeholder, str) else None
    if m is None or m.group(1) not in KIND_WORDS:
        return "hidden value"
    return f"{KIND_WORDS[m.group(1)]} {m.group(2)}"


def sensitive(value: SensitiveValue, role: str) -> Html:
    """The ONLY reader of ``SensitiveValue.restored``. The approver gets the restored value; every other role gets a chip; a missing original
    shows the chip too."""
    if role == routes.APPROVER and value.restored is not None:
        return h('<span class="val">{v}</span>', v=value.restored)
    tail = "hidden" if role != routes.APPROVER else "original not available"
    return h('<span class="chip">{w}, {t}</span>', w=_chip_word(value), t=tail)


def marked(value: str | None, *, compact: bool = False) -> Html:
    """Untrusted text where a placeholder lookalike is shown as ordinary text with a visible marker, never as a chip. Each piece is neutralised
    after the split; no part of the value is cut. A missing value is shown as "not recorded". ``compact`` (for clipped table cells, where a long
    note would be cut off) shows a "!" in front of the look-alike instead of the sentence."""
    if value is None:
        return text("not recorded")
    out: list[Html] = []
    pos = 0
    for m in _LOOKALIKE.finditer(value):
        out.append(_text_span(value[pos : m.start()]))
        if compact:
            out.append(h('<span class="forged">! {m}</span>', m=m.group(0)))
        else:
            out.append(
                h(
                    '<span class="forged">{m}</span><span class="forged-note"> looks like a placeholder; not from our masking</span>',
                    m=m.group(0),
                )
            )
        pos = m.end()
    out.append(_text_span(value[pos:]))
    return join(out)


def _value(v: str | SensitiveValue, role: str) -> Html:
    return sensitive(v, role) if isinstance(v, SensitiveValue) else marked(v)


# ---------------------------------------------------------------------------------------------- components
def status_pill(state: str) -> Html:
    label, tone = STATE_LABELS.get(state, ("Unknown state", "neutral"))
    return h('<span class="pill t-{t}">{l}</span>', t=_mk(_tone(tone)), l=label)


def tone_pill(label: str, tone: str) -> Html:
    return h('<span class="pill t-{t}">{l}</span>', t=_mk(_tone(tone)), l=label)


def banner(b: BannerView) -> Html:
    return h(
        '<div class="banner t-{t}" role="{r}"><span>{x}</span></div>',
        t=_mk(_tone(b.tone)),
        r=_mk("alert" if b.kind == KILL_SWITCH_SOURCE else "status"),  # an engaged kill switch is announced at once
        x=b.text,
    )


def flag_chip(f: FlagView) -> Html:
    rejects = _rejects(f)  # the same verdict as the view check: an unknown code or a hand-built tone cannot promise an Approve button
    may = "A person may only reject this invoice." if rejects else "A person may approve this invoice with a reason, or reject it."
    return h(
        '<div class="flag t-{t}"><span class="tag">{c}</span><span>{s}<span class="may">{m}</span></span></div>',
        t=_mk("bad" if rejects else "warn"),
        c=f.code,
        s=FLAG_TEXT.get(f.code, FLAG_FALLBACK)[0],  # the wording is ours: a caller's sentence is never shown
        m=may,
    )


@dataclass(frozen=True)
class Col:
    label: str
    numeric: bool = False
    sort: str | None = None  # sort key when the header is a link
    meta: bool = False  # hidden on narrow screens (the first cell then carries the state and flags)


def _cell_class(c: Col) -> Html:
    if c.numeric and c.meta:
        return _mk(' class="num meta"')
    if c.numeric:
        return _mk(' class="num"')
    return _mk(' class="meta"') if c.meta else _mk("")


def table(
    caption: str,
    cols: tuple[Col, ...],
    rows: Iterable[tuple[Html, ...]],
    *,
    header_links: Mapping[str, Url] | None = None,
    sorted_by: tuple[str | None, str] | None = None,
) -> Html:
    """A data table. Cells are ``Html`` built with ``h``; ``header_links`` maps a sort key to its ``url()`` result."""
    head = []
    for c in cols:
        label = (
            h('<a href="{u}">{l}</a>', u=_u(header_links[c.sort]), l=c.label)
            if c.sort and header_links and c.sort in header_links
            else text(c.label)
        )
        aria = _mk("")
        if c.sort and header_links and c.sort in header_links:  # a sortable column says which way it is sorted
            by, direction = sorted_by or (None, "desc")
            aria = (
                _mk(' aria-sort="none"')
                if by != c.sort
                else _mk(' aria-sort="ascending"')
                if direction == "asc"
                else _mk(' aria-sort="descending"')
            )
        head.append(h('<th scope="col"{n}{a}>{l}</th>', n=_cell_class(c), a=aria, l=label))
    body = []
    for r in rows:
        if len(r) != len(cols):
            raise ValueError("row width differs from the header")
        body.append(
            h(
                "<tr>{c}</tr>",
                c=join(h("<td{n}>{x}</td>", n=_cell_class(col), x=cell) for col, cell in zip(cols, r, strict=True)),
            )
        )
    return h(
        '<div class="table-wrap" role="region" tabindex="0" aria-label="{cap}">'
        "<table><caption>{cap}</caption><thead><tr>{hd}</tr></thead><tbody>{b}</tbody></table></div>",
        cap=caption,
        hd=join(head),
        b=join(body),
    )


def kv_card(title: str, pairs: Iterable[tuple[str, object]], why: str | None = None) -> Html:
    items = join(h("<dt>{k}</dt><dd>{v}</dd>", k=k, v=v) for k, v in pairs)
    sub = h('<p class="why">{w}</p>', w=why) if why else _mk("")
    return h('<section class="card"><h2>{t}</h2>{s}<dl class="kv">{i}</dl></section>', t=title, s=sub, i=items)


def disclosure(summary: str, body: Html) -> Html:
    """A native expander (no script)."""
    return h("<details><summary>{s}</summary>{b}</details>", s=summary, b=body)


def empty_state(heading: str, sentence: str, action: tuple[str, Url] | None = None) -> Html:
    """One heading, one sentence with real counts, at most one action ``(label, url() result)``."""
    act = h('<a class="btn" href="{u}">{l}</a>', u=_u(action[1]), l=action[0]) if action else _mk("")
    return h('<div class="empty"><h2>{h}</h2><p>{s}</p>{a}</div>', h=heading, s=sentence, a=act)


def _bar_width(part: int, whole: int, full: int) -> int:
    if whole <= 0 or part <= 0:
        return 0
    return min(full, max(2, part * full // whole))


def spend_meter(spent_micro: int, cap_micro: int | None, halted: bool | None) -> Html:
    if cap_micro is None or cap_micro <= 0:
        return h('<p class="why">No spending limit is recorded.</p>')
    w = _bar_width(spent_micro, cap_micro, 100)
    tone = "t-bad" if halted or spent_micro >= cap_micro else ""
    label = f"Spent {_esc(usd_micro(spent_micro))} of {_esc(usd_micro(cap_micro))} (our spend counter)"
    return h(
        '<div class="meter"><svg viewBox="0 0 100 10" preserveAspectRatio="none" role="img" aria-label="{l}"><title>{l}</title>'
        '<rect class="track" x="0" y="0" width="100" height="10"/><rect class="fill {t}" x="0" y="0" width="{w}" height="10"/></svg></div>',
        l=_mk(label),
        t=_mk(tone),
        w=w,
    )


def count_bar(label: str, count: int, total: int) -> Html:
    w = _bar_width(count, total, 360)
    return h(
        '<div><div class="why">{l}</div><svg viewBox="0 0 400 24" role="img" aria-label="{l}: {c} of {n}"><title>{l}: {c} of {n}</title>'
        '<rect class="track" x="0" y="8" width="360" height="8"/><rect class="fill" x="0" y="8" width="{w}" height="8"/>'
        '<text x="372" y="12" dominant-baseline="middle">{c}</text></svg></div>',
        l=label,
        c=count,
        n=total,
        w=w,
    )


# ---------------------------------------------------------------------------------------------- shell
_CSS = re.sub(r"/\*.*?\*/\s*", "", Path(__file__).with_name("ui_tokens.css").read_text(encoding="utf-8"), flags=re.DOTALL)
if "</style" in _CSS.lower() or "<" in _CSS:
    raise RuntimeError("ui_tokens.css must not contain markup")
STYLE_SHA256 = base64.b64encode(hashlib.sha256(_CSS.encode("utf-8")).digest()).decode(
    "ascii"
)  # of the exact text inside the one style element

PROFILES = ("strict",)  # "strict": no script, style by hash. The header string has one owner (the service), built from STYLE_SHA256.
_NAV = ("home", "overview", "export")
_NAV_LABELS = MappingProxyType({"home": "Invoice list", "overview": "Overview", "export": "Export"})
KILL_SWITCH_SOURCE = "kill_switch"  # the one banner-source name that always fails closed. Any banner of this kind means "engaged": a source
# of this name must never return a healthy or informational banner (it would close the Write form and be announced as an alert).
KILL_SWITCH_ENGAGED = BannerView(KILL_SWITCH_SOURCE, "Export is switched off", "bad")


@dataclass(frozen=True)
class Page:
    html: Html
    profile: str  # the script mode; the service turns it into the header
    status: int = 200


def collect_banners(
    sources: Mapping[str, Callable[[], BannerView | None]], fail_closed: Mapping[str, BannerView] | None = None
) -> tuple[BannerView, ...]:
    """Run each banner source on its own. A source that fails shows "Status unavailable" for that line only and the page still renders; the kill
    switch (always) and any name in ``fail_closed`` show an engaged banner instead, never "unavailable". The error text is never shown."""
    closed = {**(fail_closed or {}), KILL_SWITCH_SOURCE: KILL_SWITCH_ENGAGED}
    out: list[BannerView] = []
    for name, src in sources.items():
        try:
            b = src()
        except Exception:
            b = closed.get(name) or BannerView("unavailable", f"Status unavailable: {name}", "warn")
        if b is not None:
            out.append(b)
    return tuple(out)


def page(
    title: str,
    body: Html,
    *,
    session: SessionView | None = None,
    active: str | None = None,
    purpose: str = "",
    banners: Iterable[BannerView] = (),
    profile: str = "strict",
    status: int = 200,
) -> Page:
    """The shell. ``profile`` names a script mode of ``PROFILES``; only ``strict`` (no script, style by hash) exists today."""
    if profile not in PROFILES:
        raise ValueError("unknown page profile")
    stack = list(banners)
    banner_html = (
        h('<section class="banners" aria-label="Status messages">{b}</section>', b=join(banner(b) for b in stack)) if stack else _mk("")
    )
    sub = h('<p class="lede">{p}</p>', p=purpose) if purpose else _mk("")
    if session is None:
        inner = h('<div class="app bare"><main id="main" class="narrow"><h1>{t}</h1>{s}{b}</main></div>', t=title, s=sub, b=body)
    else:
        nav = join(
            h(
                '<a href="{u}"{c}>{l}</a>',
                u=_u(url(n)),
                c=_mk(' aria-current="page"') if n == active else _mk(""),
                l=_NAV_LABELS[n],
            )
            for n in _NAV
            if routes.allowed("GET", str(url(n)), session.role)  # a link only for a page this role may open
        )
        out_form = h(
            '<form method="post" action="{a}"><input type="hidden" name="csrf" value="{c}"><button type="submit">Sign out</button></form>',
            a=_u(url("logout")),
            c=session.csrf,
        )
        inner = h(
            '<div class="app"><aside class="rail"><div class="brand">Intake<small>by Hadavin</small></div><nav aria-label="Main">{nav}</nav></aside>'
            '<div class="main"><header class="top"><div><h1>{t}</h1>{s}</div><div class="who"><span>{n} ({r})</span>{o}</div></header>'
            '<main id="main" class="content">{b}</main></div></div>',
            nav=nav,
            t=title,
            s=sub,
            n=session.login_name,
            r=session.role,
            o=out_form,
            b=body,
        )
    doc = h(
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="color-scheme" content="light dark"><title>{t} - Intake</title><style>{css}</style></head>'
        '<body><a class="skip" href="#main">Skip to content</a>{bn}{i}</body></html>',
        t=title,
        css=_mk(_CSS),
        bn=banner_html,
        i=inner,
    )
    return Page(doc, profile, status)


# ---------------------------------------------------------------------------------------------- pages
def render_login(error: str | None = None, *, csrf: str, banners: Iterable[BannerView] = ()) -> Page:
    err = h('<p class="refusal" id="login-error" role="alert">{e}</p>', e=error) if error else _mk("")
    form = h(
        '<form method="post" action="{a}"><input type="hidden" name="csrf" value="{c}">'
        '<label>Name<input type="text" name="login" autocomplete="username" required></label>'
        '<label>Passphrase<input type="password" name="passphrase" autocomplete="off" required{d}></label>{e}'
        '<button class="primary" type="submit">Sign in</button></form>',
        a=_u(url("login_post")),
        c=csrf,
        d=_mk(' aria-describedby="login-error"') if error else _mk(""),
        e=err,
    )
    return page("Sign in", form, purpose="Sign in to review and approve invoices.", banners=banners, status=401 if error else 200)


def render_error(status: int, heading: str, sentence: str, session: SessionView | None = None, banners: Iterable[BannerView] = ()) -> Page:
    body = empty_state(heading, sentence, ("Back to the invoice list", url("home")) if session else None)
    return page(heading, body, session=session, banners=banners, status=status)


def render_query_refused(session: SessionView | None = None) -> Page:
    """A fixed sentence. Nothing from the request is shown (an attacker could otherwise put words on our page)."""
    body = empty_state(
        "This link is not valid",
        "The page does not accept this combination of sort and filter options.",
        ("Back to the invoice list", url("home")),
    )
    return page("Link not valid", body, session=session, status=422)


def apply_query(rows: Iterable[InvoiceView], q: ListQuery) -> tuple[InvoiceView, ...]:
    keys: dict[str, Callable[[InvoiceView], object]] = {
        "created": lambda r: (r.created_at, r.order),
        "state": lambda r: STATE_ORDER.index(r.state) if r.state in STATE_ORDER else len(STATE_ORDER),
        "supplier": lambda r: (r.supplier or "").casefold(),
        "total": lambda r: (r.total_minor is not None, r.total_minor or 0),  # a missing total sorts before every real one
    }
    sel = [r for r in rows if q.state is None or r.state == q.state]
    if q.sort is None:
        return default_order(sel)
    return tuple(sorted(sel, key=keys[q.sort], reverse=q.dir == "desc"))


def render_list(v: QueueView, session: SessionView) -> Page:
    q = v.query
    flt = join(
        h(
            '<a class="filter" href="{u}"{c}>{l}</a>',
            u=_u(url("home", **({"state": s} if s else {}))),
            c=_mk(' aria-current="true"') if (q.state or "") == s else _mk(""),
            l=label,
        )
        for s, label in (("", "All"), *((s, STATE_LABELS[s][0]) for s in STATE_ORDER))
    )
    if v.rows:
        links = {
            k: url("home", sort=k, dir="asc" if (q.sort == k and q.dir == "desc") else "desc", **({"state": q.state} if q.state else {}))
            for k in SORTS
        }
        cols = (
            Col("Supplier", sort="supplier"),
            Col("Invoice no."),
            Col("Date"),
            Col("Total", numeric=True, sort="total"),
            Col("State", sort="state", meta=True),
            Col("Flags", meta=True),
        )
        rows = [
            (
                h(
                    '<a class="row-link clip" href="{u}">{s}</a><span class="narrow-meta">{p} {f}</span>',
                    u=_u(url("item", id=r.item_id)),
                    s=marked(r.supplier, compact=True),
                    p=status_pill(r.state),
                    f=join((h('<span class="tag">{c}</span>', c=f.code) for f in r.flags), " "),
                ),
                h('<span class="clip">{x}</span>', x=marked(r.invoice_no, compact=True)),
                marked(r.invoice_date),
                _total(r.total_minor, r.currency),
                status_pill(r.state),
                join((h('<span class="tag">{c}</span>', c=f.code) for f in r.flags), " "),
            )
            for r in v.rows
        ]
        main = table(f"{len(v.rows)} invoice(s) shown", cols, rows, header_links=links, sorted_by=(q.sort, q.dir))
    else:
        main = empty_state(
            "No invoices to show",
            "0 invoices match this view. Run a scan to read the made-up invoice files, or choose another state above.",
        )
    refused = (
        disclosure(
            f"Files not processed ({len(v.refused_files)})",
            h("<ul>{i}</ul>", i=join(h('<li><span class="val">{f}</span>: {r}</li>', f=f, r=r) for f, r in v.refused_files)),
        )
        if v.refused_files
        else _mk("")
    )
    body = h('<div class="filters" role="group" aria-label="Filter by state">{f}</div>{m}{r}', f=flt, m=main, r=refused)
    return page(
        "Invoice list", body, session=session, active="home", purpose="Every invoice Intake has read, with its state.", banners=v.banners
    )


def _fields_table(v: InvoiceView, role: str) -> Html:
    if not v.fields:
        return h('<p class="why">Intake stored no extracted values for this invoice.</p>')
    rows = [
        (
            marked(f.name),
            _value(f.value, role),
            tone_pill("Found in the invoice text", "ok") if f.grounded else tone_pill("Not found in the invoice text", "warn"),
        )
        for f in v.fields
    ]
    return table("Values Intake extracted", (Col("Field"), Col("Value"), Col("Check")), rows)


def _reason_input(max_chars: int, required: bool, described: bool) -> Html:
    return h(
        '<input type="text" name="reason" maxlength="{m}" autocomplete="off"{r}{d}>',
        m=max_chars,
        r=_mk(" required") if required else _mk(""),
        d=_mk(' aria-describedby="refusal"') if described else _mk(""),
    )


def _decide_forms(v: InvoiceView, session: SessionView) -> Html:
    hidden = h(
        '<input type="hidden" name="csrf" value="{c}"><input type="hidden" name="version" value="{v}">'
        '<input type="hidden" name="content_code" value="{cc}">',
        c=session.csrf,
        v=v.version,
        cc=v.content_code,
    )
    action = url("decide", id=v.item_id)
    described = bool(v.refusal)
    err = h('<p class="refusal" id="refusal">{e}</p>', e=v.refusal) if v.refusal else _mk("")
    approve = (
        h(
            '<form method="post" action="{a}">{hid}<input type="hidden" name="decision" value="approve">'
            '<label>Reason for approving{req}{i}</label><button class="primary" type="submit">Approve</button></form>',
            a=_u(action),
            hid=hidden,
            req=_mk(" (required)") if v.approve_needs_reason else _mk(" (optional)"),
            i=_reason_input(v.reason_max_chars, v.approve_needs_reason, described),
        )
        if v.may_approve
        else _mk("")
    )
    reject = h(
        '<form method="post" action="{a}">{hid}<input type="hidden" name="decision" value="reject">'
        '<label>Reason for rejecting (required){i}</label><button class="danger" type="submit">Reject</button></form>',
        a=_u(action),
        hid=hidden,
        i=_reason_input(v.reason_max_chars, True, described),
    )
    note = h('<p class="why">{s}</p>', s=v.approve_refusal or "Approve is not offered for this invoice.") if not v.may_approve else _mk("")
    return h(
        '<section class="card"><h2>Your decision</h2>{n}{e}<div class="actions">{a}{r}</div></section>', n=note, e=err, a=approve, r=reject
    )


_TITLE_MAX = 60


def _title(invoice_no: str | None) -> str:
    """The page title: the invoice number cut to ``_TITLE_MAX`` characters plus an ellipsis (the whole value is in the Invoice card)."""
    if not invoice_no:
        return "Invoice"
    return f"Invoice {invoice_no[:_TITLE_MAX]}" + ("\u2026" if len(invoice_no) > _TITLE_MAX else "")


def render_item(v: InvoiceView, session: SessionView) -> Page:
    role = session.role
    approver = role == routes.APPROVER
    head = kv_card(
        "Invoice",
        [
            ("Supplier", marked(v.supplier)),
            ("Invoice no.", marked(v.invoice_no)),
            ("Date", marked(v.invoice_date)),
            ("Total", _total(v.total_minor, v.currency)),
            ("State", status_pill(v.state)),
        ],
    )
    flags = (
        h(
            '<section class="card"><h2>Flagged problems</h2><p class="why">Found by the automatic checks.</p>{f}</section>',
            f=join(flag_chip(f) for f in v.flags),
        )
        if v.flags
        else _mk("")
    )
    bank = (
        kv_card(
            "Bank details",
            why="Computed now from the current suppliers file." if any(f.code == "D10" for f in v.flags) else None,
            pairs=[
                ("On file for the supplier", sensitive(v.bank_on_file, role) if v.bank_on_file else text("not recorded")),
                (
                    "In the invoice text",
                    join((sensitive(b, role) for b in v.bank_in_text), " ") if v.bank_in_text else text("none found"),
                ),
            ],
        )
        if (v.bank_on_file or v.bank_in_text)
        else _mk("")
    )
    d12 = (
        kv_card(
            "Numbers not explained",
            [("Numbers", join((marked(n) for n in v.d12_numbers), " "))],
            why="Found in the invoice text, not explained by the supplier's details or the extracted values. Shown to the approver only.",
        )
        if approver and v.d12_numbers
        else _mk("")
    )
    missing = (
        h('<p class="why">Original values are not available for this invoice; decide from what is shown or reject.</p>')
        if approver and not v.restore_available
        else _mk("")
    )
    if approver and v.source_text is not None:
        src = h(
            '<section class="card"><h2>Invoice text</h2><pre class="source">{t}</pre></section>',
            t=marked(v.source_text),
        )
    else:
        src = h('<section class="card"><h2>Invoice text</h2><p>Invoice text is shown to the approver only.</p></section>')
    outcome = _mk("")
    if v.decision:
        d = v.decision
        pairs: list[tuple[str, object]] = [
            (
                "Decision",
                tone_pill("Approved" if d.decision == "approved" else "Rejected", "ok" if d.decision == "approved" else "neutral"),
            ),
            ("Recorded as", marked(d.approver)),
            ("At (UTC)", text(d.at_utc)),
        ]
        if d.approved_although:
            pairs.append(("Approved although", join(d.approved_although, " ")))
        if d.reason:
            pairs.append(("Reason", marked(d.reason)))
        outcome = kv_card("Decision recorded", pairs)
    receipt = (
        kv_card(
            "Written to the spreadsheet file",
            [("Row id", text(v.export.row_id)), ("At (UTC)", text(v.export.at_utc)), ("Content code", text(v.export.content_code_prefix))],
        )
        if v.export
        else _mk("")
    )
    forms = _decide_forms(v, session) if approver and v.decision is None and v.state in ("READY", "NEEDS_PERSON") else _mk("")
    body = join(
        [
            head,
            flags,
            bank,
            d12,
            h('<section class="card"><h2>Extracted values</h2>{m}{t}</section>', m=missing, t=_fields_table(v, role)),
            src,
            outcome,
            receipt,
            forms,
        ]
    )
    return page(
        _title(v.invoice_no),
        body,
        session=session,
        active="home",
        purpose="One invoice, its flagged problems and your decision.",
        banners=v.banners,
    )


def render_export(v: ExportPageView, session: SessionView) -> Page:
    if session.role != routes.APPROVER:  # the preview holds the guarded rows: approver only
        return render_error(403, "Not allowed", "This page is shown to the approver only.", session)
    parts: list[Html] = []
    banners = list(v.banners)
    # one verdict from both sources: unreadable (None), engaged (True) or an engaged banner already on the page all mean engaged
    engaged = v.kill_switch is not False or any(b.kind == KILL_SWITCH_SOURCE for b in v.banners)
    if engaged and not any(b.kind == KILL_SWITCH_SOURCE for b in banners):
        banners.insert(0, KILL_SWITCH_ENGAGED)
    if v.refusal:
        parts.append(h('<p class="refusal" role="alert">{r}</p>', r=v.refusal))
    if v.results or v.file_text:
        if v.results:
            parts.append(table("Result for each invoice", (Col("Invoice"), Col("Outcome")), [(marked(i), marked(o)) for i, o in v.results]))
        if v.file_text:
            parts.append(kv_card("The spreadsheet file", [("Status", text(v.file_text))]))
        if v.skipped:
            parts.append(kv_card("Skipped", [("Rows", join((text(s) for s in v.skipped), " "))], why="These rows were not written."))
    if v.rows:
        rows = [(marked(r.supplier), marked(r.invoice_no), marked(r.invoice_date), money(r.total_minor, r.currency)) for r in v.rows]
        parts.append(
            table(
                f"{len(v.rows)} approved invoice(s) ready to write",
                (Col("Supplier"), Col("Invoice no."), Col("Date"), Col("Total", numeric=True)),
                rows,
            )
        )
        if not engaged and v.may_export:
            parts.append(
                h(
                    '<form method="post" action="{a}"><input type="hidden" name="csrf" value="{c}">'
                    '{tok}<label>Your passphrase<input type="password" name="passphrase" autocomplete="off" required></label>'
                    '<button class="primary" type="submit">Write {n} invoice(s) to the spreadsheet file</button></form>',
                    a=_u(url("export_run")),
                    c=session.csrf,
                    tok=h('<input type="hidden" name="preview" value="{p}">', p=v.preview_token) if v.preview_token else _mk(""),
                    n=len(v.rows),
                )
            )
    elif not (v.results or v.file_text):
        parts.append(
            empty_state(
                "Nothing to export", "0 approved invoices are waiting. Approve an invoice first.", ("Go to the invoice list", url("home"))
            )
        )
    return page(
        "Export",
        join(parts),
        session=session,
        active="export",
        purpose="Write approved invoices into the spreadsheet file.",
        banners=banners,
    )


def render_overview(v: OverviewView, session: SessionView) -> Page:
    unknown = v.halted is None or v.spend_settled_micro is None
    if unknown:
        spend: list[Html] = [
            h("<p>{p}</p>", p=tone_pill("Spending status unavailable", "warn")),
            h('<p class="why">Run intake check to read the spend counter again.</p>'),
        ]
    else:
        spent = v.spend_settled_micro
        spend = [
            h('<div class="big">{s}</div>', s=usd_micro(spent)),
            h(
                "<p>{x}</p>",
                x=h("Spent {s} of {c} (our spend counter).", s=usd_micro(spent), c=usd_micro(v.spend_cap_micro))
                if v.spend_cap_micro is not None
                else _mk("Spent so far (our spend counter); no limit is recorded."),
            ),
            spend_meter(spent, v.spend_cap_micro, v.halted),
        ]
        if v.halted:
            spend.append(h("<p>{p}</p>", p=tone_pill("Spending halted", "bad")))
            spend.append(h('<p class="why">Our spend counter stopped new AI calls. Run intake check.</p>'))
    if v.provider_limit_micro is not None:
        spend.append(h('<p class="why">Limit at the provider: {l}.</p>', l=usd_micro(v.provider_limit_micro)))
    if v.prices_date:
        spend.append(h('<p class="why">Prices as of {d}.</p>', d=v.prices_date))
    spend_card = h(
        '<section class="card"><h2>Spend so far</h2><p class="why">Our own running total of AI model calls; the provider\'s bill is separate.</p>{s}</section>',
        s=join(spend),
    )
    if v.n_items > 0:
        bars = h(
            '<section class="card"><h2>Invoices by state</h2><p class="why">{n} invoice(s) in this run.</p><div class="bars">{b}</div></section>',
            n=v.n_items,
            b=join(count_bar(label, c, v.n_items) for _s, label, c in v.counts_by_state),
        )
    else:
        bars = h('<section class="card"><h2>Invoices by state</h2><p class="why">0 invoices in this run.</p></section>')
    return page(
        "Overview",
        h('<div class="grid">{a}{b}</div>', a=spend_card, b=bars),
        session=session,
        active="overview",
        purpose="Read-only: nothing on this page changes data.",
        banners=v.banners,
    )
