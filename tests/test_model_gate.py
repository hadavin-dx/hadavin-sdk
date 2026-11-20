"""Step F: the model gate wrapper (`guard/model_gate.py`). Invariants I1 to I11 and tests T1 to T20 of ticket F as
corrected by F-review-1.md and ORDER 006 (INTERFACE (ii)). Fake client, fake meter, list audit sink: no network."""

from __future__ import annotations

import copy
import inspect
import json
import logging
import threading
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.config import Route
from hadavin_sdk.guard import model_gate, runmap
from hadavin_sdk.guard.model_gate import BoundGate, GateRefused, ModelGate, UnmaskedInput
from hadavin_sdk.llm.fake import FakeLLM, UnknownRecording
from hadavin_sdk.llm.protocol import LLM, ProviderError, ProviderExhausted
from hadavin_sdk.models import Reply
from tests.k5_support import ScriptLLM

KEY = "AKIA" + "IOSFODNN7EXAMPLE"  # the documented AWS example key, built from parts
TOKEN = "s3cr3t" + "VALUE9xQ2"  # a fake, built from parts
IP = "10.0.0.5"
WORST = Decimal("0.25")
COST = Decimal("0.0123")
CLEAN = [{"role": "user", "content": "summarise the alert"}]


class Client:
    """A model client double: records what it was sent, returns one fixed Reply object or raises."""

    def __init__(self, log=None, raises: BaseException | None = None) -> None:
        self.log = [] if log is None else log
        self.raises, self.sent = raises, []
        self.reply = Reply(text="done", cost_usd=COST, model_id="fake-model")

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        self.log.append("call")
        self.sent.append(
            {"messages": messages, "system": system, "tools": tools, "docs": documents}
        )
        if self.raises is not None:
            raise self.raises
        return self.reply

    def text_sent(self) -> str:
        return json.dumps(self.sent, default=lambda b: b.decode("utf-8", "replace"))


class Meter:
    """INTERFACE (ii) double: the first settle of a reservation wins; every call is recorded."""

    def __init__(self, log=None, reserve_raises=None, settle_raises=None) -> None:
        self.log = [] if log is None else log
        self.reserve_raises, self.settle_raises = reserve_raises, settle_raises
        self.reserved: dict[str, tuple[str, Decimal, str | None]] = {}
        self.settles: list[tuple[str, Decimal]] = []
        self._lock = threading.Lock()

    def reserve(self, agent_id, worst_usd, *, run_id=None):
        self.log.append("reserve")
        if self.reserve_raises is not None:
            raise self.reserve_raises
        with self._lock:
            rid = f"res_{len(self.reserved) + 1}"
            self.reserved[rid] = (agent_id, worst_usd, run_id)
        return rid

    def settle(self, reservation_id, actual_usd):
        self.log.append("settle")
        with self._lock:
            self.settles.append((reservation_id, actual_usd))
        if self.settle_raises is not None:
            raise self.settle_raises
        return max(Decimal(0), actual_usd - self.reserved[reservation_id][1])

    def open(self) -> set[str]:
        return set(self.reserved) - {rid for rid, _ in self.settles}


class Sink:
    """`write_outcome` only, as the gate may use nothing else. Returns None (parked) or raises on demand."""

    def __init__(self, log=None, raises: Exception | None = None, parked: bool = False) -> None:
        self.log = [] if log is None else log
        self.raises, self.parked, self.rows = raises, parked, []

    def write_outcome(self, event):
        self.log.append("audit")
        if self.raises is not None:
            raise self.raises
        self.rows.append(event)
        return None if self.parked else event.event_id

    def codes(self) -> list[tuple[str | None, str | None]]:
        return [(e.result, e.error_code) for e in self.rows]


def worst(route, system, messages, tools, documents, output_schema) -> Decimal:
    return WORST


def build(client=None, *, meter=None, sink=None, mapping=None, worst_case=worst, log=None, **bind):
    """(bound gate, client, meter, sink) sharing one call log."""
    log = [] if log is None else log
    client = Client(log) if client is None else client
    meter = Meter(log) if meter is None else meter
    sink = Sink(log) if sink is None else sink
    for part in (client, meter, sink):
        if hasattr(part, "log"):
            part.log = log
    gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst_case)
    return gate.bind("agent-1", "run-1", mapping=mapping, **bind), client, meter, sink


