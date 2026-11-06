"""Order 93: each ``except Exception`` in ``guard/diagnostic.py`` is a never-raise guard.

For every guard site: a hostile object that raises an ordinary ``Exception`` is caught, the failure is recorded (a counter
for the site; nothing about the exception), and a ``KeyboardInterrupt`` or ``SystemExit`` raised at the same place goes through.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from hadavin_sdk.codes import Code, Where
from hadavin_sdk.guard import diagnostic as dg

CANARY = "canary-p5a-guard-text"
SOURCE = Path(dg.__file__)
SITES_FILE = Path(__file__).parent / "noqa_sites.txt"


def _boom(exc_cls: type[BaseException]):
    def raiser(*_a: object, **_k: object):
        raise exc_cls(CANARY)

    return raiser


def _hostile(attr: str, exc_cls: type[BaseException]) -> object:
    """An object whose attribute ``attr`` raises ``exc_cls`` when read."""

    def get(_self: object) -> object:
        raise exc_cls(CANARY)

    return type("Hostile", (), {attr: property(get)})()


def _validation_error() -> ValidationError:
    try:
        TypeAdapter(int).validate_python("x")
    except ValidationError as e:
        return e
    raise AssertionError("validated")


def _group(exc_cls: type[BaseException]) -> BaseException:
    class Group(ExceptionGroup):  # type: ignore[type-arg]
        @property
        def exceptions(self):  # type: ignore[override]
            raise exc_cls(CANARY)

    return Group("m", [ValueError("x")])


def _named_class(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    return dg._is_the_named_class(_hostile("__module__", exc_cls))  # type: ignore[arg-type]


def _class_name(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    mp.setattr(dg, "_is_the_named_class", _boom(exc_cls))
    return dg.class_name_of(ValueError)


def _own_code(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    from hadavin_sdk.errors import ConfigError

    mp.setattr(dg, "_is_the_named_class", _boom(exc_cls))
    return dg._own_code(ConfigError)


def _counted(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    return dg._counted_module(_hostile("f_globals", exc_cls))


def _locate(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    mp.setattr(dg, "_counted_module", lambda _f: "hadavin_sdk.stats")
    return dg._locate([(_hostile("f_code", exc_cls), 1)])


def _validation(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    mp.setattr(dg, "_error_types", _boom(exc_cls))
    return dg.validation_text(_validation_error())


def _group_member(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    return dg._classify(_group(exc_cls), type(_group(exc_cls)), read_facts=False, nested=False)


def _diagnose(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    mp.setattr(dg, "_diagnose", _boom(exc_cls))
    return dg.diagnose(ValueError("x"), step=Where.other)


def _render(mp: pytest.MonkeyPatch, exc_cls: type[BaseException]) -> object:
    return dg.render(_hostile("kind", exc_cls))  # type: ignore[arg-type]


# site -> (trigger, a check of the value the guard returns)
SITES = {
    "named_class": (_named_class, lambda r: r is False),
    "class_name": (_class_name, lambda r: r == "dynamic_class"),
    "own_code": (_own_code, lambda r: r is None),
    "counted_module": (_counted, lambda r: r is None),
    "locator": (_locate, lambda r: r == ("-", "-", "-")),
    "validation_text": (_validation, lambda r: r == "other"),
    "group_member": (_group_member, lambda r: r == (Code.foreign_exception, {})),
    "diagnose": (_diagnose, lambda r: r.code is Code.foreign_exception and r.fp == dg.FALLBACK_FP),
    "render": (_render, lambda r: r.startswith("unknown: ") and "code=foreign_exception" in r),
}


@pytest.mark.parametrize("exc_cls", [ValueError, RuntimeError, RecursionError, KeyError])
@pytest.mark.parametrize("site", sorted(SITES))
def test_guard_catches_and_records(
    site: str, exc_cls: type[Exception], monkeypatch: pytest.MonkeyPatch
) -> None:
    trigger, ok = SITES[site]
    before = dg.guard_failures()
    result = trigger(monkeypatch, exc_cls)
    after = dg.guard_failures()
    assert ok(result), (site, result)
    assert after.get(site, 0) == before.get(site, 0) + 1, (
        "the failure is recorded once, at its own site"
    )
    assert {k: v for k, v in after.items() if k != site} == {
        k: v for k, v in before.items() if k != site
    }
    assert CANARY not in repr(after) and CANARY not in repr(result), (
        "nothing of the exception is kept or returned"
    )


@pytest.mark.parametrize("exc_cls", [KeyboardInterrupt, SystemExit, GeneratorExit])
@pytest.mark.parametrize("site", sorted(SITES))
def test_guard_lets_stop_requests_through(
    site: str, exc_cls: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    trigger, _ = SITES[site]
    before = dg.guard_failures()
    with pytest.raises(exc_cls):
        trigger(monkeypatch, exc_cls)
    assert dg.guard_failures() == before, "a stop request is not counted as a caught failure"


def test_guard_failures_is_a_copy_of_fixed_site_names() -> None:
    snap = dg.guard_failures()
    snap["x"] = 1
    assert "x" not in dg.guard_failures()
    assert set(dg.guard_failures()) <= set(SITES)


def _noqa_lines() -> list[tuple[int, str]]:
    return [
        (i, t)
        for i, t in enumerate(SOURCE.read_text(encoding="utf-8").splitlines(), 1)
        if "noqa" in t
    ]


def test_every_blind_except_is_one_listed_guard_with_its_reason_on_its_line() -> None:
    lines = _noqa_lines()
    for n, text in lines:
        m = re.fullmatch(r"\s*except Exception:  # noqa: BLE001 - \S.*", text)
        assert m, (
            f"line {n}: a guard is `except Exception:  # noqa: BLE001 - <reason>` and nothing else"
        )
    listed = [
        ln
        for ln in SITES_FILE.read_text(encoding="utf-8").splitlines()
        if ln and not ln.startswith("#")
    ]
    rows = [ln.split("\t") for ln in listed]
    assert sorted(int(r[0]) for r in rows) == [n for n, _ in lines], (
        "noqa_sites.txt lists exactly the guard lines"
    )
    assert sorted(r[2] for r in rows) == sorted(
        f"test_guard_catches_and_records[{s}]" for s in SITES
    )
    src = SOURCE.read_text(encoding="utf-8")
    assert "suppress" not in src and "S110" not in src and "S112" not in src
    pyproject = (SOURCE.parents[3] / "pyproject.toml").read_text(encoding="utf-8")
    assert "diagnostic" not in pyproject and "codes.py" not in pyproject, (
        "no per-file ignore for these files"
    )
