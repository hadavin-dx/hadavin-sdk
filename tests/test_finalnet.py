"""G15: the independent final net (`guard/finalnet.py`) and its wiring as the LAST check of the gate's enforce step.

The net matches registered SECRET values as plain substrings with its own Aho-Corasick automaton; it shares no matching
code with the redactor (`redact._Redactor`) or the runmap checker. Fake client, fake meter, list audit sink (the helpers of
tests/test_model_gate.py)."""

from __future__ import annotations

import base64
import importlib
import time
import unicodedata

import pytest

from hadavin_sdk.guard import finalnet, model_gate, runmap
from hadavin_sdk.guard.model_gate import FinalNetRefused, GateRefused, ModelGate
from tests.test_model_gate import (
    Client,
    Meter,
    Sink,
    build,
    worst,
)

redact = importlib.import_module(
    "hadavin_sdk.guard.redact"
)  # the package re-exports a function of that name
SECRET = "zq7Vw9Lp3Xk2Rt8N"  # noqa: S105 - a fake registered secret, 16 characters


def _outcome(bound, messages):
    """The refusal code of one call or "sent": an assertion on it fails as an assertion (not as an error)."""
    try:
        bound.chat(messages, system="s", route="main")
    except GateRefused as exc:
        return exc.code
    return "sent"


def _blind(monkeypatch):
    """Make the sweep and the gate's own net find nothing: the finder of the redactor returns the text as it is, and the
    runmap net functions report nothing. Only an independent check can still catch a value."""
    monkeypatch.setattr(redact._Redactor, "sweep", lambda self, text, deadline=None: text)
    monkeypatch.setattr(runmap, "held_value_left", lambda text, snap: False)
    monkeypatch.setattr(runmap, "held_in_views", lambda text, snap: False)


def _blind_gate():
    client, meter, sink = Client(), Meter([]), Sink([])
    gate = ModelGate(
        client, meter=meter, audit=sink, worst_case=worst, enforce=lambda text, mapping: text
    )
    return (
        gate.bind("agent-1", "run-1", mapping=runmap.RunMap({"<SECRET_1>": SECRET})),
        client,
        sink,
    )


def test_g15_the_code_is_in_the_vocabulary_and_the_exception_has_it():
    assert model_gate.CODE_FINAL_NET == "final_net_refused"
    assert model_gate.CODE_FINAL_NET in model_gate.AUDIT_CODES, "G15 the code is not audited"
    assert FinalNetRefused.code == "final_net_refused" and issubclass(FinalNetRefused, GateRefused)


def test_g15_a_secret_that_the_sweep_and_the_net_miss_is_still_caught_by_the_final_net(monkeypatch):
    _blind(monkeypatch)
    bound, client, sink = _blind_gate()
    with pytest.raises(FinalNetRefused):
        bound.chat([{"role": "user", "content": f"token {SECRET} end"}], system="s", route="main")
    assert client.sent == [], "G15 a message with a missed secret was sent"
    assert sink.codes() == [("refused", "final_net_refused")], "G15 the refusal was not audited"
    # the same call, final net off: it IS sent, so the refusal above is the final net's and nobody else's
    monkeypatch.setattr(model_gate.BoundGate, "_final_net_finds", lambda *a: False)
    bound, client, sink = _blind_gate()
    bound.chat([{"role": "user", "content": f"token {SECRET} end"}], system="s", route="main")
    assert len(client.sent) == 1


def test_g15_a_document_with_a_missed_secret_is_refused(monkeypatch):
    _blind(monkeypatch)
    bound, client, _ = _blind_gate()
    with pytest.raises(FinalNetRefused):
        bound.chat(
            [{"role": "user", "content": "hi"}],
            system="s",
            route="main",
            documents=[f"a {SECRET} b".encode()],
        )
    assert client.sent == [], "G15 a document with a missed secret was sent"


def test_g15_a_secret_split_by_a_zero_width_character_is_caught_in_the_folded_view():
    split = SECRET[:6] + "\u200b" + SECRET[6:]
    assert finalnet.secret_left(f"x {split} y", [SECRET]) == 0, "G15 a zero-width split was missed"
    assert finalnet.secret_left(f"x {SECRET[:6]} {SECRET[6:]} y", [SECRET]) is None


def test_g15_a_nul_split_and_a_utf16_document_are_caught_in_the_cleaned_view():
    nul = "a " + chr(0).join(SECRET) + " b"
    assert finalnet.secret_left(nul, [SECRET]) == 0, "G15 a NUL split was missed"
    wide = f"key {SECRET} at x".encode("utf-16-le").decode("utf-8", "replace")
    assert finalnet.secret_left(wide, [SECRET]) == 0


def test_g15_a_decomposed_text_and_a_precomposed_value_meet_in_the_folded_spellings():
    value = "café-secret-über"
    decomposed = unicodedata.normalize("NFD", value)
    assert decomposed != value
    assert finalnet.secret_left(f"a {decomposed} b", [value]) == 0, "G15 a spelling was missed"
    assert finalnet.secret_left(f"a {value} b", [decomposed]) == 0


