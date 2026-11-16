"""Approval channel Protocol and the fake channel. Channel text is template-built, redacted and link-free."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.approvals.gate import sanitise_text, withhold_commands
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import ApprovalDecision, ApprovalRequest

if TYPE_CHECKING:
    from hadavin_sdk.approvals.cards import Card, Delivery


def clean(text: str) -> str:
    """WARDEN's G3 cleaning (`gate.sanitise_text`): no link, image, HTML, mention, control character or forged
    markdown structure survives in text a person acts on; then G4 (`gate.withhold_commands`): no command a person could
    paste to change a system, on any platform; then ONE redaction, last."""
    # The neutralising hook (sanitise, then withhold commands) runs on the text AND on every decoded view the redactor
    # tries (`redact_text(..., neutralise=)`): a view that replaces the text (because it found a secret only the decoding
    # shows) is sanitised too, so `%72m -rf /`, `%3Cimg%3E`, `&lt;!channel&gt;` cannot come back as a command, an image
    # or a mention. Nothing transforms the text after its final redaction. Placeholders already in the text
    # (`<IPV4_1>`) survive sanitising (tested) and are seeded into the map so a new one never reuses their number.
    text = text.replace("\x00", "")
    mapping = _seeded(text)
    pre = _premask_dotted(text, mapping)
    out = runmap.redact_text(pre, mapping, neutralise=_neutralise)
    used = mapping
    joined = _TAGS.sub("", text)
    if joined != text:
        joined_map = _seeded(joined)
        jpre = _premask_dotted(joined, joined_map)
        alt = runmap.redact_text(jpre, joined_map, neutralise=_neutralise)
        if _assignment_originals(joined_map) - _assignment_originals(mapping):
            out, used = alt, joined_map
    _p1d_check(text, out, used)
    return out


_DOTTED_KINDS = {"EMAIL", "HOSTNAME"}


def _premask_dotted(text, mapping):
    """PROTO: values whose spelling the gate's defang (`.` -> `[.]`) would split are masked BEFORE the gate runs."""
    probe = _seeded(text)
    runmap.redact_text(text, probe)
    for ph, original in sorted(probe.items(), key=lambda kv: -len(kv[1])):
        m = runmap.PLACEHOLDER.fullmatch(ph)
        if original.startswith("\0seed") or not m or m.group(1) not in _DOTTED_KINDS:
            continue
        if original in text:
            mapping[ph] = original
            text = text.replace(original, ph)
    return text


class _P1dRefused(runmap.RedactionError):
    pass


def _p1d_views(t):
    import importlib
    from hadavin_sdk.approvals import gate
    from hadavin_sdk.guard import textnorm
    _rd = importlib.import_module("hadavin_sdk.guard.redact")
    v = {t, _TAGS.sub("", t)}
    v |= {runmap.undo(x) for x in list(v)}
    v = set().union(*(gate._views(x) for x in v))
    v |= {_rd._ANSI.sub("", x) for x in list(v)} | {gate._ANSI_AS_TEXT.sub("", x) for x in list(v)}
    v |= {gate.strip_controls(x) for x in list(v)}
    v |= gate._rendered(v)
    v |= {x.replace("[.]", ".") for x in list(v)}
    v |= {textnorm.fold(x) for x in list(v)}
    return v


def _p1d_holds(view, v):
    from hadavin_sdk.guard import textnorm
    if len(v) >= 12:
        try:
            return textnorm.scan_holds(view, v)
        except textnorm.TextnormError:
            return True
    return v in view


def _p1d_check(text, out, m):
    """PROTO v3: one put-back form (count rule of lookalike-leak section 5 item 3) + one dropped form (scan_holds)."""
    from hadavin_sdk.guard import textnorm
    known = {o for o in m.values() if not o.startswith("\0seed")}
    for v in _p1d_views(text):
        pm = _seeded(v)
        runmap.redact_text(v, pm)
        known |= {o for o in pm.values() if not o.startswith("\0seed")}
    if not known:
        return
    tally = {}
    def back(mt):
        o = m.get(mt.group(0))
        if o is None or o.startswith("\0seed"):
            return mt.group(0)
        tally[o] = tally.get(o, 0) + 1
        return " " + o + " "
    f_all = runmap.PLACEHOLDER.sub(back, out)
    f_none = runmap.PLACEHOLDER.sub(lambda mt: mt.group(0) if mt.group(0) not in m or m[mt.group(0)].startswith("\0seed") else " ", out)
    try:
        all_keys = [k for v in _p1d_views(f_all) for k in textnorm.scan_keyset(v)]
        none_views = _p1d_views(f_none)
        keymemo = {o: textnorm.scan_keyset(o) for o in set(tally) | known}
        long_known = [V for V in known if len(V) >= 12]
        for x in none_views:
            if any(V in x for V in known if len(V) < 12):
                raise _P1dRefused("_P1dRefused")
            with textnorm.scan_cache():
                if any(textnorm.scan_holds(x, V) for V in long_known):
                    raise _P1dRefused("_P1dRefused")
        for V in long_known:
            if True:
                for k in (k for k in keymemo[V] if len(k) >= 8):
                    c = max(s.count(k) for s in all_keys)
                    if c and c > sum(n * min((ok.count(k) for ok in keymemo[o]), default=0) for o, n in tally.items()):
                        raise _P1dRefused("_P1dRefused")
    except textnorm.TextnormError:
        raise _P1dRefused("_P1dRefused") from None


