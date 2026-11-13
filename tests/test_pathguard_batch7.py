"""pathguard batch 7: the whole-path limit (4095 bytes) on both sides, the resolved path measured again, a tool module path
measured whole, errors of the system turned into one fixed refusal with no cause and no context, the audit id test shared by
both writers, a projected-volume token file, and the folder checks of the replay and score commands.

Labels, measured by real runs on (a) origin/main source plus this change's ``pathguard.py`` and (b) origin/main as it is (``pathguard`` does not exist on main, so for a file that imports it an empty stand-in module let the file load; a test that calls the module fails there): ``test_control_*`` passes on (a) and (b); ``test_pin_*`` passes on (a) and fails on (b); every other name fails on (a). This file: 0 control, 16 pin, 25 other. Nothing here says a test "fails on old main".

Fake paths only; names are built from parts.
"""

from __future__ import annotations

import errno
import os
import sys
from pathlib import Path

import pytest

from hadavin_sdk import pathguard, tools
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.audit.signer import key_path
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b import atomic
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.pathguard import PathRefused
from tests.conftest import make_cfg
from tests.fixtures.pathsize import path_of_bytes
from tests.k1b_support import ScriptedLLM
from tests.test_k1b_replay import HAPPY, Env


def _link(target, link, *, directory=False):
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")


def _event(event_id: str) -> AuditEvent:
    item = AuditEvent(run_id="r1", domain="run", operation="state", principal="p", source="runtime")
    item.event_id = event_id
    return item


def _refused(call, rule: str) -> PathRefused:
    with pytest.raises(PathRefused) as info:
        call()
    assert info.value.rule == rule
    return info.value


# ------------------------------------------------------------ A: the whole path, 4095 bytes and not 4096

LIMIT = pathguard.MAX_PATH_BYTES


def _relative_target(folder: Path, total: int) -> str:
    """A link target that is short enough for the system to store but resolves, from ``folder``, to ``total`` bytes."""
    return path_of_bytes(str(folder), total)[len(str(folder)) + 1 :]


def test_the_limit_is_4095_because_the_system_counts_the_closing_nul():
    assert LIMIT == 4095


@pytest.mark.parametrize("kind", ["dir", "file"])
def test_a_typed_path_of_4095_bytes_is_accepted_and_4096_is_refused(tmp_path, kind):
    call = pathguard.operator_dir if kind == "dir" else pathguard.operator_file
    ok = path_of_bytes(str(tmp_path), LIMIT)
    assert len(ok.encode()) == LIMIT
    assert call(ok, what="typed path", must_exist=False)
    over = path_of_bytes(str(tmp_path), LIMIT + 1)
    _refused(lambda: call(over, what="typed path", must_exist=False), "R5")


def test_pin_a_join_of_4095_bytes_is_accepted_and_4096_is_refused(tmp_path):
    base = path_of_bytes(str(tmp_path), LIMIT - 60)
    ok = pathguard.join(base, "a" * 59, what="joined path")
    assert len(str(ok).encode()) == LIMIT
    _refused(lambda: pathguard.join(base, "a" * 60, what="joined path"), "R5")


def test_pin_a_join_measures_the_whole_path_not_only_each_name(tmp_path):
    base = path_of_bytes(str(tmp_path), LIMIT - 3)
    _refused(lambda: pathguard.join(base, "a" * 10, what="joined path"), "R5")


def test_a_link_that_leads_to_a_path_over_the_limit_is_refused_after_resolving(tmp_path):
    link = tmp_path / "go"
    _link(_relative_target(tmp_path, LIMIT + 40), link, directory=True)
    err = _refused(
        lambda: pathguard.operator_dir(link, what="typed folder", must_exist=False), "R5"
    )
    assert str(tmp_path) not in str(err)


def test_a_link_that_leads_to_a_path_of_exactly_the_limit_is_accepted(tmp_path):
    link = tmp_path / "go"
    _link(_relative_target(tmp_path, LIMIT), link, directory=True)
    got = pathguard.operator_dir(link, what="typed folder", must_exist=False)
    assert len(str(got).encode()) == LIMIT


def test_a_link_that_leads_to_a_name_over_255_bytes_is_refused_after_resolving(tmp_path):
    link = tmp_path / "go"
    _link(str(tmp_path / ("n" * 256)), link, directory=True)
    _refused(lambda: pathguard.operator_dir(link, what="typed folder", must_exist=False), "R5")