def test_g15_a_base64_copy_that_decodes_to_the_secret_is_caught():
    blob = base64.b64encode(f"user=ops token={SECRET} end".encode()).decode()
    assert finalnet.secret_left(f"blob {blob}", [SECRET]) == 0, "G15 a base64 copy was missed"
    assert (
        finalnet.secret_left(
            "blob " + base64.b64encode(b"nothing here at all, ok").decode(), [SECRET]
        )
        is None
    )


def test_g15_an_escaped_copy_is_caught_in_the_decoded_views():
    assert finalnet.secret_left("p %7a" + SECRET[1:], [SECRET]) == 0, (
        "G15 a percent copy was missed"
    )
    assert finalnet.secret_left("p \\u007a" + SECRET[1:], [SECRET]) == 0


def test_g15_overlapping_secrets_and_a_value_inside_another_are_all_found():
    values = ["abcdef", "cdefgh", "bcdx", "wxyz1234"]
    at = sorted(values).index  # the answer is an index into the sorted values
    assert finalnet.secret_left("xx cdefgh yy", values) == at("cdefgh")
    assert finalnet.secret_left("zzabcdx", values) == at("bcdx"), "G15 a suffix link was missed"
    assert finalnet.secret_left("abcde cdefg", values) is None
    # a value that is the end of a longer one that fails half way
    assert finalnet.secret_left("abcdefgh", values) == at("abcdef")
    inner = finalnet.FinalNet(["longvalue-123456", "value-1234"])
    assert inner.first_hit("long value-1234 tail") == 1, "G15 the shorter inner value was missed"
    assert inner.first_hit("longvalue-12") is None
    nested = finalnet.FinalNet(["xabcdefgh", "cdef"])
    assert nested.first_hit("xabcdef") == nested.values.index("cdef"), (
        "G15 the inherited value was missed"
    )
    assert finalnet.FinalNet(["abcdef"]).first_hit("xabcdefx") == 0, (
        "G15 the first value (index 0) was missed"
    )


def test_g15_values_under_four_characters_are_not_read():
    assert finalnet.secret_left("abc abc", ["abc"]) is None, "G15 a 3-character value was read"
    assert finalnet.secret_left("abcd", ["abcd"]) == 0


def test_g15_a_key_of_the_map_is_a_barrier_a_forged_token_is_not():
    net = finalnet.FinalNet(["ECRET_1", "ABCD_9"])
    keys = {"<SECRET_1>"}.__contains__
    assert net.first_hit("see <SECRET_1> here", keys) is None, "G15 a placeholder matched a value"
    assert net.first_hit("see <SECRET_1> here") == 1 or net.first_hit("see <SECRET_1> here") == 0
    assert net.first_hit("see <XECRET_1> here", keys) is not None, (
        "G15 a forged token was a barrier"
    )
    # a value cannot be spelled across a key: the search restarts after it
    assert net.first_hit("ECR<SECRET_1>ET_1", keys) is None


def test_g15_the_fixed_words_of_the_framing_are_not_read_but_the_text_between_is():
    bound, client, _, sink = build(mapping=runmap.RunMap({"<SECRET_1>": "ESULT"}))
    msg = "<<TOOL RESULT call_id=c1 tool=t>>\nhello\n<<END TOOL RESULT>>"
    got = _outcome(bound, [{"role": "user", "content": msg}])
    assert got == "sent", f"G15 a value inside a fixed framing word refused the call ({got})"
    assert sink.codes()[-1][0] != "refused"
    bound, client, _, sink = build(mapping=runmap.RunMap({"<SECRET_1>": "ESULT"}))
    between = "<<TOOL RESULT call_id=c1 tool=t>>\nESULT\n<<END TOOL RESULT>>"
    bound.chat([{"role": "user", "content": between}], system="s", route="main")
    sent = client.sent[0]["messages"][0]["content"]
    assert "<SECRET_1>" in sent and "\nESULT\n" not in sent, (
        "G15 the text between the tokens was not enforced"
    )


def test_g15_text_with_no_secret_passes_byte_identical():
    mapping = runmap.RunMap({"<SECRET_1>": SECRET, "<HOST_1>": "db1.corp.example.org"})
    bound, client, _, sink = build(mapping=mapping)
    messages = [{"role": "user", "content": "summarise the alert on <HOST_1>, no secret here"}]
    docs = [b"plain bytes \xff\xfe stay"]
    bound.chat(messages, system="s", route="main", documents=docs)
    sent = client.sent[0]
    assert sent["messages"][0] is messages[0], "G15 clean text was changed"
    assert sent["docs"][0] == docs[0] and sent["docs"][0] is docs[0]
    assert sink.codes()[-1][0] != "refused"


def test_g15_the_secret_set_is_the_gates_snapshot_set_with_no_map_no_net():
    bound, client, _, _ = build()  # NO_MAP
    bound.chat([{"role": "user", "content": f"x {SECRET} y"}], system="s", route="main")
    assert len(client.sent) == 1


