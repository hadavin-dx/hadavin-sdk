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


class RegexDetector:
    backend = "regex"

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    @staticmethod
    def _read(text: str) -> Iterator[tuple[str, tuple[str, ...]]]:
        """``(piece, its scan views)``: the text whole when the fold takes it; otherwise (over the size rule) overlapping pieces of
        ``defaults.TEXTNORM_INJECTION_CHUNK_CHARS`` characters that share ``defaults.TEXTNORM_INJECTION_OVERLAP_CHARS``, each halved until the fold
        takes it, so a long document is READ, not flagged. CEILING: a text longer than ``defaults.TEXTNORM_INJECTION_MAX_CHARS`` raises
        ``TextTooLong`` (flagged as guard_unavailable), and a phrase whose letters are spread over more than the overlap across a piece boundary is
        not seen (a tripwire, not a gate)."""
        if len(text) > defaults.TEXTNORM_INJECTION_MAX_CHARS:
            raise textnorm.TextTooLong(
                f"a text of {len(text)} characters is over the injection check's limit of {defaults.TEXTNORM_INJECTION_MAX_CHARS}"
            )
        try:
            yield text, textnorm.scan_views_no_value(text)
            return
        except textnorm.TextTooLong:
            pass
        size = defaults.TEXTNORM_INJECTION_CHUNK_CHARS
        step = size - defaults.TEXTNORM_INJECTION_OVERLAP_CHARS
        for start in range(0, len(text), step):
            yield from RegexDetector._fit(text[start : start + size])
            if start + size >= len(text):
                break

    @staticmethod
    def _fit(piece: str) -> Iterator[tuple[str, tuple[str, ...]]]:
        try:
            yield piece, textnorm.scan_views_no_value(piece)
        except textnorm.TextTooLong:
            half = len(piece) // 2
            if half == 0:
                raise
            overlap = defaults.TEXTNORM_INJECTION_OVERLAP_CHARS
            yield from RegexDetector._fit(piece[: half + overlap])
            yield from RegexDetector._fit(piece[half:])

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