def refused(bound, client, meter, sink, messages=CLEAN, documents=None, mapping=None):
    """A hostile input: UnmaskedInput, zero client calls, zero reservations, map unchanged, one refused row."""
    before = copy.deepcopy(dict(mapping)) if mapping is not None else None
    with pytest.raises(UnmaskedInput) as caught:
        bound.chat(messages, system="s", route="main", documents=documents)
    assert client.sent == [] and meter.reserved == {} and meter.settles == []
    assert sink.codes() == [("refused", "mask_refused")]
    if mapping is not None:
        assert dict(mapping) == before
    return caught.value


# --- pass path: I1, I3, I6, I8, I11 (T1, T2, T3) ------------------------------------------------------------------


def test_t1_pass_path_order_is_mask_check_reserve_call_settle_audit(monkeypatch):
    log: list[str] = []
    real = runmap.is_masked

    def check(text, mapping):
        log.append("check")
        return real(text, mapping)

    client, meter, sink = Client(log), Meter(log), Sink(log)
    gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst, mask_check=check)
    gate.bind("agent-1", "run-1").chat(CLEAN, system="s", route="main", documents=[b"a clean doc"])
    assert log == ["check", "check", "reserve", "call", "settle", "audit"]


def test_the_default_mask_check_is_runmap_is_masked():
    assert inspect.signature(ModelGate).parameters["mask_check"].default is runmap.is_masked


def test_t2_the_reply_object_is_returned_unchanged():
    bound, client, _, _ = build()
    before = client.reply.model_dump()
    reply = bound.chat(CLEAN, system="s", route="main")
    assert reply is client.reply and reply.model_dump() == before


def test_t3_one_reservation_for_the_worst_case_settled_once_with_the_real_cost():
    bound, _, meter, sink = build()
    bound.chat(CLEAN, system="s", route="main")
    assert meter.reserved == {"res_1": ("agent-1", WORST, "run-1")}  # I6: one, for worst_case(...)
    assert meter.settles == [("res_1", COST)]  # I7
    assert sink.codes() == [("ok", None)]


def test_the_client_gets_exactly_what_the_caller_passed():
    bound, client, _, _ = build()
    tools, docs, schema = [{"name": "read_logs"}], [b"doc"], {"type": "object"}
    bound.chat(CLEAN, system="sys", route="main", tools=tools, documents=docs, output_schema=schema)
    sent = client.sent[0]
    assert sent["messages"] is CLEAN and sent["tools"] is tools and sent["docs"] is docs
    assert sent["system"] == "sys"


def test_worst_case_gets_the_call_and_a_large_document_raises_the_reservation():
    """rd-1-B4: the reservation is whatever worst_case says for THIS call, documents included."""
    seen = []

    def by_size(route, system, messages, tools, documents, output_schema):
        seen.append((route, system, messages, tools, documents, output_schema))
        chars = sum(len(d) for d in documents or []) + sum(len(m["content"]) for m in messages)
        return Decimal(chars) / Decimal(1000)

    bound, _, meter, _ = build(worst_case=by_size)
    tools, schema = [{"name": "t"}], {"type": "object"}
    bound.chat(CLEAN, system="sys", route="main", documents=[b"ok line\n" * 10])
    bound.chat(
        CLEAN,
        system="sys",
        route="big",
        tools=tools,
        documents=[b"ok line\n" * 5000],
        output_schema=schema,
    )
    small, large = (meter.reserved[r][1] for r in ("res_1", "res_2"))
    assert large > small and large == Decimal(40_000 + len(CLEAN[0]["content"])) / Decimal(1000)
    assert seen[1][0] == "big" and seen[1][1] == "sys" and seen[1][2] is CLEAN
    assert seen[1][3] is tools and seen[1][5] is schema


def test_a_settle_above_the_reservation_is_passed_through():
    """cb-1-B2: the worst case is an estimate, not a bound."""
    client = Client()
    client.reply = Reply(cost_usd=WORST * 4, model_id="fake-model")
    bound, _, meter, sink = build(client)
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert meter.settles == [("res_1", WORST * 4)] and sink.codes() == [("ok", None)]


def test_positive_masked_text_passes_and_the_map_is_untouched():
    """I3 on the pass path, with a RunMap: equal map, same cache object and content (cb-1-M8)."""
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(f"alert from {IP}, key {KEY}", mapping)
    msg = runmap.redact_text(f"what happened at {IP}?", mapping)
    assert KEY not in doc and IP not in msg
    before, cache, cache_id = (
        dict(mapping),
        copy.copy(mapping.redact_cache),
        id(mapping.redact_cache),
    )
    bound, client, _, sink = build(mapping=mapping)
    bound.chat(
        [{"role": "user", "content": msg}], system="s", route="main", documents=[doc.encode()]
    )
    assert len(client.sent) == 1 and sink.codes() == [("ok", None)]
    assert dict(mapping) == before
    assert id(mapping.redact_cache) == cache_id and mapping.redact_cache == cache
    assert all(mapping.redact_cache[k] is cache[k] for k in cache)


