"""Step F: the model gate wrapper (`guard/model_gate.py`). Invariants I1 to I11 and tests T1 to T20 of ticket F as
corrected by F-review-1.md, ORDER 006 (INTERFACE (ii)) and ORDER 007 (the mask step ENFORCES the caller's run map:
known values are replaced, nothing is refused because a pattern matched). Fake client, fake meter, list audit sink."""

from __future__ import annotations

import contextlib
import copy
import inspect
import json
import logging
import threading
from decimal import Decimal
from pathlib import Path

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


def test_t1_pass_path_order_is_enforce_reserve_call_settle_audit():
    log: list[str] = []

    def enforce(text, mapping):
        log.append("enforce")
        return runmap.enforce_map(text, mapping)

    def worst_logged(*args):
        log.append("worst_case")
        return WORST

    client, meter, sink = Client(log), Meter(log), Sink(log)
    gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst_logged, enforce=enforce)
    bound = gate.bind("agent-1", "run-1", mapping={})
    bound.chat(CLEAN, system="s", route="main", documents=[b"a clean doc"])
    assert log == ["enforce", "enforce", "worst_case", "reserve", "call", "settle", "audit"]


def test_the_default_enforce_step_is_runmap_enforce_map():
    assert inspect.signature(ModelGate).parameters["enforce"].default is runmap.enforce_map


def test_t2_the_reply_object_is_returned_unchanged():
    bound, client, _, _ = build()
    before = client.reply.model_dump()
    reply = bound.chat(CLEAN, system="s", route="main")
    assert reply is client.reply and reply.model_dump() == before


def test_t3_one_reservation_for_the_worst_case_settled_once_with_the_real_cost():
    bound, _, meter, sink = build()
    bound.chat(CLEAN, system="s", route="main")
    assert meter.reserved == {"res_1": ("agent-1", WORST, "run-1")}, (
        "one reservation for worst_case"
    )
    assert meter.settles == [("res_1", COST)], "settle on success with the real cost"
    assert sink.codes() == [("ok", None)]


@pytest.mark.parametrize("mapping", [None, {}, {"<IPV4_1>": IP}], ids=["no-map", "empty", "map"])
def test_when_nothing_in_the_map_occurs_raw_the_client_gets_the_callers_own_objects(mapping):
    """Byte-identical: the same message dicts and the same document bytes, in new lists."""
    bound, client, _, _ = build(mapping=mapping)
    tools, schema = [{"name": "read_logs"}], {"type": "object"}
    messages = [*CLEAN, {"role": "assistant", "content": "host <IPV4_1> and <IPV4_7>"}]
    docs = [b"a clean doc", b"\xff\xfe not utf-8 \x80"]
    bound.chat(
        messages, system="sys", route="main", tools=tools, documents=docs, output_schema=schema
    )
    sent = client.sent[0]
    assert sent["messages"] == messages and all(
        a is b for a, b in zip(sent["messages"], messages, strict=True)
    )
    assert sent["docs"] == docs and all(a is b for a, b in zip(sent["docs"], docs, strict=True))
    assert sent["tools"] is tools and sent["system"] == "sys"


def test_no_documents_stays_none():
    bound, client, _, _ = build(mapping={"<IPV4_1>": IP})
    bound.chat(CLEAN, system="s", route="main")
    assert client.sent[0]["docs"] is None


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
    assert seen[1][0] == "big" and seen[1][1] == "sys" and seen[1][2] == CLEAN
    assert seen[1][3] is tools and seen[1][5] is schema


def test_worst_case_is_computed_on_the_enforced_copies():
    seen = []

    def spy(route, system, messages, tools, documents, output_schema):
        seen.append(json.dumps(messages) + b"".join(documents).decode())
        return WORST

    bound, _, _, _ = build(worst_case=spy, mapping={"<SECRET_1>": TOKEN})
    bound.chat(
        [{"role": "user", "content": f"token {TOKEN}"}],
        system="s",
        route="main",
        documents=[TOKEN.encode()],
    )
    assert TOKEN not in seen[0] and seen[0].count("<SECRET_1>") == 2


