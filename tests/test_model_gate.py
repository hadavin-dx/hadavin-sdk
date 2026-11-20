"""Step F: the model gate wrapper (`guard/model_gate.py`). Invariants I1 to I11 and tests T1 to T20 of ticket F as
corrected by F-review-1.md, ORDER 006 (INTERFACE (ii)) and ORDER 007 (the mask step ENFORCES the caller's run map:
known values are replaced, nothing is refused because a pattern matched). Fake client, fake meter, list audit sink."""

from __future__ import annotations

import ast
import contextlib
import copy
import inspect
import json
import logging
import threading
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

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

    objects = []

    def spy_objects(route, system, messages, tools, documents, output_schema):
        objects.append((messages, documents))
        return spy(route, system, messages, tools, documents, output_schema)

    bound, client, _, _ = build(worst_case=spy_objects, mapping={"<SECRET_1>": TOKEN})
    bound.chat(
        [{"role": "user", "content": f"token {TOKEN}"}],
        system="s",
        route="main",
        documents=[TOKEN.encode()],
    )
    assert TOKEN not in seen[0] and seen[0].count("<SECRET_1>") == 2
    # ... and it is the very lists the client is then sent
    assert objects[0][0] is client.sent[0]["messages"] and objects[0][1] is client.sent[0]["docs"]


def test_a_settle_above_the_reservation_is_passed_through():
    """cb-1-B2: the worst case is an estimate, not a bound. D4: the overshoot is not dropped: the ok row of a paid
    call that cost more than was reserved carries the fixed code `overshoot`."""
    client = Client()
    client.reply = Reply(cost_usd=WORST * 4, model_id="fake-model")
    bound, _, meter, sink = build(client)
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert meter.settles == [("res_1", WORST * 4)] and sink.codes() == [("ok", "overshoot")]
    exact = Client()
    exact.reply = Reply(
        cost_usd=WORST, model_id="fake-model"
    )  # exactly the reservation: no overshoot
    bound, _, _, sink = build(exact)
    bound.chat(CLEAN, system="s", route="main")
    assert sink.codes() == [("ok", None)]


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
    "backslash-u escape": "\\u0073" + TOKEN[1:],  # D7: the claim is pinned (m-new-3)
    "html entity": "&#115;" + TOKEN[1:],
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
    big = "a" * (
        runmap.ENFORCE_MAX_CHARS + 1
    )  # the enforce step's own cap (E1), not the redaction cap
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


def test_a_map_whose_iteration_raises_is_a_refusal_not_a_crash():
    """No thread here: a Mapping whose `__iter__` raises what a dict raises when it changes under a reader."""
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


# --- lead review round 1, B1: the traps of the enforce build, seen from the client's side -------------------------


def test_b1_a_placeholder_inserted_in_this_pass_is_not_rewritten_by_a_later_shorter_original():
    mapping = runmap.RunMap({"<SECRET_2>": TOKEN, "<SECRET_1>": "SECRET", "<TENANT_1>": "UUID_1"})
    bound, client, _, _ = build(mapping=mapping)
    bound.chat(
        [{"role": "user", "content": f"a {TOKEN} b SECRET c UUID_1 d <UUID_1>"}],
        system="s",
        route="main",
        documents=[f"{TOKEN} SECRET".encode()],
    )
    sent = client.sent[0]
    assert sent["messages"][0]["content"] == "a <SECRET_2> b <SECRET_1> c <TENANT_1> d <UUID_1>", (
        "a placeholder inserted in this pass was rewritten"
    )
    assert sent["docs"] == [b"<SECRET_2> <SECRET_1>"]


def test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent():
    """`abcd` and `cdef` known, `abcdef` in the text: `<SECRET_1>ef` is sent. A stated limit, pinned."""
    bound, client, _, sink = build(mapping={"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"})
    bound.chat([{"role": "user", "content": "abcdef"}], system="s", route="main")
    assert client.sent[0]["messages"][0]["content"] == "<SECRET_1>ef"
    assert sink.codes() == [("ok", None)]


def test_b1_seed_entries_of_the_map_cause_no_refusal_and_no_change():
    seeded = runmap.RunMap({"<IPV4_1>": "\0seed<IPV4_1>", "<IPV4_2>": IP})
    message = {"role": "user", "content": "host <IPV4_1> was named, seed"}
    doc = b"about <IPV4_1> and <IPV4_2>"
    bound, client, _, sink = build(mapping=seeded)
    bound.chat([message, {"role": "user", "content": f"raw {IP}"}], system="s", route="main", documents=[doc])  # fmt: skip
    sent = client.sent[0]
    assert sent["messages"][0] is message and sent["docs"][0] is doc
    assert sent["messages"][1]["content"] == "raw <IPV4_2>"
    assert sink.codes() == [("ok", None)] and dict(seeded) == {"<IPV4_1>": "\0seed<IPV4_1>", "<IPV4_2>": IP}  # fmt: skip


def test_b1_the_callers_cache_is_not_written_by_a_call_through_the_gate():
    mapping = runmap.RunMap(
        {"<IPV4_1>": IP, "<SECRET_1>": TOKEN}
    )  # an empty cache: the sweep must build
    cache = mapping.redact_cache
    bound, client, _, _ = build(mapping=mapping)
    bound.chat([{"role": "user", "content": f"at {IP}"}], system="s", route="main", documents=[TOKEN.encode()])  # fmt: skip
    assert client.sent[0]["docs"] == [b"<SECRET_1>"]
    assert mapping.redact_cache is cache and cache == {}, "the caller's cache was written"