def test_a_tool_module_path_is_measured_whole_before_the_file_is_asked_about(tmp_path, monkeypatch):
    """The parts each fit a name, the whole path does not: a refusal, never an OSError that carries the path."""
    module = ".".join(f"m{n}" + "a" * 198 for n in range(21))
    monkeypatch.setattr(sys, "path", [str(tmp_path)])
    err = _refused(lambda: tools._module_files(module), "R5")
    assert str(tmp_path) not in str(err)


def test_pin_a_tool_module_inside_the_limit_is_still_found(tmp_path, monkeypatch):
    (tmp_path / "pkg_seven").mkdir()
    (tmp_path / "pkg_seven" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg_seven" / "leaf.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "path", [str(tmp_path)])
    got = tools._module_files("pkg_seven.leaf")
    assert [name for name, _ in got] == ["pkg_seven", "pkg_seven.leaf"]


# ------------------------------------------------------------ B: an error of the system is one fixed refusal


def _raise(exc: BaseException):
    def call():
        raise exc

    return call


@pytest.mark.parametrize(
    "exc",
    [
        OSError(errno.EACCES, "no right"),
        ValueError("embedded null byte"),
        TypeError("not a path"),
        RecursionError("too deep"),
        RuntimeError("Symlink loop from 'somewhere'"),
    ],
    ids=["oserror", "valueerror", "typeerror", "recursion", "symlink-loop"],
)
def test_pin_each_listed_error_of_the_system_is_a_refusal_with_no_cause_no_context_no_value(exc):
    err = _refused(lambda: pathguard._os(_raise(exc), "typed path"), "R10")
    assert err.__cause__ is None and err.__context__ is None
    assert "somewhere" not in str(err) and "no right" not in str(err)


def test_a_surprise_runtimeerror_is_not_hidden_as_a_path_refusal():
    with pytest.raises(RuntimeError, match="something else"):
        pathguard._os(_raise(RuntimeError("something else")), "typed path")


def test_an_error_while_looking_into_a_folder_is_a_refusal_with_no_path(tmp_path, monkeypatch):
    (tmp_path / "f").write_text("x", encoding="utf-8")

    def deny(self):
        raise PermissionError(errno.EACCES, "denied", str(self))

    monkeypatch.setattr(Path, "iterdir", deny)
    err = _refused(lambda: pathguard.has_entries(tmp_path, what="some folder"), "R10")
    assert str(tmp_path) not in str(err) and err.__context__ is None


def test_has_entries_says_yes_for_a_folder_with_something_and_no_for_empty_or_missing(tmp_path):
    (tmp_path / "full").mkdir()
    (tmp_path / "full" / "f").write_text("x", encoding="utf-8")
    (tmp_path / "empty").mkdir()
    assert pathguard.has_entries(tmp_path / "full", what="a folder") is True
    assert pathguard.has_entries(tmp_path / "empty", what="a folder") is False
    assert pathguard.has_entries(tmp_path / "missing", what="a folder") is False


def test_pin_a_folder_that_cannot_be_made_under_a_regular_file_is_a_refusal_with_no_path(tmp_path):
    (tmp_path / "plain").write_text("x", encoding="utf-8")
    err = _refused(
        lambda: pathguard.operator_dir(
            tmp_path / "plain" / "sub", what="made folder", must_exist=False, create_mode=0o700
        ),
        "R10",
    )
    assert str(tmp_path) not in str(err) and err.__context__ is None


def test_pin_a_folder_made_by_operator_dir_is_made_with_its_parents_and_returned_resolved(tmp_path):
    got = pathguard.operator_dir(
        tmp_path / "a" / "b", what="made folder", must_exist=False, create_mode=0o700
    )
    assert got == (tmp_path / "a" / "b").resolve() and got.is_dir()


# ------------------------------------------------------------ C: callers with no cause and no context


def _no_space(*_a, **_k):
    raise OSError(errno.ENOSPC, "disk full", "/some/where/file")


def test_a_failed_temp_file_open_leaves_no_cause_and_no_context(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "open", _no_space)
    with pytest.raises(OSError) as info:
        atomic.atomic_write(tmp_path, "out.md", "x")
    assert info.value.__cause__ is None and info.value.__context__ is None
    assert "/some/where" not in str(info.value) and str(tmp_path) not in str(info.value)