def test_a_settle_above_the_reservation_is_passed_through():
    """cb-1-B2: the worst case is an estimate, not a bound."""
    client = Client()
    client.reply = Reply(cost_usd=WORST * 4, model_id="fake-model")
    bound, _, meter, sink = build(client)
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert meter.settles == [("res_1", WORST * 4)] and sink.codes() == [("ok", None)]


def test_positive_masked_text_passes_unchanged_and_the_map_is_untouched():
    """I3 on the pass path, with a RunMap: equal map, same cache object and content (cb-1-M8)."""
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(f"alert from {IP}, key {KEY}", mapping).encode()
    msg = {"role": "user", "content": runmap.redact_text(f"what happened at {IP}?", mapping)}
    before, cache, cache_id = (
        dict(mapping),
        copy.copy(mapping.redact_cache),
        id(mapping.redact_cache),
    )
    bound, client, _, sink = build(mapping=mapping)
    bound.chat([msg], system="s", route="main", documents=[doc])
    assert client.sent[0]["messages"][0] is msg and client.sent[0]["docs"][0] is doc
    assert sink.codes() == [("ok", None)]
    assert dict(mapping) == before
    assert id(mapping.redact_cache) == cache_id and mapping.redact_cache == cache
    assert all(mapping.redact_cache[k] is cache[k] for k in cache)


# --- FAIL-BEFORE (T4) ---------------------------------------------------------------------------------------------


def test_t4_without_the_gate_a_known_value_the_caller_forgot_to_mask_reaches_the_client():
    mapping = runmap.RunMap()
    runmap.redact_untrusted(f"password={TOKEN}", mapping)  # the run knows the value
    doc = f"alert\ntoken {TOKEN} seen\n".encode()  # ... and one producer forgot to mask this text
    bare = Client()
    bare.chat(CLEAN, system="s", route="main", documents=[doc])  # today
    assert TOKEN in bare.text_sent()
    bound, client, _, _ = build(mapping=mapping)
    bound.chat(CLEAN, system="s", route="main", documents=[doc])
    assert TOKEN not in client.text_sent(), "a known original was sent"
    assert client.sent[0]["docs"] == [b"alert\ntoken <SECRET_1> seen\n"]


# --- the enforce step (T5 to T11 as reworked by ORDER 007) --------------------------------------------------------


def known() -> runmap.RunMap:
    mapping = runmap.RunMap()
    runmap.redact_untrusted(
        f"ERROR user_id=abc123 at {IP} password={TOKEN} peer 10.0.0.50", mapping
    )
    return mapping


def test_t5_a_raw_value_that_is_in_the_map_is_replaced_in_document_bytes_never_sent():
    mapping = known()
    before = dict(mapping)
    bound, client, _, sink = build(mapping=mapping)
    docs = [b"clean", f"key {TOKEN} from {IP}".encode()]
    bound.chat(CLEAN, system="s", route="main", documents=docs)
    assert client.sent[0]["docs"] == [b"clean", b"key <SECRET_1> from <IPV4_1>"], (
        "known originals replaced"
    )
    assert client.sent[0]["docs"][0] is docs[0]
    assert TOKEN not in client.text_sent() and IP not in client.text_sent()
    assert dict(mapping) == before and sink.codes() == [("ok", None)]


def test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job():
    """ORDER 007: the gate runs no pattern. This is the stated limit, pinned."""
    mapping = known()
    doc = f"key {KEY} peer 10.9.9.9 password=hunter2".encode()
    bound, client, _, sink = build(mapping=mapping)
    bound.chat(CLEAN, system="s", route="main", documents=[doc])
    assert client.sent[0]["docs"][0] is doc and sink.codes() == [("ok", None)]
    assert dict(mapping) == dict(known())  # and nothing was learned: the gate never writes a map


