"""pathguard at every converted site: one test per site, plus the class tests (rules R4, R5, R8, R10, R12 and the
function-level checks). A NUL or other control character in a path an operator typed, or a name that came from data,
must be refused with ``PathRefused`` (a ``ConfigError``), never reach the file system and never put the value in the text.

Fake paths are built from parts. FAIL-BEFORE: each test below ran on ddf1d584 (see handover evidence); the tests marked
test_control_* pass on both.
"""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest

from hadavin_sdk import pathguard
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b.atomic import atomic_write
from hadavin_sdk.pathguard import PathRefused

NUL = "\x00"
BAD_TEXTS = ["a" + chr(code) + "b" for code in (0x00, 0x1F, 0x7F, 0x85, 0x202E, 0x200B, 0xFEFF)]


def _refused(rule: str, fn, *args, **kwargs) -> PathRefused:
    """``fn`` must raise ``PathRefused`` with ``rule``; any other outcome is an assertion failure (so a mutant that lets
    the value through to the file system is reported as a failed check, not as a crash)."""
    with pytest.raises(
        PathRefused
    ) as caught:  # any other error, or none, fails here with pytest's own message
        fn(*args, **kwargs)
    refused = caught.value
    assert refused.rule == rule, f"wrong rule {refused.rule}, wanted {rule}"
    assert isinstance(refused, ConfigError)
    assert isinstance(refused, ValueError)
    return refused


# ---------------------------------------------------------------- the choke point itself


def test_every_public_function_refuses_a_control_character_explicitly(tmp_path):
    for text in BAD_TEXTS:
        _refused("R4", pathguard.component, text, what="n")
        _refused("R4", pathguard.join, tmp_path, text, what="n")
        _refused("R4", pathguard.inside, tmp_path, str(tmp_path) + "/" + text, what="n")
        _refused("R4", pathguard.operator_dir, str(tmp_path) + "/" + text, what="n")
        _refused("R4", pathguard.operator_file, str(tmp_path) + "/" + text, what="n")
        _refused("R4", pathguard.operator_text, str(tmp_path) + "/" + text, what="n")


def test_a_control_character_in_the_base_is_refused_not_only_in_the_names(tmp_path):
    _refused("R4", pathguard.join, str(tmp_path) + NUL, "x", what="n")


def test_the_nul_is_refused_even_when_resolve_would_not_raise(tmp_path, monkeypatch):
    # on Python 3.13 a NUL does not always make resolve() raise: the check must not depend on it
    monkeypatch.setattr(Path, "resolve", lambda self, strict=False: self)
    _refused("R4", pathguard.inside, tmp_path, str(tmp_path / ("a" + NUL)), what="n")
    _refused("R4", pathguard.operator_dir, str(tmp_path / ("a" + NUL)), what="n")


def test_windows_invalid_characters_are_refused_in_a_name_r12():
    for char in '<>"|?*':
        _refused("R12", pathguard.component, "a" + char + "b", what="n")


