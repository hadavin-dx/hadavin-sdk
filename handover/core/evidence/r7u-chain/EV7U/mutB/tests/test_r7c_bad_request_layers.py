"""Round 7C, finding E: each protective layer is tested ALONE (the r7b review: mutants M8 and M3 survived because
two layers covered each other).

M8: `RecursionError` removed from `BAD_REQUEST_ERRORS`: the deep-body tests still passed because the loader already
turned the text into a ValueError. Here a handler method raises a literal RecursionError.
M3: `loads_bounded` without its RecursionError catch: the same, because the shield caught it later. Here the loader is
called alone (tests/test_r7c_one_json_loader.py holds the loader unit test; this file pins the layer split)."""

from __future__ import annotations

from typing import Any

import pytest

from demo_only.bad_request import BAD_REQUEST_ERRORS, _shield
from lead_desk.jsonread import JsonTooDeep, loads_bounded


def test_the_shield_list_names_recursion_error_and_the_five_classic_errors() -> None:
    assert set(BAD_REQUEST_ERRORS) == {KeyError, TypeError, ValueError, AttributeError, IndexError, RecursionError}


@pytest.mark.parametrize("error", [RecursionError, KeyError, TypeError, ValueError, AttributeError, IndexError])
def test_the_shield_alone_turns_a_literal_error_into_one_bad_request(error: type[Exception]) -> None:
    class Stub:
        close_connection = False
        _answer_started = False
        sent = 0

        def _send_bad_request(self) -> None:
            self.sent += 1

    def boom(_self: Any) -> None:
        raise error("x")

    stub: Any = Stub()
    _shield(boom)(stub)
    assert stub.sent == 1 and stub.close_connection is True


def test_the_shield_does_not_hide_an_error_it_does_not_name() -> None:
    class Stub:
        close_connection = False
        _answer_started = False

        def _send_bad_request(self) -> None:
            raise AssertionError("must not answer")

    def boom(_self: Any) -> None:
        raise ZeroDivisionError

    stub: Any = Stub()
    with pytest.raises(ZeroDivisionError):
        _shield(boom)(stub)


def test_the_loader_alone_never_lets_a_recursion_error_out() -> None:
    with pytest.raises(JsonTooDeep):  # a RecursionError coming out would fail this test
        loads_bounded("[" * 100_000)
