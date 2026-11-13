"""The demo-only folder guard (tools/demo_only_guard.py): product code must not name the folder that
holds everything that exists only for demos, nor a made-up record id; the build must still pass with
the folder deleted. Made-up data only.

Rows: the real repo is clean and the scan is not vacuous; each way to depend on the folder is a hit
that names the file and line but never prints the matched text (symlinks, every file type, every
product folder, any depth, any spelling of the name, loader files, the copy-run marker); the
settings are checked (a bad setting stops the guard); a missing folder stops a run that requires it;
pytest in a copy without the folder passes for a clean product and fails for one that reaches into
the folder, and the copy imports its own code, never the original checkout. (That CI runs the scan
is checked in tests/test_demo_only_guard_ci.py.)"""

from __future__ import annotations

import importlib
import importlib.util
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from tools import demo_only_guard as g
from tools import fixed_run

from tests.fixed_run import run as run_fixed
from tests.refusal import refused
from tests.seeded import Seeded

ROOT = Path(__file__).resolve().parents[1]
FOLDER = "demo_only"
FAKE_ID = "FAKE-REC-[0-9]{4}"


def _cfg(**over: Any) -> g.GuardConfig:
    base: dict[str, Any] = {
        "folder": FOLDER,
        "product_roots": ("src",),
        "loaders": (),
        "fake_id_patterns": (re.compile(FAKE_ID),),
        "product_packages": ("pkg",),
    }
    base.update(over)
    return g.GuardConfig(**base)


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    """A made-up repository. It is a git repository (the guard lists files with git) with nothing added
    or committed: files that are not ignored count, as in a fresh checkout that has not run `git
    add` yet."""
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    if not (tmp_path / ".git").exists():
        run_fixed(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def _track(repo: Path) -> Path:
    """Add every file that is not ignored to git's index: the copy run copies the files git tracks (and
    only those)."""
    run_fixed(["git", "-C", str(repo), "add", "-A"], check=True)
    return repo


# the mutation runner copies the sources without .git: the two tests on this very repository then
# have nothing to scan
needs_git = pytest.mark.skipif(not (ROOT / ".git").exists(), reason="this copy has no .git")


PNG = b"\x89PNG\r\n\x1a\n"  # the first bytes of every real picture of this kind
MARKER = "tools/demo_only_guard.copy_run"
CLEAN = {
    "src/pkg/__init__.py": "X = 1\n",
    f"{FOLDER}/data.json": '{"id": "FAKE-REC-0001"}\n',
    MARKER: "",  # a repository that has the folder says its CI runs the copy run
}


# -- the real repository
# ---------------------------------------------------------------------------------------------
@needs_git
def test_this_repository_is_clean_and_the_scan_is_not_vacuous() -> None:
    cfg = g.load_config(ROOT / "tools" / "demo_only_guard.toml")
    assert g.scan(ROOT, cfg) == []
    assert any(
        p.startswith("src/hadavin_sdk/") for p in g.tracked_paths(ROOT)
    )  # it really looked at product files
    planted = g.scan(
        ROOT, _cfg(folder="hadavin_sdk", product_roots=("src",))
    )  # the same scan finds a folder name that product code does hold
    assert any(h.endswith("names-demo-only-folder") for h in planted)


def test_the_folder_name_is_in_the_settings_file_only() -> None:
    text = (ROOT / "tools" / "demo_only_guard.py").read_text(encoding="utf-8")
    assert '"demo_only"' not in text  # no hard-coded name in the script itself


# -- every way to depend on the folder
# --------------------------------------------------------------------------------
def test_a_clean_product_passes_even_though_the_folder_holds_fake_ids(tmp_path: Path) -> None:
    assert g.scan(_repo(tmp_path, CLEAN), _cfg()) == []


def test_product_code_that_names_the_folder_is_a_hit_with_file_and_line_only(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/a.py": f"x = 1\nimport {FOLDER}.fakes\n"})
    assert g.scan(repo, _cfg()) == ["src/pkg/a.py:2: names-demo-only-folder"], (
        "product_code_that_names_the_folder_is_a_hit_with_file_and_li: check 1"
    )


def test_a_fake_record_id_in_product_code_is_a_hit_and_the_id_is_not_printed(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/b.py": 'ID = "FAKE-REC-0042"\n'})
    hits = g.scan(repo, _cfg())
    assert hits == ["src/pkg/b.py:1: fake-record-id"] and "0042" not in "".join(hits), (
        "a_fake_record_id_in_product_code_is_a_hit_and_the_id_is_not_: check 1"
    )


def test_the_table_name_and_listed_phrases_are_not_hits_but_a_path_or_a_longer_word_is(
    tmp_path: Path,
) -> None:
    cfg = _cfg(allowed_phrases=("DEMO_ONLY", "demo-only kinds"))
    ok = _repo(tmp_path / "ok", {**CLEAN, "src/pkg/c.py": "DEMO_ONLY = 1\n# the demo-only kinds\n"})
    assert g.scan(ok, cfg) == []
    for i, line in enumerate(
        ["DEMO_ONLY/x.json", "src/DEMO_ONLY", "xDEMO_ONLY", "DEMO_ONLY_X", "DEMO_ONLYx"]
    ):
        bad = _repo(
            tmp_path / f"b{i}",
            {**CLEAN, "src/pkg/c.py": f"# demo-only kinds, DEMO_ONLY\nV = '{line}'\n"},
        )
        assert g.scan(bad, cfg) == ["src/pkg/c.py:2: names-demo-only-folder"], line


def test_a_listed_phrase_that_no_product_file_holds_is_a_stale_hit(tmp_path: Path) -> None:
    hits = g.scan(_repo(tmp_path, CLEAN), _cfg(allowed_phrases=("never written anywhere",)))
    assert len(hits) == 1, f"stale phrase gave {len(hits)} hits"
    assert "stale-allowed-phrase" in hits[0]


def test_the_folder_inside_a_product_root_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/pkg/__init__.py": "", f"src/{FOLDER}/x.py": "A = 1\n"})
    assert any("folder-inside-product-root" in h for h in g.scan(repo, _cfg()))


def test_a_missing_product_root_is_a_hit_not_a_silent_pass(tmp_path: Path) -> None:
    hits = g.scan(_repo(tmp_path, {f"{FOLDER}/a.json": "{}", MARKER: ""}), _cfg())
    assert hits == [
        "src: product-root-missing (a missing root would make the scan prove nothing)"
    ], "a_missing_product_root_is_a_hit_not_a_silent_pass: check 1"


def test_a_loader_may_name_the_folder_and_nothing_else_may(tmp_path: Path) -> None:
    files = {
        "src/pkg/loader.py": f'NAME = "{FOLDER}"\n',
        "src/pkg/other.py": f'NAME = "{FOLDER}"\n',
    }
    hits = g.scan(_repo(tmp_path, files), _cfg(loaders=("src/pkg/loader.py",)))
    assert hits == ["src/pkg/other.py:1: names-demo-only-folder"]


def test_a_loader_may_name_the_folder_once_only_and_may_not_hold_a_fake_id(tmp_path: Path) -> None:
    loader = ("src/pkg/loader.py",)
    one = _repo(tmp_path / "one", {**CLEAN, "src/pkg/loader.py": f"A = '{FOLDER}'\nB = 1\n"})
    assert g.scan(one, _cfg(loaders=loader)) == [], (
        "a_loader_may_name_the_folder_once_only_and_may_not_hold_a_fa: check 1"
    )
    two = _repo(
        tmp_path / "two", {**CLEAN, "src/pkg/loader.py": f"A = '{FOLDER}'\nB = '{FOLDER}'\n"}
    )
    assert g.scan(two, _cfg(loaders=loader)) == [
        "src/pkg/loader.py:2: loader-names-folder-too-often"
    ], "a_loader_may_name_the_folder_once_only_and_may_not_hold_a_fa: check 2"
    assert g.scan(two, _cfg(loaders=loader, loader_max_lines=2)) == [], (
        "a_loader_may_name_the_folder_once_only_and_may_not_hold_a_fa: check 3"
    )
    fake = _repo(
        tmp_path / "fk", {**CLEAN, "src/pkg/loader.py": f"A = '{FOLDER}'\nID = 'FAKE-REC-0001'\n"}
    )
    assert g.scan(fake, _cfg(loaders=loader)) == ["src/pkg/loader.py:2: fake-record-id"], (
        "a_loader_may_name_the_folder_once_only_and_may_not_hold_a_fa: check 4"
    )
    named = _repo(tmp_path / "nm", {**CLEAN, f"src/pkg/{FOLDER}_loader.py": f"A = '{FOLDER}'\n"})
    assert g.scan(named, _cfg(loaders=(f"src/pkg/{FOLDER}_loader.py",))) == [], (
        "a loader file whose own name holds the folder name was reported"
    )


def test_a_stale_loader_entry_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/pkg/loader.py": "NAME = 'x'\n"})
    hits = g.scan(repo, _cfg(loaders=("src/pkg/loader.py", "src/pkg/gone.py")))
    assert sorted(hits) == [
        "src/pkg/gone.py: stale-loader-entry (file does not exist)",
        "src/pkg/loader.py: stale-loader-entry (file does not name the folder)",
    ], "a_stale_loader_entry_is_a_hit: check 1"


def test_ignored_files_and_binary_endings_are_skipped(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path, {**CLEAN, "src/pkg/__pycache__/x.py": FOLDER, ".gitignore": "__pycache__/\n"}
    )
    (repo / "src/pkg/logo.png").write_bytes(PNG + b"\xff\xfe" + b"pixels")
    (repo / "src/pkg/LOGO.PNG").write_bytes(PNG + b"\x00\x00 pixels")
    hits = g.scan(repo, _cfg())
    assert hits == [], f"scan hits: {hits}"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_every_file_type_is_read_not_only_a_list_of_endings(tmp_path: Path) -> None:
    names = [
        "a.cfg",
        "a.ini",
        "a.sh",
        "a.pyi",
        "a.j2",
        "a.csv",
        "a.rst",
        "a.xml",
        "Makefile",
        "a.PY",
        "a.html",
    ]
    for i, name in enumerate(names):
        repo = _repo(tmp_path / f"r{i}", {**CLEAN, f"src/pkg/{name}": f"x\n{FOLDER}\n"})
        assert g.scan(repo, _cfg()) == [f"src/pkg/{name}:2: names-demo-only-folder"], (
            f"the file {name!r} was not read for the folder name"
        )


def test_a_file_that_is_not_text_and_not_a_known_binary_ending_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, CLEAN)
    (repo / "src/pkg/blob.dat").write_bytes(b"\xff\xfe\x00" + FOLDER.encode())
    (repo / "src/pkg/noending").write_bytes(b"\xc3\x28")
    assert sorted(h.split(" (")[0] for h in g.scan(repo, _cfg())) == [
        "src/pkg/blob.dat: unreadable-file",
        "src/pkg/noending: unreadable-file",
    ], "a_file_that_is_not_text_and_not_a_known_binary_ending_is_ref: check 1"


@pytest.mark.parametrize("root", ["templates", "tools", "demos"])
def test_the_other_product_folders_are_scanned_too(tmp_path: Path, root: str) -> None:
    repo = _repo(tmp_path, {**CLEAN, f"{root}/a.txt": f"{FOLDER}\n"})
    cfg = _cfg(product_roots=("src", "templates", "tools", "demos"))
    hits = g.scan(
        _repo(tmp_path / "x", {**CLEAN, "templates/k": "", "tools/k": "", "demos/k": ""}), cfg
    )
    assert hits == []
    repo = _repo(
        tmp_path / "y",
        {**CLEAN, "templates/k": "", "tools/k": "", "demos/k": "", f"{root}/a.txt": f"{FOLDER}\n"},
    )
    assert g.scan(repo, cfg) == [f"{root}/a.txt:1: names-demo-only-folder"]


def test_the_settings_of_this_repository_scan_every_product_folder() -> None:
    cfg = g.load_config(ROOT / "tools" / "demo_only_guard.toml")
    assert cfg.product_roots == ("src", "templates", "tools", "demos"), (
        "the_settings_of_this_repository_scan_every_product_folder: check 1"
    )
    assert cfg.skip_suffixes == g.DEFAULT_SKIP_SUFFIXES, (
        "the_settings_of_this_repository_scan_every_product_folder: check 2"
    )
    assert not any(
        s in cfg.skip_suffixes for s in (".py", ".js", ".toml", ".md", ".txt", ".sh", ".cfg")
    ), "the_settings_of_this_repository_scan_every_product_folder: check 3"


# -- symlinks, spellings, depth
# ---------------------------------------------------------------------------------------
def test_every_symlink_under_a_product_root_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "r", CLEAN)
    outside = _repo(tmp_path / "outside", {"x.py": "A = 1\n"})
    (repo / "src/pkg/to_file.py").symlink_to(repo / FOLDER / "data.json")
    (repo / "src/pkg/to_dir").symlink_to(repo / FOLDER, target_is_directory=True)
    (repo / "src/pkg/to_out.py").symlink_to(outside / "x.py")
    (repo / "src/pkg/dangling.py").symlink_to(repo / "gone.py")
    (repo / "src/pkg/__pycache__").symlink_to(repo / FOLDER, target_is_directory=True)
    hits = g.scan(repo, _cfg())
    assert sorted(hits) == sorted(
        f"src/pkg/{n}: symlink-in-product-root"
        for n in ("to_file.py", "to_dir", "to_out.py", "dangling.py", "__pycache__")
    ), f"link hits: {sorted(hits)}"
    for name in ("to_file.py", "to_dir", "to_out.py", "dangling.py"):
        one = _repo(tmp_path / f"one-{name}", CLEAN)
        link = one / "src/pkg" / name
        link.symlink_to(
            one / FOLDER if name == "to_dir" else one / "gone.py",
            target_is_directory=name == "to_dir",
        )
        assert _main(one, _toml(tmp_path)) == 1, (
            "every_symlink_under_a_product_root_is_a_hit: check 2"
        )


def test_a_product_root_that_is_itself_a_symlink_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "r", {"real/a.py": "A = 1\n"})
    (repo / "src").symlink_to(repo / "real", target_is_directory=True)
    assert g.scan(repo, _cfg()) == ["src: symlink-in-product-root"]


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_folder_inside_a_product_root_is_a_hit_at_any_depth_and_in_any_spelling(
    tmp_path: Path,
) -> None:
    for i, name in enumerate(["Demo_Only", "demo-only", "demo only", "DEMO_ONLY", "demo_only"]):
        repo = _repo(
            tmp_path / f"r{i}", {"src/pkg/__init__.py": "", f"src/pkg/sub/{name}/x.py": "A = 1\n"}
        )
        assert g.scan(repo, _cfg()) == [f"src/pkg/sub/{name}: folder-inside-product-root"], (
            f"a deep folder spelled {name!r} was not the one hit"
        )


def test_a_file_or_folder_name_that_holds_the_folder_name_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/pkg/x_demo_only.py": "", "src/pkg/my-demo_only-data/k.txt": ""})
    assert sorted(g.scan(repo, _cfg())) == [
        "src/pkg/my-demo_only-data: path-names-demo-only-folder",
        "src/pkg/x_demo_only.py: path-names-demo-only-folder",
    ], "a_file_or_folder_name_that_holds_the_folder_name_is_a_hit: check 1"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_line_that_names_the_folder_in_another_spelling_is_a_hit(tmp_path: Path) -> None:
    for i, spelling in enumerate(
        ["Demo_Only", "demo-only", "demo only", "DEMO-ONLY", "Demo  Only", "demo_-only"]
    ):
        repo = _repo(
            tmp_path / f"r{i}", {**CLEAN, "src/pkg/a.py": f"x = 1\nPATH = '{spelling}/fakes'\n"}
        )
        assert g.scan(repo, _cfg()) == ["src/pkg/a.py:2: names-demo-only-folder"], (
            f"a line that names the folder as {spelling!r} was not the one hit"
        )


# -- the guard's own files, and the copy-run marker
# ---------------------------------------------------------------------
def test_the_exempt_files_are_exactly_the_guard_itself_and_each_is_skipped_whole(
    tmp_path: Path,
) -> None:
    cfg = g.load_config(ROOT / "tools" / "demo_only_guard.toml")
    assert cfg.exempt_files == ("tools/demo_only_guard.py", "tools/demo_only_guard.toml"), (
        "the_exempt_files_are_exactly_the_guard_itself_and_each_is_sk: check 1"
    )
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/self.py": f"# {FOLDER}\n"})
    assert g.scan(repo, _cfg(exempt_files=("src/pkg/self.py",))) == [], (
        "the_exempt_files_are_exactly_the_guard_itself_and_each_is_sk: check 2"
    )
    assert g.scan(repo, _cfg()) == ["src/pkg/self.py:1: names-demo-only-folder"], (
        "the_exempt_files_are_exactly_the_guard_itself_and_each_is_sk: check 3"
    )
    assert g.scan(repo, _cfg(exempt_files=("src/pkg/gone.py",)))[0].startswith(
        "src/pkg/gone.py: stale-exempt-entry"
    ), "the_exempt_files_are_exactly_the_guard_itself_and_each_is_sk: check 4"


def test_a_repository_that_has_the_folder_needs_the_copy_run_marker(tmp_path: Path) -> None:
    without = {k: v for k, v in CLEAN.items() if k != MARKER}
    repo = _repo(tmp_path / "a", without)
    assert [h.split(" (")[0] for h in g.scan(repo, _cfg())] == [f"{MARKER}: copy-run-not-wired"], (
        "a_repository_that_has_the_folder_needs_the_copy_run_marker: check 1"
    )
    assert _main(repo, _toml(tmp_path)) == 1, (
        "a_repository_that_has_the_folder_needs_the_copy_run_marker: check 2"
    )
    assert g.scan(_repo(tmp_path / "b", CLEAN), _cfg()) == [], (
        "a_repository_that_has_the_folder_needs_the_copy_run_marker: check 3"
    )
    no_folder = _repo(
        tmp_path / "c", {"src/pkg/__init__.py": ""}
    )  # no folder, no marker needed (core)
    assert g.scan(no_folder, _cfg()) == [], (
        "a_repository_that_has_the_folder_needs_the_copy_run_marker: check 4"
    )