def test_b1_an_unchanged_document_with_bad_bytes_is_the_callers_own_object_beside_a_changed_one():
    """Trap 5: nothing replaced means no decode-and-encode round trip, so invalid bytes stay as they are."""
    bad = b"\xff\xfe not utf-8 \x80 <SECRET_1>"
    docs = [bad, TOKEN.encode()]
    bound, client, _, _ = build(mapping=known())
    bound.chat(CLEAN, system="s", route="main", documents=docs)
    assert client.sent[0]["docs"][0] is bad and client.sent[0]["docs"][1] == b"<SECRET_1>"


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
    assert sink.rows[0].object_ref is None  # no reservation was made
    assert not isinstance(error, ProviderError | GateRefused)


def test_m4_only_the_published_reasons_become_an_audit_code():
    """The allowlist: a `.reason` that merely looks like a code (urllib's URLError has a `.reason`) is not copied."""
    assert model_gate.SPEND_REASONS == {
        "kill_switch",
        "daily_budget",
        "monthly_budget",
        "limits_unavailable",
        "bad_amount",
        "usd_cap",  # ORDER 014: the in-memory budget of the eval and replay command lines
    }
    assert len(model_gate.SPEND_REASONS) == 6
    for reason in sorted(model_gate.SPEND_REASONS):
        bound, _, _, sink = build(meter=Meter(reserve_raises=SpendRefused(reason)))
        with pytest.raises(SpendRefused):
            bound.chat(CLEAN, system="s", route="main")
        assert sink.codes() == [("refused", reason)]
    for reason in (
        "timed_out",
        "provider_refused",
        "ok",
        "",
        None,
        7,
        ["daily_budget"],
        b"daily_budget",
    ):
        error = OSError("network")
        error.reason = reason
        bound, client, _, sink = build(meter=Meter(reserve_raises=error))
        with pytest.raises(OSError):
            bound.chat(CLEAN, system="s", route="main")
        assert sink.codes() == [("refused", "reserve_refused")], (
            "a reason that is not published was copied"
        )
        assert client.sent == []


PUBLISHED = (
    Path(__file__).resolve().parents[1]
    / "handover/core-c/inputs/interfaces-from-core-b/ii_meter.py"
)


# INTERFACE (ii) v2 as core-b published it, EMBEDDED so the check runs on every checkout (the handover file is
# not on main: lead review round 2, m-new-5). `usd_cap` is the sixth reason (ORDER 014), not in the file.
EXPECTED_METER_SIGNATURES = {
    "reserve": "(self, agent_id: 'str', worst_usd: 'Decimal', *, run_id: 'str | None' = None) -> 'str'",
    "settle": "(self, reservation_id: 'str', actual_usd: 'Decimal') -> 'Decimal'",
}
EXPECTED_PUBLISHED_REASONS = {
    "kill_switch",
    "daily_budget",
    "monthly_budget",
    "limits_unavailable",
    "bad_amount",
}


def test_the_gates_meter_protocol_and_reason_codes_equal_the_published_interface():
    """The gate's local Protocol has the published methods with the published signatures (embedded above), and the
    reason allowlist is the published five plus `usd_cap`."""
    names = sorted(n for n in vars(model_gate.Meter) if not n.startswith("_"))
    assert names == sorted(EXPECTED_METER_SIGNATURES)
    for name, expected in EXPECTED_METER_SIGNATURES.items():
        assert str(inspect.signature(getattr(model_gate.Meter, name))) == expected
    assert model_gate.SPEND_REASONS == EXPECTED_PUBLISHED_REASONS | {"usd_cap"}


def test_the_gate_agrees_with_the_published_signature_file_when_it_is_present():
    """Extra, not the only check: the same comparison against the handover file itself (absent on main)."""
    if not PUBLISHED.exists():
        pytest.skip("the published signature file is not in this checkout")
    published: dict = {}
    exec(compile(PUBLISHED.read_text(encoding="utf-8"), str(PUBLISHED), "exec"), published)  # noqa: S102
    theirs, ours = published["Meter"], model_gate.Meter
    for name in EXPECTED_METER_SIGNATURES:
        assert inspect.signature(getattr(ours, name)) == inspect.signature(getattr(theirs, name))
    reasons = published["SpendRefused"].__doc__.split("one of:")[1].replace("|", " ").split()
    assert set(reasons) == EXPECTED_PUBLISHED_REASONS and len(reasons) == 5
    assert published["SpendRefused"]("daily_budget").reason == "daily_budget"
    assert issubclass(published["SpendRefused"], RuntimeError)
    refused = published["SpendRefused"]("monthly_budget")  # the real class through the gate
    bound, client, _, sink = build(meter=Meter(reserve_raises=refused))
    with pytest.raises(published["SpendRefused"]):
        bound.chat(CLEAN, system="s", route="main")
    assert client.sent == [] and sink.codes() == [("refused", "monthly_budget")]


def test_every_error_code_the_gate_writes_is_in_its_allowlist():
    own = {v for k, v in vars(model_gate).items() if k.startswith("CODE_")}
    assert model_gate.AUDIT_CODES == model_gate.SPEND_REASONS | own
    assert not (model_gate.SPEND_REASONS & own)


def test_e4_note_enforces_the_allowlist_a_code_outside_it_is_never_written():
    """E4: AUDIT_CODES is enforced where the row is built, not only listed. Reasons are filtered at the meter
    site already; this is the last line for any future caller of `_note`."""
    bound, _, _, sink = build()
    for bad in ("daily budget; DROP", "x" * 500, "", 7, b"bytes", ["call_failed"]):
        bound._note("failed", bad)
    bound._note("failed", "call_failed")
    bound._note("ok", None)
    assert [row.error_code for row in sink.rows] == ["gate_refused"] * 6 + ["call_failed", None]


