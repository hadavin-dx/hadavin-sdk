"""Review 10 follow-ups: egress IDN / punycode / backslash / UNC / right boundary / wider scheme list / case-folded lists, marker separator boundary,
RateCap input validation and ownership tokens (tests that already pass on the previous code, e.g. the exact-binomial and prose-is-clean ones, are regression guards for behaviour that must not change), verdict mode closed set and exact-binomial checks, ingest spec model (no body = rejected, first body acted on)."""

import math
from fractions import Fraction

import pytest

from refunds import guards, textnorm, verdict

VERIFIED = "pat@example.com"
SHOP = frozenset({"shop.example"})


def eg(text, **kw):
    return guards.egress_check(text, VERIFIED, VERIFIED, **kw)


# ---------------------------------------------------------------- egress: hosts
@pytest.mark.parametrize(
    "text",
    [
        "pay at \u4f8b\u3048.jp/pay",  # a bare Unicode (IDN) host
        "\u043f\u0440\u0438\u043c\u0435\u0440.\u0440\u0444",  # all-Cyrillic host and TLD
        "see evil.xn--p1ai",  # punycode TLD
        "see xn--e1afmkfd.xn--80akhbyknj4f",  # punycode label and TLD
        "shop.example_evil.com",  # must not read as shop.example
        "shop.exampl\u00e9.com",  # must not read as shop.example
        "shop.example-evil.com",
        "shop.example_evil",
        "shop.example1",
        "shop.example-evil",
    ],
)
def test_idn_punycode_and_continued_hosts_are_unlisted_even_with_a_shop_example_allow_list(text):
    assert eg(text, allowed_hosts=SHOP) == ["UNLISTED_LINK"], text


def test_an_allowed_host_matches_in_unicode_punycode_and_case_forms():
    assert eg("see shop.example/pay", allowed_hosts=SHOP) == []
    assert eg("see SHOP.Example", allowed_hosts=SHOP) == []
    assert eg("see 例え.jp/x", allowed_hosts=frozenset({"xn--r8jz45g.jp"})) == []
    assert eg("see xn--r8jz45g.jp", allowed_hosts=frozenset({"例え.jp"})) == []
    # an accented letter is folded to its base by the text fold, so an allow-listed accented host never matches (fails closed, documented)
    assert eg("see bücher.example", allowed_hosts=frozenset({"bücher.example"})) == ["UNLISTED_LINK"]
    assert eg("see xn--e1afmkfd.xn--80akhbyknj4f", allowed_hosts=frozenset({"xn--e1afmkfd.xn--80akhbyknj4f"})) == []
    assert eg("see shop.example/Pay", allowed_links=frozenset({"SHOP.example/pay"})) == []


@pytest.mark.parametrize(
    "text",
    [
        "go http:\\\\intranet\\x",
        "go http:/intranet",
        "go http:intranet",
        "go https:\\intranet",
        "go ws:intranet",
        "go ldaps ://intranet/x",
        "go gemini\t://intranet/x",
        "go ftp:/intranet",
        "open \\\\fileserver\\share",
        "open \\\\10.0.0.9\\c$",
    ],
)
def test_special_scheme_forms_and_unc_paths_are_refused(text):
    assert eg(text) == ["UNLISTED_LINK"], text


@pytest.mark.parametrize(
    "text",
    [
        "see blob:https://x",
        "about:blank",
        "ms-msdt:id",
        "search-ms:query=x",
        "sip:alice",
        "intent://x",
        "view-source:x",
        "ms-ms\tdt:id",
        "smb:x",
        "ldap:x",
    ],
)
def test_the_wider_scheme_list_is_refused(text):
    assert eg(text) == ["UNLISTED_LINK"], text


@pytest.mark.parametrize(
    "text",
    [
        "Thanks. Regards",
        "Time 10:30 and e.g. This",
        "Note: http: later",
        "Order 12: refund approved",
        "price 2.75 USD",
        "C:\\ no",
    ],
)
def test_prose_is_still_clean(text):
    assert eg(text) == [], text


# ---------------------------------------------------------------- marker separator boundary
@pytest.mark.parametrize(
    "marker,text",
    [("999900", "id 9999.00 x"), ("999900", "99-99-00"), ("999900", "9 99900"), ("ok!", "o.k!"), ("ab12cd", "a.b.1.2.c.d")],
)
def test_digit_and_short_markers_get_no_separator_tolerance(marker, text):
    assert not textnorm.contains_marker(text, marker), (marker, text)