def test_t6_a_known_value_inside_a_tool_result_user_string_is_replaced():
    mapping = known()
    result = f"<<TOOL RESULT call_id=c1 tool=read_logs>>\nERROR password={TOKEN}\n<<END>>"
    messages = [
        *CLEAN,
        {"role": "assistant", "content": 'tool read_logs {"name": "app"}'},
        {"role": "user", "content": result},
    ]
    bound, client, _, _ = build(mapping=mapping)
    bound.chat(messages, system="s", route="main")
    sent = client.sent[0]["messages"]
    assert sent[2] == {"role": "user", "content": result.replace(TOKEN, "<SECRET_1>")}
    assert sent[0] is messages[0] and sent[1] is messages[1]
    assert TOKEN not in client.text_sent()


def test_extra_keys_of_a_message_are_kept_when_its_content_is_replaced():
    bound, client, _, _ = build(mapping=known())
    bound.chat([{"role": "user", "content": f"at {IP}", "name": "ops"}], system="s", route="main")
    assert client.sent[0]["messages"] == [{"role": "user", "content": "at <IPV4_1>", "name": "ops"}]


HIDDEN = {
    "full-width letter": "ｓ" + TOKEN[1:],
    "zero-width space": TOKEN[:2] + "\u200b" + TOKEN[2:],
    "percent-encoding": "%73" + TOKEN[1:],
}


@pytest.mark.parametrize("spelling", HIDDEN.values(), ids=HIDDEN.keys())
def test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate(spelling):
    """Only the spelling the map holds is replaced. Finding hidden spellings is the pattern redactor's work
    (the producers call redact_text / redact_untrusted, which scan the decoded views)."""
    doc = f"line {spelling} end".encode()
    bound, client, _, _ = build(mapping=known())
    bound.chat(CLEAN, system="s", route="main", documents=[doc])
    assert client.sent[0]["docs"][0] is doc


def test_a_second_copy_of_a_value_beside_its_placeholder_is_replaced():
    bound, client, _, _ = build(mapping=known())
    bound.chat(CLEAN, system="s", route="main", documents=[f"<IPV4_1> again {IP}".encode()])
    assert client.sent[0]["docs"] == [b"<IPV4_1> again <IPV4_1>"]


def test_an_original_that_is_a_substring_of_another_original_is_replaced_whole():
    mapping = known()  # 10.0.0.5 and 10.0.0.50
    bound, client, _, _ = build(mapping=mapping)
    bound.chat([{"role": "user", "content": "a 10.0.0.50 b 10.0.0.5 c"}], system="s", route="main")
    assert client.sent[0]["messages"][0]["content"] == "a <IPV4_2> b <IPV4_1> c"


def test_t8_input_over_the_cap_is_refused_with_a_map_and_not_looked_at_without_one():
    big = "a" * (defaults.MAX_REDACT_CHARS + 1)
    refused(*build(mapping={}), messages=[{"role": "user", "content": big}])
    refused(*build(mapping=known()), documents=[big.encode()])
    bound, client, _, _ = build(mapping=None)  # no map: no enforce step (ORDER 007 item 4)
    bound.chat(CLEAN, system="s", route="main", documents=[big.encode()])
    assert len(client.sent) == 1


def test_t9_bytes_that_are_not_utf8_are_read_as_the_adapters_read_them():
    """`decode("utf-8", "replace")`, as llm/common.py: bad bytes do not hide a known value."""
    bound, client, _, _ = build(mapping=known())
    bound.chat(
        CLEAN, system="s", route="main", documents=[b"\xff key " + TOKEN.encode() + b" \x80"]
    )
    assert client.sent[0]["docs"] == ["� key <SECRET_1> �".encode()]


def test_t10_placeholders_already_present_are_untouched_also_ones_the_map_does_not_hold():
    for mapping in (None, {}, known()):
        bound, client, meter, _ = build(mapping=mapping)
        message = {"role": "user", "content": "host <IPV4_7>, <IPV4_1> and <SECRET_2> were named"}
        doc = b"<EMAIL_4> wrote in about <SECRET_1>"
        bound.chat([message], system="s", route="main", documents=[doc])
        assert client.sent[0]["messages"][0] is message and client.sent[0]["docs"][0] is doc
        assert len(meter.settles) == 1