def test_d2_worst_case_raising_has_its_own_code_and_its_error_comes_out_unchanged():
    def cannot(*args):
        raise LookupError("no such route")

    bound, client, meter, sink = build(worst_case=cannot)
    with pytest.raises(LookupError):
        bound.chat(CLEAN, system="s", route="nope")
    assert (
        client.sent == [] and meter.reserved == {}
    )  # a raising worst_case is not a meter refusal:
    assert sink.codes() == [("refused", "worst_case_failed")]


@pytest.mark.parametrize(
    "amount",
    [
        None,
        0.25,
        1,
        "0.25",
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-0.01"),
        Decimal("-Infinity"),
    ],
    ids=["none", "float", "int", "str", "nan", "inf", "negative", "neg-inf"],
)
def test_d2_a_worst_case_that_is_not_a_finite_decimal_of_zero_or_more_is_refused_before_reserve(
    amount,
):
    """D2 (design review dz-M4): the gate does not trust the installer's function. Nothing is reserved."""
    bound, client, meter, sink = build(worst_case=lambda *args: amount)
    with pytest.raises(model_gate.WorstCaseInvalid) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value.args == ("worst_case_invalid",) and caught.value.__cause__ is None
    assert client.sent == [] and meter.reserved == {} and meter.settles == []
    assert sink.codes() == [("refused", "worst_case_invalid")]


def test_d2_a_zero_worst_case_is_allowed():
    free = Client()
    free.reply = Reply(cost_usd=Decimal(0), model_id="fake-model")
    bound, client, meter, sink = build(free, worst_case=lambda *args: Decimal(0))
    bound.chat(CLEAN, system="s", route="main")
    assert meter.reserved["res_1"][1] == Decimal(0) and sink.codes() == [("ok", None)]


class Marked(ProviderError):
    """A ProviderError carrying the mark core-b is asked for (requests/2-refused-before-response.md)."""

    refused_before_response = True


def _flagged(error: BaseException, value: object = True) -> BaseException:
    error.refused_before_response = value
    return error


UNSETTLED = [
    (
        ProviderError("bad key"),
        "provider_error",
    ),  # unmarked: may be a billed reply that did not parse
    (ProviderExhausted("throttled"), "provider_exhausted"),
    (
        _flagged(ProviderExhausted("throttled, flagged")),
        "provider_exhausted",
    ),  # exhausted is never (b)
    (_flagged(ProviderError("truthy, not True"), 1), "provider_error"),
    (_flagged(ProviderError("a str"), "yes"), "provider_error"),
    (_flagged(ValueError("flag on an error that is not the adapter's")), "call_failed"),
    (ValueError("a billed reply that did not parse"), "call_failed"),
    (TimeoutError(), "call_failed"),
    (OSError("connection reset"), "call_failed"),
]


@pytest.mark.parametrize(
    ("error", "code"), UNSETTLED, ids=[f"{c}-{i}" for i, (_, c) in enumerate(UNSETTLED)]
)
def test_t13_rule_c_a_failed_call_is_not_settled_and_the_same_error_comes_out(error, code):
    """ORDER 011 rule (c): cost unknown, so the worst case stays booked; the store's sweep closes it."""
    bound, client, meter, sink = build(Client(raises=error))
    with pytest.raises(type(error)) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value is error
    assert meter.settles == [], "a failed call with no mark was settled"
    assert meter.open() == {"res_1"}, "the worst case does not stay booked"
    assert len(client.sent) == 1
    assert sink.codes() == [("failed", code)]
    assert sink.rows[0].object_ref == "res_1"


@pytest.mark.parametrize(
    "error", [Marked("bad key"), _flagged(ProviderError("bad request"))], ids=["subclass", "flag"]
)
def test_t13_rule_b_an_error_marked_refused_before_response_is_settled_at_zero(error):
    """ORDER 011 rule (b), with a fake exception carrying the mark: llm/retry.py does not set it yet."""
    bound, _, meter, sink = build(Client(raises=error))
    with pytest.raises(ProviderError) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value is error
    assert meter.settles == [("res_1", Decimal(0))], "a marked refusal was not settled at 0"
    assert sink.codes() == [("failed", "provider_refused")]
    assert sink.rows[0].object_ref == "res_1"


def test_no_error_the_adapters_raise_today_carries_the_mark():
    """Until core-b adds it, rule (b) never fires: every error `with_retry` can raise is unmarked."""
    from hadavin_sdk.llm import retry

    def boom(exc):
        def call():
            raise exc

        return call

    raised = []
    for inner in (ValueError("did not parse"), OSError("reset"), ProviderError("inner")):
        with pytest.raises(ProviderError) as caught:
            retry.with_retry(boom(inner), label="x", max_attempts=1, sleep=lambda s: None)
        raised.append(caught.value)
    assert [model_gate.refused_before_response(e) for e in raised] == [False, False, False]
    assert not hasattr(ProviderError("x"), "refused_before_response")


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
    assert sink.rows[0].object_ref == "res_1"


def test_m2_settle_raising_after_a_paid_call_returns_the_reply_and_the_row_says_ok():
    """Minor m2: the call was paid and answered, so it is counted as `ok`; the code says what went wrong."""
    meter = Meter(settle_raises=RuntimeError(f"store down {TOKEN}"))
    bound, client, _, sink = build(meter=meter)
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert (
        meter.log.count("reserve") == 1 and len(meter.settles) == 1
    )  # no second reserve, no retry
    assert sink.codes() == [("ok", "settle_failed")], "a paid call was written as failed"
    assert sink.rows[0].object_ref == "res_1"


def test_settle_raising_after_a_marked_refusal_does_not_hide_the_clients_error():
    error = Marked("bad key")
    meter = Meter(settle_raises=RuntimeError("store down"))
    bound, _, _, sink = build(Client(raises=error), meter=meter)
    with pytest.raises(ProviderError) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value is error and sink.codes() == [("failed", "settle_failed")]
    assert len(meter.settles) == 1  # one try, no retry


