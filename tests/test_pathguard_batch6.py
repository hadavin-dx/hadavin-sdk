"""pathguard batch 6: links an operator typed, names that grow after the check, errors of the system in the key folder,
the audit sink edges, and a header test that counts the label sentences from the files themselves.

Labels, measured by real runs on (a) origin/main source plus this change's ``pathguard.py`` and (b) origin/main as it is (``pathguard`` does not exist on main, so for a file that imports it an empty stand-in module let the file load; a test that calls the module fails there): ``test_control_*`` passes on (a) and (b); ``test_pin_*`` passes on (a) and fails on (b); every other name fails on (a). This file: 3 control, 6 pin, 29 other. Nothing here says a test "fails on old main".

Fake paths only; names are built from parts.
"""

from __future__ import annotations

import importlib
import os
import re
from pathlib import Path

import pytest

from hadavin_sdk import pathguard
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.audit.signer import generate_key, key_path, load_private_key, load_public_key
from hadavin_sdk.config import confined
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.pathguard import PathRefused

NUL = chr(0)
ROOT = Path(__file__).resolve().parents[1]
LABELLED = (
    "test_pathguard",
    "test_pathguard_batch3",
    "test_pathguard_batch4",
    "test_pathguard_batch5",
    "test_pathguard_batch6",
    "test_pathguard_callers",
    "test_pathguard_sites",
    "test_pathguard_tripwire",
    "test_changelog_claims",
)


def _link(target, link, *, directory=False):
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")


def _event(event_id: str) -> AuditEvent:
    item = AuditEvent(run_id="r1", domain="run", operation="state", principal="p", source="runtime")
    item.event_id = event_id
    return item


# ------------------------------------------------------------ A: a link an operator typed (key files)


def _pair(folder: Path) -> tuple[Path, Path]:
    generate_key(folder / "k.pem", folder / "k.pub", base=folder)
    return folder / "k.pem", folder / "k.pub"


def test_control_a_key_file_that_is_a_link_to_a_file_in_the_same_folder_is_read(tmp_path):
    """A mount such as Kubernetes ``token -> ..data/token`` keeps its target inside the folder: read as before."""
    _private, public = _pair(tmp_path)
    _link("k.pem", tmp_path / "again.pem")
    _link("k.pub", tmp_path / "again.pub")
    assert load_private_key(tmp_path / "again.pem") is not None
    assert load_public_key(tmp_path / "again.pub") == load_public_key(public)


def test_a_key_file_that_is_a_link_to_another_folder_is_refused_in_words_with_no_path(tmp_path):
    """The case the CHANGELOG names: ``/run/secrets/key -> /run/secrets.d/1/key`` worked on main and is refused now."""
    keys, mount = tmp_path / "keys", tmp_path / "mount"
    keys.mkdir()
    mount.mkdir()
    private, public = _pair(keys)
    _link(private, mount / "linked.pem")
    _link(public, mount / "linked.pub")
    for call, name in ((load_private_key, "linked.pem"), (load_public_key, "linked.pub")):
        with pytest.raises(PathRefused) as caught:
            call(mount / name)
        assert caught.value.rule == "R8" and str(tmp_path) not in str(caught.value)


# ------------------------------------------------------------ B: a name that grows after the check


@pytest.mark.parametrize("size", range(250, 258))
def test_a_tool_module_part_that_fits_a_name_but_not_with_py_is_a_config_error(size):
    """The file looked up is ``<part>.py``: 3 bytes more than the part. 253 to 255 bytes used to reach ``is_file``."""
    from hadavin_sdk import tools

    text = "a" * size + ".b"
    if size + len(".py") > pathguard.MAX_COMPONENT_BYTES:
        with pytest.raises(ConfigError, match="each part at most 252 bytes"):
            tools._module_files(text)
    else:
        with pytest.raises(ConfigError, match="cannot be found"):
            tools._module_files(text)
    for last in (size,):  # the last part is the one that becomes ``<part>.py``
        with pytest.raises(ConfigError) as caught:
            tools._module_files("b." + "a" * last)
        assert "File name too long" not in str(caught.value)


@pytest.mark.parametrize("size", range(248, 258))
def test_a_golden_file_name_built_from_an_agent_id_is_refused_by_length_never_an_oserror(
    tmp_path, size
):
    """``<agent id>.jsonl`` is 6 bytes more than the id; ``confined`` (what ``registry.golden_path`` calls) must refuse a
    final name over 255 bytes in words, so the ``is_file`` after it cannot raise on 3.12."""
    name = "a" * size + ".jsonl"
    if len(name) > pathguard.MAX_COMPONENT_BYTES:
        with pytest.raises(ConfigError, match="too long"):
            confined(tmp_path, name)
    else:
        assert confined(tmp_path, name).name == name
        assert not confined(tmp_path, name).is_file()


