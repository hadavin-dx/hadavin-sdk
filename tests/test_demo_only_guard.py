"""The demo-only folder guard (tools/demo_only_guard.py): product code must not name the folder that holds everything
that exists only for demos, nor a made-up record id; the build must still pass with the folder deleted. Made-up data only.

Rows: the real repo is clean and the scan is not vacuous; each way to depend on the folder is a hit that names the file
and line but never prints the matched text (symlinks, every file type, every product folder, any depth, any spelling of
the name, loader files, the copy-run marker); the settings are checked (a bad setting stops the guard); a missing folder
stops a run that requires it; pytest in a copy without the folder passes for a clean product and fails for one that
reaches into the folder, and the copy imports its own code, never the original checkout.
(That CI runs the scan is checked in tests/test_demo_only_guard_ci.py.)
"""

from __future__ import annotations

import random
import re
import subprocess
import sys
from pathlib import Path

import pytest
from tools import demo_only_guard as g

ROOT = Path(__file__).resolve().parents[1]
FOLDER = "demo_only"
FAKE_ID = "FAKE-REC-[0-9]{4}"


def _cfg(**over: object) -> g.GuardConfig:
    base = {
        "folder": FOLDER,
        "product_roots": ("src",),
        "loaders": (),
        "fake_id_patterns": (re.compile(FAKE_ID),),
        "product_packages": ("pkg",),
    }
    base.update(over)
    return g.GuardConfig(**base)  # type: ignore[arg-type]


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    """A made-up repository. It is a git repository (the guard lists files with git) with nothing added or committed:
    files that are not ignored count, as in a fresh checkout that has not run `git add` yet."""
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    if not (tmp_path / ".git").exists():
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
    return tmp_path


# the mutation runner copies the sources without .git: the two tests on this very repository then have nothing to scan
needs_git = pytest.mark.skipif(not (ROOT / ".git").exists(), reason="this copy has no .git")


MARKER = "tools/demo_only_guard.copy_run"
CLEAN = {
    "src/pkg/__init__.py": "X = 1\n",
    f"{FOLDER}/data.json": '{"id": "FAKE-REC-0001"}\n',
    MARKER: "",  # a repository that has the folder says its CI runs the copy run
}


# -- the real repository ---------------------------------------------------------------------------------------------
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


# -- every way to depend on the folder --------------------------------------------------------------------------------
def test_a_clean_product_passes_even_though_the_folder_holds_fake_ids(tmp_path: Path) -> None:
    assert g.scan(_repo(tmp_path, CLEAN), _cfg()) == []


def test_product_code_that_names_the_folder_is_a_hit_with_file_and_line_only(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/a.py": f"x = 1\nimport {FOLDER}.fakes\n"})
    assert g.scan(repo, _cfg()) == ["src/pkg/a.py:2: names-demo-only-folder"]


def test_a_fake_record_id_in_product_code_is_a_hit_and_the_id_is_not_printed(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/b.py": 'ID = "FAKE-REC-0042"\n'})
    hits = g.scan(repo, _cfg())
    assert hits == ["src/pkg/b.py:1: fake-record-id"] and "0042" not in "".join(hits)


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
    assert len(hits) == 1 and "stale-allowed-phrase" in hits[0]


def test_the_folder_inside_a_product_root_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/pkg/__init__.py": "", f"src/{FOLDER}/x.py": "A = 1\n"})
    assert any("folder-inside-product-root" in h for h in g.scan(repo, _cfg()))


def test_a_missing_product_root_is_a_hit_not_a_silent_pass(tmp_path: Path) -> None:
    hits = g.scan(_repo(tmp_path, {f"{FOLDER}/a.json": "{}", MARKER: ""}), _cfg())
    assert hits == ["src: product-root-missing (a missing root would make the scan prove nothing)"]


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
    assert g.scan(one, _cfg(loaders=loader)) == []
    two = _repo(
        tmp_path / "two", {**CLEAN, "src/pkg/loader.py": f"A = '{FOLDER}'\nB = '{FOLDER}'\n"}
    )
    assert g.scan(two, _cfg(loaders=loader)) == [
        "src/pkg/loader.py:2: loader-names-folder-too-often"
    ]
    assert g.scan(two, _cfg(loaders=loader, loader_max_lines=2)) == []
    fake = _repo(
        tmp_path / "fk", {**CLEAN, "src/pkg/loader.py": f"A = '{FOLDER}'\nID = 'FAKE-REC-0001'\n"}
    )
    assert g.scan(fake, _cfg(loaders=loader)) == ["src/pkg/loader.py:2: fake-record-id"]


def test_a_stale_loader_entry_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/pkg/loader.py": "NAME = 'x'\n"})
    hits = g.scan(repo, _cfg(loaders=("src/pkg/loader.py", "src/pkg/gone.py")))
    assert sorted(hits) == [
        "src/pkg/gone.py: stale-loader-entry (file does not exist)",
        "src/pkg/loader.py: stale-loader-entry (file does not name the folder)",
    ]


def test_ignored_files_and_binary_endings_are_skipped(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path, {**CLEAN, "src/pkg/__pycache__/x.py": FOLDER, ".gitignore": "__pycache__/\n"}
    )
    (repo / "src/pkg/logo.png").write_bytes(b"\xff\xfe" + FOLDER.encode())
    (repo / "src/pkg/LOGO.PNG").write_bytes(b"\xff\xfe" + FOLDER.encode())
    assert g.scan(repo, _cfg()) == []


def test_every_file_type_is_read_not_only_a_list_of_endings(tmp_path: Path) -> None:
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
        assert g.scan(repo, _cfg()) == [f"src/pkg/{name}:2: names-demo-only-folder"], name


def test_a_file_that_is_not_text_and_not_a_known_binary_ending_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path, CLEAN)
    (repo / "src/pkg/blob.dat").write_bytes(b"\xff\xfe\x00" + FOLDER.encode())
    (repo / "src/pkg/noending").write_bytes(b"\xc3\x28")
    assert sorted(h.split(" (")[0] for h in g.scan(repo, _cfg())) == [
        "src/pkg/blob.dat: unreadable-file",
        "src/pkg/noending: unreadable-file",
    ]


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
    assert cfg.product_roots == ("src", "templates", "tools", "demos")
    assert cfg.skip_suffixes == g.DEFAULT_SKIP_SUFFIXES
    assert not any(
        s in cfg.skip_suffixes for s in (".py", ".js", ".toml", ".md", ".txt", ".sh", ".cfg")
    )


# -- symlinks, spellings, depth ---------------------------------------------------------------------------------------
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
    )
    for name in ("to_file.py", "to_dir", "to_out.py", "dangling.py"):
        one = _repo(tmp_path / f"one-{name}", CLEAN)
        link = one / "src/pkg" / name
        link.symlink_to(
            one / FOLDER if name == "to_dir" else one / "gone.py",
            target_is_directory=name == "to_dir",
        )
        assert _main(one, _toml(tmp_path)) == 1


