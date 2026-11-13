"""Round 15 of Q8a-1: the fixes of this round at the shared places, each with a test that fails on the code of round 14
(head fef4ddd5). Every test is free of fixtures of `conftest` so that the mutant runner (no conftest) can use it. A marker
that must never be shown is built from parts so that it is no secret-shaped literal."""

from __future__ import annotations

import urllib.error

import pytest


def _marker(tag: str) -> str:
    return "zq-b15-" + tag + "-" + "Wm4"


# ---- Issue 6: a status that is no number never reaches a message ------------------------------------------------------


def test_the_executor_error_code_for_a_status_that_is_no_number_is_a_question_mark():
    from hadavin_sdk.actions.executor import _http_code

    text = "418 " + _marker("status")
    try:
        got = _http_code(text)
    except ValueError:  # `int(text)` raises, and the error quotes the text
        got = "raised"
    assert got != "raised", (
        "the executor error code took int() of a text status, and int() raised with the text"
    )
    assert got == "http_?", "the executor error code for a text status is not http_?"
    assert _http_code(None) == "http_?" and _http_code(True) == "http_?", (
        "a missing or boolean status is not http_?"
    )
    assert _http_code(404) == "http_404"


def test_the_executor_error_code_takes_the_number_of_an_int_subclass_never_its_text():
    from hadavin_sdk.actions.executor import _http_code

    text = _marker("subclass")

    class Odd(int):
        def __str__(self) -> str:
            return text

        __repr__ = __str__

    assert _http_code(Odd(503)) == "http_503"
    assert text not in _http_code(Odd(503))


def test_a_tool_refusal_for_an_answer_with_a_text_status_shows_a_question_mark(monkeypatch):
    from hadavin_sdk import tools as tools_mod
    from tests.test_k5_tools import _ctx, _Opener

    text = "x " + _marker("tool")
    err = urllib.error.HTTPError("https://api.example.com/x", text, "down", {}, None)  # type: ignore[arg-type]
    ctx = _ctx(monkeypatch, _Opener(error=err))
    try:
        ctx.fetch("GET", "https://api.example.com/x", operation="bundle.read")
        got = "no refusal"
    except tools_mod.ToolRefused as exc:
        got = str(exc)
    except ValueError:  # `int(code)` raises, and the error quotes the text
        got = "raised"
    assert got != "raised", (
        "the tool refusal took int() of a text status, and int() raised with the text"
    )
    assert got == "HTTP ?", "the tool refusal for a text status is not 'HTTP ?'"


def test_describe_shows_the_number_of_a_status_and_never_the_text_of_an_int_subclass():
    from hadavin_sdk.llm.retry import describe

    text = _marker("describe")

    class Odd(int):
        def __str__(self) -> str:
            return text

    class Boom(Exception):
        status_code = Odd(429)

    shown = describe(Boom("q"), lambda e: "rate_limit")
    assert shown == "Boom 429 rate_limit" and text not in shown


def test_describe_drops_a_detail_that_is_a_run_of_32_letters_and_digits():
    from hadavin_sdk.llm.retry import describe

    class Boom(Exception):
        status_code = 429

    key = "A1" * 16  # 32 letters and digits in one run: the shape of a key
    assert describe(Boom("q"), lambda e: key) == "Boom 429", (
        "describe kept a code that is a run of 32 letters and digits"
    )
    assert describe(Boom("q"), lambda e: "403 " + key) == "Boom 429", (
        "describe kept a number followed by a key-shaped run"
    )
    assert describe(Boom("q"), lambda e: key[:31]) == "Boom 429 " + key[:31], (
        "describe dropped a code of 31 characters"
    )
    # a long code cut by separators passes, as in `Route.model_id`
    cut = "a" * 15 + "-" + "b" * 15
    assert describe(Boom("q"), lambda e: cut) == "Boom 429 " + cut


# ---- Issue 5: the refusal of an immutable pin says why; `check-config` says before an upgrade whether a config is accepted


def test_the_refusal_of_a_long_model_id_says_what_to_write_instead_and_not_the_value():
    from pydantic import ValidationError

    from hadavin_sdk.config import Route

    value = "model@sha256:" + "ab12" * 16
    with pytest.raises(ValidationError) as raised:
        Route(model_id=value, input_usd_per_mtok="1", output_usd_per_mtok="1", max_tokens=10)
    shown = str(raised.value)
    assert "short name or version" in shown and "immutable hash pin" in shown
    assert value not in shown and ("ab12" * 8) not in shown


def _config_dir(tmp_path, model_id: str | None = None):
    from tests.conftest import make_cfg

    d = make_cfg(tmp_path)
    if model_id is not None:
        f = d / "config.yaml"
        f.write_text(
            f.read_text(encoding="utf-8").replace("model_id: fake-model", f"model_id: {model_id}"),
            encoding="utf-8",
        )
    return d


def test_check_config_accepts_a_good_configuration_and_exits_0(tmp_path, capsys):
    from hadavin_sdk import cli

    assert cli.main(["--config", str(_config_dir(tmp_path)), "check-config"]) == 0
    assert "the configuration files are accepted" in capsys.readouterr().out


