"""pathguard batch 3: every range of rule R4, every part of the other rules, every converted site, and the failure paths.

Labels, measured by real runs on (a) origin/main source plus this change's ``pathguard.py`` and (b) origin/main as it is (``pathguard`` does not exist on main, so for a file that imports it an empty stand-in module let the file load; a test that calls the module fails there): ``test_control_*`` passes on (a) and (b); ``test_pin_*`` passes on (a) and fails on (b); every other name fails on (a). This file: 12 control, 42 pin, 44 other. Nothing here says a test "fails on old main".
A pin or control name on a test that calls ``pathguard`` directly means only the measured result above, not a claim about
old behaviour: the module is new.

A NUL character makes the operating system itself raise, so a site that lost its guard can still look refused. Where
that matters the tests use ``CTRL`` (a right-to-left override, U+202E): the file system accepts it, only R4 refuses it.
Fake paths are built from parts; no real data.
"""

from __future__ import annotations

import itertools
import logging
import os
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk import pathguard, pathtext
from hadavin_sdk.config import ConfigError, confined
from hadavin_sdk.k1b import atomic
from hadavin_sdk.k1b.atomic import atomic_write
from hadavin_sdk.pathguard import PathRefused
from tests.conftest import make_cfg
from tests.fixtures.pathsize import path_of_bytes
from tests.test_k1b_replay import HAPPY, Env, ScriptedLLM
from tests.test_pathguard_callers import _fixture, _link
from tests.test_pathguard_sites import _refused

CTRL = chr(0x202E)
NUL = chr(0)


# ------------------------------------------------------------------ R4: one test per range


# written out here, NOT read from the module under test: a test that read its own table from the code it checks would shrink
# together with a mutant that drops a range
EXPECTED_RANGES = (
    ("C0 controls and NUL", 0x0000, 0x001F),
    ("DEL and C1 controls", 0x007F, 0x009F),
    ("soft hyphen", 0x00AD, 0x00AD),
    ("combining grapheme joiner", 0x034F, 0x034F),
    ("Arabic letter mark", 0x061C, 0x061C),
    ("Hangul fillers", 0x115F, 0x1160),
    ("Khmer inherent vowels", 0x17B4, 0x17B5),
    ("Mongolian vowel separator", 0x180E, 0x180E),
    ("zero-width and direction marks", 0x200B, 0x200F),
    ("line and paragraph separators and bidirectional embeddings", 0x2028, 0x202E),
    ("word joiner, invisible operators, isolates and deprecated format characters", 0x2060, 0x206F),
    ("braille blank", 0x2800, 0x2800),
    ("Hangul filler", 0x3164, 0x3164),
    ("variation selectors", 0xFE00, 0xFE0F),
    ("byte order mark", 0xFEFF, 0xFEFF),
    ("halfwidth Hangul filler", 0xFFA0, 0xFFA0),
    ("interlinear annotation", 0xFFF9, 0xFFFB),
    ("musical symbol format characters", 0x1D173, 0x1D17A),
    ("tag characters", 0xE0000, 0xE007F),
    ("variation selectors supplement", 0xE0100, 0xE01EF),
)


def _in_any_range(code: int) -> bool:
    return any(lo <= code <= hi for _, lo, hi in EXPECTED_RANGES)


