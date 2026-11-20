"""Injection detector: a tripwire, never a gate that clears text as safe. Fail closed.

The regex detector rewrites WARDEN's tripwire + STEER idea for documents: phrases that try to steer the model.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from decimal import Decimal
from typing import Protocol

from hadavin_sdk import defaults
from hadavin_sdk.guard import textnorm
from hadavin_sdk.guard.runmap import safe_head
from hadavin_sdk.models import Verdict

_LOG = logging.getLogger("hadavin_sdk.guard")


class Detector(Protocol):
    def check(self, text: str, source: str) -> Verdict: ...


_PATTERNS = [
    r"\bignore\b.{0,40}\b(previous|prior|above|earlier|all)\b.{0,20}\b(instructions?|rules?|prompts?)\b",
    r"\bdisregard\b.{0,40}\b(instructions?|rules?|prompts?|above)\b",
    r"\bforget\b.{0,30}\b(instructions?|rules?|everything)\b",
    r"\b(system|developer)\s+prompt\b",
    r"\byou\s+are\s+now\b",
    r"\bnew\s+instructions?\s*:",
    r"\b(act|pretend)\s+as\b",
    r"\boverride\b.{0,30}\b(rules?|policy|safety|instructions?)\b",
]
_RX = re.compile("|".join(f"(?:{p})" for p in _PATTERNS), re.IGNORECASE | re.DOTALL)
_SQUASH = re.compile(r"[^a-z]")
_SQUASHED = ("ignorepreviousinstructions", "ignoreallpreviousinstructions", "disregardtheabove")


def _check_geometry() -> None:
    """The settings of the chunked read, checked before use (a bad value raises, which ``injection_check`` turns into a flag): whole positive
    numbers, an overlap smaller than the piece, a largest overlap that still leaves a piece twice as long as it."""
    names = (
        "TEXTNORM_INJECTION_CHUNK_CHARS",
        "TEXTNORM_INJECTION_OVERLAP_CHARS",
        "TEXTNORM_INJECTION_OVERLAP_MAX_CHARS",
        "TEXTNORM_INJECTION_PHRASE_CHARS",
    )
    for name in names:
        value = getattr(defaults, name)
        if type(value) is not int or value < 1:
            raise ValueError(f"defaults.{name} must be a whole number of at least 1")
    size = defaults.TEXTNORM_INJECTION_CHUNK_CHARS
    low = defaults.TEXTNORM_INJECTION_OVERLAP_CHARS
    high = defaults.TEXTNORM_INJECTION_OVERLAP_MAX_CHARS
    if not (low <= high and 2 * high <= size):
        raise ValueError(
            "the injection overlap must be smaller than the largest overlap, and twice the largest must fit in one piece "
            f"(overlap {low}, largest {high}, piece {size})"
        )


def _holds(window: str, need_kept: int, need_letters: int) -> bool:
    """True when EVERY view of ``window`` (``textnorm.scan_views_no_value``, the views the scan reads) keeps at least ``need_kept`` characters and holds at
    least ``need_letters`` a-z letters. A phrase is read in one of the views, so a count that holds in all of them holds in the one that matters. A view
    drops what the fold drops (invisible characters, spaces) and turns a look-alike into its letter (a Cyrillic o gives one), so padding is not counted
    and a tag character (which reads as a letter in one view only) cannot lend letters to the others. No view at all (nothing but invisible
    characters) holds nothing."""
    # A mark on both sides: a view that drops everything of ``window`` (the tag characters, which read as letters in one view only) is then still a
    # view (of the marks, with no letter), not a view that is left out because it is empty, so it counts as zero.
    views = textnorm.scan_views_no_value("|" + window + "|")
    if not views:
        return False
    return (
        min(len(v) for v in views)
        >= need_kept + 2  # +2: the marks (some views drop them; that only asks for a little more)
        and min(len(_SQUASH.sub("", v.lower())) for v in views) >= need_letters
    )


def _start_of_next(text: str, start: int, end: int) -> int:
    """Where the piece after ``text[start:end]`` starts. Going back from ``end``, the new piece must hold at least
    ``defaults.TEXTNORM_INJECTION_OVERLAP_CHARS`` characters of the old one, AND in every view of it at least ``defaults.TEXTNORM_INJECTION_PHRASE_CHARS`` + 1
    characters the fold keeps, AND more letters than the longest squeezed phrase (``_holds``). Then a phrase cut by the boundary would have to hold all
    of those and its own first and last letter: more than it can. Invisible characters, spaces, digits and punctuation between its letters do not
    help the writer: they are not counted, the start just moves back (in steps of a quarter of the overlap so far, so the work stays small) until
    enough real ones are in. If that takes more than ``defaults.TEXTNORM_INJECTION_OVERLAP_MAX_CHARS`` characters, or the piece itself begins first
    (a piece with almost no letters before the boundary), the text is refused (``TextTooLong``, fail closed)."""
    need_kept = defaults.TEXTNORM_INJECTION_PHRASE_CHARS + 1
    need_letters = max(len(s) for s in _SQUASHED) + 1
    low = defaults.TEXTNORM_INJECTION_OVERLAP_CHARS
    high = defaults.TEXTNORM_INJECTION_OVERLAP_MAX_CHARS
    cap = min(high, end - start - 2)
    back = min(low, cap)
    while back >= 1:
        if back >= low and _holds(text[end - back : end], need_kept, need_letters):
            return end - back
        if back >= cap:
            break
        back = min(cap, back + max(16, back // 4))
    raise textnorm.TextTooLong(
        f"the {back} characters before a piece boundary (the most allowed: {high}) hold too few letters to read a steering phrase across it"
    )


class RegexDetector:
    backend = "regex"

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    @staticmethod
    def _read(text: str) -> Iterator[tuple[str, tuple[str, ...]]]:
        """``(piece, its scan views)``: the text whole when the fold takes it; otherwise (over the size rule) overlapping pieces of about
        ``defaults.TEXTNORM_INJECTION_CHUNK_CHARS`` characters, each halved until the fold takes it, so a long document is READ, not flagged.
        A piece starts where ``_start_of_next`` says (at least ``defaults.TEXTNORM_INJECTION_OVERLAP_CHARS`` before the end of the one before,
        and far enough back to hold enough letters that no steering phrase can be cut in two, however many invisible or other non-letter
        characters its writer puts between its letters). CEILING: a text longer than ``defaults.TEXTNORM_INJECTION_MAX_CHARS`` raises
        ``TextTooLong`` (flagged as guard_unavailable), and so does a boundary that has too few letters before it within
        ``defaults.TEXTNORM_INJECTION_OVERLAP_MAX_CHARS`` characters (fail closed, never a pass)."""
        if len(text) > defaults.TEXTNORM_INJECTION_MAX_CHARS:
            raise textnorm.TextTooLong(
                f"a text of {len(text)} characters is over the injection check's limit of {defaults.TEXTNORM_INJECTION_MAX_CHARS}"
            )
        try:
            yield text, textnorm.scan_views_no_value(text)
            return
        except textnorm.TextTooLong:
            pass
        _check_geometry()
        size = defaults.TEXTNORM_INJECTION_CHUNK_CHARS
        start = 0
        while True:
            end = min(start + size, len(text))
            yield from RegexDetector._fit(text[start:end])
            if end >= len(text):
                break
            start = _start_of_next(text, start, end)

    @staticmethod
    def _fit(piece: str) -> Iterator[tuple[str, tuple[str, ...]]]:
        try:
            yield piece, textnorm.scan_views_no_value(piece)
        except textnorm.TextTooLong:
            half = len(piece) // 2
            if half == 0:
                raise
            # The second part starts where ``_start_of_next`` says. If the first half is too short or too bare to look back over, the cut moves
            # later (the first part grows, the second shrinks), so both parts are smaller than the piece and the recursion ends.
            cut, second = half, None
            while second is None:
                try:
                    second = _start_of_next(piece, 0, cut)
                except textnorm.TextTooLong:
                    cut += max(1, half // 2)
                    if cut >= len(piece):
                        raise
            yield from RegexDetector._fit(piece[:cut])
            yield from RegexDetector._fit(piece[second:])

    def _score(self, text: str) -> float:
        """1.0 when the raw text OR any view of it (``textnorm.scan_views_no_value``: the look-alike fold, the squeeze, the scan keys; there is no protected value here) holds a
        steering phrase, so a Cyrillic o or an inserted mark does not hide it. A text over the size rule of the fold is read in overlapping pieces
        (``_read``); a text over ``defaults.TEXTNORM_INJECTION_MAX_CHARS`` raises ``TextnormError``, which ``injection_check`` turns into a flag
        (fail closed)."""
        for piece, views in self._read(text):
            for view in (piece, *views):
                if _RX.search(view):
                    return 1.0
                squashed = _SQUASH.sub("", view.lower())
                if any(s in squashed for s in _SQUASHED):
                    return 1.0
        return 0.0

    def check(self, text: str, source: str) -> Verdict:
        score = self._score(text)
        flagged = score >= self.threshold
        return Verdict(
            flagged=flagged,
            score=score,
            backend=self.backend,
            reason_code="injection_suspected" if flagged else None,
        )


class AnyOf:
    """A detector list (design 4.3): every entry runs, and any flag flags the run. The combined verdict has the
    max score, the names that flagged joined by `+`, the first flag's reason and the summed cost. One entry's
    error is that entry's flag (guard_unavailable); the others still run."""

    def __init__(self, detectors: list[Detector]) -> None:
        self.detectors = detectors

    def check(self, text: str, source: str) -> Verdict:
        verdicts = [injection_check(d, text, source) for d in self.detectors]
        flagged = [v for v in verdicts if v.flagged]
        return Verdict(
            flagged=bool(flagged),
            score=max(v.score for v in verdicts),
            backend="+".join(v.backend for v in flagged or verdicts),
            reason_code=flagged[0].reason_code if flagged else None,
            cost_usd=sum((v.cost_usd for v in verdicts), Decimal(0)),
        )


def combine(detectors: list[Detector]) -> Detector:
    return detectors[0] if len(detectors) == 1 else AnyOf(detectors)


def injection_check(detector: Detector, text: str, source: str) -> Verdict:
    """Any detector error is a flag (guard_unavailable), never a pass."""
    try:
        return detector.check(text, source)
    except Exception as exc:  # noqa: BLE001 - fail closed on anything
        # The cause is logged (class and message, never the text checked) so a broken detector is
        # diagnosable, e.g. a custom detector returning a score outside 0..1.
        _LOG.warning(
            "detector %s failed, run flagged: %s: %s",
            type(detector).__name__,
            type(exc).__name__,
            safe_head(str(exc), 300),
        )
        # Named after the detector that failed, so a list's verdict says which one.
        name = getattr(detector, "backend", None)
        name = name if isinstance(name, str) and name else "error"
        return Verdict(flagged=True, score=1.0, backend=name, reason_code="guard_unavailable")