def test_a_product_root_that_is_itself_a_symlink_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "r", {"real/a.py": "A = 1\n"})
    (repo / "src").symlink_to(repo / "real", target_is_directory=True)
    assert g.scan(repo, _cfg()) == ["src: symlink-in-product-root"]


def test_the_folder_inside_a_product_root_is_a_hit_at_any_depth_and_in_any_spelling(
    tmp_path: Path,
) -> None:
    for i, name in enumerate(["Demo_Only", "demo-only", "demo only", "DEMO_ONLY", "demo_only"]):
        repo = _repo(
            tmp_path / f"r{i}", {"src/pkg/__init__.py": "", f"src/pkg/sub/{name}/x.py": "A = 1\n"}
        )
        assert g.scan(repo, _cfg()) == [f"src/pkg/sub/{name}: folder-inside-product-root"], name


def test_a_file_or_folder_name_that_holds_the_folder_name_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/pkg/x_demo_only.py": "", "src/pkg/my-demo_only-data/k.txt": ""})
    assert sorted(g.scan(repo, _cfg())) == [
        "src/pkg/my-demo_only-data: path-names-demo-only-folder",
        "src/pkg/x_demo_only.py: path-names-demo-only-folder",
    ]


def test_a_line_that_names_the_folder_in_another_spelling_is_a_hit(tmp_path: Path) -> None:
    for i, spelling in enumerate(
        ["Demo_Only", "demo-only", "demo only", "DEMO-ONLY", "Demo  Only", "demo_-only"]
    ):
        repo = _repo(
            tmp_path / f"r{i}", {**CLEAN, "src/pkg/a.py": f"x = 1\nPATH = '{spelling}/fakes'\n"}
        )
        assert g.scan(repo, _cfg()) == ["src/pkg/a.py:2: names-demo-only-folder"], spelling


# -- the guard's own files, and the copy-run marker ---------------------------------------------------------------------
def test_the_exempt_files_are_exactly_the_guard_itself_and_each_is_skipped_whole(
    tmp_path: Path,
) -> None:
    cfg = g.load_config(ROOT / "tools" / "demo_only_guard.toml")
    assert cfg.exempt_files == ("tools/demo_only_guard.py", "tools/demo_only_guard.toml")
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/self.py": f"# {FOLDER}\n"})
    assert g.scan(repo, _cfg(exempt_files=("src/pkg/self.py",))) == []
    assert g.scan(repo, _cfg()) == ["src/pkg/self.py:1: names-demo-only-folder"]
    assert g.scan(repo, _cfg(exempt_files=("src/pkg/gone.py",)))[0].startswith(
        "src/pkg/gone.py: stale-exempt-entry"
    )