def test_a_symlink_loop_is_refused_or_fails_at_open_never_escapes(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    try:
        os.symlink(b, a)
        os.symlink(a, b)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    try:
        real = pathguard.join(tmp_path, "a", what="n")
    except PathRefused as exc:  # Python 3.12 raises on a loop: refused as R10
        assert exc.rule == "R10"
        return
    # Python 3.13 resolves a loop without raising: it stays inside the base and the open fails
    assert real.is_relative_to(tmp_path.resolve())
    with pytest.raises(OSError):
        real.read_bytes()


def test_pathrefused_keeps_its_rule_through_copy_and_pickle():
    exc = PathRefused("R8", "x: path escapes its folder")
    rebuilt = exc.__reduce__()[0](
        *exc.__reduce__()[1]
    )  # what pickle does, without loading untrusted bytes
    for clone in (copy.copy(exc), copy.deepcopy(exc), rebuilt):
        assert isinstance(clone, PathRefused), "a copy lost its class"
        assert clone.rule == "R8"
        assert str(clone) == str(exc)


def test_the_refusal_text_never_holds_the_value(tmp_path):
    secret = "tok" + "en-" + "abc"
    exc = _refused("R4", pathguard.component, secret + NUL, what="the name")
    assert secret not in str(exc)


def test_operator_file_without_must_exist_checks_shape_only(tmp_path):
    missing = tmp_path / "nope"
    assert pathguard.operator_file(missing, what="n", must_exist=False) == missing.resolve()
    _refused("R10", pathguard.operator_file, missing, what="n")
    _refused(
        "R11", pathguard.operator_file, tmp_path, what="n", must_exist=False
    )  # exists: not a file


def test_operator_text_returns_nothing_and_refuses_a_long_path():
    assert pathguard.operator_text("fine", what="n") is None
    _refused("R5", pathguard.operator_text, "a" * (pathguard.MAX_PATH_BYTES + 1), what="n")


def test_the_temp_name_is_the_write_name_plus_the_shared_extra(tmp_path, monkeypatch):
    seen = []
    real = os.open

    def spy(path, *args, **kwargs):
        seen.append(os.path.basename(path))
        return real(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", spy)
    name = "n" * pathguard.MAX_WRITE_NAME_BYTES
    atomic_write(tmp_path, name, "x")
    assert len(seen) == 1
    assert len(seen[0]) == pathguard.MAX_COMPONENT_BYTES, "temp name is not name + TEMP_EXTRA_BYTES"
    assert len(seen[0]) - len(name) == pathguard.TEMP_EXTRA_BYTES


def test_r10_a_nul_is_r4_and_a_missing_path_is_r10(tmp_path):
    _refused("R10", pathguard.inside, tmp_path, tmp_path / "missing", what="n", must_exist=True)
    _refused("R4", pathguard.inside, tmp_path, str(tmp_path / "x") + NUL, what="n", must_exist=True)


# ---------------------------------------------------------------- atomic_write (brief G)


def test_atomic_write_refuses_an_existing_symlink_as_the_final_name(tmp_path):
    from hadavin_sdk.k1b.atomic import atomic_write

    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")
    base = tmp_path / "base"
    base.mkdir()
    try:
        os.symlink(outside, base / "f.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    _refused("R8", atomic_write, base, "f.txt", "new")
    assert outside.read_text(encoding="utf-8") == "keep"
    assert (base / "f.txt").is_symlink()
    assert sorted(p.name for p in base.iterdir()) == ["f.txt"]  # no temp file left


def test_atomic_write_refuses_a_symlink_name_even_when_its_target_is_inside_the_folder(tmp_path):
    """The final name is a link to a file in the same folder: ``join`` accepts the resolved target, so only the
    explicit link check refuses it."""
    from hadavin_sdk.k1b.atomic import atomic_write

    (tmp_path / "real.txt").write_text("keep", encoding="utf-8")
    try:
        os.symlink(tmp_path / "real.txt", tmp_path / "f.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    exc = _refused("R8", atomic_write, tmp_path, "f.txt", "new")
    assert "a link is not replaced" in str(exc)
    assert (tmp_path / "real.txt").read_text(encoding="utf-8") == "keep"


def test_atomic_write_replaces_a_hard_link_and_leaves_the_other_name_alone(tmp_path):
    from hadavin_sdk.k1b.atomic import atomic_write

    first = tmp_path / "first.txt"
    first.write_text("old", encoding="utf-8")
    try:
        os.link(first, tmp_path / "second.txt")
    except (OSError, NotImplementedError):
        pytest.skip("hard links unavailable")
    atomic_write(tmp_path, "second.txt", "new")
    assert (tmp_path / "second.txt").read_text(encoding="utf-8") == "new"
    assert first.read_text(encoding="utf-8") == "old"  # control: documented in the module text


def test_atomic_write_refuses_the_longest_name_plus_one(tmp_path):
    from hadavin_sdk.k1b.atomic import atomic_write

    ok = "a" * pathguard.MAX_WRITE_NAME_BYTES
    atomic_write(tmp_path, ok, "x")
    assert (tmp_path / ok).read_text(encoding="utf-8") == "x"
    exc = _refused("R5", atomic_write, tmp_path, ok + "a", "x")
    assert str(exc).startswith(
        "output file:"
    )  # refused by the name limit, not later by the temp name


# ---------------------------------------------------------------- one test per converted site


def test_site_bundle_load_bundles_refuses_a_nul_folder_and_maps_missing(tmp_path):
    from hadavin_sdk.k1b.bundle import load_bundles

    _refused("R4", load_bundles, str(tmp_path) + NUL)
    with pytest.raises(ConfigError, match="bundles folder does not exist"):
        load_bundles(tmp_path / "missing")


def test_site_bundle_load_bundle_refuses_a_long_case_id_at_load(tmp_path):
    from hadavin_sdk.k1b.bundle import load_bundle

    folder = tmp_path / ("case-" + "1" * 250)
    folder.mkdir()
    with pytest.raises(ConfigError, match="too long"):
        load_bundle(folder)


def test_site_score_outputs_folder_nul_and_missing(tmp_path):
    from hadavin_sdk.k1b import score as score_mod

    _refused("R4", score_mod.outputs_dir, str(tmp_path) + NUL)
    with pytest.raises(ConfigError, match="outputs folder does not exist"):
        score_mod.outputs_dir(tmp_path / "missing")


def test_pin_site_score_answers_file_nul_is_a_config_error(tmp_path):
    from hadavin_sdk.k1b.causelist import CauseList
    from hadavin_sdk.k1b.score import load_answers

    cause = CauseList(frozenset(), frozenset(), "0" * 64, "0" * 64)
    with pytest.raises(ConfigError, match="answers file"):
        load_answers(Path(str(tmp_path / "a.json") + NUL), cause)


def test_site_score_check_layout_rechecks_its_own_folder(tmp_path):
    from hadavin_sdk.k1b.score import _check_layout

    _refused("R4", _check_layout, Path(str(tmp_path) + NUL), ["case-001"])


def test_site_causelist_folder_nul_gives_the_one_wording(tmp_path):
    from hadavin_sdk.k1b.causelist import load_cause_list

    with pytest.raises(ConfigError, match="directory not found"):
        load_cause_list(Path(str(tmp_path) + NUL))


def test_site_replay_output_folder_nul_is_refused(tmp_path):
    from hadavin_sdk.k1b.replay import outputs_files

    _refused("R4", outputs_files, Path(str(tmp_path) + NUL))


def test_site_signer_key_file_nul_and_missing(tmp_path):
    from hadavin_sdk.audit import signer

    _refused("R4", signer.load_private_key, Path(str(tmp_path / "k") + NUL))
    _refused("R4", signer.load_public_key, Path(str(tmp_path / "k") + NUL))
    _refused("R10", signer.load_private_key, tmp_path / "missing")
    _refused("R10", signer.load_public_key, tmp_path / "missing")
    _refused("R11", signer.load_private_key, tmp_path)  # a folder, not a file


def test_site_signer_key_path_nul_is_refused_before_resolve(tmp_path):
    from hadavin_sdk.audit.signer import key_path

    _refused("R4", key_path, Path(str(tmp_path / "k") + NUL), tmp_path)


def test_site_local_dir_root_nul_and_event_id(tmp_path):
    from hadavin_sdk.audit import AuditUnavailable, LocalDirSink

    _refused("R4", LocalDirSink, Path(str(tmp_path) + NUL))
    sink = LocalDirSink(tmp_path / "aud")
    from hadavin_sdk.models import AuditEvent

    event = AuditEvent(
        run_id="r1", domain="run", operation="state", principal="p", source="runtime"
    )
    event.event_id = ".." + os.sep + "evil"
    with pytest.raises(AuditUnavailable):
        sink.write_intent(event)
    assert not (tmp_path / "evil.json").exists()


def test_site_config_root_nul(tmp_path):
    from hadavin_sdk.config import load_config

    _refused("R4", load_config, Path(str(tmp_path) + NUL))


def test_site_cli_config_flag_nul_is_refused(tmp_path, capsys):
    from hadavin_sdk.cli import main

    assert main(["--config", str(tmp_path) + NUL, "tick"]) == 2
    assert "control character" in capsys.readouterr().err


@pytest.mark.skipif(sys.platform == "win32", reason="posix modes")
def test_every_site_message_names_the_argument_not_the_value(tmp_path):
    exc = _refused("R4", pathguard.operator_dir, str(tmp_path) + NUL, what="outputs folder")
    assert str(exc) == "outputs folder: contains a control character"


def test_inside_checks_the_base_text_too(tmp_path):
    _refused("R4", pathguard.inside, str(tmp_path) + NUL, tmp_path / "x", what="n")


def test_operator_text_refuses_a_control_character():
    _refused("R4", pathguard.operator_text, "a" + NUL + "b", what="n")


# ---- sites that need a config folder or a fake vault (self-contained: the mutant runner runs without conftest.py) ----


def _replay_env(tmp_path):
    from tests.conftest import make_cfg
    from tests.test_k1b_replay import Env

    return Env(tmp_path, make_cfg(tmp_path))


def test_a_path_refusal_after_output_exists_still_leaves_failed_txt(tmp_path):
    """FAIL-BEFORE (brief C): PathRefused is a ConfigError, and replay used to re-raise every ConfigError without the
    marker, so a refusal mid-run left an unfinished folder that looked finished."""
    from tests.k1b_support import ScriptedLLM, submit_not_sure

    env = _replay_env(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("keep", encoding="utf-8")

    def plant_a_link(_):
        try:
            os.symlink(outside, env.out / "run1" / "case-002.json")
        except (OSError, NotImplementedError):
            pytest.skip("symlinks unavailable")
        return submit_not_sure()

    with pytest.raises(PathRefused):
        env.run(ScriptedLLM([submit_not_sure(), plant_a_link, submit_not_sure()]))
    assert (env.out / "FAILED.txt").exists(), "no FAILED.txt marker"
    text = (env.out / "FAILED.txt").read_text(encoding="utf-8")
    assert text.startswith("replay did not finish: PathRefused")
    assert outside.read_text(encoding="utf-8") == "keep"


def test_control_a_refusal_before_output_exists_writes_no_marker(tmp_path):
    """Control: passes before and after. A refusal before the folder exists wrote nothing, so no marker."""
    from tests.k1b_support import ScriptedLLM

    env = _replay_env(tmp_path)
    with pytest.raises(ConfigError):
        env.run(ScriptedLLM([]), k=0)
    assert not env.out.exists()


def test_score_with_a_nul_in_the_outputs_path_is_refused_with_exit_2(tmp_path, capsys):
    """FAIL-BEFORE (brief F): the text used to be a generic failure, not the one control-character refusal."""
    from hadavin_sdk.cli import main
    from tests.conftest import make_cfg

    code = main(
        [
            "--config",
            str(make_cfg(tmp_path)),
            "score",
            "--outputs",
            str(tmp_path / "out") + NUL,
            "--answers",
            str(tmp_path / "a.json"),
            "--cause-list",
            str(tmp_path),
            "--bundles",
            str(tmp_path),
        ]
    )
    assert code == 2
    assert "outputs folder: contains a control character" in capsys.readouterr().err


def test_vault_kubernetes_token_path_with_a_nul_is_a_config_error():
    """FAIL-BEFORE (brief A): the jwt path was opened without a guard; a NUL reached open()."""
    from hadavin_sdk.backends.factory import make
    from tests.contracts.vault_fake import fake_vault
    from tests.test_p4b_secrets import _settings

    vault = fake_vault()
    settings = _settings(vault, auth="kubernetes", role="hadavin", jwt_path="jwt" + NUL)
    with pytest.raises(ConfigError, match="cannot read"):
        make("secrets", settings).get("db")


def test_pin_site_local_dir_outbox_refuses_a_device_name_as_the_event_id(tmp_path):
    """``.tmp-con`` is a fine name and ``con.json`` is a device name: only the guard on the final name stops the write."""
    from hadavin_sdk.audit import LocalDirSink
    from hadavin_sdk.models import AuditEvent

    sink = LocalDirSink(tmp_path / "aud")
    event = AuditEvent(
        run_id="r1", domain="run", operation="state", principal="p", source="runtime"
    )
    event.event_id = "con"
    sink.write_outcome(event)  # never raises by contract
    assert not (sink.outbox / "con.json").exists(), "a device name reached the outbox"
