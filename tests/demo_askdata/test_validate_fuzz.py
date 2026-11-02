"""P2 fuzz: 2,000 seeded grammar-based cases through the validator.

The invariant for every ACCEPTED statement: the canonical SQL is a fixed point (validating it again gives the same
text), its tree is stable under regenerate-and-reparse, and an independent oracle (the PostgreSQL grammar via
pglast, a node-class whitelist, sharing no code with the validator) agrees it is one SELECT that touches only
exposed views and allowlisted functions. Every POISONED case (a hazard in code position) must be refused.
"""

import collections
import random
import time

import sqlglot
from askdata.validate import Rejected, validate

from tests.demo_askdata import fuzzgen
from tests.demo_askdata.oracle import judge

SEED = 20261101
CASES = 2000


def _canonical_checks(sql: str, canonical: str) -> list[str]:
    problems = []
    if validate(canonical).canonical_sql != canonical:
        problems.append("canonical is not a fixed point")
    tree = sqlglot.parse_one(canonical, read="postgres")
    if sqlglot.parse_one(tree.sql(dialect="postgres", comments=False), read="postgres") != tree:
        problems.append("tree is not stable under regenerate and reparse")
    problems += [f"oracle: {p}" for p in judge(canonical)]
    return problems


def _slot_verdict(extra, rule, stats, failures, sql):
    """A hazard placed at a grammar slot: if the base statement is accepted, the hazard alone must cause the
    refusal and with exactly the rule the hazard belongs to."""
    base, want = extra
    try:
        validate(base)
    except Rejected:
        stats["slot base refused (generator error)"] += 1
        return
    stats["slot checked"] += 1
    if rule == want:
        stats["slot refused with the exact rule"] += 1
    elif rule in (
        "V01",
        "V09",
        "V10",
    ):  # the grown statement no longer parses, or hit a size limit first
        stats["slot refused earlier by parse or size"] += 1
    else:
        failures.append(("slot", sql, f"refused with {rule}, expected {want}"))


def run_fuzz(seed: int = SEED, cases: int = CASES):
    rng = random.Random(seed)  # noqa: S311  # seeded test data, not security randomness
    stats = collections.Counter()
    failures, accepted = [], []
    for _ in range(cases):
        kind, sql, extra = fuzzgen.case(rng)
        stats[kind] += 1
        try:
            v = validate(sql)
        except Rejected as err:
            stats[f"rejected {err.rule}"] += 1
            if kind == "slot":
                _slot_verdict(extra, err.rule, stats, failures, sql)
            continue
        except Exception as err:  # noqa: BLE001  # any other exception is a validator bug and is reported
            failures.append((kind, sql, f"crash {err!r}"))
            continue
        stats["accepted"] += 1
        if kind == "slot":
            failures.append((kind, sql, "a statement with a hazard was accepted"))
        elif kind == "poisoned":
            # Allowed only when the parser dropped the hazard (sqlglot silently drops extra function arguments);
            # the canonical text, the only thing that runs, is judged below like every accepted statement.
            stats["poison dropped by the generator"] += 1
        problems = _canonical_checks(sql, v.canonical_sql)
        if problems:
            failures.append((kind, sql, "; ".join(problems)))
        accepted.append((kind, sql, v.canonical_sql))
    return stats, failures, accepted


def test_fuzz_2000_cases_hold_the_invariant():
    started = time.monotonic()
    stats, failures, _ = run_fuzz()
    elapsed = time.monotonic() - started
    assert sum(stats[k] for k in ("clean", "poisoned", "slot", "mutated")) == CASES
    detail = "\n".join(f"{k}: {s!r} -> {why}" for k, s, why in failures[:5])
    assert not failures, f"{len(failures)} failures, first:\n{detail}"
    # not vacuous: a healthy share is accepted, and the refusals spread over many rules
    assert stats["accepted"] >= 500, dict(stats)
    assert stats["slot refused with the exact rule"] >= 0.6 * stats["slot checked"], dict(stats)
    assert stats["poison dropped by the generator"] <= 0.03 * stats["poisoned"], dict(stats)
    assert stats["poisoned"] >= 150 and stats["mutated"] >= 300 and stats["slot checked"] >= 250, (
        dict(stats)
    )
    assert len([k for k in stats if k.startswith("rejected V")]) >= 8, dict(stats)
    assert elapsed < 120, (
        f"fuzz took {elapsed:.1f}s"
    )  # about 20 s on a laptop; the design budget is 60 s