BAD_COSTS = {
    "none": None,
    "negative": Decimal("-0.01"),
    "nan": Decimal("NaN"),
    "snan": Decimal("sNaN"),
    "infinite": Decimal("Infinity"),
    "float": 0.01,
    "str": "0.01",
}


@pytest.mark.parametrize("cost", BAD_COSTS.values(), ids=BAD_COSTS.keys())
def test_m5_a_reply_with_no_usable_cost_is_returned_and_not_settled(cost):
    """Minor m5 (decision): the call happened, so the reply is returned; the gate settles nothing (never 0,
    never a made-up amount), the worst case stays booked, and the row is `ok` with code `cost_unknown`."""
    client = Client()
    client.reply = SimpleNamespace(text="done", cost_usd=cost)
    bound, _, meter, sink = build(client)
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert meter.settles == [], "a reply with no usable cost was settled"
    assert meter.open() == {"res_1"}
    assert sink.codes() == [("ok", "cost_unknown")]
    assert sink.rows[0].object_ref == "res_1"


def test_m5_a_reply_object_without_a_cost_attribute_is_returned_and_not_settled():
    client = Client()
    client.reply = object()
    bound, _, meter, sink = build(client)
    assert bound.chat(CLEAN, system="s", route="main") is client.reply
    assert meter.settles == [] and sink.codes() == [("ok", "cost_unknown")]


def test_m5_a_zero_cost_reply_is_settled_at_zero():
    client = Client()
    client.reply = Reply(
        model_id="fake-model"
    )  # cost_usd defaults to Decimal(0): a real, known cost
    bound, _, meter, sink = build(client)
    bound.chat(CLEAN, system="s", route="main")
    assert meter.settles == [("res_1", Decimal(0))] and sink.codes() == [("ok", None)]


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


class Meeting(Client):
    """A client that lets NOBODY out until all `n` callers are inside `chat` at once (a Barrier). The barrier's
    action runs once per round, with every caller holding an open reservation, and records how many were open."""

    def __init__(self, n: int, meter: Meter) -> None:
        super().__init__()
        self.open_at_meeting: list[int] = []
        self._barrier = threading.Barrier(
            n, action=lambda: self.open_at_meeting.append(len(meter.open()))
        )

    def chat(self, messages, **kwargs):
        self._barrier.wait(
            10
        )  # raises BrokenBarrierError if a caller never arrives: the test then fails
        return super().chat(messages, **kwargs)