def _range_test(index: int):
    label, lo, hi = EXPECTED_RANGES[index]

    def check() -> None:
        for code in sorted({lo, hi, (lo + hi) // 2}):
            _refused("R4", pathguard.component, "a" + chr(code) + "b", what="n")
        for code in (
            lo - 1,
            hi + 1,
        ):  # just outside: allowed unless it is the start of the next range
            if code >= 0 and not _in_any_range(code):
                name = "a" + chr(code) + "b"
                assert pathguard.component(name, what="n") == name, f"{label}: U+{code:04X} refused"

    check.__name__ = f"test_pin_r4_range_{index:02d}"
    check.__doc__ = f"R4 refuses the whole range: {label} (U+{lo:04X} to U+{hi:04X})."
    return check


for _i in range(len(EXPECTED_RANGES)):
    globals()[f"test_pin_r4_range_{_i:02d}"] = _range_test(_i)


def test_pin_r4_there_are_twenty_named_ranges_and_none_overlaps():
    ranges = pathguard.CONTROL_RANGES
    assert len(ranges) == 20
    assert tuple(ranges) == EXPECTED_RANGES
    spans = sorted((lo, hi) for _, lo, hi in ranges)
    assert all(a[1] < b[0] for a, b in itertools.pairwise(spans))


# ------------------------------------------------------------------ R6, R7: each part on its own


def test_pin_r6_a_trailing_dot_is_refused():
    _refused("R6", pathguard.component, "name.", what="n")


def test_pin_r6_a_trailing_space_is_refused():
    _refused("R6", pathguard.component, "name ", what="n")


def test_pin_r7_the_part_before_the_first_dot_decides():
    for name in ("con.txt.bak", "nul.tar.gz", "aux.a.b.c"):
        _refused("R7", pathguard.component, name, what="n")


def test_pin_r7_spaces_before_the_dot_do_not_hide_a_device_name():
    for name in ("con .txt", "nul  .x", "prn   .y.z"):
        _refused("R7", pathguard.component, name, what="n")


def test_pin_r7_a_name_that_only_starts_like_a_device_is_allowed():
    for name in ("console.txt", "my.con.txt", "auxiliary", "a.con"):
        assert pathguard.component(name, what="n") == name


# ------------------------------------------------------------------ R5: each call of the text check, on its own


def _wide(tmp_path) -> str:
    """Over the length limit as TEXT, yet it resolves to a short path (``/d/..`` over and over). A check that runs only on the
    resolved path does not see it, so each place that checks the text itself fails on its own."""
    (tmp_path / "d").mkdir(exist_ok=True)
    text = str(tmp_path) + "/d/.." * 900
    assert len(text) > pathguard.MAX_PATH_BYTES and len(str(Path(text).resolve())) < 400
    return text


LONG = "/" + "/".join(
    ["a" * 200] * 21
)  # over the limit as text, no name over 255 bytes; text only: no file system call can come first


def test_pin_r5_join_refuses_a_long_base_text():
    _refused("R5", pathguard.join, LONG, "x", what="n")


def test_pin_r5_join_refuses_a_wide_base_text_that_resolves_short(tmp_path):
    _refused("R5", pathguard.join, _wide(tmp_path), "x", what="n")


def test_pin_r5_join_refuses_a_long_joined_path_when_base_and_names_are_short(tmp_path):
    names = ["a" * 200] * 25  # each name is fine; together they are over the limit
    base = str(tmp_path)
    assert len(base) + sum(len(n) + 1 for n in names) > pathguard.MAX_PATH_BYTES
    _refused("R5", pathguard.join, base, *names, what="n")


def test_pin_r5_inside_refuses_a_long_base_text(tmp_path):
    _refused("R5", pathguard.inside, _wide(tmp_path), tmp_path / "x", what="n")


def test_pin_r5_inside_refuses_a_long_path_text(tmp_path):
    _refused("R5", pathguard.inside, tmp_path, _wide(tmp_path), what="n")


def test_pin_r5_operator_dir_refuses_a_long_text(tmp_path):
    _refused("R5", pathguard.operator_dir, _wide(tmp_path), what="n")
    _refused("R5", pathguard.operator_dir, LONG, what="n")


def test_pin_r5_operator_file_refuses_a_long_text():
    _refused("R5", pathguard.operator_file, LONG, what="n")


def test_pin_r5_a_path_of_exactly_4095_bytes_is_allowed_and_4096_is_refused(tmp_path):
    """PATH_MAX is 4096 counting the closing NUL: 4095 is the longest path, 4096 is refused (the text only, no system call)."""
    base = str(tmp_path)
    pathtext.check_text(path_of_bytes(base, pathguard.MAX_PATH_BYTES), "n")
    assert len(path_of_bytes(base, pathguard.MAX_PATH_BYTES).encode()) == 4095
    with pytest.raises(PathRefused) as refused:
        pathtext.check_text(path_of_bytes(base, pathguard.MAX_PATH_BYTES + 1), "n")
    assert (
        refused.value.rule == "R5"
        and len(path_of_bytes(base, pathguard.MAX_PATH_BYTES + 1).encode()) == 4096
    )


# ------------------------------------------------------------------ the rest of the choke point


def test_pin_r10_a_runtime_error_from_resolve_is_refused_as_r10(tmp_path, monkeypatch):
    """Python 3.12 raises RuntimeError for a symlink loop; it must be a refusal, not a crash."""

    def loop(self, strict=False):
        raise RuntimeError("Symlink loop")

    monkeypatch.setattr(Path, "resolve", loop)
    _refused("R10", pathguard.join, tmp_path, "a", what="n")
    _refused("R10", pathguard.operator_dir, tmp_path, what="n")


def test_pin_r11_an_existing_file_is_refused_as_a_folder_even_when_it_need_not_exist(tmp_path):
    file = tmp_path / "f"
    file.write_text("x", encoding="utf-8")
    _refused("R11", pathguard.operator_dir, file, what="n", must_exist=False)


def test_pin_r11_a_missing_path_is_accepted_when_it_need_not_exist(tmp_path):
    assert pathguard.operator_dir(tmp_path / "later", what="n", must_exist=False).name == "later"


def test_pin_mapped_turns_only_the_listed_rules_into_one_plain_message(tmp_path):
    with pytest.raises(PathRefused) as missing:
        pathguard.operator_dir(tmp_path / "missing", what="n")
    result = pathguard.mapped(missing.value, R10="plain words")
    assert type(result) is ConfigError and str(result) == "plain words"
    with pytest.raises(PathRefused) as control:
        pathguard.operator_dir(str(tmp_path) + CTRL, what="n")
    assert pathguard.mapped(control.value, R10="plain words") is control.value  # R4 is not listed
    assert pathguard.mapped(missing.value, R11="other") is missing.value  # R10 is not listed here


def test_pin_r5_the_whole_path_limit_counts_bytes_not_characters():
    text = "/" + "/".join(
        ["\u20ac" * 80] * 30
    )  # 2,430 characters, 7,230 bytes in UTF-8, no name over 255 bytes
    assert len(text) < pathguard.MAX_PATH_BYTES < len(text.encode())
    with pytest.raises(PathRefused) as refused:
        pathtext.check_text(text, "n")
    assert refused.value.rule == "R5"


# ------------------------------------------------------------------ atomic_write


def test_atomic_write_onto_a_folder_is_a_refusal_with_no_path_in_the_text(tmp_path):
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "keep.txt").write_text("keep", encoding="utf-8")
    exc = _refused("R13", atomic_write, tmp_path, "d", "text")
    assert str(tmp_path) not in str(exc) and str(exc) == "output file: a folder is not replaced"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["d"], "a temp file was left"
    assert (tmp_path / "d" / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_atomic_write_with_a_taken_temp_name_leaves_the_existing_file_untouched(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(atomic.secrets, "token_hex", lambda n: "1" * (2 * n))
    taken = tmp_path / f".r.txt.{'1' * 16}.tmp"
    taken.write_text("not ours", encoding="utf-8")
    exc = _refused("R13", atomic_write, tmp_path, "r.txt", "mine")
    assert str(exc) == "temp file: the name is already in use" and str(tmp_path) not in str(exc)
    assert taken.read_text(encoding="utf-8") == "not ours"
    assert not (tmp_path / "r.txt").exists()
    assert exc.__cause__ is None and exc.__context__ is None


def test_atomic_write_checks_the_temp_path_length_not_only_the_final_one(tmp_path, monkeypatch):
    final = pathguard.join(tmp_path, "r.txt", what="n")
    monkeypatch.setattr(
        pathtext, "MAX_PATH_BYTES", len(str(final)) + 3
    )  # the final path fits, the temp one does not
    _refused("R5", atomic_write, tmp_path, "r.txt", "x")
    assert list(tmp_path.iterdir()) == []


def test_the_longest_writable_name_can_really_be_written(tmp_path):
    name = "n" * pathguard.MAX_WRITE_NAME_BYTES
    atomic_write(
        tmp_path, name, "ok"
    )  # the temp name (255 bytes) and the final name both fit the file system
    assert (tmp_path / name).read_text(encoding="utf-8") == "ok"
    assert [p.name for p in tmp_path.iterdir()] == [name]


def test_atomic_write_removes_its_temp_file_when_fdopen_is_interrupted(tmp_path, monkeypatch):
    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "fdopen", interrupted)
    with pytest.raises(KeyboardInterrupt):
        atomic_write(tmp_path, "r.txt", "x")
    monkeypatch.undo()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_removes_its_temp_file_when_the_rename_is_interrupted(tmp_path, monkeypatch):
    def interrupted(src, dst):
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "replace", interrupted)
    with pytest.raises(KeyboardInterrupt):
        atomic_write(tmp_path, "r.txt", "x")
    monkeypatch.undo()
    assert list(tmp_path.iterdir()) == []


def test_atomic_write_flushes_the_file_to_disk_before_the_rename(tmp_path, monkeypatch):
    synced: list[int] = []
    real = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (synced.append(fd), real(fd))[1])
    atomic_write(tmp_path, "r.txt", "x")
    assert len(synced) == 1


