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

import os
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


def _track(repo: Path) -> Path:
    """Add every file that is not ignored to git's index: the copy run copies the files git tracks (and only those)."""
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)  # noqa: S603, S607
    return repo


# the mutation runner copies the sources without .git: the two tests on this very repository then have nothing to scan
needs_git = pytest.mark.skipif(not (ROOT / ".git").exists(), reason="this copy has no .git")


PNG = b"\x89PNG\r\n\x1a\n"  # the first bytes of every real picture of this kind
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
    assert g.scan(repo, _cfg()) == [], "ignored_files_and_binary_endings_are_skipped: check 1"


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
    ), "every_symlink_under_a_product_root_is_a_hit: check 1"
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
    ], "a_file_or_folder_name_that_holds_the_folder_name_is_a_hit: check 1"


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
    repo = _mini(tmp_path / "r", PRODUCT + f"import {FOLDER}.fakes\n")
    assert g.run_without_folder(repo, _cfg(), []) != 0


def test_the_copy_run_really_has_no_folder(tmp_path: Path) -> None:
    repo = _mini(tmp_path / "r")
    (repo / "tests" / "test_needs.py").write_text(NEEDS_FOLDER_TEST, encoding="utf-8")
    _track(repo)
    assert g.run_without_folder(repo, _cfg(), ["tests/test_needs.py"]) != 0, (
        "a test that needs the folder passed in the copy"
    )  # proves the folder is gone from the copy
    assert g.run_without_folder(repo, _cfg(), ["tests/test_plain.py"]) == 0


# -- one list of files: git's ---------------------------------------------------------------------------------------
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
    subprocess.run(["git", "-C", str(repo), "add", "src/pkg/added.py"], check=True)  # noqa: S603, S607
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


# -- the copy run proves the copy, not the original -----------------------------------------------------------------
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
    # "json" is real and importable but is not in the copy: the check must refuse to call that a pass
    assert g.run_without_folder(repo, _cfg(product_packages=("json",)), []) == 3, (
        "a package that does not come from the copy was accepted"
    )
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
    # a NUL byte near the start: a real binary, not read as text; its bytes are searched for the name instead
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
    ], "a_submodule_under_a_product_root_is_a_hit_and_one_outside_is: check 1"


# -- round 4 ---------------------------------------------------------------------------------------------------------
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
    assert g.scan(repo, _cfg(exempt_files=("src/vendored",))) == [], (
        "a_submodule_that_is_listed_as_exempt_is_not_a_second_hit: check 1"
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


# -- round 5: the guard fails closed everywhere -----------------------------------------------------------------------
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
    # a tracked file that was replaced by a pipe (git still lists it): a read would block, so it is a hit, never opened
    (repo / "src/pkg/pipe.py").write_text("X = 1\n", encoding="utf-8")
    (repo / "elsewhere/pipe.py").write_text("X = 1\n", encoding="utf-8")
    subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), "add", "src/pkg/pipe.py", "elsewhere/pipe.py"],  # noqa: S607
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
}


def test_a_compiled_or_packed_file_is_refused_by_its_first_bytes_whatever_its_ending(
    tmp_path: Path,
) -> None:
    variants = [(k, v) for k, v in MAGIC.items()]
    variants += [
        ("zip", b"PK\x05\x06" + b"\x00" * 20),
        ("zip", b"PK\x07\x08" + b"\x00" * 20),
    ]  # empty, spanned
    for low_or_high in (
        3000,
        3999,
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
            ], (kind, raw[:4].hex(), ending)
    for number in (2999, 4000):  # just outside the range: not read as compiled Python
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
    )
    assert g.scan(repo, _cfg(max_file_bytes=1000)) == ["src/pkg/big.py:1: names-demo-only-folder"]
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
    real_stat = Path.stat

    def small_stat(self: Path, *args: object, **kwargs: object):
        got = real_stat(self, *args, **kwargs)
        if self.name != "big.py" or kwargs.get("follow_symlinks") is False:
            return got
        fields = {k: getattr(got, k) for k in dir(got) if k.startswith("st_")}
        fields["st_size"] = 5
        return type("FakeStat", (), fields)()

    monkeypatch.setattr(Path, "stat", small_stat)
    assert g.scan(repo, _cfg(max_file_bytes=100)) == [
        "src/pkg/big.py: file-too-large (over 100 bytes; it is not read)"
    ]


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
    assert f"{wide}: folder-inside-product-root (it would be packaged with the product)" in hits