def test_t15_one_bound_gate_from_8_threads_every_reservation_settled_exactly_once():
    """m-new-5 (E3): deterministic. The client is released only when all 8 threads are inside `chat` (a
    Barrier), five rounds in a row, so the 8 reservations are certainly open together; then every settle id is
    checked, not a count."""
    meter = Meter()
    client = Meeting(8, meter)
    bound, _, meter, sink = build(client, meter=meter)
    results, errors = [], []

    def work(i: int) -> None:
        try:
            for round_no in range(5):
                content = f"question {i} round {round_no}"
                results.append(
                    bound.chat([{"role": "user", "content": content}], system="s", route="main")
                )
        except BaseException as exc:  # noqa: BLE001 - reported below
            errors.append(type(exc).__name__)

    threads = [threading.Thread(target=work, args=(i,), daemon=True) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert errors == [] and not any(t.is_alive() for t in threads)
    assert client.open_at_meeting == [8] * 5, "the 8 calls were not inside the gate together"
    assert results == [client.reply] * 40
    ids = sorted(meter.reserved)
    assert len(ids) == 40 and [rid for rid, _ in meter.settles].count(ids[0]) == 1
    assert sorted(rid for rid, _ in meter.settles) == ids  # every id settled, each exactly once
    assert all(amount == COST for _, amount in meter.settles) and meter.open() == set()
    assert sink.codes() == [("ok", None)] * 40
    assert (
        sorted(row.object_ref for row in sink.rows) == ids
    )  # and every row names its own reservation


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


def test_pin_an_unmarked_provider_error_is_not_settled():
    for error in (ProviderError("bad key"), ProviderExhausted("throttled")):
        bound, _, meter, _ = build(Client(raises=error))
        with pytest.raises(ProviderError):
            bound.chat(CLEAN, system="s", route="main")
        assert meter.settles == [], "an unmarked provider error was settled"


def test_pin_a_generic_exception_is_not_settled():
    for error in (ValueError("did not parse"), TimeoutError()):
        bound, _, meter, _ = build(Client(raises=error))
        with pytest.raises(type(error)):
            bound.chat(CLEAN, system="s", route="main")
        assert meter.settles == [], "a generic exception was settled"


def test_pin_a_marked_refusal_is_settled_at_zero():
    bound, _, meter, _ = build(Client(raises=Marked("bad key")))
    with pytest.raises(ProviderError):
        bound.chat(CLEAN, system="s", route="main")
    assert meter.settles == [("res_1", Decimal(0))], "a marked refusal was not settled at 0"


def test_pin_a_reply_with_no_usable_cost_is_not_settled():
    client = Client()
    client.reply = SimpleNamespace(text="done", cost_usd=Decimal("NaN"))
    bound, _, meter, _ = build(client)
    bound.chat(CLEAN, system="s", route="main")
    assert meter.settles == [], "a reply with no usable cost was settled"


def test_pin_a_known_value_in_a_message_is_replaced():
    bound, client, _, _ = build(mapping=known())
    bound.chat([{"role": "user", "content": f"key {TOKEN} from {IP}"}], system="s", route="main")
    assert client.sent[0]["messages"][0]["content"] == "key <SECRET_1> from <IPV4_1>", (
        "known originals replaced in messages"
    )


def test_pin_a_document_that_is_not_bytes_means_no_call():
    for document in ("a str", None, 7, bytearray(b"x"), ["x"]):
        for mapping in (None, {}):
            bound, client, meter, _ = build(mapping=mapping)
            with contextlib.suppress(Exception):
                bound.chat(CLEAN, system="s", route="main", documents=[document])
            assert client.sent == [], "the client was called with a document that is not bytes"
            assert meter.reserved == {}, "a reservation for a document that is not bytes"


def test_pin_every_outcome_writes_exactly_one_audit_row():
    cases = [
        build(),  # ok
        build(Client(raises=ProviderError("x"))),  # failed
        build(meter=Meter(reserve_raises=OSError("down"))),  # refused at reserve
        build(worst_case=lambda *args: None),  # refused at worst_case
    ]
    for bound, _, _, sink in cases:
        with contextlib.suppress(Exception):
            bound.chat(CLEAN, system="s", route="main")
        assert len(sink.rows) == 1, "an outcome without exactly one audit row"


def test_pin_a_gate_is_never_wrapped_twice_in_either_form():
    gate = ModelGate(Client(), meter=Meter(), audit=None, worst_case=worst)
    for inner in (gate, gate.bind("agent-1", "run-1", mapping=None)):
        try:
            ModelGate(inner, meter=Meter(), audit=None, worst_case=worst)
        except TypeError:
            continue
        raise AssertionError("a gate was wrapped by a second gate")


def test_pin_the_mark_counts_only_on_a_provider_error_that_is_not_exhausted():
    """E4: the predicate itself. A flagged non-ProviderError and a flagged ProviderExhausted are NOT refused
    before response (the second may have had attempts that were answered)."""
    refused_before = model_gate.refused_before_response
    assert refused_before(Marked("x")) is True
    assert refused_before(_flagged(ProviderError("x"))) is True
    assert refused_before(_flagged(ValueError("x"))) is False, "a flagged non-ProviderError counted"
    assert refused_before(_flagged(OSError("x"))) is False, "a flagged non-ProviderError counted"
    assert refused_before(_flagged(ProviderExhausted("x"))) is False, "a flagged ProviderExhausted counted"
    assert refused_before(ProviderError("x")) is False


def test_pin_a_flagged_exhausted_and_a_flagged_value_error_are_not_settled_through_the_gate():
    for error in (_flagged(ProviderExhausted("x")), _flagged(ValueError("x"))):
        bound, _, meter, _ = build(Client(raises=error))
        with pytest.raises(type(error)):
            bound.chat(CLEAN, system="s", route="main")
        assert meter.settles == [], "a flagged error that is not a plain ProviderError was settled"


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
    assert meter.settles == [] and meter.open() == {"res_1"}
    bound, _, meter, _ = build(
        Client(raises=Marked("bad key")), sink=Sink(raises=RuntimeError("audit down"))
    )
    with pytest.raises(ProviderError):
        bound.chat(CLEAN, system="s", route="main")
    assert meter.settles == [("res_1", Decimal(0))]


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
    assert (
        row.object_ref == "res_1"
    )  # minor m3: the reservation id, to match the row to the spend row
    assert row.decision == "no_map"  # D1: whether the map was enforced (this bound gate has none)
    assert row.inputs_hash is None
    assert row.rule_id is None and row.error_code is None
    assert row.output_hash is None and row.restored_hash is None and row.rows is None


def test_m3_a_row_written_before_any_reservation_has_no_object_reference():
    bound, _, _, sink = build()
    with pytest.raises(UnmaskedInput):
        bound.chat([{"role": "user", "content": 7}], system="s", route="main")
    assert sink.codes() == [("refused", "mask_refused")] and sink.rows[0].object_ref is None


@pytest.mark.parametrize("bad_id", [17, None, "", b"res_1", ["res_1"], Decimal(1)], ids=repr)
def test_d3_a_reservation_id_that_is_not_a_non_empty_str_means_no_call(bad_id):
    """D3 (design review). CHANGED from the test that pinned the opposite (round 1, m3: a non-str id was settled
    and the row written with no object reference). There is nothing to settle against, so the gate makes no
    call and raises its own `ReservationInvalid` (code `reservation_invalid`); the meter's booking stays until
    its sweep."""

    class OddMeter(Meter):
        def reserve(self, agent_id, worst_usd, *, run_id=None):
            super().reserve(agent_id, worst_usd, run_id=run_id)
            return bad_id

    bound, client, meter, sink = build(meter=OddMeter())
    with pytest.raises(model_gate.ReservationInvalid) as caught:
        bound.chat(CLEAN, system="s", route="main")
    assert caught.value.args == ("reservation_invalid",) and caught.value.__cause__ is None
    assert client.sent == [] and meter.settles == []
    assert sink.codes() == [("refused", "reservation_invalid")] and sink.rows[0].object_ref is None


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
        ("ok", "settle_failed"),
    ]
    assert caplog.records == []  # the module has no logger
    blob = "\n".join(captured)
    for secret in (KEY, TOKEN, "upstream said", CLEAN[0]["content"]):
        assert secret not in blob