# --- FAIL-BEFORE (T4) ---------------------------------------------------------------------------------------------


def test_t4_without_the_gate_an_unmasked_document_reaches_the_client_and_with_it_does_not():
    doc = f"alert\npassword={TOKEN}\n".encode()
    bare = Client()
    bare.chat(CLEAN, system="s", route="main", documents=[doc])  # today: the caller forgot to mask
    assert TOKEN in bare.text_sent()
    bound, client, meter, sink = build()
    refused(bound, client, meter, sink, documents=[doc])
    assert TOKEN not in client.text_sent()


# --- hostile inputs (T5 to T11): UnmaskedInput, zero calls, zero reservations, map unchanged ------------------------


def test_t5_a_secret_in_document_bytes_is_refused():
    mapping = runmap.RunMap({"<IPV4_1>": IP})
    refused(*build(mapping=mapping), documents=[b"clean", f"key {KEY}".encode()], mapping=mapping)


def test_t6_a_secret_inside_a_tool_result_user_string_is_refused():
    mapping = runmap.RunMap({"<IPV4_1>": IP})
    messages = [
        *CLEAN,
        {"role": "assistant", "content": 'tool read_logs {"name": "app"}'},
        {
            "role": "user",
            "content": f"<<TOOL RESULT call_id=c1 tool=read_logs>>\nERROR password={TOKEN}\n<<END>>",
        },
    ]
    refused(*build(mapping=mapping), messages=messages, mapping=mapping)


HIDDEN = {
    "full-width letter": "Ａ" + KEY[1:],
    "zero-width space": KEY[:2] + "\u200b" + KEY[2:],
    "backslash-u-0-0-4-1 escape": "\\u0041" + KEY[1:],
    "percent-encoding": "%41" + KEY[1:],
}


@pytest.mark.parametrize("spelling", HIDDEN.values(), ids=HIDDEN.keys())
@pytest.mark.parametrize("where", ["message", "document"])
def test_t7_a_secret_behind_a_layer_is_refused(spelling, where):
    mapping = runmap.RunMap({"<IPV4_1>": IP})
    text = f"line {spelling} end"
    if where == "message":
        refused(
            *build(mapping=mapping), messages=[{"role": "user", "content": text}], mapping=mapping
        )
    else:
        refused(*build(mapping=mapping), documents=[text.encode()], mapping=mapping)


def test_a_second_copy_of_a_value_the_map_already_holds_is_refused():
    mapping = runmap.RunMap({"<IPV4_1>": IP})
    refused(*build(mapping=mapping), documents=[f"<IPV4_1> again {IP}".encode()], mapping=mapping)


def test_t8_input_over_the_redaction_cap_is_refused():
    big = "a" * (defaults.MAX_REDACT_CHARS + 1)
    refused(*build(), messages=[{"role": "user", "content": big}])
    refused(*build(), documents=[big.encode()])


def test_a_text_nested_too_deep_is_refused():
    deep = "%41" + KEY[1:]
    for _ in range(defaults.SCRUB_MAX_LAYERS + 2):
        deep = quote(deep, safe="")
    refused(*build(), documents=[deep.encode()])


def test_t9_bytes_that_are_not_utf8_are_checked_as_the_adapters_decode_them():
    """`decode("utf-8", "replace")`, as llm/common.py: bad bytes do not hide a secret, and alone they pass."""
    refused(*build(), documents=[b"\xff\xfe key " + KEY.encode() + b" \x80"])
    bound, client, _, _ = build()
    bound.chat(CLEAN, system="s", route="main", documents=[b"\xff\xfe plain \x80 bytes"])
    assert len(client.sent) == 1


def test_t10_a_placeholder_that_is_not_in_the_map_passes():
    """Q4 as CHANGED by F-review-1.md: the judge, evals and replay have no run map."""
    for mapping in (None, {}, runmap.RunMap({"<IPV4_1>": IP})):
        bound, client, meter, _ = build(mapping=mapping)
        bound.chat(
            [{"role": "user", "content": "host <IPV4_7> and <SECRET_2> were named"}],
            system="s",
            route="main",
            documents=[b"<EMAIL_4> wrote in"],
        )
        assert len(client.sent) == 1 and len(meter.settles) == 1


