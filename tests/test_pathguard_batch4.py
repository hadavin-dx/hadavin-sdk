"""pathguard batch 4: the guard of each converted site that the earlier tests did not pin, the names an operator typed, and
the text of refusals. Each test names the mutant row of ``tests/pathguard_mutants.py`` that it kills.

Labels, measured by real runs on (a) origin/main source plus this change's ``pathguard.py`` and (b) origin/main as it is (``pathguard`` does not exist on main, so for a file that imports it an empty stand-in module let the file load; a test that calls the module fails there): ``test_control_*`` passes on (a) and (b); ``test_pin_*`` passes on (a) and fails on (b); every other name fails on (a). This file: 6 control, 0 pin, 26 other. Nothing here says a test "fails on old main".
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.pathguard import PathRefused

CTRL = chr(0x202E)
# names the data-name rules refuse (R12, R7, R6, R3, R7): since the join pattern is used at every flagged read, a name the
# caller typed is refused too. Each is paired with the words of its refusal.
OPERATOR_NAMES = {
    "a?b": "contains a character Windows does not allow",
    "con": "reserved device name",
    "x.": "ends with a dot or space",
    "vault:token": "contains a colon",
    "aux.txt": "reserved device name",
}


def _link(target, link, *, directory):
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")


def test_hash_files_refuses_a_name_with_a_colon_device_name_or_trailing_dot(tmp_path):
    """Mutant S-hashing the last check is the join: these names were hashed on main; now each is refused, with no name echoed."""
    from hadavin_sdk.hashing import hash_files

    for name, words in OPERATOR_NAMES.items():
        (tmp_path / name).write_text("x", encoding="utf-8")
        said = _said(hash_files, tmp_path, [name])
        assert said == f"PathRefused: hash file: {words}", f"wrong wording for {name!r}: {said}"


def test_secrets_file_refuses_a_secret_name_with_a_colon_device_name_or_trailing_dot(tmp_path):
    from hadavin_sdk.actions.secrets_file import MountedFileProvider

    for name, words in OPERATOR_NAMES.items():
        (tmp_path / name).write_text("value-1", encoding="utf-8")
        (tmp_path / name).chmod(0o400)
        said = _said(MountedFileProvider(tmp_path, 1).get, name)
        assert said == f"PathRefused: mounted secret: {words}", (
            f"wrong wording for {name!r}: {said}"
        )


@pytest.mark.parametrize("name", list(OPERATOR_NAMES))
def test_answers_file_name_with_a_colon_device_name_or_trailing_dot_is_refused(tmp_path, name):
    from hadavin_sdk.k1b.causelist import load_cause_list
    from hadavin_sdk.k1b.score import load_answers
    from tests.k1b_support import make_cause_list, write_answers

    cause = load_cause_list(make_cause_list(tmp_path / "c"))
    path = write_answers(tmp_path / name, {"case-001": ([("api", "bad_deploy")], False)})
    with pytest.raises(ConfigError, match="^answers file is missing or not valid JSON$"):
        load_answers(path, cause)


def _said(fn, *args, **kwargs) -> str:
    """The text of whatever ``fn`` raised ("" when nothing). The caller compares it whole, so the failing line is our message."""
    try:
        fn(*args, **kwargs)
    except (
        ConfigError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RuntimeError,
        AttributeError,
    ) as exc:  # the usual types: a wrong type must show as a wrong wording
        return f"{type(exc).__name__}: {exc}"
    return ""


def test_control_hash_files_keeps_the_escape_wording_for_a_missing_file_outside_the_folder(
    tmp_path,
):
    """Mutant S-hashing a file name is not confined: without ``confined`` a missing ``../x`` reads "not a file"."""
    from hadavin_sdk.hashing import hash_files

    said = _said(hash_files, tmp_path, ["../nope"])
    assert said == "ConfigError: path escapes its folder: ../nope", f"wrong wording: {said}"


def test_control_hash_files_says_not_a_file_for_a_missing_name_and_a_folder(tmp_path):
    """Mutant S-hashing the strict last check is removed: a folder named as a file is then read."""
    from hadavin_sdk.hashing import hash_files

    (tmp_path / "d").mkdir()
    for name in ("nope", "d"):
        said = _said(hash_files, tmp_path, [name])
        assert said == f"ConfigError: not a file: {name}", f"wrong wording: {said}"


def test_control_secrets_file_keeps_the_escape_wording_for_a_missing_name_outside_the_folder(
    tmp_path,
):
    from hadavin_sdk.actions.secrets_file import MountedFileProvider

    said = _said(MountedFileProvider(tmp_path, 1).get, "../nope")
    assert said == "ConfigError: path escapes its folder: ../nope", f"wrong wording: {said}"


def test_secrets_file_says_not_found_and_not_a_regular_file(tmp_path):
    """Mutant S-secrets_file the strict last check is removed: a folder named as a secret reaches the open."""
    from hadavin_sdk.actions.secrets_file import MountedFileProvider

    (tmp_path / "d").mkdir()
    provider = MountedFileProvider(tmp_path, 1)
    said = _said(provider.get, "nope")
    assert said == "ConfigError: secret 'nope' not found in the mounted folder", (
        f"wrong wording: {said}"
    )
    said = _said(provider.get, "d")
    assert said == "ConfigError: secret 'd' is not a regular file", f"wrong wording: {said}"


def test_local_dir_reconcile_leaves_a_corrupt_file_when_its_name_in_corrupt_is_a_link(tmp_path):
    """Mutant S-local_dir the second join into corrupt is removed: os.replace then replaces the planted link."""
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")
    sink.outbox.mkdir(parents=True)
    (sink.outbox / "bad.json").write_text("not json", encoding="utf-8")
    (sink.outbox / "corrupt").mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")
    _link(outside, sink.outbox / "corrupt" / "bad.json", directory=False)
    sink.reconcile()
    assert (sink.outbox / "bad.json").is_file(), "the file moved over a link a person planted"
    assert outside.read_text(encoding="utf-8") == "keep"


def test_local_dir_reconcile_leaves_a_link_to_a_file_outside_the_outbox(tmp_path):
    """A link inside the outbox that points outside it: ``join`` refuses it (R8), so it is left alone. Passes on any code that refuses."""
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")
    sink.outbox.mkdir(parents=True)
    real = sink.root / "real-event.json"
    real.write_text("not json", encoding="utf-8")
    _link(real, sink.outbox / "linked.json", directory=False)
    sink.reconcile()
    assert real.is_file()
    assert (sink.outbox / "linked.json").is_symlink()


def test_control_local_dir_reconcile_does_not_follow_a_link_to_another_file_in_the_outbox(tmp_path):
    """Mutant S-local_dir a link in the outbox is unlinked through its target: ``join`` accepts a link whose target is
    inside the outbox, so only the comparison with the plain name keeps the target from being moved or removed."""
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")
    sink.outbox.mkdir(parents=True)
    (sink.outbox / "target.json").write_text("not json", encoding="utf-8")
    _link(sink.outbox / "target.json", sink.outbox / "linked.json", directory=False)
    try:
        sink.reconcile()
    except OSError:
        raise AssertionError("reconcile followed a link to another file in the outbox") from None
    assert not (sink.outbox / "corrupt" / "linked.json").exists(), "reconcile followed a link"


def test_signer_key_path_refuses_a_parent_link_that_resolves_to_a_folder_with_a_control_character(
    tmp_path,
):
    """Mutant S-signer the containment call is removed: only ``inside`` sees the resolved path, which holds U+202E."""
    from hadavin_sdk.audit.signer import key_path

    folder = tmp_path / "keys"
    (folder / f"a{CTRL}b").mkdir(parents=True)
    _link(folder / f"a{CTRL}b", folder / "lnk", directory=True)
    with pytest.raises(PathRefused) as caught:
        key_path(folder / "lnk" / "k", folder)
    assert caught.value.rule == "R4"


def test_bundle_manifest_that_is_a_link_out_is_refused_with_the_pathguard_wording(tmp_path):
    """Mutant S-bundle the manifest join is removed: the link is then followed by ``is_file`` and refused later with
    another wording."""
    from hadavin_sdk.k1b.bundle import BundleError, load_bundle
    from tests.k1b_support import make_bundle

    case = make_bundle(tmp_path / "m", "case-001")
    stolen = tmp_path / "stolen.json"
    stolen.write_bytes((case / "manifest.json").read_bytes())
    (case / "manifest.json").unlink()
    _link(stolen, case / "manifest.json", directory=False)
    with pytest.raises(BundleError, match="bundle file: path escapes its folder"):
        load_bundle(case)


def test_bundle_folder_under_a_parent_with_a_control_character_is_refused(tmp_path):
    """Mutant S-bundle the bundle folder is not checked: a U+202E parent passes ``is_dir``."""
    from hadavin_sdk.k1b.bundle import load_bundle
    from tests.k1b_support import make_bundle

    case = make_bundle(tmp_path / f"p{CTRL}q", "case-001")
    said = _said(load_bundle, case)
    assert "bundle folder: contains a control character" in said, f"wrong wording: {said}"


def test_bundles_folder_entry_with_a_reserved_name_is_refused_as_a_path_refusal(tmp_path):
    """Mutant S-bundle the listed name is not checked: the entry would reach ``load_bundle`` and give a BundleError."""
    from hadavin_sdk.k1b.bundle import load_bundles

    (tmp_path / "con").mkdir()
    said = _said(load_bundles, tmp_path)
    assert said.startswith("PathRefused: bundle folder: "), f"wrong wording: {said}"


def test_score_check_layout_refuses_a_run_folder_that_is_a_link_out(tmp_path):
    """Mutant S-score the layout check joins without pathguard (a direct call: the later digest step refuses the same link
    with the same words, so only a direct call shows this guard)."""
    from hadavin_sdk.k1b.score import _check_layout

    out = tmp_path / "out"
    out.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "case-001.json").write_text("{}", encoding="utf-8")
    (elsewhere / "run.json").write_text("{}", encoding="utf-8")
    _link(elsewhere, out / "run1", directory=True)
    with pytest.raises(PathRefused) as caught:
        _check_layout(out, ["case-001"])
    assert caught.value.rule == "R8"


def test_replay_mark_failed_writes_nothing_into_a_folder_with_a_control_character(tmp_path):
    """Mutant S-replay the marker folder is not checked."""
    from hadavin_sdk.k1b.replay import _mark_failed

    folder = tmp_path / f"o{CTRL}"
    folder.mkdir()
    said = _said(
        _mark_failed, folder, RuntimeError("x")
    )  # best effort: it must neither write nor raise
    assert said == "", f"marking raised: {said}"
    assert list(folder.iterdir()) == [], "a marker was written into a refused folder"


def test_replay_keeps_the_first_error_and_names_it_when_marking_is_interrupted(
    tmp_path, monkeypatch
):
    from hadavin_sdk.k1b import replay as replay_mod

    class Stop(Exception):
        pass

    def boom(*_a, **_k):
        raise MemoryError("marking")

    def fail(*_a, progress=None, **_k):
        progress.output_created = True
        raise Stop("first")

    monkeypatch.setattr(replay_mod, "_replay", fail)
    monkeypatch.setattr(replay_mod, "_mark_failed", boom)
    with pytest.raises(MemoryError) as caught:
        replay_mod.replay(out=tmp_path)
    notes = getattr(caught.value, "__notes__", [])
    assert any("Stop" in n for n in notes), f"the first error carries no note: {notes}"


def test_replay_marking_failure_leaves_the_first_error_with_a_note(tmp_path, monkeypatch):
    from hadavin_sdk.k1b import replay as replay_mod

    def fail(*_a, progress=None, **_k):
        progress.output_created = True
        raise ValueError("first")

    def cannot(*_a, **_k):
        raise OSError("disk")

    monkeypatch.setattr(replay_mod, "_replay", fail)
    monkeypatch.setattr(replay_mod, "_mark_failed", cannot)
    with pytest.raises(ValueError, match="first") as caught:
        replay_mod.replay(out=tmp_path)
    notes = getattr(caught.value, "__notes__", [])
    assert any("FAILED.txt was not written (OSError)" in n for n in notes), (
        f"the first error carries no note: {notes}"
    )


def test_fake_llm_refuses_a_recording_name_that_is_a_link_out(tmp_path):
    """Mutant S-fake the recording name is not joined through pathguard; the test asserts the NAME, not only the folder."""
    import hashlib

    from hadavin_sdk.llm.fake import FakeLLM

    messages = [{"role": "user", "content": "hi"}]
    digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode("utf-8")).hexdigest()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    rec = tmp_path / "rec"
    rec.mkdir()
    _link(outside, rec / f"{digest}-1.json", directory=False)
    said = _said(FakeLLM(rec, {}).chat, messages, system="s", route="r")
    assert said.startswith("PathRefused: recording: "), f"wrong wording: {said}"


def test_atomic_write_creates_its_file_for_the_owner_only(tmp_path):
    from hadavin_sdk.k1b.atomic import atomic_write

    atomic_write(tmp_path, "r.md", "x")
    assert (tmp_path / "r.md").stat().st_mode & 0o777 == 0o600


def test_atomic_write_errors_carry_no_path(tmp_path, monkeypatch):
    from hadavin_sdk.k1b import atomic

    def deny(path, flags, mode=0o777):
        raise PermissionError(13, "Permission denied", str(path))

    monkeypatch.setattr(os, "open", deny)
    with pytest.raises(PermissionError) as caught:
        atomic.atomic_write(tmp_path, "r.md", "x")
    assert str(tmp_path) not in str(caught.value) and caught.value.filename is None


def test_atomic_write_rename_error_carries_no_path(tmp_path, monkeypatch):
    from hadavin_sdk.k1b import atomic

    def deny(src, dst):
        raise OSError(28, "No space left on device", str(src), None, str(dst))

    monkeypatch.setattr(os, "replace", deny)
    with pytest.raises(OSError) as caught:
        atomic.atomic_write(tmp_path, "r.md", "x")
    assert str(tmp_path) not in str(caught.value)
    assert list(tmp_path.iterdir()) == []


def test_hash_files_read_error_is_raised_without_a_chain(tmp_path, monkeypatch):
    from hadavin_sdk import hashing

    (tmp_path / "a.txt").write_text("x", encoding="utf-8")

    def deny(self):
        raise PermissionError(13, "denied", str(self))

    monkeypatch.setattr(Path, "read_bytes", deny)
    with pytest.raises(ConfigError, match="^cannot read: a.txt$") as caught:
        hashing.hash_files(tmp_path, ["a.txt"])
    assert caught.value.__cause__ is None and caught.value.__suppress_context__


def test_control_build_local_signer_error_prints_the_key_path_as_typed(tmp_path):
    from hadavin_sdk.audit.signer import build_local

    key = tmp_path / "typed-key.pem"
    key.write_text("not a pem", encoding="utf-8")
    link = tmp_path / "link.pem"
    _link(key, link, directory=False)
    settings = SimpleNamespace(
        private_key_path=str(link), private_key_secret_name=None, passphrase_secret_name=None
    )
    with pytest.raises(Exception) as caught:
        build_local(settings, SimpleNamespace(resolve=lambda _n: ""))
    assert "typed-key" not in str(caught.value), "the resolved path was printed"


def test_atomic_write_refuses_a_data_name_with_a_colon_or_a_device_name(tmp_path):
    """Mutant S-atomic the output name is not joined through pathguard: the name rules (R3, R7) sit in ``join``."""
    from hadavin_sdk.k1b.atomic import atomic_write

    for name in ("a:b", "con", "x."):
        said = _said(atomic_write, tmp_path, name, "x")
        assert said.startswith("PathRefused: output file: "), f"wrong wording for {name!r}: {said}"
    assert list(tmp_path.iterdir()) == []


def test_build_local_refuses_a_key_path_with_a_control_character_as_a_path_refusal(tmp_path):
    """Mutant S-signer the key file is not checked: a missing file would then be a plain FileNotFoundError."""
    from types import SimpleNamespace

    from hadavin_sdk.audit.signer import build_local

    settings = SimpleNamespace(
        passphrase_secret_name=None,
        private_key_secret_name=None,
        private_key_path=str(tmp_path / f"k{CTRL}"),
    )
    said = _said(build_local, settings, None)
    assert said.startswith("PathRefused: signer key file: contains a control character"), (
        f"wrong wording: {said}"
    )


def test_local_dir_object_names_are_joined_through_pathguard(tmp_path):
    """Mutant S-local_dir the object name is not joined through pathguard: ``_object`` is what keeps a key inside ``objects``."""
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")
    for key in ("a:b", "con", "../x", "x."):
        said = _said(sink._object, key)
        assert said.startswith("PathRefused: audit object: "), f"wrong wording for {key!r}: {said}"


# ------------------------------------------------------------------ every converted call site has a mutant row


def _converted_sites() -> list[tuple[str, str, str]]:
    """(file, guard name, the ``what`` words) of every ``pathguard.<guard>(...)`` call in the package outside pathguard.py."""
    import ast

    src = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
    sites = []
    for path in sorted(src.rglob("*.py")):
        if path.name == "pathguard.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            f = node.func if isinstance(node, ast.Call) else None
            if (
                isinstance(f, ast.Attribute)
                and isinstance(f.value, ast.Name)
                and f.value.id == "pathguard"
                and f.attr in {"inside", "join", "operator_dir", "operator_file", "component"}
            ):
                what = next(
                    (
                        k.value.value
                        for k in node.keywords
                        if k.arg == "what" and isinstance(k.value, ast.Constant)
                    ),
                    "",
                )
                sites.append((path.relative_to(src.parent.parent).as_posix(), f.attr, what))
    return sites


def test_control_every_converted_call_site_has_a_mutant_row_or_an_equivalent_entry():
    """A site added later without a row fails here. A site is covered when a row for its file (or an EQUIVALENT entry) holds
    the same guard name and the same ``what`` words in the text it replaces."""
    from tests import pathguard_mutants as pm

    texts: dict[str, list[str]] = {}
    for m in pm.M:
        texts.setdefault(m.file, []).append(m.old)
    for rel, text, _arg in pm.EQUIVALENT:
        texts.setdefault(f"src/hadavin_sdk/{rel}", []).append(text)
    uncovered = []
    for rel, guard, what in _converted_sites():
        wanted = f"pathguard.{guard}("
        if not any(
            wanted in old and (not what or f'what="{what}"' in old) for old in texts.get(rel, [])
        ):
            uncovered.append(f"{rel}: pathguard.{guard} what={what!r}")
    assert sorted(set(uncovered)) == []
