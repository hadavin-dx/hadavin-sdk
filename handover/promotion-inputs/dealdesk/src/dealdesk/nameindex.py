"""Inverted index over the tenant's account names, so a name scan costs the number of CANDIDATES, not the number of accounts.

Why: the first burst measurement showed the linear scan per message (every message compared against every account name) made 10,000 messages take 27 times
as long as 1,000 (quadratic). A whole-name occurrence needs the name's first alphanumeric run to be a MAXIMAL alphanumeric run of the text (the characters
around a whole-name match are not alphanumeric), so the index maps that first run to the names that start with it. `by_views` and `by_lower` return a
SUPERSET of the names that can occur; the callers still run their exact whole-name test on every candidate, so the answer equals the linear scan
(`tests/test_nameindex.py` checks that on random and hostile names). Names with no alphanumeric run are kept in an `always` list.

Two token notions, one per matcher: Unicode alphanumerics for the quote-text check (`desk_rules._whole`), ASCII alphanumerics for the inbound-message
check (`gate_rules._whole_name`).
"""

from __future__ import annotations

import re
from collections import defaultdict

from dealdesk.textnorm import views

_UNI = re.compile(r"[^\W_]+")  # same set as str.isalnum
_ASCII = re.compile(r"[A-Za-z0-9]+")


def lower_norm(name: str) -> str:
    return " ".join(name.lower().split())


class NameIndex:
    def __init__(self, accounts: dict[str, str]) -> None:
        self.entries: list[tuple[str, str]] = list(accounts.items())
        self._view: defaultdict[str, list[int]] = defaultdict(list)
        self._lower: defaultdict[str, list[int]] = defaultdict(list)
        self._always_view: list[int] = []
        self._always_lower: list[int] = []
        for i, (_aid, name) in enumerate(self.entries):
            firsts = set()
            for v in views(name):
                m = _UNI.search(v) if v else None
                if m:
                    firsts.add(m.group(0))
            if firsts:
                for t in firsts:
                    self._view[t].append(i)
            else:
                self._always_view.append(i)
            m = _ASCII.search(lower_norm(name))
            if m:
                self._lower[m.group(0)].append(i)
            else:
                self._always_lower.append(i)

    def by_views(self, own: tuple[str, str]) -> list[tuple[str, str]]:
        """Entries whose folded name could occur inside one of the two folded views `own` (a superset)."""
        idx = set(self._always_view)
        for v in own:
            for t in set(_UNI.findall(v)):
                idx.update(self._view.get(t, ()))
        return [self.entries[i] for i in sorted(idx)]

    def by_lower(self, clean: str) -> list[tuple[str, str]]:
        """Entries whose lower-cased name could occur inside the cleaned message text (a superset)."""
        idx = set(self._always_lower)
        for t in set(_ASCII.findall(clean)):
            idx.update(self._lower.get(t, ()))
        return [self.entries[i] for i in sorted(idx)]