@pytest.mark.parametrize(
    "content",
    [7, None, b"bytes", ["a list"], [{"type": "text", "text": "a block"}], {"text": "a dict"}],
    ids=["int", "none", "bytes", "list", "blocks", "dict"],
)
def test_t11_content_that_is_not_a_str_is_refused_not_skipped(content):
    refused(*build(), messages=[*CLEAN, {"role": "user", "content": content}])


@pytest.mark.parametrize(
    "messages",
    [[{"role": "user"}], ["not a dict"], [None], 5],
    ids=["no-content", "str", "none", "int"],
)
def test_a_message_the_check_cannot_read_is_refused(messages):
    refused(*build(), messages=messages)


def test_a_document_that_is_not_bytes_is_refused():
    refused(*build(), documents=["a str, not bytes"])
    refused(*build(), documents=[None])


def test_a_failing_or_false_mask_check_is_a_refusal_with_no_cause_and_no_context():
    def boom(text, mapping):
        raise ValueError(f"leaky {TOKEN}")

    for check in (boom, lambda text, mapping: False):
        client, meter, sink = Client(), Meter(), Sink()
        gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst, mask_check=check)
        error = refused(gate.bind("agent-1", "run-1"), client, meter, sink)
        assert error.__cause__ is None and error.__context__ is None
        assert error.args == ("mask_refused",) and error.code == "mask_refused"


def test_a_map_changed_by_another_thread_during_the_check_is_a_refusal_not_a_crash():
    from collections.abc import Mapping

    class Moving(Mapping):
        def __getitem__(self, key):
            raise KeyError(key)

        def __len__(self):
            return 1

        def __iter__(self):
            raise RuntimeError("dictionary changed size during iteration")

    refused(*build(mapping=Moving()), mapping=None)


# --- the live map (cb-1-M9, I3, I10) ------------------------------------------------------------------------------


def test_the_map_is_held_by_reference_a_value_masked_between_two_calls_is_seen_by_the_second():
    mapping = runmap.RunMap()
    bound, client, meter, sink = build(mapping=mapping)
    text = "ticket ref abc123 is open"  # not a pattern: nothing to mask yet
    bound.chat([{"role": "user", "content": text}], system="s", route="main")
    runmap.redact_untrusted("ERROR user_id=abc123 refused", mapping)  # the run learns the value
    assert "abc123" in mapping.values()
    before = dict(mapping)
    with pytest.raises(UnmaskedInput):
        bound.chat([{"role": "user", "content": text}], system="s", route="main")
    assert len(client.sent) == 1 and len(meter.reserved) == 1 and dict(mapping) == before
    assert sink.codes() == [("ok", None), ("refused", "mask_refused")]


def test_no_map_means_an_empty_map_and_the_gate_never_creates_or_writes_one():
    bound, client, _, _ = build(mapping=None)
    bound.chat(CLEAN, system="s", route="main")
    with pytest.raises(UnmaskedInput):
        bound.chat([{"role": "user", "content": f"host {IP}"}], system="s", route="main")
    with pytest.raises(UnmaskedInput):  # nothing was remembered from the refused call
        bound.chat([{"role": "user", "content": f"host {IP}"}], system="s", route="main")
    assert bound._mapping is None and len(client.sent) == 1


def test_two_bound_gates_share_only_the_client_the_meter_and_the_sink():
    client, meter, sink = Client(), Meter(), Sink()
    gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst)
    with_map = gate.bind("agent-a", "run-a", mapping={"<IPV4_1>": IP}, principal="svc:a")
    without = gate.bind("agent-b", "run-b")
    text = [{"role": "user", "content": "ref abc123"}]
    with_map._mapping["<TENANT_1>"] = "abc123"
    with pytest.raises(UnmaskedInput):
        with_map.chat(text, system="s", route="main")
    without.chat(text, system="s", route="main")  # the other gate's map is not this one's
    assert meter.reserved == {"res_1": ("agent-b", WORST, "run-b")}
    assert [(e.run_id, e.principal, e.source) for e in sink.rows] == [
        ("run-a", "svc:a", "gate"),
        ("run-b", "agent-b", "gate"),  # principal defaults to the agent id
    ]


# --- money (T12 to T15) -------------------------------------------------------------------------------------------


