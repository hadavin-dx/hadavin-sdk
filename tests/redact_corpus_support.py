"""Shared corpus helper of the redactor tests: the seeded text generator that tests/test_runmap_map_write.py and
tests/test_redact_idempotent_property.py both use (moved from the deleted tests/test_runmap_is_masked.py, lead review
round 2, m7). `random_text(random.Random(20261120))` x 300 and `LOOKALIKES` are corpora of the property test: the
property test's own count test pins the total (1,835 inputs)."""

from __future__ import annotations

import random
from urllib.parse import quote

KEY = "AKIA" + "IOSFODNN7EXAMPLE"  # the documented AWS example key, built from parts
TOKEN = "s3cr3t" + "VALUE9xQ2"  # a fake, built from parts
IP = "10.0.0.5"

FILLER = [
    "ERROR",
    "upstream",
    "refused",
    "retry",
    "at",
    "from",
    "deploy",
    "ok",
    "line",
    "café",
    "50%",
]
VALUES = [
    KEY,
    f"password={TOKEN}",
    f"api_key={TOKEN}x",
    IP,
    "10.9.9.9",
    "10.0.0.6",
    "user_id=abc123",
    "ops@example.com",
    "http://10.0.0.5/health",
]
LAYERS = [
    lambda s: s,
    lambda s: s,
    lambda s: quote(s, safe=""),
    lambda s: s[0] + "\u200b" + s[1:],
    lambda s: f"\\u{ord(s[0]):04x}" + s[1:],
    lambda s: f"&#{ord(s[0])};" + s[1:],
    lambda s: chr(ord(s[0]) + 0xFEE0) + s[1:] if s[0].isalnum() else s,
]
LOOKALIKES = [
    "&lt;ID_5&gt;",
    "\\u003cID_5\\u003e",
    "%3CID_5%3E",
    "&lt;IPV4_1&gt;",
    "<IPV4_3>",
    "<ipv4_2>",
]


def random_text(rng: random.Random) -> str:
    parts = []
    for _ in range(rng.randint(1, 8)):
        if rng.random() < 0.5:
            parts.append(rng.choice(FILLER))
        else:
            parts.append(rng.choice(LAYERS)(rng.choice(VALUES)))
    return rng.choice([" ", " ", "\n", "; "]).join(parts)
