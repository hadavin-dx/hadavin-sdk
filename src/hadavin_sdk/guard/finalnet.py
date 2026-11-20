"""G15: the final safety net of the model gate, INDEPENDENT of the redactor.

The gate's net (`runmap.held_value_left`, `held_in_views`) reuses the sweep's own finder (`redact._Redactor`, its
trie, the run map checker), so a bug in the sweep can be a bug in the net. This module is the last check on the bytes
about to be sent and shares none of that matching code: a plain-substring search of every registered SECRET value
(the set the gate's snapshot holds: a secret kind, 4 or more characters, `runmap.MapSnapshot.secret_values`) with an
Aho-Corasick automaton built here.

What it does:

- Matching is a plain substring test: no regex is ever built from a client value, no case folding, no normalising
  inside the matcher. A placeholder of the run's own map (an exact KEY) is a barrier: the automaton restarts after
  it, so `<SECRET_1>` never matches a value `SECRET_1`; a forged placeholder-shaped token is not a key and is read
  as plain text.
- The text is searched as written and in the forms a reader may decode: the text without NUL and lone surrogates,
  every `runmap._views` form of it (the folded, composed, unescaped, percent and entity forms: those functions only
  PRODUCE the views, the matching is this module's) and the text of every base64 run that decodes to text
  (`runmap._b64_units`, `_b64_text`). Every secret value is searched in its written form and in its folded and
  composed spellings (`textnorm`), so a precomposed value is found in a decomposed text and the other way round.
- Cost: the automaton is built in O(total value characters) and a text is read in O(text + matches); the fail
  steps of one scan never exceed its length (`FinalNet.fail_steps`). Memory is bounded by an explicit cap on the
  automaton's states (`MAX_STATES`): a set of values that would need more is refused closed with `FinalNetTooLarge`
  (fixed text, never a value), and the gate refuses the call.
- It answers a bool or the INDEX of the first offending value in the sorted value list, never the value.

Stated limits (the module adds a check, it does not widen the views): a spelling no view of `runmap._views` and no
base64 run produces is not found (a ROT13 copy, a value split by words); a base64 text is read one level (its
decoded text, and that text's `_views`), not nested; a value split across two chunks the gate enforced one by one is
not seen, as in the gate's own net. Pinned by tests/test_finalnet.py.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterable

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap

MIN_VALUE_CHARS = 4  # the threshold of the gate's net (`held_value_left`): shorter values are not swept in every copy
MAX_STATES = (
    defaults.MAX_MAP_CHARS
)  # explicit cap on automaton states (about 100 bytes each): 524,288
MAX_CLEAN_CACHE = defaults.GATE_CACHE_MAX_ENTRIES

_TOKEN = re.compile(
    r"<[A-Z][A-Z0-9]*_[0-9]+>"
)  # a placeholder SHAPE; a key of the map only is a barrier
_SHIFT = 21  # a code point is below 2**21: the goto table key is (state << 21) | ord(char)


class FinalNetTooLarge(Exception):
    """The values need more than `MAX_STATES` automaton states. Fixed text: it never names a value."""

    def __init__(self) -> None:
        super().__init__("final net: too many characters of secret values")


def _spellings(value: str) -> list[str]:
    """`value` as stored and, when different, its folded and composed forms (the forms the views of a text take)."""
    out = [value]
    if not value.isascii():
        for form in (runmap.canonical(value), runmap.composed(value)):
            if form and form not in out:
                out.append(form)
    return out


class FinalNet:
    """Aho-Corasick automaton over the secret values; `first_hit(text)` is the index of the first value found."""

    def __init__(self, values: Iterable[str], max_states: int | None = None) -> None:
        max_states = MAX_STATES if max_states is None else max_states
        self.values = sorted(
            {v for v in values if isinstance(v, str) and len(v) >= MIN_VALUE_CHARS}
        )
        self.source: frozenset[str] | None = (
            None  # the value set the owner built this from (its cache key)
        )
        self.fail_steps = (
            0  # fail links followed by the last scan (a scan follows at most len(text))
        )
        self._clean: set[tuple[str, tuple[tuple[int, int], ...]]] = (
            set()
        )  # SHA-256 of texts found clean by `check`
        goto: dict[int, int] = {}
        owner: list[int] = [-1]  # state -> index of a value ending here (-1 none)
        parent: list[int] = [0]
        char: list[int] = [0]
        depth: list[int] = [0]
        for index, value in enumerate(self.values):
            for spelling in _spellings(value):
                state = 0
                for c in spelling:
                    key = (state << _SHIFT) | ord(c)
                    nxt = goto.get(key)
                    if nxt is None:
                        if len(owner) >= max_states:
                            raise FinalNetTooLarge
                        nxt = len(owner)
                        goto[key] = nxt
                        owner.append(-1)
                        parent.append(state)
                        char.append(ord(c))
                        depth.append(depth[state] + 1)
                    state = nxt
                if owner[state] < 0:
                    owner[state] = index
        fail = [0] * len(owner)
        # states in order of depth: a state's fail link has a smaller depth, so it is final before the state is read
        order = sorted(range(1, len(owner)), key=depth.__getitem__)
        for v in order:
            p = parent[v]
            if p == 0:
                continue  # depth 1: fail is the root
            f, c = fail[p], char[v]
            while f and ((f << _SHIFT) | c) not in goto:
                f = fail[f]
            fail[v] = goto.get((f << _SHIFT) | c, 0)
            if owner[v] < 0:
                owner[v] = owner[fail[v]]  # the nearest value that ends here as a suffix
        self._goto, self._fail, self._owner = goto, fail, owner
        self.states = len(owner)

    def first_hit(
        self,
        text: str,
        barrier: Callable[[str], bool] | None = None,
        fixed: tuple[tuple[int, int], ...] = (),
    ) -> int | None:
        """Index (in `self.values`) of the first value that occurs in `text` as a plain substring, else None.
        `barrier(token)` True for a `<NAME_n>` token that is a placeholder of the run: the search restarts after it.
        `fixed`: (start, end) spans of the trusted framing's fixed words of THIS text (the gate never replaces inside
        them: a value that lies inside `ESULT` of `<<TOOL RESULT` is the stated limit of the gate's own net); the
        search restarts after each. Spans apply to the text as written only, never to a decoded form."""
        goto, fail, owner = self._goto, self._fail, self._owner
        steps = 0
        self.fail_steps = 0
        if not owner or len(owner) == 1:
            return None
        pieces: list[str]
        if (barrier is not None and "<" in text) or fixed:
            cuts = list(fixed)
            if barrier is not None and "<" in text:
                cuts.extend(m.span() for m in _TOKEN.finditer(text) if barrier(m.group()))
            pieces, last = [], 0
            for start, end in sorted(cuts):
                if start >= last:
                    pieces.append(text[last:start])
                    last = end
            pieces.append(text[last:])
        else:
            pieces = [text]
        for piece in pieces:
            state = 0
            for c in piece:
                key = ord(c)
                while state and ((state << _SHIFT) | key) not in goto:
                    state = fail[state]
                    steps += 1
                state = goto.get((state << _SHIFT) | key, 0)
                hit = owner[state]
                if hit >= 0:
                    self.fail_steps = steps
                    return hit
        self.fail_steps = steps
        return None

    def forms(self, text: str) -> list[str]:
        """The text and the decoded forms a reader may read: without NUL and lone surrogates, every `_views` form
        (in windows when long) and the text of each base64 run that decodes to text with its own views. Produced by
        the redactor's view functions; nothing in them is matched here. May raise `runmap.InputTooLarge` or
        `RedactionError` (the caller refuses)."""
        out = [text]
        cleaned = runmap._clean(text)
        if cleaned != text:
            out.append(cleaned)
        longest = max((len(v) for v in self.values), default=1)
        if not (cleaned.isascii() and not any(c in cleaned for c in "\\%&")):
            for window in runmap._windows(cleaned, longest):
                out.extend(runmap._views(window))
        for decoded in _base64_texts(cleaned):
            out.append(decoded)
            if not (decoded.isascii() and not any(c in decoded for c in "\\%&")):
                out.extend(runmap._views(decoded))
        return out

    def check(
        self,
        text: str,
        keys: Callable[[str], bool] | None = None,
        fixed: tuple[tuple[int, int], ...] = (),
    ) -> bool:
        """True when a registered secret value is left in `text` (as written or in a decoded form). A text found
        clean is remembered by its hash, so an unchanged message of a long conversation is read once."""
        digest = (hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest(), fixed)
        if digest in self._clean:
            return False
        for i, form in enumerate(self.forms(text)):
            if self.first_hit(form, keys, fixed if i == 0 else ()) is not None:
                return True
        if len(self._clean) >= MAX_CLEAN_CACHE:
            self._clean.clear()
        self._clean.add(digest)
        return False


def _base64_texts(text: str) -> list[str]:
    """The text each base64 run (and each line of a wrapped block) decodes to; only runs that decode to text."""
    out: list[str] = []
    _stripped, units = runmap._b64_units(text)
    for unit in units:
        for u in (unit, *unit.parts):
            decoded = runmap._b64_text(u.joined)
            if decoded:
                out.append(decoded)
    return out


def secret_left(text: str, secrets: Iterable[str]) -> int | None:
    """Index of the first value of `secrets` (sorted, values under `MIN_VALUE_CHARS` ignored) found in `text` as a
    plain substring or in a decoded form, else None. Never returns a value. `FinalNetTooLarge` past `MAX_STATES`."""
    net = FinalNet(secrets)
    for form in net.forms(text):
        hit = net.first_hit(form)
        if hit is not None:
            return hit
    return None
