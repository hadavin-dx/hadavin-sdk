"""Mutant 100 / old guard of mutant 90: equivalence evidence. Compares the tool and error paths with and without the removed
extra view (the decoded readings with ignorable characters taken out). Usage: PYTHONPATH=src python equivalence_100.py"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fuzz_classify import HAND, KEY, texts

from hadavin_sdk import tools
from hadavin_sdk.guard import hidden

IGN = ["\u2066", "\u200b", "\u202e", "\u2060", "\ufeff", "\u00ad"]
ENC = [
    lambda x: x,
    lambda x: "".join(f"%{ord(c):02x}" if c in "AKI" else c for c in x),
    lambda x: x.replace("A", "&#65;", 1),
    lambda x: x.replace("A", "\\u0041", 1),
]


def second_set():
    r = random.Random(3)  # noqa: S311 - a seeded evidence generator
    for _ in range(4000):
        sec = r.choice([KEY, HAND])
        k = r.randrange(1, len(sec))
        cut = sec[:k] + r.choice(IGN) + sec[k:]
        yield (
            r.choice(["", "\x1b[31m ", "a "]) + r.choice(ENC)(cut) + r.choice(["", " " + sec, " z"])
        )


def outputs(corpus):
    return [
        (tools.prepare_output(t, {}, 4000, [HAND]), tools.error_reason(ValueError(t), [HAND]))
        for t in corpus
    ]


corpus = list(texts(3000)) + list(second_set())
current = outputs(corpus)
original = tools._decoded_readings


def with_extra_view(text):
    views = original(text)
    return tuple(dict.fromkeys([*views, *(hidden.IGNORABLE_RE.sub("", v) for v in views)]))


tools._decoded_readings = with_extra_view
extra = outputs(corpus)
tools._decoded_readings = original
diff = sum(a != b for a, b in zip(current, extra, strict=True))
print("texts", len(corpus), "| outputs differing with the extra view", diff)
sys.exit(1 if diff else 0)