GATE_SOURCE = Path(model_gate.__file__)
# What an exception variable may be handed to, and nothing else: a type test, one attribute read by name, the
# rule (b) predicate. Never str(), repr(), format, an f-string, `raise ... from`, an audit row or a constructor.
EXC_MAY_GO_TO = {"isinstance", "getattr", "refused_before_response"}
# `getattr` may read an exception only with these two constant names (m-new-6): `getattr(exc, "args")` is a leak
GETATTR_ON_EXC = {"reason", "refused_before_response"}
BANNED_NAMES = {"logging", "getLogger", "print", "warnings", "traceback", "repr", "format", "vars", "ContextVar", "__import__", "exec", "eval", "open", "sys", "io", "os", "pathlib"}  # fmt: skip
BANNED_ATTRS = {"__cause__", "__context__", "__traceback__", "args", "with_traceback", "add_note", "__notes__", "__dict__", "local", "getLogger", "exception", "exc_info", "stderr", "stdout", "write", "format", "format_map", "open", "write_text", "print_exc"}  # fmt: skip
# a module-level value of these kinds is state (I10): a container that a call could fill
MUTABLE_VALUES = (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)
MUTABLE_FACTORIES = {"list", "dict", "set", "bytearray", "deque", "defaultdict", "OrderedDict", "Counter"}
ROW_VALUES = {
    "run_id": "self._run_id",
    "domain": "AUDIT_DOMAIN",
    "operation": "AUDIT_OPERATION",
    "principal": "self._principal",
    "source": "self._source",
    "object_ref": "reservation if isinstance(reservation, str) else None",
    "decision": "self._mode",
    "result": "result",
    "error_code": "error_code",
}


def gate_source_problems(source: str) -> list[str]:
    """Every place in the WHOLE module (every function body, not only its head) where a logger, a print,
    exception text, an exception chain, message text in a row or in a raised error, or module state could
    get in. Walks the syntax tree, so a docstring or a comment that names a banned word does not count and
    code anywhere in the file does."""
    tree = ast.parse(source)
    parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    problems: list[str] = []
    exc_names = {"exc"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.name:
            exc_names.add(node.name)
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Import | ast.ImportFrom):
            names = {a.name.split(".")[0] for a in node.names} | {(getattr(node, "module", "") or "").split(".")[0]}  # fmt: skip
            names |= {a.name for a in node.names}
            if names & (BANNED_NAMES | {"threading", "contextvars"}):
                problems.append(f"line {line}: banned import")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            problems.append(f"line {line}: banned name {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_ATTRS:
            problems.append(f"line {line}: banned attribute {node.attr}")
        elif isinstance(node, ast.Global | ast.Nonlocal):
            problems.append(f"line {line}: module state")
        elif isinstance(node, ast.Name) and node.id in exc_names and isinstance(node.ctx, ast.Load):
            call = parent.get(node)
            target = call.func.id if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) else None  # fmt: skip
            if target not in EXC_MAY_GO_TO or node not in call.args:
                problems.append(f"line {line}: exception text could leave through {node.id}")
            elif target == "getattr" and not (
                call.args[0] is node
                and len(call.args) >= 2
                and isinstance(call.args[1], ast.Constant)
                and call.args[1].value in GETATTR_ON_EXC
            ):
                problems.append(f"line {line}: getattr on an exception with a name that is not allowed")
        elif isinstance(node, ast.Raise):
            bare_or_fixed = node.exc is None or (
                isinstance(node.exc, ast.Name) and node.cause is None
            )
            fixed_type_error = (
                isinstance(node.exc, ast.Call)
                and ast.unparse(node.exc.func) == "TypeError"
                and all(isinstance(a, ast.Constant) for a in node.exc.args)
                and node.cause is None
            )
            if not (bare_or_fixed or fixed_type_error):
                problems.append(f"line {line}: a raise that could carry text")
        elif isinstance(node, ast.Call) and ast.unparse(node.func) == "AuditEvent":
            row = {k.arg: ast.unparse(k.value) for k in node.keywords}
            if node.args or row != ROW_VALUES:
                problems.append(f"line {line}: an audit row field that is not a fixed code or id")
        elif isinstance(node, ast.Call) and ast.unparse(node.func) == "str":
            problems.append(f"line {line}: str() call")
    for node in tree.body:  # module-level state: a mutable container (a constant frozenset or tuple is fine)
        value = getattr(node, "value", None) if isinstance(node, ast.Assign | ast.AnnAssign) else None
        factory = value.func if isinstance(value, ast.Call) else None
        name = factory.id if isinstance(factory, ast.Name) else getattr(factory, "attr", None)
        if isinstance(value, MUTABLE_VALUES) or name in MUTABLE_FACTORIES:
            problems.append(f"line {node.lineno}: a module-level mutable container")
    return problems


