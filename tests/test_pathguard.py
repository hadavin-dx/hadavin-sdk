"""pathguard: the one place that decides whether a file name or a folder is safe (rules R1 to R11), the three old checks that
now call it, and ``atomic_write``.

Proof rules (design ``sonar-path-traversal-design.md`` section 6):

* Tests that call ``pathguard`` directly are proven by the mutants in ``tests/pathguard_mutants.py`` (one reverted rule each),
  not by "fails on main": the module does not exist on main.
* Labels, measured by real runs on (a) origin/main source plus this change's ``pathguard.py`` and (b) origin/main as it is (``pathguard`` does not exist on main, so for a file that imports it an empty stand-in module let the file load; a test that calls the module fails there): ``test_control_*`` passes on (a) and (b); ``test_pin_*`` passes on (a) and fails on (b); every other name fails on (a). This file: 3 control, 31 pin, 15 other. Nothing here says a test "fails on old main".

Each killer below has a distinctive assertion text that the mutant runner pins.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from hadavin_sdk import pathguard
from hadavin_sdk.audit.signer import key_path
from hadavin_sdk.config import ConfigError, confined
from hadavin_sdk.k1b import atomic
from hadavin_sdk.k1b.atomic import atomic_write
from hadavin_sdk.k1b.causelist import load_cause_list
from hadavin_sdk.pathguard import PathRefused


def _link(target: Path, link: Path, *, directory: bool = False) -> None:
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")


def _must_refuse(rule: str, label: str, fn, *args, **kwargs) -> PathRefused:
    """Call ``fn``; it must raise ``PathRefused`` with exactly ``rule``. The text starts "<rule> not refused" for every miss."""
    refused: PathRefused | None = None
    other = ""
    try:
        fn(*args, **kwargs)
    except PathRefused as exc:
        refused = exc
    except (OSError, ValueError, RuntimeError, TypeError, IndexError) as exc:
        other = type(exc).__name__
    # The checks sit outside the handlers so the first error line is ours, not a chained earlier error.
    if other:
        raise AssertionError(f"{rule} not refused ({label}): {other}")
    if refused is None:
        raise AssertionError(f"{rule} not refused ({label})")
    assert refused.rule == rule, f"{rule} not refused ({label}): the rule was {refused.rule}"
    return refused


def _comp(name: str):
    return pathguard.component(name, what="name")


# ---------------------------------------------------------------- R1 to R7: one name


def test_pin_r1_empty_and_dot_names_are_refused():
    for name in ("", ".", ".."):
        _must_refuse("R1", repr(name), _comp, name)


def test_pin_r2_a_separator_is_refused_on_every_os():
    for name in ("a/b", "a\\b", "/", "\\", "a/"):
        _must_refuse("R2", repr(name), _comp, name)


def test_pin_r3_a_colon_is_refused_on_every_os():
    for name in ("C:x", "a:b", "NUL:", "a.txt:stream", ":"):
        _must_refuse("R3", repr(name), _comp, name)


def test_pin_r4_a_control_character_is_refused_in_a_name():
    for name in (
        "a\x00b",
        "a\nb",
        "a\x1fb",
        "a\x7fb",
        "a\x85b",
        "a\u202eb",
        "a\u2066b",
        "a\u2069b",
    ):
        _must_refuse("R4", repr(name), _comp, name)


def test_pin_r4_a_control_character_is_refused_in_an_operator_path(tmp_path):
    for text in ("a\x00b", "a\nb", "a\x7fb"):
        _must_refuse(
            "R4", f"operator_dir {text!r}", pathguard.operator_dir, tmp_path / text, what="x"
        )
        _must_refuse(
            "R4", f"operator_file {text!r}", pathguard.operator_file, tmp_path / text, what="x"
        )


def test_pin_r5_a_name_over_255_utf8_bytes_is_refused():
    assert _comp("a" * 255) == "a" * 255, "R5 refused a name of exactly 255 bytes"
    assert _comp("\u00e9" * 127) == "\u00e9" * 127, "R5 refused 254 bytes (127 two-byte letters)"
    _must_refuse("R5", "256 ascii", _comp, "a" * 256)
    _must_refuse("R5", "128 two-byte letters", _comp, "\u00e9" * 128)


def test_pin_r5_a_path_over_4096_characters_is_refused(tmp_path):
    long_tail = ["d" * 200] * 21  # 4200 characters once joined
    _must_refuse("R5", "join", pathguard.join, tmp_path, *long_tail, what="x")
    _must_refuse("R5", "inside", pathguard.inside, tmp_path, tmp_path / ("e" * 4100), what="x")
    _must_refuse("R5", "operator_dir", pathguard.operator_dir, tmp_path / ("e" * 4100), what="x")


def test_pin_r6_a_trailing_dot_or_space_is_refused():
    for name in ("a.", "a ", "a.b.", "x y "):
        _must_refuse("R6", repr(name), _comp, name)
    for name in (".hidden", "a b", "a.b", "a-"):
        assert _comp(name) == name, f"R6 refused a plain name: {name!r}"


def test_pin_r7_a_reserved_device_name_is_refused():
    names = (
        "con",
        "CON",
        "Con.txt",
        "prn",
        "aux.json",
        "NUL",
        "nul.tar.gz",
        "COM0",
        "COM1",
        "com9.log",
        "LPT1",
        "lpt9",
        "LPT0.x",
        "CONIN$",
        "conout$",
        "CLOCK$",
        "COM\u00b9",
        "lpt\u00b2.txt",
        "COM\u00b3",
        "con .txt",
    )
    for name in names:
        _must_refuse("R7", repr(name), _comp, name)


def test_pin_r7_names_that_only_look_like_devices_are_allowed():
    for name in (
        "console",
        "com10",
        "COMM1",
        "xcon",
        "aux2",
        "lpt",
        "case-001",
        "run1",
        "con-x",
        "nul_a",
        "x.con",
    ):
        assert _comp(name) == name, f"R7 refused an ordinary name: {name!r}"


def test_pin_a_plain_name_is_returned_unchanged():
    for name in (
        "run.json",
        "case-001.json",
        "caf\u00e9 bar.txt",
        "score-report.md",
        ".tmp",
        "\u65e5\u672c.json",
    ):
        assert _comp(name) is name or _comp(name) == name, f"component changed {name!r}"


# ---------------------------------------------------------------- R8: containment


def test_pin_r8_a_link_out_of_the_base_is_refused(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "f.txt").write_text("x", encoding="utf-8")
    _link(outside, base / "dirlink", directory=True)
    _link(outside / "f.txt", base / "filelink")
    _must_refuse("R8", "join via a folder link", pathguard.join, base, "dirlink", "f.txt", what="x")
    _must_refuse("R8", "join via a file link", pathguard.join, base, "filelink", what="x")
    _must_refuse(
        "R8",
        "inside via a folder link",
        pathguard.inside,
        base,
        base / "dirlink" / "f.txt",
        what="x",
    )
    _must_refuse("R8", "inside via ..", pathguard.inside, base, base / ".." / "outside", what="x")
    _must_refuse("R8", "inside absolute", pathguard.inside, base, outside / "f.txt", what="x")


def test_pin_r8_join_refuses_a_link_that_leaves_the_base_even_without_must_exist(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    _link(outside, base / "dirlink", directory=True)
    _must_refuse(
        "R8",
        "a new file under a folder link",
        pathguard.join,
        base,
        "dirlink",
        "new.json",
        what="x",
    )
    assert not (outside / "new.json").exists()


def test_pin_a_link_that_stays_inside_the_base_is_allowed(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "f.txt").write_text("x", encoding="utf-8")
    _link(tmp_path / "data", tmp_path / "alias", directory=True)
    got = pathguard.join(tmp_path, "alias", "f.txt", what="x", must_exist=True, kind="file")
    assert got == (tmp_path / "data" / "f.txt").resolve()


def test_pin_r9_absolute_drive_rooted_and_unc_names_are_refused(tmp_path):
    cases = {
        "/etc/passwd": ("R2", "absolute posix"),
        "\\x": ("R2", "rooted"),
        "\\\\server\\share": ("R2", "unc"),
        "\\\\?\\C:\\x": ("R2", "extended length"),
        "C:x": ("R3", "drive relative"),
        "C:\\x": ("R2", "drive absolute"),
    }
    for name, (rule, label) in cases.items():
        got = _must_refuse(rule, label, _comp, name)
        assert got.rule in ("R2", "R3"), f"R9 not refused ({label})"
        _must_refuse(rule, f"join {label}", pathguard.join, tmp_path, name, what="x")
    # the backslash forms alone (no drive colon) must fail on the separator rule: a rooted or UNC name is a refusal
    for name in ("\\x", "\\\\server\\share"):
        assert name.startswith("\\"), "R9 not refused: the test input is wrong"
        _must_refuse("R2", f"R9 not refused rooted {name!r}", _comp, name)


# ---------------------------------------------------------------- R10, R11


def test_pin_r10_a_path_that_cannot_be_resolved_is_refused(tmp_path):
    _must_refuse(
        "R10",
        "missing with must_exist",
        pathguard.join,
        tmp_path,
        "nope.json",
        what="x",
        must_exist=True,
    )
    _must_refuse(
        "R10", "missing operator folder", pathguard.operator_dir, tmp_path / "nope", what="x"
    )
    _must_refuse(
        "R10", "missing operator file", pathguard.operator_file, tmp_path / "nope", what="x"
    )


def test_pin_r10_a_symlink_loop_is_refused(tmp_path):
    _link(tmp_path / "loop", tmp_path / "loop")
    _must_refuse(
        "R10", "loop with must_exist", pathguard.join, tmp_path, "loop", what="x", must_exist=True
    )
    _must_refuse(
        "R10", "loop in operator_file", pathguard.operator_file, tmp_path / "loop", what="x"
    )


def test_pin_r11_the_wrong_type_is_refused(tmp_path):
    (tmp_path / "d").mkdir()
    (tmp_path / "f").write_text("x", encoding="utf-8")
    exc = _must_refuse(
        "R11",
        "file wanted, folder found",
        pathguard.join,
        tmp_path,
        "d",
        what="x",
        must_exist=True,
        kind="file",
    )
    assert "not a file" in str(exc), "R11 text for a folder named as a file is wrong"
    exc = _must_refuse(
        "R11",
        "folder wanted, file found",
        pathguard.join,
        tmp_path,
        "f",
        what="x",
        must_exist=True,
        kind="dir",
    )
    assert "not a folder" in str(exc), "R11 text for a file named as a folder is wrong"
    _must_refuse(
        "R11",
        "inside file wanted",
        pathguard.inside,
        tmp_path,
        tmp_path / "d",
        what="x",
        kind="file",
    )
    _must_refuse("R11", "operator_dir on a file", pathguard.operator_dir, tmp_path / "f", what="x")
    _must_refuse(
        "R11", "operator_file on a folder", pathguard.operator_file, tmp_path / "d", what="x"
    )
    _must_refuse(
        "R11",
        "operator_dir must_exist False on a file",
        pathguard.operator_dir,
        tmp_path / "f",
        what="x",
        must_exist=False,
    )


# ---------------------------------------------------------------- how join and the others behave when all is well


def test_pin_join_applies_component_to_every_name(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "file.json").write_text("{}", encoding="utf-8")
    # "sub/file.json" stays inside the base and exists: only the per-name check refuses it
    _must_refuse(
        "R2",
        "component not applied to a name with a separator",
        pathguard.join,
        tmp_path,
        "sub/file.json",
        what="x",
        must_exist=True,
    )
    _must_refuse(
        "R7",
        "component not applied to the second name",
        pathguard.join,
        tmp_path,
        "sub",
        "con.json",
        what="x",
    )


def test_pin_join_with_no_names_returns_the_resolved_base_and_empty_names_are_refused(tmp_path):
    assert pathguard.join(tmp_path, what="x") == tmp_path.resolve()
    _must_refuse("R1", "empty name", pathguard.join, tmp_path, "", what="x")
    _must_refuse("R1", "dot name", pathguard.join, tmp_path, ".", what="x")


@pytest.mark.parametrize(
    "name",
    [
        "with space.txt",
        "caf\u00e9.txt",
        "\u65e5\u672c.json",
        "a.b.c",
        "x" * 200,
        "UPPER.JSON",
        "dash-name_1.md",
    ],
)
def test_pin_ordinary_names_work(tmp_path, name):
    got = pathguard.join(tmp_path / "nested" / "deeper", name, what="x")
    assert got == tmp_path.resolve() / "nested" / "deeper" / name


def test_pin_the_refusal_text_names_the_argument_and_never_the_value(tmp_path):
    hostile = "../sekrit-value\x00"
    try:
        pathguard.join(tmp_path, hostile, what="outputs file")
    except PathRefused as exc:
        assert "outputs file" in str(exc)
        assert "sekrit" not in str(exc)
        assert isinstance(exc, ConfigError) and isinstance(exc, ValueError)
    else:
        raise AssertionError("not refused")


def test_pin_operator_dir_accepts_a_folder_that_will_be_created(tmp_path):
    got = pathguard.operator_dir(tmp_path / "new" / "deeper", what="x", must_exist=False)
    assert got == tmp_path.resolve() / "new" / "deeper"
    assert not got.exists()
    assert pathguard.operator_dir(tmp_path, what="x") == tmp_path.resolve()
    assert pathguard.operator_file(__file__, what="x") == Path(__file__).resolve()


# ---------------------------------------------------------------- the three old checks now call it


def test_control_confined_keeps_its_pinned_wording_for_a_dotdot_and_for_a_link(tmp_path):
    """REGRESSION: passed on main."""
    base = tmp_path / "base"
    base.mkdir()
    (tmp_path / "outside").mkdir()
    with pytest.raises(ConfigError, match="escapes"):
        confined(base, "../outside")
    with pytest.raises(ConfigError, match="escapes"):
        confined(base, str(tmp_path / "outside"))
    _link(tmp_path / "outside", base / "ln", directory=True)
    with pytest.raises(ConfigError, match="path escapes its folder: ln/x"):
        confined(base, "ln/x")
    assert confined(base, "a/b.txt") == base.resolve() / "a" / "b.txt"
    assert confined(base, "") == base.resolve()


def test_control_confined_does_not_gain_the_windows_name_rules(tmp_path):
    """REGRESSION: twelve other callers pass operator config names; only data-derived names get R6 and R7."""
    assert confined(tmp_path, "aux.md") == tmp_path.resolve() / "aux.md"
    assert confined(tmp_path, "notes.") == tmp_path.resolve() / "notes."


def test_confined_turns_a_nul_into_a_config_error(tmp_path):
    """FAIL-BEFORE: on main a NUL raised a bare ValueError (not a ConfigError)."""
    with pytest.raises(ConfigError):
        confined(tmp_path, "a\x00b")


def test_a_nul_in_the_cause_list_folder_is_a_config_error(tmp_path):
    """FAIL-BEFORE: on main the NUL escaped as a bare ValueError."""
    with pytest.raises(ConfigError, match="directory not found"):
        load_cause_list(Path(str(tmp_path) + "\x00x"))


def test_control_key_path_keeps_the_word_outside_and_its_order(tmp_path):
    """REGRESSION: tests pin "outside"; the key may not exist yet; a final symlink is refused first."""
    folder = tmp_path / "keys"
    folder.mkdir()
    assert key_path(folder / "new.pem", folder) == folder.resolve() / "new.pem"
    with pytest.raises(ValueError, match="outside"):
        key_path(tmp_path / "elsewhere.pem", folder)
    with pytest.raises(ValueError, match="outside"):
        key_path(folder / ".." / "x.pem", folder)
    with pytest.raises(ValueError, match="outside"):
        key_path(folder, folder)
    _link(tmp_path / "t", folder / "ln.pem")
    with pytest.raises(ValueError, match="symlink"):
        key_path(folder / "ln.pem", folder)


# ---------------------------------------------------------------- atomic_write


def test_atomic_write_writes_utf8_with_unix_newlines_and_backslash_escapes(tmp_path):
    atomic_write(tmp_path, "out.txt", "line1\nline2\n\u00e9\ud800x")
    assert (tmp_path / "out.txt").read_bytes() == "line1\nline2\n\u00e9\\ud800x".encode()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.txt"], "a temp file was left behind"


def test_atomic_write_replaces_an_existing_file(tmp_path):
    (tmp_path / "out.txt").write_text("old", encoding="utf-8")
    atomic_write(tmp_path, "out.txt", "new")
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "new"


def test_atomic_write_refuses_a_name_that_is_not_a_plain_name(tmp_path):
    """FAIL-BEFORE (call shape): main had no name argument; the refusals are the new behaviour."""
    for name, rule in (
        ("../x.txt", "R2"),
        ("a/b.txt", "R2"),
        ("/abs.txt", "R2"),
        ("con.json", "R7"),
        ("x.", "R6"),
        ("", "R1"),
        ("a:b", "R3"),
    ):
        _must_refuse(rule, repr(name), atomic_write, tmp_path, name, "t")
    assert list(tmp_path.iterdir()) == [], "a refused name still wrote a file"


def test_atomic_write_needs_a_base_and_a_name(tmp_path):
    with pytest.raises(TypeError):
        atomic_write("only-text")
    with pytest.raises(TypeError):
        atomic_write(tmp_path / "x.txt", "text")


def test_atomic_write_refuses_a_name_whose_temp_name_would_be_too_long(tmp_path):
    atomic_write(tmp_path, "a" * 233, "ok")
    _must_refuse("R5", "name of 234 bytes", atomic_write, tmp_path, "b" * 234, "t")


def test_atomic_write_does_not_write_through_a_link_that_leaves_the_folder(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")
    _link(outside, base / "out.txt")
    _must_refuse("R8", "final name is a link out", atomic_write, base, "out.txt", "overwritten")
    assert outside.read_text(encoding="utf-8") == "keep"


def test_atomic_write_temp_name_is_random_and_not_chosen_by_the_caller(tmp_path, monkeypatch):
    """FAIL-BEFORE: on main the temp name was ``<name>.tmp`` every time."""
    seen = []
    real_replace = os.replace

    def spy(src, dst):
        seen.append(Path(src).name)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", spy)
    atomic_write(tmp_path, "r.txt", "1")
    atomic_write(tmp_path, "r.txt", "2")
    assert len(seen) == 2 and seen[0] != seen[1], "the temp file name was the same twice"
    assert all(n.startswith(".r.txt.") and len(n) > len(".r.txt..tmp") for n in seen), (
        f"unexpected temp names {seen}"
    )


def test_atomic_write_temp_name_keeps_the_tmp_suffix(tmp_path, monkeypatch):
    """score reports a file ending in .tmp as a stray file (a crashed write)."""
    seen = []
    real_replace = os.replace

    def spy(src, dst):
        seen.append(Path(src).name)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", spy)
    atomic_write(tmp_path, "r.txt", "1")
    assert seen and seen[0].endswith(".tmp"), f"the temp name lost its .tmp suffix: {seen}"


def test_atomic_write_creates_its_temp_file_exclusively(tmp_path, monkeypatch):
    monkeypatch.setattr(atomic.secrets, "token_hex", lambda n: "0" * (2 * n))
    squatter = tmp_path / f".r.txt.{'0' * 16}.tmp"
    squatter.write_text("someone else's file", encoding="utf-8")
    with pytest.raises(
        pathguard.PathRefused, match="temp file: the name is already in use"
    ) as caught:
        atomic_write(tmp_path, "r.txt", "mine")  # O_EXCL: the temp name is never reused
    assert caught.value.rule == "R13"
    assert str(tmp_path) not in str(caught.value), "the refusal text must not hold the path"
    assert squatter.read_text(encoding="utf-8") == "someone else's file"
    assert not (tmp_path / "r.txt").exists()


def test_atomic_write_removes_its_temp_file_when_the_rename_fails(tmp_path, monkeypatch):
    def boom(src, dst):
        raise OSError("disk gone")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError, match="disk gone"):
        atomic_write(tmp_path, "r.txt", "x")
    assert list(tmp_path.iterdir()) == [], "the temp file was left after a failed rename"


def test_atomic_write_removes_its_temp_file_when_the_write_fails(tmp_path, monkeypatch):
    def boom(fd):
        raise OSError("fsync failed")

    monkeypatch.setattr(os, "fsync", boom)
    with pytest.raises(OSError, match="fsync failed"):
        atomic_write(tmp_path, "r.txt", "x")
    assert list(tmp_path.iterdir()) == [], "the temp file was left after a failed write"


def test_atomic_write_removes_its_temp_file_on_ctrl_c(tmp_path, monkeypatch):
    def boom(src, dst):
        raise KeyboardInterrupt

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(KeyboardInterrupt):
        atomic_write(tmp_path, "r.txt", "x")
    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------- filesystem-effect property test


def _draws(seed: int):
    """A fixed, repeatable stream of numbers (a 64-bit linear congruential generator): the same 300 examples on every run."""
    state = seed
    while True:
        state = (state * 6364136223846793005 + 1442695040888963407) % 2**64
        yield state >> 33


def _tree_state(root: Path) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob("*")):
        key = p.relative_to(root).as_posix()
        out[key] = (
            "dir"
            if p.is_dir() and not p.is_symlink()
            else hashlib.sha256(p.read_bytes()).hexdigest()
            if p.is_file()
            else "other"
        )
    return out


def test_random_names_never_change_anything_outside_the_base(tmp_path):
    """The oracle is the disk, not a second copy of the containment logic: a sibling folder with files and a link to it
    sit beside the base; after 300 random calls (fixed seed) nothing outside the base changed and nothing new appeared."""
    base = tmp_path / "base"
    outside = tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    (outside / "sub").mkdir()
    (outside / "sub" / "deep.txt").write_text("deep", encoding="utf-8")
    (base / "inner").mkdir()
    try:
        os.symlink(outside, base / "out_dir", target_is_directory=True)
        os.symlink(outside / "secret.txt", base / "out_file")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    before_outside = _tree_state(outside)
    pieces = [
        "a",
        "b.json",
        "..",
        ".",
        "",
        "inner",
        "out_dir",
        "out_file",
        "sub",
        "secret.txt",
        "con",
        "x/y",
        "../outside",
        "..\\outside",
        "C:x",
        "a\x00b",
        "z.",
        "\u00e9",
        "q" * 300,
        str(outside),
        str(outside / "secret.txt"),
        "\n",
        "NUL",
        "deep.txt",
    ]
    draw = _draws(20261112)
    refused = allowed = 0
    for _ in range(300):
        names = [pieces[next(draw) % len(pieces)] for _ in range(1 + next(draw) % 3)]
        try:
            got = pathguard.join(base, *names, what="x")
            assert got.is_relative_to(base.resolve()), (
                f"join returned a path outside the base for {names!r}"
            )
            allowed += 1
        except PathRefused:
            refused += 1
        try:
            atomic_write(base, names[0], "payload")
        except (PathRefused, OSError):
            pass
        try:
            atomic_write(pathguard.join(base, *names[:-1], what="x"), names[-1], "payload")
        except (PathRefused, OSError):
            pass
    assert _tree_state(outside) == before_outside, "a file outside the base changed or appeared"
    assert sorted(os.listdir(tmp_path)) == ["base", "outside"], "something appeared beside the base"
    assert allowed and refused, "the random names did not reach both outcomes"
    leftovers = [p for p in base.rglob("*") if p.name.endswith(".tmp")]
    assert leftovers == [], f"temp files left behind: {leftovers}"


# ---------------------------------------------------------------- behaviour through the real callers (score and replay)


def test_pin_r10_a_value_error_from_resolve_is_refused_as_r10(tmp_path, monkeypatch):
    """The NUL case moved to R4 (explicit check); a ValueError raised by resolve itself is still R10."""

    def boom(self, strict=False):
        raise ValueError("embedded null byte")

    monkeypatch.setattr(Path, "resolve", boom)
    _must_refuse("R10", "resolve raises ValueError", pathguard.operator_dir, "plain", what="x")


def test_pin_r4_a_nul_in_a_whole_path_is_refused_explicitly(tmp_path):
    _must_refuse(
        "R4",
        "NUL in operator folder",
        pathguard.operator_dir,
        str(tmp_path) + "\x00",
        what="x",
    )
