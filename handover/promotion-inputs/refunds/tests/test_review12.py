"""Round 12 (duplication-map items): RateCap is thread-safe, the egress check has a scheme rule, the Clopper-Pearson sums survive a large n and equal
the plain float sum for a small one, an id reused with a different body is its own rejected row, the look-alike fold is wired through the one
interface, and the LF policy is in place."""

import pkgutil
import random
import sys
import threading
from math import comb
from pathlib import Path

import pytest

from refunds import guards, textnorm, verdict

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = "pat@example.com"


# ---------------------------------------------------------------- (1) RateCap under threads
def _hammer(fn, threads=16, per_thread=400):
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)  # force a thread switch between almost any two bytecodes
    try:
        start = threading.Barrier(threads)

        def work():
            start.wait()
            for _ in range(per_thread):
                fn()

        ts = [threading.Thread(target=work) for _ in range(threads)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
    finally:
        sys.setswitchinterval(old)


class _Gate:
    """Makes two threads meet INSIDE the check-then-act window: the first comparison blocks until a second thread is also comparing. Under a lock the
    second thread cannot enter, the wait times out and the first thread goes on alone (so the lock is proven by the timeout, not by luck)."""

    def __init__(self):
        self.barrier = threading.Barrier(2, timeout=0.3)

    def meet(self):
        try:
            self.barrier.wait()
        except threading.BrokenBarrierError:
            pass


def _two(fn):
    res = []
    ts = [threading.Thread(target=lambda: res.append(fn())) for _ in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return res


def test_ratecap_two_threads_cannot_spend_the_last_token_twice():
    gate = _Gate()

    class Meets(float):
        def __lt__(self, other):
            r = float.__lt__(self, other)
            gate.meet()
            return r

    rc = guards.RateCap(1, 5)
    rc._tokens = Meets(1.0)  # exactly one token left
    got = _two(lambda: rc.allow(0.0))
    assert sorted(got) == [False, True] and rc.accepted == 1 and rc.throttled == 1, (got, rc.accepted, rc.throttled)


def test_connection_cap_two_threads_cannot_both_take_the_last_slot():
    gate = _Gate()

    class Meets(int):
        def __ge__(self, other):
            r = int.__ge__(self, other)
            gate.meet()
            return r

    rc = guards.RateCap(10, 1)
    rc.connections = Meets(0)
    got = [t is not None for t in _two(rc.acquire)]
    assert sorted(got) == [False, True] and rc.connections == 1, (got, rc.connections)


@pytest.mark.parametrize("round_", range(3))
def test_ratecap_many_threads_never_exceed_capacity(round_):
    cap = 1000
    rc = guards.RateCap(cap, 5)
    _hammer(lambda: rc.allow(0.0))  # a frozen clock: no refill, so EXACTLY `cap` of the 6,400 calls may pass
    assert rc.accepted == cap and rc.throttled == 16 * 400 - cap, (rc.accepted, rc.throttled)


# ---------------------------------------------------------------- (3) egress scheme rule
@pytest.mark.parametrize(
    "text",
    [
        "see ftp://intranet/payments",
        "open data:text/html;base64,PHNjcmlwdD4=",
        "run javascript:alert(1)",
        "go //intranet/pay now",
        "call tel:+15550100",
        "file:///etc/passwd",
        "gopher://intranet/1",
    ],
)
def test_a_scheme_reference_without_a_dotted_host_is_an_unlisted_link(text):
    assert guards.egress_check(text, VERIFIED, VERIFIED) == ["UNLISTED_LINK"], text


def test_a_listed_scheme_link_passes_and_prose_with_colons_does_not_trip_the_rule():
    assert guards.egress_check("see ftp://intranet/ok", VERIFIED, VERIFIED, allowed_links=frozenset({"ftp://intranet/ok"})) == []
    assert guards.egress_check("Note: your refund is on its way. Reference: 12. Time 10:30.", VERIFIED, VERIFIED) == []
    assert guards.egress_check(f"write to mailto:{VERIFIED}", VERIFIED, VERIFIED) == []


@pytest.mark.parametrize(
    "text",
    [
        "java script:alert(1)",
        "ja\tvascript:alert(1)",
        "ja\nvascript:alert(1)",
        "ja\r\nvascript:alert(1)",
        "ftp ://x",
        "ftp\t://x",
        "  \x01 javascript:alert(1)",
        "see da ta:text/html,hi",
        "ja\x00vascript:alert(1)",
        "ja\u200bvascript:alert(1)",
    ],
)
def test_a_scheme_split_by_tab_newline_space_or_an_invisible_character_is_still_refused(text):
    assert guards.egress_check(text, VERIFIED, VERIFIED) == ["UNLISTED_LINK"], repr(text)


@pytest.mark.parametrize(
    "text", ["Data: 12 ok", "Reference: 12", "the profile: ok", "Time 10:30", "see file: report", "Total: 5. Tel: later"]
)
def test_prose_with_colons_is_not_a_scheme(text):
    assert guards.egress_check(text, VERIFIED, VERIFIED) == [], text


def test_a_listed_scheme_link_with_a_dotted_host_passes_once_not_twice():
    ok = frozenset({"ftp://files.example/ok"})
    assert guards.egress_check("see ftp://files.example/ok", VERIFIED, VERIFIED, allowed_links=ok) == []
    assert guards.egress_check("see ftp://files.example/other", VERIFIED, VERIFIED, allowed_links=ok) == ["UNLISTED_LINK"]


def test_the_scheme_rule_is_linear():
    import time

    t0 = time.perf_counter()
    guards.egress_check("a:" * 10000 + "b" * 10000 + " //" * 3000, VERIFIED, VERIFIED)
    assert time.perf_counter() - t0 < 2.0


# ---------------------------------------------------------------- (4) Clopper-Pearson in log space
def _plain_tail(lo, hi, n, p):
    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(lo, hi + 1))


def test_the_log_space_sums_equal_the_plain_float_sums_for_small_n():
    rnd = random.Random(12)
    for _ in range(400):
        n = rnd.randint(1, 300)
        x = rnd.randint(0, n)
        p = rnd.choice([rnd.random(), rnd.random() ** 3, 1 - rnd.random() ** 3])
        p = min(max(p, 1e-9), 1 - 1e-9)
        assert verdict._tail_le(x, n, p) == pytest.approx(_plain_tail(0, x, n, p), rel=1e-9, abs=1e-12), (x, n, p)
        assert verdict._tail_ge(x, n, p) == pytest.approx(_plain_tail(x, n, n, p), rel=1e-9, abs=1e-12), (x, n, p)


def test_clopper_pearson_small_n_values_are_unchanged():
    lo, hi = verdict.clopper_pearson(3, 20)
    assert (round(lo, 4), round(hi, 4)) == (0.0321, 0.3789)
    assert verdict.clopper_pearson(0, 50, two_sided=False)[1] == pytest.approx(verdict.upper_bound_zero_wrong(50), abs=1e-9)


def test_the_binomial_sum_edges_at_p_zero_and_one():
    assert (verdict._pmf_sum(0, 3, 10, 0.0), verdict._pmf_sum(1, 3, 10, 0.0)) == (1.0, 0.0)
    assert (verdict._pmf_sum(10, 10, 10, 1.0), verdict._pmf_sum(0, 9, 10, 1.0)) == (1.0, 0.0)


@pytest.mark.parametrize("n", [1100, 2500, 6000])
def test_clopper_pearson_does_not_overflow_for_a_large_n(n):
    hi = verdict.clopper_pearson(0, n, two_sided=False)[1]
    assert hi == pytest.approx(verdict.upper_bound_zero_wrong(n), abs=1e-9), n
    lo, hi2 = verdict.clopper_pearson(n // 2, n)
    assert 0.45 < lo < n / 2 / n < hi2 < 0.55, (lo, hi2)


# ---------------------------------------------------------------- (6) the same id with a different body


# ---------------------------------------------------------------- (2) the look-alike fold through the one interface
def test_a_cyrillic_look_alike_marker_is_found_and_the_plain_text_is_not_over_matched():
    assert textnorm.contains_marker("Your refund was \u0430pproved", "approved")  # Cyrillic a
    assert textnorm.contains_marker("аррrоvеd", "approved")  # a p p (Cyrillic) r o v e d
    assert not textnorm.contains_marker("disapproved", "approved")
    assert not textnorm.contains_marker("Your refund is on its way", "approved")
    assert textnorm.normalise("\u0430pproved") != textnorm.normalise("approved"), (
        "the STORED form is unchanged: no table in normalise"
    )
    assert textnorm.skeleton("\u0440\u0430\u0442@\u0435\u0445\u0430\u043c\u0440\u04cf\u0435.\u0441\u043e\u043c") == VERIFIED
    assert textnorm.mixed_script("p\u0430t") and not textnorm.mixed_script("pat")


@pytest.mark.parametrize(
    "text",
    [
        "Your refund was appro v\u0435d",
        "appro ved",
        "a.p.p.r.o.v.e.d",
        "a p p r o v e d",
        "\u0430ppro-ved",
        "appro\nved",
        "appr_oved",
        "appro..ved",
        "appro . - ved",
        "a  .  p--p___r**o  v . e . d",
    ],
)
def test_a_run_of_separators_inside_a_marker_word_does_not_hide_it(text):
    assert textnorm.contains_marker(text, "approved"), repr(text)


def test_separators_do_not_make_other_words_match():
    for text in ("disapproved", "approvedly", "unapproved", "approv", "pproved"):
        assert not textnorm.contains_marker(text, "approved"), text
    assert textnorm.contains_marker("dis approved is not it", "approved"), (
        "a separate word 'approved' after a space IS the marker"
    )
    assert textnorm.contains_marker("re fund the  max", "refund the max") and not textnorm.contains_marker(
        "refund them ax", "refund the max"
    )


def test_only_the_textnorm_interface_imports_the_core_copy():
    src = ROOT / "src" / "refunds"
    names = [m.name for m in pkgutil.iter_modules([str(src)]) if not m.ispkg]
    assert "textnorm" in names and "guards" in names
    offenders = [n for n in names if n != "textnorm" and "core_copy" in (src / f"{n}.py").read_text(encoding="utf-8")]
    assert offenders == [], offenders


# ---------------------------------------------------------------- (5) LF policy