# A tag, but never a real placeholder (`<IPV4_1>`), and only the spaces and tabs after it (never a line break).
_TAGS = re.compile(r"(?:<(?![A-Z][A-Z0-9]*_\d+>)[^<>]{0,200}>[ \t]*)+")
_ASSIGNMENT_KINDS = {"SECRET", "APIKEY", "BEARER", "BASIC", "URLCRED"}


def _neutralise(text: str) -> str:
    return withhold_commands(sanitise_text(text))


def _seeded(text: str) -> runmap.RunMap:
    """A map that already holds the placeholders in `text` (a fake original that never occurs in text)."""
    return runmap.RunMap(
        {m.group(0): "\0seed" + m.group(0) for m in runmap.PLACEHOLDER.finditer(text)}
    )


def _assignment_originals(mapping: dict[str, str]) -> set[str]:
    """The originals of the assignment-kind secrets a map holds (seed entries excluded), spaces ignored."""
    return {
        "".join(original.split())
        for ph, original in mapping.items()
        if not original.startswith("\0seed")
        and (m := runmap.PLACEHOLDER.fullmatch(ph))
        and m.group(1) in _ASSIGNMENT_KINDS
    }


class Channel(Protocol):
    name: str
    max_card_chars: int  # the longest card text this channel posts; longer is `card_too_long`

    def send(self, req: ApprovalRequest, approver_ids: list[str]) -> str: ...
    def update(self, req: ApprovalRequest) -> None: ...
    def notify(self, principal_id: str, text: str) -> None: ...
    def post_card(self, card: Card) -> Delivery: ...

    def parse_decision(
        self, headers: Mapping[str, str], body: bytes, now_ts: float
    ) -> ApprovalDecision | None:
        """Verify the callback and return the decision with the approver taken from the verified request."""
        ...


class FakeChannel:
    """Records what would be sent. Callbacks are verified with the shared ``hmac_v0`` scheme under its own
    ``X-Hadavin-*`` headers and a test secret (with no secret every callback is refused); approvers are
    ``fake:<id>``."""

    name = "fake"
    header_prefix = "X-Hadavin"  # the shared hmac_v0 scheme under neutral header names

    max_card_chars = 3000

    def __init__(self, signing_secret: str = "", *, fail_cards: bool = False) -> None:
        self._secret = signing_secret
        self.fail_cards = fail_cards  # tests: make post_card report a failed delivery
        self.cards: list[Card] = []
        self.sent: list[tuple[str, str, list[str]]] = []
        self.updates: list[tuple[str, str]] = []
        self.notices: list[tuple[str, str]] = []

    def send(self, req: ApprovalRequest, approver_ids: list[str]) -> str:
        self.sent.append((req.approval_id, clean(req.summary), list(approver_ids)))
        return f"fake-{len(self.sent)}"

    def update(self, req: ApprovalRequest) -> None:
        self.updates.append((req.approval_id, req.status))

    def notify(self, principal_id: str, text: str) -> None:
        self.notices.append((principal_id, clean(text)))

    def post_card(self, card: Card) -> Delivery:
        from hadavin_sdk.approvals.cards import Delivery

        if self.fail_cards:
            return Delivery(ok=False, reason="channel_error")
        self.cards.append(card)
        return Delivery(ok=True, ref=f"fake-card-{len(self.cards)}")

    def parse_decision(
        self, headers: Mapping[str, str], body: bytes, now_ts: float
    ) -> ApprovalDecision | None:
        return hmac_v0.parse_button(
            headers, body, now_ts, self._secret, prefix=self.header_prefix, channel=self.name
        )