def test_a_failed_replace_leaves_no_cause_no_context_and_no_temp_file(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "replace", _no_space)
    with pytest.raises(OSError) as info:
        atomic.atomic_write(tmp_path, "out.md", "x")
    assert info.value.__cause__ is None and info.value.__context__ is None
    assert "/some/where" not in str(info.value)
    assert list(tmp_path.iterdir()) == []


def test_a_target_name_that_is_a_folder_is_refused_even_when_the_folder_test_raises(
    tmp_path, monkeypatch
):
    (tmp_path / "out.md").mkdir()

    def boom(self):
        raise OSError(errno.EIO, "io", str(self))

    monkeypatch.setattr(Path, "is_dir", boom)
    err = _refused(lambda: atomic.atomic_write(tmp_path, "out.md", "x"), "R13")
    assert str(tmp_path) not in str(err)


def test_a_key_path_with_a_home_folder_that_cannot_be_found_has_no_cause_and_no_context(tmp_path):
    with pytest.raises(ValueError, match="home folder not found") as info:
        key_path(Path("~no_such_user_for_sure_zq/k.pem"), tmp_path)
    assert info.value.__cause__ is None and info.value.__context__ is None


@pytest.mark.parametrize(
    "bad", [123, "k" + chr(0) + ".pem"], ids=["not-a-path-typeerror", "nul-valueerror"]
)
def test_a_key_path_that_is_not_a_valid_path_is_one_fixed_text_with_no_context(tmp_path, bad):
    with pytest.raises((ValueError, PathRefused)) as info:
        key_path(bad, tmp_path)
    assert info.value.__cause__ is None and info.value.__context__ is None
    assert str(tmp_path) not in str(info.value)


def test_a_nul_in_a_home_name_is_the_fixed_text_for_a_path_that_is_not_valid(tmp_path):
    with pytest.raises(ValueError, match=r"\(not a valid path\)") as info:
        key_path(Path("~" + chr(0) + "x/k.pem"), tmp_path)
    assert info.value.__cause__ is None and info.value.__context__ is None


def test_a_key_path_whose_link_test_raises_is_one_fixed_text_with_no_context(tmp_path, monkeypatch):
    def boom(self):
        raise OSError(errno.ENAMETOOLONG, "long", str(self))

    monkeypatch.setattr(Path, "is_symlink", boom)
    with pytest.raises(ValueError, match="cannot be checked") as info:
        key_path(tmp_path / "k.pem", tmp_path)
    assert info.value.__cause__ is None and info.value.__context__ is None
    assert str(tmp_path) not in str(info.value)


@pytest.mark.parametrize(
    ("name", "rule"),
    [("k.pem.", "R6"), ("CON", "R7"), ("k:x", "R3")],
    ids=["dot", "device", "colon"],
)
def test_a_key_file_name_with_a_rule_broken_is_refused_by_name(tmp_path, name, rule):
    err = _refused(lambda: key_path(tmp_path / name, tmp_path), rule)
    assert str(tmp_path) not in str(err)


# ------------------------------------------------------------ D: the audit id is tested once, for both writers


def test_an_id_ending_in_a_dot_is_usable_because_only_the_object_name_is_checked():
    """``<id>.json`` is the name written; the outbox name ``.tmp-<id>`` ends in the dot and was refused (R6) although the
    object name was fine: one test for both writers, on the name that is really used."""
    assert LocalDirSink._id_refused(_event("abc.")) is False
    assert LocalDirSink._id_refused(_event("abc" + "/")) is True
    assert LocalDirSink._id_refused(_event("i" * 251)) is True


# ------------------------------------------------------------ E: a token file in a projected volume


def _projected(folder: Path) -> Path:
    stamp = folder / "2026_11_13_stamp"
    stamp.mkdir()
    (stamp / "token").write_text("t", encoding="utf-8")
    _link("2026_11_13_stamp", folder / "..data", directory=True)
    _link("..data/token", folder / "token")
    return folder / "token"


def test_pin_a_token_file_that_is_a_link_through_a_projected_volume_is_read(tmp_path):
    got = pathguard.operator_file(_projected(tmp_path), what="token file")
    assert got.name == "token" and got.parent.name == "2026_11_13_stamp"