@pytest.mark.parametrize("mapping", [None, {}], ids=["no-map", "map"])
@pytest.mark.parametrize(
    "content",
    [7, None, b"bytes", ["a list"], [{"type": "text", "text": "a block"}], {"text": "a dict"}],
    ids=["int", "none", "bytes", "list", "blocks", "dict"],
)
def test_t11_content_that_is_not_a_str_is_refused_not_skipped(content, mapping):
    refused(*build(mapping=mapping), messages=[*CLEAN, {"role": "user", "content": content}])


@pytest.mark.parametrize("mapping", [None, {}], ids=["no-map", "map"])
@pytest.mark.parametrize(
    "messages",
    [[{"role": "user"}], ["not a dict"], [None], 5],
    ids=["no-content", "str", "none", "int"],
)
def test_a_message_the_gate_cannot_read_is_refused(messages, mapping):
    refused(*build(mapping=mapping), messages=messages)


@pytest.mark.parametrize("mapping", [None, {}], ids=["no-map", "map"])
def test_a_document_that_is_not_bytes_is_refused(mapping):
    refused(*build(mapping=mapping), documents=["a str, not bytes"])
    refused(*build(mapping=mapping), documents=[None])


def _leaky(text, mapping):
    raise ValueError(f"leaky {TOKEN}")


@pytest.mark.parametrize(
    "enforce",
    [
        _leaky,
        lambda text, mapping: None,
        lambda text, mapping: True,
        lambda text, mapping: text.encode(),
    ],
    ids=["raises", "none", "bool", "bytes"],
)
def test_a_failing_enforce_step_means_no_call_with_no_cause_and_no_context(enforce):
    client, meter, sink = Client(), Meter(), Sink()
    gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst, enforce=enforce)
    with pytest.raises(UnmaskedInput) as caught:
        gate.bind("agent-1", "run-1", mapping={}).chat(CLEAN, system="s", route="main")
    assert client.sent == [], "the client was called after a failed enforce step"
    assert meter.reserved == {} and sink.codes() == [("refused", "mask_refused")]
    error = caught.value
    assert error.__cause__ is None and error.__context__ is None
    assert error.args == ("mask_refused",) and error.code == "mask_refused"


@pytest.mark.parametrize("bad", [{"<A_1>": 5}, {5: "x"}], ids=["int-value", "int-key"])
def test_a_bad_map_means_no_call(bad):
    refused(*build(mapping=bad))


def test_a_map_changed_by_another_thread_during_the_step_is_a_refusal_not_a_crash():
    from collections.abc import Mapping

    class Moving(Mapping):
        def __getitem__(self, key):
            raise KeyError(key)

        def __len__(self):
            return 1

        def __iter__(self):
            raise RuntimeError("dictionary changed size during iteration")

    refused(*build(mapping=Moving()))


def test_the_callers_messages_dicts_and_documents_are_not_mutated():
    mapping = known()
    messages = [{"role": "user", "content": f"host {IP}"}, {"role": "assistant", "content": "ok"}]
    documents = [f"token {TOKEN}".encode(), b"clean"]
    frozen = (copy.deepcopy(messages), list(documents), [id(m) for m in messages], dict(mapping))
    bound, client, _, _ = build(mapping=mapping)
    bound.chat(messages, system="s", route="main", documents=documents)
    now = (messages, documents, [id(m) for m in messages], dict(mapping))
    assert now == frozen, "the caller's objects were changed"
    sent = client.sent[0]
    assert sent["messages"] is not messages and sent["docs"] is not documents
    assert (
        sent["messages"][0] is not messages[0] and sent["messages"][0]["content"] == "host <IPV4_1>"
    )


# --- the live map (cb-1-M9, I3, I10) ------------------------------------------------------------------------------


def test_a_value_added_to_the_map_after_an_earlier_message_is_replaced_in_it_on_the_next_call():
    """The map is held by reference: no re-masking by the caller, no refusal (ORDER 007 item 1)."""
    mapping = runmap.RunMap()
    bound, client, meter, sink = build(mapping=mapping)
    earlier = {
        "role": "user",
        "content": "ticket ref abc123 is open",
    }  # not a pattern: nothing to mask yet
    bound.chat([earlier], system="s", route="main")
    assert client.sent[0]["messages"][0] is earlier
    runmap.redact_untrusted("ERROR user_id=abc123 refused", mapping)  # the run learns the value
    before = dict(mapping)
    bound.chat([earlier], system="s", route="main")  # the same earlier message, re-sent unchanged
    assert client.sent[1]["messages"] == [
        {"role": "user", "content": "ticket ref <TENANT_1> is open"}
    ]
    assert earlier["content"] == "ticket ref abc123 is open" and dict(mapping) == before
    assert len(meter.settles) == 2 and sink.codes() == [("ok", None), ("ok", None)]


