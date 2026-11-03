"""Approval channel Protocol and the fake channel. Channel text is template-built, redacted and link-free."""

from __future__ import annotations

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
    # Sanitise and withhold FIRST, redact ONCE and LAST through the one choke point (NFKC, invisible characters, escapes,
    # the layered decode, the size cap; a text over the cap is REFUSED, never cut): nothing transforms the text after its
    # final redaction, so a tag, a zero-width character or a removed command cannot join pieces pass one saw apart.
    # Placeholders already in the text (`<IPV4_1>`) survive sanitising (tested).
    cleaned = withhold_commands(sanitise_text(text))
    mapping = runmap.RunMap()
    out = runmap.redact_text(cleaned, mapping)
    # A key and a value split by markup that became a space (`password%<i> </i>3Dx`) read as one only without spaces:
    # that view is used when it finds a secret the spaced text hid (fidelity of that one card is traded for safety).
    compact_map = runmap.RunMap()
    compact = runmap.redact_text("".join(cleaned.split()), compact_map)
    if _secret_kinds(compact_map) - _secret_kinds(mapping):
        return compact
    return out


def _secret_kinds(mapping: dict[str, str]) -> set[str]:
    kinds = {m.group(1) for ph in mapping if (m := runmap.PLACEHOLDER.fullmatch(ph))}
    # a markup-split KEY and value: the assignment kinds only (the entropy kind would fire on any run of words joined)
    return kinds & {"SECRET", "APIKEY", "BEARER", "BASIC", "URLCRED"}


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