def test_a_repository_that_has_the_folder_needs_the_copy_run_marker(tmp_path: Path) -> None:
    without = {k: v for k, v in CLEAN.items() if k != MARKER}
    repo = _repo(tmp_path / "a", without)
    assert [h.split(" (")[0] for h in g.scan(repo, _cfg())] == [f"{MARKER}: copy-run-not-wired"]
    assert _main(repo, _toml(tmp_path)) == 1
    assert g.scan(_repo(tmp_path / "b", CLEAN), _cfg()) == []
    no_folder = _repo(
        tmp_path / "c", {"src/pkg/__init__.py": ""}
    )  # no folder, no marker needed (core)
    assert g.scan(no_folder, _cfg()) == []


def test_the_copy_run_if_present_does_nothing_without_a_folder_and_runs_with_one(
    tmp_path: Path,
) -> None:
    cfg = _toml(tmp_path, product_packages='["pkg"]')
    none = _repo(tmp_path / "none", {"src/pkg/__init__.py": ""})
    assert _main(none, cfg, "--without-folder-if-present") == 0
    repo = _mini(tmp_path / "r")
    assert _main(repo, cfg, "--without-folder-if-present", "--", "tests/test_plain.py") == 0
    (repo / "tests" / "test_needs.py").write_text(NEEDS_FOLDER_TEST, encoding="utf-8")
    assert _main(repo, cfg, "--without-folder-if-present", "--", "tests/test_needs.py") != 0


def test_property_a_hit_is_reported_exactly_where_it_was_planted(tmp_path: Path) -> None:
    rng = random.Random(20261112)  # noqa: S311 - a seeded test generator, not a secret
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


# -- the settings are checked -----------------------------------------------------------------------------------------
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
        with pytest.raises(SystemExit, match="'folder'"):
            g.load_config(_toml(tmp_path, folder=f'"{name}"'))


def test_a_pattern_that_matches_the_empty_text_stops_the_guard(tmp_path: Path) -> None:
    for pattern in ("x*", "", "(a|)"):
        with pytest.raises(SystemExit, match="matches the empty text"):
            g.load_config(_toml(tmp_path, fake_id_patterns=f'["{pattern}"]'))


# -- the command line ------------------------------------------------------------------------------------------------
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
    assert _main(no_folder, cfg, "--require") == 2
    assert "is missing but is required" in capsys.readouterr().out
    dirty = _repo(tmp_path / "dirty", {**CLEAN, "src/pkg/a.py": f"# {FOLDER}\n"})
    assert (
        _main(dirty, cfg) == 1
        and "src/pkg/a.py:1: names-demo-only-folder" in capsys.readouterr().out
    )


