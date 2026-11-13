"""PR H, WP0: one span rule for every place that puts known values back as placeholders.

Bug class: values replaced one after another, so the first replacement cut the second value and a piece of it stayed
readable. Main has it in the redactor's own sweep of known values and in `runmap._keep_earlier_masks`. Every test whose
name starts `test_mf_` must FAIL on main (by an assertion about readable pieces, never by a missing name) and pass on
the branch; the others pass on both. Every value here is made up and built from parts."""

from __future__ import annotations

import hashlib
import inspect

import pytest

from hadavin_sdk.approvals import channel as channel_mod
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact

A = "Qz7" + "kPQRSTmn"  # its tail is the head of B
B = "PQRSTmn" + "w4Xy9"
C = "Hh2" + "PQRSTmn"  # the same length as A, the same 7-character overlap with B
INNER = "PQRSTmn"  # nested inside A and inside B
MERGED = A + B[7:]

# (name, text, pairs of (placeholder, value)) - the rows of the rev-3 probe, one per overlap shape
ROWS = [
    ("partial, A first", "id " + A + B[7:] + " end", [("<SECRET_1>", A), ("<SECRET_2>", B)]),
    ("partial, B first", "id " + A + B[7:] + " end", [("<SECRET_2>", B), ("<SECRET_1>", A)]),
    ("equal length", "id " + C + B[7:] + " end", [("<SECRET_1>", C), ("<SECRET_2>", B)]),
    ("nested, short first", "id " + A + " end", [("<SECRET_3>", INNER), ("<SECRET_1>", A)]),
    (
        "three-chain",
        "id " + A + B[7:] + "Zr8" + " end",
        [("<SECRET_1>", A), ("<SECRET_2>", B), ("<SECRET_4>", "w4Xy9Zr8")],
    ),
    (
        "same start, equal length",
        "id " + A + " end",
        [("<SECRET_1>", A), ("<SECRET_5>", A[:-1] + "n")],
    ),
    (
        "mixed spelling domains",
        "id " + "x%3Dy" + A + " end",
        [("<SECRET_3>", "x%3Dy" + A[:3]), ("<SECRET_1>", A)],
    ),
]
IDS = [r[0] for r in ROWS]


def readable_pieces(out: str, values: list[str]) -> list[str]:
    """The first piece of 4 characters of each value that stands readable in `out`."""
    bad = []
    for v in values:
        for i in range(len(v) - 3):
            if v[i : i + 4] in out:
                bad.append(v[i : i + 4])
                break
    return bad


def restore(out: str, mapping: dict[str, str]) -> str:
    for ph, original in mapping.items():
        out = out.replace(ph, original)
    return out


def keep_earlier(view: str, pairs: list[tuple[str, str]]) -> tuple[str, dict[str, str]]:
    """`_keep_earlier_masks` through whatever signature the code under test has (main takes two arguments, the branch
    three: the map a merged placeholder is issued into)."""
    work = dict(pairs)
    if len(inspect.signature(runmap._keep_earlier_masks).parameters) == 3:
        return runmap._keep_earlier_masks(view, pairs, work), work
    return runmap._keep_earlier_masks(view, pairs), work


ROW = {name: (text, pairs) for name, text, pairs in ROWS}
# The rows main fails, found by running these tests on main (`/home/user/build/PRH-fail-before-WP0.txt`): the
# `test_mf_` tests hold only those, so each of them fails on main; the other rows are in `test_overlap_rows_hold`.
SWEEP_MF = ["partial, A first", "partial, B first", "three-chain", "mixed spelling domains"]
KEEP_MF = [
    "partial, A first",
    "partial, B first",
    "equal length",
    "nested, short first",
    "mixed spelling domains",
]
CHOKE_MF = ["partial, A first", "partial, B first"]


def check_sweep(name: str) -> None:
    text, pairs = ROW[name]
    result = redact(text, mapping=dict(pairs))
    assert readable_pieces(result.text, [v for _, v in pairs]) == [], result.text
    assert result.restore(result.text) == text


def check_keep(name: str) -> None:
    text, pairs = ROW[name]
    out, work = keep_earlier(text, pairs)
    assert readable_pieces(out, [v for _, v in pairs]) == [], out
    assert restore(out, work) == text


def check_choke(name: str, entry: str) -> None:
    text, pairs = ROW[name]
    run_map = dict(pairs)
    out = getattr(runmap, entry)(text, run_map)
    assert readable_pieces(out, [v for _, v in pairs]) == [], out
    assert restore(out, run_map) == text


@pytest.mark.parametrize("name", SWEEP_MF)
def test_mf_sweep_partial_overlap(name):
    check_sweep(name)


@pytest.mark.parametrize("name", KEEP_MF)
def test_mf_keep_earlier_masks_partial_overlap(name):
    check_keep(name)


@pytest.mark.parametrize("entry", ["redact_text", "redact_untrusted"])
@pytest.mark.parametrize("name", CHOKE_MF)
def test_mf_run_map_through_the_choke_point(name, entry):
    check_choke(name, entry)


@pytest.mark.parametrize("name", [n for n in IDS if n not in SWEEP_MF])
def test_overlap_rows_hold_in_the_sweep(name):
    check_sweep(name)


@pytest.mark.parametrize("name", [n for n in IDS if n not in KEEP_MF])
def test_overlap_rows_hold_in_keep_earlier_masks(name):
    check_keep(name)


@pytest.mark.parametrize("entry", ["redact_text", "redact_untrusted"])
@pytest.mark.parametrize("name", [n for n in IDS[:3] if n not in CHOKE_MF])
def test_overlap_rows_hold_through_the_choke_point(name, entry):
    check_choke(name, entry)


