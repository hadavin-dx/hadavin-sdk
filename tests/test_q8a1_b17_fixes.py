"""Q8a-1 batch 17: tests of the fixes. Every value that must not be seen is built from parts (no secret-shaped literal)."""

from __future__ import annotations

import importlib
import json
import pkgutil
import sys

import pytest
from pydantic import BaseModel, ValidationError

_EVENT = {"run_id": "r", "domain": "d", "operation": "o", "principal": "p", "source": "s"}


def _marker(tag: str) -> str:
    return "zq-b17-" + tag + "-" + "Wm4"


# ---- Issue 5a: the refused value is in no error channel ------------------------------------------------------------------


def _everything_a_caller_can_print(exc: BaseException) -> str:
    """`str`, `repr`, `args`, `errors()`, `json()`, and the same for the whole chain (`__cause__`, `__context__`)."""
    parts, seen = [], set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        parts += [str(exc), repr(exc), repr(exc.args)]
        if isinstance(exc, ValidationError):
            parts += [
                repr(exc.errors()),
                exc.json(),
                repr(exc.errors(include_input=True, include_url=True, include_context=True)),
            ]
        exc = exc.__cause__ or exc.__context__
    return "\n".join(parts)


def _hostile_ids():
    m = _marker("id")
    return ["../" + m, m.upper(), m + " x", m + "\n", "a:" + m, m + "/" + m, "." + m]


def _refusals(how: str):
    from hadavin_sdk.models import AuditEvent

    for hostile in _hostile_ids():
        data = {**_EVENT, "event_id": hostile}
        with pytest.raises(ValidationError) as raised:
            if how == "init":
                AuditEvent(**data)
            elif how == "validate":
                AuditEvent.model_validate(data)
            elif how == "validate_json":
                AuditEvent.model_validate_json(json.dumps(data))
            else:
                AuditEvent.model_validate_strings(data)
        yield raised.value


def _assert_no_channel_holds_the_id(how: str):
    for err in _refusals(how):
        seen = _everything_a_caller_can_print(err)
        assert "zq-b17-id" not in seen.lower(), (
            f"a refused AuditEvent still holds the refused id ({how}): in str, repr, args, errors(), json() or the chain"
        )
        assert "plain file name" in seen, "the refusal lost its fixed sentence"
        assert err.errors()[0]["loc"] == ("event_id",), "the refusal lost its place line"


def test_a_refused_audit_event_holds_the_id_in_no_channel_constructor():
    _assert_no_channel_holds_the_id("init")


def test_a_refused_audit_event_holds_the_id_in_no_channel_model_validate():
    _assert_no_channel_holds_the_id("validate")


def test_a_refused_audit_event_holds_the_id_in_no_channel_model_validate_json():
    _assert_no_channel_holds_the_id("validate_json")


def test_a_refused_audit_event_holds_the_id_in_no_channel_model_validate_strings():
    _assert_no_channel_holds_the_id("validate_strings")


def test_the_fixed_word_replaces_the_input_and_the_title_is_kept():
    from hadavin_sdk.hidden_input import HIDDEN
    from hadavin_sdk.models import AuditEvent

    with pytest.raises(ValidationError) as raised:
        AuditEvent(event_id="../x", **_EVENT)
    assert raised.value.errors()[0]["input"] == HIDDEN
    assert raised.value.title == "AuditEvent"
    assert raised.value.__context__ is None and raised.value.__cause__ is None, (
        "the first error is kept as the context of the new one, and it still holds the id"
    )


def _import_or_none(name):
    try:
        return importlib.import_module(name)
    except (
        ImportError
    ):  # an optional dependency that is not installed: the module has no model to check
        return None


def _all_models():
    import hadavin_sdk

    for info in pkgutil.walk_packages(hadavin_sdk.__path__, "hadavin_sdk."):
        if ".demo" in info.name:
            continue
        mod = _import_or_none(info.name)
        for obj in vars(mod).values() if mod is not None else ():
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseModel)
                and obj.__module__ == mod.__name__
            ):
                yield obj


