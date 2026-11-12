"""One seeded random generator for the tests of the hidden-item guards (a test corpus that can be reproduced exactly; never a
secret). The ONE place that carries the allowance for the rule S311 in these tests."""

import random


def rng(seed: int) -> random.Random:
    return random.Random(seed)  # noqa: S311 - a seeded test corpus, reproducible by its seed, not a secret