def test_digit_marker_still_found_exactly_and_after_the_fold():
    assert textnorm.contains_marker("amount 999900 now", "999900")
    assert textnorm.contains_marker("amount \uff19\uff19\uff19\uff19\uff10\uff10 now", "999900")  # fullwidth digits


def test_the_documented_false_positive_set_is_pinned():
    hits = [  # (text, marker): each must match, exactly this marker
        ("ap.prove", "approve"),
        ("app-roved", "approved"),
        ("a p p r o v e", "approve"),
        ("pre-approved", "approved"),
        ("not approved", "approved"),
        ("dis approved", "approved"),
    ]
    for text, marker in hits:
        assert textnorm.contains_marker(text, marker) is True, (text, marker)
    misses = [
        ("ap.prove", "approved"),
        ("a p p r o v e", "approved"),
        ("disapproved", "approved"),
        ("approvedly", "approved"),
        ("unapproved", "approved"),
        ("reapproved", "approved"),
    ]
    for text, marker in misses:
        assert textnorm.contains_marker(text, marker) is False, (text, marker)


# ---------------------------------------------------------------- RateCap input and ownership
@pytest.mark.parametrize("args", [(0, 1), (-1, 1), (1, -1), (0.5, 1), (1, 1.5), (True, 1), ("5", 1), (None, 1)])
def test_ratecap_rejects_nonsense_limits(args):
    with pytest.raises(ValueError):
        guards.RateCap(*args)


def test_ratecap_accepts_zero_connections_and_refuses_every_connect():
    rc = guards.RateCap(5, 0)
    assert rc.acquire() is None


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), "1", None, True])
def test_a_bad_timestamp_is_refused_and_does_not_freeze_the_bucket(bad):
    rc = guards.RateCap(2, 1)
    assert rc.allow(bad) is False
    assert rc.allow(0.0) and rc.allow(0.0) and not rc.allow(0.0)  # capacity 2 at t=0
    assert rc.allow(1.0), "the bucket still refills: the bad reading was never stored"


def test_release_is_once_per_token_and_foreign_tokens_change_nothing():
    rc = guards.RateCap(5, 2)
    a, b = rc.acquire(), rc.acquire()
    assert a is not None and b is not None and rc.acquire() is None and rc.connections == 2
    assert rc.release(a) is True and rc.release(a) is False and rc.release(object()) is False
    assert rc.connections == 1, "a double release must not free someone else's slot"
    assert rc.acquire() is not None and rc.acquire() is None


# ---------------------------------------------------------------- verdict
@pytest.mark.parametrize("mode", ["Scripted", "script", "", "LIVE", None, "scripted "])
def test_a_mode_typo_is_an_error_never_green(mode):
    with pytest.raises(ValueError):
        verdict.verdict(0.0, mode)
    with pytest.raises(ValueError):
        verdict.verdict(None, mode)


def test_the_zero_wrong_bound_matches_the_exact_form_at_large_n():
    for n in (1, 10, 1000, 5000, 100000):
        # the bound p solves (1-p)^n = 0.05: check it with exact rational arithmetic on the float result
        p = Fraction(verdict.upper_bound_zero_wrong(n))
        assert abs(float((1 - p) ** n) - 0.05) < 1e-9, n


def _exact_cdf(lo, hi, n, p):
    """P(lo <= X <= hi) for Binomial(n, p) in exact integer arithmetic: p = a / d with d a power of two (a float), no rounding anywhere."""
    num, den = p.as_integer_ratio()
    total = sum(math.comb(n, i) * num**i * (den - num) ** (n - i) for i in range(lo, hi + 1))
    return Fraction(total, den**n)


@pytest.mark.parametrize("x,n", [(0, 800), (3, 800), (400, 800), (797, 800), (799, 800), (1, 1500)])
def test_clopper_pearson_bounds_hit_alpha_in_exact_arithmetic(x, n):
    lower, upper = verdict.clopper_pearson(x, n)
    if x < n:
        assert float(_exact_cdf(0, x, n, upper)) == pytest.approx(0.025, rel=1e-6, abs=1e-12), (x, n, upper)
    if x > 0:
        assert float(_exact_cdf(x, n, n, lower)) == pytest.approx(0.025, rel=1e-6, abs=1e-12), (x, n, lower)


# ---------------------------------------------------------------- ingest spec model
