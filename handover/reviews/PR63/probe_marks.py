"""Read-only probe for ticket P1 rev2 (item 6): does a spacing mark (Mc), modifier letter (Lm) or modifier symbol (Sk)
inserted into a name change could_be_same_person / identity_keys on the PR63 head, and what would the marks-dropped keys
cost on the names corpus. Usage: python3 -I probe_marks.py <snapshot root>"""

import itertools
import json
import sys
import unicodedata

root = sys.argv[1]
sys.path.insert(0, root + "/src")
from hadavin_sdk.guard import textnorm as t  # noqa: E402

print("FOLD_VERSION", t.FOLD_VERSION)
print("len(__all__)", len(t.__all__))
cases = [("alice", "aliःce"), ("alice", "alʰice"), ("alice", "ali^ce"), ("bob", "bʼob")]
for a, b in cases:
    marks = [f"U+{ord(c):04X} {unicodedata.category(c)}" for c in b if unicodedata.category(c) in ("Mc", "Lm", "Sk")]
    sv = t.squeeze_views(b)
    fv = t.fold_views(b, casefold=True, collapse_ws=True)
    print(
        repr(b), marks,
        "could_be_same_person:", t.could_be_same_person(a, b),
        "| a in squeeze_views:", a.upper() in sv,
        "| a in fold_views:", a in fv,
    )


def keys_marks(raw):
    return set(t.identity_keys(raw)) | set(
        t.key_tag() + v for v in t._views(raw, casefold=True, collapse_ws=True, marks_dropped=True)
    )


names = json.load(open(root + "/tests/fixtures/textnorm_names.json", encoding="utf-8"))
for group, items in names.items():
    if not isinstance(items, list) or not items or not isinstance(items[0], str):
        continue
    items = sorted(set(items))
    pairs = list(itertools.combinations(items, 2))
    now = sum(1 for a, b in pairs if t.could_be_same_person(a, b))
    after = sum(1 for a, b in pairs if not keys_marks(a).isdisjoint(keys_marks(b)))
    print(f"{group}: {len(items)} names, {len(pairs)} pairs; could_be_same_person now {now}; with marks-dropped keys {after}")
