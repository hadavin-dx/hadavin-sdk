# ruff: noqa: F811 - the fixtures `store` and `world` are imported from the live-path test
"""P1 (D-config-and-mark-rereview-1): mark to gate. core-c's guard/model_gate.py (which settles a call marked
`refused_before_response` at 0) is not in this tree, so this pins core-b's side of the contract through the live
loop: a router's 429 exhausted through the real OpenAICompatLLM must carry no mark, and the loop (a provider error
never settles) leaves the reservation booked at the worst case in the day counter. The control: an exhausted call
that IS marked (every attempt never sent) is also not settled by the loop itself; settling it at 0 is the gate's job.
"""

from __future__ import annotations

import urllib.error

from hadavin_sdk.llm import openai_compat
from hadavin_sdk.llm.protocol import ProviderExhausted
from hadavin_sdk.models import RunState
from tests.k5_support import handle
from tests.test_live_path_reserve_settle import (  # noqa: F401 - fixtures
    ROUTES,
    StubLLM,
    _day,
    _worst,
    store,
    world,
)
from tests.test_refused_before_response import ROUTE


def _http(code):
    return urllib.error.HTTPError("https://router.example/v1", code, "slow", {}, None)


class RouterLLM(StubLLM):
    """The real openai_compat kind over a scripted transport that answers 429 every time; the loop's reservation
    and pricing come from StubLLM's bookkeeping."""

    def __init__(self, monkeypatch, script):
        super().__init__()
        self.script, self.real = list(script), None

        def post(url, body, headers, timeout_s):
            item = self.script.pop(0)
            raise item

        monkeypatch.setattr(openai_compat, "post_json", post)
        self.real = openai_compat.OpenAICompatLLM(
            "https://router.example/v1",
            None,
            {"default": ROUTE},
            1.0,
            3,
            sleep=lambda s: None,
        )
        self.caught: BaseException | None = None

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        super().chat(
            messages, system=system, route=route, tools=tools, documents=documents
        )  # records
        try:
            return self.real.chat(messages, system=system, route=route, tools=tools)
        except ProviderExhausted as exc:
            self.caught = exc
            raise


def test_a_router_429_leaves_the_reservation_at_the_worst_case(world, store, monkeypatch):
    llm = RouterLLM(monkeypatch, [_http(429)] * 3)
    rt, spy = world(llm)
    run = handle(rt)
    assert run.state == RunState.NEEDS_PERSON
    assert isinstance(llm.caught, ProviderExhausted)
    assert llm.caught.refused_before_response is False  # the gate would settle a True at 0
    assert len(spy.reserves) == 1 and spy.settles == []
    assert _day(store) == spy.reserves[0][1] == _worst(llm, rt)  # worst case, not 0


def test_a_marked_exhaustion_is_the_gates_to_settle_not_the_loops(world, store, monkeypatch):
    refused = urllib.error.URLError(ConnectionRefusedError(111, "refused"))
    llm = RouterLLM(monkeypatch, [refused] * 3)
    rt, spy = world(llm)
    handle(rt)
    assert llm.caught.refused_before_response is True
    assert spy.settles == []
    assert _day(store) == _worst(llm, rt)