class SpendRefused(RuntimeError):
    """Shaped as INTERFACE (ii) says limits.SpendRefused will be (not importable yet)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (SpendRefused("daily_budget"), "daily_budget"),
        (SpendRefused("kill_switch"), "kill_switch"),
        (KeyError("agent-1"), "reserve_refused"),
        (RuntimeError(f"store down {TOKEN}"), "reserve_refused"),
        (
            SpendRefused(f"free text {TOKEN}"),
            "reserve_refused",
        ),  # not shaped like a code: never copied
    ],
    ids=["daily_budget", "kill_switch", "unknown-agent", "runtime-error", "reason-is-text"],
)
def test_t12_reserve_raises_no_client_call_and_the_same_error_comes_out(error, code):
    bound, client, meter, sink = build(meter=Meter(reserve_raises=error))
    with pytest.raises(type(error)) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value is error
    assert client.sent == [] and meter.settles == []
    assert sink.codes() == [("refused", code)]
    assert not isinstance(error, ProviderError | GateRefused)


def test_worst_case_raising_is_a_reserve_refusal_too():
    def cannot(*args):
        raise LookupError("no such route")

    bound, client, meter, sink = build(worst_case=cannot)
    with pytest.raises(LookupError):
        bound.chat(CLEAN, system="s", route="nope")
    assert (
        client.sent == []
        and meter.reserved == {}
        and sink.codes() == [("refused", "reserve_refused")]
    )


@pytest.mark.parametrize(
    ("error", "settled", "code"),
    [
        (ProviderError("bad key"), Decimal(0), "provider_error"),  # refused before any work
        (ProviderExhausted("throttled"), WORST, "provider_exhausted"),
        (ValueError("a billed reply that did not parse"), WORST, "call_failed"),
        (TimeoutError(), WORST, "call_failed"),
    ],
    ids=["provider-error", "provider-exhausted", "value-error", "timeout"],
)
def test_t13_the_client_raises_settle_once_and_the_same_error_comes_out(error, settled, code):
    bound, client, meter, sink = build(Client(raises=error))
    with pytest.raises(type(error)) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value is error
    assert meter.settles == [("res_1", settled)] and len(client.sent) == 1
    assert sink.codes() == [("failed", code)]


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit(1)], ids=["interrupt", "exit"])
def test_t14_a_base_exception_is_not_settled_the_worst_case_stays_booked(error):
    """INTERFACE (ii) rule 4: cost unknown, the store's sweep closes the reservation."""
    bound, _, meter, sink = build(Client(raises=error))
    with pytest.raises(type(error)) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value is error
    assert meter.settles == [] and meter.open() == {"res_1"}
    assert sink.codes() == [("failed", "call_interrupted")]


def test_settle_raising_after_a_paid_call_still_returns_the_reply():
    meter = Meter(settle_raises=RuntimeError(f"store down {TOKEN}"))
    bound, client, _, sink = build(meter=meter)
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert (
        meter.log.count("reserve") == 1 and len(meter.settles) == 1
    )  # no second reserve, no retry
    assert sink.codes() == [("failed", "settle_failed")]


def test_settle_raising_after_a_failed_call_does_not_hide_the_clients_error():
    error = ProviderExhausted("throttled")
    meter = Meter(settle_raises=RuntimeError("store down"))
    bound, _, _, sink = build(Client(raises=error), meter=meter)
    with pytest.raises(ProviderExhausted) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value is error and sink.codes() == [("failed", "settle_failed")]


class Blocked(Client):
    """Holds every call until `release` is set."""

    def __init__(self) -> None:
        super().__init__()
        self.entered, self.release = threading.Event(), threading.Event()

    def chat(self, messages, **kwargs):
        self.entered.set()
        assert self.release.wait(10)
        return super().chat(messages, **kwargs)


def test_a_blocked_client_holds_the_reservation_and_it_is_settled_once_on_release():
    """rd-1-M3: the gate cannot see an abandoned call; until its own call returns the reservation is open."""
    client = Blocked()
    bound, _, meter, sink = build(client)
    out = []
    thread = threading.Thread(
        target=lambda: out.append(bound.chat(CLEAN, system="s", route="main")), daemon=True
    )
    thread.start()
    assert client.entered.wait(10)
    assert meter.open() == {"res_1"} and meter.settles == [] and sink.rows == []
    client.release.set()
    thread.join(10)
    assert not thread.is_alive() and out == [client.reply]
    assert meter.settles == [("res_1", COST)] and meter.open() == set()


def test_t15_one_bound_gate_from_8_threads_every_reservation_settled_exactly_once():
    client = Blocked()
    bound, _, meter, sink = build(client)
    barrier, errors = threading.Barrier(8), []

    def work(i: int) -> None:
        try:
            barrier.wait(10)
            for _ in range(5):
                bound.chat([{"role": "user", "content": f"question {i}"}], system="s", route="main")
        except BaseException as exc:  # noqa: BLE001 - reported below
            errors.append(type(exc).__name__)

    threads = [threading.Thread(target=work, args=(i,), daemon=True) for i in range(8)]
    for t in threads:
        t.start()
    client.release.set()
    for t in threads:
        t.join(30)
    assert errors == [] and not any(t.is_alive() for t in threads)
    assert len(meter.reserved) == 40 and meter.open() == set()
    assert sorted(rid for rid, _ in meter.settles) == sorted(meter.reserved)  # each exactly once
    assert sink.codes() == [("ok", None)] * 40