def test_no_map_means_no_enforce_step_at_all():
    """ORDER 007 item 4: the eval and replay command lines, the judge with its own map."""
    calls = []

    def enforce(text, mapping):
        calls.append(text)
        return text

    client = Client()
    gate = ModelGate(client, meter=Meter(), audit=None, worst_case=worst, enforce=enforce)
    bound = gate.bind("agent-1", "run-1")
    message = {"role": "user", "content": f"host {IP} key {KEY}"}
    bound.chat([message], system="s", route="main", documents=[TOKEN.encode()])
    assert calls == [] and bound._mapping is None
    assert client.sent[0]["messages"][0] is message


def test_two_bound_gates_share_only_the_client_the_meter_and_the_sink():
    client, meter, sink = Client(), Meter(), Sink()
    gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst)
    with_map = gate.bind("agent-a", "run-a", mapping={"<TENANT_1>": "abc123"}, principal="svc:a")
    without = gate.bind("agent-b", "run-b")
    text = [{"role": "user", "content": "ref abc123"}]
    with_map.chat(text, system="s", route="main")
    without.chat(text, system="s", route="main")  # the other gate's map is not this one's
    assert [c["messages"][0]["content"] for c in client.sent] == ["ref <TENANT_1>", "ref abc123"]
    assert meter.reserved == {
        "res_1": ("agent-a", WORST, "run-a"),
        "res_2": ("agent-b", WORST, "run-b"),
    }
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
    assert client.sent == [], "a client call without a reservation"
    assert meter.settles == []
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
    assert meter.settles == [("res_1", settled)], "wrong settle after a client error"
    assert len(client.sent) == 1
    assert sink.codes() == [("failed", code)]


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit(1)], ids=["interrupt", "exit"])
def test_t14_a_base_exception_is_not_settled_the_worst_case_stays_booked(error):
    """INTERFACE (ii) rule 4: cost unknown, the store's sweep closes the reservation."""
    bound, _, meter, sink = build(Client(raises=error))
    with pytest.raises(type(error)) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value is error
    assert meter.settles == [], "settled after a KeyboardInterrupt or SystemExit"
    assert meter.open() == {"res_1"}
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


# --- the pinned killers of tests/gate_mutants.py (each assertion message is what the mutant must show) ------------


def test_pin_no_client_call_without_a_reservation():
    for error in (SpendRefused("daily_budget"), RuntimeError("store down")):
        bound, client, meter, _ = build(meter=Meter(reserve_raises=error))
        with contextlib.suppress(Exception):
            bound.chat(CLEAN, system="s", route="main")
        assert client.sent == [], "a client call without a reservation"
        assert meter.settles == [], "a settle without a reservation"


def test_pin_a_failing_enforce_step_means_no_call():
    client, meter = Client(), Meter()
    gate = ModelGate(client, meter=meter, audit=None, worst_case=worst, enforce=_leaky)
    with contextlib.suppress(Exception):
        gate.bind("agent-1", "run-1", mapping={}).chat(CLEAN, system="s", route="main")
    assert client.sent == [], "the client was called after a failed enforce step"
    assert meter.reserved == {}, "a reservation after a failed enforce step"


def test_pin_a_content_that_is_not_a_str_means_no_call():
    for mapping in (None, {}):
        bound, client, _, _ = build(mapping=mapping)
        with contextlib.suppress(Exception):
            bound.chat([{"role": "user", "content": 7}], system="s", route="main")
        assert client.sent == [], "the client was called with a content that is not a str"