def test_every_model_of_the_package_that_hides_its_input_is_a_hidden_input_model():
    """Siblings of the audit event: a model that sets `hide_input_in_errors` but is not a `HiddenInputModel` closes two
    channels and leaves `errors()` and `json()` open."""
    from hadavin_sdk.hidden_input import HiddenInputModel

    loose = [
        f"{m.__module__}.{m.__name__}"
        for m in _all_models()
        if m.model_config.get("hide_input_in_errors") and not issubclass(m, HiddenInputModel)
    ]
    assert not loose, f"these models hide the input in the text only: {loose}"


def test_a_setting_of_the_wrong_type_is_held_in_no_channel():
    from hadavin_sdk.scrub_settings import ScrubSettings

    m = _marker("val")
    with pytest.raises(ValidationError) as raised:
        ScrubSettings(tail_window=m)
    assert m not in _everything_a_caller_can_print(raised.value)


def test_a_valid_value_and_a_refusal_for_another_reason_still_work():
    """Control: the base class changes no behaviour of a good input, and keeps the problem lines of a refusal."""
    from hadavin_sdk.models import AuditEvent
    from hadavin_sdk.scrub_settings import ScrubSettings

    assert AuditEvent(event_id="evt-ok", **_EVENT).event_id == "evt-ok"
    with pytest.raises(ValidationError) as raised:
        ScrubSettings(tail_window=1)
    assert raised.value.errors()[0]["type"] == "greater_than_equal"
    assert raised.value.errors()[0]["loc"] == ("tail_window",)


def test_a_custom_error_type_that_pydantic_does_not_know_keeps_the_place_and_says_one_fixed_sentence():
    from pydantic_core import PydanticCustomError

    from hadavin_sdk.hidden_input import HIDDEN, without_input

    original = ValidationError.from_exception_data(
        "Mini",
        [
            {
                "type": PydanticCustomError(
                    "zq_b17_custom", "a sentence that may quote {x}", {"x": _marker("c")}
                ),
                "loc": ("x",),
                "input": _marker("c"),
            }
        ],
    )
    hidden = without_input(original)
    seen = _everything_a_caller_can_print(hidden)
    assert _marker("c") not in seen
    assert hidden.errors()[0]["input"] == HIDDEN and "the value was refused" in seen
    assert hidden.errors()[0]["loc"] == ("x",)


# ---- Issue 5b: a str subclass with its own text methods is not shown ------------------------------------------------------


def test_a_str_subclass_is_never_shown_as_an_id_or_a_name():
    from hadavin_sdk.errors import NOT_SHOWN, shown_id, shown_name

    class Loud(str):
        def __str__(self) -> str:
            return _marker("loud")

        __repr__ = __str__

    good = "run-" + "a" * 32
    assert shown_id(Loud(good)) == "?", "shown_id shows a str subclass"
    assert shown_name(Loud("plain")) == NOT_SHOWN, "shown_name shows a str subclass"
    assert shown_id(good) == good and shown_name("plain") == "plain"


# ---- Issue 5c: the YAML reader that check-config reaches ------------------------------------------------------------------


@pytest.mark.parametrize("error_class", ["yaml", "other"])
def test_check_config_shows_no_text_of_a_failure_of_the_yaml_reader(
    tmp_path, monkeypatch, capsys, error_class
):
    import yaml

    from hadavin_sdk import cli, config
    from tests.conftest import make_cfg

    text = _marker("yaml")
    cfg = make_cfg(tmp_path)

    def boom(*a, **k):
        raise (yaml.YAMLError(text) if error_class == "yaml" else RuntimeError(text))

    monkeypatch.setattr(config.yaml, "load", boom)
    code = cli.main(["--config", str(cfg), "check-config"])
    seen = capsys.readouterr()
    assert text not in seen.out + seen.err, (
        "check-config printed the text of a failure of the YAML reader"
    )
    assert code == (2 if error_class == "yaml" else 3), (
        f"check-config exited {code} for {error_class}"
    )
    assert "the configuration files are accepted" not in seen.out, (
        "check-config accepted a configuration it could not read"
    )


def test_the_module_search_path_is_not_changed_by_these_tests():
    assert "zq-b17" not in " ".join(sys.path)
