"""pathguard batch 5: an error from the operating system must never escape a typed path check, and the audit sink drops an
outcome only for a bad event id.

Labels, measured by real runs on (a) origin/main source plus this change's ``pathguard.py`` and (b) origin/main as it is (``pathguard`` does not exist on main, so for a file that imports it an empty stand-in module let the file load; a test that calls the module fails there): ``test_control_*`` passes on (a) and (b); ``test_pin_*`` passes on (a) and fails on (b); every other name fails on (a). This file: 1 control, 6 pin, 20 other. Nothing here says a test "fails on old main".

A third run, (c) = origin/main source plus the ``pathguard.py`` of the commit before this change (abb3e90a), is the real
fail-before for the long-name tests only: a raw ``OSError`` escaped there. The audit tests in this file (a bad event id is dropped and counted, another reason takes the outbox path, a loop in the objects folder) PASS on (c): they pin behaviour and are not fail-before. A test with several parameters carries the label of its worst case; the long-name cases of 250, 254 and 255 bytes pass on (c) too. ``test_control_every_converted_call_site_has_a_mutant_row_or_an_equivalent_entry`` is a control by (a) and (b) but fails on (c), because it reads this change's mutant table against the older source. Fake paths only; the tests build every name from parts.
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path

import pytest

from hadavin_sdk import pathguard
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.pathguard import PathRefused

NUL = chr(0)
LENGTHS = (250, 254, 255, 256, 257, 300, 1000, 4095, 4096, 4097, 5000)
# the only problems a refusal may name after the argument words (no path, no value, no error text of the system)
FIXED = {
    "too long",
    "cannot be resolved",
    "contains a control character",
    "not a plain name",
    "path escapes its folder",
    "not a file",
    "not a folder",
    "ends with a dot or space",
    "reserved device name",
}


def _link(target, link, *, directory=True):
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")


def _calls(base: Path, tail: tuple[str, ...]):
    """Every typed-path entry point, with ``must_exist`` both ways, on ``base`` plus ``tail`` (text only)."""
    path = base.joinpath(*tail)
    for must in (False, True):
        yield (
            "operator_dir",
            lambda must=must: pathguard.operator_dir(path, what="n", must_exist=must),
        )
        yield (
            "operator_file",
            lambda must=must: pathguard.operator_file(path, what="n", must_exist=must),
        )
        yield "join", lambda must=must: pathguard.join(base, *tail, what="n", must_exist=must)
        yield (
            "join-file",
            lambda must=must: pathguard.join(base, *tail, what="n", must_exist=must, kind="file"),
        )
        yield "inside", lambda must=must: pathguard.inside(base, path, what="n", must_exist=must)
    yield "LocalDirSink", lambda: LocalDirSink(path)


def _only_a_refusal(label: str, call, secrets: list[str]) -> str:
    """Run ``call``: a result, or a ``PathRefused`` whose text is one of the fixed texts. Anything else fails the test."""
    try:
        call()
    except PathRefused as exc:
        text = str(exc)
        assert text.split(": ", 1)[-1] in FIXED, f"{label}: unexpected refusal text {text[:80]!r}"
        assert exc.__cause__ is None and (exc.__context__ is None or exc.__suppress_context__), (
            label
        )
        assert not any(s and s in text for s in secrets), f"{label}: the path is in the text"
        return exc.rule
    except (
        OSError,
        ValueError,
        RuntimeError,
        TypeError,
        UnicodeError,
    ) as exc:  # a raw error of the system
        pytest.fail(f"{label}: {type(exc).__name__} escaped: {str(exc)[:80]!r}")
    return ""


@pytest.mark.parametrize("length", LENGTHS)
def test_a_long_name_is_a_refusal_never_an_oserror_in_every_typed_path_entry_point(
    tmp_path, length
):
    """Fail-before: on abb3e90a a 256-byte name with ``must_exist=False`` gave ``OSError [Errno 36]`` holding the path."""
    name = "a" * length
    for label, call in _calls(tmp_path, (name,)):
        rule = _only_a_refusal(f"{label} L={length}", call, [str(tmp_path), name[:40]])
        if length > pathguard.MAX_COMPONENT_BYTES and label != "inside":
            assert rule, f"{label} L={length}: a name over 255 bytes was accepted"


def test_pin_a_name_over_255_bytes_is_refused_by_length_before_the_system_is_asked(tmp_path):
    with pytest.raises(PathRefused) as caught:
        pathguard.operator_dir(tmp_path / ("a" * 300), what="n", must_exist=False)
    assert str(caught.value) == "n: too long" and caught.value.rule == "R5"
    assert str(tmp_path) not in str(caught.value)


def test_pin_a_name_at_the_limit_is_still_accepted(tmp_path):
    name = "a" * pathguard.MAX_COMPONENT_BYTES
    assert pathguard.operator_dir(tmp_path / name, what="n", must_exist=False).name == name
    assert pathguard.join(tmp_path, name, what="n").name == name


def test_pin_a_symlink_loop_is_a_refusal_in_every_entry_point(tmp_path):
    loop = tmp_path / "loop"
    _link(loop, loop)
    for label, call in _calls(tmp_path, ("loop", "x")):
        _only_a_refusal(f"{label} loop", call, [str(tmp_path)])
    for label, call in _calls(tmp_path, ("loop",)):
        _only_a_refusal(f"{label} loop-end", call, [str(tmp_path)])


def test_pin_every_short_mix_of_long_names_dots_links_and_loops_is_a_refusal_or_a_result(tmp_path):
    """An exhaustive walk (no random library): every path of one to three pieces taken from long names, ``..``, ``.``, a
    link out, a loop and a control character goes to every entry point."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    _link(elsewhere, tmp_path / "out")
    _link(tmp_path / "loop", tmp_path / "loop")
    pieces = ["..", ".", "out", "loop", "ok", chr(0x202E) + "x", "x" * 255, "x" * 256, "x" * 1200]
    count = 0
    for size in (1, 2, 3):
        for tail in itertools.product(pieces, repeat=size):
            for label, call in _calls(tmp_path, tail):
                _only_a_refusal(f"{label} {tail!r}", call, [str(tmp_path)])
                count += 1
    assert count > 5000