# --- audit (T16 to T18) -------------------------------------------------------------------------------------------


def test_t16_a_parked_audit_row_does_not_raise():
    bound, client, meter, _ = build(sink=Sink(parked=True))
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert len(meter.settles) == 1


def test_t17_a_raising_audit_sink_never_loses_the_reply_or_the_settle():
    bound, client, meter, _ = build(sink=Sink(raises=RuntimeError("audit down")))
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert meter.settles == [("res_1", COST)]


def test_a_raising_audit_sink_does_not_change_a_refusal_or_an_error():
    sink = Sink(raises=RuntimeError("audit down"))
    bound, client, meter, _ = build(sink=sink)
    with pytest.raises(UnmaskedInput) as caught:
        bound.chat([{"role": "user", "content": f"key {KEY}"}], system="s", route="main")
    assert caught.value.__context__ is None and client.sent == []
    error = ProviderExhausted("throttled")
    bound, _, meter, _ = build(Client(raises=error), sink=Sink(raises=RuntimeError("audit down")))
    with pytest.raises(ProviderExhausted):
        bound.chat(CLEAN, system="s", route="main")
    assert meter.settles == [("res_1", WORST)]


def test_audit_may_be_none_on_every_path():
    for client, meter_kw, expect in [
        (Client(), {}, None),
        (Client(raises=ProviderError("x")), {}, ProviderError),
        (Client(), {"reserve_raises": SpendRefused("daily_budget")}, SpendRefused),
        (Client(), {"settle_raises": RuntimeError("x")}, None),
    ]:
        gate = ModelGate(client, meter=Meter(**meter_kw), audit=None, worst_case=worst)
        bound = gate.bind("agent-1", "run-1")
        if expect is None:
            assert bound.chat(CLEAN, system="s", route="main") is client.reply
        else:
            with pytest.raises(expect):
                bound.chat(CLEAN, system="s", route="main")
    with pytest.raises(UnmaskedInput):
        bound.chat([{"role": "user", "content": f"key {KEY}"}], system="s", route="main")


def test_the_audit_row_has_the_agreed_fields_and_nothing_else():
    bound, _, _, sink = build(principal="svc:ops", source="replay")
    bound.chat(CLEAN, system="s", route="main")
    row = sink.rows[0]
    assert (row.run_id, row.domain, row.operation, row.principal, row.source, row.result) == (
        "run-1",
        "llm",
        "chat",
        "svc:ops",
        "replay",
        "ok",
    )
    assert row.object_ref is None and row.inputs_hash is None and row.decision is None
    assert row.rule_id is None and row.error_code is None


def test_t18_no_secret_in_any_audit_row_exception_or_log_record(caplog):
    caplog.set_level(logging.DEBUG)
    captured: list[str] = []
    sink = Sink()
    secret_error = RuntimeError(f"upstream said {TOKEN}")
    cases = [
        (Client(), Meter(), [f"key {KEY} password={TOKEN}".encode()]),  # T5's secret
        (Client(), Meter(reserve_raises=SpendRefused(f"text {TOKEN}")), None),
        (Client(raises=secret_error), Meter(), None),
        (Client(), Meter(settle_raises=secret_error), None),
    ]
    for client, meter, documents in cases:
        gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst)
        bound = gate.bind("agent-1", "run-1", mapping=runmap.RunMap())
        try:
            bound.chat(CLEAN, system="s", route="main", documents=documents)
        except GateRefused as exc:  # the gate's own exception: nothing of the input may be in it
            captured += [
                repr(exc),
                str(exc),
                repr(exc.args),
                repr(exc.__cause__),
                repr(exc.__context__),
            ]
            assert exc.__cause__ is None and exc.__context__ is None
        except (SpendRefused, RuntimeError):
            pass  # the meter's and the client's own errors are re-raised unchanged: theirs, not the gate's
    captured += [row.model_dump_json() for row in sink.rows]
    captured += [record.getMessage() for record in caplog.records]
    assert len(sink.rows) == 4 and sink.codes() == [
        ("refused", "mask_refused"),
        ("refused", "reserve_refused"),
        ("failed", "call_failed"),
        ("failed", "settle_failed"),
    ]
    assert caplog.records == []  # the module has no logger
    blob = "\n".join(captured)
    for secret in (KEY, TOKEN, "upstream said", CLEAN[0]["content"]):
        assert secret not in blob


