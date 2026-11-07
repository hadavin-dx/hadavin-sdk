"""The never-raise guards each ``except Exception`` in a guard is caught, RECORDED, and does not propagate, while
``KeyboardInterrupt`` and ``SystemExit`` (not ``Exception`` subclasses) still propagate. One test per file that holds guards:
``guard/diagnostic.py``, ``llm/provider_facts.py``, ``llm/retry.py``. The guards are listed in ``tests/fixtures/guard_ledger.txt``, keyed by
file, function and site name (no line numbers); ``test_ledger_*`` parses the source and checks that list against the code.
There is ONE counter (``hadavin_sdk.neverraise``); the counters are never reset, a test reads the difference it caused.
"""

from __future__ import annotations

import ast
import multiprocessing
import urllib.error
from pathlib import Path

import pytest

from hadavin_sdk import neverraise
from hadavin_sdk.guard import diagnostic
from hadavin_sdk.llm import ProviderError, ProviderExhausted, retry
from hadavin_sdk.llm.provider_facts import NO_FACTS, ProviderFacts, safe_attr, safe_facts
from tests.import_order_child import record_while_holding_the_lock

PASSING = (KeyboardInterrupt, SystemExit)


ROOT = Path(__file__).resolve().parents[1]
GUARD_FILES = (
    "src/hadavin_sdk/guard/diagnostic.py",
    "src/hadavin_sdk/llm/provider_facts.py",
    "src/hadavin_sdk/llm/retry.py",
)
LEDGER = Path(__file__).parent / "fixtures" / "guard_ledger.txt"


