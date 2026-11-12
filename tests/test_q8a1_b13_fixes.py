"""Round 13 of Q8a-1: the fixes that this round made at the shared places, each with a test that fails on the code of
round 12 (head 0e7da095). A marker that must never be shown is built from parts so that it is no secret-shaped literal."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from hadavin_sdk.errors import call_class_only


def _numbers(seed: int):
    """A fixed, repeatable stream of numbers (a small linear generator): the cases are the same on every run."""
    state = seed
    while True:
        state = (state * 1103515245 + 12345) % 2**31
        yield state


MARKER = "zq-b13-" + "Wm4" + "-text"


def test_status_text_shows_only_a_real_number():
    from hadavin_sdk.errors import status_text

    assert status_text(404) == "404"
    for odd in (MARKER, b"500", None, True, 4.5, [500], {"a": 1}, "500"):
        assert status_text(odd) == "?", odd
    nums = _numbers(13)
    for _ in range(300):
        junk = "".join(chr(32 + next(nums) % 600) for _ in range(1 + next(nums) % 29))
        assert status_text(junk) == "?"


def test_a_vault_sign_in_answered_with_a_text_status_says_no_text():
    from hadavin_sdk.actions.secrets_vault import ConfigError, _login_with

    provider = SimpleNamespace(call=lambda *a, **k: (MARKER, {}))
    with pytest.raises(ConfigError) as err:
        _login_with(provider, "auth", {}, "approle")
    assert MARKER not in str(err.value) and "sign-in refused (?)" in str(err.value)


def test_the_refused_host_is_cut_to_host_name_characters():
    from hadavin_sdk.guard.egress import EgressRefused, egress_check

    for hostile in ("a b", "k=v", "x'y", "<t>", "a" * 300, "pa$$.example"):
        with pytest.raises(EgressRefused) as err:
            egress_check(hostile, frozenset({"api.example.com"}))
        assert hostile not in str(err.value), hostile
        assert str(err.value).endswith(": ?"), str(err.value)
    with pytest.raises(EgressRefused) as err:
        egress_check("other.example.com", frozenset({"api.example.com"}))
    assert str(err.value).endswith("other.example.com")


def test_a_provider_error_code_with_other_characters_is_dropped_by_describe():
    from hadavin_sdk.llm.retry import describe

    class Boom(Exception):
        status_code = 429

    nums = _numbers(7)
    for _ in range(200):
        code = "".join("ab-_. /?=&%\n\"'é"[next(nums) % 14] for _ in range(1 + next(nums) % 99))
        out = describe(Boom("q"), lambda e, c=code: c)
        assert out == "Boom 429" or (
            code and len(code) <= 80 and all(c in "ab-_. " for c in code) and out.endswith(code)
        ), (code, out)
    assert describe(Boom("q"), lambda e: "rate_limit") == "Boom 429 rate_limit"


def test_a_model_id_that_is_a_sentence_or_a_key_is_refused_at_load():
    from pydantic import ValidationError

    from hadavin_sdk.config import Route

    base = {"input_usd_per_mtok": "1", "output_usd_per_mtok": "1", "max_tokens": 10}
    for ok in ("claude-sonnet-5-5", "us.anthropic.claude-x-v1:0", "claude-y@20250514", "a/b"):
        assert Route(model_id=ok, **base).model_id == ok
    for bad in ("two words", "key=value", "", "-lead", "x" * 200, MARKER + "\n", "é"):
        with pytest.raises(ValidationError):
            Route(model_id=bad, **base)


def test_failed_takes_the_error_out_of_the_handler_and_lets_the_others_pass():
    from hadavin_sdk.errors import Failed

    with Failed() as one:
        raise ValueError(MARKER)
    assert isinstance(one.error, ValueError) and one.error.__context__ is None
    with pytest.raises(KeyError), Failed((KeyError,)) as two:
        raise KeyError("x")
    assert two.error is None
    with pytest.raises(KeyboardInterrupt), Failed():
        raise KeyboardInterrupt  # not an `Exception`: never taken
    with Failed() as none:
        pass
    assert none.error is None


def test_call_class_only_raises_without_a_cause_or_a_context_and_without_a_handler():
    def boom():
        raise OSError(MARKER)

    with pytest.raises(RuntimeError) as err:
        call_class_only(boom, lambda name: RuntimeError(f"failed: {name}"))
    assert str(err.value) == "failed: OSError"
    assert err.value.__cause__ is None and err.value.__context__ is None
    assert err.value.__suppress_context__ is False
    assert call_class_only(lambda: 5, RuntimeError) == 5
    with pytest.raises(KeyError):
        call_class_only(lambda: {}["k"], RuntimeError, passthrough=(KeyError,))


def test_no_src_module_uses_a_blind_handler_for_the_two_wrappers():
    """The two reasoned `noqa: BLE001` of round 12 are gone: the handler is the `Failed` context manager."""
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "src" / "hadavin_sdk"
    for rel in ("errors.py", "llm/retry.py"):
        text = (src / rel).read_text(encoding="utf-8")
        assert "noqa: BLE001" not in text, rel
        assert "except Exception" not in text.replace("`except Exception`", ""), rel


def _strict_models():
    from hadavin_sdk import config, registry, tools

    seen = []
    for mod in (config, registry, tools):
        for obj in vars(mod).values():
            cfg = getattr(obj, "model_config", None)
            if isinstance(obj, type) and cfg and cfg.get("extra") == "forbid":
                seen.append(obj)
    return seen


@pytest.mark.parametrize("model", _strict_models(), ids=lambda m: f"{m.__module__}.{m.__name__}")
def test_every_model_of_a_whole_file_hides_an_unknown_key_in_its_error_text(model):
    """The class that task 6 asked about: whichever way a settings model refuses an unknown key, the typed key is not in
    the text a person sees (whole-file models through the loader's `<unknown key>`, section models by position)."""
    from pydantic import ValidationError

    from hadavin_sdk.config import config_error_text

    try:
        model.model_validate({MARKER: MARKER})
    except ValidationError as exc:
        assert MARKER not in config_error_text(exc)
    else:
        pytest.fail(f"{model.__name__} accepted an unknown key")