def test_i9_the_module_has_no_logger_no_exception_text_and_no_module_state():
    source = Path(model_gate.__file__).read_text(encoding="utf-8")
    code = "\n".join(line.split("#")[0] for line in source.split('"""')[2].splitlines())
    for banned in (
        "logging",
        "getLogger",
        "print(",
        "str(exc",
        "repr(exc",
        "__cause__",
        "exc.args",
    ):
        assert banned not in code, banned
    for banned in ("ContextVar", "threading.local", "global "):
        assert banned not in source, banned
    mutable = {
        name
        for name, value in vars(model_gate).items()
        if not name.startswith("__") and isinstance(value, dict | list | set)
    }
    assert mutable == set()  # I10: no module-level state


# --- structure (T19, T20) -----------------------------------------------------------------------------------------


def test_t19_an_unbound_gate_has_no_chat_and_a_bound_one_has_the_protocol_signature():
    gate = ModelGate(Client(), meter=Meter(), audit=None, worst_case=worst)
    assert not hasattr(gate, "chat")
    bound = gate.bind("agent-1", "run-1")
    assert isinstance(bound, BoundGate)
    assert inspect.signature(BoundGate.chat) == inspect.signature(LLM.chat)
    assert inspect.signature(FakeLLM.chat) == inspect.signature(BoundGate.chat)


def test_bind_has_the_published_signature():
    params = inspect.signature(ModelGate.bind).parameters
    assert list(params) == ["self", "agent_id", "run_id", "mapping", "principal", "source"]
    assert [params[n].default for n in ("mapping", "principal", "source")] == [None, None, "gate"]
    assert all(
        params[n].kind is inspect.Parameter.KEYWORD_ONLY for n in ("mapping", "principal", "source")
    )


def test_a_gate_is_never_wrapped_twice():
    gate = ModelGate(Client(), meter=Meter(), audit=None, worst_case=worst)
    for inner in (gate, gate.bind("agent-1", "run-1")):
        with pytest.raises(TypeError):
            ModelGate(inner, meter=Meter(), audit=None, worst_case=worst)


def test_t20_system_and_tools_are_not_checked():
    """I4, a documented limit: operator text is not the gate's to check."""
    bound, client, _, sink = build()
    tools = [{"name": "t", "description": f"use password={TOKEN}"}]
    bound.chat(CLEAN, system=f"operator key {KEY}", route="main", tools=tools)
    assert len(client.sent) == 1 and sink.codes() == [("ok", None)]


def test_the_exceptions_carry_a_stable_code_and_are_not_provider_errors():
    assert issubclass(UnmaskedInput, GateRefused) and issubclass(GateRefused, RuntimeError)
    assert not issubclass(GateRefused, ProviderError)
    assert GateRefused().code == "gate_refused" and UnmaskedInput().code == "mask_refused"
    assert UnmaskedInput().args == ("mask_refused",)


# --- existing doubles: the gate in front of ScriptLLM and FakeLLM -------------------------------------------------


def test_the_gate_in_front_of_script_llm_passes_masked_steps_and_stops_an_unmasked_one():
    llm = ScriptLLM([{"tool": "app"}, {"noaction": True}])
    mapping = runmap.RunMap()
    meter, sink = Meter(), Sink()
    bound = ModelGate(llm, meter=meter, audit=sink, worst_case=worst).bind(
        "agent-1", "run-1", mapping=mapping
    )
    doc = runmap.redact_untrusted(f"alert at {IP}", mapping).encode()
    first = bound.chat(CLEAN, system="s", route="main", documents=[doc])
    assert first.tool_calls[0].name == "read_logs"
    raw = [*CLEAN, {"role": "user", "content": f"ERROR upstream 10.9.9.9 password={TOKEN}"}]
    with pytest.raises(UnmaskedInput):
        bound.chat(raw, system="s", route="main", documents=[doc])
    assert len(llm.sent) == 1 and TOKEN not in llm.everything_sent()
    assert len(llm.script) == 1  # the refused step was not played