def test_i9_the_module_has_no_logger_no_exception_text_and_no_module_state():
    """Major M1: the guard reads the whole module's syntax tree, and tests/gate_mutants.py proves it can
    fail (mutants G7a to G7d put a str(exc), a logger, a `__cause__` and message text into method bodies)."""
    problems = gate_source_problems(GATE_SOURCE.read_text(encoding="utf-8"))
    assert problems == [], f"exception text, a logger or message text in the gate: {problems}"
    audit_calls = [
        n
        for n in ast.walk(ast.parse(GATE_SOURCE.read_text(encoding="utf-8")))
        if isinstance(n, ast.Call) and ast.unparse(n.func) == "AuditEvent"
    ]
    assert len(audit_calls) == 1  # the one row writer the check above looked at
    mutable = {
        name
        for name, value in vars(model_gate).items()
        if not name.startswith("__") and isinstance(value, dict | list | set)
    }
    assert mutable == set()  # I10: no module-level state


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("            self._note(RESULT_FAILED, CODE_CALL_FAILED, reservation)\n", "            self._note(RESULT_FAILED, str(exc), reservation)\n"),
        ("        except Exception:  # rule (c): may", "        except Exception as err:  # {err} may"),
        ("            raise UnmaskedInput  #", "            raise UnmaskedInput(messages)  #"),
        ("            raise\n        except Exception:  # rule (c)", "            raise RuntimeError from exc\n        except Exception:  # rule (c)"),
        ("                    error_code=error_code,\n", "                    error_code=error_code,\n                    rule_id=self._agent_id,\n"),
        ("                    result=result,\n", "                    result=f\"{result}\",\n"),
        ("        if self._audit is None:\n            return\n", "        if self._audit is None:\n            return\n        import logging\n"),
        ("        mapping = self._mapping\n", "        mapping = self._mapping\n        print(messages)\n"),
        ("            code = CODE_SETTLE_FAILED\n", "            code = CODE_SETTLE_FAILED\n            self.last = exc.__cause__\n"),
        ("            reason = getattr(exc, \"reason\", None)\n", "            reason = getattr(exc, \"args\", None)\n"),
        ("            reason = getattr(exc, \"reason\", None)\n", "            reason = getattr(exc, \"__cause__\", None)\n"),
        ("            reason = getattr(exc, \"reason\", None)\n", "            reason = getattr(exc, \"reason\", None)\n            self.seen = sys.exception()\n"),
        ("            reason = getattr(exc, \"reason\", None)\n", "            reason = getattr(exc, \"reason\", None)\n            self.seen = sys.exc_info()\n"),
        ("            reason = getattr(exc, \"reason\", None)\n", "            reason = getattr(exc, \"reason\", None)\n            sys.stderr.write(\"x\")\n"),
        ("            reason = getattr(exc, \"reason\", None)\n", "            reason = getattr(exc, \"reason\", None)\n            self.seen = \"{}\".format(exc)\n"),
        ("        mapping = self._mapping\n", "        mapping = self._mapping\n        open(\"/tmp/x\", \"w\")\n"),
        ("AUDIT_DOMAIN = \"llm\"\n", "AUDIT_DOMAIN = \"llm\"\nSEEN = []\n"),
        ("AUDIT_DOMAIN = \"llm\"\n", "AUDIT_DOMAIN = \"llm\"\nSEEN = dict()\n"),
    ],
    ids=["str-exc", "fstring-exc", "raise-with-text", "raise-from", "extra-row-field", "fstring-row", "import-logging", "print", "cause", "getattr-args", "getattr-cause", "sys-exception", "sys-exc-info", "stderr-write", "format-on-exc", "open", "module-list", "module-dict-call"],
)  # fmt: skip
def test_i9_the_guard_fails_on_each_planted_leak_anywhere_in_the_module(old, new):
    """The guard itself, tried here on edited copies of the source (in memory): each plant sits inside a
    method body, where the old text-slice check never looked."""
    source = GATE_SOURCE.read_text(encoding="utf-8")
    assert source.count(old) == 1
    planted = source.replace(old, new)
    if "as err" in new:  # the handler now binds a name: use it in an f-string in its body
        planted = planted.replace(
            "            self._note(RESULT_FAILED, CODE_CALL_FAILED, reservation)\n",
            '            self.seen = f"{err}"\n            self._note(RESULT_FAILED, CODE_CALL_FAILED, reservation)\n',
        )
        assert planted.count("self.seen") == 1
    ast.parse(planted)  # a plant that does not parse proves nothing
    assert gate_source_problems(planted) != []


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


def test_d1_every_audit_row_says_whether_the_map_was_enforced():
    """D1: `decision` is `map_enforced` or `no_map` on every row of a bound gate: ok, failed and refused."""
    for mapping, mode in ((runmap.RunMap(), "map_enforced"), (None, "no_map")):
        for client, meter, content in (
            (Client(), Meter(), "fine"),  # ok
            (Client(raises=ProviderError("x")), Meter(), "fine"),  # failed
            (Client(), Meter(reserve_raises=OSError("down")), "fine"),  # refused at reserve
            (Client(), Meter(), 7),  # refused at the enforce step (a content that is not a str)
        ):
            bound, _, _, sink = build(client, meter=meter, mapping=mapping)
            with contextlib.suppress(Exception):
                bound.chat([{"role": "user", "content": content}], system="s", route="main")
            assert len(sink.rows) == 1 and sink.rows[0].decision == mode, (mode, sink.codes())


@pytest.mark.parametrize(
    "args",
    [
        {"agent_id": 1, "run_id": "r"},
        {"agent_id": "a", "run_id": None},
        {"agent_id": "a", "run_id": b"r"},
        {"agent_id": "a", "run_id": "r", "source": 3},
        {"agent_id": "a", "run_id": "r", "principal": 7},
        {"agent_id": "a", "run_id": "r", "principal": b"p"},
    ],
    ids=["agent", "run-none", "run-bytes", "source", "principal-int", "principal-bytes"],
)
def test_d5_bind_refuses_ids_that_are_not_str_at_bind_not_later_in_a_lost_row(args):
    """D5: the ids go into audit rows; the row is built inside `suppress`, so a bad id used to drop every row
    silently. It is a TypeError at `bind` now (a programming error at install time, with a fixed message)."""
    gate = ModelGate(Client(), meter=Meter(), audit=Sink(), worst_case=worst)
    with pytest.raises(TypeError) as caught:
        gate.bind(**args)
    assert caught.value.__cause__ is None
    assert caught.value.args[0] in {
        "agent_id, run_id and source must be str",
        "principal must be a str or None",
    }  # a fixed message: never the value that was passed


def test_d5_a_principal_of_none_or_empty_falls_back_to_the_agent_id():
    bound, _, _, sink = build(principal=None)
    bound.chat(CLEAN, system="s", route="main")
    assert sink.rows[0].principal == "agent-1"


def test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced():
    """The replace is case-sensitive: a known host written in another letter case passes."""
    mapping = runmap.RunMap({"<HOST_1>": "db1.corp.example.org", "<SECRET_1>": TOKEN})
    doc = f"see DB1.CORP.EXAMPLE.ORG and {TOKEN.upper()} and {TOKEN.swapcase()}".encode()
    bound, client, _, _ = build(mapping=mapping)
    bound.chat(CLEAN, system="s", route="main", documents=[doc])
    assert client.sent[0]["docs"][0] is doc
    bound.chat(CLEAN, system="s", route="main", documents=[b"see db1.corp.example.org"])
    assert client.sent[1]["docs"] == [b"see <HOST_1>"]  # the spelling the map holds is replaced