def test_pin_no_settle_on_keyboard_interrupt():
    bound, _, meter, _ = build(Client(raises=KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        bound.chat(CLEAN, system="s", route="main")
    assert meter.settles == [], "settled after a KeyboardInterrupt"
    assert meter.open() == {"res_1"}, "the worst case does not stay booked"


def test_pin_the_settle_amount_after_a_client_error():
    for error, amount in [
        (ProviderError("bad key"), Decimal(0)),
        (ProviderExhausted("throttled"), WORST),
    ]:
        bound, _, meter, _ = build(Client(raises=error))
        with pytest.raises(ProviderError):
            bound.chat(CLEAN, system="s", route="main")
        assert meter.settles == [("res_1", amount)], "wrong settle after a client error"


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
        bound.chat([{"role": "user", "content": 7}], system="s", route="main")
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
        bound.chat([{"role": "user", "content": 7}], system="s", route="main")


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
        (Client(), Meter(), [f"key {KEY} password={TOKEN}".encode(), "not bytes"]),  # refused
        (Client(), Meter(reserve_raises=SpendRefused(f"text {TOKEN}")), None),
        (Client(raises=secret_error), Meter(), None),
        (Client(), Meter(settle_raises=secret_error), None),
    ]
    for client, meter, documents in cases:
        gate = ModelGate(client, meter=meter, audit=sink, worst_case=worst)
        bound = gate.bind("agent-1", "run-1", mapping=runmap.RunMap({"<SECRET_1>": TOKEN}))
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


def test_t20_system_and_tools_are_not_touched():
    """I4, a documented limit: operator text is not the gate's to change, even for a known value."""
    bound, client, _, sink = build(mapping={"<SECRET_1>": TOKEN})
    tools = [{"name": "t", "description": f"use password={TOKEN}"}]
    system = f"operator note {TOKEN}"
    bound.chat(CLEAN, system=system, route="main", tools=tools)
    assert client.sent[0]["system"] == system and client.sent[0]["tools"] is tools
    assert sink.codes() == [("ok", None)]


def test_the_exceptions_carry_a_stable_code_and_are_not_provider_errors():
    assert issubclass(UnmaskedInput, GateRefused) and issubclass(GateRefused, RuntimeError)
    assert not issubclass(GateRefused, ProviderError)
    assert GateRefused().code == "gate_refused" and UnmaskedInput().code == "mask_refused"
    assert UnmaskedInput().args == ("mask_refused",)


# --- existing doubles: the gate in front of ScriptLLM and FakeLLM -------------------------------------------------


def test_the_gate_in_front_of_script_llm_replaces_a_known_value_a_step_forgot_to_mask():
    llm = ScriptLLM([{"tool": "app"}, {"noaction": True}])
    mapping = runmap.RunMap()
    meter, sink = Meter(), Sink()
    bound = ModelGate(llm, meter=meter, audit=sink, worst_case=worst).bind(
        "agent-1", "run-1", mapping=mapping
    )
    doc = runmap.redact_untrusted(f"alert at {IP}", mapping).encode()
    first = bound.chat(CLEAN, system="s", route="main", documents=[doc])
    assert first.tool_calls[0].name == "read_logs"
    raw = [
        *CLEAN,
        {"role": "user", "content": f"ERROR upstream {IP} refused"},
    ]  # not masked by the caller
    second = bound.chat(raw, system="s", route="main", documents=[doc])
    assert second.text == "Nothing to do." and len(llm.sent) == 2
    assert (
        IP not in llm.everything_sent()
        and "ERROR upstream <IPV4_1> refused" in llm.everything_sent()
    )
    assert len(meter.settles) == 2


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


# --- no false refusal with real producer output (finding cb-1-B1, decided by ORDER 007) ---------------------------
# These build the strings the real producers build and put them through the gate with the run's live map:
# ZERO refusals, and what is sent is the caller's own objects whenever nothing in the map occurs raw.

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


def _through_the_gate(mapping, messages, document: bytes):
    """One call; returns (messages sent, document sent). No refusal, one settle, the map unchanged."""
    bound, client, meter, sink = build(mapping=mapping)
    before = dict(mapping)
    bound.chat(messages, system="s", route="main", documents=[document])
    assert len(client.sent) == 1 and len(meter.settles) == 1 and dict(mapping) == before
    assert sink.codes() == [("ok", None)]
    return client.sent[0]["messages"], client.sent[0]["docs"][0]


def _identical(sent, messages, sent_doc, document) -> bool:
    same = len(sent) == len(messages) and all(a is b for a, b in zip(sent, messages, strict=True))
    return same and sent_doc is document


def test_no_false_refusal_a_document_masked_with_redact_untrusted_passes_byte_identical():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(DOCUMENT + " <IPV4_7> ＜IPV4＿2＞ &lt;ID_5&gt;", mapping).encode()
    assert IP.encode() not in doc and b"ops@example.com" not in doc
    sent, sent_doc = _through_the_gate(mapping, CLEAN, doc)
    assert _identical(sent, CLEAN, sent_doc, doc)


def test_no_false_refusal_a_tool_round_with_plain_inputs_passes_byte_identical():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(DOCUMENT, mapping).encode()
    step = _tool_round(
        mapping, "c1", "read_logs", {"name": "app", "host": IP}, f"ERROR upstream {IP}"
    )
    messages = [*CLEAN, *step]
    sent, sent_doc = _through_the_gate(mapping, messages, doc)
    assert _identical(sent, messages, sent_doc, doc)


def test_no_false_refusal_a_second_tool_result_with_a_new_value_passes_byte_identical():
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(DOCUMENT, mapping).encode()
    one = _tool_round(mapping, "c1", "read_logs", {"name": "app"}, f"ERROR upstream {IP}")
    two = _tool_round(mapping, "c2", "read_logs", {"name": "db"}, "ERROR peer 10.9.9.9 refused")
    assert "10.9.9.9" in mapping.values()  # the map grew, with a value that occurs nowhere earlier
    messages = [*CLEAN, *one, *two]
    sent, sent_doc = _through_the_gate(mapping, messages, doc)
    assert _identical(sent, messages, sent_doc, doc)


def test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched():
    """cb-1-B1 (a), ORDER 007 item 2: `"user_id": "abc123"` is no pattern leaf by leaf and is one once
    composed as JSON. It is not a value the run has identified, so the gate sends it as written."""
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted("alert: checkout failing", mapping).encode()
    step = _tool_round(
        mapping, "c1", "read_logs", {"name": "app", "user_id": "abc123"}, "ERROR upstream refused"
    )
    assert step[0]["content"] == 'tool read_logs {"name": "app", "user_id": "abc123"}'
    assert "abc123" not in mapping.values()
    assert (
        runmap.is_masked(step[0]["content"], mapping) is False
    )  # the pattern redactor WOULD mask it
    messages = [*CLEAN, *step]
    sent, sent_doc = _through_the_gate(mapping, messages, doc)
    assert _identical(sent, messages, sent_doc, doc)


def test_no_false_refusal_a_later_tool_result_grows_the_map_with_a_value_the_document_holds():
    """cb-1-B1 (b): the document, masked earlier with the smaller map, is re-sent unchanged by the caller;
    the gate replaces the value the run has learned since. No refusal, no re-masking by the caller."""
    mapping = runmap.RunMap()
    doc = runmap.redact_untrusted(DOCUMENT, mapping).encode()
    assert b"abc123" in doc  # not a pattern in the document: left as written
    one = _tool_round(mapping, "c1", "read_logs", {"name": "app"}, f"ERROR upstream {IP}")
    messages = [*CLEAN, *one]
    sent, sent_doc = _through_the_gate(mapping, messages, doc)  # step 2 of the run
    assert _identical(sent, messages, sent_doc, doc)
    two = _tool_round(mapping, "c2", "read_logs", {"name": "db"}, "ERROR user_id=abc123 refused")
    assert "abc123" in mapping.values()  # the second tool result grew the map
    messages = [*CLEAN, *one, *two]
    sent, sent_doc = _through_the_gate(mapping, messages, doc)  # step 3 re-sends the same document
    assert all(a is b for a, b in zip(sent, messages, strict=True))  # the messages hold no raw copy
    assert sent_doc == doc.replace(b"abc123", b"<TENANT_1>") and b"abc123" not in sent_doc
