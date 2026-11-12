"""Approval channel Protocol and the fake channel. Channel text is template-built, redacted and link-free."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.approvals.gate import defang_domains, sanitise_text, withhold_commands
from hadavin_sdk.guard import runmap
from hadavin_sdk.models import ApprovalDecision, ApprovalRequest

if TYPE_CHECKING:
    from hadavin_sdk.approvals.cards import Card, Delivery


def clean(text: str) -> str:
    """WARDEN's G3 cleaning (`gate.sanitise_text`): no link, image, HTML, mention, control character or forged
    markdown structure survives in text a person acts on; then G4 (`gate.withhold_commands`): no command a person could
    paste to change a system, on any platform; then one redaction; last, dots of domains outside code are bracketed and a
    mention word is neutralised."""
    # Order of the cleaning, and why:
    # 1. The neutralising hook (sanitise, then withhold commands) runs on the text AND on every decoded view the redactor
    #    tries (`redact_text(..., neutralise=)`). A view that replaces the text (the decoding shows a secret only there) is
    #    sanitised too, so `%72m -rf /`, `%3Cimg%3E` and `&lt;!channel&gt;` cannot come back as a command, an image or a
    #    mention.
    # 2. After the final redaction, brackets are added to domains and wide dots are written as dots; `@here`-style words
    #    are rewritten. Nothing is removed or joined: an unquoted credential value that holds spaces is masked whole by the
    #    redactor's own key rule (`guard.redact._VALUE_TAIL`); flags and the words after the next key stay.
    # 3. Placeholders already in the text (`<IPV4_1>`) survive sanitising (tested) and are seeded into the map, so a new
    #    one never reuses their number.
    text = text.replace("\x00", "")
    mapping = _seeded(text)
    out = redact_for_people(text, mapping)
    # A key and a value split by markup (`password%<i></i>3Dx`) read as one only when the tags are DELETED, not turned
    # into spaces: that joined view (real placeholders and line breaks kept) is used when it finds a secret value the
    # text pass did not (compared by the originals, spaces ignored), not by count or kind.
    joined = _TAGS.sub("", text)
    if joined != text:
        joined_map = runmap.RunMap({**_seeded(joined), **mapping})
        alt = redact_for_people(joined, joined_map)
        if _secret_originals(joined_map) - _secret_originals(mapping):
            return alt
    return out


# A tag, but never a real placeholder (`<IPV4_1>`), and only the spaces and tabs after it (never a line break).
_TAGS = re.compile(r"(?:<(?![A-Z][A-Z0-9]*_\d+>)[^<>]{0,200}>[ \t]*)+")


# The control characters that `\s` reads as white space (`\x0b`, `\x0c`, `\x1c`-`\x1f`, `\x85`, U+2028, U+2029): the sanitiser removes a
# control character, which JOINED the words on both sides (`Basic<VT><token>` became `Basic<token>`, one word no rule read as a
# scheme word and a token; main did the same). They are written as a plain space first, so the redactor sees the gap the
# text had (round 9, Issue 1, a sibling found while fixing). Other controls are still removed.
_WHITE_SPACE_CONTROLS = re.compile("[\x0b\x0c\x1c-\x1f\x85\u2028\u2029]")
# Of those, the ones that `str.splitlines` reads as a line break (all but `\x1f`) and that a space or a tab follows (a line fold) are written as a LINE FEED, not a space (batch 13, group 7):
# a tool that splits on them sees a line break there, and a header folded over one (`Authorization: Bearer <a><VT> <b>`) is a folded header
# for the rules that read the fold; as a space it was one flat line and the second part stayed readable on the card path.
_LINE_BREAK_CONTROLS = re.compile("[\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029](?=[ \t])")


def _neutralise(text: str) -> str:
    text = _LINE_BREAK_CONTROLS.sub("\n", text)
    return withhold_commands(sanitise_text(_WHITE_SPACE_CONTROLS.sub(" ", text), defang=False))


def redact_for_people(text: str, mapping: dict[str, str]) -> str:
    """The one function that turns text into what a person reads on a card: sanitise and withhold commands (on the
    text and on every decoded view the redactor tries), ONE redaction, then `gate.defang_domains` on the masked text.
    Bracketing dots before the redaction would hide an address from the redactor (`bob@example[.]com` is no address
    to it), so the brackets are written last."""
    return defang_domains(runmap.redact_text(text, mapping, neutralise=_neutralise))


def _seeded(text: str) -> runmap.RunMap:
    """A map that already holds the placeholders in `text` (a fake original that never occurs in text)."""
    return runmap.RunMap(
        {m.group(0): "\0seed" + m.group(0) for m in runmap.PLACEHOLDER.finditer(text)}
    )


def _secret_originals(mapping: dict[str, str]) -> set[str]:
    """The originals of the secrets a map holds (every kind of `runmap.SECRET_KINDS`, the one list; seed entries
    excluded), spaces ignored."""
    return {
        "".join(original.split())
        for ph, original in mapping.items()
        if not original.startswith("\0seed")
        and (m := runmap.PLACEHOLDER.fullmatch(ph))
        and m.group(1) in runmap.SECRET_KINDS
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