def test_pin_a_nul_and_a_long_name_together_are_one_refusal(tmp_path):
    for label, call in _calls(tmp_path, ("a" * 300 + NUL,)):
        _only_a_refusal(label, call, [str(tmp_path)])


def _event(event_id: str) -> AuditEvent:
    item = AuditEvent(run_id="r1", domain="run", operation="state", principal="p", source="runtime")
    item.event_id = event_id
    return item


def test_an_outcome_with_a_bad_event_id_is_dropped_and_counted(tmp_path):
    sink = LocalDirSink(tmp_path / "aud")
    assert sink.write_outcome(_event("c?d")) is None
    assert sink.refused_events == 1 and sink._pending == []
    assert not (sink.outbox.exists() and list(sink.outbox.glob("*"))), (
        "a refused id reached the outbox"
    )


def test_an_outcome_refused_for_another_reason_takes_the_outbox_path_not_the_drop(tmp_path):
    """The objects folder is a file, so the write fails and the record takes the outbox path. This passes on abb3e90a too (the
    failure there is the ``mkdir`` error, not a refusal); the real refusals that abb3e90a dropped are in batch 6."""
    sink = LocalDirSink(tmp_path / "aud")
    sink.root.mkdir(parents=True, exist_ok=True)
    sink.objects.write_text("not a folder", encoding="utf-8")
    assert sink.write_outcome(_event("abc")) is None
    assert sink.refused_events == 0, "an outcome with a good id was counted as refused"
    assert [p.name for p in sink.outbox.glob("*.json")] == ["abc.json"], "the record was lost"


def test_a_loop_in_the_objects_folder_takes_the_outbox_path_too(tmp_path):
    """On 3.12 the loop is a ``PathRefused`` (a real trigger that abb3e90a dropped); on 3.13 ``resolve`` does not raise, so
    there the test only shows the outbox path."""
    sink = LocalDirSink(tmp_path / "aud")
    sink.root.mkdir(parents=True, exist_ok=True)
    _link(sink.objects, sink.objects)
    assert sink.write_outcome(_event("abc")) is None
    assert sink.refused_events == 0
    assert [p.name for p in sink.outbox.glob("*.json")] == ["abc.json"]