def test_pin_a_name_over_255_bytes_in_the_middle_of_a_typed_path_is_refused_by_length(tmp_path):
    for call in (
        lambda: pathguard.operator_dir(tmp_path / ("m" * 300) / "x", what="n", must_exist=False),
        lambda: pathguard.operator_file(tmp_path / ("m" * 300) / "x", what="n", must_exist=False),
        lambda: pathguard.inside(tmp_path, tmp_path / ("m" * 256) / "x", what="n"),
    ):
        with pytest.raises(PathRefused) as caught:
            call()
        assert caught.value.rule == "R5" and str(caught.value) == "n: too long"


# ------------------------------------------------------------ B: key folder, errors of the system


def test_a_key_folder_under_a_regular_file_is_a_refusal_with_no_path(tmp_path):
    (tmp_path / "plain").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError) as caught:
        key_path(tmp_path / "plain" / "keys" / "k.pem", tmp_path / "plain" / "keys")
    assert str(tmp_path) not in str(caught.value) and "Not a directory" not in str(caught.value)
    assert not isinstance(caught.value, OSError)


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason="root can write into a folder without the right: the permission error cannot be made here",
)
def test_a_key_folder_that_cannot_be_made_is_a_refusal_with_no_path(tmp_path):
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)
    try:
        with pytest.raises(ValueError) as caught:
            key_path(locked / "keys" / "k.pem", locked / "keys")
    finally:
        locked.chmod(0o700)
    assert str(tmp_path) not in str(caught.value) and "Permission denied" not in str(caught.value)


def test_a_nul_in_the_key_file_is_refused_before_any_folder_is_made(tmp_path):
    folder = tmp_path / "newkeys"
    with pytest.raises(PathRefused) as caught:
        key_path(Path(str(folder / "k") + NUL + ".pem"), folder)
    assert caught.value.rule == "R4" and not folder.exists(), "a folder was made before the refusal"


def test_a_key_file_name_over_255_bytes_is_refused_before_any_folder_is_made(tmp_path):
    folder = tmp_path / "newkeys"
    with pytest.raises(PathRefused) as caught:
        key_path(folder / ("k" * 256), folder)
    assert caught.value.rule == "R5" and not folder.exists()


def test_each_cause_of_an_unreadable_key_path_has_its_own_fixed_text(tmp_path):
    texts = []
    for typed in (Path("~" + "nouser" * 3 + "/k.pem"), Path("~" + NUL + "/k.pem")):
        with pytest.raises(ValueError) as caught:
            key_path(typed, tmp_path)
        texts.append(str(caught.value))
    assert "home folder not found" in texts[0] and "not a valid path" in texts[1], texts


def test_pin_an_error_of_the_system_is_a_fixed_refusal_with_no_cause_no_context_and_no_path(
    tmp_path,
):
    (tmp_path / "plain").write_text("x", encoding="utf-8")
    with pytest.raises(PathRefused) as caught:
        pathguard.operator_dir(
            tmp_path / "plain" / "sub", what="n", must_exist=False, create_mode=0o700
        )
    exc = caught.value
    assert str(exc) == "n: cannot be resolved" and exc.rule == "R10"
    assert exc.__cause__ is None and exc.__context__ is None, (
        "the system's error is still reachable"
    )
    assert all(str(tmp_path) not in str(a) for a in exc.args)


@pytest.mark.parametrize("bad", [None, b"bytes", 7, ["a"]])
def test_pin_a_value_that_is_not_a_path_is_a_refusal_not_a_typeerror(tmp_path, bad):
    for call in (
        lambda: pathguard.operator_dir(bad, what="n", must_exist=False),
        lambda: pathguard.operator_file(bad, what="n", must_exist=False),
        lambda: pathguard.join(bad, "x", what="n"),
        lambda: pathguard.inside(tmp_path, bad, what="n"),
        lambda: pathguard.inside(bad, tmp_path, what="n"),
    ):
        with pytest.raises(PathRefused) as caught:
            call()
        assert caught.value.rule == "R10" and caught.value.__context__ is None


# ------------------------------------------------------------ D and E: the audit sink


def _cannot_write_objects(sink: LocalDirSink) -> None:
    """Make the object store unusable without a refusal from the guard: the folder is a file (``mkdir`` fails)."""
    sink.root.mkdir(parents=True, exist_ok=True)
    sink.objects.write_text("not a folder", encoding="utf-8")


def test_an_outbox_file_that_is_a_link_out_is_refused_and_the_outcome_stays_in_memory(tmp_path):
    sink = LocalDirSink(tmp_path / "aud")
    _cannot_write_objects(sink)
    sink.outbox.mkdir(parents=True, exist_ok=True)
    victim = tmp_path / "elsewhere.txt"
    victim.write_text("keep me", encoding="utf-8")
    _link(victim, sink.outbox / "abc.json")
    event = _event("abc")
    assert sink.write_outcome(event) is None
    assert victim.read_text(encoding="utf-8") == "keep me", "the link target was overwritten"
    assert (sink.outbox / "abc.json").is_symlink(), "the link in the outbox was replaced by a file"
    assert sink._pending == [event] and sink.refused_events == 0


