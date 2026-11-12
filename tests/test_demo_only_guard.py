"""The demo-only folder guard (tools/demo_only_guard.py): product code must not name the folder that holds everything
that exists only for demos, nor a made-up record id; the build must still pass with the folder deleted. Made-up data only.

Rows: the real repo is clean and the scan is not vacuous; each way to depend on the folder is a hit that names the file
and line but never prints the matched text; the settings are checked (a bad setting stops the guard); a missing folder
stops a run that requires it; pytest in a copy without the folder passes for a clean product and fails for one that
reaches into the folder.
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
        "suffixes": (".py", ".md", ".json"),
    }
    base.update(over)
    return g.GuardConfig(**base)  # type: ignore[arg-type]


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


CLEAN = {"src/pkg/__init__.py": "X = 1\n", f"{FOLDER}/data.json": '{"id": "FAKE-REC-0001"}\n'}


# -- the real repository ---------------------------------------------------------------------------------------------
def test_this_repository_is_clean_and_the_scan_is_not_vacuous() -> None:
    cfg = g.load_config(ROOT / "tools" / "demo_only_guard.toml")
    assert g.scan(ROOT, cfg) == []
    assert (ROOT / "src").is_dir() and any(
        g._files(ROOT / "src", cfg.suffixes)
    )  # it really looked at product files
    planted = g.scan(
        ROOT, _cfg(folder="hadavin_sdk")
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


def test_the_upper_case_table_name_is_not_a_hit(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path, {**CLEAN, "src/pkg/c.py": "DEMO_ONLY = frozenset()\n# the demo-only kinds\n"}
    )
    assert g.scan(repo, _cfg()) == []


def test_the_folder_inside_a_product_root_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/pkg/__init__.py": "", f"src/{FOLDER}/x.py": "A = 1\n"})
    assert any("folder-inside-product-root" in h for h in g.scan(repo, _cfg()))


def test_a_missing_product_root_is_a_hit_not_a_silent_pass(tmp_path: Path) -> None:
    hits = g.scan(_repo(tmp_path, {f"{FOLDER}/a.json": "{}"}), _cfg())
    assert hits == ["src: product-root-missing (a missing root would make the scan prove nothing)"]


def test_a_loader_may_name_the_folder_and_nothing_else_may(tmp_path: Path) -> None:
    files = {
        "src/pkg/loader.py": f'NAME = "{FOLDER}"\n',
        "src/pkg/other.py": f'NAME = "{FOLDER}"\n',
    }
    hits = g.scan(_repo(tmp_path, files), _cfg(loaders=("src/pkg/loader.py",)))
    assert hits == ["src/pkg/other.py:1: names-demo-only-folder"]


def test_a_stale_loader_entry_is_a_hit(tmp_path: Path) -> None:
    repo = _repo(tmp_path, {"src/pkg/loader.py": "NAME = 'x'\n"})
    hits = g.scan(repo, _cfg(loaders=("src/pkg/loader.py", "src/pkg/gone.py")))
    assert sorted(hits) == [
        "src/pkg/gone.py: stale-loader-entry (file does not exist)",
        "src/pkg/loader.py: stale-loader-entry (file does not name the folder)",
    ]


def test_caches_and_other_file_types_are_skipped(tmp_path: Path) -> None:
    repo = _repo(
        tmp_path, {**CLEAN, "src/pkg/__pycache__/x.py": FOLDER, "src/pkg/blob.bin": FOLDER}
    )
    assert g.scan(repo, _cfg()) == []


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
        "suffixes": '[".py"]',
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
        ({"suffixes": "[]"}, "'suffixes'"),
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
    (repo / ".git").mkdir()
    (repo / ".git" / "HEAD").write_text("x", encoding="utf-8")
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
