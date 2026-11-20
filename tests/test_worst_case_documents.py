"""`llm.common.worst_case_usd` counts a document as the UTF-8 bytes of its lossy text decoding (fix round 3 of
F-store): valid UTF-8 counts its own length, each undecodable byte counts 3 (the replacement character), an empty
document counts nothing, and a binary blob counts what a provider that decodes it leniently would send.

Written by a different agent than the builder, from the documented formula in `worst_case_usd`: the input bytes at
one token per byte, the output cap, both priced per million tokens, times the requests, rounded up to 12 places.
"""

import random
from decimal import ROUND_CEILING, Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.llm.common import worst_case_usd

D = Decimal
ROUTE = SimpleNamespace(
    input_usd_per_mtok=D("3.00"), output_usd_per_mtok=D("15.00"), max_tokens=1024
)
PER_BYTE = ROUTE.input_usd_per_mtok / D(1_000_000)
BASE = defaults.WORST_CASE_OVERHEAD_BYTES


def _expected(size, requests=1, route=ROUTE):
    one = (
        D(size) * route.input_usd_per_mtok + D(route.max_tokens) * route.output_usd_per_mtok
    ) / D(1_000_000)
    return (one * requests).quantize(D(1).scaleb(-12), rounding=ROUND_CEILING)


def _cost(documents, **kw):
    return worst_case_usd(ROUTE, "", [], documents=documents, **kw)


def _doc_bytes(documents):
    """How many bytes the documents add: the cost of the call minus the cost with no document, in bytes."""
    extra = _cost(documents) - _cost(None)
    bytes_ = extra / PER_BYTE
    assert bytes_ == bytes_.to_integral_value() or abs(bytes_ - bytes_.to_integral_value()) < D(
        "1e-6"
    )
    return int(bytes_.to_integral_value())


def test_the_baseline_is_the_documented_formula():
    # an empty system, no messages ("[]" is 2 JSON bytes), the overhead, the output cap
    assert _cost(None) == _expected(2 + BASE)
    assert _cost([]) == _cost(None)


def test_a_valid_utf8_document_counts_its_own_bytes():
    ascii_doc = b"hello world"
    multibyte = "héllo wörld ✓ 日本語 😀".encode()
    assert _doc_bytes([ascii_doc]) == 11
    assert _doc_bytes([multibyte]) == len(multibyte)
    assert _cost([multibyte]) == _expected(2 + BASE + len(multibyte))


def test_an_empty_document_counts_nothing():
    assert _doc_bytes([b""]) == 0
    assert _doc_bytes([b"", b"", b""]) == 0
    assert _cost([b""]) == _cost(None)


@pytest.mark.parametrize(
    "bad", [b"\xff", b"\xfe", b"\x80", b"\xc0", b"\xc1", b"\xf5", b"\xed\xa0\x80"[:1]]
)
def test_each_invalid_byte_counts_three(bad):
    assert _doc_bytes([bad]) == 3
    assert _doc_bytes([bad * 10]) == 30


def test_a_run_of_invalid_bytes_counts_three_each():
    assert _doc_bytes([b"\xff" * 1000]) == 3000
    assert _doc_bytes([b"ok" + b"\xff" * 5 + b"ok"]) == 2 + 15 + 2


def test_a_truncated_multibyte_sequence_counts_as_the_decoder_replaces_it():
    doc = "日本".encode()[:-1]  # the last character cut after two of its three bytes
    want = len(doc.decode("utf-8", "replace").encode("utf-8"))
    assert want == 3 + 3  # one real character, one replacement character
    assert _doc_bytes([doc]) == want


def test_a_binary_blob_counts_what_the_lossy_decoding_sends():
    blob = bytes(range(256)) * 8
    want = len(blob.decode("utf-8", "replace").encode("utf-8"))
    assert want > len(blob)  # the high bytes grow: the raw length would undercount
    assert _doc_bytes([blob]) == want
    assert _cost([blob]) == _expected(2 + BASE + want)


def test_a_random_blob_is_never_counted_below_its_raw_length():
    rnd = random.Random(7)  # noqa: S311 - a seeded blob
    for _ in range(30):
        blob = bytes(rnd.randrange(256) for _ in range(rnd.randrange(0, 400)))
        got = _doc_bytes([blob])
        assert got == len(blob.decode("utf-8", "replace").encode("utf-8"))
        assert got >= len(blob)


def test_documents_add_up_and_the_other_parts_are_unchanged():
    docs = [b"abc", "é".encode(), b"\xff\xfe", b""]
    assert _doc_bytes(docs) == 3 + 2 + 6 + 0
    full = worst_case_usd(
        ROUTE,
        "sys",
        [{"role": "user", "content": "hi"}],
        tools=[{"name": "t"}],
        documents=docs,
        output_schema={"type": "object"},
        requests=3,
    )
    messages = len(b'[{"content": "hi", "role": "user"}]')
    tools = len(b'[{"name": "t"}]')
    schema = len(b'{"type": "object"}')
    size = 3 + messages + tools + 11 + 2 * schema + BASE
    assert full == _expected(size, requests=3)


def test_a_larger_binary_document_never_costs_less():
    costs = [_cost([b"\xff" * n]) for n in (0, 1, 10, 100, 1000)]
    assert costs == sorted(costs) and len(set(costs)) == len(costs)