class Gen:
    """A seeded stream of made-up values (SHA-256 of seed and counter: repeatable, and no `random` module)."""

    ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    def __init__(self, seed: int) -> None:
        self.seed, self.n = seed, 0

    def below(self, k: int) -> int:
        self.n += 1
        digest = hashlib.sha256(f"{self.seed}:{self.n}".encode()).digest()
        return int.from_bytes(digest[:8], "big") % k

    def between(self, lo: int, hi: int) -> int:
        return lo + self.below(hi - lo + 1)

    def word(self, n: int) -> str:
        return "".join(self.ALPHABET[self.below(len(self.ALPHABET))] for _ in range(n))


def _pair(g: Gen, shape: str) -> tuple[str, str, str]:
    """(value one, value two, text) for one overlap shape; the text holds both values glued as they overlap."""
    a = g.word(g.between(14, 22))
    if shape == "partial":
        k = g.between(1, 12)
        b = a[-k:] + g.word(g.between(10, 16))
        return a, b, a + b[k:]
    if shape == "equal-length":
        k = g.between(1, 12)
        b = a[-k:] + g.word(len(a) - k)
        return a, b, a + b[k:]
    if shape == "nested":
        i = g.between(1, len(a) - 6)
        j = g.between(i + 5, len(a))
        return a, a[i:j], a
    b = a[: g.between(5, len(a) - 1)]  # same start
    return a, b, a


def check_generator(shape: str) -> None:
    g = Gen(790)
    cases = 0
    for _ in range(500):
        a, b, body = _pair(g, shape)
        text = "id " + body + " end"
        for pairs in (
            [("<SECRET_1>", a), ("<SECRET_2>", b)],
            [("<SECRET_2>", b), ("<SECRET_1>", a)],
        ):
            result = redact(text, mapping=dict(pairs))
            assert readable_pieces(result.text, [a, b]) == [], (shape, a, b, result.text)
            assert result.restore(result.text) == text, (shape, a, b)
            cases += 1
    assert cases == 1000


@pytest.mark.parametrize("shape", ["partial", "equal-length"])
def test_mf_span_rule_generator(shape):
    """1,000 seeded pairs per shape (overlap of 1 to 12 characters), both list orders: no piece of 4 characters of
    either value readable, and restore gives the input back. Main leaks in these two shapes."""
    check_generator(shape)


@pytest.mark.parametrize("shape", ["nested", "same-start"])
def test_span_rule_generator_shapes_main_masks(shape):
    check_generator(shape)


def test_nested_restore_exact():
    """A value nested in another: only the longer value's placeholder stands, and restore is exact (passes on main)."""
    pairs = [("<SECRET_3>", INNER), ("<SECRET_1>", A)]
    text = "id " + A + " end"
    result = redact(text, mapping=dict(pairs))
    assert "<SECRET_1>" in result.text
    assert "<SECRET_3>" not in result.text
    assert result.restore(result.text) == text


def test_mf_merged_entry_reused():
    """Two texts of one run that hold the same partially overlapping pair get the same placeholder for it."""
    pairs = [("<SECRET_1>", A), ("<SECRET_2>", B)]
    first = redact("id " + MERGED + " end", mapping=dict(pairs))
    second = redact("again " + MERGED + " done", mapping=first.mapping)
    assert readable_pieces(first.text, [A, B]) == [], first.text
    assert readable_pieces(second.text, [A, B]) == [], second.text
    holders = [ph for ph, v in second.mapping.items() if v == MERGED]
    assert len(holders) == 1, second.mapping
    assert holders[0] in first.text
    assert holders[0] in second.text


def test_merged_text_is_issued_into_the_given_map_only_when_needed():
    """No merged entry when nothing overlaps partially (passes on main)."""
    pairs = [("<SECRET_1>", A), ("<SECRET_2>", "Nn5" + "vBcDeFg")]
    text = "x " + A + " y " + "Nn5" + "vBcDeFg" + " z"
    result = redact(text, mapping=dict(pairs))
    assert result.restore(result.text) == text
    assert set(result.mapping) == {"<SECRET_1>", "<SECRET_2>"}


def test_case_790_regression():
    """The exact case 790 of the round-12 fuzz generator (seed 20261104): a `password` assignment with a markup tag in
    the key whose value holds an encoded vertical tab. Passes on main; a fix that only sorted pairs, or that
    changed the order of replacement, leaked the second part on the card path (PR H plan, section 8.1)."""
    from tests import test_k5_round12_fuzz as fuzz

    rng = fuzz.random.Random(fuzz.SEED)  # the generator the fuzz file itself uses
    names = sorted(fuzz.PRODUCERS)
    case790 = None
    for i in range(791):
        text, parts, _strict, tagged, base = fuzz._case(rng)
        pool = [n for n in names if n in {"clean", "slack"}] if tagged else names
        rng.sample(pool, 1)
        if i == 790:
            case790 = (text, parts, base)
    assert case790 is not None
    text, parts, base = case790
    frags = fuzz._fragments(parts, base)
    assert frags
    for name in ("clean", "slack"):
        out = fuzz.PRODUCERS[name](text)
        assert [f for f in frags if f in out] == [], name


def test_case_790_reduced_form_on_the_card():
    part1, part2 = "qxzjkwvyqx", "zjkwvyqxzj"
    text = "note " + "passw<i> </i>d=" + part1 + "\\U0000000b" + part2 + " end"
    out = channel_mod.clean(text)
    assert part1 not in out
    assert part2 not in out