def test_every_mutant_row_old_text_occurs_exactly_once_in_its_file():
    """Text only, no test run: a row whose old text moved or doubled would test nothing."""
    import sys

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    try:
        from tests import pathguard_mutants
    finally:
        sys.path.pop(0)
    bad = [
        (row.name, (root / row.file).read_text(encoding="utf-8").count(row.old))
        for row in pathguard_mutants.M
        if (root / row.file).read_text(encoding="utf-8").count(row.old) != 1
    ]
    assert not bad, bad


def test_control_reconcile_replays_a_file_when_the_outbox_folder_itself_is_a_link(tmp_path):
    """The outbox folder may be a link the operator set up; only a link INSIDE it is left alone."""
    sink = LocalDirSink(tmp_path / "aud")
    real = tmp_path / "real_outbox"
    real.mkdir()
    sink.root.mkdir(parents=True, exist_ok=True)
    _link(real, sink.outbox)
    (real / "abc.json").write_text(_event("abc").model_dump_json(), encoding="utf-8")
    assert sink.reconcile() == 1
    assert not (real / "abc.json").exists(), "the replayed file was left in the outbox"


def test_pin_an_error_while_asking_if_a_path_is_a_file_is_a_refusal(tmp_path, monkeypatch):
    """The operating system can refuse the file check itself (for example no right to look); it must not escape."""
    (tmp_path / "f").write_text("x", encoding="utf-8")

    def refuse(self, **_kw):
        raise PermissionError(13, "denied")

    monkeypatch.setattr(Path, "is_file", refuse)
    with pytest.raises(PathRefused) as caught:
        pathguard.join(tmp_path, "f", what="n", must_exist=True, kind="file")
    assert str(caught.value) == "n: cannot be resolved" and caught.value.rule == "R10"


def test_a_mounted_secret_folder_with_a_nul_in_its_name_is_a_config_error(
    tmp_path,
):
    """The folder name is typed by the operator; a read must refuse it in words, not leak the error of the system."""
    from hadavin_sdk.actions.secrets_file import MountedFileProvider
    from hadavin_sdk.errors import ConfigError

    provider = MountedFileProvider(tmp_path / ("s" + NUL))
    with pytest.raises(ConfigError) as caught:
        provider.get("db")
    assert str(tmp_path) not in str(caught.value)


def test_a_tool_module_part_longer_than_a_file_name_is_a_config_error(monkeypatch):
    """Config text, not a typed path, but it builds a path: on 3.12 the existence check of a long name raised ``OSError``."""
    from hadavin_sdk import tools
    from hadavin_sdk.errors import ConfigError

    with pytest.raises(ConfigError, match="each part at most 252 bytes"):
        tools._module_files("a" * 300 + ".b")


def test_a_key_file_name_too_long_for_the_system_is_a_refusal_not_an_oserror(tmp_path):
    from hadavin_sdk.audit.signer import key_path

    with pytest.raises(ValueError) as caught:
        key_path(tmp_path / ("k" * 300), tmp_path)
    assert str(tmp_path) not in str(caught.value) and "File name too long" not in str(caught.value)


def test_a_key_path_with_an_unknown_home_is_a_refusal_not_a_runtimeerror(tmp_path):
    from hadavin_sdk.audit.signer import key_path

    with pytest.raises(ValueError):
        key_path(Path("~" + "nouser" * 3 + "/key.pem"), tmp_path)


def test_a_tools_file_for_an_agent_id_longer_than_a_file_name_is_refused_in_words(tmp_path):
    from types import SimpleNamespace

    from hadavin_sdk import registry
    from hadavin_sdk.errors import ConfigError

    config = SimpleNamespace(root=tmp_path, tool_modules=(), tool_module_hashes={})
    with pytest.raises(ConfigError) as caught:
        registry._load_tools(config, {"a" * 300: object()}, {})
    assert str(tmp_path) not in str(caught.value) and "File name too long" not in str(caught.value)