@needs_git
def test_the_script_runs_as_a_program_on_this_repository() -> None:
    done = subprocess.run(  # noqa: S603 (our own interpreter and script)
        [sys.executable, str(ROOT / "tools" / "demo_only_guard.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0 and done.stdout == "", done.stdout + done.stderr


# -- the build without the folder -------------------------------------------------------------------------------------
PRODUCT = "def answer():\n    return 42\n"
PLAIN_TEST = "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parents[1] / 'src'))\nfrom pkg import answer\n\n\ndef test_it():\n    assert answer() == 42\n"
NEEDS_FOLDER_TEST = "def test_needs_folder():\n    import demo_only.fakes  # noqa: F401\n"


def _mini(tmp_path: Path, product: str = PRODUCT) -> Path:
    return _repo(
        tmp_path,
        {
            "src/pkg/__init__.py": product,
            "tests/test_plain.py": PLAIN_TEST,
            f"{FOLDER}/__init__.py": "",
            f"{FOLDER}/fakes.py": "RECORD = 'x'\n",
        },
    )


def test_the_copy_has_no_folder_and_nothing_else_is_lost(tmp_path: Path) -> None:
    repo = _mini(tmp_path / "r")
    dest = tmp_path / "copy"
    g.copy_without_folder(repo, _cfg(), dest)
    assert not (dest / FOLDER).exists() and (dest / "src" / "pkg" / "__init__.py").is_file()
    assert (dest / "tests" / "test_plain.py").is_file() and not (dest / ".git").exists()
    assert (repo / FOLDER / "fakes.py").is_file()  # the original is untouched


def test_a_clean_product_passes_in_a_copy_without_the_folder(tmp_path: Path) -> None:
    assert g.run_without_folder(_mini(tmp_path / "r"), _cfg(), []) == 0


def test_a_product_that_reaches_into_the_folder_fails_in_the_copy(tmp_path: Path) -> None:
    repo = _mini(tmp_path / "r", PRODUCT + f"import {FOLDER}.fakes\n")
    assert g.run_without_folder(repo, _cfg(), []) != 0


def test_the_copy_run_really_has_no_folder(tmp_path: Path) -> None:
    repo = _mini(tmp_path / "r")
    (repo / "tests" / "test_needs.py").write_text(NEEDS_FOLDER_TEST, encoding="utf-8")
    assert (
        g.run_without_folder(repo, _cfg(), ["tests/test_needs.py"]) != 0
    )  # proves the folder is gone from the copy
    assert g.run_without_folder(repo, _cfg(), ["tests/test_plain.py"]) == 0


# -- one list of files: git's ---------------------------------------------------------------------------------------
def test_the_scan_refuses_a_folder_that_is_not_a_git_checkout(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    with pytest.raises(SystemExit, match="not a git checkout"):
        g.scan(tmp_path, _cfg())


def test_a_file_is_scanned_whether_it_is_added_to_git_or_not(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path, {**CLEAN, "src/pkg/added.py": f"# {FOLDER}\n", "src/pkg/new.py": f"# {FOLDER}\n"}
    )
    subprocess.run(["git", "-C", str(repo), "add", "src/pkg/added.py"], check=True)  # noqa: S603, S607
    assert sorted(g.scan(repo, _cfg())) == [
        "src/pkg/added.py:1: names-demo-only-folder",
        "src/pkg/new.py:1: names-demo-only-folder",
    ]


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
    ]


# -- the copy run proves the copy, not the original -----------------------------------------------------------------
def test_the_copy_run_imports_the_copy_even_if_the_original_is_on_the_import_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _mini(tmp_path / "r")
    monkeypatch.setenv(
        "PYTHONPATH", str(repo / "src")
    )  # an inherited path to the ORIGINAL checkout
    assert g.run_without_folder(repo, _cfg(), []) == 0  # the child replaces it with the copy's src
    assert g.run_without_folder(repo, _cfg(product_packages=("pkg_missing",)), []) != 0


def test_the_copy_run_fails_when_the_package_comes_from_somewhere_else(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _mini(tmp_path / "r")
    # "json" is real and importable but is not in the copy: the check must refuse to call that a pass
    assert g.run_without_folder(repo, _cfg(product_packages=("json",)), []) == 3
    assert "not imported from the copy" in capsys.readouterr().out


def test_the_copy_run_without_a_package_to_check_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="product_packages"):
        g.run_without_folder(_mini(tmp_path / "r"), _cfg(product_packages=()), [])


# -- round 3 ---------------------------------------------------------------------------------------------------------
def test_a_listed_phrase_is_matched_in_its_own_case_and_not_beside_a_dash(tmp_path: Path) -> None:
    cfg = _cfg(allowed_phrases=("DEMO_ONLY",))
    for i, line in enumerate(["DEMO_ONLY-x", "x-DEMO_ONLY", "demo_only", "Demo_Only", "DEMO-ONLY"]):
        bad = _repo(tmp_path / f"p{i}", {**CLEAN, "src/pkg/c.py": f"V = DEMO_ONLY\nW = '{line}'\n"})
        assert g.scan(bad, cfg) == ["src/pkg/c.py:2: names-demo-only-folder"], line


def test_a_text_file_renamed_to_a_binary_ending_is_read_but_a_real_binary_is_skipped(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, {**CLEAN, "src/pkg/notes.png": f"see {FOLDER}\n"})
    assert g.scan(repo, _cfg()) == ["src/pkg/notes.png:1: names-demo-only-folder"]
    real = _repo(tmp_path / "real", CLEAN)
    (real / "src/pkg/logo.png").write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + FOLDER.encode()
    )
    assert g.scan(real, _cfg()) == []  # a NUL byte near the start: a real binary, skipped
    zeroes = _repo(
        tmp_path / "late", CLEAN
    )  # a NUL only after the first 8192 bytes does not make it binary
    (zeroes / "src/pkg/late.png").write_bytes(b"a" * 9000 + b"\x00" + FOLDER.encode())
    assert g.scan(zeroes, _cfg()) == ["src/pkg/late.png:1: names-demo-only-folder"]


def _gitlink(repo: Path, rel: str) -> None:
    """Add a git link (what a submodule is) at `rel`: the index holds mode 160000 and the path is a folder on disk."""
    (repo / rel).mkdir(parents=True)
    sha = "1" * 40
    subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), "update-index", "--add", "--cacheinfo", f"160000,{sha},{rel}"],  # noqa: S607
        check=True,
    )


def test_a_submodule_under_a_product_root_is_a_hit_and_one_outside_is_not(tmp_path: Path) -> None:
    repo = _repo(tmp_path, CLEAN)
    _gitlink(repo, "src/vendored")
    _gitlink(repo, "elsewhere/vendored")
    assert g.scan(repo, _cfg()) == [
        "src/vendored: submodule-in-product-root (its files cannot be scanned)"
    ]