def test_g15_a_set_of_values_past_the_state_cap_is_refused_with_a_fixed_text(monkeypatch):
    with pytest.raises(finalnet.FinalNetTooLarge) as caught:
        finalnet.FinalNet(["a" * 50, "b" * 50], max_states=60)
    assert SECRET not in str(caught.value) and "a" * 5 not in str(caught.value)
    finalnet.FinalNet(["a" * 50, "b" * 50], max_states=101)  # exactly fits: root + 100
    monkeypatch.setattr(finalnet, "MAX_STATES", 5)
    bound, client, _, sink = build(mapping=runmap.RunMap({"<SECRET_1>": SECRET}))
    got = _outcome(bound, [{"role": "user", "content": "clean text"}])
    assert got == "final_net_refused", f"G15 a set past the cap was not refused ({got})"
    assert client.sent == [] and sink.codes() == [("refused", "final_net_refused")]


def test_g15_the_answer_is_an_index_never_the_value():
    hit = finalnet.secret_left(f"x {SECRET}", [SECRET, "other-value-1"])
    assert isinstance(hit, int) and not isinstance(hit, str)
    for name in ("first_hit", "check", "forms"):
        assert name in dir(finalnet.FinalNet)


def test_g15_a_megabyte_with_two_thousand_values_is_read_in_bounded_work():
    import random

    rng = random.Random(15)  # noqa: S311 - a test fixture
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    values = [
        "".join(rng.choice(alphabet) for _ in range(rng.randint(12, 48))) for _ in range(2000)
    ]
    filler = "".join(rng.choice(alphabet + "     ") for _ in range(1_000_000))
    started = time.perf_counter()
    net = finalnet.FinalNet(values)
    assert net.first_hit(filler) is None
    assert net.fail_steps <= len(filler), "G15 the fail steps of one scan passed its length"
    assert net.first_hit(filler[:500_000] + values[1234] + filler[500_000:]) == net.values.index(
        values[1234]
    )
    assert time.perf_counter() - started < 60, "G15 a megabyte with 2,000 values took over a minute"


def test_g15_periodic_text_and_repeated_prefixes_stay_linear():
    values = ["a" * 60 + "b", "a" * 30 + "c", ("ab" * 40) + "x", "aaaa"[:3] + "b" * 20]
    net = finalnet.FinalNet(values)
    for text in (
        "a" * 300_000,
        "ab" * 150_000,
        ("a" * 59 + "b") * 5_000,
        "a" * 58 + "ab" * 100_000,
    ):
        assert net.first_hit(text) is None
        assert net.fail_steps <= len(text), "G15 not linear: fail steps passed the text length"
    net.first_hit("a" * 300_000)
    assert net.fail_steps > 0, "G15 the fail steps are not counted"
    assert net.first_hit("a" * 100 + "b" * 60 + ("a" * 60 + "b")) is not None


def test_g15_a_clean_text_is_remembered_and_a_changed_one_is_read_again():
    net = finalnet.FinalNet([SECRET])
    assert net.check("one clean text") is False and len(net._clean) == 1
    assert net.check("one clean text") is False and len(net._clean) == 1
    assert net.check(f"one {SECRET}") is True
    assert net.check(f"one {SECRET}") is True, "G15 a refused text was remembered as clean"


def test_g15_a_placeholder_the_sweep_wrote_is_not_a_leak_of_a_value_that_is_part_of_its_name():
    bound, client, _, _ = build(mapping=runmap.RunMap({"<SECRET_1>": "ECRET_1"}))
    got = _outcome(bound, [{"role": "user", "content": "see ECRET_1 here"}])
    assert got == "sent", f"G15 a placeholder of the map was read as a leak ({got})"
    assert client.sent[0]["messages"][0]["content"] == "see <SECRET_1> here", (
        "G15 a placeholder of the map was read as a leak"
    )


def test_g15_the_tool_word_of_an_assistant_line_is_a_fixed_word():
    bound, client, _, _ = build(mapping=runmap.RunMap({"<SECRET_1>": "tool"}))
    line = {"role": "assistant", "content": "tool read_logs {}"}
    got = _outcome(bound, [line])
    assert got == "sent", f"G15 the tool word of an assistant line was read ({got})"
    assert client.sent[0]["messages"][0]["content"] == "tool read_logs {}", (
        "G15 the tool word of an assistant line was read"
    )


def test_g15_the_net_follows_the_map_a_value_registered_after_the_first_call_is_read(monkeypatch):
    _blind(monkeypatch)
    mapping = runmap.RunMap({"<SECRET_1>": SECRET})
    client, meter, sink = Client(), Meter([]), Sink([])
    gate = ModelGate(
        client, meter=meter, audit=sink, worst_case=worst, enforce=lambda text, mapping: text
    )
    bound = gate.bind("agent-1", "run-1", mapping=mapping)
    bound.chat([{"role": "user", "content": "first call, clean"}], system="s", route="main")
    mapping["<SECRET_2>"] = "pk-live-91827364"
    with pytest.raises(FinalNetRefused):
        bound.chat(
            [{"role": "user", "content": "now pk-live-91827364 leaks"}], system="s", route="main"
        )
    assert len(client.sent) == 1, "G15 the net kept the values of the first call"
