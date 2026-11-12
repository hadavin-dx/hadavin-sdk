"""Approval channel Protocol and the fake channel. Channel text is template-built, redacted and link-free."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.approvals.gate import sanitise_text, withhold_commands
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import ApprovalDecision, ApprovalRequest
from hadavin_sdk.standins import stand_in

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
    out = runmap.redact_text(text, mapping, neutralise=_neutralise)
    # A key and a value split by markup (`password%<i></i>3Dx`) read as one only when the tags are DELETED, not turned
    # into spaces: that joined view (real placeholders and line breaks kept) is used when it finds a secret value the
    # text pass did not (compared by the originals, spaces ignored), not by count or kind.
    joined = _TAGS.sub("", text)
    if joined != text:
        joined_map = _seeded(joined)
        alt = runmap.redact_text(joined, joined_map, neutralise=_neutralise)
        if _assignment_originals(joined_map) - _assignment_originals(mapping):
            return alt
    return out


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


@stand_in
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
