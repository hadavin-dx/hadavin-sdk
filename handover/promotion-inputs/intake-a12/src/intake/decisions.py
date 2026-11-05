"""Approve and reject decisions (spec 6.5, 6.6, 7, 8, errata 32). ``approve_refusal`` is the ONE reject-only rule (``may_approve`` is its boolean), used
by ``decide`` and by the exporter; ``valid_reason`` is the one reason rule. A decision and its state change are one ``BEGIN IMMEDIATE`` transaction.
Every function takes the ``Settings`` first, so the reason limits and currencies come from the same configuration the service runs with.

The database triggers (``queue_schema``) refuse a forged approve row, but they only see stored text: the exporter's recompute of the content code and of
``approve_refusal`` (WP5) is the final check before a row is written to the CSV."""

from __future__ import annotations

import sqlite3
import unicodedata

from . import content_code as cc
from . import flags as flagtable
from . import settings, validators, workqueue
from .codes import Refused

Decision = workqueue.Decision
# Reasons are typed by a person: letters, digits, punctuation, symbols and ordinary spaces only (an allowlist of Unicode categories, so a new or
# unassigned code point is refused by default). Marks (combining characters, variation selectors) are refused after NFC composes the usual accents.
_ALLOWED = frozenset(
    {"Lu", "Ll", "Lt", "Lm", "Lo", "Nd", "Nl", "No", "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Sm", "Sc", "Sk", "So", "Zs"}
)
# blank-looking letters and symbols that the allowlist would otherwise accept
_BLANK_LOOKALIKES = frozenset(chr(c) for c in (0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0))  # chr(): a formatter inlines invisible characters
BLANK_LOOKALIKES = _BLANK_LOOKALIKES  # public alias, the same object: ui.py's escaping set imports this name, never the private one
DECISIONS = {"approve": "APPROVED", "reject": "REJECTED"}


def valid_reason(s: settings.Settings, text: object) -> bool:
    """At least ``reason_min_chars`` visible (non-whitespace) characters, at most ``reason_max_chars`` characters in all, and only allowed characters
    (no control, format, zero-width, mark or blank-looking character). Ten identical characters are valid (a person's choice)."""
    if not isinstance(text, str) or len(text) > s.review.reason_max_chars:
        return False
    nfc = unicodedata.normalize("NFC", text)
    if any(unicodedata.category(c) not in _ALLOWED or c in _BLANK_LOOKALIKES for c in nfc):
        return False
    return sum(1 for c in nfc if not c.isspace()) >= s.review.reason_min_chars


def approve_refusal(s: settings.Settings, item: workqueue.Item, reason: str | None) -> Refused | None:
    """Why this item cannot be approved with this reason, or None. Order: no usable record, then ``flags.approval_blocker`` (reject-only flag, or a flag that needs a valid reason)."""
    if item.fields is None or validators.validate_record(item.fields, s.service.currencies):
        return Refused("not_approvable", "the item has no valid record")
    try:
        blocker = flagtable.approval_blocker(item.flags, valid_reason(s, reason))  # the ONLY approval decision (errata 41e)
    except flagtable.UnknownFlag:
        return Refused("not_approvable", "unknown flag")
    if blocker == "reject_only":
        return Refused("reject_only", "an item with this flag can only be rejected")
    if blocker == "invalid_reason":
        return Refused("invalid_reason", "approving a flagged item needs a valid reason")
    return None


def may_approve(s: settings.Settings, item: workqueue.Item, reason: str | None) -> bool:
    return approve_refusal(s, item, reason) is None


def decide(
    s: settings.Settings,
    item_id: str,
    decision: str,
    approver: str,
    reason: str | None,
    content_code: str,
    version: int,
    conn: sqlite3.Connection | None = None,
) -> Decision:
    """Record one decision. Refused (``Refused(code, text)``): ``not_found``, ``bad_decision``, ``already_decided``, ``state_conflict`` (RECEIVED or a
    database guard), ``stale_content`` (content code or version differs from the stored item), ``invalid_reason``, ``reject_only``, ``not_approvable``.
    With ``conn`` the caller holds the transaction (the decision is undone if the caller rolls back); otherwise one is opened here."""
    if decision not in DECISIONS:
        raise Refused("bad_decision", "decision must be approve or reject")
    if not isinstance(approver, str) or not workqueue.ACTOR_RE.fullmatch(approver):
        raise Refused("bad_decision", "approver must be 1 to 64 characters of letters, digits and . _ @ -")
    if approver.casefold() in workqueue.RESERVED_ACTORS:
        raise Refused("bad_decision", "that name is reserved for the program itself")
    if reason == "":
        reason = None  # a blank form field is "no reason supplied"
    with workqueue.scope(s, conn) as c:
        item = workqueue.get_in(c, item_id)
        if item is None:
            raise Refused("not_found", "no such item")
        if item.state in ("APPROVED", "REJECTED", "EXPORTED"):
            raise Refused("already_decided", "this item already has a decision")
        if item.state == "RECEIVED":
            raise Refused("state_conflict", "the item has no result yet")
        if content_code != cc.content_code(item):
            raise Refused("stale_content", "the item changed since the form was shown")
        if decision == "reject":
            if not valid_reason(s, reason):
                raise Refused("invalid_reason", "a reject needs a valid reason")
        else:
            if reason is not None and not valid_reason(s, reason):
                raise Refused("invalid_reason", "the reason is not valid")
            refusal = approve_refusal(s, item, reason)
            if refusal is not None:
                raise refusal
        return workqueue.apply_decision(c, item, decision, DECISIONS[decision], approver, reason, content_code, version)
