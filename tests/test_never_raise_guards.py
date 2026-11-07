"""The never-raise guards (order 93): each ``except Exception`` in a guard is caught, RECORDED, and does not propagate, while
``KeyboardInterrupt`` and ``SystemExit`` (not ``Exception`` subclasses) still propagate. One test per file that holds guards:
``guard/diagnostic.py``, ``llm/provider_facts.py``, ``llm/retry.py``. The sites are listed in ``noqa_sites.txt`` of the evidence.
"""

from __future__ import annotations

import urllib.error

import pytest

from hadavin_sdk import neverraise
from hadavin_sdk.guard import diagnostic
from hadavin_sdk.llm import ProviderError, ProviderExhausted, retry
from hadavin_sdk.llm.provider_facts import NO_FACTS, ProviderFacts, safe_attr, safe_facts

PASSING = (KeyboardInterrupt, SystemExit)


@pytest.fixture(autouse=True)
def _clean_counters():
    neverraise.reset()
    yield
    neverraise.reset()


def _raising_dict_object(exc_type):
    class Hostile:
        @property
        def __dict__(self):  # type: ignore[override]
            raise exc_type("hostile")

    return Hostile()


def _raising_module_class(exc_type):
    class Meta(type):
        @property
        def __module__(cls):  # type: ignore[override]
            raise exc_type("hostile")

    return Meta("Hostile", (Exception,), {})


def test_diagnostic_guards_catch_record_and_let_base_exceptions_through():
    # vars(exc) raises: no provider facts, one record (diagnostic.py keeps its own per-site counter, ``guard_failures``)
    before = diagnostic.guard_failures()
    assert diagnostic._provider_facts(_raising_dict_object(RuntimeError)) == {}
    after = diagnostic.guard_failures()
    assert after.get("provider_attrs", 0) == before.get("provider_attrs", 0) + 1
    # a class in the MRO whose names raise is not the provider class, the walk goes on
    assert diagnostic._is_provider_subclass(_raising_module_class(ValueError)) is False
    assert diagnostic.guard_failures().get("provider_class", 0) >= 1
    for base in PASSING:
        with pytest.raises(base):
            diagnostic._provider_facts(_raising_dict_object(base))
        with pytest.raises(base):
            diagnostic._is_provider_subclass(_raising_module_class(base))


def test_provider_facts_guards_catch_record_and_let_base_exceptions_through():
    class Obj:
        def __init__(self, exc_type):
            self._t = exc_type

        @property
        def value(self):
            raise self._t("hostile")

    assert safe_attr(Obj(RuntimeError), "value") is None
    assert neverraise.counts() == {"facts_safe_attr": 1}

    def hook_raises(_e):
        raise RuntimeError("adapter bug")

    assert safe_facts(hook_raises, ValueError("x")) is NO_FACTS
    assert neverraise.counts() == {"facts_safe_attr": 1, "facts_adapter_hook": 1}
    assert safe_facts(lambda _e: ProviderFacts(429, None, None), ValueError("x")).status == 429
    assert neverraise.counts() == {
        "facts_safe_attr": 1,
        "facts_adapter_hook": 1,
    }  # a good hook records nothing
    for base in PASSING:
        with pytest.raises(base):
            safe_attr(Obj(base), "value")

        def hook_base(_e, base=base):
            raise base()

        with pytest.raises(base):
            safe_facts(hook_base, ValueError("x"))


def _always(exc_type):
    def call(*_args):
        raise exc_type("boom")

    return call


def _run(call, **kw):
    return retry.with_retry(call, label="x", max_attempts=3, sleep=lambda _s: None, **kw)


def test_retry_guards_catch_record_and_let_base_exceptions_through(monkeypatch):
    # classify: a raw failure leaves as a ProviderError, recorded
    with pytest.raises(ProviderError):
        _run(_always(ValueError))
    assert neverraise.counts().get("retry_classify") == 1

    # class text: class_name_of breaks -> a fixed word, recorded
    neverraise.reset()
    monkeypatch.setattr(retry, "class_name_of", _always(RuntimeError))
    with pytest.raises(ProviderError, match=r"^x: dynamic_class$"):
        _run(_always(ValueError))
    assert neverraise.counts()["retry_class_text"] >= 1
    monkeypatch.undo()

    # decision: the transient test breaks -> the billed class, recorded
    neverraise.reset()
    monkeypatch.setattr(retry, "transient", _always(RuntimeError))
    with pytest.raises(ProviderExhausted):
        _run(_always(ValueError))
    assert neverraise.counts()["retry_decision"] == 1
    monkeypatch.undo()

    # wait: retry_after breaks -> the billed class, recorded
    neverraise.reset()
    monkeypatch.setattr(retry, "transient", lambda _e, _r: True)
    monkeypatch.setattr(retry, "retry_after", _always(RuntimeError))
    with pytest.raises(ProviderExhausted):
        _run(_always(ValueError))
    assert neverraise.counts()["retry_wait"] == 1
    monkeypatch.undo()

    # close: HTTPError.close raises -> never replaces the real error, recorded
    neverraise.reset()

    class BadClose(urllib.error.HTTPError):
        def close(self):
            raise RuntimeError("close failed")

    def call():
        raise BadClose("http://x.invalid/", 503, "m", {}, None)  # type: ignore[arg-type]

    with pytest.raises(ProviderError):
        _run(call)
    assert neverraise.counts()["retry_close_failed_http"] >= 1

    # KeyboardInterrupt / SystemExit pass through every path untouched
    for base in PASSING:
        with pytest.raises(base):
            _run(_always(base))
        monkeypatch.setattr(retry, "transient", _always(base))
        with pytest.raises(base):
            _run(_always(ValueError))
        monkeypatch.undo()
        monkeypatch.setattr(retry, "transient", lambda _e, _r: True)
        monkeypatch.setattr(retry, "retry_after", _always(base))
        with pytest.raises(base):
            _run(_always(ValueError))
        monkeypatch.undo()