def test_pin_a_name_that_starts_with_two_dots_is_a_plain_name():
    assert pathguard.component("..data", what="a name") == "..data"
    _refused(lambda: pathguard.component("..", what="a name"), "R1")


def test_pin_a_key_file_inside_a_folder_called_dot_dot_data_is_accepted(tmp_path):
    (tmp_path / "..data").mkdir()
    got = key_path(tmp_path / "..data" / "k.pem", tmp_path)
    assert got.name == "k.pem" and got.parent.name == "..data"


def test_pin_a_key_file_that_is_a_link_through_a_projected_volume_is_refused_in_words(tmp_path):
    with pytest.raises(ValueError, match="symlink") as info:
        key_path(_projected(tmp_path), tmp_path)
    assert str(tmp_path) not in str(info.value)


def test_pin_a_link_out_of_the_key_folder_is_still_refused_with_its_own_words(tmp_path):
    folder = tmp_path / "keys"
    folder.mkdir()
    (tmp_path / "outside").mkdir()
    _link("../outside", folder / "..data", directory=True)
    with pytest.raises(ValueError, match="outside the key folder") as info:
        key_path(folder / "..data" / "k.pem", folder)
    assert str(tmp_path) not in str(info.value)


# ------------------------------------------------------------ F: the folder checks of replay and score


def test_pin_a_report_folder_that_is_a_file_is_refused_in_the_words_of_the_command(tmp_path):
    (tmp_path / "plain").write_text("x", encoding="utf-8")
    with pytest.raises(PathRefused) as info:
        pathguard.operator_dir(tmp_path / "plain", what="score report folder", must_exist=False)
    err = pathguard.mapped(info.value, R11="score report folder exists and is not empty")
    assert isinstance(err, ConfigError) and not isinstance(err, PathRefused)
    assert str(err) == "score report folder exists and is not empty"


def test_a_report_folder_that_turns_into_a_file_before_it_is_made_is_a_refusal_with_no_path(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    from hadavin_sdk import cli
    from hadavin_sdk.k1b import score as score_mod
    from hadavin_sdk.k1b.score import REPORT_DIR

    out = tmp_path / "out"
    out.mkdir()

    def fake_score(*_a, **_k):  # runs after the first folder check and before the folder is made
        (out / REPORT_DIR).write_text("x", encoding="utf-8")
        return SimpleNamespace(answers_sha256="a", outputs_digest="b", runs=[])

    monkeypatch.setattr(score_mod, "score", fake_score)

    class Audit:
        def emit(self, *a, **k): ...

        def emit_outcome(self, *a, **k): ...

    args = SimpleNamespace(
        outputs=out, answers=tmp_path / "a", cause_list=tmp_path, bundles=tmp_path
    )
    with pytest.raises(PathRefused) as caught:
        cli.score_cmd(Audit(), args)
    assert str(tmp_path) not in str(caught.value)


@pytest.fixture
def replay_env(tmp_path):
    return Env(
        tmp_path, make_cfg(tmp_path)
    )  # the config helper, imported: the mutant runner runs without conftest


def test_a_run_folder_that_turns_into_a_file_is_a_refusal_in_words_with_no_path(
    replay_env, monkeypatch
):
    from hadavin_sdk.k1b import loop

    real = loop.Budget

    def plant(*a, **k):  # runs after the output folder was made and before the run folder is
        (replay_env.out / "run1").write_text("x", encoding="utf-8")
        return real(*a, **k)

    monkeypatch.setattr(loop, "Budget", plant)
    with pytest.raises(PathRefused) as caught:
        replay_env.run(ScriptedLLM(HAPPY()))
    assert str(replay_env.tmp) not in str(caught.value)


def test_an_output_folder_that_turns_into_a_file_is_a_refusal_in_words_with_no_path(
    replay_env, monkeypatch
):
    from hadavin_sdk.k1b import replay as replay_mod

    real = replay_mod.bundle_set_sha256

    def plant(*a, **k):  # runs after the first folder check and before the folder is made
        replay_env.out.write_text("x", encoding="utf-8")
        return real(*a, **k)

    monkeypatch.setattr(replay_mod, "bundle_set_sha256", plant)
    with pytest.raises(PathRefused) as caught:
        replay_env.run(ScriptedLLM(HAPPY()))
    assert str(replay_env.tmp) not in str(caught.value)