class Seen:
    """What the shared counters gained since this object was made (the counters are process-wide and never reset)."""

    def __init__(self) -> None:
        self._start = neverraise.counts()

    def delta(self) -> dict[str, int]:
        now = neverraise.counts()
        return {k: n - self._start.get(k, 0) for k, n in now.items() if n != self._start.get(k, 0)}


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
    # vars(exc) raises: no provider facts, ONE record, in the one shared counter (diagnostic.guard_failures() is a view of it)
    seen = Seen()
    before = diagnostic.guard_failures()
    assert diagnostic._provider_facts(_raising_dict_object(RuntimeError)) == {}
    after = diagnostic.guard_failures()
    assert after.get("provider_attrs", 0) == before.get("provider_attrs", 0) + 1
    assert seen.delta() == {"diag_provider_attrs": 1}
    # a class in the MRO whose names raise is not the provider class, the walk goes on
    assert diagnostic._is_provider_subclass(_raising_module_class(ValueError)) is False
    assert seen.delta()["diag_provider_class"] >= 1
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

    seen = Seen()
    assert safe_attr(Obj(RuntimeError), "value") is None
    assert seen.delta() == {"facts_safe_attr": 1}

    def hook_raises(_e):
        raise RuntimeError("adapter bug")

    assert safe_facts(hook_raises, ValueError("x")) is NO_FACTS
    assert seen.delta() == {"facts_safe_attr": 1, "facts_adapter_hook": 1}
    assert safe_facts(lambda _e: ProviderFacts(429, None, None), ValueError("x")).status == 429
    assert seen.delta() == {
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


def _http_error(status):
    return urllib.error.HTTPError("http://x.invalid/", status, "m", {}, None)  # type: ignore[arg-type]


def test_retry_guards_catch_record_and_let_base_exceptions_through(monkeypatch):
    # class text: class_name_of breaks -> a fixed word, recorded
    seen = Seen()
    monkeypatch.setattr(retry, "class_name_of", _always(RuntimeError))
    with pytest.raises(ProviderError, match=r"^x: dynamic_class$"):
        _run(_always(ValueError))
    assert seen.delta()["retry_class_text"] >= 1
    monkeypatch.undo()

    # decision: the transient test breaks -> the billed class, recorded
    seen = Seen()
    monkeypatch.setattr(retry, "transient", _always(RuntimeError))
    with pytest.raises(ProviderExhausted):
        _run(_always(ValueError))
    assert seen.delta()["retry_decision"] == 1
    monkeypatch.undo()

    # wait: retry_after breaks -> the billed class, recorded
    seen = Seen()
    monkeypatch.setattr(retry, "transient", lambda _e, _r: True)
    monkeypatch.setattr(retry, "retry_after", _always(RuntimeError))
    with pytest.raises(ProviderExhausted):
        _run(_always(ValueError))
    assert seen.delta()["retry_wait"] == 1
    monkeypatch.undo()

    # close: HTTPError.close raises -> never replaces the real error, recorded
    seen = Seen()

    class BadClose(urllib.error.HTTPError):
        def close(self):
            raise RuntimeError("close failed")

    def call():
        raise BadClose("http://x.invalid/", 503, "m", {}, None)  # type: ignore[arg-type]

    with pytest.raises(ProviderError):
        _run(call)
    assert seen.delta()["retry_close_failed_http"] >= 1

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


def test_an_ordinary_retried_failure_is_not_counted_and_a_genuine_fault_is(monkeypatch):
    # (a) a 429 that is retried and then succeeds: ordinary control flow, nothing is counted
    seen = Seen()
    answers = iter([_http_error(429), _http_error(429)])

    def flaky():
        err = next(answers, None)
        if err is not None:
            raise err
        return "ok"

    assert _run(flaky) == "ok"
    assert seen.delta() == {}, "a retried 429 is not an absorbed fault"
    # (b) a 429 that stays: refused as designed (ProviderExhausted), still nothing counted
    seen = Seen()
    with pytest.raises(ProviderExhausted):
        _run(lambda: (_ for _ in ()).throw(_http_error(429)))
    assert seen.delta() == {}
    # (c) a 401 that is not retried, and a plain error that is not transient: nothing counted
    seen = Seen()
    with pytest.raises(ProviderError):
        _run(lambda: (_ for _ in ()).throw(_http_error(401)))
    with pytest.raises(ProviderError):
        _run(_always(ValueError))
    assert seen.delta() == {}
    # (d) a genuine absorbed fault (the retry decision crashes) is counted, once
    seen = Seen()
    monkeypatch.setattr(retry, "transient", _always(RuntimeError))
    with pytest.raises(ProviderExhausted):
        _run(_always(ValueError))
    assert seen.delta() == {"retry_decision": 1}


def test_a_failed_wait_computation_stops_the_loop_and_is_recorded(monkeypatch):
    # PENDING LEAD 25, option A: retry_after raises -> no second request, no sleep, the billed class, the failure recorded
    monkeypatch.setattr(retry, "transient", lambda _e, _r: True)
    monkeypatch.setattr(retry, "retry_after", _always(RuntimeError))
    calls = []
    slept = []

    def call():
        calls.append(1)
        raise _http_error(429)

    seen = Seen()
    with pytest.raises(ProviderExhausted) as got:
        retry.with_retry(call, label="x", max_attempts=5, sleep=slept.append)
    err = got.value
    assert len(calls) == 1, "the loop stops: no further request after a failed wait computation"
    assert slept == []
    assert seen.delta() == {"retry_wait": 1}
    assert (err.status, err.error_type, err.retryable, err.retry_count) == (
        429,
        "rate_limit",
        None,
        1,
    )
    assert str(err) == "x: urllib.error.HTTPError 429 rate_limit after 1 attempts"
    assert err.__cause__ is None and err.__suppress_context__


@pytest.mark.parametrize(
    "site",
    sorted(s.value.removeprefix("diag_") for s in neverraise.Site if s.value.startswith("diag_")),
)
def test_every_diagnostic_guard_site_records_into_the_shared_counter(site):
    seen = Seen()
    before = diagnostic.guard_failures()
    diagnostic._guard_failed(site)
    assert seen.delta() == {f"diag_{site}": 1}
    assert diagnostic.guard_failures().get(site, 0) == before.get(site, 0) + 1


def test_one_counter_not_two():
    assert not hasattr(neverraise, "reset"), (
        "a production module does not expose a way to zero the counters"
    )
    assert not hasattr(diagnostic, "_GUARD_FAILURES"), (
        "guard/diagnostic.py keeps no counter of its own"
    )


def test_record_can_be_entered_again_on_the_same_thread():
    # A finalizer or signal handler that records while this thread is already inside ``record`` must not deadlock. A fresh child
    # process, so a lock that blocks cannot hold up the counters of this process.
    ctx = multiprocessing.get_context("spawn")
    child = ctx.Process(target=record_while_holding_the_lock, daemon=True)
    child.start()
    child.join(timeout=20)
    blocked = child.is_alive()
    if blocked:
        child.kill()
        child.join()
    assert not blocked, "record() blocked on a lock held by its own thread"
    assert child.exitcode == 0, child.exitcode


def _guard_rows(rel):
    """(file, function, site) for every ``except Exception`` (or broader) handler in a file. The site is the name its own body
    passes to ``_guard_failed("<site>")`` or ``record(Site.<site>)``; ``-`` when the handler records nothing."""
    tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
    rows = []

    def own_calls(handler):
        stack = list(handler.body)
        while stack:
            node = stack.pop(0)
            if isinstance(node, ast.ExceptHandler):
                continue  # a nested handler has its own row
            if isinstance(node, ast.Call):
                yield node
            stack = [*ast.iter_child_nodes(node), *stack]

    def visit(node, func):
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else func
            if isinstance(child, ast.ExceptHandler):
                kind = ast.unparse(child.type) if child.type is not None else "bare"
                assert kind not in ("BaseException", "bare"), f"{rel} {func}: {kind}"
                if kind == "Exception":
                    sites = []
                    for call in own_calls(child):
                        fn = ast.unparse(call.func)
                        if fn == "_guard_failed" and call.args:
                            sites.append(ast.literal_eval(call.args[0]))
                        elif fn == "record" and call.args:
                            arg = ast.unparse(call.args[0])
                            assert arg.startswith("Site."), arg
                            sites.append(arg.removeprefix("Site."))
                    assert len(sites) <= 1, f"{rel} {func}: one guard records one site: {sites}"
                    rows.append((rel, func, sites[0] if sites else "-"))
            visit(child, name)

    visit(tree, "<module>")
    return rows


def _ledger_rows():
    rows = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            cols = line.split("\t")
            assert len(cols) == 5, line
            rows.append(cols)
    return rows


def test_ledger_lists_exactly_the_guards_in_the_code_by_file_function_and_site():
    actual = sorted(row for rel in GUARD_FILES for row in _guard_rows(rel))
    listed = sorted((r[0], r[1], r[2]) for r in _ledger_rows())
    assert listed == actual, (
        "tests/fixtures/guard_ledger.txt and the except-Exception handlers of the three files differ"
    )
    assert len(actual) == len(set(actual)), "two handlers share file, function and site"


def test_ledger_names_a_test_that_exists_and_a_reason_for_every_row():
    here = Path(__file__).parent
    in_mutant_copy = not (
        ROOT / "pyproject.toml"
    ).exists()  # the mutant runner copies only some test files
    for _file, _func, site, why, test in _ledger_rows():
        assert len(why) >= 30, f"{site}: no reason"
        test_file, name = test.split("::")
        base = name.split("[")[0]
        path = here / test_file
        if not path.exists() and in_mutant_copy:
            continue
        assert f"def {base}(" in path.read_text(encoding="utf-8"), f"{site}: no {test}"


def test_every_site_name_is_recorded_by_exactly_one_guard_and_none_is_dead():
    recorded = []
    for rel in GUARD_FILES:
        for _f, _fn, site in _guard_rows(rel):
            if site != "-":
                recorded.append(site if not rel.endswith("diagnostic.py") else f"diag_{site}")
    assert sorted(recorded) == sorted(site.value for site in neverraise.Site), (
        "a Site member that no guard records (or a guard with no member)"
    )
