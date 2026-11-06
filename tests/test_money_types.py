"""P4b1-a T1.1 to T1.7: the two money types (SpendMicro, BusinessMoney)."""

import itertools
from decimal import Decimal

import pytest

from hadavin_sdk.defaults import MAX_USD, MICRO_PER_USD
from hadavin_sdk.money import BusinessMoney, SpendMicro
from hadavin_sdk.store.protocol import check_usd

D = Decimal
TOP = MAX_USD * MICRO_PER_USD


class _IntSub(int):
    pass


class _DecSub(Decimal):
    pass


@pytest.mark.parametrize(
    "bad", [True, False, 1.0, "1", D(1), -1, 10**19, _IntSub(5), None, TOP + 1]
)
def test_t1_1_constructor_refuses_everything_but_an_exact_in_range_int(bad):
    with pytest.raises((ValueError, TypeError)):
        SpendMicro(bad)


def test_t1_2_bound_is_exact():
    assert SpendMicro(TOP).micro == TOP
    with pytest.raises(ValueError):
        SpendMicro(TOP + 1)
    assert SpendMicro(0).micro == 0


HOSTILE = [
    "NaN",
    "sNaN",
    "Infinity",
    "-Infinity",
    "-0",
    "-1",
    "1E+13",
    "0.0000001",
    "1." + "0" * 6 + "1",
    "1." + "0" * 28 + "1",
    "1." + "0" * 30 + "1",
    "1." + "0" * 39 + "1",
    "1." + "0" * 999 + "1",
    "1." + "0" * 1000,
    "0E-1000",
    "0E+5",
    "0",
    "0.000001",
    "999999999999.999999",
    "1000000000000",
    "1000000000000.000001",
    "12.5",
    "1E+3",
    "0E+999999999",
]


@pytest.mark.parametrize("text", HOSTILE)
def test_t1_3_from_usd_has_the_same_verdict_as_check_usd(text):
    x = D(text)
    try:
        check_usd(x, max_decimals=6)
        ok = True
    except ValueError:
        ok = False
    if ok:
        got = SpendMicro.from_usd(x)
        assert D(got.micro) == x * MICRO_PER_USD  # exact, never rounded
    else:
        with pytest.raises(ValueError):
            SpendMicro.from_usd(x)


@pytest.mark.parametrize("bad", [1, 1.5, "1", None, _DecSub("1")])
def test_t1_3_from_usd_refuses_non_decimals_and_subclasses(bad):
    with pytest.raises(ValueError):
        SpendMicro.from_usd(bad)


def test_t1_4_to_usd_has_exponent_minus_six():
    for micro in (0, 1, 999_999, 1_000_000, 123_456_789, TOP):
        usd = SpendMicro(micro).to_usd()
        assert usd.as_tuple().exponent == -6
        assert usd * MICRO_PER_USD == micro
        assert SpendMicro.from_usd(usd).micro == micro


def test_t1_5_ceil_cost_rounds_up_once():
    assert SpendMicro.ceil_cost(1, 3).micro == 1
    assert SpendMicro.ceil_cost(333_334).micro == 1
    assert SpendMicro.ceil_cost(1_000_000).micro == 1
    assert SpendMicro.ceil_cost(1_000_001).micro == 2
    assert SpendMicro.ceil_cost(0).micro == 0
    # 10,000 tiny calls: the sum of single round-ups is never below the exact total (bible R214)
    total = sum(SpendMicro.ceil_cost(7 * n % 999 + 1).micro for n in range(10_000))
    exact = sum(D(7 * n % 999 + 1) / MICRO_PER_USD for n in range(10_000))
    assert total >= exact
    for numerator, denominator in [(1, 0), (1, -3), (-1, 1), (1.0, 1), (1, True), (True, 1)]:
        with pytest.raises(ValueError):
            SpendMicro.ceil_cost(numerator, denominator)


def test_t1_6_operators():
    a, b = SpendMicro(5), SpendMicro(3)
    assert (a + b).micro == 8 and (a - b).micro == 2 and (a - a).micro == 0
    assert a > b and b < a and a >= SpendMicro(5) and b <= SpendMicro(3)
    with pytest.raises(ValueError):
        b - a
    biz = BusinessMoney(5, "USD")
    for other in (1, 1.0, D(1), biz, True, None):
        for op in (lambda x, y: x + y, lambda x, y: x - y, lambda x, y: x < y, lambda x, y: x >= y):
            with pytest.raises(TypeError):
                op(a, other)
    assert not hasattr(a, "__int__") and not hasattr(a, "__float__") and not hasattr(a, "__index__")
    with pytest.raises(TypeError):
        int(a)
    with pytest.raises(TypeError):
        float(a)
    assert a != 5 and a == SpendMicro(5)


def test_t1_7_business_money():
    for bad in (True, 1.0, "1", None, D(1)):
        with pytest.raises(ValueError):
            BusinessMoney(bad, "USD")
    for cur in ("USD\n", "usd", "US", "USDX", "", 5, None, "US1", "\nUSD"):
        with pytest.raises(ValueError):
            BusinessMoney(1, cur)
    assert (BusinessMoney(2, "EUR") + BusinessMoney(3, "EUR")).minor == 5
    assert (BusinessMoney(2, "EUR") - BusinessMoney(3, "EUR")).minor == -1
    with pytest.raises(ValueError):
        BusinessMoney(1, "EUR") + BusinessMoney(1, "USD")
    with pytest.raises(TypeError):
        BusinessMoney(1, "EUR") + 1
    with pytest.raises(TypeError):
        BusinessMoney(1, "EUR") + SpendMicro(1)
    with pytest.raises(TypeError):
        SpendMicro(1) + BusinessMoney(1, "EUR")
    # no conversion either way: the public names of both types hold nothing that converts
    names = {
        n
        for n in itertools.chain(dir(BusinessMoney(1, "USD")), dir(SpendMicro(1)))
        if not n.startswith("_")
    }
    assert names == {"minor", "currency", "micro", "from_usd", "to_usd", "ceil_cost"}
    assert not hasattr(BusinessMoney(1, "USD"), "to_usd")
