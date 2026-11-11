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
    mention word after a masked value is neutralised."""
    # The neutralising hook (sanitise, then withhold commands) runs on the text AND on every decoded view the redactor
    # tries (`redact_text(..., neutralise=)`): a view that replaces the text (because it found a secret only the decoding
    # shows) is sanitised too, so `%72m -rf /`, `%3Cimg%3E`, `&lt;!channel&gt;` cannot come back as a command, an image
    # or a mention. After the final redaction brackets are added, wide dots are written as dots, `@here`-style words are
    # rewritten, and the words after a masked unquoted credential value are dropped (`whole_assignment_values`); no
    # other text is removed or joined. Placeholders already in the text (`<IPV4_1>`) survive sanitising (tested) and are
    # seeded into the map so a new one never reuses their number.
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
        if _assignment_originals(joined_map) - _assignment_originals(mapping):
            return alt
    return out


# A tag, but never a real placeholder (`<IPV4_1>`), and only the spaces and tabs after it (never a line break).
_TAGS = re.compile(r"(?:<(?![A-Z][A-Z0-9]*_\d+>)[^<>]{0,200}>[ \t]*)+")
_ASSIGNMENT_KINDS = {"SECRET", "APIKEY", "BEARER", "BASIC", "URLCRED"}


def _neutralise(text: str) -> str:
    return withhold_commands(sanitise_text(text, defang=False))


def redact_for_people(text: str, mapping: dict[str, str]) -> str:
    """The one function that turns text into what a person reads on a card: sanitise and withhold commands (on the
    text and on every decoded view the redactor tries), ONE redaction, then `gate.defang_domains` on the masked text.
    Bracketing dots before the redaction would hide an address from the redactor (`bob@example[.]com` is no address
    to it), so the brackets are written last."""
    return defang_domains(
        whole_assignment_values(runmap.redact_text(text, mapping, neutralise=_neutralise))
    )


# A credential key, `=` or `:`, and a placeholder the redactor wrote for its value (the redactor stops an unquoted
# value at the first white space, so the words after it were left readable: `password=<SECRET_1> horse battery`).
_ASSIGNED = re.compile(
    r"(?i)(?:password|passwd|pwd|passphrase|pass|secret|token|api[_\-]?key|apikey|credential|auth)[\w.\-]{0,20}"
    r"[\"']?[ \t]*[:=][ \t]*<SECRET_\d+>"
)
# The words after it, up to the end of the line or the next `key=` / `key:` / placeholder / quote.
_TAIL_WORD = re.compile(r"[ \t]+(?![\w.\-]+[\"']?[ \t]*[:=])[^\s<>\"']+")


def whole_assignment_values(text: str) -> str:
    """An unquoted value that holds spaces is masked whole on a card, as it is in a case bundle: the words that follow a
    masked credential value (up to the end of the line or the next `key=`) are dropped, so `password=<SECRET_1>` is all
    a person sees of `password=correct horse battery staple`. Cost: prose right after an unquoted credential value on
    the same line (`token=abc12345 failed for bob`) is dropped with it. Idempotent: it only removes."""
    out: list[str] = []
    pos = 0
    for m in _ASSIGNED.finditer(text):
        if m.start() < pos:
            continue
        end = m.end()
        while (w := _TAIL_WORD.match(text, end)) is not None:
            end = w.end()
        out.append(text[pos : m.end()])
        pos = end
    out.append(text[pos:])
    return "".join(out)


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