def test_the_gate_in_front_of_fake_llm_settles_the_worst_case_when_the_recording_is_missing(
    tmp_path,
):
    routes = {
        "main": Route(
            model_id="fake-model",
            input_usd_per_mtok=Decimal(1),
            output_usd_per_mtok=Decimal(1),
            max_tokens=100,
        )
    }
    llm = FakeLLM(tmp_path, routes)
    meter, sink = Meter(), Sink()
    bound = ModelGate(llm, meter=meter, audit=sink, worst_case=worst).bind("agent-1", "run-1")
    with pytest.raises(UnknownRecording):
        bound.chat(CLEAN, system="s", route="main", documents=[b"a clean doc"])
    assert len(llm.calls) == 1 and meter.settles == [("res_1", WORST)]
    assert sink.codes() == [("failed", "call_failed")]


# --- no false refusal with real producer output (finding cb-1-B1, escalation E2) ----------------------------------
# These build the strings the real producers build and put them through the gate with the run's live map.
# The gate is NOT weakened for them: a strict xfail is the report of what E2 has to decide.

DOCUMENT = f"alert: checkout failing, session ref abc123, upstream {IP}, owner ops@example.com"


def _tool_round(mapping, call_id, name, inputs, result):
    """One tool round as runtime/agent_loop.py lines 570-581 compose it: inputs masked leaf by leaf with
    `redact_value`, shown as sorted JSON; the result masked with `redact_untrusted`."""
    shown = json.dumps(
        runmap.redact_value(inputs, mapping), sort_keys=True, default=str, ensure_ascii=False
    )
    out = runmap.redact_untrusted(result, mapping)
    return [
        {"role": "assistant", "content": f"tool {name} {shown}"},
        {
            "role": "user",
            "content": f"<<TOOL RESULT call_id={call_id} tool={name}>>\n{out}\n<<END>>",
        },
    ]


def _through_the_gate(mapping, messages, document):
    bound, client, meter, _ = build(mapping=mapping)
    before = dict(mapping)
    bound.chat(messages, system="s", route="main", documents=[document.encode()])
    assert len(client.sent) == 1 and len(meter.settles) == 1 and dict(mapping) == before


def test_no_false_refusal_a_document_masked_with_redact_untrusted_passes():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(DOCUMENT + " <IPV4_7> ＜IPV4＿2＞", mapping)
    assert IP not in doc and "ops@example.com" not in doc
    _through_the_gate(mapping, CLEAN, doc)


def test_no_false_refusal_a_tool_round_with_plain_inputs_passes():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(DOCUMENT, mapping)
    step = _tool_round(
        mapping, "c1", "read_logs", {"name": "app", "host": IP}, f"ERROR upstream {IP}"
    )
    _through_the_gate(mapping, [*CLEAN, *step], doc)


def test_no_false_refusal_a_second_tool_result_with_a_new_value_passes():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(DOCUMENT, mapping)
    one = _tool_round(mapping, "c1", "read_logs", {"name": "app"}, f"ERROR upstream {IP}")
    two = _tool_round(mapping, "c2", "read_logs", {"name": "db"}, "ERROR peer 10.9.9.9 refused")
    assert "10.9.9.9" in mapping.values()  # the map grew, with a value that occurs nowhere earlier
    _through_the_gate(mapping, [*CLEAN, *one, *two], doc)


@pytest.mark.xfail(
    strict=True,
    reason="E2 / cb-1-B1 (a): tool inputs are masked leaf by leaf (redact_value) and sent as composed JSON; "
    '`"user_id": "abc123"` is no pattern as a leaf and is one once composed, so the gate refuses the step',
)
def test_no_false_refusal_tool_inputs_masked_per_leaf_then_composed_as_json():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted("alert: checkout failing", mapping)
    step = _tool_round(
        mapping, "c1", "read_logs", {"name": "app", "user_id": "abc123"}, "ERROR upstream refused"
    )
    _through_the_gate(mapping, [*CLEAN, *step], doc)


@pytest.mark.xfail(
    strict=True,
    reason="E2 / cb-1-B1 (b): a later tool result grows the run map with a value that also occurs in the "
    "document masked earlier with the smaller map; the document is re-sent unchanged and is now unmasked",
)
def test_no_false_refusal_a_later_tool_result_grows_the_map_with_a_value_the_document_holds():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(DOCUMENT, mapping)
    assert "abc123" in doc  # not a pattern in the document: left as written
    one = _tool_round(mapping, "c1", "read_logs", {"name": "app"}, f"ERROR upstream {IP}")
    _through_the_gate(mapping, [*CLEAN, *one], doc)  # step 2 of the run passes
    two = _tool_round(mapping, "c2", "read_logs", {"name": "db"}, "ERROR user_id=abc123 refused")
    assert "abc123" in mapping.values()  # the second tool result grew the map
    _through_the_gate(mapping, [*CLEAN, *one, *two], doc)  # step 3 re-sends the same document