def test_check_config_refuses_a_key_shaped_model_id_by_field_and_rule_never_the_value(
    tmp_path, capsys
):
    from hadavin_sdk import cli

    value = "zq" + "A1" * 16
    d = _config_dir(tmp_path, model_id=value)
    assert cli.main(["--config", str(d), "check-config"]) == 2, (
        "check-config must exit 2 for a refused configuration"
    )
    seen = capsys.readouterr()
    assert "refused" in seen.err and "model_id" in seen.err
    assert value not in seen.err and value not in seen.out and "accepted" not in seen.out


def test_check_config_opens_no_connection_and_writes_nothing(tmp_path, monkeypatch, capsys):
    import socket

    from hadavin_sdk import cli

    d = _config_dir(tmp_path)

    def tree():
        return sorted(
            (p.relative_to(tmp_path).as_posix(), p.stat().st_mtime_ns, p.stat().st_size)
            for p in tmp_path.rglob("*")
        )

    before = tree()

    def no_connect(*a, **k):
        raise AssertionError("check-config opened a connection")

    monkeypatch.setattr(socket.socket, "connect", no_connect)
    code = cli.main(["--config", str(d), "check-config"])
    assert code == 0, capsys.readouterr().err
    assert tree() == before, "check-config changed the configuration folder"


# ---- Issue 4: an id that a caller hands in never reaches a message -------------------------------------------------------


def test_shown_id_shows_only_the_shape_of_an_id_the_code_makes():
    import re

    from hadavin_sdk.errors import shown_id
    from hadavin_sdk.models import new_id

    run = new_id("run")
    assert shown_id(run) == run and shown_id(run + ":12") == run + ":12"
    text = _marker("id")

    class Odd(str):
        def __str__(self) -> str:
            return text

        __format__ = lambda self, spec: text

    assert shown_id(Odd(run)) == run and f"{shown_id(Odd(run))}" == run
    for bad in (
        text,
        "run-1",
        run.upper(),
        run[:-1],
        run + "x",
        run + ":",
        "../" + run,
        run + "\n",
        "",
        None,
        7,
        b"x",
    ):
        assert shown_id(bad) == "?", (
            f"shown_id showed a value that is not an id of the code (b15 case {str(bad)[:6]!r})"
        )
    # a fuzz: whatever comes out is "?" or the shape
    state = 5
    alphabet = "run-0123456789abcdefABCDEF:/ .?\n"
    for _ in range(3000):
        state = (state * 1103515245 + 12345) % 2**31
        value = "".join(
            alphabet[(state >> (i % 17) + i) % len(alphabet)] for i in range(state % 60)
        )
        out = shown_id(value)
        assert out == "?" or (
            out == value and re.fullmatch(r"[a-z]{2,8}-[0-9a-f]{32}(:[0-9]{1,6})?", out)
        )


def test_not_found_keeps_the_id_and_shows_one_fixed_sentence():
    from hadavin_sdk.store import MemoryStore, NotFound

    text = _marker("notfound")
    err = NotFound(text)
    assert text not in str(err) and text not in repr(err), (
        "NotFound shows the id it was given (b15 notfound marker)"
    )
    assert err.key == text, "NotFound did not keep the id as .key"
    with pytest.raises(NotFound) as raised:
        MemoryStore().get_run(text)
    assert text not in str(raised.value) and text not in repr(raised.value), (
        "a store NotFound shows the id (b15 notfound marker)"
    )
    assert raised.value.key == text, "a store NotFound did not keep the id as .key"


def test_a_stale_state_message_shows_a_caller_chosen_id_as_a_question_mark():
    from hadavin_sdk.models import Run
    from hadavin_sdk.store import MemoryStore, StaleState

    text = _marker("stale")
    store = MemoryStore()
    run = Run(run_id=text, agent_id="a", principal_id="p", trigger_kind="user", trigger_ref="t")
    store.create_run(run)
    with pytest.raises(StaleState) as raised:
        store.create_run(run)
    assert text not in str(raised.value), (
        "a stale-state message shows a caller-chosen id (b15 stale marker)"
    )
    assert "?" in str(raised.value), (
        "a stale-state message does not show a question mark for the id"
    )


def test_an_audit_event_id_is_a_plain_name_so_it_can_be_a_file_name():
    from pydantic import ValidationError

    from hadavin_sdk.models import AuditEvent, new_id

    base = {"run_id": "r", "domain": "d", "operation": "o", "principal": "p", "source": "s"}
    assert AuditEvent(event_id=new_id("evt"), **base).event_id.startswith("evt-")
    for hostile in (
        "../x",
        "a/b",
        "a\\b",
        ".hidden",
        "a b",
        "",
        "x" * 129,
        "a\x00b",
        "a.json",
        "x\n",
    ):
        try:
            AuditEvent(event_id=hostile, **base)
        except ValidationError:
            continue
        raise AssertionError(
            f"an audit event id that is not a plain file name was accepted ({hostile[:6]!r})"
        )