def test_the_copy_run_if_present_does_nothing_without_a_folder_and_runs_with_one(
    tmp_path: Path,
) -> None:
    cfg = _toml(tmp_path, product_packages='["pkg"]')
    none = _repo(tmp_path / "none", {"src/pkg/__init__.py": ""})
    assert _main(none, cfg, "--without-folder-if-present") == 0
    repo = _mini(tmp_path / "r")
    assert _main(repo, cfg, "--without-folder-if-present", "--", "tests/test_plain.py") == 0
    (repo / "tests" / "test_needs.py").write_text(NEEDS_FOLDER_TEST, encoding="utf-8")
    _track(repo)
    assert _main(repo, cfg, "--without-folder-if-present", "--", "tests/test_needs.py") != 0


def test_property_a_hit_is_reported_exactly_where_it_was_planted(tmp_path: Path) -> None:
    rng = Seeded(20261112)
    for i in range(60):
        repo = tmp_path / f"r{i}"
        files = {
            f"src/p{j}/m{j}.py": "".join(f"v{k} = {k}\n" for k in range(rng.randint(1, 5)))
            for j in range(4)
        }
        planted: set[str] = set()
        for rel in rng.sample(sorted(files), rng.randint(0, 3)):
            lines = files[rel].splitlines()
            at = rng.randrange(len(lines) + 1)
            bad = rng.choice([f"# {FOLDER}", "X = 'FAKE-REC-1234'"])
            lines.insert(at, bad)
            files[rel] = "\n".join(lines) + "\n"
            planted.add(
                f"{rel}:{at + 1}: "
                + ("names-demo-only-folder" if FOLDER in bad else "fake-record-id")
            )
        assert set(g.scan(_repo(repo, files), _cfg())) == planted


# -- the settings are checked
# -----------------------------------------------------------------------------------------
def _toml(tmp_path: Path, **over: str) -> Path:
    base = {
        "folder": '"demo_only"',
        "product_roots": '["src"]',
        "fake_id_patterns": "[]",
        "loaders": "[]",
    }
    base.update(over)
    path = tmp_path / "g.toml"
    path.write_text("\n".join(f"{k} = {v}" for k, v in base.items()) + "\n", encoding="utf-8")
    return path


def test_good_settings_load(tmp_path: Path) -> None:
    cfg = g.load_config(_toml(tmp_path))
    assert cfg.folder == FOLDER and cfg.product_roots == ("src",)


@pytest.mark.parametrize(
    ("over", "message"),
    [
        ({"folder": '""'}, "'folder'"),
        ({"folder": "3"}, "'folder'"),
        ({"product_roots": "[]"}, "'product_roots'"),
        ({"product_roots": '[""]'}, "'product_roots'"),
        ({"skip_suffixes": "[1]"}, "'skip_suffixes'"),
        ({"skip_suffixes": '["png"]'}, "starts with a dot"),
        ({"exempt_files": '[""]'}, "'exempt_files'"),
        ({"allowed_phrases": "[3]"}, "'allowed_phrases'"),
        ({"product_packages": '"x"'}, "'product_packages'"),
        ({"loader_max_lines": "0"}, "'loader_max_lines'"),
        ({"loader_max_lines": "true"}, "'loader_max_lines'"),
        ({"copy_run_marker": '""'}, "'copy_run_marker'"),
        ({"folder": '"__"'}, "'folder'"),
        ({"fake_id_patterns": '["("]'}, "not a valid pattern"),
        ({"loaders": '"a"'}, "must be lists"),
    ],
)
def test_a_bad_setting_stops_the_guard(tmp_path: Path, over: dict[str, str], message: str) -> None:
    with pytest.raises(SystemExit, match=message):
        g.load_config(_toml(tmp_path, **over))


def test_a_folder_name_that_is_a_path_stops_the_guard(tmp_path: Path) -> None:
    for name in ("a/b", "../x", "a b", "-x"):
        with refused(SystemExit, f"the folder name {name!r}", match="'folder'"):
            g.load_config(_toml(tmp_path, folder=f'"{name}"'))


def test_a_pattern_that_matches_the_empty_text_stops_the_guard(tmp_path: Path) -> None:
    for pattern in ("x*", "", "(a|)"):
        with refused(SystemExit, f"the pattern {pattern!r}", match="matches the empty text"):
            g.load_config(_toml(tmp_path, fake_id_patterns=f'["{pattern}"]'))


# -- the command line
# ------------------------------------------------------------------------------------------------
def _main(repo: Path, cfg: Path, *extra: str) -> int:
    return g.main(["--root", str(repo), "--config", str(cfg), *extra])


def test_exit_codes_clean_dirty_and_required_folder_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = _toml(tmp_path)
    clean = _repo(tmp_path / "clean", CLEAN)
    assert _main(clean, cfg) == 0 and capsys.readouterr().out == ""
    assert _main(clean, cfg, "--require") == 0
    no_folder = _repo(tmp_path / "nofolder", {"src/pkg/__init__.py": ""})
    assert (
        _main(no_folder, cfg) == 0
    )  # a core-style repository has no such folder: fine unless required
    assert _main(no_folder, cfg, "--require") == 2, (
        "a required folder that is missing did not stop the run"
    )
    assert "is missing but is required" in capsys.readouterr().out
    dirty = _repo(tmp_path / "dirty", {**CLEAN, "src/pkg/a.py": f"# {FOLDER}\n"})
    assert (
        _main(dirty, cfg) == 1
        and "src/pkg/a.py:1: names-demo-only-folder" in capsys.readouterr().out
    )