def test_an_outcome_whose_object_file_is_a_link_out_takes_the_outbox_path_not_the_drop(tmp_path):
    """Real trigger: ``objects/<id>.json`` is a link out, so ``_write`` is refused with R8 (a refusal that is not about the
    id). On abb3e90a every refusal dropped the record and counted it as a bad id; the outbox path keeps it."""
    sink = LocalDirSink(tmp_path / "aud")
    sink.objects.mkdir(parents=True, exist_ok=True)
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text("{}", encoding="utf-8")
    _link(elsewhere, sink.objects / "abc.json")
    assert sink.write_outcome(_event("abc")) is None
    assert sink.refused_events == 0, "an outcome with a good id was counted as refused"
    assert [p.name for p in sink.outbox.glob("*.json")] == ["abc.json"], "the record was lost"
    assert elsewhere.read_text(encoding="utf-8") == "{}"


def test_an_outcome_over_the_path_limit_is_kept_in_memory_not_dropped(tmp_path):
    """Real trigger for R5: the id is a plain name, the whole path is over 4096 bytes. On abb3e90a it was dropped."""
    deep = tmp_path.joinpath(*["d" * 200] * 20)
    sink = LocalDirSink(deep)
    event = _event("i" * 200)
    assert sink.write_outcome(event) is None
    assert sink.refused_events == 0 and sink._pending == [event]


def test_an_id_whose_temp_name_is_refused_is_rejected_up_front_with_the_id_refusal(tmp_path):
    """``.tmp-<id>`` ends with the id: an id ending in a dot or a space passes as ``<id>.json`` but not as the temp name."""
    sink = LocalDirSink(tmp_path / "aud")
    for bad in ("abc.", "abc "):
        assert sink.write_outcome(_event(bad)) is None
    assert sink.refused_events == 2 and sink._pending == []


def test_the_intent_text_says_event_id_only_for_an_id_refusal(tmp_path):
    from hadavin_sdk.audit.protocol import AuditUnavailable

    sink = LocalDirSink(tmp_path / "aud")
    with pytest.raises(AuditUnavailable, match=r"event id refused \(R\d+\)"):
        sink.write_intent(_event("c?d"))
    deep = LocalDirSink(tmp_path.joinpath(*["d" * 200] * 20))
    with pytest.raises(AuditUnavailable, match=r"path refused \(R5\)") as caught:
        deep.write_intent(_event("i" * 200))
    assert "event id" not in str(caught.value)


# ------------------------------------------------------------ C: the label sentences are counted from the files


def _ids(name: str) -> list[str]:
    """The test ids of one file, as pytest would make them: a function counts once per parameter (stacked
    ``parametrize`` marks multiply). The module is imported, not run."""
    try:
        module = importlib.import_module(f"tests.{name}")
    except (
        FileNotFoundError
    ):  # the mutant runner's copy of the tree has no CHANGELOG.md, which the claims file reads
        pytest.skip(f"{name} reads a file that is not in this copy of the tree")
    out: list[str] = []
    for attr, fn in sorted(vars(module).items()):
        if not (attr.startswith("test_") and callable(fn)):
            continue
        count = 1
        for mark in getattr(fn, "pytestmark", []):
            if mark.name == "parametrize":
                count *= len(list(mark.args[1]))
        out += [f"{attr}[{i}]" for i in range(count)]
    return out


def _collected() -> dict[str, list[str]]:
    return {name: _ids(name) for name in LABELLED}


def _label(test_id: str) -> str:
    name = test_id.split("[")[0].split("::")[-1]
    return (
        "control"
        if name.startswith("test_control_")
        else "pin"
        if name.startswith("test_pin_")
        else "other"
    )


def test_control_every_header_count_is_the_count_of_ids_in_its_file():
    """Each labelled file says ``This file: N control, N pin, N other`` (test ids, a parametrized test counts once per
    parameter). The numbers are derived here from the collected ids, so a header cannot drift from its file."""
    ids = _collected()
    wrong = []
    for name in LABELLED:
        doc = (ROOT / "tests" / f"{name}.py").read_text(encoding="utf-8")
        m = re.search(r"This file: (\d+) control, (\d+) pin, (\d+) other", doc)
        assert m, f"{name}: no counts sentence in the header"
        said = tuple(int(x) for x in m.groups())
        found = tuple(
            sum(_label(i) == k for i in ids.get(name, [])) for k in ("control", "pin", "other")
        )
        if said != found:
            wrong.append((name, said, found))
    assert not wrong, wrong


def test_control_a_header_count_test_sees_the_ids_of_every_labelled_file():
    ids = _collected()
    assert set(ids) == set(LABELLED) and all(ids[name] for name in LABELLED)