def test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced():
    """The gate does not clean the text: a NUL between characters, a UTF-16 document read as UTF-8, and an ANSI
    colour sequence inside a copy pass as written. Whole copies beside them are replaced."""
    mapping = runmap.RunMap({"<SECRET_1>": TOKEN, "<IPV4_1>": IP})
    nul = chr(0).join(TOKEN)
    ansi = TOKEN[:4] + "\x1b[31m" + TOKEN[4:]
    utf16 = f"key {TOKEN} at {IP}".encode("utf-16-le")
    assert TOKEN.encode() not in utf16
    bound, client, _, _ = build(mapping=mapping)
    bound.chat(
        [{"role": "user", "content": f"a {nul} b {ansi} c {TOKEN}"}],
        system="s",
        route="main",
        documents=[utf16, f"{nul} {IP}".encode()],
    )
    assert client.sent[0]["messages"][0]["content"] == f"a {nul} b {ansi} c <SECRET_1>"
    assert client.sent[0]["docs"][0] is utf16
    assert client.sent[0]["docs"][1] == f"{nul} <IPV4_1>".encode()


def test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched():
    """Only `content` is enforced. A known value in `role`, in an extra key, in `output_schema` or in `route`
    goes out as written (they are operator-controlled); the content beside them is replaced."""
    mapping = runmap.RunMap({"<SECRET_1>": TOKEN})
    schema = {"type": "object", "description": f"use {TOKEN}"}
    message = {"role": TOKEN, "content": f"x {TOKEN}", "name": TOKEN, "extra": [TOKEN]}
    bound, client, _, _ = build(mapping=mapping)
    bound.chat([message], system="s", route="main", output_schema=schema)
    sent = client.sent[0]["messages"][0]
    assert sent == {"role": TOKEN, "content": "x <SECRET_1>", "name": TOKEN, "extra": [TOKEN]}
    assert message["content"] == f"x {TOKEN}"  # the caller's dict is not changed


class _Counting:
    """Counts the redactors `runmap` builds (monkeypatched in)."""

    def __init__(self, monkeypatch):
        self.sizes, self._real = [], runmap._Redactor
        monkeypatch.setattr(runmap, "_Redactor", self)

    def __call__(self, known, cache=None):
        self.sizes.append(len(known))
        return self._real(known, cache)


def test_d9_one_map_snapshot_and_one_redactor_per_chat_call_for_100_messages_and_a_2000_entry_map(
    monkeypatch,
):
    """m-new-1 / D9. 100 messages and 2 documents against a 2,000-entry map build ONE redactor (the call's
    snapshot), not one per text. (Measured 2026-11-20 on a 6,000-entry map: the snapshot 0.18 s once per call,
    each of 100 texts 0.03 ms; before, a fresh copy and redactor per text.)"""
    mapping = runmap.RunMap({f"<TENANT_{i}>": f"tenant{i:05d}x" for i in range(1, 2001)})
    mapping["<IPV4_1>"] = IP
    counting = _Counting(monkeypatch)
    messages = [
        {"role": "user", "content": f"msg {i} peer {IP} tenant{i:05d}x"} for i in range(100)
    ]
    bound, client, _, sink = build(mapping=mapping)
    bound.chat(messages, system="s", route="main", documents=[f"doc {IP}".encode(), b"clean"])
    assert counting.sizes == [2001], "more than one redactor was built for one chat call"
    sent = client.sent[0]
    assert sent["messages"][7]["content"] == "msg 7 peer <IPV4_1> <TENANT_7>"
    assert sent["docs"][0] == b"doc <IPV4_1>" and sink.codes() == [("ok", None)]


def test_d9_the_snapshot_is_taken_once_per_call_so_every_text_sees_the_same_entries():
    """A map that grows while the call enforces its texts: every text of this call is enforced against the one
    copy taken at the start; a value the run learns meanwhile is replaced on the NEXT call (I12)."""
    mapping = runmap.RunMap({"<IPV4_1>": IP})
    later = "tenant" + "42x7"
    first_seen = []

    def enforce(text, snap):
        first_seen.append(dict(snap))
        mapping["<TENANT_1>"] = later  # the run learns a value while this call enforces
        return runmap.enforce_map(text, snap)

    gate = ModelGate(Client(), meter=Meter(), audit=Sink(), worst_case=worst, enforce=enforce)
    bound = gate.bind("agent-1", "run-1", mapping=mapping)
    bound.chat(
        [{"role": "user", "content": f"{IP} {later}"}, {"role": "user", "content": later}],
        system="s",
        route="main",
    )
    assert len(first_seen) == 2 and first_seen[0] == first_seen[1] == {"<IPV4_1>": IP}
    sent = gate._llm.sent[0]["messages"]
    assert [m["content"] for m in sent] == [
        "<IPV4_1> " + later,
        later,
    ]  # not yet known to this call
    bound.chat([{"role": "user", "content": later}], system="s", route="main")
    assert gate._llm.sent[1]["messages"][0]["content"] == "<TENANT_1>"


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


def test_the_gate_in_front_of_fake_llm_keeps_the_worst_case_booked_when_the_recording_is_missing(
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
    assert len(llm.calls) == 1 and meter.settles == [] and meter.open() == {"res_1"}
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
    probe = runmap.RunMap(mapping)  # the pattern redactor WOULD mask it
    assert "abc123" not in runmap.redact_text(step[0]["content"], probe) and len(probe) > len(
        mapping
    )
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