@needs_git
def test_the_script_runs_as_a_program_on_this_repository() -> None:
    done = run_fixed(
        [sys.executable, str(ROOT / "tools" / "demo_only_guard.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0 and done.stdout == "", done.stdout + done.stderr


# -- the build without the folder
# -------------------------------------------------------------------------------------
PRODUCT = "def answer():\n    return 42\n"
PLAIN_TEST = "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parents[1] / 'src'))\nfrom pkg import answer\n\n\ndef test_it():\n    assert answer() == 42\n"
NEEDS_FOLDER_TEST = "def test_needs_folder():\n    import demo_only.fakes\n"


def _mini(tmp_path: Path, product: str = PRODUCT) -> Path:
    return _track(
        _repo(
            tmp_path,
            {
                "src/pkg/__init__.py": product,
                "tests/test_plain.py": PLAIN_TEST,
                f"{FOLDER}/__init__.py": "",
                f"{FOLDER}/fakes.py": "RECORD = 'x'\n",
            },
        )
    )


def test_the_copy_has_no_folder_and_nothing_else_is_lost(tmp_path: Path) -> None:
    repo = _mini(tmp_path / "r")
    dest = tmp_path / "copy"
    g.copy_without_folder(repo, _cfg(), dest)
    assert not (dest / FOLDER).exists(), "the copy still holds the demo-only folder"
    assert (dest / "src" / "pkg" / "__init__.py").is_file(), "the copy lost a product file"
    assert (dest / "tests" / "test_plain.py").is_file() and not (dest / ".git").exists()
    assert (repo / FOLDER / "fakes.py").is_file()  # the original is untouched


def test_a_clean_product_passes_in_a_copy_without_the_folder(tmp_path: Path) -> None:
    assert g.run_without_folder(_mini(tmp_path / "r"), _cfg(), []) == 0


def test_a_product_that_reaches_into_the_folder_fails_in_the_copy(tmp_path: Path) -> None:
    # the name is built from pieces at run time, which no text scan finds: the copy run is the check
    # for it (a name written out is stopped by the scan that now runs first, see the batch 7 tests)
    repo = _mini(
        tmp_path / "r",
        PRODUCT + 'import importlib\nimportlib.import_module("demo" + "_only.fakes")\n',
    )
    assert g.scan(repo, _cfg(), running_copy_run=True) == [], (
        "the pieced-together name was found by the scan"
    )
    assert g.run_without_folder(repo, _cfg(), []) != 0, (
        "the copy run passed although the product needs the folder"
    )


def test_the_copy_run_really_has_no_folder(tmp_path: Path) -> None:
    repo = _mini(tmp_path / "r")
    (repo / "tests" / "test_needs.py").write_text(NEEDS_FOLDER_TEST, encoding="utf-8")
    _track(repo)
    assert g.run_without_folder(repo, _cfg(), ["tests/test_needs.py"]) != 0, (
        "a test that needs the folder passed in the copy"
    )  # proves the folder is gone from the copy
    assert g.run_without_folder(repo, _cfg(), ["tests/test_plain.py"]) == 0


# -- one list of files: git's
# ---------------------------------------------------------------------------------------
def test_the_scan_refuses_a_folder_that_is_not_a_git_checkout(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    with pytest.raises(SystemExit) as stop:
        g.scan(tmp_path, _cfg())
    assert "not a git checkout" in str(stop.value), (
        f"the scan of a folder that is not a git checkout was not refused as such: {stop.value}"
    )


def test_a_file_is_scanned_whether_it_is_added_to_git_or_not(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path, {**CLEAN, "src/pkg/added.py": f"# {FOLDER}\n", "src/pkg/new.py": f"# {FOLDER}\n"}
    )
    run_fixed(["git", "-C", str(repo), "add", "src/pkg/added.py"], check=True)
    assert sorted(g.scan(repo, _cfg())) == [
        "src/pkg/added.py:1: names-demo-only-folder",
        "src/pkg/new.py:1: names-demo-only-folder",
    ], "a_file_is_scanned_whether_it_is_added_to_git_or_not: check 1"


def test_a_link_outside_the_product_folders_that_points_into_the_folder_is_a_hit(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "docs/a.md": "x\n", "other/f.txt": "y\n"})
    (repo / "docs/to_folder").symlink_to(repo / FOLDER, target_is_directory=True)
    (repo / "docs/to_file").symlink_to(repo / FOLDER / "data.json")
    (repo / "docs/elsewhere").symlink_to(repo / "other" / "f.txt")  # control: not into the folder
    assert sorted(g.scan(repo, _cfg())) == [
        "docs/to_file: symlink-to-demo-only-folder",
        "docs/to_folder: symlink-to-demo-only-folder",
    ], "a_link_outside_the_product_folders_that_points_into_the_fold: check 1"


# -- the copy run proves the copy, not the original
# -----------------------------------------------------------------
def test_the_copy_run_imports_the_copy_even_if_the_original_is_on_the_import_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _mini(tmp_path / "r")
    monkeypatch.setenv(
        "PYTHONPATH", str(repo / "src")
    )  # an inherited path to the ORIGINAL checkout
    assert g.run_without_folder(repo, _cfg(), []) == 0, (
        "the copy run kept the inherited import path"
    )  # the child replaces it with the copy's src
    assert g.run_without_folder(repo, _cfg(product_packages=("pkg_missing",)), []) != 0


def test_the_copy_run_fails_when_the_package_comes_from_somewhere_else(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _mini(tmp_path / "r")
    # "json" is real and importable but is not in the copy: the check must refuse to call that a
    # pass
    assert g.run_without_folder(repo, _cfg(product_packages=("json",)), []) == 3, (
        "a package that does not come from the copy was accepted"
    )
    assert "not imported from the copy" in capsys.readouterr().out


def test_the_copy_run_without_a_package_to_check_is_refused(tmp_path: Path) -> None:
    with refused(SystemExit, "a copy run with no product package", match="product_packages"):
        g.run_without_folder(_mini(tmp_path / "r"), _cfg(product_packages=()), [])


# -- round 3
# ---------------------------------------------------------------------------------------------------------
def test_a_listed_phrase_is_matched_in_its_own_case_and_not_beside_a_dash(tmp_path: Path) -> None:
    cfg = _cfg(allowed_phrases=("DEMO_ONLY",))
    for i, line in enumerate(["DEMO_ONLY-x", "x-DEMO_ONLY", "demo_only", "Demo_Only", "DEMO-ONLY"]):
        bad = _repo(tmp_path / f"p{i}", {**CLEAN, "src/pkg/c.py": f"V = DEMO_ONLY\nW = '{line}'\n"})
        assert g.scan(bad, cfg) == ["src/pkg/c.py:2: names-demo-only-folder"], line


def test_a_text_file_renamed_to_a_binary_ending_is_read_and_a_real_binary_is_searched_as_bytes(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/notes.png": f"see {FOLDER}\n"})
    assert (
        [h.split(" (")[0] for h in g.scan(repo, _cfg())]
        == [
            "src/pkg/notes.png: ending-does-not-match-content",  # the content decides: this is no picture
            "src/pkg/notes.png:1: names-demo-only-folder",  # and it is still read as text
        ]
    ), "a text file renamed to a picture ending was not read as text"
    real = _repo(tmp_path / "real", CLEAN)
    (real / "src/pkg/logo.png").write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + FOLDER.encode()
    )
    # a NUL byte near the start: a real binary, not read as text; its bytes are searched for the
    # name instead
    assert g.scan(real, _cfg()) == [
        "src/pkg/logo.png: names-demo-only-folder (inside a binary file)"
    ]
    clean = _repo(tmp_path / "clean", CLEAN)
    (clean / "src/pkg/logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    assert g.scan(clean, _cfg()) == []
    zeroes = _repo(
        tmp_path / "late", CLEAN
    )  # a NUL only after the first 8192 bytes does not make it binary
    (zeroes / "src/pkg/late.png").write_bytes(b"a" * 9000 + b"\x00" + FOLDER.encode())
    assert [h.split(" (")[0] for h in g.scan(zeroes, _cfg())] == [
        "src/pkg/late.png: ending-does-not-match-content",
        "src/pkg/late.png:1: names-demo-only-folder",
    ], "a NUL byte after the first 8192 bytes made the file binary"


def _gitlink(repo: Path, rel: str) -> None:
    """Add a git link (what a submodule is) at `rel`: the index holds mode 160000 and the path is a
    folder on disk."""
    (repo / rel).mkdir(parents=True)
    sha = "1" * 40
    run_fixed(
        ["git", "-C", str(repo), "update-index", "--add", "--cacheinfo", f"160000,{sha},{rel}"],
        check=True,
    )


def test_a_submodule_under_a_product_root_is_a_hit_and_one_outside_is_not(tmp_path: Path) -> None:
    repo = _repo(tmp_path, CLEAN)
    _gitlink(repo, "src/vendored")
    _gitlink(repo, "elsewhere/vendored")
    assert g.scan(repo, _cfg()) == [
        "src/vendored: submodule-in-product-root (its files cannot be scanned)"
    ], "a_submodule_under_a_product_root_is_a_hit_and_one_outside_is: check 1"


# -- round 4
# ---------------------------------------------------------------------------------------------------------
def test_a_full_width_spelling_of_the_name_is_a_hit_in_a_line_and_in_a_path(tmp_path: Path) -> None:
    wide = "".join(
        chr(ord(c) + 0xFEE0) if c.isalpha() else c for c in FOLDER
    )  # full-width letters, ASCII "_"
    wide_all = wide.replace("_", chr(0xFF3F))  # and the full-width underscore
    for i, spelling in enumerate((wide, wide_all)):
        repo = _repo(tmp_path / f"l{i}", {**CLEAN, "src/pkg/a.py": f"from {spelling} import y\n"})
        assert g.scan(repo, _cfg()) == ["src/pkg/a.py:1: names-demo-only-folder"], spelling
        path_repo = _repo(tmp_path / f"p{i}", {**CLEAN, f"src/pkg/{spelling}/x.py": "X = 1\n"})
        assert g.scan(path_repo, _cfg()) == [f"src/pkg/{spelling}: folder-inside-product-root"], (
            "a_full_width_spelling_of_the_name_is_a_hit_in_a_line_and_in_: check 2"
        )


def test_a_compiled_or_packed_file_in_a_product_folder_is_refused(tmp_path: Path) -> None:
    for suffix in (".pyc", ".so", ".zip", ".whl", ".PYC"):
        repo = _repo(tmp_path / suffix.strip("."), CLEAN)
        (repo / f"src/pkg/m{suffix}").write_bytes(b"\x00\x01 no name in here")
        assert g.scan(repo, _cfg()) == [
            f"src/pkg/m{suffix}: binary-in-product-root (a {suffix.lower()} file cannot be read or hides what it packs)"
        ], f"a {suffix} file in a product folder was not refused"


def test_a_binary_is_searched_as_bytes_in_utf8_and_both_utf16_orders(tmp_path: Path) -> None:
    spellings = {
        "u8": FOLDER.encode("utf-8"),
        "le": FOLDER.encode("utf-16-le"),
        "be": FOLDER.encode("utf-16-be"),
        "mixed": FOLDER.upper().replace("_", "-").encode("utf-16-le"),
    }
    for key, raw in spellings.items():
        repo = _repo(tmp_path / key, CLEAN)
        (repo / "src/pkg/blob.gif").write_bytes(b"GIF89a\x00\x01" + raw + b"\x00\x00")
        assert g.scan(repo, _cfg()) == [
            "src/pkg/blob.gif: names-demo-only-folder (inside a binary file)"
        ], f"the name in the {key} spelling was not found in the binary"


def test_text_written_as_utf16_without_a_mark_is_found_in_a_text_ending(tmp_path: Path) -> None:
    repo = _repo(tmp_path, CLEAN)
    (repo / "src/pkg/notes.txt").write_bytes(f"see {FOLDER}\n".encode("utf-16-le"))
    assert g.scan(repo, _cfg()) == [
        "src/pkg/notes.txt: names-demo-only-folder (as UTF-16 or UTF-32 text)"
    ], "text_written_as_utf16_without_a_mark_is_found_in_a_text_endi: check 1"


def test_a_binary_that_is_not_valid_text_and_has_no_nul_is_searched_not_skipped(
    tmp_path: Path,
) -> None:
    repo = _repo(
        tmp_path, CLEAN
    )  # no NUL anywhere: only the "not valid UTF-8" rule marks it as binary
    (repo / "src/pkg/a.png").write_bytes(PNG + b"\xff\xfe" + FOLDER.encode())
    (repo / "src/pkg/b.png").write_bytes(PNG + b"\xff\xfe pixels only")
    assert g.scan(repo, _cfg()) == [
        "src/pkg/a.png: names-demo-only-folder (inside a binary file)"
    ], "a_binary_that_is_not_valid_text_and_has_no_nul_is_searched_n: check 1"


def test_a_submodule_that_is_listed_as_exempt_is_not_a_second_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, CLEAN)
    _gitlink(repo, "src/vendored")
    clean = g.scan(repo, _cfg(exempt_files=("src/vendored",)))
    assert clean == [], (
        f"an exempt submodule gave hits: {clean}"
    )  # a clean exempt git link is no hit
    gone = g.scan(repo, _cfg(exempt_files=("src/vendored", "src/not-there")))
    assert gone == [
        "src/not-there: stale-exempt-entry (neither a file nor a git link that exists)"
    ], "a_submodule_that_is_listed_as_exempt_is_not_a_second_hit: check 2"


def test_a_submodule_whose_folder_is_missing_is_still_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, CLEAN)
    _gitlink(repo, "src/vendored")
    (repo / "src/vendored").rmdir()
    _gitlink(repo, "elsewhere/vendored")
    (repo / "elsewhere/vendored").rmdir()
    assert g.scan(repo, _cfg()) == [
        "src/vendored: submodule-in-product-root (its files cannot be scanned)"
    ], "a_submodule_whose_folder_is_missing_is_still_a_hit: check 1"


# -- round 5: the guard fails closed everywhere
# -----------------------------------------------------------------------
def test_an_entry_git_lists_that_cannot_be_read_is_a_hit_not_a_skip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/locked.py": "X = 1\n", "elsewhere/y.py": "Y = 1\n"})
    real_open = Path.open

    def locked_open(self: Path, *args: object, **kwargs: object):  # a permission error on one file
        if self.name == "locked.py":
            raise PermissionError("locked")
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", locked_open)
    assert g.scan(repo, _cfg()) == ["src/pkg/locked.py: unreadable-file (it cannot be read)"], (
        "a file that cannot be read was not a hit"
    )
    monkeypatch.undo()
    # a tracked file that was replaced by a pipe (git still lists it): a read would block, so it is
    # a hit, never opened
    (repo / "src/pkg/pipe.py").write_text("X = 1\n", encoding="utf-8")
    (repo / "elsewhere/pipe.py").write_text("X = 1\n", encoding="utf-8")
    run_fixed(
        ["git", "-C", str(repo), "add", "src/pkg/pipe.py", "elsewhere/pipe.py"],
        check=True,
    )
    for rel in (
        "src/pkg/pipe.py",
        "elsewhere/pipe.py",
    ):  # outside the product folders: not scanned, not a hit
        (repo / rel).unlink()
        os.mkfifo(repo / rel)
    assert g.scan(repo, _cfg()) == [
        "src/pkg/pipe.py: unreadable-file (the entry cannot be inspected)"
    ], "a pipe that git lists was not a hit"


MAGIC = {
    "zip": b"PK\x03\x04" + b"\x00" * 20,
    "ELF": b"\x7fELF\x02\x01\x01" + b"\x00" * 20,
    "gzip": b"\x1f\x8b\x08\x00" + b"\x00" * 20,
    "bzip2": b"BZh9" + b"1AY&SY" + b"\x00" * 20,
    "xz": b"\xfd7zXZ\x00" + b"\x00" * 20,
    "tar": b"a" * 257 + b"ustar" + b"\x00" * 20,
    "compiled Python": (3531).to_bytes(2, "little") + b"\r\n" + b"\x00" * 20,
    "fat Mach-O or Java class file": b"\xca\xfe\xba\xbe\x00\x00\x00\x02" + b"\x00" * 20,
    "RAR": b"Rar!\x1a\x07\x00" + b"\x00" * 20,
    "DOS or Windows program": b"MZ\x00\x00" + b"\x00" * 20,
}


def test_a_compiled_or_packed_file_is_refused_by_its_first_bytes_whatever_its_ending(
    tmp_path: Path,
) -> None:
    variants = [(k, v) for k, v in MAGIC.items()]
    variants += [
        ("zip", b"PK\x05\x06" + b"\x00" * 20),
        ("zip", b"PK\x07\x08" + b"\x00" * 20),
        (
            "fat Mach-O or Java class file",
            b"\xbe\xba\xfe\xca" + b"\x00" * 20,
        ),  # the other byte order
        (
            "fat Mach-O or Java class file",
            b"\xca\xfe\xba\xbe\x00\x00\x00\x34",
        ),  # a Java class file header
        (
            "fat Mach-O or Java class file",
            b"\xca\xfe\xba\xbf" + b"\x00" * 20,
        ),  # fat, 64-bit offsets
        (
            "fat Mach-O or Java class file",
            b"\xbf\xba\xfe\xca" + b"\x00" * 20,
        ),  # the other byte order
        ("bzip2", b"BZh1" + b"\x17rE8P\x90" + b"\x00" * 20),  # an empty stream (end-of-stream mark)
        ("bzip2", b"BZh1" + b"1AY&SY" + b"\x00" * 20),  # the lowest level
        ("RAR", b"Rar!\x1a\x07\x01" + b"\x00" * 20),  # the newer format
    ]  # empty, spanned
    running = int.from_bytes(importlib.util.MAGIC_NUMBER[:2], "little")
    for low_or_high in (
        3000,
        3999,
        running,  # the interpreter running the tests, whatever its version
        running + 1,
    ):  # the whole range of compiled-Python version numbers, both ends
        variants.append(
            ("compiled Python", low_or_high.to_bytes(2, "little") + b"\r\n" + b"\x00" * 20)
        )
    for kind, raw in variants:
        for ending in (".png", ".txt", ".dat", ""):
            tag = f"{kind.replace(' ', '')}{raw[:4].hex()}{ending.strip('.') or 'none'}"
            repo = _repo(tmp_path / tag, CLEAN)
            (repo / f"src/pkg/blob{ending}").write_bytes(raw)
            assert g.scan(repo, _cfg()) == [
                f"src/pkg/blob{ending}: binary-in-product-root (the file is {kind}, whatever its ending says)"
            ], (
                f"first bytes of {kind} ({raw[:4].hex()}) in a file ending {ending!r} were not refused as that kind"
            )
    for number in (2999, 8192):  # just outside the range: not read as compiled Python
        outside = _repo(tmp_path / f"out{number}", CLEAN)
        (outside / "src/pkg/blob.dat").write_bytes(
            number.to_bytes(2, "little") + b"\r\n" + b"\x00" * 20
        )
        assert not any("compiled Python" in h for h in g.scan(outside, _cfg())), f"version {number}"
    text = _repo(tmp_path / "text", {**CLEAN, "src/pkg/a.txt": "PK is fine as text, BZh too\n"})
    assert g.scan(text, _cfg()) == []  # the marks must be at the start and exact


def test_every_archive_ending_is_refused_like_a_zip(tmp_path: Path) -> None:
    for suffix in (".gz", ".tgz", ".tar", ".bz2", ".xz", ".GZ"):
        repo = _repo(tmp_path / suffix.strip("."), CLEAN)
        (repo / f"src/pkg/m{suffix}").write_bytes(b"x")
        assert g.scan(repo, _cfg()) == [
            f"src/pkg/m{suffix}: binary-in-product-root (a {suffix.lower()} file cannot be read or hides what it packs)"
        ], suffix


def test_the_name_is_found_as_utf32_in_a_binary_and_in_a_text_ending(tmp_path: Path) -> None:
    for enc in ("utf-32-le", "utf-32-be"):
        repo = _repo(tmp_path / enc, CLEAN)
        (repo / "src/pkg/blob.gif").write_bytes(
            b"GIF89a\x00\x01" + FOLDER.encode(enc) + b"\x00\x00"
        )
        assert g.scan(repo, _cfg()) == [
            "src/pkg/blob.gif: names-demo-only-folder (inside a binary file)"
        ], f"binary {enc}"
        text = _repo(tmp_path / f"t{enc}", CLEAN)
        (text / "src/pkg/notes.txt").write_bytes(f"see {FOLDER}\n".encode(enc))
        assert g.scan(text, _cfg()) == [
            "src/pkg/notes.txt: names-demo-only-folder (as UTF-16 or UTF-32 text)"
        ], f"text {enc}"


def test_a_file_over_the_size_cap_is_a_hit_and_is_not_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(
        tmp_path,
        {**CLEAN, "src/pkg/big.py": f"# {FOLDER}\n" + "x" * 200, "src/pkg/ok.py": "X = 1\n"},
    )
    assert (
        g.scan(repo, _cfg(max_file_bytes=100))
        == [
            "src/pkg/big.py: file-too-large (over 100 bytes; it is not read)"  # the name inside is not reported: not read
        ]
    ), "a_file_over_the_size_cap_is_a_hit_and_is_not_read: check 1"
    assert g.scan(repo, _cfg(max_file_bytes=1000)) == [
        "src/pkg/big.py:1: names-demo-only-folder"
    ], "a_file_over_the_size_cap_is_a_hit_and_is_not_read: check 2"
    real_open = Path.open

    def no_big(self: Path, *args: object, **kwargs: object):
        if self.name == "big.py":
            raise AssertionError("a file over the cap was opened")
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", no_big)
    assert g.scan(repo, _cfg(max_file_bytes=100)) == [
        "src/pkg/big.py: file-too-large (over 100 bytes; it is not read)"
    ], "a file over the cap was opened"
    monkeypatch.undo()
    # a file that grew after the size check is still bounded
    real_info = g._stat_info

    def small_info(full: Path | str) -> tuple[str, int]:
        kind, size = real_info(full)
        return (kind, 5) if str(full).endswith("big.py") else (kind, size)

    monkeypatch.setattr(g, "_stat_info", small_info)
    assert g.scan(repo, _cfg(max_file_bytes=100)) == [
        "src/pkg/big.py: file-too-large (over 100 bytes; it is not read)"
    ], "a_file_over_the_size_cap_is_a_hit_and_is_not_read: check 4"


def test_the_settings_file_checks_the_size_cap_the_copy_exclusions_and_the_child_environment(
    tmp_path: Path,
) -> None:
    base = (ROOT / "tools" / "demo_only_guard.toml").read_text(encoding="utf-8")
    cfg = g.load_config(ROOT / "tools" / "demo_only_guard.toml")
    assert (
        cfg.max_file_bytes == 8388608
        and not hasattr(cfg, "copy_exclude")
        and "PATH" in cfg.child_env_allowed
    )
    for line, message in (
        ("max_file_bytes = 0", "max_file_bytes"),
        ('max_file_bytes = "big"', "max_file_bytes"),
        ("copy_exclude = [1]", "copy_exclude"),
        ("child_env_allowed = 5", "child_env_allowed"),
    ):
        key = line.split(" =")[0]
        kept = [ln for ln in base.splitlines() if not ln.startswith(key + " ")]
        bad = tmp_path / f"{key}.toml"
        bad.write_text("\n".join([*kept, line]) + "\n", encoding="utf-8")
        with pytest.raises(SystemExit, match=message):
            g.load_config(bad)


def test_a_hit_is_printed_with_control_characters_escaped_and_never_as_a_workflow_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert g.printable("src/a\nb\x1b[31m.py:1: x") == "src/a\\x0ab\\x1b[31m.py:1: x", "category Cc"
    assert g.printable("::error::x") == "\\x3a:error::x", "a line starting with ::"
    assert g.printable("a::b") == "a::b", "a :: inside a line"
    assert g.printable("a\u202eb") == "a\\u202eb", "category Cf"
    assert g.printable("a\ud800b") == "a\\ud800b", "category Cs"
    assert g.printable("a\u2028b\u2029c") == "a\\u2028b\\u2029c", "category Zl and Zp"
    assert g.printable("a\ue000b") == "a\\ue000b", "category Co"
    assert g.printable("a\u0378b") == "a\\u0378b", "category Cn"
    assert g.printable("a\U0001f600b") == "a\U0001f600b", (
        "a printable character beyond U+FFFF stays"
    )
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/a\nb.py": 'ID = "FAKE-REC-0042"\n'})
    settings = tmp_path / "s.toml"
    settings.write_text(
        f'folder = "{FOLDER}"\nproduct_roots = ["src", "::notice"]\nfake_id_patterns = ["{FAKE_ID}"]\n',
        encoding="utf-8",
    )
    assert g.main(["--root", str(repo), "--config", str(settings)]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert "src/pkg/a\\x0ab.py:1: fake-record-id" in lines
    assert any(ln.startswith("\\x3a:notice: product-root-missing") for ln in lines)
    assert not any(ln.startswith("::") for ln in lines) and len(lines) == 2


def test_the_copy_run_child_gets_only_the_allowed_environment_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret_name = (
        "HADAVIN_" + "TEST_" + "CALLER_" + "TOKEN"
    )  # built from parts: a name only, no value of any key
    monkeypatch.setenv(secret_name, "not-a-real-value")
    check = (
        "import os\n\n\ndef test_env():\n"
        f"    assert {secret_name!r} not in os.environ\n    assert 'PATH' in os.environ\n"
    )
    repo = _mini(tmp_path / "r")
    (repo / "tests" / "test_env.py").write_text(check, encoding="utf-8")
    _track(repo)
    assert g.run_without_folder(repo, _cfg(), ["tests/test_env.py"]) == 0, (
        "the caller's environment reached the copy run child"
    )
    allowed = _cfg(child_env_allowed=(*g.DEFAULT_CHILD_ENV, secret_name))
    assert (
        g.run_without_folder(repo, allowed, ["tests/test_env.py"]) != 0
    )  # a listed name does pass through


def test_the_copy_holds_exactly_the_tracked_files_whatever_their_names(tmp_path: Path) -> None:
    repo = _mini(tmp_path / "r")
    for rel in ("src/pkg/credentials/__init__.py", ".env.d/a.cfg", ".env.example"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("x\n", encoding="utf-8")
    _track(repo)  # tracked: part of the product, whatever the folder or file is called
    for rel in (".env", ".pgpass", "src/pkg/key.pem", "build/out.txt", "src/pkg/new_untracked.py"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("x\n", encoding="utf-8")
    (repo / ".gitignore").write_text(
        "build/\n", encoding="utf-8"
    )  # build/ is ignored, the rest is only new
    dest = tmp_path / "copy"
    g.copy_without_folder(repo, _cfg(), dest)
    for rel in (
        "src/pkg/credentials/__init__.py",
        ".env.d/a.cfg",
        ".env.example",
        "src/pkg/__init__.py",
    ):
        assert (dest / rel).is_file(), f"a tracked file was left out of the copy: {rel}"
    for rel in (
        ".env",
        ".pgpass",
        "src/pkg/key.pem",
        "build/out.txt",
        "src/pkg/new_untracked.py",
        ".gitignore",
    ):
        assert not (dest / rel).exists(), f"a file git does not track reached the copy: {rel}"
    assert not (dest / FOLDER).exists() and not (dest / MARKER).exists()


def test_the_copy_does_not_depend_on_the_git_variables_of_the_caller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _mini(tmp_path / "r")
    other = _track(_repo(tmp_path / "other", {"elsewhere.txt": "x\n"}))
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_INDEX_FILE", str(other / ".git" / "index"))
    assert "src/pkg/__init__.py" in g.tracked_paths(repo), "GIT_DIR made git list another tree"
    assert "elsewhere.txt" not in g.tracked_paths(repo)
    dest = tmp_path / "copy"
    g.copy_without_folder(repo, _cfg(), dest)
    assert (dest / "src/pkg/__init__.py").is_file() and not (dest / "elsewhere.txt").exists()
    assert not any("elsewhere" in h for h in g.scan(repo, _cfg())), "the scan read the other tree"


def test_a_folder_that_a_loader_entry_names_is_still_a_folder_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {**CLEAN, f"src/pkg/{FOLDER}/x.py": "X = 1\n"})
    hits = g.scan(repo, _cfg(loaders=(f"src/pkg/{FOLDER}",)))
    assert (
        f"src/pkg/{FOLDER}: folder-inside-product-root" in hits
    )  # a loader is a file, never a folder
    assert f"src/pkg/{FOLDER}: stale-loader-entry (file does not exist)" in hits


def test_the_byte_patterns_are_built_once_for_a_whole_scan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/a.py": "A = 1\n", "src/pkg/b.py": "B = 1\n"})
    calls: list[str] = []
    real = g._byte_patterns
    monkeypatch.setattr(g, "_byte_patterns", lambda folder: calls.append(folder) or real(folder))
    assert g.scan(repo, _cfg()) == [], "the_byte_patterns_are_built_once_for_a_whole_scan: check 1"
    assert calls == [FOLDER], "the_byte_patterns_are_built_once_for_a_whole_scan: check 2"


def test_a_full_width_product_root_that_is_the_folder_is_a_hit(tmp_path: Path) -> None:
    wide = "".join(chr(ord(c) + 0xFEE0) if c.isalpha() else c for c in FOLDER)
    repo = _repo(tmp_path, {**CLEAN, f"{wide}/x.py": "X = 1\n"})
    hits = g.scan(repo, _cfg(product_roots=("src", wide)))
    want = f"{wide}: folder-inside-product-root (it would be packaged with the product)"
    assert want in hits, f"a full-width product root named like the folder was not a hit: {hits}"


# -- batch 6, class B: the content decides, an entry that cannot be inspected is a hit, special
# files keep their shape ---
REAL_SAMPLES = {  # the first bytes of a real file of each kind the settings allow without reading it as text
    ".png": PNG + b"\x00\x00",
    ".jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00",
    ".jpeg": b"\xff\xd8\xff\xdb\x00",
    ".gif": b"GIF89a\x01\x00\x01\x00\x00",
    ".ico": b"\x00\x00\x01\x00\x01\x00",
    ".pdf": b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n",
    ".woff": b"wOFF\x00\x01\x00\x00",
    ".woff2": b"wOF2\x00\x01\x00\x00",
    ".webp": b"RIFF\x24\x00\x00\x00WEBPVP8 ",
    ".ttf": b"\x00\x01\x00\x00\x00\x0f\x00\x80",
    ".otf": b"OTTO\x00\x0f\x00\x80",
}
FOREIGN_HEADERS = {  # real file marks of kinds the guard has no special rule for
    "zstd": b"\x28\xb5\x2f\xfd\x04\x00",
    "7z": b"7z\xbc\xaf\x27\x1c\x00\x04",
    "lz4": b"\x04\x22\x4d\x18\x64\x40",
    "a short MZ header (cannot be called a PE file)": b"MZ\x90\x00\x03\x00\x00\x00",
    "wav (a RIFF file that is not webp)": b"RIFF\x24\x00\x00\x00WAVEfmt ",
    "compressed json": b"\x78\x9c\xab\x56\x4a\xce\xcf",
}


def test_the_marks_table_covers_every_default_ending_and_each_real_sample_passes(
    tmp_path: Path,
) -> None:
    assert set(g.DEFAULT_SKIP_SUFFIXES) == set(g.ENDING_MARKS) == set(REAL_SAMPLES)
    for ending, sample in REAL_SAMPLES.items():
        repo = _repo(tmp_path / ending.strip("."), CLEAN)
        (repo / f"src/pkg/art{ending}").write_bytes(sample)
        assert g.scan(repo, _cfg()) == [], f"a real {ending} sample was refused"


def test_a_foreign_file_with_a_picture_font_or_pdf_ending_is_a_hit_for_every_ending(
    tmp_path: Path,
) -> None:
    for ending in REAL_SAMPLES:
        for kind, header in FOREIGN_HEADERS.items():
            repo = _repo(tmp_path / f"{ending.strip('.')}-{kind.replace(' ', '')}", CLEAN)
            (repo / f"src/pkg/art{ending}").write_bytes(header + b"payload")
            hits = [h.split(" (")[0] for h in g.scan(repo, _cfg())]
            assert hits == [f"src/pkg/art{ending}: ending-does-not-match-content"], (
                f"{kind} named {ending}: {hits}"
            )
    empty = _repo(tmp_path / "empty", CLEAN)
    (empty / "src/pkg/e.png").write_bytes(b"")
    assert [h.split(" (")[0] for h in g.scan(empty, _cfg())] == [
        "src/pkg/e.png: ending-does-not-match-content"
    ]


def test_an_ending_with_no_known_mark_cannot_be_listed_in_the_settings(tmp_path: Path) -> None:
    base = (ROOT / "tools" / "demo_only_guard.toml").read_text(encoding="utf-8")
    kept = [ln for ln in base.splitlines() if not ln.startswith("skip_suffixes ")]
    bad = tmp_path / "bad.toml"
    bad.write_text("\n".join([*kept, 'skip_suffixes = [".png", ".bmp"]']) + "\n", encoding="utf-8")
    with refused(SystemExit, "the ending .bmp with no known mark", match="no known first bytes"):
        g.load_config(bad)


def test_an_entry_is_gone_only_when_the_system_says_no_such_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import errno

    repo = _repo(tmp_path, {**CLEAN, "src/pkg/a.py": "A = 1\n"})
    real = os.lstat

    def fails_with(error: BaseException):
        def lstat(path, *a, **kw):
            if str(path).endswith("src/pkg/a.py"):
                raise error
            return real(path, *a, **kw)

        return lstat

    for error, expected in (
        (PermissionError(errno.EACCES, "denied"), ["src/pkg/a.py: unreadable-file"]),
        (OSError(errno.ELOOP, "loop"), ["src/pkg/a.py: unreadable-file"]),
        (NotADirectoryError(errno.ENOTDIR, "not a folder"), ["src/pkg/a.py: unreadable-file"]),
        (FileNotFoundError(errno.ENOENT, "gone"), []),
    ):
        with monkeypatch.context() as m:
            m.setattr(os, "lstat", fails_with(error))
            got = [h.split(" (")[0] for h in g.scan(repo, _cfg())]
        assert got == expected, (
            f"an lstat that fails with {type(error).__name__} gave hits {got}, not {expected}"
        )
    assert g._stat_kind(tmp_path / "no" / "such") == "gone"
    assert g._stat_kind(repo / "src/pkg/a.py") == "file" and g._stat_kind(repo / "src") == "folder"


def test_a_tracked_file_in_a_folder_that_cannot_be_entered_is_a_hit_not_a_skip(
    tmp_path: Path,
) -> None:
    """Run as a user that is not root (root can enter any folder): a tracked file under a folder of
    mode 000."""
    import shutil
    import tempfile

    base = Path(tempfile.mkdtemp(prefix="guard-locked-"))
    try:
        base.chmod(0o755)
        repo = _track(_repo(base / "r", {**CLEAN, "src/pkg/locked/x.py": "X = 1\n"}))
        script = base / "demo_only_guard.py"
        shutil.copy(ROOT / "tools" / "demo_only_guard.py", script)
        shutil.copy(
            ROOT / "tools" / "fixed_run.py", base / "fixed_run.py"
        )  # the guard starts programs through it
        settings = base / "s.toml"
        settings.write_text(
            f'folder = "{FOLDER}"\nproduct_roots = ["src"]\nproduct_packages = ["pkg"]\n',
            encoding="utf-8",
        )
        (repo / "src/pkg/locked").chmod(0o000)
        command = [
            sys.executable,
            "-I",
            str(script),
            "--root",
            str(repo),
            "--config",
            str(settings),
        ]
        if os.geteuid() == 0:
            setpriv = shutil.which("setpriv")
            if setpriv is None:
                pytest.skip("running as root and no setpriv to drop to another user")
            run_fixed(["chown", "-R", "65534:65534", str(base)], check=True)
            command = [setpriv, "--reuid=65534", "--regid=65534", "--clear-groups", *command]
        done = run_fixed(
            command,
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": os.environ["PATH"], "HOME": str(base)},
        )
        assert done.returncode == 1, done.stdout + done.stderr
        assert "src/pkg/locked/x.py: unreadable-file" in done.stdout, done.stdout + done.stderr
    finally:
        run_fixed(["chmod", "-R", "u+rwx", str(base)], check=False)
        shutil.rmtree(base, ignore_errors=True)


def test_the_marker_must_be_an_empty_regular_file(tmp_path: Path) -> None:
    full = _repo(tmp_path / "ok", CLEAN)
    assert g.scan(full, _cfg()) == []
    content = _repo(tmp_path / "content", {**CLEAN, MARKER: "something\n"})
    assert [h.split(" (")[0] for h in g.scan(content, _cfg())] == [
        f"{MARKER}: copy-run-marker-not-empty"
    ], "a marker with content was not a hit (copy-run-marker-not-empty)"
    link = _repo(tmp_path / "link", {k: v for k, v in CLEAN.items() if k != MARKER})
    (link / MARKER).parent.mkdir(parents=True, exist_ok=True)
    (link / MARKER).symlink_to(link / FOLDER / "data.json")  # a link into the folder
    hits = [h.split(" (")[0] for h in g.scan(link, _cfg())]
    assert (
        f"{MARKER}: copy-run-marker-not-a-regular-file" in hits
        and f"{MARKER}: copy-run-not-wired" in hits
    ), f"a marker that is a link was not a hit (copy-run-marker-not-a-regular-file): {hits}"
    as_folder = _repo(tmp_path / "dir", {k: v for k, v in CLEAN.items() if k != MARKER})
    (as_folder / MARKER).mkdir(parents=True)
    assert f"{MARKER}: copy-run-marker-not-a-regular-file" in [
        h.split(" (")[0] for h in g.scan(as_folder, _cfg())
    ]


def test_an_exempt_file_must_not_be_a_link_and_the_size_cap_still_applies(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path, {**CLEAN, "src/pkg/own.py": f"# {FOLDER}\n", "cfg/x.toml": f"{FOLDER}\n"}
    )
    cfg = _cfg(exempt_files=("src/pkg/own.py", "cfg/x.toml"))
    assert g.scan(repo, cfg) == [], "an exempt regular file is not searched"
    big = g.scan(repo, _cfg(exempt_files=("src/pkg/own.py", "cfg/x.toml"), max_file_bytes=5))
    too_large = [h.split(" (")[0] for h in big if "file-too-large" in h]
    assert "cfg/x.toml: file-too-large" in too_large
    assert "src/pkg/own.py: file-too-large" in too_large
    (repo / "src/pkg/own.py").unlink()
    (repo / "src/pkg/own.py").symlink_to(repo / FOLDER / "data.json")
    hits = [h.split(" (")[0] for h in g.scan(repo, cfg)]
    assert "src/pkg/own.py: symlink-exempt-file" in hits, (
        f"an exempt link was not a hit (symlink-exempt-file): {hits}"
    )
    (repo / "cfg/x.toml").unlink()
    (repo / "cfg/x.toml").symlink_to(repo / FOLDER / "data.json")
    assert "cfg/x.toml: symlink-exempt-file" in [h.split(" (")[0] for h in g.scan(repo, cfg)]


def test_the_modes_exclude_each_other_and_pytest_arguments_need_a_copy_run_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = _toml(tmp_path)
    repo = _repo(tmp_path / "r", CLEAN)
    combos = [
        ("--require", "--without-folder"),
        ("--require", "--without-folder-if-present"),
        ("--without-folder", "--without-folder-if-present"),
    ]
    for combo in combos:
        code = None
        try:
            _main(repo, cfg, *combo)
        except SystemExit as stop:
            code = stop.code
        assert code == 2, f"the modes {combo} were not refused with exit 2 (got {code!r})"
        assert "not allowed with" in capsys.readouterr().err, f"no refusal text for {combo}"
    for flags in ((), ("--require",)):
        code = None
        try:
            _main(repo, cfg, *flags, "--", "tests/test_x.py")
        except SystemExit as stop:
            code = stop.code
        assert code == 2, (
            f"pytest arguments with flags {flags} were not refused with exit 2 (got {code!r})"
        )
        assert "pytest arguments are accepted only with" in capsys.readouterr().err, (
            f"no refusal text for pytest arguments with flags {flags}"
        )


def test_the_copy_run_says_which_files_are_left_out_because_git_does_not_track_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _mini(tmp_path / "r")
    (repo / "src/pkg/new.py").write_text("N = 1\n", encoding="utf-8")
    assert g.run_without_folder(repo, _cfg(), ["tests/test_plain.py"]) == 0
    assert "1 file(s) are not added to git" in capsys.readouterr().out


# -- batch 7: first-byte kinds, marks for webp/ttf/otf, exempt files, the copy run, git excludes
# ------------------------ "Fails on old code" is stated per test (old code = 88e79c25).
def _pe_blob(offset: int = 0x40, total: int | None = None) -> bytes:
    """A made-up PE header made only of valid UTF-8 bytes: "MZ", filler, the offset at 0x3C, "PE\\0\\0"
    at the offset."""
    head = bytearray(b"MZ" + b"A" * 58 + offset.to_bytes(4, "little"))
    head += b"A" * max(0, offset - len(head)) + b"PE\x00\x00" + b"tail"
    if total:
        head += b"A" * max(0, total - len(head))
    return bytes(head)


KIND_SAMPLES: dict[str, bytes] = {
    "zip": b"PK\x03\x04rest",
    "ELF": b"\x7fELF\x02\x01\x01\x00",
    "gzip": b"\x1f\x8b\x08\x00rest",
    "bzip2": b"BZh91AY&SYrest",
    "xz": b"\xfd7zXZ\x00\x00\x04rest",
    "tar": b"x" * 257 + b"ustar" + b"\x0000",
    "compiled Python": (3495).to_bytes(2, "little") + b"\r\n" + b"\x00\x00\x00\x00rest",
    "Mach-O": b"\xcf\xfa\xed\xfe\x07\x00\x00\x01",
    "fat Mach-O or Java class file": b"\xca\xfe\xba\xbe\x00\x00\x00\x02",
    "RAR": b"Rar!\x1a\x07\x00rest",
    "DOS or Windows program": b"MZ" + b"\x00" * 30,
    "PE": _pe_blob(),
}
MACHO_MAGICS = (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe")


def _first_hit(repo: Path, **over: object) -> str:
    hits = [h.split(" (")[0] for h in g.scan(repo, _cfg(**over))]
    return "; ".join(hits)


def test_the_samples_cover_exactly_the_kinds_the_guard_lists() -> None:
    # fails on old code: MAGIC_KINDS did not exist
    assert set(KIND_SAMPLES) == set(g.MAGIC_KINDS), sorted(set(KIND_SAMPLES) ^ set(g.MAGIC_KINDS))
    for kind, sample in KIND_SAMPLES.items():
        assert g._magic_kind(sample) == kind, (
            f"the sample of {kind} is read as {g._magic_kind(sample)!r}"
        )


def test_every_first_byte_kind_is_a_hit_by_kind_under_an_unmarked_and_a_marked_ending(
    tmp_path: Path,
) -> None:
    # fails on old code for Mach-O and PE (a hit only when not valid UTF-8; the PE sample is valid
    # UTF-8, and a Mach-O file named .png was reported as "ending-does-not-match-content" instead of
    # by kind)
    for kind, sample in KIND_SAMPLES.items():
        for ending in (".dat", ".txt", ".png", ".woff2", ".ttf"):
            label = f"{kind} named {ending}"
            repo = _repo(tmp_path / f"{kind.replace(' ', '')}{ending.strip('.')}", CLEAN)
            (repo / f"src/pkg/blob{ending}").write_bytes(sample)
            got = _first_hit(repo)
            want = f"src/pkg/blob{ending}: binary-in-product-root"
            assert got == want, f"{label}: expected {want!r}, got {got!r}"
            hit = g.scan(repo, _cfg())[0]
            assert f"the file is {kind}," in hit, (
                f"{label}: the hit does not name the kind: {hit!r}"
            )


def test_all_four_mach_o_magic_values_are_hits(tmp_path: Path) -> None:
    # fails on old code: no rule for Mach-O
    for magic in MACHO_MAGICS:
        repo = _repo(tmp_path / magic.hex(), CLEAN)
        (repo / "src/pkg/m.dat").write_bytes(magic + b"\x07\x00\x00\x01 plain ascii after it")
        assert _first_hit(repo) == "src/pkg/m.dat: binary-in-product-root", (
            f"magic {magic.hex()} was not refused"
        )


def test_a_pe_header_that_cannot_say_is_not_called_a_pe_file_and_one_far_in_is_found() -> None:
    # fails on old code: no PE rule
    assert g._magic_kind(b"MZ") == "" and g._magic_kind(b"MZ" + b"A" * 20) == "", (
        "a short MZ file was read as PE"
    )
    far = _pe_blob(offset=900, total=1000)
    assert g._magic_kind(far) == "PE", (
        "a PE header whose offset lies beyond 512 bytes was not found"
    )
    beyond = bytearray(_pe_blob())
    beyond[0x3C:0x40] = (10_000).to_bytes(4, "little")
    assert g._magic_kind(bytes(beyond)) == "", "an offset beyond the file was read as PE"
    wrong = bytearray(_pe_blob())
    wrong[0x40:0x44] = b"XX\x00\x00"
    assert g._magic_kind(bytes(wrong)) == "", "a file without PE at the offset was read as PE"


def test_an_unmarked_ending_that_is_not_utf8_is_a_hit_and_is_not_searched_and_a_nul_file_is_read_as_text(
    tmp_path: Path,
) -> None:
    # the branches of the CHANGELOG sentence about unmarked endings; the first two held already on
    # old code
    repo = _repo(tmp_path / "a", CLEAN)
    (repo / "src/pkg/blob.dat").write_bytes(b"\xff\xfe\x00demo_only")
    got = _first_hit(repo)
    assert got == "src/pkg/blob.dat: unreadable-file", (
        f"a non-UTF-8 file with an unmarked ending: {got!r}"
    )
    repo = _repo(tmp_path / "b", CLEAN)
    (repo / "src/pkg/nul.dat").write_bytes(b"ok\x00 demo_only here")
    got = _first_hit(repo)
    assert got == "src/pkg/nul.dat:1: names-demo-only-folder", (
        f"valid UTF-8 with a NUL byte was not read as text: {got!r}"
    )
    repo = _repo(tmp_path / "c", CLEAN)
    (repo / "src/pkg/wide.dat").write_bytes("a demo_only b".encode("utf-16-le"))
    got = _first_hit(repo)
    assert "as UTF-16 or UTF-32 text" in str(g.scan(repo, _cfg())), (
        f"the name as UTF-16 was not found: {got!r}"
    )


def test_webp_ttf_and_otf_with_wrong_first_bytes_are_hits_and_with_the_right_ones_pass(
    tmp_path: Path,
) -> None:
    # fails on old code: these three endings had no mark, so a wrong file was read as text and
    # passed
    wrong = {
        ".webp": b"NOTMAGIC plain text",
        ".ttf": b"NOTMAGIC plain text",
        ".otf": b"NOTMAGIC plain text",
    }
    for ending, content in wrong.items():
        repo = _repo(tmp_path / ending.strip("."), CLEAN)
        (repo / f"src/pkg/f{ending}").write_bytes(content)
        got = _first_hit(repo)
        assert got == f"src/pkg/f{ending}: ending-does-not-match-content", (
            f"wrong {ending}: {got!r}"
        )
    repo = _repo(tmp_path / "wav", CLEAN)
    (repo / "src/pkg/w.webp").write_bytes(REAL_SAMPLES[".webp"].replace(b"WEBP", b"WAVE"))
    got = _first_hit(repo)
    assert got == "src/pkg/w.webp: ending-does-not-match-content", (
        f"a RIFF file that is not webp: {got!r}"
    )
    for ending in (".webp", ".ttf", ".otf", ".ttf"):
        repo = _repo(tmp_path / f"ok{ending.strip('.')}", CLEAN)
        (repo / f"src/pkg/f{ending}").write_bytes(REAL_SAMPLES[ending])
        assert g.scan(repo, _cfg()) == [], f"a real {ending} sample was refused"
    repo = _repo(tmp_path / "ttftrue", CLEAN)
    (repo / "src/pkg/t.ttf").write_bytes(b"true\x00\x0f\x00\x80")
    assert g.scan(repo, _cfg()) == [], "a ttf that starts with 'true' was refused"


def test_an_svg_is_text_it_is_read_and_a_binary_one_is_refused(tmp_path: Path) -> None:
    # svg is not listed on purpose: stated in the docstring and the settings file
    ok = _repo(
        tmp_path / "ok", {**CLEAN, "src/pkg/a.svg": "<svg xmlns='http://www.w3.org/2000/svg'/>\n"}
    )
    assert g.scan(ok, _cfg()) == [], "a plain svg was refused"
    named = _repo(tmp_path / "named", {**CLEAN, "src/pkg/a.svg": "<svg><!-- demo_only --></svg>\n"})
    assert _first_hit(named) == "src/pkg/a.svg:1: names-demo-only-folder", (
        "an svg that names the folder was not read"
    )
    odd = _repo(tmp_path / "odd", CLEAN)
    (odd / "src/pkg/b.svg").write_bytes(b"\xff\xd8\xff\xe0 not text")
    assert _first_hit(odd) == "src/pkg/b.svg: unreadable-file", (
        "a binary file named .svg was not refused"
    )
    assert (
        ".svg" not in g.ENDING_MARKS
        and ".svg" in (g.__doc__ or "")
        and "svg" in (ROOT / "tools" / "demo_only_guard.toml").read_text(encoding="utf-8")
    )


def test_an_exempt_file_that_is_a_binary_is_a_hit_by_kind(tmp_path: Path) -> None:
    # fails on old code: an exempt file got a shape and size check only
    for kind in ("ELF", "PE"):
        repo = _repo(tmp_path / kind, CLEAN)
        (repo / "src/pkg/ex.bin").write_bytes(KIND_SAMPLES[kind])
        got = _first_hit(repo, exempt_files=("src/pkg/ex.bin",))
        assert got == "src/pkg/ex.bin: binary-in-product-root", f"exempt {kind}: {got!r}"
    clean = _repo(tmp_path / "plain", {**CLEAN, "src/pkg/ex.txt": f"names {FOLDER} on purpose\n"})
    assert g.scan(clean, _cfg(exempt_files=("src/pkg/ex.txt",))) == [], (
        "a plain exempt file was refused"
    )


def test_the_docstring_states_that_the_first_512_bytes_decide_and_appended_data_is_not_looked_at() -> (
    None
):
    doc = g.__doc__ or ""
    assert "first 512 bytes decide" in doc and "appended" in doc, (
        "the docstring does not state the 512 byte limit"
    )
    assert "png, jpg, jpeg" in (ROOT / "tools" / "demo_only_guard.toml").read_text(
        encoding="utf-8"
    ), "the settings file leaves out jpg"


def _tracked_repo(tmp_path: Path, extra: dict[str, str] | None = None) -> Path:
    return _track(_repo(tmp_path, {**CLEAN, **(extra or {})}))


def test_the_copy_run_refuses_a_tracked_symlink_that_is_absolute_or_leaves_the_copy_or_enters_the_folder(
    tmp_path: Path,
) -> None:
    # fails on old code: every tracked symlink was recreated verbatim
    cases = {
        "absolute": "/etc/hostname",
        "leaves the copy": "../../../outside.txt",
        "into the folder": f"../{FOLDER}/data.json",
    }
    for label, target in cases.items():
        repo = _tracked_repo(tmp_path / label.replace(" ", "-"), {"docs/readme.txt": "x\n"})
        os.symlink(target, repo / "docs" / "link")
        _track(repo)
        try:
            g.copy_without_folder(repo, _cfg(), tmp_path / f"copy-{label.replace(' ', '-')}")
        except SystemExit as exc:
            assert "symlink" in str(exc), f"{label}: refused for another reason: {exc}"
        else:
            raise AssertionError(f"a tracked symlink that is {label} was copied")
    inside = _tracked_repo(tmp_path / "inside", {"docs/readme.txt": "x\n"})
    os.symlink("readme.txt", inside / "docs" / "link")
    _track(inside)
    g.copy_without_folder(inside, _cfg(), tmp_path / "copy-inside")
    assert os.readlink(tmp_path / "copy-inside" / "docs" / "link") == "readme.txt", (
        "a safe relative link was not kept"
    )


def test_a_path_swapped_for_a_link_after_the_check_is_refused_not_copied_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # fails on old code: shutil.copy2 followed the link
    repo = _tracked_repo(tmp_path / "r", {"docs/a.txt": "plain\n"})
    secret = tmp_path / "secret.txt"
    secret.write_text("outside content\n", encoding="utf-8")
    real = g._stat_kind

    def swapped(path: Path) -> str:
        kind = real(path)
        if str(path).endswith(
            "docs/a.txt"
        ):  # between the check and the copy the file becomes a link
            (repo / "docs" / "a.txt").unlink()
            os.symlink(secret, repo / "docs" / "a.txt")
        return kind

    monkeypatch.setattr(g, "_stat_kind", swapped)
    with pytest.raises(SystemExit, match="plain file"):
        g.copy_without_folder(repo, _cfg(), tmp_path / "copy")
        raise AssertionError("a path swapped for a link was copied through")
    assert (
        not (tmp_path / "copy" / "docs" / "a.txt").exists()
        or (tmp_path / "copy" / "docs" / "a.txt").read_text(encoding="utf-8") != "outside content\n"
    ), "the content behind the swapped link reached the copy"


def test_the_copy_run_does_not_start_when_the_scan_has_a_hit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # fails on old code: the copy run did not run the scan itself
    repo = _tracked_repo(tmp_path / "r", {"src/pkg/bad.py": f"import {FOLDER}\n"})
    called: list[str] = []
    real_run = subprocess.run

    def watch(argv: list[str], **kw: Any) -> subprocess.CompletedProcess[bytes]:
        if (
            Path(argv[0]).name != "git"
        ):  # the scan asks git for the file list; only other processes (pytest) count
            called.append(" ".join(map(str, argv)))
        return real_run(argv, **kw)

    monkeypatch.setattr(fixed_run.subprocess, "run", watch)
    rc = g.run_without_folder(repo, _cfg(), [])
    out = capsys.readouterr().out
    assert rc == 1 and "names-demo-only-folder" in out and "copy run is not started" in out, (
        f"the scan hit did not stop the copy run (rc {rc}): {out!r}"
    )
    assert called == [], f"processes were started although the scan had a hit: {called}"


def test_an_entry_that_cannot_be_inspected_is_a_hit_or_present_never_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # fails on old code: Path.is_dir and is_file swallowed ELOOP, ENOTDIR and EACCES and read the
    # entry as absent
    import errno

    repo = _tracked_repo(tmp_path / "r", {"tools/loader.py": f"# {FOLDER}\n"})
    real = os.lstat

    def failing(error: BaseException, ending: str):
        def lstat(path, *a, **kw):
            if str(path).endswith(ending):
                raise error
            return real(path, *a, **kw)

        return lstat

    for error in (
        OSError(errno.ELOOP, "loop"),
        NotADirectoryError(errno.ENOTDIR, "x"),
        PermissionError(errno.EACCES, "x"),
    ):
        label = type(error).__name__ + "/" + errno.errorcode[error.errno or 0]
        with monkeypatch.context() as m:
            m.setattr(os, "lstat", failing(error, "/src"))
            got = [h.split(" (")[0] for h in g.scan(repo, _cfg())]
        assert "src: unreadable-file" in got, (
            f"{label}: a product root that cannot be inspected was read as {got}"
        )
        with monkeypatch.context() as m:
            m.setattr(os, "lstat", failing(error, f"/{FOLDER}"))
            present = g._folder_present(repo, _cfg())
        assert present is True, (
            f"{label}: a demo-only folder that cannot be inspected was read as absent"
        )
        with monkeypatch.context() as m:
            m.setattr(os, "lstat", failing(error, "tools/loader.py"))
            got = [h.split(" (")[0] for h in g.scan(repo, _cfg(loaders=("tools/loader.py",)))]
        assert "tools/loader.py: unreadable-file" in got, (
            f"{label}: a loader that cannot be inspected: {got}"
        )
    with monkeypatch.context() as m:
        m.setattr(os, "lstat", failing(FileNotFoundError(errno.ENOENT, "gone"), f"/{FOLDER}"))
        assert g._folder_present(repo, _cfg()) is False, (
            "a folder the system says is not there was read as present"
        )


def test_if_present_and_require_do_not_take_an_unreadable_folder_for_a_missing_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # passes on old code too (run, see the fail-before log): it pins that an unreadable folder is never read as missing
    import errno

    repo = _tracked_repo(tmp_path / "r")
    real = os.lstat

    def lstat(path, *a, **kw):
        if str(path).endswith(f"/{FOLDER}"):
            raise OSError(errno.ELOOP, "loop")
        return real(path, *a, **kw)

    monkeypatch.setattr(os, "lstat", lstat)
    cfg_path = ROOT / "tools" / "demo_only_guard.toml"
    rc = g.main(["--root", str(repo), "--config", str(cfg_path), "--without-folder-if-present"])
    assert rc != 0, (
        "--without-folder-if-present skipped the copy run for a folder it could not inspect"
    )
    rc = g.main(["--root", str(repo), "--config", str(cfg_path), "--require"])
    assert rc != 2, "--require called a folder it could not inspect missing"
    capsys.readouterr()


def test_a_file_the_person_running_the_guard_ignores_for_themselves_is_still_scanned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # fails on old code: core.excludesFile of the global git config hid the untracked file from the
    # scan
    home = tmp_path / "home"
    (home / ".config" / "git").mkdir(parents=True)
    ignore = home / "my-ignore"
    ignore.write_text("src/pkg/secret_*.py\n", encoding="utf-8")
    (home / ".gitconfig").write_text(f"[core]\n\texcludesFile = {ignore}\n", encoding="utf-8")
    (home / ".config" / "git" / "ignore").write_text("src/pkg/xdg_*.py\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    repo = _repo(
        tmp_path / "r",
        {
            **CLEAN,
            "src/pkg/secret_a.py": f"import {FOLDER}\n",
            "src/pkg/xdg_b.py": f"import {FOLDER}\n",
            "src/pkg/ignored_here.py": f"import {FOLDER}\n",
            ".gitignore": "ignored_here.py\n",
        },
    )
    assert "src/pkg/secret_a.py" in g.tracked_paths(repo), (
        "a file in the person's own ignore file was hidden"
    )
    assert "src/pkg/xdg_b.py" in g.tracked_paths(repo), "a file in the XDG ignore file was hidden"
    assert "src/pkg/ignored_here.py" not in g.tracked_paths(repo), (
        "the repository's own .gitignore is no longer honoured"
    )
    got = [h.split(":")[0] for h in g.scan(repo, _cfg())]
    assert "src/pkg/secret_a.py" in got and "src/pkg/xdg_b.py" in got, (
        f"the scan did not reach the hidden files: {got}"
    )


# -- batch 8: the copy run and the scan decide paths from the file system, not from text (class E)
# ------------------------
def test_two_chained_links_cannot_lead_the_copy_run_out_of_the_copy(tmp_path: Path) -> None:
    # proof (fails on old code: each target was worked out by text, so `k -> ..` then `l ->
    # k/../../outside` passed)
    cases = {
        "k-then-l": {"docs/k": "..", "docs/l": "k/../../outside"},
        "nested": {"a/b/link1": "../..", "a/link2": "b/link1/../.."},
    }
    for label, links in cases.items():
        repo = _tracked_repo(tmp_path / label, {"docs/readme.txt": "x\n", "a/b/f.txt": "x\n"})
        for rel, target in links.items():
            os.symlink(target, repo / rel)
        _track(repo)
        with pytest.raises(SystemExit, match="symlink"):
            g.copy_without_folder(repo, _cfg(), tmp_path / f"copy-{label}")
            raise AssertionError(f"{label}: two chained links were copied")


def test_a_loop_of_tracked_links_stops_the_copy_run_and_a_safe_link_is_still_copied(
    tmp_path: Path,
) -> None:
    # proof (fails on old code: the text check passed `a -> b`, `b -> a`)
    repo = _tracked_repo(tmp_path / "loop", {"docs/readme.txt": "x\n"})
    os.symlink("b", repo / "docs" / "a")
    os.symlink("a", repo / "docs" / "b")
    _track(repo)
    with pytest.raises(SystemExit, match="loop"):
        g.copy_without_folder(repo, _cfg(), tmp_path / "copy-loop")
        raise AssertionError("a loop of links was copied")
    fine = _tracked_repo(tmp_path / "fine", {"docs/readme.txt": "x\n"})
    os.symlink("readme.txt", fine / "docs" / "ok")
    _track(fine)
    g.copy_without_folder(fine, _cfg(), tmp_path / "copy-fine")
    assert (tmp_path / "copy-fine" / "docs" / "ok").read_text(encoding="utf-8") == "x\n"


def test_a_parent_folder_swapped_for_a_link_between_the_check_and_the_open_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # proof (fails on old code: O_NOFOLLOW guarded the last component only, so a swapped parent was
    # read through)
    repo = _tracked_repo(tmp_path / "r", {"docs/a.txt": "plain\n"})
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "a.txt").write_text("outside content\n", encoding="utf-8")
    real = g._stat_kind

    def swapped(path: Path) -> str:
        kind = real(path)
        if str(path).endswith("docs/a.txt") and (repo / "docs").is_dir():
            (repo / "docs").rename(tmp_path / "docs-moved")
            os.symlink(outside, repo / "docs")
        return kind

    monkeypatch.setattr(g, "_stat_kind", swapped)
    with pytest.raises(SystemExit, match="plain file"):
        g.copy_without_folder(repo, _cfg(), tmp_path / "copy")
        raise AssertionError("a swapped parent folder was copied through")
    assert not (tmp_path / "copy" / "docs" / "a.txt").exists() or (
        (tmp_path / "copy" / "docs" / "a.txt").read_text(encoding="utf-8") != "outside content\n"
    ), "the content behind the swapped parent reached the copy"


def test_without_the_walk_flags_a_link_anywhere_on_the_path_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # pin of the Windows branch (it runs here by switching `_CAN_WALK` off): a link on a parent
    # folder is refused
    repo = _tracked_repo(tmp_path / "r", {"docs/a.txt": "plain\n"})
    monkeypatch.setattr(g, "_CAN_WALK", False)
    g._copy_regular(repo, "docs/a.txt", tmp_path / "plain-copy")
    assert (tmp_path / "plain-copy").read_text(encoding="utf-8") == "plain\n"
    (tmp_path / "real").mkdir()
    (tmp_path / "real" / "a.txt").write_text("x\n", encoding="utf-8")
    os.symlink(tmp_path / "real", repo / "linked")
    with pytest.raises(SystemExit, match="plain file"):
        g._copy_regular(repo, "linked/a.txt", tmp_path / "never")
        raise AssertionError("a link on the path was followed")


def test_a_loop_of_links_is_a_hit_never_a_traceback_even_where_resolve_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # proof (fails on old code: with `Path.resolve` raising RuntimeError, as Python 3.12 does on a
    # loop, the scan died with a traceback; on 3.13 a link outside the product folders that loops
    # was no hit at all)
    repo = _tracked_repo(tmp_path / "r", {"docs/readme.txt": "x\n"})
    os.symlink("loop", repo / "docs" / "loop")
    _track(repo)
    plain = g.scan(repo, _cfg())
    assert any(h.startswith("docs/loop: symlink-loop") for h in plain), (
        f"no symlink-loop hit for a tracked loop in {plain}"
    )

    def raising(self: Path, strict: bool = False) -> Path:
        raise RuntimeError("Symlink loop from " + str(self))

    monkeypatch.setattr(Path, "resolve", raising)
    assert any(h.startswith("docs/loop: symlink-loop") for h in g.scan(repo, _cfg())), (
        "a Python whose Path.resolve raises on a loop gave a traceback or no hit"
    )
    monkeypatch.undo()
    loop_folder = _repo(tmp_path / "f", {"src/pkg/__init__.py": "X = 1\n", MARKER: ""})
    os.symlink(FOLDER, loop_folder / FOLDER)  # the demo-only folder is a loop of links
    _track(loop_folder)
    cfg_file = _toml(tmp_path)
    assert _main(loop_folder, cfg_file) == 1, (
        "a loop as the demo-only folder was not a hit (exit 1)"
    )


def test_a_file_that_vanishes_at_any_point_of_the_scan_is_never_a_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # proof (fails on old code: a second `os.lstat` after `_stat_kind` raised FileNotFoundError for
    # an exempt file)
    files = {"src/pkg/ex.txt": f"names {FOLDER} on purpose\n"}

    def calls_for(vanish_after: int | None) -> int:
        repo = _repo(tmp_path / f"v{vanish_after}", {**CLEAN, **files})
        target = repo / "src/pkg/ex.txt"
        count = [0]
        real = os.lstat

        def counting(path, *a, **k):
            if str(path) == str(target):
                count[0] += 1
                if vanish_after is not None and count[0] == vanish_after + 1 and target.exists():
                    target.unlink()
            return real(path, *a, **k)

        monkeypatch.setattr(os, "lstat", counting)
        g.scan(repo, _cfg(exempt_files=("src/pkg/ex.txt",)))
        monkeypatch.undo()
        return count[0]

    total = calls_for(None)
    assert total >= 1
    for k in range(total + 1):
        calls_for(k)  # must not raise


def test_a_file_in_a_product_folder_is_looked_at_with_one_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # proof (fails on old code: the size came from a second `stat` call on the same file)
    repo = _repo(tmp_path / "r", {**CLEAN, "src/pkg/b.py": "Y = 2\n"})
    seen: dict[str, int] = {}
    real_lstat, real_stat = os.lstat, os.stat

    def count(kind: str, real):
        def inner(path, *a, **k):
            if str(path).endswith("src/pkg/b.py"):
                seen[kind] = seen.get(kind, 0) + 1
            return real(path, *a, **k)

        return inner

    monkeypatch.setattr(os, "lstat", count("lstat", real_lstat))
    monkeypatch.setattr(os, "stat", count("stat", real_stat))
    assert g.scan(repo, _cfg()) == []
    assert seen == {"lstat": 1}, f"calls for one product file: {seen}"


def test_a_failed_git_call_shows_the_first_line_of_gits_own_message_masked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # proof (fails on old code: the message was only "git ls-files failed")
    repo = _repo(tmp_path / "r", CLEAN)
    fake = tmp_path / "bin"
    fake.mkdir()
    script = fake / "git"
    script.write_text(
        "#!/bin/sh\n"
        f"printf 'fatal: detected dubious ownership in repository at %s\\n\\033[31mhint\\n' '{repo}' >&2\n"
        "exit 128\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake}{os.pathsep}{os.environ['PATH']}")
    for call in (g.tracked_paths, g._gitlinks):
        with pytest.raises(SystemExit) as raised:
            call(repo)
        text = str(raised.value)
        assert "detected dubious ownership" in text, f"git's own first line is missing from: {text}"
        assert str(repo) not in text and "<repo>" in text, (
            f"the repository path was not masked: {text}"
        )
        assert "\x1b" not in text and "hint" not in text, (
            f"more than the first line, or a raw escape: {text!r}"
        )


def _only_the_mark_and_nul_bytes(tmp_path: Path, label: str, raw: bytes, kind: str) -> None:
    repo = _repo(tmp_path / label, CLEAN)
    (repo / "src/pkg/blob").write_bytes(raw)
    assert g.scan(repo, _cfg()) == [
        f"src/pkg/blob: binary-in-product-root (the file is {kind}, whatever its ending says)"
    ], f"{label}: a file of only the mark and NUL bytes was not refused as {kind}"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_file_that_is_only_the_mz_mark_and_nul_bytes_is_a_hit(tmp_path: Path) -> None:
    # What it guards against (a fault of the code before batch 8): the mark is valid UTF-8, so such
    # a file was read as text and passed)
    _only_the_mark_and_nul_bytes(tmp_path, "mz", b"MZ" + b"\x00" * 30, "DOS or Windows program")


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_file_that_is_only_the_rar_mark_and_nul_bytes_is_a_hit(tmp_path: Path) -> None:
    # What it guards against (a fault of the code before batch 8): the mark is valid UTF-8, so such
    # a file was read as text and passed)
    _only_the_mark_and_nul_bytes(tmp_path, "rar", b"Rar!\x1a\x07\x00" + b"\x00" * 8, "RAR")


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_plain_text_that_starts_like_a_mark_and_utf16_text_are_not_hits(tmp_path: Path) -> None:
    # What it guards against (a fault of the code before batch 8): it needs the kinds to exist;
    # otherwise a pin that text is not refused)
    text = _repo(tmp_path / "text", {**CLEAN, "src/pkg/a.txt": "MZ is fine as text, so is Rar!\n"})
    assert g.scan(text, _cfg()) == [], "plain text that starts like a mark was refused"
    utf16 = _repo(tmp_path / "u16", CLEAN)
    (utf16 / "src/pkg/clean.txt").write_bytes("hello\n".encode("utf-16-le"))
    assert g.scan(utf16, _cfg()) == [], (
        "clean UTF-16 text was refused: a NUL byte alone is not a hit"
    )


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_bzip2_needs_a_level_from_1_to_9() -> None:
    # What it guards against (a fault of the code before batch 8): the level byte was not looked
    # at). On purpose, level 0 and ":" are not bzip2: the format has levels 1 to 9, so a file with
    # another level byte is not a valid bzip2 file.
    for head, is_bzip2 in (
        (b"BZh1" + b"1AY&SY", True),
        (b"BZh9" + b"\x17rE8P\x90", True),
        (b"BZh0" + b"1AY&SY", False),
        (b"BZh:" + b"1AY&SY", False),
        (b"BZha" + b"1AY&SY", False),
    ):
        got = g._magic_kind(head + b"rest")
        assert (got == "bzip2") == is_bzip2, f"bzip2 level check: {head!r} was read as {got!r}"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_bzip2_needs_a_block_or_end_of_stream_mark() -> None:
    # What it guards against (a fault of the code before batch 8): the mark after the level byte was
    # not looked at). On purpose, a bad block mark is not bzip2.
    for head, is_bzip2 in (
        (b"BZh9" + b"XXXXXX", False),
        (b"BZh5" + b"1AY&SX", False),
        (b"BZh", False),
        (b"BZh5" + b"1AY&SY", True),
    ):
        got = g._magic_kind(head + b"rest")
        assert (got == "bzip2") == is_bzip2, f"bzip2 mark check: {head!r} was read as {got!r}"
    assert g._magic_kind(b"BZh") == "", "three letters alone were read as bzip2"


# The places that list the tracked files of the repository. The CHANGELOG states how many there are
# and names each of them; the test below compares exactly these, and
# `tests/test_changelog_numbers.py` reads this table, so the count is written once.
LISTING_FILES = ("tools/demo_only_guard.py", "tools/scan_repo.py", "tests/test_repo_rules.py")
SUPERSET_FILE = "tests/test_no_reference_material.py"  # walks the folder on purpose; only checked to hold every tracked file


def test_the_listings_of_tracked_files_agree_on_a_repo_with_a_global_ignore_file_and_an_unusual_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Decision (also in the CHANGELOG): core has no shared helper, so the guard,
    # `tools/scan_repo.py` and `tests/test_repo_rules.py` each ask `git ls-files` for the TRACKED
    # files (exact names, `-z`), and these THREE listings must be equal;
    # `tests/test_no_reference_material.py` walks the folder on purpose (an untracked copy of a
    # reference file counts too), so it is only a SUPERSET check What it guards: (it must hold every
    # tracked file, and is not compared for equality). Proof (fails only on the code before batch 8:
    # test_repo_rules listed without -z and quoted the name).
    import importlib.util

    from tests.test_repo_rules import tracked_files

    spec = importlib.util.spec_from_file_location(
        "_scan_repo_listing", ROOT / "tools" / "scan_repo.py"
    )
    assert spec is not None and spec.loader is not None
    scan_repo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scan_repo)

    home = tmp_path / "home"
    (home / ".config" / "git").mkdir(parents=True)
    (home / ".config" / "git" / "ignore").write_text("*.secretnote\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    repo = _repo(tmp_path / "r", {**CLEAN, "docs/café.txt": "x\n", "docs/b.secretnote": "x\n"})
    _track(repo)
    (repo / "docs" / "new-not-added.txt").write_text("x\n", encoding="utf-8")

    from_guard = set(g.tracked_paths(repo, include_new=False))
    listings = {
        "tools/demo_only_guard.py": from_guard,
        "tools/scan_repo.py": scan_repo.tracked_paths(repo),
        "tests/test_repo_rules.py": set(tracked_files(repo)),
    }
    assert tuple(listings) == LISTING_FILES, (
        "the table of listings and the listings compared differ"
    )
    assert all(listing == from_guard for listing in listings.values()), listings
    assert "docs/café.txt" in from_guard and "docs/new-not-added.txt" not in from_guard
    # the guard's default listing adds files not yet added, and still lists one a user-level ignore
    # file hides
    assert "docs/new-not-added.txt" in g.tracked_paths(repo)
    assert "docs/b.secretnote" in g.tracked_paths(repo) and "docs/b.secretnote" not in from_guard

    walk_spec = importlib.util.spec_from_file_location("_no_ref_listing", ROOT / SUPERSET_FILE)
    assert walk_spec is not None and walk_spec.loader is not None
    nr = importlib.util.module_from_spec(walk_spec)
    walk_spec.loader.exec_module(nr)
    monkeypatch.setattr(nr, "ROOT", repo)
    assert from_guard <= set(nr._tracked()), "the folder walk misses a tracked file"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_git_message_hides_names_with_key_or_token() -> None:
    # What it guards against (a fault of the code before batch 8): the whole first line of git was
    # shown as it came)
    line = (
        "fatal: bypass_key=abc123 bypass_token=def456 url https://user:pw@host/x.git "
        "plain Bearer yyyy Authorization: Bearer zzz9"
    )
    shown = g._git_failure("git ls-files failed", line.encode(), Path("/nowhere"))
    for secret in ("abc123", "def456", "user:pw", "zzz9"):
        assert secret not in shown, f"a secret value was shown: {secret}"
    assert "bypass_key=<hidden>" in shown and "bypass_token=<hidden>" in shown, shown
    assert "Bearer yyyy" in shown, f"a bare scheme word was changed: {shown}"


# -- batch 9: the git-message masker (class 4) and the guard minors (class 5)
# --------------------------------------------- Every fake value below is built from parts: no
# secret-shaped literal sits in this file.
TOK = "to" + "ken"
PW = "pass" + "word"
SEC = "sec" + "ret"


def _core(name: str) -> re.Pattern[str]:
    redact = importlib.import_module(
        "hadavin_sdk.guard.redact"
    )  # not `from ... import redact`: the package exports a function of that name

    return dict(redact.PATTERNS)[name]


def test_the_guard_bearer_and_basic_patterns_are_the_text_of_the_core_ones() -> None:
    # what it shows (there were no such patterns here)
    assert (
        g._BEARER.pattern == _core("BEARER").pattern and g._BEARER.flags == _core("BEARER").flags
    ), "the guard BEARER pattern differs from the core one"
    assert g._BASIC.pattern == _core("BASIC").pattern and g._BASIC.flags == _core("BASIC").flags, (
        "the guard BASIC pattern differs from the core one"
    )


# fail-before (real run on dd827d79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
# fail-before (real run on c7eb5c79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_a_bare_scheme_word_hides_at_least_what_the_core_hides_by_a_table() -> None:
    # letters only: the guard and the core agree (the rows where the guard hides more are in the
    # next test)
    for scheme, core, low in (
        ("Bearer", "BEARER", 12),
        ("basic", "BASIC", 8),
        ("BEARER", "BEARER", 12),
    ):
        for n in (low - 1, low, low + 1, 40):
            token = ("a" * 30)[
                :n
            ]  # letters only: a token that mixes digits is hidden at any length
            line = f"x {scheme} {token} y"
            hidden = g._hide_secrets(line)
            m = _core(core).search(line)
            expected = line if m is None else line.replace(m.group(1), "<hidden>", 1)
            assert hidden == expected, (
                f"{scheme} {n}: the guard and the core disagree: {hidden!r} vs {expected!r}"
            )
            assert (token in hidden) == (n < low), (
                f"{scheme} {n} characters: visible or hidden wrongly: {hidden!r}"
            )


# fail-before (real run on dd827d79, batch 14): it FAILS there, first failing line: AssertionError: a stated row differs: 'x Bearer a1b2c3 y' gave 'x Bearer a1b2c3 y'
# fail-before (real run on c7eb5c79, batch 14): it FAILS there, first failing line: AssertionError: a stated row differs: 'x Bearer a1b2c3 y' gave 'x Bearer a1b2c3 y'
def test_a_bare_scheme_word_rows_where_the_guard_differs_from_the_core_are_the_stated_ones() -> (
    None
):
    # (line, what the guard shows, whether the core hides a token in it). Intended differences: the
    # guard hides more.
    rows = (
        (
            "x Bearer a1b2c3 y",
            "x Bearer <hidden> y",
            False,
        ),  # mixed letters and digits, 6 characters
        ("x Basic a1b2 y", "x Basic <hidden> y", False),  # mixed, 4 characters
        (
            "x Basic abc-defghijk y",
            "x Basic abc-defghijk y",
            False,
        ),  # 12 with a dash: shown, as the core
        (
            "x Basic abc-defghijklmnop y",
            "x Basic <hidden> y",
            False,
        ),  # 17 with a dash: hidden, the core shows it
        ('authorization=Bearer "abc def" tail', "authorization=<hidden> tail", False),
        ("authorization=Bearer abcdefgh x", "authorization=<hidden> x", False),
    )
    for line, guard_shows, core_hides in rows:
        core_does = any(_core(name).search(line) for name in ("BEARER", "BASIC"))
        assert core_does == core_hides, (
            f"the row says the core hides {line!r}: {core_hides}, it does: {core_does}"
        )
        shown = g._hide_secrets(line)
        assert shown == guard_shows, f"a stated row differs: {line!r} gave {shown!r}"


# fail-before (real run on dd827d79, batch 14): it FAILS there, first failing line: AssertionError: a 17 character Basic token with a dash stayed visible
# fail-before (real run on c7eb5c79, batch 14): it FAILS there, first failing line: AssertionError: a 17 character Basic token with a dash stayed visible
def test_a_basic_token_of_17_characters_with_a_dash_is_hidden_where_the_core_shows_it() -> None:
    line = "x Basic abc-defghijklmnop y"
    assert _core("BASIC").search(line) is None, (
        "the core hides it: this is not a difference any more"
    )
    assert g._hide_secrets(line) == "x Basic <hidden> y", (
        "a 17 character Basic token with a dash stayed visible"
    )


# fail-before (real run on dd827d79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
# fail-before (real run on c7eb5c79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_basic_token_of_12_characters_with_a_dash_stays_visible_as_in_the_core() -> None:
    line = "x Basic abc-defghijk y"
    assert g._hide_secrets(line) == line, "a 12 character Basic token with a dash was hidden"


# fail-before (real run on dd827d79, batch 14): it FAILS there, first failing line: AssertionError: the quoted authorization value was not hidden whole
# fail-before (real run on c7eb5c79, batch 14): it FAILS there, first failing line: AssertionError: the quoted authorization value was not hidden whole
def test_a_quoted_authorization_value_after_a_scheme_word_is_hidden_whole() -> None:
    shown = g._hide_secrets('authorization=Bearer "abc def" tail')
    assert shown == "authorization=<hidden> tail", (
        "the quoted authorization value was not hidden whole"
    )


def test_a_bearer_token_of_11_and_a_basic_token_of_7_stay_visible() -> None:
    # what it shows (nothing was hidden, so the 12 and 8 sides fail; the 11 and 7 sides are pins)
    assert "Bearer " + "a" * 11 in g._hide_secrets("Bearer " + "a" * 11), (
        "a bearer token of 11 characters was hidden"
    )
    assert "Basic " + "b" * 7 in g._hide_secrets("Basic " + "b" * 7), (
        "a basic token of 7 characters was hidden"
    )
    assert "a" * 12 not in g._hide_secrets("Bearer " + "a" * 12), (
        "a bearer token of 12 characters was shown"
    )
    assert "b" * 8 not in g._hide_secrets("Basic " + "b" * 8), (
        "a basic token of 8 characters was shown"
    )
    assert "<hidden>" in g._hide_secrets("Bearer " + "a" * 12 + "=="), (
        "a bearer token with padding was shown"
    )


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: Bearer 8 characters stayed visible: 'fatal: authorization=<hidden> qqqqqqqq tail'
def test_authorization_pair_with_a_scheme_word_hides_the_token_at_8_10_and_11_characters() -> None:
    # what it shows (`authorization=Bearer <token>` of 8, 10 or 11 characters stayed visible; the
    # core hides them)
    for n in (8, 10, 11):
        token = "q" * n
        for scheme in ("Bearer", "bearer", "Basic"):
            shown = g._hide_secrets(f"fatal: authorization={scheme} {token} tail")
            assert token not in shown, f"{scheme} {n} characters stayed visible: {shown!r}"
    # the colon header form and the `token=Bearer` form are unchanged
    assert g._hide_secrets("authorization: Bearer " + "q" * 8) == "authorization: <hidden>"
    assert "q" * 11 in g._hide_secrets(f"{TOK}=Bearer " + "q" * 11), (
        "the stated 11 character limit moved"
    )


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: a hidden-side value stayed visible, bypass=abc123: 'bypass=abc123 tail'
def test_a_bare_word_bypass_is_hidden_unless_its_value_is_a_plain_on_off_word() -> None:
    # visible side
    for line in (
        "bypass=true",
        "BYPASS=False",
        "bypass=Yes",
        "bypass=no",
        "bypass=ON",
        "bypass=off",
        "bypass=0",
        "bypass=1  ",
    ):
        assert g._hide_secrets(line) == line, f"a plain flag was hidden: {line!r}"
    # hidden side: any other value, a flag with more stuck to it, case does not matter
    for value in ("abc123", "truex", "true,abc123", "2", "yes!", "Secret7"):
        for name in ("bypass", "BYPASS", "Bypass"):
            shown = g._hide_secrets(f"{name}={value} tail")
            assert shown == f"{name}=<hidden> tail", (
                f"a hidden-side value stayed visible, {name}={value}: {shown!r}"
            )
    # nothing after the value (the end of the line): only a plain on/off word is shown
    for line in (
        "bypass=abc123",
        "bypass=truex",
        "bypass=2",
        "x bypass=yes!",
        "bypass=true,abc123",
    ):
        shown = g._hide_secrets(line)
        assert "<hidden>" in shown, (
            f"a hidden-side value at the end of the line stayed visible: {line!r}"
        )
    # a plain word followed by anything else on the line is hidden (only the end of the line may
    # follow it)
    assert g._hide_secrets("bypass=true x") == "bypass=<hidden> x", (
        "a flag with a word after it was shown"
    )
    assert g._hide_secrets("a=b bypass=Off y=1") == "a=b bypass=<hidden> y=1"
    assert g._hide_secrets("bypass=true") == "bypass=true"
    assert g._hide_secrets("bypass_ke" + "y=true") == "bypass_ke" + "y=<hidden>"
    assert g._hide_secrets("bypass_" + TOK + "=true") == "bypass_" + TOK + "=<hidden>"


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: Bearer 11 mixed characters stayed: 'x Bearer a1a1a1a1a1a y'
def test_a_bare_scheme_word_hides_a_token_of_16_or_more_or_one_that_mixes_letters_and_digits() -> (
    None
):
    assert "<hidden>" in g._hide_secrets("Bearer " + "a" * 16), "a 16 letter bearer token stayed"
    assert "<hidden>" in g._hide_secrets("Basic " + "a" * 16), "a 16 letter basic token stayed"
    for scheme, n in (("Bearer", 11), ("Bearer", 3), ("basic", 7), ("BASIC", 2)):
        token = ("a1" * 10)[:n]
        shown = g._hide_secrets(f"x {scheme} {token} y")
        assert token not in shown, f"{scheme} {n} mixed characters stayed: {shown!r}"
    assert "Bearer " + "a" * 11 in g._hide_secrets("Bearer " + "a" * 11), (
        "letters only: still the core limit"
    )
    assert "Basic " + "b" * 7 in g._hide_secrets("Basic " + "b" * 7)


def test_after_an_authorization_header_name_everything_to_the_end_of_the_line_is_hidden() -> None:
    # what it shows (only two words were hidden, so a Digest header leaked)
    for scheme in ("Digest", "Basic", "Bearer", "Negotiate", ""):
        line = f"Authorization: {scheme} u1=aaaa, r2=bbbb, n3=cccc"
        shown = g._hide_secrets(line)
        assert shown == "Authorization: <hidden>", f"header scheme {scheme!r}: {shown!r}"
    assert (
        g._hide_secrets("fatal: authorization:abcdef tail") == "fatal: authorization: <hidden>"
    ), "a header written in lower case or without a space was shown"


def test_a_name_value_pair_hides_quoted_and_odd_values_and_the_wider_name_list() -> None:
    # what it shows (quoted values, inner quotes, passwd/pwd/auth/credential were shown or cut)
    for name in (
        PW,
        TOK,
        SEC,
        "pass" + "wd",
        "p" + "wd",
        "au" + "th",
        "cred" + "ential",
        "api_ke" + "y",
        PW.upper(),
    ):
        for value in ("abc123", "ab'cd", "ab&cd", 'ab"cd', "ab=cd"):
            shown = g._hide_secrets(f"fatal: {name}={value} tail")
            assert shown == f"fatal: {name}=<hidden> tail", f"unquoted {name}={value!r}: {shown!r}"
        for quoted in ('"ab cd\'ef"', "'ab cd\"ef'", '"ab \\" cd"'):
            shown = g._hide_secrets(f"fatal: {name}={quoted} tail")
            assert shown == f"fatal: {name}=<hidden> tail", f"quoted {name}={quoted}: {shown!r}"
    assert g._hide_secrets("a=b bypass=true") == "a=b bypass=true", (
        "a plain flag at the end was hidden"
    )
    assert g._hide_secrets("bypass_ke" + "y=1") == "bypass_ke" + "y=<hidden>", (
        "bypass_key was shown"
    )
    assert g._hide_secrets("bypass_" + TOK + "=1") == "bypass_" + TOK + "=<hidden>", (
        "bypass_token was shown"
    )
    assert g._hide_secrets(PW + "=") == PW + "=<hidden>", "an empty value was not marked"


def test_url_credentials_are_hidden_up_to_the_last_at_sign_whatever_they_hold() -> None:
    # what it shows (an `@` or `/` inside the password left part of it visible)
    for cred in ("user:pw", "user:p@ss", "user:p/ss", "user:p@s/s@x", "u"):
        shown = g._hide_secrets(f"fatal: unable to access https://{cred}@host.example/x.git here")
        assert shown == "fatal: unable to access https://<hidden>@host.example/x.git here", (
            f"url credentials {cred!r}: {shown!r}"
        )
    assert (
        g._hide_secrets("see https://host.example/x.git and ssh://h/p")
        == "see https://host.example/x.git and ssh://h/p"
    ), "a url without credentials was changed"
    assert g._hide_secrets("a://://://@h") == "a://<hidden>@h", (
        "repeated scheme marks were not handled"
    )


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_masker_costs_time_in_proportion_to_the_line_and_never_raises_on_a_long_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Counted work, not seconds: the number of characters the name check reads and the output length
    # are bounded by the line length. (The old quadratic pattern is shown by
    # `test_pin_the_masker_hides_a_line_of_60000_characters_in_under_5_seconds`.)
    for line in (
        "a-" * 5000,
        "=" * 10000,
        "://" * 3333 + "@",
        "bearer " + "a" * 9990,
        "k=" * 5000,
        "'" * 10000,
    ):
        shown = g._hide_secrets(line)
        assert isinstance(shown, str) and len(shown) <= 10 * len(line), len(shown)
    steps = 0
    real = g._SECRET_NAME.search

    class Counting:
        def search(self, text: str):
            nonlocal steps
            steps += len(text)
            return real(text)

    monkeypatch.setattr(g, "_SECRET_NAME", Counting())
    g._hide_secrets("a=" * 5000 + "x-" * 5000)
    assert steps <= 3 * 10000, f"the name check read {steps} characters for a 20000 character line"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_masker_hides_a_line_of_60000_characters_in_under_5_seconds() -> None:
    # what it keeps (also: fails on 07bfda12, whose `[\w.-]*` pattern is quadratic on a long run of
    # name characters, with no name of the new code needed): a wide bound only, not a ratio of two
    # timings: a line of 60000 characters is hidden in under 5 seconds (linear: a few milliseconds;
    # quadratic: minutes). The exact check is the count of steps in
    # `test_pin_the_masker_pair_step_reads_each_character_a_bounded_number_of_times_whatever_the_line`.
    import time

    t0 = time.perf_counter()
    g._hide_secrets("a-" * 30000)
    took = time.perf_counter() - t0
    assert took < 5.0, f"a line of 60000 characters took {took:.1f} seconds"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_masker_pair_step_reads_each_character_a_bounded_number_of_times_whatever_the_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Counted work, not seconds, and ONLY for the pair step (the `name=value` search): characters
    # handed to the name pattern plus the calls of the name-character test; the header, bearer,
    # basic and URL steps are not counted here. Lines with many `=` and short names (a quadratic
    # pair step would search the whole text before each `=` again), one long name, many
    # secret-looking names. The bound is 4 reads of a character; a linear pass reads each one about
    # once or twice.
    steps = 0
    real_search, real_char = g._SECRET_NAME.search, g._is_name_char

    class Counting:
        def search(self, text: str):
            nonlocal steps
            steps += len(text)
            return real_search(text)

    def counting_char(c: str) -> bool:
        nonlocal steps
        steps += 1
        return real_char(c)

    monkeypatch.setattr(g, "_SECRET_NAME", Counting())
    monkeypatch.setattr(g, "_is_name_char", counting_char)
    for line in (
        "ab=" * 3000,
        "a-" * 5000,
        "a=" * 5000 + "x-" * 5000,
        f"{TOK}=v " * 2000,
        "k=" * 5000,
    ):
        steps = 0
        shown = g._hide_secrets(line)
        assert len(shown) <= 10 * len(line)
        assert steps <= 4 * len(line), (
            f"{steps} reads for a line of {len(line)} characters ({line[:12]!r}...)"
        )


def _a_scheme_after_a_secret_name(scheme: str, token: str) -> None:
    for name in ("authorization", "auth", SEC, TOK, PW, "api_ke" + "y"):
        for tail in ("", " tail"):
            line = f"fatal: {name}={scheme} {token}{tail}"
            shown = g._hide_secrets(line)
            assert token not in shown, f"{name}={scheme}: the token stayed visible: {shown!r}"


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: authorization=Bearer: the token stayed visible: 'fatal: authorization=<hidden> a1a1a1a1a1a1a1a1a1a1'
def test_a_bearer_token_after_a_secret_looking_name_is_hidden_with_its_scheme_word() -> None:
    # what it shows (the pair step ran first and hid only the word `Bearer`, leaving the token in
    # clear)
    _a_scheme_after_a_secret_name("Bearer", "a1" * 10)


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: authorization=Basic: the token stayed visible: 'fatal: authorization=<hidden> b2b2b2b2b2b2'
def test_a_basic_token_after_a_secret_looking_name_is_hidden_with_its_scheme_word() -> None:
    # what it shows (the pair step ran first and hid only the word `Basic`, leaving the token in
    # clear)
    _a_scheme_after_a_secret_name("Basic", "b2" * 6)


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_colon_form_is_left_alone_by_the_masker() -> None:
    # pin: only `name=value` pairs are hidden; the colon form is a stated limit (see the comment
    # above `_BEARER`), shown here by behaviour. A made-up value built from parts.
    value = "v1" * 6
    for line in (f"fatal: {PW}: {value}", f'fatal: "{TOK}": "{value}"', f"fatal: --{PW} {value}"):
        assert g._hide_secrets(line) == line, (
            f"the colon form was changed: {g._hide_secrets(line)!r}"
        )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a 12 character token stayed
def test_a_bearer_token_of_11_characters_stays_visible_as_on_main() -> None:
    # pin: the bearer rule needs 12 or more characters, as on main (`hadavin_sdk.guard.redact`), so
    # a shorter token after a name stays visible; 12 characters are hidden. A made-up token built
    # from parts.
    short, long_ = "c" * 11, "c3" * 6
    assert len(short) == 11 and len(long_) == 12
    assert short in g._hide_secrets(f"fatal: {TOK}=Bearer {short}"), (
        "an 11 character token was hidden"
    )
    assert long_ not in g._hide_secrets(f"fatal: {TOK}=Bearer {long_}"), (
        "a 12 character token stayed"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: assert 'fatal: autho...1a1a1a1a1a1a1' == 'fatal: autho...den> <hidden>'
def test_the_masker_hides_the_scheme_word_and_the_token_of_a_bearer_and_a_basic_line() -> None:
    # what it shows (the line stayed `authorization=<hidden> a1a1...`, the token in clear)
    assert (
        g._hide_secrets("fatal: authorization=Bearer " + "a1" * 10)
        == "fatal: authorization=<hidden> <hidden>"
    )
    assert (
        g._hide_secrets("fatal: authorization=Basic " + "b2" * 6)
        == "fatal: authorization=<hidden> <hidden>"
    )


def test_a_fat_mach_o_with_64_bit_offsets_is_a_hit_in_both_byte_orders(tmp_path: Path) -> None:
    # what it shows (cafebabf and bfbafeca were not recognised)
    for raw in (b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"):
        repo = _repo(tmp_path / raw.hex(), CLEAN)
        (repo / "src/pkg/blob.dat").write_bytes(raw + b"\x00" * 20)
        assert g.scan(repo, _cfg()) == [
            "src/pkg/blob.dat: binary-in-product-root (the file is fat Mach-O or Java class file, whatever its ending says)"
        ], f"fat Mach-O 64 mark {raw.hex()} was not a hit"


def test_the_compiled_python_range_follows_the_running_interpreter_and_python_2_is_not_read(
    tmp_path: Path,
) -> None:
    # what it shows (the range was 3000-3999 only, a fixed number)
    running = int.from_bytes(importlib.util.MAGIC_NUMBER[:2], "little")
    assert 3000 <= running <= g._PYC_MAGIC_MAX
    assert g._PYC_MAGIC_MAX == min(8191, max(3999, running + 1000)), (
        "the upper end is not derived from the running interpreter"
    )
    assert g._magic_kind(importlib.util.MAGIC_NUMBER + b"\x00" * 20) == "compiled Python"
    assert (
        g._magic_kind((20121).to_bytes(2, "little") + b"\r\n" + b"\x00" * 20) == ""
    )  # Python 1.5/2.x: letters, not read
    assert g._magic_kind(b"ab\r\nsome text") == ""


def test_a_file_that_swaps_the_link_target_of_a_copied_link_is_refused_in_plain_words(
    tmp_path: Path,
) -> None:
    # what it shows (os.readlink raised an unhandled OSError when the link had become a file)
    dest = tmp_path / "copy"
    dest.mkdir()
    (dest / "plain.txt").write_text("not a link\n", encoding="utf-8")
    for name in ("plain.txt", "gone.txt"):
        got = g._link_problem(dest, name, dest, FOLDER)
        assert got == "changed while it was being checked", (
            f"a swapped link was not refused: {name}: {got!r}"
        )


def test_the_link_chain_message_says_too_long_or_looped(tmp_path: Path) -> None:
    # what it shows (the text said "loop" for any ELOOP)
    dest = tmp_path / "copy"
    dest.mkdir()
    (dest / "a").symlink_to("b")
    (dest / "b").symlink_to("a")
    got = g._link_problem(dest, "a", dest, FOLDER)
    assert got == "is a link chain that is too long or loops", (
        f"the link chain wording is wrong: {got!r}"
    )


def test_a_tracked_file_whose_parent_folder_became_a_link_is_a_link_hit(tmp_path: Path) -> None:
    # what it shows (the file was lstat'ed through the swapped folder and read as a plain file)
    repo = _track(_repo(tmp_path / "r", {**CLEAN, "src/pkg/sub/inner.txt": "plain\n"}))
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "inner.txt").write_text("plain\n", encoding="utf-8")
    shutil.rmtree(repo / "src/pkg/sub")
    (repo / "src/pkg/sub").symlink_to(outside)
    hits = g.scan(repo, _cfg())
    assert any(h.startswith("src/pkg/sub/inner.txt:") and "symlink" in h for h in hits), (
        f"a file behind a swapped folder was read through it: {hits}"
    )


def test_the_module_docstring_lists_exactly_the_kinds_of_first_bytes_in_the_table() -> None:
    # what it shows (the docstring listed 9 kinds, the table has 12)
    doc = " ".join((g.__doc__ or "").split())
    start = doc.index("first bytes are the mark of one of `MAGIC_KINDS` (") + len(
        "first bytes are the mark of one of `MAGIC_KINDS` ("
    )
    listed = doc[start : doc.index(":", start)]
    assert listed == ", ".join(g.MAGIC_KINDS), (
        f"the docstring lists {listed!r}, the table has {g.MAGIC_KINDS!r}"
    )


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_copy_keeps_the_file_mode_where_os_has_no_fchmod(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # what it shows (os.fchmod was called unguarded, an AttributeError where it is absent (Windows
    # before 3.13))
    repo = tmp_path / "r"
    (repo / "d").mkdir(parents=True)
    (repo / "d" / "run.sh").write_text("x\n", encoding="utf-8")
    (repo / "d" / "run.sh").chmod(0o751)
    monkeypatch.delattr(os, "fchmod", raising=False)
    target = tmp_path / "out.sh"
    g._copy_regular(repo, "d/run.sh", target)
    # the mode first: a copy with mode 0 cannot be read by an ordinary user, and a read before the
    # mode would end in a crash (PermissionError) instead of this assertion
    assert stat.S_IMODE(target.stat().st_mode) == 0o751, "the mode was not copied without fchmod"
    assert target.read_text(encoding="utf-8") == "x\n"


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_copy_keeps_the_file_mode_when_os_has_fchmod(tmp_path: Path) -> None:
    # what it shows (no test read the mode of a copy made through `fchmod`, so a wrong mode went
    # unseen)
    repo = tmp_path / "r"
    (repo / "d").mkdir(parents=True)
    (repo / "d" / "run.sh").write_text("x\n", encoding="utf-8")
    (repo / "d" / "run.sh").chmod(0o751)
    target = tmp_path / "out.sh"
    g._copy_regular(repo, "d/run.sh", target)
    assert stat.S_IMODE(target.stat().st_mode) == 0o751, (
        f"the mode of the copy is {oct(stat.S_IMODE(target.stat().st_mode))}, not 0o751"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a bare OSError came out of the copy: OSError(22, 'Invalid argument')
def test_an_entry_swapped_between_the_check_and_the_copy_is_refused_in_words_never_a_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # what it shows (a bare OSError came out of `copy_without_folder`)
    repo = _tracked_repo(tmp_path / "r", {"docs/plain.txt": "x\n"})
    real = g._stat_kind

    def says_link(full: Path | str) -> str:
        return "link" if str(full).endswith("docs/plain.txt") else real(full)

    monkeypatch.setattr(
        g, "_stat_kind", says_link
    )  # the check saw a link; the entry is a file by the time it is read
    try:
        g.copy_without_folder(repo, _cfg(), tmp_path / "copy")
    except SystemExit as exc:
        assert "changed or could not be copied" in str(exc), f"the refusal is not in words: {exc}"
    except OSError as exc:
        raise AssertionError(f"a bare OSError came out of the copy: {exc!r}") from None
    else:
        raise AssertionError("a swapped entry was copied without a word")


def _swap_parent_for_link(repo: Path, parent: str, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    shutil.copytree(repo / parent, outside)
    shutil.rmtree(repo / parent)
    (repo / parent).symlink_to(outside)


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a loader behind a link was read through it: ['src/pkg: symlink-in-product-root', 'src/pkg/__init__.py: symlink-in-produc
def test_a_loader_behind_a_folder_that_became_a_link_is_a_hit(tmp_path: Path) -> None:
    # what it shows (the loader was read through the swapped folder and passed)
    repo = _tracked_repo(tmp_path / "r", {"src/pkg/loader.py": f"x = '{FOLDER}'\n"})
    cfg = _cfg(loaders=("src/pkg/loader.py",))
    assert g.scan(repo, cfg) == [], "the control repository is not clean"
    _swap_parent_for_link(repo, "src/pkg", tmp_path)
    hits = g.scan(repo, cfg)
    assert any(h.startswith("src/pkg/loader.py: symlink-loader-entry") for h in hits), (
        f"a loader behind a link was read through it: {hits}"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: an exempt file behind a link was read through it: ['src/pkg: symlink-in-product-root', 'src/pkg/__init__.py: symlink-in-
def test_an_exempt_file_behind_a_folder_that_became_a_link_is_a_hit(tmp_path: Path) -> None:
    # what it shows (the exempt file was read through the swapped folder)
    repo = _tracked_repo(tmp_path / "r", {"src/pkg/self.py": "x = 1\n"})
    cfg = _cfg(exempt_files=("src/pkg/self.py",))
    assert g.scan(repo, cfg) == [], "the control repository is not clean"
    _swap_parent_for_link(repo, "src/pkg", tmp_path)
    hits = g.scan(repo, cfg)
    assert any(h.startswith("src/pkg/self.py: symlink-exempt-file") for h in hits), (
        f"an exempt file behind a link was read through it: {hits}"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: the marker behind a link was read through it: []
def test_the_copy_run_marker_behind_a_folder_that_became_a_link_is_a_hit(tmp_path: Path) -> None:
    # what it shows (the marker was read through the swapped folder and counted as a regular file)
    repo = _tracked_repo(tmp_path / "r")
    assert g.scan(repo, _cfg()) == [], "the control repository is not clean"
    _swap_parent_for_link(repo, "tools", tmp_path)
    hits = g.scan(repo, _cfg())
    assert any("copy-run-marker-not-a-regular-file" in h for h in hits), (
        f"the marker behind a link was read through it: {hits}"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: a chain of 45 links was not named as a chain: ['docs/link40: symlink-loop (a loop of links cannot be followed)', 'docs/l
def test_a_chain_of_45_links_is_a_hit_and_the_rule_text_names_both_causes(
    tmp_path: Path,
) -> None:
    # Wording only: the system gives the same error (ELOOP) for a loop and for a chain that is too
    # long, so the rule text names both causes; this test does not tell the two apart. It fails on
    # dd827d79 because the text there named only a loop.
    repo = _tracked_repo(tmp_path / "r", {"docs/end.txt": "x\n"})
    previous = "end.txt"
    for i in range(45):
        name = f"link{i:02d}"
        os.symlink(previous, repo / "docs" / name)
        previous = name
    _track(repo)
    hits = g.scan(repo, _cfg())
    assert any(h.startswith("docs/link44: symlink-loop") and "chain too long" in h for h in hits), (
        f"a chain of 45 links was not named as a chain: {hits}"
    )


# fail-before (real run on dd827d79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix. The helper file and the new tests were copied into the old tree.
# fail-before (real run on c7eb5c79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix. The helper file and the new tests were copied into the old tree.
def test_pin_the_shared_start_of_a_program_refuses_a_shell_a_hook_and_any_keyword_it_does_not_list() -> (
    None
):
    # Under a broken helper some of these cases would really start a program (`shell=True` runs `sh
    # -c <python> -c pass`, which is a bare interpreter reading its input). So no case may wait: the
    # input is empty and ends at once, and a time limit stops anything else.
    started = time.monotonic()
    for kwargs in (
        {"shell": True},
        {"shell": 1},
        {"executable": "/bin/sh"},
        {"preexec_fn": print},
        {"stdin": None},
    ):
        try:
            fixed_run.run_fixed(
                [sys.executable, "-c", "pass"],
                check=True,
                timeout=20,
                input=None if "stdin" in kwargs else "",
                text=True,
                **kwargs,
            )
        except subprocess.TimeoutExpired:
            raise AssertionError(f"a program was started with {kwargs} and ran on") from None
        except ValueError as refusal:
            assert next(iter(kwargs)) in str(refusal), (
                f"the refused keyword is not named: {refusal}"
            )
            continue
        raise AssertionError(f"a program was started with {kwargs}")
    assert not ({"shell", "executable", "preexec_fn", "stdin"} & fixed_run.ALLOWED_KEYWORDS), (
        "a risky keyword is allowed"
    )
    assert time.monotonic() - started < 60, (
        "the refusals took more than a minute: a case ran a program"
    )


# fail-before (real run on dd827d79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix. The helper file and the new tests were copied into the old tree.
# fail-before (real run on c7eb5c79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix. The helper file and the new tests were copied into the old tree.
def test_pin_the_shared_start_of_a_program_refuses_a_string_an_empty_list_and_elements_that_are_not_text() -> (
    None
):

    for bad in (
        "echo hello",
        b"echo hello",
        [],
        (),
        None,
        [sys.executable, 7],
        [sys.executable, None],
    ):
        try:
            fixed_run.run_fixed(bad, check=True)
        except TypeError:
            continue
        raise AssertionError(f"a command that is not a list of texts was run: {bad!r}")
    for bad in ([sys.executable, "-c", "pass\0x"], ["git\0", "status"]):
        try:
            fixed_run.run_fixed(bad, check=True)
        except TypeError:
            continue
        raise AssertionError(f"a text with a NUL character was run: {bad!r}")


# fail-before (real run on dd827d79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix. The helper file and the new tests were copied into the old tree.
# fail-before (real run on c7eb5c79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix. The helper file and the new tests were copied into the old tree.
def test_pin_the_shared_start_of_a_program_names_a_missing_program_and_runs_a_found_one() -> None:

    done = fixed_run.run_fixed([sys.executable, "-c", "print(7)"], check=True, capture_output=True)
    assert done.stdout.strip() == b"7", f"the program did not run: {done.stdout!r}"
    missing = "no-such-program-" + "x" * 8
    try:
        fixed_run.run_fixed([missing], check=True)
    except SystemExit as stop:
        assert missing in str(stop), f"the missing program is not named: {stop}"
    else:
        raise AssertionError("a missing program did not stop the caller")


def _calls_of(path: Path, names: set[str]) -> list[Any]:
    import ast

    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call):
            f = node.func
            called = (
                f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
            )
            if called in names:
                out.append(node)
    return out


# fail-before (real run on dd827d79, batch 14): it FAILS there, first failing line: AssertionError: demo_only_guard.py line 362: a program is started without the helper
# fail-before (real run on c7eb5c79, batch 14): it FAILS there, first failing line: AssertionError: demo_only_guard.py line 400: a program is started without the helper
def test_the_guard_and_the_repo_scan_start_programs_only_through_the_one_helper() -> None:
    import ast

    for name in ("demo_only_guard.py", "scan_repo.py"):
        tree = ast.parse((ROOT / "tools" / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                owner = node.func.value
                assert not (isinstance(owner, ast.Name) and owner.id == "subprocess"), (
                    f"{name} line {node.lineno}: a program is started without the helper"
                )
        calls = _calls_of(ROOT / "tools" / name, {"run_fixed"})
        assert calls, f"{name} no longer uses the helper"
        for call in calls:
            risky = {k.arg for k in call.keywords} & {"shell", "executable", "preexec_fn"}
            assert not risky, f"{name} line {call.lineno}: passes {sorted(risky)}"


# -- batch 15: the limits of the line masker, the empty file list, the one program starter
# ---------------------------
# fail-before: the rows below are real runs on dd827d79 and c7eb5c79 in the table "fail-before runs" of batch 15 (see the
# CHANGELOG); a test that needs the guard code of this branch cannot say more than that there.
def test_a_dashed_scheme_token_of_16_characters_is_hidden() -> None:
    assert g._hide_secrets("x Basic abc-defghijklmno y") == "x Basic <hidden> y", (
        "a 16 character Basic token with a dash stayed visible"
    )


def test_pin_a_dashed_scheme_token_of_15_characters_stays_visible_as_in_the_core() -> None:
    line = "x Basic abc-defghijklmn y"
    assert g._hide_secrets(line) == line, "a 15 character Basic token with a dash was hidden"


def test_pin_a_dashed_scheme_token_of_13_characters_stays_visible_as_in_the_core() -> None:
    line = "x Basic abc-defghijkl y"
    assert g._hide_secrets(line) == line, "a 13 character Basic token with a dash was hidden"


def test_the_end_of_a_value_with_a_quote_that_never_closes_is_the_end_of_the_line() -> None:
    for text in ('a="abc', 'a="ab\\'):
        assert g._value_end(text, 2) == len(text), (
            f"the end of an open quote is not the end of {text!r}"
        )


def test_the_end_of_a_value_with_a_quote_that_closes_is_after_the_closing_quote() -> None:
    assert g._value_end('a="x" y', 2) == 5, "the closing quote is not part of the quoted value"


def test_a_token_that_an_earlier_pass_already_hid_is_not_hidden_twice_into_the_scheme_word() -> (
    None
):
    shown = g._hide_secrets("authorization=Bearer abcdefghijklmn x")
    assert shown == "authorization=<hidden> <hidden> x", (
        f"an already hidden token was handled: {shown!r}"
    )


def test_an_authorization_scheme_word_with_nothing_after_it_keeps_the_white_space_after_it() -> (
    None
):
    shown = g._hide_secrets("authorization=Bearer   \nnext")
    assert shown == "authorization=<hidden>   \nnext", (
        f"white space after a bare scheme word: {shown!r}"
    )


def test_an_authorization_digest_with_several_parts_is_hidden_to_the_end_of_its_line() -> None:
    shown = g._hide_secrets('authorization=Digest username="a", response="b" tail')
    assert shown == "authorization=<hidden>", f"a part of a Digest value stayed visible: {shown!r}"


def test_an_authorization_digest_does_not_hide_the_next_line() -> None:
    shown = g._hide_secrets('authorization=Digest username="a", response="b"\nnext line=1')
    assert shown == "authorization=<hidden>\nnext line=1", (
        f"the Digest hid the next line: {shown!r}"
    )


def _stop_text(call: Any) -> str | None:
    """The text of the stop (`SystemExit`) that `call()` ends in, or None when it does not stop. The
    caller asserts after this returns, so a failed assert is not chained to the stop it was reading.
    """
    try:
        call()
    except SystemExit as stop:
        return str(stop)
    return None


def test_an_empty_repository_is_refused_with_the_message_for_an_empty_list(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {})
    said = _stop_text(lambda: g.tracked_paths(repo))
    assert said is not None, "an empty file list of an empty repository was not refused"
    assert "git listed no files" in said, f"the empty list message is not given: {said}"


def test_a_repository_with_only_files_not_added_is_refused_by_the_tracked_list_and_says_so(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, {"src/pkg/a.py": "A = 1\n"})
    assert g.tracked_paths(repo) == ["src/pkg/a.py"], (
        "the new file is not in the list with new files"
    )
    said = _stop_text(lambda: g.tracked_paths(repo, include_new=False))
    assert said is not None, "an empty tracked list was not refused"
    assert "git add the files" in said, f"the message does not say what to do: {said}"


def test_the_copy_run_of_a_repository_with_only_files_not_added_says_which_and_stops(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repo(tmp_path, {"src/pkg/a.py": "A = 1\n"})
    said = _stop_text(lambda: g.run_without_folder(repo, _cfg(), ["tests"]))
    printed = capsys.readouterr().out
    assert said is not None, "the copy run on a repository with no tracked file was not refused"
    assert "1 file(s) are not added to git" in printed, f"the new file is not named: {printed!r}"
    assert "git tracks no files" in said, f"the stop does not say why: {said}"


# -- the one program starter: what each check of it refuses or accepts
# ---------------------------------------------------
def _outcome(argv: Any, **kwargs: Any) -> str:
    """What `run_fixed` does with `argv`: the name of what it raised, or "ran". No case waits: empty
    input and a limit."""
    if "stdin" not in kwargs:
        kwargs.setdefault("input", "")
    try:
        fixed_run.run_fixed(argv, check=True, timeout=20, text=True, **kwargs)
    except (
        TypeError,
        ValueError,
        LookupError,
        SystemExit,
        OSError,
        subprocess.SubprocessError,
    ) as error:
        return type(error).__name__
    return "ran"


def test_pin_a_string_as_the_command_is_refused() -> None:
    got = _outcome("echo hello")
    assert got == "TypeError", f"a string as the command was not refused: {got}"


def test_pin_an_empty_command_is_refused() -> None:
    got = [_outcome([]), _outcome(())]
    assert got == ["TypeError", "TypeError"], f"an empty command was not refused: {got}"


def test_pin_a_text_with_a_nul_character_is_refused() -> None:
    got = _outcome([sys.executable, "-c", "pass\0x"])
    assert got == "TypeError", f"a NUL character in an argument was not refused: {got}"


def test_pin_an_element_that_is_not_text_or_a_path_is_refused() -> None:
    got = {repr(e): _outcome([sys.executable, e]) for e in (7, None, b"x")}
    assert set(got.values()) == {"TypeError"}, f"an element that is not text was not refused: {got}"


def test_pin_a_tuple_and_a_path_element_are_accepted() -> None:
    assert _outcome((sys.executable, "-c", "pass")) == "ran", "a tuple was refused"
    assert _outcome([Path(sys.executable), "-c", "pass"]) == "ran", "a path element was refused"


def test_pin_a_dict_a_set_a_generator_and_a_path_as_the_whole_command_are_refused() -> None:
    cases = {
        "dict": {sys.executable: 1},
        "set": {sys.executable},
        "generator": (a for a in [sys.executable]),
        "path": Path(sys.executable),
    }
    got = {name: _outcome(value) for name, value in cases.items()}
    assert set(got.values()) == {"TypeError"}, f"a whole command that is not a list was run: {got}"


def test_pin_a_program_that_is_found_on_the_path_runs_and_one_that_is_not_stops_the_caller() -> (
    None
):
    assert _outcome(["git", "--version"]) == "ran", "a program on the PATH was not started"
    missing = _outcome(["no-such-program-" + "x" * 8])
    assert missing == "SystemExit", (
        f"a program that is not found did not stop the caller: {missing}"
    )


def test_pin_a_missing_program_is_not_handed_on_as_no_program() -> None:
    got = _outcome(["no-such-program-" + "x" * 8])
    assert got != "TypeError", "a missing program was handed on as no program"


def test_pin_each_keyword_of_the_list_is_accepted_and_every_other_one_is_refused(
    tmp_path: Path,
) -> None:
    ok = {
        "cwd": str(tmp_path),
        "env": dict(os.environ),
        "capture_output": True,
        "encoding": "utf-8",
    }
    for name, value in ok.items():
        got = _outcome([sys.executable, "-c", "pass"], **{name: value})
        assert got == "ran", f"the allowed keyword {name} was refused: {got}"
    risky = {
        "shell": True,
        "executable": "/bin/sh",
        "preexec_fn": print,
        "stdin": None,
        "stdout": None,
        "close_fds": False,
        "start_new_session": True,
    }
    for name, value in risky.items():
        got = _outcome([sys.executable, "-c", "pass"], **{name: value})
        assert got == "ValueError", f"{name} was not refused: {got}"


# -- the marker count and the sweep of every program start
# --------------------------------------------------------------
def _comment_markers(path: Path) -> list[tuple[int, str]]:
    import io
    import tokenize

    pattern = re.compile(r"noqa|nosec|type:\s*ignore|fmt:\s*(?:skip|off)|pragma:\s*no\s*cover")
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(path.read_text(encoding="utf-8")).readline):
        if tok.type == tokenize.COMMENT and pattern.search(tok.string):
            out.append((tok.start[0], tok.string))
    return out


def test_the_guard_and_the_helper_files_hold_exactly_one_marker_and_it_is_on_the_line_that_starts_the_program() -> (
    None
):
    files = (
        "tools/demo_only_guard.py",
        "tools/fixed_run.py",
        "tools/scan_repo.py",
        "tests/fixed_run.py",
    )
    found = {f: _comment_markers(ROOT / f) for f in files}
    total = [(f, m) for f, ms in found.items() for m in ms]
    assert len(total) == 1, f"the markers are not exactly one: {total}"
    ((name, (lineno, text)),) = total
    assert name == "tools/fixed_run.py" and "S603" in text, (
        f"the marker is not the S603 one: {total}"
    )
    line = (ROOT / name).read_text(encoding="utf-8").splitlines()[lineno - 1]
    assert "subprocess.run(" in line, (
        f"the marker is not on the line that starts the program: {line!r}"
    )


_STARTING_CALLS = {
    "run",
    "Popen",
    "call",
    "check_call",
    "check_output",
    "getoutput",
    "getstatusoutput",
}


def _program_starts(source: str) -> list[tuple[int, str]]:
    """Where a source starts a program by itself: an attribute call on the `subprocess` or `os` module
    under any alias, and any `from subprocess import ...` or `from os import
    system/popen/exec*/spawn*`."""
    import ast

    tree = ast.parse(source)
    modules: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in ("subprocess", "os"):
                    modules[a.asname or a.name] = a.name
    os_names = ("system", "popen", "fork", "forkpty")
    os_prefixes = ("exec", "spawn", "posix_spawn")
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in ("subprocess", "os"):
            for a in node.names:
                if (
                    node.module == "subprocess"
                    or a.name in os_names
                    or a.name.startswith(os_prefixes)
                ):
                    out.append((node.lineno, f"from {node.module} import {a.name}"))
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            owner, attr = modules.get(node.func.value.id), node.func.attr
            if owner == "subprocess" and attr in _STARTING_CALLS:
                out.append((node.lineno, f"subprocess.{attr}"))
            if owner == "os" and (attr in os_names or attr.startswith(os_prefixes)):
                out.append((node.lineno, f"os.{attr}"))
    return sorted(out)


# The ONE allowed place is the helper. The files below start programs by themselves TODAY. They are
# listed with their number of starts so that no new one slips in and so that a fixed file must leave
# the list; each is a follow-up item (a later batch moves it to the helper), not an allowed way.
THE_HELPER = {"tools/fixed_run.py": 1}
FOLLOW_UP_DIRECT_STARTS = {
    "tests/demo_askdata/conftest.py": 1,
    "tests/demo_askdata/test_meter.py": 1,
    "tests/test_ci_gitleaks_scope.py": 4,
    "tests/test_k5_classes.py": 1,
    "tests/test_mutation_runner.py": 6,
    "tests/test_mutation_runner_helpers.py": 2,
    "tests/test_mutation_runner_meta.py": 1,
    "tests/test_scan_repo.py": 3,
    "tools/mutation_runner.py": 2,
}


def test_every_start_of_a_program_in_tools_tests_and_src_is_the_helper_or_a_listed_follow_up() -> (
    None
):
    found: dict[str, int] = {}
    for top in ("tools", "tests", "src"):
        for path in sorted((ROOT / top).rglob("*.py")):
            starts = _program_starts(path.read_text(encoding="utf-8"))
            if starts:
                found[path.relative_to(ROOT).as_posix()] = len(starts)
    assert found == {**THE_HELPER, **FOLLOW_UP_DIRECT_STARTS}, (
        "the files that start a program by themselves are not the listed ones: "
        f"{sorted(set(found.items()) ^ set({**THE_HELPER, **FOLLOW_UP_DIRECT_STARTS}.items()))}"
    )


def test_the_sweep_finds_an_alias_a_from_import_and_the_os_calls() -> None:
    source = (
        "import subprocess as sp\nimport os as o\nfrom subprocess import run\nfrom os import system\n"
        "sp.run(['x'])\nsp.Popen(['x'])\no.system('x')\no.execvp('x', [])\no.spawnl(0, 'x')\no.popen('x')\nsp.DEVNULL\n"
    )
    names = [what for _, what in _program_starts(source)]
    assert names == [
        "from subprocess import run",
        "from os import system",
        "subprocess.run",
        "subprocess.Popen",
        "os.system",
        "os.execvp",
        "os.spawnl",
        "os.popen",
    ], f"the sweep missed or added a start: {names}"


def _loader_body(name: str) -> str:
    import ast

    tree = ast.parse((ROOT / "tools" / name).read_text(encoding="utf-8"))
    (fn,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_load_fixed_run"]
    return ast.dump(
        ast.Module(body=fn.body[1:], type_ignores=[])
    )  # the body, without its docstring


# The two files cannot share this function: each must load the program starter before it can import anything, and the
# scan rule forbids a product file that names the demo-only folder (the guard does), so the scan cannot import the guard.
def test_the_two_loaders_of_the_program_starter_are_the_same() -> None:
    guard, scan = _loader_body("demo_only_guard.py"), _loader_body("scan_repo.py")
    assert guard == scan, "the two copies of _load_fixed_run have drifted apart"


def test_a_changed_loader_is_not_the_same_as_the_other_one(tmp_path: Path) -> None:
    src = (ROOT / "tools" / "scan_repo.py").read_text(encoding="utf-8")
    changed = src.replace("spec.loader is None", "spec.loader is not None", 1)
    assert changed != src, "the planted change did not apply"
    (tmp_path / "scan_repo.py").write_text(changed, encoding="utf-8")
    import ast

    tree = ast.parse(changed)
    (fn,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_load_fixed_run"]
    assert ast.dump(ast.Module(body=fn.body[1:], type_ignores=[])) != _loader_body(
        "demo_only_guard.py"
    ), "a changed copy still compares equal"