def test_pin_atomic_write_still_leaves_its_temp_file_after_a_crash_it_cannot_catch():
    """The documented behaviour: a process killed between the write and the rename leaves ``.name.<hex>.tmp``. The temp
    name carries the ``.tmp`` suffix and 16 random hex characters so a leftover is recognisable and never reused."""
    assert pathguard.MAX_COMPONENT_BYTES - pathguard.MAX_WRITE_NAME_BYTES == len("..") + 16 + len(
        ".tmp"
    )


# ------------------------------------------------------------------ score, bundle, causelist: converted sites


def test_site_score_read_json_refuses_a_file_name_with_a_control_character(tmp_path):
    from hadavin_sdk.k1b import score as score_mod

    (tmp_path / f"a{CTRL}.json").write_text('{"x": 1}', encoding="utf-8")
    with pytest.raises(ConfigError, match="is missing or not valid JSON"):
        score_mod._read_json(tmp_path, f"a{CTRL}.json", what="the file")


def test_site_score_recorded_digest_does_not_read_a_file_behind_a_link(tmp_path):
    from hadavin_sdk.k1b import score as score_mod

    outside = tmp_path / "outside.sha256"
    outside.write_text("0" * 64, encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    _link(outside, out / "outputs.sha256", directory=False)
    assert score_mod._recorded_digest(out) == ""  # unreadable, so counted as changed


def test_site_score_recorded_digest_reads_a_plain_file_and_none_when_absent(tmp_path):
    from hadavin_sdk.k1b import score as score_mod

    assert score_mod._recorded_digest(tmp_path) is None
    (tmp_path / "outputs.sha256").write_text("ab\n", encoding="utf-8")
    assert score_mod._recorded_digest(tmp_path) == "ab"


def test_site_score_answers_file_with_a_control_character_in_its_name_is_refused(tmp_path):
    from hadavin_sdk.k1b.causelist import CauseList
    from hadavin_sdk.k1b.score import load_answers
    from tests.k1b_support import write_answers

    path = write_answers(tmp_path / f"a{CTRL}.json", {"case-001": ([("api", "bad_deploy")], False)})
    assert path.is_file()
    cause = CauseList(frozenset({"api"}), frozenset({"bad_deploy"}), "0" * 64, "0" * 64)
    with pytest.raises(ConfigError, match="answers file"):
        load_answers(path, cause)


def test_site_score_run_folder_join_refuses_a_link_out_when_the_layout_check_is_skipped(
    tmp_path, monkeypatch
):
    """The join at the run folder is its own guard: ``_check_layout`` and the digest steps are replaced so only it is left."""
    import shutil

    from hadavin_sdk.k1b import score as score_mod

    out, answers, cause_dir, bundles = _fixture(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    shutil.move(str(out / "run1"), str(elsewhere))
    _link(elsewhere, out / "run1", directory=True)
    monkeypatch.setattr(score_mod, "_check_layout", lambda out, case_ids: [1])
    monkeypatch.setattr(score_mod, "outputs_files", lambda out: [])
    monkeypatch.setattr(score_mod, "hash_files", lambda out, files: "x")
    with pytest.raises(ConfigError, match="escapes its folder"):
        score_mod.score(out, answers, cause_dir, bundles)


def test_site_outputs_files_refuses_a_missing_folder_a_control_character_and_a_link(tmp_path):
    import shutil

    from hadavin_sdk.k1b.replay import outputs_files

    with pytest.raises(ConfigError):
        outputs_files(tmp_path / "missing")
    _refused("R4", outputs_files, Path(str(tmp_path) + CTRL))
    out, _, _, _ = _fixture(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    shutil.move(str(out / "run1"), str(elsewhere))
    _link(elsewhere, out / "run1", directory=True)
    _refused("R8", outputs_files, out)


def test_site_bundle_load_json_and_text_refuse_a_file_name_with_a_control_character(tmp_path):
    from hadavin_sdk.k1b import bundle as bundle_mod

    (tmp_path / f"a{CTRL}.json").write_text('{"x": 1}', encoding="utf-8")
    with pytest.raises(bundle_mod.BundleError, match="is not valid JSON"):
        bundle_mod._load_json("case-001", tmp_path, f"a{CTRL}.json")
    with pytest.raises(bundle_mod.BundleError, match="is not valid UTF-8 text"):
        bundle_mod._text("case-001", tmp_path, f"a{CTRL}.json")


def test_control_site_bundle_manifest_and_part_files_that_are_links_out_are_refused(tmp_path):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundle
    from tests.k1b_support import make_bundle, write_manifest

    manifest_case = make_bundle(tmp_path / "m", "case-001")
    stolen = tmp_path / "manifest-outside.json"
    stolen.write_bytes((manifest_case / "manifest.json").read_bytes())
    (manifest_case / "manifest.json").unlink()
    _link(stolen, manifest_case / "manifest.json", directory=False)
    with pytest.raises(BundleError):
        load_bundle(manifest_case)

    part_case = make_bundle(tmp_path / "p", "case-001")
    part = next((part_case / "logs").glob("*.jsonl"))
    outside = tmp_path / "log-outside.jsonl"
    outside.write_bytes(part.read_bytes())
    part.unlink()
    _link(outside, part, directory=False)
    write_manifest(part_case)
    with pytest.raises(BundleError):
        load_bundle(part_case)


def test_control_site_causelist_file_that_is_a_link_out_is_refused(tmp_path):
    from hadavin_sdk.k1b.causelist import load_cause_list
    from tests.k1b_support import make_cause_list

    cause_dir = make_cause_list(tmp_path / "cause")
    outside = tmp_path / "services-outside.json"
    outside.write_bytes((cause_dir / "services.json").read_bytes())
    (cause_dir / "services.json").unlink()
    _link(outside, cause_dir / "services.json", directory=False)
    with pytest.raises(ConfigError, match="must be a file inside the directory"):
        load_cause_list(cause_dir)


# ------------------------------------------------------------------ briefs D and F: only the returned path is used


def test_score_uses_only_the_folder_that_the_check_returned(tmp_path, monkeypatch):
    """``score`` must read the folder ``outputs_dir`` returned, never the argument it was given."""
    from hadavin_sdk.k1b import score as score_mod

    out, answers, cause_dir, bundles = _fixture(tmp_path)
    decoy = tmp_path / "decoy"
    decoy.mkdir()  # an empty folder: reading it fails the layout check
    monkeypatch.setattr(score_mod, "outputs_dir", lambda arg: out)
    assert score_mod.score(decoy, answers, cause_dir, bundles).runs[0].hits == 2


def test_the_hash_folder_is_checked_and_a_missing_one_has_one_plain_message(tmp_path):
    from hadavin_sdk.hashing import hash_files

    with pytest.raises(ConfigError, match="^hash folder does not exist$"):
        hash_files(tmp_path / "missing", [])
    with pytest.raises(ConfigError, match="^hash folder does not exist$"):
        hash_files(tmp_path / "f", [])  # a file, not a folder
    _refused("R4", hash_files, Path(str(tmp_path) + CTRL), [])


def test_control_hash_files_refuses_a_file_that_is_a_link_out_of_the_folder(tmp_path):
    from hadavin_sdk.hashing import hash_files

    (tmp_path / "outside.txt").write_text("x", encoding="utf-8")
    folder = tmp_path / "folder"
    folder.mkdir()
    _link(tmp_path / "outside.txt", folder / "a.txt", directory=False)
    with pytest.raises(ConfigError):
        hash_files(folder, ["a.txt"])


def test_control_hash_files_still_hashes_a_plain_file(tmp_path):
    from hadavin_sdk.hashing import hash_files

    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    assert len(hash_files(tmp_path, ["a.txt"])) == 64


def test_secrets_folder_is_checked_when_the_provider_is_built(tmp_path):
    from hadavin_sdk.actions.secrets_file import build

    ok = SimpleNamespace(dir=str(tmp_path), ttl_s=1)
    assert build(ok, None).root == tmp_path.resolve()
    with pytest.raises(ConfigError, match="is not a folder"):
        build(SimpleNamespace(dir=str(tmp_path / "missing"), ttl_s=1), None)
    (tmp_path / "f").write_text("x", encoding="utf-8")
    with pytest.raises(ConfigError, match="is not a folder"):
        build(SimpleNamespace(dir=str(tmp_path / "f"), ttl_s=1), None)
    _refused("R4", build, SimpleNamespace(dir=str(tmp_path) + CTRL, ttl_s=1), None)


def test_control_secrets_file_refuses_a_name_that_leaves_the_folder(tmp_path):
    from hadavin_sdk.actions.secrets_file import MountedFileProvider

    outside = tmp_path / "outside"
    outside.write_text("x", encoding="utf-8")
    outside.chmod(0o400)  # a file the provider would accept if it were inside the folder
    folder = tmp_path / "mount"
    folder.mkdir()
    _link(outside, folder / "s", directory=False)
    provider = MountedFileProvider(folder, 1)
    with pytest.raises(ConfigError, match="escapes its folder"):
        provider.get("s")
    with pytest.raises(ConfigError, match="escapes its folder"):
        provider.get(".." + "/outside")


def test_fake_llm_recording_folder_and_names_go_through_pathguard(tmp_path):
    from hadavin_sdk.llm.fake import FakeLLM

    _refused("R4", FakeLLM, Path(str(tmp_path) + CTRL), {})
    (tmp_path / "f").write_text("x", encoding="utf-8")
    _refused("R11", FakeLLM, tmp_path / "f", {})
    assert FakeLLM(tmp_path / "later", {}).recorded_dir == (tmp_path / "later").resolve()


def test_judge_qualify_checks_the_golden_file_path(tmp_path):
    from hadavin_sdk.guard.judge import qualify

    _refused("R4", qualify, None, Path(str(tmp_path / "g.jsonl")) / CTRL)
    _refused("R10", qualify, None, tmp_path / "missing.jsonl")


def test_control_tool_module_names_are_checked_before_any_path_is_built(tmp_path, monkeypatch):
    from hadavin_sdk.tools import module_sha256

    (tmp_path / "pkgx").mkdir()
    (tmp_path / "pkgx" / "m.py").write_text("X = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    assert len(module_sha256("pkgx.m")) == 64  # the control: a dotted name resolves
    with pytest.raises(ConfigError, match="not a dotted module name"):
        module_sha256("pkgx/m")  # a separator would reach the same file
    with pytest.raises(ConfigError, match="not a dotted module name"):
        module_sha256("pkgx.." + "m")


# ------------------------------------------------------------------ audit sink and signer


def _event(event_id):
    from hadavin_sdk.models import AuditEvent

    event = AuditEvent(
        run_id="r1", domain="run", operation="state", principal="p", source="runtime"
    )
    event.event_id = event_id
    return event


@pytest.mark.parametrize("bad_id", ["a:b", "a?b"])
def test_local_dir_refuses_an_event_id_that_is_not_one_plain_file_name(tmp_path, bad_id):
    from hadavin_sdk.audit import LocalDirSink
    from hadavin_sdk.audit.protocol import AuditUnavailable

    sink = LocalDirSink(tmp_path / "aud")
    with pytest.raises(AuditUnavailable) as caught:
        sink.write_intent(_event(bad_id))
    assert bad_id not in str(caught.value), (
        "the refused id is the refused text: it must not be printed"
    )


def test_local_dir_counts_a_refused_outcome_warns_once_and_keeps_nothing(tmp_path, caplog):
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.audit.local_dir"):
        assert sink.write_outcome(_event("a:b")) is None
        assert sink.write_outcome(_event("c?d")) is None
    assert sink.refused_events == 2
    assert sink._pending == [], "a poison event stays in memory and is retried on every reconcile"
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1 and "a:b" not in warnings[0] and "c?d" not in warnings[0]
    assert sink.reconcile() == 0


def test_local_dir_a_good_outcome_is_still_written(tmp_path):
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")
    assert sink.write_outcome(_event("evt-1")) == "evt-1.json"
    assert sink.refused_events == 0


def test_local_dir_reconcile_leaves_a_corrupt_file_when_the_corrupt_folder_is_a_link_out(tmp_path):
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")
    outbox = sink.outbox
    outbox.mkdir(parents=True)
    (outbox / "bad.json").write_text("not json", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    _link(outside, outbox / "corrupt", directory=True)
    assert sink.reconcile() == 0  # no crash: the file stays for a person
    assert (outbox / "bad.json").is_file()
    assert list(outside.iterdir()) == []


def test_control_local_dir_reconcile_moves_a_corrupt_file_into_the_corrupt_folder(tmp_path):
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")
    sink.outbox.mkdir(parents=True)
    (sink.outbox / "bad.json").write_text("not json", encoding="utf-8")
    sink.reconcile()
    assert (sink.outbox / "corrupt" / "bad.json").is_file()


def test_signer_key_path_checks_the_shape_before_it_makes_any_folder(tmp_path):
    from hadavin_sdk.audit.signer import key_path

    nul_folder = Path(str(tmp_path / "keys") + NUL)
    _refused("R4", key_path, tmp_path / "keys" / "k", nul_folder)
    ctrl_folder = tmp_path / f"keys{CTRL}"
    _refused("R4", key_path, ctrl_folder / "k", ctrl_folder)
    assert not ctrl_folder.exists(), "the folder was made before the shape was checked"
    parent = tmp_path / f"p{CTRL}" / "keys"
    _refused("R4", key_path, parent / "k", parent)
    assert not (tmp_path / f"p{CTRL}").exists()


def test_signer_key_path_refusal_text_holds_no_path(tmp_path):
    """The evidence run on 9602b4ca found the full key file path and the resolved key folder in both ValueErrors."""
    from hadavin_sdk.audit.signer import key_path

    folder = tmp_path / "keys-CANARYDIR"
    folder.mkdir()
    outside = tmp_path / "elsewhere-CANARYFILE"
    outside.write_text("x", encoding="utf-8")
    link = folder / "lnk"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink") as linked:
        key_path(link, folder)
    with pytest.raises(ValueError, match="outside") as away:
        key_path(outside, folder)
    for caught in (linked, away):
        assert "CANARY" not in str(caught.value) and str(tmp_path) not in str(caught.value)


def test_control_signer_key_path_still_makes_a_missing_key_folder_and_returns_the_path(tmp_path):
    from hadavin_sdk.audit.signer import key_path

    folder = tmp_path / "keys"
    got = key_path(folder / "k", folder)
    assert got == (folder.resolve() / "k") and folder.is_dir()


# ------------------------------------------------------------------ config and traceback hygiene


@pytest.mark.parametrize("key", ["golden_dir", "inputs_dir"])
def test_site_config_folder_setting_with_a_control_character_is_refused(tmp_path, cfg_dir, key):
    from hadavin_sdk.config import load_config

    path = cfg_dir / "config.yaml"
    text = path.read_text(encoding="utf-8")
    old = next(line for line in text.splitlines() if line.startswith(f"{key}:"))
    path.write_text(text.replace(old, f'{key}: "x\\u202e"'), encoding="utf-8")
    _refused("R4", load_config, cfg_dir)


@pytest.mark.parametrize("key", ["golden_dir", "inputs_dir"])
def test_site_config_folder_setting_that_is_not_text_says_so_plainly(tmp_path, cfg_dir, key):
    from hadavin_sdk.config import load_config

    path = cfg_dir / "config.yaml"
    text = path.read_text(encoding="utf-8")
    old = next(line for line in text.splitlines() if line.startswith(f"{key}:"))
    path.write_text(text.replace(old, f"{key}: 5"), encoding="utf-8")
    with pytest.raises(ConfigError, match=f"^{key} must be a folder name written as text$"):
        load_config(cfg_dir)


def test_site_config_confined_delegates_to_pathguard_and_keeps_its_wording(tmp_path):
    _refused("R4", confined, tmp_path, "a" + CTRL)
    with pytest.raises(ConfigError, match="escapes"):
        confined(tmp_path, "../x")


def _no_chain(exc: BaseException) -> None:
    text = "".join(traceback.format_exception(exc))
    assert exc.__cause__ is None and exc.__suppress_context__, (
        "the error was chained to another one"
    )
    assert "The above exception" not in text, (
        "an earlier error (which can hold the value) is printed"
    )


def test_causelist_errors_carry_no_chain_for_bad_json_and_bad_characters(tmp_path):
    from hadavin_sdk.k1b.causelist import load_cause_list
    from tests.k1b_support import make_cause_list

    cause_dir = make_cause_list(tmp_path / "bad-json")
    (cause_dir / "services.json").write_text("{not json CANARY", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid JSON") as bad_json:
        load_cause_list(cause_dir)
    _no_chain(bad_json.value)
    cause_dir = make_cause_list(tmp_path / "bad-char")
    (cause_dir / "services.json").write_text('["\\ud800"]', encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid character") as bad_char:
        load_cause_list(cause_dir)
    _no_chain(bad_char.value)


def test_bundle_errors_carry_no_chain_for_a_bad_log_line_and_a_bad_character(tmp_path):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundle
    from tests.k1b_support import make_bundle, write_manifest

    case = make_bundle(tmp_path / "a", "case-001")
    log = next((case / "logs").glob("*.jsonl"))
    log.write_text("CANARY not json\n", encoding="utf-8")
    write_manifest(case)
    with pytest.raises(BundleError, match="not valid JSON") as bad_line:
        load_bundle(case)
    _no_chain(bad_line.value)

    case = make_bundle(tmp_path / "b", "case-001")
    (case / "deploys.json").write_text('["\\ud800"]', encoding="utf-8")
    write_manifest(case)
    with pytest.raises(BundleError, match="invalid character") as bad_char:
        load_bundle(case)
    _no_chain(bad_char.value)


def test_pin_a_traceback_of_a_refusal_never_holds_the_value(tmp_path):
    secret = "canary" + "-value"
    exc = _refused(
        "R4", pathguard.operator_dir, str(tmp_path / secret) + CTRL, what="outputs folder"
    )
    text = "".join(traceback.format_exception(exc))
    assert secret not in text.split("PathRefused:")[-1]
    assert exc.__cause__ is None


# ------------------------------------------------------------------ suppressions: one check, case-insensitive

SUPPRESSION_TOKENS = (
    "no" + "sonar",
    "no" + "qa",
    "no" + "sec",
    "type:" + " ignore",
    "fmt:" + " skip",
    "fmt:" + " off",
    "pragma:" + " no cover",
)
# The Sonar marker is refused everywhere in the package and the tests. The other markers are refused in the files this change
# wrote or rewrote (older files keep the ones they had: they are not part of this change).
EVERYWHERE = SUPPRESSION_TOKENS[:1]
ROOT = Path(__file__).resolve().parents[1]
TOUCHED = [
    "src/hadavin_sdk/pathguard.py",
    "src/hadavin_sdk/k1b/atomic.py",
    "src/hadavin_sdk/k1b/score.py",
    "src/hadavin_sdk/k1b/replay.py",
    "src/hadavin_sdk/k1b/bundle.py",
    "src/hadavin_sdk/k1b/causelist.py",
    "src/hadavin_sdk/hashing.py",
    "src/hadavin_sdk/llm/fake.py",
    "src/hadavin_sdk/actions/secrets_file.py",
    "tests/test_pathguard.py",
    "tests/test_pathguard_sites.py",
    "tests/test_pathguard_callers.py",
    "tests/test_pathguard_tripwire.py",
    "tests/test_pathguard_batch3.py",
    "tests/test_pathguard_batch4.py",
    "tests/test_changelog_claims.py",
    "tests/test_pathguard_batch5.py",
    "tests/pathguard_mutants.py",
]


def suppression_hits(name: str, text: str, tokens: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [f"{name}: {t}" for t in tokens if t in lowered]


def test_control_the_suppression_check_finds_every_spelling_in_a_seeded_line():
    for seeded in (
        "x = 1  # " + "NO" + "SONAR",
        "x = 1  # " + "No" + "Sonar",
        "x = 1  # " + "NO" + "QA: E501",
        "x = 1  # " + "Type" + ": " + "Ignore[arg-type]",
        "x = 1  # " + "FMT" + ": " + "SKIP",
    ):
        assert suppression_hits("seed.py", seeded, SUPPRESSION_TOKENS), seeded
    assert suppression_hits("clean.py", "x = 1  # a plain comment\n", SUPPRESSION_TOKENS) == []


def test_there_is_no_sonar_exemption_comment_in_the_package_or_the_tests_in_any_letter_case():
    files = [*ROOT.joinpath("src").rglob("*.py"), *ROOT.joinpath("tests").rglob("*.py")]
    hits = [
        h
        for f in files
        for h in suppression_hits(f.name, f.read_text(encoding="utf-8"), EVERYWHERE)
    ]
    assert hits == []


def test_the_files_of_this_change_hold_no_suppression_comment_of_any_kind():
    hits = []
    for rel in TOUCHED:
        hits += suppression_hits(rel, (ROOT / rel).read_text(encoding="utf-8"), SUPPRESSION_TOKENS)
    assert hits == []


# ------------------------------------------------------------------ the Windows-only limits stay written down


@pytest.mark.skipif(sys.platform == "win32", reason="posix test of the written limits")
def test_pin_the_docstring_states_what_the_guard_does_not_cover():
    text = pathguard.__doc__ or ""
    for limit in ("Hard links", "Case-insensitive", "8.3"):
        assert limit in text, limit


def test_score_refuses_a_report_folder_that_is_a_link_out_of_the_outputs_folder(
    cfg_dir, tmp_path, capsys
):
    from hadavin_sdk import cli
    from tests.k1b_support import dry_run_export

    export = dry_run_export(tmp_path, cfg_dir)
    common = ["--config", str(cfg_dir)]
    replay = [
        *common,
        "replay",
        "test-agent",
        "--bundles",
        str(export["bundles"]),
        "--cause-list",
        str(export["cause"]),
        "--max-usd",
        "5",
        "--out",
        str(export["out"]),
    ]
    assert cli.main(replay) == 0
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    _link(elsewhere, export["out"] / "score", directory=True)
    score = [
        *common,
        "score",
        "--outputs",
        str(export["out"]),
        "--answers",
        str(export["answers"]),
        "--cause-list",
        str(export["cause"]),
        "--bundles",
        str(export["bundles"]),
    ]
    assert cli.main(score) == 2, "the score command went through the link"
    assert list(elsewhere.iterdir()) == [], "the report was written through the link"
    assert "escapes its folder" in capsys.readouterr().err


# ------------------------------------------------------------------ replay: failure path and links
# These tests build their own folders (the mutation runner starts without the shared test setup file).


@pytest.fixture
def cfg_dir(tmp_path):
    return make_cfg(tmp_path)


@pytest.fixture
def env(tmp_path, cfg_dir):
    return Env(tmp_path, cfg_dir)


def _boom(*args, **kwargs):
    raise RuntimeError("boom")


def test_replay_with_a_control_character_in_the_output_folder_is_refused_and_writes_nothing(
    env,
):
    from hadavin_sdk.pathguard import PathRefused

    env.out = env.tmp / ("out" + chr(0x202E))
    with pytest.raises(PathRefused):
        env.run(ScriptedLLM([]))
    assert not env.out.exists()
    assert sorted(p.name for p in env.tmp.iterdir() if p.name.startswith("out")) == []


def test_control_replay_into_an_existing_file_says_the_folder_is_not_usable_in_one_wording(env):
    env.out.write_text("x", encoding="utf-8")
    with pytest.raises(ConfigError, match="^replay output folder exists and is not empty$"):
        env.run(ScriptedLLM([]))


def test_a_failed_replay_writes_the_marker_even_into_an_empty_folder(env, monkeypatch):
    from hadavin_sdk.k1b import replay as replay_mod

    monkeypatch.setattr(replay_mod.loop, "Budget", _boom)  # fails right after the folder is made
    with pytest.raises(RuntimeError, match="boom"):
        env.run(ScriptedLLM([]))
    assert (env.out / "FAILED.txt").is_file()
    assert [p.name for p in env.out.iterdir()] == ["FAILED.txt"]


def test_a_marker_that_cannot_be_written_never_replaces_the_original_error(env, monkeypatch):
    from hadavin_sdk.k1b import replay as replay_mod

    def no_marker(out, exc):
        raise OSError("disk full")

    monkeypatch.setattr(replay_mod.loop, "run_case", _boom)
    monkeypatch.setattr(replay_mod, "_mark_failed", no_marker)
    with pytest.raises(RuntimeError, match="boom") as caught:
        env.run(ScriptedLLM(HAPPY()))
    assert any("FAILED.txt was not written" in n for n in caught.value.__notes__)
    assert "disk full" not in "".join(caught.value.__notes__)


def test_a_run_folder_swapped_for_a_link_mid_run_stops_the_next_write(env, monkeypatch):
    """Honest part only: the run folder is checked again before every write, so after the swap the next file is refused and
    nothing more lands outside. A swap in the instant between that check and the write itself is not covered."""
    import os

    from hadavin_sdk.k1b import replay as replay_mod
    from hadavin_sdk.pathguard import PathRefused

    outside = env.tmp / "outside"
    real = replay_mod.loop.run_case
    calls = []

    def swap_after_first(*args, **kwargs):
        calls.append(1)
        out = real(*args, **kwargs)
        if (
            len(calls) == 2
        ):  # case-001 is written; swap the run folder for a link out before case-002
            os.rename(env.out / "run1", outside)
            try:
                os.symlink(outside, env.out / "run1", target_is_directory=True)
            except (OSError, NotImplementedError):
                pytest.skip("symlinks unavailable")
        return out

    monkeypatch.setattr(replay_mod.loop, "run_case", swap_after_first)
    with pytest.raises(PathRefused):
        env.run(ScriptedLLM(HAPPY()))
    assert sorted(p.name for p in outside.iterdir()) == [
        "case-001.json"
    ]  # written before the swap; nothing after it


def test_local_dir_outbox_fallback_refuses_a_device_name_as_the_event_id(tmp_path, monkeypatch):
    """The outbox is used when the object store fails; ``con.json`` is a device name and only the guard on the final name stops
    it (``.tmp-con`` is a fine name)."""
    from hadavin_sdk.audit import LocalDirSink

    sink = LocalDirSink(tmp_path / "aud")

    def store_down(event):
        raise OSError("store down")

    monkeypatch.setattr(sink, "_write", store_down)
    assert sink.write_outcome(_event("con")) is None
    assert not (sink.outbox / "con.json").exists(), "a device name reached the outbox"
    assert not list(sink.outbox.glob(".tmp-*")), "a temp file was left"


# ------------------------------------------------------------------ the mutant file


def test_every_equivalent_mutant_still_names_text_that_exists_and_gives_its_argument():
    """A mutant that cannot be killed is listed with a one-line argument; the text it describes must still be in the source,
    so an entry cannot outlive its code."""
    from tests import pathguard_mutants

    root = Path(pathguard.__file__).parent
    assert pathguard_mutants.EQUIVALENT, "the list is empty"
    for rel, text, argument in pathguard_mutants.EQUIVALENT:
        assert text in (root / rel).read_text(encoding="utf-8"), f"{rel}: the text is gone"
        assert len(argument.split()) >= 8 and "\n" not in argument, f"{rel}: no argument"


def test_control_the_mutant_file_has_no_duplicate_names_and_every_killer_exists():
    from tests import pathguard_mutants

    names = [m.name for m in pathguard_mutants.M]
    assert len(names) == len(set(names))
    for m in pathguard_mutants.M:
        source = (Path(__file__).parents[1] / m.test_file).read_text(encoding="utf-8")
        assert f"def {m.only_test}(" in source or m.only_test.startswith("test_pin_r4_range_"), (
            m.name
        )


# ------------------------------------------------------------------ strict joins before a read (wording stays the same)


def test_control_hash_files_says_not_a_file_for_a_missing_file_and_for_a_folder(tmp_path):
    from hadavin_sdk.hashing import hash_files

    (tmp_path / "sub").mkdir()
    for rel in ("missing.txt", "sub"):
        with pytest.raises(ConfigError, match=f"^not a file: {rel}$"):
            hash_files(tmp_path, [rel])


def test_secrets_file_keeps_its_not_found_and_not_a_regular_file_wording(tmp_path):
    from hadavin_sdk.actions.secrets_file import MountedFileProvider

    folder = tmp_path / "mount"
    (folder / "d").mkdir(parents=True)
    provider = MountedFileProvider(folder, 1)
    with pytest.raises(ConfigError, match="not found in the mounted folder"):
        provider.get("nope")
    with pytest.raises(ConfigError, match="not a regular file"):
        provider.get("d")


def test_score_digest_and_answers_reads_keep_their_results(tmp_path):
    from hadavin_sdk.k1b.score import _recorded_digest, load_answers

    assert _recorded_digest(tmp_path) is None  # no digest file
    (tmp_path / "outputs.sha256").write_text("abc\n", encoding="utf-8")
    assert _recorded_digest(tmp_path) == "abc"
    with pytest.raises(ConfigError, match="missing or not valid JSON"):
        load_answers(tmp_path / "none.json", None)  # the cause list is not reached