# -- batch 6, class B: the content decides, an entry that cannot be inspected is a hit, special files keep their shape ---
REAL_SAMPLES = {  # the first bytes of a real file of each kind the settings allow without reading it as text
    ".png": PNG + b"\x00\x00",
    ".jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00",
    ".jpeg": b"\xff\xd8\xff\xdb\x00",
    ".gif": b"GIF89a\x01\x00\x01\x00\x00",
    ".ico": b"\x00\x00\x01\x00\x01\x00",
    ".pdf": b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n",
    ".woff": b"wOFF\x00\x01\x00\x00",
    ".woff2": b"wOF2\x00\x01\x00\x00",
}
FOREIGN_HEADERS = {  # real file marks of kinds the guard has no special rule for
    "zstd": b"\x28\xb5\x2f\xfd\x04\x00",
    "7z": b"7z\xbc\xaf\x27\x1c\x00\x04",
    "rar": b"Rar!\x1a\x07\x01\x00",
    "lz4": b"\x04\x22\x4d\x18\x64\x40",
    "PE": b"MZ\x90\x00\x03\x00\x00\x00",
    "Mach-O": b"\xcf\xfa\xed\xfe\x07\x00\x00\x01",
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
    with pytest.raises(SystemExit, match="no known first bytes"):
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
        assert got == expected, f"{type(error).__name__}: {got}"
    assert g._stat_kind(tmp_path / "no" / "such") == "gone"
    assert g._stat_kind(repo / "src/pkg/a.py") == "file" and g._stat_kind(repo / "src") == "folder"


def test_a_tracked_file_in_a_folder_that_cannot_be_entered_is_a_hit_not_a_skip(
    tmp_path: Path,
) -> None:
    """Run as a user that is not root (root can enter any folder): a tracked file under a folder of mode 000."""
    import shutil
    import tempfile

    base = Path(tempfile.mkdtemp(prefix="guard-locked-"))
    try:
        base.chmod(0o755)
        repo = _track(_repo(base / "r", {**CLEAN, "src/pkg/locked/x.py": "X = 1\n"}))
        script = base / "demo_only_guard.py"
        shutil.copy(ROOT / "tools" / "demo_only_guard.py", script)
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
            subprocess.run(["chown", "-R", "65534:65534", str(base)], check=True)  # noqa: S603, S607
            command = [setpriv, "--reuid=65534", "--regid=65534", "--clear-groups", *command]
        done = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": os.environ["PATH"], "HOME": str(base)},
        )
        assert done.returncode == 1, done.stdout + done.stderr
        assert "src/pkg/locked/x.py: unreadable-file" in done.stdout, done.stdout + done.stderr
    finally:
        subprocess.run(["chmod", "-R", "u+rwx", str(base)], check=False)  # noqa: S603, S607
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
        with pytest.raises(SystemExit) as stop:
            _main(repo, cfg, *combo)
        assert stop.value.code == 2, f"the modes {combo} were not refused with exit 2"
        assert "not allowed with" in capsys.readouterr().err, f"no refusal text for {combo}"
    for flags in ((), ("--require",)):
        with pytest.raises(SystemExit) as stop:
            _main(repo, cfg, *flags, "--", "tests/test_x.py")
        assert stop.value.code == 2, flags
        assert "pytest arguments are accepted only with" in capsys.readouterr().err, flags


def test_the_copy_run_says_which_files_are_left_out_because_git_does_not_track_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _mini(tmp_path / "r")
    (repo / "src/pkg/new.py").write_text("N = 1\n", encoding="utf-8")
    assert g.run_without_folder(repo, _cfg(), ["tests/test_plain.py"]) == 0
    assert "1 file(s) are not added to git" in capsys.readouterr().out
